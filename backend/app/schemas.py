from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# --- Question Schemas ---
class QuestionOption(BaseModel):
    id: str
    label: str

class LogicRule(BaseModel):
    depends_on_question_id: str
    operator: str  # 'equals', 'not_equals', 'contains'
    value: Any
    action: str = 'show'  # 'show' or 'hide'

class QuestionBase(BaseModel):
    order_index: int = 0
    question_type: str = "single_choice"
    title: str
    description: Optional[str] = ""
    is_required: bool = False
    options: Any = Field(default_factory=list)
    logic_rules: List[Dict[str, Any]] = Field(default_factory=list)

class QuestionCreate(QuestionBase):
    id: Optional[str] = None

class QuestionOut(QuestionBase):
    id: str
    survey_id: str
    created_at: str

# --- Survey Schemas ---
class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    instructions: Optional[str] = ""

class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    questions: Optional[List[QuestionCreate]] = None

class SurveyOut(BaseModel):
    id: str
    title: str
    description: str
    instructions: str
    status: str
    public_slug: str
    version: int
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    questions: List[QuestionOut] = []
    responses_count: int = 0

class SurveyListItemOut(BaseModel):
    id: str
    title: str
    description: str
    status: str
    public_slug: str
    version: int
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    questions_count: int = 0
    responses_count: int = 0
    avg_risk_score: float = 0.0

class SurveyPublishOut(BaseModel):
    id: str
    status: str
    public_slug: str
    public_url: str
    published_at: str

# --- Public Survey Schemas ---
class PublicQuestionOut(BaseModel):
    id: str
    order_index: int
    question_type: str
    title: str
    description: str
    is_required: bool
    options: Any = Field(default_factory=list)
    logic_rules: List[Dict[str, Any]] = Field(default_factory=list)

class PublicSurveyOut(BaseModel):
    id: str
    title: str
    description: str
    instructions: str
    public_slug: str
    version: int
    questions: List[PublicQuestionOut]

class ResponseSubmit(BaseModel):
    started_at: str
    submitted_at: str
    client_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    answers: Dict[str, Any]  # question_id -> answer value (string, array, or object)
    source: Optional[str] = "online_form"
    enumerator_id: Optional[str] = ""

# --- Quality & Review Schemas ---
class QualityFlag(BaseModel):
    code: str
    severity: str  # 'INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    message: str
    details: Optional[Dict[str, Any]] = None

class QualityAssessmentOut(BaseModel):
    id: str
    score_dup: float
    score_pattern: float
    score_logic: float
    score_speed: float
    score_text: float
    score_enum: float = 0.0
    composite_score: float
    flags: List[QualityFlag]
    closest_match_response_id: Optional[str] = None
    highest_similarity: float = 0.0
    assessed_at: str

class ResponseListItemOut(BaseModel):
    id: str
    survey_id: str
    started_at: str
    submitted_at: str
    duration_seconds: float
    risk_score: float
    risk_level: str
    analysis_status: str
    review_status: str
    flags_count: int = 0
    flags_summary: List[str] = []
    source: str = "online_form"
    enumerator_id: str = ""
    omr_confidence: float = 1.0

class ResponseDetailOut(BaseModel):
    id: str
    survey_id: str
    survey_title: str
    survey_version: int
    started_at: str
    submitted_at: str
    duration_seconds: float
    risk_score: float
    risk_level: str
    analysis_status: str
    review_status: str
    review_notes: str
    reviewed_at: Optional[str] = None
    client_metadata: Dict[str, Any]
    answers: Dict[str, Any]
    questions: List[QuestionOut]
    assessment: Optional[QualityAssessmentOut] = None
    source: str = "online_form"
    enumerator_id: str = ""
    paper_form_id: str = ""
    scan_image_url: str = ""
    omr_confidence: float = 1.0

class ReviewStatusUpdate(BaseModel):
    review_status: str  # 'unverified', 'under_review', 'verified_valid', 'verified_fraud', 'inconclusive'
    review_notes: Optional[str] = ""

# --- Paper Survey & OMR Schemas ---
class PaperBubbleConfig(BaseModel):
    option_id: str
    option_label: str
    x: int
    y: int
    radius: int = 14

class PaperQuestionLayout(BaseModel):
    question_id: str
    question_type: str
    title: str
    order_index: int
    box_x: int
    box_y: int
    box_w: int
    box_h: int
    bubbles: List[PaperBubbleConfig]

class PaperTemplateLayout(BaseModel):
    survey_id: str
    survey_title: str
    template_version: int
    page_width: int = 1240
    page_height: int = 1754
    fiducial_markers: List[Dict[str, int]]
    qr_region: Dict[str, int]
    questions: List[PaperQuestionLayout]

class PaperScanResult(BaseModel):
    success: bool
    survey_id: str
    form_id: str
    enumerator_id: str
    image_quality: Dict[str, Any]  # sharpness, brightness, status
    confidence_score: float
    detected_answers: Dict[str, Any]
    question_confidences: Dict[str, float]
    overlay_image_base64: Optional[str] = None
    warnings: List[str] = []

class PaperIngestPayload(BaseModel):
    form_id: str
    enumerator_id: str = ""
    answers: Dict[str, Any]
    omr_confidence: float = 1.0
    scan_image_url: Optional[str] = ""
    manual_corrections: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

# --- Enumerator Analytics Schemas ---
class EnumeratorMetrics(BaseModel):
    enumerator_id: str
    total_responses: int
    online_count: int
    paper_count: int
    avg_duration_seconds: float
    avg_risk_score: float
    high_risk_count: int
    high_risk_rate: float
    variance_z_score: float
    is_anomaly: bool
    anomaly_reasons: List[str]

class EnumeratorAnalyticsOut(BaseModel):
    survey_id: str
    total_enumerators: int
    total_field_responses: int
    enumerators: List[EnumeratorMetrics]


# --- Analytics Schemas ---
class QuestionStats(BaseModel):
    question_id: str
    question_title: str
    question_type: str
    total_answers: int
    option_distribution: Optional[Dict[str, int]] = None
    stats_summary: Optional[Dict[str, Any]] = None  # min, max, avg for numeric
    recent_text_samples: Optional[List[str]] = None

class SurveyAnalyticsOut(BaseModel):
    survey_id: str
    survey_title: str
    total_responses: int
    is_sample_size_sufficient: bool  # True if total_responses >= 5
    sample_size_notice: Optional[str] = None
    avg_duration_seconds: float
    risk_distribution: Dict[str, int]  # 'low', 'medium', 'high'
    review_distribution: Dict[str, int]
    questions_analytics: List[QuestionStats]


# --- Quality Audit Report & Compliance Schemas ---
class QualityAuditReportOut(BaseModel):
    survey_id: str
    survey_title: str
    survey_status: str
    generated_at: str
    total_collected: int
    source_breakdown: Dict[str, int]
    verified_clean_count: int
    data_trust_index: float  # Percentage 0 - 100%
    risk_breakdown: Dict[str, int]
    review_breakdown: Dict[str, int]
    fraud_signals: Dict[str, int]
    compliance_statement: Dict[str, Any]
    methodology_citations: List[str]
    audit_hash: str

class AnonymizeRequest(BaseModel):
    anonymize_client_metadata: bool = True
    mask_text_answers: bool = False
    operator_notes: str = ""

class AnonymizeResponse(BaseModel):
    message: str
    anonymized_responses_count: int
    audit_log_id: str

