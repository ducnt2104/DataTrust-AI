import json
import math
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.schemas import EnumeratorAnalyticsOut, EnumeratorMetrics
from app.engine.quality_engine import QualityEngine

router = APIRouter(prefix="/api/surveys/{survey_id}/enumerators", tags=["Enumerator Analytics"])

@router.get("", response_model=EnumeratorAnalyticsOut)
def get_enumerator_analytics(survey_id: str):
    """
    Phân tích thống kê và phát hiện bất thường theo từng điều tra viên (Interviewer / Field Group Falsification).
    Đo độ lệch chuẩn Z-score về phương sai câu trả lời, tỷ lệ cảnh báo rủi ro cao và tính đồng nhất bất thường.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT id, duration_seconds, risk_score, risk_level, source, enumerator_id, client_metadata_json
            FROM responses
            WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        if not resp_rows:
            return EnumeratorAnalyticsOut(
                survey_id=survey_id,
                total_enumerators=0,
                total_field_responses=0,
                enumerators=[]
            )

        # Lấy danh sách câu hỏi đóng để đo phương sai câu trả lời
        q_rows = conn.execute("""
            SELECT id, question_type, options_json FROM questions
            WHERE survey_id = ? AND question_type NOT IN ('short_text', 'long_text')
        """, (survey_id,)).fetchall()
        eval_q_ids = [q["id"] for q in q_rows]

        # Nhóm responses theo enumerator_id
        grouped: Dict[str, List[Any]] = {}
        for r in resp_rows:
            # Nếu không có enumerator_id, kiểm tra trong client_metadata_json hoặc gán 'unassigned'
            enum_id = (r["enumerator_id"] or "").strip()
            if not enum_id:
                try:
                    meta = json.loads(r["client_metadata_json"] or "{}")
                    enum_id = meta.get("enumerator_id", "").strip()
                except Exception:
                    pass
            if not enum_id:
                enum_id = "Chưa gán mã ĐTV (Online/Khách vãng lai)"
            
            grouped.setdefault(enum_id, []).append(r)

        # Tính phương sai câu trả lời cho từng điều tra viên
        enum_variances: Dict[str, float] = {}
        for enum_id, r_list in grouped.items():
            r_ids = [r["id"] for r in r_list]
            if len(r_ids) < 2 or not eval_q_ids:
                enum_variances[enum_id] = 1.0
                continue

            # Lấy tất cả đáp án
            placeholders = ",".join(["?"] * len(r_ids))
            ans_rows = conn.execute(f"""
                SELECT response_id, question_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders})
            """, r_ids).fetchall()

            # Chuyển đổi sang số tương ứng
            numeric_vals = []
            for a in ans_rows:
                val_str = str(a["answer_value"]).strip().lower()
                try:
                    numeric_vals.append(float(val_str))
                except Exception:
                    # Mã hóa hash ngắn thành số nguyên nhỏ
                    numeric_vals.append(float(sum(ord(c) for c in val_str) % 10))

            if len(numeric_vals) >= 4:
                mean_val = sum(numeric_vals) / len(numeric_vals)
                var_val = sum((x - mean_val) ** 2 for x in numeric_vals) / (len(numeric_vals) - 1)
                enum_variances[enum_id] = var_val
            else:
                enum_variances[enum_id] = 1.0

        # Tính mean và std của phương sai trên toàn bộ tập điều tra viên
        all_vars = list(enum_variances.values())
        mean_global_var = sum(all_vars) / max(1, len(all_vars))
        std_global_var = math.sqrt(sum((v - mean_global_var) ** 2 for v in all_vars) / max(1, len(all_vars)))
        std_global_var = max(0.1, std_global_var)

        metrics_list: List[EnumeratorMetrics] = []
        for enum_id, r_list in grouped.items():
            total = len(r_list)
            online_c = sum(1 for r in r_list if r["source"] == "online_form")
            paper_c = sum(1 for r in r_list if r["source"] == "paper_scan")

            durations = [r["duration_seconds"] for r in r_list if r["duration_seconds"] > 0]
            avg_dur = sum(durations) / len(durations) if durations else 0.0

            risks = [r["risk_score"] for r in r_list]
            avg_risk = sum(risks) / len(risks) if risks else 0.0

            high_risk_c = sum(1 for r in r_list if r["risk_level"] == "high" or r["risk_score"] >= 70.0)
            high_risk_rate = high_risk_c / total if total > 0 else 0.0

            # Tính Z-score phương sai
            this_var = enum_variances.get(enum_id, 1.0)
            z_score = (this_var - mean_global_var) / std_global_var

            reasons = []
            is_anomaly = False

            # Điều kiện cảnh báo bất thường:
            # 1. Z-score phương sai quá thấp (Z < -1.75) khi có từ 4 phiếu trở lên
            if total >= 4 and z_score < -1.75:
                is_anomaly = True
                reasons.append(f"Phương sai câu trả lời thấp bất thường (Z = {z_score:.2f}), dấu hiệu trả lời rập khuôn.")

            # 2. Tỷ lệ rủi ro cao >= 40% trên tổng số phiếu
            if total >= 3 and high_risk_rate >= 0.40:
                is_anomaly = True
                reasons.append(f"Tỷ lệ phiếu bị gắn cờ rủi ro cao vượt mức ({round(high_risk_rate * 100)}%).")

            # 3. Thời gian nộp bài trung bình quá nhanh (< 15s/phiếu)
            if total >= 3 and avg_dur > 0 and avg_dur < 15.0:
                is_anomaly = True
                reasons.append(f"Tốc độ nộp bài trung bình siêu tốc ({round(avg_dur, 1)}s/phiếu).")

            metrics_list.append(EnumeratorMetrics(
                enumerator_id=enum_id,
                total_responses=total,
                online_count=online_c,
                paper_count=paper_c,
                avg_duration_seconds=round(avg_dur, 1),
                avg_risk_score=round(avg_risk, 1),
                high_risk_count=high_risk_c,
                high_risk_rate=round(high_risk_rate, 3),
                variance_z_score=round(z_score, 2),
                is_anomaly=is_anomaly,
                anomaly_reasons=reasons
            ))

        # Sắp xếp theo tỷ lệ rủi ro cao giảm dần
        metrics_list.sort(key=lambda m: (m.is_anomaly, m.avg_risk_score), reverse=True)

        return EnumeratorAnalyticsOut(
            survey_id=survey_id,
            total_enumerators=len(metrics_list),
            total_field_responses=len(resp_rows),
            enumerators=metrics_list
        )
