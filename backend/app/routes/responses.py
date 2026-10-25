import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple, Set
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db, record_audit_log
from app.schemas import (
    ResponseListItemOut, ResponseDetailOut, QualityAssessmentOut,
    ReviewStatusUpdate, BatchReviewRequest, QuestionOut,
    DataCleansingCriteria, DataCleansingReport, DataCleansingApplyResult,
    BatchAnomalyQuarantineRequest, BatchAnomalyQuarantineResult,
    BatchAnomalyQuarantineItem, BatchRestoreQuarantineRequest, BatchRestoreQuarantineResult
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
                flags_summary=flag_msgs,
                source=r["source"] if "source" in r.keys() and r["source"] else "online_form",
                enumerator_id=r["enumerator_id"] if "enumerator_id" in r.keys() and r["enumerator_id"] else "",
                omr_confidence=float(r["omr_confidence"]) if "omr_confidence" in r.keys() and r["omr_confidence"] is not None else 1.0
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
                score_enum=round(qa_row["score_enum"], 1) if "score_enum" in qa_row.keys() and qa_row["score_enum"] is not None else 0.0,
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
            assessment=assessment,
            source=r_row["source"] if "source" in r_row.keys() and r_row["source"] else "online_form",
            enumerator_id=r_row["enumerator_id"] if "enumerator_id" in r_row.keys() and r_row["enumerator_id"] else "",
            paper_form_id=r_row["paper_form_id"] if "paper_form_id" in r_row.keys() and r_row["paper_form_id"] else "",
            scan_image_url=r_row["scan_image_url"] if "scan_image_url" in r_row.keys() and r_row["scan_image_url"] else "",
            omr_confidence=float(r_row["omr_confidence"]) if "omr_confidence" in r_row.keys() and r_row["omr_confidence"] is not None else 1.0
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

        record_audit_log(conn, 'verification', response_id, 'REVIEW_DECISION', {
            "status": payload.review_status,
            "notes": payload.review_notes
        }, current_time)

    return {"message": "Cập nhật quyết định xác minh thành công.", "review_status": payload.review_status}

@router.post("/batch-review")
def update_batch_review_decisions(survey_id: str, payload: BatchReviewRequest):
    """
    Cập nhật quyết định thẩm định hàng loạt cho nhiều phản hồi:
    - Kiểm tra tính hợp lệ của trạng thái và danh sách response_ids.
    - Cập nhật nguyên tử (Atomic batch execution) và ghi nhật ký chuỗi băm bất biến cho từng phản hồi.
    """
    valid_statuses = ("unverified", "under_review", "verified_valid", "verified_fraud", "inconclusive")
    if payload.review_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Trạng thái không hợp lệ. Phải là một trong: {valid_statuses}")

    if not payload.response_ids:
        raise HTTPException(status_code=400, detail="Danh sách mã phản hồi không được để trống.")

    current_time = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Lấy danh sách ID thực sự thuộc survey_id để đảm bảo an toàn phân quyền
        placeholders = ",".join(["?"] * len(payload.response_ids))
        valid_rows = conn.execute(
            f"SELECT id FROM responses WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + payload.response_ids
        ).fetchall()
        valid_ids = [r["id"] for r in valid_rows]

        if not valid_ids:
            raise HTTPException(status_code=404, detail="Không tìm thấy phản hồi hợp lệ nào thuộc khảo sát này.")

        update_params = [(payload.review_status, payload.review_notes or "", current_time, rid) for rid in valid_ids]
        conn.executemany("""
            UPDATE responses 
            SET review_status = ?, review_notes = ?, reviewed_at = ?
            WHERE id = ?
        """, update_params)

        for rid in valid_ids:
            record_audit_log(conn, 'verification', rid, 'REVIEW_DECISION', {
                "status": payload.review_status,
                "notes": payload.review_notes,
                "batch": True
            }, current_time)

    return {
        "message": f"Đã cập nhật quyết định xác minh cho {len(valid_ids)} phản hồi.",
        "updated_count": len(valid_ids),
        "review_status": payload.review_status
    }


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
            "resp1_meta": {
                "source": r1["source"] if "source" in r1.keys() and r1["source"] else "online_form",
                "enumerator_id": r1["enumerator_id"] if "enumerator_id" in r1.keys() and r1["enumerator_id"] else "",
                "risk_level": r1["risk_level"],
                "review_status": r1["review_status"],
                "submitted_at": r1["submitted_at"],
                "duration_seconds": round(r1["duration_seconds"], 1) if r1["duration_seconds"] is not None else 0.0
            },
            "resp2_meta": {
                "source": r2["source"] if "source" in r2.keys() and r2["source"] else "online_form",
                "enumerator_id": r2["enumerator_id"] if "enumerator_id" in r2.keys() and r2["enumerator_id"] else "",
                "risk_level": r2["risk_level"],
                "review_status": r2["review_status"],
                "submitted_at": r2["submitted_at"],
                "duration_seconds": round(r2["duration_seconds"], 1) if r2["duration_seconds"] is not None else 0.0
            },
            "total_questions_compared": total_compared,
            "matching_answers_count": matching_count,
            "similarity_percentage": round(similarity * 100, 1),
            "questions_comparison": comparison
        }

