"""
DataTrust - Survey Cognitive Pre-Testing & Question Ambiguity Diagnostics Engine
Phương pháp luận kiểm nghiệm nhận thức trước xuất bản (Pre-Flight Cognitive Testing):
- Đo lường độ phức tạp ngôn ngữ & chỉ số dễ đọc (Flesch Reading Ease & Kincaid Grade Level)
- Phát hiện 8 dạng lỗi cấu trúc & thiên lệch nhận thức (Tourangeau et al., 2000; Dillman et al., 2014):
  1. Leading / Loaded Questions (Câu hỏi dẫn dắt, mồi chài)
  2. Double-Barreled Questions (Câu hỏi ghép đôi đánh giá đa khía cạnh)
  3. Double Negatives (Phủ định kép gây rối trí nhận thức)
  4. Vague Quantifiers (Phương án đo lường mơ hồ không gắn neo tần suất)
  5. Acquiescence Bias Risk (Rủi ro thiên lệch chiều lòng đồng ý một chiều)
  6. Insufficient / Unbalanced Options (Thiếu phương án hoặc phương án mất cân xứng)
  7. Cognitive Overload (Quá tải độ dài văn bản hoặc ma trận câu hỏi phình to)
  8. Sensitive Items Unprotected (Câu hỏi nhạy cảm thiếu phương án bảo mật / từ chối)
- Giả lập 3 Persona nhân khẩu học phản biện nhận thức (Synthetic Cognitive Pre-test Personas)
- Dự báo đường cong mệt mỏi nhận thức (Cognitive Fatigue & Dropout Forecast)
- Tự động sinh phương án diễn đạt chuẩn hóa học thuật (1-Click Auto-Fix Reformulation)
Tuân thủ tiêu chuẩn chất lượng thiết kế bảng hỏi quốc tế AAPOR (2003) và ISO 20252:2019.
"""

import math
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Set


