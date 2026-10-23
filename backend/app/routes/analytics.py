import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.schemas import SurveyAnalyticsOut, QuestionStats
from app.engine.quality_engine import QualityEngine

router = APIRouter(prefix="/api/surveys/{survey_id}/analytics", tags=["Analytics"])

@router.get("", response_model=SurveyAnalyticsOut)
def get_survey_analytics(survey_id: str):
    """Tính toán thống kê thực từ cơ sở dữ liệu cho cuộc khảo sát"""
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT * FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        total_responses = len(resp_rows)
        is_sufficient = total_responses >= 5
        notice = None if is_sufficient else f"Cỡ mẫu hiện tại (N = {total_responses}) chưa đạt ngưỡng tối thiểu N >= 5 để đảm bảo độ tin cậy thống kê tổng thể."

        avg_dur = 0.0
        risk_dist = {"low": 0, "medium": 0, "high": 0}
        review_dist = {"unverified": 0, "under_review": 0, "verified_valid": 0, "verified_fraud": 0, "inconclusive": 0}

        if total_responses > 0:
            durations = [r["duration_seconds"] for r in resp_rows if r["duration_seconds"] > 0]
            avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0

            for r in resp_rows:
                lvl = r["risk_level"] or "low"
                risk_dist[lvl] = risk_dist.get(lvl, 0) + 1
                
                rev = r["review_status"] or "unverified"
                review_dist[rev] = review_dist.get(rev, 0) + 1

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        questions_analytics = []
        for q in q_rows:
            qid = q["id"]
            q_type = q["question_type"]
            options = json.loads(q["options_json"] or "[]")
            
            # Đọc tất cả câu trả lời cho câu hỏi này
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                WHERE ra.question_id = ? AND r.survey_id = ?
            """, (qid, survey_id)).fetchall()

            total_ans = len(ans_rows)
            opt_dist = None
            stats_sum = None
            text_samples = None

            if q_type in ("single_choice", "dropdown", "likert"):
                # Tạo map từ id sang label
                id_to_label = {opt.get("id"): opt.get("label") for opt in options if isinstance(opt, dict)}
                counts = {opt.get("label", opt.get("id")): 0 for opt in options if isinstance(opt, dict)}
                
                for a in ans_rows:
                    raw = a["answer_value"]
                    val = id_to_label.get(raw, raw)
                    counts[val] = counts.get(val, 0) + 1
                opt_dist = counts

            elif q_type == "multiple_choice":
                id_to_label = {opt.get("id"): opt.get("label") for opt in options if isinstance(opt, dict)}
                counts = {opt.get("label", opt.get("id")): 0 for opt in options if isinstance(opt, dict)}
                
                for a in ans_rows:
                    raw = a["answer_value"]
                    try:
                        selected = json.loads(raw)
                        if isinstance(selected, list):
                            for s in selected:
                                label = id_to_label.get(s, s)
                                counts[label] = counts.get(label, 0) + 1
                        else:
                            label = id_to_label.get(raw, raw)
                            counts[label] = counts.get(label, 0) + 1
                    except Exception:
                        label = id_to_label.get(raw, raw)
                        counts[label] = counts.get(label, 0) + 1
                opt_dist = counts

            elif q_type in ("linear_scale", "number"):
                nums = []
                for a in ans_rows:
                    try:
                        nums.append(float(a["answer_value"]))
                    except Exception:
                        pass
                if nums:
                    stats_sum = {
                        "min": min(nums),
                        "max": max(nums),
                        "avg": round(sum(nums) / len(nums), 2),
                        "count": len(nums)
                    }
                    # Phân bố tần suất theo số nguyên
                    num_counts = {}
                    for n in nums:
                        k = str(int(n) if n.is_integer() else n)
                        num_counts[k] = num_counts.get(k, 0) + 1
                    opt_dist = num_counts

            elif q_type == "matrix":
                matrix_rows = options.get("rows", []) if isinstance(options, dict) else []
                matrix_cols = options.get("columns", []) if isinstance(options, dict) else []
                row_map = {
                    (r.get("id") if isinstance(r, dict) else str(r)): (r.get("label") if isinstance(r, dict) else str(r))
                    for r in matrix_rows
                }
                col_map = {
                    (c.get("id") if isinstance(c, dict) else str(c)): (c.get("label") if isinstance(c, dict) else str(c))
                    for c in matrix_cols
                }
                
                # Matrix distribution: row_label -> { col_label -> count }
                matrix_dist = {}
                for r_label in row_map.values():
                    matrix_dist[r_label] = {c_label: 0 for c_label in col_map.values()}
                
                for a in ans_rows:
                    try:
                        val_dict = json.loads(a["answer_value"])
                        if isinstance(val_dict, dict):
                            for r_id, c_id in val_dict.items():
                                r_label = row_map.get(r_id, r_id)
                                c_label = col_map.get(c_id, c_id)
                                if r_label not in matrix_dist:
                                    matrix_dist[r_label] = {}
                                matrix_dist[r_label][c_label] = matrix_dist[r_label].get(c_label, 0) + 1
                    except Exception:
                        pass
                stats_sum = {"matrix_distribution": matrix_dist}

            elif q_type == "ranking":
                item_map = {
                    (opt.get("id") if isinstance(opt, dict) else str(opt)): (opt.get("label") if isinstance(opt, dict) else str(opt))
                    for opt in (options if isinstance(options, list) else [])
                }
                rank_positions = {label: [] for label in item_map.values()}
                
                for a in ans_rows:
                    try:
                        ranked_list = json.loads(a["answer_value"])
                        if isinstance(ranked_list, list):
                            for pos, item_id in enumerate(ranked_list):
                                label = item_map.get(item_id, item_id)
                                if label not in rank_positions:
                                    rank_positions[label] = []
                                rank_positions[label].append(pos + 1)
                    except Exception:
                        pass
                
                # Tính thứ hạng trung bình (Rank 1 là cao nhất)
                avg_ranks = {}
                first_place_counts = {}
                for label, positions in rank_positions.items():
                    if positions:
                        avg_ranks[label] = round(sum(positions) / len(positions), 2)
                        first_place_counts[label] = positions.count(1)
                    else:
                        avg_ranks[label] = 0.0
                        first_place_counts[label] = 0
                
                opt_dist = first_place_counts
                stats_sum = {"ranking_averages": avg_ranks}

            elif q_type in ("long_text", "short_text"):
                samples = []
                for a in ans_rows:
                    txt = (a["answer_value"] or "").strip()
                    if txt and txt not in samples:
                        samples.append(txt)
                    if len(samples) >= 8:
                        break
                text_samples = samples

            questions_analytics.append(QuestionStats(
                question_id=qid,
                question_title=q["title"],
                question_type=q_type,
                total_answers=total_ans,
                option_distribution=opt_dist,
                stats_summary=stats_sum,
                recent_text_samples=text_samples
            ))

        return SurveyAnalyticsOut(
            survey_id=survey_id,
            survey_title=s_row["title"],
            total_responses=total_responses,
            is_sample_size_sufficient=is_sufficient,
            sample_size_notice=notice,
            avg_duration_seconds=avg_dur,
            risk_distribution=risk_dist,
            review_distribution=review_dist,
            questions_analytics=questions_analytics
        )

@router.get("/benford")
def get_benford_analysis(survey_id: str, question_id: Optional[str] = Query(None)):
    """
    Phân tích định luật Benford (First-Digit Test) trên các câu hỏi kiểu số học
    để phát hiện số liệu ngụy tạo / bịa đặt theo phương pháp Schräpler & Wagner (2012)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if question_id:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                WHERE ra.question_id = ? AND r.survey_id = ?
            """, (question_id, survey_id)).fetchall()
        else:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                JOIN questions q ON q.id = ra.question_id
                WHERE r.survey_id = ? AND q.question_type = 'number'
            """, (survey_id,)).fetchall()

        raw_numbers = []
        for r in ans_rows:
            v = r["answer_value"]
            if v is not None and v != "":
                try:
                    raw_numbers.append(float(v))
                except Exception:
                    pass

        analysis = QualityEngine.compute_benford_analysis(raw_numbers)
        analysis["survey_id"] = survey_id
        analysis["question_id"] = question_id
        return analysis

