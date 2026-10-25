import React, { useState } from 'react';
import {
  HelpCircle,
  Play,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Info,
  Copy,
  Sliders,
  Layers,
  Activity,
  Award,
  TrendingDown,
  TrendingUp,
  Percent,
  Search,
  Filter,
  ShieldCheck
} from 'lucide-react';
import { api } from '../api/client';
import { CausalSensitivityRequest, CausalSensitivityResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface CausalSensitivityBiasCardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const CausalSensitivityBiasCard: React.FC<CausalSensitivityBiasCardProps> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [qReduction, setQReduction] = useState<number>(1.0);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [multipliers, setMultipliers] = useState<number[]>([1.0, 2.0, 3.0]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalSensitivityResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId) {
      setError('Vui lòng chọn Biến kết quả (Y) và Biến can thiệp (D).');
      return;
    }
    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả và Biến can thiệp không được trùng lặp.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: CausalSensitivityRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      covariate_question_ids: selectedCovariates.filter(
        (id) => id !== outcomeQId && id !== treatmentQId
      ),
      q_reduction: qReduction,
      alpha_level: alphaLevel,
      benchmark_multipliers: multipliers,
      scope: scope
    };

    try {
      const res = await api.runCausalSensitivityBias(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể thực hiện phân tích Causal Sensitivity.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng Causal Sensitivity.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/60 rounded-lg border border-emerald-200 dark:border-emerald-800">
            <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Causal Sensitivity &amp; Omitted Variable Bias Contours
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300">
                Cinelli &amp; Hazlett (2020 JRSS-B)
              </span>
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Định lượng độ bền vững của kết luận nhân quả trước biến ẩn gây nhiễu chưa quan sát qua Robustness Value (RV) và bản đồ đẳng mức.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !outcomeQId || !treatmentQId}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm ${
              loading || !outcomeQId || !treatmentQId
                ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white hover:shadow'
            }`}
          >
            {loading ? (
              <>
                <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                Đang phân tích độ nhạy...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2 fill-current" />
                Phân tích Độ nhạy &amp; RV
              </>
            )}
          </button>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50/70 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800">
        {/* Outcome Y */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Biến kết quả (Y):
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn câu hỏi kết quả --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Treatment D */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Biến can thiệp / Tiếp xúc (D):
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến can thiệp --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Target Reduction q */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Mục tiêu triệt tiêu hiệu ứng (q):
          </label>
          <select
            value={qReduction}
            onChange={(e) => setQReduction(parseFloat(e.target.value))}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500"
          >
            <option value={1.0}>100% Triệt tiêu (Giảm về 0.0) [Chuẩn]</option>
            <option value={0.5}>50% Triệt tiêu (Giảm một nửa)</option>
            <option value={0.25}>25% Triệt tiêu (Giảm một phần tư)</option>
          </select>
        </div>

        {/* Scope and Alpha */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Mức ý nghĩa thống kê (α) &amp; Phạm vi:
          </label>
          <div className="flex items-center gap-2">
            <select
              value={alphaLevel}
              onChange={(e) => setAlphaLevel(parseFloat(e.target.value))}
              className="text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2.5 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500 flex-1"
            >
              <option value={0.05}>α = 0.05 (95% CI)</option>
              <option value={0.01}>α = 0.01 (99% CI)</option>
              <option value={0.10}>α = 0.10 (90% CI)</option>
            </select>

            <div className="inline-flex rounded-md shadow-sm">
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`px-2 py-1.5 text-xs font-medium rounded-l-md border ${
                  scope === 'all'
                    ? 'bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                }`}
              >
                Tất cả
              </button>
              <button
                type="button"
                onClick={() => setScope('verified_clean')}
                className={`px-2 py-1.5 text-xs font-medium rounded-r-md border-t border-b border-r ${
                  scope === 'verified_clean'
                    ? 'bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                }`}
              >
                Sạch
              </button>
            </div>
          </div>
        </div>

        {/* Covariates Multi-Select */}
        <div className="col-span-1 md:col-span-2 lg:col-span-4 space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Biến kiểm soát quan sát được (X) làm mốc đối chuẩn (Benchmarks):</span>
            <span className="text-slate-400 font-normal">Đã chọn {selectedCovariates.length} biến</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
            {questions
              .filter((q) => q.id !== outcomeQId && q.id !== treatmentQId)
              .map((q) => {
                const isSelected = selectedCovariates.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleCovariate(q.id)}
                    className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                      isSelected
                        ? 'bg-emerald-50 dark:bg-emerald-950/80 border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300 font-medium'
                        : 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
                    }`}
                  >
                    {q.title}
                  </button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/80 text-rose-700 dark:text-rose-300 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
          <div className="text-sm font-medium">{error}</div>
        </div>
      )}

      {/* Result Section */}
      {result && result.overall_summary && (
        <div className="space-y-6 pt-2">
          {/* KPI Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
              <div className="text-xs text-emerald-700 dark:text-emerald-300 font-semibold flex items-center justify-between">
                <span>Robustness Value (RV_q)</span>
                <span className="text-[10px] bg-emerald-200 dark:bg-emerald-900 px-1.5 py-0.5 rounded text-emerald-800 dark:text-emerald-200">
                  q = {(result.overall_summary.target_reduction_q * 100).toFixed(0)}%
                </span>
              </div>
              <div className="text-3xl font-extrabold text-emerald-700 dark:text-emerald-400 mt-1">
                {(result.overall_summary.robustness_value_q * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">
                Cần giải thích &ge; {(result.overall_summary.robustness_value_q * 100).toFixed(1)}% phương sai ở cả D và Y để triệt tiêu hiệu ứng.
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800">
              <div className="text-xs text-indigo-700 dark:text-indigo-300 font-semibold flex items-center justify-between">
                <span>Significance RV (RV_α)</span>
                <span className="text-[10px] bg-indigo-200 dark:bg-indigo-900 px-1.5 py-0.5 rounded text-indigo-800 dark:text-indigo-200">
                  α = {result.overall_summary.significance_alpha}
                </span>
              </div>
              <div className="text-3xl font-extrabold text-indigo-700 dark:text-indigo-400 mt-1">
                {(result.overall_summary.robustness_value_alpha * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-indigo-600 dark:text-indigo-400 mt-1">
                Cần &ge; {(result.overall_summary.robustness_value_alpha * 100).toFixed(1)}% để làm mất ý nghĩa thống kê (p &gt; 0.05).
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Hiệu ứng Gốc (Baseline τ)</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                {result.overall_summary.baseline_estimate.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 mt-0.5 font-mono">
                t = {result.overall_summary.baseline_t.toFixed(2)} (SE = {result.overall_summary.baseline_se.toFixed(3)})
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Partial R² (Treatment)</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1 font-mono">
                {(result.overall_summary.partial_r2_treatment * 100).toFixed(2)}%
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Cực hạn R²(D~Z): {(result.overall_summary.extreme_r2_dz_needed_to_zero * 100).toFixed(2)}%
              </div>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-inner overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                Bản đồ Đẳng mức Độ nhạy &amp; Các Điểm Đối chuẩn Covariates (Cinelli &amp; Hazlett 2020)
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Benchmark Multiplier Scenarios Table */}
          {result.benchmark_scenarios && result.benchmark_scenarios.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-500" />
                Kiểm thử Sức chịu đựng theo Bội số Biến kiểm soát (Benchmark Multipliers)
              </h4>
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold">
                    <tr>
                      <th className="px-4 py-3">Biến đối chuẩn (Benchmark)</th>
                      <th className="px-3 py-3 text-center">Bội số lực (Mult)</th>
                      <th className="px-3 py-3 text-right">R²(D ~ Z)</th>
                      <th className="px-3 py-3 text-right">R²(Y ~ Z)</th>
                      <th className="px-3 py-3 text-right">Hiệu ứng hiệu chỉnh (τ_adj)</th>
                      <th className="px-3 py-3 text-right">t-stat hiệu chỉnh</th>
                      <th className="px-3 py-3 text-right">95% CI hiệu chỉnh</th>
                      <th className="px-4 py-3 text-center">Kết luận</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900 font-mono">
                    {result.benchmark_scenarios.map((sc, idx) => {
                      const isOverturned = sc.is_overturned;
                      const badgeCls = isOverturned
                        ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border-rose-300 dark:border-rose-800'
                        : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800';

                      return (
                        <tr key={idx} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                          <td className="px-4 py-2.5 font-sans font-medium text-slate-900 dark:text-slate-100">
                            {sc.covariate}
                          </td>
                          <td className="px-3 py-2.5 text-center font-bold text-slate-700 dark:text-slate-300">
                            {sc.multiplier.toFixed(0)}x
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-600 dark:text-slate-400">
                            {(sc.r2_dz_x * 100).toFixed(2)}%
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-600 dark:text-slate-400">
                            {(sc.r2_yz_dx * 100).toFixed(2)}%
                          </td>
                          <td className="px-3 py-2.5 text-right font-bold text-slate-900 dark:text-slate-100">
                            {sc.adjusted_estimate.toFixed(3)}
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-700 dark:text-slate-300 font-semibold">
                            {sc.adjusted_t.toFixed(2)}
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-600 dark:text-slate-400">
                            [{sc.adjusted_ci[0].toFixed(2)}, {sc.adjusted_ci[1].toFixed(2)}]
                          </td>
                          <td className="px-4 py-2.5 text-center font-sans">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${badgeCls}`}>
                              {isOverturned ? 'BỊ ĐẢO NGƯỢC' : 'BỀN VỮNG'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-900 dark:text-emerald-300 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  Báo cáo Thống kê &amp; Trình bày Chuẩn APA 7th
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="text-xs text-emerald-700 dark:text-emerald-300 hover:text-emerald-900 dark:hover:text-emerald-100 flex items-center gap-1 font-medium transition-colors"
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                      Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 italic font-serif">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