@router.post("/re-analyze")
def reanalyze_all_responses(survey_id: str):
    """
    Tái phân tích toàn bộ phản hồi của cuộc khảo sát:
    Áp dụng các cấu hình nhạy cảm mới nhất và thuật toán mở rộng (Đường chéo, Zíc-zắc, Sàng lọc ĐTV).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        settings = json.loads(s_row["settings_json"] or "{}")
        quality_settings = settings.get("quality_settings", {})

        q_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()
        questions = [dict(q) for q in q_rows]
        for q in questions:
            q["options"] = json.loads(q.get("options_json") or "[]")
            q["logic_rules"] = json.loads(q.get("logic_rules_json") or "[]")

        resp_rows = conn.execute("SELECT * FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()
        if not resp_rows:
            return {
                "survey_id": survey_id,
                "total_reanalyzed": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "message": "Không có phản hồi nào để phân tích."
            }

        # Tối ưu hóa: Tải trước toàn bộ câu trả lời trong 1 truy vấn duy nhất (Tránh N+1)
        all_ans_rows = conn.execute("""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON r.id = ra.response_id
            WHERE r.survey_id = ?
        """, (survey_id,)).fetchall()
        
        all_answers = {}
        for a in all_ans_rows:
            rid = a["response_id"]
            raw_v = a["answer_value"]
            try:
                parsed_v = json.loads(raw_v)
            except Exception:
                parsed_v = raw_v
            all_answers.setdefault(rid, {})[a["question_id"]] = parsed_v

        counts = {"high": 0, "medium": 0, "low": 0}
        now_ts = now_iso()
        qa_inserts = []
        resp_updates = []

        # Xóa toàn bộ quality_assessments cũ của cuộc khảo sát trong 1 câu lệnh duy nhất
        conn.execute("""
            DELETE FROM quality_assessments 
            WHERE response_id IN (SELECT id FROM responses WHERE survey_id = ?)
        """, (survey_id,))

        for r in resp_rows:
            rid = r["id"]
            dur = r["duration_seconds"] or 0.0
            enum_id = r["enumerator_id"] if "enumerator_id" in r.keys() else ""
            my_answers = all_answers.get(rid, {})

            # Tập đối chiếu
            priors = []
            for other_r in resp_rows:
                if other_r["id"] != rid:
                    priors.append({
                        "id": other_r["id"],
                        "answers": all_answers.get(other_r["id"], {}),
                        "enumerator_id": other_r["enumerator_id"] if "enumerator_id" in other_r.keys() else "",
                        "risk_score": other_r["risk_score"] or 0.0
                    })

            analysis = QualityEngine.analyze_response(
                new_answers=my_answers,
                duration_seconds=dur,
                questions=questions,
                prior_responses=priors,
                enumerator_id=enum_id,
                quality_settings=quality_settings
            )

            risk_lvl = analysis["risk_level"]
            counts[risk_lvl] = counts.get(risk_lvl, 0) + 1

            resp_updates.append((analysis["composite_score"], risk_lvl, rid))

            qa_inserts.append((
                str(uuid.uuid4()), rid,
                analysis["score_dup"], analysis["score_pattern"], analysis["score_logic"],
                analysis["score_speed"], analysis["score_text"], analysis.get("score_enum", 0.0),
                analysis["composite_score"],
                json.dumps(analysis["flags"], ensure_ascii=False),
                analysis.get("closest_match_response_id"), analysis.get("highest_similarity", 0.0),
                now_ts
            ))

        # Cập nhật hàng loạt (Batch Executemany)
        conn.executemany("""
            UPDATE responses
            SET risk_score = ?, risk_level = ?, analysis_status = 'completed'
            WHERE id = ?
        """, resp_updates)

        conn.executemany("""
            INSERT INTO quality_assessments (
                id, response_id, score_dup, score_pattern, score_logic, score_speed, score_text, score_enum,
                composite_score, flags_json, closest_match_response_id, highest_similarity, assessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, qa_inserts)

        return {
            "survey_id": survey_id,
            "total_reanalyzed": len(resp_rows),
            "high_risk_count": counts.get("high", 0),
            "medium_risk_count": counts.get("medium", 0),
            "low_risk_count": counts.get("low", 0),
            "quality_sensitivity": quality_settings.get("sensitivity", "standard"),
            "message": f"Đã tái phân tích thành công {len(resp_rows)} phản hồi."
        }

