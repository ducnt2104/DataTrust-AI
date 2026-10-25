import React, { useState } from 'react';
import {
  AutoDMLRieszResult,
  AutoDMLRieszRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Cpu,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertTriangle,
  AlertCircle,
  ShieldCheck,
  Sparkles,
  Sliders,
  Layers,
  Activity,
  CheckCircle2,
  TrendingUp,
  Percent,
  Compass,
  Zap,
  BarChart3,
  Scale
} from 'lucide-react';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface Props {
  surveyId: string;
  questions: QuestionSummary[];
}

export const AutoDMLRieszCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [functionalType, setFunctionalType] = useState<'ate' | 'policy_shift' | 'marginal_derivative'>('ate');
  const [shiftDelta, setShiftDelta] = useState<number>(1.0);
  const [nSplits, setNSplits] = useState<number>(5);
  const [ridgeLambda, setRidgeLambda] = useState<number>(0.001);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<AutoDMLRieszResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleToggleCovariate = (qId: string) => {
    if (selectedCovariates.includes(qId)) {
      setSelectedCovariates(selectedCovariates.filter(id => id !== qId));
    } else {
      setSelectedCovariates([...selectedCovariates, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId) {
      setError('Vui lòng chọn biến kết quả Y và biến can thiệp D.');
      return;
    }

    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả Y và biến can thiệp D không được trùng nhau.');
      return;
    }

    if (selectedCovariates.length === 0) {
      setError('Vui lòng chọn ít nhất một biến kiểm soát / đồng biến (Covariates X).');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: AutoDMLRieszRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      covariate_question_ids: selectedCovariates,
      functional_type: functionalType,
      shift_delta: shiftDelta,
      n_splits: nSplits,
      ridge_lambda: ridgeLambda,
      alpha_level: 0.05,
      scope
    };

    try {
      const res = await api.runAutoDMLRiesz(surveyId, payload);
      if (res.status === 'ERROR') {
        setError(res.message || 'Lỗi khi thực hiện Automatic Debiased Machine Learning.');
        setResult(null);
      } else if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Cỡ mẫu chưa đủ để thực hiện Auto-DML.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối máy chủ.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setOutcomeQId('');
    setTreatmentQId('');
    setSelectedCovariates([]);
    setFunctionalType('ate');
    setShiftDelta(1.0);
    setNSplits(5);
    setRidgeLambda(0.001);
    setResult(null);
    setError(null);
  };

  const handleCopyNarrative = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const summ = result?.overall_summary;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-sky-500/10 border border-sky-500/20 rounded-lg text-sky-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                Automatic Debiased Machine Learning via Riesz Representer Learning
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-sky-950/80 text-sky-400 border border-sky-800/60">
                  Chernozhukov et al. (2022) Econometrica
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Tự động học hàm biểu diễn Riesz &alpha;<sub>0</sub>(W) để khử thiên lệch chính quy hóa ML với trực giao Neyman &amp; Cross-Fitting K-Fold mà không cần đạo hàm thủ công.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700/80 rounded-lg transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Làm mới
          </button>
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !outcomeQId || !treatmentQId || selectedCovariates.length === 0}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow transition-all"
          >
            {loading ? (
              <>
                <Activity className="w-3.5 h-3.5 animate-spin" />
                Đang học Riesz &amp; Cross-Fitting...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Ước lượng Auto-DML
              </>
            )}
          </button>
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-6">
        {/* Outcome Y */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
            1. Biến Kết Quả Y (Outcome)
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="">-- Chọn câu hỏi đo lường Y --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Biến số liên tục (e.g. Doanh thu, Điểm số, Đánh giá).</span>
        </div>

        {/* Treatment D */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            2. Biến Can Thiệp D (Treatment / Policy)
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="">-- Chọn câu hỏi can thiệp D --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Nhị phân (0/1) hoặc liều lượng can thiệp liên tục.</span>
        </div>

        {/* Functional Type & Policy Shift */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-indigo-400" />
            3. Mục Tiêu Ước Lượng (Target Parameter)
          </label>
          <div className="grid grid-cols-3 gap-1 mb-2">
            <button
              type="button"
              onClick={() => setFunctionalType('ate')}
              className={`py-1 text-[11px] font-medium rounded ${
                functionalType === 'ate'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              ATE (0/1)
            </button>
            <button
              type="button"
              onClick={() => setFunctionalType('policy_shift')}
              className={`py-1 text-[11px] font-medium rounded ${
                functionalType === 'policy_shift'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              D + &delta; Shift
            </button>
            <button
              type="button"
              onClick={() => setFunctionalType('marginal_derivative')}
              className={`py-1 text-[11px] font-medium rounded ${
                functionalType === 'marginal_derivative'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Đạo Hàm Biên
            </button>
          </div>

          {functionalType === 'policy_shift' && (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-[11px] text-slate-400">&Delta; Liều lượng:</span>
              <input
                type="number"
                step="0.1"
                value={shiftDelta}
                onChange={(e) => setShiftDelta(parseFloat(e.target.value) || 1.0)}
                className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 text-right focus:outline-none"
              />
            </div>
          )}
        </div>
      </div>

      {/* Covariates & Advanced Options */}
      <div className="bg-slate-950/30 p-4 rounded-lg border border-slate-800/80 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            4. Biến Kiểm Soát / Đồng Biến Confounding X ({selectedCovariates.length} đã chọn)
          </label>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Cross-Fitting K:</span>
              <select
                value={nSplits}
                onChange={(e) => setNSplits(parseInt(e.target.value, 10))}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
              >
                <option value={3}>3 Folds</option>
                <option value={4}>4 Folds</option>
                <option value={5}>5 Folds (Khuyến nghị)</option>
                <option value={8}>8 Folds</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400">Phạm vi:</span>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
              >
                <option value="all">Tất cả mẫu</option>
                <option value="verified_clean">Chỉ mẫu sạch (Verified)</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-1">
          {numericQuestions
            .filter(q => q.id !== outcomeQId && q.id !== treatmentQId)
            .map(q => {
              const active = selectedCovariates.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => handleToggleCovariate(q.id)}
                  className={`px-2.5 py-1 rounded text-xs transition-colors flex items-center gap-1.5 ${
                    active
                      ? 'bg-purple-900/60 border border-purple-600/80 text-purple-200'
                      : 'bg-slate-800/80 border border-slate-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {active && <Check className="w-3 h-3 text-purple-400" />}
                  {q.title}
                </button>
              );
            })}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-red-950/50 border border-red-800/80 rounded-lg text-xs text-red-300 flex items-center gap-2 mb-6">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && summ && (
        <div className="space-y-6 pt-2">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Auto-DML Causal Effect */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-sky-500/30 relative overflow-hidden shadow-lg">
              <div className="absolute top-0 right-0 w-24 h-24 bg-sky-500/5 rounded-full blur-xl pointer-events-none" />
              <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block mb-1">
                Ước Lượng Auto-DML &theta;
              </span>
              <div className="text-2xl font-black text-slate-100">
                {summ.theta_autodml > 0 ? `+${summ.theta_autodml}` : summ.theta_autodml}
              </div>
              <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <span>SE: {summ.se_autodml}</span>
                <span>·</span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                  summ.p_value < 0.05 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-slate-800 text-slate-400'
                }`}>
                  p = {summ.p_value}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-2 font-mono">
                95% CI: [{summ.ci_95[0]}, {summ.ci_95[1]}]
              </div>
            </div>

            {/* Bias Removed */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-indigo-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400 block mb-1">
                Thiên Lệch Được Khử
              </span>
              <div className="text-2xl font-black text-indigo-300">
                {summ.debiasing_correction_magnitude}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                | &theta;<sub>Auto-DML</sub> - &theta;<sub>Naive ML</sub> |
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                Naive ML Plug-in: {summ.theta_naive_plugin}
              </div>
            </div>

            {/* Benchmark OLS */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Đối Chuẩn Hồi Quy OLS
              </span>
              <div className="text-2xl font-black text-slate-200">
                {summ.beta_ols_benchmark > 0 ? `+${summ.beta_ols_benchmark}` : summ.beta_ols_benchmark}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE OLS: {summ.se_ols_benchmark}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                Hồi quy tuyến tính truyền thống
              </div>
            </div>

            {/* Riesz Weight Diagnostics */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-emerald-500/30 p-4 rounded-xl shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 block mb-1">
                Độ Ổn Định Trọng Số Riesz
              </span>
              <div className="text-sm font-bold text-slate-100 flex items-center gap-1.5 mt-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>{summ.weight_stability_verdict}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                &alpha; SD: {summ.riesz_weight_sd} · Mean: {summ.riesz_weight_mean}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                R<sup>2</sup> Dự Báo Y: {summ.mean_outcome_r2}
              </div>
            </div>
          </div>

          {/* Model Specification Details */}
          <div className="bg-slate-950/40 border border-slate-800 rounded-lg p-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block">Cỡ mẫu phân tích (N):</span>
              <span className="font-semibold text-slate-200">{summ.sample_size} bản ghi</span>
            </div>
            <div>
              <span className="text-slate-500 block">Số đồng biến kiểm soát:</span>
              <span className="font-semibold text-slate-200">{summ.n_covariates} biến</span>
            </div>
            <div>
              <span className="text-slate-500 block">Kích thước từ điển phi(W):</span>
              <span className="font-semibold text-slate-200">{summ.basis_dimension_p} cơ sở đa thức</span>
            </div>
            <div>
              <span className="text-slate-500 block">Số phân vùng Cross-Fitting:</span>
              <span className="font-semibold text-slate-200">K = {summ.cross_fitting_splits_K} folds</span>
            </div>
          </div>

          {/* Scientific Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-hidden">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-sky-400" />
                  <span className="text-xs font-semibold text-slate-200">
                    Trực Quan Hóa Khoa Học: Phân Bố Trọng Số Riesz &amp; Biểu Đồ Rừng Đối Soánh Ước Lượng
                  </span>
                </div>
                <span className="text-[11px] text-slate-500">Vector SVG 780x360</span>
              </div>
              <div
                className="w-full flex justify-center bg-slate-950 rounded-lg p-2 overflow-x-auto"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Báo Cáo Thuyết Minh Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 bg-slate-800 px-2 py-1 rounded transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      Sao chép
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/80 p-3 rounded border border-slate-800/80">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
