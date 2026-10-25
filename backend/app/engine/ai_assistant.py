from typing import Dict, List, Any, Optional
from app.engine.ai_service import AIService
from app.config import is_gemini_configured

class AIAssistant:
    """
    Adapter tương thích ngược (Backward-Compatibility Layer) cho AIAssistant.
    Toàn bộ xử lý AI đã được nâng cấp lên AIService chuẩn kiến trúc 6 bước,
    bảo mật Header-Auth và hỗ trợ đầy đủ 12 loại câu hỏi khoa học.
    """

    @classmethod
    def is_ai_configured(cls) -> bool:
        return is_gemini_configured()

    @classmethod
    async def generate_survey_draft(
        cls,
        topic: str,
        audience: Optional[str] = "",
        expected_time_minutes: int = 5,
        research_objectives: Optional[str] = "",
        preferred_question_types: Optional[List[str]] = None,
        target_question_count: int = 7
    ) -> Dict[str, Any]:
        """Tạo dàn ý khảo sát hoàn chỉnh bằng AIService pipeline"""
        result = await AIService.generate_survey_pipeline(
            topic=topic,
            audience=audience,
            research_objectives=research_objectives,
            expected_time_minutes=expected_time_minutes,
            preferred_question_types=preferred_question_types,
            target_question_count=target_question_count
        )
        # Trả về đối tượng survey_draft để tương thích với các component frontend hiện tại
        draft = result.get("survey_draft", {})
        draft["ai_metadata"] = {
            "session_id": result.get("session_id"),
            "provider": result.get("provider"),
            "model_used": result.get("model_used"),
            "validation": result.get("validation"),
            "duration_ms": result.get("duration_ms")
        }
        return draft

    @classmethod
    def audit_questions(cls, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Kiểm định chất lượng câu hỏi tương thích ngược"""
        audit_res = AIService.audit_questions_deep(questions)
        return audit_res.get("issues", [])
