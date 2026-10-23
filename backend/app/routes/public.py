import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from app.database import get_db
from app.schemas import PublicSurveyOut, PublicQuestionOut, ResponseSubmit
from app.engine.quality_engine import QualityEngine
from app.middleware.rate_limiter import public_submission_limiter

router = APIRouter(prefix="/api/public/surveys", tags=["Public Survey"])

def parse_iso(dt_str: str) -> datetime:
    try:
        # Xử lý cả dạng kết thúc bằng Z hoặc +00:00
        clean = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return datetime.now(timezone.utc)

@router.get("/{slug_or_id}", response_model=PublicSurveyOut)
def get_public_survey(slug_or_id: str):
    """Lấy dữ liệu khảo sát công khai cho người tham gia làm bài"""
    with get_db() as conn:
        s_row = conn.execute("""
            SELECT * FROM surveys WHERE public_slug = ? OR id = ?
        """, (slug_or_id, slug_or_id)).fetchone()

        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        status = s_row["status"]
        if status == "draft":
            raise HTTPException(
                status_code=403,
                detail="Khảo sát này đang ở chế độ bản nháp và chưa được xuất bản. Vui lòng liên hệ người tạo khảo sát."
            )
        if status == "closed":
            raise HTTPException(
                status_code=410,
                detail="Khảo sát này đã kết thúc và không còn chấp nhận phản hồi mới."
            )
        if status == "archived":
            raise HTTPException(status_code=404, detail="Khảo sát đã được lưu trữ và không còn khả dụng.")

        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (s_row["id"],)).fetchall()

        questions = []
        for q in q_rows:
            questions.append(PublicQuestionOut(
                id=q["id"],
                order_index=q["order_index"],
                question_type=q["question_type"],
                title=q["title"],
                description=q["description"] or "",
                is_required=bool(q["is_required"]),
                options=json.loads(q["options_json"] or "[]"),
                logic_rules=json.loads(q["logic_rules_json"] or "[]")
            ))

        return PublicSurveyOut(
            id=s_row["id"],
            title=s_row["title"],
            description=s_row["description"] or "",
            instructions=s_row["instructions"] or "",
            public_slug=s_row["public_slug"],
            version=s_row["version"],
            questions=questions
        )

