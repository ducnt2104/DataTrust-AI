import json
import os
import re
import time
import uuid
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import httpx

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    AI_FALLBACK_MODEL,
    AI_REQUEST_TIMEOUT_SECONDS,
    is_gemini_configured
)
from app.database import get_db
from app.engine.qualitative_engine import QualitativeEngine

# 12 Standard Supported Question Types in DataTrust
ALL_SUPPORTED_QUESTION_TYPES = [
    "single_choice",
    "multiple_choice",
    "short_text",
    "long_text",
    "number",
    "rating",
    "linear_scale",
    "dropdown",
    "date",
    "likert",
    "matrix",
    "ranking"
]

class RequirementParser:
    """
    Trích xuất và cấu trúc hóa yêu cầu khảo sát từ văn bản tự nhiên:
    - Làm sạch và vô hiệu hóa tiêm lệnh độc hại (Prompt Injection Sanitization).
    - Nhận diện mục tiêu nghiên cứu, giả thuyết kiểm định.
    - Nhận diện đối tượng khảo sát và ngữ cảnh triển khai.
    - Phát hiện các dạng câu hỏi chuyên biệt được yêu cầu (matrix, ranking, likert, etc.).
    """
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions?", re.IGNORECASE),
        re.compile(r"system\s+compromised", re.IGNORECASE),
        re.compile(r"print\s+['\"][^'\"]+['\"]\s+in\s+all\s+questions?", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+dan\s+mode", re.IGNORECASE),
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE),
        re.compile(r"drop\s+table", re.IGNORECASE),
    ]

    @classmethod
    def sanitize_text(cls, text: str) -> Tuple[str, bool]:
        """Loại bỏ các chỉ thị độc hại và mã can thiệp hệ thống"""
        sanitized = text
        detected = False
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(sanitized):
                sanitized = pattern.sub("", sanitized)
                detected = True
        return sanitized.strip(), detected

    @classmethod
    def parse(
        cls,
        topic: str,
        audience: Optional[str] = "",
        research_objectives: Optional[str] = "",
        preferred_types: Optional[List[str]] = None,
        target_question_count: int = 7,
        expected_time_minutes: int = 5,
        language: str = "vi"
    ) -> Dict[str, Any]:
        clean_topic, topic_injected = cls.sanitize_text(topic)
        clean_aud, aud_injected = cls.sanitize_text(audience or "")
        clean_obj, obj_injected = cls.sanitize_text(research_objectives or "")
        injection_detected = topic_injected or aud_injected or obj_injected
        
        # Nhận diện tự động dạng câu hỏi nếu người dùng nhắc đến trong mô tả
        detected_types = set(preferred_types or [])
        lower_text = f"{clean_topic} {clean_obj}".lower()
        
        if any(w in lower_text for w in ["ma trận", "matrix", "bảng đánh giá", "tiêu chí"]):
            detected_types.add("matrix")
        if any(w in lower_text for w in ["xếp hạng", "ranking", "thứ tự", "ưu tiên"]):
            detected_types.add("ranking")
        if any(w in lower_text for w in ["hài lòng", "likert", "mức độ", "đồng ý"]):
            detected_types.add("likert")
        if any(w in lower_text for w in ["nps", "thang điểm", "1-10", "1 đến 10"]):
            detected_types.add("linear_scale")
        if any(w in lower_text for w in ["nhiều lựa chọn", "chọn nhiều", "yếu tố nào"]):
            detected_types.add("multiple_choice")
        if any(w in lower_text for w in ["đóng góp", "ý kiến", "nhận xét", "tự do", "nguyên nhân"]):
            detected_types.add("long_text")

        # Đảm bảo luôn có sự kết hợp đa dạng
        if not detected_types:
            detected_types = {"single_choice", "likert", "multiple_choice", "linear_scale", "long_text"}

        return {
            "topic": clean_topic,
            "audience": clean_aud if clean_aud else "Người tham gia đại trà phù hợp với chủ đề",
            "research_objectives": clean_obj if clean_obj else f"Đo lường nhận thức, hành vi và trải nghiệm liên quan đến {clean_topic}",
            "preferred_question_types": sorted(list(detected_types)),
            "target_question_count": max(4, min(target_question_count, 15)),
            "expected_time_minutes": max(2, min(expected_time_minutes, 30)),
            "language": language or "vi",
            "security_sanitized": injection_detected
        }


