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
  settings?: Record<string, any>;
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
  orientation_corrected?: number;
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
export interface GPSPoint {
  response_id: string;
  lat: number;
  lon: number;
  submitted_at: string;
  risk_score: number;
  speed_to_next_kmh?: number | null;
  is_speed_anomaly?: boolean;
  is_geofence_breach?: boolean;
  distance_from_center_km?: number;
}

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
  gps_coverage_rate?: number;
  impossible_speed_detected?: boolean;
  max_speed_kmh?: number | null;
  stationary_cluster_detected?: boolean;
  radius_of_gyration_km?: number | null;
  spatial_coverage_sqkm?: number | null;
  geofence_breach_count?: number;
  gps_points?: GPSPoint[];
}

export interface EnumeratorAnalytics {
  survey_id: string;
  total_enumerators: number;
  total_field_responses: number;
  geofence_setting?: {
    enabled?: boolean;
    target_lat?: number;
    target_lon?: number;
    max_radius_km?: number;
    location_name?: string;
  } | null;
  enumerators: EnumeratorMetrics[];
}

export interface QuestionStats {
  question_id: string;
  question_title: string;
  question_type: QuestionType;
  total_answers: number;
  completion_rate?: number | null;
  drop_off_rate?: number | null;
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
  overall_completion_rate?: number | null;
  funnel_analytics?: {
    step: number;
    question_id: string;
    question_title: string;
    question_type: string;
    total_answers: number;
    completion_rate_pct: number;
    drop_off_pct: number;
  }[] | null;
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
  cronbach_alpha?: number | null;
  ledger_head_hash?: string | null;
  is_ledger_valid?: boolean;
}

// --- Tamper-Evident SHA-256 Audit Trail Types ---
export interface AuditLogEntry {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  details_json: string;
  details?: Record<string, any>;
  created_at: string;
  prev_hash: string;
  entry_hash: string;
  is_valid_hash: boolean;
}

export interface AuditTrail {
  survey_id: string;
  is_chain_valid: boolean;
  chain_status: 'VALID' | 'TAMPERED' | 'EMPTY';
  total_records: number;
  genesis_hash?: string;
  head_hash?: string;
  tampered_at_index?: number;
  tampered_record_id?: string;
  verification_message: string;
  verified_at: string;
  events: AuditLogEntry[];
}

// --- AI Survey Engine Types ---
export interface AIGenerateSurveyOptions {
  topic: string;
  audience?: string;
  research_objectives?: string;
  expected_time_minutes?: number;
  preferred_question_types?: string[];
  target_question_count?: number;
  language?: string;
  strict_scientific_mode?: boolean;
}

export interface AIGenerationMetadata {
  session_id: string;
  status: string;
  provider: string;
  model_used: string;
  validation: {
    is_valid: boolean;
    coverage_score: number;
    adherence_score: number;
    objectivity_score: number;
    issues: any[];
    repaired: boolean;
    repair_attempts: number;
  };
  duration_ms: number;
  error_detail?: string;
}

export interface AIAuditIssue {
  question_id?: string;
  question_title?: string;
  issue_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  explanation: string;
  suggestion: string;
  auto_fix_title?: string;
}

export interface AIAuditResponse {
  audit_id?: string;
  total_questions: number;
  total_issues: number;
  scientific_readiness: 'READY' | 'WARNINGS_PRESENT' | 'CRITICAL_ISSUES';
  issues: AIAuditIssue[];
}

export interface AIStatus {
  ai_active: boolean;
  provider_available: string;
  configured_model: string;
  fallback_model: string;
  security_mode: string;
  supported_question_types_count: number;
  description: string;
}

export interface AIQualitativeAnalysis {
  total_analyzed: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  key_themes: {
    theme_name: string;
    sentiment: string;
    prevalence_percent: number;
    sample_quotes: string[];
  }[];
  anomaly_flags: string[];
  methodology_summary: string;
}

export interface CodebookVariable {
  variable_name: string;
  question_id: string;
  variable_label: string;
  question_type: string;
  measurement_level: string;
  is_required: boolean;
  value_labels: Record<string, string>;
  missing_values: Record<string, string>;
}

export interface CodebookData {
  survey_id: string;
  title: string;
  variables_count: number;
  variables: CodebookVariable[];
  spss_syntax: string;
  r_script: string;
  stata_syntax: string;
  sas_syntax?: string;
}

// --- Adversarial Red-Team Security Simulation Types ---
export interface AttackDefenseItem {
  id: string;
  name: string;
  category: string;
  threat_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  payload_sample: string;
  result: 'DEFENDED' | 'VULNERABLE';
  defense_layer: string;
  latency_ms: number;
  technical_detail: string;
}

export interface RedTeamSimulationResult {
  survey_id: string;
  timestamp: string;
  overall_status: 'SECURE' | 'VULNERABLE';
  compliance_score: number;
  attacks_tested: number;
  attacks_deflected: number;
  total_duration_ms: number;
  standards_verified: string[];
  attack_results: AttackDefenseItem[];
}

// --- Cross-Tabulation & Chi-Square Heatmap Types ---
export interface CrosstabCell {
  observed: number;
  expected: number;
  row_percentage: number;
  column_percentage: number;
  total_percentage: number;
  pearson_residual?: number;
}

export interface CrosstabAnalysisResult {
  total_valid_samples: number;
  is_sample_sufficient: boolean;
  notice?: string | null;
  variable_row: {
    question_id: string;
    title: string;
    categories: string[];
    totals: Record<string, number>;
  };
  variable_col: {
    question_id: string;
    title: string;
    categories: string[];
    totals: Record<string, number>;
  };
  row_categories: string[];
  col_categories: string[];
  matrix: Record<string, Record<string, CrosstabCell>>;
  chi_square_statistic: number;
  degrees_of_freedom: number;
  p_value: number;
  cramers_v: number;
  association_strength: string;
  is_statistically_significant: boolean;
  interpretation: string;
}

// --- Psychometric Scale Reliability Types ---
export interface ScaleItemStatistic {
  item_index: number;
  item_id: string;
  item_title: string;
  item_mean: number;
  item_variance: number;
  item_std_dev: number;
  scale_mean_if_deleted: number;
  scale_variance_if_deleted: number;
  corrected_item_total_correlation: number;
  alpha_if_item_deleted: number | null;
  status: 'GOOD' | 'ACCEPTABLE' | 'CONSIDER_REVISE';
  recommendation: string;
}

export interface ScaleReliabilityResult {
  survey_id: string;
  scope: string;
  is_sufficient: boolean;
  notice?: string | null;
  cronbach_alpha: number | null;
  standardized_alpha: number | null;
  n_samples: number;
  k_items: number;
  scale_mean: number;
  scale_variance: number;
  scale_std_dev: number;
  academic_rating: string;
  interpretation: string;
  item_statistics: ScaleItemStatistic[];
}

export interface PublicCertificateVerification {
  query: string;
  is_valid: boolean;
  status: 'VERIFIED_VALID' | 'TAMPERED' | 'NOT_FOUND';
  certificate_id: string;
  survey_id: string;
  survey_title: string;
  survey_description?: string | null;
  public_slug?: string | null;
  issued_at: string;
  total_responses: number;
  clean_responses: number;
  excluded_responses: number;
  trust_index: number;
  cronbach_alpha?: number | null;
  reliability_verdict?: string | null;
  ledger_chain_valid: boolean;
  ledger_head_hash?: string | null;
  ledger_genesis_hash?: string | null;
  total_audit_events: number;
  verification_verdict: string;
  compliance_standards: string[];
  printable_certificate_url: string;
}

export interface LongitudinalItemComparison {
  question_id_1?: string | null;
  question_id_2?: string | null;
  title: string;
  question_type: string;
  is_scale: boolean;
  n_wave1: number;
  n_wave2: number;
  mean_wave1?: number | null;
  mean_wave2?: number | null;
  std_wave1?: number | null;
  std_wave2?: number | null;
  mean_shift?: number | null;
  percent_change?: number | null;
  cohens_d?: number | null;
  effect_size: string;
  t_statistic?: number | null;
  degrees_of_freedom?: number | null;
  p_value?: number | null;
  is_statistically_significant: boolean;
  significance_label: string;
  trend_direction: 'INCREASED' | 'DECREASED' | 'STABLE' | 'SHIFTED';
  category_shifts?: Array<{
    option: string;
    count_wave1: number;
    pct_wave1: number;
    count_wave2: number;
    pct_wave2: number;
    delta_pct: number;
  }> | null;
  apa_summary: string;
}

export interface LongitudinalWaveComparisonResult {
  wave1_survey: {
    survey_id: string;
    title: string;
    version: number;
    total_responses: number;
    trust_index: number;
    avg_duration: number;
  };
  wave2_survey: {
    survey_id: string;
    title: string;
    version: number;
    total_responses: number;
    trust_index: number;
    avg_duration: number;
  };
  matched_questions_count: number;
  overall_scale_mean_wave1?: number | null;
  overall_scale_mean_wave2?: number | null;
  overall_scale_delta?: number | null;
  items_increased_count: number;
  items_decreased_count: number;
  items_stable_count: number;
  comparative_summary: string;
  items: LongitudinalItemComparison[];
}

export interface StressTestReport {
  status: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  concurrency_workers: number;
  total_time_seconds: number;
  throughput_rps: number;
  latency_mean_ms: number;
  latency_median_p50_ms: number;
  latency_p90_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  latency_min_ms: number;
  latency_max_ms: number;
  database_lock_errors: number;
  audit_chain_valid_post_stress: boolean;
  audit_chain_head_hash?: string | null;
  wal_size_bytes_after: number;
}

// --- Sampling Quotas & Demographic Raking Types ---
export interface SamplingQuotaRule {
  id?: string;
  name: string;
  question_id: string;
  target_value: string;
  max_target: number;
  action?: 'flag_overflow' | 'screen_out';
}

export interface SamplingQuotaCellProgress {
  cell_id: string;
  name: string;
  question_id: string;
  target_value: string;
  max_target: number;
  achieved_count: number;
  remaining_count: number;
  completion_pct: number;
  status: 'open' | 'almost_full' | 'filled';
  action: 'flag_overflow' | 'screen_out';
}

export interface SamplingQuotaReport {
  survey_id: string;
  total_quota_cells: number;
  filled_cells: number;
  open_cells: number;
  overall_target_sum: number;
  overall_achieved_sum: number;
  overall_completion_pct: number;
  cells: SamplingQuotaCellProgress[];
}

export interface RakingMarginalCategory {
  category: string;
  unweighted_count: number;
  unweighted_pct: number;
  target_benchmark_pct: number;
  weighted_pct: number;
  absolute_bias_reduction_pct: number;
}

export interface RakingMarginalComparison {
  variable: string;
  categories: RakingMarginalCategory[];
}

export interface DemographicRakingResult {
  survey_id: string;
  converged: boolean;
  iterations: number;
  max_discrepancy: number;
  sample_size: number;
  design_effect_deff: number;
  effective_sample_size_neff: number;
  statistical_efficiency_pct: number;
  weight_stats: {
    min: number;
    max: number;
    mean: number;
    std: number;
    trim_bounds: [number, number];
  };
  marginal_comparisons: RakingMarginalComparison[];
  summary: string;
}

export interface DemographicRakingRequest {
  target_margins: Record<string, Record<string, number>>;
  scope?: 'verified_clean' | 'all';
  max_iterations?: number;
  convergence_tol?: number;
  trim_min?: number;
  trim_max?: number;
}

// --- Differential Item Functioning (DIF) Types ---
export interface DIFItemResult {
  question_id: string;
  question_title: string;
  median_threshold: number;
  active_strata_count: number;
  chi2_mh: number;
  p_value: number;
  alpha_odds_ratio: number;
  delta_ets: number;
  abs_delta_ets: number;
  ets_class: 'A' | 'B' | 'C';
  ets_label: string;
  favored_group: string;
  action_recommendation: string;
  is_statistically_significant: boolean;
}

export interface DIFReport {
  survey_id: string;
  grouping_variable_id: string;
  grouping_variable_title: string;
  reference_group: string;
  focal_group: string;
  sample_reference: number;
  sample_focal: number;
  total_eval_sample: number;
  strata_count: number;
  class_a_count: number;
  class_b_count: number;
  class_c_count: number;
  overall_verdict: string;
  summary: string;
  items: DIFItemResult[];
}

export interface QuestionPacingAnalysis {
  id: string;
  order_index: number;
  title: string;
  question_type: string;
  title_words: number;
  options_word_count: number;
  total_words: number;
  num_options: number;
  expected_reading_seconds: number;
  cognitive_burden_score: number;
  burden_tier: 'Low' | 'Moderate' | 'High' | 'Critical';
  risk_factors: string[];
  redesign_recommendation: string;
}

export interface SurveyPacingReport {
  survey_level: {
    survey_title: string;
    total_questions: number;
    total_survey_words: number;
    expected_reading_seconds: number;
    expected_reading_minutes: number;
    actual_sample_size: number;
    actual_median_seconds: number;
    actual_mean_seconds: number;
    overall_pacing_ratio: number;
    engagement_level: string;
    engagement_desc: string;
    respondent_pacing_distribution: {
      severe_speeding: number;
      rushed: number;
      optimal: number;
      deliberate: number;
    };
    average_question_burden: number;
    high_burden_questions_count: number;
    fatigue_slope: number;
    fatigue_risk: boolean;
    fatigue_note: string;
    apa_interpretation: string;
  };
  question_analyses: QuestionPacingAnalysis[];
}

export interface MultivariateOutlierItem {
  response_id: string;
  d2_mahalanobis: number;
  distance_d: number;
  p_value: number;
  degrees_of_freedom: number;
  is_outlier: boolean;
  outlier_tier: 'Extreme Anomaly' | 'Moderate Outlier' | 'Normal Multivariate Range';
  duration_seconds: number;
  risk_score: number;
  review_status: string;
  answers_vector: number[];
}

export interface MultivariateOutlierReport {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'INSUFFICIENT_VARIABLES' | 'SINGULAR_MATRIX';
  message?: string;
  sample_size?: number;
  degrees_of_freedom?: number;
  scale_variables_count?: number;
  scale_variable_ids?: string[];
  scale_variable_titles?: string[];
  mean_d2?: number;
  median_d2?: number;
  max_d2?: number;
  critical_chi2_001?: number;
  total_outliers_count?: number;
  extreme_outliers_count?: number;
  moderate_outliers_count?: number;
  outlier_rate_pct?: number;
  apa_interpretation?: string;
  outliers_summary?: MultivariateOutlierItem[];
  all_records_count?: number;
}

export interface EFAEigenvalueStat {
  factor_index: number;
  eigenvalue: number;
  variance_pct: number;
  cumulative_variance_pct: number;
  retained_kaiser: boolean;
}

export interface EFAScreePlotPoint {
  factor: number;
  eigenvalue: number;
  threshold: number;
}

export interface EFARotatedVariance {
  factor_name: string;
  factor_index: number;
  ss_loadings: number;
  variance_pct: number;
}

export interface EFAItemResult {
  question_id: string;
  question_title?: string;
  order_index?: number;
  msa_index: number;
  communality: number;
  factor_loadings: number[];
  primary_factor: string;
  primary_factor_index: number;
  max_loading: number;
  is_acceptable: boolean;
}

export interface EFAReport {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'INSUFFICIENT_VARIABLES' | 'ERROR';
  message?: string;
  sample_size?: number;
  variables_count?: number;
  variable_ids?: string[];
  scale_variable_titles?: string[];
  kmo_overall?: number;
  kmo_verdict?: string;
  is_kmo_acceptable?: boolean;
  bartlett_chi2?: number;
  bartlett_df?: number;
  bartlett_p_value?: number;
  is_bartlett_significant?: boolean;
  factors_extracted_count?: number;
  rotation_method?: string;
  cumulative_variance_extracted_pct?: number;
  is_variance_sufficient?: boolean;
  eigenvalue_stats?: EFAEigenvalueStat[];
  scree_plot_data?: EFAScreePlotPoint[];
  factors?: string[];
  rotated_factor_variance?: EFARotatedVariance[];
  items?: EFAItemResult[];
  weak_loadings_count?: number;
  low_communalities_count?: number;
  correlation_matrix?: number[][];
  apa_interpretation?: string;
}

export interface TTestGroupStats {
  label: string;
  n: number;
  mean: number;
  var: number;
  sd: number;
  se: number;
  median: number;
  skew: number;
  kurt: number;
}

export interface IndependentTTestReport {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  test_type: 'independent';
  test_method: string;
  variable_label: string;
  group1: TTestGroupStats;
  group2: TTestGroupStats;
  mean_difference: number;
  std_error_difference: number;
  ci_95_lower: number;
  ci_95_upper: number;
  levene_test: {
    f_stat: number;
    df1: number;
    df2: number;
    p_value: number;
    equal_variances_assumed: boolean;
  };
  primary_test: {
    t_stat: number;
    df: number;
    p_value: number;
    is_significant_05: boolean;
    is_significant_01: boolean;
  };
  student_test: {
    t_stat: number;
    df: number;
    p_value: number;
    se: number;
  };
  welch_test: {
    t_stat: number;
    df: number;
    p_value: number;
    se: number;
  };
  effect_size: {
    cohen_d: number;
    hedges_g: number;
    magnitude: string;
  };
  apa_interpretation: string;
}

export interface PairedTTestReport {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  test_type: 'paired';
  test_method: string;
  sample_size: number;
  mean_difference: number;
  variable1: TTestGroupStats;
  variable2: TTestGroupStats;
  difference: TTestGroupStats;
  pearson_r: number;
  t_stat: number;
  degrees_of_freedom: number;
  p_value: number;
  is_significant_05: boolean;
  is_significant_01: boolean;
  ci_95_lower: number;
  ci_95_upper: number;
  effect_size: {
    cohen_d: number;
    hedges_g: number;
    magnitude: string;
  };
  apa_interpretation: string;
}

// --- One-Way ANOVA & Tukey HSD Types ---
export interface ANOVAGroupStat {
  group_name: string;
  n: number;
  mean: number;
  std: number;
  median: number;
  std_error: number;
  ci_95_lower: number;
  ci_95_upper: number;
}

export interface ANOVATable {
  ss_between: number;
  df_between: number;
  ms_between: number;
  ss_within: number;
  df_within: number;
  ms_within: number;
  ss_total: number;
  df_total: number;
  f_stat: number;
  p_value: number;
  is_significant_05: boolean;
  is_significant_01: boolean;
}

export interface ANOVATukeyPair {
  comparison: string;
  group1: string;
  group2: string;
  mean1: number;
  mean2: number;
  mean_difference: number;
  std_error: number;
  q_stat: number;
  q_critical_05: number;
  is_significant: boolean;
  ci_95_lower: number;
  ci_95_upper: number;
}

export interface OneWayANOVAReport {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  grouping_label: string;
  variable_label: string;
  total_sample_size: number;
  groups_count: number;
  grand_mean: number;
  group_statistics: ANOVAGroupStat[];
  levene_test: {
    f_stat: number;
    df1: number;
    df2: number;
    p_value: number;
    equal_variances_assumed: boolean;
  };
  anova_table: ANOVATable;
  effect_size: {
    eta_squared: number;
    omega_squared: number;
    magnitude: string;
  };
  post_hoc_tukey: ANOVATukeyPair[];
  apa_interpretation: string;
}

// --- Bivariate Correlation Matrix Types ---
export interface CorrelationVariableSummary {
  id: string;
  title: string;
  label: string;
  n: number;
  mean: number;
  std: number;
}

export interface CorrelationMatrixCell {
  var1_id: string;
  var2_id: string;
  correlation: number;
  p_value: number;
  is_significant_05: boolean;
  is_significant_01: boolean;
  is_significant_001: boolean;
  ci_95_lower: number;
  ci_95_upper: number;
  strength: string;
  direction: string;
}

export interface CorrelationPairSummary {
  var1_id: string;
  var1_title: string;
  var2_id: string;
  var2_title: string;
  correlation: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  strength: string;
  direction: string;
  n: number;
  warning?: string;
}

export interface CorrelationMatrixReport {
  status: 'SUCCESS' | 'INSUFFICIENT_VARIABLES' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  method: 'pearson' | 'spearman';
  variables_count: number;
  total_pairs_count: number;
  significant_pairs_count: number;
  variables: CorrelationVariableSummary[];
  matrix: CorrelationMatrixCell[][];
  high_correlations: CorrelationPairSummary[];
  multicollinearity_warnings: CorrelationPairSummary[];
  apa_interpretation: string;
}

// --- Multiple Linear Regression OLS Types ---
export interface RegressionCoefficient {
  term: string;
  label: string;
  title: string;
  b_unstandardized: number;
  std_error: number;
  beta_standardized: number;
  t_stat: number;
  p_value: number;
  is_significant_05: boolean;
  is_significant_01: boolean;
  ci_95_lower: number;
  ci_95_upper: number;
  tolerance: number;
  vif: number;
}

export interface RegressionModelSummary {
  r_squared: number;
  r_squared_adjusted: number;
  std_error_of_estimate: number;
  f_stat: number;
  df_regression: number;
  df_residual: number;
  df_total: number;
  p_value: number;
  is_significant_05: boolean;
  is_significant_01: boolean;
}

export interface RegressionANOVATable {
  ss_regression: number;
  df_regression: number;
  ms_regression: number;
  ss_residual: number;
  df_residual: number;
  ms_residual: number;
  ss_total: number;
  df_total: number;
  f_stat: number;
  p_value: number;
}

export interface LinearRegressionReport {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'SINGULAR_MATRIX' | 'ERROR';
  message?: string;
  sample_size: number;
  predictors_count: number;
  dependent_title: string;
  model_summary: RegressionModelSummary;
  anova_table: RegressionANOVATable;
  coefficients: RegressionCoefficient[];
  max_vif: number;
  multicollinearity_risk: 'LOW' | 'MODERATE' | 'HIGH';
  apa_interpretation: string;
}

// --- Survey Logic & Branching DAG Simulation ---
export interface LogicIssue {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'INFO';
  type: 'CYCLE' | 'ORDER_INVERSION' | 'DANGLING_REF' | 'UNREACHABLE' | 'CONTRADICTION';
  title: string;
  question_id: string;
  question_title: string;
  description: string;
  recommendation: string;
  cycle_path?: string[];
}

export interface LogicTopology {
  node_count: number;
  edge_count: number;
  cyclomatic_complexity: number;
  branch_points_count: number;
  branch_points: string[];
  unreachable_count: number;
  all_paths_count: number;
}

export interface LogicNode {
  id: string;
  order_index: number;
  title: string;
  question_type: string;
  is_required: boolean;
  rule_count: number;
  status: 'normal' | 'cycle' | 'unreachable' | 'inversion';
  rules: any[];
}

export interface LogicEdge {
  source: string;
  target: string;
  type: 'sequential' | 'conditional' | 'jump';
  action?: string;
  label: string;
  condition?: any;
}

export interface LogicSamplePath {
  path_id: string;
  name: string;
  length: number;
  question_ids: string[];
  completion_percentage: number;
  description: string;
}

export interface SurveyLogicReport {
  survey_id: string;
  survey_title: string;
  is_valid: boolean;
  health_score: number;
  status: 'OPTIMAL' | 'WARNING' | 'CRITICAL';
  summary: string;
  issues: LogicIssue[];
  topology: LogicTopology;
  nodes: LogicNode[];
  edges: LogicEdge[];
  paths: LogicSamplePath[];
}

export interface SurveySimulationReport {
  survey_id: string;
  survey_title: string;
  total_questions: number;
  visible_count: number;
  hidden_count: number;
  visible_questions: string[];
  hidden_questions: string[];
  skipped_reasons: Record<string, string>;
  completion_ratio: number;
}

// --- Statistical Power Analysis & Sample Size Estimator ---
export interface SampleAdequacyEvaluation {
  current_n: number;
  status: 'ADEQUATE' | 'MODERATE' | 'UNDERPOWERED' | 'CRITICAL_INSUFFICIENT';
  rating: string;
  badge_color: 'emerald' | 'amber' | 'red';
  achieved_margin_of_error: number;
  achieved_margin_of_error_pct: string;
  ttest_power: {
    small_d_02: number;
    medium_d_05: number;
    large_d_08: number;
  };
  correlation_power: {
    small_r_01: number;
    medium_r_03: number;
    large_r_05: number;
  };
  minimum_n_required: {
    ttest_medium_80pct: number;
    ttest_large_80pct: number;
    correlation_medium_80pct: number;
  };
  summary: string;
  apa_narrative: string;
}

export interface CochranEstimation {
  formula: string;
  confidence_level: number;
  z_critical: number;
  margin_of_error: number;
  margin_of_error_pct: string;
  proportion: number;
  population_size?: number | null;
  unadjusted_sample_size: number;
  required_sample_size: number;
  fpc_applied: boolean;
  recommendation: string;
}

export interface PowerCurvePoint {
  n: number;
  n_per_group?: number;
  power: number;
  power_pct: number;
}

export interface PowerAnalysisReport {
  survey_id: string;
  survey_title: string;
  scope: string;
  current_sample_size: number;
  adequacy: SampleAdequacyEvaluation;
  cochran_estimation: CochranEstimation;
  power_curve: PowerCurvePoint[];
  parameters: {
    analysis_type: string;
    confidence_level: number;
    margin_of_error: number;
    population_size?: number | null;
    effect_size: number;
    target_power: number;
    alpha: number;
  };
}

export interface SplitBallotArmSummary {
  arm_id: string;
  label: string;
  total_responses: number;
  answered_count: number;
  response_rate_pct: number;
}

export interface SplitBallotNumericArmStats {
  count: number;
  mean: number;
  variance: number;
  std_dev: number;
  standard_error: number;
}

export interface SplitBallotNumericDetails {
  is_sufficient: boolean;
  message?: string;
  arm_a: SplitBallotNumericArmStats;
  arm_b: SplitBallotNumericArmStats;
  mean_difference: number;
  t_statistic: number;
  degrees_of_freedom: number;
  p_value: number;
  is_significant: boolean;
  cohens_d: number;
  confidence_interval_95: [number, number];
}

export interface SplitBallotCategoricalOption {
  option: string;
  count_a: number;
  prop_a: number;
  count_b: number;
  prop_b: number;
  difference_pct: number;
}

export interface SplitBallotCategoricalDetails {
  is_sufficient: boolean;
  message?: string;
  arm_a_total: number;
  arm_b_total: number;
  chi_square: number;
  degrees_of_freedom: number;
  p_value: number;
  is_significant: boolean;
  cramer_v: number;
  total_variation_distance: number;
  option_comparison: SplitBallotCategoricalOption[];
}

export interface SplitBallotComparison {
  comparison_type: 'numeric' | 'categorical';
  details: SplitBallotNumericDetails | SplitBallotCategoricalDetails | any;
}

export interface SplitBallotDistortionIndex {
  mwdi: number;
  level: 'FRAME_ROBUST' | 'MODERATELY_SENSITIVE' | 'HIGHLY_PLASTIC';
  badge_color: string;
  classification_title: string;
  scientific_interpretation: string;
  methodological_recommendation: string;
}

export interface SplitBallotReport {
  survey_id: string;
  survey_title: string;
  question_id: string;
  question_title: string;
  question_type: string;
  scope: string;
  total_responses: number;
  arms_count: number;
  arms_summary: SplitBallotArmSummary[];
  comparison: SplitBallotComparison;
  distortion_index: SplitBallotDistortionIndex;
  apa_narrative: string;
}

export interface RaschItemCalibration {
  question_id: string;
  order_index: number;
  item_code: string;
  title: string;
  question_type: string;
  difficulty_logit: number;
  standard_error: number;
  infit_mnsq: number;
  outfit_mnsq: number;
  fit_status: 'OPTIMAL_FIT' | 'UNDERFIT_NOISY' | 'OVERFIT_REDUNDANT';
  fit_badge: string;
  fit_label: string;
}

export interface RaschWrightMapBucket {
  logit_level: number;
  person_count: number;
  person_percent: number;
  items: string[];
}

export interface RaschModelReport {
  survey_id: string;
  survey_title: string;
  scope: string;
  sample_size: number;
  item_count: number;
  convergence: {
    converged: boolean;
    iterations: number;
  };
  reliability: {
    item_reliability: number;
    item_separation_index: number;
    person_reliability: number;
    person_mean_theta: number;
  };
  targeting: {
    targeting_gap_logit: number;
    targeting_evaluation: string;
    description: string;
  };
  item_calibrations: RaschItemCalibration[];
  wright_map: RaschWrightMapBucket[];
  apa_narrative: string;
}

export interface ClusterElbowPoint {
  k: number;
  wcss: number;
  silhouette_score: number;
}

export interface ClusterPersona {
  cluster_id: number;
  cluster_code: string;
  name: string;
  archetype_description: string;
  size: number;
  percentage: number;
  high_traits: string[];
  low_traits: string[];
}

export interface ClusterFeatureImportance {
  feature_index: number;
  feature_name: string;
  f_ratio: number;
  eta_squared: number;
  cluster_means: number[];
  grand_mean: number;
}

