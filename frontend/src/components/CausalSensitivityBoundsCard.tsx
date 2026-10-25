import React, { useState } from 'react';
import {
  ShieldAlert,
  Sliders,
  Target,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Activity,
  Layers,
  Award
} from 'lucide-react';
import { api } from '../api/client';
import {
  CausalSensitivityBoundsResult,
  CausalSensitivityBoundsRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const CausalSensitivityBoundsCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalSensitivityBoundsResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'benchmarks' | 'worstcase' | 'guidelines'>('benchmarks');

  const handleToggleCovariate = (qid: string) => {
    setCovariateQIds((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!treatmentQId || !outcomeQId) {
      setError('Vui lòng chọn biến Can thiệp (Treatment D) và biến Kết quả (Outcome Y).');
      return;
    }
    if (covariateQIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến kiểm soát (Covariates) để làm chuẩn đối sánh (benchmarking).');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: CausalSensitivityBoundsRequest = {
      treatment_question_id: treatmentQId,
      outcome_question_id: outcomeQId,
      covariate_question_ids: covariateQIds,
      alpha_level: alphaLevel,
      scope
    };

    try {
      const res = await api.runCausalSensitivityBounds(surveyId, payload);
      if (res.status === 'success') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể tính toán Causal Sensitivity Bounds.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi endpoint Causal Sensitivity Bounds.');
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">
                Causal Sensitivity Bounds &amp; Unmeasured Confounding Tolerance
              </h3>
              <span className="px-2 py-0.5 text-xs bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-full font-medium">
                Cinelli &amp; Hazlett 2020 JRSS-B
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Định lượng ngưỡng chịu đựng nhiễu loạn ẩn (Robustness Value RV), đối chuẩn biến quan sát và biên phụ thuộc đuôi Copula.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowConfig(!showConfig)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition"
        >
          {showConfig ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          <span>{showConfig ? 'Thu gọn thiết lập' : 'Mở cấu hình'}</span>
        </button>
      </div>

      {/* Configuration Section */}
      {showConfig && (
        <div className="mt-5 p-4 bg-slate-950/70 border border-slate-800/80 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Biến Can thiệp / Chính sách (Treatment D) <span className="text-rose-400">*</span>
              </label>
              <select
                value={treatmentQId}
                onChange={(e) => setTreatmentQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-rose-500"
              >
                <option value="">-- Chọn biến can thiệp (0/1 hoặc liên tục) --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Biến Kết quả đo lường (Outcome Y) <span className="text-rose-400">*</span>
              </label>
              <select
                value={outcomeQId}
                onChange={(e) => setOutcomeQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-rose-500"
              >
                <option value="">-- Chọn biến kết quả định lượng --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Các biến kiểm soát quan sát (Observed Covariates for Benchmarking) <span className="text-rose-400">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto p-2 bg-slate-900 border border-slate-800 rounded-lg">
              {questions
                .filter((q) => q.id !== treatmentQId && q.id !== outcomeQId)
                .map((q) => {
                  const isChecked = covariateQIds.includes(q.id);
                  return (
                    <label
                      key={q.id}
                      onClick={() => handleToggleCovariate(q.id)}
                      className={`flex items-center gap-2 p-2 rounded cursor-pointer text-xs transition ${
                        isChecked
                          ? 'bg-rose-500/15 border border-rose-500/40 text-white font-medium'
                          : 'hover:bg-slate-800 text-slate-300 border border-transparent'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="rounded border-slate-700 text-rose-500 focus:ring-0"
                      />
                      <span className="truncate">{q.title}</span>
                    </label>
                  );
                })}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Đã chọn: {covariateQIds.length} biến kiểm soát làm chuẩn đối sánh sức mạnh của biến ẩn chưa quan sát.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Mức ý nghĩa thống kê (Significance Level α)
              </label>
              <select
                value={alphaLevel}
                onChange={(e) => setAlphaLevel(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-rose-500"
              >
                <option value={0.01}>α = 0.01 (Độ tin cậy 99%)</option>
                <option value={0.05}>α = 0.05 (Độ tin cậy 95% - Chuẩn học thuật)</option>
                <option value={0.10}>α = 0.10 (Độ tin cậy 90%)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Phạm vi tập mẫu phân tích (Scope)
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-rose-500"
              >
                <option value="all">Toàn bộ dữ liệu phản hồi (All)</option>
                <option value="verified_clean">Chỉ tập mẫu sạch đã xác thực (Verified Clean)</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 disabled:opacity-50 rounded-lg transition shadow-md shadow-rose-500/20"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  <span>Đang tính toán Robustness Values &amp; Bounding...</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-4 h-4" />
                  <span>Chạy Kiểm Định Độ Nhạy Nhân Quả (Cinelli-Hazlett)</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg flex items-center gap-2.5 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="mt-6 space-y-6">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Hiệu ứng Cơ sở OLS (Baseline τ)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-white">
                  {result.baseline_estimates?.tau_hat !== undefined
                    ? (result.baseline_estimates.tau_hat > 0 ? `+${result.baseline_estimates.tau_hat.toFixed(4)}` : result.baseline_estimates.tau_hat.toFixed(4))
                    : '--'}
                </span>
                <span className="text-xs text-slate-400">
                  (SE: {result.baseline_estimates?.se_hat?.toFixed(4) || '--'})
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                t({result.degrees_of_freedom}) = {result.baseline_estimates?.t_statistic.toFixed(2)}, p = {result.baseline_estimates?.p_value.toFixed(4)}
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Độ vững Triệt tiêu (RV to Zero)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-rose-400">
                  {result.robustness_values?.rv_q_to_zero !== undefined
                    ? `${(result.robustness_values.rv_q_to_zero * 100).toFixed(1)}%`
                    : '--'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  result.robustness_values?.robustness_tier === 'HIGHLY_ROBUST'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : result.robustness_values?.robustness_tier === 'MODERATELY_ROBUST'
                    ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                }`}>
                  {result.robustness_values?.robustness_tier || '--'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Sức mạnh tối thiểu của biến ẩn U để kéo hiệu ứng về 0
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Độ vững Ý nghĩa (RV at α=0.05)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-amber-400">
                  {result.robustness_values?.rv_alpha_significance !== undefined
                    ? `${(result.robustness_values.rv_alpha_significance * 100).toFixed(1)}%`
                    : '--'}
                </span>
                <span className="text-xs text-slate-400">
                  (R²_Y~D = {(result.baseline_estimates?.partial_r2_treatment ?? 0 * 100).toFixed(1)}%)
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Sức mạnh biến ẩn để làm mất ý nghĩa thống kê (CI chạm 0)
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Biên Phụ thuộc Đuôi Copula</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-sky-400">
                  τ_k = {result.copula_tail_bounds?.kendall_tau.toFixed(3) || '0.000'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Clayton λ_L = {result.copula_tail_bounds?.clayton_lower_tail.toFixed(3)} | Gumbel λ_U = {result.copula_tail_bounds?.gumbel_upper_tail.toFixed(3)}
              </p>
            </div>
          </div>

          {/* Dual-Panel SVG Visualizer */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-inner">
              <div
                className="w-full flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Detailed Tabs */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-3 mb-4">
              <button
                onClick={() => setActiveTab('benchmarks')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'benchmarks'
                    ? 'bg-rose-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Đối chuẩn Biến kiểm soát ({result.covariate_benchmarks?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('worstcase')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'worstcase'
                    ? 'bg-rose-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Đường cong Kịch bản Tệ nhất (Worst-Case)
              </button>
              <button
                onClick={() => setActiveTab('guidelines')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'guidelines'
                    ? 'bg-rose-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Quy tắc Luận giải Học thuật
              </button>
            </div>

            {/* Tab 1: Benchmarks */}
            {activeTab === 'benchmarks' && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Tên Biến Kiểm Soát Đối Chuẩn</th>
                      <th className="py-2.5 px-3 text-right">{'R²(D ~ X | X_{-j})'}</th>
                      <th className="py-2.5 px-3 text-right">{'R²(Y ~ X | D, X_{-j})'}</th>
                      <th className="py-2.5 px-3 text-right">Tác động Độ chệch (1x Bias)</th>
                      <th className="py-2.5 px-3 text-right">Hiệu ứng Điều chỉnh (τ*)</th>
                      <th className="py-2.5 px-3 text-center">Bảo toàn Ý nghĩa?</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.covariate_benchmarks?.map((bm, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50 transition">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{bm.name}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-amber-400">
                          {(bm.r2_d * 100).toFixed(2)}%
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-sky-400">
                          {(bm.r2_y * 100).toFixed(2)}%
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-rose-300">
                          {bm.bias_impact_1x.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-white">
                          {bm.adjusted_tau_1x > 0 ? `+${bm.adjusted_tau_1x.toFixed(4)}` : bm.adjusted_tau_1x.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {bm.retains_significance ? (
                            <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Có (Vững)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-amber-400 font-semibold">
                              <AlertCircle className="w-3.5 h-3.5" /> Bị triệt tiêu
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 2: Worst Case Curve */}
            {activeTab === 'worstcase' && (
              <div className="overflow-x-auto max-h-80 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-slate-950">
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Cường độ Biến nhiễu ẩn (R² = R²_D = R²_Y)</th>
                      <th className="py-2.5 px-3 text-right">Độ chệch tiềm tàng (Bias)</th>
                      <th className="py-2.5 px-3 text-right">Hiệu ứng can thiệp sau điều chỉnh (τ*)</th>
                      <th className="py-2.5 px-3 text-center">Trạng thái kết luận</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.worst_case_curve?.map((wc, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50 transition">
                        <td className="py-2 px-3 font-mono text-slate-300">
                          {(wc.r2_strength * 100).toFixed(1)}% ({wc.r2_strength.toFixed(3)})
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-rose-400">
                          {wc.bias.toFixed(4)}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-sky-300">
                          {wc.adjusted_tau > 0 ? `+${wc.adjusted_tau.toFixed(4)}` : wc.adjusted_tau.toFixed(4)}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {wc.adjusted_tau > 0 ? (
                            <span className="text-emerald-400 font-medium">Dương tính</span>
                          ) : (
                            <span className="text-rose-400 font-bold">Bị đảo ngược / Triệt tiêu</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 3: Guidelines */}
            {activeTab === 'guidelines' && (
              <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <h4 className="font-semibold text-white mb-1 flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-emerald-400" />
                    Tiêu chuẩn Đánh giá Độ vững Vàng (Cinelli &amp; Hazlett 2020)
                  </h4>
                  <p>
                    <strong>RV &ge; 25%:</strong> Cực kỳ vững vàng (Highly Robust). Cần một biến tiềm ẩn cực mạnh chưa từng ghi nhận mới có thể làm thay đổi kết luận nghiên cứu.
                  </p>
                  <p className="mt-1">
                    <strong>10% &le; RV &lt; 25%:</strong> Độ vững trung bình (Moderately Robust). Nghiên cứu an toàn trước các yếu tố nhiễu thông thường nhưng cần biện luận cẩn trọng.
                  </p>
                  <p className="mt-1">
                    <strong>RV &lt; 10%:</strong> Nhạy cảm cao (Fragile). Cần bổ sung các biến kiểm soát chất lượng cao hoặc công cụ ngoại sinh để củng cố suy luận nhân quả.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-950/90 border border-slate-800 rounded-xl relative">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition (Cinelli &amp; Hazlett 2020)
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded transition"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed italic">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