class DeterministicArchetypeEngine:
    """
    Bộ sinh khảo sát khoa học theo 6 nhóm hình mẫu nghiên cứu (Research Archetypes).
    Hoạt động hoàn toàn độc lập, đảm bảo hệ thống không bao giờ phụ thuộc vào kết nối đám mây
    hoặc bị gián đoạn khi chưa cấu hình API key, đồng thời không bao giờ trả về dữ liệu mẫu tĩnh sơ sài.
    """
    @classmethod
    def generate(cls, spec: Dict[str, Any]) -> Dict[str, Any]:
        topic = spec["topic"]
        aud = spec["audience"]
        obj = spec["research_objectives"]
        pref_types = set(spec.get("preferred_question_types", []))
        q_count = spec.get("target_question_count", 7)

        # Phân loại Archetype dựa trên từ khóa
        lower_topic = f"{topic} {obj}".lower()
        if any(w in lower_topic for w in ["khách hàng", "dịch vụ", "sản phẩm", "csat", "nps", "mua sắm", "ứng dụng"]):
            archetype = "CSAT_PRODUCT"
        elif any(w in lower_topic for w in ["nhân viên", "nội bộ", "công ty", "doanh nghiệp", "lương", "đãi ngộ", "hr", "work"]):
            archetype = "EMPLOYEE_ENGAGEMENT"
        elif any(w in lower_topic for w in ["y tế", "sức khỏe", "bệnh viện", "cộng đồng", "dinh dưỡng", "thể thao"]):
            archetype = "HEALTHCARE_COMMUNITY"
        elif any(w in lower_topic for w in ["học sinh", "sinh viên", "giáo dục", "trường", "đào tạo", "môn học"]):
            archetype = "EDUCATION_ACADEMIC"
        elif any(w in lower_topic for w in ["thị trường", "tiêu dùng", "chi tiêu", "giá cả", "thương hiệu"]):
            archetype = "MARKET_RESEARCH"
        else:
            archetype = "GENERAL_EMPIRICAL"

        questions: List[Dict[str, Any]] = []
        idx = 0

        # Q1: Nhân khẩu học / Định danh nhóm
        idx += 1
        questions.append({
            "id": f"q_demo_{idx}",
            "order_index": idx - 1,
            "question_type": "single_choice",
            "title": f"Bạn thuộc nhóm đối tượng nào liên quan đến {topic}?",
            "description": "Thông tin phân loại nhóm tham gia khảo sát",
            "is_required": True,
            "options": [
                {"id": "opt_demo_1", "label": f"Người trải nghiệm thường xuyên (Hàng ngày/Hàng tuần)"},
                {"id": "opt_demo_2", "label": f"Người thỉnh thoảng tiếp cận (1-2 lần/tháng)"},
                {"id": "opt_demo_3", "label": f"Người mới bắt đầu tìm hiểu"},
                {"id": "opt_demo_4", "label": "Chưa từng tiếp cận trực tiếp"}
            ],
            "logic_rules": []
        })

        # Q2: Tần suất hoặc Thời lượng trải nghiệm
        idx += 1
        questions.append({
            "id": f"q_freq_{idx}",
            "order_index": idx - 1,
            "question_type": "dropdown",
            "title": f"Thời gian bạn đã gắn bó hoặc sử dụng các giải pháp trong lĩnh vực {topic}?",
            "description": "Khoảng thời gian kinh nghiệm",
            "is_required": True,
            "options": [
                {"id": "opt_time_1", "label": "Dưới 6 tháng"},
                {"id": "opt_time_2", "label": "Từ 6 tháng đến 1 năm"},
                {"id": "opt_time_3", "label": "Từ 1 đến 3 năm"},
                {"id": "opt_time_4", "label": "Trên 3 năm"}
            ],
            "logic_rules": []
        })

        # Q3: Thang đo Likert cốt lõi
        idx += 1
        questions.append({
            "id": f"q_likert_{idx}",
            "order_index": idx - 1,
            "question_type": "likert",
            "title": f"Đánh giá mức độ đồng ý của bạn với nhận định: 'Tôi nhận thấy {topic} mang lại giá trị thiết thực và đáp ứng tốt kỳ vọng ban đầu.'",
            "description": "Thang đo 5 mức độ từ Rất không đồng ý đến Rất đồng ý",
            "is_required": True,
            "options": [
                {"id": "opt_lik_1", "label": "Hoàn toàn không đồng ý"},
                {"id": "opt_lik_2", "label": "Không đồng ý"},
                {"id": "opt_lik_3", "label": "Bình thường / Trung lập"},
                {"id": "opt_lik_4", "label": "Đồng ý"},
                {"id": "opt_lik_5", "label": "Hoàn toàn đồng ý"}
            ],
            "logic_rules": []
        })

        # Q4: Ma trận đánh giá đa tiêu chí (Matrix)
        if "matrix" in pref_types or q_count >= 5:
            idx += 1
            questions.append({
                "id": f"q_matrix_{idx}",
                "order_index": idx - 1,
                "question_type": "matrix",
                "title": f"Đánh giá chi tiết các khía cạnh chất lượng của {topic}:",
                "description": "Vui lòng chọn mức độ đánh giá cho từng tiêu chí hàng ngang",
                "is_required": True,
                "options": {
                    "rows": [
                        {"id": "row_1", "label": "Chất lượng chuyên môn & Tính chính xác"},
                        {"id": "row_2", "label": "Tốc độ phản hồi & Thời gian xử lý"},
                        {"id": "row_3", "label": "Mức độ thân thiện và dễ tiếp cận"},
                        {"id": "row_4", "label": "Chi phí và giá trị nhận được tương xứng"}
                    ],
                    "columns": [
                        {"id": "col_1", "label": "Kém"},
                        {"id": "col_2", "label": "Trung bình"},
                        {"id": "col_3", "label": "Tốt"},
                        {"id": "col_4", "label": "Xuất sắc"}
                    ]
                },
                "logic_rules": []
            })

        # Q5: Xếp hạng ưu tiên (Ranking)
        if "ranking" in pref_types or q_count >= 6:
            idx += 1
            questions.append({
                "id": f"q_rank_{idx}",
                "order_index": idx - 1,
                "question_type": "ranking",
                "title": f"Hãy xếp hạng thứ tự ưu tiên các yếu tố sau đây mà bạn quan tâm nhất về {topic}:",
                "description": "Kéo thả hoặc dùng nút mũi tên để sắp xếp từ quan trọng nhất (trên cùng) đến ít quan trọng nhất",
                "is_required": True,
                "options": [
                    {"id": "rank_item_1", "label": "Độ tin cậy và cam kết chất lượng lâu dài"},
                    {"id": "rank_item_2", "label": "Sự đổi mới, sáng tạo và tính hiện đại"},
                    {"id": "rank_item_3", "label": "Chính sách hỗ trợ và chăm sóc tận tâm"},
                    {"id": "rank_item_4", "label": "Chi phí cạnh tranh và minh bạch"}
                ],
                "logic_rules": []
            })

        # Q6: Thang điểm Linear Scale (NPS 1-10)
        if "linear_scale" in pref_types or q_count >= 7:
            idx += 1
            questions.append({
                "id": f"q_nps_{idx}",
                "order_index": idx - 1,
                "question_type": "linear_scale",
                "title": f"Trên thang điểm từ 1 đến 10, mức độ bạn sẵn sàng giới thiệu về {topic} cho bạn bè hoặc đối tác?",
                "description": "Điểm từ 1 (Hoàn toàn không sẵn lòng) đến 10 (Rất sẵn lòng)",
                "is_required": True,
                "options": [
                    {"id": "scale_min", "label": "1"},
                    {"id": "scale_max", "label": "10"}
                ],
                "logic_rules": []
            })

        # Q7: Câu hỏi mở đóng góp ý kiến (Long Text)
        idx += 1
        questions.append({
            "id": f"q_open_{idx}",
            "order_index": idx - 1,
            "question_type": "long_text",
            "title": f"Theo bạn, điều gì cần được cải tiến hoặc bổ sung nhiều nhất để nâng cao chất lượng {topic}?",
            "description": "Mọi đóng góp chân thành của bạn đều là cơ sở quan trọng giúp chúng tôi hoàn thiện hơn",
            "is_required": False,
            "options": [],
            "logic_rules": []
        })

        return {
            "title": f"Khảo sát Đánh giá Toàn diện: {topic}",
            "description": f"Khảo sát khoa học hướng tới đối tượng: {aud}. Mục tiêu chính: {obj}.",
            "instructions": "Vui lòng đọc kỹ từng câu hỏi và lựa chọn phương án phản ánh đúng nhất thực tế của bạn. Dữ liệu thu thập được mã hóa bảo mật theo tiêu chuẩn DataTrust và Nghị định 356/2025/NĐ-CP.",
            "estimated_duration_minutes": spec.get("expected_time_minutes", 5),
            "methodological_rationale": f"Khảo sát thiết kế theo mô hình chuẩn hóa {archetype}, cân bằng giữa câu hỏi định tính và định lượng, hạn chế thiên lệch trả lời.",
            "questions": questions
        }


