import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.schemas import (
    ResponseListItemOut, ResponseDetailOut, QualityAssessmentOut,
    ReviewStatusUpdate, QuestionOut
)
from app.engine.quality_engine import QualityEngine

router = APIRouter(prefix="/api/surveys/{survey_id}/responses", tags=["Responses & Review"])

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.get("", response_model=List[ResponseListItemOut])
def list_responses(
    survey_id: str,
    risk_level: Optional[str] = Query(None, description="Lọc theo mức độ rủi ro: low, medium, high"),
    review_status: Optional[str] = Query(None, description="Lọc theo trạng thái xác minh: unverified, under_review, verified_valid, verified_fraud, inconclusive"),
    limit: int = 100,
    offset: int = 0
):
    with get_db() as conn:
        query = """
            SELECT r.*, q.flags_json
            FROM responses r
            LEFT JOIN quality_assessments q ON q.response_id = r.id
            WHERE r.survey_id = ?
        """
        params = [survey_id]
        if risk_level:
            query += " AND r.risk_level = ?"
            params.append(risk_level)
        if review_status:
            query += " AND r.review_status = ?"
            params.append(review_status)

        query += " ORDER BY r.submitted_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            flags = json.loads(r["flags_json"] or "[]") if r["flags_json"] else []
            flag_msgs = [f.get("message", "") for f in flags[:2]]
            result.append(ResponseListItemOut(
                id=r["id"],
                survey_id=r["survey_id"],
                started_at=r["started_at"],
                submitted_at=r["submitted_at"],
                duration_seconds=round(r["duration_seconds"], 1),
                risk_score=round(r["risk_score"], 1),
                risk_level=r["risk_level"],
                analysis_status=r["analysis_status"],
                review_status=r["review_status"],
                flags_count=len(flags),
                flags_summary=flag_msgs
            ))
        return result

@router.get("/{response_id}", response_model=ResponseDetailOut)
def get_response_detail(survey_id: str, response_id: str):
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        r_row = conn.execute("""
            SELECT * FROM responses WHERE id = ? AND survey_id = ?
        """, (response_id, survey_id)).fetchone()
        if not r_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy phản hồi.")

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()
        
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

        # Lấy câu trả lời
        ans_rows = conn.execute("""
            SELECT question_id, answer_value FROM response_answers WHERE response_id = ?
        """, (response_id,)).fetchall()
        
        answers = {}
        for a in ans_rows:
            raw = a["answer_value"]
            try:
                answers[a["question_id"]] = json.loads(raw)
            except Exception:
                answers[a["question_id"]] = raw

        # Lấy kết quả đánh giá chất lượng
        qa_row = conn.execute("""
            SELECT * FROM quality_assessments WHERE response_id = ?
        """, (response_id,)).fetchone()

        assessment = None
        if qa_row:
            flags_data = json.loads(qa_row["flags_json"] or "[]")
            assessment = QualityAssessmentOut(
                id=qa_row["id"],
                score_dup=round(qa_row["score_dup"], 1),
                score_pattern=round(qa_row["score_pattern"], 1),
                score_logic=round(qa_row["score_logic"], 1),
                score_speed=round(qa_row["score_speed"], 1),
                score_text=round(qa_row["score_text"], 1),
                composite_score=round(qa_row["composite_score"], 1),
                flags=flags_data,
                closest_match_response_id=qa_row["closest_match_response_id"],
                highest_similarity=round(qa_row["highest_similarity"], 3),
                assessed_at=qa_row["assessed_at"]
            )

        client_meta = json.loads(r_row["client_metadata_json"] or "{}")

        return ResponseDetailOut(
            id=r_row["id"],
            survey_id=survey_id,
            survey_title=s_row["title"],
            survey_version=r_row["survey_version"],
            started_at=r_row["started_at"],
            submitted_at=r_row["submitted_at"],
            duration_seconds=round(r_row["duration_seconds"], 1),
            risk_score=round(r_row["risk_score"], 1),
            risk_level=r_row["risk_level"],
            analysis_status=r_row["analysis_status"],
            review_status=r_row["review_status"],
            review_notes=r_row["review_notes"] or "",
            reviewed_at=r_row["reviewed_at"],
            client_metadata=client_meta,
            answers=answers,
            questions=questions,
            assessment=assessment
        )

