import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.schemas import (
    SurveyCreate, SurveyUpdate, SurveyOut, SurveyListItemOut, SurveyPublishOut, QuestionOut
)
from app.config import PUBLIC_BASE_URL

router = APIRouter(prefix="/api/surveys", tags=["Surveys"])

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def generate_slug(title: str) -> str:
    # Sinh slug thân thiện từ tiêu đề
    import re
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower()).strip()
    slug_part = re.sub(r'[\s-]+', '-', cleaned)[:30]
    rand_suffix = uuid.uuid4().hex[:6]
    return f"{slug_part}-{rand_suffix}" if slug_part else f"survey-{rand_suffix}"

@router.get("", response_model=List[SurveyListItemOut])
def list_surveys(status: Optional[str] = None):
    with get_db() as conn:
        query = """
            SELECT s.*, 
                   (SELECT COUNT(*) FROM questions q WHERE q.survey_id = s.id) AS questions_count,
                   (SELECT COUNT(*) FROM responses r WHERE r.survey_id = s.id) AS responses_count,
                   (SELECT COALESCE(AVG(risk_score), 0.0) FROM responses r WHERE r.survey_id = s.id) AS avg_risk_score
            FROM surveys s
        """
        params = []
        if status:
            query += " WHERE s.status = ?"
            params.append(status)
        query += " ORDER BY s.created_at DESC"
        
        rows = conn.execute(query, params).fetchall()
        
        result = []
        for r in rows:
            result.append(SurveyListItemOut(
                id=r["id"],
                title=r["title"],
                description=r["description"] or "",
                status=r["status"],
                public_slug=r["public_slug"],
                version=r["version"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                closed_at=r["closed_at"],
                questions_count=r["questions_count"],
                responses_count=r["responses_count"],
                avg_risk_score=round(r["avg_risk_score"], 1)
            ))
        return result

@router.post("", response_model=SurveyOut, status_code=201)
def create_survey(payload: SurveyCreate):
    survey_id = str(uuid.uuid4())
    slug = generate_slug(payload.title)
    current_time = now_iso()
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO surveys (id, title, description, instructions, status, public_slug, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'draft', ?, 1, ?, ?)
        """, (survey_id, payload.title, payload.description or "", payload.instructions or "", slug, current_time, current_time))
        
        # Ghi audit log
        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'survey', ?, 'CREATE', ?, ?)
        """, (str(uuid.uuid4()), survey_id, json.dumps({"title": payload.title}), current_time))

    return get_survey(survey_id)

@router.get("/{survey_id}", response_model=SurveyOut)
def get_survey(survey_id: str):
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()
        
        resp_count = conn.execute("""
            SELECT COUNT(*) AS cnt FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchone()["cnt"]
        
        questions = []
        for q in q_rows:
            questions.append(QuestionOut(
                id=q["id"],
                survey_id=q["survey_id"],
                order_index=q["order_index"],
                question_type=q["question_type"],
                title=q["title"],
                description=q["description"] or "",
                is_required=bool(q["is_required"]),
                options=json.loads(q["options_json"] or "[]"),
                logic_rules=json.loads(q["logic_rules_json"] or "[]"),
                created_at=q["created_at"]
            ))
            
        return SurveyOut(
            id=s_row["id"],
            title=s_row["title"],
            description=s_row["description"] or "",
            instructions=s_row["instructions"] or "",
            status=s_row["status"],
            public_slug=s_row["public_slug"],
            version=s_row["version"],
            created_at=s_row["created_at"],
            updated_at=s_row["updated_at"],
            closed_at=s_row["closed_at"],
            questions=questions,
            responses_count=resp_count
        )

@router.put("/{survey_id}", response_model=SurveyOut)
def update_survey(survey_id: str, payload: SurveyUpdate):
    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        
        # Cập nhật thông tin cơ bản
        title = payload.title if payload.title is not None else s_row["title"]
        description = payload.description if payload.description is not None else s_row["description"]
        instructions = payload.instructions if payload.instructions is not None else s_row["instructions"]
        new_version = s_row["version"] + 1

        conn.execute("""
            UPDATE surveys 
            SET title = ?, description = ?, instructions = ?, version = ?, updated_at = ?
            WHERE id = ?
        """, (title, description, instructions, new_version, current_time, survey_id))

        # Cập nhật danh sách câu hỏi nếu được cung cấp
        if payload.questions is not None:
            # Xóa các câu hỏi cũ để đồng bộ chính xác danh sách câu hỏi mới
            conn.execute("DELETE FROM questions WHERE survey_id = ?", (survey_id,))
            
            for idx, q in enumerate(payload.questions):
                qid = q.id if q.id else str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO questions (
                        id, survey_id, order_index, question_type, title, description,
                        is_required, options_json, logic_rules_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    qid, survey_id, idx, q.question_type, q.title, q.description or "",
                    1 if q.is_required else 0,
                    json.dumps(q.options),
                    json.dumps(q.logic_rules),
                    current_time
                ))

        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'survey', ?, 'UPDATE', ?, ?)
        """, (str(uuid.uuid4()), survey_id, json.dumps({"version": new_version}), current_time))

    return get_survey(survey_id)