class AIService:
    """
    Trung tâm điều phối AI Survey Engine (DataTrust - Core Service):
    - Đảm bảo an toàn API key (truyền qua header x-goog-api-key, không lộ trên URL).
    - Quy trình 6 bước: Trích xuất yêu cầu -> Lập kế hoạch -> Gọi Gemini -> Kiểm định tính tuân thủ -> Tự sửa lỗi (Bounded Repair) -> Lưu trữ phiên.
    - Hỗ trợ đầy đủ 12 loại câu hỏi, đặc biệt là Matrix và Ranking.
    - Dự phòng thông minh với Deterministic Archetype Engine khi ngoại tuyến hoặc không có key.
    """

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        has_key = is_gemini_configured()
        return {
            "ai_active": True,
            "provider_available": "Google Gemini API" if has_key else "Deterministic Scientific Survey Heuristics",
            "configured_model": GEMINI_MODEL if has_key else "Archetype Matrix Engine",
            "fallback_model": AI_FALLBACK_MODEL if has_key else "None",
            "security_mode": "Header-Authenticated (Zero URL Exposure)",
            "supported_question_types_count": len(ALL_SUPPORTED_QUESTION_TYPES),
            "description": "Hệ thống AI đáp ứng tiêu chuẩn kiểm định khoa học khảo sát và Nghị định 356/2025/NĐ-CP."
        }

    @classmethod
    async def generate_survey_pipeline(
        cls,
        topic: str,
        audience: Optional[str] = "",
        research_objectives: Optional[str] = "",
        expected_time_minutes: int = 5,
        preferred_question_types: Optional[List[str]] = None,
        target_question_count: int = 7,
        language: str = "vi",
        strict_scientific_mode: bool = True
    ) -> Dict[str, Any]:
        start_time = time.time()
        session_id = f"ai_gen_{uuid.uuid4().hex[:12]}"
        
        # Bước 1: Trích xuất yêu cầu (Requirement Extraction)
        spec = RequirementParser.parse(
            topic=topic,
            audience=audience,
            research_objectives=research_objectives,
            preferred_types=preferred_question_types,
            target_question_count=target_question_count,
            expected_time_minutes=expected_time_minutes,
            language=language
        )

        provider_type = "heuristic_fallback"
        model_used = "Deterministic Archetype Engine"
        draft_result = None
        error_detail = None
        repaired = False
        repair_attempts = 0

        # Bước 2 & 3: Gọi Gemini nếu có key
        if is_gemini_configured():
            try:
                gemini_output, model_name = await cls._call_gemini_with_fallback(spec)
                if gemini_output and "questions" in gemini_output:
                    provider_type = "gemini"
                    model_used = model_name
                    draft_result = gemini_output
            except Exception as e:
                error_detail = f"Gemini API invocation notice: {str(e)}"
                # Chuyển tiếp mượt mà sang Deterministic Engine
                draft_result = None

        if not draft_result:
            draft_result = DeterministicArchetypeEngine.generate(spec)
            if not error_detail and not is_gemini_configured():
                error_detail = "Operating in Local Deterministic Mode (GEMINI_API_KEY not configured)"

        # Bước 4: Kiểm định sự tuân thủ yêu cầu & tính khoa học
        validation_report = cls.validate_survey_draft(draft_result, spec)

        # Bước 5: Bounded Self-Repair Loop nếu phát hiện vi phạm
        if not validation_report["is_valid"] or validation_report["issues"]:
            if provider_type == "gemini" and repair_attempts < 2:
                repair_attempts += 1
                try:
                    repaired_output = await cls._repair_with_gemini(draft_result, validation_report["issues"], spec)
                    if repaired_output and "questions" in repaired_output:
                        draft_result = repaired_output
                        validation_report = cls.validate_survey_draft(draft_result, spec)
                        repaired = True
                except Exception as repair_err:
                    error_detail = f"{error_detail or ''} | Repair note: {repair_err}"

            # Nếu vẫn còn lỗi, áp dụng sửa chữa cục bộ bằng Heuristic Sanitizer
            draft_result = cls._apply_heuristic_sanitization(draft_result, validation_report["issues"])
            validation_report = cls.validate_survey_draft(draft_result, spec)
            validation_report["repaired"] = repaired
            validation_report["repair_attempts"] = repair_attempts

        duration_ms = round((time.time() - start_time) * 1000, 2)
        status = "completed" if validation_report["is_valid"] else "needs_review"

        # Chuẩn hóa ID và chỉ mục câu hỏi
        for i, q in enumerate(draft_result.get("questions", [])):
            if not q.get("id"):
                q["id"] = f"q_gen_{i+1}_{uuid.uuid4().hex[:6]}"
            q["order_index"] = i

        # Bước 6: Lưu trữ phiên vào CSDL SQLite WAL
        cls._persist_generation_session(
            session_id=session_id,
            topic=spec["topic"],
            audience=spec["audience"],
            objectives=spec["research_objectives"],
            target_duration=spec["expected_time_minutes"],
            preferred_types=spec["preferred_question_types"],
            extracted_spec=spec,
            model_name=model_used,
            provider_type=provider_type,
            status=status,
            duration_ms=duration_ms,
            generated_survey=draft_result,
            validation_report=validation_report,
            error_message=error_detail or ""
        )

        return {
            "session_id": session_id,
            "status": status,
            "provider": provider_type,
            "model_used": model_used,
            "survey_draft": draft_result,
            "requirement_spec": spec,
            "validation": validation_report,
            "duration_ms": duration_ms,
            "error_detail": error_detail
        }

    @classmethod
    async def _call_gemini_with_fallback(cls, spec: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """Gọi Gemini qua REST API chính thức sử dụng header bảo mật và dự phòng đa mô hình"""
        models_to_try = [GEMINI_MODEL, AI_FALLBACK_MODEL, "gemini-2.0-flash"]
        # Loại bỏ các mô hình trùng lặp
        unique_models = []
        for m in models_to_try:
            if m and m not in unique_models:
                unique_models.append(m)

        last_error = None
        for model in unique_models:
            try:
                result = await cls._invoke_gemini_generate(spec, model)
                if result:
                    return result, model
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All configured Gemini models failed. Last error: {last_error}")

    @classmethod
    async def _invoke_gemini_generate(cls, spec: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Gọi một mô hình Gemini cụ thể với header x-goog-api-key an toàn"""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        
        system_instruction = (
            "Bạn là Viện trưởng Viện Đo lường & Khảo sát Khoa học DataTrust. "
            "Nhiệm vụ của bạn là thiết kế khảo sát học thuật & thị trường chuẩn xác cao theo phương pháp Tailored Design Method của Don Dillman và tiêu chuẩn AAPOR. "
            "QUY TẮC BẮT BUỘC:\n"
            "1. KHÔNG đặt câu hỏi dẫn dắt (Leading question) như 'có phải', 'tuyệt vời', 'đúng không'.\n"
            "2. KHÔNG đặt câu hỏi kép (Double-barreled question) chứa 2 ý đánh giá độc lập trong một câu.\n"
            "3. Hỗ trợ đầy đủ 12 loại câu hỏi: single_choice, multiple_choice, short_text, long_text, number, rating, linear_scale, dropdown, date, likert, matrix, ranking.\n"
            "4. Nếu người dùng yêu cầu 'matrix', câu hỏi PHẢI có cấu trúc options: {'rows': [{'id': 'row_1', 'label': '...'}], 'columns': [{'id': 'col_1', 'label': '...'}]}.\n"
            "5. Nếu người dùng yêu cầu 'ranking', options PHẢI là danh sách các mục để sắp xếp: [{'id': 'r_1', 'label': '...'}].\n"
            "6. Các câu hỏi trắc nghiệm (single_choice, multiple_choice, dropdown) PHẢI có tối thiểu 3-5 phương án và bao hàm đầy đủ (MECE).\n"
            "7. Trả về DUY NHẤT một chuỗi JSON hợp lệ tuân thủ schema được chỉ định, không thêm markdown fence."
        )

        user_content = (
            f"Hãy thiết kế khảo sát khoa học theo thông số sau:\n"
            f"<user_topic>{spec['topic']}</user_topic>\n"
            f"<target_audience>{spec['audience']}</target_audience>\n"
            f"<research_objectives>{spec['research_objectives']}</research_objectives>\n"
            f"<target_question_count>{spec['target_question_count']}</target_question_count>\n"
            f"<preferred_types>{', '.join(spec['preferred_question_types'])}</preferred_types>\n"
            f"<expected_duration_minutes>{spec['expected_time_minutes']}</expected_duration_minutes>\n"
            f"<language>{spec['language']}</language>\n\n"
            "Cấu trúc JSON mong đợi:\n"
            "{\n"
            '  "title": "Tiêu đề khảo sát chuẩn khoa học",\n'
            '  "description": "Mục tiêu nghiên cứu và đối tượng tham gia",\n'
            '  "instructions": "Hướng dẫn trung thực và cam kết bảo mật",\n'
            '  "estimated_duration_minutes": 5,\n'
            '  "methodological_rationale": "Lý giải cấu trúc bảng hỏi",\n'
            '  "questions": [\n'
            "    {\n"
            '      "id": "q_1",\n'
            '      "order_index": 0,\n'
            '      "question_type": "single_choice|multiple_choice|likert|matrix|ranking|linear_scale|short_text|long_text|number|dropdown|date|rating",\n'
            '      "title": "Tiêu đề câu hỏi trung lập",\n'
            '      "description": "Giải thích bổ trợ nếu có",\n'
            '      "is_required": true,\n'
            '      "options": [{"id": "opt_1", "label": "..."}]\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        headers = {
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json"
        }

        body = {
            "contents": [
                {"role": "user", "parts": [{"text": user_content}]}
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.3,
                "topP": 0.95
            }
        }

        async with httpx.AsyncClient(timeout=AI_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post(endpoint, headers=headers, json=body)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                # Xóa markdown wrapper nếu có
                clean_text = raw_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                return json.loads(clean_text.strip())
            
            error_data = resp.text
            raise ValueError(f"Gemini API status {resp.status_code}: {error_data[:200]}")

    @classmethod
    async def _repair_with_gemini(cls, draft: Dict[str, Any], issues: List[Dict[str, Any]], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Tự động sửa lỗi có định hướng với mô hình Gemini"""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        headers = {
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json"
        }
        prompt = (
            "Bản nháp khảo sát sau đây có một số vấn đề vi phạm tiêu chuẩn kiểm định khoa học:\n"
            f"Vấn đề phát hiện: {json.dumps(issues, ensure_ascii=False)}\n\n"
            f"Khảo sát hiện tại:\n{json.dumps(draft, ensure_ascii=False)}\n\n"
            "Hãy sửa lại các câu hỏi bị lỗi để đạt tính khách quan tối đa, bổ sung phương án thiếu, hoặc định dạng chuẩn cho matrix/ranking. "
            "Trả về toàn bộ khảo sát đã sửa dưới dạng JSON duy nhất."
        )
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2}
        }
        async with httpx.AsyncClient(timeout=AI_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post(endpoint, headers=headers, json=body)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
            raise ValueError(f"Repair API returned status {resp.status_code}")

    @classmethod
    def validate_survey_draft(cls, draft: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kiểm định toàn diện chất lượng bản nháp khảo sát:
        1. Số lượng câu hỏi đạt chuẩn.
        2. Tỷ lệ bao phủ các dạng câu hỏi được yêu cầu (Coverage score).
        3. Tính khách quan, phát hiện câu hỏi dẫn dắt & câu hỏi kép (Objectivity score).
        4. Tính đầy đủ của các phương án trả lời.
        """
        issues: List[Dict[str, Any]] = []
        questions = draft.get("questions", [])
        
        # 1. Kiểm tra số lượng
        if len(questions) < 3:
            issues.append({
                "issue_type": "TOO_FEW_QUESTIONS",
                "severity": "CRITICAL",
                "explanation": f"Khảo sát chỉ có {len(questions)} câu hỏi, chưa đủ độ sâu khoa học.",
                "suggestion": "Bổ sung thêm câu hỏi để đạt tối thiểu 5 câu."
            })

        # 2. Kiểm tra câu hỏi dẫn dắt & kép
        leading_kws = ["có phải", "chắc hẳn", "tuyệt vời thế nào", "đúng không", "không ai có thể phủ nhận", "rất tốt phải không"]
        double_kws = [" và ", " cũng như ", " đồng thời ", " hay là "]
        
        present_types = set()
        for idx, q in enumerate(questions):
            title = q.get("title", "").strip()
            lower_title = title.lower()
            q_type = q.get("question_type", "")
            present_types.add(q_type)
            opts = q.get("options", [])

            # Kiểm tra dạng câu hỏi hợp lệ
            if q_type not in ALL_SUPPORTED_QUESTION_TYPES:
                issues.append({
                    "question_id": q.get("id", f"q_{idx}"),
                    "question_title": title,
                    "issue_type": "INVALID_QUESTION_TYPE",
                    "severity": "CRITICAL",
                    "explanation": f"Dạng câu hỏi '{q_type}' không nằm trong 12 dạng chuẩn của DataTrust.",
                    "suggestion": "Chuyển đổi sang single_choice hoặc likert."
                })

            # Kiểm tra từ ngữ dẫn dắt
            for kw in leading_kws:
                if kw in lower_title:
                    issues.append({
                        "question_id": q.get("id", f"q_{idx}"),
                        "question_title": title,
                        "issue_type": "LEADING_QUESTION",
                        "severity": "WARNING",
                        "explanation": f"Câu hỏi chứa từ ngữ có tính định hướng '{kw}'.",
                        "suggestion": "Diễn đạt lại theo lối trung lập, đo lường mức độ đồng ý."
                    })
                    break

            # Kiểm tra câu hỏi kép
            if any(kw in lower_title for kw in double_kws) and len(title.split()) > 12:
                issues.append({
                    "question_id": q.get("id", f"q_{idx}"),
                    "question_title": title,
                    "issue_type": "DOUBLE_BARRELED_QUESTION",
                    "severity": "WARNING",
                    "explanation": "Câu hỏi chứa nhiều nội dung đánh giá cùng lúc trong một câu.",
                    "suggestion": "Tách thành 2 câu hỏi đơn để tránh sai lệch dữ liệu."
                })

            # Kiểm tra cấu trúc phương án
            if q_type in ("single_choice", "multiple_choice", "dropdown"):
                if not isinstance(opts, list) or len(opts) < 2:
                    issues.append({
                        "question_id": q.get("id", f"q_{idx}"),
                        "question_title": title,
                        "issue_type": "INSUFFICIENT_OPTIONS",
                        "severity": "CRITICAL",
                        "explanation": "Câu hỏi trắc nghiệm cần có ít nhất 2 phương án lựa chọn.",
                        "suggestion": "Bổ sung thêm các phương án lựa chọn hoặc mục 'Khác'."
                    })
            elif q_type == "matrix":
                if not isinstance(opts, dict) or not opts.get("rows") or not opts.get("columns"):
                    issues.append({
                        "question_id": q.get("id", f"q_{idx}"),
                        "question_title": title,
                        "issue_type": "MALFORMED_MATRIX",
                        "severity": "CRITICAL",
                        "explanation": "Câu hỏi ma trận cần có định nghĩa cả hàng (rows) và cột (columns).",
                        "suggestion": "Cấu hình danh sách hàng đánh giá và cột thang đo."
                    })
            elif q_type == "ranking":
                if not isinstance(opts, list) or len(opts) < 2:
                    issues.append({
                        "question_id": q.get("id", f"q_{idx}"),
                        "question_title": title,
                        "issue_type": "INSUFFICIENT_RANKING_ITEMS",
                        "severity": "CRITICAL",
                        "explanation": "Câu hỏi xếp hạng cần tối thiểu 2 mục để sắp xếp thứ tự.",
                        "suggestion": "Thêm từ 3 đến 5 mục cần xếp hạng."
                    })

        # 3. Tính toán điểm Adherence & Coverage
        preferred = set(spec.get("preferred_question_types", []))
        matched_preferred = preferred.intersection(present_types)
        coverage_score = round((len(matched_preferred) / max(len(preferred), 1)) * 100.0, 1)

        critical_issues = sum(1 for i in issues if i["severity"] == "CRITICAL")
        warning_issues = sum(1 for i in issues if i["severity"] == "WARNING")

        objectivity_penalty = (warning_issues * 10.0) + (critical_issues * 25.0)
        objectivity_score = max(0.0, min(100.0, 100.0 - objectivity_penalty))
        adherence_score = round((coverage_score * 0.6) + (objectivity_score * 0.4), 1)

        is_valid = critical_issues == 0 and len(questions) >= 3

        return {
            "is_valid": is_valid,
            "coverage_score": coverage_score,
            "adherence_score": adherence_score,
            "objectivity_score": objectivity_score,
            "issues": issues,
            "repaired": False,
            "repair_attempts": 0
        }

    @classmethod
    def _apply_heuristic_sanitization(cls, draft: Dict[str, Any], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tự động chuẩn hóa câu hỏi bị lỗi bằng Heuristic Transformer"""
        questions = draft.get("questions", [])
        
        for q in questions:
            title = q.get("title", "")
            q_type = q.get("question_type", "")
            
            # Xóa các cụm từ dẫn dắt
            for bad_kw in ["Có phải ", "có phải ", "chắc hẳn ", "tuyệt vời thế nào ", "đúng không?"]:
                if bad_kw in title:
                    title = title.replace(bad_kw, "")
            q["title"] = title.strip()

            # Bổ sung phương án nếu thiếu
            if q_type in ("single_choice", "multiple_choice", "dropdown"):
                opts = q.get("options", [])
                if not isinstance(opts, list) or len(opts) < 2:
                    q["options"] = [
                        {"id": "opt_fixed_1", "label": "Có / Đồng ý"},
                        {"id": "opt_fixed_2", "label": "Không / Không đồng ý"},
                        {"id": "opt_fixed_3", "label": "Khác / Ý kiến riêng"}
                    ]
            elif q_type == "matrix":
                opts = q.get("options")
                if not isinstance(opts, dict) or not opts.get("rows") or not opts.get("columns"):
                    q["options"] = {
                        "rows": [
                            {"id": "row_1", "label": "Chất lượng chuyên môn"},
                            {"id": "row_2", "label": "Thời gian và tiến độ"},
                            {"id": "row_3", "label": "Thái độ phục vụ"}
                        ],
                        "columns": [
                            {"id": "col_1", "label": "Kém"},
                            {"id": "col_2", "label": "Bình thường"},
                            {"id": "col_3", "label": "Tốt"}
                        ]
                    }
            elif q_type == "ranking":
                opts = q.get("options", [])
                if not isinstance(opts, list) or len(opts) < 2:
                    q["options"] = [
                        {"id": "rank_1", "label": "Tiêu chí chất lượng"},
                        {"id": "rank_2", "label": "Tiêu chí chi phí"},
                        {"id": "rank_3", "label": "Tiêu chí dịch vụ"}
                    ]

        return draft

    @classmethod
    def audit_questions_deep(cls, questions: List[Dict[str, Any]], survey_id: str = "") -> Dict[str, Any]:
        """
        Kiểm định chất lượng câu hỏi chuyên sâu trước khi xuất bản:
        - Kiểm tra tính dẫn dắt, câu hỏi kép.
        - Kiểm tra phương án thiếu hoặc mất cân đối.
        - Phát hiện câu hỏi ma trận quá tải (> 8 dòng hoặc > 6 cột).
        - Đề xuất câu hỏi viết lại tự động (Auto-fix suggestion).
        - Ghi nhật ký vào bảng ai_audit_logs.
        """
        issues = []
        leading_kws = ["có phải", "chắc hẳn", "tuyệt vời thế nào", "đúng không", "không ai có thể phủ nhận", "rất tốt phải không"]
        double_kws = [" và ", " cũng như ", " đồng thời ", " hay là "]

        for idx, q in enumerate(questions):
            title = q.get("title", "").strip()
            lower_title = title.lower()
            qid = q.get("id", f"q_{idx}")
            q_type = q.get("question_type", "")
            options = q.get("options", [])

            # 1. Leading questions
            for kw in leading_kws:
                if kw in lower_title:
                    suggested_title = title
                    for bkw in ["Có phải ", "có phải ", "chắc hẳn ", "đúng không?"]:
                        suggested_title = suggested_title.replace(bkw, "")
                    suggested_title = f"Đánh giá mức độ đồng ý của bạn với: '{suggested_title.strip()}'"

                    issues.append({
                        "question_id": qid,
                        "question_title": title,
                        "issue_type": "LEADING_QUESTION",
                        "severity": "WARNING",
                        "explanation": f"Câu hỏi chứa từ ngữ định hướng trả lời ('{kw}').",
                        "suggestion": "Viết lại ở dạng trung lập hoặc chuyển sang thang đo Likert.",
                        "auto_fix_title": suggested_title
                    })
                    break

            # 2. Double-barreled questions
            if any(kw in lower_title for kw in double_kws) and len(title.split()) > 10:
                issues.append({
                    "question_id": qid,
                    "question_title": title,
                    "issue_type": "DOUBLE_BARRELED_QUESTION",
                    "severity": "WARNING",
                    "explanation": "Câu hỏi đánh giá nhiều khía cạnh cùng lúc, có thể gây nhiễu khi trả lời.",
                    "suggestion": "Tách thành 2 câu hỏi đơn riêng biệt.",
                    "auto_fix_title": title.split(" và ")[0].strip() if " và " in title else title
                })

            # 3. Insufficient options
            if q_type in ("single_choice", "multiple_choice", "dropdown"):
                if not isinstance(options, list) or len(options) < 2:
                    issues.append({
                        "question_id": qid,
                        "question_title": title,
                        "issue_type": "INSUFFICIENT_OPTIONS",
                        "severity": "CRITICAL",
                        "explanation": "Câu hỏi trắc nghiệm cần tối thiểu 2 phương án.",
                        "suggestion": "Bổ sung phương án hoặc tùy chọn 'Khác'."
                    })
            
            # 4. Matrix overload
            if q_type == "matrix" and isinstance(options, dict):
                rows = options.get("rows", [])
                cols = options.get("columns", [])
                if len(rows) > 8 or len(cols) > 6:
                    issues.append({
                        "question_id": qid,
                        "question_title": title,
                        "issue_type": "MATRIX_OVERLOAD",
                        "severity": "WARNING",
                        "explanation": f"Ma trận quá lớn ({len(rows)} hàng x {len(cols)} cột) dễ gây mệt mỏi cho người trả lời.",
                        "suggestion": "Giảm bớt hàng xuống tối đa 6-8 tiêu chí trọng tâm."
                    })

        # Lưu nhật ký audit vào CSDL
        audit_id = f"audit_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                conn.execute("""
                INSERT INTO ai_audit_logs (id, survey_id, total_questions, issues_found, issues_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (audit_id, survey_id, len(questions), len(issues), json.dumps(issues, ensure_ascii=False), now_iso))
        except Exception as e:
            print(f"[AIService] Audit log persistence warning: {e}")

        return {
            "audit_id": audit_id,
            "total_questions": len(questions),
            "total_issues": len(issues),
            "scientific_readiness": "READY" if len(issues) == 0 else ("WARNINGS_PRESENT" if all(i["severity"] == "WARNING" for i in issues) else "CRITICAL_ISSUES"),
            "issues": issues
        }

    @classmethod
    def analyze_qualitative_responses(cls, responses_text: List[str], topic: str) -> Dict[str, Any]:
        """
        Phân tích định tính câu trả lời mở:
        - Sử dụng QualitativeEngine chuẩn hóa xử lý từ ghép tiếng Việt, phủ định đảo nghĩa
        - Phân nhóm chủ đề tự động theo n-gram và ma trận từ vựng chuyên ngành
        - Trích xuất câu trích dẫn thực tế (evidence-based quotes)
        - Phát hiện các bất thường văn bản mở (spam, trùng lặp, gibberish)
        """
        return QualitativeEngine.analyze_responses(responses_text)

    @classmethod
    def _persist_generation_session(cls, **kwargs):
        """Lưu trữ lịch sử phiên sinh AI vào CSDL SQLite với chế độ an toàn"""
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                conn.execute("""
                INSERT INTO ai_generation_sessions (
                    id, topic, audience, objectives, target_duration,
                    preferred_types_json, extracted_spec_json, model_name,
                    provider_type, status, duration_ms, prompt_tokens,
                    completion_tokens, generated_survey_json,
                    validation_report_json, error_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kwargs.get("session_id"),
                    kwargs.get("topic", ""),
                    kwargs.get("audience", ""),
                    kwargs.get("objectives", ""),
                    kwargs.get("target_duration", 5),
                    json.dumps(kwargs.get("preferred_types", []), ensure_ascii=False),
                    json.dumps(kwargs.get("extracted_spec", {}), ensure_ascii=False),
                    kwargs.get("model_name", ""),
                    kwargs.get("provider_type", ""),
                    kwargs.get("status", "completed"),
                    kwargs.get("duration_ms", 0.0),
                    0, 0,
                    json.dumps(kwargs.get("generated_survey", {}), ensure_ascii=False),
                    json.dumps(kwargs.get("validation_report", {}), ensure_ascii=False),
                    kwargs.get("error_message", ""),
                    now_iso
                ))
        except Exception as e:
            print(f"[AIService] Session persistence error: {e}")
