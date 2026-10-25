import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from app.database import get_db, record_audit_log
from app.schemas import (
    PublicSurveyOut, PublicQuestionOut, ResponseSubmit,
    BatchResponseSubmit, BatchSyncResponseOut, BatchSyncResultItem
)
from app.engine.quality_engine import QualityEngine
from app.engine.quota_engine import QuotaEngine
from app.engine.webhook_engine import WebhookEngine
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
def get_public_survey(slug_or_id: str, lang: str = "vi"):
    """Lấy dữ liệu khảo sát công khai cho người tham gia làm bài, hỗ trợ bản địa hóa đa ngôn ngữ (i18n)"""
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

        settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() and s_row["settings_json"] else {}
        translations = settings.get("translations", {})
        available_languages = ["vi"] + [l for l in translations.keys() if l != "vi"]

        survey_title = s_row["title"]
        survey_desc = s_row["description"] or ""
        survey_inst = s_row["instructions"] or ""
        current_lang = "vi"

        t_data = None
        if lang != "vi" and lang in translations:
            t_data = translations[lang]
            current_lang = lang
            survey_title = t_data.get("title") or survey_title
            if "description" in t_data and t_data["description"]:
                survey_desc = t_data["description"]
            if "instructions" in t_data and t_data["instructions"]:
                survey_inst = t_data["instructions"]

        t_questions = t_data.get("questions", {}) if t_data else {}

        questions = []
        for q in q_rows:
            qid = q["id"]
            q_title = q["title"]
            q_desc = q["description"] or ""
            q_opts = json.loads(q["options_json"] or "[]")

            if qid in t_questions:
                t_q = t_questions[qid]
                if t_q.get("title"):
                    q_title = t_q["title"]
                if t_q.get("description"):
                    q_desc = t_q["description"]
                if t_q.get("options") is not None:
                    q_opts = t_q["options"]

            questions.append(PublicQuestionOut(
                id=qid,
                order_index=q["order_index"],
                question_type=q["question_type"],
                title=q_title,
                description=q_desc,
                is_required=bool(q["is_required"]),
                options=q_opts,
                logic_rules=json.loads(q["logic_rules_json"] or "[]")
            ))

        return PublicSurveyOut(
            id=s_row["id"],
            title=survey_title,
            description=survey_desc,
            instructions=survey_inst,
            public_slug=s_row["public_slug"],
            version=s_row["version"],
            questions=questions,
            available_languages=available_languages,
            current_language=current_lang
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

            # Kiểm tra xếp hạng ranking không trùng lặp
            if q_type == "ranking" and val is not None:
                if not isinstance(val, list):
                    errors.append(f"Câu hỏi xếp hạng '{q['title']}' phải là một danh sách thứ tự các mục.")
                elif len(val) != len(set(val)):
                    errors.append(f"Câu hỏi xếp hạng '{q['title']}' chứa các mục xếp hạng trùng lặp.")

            # Kiểm tra thang đo rating (1-5)
            if q_type == "rating" and val is not None and str(val).strip() != "":
                try:
                    r_val = float(val)
                    if r_val < 1 or r_val > 5:
                        errors.append(f"Câu hỏi đánh giá sao '{q['title']}' phải nằm trong thang điểm từ 1 đến 5.")
                except (ValueError, TypeError):
                    errors.append(f"Câu hỏi đánh giá sao '{q['title']}' yêu cầu điểm số hợp lệ.")

            # Kiểm tra thang đo tuyến tính linear_scale hoặc nps (0-10)
            if q_type in ("linear_scale", "nps") and val is not None and str(val).strip() != "":
                try:
                    s_val = float(val)
                    if s_val < 0 or s_val > 10:
                        errors.append(f"Câu hỏi thang điểm '{q['title']}' phải nằm trong khoảng từ 0 đến 10.")
                except (ValueError, TypeError):
                    errors.append(f"Câu hỏi thang điểm '{q['title']}' yêu cầu giá trị số hợp lệ.")

            # Giới hạn độ dài văn bản chống tràn dữ liệu / DoS
            if isinstance(val, str) and len(val) > 10000:
                errors.append(f"Câu trả lời cho '{q['title']}' vượt quá độ dài tối đa cho phép (10,000 ký tự).")

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
        arm_val = payload.experimental_arm or (payload.client_metadata or {}).get("experimental_arm", "")
        conn.execute("""
            INSERT INTO responses (
                id, survey_id, survey_version, started_at, submitted_at,
                duration_seconds, client_metadata_json, risk_score, risk_level,
                analysis_status, review_status, source, enumerator_id, experimental_arm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 'low', 'pending', 'unverified', ?, ?, ?)
        """, (
            response_id, survey_id, survey_version, started_at_iso, submitted_at_iso,
            duration, json.dumps(payload.client_metadata or {}), source_val, enum_val, arm_val
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
            SELECT id, enumerator_id, risk_score FROM responses 
            WHERE survey_id = ? AND id != ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
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
            quality_settings=quality_settings,
            client_metadata=payload.client_metadata
        )

        # 4.1. Kiểm tra hạn ngạch phân tầng (Sampling Quota Check)
        quota_rules = s_settings.get("quotas", [])
        if quota_rules:
            quota_counts: Dict[str, int] = {}
            for qr in quota_rules:
                cid = qr.get("id", f"{qr.get('question_id')}_{qr.get('target_value')}")
                quota_counts[cid] = 0

            for pr in prior_responses:
                p_ans = pr.get("answers", {})
                for qr in quota_rules:
                    cid = qr.get("id", f"{qr.get('question_id')}_{qr.get('target_value')}")
                    q_val = p_ans.get(qr.get("question_id"))
                    target_val = qr.get("target_value")
                    if isinstance(q_val, list) and target_val in q_val:
                        quota_counts[cid] = quota_counts.get(cid, 0) + 1
                    elif q_val is not None and str(q_val).strip() == str(target_val).strip():
                        quota_counts[cid] = quota_counts.get(cid, 0) + 1

            quota_eval = QuotaEngine.evaluate_quotas(payload.answers, quota_rules, quota_counts)
            if quota_eval["is_quota_full"]:
                if quota_eval["action"] == "screen_out":
                    conn.execute("""
                        UPDATE responses SET review_status = 'quota_screened_out', risk_level = 'medium'
                        WHERE id = ?
                    """, (response_id,))
                    return {
                        "response_id": response_id,
                        "status": "screen_out",
                        "message": "Hạn ngạch khảo sát cho nhóm nhân khẩu học này đã đủ số lượng nghiên cứu. Trân trọng cảm ơn sự quan tâm của bạn!",
                        "quota_reasons": quota_eval["reasons"],
                        "risk_score": 0.0,
                        "risk_level": "medium"
                    }
                else:
                    analysis["flags"].append({
                        "type": "QUOTA_OVERFLOW",
                        "message": "; ".join(quota_eval["reasons"]),
                        "severity": "medium",
                        "score_penalty": 0.0
                    })

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

        # Phát tán cảnh báo bất thường thời gian thực nếu khảo sát có cấu hình webhook
        WebhookEngine.async_dispatch_anomaly_alert(
            survey_settings=s_settings,
            survey_id=survey_id,
            response_id=response_id,
            risk_score=analysis["composite_score"],
            risk_level=analysis["risk_level"],
            flags=analysis["flags"],
            metadata=payload.client_metadata
        )

        return {
            "response_id": response_id,
            "message": "Phản hồi của bạn đã được ghi nhận thành công.",
            "status": "recorded",
            "risk_score": analysis["composite_score"],
            "risk_level": analysis["risk_level"]
        }

@router.post("/{slug_or_id}/batch-sync", response_model=BatchSyncResponseOut, status_code=200)
def batch_sync_responses(slug_or_id: str, payload: BatchResponseSubmit, request: Request):
    """
    Đồng bộ hàng loạt các phiếu khảo sát ngoại tuyến từ hàng đợi thiết bị của điều tra viên.
    Xử lý tất cả phiếu trong 1 transaction CSDL SQLite duy nhất, hỗ trợ idempotency tránh trùng lặp
    thông qua client_uuid, và kích hoạt đầy đủ 7 tầng kiểm định chất lượng (Quality Engine).
    """
    if not payload.responses:
        return BatchSyncResponseOut(
            success=True,
            total_received=0,
            synced_count=0,
            duplicates_skipped=0,
            error_count=0,
            results=[]
        )

    # Giới hạn số lượng tối đa 100 phiếu mỗi mẻ gửi để bảo vệ tài nguyên máy chủ
    if len(payload.responses) > 100:
        raise HTTPException(
            status_code=400,
            detail="Mỗi mẻ đồng bộ ngoại tuyến chỉ được chứa tối đa 100 phiếu khảo sát."
        )

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

        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        questions = [dict(q) for q in q_rows]
        for q in questions:
            q["options"] = json.loads(q.get("options_json") or "[]")
            q["logic_rules"] = json.loads(q.get("logic_rules_json") or "[]")

        s_settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() else {}
        quality_settings = s_settings.get("quality_settings", {})

        # Tải danh sách client_uuid đã tồn tại trong CSDL để đảm bảo idempotency
        existing_rows = conn.execute("""
            SELECT id, client_metadata_json, submitted_at, enumerator_id, risk_score
            FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        known_client_uuids: Dict[str, str] = {}
        for er in existing_rows:
            try:
                m = json.loads(er["client_metadata_json"] or "{}")
                c_uuid = m.get("client_uuid")
                if c_uuid:
                    known_client_uuids[str(c_uuid)] = er["id"]
            except Exception:
                pass

        # Tải toàn bộ response_answers của các phiếu trước để đối chiếu Hamming & Trùng lặp
        all_prior_ans = conn.execute("""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON r.id = ra.response_id
            WHERE r.survey_id = ?
        """, (survey_id,)).fetchall()

        ans_by_resp_id: Dict[str, Dict[str, Any]] = {}
        for a in all_prior_ans:
            raw_val = a["answer_value"]
            try:
                parsed_v = json.loads(raw_val)
            except Exception:
                parsed_v = raw_val
            ans_by_resp_id.setdefault(a["response_id"], {})[a["question_id"]] = parsed_v

        prior_responses: List[Dict[str, Any]] = []
        for er in existing_rows:
            prior_responses.append({
                "id": er["id"],
                "answers": ans_by_resp_id.get(er["id"], {}),
                "enumerator_id": er["enumerator_id"] if "enumerator_id" in er.keys() else "",
                "risk_score": er["risk_score"] if "risk_score" in er.keys() else 0.0
            })

        results: List[BatchSyncResultItem] = []
        synced_count = 0
        duplicates_skipped = 0
        error_count = 0

        for item in payload.responses:
            c_uuid = (item.client_uuid or "").strip()

            # 1. Kiểm tra Idempotency thông qua client_uuid
            if c_uuid and c_uuid in known_client_uuids:
                duplicates_skipped += 1
                results.append(BatchSyncResultItem(
                    client_uuid=c_uuid,
                    response_id=known_client_uuids[c_uuid],
                    status="skipped_duplicate",
                    message="Phiếu này đã được đồng bộ lên hệ thống trước đó (Idempotent)."
                ))
                continue

            # 2. Kiểm tra tính hợp lệ cơ bản
            item_errors = []
            for q in questions:
                qid = q["id"]
                val = item.answers.get(qid)
                is_req = bool(q["is_required"])

                if is_req:
                    if val is None or (isinstance(val, str) and not val.strip()):
                        item_errors.append(f"Câu hỏi bắt buộc '{q['title']}' chưa có câu trả lời.")
                    elif isinstance(val, list) and len(val) == 0:
                        item_errors.append(f"Câu hỏi bắt buộc '{q['title']}' chưa có phương án nào.")
                if isinstance(val, str) and len(val) > 10000:
                    item_errors.append(f"Câu trả lời cho '{q['title']}' vượt quá độ dài tối đa.")

            if item_errors:
                error_count += 1
                results.append(BatchSyncResultItem(
                    client_uuid=c_uuid,
                    status="error",
                    message="; ".join(item_errors[:2])
                ))
                continue

            # 3. Tính duration và thời gian
            start_dt = parse_iso(item.started_at)
            submit_dt = parse_iso(item.submitted_at)
            duration = max(0.0, (submit_dt - start_dt).total_seconds())

            response_id = str(uuid.uuid4())
            submitted_at_iso = submit_dt.isoformat()
            started_at_iso = start_dt.isoformat()

            item_meta = dict(item.client_metadata or {})
            if c_uuid:
                item_meta["client_uuid"] = c_uuid
            item_meta["sync_method"] = "offline_batch_sync"

            source_val = item.source or "offline_sync"
            enum_val = item.enumerator_id or ""

            # 4. Ghi nhận response vào SQLite
            conn.execute("""
                INSERT INTO responses (
                    id, survey_id, survey_version, started_at, submitted_at,
                    duration_seconds, client_metadata_json, risk_score, risk_level,
                    analysis_status, review_status, source, enumerator_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 'low', 'pending', 'unverified', ?, ?)
            """, (
                response_id, survey_id, survey_version, started_at_iso, submitted_at_iso,
                duration, json.dumps(item_meta, ensure_ascii=False), source_val, enum_val
            ))

            # 5. Ghi nhận response_answers
            ra_tuples = []
            for qid, val in item.answers.items():
                ans_str = json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else str(val)
                ra_tuples.append((str(uuid.uuid4()), response_id, qid, ans_str, submitted_at_iso))

            conn.executemany("""
                INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ra_tuples)

            # 6. Chạy QualityEngine
            analysis = QualityEngine.analyze_response(
                new_answers=item.answers,
                duration_seconds=duration,
                questions=questions,
                prior_responses=prior_responses,
                enumerator_id=enum_val,
                quality_settings=quality_settings,
                client_metadata=item.client_metadata
            )

            # 7. Lưu quality_assessments
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

            # 8. Cập nhật rủi ro cho response
            conn.execute("""
                UPDATE responses 
                SET risk_score = ?, risk_level = ?, analysis_status = 'analyzed'
                WHERE id = ?
            """, (analysis["composite_score"], analysis["risk_level"], response_id))

            # Cập nhật danh sách đối chiếu cho các phiếu tiếp theo trong cùng mẻ
            if c_uuid:
                known_client_uuids[c_uuid] = response_id

            prior_responses.append({
                "id": response_id,
                "answers": item.answers,
                "enumerator_id": enum_val,
                "risk_score": analysis["composite_score"]
            })

            if analysis["risk_level"] == "high" or analysis["composite_score"] >= WebhookEngine.RISK_ALERT_THRESHOLD:
                WebhookEngine.async_dispatch_anomaly_alert(
                    survey_settings=s_settings,
                    survey_id=survey_id,
                    response_id=response_id,
                    risk_score=analysis["composite_score"],
                    risk_level=analysis["risk_level"],
                    flags=analysis["flags"],
                    metadata=item.client_metadata
                )

            synced_count += 1
            results.append(BatchSyncResultItem(
                client_uuid=c_uuid,
                response_id=response_id,
                status="synced",
                risk_score=analysis["composite_score"],
                risk_level=analysis["risk_level"],
                message="Đồng bộ và kiểm định thành công."
            ))

        # Ghi nhật ký vào chuỗi băm bất biến nếu có phiếu được đồng bộ
        if synced_count > 0:
            record_audit_log(
                conn, 'survey', survey_id, 'OFFLINE_BATCH_SYNC',
                {
                    "synced_count": synced_count,
                    "duplicates_skipped": duplicates_skipped,
                    "error_count": error_count,
                    "total_received": len(payload.responses)
                }
            )

        return BatchSyncResponseOut(
            success=True,
            total_received=len(payload.responses),
            synced_count=synced_count,
            duplicates_skipped=duplicates_skipped,
            error_count=error_count,
            results=results
        )