def _extract_anomaly_sets(survey_id: str, criteria_dict: Dict[str, Any]) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """
    Trích xuất các tập response_id vi phạm mạng lưới thông đồng (Collusion Syndicate Rings)
    hoặc gian lận không gian (Coffee-shop clusters, Impossible Travel, Geofence breach).
    """
    syndicate_ids: Set[str] = set()
    coffee_shop_ids: Set[str] = set()
    impossible_travel_ids: Set[str] = set()
    geofence_breach_ids: Set[str] = set()

    if criteria_dict.get("exclude_collusion_syndicates", True):
        try:
            from app.engine.similarity_engine import SimilarityEngine
            sim_res = SimilarityEngine.analyze_survey_similarity(survey_id=survey_id)
            for ring in sim_res.get("collusion_rings", []):
                for rid in ring.get("response_ids", []):
                    syndicate_ids.add(rid)
        except Exception:
            pass

    need_spatial = (
        criteria_dict.get("exclude_coffee_shop_congregations", True) or
        criteria_dict.get("exclude_impossible_travel", True) or
        criteria_dict.get("exclude_geofence_violations", False)
    )
    if need_spatial:
        try:
            from app.engine.spatial_engine import SpatialEngine
            spat_res = SpatialEngine.analyze_survey_spatial(survey_id=survey_id)
            if criteria_dict.get("exclude_coffee_shop_congregations", True):
                for cl in spat_res.get("clusters", []):
                    if cl.get("is_coffee_shop_congregation"):
                        for rid in cl.get("response_ids", []):
                            coffee_shop_ids.add(rid)
            if criteria_dict.get("exclude_impossible_travel", True):
                for sp in spat_res.get("speed_anomalies", []):
                    if sp.get("response_a_id"):
                        impossible_travel_ids.add(sp["response_a_id"])
                    if sp.get("response_b_id"):
                        impossible_travel_ids.add(sp["response_b_id"])
            if criteria_dict.get("exclude_geofence_violations", False):
                for gb in spat_res.get("geofence_breaches", []):
                    if gb.get("response_id"):
                        geofence_breach_ids.add(gb["response_id"])
        except Exception:
            pass

    return syndicate_ids, coffee_shop_ids, impossible_travel_ids, geofence_breach_ids