@router.post("/{survey_id}/publish", response_model=SurveyPublishOut)
def publish_survey(survey_id: str):
    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        
        # Kiểm tra khảo sát có ít nhất 1 câu hỏi
        q_count = conn.execute("SELECT COUNT(*) AS cnt FROM questions WHERE survey_id = ?", (survey_id,)).fetchone()["cnt"]
        if q_count == 0:
            raise HTTPException(status_code=400, detail="Không thể xuất bản: Khảo sát chưa có câu hỏi nào.")

        conn.execute("""
            UPDATE surveys SET status = 'published', updated_at = ? WHERE id = ?
        """, (current_time, survey_id))

        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'survey', ?, 'PUBLISH', '{}', ?)
        """, (str(uuid.uuid4()), survey_id, current_time))

        slug = s_row["public_slug"]
        public_url = f"{PUBLIC_BASE_URL}/s/{slug}"

        return SurveyPublishOut(
            id=survey_id,
            status="published",
            public_slug=slug,
            public_url=public_url,
            published_at=current_time
        )

@router.post("/{survey_id}/close", response_model=SurveyOut)
def close_survey(survey_id: str):
    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        conn.execute("""
            UPDATE surveys SET status = 'closed', closed_at = ?, updated_at = ? WHERE id = ?
        """, (current_time, current_time, survey_id))

        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'survey', ?, 'CLOSE', '{}', ?)
        """, (str(uuid.uuid4()), survey_id, current_time))

    return get_survey(survey_id)

@router.post("/{survey_id}/reopen", response_model=SurveyOut)
def reopen_survey(survey_id: str):
    """Mở lại cuộc khảo sát đã đóng để tiếp tục thu thập phản hồi"""
    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        conn.execute("""
            UPDATE surveys SET status = 'published', closed_at = NULL, updated_at = ? WHERE id = ?
        """, (current_time, survey_id))

        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'survey', ?, 'REOPEN', '{}', ?)
        """, (str(uuid.uuid4()), survey_id, current_time))

    return get_survey(survey_id)

@router.post("/{survey_id}/duplicate", response_model=SurveyOut, status_code=201)
def duplicate_survey(survey_id: str):
    """Nhân bản toàn bộ cấu trúc khảo sát và danh sách câu hỏi sang một bản nháp mới"""
    current_time = now_iso()
    new_survey_id = str(uuid.uuid4())
    
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát gốc.")

        new_title = f"Bản sao của {s_row['title']}"
        new_slug = generate_slug(new_title)

        conn.execute("""
            INSERT INTO surveys (id, title, description, instructions, status, public_slug, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'draft', ?, 1, ?, ?)
        """, (new_survey_id, new_title, s_row["description"] or "", s_row["instructions"] or "", new_slug, current_time, current_time))

        # Nhân bản danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        for q in q_rows:
            conn.execute("""
                INSERT INTO questions (
                    id, survey_id, order_index, question_type, title, description,
                    is_required, options_json, logic_rules_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), new_survey_id, q["order_index"], q["question_type"],
                q["title"], q["description"] or "", q["is_required"],
                q["options_json"] or "[]", q["logic_rules_json"] or "[]", current_time
            ))

        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'survey', ?, 'DUPLICATE', ?, ?)
        """, (str(uuid.uuid4()), new_survey_id, json.dumps({"source_survey_id": survey_id}), current_time))

    return get_survey(new_survey_id)

@router.delete("/{survey_id}", status_code=204)
def delete_survey(survey_id: str):
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        conn.execute("DELETE FROM surveys WHERE id = ?", (survey_id,))
    return None
