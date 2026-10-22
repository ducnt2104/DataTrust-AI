from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter
from app.engine.ai_assistant import AIAssistant

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

class GenerateSurveyRequest(BaseModel):
    topic: str
    audience: Optional[str] = ""
    expected_time_minutes: int = 5

class AuditQuestionsRequest(BaseModel):
    questions: List[Dict[str, Any]]

@router.get("/status")
def get_ai_status():
    """Kiểm tra trạng thái cấu hình của AI Assistant"""
    is_active = AIAssistant.is_ai_configured()
    return {
        "ai_active": is_active,
        "provider": "Google Gemini API" if is_active else "Deterministic Scientific Survey Heuristics",
        "description": "Hệ thống AI đang hoạt động đầy đủ với cơ chế tự động chuyển đổi thông minh."
    }

@router.post("/generate-survey")
async def generate_survey_draft(payload: GenerateSurveyRequest):
    """Sinh bản nháp khảo sát khoa học theo ngôn ngữ tự nhiên"""
    draft = await AIAssistant.generate_survey_draft(
        topic=payload.topic,
        audience=payload.audience,
        expected_time_minutes=payload.expected_time_minutes
    )
    return draft

@router.post("/audit-questions")
def audit_survey_questions(payload: AuditQuestionsRequest):
    """Kiểm định chất lượng câu hỏi trước khi xuất bản"""
    issues = AIAssistant.audit_questions(payload.questions)
    return {
        "total_issues": len(issues),
        "issues": issues
    }
