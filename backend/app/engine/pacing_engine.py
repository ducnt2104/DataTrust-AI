import re
import math
from typing import Dict, Any, List, Optional

class CognitivePacingEngine:
    """
    Động cơ Phân tích Gánh nặng Nhận thức & Nhịp độ Trả lời Khảo sát
    (Survey Cognitive Burden & Inattention Pacing Engine).

    Cơ sở phương pháp luận:
    - Krosnick, J. A. (1991). Response strategies for coping with the cognitive demands
      of attitude measures in surveys. Applied Cognitive Psychology, 5(3), 213-236.
    - Couper, M. P., Traugott, M. W., & Lamias, M. J. (2001). Web survey design and
      administration. Public Opinion Quarterly, 65(2), 230-253.
    - Yan, T., & Tourangeau, R. (2008). Fast times and easy questions: The effects of
      age, experience and question complexity on web survey response times. Applied
      Cognitive Psychology, 22(1), 51-68.
    - Dillman, D. A., Smyth, J. D., & Christian, L. M. (2014). Internet, Phone, Mail,
      and Mixed-Mode Surveys: The Tailored Design Method.
    """

    # Hằng số nhận thức học thuật (Academic Cognitive Constants)
    WORDS_PER_MINUTE_STANDARD = 220.0  # Tốc độ đọc trung bình người trưởng thành
    SECONDS_PER_WORD = 60.0 / WORDS_PER_MINUTE_STANDARD  # ~0.272 giây/từ

    # Thời gian định hướng thao tác nhận thức theo loại câu hỏi (Cognitive Interaction Overhead)
    TYPE_COGNITIVE_OVERHEAD = {
        "short_text": 3.0,       # Đọc prompt + gõ suy nghĩ ngắn
        "long_text": 8.0,        # Đọc prompt + diễn giải tư duy sâu
        "single_choice": 1.5,    # Đọc các phương án + so sánh loại trừ
        "multiple_choice": 2.5,  # Đọc các phương án + quyết định chọn nhiều
        "dropdown": 2.0,         # Mở menu + cuộn tìm
        "linear_scale": 1.2,     # Định vị trên dải thang đo
        "likert": 1.5,           # Định vị mức độ đồng ý/hài lòng
        "rating": 1.2,           # Đánh giá sao/điểm
        "nps": 1.5,              # Thang đo 0-10
        "matrix": 3.5,           # Đọc ma trận 2 chiều hàng x cột
        "number": 1.5,           # Nhập số liệu
        "date": 2.0,             # Chọn lịch ngày tháng
        "boolean": 1.0,          # Có/Không nhị phân
        "ranking": 4.5           # Sắp xếp thứ tự ưu tiên
    }

    @staticmethod
    def _count_words(text: str) -> int:
        """Đếm số từ thực tế của một đoạn văn bản tiếng Việt hoặc tiếng Anh"""
        if not text or not isinstance(text, str):
            return 0
        tokens = re.findall(r'\b[\w\u00C0-\u1EF9\-]+\b', text)
        return len(tokens)

    @classmethod
    def calculate_question_cognitive_burden(cls, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tính toán chỉ số gánh nặng nhận thức (Cognitive Burden Score 0-100) cho từng câu hỏi.
        """
        qid = question.get("id", "")
        q_title = question.get("title", "")
        q_desc = question.get("description", "")
        q_type = question.get("question_type", "single_choice")
        options = question.get("options", [])

        # 1. Đếm từ ngữ tiêu đề & mô tả
        title_words = cls._count_words(q_title)
        desc_words = cls._count_words(q_desc)
        total_prompt_words = title_words + desc_words

        # 2. Đếm từ ngữ trong các phương án trả lời
        options_word_count = 0
        num_options = 0
        num_rows = 0
        num_cols = 0

        if isinstance(options, list):
            num_options = len(options)
            for opt in options:
                if isinstance(opt, str):
                    options_word_count += cls._count_words(opt)
                elif isinstance(opt, dict):
                    options_word_count += cls._count_words(opt.get("label", "") or opt.get("text", ""))
        elif isinstance(options, dict):
            # Ma trận matrix: { "rows": [...], "columns": [...] }
            rows = options.get("rows", [])
            cols = options.get("columns", [])
            num_rows = len(rows) if isinstance(rows, list) else 0
            num_cols = len(cols) if isinstance(cols, list) else 0
            num_options = num_rows * max(num_cols, 1)

            if isinstance(rows, list):
                for r in rows:
                    options_word_count += cls._count_words(r.get("label", "") if isinstance(r, dict) else str(r))
            if isinstance(cols, list):
                for c in cols:
                    options_word_count += cls._count_words(c.get("label", "") if isinstance(c, dict) else str(c))

        total_words = total_prompt_words + options_word_count

        # 3. Tính thời gian đọc & xử lý nhận thức lý thuyết (Expected Cognitive Seconds)
        base_interaction = cls.TYPE_COGNITIVE_OVERHEAD.get(q_type, 2.0)
        if q_type == "matrix" and num_rows > 0:
            base_interaction = max(3.0, num_rows * 1.5)

        expected_reading_seconds = (total_words * cls.SECONDS_PER_WORD) + base_interaction

        # 4. Xác định các yếu tố kích hoạt gánh nặng quá tải (Risk Factors)
        risk_factors: List[str] = []
        raw_burden = 0.0

        # Phạt độ dài prompt (> 30 từ)
        if title_words > 35:
            risk_factors.append(f"Tiêu đề câu hỏi quá dài ({title_words} từ > 35 từ chuẩn)")
            raw_burden += 25.0
        elif title_words > 25:
            raw_burden += 15.0

        # Phạt số lượng phương án lựa chọn (> 7 phương án - Quy luật Miller 7±2)
        if q_type in ("single_choice", "multiple_choice", "dropdown") and num_options > 7:
            risk_factors.append(f"Quá tải lựa chọn ({num_options} phương án > 7, vi phạm quy luật Miller)")
            raw_burden += 25.0
        elif num_options > 5:
            raw_burden += 10.0

        # Phạt độ phức tạp ma trận
        if q_type == "matrix":
            if num_rows > 6 or num_cols > 6:
                risk_factors.append(f"Kích thước ma trận quá lớn ({num_rows} hàng x {num_cols} cột)")
                raw_burden += 30.0
            else:
                raw_burden += 15.0

        # Phạt câu hỏi tự luận mở dài
        if q_type == "long_text":
            raw_burden += 20.0

        # Đóng góp từ tổng thời gian đọc lý thuyết
        time_contribution = min(35.0, (expected_reading_seconds / 20.0) * 35.0)
        burden_score = round(min(100.0, raw_burden + time_contribution), 1)

        # 5. Phân tầng gánh nặng nhận thức
        if burden_score >= 70.0:
            burden_tier = "Critical"
        elif burden_score >= 50.0:
            burden_tier = "High"
        elif burden_score >= 30.0:
            burden_tier = "Moderate"
        else:
            burden_tier = "Low"

        # 6. Khuyến nghị thiết kế chuẩn Don Dillman
        redesign_recommendation = ""
        if burden_score >= 70.0:
            if "ma trận" in " ".join(risk_factors).lower():
                redesign_recommendation = "Nên tách ma trận lớn thành các câu hỏi trắc nghiệm hoặc thang đo đơn lẻ để tránh người dùng chọn lướt (straightlining)."
            elif "phương án" in " ".join(risk_factors).lower():
                redesign_recommendation = "Nên nhóm các phương án tương đồng hoặc cung cấp tùy chọn 'Khác (ghi rõ)' để giới hạn danh sách dưới 7 phương án."
            elif "tiêu đề" in " ".join(risk_factors).lower():
                redesign_recommendation = "Nên rút gọn câu chữ, đưa các giải thích chi tiết vào trường mô tả phụ thay vì dồn vào tiêu đề chính."
            else:
                redesign_recommendation = "Cân nhắc đơn giản hóa cấu trúc câu hỏi để giảm tỷ lệ bỏ cuộc giữa chừng (drop-off)."
        elif burden_score >= 50.0:
            redesign_recommendation = "Câu hỏi có mức độ nhận thức vừa phải, hãy đảm bảo hiển thị rõ ràng trên thiết bị di động."
        else:
            redesign_recommendation = "Cấu trúc tối ưu, thân thiện nhận thức và dễ trả lời."

        return {
            "id": qid,
            "order_index": question.get("order_index", 0),
            "title": q_title,
            "question_type": q_type,
            "title_words": title_words,
            "options_word_count": options_word_count,
            "total_words": total_words,
            "num_options": num_options,
            "expected_reading_seconds": round(expected_reading_seconds, 1),
            "cognitive_burden_score": burden_score,
            "burden_tier": burden_tier,
            "risk_factors": risk_factors,
            "redesign_recommendation": redesign_recommendation
        }

    @classmethod
    def analyze_survey_pacing(
        cls,
        survey_title: str,
        questions: List[Dict[str, Any]],
        durations: List[float]
    ) -> Dict[str, Any]:
        """
        Phân tích tổng thể nhịp độ trả lời, gánh nặng nhận thức và hiện tượng mệt mỏi nhận thức (Cognitive Fatigue).
        """
        # 1. Phân tích từng câu hỏi
        question_analyses = []
        total_survey_words = 0
        total_expected_seconds = 0.0

        for q in questions:
            q_res = cls.calculate_question_cognitive_burden(q)
            question_analyses.append(q_res)
            total_survey_words += q_res["total_words"]
            total_expected_seconds += q_res["expected_reading_seconds"]

        total_expected_seconds = max(total_expected_seconds, 5.0)

        # 2. Phân tích nhịp độ thực nghiệm từ các phản hồi đã thu thập
        clean_durations = [d for d in durations if isinstance(d, (int, float)) and d > 0]
        n_responses = len(clean_durations)

        if clean_durations:
            sorted_dur = sorted(clean_durations)
            median_actual = sorted_dur[n_responses // 2]
            mean_actual = sum(clean_durations) / n_responses
        else:
            median_actual = 0.0
            mean_actual = 0.0

        # 3. Tỷ số nhịp độ nhận thức Pacing Ratio = Actual / Expected
        if clean_durations and total_expected_seconds > 0:
            overall_pacing_ratio = round(median_actual / total_expected_seconds, 2)
        else:
            overall_pacing_ratio = 1.0

        # Phân loại mức độ tương tác nhận thức
        if overall_pacing_ratio < 0.30:
            engagement_level = "Severe Speeding / Sub-cognitive Satisficing"
            engagement_desc = "Tốc độ làm bài quá nhanh (< 30% thời gian tối thiểu). Rất cao khả năng người trả lời chọn bừa không đọc câu hỏi."
        elif overall_pacing_ratio < 0.65:
            engagement_level = "Rushed / Superficial Attention"
            engagement_desc = "Tốc độ làm bài vội vã. Người trả lời chỉ lướt qua từ khóa mà không đọc kỹ toàn bộ phương án."
        elif overall_pacing_ratio <= 1.80:
            engagement_level = "Optimal Cognitive Engagement"
            engagement_desc = "Nhịp độ nhận thức lý tưởng (0.65x – 1.8x thời gian chuẩn). Phản hồi thể hiện sự tập trung và cân nhắc kỹ lưỡng."
        else:
            engagement_level = "Deliberate / Distracted"
            engagement_desc = "Thời gian làm bài kéo dài (> 1.8x thời gian chuẩn). Thể hiện sự cân nhắc sâu hoặc người trả lời bị ngắt quãng/đa nhiệm."

        # 4. Phân phối nhóm người trả lời theo Pacing Ratio
        distribution = {
            "severe_speeding": 0,
            "rushed": 0,
            "optimal": 0,
            "deliberate": 0
        }

        for d in clean_durations:
            r = d / total_expected_seconds
            if r < 0.30:
                distribution["severe_speeding"] += 1
            elif r < 0.65:
                distribution["rushed"] += 1
            elif r <= 1.80:
                distribution["optimal"] += 1
            else:
                distribution["deliberate"] += 1

        # 5. Phân tích đường cong mệt mỏi nhận thức (Fatigue Curve)
        # Xem xét phân bố điểm gánh nặng theo thứ tự câu hỏi
        burden_scores = [qa["cognitive_burden_score"] for qa in question_analyses]
        avg_burden = sum(burden_scores) / len(burden_scores) if burden_scores else 0.0
        high_burden_count = sum(1 for qa in question_analyses if qa["cognitive_burden_score"] >= 50.0)

        # Tính độ dốc phân bổ gánh nặng (burden gradient theo vị trí)
        if len(burden_scores) >= 3:
            n_q = len(burden_scores)
            x_vals = list(range(n_q))
            x_mean = sum(x_vals) / n_q
            y_mean = avg_burden
            numerator = sum((x_vals[i] - x_mean) * (burden_scores[i] - y_mean) for i in range(n_q))
            denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n_q))
            fatigue_slope = round(numerator / denominator, 3) if denominator != 0 else 0.0
        else:
            fatigue_slope = 0.0

        fatigue_risk = False
        fatigue_note = ""
        if total_expected_seconds > 420:  # Khảo sát > 7 phút
            fatigue_risk = True
            fatigue_note = f"Thời lượng khảo sát dự kiến ({round(total_expected_seconds/60, 1)} phút) vượt ngưỡng tối ưu 7 phút của Tourangeau (2000), dễ gây ra hiện tượng mệt mỏi nhận thức về cuối."
        elif fatigue_slope > 2.5:
            fatigue_note = "Các câu hỏi nặng nhận thức dồn nhiều về nửa sau khảo sát, có thể làm tăng tỷ lệ bỏ dở."
        else:
            fatigue_note = "Thời lượng và phân bổ tải trọng nhận thức nằm trong ngưỡng tối ưu."

        # 6. Đoạn diễn giải học thuật APA 7th Edition
        apa_interpretation = (
            f"Theo mô hình nhịp độ nhận thức của Couper et al. (2001) và Krosnick (1991), "
            f"khảo sát có tổng dung lượng {total_survey_words} từ với thời gian xử lý nhận thức lý thuyết "
            f"là {round(total_expected_seconds, 1)} giây (~{round(total_expected_seconds/60, 1)} phút). "
            f"Trên tập mẫu thực nghiệm (N = {n_responses}), thời gian hoàn thành trung vị đạt {round(median_actual, 1)} giây, "
            f"tương ứng với Tỷ số nhịp độ Pacing Ratio = {overall_pacing_ratio} ({engagement_level}). "
            f"Toàn bộ {len(questions)} câu hỏi có điểm gánh nặng nhận thức trung bình là {round(avg_burden, 1)}/100, "
            f"trong đó có {high_burden_count} câu hỏi ở mức gánh nặng đáng chú ý (Burden Score ≥ 50)."
        )

        return {
            "survey_level": {
                "survey_title": survey_title,
                "total_questions": len(questions),
                "total_survey_words": total_survey_words,
                "expected_reading_seconds": round(total_expected_seconds, 1),
                "expected_reading_minutes": round(total_expected_seconds / 60.0, 1),
                "actual_sample_size": n_responses,
                "actual_median_seconds": round(median_actual, 1),
                "actual_mean_seconds": round(mean_actual, 1),
                "overall_pacing_ratio": overall_pacing_ratio,
                "engagement_level": engagement_level,
                "engagement_desc": engagement_desc,
                "respondent_pacing_distribution": distribution,
                "average_question_burden": round(avg_burden, 1),
                "high_burden_questions_count": high_burden_count,
                "fatigue_slope": fatigue_slope,
                "fatigue_risk": fatigue_risk,
                "fatigue_note": fatigue_note,
                "apa_interpretation": apa_interpretation
            },
            "question_analyses": question_analyses
        }