@router.post("/cleansing/preview", response_model=DataCleansingReport)
def preview_data_cleansing(survey_id: str, criteria: DataCleansingCriteria):
    """
    Mô phỏng trước tác động của quy trình làm sạch dữ liệu tự động (Exclusion Criteria Preview).
    Tính toán số lượng phiếu bị loại theo từng quy tắc, so sánh thời gian làm bài, điểm rủi ro
    và kiểm định sự cải thiện của hệ số Cronbach's Alpha thang đo trước vs sau khi làm sạch.
    Không ghi nhận thay đổi vào CSDL.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT id, duration_seconds, risk_score, source, enumerator_id, omr_confidence
            FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        responses = [dict(r) for r in resp_rows]
        if not responses:
            return DataCleansingReport(
                survey_id=survey_id,
                total_responses=0,
                clean_responses_count=0,
                clean_percentage=100.0,
                flagged_speeders=0,
                flagged_straightlining=0,
                flagged_contradictions=0,
                flagged_high_risk=0,
                flagged_low_omr=0,
                overlap_count=0,
                pre_avg_duration=0.0,
                post_avg_duration=0.0,
                pre_avg_risk=0.0,
                post_avg_risk=0.0,
                cronbach_alpha_pre=None,
                cronbach_alpha_post=None,
                applied_criteria=criteria,
                flagged_collusion_syndicates=0,
                flagged_coffee_shop=0,
                flagged_impossible_travel=0,
                flagged_geofence_violations=0
            )

        # Lấy quality_assessments để đọc flags
        qa_rows = conn.execute("""
            SELECT response_id, flags_json FROM quality_assessments
            WHERE response_id IN (SELECT id FROM responses WHERE survey_id = ?)
        """, (survey_id,)).fetchall()

        assessments_by_resp = {}
        for qa in qa_rows:
            try:
                flags = json.loads(qa["flags_json"] or "[]")
            except Exception:
                flags = []
            assessments_by_resp[qa["response_id"]] = {"flags": flags}

        # Đánh giá các quy tắc làm sạch
        criteria_dict = criteria.model_dump() if hasattr(criteria, "model_dump") else criteria.dict()
        syn_ids, cs_ids, imp_ids, geo_ids = _extract_anomaly_sets(survey_id, criteria_dict)
        eval_res = QualityEngine.evaluate_cleansing_rules(
            responses=responses,
            assessments_by_resp=assessments_by_resp,
            criteria=criteria_dict,
            syndicate_response_ids=syn_ids,
            coffee_shop_response_ids=cs_ids,
            impossible_travel_response_ids=imp_ids,
            geofence_violation_response_ids=geo_ids
        )

        clean_set = set(eval_res["clean_ids"])

        # Tính toán thời gian trung bình
        pre_durs = [r["duration_seconds"] for r in responses if r["duration_seconds"] > 0]
        post_durs = [r["duration_seconds"] for r in responses if r["id"] in clean_set and r["duration_seconds"] > 0]
        pre_avg_dur = round(sum(pre_durs) / len(pre_durs), 1) if pre_durs else 0.0
        post_avg_dur = round(sum(post_durs) / len(post_durs), 1) if post_durs else 0.0

        # Tính toán điểm rủi ro trung bình
        pre_risks = [r["risk_score"] for r in responses]
        post_risks = [r["risk_score"] for r in responses if r["id"] in clean_set]
        pre_avg_risk = round(sum(pre_risks) / len(pre_risks), 1) if pre_risks else 0.0
        post_avg_risk = round(sum(post_risks) / len(post_risks), 1) if post_risks else 0.0

        # Tìm các câu hỏi thang đo để tính Cronbach's Alpha
        scale_q_rows = conn.execute("""
            SELECT id FROM questions
            WHERE survey_id = ? AND question_type IN ('rating', 'linear_scale', 'likert', 'nps')
            ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        scale_q_ids = [q["id"] for q in scale_q_rows]
        cronbach_pre = None
        cronbach_post = None

        if len(scale_q_ids) >= 2:
            # Tải câu trả lời cho các câu hỏi thang đo
            ans_rows = conn.execute("""
                SELECT ra.response_id, ra.question_id, ra.answer_value
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                WHERE r.survey_id = ? AND ra.question_id IN ({})
            """.format(",".join("?" for _ in scale_q_ids)), [survey_id] + scale_q_ids).fetchall()

            ans_map = {}
            for a in ans_rows:
                try:
                    val = float(str(a["answer_value"]).strip())
                    ans_map.setdefault(a["response_id"], {})[a["question_id"]] = val
                except (ValueError, TypeError):
                    pass

            pre_matrix = []
            post_matrix = []
            for r in responses:
                rid = r["id"]
                row_ans = ans_map.get(rid, {})
                if len(row_ans) == len(scale_q_ids):
                    row_vec = [row_ans[qid] for qid in scale_q_ids]
                    pre_matrix.append(row_vec)
                    if rid in clean_set:
                        post_matrix.append(row_vec)

            cronbach_pre = QualityEngine.compute_cronbach_alpha(pre_matrix)
            cronbach_post = QualityEngine.compute_cronbach_alpha(post_matrix)

        return DataCleansingReport(
            survey_id=survey_id,
            total_responses=eval_res["total_evaluated"],
            clean_responses_count=eval_res["clean_count"],
            clean_percentage=eval_res["clean_percentage"],
            flagged_speeders=eval_res["flagged_speeders"],
            flagged_straightlining=eval_res["flagged_straightlining"],
            flagged_contradictions=eval_res["flagged_contradictions"],
            flagged_high_risk=eval_res["flagged_high_risk"],
            flagged_low_omr=eval_res["flagged_low_omr"],
            overlap_count=eval_res["overlap_count"],
            pre_avg_duration=pre_avg_dur,
            post_avg_duration=post_avg_dur,
            pre_avg_risk=pre_avg_risk,
            post_avg_risk=post_avg_risk,
            cronbach_alpha_pre=cronbach_pre,
            cronbach_alpha_post=cronbach_post,
            applied_criteria=criteria,
            flagged_collusion_syndicates=eval_res.get("flagged_collusion_syndicates", 0),
            flagged_coffee_shop=eval_res.get("flagged_coffee_shop", 0),
            flagged_impossible_travel=eval_res.get("flagged_impossible_travel", 0),
            flagged_geofence_violations=eval_res.get("flagged_geofence_violations", 0)
        )

