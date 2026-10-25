import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Users,
  Clock,
  ShieldAlert,
  AlertTriangle,
  Download,
  CheckCircle2,
  HelpCircle,
  FileText,
  FileCheck,
  RefreshCw,
  TrendingDown,
  CheckCircle,
  Sparkles,
  BookOpen,
  BarChart2,
  Scale,
  PieChart,
  ShieldCheck,
  Network
} from 'lucide-react';
import { api } from '../api/client';
import { SurveyAnalytics } from '../types/survey';
import { QualityAuditReportModal } from '../components/QualityAuditReportModal';
import { BenfordAnalysisCard } from '../components/BenfordAnalysisCard';
import { AIQualitativeInsightsCard } from '../components/AIQualitativeInsightsCard';
import { CrossTabulationCard } from '../components/CrossTabulationCard';
import { ScaleReliabilityCard } from '../components/ScaleReliabilityCard';
import { EFAAnalysisCard } from '../components/EFAAnalysisCard';
import { CorrelationMatrixCard } from '../components/CorrelationMatrixCard';
import { HypothesisTTestCard } from '../components/HypothesisTTestCard';
import { ANOVAAnalysisCard } from '../components/ANOVAAnalysisCard';
import { LinearRegressionCard } from '../components/LinearRegressionCard';
import { MediationAnalysisCard } from '../components/MediationAnalysisCard';
import { ModerationAnalysisCard } from '../components/ModerationAnalysisCard';
import { ModeratedMediationCard } from '../components/ModeratedMediationCard';
import { ComplexSamplingCard } from '../components/ComplexSamplingCard';
import { PropensityMatchingCard } from '../components/PropensityMatchingCard';
import { TopicModelingCard } from '../components/TopicModelingCard';
import { PsychometricNetworkCard } from '../components/PsychometricNetworkCard';
import { IRT2PLCard } from '../components/IRT2PLCard';
import { SurvivalDropOffCard } from '../components/SurvivalDropOffCard';
import { MultilevelModelingCard } from '../components/MultilevelModelingCard';
import { ConjointAnalysisCard } from '../components/ConjointAnalysisCard';
import { LatentClassAnalysisCard } from '../components/LatentClassAnalysisCard';
import { DifferenceInDifferencesCard } from '../components/DifferenceInDifferencesCard';
import { SEMPathAnalysisCard } from '../components/SEMPathAnalysisCard';
import { CompetingRisksFrailtyCard } from '../components/CompetingRisksFrailtyCard';
import { IRT4PLAnalysisCard } from '../components/IRT4PLAnalysisCard';
import { IPWDoublyRobustCard } from '../components/IPWDoublyRobustCard';
import { GAMSplineRegressionCard } from '../components/GAMSplineRegressionCard';
import { QuantileRegressionCard } from '../components/QuantileRegressionCard';
import { GTheoryCard } from '../components/GTheoryCard';
import { RDDCard } from '../components/RDDCard';
import { SyntheticControlCard } from '../components/SyntheticControlCard';
import { SmallAreaEstimationCard } from '../components/SmallAreaEstimationCard';
import { EventStudyCard } from '../components/EventStudyCard';
import { BSTSCausalImpactCard } from '../components/BSTSCausalImpactCard';
import { AIPWCATECard } from '../components/AIPWCATECard';
import { IV2SLSCard } from '../components/IV2SLSCard';
import { BifactorCard } from '../components/BifactorCard';
import { PanelVARCard } from '../components/PanelVARCard';
import { LatentGrowthCard } from '../components/LatentGrowthCard';
import { QTECard } from '../components/QTECard';
import { CausalDAGCard } from '../components/CausalDAGCard';
import { MSMCard } from '../components/MSMCard';
import { GEECard } from '../components/GEECard';
import { RandomizationInferenceCard } from '../components/RandomizationInferenceCard';
import { EVTCard } from '../components/EVTCard';
import { JointModelCard } from '../components/JointModelCard';
import { ConformalPredictionCard } from '../components/ConformalPredictionCard';
import { MSEMCard } from '../components/MSEMCard';
import { TMLECard } from '../components/TMLECard';
import { SDIDCard } from '../components/SDIDCard';
import { CausalForestCard } from '../components/CausalForestCard';
import { CausalMediationSensitivityCard } from '../components/CausalMediationSensitivityCard';
import { DTWClusteringCard } from '../components/DTWClusteringCard';
import { CausalTreeCard } from '../components/CausalTreeCard';
import { MultipleTestingFDRCard } from '../components/MultipleTestingFDRCard';
import { BSEMCard } from '../components/BSEMCard';
import { GaussianCopulaCard } from '../components/GaussianCopulaCard';
import { DynamicFactorModelCard } from '../components/DynamicFactorModelCard';
import { ExtremeBoundsAnalysisCard } from '../components/ExtremeBoundsAnalysisCard';
import { SpatialEconometricsCard } from '../components/SpatialEconometricsCard';
import { IVQuantileRegressionCard } from '../components/IVQuantileRegressionCard';
import { ConjointHBCard } from '../components/ConjointHBCard';
import { FractionalResponseCard } from '../components/FractionalResponseCard';
import { MIRTCard } from '../components/MIRTCard';
import { HeckmanSelectionCard } from '../components/HeckmanSelectionCard';
import { StochasticFrontierCard } from '../components/StochasticFrontierCard';
import { ZeroInflatedCountCard } from '../components/ZeroInflatedCountCard';
import { LatentModerationCard } from '../components/LatentModerationCard';
import { EndogenousSwitchingCard } from '../components/EndogenousSwitchingCard';
import { GPSDoseResponseCard } from '../components/GPSDoseResponseCard';
import { CausalDiscoveryCard } from '../components/CausalDiscoveryCard';
import { BARTCausalCard } from '../components/BARTCausalCard';
import { ConjointChoiceCard } from '../components/ConjointChoiceCard';
import { MGSEMInvarianceCard } from '../components/MGSEMInvarianceCard';
import { GAMSplineCard } from '../components/GAMSplineCard';
import { LatentProfileCard } from '../components/LatentProfileCard';
import { ShapleyDriverCard } from '../components/ShapleyDriverCard';
import { PlackettLuceCard } from '../components/PlackettLuceCard';
import { MaxDiffCard } from '../components/MaxDiffCard';
import { BayesianNetworkCard } from '../components/BayesianNetworkCard';
import { StochasticDominanceCard } from '../components/StochasticDominanceCard';
import { ManskiBoundsCard } from '../components/ManskiBoundsCard';
import { DynamicTreatmentRegimesCard } from '../components/DynamicTreatmentRegimesCard';
import { FiniteMixtureRaschCard } from '../components/FiniteMixtureRaschCard';
import { DoubleMachineLearningCard } from '../components/DoubleMachineLearningCard';
import { RegressionKinkCard } from '../components/RegressionKinkCard';
import { StaggeredDIDCard } from '../components/StaggeredDIDCard';
import { MatrixCompletionCausalCard } from '../components/MatrixCompletionCausalCard';
import { SDIDAdvancedCard } from '../components/SDIDAdvancedCard';
import { InteractiveFixedEffectsCard } from '../components/InteractiveFixedEffectsCard';
import { MultipleMediatorsCard } from '../components/MultipleMediatorsCard';
import { PolicyLearningCard } from '../components/PolicyLearningCard';
import { RDDLocalRandomizationCard } from '../components/RDDLocalRandomizationCard';
import { DynamicPanelGMMCard } from '../components/DynamicPanelGMMCard';
import { WeakIVRobustCard } from '../components/WeakIVRobustCard';
import { SequentialMediationCard } from '../components/SequentialMediationCard';
import { PostDoubleSelectionLassoCard } from '../components/PostDoubleSelectionLassoCard';
import { LARFCard } from '../components/LARFCard';
import { MTECard } from '../components/MTECard';
import { LeeBoundsCard } from '../components/LeeBoundsCard';
import { SurrogateIndexCard } from '../components/SurrogateIndexCard';
import { ConformalCounterfactualCard } from '../components/ConformalCounterfactualCard';
import { CausalSensitivityBiasCard } from '../components/CausalSensitivityBiasCard';
import { BCFCard } from '../components/BCFCard';
import { ShiftShareIVCard } from '../components/ShiftShareIVCard';
import { QuantileSyntheticControlCard } from '../components/QuantileSyntheticControlCard';
import { TWFEDecompositionCard } from '../components/TWFEDecompositionCard';
import { FactorIVCard } from '../components/FactorIVCard';
import { NestedLogitCard } from '../components/NestedLogitCard';
import { AutoDMLRieszCard } from '../components/AutoDMLRieszCard';
import { LocalInstrumentalVariablesCard } from '../components/LocalInstrumentalVariablesCard';
import { ConformalOptimalTransportCard } from '../components/ConformalOptimalTransportCard';
import { DPMDeconvolutionCard } from '../components/DPMDeconvolutionCard';
import { MultiCutoffRDCard } from '../components/MultiCutoffRDCard';
import { HighDimensionalMediationCard } from '../components/HighDimensionalMediationCard';
import { NetworkSpilloverCard } from '../components/NetworkSpilloverCard';
import { DynamicSpatialPanelCard } from '../components/DynamicSpatialPanelCard';
import { ContinuousPolicyShiftCard } from '../components/ContinuousPolicyShiftCard';
import { GeneralizedSyntheticControlCard } from '../components/GeneralizedSyntheticControlCard';
import { HierarchicalBayesConjointCard } from '../components/HierarchicalBayesConjointCard';
import { BoundaryKernelDeconvolutionCard } from '../components/BoundaryKernelDeconvolutionCard';
import { TargetedMaximumLikelihoodCard } from '../components/TargetedMaximumLikelihoodCard';
import { CopulaEndogeneityCard } from '../components/CopulaEndogeneityCard';
import { CausalSurvivalRMSTCard } from '../components/CausalSurvivalRMSTCard';
import { DynamicDiscreteChoiceCard } from '../components/DynamicDiscreteChoiceCard';
import { SyntheticDiffInDiffCard } from '../components/SyntheticDiffInDiffCard';
import { RIFOaxacaDecompositionCard } from '../components/RIFOaxacaDecompositionCard';
import { DiffInDiscontinuitiesCard } from '../components/DiffInDiscontinuitiesCard';
import { NonParametricTestsCard } from '../components/NonParametricTestsCard';
import { MissingDataCard } from '../components/MissingDataCard';
import { ScaleEquatingCard } from '../components/ScaleEquatingCard';
import { MeasurementInvarianceCard } from '../components/MeasurementInvarianceCard';
import { CommonMethodBiasCard } from '../components/CommonMethodBiasCard';
import { SamplePowerAnalysisCard } from '../components/SamplePowerAnalysisCard';
import { LongitudinalComparisonCard } from '../components/LongitudinalComparisonCard';
import { SamplingQuotaCard } from '../components/SamplingQuotaCard';
import { CognitivePacingCard } from '../components/CognitivePacingCard';
import { MultivariateOutlierCard } from '../components/MultivariateOutlierCard';
import { DemographicRakingModal } from '../components/DemographicRakingModal';
import { DIFAnalysisModal } from '../components/DIFAnalysisModal';
import { DataCleansingModal } from '../components/DataCleansingModal';
import { CodebookModal } from '../components/CodebookModal';
import { AcademicChartExportModal } from '../components/AcademicChartExportModal';
import { AcademicManuscriptModal } from '../components/AcademicManuscriptModal';
import { SurveyLogicSimulatorModal } from '../components/SurveyLogicSimulatorModal';
import { SplitBallotExperimentCard } from '../components/SplitBallotExperimentCard';
import { RaschWrightMapCard } from '../components/RaschWrightMapCard';
import { RespondentClusterCard } from '../components/RespondentClusterCard';
import { PairwiseSimilarityCard } from '../components/PairwiseSimilarityCard';
import { SpatialGeoAuditCard } from '../components/SpatialGeoAuditCard';

