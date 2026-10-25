import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db, record_audit_log
from app.schemas import (
    SurveyCreate, SurveyUpdate, SurveyOut, SurveyListItemOut, SurveyPublishOut, QuestionOut,
    SurveyVersionOut, WebhookTestRequest, WebhookTestResponse, CognitivePretestReport
)
from app.engine.webhook_engine import WebhookEngine
from app.engine.demo_seeder import DemoAcademicSeeder
from app.engine.translation_engine import TranslationEngine
from app.engine.logic_engine import SurveyLogicEngine
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
    settings_str = json.dumps(payload.settings, ensure_ascii=False) if payload.settings else "{}"
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO surveys (id, title, description, instructions, status, public_slug, version, created_at, updated_at, settings_json)
            VALUES (?, ?, ?, ?, 'draft', ?, 1, ?, ?, ?)
        """, (survey_id, payload.title, payload.description or "", payload.instructions or "", slug, current_time, current_time, settings_str))
        
        # Ghi audit log vào chuỗi băm bất biến
        record_audit_log(conn, 'survey', survey_id, 'CREATE', {"title": payload.title}, current_time)

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
            
        settings_val = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() else {}

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
            settings=settings_val,
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

        # Cập nhật cài đặt cấu hình khảo sát (chất lượng, độ nhạy, v.v.)
        if payload.settings is not None:
            settings_str = json.dumps(payload.settings, ensure_ascii=False)
            conn.execute("UPDATE surveys SET settings_json = ? WHERE id = ?", (settings_str, survey_id))

        # Cập nhật danh sách câu hỏi nếu được cung cấp
        if payload.questions is not None:
            # Lưu snapshot phiên bản trước đó vào survey_versions phục vụ lưu vết khoa học
            curr_q_rows = conn.execute("""
                SELECT id, order_index, question_type, title, description,
                       is_required, options_json, logic_rules_json
                FROM questions WHERE survey_id = ? ORDER BY order_index ASC
            """, (survey_id,)).fetchall()

            if curr_q_rows:
                old_ver = s_row["version"]
                existing_ver = conn.execute("""
                    SELECT id FROM survey_versions WHERE survey_id = ? AND version = ?
                """, (survey_id, old_ver)).fetchone()

                if not existing_ver:
                    snap_questions = []
                    for q in curr_q_rows:
                        snap_questions.append({
                            "id": q["id"],
                            "order_index": q["order_index"],
                            "question_type": q["question_type"],
                            "title": q["title"],
                            "description": q["description"] or "",
                            "is_required": bool(q["is_required"]),
                            "options": json.loads(q["options_json"] or "[]"),
                            "logic_rules": json.loads(q["logic_rules_json"] or "[]")
                        })
                    conn.execute("""
                        INSERT INTO survey_versions (id, survey_id, version, title, description, questions_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), survey_id, old_ver, s_row["title"],
                        s_row["description"] or "", json.dumps(snap_questions, ensure_ascii=False), current_time
                    ))

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

        record_audit_log(conn, 'survey', survey_id, 'UPDATE', {"version": new_version}, current_time)

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

        record_audit_log(conn, 'survey', survey_id, 'PUBLISH', {}, current_time)

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

        record_audit_log(conn, 'survey', survey_id, 'CLOSE', {}, current_time)

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

        record_audit_log(conn, 'survey', survey_id, 'REOPEN', {}, current_time)

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

        record_audit_log(conn, 'survey', new_survey_id, 'DUPLICATE', {"source_survey_id": survey_id}, current_time)

    return get_survey(new_survey_id)

@router.delete("/{survey_id}", status_code=204)
def delete_survey(survey_id: str):
    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        
        # Ghi vết nhật ký kiểm toán trước khi xóa
        record_audit_log(conn, 'survey', survey_id, 'DELETE', {"title": s_row["title"]}, current_time)
        conn.execute("DELETE FROM surveys WHERE id = ?", (survey_id,))
    return None