@router.post("/cleansing/apply", response_model=DataCleansingApplyResult)
def apply_data_cleansing(survey_id: str, criteria: DataCleansingCriteria):
    """
    Thực thi áp dụng quy trình làm sạch dữ liệu tự động lên toàn bộ phản hồi của cuộc khảo sát.
    Tự động cập nhật review_status = 'verified_fraud' đối với các phiếu vi phạm quy tắc làm sạch,
    kèm theo lý do loại trừ chi tiết. Tự động gắn nhãn 'verified_valid' cho mẫu sạch chưa duyệt.
    Ghi nhật ký kiểm toán bất biến SHA-256 vào ledger.
    """
    now_ts = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT id, duration_seconds, risk_score, source, enumerator_id, omr_confidence, review_status
            FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        responses = [dict(r) for r in resp_rows]
        if not responses:
            return DataCleansingApplyResult(
                success=True,
                survey_id=survey_id,
                applied_count=0,
                rejected_count=0,
                verified_clean_count=0,
                audit_log_id="",
                timestamp=now_ts
            )

        qa_rows = conn.execute("""
            SELECT response_id, flags_json FROM quality_assessments
            WHERE response_id IN (SELECT id FROM responses WHERE survey_id = ?)
        """, (survey_id,)).fetchall()

        assessments_by_resp = {}
        for qa in qa_rows:
            try:
                flags = json.loads(qa["flags_json"] or "[]")
            except Exception:
                flags = []
            assessments_by_resp[qa["response_id"]] = {"flags": flags}

        criteria_dict = criteria.model_dump() if hasattr(criteria, "model_dump") else criteria.dict()
        syn_ids, cs_ids, imp_ids, geo_ids = _extract_anomaly_sets(survey_id, criteria_dict)
        eval_res = QualityEngine.evaluate_cleansing_rules(
            responses=responses,
            assessments_by_resp=assessments_by_resp,
            criteria=criteria_dict,
            syndicate_response_ids=syn_ids,
            coffee_shop_response_ids=cs_ids,
            impossible_travel_response_ids=imp_ids,
            geofence_violation_response_ids=geo_ids
        )

        reject_updates = []
        for rid, reasons in eval_res["rejected_reasons"].items():
            notes = f"[DataTrust Cleansing] Loại trừ theo tiêu chuẩn: {'; '.join(reasons)}"
            reject_updates.append(("verified_fraud", notes, now_ts, rid))

        clean_updates = []
        for rid in eval_res["clean_ids"]:
            clean_updates.append(("verified_valid", "[DataTrust Cleansing] Đạt toàn bộ tiêu chuẩn dữ liệu sạch", now_ts, rid))

        if reject_updates:
            conn.executemany("""
                UPDATE responses
                SET review_status = ?, review_notes = ?, reviewed_at = ?
                WHERE id = ?
            """, reject_updates)

        if clean_updates:
            conn.executemany("""
                UPDATE responses
                SET review_status = ?, review_notes = ?, reviewed_at = ?
                WHERE id = ? AND review_status = 'unverified'
            """, clean_updates)

        # Ghi nhật ký vào chuỗi băm bất biến
        audit_res = record_audit_log(
            conn, 'survey', survey_id, 'DATA_CLEANSING_APPLIED',
            {
                "total_evaluated": len(responses),
                "rejected_count": len(reject_updates),
                "verified_clean_count": len(clean_updates),
                "criteria": criteria_dict
            },
            now_ts
        )

        return DataCleansingApplyResult(
            success=True,
            survey_id=survey_id,
            applied_count=len(responses),
            rejected_count=len(reject_updates),
            verified_clean_count=len(clean_updates),
            audit_log_id=audit_res["id"],
            timestamp=now_ts
        )