export interface ClusterAnalysisReport {
  survey_id: string;
  survey_title: string;
  scope: string;
  sample_size: number;
  features_count: number;
  features: { id: string; title: string }[];
  chosen_k: number;
  wcss: number;
  silhouette: {
    overall_score: number;
    cluster_scores: number[];
    quality_level: 'STRONG_CLUSTERING' | 'ACCEPTABLE_CLUSTERING' | 'WEAK_CLUSTERING';
    quality_badge: string;
    description: string;
  };
  elbow_curve: ClusterElbowPoint[];
  personas: ClusterPersona[];
  feature_importance: ClusterFeatureImportance[];
  apa_narrative: string;
}

// --- Pairwise Response Similarity & Collusion Ring Interfaces ---
export interface PairwiseMatchMetric {
  response_id_a: string;
  response_id_b: string;
  composite_similarity: number;
  closed_similarity: number;
  closed_matches: number;
  closed_valid_comparisons: number;
  open_similarity: number;
  same_device: boolean;
  same_ip: boolean;
  same_enumerator: boolean;
  time_delta_seconds?: number | null;
  rapid_succession: boolean;
  risk_category: 'IDENTICAL_DUPLICATE' | 'NEAR_DUPLICATE' | 'SUSPICIOUS_VARIANT' | 'NORMAL_VARIATION';
  is_collusion_syndicate: boolean;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  badge: string;
}

export interface CollusionRing {
  ring_id: string;
  member_count: number;
  response_ids: string[];
  mean_internal_similarity: number;
  shared_devices_count: number;
  has_shared_device: boolean;
  shared_ips_count: number;
  has_shared_ip: boolean;
  enumerators_involved: string[];
  time_span_seconds?: number | null;
  threat_level: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  recommended_action: string;
}

export interface SimilarityMatrixNode {
  index: number;
  id: string;
  short_id: string;
  review_status: string;
  quality_score: number;
  submitted_at: string;
  is_in_collusion_ring: boolean;
}

export interface PairwiseSimilarityAnalysisReport {
  survey_id: string;
  survey_title: string;
  scope: string;
  total_responses: number;
  matrix_size: number;
  threshold: number;
  high_risk_pairs: PairwiseMatchMetric[];
  collusion_rings: CollusionRing[];
  matrix_nodes: SimilarityMatrixNode[];
  similarity_matrix: number[][];
  summary: {
    total_responses: number;
    evaluated_pairs: number;
    high_risk_pairs_count: number;
    collusion_rings_count: number;
    collusion_nodes_count: number;
    highest_similarity: number;
    average_similarity: number;
    data_integrity_index: number;
    status: string;
  };
  academic_narrative: string;
}

// --- Geographic Spatial Clustering & Geo-Fencing Interfaces ---
export interface SpatialCluster {
  cluster_id: string;
  center_lat: number;
  center_lon: number;
  radius_meters: number;
  member_count: number;
  response_ids: string[];
  enumerators_involved: string[];
  devices_involved: string[];
  time_span_seconds: number;
  is_suspicious_coffee_shop: boolean;
  threat_level: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  recommended_action: string;
}

export interface SpeedAnomaly {
  actor_id: string;
  response_id_from: string;
  response_id_to: string;
  from_lat: number;
  from_lon: number;
  to_lat: number;
  to_lon: number;
  distance_km: number;
  time_delta_seconds: number;
  speed_kmh: number;
  max_allowed_speed_kmh: number;
  threat_level: 'CRITICAL' | 'HIGH';
  message: string;
}

export interface GeofenceBreach {
  response_id: string;
  lat: number;
  lon: number;
  submitted_at: string;
  excess_distance_meters: number;
  enumerator_id?: string;
  severity: 'HIGH' | 'MEDIUM';
}

export interface SpatialDispersion {
  total_gps_points: number;
  center_lat: number;
  center_lon: number;
  standard_distance_meters: number;
  standard_distance_km: number;
  bounding_box?: {
    min_lat: number;
    max_lat: number;
    min_lon: number;
    max_lon: number;
  } | null;
  territory_spread: string;
}

export interface SpatialGpsPoint {
  id: string;
  lat: number;
  lon: number;
  enumerator_id: string;
  device_id: string;
  submitted_at: string;
  review_status: string;
  quality_score: number;
  is_clustered: boolean;
}

export interface SpatialAnalysisReport {
  survey_id: string;
  survey_title: string;
  scope: string;
  total_responses: number;
  total_gps_points: number;
  gps_coverage_pct: number;
  eps_meters: number;
  min_samples: number;
  max_speed_kmh: number;
  has_geofence_polygon: boolean;
  clusters: SpatialCluster[];
  speed_anomalies: SpeedAnomaly[];
  geofence_breaches: GeofenceBreach[];
  dispersion: SpatialDispersion;
  gps_points: SpatialGpsPoint[];
  summary: {
    total_responses: number;
    total_gps_points: number;
    clusters_count: number;
    suspicious_nodes_count: number;
    speed_anomalies_count: number;
    geofence_breaches_count: number;
    spatial_integrity_index: number;
    status: string;
  };
  academic_narrative: string;
}

export interface CleansingCriteria {
  exclude_speeders: boolean;
  speeder_min_seconds: number;
  exclude_straightlining: boolean;
  straightlining_threshold: number;
  exclude_logic_contradictions: boolean;
  exclude_high_risk: boolean;
  min_omr_confidence: number;
  exclude_unverified_enumerator: boolean;
  exclude_collusion_syndicates?: boolean;
  exclude_coffee_shop_congregations?: boolean;
  exclude_impossible_travel?: boolean;
  exclude_geofence_violations?: boolean;
}

export interface CleansingReport {
  survey_id: string;
  total_responses: number;
  clean_responses_count: number;
  clean_percentage: number;
  flagged_speeders: number;
  flagged_straightlining: number;
  flagged_contradictions: number;
  flagged_high_risk: number;
  flagged_low_omr: number;
  overlap_count: number;
  pre_avg_duration: number;
  post_avg_duration: number;
  pre_avg_risk: number;
  post_avg_risk: number;
  cronbach_alpha_pre?: number | null;
  cronbach_alpha_post?: number | null;
  applied_criteria: CleansingCriteria;
  flagged_collusion_syndicates?: number;
  flagged_coffee_shop?: number;
  flagged_impossible_travel?: number;
  flagged_geofence_violations?: number;
}

export interface BatchAnomalyQuarantineRequest {
  quarantine_syndicates?: boolean;
  quarantine_coffee_shop?: boolean;
  quarantine_impossible_velocity?: boolean;
  quarantine_geofence_violations?: boolean;
  quarantine_speeders?: boolean;
  quarantine_straightlining?: boolean;
  min_risk_score?: number | null;
  action?: 'verified_fraud' | 'quarantined';
  custom_note?: string | null;
  dry_run?: boolean;
}

export interface BatchAnomalyQuarantineItem {
  response_id: string;
  enumerator_id?: string | null;
  duration_seconds: number;
  risk_score: number;
  reasons: string[];
  previous_status: string;
  new_status: string;
}

export interface BatchAnomalyQuarantineResult {
  success: boolean;
  survey_id: string;
  dry_run: boolean;
  total_evaluated: number;
  quarantined_count: number;
  reasons_breakdown: Record<string, number>;
  items: BatchAnomalyQuarantineItem[];
  audit_log_id?: string | null;
  timestamp: string;
}

export interface BatchRestoreQuarantineRequest {
  response_ids?: string[] | null;
  restore_to_status?: string;
  reason?: string;
}

export interface BatchRestoreQuarantineResult {
  success: boolean;
  survey_id: string;
  restored_count: number;
  restored_ids: string[];
  audit_log_id: string;
  timestamp: string;
}

// --- Survey Cognitive Pre-Testing & Ambiguity Diagnostics Interfaces ---
export interface CognitiveIssue {
  question_id: string;
  question_order: number;
  question_title: string;
  issue_type: 'LEADING_QUESTION' | 'DOUBLE_BARRELED' | 'DOUBLE_NEGATIVE' | 'VAGUE_QUANTIFIER' | 'COGNITIVE_OVERLOAD' | 'INSUFFICIENT_OPTIONS' | 'SENSITIVE_UNPROTECTED';
  severity: 'CRITICAL' | 'WARNING' | 'SUGGESTION';
  cognitive_dimension: string;
  explanation: string;
  academic_rule: string;
  auto_fix_title?: string | null;
  suggested_options?: Array<{ id: string; label: string }> | null;
}

export interface PersonaSimulationResult {
  persona_id: string;
  persona_name: string;
  persona_demographic: string;
  cognitive_style: string;
  overall_difficulty_rating: 'SMOOTH' | 'ACCEPTABLE' | 'CHALLENGING' | 'DROPOUT_RISK';
  predicted_completion_time_sec: number;
  predicted_dropout_probability: number;
  bottleneck_question_ids: string[];
  qualitative_feedback: string;
}

export interface CognitiveFatiguePoint {
  question_index: number;
  question_id: string;
  question_title: string;
  cumulative_time_seconds: number;
  fatigue_percentage: number;
  dropout_risk_percentage: number;
}

export interface CognitivePretestReport {
  survey_id?: string | null;
  survey_title: string;
  total_questions: number;
  total_words: number;
  readability_score: number;
  readability_level: 'EASY' | 'MODERATE' | 'DIFFICULT';
  estimated_duration_minutes: number;
  design_quality_score: number;
  academic_grade: 'A+' | 'A' | 'B' | 'C';
  total_issues_count: number;
  critical_issues_count: number;
  warning_issues_count: number;
  issues: CognitiveIssue[];
  personas: PersonaSimulationResult[];
  fatigue_curve: CognitiveFatiguePoint[];
  methodological_summary: string;
  timestamp: string;
}

// --- Statistical Mediation & Path Analysis Types ---
export interface MediationAnalysisRequest {
  x_question_id: string;
  m_question_id: string;
  y_question_id: string;
  scope?: 'all' | 'verified_clean';
  bootstrap_samples?: number;
}

export interface MediationPathInfo {
  id: string;
  source: string;
  target: string;
  coeff: number;
  std_beta: number;
  se: number;
  p_value: number;
  stars: string;
  is_significant: boolean;
  label: string;
}

export interface MediationStep {
  step: number;
  title: string;
  formula: string;
  r_squared: number;
  f_stat?: number;
  f_p_value?: number;
  coefficient?: number;
  std_beta?: number;
  se?: number;
  t_stat?: number;
  p_value?: number;
  ci_95?: [number, number];
  is_significant?: boolean;
  delta_r_squared?: number;
  path_c_prime?: {
    coefficient: number;
    std_beta: number;
    se: number;
    t_stat: number;
    p_value: number;
    is_significant: boolean;
  };
  path_b?: {
    coefficient: number;
    std_beta: number;
    se: number;
    t_stat: number;
    p_value: number;
    is_significant: boolean;
  };
}

export interface MediationEffectsSummary {
  total_effect_c: number;
  direct_effect_c_prime: number;
  indirect_effect_ab: number;
  std_indirect_effect_ab: number;
  indirect_to_direct_ratio?: number | null;
  vaf_percent: number;
}

export interface MediationSignificanceTests {
  sobel_test: {
    z_stat: number;
    p_value: number;
    is_significant: boolean;
  };
  aroian_test: {
    z_stat: number;
    p_value: number;
    is_significant: boolean;
  };
  goodman_test: {
    z_stat: number;
    p_value: number;
    is_significant: boolean;
  };
  bootstrap_resampling: {
    bootstrap_samples: number;
    indirect_mean: number;
    se_boot: number;
    ci_lower: number;
    ci_upper: number;
    is_significant: boolean;
  };
}

export interface MediationConclusion {
  mediation_type: 'FULL_MEDIATION' | 'COMPLEMENTARY_PARTIAL_MEDIATION' | 'COMPETITIVE_PARTIAL_MEDIATION' | 'DIRECT_ONLY' | 'NO_EFFECT' | 'INCONCLUSIVE';
  mediation_label_vn: string;
  description: string;
  apa_narrative: string;
}

export interface MediationDiagram {
  nodes: Array<{
    id: string;
    label: string;
    role: 'predictor' | 'mediator' | 'outcome';
    x: number;
    y: number;
  }>;
  paths: MediationPathInfo[];
}

export interface MediationAnalysisResult {
  status: 'OK' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  sample_size?: number;
  variables?: {
    x: { label: string };
    m: { label: string };
    y: { label: string };
  };
  steps?: MediationStep[];
  effects_summary?: MediationEffectsSummary;
  significance_tests?: MediationSignificanceTests;
  conclusion?: MediationConclusion;
  diagram?: MediationDiagram;
}

// --- Non-Parametric Hypothesis Testing Types ---
export interface MannWhitneyURequest {
  target_question_id: string;
  grouping_question_id: string;
  group1_value?: string;
  group2_value?: string;
  scope?: 'all' | 'verified_clean';
}

export interface NonParametricDescriptives {
  n: number;
  mean: number;
  std: number;
  median: number;
  q1: number;
  q3: number;
  iqr: number;
  min: number;
  max: number;
}

export interface MannWhitneyUResult {
  status: 'OK' | 'INSUFFICIENT_DATA' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  test_type?: 'MANN_WHITNEY_U';
  total_sample_size?: number;
  groups?: {
    group1: {
      name: string;
      rank_sum: number;
      mean_rank: number;
      descriptives: NonParametricDescriptives;
    };
    group2: {
      name: string;
      rank_sum: number;
      mean_rank: number;
      descriptives: NonParametricDescriptives;
    };
  };
  statistics?: {
    u_statistic: number;
    u1: number;
    u2: number;
    expected_mean_u: number;
    std_error_u: number;
    z_statistic: number;
    p_value: number;
    is_significant: boolean;
    ties_count: number;
  };
  effect_size?: {
    rosenthal_r: number;
    rosenthal_magnitude: string;
    rank_biserial_correlation: number;
    common_language_effect_size_pct: number;
  };
  conclusion?: {
    higher_group: string;
    is_significant: boolean;
    apa_narrative: string;
  };
}

export interface WilcoxonSignedRankRequest {
  question_id_1: string;
  question_id_2: string;
  scope?: 'all' | 'verified_clean';
}

export interface WilcoxonSignedRankResult {
  status: 'OK' | 'INSUFFICIENT_DATA' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  test_type?: 'WILCOXON_SIGNED_RANK';
  total_pairs?: number;
  effective_pairs?: number;
  zero_differences_count?: number;
  samples?: {
    sample1: { name: string; descriptives: NonParametricDescriptives };
    sample2: { name: string; descriptives: NonParametricDescriptives };
    differences: NonParametricDescriptives;
  };
  statistics?: {
    w_statistic: number;
    w_plus: number;
    w_minus: number;
    expected_mean_w: number;
    std_error_w: number;
    z_statistic: number;
    p_value: number;
    is_significant: boolean;
    ties_count: number;
  };
  effect_size?: {
    rosenthal_r: number;
    rosenthal_magnitude: string;
    matched_pairs_rank_biserial: number;
  };
  conclusion?: {
    is_significant: boolean;
    apa_narrative: string;
  };
}

// --- Missing Data Pattern Diagnostics & Imputation Types ---
export interface MissingVariableSummary {
  variable: string;
  observed_count: number;
  missing_count: number;
  missing_pct: number;
  mean: number | null;
  std: number | null;
}

export interface MissingPatternItem {
  pattern_id: string;
  bitstring: string;
  case_count: number;
  percentage: number;
  observed_variables: string[];
  missing_variables: string[];
  is_complete: boolean;
}

export interface LittlesMCARTest {
  applicable: boolean;
  reason?: string;
  chi_square: number | null;
  df: number;
  p_value: number | null;
  is_mcar?: boolean;
  conclusion: string;
  apa_writeup?: string;
}

export interface MissingDataDiagnosticsResult {
  status: 'OK' | 'INSUFFICIENT_VARIABLES' | 'INSUFFICIENT_SAMPLE' | 'EMPTY_DATA' | 'ERROR';
  message?: string;
  sample_size?: number;
  variables_count?: number;
  complete_cases_count?: number;
  incomplete_cases_count?: number;
  complete_cases_pct?: number;
  total_cells?: number;
  total_missing_cells?: number;
  overall_missing_rate?: number;
  variables_summary?: MissingVariableSummary[];
  patterns?: MissingPatternItem[];
  patterns_count?: number;
  littles_mcar_test?: LittlesMCARTest;
}

export interface MissingImputationComparison {
  variable: string;
  missing_cells_imputed: number;
  original_mean: number;
  imputed_mean: number;
  mean_delta_pct: number;
  original_std: number;
  imputed_std: number;
  preservation_status: 'HIGH' | 'MODERATE' | 'DRIFT_ALERT';
}

export interface MissingDataImputationResult {
  status: 'OK' | 'NO_MISSING_DATA' | 'INSUFFICIENT_VARIABLES' | 'INSUFFICIENT_SAMPLE' | 'EMPTY_DATA' | 'ERROR';
  message?: string;
  method?: string;
  method_label?: string;
  sample_size?: number;
  variables_count?: number;
  imputed_cells_count?: number;
  imputed_cells_pct?: number;
  comparison?: MissingImputationComparison[];
  apa_writeup?: string;
  imputed_data_sample?: Array<Record<string, number>>;
}

// --- Scale Equating & Concordance Transformation Types ---
export interface ConcordanceRow {
  x_score: number;
  percentile_rank: number;
  linear_equivalent_raw: number;
  linear_equivalent: number;
  linear_equivalent_rounded: number;
  equipercentile_equivalent: number;
  equipercentile_rounded: number;
  t_score: number;
  stanine: number;
}

export interface ScaleEquatingResult {
  status: 'OK' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  x_label?: string;
  y_label?: string;
  sample_sizes?: { x_count: number; y_count: number };
  descriptive_statistics?: {
    x_scale: { mean: number; std: number; skewness: number; min_observed: number; max_observed: number; theoretical_range: [number, number] };
    y_scale: { mean: number; std: number; skewness: number; min_observed: number; max_observed: number; theoretical_range: [number, number] };
  };
  linear_equating?: {
    slope_alpha: number;
    intercept_beta: number;
    formula: string;
  };
  discrepancy_analysis?: {
    max_discrepancy: number;
    mean_discrepancy: number;
    agreement_verdict: 'EXCELLENT' | 'MODERATE' | 'SKEWED_DIVERGENCE';
    agreement_narrative: string;
  };
  concordance_table?: ConcordanceRow[];
  apa_narrative?: string;
}



// --- Multi-Group Measurement Invariance Types ---
export interface InvarianceModelSummary {
  model: string;
  level: 'CONFIGURAL' | 'METRIC' | 'SCALAR' | 'STRICT';
  chi_square: number;
  df: number;
  p_value: number;
  cfi: number;
  rmsea: number;
  delta_chi2: number | null;
  delta_df: number | null;
  delta_p: number | null;
  delta_cfi: number | null;
  delta_rmsea: number | null;
  supported: boolean;
}

export interface InvarianceItemDetail {
  item_name: string;
  loadings: Record<string, number>;
  intercepts: Record<string, number>;
  residual_variances: Record<string, number>;
  max_loading_discrepancy: number;
  is_stable: boolean;
}

export interface KruskalWallisRequest {
  target_question_id: string;
  grouping_question_id: string;
  scope?: 'all' | 'verified_clean';
}

export interface DunnPostHocPair {
  comparison: string;
  group1: string;
  group2: string;
  mean_rank1: number;
  mean_rank2: number;
  mean_rank_diff: number;
  std_error: number;
  z_statistic: number;
  p_value_unadjusted: number;
  p_value_bonferroni: number;
  is_significant_bonferroni: boolean;
}

export interface KruskalWallisResult {
  status: 'OK' | 'INSUFFICIENT_DATA' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  test_type?: 'KRUSKAL_WALLIS_H';
  k_groups?: number;
  total_sample_size?: number;
  degrees_of_freedom?: number;
  statistics?: {
    h_raw: number;
    h_adjusted: number;
    tie_correction_factor: number;
    ties_count: number;
    p_value: number;
    is_significant: boolean;
  };
  effect_size?: {
    epsilon_squared: number;
    magnitude: string;
  };
  groups_summary?: Array<{
    group_name: string;
    sample_size: number;
    rank_sum: number;
    mean_rank: number;
    median: number;
    iqr: number;
    mean: number;
    std: number;
  }>;
  post_hoc_dunn_tests?: DunnPostHocPair[];
  conclusion?: {
    is_significant: boolean;
    apa_narrative: string;
  };
}

// --- Missing Data Pattern Diagnostics & Imputation Types ---
export interface MissingVariableSummary {
  variable: string;
  observed_count: number;
  missing_count: number;
  missing_pct: number;
  mean: number | null;
  std: number | null;
}

export interface MissingPatternItem {
  pattern_id: string;
  bitstring: string;
  case_count: number;
  percentage: number;
  observed_variables: string[];
  missing_variables: string[];
  is_complete: boolean;
}

export interface LittlesMCARTest {
  applicable: boolean;
  reason?: string;
  chi_square: number | null;
  df: number;
  p_value: number | null;
  is_mcar?: boolean;
  conclusion: string;
  apa_writeup?: string;
}

export interface MissingDataDiagnosticsResult {
  status: 'OK' | 'INSUFFICIENT_VARIABLES' | 'INSUFFICIENT_SAMPLE' | 'EMPTY_DATA' | 'ERROR';
  message?: string;
  sample_size?: number;
  variables_count?: number;
  complete_cases_count?: number;
  incomplete_cases_count?: number;
  complete_cases_pct?: number;
  total_cells?: number;
  total_missing_cells?: number;
  overall_missing_rate?: number;
  variables_summary?: MissingVariableSummary[];
  patterns?: MissingPatternItem[];
  patterns_count?: number;
  littles_mcar_test?: LittlesMCARTest;
}

export interface MissingImputationComparison {
  variable: string;
  missing_cells_imputed: number;
  original_mean: number;
  imputed_mean: number;
  mean_delta_pct: number;
  original_std: number;
  imputed_std: number;
  preservation_status: 'HIGH' | 'MODERATE' | 'DRIFT_ALERT';
}

export interface MissingDataImputationResult {
  status: 'OK' | 'NO_MISSING_DATA' | 'INSUFFICIENT_VARIABLES' | 'INSUFFICIENT_SAMPLE' | 'EMPTY_DATA' | 'ERROR';
  message?: string;
  method?: string;
  method_label?: string;
  sample_size?: number;
  variables_count?: number;
  imputed_cells_count?: number;
  imputed_cells_pct?: number;
  comparison?: MissingImputationComparison[];
  apa_writeup?: string;
  imputed_data_sample?: Array<Record<string, number>>;
}

// --- Scale Equating & Concordance Transformation Types ---
export interface ConcordanceRow {
  x_score: number;
  percentile_rank: number;
  linear_equivalent_raw: number;
  linear_equivalent: number;
  linear_equivalent_rounded: number;
  equipercentile_equivalent: number;
  equipercentile_rounded: number;
  t_score: number;
  stanine: number;
}

export interface ScaleEquatingResult {
  status: 'OK' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  x_label?: string;
  y_label?: string;
  sample_sizes?: { x_count: number; y_count: number };
  descriptive_statistics?: {
    x_scale: { mean: number; std: number; skewness: number; min_observed: number; max_observed: number; theoretical_range: [number, number] };
    y_scale: { mean: number; std: number; skewness: number; min_observed: number; max_observed: number; theoretical_range: [number, number] };
  };
  linear_equating?: {
    slope_alpha: number;
    intercept_beta: number;
    formula: string;
  };
  discrepancy_analysis?: {
    max_discrepancy: number;
    mean_discrepancy: number;
    agreement_verdict: 'EXCELLENT' | 'MODERATE' | 'SKEWED_DIVERGENCE';
    agreement_narrative: string;
  };
  concordance_table?: ConcordanceRow[];
  apa_narrative?: string;
}



// --- Multi-Group Measurement Invariance Types ---
export interface InvarianceModelSummary {
  model: string;
  level: 'CONFIGURAL' | 'METRIC' | 'SCALAR' | 'STRICT';
  chi_square: number;
  df: number;
  p_value: number;
  cfi: number;
  rmsea: number;
  delta_chi2: number | null;
  delta_df: number | null;
  delta_p: number | null;
  delta_cfi: number | null;
  delta_rmsea: number | null;
  supported: boolean;
}

export interface InvarianceItemDetail {
  item_name: string;
  loadings: Record<string, number>;
  intercepts: Record<string, number>;
  residual_variances: Record<string, number>;
  max_loading_discrepancy: number;
  is_stable: boolean;
}

export interface MeasurementInvarianceResult {
  status: 'OK' | 'INSUFFICIENT_GROUPS' | 'INSUFFICIENT_ITEMS' | 'INSUFFICIENT_SAMPLE' | 'ERROR';
  message?: string;
  k_groups?: number;
  groups?: Record<string, number>;
  total_sample_size?: number;
  items_count?: number;
  highest_level_achieved?: 'CONFIGURAL_ONLY' | 'METRIC_INVARIANCE' | 'SCALAR_INVARIANCE' | 'STRICT_INVARIANCE';
  verdict_badge?: string;
  recommendation?: string;
  models_summary?: InvarianceModelSummary[];
  item_details?: InvarianceItemDetail[];
  apa_narrative?: string;
}



// --- Common Method Bias / Variance (CMB/CMV) Types ---
export interface HarmanFactorBreakdown {
  factor: number;
  eigenvalue: number;
  variance_pct: number;
  cumulative_pct: number;
}

export interface HarmanTestResult {
  n_sample: number;
  n_items: number;
  first_factor_eigenvalue: number;
  first_factor_variance_pct: number;
  factors_with_eigenvalue_gt_one: number;
  threshold_pct: number;
  has_cmv_risk: boolean;
  passed: boolean;
  variance_breakdown: HarmanFactorBreakdown[];
  first_factor_loadings: Record<string, number>;
  interpretation: string;
}

export interface MarkerPairComparison {
  variable_x: string;
  variable_y: string;
  r_original: number;
  p_original: number;
  r_adjusted: number;
  p_adjusted: number;
  significance_retained: boolean;
  t_statistic_adjusted: number;
}

export interface MarkerTestResult {
  marker_variable: string;
  is_auto_marker: boolean;
  marker_correlation_r_m: number;
  n_sample: number;
  degrees_of_freedom: number;
  total_pairs_tested: number;
  significant_pairs_before: number;
  significant_pairs_after: number;
  significance_retention_rate_pct: number;
  pair_comparisons: MarkerPairComparison[];
  interpretation: string;
}

export interface ULMCFTestResult {
  n_sample: number;
  n_items: number;
  estimated_cmv_variance_pct: number;
  benchmark_threshold_pct: number;
  is_acceptable: boolean;
  average_method_r2: number;
  method_loadings: Record<string, number>;
  interpretation: string;
}

export interface CMBRemedy {
  type: 'PROCEDURAL' | 'STATISTICAL' | 'REPORTING';
  title: string;
  detail: string;
}

export interface CommonMethodBiasResult {
  status: 'SUCCESS' | 'INSUFFICIENT_ITEMS' | 'INSUFFICIENT_SAMPLE' | 'INSUFFICIENT_COMPLETE_DATA' | 'ERROR';
  message?: string;
  overall_risk?: 'LOW' | 'MODERATE' | 'HIGH';
  risk_score?: number;
  risk_summary?: string;
  flagged_issues?: string[];
  harman_test?: HarmanTestResult;
  marker_test?: MarkerTestResult;
  ulmcf_test?: ULMCFTestResult;
  apa_writeup?: string;
  recommended_remedies?: CMBRemedy[];
}

// --- Statistical Moderation (PROCESS Model 1) Types ---
export interface ModerationVariableDetail {
  label: string;
  title: string;
  mean: number;
  std: number;
  range?: [number, number];
}

