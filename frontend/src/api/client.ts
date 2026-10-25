import {
  Survey,
  SurveyListItem,
  ResponseListItem,
  ResponseDetail,
  SurveyAnalytics,
  Question,
  CleansingCriteria,
  CleansingReport,
  BatchAnomalyQuarantineRequest,
  BatchAnomalyQuarantineResult,
  BatchRestoreQuarantineRequest,
  BatchRestoreQuarantineResult,
  CognitivePretestReport,
  MediationAnalysisRequest,
  MediationAnalysisResult,
  MannWhitneyURequest,
  MannWhitneyUResult,
  WilcoxonSignedRankRequest,
  WilcoxonSignedRankResult,
  KruskalWallisRequest,
  KruskalWallisResult,
  MissingDataDiagnosticsResult,
  MissingDataImputationResult,
  ScaleEquatingResult,
  MeasurementInvarianceResult,
  CommonMethodBiasResult,
  ModerationAnalysisResult,
  ModeratedMediationRequest,
  ModeratedMediationResult,
  ComplexSamplingRequest,
  ComplexSamplingResult,
  PSMAnalysisRequest,
  PSMAnalysisResult,
  TopicModelAnalysisRequest,
  TopicModelAnalysisResult,
  PsychometricNetworkRequest,
  PsychometricNetworkResult,
  IRT2PLAnalysisRequest,
  IRT2PLAnalysisResult,
  SurvivalAnalysisRequest,
  SurvivalAnalysisResult,
  MultilevelAnalysisRequest,
  MultilevelAnalysisResult,
  ConjointAnalysisRequest,
  ConjointAnalysisResult,
  ConjointSimulationRequest,
  ConjointSimulationResult,
  LCAAnalysisRequest,
  LCAAnalysisResult,
  DiDAnalysisRequest,
  DiDAnalysisResult,
  SEMAnalysisRequest,
  SEMAnalysisResult,
  CompetingRisksAnalysisRequest,
  CompetingRisksAnalysisResult,
  IRT4PLAnalysisRequest,
  IRT4PLAnalysisResult,
  IPWAnalysisRequest,
  IPWAnalysisResult,
  GAMSplineAnalysisRequest,
  GAMSplineAnalysisResult,
  QuantileRegressionRequest,
  QuantileRegressionResult,
  GTheoryAnalysisRequest,
  GTheoryAnalysisResult,
  RDDAnalysisRequest,
  RDDAnalysisResult,
  SyntheticControlAnalysisRequest,
  SyntheticControlAnalysisResult,
  SmallAreaEstimationRequest,
  SmallAreaEstimationResult,
  EventStudyAnalysisRequest,
  EventStudyAnalysisResult,
  BSTSCausalImpactRequest,
  BSTSCausalImpactResult,
  AIPWCATERequest,
  AIPWCATEResult,
  IV2SLSRequest,
  IV2SLSResult,
  BifactorAnalysisRequest,
  BifactorAnalysisResult,
  PanelVARRequest,
  PanelVARResult,
  LatentGrowthRequest,
  LatentGrowthResult,
  QTERequest,
  QTEResult,
  CausalDAGRequest,
  CausalDAGResult,
  MSMAnalysisRequest,
  MSMAnalysisResult,
  GEEAnalysisRequest,
  GEEAnalysisResult,
  RandomizationInferenceRequest,
  RandomizationInferenceResult,
  EVTAnalysisRequest,
  EVTAnalysisResult,
  JointModelAnalysisRequest,
  JointModelAnalysisResult,
  ConformalPredictionRequest,
  ConformalPredictionResult,
  MSEMAnalysisRequest,
  MSEMAnalysisResult,
  TMLEAnalysisRequest,
  TMLEAnalysisResult,
  SDIDAnalysisRequest,
  SDIDAnalysisResult,
  CausalForestAnalysisRequest,
  CausalForestAnalysisResult,
  CausalMediationSensitivityRequest,
  CausalMediationSensitivityResult,
  DTWClusteringRequest,
  DTWClusteringResult,
  CausalTreeAnalysisRequest,
  CausalTreeAnalysisResult,
  MultipleTestingFDRRequest,
  MultipleTestingFDRResult,
  BSEMRequest,
  BSEMResult,
  GaussianCopulaRequest,
  GaussianCopulaResult,
  DynamicFactorModelRequest,
  DynamicFactorModelResult,
  ExtremeBoundsRequest,
  ExtremeBoundsResult,
  SpatialEconometricsRequest,
  SpatialEconometricsResult,
  IVQuantileRegressionRequest,
  IVQuantileRegressionResult,
  ConjointHBRequest,
  ConjointHBResult,
  FractionalResponseRequest,
  FractionalResponseResult,
  MIRTRequest,
  MIRTResult,
  HeckmanSelectionRequest,
  HeckmanSelectionResult,
  StochasticFrontierRequest,
  StochasticFrontierResult,
  ZeroInflatedRequest,
  ZeroInflatedResult,
  LatentModerationRequest,
  LatentModerationResult,
  EndogenousSwitchingRequest,
  EndogenousSwitchingResult,
  GPSDoseResponseRequest,
  GPSDoseResponseResult,
  CausalDiscoveryRequest,
  CausalDiscoveryResult,
  BARTCausalRequest,
  BARTCausalResult,
  ConjointChoiceRequest,
  ConjointChoiceResult,
  MGSEMInvarianceRequest,
  MGSEMInvarianceResult,
  GAMSplineRequest,
  GAMSplineResult,
  LatentProfileRequest,
  LatentProfileResult,
  ShapleyDriverRequest,
  ShapleyDriverResult,
  PlackettLuceRequest,
  PlackettLuceResult,
  MaxDiffRequest,
  MaxDiffResult,
  BayesianNetworkRequest,
  BayesianNetworkResult,
  StochasticDominanceRequest,
  StochasticDominanceResult,
  ManskiBoundsRequest,
  ManskiBoundsResult,
  DynamicTreatmentRegimesRequest,
  DynamicTreatmentRegimesResult,
  FiniteMixtureRaschRequest,
  FiniteMixtureRaschResult,
  DoubleMachineLearningRequest,
  DoubleMachineLearningResult,
  RegressionKinkRequest,
  RegressionKinkResult,
  StaggeredDIDRequest,
  StaggeredDIDResult,
  MatrixCompletionCausalRequest,
  MatrixCompletionCausalResult,
  SDIDAdvancedRequest,
  SDIDAdvancedResult,
  InteractiveFixedEffectsRequest,
  InteractiveFixedEffectsResult,
  MultipleMediatorsRequest,
  MultipleMediatorsResult,
  PolicyLearningRequest,
  PolicyLearningResult,
  RDDLocalRandomizationRequest,
  RDDLocalRandomizationResult,
  DynamicPanelGMMRequest,
  DynamicPanelGMMResult,
  WeakIVRobustRequest,
  WeakIVRobustResult,
  SequentialMediationRequest,
  SequentialMediationResult,
  PostDoubleSelectionLassoRequest,
  PostDoubleSelectionLassoResult,
  LARFRequest,
  LARFResult,
  MTERequest,
  MTEResult,
  LeeBoundsRequest,
  LeeBoundsResult,
  SurrogateIndexRequest,
  SurrogateIndexResult,
  ConformalCounterfactualRequest,
  ConformalCounterfactualResult,
  CausalSensitivityRequest,
  CausalSensitivityResult,
  BCFRequest,
  BCFResult,
  ShiftShareIVRequest,
  ShiftShareIVResult,
  QuantileSyntheticControlRequest,
  QuantileSyntheticControlResult,
  TWFEDecompositionRequest,
  TWFEDecompositionResult,
  FactorIVRequest,
  FactorIVResult,
  NestedLogitRequest,
  NestedLogitResult,
  AutoDMLRieszRequest,
  AutoDMLRieszResult,
  LocalInstrumentalVariablesRequest,
  LocalInstrumentalVariablesResult,
  ConformalOptimalTransportRequest,
  ConformalOptimalTransportResult,
  DPMDeconvolutionRequest,
  DPMDeconvolutionResult,
  MultiCutoffRDRequest,
  MultiCutoffRDResult,
  HighDimensionalMediationRequest,
  HighDimensionalMediationResult,
  NetworkSpilloverRequest,
  NetworkSpilloverResult,
  DynamicSpatialPanelRequest,
  DynamicSpatialPanelResult,
  ContinuousPolicyShiftRequest,
  ContinuousPolicyShiftResult,
  GeneralizedSyntheticControlRequest,
  GeneralizedSyntheticControlResult
} from '../types/survey';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'Lỗi kết nối máy chủ.';
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        if (typeof errJson.detail === 'string') {
          errorDetail = errJson.detail;
        } else if (errJson.detail.validation_errors) {
          errorDetail = errJson.detail.validation_errors.join('; ');
        } else {
          errorDetail = JSON.stringify(errJson.detail);
        }
      }
    } catch {
      errorDetail = `Lỗi HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // --- Surveys Management ---
  async getSurveys(status?: string): Promise<SurveyListItem[]> {
    const url = status ? `${BASE_URL}/surveys?status=${encodeURIComponent(status)}` : `${BASE_URL}/surveys`;
    const res = await fetch(url);
    return handleResponse<SurveyListItem[]>(res);
  },

  async createSurvey(data: { title: string; description?: string; instructions?: string }): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return handleResponse<Survey>(res);
  },

  async getSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}`);
    return handleResponse<Survey>(res);
  },

  async updateSurvey(id: string, data: Partial<Survey>): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return handleResponse<Survey>(res);
  },

  async publishSurvey(id: string): Promise<{ id: string; status: string; public_slug: string; public_url: string }> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/publish`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async closeSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/close`, {
      method: 'POST'
    });
    return handleResponse<Survey>(res);
  },

  async reopenSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/reopen`, {
      method: 'POST'
    });
    return handleResponse<Survey>(res);
  },

  async duplicateSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/duplicate`, {
      method: 'POST'
    });
    return handleResponse<Survey>(res);
  },

  async deleteSurvey(id: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/surveys/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      throw new Error('Không thể xóa khảo sát.');
    }
  },

  // --- Survey Multilingual Translations ---
  async autoTranslateSurvey(surveyId: string, targetLang: string = 'en'): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/translations/auto-translate?target_lang=${encodeURIComponent(targetLang)}`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async getSurveyTranslations(surveyId: string): Promise<{ survey_id: string; available_languages: string[]; translations: Record<string, any> }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/translations`);
    return handleResponse(res);
  },

  async updateSurveyTranslation(surveyId: string, lang: string, payload: any): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/translations/${encodeURIComponent(lang)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- Public Survey ---
  async getPublicSurvey(slugOrId: string, lang?: string): Promise<Survey & { available_languages?: string[]; current_language?: string }> {
    const url = lang ? `${BASE_URL}/public/surveys/${encodeURIComponent(slugOrId)}?lang=${encodeURIComponent(lang)}` : `${BASE_URL}/public/surveys/${encodeURIComponent(slugOrId)}`;
    const res = await fetch(url);
    return handleResponse<Survey & { available_languages?: string[]; current_language?: string }>(res);
  },

  async submitPublicSurvey(slugOrId: string, payload: {
    started_at: string;
    submitted_at: string;
    client_metadata?: Record<string, any>;
    answers: Record<string, any>;
  }): Promise<{ response_id: string; message: string; risk_score?: number; risk_level?: string }> {
    const res = await fetch(`${BASE_URL}/public/surveys/${encodeURIComponent(slugOrId)}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async batchSyncPublicResponses(slugOrId: string, items: Array<{
    client_uuid?: string;
    started_at: string;
    submitted_at: string;
    client_metadata?: Record<string, any>;
    answers: Record<string, any>;
    source?: string;
    enumerator_id?: string;
  }>): Promise<{
    success: boolean;
    total_received: number;
    synced_count: number;
    duplicates_skipped: number;
    error_count: number;
    results: Array<{
      client_uuid?: string;
      response_id?: string;
      status: string;
      risk_score?: number;
      risk_level?: string;
      message?: string;
    }>;
  }> {
    const res = await fetch(`${BASE_URL}/public/surveys/${encodeURIComponent(slugOrId)}/batch-sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses: items })
    });
    return handleResponse(res);
  },

  // --- Responses & Review ---
  async getResponses(surveyId: string, riskLevel?: string, reviewStatus?: string): Promise<ResponseListItem[]> {
    const params = new URLSearchParams();
    if (riskLevel) params.append('risk_level', riskLevel);
    if (reviewStatus) params.append('review_status', reviewStatus);
    const url = `${BASE_URL}/surveys/${surveyId}/responses?${params.toString()}`;
    const res = await fetch(url);
    return handleResponse<ResponseListItem[]>(res);
  },

  async getResponseDetail(surveyId: string, responseId: string): Promise<ResponseDetail> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/${responseId}`);
    return handleResponse<ResponseDetail>(res);
  },

  async updateReviewDecision(surveyId: string, responseId: string, reviewStatus: string, reviewNotes?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/${responseId}/review`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_status: reviewStatus, review_notes: reviewNotes || '' })
    });
    return handleResponse(res);
  },

  async batchUpdateReviewDecision(surveyId: string, responseIds: string[], reviewStatus: string, reviewNotes?: string): Promise<{ message: string; updated_count: number; review_status: string }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/batch-review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        response_ids: responseIds,
        review_status: reviewStatus,
        review_notes: reviewNotes || ''
      })
    });
    return handleResponse(res);
  },

  async compareResponses(surveyId: string, resp1: string, resp2: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/compare/side-by-side?resp1=${encodeURIComponent(resp1)}&resp2=${encodeURIComponent(resp2)}`);
    return handleResponse(res);
  },

  async reanalyzeSurveyResponses(surveyId: string): Promise<{
    survey_id: string;
    total_reanalyzed: number;
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
    quality_sensitivity: string;
    message: string;
  }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/re-analyze`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  // --- Automated Data Cleansing & Exclusion Rules ---
  async previewDataCleansing(surveyId: string, criteria: Partial<CleansingCriteria>): Promise<CleansingReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/cleansing/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(criteria)
    });
    return handleResponse(res);
  },

  async applyDataCleansing(surveyId: string, criteria: Partial<CleansingCriteria>): Promise<{
    success: boolean;
    survey_id: string;
    applied_count: number;
    rejected_count: number;
    verified_clean_count: number;
    audit_log_id: string;
    timestamp: string;
  }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/cleansing/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(criteria)
    });
    return handleResponse(res);
  },

  // --- Automated Batch Anomaly Quarantine Pipeline ---
  async batchQuarantineAnomalies(
    surveyId: string,
    payload: BatchAnomalyQuarantineRequest = {}
  ): Promise<BatchAnomalyQuarantineResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/batch-quarantine-anomalies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async batchRestoreQuarantined(
    surveyId: string,
    payload: BatchRestoreQuarantineRequest = {}
  ): Promise<BatchRestoreQuarantineResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/batch-restore-quarantined`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- Cognitive Pre-Testing & Question Ambiguity Diagnostics ---
  async runSurveyCognitivePretest(surveyId: string): Promise<CognitivePretestReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/cognitive-pretest`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async runDraftCognitivePretest(payload: {
    survey_id?: string;
    title?: string;
    questions: any[];
  }): Promise<CognitivePretestReport> {
    const res = await fetch(`${BASE_URL}/ai/cognitive-pretest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- Survey Historical Versions ---
  async getSurveyVersions(surveyId: string): Promise<Array<{
    id: string;
    survey_id: string;
    version: number;
    title: string;
    description: string;
    questions_count: number;
    questions: any[];
    created_at: string;
  }>> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/versions`);
    return handleResponse(res);
  },

  async getSurveyVersionDetail(surveyId: string, versionNum: number): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/versions/${versionNum}`);
    return handleResponse(res);
  },

  // --- Analytics ---
  async getSurveyAnalytics(surveyId: string): Promise<SurveyAnalytics> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics`);
    return handleResponse<SurveyAnalytics>(res);
  },

  // --- AI Survey Engine ---
  async generateSurveyDraft(
    paramOrTopic: string | import('../types/survey').AIGenerateSurveyOptions,
    audience?: string,
    minutes: number = 5
  ): Promise<any> {
    const payload = typeof paramOrTopic === 'string'
      ? { topic: paramOrTopic, audience: audience || '', expected_time_minutes: minutes }
      : paramOrTopic;

    const res = await fetch(`${BASE_URL}/ai/generate-survey`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async auditQuestions(questions: Question[], surveyId: string = ''): Promise<import('../types/survey').AIAuditResponse> {
    const res = await fetch(`${BASE_URL}/ai/audit-questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questions, survey_id: surveyId })
    });
    return handleResponse<import('../types/survey').AIAuditResponse>(res);
  },

  async getAiStatus(): Promise<import('../types/survey').AIStatus> {
    const res = await fetch(`${BASE_URL}/ai/status`);
    return handleResponse<import('../types/survey').AIStatus>(res);
  },

  async analyzeQualitativeResponses(surveyId: string, questionId?: string): Promise<import('../types/survey').AIQualitativeAnalysis> {
    const res = await fetch(`${BASE_URL}/ai/analyze-responses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ survey_id: surveyId, question_id: questionId })
    });
    return handleResponse<import('../types/survey').AIQualitativeAnalysis>(res);
  },

  async getAiSessions(limit: number = 20): Promise<any[]> {
    const res = await fetch(`${BASE_URL}/ai/sessions?limit=${limit}`);
    return handleResponse<any[]>(res);
  },

  async getAiSessionDetail(sessionId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/ai/sessions/${sessionId}`);
    return handleResponse<any>(res);
  },

  // --- Paper Survey & OMR Scanning ---
  async getPaperTemplate(surveyId: string): Promise<{ template_id: string; survey_id: string; version: number; layout: any }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/paper/template`);
    return handleResponse(res);
  },

  async scanPaperImage(surveyId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/paper/scan`, {
      method: 'POST',
      body: formData
    });
    return handleResponse(res);
  },

  async batchScanPaperImages(surveyId: string, files: File[]): Promise<any> {
    const formData = new FormData();
    for (const f of files) {
      formData.append('files', f);
    }
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/paper/batch-scan`, {
      method: 'POST',
      body: formData
    });
    return handleResponse(res);
  },

  async ingestPaperResponse(surveyId: string, payload: {
    form_id: string;
    enumerator_id?: string;
    answers: Record<string, any>;
    omr_confidence?: number;
    scan_image_url?: string;
    manual_corrections?: any[];
  }): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/paper/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- Enumerator Analytics ---
  async getEnumeratorAnalytics(surveyId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/enumerators`);
    return handleResponse(res);
  },

  // --- Quality Audit Report & Compliance ---
  async getQualityAuditReport(surveyId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/audit-report`);
    return handleResponse(res);
  },

  async getAuditTrail(surveyId: string): Promise<import('../types/survey').AuditTrail> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/audit-trail`);
    return handleResponse<import('../types/survey').AuditTrail>(res);
  },

  async anonymizeSurveyResponses(surveyId: string, payload: {
    anonymize_client_metadata?: boolean;
    mask_text_answers?: boolean;
    operator_notes?: string;
  }): Promise<{ message: string; anonymized_responses_count: number; audit_log_id: string }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/privacy/anonymize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async simulateRedTeamAttack(surveyId: string): Promise<import('../types/survey').RedTeamSimulationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/audit/simulate-attack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    return handleResponse<import('../types/survey').RedTeamSimulationResult>(res);
  },

  // --- Public Certificate & Cryptographic Ledger Verification ---
  async verifyCertificate(identifier: string): Promise<import('../types/survey').PublicCertificateVerification> {
    const res = await fetch(`${BASE_URL}/public/verify/${encodeURIComponent(identifier)}`);
    return handleResponse<import('../types/survey').PublicCertificateVerification>(res);
  },



  // --- Statistical & Academic Tools (Benford & Codebook) ---
  async getBenfordAnalysis(surveyId: string, questionId?: string): Promise<any> {
    const query = questionId ? `?question_id=${encodeURIComponent(questionId)}` : '';
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/benford${query}`);
    return handleResponse(res);
  },

  async getQualitativeAnalysis(surveyId: string, questionId?: string): Promise<any> {
    const query = questionId ? `?question_id=${encodeURIComponent(questionId)}` : '';
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/qualitative${query}`);
    return handleResponse(res);
  },

  async getCrosstabAnalysis(surveyId: string, rowVar: string, colVar: string, scope: string = 'all'): Promise<any> {
    const params = new URLSearchParams({ row_var: rowVar, col_var: colVar, scope });
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/crosstab?${params.toString()}`);
    return handleResponse(res);
  },

  async getScaleReliability(surveyId: string, scope: string = 'all', questionIds?: string): Promise<any> {
    const params = new URLSearchParams({ scope });
    if (questionIds) params.append('question_ids', questionIds);
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/reliability?${params.toString()}`);
    return handleResponse(res);
  },

  async getSurveyCodebook(surveyId: string, format: 'json' | 'spss' | 'r' | 'stata' = 'json'): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/codebook?format=${format}`);
    if (format === 'spss' || format === 'r' || format === 'stata') {
      return res.text();
    }
    return handleResponse(res);
  },

  async testSurveyWebhook(surveyId: string, payload: {
    webhook_url: string;
    webhook_secret?: string;
  }): Promise<{
    success: boolean;
    status_code?: number;
    delivery_id: string;
    latency_ms: number;
    message: string;
    error?: string;
  }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/settings/test-webhook`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- System Diagnostics & Observability ---
  async getSystemDiagnostics(): Promise<any> {
    const res = await fetch(`${BASE_URL}/system/diagnostics`);
    return handleResponse(res);
  },

  async runWalCheckpoint(): Promise<any> {
    const res = await fetch(`${BASE_URL}/system/maintenance/wal-checkpoint`, { method: 'POST' });
    return handleResponse(res);
  },

  async runVacuum(): Promise<any> {
    const res = await fetch(`${BASE_URL}/system/maintenance/vacuum`, { method: 'POST' });
    return handleResponse(res);
  },

  // --- Demo Dataset Seeder ---
  async seedAcademicDemo(): Promise<{
    survey_id: string;
    public_slug: string;
    title: string;
    total_responses: number;
    clean_count: number;
    flagged_count: number;
    data_trust_index: number;
    cronbach_alpha?: number;
    message: string;
  }> {
    const res = await fetch(`${BASE_URL}/surveys/seed-academic-demo`, { method: 'POST' });
    return handleResponse(res);
  },

  async seedSurveyResponses(surveyId: string, count: number = 15): Promise<{
    survey_id: string;
    seeded_count: number;
    message: string;
  }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/seed-demo-responses?count=${count}`, { method: 'POST' });
    return handleResponse(res);
  },

  // --- Longitudinal Wave Comparison & Cohen's d ---
  async getLongitudinalAnalysis(surveyId: string, compareSurveyId: string, scope: string = 'verified_clean'): Promise<import('../types/survey').LongitudinalWaveComparisonResult> {
    const params = new URLSearchParams({ compare_survey_id: compareSurveyId, scope });
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/longitudinal?${params.toString()}`);
    return handleResponse<import('../types/survey').LongitudinalWaveComparisonResult>(res);
  },

  // --- Concurrency Stress Test Profiler ---
  async runStressTest(totalRequests: number = 30, concurrency: number = 6): Promise<import('../types/survey').StressTestReport> {
    const params = new URLSearchParams({ total_requests: totalRequests.toString(), concurrency: concurrency.toString() });
    const res = await fetch(`${BASE_URL}/system/maintenance/stress-test?${params.toString()}`, { method: 'POST' });
    return handleResponse<import('../types/survey').StressTestReport>(res);
  },

  // --- Sampling Quotas & Demographic Raking ---
  async getSurveyQuotas(surveyId: string): Promise<import('../types/survey').SamplingQuotaReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/quotas`);
    return handleResponse<import('../types/survey').SamplingQuotaReport>(res);
  },

  async updateSurveyQuotas(surveyId: string, quotaRules: import('../types/survey').SamplingQuotaRule[]): Promise<{ status: string; message: string }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/quotas`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quota_rules: quotaRules })
    });
    return handleResponse<{ status: string; message: string }>(res);
  },

  async runDemographicRaking(surveyId: string, payload: import('../types/survey').DemographicRakingRequest): Promise<import('../types/survey').DemographicRakingResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/raking`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<import('../types/survey').DemographicRakingResult>(res);
  },

  async downloadRakedCsv(surveyId: string, payload: import('../types/survey').DemographicRakingRequest): Promise<void> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/raking/export-csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      throw new Error(`Lỗi tải tệp CSV: ${res.statusText}`);
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `datatrust_raked_weighted_${surveyId.slice(0, 8)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },

  // --- Differential Item Functioning (DIF) Analysis ---
  async getDIFAnalysis(
    surveyId: string,
    groupingQuestionId: string,
    refGroup: string,
    focalGroup: string,
    scope: string = 'verified_clean',
    strataCount: number = 4
  ): Promise<import('../types/survey').DIFReport> {
    const params = new URLSearchParams({
      grouping_question_id: groupingQuestionId,
      reference_group: refGroup,
      focal_group: focalGroup,
      scope,
      strata_count: strataCount.toString()
    });
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/dif?${params.toString()}`);
    return handleResponse<import('../types/survey').DIFReport>(res);
  },

  // --- Cognitive Burden & Inattention Pacing ---
  async getCognitivePacingAnalytics(surveyId: string): Promise<import('../types/survey').SurveyPacingReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/cognitive-pacing`);
    return handleResponse<import('../types/survey').SurveyPacingReport>(res);
  },

  // --- Multivariate Outliers & Mahalanobis Distance ---
  async getMultivariateOutliers(
    surveyId: string,
    scope: 'all' | 'verified_clean' = 'all',
    questionIds?: string
  ): Promise<import('../types/survey').MultivariateOutlierReport> {
    const params = new URLSearchParams({ scope });
    if (questionIds) {
      params.append('question_ids', questionIds);
    }
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/multivariate-outliers?${params.toString()}`);
    return handleResponse<import('../types/survey').MultivariateOutlierReport>(res);
  },

  // --- Exploratory Factor Analysis (EFA) & Scree Plot ---
  async getExploratoryFactorAnalysis(
    surveyId: string,
    scope: 'all' | 'verified_clean' = 'all',
    rotation: 'varimax' | 'none' = 'varimax',
    minEigenvalue: number = 1.0,
    forcedFactors?: number,
    questionIds?: string
  ): Promise<import('../types/survey').EFAReport> {
    const params = new URLSearchParams({
      scope,
      rotation,
      min_eigenvalue: minEigenvalue.toString()
    });
    if (forcedFactors) {
      params.append('forced_factors', forcedFactors.toString());
    }
    if (questionIds) {
      params.append('question_ids', questionIds);
    }
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/efa?${params.toString()}`);
    return handleResponse<import('../types/survey').EFAReport>(res);
  },

  // --- Hypothesis Testing T-Test Engine ---
  async runIndependentTTest(
    surveyId: string,
    payload: {
      grouping_question_id: string;
      group1_value: string;
      group2_value: string;
      target_question_id: string;
      scope?: 'all' | 'verified_clean';
    }
  ): Promise<import('../types/survey').IndependentTTestReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/ttest/independent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<import('../types/survey').IndependentTTestReport>(res);
  },

  async runPairedTTest(
    surveyId: string,
    payload: {
      pre_question_id: string;
      post_question_id: string;
      scope?: 'all' | 'verified_clean';
    }
  ): Promise<import('../types/survey').PairedTTestReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/ttest/paired`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<import('../types/survey').PairedTTestReport>(res);
  },

  // --- One-Way ANOVA & Tukey HSD Engine ---
  async runOneWayANOVA(
    surveyId: string,
    payload: {
      grouping_question_id: string;
      target_question_id: string;
      scope?: 'all' | 'verified_clean';
    }
  ): Promise<import('../types/survey').OneWayANOVAReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/anova`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<import('../types/survey').OneWayANOVAReport>(res);
  },

  // --- Bivariate Correlation Analysis Suite ---
  async getCorrelationMatrix(
    surveyId: string,
    options?: {
      method?: 'pearson' | 'spearman';
      scope?: 'all' | 'verified_clean';
      questionIds?: string;
    }
  ): Promise<import('../types/survey').CorrelationMatrixReport> {
    const params = new URLSearchParams();
    if (options?.method) params.append('method', options.method);
    if (options?.scope) params.append('scope', options.scope);
    if (options?.questionIds) params.append('question_ids', options.questionIds);
    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/correlation${queryStr}`);
    return handleResponse<import('../types/survey').CorrelationMatrixReport>(res);
  },

  // --- Multiple Linear Regression OLS Engine ---
  async runLinearRegression(
    surveyId: string,
    payload: {
      dependent_question_id: string;
      predictor_question_ids: string[];
      scope?: 'all' | 'verified_clean';
    }
  ): Promise<import('../types/survey').LinearRegressionReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/regression`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<import('../types/survey').LinearRegressionReport>(res);
  },

  // --- Academic Research Manuscript Export ---
  async getManuscript(
    surveyId: string,
    format: 'html' | 'markdown' | 'latex' = 'markdown',
    scope: 'all' | 'verified_clean' = 'verified_clean'
  ): Promise<string> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/export/manuscript?format=${format}&scope=${scope}`);
    if (!res.ok) {
      throw new Error(`Lỗi tải bản thảo (${res.status}): ${res.statusText}`);
    }
    return res.text();
  },

  // --- Survey Logic & Branching DAG Simulation ---
  async validateSurveyLogic(surveyId: string): Promise<import('../types/survey').SurveyLogicReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/logic/validate`);
    return handleResponse<import('../types/survey').SurveyLogicReport>(res);
  },

  async simulateSurveyLogic(surveyId: string, answers: Record<string, any>): Promise<import('../types/survey').SurveySimulationReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/logic/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers })
    });
    return handleResponse<import('../types/survey').SurveySimulationReport>(res);
  },

  // --- Statistical Power Analysis & Sample Size Estimator ---
  async runPowerAnalysis(
    surveyId: string,
    payload: {
      analysis_type?: 'sample_adequacy' | 'cochran' | 'ttest' | 'correlation';
      confidence_level?: number;
      margin_of_error?: number;
      population_size?: number | null;
      effect_size?: number;
      target_power?: number;
      alpha?: number;
      scope?: 'all' | 'verified_clean';
    }
  ): Promise<import('../types/survey').PowerAnalysisReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/power-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<import('../types/survey').PowerAnalysisReport>(res);
  },

  // --- Split-Ballot & Question Wording Experimentation ---
  async getSplitBallotAnalysis(
    surveyId: string,
    questionId: string,
    scope: 'all' | 'verified_clean' = 'verified_clean'
  ): Promise<import('../types/survey').SplitBallotReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/split-ballot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_id: questionId, scope })
    });
    return handleResponse<import('../types/survey').SplitBallotReport>(res);
  },

  // --- Rasch Model & Item Response Theory (IRT) ---
  async getRaschAnalysis(
    surveyId: string,
    scope: 'all' | 'verified_clean' = 'verified_clean'
  ): Promise<import('../types/survey').RaschModelReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/rasch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scope })
    });
    return handleResponse<import('../types/survey').RaschModelReport>(res);
  },

  // --- Respondent Clustering & Typology Segmentation ---
  async getClusterAnalysis(
    surveyId: string,
    k?: number,
    scope: 'all' | 'verified_clean' = 'verified_clean',
    questionIds?: string[]
  ): Promise<import('../types/survey').ClusterAnalysisReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/clusters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ k, scope, question_ids: questionIds })
    });
    return handleResponse<import('../types/survey').ClusterAnalysisReport>(res);
  },

  // --- Pairwise Response Similarity & Collusion Ring Matrix ---
  async getPairwiseSimilarityAnalysis(
    surveyId: string,
    params?: { threshold?: number; max_matrix_size?: number; scope?: 'all' | 'verified_clean' }
  ): Promise<import('../types/survey').PairwiseSimilarityAnalysisReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/pairwise-similarity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        threshold: params?.threshold ?? 0.80,
        max_matrix_size: params?.max_matrix_size ?? 60,
        scope: params?.scope ?? 'all'
      })
    });
    return handleResponse<import('../types/survey').PairwiseSimilarityAnalysisReport>(res);
  },

  // --- Geographic Spatial Clustering & Geo-Fencing Compliance ---
  async getSpatialAnalysis(
    surveyId: string,
    params?: {
      eps_meters?: number;
      min_samples?: number;
      max_speed_kmh?: number;
      geofence_polygon?: [number, number][];
      scope?: 'all' | 'verified_clean';
    }
  ): Promise<import('../types/survey').SpatialAnalysisReport> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/spatial`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        eps_meters: params?.eps_meters ?? 75.0,
        min_samples: params?.min_samples ?? 3,
        max_speed_kmh: params?.max_speed_kmh ?? 120.0,
        geofence_polygon: params?.geofence_polygon,
        scope: params?.scope ?? 'all'
      })
    });
    return handleResponse<import('../types/survey').SpatialAnalysisReport>(res);
  },

  // --- Statistical Mediation & Path Analysis ---
  async runMediationAnalysis(
    surveyId: string,
    payload: MediationAnalysisRequest
  ): Promise<MediationAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/mediation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MediationAnalysisResult>(res);
  },

  // --- Non-Parametric Hypothesis Testing ---
  async runMannWhitneyU(
    surveyId: string,
    payload: MannWhitneyURequest
  ): Promise<MannWhitneyUResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/mann-whitney-u`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MannWhitneyUResult>(res);
  },

  async runWilcoxonSignedRank(
    surveyId: string,
    payload: WilcoxonSignedRankRequest
  ): Promise<WilcoxonSignedRankResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/wilcoxon-signed-rank`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<WilcoxonSignedRankResult>(res);
  },

  async runKruskalWallis(
    surveyId: string,
    payload: KruskalWallisRequest
  ): Promise<KruskalWallisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/kruskal-wallis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<KruskalWallisResult>(res);
  },

  // --- Missing Data Pattern Diagnostics & Imputation ---
  async getMissingDataDiagnostics(
    surveyId: string,
    params?: { question_ids?: string[]; scope?: string }
  ): Promise<MissingDataDiagnosticsResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/missing-data-diagnostics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params || {})
    });
    return handleResponse<MissingDataDiagnosticsResult>(res);
  },

  async runMissingDataImputation(
    surveyId: string,
    params?: { question_ids?: string[]; method?: string; scope?: string }
  ): Promise<MissingDataImputationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/missing-data-imputation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params || {})
    });
    return handleResponse<MissingDataImputationResult>(res);
  },

  // --- Scale Equating & Concordance Transformation ---
  async runScaleEquating(
    surveyId: string,
    payload: { source_question_id: string; target_question_id: string; scope?: string }
  ): Promise<ScaleEquatingResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/scale-equating`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ScaleEquatingResult>(res);
  },

  // --- Multi-Group Measurement Invariance Testing ---
  async runMeasurementInvariance(
    surveyId: string,
    payload: { grouping_question_id: string; scale_question_ids: string[]; scope?: string }
  ): Promise<MeasurementInvarianceResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/measurement-invariance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MeasurementInvarianceResult>(res);
  },

  // --- Common Method Bias / Variance (CMB/CMV) Diagnostics ---
  async runCommonMethodBias(
    surveyId: string,
    payload?: { scale_question_ids?: string[]; marker_question_id?: string; scope?: string }
  ): Promise<CommonMethodBiasResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/common-method-bias`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {})
    });
    return handleResponse<CommonMethodBiasResult>(res);
  },

  // --- Statistical Moderation (PROCESS Model 1) ---
  async runModerationAnalysis(
    surveyId: string,
    payload: {
      independent_question_id: string;
      moderator_question_id: string;
      dependent_question_id: string;
      center_variables?: boolean;
      scope?: string;
    }
  ): Promise<ModerationAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/moderation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ModerationAnalysisResult>(res);
  },

  // --- Moderated Mediation (PROCESS Model 7) ---
  async runModeratedMediation(
    surveyId: string,
    payload: ModeratedMediationRequest
  ): Promise<ModeratedMediationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/moderated-mediation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ModeratedMediationResult>(res);
  },

  // --- Complex Survey Sampling (Two-Stage Cluster & Taylor Linearization) ---
  async runComplexSamplingAnalysis(
    surveyId: string,
    payload: ComplexSamplingRequest
  ): Promise<ComplexSamplingResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/complex-sampling`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ComplexSamplingResult>(res);
  },

  // --- Propensity Score Matching (PSM) & Inverse Probability Weighting (IPW) ---
  async runPropensityMatching(
    surveyId: string,
    payload: PSMAnalysisRequest
  ): Promise<PSMAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/propensity-matching`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<PSMAnalysisResult>(res);
  },

  // --- Structural Topic Modeling (STM) & Latent Dirichlet Allocation (LDA) ---
  async runTopicModeling(
    surveyId: string,
    payload: TopicModelAnalysisRequest
  ): Promise<TopicModelAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/topic-modeling`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<TopicModelAnalysisResult>(res);
  },

  // --- Psychometric Network Analysis (Gaussian Graphical Model) ---
  async runPsychometricNetwork(
    surveyId: string,
    payload: PsychometricNetworkRequest
  ): Promise<PsychometricNetworkResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/psychometric-network`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<PsychometricNetworkResult>(res);
  },

  // --- Item Response Theory (IRT) 2-Parameter Logistic (2PL) ---
  async runIRT2PLAnalysis(
    surveyId: string,
    payload: IRT2PLAnalysisRequest
  ): Promise<IRT2PLAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/irt-2pl`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<IRT2PLAnalysisResult>(res);
  },

  // --- Survival Analysis & Time-to-Drop-off (Kaplan-Meier & Cox HR) ---
  async runSurvivalDropOffAnalysis(
    surveyId: string,
    payload: SurvivalAnalysisRequest
  ): Promise<SurvivalAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/survival-dropoff`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SurvivalAnalysisResult>(res);
  },

  // --- Multilevel Modeling / Hierarchical Linear Models (HLM / MLM) ---
  async runMultilevelAnalysis(
    surveyId: string,
    payload: MultilevelAnalysisRequest
  ): Promise<MultilevelAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/multilevel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MultilevelAnalysisResult>(res);
  },

  // --- Choice-Based Conjoint (CBC / DCE) & Market Simulator ---
  async runConjointAnalysis(
    surveyId: string,
    payload: ConjointAnalysisRequest
  ): Promise<ConjointAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/conjoint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ConjointAnalysisResult>(res);
  },

  async runConjointSimulation(
    surveyId: string,
    payload: ConjointSimulationRequest
  ): Promise<ConjointSimulationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/conjoint-simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ConjointSimulationResult>(res);
  },

  // --- Latent Class Analysis (LCA) & Finite Mixture Modeling ---
  async runLCAAnalysis(
    surveyId: string,
    payload: LCAAnalysisRequest
  ): Promise<LCAAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/lca`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<LCAAnalysisResult>(res);
  },

  // --- Difference-in-Differences (DiD) & Policy Impact Evaluation ---
  async runDiDAnalysis(
    surveyId: string,
    payload: DiDAnalysisRequest
  ): Promise<DiDAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/did`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DiDAnalysisResult>(res);
  },

  // --- Structural Equation Modeling (SEM) & Path Analysis ---
  async runSEMAnalysis(
    surveyId: string,
    payload: SEMAnalysisRequest
  ): Promise<SEMAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/sem`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SEMAnalysisResult>(res);
  },

  // --- Competing Risks & Shared Frailty Survival Analysis ---
  async runCompetingRisksAnalysis(
    surveyId: string,
    payload: CompetingRisksAnalysisRequest
  ): Promise<CompetingRisksAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/competing-risks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<CompetingRisksAnalysisResult>(res);
  },

  // --- Item Response Theory (IRT) 3PL & 4PL Models ---
  async runIRT4PLAnalysis(
    surveyId: string,
    payload: IRT4PLAnalysisRequest
  ): Promise<IRT4PLAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/irt-4pl`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<IRT4PLAnalysisResult>(res);
  },

  // --- Propensity Score Weighting (IPW) & Doubly Robust Estimation ---
  async runIPWAnalysis(
    surveyId: string,
    payload: IPWAnalysisRequest
  ): Promise<IPWAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/ipw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<IPWAnalysisResult>(res);
  },

  // --- Generalized Additive Models (GAM) & Spline Regression ---
  async runGAMSplineAnalysis(
    surveyId: string,
    payload: GAMSplineAnalysisRequest
  ): Promise<GAMSplineAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/gam`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<GAMSplineAnalysisResult>(res);
  },

  // --- Quantile Regression & Conditional Distributional Effects ---
  async runQuantileRegressionAnalysis(
    surveyId: string,
    payload: QuantileRegressionRequest
  ): Promise<QuantileRegressionResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/quantile-regression`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<QuantileRegressionResult>(res);
  },

  // --- Generalizability Theory (G-Theory & D-Study) ---
  async runGTheoryAnalysis(
    surveyId: string,
    payload: GTheoryAnalysisRequest
  ): Promise<GTheoryAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/g-theory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<GTheoryAnalysisResult>(res);
  },

  // --- Regression Discontinuity Design (Sharp RDD) ---
  async runRDDAnalysis(
    surveyId: string,
    payload: RDDAnalysisRequest
  ): Promise<RDDAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/rdd`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<RDDAnalysisResult>(res);
  },

  // --- Synthetic Control Method (SCM) ---
  async runSyntheticControlAnalysis(
    surveyId: string,
    payload: SyntheticControlAnalysisRequest
  ): Promise<SyntheticControlAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/synthetic-control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SyntheticControlAnalysisResult>(res);
  },

  // --- Small Area Estimation (SAE & Fay-Herriot Empirical Bayes) ---
  async runSmallAreaEstimation(
    surveyId: string,
    payload: SmallAreaEstimationRequest
  ): Promise<SmallAreaEstimationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/small-area-estimation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SmallAreaEstimationResult>(res);
  },

  // --- Dynamic Event-Study & Staggered DiD ---
  async runEventStudyAnalysis(
    surveyId: string,
    payload: EventStudyAnalysisRequest
  ): Promise<EventStudyAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/event-study`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<EventStudyAnalysisResult>(res);
  },

  // --- Bayesian Structural Time Series (BSTS) & Causal Impact ---
  async runBSTSCausalImpact(
    surveyId: string,
    payload: BSTSCausalImpactRequest
  ): Promise<BSTSCausalImpactResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/bsts-causal-impact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<BSTSCausalImpactResult>(res);
  },

  // --- Doubly Robust AIPW & Heterogeneous CATE ---
  async runAIPWCATEAnalysis(
    surveyId: string,
    payload: AIPWCATERequest
  ): Promise<AIPWCATEResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/aipw-cate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<AIPWCATEResult>(res);
  },

  // --- Instrumental Variables Two-Stage Least Squares (2SLS) ---
  async runIV2SLSAnalysis(
    surveyId: string,
    payload: IV2SLSRequest
  ): Promise<IV2SLSResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/iv-2sls`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<IV2SLSResult>(res);
  },

  // --- Bifactor Psychometric Modeling & Omega Hierarchical ---
  async runBifactorAnalysis(
    surveyId: string,
    payload: BifactorAnalysisRequest
  ): Promise<BifactorAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/bifactor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<BifactorAnalysisResult>(res);
  },

  // --- Panel Vector Autoregression (Panel VAR) & Granger Causality ---
  async runPanelVARAnalysis(
    surveyId: string,
    payload: PanelVARRequest
  ): Promise<PanelVARResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/panel-var`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<PanelVARResult>(res);
  },

  // --- Latent Growth Curve Modeling (LGCM) ---
  async runLatentGrowthAnalysis(
    surveyId: string,
    payload: LatentGrowthRequest
  ): Promise<LatentGrowthResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/latent-growth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<LatentGrowthResult>(res);
  },

  // --- Quantile Treatment Effects (QTE) & Distributional Treatment Effects ---
  async runQTEAnalysis(
    surveyId: string,
    payload: QTERequest
  ): Promise<QTEResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/qte`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<QTEResult>(res);
  },

  // --- Causal DAG & Structure Learning (PC Algorithm) ---
  async runCausalDAGAnalysis(
    surveyId: string,
    payload: CausalDAGRequest
  ): Promise<CausalDAGResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/causal-dag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<CausalDAGResult>(res);
  },

  // --- Marginal Structural Models (MSM) with Stabilized IPTW ---
  async runMSMAnalysis(
    surveyId: string,
    payload: MSMAnalysisRequest
  ): Promise<MSMAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/msm-iptw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MSMAnalysisResult>(res);
  },

  // --- Generalized Estimating Equations (GEE) ---
  async runGEEAnalysis(
    surveyId: string,
    payload: GEEAnalysisRequest
  ): Promise<GEEAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/gee`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<GEEAnalysisResult>(res);
  },

  // --- Exact Permutation & Randomization Inference (Fisher Sharp Null) ---
  async runRandomizationInference(
    surveyId: string,
    payload: RandomizationInferenceRequest
  ): Promise<RandomizationInferenceResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/randomization-inference`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<RandomizationInferenceResult>(res);
  },

  // --- Extreme Value Theory (EVT) & Survey Tail Risk ---
  async runEVTAnalysis(
    surveyId: string,
    payload: EVTAnalysisRequest
  ): Promise<EVTAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/extreme-value`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<EVTAnalysisResult>(res);
  },

  // --- Joint Modeling of Longitudinal & Survival Data ---
  async runJointModelAnalysis(
    surveyId: string,
    payload: JointModelAnalysisRequest
  ): Promise<JointModelAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/joint-model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<JointModelAnalysisResult>(res);
  },

  // --- Conformal Prediction & Distribution-Free Risk Intervals ---
  async runConformalPrediction(
    surveyId: string,
    payload: ConformalPredictionRequest
  ): Promise<ConformalPredictionResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/conformal-prediction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ConformalPredictionResult>(res);
  },

  // --- Multilevel Structural Equation Modeling (MSEM) ---
  async runMSEMAnalysis(
    surveyId: string,
    payload: MSEMAnalysisRequest
  ): Promise<MSEMAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/msem`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MSEMAnalysisResult>(res);
  },

  // --- Targeted Maximum Likelihood Estimation (TMLE) ---
  async runTMLEAnalysis(
    surveyId: string,
    payload: TMLEAnalysisRequest
  ): Promise<TMLEAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/tmle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<TMLEAnalysisResult>(res);
  },

  // --- Synthetic Difference-in-Differences (SDID) ---
  async runSDIDAnalysis(
    surveyId: string,
    payload: SDIDAnalysisRequest
  ): Promise<SDIDAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/sdid`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SDIDAnalysisResult>(res);
  },

  // --- Generalized Causal Forest (GRF; Athey, Tibshirani & Wager 2019) ---
  async runCausalForestAnalysis(
    surveyId: string,
    payload: CausalForestAnalysisRequest
  ): Promise<CausalForestAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/causal-forest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<CausalForestAnalysisResult>(res);
  },
  // --- Causal Mediation Sensitivity Analysis (Imai, Keele & Tingley 2010) ---
  async runCausalMediationSensitivity(
    surveyId: string,
    payload: CausalMediationSensitivityRequest
  ): Promise<CausalMediationSensitivityResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/causal-mediation-sensitivity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<CausalMediationSensitivityResult>(res);
  },
  // --- Dynamic Time Warping (DTW) Trajectory Clustering ---
  async runDTWClustering(
    surveyId: string,
    payload: DTWClusteringRequest
  ): Promise<DTWClusteringResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/dtw-clustering`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DTWClusteringResult>(res);
  },
  // --- Causal Interaction Trees & Honest Subgroup Identification (Athey & Imbens 2016) ---
  async runCausalTreeAnalysis(
    surveyId: string,
    payload: CausalTreeAnalysisRequest
  ): Promise<CausalTreeAnalysisResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/causal-tree`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<CausalTreeAnalysisResult>(res);
  },
  // --- Multiple Testing Correction & False Discovery Rate (FDR) (Benjamini & Hochberg 1995, Storey 2002) ---
  async runMultipleTestingFDR(
    surveyId: string,
    payload: MultipleTestingFDRRequest
  ): Promise<MultipleTestingFDRResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/multiple-testing-fdr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MultipleTestingFDRResult>(res);
  },
  // --- Bayesian Structural Equation Modeling (BSEM) (Muthén & Asparouhov 2012) ---
  async runBSEMAnalysis(
    surveyId: string,
    payload: BSEMRequest
  ): Promise<BSEMResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/bsem`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<BSEMResult>(res);
  },
  // --- Gaussian Copula Endogeneity Estimation (Park & Gupta 2012) ---
  async runGaussianCopulaAnalysis(
    surveyId: string,
    payload: GaussianCopulaRequest
  ): Promise<GaussianCopulaResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/gaussian-copula`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<GaussianCopulaResult>(res);
  },
  // --- Dynamic Factor Modeling (DFM) (Stock & Watson 2002) ---
  async runDynamicFactorAnalysis(
    surveyId: string,
    payload: DynamicFactorModelRequest
  ): Promise<DynamicFactorModelResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/dynamic-factor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DynamicFactorModelResult>(res);
  },

  // --- Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997) ---
  async runExtremeBoundsAnalysis(
    surveyId: string,
    payload: ExtremeBoundsRequest
  ): Promise<ExtremeBoundsResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/extreme-bounds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ExtremeBoundsResult>(res);
  },

  // --- Spatial Econometrics & Moran's I Models (Anselin 1988, LeSage & Pace 2009) ---
  async runSpatialEconometricsAnalysis(
    surveyId: string,
    payload: SpatialEconometricsRequest
  ): Promise<SpatialEconometricsResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/spatial-econometrics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SpatialEconometricsResult>(res);
  },

  // --- Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005) ---
  async runIVQuantileRegressionAnalysis(
    surveyId: string,
    payload: IVQuantileRegressionRequest
  ): Promise<IVQuantileRegressionResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/iv-quantile-regression`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<IVQuantileRegressionResult>(res);
  },

  // --- Choice-Based Conjoint with Hierarchical Bayes (HB-CBC) ---
  async runConjointHBAnalysis(
    surveyId: string,
    payload: ConjointHBRequest
  ): Promise<ConjointHBResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/conjoint-hb`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ConjointHBResult>(res);
  },

  // --- Fractional Response QMLE Regression (Papke & Wooldridge 1996, 2008) ---
  async runFractionalResponse(
    surveyId: string,
    payload: FractionalResponseRequest
  ): Promise<FractionalResponseResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/fractional-response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<FractionalResponseResult>(res);
  },

  // --- Multidimensional Item Response Theory (MIRT; Reckase 2009) ---
  async runMIRTAnalysis(
    surveyId: string,
    payload: MIRTRequest
  ): Promise<MIRTResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/mirt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MIRTResult>(res);
  },

  // --- Heckman Two-Step Sample Selection Model (Heckman 1979) ---
  async runHeckmanSelection(
    surveyId: string,
    payload: HeckmanSelectionRequest
  ): Promise<HeckmanSelectionResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/heckman-selection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<HeckmanSelectionResult>(res);
  },

  // --- Stochastic Frontier Analysis (SFA; Aigner et al. 1977; JLMS 1982) ---
  async runStochasticFrontier(
    surveyId: string,
    payload: StochasticFrontierRequest
  ): Promise<StochasticFrontierResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/stochastic-frontier`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<StochasticFrontierResult>(res);
  },

  // --- Zero-Inflated Count Models (ZIP & ZINB; Lambert 1992, Greene 1994, Vuong 1989) ---
  async runZeroInflatedAnalysis(
    surveyId: string,
    payload: ZeroInflatedRequest
  ): Promise<ZeroInflatedResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/zero-inflated`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ZeroInflatedResult>(res);
  },

  // --- Latent Moderated Structural Equations (LMS / QML; Klein & Moosbrugger 2000) ---
  async runLatentModeration(
    surveyId: string,
    payload: LatentModerationRequest
  ): Promise<LatentModerationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/latent-moderation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<LatentModerationResult>(res);
  },

  // --- Endogenous Switching Regression (ESR; Maddala 1983, Lokshin & Sajaia 2004) ---
  async runEndogenousSwitching(
    surveyId: string,
    payload: EndogenousSwitchingRequest
  ): Promise<EndogenousSwitchingResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/endogenous-switching`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<EndogenousSwitchingResult>(res);
  },

  // --- Generalized Propensity Score (GPS) Dose-Response (Hirano & Imbens 2004) ---
  async runGPSDoseResponse(
    surveyId: string,
    payload: GPSDoseResponseRequest
  ): Promise<GPSDoseResponseResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/gps-dose-response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<GPSDoseResponseResult>(res);
  },

  // --- Causal Discovery DAG (LiNGAM & ANM - Shimizu et al. 2006; Hoyer et al. 2009) ---
  async runCausalDiscovery(
    surveyId: string,
    payload: CausalDiscoveryRequest
  ): Promise<CausalDiscoveryResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/causal-discovery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<CausalDiscoveryResult>(res);
  },

  // --- Bayesian Additive Regression Trees (BART) Causal (Chipman et al. 2010; Hill 2011) ---
  async runBARTCausal(
    surveyId: string,
    payload: BARTCausalRequest
  ): Promise<BARTCausalResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/bart-causal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<BARTCausalResult>(res);
  },

  // --- Conjoint Analysis & Discrete Choice Experiment (DCE - McFadden 1974; Train 2009) ---
  async runConjointChoice(
    surveyId: string,
    payload: ConjointChoiceRequest
  ): Promise<ConjointChoiceResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/conjoint-choice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ConjointChoiceResult>(res);
  },

  // --- Multi-Group SEM Invariance & Latent Means (Meredith 1993; Byrne 2013) ---
  async runMGSEMInvariance(
    surveyId: string,
    payload: MGSEMInvarianceRequest
  ): Promise<MGSEMInvarianceResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/mgsem-invariance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MGSEMInvarianceResult>(res);
  },

  // --- Generalized Additive Models (GAM) & Penalized Splines (Hastie & Tibshirani 1990; Wood 2017) ---
  async runGAMSpline(
    surveyId: string,
    payload: GAMSplineRequest
  ): Promise<GAMSplineResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/gam-spline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<GAMSplineResult>(res);
  },

  // --- Latent Profile Analysis (LPA) & Gaussian Mixture Models (McLachlan & Peel 2000; Collins & Lanza 2010) ---
  async runLatentProfile(
    surveyId: string,
    payload: LatentProfileRequest
  ): Promise<LatentProfileResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/latent-profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<LatentProfileResult>(res);
  },

  // --- Shapley Value Regression & Key Driver Analysis (Lipovetsky & Conklin 2001; Lundberg & Lee 2017) ---
  async runShapleyDrivers(
    surveyId: string,
    payload: ShapleyDriverRequest
  ): Promise<ShapleyDriverResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/shapley-drivers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ShapleyDriverResult>(res);
  },

  // --- Plackett-Luce Choice Model & Rank-Ordered Logit (Luce 1959; Hunter 2004 MM) ---
  async runPlackettLuce(
    surveyId: string,
    payload: PlackettLuceRequest
  ): Promise<PlackettLuceResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/plackett-luce`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<PlackettLuceResult>(res);
  },

  // --- MaxDiff Best-Worst Scaling (Finn & Louviere 1992; Marley & Louviere 2005) ---
  async runMaxDiff(
    surveyId: string,
    payload: MaxDiffRequest
  ): Promise<MaxDiffResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/maxdiff`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MaxDiffResult>(res);
  },

  // --- Gaussian Bayesian Network DAG Structure Learning (Heckerman 1995; Scutari 2010) ---
  async runBayesianNetwork(
    surveyId: string,
    payload: BayesianNetworkRequest
  ): Promise<BayesianNetworkResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/bayesian-network`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<BayesianNetworkResult>(res);
  },

  // --- Stochastic Dominance & Distributional Inequality (Davidson & Duclos 2000) ---
  async runStochasticDominance(
    surveyId: string,
    payload: StochasticDominanceRequest
  ): Promise<StochasticDominanceResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/stochastic-dominance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<StochasticDominanceResult>(res);
  },

  // --- Manski Non-Parametric Partial Identification & Worst-Case Bounds (Manski 1990, 2000; Imbens & Manski 2004) ---
  async runManskiBounds(
    surveyId: string,
    payload: ManskiBoundsRequest
  ): Promise<ManskiBoundsResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/manski-bounds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ManskiBoundsResult>(res);
  },

  // --- Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine (Murphy 2003, Robins 2004) ---
  async runDynamicTreatmentRegimes(
    surveyId: string,
    payload: DynamicTreatmentRegimesRequest
  ): Promise<DynamicTreatmentRegimesResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/dynamic-treatment-regimes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DynamicTreatmentRegimesResult>(res);
  },

  // --- Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine (Rost 1990; von Davier & Rost 2007) ---
  async runFiniteMixtureRasch(
    surveyId: string,
    payload: FiniteMixtureRaschRequest
  ): Promise<FiniteMixtureRaschResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/finite-mixture-rasch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<FiniteMixtureRaschResult>(res);
  },

  // --- Double / Debiased Machine Learning (DML) for Causal Inference (Chernozhukov et al. 2018) ---
  async runDoubleMachineLearning(
    surveyId: string,
    payload: DoubleMachineLearningRequest
  ): Promise<DoubleMachineLearningResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/double-machine-learning`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DoubleMachineLearningResult>(res);
  },

  // --- Regression Kink Design (Card, Lee, Pei, & Weber 2015; Dong 2018) ---
  async runRegressionKink(
    surveyId: string,
    payload: RegressionKinkRequest
  ): Promise<RegressionKinkResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/regression-kink`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<RegressionKinkResult>(res);
  },

  // --- Staggered Difference-in-Differences (Callaway & Sant'Anna 2021; Goodman-Bacon 2021) ---
  async runStaggeredDID(
    surveyId: string,
    payload: StaggeredDIDRequest
  ): Promise<StaggeredDIDResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/staggered-did`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<StaggeredDIDResult>(res);
  },

  // --- Matrix Completion for Causal Panel Data (Athey et al. 2021) ---
  async runMatrixCompletionCausal(
    surveyId: string,
    payload: MatrixCompletionCausalRequest
  ): Promise<MatrixCompletionCausalResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/matrix-completion-causal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MatrixCompletionCausalResult>(res);
  },

  // --- Synthetic Difference-in-Differences Advanced (Arkhangelsky et al. 2021) ---
  async runSDIDAdvanced(
    surveyId: string,
    payload: SDIDAdvancedRequest
  ): Promise<SDIDAdvancedResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/sdid-advanced`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SDIDAdvancedResult>(res);
  },

  // --- Interactive Fixed Effects (Bai 2009; Gobillon & Magnac 2016) ---
  async runInteractiveFixedEffects(
    surveyId: string,
    payload: InteractiveFixedEffectsRequest
  ): Promise<InteractiveFixedEffectsResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/interactive-fixed-effects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<InteractiveFixedEffectsResult>(res);
  },

  // --- Multiple Sequential Mediators (VanderWeele 2014) ---
  async runMultipleMediators(
    surveyId: string,
    payload: MultipleMediatorsRequest
  ): Promise<MultipleMediatorsResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/multiple-mediators`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MultipleMediatorsResult>(res);
  },

  // --- Doubly Robust Policy Learning (Athey & Wager 2021) ---
  async runPolicyLearning(
    surveyId: string,
    payload: PolicyLearningRequest
  ): Promise<PolicyLearningResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/policy-learning`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<PolicyLearningResult>(res);
  },

  // --- RDD with Local Randomization (Cattaneo et al. 2015) ---
  async runRDDLocalRandomization(
    surveyId: string,
    payload: RDDLocalRandomizationRequest
  ): Promise<RDDLocalRandomizationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/rdd-local-randomization`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<RDDLocalRandomizationResult>(res);
  },

  // --- Dynamic Panel System & Difference GMM (Arellano-Bond 1991, Blundell-Bond 1998, Windmeijer 2005) ---
  async runDynamicPanelGMM(
    surveyId: string,
    payload: DynamicPanelGMMRequest
  ): Promise<DynamicPanelGMMResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/dynamic-panel-gmm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DynamicPanelGMMResult>(res);
  },

  // --- Weak-Instrument Robust Inference (Anderson-Rubin 1949, Moreira 2003 CLR, Montiel Olea & Pflueger 2013) ---
  async runWeakIVRobust(
    surveyId: string,
    payload: WeakIVRobustRequest
  ): Promise<WeakIVRobustResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/weak-iv-robust`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<WeakIVRobustResult>(res);
  },

  // --- Sequential Causal Mediation Analysis (Hayes Model 6 / Imai & Yamamoto 2013) ---
  async runSequentialMediation(
    surveyId: string,
    payload: SequentialMediationRequest
  ): Promise<SequentialMediationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/sequential-mediation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SequentialMediationResult>(res);
  },

  // --- High-Dimensional Post-Double-Selection (PDS) Lasso (Belloni, Chernozhukov, & Hansen 2014) ---
  async runPostDoubleSelectionLasso(
    surveyId: string,
    payload: PostDoubleSelectionLassoRequest
  ): Promise<PostDoubleSelectionLassoResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/post-double-selection-lasso`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<PostDoubleSelectionLassoResult>(res);
  },

  async runLARF(
    surveyId: string,
    payload: LARFRequest
  ): Promise<LARFResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/larf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<LARFResult>(res);
  },

  async runMTE(
    surveyId: string,
    payload: MTERequest
  ): Promise<MTEResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/mte`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MTEResult>(res);
  },

  async runLeeBounds(
    surveyId: string,
    payload: LeeBoundsRequest
  ): Promise<LeeBoundsResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/lee-bounds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<LeeBoundsResult>(res);
  },

  async runSurrogateIndex(
    surveyId: string,
    payload: SurrogateIndexRequest
  ): Promise<SurrogateIndexResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/surrogate-index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<SurrogateIndexResult>(res);
  },

  async runConformalCounterfactual(
    surveyId: string,
    payload: ConformalCounterfactualRequest
  ): Promise<ConformalCounterfactualResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/conformal-counterfactual`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ConformalCounterfactualResult>(res);
  },

  async runCausalSensitivityBias(
    surveyId: string,
    payload: CausalSensitivityRequest
  ): Promise<CausalSensitivityResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/causal-sensitivity-bias`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<CausalSensitivityResult>(res);
  },

  async runBCF(
    surveyId: string,
    payload: BCFRequest
  ): Promise<BCFResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/bcf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<BCFResult>(res);
  },

  async runShiftShareIV(
    surveyId: string,
    payload: ShiftShareIVRequest
  ): Promise<ShiftShareIVResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/shift-share-iv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ShiftShareIVResult>(res);
  },
  async runQuantileSyntheticControl(
    surveyId: string,
    payload: QuantileSyntheticControlRequest
  ): Promise<QuantileSyntheticControlResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/quantile-synthetic-control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<QuantileSyntheticControlResult>(res);
  },
  async runTWFEDecomposition(
    surveyId: string,
    payload: TWFEDecompositionRequest
  ): Promise<TWFEDecompositionResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/twfe-decomposition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<TWFEDecompositionResult>(res);
  },
  async runFactorIV(
    surveyId: string,
    payload: FactorIVRequest
  ): Promise<FactorIVResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/factor-iv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<FactorIVResult>(res);
  },
  async runNestedLogit(
    surveyId: string,
    payload: NestedLogitRequest
  ): Promise<NestedLogitResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/nested-logit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<NestedLogitResult>(res);
  },
  async runAutoDMLRiesz(
    surveyId: string,
    payload: AutoDMLRieszRequest
  ): Promise<AutoDMLRieszResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/auto-dml-riesz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<AutoDMLRieszResult>(res);
  },
  async runLocalInstrumentalVariables(
    surveyId: string,
    payload: LocalInstrumentalVariablesRequest
  ): Promise<LocalInstrumentalVariablesResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/local-instrumental-variables`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<LocalInstrumentalVariablesResult>(res);
  },
  async runConformalOptimalTransport(
    surveyId: string,
    payload: ConformalOptimalTransportRequest
  ): Promise<ConformalOptimalTransportResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/conformal-optimal-transport`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ConformalOptimalTransportResult>(res);
  },
  async runDPMDeconvolution(
    surveyId: string,
    payload: DPMDeconvolutionRequest
  ): Promise<DPMDeconvolutionResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/dpm-deconvolution`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DPMDeconvolutionResult>(res);
  },
  async runMultiCutoffRD(
    surveyId: string,
    payload: MultiCutoffRDRequest
  ): Promise<MultiCutoffRDResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/multi-cutoff-rd`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<MultiCutoffRDResult>(res);
  },
  async runHighDimensionalMediation(
    surveyId: string,
    payload: HighDimensionalMediationRequest
  ): Promise<HighDimensionalMediationResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/high-dimensional-mediation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<HighDimensionalMediationResult>(res);
  },
  async runNetworkSpillover(
    surveyId: string,
    payload: NetworkSpilloverRequest
  ): Promise<NetworkSpilloverResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/network-spillover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<NetworkSpilloverResult>(res);
  },
  async runDynamicSpatialPanel(
    surveyId: string,
    payload: DynamicSpatialPanelRequest
  ): Promise<DynamicSpatialPanelResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/dynamic-spatial-panel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<DynamicSpatialPanelResult>(res);
  },
  async runContinuousPolicyShift(
    surveyId: string,
    payload: ContinuousPolicyShiftRequest
  ): Promise<ContinuousPolicyShiftResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/continuous-policy-shift`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<ContinuousPolicyShiftResult>(res);
  },
  async runGeneralizedSyntheticControl(
    surveyId: string,
    payload: GeneralizedSyntheticControlRequest
  ): Promise<GeneralizedSyntheticControlResult> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/generalized-synthetic-control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<GeneralizedSyntheticControlResult>(res);
  }
};