@router.get("/{survey_id}/versions", response_model=List[SurveyVersionOut])
def list_survey_versions(survey_id: str):
    """
    Lấy danh sách các phiên bản cấu trúc câu hỏi lịch sử của cuộc khảo sát.
    Bảo đảm khả năng tái lập và kiểm chứng khoa học theo chuẩn Don Dillman & AAPOR.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id, title, description, version, created_at, updated_at FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        rows = conn.execute("""
            SELECT id, survey_id, version, title, description, questions_json, created_at
            FROM survey_versions WHERE survey_id = ? ORDER BY version ASC
        """, (survey_id,)).fetchall()

        result = []
        recorded_versions = set()
        for r in rows:
            q_data = json.loads(r["questions_json"] or "[]")
            v_num = r["version"]
            recorded_versions.add(v_num)
            result.append(SurveyVersionOut(
                id=r["id"],
                survey_id=r["survey_id"],
                version=v_num,
                title=r["title"],
                description=r["description"] or "",
                questions_count=len(q_data),
                questions=q_data,
                created_at=r["created_at"]
            ))

        # Luôn bao gồm phiên bản hiện tại
        curr_ver = s_row["version"]
        if curr_ver not in recorded_versions:
            curr_q_rows = conn.execute("""
                SELECT id, order_index, question_type, title, description, is_required, options_json, logic_rules_json
                FROM questions WHERE survey_id = ? ORDER BY order_index ASC
            """, (survey_id,)).fetchall()
            curr_q_list = []
            for q in curr_q_rows:
                curr_q_list.append({
                    "id": q["id"],
                    "order_index": q["order_index"],
                    "question_type": q["question_type"],
                    "title": q["title"],
                    "description": q["description"] or "",
                    "is_required": bool(q["is_required"]),
                    "options": json.loads(q["options_json"] or "[]"),
                    "logic_rules": json.loads(q["logic_rules_json"] or "[]")
                })
            result.append(SurveyVersionOut(
                id=f"current-{survey_id}-v{curr_ver}",
                survey_id=survey_id,
                version=curr_ver,
                title=s_row["title"],
                description=s_row["description"] or "",
                questions_count=len(curr_q_list),
                questions=curr_q_list,
                created_at=s_row["updated_at"] or s_row["created_at"]
            ))

        return sorted(result, key=lambda v: v.version)

@router.get("/{survey_id}/versions/{version_num}", response_model=SurveyVersionOut)
def get_survey_version_detail(survey_id: str, version_num: int):
    """Lấy chi tiết cấu trúc câu hỏi tại một phiên bản lịch sử cụ thể"""
    with get_db() as conn:
        v_row = conn.execute("""
            SELECT id, survey_id, version, title, description, questions_json, created_at
            FROM survey_versions WHERE survey_id = ? AND version = ?
        """, (survey_id, version_num)).fetchone()

        if not v_row:
            s_row = conn.execute("SELECT * FROM surveys WHERE id = ? AND version = ?", (survey_id, version_num)).fetchone()
            if not s_row:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy phiên bản v{version_num} của khảo sát.")

            curr_q_rows = conn.execute("""
                SELECT id, order_index, question_type, title, description, is_required, options_json, logic_rules_json
                FROM questions WHERE survey_id = ? ORDER BY order_index ASC
            """, (survey_id,)).fetchall()
            curr_q_list = []
            for q in curr_q_rows:
                curr_q_list.append({
                    "id": q["id"],
                    "order_index": q["order_index"],
                    "question_type": q["question_type"],
                    "title": q["title"],
                    "description": q["description"] or "",
                    "is_required": bool(q["is_required"]),
                    "options": json.loads(q["options_json"] or "[]"),
                    "logic_rules": json.loads(q["logic_rules_json"] or "[]")
                })
            return SurveyVersionOut(
                id=f"current-{survey_id}-v{version_num}",
                survey_id=survey_id,
                version=version_num,
                title=s_row["title"],
                description=s_row["description"] or "",
                questions_count=len(curr_q_list),
                questions=curr_q_list,
                created_at=s_row["updated_at"] or s_row["created_at"]
            )

        q_data = json.loads(v_row["questions_json"] or "[]")
        return SurveyVersionOut(
            id=v_row["id"],
            survey_id=v_row["survey_id"],
            version=v_row["version"],
            title=v_row["title"],
            description=v_row["description"] or "",
            questions_count=len(q_data),
            questions=q_data,
            created_at=v_row["created_at"]
        )

@router.post("/{survey_id}/settings/test-webhook", response_model=WebhookTestResponse)
def test_survey_webhook(survey_id: str, payload: WebhookTestRequest):
    """
    Kiểm tra kết nối và gửi thử nghiệm gói tin cảnh báo webhook đến máy chủ bên ngoài
    Xác minh mã HTTP status, độ trễ phản hồi (ms) và chữ ký HMAC-SHA256
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

    test_data = {
        "survey_id": survey_id,
        "survey_title": s_row["title"],
        "event_type": "TEST_WEBHOOK_PING",
        "simulated_risk_score": 85.0,
        "simulated_risk_level": "high",
        "message": "Gói tin kiểm tra kết nối từ hệ thống DataTrust Webhook Dispatcher.",
        "simulated_flags": [
            {
                "code": "FLAG_TEST_SIMULATION",
                "severity": "HIGH",
                "message": "Mô phỏng cảnh báo bất thường kiểm thử kết nối webhook."
            }
        ]
    }

    result = WebhookEngine.dispatch_payload(
        webhook_url=payload.webhook_url,
        payload=test_data,
        webhook_secret=payload.webhook_secret,
        event_type="TEST_WEBHOOK_PING",
        timeout=4.0
    )

    msg = "Gửi thử nghiệm thành công." if result["success"] else f"Gửi thử nghiệm thất bại: {result.get('error') or 'Mã phản hồi không hợp lệ'}"

    return WebhookTestResponse(
        success=result["success"],
        status_code=result.get("status_code"),
        delivery_id=result["delivery_id"],
        latency_ms=result["latency_ms"],
        message=msg,
        error=result.get("error")
    )

