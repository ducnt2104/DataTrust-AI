import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Request
from app.engine.ai_service import AIService
from app.database import get_db
from app.middleware.rate_limiter import ai_generation_limiter
from app.schemas import CognitivePretestRequest, CognitivePretestReport

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

class GenerateSurveyRequest(BaseModel):
    topic: str
    audience: Optional[str] = ""
    research_objectives: Optional[str] = ""
    expected_time_minutes: int = 5
    preferred_question_types: Optional[List[str]] = Field(default_factory=list)
    target_question_count: Optional[int] = 7
    language: Optional[str] = "vi"
    strict_scientific_mode: bool = True

class AuditQuestionsRequest(BaseModel):
    survey_id: Optional[str] = ""
    questions: List[Dict[str, Any]]

class QualitativeAnalysisRequest(BaseModel):
    survey_id: str
    question_id: Optional[str] = None
    sample_limit: int = 50

@router.get("/status")
def get_ai_status():
    """Kiểm tra trạng thái cấu hình và năng lực của AI Survey Engine"""
    return AIService.get_status()

@router.post("/generate-survey")
@router.post("/generate-survey-advanced")
async def generate_survey_draft(payload: GenerateSurveyRequest, request: Request):
    """
    Sinh bản nháp khảo sát khoa học theo chuẩn Don Dillman & AAPOR.
    Tự động trích xuất yêu cầu, thiết lập thang đo, kiểm định tính khách quan
    và tự sửa lỗi trước khi xuất bản.
    """
    # 0. Giới hạn tốc độ sinh AI (Rate Limiting)
    ai_generation_limiter.check(request)

    if not payload.topic or not payload.topic.strip():
        raise HTTPException(status_code=400, detail="Chủ đề khảo sát không được để trống.")
    
    # Giới hạn độ dài đầu vào để ngăn chặn lạm dụng tài nguyên
    if len(payload.topic) > 2000 or (payload.research_objectives and len(payload.research_objectives) > 3000):
        raise HTTPException(status_code=400, detail="Văn bản yêu cầu vượt quá giới hạn an toàn (tối đa 2000 ký tự).")

    pipeline_result = await AIService.generate_survey_pipeline(
        topic=payload.topic,
        audience=payload.audience,
        research_objectives=payload.research_objectives,
        expected_time_minutes=payload.expected_time_minutes,
        preferred_question_types=payload.preferred_question_types,
        target_question_count=payload.target_question_count or 7,
        language=payload.language or "vi",
        strict_scientific_mode=payload.strict_scientific_mode
    )

    # Trả về đối tượng survey_draft kèm metadata cho frontend
    draft = pipeline_result.get("survey_draft", {})
    draft["ai_metadata"] = {
        "session_id": pipeline_result.get("session_id"),
        "status": pipeline_result.get("status"),
        "provider": pipeline_result.get("provider"),
        "model_used": pipeline_result.get("model_used"),
        "validation": pipeline_result.get("validation"),
        "duration_ms": pipeline_result.get("duration_ms"),
        "error_detail": pipeline_result.get("error_detail")
    }
    return draft

@router.post("/audit-questions")
def audit_survey_questions(payload: AuditQuestionsRequest):
    """
    Kiểm định chất lượng câu hỏi chuyên sâu trước khi xuất bản:
    - Phát hiện câu hỏi dẫn dắt (Leading question).
    - Phát hiện câu hỏi kép (Double-barreled question).
    - Phát hiện phương án thiếu hoặc mất cân đối.
    - Cung cấp gợi ý viết lại tự động (Auto-fix suggestion).
    """
    if not payload.questions:
        return {
            "total_questions": 0,
            "total_issues": 0,
            "scientific_readiness": "READY",
            "issues": []
        }

    return AIService.audit_questions_deep(
        questions=payload.questions,
        survey_id=payload.survey_id or ""
    )

@router.post("/cognitive-pretest", response_model=CognitivePretestReport)
def run_ai_cognitive_pretest(payload: CognitivePretestRequest):
    """
    Thử nghiệm nhận thức tiền xuất bản trên bản thảo câu hỏi (Pre-Flight Cognitive Testing):
    - Đánh giá chỉ số dễ đọc Flesch Reading Ease & độ phức tạp câu hỏi
    - Phát hiện 8 dạng lỗi cấu trúc & thiên lệch nhận thức (Tourangeau et al., 2000; Dillman et al., 2014)
    - Giả lập 3 Persona nhận thức nhân khẩu học (Fast Paced Mobile, Elderly Plain Language, Analytical Reviewer)
    - Dự báo đường cong mệt mỏi nhận thức và nguy cơ bỏ ngang
    - Cung cấp gợi ý viết lại tự động chuẩn học thuật Don Dillman & AAPOR
    """
    from app.engine.cognitive_pretest_engine import CognitivePretestEngine
    return CognitivePretestEngine.run_pretest_audit(
        survey_id=payload.survey_id,
        title=payload.title or "Bản thảo khảo sát",
        questions=payload.questions or []
    )

@router.post("/analyze-responses")
def analyze_qualitative_responses(payload: QualitativeAnalysisRequest):
    """Phân tích định tính câu trả lời mở của khảo sát (Sắc thái tình cảm, chủ đề then chốt, cờ bất thường)"""
    with get_db() as conn:
        # Lấy thông tin khảo sát
        survey_row = conn.execute("SELECT title FROM surveys WHERE id = ?", (payload.survey_id,)).fetchone()
        if not survey_row:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")
        survey_title = survey_row["title"]

        # Lấy các câu trả lời dạng văn bản
        query = """
        SELECT ra.answer_value
        FROM response_answers ra
        JOIN questions q ON ra.question_id = q.id
        WHERE ra.response_id IN (SELECT id FROM responses WHERE survey_id = ?)
          AND q.question_type IN ('long_text', 'short_text')
        """
        params = [payload.survey_id]
        if payload.question_id:
            query += " AND q.id = ?"
            params.append(payload.question_id)
        query += f" LIMIT {max(10, min(payload.sample_limit, 200))}"

        rows = conn.execute(query, params).fetchall()
        texts = [r["answer_value"] for r in rows if r["answer_value"]]

    return AIService.analyze_qualitative_responses(texts, topic=survey_title)

@router.get("/sessions")
def list_ai_generation_sessions(limit: int = Query(20, ge=1, le=100)):
    """Lấy danh sách các phiên sinh AI gần nhất để kiểm toán và theo dõi hiệu năng"""
    with get_db() as conn:
        rows = conn.execute("""
        SELECT id, topic, audience, model_name, provider_type, status, duration_ms, error_message, created_at
        FROM ai_generation_sessions
        ORDER BY created_at DESC
        LIMIT ?
        """, (limit,)).fetchall()

        return [dict(r) for r in rows]

@router.get("/sessions/{session_id}")
def get_ai_generation_session_detail(session_id: str):
    """Lấy thông tin chi tiết của một phiên sinh khảo sát AI"""
    with get_db() as conn:
        row = conn.execute("""
        SELECT * FROM ai_generation_sessions WHERE id = ?
        """, (session_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Phiên sinh AI không tồn tại.")
        
        data = dict(row)
        for json_col in ["preferred_types_json", "extracted_spec_json", "generated_survey_json", "validation_report_json"]:
            if data.get(json_col):
                try:
                    data[json_col] = json.loads(data[json_col])
                except Exception:
                    pass
        return data