export interface ModerationSimpleSlope {
  level: 'LOW' | 'MEAN' | 'HIGH';
  label: string;
  w_value: number;
  slope: number;
  std_error: number;
  t_stat: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface ModerationPlotPoint {
  x: number;
  y_pred: number;
}

export interface ModerationPlotLine {
  level: 'LOW' | 'MEAN' | 'HIGH';
  label: string;
  point_low_x: ModerationPlotPoint;
  point_high_x: ModerationPlotPoint;
}

export interface ModerationAnalysisResult {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'INSUFFICIENT_COMPLETE_DATA' | 'ZERO_VARIANCE' | 'ERROR';
  message?: string;
  sample_size?: number;
  center_variables?: boolean;
  variables?: {
    independent_x: ModerationVariableDetail;
    moderator_w: ModerationVariableDetail;
    dependent_y: ModerationVariableDetail;
  };
  model_1_main_effects?: {
    r_squared: number;
    f_stat: number;
    p_value: number;
  };
  model_2_moderation?: {
    r_squared: number;
    f_stat: number;
    p_value: number;
    coefficients: Array<{
      term: string;
      label: string;
      title: string;
      b_unstandardized: number;
      std_error: number;
      beta_standardized: number;
      t_stat: number;
      p_value: number;
      is_significant_05: boolean;
      ci_95_lower: number;
      ci_95_upper: number;
      vif: number;
    }>;
  };
  moderation_effect?: {
    delta_r_squared: number;
    delta_f_stat: number;
    delta_p_value: number;
    interaction_b: number;
    interaction_se: number;
    interaction_t: number;
    interaction_p: number;
    is_significant: boolean;
    verdict_badge: string;
  };
  simple_slopes?: ModerationSimpleSlope[];
  johnson_neyman?: {
    has_solution: boolean;
    all_transition_points: number[];
    points_within_observed_range: number[];
    observed_moderator_range: [number, number];
    percent_sample_significant: number;
    interpretation: string;
  };
  interaction_plot?: {
    x_axis_label: string;
    y_axis_label: string;
    x_range: [number, number];
    lines: ModerationPlotLine[];
  };
  apa_narrative?: string;
}

export interface ModeratedMediationRequest {
  independent_question_id: string;
  mediator_question_id: string;
  moderator_question_id: string;
  dependent_question_id: string;
  center_variables?: boolean;
  num_bootstrap?: number;
  scope?: string;
}

export interface ModeratedMediationVariableDetail {
  title: string;
  mean: number;
  std: number;
}

export interface ConditionalIndirectEffect {
  level: 'LOW' | 'MEAN' | 'HIGH';
  label: string;
  w_value: number;
  conditional_a: number;
  b_path: number;
  indirect_effect: number;
  bootstrap_se: number;
  boot_ci_95_lower: number;
  boot_ci_95_upper: number;
  is_significant: boolean;
}

export interface ModeratedMediationResult {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'INSUFFICIENT_COMPLETE_DATA' | 'ZERO_VARIANCE' | 'SINGULAR_MATRIX' | 'ERROR';
  message?: string;
  sample_size?: number;
  bootstrap_samples_executed?: number;
  center_variables?: boolean;
  variables?: {
    independent_x: ModeratedMediationVariableDetail;
    mediator_m: ModeratedMediationVariableDetail;
    moderator_w: ModeratedMediationVariableDetail;
    dependent_y: ModeratedMediationVariableDetail;
  };
  stage1_mediator_model?: {
    formula: string;
    r_squared: number;
    f_stat: number;
    p_value: number;
    coefficients: {
      intercept_a0: number;
      path_a1_X: number;
      path_a2_W: number;
      interaction_a3_XW: number;
    };
  };
  stage2_dependent_model?: {
    formula: string;
    r_squared: number;
    f_stat: number;
    p_value: number;
    coefficients: {
      intercept_c0: number;
      direct_path_c_prime: number;
      mediator_path_b: number;
    };
  };
  index_of_moderated_mediation?: {
    index_omega: number;
    bootstrap_se: number;
    boot_ci_95_lower: number;
    boot_ci_95_upper: number;
    is_significant: boolean;
    verdict_badge: string;
  };
  conditional_indirect_effects?: ConditionalIndirectEffect[];
  apa_narrative?: string;
}























// --- Complex Survey Sampling (Two-Stage Cluster & Taylor Linearization) Types ---
export interface ComplexSamplingRequest {
  target_question_id: string;
  cluster_question_id: string;
  stratum_question_id?: string;
  weight_question_id?: string;
  scope?: string;
}

export interface ClusterBreakdownItem {
  stratum: string;
  cluster_id: string;
  sample_size: number;
  sum_weights: number;
  cluster_mean: number;
  deviation_from_mean: number;
}

export interface ComplexSamplingResult {
  status: 'SUCCESS' | 'INSUFFICIENT_SAMPLE' | 'INSUFFICIENT_COMPLETE_DATA' | 'ZERO_VARIANCE' | 'INSUFFICIENT_CLUSTERS' | 'ERROR';
  message?: string;
  sample_size?: number;
  strata_count?: number;
  psu_count?: number;
  degrees_of_freedom?: number;
  cluster_size_summary?: {
    mean_size: number;
    std_size: number;
    min_size: number;
    max_size: number;
    cv_size: number;
  };
  weight_summary?: {
    total_population_estimate: number;
    mean_weight: number;
    std_weight: number;
    cv_weight: number;
    kish_weight_deff: number;
  };
  horvitz_thompson_estimates?: {
    weighted_mean: number;
    unweighted_mean: number;
    weighting_bias_shift: number;
    weighted_total: number;
  };
  taylor_linearization_variance?: {
    complex_variance: number;
    complex_se: number;
    t_critical_95: number;
    ci_95_lower: number;
    ci_95_upper: number;
    margin_of_error: number;
    lonely_psu_detected: boolean;
  };
  srs_comparison?: {
    srs_variance: number;
    srs_se: number;
    ci_95_lower: number;
    ci_95_upper: number;
    se_inflation_ratio: number;
  };
  design_effects?: {
    deff: number;
    deft: number;
    icc: number;
    effective_sample_size: number;
    efficiency_loss_pct: number;
    rating: string;
    interpretation: string;
  };
  clusters_breakdown?: ClusterBreakdownItem[];
  apa_narrative?: string;
}


// --- Propensity Score Matching (PSM) & Inverse Probability Weighting (IPW) Types ---
export interface PSMAnalysisRequest {
  treatment_question_id: string;
  treatment_value: any;
  outcome_question_id: string;
  covariate_question_ids: string[];
  caliper_factor?: number;
  scope?: string;
}

export interface CovariateBalanceItem {
  covariate: string;
  raw_treated_mean: number;
  raw_control_mean: number;
  raw_smd: number;
  raw_variance_ratio: number;
  matched_treated_mean: number;
  matched_control_mean: number;
  matched_smd: number;
  matched_variance_ratio: number;
  pct_bias_reduction: number;
  is_balanced: boolean;
}

export interface CommonSupportBin {
  bin_index: number;
  bin_min: number;
  bin_max: number;
  bin_label: string;
  treated_count: number;
  control_count: number;
  is_overlapping: boolean;
}

export interface LovePlotPoint {
  covariate: string;
  raw_smd: number;
  matched_smd: number;
  threshold_lower: number;
  threshold_upper: number;
}

export interface PSMAnalysisResult {
  status: string;
  survey_id?: string;
  treatment_name?: string;
  outcome_name?: string;
  sample_size?: number;
  sample_treated?: number;
  sample_control?: number;
  matched_pairs_count?: number;
  unmatched_treated_count?: number;
  unmatched_control_count?: number;
  caliper_factor?: number;
  caliper_width?: number;
  unadjusted_effect?: {
    treated_mean: number;
    control_mean: number;
    raw_difference: number;
    t_stat: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
  };
  matched_att?: {
    estimate: number;
    se: number;
    t_stat: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
    cohens_d: number;
    is_significant: boolean;
  };
  ipw_att?: {
    estimate: number;
    se: number;
    t_stat: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
  };
  covariate_balance?: CovariateBalanceItem[];
  balance_summary?: {
    total_covariates: number;
    balanced_covariates: number;
    all_balanced: boolean;
    max_matched_smd: number;
    mean_bias_reduction_pct: number;
  };
  common_support_overlap?: CommonSupportBin[];
  love_plot?: LovePlotPoint[];
  apa_narrative?: string;
}


// --- Structural Topic Modeling (STM) & Latent Dirichlet Allocation (LDA) Types ---
export interface TopicModelAnalysisRequest {
  text_question_id: string;
  covariate_question_id?: string;
  num_topics?: number;
  num_iterations?: number;
  scope?: string;
}

export interface TopicWordItem {
  word: string;
  probability: number;
  frequency: number;
  exclusivity: number;
}

export interface TopicResultItem {
  topic_id: number;
  label: string;
  short_label: string;
  prevalence_share: number;
  prevalence_percent: number;
  coherence_umass: number;
  top_words: TopicWordItem[];
}

export interface TopicCovariateEffect {
  topic_id: number;
  topic_label: string;
  beta_coefficient: number;
  correlation_r: number;
  direction: 'positive' | 'negative' | 'neutral';
  interpretation: string;
}

export interface TopicDocumentAssignment {
  response_id: string;
  text_snippet: string;
  dominant_topic_id: number;
  dominant_probability: number;
  covariate_value?: number | null;
}

export interface TopicModelAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  vocabulary_size?: number;
  num_topics?: number;
  hyperparameters?: {
    alpha: number;
    beta: number;
    iterations: number;
  };
  mean_coherence_umass?: number;
  topics?: TopicResultItem[];
  covariate_effects?: TopicCovariateEffect[];
  document_sample_assignments?: TopicDocumentAssignment[];
  apa_narrative?: string;
}


// --- Psychometric Network Analysis (GGM) Types ---
export interface PsychometricNetworkRequest {
  question_ids?: string[];
  regularization_threshold?: number;
  scope?: string;
}

export interface NetworkNodeItem {
  id: number;
  name: string;
  x: number;
  y: number;
  strength: number;
  z_strength: number;
  expected_influence: number;
  z_influence: number;
  closeness: number;
  z_closeness: number;
  betweenness: number;
  z_betweenness: number;
}

export interface NetworkEdgeItem {
  source: number;
  target: number;
  source_name: string;
  target_name: string;
  weight: number;
  abs_weight: number;
  edge_type: 'positive' | 'negative';
}

export interface PsychometricNetworkResult {
  status: string;
  message?: string;
  sample_size?: number;
  num_nodes?: number;
  num_edges?: number;
  possible_edges?: number;
  density?: number;
  density_percent?: number;
  sparsity_percent?: number;
  mean_weight?: number;
  most_central_node?: string;
  nodes?: NetworkNodeItem[];
  edges?: NetworkEdgeItem[];
  apa_narrative?: string;
}


// --- Item Response Theory (IRT) 2-Parameter Logistic (2PL) Types ---
export interface IRT2PLAnalysisRequest {
  question_ids?: string[];
  binarization_threshold?: number;
  max_em_iter?: number;
  scope?: string;
}

export interface IRTItemResult {
  item_id: string;
  item_name: string;
  discrimination_a: number;
  discrimination_class: 'VERY_LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
  discrimination_label: string;
  difficulty_b: number;
  difficulty_class: 'VERY_EASY' | 'EASY' | 'MEDIUM' | 'HARD' | 'VERY_HARD';
  difficulty_label: string;
  endorsement_rate: number;
  peak_information: number;
  fit_chi_sq: number;
  is_good_fit: boolean;
}

export interface IRTCurvePoint {
  theta: number;
  prob?: number;
  info?: number;
  se?: number;
  svg_x: number;
  svg_y: number;
}

export interface IRTICCCurve {
  item_id: string;
  item_name: string;
  points: IRTCurvePoint[];
  svg_path: string;
}

export interface IRTTestInformationCurve {
  max_tif: number;
  tif_points: IRTCurvePoint[];
  se_points: IRTCurvePoint[];
  tif_path: string;
  se_path: string;
}

export interface IRTPersonTraitSummary {
  mean_theta: number;
  sd_theta: number;
  min_theta: number;
  max_theta: number;
  mean_se: number;
}

export interface IRT2PLAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  num_items?: number;
  is_already_binary?: boolean;
  marginal_reliability?: number;
  max_test_information?: number;
  optimal_theta_range?: [number, number];
  average_discrimination?: number;
  average_difficulty?: number;
  items?: IRTItemResult[];
  icc_curves?: IRTICCCurve[];
  test_information_curve?: IRTTestInformationCurve;
  person_trait_summary?: IRTPersonTraitSummary;
  apa_narrative?: string;
}


// --- Survival Analysis & Time-to-Drop-off (Kaplan-Meier & Cox HR) Types ---
export interface SurvivalAnalysisRequest {
  grouping_question_id?: string;
  time_milestones?: number[];
  scope?: string;
}

export interface SurvivalStep {
  time: number;
  at_risk: number;
  events: number;
  censored: number;
  survival_prob: number;
  se_greenwood: number;
  ci_lower: number;
  ci_upper: number;
}

export interface SurvivalMilestone {
  time_seconds: number;
  time_minutes: number;
  survival_probability: number;
  retention_percentage: number;
  dropout_percentage: number;
}

export interface SurvivalCurveData {
  max_observed_time: number;
  median_survival_time?: number | null;
  steps: SurvivalStep[];
  svg_path: string;
  svg_points: {
    time: number;
    prob: number;
    svg_x: number;
    svg_y: number;
  }[];
}

export interface SurvivalGroupComparison {
  group_1: {
    name: string;
    sample_size: number;
    events_count: number;
    median_survival?: number | null;
    svg_path: string;
  };
  group_2: {
    name: string;
    sample_size: number;
    events_count: number;
    median_survival?: number | null;
    svg_path: string;
  };
}

export interface LogRankTestResult {
  group1_name: string;
  group2_name: string;
  observed_events_1: number;
  expected_events_1: number;
  observed_events_2: number;
  expected_events_2: number;
  chi2_statistic: number;
  degrees_of_freedom: number;
  p_value: number;
  is_statistically_significant: boolean;
}

export interface CoxHazardRatioResult {
  reference_group: string;
  comparison_group: string;
  hazard_ratio: number;
  ci_95_lower: number;
  ci_95_upper: number;
  risk_interpretation: string;
}

export interface SurvivalAnalysisResult {
  status: string;
  message?: string;
  total_participants?: number;
  completed_count?: number;
  drop_off_count?: number;
  overall_completion_rate?: number;
  overall_drop_off_rate?: number;
  overall_km?: SurvivalCurveData;
  milestones?: SurvivalMilestone[];
  group_comparison?: SurvivalGroupComparison;
  log_rank_test?: LogRankTestResult;
  cox_hazard_ratio?: CoxHazardRatioResult;
  apa_narrative?: string;
}

export interface MultilevelAnalysisRequest {
  outcome_question_id: string;
  predictor_question_id?: string | null;
  cluster_question_id?: string | null;
  centering?: 'grand_mean' | 'group_mean' | 'none';
  scope?: 'all' | 'verified_clean';
}

export interface MultilevelNullModel {
  intercept_gamma_00: number;
  tau_00: number;
  sigma_sq: number;
  icc: number;
  icc_percentage: number;
  icc_tier: string;
  icc_label: string;
  icc_recommendation: string;
}

export interface MultilevelFixedEffects {
  intercept_gamma_00: number;
  se_gamma_00: number;
  t_gamma_00: number;
  p_gamma_00: number;
  slope_gamma_10?: number | null;
  se_gamma_10?: number | null;
  t_gamma_10?: number | null;
  p_gamma_10?: number | null;
}

export interface MultilevelRandomEffects {
  tau_00_intercept_var: number;
  tau_11_slope_var: number;
  sigma_sq_residual_var: number;
  r2_level_1: number;
  r2_level_2: number;
}

export interface MultilevelModelComparison {
  deviance_hlm: number;
  deviance_ols: number;
  delta_deviance_chi2: number;
  df: number;
  p_value: number;
  is_hlm_significantly_better: boolean;
}

export interface MultilevelClusterTrajectory {
  cluster_id: string;
  n_j: number;
  y_mean: number;
  x_mean: number;
  eb_intercept: number;
  eb_slope: number;
  shrinkage_weight: number;
  svg_path: string;
  color: string;
}

export interface MultilevelAnalysisResult {
  status: string;
  message?: string;
  total_sample_size?: number;
  num_clusters?: number;
  average_cluster_size?: number;
  dependent_variable?: string;
  predictor_variable?: string;
  cluster_variable?: string;
  centering?: string;
  null_model?: MultilevelNullModel;
  fixed_effects?: MultilevelFixedEffects;
  random_effects?: MultilevelRandomEffects;
  model_comparison_ols_vs_hlm?: MultilevelModelComparison;
  cluster_trajectories?: MultilevelClusterTrajectory[];
  grand_trajectory_path?: string;
  apa_narrative?: string;
}

export interface ConjointAnalysisRequest {
  rating_question_id: string;
  attribute_question_ids: string[];
  price_question_id?: string | null;
  scope?: 'all' | 'verified_clean';
}

export interface ConjointImportanceItem {
  attribute: string;
  importance_pct: number;
  range: number;
  levels_count: number;
  best_level: string;
  worst_level: string;
}

export interface ConjointWTPItem {
  attribute: string;
  level: string;
  part_worth: number;
  wtp_valuation: number;
}

export interface ConjointAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  attributes_count?: number;
  parameters_estimated?: number;
  overall_utility_intercept?: number;
  model_fit?: {
    r_squared: number;
    adjusted_r_squared: number;
    mcfadden_pseudo_r2: number;
    rmse: number;
    fit_quality: string;
  };
  importance_ranking?: ConjointImportanceItem[];
  part_worth_utilities?: Record<string, Record<string, number>>;
  willingness_to_pay?: ConjointWTPItem[];
  svg_importance_chart?: string;
  apa_narrative?: string;
}

export interface ConjointSimulationRequest {
  rating_question_id: string;
  attribute_question_ids: string[];
  candidate_profiles: Array<{
    id: string;
    attributes: Record<string, string>;
  }>;
  scope?: 'all' | 'verified_clean';
}

export interface ConjointSimulationResult {
  status: string;
  message?: string;
  market_shares?: Array<{
    profile_id: string;
    total_utility: number;
    choice_share_pct: number;
  }>;
}

export interface LCAAnalysisRequest {
  item_question_ids: string[];
  num_classes?: number | null;
  scope?: 'all' | 'verified_clean';
}

export interface LCAModelComparisonItem {
  num_classes: number;
  log_likelihood: number;
  num_parameters: number;
  aic: number;
  bic: number;
  sabic: number;
  entropy: number;
  converged: boolean;
}

export interface LCAClassProfile {
  class_index: number;
  class_name: string;
  prevalence_pct: number;
  assigned_count: number;
  color: string;
  item_probabilities: Record<string, Record<string, number>>;
}

export interface LCAAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  items_count?: number;
  optimal_classes_count?: number;
  model_selection_criteria?: LCAModelComparisonItem[];
  entropy?: number;
  entropy_quality?: string;
  class_prevalences?: Record<string, number>;
  class_profiles?: LCAClassProfile[];
  posterior_class_distribution?: number[];
  svg_profile_plot?: string;
  apa_narrative?: string;
}

export interface DiDAnalysisRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  time_question_id: string;
  treatment_value?: string | null;
  post_value?: string | null;
  scope?: 'all' | 'verified_clean';
}

export interface DiDCellMeanItem {
  mean: number;
  n: number;
  diff?: number;
}

export interface DiDAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  groups?: {
    treatment_name: string;
    control_name: string;
    pre_period_name: string;
    post_period_name: string;
  };
  cell_means_2x2?: {
    control_pre: DiDCellMeanItem;
    control_post: DiDCellMeanItem;
    treat_pre: DiDCellMeanItem;
    treat_post: DiDCellMeanItem;
    counterfactual_post: number;
  };
  did_treatment_effect?: {
    att_estimate: number;
    std_error: number;
    t_statistic: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
    is_statistically_significant: boolean;
    relative_gain_pct: number;
  };
  regression_coefficients?: {
    intercept_beta_0: number;
    baseline_selection_beta_1: number;
    time_trend_drift_beta_2: number;
    interaction_att_delta: number;
    r_squared: number;
  };
  svg_trajectory_chart?: string;
  apa_narrative?: string;
}

export interface SEMPathSpec {
  source: string;
  target: string;
}

export interface SEMAnalysisRequest {
  paths: SEMPathSpec[];
  scope?: 'all' | 'verified_clean';
}

export interface SEMPathParameter {
  source: string;
  target: string;
  source_label: string;
  target_label: string;
  unstandardized: number;
  standard_error: number;
  z_value: number;
  p_value: number;
  standardized: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface SEMEquationSummary {
  endogenous_var: string;
  endogenous_label: string;
  predictors: string[];
  r_squared: number;
  adj_r_squared: number;
  residual_variance: number;
  f_statistic: number;
  p_value: number;
}

export interface SEMIndirectEffect {
  source: string;
  target: string;
  source_label: string;
  target_label: string;
  path: string[];
  path_str: string;
  unstandardized: number;
  standard_error: number;
  z_value: number;
  p_value: number;
  standardized: number;
  is_significant: boolean;
}

export interface SEMTotalEffect {
  source: string;
  target: string;
  source_label: string;
  target_label: string;
  direct: number;
  indirect: number;
  total: number;
  standardized_direct: number;
  standardized_indirect: number;
  standardized_total: number;
}

export interface SEMFitIndices {
  chi_square: number;
  df: number;
  p_value: number;
  chi_square_baseline: number;
  df_baseline: number;
  cfi: number;
  tli: number;
  rmsea: number;
  rmsea_ci_90_lower: number;
  rmsea_ci_90_upper: number;
  srmr: number;
  is_good_fit: boolean;
  fit_assessment: string;
}

export interface SEMAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  observed_variables?: string[];
  exogenous_variables?: string[];
  endogenous_variables?: string[];
  paths?: SEMPathParameter[];
  equations?: SEMEquationSummary[];
  indirect_effects?: SEMIndirectEffect[];
  total_effects?: SEMTotalEffect[];
  fit_indices?: SEMFitIndices;
  svg_path_diagram?: string;
  apa_narrative?: string;
}

export interface CompetingRisksAnalysisRequest {
  cluster_question_id?: string | null;
  event_question_id?: string | null;
  time_milestones?: number[] | null;
  scope?: 'all' | 'verified_clean';
}

export interface CompetingRisksMilestone {
  time_seconds: number;
  overall_completion_rate: number;
  cumulative_incidence: Record<string, number>;
  naive_kaplan_meier: Record<string, number>;
  km_overestimation_bias: Record<string, number>;
}

export interface ClusterFrailtyEstimate {
  cluster_id: string;
  sample_size: number;
  dropoffs: number;
  dropoff_rate: number;
  frailty_relative_risk: number;
  interpretation: string;
}

export interface SharedFrailtyModelResult {
  clusters_count: number;
  frailty_variance_theta: number;
  lrt_statistic: number;
  p_value: number;
  is_cluster_heterogeneity_significant: boolean;
  cluster_frailty_estimates: ClusterFrailtyEstimate[];
}

export interface CompetingRisksAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  competing_causes?: string[];
  final_cumulative_incidence?: Record<string, number>;
  milestone_evaluations?: CompetingRisksMilestone[];
  shared_frailty_model?: SharedFrailtyModelResult;
  svg_cif_chart?: string;
  apa_narrative?: string;
}

export interface IRT4PLAnalysisRequest {
  question_ids: string[];
  model_type?: '3pl' | '4pl';
  binarization_threshold?: number | null;
  scope?: 'all' | 'verified_clean';
}

export interface IRT4PLItemParameter {
  item_index: number;
  item_name: string;
  proportion_correct: number;
  discrimination_a: number;
  difficulty_b: number;
  guessing_c: number;
  inattention_d: number;
  quality_tier: string;
}

export interface IRT4PLTestInformation {
  peak_theta: number;
  peak_information: number;
  minimum_standard_error: number;
  theta_range: number[];
  theta_grid: number[];
  information_values: number[];
  standard_errors: number[];
  conditional_reliabilities: number[];
}

export interface IRT4PLCatStep {
  step: number;
  item_index: number;
  item_name: string;
  item_difficulty_b: number;
  simulated_response: number;
  provisional_theta: number;
  measurement_se: number;
}

export interface IRT4PLAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  items_count?: number;
  model_type?: '3PL' | '4PL';
  binarization_threshold?: number;
  items_parameters?: IRT4PLItemParameter[];
  test_information_function?: IRT4PLTestInformation;
  cat_simulation?: IRT4PLCatStep[];
  svg_curves?: string;
  apa_narrative?: string;
}

export interface IPWBalanceDiagnostic {
  covariate_key: string;
  covariate_label: string;
  raw_asmd: number;
  weighted_asmd: number;
  weighted_variance_ratio: number;
  is_balanced: boolean;
  improvement_pct: number;
}

export interface IPWAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  treated_count?: number;
  control_count?: number;
  weight_scheme?: string;
  unadjusted_effect?: {
    difference_in_means: number;
    standard_error: number;
    treated_mean: number;
    control_mean: number;
  };
  ipw_estimator?: {
    treatment_effect: number;
    standard_error: number;
    z_value: number;
    p_value: number;
    is_significant: boolean;
  };
  doubly_robust_estimator?: {
    treatment_effect: number;
    standard_error: number;
    z_value: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
    is_significant: boolean;
  };
  covariate_balance?: {
    all_balanced_under_0_10: boolean;
    maximum_weighted_asmd: number;
    diagnostics: IPWBalanceDiagnostic[];
  };
  svg_love_plot?: string;
  apa_narrative?: string;
}

export interface IPWAnalysisRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  treatment_value?: string;
  weight_scheme?: 'ate' | 'att' | 'overlap' | 'stabilized';
  trim_weights?: boolean;
  scope?: 'all' | 'verified_clean';
}

export interface GAMSplineTurningPoint {
  x_value: number;
  predicted_y: number;
  point_type: string;
}

