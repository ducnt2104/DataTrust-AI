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
    settings: Optional[Dict[str, Any]] = None

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

class WebhookTestRequest(BaseModel):
    webhook_url: str
    webhook_secret: Optional[str] = None

class WebhookTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    delivery_id: str
    latency_ms: float
    message: str
    error: Optional[str] = None

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
    available_languages: List[str] = Field(default_factory=lambda: ["vi"])
    current_language: str = "vi"

class ResponseSubmit(BaseModel):
    started_at: str
    submitted_at: str
    client_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    answers: Dict[str, Any]  # question_id -> answer value (string, array, or object)
    source: Optional[str] = "online_form"
    enumerator_id: Optional[str] = ""
    experimental_arm: Optional[str] = ""

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

class BatchReviewRequest(BaseModel):
    response_ids: List[str]
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
    orientation_corrected: int = 0

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
    gps_coverage_rate: float = 0.0
    impossible_speed_detected: bool = False
    max_speed_kmh: Optional[float] = None
    stationary_cluster_detected: bool = False
    radius_of_gyration_km: Optional[float] = None
    spatial_coverage_sqkm: Optional[float] = None
    geofence_breach_count: int = 0
    gps_points: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class EnumeratorAnalyticsOut(BaseModel):
    survey_id: str
    total_enumerators: int
    total_field_responses: int
    geofence_setting: Optional[Dict[str, Any]] = None
    enumerators: List[EnumeratorMetrics]


# --- Analytics Schemas ---
class QuestionStats(BaseModel):
    question_id: str
    question_title: str
    question_type: str
    total_answers: int
    completion_rate: Optional[float] = None
    drop_off_rate: Optional[float] = None
    option_distribution: Optional[Dict[str, Any]] = None
    stats_summary: Optional[Dict[str, Any]] = None  # min, max, avg for numeric
    recent_text_samples: Optional[List[str]] = None

class SurveyAnalyticsOut(BaseModel):
    survey_id: str
    survey_title: str
    total_responses: int
    is_sample_size_sufficient: bool  # True if total_responses >= 5
    sample_size_notice: Optional[str] = None
    avg_duration_seconds: float
    overall_completion_rate: Optional[float] = None
    funnel_analytics: Optional[List[Dict[str, Any]]] = None
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
    cronbach_alpha: Optional[float] = None
    ledger_head_hash: Optional[str] = None
    is_ledger_valid: Optional[bool] = None

class AnonymizeRequest(BaseModel):
    anonymize_client_metadata: bool = True
    mask_text_answers: bool = False
    operator_notes: str = ""

class AnonymizeResponse(BaseModel):
    message: str
    anonymized_responses_count: int
    audit_log_id: str

class AuditLogEntryOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    details_json: str
    details: Optional[Dict[str, Any]] = None
    created_at: str
    prev_hash: str
    entry_hash: str
    is_valid_hash: bool

class AuditTrailOut(BaseModel):
    survey_id: str
    is_chain_valid: bool
    chain_status: str  # 'VALID', 'TAMPERED', 'EMPTY'
    total_records: int
    genesis_hash: Optional[str] = None
    head_hash: Optional[str] = None
    tampered_at_index: Optional[int] = None
    tampered_record_id: Optional[str] = None
    verification_message: str
    verified_at: str
    events: List[AuditLogEntryOut]


# --- Advanced AI Survey Assistant Schemas ---
class GenerateSurveyAdvancedRequest(BaseModel):
    topic: str
    audience: Optional[str] = ""
    research_objectives: Optional[str] = ""
    expected_time_minutes: int = 5
    preferred_question_types: Optional[List[str]] = Field(default_factory=list)
    target_question_count: Optional[int] = 7
    language: Optional[str] = "vi"
    strict_scientific_mode: bool = True

class QuestionDraftSchema(BaseModel):
    id: str
    order_index: int
    question_type: str
    title: str
    description: Optional[str] = ""
    is_required: bool = True
    options: Any = Field(default_factory=list)
    logic_rules: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class SurveyDraftOutputSchema(BaseModel):
    title: str
    description: str
    instructions: str
    estimated_duration_minutes: int = 5
    methodological_rationale: Optional[str] = ""
    questions: List[QuestionDraftSchema]

class ValidationReportSchema(BaseModel):
    is_valid: bool
    coverage_score: float
    adherence_score: float
    objectivity_score: float
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    repaired: bool = False
    repair_attempts: int = 0

class AIGenerationResponseSchema(BaseModel):
    session_id: str
    status: str
    provider: str
    model_used: str
    survey_draft: SurveyDraftOutputSchema
    validation: ValidationReportSchema
    duration_ms: float
    error_detail: Optional[str] = None

class QualitativeAnalysisRequest(BaseModel):
    survey_id: str
    question_id: Optional[str] = None
    sample_limit: int = 50

class QualitativeTheme(BaseModel):
    theme_name: str
    sentiment: str  # positive, neutral, negative
    prevalence_percent: float
    sample_quotes: List[str]

class QualitativeAnalysisResponse(BaseModel):
    survey_id: str
    total_analyzed: int
    sentiment_distribution: Dict[str, int]
    key_themes: List[QualitativeTheme]
    anomaly_flags: List[str]
    methodology_summary: str

# --- Offline Batch Sync Schemas ---
class BatchResponseItem(BaseModel):
    client_uuid: Optional[str] = None
    started_at: str
    submitted_at: str
    client_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    answers: Dict[str, Any]
    source: Optional[str] = "offline_sync"
    enumerator_id: Optional[str] = ""

class BatchResponseSubmit(BaseModel):
    responses: List[BatchResponseItem]

class BatchSyncResultItem(BaseModel):
    client_uuid: Optional[str] = None
    response_id: Optional[str] = None
    status: str  # 'synced', 'skipped_duplicate', 'error'
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    message: Optional[str] = None

class BatchSyncResponseOut(BaseModel):
    success: bool
    total_received: int
    synced_count: int
    duplicates_skipped: int
    error_count: int
    results: List[BatchSyncResultItem]

# --- Data Cleansing & Exclusion Criteria Schemas ---
class DataCleansingCriteria(BaseModel):
    exclude_speeders: bool = True
    speeder_min_seconds: float = 10.0
    exclude_straightlining: bool = True
    straightlining_threshold: float = 0.85
    exclude_logic_contradictions: bool = True
    exclude_high_risk: bool = False
    min_omr_confidence: float = 0.70
    exclude_unverified_enumerator: bool = False
    exclude_collusion_syndicates: bool = True
    exclude_coffee_shop_congregations: bool = True
    exclude_impossible_travel: bool = True
    exclude_geofence_violations: bool = False

class DataCleansingReport(BaseModel):
    survey_id: str
    total_responses: int
    clean_responses_count: int
    clean_percentage: float
    flagged_speeders: int
    flagged_straightlining: int
    flagged_contradictions: int
    flagged_high_risk: int
    flagged_low_omr: int
    overlap_count: int
    pre_avg_duration: float
    post_avg_duration: float
    pre_avg_risk: float
    post_avg_risk: float
    cronbach_alpha_pre: Optional[float] = None
    cronbach_alpha_post: Optional[float] = None
    applied_criteria: DataCleansingCriteria
    flagged_collusion_syndicates: int = 0
    flagged_coffee_shop: int = 0
    flagged_impossible_travel: int = 0
    flagged_geofence_violations: int = 0

class DataCleansingApplyResult(BaseModel):
    success: bool
    survey_id: str
    applied_count: int
    rejected_count: int
    verified_clean_count: int
    audit_log_id: str
    timestamp: str

# --- Batch Anomaly Quarantine Schemas ---
class BatchAnomalyQuarantineRequest(BaseModel):
    quarantine_syndicates: bool = True
    quarantine_coffee_shop: bool = True
    quarantine_impossible_velocity: bool = True
    quarantine_geofence_violations: bool = False
    quarantine_speeders: bool = True
    quarantine_straightlining: bool = True
    min_risk_score: Optional[float] = 75.0
    action: str = "verified_fraud"
    custom_note: Optional[str] = None
    dry_run: bool = False

class BatchAnomalyQuarantineItem(BaseModel):
    response_id: str
    enumerator_id: Optional[str] = None
    duration_seconds: float
    risk_score: float
    reasons: List[str]
    previous_status: str
    new_status: str

class BatchAnomalyQuarantineResult(BaseModel):
    success: bool
    survey_id: str
    dry_run: bool
    total_evaluated: int
    quarantined_count: int
    reasons_breakdown: Dict[str, int]
    items: List[BatchAnomalyQuarantineItem]
    audit_log_id: Optional[str] = None
    timestamp: str

class BatchRestoreQuarantineRequest(BaseModel):
    response_ids: Optional[List[str]] = None
    restore_to_status: str = "unverified"
    reason: Optional[str] = "Phục hồi thủ công sau khi xem xét kiểm toán"

class BatchRestoreQuarantineResult(BaseModel):
    success: bool
    survey_id: str
    restored_count: int
    restored_ids: List[str]
    audit_log_id: str
    timestamp: str

# --- Survey Historical Versioning Schemas ---
class SurveyVersionOut(BaseModel):
    id: str
    survey_id: str
    version: int
    title: str
    description: Optional[str] = ""
    questions_count: int
    questions: List[Dict[str, Any]] = []
    created_at: str

# --- Red-Team Adversarial Simulation Schemas ---
class AttackDefenseItem(BaseModel):
    id: str
    name: str
    category: str  # 'injection', 'xss', 'formula_cwe1236', 'ledger_tamper', 'speeder_bot', 'straightlining'
    threat_level: str  # 'CRITICAL', 'HIGH', 'MEDIUM'
    payload_sample: str
    result: str  # 'DEFENDED', 'VULNERABLE'
    defense_layer: str
    latency_ms: float
    technical_detail: str

class RedTeamSimulationResult(BaseModel):
    survey_id: str
    timestamp: str
    overall_status: str  # 'SECURE', 'DEGRADED', 'VULNERABLE'
    compliance_score: float  # 0 - 100%
    attacks_tested: int
    attacks_deflected: int
    total_duration_ms: float
    standards_verified: List[str]
    attack_results: List[AttackDefenseItem]

# --- Public Certificate & Ledger Verification Schemas ---
class PublicCertificateVerificationOut(BaseModel):
    query: str
    is_valid: bool
    status: str  # 'VERIFIED_VALID', 'TAMPERED', 'NOT_FOUND'
    certificate_id: str
    survey_id: str
    survey_title: str
    survey_description: Optional[str] = None
    public_slug: Optional[str] = None
    issued_at: str
    total_responses: int
    clean_responses: int
    excluded_responses: int
    trust_index: float
    cronbach_alpha: Optional[float] = None
    reliability_verdict: Optional[str] = None
    ledger_chain_valid: bool
    ledger_head_hash: Optional[str] = None
    ledger_genesis_hash: Optional[str] = None
    total_audit_events: int
    verification_verdict: str
    compliance_standards: List[str]
    printable_certificate_url: str

