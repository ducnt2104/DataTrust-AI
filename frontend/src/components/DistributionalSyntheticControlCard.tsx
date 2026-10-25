import React, { useState } from 'react';
import {
  Layers,
  Activity,
  TrendingUp,
  BarChart2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import {
  DistributionalSyntheticControlResult,
  DistributionalSyntheticControlRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const DistributionalSyntheticControlCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [unitQId, setUnitQId] = useState<string>('');
  const [periodQId, setPeriodQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatedUnitVal, setTreatedUnitVal] = useState<string>('');
  const [postPeriodsInput, setPostPeriodsInput] = useState<string>('');
  const [numQuantiles, setNumQuantiles] = useState<number>(19);
  const [l2Penalty, setL2Penalty] = useState<number>(0.0001);
  const [numPlacebos, setNumPlacebos] = useState<number>(15);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DistributionalSyntheticControlResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'weights' | 'quantiles' | 'inequality'>('weights');

  const handleRun = async () => {
    if (!unitQId || !periodQId || !outcomeQId || !treatedUnitVal.trim() || !postPeriodsInput.trim()) {
      setError('Vui lòng chọn đầy đủ biến Đơn vị, Thời kỳ, Kết quả, Tên đơn vị can thiệp và Kỳ hậu can thiệp.');
      return;
    }

    setLoading(true);
    setError(null);

    const postPeriods = postPeriodsInput
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const payload: DistributionalSyntheticControlRequest = {
      unit_question_id: unitQId,
      period_question_id: periodQId,
      outcome_question_id: outcomeQId,
      treated_unit_val: treatedUnitVal.trim(),
      post_period_vals: postPeriods,
      num_quantiles: numQuantiles,
      l2_penalty: l2Penalty,
      num_placebos: numPlacebos,
      scope
    };

    try {
      const res = await api.runDistributionalSyntheticControl(surveyId, payload);
      if (res.status === 'success') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể ước lượng Distributional Synthetic Controls.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi endpoint Distributional Synthetic Controls.');
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
          <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">
                Distributional Synthetic Controls &amp; Counterfactual Density Decomposition
              </h3>
              <span className="px-2 py-0.5 text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full font-medium">
                Chernozhukov et al. 2021
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Tổ hợp đối chứng tổng hợp phân vị theo không gian Wasserstein-2, giải mã hiệu ứng phân phối QTE, Gini &amp; Trội ngẫu nhiên FSD.
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Biến Đơn vị khảo sát (Unit ID) <span className="text-rose-400">*</span>
              </label>
              <select
                value={unitQId}
                onChange={(e) => setUnitQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">-- Chọn biến đơn vị / tỉnh / phòng ban --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Tên đơn vị Can thiệp (Treated Unit) <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                placeholder="VD: Province_T hoặc Chi nhánh A"
                value={treatedUnitVal}
                onChange={(e) => setTreatedUnitVal(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Biến Thời kỳ khảo sát (Period) <span className="text-rose-400">*</span>
              </label>
              <select
                value={periodQId}
                onChange={(e) => setPeriodQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">-- Chọn biến chu kỳ / năm / đợt --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Kỳ Hậu can thiệp (Post Periods, phẩy) <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                placeholder="VD: 2023 hoặc 2023, 2024"
                value={postPeriodsInput}
                onChange={(e) => setPostPeriodsInput(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Biến Kết quả đo lường (Outcome Y) <span className="text-rose-400">*</span>
              </label>
              <select
                value={outcomeQId}
                onChange={(e) => setOutcomeQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">-- Chọn biến kết quả định lượng --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Số mốc phân vị (Quantile Grid)
              </label>
              <select
                value={numQuantiles}
                onChange={(e) => setNumQuantiles(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value={9}>9 mốc (p10 - p90, bước 0.10)</option>
                <option value={19}>19 mốc (p05 - p95, bước 0.05)</option>
                <option value={37}>37 mốc (p025 - p975, bước 0.025)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Phạt L2 Simplex (Regularizer λ)
              </label>
              <input
                type="number"
                step="0.0001"
                min="0"
                value={l2Penalty}
                onChange={(e) => setL2Penalty(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Kiểm định Hoán vị Placebo (Permutations)
              </label>
              <select
                value={numPlacebos}
                onChange={(e) => setNumPlacebos(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value={5}>5 permutations</option>
                <option value={15}>15 permutations (Chuẩn)</option>
                <option value={30}>30 permutations (Chính xác cao)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Phạm vi mẫu phân tích (Scope)
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all">Toàn bộ phản hồi (All)</option>
                <option value="verified_clean">Chỉ mẫu sạch xác thực (Verified Clean)</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg transition shadow-md shadow-blue-500/20"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  <span>Đang tối ưu hóa Wasserstein Barycenter...</span>
                </>
              ) : (
                <>
                  <Layers className="w-4 h-4" />
                  <span>Chạy Phân Tích Distributional SCM</span>
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
              <span className="text-xs text-slate-400 font-medium">Hiệu ứng Trung bình &amp; Trung vị (QTE)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-white">
                  {result.mean_treatment_effect !== undefined ? (result.mean_treatment_effect > 0 ? `+${result.mean_treatment_effect}` : result.mean_treatment_effect) : '--'}
                </span>
                <span className="text-xs text-blue-400 font-semibold">
                  (Median: {result.median_treatment_effect !== undefined ? (result.median_treatment_effect > 0 ? `+${result.median_treatment_effect}` : result.median_treatment_effect) : '--'})
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Tác động can thiệp trung bình trên toàn dải phân vị
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Khoảng cách Wasserstein-2 (W2)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-sky-400">
                  {result.wasserstein_distance?.toFixed(4) || '--'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  (result.permutation_p_value ?? 1) <= 0.05
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                }`}>
                  p = {result.permutation_p_value?.toFixed(3) || '--'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Độ lệch phân phối tối ưu theo mô hình Gunsilius (2023)
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Biến thiên Bất bình đẳng (ΔGini)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className={`text-2xl font-bold ${
                  (result.inequality_diagnostics?.delta_gini ?? 0) <= 0 ? 'text-emerald-400' : 'text-amber-400'
                }`}>
                  {result.inequality_diagnostics?.delta_gini !== undefined
                    ? (result.inequality_diagnostics.delta_gini > 0 ? `+${result.inequality_diagnostics.delta_gini}` : result.inequality_diagnostics.delta_gini)
                    : '--'}
                </span>
                <span className="text-xs text-slate-400">
                  (ΔIQR: {result.inequality_diagnostics?.delta_iqr !== undefined ? (result.inequality_diagnostics.delta_iqr > 0 ? `+${result.inequality_diagnostics.delta_iqr}` : result.inequality_diagnostics.delta_iqr) : '--'})
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {(result.inequality_diagnostics?.delta_gini ?? 0) <= 0
                  ? 'Thu hẹp khoảng cách phân phối (Bình đẳng hơn)'
                  : 'Phân hóa và nới rộng phân phối'}
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Trội Ngẫu Nhiên (Stochastic Dominance)</span>
              <div className="mt-1 flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold">
                  <span className="text-slate-400">Bậc 1 (FSD):</span>
                  {result.inequality_diagnostics?.first_order_stochastic_dominance ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Đạt
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5" /> Không đồng nhất
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 text-xs font-semibold">
                  <span className="text-slate-400">Bậc 2 (SSD):</span>
                  {result.inequality_diagnostics?.second_order_stochastic_dominance ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Đạt
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5" /> Chưa thỏa
                    </span>
                  )}
                </div>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Kiểm định phúc lợi kinh tế theo tiêu chuẩn Hadar &amp; Russell
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
                onClick={() => setActiveTab('weights')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'weights'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Trọng số Synthetic Donors ({result.donor_weights?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('quantiles')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'quantiles'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Bảng Phân rã Phân vị QTE ({result.quantile_curve?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('inequality')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'inequality'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Chẩn đoán Bất bình đẳng &amp; Dominance
              </button>
            </div>

            {/* Tab 1: Weights */}
            {activeTab === 'weights' && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Đơn vị Đối chứng (Donor Pool)</th>
                      <th className="py-2.5 px-3 text-right">Trọng số Synthetic (w)</th>
                      <th className="py-2.5 px-3 text-right">Tỷ trọng đóng góp (%)</th>
                      <th className="py-2.5 px-3">Thanh trực quan</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.donor_weights?.map((d, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50 transition">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{d.donor_unit}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-emerald-400">
                          {d.synthetic_weight.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                          {(d.synthetic_weight * 100).toFixed(1)}%
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="w-36 bg-slate-800 h-2 rounded-full overflow-hidden">
                            <div
                              className="bg-emerald-500 h-full rounded-full"
                              style={{ width: `${Math.min(d.synthetic_weight * 100, 100)}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 2: Quantiles */}
            {activeTab === 'quantiles' && (
              <div className="overflow-x-auto max-h-80 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-slate-950">
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Phân vị (τ)</th>
                      <th className="py-2.5 px-3 text-right">Quan sát Can thiệp Q_obs(τ)</th>
                      <th className="py-2.5 px-3 text-right">Đối chứng Tổng hợp Q_syn(τ)</th>
                      <th className="py-2.5 px-3 text-right">Hiệu ứng Phân vị QTE(τ)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.quantile_curve?.map((q, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50 transition">
                        <td className="py-2 px-3 font-mono font-medium text-blue-400">
                          p{Math.round(q.tau * 100).toString().padStart(2, '0')} ({q.tau.toFixed(2)})
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-200">{q.observed_q.toFixed(4)}</td>
                        <td className="py-2 px-3 text-right font-mono text-emerald-400">{q.synthetic_q.toFixed(4)}</td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-sky-300">
                          {q.quantile_treatment_effect > 0 ? `+${q.quantile_treatment_effect.toFixed(4)}` : q.quantile_treatment_effect.toFixed(4)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 3: Inequality */}
            {activeTab === 'inequality' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-2.5">
                  <h4 className="font-semibold text-slate-200 border-b border-slate-800 pb-1.5 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                    Chỉ số Bất bình đẳng Gini
                  </h4>
                  <div className="flex justify-between py-1 border-b border-slate-800/40">
                    <span className="text-slate-400">Gini Quan sát Can thiệp:</span>
                    <span className="font-mono text-slate-200 font-semibold">{result.inequality_diagnostics?.observed_gini.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/40">
                    <span className="text-slate-400">Gini Đối chứng Tổng hợp:</span>
                    <span className="font-mono text-emerald-400 font-semibold">{result.inequality_diagnostics?.synthetic_gini.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Chênh lệch Thay đổi (ΔGini):</span>
                    <span className="font-mono font-bold text-sky-400">
                      {(result.inequality_diagnostics?.delta_gini ?? 0) > 0 ? `+${result.inequality_diagnostics?.delta_gini.toFixed(4)}` : result.inequality_diagnostics?.delta_gini.toFixed(4)}
                    </span>
                  </div>
                </div>

                <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-2.5">
                  <h4 className="font-semibold text-slate-200 border-b border-slate-800 pb-1.5 flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-sky-400" />
                    Độ biến thiên Khoảng Tứ phân vị (IQR = p75 - p25)
                  </h4>
                  <div className="flex justify-between py-1 border-b border-slate-800/40">
                    <span className="text-slate-400">IQR Quan sát Can thiệp:</span>
                    <span className="font-mono text-slate-200 font-semibold">{result.inequality_diagnostics?.observed_iqr.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/40">
                    <span className="text-slate-400">IQR Đối chứng Tổng hợp:</span>
                    <span className="font-mono text-emerald-400 font-semibold">{result.inequality_diagnostics?.synthetic_iqr.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Chênh lệch Thay đổi (ΔIQR):</span>
                    <span className="font-mono font-bold text-sky-400">
                      {(result.inequality_diagnostics?.delta_iqr ?? 0) > 0 ? `+${result.inequality_diagnostics?.delta_iqr.toFixed(4)}` : result.inequality_diagnostics?.delta_iqr.toFixed(4)}
                    </span>
                  </div>
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
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition (Chernozhukov et al. 2021)
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
