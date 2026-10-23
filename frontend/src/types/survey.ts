export type QuestionType =
  | 'short_text'
  | 'long_text'
  | 'single_choice'
  | 'multiple_choice'
  | 'dropdown'
  | 'linear_scale'
  | 'likert'
  | 'matrix'
  | 'number'
  | 'date'
  | 'boolean'
  | 'ranking';

export interface QuestionOption {
  id: string;
  label: string;
}

export interface MatrixOptions {
  rows: { id: string; label: string }[];
  columns: { id: string; label: string }[];
}

export interface LogicRule {
  depends_on_question_id: string;
  operator: 'equals' | 'not_equals';
  value: any;
  action: 'show' | 'hide';
}

export interface Question {
  id: string;
  survey_id?: string;
  order_index: number;
  question_type: QuestionType;
  title: string;
  description?: string;
  is_required: boolean;
  options: QuestionOption[] | MatrixOptions | any;
  logic_rules: LogicRule[];
}

export interface Survey {
  id: string;
  title: string;
  description: string;
  instructions: string;
  status: 'draft' | 'published' | 'closed' | 'archived';
  public_slug: string;
  version: number;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
  questions: Question[];
  responses_count?: number;
}

export interface SurveyListItem {
  id: string;
  title: string;
  description: string;
  status: 'draft' | 'published' | 'closed' | 'archived';
  public_slug: string;
  version: number;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
  questions_count: number;
  responses_count: number;
  avg_risk_score: number;
}

export interface QualityFlag {
  code: string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  details?: Record<string, any>;
}

export interface QualityAssessment {
  id: string;
  score_dup: number;
  score_pattern: number;
  score_logic: number;
  score_speed: number;
  score_text: number;
  score_enum?: number;
  composite_score: number;
  flags: QualityFlag[];
  closest_match_response_id?: string | null;
  highest_similarity: number;
  assessed_at: string;
}

export interface ResponseListItem {
  id: string;
  survey_id: string;
  started_at: string;
  submitted_at: string;
  duration_seconds: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  analysis_status: string;
  review_status: 'unverified' | 'under_review' | 'verified_valid' | 'verified_fraud' | 'inconclusive';
  flags_count: number;
  flags_summary: string[];
  source?: string;
  enumerator_id?: string;
  omr_confidence?: number;
}

export interface ResponseDetail {
  id: string;
  survey_id: string;
  survey_title: string;
  survey_version: number;
  started_at: string;
  submitted_at: string;
  duration_seconds: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  analysis_status: string;
  review_status: 'unverified' | 'under_review' | 'verified_valid' | 'verified_fraud' | 'inconclusive';
  review_notes: string;
  reviewed_at?: string | null;
  client_metadata: Record<string, any>;
  answers: Record<string, any>;
  questions: Question[];
  assessment?: QualityAssessment | null;
  source?: string;
  enumerator_id?: string;
  paper_form_id?: string;
  scan_image_url?: string;
  omr_confidence?: number;
}

// --- Paper Survey & OMR Types ---
export interface PaperBubbleConfig {
  option_id: string;
  option_label: string;
  x: number;
  y: number;
  radius: number;
}

export interface PaperQuestionLayout {
  question_id: string;
  question_type: string;
  title: string;
  order_index: number;
  box_x: number;
  box_y: number;
  box_w: number;
  box_h: number;
  bubbles: PaperBubbleConfig[];
}

export interface PaperTemplateLayout {
  survey_id: string;
  survey_title: string;
  template_version: number;
  page_width: number;
  page_height: number;
  fiducial_markers: { id: string; x: number; y: number; w: number; h: number }[];
  qr_region: { x: number; y: number; w: number; h: number };
  questions: PaperQuestionLayout[];
}

export interface PaperScanResult {
  success: boolean;
  survey_id: string;
  form_id: string;
  enumerator_id: string;
  image_quality: {
    is_passed: boolean;
    laplacian_variance: number;
    sharpness_status: string;
    mean_brightness: number;
    contrast_std: number;
    message: string;
  };
  confidence_score: number;
  detected_answers: Record<string, any>;
  question_confidences: Record<string, number>;
  overlay_image_base64?: string | null;
  warnings: string[];
}

export interface PaperIngestPayload {
  form_id: string;
  enumerator_id: string;
  answers: Record<string, any>;
  omr_confidence: number;
  scan_image_url?: string;
  manual_corrections?: {
    question_id: string;
    original: any;
    corrected: any;
    reason: string;
  }[];
}

// --- Enumerator Analytics Types ---
export interface EnumeratorMetrics {
  enumerator_id: string;
  total_responses: number;
  online_count: number;
  paper_count: number;
  avg_duration_seconds: number;
  avg_risk_score: number;
  high_risk_count: number;
  high_risk_rate: number;
  variance_z_score: number;
  is_anomaly: boolean;
  anomaly_reasons: string[];
}

export interface EnumeratorAnalytics {
  survey_id: string;
  total_enumerators: number;
  total_field_responses: number;
  enumerators: EnumeratorMetrics[];
}

export interface QuestionStats {
  question_id: string;
  question_title: string;
  question_type: QuestionType;
  total_answers: number;
  option_distribution?: Record<string, number> | null;
  stats_summary?: {
    min?: number;
    max?: number;
    avg?: number;
    count?: number;
    matrix_distribution?: Record<string, Record<string, number>>;
    ranking_averages?: Record<string, number>;
  } | null;
  recent_text_samples?: string[] | null;
}

export interface SurveyAnalytics {
  survey_id: string;
  survey_title: string;
  total_responses: number;
  is_sample_size_sufficient: boolean;
  sample_size_notice?: string | null;
  avg_duration_seconds: number;
  risk_distribution: Record<string, number>;
  review_distribution: Record<string, number>;
  questions_analytics: QuestionStats[];
}

export interface QualityAuditReport {
  survey_id: string;
  survey_title: string;
  survey_status: string;
  generated_at: string;
  total_collected: number;
  source_breakdown: Record<string, number>;
  verified_clean_count: number;
  data_trust_index: number;
  risk_breakdown: Record<string, number>;
  review_breakdown: Record<string, number>;
  fraud_signals: {
    speeding: number;
    straightlining: number;
    duplicate: number;
    logic_violation: number;
    gibberish_text: number;
    enumerator_anomaly: number;
  };
  compliance_statement: {
    law_name: string;
    principles_applied: {
      principle: string;
      description: string;
    }[];
    compliance_status: string;
  };
  methodology_citations: string[];
  audit_hash: string;
}