# --- Longitudinal Wave-over-Wave Analytics Schemas ---
class LongitudinalItemComparison(BaseModel):
    question_id_1: Optional[str] = None
    question_id_2: Optional[str] = None
    title: str
    question_type: str
    is_scale: bool
    n_wave1: int
    n_wave2: int
    mean_wave1: Optional[float] = None
    mean_wave2: Optional[float] = None
    std_wave1: Optional[float] = None
    std_wave2: Optional[float] = None
    mean_shift: Optional[float] = None
    percent_change: Optional[float] = None
    cohens_d: Optional[float] = None
    effect_size: str
    t_statistic: Optional[float] = None
    degrees_of_freedom: Optional[float] = None
    p_value: Optional[float] = None
    is_statistically_significant: bool
    significance_label: str
    trend_direction: str
    category_shifts: Optional[List[Dict[str, Any]]] = None
    apa_summary: str

class LongitudinalWaveComparisonOut(BaseModel):
    wave1_survey: Dict[str, Any]
    wave2_survey: Dict[str, Any]
    matched_questions_count: int
    overall_scale_mean_wave1: Optional[float] = None
    overall_scale_mean_wave2: Optional[float] = None
    overall_scale_delta: Optional[float] = None
    items_increased_count: int
    items_decreased_count: int
    items_stable_count: int
    comparative_summary: str
    items: List[LongitudinalItemComparison]

# --- Stress Test & Concurrency Simulation Schemas ---
class StressTestReportOut(BaseModel):
    status: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    concurrency_workers: int
    total_time_seconds: float
    throughput_rps: float
    latency_mean_ms: float
    latency_median_p50_ms: float
    latency_p90_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_min_ms: float
    latency_max_ms: float
    database_lock_errors: int
    audit_chain_valid_post_stress: bool
    audit_chain_head_hash: Optional[str] = None
    wal_size_bytes_after: int

# --- Sampling Quotas & Demographic Raking Schemas ---
class SamplingQuotaRule(BaseModel):
    id: Optional[str] = None
    name: str
    question_id: str
    target_value: str
    max_target: int
    action: Optional[str] = "flag_overflow"

class SamplingQuotaCellProgress(BaseModel):
    cell_id: str
    name: str
    question_id: str
    target_value: str
    max_target: int
    achieved_count: int
    remaining_count: int
    completion_pct: float
    status: str  # 'open', 'almost_full', 'filled'
    action: str

class SamplingQuotaReportOut(BaseModel):
    survey_id: str
    total_quota_cells: int
    filled_cells: int
    open_cells: int
    overall_target_sum: int
    overall_achieved_sum: int
    overall_completion_pct: float
    cells: List[SamplingQuotaCellProgress]

class SaveQuotasRequest(BaseModel):
    quota_rules: List[SamplingQuotaRule]

class DemographicRakingRequest(BaseModel):
    target_margins: Dict[str, Dict[str, float]]
    scope: Optional[str] = "verified_clean"
    max_iterations: Optional[int] = 50
    convergence_tol: Optional[float] = 0.001
    trim_min: Optional[float] = 0.2
    trim_max: Optional[float] = 5.0

class RakingMarginalCategory(BaseModel):
    category: str
    unweighted_count: int
    unweighted_pct: float
    target_benchmark_pct: float
    weighted_pct: float
    absolute_bias_reduction_pct: float

class RakingMarginalComparison(BaseModel):
    variable: str
    categories: List[RakingMarginalCategory]

class DemographicRakingOut(BaseModel):
    survey_id: str
    converged: bool
    iterations: int
    max_discrepancy: float
    sample_size: int
    design_effect_deff: float
    effective_sample_size_neff: float
    statistical_efficiency_pct: float
    weight_stats: Dict[str, Any]
    marginal_comparisons: List[RakingMarginalComparison]
    summary: str

# --- Differential Item Functioning (DIF) Schemas ---
class DIFItemResult(BaseModel):
    question_id: str
    question_title: str
    median_threshold: float
    active_strata_count: int
    chi2_mh: float
    p_value: float
    alpha_odds_ratio: float
    delta_ets: float
    abs_delta_ets: float
    ets_class: str  # 'A', 'B', 'C'
    ets_label: str
    favored_group: str
    action_recommendation: str
    is_statistically_significant: bool

class DIFReportOut(BaseModel):
    survey_id: str
    grouping_variable_id: str
    grouping_variable_title: str
    reference_group: str
    focal_group: str
    sample_reference: int
    sample_focal: int
    total_eval_sample: int
    strata_count: int
    class_a_count: int
    class_b_count: int
    class_c_count: int
    overall_verdict: str
    summary: str
    items: List[DIFItemResult]

# --- Hypothesis Testing T-Test Schemas ---
class IndependentTTestRequest(BaseModel):
    grouping_question_id: str
    group1_value: str
    group2_value: str
    target_question_id: str
    scope: str = Field(default="all", pattern="^(all|verified_clean)$")

class PairedTTestRequest(BaseModel):
    pre_question_id: str
    post_question_id: str
    scope: str = Field(default="all", pattern="^(all|verified_clean)$")

# --- One-Way ANOVA Schemas ---
class OneWayANOVARequest(BaseModel):
    grouping_question_id: str
    target_question_id: str
    scope: str = Field(default="all", pattern="^(all|verified_clean)$")
    selected_groups: Optional[List[str]] = Field(default=None)

# --- Multiple Linear Regression OLS Schemas ---
class LinearRegressionRequest(BaseModel):
    dependent_question_id: str
    predictor_question_ids: List[str]
    scope: str = Field(default="all", pattern="^(all|verified_clean)$")

# --- Statistical Power Analysis Schemas ---
class PowerAnalysisRequest(BaseModel):
    analysis_type: str = Field(default="sample_adequacy")
    confidence_level: float = Field(default=0.95, ge=0.80, le=0.999)
    margin_of_error: float = Field(default=0.05, ge=0.005, le=0.20)
    population_size: Optional[int] = Field(default=None, ge=10)
    effect_size: float = Field(default=0.50, ge=0.05, le=2.0)
    target_power: float = Field(default=0.80, ge=0.50, le=0.99)
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)
    scope: str = Field(default="verified_clean", pattern="^(all|verified_clean)$")

# --- Split-Ballot & Question Wording Experimentation Schemas ---
class SplitBallotAnalysisRequest(BaseModel):
    question_id: str
    scope: str = Field(default="verified_clean", pattern="^(all|verified_clean)$")

# --- Rasch Model & Item Response Theory (IRT) Schemas ---
class RaschAnalysisRequest(BaseModel):
    scope: str = Field(default="verified_clean", pattern="^(all|verified_clean)$")

# --- Respondent Clustering & Segmentation Schemas ---
class ClusterAnalysisRequest(BaseModel):
    question_ids: Optional[List[str]] = None
    k: Optional[int] = Field(default=None, ge=2, le=10)
    scope: str = Field(default="verified_clean", pattern="^(all|verified_clean)$")

# --- Pairwise Response Similarity & Collusion Ring Schemas ---
class PairwiseSimilarityRequest(BaseModel):
    threshold: float = Field(default=0.80, ge=0.50, le=1.0, description="Ngưỡng tương đồng tối thiểu để đưa vào danh sách cảnh báo (0.50 - 1.0)")
    max_matrix_size: int = Field(default=60, ge=10, le=200, description="Kích thước ma trận trực quan (10 - 200 phản hồi)")
    scope: str = Field(default="all", pattern="^(all|verified_clean)$", description="Phạm vi phản hồi: all hoặc verified_clean")

# --- Geographic Spatial Clustering & Geo-Fencing Schemas ---
class SpatialAnalysisRequest(BaseModel):
    eps_meters: float = Field(default=75.0, ge=10.0, le=2000.0, description="Bán kính láng giềng DBSCAN (mét, 10 - 2000m)")
    min_samples: int = Field(default=3, ge=2, le=20, description="Số điểm tối thiểu để hình thành cụm mật độ (2 - 20)")
    max_speed_kmh: float = Field(default=120.0, ge=20.0, le=500.0, description="Vận tốc di chuyển tối đa cho phép giữa 2 lần nộp (km/h)")
    geofence_polygon: Optional[List[List[float]]] = Field(default=None, description="Đa giác ranh giới kiểm định [[lat, lon], ...]")
    scope: str = Field(default="all", pattern="^(all|verified_clean)$", description="Phạm vi phản hồi: all hoặc verified_clean")

# --- Cognitive Pre-Testing & Question Ambiguity Diagnostics Schemas ---
class CognitiveIssue(BaseModel):
    question_id: str
    question_order: int
    question_title: str
    issue_type: str
    severity: str
    cognitive_dimension: str
    explanation: str
    academic_rule: str
    auto_fix_title: Optional[str] = None
    suggested_options: Optional[List[Dict[str, Any]]] = None

class PersonaSimulationResult(BaseModel):
    persona_id: str
    persona_name: str
    persona_demographic: str
    cognitive_style: str
    overall_difficulty_rating: str
    predicted_completion_time_sec: float
    predicted_dropout_probability: float
    bottleneck_question_ids: List[str]
    qualitative_feedback: str

class CognitivePretestRequest(BaseModel):
    survey_id: Optional[str] = None
    title: Optional[str] = "Khảo sát khảo nghiệm"
    questions: Optional[List[Dict[str, Any]]] = None

class CognitivePretestReport(BaseModel):
    survey_id: Optional[str] = None
    survey_title: str
    total_questions: int
    total_words: int
    readability_score: float
    readability_level: str
    estimated_duration_minutes: float
    design_quality_score: float
    academic_grade: str
    total_issues_count: int
    critical_issues_count: int
    warning_issues_count: int
    issues: List[CognitiveIssue]
    personas: List[PersonaSimulationResult]
    fatigue_curve: List[Dict[str, Any]]
    methodological_summary: str
    timestamp: str


# --- Statistical Mediation & Path Analysis Schemas ---
class MediationAnalysisRequest(BaseModel):
    x_question_id: Optional[str] = None
    m_question_id: Optional[str] = None
    y_question_id: Optional[str] = None
    independent_var_id: Optional[str] = None
    mediator_var_id: Optional[str] = None
    dependent_var_id: Optional[str] = None
    scope: Optional[str] = "all"  # "all" hoặc "verified_clean"
    bootstrap_samples: Optional[int] = 1000
    num_bootstrap: Optional[int] = None
    random_seed: Optional[int] = 42

class MediationPathInfo(BaseModel):
    id: str
    source: str
    target: str
    coeff: float
    std_beta: float
    se: float
    p_value: float
    stars: str
    is_significant: bool
    label: str