interface Props {
  surveyId: string;
  onNavigate: (path: string) => void;
}

export const SurveyAnalyticsPage: React.FC<Props> = ({ surveyId, onNavigate }) => {
  const [analytics, setAnalytics] = useState<SurveyAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
  const [isCleansingOpen, setIsCleansingOpen] = useState(false);
  const [isCodebookOpen, setIsCodebookOpen] = useState(false);
  const [isChartExportOpen, setIsChartExportOpen] = useState(false);
  const [isManuscriptOpen, setIsManuscriptOpen] = useState(false);
  const [isLogicSimulatorOpen, setIsLogicSimulatorOpen] = useState(false);
  const [isRakingOpen, setIsRakingOpen] = useState(false);
  const [isDIFOpen, setIsDIFOpen] = useState(false);
  const [chartExportQuestionId, setChartExportQuestionId] = useState<string | null>(null);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [autoRefreshSecs, setAutoRefreshSecs] = useState<number>(0);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date>(new Date());
  const [refreshingSilent, setRefreshingSilent] = useState<boolean>(false);

  useEffect(() => {
    loadAnalytics();
  }, [surveyId]);

  useEffect(() => {
    if (autoRefreshSecs <= 0) return;
    const timer = setInterval(() => {
      refreshAnalyticsSilent();
    }, autoRefreshSecs * 1000);
    return () => clearInterval(timer);
  }, [surveyId, autoRefreshSecs]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await api.getSurveyAnalytics(surveyId);
      setAnalytics(data);
      setLastRefreshedAt(new Date());
    } catch (err) {
      console.error(err);
      alert('Không thể tải báo cáo phân tích.');
    } finally {
      setLoading(false);
    }
  };

  const refreshAnalyticsSilent = async () => {
    try {
      setRefreshingSilent(true);
      const data = await api.getSurveyAnalytics(surveyId);
      setAnalytics(data);
      setLastRefreshedAt(new Date());
    } catch (err) {
      console.warn('Lỗi làm mới tự động:', err);
    } finally {
      setRefreshingSilent(false);
    }
  };

  const handleReanalyze = async () => {
    try {
      setReanalyzing(true);
      const res = await api.reanalyzeSurveyResponses(surveyId);
      alert(`Tái phân tích chất lượng hoàn tất!\n- Tổng số phản hồi: ${res.total_reanalyzed}\n- Rủi ro cao: ${res.high_risk_count}\n- Rủi ro trung bình: ${res.medium_risk_count}\n- Rủi ro thấp: ${res.low_risk_count}`);
      await loadAnalytics();
    } catch (err: any) {
      alert(err.message || 'Lỗi khi tái phân tích');
    } finally {
      setReanalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center text-slate-500 text-sm">
        Đang tổng hợp dữ liệu thống kê từ database...
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="p-8 text-center text-slate-500">
        Không có dữ liệu phân tích.
      </div>
    );
  }

  const {
    survey_title,
    total_responses,
    is_sample_size_sufficient,
    sample_size_notice,
    avg_duration_seconds,
    risk_distribution,
    review_distribution,
    questions_analytics
  } = analytics;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-300">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('/surveys')}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Báo cáo phân tích chất lượng
            </h1>
            <p className="text-sm text-slate-500 font-medium">
              Khảo sát: <span className="text-indigo-600 font-semibold">{survey_title}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Live Auto-Refresh Controller */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-600 shadow-2xs">
            <span className={`w-2 h-2 rounded-full ${autoRefreshSecs > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`} />
            <span className="text-[11px] font-medium text-slate-500">Live Sync:</span>
            <select
              value={autoRefreshSecs}
              onChange={(e) => setAutoRefreshSecs(Number(e.target.value))}
              className="bg-transparent font-bold text-slate-800 text-[11px] focus:outline-hidden cursor-pointer"
            >
              <option value={0}>Tắt</option>
              <option value={15}>15s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
            </select>
            {refreshingSilent ? (
              <RefreshCw className="w-3 h-3 text-indigo-500 animate-spin" />
            ) : (
              <span className="text-[10px] text-slate-400 font-mono ml-0.5">
                {lastRefreshedAt.toLocaleTimeString('vi-VN')}
              </span>
            )}
          </div>

          <button
            onClick={() => {
              setChartExportQuestionId(null);
              setIsChartExportOpen(true);
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-violet-600 text-white hover:bg-violet-700 shadow-xs transition-all"
            title="Xuất biểu đồ nghiên cứu chất lượng cao định dạng Vector SVG và PNG 300 DPI"
          >
            <BarChart2 className="w-4 h-4" />
            <span>Xuất Biểu Đồ (SVG/PNG)</span>
          </button>

          <button
            onClick={() => setIsLogicSimulatorOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-xs transition-all"
            title="Mô phỏng đồ thị luồng rẽ nhánh DAG và kiểm định chu trình logic"
          >
            <Network className="w-4 h-4 text-indigo-600" />
            <span>Logic DAG</span>
          </button>

          <button
            onClick={() => setIsManuscriptOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-white hover:bg-slate-900 shadow-xs transition-all"
            title="Mở Studio xem trước, in ấn và xuất bản thảo nghiên cứu khoa học (HTML / Markdown / LaTeX)"
          >
            <FileText className="w-4 h-4 text-violet-400" />
            <span>Bản Thảo Studio</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/export/academic-dossier?scope=verified_clean`, '_blank')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs transition-all"
            title="Tải trọn gói 8 tệp hồ sơ nghiên cứu học thuật (.ZIP)"
          >
            <Download className="w-4 h-4" />
            <span>Xuất Dossier (.ZIP)</span>
          </button>

          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/export`)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-all shadow-xs"
            title="Tùy chỉnh phạm vi lọc và định dạng xuất nhập dữ liệu"
          >
            <FileText className="w-4 h-4 text-indigo-600" />
            <span>Xuất/Nhập dữ liệu</span>
          </button>

          <button
            onClick={() => setIsCleansingOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 shadow-xs transition-all"
            title="Quy trình lọc loại bỏ speeders, straightlining và tính hệ số Cronbach's Alpha"
          >
            <Sparkles className="w-4 h-4 text-emerald-200" />
            <span>Làm sạch dữ liệu</span>
          </button>

          <button
            onClick={() => setIsRakingOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-all shadow-xs"
            title="Cân bằng trọng số sau thu thập (Demographic Raking / Iterative Proportional Fitting)"
          >
            <Scale className="w-4 h-4 text-indigo-600" />
            <span>Cân bằng mẫu (Raking/IPF)</span>
          </button>

          <button
            onClick={() => setIsDIFOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-violet-50 text-violet-700 hover:bg-violet-100 border border-violet-200 transition-all shadow-xs"
            title="Kiểm định bất biến đo lường và sai lệch câu hỏi (Mantel-Haenszel DIF & ETS Classification)"
          >
            <ShieldCheck className="w-4 h-4 text-violet-600" />
            <span>Kiểm định sai lệch (DIF)</span>
          </button>

          <button
            onClick={handleReanalyze}
            disabled={reanalyzing}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-violet-50 text-violet-700 hover:bg-violet-100 border border-violet-200 transition-all shadow-xs disabled:opacity-50"
            title="Tái chạy động cơ Quality Engine đa tầng trên toàn bộ phản hồi"
          >
            <RefreshCw className={`w-4 h-4 text-violet-600 ${reanalyzing ? 'animate-spin' : ''}`} />
            <span>{reanalyzing ? 'Đang phân tích...' : 'Tái phân tích'}</span>
          </button>
          <button
            onClick={() => setIsAuditModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 transition-all shadow-xs"
          >
            <FileCheck className="w-4 h-4 text-emerald-600" />
            <span>Báo cáo kiểm định độc lập</span>
          </button>
          <button
            onClick={() => setIsCodebookOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-all shadow-xs"
            title="Mở từ điển dữ liệu, nhãn biến và cú pháp SPSS/Stata/R"
          >
            <BookOpen className="w-4 h-4 text-indigo-600" />
            <span>Từ điển biến & Cú pháp</span>
          </button>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/enumerators`)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-all"
          >
            <Users className="w-4 h-4" />
            <span>Giám sát Điều tra viên</span>
          </button>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/responses`)}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all"
          >
            Xem danh sách phản hồi ({total_responses})
          </button>
        </div>
      </div>

      {/* Sample Size Warning if N < 5 */}
      {!is_sample_size_sufficient && (
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <h4 className="font-bold text-sm">Cảnh báo tính đại diện của mẫu (Data Integrity Guard)</h4>
            <p className="text-xs text-amber-800 leading-relaxed">
              {sample_size_notice || 'Cỡ mẫu hiện tại chưa đạt ngưỡng N >= 5 để đảm bảo ý nghĩa thống kê tổng thể.'} Các tỷ lệ phân phối dưới đây chỉ mang tính chất mô tả các phản hồi đã thu thập thực tế.
            </p>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tổng phản hồi đã lưu</span>
            <div className="text-3xl font-extrabold text-slate-900">{total_responses}</div>
            <span className="text-xs text-slate-400">100% dữ liệu thực</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Thời gian làm bài TB</span>
            <div className="text-3xl font-extrabold text-slate-900">{avg_duration_seconds}s</div>
            <span className="text-xs text-slate-400">Độ dài trung bình mỗi lượt</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tỷ lệ hoàn thành toàn bài</span>
            <div className="text-3xl font-extrabold text-emerald-600">
              {analytics.overall_completion_rate ?? 100}%
            </div>
            <span className="text-xs text-slate-400">Trả lời đủ câu hỏi bắt buộc</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <CheckCircle className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Phân loại rủi ro</span>
            <div className="flex items-center gap-2 pt-1 text-sm font-bold">
              <span className="text-emerald-600">{risk_distribution['low'] || 0} thấp</span>
              <span>•</span>
              <span className="text-amber-600">{risk_distribution['medium'] || 0} vừa</span>
              <span>•</span>
              <span className="text-rose-600">{risk_distribution['high'] || 0} cao</span>
            </div>
            <span className="text-xs text-slate-400">Được phân tích tự động</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center text-amber-600">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Benford's Law First-Digit Statistical Analysis */}
      <BenfordAnalysisCard surveyId={surveyId} />

      {/* AI Qualitative Analysis & Sentiment Insights */}
      <AIQualitativeInsightsCard surveyId={surveyId} />

      {/* Cross-Tabulation & Chi-Square Independence Test */}
      <CrossTabulationCard surveyId={surveyId} questions={analytics.questions_analytics} />

      {/* Psychometric Scale Reliability Analysis (Cronbach's Alpha & Item-Total Statistics) */}
      <ScaleReliabilityCard surveyId={surveyId} />

      {/* Exploratory Factor Analysis (EFA), Scree Plot & Varimax Orthogonal Rotation */}
      <EFAAnalysisCard surveyId={surveyId} />

      {/* Bivariate Correlation Matrix (Pearson r & Spearman rho) & Interactive Heatmap */}
      <CorrelationMatrixCard surveyId={surveyId} />

      {/* Hypothesis Testing T-Test (Independent & Paired Pre-Post) & Effect Sizes */}
      <HypothesisTTestCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type,
          options: q.option_distribution ? Object.keys(q.option_distribution) : []
        }))}
      />

      {/* One-Way ANOVA & Post-Hoc Tukey HSD Pairwise Analysis */}
      <ANOVAAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type,
          options: q.option_distribution ? Object.keys(q.option_distribution) : []
        }))}
      />

      {/* Multiple Linear Regression OLS & Multicollinearity VIF Diagnostic */}
      <LinearRegressionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Statistical Mediation & Path Analysis (Baron & Kenny 1986, Sobel 1982, Hayes 2018) */}
      <MediationAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Statistical Moderation & Interaction Effects (PROCESS Model 1 - Hayes 2018, Aiken & West 1991) */}
      <ModerationAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Moderated Mediation Analysis (PROCESS Model 7 - Hayes 2018) */}
      <ModeratedMediationCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Two-Stage Complex Survey Sampling & Taylor Series Linearization (Cochran 1977, Kish 1965) */}
      <ComplexSamplingCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Propensity Score Matching & IPW Causal Inference Engine (Rosenbaum & Rubin 1983, Austin 2011) */}
      <PropensityMatchingCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Structural Topic Modeling & Latent Dirichlet Allocation (Blei et al. 2003, Roberts et al. 2014) */}
      <TopicModelingCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Psychometric Network Analysis & Gaussian Graphical Model (Borsboom & Cramer 2013, Epskamp et al. 2018) */}
      <PsychometricNetworkCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Item Response Theory 2-Parameter Logistic & Item Characteristic Curves (Birnbaum 1968, Reckase 2009) */}
      <IRT2PLCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Survival Analysis & Time-to-Drop-off (Kaplan-Meier & Cox Proportional Hazards) */}
      <SurvivalDropOffCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Multilevel Modeling & Hierarchical Linear Models (HLM / MLM; Raudenbush & Bryk 2002) */}
      <MultilevelModelingCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Choice-Based Conjoint (CBC / DCE) & Market Simulator (McFadden 1974, Green & Srinivasan 1990) */}
      <ConjointAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Latent Class Analysis (LCA) & Finite Mixture Segmentation (Goodman 1974, McLachlan 2000) */}
      <LatentClassAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Difference-in-Differences (DiD) & Policy Impact Evaluation (Card & Krueger 1994, Angrist & Pischke 2009) */}
      <DifferenceInDifferencesCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Structural Equation Modeling (SEM) & Path Analysis (Wright 1934, Jöreskog 1970, Hu & Bentler 1999) */}
      <SEMPathAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Competing Risks & Shared Frailty Survival Engine (Fine & Gray 1999, Hougaard 2000, Wienke 2010) */}
      <CompetingRisksFrailtyCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Item Response Theory (IRT) 3PL & 4PL Models & CAT Simulation (Birnbaum 1968, Lord 1980, Magis 2013) */}
      <IRT4PLAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Propensity Score Weighting (IPW) & Doubly Robust Estimation (Rosenbaum & Rubin 1983, Robins 1994, Austin 2015) */}
      <IPWDoublyRobustCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Generalized Additive Models (GAM) & Spline Regression (Hastie & Tibshirani 1990, Wood 2017) */}
      <GAMSplineRegressionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Quantile Regression & Conditional Distributional Effects (Koenker & Bassett 1978, Koenker 2005) */}
      <QuantileRegressionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Generalizability Theory (G-Theory & D-Study; Cronbach et al. 1972, Brennan 2001) */}
      <GTheoryCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Regression Discontinuity Design (Sharp RDD; Thistlethwaite & Campbell 1960, Hahn et al. 2001, Imbens & Kalyanaraman 2012) */}
      <RDDCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Synthetic Control Method (SCM; Abadie et al. 2010, Abadie 2021) */}
      <SyntheticControlCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Small Area Estimation (SAE & Fay-Herriot Empirical Bayes; Fay & Herriot 1979, Rao & Molina 2015) */}
      <SmallAreaEstimationCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Dynamic Event-Study & Staggered DiD (Hausman & Rapson 2018, Sun & Abraham 2021) */}
      <EventStudyCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Bayesian Structural Time Series (BSTS) & Causal Impact (Brodersen et al. 2015, Harvey 1989) */}
      <BSTSCausalImpactCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Doubly Robust AIPW & Heterogeneous Treatment Effects CATE (Robins et al. 1994, Chernozhukov et al. 2018) */}
      <AIPWCATECard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Instrumental Variables Two-Stage Least Squares (2SLS) & Weak Instruments (Stock & Yogo 2005) */}
      <IV2SLSCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Bifactor Psychometric Modeling & Essential Unidimensionality (Reise 2012, Rodriguez et al. 2016) */}
      <BifactorCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Panel Vector Autoregression (Panel VAR) & Granger Causality (Holtz-Eakin et al. 1988, Abrigo & Love 2016) */}
      <PanelVARCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Latent Growth Curve Modeling (LGCM) Engine (Meredith & Tisak 1990, Bollen & Curran 2006) */}
      <LatentGrowthCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Quantile Treatment Effects (QTE) & Distributional Treatment Effects (Firpo 2007, Koenker & Bassett 1978) */}
      <QTECard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Causal DAG & Structure Learning Engine (Spirtes et al. 2000, Pearl 2009, Meek 1995) */}
      <CausalDAGCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Marginal Structural Models (MSM) with Stabilized IPTW (Robins et al. 2000, Hernán & Robins 2024) */}
      <MSMCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Generalized Estimating Equations (GEE) - Population-Averaged Longitudinal Models (Liang & Zeger 1986) */}
      <GEECard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Exact Permutation & Randomization Inference (Fisher's Sharp Null 1935, Rosenbaum 2002) */}
      <RandomizationInferenceCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Extreme Value Theory (EVT) & Survey Tail Risk Modeling (Pickands 1975, McNeil & Frey 2000) */}
      <EVTCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Joint Modeling (JM) of Longitudinal Trajectories & Panel Drop-off Survival (Wulfsohn & Tsiatis 1997, Rizopoulos 2012) */}
      <JointModelCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Conformal Prediction & Distribution-Free Risk Intervals (Vovk et al. 2005, Angelopoulos & Bates 2023) */}
      <ConformalPredictionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Multilevel Structural Equation Modeling (MSEM; Preacher, Zyphur & Zhang 2010, Muthén 1994) */}
      <MSEMCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Targeted Maximum Likelihood Estimation (TMLE; van der Laan & Rose 2011) */}
      <TMLECard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Synthetic Difference-in-Differences (SDID; Arkhangelsky, Athey, Imbens & Wager 2021) */}
      <SDIDCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Generalized Causal Forest (GRF; Athey, Tibshirani & Wager 2019) */}
      <CausalForestCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Causal Mediation Analysis with Sensitivity Analysis (Imai, Keele & Tingley 2010) */}
      <CausalMediationSensitivityCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Dynamic Time Warping (DTW) Trajectory Clustering (Sakoe & Chiba 1978; Petitjean et al. 2011) */}
      <DTWClusteringCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Causal Interaction Trees & Honest Subgroup Identification (Athey & Imbens 2016) */}
      <CausalTreeCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Multiple Testing Correction & False Discovery Rate (FDR Matrix) (Benjamini & Hochberg 1995, Storey 2002) */}
      <MultipleTestingFDRCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Bayesian Structural Equation Modeling (BSEM) (Muthén & Asparouhov 2012) */}
      <BSEMCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Endogeneity Control via Gaussian Copula (Park & Gupta 2012) */}
      <GaussianCopulaCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Dynamic Factor Modeling (DFM) with Kalman Filter & RTS State-Space Smoothing (Stock & Watson 2002, Durbin & Koopman 2012) */}
      <DynamicFactorModelCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Extreme Bound Analysis (EBA) Specification Curve Engine (Leamer 1983, Sala-i-Martin 1997) */}
      <ExtremeBoundsAnalysisCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Spatial Econometrics & Moran's I Autoregressive Models (SAR / SEM; Anselin 1988, LeSage & Pace 2009) */}
      <SpatialEconometricsCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Instrumental Variable Quantile Regression (IV-QR; Chernozhukov & Hansen 2005, 2008) */}
      <IVQuantileRegressionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Choice-Based Conjoint with Hierarchical Bayes (HB-CBC; Rossi et al. 2005, McFadden 1974) */}
      <ConjointHBCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Fractional Response Regression QMLE (Papke & Wooldridge 1996, 2008) */}
      <FractionalResponseCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Multidimensional Item Response Theory (MIRT; Reckase 2009) */}
      <MIRTCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Heckman Two-Step Sample Selection Model (Heckman 1979 Nobel Prize) */}
      <HeckmanSelectionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Stochastic Frontier Analysis (SFA) & Technical Efficiency (Aigner et al. 1977, JLMS 1982) */}
      <StochasticFrontierCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Zero-Inflated Count Regression Models (ZIP & ZINB; Lambert 1992, Greene 1994, Vuong 1989) */}
      <ZeroInflatedCountCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Latent Moderated Structural Equations (LMS / QML; Klein & Moosbrugger 2000, Marsh et al. 2004) */}
      <LatentModerationCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Endogenous Switching Regression (ESR - FIML; Maddala 1983, Lokshin & Sajaia 2004) */}
      <EndogenousSwitchingCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Generalized Propensity Score & Dose-Response Analysis (Hirano & Imbens 2004) */}
      <GPSDoseResponseCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Causal Discovery DAG Engine (LiNGAM & ANM; Shimizu et al. 2006, Hoyer et al. 2009) */}
      <CausalDiscoveryCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Bayesian Additive Regression Trees (BART) Causal Engine (Chipman et al. 2010, Hill 2011) */}
      <BARTCausalCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Choice-Based Conjoint (CBC) & Discrete Choice Experiment (DCE; McFadden 1974, Train 2009) */}
      <ConjointChoiceCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Multi-Group SEM Invariance & Latent Means Difference (Meredith 1993, Byrne 2013) */}
      <MGSEMInvarianceCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Generalized Additive Models (GAM) & Penalized Splines (Hastie & Tibshirani 1990; Wood 2017) */}
      <GAMSplineCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Latent Profile Analysis (LPA) & Gaussian Finite Mixture Models (McLachlan & Peel 2000; Collins & Lanza 2010) */}
      <LatentProfileCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Shapley Value Regression & Key Driver Analysis (Lipovetsky & Conklin 2001; Lundberg & Lee 2017) */}
      <ShapleyDriverCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Plackett-Luce Choice Model & Rank-Ordered Logit (Luce 1959; Plackett 1975; Hunter 2004 MM) */}
      <PlackettLuceCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* MaxDiff Best-Worst Scaling Case 1 (Finn & Louviere 1992; Marley & Louviere 2005) */}

      <MaxDiffCard

        surveyId={surveyId}

        questions={analytics.questions_analytics.map((q) => ({

          id: q.question_id,

          title: q.question_title,

          question_type: q.question_type

        }))}

      />



      {/* Gaussian Bayesian Network DAG Structure Learning (Heckerman 1995; Scutari 2010) */}

      <BayesianNetworkCard

        surveyId={surveyId}

        questions={analytics.questions_analytics.map((q) => ({

          id: q.question_id,

          title: q.question_title,

          question_type: q.question_type

        }))}

      />



      {/* Stochastic Dominance & Distributional Inequality (Davidson & Duclos 2000; Hadar & Russell 1969) */}
      <StochasticDominanceCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Manski Non-Parametric Partial Identification & Worst-Case Bounds (Manski 1990, 2000; Imbens & Manski 2004) */}
      <ManskiBoundsCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine (Murphy 2003, Robins 2004) */}
      <DynamicTreatmentRegimesCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine (Rost 1990; von Davier & Rost 2007) */}
      <FiniteMixtureRaschCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Double / Debiased Machine Learning (DML) for Causal Inference (Chernozhukov et al. 2018) */}
      <DoubleMachineLearningCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />
      {/* Regression Kink Design (RKD) Engine (Card, Lee, Pei, & Weber 2015; Dong 2018) */}
      <RegressionKinkCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />
      {/* Staggered Difference-in-Differences (Callaway & Sant'Anna 2021; Goodman-Bacon 2021) */}
      <StaggeredDIDCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />
      {/* Matrix Completion for Causal Panel Data (Athey, Bayati, Doudchenko, Imbens, & Khosravi 2021) */}
      <MatrixCompletionCausalCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Synthetic Difference-in-Differences Advanced (Arkhangelsky et al. 2021 AER) */}
      <SDIDAdvancedCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Interactive Fixed Effects & Factor Models (Bai 2009; Gobillon & Magnac 2016) */}
      <InteractiveFixedEffectsCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Multiple Sequential Mediators (VanderWeele 2014; Steen et al. 2012) */}
      <MultipleMediatorsCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Doubly Robust Policy Learning (Athey & Wager 2021 Econometrica) */}
      <PolicyLearningCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* RDD Local Randomization for Discrete Running Variables (Cattaneo, Frandsen, & Titiunik 2015 JCA) */}
      <RDDLocalRandomizationCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Dynamic Panel System & Difference GMM (Arellano & Bond 1991; Blundell & Bond 1998; Windmeijer 2005) */}
      <DynamicPanelGMMCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Weak-Instrument Robust Inference (Anderson-Rubin 1949, Moreira 2003 CLR, Montiel Olea & Pflueger 2013) */}
      <WeakIVRobustCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Sequential Causal Mediation Analysis (Hayes Model 6 / Imai & Yamamoto 2013) */}
      <SequentialMediationCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Post-Double-Selection Lasso for High-Dimensional Confounders (Belloni, Chernozhukov, & Hansen 2014) */}
      <PostDoubleSelectionLassoCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Instrumental Variable Local Average Response Function (LARF; Abadie 2003 Econometrica) */}
      <LARFCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Marginal Treatment Effects & Local Instrumental Variables (MTE / LIV; Heckman & Vytlacil 2005) */}
      <MTECard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Non-random Survey Attrition & Selection Bounds (Lee Bounds; Lee 2009 Restud) */}
      <LeeBoundsCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Surrogate Index Long-Term Causal Evaluation (Athey, Chetty, Imbens, & Kang 2019) */}
      <SurrogateIndexCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Conformal Counterfactual Risk Inference (Chernozhukov et al. 2021; Lei & Candes 2021) */}
      <ConformalCounterfactualCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Causal Sensitivity Analysis & Omitted Variable Bias Contours (Cinelli & Hazlett 2020) */}
      <CausalSensitivityBiasCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Bayesian Causal Forest (BCF; Hahn, Murray, & Carver 2020) */}
      <BCFCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Shift-Share / Bartik Instrumental Variables & Rotemberg Decomposition (Goldsmith-Pinkham et al. 2020) */}
      <ShiftShareIVCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Quantile Synthetic Control & Distributional Counterfactuals (Gunsilius 2023 Econometrica) */}
      <QuantileSyntheticControlCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Two-Way Fixed Effects (TWFE) Decomposition & Negative Weights Diagnostics (de Chaisemartin & D'Haultfoeuille 2020 AER) */}
      <TWFEDecompositionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Factor Instrumental Variables & Principal Component 2SLS (Bai & Ng 2010 Econometrica) */}
      <FactorIVCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Nested Logit Structural Choice & Substitution Elasticities (McFadden 1978 Nobel Prize) */}
      <NestedLogitCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Automatic Debiased Machine Learning via Riesz Representer Learning (Chernozhukov, Newey, & Singh 2022) */}
      <AutoDMLRieszCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Local Instrumental Variables & Marginal Treatment Effects (Heckman & Vytlacil 2005 Econometrica) */}
      <LocalInstrumentalVariablesCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Conformal Optimal Transport Counterfactual Distributional Alignment (Cuturi 2013 NeurIPS; Courty 2017) */}
      <ConformalOptimalTransportCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Bayesian Nonparametric Dirichlet Process Mixture Density Deconvolution (Ferguson 1973; Escobar & West 1995) */}
      <DPMDeconvolutionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Multi-Cutoff Regression Discontinuity & Boundary Treatment Effects (Cattaneo 2015; Bertanha 2020) */}
      <MultiCutoffRDCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* High-Dimensional Causal Mediation & Latent Path Invariance (Imai 2010; VanderWeele 2015; Zhao & Luo 2022) */}
      <HighDimensionalMediationCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Causal Inference under Network Interference & Peer Spillover (Hudgens 2008; Aronow & Samii 2017) */}
      <NetworkSpilloverCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Dynamic Spatial Panel Econometrics & Spatio-Temporal Diffusion (Elhorst 2014; Lee & Yu 2010; LeSage & Pace 2009) */}
      <DynamicSpatialPanelCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Continuous Policy Shift & Doubly Robust Dosage Response (Kennedy et al. 2017 JASA; Chernozhukov et al. 2022) */}
      <ContinuousPolicyShiftCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Generalized Synthetic Control & Latent Interactive Factor Engine (Xu 2017 Political Analysis; Bai 2009; Gobillon & Magnac 2016) */}
      <GeneralizedSyntheticControlCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Choice-Based Conjoint Hierarchical Bayes & Market Simulator (Rossi et al. 2005; Train 2009) */}
      <HierarchicalBayesConjointCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Nonparametric Boundary Kernel Deconvolution & Measurement Error Correction (Delaigle & Meister 2008 JASA; Fan 1991) */}
      <BoundaryKernelDeconvolutionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Targeted Maximum Likelihood Estimation with Efficient Influence Curve Inference (TMLE; van der Laan & Rose 2011; Schuler & Rose 2017) */}
      <TargetedMaximumLikelihoodCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Copula-Based Endogeneity Correction Engine (Park & Gupta 2012 Marketing Science; Tran & Tsionas 2015) */}
      <CopulaEndogeneityCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Causal Survival Analysis & RMST Engine (Royston & Parmar 2013; Díaz et al. 2019; Knaus 2022) */}
      <CausalSurvivalRMSTCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Dynamic Discrete Choice Structural Dynamic Programming Engine (Rust 1987 NFXP) */}
      <DynamicDiscreteChoiceCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Synthetic Difference-in-Differences Engine (Arkhangelsky et al. 2021 AER) */}
      <SyntheticDiffInDiffCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Distributional Oaxaca-Blinder & RIF Decomposition Engine (Firpo et al. 2009 Econometrica, 2018) */}
      <RIFOaxacaDecompositionCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />

      {/* Difference-in-Discontinuities Design Engine (Diff-in-Disc / RD-DID; Grembi et al. 2016 AER) */}
      <DiffInDiscontinuitiesCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type
        }))}
      />









      {/* Non-Parametric Hypothesis Tests (Mann-Whitney U, Wilcoxon Signed-Rank, Kruskal-Wallis & Dunn Post-Hoc) */}
      <NonParametricTestsCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Missing Data Pattern Diagnostics & Multiple Imputation Engine (Little's MCAR 1988, EM, PMM) */}
      <MissingDataCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Scale Equating & Concordance Transformation Engine (Linear & Equipercentile Equating) */}
      <ScaleEquatingCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Multi-Group Measurement Invariance Testing (Configural, Metric, Scalar, Strict Invariance) */}
      <MeasurementInvarianceCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Common Method Bias / Variance (CMB/CMV) Diagnostics (Harman, Marker Variable, ULMCF) */}
      <CommonMethodBiasCard
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Statistical Power Analysis & Sample Size Estimator (Cohen 1988 & Cochran 1977) */}
      <SamplePowerAnalysisCard surveyId={surveyId} />

      {/* Split-Ballot & Question Wording Experimentation (Schuman & Presser) */}
      <SplitBallotExperimentCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type,
          options: q.option_distribution ? Object.keys(q.option_distribution) : []
        }))}
      />

      {/* Rasch Model 1-PL & Wright Map (Item Response Theory) */}
      <RaschWrightMapCard surveyId={surveyId} />

      {/* Respondent Clustering & Typology Segmentation (K-Means & Silhouette) */}
      <RespondentClusterCard surveyId={surveyId} />

      {/* Pairwise Response Similarity Matrix & Collusion Syndicate Rings (AAPOR & ISO 20252) */}
      <PairwiseSimilarityCard surveyId={surveyId} />

      {/* Geographic Spatial Clustering & Geo-Fencing Compliance (DBSCAN & ISO 20252 §4.5.3) */}
      <SpatialGeoAuditCard surveyId={surveyId} />

      {/* Longitudinal Wave-over-Wave Comparative Analytics & Cohen's d Effect Size */}
      <LongitudinalComparisonCard currentSurveyId={surveyId} currentSurveyTitle={survey_title} />

      {/* Sampling Quotas & Demographic Stratification Control */}
      <SamplingQuotaCard
        surveyId={surveyId}
        questions={analytics.questions_analytics.map((q) => ({
          id: q.question_id,
          title: q.question_title,
          question_type: q.question_type,
          options: q.option_distribution ? Object.keys(q.option_distribution) : []
        }))}
      />

      {/* Cognitive Burden & Inattention Pacing Analyzer */}
      <CognitivePacingCard surveyId={surveyId} />

      {/* Multivariate Outlier & Mahalanobis Distance Detection */}
      <MultivariateOutlierCard surveyId={surveyId} />

      {/* Survey Drop-Off Funnel & Completion Card */}
      {analytics.funnel_analytics && analytics.funnel_analytics.length > 1 && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-indigo-600" />
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Phễu Hoàn Thành & Điểm Nghẽn Rơi Rụng (Drop-Off Funnel)
                </h3>
                <p className="text-xs text-slate-500">
                  Đo lường mức độ mệt mỏi nhận thức và tỷ lệ bỏ dở giữa chừng qua từng câu hỏi (Phương pháp luận Don Dillman)
                </p>
              </div>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg self-start sm:self-auto">
              Hoàn thành toàn bài: {analytics.overall_completion_rate ?? 100}%
            </span>
          </div>

          <div className="space-y-3 pt-1">
            {analytics.funnel_analytics.map((step) => {
              const isHighDrop = (step.drop_off_pct || 0) >= 15;
              return (
                <div key={step.question_id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-medium text-slate-700">
                    <span className="line-clamp-1 max-w-[70%]">
                      <strong className="text-slate-900">Câu #{step.step}:</strong> {step.question_title}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      {isHighDrop && (
                        <span className="text-[11px] font-bold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                          ⚠️ Rơi rụng {step.drop_off_pct}%
                        </span>
                      )}
                      <span className="text-slate-500 font-mono">
                        {step.total_answers} trả lời ({step.completion_rate_pct}%)
                      </span>
                    </div>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isHighDrop ? 'bg-amber-500' : 'bg-indigo-600'
                      }`}
                      style={{ width: `${step.completion_rate_pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Per-Question Analytics */}
      <div className="space-y-6">
        <h2 className="text-lg font-bold text-slate-900">Chi tiết phân bố theo từng câu hỏi</h2>

        {questions_analytics.map((q, idx) => (
          <div
            key={q.question_id}
            className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
                  Câu hỏi {idx + 1} • {q.question_type}
                </span>
                <h3 className="text-base font-bold text-slate-900">{q.question_title}</h3>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => {
                    setChartExportQuestionId(q.question_id);
                    setIsChartExportOpen(true);
                  }}
                  className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-violet-700 bg-violet-50 hover:bg-violet-100 border border-violet-200 rounded-lg transition-all"
                  title="Xuất biểu đồ phân bố cho câu hỏi này (SVG / PNG 300 DPI)"
                >
                  <BarChart2 className="w-3.5 h-3.5 text-violet-600" />
                  <span>Xuất đồ thị</span>
                </button>
                {q.drop_off_rate && q.drop_off_rate > 10 ? (
                  <span className="text-[11px] text-amber-700 font-semibold bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                    Rơi rụng {q.drop_off_rate}%
                  </span>
                ) : null}
                <span className="text-xs text-slate-500 font-medium whitespace-nowrap bg-slate-100 px-2.5 py-1 rounded-full">
                  {q.total_answers} câu trả lời ({q.completion_rate ?? 100}%)
                </span>
              </div>
            </div>

            {/* Option distribution bars */}
            {q.option_distribution && (
              <div className="space-y-3 pt-2">
                {Object.entries(q.option_distribution).map(([label, count]) => {
                  const percent = q.total_answers > 0 ? Math.round((count / q.total_answers) * 100) : 0;
                  return (
                    <div key={label} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-medium text-slate-700">
                        <span className="line-clamp-1">{label}</span>
                        <span className="text-slate-500 shrink-0 font-semibold">{count} ({percent}%)</span>
                      </div>
                      <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Numeric summary */}
            {q.stats_summary && q.stats_summary.min !== undefined && (
              <div className="grid grid-cols-3 gap-3 p-3 bg-slate-50 rounded-xl text-center text-xs">
                <div>
                  <span className="text-slate-400 block">Thấp nhất (Min)</span>
                  <span className="font-bold text-slate-800 text-sm">{q.stats_summary.min}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Trung bình (Avg)</span>
                  <span className="font-bold text-indigo-600 text-sm">{q.stats_summary.avg}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Cao nhất (Max)</span>
                  <span className="font-bold text-slate-800 text-sm">{q.stats_summary.max}</span>
                </div>
              </div>
            )}

            {/* Matrix summary */}
            {q.stats_summary?.matrix_distribution && (
              <div className="space-y-2 pt-1 overflow-x-auto">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Phân bố tần suất theo ma trận tiêu chí
                </span>
                <table className="w-full text-xs text-left border-collapse border border-slate-200 rounded-lg overflow-hidden">
                  <thead className="bg-slate-50 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3 border border-slate-200">Tiêu chí</th>
                      {Object.keys(Object.values(q.stats_summary.matrix_distribution)[0] || {}).map((col) => (
                        <th key={col} className="py-2.5 px-3 border border-slate-200 text-center">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {Object.entries(q.stats_summary.matrix_distribution).map(([rowLabel, colCounts]: [string, any]) => (
                      <tr key={rowLabel} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-medium text-slate-800 border border-slate-200">{rowLabel}</td>
                        {Object.entries(colCounts).map(([cLabel, count]: [string, any]) => (
                          <td key={cLabel} className="py-2.5 px-3 text-center border border-slate-200 font-semibold text-indigo-700">
                            {count}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Ranking summary */}
            {q.stats_summary?.ranking_averages && (
              <div className="space-y-2 pt-1">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Thứ hạng trung bình các mục ưu tiên (Số càng nhỏ biểu thị mức ưu tiên càng cao)
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {Object.entries(q.stats_summary.ranking_averages).map(([itemLabel, avgRank]: [string, any]) => (
                    <div key={itemLabel} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-800">{itemLabel}</span>
                      <span className="font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-200">
                        Hạng TB: {avgRank}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Text Samples */}
            {q.recent_text_samples && q.recent_text_samples.length > 0 && (
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Các câu trả lời mẫu gần đây
                </span>
                <div className="space-y-1.5">
                  {q.recent_text_samples.map((sample, sIdx) => (
                    <div key={sIdx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-xs text-slate-700 italic">
                      "{sample}"
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quality Audit Report & Legal Compliance Modal */}
      <QualityAuditReportModal
        surveyId={surveyId}
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        onRefreshAnalytics={loadAnalytics}
      />

      {/* Automated Data Cleansing Modal */}
      <DataCleansingModal
        surveyId={surveyId}
        isOpen={isCleansingOpen}
        onClose={() => setIsCleansingOpen(false)}
        onSuccess={loadAnalytics}
      />

      {/* Academic Codebook & Statistical Syntax Modal */}
      <CodebookModal
        isOpen={isCodebookOpen}
        onClose={() => setIsCodebookOpen(false)}
        surveyId={surveyId}
        surveyTitle={analytics?.survey_title || 'Khảo sát'}
      />

      {/* Academic Manuscript Studio Modal */}
      <AcademicManuscriptModal
        isOpen={isManuscriptOpen}
        onClose={() => setIsManuscriptOpen(false)}
        surveyId={surveyId}
        surveyTitle={analytics?.survey_title || 'Khảo sát'}
      />

      {/* Survey Logic DAG & Branching Simulator Modal */}
      <SurveyLogicSimulatorModal
        isOpen={isLogicSimulatorOpen}
        onClose={() => setIsLogicSimulatorOpen(false)}
        surveyId={surveyId}
        surveyTitle={analytics?.survey_title || 'Khảo sát'}
      />

      {/* High-Resolution Academic Chart Export Modal */}
      <AcademicChartExportModal
        isOpen={isChartExportOpen}
        onClose={() => setIsChartExportOpen(false)}
        analytics={analytics}
        initialQuestionId={chartExportQuestionId}
      />

      {/* Demographic Raking (IPF) Scientific Weighting Modal */}
      <DemographicRakingModal
        isOpen={isRakingOpen}
        onClose={() => setIsRakingOpen(false)}
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />

      {/* Differential Item Functioning (DIF) Analysis Modal */}
      <DIFAnalysisModal
        isOpen={isDIFOpen}
        onClose={() => setIsDIFOpen(false)}
        surveyId={surveyId}
        questions={analytics.questions_analytics}
      />
    </div>
  );
};