export interface GAMSplineAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  knots_count?: number;
  knots?: number[];
  linear_baseline?: {
    r_squared: number;
    rss: number;
    intercept: number;
    slope: number;
  };
  gam_spline_model?: {
    effective_degrees_of_freedom: number;
    r_squared: number;
    adjusted_r_squared: number;
    rss: number;
    residual_variance: number;
    gcv_score: number;
  };
  nonlinearity_test?: {
    f_statistic: number;
    delta_df: number;
    p_value: number;
    is_significant_nonlinearity: boolean;
  };
  turning_points?: GAMSplineTurningPoint[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface GAMSplineAnalysisRequest {
  predictor_question_id: string;
  outcome_question_id: string;
  n_knots?: number;
  smoothing_penalty?: number;
  scope?: 'all' | 'verified_clean';
}

export interface QuantileEstimateRow {
  tau: number;
  intercept: number;
  slope: number;
  standard_error: number;
  t_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
  pseudo_r1: number;
  pinball_loss: number;
}

export interface QuantileRegressionResult {
  status: string;
  message?: string;
  sample_size?: number;
  covariates_count?: number;
  ols_baseline?: {
    slope: number;
    standard_error: number;
    t_statistic: number;
    p_value: number;
    is_significant: boolean;
    r_squared: number;
  };
  quantile_estimates?: QuantileEstimateRow[];
  heterogeneity_test?: {
    tau_comparison: string;
    slope_difference: number;
    standard_error: number;
    z_statistic: number;
    p_value: number;
    has_significant_heterogeneity: boolean;
  };
  svg_process_plot?: string;
  apa_narrative?: string;
}

export interface QuantileRegressionRequest {
  predictor_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  quantiles?: number[];
  scope?: 'all' | 'verified_clean';
}

export interface GTheoryVarianceComponent {
  source: string;
  label: string;
  df: number;
  ss: number;
  ms: number;
  variance: number;
  percent: number;
}

export interface GTheoryDStudyRow {
  n_items: number;
  relative_error_var: number;
  absolute_error_var: number;
  sem_relative: number;
  sem_absolute: number;
  g_coefficient: number;
  phi_coefficient: number;
  is_acceptable_norm: boolean;
  is_acceptable_criterion: boolean;
}

export interface GTheoryAnalysisResult {
  status: string;
  message?: string;
  design_type?: string;
  sample_size?: number;
  items_count?: number;
  variance_components?: GTheoryVarianceComponent[];
  current_design_metrics?: {
    universe_score_variance: number;
    relative_error_variance: number;
    absolute_error_variance: number;
    g_coefficient_relative: number;
    phi_coefficient_absolute: number;
    sem_relative: number;
    sem_absolute: number;
  };
  d_study_projections?: GTheoryDStudyRow[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface GTheoryAnalysisRequest {
  item_question_ids: string[];
  rater_question_id?: string | null;
  scope?: 'all' | 'verified_clean';
}

export interface RDDBinnedScatterPoint {
  side: 'left' | 'right';
  x_mean: number;
  y_mean: number;
  count: number;
}

export interface RDDAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  effective_sample_size?: number;
  cutoff_threshold?: number;
  bandwidth?: number;
  treatment_effect_late?: {
    tau_rdd: number;
    standard_error: number;
    z_statistic: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
    is_significant: boolean;
    left_limit_intercept: number;
    right_limit_intercept: number;
    left_slope: number;
    right_slope: number;
  };
  mccrary_manipulation_test?: {
    log_difference: number;
    p_value: number;
    has_manipulation: boolean;
    verdict: string;
  };
  binned_scatter_points?: RDDBinnedScatterPoint[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface RDDAnalysisRequest {
  running_question_id: string;
  outcome_question_id: string;
  cutoff: number;
  bandwidth?: number | null;
  polynomial_order?: number;
  scope?: 'all' | 'verified_clean';
}

export interface SCMDonorWeight {
  donor_name: string;
  weight: number;
  weight_percentage: number;
}

export interface SCMBalanceRow {
  period: string;
  treated_value: number;
  synthetic_value: number;
  donor_mean_value: number;
  difference: number;
}

export interface SCMTrajectoryPoint {
  period: string;
  actual_treated: number;
  synthetic_control: number;
  gap: number;
  is_post_treatment: boolean;
}

export interface SyntheticControlAnalysisResult {
  status: string;
  message?: string;
  treated_unit?: string;
  treatment_period?: string;
  treatment_period_index?: number;
  donor_pool_count?: number;
  att_effect?: number;
  rmspe_pre?: number;
  rmspe_post?: number;
  rmspe_ratio?: number;
  empirical_p_value?: number;
  is_significant?: boolean;
  top_donor_weights?: SCMDonorWeight[];
  balance_table?: SCMBalanceRow[];
  trajectory?: SCMTrajectoryPoint[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface SyntheticControlAnalysisRequest {
  unit_question_id: string;
  period_question_id: string;
  outcome_question_id: string;
  treated_unit: string;
  treatment_period: any;
  scope?: 'all' | 'verified_clean';
}

export interface SAEAreaEstimate {
  area_name: string;
  sample_size: number;
  direct_estimate: number;
  direct_se: number;
  direct_ci_lower: number;
  direct_ci_upper: number;
  synthetic_prediction: number;
  shrinkage_weight_gamma: number;
  eblup_estimate: number;
  eblup_se: number;
  eblup_ci_lower: number;
  eblup_ci_upper: number;
  efficiency_gain_pct: number;
}

export interface SAERegressionCoef {
  term: string;
  coefficient: number;
  std_error: number;
  z_statistic: number;
  p_value: number;
}

export interface SmallAreaEstimationResult {
  status: string;
  message?: string;
  area_count?: number;
  between_area_variance_sigma_v2?: number;
  mean_shrinkage_weight_gamma?: number;
  mean_efficiency_gain_pct?: number;
  regression_coefficients?: SAERegressionCoef[];
  area_estimates?: SAEAreaEstimate[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface SmallAreaEstimationRequest {
  area_question_id: string;
  outcome_question_id: string;
  auxiliary_question_ids?: string[];
  scope?: 'all' | 'verified_clean';
}

export interface EventStudyCoefficient {
  relative_period: number;
  period_label: string;
  coefficient: number;
  std_error: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_reference: boolean;
  is_lead: boolean;
  is_significant: boolean;
}

export interface EventStudyAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  units_count?: number;
  periods_count?: number;
  event_window_min?: number;
  event_window_max?: number;
  pre_trend_wald_stat?: number;
  pre_trend_df?: number;
  pre_trend_p_value?: number;
  parallel_trends_supported?: boolean;
  avg_post_treatment_effect?: number;
  cumulative_post_treatment_effect?: number;
  event_coefficients?: EventStudyCoefficient[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface EventStudyAnalysisRequest {
  unit_question_id: string;
  time_question_id: string;
  outcome_question_id: string;
  event_time_question_id?: string;
  treated_units?: string[];
  global_event_time?: any;
  max_leads?: number;
  max_lags?: number;
  scope?: 'all' | 'verified_clean';
}

export interface BSTSTrajectoryPoint {
  period: string;
  actual: number;
  counterfactual: number;
  ci_95_lower: number;
  ci_95_upper: number;
  pointwise_impact: number;
  cumulative_impact: number;
  cumulative_ci_lower: number;
  cumulative_ci_upper: number;
  is_post: boolean;
}

export interface BSTSCausalImpactResult {
  status: string;
  message?: string;
  intervention_time?: string;
  intervention_index?: number;
  pre_periods_count?: number;
  post_periods_count?: number;
  avg_actual_post?: number;
  avg_counterfactual_post?: number;
  avg_pointwise_effect?: number;
  cumulative_effect?: number;
  relative_effect_pct?: number;
  posterior_tail_p_value?: number;
  is_significant?: boolean;
  trajectory?: BSTSTrajectoryPoint[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface BSTSCausalImpactRequest {
  time_question_id: string;
  outcome_question_id: string;
  intervention_time: any;
  covariate_question_ids?: string[];
  scope?: 'all' | 'verified_clean';
}




















// --- Doubly Robust AIPW & Heterogeneous CATE (Robins et al. 1994, Chernozhukov et al. 2018) Types ---
export interface AIPWSubgroupCATE {
  subgroup: string;
  sample_size: number;
  cate: number;
  se: number;
  ci_lower: number;
  ci_upper: number;
  z_score: number;
  p_value: number;
}

export interface AIPWPropensityOverlap {
  treated_mean: number;
  control_mean: number;
  overlap_range: [number, number];
  strong_overlap: boolean;
}

export interface AIPWHeterogeneityTest {
  f_statistic?: number;
  p_value?: number;
  is_heterogeneous: boolean;
}

export interface AIPWCATEResult {
  status: string;
  message?: string;
  ate?: number;
  se?: number;
  z_stat?: number;
  p_value?: number;
  ci_95_lower?: number;
  ci_95_upper?: number;
  is_significant?: boolean;
  naive_difference?: number;
  selection_bias_estimate?: number;
  total_sample_size?: number;
  effective_sample_size?: number;
  trimmed_units_count?: number;
  propensity_overlap?: AIPWPropensityOverlap;
  subgroup_cate?: AIPWSubgroupCATE[];
  heterogeneity_test?: AIPWHeterogeneityTest;
  svg_chart?: string;
  apa_narrative?: string;
}

export interface AIPWCATERequest {
  treatment_question_id: string;
  outcome_question_id: string;
  confounder_question_ids: string[];
  subgroup_question_id?: string;
  treatment_value?: any;
  trim_alpha?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Instrumental Variables Two-Stage Least Squares (2SLS) Types ---
export interface IVEstimate {
  beta: number;
  se: number;
  z_stat: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface OLSBenchmark {
  beta: number;
  se: number;
  t_stat: number;
  p_value: number;
  bias_difference: number;
}

export interface FirstStageDiagnostics {
  f_statistic: number;
  p_value: number;
  is_weak_instrument: boolean;
  staiger_stock_rule_of_thumb: number;
  stock_yogo_10_pct_critical_value: number;
  stock_yogo_15_pct_critical_value: number;
}

export interface WuHausmanTest {
  t_statistic: number;
  p_value: number;
  is_endogenous: boolean;
}

export interface SarganHansenTest {
  j_statistic?: number;
  p_value?: number;
  instruments_valid?: boolean;
  degrees_of_freedom?: number;
}

export interface IV2SLSResult {
  status: string;
  message?: string;
  sample_size?: number;
  instruments_count?: number;
  iv_estimate?: IVEstimate;
  ols_benchmark?: OLSBenchmark;
  first_stage_diagnostics?: FirstStageDiagnostics;
  wu_hausman_test?: WuHausmanTest;
  sargan_hansen_overid_test?: SarganHansenTest;
  svg_chart?: string;
  apa_narrative?: string;
}

export interface IV2SLSRequest {
  outcome_question_id: string;
  endogenous_question_id: string;
  instrument_question_ids: string[];
  control_question_ids?: string[];
  scope?: 'all' | 'verified_clean';
}


// --- Bifactor Psychometric Modeling & Omega Hierarchical Types ---
export interface BifactorSubscaleMetric {
  subscale: string;
  item_count: number;
  items: string[];
  omega_subscale_total: number;
  omega_hierarchical_subscale: number;
  viable_as_independent_scale: boolean;
}

export interface BifactorItemDiagnostic {
  item_index: number;
  label: string;
  subscale: string;
  loading_general: number;
  loading_subscale: number;
  uniqueness: number;
  item_ecv: number;
  is_general_anchor: boolean;
}

export interface BifactorAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  items_count?: number;
  subscales_count?: number;
  omega_total?: number;
  omega_hierarchical?: number;
  explained_common_variance?: number;
  percent_uncontaminated_correlations?: number;
  is_essentially_unidimensional?: boolean;
  recommendation?: string;
  subscale_metrics?: BifactorSubscaleMetric[];
  item_diagnostics?: BifactorItemDiagnostic[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface BifactorSubscaleInput {
  subscale_name: string;
  question_ids: string[];
}

export interface BifactorAnalysisRequest {
  subscales: BifactorSubscaleInput[];
  scope?: 'all' | 'verified_clean';
}


// --- Panel Vector Autoregression (Panel VAR) & Granger Causality Types ---
export interface PVARGrangerTest {
  wald_chi2: number;
  p_value: number;
  is_significant: boolean;
}

export interface PVAREquation {
  dependent_var: string;
  coeff_self_lag: number;
  se_self_lag: number;
  coeff_cross_lag: number;
  se_cross_lag: number;
}

export interface PanelVARResult {
  status: string;
  message?: string;
  panel_units_count?: number;
  effective_observations?: number;
  lags?: number;
  var1_name?: string;
  var2_name?: string;
  is_stable?: boolean;
  stability_max_modulus?: number;
  causality_conclusion?: string;
  equations?: {
    eq_var1: PVAREquation;
    eq_var2: PVAREquation;
  };
  granger_causality?: {
    var1_causes_var2: PVARGrangerTest;
    var2_causes_var1: PVARGrangerTest;
  };
  fevd_horizon_5?: {
    var1_explained_by_var2_pct: number;
    var2_explained_by_var1_pct: number;
  };
  oirf_trajectory?: {
    response_of_var2_to_var1: number[];
    response_of_var1_to_var2: number[];
  };
  svg_chart?: string;
  apa_narrative?: string;
}

export interface PanelVARRequest {
  unit_question_id: string;
  time_question_id: string;
  var1_question_id: string;
  var2_question_id: string;
  lags?: number;
  irf_horizons?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Latent Growth Curve Modeling (LGCM) Types ---
export interface LatentGrowthMeans {
  intercept_mean: number;
  intercept_se: number;
  intercept_z: number;
  intercept_p: number;
  slope_mean: number;
  slope_se: number;
  slope_z: number;
  slope_p: number;
}

export interface LatentGrowthVariances {
  intercept_variance: number;
  slope_variance: number;
  intercept_slope_covariance: number;
  intercept_slope_correlation: number;
}

export interface LatentGrowthFit {
  chi_square: number;
  degrees_of_freedom: number;
  p_value: number;
  cfi: number;
  tli: number;
  rmsea: number;
  is_good_fit: boolean;
}

export interface LatentGrowthDynamics {
  has_significant_trajectory: boolean;
  has_individual_heterogeneity: boolean;
  direction: string;
}

export interface LatentGrowthResult {
  status: string;
  message?: string;
  sample_size?: number;
  waves_count?: number;
  latent_means?: LatentGrowthMeans;
  latent_variances?: LatentGrowthVariances;
  model_fit?: LatentGrowthFit;
  growth_dynamics?: LatentGrowthDynamics;
  observed_wave_means?: number[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface LatentGrowthRequest {
  wave_question_ids: string[];
  time_scores?: number[];
  wave_labels?: string[];
  scope?: 'all' | 'verified_clean';
}


// --- Quantile Treatment Effects (QTE) Types ---
export interface QuantileEffectItem {
  quantile: number;
  qte: number;
  q_treated: number;
  q_control: number;
  std_error: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface QTEResult {
  status: string;
  message?: string;
  sample_size?: number;
  treated_count?: number;
  control_count?: number;
  average_treatment_effect?: number;
  median_treatment_effect?: number;
  delta_iqr_effect?: number;
  delta_90_10_effect?: number;
  has_heterogeneous_distributional_effects?: boolean;
  inequality_impact?: string;
  quantile_effects?: QuantileEffectItem[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface QTERequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids?: string[];
  quantiles?: number[];
  alpha_trim?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Causal DAG & Structure Learning Types ---
export interface DAGNodeInfo {
  index: number;
  name: string;
  in_degree: number;
  out_degree: number;
  total_degree: number;
  causal_role: string;
}

export interface DAGEdgeInfo {
  source_index: number;
  source_name: string;
  target_index: number;
  target_name: string;
  type: 'directed' | 'undirected';
  weight: number;
  direction: string;
}

export interface CausalDAGResult {
  status: string;
  message?: string;
  sample_size?: number;
  variables_count?: number;
  edges_count?: number;
  directed_edges_count?: number;
  undirected_edges_count?: number;
  root_causes?: string[];
  sink_outcomes?: string[];
  mediators?: string[];
  nodes?: DAGNodeInfo[];
  edges?: DAGEdgeInfo[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface CausalDAGRequest {
  question_ids: string[];
  alpha?: number;
  max_cond_size?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Marginal Structural Models (MSM) Types ---
export interface MSMWeightDiagnostics {
  mean: number;
  std: number;
  min: number;
  max: number;
  truncated_p1: number;
  truncated_p99: number;
}

export interface MSMAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  waves_count?: number;
  causal_effect_per_wave?: number;
  std_error?: number;
  z_statistic?: number;
  p_value?: number;
  ci_95_lower?: number;
  ci_95_upper?: number;
  naive_ols_effect?: number;
  naive_ols_p_value?: number;
  confounding_bias_pct?: number;
  confounding_verdict?: string;
  stabilized_weights_diagnostics?: MSMWeightDiagnostics;
  svg_chart?: string;
  apa_narrative?: string;
}

export interface MSMAnalysisRequest {
  treatment_question_ids: string[];
  confounder_question_ids: string[];
  outcome_question_id: string;
  wave_labels?: string[];
  scope?: 'all' | 'verified_clean';
}


// --- Generalized Estimating Equations (GEE) Types ---
export interface GEECoefficient {
  term: string;
  estimate: number;
  robust_se: number;
  naive_se: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface GEEAnalysisResult {
  status: string;
  message?: string;
  clusters_count?: number;
  observations_count?: number;
  family?: string;
  working_correlation_structure?: string;
  estimated_correlation_parameter?: number;
  dispersion_phi?: number;
  qic?: number;
  coefficients?: GEECoefficient[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface GEEAnalysisRequest {
  cluster_question_id: string;
  time_question_id: string;
  outcome_question_id: string;
  predictor_question_ids: string[];
  family?: 'gaussian' | 'binomial';
  corstr?: 'exchangeable' | 'ar1' | 'independent';
  scope?: 'all' | 'verified_clean';
}


// --- Exact Permutation & Randomization Inference Types ---
export interface RandomizationInferenceResult {
  status: string;
  message?: string;
  sample_size?: number;
  treated_count?: number;
  control_count?: number;
  permutations_count?: number;
  difference_in_means?: {
    observed_statistic: number;
    exact_p_value: number;
    is_significant: boolean;
  };
  difference_in_medians?: {
    observed_statistic: number;
    exact_p_value: number;
    is_significant: boolean;
  };
  wilcoxon_rank_sum?: {
    observed_statistic: number;
    exact_p_value: number;
    is_significant: boolean;
  };
  hodges_lehmann_shift?: {
    point_estimate: number;
    ci_95_lower: number;
    ci_95_upper: number;
  };
  asymptotic_welch_t_test?: {
    t_statistic: number;
    p_value: number;
  };
  svg_chart?: string;
  apa_narrative?: string;
}

export interface RandomizationInferenceRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  num_permutations?: number;
  alternative?: 'two-sided' | 'greater' | 'less';
  scope?: 'all' | 'verified_clean';
}

// --- Extreme Value Theory (EVT) & Survey Tail Risk Types ---
export interface EVTRiskMeasure {
  confidence_level: number;
  var_p: number;
  es_p?: number | null;
  is_infinite_mean?: boolean;
}

export interface EVTMeanExcessPoint {
  threshold: number;
  mean_excess: number;
  count: number;
}

export interface EVTAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  threshold?: number;
  exceedances_count?: number;
  exceedance_probability?: number;
  shape_xi?: number;
  se_shape_xi?: number;
  scale_sigma?: number;
  se_scale_sigma?: number;
  tail_classification?: string;
  tail_interpretation?: string;
  gof_ks_statistic?: number;
  gof_ks_p_value?: number;
  gof_passed?: boolean;
  risk_measures?: EVTRiskMeasure[];
  mean_excess_grid?: EVTMeanExcessPoint[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface EVTAnalysisRequest {
  metric_question_id: string;
  threshold_percentile?: number;
  custom_threshold?: number;
  alpha_levels?: number[];
  scope?: 'all' | 'verified_clean';
}

// --- Joint Modeling of Longitudinal & Survival Data Types ---
export interface DynamicSurvivalPrediction {
  time: number;
  surv_low: number;
  surv_mean: number;
  surv_high: number;
}

export interface JointModelAnalysisResult {
  status: string;
  message?: string;
  sample_size?: number;
  total_longitudinal_observations?: number;
  events_attrited_count?: number;
  censored_retained_count?: number;
  longitudinal_submodel?: {
    intercept_fixed: number;
    slope_fixed: number;
    residual_std_sigma_e: number;
    random_intercept_std: number;
    random_slope_std: number;
  };
  survival_submodel?: {
    association_alpha: number;
    se_alpha: number;
    z_statistic: number;
    p_value: number;
    hazard_ratio: number;
    ci_95_lower: number;
    ci_95_upper: number;
    is_significant: boolean;
  };
  attrition_diagnostics?: {
    is_non_ignorable: boolean;
    interpretation: string;
  };
  dynamic_predictions?: DynamicSurvivalPrediction[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface JointModelAnalysisRequest {
  subject_question_id: string;
  time_question_id: string;
  outcome_question_id: string;
  event_question_id?: string;
  event_time_question_id?: string;
  scope?: 'all' | 'verified_clean';
}


// --- Conformal Prediction & Distribution-Free Risk Intervals Types ---
export interface ConformalCalibrationPoint {
  alpha: number;
  nominal_coverage: number;
  conformal_coverage: number;
  gaussian_coverage: number;
  quantile_cutoff: number;
}

export interface ConformalSamplePrediction {
  test_index: number;
  actual_y: number;
  predicted_y: number;
  lower_bound: number;
  upper_bound: number;
  interval_width: number;
  is_covered: boolean;
}

export interface ConformalPredictionResult {
  status: string;
  message?: string;
  method?: string;
  target_field?: string;
  feature_fields?: string[];
  sample_sizes?: {
    total: number;
    train: number;
    calibration: number;
    test: number;
  };
  parameters?: {
    nominal_coverage: number;
    alpha: number;
    conformal_quantile: number;
    finite_sample_lower_guarantee: number;
    finite_sample_upper_bound: number;
  };
  evaluation_metrics?: {
    conformal_coverage: number;
    gaussian_coverage: number;
    conformal_mean_width: number;
    conformal_median_width: number;
    conformal_iqr_width: number;
    gaussian_mean_width: number;
    efficiency_gain_ratio: number;
  };
  calibration_curve?: ConformalCalibrationPoint[];
  sample_predictions?: ConformalSamplePrediction[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface ConformalPredictionRequest {
  target_question_id: string;
  feature_question_ids: string[];
  alpha?: number;
  method?: 'split_conformal' | 'locally_weighted';
  calib_fraction?: number;
  test_fraction?: number;
  clamp_min?: number;
  clamp_max?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Multilevel Structural Equation Modeling (MSEM) Types ---
export interface MSEMSubmodelResult {
  a_path: number;
  se_a: number;
  p_a: number;
  b_path: number;
  se_b: number;
  p_b: number;
  c_prime_path: number;
  se_c_prime: number;
  indirect_effect: number;
  ci_95_lower: number;
  ci_95_upper: number;
  p_indirect: number;
  is_significant: boolean;
}

export interface MSEMAnalysisResult {
  status: string;
  message?: string;
  cluster_field?: string;
  x_field?: string;
  m_field?: string;
  y_field?: string;
  sample_diagnostics?: {
    n_total: number;
    n_clusters: number;
    avg_cluster_size: number;
    cluster_size_min: number;
    cluster_size_max: number;
  };
  intraclass_correlations?: {
    icc_x: number;
    icc_m: number;
    icc_y: number;
    interpretation: string;
  };
  level1_within_submodel?: MSEMSubmodelResult;
  level2_between_submodel?: MSEMSubmodelResult;
  conflation_test?: {
    diff_between_within: number;
    ci_95_lower: number;
    ci_95_upper: number;
    is_conflated: boolean;
    interpretation: string;
  };
  fit_indices?: {
    cfi: number;
    rmsea: number;
    srmr_within: number;
    srmr_between: number;
  };
  svg_chart?: string;
  apa_narrative?: string;
}

export interface MSEMAnalysisRequest {
  cluster_question_id: string;
  x_question_id: string;
  m_question_id: string;
  y_question_id: string;
  n_mc_sims?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Targeted Maximum Likelihood Estimation (TMLE) Types ---
export interface TMLEComparisonEstimator {
  name: string;
  ate: number;
  ci_lower: number;
  ci_upper: number;
  bias_risk: string;
}

export interface TMLEAnalysisResult {
  status: string;
  message?: string;
  treatment_field?: string;
  outcome_field?: string;
  covariate_fields?: string[];
  sample_diagnostics?: {
    n_total: number;
    n_treated: number;
    n_control: number;
    treated_ratio: number;
    min_propensity_score: number;
    max_propensity_score: number;
    positivity_violation_risk: boolean;
  };
  targeted_parameters?: {
    fluctuation_epsilon: number;
    initial_gcomp_ate: number;
    targeted_tmle_ate: number;
    se_tmle: number;
    z_statistic: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
    is_significant: boolean;
  };
  estimator_comparisons?: TMLEComparisonEstimator[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface TMLEAnalysisRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  gbound?: number;
  target_treatment_val?: any;
  control_treatment_val?: any;
  scope?: 'all' | 'verified_clean';
}


// --- Synthetic Difference-in-Differences (SDID) Types ---
export interface SDIDTrajectoryPoint {
  time: string;
  is_post: boolean;
  treated_actual: number;
  synthetic_control: number;
  counterfactual_parallel: number;
}

export interface SDIDDonorWeight {
  unit: string;
  weight: number;
}

export interface SDIDTimeWeight {
  time: string;
  weight: number;
}

export interface SDIDAnalysisResult {
  status: string;
  message?: string;
  unit_field?: string;
  time_field?: string;
  outcome_field?: string;
  treated_units?: string[];
  treatment_start_time?: string;
  sample_diagnostics?: {
    n_treated_units: number;
    n_control_units: number;
    t_pre_periods: number;
    t_post_periods: number;
    total_panel_records: number;
  };
  sdid_estimates?: {
    tau_sdid: number;
    se_sdid: number;
    z_statistic: number;
    p_value: number;
    ci_95_lower: number;
    ci_95_upper: number;
    is_significant: boolean;
  };
  comparison_estimates?: {
    tau_did_unweighted: number;
    tau_scm_standard: number;
    tau_sdid_doubly_weighted: number;
  };
  top_donor_weights?: SDIDDonorWeight[];
  time_weights?: SDIDTimeWeight[];
  time_trajectories?: SDIDTrajectoryPoint[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface SDIDAnalysisRequest {
  unit_question_id: string;
  time_question_id: string;
  outcome_question_id: string;
  treated_units: string[];
  treatment_start_time: any;
  n_placebo_reps?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Generalized Causal Forest (GRF; Athey, Tibshirani & Wager 2019) Types ---
export interface CausalForestVariableImportance {
  feature: string;
  importance: number;
  relative_pct: number;
}

export interface CausalForestBin {
  bin_start: number;
  bin_end: number;
  bin_label: string;
  count: number;
  pct: number;
}

export interface CausalForestAnalysisResult {
  status: string;
  message?: string;
  treatment_field?: string;
  outcome_field?: string;
  feature_fields?: string[];
  sample_diagnostics?: {
    n_total: number;
    n_treated: number;
    n_control: number;
    p_treated: number;
    n_features: number;
    n_trees: number;
  };
  cate_summary?: {
    mean_ate: number;
    se_ate: number;
    ci_95_lower: number;
    ci_95_upper: number;
    median_cate: number;
    std_cate: number;
    iqr_cate: number;
    min_cate: number;
    max_cate: number;
    p_positive_effect: number;
    heterogeneity_variance: number;
    heterogeneity_p_value: number;
    has_heterogeneity: boolean;
  };
  variable_importance?: CausalForestVariableImportance[];
  cate_distribution?: CausalForestBin[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface CausalForestAnalysisRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  feature_question_ids: string[];
  n_trees?: number;
  min_leaf_size?: number;
  target_treatment_val?: any;
  scope?: 'all' | 'verified_clean';
}



// --- Causal Mediation Sensitivity Analysis (Imai, Keele & Tingley 2010) Types ---
export interface CausalMediationPathEstimate {
  coefficient: number;
  se: number;
  z_stat: number;
  p_value: number;
  is_significant: boolean;
}

export interface CausalMediationSensitivityPoint {
  rho: number;
  acme: number;
  se: number;
  ci_lower: number;
  ci_upper: number;
  is_zero_in_ci: boolean;
}

export interface CausalMediationSensitivityResult {
  status: string;
  message?: string;
  treatment_field?: string;
  mediator_field?: string;
  outcome_field?: string;
  covariate_fields?: string[];
  sample_diagnostics?: {
    n_total: number;
    n_treated: number;
    n_control: number;
    mean_mediator: number;
    sd_mediator: number;
    mean_outcome: number;
    sd_outcome: number;
    r_squared_mediator_model: number;
    r_squared_outcome_model: number;
  };
  path_estimates?: {
    path_a: CausalMediationPathEstimate;
    path_b: CausalMediationPathEstimate;
    path_c_prime: CausalMediationPathEstimate;
  };
  baseline_effects?: {
    acme: number;
    se_acme: number;
    ci_95_lower: number;
    ci_95_upper: number;
    z_stat: number;
    p_value: number;
    is_significant: boolean;
    ade: number;
    se_ade: number;
    p_ade: number;
    total_effect: number;
    proportion_mediated: number;
  };
  sensitivity_analysis?: {
    critical_rho_threshold: number;
    r2_star_product: number;
    robustness_level: string;
    robustness_badge: string;
    robustness_description: string;
    sensitivity_curve: CausalMediationSensitivityPoint[];
  };
  svg_chart?: string;
  apa_narrative?: string;
}

export interface CausalMediationSensitivityRequest {
  treatment_question_id: string;
  mediator_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  target_treatment_val?: any;
  scope?: 'all' | 'verified_clean';
}


// --- Dynamic Time Warping (DTW) Trajectory Clustering Types ---
export interface DTWClusterInfo {
  cluster_id: number;
  color: string;
  size: number;
  percentage: number;
  archetype_title: string;
  within_cluster_dispersion: number;
  mean_trajectory: number[];
  medoid_trajectory: number[];
}

export interface DTWClusteringResult {
  status: string;
  message?: string;
  time_series_fields?: string[];
  time_labels?: string[];
  sample_diagnostics?: {
    n_total: number;
    n_time_points: number;
    n_clusters: number;
    window_radius: number;
    mean_silhouette_score: number;
  };
  clusters?: DTWClusterInfo[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface DTWClusteringRequest {
  time_series_question_ids: string[];
  time_labels?: string[];
  n_clusters?: number;
  window_radius?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Causal Interaction Trees & Honest Subgroup Identification (Athey & Imbens 2016) Types ---
export interface CausalTreeSubgroup {
  leaf_id: number;
  rule: string;
  n_total: number;
  n_treated: number;
  n_control: number;
  tau_subgroup: number;
  se: number;
  ci_lower: number;
  ci_upper: number;
  p_value: number;
  is_significant: boolean;
  category: string;
}

export interface CausalTreeAnalysisResult {
  status: string;
  message?: string;
  treatment_field?: string;
  outcome_field?: string;
  feature_fields?: string[];
  sample_diagnostics?: {
    n_total: number;
    n_training_structure: number;
    n_estimation_honest: number;
    n_treated_total: number;
    n_control_total: number;
    n_subgroups: number;
    ate_overall: number;
  };
  subgroups?: CausalTreeSubgroup[];
  tree_structure?: any;
  svg_chart?: string;
  apa_narrative?: string;
}

export interface CausalTreeAnalysisRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  feature_question_ids: string[];
  max_depth?: number;
  min_leaf_size?: number;
  target_treatment_val?: any;
  scope?: 'all' | 'verified_clean';
}


// --- Multiple Testing Correction & False Discovery Rate (FDR) (Benjamini & Hochberg 1995, Storey 2002) Types ---
export interface FDRCorrectionItem {
  rank: number;
  hypothesis: string;
  raw_p_value: number;
  bh_q_value: number;
  by_adjusted_p: number;
  bonferroni_p: number;
  bh_critical_value: number;
  is_significant_bh: boolean;
  is_significant_bonferroni: boolean;
  decision_status: 'SURVIVES_BONFERRONI' | 'DISCOVERED_BH_FDR' | 'FILTERED_FALSE_POSITIVE' | 'NON_SIGNIFICANT' | string;
  decision_badge: string;
}

export interface MultipleTestingFDRResult {
  status: string;
  message?: string;
  sample_diagnostics?: {
    total_hypotheses_m: number;
    fdr_target_q: number;
    estimated_pi_0_null_proportion: number;
    raw_significant_count: number;
    bh_fdr_significant_count: number;
    by_fdr_significant_count: number;
    bonferroni_significant_count: number;
    rescued_by_bh_count: number;
    filtered_false_positives_count: number;
  };
  corrections?: FDRCorrectionItem[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface MultipleTestingFDRRequest {
  question_ids?: string[];
  custom_p_values?: number[];
  custom_labels?: string[];
  fdr_q?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Bayesian Structural Equation Modeling (BSEM) (Muthén & Asparouhov 2012) Types ---
export interface BSEMStructuralPath {
  source_factor: string;
  target_factor: string;
  posterior_mean: number;
  posterior_sd: number;
  ci_lower: number;
  ci_upper: number;
  gelman_rubin_r_hat: number;
  effective_sample_size: number;
  mcse: number;
  bayesian_p_value: number;
  is_significant: boolean;
  convergence_status: string;
}

export interface BSEMLoadingItem {
  item_id: string;
  item_title: string;
  factor_name: string;
  is_primary: boolean;
  prior_type: string;
  posterior_mean: number;
  posterior_sd: number;
  ci_lower: number;
  ci_upper: number;
}

export interface BSEMPriorSensitivityItem {
  prior_sd: number;
  prior_variance: number;
  posterior_mean_beta: number;
  absolute_drift_from_baseline: number;
}

export interface BSEMResult {
  status: string;
  message?: string;
  sample_diagnostics?: {
    n_observations: number;
    n_factors: number;
    n_items: number;
    n_chains: number;
    n_iterations: number;
    n_burnin: number;
    prior_cross_loading_sd: number;
    posterior_predictive_p_value: number;
    model_fit_status: string;
    model_fit_badge: string;
    prior_robustness_status: string;
    prior_robustness_badge: string;
  };
  structural_paths?: BSEMStructuralPath[];
  loadings?: BSEMLoadingItem[];
  prior_sensitivity?: BSEMPriorSensitivityItem[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface BSEMRequest {
  measurement_spec: Record<string, string[]>;
  structural_regressions?: Array<{ source: string; target: string }>;
  prior_cross_loading_sd?: number;
  n_iterations?: number;
  n_burnin?: number;
  n_chains?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Gaussian Copula Endogeneity Estimation (Park & Gupta 2012) Types ---
export interface GaussianCopulaResult {
  status: string;
  message?: string;
  sample_diagnostics?: {
    n_observations: number;
    endogenous_variable: string;
    outcome_variable: string;
    control_variables: string[];
    jarque_bera_stat: number;
    jarque_bera_p_value: number;
    skewness: number;
    excess_kurtosis: number;
    non_normality_satisfied: boolean;
    copula_vif: number;
    endogeneity_status: string;
    endogeneity_badge: string;
  };
  naive_ols?: {
    beta: number;
    se: number;
    t_stat: number;
    ci_lower: number;
    ci_upper: number;
    r_squared: number;
  };
  copula_corrected?: {
    beta_copula: number;
    se_bootstrap: number;
    ci_lower_bootstrap: number;
    ci_upper_bootstrap: number;
    copula_rho_parameter: number;
    se_copula_rho: number;
    t_rho: number;
    p_value_rho: number;
    is_endogeneity_significant: boolean;
    endogeneity_bias_gap: number;
    percentage_bias: number;
    r_squared: number;
  };
  svg_chart?: string;
  apa_narrative?: string;
}

export interface GaussianCopulaRequest {
  endogenous_question_id: string;
  outcome_question_id: string;
  control_question_ids?: string[];
  n_bootstraps?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Dynamic Factor Modeling (DFM) (Stock & Watson 2002) Types ---
export interface DFMTrajectoryPoint {
  wave_index: number;
  wave_label: string;
  sample_size: number;
  filtered_state: number;
  smoothed_factor: number;
  standard_error: number;
  ci_lower_95: number;
  ci_upper_95: number;
}

export interface DFMVarianceDecompositionItem {
  question_id: string;
  title: string;
  loading_lambda: number;
  common_variance_share_r2: number;
  idiosyncratic_noise_share: number;
  signal_to_noise_ratio: number;
}

export interface DynamicFactorModelResult {
  status: string;
  message?: string;
  sample_diagnostics?: {
    total_waves_t: number;
    total_indicators_p: number;
    total_observations: number;
    n_dynamic_factors: number;
    ar1_persistence: number;
    overall_signal_variance_share: number;
    state_space_filter: string;
  };
  trajectory?: DFMTrajectoryPoint[];
  variance_decomposition?: DFMVarianceDecompositionItem[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface DynamicFactorModelRequest {
  indicator_question_ids: string[];
  wave_question_id?: string;
  time_field?: string;
  n_factors?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Extreme Bound Analysis (EBA) Interfaces ---
export interface EBASpecificationItem {
  model_id: number;
  beta: number;
  se: number;
  t_stat: number;
  p_value: number;
  r_squared: number;
  ci_lower: number;
  ci_upper: number;
  is_significant: boolean;
  controls: string[];
  cdf_zero: number;
}

export interface EBASummary {
  n_samples: number;
  total_models_evaluated: number;
  candidate_controls_pool_size: number;
  mean_beta: number;
  median_beta: number;
  std_beta: number;
  min_beta: number;
  max_beta: number;
  leamer_lower_bound: number;
  leamer_upper_bound: number;
  leamer_verdict: 'ROBUST_POSITIVE' | 'ROBUST_NEGATIVE' | 'FRAGILE';
  leamer_label: string;
  sala_i_martin_cdf: number;
  sala_i_martin_weighted_cdf: number;
  sala_i_martin_verdict: 'ROBUST' | 'FRAGILE';
  sala_i_martin_label: string;
  significant_models_fraction: number;
  positive_models_fraction: number;
  sig_positive_models: number;
  sig_negative_models: number;
  non_significant_models: number;
  min_beta_model_controls: string[];
  max_beta_model_controls: string[];
}

export interface ExtremeBoundsResult {
  status: string;
  message?: string;
  summary?: EBASummary;
  specifications_sample?: EBASpecificationItem[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface ExtremeBoundsRequest {
  focus_question_id: string;
  outcome_question_id: string;
  candidate_question_ids: string[];
  free_question_ids?: string[];
  max_controls_per_model?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Spatial Econometrics & Moran's I Interfaces ---
export interface SpatialEconometricsImpact {
  variable: string;
  coefficient: number;
  direct_impact: number;
  indirect_spillover_impact: number;
  total_impact: number;
  spillover_ratio: number;
}

export interface SpatialEconometricsResult {
  status: string;
  message?: string;
  morans_i?: {
    morans_i: number;
    expected_i: number;
    variance_i: number;
    standard_error: number;
    z_score: number;
    p_value: number;
    is_significant: boolean;
    classification: string;
    interpretation: string;
    quadrants: {
      high_high: number;
      low_low: number;
      high_low: number;
      low_high: number;
    };
  };
  lm_diagnostics?: {
    lm_error_stat: number;
    lm_error_p_value: number;
    lm_lag_stat: number;
    lm_lag_p_value: number;
    recommended_model: string;
    advice: string;
  };
  baseline_ols?: {
    r_squared: number;
    sigma_squared: number;
    coefficients: number[];
    standard_errors: number[];
    p_values: number[];
  };
  spatial_lag_model?: {
    rho: number;
    rho_standard_error: number;
    rho_z_stat: number;
    rho_p_value: number;
    is_rho_significant: boolean;
    intercept: number;
    r_squared: number;
    impact_decomposition: SpatialEconometricsImpact[];
  };
  svg_chart?: string;
  apa_narrative?: string;
}

export interface SpatialEconometricsRequest {
  outcome_question_id: string;
  covariate_question_ids?: string[];
  lat_field?: string;
  lon_field?: string;
  weights_type?: string;
  knn_k?: number;
  distance_power?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Instrumental Variable Quantile Regression (IV-QR) Interfaces ---
export interface IVQRQuantileItem {
  quantile: number;
  iv_qr_estimate: number;
  ci_lower: number;
  ci_upper: number;
  is_significant: boolean;
  exogenous_qr_estimate: number;
  exogenous_qr_se: number;
  endogeneity_bias_gap: number;
  min_wald_stat: number;
}

export interface IVQRSummary {
  n_samples: number;
  instrument_strength: 'STRONG_INSTRUMENT' | 'WEAK_INSTRUMENT';
  instrument_f_stat: number;
  strength_warning: string;
  ols_estimate: number;
  ols_se: number;
  tsls_estimate: number;
  tsls_se: number;
  interquantile_spread_90_10: number;
  has_quantile_heterogeneity: boolean;
  chi2_critical_value: number;
}

export interface IVQuantileRegressionResult {
  status: string;
  message?: string;
  summary?: IVQRSummary;
  quantile_estimates?: IVQRQuantileItem[];
  svg_chart?: string;
  apa_narrative?: string;
}

export interface IVQuantileRegressionRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  instrument_question_id: string;
  covariate_question_ids?: string[];
  quantiles?: number[];
  grid_points?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Choice-Based Conjoint with Hierarchical Bayes (HB-CBC) Interfaces ---
export interface ConjointHBDiagnostics {
  n_respondents: number;
  n_total_observations: number;
  n_parameters: number;
  mcmc_draws: number;
  mcmc_burn_in: number;
  mcmc_acceptance_rate: number;
  log_likelihood: number;
  null_log_likelihood: number;
  mcfadden_pseudo_r2: number;
  hit_rate_pct: number;
  rmse: number;
}

export interface ConjointHBAttributeImportance {
  attribute: string;
  relative_importance_pct: number;
  importance_sd_pct: number;
}

export interface ConjointHBPartWorth {
  attribute: string;
  level: string;
  part_worth_utility: number;
  bci_95_lower: number;
  bci_95_upper: number;
  is_reference: boolean;
}

export interface ConjointHBWTPItem {
  attribute: string;
  level: string;
  utility_gain_vs_ref: number;
  wtp_currency: number;
}

export interface ConjointHBWTP {
  price_attribute: string;
  price_range: number[];
  marginal_utility_of_price: number;
  wtp_estimates: ConjointHBWTPItem[];
}

export interface ConjointHBSimulationScenario {
  scenario_name: string;
  attributes: Record<string, any>;
  predicted_choice_share_pct: number;
}

export interface ConjointHBResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: ConjointHBDiagnostics;
  attribute_importance?: ConjointHBAttributeImportance[];
  attribute_details?: Record<string, any>;
  part_worth_utilities?: ConjointHBPartWorth[];
  willingness_to_pay?: ConjointHBWTP;
  market_simulations?: ConjointHBSimulationScenario[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ConjointHBRequest {
  attributes_config: Record<string, string[]>;
  tasks_data?: Array<{
    respondent_id?: string;
    task_id?: string;
    attributes: Record<string, any>;
    chosen: number;
  }>;
  choice_question_id?: string;
  profile_attribute_mapping?: Record<string, string>;
  price_attribute?: string;
  simulation_scenarios?: Array<{
    name?: string;
    attributes: Record<string, any>;
  }>;
  n_draws?: number;
  burn_in?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Fractional Response Regression (Papke & Wooldridge 1996, 2008) Interfaces ---
export interface FractionalResponseCoefficient {
  variable: string;
  is_intercept: boolean;
  estimate: number;
  robust_se: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  average_marginal_effect?: number;
  ame_se?: number;
  marginal_effect_at_mean?: number;
  is_significant: boolean;
}

export interface FractionalResponseDiagnostics {
  n_samples: number;
  n_covariates: number;
  link_function: string;
  boundary_zeros: number;
  boundary_ones: number;
  interior_observations: number;
  converged: boolean;
  quasi_log_likelihood: number;
  null_log_likelihood: number;
  mcfadden_pseudo_r2: number;
  qaic: number;
  qbic: number;
  qmle_rmse: number;
  ols_rmse: number;
  ols_out_of_bounds_count: number;
  reset_test_stat: number;
  reset_test_pval: number;
  reset_passed: boolean;
}

export interface FractionalResponseResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: FractionalResponseDiagnostics;
  coefficients?: FractionalResponseCoefficient[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface FractionalResponseRequest {
  outcome_question_id: string;
  covariate_question_ids: string[];
  link?: 'logit' | 'probit' | 'cloglog';
  scale_from_percentage?: boolean;
  scope?: 'all' | 'verified_clean';
}


// --- Multidimensional Item Response Theory (MIRT; Reckase 2009) Interfaces ---
export interface MIRTItemParameter {
  item_name: string;
  intercept_d: number;
  slopes_a: number[];
  mdisc: number;
  mdisc_classification: string;
  mid: number;
  directional_angles_deg: number[];
  item_p_value: number;
  item_chi_square: number;
  item_rmsea: number;
  item_fit_verdict: string;
}

export interface MIRTDiagnostics {
  n_samples: number;
  n_items: number;
  n_dimensions: number;
  dimension_labels: string[];
  converged: boolean;
  em_iterations: number;
  log_likelihood: number;
  aic: number;
  bic: number;
  eap_trait_means: number[];
  eap_trait_sds: number[];
  trait_correlations: Array<{
    dim1: string;
    dim2: string;
    correlation_r: number;
  }>;
}

export interface MIRTResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: MIRTDiagnostics;
  item_parameters?: MIRTItemParameter[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface MIRTRequest {
  item_question_ids: string[];
  n_dimensions?: number;
  dimension_names?: string[];
  max_em_iter?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Heckman Two-Step Sample Selection Model (Heckman 1979) Interfaces ---
export interface HeckmanCoefficientComparison {
  variable: string;
  is_intercept: boolean;
  ols_estimate: number;
  ols_se: number;
  heckman_estimate: number;
  heckman_se: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  selection_bias_gap: number;
  is_significant: boolean;
}

export interface HeckmanDiagnostics {
  n_total_observations: number;
  n_selected_observed: number;
  n_unselected_censored: number;
  selection_rate_pct: number;
  inverse_mills_ratio_coef: number;
  imr_se: number;
  imr_t_statistic: number;
  imr_p_value: number;
  rho_correlation: number;
  sigma_epsilon: number;
  has_selection_bias: boolean;
  selection_verdict: string;
  exclusion_restrictions: string[];
  has_valid_exclusion: boolean;
}

export interface HeckmanSelectionResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: HeckmanDiagnostics;
  coefficients_comparison?: HeckmanCoefficientComparison[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface HeckmanSelectionRequest {
  outcome_question_id: string;
  selection_indicator_question_id?: string;
  outcome_covariate_question_ids: string[];
  exclusion_restriction_question_ids?: string[];
  scope?: 'all' | 'verified_clean';
}


// --- Stochastic Frontier Analysis (SFA; Aigner et al. 1977; JLMS 1982) Interfaces ---
export interface SFACoefficient {
  variable: string;
  is_intercept: boolean;
  frontier_coefficient: number;
  elasticity_estimate: number;
  standard_error: number;
  t_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface SFAIndividualEfficiency {
  unit_index: number;
  technical_inefficiency_u: number;
  technical_efficiency_pct: number;
}

export interface SFADiagnostics {
  n_units: number;
  n_inputs: number;
  log_transformed: boolean;
  converged: boolean;
  sfa_log_likelihood: number;
  ols_log_likelihood: number;
  lr_test_stat: number;
  lr_test_pval: number;
  has_inefficiency: boolean;
  inefficiency_verdict: string;
  sigma_total: number;
  sigma_u_inefficiency: number;
  sigma_v_noise: number;
  lambda_ratio: number;
  gamma_variance_share: number;
  ols_residual_skewness: number;
  returns_to_scale: number;
  rts_verdict: string;
  mean_technical_efficiency_pct: number;
  median_technical_efficiency_pct: number;
  min_technical_efficiency_pct: number;
  max_technical_efficiency_pct: number;
  std_technical_efficiency_pct: number;
}

export interface SFAInefficiencySummary {
  mean_efficiency: number;
  median_efficiency: number;
  min_efficiency: number;
  max_efficiency: number;
  efficiency_distribution_quartiles: {
    q25: number;
    median: number;
    q75: number;
  };
}

export interface StochasticFrontierResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: SFADiagnostics;
  coefficients?: SFACoefficient[];
  inefficiency_summary?: SFAInefficiencySummary;
  individual_efficiency_sample?: SFAIndividualEfficiency[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface StochasticFrontierRequest {
  output_question_id: string;
  input_question_ids: string[];
  log_transform?: boolean;
  scope?: 'all' | 'verified_clean';
}


// --- Zero-Inflated Count Models (ZIP & ZINB; Lambert 1992, Greene 1994) Interfaces ---
export interface ZeroInflatedCountCoefficient {
  variable: string;
  is_intercept: boolean;
  coefficient: number;
  incidence_rate_ratio_irr: number;
  standard_error: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  irr_95_lower: number;
  irr_95_upper: number;
  is_significant: boolean;
}

export interface ZeroInflatedLogitCoefficient {
  variable: string;
  is_intercept: boolean;
  logit_coefficient: number;
  odds_ratio: number;
  standard_error: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  or_95_lower: number;
  or_95_upper: number;
  is_significant: boolean;
}

export interface ZeroInflatedDiagnostics {
  sample_size: number;
  zero_observations_count: number;
  zero_percentage: number;
  sample_mean: number;
  sample_variance: number;
  dispersion_ratio: number;
  converged: boolean;
  model_type: string;
  log_likelihood_zi: number;
  log_likelihood_standard_poisson: number;
  aic_zi: number;
  bic_zi: number;
  aic_standard_poisson: number;
  bic_standard_poisson: number;
  vuong_test_z: number;
  vuong_test_p: number;
  vuong_favors_zero_inflation: boolean;
  vuong_verdict: string;
  dispersion_parameter_alpha?: number | null;
}

export interface ZeroInflatedFrequencyDistribution {
  counts: number[];
  observed_frequencies: number[];
  predicted_frequencies: number[];
}

export interface ZeroInflatedResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: ZeroInflatedDiagnostics;
  count_model_coefficients?: ZeroInflatedCountCoefficient[];
  inflation_model_coefficients?: ZeroInflatedLogitCoefficient[];
  frequency_distribution?: ZeroInflatedFrequencyDistribution;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ZeroInflatedRequest {
  count_question_id: string;
  covariate_question_ids: string[];
  inflation_covariate_question_ids?: string[];
  model_type?: 'ZIP' | 'ZINB';
  scope?: 'all' | 'verified_clean';
}


// --- Latent Moderated Structural Equations (LMS / QML; Klein & Moosbrugger 2000) Interfaces ---
export interface LMSCoefficient {
  parameter: string;
  label: string;
  estimate: number;
  standard_error: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface LMSSimpleSlope {
  level_label: string;
  moderator_value: number;
  simple_slope: number;
  standard_error: number;
  z_statistic: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  is_significant: boolean;
}

export interface LMSDiagnostics {
  sample_size: number;
  converged: boolean;
  structural_r2: number;
  cohen_f2_effect_size: number;
  f2_classification: string;
  attenuation_bias_gap_pct: number;
  naive_observed_interaction_gamma: number;
  latent_interaction_gamma: number;
  latent_predictor_reliability_alpha: number;
  latent_moderator_reliability_alpha: number;
  latent_outcome_reliability_alpha: number;
  latent_correlation_xi1_xi2: number;
  has_significant_moderation: boolean;
  johnson_neyman_cutoffs: number[];
}

export interface LatentModerationResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: LMSDiagnostics;
  coefficients?: LMSCoefficient[];
  simple_slopes?: LMSSimpleSlope[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface LatentModerationRequest {
  predictor_item_ids: string[];
  moderator_item_ids: string[];
  outcome_item_ids: string[];
  scope?: 'all' | 'verified_clean';
}


// --- Endogenous Switching Regression (ESR; Maddala 1983, Lokshin & Sajaia 2004) Interfaces ---
export interface ESRCoefficient {
  variable: string;
  is_intercept: boolean;
  regime1_estimate: number;
  regime1_se: number;
  regime1_z: number;
  regime1_p: number;
  regime1_ci_95: [number, number];
  regime0_estimate: number;
  regime0_se: number;
  regime0_z: number;
  regime0_p: number;
  regime0_ci_95: [number, number];
  coefficient_difference: number;
}

export interface ESRTreatmentEffectItem {
  estimate: number;
  standard_error: number;
  t_statistic: number;
  p_value: number;
  ci_95: [number, number];
}

export interface ESRTreatmentEffects {
  att: ESRTreatmentEffectItem;
  atu: ESRTreatmentEffectItem;
  transitional_heterogeneity: number;
}

export interface ESRDiagnostics {
  total_sample: number;
  regime1_count: number;
  regime0_count: number;
  treatment_rate_pct: number;
  converged: boolean;
  fiml_log_likelihood: number;
  lr_test_independence_stat: number;
  lr_test_independence_pval: number;
  has_endogenous_selection: boolean;
  rho_1_treated_selection: number;
  rho_1_se: number;
  rho_0_untreated_selection: number;
  rho_0_se: number;
  sigma_1_treated: number;
  sigma_0_untreated: number;
  average_treatment_effect_treated_att: number;
  att_se: number;
  att_p_value: number;
  average_treatment_effect_untreated_atu: number;
  atu_se: number;
  atu_p_value: number;
  transitional_heterogeneity: number;
  base_heterogeneity_treated: number;
  base_heterogeneity_untreated: number;
}

export interface EndogenousSwitchingResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: ESRDiagnostics;
  treatment_effects?: ESRTreatmentEffects;
  coefficients?: ESRCoefficient[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface EndogenousSwitchingRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  instrument_question_ids?: string[];
  scope?: 'all' | 'verified_clean';
}


// --- Generalized Propensity Score (GPS) Dose-Response (Hirano & Imbens 2004) Interfaces ---
export interface GPSDosePoint {
  dosage_t: number;
  expected_outcome_mu: number;
  standard_error: number;
  ci_95_lower: number;
  ci_95_upper: number;
}

export interface GPSMarginalEffectPoint {
  dosage_t: number;
  marginal_treatment_effect: number;
  standard_error: number;
  ci_95_lower: number;
  ci_95_upper: number;
}

export interface GPSDiagnostics {
  sample_size: number;
  n_covariates: number;
  treatment_min: number;
  treatment_max: number;
  treatment_mean: number;
  treatment_sd: number;
  treatment_model_r2: number;
  treatment_model_sigma: number;
  outcome_model_r2: number;
  optimal_dosage_peak: number;
  peak_expected_outcome: number;
  baseline_expected_outcome: number;
  net_causal_gain_at_optimal: number;
}

export interface GPSDoseResponseResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: GPSDiagnostics;
  dose_response_curve?: GPSDosePoint[];
  marginal_effects_curve?: GPSMarginalEffectPoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface GPSDoseResponseRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  n_grid_points?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Causal Discovery DAG (LiNGAM & ANM - Shimizu et al. 2006; Hoyer et al. 2009) ---
export interface CausalEdge {
  from: string;
  to: string;
  path_coefficient: number;
  total_effect: number;
  t_statistic: number;
  p_value: number;
  is_significant: boolean;
}

export interface CausalNonGaussianityTest {
  variable: string;
  skewness: number;
  excess_kurtosis: number;
  omnibus_stat: number;
  p_value: number;
  is_non_gaussian: boolean;
}

export interface CausalANMDiagnostic {
  edge: string;
  residual_cause_corr: number;
  independence_p_value: number;
  anm_noise_independent: boolean;
}

export interface CausalMatrixData {
  variables: string[];
  matrix: number[][];
}

export interface CausalDiscoveryDiagnostics {
  N: number;
  p: number;
  fastica_converged: boolean;
  non_gaussian_variables_count: number;
  total_directed_edges: number;
  prune_threshold: number;
}

export interface CausalDiscoveryResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: CausalDiscoveryDiagnostics;
  causal_order?: string[];
  directed_edges?: CausalEdge[];
  non_gaussianity_tests?: CausalNonGaussianityTest[];
  anm_diagnostics?: CausalANMDiagnostic[];
  adjacency_matrix?: CausalMatrixData;
  total_effects_matrix?: CausalMatrixData;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface CausalDiscoveryRequest {
  variable_question_ids: string[];
  prune_threshold?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Bayesian Additive Regression Trees (BART) Causal (Chipman et al. 2010; Hill 2011) ---
export interface BARTTreatmentEffectMetric {
  estimate: number;
  se: number;
  ci_95_lower: number;
  ci_95_upper: number;
  p_value?: number;
}

export interface BARTTreatmentEffects {
  ate: BARTTreatmentEffectMetric;
  att: BARTTreatmentEffectMetric;
  atu: BARTTreatmentEffectMetric;
}

export interface BARTITEDistribution {
  p05: number;
  p25: number;
  median: number;
  p75: number;
  p95: number;
  sd_tau: number;
  sd_tau_ci_lower: number;
  sd_tau_ci_upper: number;
}

export interface BARTVariableImportance {
  covariate: string;
  split_count: number;
  relative_importance: number;
  is_primary_moderator: boolean;
}

export interface BARTSubgroupCATE {
  moderator: string;
  subgroup: string;
  n_respondents: number;
  cate_estimate: number;
  se: number;
  ci_95_lower: number;
  ci_95_upper: number;
}

export interface BARTCausalDiagnostics {
  N: number;
  n_treated: number;
  n_control: number;
  n_covariates: number;
  n_trees: number;
  n_posterior_samples: number;
  has_significant_heterogeneity: boolean;
}

export interface BARTCausalResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: BARTCausalDiagnostics;
  treatment_effects?: BARTTreatmentEffects;
  ite_distribution?: BARTITEDistribution;
  variable_importance?: BARTVariableImportance[];
  subgroup_cate?: BARTSubgroupCATE[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface BARTCausalRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  n_trees?: number;
  n_samples?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Conjoint Analysis & Discrete Choice Experiment (DCE - McFadden 1974; Train 2009) ---
export interface ConjointPartWorth {
  attribute: string;
  part_worth_utility: number;
  se: number;
  t_stat: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  range_utility: number;
  relative_importance_pct: number;
  is_significant: boolean;
}

export interface ConjointWTP {
  attribute: string;
  wtp_estimate: number;
  wtp_se: number;
  wtp_ci_lower: number;
  wtp_ci_upper: number;
  unit: string;
}

export interface ConjointDiagnostics {
  N: number;
  n_chosen: number;
  n_rejected: number;
  n_attributes: number;
  mcfadden_pseudo_r2: number;
  log_likelihood: number;
  null_log_likelihood: number;
  lr_test_stat: number;
  lr_test_p_value: number;
  aic: number;
  bic: number;
  converged: boolean;
}

export interface ConjointChoiceResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: ConjointDiagnostics;
  part_worth_utilities?: ConjointPartWorth[];
  willingness_to_pay?: ConjointWTP[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ConjointChoiceRequest {
  choice_question_id: string;
  attribute_question_ids: string[];
  price_question_id?: string;
  price_unit?: string;
  scope?: 'all' | 'verified_clean';
}


// --- Multi-Group SEM Invariance & Latent Means (Meredith 1993; Byrne 2013) ---
export interface MGSEMInvarianceStep {
  model: string;
  chi2: number;
  df: number;
  p_value: number;
  cfi: number;
  rmsea: number;
  srmr: number;
  delta_chi2: number;
  delta_df: number;
  delta_p: number;
  delta_cfi: number;
  status: string;
}

export interface MGSEMLatentMeans {
  reference_group: string;
  comparison_group: string;
  latent_mean_ref: number;
  latent_mean_comp: number;
  se: number;
  z_stat: number;
  p_value: number;
  ci_95_lower: number;
  ci_95_upper: number;
  cohens_d: number;
  is_significant: boolean;
  is_valid_comparison: boolean;
}

export interface MGSEMIndicatorParam {
  indicator: string;
  loading_g1: number;
  loading_g2: number;
  loading_diff: number;
  intercept_g1: number;
  intercept_g2: number;
  intercept_diff: number;
  is_scalar_invariant: boolean;
}

export interface MGSEMDiagnostics {
  N_total: number;
  N1: number;
  N2: number;
  group1: string;
  group2: string;
  n_indicators: number;
  metric_supported: boolean;
  scalar_supported: boolean;
  strict_supported: boolean;
}

export interface MGSEMInvarianceResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: MGSEMDiagnostics;
  invariance_hierarchy?: MGSEMInvarianceStep[];
  latent_means_comparison?: MGSEMLatentMeans;
  indicator_parameters?: MGSEMIndicatorParam[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface MGSEMInvarianceRequest {
  group_question_id: string;
  indicator_question_ids: string[];
  reference_group?: string;
  scope?: 'all' | 'verified_clean';
}


// --- Generalized Additive Models (GAM) & Penalized Splines (Hastie & Tibshirani 1990; Wood 2017) ---
export interface GAMCurvePoint {
  x: number;
  f_x: number;
  ci_lower: number;
  ci_upper: number;
  deriv1: number;
}

export interface GAMTippingPoint {
  x_value: number;
  predicted_response: number;
  type: string;
  interpretation: string;
}

export interface GAMDiagnostics {
  N: number;
  n_knots: number;
  optimal_smoothing_lambda: number;
  effective_degrees_of_freedom: number;
  r_squared: number;
  f_stat_nonlinearity: number;
  p_value_nonlinearity: number;
  is_strictly_nonlinear: boolean;
  total_tipping_points: number;
}

export interface GAMSplineResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: GAMDiagnostics;
  tipping_points?: GAMTippingPoint[];
  smooth_curve?: GAMCurvePoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface GAMSplineRequest {
  predictor_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  n_knots?: number;
  grid_points?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Latent Profile Analysis (LPA) Interfaces ---
export interface LatentProfileItemStat {
  indicator: string;
  mean: number;
  std: number;
  z_score: number;
}

export interface LatentProfileDetail {
  profile_id: number;
  name: string;
  size: number;
  percentage: number;
  average_posterior_prob: number;
  item_statistics: LatentProfileItemStat[];
}

export interface LPAClassComparison {
  n_classes: number;
  log_likelihood: number;
  num_params: number;
  aic: number;
  bic: number;
  sabic: number;
  entropy: number;
  min_class_pct: number;
}

export interface LPADiagnostics {
  sample_size: number;
  n_indicators: number;
  optimal_n_classes: number;
  log_likelihood: number;
  aic: number;
  bic: number;
  sabic: number;
  entropy: number;
  is_well_separated: boolean;
  separation_quality: string;
}

export interface LatentProfileResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: LPADiagnostics;
  model_comparison?: LPAClassComparison[];
  profiles?: LatentProfileDetail[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface LatentProfileRequest {
  indicator_question_ids: string[];
  n_profiles?: number;
  max_profiles?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Shapley Value Regression & Key Driver Analysis (KDA) Interfaces ---
export interface ShapleyDriverItem {
  driver_id: number;
  driver_name: string;
  shapley_r2_contribution: number;
  importance_share_pct: number;
  performance_mean: number;
  performance_std: number;
  bivariate_correlation: number;
  vif: number;
  strategic_quadrant: string;
  strategic_label: string;
  action_urgency: string;
}

export interface ShapleyDriverDiagnostics {
  sample_size: number;
  n_drivers: number;
  full_model_r2: number;
  sum_shapley_contributions: number;
  efficiency_gap: number;
  max_vif: number;
  has_multicollinearity: boolean;
  importance_threshold_median: number;
  performance_threshold_median: number;
}

export interface ShapleyDriverResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: ShapleyDriverDiagnostics;
  drivers?: ShapleyDriverItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ShapleyDriverRequest {
  driver_question_ids: string[];
  outcome_question_id: string;
  scope?: 'all' | 'verified_clean';
}


// --- Plackett-Luce Choice Model & Rank-Ordered Logit Interfaces ---
export interface PlackettLuceItem {
  item_id: number;
  item_name: string;
  latent_worth: number;
  worth_percentage: number;
  utility_log_worth: number;
  std_error: number;
  z_statistic: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
}

export interface PlackettLuceDiagnostics {
  sample_size: number;
  n_items: number;
  log_likelihood: number;
  null_log_likelihood: number;
  mcfadden_pseudo_r2: number;
  lr_chi_square: number;
  df: number;
  p_value: number;
  converged: boolean;
}

export interface PlackettLuceResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: PlackettLuceDiagnostics;
  items?: PlackettLuceItem[];
  pairwise_win_matrix?: number[][];
  item_labels?: string[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface PlackettLuceRequest {
  ranking_question_id?: string;
  item_question_ids?: string[];
  scope?: 'all' | 'verified_clean';
}


// --- MaxDiff Best-Worst Scaling Interfaces ---
export interface MaxDiffItem {
  item_id: number;
  item_name: string;
  raw_utility: number;
  std_error: number;
  z_statistic: number;
  p_value: number;
  preference_share_pct: number;
  best_count: number;
  worst_count: number;
  times_shown: number;
  best_rate_pct: number;
  worst_rate_pct: number;
  counting_score: number;
}

export interface MaxDiffDiagnostics {
  n_tasks: number;
  n_items: number;
  log_likelihood: number;
  null_log_likelihood: number;
  mcfadden_pseudo_r2: number;
  converged: boolean;
}

export interface MaxDiffResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: MaxDiffDiagnostics;
  items?: MaxDiffItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface MaxDiffRequest {
  best_question_id?: string;
  worst_question_id?: string;
  item_question_ids?: string[];
  scope?: 'all' | 'verified_clean';
}


// --- Bayesian Network DAG Structure Learning Interfaces ---
export interface BayesianNetworkNode {
  node_id: number;
  label: string;
  topological_role: string;
  in_degree: number;
  out_degree: number;
  parents: string[];
  children: string[];
  markov_blanket: string[];
}

export interface BayesianNetworkEdge {
  from_node: string;
  to_node: string;
  from_index: number;
  to_index: number;
  standardized_path_coeff: number;
  relationship_type: string;
}

export interface BayesianNetworkDiagnostics {
  sample_size: number;
  n_nodes: number;
  total_edges: number;
  graph_density: number;
  final_bic_score: number;
  empty_graph_bic: number;
  bic_gain: number;
  is_acyclic: boolean;
}

export interface BayesianNetworkResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: BayesianNetworkDiagnostics;
  nodes?: BayesianNetworkNode[];
  edges?: BayesianNetworkEdge[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface BayesianNetworkRequest {
  question_ids: string[];
  max_parents?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Stochastic Dominance & Distributional Inequality (Davidson & Duclos 2000) ---
export interface StochasticDominanceDiagnostics {
  sample_size_a: number;
  sample_size_b: number;
  mean_a: number;
  mean_b: number;
  median_a: number;
  median_b: number;
  std_a: number;
  std_b: number;
  gini_a: number;
  gini_b: number;
  ks_statistic: number;
  ks_p_value: number;
  fsd_conclusion: string;
  ssd_conclusion: string;
  tsd_conclusion: string;
  fsd_dominant_group: string;
  ssd_dominant_group: string;
}

export interface StochasticDominanceThreshold {
  threshold: number;
  cdf_a: number;
  cdf_b: number;
  fsd_diff_b_minus_a: number;
  d2_integral_a: number;
  d2_integral_b: number;
  ssd_diff_b_minus_a: number;
}

export interface StochasticDominanceResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: StochasticDominanceDiagnostics;
  grid_thresholds?: StochasticDominanceThreshold[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface StochasticDominanceRequest {
  outcome_question_id: string;
  group_question_id: string;
  group_a_value?: string;
  group_b_value?: string;
  group_a_label?: string;
  group_b_label?: string;
  n_grid_points?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Manski Non-Parametric Partial Identification & Worst-Case Bounds Types ---
export interface ManskiBoundsDiagnostics {
  sample_size_total: number;
  n_treated: number;
  n_control: number;
  observed_count: number;
  missing_rate: number;
  support_min: number;
  support_max: number;
  naive_ate: number;
  worst_case_lower: number;
  worst_case_upper: number;
  worst_case_width: number;
  mts_lower: number;
  mts_upper: number;
  mtr_lower: number;
  mtr_upper: number;
  joint_mts_mtr_lower: number;
  joint_mts_mtr_upper: number;
  ci_joint_lower_95: number;
  ci_joint_upper_95: number;
  breakdown_rate?: number | null;
  is_sign_identified: boolean;
}

export interface ManskiBoundsTier {
  tier: string;
  lower: number;
  upper: number;
  width: number;
}

export interface ManskiSensitivityPoint {
  missing_rate: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ManskiBoundsResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: ManskiBoundsDiagnostics;
  tiers?: ManskiBoundsTier[];
  sensitivity_grid?: ManskiSensitivityPoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ManskiBoundsRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  response_indicator_question_id?: string;
  support_min?: number;
  support_max?: number;
  confidence_level?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Types ---
export interface DTRDiagnostics {
  sample_size: number;
  v_optimal: number;
  v_always_treated: number;
  v_never_treated: number;
  v_observed: number;
  policy_value_gain: number;
  policy_value_gain_pct: number;
  pct_stage1_treated: number;
  pct_stage2_treated: number;
  stage1_threshold: number;
  stage2_threshold: number;
}

export interface DTRStage1Model {
  intercept: number;
  main_x1: number;
  main_a1: number;
  interaction_a1_x1: number;
  se_interaction: number;
  t_stat: number;
  p_value: number;
  r_squared: number;
}

export interface DTRStage2Model {
  intercept: number;
  main_x1: number;
  main_a1: number;
  main_x2: number;
  main_a2: number;
  interaction_a2_x2: number;
  se_interaction: number;
  t_stat: number;
  p_value: number;
  r_squared: number;
}

export interface DynamicTreatmentRegimesResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: DTRDiagnostics;
  stage1_model?: DTRStage1Model;
  stage2_model?: DTRStage2Model;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DynamicTreatmentRegimesRequest {
  outcome_question_id: string;
  stage1_action_question_id: string;
  stage2_action_question_id: string;
  baseline_covariate_question_id: string;
  interim_state_question_id: string;
  scope?: 'all' | 'verified_clean';
}

// --- Finite Mixture Rasch Models (FMRM) & Latent Class IRT Types ---
export interface FMRMDiagnostics {
  sample_size: number;
  sample_size_total: number;
  n_items: number;
  n_classes: number;
  log_likelihood: number;
  aic: number;
  bic: number;
  abic: number;
  entropy: number;
  is_well_separated: boolean;
  top_shifted_item: string;
  top_shift_magnitude: number;
}

export interface FMRMClassProportion {
  class_name: string;
  class_index: number;
  proportion: number;
}

export interface FMRMItemParameter {
  item_title: string;
  item_index: number;
  beta_class_1?: number;
  beta_class_2?: number;
  beta_class_3?: number;
  beta_class_4?: number;
  max_diff: number;
}

export interface FiniteMixtureRaschResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: FMRMDiagnostics;
  class_proportions?: FMRMClassProportion[];
  items_parameters?: FMRMItemParameter[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface FiniteMixtureRaschRequest {
  question_ids: string[];
  n_classes?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Double / Debiased Machine Learning (DML) Types ---
export interface DMLDiagnostics {
  sample_size: number;
  n_covariates: number;
  n_folds: number;
  theta_dml: number;
  se_dml: number;
  z_statistic: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  theta_naive_ols: number;
  se_naive_ols: number;
  confounding_bias: number;
  r2_nuisance_y: number;
  r2_nuisance_d: number;
  is_statistically_significant: boolean;
}

export interface DMLConfoundingCovariate {
  covariate: string;
  corr_outcome: number;
  corr_treatment: number;
  confounding_score: number;
}

export interface DoubleMachineLearningResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: DMLDiagnostics;
  confounding_covariates?: DMLConfoundingCovariate[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DoubleMachineLearningRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids: string[];
  n_folds?: number;
  alpha_penalty?: number;
  scope?: 'all' | 'verified_clean';
}

export interface RegressionKinkDiagnostics {
  sample_size_total: number;
  effective_sample_size: number;
  cutoff: number;
  bandwidth: number;
  tau_rkd: number;
  se_rkd: number;
  t_statistic: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  delta_slope_outcome: number;
  left_slope: number;
  right_slope: number;
  level_at_cutoff: number;
  mccrary_p_value: number;
  is_density_smooth: boolean;
  is_statistically_significant: boolean;
  design_type?: string;
  treatment_kink?: number;
  delta_slope_treatment?: number;
}

export interface RegressionKinkBinnedScatter {
  bin_center: number;
  mean_running: number;
  mean_outcome: number;
  count: number;
  side: string;
}

export interface RegressionKinkResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: RegressionKinkDiagnostics;
  binned_scatter?: RegressionKinkBinnedScatter[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface RegressionKinkRequest {
  outcome_question_id: string;
  running_question_id: string;
  cutoff: number;
  treatment_question_id?: string | null;
  bandwidth?: number | null;
  polynomial_order?: number;
  known_kink_slope?: number;
  scope?: 'all' | 'verified_clean';
}

export interface StaggeredDIDDiagnostics {
  n_observations: number;
  n_units: number;
  n_time_periods: number;
  n_cohorts: number;
  n_never_treated_units: number;
  overall_att: number;
  overall_se: number;
  overall_z: number;
  overall_p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_statistically_significant: boolean;
  pre_trends_p_value: number;
  pre_trends_wald_stat: number;
  parallel_trends_supported: boolean;
  twfe_naive_beta: number;
  twfe_naive_se: number;
  twfe_bias_gap: number;
  pct_negative_weights: number;
}

export interface GroupTimeEffect {
  cohort_g: number;
  calendar_time_t: number;
  event_time_e: number;
  att: number;
  se: number;
  t_statistic: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_pre_treatment: boolean;
  n_treated: number;
  n_control: number;
}

export interface EventStudyEffect {
  event_time: number;
  att: number;
  se: number;
  z_statistic: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_pre_period: boolean;
}

export interface BaconComponent {
  comparison_type: string;
  group_k: number | string;
  group_u: number | string;
  estimate: number;
  weight: number;
  weight_share?: number;
}

export interface BaconDecomposition {
  n_comparisons: number;
  pct_negative_weights: number;
  components: BaconComponent[];
}

export interface StaggeredDIDResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: StaggeredDIDDiagnostics;
  group_time_effects?: GroupTimeEffect[];
  event_study_effects?: EventStudyEffect[];
  bacon_decomposition?: BaconDecomposition;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface StaggeredDIDRequest {
  outcome_question_id: string;
  unit_question_id: string;
  time_question_id: string;
  treatment_timing_question_id: string;
  anticipation_periods?: number;
  control_group_type?: 'never_treated' | 'not_yet_treated';
  scope?: 'all' | 'verified_clean';
}

export interface MatrixCompletionDiagnostics {
  n_units: number;
  n_time_periods: number;
  total_cells: number;
  n_treated_cells: number;
  n_control_cells: number;
  lambda_penalty: number;
  iterations_count: number;
  is_converged: boolean;
  effective_rank: number;
  rmse_control_fit: number;
  overall_att: number;
  att_se: number;
  z_statistic: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_statistically_significant: boolean;
  top_factor_variance_share: number;
}

export interface CellTreatmentEffect {
  unit_id: string;
  time_period: number;
  realized_outcome_y1: number;
  imputed_counterfactual_y0: number;
  treatment_effect_tau: number;
}

export interface SingularSpectrumItem {
  rank_component: number;
  singular_value: number;
  variance_explained_ratio: number;
}

export interface MatrixCompletionCausalResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: MatrixCompletionDiagnostics;
  cell_treatment_effects?: CellTreatmentEffect[];
  singular_value_spectrum?: SingularSpectrumItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface MatrixCompletionCausalRequest {
  outcome_question_id: string;
  unit_question_id: string;
  time_question_id: string;
  treatment_question_id: string;
  lambda_penalty?: number | null;
  max_rank?: number;
  scope?: 'all' | 'verified_clean';
}

export interface SDIDAdvancedDiagnostics {
  n_units: number;
  n_treated_units: number;
  n_control_units: number;
  n_time_periods: number;
  n_pre_periods: number;
  n_post_periods: number;
  zeta_regularization: number;
  unit_intercept_omega0: number;
  tau_sdid: number;
  se_sdid: number;
  z_statistic: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_statistically_significant: boolean;
  tau_standard_did: number;
  tau_standard_sc: number;
  did_bias_gap: number;
}

export interface SDIDUnitWeight {
  unit_id: string;
  weight: number;
  percentage: number;
}

export interface SDIDTimeWeight {
  time_period: number;
  weight: number;
  percentage: number;
}

export interface SDIDTrajectoryItem {
  time_period: number;
  is_post_treatment: boolean;
  treated_actual: number;
  control_unweighted: number;
  synthetic_control: number;
  sdid_counterfactual: number;
}

export interface SDIDAdvancedResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: SDIDAdvancedDiagnostics;
  unit_weights?: SDIDUnitWeight[];
  time_weights?: SDIDTimeWeight[];
  trajectories?: SDIDTrajectoryItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface SDIDAdvancedRequest {
  outcome_question_id: string;
  unit_question_id: string;
  time_question_id: string;
  treatment_question_id: string;
  zeta_regularization?: number | null;
  scope?: 'all' | 'verified_clean';
}

// --- Interactive Fixed Effects (Bai 2009; Gobillon & Magnac 2016) Types ---
export interface IFEDiagnostics {
  n_units: number;
  n_time_periods: number;
  n_treated_cells: number;
  n_control_cells: number;
  num_factors_selected: number;
  total_variance_explained_pct: number;
  tau_ife: number;
  se_ife: number;
  z_statistic: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_statistically_significant: boolean;
  tau_twfe: number;
  factor_bias_gap: number;
  pesaran_cd_statistic: number;
  pesaran_cd_p_value: number;
  cross_sectional_dependence_purged: boolean;
}

export interface IFEFactorSeriesPoint {
  time_period: number;
  value: number;
}

export interface IFELatentFactorItem {
  factor_index: number;
  variance_explained_pct: number;
  eigenvalue: number;
  series: IFEFactorSeriesPoint[];
}

export interface IFEScreeSpectrumItem {
  factor_number: number;
  eigenvalue: number;
  variance_pct: number;
  cumulative_pct: number;
  is_selected: boolean;
}

export interface IFECellEffectItem {
  unit_id: string;
  time_period: number;
  observed_y: number;
  counterfactual_y0: number;
  treatment_effect: number;
}

export interface InteractiveFixedEffectsResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: IFEDiagnostics;
  latent_factors?: IFELatentFactorItem[];
  scree_spectrum?: IFEScreeSpectrumItem[];
  cell_effects?: IFECellEffectItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface InteractiveFixedEffectsRequest {
  outcome_question_id: string;
  unit_question_id: string;
  time_question_id: string;
  treatment_question_id: string;
  num_factors?: number | null;
  max_factors?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Multiple Sequential Mediators (VanderWeele 2014; Steen et al. 2012) Types ---
export interface MultipleMediatorsDiagnostics {
  sample_size: number;
  n_bootstraps: number;
  total_effect: number;
  direct_effect: number;
  total_indirect_effect: number;
  nie_m1: number;
  nie_m2: number;
  nie_seq: number;
  proportion_mediated_pct: number;
  proportion_m1_pct: number;
  proportion_m2_pct: number;
  proportion_seq_pct: number;
  is_full_mediation: boolean;
  is_partial_mediation: boolean;
}

export interface MultipleMediatorsPathCoefficient {
  path: string;
  estimate: number;
  se: number;
  p_value: number;
}

export interface MultipleMediatorsEffectStats {
  estimate: number;
  se: number;
  z: number;
  p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_significant: boolean;
}

export interface MultipleMediatorsEffectItem {
  effect_name: string;
  stats: MultipleMediatorsEffectStats;
  proportion_pct: number;
}

export interface MultipleMediatorsResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: MultipleMediatorsDiagnostics;
  path_coefficients?: MultipleMediatorsPathCoefficient[];
  effects_summary?: MultipleMediatorsEffectItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface MultipleMediatorsRequest {
  treatment_question_id: string;
  mediator1_question_id: string;
  mediator2_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  n_bootstraps?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Doubly Robust Policy Learning (Athey & Wager 2021) Types ---
export interface PolicyLearningDiagnostics {
  sample_size: number;
  n_treated_observed: number;
  n_control_observed: number;
  pct_recommended_treatment: number;
  n_recommended_treatment: number;
  optimal_welfare_value: number;
  treat_all_welfare_value: number;
  treat_none_welfare_value: number;
  observed_welfare_value: number;
  net_welfare_gain: number;
  se_gain: number;
  z_gain: number;
  p_value_gain: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_significant_gain: boolean;
}

export interface PolicyLearningRegime {
  regime_name: string;
  expected_welfare: number;
  treated_pct: number;
  description: string;
}

export interface PolicyLearningSampleAllocation {
  respondent_id: string;
  primary_feature_val: number;
  observed_treatment: number;
  aipw_score: number;
  recommended_policy: number;
  status: string;
}

export interface PolicyLearningResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: PolicyLearningDiagnostics;
  regimes_comparison?: PolicyLearningRegime[];
  sample_allocations?: PolicyLearningSampleAllocation[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface PolicyLearningRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids: string[];
  primary_feature_idx?: number;
  n_bootstraps?: number;
  scope?: 'all' | 'verified_clean';
}

// --- RDD with Local Randomization (Cattaneo, Frandsen, & Titiunik 2015) Types ---
export interface RDDLocalRandomizationDiagnostics {
  sample_size: number;
  cutoff_c: number;
  window_half_width: number;
  window_lower: number;
  window_upper: number;
  n_in_window: number;
  n_window_treated: number;
  n_window_control: number;
  tau_diff_means: number;
  tau_diff_medians: number;
  se_permutation: number;
  permutation_p_value: number;
  ci_lower_95: number;
  ci_upper_95: number;
  is_statistically_significant: boolean;
  tau_continuity_benchmark: number;
  methodology_bias_gap: number;
}

export interface RDDLocalRandomizationBalanceItem {
  covariate_name: string;
  mean_treated: number;
  mean_control: number;
  difference: number;
  p_value: number;
  is_balanced: boolean;
}

export interface RDDLocalRandomizationDiscreteBin {
  x_value: number;
  centered_x: number;
  is_treated: boolean;
  is_in_window: boolean;
  count: number;
  mean_y: number;
}

export interface RDDLocalRandomizationResult {
  status: string;
  message?: string;
  model_type?: string;
  diagnostics?: RDDLocalRandomizationDiagnostics;
  balance_table?: RDDLocalRandomizationBalanceItem[];
  discrete_bins?: RDDLocalRandomizationDiscreteBin[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface RDDLocalRandomizationRequest {
  outcome_question_id: string;
  running_question_id: string;
  cutoff?: number;
  covariate_question_ids?: string[];
  window_half_width?: number | null;
  n_permutations?: number;
  scope?: 'all' | 'verified_clean';
}






// --- Dynamic Panel System & Difference GMM (Arellano-Bond 1991, Blundell-Bond 1998, Windmeijer 2005) ---
export interface DynamicPanelGMMDiagnostics {
  num_panel_units: number;
  total_observations: number;
  time_waves: number;
  method: string;
  two_step: boolean;
  windmeijer_correction: boolean;
  instrument_count: number;
  alpha_gmm: number;
  se_alpha_gmm: number;
  alpha_ols_bound: number;
  alpha_fe_bound: number;
  nickell_bound_passed: boolean;
  ar1_z: number;
  ar1_p_value: number;
  ar2_z: number;
  ar2_p_value: number;
  ar2_valid: boolean;
  hansen_j_statistic: number;
  hansen_df: number;
  hansen_p_value: number;
  hansen_valid: boolean;
}

export interface DynamicPanelGMMParameter {
  parameter: string;
  estimate: number;
  std_error: number;
  z_statistic: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
  is_significant: boolean;
}

export interface DynamicPanelGMMResult {
  status: string;
  model_type?: string;
  message?: string;
  diagnostics?: DynamicPanelGMMDiagnostics;
  parameters?: DynamicPanelGMMParameter[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DynamicPanelGMMRequest {
  unit_id_question_id: string;
  time_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  method?: 'system' | 'difference';
  two_step?: boolean;
  windmeijer_correction?: boolean;
  max_instrument_lags?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Weak-Instrument Robust Inference (Anderson-Rubin 1949, Moreira 2003 CLR, Montiel Olea & Pflueger 2013) ---
export interface WeakIVRobustDiagnostics {
  sample_size: number;
  num_instruments: number;
  num_covariates: number;
  first_stage_f: number;
  first_stage_p: number;
  effective_f: number;
  effective_f_threshold_10pct: number;
  identification_status: string;
  identification_label: string;
  ar_null_zero_f_stat: number;
  ar_null_zero_p_value: number;
  ar_critical_value: number;
}

export interface WeakIVRobustEstimates {
  beta_2sls: number;
  se_2sls: number;
  p_2sls: number;
  wald_ci_95: [number, number];
  beta_ols: number;
  se_ols: number;
  ar_ci_type: string;
  ar_ci_95: Array<[number, number]>;
  clr_ci_95?: [number, number] | null;
  kleibergen_k_ci_95?: [number, number] | null;
}

export interface WeakIVRobustResult {
  status: string;
  model_type?: string;
  message?: string;
  diagnostics?: WeakIVRobustDiagnostics;
  estimates?: WeakIVRobustEstimates;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface WeakIVRobustRequest {
  outcome_question_id: string;
  endogenous_question_id: string;
  instrument_question_ids: string[];
  covariate_question_ids?: string[];
  alpha_level?: number;
  grid_points?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Sequential Causal Mediation Analysis (Hayes Model 6 / Imai & Yamamoto 2013) ---
export interface SequentialMediationEffect {
  estimate: number;
  bootstrap_se: number;
  ci_lower: number;
  ci_upper: number;
  is_significant: boolean;
}

export interface SequentialMediationProportions {
  proportion_mediated_total: number;
  proportion_mediated_sequential: number;
}

export interface SequentialMediationEquation {
  dependent_variable: string;
  r_squared: number;
  coefficients: Record<string, number>;
}

export interface SequentialMediationResult {
  status: string;
  model_type?: string;
  message?: string;
  sample_size?: number;
  bootstrap_replications?: number;
  effects?: {
    direct_effect: SequentialMediationEffect;
    indirect_path1_m1: SequentialMediationEffect;
    indirect_path2_m2: SequentialMediationEffect;
    indirect_sequential_m1_m2: SequentialMediationEffect;
    indirect_total: SequentialMediationEffect;
    total_effect: SequentialMediationEffect;
  };
  proportions?: SequentialMediationProportions;
  regression_equations?: SequentialMediationEquation[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface SequentialMediationRequest {
  treatment_question_id: string;
  mediator1_question_id: string;
  mediator2_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  n_bootstraps?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- High-Dimensional Post-Double-Selection (PDS) Lasso (Belloni, Chernozhukov, & Hansen 2014) ---
export interface PostDoubleSelectionLassoDiagnostics {
  sample_size: number;
  total_candidate_controls: number;
  selected_by_outcome_model: number;
  selected_by_treatment_model: number;
  union_selected_controls: number;
  lambda_y_cross_validated: number;
  lambda_d_cross_validated: number;
  dimension_reduction_ratio: number;
}

export interface PostDoubleSelectionSelectedControl {
  index: number;
  name: string;
  selected_in_outcome_model: boolean;
  selected_in_treatment_model: boolean;
  in_union_set: boolean;
  coef_y_stage: number;
  coef_d_stage: number;
}

export interface PostDoubleSelectionEstimates {
  post_double_selection_lasso: {
    estimate: number;
    robust_se: number;
    z_statistic: number;
    p_value: number;
    ci_lower: number;
    ci_upper: number;
    is_significant: boolean;
  };
  naive_single_selection_lasso: {
    estimate: number;
    robust_se: number;
    z_statistic: number;
    p_value: number;
    ci_lower: number;
    ci_upper: number;
    is_significant: boolean;
  };
  unadjusted_base_ols: {
    estimate: number;
    robust_se: number;
    z_statistic: number;
    p_value: number;
    ci_lower: number;
    ci_upper: number;
    is_significant: boolean;
  };
  saturated_full_ols: {
    estimate?: number;
    robust_se?: number;
    z_statistic?: number;
    p_value?: number;
    ci_lower?: number;
    ci_upper?: number;
    is_significant?: boolean;
    note?: string;
  };
}

export interface PostDoubleSelectionLassoResult {
  status: string;
  model_type?: string;
  message?: string;
  diagnostics?: PostDoubleSelectionLassoDiagnostics;
  selected_controls?: PostDoubleSelectionSelectedControl[];
  estimates?: PostDoubleSelectionEstimates;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface PostDoubleSelectionLassoRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  candidate_control_question_ids: string[];
  cv_folds?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


export interface LARFEffectItem {
  estimate: number;
  std_error: number;
  z_stat: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
  is_significant: boolean;
}

export interface LARFPotentialOutcomes {
  e_y1_compliers: number;
  e_y0_compliers: number;
}

export interface LARFModelCoefficient {
  feature: string;
  coefficient: number;
}

export interface LARFResult {
  status: string;
  message?: string;
  model_type?: string;
  sample_size?: number;
  effective_sample_size?: number;
  bootstrap_replications?: number;
  complier_probability?: number;
  complier_probability_se?: number;
  pct_negative_weights?: number;
  potential_outcomes_compliers?: LARFPotentialOutcomes;
  effects?: {
    late: LARFEffectItem;
    naive: LARFEffectItem;
    itt: LARFEffectItem;
  };
  model_coefficients?: LARFModelCoefficient[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface LARFRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  instrument_question_id: string;
  covariate_question_ids?: string[];
  model_type?: 'logit' | 'linear';
  alpha_level?: number;
  n_bootstraps?: number;
  trim_negative?: boolean;
  scope?: 'all' | 'verified_clean';
}


export interface MTEParameterItem {
  estimate: number;
  std_error: number;
  z_stat: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
  is_significant: boolean;
}

export interface MTECurvePoint {
  u_d: number;
  mte: number;
  std_error: number;
  ci_lower: number;
  ci_upper: number;
  w_att: number;
  w_atu: number;
}

export interface MTEParameters {
  ate: MTEParameterItem;
  att: MTEParameterItem;
  atu: MTEParameterItem;
  late: MTEParameterItem;
  prte: MTEParameterItem;
}

export interface MTEResult {
  status: string;
  message?: string;
  model_type?: string;
  sample_size?: number;
  bootstrap_replications?: number;
  polynomial_degree?: number;
  common_support?: {
    p_min: number;
    p_max: number;
  };
  selection_sorting_pattern?: string;
  mte_slope?: number;
  parameters?: MTEParameters;
  mte_curve?: MTECurvePoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface MTERequest {
  outcome_question_id: string;
  treatment_question_id: string;
  instrument_question_ids: string[];
  covariate_question_ids?: string[];
  poly_degree?: number;
  alpha_level?: number;
  n_bootstraps?: number;
  policy_shift_pct?: number;
  scope?: 'all' | 'verified_clean';
}


export interface LeeBoundsResponseRates {
  treated_response_rate: number;
  control_response_rate: number;
  differential_response_rate: number;
  trimming_fraction_q: number;
  trimmed_group: string;
}

export interface LeeBoundsUnconditional {
  lower_bound: number;
  upper_bound: number;
  se_lower: number;
  se_upper: number;
  im_critical_value: number;
  ci_lower: number;
  ci_upper: number;
  excludes_zero: boolean;
}

export interface LeeBoundsTightened {
  lower_bound: number;
  upper_bound: number;
  ci_lower: number;
  ci_upper: number;
  is_available: boolean;
}

export interface LeeBoundsNaive {
  estimate: number;
  std_error: number;
  ci_lower: number;
  ci_upper: number;
  p_value: number;
}

export interface LeeBoundsResult {
  status: string;
  message?: string;
  model_type?: string;
  sample_size?: number;
  observed_sample_size?: number;
  bootstrap_replications?: number;
  response_rates?: LeeBoundsResponseRates;
  bounds?: {
    unconditional: LeeBoundsUnconditional;
    covariate_tightened: LeeBoundsTightened;
  };
  naive_complete_case?: LeeBoundsNaive;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface LeeBoundsRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  response_question_id?: string;
  covariate_question_ids?: string[];
  alpha_level?: number;
  n_bootstraps?: number;
  scope?: 'all' | 'verified_clean';
}


export interface SurrogateDecompositionItem {
  surrogate_name: string;
  treatment_effect: number;
  std_error: number;
  surrogate_weight_in_index: number;
}

export interface SurrogateIndexResult {
  status: string;
  message?: string;
  model_type?: string;
  sample_sizes?: {
    experimental_sample: number;
    observational_sample: number;
    total: number;
  };
  bootstrap_replications?: number;
  surrogate_index_fit?: {
    r_squared: number;
    ridge_lambda: number;
  };
  longterm_treatment_effect?: {
    estimate: number;
    std_error: number;
    z_stat: number;
    p_value: number;
    ci_lower: number;
    ci_upper: number;
    is_significant: boolean;
  };
  surrogate_decomposition?: SurrogateDecompositionItem[];
  surrogacy_validation?: {
    risk_status: string;
    direct_effect_p_value?: number;
  };
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface SurrogateIndexRequest {
  treatment_question_id: string;
  surrogate_question_ids: string[];
  longterm_outcome_question_id: string;
  covariate_question_ids?: string[];
  sample_indicator_question_id?: string;
  alpha_level?: number;
  n_bootstraps?: number;
  ridge_lambda?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Conformal Counterfactual Risk Inference Types (Chernozhukov et al. 2021; Lei & Candes 2021) ---
export interface ConformalCounterfactualSubgroup {
  group_name: string;
  sample_size: number;
  mean_ite: number;
  mean_ite_lower: number;
  mean_ite_upper: number;
  downside_risk_rate: number;
  strictly_beneficial_rate: number;
  strictly_harmful_rate: number;
  policy_recommendation: string;
  recommendation_code: 'ROLLOUT' | 'CONTRAINDICATED' | 'SAFEGUARDS' | 'MONITOR';
}

export interface ConformalCounterfactualIndividual {
  unit_id: number;
  treatment_observed: number;
  outcome_observed: number;
  propensity_score: number;
  predicted_y1: number;
  predicted_y0: number;
  y1_conformal_interval: [number, number];
  y0_conformal_interval: [number, number];
  ite_point_estimate: number;
  ite_conformal_interval: [number, number];
  downside_risk: boolean;
  risk_status: string;
}

export interface ConformalCounterfactualResult {
  status: string;
  message?: string;
  overall_summary?: {
    sample_size: number;
    treated_count: number;
    control_count: number;
    miscoverage_alpha: number;
    target_coverage_pct: number;
    estimated_ate: number;
    ate_conformal_interval: [number, number];
    downside_risk_rate: number;
    strictly_beneficial_rate: number;
    strictly_harmful_rate: number;
    ambiguous_rate: number;
    var_downside_5pct: number;
    cvar_downside_5pct: number;
    mean_ite_interval_length: number;
  };
  calibration_diagnostics?: {
    propensity_auc: number;
    propensity_overlap_min: number;
    propensity_overlap_max: number;
    propensity_overlap_median_treated: number;
    propensity_overlap_median_control: number;
    treated_calibration_size: number;
    treated_training_size: number;
    control_calibration_size: number;
    control_training_size: number;
    treated_nonconformity_cutoff: number;
    control_nonconformity_cutoff: number;
    ite_band_half_width: number;
    weighted_conformal_shift_applied: boolean;
  };
  subgroup_risk_profiles?: ConformalCounterfactualSubgroup[];
  individual_predictions_sample?: ConformalCounterfactualIndividual[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ConformalCounterfactualRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids: string[];
  miscoverage_alpha?: number;
  calibration_ratio?: number;
  use_propensity_weighting?: boolean;
  subgroup_question_id?: string;
  scope?: 'all' | 'verified_clean';
}


// --- Causal Sensitivity Analysis & Omitted Variable Bias Types (Cinelli & Hazlett 2020) ---
export interface CausalSensitivityBenchmark {
  covariate: string;
  r2_d_given_x: number;
  r2_y_given_dx: number;
}

export interface CausalSensitivityScenario {
  covariate: string;
  multiplier: number;
  r2_dz_x: number;
  r2_yz_dx: number;
  adjusted_estimate: number;
  adjusted_se: number;
  adjusted_t: number;
  adjusted_ci: [number, number];
  remains_significant: boolean;
  is_overturned: boolean;
}

export interface CausalSensitivityResult {
  status: string;
  message?: string;
  overall_summary?: {
    sample_size: number;
    residual_df: number;
    baseline_estimate: number;
    baseline_se: number;
    baseline_t: number;
    baseline_p_value: number;
    baseline_ci: [number, number];
    partial_r2_treatment: number;
    robustness_value_q: number;
    robustness_value_alpha: number;
    target_reduction_q: number;
    significance_alpha: number;
    extreme_r2_dz_needed_to_zero: number;
  };
  covariate_benchmarks?: CausalSensitivityBenchmark[];
  benchmark_scenarios?: CausalSensitivityScenario[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface CausalSensitivityRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids?: string[];
  q_reduction?: number;
  alpha_level?: number;
  benchmark_question_ids?: string[];
  benchmark_multipliers?: number[];
  scope?: 'all' | 'verified_clean';
}


// --- Bayesian Causal Forest (BCF; Hahn et al. 2020) Types ---
export interface BCFSubgroup {
  segment_name: string;
  rule: string;
  sample_size: number;
  cate_mean: number;
  credible_interval_95: [number, number];
  posterior_prob_positive: number;
  targeting_tier: 'HIGH_PRIORITY' | 'TARGETED' | 'CONTRAINDICATED';
}

export interface BCFIndividualSample {
  unit_id: number;
  treatment_w: number;
  outcome_y: number;
  propensity_pi: number;
  prognostic_mu: number;
  cate_mean: number;
  cate_ci_95: [number, number];
  prob_positive: number;
}

export interface BCFResult {
  status: string;
  message?: string;
  overall_summary?: {
    sample_size: number;
    treated_count: number;
    control_count: number;
    posterior_draws_count: number;
    posterior_ate_mean: number;
    posterior_ate_se: number;
    posterior_ate_ci_95: [number, number];
    posterior_prob_positive_ate: number;
    treatment_heterogeneity_sd: number;
    residual_sigma: number;
    variance_decomposition: {
      prognostic_baseline_pct: number;
      treatment_effect_pct: number;
      residual_noise_pct: number;
    };
    ric_correction_active: boolean;
  };
  subgroups?: BCFSubgroup[];
  individual_sample?: BCFIndividualSample[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface BCFRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids: string[];
  n_posterior_draws?: number;
  alpha_ridge?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Shift-Share Instrumental Variables & Rotemberg Diagnostics (Goldsmith-Pinkham et al. 2020) Types ---
export interface RotembergItem {
  share_variable: string;
  rotemberg_weight: number;
  rotemberg_weight_pct: number;
  share_shock_value: number;
  just_identified_beta: number;
  first_stage_cov: number;
}

export interface ShiftShareIVResult {
  status: string;
  message?: string;
  overall_summary?: {
    sample_size: number;
    n_shares_k: number;
    first_stage_f_statistic: number;
    is_weak_instrument: boolean;
    beta_2sls: number;
    se_conventional: number;
    se_akm_robust: number;
    t_statistic: number;
    p_value: number;
    confidence_interval_95: [number, number];
    rotemberg_hhi: number;
    sum_positive_rotemberg_weights: number;
    sum_negative_rotemberg_weights: number;
    top_5_shares_weight_share: number;
    overid_sargan_stat: number;
    overid_p_value: number;
  };
  rotemberg_decomposition?: RotembergItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ShiftShareIVRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  share_question_ids: string[];
  shocks?: number[];
  covariate_question_ids?: string[];
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Quantile Synthetic Control & Distributional Counterfactuals (Gunsilius 2023) Types ---
export interface QuantileEffectItem {
  quantile: number;
  quantile_label: string;
  treated_observed: number;
  synthetic_counterfactual: number;
  treatment_effect_qte: number;
  interpretation: string;
}

export interface DonorWeightItem {
  donor_unit: string;
  weight: number;
  weight_pct: number;
}

export interface QuantileSyntheticControlSummary {
  treated_unit: string;
  treatment_time: string;
  n_valid_donors: number;
  pre_treatment_periods: number;
  post_treatment_periods: number;
  pre_treatment_wasserstein_dist: number;
  mean_qte_effect: number;
  median_qte_effect: number;
  gini_observed: number;
  gini_counterfactual: number;
  gini_impact: number;
  iqr_observed: number;
  iqr_counterfactual: number;
  iqr_impact: number;
  p90_p10_ratio_observed?: number;
  p90_p10_ratio_counterfactual?: number;
}

export interface QuantileSyntheticControlResult {
  status: string;
  message?: string;
  overall_summary?: QuantileSyntheticControlSummary;
  donor_weights?: DonorWeightItem[];
  quantile_treatment_effects?: QuantileEffectItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface QuantileSyntheticControlRequest {
  outcome_question_id: string;
  unit_question_id: string;
  time_question_id: string;
  treated_unit_id: string;
  treatment_time: any;
  quantiles?: number[];
  regularization_lambda?: number;
  scope?: 'all' | 'verified_clean';
}



// --- Two-Way Fixed Effects (TWFE) Decomposition & Negative Weights (de Chaisemartin 2020) Types ---
export interface TWFESwitcherItem {
  period: string;
  time_index: number;
  n_switchers: number;
  n_stayers: number;
  did_m_effect: number;
  placebo_pretrend_effect?: number | null;
}

export interface TWFEWeightCell {
  unit: string;
  time_period: string;
  weight: number;
  weight_pct: number;
}

export interface TWFEDecompositionSummary {
  sample_size: number;
  n_units: number;
  n_time_periods: number;
  n_treated_cells: number;
  n_control_cells: number;
  beta_twfe: number;
  se_twfe: number;
  t_statistic_twfe: number;
  p_value_twfe: number;
  ci_twfe_95: [number, number];
  sum_positive_weights: number;
  sum_negative_weights: number;
  n_negative_cells: number;
  n_positive_cells: number;
  pct_negative_cells: number;
  minimal_heterogeneity_sd_sigma_fe: number;
  twfe_validity_status: 'ROBUST_LOW_RISK' | 'MODERATE_BIAS_RISK' | 'CRITICAL_BIAS_RISK';
  risk_interpretation: string;
  did_m_estimate: number;
  se_did_m: number;
  t_statistic_did_m: number;
  p_value_did_m: number;
  ci_did_m_95: [number, number];
  total_switchers_identified: number;
  placebo_pretrend_estimate: number;
  placebo_p_value: number;
  parallel_trends_pass: boolean;
}

export interface TWFEDecompositionResult {
  status: string;
  message?: string;
  overall_summary?: TWFEDecompositionSummary;
  period_switchers?: TWFESwitcherItem[];
  top_negative_weights?: TWFEWeightCell[];
  top_positive_weights?: TWFEWeightCell[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface TWFEDecompositionRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  unit_question_id: string;
  time_question_id: string;
  covariate_question_ids?: string[];
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Factor Instrumental Variables & PC-2SLS (Bai & Ng 2010 Econometrica) Types ---
export interface FactorSummaryItem {
  factor_name: string;
  factor_index: number;
  eigenvalue: number;
  variance_explained_pct: number;
  top_loading_instruments: string[];
}

export interface FactorCriteriaItem {
  k: number;
  v_k: number;
  ic_p1: number;
  ic_p2: number;
  pc_p1: number;
  variance_explained_pct: number;
  eigenvalue: number;
  eigenvalue_ratio?: number;
}

export interface FactorIVSummary {
  sample_size: number;
  n_candidate_instruments_K: number;
  n_factors_r: number;
  selection_method: string;
  total_variance_explained_pct: number;
  first_stage_f_statistic: number;
  first_stage_p_value: number;
  first_stage_r2: number;
  is_weak_instrument: boolean;
  weak_instrument_guidance: string;
  beta_factor_iv: number;
  se_factor_iv: number;
  t_statistic_factor_iv: number;
  p_value_factor_iv: number;
  ci_factor_iv_95: [number, number];
  beta_ols_baseline: number;
  se_ols_baseline: number;
  endogeneity_gap: number;
  hausman_durbin_wu_stat: number;
  hausman_p_value: number;
  endogeneity_detected: boolean;
  sargan_j_statistic: number;
  sargan_df: number;
  sargan_p_value: number;
  overidentification_valid: boolean;
}

export interface FactorIVResult {
  status: string;
  message?: string;
  overall_summary?: FactorIVSummary;
  factor_summaries?: FactorSummaryItem[];
  criteria_table?: FactorCriteriaItem[];
  instrument_loadings?: Record<string, any>[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface FactorIVRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  instrument_question_ids: string[];
  covariate_question_ids?: string[];
  n_factors?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Nested Logit Structural Choice (McFadden 1978) Types ---
export interface NestDiagnosticItem {
  nest_name: string;
  alternatives: string[];
  n_alternatives: number;
  dissimilarity_lambda: number;
  se_lambda: number;
  intra_nest_correlation_rho: number;
  iia_violation: boolean;
  status: string;
}

export interface ChoiceCoefficientItem {
  parameter: string;
  coefficient: number;
  se: number;
  t_statistic: number;
  p_value: number;
  ci_95: [number, number];
}

export interface ElasticityComparisonItem {
  base_alternative: string;
  within_nest_substitute: string;
  within_nest_name: string;
  within_nest_divergence_multiplier: number;
  cross_nest_substitute: string;
  cross_nest_name: string;
  interpretation: string;
}

export interface NestedLogitSummary {
  n_choice_situations: number;
  n_alternatives: number;
  n_nests: number;
  log_likelihood_nested_logit: number;
  log_likelihood_mnl_baseline: number;
  log_likelihood_null: number;
  mcfadden_pseudo_r2: number;
  lr_test_iia_statistic: number;
  lr_test_iia_p_value: number;
  iia_assumption_rejected: boolean;
  iia_status_verdict: string;
}

export interface NestedLogitResult {
  status: string;
  message?: string;
  overall_summary?: NestedLogitSummary;
  nests?: NestDiagnosticItem[];
  coefficients?: ChoiceCoefficientItem[];
  elasticity_comparison?: ElasticityComparisonItem;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface NestedLogitRequest {
  choice_question_id: string;
  alternative_question_id: string;
  nest_question_id: string;
  choice_id_question_id: string;
  attribute_question_ids: string[];
  cost_question_id?: string;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Automatic Debiased Machine Learning via Riesz Learning (Chernozhukov et al. 2022) Types ---
export interface AutoDMLRieszSummary {
  sample_size: number;
  n_covariates: number;
  basis_dimension_p: number;
  cross_fitting_splits_K: number;
  functional_type: string;
  functional_label: string;
  theta_autodml: number;
  se_autodml: number;
  t_statistic: number;
  p_value: number;
  ci_95: [number, number];
  theta_naive_plugin: number;
  se_naive_plugin: number;
  debiasing_correction_magnitude: number;
  beta_ols_benchmark: number;
  se_ols_benchmark: number;
  mean_outcome_r2: number;
  mean_riesz_loss: number;
  riesz_weight_mean: number;
  riesz_weight_sd: number;
  riesz_weight_min: number;
  riesz_weight_max: number;
  weight_stability_verdict: string;
}

export interface AutoDMLRieszResult {
  status: string;
  message?: string;
  overall_summary?: AutoDMLRieszSummary;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface AutoDMLRieszRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids: string[];
  functional_type?: 'ate' | 'policy_shift' | 'marginal_derivative';
  shift_delta?: number;
  n_splits?: number;
  ridge_lambda?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Local Instrumental Variables & Marginal Treatment Effects (Heckman & Vytlacil 2005) Types ---
export interface MTECurvePoint {
  u: number;
  mte: number;
  se: number;
  ci_95: [number, number];
}

export interface CausalParameterItem {
  estimate: number;
  se: number;
  ci_95?: [number, number];
  label: string;
}

export interface LIVMTESummary {
  sample_size: number;
  n_instruments: number;
  n_covariates: number;
  propensity_support: [number, number];
  propensity_mean: number;
  mte_intercept_delta1: number;
  mte_linear_slope_delta2: number;
  mte_quadratic_delta3: number;
  ate: CausalParameterItem;
  att: CausalParameterItem;
  atu: CausalParameterItem;
  late: CausalParameterItem;
  ols_benchmark: CausalParameterItem;
  standard_2sls: CausalParameterItem;
  sorting_on_gains_att_minus_ate: number;
  wald_test_essential_heterogeneity: number;
  wald_test_p_value: number;
  essential_heterogeneity_present: boolean;
  heterogeneity_verdict: string;
}

export interface LocalInstrumentalVariablesResult {
  status: string;
  message?: string;
  overall_summary?: LIVMTESummary;
  mte_curve?: MTECurvePoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface LocalInstrumentalVariablesRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  instrument_question_ids: string[];
  covariate_question_ids?: string[];
  n_grid_points?: number;
  trim_quantile?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Conformal Optimal Transport Counterfactual Distributional Alignment (Cuturi 2013; Courty 2017) Types ---
export interface ConformalOptimalTransportSummary {
  n_treated: number;
  n_control: number;
  n_covariates: number;
  entropic_regularization_eps: number;
  covariate_weight_kappa: number;
  conformal_confidence_level: number;
  wasserstein_2_distance: number;
  mean_outcome_treated: number;
  mean_outcome_control_observed: number;
  mean_outcome_control_counterfactual: number;
  optimal_transport_ate: number;
  optimal_transport_att: number;
  optimal_transport_atu: number;
  conformal_half_width_delta: number;
  conformal_coverage_guarantee_pct: number;
  quantiles: number[];
  treated_quantiles: number[];
  control_observed_quantiles: number[];
  control_counterfactual_quantiles: number[];
  quantile_treatment_effects: number[];
  counterfactual_quantile_shifts: number[];
}

export interface ConformalOptimalTransportResult {
  status: string;
  message?: string;
  overall_summary?: ConformalOptimalTransportSummary;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ConformalOptimalTransportRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids?: string[];
  reg_eps?: number;
  covariate_weight_kappa?: number;
  conformal_alpha?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Bayesian Nonparametric Dirichlet Process Mixture Deconvolution (Ferguson 1973; Escobar 1995) Types ---
export interface DPMComponentItem {
  component_id: number;
  weight: number;
  mean: number;
  sd_latent: number;
  sd_total_observed: number;
}

export interface DPMDeconvolutionSummary {
  sample_size: number;
  n_components_k: number;
  observed_mean: number;
  observed_variance: number;
  observed_sd: number;
  measurement_error_variance: number;
  measurement_error_sd: number;
  measurement_error_source: string;
  latent_true_variance: number;
  latent_true_sd: number;
  reliability_ratio: number;
  variance_reduction_pct: number;
  entropy_observed: number;
  entropy_deconvolved: number;
  entropy_reduction: number;
  quantiles_evaluated: number[];
  quantiles_deconvolved: number[];
  quantiles_observed: number[];
  quantile_compression_delta: number[];
}

export interface DPMDeconvolutionResult {
  status: string;
  message?: string;
  overall_summary?: DPMDeconvolutionSummary;
  components?: DPMComponentItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DPMDeconvolutionRequest {
  target_question_id: string;
  replicate_question_id?: string;
  error_variance_ratio?: number;
  max_components?: number;
  dp_alpha?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Multi-Cutoff Regression Discontinuity (Cattaneo 2015, Bertanha 2020) Types ---
export interface CutoffSpecificSummary {
  cutoff_value: number;
  sample_size: number;
  effective_n: number;
  tau_estimate: number;
  se: number;
  t_statistic: number;
  p_value: number;
  ci_95: [number, number];
}

export interface MultiCutoffRDSummary {
  sample_size: number;
  n_distinct_cutoffs: number;
  cutoffs_list: number[];
  bandwidth_h: number;
  effective_n_pooled: number;
  tau_pooled: number;
  se_pooled: number;
  t_statistic_pooled: number;
  p_value_pooled: number;
  ci_95_pooled: [number, number];
  wald_test_heterogeneity: number;
  p_value_heterogeneity: number;
  is_cutoff_heterogeneous: boolean;
  heterogeneity_verdict: string;
  mccrary_z_statistic: number;
  mccrary_p_value: number;
  is_manipulation_suspected: boolean;
  manipulation_verdict: string;
}

export interface MultiCutoffRDResult {
  status: string;
  message?: string;
  overall_summary?: MultiCutoffRDSummary;
  cutoff_summaries?: CutoffSpecificSummary[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface MultiCutoffRDRequest {
  outcome_question_id: string;
  running_question_id: string;
  cutoff_question_id?: string;
  group_question_id?: string;
  fixed_cutoffs?: Record<string, number>;
  covariate_question_ids?: string[];
  bandwidth?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- High-Dimensional Causal Mediation & Latent Path Invariance Types ---
export interface MediatorPathway {
  mediator_col: string;
  alpha_treatment_to_med: number;
  alpha_se: number;
  alpha_pvalue: number;
  beta_med_to_outcome: number;
  beta_se: number;
  beta_pvalue: number;
  indirect_effect: number;
  sobel_se: number;
  sobel_pvalue: number;
  mediation_share_pct: number;
  critical_rho_sensitivity: number;
  sensitivity_robustness: 'ROBUST' | 'MODERATE' | 'SENSITIVE';
  ci_lower?: number;
  ci_upper?: number;
}

export interface CausalEffectEstimate {
  estimate: number;
  se?: number;
  p_value?: number;
  ci_lower?: number;
  ci_upper?: number;
  percentage?: number;
}

export interface HighDimensionalMediationResult {
  status: string;
  message?: string;
  sample_size?: number;
  n_mediators?: number;
  treatment_variable?: string;
  outcome_variable?: string;
  confounder_variables?: string[];
  total_effect?: CausalEffectEstimate;
  natural_direct_effect?: CausalEffectEstimate;
  natural_indirect_effect?: CausalEffectEstimate;
  proportion_mediated?: CausalEffectEstimate;
  sequential_ignorability_sensitivity?: {
    dominant_rho_critical: number;
    robustness: 'ROBUST' | 'MODERATE' | 'SENSITIVE';
    interpretation: string;
  };
  mediator_pathways?: MediatorPathway[];
  latent_path_invariance?: {
    tested: boolean;
    subgroup_col?: string;
    groups_compared?: string[];
    wald_statistic?: number;
    p_value?: number;
    is_invariant: boolean;
    interpretation: string;
  };
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface HighDimensionalMediationRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  mediator_question_ids: string[];
  confounder_question_ids?: string[];
  subgroup_question_id?: string;
  n_boot?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Causal Inference under Network Interference & Spillover Types ---
export interface ExposureSampleSizes {
  isolated_control: number;
  direct_only: number;
  spillover_only: number;
  joint_treated: number;
}

export interface PotentialOutcomeMeans {
  isolated_control: number;
  direct_only: number;
  spillover_only: number;
  joint_treated: number;
}

export interface NetworkCausalEffect {
  estimate: number;
  se: number;
  z_stat?: number;
  p_value?: number;
  ci_95: [number, number];
}

export interface NetworkSpilloverResult {
  status: string;
  message?: string;
  sample_size?: number;
  n_clusters?: number;
  outcome_variable?: string;
  treatment_variable?: string;
  cluster_variable?: string;
  exposure_sample_sizes?: ExposureSampleSizes;
  potential_outcome_means?: PotentialOutcomeMeans;
  average_direct_effect?: NetworkCausalEffect;
  average_spillover_effect?: NetworkCausalEffect;
  total_overall_effect?: NetworkCausalEffect;
  spillover_share_pct?: number;
  sutva_test?: {
    is_violated: boolean;
    p_value: number;
    verdict: string;
  };
  dosage_regression?: {
    direct_coefficient: number;
    direct_se: number;
    direct_pvalue: number;
    peer_spillover_slope: number;
    spillover_se: number;
    spillover_pvalue: number;
    interpretation: string;
  };
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface NetworkSpilloverRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  cluster_question_id: string;
  covariate_question_ids?: string[];
  spillover_threshold?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Dynamic Spatial Panel Econometrics & Spatio-Temporal Diffusion Types ---
export interface SpatioTemporalParameter {
  estimate: number;
  se: number;
  p_value: number;
}

export interface SpatialMultiplierImpact {
  direct: number;
  indirect: number;
  total: number;
  spillover_share_pct: number;
}

export interface DynamicSpatialPanelResult {
  status: string;
  message?: string;
  sample_size?: number;
  effective_panel_observations?: number;
  n_regions?: number;
  n_time_periods?: number;
  outcome_variable?: string;
  region_variable?: string;
  time_variable?: string;
  spatio_temporal_parameters?: {
    time_persistence_gamma: SpatioTemporalParameter;
    contemporaneous_spatial_rho: SpatioTemporalParameter;
    spatio_temporal_diffusion_eta: SpatioTemporalParameter;
  };
  system_stability?: {
    is_stable: boolean;
    max_eigen_modulus: number;
    persistence_half_life_periods: number;
    interpretation: string;
  };
  short_run_impacts?: SpatialMultiplierImpact;
  long_run_impacts?: SpatialMultiplierImpact;
  covariate_estimates?: Array<{
    covariate: string;
    coefficient: number;
    se: number;
    p_value: number;
  }>;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DynamicSpatialPanelRequest {
  outcome_question_id: string;
  region_question_id: string;
  time_question_id: string;
  covariate_question_ids?: string[];
  lat_question_id?: string;
  lon_question_id?: string;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Continuous Policy Shift & Doubly Robust Dosage Response Types ---
export interface DRCDosagePoint {
  dosage_level: number;
  outcome_estimate: number;
  se: number;
  ci_95: [number, number];
  marginal_derivative: number;
}

export interface ContinuousPolicyShiftResult {
  status: string;
  message?: string;
  sample_size?: number;
  outcome_variable?: string;
  treatment_variable?: string;
  covariates_controlled?: string[];
  bandwidth?: number;
  treatment_support?: {
    min_evaluated: number;
    max_evaluated: number;
    current_mean: number;
    optimal_dosage: number;
  };
  policy_shift?: {
    delta_shift: number;
    average_policy_effect: number;
    se: number;
    p_value: number;
    ci_95: [number, number];
    interpretation: string;
  };
  dose_response_curve?: DRCDosagePoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ContinuousPolicyShiftRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids?: string[];
  grid_points?: number;
  shift_delta?: number;
  bandwidth?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Generalized Synthetic Control & Latent Interactive Factor (Xu 2017) Types ---
export interface GsynthEventStudyPoint {
  relative_time: number;
  att: number;
  se: number;
  p_value: number;
  ci_95: [number, number];
  n_treated_units: number;
  is_post_treatment: boolean;
}

export interface GsynthTreatedUnitSummary {
  unit: string;
  adoption_time: number;
  pre_rmspe: number;
  post_mean_effect: number;
}

export interface GeneralizedSyntheticControlResult {
  status: string;
  message?: string;
  sample_size?: number;
  n_treated_units?: number;
  n_control_units?: number;
  n_time_periods?: number;
  n_latent_factors?: number;
  variance_explained_ratio?: number[];
  overall_att?: {
    estimate: number;
    se: number;
    p_value: number;
    ci_95: [number, number];
    interpretation: string;
  };
  pre_treatment_diagnostics?: {
    mean_pre_rmspe: number;
    mean_pre_placebo: number;
    parallel_trends_supported: boolean;
  };
  event_study_trajectory?: GsynthEventStudyPoint[];
  treated_unit_summaries?: GsynthTreatedUnitSummary[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface GeneralizedSyntheticControlRequest {
  outcome_question_id: string;
  unit_question_id: string;
  time_question_id: string;
  treatment_question_id: string;
  covariate_question_ids?: string[];
  n_factors?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Choice-Based Conjoint Hierarchical Bayes & Market Simulator (Rossi et al. 2005) Types ---
export interface ConjointPartWorthUtility {
  attribute: string;
  level: string;
  is_reference: boolean;
  mean_part_worth: number;
  se: number;
}

export interface ConjointAttributeImportance {
  mean_importance: number;
  median_importance: number;
  std_dev: number;
}

export interface ConjointWTPItem {
  attribute: string;
  level: string;
  mean_wtp: number;
  median_wtp: number;
  ci_95: [number, number];
}

export interface ConjointMarketSimulationItem {
  product_name: string;
  share_of_preference: number;
  first_choice_share: number;
  mean_utility: number;
}

export interface HierarchicalBayesConjointResult {
  status: string;
  message?: string;
  sample_size?: number;
  n_respondents?: number;
  attribute_importance?: Record<string, ConjointAttributeImportance>;
  part_worth_utilities?: ConjointPartWorthUtility[];
  wtp_estimates?: Record<string, ConjointWTPItem>;
  market_simulation?: ConjointMarketSimulationItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface HierarchicalBayesConjointRequest {
  choice_question_id: string;
  respondent_question_id: string;
  attribute_question_ids: string[];
  price_question_id?: string;
  simulation_profiles?: Array<Record<string, any>>;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Nonparametric Boundary Kernel Deconvolution (Delaigle & Meister 2008) Types ---
export interface DeconvolutionMoments {
  mean: number;
  std_dev: number;
  skewness: number;
  percentiles: number[];
}

export interface DeconvolutionDensityPoint {
  x: number;
  f_observed: number;
  f_deconvoluted: number;
}

export interface BoundaryKernelDeconvolutionResult {
  status: string;
  message?: string;
  sample_size?: number;
  variable_evaluated?: string;
  reliability_ratio?: number;
  error_structure?: string;
  bandwidth?: number;
  attenuation_correction_factor?: number;
  dispersion_metrics?: {
    observed_variance: number;
    deconvoluted_variance: number;
    variance_reduction_percent: number;
    noise_standard_deviation: number;
  };
  moments_comparison?: {
    observed: DeconvolutionMoments;
    deconvoluted: DeconvolutionMoments;
  };
  density_profile?: DeconvolutionDensityPoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface BoundaryKernelDeconvolutionRequest {
  variable_question_id: string;
  reliability_ratio?: number;
  error_type?: string;
  lower_bound?: number;
  grid_points?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Targeted Maximum Likelihood Estimation (TMLE; van der Laan & Rose 2011) Types ---
export interface TMLEEstimatorComparison {
  method: string;
  estimate: number;
  se: number;
  ci_95: [number, number];
  p_value: number;
  is_semiparametric_efficient: boolean;
}

export interface TargetedMaximumLikelihoodResult {
  status: string;
  message?: string;
  sample_size?: number;
  n_treated?: number;
  n_control?: number;
  outcome_variable?: string;
  treatment_variable?: string;
  covariates_controlled?: string[];
  ate_tmle?: {
    estimate: number;
    se: number;
    z_stat: number;
    p_value: number;
    ci_95: [number, number];
    ey1_counterfactual: number;
    ey0_counterfactual: number;
    interpretation: string;
  };
  targeted_fluctuation?: {
    epsilon_fluctuation: number;
    eic_mean_residual: number;
    eic_variance: number;
    equation_solved: boolean;
  };
  propensity_diagnostics?: {
    min_propensity: number;
    max_propensity: number;
    mean_treated_propensity: number;
    mean_control_propensity: number;
    positivity_violation_risk: string;
  };
  estimators_comparison?: TMLEEstimatorComparison[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface TargetedMaximumLikelihoodRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  covariate_question_ids?: string[];
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Copula-Based Endogeneity Correction (Park & Gupta 2012) Types ---
export interface CopulaNonNormalityDiagnostics {
  shapiro_w: number;
  shapiro_p: number;
  skewness: number;
  kurtosis: number;
  is_non_normal: boolean;
  status_label: string;
  regressor_copula_correlation: number;
}

export interface CopulaModelEstimate {
  estimate: number;
  se?: number;
  se_asymptotic?: number;
  se_bootstrap?: number;
  t_stat: number;
  p_value: number;
  ci_95: [number, number];
  r2: number;
}

export interface CopulaEndogeneityTest {
  lambda_pstar: number;
  se_lambda: number;
  se_bootstrap: number;
  t_stat: number;
  p_value: number;
  ci_95: [number, number];
  implied_rho: number;
  is_endogenous: boolean;
  conclusion: string;
}

export interface CopulaBiasCorrection {
  absolute_bias: number;
  relative_bias_pct: number;
  recommended_estimator: string;
}

export interface CopulaEndogeneityResult {
  status: string;
  message?: string;
  sample_size?: number;
  copula_family?: string;
  non_normality_diagnostics?: CopulaNonNormalityDiagnostics;
  naive_ols?: CopulaModelEstimate;
  copula_augmented?: CopulaModelEstimate;
  endogeneity_test?: CopulaEndogeneityTest;
  bias_correction?: CopulaBiasCorrection;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface CopulaEndogeneityRequest {
  outcome_question_id: string;
  endogenous_question_id: string;
  covariate_question_ids?: string[];
  copula_family?: 'gaussian' | 'clayton';
  bootstrap_replications?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Causal Survival Analysis & RMST Engine (Royston & Parmar 2013) Types ---
export interface CausalRMSTDifference {
  estimate: number;
  se_asymptotic: number;
  se_bootstrap: number;
  z_stat: number;
  p_value: number;
  ci_95: [number, number];
  is_significant: boolean;
}

export interface CausalRMTLMetrics {
  rmtl_treated: number;
  rmtl_control: number;
  rmtl_reduction_pct: number;
}

export interface MilestoneSurvivalTau {
  survival_treated: number;
  survival_control: number;
  risk_difference: number;
}

export interface SurvivalCurvePoint {
  time: number;
  survival_treated: number;
  survival_control: number;
  survival_difference: number;
}

export interface CausalSurvivalRMSTResult {
  status: string;
  message?: string;
  sample_size?: number;
  n_treated?: number;
  n_control?: number;
  tau_horizon?: number;
  rmst_treated?: number;
  rmst_control?: number;
  causal_rmst_difference?: CausalRMSTDifference;
  rmst_ratio?: number;
  rmtl_metrics?: CausalRMTLMetrics;
  milestone_survival_tau?: MilestoneSurvivalTau;
  curve_points?: SurvivalCurvePoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface CausalSurvivalRMSTRequest {
  time_question_id: string;
  event_question_id: string;
  treatment_question_id: string;
  covariate_question_ids?: string[];
  tau_horizon?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Dynamic Discrete Choice Structural Dynamic Programming (Rust 1987 NFXP) Types ---
export interface DDCStructuralParameter {
  estimate: number;
  se?: number;
  ci_95?: [number, number];
  p_value?: number;
}

export interface DDCEquilibriumThresholds {
  baseline_threshold_state: number;
  counterfactual_threshold_state: number;
  baseline_stationary_rate_pct: number;
  counterfactual_stationary_rate_pct: number;
  rate_delta_pct: number;
}

export interface DDCStateProfile {
  state_bin: number;
  state_value: number;
  expected_value_maintain: number;
  expected_value_replace: number;
  choice_prob_baseline: number;
  choice_prob_counterfactual: number;
  stationary_density_pct: number;
}

export interface DynamicDiscreteChoiceResult {
  status: string;
  message?: string;
  sample_size?: number;
  num_states?: number;
  discount_factor?: number;
  log_likelihood?: number;
  structural_parameters?: {
    replacement_cost_rc: DDCStructuralParameter;
    linear_operating_cost_th1: DDCStructuralParameter;
    quadratic_operating_cost_th2: DDCStructuralParameter;
  };
  equilibrium_thresholds?: DDCEquilibriumThresholds;
  state_profiles?: DDCStateProfile[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DynamicDiscreteChoiceRequest {
  state_question_id: string;
  decision_question_id: string;
  discount_factor?: number;
  num_discretized_states?: number;
  counterfactual_subsidy_pct?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Synthetic Difference-in-Differences (SDID; Arkhangelsky et al. 2021 AER) Types ---
export interface SDIDDonorWeight {
  unit_id: string;
  weight: number;
  weight_pct: number;
}

export interface SDIDPeriodProfile {
  period: string;
  period_index: number;
  is_post_treatment: boolean;
  treated_mean: number;
  synthetic_control_mean: number;
  raw_control_mean: number;
  time_weight: number;
}

export interface SDIDEstimates {
  sdid_tau: number;
  sdid_se: number;
  sdid_ci_95: [number, number];
  sdid_z_stat: number;
  sdid_p_value: number;
  is_significant: boolean;
  did_tau: number;
  scm_tau: number;
  bias_correction_vs_did: number;
}

export interface SDIDDiagnostics {
  rmse_sdid_pre: number;
  rmse_did_pre: number;
  rmse_reduction_pct: number;
  effective_donors_n_eff: number;
  l2_regularization_zeta: number;
}

export interface SyntheticDiffInDiffResult {
  status: string;
  message?: string;
  sample_size?: number;
  num_units_total?: number;
  num_treated_units?: number;
  num_control_units?: number;
  num_periods_total?: number;
  num_pre_periods?: number;
  num_post_periods?: number;
  first_treated_period?: string;
  estimates?: SDIDEstimates;
  diagnostics?: SDIDDiagnostics;
  top_donor_weights?: SDIDDonorWeight[];
  period_profiles?: SDIDPeriodProfile[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface SyntheticDiffInDiffRequest {
  unit_question_id: string;
  time_question_id: string;
  treatment_question_id: string;
  outcome_question_id: string;
  l2_regularization_zeta?: number;
  num_bootstrap_reps?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- RIF Oaxaca-Blinder Decomposition (Firpo, Fortin, & Lemieux 2009, 2018) Types ---
export interface RIFCovariateContribution {
  variable_name: string;
  mean_group_a: number;
  mean_group_b: number;
  mean_diff: number;
  explained_effect: number;
  unexplained_effect: number;
  total_effect: number;
}

export interface RIFQuantilePoint {
  quantile: number;
  group_a_val: number;
  group_b_val: number;
  total_gap: number;
  explained_gap: number;
  unexplained_gap: number;
  explained_pct: number;
  unexplained_pct: number;
  detailed_contributions?: RIFCovariateContribution[];
}

export interface RIFOaxacaMeanDecomposition {
  group_a_mean: number;
  group_b_mean: number;
  total_mean_gap: number;
  explained_endowments: number;
  unexplained_coefficients: number;
  explained_pct: number;
  unexplained_pct: number;
}

export interface RIFOaxacaMedianEstimates {
  total_median_gap: number;
  explained_endowments: number;
  unexplained_coefficients: number;
  unexplained_se: number;
  unexplained_ci_95: [number, number];
  unexplained_z_stat: number;
  unexplained_p_value: number;
  is_significant: boolean;
  explained_pct: number;
  unexplained_pct: number;
}

export interface RIFGlassCeilingDiagnostics {
  gap_p10: number;
  gap_p90: number;
  gap_p90_minus_p10: number;
  diagnostic_label: string;
}

export interface RIFOaxacaDecompositionResult {
  status: string;
  message?: string;
  sample_size?: number;
  group_a_label?: string;
  group_b_label?: string;
  sample_counts?: {
    group_a_n: number;
    group_b_n: number;
  };
  mean_decomposition?: RIFOaxacaMeanDecomposition;
  median_rif_estimates?: RIFOaxacaMedianEstimates;
  glass_ceiling_diagnostics?: RIFGlassCeilingDiagnostics;
  quantile_decomposition_curve?: RIFQuantilePoint[];
  detailed_covariates?: RIFCovariateContribution[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface RIFOaxacaDecompositionRequest {
  group_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  reference_group_val?: any;
  target_quantiles?: number[];
  num_bootstrap_reps?: number;
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Difference-in-Discontinuities (Diff-in-Disc / RD-DID; Grembi et al. 2016 AER) Types ---
export interface DiffInDiscBandwidthPoint {
  multiplier: number;
  bandwidth: number;
  tau_estimate: number;
  se: number;
  ci_95: [number, number];
  p_value: number;
}

export interface DiffInDiscEstimates {
  diff_in_disc_tau: number;
  se: number;
  ci_95: [number, number];
  t_stat: number;
  p_value: number;
  is_significant: boolean;
  naive_post_rd_tau: number;
  baseline_pre_jump_gamma0: number;
  baseline_pre_p_value: number;
  bias_correction_delta: number;
}

export interface DiffInDiscDiagnostics {
  optimal_bandwidth_h: number;
  kernel_type: string;
  effective_sample_size_n_h: number;
  mccrary_density_p_value: number;
  mccrary_sorting_detected: boolean;
}

export interface DiffInDiscontinuitiesResult {
  status: string;
  message?: string;
  sample_size_total?: number;
  sample_size_effective_h?: number;
  cutoff_threshold?: number;
  post_period_label?: string;
  estimates?: DiffInDiscEstimates;
  diagnostics?: DiffInDiscDiagnostics;
  bandwidth_sensitivity?: DiffInDiscBandwidthPoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DiffInDiscontinuitiesRequest {
  running_question_id: string;
  cutoff: number;
  period_question_id: string;
  outcome_question_id: string;
  unit_question_id?: string;
  post_period_val?: any;
  bandwidth?: number;
  kernel_type?: 'triangular' | 'epanechnikov' | 'uniform';
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}


// --- Cluster-Robust Double Machine Learning (Cluster-DML; Chiang et al. 2022) Types ---
export interface ClusterDMLProfileItem {
  cluster_id: string;
  sample_size: number;
  treatment_mean: number;
  outcome_mean: number;
  cluster_score: number;
  contribution_pct: number;
}

export interface ClusterDMLEstimates {
  theta: number;
  se_cluster: number;
  ci_95_cluster: [number, number];
  t_stat_cluster: number;
  p_value_cluster: number;
  is_significant: boolean;
  se_naive: number;
  ci_95_naive: [number, number];
  p_value_naive: number;
  se_inflation_ratio: number;
}

export interface ClusterDMLDiagnostics {
  num_clusters: number;
  avg_cluster_size: number;
  min_cluster_size: number;
  max_cluster_size: number;
  intra_cluster_correlation_icc: number;
  r2_outcome_ml: number;
  r2_treatment_ml: number;
  ml_algorithm: string;
  k_folds: number;
}

export interface ClusterDMLResult {
  status: string;
  message?: string;
  sample_size?: number;
  estimates?: ClusterDMLEstimates;
  diagnostics?: ClusterDMLDiagnostics;
  cluster_profiles?: ClusterDMLProfileItem[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface ClusterDMLRequest {
  cluster_question_id: string;
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  n_splits?: number;
  ml_model?: 'random_forest' | 'gradient_boost' | 'ridge';
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Distributional Synthetic Controls & Counterfactual Density Decomposition (Chernozhukov et al. 2021) ---
export interface DSCDonorWeightItem {
  donor_unit: string;
  synthetic_weight: number;
}

export interface DSCQuantilePoint {
  tau: number;
  observed_q: number;
  synthetic_q: number;
  quantile_treatment_effect: number;
}

export interface DSCInequalityDiagnostics {
  observed_gini: number;
  synthetic_gini: number;
  delta_gini: number;
  observed_iqr: number;
  synthetic_iqr: number;
  delta_iqr: number;
  first_order_stochastic_dominance: boolean;
  second_order_stochastic_dominance: boolean;
}

export interface DistributionalSyntheticControlResult {
  status: string;
  message?: string;
  sample_size?: number;
  treated_unit?: string;
  num_donors?: number;
  pre_periods?: string[];
  post_periods?: string[];
  wasserstein_distance?: number;
  permutation_p_value?: number;
  mean_treatment_effect?: number;
  median_treatment_effect?: number;
  inequality_diagnostics?: DSCInequalityDiagnostics;
  donor_weights?: DSCDonorWeightItem[];
  quantile_curve?: DSCQuantilePoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface DistributionalSyntheticControlRequest {
  unit_question_id: string;
  period_question_id: string;
  outcome_question_id: string;
  treated_unit_val: string;
  post_period_vals: string[];
  num_quantiles?: number;
  l2_penalty?: number;
  num_placebos?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Nonparametric Copula Causal Sensitivity Bounds (Cinelli & Hazlett 2020) ---
export interface CSBBaselineEstimates {
  tau_hat: number;
  se_hat: number;
  t_statistic: number;
  p_value: number;
  partial_r2_treatment: number;
}

export interface CSBRobustnessValues {
  rv_q_to_zero: number;
  rv_alpha_significance: number;
  robustness_tier: string;
  tier_description: string;
}

export interface CSBCovariateBenchmark {
  name: string;
  r2_d: number;
  r2_y: number;
  bias_impact_1x: number;
  adjusted_tau_1x: number;
  retains_significance: boolean;
}

export interface CSBWorstCasePoint {
  r2_strength: number;
  bias: number;
  adjusted_tau: number;
}

export interface CSBCopulaTailBounds {
  kendall_tau: number;
  clayton_lower_tail: number;
  gumbel_upper_tail: number;
}

export interface CausalSensitivityBoundsResult {
  status: string;
  message?: string;
  sample_size?: number;
  degrees_of_freedom?: number;
  baseline_estimates?: CSBBaselineEstimates;
  robustness_values?: CSBRobustnessValues;
  covariate_benchmarks?: CSBCovariateBenchmark[];
  worst_case_curve?: CSBWorstCasePoint[];
  copula_tail_bounds?: CSBCopulaTailBounds;
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface CausalSensitivityBoundsRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  alpha_level?: number;
  scope?: 'all' | 'verified_clean';
}

// --- Causal Matrix Completion & Nuclear Norm Minimization (Athey et al. 2021) ---
export interface CMCDimensions {
  units_count: number;
  periods_count: number;
}

export interface CMCAdoptionCounts {
  control_cells: number;
  treated_cells: number;
}

export interface CMCAlgorithmConvergence {
  converged: boolean;
  iterations: number;
  latent_rank: number;
  control_rmse: number;
}

export interface CMCEstimates {
  att: number;
  se: number;
  ci_low: number;
  ci_high: number;
  p_value: number;
  median_att: number;
}

export interface CMCUnitHeterogeneity {
  unit: string;
  treated_periods_count: number;
  unit_att: number;
}

export interface CMCEventStudyPoint {
  event_time: number;
  att: number;
  ci_low: number;
  ci_high: number;
  sample_count: number;
}

export interface CausalMatrixCompletionResult {
  status: string;
  message?: string;
  sample_size?: number;
  dimensions?: CMCDimensions;
  adoption_counts?: CMCAdoptionCounts;
  algorithm_convergence?: CMCAlgorithmConvergence;
  estimates?: CMCEstimates;
  unit_heterogeneity?: CMCUnitHeterogeneity[];
  event_study_trajectory?: CMCEventStudyPoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}

export interface CausalMatrixCompletionRequest {
  unit_question_id: string;
  period_question_id: string;
  outcome_question_id: string;
  treatment_question_id: string;
  lambda_nuc?: number;
  max_iter?: number;
  tol?: number;
  scope?: 'all' | 'verified_clean';
}


export interface IVLATEMonotonicityTest {
  passed: boolean;
  min_density_difference: number;
  defiers_detected: boolean;
}

export interface IVLATEComplierInequality {
  gini_treated_c: number;
  gini_control_c: number;
  delta_gini_c: number;
  iqr_treated_c: number;
  iqr_control_c: number;
  delta_iqr_c: number;
  first_order_stochastic_dominance: boolean;
}

export interface IVLATEQuantilePoint {
  tau: number;
  q_treated_complier: number;
  q_control_complier: number;
  qte_complier: number;
}

export interface IVLATEQuantileRequest {
  outcome_question_id: string;
  treatment_question_id: string;
  instrument_question_id: string;
  covariate_question_ids?: string[];
  num_quantiles?: number;
  scope?: 'all' | 'verified_clean';
}

export interface IVLATEQuantileResult {
  status: string;
  message?: string;
  sample_size?: number;
  complier_share?: number;
  first_stage_diff?: number;
  mean_late?: number;
  median_qte_complier?: number;
  monotonicity_test?: IVLATEMonotonicityTest;
  complier_inequality?: IVLATEComplierInequality;
  quantile_curve?: IVLATEQuantilePoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}


export interface ConformalSubgroupCounts {
  treated: number;
  control: number;
  calibration_set: number;
  training_set: number;
}

export interface ConformalCutoffs {
  cutoff_q0: number;
  cutoff_q1: number;
  coverage_control: number;
  coverage_treated: number;
}

export interface ConformalTreatmentSummary {
  ate_conformal: number;
  avg_width_y0: number;
  avg_width_y1: number;
  avg_width_ite: number;
  sig_positive_ite_pct: number;
  sig_negative_ite_pct: number;
}

export interface ConformalSampleITEPoint {
  observation_id: number;
  treatment: number;
  factual_outcome: number;
  predicted_ite: number;
  ite_lower_bound: number;
  ite_upper_bound: number;
  band_width: number;
  significant: boolean;
}

export interface ConformalCausalRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  alpha?: number;
  calibration_ratio?: number;
  scope?: 'all' | 'verified_clean';
}

export interface ConformalCausalResult {
  status: string;
  message?: string;
  sample_size?: number;
  nominal_coverage?: number;
  empirical_calibration_coverage?: number;
  subgroup_counts?: ConformalSubgroupCounts;
  conformal_cutoffs?: ConformalCutoffs;
  treatment_effect_summary?: ConformalTreatmentSummary;
  sample_ite_points?: ConformalSampleITEPoint[];
  svg_visualization?: string;
  apa_narrative?: string;
}


export interface BCFSubgroupCounts {
  treated: number;
  control: number;
}

export interface BCFATEEstimates {
  posterior_mean: number;
  posterior_sd: number;
  ci_lower_95: number;
  ci_upper_95: number;
  prob_positive_effect: number;
}

export interface BCFATTEstimates {
  posterior_mean: number;
  posterior_sd: number;
  ci_lower_95: number;
  ci_upper_95: number;
}

export interface BCFMCMCDiagnostics {
  residual_std: number;
  residual_variance: number;
  effective_sample_size: number;
}

export interface BCFPropensityQuintile {
  quintile: number;
  quintile_label: string;
  sample_count: number;
  cate_mean: number;
  cate_ci_lower: number;
  cate_ci_upper: number;
}

export interface BCFSampleCATE {
  observation_id: number;
  treatment: number;
  propensity_score: number;
  prognostic_baseline: number;
  cate_point_estimate: number;
  cate_lower_bci: number;
  cate_upper_bci: number;
}

export interface BayesianCausalForestRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  num_mcmc_draws?: number;
  credibility_level?: number;
  scope?: 'all' | 'verified_clean';
}

export interface BayesianCausalForestResult {
  status: string;
  message?: string;
  sample_size?: number;
  mcmc_draws_count?: number;
  effective_sample_size?: number;
  subgroup_counts?: BCFSubgroupCounts;
  ate_estimates?: BCFATEEstimates;
  att_estimates?: BCFATTEstimates;
  mcmc_diagnostics?: BCFMCMCDiagnostics;
  propensity_quintiles?: BCFPropensityQuintile[];
  sample_cate_estimates?: BCFSampleCATE[];
  svg_visualization?: string;
  apa_narrative?: string;
}


export interface SpatialDIDEffect {
  estimate: number;
  std_error: number;
  t_statistic: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
}

export interface SpatialDIDMoranDiagnostic {
  moran_i: number;
  z_score: number;
  p_value: number;
  residual_autocorrelation_cleared: boolean;
}

export interface SpatialDIDModelFit {
  r_squared: number;
  sample_size: number;
  degrees_of_freedom: number;
}

export interface SpatialDIDRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  lat_field?: string;
  lon_field?: string;
  time_question_id?: string;
  covariate_question_ids?: string[];
  weight_type?: 'inverse_distance' | 'knn';
  knn_k?: number;
  power?: number;
  scope?: 'all' | 'verified_clean';
}

export interface SpatialDIDResult {
  status: string;
  message?: string;
  sample_size?: number;
  weights_type?: string;
  direct_effect?: SpatialDIDEffect;
  spillover_effect?: SpatialDIDEffect;
  total_impact?: SpatialDIDEffect;
  morans_i_diagnostic?: SpatialDIDMoranDiagnostic;
  model_fit?: SpatialDIDModelFit;
  svg_visualization?: string;
  apa_narrative?: string;
}


// --- Entropy Balancing (Hainmueller 2012) Interfaces ---
export interface EntropyBalancingCovariateBalance {
  covariate_id: string;
  covariate_name: string;
  mean_treated: number;
  mean_control_unweighted: number;
  mean_control_weighted: number;
  smd_unweighted: number;
  smd_weighted: number;
  var_ratio_unweighted: number;
  var_ratio_weighted: number;
}

export interface EntropyBalancingEffect {
  att: number;
  se: number;
  t_stat: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
}

export interface EntropyBalancingDiagnostics {
  converged: boolean;
  iterations: number;
  entropy_loss: number;
  effective_sample_size: number;
  ess_ratio: number;
  max_weight: number;
  min_weight: number;
  max_smd_post: number;
}

export interface EntropyBalancingSampleWeight {
  unit_index: number;
  raw_outcome: number;
  entropy_weight: number;
  normalized_multiplier: number;
}

export interface EntropyBalancingRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  moment_orders?: number[];
  tolerance?: number;
  max_iterations?: number;
  scope?: 'all' | 'verified_clean';
}

export interface EntropyBalancingResult {
  status: string;
  sample_size: number;
  treated_count: number;
  control_count: number;
  treatment_effect: EntropyBalancingEffect;
  covariate_balance: EntropyBalancingCovariateBalance[];
  diagnostics: EntropyBalancingDiagnostics;
  sample_weights: EntropyBalancingSampleWeight[];
  svg_visualization: string;
  apa_narrative: string;
}


// --- Covariate Balancing Propensity Score (CBPS; Imai & Ratkovic 2014) Interfaces ---
export interface CBPSCovariateBalance {
  covariate_id: string;
  covariate_name: string;
  mean_treated_raw: number;
  mean_control_raw: number;
  mean_treated_weighted: number;
  mean_control_weighted: number;
  smd_raw: number;
  smd_weighted: number;
  var_ratio_raw: number;
  var_ratio_weighted: number;
}

export interface CBPSEffect {
  effect: number;
  se: number;
  t_stat: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
}

export interface CBPSDiagnostics {
  converged: boolean;
  iterations: number;
  method: string;
  estimand: string;
  hansen_j_stat: number;
  hansen_j_df: number;
  hansen_j_p_value: number;
  specification_valid: boolean;
}

export interface CBPSOverlapMetrics {
  min_propensity_treated: number;
  max_propensity_treated: number;
  min_propensity_control: number;
  max_propensity_control: number;
  common_support_overlap: boolean;
  effective_sample_size_treated: number;
  effective_sample_size_control: number;
  max_smd_post: number;
}

export interface CBPSPropensityPoint {
  unit_index: number;
  treatment: number;
  outcome: number;
  propensity_score: number;
  cbps_weight: number;
}

export interface CBPSRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids: string[];
  method?: 'overidentified' | 'just_identified';
  estimand?: 'ATE' | 'ATT';
  max_iterations?: number;
  tolerance?: number;
  scope?: 'all' | 'verified_clean';
}

export interface CBPSResult {
  status: string;
  sample_size: number;
  treated_count: number;
  control_count: number;
  estimand: string;
  causal_effect: CBPSEffect;
  covariate_balance: CBPSCovariateBalance[];
  diagnostics: CBPSDiagnostics;
  overlap_metrics: CBPSOverlapMetrics;
  sample_points: CBPSPropensityPoint[];
  svg_visualization: string;
  apa_narrative: string;
}


// --- Robust E-Values & Multi-Bias Causal Sensitivity (VanderWeele & Ding 2017) Interfaces ---
export interface EValueResults {
  rr_equivalent: number;
  ci_lower_rr: number;
  ci_upper_rr: number;
  is_protective: boolean;
  e_value_estimate: number;
  e_value_ci: number;
  ci_closest_to_null: number;
  ci_already_spans_null: boolean;
  selection_bias_factor: number;
  misclassification_factor: number;
  adjusted_rr_after_selection_and_measurement: number;
  e_value_confounding_remaining: number;
  e_value_joint_equal_biases: number;
}

export interface EValueBenchmark {
  name: string;
  rr_benchmark: number;
}

export interface EValueRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  covariate_question_ids?: string[];
  effect_type?: 'OLS_CONTINUOUS' | 'RR' | 'OR' | 'HR' | 'COHEN_D';
  selection_bias_rr?: number;
  misclassification_rr?: number;
  scope?: 'all' | 'verified_clean';
}

export interface EValueResult {
  status: string;
  sample_size: number;
  effect_type: string;
  point_estimate: number;
  standard_error: number;
  outcome_sd: number;
  e_value_results: EValueResults;
  benchmarks: EValueBenchmark[];
  svg_visualization: string;
  apa_narrative: string;
}


// --- Two-Stage Residual Inclusion (2SRI) & Control Function Causal Engine (Terza et al. 2008) ---
export interface ControlFunction2SRIFirstStage {
  f_statistic: number;
  p_value: number;
  r_squared: number;
  weak_instrument: boolean;
  instrument_count: number;
  instruments: string[];
}

export interface ControlFunction2SRIEndogeneityTest {
  residual_coefficient_rho: number;
  bootstrap_se: number;
  z_statistic: number;
  p_value: number;
  is_endogenous: boolean;
  interpretation: string;
}

export interface ControlFunction2SRIEffectItem {
  estimate: number;
  bootstrap_se: number;
  ci_lower: number;
  ci_upper: number;
  p_value: number;
}

export interface ControlFunction2SRICausalEffects {
  ate: ControlFunction2SRIEffectItem;
  att: ControlFunction2SRIEffectItem;
  structural_alpha: number;
  structural_alpha_se: number;
}

export interface ControlFunction2SRIModelComparison {
  model: string;
  treatment_coefficient: number;
  bias_risk: string;
}

export interface ControlFunction2SRIRequest {
  treatment_question_id: string;
  outcome_question_id: string;
  instrument_question_ids: string[];
  covariate_question_ids?: string[];
  outcome_family?: 'logistic' | 'linear' | 'poisson';
  n_bootstraps?: number;
  scope?: 'all' | 'verified_clean';
}

export interface ControlFunction2SRIResult {
  status: string;
  sample_size: number;
  treated_count: number;
  control_count: number;
  treatment_type: string;
  outcome_family: string;
  first_stage: ControlFunction2SRIFirstStage;
  endogeneity_test: ControlFunction2SRIEndogeneityTest;
  causal_effects: ControlFunction2SRICausalEffects;
  model_comparison: ControlFunction2SRIModelComparison[];
  svg_visualization: string;
  apa_narrative: string;
}