@router.post("/batch-quarantine-anomalies", response_model=BatchAnomalyQuarantineResult)
def batch_quarantine_anomalies(survey_id: str, payload: BatchAnomalyQuarantineRequest = BatchAnomalyQuarantineRequest()):
    """
    Quy trình cách ly và gắn cờ gian lận hàng loạt tự động (Automated Batch Anomaly Quarantine):
    - Quét mạng lưới thông đồng (Collusion Syndicate Rings)
    - Quét cụm tọa độ GPS tĩnh bất thường nghi vấn ngồi quán cà phê (Coffee-Shop Congregation Fraud)
    - Quét vận tốc di chuyển phi thực tế / GPS giả mạo (Impossible Travel > 120 km/h)
    - Quét vi phạm ranh giới địa lý cấp phép (Geofence Breaches)
    - Quét người trả lời siêu tốc (Speeders) và hoa văn rập khuôn (Straightlining)
    - Hỗ trợ chế độ dry_run mô phỏng trước tác động mà không thay đổi CSDL
    - Ghi nhận nhật ký kiểm toán bất biến SHA-256 vào ledger
    """
    now_ts = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT id, duration_seconds, risk_score, source, enumerator_id, omr_confidence, review_status, client_metadata_json, submitted_at
            FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        responses = [dict(r) for r in resp_rows]
        if not responses:
            return BatchAnomalyQuarantineResult(
                success=True,
                survey_id=survey_id,
                dry_run=payload.dry_run,
                total_evaluated=0,
                quarantined_count=0,
                reasons_breakdown={},
                items=[],
                audit_log_id=None,
                timestamp=now_ts
            )

        # Lấy quality_assessments để đọc flags
        qa_rows = conn.execute("""
            SELECT response_id, flags_json FROM quality_assessments
            WHERE response_id IN (SELECT id FROM responses WHERE survey_id = ?)
        """, (survey_id,)).fetchall()

        assessments_by_resp = {}
        for qa in qa_rows:
            try:
                flags = json.loads(qa["flags_json"] or "[]")
            except Exception:
                flags = []
            assessments_by_resp[qa["response_id"]] = {"flags": flags}

        # Trích xuất các tập bất thường không gian và tương đồng
        criteria_proxy = {
            "exclude_collusion_syndicates": payload.quarantine_syndicates,
            "exclude_coffee_shop_congregations": payload.quarantine_coffee_shop,
            "exclude_impossible_travel": payload.quarantine_impossible_velocity,
            "exclude_geofence_violations": payload.quarantine_geofence_violations
        }
        syn_ids, cs_ids, imp_ids, geo_ids = _extract_anomaly_sets(survey_id, criteria_proxy)

        quarantined_items: List[BatchAnomalyQuarantineItem] = []
        breakdown: Dict[str, int] = {
            "collusion_syndicate": 0,
            "coffee_shop_congregation": 0,
            "impossible_travel": 0,
            "geofence_breach": 0,
            "speeder": 0,
            "straightlining": 0,
            "high_risk_score": 0
        }

        pattern_flags = {"FLAG_STRAIGHTLINING", "FLAG_DIAGONAL_PATTERN", "FLAG_ZIGZAG_PATTERN"}

        for r in responses:
            rid = r["id"]
            dur = float(r.get("duration_seconds") or 0.0)
            risk = float(r.get("risk_score") or 0.0)
            cur_status = r.get("review_status") or "unverified"
            qa = assessments_by_resp.get(rid, {})
            flags = qa.get("flags", [])
            flag_codes = {f.get("code") for f in flags if isinstance(f, dict)}

            reasons: List[str] = []

            # 1. Collusion syndicate
            if payload.quarantine_syndicates and ((rid in syn_ids) or ("FLAG_COLLUSION_SUSPECT" in flag_codes)):
                reasons.append("Thuộc mạng lưới thông đồng sao chép (Collusion Syndicate Ring)")
                breakdown["collusion_syndicate"] += 1

            # 2. Coffee-shop congregation
            if payload.quarantine_coffee_shop and (rid in cs_ids):
                reasons.append("Cụm GPS tĩnh nghi vấn quán cà phê (Coffee-Shop Congregation Fraud)")
                breakdown["coffee_shop_congregation"] += 1

            # 3. Impossible travel velocity
            if payload.quarantine_impossible_velocity and ((rid in imp_ids) or ("FLAG_GPS_SPOOFING" in flag_codes)):
                reasons.append("Vận tốc di chuyển phi thực tế / GPS giả mạo (> 120 km/h)")
                breakdown["impossible_travel"] += 1

            # 4. Geofence violation
            if payload.quarantine_geofence_violations and (rid in geo_ids):
                reasons.append("Thu thập ngoài ranh giới địa bàn được cấp phép (Geofence Breach)")
                breakdown["geofence_breach"] += 1

            # 5. Speeder
            if payload.quarantine_speeders and ((dur > 0 and dur < 10.0) or ("FLAG_SPEEDING" in flag_codes)):
                reasons.append(f"Tốc độ nộp bài quá nhanh ({dur:.1f}s)")
                breakdown["speeder"] += 1

            # 6. Straightlining
            if payload.quarantine_straightlining and bool(flag_codes.intersection(pattern_flags)):
                reasons.append("Hoa văn trả lời rập khuôn / thẳng hàng (Straightlining)")
                breakdown["straightlining"] += 1

            # 7. Min risk score
            if payload.min_risk_score is not None and risk >= payload.min_risk_score:
                reasons.append(f"Điểm rủi ro tổng hợp cao ({risk:.1f}/100 >= {payload.min_risk_score:.1f})")
                breakdown["high_risk_score"] += 1

            if reasons:
                quarantined_items.append(BatchAnomalyQuarantineItem(
                    response_id=rid,
                    enumerator_id=r.get("enumerator_id"),
                    duration_seconds=dur,
                    risk_score=risk,
                    reasons=reasons,
                    previous_status=cur_status,
                    new_status=payload.action
                ))

        audit_id = None
        if not payload.dry_run and quarantined_items:
            updates = []
            for item in quarantined_items:
                note = payload.custom_note or f"[DataTrust Anomaly Quarantine] Cách ly tự động: {'; '.join(item.reasons)}"
                updates.append((payload.action, note, now_ts, item.response_id))

            conn.executemany("""
                UPDATE responses
                SET review_status = ?, review_notes = ?, reviewed_at = ?
                WHERE id = ?
            """, updates)

            audit_res = record_audit_log(
                conn, 'survey', survey_id, 'BATCH_ANOMALIES_QUARANTINED',
                {
                    "total_evaluated": len(responses),
                    "quarantined_count": len(quarantined_items),
                    "action": payload.action,
                    "reasons_breakdown": breakdown,
                    "quarantined_ids": [item.response_id for item in quarantined_items]
                },
                now_ts
            )
            audit_id = audit_res["id"]

        active_breakdown = {k: v for k, v in breakdown.items() if v > 0}

        return BatchAnomalyQuarantineResult(
            success=True,
            survey_id=survey_id,
            dry_run=payload.dry_run,
            total_evaluated=len(responses),
            quarantined_count=len(quarantined_items),
            reasons_breakdown=active_breakdown,
            items=quarantined_items,
            audit_log_id=audit_id,
            timestamp=now_ts
        )

