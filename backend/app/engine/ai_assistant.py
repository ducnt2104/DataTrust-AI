import json
import os
import re
from typing import Dict, List, Any, Optional
import httpx
from app.config import GEMINI_API_KEY

class AIAssistant:
    """
    Module hỗ trợ AI cho DataTrust AI:
    - Sinh bản nháp khảo sát theo ngôn ngữ tự nhiên.
    - Kiểm định câu hỏi trước khi xuất bản (phát hiện câu hỏi dẫn dắt, câu hỏi kép, thiên lệch).
    - Phân tích định tính câu trả lời mở.
    Hỗ trợ chế độ Google Gemini API và chế độ dự phòng thông minh (Deterministic Fallback Adapter)
    khi chưa có API key, đảm bảo hệ thống không bao giờ bị gián đoạn hoạt động.
    """

    @classmethod
    def is_ai_configured(cls) -> bool:
        return bool(GEMINI_API_KEY and len(GEMINI_API_KEY.strip()) > 10)

    @classmethod
    async def generate_survey_draft(
        cls,
        topic: str,
        audience: Optional[str] = "",
        expected_time_minutes: int = 5
    ) -> Dict[str, Any]:
        """Tạo dàn ý khảo sát hoàn chỉnh gồm tiêu đề, mô tả và danh sách câu hỏi đa dạng"""
        if cls.is_ai_configured():
            try:
                return await cls._gemini_generate_survey(topic, audience, expected_time_minutes)
            except Exception as e:
                print(f"[AIAssistant] Gemini API error, falling back to heuristic engine: {e}")

        # Deterministic Heuristic Engine
        return cls._heuristic_generate_survey(topic, audience)

    @classmethod
    def audit_questions(cls, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Kiểm định chất lượng câu hỏi trước khi xuất bản:
        - Phát hiện câu hỏi dẫn dắt (Leading question).
        - Phát hiện câu hỏi kép (Double-barreled question).
        - Kiểm tra độ đầy đủ của phương án trả lời.
        """
        audit_results = []

        leading_keywords = ["có phải", "chắc hẳn", "tuyệt vời thế nào", "đúng không", "không ai có thể phủ nhận"]
        double_barreled_keywords = [" và ", " cũng như ", " đồng thời ", " hay là "]

        for q in questions:
            title = q.get("title", "").strip().lower()
            qid = q.get("id")
            q_type = q.get("question_type")
            options = q.get("options", [])

            # 1. Kiểm tra câu hỏi dẫn dắt
            for kw in leading_keywords:
                if kw in title:
                    audit_results.append({
                        "question_id": qid,
                        "question_title": q.get("title"),
                        "issue_type": "LEADING_QUESTION",
                        "severity": "WARNING",
                        "explanation": f"Câu hỏi chứa từ ngữ có tính định hướng người trả lời ('{kw}').",
                        "suggestion": "Hãy viết lại câu hỏi ở dạng trung lập (ví dụ: 'Đánh giá mức độ hài lòng của bạn đối với...')"
                    })
                    break

            # 2. Kiểm tra câu hỏi kép (Hỏi 2 vấn đề trong 1 câu)
            if any(kw in title for kw in double_barreled_keywords) and len(title.split()) > 10:
                audit_results.append({
                    "question_id": qid,
                    "question_title": q.get("title"),
                    "issue_type": "DOUBLE_BARRELED_QUESTION",
                    "severity": "WARNING",
                    "explanation": "Câu hỏi có dấu hiệu chứa nhiều nội dung đánh giá cùng lúc trong một câu.",
                    "suggestion": "Tách thành 2 câu hỏi riêng biệt để người tham gia không bối rối khi có đánh giá trái ngược nhau."
                })

            # 3. Kiểm tra số lượng phương án
            if q_type in ("single_choice", "multiple_choice", "dropdown"):
                if len(options) < 2:
                    audit_results.append({
                        "question_id": qid,
                        "question_title": q.get("title"),
                        "issue_type": "INSUFFICIENT_OPTIONS",
                        "severity": "CRITICAL",
                        "explanation": "Câu hỏi trắc nghiệm cần có tối thiểu 2 phương án lựa chọn.",
                        "suggestion": "Bổ sung thêm các phương án hoặc tùy chọn 'Khác'."
                    })

        return audit_results

    @classmethod
    def _heuristic_generate_survey(cls, topic: str, audience: Optional[str] = "") -> Dict[str, Any]:
        """Bộ sinh khảo sát thông minh dựa trên mẫu chuẩn khoa học xã hội & thị trường"""
        t = topic.strip()
        aud = f" cho đối tượng {audience.strip()}" if audience and audience.strip() else ""

        return {
            "title": f"Khảo sát về {t}{aud}",
            "description": f"Mục tiêu: Đánh giá thực trạng, trải nghiệm và nhu cầu liên quan đến {t}.",
            "instructions": "Vui lòng trả lời trung thực các câu hỏi dưới đây. Thông tin của bạn được ẩn danh và phục vụ cho mục đích nghiên cứu chất lượng.",
            "questions": [
                {
                    "title": "Bạn thuộc nhóm độ tuổi nào dưới đây?",
                    "question_type": "single_choice",
                    "is_required": True,
                    "description": "Thông tin nhân khẩu học cơ bản",
                    "options": [
                        {"id": "opt_age_1", "label": "Dưới 18 tuổi"},
                        {"id": "opt_age_2", "label": "18 - 25 tuổi"},
                        {"id": "opt_age_3", "label": "26 - 35 tuổi"},
                        {"id": "opt_age_4", "label": "Trên 35 tuổi"}
                    ]
                },
                {
                    "title": f"Mức độ thường xuyên bạn tiếp cận hoặc sử dụng {t}?",
                    "question_type": "single_choice",
                    "is_required": True,
                    "description": "Tần suất trải nghiệm",
                    "options": [
                        {"id": "opt_freq_1", "label": "Hàng ngày"},
                        {"id": "opt_freq_2", "label": "Vài lần một tuần"},
                        {"id": "opt_freq_3", "label": "Vài lần một tháng"},
                        {"id": "opt_freq_4", "label": "Hiếm khi hoặc Chưa bao giờ"}
                    ]
                },
                {
                    "title": f"Đánh giá tổng quan mức độ hài lòng của bạn về {t}:",
                    "question_type": "likert",
                    "is_required": True,
                    "description": "Thang đo 5 mức độ",
                    "options": [
                        {"id": "opt_lik_1", "label": "Rất không hài lòng"},
                        {"id": "opt_lik_2", "label": "Không hài lòng"},
                        {"id": "opt_lik_3", "label": "Bình thường / Trung lập"},
                        {"id": "opt_lik_4", "label": "Hài lòng"},
                        {"id": "opt_lik_5", "label": "Rất hài lòng"}
                    ]
                },
                {
                    "title": "Những yếu tố nào sau đây bạn quan tâm nhất? (Chọn tối đa 3)",
                    "question_type": "multiple_choice",
                    "is_required": False,
                    "description": "Chọn nhiều phương án",
                    "options": [
                        {"id": "opt_fac_1", "label": "Chất lượng và độ tin cậy"},
                        {"id": "opt_fac_2", "label": "Chi phí hợp lý"},
                        {"id": "opt_fac_3", "label": "Tính tiện dụng và tốc độ"},
                        {"id": "opt_fac_4", "label": "Chính sách hỗ trợ khách hàng"}
                    ]
                },
                {
                    "title": "Bạn có sẵn sàng giới thiệu điều này cho bạn bè, đồng nghiệp không?",
                    "question_type": "linear_scale",
                    "is_required": True,
                    "description": "Thang điểm Net Promoter Score (NPS) từ 1 (Hoàn toàn không) đến 10 (Rất sẵn lòng)",
                    "options": [
                        {"id": "scale_min", "label": "1"},
                        {"id": "scale_max", "label": "10"}
                    ]
                },
                {
                    "title": "Đóng góp ý kiến hoặc đề xuất cải tiến của bạn:",
                    "question_type": "long_text",
                    "is_required": False,
                    "description": "Chia sẻ ý kiến tự do để giúp chúng tôi nâng cao chất lượng",
                    "options": []
                }
            ]
        }

    @classmethod
    async def _gemini_generate_survey(cls, topic: str, audience: str, minutes: int) -> Dict[str, Any]:
        """Gọi Gemini API nếu có key"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        prompt_text = (
            f"Bạn là chuyên gia thiết kế khảo sát khoa học DataTrust AI. Hãy tạo một khảo sát chuẩn xác về chủ đề: '{topic}'. "
            f"Đối tượng: '{audience}'. Thời lượng làm bài dự kiến: {minutes} phút. "
            "Trả về DUY NHẤT một JSON hợp lệ có định dạng: "
            "{\"title\": \"...\", \"description\": \"...\", \"instructions\": \"...\", \"questions\": ["
            "{\"title\": \"...\", \"question_type\": \"single_choice|multiple_choice|likert|linear_scale|short_text|long_text\", "
            "\"is_required\": true, \"description\": \"...\", \"options\": [{\"id\": \"opt_1\", \"label\": \"...\"}]}]}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json={
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            })
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
            raise ValueError(f"Gemini API returned status {resp.status_code}")
