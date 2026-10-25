import pandas as pd
from app.engine.conformal_optimal_transport_engine import estimate_conformal_optimal_transport
from app.engine.local_instrumental_variables_engine import estimate_local_instrumental_variables
from app.engine.auto_dml_riesz_engine import estimate_auto_dml_riesz
from app.engine.nested_logit_engine import estimate_nested_logit
from app.engine.factor_iv_engine import estimate_factor_iv
from app.engine.twfe_decomposition_engine import estimate_twfe_decomposition
from app.engine.quantile_synthetic_control_engine import estimate_quantile_synthetic_control
from app.engine.shift_share_iv_engine import estimate_shift_share_iv
from app.engine.bcf_engine import estimate_bayesian_causal_forest
from app.engine.causal_sensitivity_bias_engine import estimate_causal_sensitivity_bias
from app.engine.conformal_counterfactual_engine import estimate_conformal_counterfactuals
from app.engine.surrogate_index_engine import estimate_surrogate_index
from app.engine.lee_bounds_engine import estimate_lee_bounds
from app.engine.mte_engine import estimate_mte
from app.engine.larf_engine import estimate_larf
from app.engine.post_double_selection_lasso_engine import PostDoubleSelectionLassoEngine
from app.engine.sequential_mediation_engine import SequentialMediationEngine
from app.engine.weak_iv_robust_engine import WeakIVRobustEngine
from app.engine.dynamic_panel_gmm_engine import DynamicPanelGMMEngine
from app.engine.extreme_bounds_engine import ExtremeBoundsEngine
from app.engine.bsem_engine import compute_bsem_analysis
from app.engine.dynamic_factor_model_engine import compute_dynamic_factor_analysis
from app.engine.causal_mediation_sensitivity_engine import run_causal_mediation_sensitivity
from app.engine.causal_tree_engine import run_causal_interaction_tree
from app.engine.dtw_clustering_engine import run_dtw_trajectory_clustering
from app.engine.gaussian_copula_engine import run_gaussian_copula_estimation
from app.engine.multiple_testing_fdr_engine import compute_fdr_corrections, run_pairwise_fdr_matrix
from app.engine.rdd_local_randomization_engine import RDDLocalRandomizationEngine
from app.engine.policy_learning_engine import PolicyLearningEngine
from app.engine.multiple_mediators_engine import MultipleMediatorsEngine
from app.engine.interactive_fixed_effects_engine import compute_interactive_fixed_effects
from app.engine.sdid_advanced_engine import SDIDAdvancedEngine
from app.engine.matrix_completion_causal_engine import MatrixCompletionCausalEngine
from app.engine.staggered_did_engine import StaggeredDIDEngine
from app.engine.regression_kink_engine import RegressionKinkEngine
from app.engine.double_machine_learning_engine import DoubleMachineLearningEngine
from app.engine.finite_mixture_rasch_engine import FiniteMixtureRaschEngine
from app.engine.dynamic_treatment_regimes_engine import DynamicTreatmentRegimesEngine
from app.engine.manski_bounds_engine import ManskiBoundsEngine
from app.engine.stochastic_dominance_engine import StochasticDominanceEngine
from app.engine.zero_inflated_engine import ZeroInflatedEngine
from app.engine.tmle_engine import TMLEEngine
from app.engine.stochastic_frontier_engine import StochasticFrontierEngine
from app.engine.spatial_econometrics_engine import SpatialEconometricsEngine
from app.engine.shapley_driver_engine import ShapleyDriverEngine
from app.engine.sdid_engine import SDIDEngine
from app.engine.quota_engine import RakingEngine
from app.engine.plackett_luce_engine import PlackettLuceEngine
from app.engine.msem_engine import MSEMEngine
from app.engine.mirt_engine import MultidimensionalIRTEngine
from app.engine.mgsem_invariance_engine import MGSEMInvarianceEngine
from app.engine.maxdiff_engine import MaxDiffEngine
from app.engine.latent_profile_engine import LatentProfileEngine
from app.engine.latent_moderation_engine import LatentModerationEngine
from app.engine.joint_modeling_engine import JointModelingEngine
from app.engine.iv_quantile_regression_engine import IVQuantileRegressionEngine
from app.engine.heckman_selection_engine import HeckmanSelectionEngine
from app.engine.gps_dose_response_engine import GPSDoseResponseEngine
from app.engine.fractional_response_engine import FractionalResponseEngine
from app.engine.endogenous_switching_engine import EndogenousSwitchingEngine
from app.engine.conjoint_hb_engine import ConjointHBEngine
from app.engine.conjoint_choice_engine import ConjointChoiceEngine
from app.engine.conformal_prediction_engine import ConformalPredictionEngine
from app.engine.causal_forest_engine import CausalForestEngine
from app.engine.causal_discovery_engine import CausalDiscoveryEngine
from app.engine.bayesian_network_engine import BayesianNetworkEngine
from app.engine.bart_causal_engine import BARTCausalEngine
import json
import numpy as np
import statistics
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from app.database import get_db, record_audit_log
from app.schemas import (
    DoubleMachineLearningRequest,
    RegressionKinkRequest,
    StaggeredDIDRequest,
    MatrixCompletionCausalRequest,
    SDIDAdvancedRequest,
    SDIDAdvancedOut,
    InteractiveFixedEffectsRequest,
    InteractiveFixedEffectsOut,
    MultipleMediatorsRequest,
    MultipleMediatorsOut,
    PolicyLearningRequest,
    PolicyLearningOut,
    RDDLocalRandomizationRequest,
    RDDLocalRandomizationOut,
    DynamicPanelGMMRequest,
    DynamicPanelGMMOut,
    WeakIVRobustRequest,
    WeakIVRobustOut,
    SequentialMediationRequest,
    SequentialMediationOut,
    PostDoubleSelectionLassoRequest,
    PostDoubleSelectionLassoOut,
    LARFRequest,
    LARFOut,
    MTERequest,
    MTEOut,
    LeeBoundsRequest,
    LeeBoundsOut,
    SurrogateIndexRequest,
    SurrogateIndexOut,
    ConformalCounterfactualRequest,
    ConformalCounterfactualOut,
    CausalSensitivityBiasRequest,
    CausalSensitivityBiasOut,
    BCFRequest,
    BCFOut,
    ShiftShareIVRequest,
    ShiftShareIVOut,
    QuantileSyntheticControlRequest,
    QuantileSyntheticControlOut,
    TWFEDecompositionRequest,
    TWFEDecompositionOut,
    FactorIVRequest,
    FactorIVOut,
    NestedLogitRequest,
    NestedLogitOut,
    AutoDMLRieszRequest,
    AutoDMLRieszOut,
    LocalInstrumentalVariablesRequest,
    LocalInstrumentalVariablesOut,
    ConformalOptimalTransportRequest,
    ConformalOptimalTransportOut,
    MatrixCompletionCausalOut,
    StaggeredDIDOut,
    RegressionKinkOut,
    DoubleMachineLearningOut,
    FiniteMixtureRaschRequest,
    FiniteMixtureRaschOut,
    DynamicTreatmentRegimesRequest,
    DynamicTreatmentRegimesOut,
    ManskiBoundsRequest,
    ManskiBoundsOut,
    StochasticDominanceRequest,
    StochasticDominanceOut,
    QuestionOption,
    LogicRule,
    QuestionBase,
    SurveyCreate,
    SurveyUpdate,
    SurveyOut,
    SurveyListItemOut,
    SurveyPublishOut,
    WebhookTestRequest,
    WebhookTestResponse,
    PublicQuestionOut,
    PublicSurveyOut,
    ResponseSubmit,
    QualityFlag,
    QualityAssessmentOut,
    ResponseListItemOut,
    ResponseDetailOut,
    ReviewStatusUpdate,
    BatchReviewRequest,
    PaperBubbleConfig,
    PaperQuestionLayout,
    PaperTemplateLayout,
    PaperScanResult,
    PaperIngestPayload,
    EnumeratorMetrics,
    EnumeratorAnalyticsOut,
    QuestionStats,
    SurveyAnalyticsOut,
    QualityAuditReportOut,
    AnonymizeRequest,
    AnonymizeResponse,
    AuditLogEntryOut,
    AuditTrailOut,
    GenerateSurveyAdvancedRequest,
    QuestionDraftSchema,
    SurveyDraftOutputSchema,
    ValidationReportSchema,
    AIGenerationResponseSchema,
    QualitativeAnalysisRequest,
    QualitativeTheme,
    QualitativeAnalysisResponse,
    BatchResponseItem,
    BatchResponseSubmit,
    BatchSyncResultItem,
    BatchSyncResponseOut,
    DataCleansingCriteria,
    DataCleansingReport,
    DataCleansingApplyResult,
    BatchAnomalyQuarantineRequest,
    BatchAnomalyQuarantineItem,
    BatchAnomalyQuarantineResult,
    BatchRestoreQuarantineRequest,
    BatchRestoreQuarantineResult,
    SurveyVersionOut,
    AttackDefenseItem,
    RedTeamSimulationResult,
    PublicCertificateVerificationOut,
    LongitudinalItemComparison,
    LongitudinalWaveComparisonOut,
    StressTestReportOut,
    SamplingQuotaRule,
    SamplingQuotaCellProgress,
    SamplingQuotaReportOut,
    SaveQuotasRequest,
    DemographicRakingRequest,
    RakingMarginalCategory,
    RakingMarginalComparison,
    DemographicRakingOut,
    DIFItemResult,
    DIFReportOut,
    IndependentTTestRequest,
    PairedTTestRequest,
    OneWayANOVARequest,
    LinearRegressionRequest,
    PowerAnalysisRequest,
    SplitBallotAnalysisRequest,
    RaschAnalysisRequest,
    ClusterAnalysisRequest,
    PairwiseSimilarityRequest,
    SpatialAnalysisRequest,
    CognitiveIssue,
    PersonaSimulationResult,
    CognitivePretestRequest,
    CognitivePretestReport,
    MediationAnalysisRequest,
    MediationPathInfo,
    MediationStep,
    MediationEffectsSummary,
    MediationSignificanceTests,
    MediationConclusion,
    MediationDiagram,
    MediationAnalysisOut,
    MannWhitneyURequest,
    MannWhitneyUOut,
    WilcoxonSignedRankRequest,
    WilcoxonSignedRankOut,
    KruskalWallisRequest,
    KruskalWallisOut,
    MissingDataDiagnosticsRequest,
    MissingDataDiagnosticsOut,
    MissingDataImputationRequest,
    MissingDataImputationOut,
    ScaleEquatingRequest,
    ScaleEquatingOut,
    MeasurementInvarianceRequest,
    MeasurementInvarianceOut,
    CommonMethodBiasRequest,
    CommonMethodBiasOut,
    ModerationAnalysisRequest,
    ModerationAnalysisOut,
    ModeratedMediationRequest,
    ModeratedMediationOut,
    ComplexSamplingRequest,
    ComplexSamplingOut,
    PSMAnalysisRequest,
    PSMAnalysisOut,
    TopicModelAnalysisRequest,
    TopicModelAnalysisOut,
    PsychometricNetworkRequest,
    PsychometricNetworkOut,
    IRT2PLAnalysisRequest,
    IRT2PLAnalysisOut,
    SurvivalAnalysisRequest,
    SurvivalAnalysisOut,
    MultilevelAnalysisRequest,
    MultilevelAnalysisOut,
    ConjointAnalysisRequest,
    ConjointSimulationRequest,
    ConjointAnalysisOut,
    ConjointSimulationOut,
    LCAAnalysisRequest,
    LCAAnalysisOut,
    DiDAnalysisRequest,
    DiDAnalysisOut,
    SEMPathSpec,
    SEMAnalysisRequest,
    SEMAnalysisOut,
    CompetingRisksAnalysisRequest,
    CompetingRisksAnalysisOut,
    IRT4PLAnalysisRequest,
    IRT4PLAnalysisOut,
    IPWAnalysisRequest,
    IPWAnalysisOut,
    GAMSplineAnalysisRequest,
    GAMSplineAnalysisOut,
    SmallAreaEstimationRequest,
    SmallAreaEstimationOut,
    QuantileRegressionRequest,
    QuantileRegressionOut,
    GTheoryAnalysisRequest,
    GTheoryAnalysisOut,
    RDDAnalysisRequest,
    RDDAnalysisOut,
    SyntheticControlAnalysisRequest,
    SyntheticControlAnalysisOut,
    SmallAreaEstimationRequest,
    SmallAreaEstimationOut,
    EventStudyAnalysisRequest,
    EventStudyAnalysisOut,
    BSTSCausalImpactRequest,
    BSTSCausalImpactOut,
    AIPWCATERequest,
    AIPWCATEOut,
    IV2SLSRequest,
    IV2SLSOut,
    BifactorSubscaleMapping,
    BifactorAnalysisRequest,
    BifactorAnalysisOut,
    PanelVARRequest,
    PanelVAROut,
    LatentGrowthRequest,
    LatentGrowthOut,
    QTERequest,
    QTEOut,
    CausalDAGRequest,
    CausalDAGOut,
    MSMAnalysisRequest,
    MSMAnalysisOut,
    GEEAnalysisRequest,
    GEEAnalysisOut,
    RandomizationInferenceRequest,
    RandomizationInferenceOut,
    EVTAnalysisRequest,
    EVTAnalysisOut,
    MSEMAnalysisRequest,
    MSEMAnalysisOut,
    TMLEAnalysisRequest,
    TMLEAnalysisOut,
    SDIDAnalysisRequest,
    SDIDAnalysisOut,
    CausalForestAnalysisRequest,
    CausalForestAnalysisOut,
    BSEMRequest,
    BSEMOut,
    GaussianCopulaRequest,
    GaussianCopulaOut,
    DynamicFactorModelRequest,
    DynamicFactorModelOut,
    ExtremeBoundsAnalysisRequest,
    ExtremeBoundsAnalysisOut,
    SpatialEconometricsRequest,
    SpatialEconometricsOut,
    IVQuantileRegressionRequest,
    IVQuantileRegressionOut,
    ConjointHBAnalysisRequest,
    ConjointHBAnalysisOut,
    FractionalResponseRequest,
    FractionalResponseOut,
    MIRTAnalysisRequest,
    MIRTAnalysisOut,
    HeckmanSelectionRequest,
    HeckmanSelectionOut,
    ZeroInflatedRequest,
    ZeroInflatedOut,
    LatentModerationRequest,
    LatentModerationOut,
    EndogenousSwitchingRequest,
    EndogenousSwitchingOut,
    GPSDoseResponseRequest,
    GPSDoseResponseOut,
    CausalDiscoveryRequest,
    CausalDiscoveryOut,
    BARTCausalRequest,
    BARTCausalOut,
    ConjointChoiceRequest,
    ConjointChoiceOut,
    MGSEMInvarianceRequest,
    MGSEMInvarianceOut,
    GAMSplineRequest,
    GAMSplineOut,
    LatentProfileRequest,
    LatentProfileOut,
    ShapleyDriverRequest,
    ShapleyDriverOut,
    PlackettLuceRequest,
    PlackettLuceOut,
    MaxDiffRequest,
    MaxDiffOut,
    BayesianNetworkRequest,
    BayesianNetworkOut,
    ExtremeBoundsAnalysisRequest,
    ExtremeBoundsAnalysisOut,
    SpatialEconometricsRequest,
    SpatialEconometricsOut,
    IVQuantileRegressionRequest,
    IVQuantileRegressionOut,
    ExtremeBoundsAnalysisRequest,
    ExtremeBoundsAnalysisOut,
    SpatialEconometricsRequest,
    SpatialEconometricsOut,
    IVQuantileRegressionRequest,
    IVQuantileRegressionOut,
    ExtremeBoundsAnalysisRequest,
    ExtremeBoundsAnalysisOut,
    SpatialEconometricsRequest,
    SpatialEconometricsOut,
    IVQuantileRegressionRequest,
    IVQuantileRegressionOut,
    JointModelAnalysisRequest,
    JointModelAnalysisOut,
    JointModelAnalysisOut,
    ConformalPredictionAnalysisRequest,
    ConformalPredictionAnalysisOut,
    CausalForestAnalysisOut,
    CausalMediationSensitivityRequest,
    CausalMediationSensitivityOut,
    CausalMediationSensitivityOut,
    DTWClusteringRequest,
    DTWClusteringOut,
    DTWClusteringOut,
    CausalTreeSubgroupRequest,
    CausalTreeSubgroupOut,
    CausalTreeSubgroupOut,
    MultipleTestingFDRRequest,
    MultipleTestingFDROut,
    HeckmanSelectionOut,
    StochasticFrontierRequest,
    StochasticFrontierOut
)


from app.engine.quality_engine import QualityEngine
from app.engine.qualitative_engine import QualitativeEngine
from app.engine.quota_engine import QuotaEngine, RakingEngine
from app.engine.dif_engine import DIFEngine
from app.engine.pacing_engine import CognitivePacingEngine
from app.engine.mahalanobis_engine import MahalanobisEngine
from app.engine.efa_engine import EFAEngine
from app.engine.ttest_engine import TTestEngine
from app.engine.anova_engine import ANOVAEngine
from app.engine.correlation_engine import CorrelationEngine
from app.engine.regression_engine import RegressionEngine
from app.engine.power_engine import PowerAnalysisEngine
from app.engine.split_ballot_engine import SplitBallotEngine
from app.engine.rasch_engine import RaschEngine
from app.engine.cluster_engine import ClusterEngine
from app.engine.similarity_engine import SimilarityEngine
from app.engine.spatial_engine import SpatialEngine
from app.engine.mediation_engine import MediationEngine
from app.engine.non_parametric_engine import NonParametricEngine
from app.engine.missing_data_engine import MissingDataEngine
from app.engine.equating_engine import EquatingEngine
from app.engine.invariance_engine import MeasurementInvarianceEngine
from app.engine.cmb_engine import CMBEngine
from app.engine.moderation_engine import ModerationEngine
from app.engine.moderated_mediation_engine import ModeratedMediationEngine
from app.engine.complex_sampling_engine import ComplexSamplingEngine
from app.engine.psm_engine import PSMEngine
from app.engine.topic_model_engine import TopicModelingEngine
from app.engine.network_engine import PsychometricNetworkEngine
from app.engine.irt_2pl_engine import IRT2PLEngine
from app.engine.survival_engine import SurvivalDropOffEngine
from app.engine.multilevel_engine import MultilevelModelingEngine
from app.engine.conjoint_engine import ConjointAnalysisEngine
from app.engine.lca_engine import LatentClassAnalysisEngine
from app.engine.did_engine import DifferenceInDifferencesEngine
from app.engine.sem_engine import SEMEngine
from app.engine.competing_risks_frailty_engine import CompetingRisksFrailtyEngine
from app.engine.irt_4pl_engine import IRT4PLEngine
from app.engine.ipw_doubly_robust_engine import IPWDoublyRobustEngine
from app.engine.gam_spline_engine import GAMSplineEngine
from app.engine.quantile_regression_engine import QuantileRegressionEngine
from app.engine.g_theory_engine import GTheoryEngine
from app.engine.rdd_engine import RDDEngine
from app.engine.synthetic_control_engine import SyntheticControlEngine
from app.engine.small_area_estimation_engine import SmallAreaEstimationEngine
from app.engine.event_study_engine import DynamicEventStudyEngine
from app.engine.bsts_causal_impact_engine import BSTSCausalImpactEngine
from app.engine.aipw_cate_engine import AIPWCATEEngine
from app.engine.iv_2sls_engine import IV2SLSEngine
from app.engine.bifactor_engine import BifactorEngine
from app.engine.panel_var_engine import PanelVAREngine
from app.engine.latent_growth_engine import LatentGrowthEngine
from app.engine.qte_engine import QTEEngine
from app.engine.causal_dag_engine import CausalDAGEngine
from app.engine.msm_iptw_engine import MSMIPTWEngine
from app.engine.gee_engine import GEEEngine
from app.engine.randomization_inference_engine import RandomizationInferenceEngine
from app.engine.extreme_value_engine import ExtremeValueEngine

router = APIRouter(prefix="/api/surveys/{survey_id}/analytics", tags=["Analytics"])


@router.get("", response_model=SurveyAnalyticsOut)
def get_survey_analytics(survey_id: str):
    """Tính toán thống kê thực từ cơ sở dữ liệu cho cuộc khảo sát"""
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT * FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        total_responses = len(resp_rows)
        is_sufficient = total_responses >= 5
        notice = None if is_sufficient else f"Cỡ mẫu hiện tại (N = {total_responses}) chưa đạt ngưỡng tối thiểu N >= 5 để đảm bảo độ tin cậy thống kê tổng thể."

        avg_dur = 0.0
        risk_dist = {"low": 0, "medium": 0, "high": 0}
        review_dist = {"unverified": 0, "under_review": 0, "verified_valid": 0, "verified_fraud": 0, "inconclusive": 0}

        if total_responses > 0:
            durations = [r["duration_seconds"] for r in resp_rows if r["duration_seconds"] > 0]
            avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0

            for r in resp_rows:
                lvl = r["risk_level"] or "low"
                risk_dist[lvl] = risk_dist.get(lvl, 0) + 1
                
                rev = r["review_status"] or "unverified"
                review_dist[rev] = review_dist.get(rev, 0) + 1

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        # Tối ưu hóa: Tải trước toàn bộ câu trả lời của khảo sát vào bộ nhớ trong 1 câu truy vấn (Tránh N+1)
        all_ans_rows = conn.execute("""
            SELECT ra.question_id, ra.answer_value 
            FROM response_answers ra
            JOIN responses r ON r.id = ra.response_id
            WHERE r.survey_id = ?
        """, (survey_id,)).fetchall()
        answers_by_qid = {}
        for a in all_ans_rows:
            answers_by_qid.setdefault(a["question_id"], []).append(a)

        questions_analytics = []
        funnel_analytics = []
        prev_ans_count = total_responses if total_responses > 0 else None

        for idx, q in enumerate(q_rows):
            qid = q["id"]
            q_type = q["question_type"]
            options = json.loads(q["options_json"] or "[]")
            
            # Lấy câu trả lời từ dict trong bộ nhớ (O(1) lookup)
            ans_rows = answers_by_qid.get(qid, [])

            total_ans = len(ans_rows)
            opt_dist = None
            stats_sum = None
            text_samples = None

            # Tính completion rate & drop-off rate
            comp_rate = round((total_ans / total_responses) * 100, 1) if total_responses > 0 else 0.0
            drop_off = round(((prev_ans_count - total_ans) / max(1, prev_ans_count)) * 100, 1) if (prev_ans_count is not None and prev_ans_count > total_ans) else 0.0
            prev_ans_count = total_ans

            funnel_analytics.append({
                "step": idx + 1,
                "question_id": qid,
                "question_title": q["title"],
                "question_type": q_type,
                "total_answers": total_ans,
                "completion_rate_pct": comp_rate,
                "drop_off_pct": drop_off
            })

            if q_type in ("single_choice", "dropdown", "likert"):
                id_to_label = {opt.get("id"): opt.get("label") for opt in options if isinstance(opt, dict)}
                counts = {opt.get("label", opt.get("id")): 0 for opt in options if isinstance(opt, dict)}
                
                for a in ans_rows:
                    raw = a["answer_value"]
                    val = id_to_label.get(raw, raw)
                    counts[val] = counts.get(val, 0) + 1
                opt_dist = counts

            elif q_type == "multiple_choice":
                id_to_label = {opt.get("id"): opt.get("label") for opt in options if isinstance(opt, dict)}
                counts = {opt.get("label", opt.get("id")): 0 for opt in options if isinstance(opt, dict)}
                
                for a in ans_rows:
                    raw = a["answer_value"]
                    try:
                        selected = json.loads(raw)
                        if isinstance(selected, list):
                            for s in selected:
                                label = id_to_label.get(s, s)
                                counts[label] = counts.get(label, 0) + 1
                        else:
                            label = id_to_label.get(raw, raw)
                            counts[label] = counts.get(label, 0) + 1
                    except Exception:
                        label = id_to_label.get(raw, raw)
                        counts[label] = counts.get(label, 0) + 1
                opt_dist = counts

            elif q_type in ("linear_scale", "number"):
                nums = []
                for a in ans_rows:
                    try:
                        nums.append(float(a["answer_value"]))
                    except Exception:
                        pass
                if nums:
                    stats_sum = {
                        "min": min(nums),
                        "max": max(nums),
                        "avg": round(sum(nums) / len(nums), 2),
                        "count": len(nums)
                    }
                    num_counts = {}
                    for n in nums:
                        k = str(int(n) if n.is_integer() else n)
                        num_counts[k] = num_counts.get(k, 0) + 1
                    opt_dist = num_counts

            elif q_type == "matrix":
                matrix_rows = options.get("rows", []) if isinstance(options, dict) else []
                matrix_cols = options.get("columns", []) if isinstance(options, dict) else []
                row_map = {
                    (r.get("id") if isinstance(r, dict) else str(r)): (r.get("label") if isinstance(r, dict) else str(r))
                    for r in matrix_rows
                }
                col_map = {
                    (c.get("id") if isinstance(c, dict) else str(c)): (c.get("label") if isinstance(c, dict) else str(c))
                    for c in matrix_cols
                }
                
                counts = {r_lbl: {c_lbl: 0 for c_lbl in col_map.values()} for r_lbl in row_map.values()}
                
                for a in ans_rows:
                    try:
                        m_ans = json.loads(a["answer_value"])
                        if isinstance(m_ans, dict):
                            for r_k, c_v in m_ans.items():
                                r_lbl = row_map.get(r_k, r_k)
                                c_lbl = col_map.get(c_v, c_v)
                                if r_lbl in counts and c_lbl in counts[r_lbl]:
                                    counts[r_lbl][c_lbl] += 1
                    except Exception:
                        pass
                opt_dist = {r_lbl: sum(counts[r_lbl].values()) for r_lbl in counts}
                stats_sum = {"matrix_distribution": counts}

            elif q_type == "ranking":
                items = options if isinstance(options, list) else []
                item_map = {
                    (it.get("id") if isinstance(it, dict) else str(it)): (it.get("label") if isinstance(it, dict) else str(it))
                    for it in items
                }
                rank_positions = {label: [] for label in item_map.values()}
                
                for a in ans_rows:
                    try:
                        ranked_list = json.loads(a["answer_value"])
                        if isinstance(ranked_list, list):
                            for pos, item_id in enumerate(ranked_list):
                                label = item_map.get(item_id, item_id)
                                if label not in rank_positions:
                                    rank_positions[label] = []
                                rank_positions[label].append(pos + 1)
                    except Exception:
                        pass
                
                avg_ranks = {}
                first_place_counts = {}
                for label, positions in rank_positions.items():
                    if positions:
                        avg_ranks[label] = round(sum(positions) / len(positions), 2)
                        first_place_counts[label] = positions.count(1)
                    else:
                        avg_ranks[label] = 0.0
                        first_place_counts[label] = 0
                
                opt_dist = first_place_counts
                stats_sum = {"ranking_averages": avg_ranks}

            elif q_type in ("long_text", "short_text"):
                samples = []
                for a in ans_rows:
                    txt = (a["answer_value"] or "").strip()
                    if txt and txt not in samples:
                        samples.append(txt)
                    if len(samples) >= 8:
                        break
                text_samples = samples

            questions_analytics.append(QuestionStats(
                question_id=qid,
                question_title=q["title"],
                question_type=q_type,
                total_answers=total_ans,
                completion_rate=comp_rate,
                drop_off_rate=drop_off,
                option_distribution=opt_dist,
                stats_summary=stats_sum,
                recent_text_samples=text_samples
            ))

        # Tính tỷ lệ hoàn thành toàn bộ cuộc khảo sát (Overall Completion Rate)
        overall_completed_count = 0
        if total_responses > 0 and q_rows:
            req_qids = [q["id"] for q in q_rows if q["is_required"]]
            target_qids = req_qids if req_qids else [q["id"] for q in q_rows]
            placeholders = ",".join(["?"] * len(target_qids))
            completed_row = conn.execute(f"""
                SELECT COUNT(*) as completed_count FROM (
                    SELECT ra.response_id
                    FROM response_answers ra
                    JOIN responses r ON r.id = ra.response_id
                    WHERE r.survey_id = ? AND ra.question_id IN ({placeholders})
                    GROUP BY ra.response_id
                    HAVING COUNT(DISTINCT ra.question_id) = ?
                )
            """, [survey_id] + target_qids + [len(target_qids)]).fetchone()
            if completed_row:
                overall_completed_count = completed_row["completed_count"]
            overall_comp_rate = round((overall_completed_count / total_responses) * 100, 1)
        else:
            overall_comp_rate = 100.0 if total_responses > 0 else 0.0

        return SurveyAnalyticsOut(
            survey_id=survey_id,
            survey_title=s_row["title"],
            total_responses=total_responses,
            is_sample_size_sufficient=is_sufficient,
            sample_size_notice=notice,
            avg_duration_seconds=avg_dur,
            overall_completion_rate=overall_comp_rate,
            funnel_analytics=funnel_analytics,
            risk_distribution=risk_dist,
            review_distribution=review_dist,
            questions_analytics=questions_analytics
        )


@router.get("/benford")
def get_benford_analysis(survey_id: str, question_id: Optional[str] = Query(None)):
    """
    Phân tích định luật Benford (First-Digit Test) trên các câu hỏi kiểu số học
    để phát hiện số liệu ngụy tạo / bịa đặt theo phương pháp Schräpler & Wagner (2012)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if question_id:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                WHERE ra.question_id = ? AND r.survey_id = ?
            """, (question_id, survey_id)).fetchall()
        else:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                JOIN questions q ON q.id = ra.question_id
                WHERE r.survey_id = ? AND q.question_type IN ('number', 'linear_scale')
            """, (survey_id,)).fetchall()

        values = []
        for a in ans_rows:
            try:
                v = float(a["answer_value"])
                values.append(v)
            except Exception:
                pass

        result = QualityEngine.compute_benford_analysis(values)
        return result


@router.get("/qualitative", response_model=QualitativeAnalysisResponse)
def get_qualitative_thematic_analysis(
    survey_id: str,
    question_id: Optional[str] = Query(None, description="Lọc theo câu hỏi cụ thể"),
    sample_limit: int = Query(150, description="Số phản hồi tối đa cần phân tích")
):
    """
    Phân tích định tính chuyên sâu: Nhận diện chủ đề, sắc thái cảm xúc (Sentiment Analysis)
    và trích xuất trích dẫn bằng chứng từ các câu hỏi phản hồi mở (short_text / long_text).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if question_id:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                WHERE ra.question_id = ? AND r.survey_id = ?
                LIMIT ?
            """, (question_id, survey_id, sample_limit)).fetchall()
        else:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                JOIN questions q ON q.id = ra.question_id
                WHERE r.survey_id = ? AND q.question_type IN ('short_text', 'long_text')
                LIMIT ?
            """, (survey_id, sample_limit)).fetchall()

        raw_texts = []
        for r in ans_rows:
            v = r["answer_value"]
            if v and isinstance(v, str) and len(v.strip()) >= 2:
                # Bỏ qua các chuỗi PII đã ẩn danh hóa
                if v.strip() != "[ANONYMIZED_PII]":
                    raw_texts.append(v.strip())

        analysis = QualitativeEngine.analyze_responses(raw_texts)
        return QualitativeAnalysisResponse(
            survey_id=survey_id,
            total_analyzed=analysis["total_analyzed"],
            sentiment_distribution=analysis["sentiment_distribution"],
            key_themes=analysis["key_themes"],
            anomaly_flags=analysis["anomaly_flags"],
            methodology_summary=analysis["methodology_summary"]
        )


@router.get("/crosstab")
def get_crosstab_analysis(
    survey_id: str,
    row_var: str = Query(..., description="ID câu hỏi đại diện cho các hàng (Row Variable)"),
    col_var: str = Query(..., description="ID câu hỏi đại diện cho các cột (Column Variable)"),
    scope: str = Query("all", description="Phạm vi dữ liệu: all (tất cả phản hồi) hoặc verified_clean (chỉ phản hồi đã duyệt hợp lệ)")
):
    """
    Phân tích Bảng Chéo (Cross-Tabulation Contingency Table & Chi-Square Independence Test):
    Kiểm định mối tương quan độc lập giữa 2 biến số định danh/thứ bậc trong cùng một cuộc khảo sát.
    """
    if row_var == col_var:
        raise HTTPException(status_code=400, detail="Vui lòng chọn 2 câu hỏi khác nhau để phân tích chéo.")

    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q1_row = conn.execute("SELECT * FROM questions WHERE id = ? AND survey_id = ?", (row_var, survey_id)).fetchone()
        q2_row = conn.execute("SELECT * FROM questions WHERE id = ? AND survey_id = ?", (col_var, survey_id)).fetchone()

        if not q1_row or not q2_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy một trong hai câu hỏi đã chọn trong khảo sát này.")

        var1_info = {
            "id": q1_row["id"],
            "title": q1_row["title"],
            "question_type": q1_row["question_type"],
            "options": json.loads(q1_row["options_json"] or "[]")
        }
        var2_info = {
            "id": q2_row["id"],
            "title": q2_row["title"],
            "question_type": q2_row["question_type"],
            "options": json.loads(q2_row["options_json"] or "[]")
        }

        query = """
            SELECT r.id, ra1.answer_value AS val1, ra2.answer_value AS val2
            FROM responses r
            JOIN response_answers ra1 ON ra1.response_id = r.id AND ra1.question_id = ?
            JOIN response_answers ra2 ON ra2.response_id = r.id AND ra2.question_id = ?
            WHERE r.survey_id = ?
        """
        params = [row_var, col_var, survey_id]
        if scope == "verified_clean":
            query += " AND (r.review_status = 'verified_valid' OR (r.risk_score < 30 AND r.review_status != 'verified_fraud'))"

        pairs_rows = conn.execute(query, params).fetchall()
        pairs = [(p["val1"], p["val2"]) for p in pairs_rows]

        crosstab = QualityEngine.compute_crosstab_analysis(pairs, var1_info, var2_info)
        crosstab["survey_id"] = survey_id
        crosstab["scope"] = scope
        return crosstab


@router.get("/reliability")
def get_survey_scale_reliability(
    survey_id: str,
    scope: str = Query("all", regex="^(all|verified_clean)$"),
    question_ids: Optional[str] = Query(None, description="Comma-separated question IDs to include in scale")
):
    """
    Phân tích chi tiết độ tin cậy thang đo (Psychometric Scale Reliability Analysis).
    Tự động nhận diện các câu hỏi thang đo Likert / Rating / Number hoặc sử dụng danh sách chỉ định.
    Tính toán Cronbach's Alpha, Standardized Alpha, Thống kê từng biến (Mean, Variance),
    Tương quan biến - tổng hiệu chỉnh (Corrected Item-Total Correlation) và Alpha nếu loại bỏ mục (Alpha if item deleted).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Lấy danh sách câu hỏi phù hợp
        if question_ids:
            specified_ids = [qid.strip() for qid in question_ids.split(",") if qid.strip()]
            placeholders = ",".join(["?"] * len(specified_ids))
            q_rows = conn.execute(f"""
                SELECT id, title, question_type, order_index, options_json
                FROM questions
                WHERE survey_id = ? AND id IN ({placeholders})
                ORDER BY order_index ASC
            """, [survey_id, *specified_ids]).fetchall()
        else:
            q_rows = conn.execute("""
                SELECT id, title, question_type, order_index, options_json
                FROM questions
                WHERE survey_id = ? AND question_type IN ('rating', 'linear_scale', 'nps', 'number')
                ORDER BY order_index ASC
            """, (survey_id,)).fetchall()

        if len(q_rows) < 2:
            all_q_rows = conn.execute("""
                SELECT id, title, question_type, order_index, options_json
                FROM questions
                WHERE survey_id = ?
                ORDER BY order_index ASC
            """, (survey_id,)).fetchall()
            
            numeric_scale_qs = []
            for q in all_q_rows:
                q_type = q["question_type"]
                if q_type in ('rating', 'linear_scale', 'nps', 'number'):
                    numeric_scale_qs.append(q)
                elif q_type in ('single_choice', 'dropdown'):
                    opts = json.loads(q["options_json"] or "[]")
                    if opts and all(isinstance(opt, (int, float)) or (isinstance(opt, str) and opt.strip().isdigit()) or (isinstance(opt, dict) and str(opt.get("value", "")).strip().isdigit()) for opt in opts):
                        numeric_scale_qs.append(q)
            q_rows = numeric_scale_qs

        if len(q_rows) < 2:
            return {
                "survey_id": survey_id,
                "scope": scope,
                "is_sufficient": False,
                "notice": "Khảo sát cần ít nhất 2 câu hỏi thang đo Likert / Rating / Điểm số để phân tích độ tin cậy Cronbach's Alpha.",
                "cronbach_alpha": None,
                "standardized_alpha": None,
                "n_samples": 0,
                "k_items": len(q_rows),
                "scale_mean": 0.0,
                "scale_variance": 0.0,
                "scale_std_dev": 0.0,
                "academic_rating": "CHƯA ĐỦ THANG ĐO",
                "interpretation": "Cần ít nhất 2 câu hỏi đo lường dạng thang đo để phân tích tính nhất quán nội tại.",
                "item_statistics": []
            }

        scale_q_ids = [q["id"] for q in q_rows]
        item_metadata = [{"id": q["id"], "title": q["title"], "order_index": q["order_index"]} for q in q_rows]

        resp_query = "SELECT id, risk_score, review_status FROM responses WHERE survey_id = ?"
        if scope == "verified_clean":
            resp_query += " AND (review_status = 'verified_valid' OR (risk_score < 30 AND review_status != 'verified_fraud'))"
        
        resp_rows = conn.execute(resp_query, (survey_id,)).fetchall()
        valid_resp_ids = [r["id"] for r in resp_rows]

        if not valid_resp_ids:
            return {
                "survey_id": survey_id,
                "scope": scope,
                "is_sufficient": False,
                "notice": "Không có phản hồi nào trong phạm vi được chọn.",
                "cronbach_alpha": None,
                "standardized_alpha": None,
                "n_samples": 0,
                "k_items": len(scale_q_ids),
                "scale_mean": 0.0,
                "scale_variance": 0.0,
                "scale_std_dev": 0.0,
                "academic_rating": "CHƯA CÓ DỮ LIỆU",
                "interpretation": "Chưa có phản hồi nào để kiểm định.",
                "item_statistics": []
            }

        placeholders_resp = ",".join(["?"] * len(valid_resp_ids))
        placeholders_q = ",".join(["?"] * len(scale_q_ids))
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, [*valid_resp_ids, *scale_q_ids]).fetchall()

        ans_by_resp: Dict[str, Dict[str, float]] = {rid: {} for rid in valid_resp_ids}
        for a in ans_rows:
            try:
                val = float(a["answer_value"])
                ans_by_resp[a["response_id"]][a["question_id"]] = val
            except (ValueError, TypeError):
                continue

        items_matrix: List[List[float]] = []
        for rid in valid_resp_ids:
            row_dict = ans_by_resp.get(rid, {})
            if len(row_dict) == len(scale_q_ids):
                items_matrix.append([row_dict[qid] for qid in scale_q_ids])

        result = QualityEngine.compute_detailed_reliability(items_matrix, item_metadata)
        result["survey_id"] = survey_id
        result["scope"] = scope
        return result


@router.get("/longitudinal", response_model=LongitudinalWaveComparisonOut)
def get_longitudinal_wave_comparison(
    survey_id: str,
    compare_survey_id: str = Query(..., description="ID của khảo sát đối chứng / Đợt 1 (Wave 1)"),
    scope: str = Query("verified_clean", description="Phạm vi phản hồi: verified_clean hoặc all")
):
    """
    Phân tích so sánh xu hướng dọc theo đợt khảo sát (Longitudinal Wave-over-Wave Comparative Analytics).
    So sánh giữa khảo sát hiện tại (Wave 2 / Post-test) và khảo sát đối chứng (Wave 1 / Pre-test):
    - Khớp các câu hỏi tương ứng giữa hai đợt (theo ID, tiêu đề hoặc thứ tự).
    - Tính toán độ lệch trung bình (Mean Shift ΔM), tỷ lệ % biến thiên.
    - Tính toán độ lệch chuẩn gộp (Pooled SD) và hệ số độ lớn hiệu ứng Cohen's d (Jacob Cohen, 1988).
    - Thực hiện kiểm định hai mẫu độc lập Welch's t-test và xác định mức ý nghĩa thống kê (p-value, APA string).
    """
    if survey_id == compare_survey_id:
        raise HTTPException(status_code=400, detail="Khảo sát so sánh đối chứng phải khác khảo sát hiện tại.")

    with get_db() as conn:
        s2_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s2_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát hiện tại.")

        s1_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (compare_survey_id,)).fetchone()
        if not s1_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát đối chứng (Wave 1).")

        # Lấy câu hỏi đợt 1 và đợt 2
        q1_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (compare_survey_id,)).fetchall()
        q2_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()

        if not q1_rows or not q2_rows:
            raise HTTPException(status_code=400, detail="Một trong hai khảo sát không có câu hỏi để phân tích đối chiếu.")

        # Khớp câu hỏi giữa 2 đợt
        matched_pairs = []
        used_q2 = set()

        # Chiến lược 1: Khớp theo ID chính xác
        q2_by_id = {q["id"]: q for q in q2_rows}
        for q1 in q1_rows:
            if q1["id"] in q2_by_id:
                matched_pairs.append((q1, q2_by_id[q1["id"]]))
                used_q2.add(q1["id"])

        # Chiến lược 2: Khớp theo tiêu đề chuẩn hóa (Title match)
        q2_by_title = {q["title"].strip().lower(): q for q in q2_rows if q["id"] not in used_q2}
        for q1 in q1_rows:
            if any(p[0]["id"] == q1["id"] for p in matched_pairs):
                continue
            clean_title = q1["title"].strip().lower()
            if clean_title in q2_by_title:
                matched_q2 = q2_by_title[clean_title]
                matched_pairs.append((q1, matched_q2))
                used_q2.add(matched_q2["id"])

        # Chiến lược 3: Khớp theo thứ tự (order_index) nếu cùng kiểu câu hỏi
        remaining_q1 = [q for q in q1_rows if not any(p[0]["id"] == q["id"] for p in matched_pairs)]
        remaining_q2 = [q for q in q2_rows if q["id"] not in used_q2]
        for q1 in remaining_q1:
            for q2 in remaining_q2:
                if q2["id"] not in used_q2 and q1["question_type"] == q2["question_type"]:
                    matched_pairs.append((q1, q2))
                    used_q2.add(q2["id"])
                    break

        if not matched_pairs:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi tương ứng nào giữa hai khảo sát để so sánh.")

        # Lấy phản hồi đợt 1 và đợt 2 theo scope
        if scope == "verified_clean":
            r1_rows = conn.execute("""
                SELECT id, duration_seconds, risk_score, risk_level, review_status
                FROM responses
                WHERE survey_id = ? AND (review_status = 'verified_valid' OR (review_status = 'unverified' AND COALESCE(risk_level, 'low') = 'low'))
            """, (compare_survey_id,)).fetchall()
            r2_rows = conn.execute("""
                SELECT id, duration_seconds, risk_score, risk_level, review_status
                FROM responses
                WHERE survey_id = ? AND (review_status = 'verified_valid' OR (review_status = 'unverified' AND COALESCE(risk_level, 'low') = 'low'))
            """, (survey_id,)).fetchall()
        else:
            r1_rows = conn.execute("SELECT id, duration_seconds, risk_score, risk_level, review_status FROM responses WHERE survey_id = ?", (compare_survey_id,)).fetchall()
            r2_rows = conn.execute("SELECT id, duration_seconds, risk_score, risk_level, review_status FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        r1_ids = [r["id"] for r in r1_rows]
        r2_ids = [r["id"] for r in r2_rows]

        # Trích xuất câu trả lời đợt 1
        ans1_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in r1_ids}
        if r1_ids:
            placeholders1 = ",".join(["?"] * len(r1_ids))
            a1_rows = conn.execute(f"SELECT response_id, question_id, answer_value FROM response_answers WHERE response_id IN ({placeholders1})", r1_ids).fetchall()
            for a in a1_rows:
                ans1_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        # Trích xuất câu trả lời đợt 2
        ans2_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in r2_ids}
        if r2_ids:
            placeholders2 = ",".join(["?"] * len(r2_ids))
            a2_rows = conn.execute(f"SELECT response_id, question_id, answer_value FROM response_answers WHERE response_id IN ({placeholders2})", r2_ids).fetchall()
            for a in a2_rows:
                ans2_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        # Chuẩn bị dữ liệu từng cặp câu hỏi
        matched_items_data = []
        for q1, q2 in matched_pairs:
            vals1 = [ans1_map[rid].get(q1["id"]) for rid in r1_ids if q1["id"] in ans1_map[rid]]
            vals2 = [ans2_map[rid].get(q2["id"]) for rid in r2_ids if q2["id"] in ans2_map[rid]]

            matched_items_data.append({
                "question_id_1": q1["id"],
                "question_id_2": q2["id"],
                "title": q2["title"] or q1["title"],
                "question_type": q2["question_type"] or q1["question_type"],
                "values_1": vals1,
                "values_2": vals2
            })

        # Metadata tổng thể
        def calc_trust(rows):
            if not rows:
                return 100.0
            clean = sum(1 for r in rows if r["review_status"] == "verified_valid" or (r["review_status"] == "unverified" and (r["risk_level"] or "low") == "low"))
            return round((clean / len(rows) * 100.0), 1)

        wave1_meta = {
            "survey_id": compare_survey_id,
            "title": s1_row["title"],
            "version": s1_row["version"],
            "total_responses": len(r1_rows),
            "trust_index": calc_trust(r1_rows),
            "avg_duration": round(statistics.mean([r["duration_seconds"] or 0 for r in r1_rows]), 1) if r1_rows else 0.0
        }

        wave2_meta = {
            "survey_id": survey_id,
            "title": s2_row["title"],
            "version": s2_row["version"],
            "total_responses": len(r2_rows),
            "trust_index": calc_trust(r2_rows),
            "avg_duration": round(statistics.mean([r["duration_seconds"] or 0 for r in r2_rows]), 1) if r2_rows else 0.0
        }

        comparison_result = QualityEngine.compute_longitudinal_comparison(
            wave1_meta=wave1_meta,
            wave2_meta=wave2_meta,
            matched_items_data=matched_items_data
        )

        return comparison_result


@router.get("/quotas", response_model=SamplingQuotaReportOut)
def get_survey_quotas(survey_id: str):
    """Lấy danh sách các ô hạn ngạch mẫu và tiến độ thu thập thực tế"""
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        
        settings = json.loads(s_row["settings_json"] or "{}")
        quota_rules = settings.get("quotas", [])

        # Lấy tất cả câu trả lời của các phản hồi hợp lệ (verified_valid hoặc unverified low risk)
        resp_rows = conn.execute("""
            SELECT id FROM responses 
            WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out') AND (risk_level != 'high' OR review_status = 'verified_valid')
        """, (survey_id,)).fetchall()
        
        r_ids = [r["id"] for r in resp_rows]
        responses_answers = []
        if r_ids:
            placeholders = ",".join(["?"] * len(r_ids))
            a_rows = conn.execute(f"""
                SELECT response_id, question_id, answer_value 
                FROM response_answers 
                WHERE response_id IN ({placeholders})
            """, r_ids).fetchall()
            
            ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in r_ids}
            for a in a_rows:
                val = a["answer_value"]
                try:
                    ans_by_resp[a["response_id"]][a["question_id"]] = json.loads(val)
                except Exception:
                    ans_by_resp[a["response_id"]][a["question_id"]] = val
            
            responses_answers = [{"id": rid, "answers": ans_by_resp[rid]} for rid in r_ids]

        cells = QuotaEngine.compute_quota_progress(quota_rules, responses_answers)
        
        total_cells = len(cells)
        filled = sum(1 for c in cells if c["status"] == "filled")
        open_c = total_cells - filled
        tot_target = sum(c["max_target"] for c in cells)
        tot_achieved = sum(c["achieved_count"] for c in cells)
        tot_pct = round((tot_achieved / tot_target * 100.0), 1) if tot_target > 0 else 100.0

        return SamplingQuotaReportOut(
            survey_id=survey_id,
            total_quota_cells=total_cells,
            filled_cells=filled,
            open_cells=open_c,
            overall_target_sum=tot_target,
            overall_achieved_sum=tot_achieved,
            overall_completion_pct=tot_pct,
            cells=cells
        )


@router.put("/quotas")
def update_survey_quotas(survey_id: str, payload: SaveQuotasRequest):
    """Cập nhật cấu hình hạn ngạch mẫu của cuộc khảo sát"""
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        settings = json.loads(s_row["settings_json"] or "{}")
        # Chuẩn hóa rules
        rules_list = []
        for r in payload.quota_rules:
            rule_id = r.id or f"{r.question_id}_{r.target_value}"
            rules_list.append({
                "id": rule_id,
                "name": r.name,
                "question_id": r.question_id,
                "target_value": r.target_value,
                "max_target": r.max_target,
                "action": r.action or "flag_overflow"
            })

        settings["quotas"] = rules_list
        conn.execute("UPDATE surveys SET settings_json = ? WHERE id = ?", (json.dumps(settings, ensure_ascii=False), survey_id))

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="UPDATE_SAMPLING_QUOTAS",
            details={"quota_cells_count": len(rules_list), "rules": rules_list}
        )

        return {"status": "success", "message": f"Đã cập nhật {len(rules_list)} quy tắc hạn ngạch mẫu."}


@router.post("/raking", response_model=DemographicRakingOut)
def run_demographic_raking(survey_id: str, payload: DemographicRakingRequest):
    """Thực thi thuật toán Cân bằng Trọng số Sau Thu thập (IPF Raking) trên mẫu sạch"""
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Lấy danh sách câu hỏi để tra cứu mã câu hỏi
        q_rows = conn.execute("SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)).fetchall()
        q_title_to_id = {q["title"].strip(): q["id"] for q in q_rows}
        q_id_to_title = {q["id"]: q["title"].strip() for q in q_rows}

        # Lọc responses theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses 
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out') AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        r_ids = [r["id"] for r in resp_rows]
        if not r_ids:
            raise HTTPException(status_code=400, detail="Không có phản hồi nào thỏa mãn phạm vi lọc để thực hiện Raking.")

        placeholders = ",".join(["?"] * len(r_ids))
        a_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value 
            FROM response_answers 
            WHERE response_id IN ({placeholders})
        """, r_ids).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in r_ids}
        for a in a_rows:
            raw_v = a["answer_value"]
            try:
                ans_map[a["response_id"]][a["question_id"]] = json.loads(raw_v)
            except Exception:
                ans_map[a["response_id"]][a["question_id"]] = raw_v

        # Chuẩn hóa target_margins: chuyển title thành question_id nếu người dùng truyền title
        resolved_targets: Dict[str, Dict[str, float]] = {}
        target_name_map: Dict[str, str] = {} # qid -> display_name

        for var_key, cat_dict in payload.target_margins.items():
            qid = var_key
            if var_key not in q_id_to_title and var_key in q_title_to_id:
                qid = q_title_to_id[var_key]
            
            resolved_targets[qid] = cat_dict
            target_name_map[qid] = q_id_to_title.get(qid, var_key)

        sample_data = []
        for rid in r_ids:
            row = {"id": rid}
            for qid in resolved_targets:
                ans_val = ans_map[rid].get(qid)
                row[qid] = ans_val
            sample_data.append(row)

        res = RakingEngine.run_raking(
            sample_data=sample_data,
            target_margins=resolved_targets,
            max_iterations=payload.max_iterations or 50,
            convergence_tol=payload.convergence_tol or 0.001,
            trim_min=payload.trim_min or 0.2,
            trim_max=payload.trim_max or 5.0
        )

        # Chuyển tên biến hiển thị trong marginal_comparisons cho thân thiện
        for comp in res["marginal_comparisons"]:
            orig_qid = comp["variable"]
            comp["variable"] = target_name_map.get(orig_qid, orig_qid)

        return DemographicRakingOut(
            survey_id=survey_id,
            converged=res["converged"],
            iterations=res["iterations"],
            max_discrepancy=res["max_discrepancy"],
            sample_size=res["sample_size"],
            design_effect_deff=res["design_effect_deff"],
            effective_sample_size_neff=res["effective_sample_size_neff"],
            statistical_efficiency_pct=res["statistical_efficiency_pct"],
            weight_stats=res["weight_stats"],
            marginal_comparisons=res["marginal_comparisons"],
            summary=res["summary"]
        )


@router.post("/raking/export-csv")
def export_raked_dataset_csv(survey_id: str, payload: DemographicRakingRequest):
    """Xuất tệp CSV với cột trọng số thống kê _statistical_weight_wi gắn theo từng bản ghi"""
    import csv
    import io

    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()
        q_title_to_id = {q["title"].strip(): q["id"] for q in q_rows}
        q_id_to_title = {q["id"]: q["title"].strip() for q in q_rows}

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT * FROM responses 
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out') AND (risk_level != 'high' OR review_status = 'verified_valid')
                ORDER BY submitted_at ASC
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT * FROM responses WHERE survey_id = ? ORDER BY submitted_at ASC", (survey_id,)).fetchall()

        r_ids = [r["id"] for r in resp_rows]
        if not r_ids:
            raise HTTPException(status_code=400, detail="Không có dữ liệu để xuất.")

        placeholders = ",".join(["?"] * len(r_ids))
        a_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value 
            FROM response_answers 
            WHERE response_id IN ({placeholders})
        """, r_ids).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in r_ids}
        for a in a_rows:
            raw_v = a["answer_value"]
            try:
                ans_map[a["response_id"]][a["question_id"]] = json.loads(raw_v)
            except Exception:
                ans_map[a["response_id"]][a["question_id"]] = raw_v

        resolved_targets: Dict[str, Dict[str, float]] = {}
        for var_key, cat_dict in payload.target_margins.items():
            qid = var_key
            if var_key not in q_id_to_title and var_key in q_title_to_id:
                qid = q_title_to_id[var_key]
            resolved_targets[qid] = cat_dict

        sample_data = []
        for rid in r_ids:
            row = {"id": rid}
            for qid in resolved_targets:
                row[qid] = ans_map[rid].get(qid)
            sample_data.append(row)

        raking_res = RakingEngine.run_raking(
            sample_data=sample_data,
            target_margins=resolved_targets,
            max_iterations=payload.max_iterations or 50,
            convergence_tol=payload.convergence_tol or 0.001,
            trim_min=payload.trim_min or 0.2,
            trim_max=payload.trim_max or 5.0
        )
        weights = raking_res["weights"]

        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ["response_id", "submitted_at", "duration_seconds", "risk_score", "risk_level", "statistical_weight_wi"]
        for q in q_rows:
            headers.append(f"Q_{q['order_index']}_{q['title'][:30]}")
        writer.writerow(headers)

        for r in resp_rows:
            rid = r["id"]
            w = weights.get(rid, 1.0)
            row_data = [
                rid,
                r["submitted_at"],
                r["duration_seconds"],
                r["risk_score"],
                r["risk_level"],
                w
            ]
            for q in q_rows:
                val = ans_map[rid].get(q["id"], "")
                if isinstance(val, (list, dict)):
                    val_str = json.dumps(val, ensure_ascii=False)
                else:
                    val_str = str(val) if val is not None else ""
                row_data.append(val_str)
            writer.writerow(row_data)

        csv_content = "\ufeff" + output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="datatrust_raked_dataset_{survey_id[:8]}.csv"'}
        )


@router.get("/dif", response_model=DIFReportOut)
def get_differential_item_functioning(
    survey_id: str,
    grouping_question_id: str = Query(..., description="ID của câu hỏi phân nhóm nhân khẩu học"),
    reference_group: str = Query(..., description="Giá trị của nhóm tham chiếu (Reference Group)"),
    focal_group: str = Query(..., description="Giá trị của nhóm tâm điểm kiểm định (Focal Group)"),
    scope: str = Query("verified_clean", description="Phạm vi mẫu: verified_clean hoặc all"),
    strata_count: int = Query(4, description="Số phân tầng tổng điểm (quartiles)")
):
    """
    Thực hiện kiểm định Bất biến Đo lường & Hàm mục Sai lệch (Mantel-Haenszel DIF)
    cho toàn bộ các câu hỏi thang đo theo chuẩn ETS (Class A, B, C).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("SELECT id, title, question_type, options_json FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()
        
        # Tìm câu hỏi phân nhóm
        grouping_q = next((q for q in q_rows if q["id"] == grouping_question_id), None)
        if not grouping_q:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phân nhóm nhân khẩu học.")

        # Tìm các câu hỏi thang đo số (rating, linear_scale, nps, hoặc number)
        scale_qs = [
            q for q in q_rows 
            if q["question_type"] in ("rating", "linear_scale", "nps", "number") 
               or (q["question_type"] == "single_choice" and any(k in q["title"].lower() for k in ["hài lòng", "đồng ý", "thang điểm", "likert", "mức độ"]))
        ]
        
        if len(scale_qs) < 2:
            raise HTTPException(
                status_code=400,
                detail="Khảo sát cần có ít nhất 2 câu hỏi dạng thang đo (Rating, Linear Scale, NPS, Likert) để phân tích DIF."
            )

        scale_q_ids = [q["id"] for q in scale_qs]
        q_id_to_title = {q["id"]: q["title"] for q in q_rows}

        # Lấy danh sách responses theo scope
        if scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses 
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        r_ids = [r["id"] for r in resp_rows]
        if not r_ids:
            raise HTTPException(status_code=400, detail="Không có phản hồi nào phù hợp trong phạm vi lọc.")

        # Nạp trước answers
        placeholders = ",".join(["?"] * len(r_ids))
        a_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value 
            FROM response_answers 
            WHERE response_id IN ({placeholders})
        """, r_ids).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in r_ids}
        for a in a_rows:
            raw_v = a["answer_value"]
            try:
                ans_map[a["response_id"]][a["question_id"]] = json.loads(raw_v)
            except Exception:
                ans_map[a["response_id"]][a["question_id"]] = raw_v

        records = []
        for rid in r_ids:
            records.append({
                "id": rid,
                "answers": ans_map[rid]
            })

        dif_res = DIFEngine.compute_mantel_haenszel_dif(
            records=records,
            scale_question_ids=scale_q_ids,
            grouping_var=grouping_question_id,
            reference_group=reference_group,
            focal_group=focal_group,
            num_strata=strata_count
        )

        item_results = []
        for it in dif_res.get("items", []):
            item_results.append(DIFItemResult(
                question_id=it["question_id"],
                question_title=q_id_to_title.get(it["question_id"], it["question_id"]),
                median_threshold=it["median_threshold"],
                active_strata_count=it["active_strata_count"],
                chi2_mh=it["chi2_mh"],
                p_value=it["p_value"],
                alpha_odds_ratio=it["alpha_odds_ratio"],
                delta_ets=it["delta_ets"],
                abs_delta_ets=it["abs_delta_ets"],
                ets_class=it["ets_class"],
                ets_label=it["ets_label"],
                favored_group=it["favored_group"],
                action_recommendation=it["action_recommendation"],
                is_statistically_significant=it["is_statistically_significant"]
            ))

        return DIFReportOut(
            survey_id=survey_id,
            grouping_variable_id=grouping_question_id,
            grouping_variable_title=grouping_q["title"],
            reference_group=reference_group,
            focal_group=focal_group,
            sample_reference=dif_res.get("sample_reference", 0),
            sample_focal=dif_res.get("sample_focal", 0),
            total_eval_sample=dif_res.get("total_eval_sample", 0),
            strata_count=dif_res.get("strata_count", strata_count),
            class_a_count=dif_res.get("class_a_count", 0),
            class_b_count=dif_res.get("class_b_count", 0),
            class_c_count=dif_res.get("class_c_count", 0),
            overall_verdict=dif_res.get("overall_verdict", "CHƯA_ĐỦ_MẪU"),
            summary=dif_res.get("summary", ""),
            items=item_results
        )


@router.get("/cognitive-pacing")
def get_cognitive_pacing_analytics(survey_id: str):
    """
    Phân tích Gánh nặng Nhận thức & Nhịp độ Trả lời (Couper 2001, Krosnick 1991, Dillman 2014).
    Đo lường thời gian đọc lý thuyết, phát hiện vội vã/chọn bừa (Satisficing),
    và đánh giá rủi ro mệt mỏi nhận thức (Cognitive Fatigue) theo thứ tự câu hỏi.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("""
            SELECT id, order_index, question_type, title, description, options_json
            FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        if not q_rows:
            raise HTTPException(status_code=400, detail="Khảo sát chưa có câu hỏi nào để phân tích nhận thức.")

        questions = []
        for q in q_rows:
            questions.append({
                "id": q["id"],
                "order_index": q["order_index"],
                "question_type": q["question_type"],
                "title": q["title"],
                "description": q["description"] or "",
                "options": json.loads(q["options_json"] or "[]")
            })

        resp_rows = conn.execute("""
            SELECT duration_seconds FROM responses WHERE survey_id = ? AND duration_seconds > 0
        """, (survey_id,)).fetchall()

        durations = [r["duration_seconds"] for r in resp_rows]

        pacing_result = CognitivePacingEngine.analyze_survey_pacing(
            survey_title=s_row["title"],
            questions=questions,
            durations=durations
        )

        return pacing_result


@router.get("/multivariate-outliers")
def get_multivariate_outliers(
    survey_id: str,
    scope: str = Query("all", regex="^(all|verified_clean)$"),
    question_ids: Optional[str] = Query(None, description="Danh sách question_id dạng phẩy cách (tùy chọn)")
):
    """
    Phân tích Điểm Dị biệt Đa biến (Multivariate Outlier Detection) bằng Khoảng cách Mahalanobis (D_M^2)
    và phân phối Chi-Square (Mahalanobis 1936, Rousseeuw 1990, Tabachnick & Fidell 2019).
    Phát hiện các phản hồi có tổ hợp câu trả lời dị biệt cực đoan (p < .001) hoặc bất thường (p < .01).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title, question_type, options_json FROM questions WHERE survey_id = ? ORDER BY order_index ASC",
            (survey_id,)
        ).fetchall()

        if not q_rows:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": "Khảo sát chưa có câu hỏi nào để phân tích dị biệt đa biến.",
                "total_records": 0,
                "variable_count": 0,
                "scale_variable_ids": [],
                "scale_variable_titles": [],
                "outliers_summary": []
            }

        q_id_to_title = {q["id"]: q["title"] for q in q_rows}

        # Xác định danh sách câu hỏi thang đo
        if question_ids:
            requested_ids = [qid.strip() for qid in question_ids.split(",") if qid.strip()]
            scale_qs = [q for q in q_rows if q["id"] in requested_ids]
        else:
            scale_qs = [
                q for q in q_rows
                if q["question_type"] in ("rating", "linear_scale", "nps", "number", "likert")
                or (q["question_type"] == "single_choice" and any(k in q["title"].lower() for k in ["hài lòng", "đồng ý", "thang điểm", "likert", "mức độ"]))
            ]

        if len(scale_qs) < 2:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": f"Cần ít nhất 2 câu hỏi thang đo số (Likert, Rating, NPS, Scale) để phân tích dị biệt đa biến. Hiện có: {len(scale_qs)}.",
                "total_records": 0,
                "variable_count": len(scale_qs),
                "scale_variable_ids": [q["id"] for q in scale_qs],
                "scale_variable_titles": [q["title"] for q in scale_qs],
                "outliers_summary": []
            }

        scale_q_ids = [q["id"] for q in scale_qs]

        # Lấy danh sách phản hồi theo scope
        if scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id, duration_seconds, risk_score, review_status
                FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id, duration_seconds, risk_score, review_status
                FROM responses
                WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Chưa có phản hồi nào trong phạm vi được chọn.",
                "total_records": 0,
                "valid_records_count": 0,
                "variable_count": len(scale_q_ids),
                "scale_variable_ids": scale_q_ids,
                "scale_variable_titles": [q_id_to_title.get(qid, qid) for qid in scale_q_ids],
                "outliers_summary": []
            }

        resp_ids = [r["id"] for r in resp_rows]
        resp_map = {r["id"]: r for r in resp_rows}

        # Nạp câu trả lời của các câu hỏi thang đo
        placeholders_r = ",".join(["?"] * len(resp_ids))
        placeholders_q = ",".join(["?"] * len(scale_q_ids))
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *scale_q_ids)).fetchall()

        answers_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            answers_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        records = []
        for rid, r in resp_map.items():
            records.append({
                "id": rid,
                "duration_seconds": r["duration_seconds"] or 0.0,
                "risk_score": r["risk_score"] or 0.0,
                "review_status": r["review_status"] or "unverified",
                "answers": answers_by_resp[rid]
            })

        result = MahalanobisEngine.compute_mahalanobis_distances(
            records=records,
            scale_question_ids=scale_q_ids
        )

        result["scale_variable_titles"] = [q_id_to_title.get(qid, qid) for qid in scale_q_ids]
        return result


@router.get("/efa")
def get_exploratory_factor_analysis(
    survey_id: str,
    scope: str = Query("all", pattern="^(all|verified_clean)$"),
    question_ids: Optional[str] = Query(None, description="Danh sách question_id dạng phẩy cách (tùy chọn)"),
    rotation: str = Query("varimax", pattern="^(varimax|none)$"),
    min_eigenvalue: float = Query(1.0, ge=0.1, le=5.0),
    forced_factors: Optional[int] = Query(None, ge=1, le=20)
):
    """
    Phân tích Nhân tố Khám phá (Exploratory Factor Analysis - EFA) và Rút gọn Thứ nguyên dữ liệu khảo sát.
    Bao gồm:
    - Kiểm định KMO (Kaiser-Meyer-Olkin) & MSA từng biến
    - Kiểm định Bartlett's Test of Sphericity
    - Phân rã trị riêng (Jacobi Eigenvalue Decomposition) & Scree Plot
    - Phép xoay trực giao Varimax (Kaiser 1958)
    - Hệ số tải nhân tố (Factor Loadings), Communalities (h²), và Phương sai trích
    - Diễn giải học thuật tự động chuẩn APA 7th Edition
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, order_index, title, question_type, options_json FROM questions WHERE survey_id = ? ORDER BY order_index ASC",
            (survey_id,)
        ).fetchall()

        if not q_rows:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": "Khảo sát chưa có câu hỏi nào để phân tích nhân tố EFA.",
                "total_records": 0,
                "variable_count": 0,
                "items": []
            }

        q_id_to_title = {q["id"]: q["title"] for q in q_rows}
        q_id_to_order = {q["id"]: q["order_index"] for q in q_rows}

        if question_ids:
            requested_ids = [qid.strip() for qid in question_ids.split(",") if qid.strip()]
            scale_qs = [q for q in q_rows if q["id"] in requested_ids]
        else:
            scale_qs = [
                q for q in q_rows
                if q["question_type"] in ("rating", "linear_scale", "nps", "number", "likert")
                or (q["question_type"] == "single_choice" and any(k in q["title"].lower() for k in ["hài lòng", "đồng ý", "thang điểm", "likert", "mức độ"]))
            ]

        if len(scale_qs) < 3:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": f"Cần ít nhất 3 câu hỏi thang đo số (Likert, Rating, NPS, Scale) để phân tích EFA. Hiện có: {len(scale_qs)}.",
                "total_records": 0,
                "variable_count": len(scale_qs),
                "items": []
            }

        scale_q_ids = [q["id"] for q in scale_qs]

        if scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Chưa có phản hồi nào trong phạm vi được chọn.",
                "total_records": 0,
                "valid_records_count": 0,
                "variable_count": len(scale_q_ids),
                "items": []
            }

        resp_ids = [r["id"] for r in resp_rows]

        placeholders_r = ",".join(["?"] * len(resp_ids))
        placeholders_q = ",".join(["?"] * len(scale_q_ids))
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *scale_q_ids)).fetchall()

        answers_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            answers_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        records = [{"id": rid, "answers": answers_by_resp[rid]} for rid in resp_ids]

        result = EFAEngine.analyze_survey_efa(
            records=records,
            scale_question_ids=scale_q_ids,
            rotation=rotation,
            min_eigenvalue=min_eigenvalue,
            forced_factors=forced_factors
        )

        if "items" in result:
            for item in result["items"]:
                qid = item["question_id"]
                item["question_title"] = q_id_to_title.get(qid, qid)
                item["order_index"] = q_id_to_order.get(qid, 0)

        result["scale_variable_titles"] = [q_id_to_title.get(qid, qid) for qid in scale_q_ids]
        return result


@router.post("/ttest/independent")
def run_independent_samples_ttest(survey_id: str, payload: IndependentTTestRequest):
    """
    Kiểm định Giả thuyết T-Test Độc lập 2 nhóm (Independent Samples T-Test):
    - Kiểm định tính đồng nhất phương sai Levene (Brown-Forsythe)
    - T-Test Student (Equal variances) hoặc T-Test Welch (Unequal variances)
    - Kích thước hiệu ứng Cohen's d & Hedges' g
    - Khoảng tin cậy 95% chênh lệch trung bình và Diễn giải APA 7th Edition
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("SELECT id, title, question_type FROM questions WHERE survey_id = ?", (survey_id,)).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        grp_q = q_map.get(payload.grouping_question_id)
        if not grp_q:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phân nhóm.")

        tgt_q = q_map.get(payload.target_question_id)
        if not tgt_q:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đo lường mục tiêu.")

        # Lấy danh sách phản hồi theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Không có phản hồi nào trong phạm vi được chọn."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN (?, ?)
        """, (*resp_ids, payload.grouping_question_id, payload.target_question_id)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        g1_vals: List[float] = []
        g2_vals: List[float] = []

        g1_target = payload.group1_value.strip().lower()
        g2_target = payload.group2_value.strip().lower()

        for rid in resp_ids:
            a_dict = ans_by_resp[rid]
            grp_val = str(a_dict.get(payload.grouping_question_id, "")).strip().lower()
            tgt_raw = a_dict.get(payload.target_question_id)
            num_val = parse_num(tgt_raw)

            if num_val is not None:
                if grp_val == g1_target:
                    g1_vals.append(num_val)
                elif grp_val == g2_target:
                    g2_vals.append(num_val)

        return TTestEngine.compute_independent_ttest(
            group1_values=g1_vals,
            group2_values=g2_vals,
            group1_label=payload.group1_value,
            group2_label=payload.group2_value,
            variable_label=tgt_q["title"]
        )


@router.post("/ttest/paired")
def run_paired_samples_ttest(survey_id: str, payload: PairedTTestRequest):
    """
    Kiểm định Giả thuyết T-Test Ghép cặp / Mẫu phụ thuộc (Paired Samples T-Test):
    - Đánh giá chênh lệch Trước vs Sau (Pre vs Post Intervention) trên cùng 1 đối tượng
    - Hệ số tương quan Pearson giữa 2 lần đo
    - Kích thước hiệu ứng Cohen's d_z & Hedges' g_z
    - Khoảng tin cậy 95% chênh lệch trung bình và Diễn giải APA 7th Edition
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("SELECT id, title, question_type FROM questions WHERE survey_id = ?", (survey_id,)).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        q1 = q_map.get(payload.pre_question_id)
        if not q1:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đo lường lần 1 (Pre).")

        q2 = q_map.get(payload.post_question_id)
        if not q2:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đo lường lần 2 (Post).")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Không có phản hồi nào trong phạm vi được chọn."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN (?, ?)
        """, (*resp_ids, payload.pre_question_id, payload.post_question_id)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        pairs: List[Tuple[float, float]] = []
        for rid in resp_ids:
            a_dict = ans_by_resp[rid]
            v_pre = parse_num(a_dict.get(payload.pre_question_id))
            v_post = parse_num(a_dict.get(payload.post_question_id))

            if v_pre is not None and v_post is not None:
                # Đặt cặp là (Post, Pre) để chênh lệch thể hiện mức cải thiện Post - Pre
                pairs.append((v_post, v_pre))

        return TTestEngine.compute_paired_ttest(
            pairs=pairs,
            variable1_label=f"{q2['title']} (Lần 2 / Post)",
            variable2_label=f"{q1['title']} (Lần 1 / Pre)"
        )


@router.post("/anova")
def run_oneway_anova(survey_id: str, payload: OneWayANOVARequest):
    """
    Phân tích Phương sai Một chiều (One-Way ANOVA) & Kiểm định Hậu nghiệm Tukey's HSD:
    - So sánh sự khác biệt điểm số qua 3 hoặc nhiều nhóm phân loại
    - Bảng ANOVA tổng quát: SS_between, SS_within, MS, F-statistic, p-value
    - Kiểm định tính đồng nhất phương sai Levene cho K nhóm
    - Kích thước hiệu ứng Eta-Squared (η²) và Omega-Squared (ω²)
    - Kiểm định hậu nghiệm Tukey's HSD (Tukey-Kramer pairwise tests)
    - Diễn giải học thuật tự động chuẩn APA 7th Edition
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("SELECT id, title, question_type FROM questions WHERE survey_id = ?", (survey_id,)).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        grp_q = q_map.get(payload.grouping_question_id)
        if not grp_q:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phân nhóm.")

        tgt_q = q_map.get(payload.target_question_id)
        if not tgt_q:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đo lường mục tiêu.")

        # Lấy danh sách phản hồi theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Không có phản hồi nào trong phạm vi được chọn."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN (?, ?)
        """, (*resp_ids, payload.grouping_question_id, payload.target_question_id)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        # Gom nhóm dữ liệu
        selected_set = set(g.strip().lower() for g in payload.selected_groups) if payload.selected_groups else None
        groups_dict: Dict[str, List[float]] = {}

        for rid in resp_ids:
            a_dict = ans_by_resp[rid]
            grp_raw = a_dict.get(payload.grouping_question_id)
            if not grp_raw:
                continue

            grp_name = str(grp_raw).strip()
            if selected_set and grp_name.lower() not in selected_set:
                continue

            tgt_val = parse_num(a_dict.get(payload.target_question_id))
            if tgt_val is not None:
                groups_dict.setdefault(grp_name, []).append(tgt_val)

        return ANOVAEngine.compute_oneway_anova(
            groups_data=groups_dict,
            grouping_label=grp_q["title"],
            variable_label=tgt_q["title"]
        )


@router.get("/correlation")
def get_bivariate_correlation_matrix(
    survey_id: str,
    method: str = Query("pearson", pattern="^(pearson|spearman)$"),
    scope: str = Query("all", pattern="^(all|verified_clean)$"),
    question_ids: Optional[str] = Query(None, description="Danh sách question_id dạng phẩy cách (tùy chọn)")
):
    """
    Phân tích Ma trận Tương quan Đôi (Bivariate Correlation Matrix)
    hỗ trợ hệ số tương quan tuyến tính Pearson r và phi tham số thứ bậc Spearman rho
    (Pearson 1895, Spearman 1904, Fisher 1915, Cohen 1988, Tabachnick & Fidell 2019).
    Bao gồm kiểm định ý nghĩa 2 phía, khoảng tin cậy 95% Fisher z, và phát hiện đa cộng tuyến (|r| >= .85).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT id, order_index, question_type, title, options_json
            FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        if not q_rows:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": "Khảo sát chưa có câu hỏi nào để phân tích tương quan."
            }

        # Lọc câu hỏi mục tiêu
        chosen_q_rows = []
        if question_ids:
            target_ids = set([qid.strip() for qid in question_ids.split(",") if qid.strip()])
            chosen_q_rows = [q for q in q_rows if q["id"] in target_ids]
        else:
            scale_types = {"rating", "linear_scale", "number", "nps", "likert"}
            for q in q_rows:
                qtype = q["question_type"]
                title_lower = q["title"].lower()
                if qtype in scale_types:
                    chosen_q_rows.append(q)
                elif qtype == "single_choice" and any(k in title_lower for k in ["hài lòng", "đồng ý", "thang điểm", "likert", "mức độ", "điểm"]):
                    chosen_q_rows.append(q)

        if len(chosen_q_rows) < 2:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": f"Cần tối thiểu 2 biến thang đo định lượng (hiện có {len(chosen_q_rows)} biến). Vui lòng chọn thêm câu hỏi."
            }

        # Lấy danh sách phản hồi theo scope
        if scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Không có phản hồi nào trong phạm vi được chọn."
            }

        resp_ids = [r["id"] for r in resp_rows]
        chosen_ids = [q["id"] for q in chosen_q_rows]

        placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(chosen_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN ({q_placeholders})
        """, (*resp_ids, *chosen_ids)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        variables_data: Dict[str, Dict[str, Any]] = {}
        for idx, q in enumerate(chosen_q_rows):
            qid = q["id"]
            num_vals = []
            for rid in resp_ids:
                raw_ans = ans_by_resp[rid].get(qid)
                num_vals.append(parse_num(raw_ans))

            variables_data[qid] = {
                "title": q["title"],
                "label": f"VAR{idx+1:03d}",
                "values": num_vals
            }

        return CorrelationEngine.analyze_correlation_matrix(
            variables_data=variables_data,
            method=method
        )


@router.post("/regression")
def run_multiple_linear_regression(survey_id: str, payload: LinearRegressionRequest):
    """
    Hồi quy Tuyến tính Đa biến OLS (Multiple Linear Regression)
    kết hợp Chẩn đoán Đa cộng tuyến (VIF & Tolerance), Kiểm định Omnibus F,
    Hệ số Chuẩn hóa Beta, và Báo cáo Diễn giải APA 7th Edition
    (Legendre 1805, Gauss 1809, Hair et al. 2010, Kline 2015).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if not payload.predictor_question_ids:
            raise HTTPException(status_code=400, detail="Cần chọn tối thiểu 1 biến độc lập (predictor).")

        if payload.dependent_question_id in payload.predictor_question_ids:
            raise HTTPException(status_code=400, detail="Biến phụ thuộc không được trùng với biến độc lập.")

        # Lấy thông tin câu hỏi
        dep_q = conn.execute("SELECT id, title, question_type FROM questions WHERE id = ? AND survey_id = ?",
                             (payload.dependent_question_id, survey_id)).fetchone()
        if not dep_q:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phụ thuộc (dependent variable).")

        pred_placeholders = ",".join(["?"] * len(payload.predictor_question_ids))
        pred_rows = conn.execute(f"""
            SELECT id, title, question_type, order_index
            FROM questions WHERE survey_id = ? AND id IN ({pred_placeholders})
            ORDER BY order_index ASC
        """, (survey_id, *payload.predictor_question_ids)).fetchall()

        if len(pred_rows) != len(payload.predictor_question_ids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều biến độc lập không tồn tại trong khảo sát.")

        # Lấy danh sách phản hồi theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Không có phản hồi nào trong phạm vi được chọn."
            }

        resp_ids = [r["id"] for r in resp_rows]
        all_qids = [payload.dependent_question_id] + [p["id"] for p in pred_rows]

        placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN ({q_placeholders})
        """, (*resp_ids, *all_qids)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        # Ghép cặp quan sát hoàn chỉnh (listwise deletion)
        X_matrix = []
        y_vector = []

        for rid in resp_ids:
            a_dict = ans_by_resp[rid]
            dep_val = parse_num(a_dict.get(payload.dependent_question_id))
            if dep_val is None:
                continue

            row_preds = []
            has_missing = False
            for p_q in pred_rows:
                p_val = parse_num(a_dict.get(p_q["id"]))
                if p_val is None:
                    has_missing = True
                    break
                row_preds.append(p_val)

            if not has_missing:
                X_matrix.append(row_preds)
                y_vector.append(dep_val)

        pred_labels = [f"VAR{idx+1:03d}" for idx in range(len(pred_rows))]
        pred_titles = [p_q["title"] for p_q in pred_rows]

        return RegressionEngine.fit_ols(
            X_matrix=X_matrix,
            y_vector=y_vector,
            predictor_labels=pred_labels,
            predictor_titles=pred_titles,
            dependent_title=dep_q["title"]
        )


@router.post("/power-analysis")
def run_power_analysis(survey_id: str, payload: PowerAnalysisRequest):
    """
    Phân tích Lực Thống Kê & Đánh Giá Tính Thỏa Đáng Cỡ Mẫu (Statistical Power Analysis):
    - Đánh giá Post-Hoc Power cho tập mẫu thực tế đã thu thập của khảo sát.
    - Tính toán cỡ mẫu Cochran (1977) với hiệu chỉnh tổng thể hữu hạn (FPC).
    - Ước lượng cỡ mẫu tối thiểu cho T-Test (Cohen's d) và Tương quan Pearson (r).
    - Sinh dữ liệu đường cong Lực thống kê (Power Curve SVG) và trích dẫn APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        scope_filter = " AND (review_status = 'verified_valid' OR (review_status = 'unverified' AND risk_level = 'low'))" if payload.scope == "verified_clean" else ""
        resp_count = conn.execute(f"SELECT COUNT(*) AS cnt FROM responses WHERE survey_id = ?{scope_filter}", (survey_id,)).fetchone()["cnt"]

    adequacy = PowerAnalysisEngine.evaluate_survey_sample_adequacy(current_n=resp_count, alpha=payload.alpha)
    cochran = PowerAnalysisEngine.calculate_cochran_sample_size(
        confidence_level=payload.confidence_level,
        margin_of_error=payload.margin_of_error,
        proportion=0.50,
        population_size=payload.population_size
    )
    power_curve = PowerAnalysisEngine.generate_power_curve(
        analysis_type=payload.analysis_type if payload.analysis_type in ("ttest", "correlation") else "ttest",
        effect_size=payload.effect_size,
        alpha=payload.alpha,
        max_n=max(200, resp_count * 2)
    )

    return {
        "survey_id": survey_id,
        "survey_title": s_row["title"],
        "scope": payload.scope,
        "current_sample_size": resp_count,
        "adequacy": adequacy,
        "cochran_estimation": cochran,
        "power_curve": power_curve,
        "parameters": {
            "analysis_type": payload.analysis_type,
            "confidence_level": payload.confidence_level,
            "margin_of_error": payload.margin_of_error,
            "population_size": payload.population_size,
            "effect_size": payload.effect_size,
            "target_power": payload.target_power,
            "alpha": payload.alpha
        }
    }


@router.post("/split-ballot")
def run_split_ballot_analysis(survey_id: str, payload: SplitBallotAnalysisRequest):
    """
    Phân tích Thử nghiệm Tách Phiếu & Khảo nghiệm Từ ngữ (Split-Ballot Survey Experiment):
    - So sánh tỷ lệ hoàn thành, phân phối câu trả lời giữa các nhóm A/B
    - Tính toán Welch's T-Test / Chi-Square kiểm định mức độ chênh lệch
    - Đánh giá Chỉ Số Biến Dạng Từ Ngữ (Manipulated Wording Distortion Index - MWDI)
    """
    try:
        return SplitBallotEngine.analyze_split_ballot_survey(
            survey_id=survey_id,
            question_id=payload.question_id,
            scope=payload.scope
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/split-ballot")
def get_split_ballot_analysis(
    survey_id: str,
    question_id: str = Query(..., description="ID câu hỏi mục tiêu cần phân tích"),
    scope: str = Query("verified_clean", description="Phạm vi: verified_clean hoặc all")
):
    """
    Endpoint GET thuận tiện cho phân tích Thử nghiệm Tách Phiếu A/B
    """
    try:
        return SplitBallotEngine.analyze_split_ballot_survey(
            survey_id=survey_id,
            question_id=question_id,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/rasch")
def get_rasch_analysis(survey_id: str, scope: str = "valid"):
    try:
        return RaschEngine.analyze_survey_rasch(
            survey_id=survey_id,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rasch")


@router.post("/rasch")
def run_rasch_analysis(survey_id: str, payload: RaschAnalysisRequest = RaschAnalysisRequest()):
    """
    Hiệu chuẩn mô hình Rasch 1-PL (Item Response Theory):
    - Ước lượng độ khó câu hỏi (Item Difficulty b_i) và năng lực tiềm ẩn (Person Theta_n)
    - Tính toán chỉ số Infit MNSQ và Outfit MNSQ (Wright & Linacre, 1994)
    - Xây dựng bản đồ Wright Map (Person-Item Map)
    - Độ tin cậy phân tách (Item & Person Separation Reliability) và đoạn trích dẫn APA 7th Edition
    """
    try:
        return RaschEngine.analyze_survey_rasch(
            survey_id=survey_id,
            scope=payload.scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rasch")
def get_rasch_analysis(
    survey_id: str,
    scope: str = Query("verified_clean", description="Phạm vi: verified_clean hoặc all")
):
    """
    Endpoint GET cho mô hình Rasch 1-PL và Wright Map
    """
    try:
        return RaschEngine.analyze_survey_rasch(
            survey_id=survey_id,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clusters")
def get_cluster_analysis(survey_id: str, k: int = 3, scope: str = "valid"):
    try:
        return ClusterEngine.analyze_survey_clusters(
            survey_id=survey_id,
            question_ids=None,
            k=k,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/clusters")


@router.post("/clusters")
def run_cluster_analysis(survey_id: str, payload: ClusterAnalysisRequest = ClusterAnalysisRequest()):
    """
    Phân tích Phân cụm Người trả lời (Respondent Typology & Persona Segmentation):
    - K-Means++ Clustering & Z-Score Standardization
    - Đánh giá hệ số Silhouette (Rousseeuw 1987) và đường cong Elbow WCSS
    - Đo lường mức độ phân hóa câu hỏi (ANOVA F-ratio)
    - Tự động sinh hồ sơ Persona và đoạn trích dẫn APA 7th Edition
    """
    try:
        return ClusterEngine.analyze_survey_clusters(
            survey_id=survey_id,
            question_ids=payload.question_ids,
            k=payload.k,
            scope=payload.scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clusters")
def get_cluster_analysis(
    survey_id: str,
    k: Optional[int] = Query(None, description="Số lượng cụm K (nếu bỏ trống hệ thống tự chọn theo Silhouette)"),
    scope: str = Query("verified_clean", description="Phạm vi: verified_clean hoặc all")
):
    """
    Endpoint GET cho phân tích phân cụm người trả lời
    """
    try:
        return ClusterEngine.analyze_survey_clusters(
            survey_id=survey_id,
            k=k,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pairwise-similarity")
def get_pairwise_similarity_analysis(survey_id: str, threshold: float = 0.85, max_matrix_size: int = 100, scope: str = "valid"):
    try:
        return SimilarityEngine.analyze_survey_similarity(
            survey_id=survey_id,
            threshold=threshold,
            max_matrix_size=max_matrix_size,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pairwise-similarity")


@router.post("/pairwise-similarity")
def run_pairwise_similarity_analysis(survey_id: str, payload: PairwiseSimilarityRequest = PairwiseSimilarityRequest()):
    """
    Phân tích ma trận tương đồng cặp (Pairwise Similarity) & Bóc tách mạng lưới thông đồng (Collusion Syndicate Rings):
    - Tính ma trận khoảng cách Hamming/Jaccard cho câu hỏi đóng & n-gram Jaccard cho câu hỏi mở.
    - Phát hiện trùng lặp 100%, gần trùng lặp, chia sẻ vân tay thiết bị (device_id) & địa chỉ IP.
    - Trích xuất các thành phần liên thông đồ thị (Connected Components) nhận diện các vòng gian lận / bot farm.
    - Tạo ma trận tương đồng trực quan (Heatmap Matrix) và đánh giá chỉ số liêm chính dữ liệu theo chuẩn AAPOR / ISO 20252.
    """
    try:
        return SimilarityEngine.analyze_survey_similarity(
            survey_id=survey_id,
            threshold=payload.threshold,
            max_matrix_size=payload.max_matrix_size,
            scope=payload.scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pairwise-similarity")
def get_pairwise_similarity_analysis(
    survey_id: str,
    threshold: float = Query(0.80, ge=0.50, le=1.0, description="Ngưỡng tương đồng tối thiểu (0.50 - 1.0)"),
    max_matrix_size: int = Query(60, ge=10, le=200, description="Kích thước ma trận tối đa (10 - 200)"),
    scope: str = Query("all", description="Phạm vi phản hồi: all hoặc verified_clean")
):
    """
    Endpoint GET cho phân tích ma trận tương đồng cặp và mạng lưới thông đồng
    """
    try:
        return SimilarityEngine.analyze_survey_similarity(
            survey_id=survey_id,
            threshold=threshold,
            max_matrix_size=max_matrix_size,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/spatial")
def run_spatial_analysis(survey_id: str, payload: SpatialAnalysisRequest = SpatialAnalysisRequest()):
    """
    Kiem dinh Khong gian Thuc dia va Gian lan Toa do GPS (Spatial Geo-Fencing va DBSCAN):
    - Phan cum mat do DBSCAN (Ester et al., 1996) phat hien gian lan ngoi mot cho khai khong
    - Phat hien van toc di chuyen bat kha thi / Gia lap vi tri (Teleportation & GPS Spoofing)
    - Kiem dinh ranh gioi da giac Geo-Fencing bang thuat toan Ray-Casting
    - Do do phan tan khong gian chuan (Spatial Standard Distance Deviation - Bachi 1962)
    """
    try:
        polygon = None
        if payload.geofence_polygon:
            polygon = [(p[0], p[1]) for p in payload.geofence_polygon if len(p) >= 2]
        return SpatialEngine.analyze_survey_spatial(
            survey_id=survey_id,
            eps_meters=payload.eps_meters,
            min_samples=payload.min_samples,
            max_speed_kmh=payload.max_speed_kmh,
            geofence_polygon=polygon,
            scope=payload.scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/spatial")
def get_spatial_analysis(
    survey_id: str,
    eps_meters: float = Query(75.0, ge=10.0, le=2000.0, description="Ban kinh lang gieng DBSCAN (met)"),
    min_samples: int = Query(3, ge=2, le=20, description="So diem toi thieu de hinh thanh cum"),
    max_speed_kmh: float = Query(120.0, ge=20.0, le=500.0, description="Van toc di chuyen toi da (km/h)"),
    scope: str = Query("all", description="Pham vi phan hoi: all hoac verified_clean")
):
    """
    Endpoint GET cho kiem dinh khong gian thuc dia va phat hien gian lan GPS
    """
    try:
        return SpatialEngine.analyze_survey_spatial(
            survey_id=survey_id,
            eps_meters=eps_meters,
            min_samples=min_samples,
            max_speed_kmh=max_speed_kmh,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mediation", response_model=MediationAnalysisOut)
def run_mediation_analysis(survey_id: str, payload: MediationAnalysisRequest):
    """
    Phân tích Tác động Trung gian (Statistical Mediation & Path Analysis)
    theo chuẩn Baron & Kenny (1986), Preacher & Hayes (2004, 2008), Sobel (1982),
    Bootstrap 95% CI và VAF (Hair et al., 2017).
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        x_id = payload.x_question_id or payload.independent_var_id
        m_id = payload.m_question_id or payload.mediator_var_id
        y_id = payload.y_question_id or payload.dependent_var_id

        if not x_id or not m_id or not y_id:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp đầy đủ x_question_id, m_question_id, y_question_id.")

        if len({x_id, m_id, y_id}) < 3:
            raise HTTPException(status_code=400, detail="Biến độc lập (X), trung gian (M) và phụ thuộc (Y) phải hoàn toàn phân biệt.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ? AND id IN (?, ?, ?)",
            (survey_id, x_id, m_id, y_id)
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}
        if x_id not in q_dict or m_id not in q_dict or y_id not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy các câu hỏi tương ứng trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Chưa có phản hồi nào trong khảo sát.",
                "sample_size": 0,
                "variables": {"x": q_dict.get(x_id, x_id), "m": q_dict.get(m_id, m_id), "y": q_dict.get(y_id, y_id)}
            }

        placeholders = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders}) AND question_id IN (?, ?, ?)
        """, resp_ids + [x_id, m_id, y_id]).fetchall()

        resp_map = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        x_data, m_data, y_data = [], [], []
        for rid in resp_ids:
            row_ans = resp_map.get(rid, {})
            if x_id in row_ans and m_id in row_ans and y_id in row_ans:
                try:
                    xv = float(row_ans[x_id])
                    mv = float(row_ans[m_id])
                    yv = float(row_ans[y_id])
                    x_data.append(xv)
                    m_data.append(mv)
                    y_data.append(yv)
                except (ValueError, TypeError):
                    continue

        if len(x_data) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(x_data)} phản hồi có dữ liệu hợp lệ cho cả 3 biến (yêu cầu tối thiểu 5).",
                "sample_size": len(x_data),
                "variables": {"x": q_dict.get(x_id, x_id), "m": q_dict.get(m_id, m_id), "y": q_dict.get(y_id, y_id)}
            }

        res = MediationEngine.analyze_mediation(
            x_data=x_data,
            m_data=m_data,
            y_data=y_data,
            x_label=q_dict[x_id],
            m_label=q_dict[m_id],
            y_label=q_dict[y_id],
            bootstrap_samples=payload.bootstrap_samples or payload.num_bootstrap or 1000
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MEDIATION_ANALYSIS_PERFORMED",
            details={
                "independent_var": q_dict[x_id],
                "mediator_var": q_dict[m_id],
                "dependent_var": q_dict[y_id],
                "sample_size": len(x_data),
                "mediation_type": res.get("sobel_test", {}).get("mediation_type"),
                "indirect_effect": res.get("paths", {}).get("indirect_effect_ab")
            }
        )

        return res


@router.post("/mann-whitney-u", response_model=MannWhitneyUOut)
def run_mann_whitney_u(survey_id: str, payload: MannWhitneyURequest):
    """
    Kiểm định U của Mann-Whitney (Wilcoxon Rank-Sum Test) cho 2 nhóm độc lập
    (Tương đương phi tham số của Independent Samples t-test khi dữ liệu ordinal/không chuẩn).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_id = payload.target_question_id
        g_id = payload.grouping_question_id

        if t_id == g_id:
            raise HTTPException(status_code=400, detail="Biến mục tiêu và biến phân nhóm không được trùng nhau.")

        q_rows = conn.execute(
            "SELECT id, title, question_type, options_json FROM questions WHERE survey_id = ? AND id IN (?, ?)",
            (survey_id, t_id, g_id)
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if t_id not in q_dict or g_id not in q_dict:
            raise HTTPException(status_code=400, detail="Một hoặc cả hai câu hỏi không tồn tại trong khảo sát.")

        # Lọc danh sách phản hồi theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không có dữ liệu phản hồi trong phạm vi được chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN (?, ?)
        """, (*resp_ids, t_id, g_id)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\\s*([0-9]+(?:\\.[0-9]+)?)\\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        grouped_data: Dict[str, List[float]] = {}
        for rid in resp_ids:
            a_dict = ans_by_resp[rid]
            val_t = parse_num(a_dict.get(t_id))
            raw_g = str(a_dict.get(g_id, "")).strip()

            if val_t is not None and raw_g != "":
                grouped_data.setdefault(raw_g, []).append(val_t)

        distinct_groups = list(grouped_data.keys())
        if len(distinct_groups) < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Biến phân nhóm chỉ có {len(distinct_groups)} nhóm dữ liệu hợp lệ. Cần tối thiểu 2 nhóm để so sánh."
            }

        g1_val = payload.group1_value or distinct_groups[0]
        g2_val = payload.group2_value or distinct_groups[1]

        data1 = grouped_data.get(g1_val, [])
        data2 = grouped_data.get(g2_val, [])

        if len(data1) < 2 or len(data2) < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Cần tối thiểu n >= 2 quan sát cho mỗi nhóm: '{g1_val}' có {len(data1)}, '{g2_val}' có {len(data2)}."
            }

        res = NonParametricEngine.mann_whitney_u_test(
            group1=data1,
            group2=data2,
            g1_name=g1_val,
            g2_name=g2_val
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MANN_WHITNEY_TEST_PERFORMED",
            details={
                "target_question": q_dict[t_id]["title"],
                "grouping_question": q_dict[g_id]["title"],
                "group1": g1_val,
                "group2": g2_val,
                "u_stat": res.get("statistics", {}).get("u_statistic"),
                "p_value": res.get("statistics", {}).get("p_value")
            }
        )

        return res


@router.post("/wilcoxon-signed-rank", response_model=WilcoxonSignedRankOut)
def run_wilcoxon_signed_rank(survey_id: str, payload: WilcoxonSignedRankRequest):
    """
    Kiểm định hạng có dấu Wilcoxon (Wilcoxon Signed-Rank Test) cho các cặp quan sát phụ thuộc.
    (Tương đương phi tham số của Paired Samples t-test khi dữ liệu không chuẩn hoặc thang đo thứ bậc).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q1_id = payload.question_id_1
        q2_id = payload.question_id_2

        if q1_id == q2_id:
            raise HTTPException(status_code=400, detail="Hai câu hỏi so sánh từng cặp không được trùng nhau.")

        q_rows = conn.execute(
            "SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN (?, ?)",
            (survey_id, q1_id, q2_id)
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if q1_id not in q_dict or q2_id not in q_dict:
            raise HTTPException(status_code=400, detail="Một hoặc cả hai câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không có dữ liệu phản hồi trong phạm vi được chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN (?, ?)
        """, (*resp_ids, q1_id, q2_id)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\\s*([0-9]+(?:\\.[0-9]+)?)\\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        sample1: List[float] = []
        sample2: List[float] = []

        for rid in resp_ids:
            a_dict = ans_by_resp[rid]
            val1 = parse_num(a_dict.get(q1_id))
            val2 = parse_num(a_dict.get(q2_id))

            if val1 is not None and val2 is not None:
                sample1.append(val1)
                sample2.append(val2)

        if len(sample1) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu N >= 5 cặp quan sát hợp lệ (hiện có N = {len(sample1)})."
            }

        res = NonParametricEngine.wilcoxon_signed_rank_test(
            sample1=sample1,
            sample2=sample2,
            s1_name=q_dict[q1_id]["title"],
            s2_name=q_dict[q2_id]["title"]
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="WILCOXON_TEST_PERFORMED",
            details={
                "question1": q_dict[q1_id]["title"],
                "question2": q_dict[q2_id]["title"],
                "n_pairs": len(sample1),
                "w_stat": res.get("statistics", {}).get("w_statistic"),
                "p_value": res.get("statistics", {}).get("p_value")
            }
        )

        return res


@router.post("/kruskal-wallis", response_model=KruskalWallisOut)
def run_kruskal_wallis(survey_id: str, payload: KruskalWallisRequest):
    """
    Kiểm định Kruskal-Wallis H (One-Way Non-Parametric ANOVA) cho k >= 2 nhóm độc lập,
    kèm so sánh cặp hậu nghiệm Dunn's Test hiệu chỉnh Bonferroni.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_id = payload.target_question_id
        g_id = payload.grouping_question_id

        if t_id == g_id:
            raise HTTPException(status_code=400, detail="Biến mục tiêu và biến phân nhóm không được trùng nhau.")

        q_rows = conn.execute(
            "SELECT id, title, question_type, options_json FROM questions WHERE survey_id = ? AND id IN (?, ?)",
            (survey_id, t_id, g_id)
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if t_id not in q_dict or g_id not in q_dict:
            raise HTTPException(status_code=400, detail="Một hoặc cả hai câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không có dữ liệu phản hồi trong phạm vi được chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN (?, ?)
        """, (*resp_ids, t_id, g_id)).fetchall()

        ans_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\\s*([0-9]+(?:\\.[0-9]+)?)\\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        grouped_data: Dict[str, List[float]] = {}
        for rid in resp_ids:
            a_dict = ans_by_resp[rid]
            val_t = parse_num(a_dict.get(t_id))
            raw_g = str(a_dict.get(g_id, "")).strip()

            if val_t is not None and raw_g != "":
                grouped_data.setdefault(raw_g, []).append(val_t)

        valid_groups = {g: vals for g, vals in grouped_data.items() if len(vals) >= 2}
        if len(valid_groups) < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Cần tối thiểu 2 nhóm có ít nhất 2 quan sát (hiện có {len(valid_groups)} nhóm thỏa mãn)."
            }

        res = NonParametricEngine.kruskal_wallis_h_test(valid_groups)

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="KRUSKAL_WALLIS_TEST_PERFORMED",
            details={
                "target_question": q_dict[t_id]["title"],
                "grouping_question": q_dict[g_id]["title"],
                "k_groups": len(valid_groups),
                "h_stat": res.get("statistics", {}).get("h_adjusted"),
                "p_value": res.get("statistics", {}).get("p_value")
            }
        )

        return res


@router.post("/missing-data-diagnostics", response_model=MissingDataDiagnosticsOut)
def get_missing_data_diagnostics(survey_id: str, req: MissingDataDiagnosticsRequest):
    """
    Khảo sát mô thức khuyết thiếu dữ liệu, tỷ lệ khuyết theo biến và theo dòng,
    nhận diện các tổ hợp mô thức (missing patterns), và kiểm định Little's MCAR Test (1988).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT id, title, question_type, options_json
            FROM questions WHERE survey_id = ?
            ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        if not q_rows:
            return {"status": "NO_QUESTIONS", "message": "Khảo sát chưa có câu hỏi nào."}

        # Xác định các câu hỏi tham gia phân tích
        if req.question_ids and len(req.question_ids) > 0:
            target_qs = [q for q in q_rows if q["id"] in req.question_ids]
        else:
            target_qs = [q for q in q_rows if q["question_type"] in ["number", "rating", "nps", "likert", "linear_scale"]]

        if len(target_qs) < 2:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": f"Cần tối thiểu 2 biến số định lượng để phân tích mô thức khuyết thiếu (hiện có {len(target_qs)} biến)."
            }

        q_ids = [q["id"] for q in target_qs]
        var_names = [q["title"] for q in target_qs]
        qid_to_name = {q["id"]: q["title"] for q in target_qs}

        # Lấy danh sách phản hồi theo phạm vi
        if req.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND (is_verified_clean = 1 OR status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 3:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 3 phản hồi để phân tích mô thức khuyết thiếu (hiện có {len(resp_rows)} phản hồi)."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join("?" for _ in resp_ids)
        q_placeholders = ",".join("?" for _ in q_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN ({q_placeholders})
        """, (*resp_ids, *q_ids)).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        data_matrix: List[Dict[str, Optional[float]]] = []
        for rid in resp_ids:
            row_dict = {}
            for q in target_qs:
                qid = q["id"]
                raw_val = ans_map[rid].get(qid)
                row_dict[q["title"]] = parse_num(raw_val)
            data_matrix.append(row_dict)

        res = MissingDataEngine.diagnose_missing_patterns(data_matrix, var_names)

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MISSING_DATA_DIAGNOSTICS_PERFORMED",
            details={
                "variables_count": len(var_names),
                "sample_size": len(resp_ids),
                "overall_missing_rate": res.get("overall_missing_rate"),
                "is_mcar": res.get("littles_mcar_test", {}).get("is_mcar")
            }
        )

        return res


@router.post("/missing-data-imputation", response_model=MissingDataImputationOut)
def run_missing_data_imputation(survey_id: str, req: MissingDataImputationRequest):
    """
    Thực hiện thuật toán bù khuyết dữ liệu đa phương pháp:
    - mean: Trung bình
    - median: Trung vị
    - hot_deck: Ghép cặp nhà tài trợ gần nhất (Nearest Neighbor Donor)
    - em: Kỳ vọng cực đại (Expectation-Maximization)
    - pmm: Predictive Mean Matching (khớp thang đo thực tế)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("""
            SELECT id, title, question_type, options_json
            FROM questions WHERE survey_id = ?
            ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        if not q_rows:
            return {"status": "NO_QUESTIONS", "message": "Khảo sát chưa có câu hỏi nào."}

        if req.question_ids and len(req.question_ids) > 0:
            target_qs = [q for q in q_rows if q["id"] in req.question_ids]
        else:
            target_qs = [q for q in q_rows if q["question_type"] in ["number", "rating", "nps", "likert", "linear_scale"]]

        if len(target_qs) < 2:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": f"Cần tối thiểu 2 biến số định lượng để thực hiện bù khuyết (hiện có {len(target_qs)} biến)."
            }

        q_ids = [q["id"] for q in target_qs]
        var_names = [q["title"] for q in target_qs]

        # Xác định bounds cho từng biến nếu có thang đo
        discrete_bounds: Dict[str, Tuple[float, float]] = {}
        for q in target_qs:
            qtype = q["question_type"]
            vname = q["title"]
            if qtype == "nps":
                discrete_bounds[vname] = (0.0, 10.0)
            elif qtype in ["rating", "likert"]:
                discrete_bounds[vname] = (1.0, 5.0)

        if req.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND (is_verified_clean = 1 OR status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 3:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 3 phản hồi để thực hiện bù khuyết (hiện có {len(resp_rows)} phản hồi)."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join("?" for _ in resp_ids)
        q_placeholders = ",".join("?" for _ in q_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN ({q_placeholders})
        """, (*resp_ids, *q_ids)).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        data_matrix: List[Dict[str, Optional[float]]] = []
        for rid in resp_ids:
            row_dict = {}
            for q in target_qs:
                qid = q["id"]
                raw_val = ans_map[rid].get(qid)
                row_dict[q["title"]] = parse_num(raw_val)
            data_matrix.append(row_dict)

        method = req.method or "em"
        res = MissingDataEngine.impute_missing_data(
            data_matrix,
            var_names,
            method=method,
            discrete_bounds=discrete_bounds
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MISSING_DATA_IMPUTATION_EXECUTED",
            details={
                "method": method,
                "variables_count": len(var_names),
                "sample_size": len(resp_ids),
                "imputed_cells_count": res.get("imputed_cells_count")
            }
        )

        return res


@router.post("/scale-equating", response_model=ScaleEquatingOut)
def run_scale_equating(survey_id: str, req: ScaleEquatingRequest):
    """
    Chuẩn hóa & Liên kết thang đo (Score Equating & Concordance Transformation):
    Thực hiện Linear Equating (Tucker / Levine) và Equipercentile Equating (Kolen & Brennan 2014),
    xây dựng bảng quy đổi tương đương (Concordance Table) giữa 2 câu hỏi/thang đo.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        src_id = req.source_question_id
        tgt_id = req.target_question_id

        if src_id == tgt_id:
            raise HTTPException(status_code=400, detail="Thang đo nguồn (X) và đích (Y) phải là hai câu hỏi khác nhau.")

        q_rows = conn.execute("""
            SELECT id, title, question_type, options_json
            FROM questions
            WHERE survey_id = ? AND id IN (?, ?)
        """, (survey_id, src_id, tgt_id)).fetchall()

        q_dict = {q["id"]: dict(q) for q in q_rows}
        if src_id not in q_dict or tgt_id not in q_dict:
            raise HTTPException(status_code=404, detail="Một trong hai câu hỏi thang đo không tồn tại trong khảo sát.")

        src_q = q_dict[src_id]
        tgt_q = q_dict[tgt_id]

        def get_bounds(q: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
            qtype = q.get("question_type")
            if qtype == "nps":
                return 0.0, 10.0
            elif qtype in ("rating", "likert"):
                return 1.0, 5.0
            return None, None

        x_min, x_max = get_bounds(src_q)
        y_min, y_max = get_bounds(tgt_q)

        # Lấy danh sách phản hồi theo phạm vi
        if req.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND (is_verified_clean = 1 OR status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 5 phản hồi để tính toán liên kết thang đo (hiện có {len(resp_rows)} phản hồi)."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN (?, ?)
        """, (*resp_ids, src_id, tgt_id)).fetchall()

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        x_vals: List[float] = []
        y_vals: List[float] = []

        for a in ans_rows:
            num = parse_num(a["answer_value"])
            if num is not None:
                if a["question_id"] == src_id:
                    x_vals.append(num)
                elif a["question_id"] == tgt_id:
                    y_vals.append(num)

        if len(x_vals) < 5 or len(y_vals) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 5 câu trả lời hợp lệ cho mỗi thang đo (hiện có X: {len(x_vals)}, Y: {len(y_vals)})."
            }

        res = EquatingEngine.equate_scales(
            x_values=x_vals,
            y_values=y_vals,
            x_label=src_q["title"],
            y_label=tgt_q["title"],
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SCALE_EQUATING_ANALYSIS_PERFORMED",
            details={
                "source_question": src_q["title"],
                "target_question": tgt_q["title"],
                "slope_alpha": res.get("linear_equating", {}).get("slope_alpha"),
                "intercept_beta": res.get("linear_equating", {}).get("intercept_beta"),
                "agreement_verdict": res.get("discrepancy_analysis", {}).get("agreement_verdict")
            }
        )

        return res


@router.post("/measurement-invariance", response_model=MeasurementInvarianceOut)
def run_measurement_invariance(survey_id: str, req: MeasurementInvarianceRequest):
    """
    Kiểm định Bất biến Đo lường Đa nhóm (Multi-Group Measurement Invariance Testing):
    Đánh giá 4 cấp bậc bất biến (Configural, Metric, Scalar, Strict Invariance)
    giữa các nhóm nhân khẩu học/sóng nghiên cứu theo tiêu chuẩn Cheung & Rensvold (2002) và Chen (2007).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        g_id = req.grouping_question_id
        item_ids = req.scale_question_ids

        if not item_ids or len(item_ids) < 2:
            raise HTTPException(status_code=400, detail="Cần chọn tối thiểu 2 câu hỏi chỉ báo để kiểm định bất biến thang đo.")

        if g_id in item_ids:
            raise HTTPException(status_code=400, detail="Biến phân nhóm không thể đồng thời là câu hỏi chỉ báo đo lường.")

        all_q_ids = [g_id] + item_ids
        placeholders_q = ",".join("?" for _ in all_q_ids)

        q_rows = conn.execute(f"""
            SELECT id, title, question_type, options_json
            FROM questions
            WHERE survey_id = ? AND id IN ({placeholders_q})
        """, (survey_id, *all_q_ids)).fetchall()

        q_dict = {q["id"]: dict(q) for q in q_rows}
        if g_id not in q_dict:
            raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi phân nhóm.")

        for iid in item_ids:
            if iid not in q_dict:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy câu hỏi chỉ báo: {iid}")

        g_q = q_dict[g_id]
        item_labels = [q_dict[iid]["title"] for iid in item_ids]

        # Lấy danh sách phản hồi theo phạm vi
        if req.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND (is_verified_clean = 1 OR status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để kiểm định bất biến đa nhóm (hiện có {len(resp_rows)} phản hồi)."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_q_ids)).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        grouped_data: Dict[str, List[List[float]]] = {}
        for rid in resp_ids:
            row_dict = ans_map[rid]
            raw_g = str(row_dict.get(g_id, "")).strip()
            if not raw_g:
                continue

            row_vals = []
            for iid in item_ids:
                val = parse_num(row_dict.get(iid))
                if val is not None:
                    row_vals.append(val)

            if len(row_vals) == len(item_ids):
                grouped_data.setdefault(raw_g, []).append(row_vals)

        # Lọc các nhóm có ít nhất 4 phản hồi hoàn chỉnh
        valid_groups = {g: rows for g, rows in grouped_data.items() if len(rows) >= 4}

        if len(valid_groups) < 2:
            return {
                "status": "INSUFFICIENT_GROUPS",
                "message": f"Cần tối thiểu 2 nhóm có ít nhất 4 quan sát hoàn chỉnh (hiện chỉ có {len(valid_groups)} nhóm thỏa mãn)."
            }

        res = MeasurementInvarianceEngine.evaluate_invariance(valid_groups, item_labels)

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MEASUREMENT_INVARIANCE_EVALUATED",
            details={
                "grouping_question": g_q["title"],
                "k_groups": res.get("k_groups"),
                "total_sample_size": res.get("total_sample_size"),
                "highest_level": res.get("highest_level_achieved")
            }
        )

        return res


@router.post("/common-method-bias", response_model=CommonMethodBiasOut)
def run_common_method_bias(survey_id: str, payload: CommonMethodBiasRequest):
    """
    Chẩn đoán Sai lệch Phương pháp Chung (Common Method Bias / Variance - CMB/CMV).
    Bao gồm:
    1. Harman's Single-Factor Test (ngưỡng 50.0%)
    2. Marker Variable Technique (Lindell & Whitney 2001)
    3. Unmeasured Latent Common Method Factor (ULMCF - Podsakoff et al. 2003)
    4. Cấp độ rủi ro (LOW, MODERATE, HIGH), khuyến nghị thủ tục/thống kê & đoạn trích APA 7th.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Xác định danh sách câu hỏi đo lường
        if payload.scale_question_ids and len(payload.scale_question_ids) > 0:
            scale_ids = list(payload.scale_question_ids)
        else:
            # Tự động tìm tất cả câu hỏi thang đo rating / likert / nps / number
            q_candidates = conn.execute("""
                SELECT id, title, question_type FROM questions
                WHERE survey_id = ?
                  AND question_type IN ('rating', 'likert', 'nps', 'number')
                ORDER BY order_index ASC
            """, (survey_id,)).fetchall()
            scale_ids = [q["id"] for q in q_candidates]

        if len(scale_ids) < 2:
            return {
                "status": "INSUFFICIENT_ITEMS",
                "message": f"Cần tối thiểu 2 câu hỏi dạng thang đo để chẩn đoán Common Method Bias (hiện có {len(scale_ids)} câu)."
            }

        all_needed_qids = list(scale_ids)
        if payload.marker_question_id and payload.marker_question_id not in all_needed_qids:
            all_needed_qids.append(payload.marker_question_id)

        # Lấy thông tin tiêu đề câu hỏi
        placeholders_q = ",".join("?" for _ in all_needed_qids)
        q_rows = conn.execute(f"""
            SELECT id, title, question_type FROM questions
            WHERE survey_id = ? AND id IN ({placeholders_q})
        """, (survey_id, *all_needed_qids)).fetchall()
        q_title_map = {q["id"]: q["title"] for q in q_rows}

        # Lọc danh sách phản hồi theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 4:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 4 phản hồi để chẩn đoán sai lệch phương pháp chung (hiện có {len(resp_rows)} phản hồi)."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_needed_qids)).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        data_rows: List[Dict[str, float]] = []
        for rid in resp_ids:
            row_dict = {}
            for qid in all_needed_qids:
                val = parse_num(ans_map[rid].get(qid))
                if val is not None:
                    row_dict[qid] = val
            if len(row_dict) >= len(scale_ids):
                data_rows.append(row_dict)

        if len(data_rows) < 4:
            return {
                "status": "INSUFFICIENT_COMPLETE_DATA",
                "message": f"Chỉ có {len(data_rows)} phản hồi điền đầy đủ các câu hỏi được chọn (cần tối thiểu 4)."
            }

        res = CMBEngine.comprehensive_diagnostic(
            data=data_rows,
            variables=scale_ids,
            marker_variable=payload.marker_question_id
        )

        res["status"] = "SUCCESS"

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="COMMON_METHOD_BIAS_DIAGNOSED",
            details={
                "items_count": len(scale_ids),
                "marker_question": q_title_map.get(payload.marker_question_id, payload.marker_question_id) if payload.marker_question_id else "AUTO",
                "overall_risk": res.get("overall_risk"),
                "harman_first_factor_pct": res.get("harman_test", {}).get("first_factor_variance_pct")
            }
        )

        return res


@router.post("/moderation", response_model=ModerationAnalysisOut)
def run_moderation_analysis(survey_id: str, payload: ModerationAnalysisRequest):
    """
    Phân tích Tác động Điều tiết & Hiệu ứng Tương tác (PROCESS Model 1 - Hayes 2018).
    Bao gồm:
    1. Chuẩn hóa Mean-Centering (Aiken & West 1991)
    2. Kiểm định gia tăng phương sai (Delta R^2 F-test) của số hạng tương tác X * W
    3. Phân tích độ dốc đơn (Simple Slopes: Low, Mean, High W)
    4. Kỹ thuật Johnson-Neyman xác định điểm chuyển tiếp ý nghĩa liên tục
    5. Tọa độ trực quan hóa đồ thị tương tác 2D và đoạn trích APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        x_id = payload.independent_question_id
        w_id = payload.moderator_question_id
        y_id = payload.dependent_question_id

        if len({x_id, w_id, y_id}) < 3:
            raise HTTPException(status_code=400, detail="Biến độc lập (X), biến điều tiết (W) và biến phụ thuộc (Y) phải là ba câu hỏi phân biệt.")

        q_rows = conn.execute(
            "SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN (?, ?, ?)",
            (survey_id, x_id, w_id, y_id)
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if x_id not in q_dict or w_id not in q_dict or y_id not in q_dict:
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong cuộc khảo sát.")

        # Lọc danh sách phản hồi theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để thực hiện phân tích điều tiết (hiện có {len(resp_rows)} phản hồi)."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp})
              AND question_id IN (?, ?, ?)
        """, (*resp_ids, x_id, w_id, y_id)).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        x_vals: List[float] = []
        w_vals: List[float] = []
        y_vals: List[float] = []

        for rid in resp_ids:
            row_dict = ans_map[rid]
            xv = parse_num(row_dict.get(x_id))
            wv = parse_num(row_dict.get(w_id))
            yv = parse_num(row_dict.get(y_id))

            if xv is not None and wv is not None and yv is not None:
                x_vals.append(xv)
                w_vals.append(wv)
                y_vals.append(yv)

        if len(x_vals) < 8:
            return {
                "status": "INSUFFICIENT_COMPLETE_DATA",
                "message": f"Chỉ có {len(x_vals)} phản hồi điền đầy đủ cả 3 biến (cần tối thiểu 8)."
            }

        res = ModerationEngine.analyze_moderation(
            x=x_vals,
            w=w_vals,
            y=y_vals,
            center_variables=payload.center_variables if payload.center_variables is not None else True,
            x_label=q_dict[x_id]["title"],
            w_label=q_dict[w_id]["title"],
            y_label=q_dict[y_id]["title"]
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MODERATION_ANALYSIS_EVALUATED",
            details={
                "independent_var": q_dict[x_id]["title"],
                "moderator_var": q_dict[w_id]["title"],
                "dependent_var": q_dict[y_id]["title"],
                "sample_size": len(x_vals),
                "is_significant": res.get("moderation_effect", {}).get("is_significant"),
                "delta_r2": res.get("moderation_effect", {}).get("delta_r_squared")
            }
        )

        return res


@router.post("/moderated-mediation", response_model=ModeratedMediationOut)
def run_moderated_mediation_analysis(survey_id: str, payload: ModeratedMediationRequest):
    """
    Phân tích Tác động Trung gian bị Điều tiết (Moderated Mediation - PROCESS Model 7; Hayes 2018).
    Bao gồm:
    1. Giai đoạn 1: M ~ X + W + X*W (Hiệu ứng trung gian bị điều tiết bởi W)
    2. Giai đoạn 2: Y ~ X + M (Tác động lên biến kết quả Y)
    3. Chỉ số Trung gian bị Điều tiết (Index of Moderated Mediation: omega = a3 * b; Hayes 2015)
    4. Tác động gián tiếp có điều kiện tại 3 mức W (Low, Mean, High W) qua tái lấy mẫu Bootstrap (95% CI)
    5. Đoạn trích APA 7th Edition hoàn chỉnh.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        x_id = payload.independent_question_id
        m_id = payload.mediator_question_id
        w_id = payload.moderator_question_id
        y_id = payload.dependent_question_id

        if len({x_id, m_id, w_id, y_id}) < 4:
            raise HTTPException(status_code=400, detail="Bốn biến X, M, W và Y phải là các câu hỏi hoàn toàn phân biệt.")

        q_rows = conn.execute(
            "SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN (?, ?, ?, ?)",
            (survey_id, x_id, m_id, w_id, y_id)
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if x_id not in q_dict or m_id not in q_dict or w_id not in q_dict or y_id not in q_dict:
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        # Lọc danh sách phản hồi theo scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi để phân tích Moderated Mediation (hiện có {len(resp_rows)} phản hồi)."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp})
              AND question_id IN (?, ?, ?, ?)
        """, (*resp_ids, x_id, m_id, w_id, y_id)).fetchall()

        ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            ans_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        x_vals: List[float] = []
        m_vals: List[float] = []
        w_vals: List[float] = []
        y_vals: List[float] = []

        for rid in resp_ids:
            row_dict = ans_map[rid]
            xv = parse_num(row_dict.get(x_id))
            mv = parse_num(row_dict.get(m_id))
            wv = parse_num(row_dict.get(w_id))
            yv = parse_num(row_dict.get(y_id))

            if xv is not None and mv is not None and wv is not None and yv is not None:
                x_vals.append(xv)
                m_vals.append(mv)
                w_vals.append(wv)
                y_vals.append(yv)

        if len(x_vals) < 10:
            return {
                "status": "INSUFFICIENT_COMPLETE_DATA",
                "message": f"Chỉ có {len(x_vals)} phản hồi điền đầy đủ cả 4 biến (cần tối thiểu 10)."
            }

        boot_count = min(1000, max(100, payload.num_bootstrap if payload.num_bootstrap else 500))

        res = ModeratedMediationEngine.analyze_moderated_mediation(
            x=x_vals,
            m=m_vals,
            w=w_vals,
            y=y_vals,
            center_variables=payload.center_variables if payload.center_variables is not None else True,
            num_bootstrap=boot_count,
            x_label=q_dict[x_id]["title"],
            m_label=q_dict[m_id]["title"],
            w_label=q_dict[w_id]["title"],
            y_label=q_dict[y_id]["title"]
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MODERATED_MEDIATION_EVALUATED",
            details={
                "independent_x": q_dict[x_id]["title"],
                "mediator_m": q_dict[m_id]["title"],
                "moderator_w": q_dict[w_id]["title"],
                "dependent_y": q_dict[y_id]["title"],
                "sample_size": len(x_vals),
                "index_omega": res.get("index_of_moderated_mediation", {}).get("index_omega"),
                "is_significant": res.get("index_of_moderated_mediation", {}).get("is_significant")
            }
        )

        return res


@router.post("/complex-sampling", response_model=ComplexSamplingOut)
def run_complex_sampling_analysis(survey_id: str, payload: ComplexSamplingRequest):
    """
    Phân tích Thiết Kế Mẫu Phức Hợp Hai Giai Đoạn (Two-Stage Cluster Sampling & Complex Design Weighting Engine).
    Ước lượng Trung bình có trọng số Horvitz-Thompson và Phương sai hiệu chỉnh qua Tuyến tính hóa chuỗi Taylor (Taylor Series Linearization).
    Tính toán Hiệu ứng thiết kế (DEFF, DEFT), Tương quan nội cụm (ICC / Kish's rho) và Cỡ mẫu hiệu dụng (Effective Sample Size n_eff).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_id = payload.target_question_id
        cluster_id = payload.cluster_question_id
        stratum_id = payload.stratum_question_id
        weight_id = payload.weight_question_id

        if target_id == cluster_id:
            raise HTTPException(status_code=400, detail="Biến mục tiêu Y và Biến cụm (PSU) không được trùng nhau.")

        needed_ids = [target_id, cluster_id]
        if stratum_id:
            needed_ids.append(stratum_id)
        if weight_id:
            needed_ids.append(weight_id)

        if len(needed_ids) != len(set(needed_ids)):
            raise HTTPException(status_code=400, detail="Các biến trong thiết kế mẫu phức hợp phải là các câu hỏi hoàn toàn phân biệt.")

        placeholders = ",".join("?" for _ in needed_ids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + needed_ids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if target_id not in q_dict or cluster_id not in q_dict:
            raise HTTPException(status_code=400, detail="Biến mục tiêu Y hoặc Biến cụm (PSU) không tồn tại trong khảo sát.")
        if stratum_id and stratum_id not in q_dict:
            raise HTTPException(status_code=400, detail="Biến phân tầng (Stratum) không tồn tại trong khảo sát.")
        if weight_id and weight_id not in q_dict:
            raise HTTPException(status_code=400, detail="Biến trọng số (Weight) không tồn tại trong khảo sát.")

        # Lấy danh sách phản hồi theo phạm vi
        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND (is_verified_clean = 1 OR review_status = 'verified_valid')",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND review_status != 'verified_fraud'",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Chưa có phản hồi nào phù hợp trong khảo sát này."
            }

        ans_rows = conn.execute(
            f"SELECT response_id, question_id, answer_value FROM response_answers WHERE question_id IN ({placeholders})",
            needed_ids
        ).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        records = []
        for rid in resp_ids:
            row_ans = resp_map.get(rid, {})
            y_str = row_ans.get(target_id)
            c_str = row_ans.get(cluster_id)
            if y_str is None or c_str is None:
                continue

            try:
                y_val = float(y_str)
            except (ValueError, TypeError):
                continue

            c_val = str(c_str).strip()
            if not c_val:
                continue

            s_val = str(row_ans.get(stratum_id, "Stratum_1")).strip() if stratum_id else "Stratum_1"
            w_val = 1.0
            if weight_id and weight_id in row_ans:
                try:
                    parsed_w = float(row_ans[weight_id])
                    if parsed_w > 0:
                        w_val = parsed_w
                except (ValueError, TypeError):
                    w_val = 1.0

            records.append({
                "target_val": y_val,
                "cluster_val": c_val,
                "stratum_val": s_val,
                "weight_val": w_val
            })

        if len(records) < 5:
            return {
                "status": "INSUFFICIENT_COMPLETE_DATA",
                "message": f"Chỉ có {len(records)} phản hồi có dữ liệu hợp lệ cho cả biến mục tiêu và biến cụm (yêu cầu tối thiểu 5)."
            }

        res = ComplexSamplingEngine.analyze_complex_design(
            records=records,
            target_title=q_dict[target_id]["title"],
            cluster_title=q_dict[cluster_id]["title"],
            stratum_title=q_dict[stratum_id]["title"] if stratum_id else None,
            weight_title=q_dict[weight_id]["title"] if weight_id else None
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="COMPLEX_SAMPLING_EVALUATED",
            details={
                "target_question": q_dict[target_id]["title"],
                "cluster_question": q_dict[cluster_id]["title"],
                "stratum_question": q_dict[stratum_id]["title"] if stratum_id else None,
                "sample_size": len(records),
                "deff": res.get("design_effects", {}).get("deff"),
                "icc": res.get("design_effects", {}).get("icc"),
                "effective_n": res.get("design_effects", {}).get("effective_sample_size")
            }
        )

        return res


@router.post("/propensity-matching", response_model=PSMAnalysisOut)
def run_propensity_matching_analysis(survey_id: str, payload: PSMAnalysisRequest):
    """
    Phân tích So khớp Điểm Xu hướng (Propensity Score Matching - PSM)
    và Nghịch đảo Xác suất Trọng số (Inverse Probability Weighting - IPW):
    - Đánh giá tác động can thiệp nhân quả (ATT - Average Treatment Effect on the Treated)
    - Mô hình hóa điểm xu hướng qua Hồi quy Logistic (Newton-Raphson/IRLS)
    - So khớp láng giềng gần nhất 1:1 không thay thế có chặn ngưỡng Caliper (Austin 2011)
    - Chẩn đoán cân bằng đồng biến (SMD < 0.10, Tỷ số phương sai VR, Love Plot)
    - Tự động sinh đoạn trích dẫn chuẩn APA 7th Edition và ghi nhận sổ cái SHA-256.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        treatment_id = payload.treatment_question_id
        outcome_id = payload.outcome_question_id
        cov_ids = payload.covariate_question_ids

        all_qids = [treatment_id, outcome_id] + cov_ids
        placeholders = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()

        q_dict = {q["id"]: {"title": q["title"], "type": q["question_type"]} for q in q_rows}
        if treatment_id not in q_dict or outcome_id not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi can thiệp hoặc kết quả.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return PSMEngine._build_empty_response(
                treatment_title=q_dict[treatment_id]["title"],
                outcome_title=q_dict[outcome_id]["title"],
                reason="Chưa có phản hồi nào trong khảo sát."
            )

        ans_rows = conn.execute(
            f"SELECT response_id, question_id, answer_value FROM response_answers WHERE question_id IN ({placeholders})",
            all_qids
        ).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        records = []
        treat_val_str = str(payload.treatment_value).strip().lower()
        for rid in resp_ids:
            ans = resp_map.get(rid, {})
            if treatment_id not in ans or outcome_id not in ans:
                continue

            raw_treat = str(ans[treatment_id]).strip().lower()
            is_treat = 1 if raw_treat == treat_val_str else 0

            try:
                outcome_val = float(ans[outcome_id])
            except (ValueError, TypeError):
                continue

            cov_vals = []
            has_all_covs = True
            for cid in cov_ids:
                if cid not in ans:
                    has_all_covs = False
                    break
                try:
                    cov_vals.append(float(ans[cid]))
                except (ValueError, TypeError):
                    has_all_covs = False
                    break

            if has_all_covs:
                records.append({
                    "id": rid,
                    "treatment": is_treat,
                    "outcome": outcome_val,
                    "covariates": cov_vals
                })

        cov_titles = [q_dict.get(cid, {}).get("title", cid) for cid in cov_ids]
        res = PSMEngine.analyze_propensity_matching(
            records=records,
            treatment_name=q_dict[treatment_id]["title"],
            outcome_name=q_dict[outcome_id]["title"],
            covariate_names=cov_titles,
            caliper_factor=payload.caliper_factor or 0.20
        )
        res["survey_id"] = survey_id

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="PROPENSITY_SCORE_MATCHING_EVALUATED",
            details={
                "treatment_question": q_dict[treatment_id]["title"],
                "outcome_question": q_dict[outcome_id]["title"],
                "sample_size": res.get("sample_size"),
                "matched_pairs": res.get("matched_pairs_count"),
                "att_matched": res.get("matched_att", {}).get("estimate"),
                "p_value": res.get("matched_att", {}).get("p_value")
            }
        )

        return res


@router.post("/topic-modeling", response_model=TopicModelAnalysisOut)
def run_topic_modeling_analysis(survey_id: str, payload: TopicModelAnalysisRequest):
    """
    Mô hình hóa Chủ đề Cấu trúc (Structural Topic Modeling - STM)
    và Phân bổ Dirichlet Tiềm ẩn (Latent Dirichlet Allocation - LDA) cho câu hỏi mở:
    - Thuật toán lấy mẫu Gibbs có điều kiện (Collapsed Gibbs Sampling; Griffiths & Steyvers 2004)
    - Tiền xử lý văn bản tiếng Việt chuyên sâu với từ ghép và từ dừng khảo sát
    - Đánh giá độ mạch lạc ngữ nghĩa UMass Topic Coherence (Mimno et al. 2011) và Exclusivity
    - Phân tích tương quan giữa biến kiểm soát và tỷ trọng chủ đề (Roberts et al. 2014)
    - Tự động biên soạn thuyết minh chuẩn APA 7th Edition và ghi nhận sổ cái SHA-256.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        text_qid = payload.text_question_id
        cov_qid = payload.covariate_question_id

        all_qids = [text_qid]
        if cov_qid:
            all_qids.append(cov_qid)

        placeholders = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()

        q_dict = {q["id"]: {"title": q["title"], "type": q["question_type"]} for q in q_rows}
        if text_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi văn bản trong khảo sát.")
        if cov_qid and cov_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến đồng biến trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return TopicModelingEngine._build_empty_response(reason="Chưa có phản hồi nào trong khảo sát.")

        ans_rows = conn.execute(
            f"SELECT response_id, question_id, answer_value FROM response_answers WHERE question_id IN ({placeholders})",
            all_qids
        ).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        documents = []
        for rid in resp_ids:
            ans = resp_map.get(rid, {})
            raw_text = ans.get(text_qid)
            if not raw_text or not str(raw_text).strip():
                continue

            cov_val = None
            if cov_qid and cov_qid in ans:
                try:
                    cov_val = float(ans[cov_qid])
                except (ValueError, TypeError):
                    cov_val = None

            documents.append({
                "id": rid,
                "text": str(raw_text).strip(),
                "covariate": cov_val
            })

        if len(documents) < 3:
            return TopicModelingEngine._build_empty_response(
                reason=f"Chỉ có {len(documents)} phản hồi chứa văn bản hợp lệ (yêu cầu tối thiểu 3)."
            )

        res = TopicModelingEngine.fit_lda_topic_model(
            documents=documents,
            num_topics=payload.num_topics or 3,
            num_iterations=payload.num_iterations or 60,
            random_seed=42
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="STRUCTURAL_TOPIC_MODEL_EVALUATED",
            details={
                "text_question": q_dict[text_qid]["title"],
                "covariate_question": q_dict.get(cov_qid, {}).get("title") if cov_qid else None,
                "sample_size": res.get("sample_size"),
                "topics_count": res.get("num_topics"),
                "mean_coherence_umass": res.get("mean_coherence_umass")
            }
        )

        return res


@router.post("/psychometric-network", response_model=PsychometricNetworkOut)
def run_psychometric_network_analysis(survey_id: str, payload: PsychometricNetworkRequest):
    """
    Phân tích Mạng Lưới Tâm lý học Đo lường (Psychometric Network Analysis)
    và Mô hình Đồ thị Gaussian (Gaussian Graphical Model - GGM; Epskamp et al. 2012, 2018):
    - Đảo ma trận hiệp phương sai mẫu thành ma trận chính xác Precision Matrix với điều chuẩn Ridge
    - Ước lượng ma trận tương quan riêng phần (Partial Correlation Matrix) và ngưỡng regularization
    - Tính toán các chỉ số trung tâm mạng lưới: Cường độ bậc (Strength), Tầm ảnh hưởng kỳ vọng (Expected Influence), Độ gần gũi (Closeness), Độ trung gian (Betweenness)
    - Thuật toán bố trí lực lò xo Fruchterman-Reingold (1991) tính toán tọa độ vector 2D phục vụ hiển thị SVG
    - Tự động sinh thuyết minh học thuật chuẩn APA 7th Edition và ghi nhận nhật ký kiểm toán SHA-256.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if payload.question_ids and len(payload.question_ids) > 0:
            placeholders = ",".join("?" for _ in payload.question_ids)
            q_rows = conn.execute(
                f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders}) ORDER BY order_index ASC",
                [survey_id] + payload.question_ids
            ).fetchall()
        else:
            q_rows = conn.execute("""
                SELECT id, title, question_type FROM questions
                WHERE survey_id = ? AND question_type IN ('number', 'rating', 'nps', 'likert', 'linear_scale')
                ORDER BY order_index ASC
            """, (survey_id,)).fetchall()

        if len(q_rows) < 3:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 3 câu hỏi định lượng để phân tích mạng lưới đồ thị.")

        q_ids = [q["id"] for q in q_rows]
        node_names = [q["title"] for q in q_rows]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if len(resp_ids) < 4:
            return PsychometricNetworkEngine._build_empty_response(
                reason=f"Cần tối thiểu 4 phản hồi để phân tích mạng lưới đồ thị (hiện có {len(resp_ids)})."
            )

        placeholders_resp = ",".join("?" for _ in resp_ids)
        placeholders_q = ",".join("?" for _ in q_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + q_ids).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        data_matrix = []
        for rid in resp_ids:
            row_dict = resp_map.get(rid, {})
            row_vals = []
            valid_row = True
            for qid in q_ids:
                if qid not in row_dict:
                    valid_row = False
                    break
                try:
                    row_vals.append(float(row_dict[qid]))
                except (ValueError, TypeError):
                    valid_row = False
                    break
            if valid_row:
                data_matrix.append(row_vals)

        if len(data_matrix) < 4:
            return PsychometricNetworkEngine._build_empty_response(
                reason=f"Chỉ có {len(data_matrix)} phản hồi hoàn chỉnh cho cả {len(q_ids)} biến (yêu cầu tối thiểu 4)."
            )

        res = PsychometricNetworkEngine.analyze_network(
            data_matrix=data_matrix,
            node_names=node_names,
            regularization_threshold=payload.regularization_threshold or 0.05
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="PSYCHOMETRIC_NETWORK_ANALYSIS_EVALUATED",
            details={
                "nodes_count": res.get("num_nodes"),
                "edges_count": res.get("num_edges"),
                "density": res.get("density"),
                "sample_size": res.get("sample_size"),
                "most_central_node": res.get("most_central_node")
            }
        )

        return res


@router.post("/irt-2pl", response_model=IRT2PLAnalysisOut)
def run_irt_2pl_analysis(survey_id: str, payload: IRT2PLAnalysisRequest):
    """
    Lý thuyết Ứng đáp Câu hỏi 2 Tham số Logistic (Item Response Theory - IRT 2PL)
    và Đường cong Đặc trưng Câu hỏi (Item Characteristic Curve - ICC; Birnbaum 1968, Reckase 2009):
    - Ước lượng độ phân biệt câu hỏi (a_i) và độ khó/ngưỡng ủng hộ (b_i) bằng thuật toán MML-EM
    - Đường cong ICC và Hàm thông tin câu hỏi (IIF) / Hàm thông tin bài test (TIF)
    - Đánh giá độ tin cậy biên thang đo (Marginal Reliability rho_IRT)
    - Ước lượng năng lực người làm bài (EAP Latent Trait Person Scoring)
    - Tự động sinh tọa độ vector SVG cho ICC và TIF, kèm thuyết minh học thuật APA 7th Edition.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if payload.question_ids and len(payload.question_ids) > 0:
            placeholders = ",".join("?" for _ in payload.question_ids)
            q_rows = conn.execute(
                f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders}) ORDER BY order_index ASC",
                [survey_id] + payload.question_ids
            ).fetchall()
        else:
            q_rows = conn.execute("""
                SELECT id, title, question_type FROM questions
                WHERE survey_id = ? AND question_type IN ('number', 'rating', 'nps', 'likert', 'linear_scale', 'single_choice', 'boolean')
                ORDER BY order_index ASC
            """, (survey_id,)).fetchall()

        if len(q_rows) < 2:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 2 câu hỏi để ước lượng mô hình IRT 2PL.")

        q_ids = [q["id"] for q in q_rows]
        item_names = [q["title"] for q in q_rows]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if len(resp_ids) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 6 phản hồi để ước lượng mô hình IRT 2PL (hiện có {len(resp_ids)})."
            }

        placeholders_resp = ",".join("?" for _ in resp_ids)
        placeholders_q = ",".join("?" for _ in q_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + q_ids).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        raw_matrix = []
        for rid in resp_ids:
            row_dict = resp_map.get(rid, {})
            row_vals = []
            valid_row = True
            for qid in q_ids:
                if qid not in row_dict:
                    valid_row = False
                    break
                val_str = str(row_dict[qid]).strip().lower()
                if val_str in ("true", "yes", "1", "đúng", "dong_y"):
                    row_vals.append(1.0)
                elif val_str in ("false", "no", "0", "sai", "khong"):
                    row_vals.append(0.0)
                else:
                    try:
                        row_vals.append(float(val_str))
                    except (ValueError, TypeError):
                        valid_row = False
                        break
            if valid_row:
                raw_matrix.append(row_vals)

        if len(raw_matrix) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(raw_matrix)} phản hồi hoàn chỉnh cho cả {len(q_ids)} câu hỏi (yêu cầu tối thiểu 6)."
            }

        res = IRT2PLEngine.analyze_irt_2pl(
            raw_matrix=raw_matrix,
            item_names=item_names,
            binarization_threshold=payload.binarization_threshold,
            max_em_iter=payload.max_em_iter or 35
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="IRT_2PL_MODEL_EVALUATED",
            details={
                "items_count": res.get("num_items"),
                "sample_size": res.get("sample_size"),
                "marginal_reliability": res.get("marginal_reliability"),
                "average_discrimination": res.get("average_discrimination"),
                "average_difficulty": res.get("average_difficulty")
            }
        )

        return res


@router.post("/survival-dropoff", response_model=SurvivalAnalysisOut)
def run_survival_dropoff_analysis(survey_id: str, payload: SurvivalAnalysisRequest):
    """
    Phân tích Sống sót & Thời gian Bỏ dở Khảo sát (Survival Analysis & Time-to-Drop-off Engine;
    Kaplan & Meier 1958, Cox 1972, Mantel 1966, Couper 2001):
    - Ước lượng hàm sống sót phi tham số Kaplan-Meier S(t) với sai số chuẩn Greenwood
    - Đánh giá tỷ lệ duy trì (retention) và tỷ lệ bỏ dở (drop-off) tại các mốc 1p, 3p, 5p, 10p
    - Kiểm định Log-Rank Mantel-Cox so sánh đường cong sống sót giữa 2 nhóm (Thiết bị, Nhân khẩu học)
    - Ước lượng Tỷ số nguy cơ Cox Hazard Ratio (HR) và khoảng tin cậy 95% CI
    - Tự động sinh tọa độ đồ thị hàm bậc thang vector SVG và đoạn thuyết minh chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        all_q_rows = conn.execute(
            "SELECT id, is_required FROM questions WHERE survey_id = ?",
            (survey_id,)
        ).fetchall()
        total_questions = len(all_q_rows)
        if total_questions == 0:
            raise HTTPException(status_code=400, detail="Khảo sát chưa có câu hỏi nào.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id, duration_seconds, client_metadata_json, review_status, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id, duration_seconds, client_metadata_json, review_status, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 5 phản hồi để phân tích đường cong sống sót (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join("?" for _ in resp_ids)

        ans_counts_rows = conn.execute(f"""
            SELECT response_id, COUNT(*) as cnt
            FROM response_answers
            WHERE response_id IN ({placeholders}) AND answer_value IS NOT NULL AND TRIM(answer_value) != ''
            GROUP BY response_id
        """, resp_ids).fetchall()
        ans_count_map = {row["response_id"]: row["cnt"] for row in ans_counts_rows}

        group_map = {}
        grouping_qid = payload.grouping_question_id
        if grouping_qid:
            grp_ans_rows = conn.execute(f"""
                SELECT response_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders}) AND question_id = ?
            """, resp_ids + [grouping_qid]).fetchall()
            for row in grp_ans_rows:
                group_map[row["response_id"]] = str(row["answer_value"]).strip()

        durations = []
        events = []
        group_labels = []

        for r in resp_rows:
            rid = r["id"]
            dur = max(5.0, float(r["duration_seconds"] or 0.0))
            ans_count = ans_count_map.get(rid, 0)
            is_screened_out = (r["review_status"] == "quota_screened_out")

            event = 1 if (ans_count < total_questions or is_screened_out) else 0

            durations.append(dur)
            events.append(event)

            if grouping_qid and rid in group_map and group_map[rid]:
                group_labels.append(group_map[rid])
            elif r["experimental_arm"]:
                group_labels.append(r["experimental_arm"])
            else:
                meta_str = (r["client_metadata_json"] or "").lower()
                if "mobile" in meta_str or "android" in meta_str or "iphone" in meta_str:
                    group_labels.append("Mobile")
                else:
                    group_labels.append("Desktop")

        res = SurvivalDropOffEngine.analyze_survival(
            durations=durations,
            events=events,
            group_labels=group_labels if len(set(group_labels)) >= 2 else None,
            time_milestones=payload.time_milestones
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SURVIVAL_ANALYSIS_EVALUATED",
            details={
                "total_participants": res.get("total_participants"),
                "drop_off_count": res.get("drop_off_count"),
                "completion_rate": res.get("overall_completion_rate"),
                "log_rank_p_value": res.get("log_rank_test", {}).get("p_value") if res.get("log_rank_test") else None
            }
        )

        return res


@router.post("/multilevel", response_model=MultilevelAnalysisOut)
def run_multilevel_analysis(survey_id: str, payload: MultilevelAnalysisRequest):
    """
    Phân tích Mô hình Tuyến tính Thứ bậc Đa cấp (Multilevel Modeling - MLM / HLM;
    Raudenbush & Bryk 2002, Snijders & Bosker 2012, Hox et al. 2017):
    - Khớp mô hình rỗng Unconditional Null Model phân rã phương sai và tính ICC
    - Ước lượng mô hình 2 tầng đầy đủ với hệ số chặn ngẫu nhiên (Random Intercepts) và độ dốc ngẫu nhiên (Random Slopes)
    - Co rút tham số Empirical Bayes (EB Shrinkage Estimates) hiệu chỉnh cỡ mẫu nhỏ của từng cụm/điều tra viên
    - Đánh giá tỷ lệ phương sai giải thích R^2 tầng 1 và tầng 2 theo Snijders & Bosker
    - Kiểm định tỷ số hợp lý LRT so sánh với hồi quy OLS gộp (-2LL Deviance Chi-Square)
    - Tự động sinh tọa độ đường quỹ đạo từng cụm vector SVG và đoạn thuyết minh chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        y_qid = payload.outcome_question_id
        x_qid = payload.predictor_question_id
        c_qid = payload.cluster_question_id

        all_qids = [y_qid]
        if x_qid:
            all_qids.append(x_qid)
        if c_qid:
            all_qids.append(c_qid)

        placeholders_q = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}

        if y_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến phụ thuộc (Y) trong khảo sát.")
        if x_qid and x_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến dự báo (X) trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id, enumerator_id, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id, enumerator_id, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để ước lượng mô hình đa cấp (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        resp_meta_map = {r["id"]: r for r in resp_rows}

        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + all_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            if y_qid not in ans:
                continue
            try:
                y_val = float(ans[y_qid])
            except (ValueError, TypeError):
                continue

            x_val = 0.0
            if x_qid:
                if x_qid not in ans:
                    continue
                try:
                    x_val = float(ans[x_qid])
                except (ValueError, TypeError):
                    continue

            # Xác định cluster ID
            cluster_id = None
            if c_qid and c_qid in ans and ans[c_qid]:
                cluster_id = str(ans[c_qid]).strip()
            elif resp_meta_map[rid]["enumerator_id"]:
                cluster_id = f"Enum_{resp_meta_map[rid]['enumerator_id']}"
            elif resp_meta_map[rid]["experimental_arm"]:
                cluster_id = f"Arm_{resp_meta_map[rid]['experimental_arm']}"
            else:
                cluster_id = f"Group_{len(data_rows) % 3 + 1}"

            row_dict = {
                "y": y_val,
                "cluster": cluster_id
            }
            if x_qid:
                row_dict["x"] = x_val
            data_rows.append(row_dict)

        if len(data_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi hợp lệ đầy đủ các biến (yêu cầu tối thiểu 8)."
            }

        res = MultilevelModelingEngine.fit_multilevel_model(
            data_rows=data_rows,
            y_var="y",
            x_var="x" if x_qid else None,
            cluster_var="cluster",
            centering=payload.centering or "grand_mean"
        )

        res["dependent_variable"] = q_dict[y_qid]
        res["predictor_variable"] = q_dict.get(x_qid) if x_qid else None
        res["cluster_variable"] = q_dict.get(c_qid, "Điều tra viên / Nhóm thực địa")

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MULTILEVEL_MODEL_EVALUATED",
            details={
                "outcome_question": q_dict[y_qid],
                "predictor_question": q_dict.get(x_qid),
                "num_clusters": res.get("num_clusters"),
                "sample_size": res.get("total_sample_size"),
                "icc": res.get("null_model", {}).get("icc"),
                "r2_level_1": res.get("random_effects", {}).get("r2_level_1")
            }
        )

        return res


@router.post("/conjoint", response_model=ConjointAnalysisOut)
def run_conjoint_analysis(survey_id: str, payload: ConjointAnalysisRequest):
    """
    Phân tích Đánh đổi Lựa chọn Choice-Based Conjoint (CBC / DCE; McFadden 1974, Green & Srinivasan 1990):
    - Ước lượng Tiện ích Từng phần (Part-Worth Utilities) theo chuẩn Effects Coding
    - Đánh giá Độ quan trọng Tương đối của các Thuộc tính (Attribute Relative Importance %)
    - Sẵn sàng Chi trả (Willingness to Pay - WTP; Hensher et al., 2005)
    - Trực quan hóa tỷ trọng thuộc tính và hồ sơ tiện ích vector SVG
    - Tự động sinh đoạn thuyết minh học thuật chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        rating_qid = payload.rating_question_id
        attr_qids = payload.attribute_question_ids
        price_qid = payload.price_question_id

        if len(attr_qids) < 2:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 2 câu hỏi thuộc tính để phân tích Conjoint.")

        all_qids = [rating_qid] + attr_qids
        if price_qid and price_qid not in all_qids:
            all_qids.append(price_qid)

        placeholders_q = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type, options_json FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + all_qids
        ).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        if rating_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đánh giá mức độ ưa thích (Rating).")

        for aq in attr_qids:
            if aq not in q_map:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi thuộc tính {aq} trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 6 phản hồi để phân tích Conjoint (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + all_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = a["answer_value"]

        # Xây dựng cấu hình attributes_config từ options_json của câu hỏi hoặc các giá trị xuất hiện
        attr_config: Dict[str, List[str]] = {}
        price_attr_title = None

        for aq_id in attr_qids:
            q_info = q_map[aq_id]
            title = q_info["title"]
            if aq_id == price_qid:
                price_attr_title = title

            # Trích xuất options_json nếu có
            levels: List[str] = []
            if q_info["options_json"]:
                try:
                    raw_opts = json.loads(q_info["options_json"]) if isinstance(q_info["options_json"], str) else q_info["options_json"]
                    levels = [str(opt).strip() for opt in raw_opts if str(opt).strip()]
                except Exception:
                    pass

            if not levels:
                # Tìm các giá trị trả lời duy nhất
                observed = set()
                for rid in resp_ids:
                    val = resp_ans.get(rid, {}).get(aq_id)
                    if val is not None and str(val).strip():
                        observed.add(str(val).strip())
                levels = sorted(list(observed))

            if len(levels) >= 2:
                attr_config[title] = levels

        if len(attr_config) < 2:
            return {
                "status": "INSUFFICIENT_ATTRIBUTES",
                "message": f"Cần tối thiểu 2 thuộc tính có từ 2 mức độ trở lên (hiện có {len(attr_config)})."
            }

        # Chuyển đổi dữ liệu từng phản hồi thành profiles_data
        profiles_data: List[Dict[str, Any]] = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            if rating_qid not in ans:
                continue
            try:
                r_val = float(ans[rating_qid])
            except (ValueError, TypeError):
                continue

            profile_entry = {"rating": r_val}
            complete = True
            for aq_id in attr_qids:
                q_title = q_map[aq_id]["title"]
                if aq_id not in ans or not str(ans[aq_id]).strip():
                    complete = False
                    break
                profile_entry[q_title] = str(ans[aq_id]).strip()

            if complete:
                profiles_data.append(profile_entry)

        res = ConjointAnalysisEngine.compute_conjoint_analysis(
            profiles_data=profiles_data,
            attributes_config=attr_config,
            rating_key="rating",
            price_attribute_name=price_attr_title
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONJOINT_MODEL_EVALUATED",
            details={
                "rating_question_id": rating_qid,
                "attributes_count": len(attr_config),
                "sample_size": res.get("sample_size", 0),
                "r2": res.get("model_fit", {}).get("r_squared")
            }
        )

        return res


@router.post("/conjoint-simulate", response_model=ConjointSimulationOut)
def run_conjoint_simulation(survey_id: str, payload: ConjointSimulationRequest):
    """
    Mô phỏng Thị phần Lựa chọn (Choice Share Market Simulator) theo mô hình Logit (McFadden 1974)
    cho danh sách các hồ sơ sản phẩm đối đầu.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        ana_req = ConjointAnalysisRequest(
            rating_question_id=payload.rating_question_id,
            attribute_question_ids=payload.attribute_question_ids,
            scope=payload.scope
        )
        ana_res = run_conjoint_analysis(survey_id, ana_req)
        if ana_res.get("status") != "SUCCESS":
            return {
                "status": "ERROR",
                "message": ana_res.get("message", "Không thể ước lượng tiện ích để mô phỏng thị phần.")
            }

        pw = ana_res.get("part_worth_utilities", {})
        intercept = ana_res.get("overall_utility_intercept", 0.0)

        shares = ConjointAnalysisEngine.simulate_choice_shares(
            part_worth_utilities=pw,
            intercept=intercept,
            candidate_profiles=payload.candidate_profiles
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONJOINT_SIMULATION_EVALUATED",
            details={
                "profiles_count": len(payload.candidate_profiles),
                "scope": payload.scope
            }
        )

        return {
            "status": "SUCCESS",
            "market_shares": shares
        }


@router.post("/lca", response_model=LCAAnalysisOut)
def run_lca_analysis(survey_id: str, payload: LCAAnalysisRequest):
    """
    Phân tích Lớp Ẩn (Latent Class Analysis - LCA; Goodman 1974, McLachlan & Peel 2000):
    - Thuật toán Expectation-Maximization (EM) phân đoạn người trả lời vào các lớp ẩn xác suất
    - Ước lượng tỷ lệ phân bố lớp ẩn (Class Prevalences) và xác suất phản hồi điều kiện (Item Probabilities)
    - So sánh tiêu chuẩn thông tin AIC, BIC, Sample-Adjusted BIC (SABIC) và Entropy để chọn K tối ưu
    - Trực quan hóa tọa độ song song Vector SVG Profile Plot
    - Tự động sinh đoạn thuyết minh học thuật chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        item_qids = payload.item_question_ids
        if len(item_qids) < 3:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 3 câu hỏi để phân tích Lớp Ẩn LCA.")

        placeholders_q = ",".join("?" for _ in item_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + item_qids
        ).fetchall()
        q_map = {q["id"]: q["title"] for q in q_rows}

        for qid in item_qids:
            if qid not in q_map:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi {qid} trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi để phân tích Lớp Ẩn LCA (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + item_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = str(a["answer_value"]).strip()

        # Dữ liệu dạng List[Dict[item_title, answer_value]]
        responses_data: List[Dict[str, str]] = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            row_dict = {}
            complete = True
            for qid in item_qids:
                if qid not in ans or not ans[qid]:
                    complete = False
                    break
                row_dict[q_map[qid]] = ans[qid]
            if complete:
                responses_data.append(row_dict)

        res = LatentClassAnalysisEngine.compute_lca(
            responses_data=responses_data,
            item_keys=[q_map[qid] for qid in item_qids],
            num_classes=payload.num_classes
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LCA_MODEL_EVALUATED",
            details={
                "items_count": len(item_qids),
                "optimal_classes": res.get("optimal_classes_count"),
                "sample_size": res.get("sample_size"),
                "entropy": res.get("entropy")
            }
        )

        return res


@router.post("/did", response_model=DiDAnalysisOut)
def run_did_analysis(survey_id: str, payload: DiDAnalysisRequest):
    """
    Phân tích Khác biệt trong Khác biệt (Difference-in-Differences - DiD / TWFE;
    Card & Krueger 1994, Angrist & Pischke 2009):
    - Đánh giá tác động nhân quả thuần túy (ATT) của can thiệp chính sách / khảo sát thử nghiệm
    - Bảng phân rã 2x2 Cell Means (Treatment vs Control qua 2 kỳ Pre vs Post)
    - Hồi quy OLS Hai chiều Cố định (TWFE) kiểm soát xu thế thời gian tự nhiên
    - Ước tính đường quỹ đạo phản thực tế (Counterfactual) theo giả định Xu hướng Song song
    - Trực quan hóa tọa độ Vector SVG và đoạn thuyết minh chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        y_qid = payload.outcome_question_id
        d_qid = payload.treatment_question_id
        t_qid = payload.time_question_id

        all_qids = [y_qid, d_qid, t_qid]
        placeholders_q = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + all_qids
        ).fetchall()
        q_map = {q["id"]: q["title"] for q in q_rows}

        if y_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (Y).")
        if d_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phân loại nhóm can thiệp (Treatment/Control).")
        if t_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phân loại thời điểm (Pre/Post).")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để ước lượng mô hình DiD (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + all_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = str(a["answer_value"]).strip()

        data_rows: List[Dict[str, Any]] = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            if y_qid not in ans or d_qid not in ans or t_qid not in ans:
                continue
            try:
                y_val = float(ans[y_qid])
            except (ValueError, TypeError):
                continue

            data_rows.append({
                "y": y_val,
                "treatment": ans[d_qid],
                "time": ans[t_qid]
            })

        res = DifferenceInDifferencesEngine.compute_did_analysis(
            data_rows=data_rows,
            outcome_key="y",
            treatment_key="treatment",
            time_key="time",
            treatment_value=payload.treatment_value,
            post_value=payload.post_value
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="DID_MODEL_EVALUATED",
            details={
                "outcome_question": q_map[y_qid],
                "treatment_question": q_map[d_qid],
                "time_question": q_map[t_qid],
                "att_estimate": res.get("did_treatment_effect", {}).get("att_estimate"),
                "sample_size": res.get("sample_size")
            }
        )

        return res


@router.post("/sem", response_model=SEMAnalysisOut)
def run_sem_analysis(survey_id: str, payload: SEMAnalysisRequest):
    """
    Mô hình Phương trình Cấu trúc & Phân tích Đường dẫn (Structural Equation Modeling - SEM / Path Analysis;
    Wright 1934, Jöreskog 1970, Hu & Bentler 1999, Kline 2015):
    - Ước lượng đồng thời các phương trình hồi quy cấu trúc nội sinh (Structural Regressions)
    - Hệ số đường dẫn chưa chuẩn hóa B, chuẩn hóa beta, sai số chuẩn SE, z-value, p-value, 95% CI
    - Phân rã tác động: Trực tiếp (Direct), Gián tiếp (Indirect/Mediation qua Sobel/Delta method), Tổng thể (Total)
    - Đánh giá độ phù hợp tổng thể (Global Fit): Chi-square, df, p, CFI, TLI, RMSEA (90% CI), SRMR
    - Trực quan hóa sơ đồ đường dẫn SVG đa tầng và báo cáo học thuật chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if not payload.paths:
            return {
                "status": "EMPTY_SPECIFICATION",
                "message": "Vui lòng chọn ít nhất một đường dẫn quan hệ giữa các biến."
            }

        q_rows = conn.execute("SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)).fetchall()
        q_map = {r["id"]: r["title"] for r in q_rows}

        resp_filter = "AND r.quality_status = 'verified_clean'" if payload.scope == "verified_clean" else ""
        resp_rows = conn.execute(f"""
            SELECT r.id
            FROM responses r
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if len(resp_rows) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi để ước lượng mô hình SEM (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp})
        """, resp_ids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            val = a["answer_value"]
            if val is not None:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = None
            by_resp[rid][a["question_id"]] = val

        data_rows = list(by_resp.values())
        paths_dict = [{"source": p.source, "target": p.target} for p in payload.paths]

        res = SEMEngine.fit_path_analysis(
            data_rows=data_rows,
            paths=paths_dict,
            labels=q_map
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SEM_MODEL_EVALUATED",
            details={
                "paths_count": len(payload.paths),
                "sample_size": res.get("sample_size"),
                "status": res.get("status"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/competing-risks", response_model=CompetingRisksAnalysisOut)
def run_competing_risks_analysis(survey_id: str, payload: CompetingRisksAnalysisRequest):
    """
    Phân tích Nguy cơ Cạnh tranh & Mô hình Suy yếu Chung (Competing Risks & Shared Frailty Survival Engine;
    Fine & Gray 1999, Hougaard 2000, Wienke 2010, Putter et al. 2007):
    - Ước lượng phi tham số Hàm Tích lũy Biến cố (Cumulative Incidence Function - CIF Aalen-Johansen)
    - Phân định các nguyên nhân kết thúc cạnh tranh loại trừ lẫn nhau (Bỏ cuộc, Quota screen-out, Loại trừ gian lận)
    - Lượng hóa độ lệch thổi phồng rủi ro của ước lượng Kaplan-Meier cổ điển (Naive KM Overestimation Bias)
    - Mô hình Suy yếu Chung Gamma (Shared Gamma Frailty) đánh giá tính không đồng nhất giữa các cụm điều tra viên / thiết bị
    - Kiểm định Tỉ số Hợp lý LRT (Self & Liang 1987) và ước lượng Bayes Thực nghiệm (Empirical Bayes)
    - Đồ họa Vector SVG đa đường cong CIF và đoạn thuyết minh chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        all_q_rows = conn.execute(
            "SELECT id, title, is_required FROM questions WHERE survey_id = ?",
            (survey_id,)
        ).fetchall()
        total_questions = len(all_q_rows)

        resp_filter = ""
        if payload.scope == "verified_clean":
            resp_filter = "AND review_status NOT IN ('verified_fraud', 'quota_screened_out') AND (risk_level != 'high' OR review_status = 'verified_valid')"

        resp_rows = conn.execute(f"""
            SELECT id, duration_seconds, review_status
            FROM responses
            WHERE survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để phân tích nguy cơ cạnh tranh và mô hình suy yếu (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join("?" for _ in resp_ids)

        ans_counts_rows = conn.execute(f"""
            SELECT response_id, COUNT(*) as cnt
            FROM response_answers
            WHERE response_id IN ({placeholders}) AND answer_value IS NOT NULL AND TRIM(answer_value) != ''
            GROUP BY response_id
        """, resp_ids).fetchall()
        ans_count_map = {row["response_id"]: row["cnt"] for row in ans_counts_rows}

        event_map = {}
        if payload.event_question_id:
            ev_ans_rows = conn.execute(f"""
                SELECT response_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders}) AND question_id = ?
            """, resp_ids + [payload.event_question_id]).fetchall()
            event_map = {row["response_id"]: str(row["answer_value"]).strip() for row in ev_ans_rows}

        cluster_map = {}
        if payload.cluster_question_id:
            c_ans_rows = conn.execute(f"""
                SELECT response_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders}) AND question_id = ?
            """, resp_ids + [payload.cluster_question_id]).fetchall()
            cluster_map = {row["response_id"]: str(row["answer_value"]).strip() for row in c_ans_rows}

        durations = []
        event_types = []
        cluster_ids = []

        for r in resp_rows:
            rid = r["id"]
            dur = max(5.0, float(r["duration_seconds"] or 60.0))
            durations.append(dur)

            if payload.event_question_id and rid in event_map:
                event_types.append(event_map[rid])
            else:
                st = r["review_status"]
                c_cnt = ans_count_map.get(rid, 0)
                if st == "quota_screened_out":
                    event_types.append("quota_screenout")
                elif st == "verified_fraud":
                    event_types.append("fraud_rejected")
                elif c_cnt < total_questions:
                    event_types.append("voluntary_dropoff")
                else:
                    event_types.append("completed")

            if payload.cluster_question_id and rid in cluster_map:
                cluster_ids.append(cluster_map[rid])
            else:
                cluster_ids.append("Default_Cluster")

        res = CompetingRisksFrailtyEngine.analyze_competing_risks_and_frailty(
            durations=durations,
            event_types=event_types,
            cluster_ids=cluster_ids if payload.cluster_question_id else None,
            time_milestones=payload.time_milestones
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="COMPETING_RISKS_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "competing_causes": res.get("competing_causes"),
                "clusters_count": res.get("shared_frailty_model", {}).get("clusters_count"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/irt-4pl", response_model=IRT4PLAnalysisOut)
def run_irt_4pl_analysis(survey_id: str, payload: IRT4PLAnalysisRequest):
    """
    Lý thuyết Ứng đáp Câu hỏi 3 & 4 Tham số Logistic (3PL & 4PL IRT Engine;
    Birnbaum 1968, Lord 1980, Barton & Lord 1981, Magis 2013):
    - Ước lượng độ phân biệt a_i, độ khó b_i, đoán mò c_i và đãng trí/bất cẩn d_i
    - Hàm Thông tin Câu hỏi (IIF) và Hàm Thông tin Bài trắc nghiệm (TIF)
    - Sai số đo lường chuẩn SE(theta) và độ tin cậy có điều kiện
    - Mô phỏng quy trình kiểm tra thích ứng máy tính (CAT Adaptive Testing)
    - Đồ họa Vector SVG đường cong ICC & TIF và đoạn thuyết minh chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if len(payload.question_ids) < 2:
            return {
                "status": "INSUFFICIENT_ITEMS",
                "message": "Cần chọn tối thiểu 2 câu hỏi để phân tích mô hình IRT 3PL/4PL."
            }

        placeholders_q = ",".join("?" for _ in payload.question_ids)
        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q}) AND survey_id = ?
        """, payload.question_ids + [survey_id]).fetchall()
        q_map = {r["id"]: r["title"] for r in q_rows}

        if len(q_map) < 2:
            return {
                "status": "INSUFFICIENT_ITEMS",
                "message": "Không tìm thấy đủ câu hỏi hợp lệ thuộc khảo sát này."
            }

        ordered_qids = [qid for qid in payload.question_ids if qid in q_map]
        item_names = [q_map[qid] for qid in ordered_qids]

        resp_filter = ""
        if payload.scope == "verified_clean":
            resp_filter = "AND review_status NOT IN ('verified_fraud', 'quota_screened_out') AND (risk_level != 'high' OR review_status = 'verified_valid')"

        resp_rows = conn.execute(f"""
            SELECT id
            FROM responses
            WHERE survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để ước lượng mô hình IRT 3PL/4PL (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + ordered_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            val = a["answer_value"]
            if val is not None:
                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    num_val = None
            else:
                num_val = None
            by_resp[rid][a["question_id"]] = num_val

        matrix = []
        for rid in resp_ids:
            row_dict = by_resp.get(rid, {})
            row_vals = []
            valid_row = True
            for qid in ordered_qids:
                v = row_dict.get(qid)
                if v is None:
                    valid_row = False
                    break
                row_vals.append(v)
            if valid_row:
                matrix.append(row_vals)

        if len(matrix) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(matrix)} người trả lời đầy đủ các câu hỏi được chọn (cần tối thiểu 8)."
            }

        res = IRT4PLEngine.fit_irt_4pl(
            raw_matrix=matrix,
            item_names=item_names,
            model_type=payload.model_type,
            binarization_threshold=payload.binarization_threshold
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="IRT_4PL_MODEL_EVALUATED",
            details={
                "items_count": len(ordered_qids),
                "model_type": payload.model_type.upper(),
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/ipw", response_model=IPWAnalysisOut)
def run_ipw_analysis(survey_id: str, payload: IPWAnalysisRequest):
    """
    Ước lượng tác động nhân quả qua Trọng số Xác suất Nghịch đảo (IPW) & Ước lượng Vững Kép (Doubly Robust / AIPW).
    (Rosenbaum & Rubin 1983; Robins et al. 1994; Lunceford & Davidian 2004; Austin & Stuart 2015)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        all_qids = [payload.treatment_question_id, payload.outcome_question_id] + payload.covariate_question_ids
        unique_qids = list(dict.fromkeys(all_qids))
        placeholders_q = ",".join("?" for _ in unique_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, unique_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.treatment_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi can thiệp (treatment).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi kết quả (outcome).")
        for cq in payload.covariate_question_ids:
            if cq not in labels:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy biến đồng biến: {cq}")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + unique_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            row_dict = {}
            t_val = ans_dict.get(payload.treatment_question_id)
            y_val = ans_dict.get(payload.outcome_question_id)
            if t_val is not None and y_val is not None:
                row_dict[payload.treatment_question_id] = t_val
                row_dict[payload.outcome_question_id] = y_val
                all_covs = True
                for cq in payload.covariate_question_ids:
                    cv = ans_dict.get(cq)
                    if cv is None:
                        all_covs = False
                        break
                    row_dict[cq] = cv
                if all_covs:
                    data_rows.append(row_dict)

        if len(data_rows) < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến can thiệp, kết quả và đồng biến (cần tối thiểu 16)."
            }

        res = IPWDoublyRobustEngine.estimate_causal_effects(
            data_rows=data_rows,
            treatment_key=payload.treatment_question_id,
            outcome_key=payload.outcome_question_id,
            covariate_keys=payload.covariate_question_ids,
            treatment_value=payload.treatment_value,
            weight_scheme=payload.weight_scheme,
            trim_weights=payload.trim_weights,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="IPW_DOUBLY_ROBUST_EVALUATED",
            details={
                "weight_scheme": payload.weight_scheme.upper(),
                "sample_size": res.get("sample_size"),
                "covariates_count": len(payload.covariate_question_ids),
                "scope": payload.scope
            }
        )

        return res


@router.post("/gam", response_model=GAMSplineAnalysisOut)
def run_gam_spline_analysis(survey_id: str, payload: GAMSplineAnalysisRequest):
    """
    Ước lượng Mô hình GAM & Hồi quy Spline Trơn (Generalized Additive Models & Natural Splines).
    (Hastie & Tibshirani 1990; Wood 2017; Green & Silverman 1994)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.predictor_question_id, payload.outcome_question_id]
        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.predictor_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến dự báo (predictor).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            xv = ans_dict.get(payload.predictor_question_id)
            yv = ans_dict.get(payload.outcome_question_id)
            if xv is not None and yv is not None:
                data_rows.append({
                    payload.predictor_question_id: xv,
                    payload.outcome_question_id: yv
                })

        if len(data_rows) < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến dự báo và kết quả (cần tối thiểu 16)."
            }

        res = GAMSplineEngine.fit_gam_spline(
            data_rows=data_rows,
            predictor_key=payload.predictor_question_id,
            outcome_key=payload.outcome_question_id,
            n_knots=payload.n_knots,
            smoothing_penalty=payload.smoothing_penalty,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="GAM_SPLINE_MODEL_EVALUATED",
            details={
                "n_knots": payload.n_knots,
                "smoothing_penalty": payload.smoothing_penalty,
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/quantile-regression", response_model=QuantileRegressionOut)
def run_quantile_regression_analysis(survey_id: str, payload: QuantileRegressionRequest):
    """
    Ước lượng Hồi quy Phân vị & Hiệu ứng Phân phối Có điều kiện (Quantile Regression & Distributional Effects).
    (Koenker & Bassett 1978; Koenker 2005; Angrist & Pischke 2009)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        cov_ids = payload.covariate_question_ids or []
        all_qids = [payload.predictor_question_id, payload.outcome_question_id] + cov_ids
        unique_qids = list(dict.fromkeys(all_qids))
        placeholders_q = ",".join("?" for _ in unique_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, unique_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.predictor_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến dự báo (predictor).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome).")
        for cq in cov_ids:
            if cq not in labels:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy biến đồng biến: {cq}")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + unique_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            xv = ans_dict.get(payload.predictor_question_id)
            yv = ans_dict.get(payload.outcome_question_id)
            if xv is not None and yv is not None:
                row_dict = {
                    payload.predictor_question_id: xv,
                    payload.outcome_question_id: yv
                }
                all_covs = True
                for cq in cov_ids:
                    cv = ans_dict.get(cq)
                    if cv is None:
                        all_covs = False
                        break
                    row_dict[cq] = cv
                if all_covs:
                    data_rows.append(row_dict)

        if len(data_rows) < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến dự báo, kết quả và đồng biến (cần tối thiểu 16)."
            }

        res = QuantileRegressionEngine.fit_quantile_regression(
            data_rows=data_rows,
            predictor_key=payload.predictor_question_id,
            outcome_key=payload.outcome_question_id,
            covariate_keys=cov_ids,
            quantiles=payload.quantiles,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="QUANTILE_REGRESSION_EVALUATED",
            details={
                "quantiles": payload.quantiles or [0.10, 0.25, 0.50, 0.75, 0.90],
                "sample_size": res.get("sample_size"),
                "covariates_count": len(cov_ids),
                "scope": payload.scope
            }
        )

        return res


@router.post("/g-theory", response_model=GTheoryAnalysisOut)
def run_g_theory_analysis(survey_id: str, payload: GTheoryAnalysisRequest):
    """
    Ước lượng Lý thuyết Khái quát hóa Đo lường (Generalizability Theory: G-Study & D-Study).
    (Cronbach et al. 1972; Brennan 2001; Shavelson & Webb 1991)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = list(dict.fromkeys(payload.item_question_ids))
        if payload.rater_question_id:
            target_qids.append(payload.rater_question_id)
            target_qids = list(dict.fromkeys(target_qids))

        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        for iq in payload.item_question_ids:
            if iq not in labels:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi đo lường: {iq}")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            row_dict = {"respondent_id": rid}
            all_valid = True
            for iq in payload.item_question_ids:
                v = ans_dict.get(iq)
                if v is None:
                    all_valid = False
                    break
                row_dict[iq] = v
            if payload.rater_question_id:
                rv = ans_dict.get(payload.rater_question_id)
                row_dict[payload.rater_question_id] = rv
            if all_valid:
                data_rows.append(row_dict)

        if len(data_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ các câu hỏi được chọn (cần tối thiểu 8)."
            }

        res = GTheoryEngine.run_g_study_two_facet(
            data_rows=data_rows,
            person_key="respondent_id",
            item_keys=payload.item_question_ids,
            rater_key=payload.rater_question_id,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="G_THEORY_MODEL_EVALUATED",
            details={
                "items_count": len(payload.item_question_ids),
                "has_rater": bool(payload.rater_question_id),
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/rdd", response_model=RDDAnalysisOut)
def run_rdd_analysis(survey_id: str, payload: RDDAnalysisRequest):
    """
    Ước lượng Thiết kế Gián đoạn Hồi quy Sắc nét (Sharp Regression Discontinuity Design / Sharp RDD).
    (Thistlethwaite & Campbell 1960; Hahn et al. 2001; Imbens & Kalyanaraman 2012; Calonico et al. 2014)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.running_question_id, payload.outcome_question_id]
        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.running_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến chỉ định (running variable).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            xv = ans_dict.get(payload.running_question_id)
            yv = ans_dict.get(payload.outcome_question_id)
            if xv is not None and yv is not None:
                data_rows.append({
                    payload.running_question_id: xv,
                    payload.outcome_question_id: yv
                })

        if len(data_rows) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến chỉ định và kết quả (cần tối thiểu 20)."
            }

        res = RDDEngine.fit_sharp_rdd(
            data_rows=data_rows,
            running_key=payload.running_question_id,
            outcome_key=payload.outcome_question_id,
            cutoff=payload.cutoff,
            bandwidth=payload.bandwidth,
            polynomial_order=payload.polynomial_order,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="RDD_MODEL_EVALUATED",
            details={
                "cutoff": payload.cutoff,
                "bandwidth": res.get("bandwidth"),
                "sample_size": res.get("sample_size"),
                "effective_sample_size": res.get("effective_sample_size"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/synthetic-control", response_model=SyntheticControlAnalysisOut)
def run_synthetic_control_analysis(survey_id: str, payload: SyntheticControlAnalysisRequest):
    """
    Ước lượng Phương pháp Kiểm chứng Tổng hợp (Synthetic Control Method - SCM).
    (Abadie and Gardeazabal 2003; Abadie, Diamond and Hainmueller 2010; Abadie 2021)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.unit_question_id, payload.period_question_id, payload.outcome_question_id]
        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.unit_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đơn vị (unit question).")
        if payload.period_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi chuỗi thời gian/kỳ (period question).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome question).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        panel_data = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            u_val = ans_dict.get(payload.unit_question_id)
            p_val = ans_dict.get(payload.period_question_id)
            y_val = ans_dict.get(payload.outcome_question_id)
            if u_val is not None and p_val is not None and y_val is not None:
                panel_data.append({
                    payload.unit_question_id: u_val,
                    payload.period_question_id: p_val,
                    payload.outcome_question_id: y_val
                })

        if len(panel_data) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(panel_data)} bản ghi dữ liệu hợp lệ (cần tối thiểu 6 bản ghi trên các đơn vị và kỳ)."
            }

        res = SyntheticControlEngine.fit_synthetic_control(
            panel_data=panel_data,
            unit_col=payload.unit_question_id,
            period_col=payload.period_question_id,
            outcome_col=payload.outcome_question_id,
            treated_unit=payload.treated_unit,
            treatment_period=payload.treatment_period
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SYNTHETIC_CONTROL_EVALUATED",
            details={
                "treated_unit": payload.treated_unit,
                "treatment_period": str(payload.treatment_period),
                "donor_pool_count": res.get("donor_pool_count"),
                "att_effect": res.get("att_effect"),
                "p_value": res.get("empirical_p_value"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/small-area-estimation", response_model=SmallAreaEstimationOut)
def run_small_area_estimation(survey_id: str, payload: SmallAreaEstimationRequest):
    """
    Ước lượng Mô hình Tiểu vùng Fay-Herriot & Empirical Bayes / EBLUP.
    (Fay & Herriot 1979; Rao & Molina 2015; Prasad & Rao 1990)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.area_question_id, payload.outcome_question_id]
        if payload.auxiliary_question_ids:
            for aqid in payload.auxiliary_question_ids:
                if aqid not in target_qids:
                    target_qids.append(aqid)

        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.area_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi định danh tiểu vùng (area question).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome question).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            a_val = ans_dict.get(payload.area_question_id)
            y_val = ans_dict.get(payload.outcome_question_id)
            if a_val is not None and y_val is not None:
                row_dict = {
                    payload.area_question_id: a_val,
                    payload.outcome_question_id: y_val
                }
                if payload.auxiliary_question_ids:
                    for aq in payload.auxiliary_question_ids:
                        row_dict[aq] = ans_dict.get(aq)
                data_rows.append(row_dict)

        if len(data_rows) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} bản ghi dữ liệu hợp lệ (cần tối thiểu 6 bản ghi trên các tiểu vùng)."
            }

        res = SmallAreaEstimationEngine.fit_fay_herriot(
            data_rows=data_rows,
            area_col=payload.area_question_id,
            outcome_col=payload.outcome_question_id,
            auxiliary_cols=payload.auxiliary_question_ids
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SMALL_AREA_ESTIMATION_EVALUATED",
            details={
                "area_count": res.get("area_count"),
                "between_area_variance": res.get("between_area_variance_sigma_v2"),
                "mean_shrinkage_gamma": res.get("mean_shrinkage_weight_gamma"),
                "mean_efficiency_gain_pct": res.get("mean_efficiency_gain_pct"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/event-study", response_model=EventStudyAnalysisOut)
def run_event_study_analysis(survey_id: str, payload: EventStudyAnalysisRequest):
    """
    Ước lượng Mô hình Nghiên cứu Sự kiện Động (Dynamic Event-Study / Staggered DiD).
    (Hausman & Rapson 2018; Sun & Abraham 2021; Callaway & Sant'Anna 2021)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.unit_question_id, payload.time_question_id, payload.outcome_question_id]
        if payload.event_time_question_id and payload.event_time_question_id not in target_qids:
            target_qids.append(payload.event_time_question_id)

        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.unit_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi định danh đơn vị (unit question).")
        if payload.time_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi mốc thời gian (time question).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome question).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        panel_data = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            u_val = ans_dict.get(payload.unit_question_id)
            t_val = ans_dict.get(payload.time_question_id)
            y_val = ans_dict.get(payload.outcome_question_id)
            if u_val is not None and t_val is not None and y_val is not None:
                row_dict = {
                    payload.unit_question_id: u_val,
                    payload.time_question_id: t_val,
                    payload.outcome_question_id: y_val
                }
                if payload.event_time_question_id:
                    row_dict[payload.event_time_question_id] = ans_dict.get(payload.event_time_question_id)
                panel_data.append(row_dict)

        if len(panel_data) < 12:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(panel_data)} bản ghi dữ liệu hợp lệ (cần tối thiểu 12 bản ghi trên các đơn vị và kỳ)."
            }

        res = DynamicEventStudyEngine.fit_event_study(
            panel_data=panel_data,
            unit_col=payload.unit_question_id,
            time_col=payload.time_question_id,
            outcome_col=payload.outcome_question_id,
            event_time_col=payload.event_time_question_id,
            treated_units=payload.treated_units,
            global_event_time=payload.global_event_time,
            max_leads=payload.max_leads,
            max_lags=payload.max_lags
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="EVENT_STUDY_EVALUATED",
            details={
                "units_count": res.get("units_count"),
                "periods_count": res.get("periods_count"),
                "pre_trend_wald_p": res.get("pre_trend_p_value"),
                "avg_post_effect": res.get("avg_post_treatment_effect"),
                "parallel_trends_supported": res.get("parallel_trends_supported"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/bsts-causal-impact", response_model=BSTSCausalImpactOut)
def run_bsts_causal_impact_analysis(survey_id: str, payload: BSTSCausalImpactRequest):
    """
    Ước lượng Tác động Nhân quả Chuỗi Thời gian Cấu trúc Bayes (BSTS / CausalImpact).
    (Brodersen, Gallusser, Koehler, Remy & Scott 2015; Harvey 1989)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.time_question_id, payload.outcome_question_id]
        if payload.covariate_question_ids:
            for cqid in payload.covariate_question_ids:
                if cqid not in target_qids:
                    target_qids.append(cqid)

        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.time_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi mốc thời gian (time question).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome question).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        series_data = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            t_val = ans_dict.get(payload.time_question_id)
            y_val = ans_dict.get(payload.outcome_question_id)
            if t_val is not None and y_val is not None:
                row_dict = {
                    payload.time_question_id: t_val,
                    payload.outcome_question_id: y_val
                }
                if payload.covariate_question_ids:
                    for cq in payload.covariate_question_ids:
                        row_dict[cq] = ans_dict.get(cq)
                series_data.append(row_dict)

        if len(series_data) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(series_data)} bản ghi dữ liệu hợp lệ (cần tối thiểu 5 bản ghi qua các mốc thời gian)."
            }

        res = BSTSCausalImpactEngine.fit_causal_impact(
            series_data=series_data,
            time_col=payload.time_question_id,
            outcome_col=payload.outcome_question_id,
            intervention_time=payload.intervention_time,
            covariate_cols=payload.covariate_question_ids
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="BSTS_CAUSAL_IMPACT_EVALUATED",
            details={
                "intervention_time": str(payload.intervention_time),
                "avg_pointwise_effect": res.get("avg_pointwise_effect"),
                "cumulative_effect": res.get("cumulative_effect"),
                "relative_effect_pct": res.get("relative_effect_pct"),
                "posterior_tail_p": res.get("posterior_tail_p_value"),
                "scope": payload.scope
            }
        )

        return res



@router.post("/aipw-cate", response_model=AIPWCATEOut)
def run_aipw_cate_analysis(survey_id: str, payload: AIPWCATERequest):
    """
    Ước lượng Tác động Can thiệp Kép Vững (Doubly Robust AIPW) &
    Phân tích Không đồng nhất CATE giữa các phân khúc (Robins et al. 1994, Chernozhukov et al. 2018).
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if not resp_rows:
            return {"status": "NO_DATA", "message": "Không có dữ liệu phản hồi trong phạm vi đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        target_qids = [payload.treatment_question_id, payload.outcome_question_id] + payload.confounder_question_ids
        if payload.subgroup_question_id:
            target_qids.append(payload.subgroup_question_id)
        target_qids = list(set(target_qids))

        placeholders_q = ",".join("?" for _ in target_qids)
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        W_list, Y_list, X_list, subgroups_list = [], [], [], []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            w_raw = ans_dict.get(payload.treatment_question_id)
            y_raw = ans_dict.get(payload.outcome_question_id)

            if w_raw is None or y_raw is None:
                continue

            try:
                y_val = float(y_raw)
            except (ValueError, TypeError):
                continue

            if payload.treatment_value is not None:
                w_val = 1.0 if str(w_raw).strip() == str(payload.treatment_value).strip() else 0.0
            else:
                try:
                    w_num = float(w_raw)
                    w_val = 1.0 if w_num > 0 else 0.0
                except (ValueError, TypeError):
                    w_str = str(w_raw).strip().lower()
                    w_val = 1.0 if w_str in ["1", "true", "yes", "có", "treated", "treatment"] else 0.0

            row_x = []
            has_all_x = True
            for cq in payload.confounder_question_ids:
                x_val = ans_dict.get(cq)
                try:
                    row_x.append(float(x_val))
                except (ValueError, TypeError):
                    has_all_x = False
                    break
            if not has_all_x or len(row_x) == 0:
                continue

            W_list.append(w_val)
            Y_list.append(y_val)
            X_list.append(row_x)

            if payload.subgroup_question_id:
                sub_val = ans_dict.get(payload.subgroup_question_id)
                subgroups_list.append(str(sub_val).strip() if sub_val is not None else "Unknown")

        if len(W_list) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(W_list)} phản hồi hợp lệ đầy đủ biến (cần tối thiểu 10 phản hồi)."
            }

        W_arr = np.array(W_list, dtype=float)
        Y_arr = np.array(Y_list, dtype=float)
        X_arr = np.array(X_list, dtype=float)
        sub_arg = subgroups_list if payload.subgroup_question_id and len(subgroups_list) == len(W_list) else None

        res = AIPWCATEEngine.estimate(
            W=W_arr,
            Y=Y_arr,
            X=X_arr,
            subgroups=sub_arg,
            trim_alpha=payload.trim_alpha if payload.trim_alpha is not None else 0.05
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="AIPW_CATE_EVALUATED",
            details={
                "ate": res.get("ate"),
                "se": res.get("se"),
                "z_stat": res.get("z_stat"),
                "p_value": res.get("p_value"),
                "is_significant": res.get("is_significant"),
                "is_heterogeneous": res.get("heterogeneity_test", {}).get("is_heterogeneous"),
                "effective_n": res.get("effective_sample_size"),
                "scope": payload.scope
            }
        )

        return res



@router.post("/iv-2sls", response_model=IV2SLSOut)
def run_iv_2sls_analysis(survey_id: str, payload: IV2SLSRequest):
    """
    Hồi quy Biến Công cụ Bình phương Tối thiểu Hai Giai đoạn (2SLS) &
    Kiểm định Biến Công cụ Yếu (Angrist & Imbens 1995, Stock & Yogo 2005).
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if not resp_rows:
            return {"status": "NO_DATA", "message": "Không có dữ liệu phản hồi trong phạm vi đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        target_qids = [payload.outcome_question_id, payload.endogenous_question_id] + payload.instrument_question_ids
        if payload.control_question_ids:
            target_qids += payload.control_question_ids
        target_qids = list(set(target_qids))

        placeholders_q = ",".join("?" for _ in target_qids)
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        Y_list, X_list, Z_list, W_list = [], [], [], []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            y_raw = ans_dict.get(payload.outcome_question_id)
            x_raw = ans_dict.get(payload.endogenous_question_id)

            if y_raw is None or x_raw is None:
                continue

            try:
                y_val = float(y_raw)
                x_val = float(x_raw)
            except (ValueError, TypeError):
                continue

            z_row = []
            has_all_z = True
            for zq in payload.instrument_question_ids:
                z_raw = ans_dict.get(zq)
                try:
                    z_row.append(float(z_raw))
                except (ValueError, TypeError):
                    has_all_z = False
                    break
            if not has_all_z or len(z_row) == 0:
                continue

            w_row = []
            if payload.control_question_ids:
                has_all_w = True
                for wq in payload.control_question_ids:
                    w_raw = ans_dict.get(wq)
                    try:
                        w_row.append(float(w_raw))
                    except (ValueError, TypeError):
                        has_all_w = False
                        break
                if not has_all_w:
                    continue

            Y_list.append(y_val)
            X_list.append(x_val)
            Z_list.append(z_row)
            if payload.control_question_ids:
                W_list.append(w_row)

        if len(Y_list) < 12:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(Y_list)} phản hồi hợp lệ đầy đủ biến (cần tối thiểu 12 phản hồi)."
            }

        Y_arr = np.array(Y_list, dtype=float)
        X_arr = np.array(X_list, dtype=float)
        Z_arr = np.array(Z_list, dtype=float)
        W_arr = np.array(W_list, dtype=float) if payload.control_question_ids and len(W_list) > 0 else None

        res = IV2SLSEngine.estimate(
            Y=Y_arr,
            X_endog=X_arr,
            Z_instruments=Z_arr,
            W_controls=W_arr
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="TWO_STAGE_LEAST_SQUARES_EVALUATED",
            details={
                "iv_beta": res.get("iv_estimate", {}).get("beta"),
                "iv_se": res.get("iv_estimate", {}).get("se"),
                "first_stage_f": res.get("first_stage_diagnostics", {}).get("f_statistic"),
                "is_weak_instrument": res.get("first_stage_diagnostics", {}).get("is_weak_instrument"),
                "wu_hausman_p": res.get("wu_hausman_test", {}).get("p_value"),
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res



@router.post("/bifactor", response_model=BifactorAnalysisOut)
def run_bifactor_analysis(survey_id: str, payload: BifactorAnalysisRequest):
    """
    Phân tích Mô hình Đo lường Phân rã Bifactor Trực giao &
    Kiểm định Tính Đơn chiều Thực chất (Reise 2012, Rodriguez et al. 2016).
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if not resp_rows:
            return {"status": "NO_DATA", "message": "Không có dữ liệu phản hồi trong phạm vi đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]

        all_item_qids = []
        subscale_assignments = {}
        for sub in payload.subscales:
            sub_indices = []
            for qid in sub.question_ids:
                if qid not in all_item_qids:
                    all_item_qids.append(qid)
                sub_indices.append(all_item_qids.index(qid))
            subscale_assignments[sub.subscale_name] = sub_indices

        if len(all_item_qids) < 4:
            return {"status": "INSUFFICIENT_ITEMS", "message": "Cần tối thiểu 4 câu hỏi để phân tích Bifactor."}

        placeholders_q = ",".join("?" for _ in all_item_qids)
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + all_item_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        q_meta_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, all_item_qids).fetchall()
        title_map = {q["id"]: q["title"] for q in q_meta_rows}
        item_labels = [title_map.get(qid, qid[:12]) for qid in all_item_qids]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            row = []
            has_all = True
            for qid in all_item_qids:
                v = ans_dict.get(qid)
                try:
                    row.append(float(v))
                except (ValueError, TypeError):
                    has_all = False
                    break
            if has_all:
                data_rows.append(row)

        if len(data_rows) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi hợp lệ đầy đủ các mục (cần tối thiểu 15 phản hồi)."
            }

        data_matrix = np.array(data_rows, dtype=float)

        res = BifactorEngine.estimate(
            data=data_matrix,
            subscale_assignments=subscale_assignments,
            item_labels=item_labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="BIFACTOR_MODEL_EVALUATED",
            details={
                "omega_total": res.get("omega_total"),
                "omega_hierarchical": res.get("omega_hierarchical"),
                "ecv": res.get("explained_common_variance"),
                "puc": res.get("percent_uncontaminated_correlations"),
                "is_essentially_unidimensional": res.get("is_essentially_unidimensional"),
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res



@router.post("/panel-var", response_model=PanelVAROut)
def run_panel_var_analysis(survey_id: str, payload: PanelVARRequest):
    """
    Ước lượng Mô hình Tự hồi quy Vector Dữ liệu Bảng (Panel VAR) &
    Kiểm định Nhân quả Động Granger (Holtz-Eakin et al. 1988, Abrigo & Love 2016).
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if not resp_rows:
            return {"status": "NO_DATA", "message": "Không có dữ liệu phản hồi trong phạm vi đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        target_qids = [payload.unit_question_id, payload.time_question_id, payload.var1_question_id, payload.var2_question_id]
        placeholders_q = ",".join("?" for _ in target_qids)
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        q_meta_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()
        title_map = {q["id"]: q["title"] for q in q_meta_rows}
        v1_name = title_map.get(payload.var1_question_id, "Biến 1")
        v2_name = title_map.get(payload.var2_question_id, "Biến 2")

        panel_records = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            u_val = ans_dict.get(payload.unit_question_id)
            t_val = ans_dict.get(payload.time_question_id)
            v1_val = ans_dict.get(payload.var1_question_id)
            v2_val = ans_dict.get(payload.var2_question_id)

            if u_val is not None and t_val is not None and v1_val is not None and v2_val is not None:
                panel_records.append({
                    "unit": str(u_val).strip(),
                    "time": t_val,
                    v1_name: v1_val,
                    v2_name: v2_val
                })

        if len(panel_records) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(panel_records)} bản ghi dữ liệu bảng hợp lệ (cần tối thiểu 15 bản ghi)."
            }

        res = PanelVAREngine.estimate(
            panel_rows=panel_records,
            unit_col="unit",
            time_col="time",
            var1_col=v1_name,
            var2_col=v2_name,
            lags=payload.lags or 1,
            irf_horizons=payload.irf_horizons or 6
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="PANEL_VAR_EVALUATED",
            details={
                "is_stable": res.get("is_stable"),
                "stability_max_modulus": res.get("stability_max_modulus"),
                "causality_conclusion": res.get("causality_conclusion"),
                "wald_1_to_2": res.get("granger_causality", {}).get("var1_causes_var2", {}).get("wald_chi2"),
                "wald_2_to_1": res.get("granger_causality", {}).get("var2_causes_var1", {}).get("wald_chi2"),
                "panel_units": res.get("panel_units_count"),
                "effective_n": res.get("effective_observations"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/latent-growth", response_model=LatentGrowthOut)
def run_latent_growth_analysis(survey_id: str, payload: LatentGrowthRequest):
    """
    Phan tich Mo hinh Quy dao Tang truong Tiem an (Latent Growth Curve Modeling - LGCM):
    - Danh gia su bien thien ca nhan ve diem khoi dau (Intercept) va toc do tang truong (Slope).
    - Do luong tuong quan giua muc do ban dau va gia toc cai thien (Intercept-Slope Covariance).
    - Danh gia do phu hop mo hinh cau truc tuyen tinh: Chi-Square, CFI, TLI, RMSEA.
    - Ve bieu do quy dao ca nhan (spaghetti plot) va duong xu the ky vong dan so voi khoang tin cay 95%.
    - Dien giai ket qua hoc thuat chuan APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Khong tim thay cuoc khao sat.")

        if not payload.wave_question_ids or len(payload.wave_question_ids) < 3:
            raise HTTPException(status_code=400, detail="Can toi thieu 3 cau hoi dai dien cho cac dot/lan song (waves).")

        if payload.scope == "verified_clean":
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if len(r_rows) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"So luong phan hoi hoan thanh ({len(r_rows)}) khong du dieu kien (toi thieu 15 phan hoi)."
            }

        resp_ids = [r["id"] for r in r_rows]
        placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(payload.wave_question_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders})
              AND question_id IN ({q_placeholders})
        """, (*resp_ids, *payload.wave_question_ids)).fetchall()

        by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_val(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        clean_matrix = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            row = []
            has_missing = False
            for qid in payload.wave_question_ids:
                val = parse_val(ans_dict.get(qid))
                if val is None:
                    has_missing = True
                    break
                row.append(val)
            if not has_missing:
                clean_matrix.append(row)

        if len(clean_matrix) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chi co {len(clean_matrix)} nguoi tham gia co cau tra loi day du o moi lan song (can toi thieu 15 nguoi)."
            }

        wave_array = np.array(clean_matrix, dtype=float)

        res = LatentGrowthEngine.estimate(
            wave_data=wave_array,
            time_scores=payload.time_scores,
            wave_labels=payload.wave_labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LATENT_GROWTH_MODEL_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "waves_count": res.get("waves_count"),
                "intercept_mean": res.get("latent_means", {}).get("intercept_mean"),
                "slope_mean": res.get("latent_means", {}).get("slope_mean"),
                "intercept_slope_corr": res.get("latent_variances", {}).get("intercept_slope_correlation"),
                "cfi": res.get("model_fit", {}).get("cfi"),
                "rmsea": res.get("model_fit", {}).get("rmsea"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/qte", response_model=QTEOut)
def run_quantile_treatment_effects(survey_id: str, payload: QTERequest):
    """
    Phân tích Hiệu ứng Can thiệp Lượng vị Bán tham số (Quantile Treatment Effects - QTE; Firpo 2007):
    - Đánh giá tác động của can thiệp/chính sách trên các phân vị khác nhau của biến kết quả (q = 0.10 đến 0.90).
    - So sánh với Hiệu ứng Can thiệp Trung bình (ATE) nhằm phát hiện tính không đồng nhất phân phối.
    - Định lượng tác động bất bình đẳng: Chênh lệch khoảng liên tứ phân vị Delta IQR và khoảng cách đuôi Delta (90-10).
    - Trực quan hóa đường cong QTE kèm dải tin cậy 95% và hàm phân phối tích lũy CDF nhóm can thiệp vs đối chứng.
    - Diễn giải học thuật tự động chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        if payload.scope == "verified_clean":
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if len(r_rows) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi hoàn thành ({len(r_rows)}) không đủ điều kiện (tối thiểu 20 phản hồi)."
            }

        resp_ids = [r["id"] for r in r_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        cov_ids = payload.covariate_question_ids or []
        all_qids = [payload.outcome_question_id, payload.treatment_question_id] + cov_ids
        placeholders_q = ",".join(["?"] * len(all_qids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_float(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        def parse_binary(v: Any) -> Optional[int]:
            if v is None or v == "":
                return None
            s = str(v).strip().lower()
            if s in ["1", "true", "yes", "co", "có", "tham gia", "treated", "can thiệp"]:
                return 1
            if s in ["0", "false", "no", "khong", "không", "chưa", "control", "đối chứng"]:
                return 0
            pf = parse_float(v)
            if pf is not None:
                return 1 if pf >= 1.0 else 0
            return None

        outcomes_list = []
        treatments_list = []
        covariates_list = []

        for rid in resp_ids:
            ans = by_resp.get(rid, {})
            y_val = parse_float(ans.get(payload.outcome_question_id))
            d_val = parse_binary(ans.get(payload.treatment_question_id))

            if y_val is None or d_val is None:
                continue

            cov_row = []
            has_missing_cov = False
            for cid in cov_ids:
                cv = parse_float(ans.get(cid))
                if cv is None:
                    has_missing_cov = True
                    break
                cov_row.append(cv)

            if has_missing_cov:
                continue

            outcomes_list.append(y_val)
            treatments_list.append(d_val)
            covariates_list.append(cov_row)

        if len(outcomes_list) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(outcomes_list)} phản hồi hợp lệ đồng thời về biến kết quả và can thiệp (cần tối thiểu 20)."
            }

        Y_arr = np.array(outcomes_list, dtype=float)
        D_arr = np.array(treatments_list, dtype=int)
        X_arr = np.array(covariates_list, dtype=float) if len(cov_ids) > 0 else None

        res = QTEEngine.estimate(
            outcomes=Y_arr,
            treatment=D_arr,
            covariates=X_arr,
            quantiles=payload.quantiles,
            alpha_trim=payload.alpha_trim or 0.05
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="QUANTILE_TREATMENT_EFFECTS_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "ate": res.get("average_treatment_effect"),
                "median_qte": res.get("median_treatment_effect"),
                "delta_iqr": res.get("delta_iqr_effect"),
                "inequality_impact": res.get("inequality_impact"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/causal-dag", response_model=CausalDAGOut)
def run_causal_dag_discovery(survey_id: str, payload: CausalDAGRequest):
    """
    Suy diễn Đồ thị Nhân quả Có hướng (Causal DAG / CPDAG) qua Thuật toán PC:
    - Tìm kiếm khung xương mạng lưới qua các kiểm định độc lập có điều kiện Fisher z.
    - Nhận diện các cấu trúc v-structure (colliders: X -> Z <- Y).
    - Định hướng các cạnh nhân quả bằng quy tắc Meek (1995) để đảm bảo tính phi chu trình (Acyclic).
    - Phân loại thứ bậc nhân quả: Nguyên nhân gốc (Root causes), Biến trung gian (Mediators), Kết quả hạ nguồn (Sink outcomes).
    - Trực quan hóa vector SVG mạng lưới nhân quả có hướng và xuất diễn giải chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        if not payload.question_ids or len(payload.question_ids) < 3:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 3 câu hỏi để suy diễn cấu trúc mạng lưới nhân quả DAG.")

        if payload.scope == "verified_clean":
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if len(r_rows) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi hoàn thành ({len(r_rows)}) không đủ điều kiện (tối thiểu 20 phản hồi)."
            }

        resp_ids = [r["id"] for r in r_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))
        placeholders_q = ",".join(["?"] * len(payload.question_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *payload.question_ids)).fetchall()

        by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        # Fetch question titles
        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, tuple(payload.question_ids)).fetchall()
        title_map = {q["id"]: q["title"] for q in q_rows}
        item_names = [title_map.get(qid, f"Item {idx+1}") for idx, qid in enumerate(payload.question_ids)]

        import re
        def parse_float(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        clean_matrix = []
        for rid in resp_ids:
            ans = by_resp.get(rid, {})
            row = []
            has_missing = False
            for qid in payload.question_ids:
                val = parse_float(ans.get(qid))
                if val is None:
                    has_missing = True
                    break
                row.append(val)
            if not has_missing:
                clean_matrix.append(row)

        if len(clean_matrix) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(clean_matrix)} người tham gia có câu trả lời đầy đủ ở mọi câu hỏi (cần tối thiểu 20 người)."
            }

        data_arr = np.array(clean_matrix, dtype=float)

        res = CausalDAGEngine.estimate(
            data=data_arr,
            item_names=item_names,
            alpha=payload.alpha or 0.05,
            max_cond_size=payload.max_cond_size or 2
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CAUSAL_DAG_DISCOVERY_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "variables_count": res.get("variables_count"),
                "edges_count": res.get("edges_count"),
                "directed_edges_count": res.get("directed_edges_count"),
                "root_causes_count": len(res.get("root_causes", [])),
                "sink_outcomes_count": len(res.get("sink_outcomes", [])),
                "scope": payload.scope
            }
        )

        return res


@router.post("/msm-iptw", response_model=MSMAnalysisOut)
def run_marginal_structural_model(survey_id: str, payload: MSMAnalysisRequest):
    """
    Ước lượng Mô hình Cấu trúc Biên (Marginal Structural Model - MSM) qua Trọng số Ổn định IPTW:
    - Giải quyết hiện tượng nhiễu biến thiên theo thời gian (time-varying confounding) trong khảo sát dọc đa đợt.
    - Ước lượng trọng số ổn định SW(t) từng đợt để loại bỏ thiên lệch chia tầng collider.
    - So sánh với hồi quy OLS ngây thơ nhằm lượng hóa phần trăm thiên lệch confounding.
    - Xuất biểu đồ phân phối trọng số ổn định và đường cong đáp ứng liều tích lũy với khoảng tin cậy 95%.
    - Diễn giải học thuật tự động chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        if len(payload.treatment_question_ids) < 2 or len(payload.treatment_question_ids) != len(payload.confounder_question_ids):
            raise HTTPException(status_code=400, detail="Cần tối thiểu 2 đợt khảo sát và số câu hỏi can thiệp phải bằng số câu hỏi biến nhiễu.")

        if payload.scope == "verified_clean":
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if len(r_rows) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi hoàn thành ({len(r_rows)}) không đủ điều kiện (tối thiểu 25 phản hồi)."
            }

        resp_ids = [r["id"] for r in r_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        all_qids = payload.treatment_question_ids + payload.confounder_question_ids + [payload.outcome_question_id]
        placeholders_q = ",".join(["?"] * len(all_qids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_float(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        def parse_binary(v: Any) -> Optional[int]:
            if v is None or v == "":
                return None
            s = str(v).strip().lower()
            if s in ["1", "true", "yes", "co", "có", "tham gia", "treated", "can thiệp"]:
                return 1
            if s in ["0", "false", "no", "khong", "không", "chưa", "control", "đối chứng"]:
                return 0
            pf = parse_float(v)
            if pf is not None:
                return 1 if pf >= 1.0 else 0
            return None

        clean_treats = []
        clean_confs = []
        clean_outcomes = []

        T = len(payload.treatment_question_ids)

        for rid in resp_ids:
            ans = by_resp.get(rid, {})
            y_val = parse_float(ans.get(payload.outcome_question_id))
            if y_val is None:
                continue

            has_missing = False
            t_row = []
            c_row = []
            for t_idx in range(T):
                t_qid = payload.treatment_question_ids[t_idx]
                c_qid = payload.confounder_question_ids[t_idx]
                a_val = parse_binary(ans.get(t_qid))
                c_val = parse_float(ans.get(c_qid))
                if a_val is None or c_val is None:
                    has_missing = True
                    break
                t_row.append(a_val)
                c_row.append(c_val)

            if not has_missing:
                clean_treats.append(t_row)
                clean_confs.append(c_row)
                clean_outcomes.append(y_val)

        if len(clean_outcomes) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(clean_outcomes)} người tham gia có dữ liệu đầy đủ qua mọi đợt (cần tối thiểu 25)."
            }

        A_arr = np.array(clean_treats, dtype=int)
        L_arr = np.array(clean_confs, dtype=float)
        Y_arr = np.array(clean_outcomes, dtype=float)

        res = MSMIPTWEngine.estimate(
            treatments=A_arr,
            confounders=L_arr,
            outcomes=Y_arr,
            wave_labels=payload.wave_labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MARGINAL_STRUCTURAL_MODEL_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "waves_count": res.get("waves_count"),
                "causal_effect_per_wave": res.get("causal_effect_per_wave"),
                "naive_ols_effect": res.get("naive_ols_effect"),
                "confounding_bias_pct": res.get("confounding_bias_pct"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/gee", response_model=GEEAnalysisOut)
def run_gee_analysis(survey_id: str, payload: GEEAnalysisRequest):
    """
    Phân tích Phương trình Ước lượng Tổng quát (Generalized Estimating Equations - GEE; Liang & Zeger, 1986):
    - Mô hình hóa tác động dân số trung bình (Population-Averaged Effects) trên dữ liệu khảo sát lặp nhiều đợt.
    - Xử lý tương quan nội cụm/cá nhân qua các cấu trúc ma trận làm việc (Exchangeable, AR(1), Independent).
    - Ước lượng sai số chuẩn vững Sandwich Huber-White đảm bảo tính nhất quán tiệm cận.
    - Tính tiêu chí lựa chọn cấu trúc tương quan QIC (Pan, 2001).
    - Diễn giải học thuật tự động chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        if not payload.predictor_question_ids or len(payload.predictor_question_ids) < 1:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 1 biến dự báo để ước lượng mô hình GEE.")

        if payload.scope == "verified_clean":
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if len(r_rows) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi hoàn thành ({len(r_rows)}) không đủ điều kiện (tối thiểu 15 phản hồi)."
            }

        resp_ids = [r["id"] for r in r_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        target_qids = [payload.cluster_question_id, payload.time_question_id, payload.outcome_question_id] + payload.predictor_question_ids
        placeholders_q = ",".join(["?"] * len(target_qids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *target_qids)).fetchall()

        by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        # Fetch titles of predictors
        q_meta_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, tuple(target_qids)).fetchall()
        title_map = {q["id"]: q["title"] for q in q_meta_rows}
        feature_names = [title_map.get(qid, f"X{idx+1}") for idx, qid in enumerate(payload.predictor_question_ids)]

        import re
        def parse_float(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        c_list = []
        t_list = []
        y_list = []
        x_rows = []

        for rid in resp_ids:
            ans = by_resp.get(rid, {})
            c_val = ans.get(payload.cluster_question_id)
            t_val = parse_float(ans.get(payload.time_question_id))
            y_val = parse_float(ans.get(payload.outcome_question_id))

            if c_val is None or t_val is None or y_val is None:
                continue

            row_x = []
            has_missing_x = False
            for x_qid in payload.predictor_question_ids:
                xv = parse_float(ans.get(x_qid))
                if xv is None:
                    has_missing_x = True
                    break
                row_x.append(xv)

            if not has_missing_x:
                c_list.append(str(c_val).strip())
                t_list.append(int(t_val))
                y_list.append(y_val)
                x_rows.append(row_x)

        if len(y_list) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(y_list)} bản ghi dữ liệu bảng lặp đầy đủ (cần tối thiểu 15 bản ghi)."
            }

        c_arr = np.array(c_list)
        t_arr = np.array(t_list, dtype=int)
        Y_arr = np.array(y_list, dtype=float)
        X_arr = np.array(x_rows, dtype=float)

        res = GEEEngine.estimate(
            cluster_ids=c_arr,
            time_points=t_arr,
            outcomes=Y_arr,
            predictors=X_arr,
            feature_names=feature_names,
            family=payload.family or "gaussian",
            corstr=payload.corstr or "exchangeable"
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="GEE_MODEL_EVALUATED",
            details={
                "clusters_count": res.get("clusters_count"),
                "observations_count": res.get("observations_count"),
                "family": res.get("family"),
                "corstr": res.get("working_correlation_structure"),
                "qic": res.get("qic"),
                "alpha_corr": res.get("estimated_correlation_parameter"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/randomization-inference", response_model=RandomizationInferenceOut)
def run_randomization_inference(survey_id: str, payload: RandomizationInferenceRequest):
    """
    Kiểm định Hoán vị Chính xác Fisher (Fisher's Exact Randomization Inference; Fisher, 1935):
    - Kiểm định Giả thuyết Vô hiệu Tuyệt đối (Sharp Null Hypothesis H0: Y_i(1) = Y_i(0) với mọi i).
    - Tạo phân phối hoán vị chính xác (B hoán vị ngẫu nhiên), miễn nhiễm trước vi phạm phân phối chuẩn.
    - Ước lượng độ dịch chuyển phân phối chính xác Hodges-Lehmann (1963) và 95% Exact CI.
    - So sánh song song giá trị p chính xác với kiểm định tiệm cận Welch t-test.
    - Diễn giải học thuật tự động chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        if payload.scope == "verified_clean":
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND verification_status = 'verified'",
                (survey_id,)
            ).fetchall()
        else:
            r_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        if len(r_rows) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi hoàn thành ({len(r_rows)}) không đủ điều kiện (tối thiểu 10 phản hồi)."
            }

        resp_ids = [r["id"] for r in r_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        target_qids = [payload.outcome_question_id, payload.treatment_question_id]
        placeholders_q = ",".join(["?"] * len(target_qids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *target_qids)).fetchall()

        by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_float(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        def parse_binary(v: Any) -> Optional[int]:
            if v is None or v == "":
                return None
            s = str(v).strip().lower()
            if s in ["1", "true", "yes", "co", "có", "tham gia", "treated", "can thiệp"]:
                return 1
            if s in ["0", "false", "no", "khong", "không", "chưa", "control", "đối chứng"]:
                return 0
            pf = parse_float(v)
            if pf is not None:
                return 1 if pf >= 1.0 else 0
            return None

        y_list = []
        d_list = []

        for rid in resp_ids:
            ans = by_resp.get(rid, {})
            y_val = parse_float(ans.get(payload.outcome_question_id))
            d_val = parse_binary(ans.get(payload.treatment_question_id))

            if y_val is not None and d_val is not None:
                y_list.append(y_val)
                d_list.append(d_val)

        if len(y_list) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(y_list)} phản hồi hợp lệ đồng thời về biến kết quả và can thiệp (cần tối thiểu 10)."
            }

        Y_arr = np.array(y_list, dtype=float)
        D_arr = np.array(d_list, dtype=int)

        res = RandomizationInferenceEngine.estimate(
            outcomes=Y_arr,
            treatment=D_arr,
            num_permutations=payload.num_permutations or 2500,
            alternative=payload.alternative or "two-sided"
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="RANDOMIZATION_INFERENCE_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "treated_count": res.get("treated_count"),
                "control_count": res.get("control_count"),
                "diff_means": res.get("difference_in_means", {}).get("observed_statistic"),
                "exact_p_value": res.get("difference_in_means", {}).get("exact_p_value"),
                "hl_estimate": res.get("hodges_lehmann_shift", {}).get("point_estimate"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/extreme-value", response_model=EVTAnalysisOut)
def analyze_extreme_value_theory(
    survey_id: str,
    payload: EVTAnalysisRequest
):
    """
    Phân tích Lý thuyết Giá trị Cực đoan (Extreme Value Theory - EVT)
    theo mô hình Peaks-Over-Threshold (POT) và Generalized Pareto Distribution (GPD)
    (Pickands 1975, Balkema & de Haan 1974, Davison & Smith 1990, McNeil & Frey 2000).
    Ước lượng tham số hình dạng đuôi ξ, quy mô σ, chỉ số Value-at-Risk (VaR) và Expected Shortfall (ES).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        metric_q = conn.execute(
            "SELECT id, title, question_type FROM questions WHERE id = ? AND survey_id = ?",
            (payload.metric_question_id, survey_id)
        ).fetchone()

        if not metric_q:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đo lường trong cuộc khảo sát này.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích đã chọn."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, answer_value
            FROM response_answers
            WHERE question_id = ? AND response_id IN ({placeholders})
        """, [payload.metric_question_id] + resp_ids).fetchall()

        metric_vals = []
        for a in ans_rows:
            raw = a["answer_value"]
            if raw is not None:
                try:
                    val = float(raw)
                    metric_vals.append(val)
                except (ValueError, TypeError):
                    continue

        if len(metric_vals) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(metric_vals)} phản hồi hợp lệ cho biến đo lường (cần tối thiểu 30 cho phân tích EVT)."
            }

        res = ExtremeValueEngine.estimate(
            data=metric_vals,
            threshold_percentile=payload.threshold_percentile or 0.90,
            custom_threshold=payload.custom_threshold,
            alpha_levels=payload.alpha_levels or [0.95, 0.99, 0.995]
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="EXTREME_VALUE_ANALYSIS_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "threshold": res.get("threshold"),
                "exceedances_count": res.get("exceedances_count"),
                "shape_xi": res.get("shape_xi"),
                "scale_sigma": res.get("scale_sigma"),
                "tail_classification": res.get("tail_classification"),
                "scope": payload.scope
            }
        )

        return res


@router.post("/extreme-bounds", response_model=ExtremeBoundsAnalysisOut)
def run_extreme_bounds_analysis(survey_id: str, payload: ExtremeBoundsAnalysisRequest):
    """
    Extreme Bound Analysis (EBA; Leamer 1983, Sala-i-Martin 1997)
    Kiểm định độ nhạy đặc tả mô hình qua toàn bộ tổ hợp biến kiểm soát ứng viên.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        focus_qid = payload.focus_question_id
        outcome_qid = payload.outcome_question_id
        cand_qids = payload.candidate_question_ids
        free_qids = payload.free_question_ids or []

        if not focus_qid or not outcome_qid:
            raise HTTPException(status_code=400, detail="Thiếu biến trọng tâm hoặc biến kết quả.")

        if not cand_qids:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 1 biến kiểm soát ứng viên để phân tích EBA.")

        all_qids = list(dict.fromkeys([outcome_qid, focus_qid] + free_qids + cand_qids))

        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            (survey_id, *all_qids)
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}

        if focus_qid not in q_dict or outcome_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Biến trọng tâm hoặc kết quả không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không có phản hồi trong phạm vi được chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        resp_placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({resp_placeholders})
              AND question_id IN ({placeholders})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            row_ok = True
            for qid in all_qids:
                num_v = parse_num(r_ans.get(qid))
                if num_v is None:
                    row_ok = False
                    break
                row_dict[qid] = num_v
            if row_ok:
                data_rows.append(row_dict)

        if len(data_rows) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi đầy đủ dữ liệu (cần tối thiểu 15 phản hồi để chạy EBA)."
            }

        res = ExtremeBoundsEngine.analyze(
            data=data_rows,
            focus_var=focus_qid,
            outcome_var=outcome_qid,
            candidate_vars=cand_qids,
            free_vars=free_qids,
            max_controls_per_model=payload.max_controls_per_model,
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="EXTREME_BOUNDS_ANALYSIS_EVALUATED",
            details={
                "focus_qid": focus_qid,
                "outcome_qid": outcome_qid,
                "total_models": res.get("summary", {}).get("total_models_evaluated"),
                "leamer_verdict": res.get("summary", {}).get("leamer_verdict"),
                "sala_cdf": res.get("summary", {}).get("sala_i_martin_cdf"),
                "scope": payload.scope,
            }
        )

        return res




@router.post("/causal-discovery", response_model=CausalDiscoveryOut)
def run_causal_discovery_analysis(
    survey_id: str,
    payload: CausalDiscoveryRequest
):
    """
    Executes observational Causal Discovery DAG identification using LiNGAM & ANM (Shimizu et al. 2006; Hoyer et al. 2009).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, question_type FROM questions WHERE survey_id = ?", (survey_id,))
        q_rows = cursor.fetchall()
        if not q_rows:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại hoặc không có câu hỏi.")
        q_titles = {q["id"]: q["title"] for q in q_rows}

        var_qids = payload.variable_question_ids
        if not var_qids or len(var_qids) < 2:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Cần tối thiểu 2 biến để khám phá cấu trúc đồ thị nhân quả DAG."
            }

        # Filter respondents by scope
        scope_clause = ""
        if payload.scope == "verified_clean":
            scope_clause = " AND is_verified = 1 AND quality_score >= 0.70"

        cursor.execute(f"SELECT id FROM responses WHERE survey_id = ?{scope_clause}", (survey_id,))
        resp_rows = cursor.fetchall()
        resp_ids = [r["id"] for r in resp_rows]

        if len(resp_ids) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(resp_ids)} phản hồi (cần tối thiểu 15 phản hồi để xác định mô hình phi Gauss LiNGAM)."
            }

        r_ph = ",".join(["?"] * len(resp_ids))
        q_ph = ",".join(["?"] * len(var_qids))
        cursor.execute(
            f"SELECT response_id, question_id, answer_value FROM response_answers WHERE response_id IN ({r_ph}) AND question_id IN ({q_ph})",
            (*resp_ids, *var_qids)
        )
        ans_rows = cursor.fetchall()

        resp_map = {}
        for row in ans_rows:
            rid = row["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            val = row["answer_value"]
            if val is not None:
                try:
                    resp_map[rid][row["question_id"]] = float(val)
                except (ValueError, TypeError):
                    pass

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map.get(rid, {})
            row_dict = {qid: r_ans.get(qid) for qid in var_qids}
            data_rows.append(row_dict)

        res = CausalDiscoveryEngine.estimate(
            data=data_rows,
            variable_qids=var_qids,
            question_titles=q_titles,
            prune_threshold=payload.prune_threshold
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CAUSAL_DISCOVERY_DAG_EVALUATED",
            details={
                "n_variables": len(var_qids),
                "prune_threshold": payload.prune_threshold,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "causal_order": res.get("causal_order"),
                "n_directed_edges": len(res.get("directed_edges", [])),
                "status": res.get("status")
            }
        )

        return res





@router.post("/bart-causal", response_model=BARTCausalOut)
def run_bart_causal_analysis(
    survey_id: str,
    payload: BARTCausalRequest
):
    """
    Executes Bayesian Additive Regression Trees (BART) flexible treatment effect estimation and heterogeneity profiling.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_qid = payload.treatment_question_id
        y_qid = payload.outcome_question_id
        x_qids = payload.covariate_question_ids

        if not x_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 biến kiểm soát/điều tiết nền (Covariates X).")

        all_qids = list(set([t_qid, y_qid] + x_qids))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        if len(q_rows) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")
        q_titles = {q["id"]: q["title"] for q in q_rows}

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 25 phản hồi để ước lượng BART Causal)."
            }

        # Map covariate IDs to question titles for readable variable importance
        cov_title_map = {qid: q_titles.get(qid, qid) for qid in x_qids}
        adapted_data = []
        for row in data_rows:
            new_r = {
                t_qid: row.get(t_qid),
                y_qid: row.get(y_qid),
            }
            for qid in x_qids:
                new_r[cov_title_map[qid]] = row.get(qid)
            adapted_data.append(new_r)

        cov_titles = [cov_title_map[qid] for qid in x_qids]

        res = BARTCausalEngine.estimate(
            data=adapted_data,
            treatment_var=t_qid,
            outcome_var=y_qid,
            covariates=cov_titles,
            n_trees=min(100, max(10, payload.n_trees)),
            n_samples=min(500, max(50, payload.n_samples))
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="BART_CAUSAL_HETEROGENEITY_EVALUATED",
            details={
                "treatment_qid": t_qid,
                "outcome_qid": y_qid,
                "n_covariates": len(x_qids),
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "ate": res.get("treatment_effects", {}).get("ate", {}).get("estimate"),
                "has_heterogeneity": res.get("diagnostics", {}).get("has_significant_heterogeneity"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/conjoint-choice", response_model=ConjointChoiceOut)
def run_conjoint_choice_analysis(
    survey_id: str,
    payload: ConjointChoiceRequest
):
    """
    Executes Choice-Based Conjoint (CBC) / Discrete Choice Experiment (DCE) analysis via Multinomial Logit (McFadden 1974).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        choice_qid = payload.choice_question_id
        attr_qids = payload.attribute_question_ids
        price_qid = payload.price_question_id

        if not attr_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 thuộc tính sản phẩm/dịch vụ (Attributes).")

        all_qids = list(set([choice_qid] + attr_qids + ([price_qid] if price_qid else [])))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        if len(q_rows) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")
        q_titles = {q["id"]: q["title"] for q in q_rows}

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 20 phản hồi để ước lượng Conjoint MNL)."
            }

        # Map attribute question IDs to readable titles
        attr_title_map = {qid: q_titles.get(qid, qid) for qid in attr_qids}
        adapted_data = []
        for row in data_rows:
            new_r = {choice_qid: row.get(choice_qid)}
            for qid in attr_qids:
                new_r[attr_title_map[qid]] = row.get(qid)
            adapted_data.append(new_r)

        attr_titles = [attr_title_map[qid] for qid in attr_qids]
        price_title = attr_title_map.get(price_qid) if price_qid else None

        res = ConjointChoiceEngine.estimate(
            choice_data=adapted_data,
            choice_var=choice_qid,
            attribute_vars=attr_titles,
            price_var=price_title,
            price_unit=payload.price_unit
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONJOINT_CHOICE_MNL_EVALUATED",
            details={
                "choice_qid": choice_qid,
                "n_attributes": len(attr_qids),
                "price_qid": price_qid,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "pseudo_r2": res.get("diagnostics", {}).get("mcfadden_pseudo_r2"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/mgsem-invariance", response_model=MGSEMInvarianceOut)
def run_mgsem_invariance_analysis(
    survey_id: str,
    payload: MGSEMInvarianceRequest
):
    """
    Executes Multi-Group Structural Equation Modeling (MG-SEM) measurement invariance testing and latent means comparison (Meredith 1993; Byrne 2013).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        grp_qid = payload.group_question_id
        ind_qids = payload.indicator_question_ids

        if not ind_qids or len(ind_qids) < 2:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 2 biến chỉ báo đo lường (Indicators).")

        all_qids = list(set([grp_qid] + ind_qids))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        if len(q_rows) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")
        q_titles = {q["id"]: q["title"] for q in q_rows}

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 30 phản hồi để kiểm định bất biến đa nhóm MG-SEM)."
            }

        # Map indicator question IDs to readable titles
        ind_title_map = {qid: q_titles.get(qid, qid) for qid in ind_qids}
        adapted_data = []
        for row in data_rows:
            new_r = {grp_qid: row.get(grp_qid)}
            for qid in ind_qids:
                new_r[ind_title_map[qid]] = row.get(qid)
            adapted_data.append(new_r)

        ind_titles = [ind_title_map[qid] for qid in ind_qids]

        res = MGSEMInvarianceEngine.estimate(
            data=adapted_data,
            group_var=grp_qid,
            indicator_vars=ind_titles,
            reference_group=payload.reference_group
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MGSEM_INVARIANCE_EVALUATED",
            details={
                "group_qid": grp_qid,
                "n_indicators": len(ind_qids),
                "reference_group": payload.reference_group,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "scalar_supported": res.get("diagnostics", {}).get("scalar_supported"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/gam-spline", response_model=GAMSplineOut)
def run_gam_spline_analysis(
    survey_id: str,
    payload: GAMSplineRequest
):
    """
    Executes Generalized Additive Models (GAM) with Penalized B-Splines (P-Splines) to model non-linear dose-response curves and tipping points.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        x_qid = payload.predictor_question_id
        y_qid = payload.outcome_question_id
        z_qids = payload.covariate_question_ids or []

        all_qids = list(set([x_qid, y_qid] + z_qids))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        if len(q_rows) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")
        q_titles = {q["id"]: q["title"] for q in q_rows}

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 25 phản hồi để ước lượng GAM Spline)."
            }

        # Readable titles
        x_title = q_titles.get(x_qid, x_qid)
        y_title = q_titles.get(y_qid, y_qid)
        z_title_map = {qid: q_titles.get(qid, qid) for qid in z_qids}

        adapted_data = []
        for row in data_rows:
            new_r = {
                x_title: row.get(x_qid),
                y_title: row.get(y_qid),
            }
            for qid in z_qids:
                new_r[z_title_map[qid]] = row.get(qid)
            adapted_data.append(new_r)

        z_titles = [z_title_map[qid] for qid in z_qids]

        res = GAMSplineEngine.estimate(
            data=adapted_data,
            predictor_var=x_title,
            outcome_var=y_title,
            covariate_vars=z_titles if z_titles else None,
            n_knots=max(5, min(20, payload.n_knots)),
            grid_points=max(30, min(100, payload.grid_points))
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="GAM_SPLINE_NONLINEARITY_EVALUATED",
            details={
                "predictor_qid": x_qid,
                "outcome_qid": y_qid,
                "n_covariates": len(z_qids),
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "edf": res.get("diagnostics", {}).get("effective_degrees_of_freedom"),
                "is_nonlinear": res.get("diagnostics", {}).get("is_strictly_nonlinear"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/latent-profile", response_model=LatentProfileOut)
def run_latent_profile_analysis(
    survey_id: str,
    payload: LatentProfileRequest
):
    """
    Executes Latent Profile Analysis (LPA) & Gaussian Finite Mixture Modeling
    (McLachlan & Peel 2000; Fraley & Raftery 2002; Collins & Lanza 2010).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        ind_qids = payload.indicator_question_ids
        if len(ind_qids) < 2:
            raise HTTPException(status_code=400, detail="Yêu cầu tối thiểu 2 biến chỉ báo để phân tích hồ sơ tiềm ẩn.")

        placeholders_q = ",".join(["?"] * len(ind_qids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *ind_qids)
        ).fetchall()
        if len(q_rows) < len(ind_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")
        q_titles = {q["id"]: q["title"] for q in q_rows}
        indicator_labels = [q_titles[qid] for qid in ind_qids]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *ind_qids)).fetchall()

        # Build pivot table
        data_by_resp: Dict[str, Dict[str, float]] = {}
        for ans in ans_rows:
            rid = ans["response_id"]
            qid = ans["question_id"]
            raw_val = ans["answer_value"]
            try:
                val = float(raw_val)
                if rid not in data_by_resp:
                    data_by_resp[rid] = {}
                data_by_resp[rid][qid] = val
            except (ValueError, TypeError):
                continue

        # Extract complete cases across all indicators
        matrix = []
        for rid, row in data_by_resp.items():
            if all(qid in row for qid in ind_qids):
                matrix.append([row[qid] for qid in ind_qids])

        if len(matrix) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(matrix)} quan sát đầy đủ mọi chỉ báo (yêu cầu tối thiểu 15 để phân tích LPA)."
            }

        res = LatentProfileEngine.compute_latent_profiles(
            data_matrix=matrix,
            indicator_labels=indicator_labels,
            n_profiles=payload.n_profiles,
            max_profiles=payload.max_profiles
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LATENT_PROFILE_ANALYSIS_ESTIMATED",
            details={
                "n_indicators": len(ind_qids),
                "n_samples": len(matrix),
                "scope": payload.scope,
                "optimal_k": res.get("diagnostics", {}).get("optimal_n_classes"),
                "entropy": res.get("diagnostics", {}).get("entropy"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/shapley-drivers", response_model=ShapleyDriverOut)
def run_shapley_driver_analysis(
    survey_id: str,
    payload: ShapleyDriverRequest
):
    """
    Executes Shapley Value Regression & Key Driver Analysis (KDA)
    (Lipovetsky & Conklin 2001; Martilla & James 1977; Lundberg & Lee 2017).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        driver_qids = payload.driver_question_ids
        outcome_qid = payload.outcome_question_id

        if len(driver_qids) < 2:
            raise HTTPException(status_code=400, detail="Yêu cầu tối thiểu 2 biến động lực để phân rã giá trị Shapley.")

        all_qids = list(set(driver_qids + [outcome_qid]))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        if len(q_rows) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")
        q_titles = {q["id"]: q["title"] for q in q_rows}
        driver_names = [q_titles[qid] for qid in driver_qids]
        outcome_name = q_titles[outcome_qid]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        # Build pivot table
        data_by_resp: Dict[str, Dict[str, float]] = {}
        for ans in ans_rows:
            rid = ans["response_id"]
            qid = ans["question_id"]
            raw_val = ans["answer_value"]
            try:
                val = float(raw_val)
                if rid not in data_by_resp:
                    data_by_resp[rid] = {}
                data_by_resp[rid][qid] = val
            except (ValueError, TypeError):
                continue

        # Extract complete cases
        X_mat = []
        y_vec = []
        for rid, row in data_by_resp.items():
            if all(qid in row for qid in driver_qids) and outcome_qid in row:
                X_mat.append([row[qid] for qid in driver_qids])
                y_vec.append(row[outcome_qid])

        if len(X_mat) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(X_mat)} quan sát đầy đủ mọi thuộc tính động lực và kết quả (yêu cầu tối thiểu 15 để phân tích Shapley KDA)."
            }

        res = ShapleyDriverEngine.compute_key_drivers(
            X_matrix=X_mat,
            y_vector=y_vec,
            driver_names=driver_names,
            outcome_name=outcome_name
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SHAPLEY_KEY_DRIVERS_EVALUATED",
            details={
                "outcome_qid": outcome_qid,
                "n_drivers": len(driver_qids),
                "n_samples": len(X_mat),
                "full_r2": res.get("diagnostics", {}).get("full_model_r2"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/plackett-luce", response_model=PlackettLuceOut)
def run_plackett_luce_analysis(
    survey_id: str,
    payload: PlackettLuceRequest
):
    """
    Executes Plackett-Luce Choice Model & Rank-Ordered Logit
    (Luce 1959; Plackett 1975; Beggs et al. 1981; Hunter 2004 MM Algorithm).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if not payload.ranking_question_id and not payload.item_question_ids:
            raise HTTPException(
                status_code=400,
                detail="Cần cung cấp ranking_question_id (câu hỏi xếp hạng) hoặc item_question_ids (danh sách câu hỏi đánh giá đa thuộc tính)."
            )

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        rankings_data: List[List[int]] = []
        item_labels: List[str] = []

        # Mode A: Dedicated Ranking Question
        if payload.ranking_question_id:
            rq_id = payload.ranking_question_id
            q_row = conn.execute("SELECT id, title, question_type, options_json FROM questions WHERE id = ? AND survey_id = ?", (rq_id, survey_id)).fetchone()
            if not q_row:
                raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi xếp hạng.")

            raw_opts = q_row["options_json"]
            opts = json.loads(raw_opts) if isinstance(raw_opts, str) else (raw_opts or [])
            if len(opts) < 2:
                raise HTTPException(status_code=400, detail="Câu hỏi xếp hạng phải có tối thiểu 2 phương án.")

            item_keys = []
            item_labels = []
            for it in opts:
                if isinstance(it, dict):
                    item_keys.append(str(it.get("id", "")))
                    item_labels.append(str(it.get("label", it.get("title", it.get("id", "")))))
                else:
                    item_keys.append(str(it))
                    item_labels.append(str(it))

            key_to_idx = {k: idx for idx, k in enumerate(item_keys)}
            label_to_idx = {l: idx for idx, l in enumerate(item_labels)}

            ans_rows = conn.execute(f"""
                SELECT response_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders_r}) AND question_id = ?
            """, (*resp_ids, rq_id)).fetchall()

            for a in ans_rows:
                val = a["answer_value"]
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list) and len(parsed) >= 2:
                        perm = []
                        for el in parsed:
                            str_el = str(el)
                            if str_el in key_to_idx:
                                perm.append(key_to_idx[str_el])
                            elif str_el in label_to_idx:
                                perm.append(label_to_idx[str_el])
                        if len(perm) >= 2:
                            rankings_data.append(perm)
                except Exception:
                    continue

        # Mode B: Multi-item rating / score questions inducing ranking
        elif payload.item_question_ids:
            iq_ids = payload.item_question_ids
            if len(iq_ids) < 2:
                raise HTTPException(status_code=400, detail="Yêu cầu tối thiểu 2 câu hỏi đánh giá thuộc tính.")

            placeholders_q = ",".join(["?"] * len(iq_ids))
            q_rows = conn.execute(
                f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
                (survey_id, *iq_ids)
            ).fetchall()
            if len(q_rows) < len(iq_ids):
                raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại.")

            q_title_map = {q["id"]: q["title"] for q in q_rows}
            item_labels = [q_title_map[qid] for qid in iq_ids]
            M = len(iq_ids)

            ans_rows = conn.execute(f"""
                SELECT response_id, question_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders_r}) AND question_id IN ({placeholders_q})
            """, (*resp_ids, *iq_ids)).fetchall()

            data_by_resp: Dict[str, Dict[str, float]] = {}
            for ans in ans_rows:
                rid = ans["response_id"]
                qid = ans["question_id"]
                try:
                    val = float(ans["answer_value"])
                    if rid not in data_by_resp:
                        data_by_resp[rid] = {}
                    data_by_resp[rid][qid] = val
                except (ValueError, TypeError):
                    continue

            for rid, row in data_by_resp.items():
                if all(qid in row for qid in iq_ids):
                    # Induce ranking: higher rating = preferred earlier
                    scores = [row[qid] for qid in iq_ids]
                    # Order indices descending by score with slight random jitter for ties
                    perm = list(np.argsort([-s for s in scores]))
                    rankings_data.append(perm)

        if len(rankings_data) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(rankings_data)} lượt xếp hạng hợp lệ (yêu cầu tối thiểu 15 để ước lượng mô hình Plackett-Luce)."
            }

        res = PlackettLuceEngine.compute_ranking_choice(
            rankings_data=rankings_data,
            item_names=item_labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="PLACKETT_LUCE_RANKING_CHOICE_EVALUATED",
            details={
                "n_items": len(item_labels),
                "n_samples": len(rankings_data),
                "mcfadden_pseudo_r2": res.get("diagnostics", {}).get("mcfadden_pseudo_r2"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/maxdiff", response_model=MaxDiffOut)
def run_maxdiff_analysis(
    survey_id: str,
    payload: MaxDiffRequest
):
    """
    Executes MaxDiff (Maximum Difference / Best-Worst Scaling Case 1)
    (Finn & Louviere 1992; Marley & Louviere 2005; Orme 2009).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if not (payload.best_question_id and payload.worst_question_id) and not payload.item_question_ids:
            raise HTTPException(
                status_code=400,
                detail="Cần cung cấp (best_question_id và worst_question_id) hoặc item_question_ids (danh sách thuộc tính đánh giá)."
            )

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        tasks_data: List[Dict[str, Any]] = []
        item_names: List[str] = []

        # Mode A: Pair of Best & Worst Questions
        if payload.best_question_id and payload.worst_question_id:
            bq_id = payload.best_question_id
            wq_id = payload.worst_question_id

            q_rows = conn.execute(
                "SELECT id, title, options_json FROM questions WHERE id IN (?, ?) AND survey_id = ?",
                (bq_id, wq_id, survey_id)
            ).fetchall()
            if len(q_rows) < 2:
                raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi Best hoặc Worst.")

            # Extract options from best question as item universe
            bq_row = next(q for q in q_rows if q["id"] == bq_id)
            raw_opts = bq_row["options_json"]
            opts = json.loads(raw_opts) if isinstance(raw_opts, str) else (raw_opts or [])
            if len(opts) < 3:
                raise HTTPException(status_code=400, detail="Mô hình MaxDiff yêu cầu tối thiểu 3 phương án lựa chọn.")

            item_keys = []
            item_names = []
            for it in opts:
                if isinstance(it, dict):
                    item_keys.append(str(it.get("id", "")))
                    item_names.append(str(it.get("label", it.get("title", it.get("id", "")))))
                else:
                    item_keys.append(str(it))
                    item_names.append(str(it))

            key_to_idx = {k: idx for idx, k in enumerate(item_keys)}
            label_to_idx = {l: idx for idx, l in enumerate(item_names)}
            M = len(item_names)

            ans_rows = conn.execute(f"""
                SELECT response_id, question_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders_r}) AND question_id IN (?, ?)
            """, (*resp_ids, bq_id, wq_id)).fetchall()

            data_by_resp: Dict[str, Dict[str, str]] = {}
            for ans in ans_rows:
                rid = ans["response_id"]
                qid = ans["question_id"]
                val = str(ans["answer_value"]).strip()
                if rid not in data_by_resp:
                    data_by_resp[rid] = {}
                data_by_resp[rid][qid] = val

            for rid, row in data_by_resp.items():
                if bq_id in row and wq_id in row:
                    b_val = row[bq_id]
                    w_val = row[wq_id]

                    b_idx = key_to_idx.get(b_val, label_to_idx.get(b_val))
                    w_idx = key_to_idx.get(w_val, label_to_idx.get(w_val))

                    if b_idx is not None and w_idx is not None and b_idx != w_idx:
                        tasks_data.append({
                            "available_items": list(range(M)),
                            "best_item": b_idx,
                            "worst_item": w_idx
                        })

        # Mode B: Multi-item rating questions inducing Best-Worst trade-offs
        elif payload.item_question_ids:
            iq_ids = payload.item_question_ids
            if len(iq_ids) < 3:
                raise HTTPException(status_code=400, detail="Yêu cầu tối thiểu 3 câu hỏi đánh giá thuộc tính.")

            placeholders_q = ",".join(["?"] * len(iq_ids))
            q_rows = conn.execute(
                f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
                (survey_id, *iq_ids)
            ).fetchall()
            if len(q_rows) < len(iq_ids):
                raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại.")

            q_title_map = {q["id"]: q["title"] for q in q_rows}
            item_names = [q_title_map[qid] for qid in iq_ids]
            M = len(iq_ids)

            ans_rows = conn.execute(f"""
                SELECT response_id, question_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders_r}) AND question_id IN ({placeholders_q})
            """, (*resp_ids, *iq_ids)).fetchall()

            data_by_resp: Dict[str, Dict[str, float]] = {}
            for ans in ans_rows:
                rid = ans["response_id"]
                qid = ans["question_id"]
                try:
                    val = float(ans["answer_value"])
                    if rid not in data_by_resp:
                        data_by_resp[rid] = {}
                    data_by_resp[rid][qid] = val
                except (ValueError, TypeError):
                    continue

            for rid, row in data_by_resp.items():
                if all(qid in row for qid in iq_ids):
                    scores = [row[qid] for qid in iq_ids]
                    b_idx = int(np.argmax(scores))
                    w_idx = int(np.argmin(scores))
                    if scores[b_idx] > scores[w_idx]:
                        tasks_data.append({
                            "available_items": list(range(M)),
                            "best_item": b_idx,
                            "worst_item": w_idx
                        })

        if len(tasks_data) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(tasks_data)} nhiệm vụ Best-Worst hợp lệ (yêu cầu tối thiểu 15 để phân tích MaxDiff)."
            }

        res = MaxDiffEngine.compute_maxdiff(
            tasks_data=tasks_data,
            item_names=item_names
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MAXDIFF_BEST_WORST_SCALING_EVALUATED",
            details={
                "n_items": len(item_names),
                "n_tasks": len(tasks_data),
                "mcfadden_pseudo_r2": res.get("diagnostics", {}).get("mcfadden_pseudo_r2"),
                "status": res.get("status")
            }
        )

        return res





@router.post("/bayesian-network", response_model=BayesianNetworkOut)
def run_bayesian_network_analysis(
    survey_id: str,
    payload: BayesianNetworkRequest
):
    """
    Executes Gaussian Bayesian Network (GBN) Structure Learning & Markov Blanket Analysis
    (Heckerman 1995; Scutari 2010; Koller & Friedman 2009).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_ids = payload.question_ids
        if len(q_ids) < 3:
            raise HTTPException(status_code=400, detail="Yêu cầu tối thiểu 3 câu hỏi để học cấu trúc Mạng Bayes.")

        placeholders_q = ",".join(["?"] * len(q_ids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *q_ids)
        ).fetchall()
        if len(q_rows) < len(q_ids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        q_title_map = {q["id"]: q["title"] for q in q_rows}
        node_labels = [q_title_map[qid] for qid in q_ids]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r}) AND question_id IN ({placeholders_q})
        """, (*resp_ids, *q_ids)).fetchall()

        # Build pivot table
        data_by_resp: Dict[str, Dict[str, float]] = {}
        for ans in ans_rows:
            rid = ans["response_id"]
            qid = ans["question_id"]
            try:
                val = float(ans["answer_value"])
                if rid not in data_by_resp:
                    data_by_resp[rid] = {}
                data_by_resp[rid][qid] = val
            except (ValueError, TypeError):
                continue

        # Complete cases
        matrix = []
        for rid, row in data_by_resp.items():
            if all(qid in row for qid in q_ids):
                matrix.append([row[qid] for qid in q_ids])

        if len(matrix) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(matrix)} quan sát đầy đủ mọi biến (yêu cầu tối thiểu 20 để học cấu trúc Mạng Bayes)."
            }

        res = BayesianNetworkEngine.learn_bayesian_network(
            data_matrix=matrix,
            node_labels=node_labels,
            max_parents=max(2, min(5, payload.max_parents))
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="BAYESIAN_NETWORK_DAG_EVALUATED",
            details={
                "n_nodes": len(q_ids),
                "n_samples": len(matrix),
                "total_edges": res.get("diagnostics", {}).get("total_edges"),
                "bic_score": res.get("diagnostics", {}).get("final_bic_score"),
                "status": res.get("status")
            }
        )

        return res


@router.post("/joint-model", response_model=JointModelAnalysisOut)
def analyze_joint_model(
    survey_id: str,
    payload: JointModelAnalysisRequest
):
    """
    Mô hình Liên kết Dọc & Sống sót (Joint Modeling of Longitudinal & Survival Data)
    (Wulfsohn & Tsiatis 1997, Henderson et al. 2000, Rizopoulos 2010, 2012).
    Liên kết mô hình hiệu ứng hỗn hợp tuyến tính (LMM) với mô hình nguy cơ tương đối (Cox PH)
    để điều chỉnh hiện tượng thất thoát mẫu có tính thông tin (Non-ignorable Panel Attrition).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        target_qids = [payload.subject_question_id, payload.time_question_id, payload.outcome_question_id]
        if payload.event_question_id:
            target_qids.append(payload.event_question_id)
        if payload.event_time_question_id:
            target_qids.append(payload.event_time_question_id)

        target_qids = list(set(target_qids))
        placeholders_q = ",".join(["?"] * len(target_qids))

        q_rows = conn.execute(f"""
            SELECT id FROM questions
            WHERE survey_id = ? AND id IN ({placeholders_q})
        """, [survey_id] + target_qids).fetchall()

        found_qids = {r["id"] for r in q_rows}
        if payload.subject_question_id not in found_qids or payload.time_question_id not in found_qids or payload.outcome_question_id not in found_qids:
            raise HTTPException(status_code=400, detail="Một trong các câu hỏi bắt buộc (subject, time, outcome) không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            r_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            r_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if len(r_rows) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi hoàn thành ({len(r_rows)}) không đủ điều kiện (tối thiểu 10 phản hồi)."
            }

        resp_ids = [r["id"] for r in r_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *target_qids)).fetchall()

        by_resp = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

        import re
        def parse_float(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                m = re.match(r'^\\s*([0-9]+(?:\\.[0-9]+)?)\\b', str(v).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
            return None

        # Build raw subject observations
        subject_waves = {}
        for rid in resp_ids:
            ans = by_resp.get(rid, {})
            subj_raw = ans.get(payload.subject_question_id)
            time_val = parse_float(ans.get(payload.time_question_id))
            out_val = parse_float(ans.get(payload.outcome_question_id))

            if subj_raw is not None and time_val is not None and out_val is not None:
                sid = str(subj_raw).strip()
                if sid not in subject_waves:
                    subject_waves[sid] = []

                ev_val = 0
                if payload.event_question_id and payload.event_question_id in ans:
                    raw_ev = str(ans[payload.event_question_id]).strip().lower()
                    if raw_ev in ["1", "true", "yes", "có", "bỏ cuộc", "attrited", "dropped"]:
                        ev_val = 1

                ev_time = time_val
                if payload.event_time_question_id and payload.event_time_question_id in ans:
                    pf_et = parse_float(ans[payload.event_time_question_id])
                    if pf_et is not None:
                        ev_time = pf_et

                subject_waves[sid].append({
                    "time": time_val,
                    "y": out_val,
                    "event": ev_val,
                    "event_time": ev_time
                })

        if len(subject_waves) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(subject_waves)} đối tượng hợp lệ đầy đủ các biến (cần tối thiểu 10 đối tượng)."
            }

        # Determine maximum wave observed in the dataset
        all_wave_times = [obs["time"] for obs_list in subject_waves.values() for obs in obs_list]
        max_study_time = max(all_wave_times) if all_wave_times else 1.0

        longitudinal_records = []
        survival_records = []

        for sid, obs_list in subject_waves.items():
            obs_list.sort(key=lambda x: x["time"])
            last_obs = obs_list[-1]

            # If event not explicitly given, infer attrition if subject was not observed at the final wave
            if payload.event_question_id:
                has_event = any(o["event"] == 1 for o in obs_list)
                final_event = 1 if has_event else 0
                final_event_time = max(o["event_time"] for o in obs_list)
            else:
                final_event = 1 if last_obs["time"] < max_study_time else 0
                final_event_time = last_obs["time"]

            survival_records.append({
                "subject_id": sid,
                "event_time": final_event_time,
                "event": final_event
            })

            for obs in obs_list:
                longitudinal_records.append({
                    "subject_id": sid,
                    "time": obs["time"],
                    "y": obs["y"]
                })

        res = JointModelingEngine.estimate(
            longitudinal_records=longitudinal_records,
            survival_records=survival_records
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="JOINT_MODEL_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "total_obs": res.get("total_longitudinal_observations"),
                "alpha": res.get("survival_submodel", {}).get("association_alpha"),
                "hazard_ratio": res.get("survival_submodel", {}).get("hazard_ratio"),
                "p_value": res.get("survival_submodel", {}).get("p_value"),
                "is_non_ignorable": res.get("attrition_diagnostics", {}).get("is_non_ignorable"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/conformal-prediction", response_model=ConformalPredictionAnalysisOut)
def run_conformal_prediction(survey_id: str, payload: ConformalPredictionAnalysisRequest):
    """
    Phân tích Conformal Prediction & Khoảng Rủi ro Phân phối Tự do (Vovk et al. 2005; Angelopoulos & Bates 2023).
    Đảm bảo hữu hạn mẫu không phụ thuộc giả định chuẩn tắc hay tính đồng nhất phương sai.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qid = payload.target_question_id
        feat_qids = payload.feature_question_ids

        if not feat_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất một câu hỏi đặc trưng làm biến dự báo.")

        all_qids = [target_qid] + feat_qids
        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if target_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi mục tiêu ID '{target_qid}'.")

        missing_feats = [fid for fid in feat_qids if fid not in q_dict]
        if missing_feats:
            raise HTTPException(status_code=400, detail=f"Các câu hỏi đặc trưng sau không tồn tại: {missing_feats}")

        # Fetch responses according to scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        # Query response answers
        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            t_val = parse_num(answers.get(target_qid))
            if t_val is None:
                continue

            row_feats = {}
            valid_feats = True
            for fid in feat_qids:
                f_val = parse_num(answers.get(fid))
                if f_val is None:
                    valid_feats = False
                    break
                row_feats[fid] = f_val

            if valid_feats:
                row_feats[target_qid] = t_val
                records.append(row_feats)

        if len(records) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ các biến số (cần tối thiểu 15 phản hồi)."
            }

        res = ConformalPredictionEngine.fit_and_predict(
            records=records,
            target_field=target_qid,
            feature_fields=feat_qids,
            alpha=payload.alpha,
            method=payload.method,
            calib_fraction=payload.calib_fraction,
            test_fraction=payload.test_fraction,
            clamp_min=payload.clamp_min,
            clamp_max=payload.clamp_max
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONFORMAL_PREDICTION_EVALUATED",
            details={
                "target_question": q_dict[target_qid]["title"],
                "feature_count": len(feat_qids),
                "alpha": payload.alpha,
                "nominal_coverage": res.get("parameters", {}).get("nominal_coverage"),
                "conformal_coverage": res.get("evaluation_metrics", {}).get("conformal_coverage"),
                "gaussian_coverage": res.get("evaluation_metrics", {}).get("gaussian_coverage"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/msem", response_model=MSEMAnalysisOut)
def run_msem_analysis(survey_id: str, payload: MSEMAnalysisRequest):
    """
    Phân tích Mô hình Cấu trúc Tuyến tính Đa cấp (MSEM 1-1-1 Multilevel Mediation; Preacher et al. 2010).
    Phân rã hiệp phương sai trực giao Within-level và Between-level, triệt tiêu Conflation Bias.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        c_qid = payload.cluster_question_id
        x_qid = payload.x_question_id
        m_qid = payload.m_question_id
        y_qid = payload.y_question_id

        all_qids = [c_qid, x_qid, m_qid, y_qid]
        if len(set(all_qids)) < 4:
            raise HTTPException(status_code=400, detail="Bốn biến số (Cụm, Tiền đề X, Trung gian M, Kết quả Y) phải là 4 câu hỏi phân biệt.")

        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        for qid in all_qids:
            if qid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi ID '{qid}' trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            c_val = answers.get(c_qid)
            if c_val is None or str(c_val).strip() == "":
                continue

            x_val = parse_num(answers.get(x_qid))
            m_val = parse_num(answers.get(m_qid))
            y_val = parse_num(answers.get(y_qid))

            if x_val is not None and m_val is not None and y_val is not None:
                records.append({
                    c_qid: str(c_val).strip(),
                    x_qid: x_val,
                    m_qid: m_val,
                    y_qid: y_val
                })

        if len(records) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ các biến (cần tối thiểu 20 phản hồi)."
            }

        res = MSEMEngine.estimate_multilevel_mediation(
            records=records,
            cluster_field=c_qid,
            x_field=x_qid,
            m_field=m_qid,
            y_field=y_qid,
            n_mc_sims=payload.n_mc_sims
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MSEM_EVALUATED",
            details={
                "cluster_question": q_dict[c_qid]["title"],
                "x_question": q_dict[x_qid]["title"],
                "m_question": q_dict[m_qid]["title"],
                "y_question": q_dict[y_qid]["title"],
                "indirect_within": res.get("level1_within_submodel", {}).get("indirect_effect"),
                "indirect_between": res.get("level2_between_submodel", {}).get("indirect_effect"),
                "is_conflated": res.get("conflation_test", {}).get("is_conflated"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/tmle", response_model=TMLEAnalysisOut)
def run_tmle_analysis(survey_id: str, payload: TMLEAnalysisRequest):
    """
    Ước lượng Tác động Nhân quả Mục tiêu (Targeted Maximum Likelihood Estimation - TMLE; van der Laan & Rose 2011).
    Ước lượng bán tham số bền vững kép (Doubly Robust) và đạt cận dưới hiệu quả Cramér-Rao.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_qid = payload.treatment_question_id
        y_qid = payload.outcome_question_id
        cov_qids = payload.covariate_question_ids

        all_qids = [t_qid, y_qid] + cov_qids
        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if t_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến can thiệp '{t_qid}'.")
        if y_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến kết quả '{y_qid}'.")

        for cid in cov_qids:
            if cid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến kiểm soát '{cid}'.")

        # Scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            raw_a = answers.get(t_qid)
            raw_y = answers.get(y_qid)
            if raw_a is None or raw_y is None:
                continue

            y_val = parse_num(raw_y)
            if y_val is None:
                continue

            row_dict = {
                t_qid: raw_a,
                y_qid: y_val
            }
            row_ok = True
            for cid in cov_qids:
                cv = parse_num(answers.get(cid))
                if cv is None:
                    row_ok = False
                    break
                row_dict[cid] = cv

            if row_ok:
                records.append(row_dict)

        if len(records) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ biến (cần tối thiểu 20 phản hồi)."
            }

        res = TMLEEngine.estimate_ate(
            records=records,
            treatment_field=t_qid,
            outcome_field=y_qid,
            covariate_fields=cov_qids,
            gbound=payload.gbound,
            target_treatment_val=payload.target_treatment_val,
            control_treatment_val=payload.control_treatment_val
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="TMLE_EVALUATED",
            details={
                "treatment_question": q_dict[t_qid]["title"],
                "outcome_question": q_dict[y_qid]["title"],
                "covariate_count": len(cov_qids),
                "tmle_ate": res.get("targeted_parameters", {}).get("targeted_tmle_ate"),
                "p_value": res.get("targeted_parameters", {}).get("p_value"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/sdid", response_model=SDIDAnalysisOut)
def run_sdid_analysis(survey_id: str, payload: SDIDAnalysisRequest):
    """
    Ước lượng Khác biệt Kép Tổng hợp (Synthetic Difference-in-Differences - SDID; Arkhangelsky et al. 2021).
    Kết hợp trọng số đơn vị (SCM) và trọng số thời gian, triệt tiêu thiên lệch xu hướng song song và biến động thời gian.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        u_qid = payload.unit_question_id
        t_qid = payload.time_question_id
        y_qid = payload.outcome_question_id

        all_qids = [u_qid, t_qid, y_qid]
        if len(set(all_qids)) < 3:
            raise HTTPException(status_code=400, detail="Ba biến số (Đơn vị, Mốc thời gian, Kết quả) phải là 3 câu hỏi phân biệt.")

        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        for qid in all_qids:
            if qid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi ID '{qid}' trong khảo sát.")

        # Scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            u_val = answers.get(u_qid)
            t_val = answers.get(t_qid)
            y_val = parse_num(answers.get(y_qid))

            if u_val is not None and t_val is not None and y_val is not None:
                records.append({
                    u_qid: str(u_val).strip(),
                    t_qid: t_val,
                    y_qid: y_val
                })

        if len(records) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ biến (cần tối thiểu 20 phản hồi)."
            }

        res = SDIDEngine.estimate(
            records=records,
            unit_field=u_qid,
            time_field=t_qid,
            outcome_field=y_qid,
            treated_units=payload.treated_units,
            treatment_start_time=payload.treatment_start_time,
            n_placebo_reps=payload.n_placebo_reps
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SDID_EVALUATED",
            details={
                "unit_question": q_dict[u_qid]["title"],
                "time_question": q_dict[t_qid]["title"],
                "outcome_question": q_dict[y_qid]["title"],
                "tau_sdid": res.get("sdid_estimates", {}).get("tau_sdid"),
                "p_value": res.get("sdid_estimates", {}).get("p_value"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/causal-forest", response_model=CausalForestAnalysisOut)
def run_causal_forest_analysis(survey_id: str, payload: CausalForestAnalysisRequest):
    """
    Phân tích Rừng Nhân quả Đa quát (Generalized Causal Forest - GRF; Athey, Tibshirani & Wager 2019).
    Ước lượng tác động nhân quả cá thể không đồng nhất (CATE), xếp hạng độ quan trọng biến số và phân khúc đối tượng.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_qid = payload.treatment_question_id
        y_qid = payload.outcome_question_id
        feat_qids = payload.feature_question_ids

        if not feat_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất một biến đặc trưng phân nhánh.")

        all_qids = [t_qid, y_qid] + feat_qids
        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if t_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến can thiệp '{t_qid}'.")
        if y_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến kết quả '{y_qid}'.")

        for fid in feat_qids:
            if fid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi đặc trưng '{fid}'.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            raw_a = answers.get(t_qid)
            raw_y = answers.get(y_qid)
            if raw_a is None or raw_y is None:
                continue

            y_val = parse_num(raw_y)
            if y_val is None:
                continue

            row_dict = {
                t_qid: raw_a,
                y_qid: y_val
            }
            row_ok = True
            for fid in feat_qids:
                fv = parse_num(answers.get(fid))
                if fv is None:
                    row_ok = False
                    break
                row_dict[fid] = fv

            if row_ok:
                records.append(row_dict)

        if len(records) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ biến (cần tối thiểu 25 phản hồi)."
            }

        res = CausalForestEngine.estimate_heterogeneity(
            records=records,
            treatment_field=t_qid,
            outcome_field=y_qid,
            feature_fields=feat_qids,
            n_trees=payload.n_trees,
            min_leaf_size=payload.min_leaf_size,
            target_treatment_val=payload.target_treatment_val
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CAUSAL_FOREST_EVALUATED",
            details={
                "treatment_question": q_dict[t_qid]["title"],
                "outcome_question": q_dict[y_qid]["title"],
                "feature_count": len(feat_qids),
                "ate_overall": res.get("cate_summary", {}).get("ate_overall"),
                "is_heterogeneous": res.get("cate_summary", {}).get("is_heterogeneous"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/causal-mediation-sensitivity", response_model=CausalMediationSensitivityOut)
def run_causal_mediation_sensitivity_analysis(survey_id: str, payload: CausalMediationSensitivityRequest):
    """
    Phân tích Trung gian Nhân quả & Kiểm định Độ nhạy với Nhiễu tiềm ẩn (Imai, Keele, Tingley 2010).
    Ước lượng ACME, ADE, Total Effect và khảo sát ngưỡng tương quan sai số rho* triệt tiêu hiệu ứng trung gian.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_qid = payload.treatment_question_id
        m_qid = payload.mediator_question_id
        y_qid = payload.outcome_question_id
        cov_qids = payload.covariate_question_ids or []

        all_qids = [t_qid, m_qid, y_qid] + cov_qids
        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if t_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến can thiệp '{t_qid}'.")
        if m_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến trung gian '{m_qid}'.")
        if y_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến kết quả '{y_qid}'.")

        for cid in cov_qids:
            if cid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi hiệp biến '{cid}'.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            raw_t = answers.get(t_qid)
            raw_m = answers.get(m_qid)
            raw_y = answers.get(y_qid)
            if raw_t is None or raw_m is None or raw_y is None:
                continue

            m_val = parse_num(raw_m)
            y_val = parse_num(raw_y)
            if m_val is None or y_val is None:
                continue

            row_dict = {
                t_qid: raw_t,
                m_qid: m_val,
                y_qid: y_val
            }
            row_ok = True
            for cid in cov_qids:
                cv = parse_num(answers.get(cid))
                if cv is None:
                    row_ok = False
                    break
                row_dict[cid] = cv

            if row_ok:
                records.append(row_dict)

        if len(records) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ biến (cần tối thiểu 20 phản hồi)."
            }

        res = run_causal_mediation_sensitivity(
            records=records,
            treatment_col=t_qid,
            mediator_col=m_qid,
            outcome_col=y_qid,
            covariate_cols=cov_qids,
            target_treatment_val=payload.target_treatment_val
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CAUSAL_MEDIATION_SENSITIVITY_EVALUATED",
            details={
                "treatment_question": q_dict[t_qid]["title"],
                "mediator_question": q_dict[m_qid]["title"],
                "outcome_question": q_dict[y_qid]["title"],
                "acme": res.get("baseline_effects", {}).get("acme"),
                "rho_tilde": res.get("sensitivity_analysis", {}).get("critical_rho_threshold"),
                "robustness": res.get("sensitivity_analysis", {}).get("robustness_level"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/dtw-clustering", response_model=DTWClusteringOut)
def run_dtw_clustering_analysis(survey_id: str, payload: DTWClusteringRequest):
    """
    Phân tích Phân cụm Quỹ đạo Thời gian bằng Dynamic Time Warping (DTW) & K-Medoids.
    Đồng chỉnh phi tuyến các chuỗi phản hồi theo làn sóng khảo sát, phát hiện các nhóm hình thái biến thiên đặc trưng.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        ts_qids = payload.time_series_question_ids
        if len(ts_qids) < 3:
            raise HTTPException(status_code=400, detail="Cần chọn tối thiểu 3 câu hỏi theo dõi thời gian/làn sóng.")

        placeholders = ",".join(["?"] * len(ts_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + ts_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        for qid in ts_qids:
            if qid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi thời gian '{qid}'.")

        labels = payload.time_labels or [q_dict[qid]["title"][:12] for qid in ts_qids]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(ts_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + ts_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            row_dict = {}
            row_ok = True
            for qid in ts_qids:
                v = parse_num(answers.get(qid))
                if v is None:
                    row_ok = False
                    break
                row_dict[qid] = v

            if row_ok:
                records.append(row_dict)

        if len(records) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ dữ liệu chuỗi thời gian (cần tối thiểu 15 phản hồi)."
            }

        res = run_dtw_trajectory_clustering(
            records=records,
            time_series_cols=ts_qids,
            time_labels=labels,
            n_clusters=payload.n_clusters,
            window_radius=payload.window_radius
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="DTW_TRAJECTORY_CLUSTERING_EVALUATED",
            details={
                "time_points_count": len(ts_qids),
                "n_clusters": payload.n_clusters,
                "silhouette_score": res.get("sample_diagnostics", {}).get("mean_silhouette_score"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/causal-tree", response_model=CausalTreeSubgroupOut)
def run_causal_tree_analysis(survey_id: str, payload: CausalTreeSubgroupRequest):
    """
    Phân tích Cây Tương Tác Nhân Quả & Phân Khúc Đối Tượng Trung Thực (Athey & Imbens 2016).
    Tự động phân tách cây quyết định tối ưu hóa phương sai hiệu ứng can thiệp và nhận diện các phân khúc phản hồi tích cực/tiêu cực.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_qid = payload.treatment_question_id
        y_qid = payload.outcome_question_id
        feat_qids = payload.feature_question_ids

        if not feat_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất một biến đặc trưng phân nhánh.")

        all_qids = [t_qid, y_qid] + feat_qids
        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        if t_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến can thiệp '{t_qid}'.")
        if y_qid not in q_dict:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi biến kết quả '{y_qid}'.")

        for fid in feat_qids:
            if fid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi đặc trưng '{fid}'.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            raw_t = answers.get(t_qid)
            raw_y = answers.get(y_qid)
            if raw_t is None or raw_y is None:
                continue

            y_val = parse_num(raw_y)
            if y_val is None:
                continue

            row_dict = {
                t_qid: raw_t,
                y_qid: y_val
            }
            row_ok = True
            for fid in feat_qids:
                fv = parse_num(answers.get(fid))
                if fv is None:
                    row_ok = False
                    break
                row_dict[fid] = fv

            if row_ok:
                records.append(row_dict)

        if len(records) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ biến (cần tối thiểu 30 phản hồi)."
            }

        res = run_causal_interaction_tree(
            records=records,
            treatment_col=t_qid,
            outcome_col=y_qid,
            feature_cols=feat_qids,
            max_depth=payload.max_depth,
            min_leaf_size=payload.min_leaf_size,
            target_treatment_val=payload.target_treatment_val
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CAUSAL_TREE_SUBGROUPS_EVALUATED",
            details={
                "treatment_question": q_dict[t_qid]["title"],
                "outcome_question": q_dict[y_qid]["title"],
                "subgroups_count": len(res.get("subgroups", [])),
                "ate_overall": res.get("sample_diagnostics", {}).get("ate_overall"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/multiple-testing-fdr", response_model=MultipleTestingFDROut)
def run_multiple_testing_fdr_analysis(survey_id: str, payload: MultipleTestingFDRRequest):
    """
    Kiểm soát Tỷ lệ Phát hiện Sai (False Discovery Rate - FDR) theo Benjamini & Hochberg (1995) và Benjamini & Yekutieli (2001).
    Hỗ trợ ma trận kiểm định lặp đa biến khảo sát hoặc danh sách các p-values tùy biến.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Mode A: Custom p-values list
        if payload.custom_p_values and len(payload.custom_p_values) > 0:
            res = compute_fdr_corrections(
                p_values=payload.custom_p_values,
                labels=payload.custom_labels,
                fdr_q=payload.fdr_q
            )
            record_audit_log(
                conn,
                entity_type="survey",
                entity_id=survey_id,
                action="MULTIPLE_TESTING_FDR_EVALUATED",
                details={
                    "mode": "custom_p_values",
                    "total_hypotheses": len(payload.custom_p_values),
                    "fdr_q": payload.fdr_q,
                    "bh_significant_count": res.get("sample_diagnostics", {}).get("bh_fdr_significant_count")
                }
            )
            return res

        # Mode B: Pairwise correlation matrix from question_ids
        q_ids = payload.question_ids
        if not q_ids or len(q_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="Cần cung cấp danh sách ít nhất 2 câu hỏi định lượng hoặc danh sách p-values tùy chọn."
            )

        placeholders = ",".join(["?"] * len(q_ids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + q_ids
        ).fetchall()
        q_dict = {q["id"]: q for q in q_rows}

        for qid in q_ids:
            if qid not in q_dict:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi '{qid}'.")

        q_titles = {qid: q_dict[qid]["title"] for qid in q_ids}

        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(q_ids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + q_ids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                if isinstance(val, str):
                    try:
                        p = json.loads(val)
                        if isinstance(p, (int, float)):
                            return float(p)
                        if isinstance(p, list) and len(p) > 0:
                            return float(p[0])
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                return None

        records = []
        for rid, answers in resp_map.items():
            row_dict = {}
            row_ok = True
            for qid in q_ids:
                v = parse_num(answers.get(qid))
                if v is None:
                    row_ok = False
                    break
                row_dict[qid] = v

            if row_ok:
                records.append(row_dict)

        if len(records) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ dữ liệu (cần tối thiểu 10 phản hồi)."
            }

        res = run_pairwise_fdr_matrix(
            records=records,
            question_ids=q_ids,
            question_titles=q_titles,
            fdr_q=payload.fdr_q
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MULTIPLE_TESTING_FDR_EVALUATED",
            details={
                "mode": "pairwise_survey_matrix",
                "questions_count": len(q_ids),
                "total_hypotheses": res.get("sample_diagnostics", {}).get("total_hypotheses_m"),
                "fdr_q": payload.fdr_q,
                "bh_significant_count": res.get("sample_diagnostics", {}).get("bh_fdr_significant_count"),
                "scope": payload.scope
            }
        )

        return res

# --- Bayesian Structural Equation Modeling (BSEM) (Muthén & Asparouhov 2012) ---
@router.post("/bsem", response_model=BSEMOut)
def run_bsem_analysis(survey_id: str, payload: BSEMRequest):
    """
    Executes full Bayesian Structural Equation Modeling (BSEM) with MCMC Gibbs Sampling.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Extract all needed question IDs from measurement_spec
        all_qids = []
        for f_name, qids in payload.measurement_spec.items():
            for qid in qids:
                if qid not in all_qids:
                    all_qids.append(qid)

        if len(all_qids) < 4:
            raise HTTPException(status_code=400, detail="Mô hình BSEM cần tối thiểu 4 biến quan sát.")

        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({','.join(['?']*len(all_qids))})",
            [survey_id] + all_qids
        ).fetchall()
        q_titles = {q["id"]: q["title"] for q in q_rows}

        # Fetch responses
        scope_clause = ""
        if payload.scope == "verified_clean":
            scope_clause = " AND is_flagged = 0 "

        resp_rows = conn.execute(
            f"SELECT id FROM responses WHERE survey_id = ? {scope_clause}",
            (survey_id,)
        ).fetchall()
        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_ph = ",".join(["?"] * len(resp_ids))
        q_ph = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"SELECT response_id, question_id, answer_value FROM response_answers WHERE response_id IN ({r_ph}) AND question_id IN ({q_ph})",
            (*resp_ids, *all_qids)
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num_bsem(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        records = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            row_ok = True
            for qid in all_qids:
                v = parse_num_bsem(r_ans.get(qid))
                if v is None:
                    row_ok = False
                    break
                row_dict[qid] = v
            if row_ok:
                records.append(row_dict)

        if len(records) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ dữ liệu (cần tối thiểu 20 phản hồi để chạy MCMC BSEM)."
            }

        res = compute_bsem_analysis(
            records=records,
            measurement_spec=payload.measurement_spec,
            structural_regressions=payload.structural_regressions,
            question_titles=q_titles,
            prior_cross_loading_sd=payload.prior_cross_loading_sd,
            n_iterations=payload.n_iterations,
            n_burnin=payload.n_burnin,
            n_chains=payload.n_chains
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="BSEM_EVALUATED",
            details={
                "factors_count": len(payload.measurement_spec),
                "items_count": len(all_qids),
                "n_observations": len(records),
                "prior_cross_loading_sd": payload.prior_cross_loading_sd,
                "ppp_value": res.get("sample_diagnostics", {}).get("posterior_predictive_p_value"),
                "scope": payload.scope
            }
        )

        return res

# --- Endogeneity Control via Gaussian Copula (Park & Gupta 2012) ---
@router.post("/gaussian-copula", response_model=GaussianCopulaOut)
def run_gaussian_copula_analysis(survey_id: str, payload: GaussianCopulaRequest):
    """
    Executes Park & Gupta (2012) Gaussian Copula Endogeneity Estimation without external instruments.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        p_qid = payload.endogenous_question_id
        y_qid = payload.outcome_question_id
        ctrl_qids = payload.control_question_ids or []
        all_qids = [p_qid, y_qid] + ctrl_qids

        q_placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({q_placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}

        if p_qid not in q_dict or y_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến nội sinh hoặc biến kết quả.")

        # Fetch responses
        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ? AND is_flagged = 0",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id FROM responses WHERE survey_id = ?",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        records = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            row_ok = True
            for qid in all_qids:
                num_v = parse_num(r_ans.get(qid))
                if num_v is None:
                    row_ok = False
                    break
                row_dict[qid] = num_v
            if row_ok:
                records.append(row_dict)

        if len(records) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ dữ liệu (cần tối thiểu 25 phản hồi để ước lượng Gaussian Copula)."
            }

        res = run_gaussian_copula_estimation(
            records=records,
            endogenous_var=p_qid,
            outcome_var=y_qid,
            control_vars=ctrl_qids,
            var_titles=q_dict,
            n_bootstraps=payload.n_bootstraps
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="GAUSSIAN_COPULA_EVALUATED",
            details={
                "endogenous_question_id": p_qid,
                "outcome_question_id": y_qid,
                "controls_count": len(ctrl_qids),
                "n_observations": len(records),
                "copula_rho": res.get("copula_corrected", {}).get("copula_rho_parameter"),
                "is_endogeneity_significant": res.get("copula_corrected", {}).get("is_endogeneity_significant"),
                "scope": payload.scope
            }
        )

        return res

# --- Dynamic Factor Modeling (DFM) with Kalman Filter & RTS Smoother (Stock & Watson 2002) ---
@router.post("/dynamic-factor", response_model=DynamicFactorModelOut)
def run_dynamic_factor_model_analysis(survey_id: str, payload: DynamicFactorModelRequest):
    """
    Executes Dynamic Factor Modeling (DFM) with Kalman Filter and RTS State-Space Smoothing.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        ind_qids = payload.indicator_question_ids
        wave_qid = payload.wave_question_id
        all_qids = list(ind_qids)
        if wave_qid and wave_qid not in all_qids:
            all_qids.append(wave_qid)

        if len(ind_qids) < 2:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 2 biến chỉ báo để phân tích nhân tố động.")

        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}

        # Fetch responses
        if payload.scope == "verified_clean":
            resp_rows = conn.execute(
                "SELECT id, submitted_at FROM responses WHERE survey_id = ? AND is_flagged = 0 ORDER BY submitted_at ASC",
                (survey_id,)
            ).fetchall()
        else:
            resp_rows = conn.execute(
                "SELECT id, submitted_at FROM responses WHERE survey_id = ? ORDER BY submitted_at ASC",
                (survey_id,)
            ).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "NO_RESPONSES",
                "message": "Không có phản hồi nào trong phạm vi khảo sát đã chọn."
            }

        r_placeholders = ",".join(["?"] * len(resp_ids))
        q_placeholders = ",".join(["?"] * len(all_qids))
        ans_rows = conn.execute(
            f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({r_placeholders})
              AND question_id IN ({q_placeholders})
            """,
            resp_ids + all_qids
        ).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        records = []
        for idx_r, r in enumerate(resp_rows):
            rid = r["id"]
            r_ans = resp_map[rid]
            row_dict = {}
            row_ok = True
            for qid in ind_qids:
                num_v = parse_num(r_ans.get(qid))
                if num_v is None:
                    row_ok = False
                    break
                row_dict[qid] = num_v

            if row_ok:
                if wave_qid and wave_qid in r_ans:
                    row_dict["wave"] = r_ans[wave_qid]
                else:
                    # Synthetic wave segmentation if no specific wave question (divide respondents into waves)
                    row_dict["wave"] = (idx_r // max(1, len(resp_rows) // 6)) + 1
                records.append(row_dict)

        if len(records) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(records)} phản hồi đầy đủ dữ liệu (cần tối thiểu 20 phản hồi để chạy mô hình nhân tố động)."
            }

        res = compute_dynamic_factor_analysis(
            records=records,
            indicator_question_ids=ind_qids,
            time_field="wave",
            indicator_titles=q_dict,
            n_factors=payload.n_factors
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="DYNAMIC_FACTOR_MODEL_EVALUATED",
            details={
                "indicators_count": len(ind_qids),
                "total_waves": res.get("sample_diagnostics", {}).get("total_waves_t"),
                "ar1_persistence": res.get("sample_diagnostics", {}).get("ar1_persistence"),
                "overall_signal_share": res.get("sample_diagnostics", {}).get("overall_signal_variance_share"),
                "scope": payload.scope
            }
        )

        return res

@router.post("/spatial-econometrics", response_model=SpatialEconometricsOut)
def run_spatial_econometrics_analysis(survey_id: str, payload: SpatialEconometricsRequest):
    """
    Spatial Econometrics & Moran\'s I Autoregressive Models (SAR / SEM; Anselin 1988, LeSage & Pace 2009).
    Kiểm định tự tương quan không gian Moran\'s I và ước lượng mô hình hồi quy lan tỏa không gian.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        outcome_qid = payload.outcome_question_id
        cov_qids = payload.covariate_question_ids or []
        all_qids = list(dict.fromkeys([outcome_qid] + cov_qids))

        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            (survey_id, *all_qids)
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}

        if outcome_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Biến kết quả không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id, client_metadata_json FROM responses
                WHERE survey_id = ? AND review_status NOT IN (\'verified_fraud\', \'quota_screened_out\')
                  AND (risk_level != \'high\' OR review_status = \'verified_valid\')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id, client_metadata_json FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không có phản hồi trong phạm vi được chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        resp_placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({resp_placeholders})
              AND question_id IN ({placeholders})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        data_rows = []
        for idx_r, r in enumerate(resp_rows):
            rid = r["id"]
            meta_raw = r["client_metadata_json"]
            pt = QualityEngine.extract_gps_point(meta_raw)

            r_ans = resp_map[rid]
            lat = None
            lon = None

            if pt:
                lat, lon = pt
            else:
                # Check if coordinates provided as answers to specific questions
                lat = parse_num(r_ans.get(payload.lat_field))
                lon = parse_num(r_ans.get(payload.lon_field))

            if lat is None or lon is None:
                continue

            row_dict = {"lat": float(lat), "lon": float(lon)}
            row_ok = True
            for qid in all_qids:
                num_v = parse_num(r_ans.get(qid))
                if num_v is None:
                    row_ok = False
                    break
                row_dict[qid] = num_v

            if row_ok:
                data_rows.append(row_dict)

        if len(data_rows) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi có tọa độ GPS và dữ liệu đầy đủ (cần tối thiểu 15 phản hồi để phân tích không gian)."
            }

        res = SpatialEconometricsEngine.analyze(
            data=data_rows,
            lat_field="lat",
            lon_field="lon",
            outcome_var=outcome_qid,
            covariate_vars=cov_qids,
            weights_type=payload.weights_type,
            knn_k=payload.knn_k,
            distance_power=payload.distance_power,
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SPATIAL_ECONOMETRICS_EVALUATED",
            details={
                "outcome_qid": outcome_qid,
                "n_samples": len(data_rows),
                "morans_i": res.get("morans_i", {}).get("morans_i"),
                "rho": res.get("spatial_lag_model", {}).get("rho"),
                "scope": payload.scope,
            }
        )

        return res

@router.post("/iv-quantile-regression", response_model=IVQuantileRegressionOut)
def run_iv_quantile_regression_analysis(survey_id: str, payload: IVQuantileRegressionRequest):
    """
    Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005, 2008).
    Ước lượng tác động nhân quả phân vị phi tuyến hiệu chỉnh nội sinh qua phương pháp nghịch đảo hồi quy phân vị.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        y_qid = payload.outcome_question_id
        d_qid = payload.treatment_question_id
        z_qid = payload.instrument_question_id
        cov_qids = payload.covariate_question_ids or []

        if not y_qid or not d_qid or not z_qid:
            raise HTTPException(status_code=400, detail="Thiếu biến kết quả Y, biến can thiệp D hoặc biến công cụ Z.")

        all_qids = list(dict.fromkeys([y_qid, d_qid, z_qid] + cov_qids))

        placeholders = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            (survey_id, *all_qids)
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}

        if y_qid not in q_dict or d_qid not in q_dict or z_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN (\'verified_fraud\', \'quota_screened_out\')
                  AND (risk_level != \'high\' OR review_status = \'verified_valid\')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không có phản hồi trong phạm vi được chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        resp_placeholders = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({resp_placeholders})
              AND question_id IN ({placeholders})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(val):
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            row_ok = True
            for qid in all_qids:
                num_v = parse_num(r_ans.get(qid))
                if num_v is None:
                    row_ok = False
                    break
                row_dict[qid] = num_v
            if row_ok:
                data_rows.append(row_dict)

        if len(data_rows) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi đầy đủ dữ liệu (cần tối thiểu 25 phản hồi để chạy IV-QR)."
            }

        res = IVQuantileRegressionEngine.analyze(
            data=data_rows,
            outcome_var=y_qid,
            treatment_var=d_qid,
            instrument_var=z_qid,
            covariate_vars=cov_qids,
            quantiles=payload.quantiles,
            grid_points=payload.grid_points,
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="IV_QUANTILE_REGRESSION_EVALUATED",
            details={
                "outcome_qid": y_qid,
                "treatment_qid": d_qid,
                "instrument_qid": z_qid,
                "n_samples": len(data_rows),
                "instrument_strength": res.get("summary", {}).get("instrument_strength"),
                "scope": payload.scope,
            }
        )

        return res

@router.post("/conjoint-hb", response_model=ConjointHBAnalysisOut)
def run_conjoint_hb_analysis(survey_id: str, payload: ConjointHBAnalysisRequest):
    """
    Choice-Based Conjoint (CBC) Analysis with Hierarchical Bayes (HB) Part-Worth Utilities (Rossi et al. 2005, McFadden 1974).
    Estimates individual-level preference parameters via Hybrid Gibbs / Metropolis-Hastings MCMC.
    Calculates Relative Attribute Importance (%), Willingness to Pay (WTP), and counterfactual market choice simulation.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        tasks_data = payload.tasks_data

        if not tasks_data:
            if payload.scope == "verified_clean":
                resp_rows = conn.execute("""
                    SELECT id FROM responses
                    WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                      AND (risk_level != 'high' OR review_status = 'verified_valid')
                """, (survey_id,)).fetchall()
            else:
                resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

            if not resp_rows:
                return {
                    "status": "INSUFFICIENT_SAMPLE",
                    "message": "Không tìm thấy phản hồi phù hợp với phạm vi khảo sát đã chọn."
                }

            resp_ids = [r["id"] for r in resp_rows]
            placeholders = ",".join(["?"] * len(resp_ids))

            ans_rows = conn.execute(f"""
                SELECT response_id, question_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders})
            """, tuple(resp_ids)).fetchall()

            ans_by_resp = {r: {} for r in resp_ids}
            for a in ans_rows:
                ans_by_resp[a["response_id"]][a["question_id"]] = a["answer_value"]

            constructed_tasks = []
            for rid, q_ans in ans_by_resp.items():
                attrs = {}
                for attr_name, qid in (payload.profile_attribute_mapping or {}).items():
                    if qid in q_ans:
                        attrs[attr_name] = str(q_ans[qid])

                for attr_name, levels in payload.attributes_config.items():
                    if attr_name not in attrs and levels:
                        attrs[attr_name] = levels[0]

                chosen_val = 1
                if payload.choice_question_id and payload.choice_question_id in q_ans:
                    val_str = str(q_ans[payload.choice_question_id]).strip().lower()
                    chosen_val = 1 if val_str in ["1", "true", "yes", "co", "chọn"] else 0

                constructed_tasks.append({
                    "respondent_id": rid,
                    "task_id": "task_1",
                    "attributes": attrs,
                    "chosen": chosen_val
                })

            tasks_data = constructed_tasks

        res = ConjointHBEngine.analyze_conjoint_hb(
            tasks_data=tasks_data,
            attributes_config=payload.attributes_config,
            price_attribute=payload.price_attribute,
            simulation_scenarios=payload.simulation_scenarios,
            n_draws=payload.n_draws,
            burn_in=payload.burn_in,
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONJOINT_HB_EVALUATED",
            details={
                "n_tasks": len(tasks_data) if tasks_data else 0,
                "n_attributes": len(payload.attributes_config),
                "price_attribute": payload.price_attribute,
                "status": res.get("status"),
                "scope": payload.scope,
            }
        )

        return res

@router.post("/fractional-response", response_model=FractionalResponseOut)
def run_fractional_response_analysis(survey_id: str, payload: FractionalResponseRequest):
    """
    Fractional Response Regression QMLE Engine (Papke & Wooldridge 1996, 2008).
    Estimates models for bounded survey outcomes y in [0, 1] or percentages with robust sandwich standard errors.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        y_qid = payload.outcome_question_id
        cov_qids = payload.covariate_question_ids
        if not cov_qids:
            raise HTTPException(status_code=400, detail="Cần chọn tối thiểu 1 biến giải thích.")

        if y_qid in cov_qids:
            raise HTTPException(status_code=400, detail="Biến kết quả không được nằm trong danh sách biến giải thích.")

        all_qids = [y_qid] + cov_qids
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không có phản hồi phù hợp trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        def parse_num(v: Any) -> Optional[float]:
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            row_ok = True
            for qid in all_qids:
                v = parse_num(r_ans.get(qid))
                if v is None:
                    row_ok = False
                    break
                row_dict[qid] = v
            if row_ok:
                data_rows.append(row_dict)

        if len(data_rows) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi đầy đủ dữ liệu (cần tối thiểu 15 quan sát)."
            }

        res = FractionalResponseEngine.estimate(
            data=data_rows,
            outcome_var=y_qid,
            covariate_vars=cov_qids,
            link=payload.link,
            scale_from_percentage=payload.scale_from_percentage
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="FRACTIONAL_RESPONSE_EVALUATED",
            details={
                "outcome_qid": y_qid,
                "covariate_qids": cov_qids,
                "link": payload.link,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "status": res.get("status")
            }
        )

        return res

@router.post("/mirt", response_model=MIRTAnalysisOut)
def run_mirt_analysis(survey_id: str, payload: MIRTAnalysisRequest):
    """
    Multidimensional Item Response Theory (MIRT; Reckase 2009) Compensatory M2PL Engine.
    Estimates multidimensional discrimination (MDISC), difficulty (MID), directional angles, and EAP trait scoring via MMLE-EM.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        item_qids = payload.item_question_ids
        if len(item_qids) < 3:
            raise HTTPException(status_code=400, detail="Cần chọn tối thiểu 3 câu hỏi để phân tích MIRT đa chiều.")

        placeholders_q = ",".join(["?"] * len(item_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *item_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(item_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *item_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            row_ok = True
            for qid in item_qids:
                v = r_ans.get(qid)
                if v is None or v == "":
                    row_ok = False
                    break
                row_dict[qid] = v
            if row_ok:
                data_rows.append(row_dict)

        if len(data_rows) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi đầy đủ dữ liệu (cần tối thiểu 20 phản hồi để ước lượng MIRT)."
            }

        res = MultidimensionalIRTEngine.estimate_mirt(
            data=data_rows,
            item_vars=item_qids,
            n_dimensions=payload.n_dimensions,
            dimension_names=payload.dimension_names,
            max_em_iter=payload.max_em_iter
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MIRT_MODEL_EVALUATED",
            details={
                "n_items": len(item_qids),
                "n_dimensions": payload.n_dimensions,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "status": res.get("status")
            }
        )

        return res

@router.post("/heckman-selection", response_model=HeckmanSelectionOut)
def run_heckman_selection_analysis(survey_id: str, payload: HeckmanSelectionRequest):
    """
    Heckman Two-Step Sample Selection Bias Correction Model (Heckman 1979 Nobel Prize).
    Corrects non-random selection bias via Probit Inverse Mills Ratio (IMR) with Heckman-Greene robust standard errors.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        y_qid = payload.outcome_question_id
        cov_qids = payload.outcome_covariate_question_ids
        sel_qid = payload.selection_indicator_question_id
        excl_qids = payload.exclusion_restriction_question_ids or []

        if not cov_qids:
            raise HTTPException(status_code=400, detail="Cần chọn tối thiểu 1 biến giải thích trong phương trình kết quả.")

        all_qids = [y_qid] + cov_qids + excl_qids
        if sel_qid and sel_qid not in all_qids:
            all_qids.append(sel_qid)

        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 25 phản hồi để ước lượng mô hình Heckman)."
            }

        res = HeckmanSelectionEngine.estimate(
            data=data_rows,
            selection_indicator_var=sel_qid if sel_qid else y_qid,
            outcome_var=y_qid,
            outcome_covariates=cov_qids,
            exclusion_restrictions=excl_qids
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="HECKMAN_SELECTION_EVALUATED",
            details={
                "outcome_qid": y_qid,
                "n_covariates": len(cov_qids),
                "n_exclusions": len(excl_qids),
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "has_selection_bias": res.get("diagnostics", {}).get("has_selection_bias"),
                "status": res.get("status")
            }
        )

        return res

@router.post("/stochastic-frontier", response_model=StochasticFrontierOut)
def run_stochastic_frontier_analysis(
    survey_id: str,
    payload: StochasticFrontierRequest
):
    """
    Ước lượng Mô hình Phân tích Biên Ngẫu nhiên (Stochastic Frontier Analysis - SFA)
    theo lý thuyết kinh tế lượng vi mô sản xuất (Aigner, Lovell & Schmidt 1977; Meeusen & van Den Broeck 1977; JLMS 1982).
    Phân rã sai số epsilon = v - u thành nhiễu ngẫu nhiên v ~ N(0, sigma_v^2)
    và độ kém hiệu quả kỹ thuật phi âm u ~ Half-Normal(0, sigma_u^2).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        y_qid = payload.output_question_id
        x_qids = payload.input_question_ids

        if not x_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 biến đầu vào (input/cost factors).")

        all_qids = [y_qid] + [qid for qid in x_qids if qid != y_qid]
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 20 phản hồi để ước lượng SFA)."
            }

        res = StochasticFrontierEngine.estimate(
            data=data_rows,
            output_var=y_qid,
            input_vars=x_qids,
            log_transform=payload.log_transform
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="STOCHASTIC_FRONTIER_ANALYSIS_EXECUTED",
            details={
                "output_qid": y_qid,
                "n_inputs": len(x_qids),
                "log_transform": payload.log_transform,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "status": res.get("status")
            }
        )

        return res

@router.post("/zero-inflated", response_model=ZeroInflatedOut)
def run_zero_inflated_analysis(
    survey_id: str,
    payload: ZeroInflatedRequest
):
    """
    Ước lượng Mô hình Hồi quy Đếm Đột biến Không (Zero-Inflated Poisson / Negative Binomial)
    theo Lambert (1992), Greene (1994) và kiểm định phi lồng ghép Vuong (1989).
    Phân tách quá trình tạo số liệu đếm thành hai trạng thái:
    - Trạng thái Đột biến Không (Structural Zero): Xác suất p_i xác định qua hàm Logit.
    - Trạng thái Phân phối Đếm: Poisson hoặc Negative Binomial (NB2) với kỳ vọng mu_i = exp(X_i beta).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        y_qid = payload.count_question_id
        x_qids = payload.covariate_question_ids
        z_qids = payload.inflation_covariate_question_ids or x_qids

        if not x_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 biến giải thích quá trình đếm (Count Covariates).")

        all_qids = list(set([y_qid] + x_qids + z_qids))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 25 phản hồi để ước lượng mô hình Zero-Inflated)."
            }

        res = ZeroInflatedEngine.estimate(
            data=data_rows,
            count_var=y_qid,
            covariates=x_qids,
            inflation_covariates=z_qids,
            model_type=payload.model_type
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="ZERO_INFLATED_MODEL_EVALUATED",
            details={
                "count_qid": y_qid,
                "n_covariates": len(x_qids),
                "n_inflation_covariates": len(z_qids),
                "model_type": payload.model_type,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "status": res.get("status")
            }
        )

        return res

@router.post("/latent-moderation", response_model=LatentModerationOut)
def run_latent_moderation_analysis(
    survey_id: str,
    payload: LatentModerationRequest
):
    """
    Ước lượng Mô hình Cấu trúc Biến Tiềm ẩn có Điều tiết (Latent Moderated Structural Equations - LMS)
    theo Klein & Moosbrugger (2000) và Klein & Muthén (2007).
    Khắc phục triệt để sai lệch suy giảm kích thước hiệu ứng tương tác (attenuation bias) do sai số đo lường.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        x1_qids = payload.predictor_item_ids
        x2_qids = payload.moderator_item_ids
        y_qids = payload.outcome_item_ids

        if not x1_qids or not x2_qids or not y_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 chỉ báo cho mỗi nhân tố (Độc lập, Điều tiết, Phụ thuộc).")

        all_qids = list(set(x1_qids + x2_qids + y_qids))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 30 phản hồi để ước lượng mô hình LMS)."
            }

        res = LatentModerationEngine.estimate(
            data=data_rows,
            predictor_items=x1_qids,
            moderator_items=x2_qids,
            outcome_items=y_qids
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LATENT_MODERATION_LMS_EVALUATED",
            details={
                "n_predictor_items": len(x1_qids),
                "n_moderator_items": len(x2_qids),
                "n_outcome_items": len(y_qids),
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "has_significant_moderation": res.get("diagnostics", {}).get("has_significant_moderation"),
                "status": res.get("status")
            }
        )

        return res

@router.post("/endogenous-switching", response_model=EndogenousSwitchingOut)
def run_endogenous_switching_analysis(
    survey_id: str,
    payload: EndogenousSwitchingRequest
):
    """
    Ước lượng Mô hình Hồi quy Chuyển đổi Nội sinh (Endogenous Switching Regression - ESR)
    bằng phương pháp Hợp lý Cực đại Toàn phần (Full Information Maximum Likelihood - FIML)
    theo Maddala (1983) và Lokshin & Sajaia (2004).
    Đo lường tác động xử lý nhân quả phản thực tế (ATT, ATU) khi có tự chọn lọc và cấu trúc sai số tương quan.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_qid = payload.treatment_question_id
        y_qid = payload.outcome_question_id
        x_qids = payload.covariate_question_ids
        z_qids = payload.instrument_question_ids or []

        if not x_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 biến giải thích cho phương trình kết quả (Covariates X).")

        all_qids = list(set([t_qid, y_qid] + x_qids + z_qids))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 30 phản hồi để ước lượng mô hình ESR)."
            }

        res = EndogenousSwitchingEngine.estimate(
            data=data_rows,
            treatment_var=t_qid,
            outcome_var=y_qid,
            covariates=x_qids,
            instruments=z_qids if len(z_qids) > 0 else None
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="ENDOGENOUS_SWITCHING_REGRESSION_EVALUATED",
            details={
                "treatment_qid": t_qid,
                "outcome_qid": y_qid,
                "n_covariates": len(x_qids),
                "n_instruments": len(z_qids),
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "att": res.get("treatment_effects", {}).get("att", {}).get("estimate"),
                "status": res.get("status")
            }
        )

        return res

@router.post("/gps-dose-response", response_model=GPSDoseResponseOut)
def run_gps_dose_response_analysis(
    survey_id: str,
    payload: GPSDoseResponseRequest
):
    """
    Ước lượng Điểm Xu hướng Tổng quát (Generalized Propensity Score - GPS)
    và Hàm Liều lượng - Phản hồi Causal (Continuous Treatment Dose-Response Function)
    theo Hirano & Imbens (2004) và Imai & van Dyk (2004).
    Đánh giá tác động nhân quả phi tuyến của can thiệp liên tục và đạo hàm tác động biên.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_qid = payload.treatment_question_id
        y_qid = payload.outcome_question_id
        x_qids = payload.covariate_question_ids

        if not x_qids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 biến kiểm soát gây nhiễu (Confounders X).")

        all_qids = list(set([t_qid, y_qid] + x_qids))
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            (survey_id, *all_qids)
        ).fetchall()
        found_qids = {r["id"] for r in q_rows}
        if len(found_qids) < len(all_qids):
            raise HTTPException(status_code=400, detail="Một hoặc nhiều câu hỏi không tồn tại trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r})
              AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        resp_map = {r: {} for r in resp_ids}
        for a in ans_rows:
            resp_map[a["response_id"]][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            r_ans = resp_map[rid]
            row_dict = {}
            for qid in all_qids:
                row_dict[qid] = r_ans.get(qid)
            data_rows.append(row_dict)

        if len(data_rows) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi (cần tối thiểu 25 phản hồi để ước lượng GPS)."
            }

        res = GPSDoseResponseEngine.estimate(
            data=data_rows,
            treatment_var=t_qid,
            outcome_var=y_qid,
            covariates=x_qids,
            n_grid_points=payload.n_grid_points
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="GPS_DOSE_RESPONSE_EVALUATED",
            details={
                "treatment_qid": t_qid,
                "outcome_qid": y_qid,
                "n_covariates": len(x_qids),
                "n_grid_points": payload.n_grid_points,
                "n_samples": len(data_rows),
                "scope": payload.scope,
                "optimal_dosage": res.get("diagnostics", {}).get("optimal_dosage_peak"),
                "status": res.get("status")
            }
        )

        return res

# --- Stochastic Dominance & Distributional Inequality (Davidson & Duclos 2000; Hadar & Russell 1969) ---
@router.post("/stochastic-dominance", response_model=StochasticDominanceOut)
def run_stochastic_dominance_analysis(
    survey_id: str,
    payload: StochasticDominanceRequest
):
    """
    Executes non-parametric First-, Second-, and Third-Order Stochastic Dominance Tests (FSD, SSD, TSD),
    Kolmogorov-Smirnov supremum statistics, Gini coefficient inequality profiling, and Lorenz curves.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        # Verify questions
        q_rows = conn.execute(
            "SELECT id, title, question_type, options_json FROM questions WHERE id IN (?, ?) AND survey_id = ?",
            (payload.outcome_question_id, payload.group_question_id, survey_id)
        ).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        if payload.outcome_question_id not in q_map or payload.group_question_id not in q_map:
            raise HTTPException(status_code=400, detail="Câu hỏi kết quả (Outcome) hoặc câu hỏi phân nhóm (Group) không tồn tại.")

        outcome_title = q_map[payload.outcome_question_id]["title"]
        group_title = q_map[payload.group_question_id]["title"]

        # Parse option labels if available
        opt_labels = {}
        try:
            opts = json.loads(q_map[payload.group_question_id]["options_json"] or "[]")
            for o in opts:
                if isinstance(o, dict):
                    opt_labels[str(o.get("value", ""))] = str(o.get("label", o.get("value", "")))
                    opt_labels[str(o.get("id", ""))] = str(o.get("label", o.get("id", "")))
        except Exception:
            pass

        # Filter scope
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r}) AND question_id IN (?, ?)
        """, (*resp_ids, payload.outcome_question_id, payload.group_question_id)).fetchall()

        data_by_resp = {}
        for row in ans_rows:
            rid = row["response_id"]
            qid = row["question_id"]
            val = row["answer_value"]
            if rid not in data_by_resp:
                data_by_resp[rid] = {}
            data_by_resp[rid][qid] = val

        # Collect paired responses
        pairs = []
        for rid, ans_dict in data_by_resp.items():
            if payload.outcome_question_id in ans_dict and payload.group_question_id in ans_dict:
                try:
                    out_val = float(ans_dict[payload.outcome_question_id])
                    grp_val = str(ans_dict[payload.group_question_id]).strip()
                    if grp_val:
                        pairs.append((out_val, grp_val))
                except (ValueError, TypeError):
                    continue

        if len(pairs) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(pairs)} phản hồi hợp lệ cho cả hai câu hỏi (yêu cầu tối thiểu 20)."
            }

        # Identify Group A and Group B values
        from collections import Counter
        grp_counts = Counter([p[1] for p in pairs])
        
        target_a = payload.group_a_value.strip() if payload.group_a_value else None
        target_b = payload.group_b_value.strip() if payload.group_b_value else None

        if not target_a or not target_b:
            common = grp_counts.most_common(2)
            if len(common) < 2:
                return {
                    "status": "INSUFFICIENT_SAMPLE",
                    "message": "Không tìm thấy đủ 2 nhóm phân loại khác nhau trong dữ liệu khảo sát."
                }
            target_a = target_a or common[0][0]
            target_b = target_b or common[1][0]

        vals_a = [p[0] for p in pairs if p[1] == target_a]
        vals_b = [p[0] for p in pairs if p[1] == target_b]

        lbl_a = payload.group_a_label or opt_labels.get(target_a, f"Nhóm {target_a}")
        lbl_b = payload.group_b_label or opt_labels.get(target_b, f"Nhóm {target_b}")

        import numpy as np
        res = StochasticDominanceEngine.evaluate_dominance(
            values_a=np.array(vals_a, dtype=float),
            values_b=np.array(vals_b, dtype=float),
            label_a=lbl_a,
            label_b=lbl_b,
            outcome_label=outcome_title,
            n_grid_points=max(20, min(100, payload.n_grid_points))
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="STOCHASTIC_DOMINANCE_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "group_qid": payload.group_question_id,
                "n_group_a": len(vals_a),
                "n_group_b": len(vals_b),
                "fsd_conclusion": res.get("diagnostics", {}).get("fsd_conclusion"),
                "ssd_conclusion": res.get("diagnostics", {}).get("ssd_conclusion"),
                "status": res.get("status")
            }
        )

        return res


# --- Manski Non-Parametric Partial Identification & Worst-Case Bounds (Manski 1990, 2000; Imbens & Manski 2004) ---
@router.post("/manski-bounds", response_model=ManskiBoundsOut)
def run_manski_bounds_analysis(
    survey_id: str,
    payload: ManskiBoundsRequest
):
    """
    Evaluates Manski Non-Parametric Partial Identification Bounds on Treatment Effects under missing/attrited survey data.
    Computes Worst-Case bounds, Monotone Treatment Selection (MTS), Monotone Treatment Response (MTR),
    Joint MTS+MTR bounds, Imbens-Manski (2004) uniform 95% confidence intervals, and Sign Breakdown Points.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        needed_qids = [payload.outcome_question_id, payload.treatment_question_id]
        if payload.response_indicator_question_id:
            needed_qids.append(payload.response_indicator_question_id)

        placeholders_q = ",".join(["?"] * len(needed_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type, options_json FROM questions WHERE id IN ({placeholders_q}) AND survey_id = ?",
            (*needed_qids, survey_id)
        ).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        if payload.outcome_question_id not in q_map or payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail="Câu hỏi kết quả (Outcome) hoặc câu hỏi can thiệp (Treatment) không tồn tại.")

        outcome_title = q_map[payload.outcome_question_id]["title"]
        treatment_title = q_map[payload.treatment_question_id]["title"]

        # Scope filter
        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r}) AND question_id IN ({placeholders_q})
        """, (*resp_ids, *needed_qids)).fetchall()

        data_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            rid = a["response_id"]
            qid = a["question_id"]
            data_by_resp[rid][qid] = a["answer_value"]

        # Treatment mapping
        treat_vals_raw = []
        for rid, ans_dict in data_by_resp.items():
            if payload.treatment_question_id in ans_dict and ans_dict[payload.treatment_question_id] is not None:
                tv = str(ans_dict[payload.treatment_question_id]).strip()
                if tv != "":
                    treat_vals_raw.append(tv)

        from collections import Counter
        t_counts = Counter(treat_vals_raw)
        top_two_t = [k for k, _ in t_counts.most_common(2)]
        if len(top_two_t) < 2:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Cần ít nhất 2 nhóm can thiệp khác nhau (Treatment vs Control) để ước lượng Manski bounds."
            }

        # Normalize treatment to 1 (treatment) and 0 (control)
        if "1" in top_two_t and "0" in top_two_t:
            treated_val = "1"
        else:
            treated_val = top_two_t[0]

        import numpy as np
        y_list = []
        d_list = []
        r_list = []

        for rid in resp_ids:
            ans_dict = data_by_resp.get(rid, {})
            t_raw = ans_dict.get(payload.treatment_question_id)
            if t_raw is None or str(t_raw).strip() not in top_two_t:
                continue

            d_i = 1 if str(t_raw).strip() == treated_val else 0

            # Response indicator
            if payload.response_indicator_question_id:
                resp_ind_raw = ans_dict.get(payload.response_indicator_question_id)
                r_i = 1 if str(resp_ind_raw).strip() in ("1", "true", "True", "yes", "Yes") else 0
            else:
                y_raw = ans_dict.get(payload.outcome_question_id)
                r_i = 1 if y_raw is not None and str(y_raw).strip() != "" else 0

            if r_i == 1:
                y_raw = ans_dict.get(payload.outcome_question_id)
                try:
                    y_val = float(y_raw)
                except (ValueError, TypeError):
                    r_i = 0
                    y_val = np.nan
            else:
                y_val = np.nan

            y_list.append(y_val)
            d_list.append(d_i)
            r_list.append(r_i)

        if len(y_list) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N={len(y_list)}) không đủ. Cần tối thiểu 20 quan sát."
            }

        res = ManskiBoundsEngine.evaluate_bounds(
            y_observed=np.array(y_list, dtype=float),
            d_treatment=np.array(d_list, dtype=int),
            r_response=np.array(r_list, dtype=int),
            support_min=payload.support_min,
            support_max=payload.support_max,
            confidence_level=payload.confidence_level,
            outcome_label=outcome_title,
            treatment_label=treatment_title
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MANSKI_BOUNDS_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "n_total": len(y_list),
                "worst_case_lb": res.get("diagnostics", {}).get("worst_case_lower"),
                "worst_case_ub": res.get("diagnostics", {}).get("worst_case_upper"),
                "joint_lb": res.get("diagnostics", {}).get("joint_mts_mtr_lower"),
                "joint_ub": res.get("diagnostics", {}).get("joint_mts_mtr_upper"),
                "status": res.get("status")
            }
        )

        return res


# --- Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine (Murphy 2003, Robins 2004) ---
@router.post("/dynamic-treatment-regimes", response_model=DynamicTreatmentRegimesOut)
def run_dynamic_treatment_regimes_analysis(
    survey_id: str,
    payload: DynamicTreatmentRegimesRequest
):
    """
    Evaluates multi-stage adaptive intervention policies (Dynamic Treatment Regimes - DTR)
    using Sequential Q-Learning Backward Induction (Murphy 2003; Robins 2004; Schulte et al. 2014).
    Estimates optimal tailoring thresholds, expected policy values V(d*), and policy value gain Delta V*.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        needed_qids = [
            payload.outcome_question_id,
            payload.stage1_action_question_id,
            payload.stage2_action_question_id,
            payload.baseline_covariate_question_id,
            payload.interim_state_question_id
        ]

        placeholders_q = ",".join(["?"] * len(needed_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE id IN ({placeholders_q}) AND survey_id = ?",
            (*needed_qids, survey_id)
        ).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        for qid in needed_qids:
            if qid not in q_map:
                raise HTTPException(status_code=400, detail=f"Câu hỏi với ID {qid} không tồn tại trong khảo sát.")

        out_title = q_map[payload.outcome_question_id]["title"]
        x1_title = q_map[payload.baseline_covariate_question_id]["title"]
        x2_title = q_map[payload.interim_state_question_id]["title"]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r}) AND question_id IN ({placeholders_q})
        """, (*resp_ids, *needed_qids)).fetchall()

        data_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            rid = a["response_id"]
            qid = a["question_id"]
            data_by_resp[rid][qid] = a["answer_value"]

        import numpy as np

        def parse_binary(val: Any) -> Optional[int]:
            if val is None:
                return None
            s = str(val).strip().lower()
            if s in ("1", "true", "yes", "có", "treatment", "can thiệp"):
                return 1
            if s in ("0", "false", "no", "không", "control", "đối chứng"):
                return 0
            try:
                num = float(s)
                return 1 if num >= 1.0 else 0
            except ValueError:
                return None

        y_list = []
        a1_list = []
        a2_list = []
        x1_list = []
        x2_list = []

        for rid in resp_ids:
            ans_dict = data_by_resp.get(rid, {})
            y_raw = ans_dict.get(payload.outcome_question_id)
            a1_raw = ans_dict.get(payload.stage1_action_question_id)
            a2_raw = ans_dict.get(payload.stage2_action_question_id)
            x1_raw = ans_dict.get(payload.baseline_covariate_question_id)
            x2_raw = ans_dict.get(payload.interim_state_question_id)

            if any(v is None for v in (y_raw, a1_raw, a2_raw, x1_raw, x2_raw)):
                continue

            try:
                y_val = float(y_raw)
                x1_val = float(x1_raw)
                x2_val = float(x2_raw)
                a1_val = parse_binary(a1_raw)
                a2_val = parse_binary(a2_raw)
                if a1_val is None or a2_val is None:
                    continue
                y_list.append(y_val)
                a1_list.append(a1_val)
                a2_list.append(a2_val)
                x1_list.append(x1_val)
                x2_list.append(x2_val)
            except (ValueError, TypeError):
                continue

        if len(y_list) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ đầy đủ hai giai đoạn (N={len(y_list)}) không đủ. Cần tối thiểu 25 quan sát."
            }

        res = DynamicTreatmentRegimesEngine.evaluate_dtr(
            y_outcome=np.array(y_list, dtype=float),
            a1_stage1=np.array(a1_list, dtype=int),
            a2_stage2=np.array(a2_list, dtype=int),
            x1_baseline=np.array(x1_list, dtype=float),
            x2_interim=np.array(x2_list, dtype=float),
            x1_label=x1_title,
            x2_label=x2_title,
            outcome_label=out_title
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="DYNAMIC_TREATMENT_REGIMES_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "n_samples": len(y_list),
                "v_optimal": res.get("diagnostics", {}).get("v_optimal"),
                "v_always": res.get("diagnostics", {}).get("v_always_treated"),
                "v_never": res.get("diagnostics", {}).get("v_never_treated"),
                "policy_gain": res.get("diagnostics", {}).get("policy_value_gain"),
                "status": res.get("status")
            }
        )

        return res


# --- Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine (Rost 1990; von Davier & Rost 2007) ---
@router.post("/finite-mixture-rasch", response_model=FiniteMixtureRaschOut)
def run_finite_mixture_rasch_analysis(
    survey_id: str,
    payload: FiniteMixtureRaschRequest
):
    """
    Evaluates Finite Mixture Rasch Models (FMRM) to identify latent classes of respondents
    exhibiting differential item functioning (DIF) and distinct psychometric response patterns
    via Expectation-Maximization (EM) algorithm (Rost 1990; von Davier & Rost 2007).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        if len(payload.question_ids) < 3:
            raise HTTPException(status_code=400, detail="Cần chọn tối thiểu 3 câu hỏi để phân tích Rasch hỗn hợp.")

        placeholders_q = ",".join(["?"] * len(payload.question_ids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE id IN ({placeholders_q}) AND survey_id = ?",
            (*payload.question_ids, survey_id)
        ).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        for qid in payload.question_ids:
            if qid not in q_map:
                raise HTTPException(status_code=400, detail=f"Câu hỏi với ID {qid} không tồn tại trong khảo sát.")

        item_titles = [q_map[qid]["title"] for qid in payload.question_ids]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r}) AND question_id IN ({placeholders_q})
        """, (*resp_ids, *payload.question_ids)).fetchall()

        data_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            rid = a["response_id"]
            qid = a["question_id"]
            data_by_resp[rid][qid] = a["answer_value"]

        import numpy as np

        # Convert to binary matrix
        # For each question, inspect values to decide threshold
        q_vals_all: Dict[str, List[float]] = {qid: [] for qid in payload.question_ids}
        for rid, ans_dict in data_by_resp.items():
            for qid in payload.question_ids:
                v_raw = ans_dict.get(qid)
                if v_raw is not None:
                    try:
                        q_vals_all[qid].append(float(v_raw))
                    except (ValueError, TypeError):
                        pass

        q_thresholds = {}
        for qid in payload.question_ids:
            arr = q_vals_all[qid]
            if len(arr) > 0:
                mx = max(arr)
                mn = min(arr)
                if mx > 1.0:
                    # Likert 1-5 or 1-10 -> midpoint
                    q_thresholds[qid] = 0.5 * (mn + mx)
                else:
                    q_thresholds[qid] = 0.5
            else:
                q_thresholds[qid] = 0.5

        valid_rows = []
        for rid in resp_ids:
            ans_dict = data_by_resp.get(rid, {})
            row = []
            has_missing = False
            for qid in payload.question_ids:
                v_raw = ans_dict.get(qid)
                if v_raw is None or str(v_raw).strip() == "":
                    has_missing = True
                    break
                try:
                    num_val = float(v_raw)
                    bin_val = 1 if num_val >= q_thresholds[qid] else 0
                except (ValueError, TypeError):
                    s = str(v_raw).strip().lower()
                    bin_val = 1 if s in ("1", "true", "yes", "đồng ý", "agree", "có") else 0
                row.append(bin_val)

            if not has_missing and len(row) == len(payload.question_ids):
                valid_rows.append(row)

        if len(valid_rows) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi trả lời đầy đủ tất cả câu hỏi (N={len(valid_rows)}) không đủ. Cần tối thiểu 30 quan sát."
            }

        mat = np.array(valid_rows, dtype=int)
        res = FiniteMixtureRaschEngine.evaluate_fmrm(
            responses_matrix=mat,
            item_labels=item_titles,
            n_classes=payload.n_classes
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="FINITE_MIXTURE_RASCH_EVALUATED",
            details={
                "n_items": len(payload.question_ids),
                "n_classes": payload.n_classes,
                "n_samples": len(valid_rows),
                "entropy": res.get("diagnostics", {}).get("entropy"),
                "log_likelihood": res.get("diagnostics", {}).get("log_likelihood"),
                "status": res.get("status")
            }
        )

        return res


# --- Double / Debiased Machine Learning (DML) for Causal Inference (Chernozhukov et al. 2018) ---
@router.post("/double-machine-learning", response_model=DoubleMachineLearningOut)
def run_double_machine_learning_analysis(
    survey_id: str,
    payload: DoubleMachineLearningRequest
):
    """
    Evaluates causal treatment effects in high-dimensional partially linear models (PLR)
    using Double/Debiased Machine Learning (DML) with Neyman-orthogonal scores and K-fold cross-fitting
    (Chernozhukov et al. 2018; Robinson 1988).
    Eliminates regularization bias and delivers valid sqrt(N)-consistent confidence intervals.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc khảo sát.")

        if not payload.covariate_question_ids:
            raise HTTPException(status_code=400, detail="Cần chọn ít nhất 1 biến kiểm soát để khử thiên lệch bằng DML.")

        all_qids = [payload.outcome_question_id, payload.treatment_question_id] + payload.covariate_question_ids
        placeholders_q = ",".join(["?"] * len(all_qids))
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE id IN ({placeholders_q}) AND survey_id = ?",
            (*all_qids, survey_id)
        ).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        if payload.outcome_question_id not in q_map or payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail="Câu hỏi kết quả (Outcome) hoặc câu hỏi can thiệp (Treatment) không tồn tại.")

        outcome_title = q_map[payload.outcome_question_id]["title"]
        treatment_title = q_map[payload.treatment_question_id]["title"]
        cov_titles = [q_map[qid]["title"] for qid in payload.covariate_question_ids if qid in q_map]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ? AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()

        if not resp_rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Không tìm thấy phản hồi trong phạm vi khảo sát đã chọn."}

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_r = ",".join(["?"] * len(resp_ids))

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_r}) AND question_id IN ({placeholders_q})
        """, (*resp_ids, *all_qids)).fetchall()

        data_by_resp: Dict[str, Dict[str, Any]] = {rid: {} for rid in resp_ids}
        for a in ans_rows:
            rid = a["response_id"]
            qid = a["question_id"]
            data_by_resp[rid][qid] = a["answer_value"]

        import numpy as np

        y_list = []
        d_list = []
        x_list = []

        for rid in resp_ids:
            ans_dict = data_by_resp.get(rid, {})
            y_raw = ans_dict.get(payload.outcome_question_id)
            d_raw = ans_dict.get(payload.treatment_question_id)

            if y_raw is None or d_raw is None:
                continue

            try:
                y_val = float(y_raw)
            except (ValueError, TypeError):
                continue

            # Treatment numeric or binary parse
            try:
                d_val = float(d_raw)
            except (ValueError, TypeError):
                s = str(d_raw).strip().lower()
                if s in ("1", "true", "yes", "treatment", "can thiệp", "có"):
                    d_val = 1.0
                elif s in ("0", "false", "no", "control", "đối chứng", "không"):
                    d_val = 0.0
                else:
                    continue

            # Covariates
            row_x = []
            has_missing_cov = False
            for qid in payload.covariate_question_ids:
                c_raw = ans_dict.get(qid)
                if c_raw is None or str(c_raw).strip() == "":
                    has_missing_cov = True
                    break
                try:
                    row_x.append(float(c_raw))
                except (ValueError, TypeError):
                    has_missing_cov = True
                    break

            if not has_missing_cov and len(row_x) == len(payload.covariate_question_ids):
                y_list.append(y_val)
                d_list.append(d_val)
                x_list.append(row_x)

        if len(y_list) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ đầy đủ biến (N={len(y_list)}) không đủ. Cần tối thiểu 30 quan sát."
            }

        res = DoubleMachineLearningEngine.evaluate_dml(
            y_outcome=np.array(y_list, dtype=float),
            d_treatment=np.array(d_list, dtype=float),
            x_covariates=np.array(x_list, dtype=float),
            covariate_names=cov_titles,
            n_folds=payload.n_folds,
            alpha_penalty=payload.alpha_penalty,
            outcome_label=outcome_title,
            treatment_label=treatment_title
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="DOUBLE_MACHINE_LEARNING_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "n_covariates": len(payload.covariate_question_ids),
                "n_samples": len(y_list),
                "theta_dml": res.get("diagnostics", {}).get("theta_dml"),
                "p_value": res.get("diagnostics", {}).get("p_value"),
                "status": res.get("status")
            }
        )

        return res


# --- Regression Kink Design (Card, Lee, Pei, and Weber 2015; Dong 2018) ---
@router.post("/regression-kink", response_model=RegressionKinkOut)
def run_regression_kink_analysis(
    survey_id: str,
    payload: RegressionKinkRequest
):
    """
    Regression Kink Design (RKD) Engine (Card, Lee, Pei, and Weber 2015; Dong 2018).
    Identifies causal derivative policy effects when treatment intensity or probability
    changes slope at a known cutoff threshold.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (QID: {payload.outcome_question_id}) không tồn tại.")
        if payload.running_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến gán chạy (Running Variable QID: {payload.running_question_id}) không tồn tại.")

        if payload.treatment_question_id is not None and payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến xử lý (Treatment QID: {payload.treatment_question_id}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [payload.outcome_question_id, payload.running_question_id]
        if payload.treatment_question_id is not None:
            target_qids.append(payload.treatment_question_id)

        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data: Dict[int, Dict[int, str]] = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        y_list = []
        x_list = []
        d_list = []

        for resp_id, answers in resp_data.items():
            if payload.outcome_question_id not in answers or payload.running_question_id not in answers:
                continue
            try:
                y_val = float(answers[payload.outcome_question_id])
                x_val = float(answers[payload.running_question_id])
            except (ValueError, TypeError):
                continue

            d_val = None
            if payload.treatment_question_id is not None:
                if payload.treatment_question_id not in answers:
                    continue
                try:
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

            y_list.append(y_val)
            x_list.append(x_val)
            if d_val is not None:
                d_list.append(d_val)

        if len(y_list) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N={len(y_list)}) không đủ cho hồi quy RKD. Cần tối thiểu 20 quan sát.",
                "model_type": "Sharp RKD" if payload.treatment_question_id is None else "Fuzzy RKD",
                "diagnostics": None,
                "binned_scatter": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        d_arr = np.array(d_list, dtype=float) if (payload.treatment_question_id is not None and len(d_list) == len(y_list)) else None

        res = RegressionKinkEngine.evaluate_rkd(
            y_outcome=np.array(y_list, dtype=float),
            x_running=np.array(x_list, dtype=float),
            cutoff=payload.cutoff,
            d_treatment=d_arr,
            bandwidth=payload.bandwidth,
            polynomial_order=payload.polynomial_order,
            known_kink_slope=payload.known_kink_slope,
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả"),
            running_label=q_map.get(payload.running_question_id, "Biến gán chạy"),
            treatment_label=q_map.get(payload.treatment_question_id, "Biến can thiệp") if payload.treatment_question_id else "Chính sách can thiệp"
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="REGRESSION_KINK_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "running_qid": payload.running_question_id,
                "cutoff": payload.cutoff,
                "is_fuzzy": payload.treatment_question_id is not None,
                "n_samples": len(y_list),
                "tau_rkd": res.get("diagnostics", {}).get("tau_rkd") if res.get("diagnostics") else None,
                "p_value": res.get("diagnostics", {}).get("p_value") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


# --- Staggered Difference-in-Differences & Group-Time ATT (Callaway & Sant'Anna 2021; Goodman-Bacon 2021) ---
@router.post("/staggered-did", response_model=StaggeredDIDOut)
def run_staggered_did_analysis(
    survey_id: str,
    payload: StaggeredDIDRequest
):
    """
    Staggered Difference-in-Differences Engine (Callaway & Sant'Anna 2021; Goodman-Bacon 2021).
    Evaluates group-time treatment effects ATT(g,t) and Goodman-Bacon decomposition
    without TWFE negative weighting bias.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (QID: {payload.outcome_question_id}) không tồn tại.")
        if payload.unit_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến đơn vị quan sát (Unit QID: {payload.unit_question_id}) không tồn tại.")
        if payload.time_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến mốc thời gian (Time QID: {payload.time_question_id}) không tồn tại.")
        if payload.treatment_timing_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến thời điểm can thiệp (Timing QID: {payload.treatment_timing_question_id}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [
            payload.outcome_question_id,
            payload.unit_question_id,
            payload.time_question_id,
            payload.treatment_timing_question_id
        ]
        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data: Dict[int, Dict[int, str]] = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        y_list = []
        u_list = []
        t_list = []
        g_list = []

        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.unit_question_id not in answers or
                payload.time_question_id not in answers or
                payload.treatment_timing_question_id not in answers):
                continue

            try:
                y_val = float(answers[payload.outcome_question_id])
                u_val = str(answers[payload.unit_question_id]).strip()
                t_val = float(answers[payload.time_question_id])
                g_raw = answers[payload.treatment_timing_question_id]
                try:
                    g_val = float(g_raw)
                except (ValueError, TypeError):
                    g_val = 0.0
            except (ValueError, TypeError):
                continue

            y_list.append(y_val)
            u_list.append(u_val)
            t_list.append(t_val)
            g_list.append(g_val)

        if len(y_list) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N={len(y_list)}) không đủ cho Staggered DiD. Cần tối thiểu 20 quan sát.",
                "model_type": "STAGGERED_DID_CALLAWAY_SANTANNA_2021",
                "diagnostics": None,
                "group_time_effects": None,
                "event_study_effects": None,
                "bacon_decomposition": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        res = StaggeredDIDEngine.evaluate_staggered_did(
            y_outcome=np.array(y_list, dtype=float),
            unit_ids=np.array(u_list),
            time_periods=np.array(t_list, dtype=float),
            first_treated_periods=np.array(g_list, dtype=float),
            anticipation_periods=payload.anticipation_periods or 0,
            control_group_type=payload.control_group_type or "never_treated",
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả"),
            unit_label=q_map.get(payload.unit_question_id, "Đơn vị khảo sát"),
            time_label=q_map.get(payload.time_question_id, "Mốc thời gian")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="STAGGERED_DID_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "unit_qid": payload.unit_question_id,
                "time_qid": payload.time_question_id,
                "timing_qid": payload.treatment_timing_question_id,
                "n_samples": len(y_list),
                "overall_att": res.get("diagnostics", {}).get("overall_att") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


# --- Matrix Completion for Causal Panel Data (Athey, Bayati, Doudchenko, Imbens, & Khosravi 2021) ---
@router.post("/matrix-completion-causal", response_model=MatrixCompletionCausalOut)
def run_matrix_completion_causal_analysis(
    survey_id: str,
    payload: MatrixCompletionCausalRequest
):
    """
    Matrix Completion for Causal Panel Data Engine (Athey et al. 2021).
    Imputes unobserved counterfactual entries Y(0) via Soft-Impute nuclear norm regularization.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (QID: {payload.outcome_question_id}) không tồn tại.")
        if payload.unit_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến đơn vị quan sát (Unit QID: {payload.unit_question_id}) không tồn tại.")
        if payload.time_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến mốc thời gian (Time QID: {payload.time_question_id}) không tồn tại.")
        if payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến can thiệp (Treatment QID: {payload.treatment_question_id}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [
            payload.outcome_question_id,
            payload.unit_question_id,
            payload.time_question_id,
            payload.treatment_question_id
        ]
        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data: Dict[int, Dict[int, str]] = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        y_list = []
        u_list = []
        t_list = []
        w_list = []

        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.unit_question_id not in answers or
                payload.time_question_id not in answers or
                payload.treatment_question_id not in answers):
                continue

            try:
                y_val = float(answers[payload.outcome_question_id])
                u_val = str(answers[payload.unit_question_id]).strip()
                t_val = float(answers[payload.time_question_id])
                w_raw = answers[payload.treatment_question_id]
                try:
                    w_val = float(w_raw)
                except (ValueError, TypeError):
                    w_val = 1.0 if str(w_raw).strip() in ["1", "true", "True", "yes", "treated"] else 0.0
            except (ValueError, TypeError):
                continue

            y_list.append(y_val)
            u_list.append(u_val)
            t_list.append(t_val)
            w_list.append(w_val)

        if len(y_list) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N={len(y_list)}) không đủ cho Matrix Completion. Cần tối thiểu 20 quan sát dạng bảng.",
                "model_type": "CAUSAL_MATRIX_COMPLETION_ATHEY_2021",
                "diagnostics": None,
                "cell_treatment_effects": None,
                "singular_value_spectrum": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        res = MatrixCompletionCausalEngine.evaluate_matrix_completion(
            y_matrix_flat=np.array(y_list, dtype=float),
            unit_indices=np.array(u_list),
            time_indices=np.array(t_list, dtype=float),
            treatment_indicator=np.array(w_list, dtype=float),
            lambda_penalty=payload.lambda_penalty,
            max_rank=payload.max_rank or 5,
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả"),
            unit_label=q_map.get(payload.unit_question_id, "Đơn vị quan sát"),
            time_label=q_map.get(payload.time_question_id, "Mốc thời gian")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MATRIX_COMPLETION_CAUSAL_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "unit_qid": payload.unit_question_id,
                "time_qid": payload.time_question_id,
                "treatment_qid": payload.treatment_question_id,
                "n_samples": len(y_list),
                "overall_att": res.get("diagnostics", {}).get("overall_att") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


# --- Synthetic Difference-in-Differences (Arkhangelsky, Athey, Hirshberg, Imbens, & Wager 2021) ---
@router.post("/sdid-advanced", response_model=SDIDAdvancedOut)
def run_sdid_advanced_analysis(
    survey_id: str,
    payload: SDIDAdvancedRequest
):
    """
    Synthetic Difference-in-Differences (SDID) Engine (Arkhangelsky et al. 2021).
    Combines unit weights, time weights, and two-way fixed effects for double-robust causal inference.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (QID: {payload.outcome_question_id}) không tồn tại.")
        if payload.unit_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến đơn vị quan sát (Unit QID: {payload.unit_question_id}) không tồn tại.")
        if payload.time_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến mốc thời gian (Time QID: {payload.time_question_id}) không tồn tại.")
        if payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến can thiệp (Treatment QID: {payload.treatment_question_id}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [
            payload.outcome_question_id,
            payload.unit_question_id,
            payload.time_question_id,
            payload.treatment_question_id
        ]
        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data: Dict[int, Dict[int, str]] = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        y_list = []
        u_list = []
        t_list = []
        w_list = []

        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.unit_question_id not in answers or
                payload.time_question_id not in answers or
                payload.treatment_question_id not in answers):
                continue

            try:
                y_val = float(answers[payload.outcome_question_id])
                u_val = str(answers[payload.unit_question_id]).strip()
                t_val = float(answers[payload.time_question_id])
                w_raw = answers[payload.treatment_question_id]
                try:
                    w_val = float(w_raw)
                except (ValueError, TypeError):
                    w_val = 1.0 if str(w_raw).strip() in ["1", "true", "True", "yes", "treated"] else 0.0
            except (ValueError, TypeError):
                continue

            y_list.append(y_val)
            u_list.append(u_val)
            t_list.append(t_val)
            w_list.append(w_val)

        if len(y_list) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N={len(y_list)}) không đủ cho SDID. Cần tối thiểu 20 quan sát dạng bảng.",
                "model_type": "SYNTHETIC_DID_ARKHANGELSKY_2021",
                "diagnostics": None,
                "unit_weights": None,
                "time_weights": None,
                "trajectories": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        res = SDIDAdvancedEngine.evaluate_sdid(
            y_matrix_flat=np.array(y_list, dtype=float),
            unit_indices=np.array(u_list),
            time_indices=np.array(t_list, dtype=float),
            treatment_indicator=np.array(w_list, dtype=float),
            zeta_regularization=payload.zeta_regularization,
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả"),
            unit_label=q_map.get(payload.unit_question_id, "Đơn vị quan sát"),
            time_label=q_map.get(payload.time_question_id, "Mốc thời gian")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SDID_ADVANCED_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "unit_qid": payload.unit_question_id,
                "time_qid": payload.time_question_id,
                "treatment_qid": payload.treatment_question_id,
                "n_samples": len(y_list),
                "tau_sdid": res.get("diagnostics", {}).get("tau_sdid") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


# --- Interactive Fixed Effects (Bai 2009; Gobillon & Magnac 2016) ---
@router.post("/interactive-fixed-effects", response_model=InteractiveFixedEffectsOut)
def run_interactive_fixed_effects_analysis(
    survey_id: str,
    payload: InteractiveFixedEffectsRequest
):
    """
    Interactive Fixed Effects (IFE) Causal Panel Engine (Bai 2009; Gobillon & Magnac 2016).
    Estimates causal treatment effects under multi-dimensional latent factors and cross-sectional dependence.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (QID: {payload.outcome_question_id}) không tồn tại.")
        if payload.unit_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến đơn vị quan sát (Unit QID: {payload.unit_question_id}) không tồn tại.")
        if payload.time_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến mốc thời gian (Time QID: {payload.time_question_id}) không tồn tại.")
        if payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến can thiệp (Treatment QID: {payload.treatment_question_id}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [
            payload.outcome_question_id,
            payload.unit_question_id,
            payload.time_question_id,
            payload.treatment_question_id
        ]
        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        records = []
        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.unit_question_id not in answers or
                payload.time_question_id not in answers or
                payload.treatment_question_id not in answers):
                continue

            records.append({
                "y": answers[payload.outcome_question_id],
                "u": answers[payload.unit_question_id],
                "t": answers[payload.time_question_id],
                "w": answers[payload.treatment_question_id]
            })

        res = compute_interactive_fixed_effects(
            records=records,
            outcome_key="y",
            unit_key="u",
            time_key="t",
            treatment_key="w",
            num_factors=payload.num_factors,
            max_factors=payload.max_factors
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="INTERACTIVE_FIXED_EFFECTS_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "unit_qid": payload.unit_question_id,
                "time_qid": payload.time_question_id,
                "treatment_qid": payload.treatment_question_id,
                "n_records": len(records),
                "tau_ife": res.get("diagnostics", {}).get("tau_ife") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


# --- Multiple Sequential Mediators (VanderWeele 2014; Steen et al. 2012) ---
@router.post("/multiple-mediators", response_model=MultipleMediatorsOut)
def run_multiple_mediators_analysis(
    survey_id: str,
    payload: MultipleMediatorsRequest
):
    """
    Multiple Sequential Mediators & Path-Specific Causal Mediation Engine (VanderWeele 2014; Steen et al. 2012).
    Decomposes total causal effect into pure direct effect and sequential indirect effects.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến can thiệp (X QID: {payload.treatment_question_id}) không tồn tại.")
        if payload.mediator1_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến trung gian 1 (M1 QID: {payload.mediator1_question_id}) không tồn tại.")
        if payload.mediator2_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến trung gian 2 (M2 QID: {payload.mediator2_question_id}) không tồn tại.")
        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (Y QID: {payload.outcome_question_id}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [
            payload.treatment_question_id,
            payload.mediator1_question_id,
            payload.mediator2_question_id,
            payload.outcome_question_id
        ]
        cov_ids = payload.covariate_question_ids or []
        for cid in cov_ids:
            if cid in q_map and cid not in target_qids:
                target_qids.append(cid)

        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        x_list, m1_list, m2_list, y_list = [], [], [], []
        cov_lists = [[] for _ in cov_ids]

        for resp_id, answers in resp_data.items():
            if (payload.treatment_question_id not in answers or
                payload.mediator1_question_id not in answers or
                payload.mediator2_question_id not in answers or
                payload.outcome_question_id not in answers):
                continue

            try:
                xv = float(answers[payload.treatment_question_id])
                m1v = float(answers[payload.mediator1_question_id])
                m2v = float(answers[payload.mediator2_question_id])
                yv = float(answers[payload.outcome_question_id])

                row_covs = []
                has_all_covs = True
                for c_idx, cid in enumerate(cov_ids):
                    if cid in answers:
                        row_covs.append(float(answers[cid]))
                    else:
                        has_all_covs = False
                        break

                if not has_all_covs and len(cov_ids) > 0:
                    continue

                x_list.append(xv)
                m1_list.append(m1v)
                m2_list.append(m2v)
                y_list.append(yv)
                for c_idx, val in enumerate(row_covs):
                    cov_lists[c_idx].append(val)
            except (ValueError, TypeError):
                continue

        cov_matrix = np.column_stack(cov_lists) if len(cov_ids) > 0 and len(x_list) > 0 else None

        res = MultipleMediatorsEngine.evaluate(
            x=np.array(x_list, dtype=float),
            m1=np.array(m1_list, dtype=float),
            m2=np.array(m2_list, dtype=float),
            y=np.array(y_list, dtype=float),
            covariates=cov_matrix,
            n_bootstraps=payload.n_bootstraps,
            x_label=q_map.get(payload.treatment_question_id, "Biến can thiệp X"),
            m1_label=q_map.get(payload.mediator1_question_id, "Biến trung gian M1"),
            m2_label=q_map.get(payload.mediator2_question_id, "Biến trung gian M2"),
            y_label=q_map.get(payload.outcome_question_id, "Biến kết quả Y")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MULTIPLE_MEDIATORS_EVALUATED",
            details={
                "treatment_qid": payload.treatment_question_id,
                "mediator1_qid": payload.mediator1_question_id,
                "mediator2_qid": payload.mediator2_question_id,
                "outcome_qid": payload.outcome_question_id,
                "n_samples": len(x_list),
                "total_effect": res.get("diagnostics", {}).get("total_effect") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


# --- Doubly Robust Policy Learning (Athey & Wager 2021) ---
@router.post("/policy-learning", response_model=PolicyLearningOut)
def run_policy_learning_analysis(
    survey_id: str,
    payload: PolicyLearningRequest
):
    """
    Doubly Robust Policy Learning & Optimal Treatment Regimes Engine (Athey & Wager 2021).
    Estimates optimal individualized treatment rule pi*(X) and net policy welfare gain.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (Y QID: {payload.outcome_question_id}) không tồn tại.")
        if payload.treatment_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến can thiệp (W QID: {payload.treatment_question_id}) không tồn tại.")

        cov_ids = payload.covariate_question_ids or []
        for cid in cov_ids:
            if cid not in q_map:
                raise HTTPException(status_code=400, detail=f"Biến đặc tính (Covariate QID: {cid}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [payload.outcome_question_id, payload.treatment_question_id] + cov_ids
        target_qids = list(dict.fromkeys(target_qids))

        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        y_list = []
        w_list = []
        cov_matrix_rows = []

        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.treatment_question_id not in answers):
                continue

            has_all_covs = True
            c_vals = []
            for cid in cov_ids:
                if cid not in answers:
                    has_all_covs = False
                    break
                try:
                    c_vals.append(float(answers[cid]))
                except (ValueError, TypeError):
                    has_all_covs = False
                    break

            if not has_all_covs:
                continue

            try:
                yv = float(answers[payload.outcome_question_id])
                wv_raw = answers[payload.treatment_question_id]
                try:
                    wv = float(wv_raw)
                except (ValueError, TypeError):
                    wv = 1.0 if str(wv_raw).strip() in ["1", "true", "True", "yes"] else 0.0

                y_list.append(yv)
                w_list.append(wv)
                cov_matrix_rows.append(c_vals)
            except (ValueError, TypeError):
                continue

        if len(cov_matrix_rows) == 0 or len(cov_ids) == 0:
            cov_mat = np.zeros((len(y_list), 1))
            feat_names = ["Chỉ số mặc định"]
        else:
            cov_mat = np.array(cov_matrix_rows, dtype=float)
            feat_names = [q_map.get(cid, cid) for cid in cov_ids]

        res = PolicyLearningEngine.evaluate(
            y=np.array(y_list, dtype=float),
            w=np.array(w_list, dtype=float),
            x_matrix=cov_mat,
            feature_names=feat_names,
            primary_feature_idx=payload.primary_feature_idx,
            n_bootstraps=payload.n_bootstraps,
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả Y"),
            treatment_label=q_map.get(payload.treatment_question_id, "Biến can thiệp W")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="POLICY_LEARNING_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "n_samples": len(y_list),
                "optimal_welfare": res.get("diagnostics", {}).get("optimal_welfare_value") if res.get("diagnostics") else None,
                "net_gain": res.get("diagnostics", {}).get("net_welfare_gain") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


# --- RDD with Local Randomization for Discrete Running Variables (Cattaneo et al. 2015) ---
@router.post("/rdd-local-randomization", response_model=RDDLocalRandomizationOut)
def run_rdd_local_randomization_analysis(
    survey_id: str,
    payload: RDDLocalRandomizationRequest
):
    """
    Regression Discontinuity Design with Local Randomization (Cattaneo, Frandsen, & Titiunik 2015).
    Specialized for discrete or few-valued running variables with exact finite-sample permutation tests.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        if payload.outcome_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến kết quả (Y QID: {payload.outcome_question_id}) không tồn tại.")
        if payload.running_question_id not in q_map:
            raise HTTPException(status_code=400, detail=f"Biến chạy phân tầng (X QID: {payload.running_question_id}) không tồn tại.")

        cov_ids = payload.covariate_question_ids or []
        for cid in cov_ids:
            if cid not in q_map:
                raise HTTPException(status_code=400, detail=f"Biến đặc tính (Covariate QID: {cid}) không tồn tại.")

        scope_sql = ""
        if payload.scope == "verified_clean":
            scope_sql = " AND r.is_verified = 1 AND r.is_flagged = 0 "

        target_qids = [payload.outcome_question_id, payload.running_question_id] + cov_ids
        target_qids = list(dict.fromkeys(target_qids))

        placeholders = ",".join(["?"] * len(target_qids))
        query = f"""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON ra.response_id = r.id
            WHERE r.survey_id = ? {scope_sql}
              AND ra.question_id IN ({placeholders})
        """
        rows = conn.execute(query, [survey_id] + target_qids).fetchall()

        resp_data = {}
        for r in rows:
            resp_id = r["response_id"]
            if resp_id not in resp_data:
                resp_data[resp_id] = {}
            resp_data[resp_id][r["question_id"]] = r["answer_value"]

        y_list = []
        x_list = []
        cov_matrix_rows = []

        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.running_question_id not in answers):
                continue

            has_all_covs = True
            c_vals = []
            for cid in cov_ids:
                if cid not in answers:
                    has_all_covs = False
                    break
                try:
                    c_vals.append(float(answers[cid]))
                except (ValueError, TypeError):
                    has_all_covs = False
                    break

            if not has_all_covs:
                continue

            try:
                yv = float(answers[payload.outcome_question_id])
                xv = float(answers[payload.running_question_id])

                y_list.append(yv)
                x_list.append(xv)
                cov_matrix_rows.append(c_vals)
            except (ValueError, TypeError):
                continue

        cov_mat = np.array(cov_matrix_rows, dtype=float) if len(cov_ids) > 0 and len(cov_matrix_rows) > 0 else None
        cov_names = [q_map.get(cid, cid) for cid in cov_ids] if len(cov_ids) > 0 else None

        res = RDDLocalRandomizationEngine.evaluate(
            y=np.array(y_list, dtype=float),
            x=np.array(x_list, dtype=float),
            cutoff=payload.cutoff,
            covariates=cov_mat,
            covariate_names=cov_names,
            window_half_width=payload.window_half_width,
            n_permutations=payload.n_permutations,
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả Y"),
            running_label=q_map.get(payload.running_question_id, "Biến chạy X")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="RDD_LOCAL_RANDOMIZATION_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "running_qid": payload.running_question_id,
                "cutoff": payload.cutoff,
                "n_samples": len(y_list),
                "tau_diff_means": res.get("diagnostics", {}).get("tau_diff_means") if res.get("diagnostics") else None,
                "permutation_p_val": res.get("diagnostics", {}).get("permutation_p_value") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res



@router.post("/dynamic-panel-gmm", response_model=DynamicPanelGMMOut)
def run_dynamic_panel_gmm_analysis(
    survey_id: str,
    payload: DynamicPanelGMMRequest
):
    """
    Dynamic Panel System & Difference GMM (Arellano-Bond 1991, Blundell-Bond 1998, Windmeijer 2005).
    Estimates autoregressive persistence and exogenous covariates in longitudinal panel survey data
    while controlling for unobserved time-invariant heterogeneity and Nickell (1981) dynamic panel bias.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        resp_data: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_data:
                resp_data[rid] = {}
            resp_data[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []
        panel_records = []

        for resp_id, answers in resp_data.items():
            if (payload.unit_id_question_id not in answers or
                payload.time_question_id not in answers or
                payload.outcome_question_id not in answers):
                continue

            has_all_covs = True
            rec = {
                "unit_id": str(answers[payload.unit_id_question_id]),
                "time": answers[payload.time_question_id],
                "outcome": answers[payload.outcome_question_id]
            }
            for cid in cov_ids:
                if cid not in answers:
                    has_all_covs = False
                    break
                rec[cid] = answers[cid]

            if has_all_covs:
                panel_records.append(rec)

        res = DynamicPanelGMMEngine.estimate(
            panel_data=panel_records,
            unit_id_col="unit_id",
            time_col="time",
            outcome_col="outcome",
            covariate_cols=cov_ids,
            method=payload.method,
            two_step=payload.two_step,
            windmeijer_correction=payload.windmeijer_correction,
            max_instrument_lags=payload.max_instrument_lags
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="DYNAMIC_PANEL_GMM_EVALUATED",
            details={
                "unit_qid": payload.unit_id_question_id,
                "time_qid": payload.time_question_id,
                "outcome_qid": payload.outcome_question_id,
                "method": payload.method,
                "two_step": payload.two_step,
                "windmeijer": payload.windmeijer_correction,
                "status": res.get("status")
            }
        )

        return res



@router.post("/weak-iv-robust", response_model=WeakIVRobustOut)
def run_weak_iv_robust_analysis(
    survey_id: str,
    payload: WeakIVRobustRequest
):
    """
    Weak-Instrument Robust Inference (Anderson-Rubin 1949, Moreira 2003 CLR, Montiel Olea & Pflueger 2013).
    Evaluates causal effects of endogenous regressors using exact finite-sample AR quadratic inversion,
    Moreira's conditional likelihood ratio test, and effective F-statistic testing.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        resp_data: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_data:
                resp_data[rid] = {}
            resp_data[rid][row["question_id"]] = row["answer_value"]

        z_ids = payload.instrument_question_ids or []
        cov_ids = payload.covariate_question_ids or []

        y_list = []
        y_endog_list = []
        z_matrix_rows = []
        cov_matrix_rows = []

        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.endogenous_question_id not in answers):
                continue

            has_all_z = True
            z_vals = []
            for zid in z_ids:
                if zid not in answers:
                    has_all_z = False
                    break
                try:
                    z_vals.append(float(answers[zid]))
                except (ValueError, TypeError):
                    has_all_z = False
                    break

            if not has_all_z:
                continue

            has_all_covs = True
            c_vals = []
            for cid in cov_ids:
                if cid not in answers:
                    has_all_covs = False
                    break
                try:
                    c_vals.append(float(answers[cid]))
                except (ValueError, TypeError):
                    has_all_covs = False
                    break

            if not has_all_covs:
                continue

            try:
                yv = float(answers[payload.outcome_question_id])
                y_ev = float(answers[payload.endogenous_question_id])
                y_list.append(yv)
                y_endog_list.append(y_ev)
                z_matrix_rows.append(z_vals)
                cov_matrix_rows.append(c_vals)
            except (ValueError, TypeError):
                continue

        cov_mat = np.array(cov_matrix_rows, dtype=float) if len(cov_ids) > 0 and len(cov_matrix_rows) > 0 else None

        res = WeakIVRobustEngine.estimate(
            y=np.array(y_list, dtype=float),
            endogenous_y=np.array(y_endog_list, dtype=float),
            instruments_z=np.array(z_matrix_rows, dtype=float),
            covariates_x=cov_mat,
            alpha_level=payload.alpha_level,
            grid_points=payload.grid_points,
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả Y"),
            endogenous_label=q_map.get(payload.endogenous_question_id, "Biến nội sinh Y_endog")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="WEAK_IV_ROBUST_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "endogenous_qid": payload.endogenous_question_id,
                "instrument_qids": z_ids,
                "covariate_qids": cov_ids,
                "effective_f": res.get("diagnostics", {}).get("effective_f") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res



@router.post("/sequential-mediation", response_model=SequentialMediationOut)
def run_sequential_mediation_analysis(
    survey_id: str,
    payload: SequentialMediationRequest
):
    """
    Sequential Causal Mediation Analysis (Hayes Model 6 / Imai & Yamamoto 2013).
    Estimates chained causal mechanisms with intermediate confounding:
    Direct effect, isolated Path 1 (T->M1->Y), isolated Path 2 (T->M2->Y),
    and sequential indirect pathway (T->M1->M2->Y) with bootstrap confidence intervals.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        resp_data: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_data:
                resp_data[rid] = {}
            resp_data[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []

        t_list = []
        m1_list = []
        m2_list = []
        y_list = []
        cov_matrix_rows = []

        for resp_id, answers in resp_data.items():
            if (payload.treatment_question_id not in answers or
                payload.mediator1_question_id not in answers or
                payload.mediator2_question_id not in answers or
                payload.outcome_question_id not in answers):
                continue

            has_all_covs = True
            c_vals = []
            for cid in cov_ids:
                if cid not in answers:
                    has_all_covs = False
                    break
                try:
                    c_vals.append(float(answers[cid]))
                except (ValueError, TypeError):
                    has_all_covs = False
                    break

            if not has_all_covs:
                continue

            try:
                tv = float(answers[payload.treatment_question_id])
                m1v = float(answers[payload.mediator1_question_id])
                m2v = float(answers[payload.mediator2_question_id])
                yv = float(answers[payload.outcome_question_id])

                t_list.append(tv)
                m1_list.append(m1v)
                m2_list.append(m2v)
                y_list.append(yv)
                cov_matrix_rows.append(c_vals)
            except (ValueError, TypeError):
                continue

        cov_mat = np.array(cov_matrix_rows, dtype=float) if len(cov_ids) > 0 and len(cov_matrix_rows) > 0 else None

        res = SequentialMediationEngine.estimate(
            treatment=np.array(t_list, dtype=float),
            mediator1=np.array(m1_list, dtype=float),
            mediator2=np.array(m2_list, dtype=float),
            outcome=np.array(y_list, dtype=float),
            covariates=cov_mat,
            n_bootstraps=payload.n_bootstraps,
            alpha_level=payload.alpha_level,
            treatment_label=q_map.get(payload.treatment_question_id, "Biến can thiệp T"),
            mediator1_label=q_map.get(payload.mediator1_question_id, "Trung gian 1 (M1)"),
            mediator2_label=q_map.get(payload.mediator2_question_id, "Trung gian 2 (M2)"),
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả Y")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SEQUENTIAL_MEDIATION_EVALUATED",
            details={
                "treatment_qid": payload.treatment_question_id,
                "m1_qid": payload.mediator1_question_id,
                "m2_qid": payload.mediator2_question_id,
                "outcome_qid": payload.outcome_question_id,
                "n_samples": len(t_list),
                "n_bootstraps": payload.n_bootstraps,
                "status": res.get("status")
            }
        )

        return res



@router.post("/post-double-selection-lasso", response_model=PostDoubleSelectionLassoOut)
def run_post_double_selection_lasso_analysis(
    survey_id: str,
    payload: PostDoubleSelectionLassoRequest
):
    """
    High-Dimensional Post-Double-Selection (PDS) Lasso (Belloni, Chernozhukov, & Hansen 2014).
    Selects control variables by taking the union of Lasso selection on Outcome Y and Treatment D,
    guaranteeing Neyman orthogonality and uniform valid causal inference against omitted variable bias.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)
        ).fetchall()
        q_map = {row["id"]: row["title"] for row in q_rows}

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        resp_data: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_data:
                resp_data[rid] = {}
            resp_data[rid][row["question_id"]] = row["answer_value"]

        cand_ids = payload.candidate_control_question_ids or []

        y_list = []
        d_list = []
        x_matrix_rows = []

        for resp_id, answers in resp_data.items():
            if (payload.outcome_question_id not in answers or
                payload.treatment_question_id not in answers):
                continue

            has_all_controls = True
            c_vals = []
            for cid in cand_ids:
                if cid not in answers:
                    has_all_controls = False
                    break
                try:
                    c_vals.append(float(answers[cid]))
                except (ValueError, TypeError):
                    has_all_controls = False
                    break

            if not has_all_controls:
                continue

            try:
                yv = float(answers[payload.outcome_question_id])
                dv = float(answers[payload.treatment_question_id])

                y_list.append(yv)
                d_list.append(dv)
                x_matrix_rows.append(c_vals)
            except (ValueError, TypeError):
                continue

        ctrl_names = [q_map.get(cid, cid) for cid in cand_ids]

        res = PostDoubleSelectionLassoEngine.estimate(
            y=np.array(y_list, dtype=float),
            treatment=np.array(d_list, dtype=float),
            candidate_controls=np.array(x_matrix_rows, dtype=float),
            control_names=ctrl_names,
            cv_folds=payload.cv_folds,
            alpha_level=payload.alpha_level,
            outcome_label=q_map.get(payload.outcome_question_id, "Biến kết quả Y"),
            treatment_label=q_map.get(payload.treatment_question_id, "Biến can thiệp D")
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="POST_DOUBLE_SELECTION_LASSO_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "candidate_qids_count": len(cand_ids),
                "union_selected_count": res.get("diagnostics", {}).get("union_selected_controls") if res.get("diagnostics") else None,
                "status": res.get("status")
            }
        )

        return res


@router.post("/larf", response_model=LARFOut)
def run_larf_analysis(
    survey_id: str,
    payload: LARFRequest
):
    """
    Instrumental Variable Local Average Response Function (LARF; Abadie 2003 Econometrica).
    Identifies semi-parametric causal effects for non-linear or bounded survey response outcomes
    under endogenous binary treatment via Abadie's kappa weighting.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        df_records = []
        cov_ids = payload.covariate_question_ids or []
        all_req_qids = [payload.outcome_question_id, payload.treatment_question_id, payload.instrument_question_id] + cov_ids

        for rid, answers in resp_dict.items():
            if all(qid in answers for qid in all_req_qids):
                record = {}
                valid = True
                for qid in all_req_qids:
                    try:
                        record[qid] = float(answers[qid])
                    except (ValueError, TypeError):
                        valid = False
                        break
                if valid:
                    df_records.append(record)

        if len(df_records) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi có đầy đủ câu trả lời số hợp lệ (N={len(df_records)}) chưa đạt tối thiểu 30 mẫu."
            }

        df = pd.DataFrame(df_records)

        res = estimate_larf(
            df=df,
            outcome_col=payload.outcome_question_id,
            treatment_col=payload.treatment_question_id,
            instrument_col=payload.instrument_question_id,
            covariate_cols=cov_ids,
            model_type=payload.model_type,
            alpha_level=payload.alpha_level,
            n_bootstraps=payload.n_bootstraps,
            trim_negative=payload.trim_negative
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LARF_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "instrument_qid": payload.instrument_question_id,
                "model_type": payload.model_type,
                "late_estimate": res.get("effects", {}).get("late", {}).get("estimate") if res.get("effects") else None,
                "complier_probability": res.get("complier_probability"),
                "status": res.get("status")
            }
        )

        return res


@router.post("/mte", response_model=MTEOut)
def run_mte_analysis(
    survey_id: str,
    payload: MTERequest
):
    """
    Marginal Treatment Effects (MTE) and Local Instrumental Variables (LIV).
    Heckman & Vytlacil (1999, 2005 Econometrica).
    Identifies the continuous treatment effect curve over unobserved resistance to treatment U_D
    and integrates across MTE to derive unified causal parameters: ATE, ATT, ATU, LATE, PRTE.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []
        inst_ids = payload.instrument_question_ids
        all_req_qids = [payload.outcome_question_id, payload.treatment_question_id] + inst_ids + cov_ids

        df_records = []
        for rid, answers in resp_dict.items():
            if all(qid in answers for qid in all_req_qids):
                record = {}
                valid = True
                for qid in all_req_qids:
                    try:
                        record[qid] = float(answers[qid])
                    except (ValueError, TypeError):
                        valid = False
                        break
                if valid:
                    df_records.append(record)

        if len(df_records) < 40:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi có đầy đủ câu trả lời số hợp lệ (N={len(df_records)}) chưa đạt tối thiểu 40 mẫu."
            }

        df = pd.DataFrame(df_records)

        res = estimate_mte(
            df=df,
            outcome_col=payload.outcome_question_id,
            treatment_col=payload.treatment_question_id,
            instrument_cols=inst_ids,
            covariate_cols=cov_ids,
            poly_degree=payload.poly_degree,
            alpha_level=payload.alpha_level,
            n_bootstraps=payload.n_bootstraps,
            policy_shift_pct=payload.policy_shift_pct
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MTE_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "instrument_qids": inst_ids,
                "ate_estimate": res.get("parameters", {}).get("ate", {}).get("estimate") if res.get("parameters") else None,
                "att_estimate": res.get("parameters", {}).get("att", {}).get("estimate") if res.get("parameters") else None,
                "selection_pattern": res.get("selection_sorting_pattern"),
                "status": res.get("status")
            }
        )

        return res


@router.post("/lee-bounds", response_model=LeeBoundsOut)
def run_lee_bounds_analysis(
    survey_id: str,
    payload: LeeBoundsRequest
):
    """
    Non-random Survey Attrition & Selection Bounds (Lee 2009 Review of Economic Studies).
    Estimates sharp non-parametric bounds on treatment effects under non-random survey attrition,
    loss to follow-up, or selective response reporting, with optional covariate tightening.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []
        df_records = []
        for rid, answers in resp_dict.items():
            # For Lee bounds, treatment must be present. Outcome might be present or missing (indicating attrition)
            if payload.treatment_question_id in answers:
                record = {}
                try:
                    record[payload.treatment_question_id] = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                if payload.outcome_question_id in answers:
                    try:
                        record[payload.outcome_question_id] = float(answers[payload.outcome_question_id])
                    except (ValueError, TypeError):
                        record[payload.outcome_question_id] = np.nan
                else:
                    record[payload.outcome_question_id] = np.nan

                if payload.response_question_id and payload.response_question_id in answers:
                    try:
                        record[payload.response_question_id] = float(answers[payload.response_question_id])
                    except (ValueError, TypeError):
                        record[payload.response_question_id] = 1.0 if not np.isnan(record[payload.outcome_question_id]) else 0.0

                for cid in cov_ids:
                    if cid in answers:
                        try:
                            record[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            pass

                df_records.append(record)

        if len(df_records) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi (N={len(df_records)}) chưa đạt tối thiểu 30 mẫu cho phân tích Lee Bounds."
            }

        df = pd.DataFrame(df_records)

        res = estimate_lee_bounds(
            df=df,
            outcome_col=payload.outcome_question_id,
            treatment_col=payload.treatment_question_id,
            response_col=payload.response_question_id,
            covariate_cols=cov_ids,
            alpha_level=payload.alpha_level,
            n_bootstraps=payload.n_bootstraps
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LEE_BOUNDS_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "lower_bound": res.get("bounds", {}).get("unconditional", {}).get("lower_bound") if res.get("bounds") else None,
                "upper_bound": res.get("bounds", {}).get("unconditional", {}).get("upper_bound") if res.get("bounds") else None,
                "trimming_fraction_q": res.get("response_rates", {}).get("trimming_fraction_q") if res.get("response_rates") else None,
                "status": res.get("status")
            }
        )

        return res


@router.post("/surrogate-index", response_model=SurrogateIndexOut)
def run_surrogate_index_analysis(
    survey_id: str,
    payload: SurrogateIndexRequest
):
    """
    Surrogate Index & Long-Term Causal Evaluation from Short-Term Proxies.
    Athey, Chetty, Imbens, & Kang (2019 Econometrica).
    Identifies long-term treatment effects by constructing a Surrogate Index r(S, X)
    from short-term intermediate survey questions and projecting long-term counterfactuals.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        surr_ids = payload.surrogate_question_ids
        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            # Surrogates must be answered
            if all(sid in answers for sid in surr_ids):
                record = {}
                valid_surrs = True
                for sid in surr_ids:
                    try:
                        record[sid] = float(answers[sid])
                    except (ValueError, TypeError):
                        valid_surrs = False
                        break
                if not valid_surrs:
                    continue

                # Treatment
                if payload.treatment_question_id in answers:
                    try:
                        record[payload.treatment_question_id] = float(answers[payload.treatment_question_id])
                    except (ValueError, TypeError):
                        record[payload.treatment_question_id] = np.nan
                else:
                    record[payload.treatment_question_id] = np.nan

                # Long-term outcome
                if payload.longterm_outcome_question_id in answers:
                    try:
                        record[payload.longterm_outcome_question_id] = float(answers[payload.longterm_outcome_question_id])
                    except (ValueError, TypeError):
                        record[payload.longterm_outcome_question_id] = np.nan
                else:
                    record[payload.longterm_outcome_question_id] = np.nan

                # Covariates
                for cid in cov_ids:
                    if cid in answers:
                        try:
                            record[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            pass

                df_records.append(record)

        if len(df_records) < 40:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi có đầy đủ câu trả lời biến đại diện (N={len(df_records)}) chưa đạt tối thiểu 40 mẫu."
            }

        df = pd.DataFrame(df_records)

        res = estimate_surrogate_index(
            df=df,
            treatment_col=payload.treatment_question_id,
            surrogate_cols=surr_ids,
            longterm_outcome_col=payload.longterm_outcome_question_id,
            covariate_cols=cov_ids,
            sample_indicator_col=payload.sample_indicator_question_id,
            alpha_level=payload.alpha_level,
            n_bootstraps=payload.n_bootstraps,
            ridge_lambda=payload.ridge_lambda
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SURROGATE_INDEX_EVALUATED",
            details={
                "treatment_qid": payload.treatment_question_id,
                "surrogate_qids": surr_ids,
                "longterm_qid": payload.longterm_outcome_question_id,
                "longterm_tau": res.get("longterm_treatment_effect", {}).get("estimate") if res.get("longterm_treatment_effect") else None,
                "index_r2": res.get("surrogate_index_fit", {}).get("r_squared") if res.get("surrogate_index_fit") else None,
                "status": res.get("status")
            }
        )

        return res



@router.post("/conformal-counterfactual", response_model=ConformalCounterfactualOut)
def run_conformal_counterfactual_analysis(
    survey_id: str,
    payload: ConformalCounterfactualRequest
):
    """
    Conformal Counterfactual Risk Inference.
    Chernozhukov, Wüthrich, & Zhu (2021 JASA); Lei & Candès (2021 JASA).
    Yields distribution-free, finite-sample valid prediction intervals for individual
    counterfactual outcomes Y(1), Y(0) and treatment effects tau(X) with downside harm risk profiling.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    w_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                record = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: w_val
                }

                # Optional Subgroup
                if payload.subgroup_question_id and payload.subgroup_question_id in answers:
                    record[payload.subgroup_question_id] = str(answers[payload.subgroup_question_id])

                # Covariates
                valid_covs = True
                for cid in cov_ids:
                    if cid in answers:
                        try:
                            record[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            valid_covs = False
                            break
                    else:
                        valid_covs = False
                        break

                if valid_covs:
                    df_records.append(record)

        if len(df_records) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi (N={len(df_records)}) chưa đạt tối thiểu 30 mẫu cho phân tích Conformal Counterfactual."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_conformal_counterfactuals(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                covariate_cols=cov_ids,
                miscoverage_alpha=payload.miscoverage_alpha,
                calibration_ratio=payload.calibration_ratio,
                use_propensity_weighting=payload.use_propensity_weighting,
                subgroup_col=payload.subgroup_question_id
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Conformal Counterfactual: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONFORMAL_COUNTERFACTUAL_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "target_coverage": res.get("overall_summary", {}).get("target_coverage_pct"),
                "estimated_ate": res.get("overall_summary", {}).get("estimated_ate"),
                "downside_risk_rate": res.get("overall_summary", {}).get("downside_risk_rate"),
                "strictly_beneficial_rate": res.get("overall_summary", {}).get("strictly_beneficial_rate"),
                "status": res.get("status")
            }
        )

        return res



@router.post("/causal-sensitivity-bias", response_model=CausalSensitivityBiasOut)
def run_causal_sensitivity_bias_analysis(
    survey_id: str,
    payload: CausalSensitivityBiasRequest
):
    """
    Causal Sensitivity Analysis & Omitted Variable Bias (Cinelli & Hazlett 2020 JRSS-B).
    Evaluates how strong unobserved confounders must be (in terms of partial R2) to explain away
    the estimated causal treatment effect or render it statistically insignificant.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                record = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: d_val
                }

                valid_covs = True
                for cid in cov_ids:
                    if cid in answers:
                        try:
                            record[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            valid_covs = False
                            break
                    else:
                        valid_covs = False
                        break

                if valid_covs:
                    df_records.append(record)

        if len(df_records) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi (N={len(df_records)}) chưa đạt tối thiểu 25 mẫu cho phân tích Độ nhạy Nhân quả."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_causal_sensitivity_bias(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                covariate_cols=cov_ids,
                q_reduction=payload.q_reduction,
                alpha_level=payload.alpha_level,
                benchmark_covariates=payload.benchmark_question_ids,
                benchmark_multipliers=payload.benchmark_multipliers
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Độ nhạy Nhân quả: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CAUSAL_SENSITIVITY_BIAS_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "baseline_estimate": res.get("overall_summary", {}).get("baseline_estimate"),
                "robustness_value_q": res.get("overall_summary", {}).get("robustness_value_q"),
                "robustness_value_alpha": res.get("overall_summary", {}).get("robustness_value_alpha"),
                "status": res.get("status")
            }
        )

        return res



@router.post("/bcf", response_model=BCFOut)
def run_bcf_analysis(
    survey_id: str,
    payload: BCFRequest
):
    """
    Bayesian Causal Forest (BCF) & Heterogeneous Treatment Effects (Hahn et al. 2020).
    Decomposes conditional expectation into prognostic baseline mu(X, pi_hat) and treatment moderation tau(X),
    eliminating Regularization-Induced Confounding (RIC) and producing full posterior distributions for CATE.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    w_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                record = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: w_val
                }

                valid_covs = True
                for cid in cov_ids:
                    if cid in answers:
                        try:
                            record[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            valid_covs = False
                            break
                    else:
                        valid_covs = False
                        break

                if valid_covs:
                    df_records.append(record)

        if len(df_records) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi (N={len(df_records)}) chưa đạt tối thiểu 30 mẫu cho phân tích Bayesian Causal Forest."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_bayesian_causal_forest(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                covariate_cols=cov_ids,
                n_posterior_draws=payload.n_posterior_draws,
                alpha_ridge=payload.alpha_ridge
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Bayesian Causal Forest: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="BCF_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "posterior_ate_mean": res.get("overall_summary", {}).get("posterior_ate_mean"),
                "prob_positive_ate": res.get("overall_summary", {}).get("posterior_prob_positive_ate"),
                "status": res.get("status")
            }
        )

        return res



@router.post("/shift-share-iv", response_model=ShiftShareIVOut)
def run_shift_share_iv_analysis(
    survey_id: str,
    payload: ShiftShareIVRequest
):
    """
    Shift-Share / Bartik Instrumental Variables & Rotemberg Decomposition.
    Goldsmith-Pinkham, Sorkin, & Swift (2020 AER); Adao, Kolesár, & Morales (2019 QJE).
    Calculates 2SLS treatment effects using portfolio share exposures z_ik and aggregate shocks g_k,
    decomposing identification power into exact Rotemberg weights alpha_k with AKM robust standard errors.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        sh_ids = payload.share_question_ids
        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                record = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: d_val
                }

                # Shares
                valid_shares = True
                for sid in sh_ids:
                    if sid in answers:
                        try:
                            record[sid] = float(answers[sid])
                        except (ValueError, TypeError):
                            valid_shares = False
                            break
                    else:
                        valid_shares = False
                        break

                if not valid_shares:
                    continue

                # Covariates
                valid_covs = True
                for cid in cov_ids:
                    if cid in answers:
                        try:
                            record[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            valid_covs = False
                            break
                    else:
                        valid_covs = False
                        break

                if valid_covs:
                    df_records.append(record)

        if len(df_records) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng phản hồi (N={len(df_records)}) chưa đạt tối thiểu 30 mẫu cho phân tích Shift-Share IV."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_shift_share_iv(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                share_cols=sh_ids,
                shocks=payload.shocks,
                covariate_cols=cov_ids,
                alpha_level=payload.alpha_level
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Shift-Share IV: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SHIFT_SHARE_IV_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "beta_2sls": res.get("overall_summary", {}).get("beta_2sls"),
                "first_stage_f": res.get("overall_summary", {}).get("first_stage_f_statistic"),
                "rotemberg_hhi": res.get("overall_summary", {}).get("rotemberg_hhi"),
                "status": res.get("status")
            }
        )

        return res



@router.post("/quantile-synthetic-control", response_model=QuantileSyntheticControlOut)
def run_quantile_synthetic_control_analysis(
    survey_id: str,
    payload: QuantileSyntheticControlRequest
):
    """
    Quantile Synthetic Control & Distributional Counterfactuals.
    Gunsilius, F. F. (2023 Econometrica); Chernozhukov, Kasahara, & Schrimpf (2020).
    Extends synthetic controls to full quantile functions and distributions using Wasserstein distance minimization,
    calculating post-treatment Quantile Treatment Effects (QTE), counterfactual CDFs, and Gini inequality impact.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        # Parse treatment_time
        try:
            treatment_time_val = float(payload.treatment_time)
        except (ValueError, TypeError):
            treatment_time_val = str(payload.treatment_time)

        df_records = []
        for rid, answers in resp_dict.items():
            if (payload.outcome_question_id in answers and
                payload.unit_question_id in answers and
                payload.time_question_id in answers):
                try:
                    y_val = float(answers[payload.outcome_question_id])
                except (ValueError, TypeError):
                    continue

                u_val = str(answers[payload.unit_question_id]).strip()

                raw_t = answers[payload.time_question_id]
                try:
                    t_val = float(raw_t)
                except (ValueError, TypeError):
                    t_val = str(raw_t).strip()

                df_records.append({
                    payload.outcome_question_id: y_val,
                    payload.unit_question_id: u_val,
                    payload.time_question_id: t_val
                })

        if len(df_records) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi đầy đủ để ước lượng Quantile Synthetic Control (hiện có: {len(df_records)})."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_quantile_synthetic_control(
                df=df,
                outcome_col=payload.outcome_question_id,
                unit_col=payload.unit_question_id,
                time_col=payload.time_question_id,
                treated_unit_id=str(payload.treated_unit_id).strip(),
                treatment_time=treatment_time_val,
                quantiles=payload.quantiles or [0.10, 0.25, 0.50, 0.75, 0.90],
                regularization_lambda=payload.regularization_lambda
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Quantile Synthetic Control: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="QUANTILE_SYNTHETIC_CONTROL_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "unit_qid": payload.unit_question_id,
                "treated_unit": str(payload.treated_unit_id),
                "treatment_time": str(payload.treatment_time),
                "median_qte": res.get("overall_summary", {}).get("median_qte_effect"),
                "gini_impact": res.get("overall_summary", {}).get("gini_impact"),
                "status": res.get("status")
            }
        )

        return res



@router.post("/twfe-decomposition", response_model=TWFEDecompositionOut)
def run_twfe_decomposition_analysis(
    survey_id: str,
    payload: TWFEDecompositionRequest
):
    """
    Two-Way Fixed Effects (TWFE) Decomposition & Negative Weights Diagnostics.
    de Chaisemartin, C., & D'Haultfœuille, X. (2020 AER; 2022 Restud).
    Decomposes linear TWFE regression weights omega_{i,t} on individual treatment effects,
    computes minimal heterogeneity standard deviation sigma_fe required for sign reversal,
    and calculates robust DID_M switcher-vs-stayer estimates with placebo pre-trend tests.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            if (payload.outcome_question_id in answers and
                payload.treatment_question_id in answers and
                payload.unit_question_id in answers and
                payload.time_question_id in answers):
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                u_val = str(answers[payload.unit_question_id]).strip()

                raw_t = answers[payload.time_question_id]
                try:
                    t_val = float(raw_t)
                except (ValueError, TypeError):
                    t_val = str(raw_t).strip()

                rec = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: d_val,
                    payload.unit_question_id: u_val,
                    payload.time_question_id: t_val
                }

                # Controls
                valid_covs = True
                for cid in cov_ids:
                    if cid in answers:
                        try:
                            rec[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            valid_covs = False
                    else:
                        valid_covs = False

                if valid_covs:
                    df_records.append(rec)

        if len(df_records) < 12:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 12 bản ghi để ước lượng TWFE Decomposition (hiện có: {len(df_records)})."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_twfe_decomposition(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                unit_col=payload.unit_question_id,
                time_col=payload.time_question_id,
                covariate_cols=cov_ids if len(cov_ids) > 0 else None,
                alpha_level=payload.alpha_level
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình phân rã TWFE: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="TWFE_DECOMPOSITION_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "beta_twfe": res.get("overall_summary", {}).get("beta_twfe"),
                "did_m": res.get("overall_summary", {}).get("did_m_estimate"),
                "sum_neg_weights": res.get("overall_summary", {}).get("sum_negative_weights"),
                "sigma_fe": res.get("overall_summary", {}).get("minimal_heterogeneity_sd_sigma_fe"),
                "status": res.get("status")
            }
        )

        return res



@router.post("/factor-iv", response_model=FactorIVOut)
def run_factor_iv_analysis(
    survey_id: str,
    payload: FactorIVRequest
):
    """
    Factor Instrumental Variables & Principal Component 2SLS (PC-2SLS).
    Bai, J., & Ng, S. (2010 Econometric Theory); Kapetanios, Marcellino, & Papailias (2019 JBES).
    Overcomes many instruments bias and weak instruments by compressing candidate instruments Z
    into dense latent factors F_hat selected via Bai-Ng Information Criteria (IC_p1), running 2SLS.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        z_ids = payload.instrument_question_ids
        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                rec = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: d_val
                }

                # Instruments
                valid_z = True
                for zid in z_ids:
                    if zid in answers:
                        try:
                            rec[zid] = float(answers[zid])
                        except (ValueError, TypeError):
                            valid_z = False
                    else:
                        valid_z = False

                # Covariates
                valid_cov = True
                for cid in cov_ids:
                    if cid in answers:
                        try:
                            rec[cid] = float(answers[cid])
                        except (ValueError, TypeError):
                            valid_cov = False
                    else:
                        valid_cov = False

                if valid_z and valid_cov:
                    df_records.append(rec)

        if len(df_records) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 20 bản ghi đầy đủ để ước lượng Factor IV (hiện có: {len(df_records)})."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_factor_iv(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                instrument_cols=z_ids,
                covariate_cols=cov_ids if len(cov_ids) > 0 else None,
                n_factors=payload.n_factors,
                alpha_level=payload.alpha_level
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Factor IV: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="FACTOR_IV_EVALUATED",
            details={
                "outcome_qid": payload.outcome_question_id,
                "treatment_qid": payload.treatment_question_id,
                "n_instruments_k": len(z_ids),
                "n_factors_r": res.get("overall_summary", {}).get("n_factors_r"),
                "beta_fiv": res.get("overall_summary", {}).get("beta_factor_iv"),
                "first_stage_f": res.get("overall_summary", {}).get("first_stage_f_statistic"),
                "status": res.get("status")
            }
        )

        return res



@router.post("/nested-logit", response_model=NestedLogitOut)
def run_nested_logit_analysis(
    survey_id: str,
    payload: NestedLogitRequest
):
    """
    Nested Logit Structural Discrete Choice & Substitution Elasticity Engine.
    McFadden, D. (1978); Train, K. E. (2009); Berry, S. T. (1994).
    Relaxes the restrictive Independence of Irrelevant Alternatives (IIA) assumption
    by grouping alternatives into correlated nests, estimating dissimilarity parameters lambda_m in (0, 1],
    computing within-nest vs cross-nest substitution elasticities, and testing IIA via Likelihood Ratio tests.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        attr_ids = payload.attribute_question_ids
        cost_id = payload.cost_question_id

        df_records = []
        for rid, answers in resp_dict.items():
            if (payload.choice_question_id in answers and
                payload.alternative_question_id in answers and
                payload.nest_question_id in answers and
                payload.choice_id_question_id in answers):
                try:
                    c_val = float(answers[payload.choice_question_id])
                except (ValueError, TypeError):
                    continue

                alt_val = str(answers[payload.alternative_question_id]).strip()
                nest_val = str(answers[payload.nest_question_id]).strip()
                cid_val = str(answers[payload.choice_id_question_id]).strip()

                rec = {
                    payload.choice_question_id: c_val,
                    payload.alternative_question_id: alt_val,
                    payload.nest_question_id: nest_val,
                    payload.choice_id_question_id: cid_val
                }

                # Attributes
                valid_attrs = True
                for aid in attr_ids:
                    if aid in answers:
                        try:
                            rec[aid] = float(answers[aid])
                        except (ValueError, TypeError):
                            valid_attrs = False
                    else:
                        valid_attrs = False

                if cost_id:
                    if cost_id in answers:
                        try:
                            rec[cost_id] = float(answers[cost_id])
                        except (ValueError, TypeError):
                            valid_attrs = False
                    else:
                        valid_attrs = False

                if valid_attrs:
                    df_records.append(rec)

        if len(df_records) < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 15 bản ghi lựa chọn để ước lượng Nested Logit (hiện có: {len(df_records)})."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_nested_logit(
                df=df,
                choice_col=payload.choice_question_id,
                alternative_col=payload.alternative_question_id,
                nest_col=payload.nest_question_id,
                id_col=payload.choice_id_question_id,
                attribute_cols=attr_ids,
                cost_col=cost_id,
                alpha_level=payload.alpha_level
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Nested Logit: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="NESTED_LOGIT_EVALUATED",
            details={
                "n_situations": res.get("overall_summary", {}).get("n_choice_situations"),
                "n_alternatives": res.get("overall_summary", {}).get("n_alternatives"),
                "n_nests": res.get("overall_summary", {}).get("n_nests"),
                "ll_nested": res.get("overall_summary", {}).get("log_likelihood_nested_logit"),
                "lr_stat": res.get("overall_summary", {}).get("lr_test_iia_statistic"),
                "iia_rejected": res.get("overall_summary", {}).get("iia_assumption_rejected"),
                "status": res.get("status")
            }
        )

        return res


@router.post("/auto-dml-riesz", response_model=AutoDMLRieszOut)
def run_auto_dml_riesz_analysis(
    survey_id: str,
    payload: AutoDMLRieszRequest
):
    """
    Automatic Debiased Machine Learning via Riesz Representer Learning Engine.
    Chernozhukov, V., Newey, W. K., & Singh, R. (2022). Econometrica.
    Directly learns the Neyman-orthogonal Riesz representer alpha_0(W) from data by minimizing
    empirical Riesz loss, bypassing manual influence function derivations or unstable propensity denominators.
    Supports binary ATE, continuous policy shifts (D -> D + delta), and average marginal derivatives with cross-fitting.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                rec = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: d_val
                }

                valid_covs = True
                for c_id in payload.covariate_question_ids:
                    if c_id in answers:
                        try:
                            rec[c_id] = float(answers[c_id])
                        except (ValueError, TypeError):
                            valid_covs = False
                    else:
                        valid_covs = False

                if valid_covs:
                    df_records.append(rec)

        if len(df_records) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 25 bản ghi hoàn chỉnh để thực hiện Auto-DML (hiện có: {len(df_records)})."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_auto_dml_riesz(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                covariate_cols=payload.covariate_question_ids,
                functional_type=payload.functional_type,
                shift_delta=payload.shift_delta,
                n_splits=payload.n_splits,
                ridge_lambda=payload.ridge_lambda,
                alpha_level=payload.alpha_level
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Auto-DML Riesz: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="AUTO_DML_RIESZ_EVALUATED",
            details={
                "functional_type": payload.functional_type,
                "theta_autodml": res.get("overall_summary", {}).get("theta_autodml"),
                "se_autodml": res.get("overall_summary", {}).get("se_autodml"),
                "p_value": res.get("overall_summary", {}).get("p_value"),
                "debiasing_correction": res.get("overall_summary", {}).get("debiasing_correction_magnitude"),
                "status": res.get("status")
            }
        )

        return res


@router.post("/local-instrumental-variables", response_model=LocalInstrumentalVariablesOut)
def run_local_instrumental_variables_analysis(
    survey_id: str,
    payload: LocalInstrumentalVariablesRequest
):
    """
    Local Instrumental Variables & Marginal Treatment Effects (LIV / MTE) Engine.
    Heckman, J. J., & Vytlacil, E. (2005). Econometrica.
    Mogstad, M., Santos, A., & Torgovitsky, A. (2018). Econometrica.
    Estimates the structural MTE(u) curve over unobserved resistance distribution U_D,
    integrates MTE against policy weights to recover ATE, ATT, ATU, LATE, and PRTE,
    and conducts a Wald test for Essential Heterogeneity (selection on unobserved gains).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []
        inst_ids = payload.instrument_question_ids

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                rec = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: d_val
                }

                # Instruments
                valid_insts = True
                for i_id in inst_ids:
                    if i_id in answers:
                        try:
                            rec[i_id] = float(answers[i_id])
                        except (ValueError, TypeError):
                            valid_insts = False
                    else:
                        valid_insts = False

                # Covariates
                valid_covs = True
                for c_id in cov_ids:
                    if c_id in answers:
                        try:
                            rec[c_id] = float(answers[c_id])
                        except (ValueError, TypeError):
                            valid_covs = False
                    else:
                        valid_covs = False

                if valid_insts and valid_covs:
                    df_records.append(rec)

        if len(df_records) < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 30 bản ghi hợp lệ để ước lượng LIV/MTE (hiện có: {len(df_records)})."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_local_instrumental_variables(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                instrument_cols=inst_ids,
                covariate_cols=cov_ids,
                n_grid_points=payload.n_grid_points,
                trim_quantile=payload.trim_quantile,
                alpha_level=payload.alpha_level
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng LIV/MTE: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LOCAL_INSTRUMENTAL_VARIABLES_EVALUATED",
            details={
                "ate": res.get("overall_summary", {}).get("ate", {}).get("estimate"),
                "att": res.get("overall_summary", {}).get("att", {}).get("estimate"),
                "atu": res.get("overall_summary", {}).get("atu", {}).get("estimate"),
                "late": res.get("overall_summary", {}).get("late", {}).get("estimate"),
                "sorting_gain": res.get("overall_summary", {}).get("sorting_on_gains_att_minus_ate"),
                "essential_heterogeneity": res.get("overall_summary", {}).get("essential_heterogeneity_present"),
                "status": res.get("status")
            }
        )

        return res


@router.post("/conformal-optimal-transport", response_model=ConformalOptimalTransportOut)
def run_conformal_optimal_transport_analysis(
    survey_id: str,
    payload: ConformalOptimalTransportRequest
):
    """
    Conformal Optimal Transport Counterfactual Distributional Alignment Engine (COT-CDA).
    Cuturi, M. (2013). NeurIPS; Courty, N., et al. (2017). IEEE TPAMI; Romano, Y., et al. (2019). NeurIPS.
    Entropy-regularized Wasserstein optimal transport (Sinkhorn algorithm) between treated and control
    distributions, individual Monge transport map counterfactual imputation, 2-Wasserstein distance W_2,
    and split-conformal prediction intervals with finite-sample coverage guarantees.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_filter = "AND r.review_status NOT IN ('verified_fraud', 'quota_screened_out')" if payload.scope == "verified_clean" else ""

        rows = conn.execute(f"""
            SELECT r.id as resp_id, ra.question_id, ra.answer_value
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if not rows:
            return {"status": "INSUFFICIENT_SAMPLE", "message": "Chưa có phản hồi khảo sát hợp lệ."}

        # Pivot responses
        resp_dict = {}
        for row in rows:
            rid = row["resp_id"]
            if rid not in resp_dict:
                resp_dict[rid] = {}
            resp_dict[rid][row["question_id"]] = row["answer_value"]

        cov_ids = payload.covariate_question_ids or []

        df_records = []
        for rid, answers in resp_dict.items():
            if payload.outcome_question_id in answers and payload.treatment_question_id in answers:
                try:
                    y_val = float(answers[payload.outcome_question_id])
                    d_val = float(answers[payload.treatment_question_id])
                except (ValueError, TypeError):
                    continue

                rec = {
                    payload.outcome_question_id: y_val,
                    payload.treatment_question_id: d_val
                }

                # Covariates
                valid_covs = True
                for c_id in cov_ids:
                    if c_id in answers:
                        try:
                            rec[c_id] = float(answers[c_id])
                        except (ValueError, TypeError):
                            valid_covs = False
                    else:
                        valid_covs = False

                if valid_covs:
                    df_records.append(rec)

        if len(df_records) < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 25 bản ghi hoàn chỉnh để thực hiện Optimal Transport (hiện có: {len(df_records)})."
            }

        df = pd.DataFrame(df_records)

        try:
            res = estimate_conformal_optimal_transport(
                df=df,
                outcome_col=payload.outcome_question_id,
                treatment_col=payload.treatment_question_id,
                covariate_cols=cov_ids,
                reg_eps=payload.reg_eps,
                covariate_weight_kappa=payload.covariate_weight_kappa,
                conformal_alpha=payload.conformal_alpha
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Lỗi trong quá trình ước lượng Conformal Optimal Transport: {str(e)}"
            }

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONFORMAL_OPTIMAL_TRANSPORT_EVALUATED",
            details={
                "w2_distance": res.get("overall_summary", {}).get("wasserstein_2_distance"),
                "ate_ot": res.get("overall_summary", {}).get("optimal_transport_ate"),
                "att_ot": res.get("overall_summary", {}).get("optimal_transport_att"),
                "conformal_half_width": res.get("overall_summary", {}).get("conformal_half_width_delta"),
                "status": res.get("status")
            }
        )

        return res