class MediationStep(BaseModel):
    step: int
    title: str
    formula: str
    r_squared: float
    f_stat: Optional[float] = None
    f_p_value: Optional[float] = None
    coefficient: Optional[float] = None
    std_beta: Optional[float] = None
    se: Optional[float] = None
    t_stat: Optional[float] = None
    p_value: Optional[float] = None
    ci_95: Optional[List[float]] = None
    is_significant: Optional[bool] = None
    delta_r_squared: Optional[float] = None
    path_c_prime: Optional[Dict[str, Any]] = None
    path_b: Optional[Dict[str, Any]] = None

class MediationEffectsSummary(BaseModel):
    total_effect_c: float
    direct_effect_c_prime: float
    indirect_effect_ab: float
    std_indirect_effect_ab: float
    indirect_to_direct_ratio: Optional[float] = None
    vaf_percent: float

class MediationSignificanceTests(BaseModel):
    sobel_test: Dict[str, Any]
    aroian_test: Dict[str, Any]
    goodman_test: Dict[str, Any]
    bootstrap_resampling: Dict[str, Any]

class MediationConclusion(BaseModel):
    mediation_type: str
    mediation_label_vn: str
    description: str
    apa_narrative: str

class MediationDiagram(BaseModel):
    nodes: List[Dict[str, Any]]
    paths: List[MediationPathInfo]

class MediationAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    variables: Optional[Dict[str, Any]] = None
    steps: Optional[List[MediationStep]] = None
    effects_summary: Optional[MediationEffectsSummary] = None
    significance_tests: Optional[MediationSignificanceTests] = None
    conclusion: Optional[MediationConclusion] = None
    diagram: Optional[MediationDiagram] = None


# --- Non-Parametric Hypothesis Testing Schemas ---
class MannWhitneyURequest(BaseModel):
    target_question_id: str
    grouping_question_id: str
    group1_value: Optional[str] = None
    group2_value: Optional[str] = None
    scope: Optional[str] = "all"

class MannWhitneyUOut(BaseModel):
    status: str
    message: Optional[str] = None
    test_type: Optional[str] = None
    total_sample_size: Optional[int] = None
    groups: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None
    effect_size: Optional[Dict[str, Any]] = None
    conclusion: Optional[Dict[str, Any]] = None

class WilcoxonSignedRankRequest(BaseModel):
    question_id_1: str
    question_id_2: str
    scope: Optional[str] = "all"

class WilcoxonSignedRankOut(BaseModel):
    status: str
    message: Optional[str] = None
    test_type: Optional[str] = None
    total_pairs: Optional[int] = None
    effective_pairs: Optional[int] = None
    zero_differences_count: Optional[int] = None
    samples: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None
    effect_size: Optional[Dict[str, Any]] = None
    conclusion: Optional[Dict[str, Any]] = None

class KruskalWallisRequest(BaseModel):
    target_question_id: str
    grouping_question_id: str
    scope: Optional[str] = "all"

class KruskalWallisOut(BaseModel):
    status: str
    message: Optional[str] = None
    test_type: Optional[str] = None
    k_groups: Optional[int] = None
    total_sample_size: Optional[int] = None
    degrees_of_freedom: Optional[int] = None
    statistics: Optional[Dict[str, Any]] = None
    effect_size: Optional[Dict[str, Any]] = None
    groups_summary: Optional[List[Dict[str, Any]]] = None
    post_hoc_dunn_tests: Optional[List[Dict[str, Any]]] = None
    conclusion: Optional[Dict[str, Any]] = None


# --- Missing Data Pattern Diagnostics & Imputation Schemas ---
class MissingDataDiagnosticsRequest(BaseModel):
    question_ids: Optional[List[str]] = None
    scope: Optional[str] = "all"

class MissingDataDiagnosticsOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    variables_count: Optional[int] = None
    complete_cases_count: Optional[int] = None
    incomplete_cases_count: Optional[int] = None
    complete_cases_pct: Optional[float] = None
    total_cells: Optional[int] = None
    total_missing_cells: Optional[int] = None
    overall_missing_rate: Optional[float] = None
    variables_summary: Optional[List[Dict[str, Any]]] = None
    patterns: Optional[List[Dict[str, Any]]] = None
    patterns_count: Optional[int] = None
    littles_mcar_test: Optional[Dict[str, Any]] = None

class MissingDataImputationRequest(BaseModel):
    question_ids: Optional[List[str]] = None
    method: Optional[str] = "em"
    scope: Optional[str] = "all"

class MissingDataImputationOut(BaseModel):
    status: str
    message: Optional[str] = None
    method: Optional[str] = None
    method_label: Optional[str] = None
    sample_size: Optional[int] = None
    variables_count: Optional[int] = None
    imputed_cells_count: Optional[int] = None
    imputed_cells_pct: Optional[float] = None
    comparison: Optional[List[Dict[str, Any]]] = None
    apa_writeup: Optional[str] = None
    imputed_data_sample: Optional[List[Dict[str, Any]]] = None


# --- Scale Equating & Concordance Transformation Schemas ---
class ScaleEquatingRequest(BaseModel):
    source_question_id: str
    target_question_id: str
    scope: Optional[str] = "all"

class ScaleEquatingOut(BaseModel):
    status: str
    message: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    sample_sizes: Optional[Dict[str, int]] = None
    descriptive_statistics: Optional[Dict[str, Any]] = None
    linear_equating: Optional[Dict[str, Any]] = None
    discrepancy_analysis: Optional[Dict[str, Any]] = None
    concordance_table: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None


# --- Multi-Group Measurement Invariance Schemas ---
class MeasurementInvarianceRequest(BaseModel):
    grouping_question_id: str
    scale_question_ids: List[str]
    scope: Optional[str] = "all"

class MeasurementInvarianceOut(BaseModel):
    status: str
    message: Optional[str] = None
    k_groups: Optional[int] = None
    groups: Optional[Dict[str, int]] = None
    total_sample_size: Optional[int] = None
    items_count: Optional[int] = None
    highest_level_achieved: Optional[str] = None
    verdict_badge: Optional[str] = None
    recommendation: Optional[str] = None
    models_summary: Optional[List[Dict[str, Any]]] = None
    item_details: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None


# --- Common Method Bias / Variance (CMB/CMV) Schemas ---
class CommonMethodBiasRequest(BaseModel):
    scale_question_ids: Optional[List[str]] = None
    marker_question_id: Optional[str] = None
    scope: Optional[str] = "all"

class CommonMethodBiasOut(BaseModel):
    status: str
    message: Optional[str] = None
    overall_risk: Optional[str] = None
    risk_score: Optional[int] = None
    risk_summary: Optional[str] = None
    flagged_issues: Optional[List[str]] = None
    harman_test: Optional[Dict[str, Any]] = None
    marker_test: Optional[Dict[str, Any]] = None
    ulmcf_test: Optional[Dict[str, Any]] = None
    apa_writeup: Optional[str] = None
    recommended_remedies: Optional[List[Dict[str, Any]]] = None


# --- Statistical Moderation Analysis (PROCESS Model 1) Schemas ---
class ModerationAnalysisRequest(BaseModel):
    independent_question_id: str
    moderator_question_id: str
    dependent_question_id: str
    center_variables: Optional[bool] = True
    scope: Optional[str] = "all"

class ModerationAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    center_variables: Optional[bool] = None
    variables: Optional[Dict[str, Any]] = None
    model_1_main_effects: Optional[Dict[str, Any]] = None
    model_2_moderation: Optional[Dict[str, Any]] = None
    moderation_effect: Optional[Dict[str, Any]] = None
    simple_slopes: Optional[List[Dict[str, Any]]] = None
    johnson_neyman: Optional[Dict[str, Any]] = None
    interaction_plot: Optional[Dict[str, Any]] = None
    apa_narrative: Optional[str] = None


# --- Moderated Mediation (PROCESS Model 7) Schemas ---
class ModeratedMediationRequest(BaseModel):
    independent_question_id: str
    mediator_question_id: str
    moderator_question_id: str
    dependent_question_id: str
    center_variables: Optional[bool] = True
    num_bootstrap: Optional[int] = 500
    scope: Optional[str] = "all"

class ModeratedMediationOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    bootstrap_samples_executed: Optional[int] = None
    center_variables: Optional[bool] = None
    variables: Optional[Dict[str, Any]] = None
    stage1_mediator_model: Optional[Dict[str, Any]] = None
    stage2_dependent_model: Optional[Dict[str, Any]] = None
    index_of_moderated_mediation: Optional[Dict[str, Any]] = None
    conditional_indirect_effects: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None

# --- Complex Survey Sampling (Two-Stage Cluster & Taylor Linearization) Schemas ---
class ComplexSamplingRequest(BaseModel):
    target_question_id: str
    cluster_question_id: str
    stratum_question_id: Optional[str] = None
    weight_question_id: Optional[str] = None
    scope: Optional[str] = "all"

class ComplexSamplingOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    strata_count: Optional[int] = None
    psu_count: Optional[int] = None
    degrees_of_freedom: Optional[int] = None
    cluster_size_summary: Optional[Dict[str, Any]] = None
    weight_summary: Optional[Dict[str, Any]] = None
    horvitz_thompson_estimates: Optional[Dict[str, Any]] = None
    taylor_linearization_variance: Optional[Dict[str, Any]] = None
    srs_comparison: Optional[Dict[str, Any]] = None
    design_effects: Optional[Dict[str, Any]] = None
    clusters_breakdown: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None


# --- Propensity Score Matching (PSM) & Inverse Probability Weighting (IPW) Schemas ---
class PSMAnalysisRequest(BaseModel):
    treatment_question_id: str
    treatment_value: Any = "1"
    outcome_question_id: str
    covariate_question_ids: List[str]
    caliper_factor: Optional[float] = 0.20
    scope: Optional[str] = "all"


class PSMAnalysisOut(BaseModel):
    status: str
    survey_id: Optional[str] = None
    treatment_name: Optional[str] = None
    outcome_name: Optional[str] = None
    sample_size: Optional[int] = None
    sample_treated: Optional[int] = None
    sample_control: Optional[int] = None
    matched_pairs_count: Optional[int] = None
    unmatched_treated_count: Optional[int] = None
    unmatched_control_count: Optional[int] = None
    caliper_factor: Optional[float] = None
    caliper_width: Optional[float] = None
    unadjusted_effect: Optional[Dict[str, Any]] = None
    matched_att: Optional[Dict[str, Any]] = None
    ipw_att: Optional[Dict[str, Any]] = None
    covariate_balance: Optional[List[Dict[str, Any]]] = None
    balance_summary: Optional[Dict[str, Any]] = None
    common_support_overlap: Optional[List[Dict[str, Any]]] = None
    love_plot: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None