@router.post("/seed-academic-demo", status_code=201)
def seed_academic_demo_survey():
    """
    Khởi tạo Khảo sát Nghiên cứu Khoa học Mẫu & Bộ Dữ liệu Thực nghiệm (35 phản hồi)
    Phục vụ Ban Giám khảo, Hội đồng Đánh giá & Nhà nghiên cứu thẩm định trực tiếp toàn diện hệ thống:
    - 28 Mẫu sạch có độ tin cậy Cronbach's Alpha >= 0.80
    - 7 Mẫu cảnh báo bất thường (Speeders, Straightlining, Text Gibberish, Duplication)
    - Chuỗi băm kiểm toán SHA-256 bất biến toàn vẹn 100%
    """
    with get_db() as conn:
        result = DemoAcademicSeeder.seed_academic_study(conn)
        return result

@router.post("/{survey_id}/seed-demo-responses", status_code=201)
def seed_survey_demo_responses(survey_id: str, count: int = 15):
    """
    Nạp nhanh các phản hồi mẫu thực tế vào một khảo sát bất kỳ đã tồn tại
    """
    with get_db() as conn:
        try:
            result = DemoAcademicSeeder.seed_responses_for_survey(conn, survey_id, count=count)
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/{survey_id}/translations/auto-translate")
def auto_translate_survey_endpoint(survey_id: str, target_lang: str = "en"):
    """
    Tự động dịch khảo sát sang ngôn ngữ chỉ định (mặc định: 'en') bằng TranslationEngine học thuật.
    Lưu bản dịch vào cấu hình settings_json của khảo sát và ghi vết audit ledger.
    """
    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("""
            SELECT id, title, description, question_type, options_json
            FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        questions_list = []
        for q in q_rows:
            questions_list.append({
                "id": q["id"],
                "title": q["title"],
                "description": q["description"] or "",
                "question_type": q["question_type"],
                "options": json.loads(q["options_json"] or "[]")
            })

        translated_dict = TranslationEngine.auto_translate_survey(
            survey_title=s_row["title"],
            survey_desc=s_row["description"] or "",
            survey_instructions=s_row["instructions"] or "",
            questions=questions_list,
            target_lang=target_lang
        )

        settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() and s_row["settings_json"] else {}
        if "translations" not in settings:
            settings["translations"] = {}
        settings["translations"][target_lang] = translated_dict

        conn.execute("UPDATE surveys SET settings_json = ?, updated_at = ? WHERE id = ?", (
            json.dumps(settings, ensure_ascii=False), current_time, survey_id
        ))

        record_audit_log(conn, 'survey', survey_id, 'AUTO_TRANSLATE', {
            "target_lang": target_lang,
            "translated_questions_count": len(translated_dict.get("questions", {}))
        }, current_time)

        return translated_dict

@router.get("/{survey_id}/translations")
def get_survey_translations(survey_id: str):
    """
    Lấy toàn bộ các bản dịch hiện có của khảo sát
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() and s_row["settings_json"] else {}
        translations = settings.get("translations", {})
        available_languages = ["vi"] + [l for l in translations.keys() if l != "vi"]

        return {
            "survey_id": survey_id,
            "available_languages": available_languages,
            "translations": translations
        }

@router.put("/{survey_id}/translations/{lang}")
def update_survey_translation(survey_id: str, lang: str, payload: dict):
    """
    Cập nhật thủ công hoặc bổ sung bản dịch cho một ngôn ngữ cụ thể
    """
    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() and s_row["settings_json"] else {}
        if "translations" not in settings:
            settings["translations"] = {}
        
        settings["translations"][lang] = payload

        conn.execute("UPDATE surveys SET settings_json = ?, updated_at = ? WHERE id = ?", (
            json.dumps(settings, ensure_ascii=False), current_time, survey_id
        ))

        record_audit_log(conn, 'survey', survey_id, 'UPDATE_TRANSLATION', {
            "lang": lang
        }, current_time)

        return {
            "survey_id": survey_id,
            "lang": lang,
            "status": "updated",
            "translation": payload
        }

@router.get("/{survey_id}/logic/validate")
def validate_survey_branching_logic(survey_id: str):
    """
    Phân tích & Kiểm định toàn diện logic rẽ nhánh khảo sát (DAG Analysis):
    - Phát hiện chu trình vòng lặp phụ thuộc luẩn quẩn (Deadly Cycles)
    - Phát hiện nghịch đảo trật tự thời gian (Order Inversions)
    - Phát hiện tham chiếu câu hỏi không tồn tại (Dangling References)
    - Phát hiện câu hỏi mồ côi không thể tiếp cận (Unreachable Questions)
    - Tính toán độ phức tạp đồ thị McCabe Cyclomatic Complexity & Liệt kê các kịch bản lộ trình
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        
        q_rows = conn.execute(
            "SELECT id, order_index, question_type, title, description, is_required, options_json, logic_rules_json "
            "FROM questions WHERE survey_id = ? ORDER BY order_index ASC",
            (survey_id,)
        ).fetchall()

        questions = []
        for q in q_rows:
            questions.append({
                "id": q["id"],
                "order_index": q["order_index"],
                "question_type": q["question_type"],
                "title": q["title"],
                "description": q["description"] or "",
                "is_required": bool(q["is_required"]),
                "options": json.loads(q["options_json"] or "[]"),
                "logic_rules": json.loads(q["logic_rules_json"] or "[]")
            })

    report = SurveyLogicEngine.analyze_survey_logic(questions)
    report["survey_id"] = survey_id
    report["survey_title"] = s_row["title"]
    return report

@router.post("/{survey_id}/logic/simulate")
def simulate_survey_respondent_flow(survey_id: str, payload: dict):
    """
    Mô phỏng trải nghiệm thực tế của người trả lời qua bảng câu hỏi dựa trên các câu trả lời giả định:
    - payload: {"answers": { question_id: answer_value }}
    - Trả về danh sách câu hỏi hiển thị, câu hỏi bị ẩn và lý do bỏ qua
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        
        q_rows = conn.execute(
            "SELECT id, order_index, question_type, title, description, is_required, options_json, logic_rules_json "
            "FROM questions WHERE survey_id = ? ORDER BY order_index ASC",
            (survey_id,)
        ).fetchall()

        questions = []
        for q in q_rows:
            questions.append({
                "id": q["id"],
                "order_index": q["order_index"],
                "question_type": q["question_type"],
                "title": q["title"],
                "description": q["description"] or "",
                "is_required": bool(q["is_required"]),
                "options": json.loads(q["options_json"] or "[]"),
                "logic_rules": json.loads(q["logic_rules_json"] or "[]")
            })

    answers = payload.get("answers", payload)
    flow_result = SurveyLogicEngine.simulate_respondent_flow(questions, answers)
    flow_result["survey_id"] = survey_id
    flow_result["survey_title"] = s_row["title"]
    return flow_result

@router.post("/{survey_id}/cognitive-pretest", response_model=CognitivePretestReport)
def run_survey_cognitive_pretest(survey_id: str):
    """
    Thử nghiệm nhận thức tiền xuất bản & Chẩn đoán mơ hồ bảng hỏi (Cognitive Pre-Testing & Ambiguity Diagnostics):
    - Đánh giá chỉ số dễ đọc Flesch Reading Ease & độ phức tạp câu hỏi
    - Phát hiện 8 dạng lỗi thiết kế bảng hỏi (Leading questions, Double-barreled, Double negatives, Vague quantifiers...)
    - Giả lập 3 Persona nhận thức nhân khẩu học (Fast Paced Mobile, Elderly Plain Language, Analytical Reviewer)
    - Dự báo đường cong mệt mỏi nhận thức và nguy cơ bỏ ngang
    - Cung cấp gợi ý viết lại tự động chuẩn học thuật Don Dillman & AAPOR
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, order_index, question_type, title, description, is_required, options_json, logic_rules_json "
            "FROM questions WHERE survey_id = ? ORDER BY order_index ASC",
            (survey_id,)
        ).fetchall()

        questions = []
        for q in q_rows:
            questions.append({
                "id": q["id"],
                "order_index": q["order_index"],
                "question_type": q["question_type"],
                "title": q["title"],
                "description": q["description"] or "",
                "is_required": bool(q["is_required"]),
                "options": json.loads(q["options_json"] or "[]"),
                "logic_rules": json.loads(q["logic_rules_json"] or "[]")
            })

    from app.engine.cognitive_pretest_engine import CognitivePretestEngine
    return CognitivePretestEngine.run_pretest_audit(
        survey_id=survey_id,
        title=s_row["title"],
        questions=questions
    )