@router.post("/{slug_or_id}/submit", status_code=201)
def submit_response(slug_or_id: str, payload: ResponseSubmit, request: Request):
    """Tiếp nhận, kiểm tra hợp lệ, lưu phản hồi thật và thực thi Quality Engine"""
    # 0. Kiểm tra giới hạn tốc độ gửi phản hồi (Rate Limiting)
    public_submission_limiter.check(request)

    with get_db() as conn:
        s_row = conn.execute("""
            SELECT * FROM surveys WHERE public_slug = ? OR id = ?
        """, (slug_or_id, slug_or_id)).fetchone()

        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        if s_row["status"] != "published":
            raise HTTPException(status_code=400, detail="Khảo sát hiện không ở trạng thái nhận phản hồi.")

        survey_id = s_row["id"]
        survey_version = s_row["version"]

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        questions = [dict(q) for q in q_rows]
        for q in questions:
            q["options"] = json.loads(q.get("options_json") or "[]")
            q["logic_rules"] = json.loads(q.get("logic_rules_json") or "[]")

        # Kiểm tra tính hợp lệ cơ bản (Validation Layer A)
        errors = []
        for q in questions:
            qid = q["id"]
            val = payload.answers.get(qid)
            is_req = bool(q["is_required"])
            q_type = q.get("question_type")
            opts = q.get("options", [])
            
            if is_req:
                if val is None or (isinstance(val, str) and not val.strip()):
                    errors.append(f"Câu hỏi bắt buộc '{q['title']}' chưa có câu trả lời.")
                elif isinstance(val, list) and len(val) == 0:
                    errors.append(f"Câu hỏi bắt buộc '{q['title']}' chưa có phương án nào được chọn.")
                elif q_type == "matrix":
                    if not isinstance(val, dict):
                        errors.append(f"Câu hỏi ma trận '{q['title']}' yêu cầu câu trả lời theo từng hàng.")
                    else:
                        # Kiểm tra xem tất cả các hàng đã được trả lời chưa
                        matrix_rows = opts.get("rows", []) if isinstance(opts, dict) else []
                        for r in matrix_rows:
                            r_id = r.get("id") if isinstance(r, dict) else str(r)
                            if not val.get(r_id):
                                r_label = r.get("label", r_id) if isinstance(r, dict) else r_id
                                errors.append(f"Câu hỏi ma trận '{q['title']}': Hàng '{r_label}' chưa có đánh giá.")
                                break
                elif q_type == "ranking":
                    if not isinstance(val, list) or len(val) == 0:
                        errors.append(f"Câu hỏi xếp hạng '{q['title']}' chưa được sắp xếp.")

            # Kiểm tra kiểu số nếu có nhập
            if q_type == "number" and val is not None and str(val).strip() != "":
                try:
                    float(val)
                except (ValueError, TypeError):
                    errors.append(f"Câu hỏi '{q['title']}' yêu cầu giá trị số hợp lệ.")

        if errors:
            raise HTTPException(status_code=422, detail={"validation_errors": errors})

        # Tính thời gian làm bài (duration_seconds)
        start_dt = parse_iso(payload.started_at)
        submit_dt = parse_iso(payload.submitted_at)
        duration = max(0.0, (submit_dt - start_dt).total_seconds())

        # 0.1. Bảo vệ chống nộp trùng lặp do vô tình double-click chuột từ cùng thiết bị trong vòng 3 giây
        recent_rows = conn.execute("""
            SELECT id, submitted_at, client_metadata_json FROM responses
            WHERE survey_id = ? ORDER BY submitted_at DESC LIMIT 5
        """, (survey_id,)).fetchall()

        for rr in recent_rows:
            try:
                r_ts = parse_iso(rr["submitted_at"]).timestamp()
                if abs(submit_dt.timestamp() - r_ts) <= 3.0:
                    prev_meta_raw = rr["client_metadata_json"] or "{}"
                    curr_meta_dict = payload.client_metadata or {}
                    try:
                        prev_meta_dict = json.loads(prev_meta_raw)
                        # Nếu cả 2 đều có metadata thiết bị và khác nhau -> là 2 thiết bị khác nhau, không phải double-click
                        if prev_meta_dict and curr_meta_dict and prev_meta_dict != curr_meta_dict:
                            continue
                    except Exception:
                        pass

                    ans_rows = conn.execute("""
                        SELECT question_id, answer_value FROM response_answers WHERE response_id = ?
                    """, (rr["id"],)).fetchall()
                    existing_answers = {a["question_id"]: a["answer_value"] for a in ans_rows}

                    is_exact_double_click = True
                    for qid, val in payload.answers.items():
                        v_str = json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else str(val)
                        if existing_answers.get(qid) != v_str:
                            is_exact_double_click = False
                            break
                    if is_exact_double_click and len(payload.answers) == len(existing_answers):
                        return {
                            "response_id": rr["id"],
                            "message": "Phản hồi đã được tiếp nhận thành công (Bảo vệ trùng lặp kích hoạt).",
                            "risk_score": 0.0,
                            "risk_level": "low"
                        }
            except Exception:
                pass

        response_id = str(uuid.uuid4())
        submitted_at_iso = submit_dt.isoformat()
        started_at_iso = start_dt.isoformat()

        # 1. Lưu bản ghi response
        source_val = payload.source or "online_form"
        enum_val = payload.enumerator_id or ""
        conn.execute("""
            INSERT INTO responses (
                id, survey_id, survey_version, started_at, submitted_at,
                duration_seconds, client_metadata_json, risk_score, risk_level,
                analysis_status, review_status, source, enumerator_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 'low', 'pending', 'unverified', ?, ?)
        """, (
            response_id, survey_id, survey_version, started_at_iso, submitted_at_iso,
            duration, json.dumps(payload.client_metadata or {}), source_val, enum_val
        ))

        # 2. Lưu từng câu trả lời vào response_answers
        for qid, val in payload.answers.items():
            ans_id = str(uuid.uuid4())
            ans_str = json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else str(val)
            conn.execute("""
                INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (ans_id, response_id, qid, ans_str, submitted_at_iso))

        # 3. Lấy các phản hồi trước đó để đối chiếu (Layer B & F & G)
        prior_resp_rows = conn.execute("""
            SELECT id, enumerator_id, risk_score FROM responses WHERE survey_id = ? AND id != ?
        """, (survey_id, response_id)).fetchall()

        prior_responses = []
        for pr in prior_resp_rows:
            pr_id = pr["id"]
            ans_rows = conn.execute("""
                SELECT question_id, answer_value FROM response_answers WHERE response_id = ?
            """, (pr_id,)).fetchall()
            
            p_answers = {}
            for a in ans_rows:
                raw_val = a["answer_value"]
                try:
                    p_answers[a["question_id"]] = json.loads(raw_val)
                except Exception:
                    p_answers[a["question_id"]] = raw_val
                    
            prior_responses.append({
                "id": pr_id,
                "answers": p_answers,
                "enumerator_id": pr["enumerator_id"] if "enumerator_id" in pr.keys() else "",
                "risk_score": pr["risk_score"] if "risk_score" in pr.keys() else 0.0
            })

        # 4. Thực thi QualityEngine phân tích chất lượng
        s_settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() else {}
        quality_settings = s_settings.get("quality_settings", {})

        analysis = QualityEngine.analyze_response(
            new_answers=payload.answers,
            duration_seconds=duration,
            questions=questions,
            prior_responses=prior_responses,
            enumerator_id=enum_val,
            quality_settings=quality_settings
        )

        # 5. Lưu kết quả đánh giá chất lượng
        assessment_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO quality_assessments (
                id, response_id, score_dup, score_pattern, score_logic, score_speed, score_text, score_enum,
                composite_score, flags_json, closest_match_response_id, highest_similarity, assessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id, response_id,
            analysis["score_dup"], analysis["score_pattern"], analysis["score_logic"],
            analysis["score_speed"], analysis["score_text"], analysis.get("score_enum", 0.0),
            analysis["composite_score"],
            json.dumps(analysis["flags"], ensure_ascii=False),
            analysis.get("closest_match_response_id"), analysis.get("highest_similarity", 0.0),
            submitted_at_iso
        ))

        # 6. Cập nhật điểm rủi ro và trạng thái vào responses
        conn.execute("""
            UPDATE responses 
            SET risk_score = ?, risk_level = ?, analysis_status = 'analyzed'
            WHERE id = ?
        """, (analysis["composite_score"], analysis["risk_level"], response_id))

        return {
            "response_id": response_id,
            "message": "Phản hồi của bạn đã được ghi nhận thành công.",
            "status": "recorded",
            "risk_score": analysis["composite_score"],
            "risk_level": analysis["risk_level"]
        }