# --- Structural Topic Modeling (STM) & Latent Dirichlet Allocation (LDA) Schemas ---
class TopicModelAnalysisRequest(BaseModel):
    text_question_id: str
    covariate_question_id: Optional[str] = None
    num_topics: Optional[int] = 3
    num_iterations: Optional[int] = 60
    scope: Optional[str] = "all"


class TopicModelAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    vocabulary_size: Optional[int] = None
    num_topics: Optional[int] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    mean_coherence_umass: Optional[float] = None
    topics: Optional[List[Dict[str, Any]]] = None
    covariate_effects: Optional[List[Dict[str, Any]]] = None
    document_sample_assignments: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None


# --- Psychometric Network Analysis & Gaussian Graphical Model (GGM) Schemas ---
class PsychometricNetworkRequest(BaseModel):
    question_ids: Optional[List[str]] = None
    regularization_threshold: Optional[float] = 0.05
    scope: Optional[str] = "all"


class PsychometricNetworkOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    num_nodes: Optional[int] = None
    num_edges: Optional[int] = None
    possible_edges: Optional[int] = None
    density: Optional[float] = None
    density_percent: Optional[float] = None
    sparsity_percent: Optional[float] = None
    mean_weight: Optional[float] = None
    most_central_node: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None


# --- Item Response Theory (IRT) 2-Parameter Logistic (2PL) Schemas ---
class IRT2PLAnalysisRequest(BaseModel):
    question_ids: Optional[List[str]] = None
    binarization_threshold: Optional[float] = None
    max_em_iter: Optional[int] = 35
    scope: Optional[str] = "all"


class IRT2PLAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    num_items: Optional[int] = None
    is_already_binary: Optional[bool] = None
    marginal_reliability: Optional[float] = None
    max_test_information: Optional[float] = None
    optimal_theta_range: Optional[List[float]] = None
    average_discrimination: Optional[float] = None
    average_difficulty: Optional[float] = None
    items: Optional[List[Dict[str, Any]]] = None
    icc_curves: Optional[List[Dict[str, Any]]] = None
    test_information_curve: Optional[Dict[str, Any]] = None
    person_trait_summary: Optional[Dict[str, Any]] = None
    apa_narrative: Optional[str] = None


# --- Survival Analysis & Time-to-Drop-off (Kaplan-Meier & Cox HR) Schemas ---
class SurvivalAnalysisRequest(BaseModel):
    grouping_question_id: Optional[str] = None
    time_milestones: Optional[List[float]] = None
    scope: Optional[str] = "all"


class SurvivalAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    total_participants: Optional[int] = None
    completed_count: Optional[int] = None
    drop_off_count: Optional[int] = None
    overall_completion_rate: Optional[float] = None
    overall_drop_off_rate: Optional[float] = None
    overall_km: Optional[Dict[str, Any]] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    group_comparison: Optional[Dict[str, Any]] = None
    log_rank_test: Optional[Dict[str, Any]] = None
    cox_hazard_ratio: Optional[Dict[str, Any]] = None
    apa_narrative: Optional[str] = None


# --- Multilevel Modeling / Hierarchical Linear Models (HLM) Schemas ---
class MultilevelAnalysisRequest(BaseModel):
    outcome_question_id: str
    predictor_question_id: Optional[str] = None
    cluster_question_id: Optional[str] = None
    centering: Optional[str] = "grand_mean"
    scope: Optional[str] = "all"


class MultilevelAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    total_sample_size: Optional[int] = None
    num_clusters: Optional[int] = None
    average_cluster_size: Optional[float] = None
    dependent_variable: Optional[str] = None
    predictor_variable: Optional[str] = None
    cluster_variable: Optional[str] = None
    centering: Optional[str] = None
    null_model: Optional[Dict[str, Any]] = None
    fixed_effects: Optional[Dict[str, Any]] = None
    random_effects: Optional[Dict[str, Any]] = None
    model_comparison_ols_vs_hlm: Optional[Dict[str, Any]] = None
    cluster_trajectories: Optional[List[Dict[str, Any]]] = None
    grand_trajectory_path: Optional[str] = None
    clusters_summary: Optional[List[Dict[str, Any]]] = None
    apa_narrative: Optional[str] = None


class ConjointAnalysisRequest(BaseModel):
    rating_question_id: str
    attribute_question_ids: List[str]
    price_question_id: Optional[str] = None
    scope: str = "all"


class ConjointSimulationRequest(BaseModel):
    rating_question_id: str
    attribute_question_ids: List[str]
    candidate_profiles: List[Dict[str, Any]]
    scope: str = "all"


class ConjointAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    attributes_count: Optional[int] = None
    parameters_estimated: Optional[int] = None
    overall_utility_intercept: Optional[float] = None
    model_fit: Optional[Dict[str, Any]] = None
    importance_ranking: Optional[List[Dict[str, Any]]] = None
    part_worth_utilities: Optional[Dict[str, Dict[str, float]]] = None
    willingness_to_pay: Optional[List[Dict[str, Any]]] = None
    svg_importance_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


class ConjointSimulationOut(BaseModel):
    status: str
    message: Optional[str] = None
    market_shares: Optional[List[Dict[str, Any]]] = None


class LCAAnalysisRequest(BaseModel):
    item_question_ids: List[str]
    num_classes: Optional[int] = None
    scope: str = "all"


class LCAAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    items_count: Optional[int] = None
    optimal_classes_count: Optional[int] = None
    model_selection_criteria: Optional[List[Dict[str, Any]]] = None
    entropy: Optional[float] = None
    entropy_quality: Optional[str] = None
    class_prevalences: Optional[Dict[str, float]] = None
    class_profiles: Optional[List[Dict[str, Any]]] = None
    posterior_class_distribution: Optional[List[int]] = None
    svg_profile_plot: Optional[str] = None
    apa_narrative: Optional[str] = None


class DiDAnalysisRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    time_question_id: str
    treatment_value: Optional[str] = None
    post_value: Optional[str] = None
    scope: str = "all"


class DiDAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    groups: Optional[Dict[str, str]] = None
    cell_means_2x2: Optional[Dict[str, Any]] = None
    did_treatment_effect: Optional[Dict[str, Any]] = None
    regression_coefficients: Optional[Dict[str, Any]] = None
    svg_trajectory_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


class SEMPathSpec(BaseModel):
    source: str
    target: str


class SEMAnalysisRequest(BaseModel):
    paths: List[SEMPathSpec]
    scope: str = "all"


class SEMAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    observed_variables: Optional[List[str]] = None
    exogenous_variables: Optional[List[str]] = None
    endogenous_variables: Optional[List[str]] = None
    paths: Optional[List[Dict[str, Any]]] = None
    equations: Optional[List[Dict[str, Any]]] = None
    indirect_effects: Optional[List[Dict[str, Any]]] = None
    total_effects: Optional[List[Dict[str, Any]]] = None
    fit_indices: Optional[Dict[str, Any]] = None
    svg_path_diagram: Optional[str] = None
    apa_narrative: Optional[str] = None


class CompetingRisksAnalysisRequest(BaseModel):
    cluster_question_id: Optional[str] = None
    event_question_id: Optional[str] = None
    time_milestones: Optional[List[float]] = None
    scope: str = "all"


class CompetingRisksAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    competing_causes: Optional[List[str]] = None
    final_cumulative_incidence: Optional[Dict[str, float]] = None
    milestone_evaluations: Optional[List[Dict[str, Any]]] = None
    shared_frailty_model: Optional[Dict[str, Any]] = None
    svg_cif_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


class IRT4PLAnalysisRequest(BaseModel):
    question_ids: List[str]
    model_type: str = "4pl"
    binarization_threshold: Optional[float] = None
    scope: str = "all"


class IRT4PLAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    items_count: Optional[int] = None
    model_type: Optional[str] = None
    binarization_threshold: Optional[float] = None
    items_parameters: Optional[List[Dict[str, Any]]] = None
    test_information_function: Optional[Dict[str, Any]] = None
    cat_simulation: Optional[List[Dict[str, Any]]] = None
    svg_curves: Optional[str] = None
    apa_narrative: Optional[str] = None


class IPWAnalysisRequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    covariate_question_ids: List[str]
    treatment_value: Optional[str] = None
    weight_scheme: str = "ate"
    trim_weights: bool = True
    scope: str = "all"


class IPWAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    treated_count: Optional[int] = None
    control_count: Optional[int] = None
    weight_scheme: Optional[str] = None
    unadjusted_effect: Optional[Dict[str, Any]] = None
    ipw_estimator: Optional[Dict[str, Any]] = None
    doubly_robust_estimator: Optional[Dict[str, Any]] = None
    covariate_balance: Optional[Dict[str, Any]] = None
    svg_love_plot: Optional[str] = None
    apa_narrative: Optional[str] = None


class GAMSplineAnalysisRequest(BaseModel):
    predictor_question_id: str
    outcome_question_id: str
    n_knots: int = 5
    smoothing_penalty: float = 1.0
    scope: str = "all"


class GAMSplineAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    knots_count: Optional[int] = None
    knots: Optional[List[float]] = None
    linear_baseline: Optional[Dict[str, Any]] = None
    gam_spline_model: Optional[Dict[str, Any]] = None
    nonlinearity_test: Optional[Dict[str, Any]] = None
    turning_points: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Small Area Estimation (SAE; Fay & Herriot 1979, Rao & Molina 2015) Schemas ---
class SmallAreaEstimationRequest(BaseModel):
    area_question_id: str
    outcome_question_id: str
    auxiliary_question_ids: Optional[List[str]] = None
    scope: str = "all"


class SmallAreaEstimationOut(BaseModel):
    status: str
    message: Optional[str] = None
    area_count: Optional[int] = None
    between_area_variance_sigma_v2: Optional[float] = None
    mean_shrinkage_weight_gamma: Optional[float] = None
    mean_efficiency_gain_pct: Optional[float] = None
    regression_coefficients: Optional[List[Dict[str, Any]]] = None
    area_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None



class QuantileRegressionRequest(BaseModel):
    predictor_question_id: str
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = None
    scope: str = "all"


class QuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    covariates_count: Optional[int] = None
    ols_baseline: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    heterogeneity_test: Optional[Dict[str, Any]] = None
    svg_process_plot: Optional[str] = None
    apa_narrative: Optional[str] = None


class GTheoryAnalysisRequest(BaseModel):
    item_question_ids: List[str]
    rater_question_id: Optional[str] = None
    scope: str = "all"


class GTheoryAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    design_type: Optional[str] = None
    sample_size: Optional[int] = None
    items_count: Optional[int] = None
    variance_components: Optional[List[Dict[str, Any]]] = None
    current_design_metrics: Optional[Dict[str, Any]] = None
    d_study_projections: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Sharp Regression Discontinuity Design (RDD; Hahn et al. 2001, Imbens & Kalyanaraman 2012) Schemas ---
