import React, { useState } from 'react';
import {
  RefreshCw,
  Cpu,
  Layers,
  Sliders,
  Copy,
  Check,
  Download,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  Percent,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  BarChart3
} from 'lucide-react';
import { api } from '../api/client';
import type {
  DynamicDiscreteChoiceRequest,
  DynamicDiscreteChoiceResult
} from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface DynamicDiscreteChoiceCardProps {
  surveyId: string;
  questions: QuestionOption[];
}

export const DynamicDiscreteChoiceCard: React.FC<DynamicDiscreteChoiceCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'likert'].includes(q.question_type)
  );
  const binaryOrChoiceQuestions = questions.filter((q) =>
    ['single_choice', 'boolean', 'rating', 'scale', 'number'].includes(q.question_type)
  );

  const [stateQId, setStateQId] = useState<string>(
    numericQuestions[0]?.id || ''
  );
  const [decisionQId, setDecisionQId] = useState<string>(
    binaryOrChoiceQuestions[1]?.id || binaryOrChoiceQuestions[0]?.id || ''
  );
  const [discountFactor, setDiscountFactor] = useState<number>(0.999);
  const [numStates, setNumStates] = useState<number>(20);
  const [subsidyPct, setSubsidyPct] = useState<number>(20);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DynamicDiscreteChoiceResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const handleRunAnalysis = async () => {
    if (!stateQId || !decisionQId) {
      setError('Vui lòng chọn biến trạng thái (State Variable) và biến quyết định (Binary Decision).');
      return;
    }
    if (stateQId === decisionQId) {
      setError('Biến trạng thái và biến quyết định không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: DynamicDiscreteChoiceRequest = {
        state_question_id: stateQId,
        decision_question_id: decisionQId,
        discount_factor: discountFactor,
        num_discretized_states: numStates,
        counterfactual_subsidy_pct: subsidyPct,
        alpha_level: alphaLevel,
        scope
      };

      const res = await api.runDynamicDiscreteChoice(surveyId, payload);
      setResult(res);
    } catch (err: any) {
      console.error('Error running Dynamic Discrete Choice analysis:', err);
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Không thể thực hiện ước lượng Dynamic Discrete Choice NFXP. Vui lòng kiểm tra lại cấu hình dữ liệu.'
      );
    } finally {
      setLoading(false);
    }
  };

  const copyNarrativeToClipboard = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  const downloadNarrative = () => {
    if (!result?.apa_narrative) return;
    const blob = new Blob([result.apa_narrative], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DataTrust_Dynamic_Discrete_Choice_NFXP_${surveyId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getPValueBadge = (pval?: number) => {
    if (pval === undefined || pval === null) return null;
    if (pval < 0.001) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
          p &lt; .001 ***
        </span>
      );
    }
    if (pval < 0.01) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
          p = {pval.toFixed(3)} **
        </span>
      );
    }
    if (pval < 0.05) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
          p = {pval.toFixed(3)} *
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
        p = {pval.toFixed(3)} (n.s.)
      </span>
    );
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 mb-8 transition-colors">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-200 dark:border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Dynamic Discrete Choice Structural Dynamic Programming Engine (NFXP)
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-100 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300">
                DataTrust Structural Rust 1987
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Ước lượng tham số cấu trúc hàm giá trị Bellman lồng nhau (Nested Fixed Point MLE) &amp; mô phỏng chính sách trợ cấp thay thế ngược thực tế
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Đang giải Bellman Fixed Point...' : 'Chạy Mô Hình DDC NFXP'}
          </button>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
        {/* State Variable */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến trạng thái (State Variable s) <span className="text-rose-500">*</span>
          </label>
          <select
            value={stateQId}
            onChange={(e) => setStateQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-indigo-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Số km, tuổi thọ, mức độ hao mòn, hoặc thâm niên
          </p>
        </div>

        {/* Binary Decision */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến quyết định (Decision d ∈ &#123;0, 1&#125;) <span className="text-rose-500">*</span>
          </label>
          <select
            value={decisionQId}
            onChange={(e) => setDecisionQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-indigo-500"
          >
            {binaryOrChoiceQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            0: Duy trì/sử dụng tiếp; 1: Thay thế/mua mới/đổi
          </p>
        </div>

        {/* Discount Factor beta */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Hệ số chiết khấu (Discount Factor β)
          </label>
          <select
            value={discountFactor}
            onChange={(e) => setDiscountFactor(parseFloat(e.target.value))}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-indigo-500"
          >
            <option value="0.999">β = 0.999 (Chuẩn Rust 1987 bus)</option>
            <option value="0.990">β = 0.990 (Hàng tháng / trung hạn)</option>
            <option value="0.950">β = 0.950 (Hàng năm / 5% lãi suất)</option>
            <option value="0.900">β = 0.900 (Chiết khấu cao 10%)</option>
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Tỷ lệ chiết khấu kỳ vọng dòng hữu dụng tương lai
          </p>
        </div>

        {/* Counterfactual Subsidy % */}
        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
              Trợ cấp thay thế ngược thực tế (%)
            </label>
            <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
              {subsidyPct}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="50"
            step="5"
            value={subsidyPct}
            onChange={(e) => setSubsidyPct(parseInt(e.target.value, 10))}
            className="w-full accent-indigo-600 cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            <span>0% (Hiện trạng)</span>
            <span>25%</span>
            <span>50% (Tối đa)</span>
          </div>
        </div>
      </div>

      {/* Secondary Controls (Discretization & Scope) */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700/60 mb-6 text-sm">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
              Số khoảng rời rạc hóa trạng thái (Bins S):
            </span>
            <select
              value={numStates}
              onChange={(e) => setNumStates(parseInt(e.target.value, 10))}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="10">10 Bins (Thô / Nhanh)</option>
              <option value="20">20 Bins (Chuẩn cân đối)</option>
              <option value="30">30 Bins (Độ mịn cao)</option>
              <option value="50">50 Bins (Rất chi tiết)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Mức ý nghĩa α:</span>
            <select
              value={alphaLevel}
              onChange={(e) => setAlphaLevel(parseFloat(e.target.value))}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="0.05">α = 0.05 (CI 95%)</option>
              <option value="0.01">α = 0.01 (CI 99%)</option>
              <option value="0.10">α = 0.10 (CI 90%)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Phạm vi mẫu:</span>
          <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-white dark:bg-slate-800">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                scope === 'all'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
              }`}
            >
              Tất cả phản hồi
            </button>
            <button
              type="button"
              onClick={() => setScope('verified_clean')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                scope === 'verified_clean'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
              }`}
            >
              <ShieldCheck className="w-3 h-3 inline mr-1" />
              Đã làm sạch
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-start gap-3 p-4 mb-6 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Lỗi ước lượng cấu trúc DDC NFXP</p>
            <p className="mt-0.5 text-xs text-rose-700 dark:text-rose-400">{error}</p>
          </div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6">
          {/* 4 KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Replacement Cost RC */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Chi phí thay thế (RC / θ₀)</span>
                {getPValueBadge(result.structural_parameters?.replacement_cost_rc?.p_value)}
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {(result.structural_parameters?.replacement_cost_rc?.estimate ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                SE: ±{(result.structural_parameters?.replacement_cost_rc?.se ?? 0).toFixed(3)} | 95% CI: [
                {(result.structural_parameters?.replacement_cost_rc?.ci_95?.[0] ?? 0).toFixed(2)},{' '}
                {(result.structural_parameters?.replacement_cost_rc?.ci_95?.[1] ?? 0).toFixed(2)}]
              </div>
            </div>

            {/* KPI 2: Operating Cost Slope theta_1 */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Chi phí vận hành tuyến tính (θ₁)</span>
                {getPValueBadge(result.structural_parameters?.linear_operating_cost_th1?.p_value)}
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {(result.structural_parameters?.linear_operating_cost_th1?.estimate ?? 0).toFixed(4)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                SE: ±{(result.structural_parameters?.linear_operating_cost_th1?.se ?? 0).toFixed(4)} | 95% CI: [
                {(result.structural_parameters?.linear_operating_cost_th1?.ci_95?.[0] ?? 0).toFixed(3)},{' '}
                {(result.structural_parameters?.linear_operating_cost_th1?.ci_95?.[1] ?? 0).toFixed(3)}]
              </div>
            </div>

            {/* KPI 3: Baseline Cutoff State */}
            <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-indigo-700 dark:text-indigo-300 mb-1">
                <span>Ngưỡng cân bằng hiện trạng (s*)</span>
                <span className="font-semibold">P(Replace) &ge; 50%</span>
              </div>
              <div className="text-2xl font-black text-indigo-900 dark:text-indigo-200">
                {(result.equilibrium_thresholds?.baseline_threshold_state ?? 0).toFixed(2)}
              </div>
              <div className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
                Tần suất thay thế cân bằng: {(result.equilibrium_thresholds?.baseline_stationary_rate_pct ?? 0).toFixed(2)}%
              </div>
            </div>

            {/* KPI 4: Counterfactual Policy Cutoff & Delta */}
            <div className="p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-emerald-700 dark:text-emerald-300 mb-1">
                <span>Ngưỡng trợ cấp ({subsidyPct}% Subsidy s*cf)</span>
                <span className="font-semibold">
                  {(result.equilibrium_thresholds?.rate_delta_pct ?? 0) >= 0 ? '+' : ''}
                  {(result.equilibrium_thresholds?.rate_delta_pct ?? 0).toFixed(2)}%
                </span>
              </div>
              <div className="text-2xl font-black text-emerald-900 dark:text-emerald-200">
                {(result.equilibrium_thresholds?.counterfactual_threshold_state ?? 0).toFixed(2)}
              </div>
              <div className="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                Tần suất sau trợ cấp: {(result.equilibrium_thresholds?.counterfactual_stationary_rate_pct ?? 0).toFixed(2)}%
              </div>
            </div>
          </div>

          {/* SVG Visualizer Panel */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    Hàm giá trị Bellman V(s) &amp; Xác suất thay thế cân bằng P(d=1|s)
                  </h4>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-indigo-600 rounded"></span>
                    <span className="text-slate-600 dark:text-slate-400">Baseline (Hiện trạng)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-emerald-500 rounded border-dashed border-b border-emerald-500"></span>
                    <span className="text-slate-600 dark:text-slate-400">Trợ cấp {subsidyPct}% RC</span>
                  </div>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* State Profiles Table */}
          {result.state_profiles && result.state_profiles.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Hồ sơ trạng thái rời rạc &amp; Phân phối dừng Markov (Stationary Distribution)
                </h4>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {result.state_profiles.length} khoảng trạng thái
                </span>
              </div>
              <div className="overflow-x-auto max-h-64">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-100/70 dark:bg-slate-800 text-slate-700 dark:text-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Bin</th>
                      <th className="py-2.5 px-3 font-semibold">Giá trị trạng thái (s)</th>
                      <th className="py-2.5 px-3 font-semibold">EV(Duy trì d=0)</th>
                      <th className="py-2.5 px-3 font-semibold">EV(Thay thế d=1)</th>
                      <th className="py-2.5 px-3 font-semibold">P(Replace | Baseline)</th>
                      <th className="py-2.5 px-3 font-semibold">P(Replace | Trợ cấp)</th>
                      <th className="py-2.5 px-3 font-semibold">Mật độ dừng π(s)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
                    {result.state_profiles.map((p) => (
                      <tr key={p.state_bin} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                          #{p.state_bin}
                        </td>
                        <td className="py-2 px-3">{p.state_value.toFixed(2)}</td>
                        <td className="py-2 px-3">{p.expected_value_maintain.toFixed(2)}</td>
                        <td className="py-2 px-3">{p.expected_value_replace.toFixed(2)}</td>
                        <td className="py-2 px-3 font-semibold text-indigo-600 dark:text-indigo-400">
                          {(p.choice_prob_baseline * 100).toFixed(1)}%
                        </td>
                        <td className="py-2 px-3 font-semibold text-emerald-600 dark:text-emerald-400">
                          {(p.choice_prob_counterfactual * 100).toFixed(1)}%
                        </td>
                        <td className="py-2 px-3">{p.stationary_density_pct.toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA Scientific Narrative Box */}
          {result.apa_narrative && (
            <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    Báo cáo khoa học chuẩn APA 7th &amp; Kinh tế lượng cấu trúc
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={copyNarrativeToClipboard}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition-colors"
                  >
                    {copiedNarrative ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedNarrative ? 'Đã sao chép' : 'Sao chép APA'}
                  </button>
                  <button
                    onClick={downloadNarrative}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Tải Markdown
                  </button>
                </div>
              </div>
              <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans whitespace-pre-wrap bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
