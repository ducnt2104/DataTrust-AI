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