@router.patch("/{response_id}/review")
def update_review_decision(survey_id: str, response_id: str, payload: ReviewStatusUpdate):
    current_time = now_iso()
    with get_db() as conn:
        r_row = conn.execute("""
            SELECT id FROM responses WHERE id = ? AND survey_id = ?
        """, (response_id, survey_id)).fetchone()
        if not r_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy phản hồi.")

        valid_statuses = ("unverified", "under_review", "verified_valid", "verified_fraud", "inconclusive")
        if payload.review_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Trạng thái không hợp lệ. Phải là một trong: {valid_statuses}")

        conn.execute("""
            UPDATE responses 
            SET review_status = ?, review_notes = ?, reviewed_at = ?
            WHERE id = ?
        """, (payload.review_status, payload.review_notes or "", current_time, response_id))

        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'verification', ?, 'REVIEW_DECISION', ?, ?)
        """, (str(uuid.uuid4()), response_id, json.dumps({
            "status": payload.review_status,
            "notes": payload.review_notes
        }, ensure_ascii=False), current_time))

    return {"message": "Cập nhật quyết định xác minh thành công.", "review_status": payload.review_status}

@router.get("/compare/side-by-side")
def compare_responses(survey_id: str, resp1: str = Query(...), resp2: str = Query(...)):
    """So sánh trực quan 2 phản hồi cạnh nhau"""
    with get_db() as conn:
        s_row = conn.execute("SELECT title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        r1 = conn.execute("SELECT * FROM responses WHERE id = ? AND survey_id = ?", (resp1, survey_id)).fetchone()
        r2 = conn.execute("SELECT * FROM responses WHERE id = ? AND survey_id = ?", (resp2, survey_id)).fetchone()
        if not r1 or not r2:
            raise HTTPException(status_code=404, detail="Một hoặc cả hai phản hồi không tồn tại.")

        q_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()

        ans1_rows = conn.execute("SELECT question_id, answer_value FROM response_answers WHERE response_id = ?", (resp1,)).fetchall()
        ans2_rows = conn.execute("SELECT question_id, answer_value FROM response_answers WHERE response_id = ?", (resp2,)).fetchall()

        ans1 = {a["question_id"]: a["answer_value"] for a in ans1_rows}
        ans2 = {a["question_id"]: a["answer_value"] for a in ans2_rows}

        comparison = []
        matching_count = 0
        total_compared = 0

        for q in q_rows:
            qid = q["id"]
            val1 = ans1.get(qid, "")
            val2 = ans2.get(qid, "")
            
            norm1 = QualityEngine.normalize_value(val1)
            norm2 = QualityEngine.normalize_value(val2)
            
            is_match = (norm1 == norm2) if (norm1 != "" or norm2 != "") else False
            if norm1 != "" or norm2 != "":
                total_compared += 1
                if is_match:
                    matching_count += 1

            comparison.append({
                "question_id": qid,
                "question_title": q["title"],
                "question_type": q["question_type"],
                "val_resp1": val1,
                "val_resp2": val2,
                "is_match": is_match
            })

        similarity = (matching_count / total_compared) if total_compared > 0 else 0.0

        return {
            "survey_title": s_row["title"],
            "resp1_id": resp1,
            "resp2_id": resp2,
            "resp1_risk_score": r1["risk_score"],
            "resp2_risk_score": r2["risk_score"],
            "total_questions_compared": total_compared,
            "matching_answers_count": matching_count,
            "similarity_percentage": round(similarity * 100, 1),
            "questions_comparison": comparison
        }