@router.post("/batch-restore-quarantined", response_model=BatchRestoreQuarantineResult)
def batch_restore_quarantined(survey_id: str, payload: BatchRestoreQuarantineRequest = BatchRestoreQuarantineRequest()):
    """
    Phục hồi phản hồi đã bị cách ly hoặc gắn cờ gian lận (Reversible Quarantine Rollback):
    - Cho phép hoàn tác về trạng thái 'unverified' hoặc 'verified_valid'
    - Ghi nhận nhật ký kiểm toán bất biến SHA-256 vào ledger minh bạch
    """
    now_ts = now_iso()
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if payload.response_ids:
            placeholders = ",".join("?" for _ in payload.response_ids)
            query = f"SELECT id FROM responses WHERE survey_id = ? AND id IN ({placeholders})"
            rows = conn.execute(query, [survey_id] + payload.response_ids).fetchall()
        else:
            rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status IN ('verified_fraud', 'quarantined')
            """, (survey_id,)).fetchall()

        restored_ids = [r["id"] for r in rows]
        if restored_ids:
            note = f"[DataTrust Rollback] {payload.reason or 'Phục hồi sau thẩm tra kiểm toán'}"
            updates = [(payload.restore_to_status, note, now_ts, rid) for rid in restored_ids]
            conn.executemany("""
                UPDATE responses
                SET review_status = ?, review_notes = ?, reviewed_at = ?
                WHERE id = ?
            """, updates)

        audit_res = record_audit_log(
            conn, 'survey', survey_id, 'BATCH_ANOMALIES_RESTORED',
            {
                "restored_count": len(restored_ids),
                "restore_to_status": payload.restore_to_status,
                "reason": payload.reason,
                "restored_ids": restored_ids
            },
            now_ts
        )

        return BatchRestoreQuarantineResult(
            success=True,
            survey_id=survey_id,
            restored_count=len(restored_ids),
            restored_ids=restored_ids,
            audit_log_id=audit_res["id"],
            timestamp=now_ts
        )