class RDDAnalysisRequest(BaseModel):
    running_question_id: str
    outcome_question_id: str
    cutoff: float
    bandwidth: Optional[float] = None
    polynomial_order: int = 1
    scope: str = "all"


class RDDAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    effective_sample_size: Optional[int] = None
    cutoff_threshold: Optional[float] = None
    bandwidth: Optional[float] = None
    treatment_effect_late: Optional[Dict[str, Any]] = None
    mccrary_manipulation_test: Optional[Dict[str, Any]] = None
    binned_scatter_points: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Synthetic Control Method (SCM; Abadie et al. 2010, Abadie 2021) Schemas ---
class SyntheticControlAnalysisRequest(BaseModel):
    unit_question_id: str
    period_question_id: str
    outcome_question_id: str
    treated_unit: str
    treatment_period: Any
    scope: str = "all"


class SyntheticControlAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    treated_unit: Optional[str] = None
    treatment_period: Optional[str] = None
    treatment_period_index: Optional[int] = None
    donor_pool_count: Optional[int] = None
    att_effect: Optional[float] = None
    rmspe_pre: Optional[float] = None
    rmspe_post: Optional[float] = None
    rmspe_ratio: Optional[float] = None
    empirical_p_value: Optional[float] = None
    is_significant: Optional[bool] = None
    top_donor_weights: Optional[List[Dict[str, Any]]] = None
    balance_table: Optional[List[Dict[str, Any]]] = None
    trajectory: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Small Area Estimation (SAE; Fay & Herriot 1979, Rao & Molina 2015) Schemas ---
class SmallAreaEstimationRequest(BaseModel):
    area_question_id: str
    outcome_question_id: str
    auxiliary_question_ids: Optional[List[str]] = None
    scope: str = "all"