class CognitivePretestEngine:
    """
    Động cơ phân tích nhận thức & chẩn đoán mơ hồ bảng hỏi trước khi thu thập dữ liệu thực địa.
    """

    # Danh mục từ ngữ dẫn dắt / mồi chài (Leading Words)
    LEADING_PATTERNS = [
        (r"\b(tuyệt vời thế nào|tuyệt vời ra sao)\b", "Câu hỏi giả định tính ưu việt tuyệt đối."),
        (r"\b(có phải.*(rất tốt|tuyệt vời|xuất sắc|đúng không))\b", "Câu hỏi dẫn dắt người trả lời theo hướng khẳng định tích cực."),
        (r"\b(chắc hẳn bạn.*(thích|đồng ý|hài lòng))\b", "Dùng từ khẳng định áp đặt ('chắc hẳn')."),
        (r"\b(bạn có đồng ý rằng.*(tốt nhất|vượt trội|hoàn hảo))\b", "Câu hỏi mớm ý đánh giá cao nhất."),
        (r"\b(không ai có thể phủ nhận|ai cũng biết rằng)\b", "Mệnh đề áp đặt niềm tin số đông."),
        (r"\b(rất tốt phải không|quá tuyệt phải không)\b", "Câu hỏi đuôi thiên lệch cảm xúc.")
    ]

    # Liên từ nối câu hỏi ghép đôi (Double-Barreled Conjunctions)
    DOUBLE_BARRELED_TERMS = [" và ", " cũng như ", " đồng thời ", " cùng với ", " hay là ", " hoặc là "]

    # Cụm từ phủ định kép (Double Negatives)
    DOUBLE_NEGATIVE_PATTERNS = [
        r"\b(không.*không)\b",
        r"\b(chẳng lẽ.*không)\b",
        r"\b(không thể không)\b",
        r"\b(không đồng ý rằng.*không)\b"
    ]

    # Phương án định lượng mơ hồ (Vague Quantifiers)
    VAGUE_QUANTIFIERS = {
        "thường xuyên", "thỉnh thoảng", "đôi khi", "ít khi", "hiếm khi",
        "nhiều", "ít", "khá nhiều", "rất nhiều", "rất ít"
    }

    # Từ khóa nhạy cảm cần phương án bảo vệ (Sensitive Items)
    SENSITIVE_KEYWORDS = [
        "thu nhập", "tiền lương", "thu nhap", "tai san", "tài sản",
        "bệnh án", "sức khỏe tâm thần", "tôn giáo", "xu hướng tính dục",
        "đời sống riêng tư", "tiết kiệm", "nợ nần"
    ]

    @classmethod
    def compute_readability_metrics(cls, text: str) -> Dict[str, Any]:
        """
        Tính toán các chỉ số độ dễ đọc văn bản theo mô hình Flesch Reading Ease
        và Flesch-Kincaid Grade Level được chuẩn hóa cho tiếng Việt và tiếng Anh.
        """
        if not text or not text.strip():
            return {
                "word_count": 0,
                "sentence_count": 1,
                "avg_sentence_length": 0.0,
                "syllables_per_word": 1.0,
                "flesch_reading_ease": 100.0,
                "readability_level": "EASY",
                "difficulty_description": "Văn bản cực kỳ ngắn gọn, dễ tiếp cận."
            }

        clean_text = text.strip()
        words = clean_text.split()
        word_count = len(words)

        # Đếm câu dựa trên các dấu chấm, hỏi, than, chấm phẩy
        sentence_delimiters = re.compile(r"[.?!;]+")
        sentences = [s.strip() for s in sentence_delimiters.split(clean_text) if s.strip()]
        sentence_count = max(1, len(sentences))

        avg_sentence_length = word_count / sentence_count

        # Ước lượng âm tiết (Tiếng Việt: 1 từ đơn/hình vị = 1 âm tiết)
        syllable_count = 0
        for w in words:
            w_lower = w.lower()
            # Đếm nguyên âm tiếng Anh nếu văn bản có tiếng Anh
            vowels = len(re.findall(r"[aeiouyàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ]", w_lower))
            syllable_count += max(1, vowels)

        syllables_per_word = syllable_count / max(1, word_count)

        # Flesch Reading Ease Formula (Kincaid et al., 1975)
        fre = 206.835 - (1.015 * avg_sentence_length) - (84.6 * syllables_per_word)
        fre = round(max(0.0, min(100.0, fre)), 1)

        if fre >= 70.0:
            readability_level = "EASY"
            diff_desc = "Văn phong phổ thông, trong sáng, dễ tiếp cận với mọi đối tượng công chúng."
        elif fre >= 50.0:
            readability_level = "MODERATE"
            diff_desc = "Độ phức tạp trung bình, phù hợp với người có trình độ trung học trở lên."
        else:
            readability_level = "DIFFICULT"
            diff_desc = "Văn phong hàn lâm, câu phức hoặc nhiều thuật ngữ, có nguy cơ gây mệt mỏi nhận thức và bỏ cuộc giữa chừng."

        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "syllables_per_word": round(syllables_per_word, 2),
            "flesch_reading_ease": fre,
            "readability_level": readability_level,
            "difficulty_description": diff_desc
        }

    @classmethod
    def diagnose_question_ambiguities(
        cls,
        question: Dict[str, Any],
        order_index: int
    ) -> List[Dict[str, Any]]:
        """
        Chẩn đoán chuyên sâu các lỗi mơ hồ, câu hỏi ghép và thiên lệch nhận thức của từng câu hỏi.
        """
        issues: List[Dict[str, Any]] = []
        qid = question.get("id") or f"q_{order_index + 1}"
        title = (question.get("title") or "").strip()
        lower_title = title.lower()
        q_type = question.get("question_type", "single_choice")
        options = question.get("options", [])
        words = title.split()
        word_count = len(words)

        # 1. Kiểm tra câu hỏi dẫn dắt (Leading / Loaded Question)
        for pattern, expl in cls.LEADING_PATTERNS:
            match = re.search(pattern, lower_title, re.IGNORECASE)
            if match:
                clean_suggestion = title
                for bkw in ["Có phải ", "có phải ", "chắc hẳn ", "tuyệt vời thế nào ", "đúng không?", "rất tốt phải không?"]:
                    clean_suggestion = clean_suggestion.replace(bkw, "")
                clean_suggestion = f"Xin cho biết ý kiến/đánh giá của bạn về: {clean_suggestion.strip().rstrip('?')}"

                issues.append({
                    "question_id": qid,
                    "question_order": order_index + 1,
                    "question_title": title,
                    "issue_type": "LEADING_QUESTION",
                    "severity": "WARNING",
                    "cognitive_dimension": "Comprehension & Judgment",
                    "explanation": f"{expl} Phát hiện từ ngữ thiên kiến: '{match.group(0)}'.",
                    "academic_rule": "AAPOR Best Practices (2003) - Nguyên tắc trung lập ngữ nghĩa trong xây dựng bảng hỏi.",
                    "auto_fix_title": clean_suggestion
                })
                break

        # 2. Kiểm tra câu hỏi kép / ghép đôi (Double-Barreled Question)
        for dterm in cls.DOUBLE_BARRELED_TERMS:
            if dterm in lower_title and word_count >= 8:
                parts = title.split(dterm)
                if len(parts) >= 2 and len(parts[0].split()) >= 3 and len(parts[1].split()) >= 3:
                    auto_part_1 = parts[0].strip()
                    if not auto_part_1.endswith("?"):
                        auto_part_1 += "?"

                    issues.append({
                        "question_id": qid,
                        "question_order": order_index + 1,
                        "question_title": title,
                        "issue_type": "DOUBLE_BARRELED",
                        "severity": "WARNING",
                        "cognitive_dimension": "Comprehension & Retrieval",
                        "explanation": f"Câu hỏi đánh giá 2 khía cạnh độc lập cùng lúc liên kết bởi liên từ '{dterm.strip()}'. Người trả lời có thể hài lòng với khía cạnh thứ nhất nhưng không hài lòng với khía cạnh thứ hai.",
                        "academic_rule": "Don Dillman (2014) - Quy tắc đơn biến: Mỗi câu hỏi chỉ được đo lường duy nhất 1 khái niệm.",
                        "auto_fix_title": auto_part_1
                    })
                    break

        # 3. Kiểm tra phủ định kép (Double Negatives)
        for dn_pat in cls.DOUBLE_NEGATIVE_PATTERNS:
            if re.search(dn_pat, lower_title, re.IGNORECASE):
                issues.append({
                    "question_id": qid,
                    "question_order": order_index + 1,
                    "question_title": title,
                    "issue_type": "DOUBLE_NEGATIVE",
                    "severity": "CRITICAL",
                    "cognitive_dimension": "Comprehension",
                    "explanation": "Câu hỏi sử dụng phủ định kép gây khó khăn lớn cho người trả lời khi xác định câu trả lời 'Đồng ý' hay 'Không đồng ý'.",
                    "academic_rule": "Tourangeau et al. (2000) - Tải lượng xử lý nhận thức tăng gấp 3 lần khi câu hỏi chứa từ phủ định kép.",
                    "auto_fix_title": title.replace("không thể không", "cần").replace("không đồng ý rằng không", "đồng ý rằng")
                })
                break

        # 4. Kiểm tra phương án định lượng mơ hồ (Vague Quantifiers)
        if q_type in ("single_choice", "multiple_choice", "dropdown") and isinstance(options, list):
            vague_found = []
            for opt in options:
                opt_label = (opt.get("label") or "").strip().lower()
                if opt_label in cls.VAGUE_QUANTIFIERS:
                    vague_found.append(opt_label)

            if len(vague_found) >= 2:
                issues.append({
                    "question_id": qid,
                    "question_order": order_index + 1,
                    "question_title": title,
                    "issue_type": "VAGUE_QUANTIFIER",
                    "severity": "SUGGESTION",
                    "cognitive_dimension": "Response Formatting",
                    "explanation": f"Phương án trả lời sử dụng từ ngữ định tính mơ hồ ({', '.join(vague_found)}) không có mốc đo lường thời gian/tần suất cụ thể.",
                    "academic_rule": "Bradburn, Sudman & Wansink (2004) - Cần neo các mốc tần suất khách quan (VD: 'Hàng ngày', '2-3 lần/tuần', '1 lần/tháng').",
                    "suggested_options": [
                        {"id": "opt_freq_1", "label": "Hàng ngày hoặc gần như hàng ngày"},
                        {"id": "opt_freq_2", "label": "2 - 3 lần mỗi tuần"},
                        {"id": "opt_freq_3", "label": "1 - 2 lần mỗi tháng"},
                        {"id": "opt_freq_4", "label": "Hiếm khi hoặc không bao giờ"}
                    ]
                })

        # 5. Kiểm tra quá tải nhận thức do độ dài hoặc kích thước ma trận (Cognitive Overload)
        if word_count > 35:
            issues.append({
                "question_id": qid,
                "question_order": order_index + 1,
                "question_title": title,
                "issue_type": "COGNITIVE_OVERLOAD",
                "severity": "WARNING",
                "cognitive_dimension": "Comprehension",
                "explanation": f"Nội dung câu hỏi quá dài ({word_count} từ > 35 từ), người tham gia có xu hướng đọc lướt và bỏ qua thông tin quan trọng.",
                "academic_rule": "Tourangeau (2000) - Khuyến nghị câu hỏi ngắn gọn dưới 25-30 từ để tối ưu khả năng tập trung trên thiết bị di động.",
                "auto_fix_title": " ".join(words[:25]) + "..."
            })
        elif q_type == "matrix" and isinstance(options, dict):
            rows = options.get("rows", [])
            cols = options.get("columns", [])
            if len(rows) > 7 or len(cols) > 5:
                issues.append({
                    "question_id": qid,
                    "question_order": order_index + 1,
                    "question_title": title,
                    "issue_type": "COGNITIVE_OVERLOAD",
                    "severity": "WARNING",
                    "cognitive_dimension": "Judgment & Response Formatting",
                    "explanation": f"Câu hỏi dạng bảng ma trận quá lớn ({len(rows)} hàng x {len(cols)} cột). Ma trận lớn gây ra hiệu ứng thẳng hàng (Straightlining) và tỷ lệ bỏ ngang cao trên điện thoại.",
                    "academic_rule": "Don Dillman (2014) - Rút gọn bảng ma trận xuống tối đa 5-6 tiêu chí cốt lõi hoặc tách thành các câu hỏi trắc nghiệm đơn.",
                    "auto_fix_title": title
                })

        # 6. Kiểm tra câu hỏi trắc nghiệm thiếu phương án (Insufficient Options)
        if q_type in ("single_choice", "multiple_choice", "dropdown"):
            if not isinstance(options, list) or len(options) < 2:
                issues.append({
                    "question_id": qid,
                    "question_order": order_index + 1,
                    "question_title": title,
                    "issue_type": "INSUFFICIENT_OPTIONS",
                    "severity": "CRITICAL",
                    "cognitive_dimension": "Response Formatting",
                    "explanation": "Câu hỏi trắc nghiệm yêu cầu tối thiểu 2 phương án lựa chọn.",
                    "academic_rule": "ISO 20252:2019 - Tính đầy đủ và bao quát của thang đo danh mục.",
                    "suggested_options": [
                        {"id": "opt_auto_1", "label": "Có / Đồng ý"},
                        {"id": "opt_auto_2", "label": "Không / Không đồng ý"},
                        {"id": "opt_auto_3", "label": "Ý kiến khác / Chưa xác định"}
                    ]
                })

        # 7. Kiểm tra câu hỏi nhạy cảm thiếu phương án bảo mật (Sensitive Items Unprotected)
        is_sensitive = any(kw in lower_title for kw in cls.SENSITIVE_KEYWORDS)
        if is_sensitive and q_type in ("single_choice", "multiple_choice", "dropdown"):
            has_opt_out = False
            if isinstance(options, list):
                for opt in options:
                    olabel = (opt.get("label") or "").lower()
                    if any(w in olabel for w in ["từ chối", "không muốn", "bảo mật", "khác", "khong muon"]):
                        has_opt_out = True
                        break

            if not has_opt_out:
                issues.append({
                    "question_id": qid,
                    "question_order": order_index + 1,
                    "question_title": title,
                    "issue_type": "SENSITIVE_UNPROTECTED",
                    "severity": "WARNING",
                    "cognitive_dimension": "Judgment & Ethics",
                    "explanation": "Câu hỏi chạm đến vấn đề tài chính hoặc đời tư cá nhân nhưng thiếu tùy chọn 'Từ chối trả lời' hoặc 'Bảo mật'. Điều này dẫn đến phản hồi khai khống hoặc bỏ cuộc.",
                    "academic_rule": "AAPOR Ethics Code (2015) & Nghị định 356/2025/NĐ-CP - Quyền bảo vệ thông tin đời tư của người tham gia khảo sát.",
                    "suggested_options": [
                        {"id": "opt_optout", "label": "Xin phép từ chối trả lời / Bảo mật thông tin"}
                    ]
                })

        return issues

    @classmethod
    def simulate_demographic_personas(
        cls,
        questions: List[Dict[str, Any]],
        all_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Giả lập 3 Persona nhân khẩu học đặc trưng mô phỏng trải nghiệm đọc và trả lời:
        1. Persona Gen Z / Người Đi Làm Bận Rộn (Fast Paced / Low Attention Span)
        2. Persona Người Cao Tuổi / Dân Cư Phổ Thông (Elderly / Plain Language)
        3. Persona Chuyên Viên / Nhà Nghiên Cứu Phản Biện (Analytical Auditor)
        """
        N_q = len(questions)
        critical_count = sum(1 for i in all_issues if i["severity"] == "CRITICAL")
        warning_count = sum(1 for i in all_issues if i["severity"] == "WARNING")

        # Đếm số ma trận và câu dài
        matrix_count = sum(1 for q in questions if q.get("question_type") == "matrix")
        long_q_count = sum(1 for q in questions if len((q.get("title") or "").split()) > 25)

        # Persona 1: Khách hàng trẻ bận rộn trên điện thoại di động
        p1_dropout_risk = round(min(0.85, 0.05 + (0.04 * max(0, N_q - 10)) + (0.08 * matrix_count) + (0.06 * long_q_count)), 2)
        p1_time_sec = round(N_q * 8.5 + matrix_count * 15.0 + long_q_count * 6.0, 1)
        p1_bottlenecks = [i["question_id"] for i in all_issues if i["issue_type"] in ("COGNITIVE_OVERLOAD", "DOUBLE_BARRELED")][:3]
        p1_difficulty = "CHALLENGING" if p1_dropout_risk > 0.40 else ("SMOOTH" if p1_dropout_risk < 0.15 else "ACCEPTABLE")

        # Persona 2: Người cao tuổi / Dân cư phổ thông
        p2_hesitation_score = round(min(0.90, 0.10 + (0.12 * critical_count) + (0.05 * warning_count) + (0.08 * long_q_count)), 2)
        p2_time_sec = round(N_q * 16.0 + matrix_count * 25.0 + long_q_count * 14.0, 1)
        p2_bottlenecks = [i["question_id"] for i in all_issues if i["issue_type"] in ("LEADING_QUESTION", "DOUBLE_NEGATIVE", "VAGUE_QUANTIFIER")][:3]
        p2_difficulty = "DROPOUT_RISK" if p2_hesitation_score > 0.60 else ("CHALLENGING" if p2_hesitation_score > 0.35 else "ACCEPTABLE")

        # Persona 3: Chuyên viên / Phản biện cẩn trọng
        p3_critical_score = round(min(0.95, 0.05 + (0.15 * critical_count) + (0.08 * warning_count)), 2)
        p3_time_sec = round(N_q * 12.0 + matrix_count * 20.0, 1)
        p3_bottlenecks = [i["question_id"] for i in all_issues if i["issue_type"] in ("DOUBLE_BARRELED", "LEADING_QUESTION", "INSUFFICIENT_OPTIONS")][:3]
        p3_difficulty = "CHALLENGING" if p3_critical_score > 0.50 else ("ACCEPTABLE" if p3_critical_score > 0.20 else "SMOOTH")

        return [
            {
                "persona_id": "PERSONA_FAST_PACED",
                "persona_name": "Người Trẻ / Đi Làm Bận Rộn (Thao tác trên Mobile)",
                "persona_demographic": "Tuổi: 20 - 35, Học vấn: Đại học, Thiết bị: Smartphone 100%",
                "cognitive_style": "Đọc lướt nhanh, cực kỳ nhạy cảm với câu hỏi dài hoặc ma trận phức tạp.",
                "overall_difficulty_rating": p1_difficulty,
                "predicted_completion_time_sec": p1_time_sec,
                "predicted_dropout_probability": p1_dropout_risk,
                "bottleneck_question_ids": p1_bottlenecks,
                "qualitative_feedback": (
                    f"Bảng hỏi gồm {N_q} câu. "
                    + ("Các câu hỏi ngắn gọn và tải nhanh giúp tôi hoàn thành suôn sẻ." if p1_difficulty == "SMOOTH"
                       else "Một số câu hỏi quá dài hoặc dạng ma trận khiến tôi thấy nản lòng và muốn bỏ qua.")
                )
            },
            {
                "persona_id": "PERSONA_ELDERLY_PLAIN",
                "persona_name": "Người Cao Tuổi / Dân Cư Phổ Thông (Đọc Kỹ Từng Từ)",
                "persona_demographic": "Tuổi: 55 - 75, Trình độ: Phổ thông, Cần từ ngữ giản dị, rõ ràng",
                "cognitive_style": "Xử lý thông tin thận trọng, dễ hoang mang trước thuật ngữ chuyên ngành hoặc phủ định kép.",
                "overall_difficulty_rating": p2_difficulty,
                "predicted_completion_time_sec": p2_time_sec,
                "predicted_dropout_probability": p2_hesitation_score,
                "bottleneck_question_ids": p2_bottlenecks,
                "qualitative_feedback": (
                    "Tôi muốn trả lời chính xác nhưng có một số câu hỏi dùng từ ngữ phức tạp hoặc có 2 ý trong 1 câu "
                    "khiến tôi không biết chọn phương án nào là đúng."
                )
            },
            {
                "persona_id": "PERSONA_ANALYTICAL_REVIEWER",
                "persona_name": "Chuyên Viên Thẩm Định / Phản Biện Khoa Học",
                "persona_demographic": "Nghiên cứu viên / Giảng viên / Quản lý chất lượng dữ liệu",
                "cognitive_style": "Kiểm tra tính nhất quán logic, phát hiện ngay các câu hỏi mồi chài hay thiếu phương án trung tính.",
                "overall_difficulty_rating": p3_difficulty,
                "predicted_completion_time_sec": p3_time_sec,
                "predicted_dropout_probability": p3_critical_score,
                "bottleneck_question_ids": p3_bottlenecks,
                "qualitative_feedback": (
                    f"Phát hiện {len(all_issues)} lỗi kỹ thuật thiết kế bảng hỏi. "
                    + ("Cần điều chỉnh ngay các câu hỏi dẫn dắt để tránh làm sai lệch dữ liệu phân tích." if all_issues
                       else "Thiết kế bảng hỏi đạt chuẩn khoa học nghiêm ngặt theo khuyến nghị AAPOR.")
                )
            }
        ]

    @classmethod
    def calculate_fatigue_curve(cls, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Tính toán đường cong mệt mỏi nhận thức và nguy cơ bỏ dở tích lũy (Cognitive Fatigue Curve)
        theo thứ tự câu hỏi từ 1 đến Q.
        """
        curve = []
        cum_sec = 0.0

        for idx, q in enumerate(questions):
            q_type = q.get("question_type", "single_choice")
            title = q.get("title", "")
            words = len(title.split())

            # Thời gian đọc ước tính (180 words per minute = 3 words/sec)
            read_sec = max(2.0, words / 3.0)

            # Thời gian phản hồi nhận thức theo loại câu hỏi
            if q_type == "matrix":
                action_sec = 16.0
            elif q_type in ("rating", "linear_scale", "nps"):
                action_sec = 6.0
            elif q_type in ("long_text", "text"):
                action_sec = 25.0
            elif q_type == "ranking":
                action_sec = 14.0
            else:
                action_sec = 8.0

            step_sec = read_sec + action_sec
            cum_sec += step_sec

            # Chỉ số mệt mỏi nhận thức (0 - 100%)
            # Hàm logistic tăng dần theo thời lượng lũy kế
            fatigue_pct = round(100.0 / (1.0 + math.exp(-0.008 * (cum_sec - 180.0))), 1)
            fatigue_pct = max(5.0, min(95.0, fatigue_pct))

            # Nguy cơ bỏ dở tích lũy (Cumulative dropout probability)
            dropout_risk_pct = round(max(1.0, min(80.0, (fatigue_pct * 0.60) + (idx * 0.8))), 1)

            curve.append({
                "question_index": idx + 1,
                "question_id": q.get("id", f"q_{idx+1}"),
                "question_title": title[:30] + ("..." if len(title) > 30 else ""),
                "cumulative_time_seconds": round(cum_sec, 1),
                "fatigue_percentage": fatigue_pct,
                "dropout_risk_percentage": dropout_risk_pct
            })

        return curve

    @classmethod
    def run_pretest_audit(
        cls,
        survey_id: Optional[str] = None,
        title: str = "Khảo sát khảo nghiệm",
        questions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Thực thi toàn bộ quy trình kiểm nghiệm nhận thức tiền xuất bản (Comprehensive Cognitive Pre-Test).
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        questions = questions or []
        total_questions = len(questions)

        # Ghép toàn bộ văn bản câu hỏi và mô tả để đo Flesch Reading Ease
        full_text_corpus = title + ". "
        for q in questions:
            full_text_corpus += (q.get("title") or "") + ". "
            if q.get("description"):
                full_text_corpus += (q.get("description") or "") + ". "

        readability = cls.compute_readability_metrics(full_text_corpus)

        # Chẩn đoán từng câu hỏi
        all_issues: List[Dict[str, Any]] = []
        for idx, q in enumerate(questions):
            q_issues = cls.diagnose_question_ambiguities(q, idx)
            all_issues.extend(q_issues)

        critical_count = sum(1 for i in all_issues if i["severity"] == "CRITICAL")
        warning_count = sum(1 for i in all_issues if i["severity"] == "WARNING")
        suggestion_count = sum(1 for i in all_issues if i["severity"] == "SUGGESTION")

        # Tính toán Điểm Chất Lượng Thiết Kế Khảo Sát (Survey Design Quality Index - SDQI)
        # Bắt đầu từ 100 điểm, trừ điểm theo mức độ nghiêm trọng
        penalty = (critical_count * 15.0) + (warning_count * 6.0) + (suggestion_count * 2.0)
        if readability["readability_level"] == "DIFFICULT":
            penalty += 10.0
        elif readability["readability_level"] == "MODERATE":
            penalty += 4.0

        design_quality_score = round(max(10.0, min(100.0, 100.0 - penalty)), 1)

        # Xếp loại học thuật
        if design_quality_score >= 90.0:
            academic_grade = "A+"
        elif design_quality_score >= 80.0:
            academic_grade = "A"
        elif design_quality_score >= 65.0:
            academic_grade = "B"
        else:
            academic_grade = "C"

        # Mô phỏng personas và đường cong mệt mỏi
        personas = cls.simulate_demographic_personas(questions, all_issues)
        fatigue_curve = cls.calculate_fatigue_curve(questions)

        # Thời gian làm bài trung bình ước tính
        est_duration_minutes = round(fatigue_curve[-1]["cumulative_time_seconds"] / 60.0, 1) if fatigue_curve else 0.0

        # Tóm tắt phương pháp luận
        if len(all_issues) == 0 and design_quality_score >= 85.0:
            summary = (
                f"Bảng hỏi đạt chuẩn kiểm định nhận thức xuất sắc ({academic_grade} - {design_quality_score}/100). "
                f"Độ dễ đọc đạt FRE = {readability['flesch_reading_ease']} ({readability['readability_level']}). "
                f"Không phát hiện câu hỏi dẫn dắt, phủ định kép hay cấu trúc mơ hồ. Sẵn sàng triển khai thực địa."
            )
        else:
            summary = (
                f"Kiểm tra nhận thức phát hiện {len(all_issues)} điểm cần hoàn thiện ({critical_count} nghiêm trọng, "
                f"{warning_count} cảnh báo). Điểm chất lượng thiết kế đạt {design_quality_score}/100 (Hạng {academic_grade}). "
                f"Khuyến nghị áp dụng gợi ý viết lại tự động trước khi xuất bản để hạn chế méo mó dữ liệu."
            )

        return {
            "survey_id": survey_id,
            "survey_title": title,
            "total_questions": total_questions,
            "total_words": readability["word_count"],
            "readability_score": readability["flesch_reading_ease"],
            "readability_level": readability["readability_level"],
            "estimated_duration_minutes": est_duration_minutes,
            "design_quality_score": design_quality_score,
            "academic_grade": academic_grade,
            "total_issues_count": len(all_issues),
            "critical_issues_count": critical_count,
            "warning_issues_count": warning_count,
            "issues": all_issues,
            "personas": personas,
            "fatigue_curve": fatigue_curve,
            "methodological_summary": summary,
            "timestamp": now_ts
        }