class SmallAreaEstimationOut(BaseModel):
    status: str
    message: Optional[str] = None
    area_count: Optional[int] = None
    between_area_variance_sigma_v2: Optional[float] = None
    mean_shrinkage_weight_gamma: Optional[float] = None
    mean_efficiency_gain_pct: Optional[float] = None
    regression_coefficients: Optional[List[Dict[str, Any]]] = None
    area_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Dynamic Event-Study (Sun & Abraham 2021, Callaway & Sant'Anna 2021) Schemas ---
class EventStudyAnalysisRequest(BaseModel):
    unit_question_id: str
    time_question_id: str
    outcome_question_id: str
    event_time_question_id: Optional[str] = None
    treated_units: Optional[List[str]] = None
    global_event_time: Optional[Any] = None
    max_leads: int = 5
    max_lags: int = 5
    scope: str = "all"


class EventStudyAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    units_count: Optional[int] = None
    periods_count: Optional[int] = None
    event_window_min: Optional[int] = None
    event_window_max: Optional[int] = None
    pre_trend_wald_stat: Optional[float] = None
    pre_trend_df: Optional[int] = None
    pre_trend_p_value: Optional[float] = None
    parallel_trends_supported: Optional[bool] = None
    avg_post_treatment_effect: Optional[float] = None
    cumulative_post_treatment_effect: Optional[float] = None
    event_coefficients: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Bayesian Structural Time Series & Causal Impact (Brodersen et al. 2015) Schemas ---
class BSTSCausalImpactRequest(BaseModel):
    time_question_id: str
    outcome_question_id: str
    intervention_time: Any
    covariate_question_ids: Optional[List[str]] = None
    scope: str = "all"


class BSTSCausalImpactOut(BaseModel):
    status: str
    message: Optional[str] = None
    intervention_time: Optional[str] = None
    intervention_index: Optional[int] = None
    pre_periods_count: Optional[int] = None
    post_periods_count: Optional[int] = None
    avg_actual_post: Optional[float] = None
    avg_counterfactual_post: Optional[float] = None
    avg_pointwise_effect: Optional[float] = None
    cumulative_effect: Optional[float] = None
    relative_effect_pct: Optional[float] = None
    posterior_tail_p_value: Optional[float] = None
    is_significant: Optional[bool] = None
    trajectory: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Doubly Robust AIPW & Heterogeneous CATE (Robins et al. 1994, Chernozhukov et al. 2018) Schemas ---
class AIPWCATERequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    confounder_question_ids: List[str]
    subgroup_question_id: Optional[str] = None
    treatment_value: Optional[Any] = None
    trim_alpha: Optional[float] = 0.05
    scope: str = 'all'


class AIPWCATEOut(BaseModel):
    status: str
    message: Optional[str] = None
    ate: Optional[float] = None
    se: Optional[float] = None
    z_stat: Optional[float] = None
    p_value: Optional[float] = None
    ci_95_lower: Optional[float] = None
    ci_95_upper: Optional[float] = None
    is_significant: Optional[bool] = None
    naive_difference: Optional[float] = None
    selection_bias_estimate: Optional[float] = None
    total_sample_size: Optional[int] = None
    effective_sample_size: Optional[int] = None
    trimmed_units_count: Optional[int] = None
    propensity_overlap: Optional[Dict[str, Any]] = None
    subgroup_cate: Optional[List[Dict[str, Any]]] = None
    heterogeneity_test: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variables Two-Stage Least Squares (2SLS) Schemas ---
class IV2SLSRequest(BaseModel):
    outcome_question_id: str
    endogenous_question_id: str
    instrument_question_ids: List[str]
    control_question_ids: Optional[List[str]] = None
    scope: str = 'all'


class IV2SLSOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    instruments_count: Optional[int] = None
    iv_estimate: Optional[Dict[str, Any]] = None
    ols_benchmark: Optional[Dict[str, Any]] = None
    first_stage_diagnostics: Optional[Dict[str, Any]] = None
    wu_hausman_test: Optional[Dict[str, Any]] = None
    sargan_hansen_overid_test: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Bifactor Psychometric Modeling & Omega Hierarchical Schemas ---
class BifactorSubscaleMapping(BaseModel):
    subscale_name: str
    question_ids: List[str]


class BifactorAnalysisRequest(BaseModel):
    subscales: List[BifactorSubscaleMapping]
    scope: str = 'all'


class BifactorAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    items_count: Optional[int] = None
    subscales_count: Optional[int] = None
    omega_total: Optional[float] = None
    omega_hierarchical: Optional[float] = None
    explained_common_variance: Optional[float] = None
    percent_uncontaminated_correlations: Optional[float] = None
    is_essentially_unidimensional: Optional[bool] = None
    recommendation: Optional[str] = None
    subscale_metrics: Optional[List[Dict[str, Any]]] = None
    item_diagnostics: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Panel Vector Autoregression (Panel VAR) Schemas ---
class PanelVARRequest(BaseModel):
    unit_question_id: str
    time_question_id: str
    var1_question_id: str
    var2_question_id: str
    lags: Optional[int] = 1
    irf_horizons: Optional[int] = 6
    scope: str = 'all'


class PanelVAROut(BaseModel):
    status: str
    message: Optional[str] = None
    panel_units_count: Optional[int] = None
    effective_observations: Optional[int] = None
    lags: Optional[int] = None
    var1_name: Optional[str] = None
    var2_name: Optional[str] = None
    is_stable: Optional[bool] = None
    stability_max_modulus: Optional[float] = None
    causality_conclusion: Optional[str] = None
    equations: Optional[Dict[str, Any]] = None
    granger_causality: Optional[Dict[str, Any]] = None
    fevd_horizon_5: Optional[Dict[str, Any]] = None
    oirf_trajectory: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Latent Growth Curve Modeling (LGCM) Schemas ---
class LatentGrowthRequest(BaseModel):
    wave_question_ids: List[str]
    time_scores: Optional[List[float]] = None
    wave_labels: Optional[List[str]] = None
    scope: str = "all"


class LatentGrowthOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    waves_count: Optional[int] = None
    latent_means: Optional[Dict[str, Any]] = None
    latent_variances: Optional[Dict[str, Any]] = None
    model_fit: Optional[Dict[str, Any]] = None
    growth_dynamics: Optional[Dict[str, Any]] = None
    observed_wave_means: Optional[List[float]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Quantile Treatment Effects (QTE) Schemas ---
class QTERequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = None
    alpha_trim: Optional[float] = 0.05
    scope: str = "all"


class QTEOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    treated_count: Optional[int] = None
    control_count: Optional[int] = None
    average_treatment_effect: Optional[float] = None
    median_treatment_effect: Optional[float] = None
    delta_iqr_effect: Optional[float] = None
    delta_90_10_effect: Optional[float] = None
    has_heterogeneous_distributional_effects: Optional[bool] = None
    inequality_impact: Optional[str] = None
    quantile_effects: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Causal DAG & Structure Learning Schemas ---
class CausalDAGRequest(BaseModel):
    question_ids: List[str]
    alpha: Optional[float] = 0.05
    max_cond_size: Optional[int] = 2
    scope: str = "all"


class CausalDAGOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    variables_count: Optional[int] = None
    edges_count: Optional[int] = None
    directed_edges_count: Optional[int] = None
    undirected_edges_count: Optional[int] = None
    root_causes: Optional[List[str]] = None
    sink_outcomes: Optional[List[str]] = None
    mediators: Optional[List[str]] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Marginal Structural Models (MSM) Schemas ---
class MSMAnalysisRequest(BaseModel):
    treatment_question_ids: List[str]
    confounder_question_ids: List[str]
    outcome_question_id: str
    wave_labels: Optional[List[str]] = None
    scope: str = "all"


class MSMAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    waves_count: Optional[int] = None
    causal_effect_per_wave: Optional[float] = None
    std_error: Optional[float] = None
    z_statistic: Optional[float] = None
    p_value: Optional[float] = None
    ci_95_lower: Optional[float] = None
    ci_95_upper: Optional[float] = None
    naive_ols_effect: Optional[float] = None
    naive_ols_p_value: Optional[float] = None
    confounding_bias_pct: Optional[float] = None
    confounding_verdict: Optional[str] = None
    stabilized_weights_diagnostics: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Generalized Estimating Equations (GEE) Schemas ---
class GEEAnalysisRequest(BaseModel):
    cluster_question_id: str
    time_question_id: str
    outcome_question_id: str
    predictor_question_ids: List[str]
    family: Optional[str] = "gaussian"
    corstr: Optional[str] = "exchangeable"
    scope: str = "all"


class GEEAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    clusters_count: Optional[int] = None
    observations_count: Optional[int] = None
    family: Optional[str] = None
    working_correlation_structure: Optional[str] = None
    estimated_correlation_parameter: Optional[float] = None
    dispersion_phi: Optional[float] = None
    qic: Optional[float] = None
    coefficients: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Exact Permutation & Randomization Inference Schemas ---
class RandomizationInferenceRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    num_permutations: Optional[int] = 2500
    alternative: Optional[str] = "two-sided"
    scope: str = "all"


class RandomizationInferenceOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    treated_count: Optional[int] = None
    control_count: Optional[int] = None
    permutations_count: Optional[int] = None
    difference_in_means: Optional[Dict[str, Any]] = None
    difference_in_medians: Optional[Dict[str, Any]] = None
    wilcoxon_rank_sum: Optional[Dict[str, Any]] = None
    hodges_lehmann_shift: Optional[Dict[str, Any]] = None
    asymptotic_welch_t_test: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Value Theory (EVT) & Survey Tail Risk Schemas ---
class EVTAnalysisRequest(BaseModel):
    metric_question_id: str
    threshold_percentile: Optional[float] = 0.90
    custom_threshold: Optional[float] = None
    alpha_levels: Optional[List[float]] = [0.95, 0.99, 0.995]
    scope: str = "all"


class EVTAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    threshold: Optional[float] = None
    exceedances_count: Optional[int] = None
    exceedance_probability: Optional[float] = None
    shape_xi: Optional[float] = None
    se_shape_xi: Optional[float] = None
    scale_sigma: Optional[float] = None
    se_scale_sigma: Optional[float] = None
    tail_classification: Optional[str] = None
    tail_interpretation: Optional[str] = None
    gof_ks_statistic: Optional[float] = None
    gof_ks_p_value: Optional[float] = None
    gof_passed: Optional[bool] = None
    risk_measures: Optional[List[Dict[str, Any]]] = None
    mean_excess_grid: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None
    



# --- Multilevel Structural Equation Modeling (MSEM) Schemas ---
class MSEMAnalysisRequest(BaseModel):
    cluster_question_id: str
    x_question_id: str
    m_question_id: str
    y_question_id: str
    n_mc_sims: int = 2000
    scope: str = "all"


class MSEMAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    cluster_field: Optional[str] = None
    x_field: Optional[str] = None
    m_field: Optional[str] = None
    y_field: Optional[str] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    intraclass_correlations: Optional[Dict[str, Any]] = None
    level1_within_submodel: Optional[Dict[str, Any]] = None
    level2_between_submodel: Optional[Dict[str, Any]] = None
    conflation_test: Optional[Dict[str, Any]] = None
    fit_indices: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Targeted Maximum Likelihood Estimation (TMLE) Schemas ---
class TMLEAnalysisRequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    covariate_question_ids: List[str]
    gbound: float = 0.025
    target_treatment_val: Optional[Any] = None
    control_treatment_val: Optional[Any] = None
    scope: str = "all"


class TMLEAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    treatment_field: Optional[str] = None
    outcome_field: Optional[str] = None
    covariate_fields: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    targeted_parameters: Optional[Dict[str, Any]] = None
    estimator_comparisons: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Synthetic Difference-in-Differences (SDID) Schemas ---
class SDIDAnalysisRequest(BaseModel):
    unit_question_id: str
    time_question_id: str
    outcome_question_id: str
    treated_units: List[str]
    treatment_start_time: Any
    n_placebo_reps: int = 200
    scope: str = "all"


class SDIDAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    unit_field: Optional[str] = None
    time_field: Optional[str] = None
    outcome_field: Optional[str] = None
    treated_units: Optional[List[str]] = None
    treatment_start_time: Optional[str] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    sdid_estimates: Optional[Dict[str, Any]] = None
    comparison_estimates: Optional[Dict[str, Any]] = None
    top_donor_weights: Optional[List[Dict[str, Any]]] = None
    time_weights: Optional[List[Dict[str, Any]]] = None
    time_trajectories: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Generalized Causal Forest (GRF) Schemas ---
class CausalForestAnalysisRequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    feature_question_ids: List[str]
    n_trees: int = 40
    min_leaf_size: int = 5
    target_treatment_val: Optional[Any] = None
    scope: str = "all"


class CausalForestAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    treatment_field: Optional[str] = None
    outcome_field: Optional[str] = None
    feature_fields: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    cate_summary: Optional[Dict[str, Any]] = None
    variable_importance: Optional[List[Dict[str, Any]]] = None
    cate_distribution: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Bayesian Structural Equation Modeling (BSEM) Schemas ---
class BSEMRequest(BaseModel):
    measurement_spec: Dict[str, List[str]]
    structural_regressions: Optional[List[Dict[str, str]]] = None
    prior_cross_loading_sd: float = 0.01
    n_iterations: int = 800
    n_burnin: int = 300
    n_chains: int = 2
    scope: str = "all"


class BSEMOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    structural_paths: Optional[List[Dict[str, Any]]] = None
    loadings: Optional[List[Dict[str, Any]]] = None
    prior_sensitivity: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Gaussian Copula Endogeneity Estimation Schemas (Park & Gupta 2012) ---
class GaussianCopulaRequest(BaseModel):
    endogenous_question_id: str
    outcome_question_id: str
    control_question_ids: Optional[List[str]] = None
    n_bootstraps: int = 400
    scope: str = "all"


class GaussianCopulaOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    naive_ols: Optional[Dict[str, Any]] = None
    copula_corrected: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Dynamic Factor Modeling (DFM) Schemas (Stock & Watson 2002) ---
class DynamicFactorModelRequest(BaseModel):
    indicator_question_ids: List[str]
    wave_question_id: Optional[str] = None
    time_field: str = "wave"
    n_factors: int = 1
    scope: str = "all"


class DynamicFactorModelOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    trajectory: Optional[List[Dict[str, Any]]] = None
    variance_decomposition: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

with open('backend/app/schemas.py', 'a', encoding='utf-8') as f:
    f.write('''

# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None
''')
print('Schemas appended successfully.')

with open('backend/app/schemas.py', 'a', encoding='utf-8') as f:
    f.write('''

# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None
''')
print("Spatial econometrics schemas appended successfully.")

with open('backend/app/schemas.py', 'a', encoding='utf-8') as f:
    f.write('''

# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None
''')
print("IV-QR schemas appended successfully.")

# --- Choice-Based Conjoint with Hierarchical Bayes (HB-CBC; Rossi et al. 2005) Schemas ---
class ConjointHBAnalysisRequest(BaseModel):
    attributes_config: Dict[str, List[str]]
    tasks_data: Optional[List[Dict[str, Any]]] = None
    choice_question_id: Optional[str] = None
    profile_attribute_mapping: Optional[Dict[str, str]] = None
    price_attribute: Optional[str] = None
    simulation_scenarios: Optional[List[Dict[str, Any]]] = None
    n_draws: int = 500
    burn_in: int = 150
    scope: str = "all"


class ConjointHBAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    attribute_importance: Optional[List[Dict[str, Any]]] = None
    attribute_details: Optional[Dict[str, Any]] = None
    part_worth_utilities: Optional[List[Dict[str, Any]]] = None
    willingness_to_pay: Optional[Dict[str, Any]] = None
    market_simulations: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Fractional Response Regression (Papke & Wooldridge 1996, 2008) Schemas ---
class FractionalResponseRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: List[str]
    link: str = "logit"
    scale_from_percentage: bool = True
    scope: str = "all"


class FractionalResponseOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    coefficients: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Multidimensional Item Response Theory (MIRT; Reckase 2009) Schemas ---
class MIRTAnalysisRequest(BaseModel):
    item_question_ids: List[str]
    n_dimensions: int = 2
    dimension_names: Optional[List[str]] = None
    max_em_iter: int = 40
    scope: str = "all"


class MIRTAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    item_parameters: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Heckman Sample Selection Model (Heckman 1979) Schemas ---
class HeckmanSelectionRequest(BaseModel):
    outcome_question_id: str
    selection_indicator_question_id: Optional[str] = None
    outcome_covariate_question_ids: List[str]
    exclusion_restriction_question_ids: Optional[List[str]] = None
    scope: str = "all"


class HeckmanSelectionOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    coefficients_comparison: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Zero-Inflated Count Models (ZIP & ZINB; Lambert 1992, Greene 1994, Vuong 1989) Schemas ---
class ZeroInflatedRequest(BaseModel):
    count_question_id: str
    covariate_question_ids: List[str]
    inflation_covariate_question_ids: Optional[List[str]] = None
    model_type: str = "ZIP"  # "ZIP" or "ZINB"
    scope: str = "all"


class ZeroInflatedOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    count_model_coefficients: Optional[List[Dict[str, Any]]] = None
    inflation_model_coefficients: Optional[List[Dict[str, Any]]] = None
    frequency_distribution: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Latent Moderated Structural Equations (LMS / QML; Klein & Moosbrugger 2000) Schemas ---
class LatentModerationRequest(BaseModel):
    predictor_item_ids: List[str]
    moderator_item_ids: List[str]
    outcome_item_ids: List[str]
    scope: str = "all"


class LatentModerationOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    coefficients: Optional[List[Dict[str, Any]]] = None
    simple_slopes: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Endogenous Switching Regression (ESR; Maddala 1983, Lokshin & Sajaia 2004) Schemas ---
class EndogenousSwitchingRequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    covariate_question_ids: List[str]
    instrument_question_ids: Optional[List[str]] = None
    scope: str = "all"


class EndogenousSwitchingOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    treatment_effects: Optional[Dict[str, Any]] = None
    coefficients: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Generalized Propensity Score (GPS) Dose-Response (Hirano & Imbens 2004) Schemas ---
class GPSDoseResponseRequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    covariate_question_ids: List[str]
    n_grid_points: int = 30
    scope: str = "all"


class GPSDoseResponseOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    dose_response_curve: Optional[List[Dict[str, Any]]] = None
    marginal_effects_curve: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Causal Discovery DAG (LiNGAM & ANM) Schemas ---
class CausalDiscoveryRequest(BaseModel):
    variable_question_ids: List[str]
    prune_threshold: float = 0.05
    scope: str = "all"


class CausalDiscoveryOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    causal_order: Optional[List[str]] = None
    directed_edges: Optional[List[Dict[str, Any]]] = None
    non_gaussianity_tests: Optional[List[Dict[str, Any]]] = None
    anm_diagnostics: Optional[List[Dict[str, Any]]] = None
    adjacency_matrix: Optional[Dict[str, Any]] = None
    total_effects_matrix: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Bayesian Additive Regression Trees (BART) Causal Schemas ---
class BARTCausalRequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    covariate_question_ids: List[str]
    n_trees: int = 50
    n_samples: int = 200
    scope: str = "all"


class BARTCausalOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    treatment_effects: Optional[Dict[str, Any]] = None
    ite_distribution: Optional[Dict[str, Any]] = None
    variable_importance: Optional[List[Dict[str, Any]]] = None
    subgroup_cate: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Conjoint Analysis & Discrete Choice Experiment (DCE) Schemas ---
class ConjointChoiceRequest(BaseModel):
    choice_question_id: str
    attribute_question_ids: List[str]
    price_question_id: Optional[str] = None
    price_unit: str = "mil VND"
    scope: str = "all"


class ConjointChoiceOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    part_worth_utilities: Optional[List[Dict[str, Any]]] = None
    willingness_to_pay: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Multi-Group SEM Invariance & Latent Means Schemas ---
class MGSEMInvarianceRequest(BaseModel):
    group_question_id: str
    indicator_question_ids: List[str]
    reference_group: Optional[str] = None
    scope: str = "all"


class MGSEMInvarianceOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    invariance_hierarchy: Optional[List[Dict[str, Any]]] = None
    latent_means_comparison: Optional[Dict[str, Any]] = None
    indicator_parameters: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Generalized Additive Models (GAM) & Penalized Spline Schemas ---
class GAMSplineRequest(BaseModel):
    predictor_question_id: str
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    n_knots: int = 10
    grid_points: int = 60
    scope: str = "all"


class GAMSplineOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    tipping_points: Optional[List[Dict[str, Any]]] = None
    smooth_curve: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Latent Profile Analysis (LPA) Schemas ---
class LatentProfileRequest(BaseModel):
    indicator_question_ids: List[str]
    n_profiles: Optional[int] = None
    max_profiles: int = 4
    scope: str = "all"


class LatentProfileOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    model_comparison: Optional[List[Dict[str, Any]]] = None
    profiles: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Shapley Value Regression & Key Driver Analysis (KDA) Schemas ---
class ShapleyDriverRequest(BaseModel):
    driver_question_ids: List[str]
    outcome_question_id: str
    scope: str = "all"


class ShapleyDriverOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    drivers: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Plackett-Luce Choice Model & Rank-Ordered Logit Schemas ---
class PlackettLuceRequest(BaseModel):
    ranking_question_id: Optional[str] = None
    item_question_ids: Optional[List[str]] = None
    scope: str = "all"


class PlackettLuceOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None
    pairwise_win_matrix: Optional[List[List[float]]] = None
    item_labels: Optional[List[str]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- MaxDiff Best-Worst Scaling Schemas ---
class MaxDiffRequest(BaseModel):
    best_question_id: Optional[str] = None
    worst_question_id: Optional[str] = None
    item_question_ids: Optional[List[str]] = None
    scope: str = "all"


class MaxDiffOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Bayesian Network DAG Structure Learning Schemas ---
class BayesianNetworkRequest(BaseModel):
    question_ids: List[str]
    max_parents: int = 4
    scope: str = "all"


class BayesianNetworkOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None





# --- Joint Modeling of Longitudinal & Survival Data Schemas ---
class JointModelAnalysisRequest(BaseModel):
    subject_question_id: str
    time_question_id: str
    outcome_question_id: str
    event_question_id: Optional[str] = None
    event_time_question_id: Optional[str] = None
    scope: str = "all"


class JointModelAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    total_longitudinal_observations: Optional[int] = None
    events_attrited_count: Optional[int] = None
    censored_retained_count: Optional[int] = None
    longitudinal_submodel: Optional[Dict[str, Any]] = None
    survival_submodel: Optional[Dict[str, Any]] = None
    attrition_diagnostics: Optional[Dict[str, Any]] = None
    dynamic_predictions: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

class JointModelAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_size: Optional[int] = None
    total_longitudinal_observations: Optional[int] = None
    events_attrited_count: Optional[int] = None
    censored_retained_count: Optional[int] = None
    longitudinal_submodel: Optional[Dict[str, Any]] = None
    survival_submodel: Optional[Dict[str, Any]] = None
    attrition_diagnostics: Optional[Dict[str, Any]] = None
    dynamic_predictions: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Conformal Prediction & Distribution-Free Risk Intervals Schemas ---
class ConformalPredictionAnalysisRequest(BaseModel):
    target_question_id: str
    feature_question_ids: List[str]
    alpha: float = 0.05
    method: str = "split_conformal"  # 'split_conformal' or 'locally_weighted'
    calib_fraction: float = 0.30
    test_fraction: float = 0.20
    clamp_min: Optional[float] = None
    clamp_max: Optional[float] = None
    scope: str = "all"


class ConformalPredictionAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    method: Optional[str] = None
    target_field: Optional[str] = None
    feature_fields: Optional[List[str]] = None
    sample_sizes: Optional[Dict[str, int]] = None
    parameters: Optional[Dict[str, Any]] = None
    evaluation_metrics: Optional[Dict[str, Any]] = None
    calibration_curve: Optional[List[Dict[str, Any]]] = None
    sample_predictions: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

class CausalForestAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    treatment_field: Optional[str] = None
    outcome_field: Optional[str] = None
    feature_fields: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    cate_summary: Optional[Dict[str, Any]] = None
    variable_importance: Optional[List[Dict[str, Any]]] = None
    cate_distribution: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Causal Mediation Sensitivity Analysis (Imai, Keele, Tingley 2010) Schemas ---
class CausalMediationSensitivityRequest(BaseModel):
    treatment_question_id: str
    mediator_question_id: str
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    target_treatment_val: Optional[Any] = None
    scope: str = "all"


class CausalMediationSensitivityOut(BaseModel):
    status: str
    message: Optional[str] = None
    treatment_field: Optional[str] = None
    mediator_field: Optional[str] = None
    outcome_field: Optional[str] = None
    covariate_fields: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    path_estimates: Optional[Dict[str, Any]] = None
    baseline_effects: Optional[Dict[str, Any]] = None
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

class CausalMediationSensitivityOut(BaseModel):
    status: str
    message: Optional[str] = None
    treatment_field: Optional[str] = None
    mediator_field: Optional[str] = None
    outcome_field: Optional[str] = None
    covariate_fields: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    path_estimates: Optional[Dict[str, Any]] = None
    baseline_effects: Optional[Dict[str, Any]] = None
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Dynamic Time Warping (DTW) Trajectory Clustering Schemas ---
class DTWClusteringRequest(BaseModel):
    time_series_question_ids: List[str]
    time_labels: Optional[List[str]] = None
    n_clusters: int = 3
    window_radius: Optional[int] = None
    scope: str = "all"


class DTWClusteringOut(BaseModel):
    status: str
    message: Optional[str] = None
    time_series_fields: Optional[List[str]] = None
    time_labels: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    clusters: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

class DTWClusteringOut(BaseModel):
    status: str
    message: Optional[str] = None
    time_series_fields: Optional[List[str]] = None
    time_labels: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    clusters: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Causal Interaction Trees & Honest Subgroup Identification Schemas ---
class CausalTreeSubgroupRequest(BaseModel):
    treatment_question_id: str
    outcome_question_id: str
    feature_question_ids: List[str]
    max_depth: int = 3
    min_leaf_size: int = 5
    target_treatment_val: Optional[Any] = None
    scope: str = "all"


class CausalTreeSubgroupOut(BaseModel):
    status: str
    message: Optional[str] = None
    treatment_field: Optional[str] = None
    outcome_field: Optional[str] = None
    feature_fields: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    subgroups: Optional[List[Dict[str, Any]]] = None
    tree_structure: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

class CausalTreeSubgroupOut(BaseModel):
    status: str
    message: Optional[str] = None
    treatment_field: Optional[str] = None
    outcome_field: Optional[str] = None
    feature_fields: Optional[List[str]] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    subgroups: Optional[List[Dict[str, Any]]] = None
    tree_structure: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Multiple Testing Correction & False Discovery Rate (FDR) Schemas ---
class MultipleTestingFDRRequest(BaseModel):
    question_ids: Optional[List[str]] = None
    custom_p_values: Optional[List[float]] = None
    custom_labels: Optional[List[str]] = None
    fdr_q: float = 0.05
    scope: str = "all"


class MultipleTestingFDROut(BaseModel):
    status: str
    message: Optional[str] = None
    sample_diagnostics: Optional[Dict[str, Any]] = None
    corrections: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None

class HeckmanSelectionOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    coefficients_comparison: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Stochastic Frontier Analysis (SFA; Aigner, Lovell & Schmidt 1977; JLMS 1982) Schemas ---
class StochasticFrontierRequest(BaseModel):
    output_question_id: str
    input_question_ids: List[str]
    log_transform: bool = True
    scope: str = "all"


class StochasticFrontierOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    coefficients: Optional[List[Dict[str, Any]]] = None
    inefficiency_summary: Optional[Dict[str, Any]] = None
    individual_efficiency_sample: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None

# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Stochastic Dominance & Distributional Inequality Schemas ---
class StochasticDominanceRequest(BaseModel):
    outcome_question_id: str
    group_question_id: str
    group_a_value: Optional[str] = None
    group_b_value: Optional[str] = None
    group_a_label: Optional[str] = None
    group_b_label: Optional[str] = None
    n_grid_points: int = 50
    scope: str = "all"


class StochasticDominanceOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    grid_thresholds: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Manski Non-Parametric Partial Identification & Worst-Case Bounds Schemas (Manski 1990, 2000; Imbens & Manski 2004) ---
class ManskiBoundsRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    response_indicator_question_id: Optional[str] = None
    support_min: Optional[float] = None
    support_max: Optional[float] = None
    confidence_level: float = 0.95
    scope: str = "all"


class ManskiBoundsOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    tiers: Optional[List[Dict[str, Any]]] = None
    sensitivity_grid: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Schemas (Murphy 2003, Robins 2004) ---
class DynamicTreatmentRegimesRequest(BaseModel):
    outcome_question_id: str
    stage1_action_question_id: str
    stage2_action_question_id: str
    baseline_covariate_question_id: str
    interim_state_question_id: str
    scope: str = "all"


class DynamicTreatmentRegimesOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    stage1_model: Optional[Dict[str, Any]] = None
    stage2_model: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Finite Mixture Rasch Models (FMRM) & Latent Class IRT Schemas (Rost 1990; von Davier & Rost 2007) ---
class FiniteMixtureRaschRequest(BaseModel):
    question_ids: List[str]
    n_classes: int = 2
    scope: str = "all"


class FiniteMixtureRaschOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    class_proportions: Optional[List[Dict[str, Any]]] = None
    items_parameters: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Double / Debiased Machine Learning (DML) Schemas (Chernozhukov et al. 2018) ---
class DoubleMachineLearningRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    covariate_question_ids: List[str]
    n_folds: int = 5
    alpha_penalty: float = 1.0
    scope: str = "all"


class DoubleMachineLearningOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    confounding_covariates: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Regression Kink Design (RKD) Schemas (Card et al. 2015; Dong 2018) ---
class RegressionKinkRequest(BaseModel):
    outcome_question_id: str
    running_question_id: str
    cutoff: float
    treatment_question_id: Optional[str] = None
    bandwidth: Optional[float] = None
    polynomial_order: int = 1
    known_kink_slope: float = 1.0
    scope: str = "all"


class RegressionKinkOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    binned_scatter: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


class StaggeredDIDRequest(BaseModel):
    outcome_question_id: str
    unit_question_id: str
    time_question_id: str
    treatment_timing_question_id: str
    anticipation_periods: Optional[int] = 0
    control_group_type: Optional[str] = "never_treated"
    scope: Optional[str] = "all"


class StaggeredDIDOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    group_time_effects: Optional[List[Dict[str, Any]]] = None
    event_study_effects: Optional[List[Dict[str, Any]]] = None
    bacon_decomposition: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


class MatrixCompletionCausalRequest(BaseModel):
    outcome_question_id: str
    unit_question_id: str
    time_question_id: str
    treatment_question_id: str
    lambda_penalty: Optional[float] = None
    max_rank: Optional[int] = 5
    scope: Optional[str] = "all"


class MatrixCompletionCausalOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    cell_treatment_effects: Optional[List[Dict[str, Any]]] = None
    singular_value_spectrum: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


class SDIDAdvancedRequest(BaseModel):
    outcome_question_id: str
    unit_question_id: str
    time_question_id: str
    treatment_question_id: str
    zeta_regularization: Optional[float] = None
    scope: Optional[str] = "all"


class SDIDAdvancedOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    unit_weights: Optional[List[Dict[str, Any]]] = None
    time_weights: Optional[List[Dict[str, Any]]] = None
    trajectories: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


class InteractiveFixedEffectsRequest(BaseModel):
    outcome_question_id: str
    unit_question_id: str
    time_question_id: str
    treatment_question_id: str
    num_factors: Optional[int] = None
    max_factors: int = 4
    scope: Optional[str] = "all"


class InteractiveFixedEffectsOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    latent_factors: Optional[List[Dict[str, Any]]] = None
    scree_spectrum: Optional[List[Dict[str, Any]]] = None
    cell_effects: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


class MultipleMediatorsRequest(BaseModel):
    treatment_question_id: str
    mediator1_question_id: str
    mediator2_question_id: str
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    n_bootstraps: int = 500
    scope: Optional[str] = "all"


class MultipleMediatorsOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    path_coefficients: Optional[List[Dict[str, Any]]] = None
    effects_summary: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


class PolicyLearningRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    covariate_question_ids: List[str]
    primary_feature_idx: int = 0
    n_bootstraps: int = 300
    scope: Optional[str] = "all"


class PolicyLearningOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    regimes_comparison: Optional[List[Dict[str, Any]]] = None
    sample_allocations: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


class RDDLocalRandomizationRequest(BaseModel):
    outcome_question_id: str
    running_question_id: str
    cutoff: float = 0.0
    covariate_question_ids: Optional[List[str]] = None
    window_half_width: Optional[float] = None
    n_permutations: int = 1000
    scope: Optional[str] = "all"


class RDDLocalRandomizationOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    balance_table: Optional[List[Dict[str, Any]]] = None
    discrete_bins: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None






# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Dynamic Panel System & Difference GMM (Arellano-Bond 1991, Blundell-Bond 1998, Windmeijer 2005) ---
class DynamicPanelGMMRequest(BaseModel):
    unit_id_question_id: str
    time_question_id: str
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    method: str = "system"  # "system" or "difference"
    two_step: bool = True
    windmeijer_correction: bool = True
    max_instrument_lags: int = 3
    scope: str = "all"


class DynamicPanelGMMOut(BaseModel):
    status: str
    model_type: Optional[str] = None
    message: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Weak-Instrument Robust Inference (Anderson-Rubin 1949, Moreira 2003 CLR, Montiel Olea & Pflueger 2013) ---
class WeakIVRobustRequest(BaseModel):
    outcome_question_id: str
    endogenous_question_id: str
    instrument_question_ids: List[str]
    covariate_question_ids: Optional[List[str]] = None
    alpha_level: float = 0.05
    grid_points: int = 120
    scope: str = "all"


class WeakIVRobustOut(BaseModel):
    status: str
    model_type: Optional[str] = None
    message: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    estimates: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Sequential Causal Mediation Analysis (Hayes Model 6 / Imai & Yamamoto 2013) ---
class SequentialMediationRequest(BaseModel):
    treatment_question_id: str
    mediator1_question_id: str
    mediator2_question_id: str
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    n_bootstraps: int = 500
    alpha_level: float = 0.05
    scope: str = "all"


class SequentialMediationOut(BaseModel):
    status: str
    model_type: Optional[str] = None
    message: Optional[str] = None
    sample_size: Optional[int] = None
    bootstrap_replications: Optional[int] = None
    effects: Optional[Dict[str, Any]] = None
    proportions: Optional[Dict[str, Any]] = None
    regression_equations: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- High-Dimensional Post-Double-Selection Lasso (Belloni, Chernozhukov, & Hansen 2014) ---
class PostDoubleSelectionLassoRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    candidate_control_question_ids: List[str]
    cv_folds: int = 5
    alpha_level: float = 0.05
    scope: str = "all"


class PostDoubleSelectionLassoOut(BaseModel):
    status: str
    model_type: Optional[str] = None
    message: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    selected_controls: Optional[List[Dict[str, Any]]] = None
    estimates: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Local Average Response Function (LARF; Abadie 2003 Econometrica) Schemas ---
class LARFRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    model_type: str = "logit"
    alpha_level: float = 0.05
    n_bootstraps: int = 300
    trim_negative: bool = False
    scope: str = "all"


class LARFOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    sample_size: Optional[int] = None
    effective_sample_size: Optional[float] = None
    bootstrap_replications: Optional[int] = None
    complier_probability: Optional[float] = None
    complier_probability_se: Optional[float] = None
    pct_negative_weights: Optional[float] = None
    potential_outcomes_compliers: Optional[Dict[str, float]] = None
    effects: Optional[Dict[str, Any]] = None
    model_coefficients: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Marginal Treatment Effects (MTE; Heckman & Vytlacil 1999, 2005) Schemas ---
class MTERequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_ids: List[str]
    covariate_question_ids: Optional[List[str]] = None
    poly_degree: int = 3
    alpha_level: float = 0.05
    n_bootstraps: int = 300
    policy_shift_pct: float = 0.15
    scope: str = "all"


class MTEOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    sample_size: Optional[int] = None
    bootstrap_replications: Optional[int] = None
    polynomial_degree: Optional[int] = None
    common_support: Optional[Dict[str, float]] = None
    selection_sorting_pattern: Optional[str] = None
    mte_slope: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None
    mte_curve: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Non-random Survey Attrition & Selection Bounds (Lee Bounds 2009 Restud) Schemas ---
class LeeBoundsRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    response_question_id: Optional[str] = None
    covariate_question_ids: Optional[List[str]] = None
    alpha_level: float = 0.05
    n_bootstraps: int = 300
    scope: str = "all"


class LeeBoundsOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    sample_size: Optional[int] = None
    observed_sample_size: Optional[int] = None
    bootstrap_replications: Optional[int] = None
    response_rates: Optional[Dict[str, Any]] = None
    bounds: Optional[Dict[str, Any]] = None
    naive_complete_case: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Surrogate Index Long-Term Causal Evaluation (Athey, Chetty, Imbens, & Kang 2019) Schemas ---
class SurrogateIndexRequest(BaseModel):
    treatment_question_id: str
    surrogate_question_ids: List[str]
    longterm_outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    sample_indicator_question_id: Optional[str] = None
    alpha_level: float = 0.05
    n_bootstraps: int = 300
    ridge_lambda: float = 1.0
    scope: str = "all"


class SurrogateIndexOut(BaseModel):
    status: str
    message: Optional[str] = None
    model_type: Optional[str] = None
    sample_sizes: Optional[Dict[str, int]] = None
    bootstrap_replications: Optional[int] = None
    surrogate_index_fit: Optional[Dict[str, Any]] = None
    longterm_treatment_effect: Optional[Dict[str, Any]] = None
    surrogate_decomposition: Optional[List[Dict[str, Any]]] = None
    surrogacy_validation: Optional[Dict[str, Any]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None



# --- Conformal Counterfactual Risk Inference (Chernozhukov et al. 2021; Lei & Candes 2021) Schemas ---
class ConformalCounterfactualRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    covariate_question_ids: List[str]
    miscoverage_alpha: float = 0.10
    calibration_ratio: float = 0.50
    use_propensity_weighting: bool = True
    subgroup_question_id: Optional[str] = None
    scope: str = "all"


class ConformalCounterfactualOut(BaseModel):
    status: str
    message: Optional[str] = None
    overall_summary: Optional[Dict[str, Any]] = None
    calibration_diagnostics: Optional[Dict[str, Any]] = None
    subgroup_risk_profiles: Optional[List[Dict[str, Any]]] = None
    individual_predictions_sample: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None



# --- Causal Sensitivity Analysis & Omitted Variable Bias (Cinelli & Hazlett 2020) Schemas ---
class CausalSensitivityBiasRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    q_reduction: float = 1.0
    alpha_level: float = 0.05
    benchmark_question_ids: Optional[List[str]] = None
    benchmark_multipliers: Optional[List[float]] = [1.0, 2.0, 3.0]
    scope: str = "all"


class CausalSensitivityBiasOut(BaseModel):
    status: str
    message: Optional[str] = None
    overall_summary: Optional[Dict[str, Any]] = None
    covariate_benchmarks: Optional[List[Dict[str, Any]]] = None
    benchmark_scenarios: Optional[List[Dict[str, Any]]] = None
    svg_visualization: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) Schemas ---
class ExtremeBoundsAnalysisRequest(BaseModel):
    focus_question_id: str
    outcome_question_id: str
    candidate_question_ids: List[str]
    free_question_ids: Optional[List[str]] = None
    max_controls_per_model: int = 4
    scope: str = "all"


class ExtremeBoundsAnalysisOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    specifications_sample: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) Schemas ---
class SpatialEconometricsRequest(BaseModel):
    outcome_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    lat_field: str = "latitude"
    lon_field: str = "longitude"
    weights_type: str = "inverse_distance"
    knn_k: int = 5
    distance_power: float = 1.0
    scope: str = "all"


class SpatialEconometricsOut(BaseModel):
    status: str
    message: Optional[str] = None
    morans_i: Optional[Dict[str, Any]] = None
    lm_diagnostics: Optional[Dict[str, Any]] = None
    baseline_ols: Optional[Dict[str, Any]] = None
    spatial_lag_model: Optional[Dict[str, Any]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None


# --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) Schemas ---
class IVQuantileRegressionRequest(BaseModel):
    outcome_question_id: str
    treatment_question_id: str
    instrument_question_id: str
    covariate_question_ids: Optional[List[str]] = None
    quantiles: Optional[List[float]] = [0.10, 0.25, 0.50, 0.75, 0.90]
    grid_points: int = 80
    scope: str = "all"


class IVQuantileRegressionOut(BaseModel):
    status: str
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quantile_estimates: Optional[List[Dict[str, Any]]] = None
    svg_chart: Optional[str] = None
    apa_narrative: Optional[str] = None
