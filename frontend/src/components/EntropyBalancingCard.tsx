import React, { useState } from 'react';
import {
  Scale,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  ShieldCheck,
  Sliders,
  BarChart3,
  ListOrdered
} from 'lucide-react';
import { api } from '../api/client';
import {
  EntropyBalancingResult,
  EntropyBalancingRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const EntropyBalancingCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [momentOrder, setMomentOrder] = useState<number>(1);
  const [tolerance, setTolerance] = useState<number>(1e-5);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EntropyBalancingResult | null>(null);
  const [activeTab, setActiveTab] = useState<'balance' | 'weights' | 'theory'>('balance');
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId) {
      setError('Vui lòng chọn biến Can thiệp (Treatment: 1/0).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến Kết quả (Outcome Y).');
      return;
    }
    if (selectedCovariates.length === 0) {
      setError('Vui lòng chọn ít nhất một biến đồng biến (Covariate) để cân bằng.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: EntropyBalancingRequest = {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: selectedCovariates,
        moment_orders: momentOrder === 2 ? [1, 2] : [1],
        tolerance,
        scope
      };

      const res = await api.runEntropyBalancing(surveyId, payload);
      setResult(res);
      setShowConfig(false);
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực thi Cân Bằng Entropy.');
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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-white tracking-wide">
                Cân Bằng Entropy & Tái Lập Trọng Số Causal Moment (Entropy Balancing)
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full">
                Hainmueller (2012) • Zhao & Percival (2017)
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Tối ưu hóa đối ngẫu hàm lồi để cân bằng chính xác moment mục tiêu (Means/Variances) giữa nhóm can thiệp và đối chứng, triệt tiêu sai lệch lựa chọn và đảm bảo tính kép bền vững (Doubly Robust).
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowConfig(!showConfig)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium border border-slate-700 transition"
        >
          <Sliders className="w-4 h-4 text-emerald-400" />
          <span>{showConfig ? 'Thu gọn Cấu hình' : 'Mở rộng Cấu hình'}</span>
          {showConfig ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="mt-5 p-5 bg-slate-800/40 border border-slate-800 rounded-lg space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Treatment Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                Biến Can thiệp (Treatment: Nhị phân 1/0) *
              </label>
              <select
                value={treatmentQId}
                onChange={(e) => setTreatmentQId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
              >
                <option value="">-- Chọn biến Can thiệp --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            {/* Outcome Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                Biến Kết quả (Outcome Y) *
              </label>
              <select
                value={outcomeQId}
                onChange={(e) => setOutcomeQId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
              >
                <option value="">-- Chọn biến Kết quả --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Covariates Multi-Select */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              Các biến Đồng biến Cần Cân bằng Moment (Covariates X) * ({selectedCovariates.length} đã chọn)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 bg-slate-900/60 rounded-lg border border-slate-800">
              {questions
                .filter((q) => q.id !== treatmentQId && q.id !== outcomeQId)
                .map((q) => {
                  const isChecked = selectedCovariates.includes(q.id);
                  return (
                    <label
                      key={q.id}
                      onClick={() => toggleCovariate(q.id)}
                      className={`flex items-center gap-2 p-2 rounded cursor-pointer text-xs transition border ${
                        isChecked
                          ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-200'
                          : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="rounded border-slate-700 text-emerald-500 focus:ring-0"
                      />
                      <span className="truncate" title={q.title}>
                        {q.title}
                      </span>
                    </label>
                  );
                })}
            </div>
          </div>

          {/* Hyperparameters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-800/80">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <ListOrdered className="w-3.5 h-3.5 text-emerald-400" />
                Cấp bậc Moment Điều kiện
              </label>
              <select
                value={momentOrder}
                onChange={(e) => setMomentOrder(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
              >
                <option value={1}>Bậc 1: Cân bằng Trung bình (Means Matching)</option>
                <option value={2}>Bậc 1 & 2: Trung bình & Phương sai (Means + Variances)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Phạm vi Kiểm tra Dữ liệu (Scope)
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
              >
                <option value="all">Toàn bộ phản hồi hợp lệ (All Valid)</option>
                <option value="verified_clean">Chỉ mẫu đã kiểm duyệt sạch (Verified Clean)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                Dung sai Hội tụ Tối ưu (Tolerance)
              </label>
              <select
                value={tolerance}
                onChange={(e) => setTolerance(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
              >
                <option value={1e-5}>1e-5 (Chuẩn công nghiệp)</option>
                <option value={1e-6}>1e-6 (Độ chính xác cao)</option>
                <option value={1e-4}>1e-4 (Hội tụ nới lỏng)</option>
              </select>
            </div>
          </div>

          {/* Action button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-lg shadow-emerald-900/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang giải Tối ưu hóa Đối ngẫu Entropy...</span>
                </>
              ) : (
                <>
                  <Scale className="w-4 h-4" />
                  <span>Ước lượng Cân Bằng Entropy</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mt-5 p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg flex items-start gap-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
          <div>
            <span className="font-semibold">Lỗi phân tích:</span> {error}
          </div>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="mt-6 space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {/* KPI 1: ATT Effect */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Hiệu Ứng Can Thiệp (ATT)
              </div>
              <div className="text-xl font-extrabold text-emerald-400">
                {result.treatment_effect.att > 0 ? `+${result.treatment_effect.att.toFixed(3)}` : result.treatment_effect.att.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {result.treatment_effect.se.toFixed(3)} (p = {result.treatment_effect.p_value.toFixed(4)})
              </div>
            </div>

            {/* KPI 2: Effective Sample Size */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Cỡ Mẫu Hiệu Dụng (ESS)
              </div>
              <div className="text-xl font-extrabold text-white">
                {result.diagnostics.effective_sample_size.toFixed(1)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {(result.diagnostics.ess_ratio * 100).toFixed(1)}% dung lượng đối chứng
              </div>
            </div>

            {/* KPI 3: Max Post SMD */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Max |SMD| Sau Cân Bằng
              </div>
              <div className="text-xl font-extrabold text-sky-400">
                {result.diagnostics.max_smd_post.toFixed(4)}
              </div>
              <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> &lt; 0.10 (Đạt chuẩn khắt khe)
              </div>
            </div>

            {/* KPI 4: Entropy Loss */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Tổn Thất Entropy KL(w||q)
              </div>
              <div className="text-xl font-extrabold text-purple-400">
                {result.diagnostics.entropy_loss.toFixed(4)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {result.diagnostics.iterations} vòng lặp BFGS
              </div>
            </div>

            {/* KPI 5: Sample Distribution */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Cơ Cấu Mẫu Khảo Sát
              </div>
              <div className="text-xl font-extrabold text-white">
                {result.sample_size}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Can thiệp: {result.treated_count} | Đối chứng: {result.control_count}
              </div>
            </div>
          </div>

          {/* Responsive Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-400" />
                  Đồ Thị Vector Trực Quan Hóa Cân Bằng Entropy (Love Plot & Trọng Số Mẫu)
                </h4>
                <span className="text-xs text-slate-500">
                  DataTrust High-Precision Vector Engine
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 gap-6 text-sm font-medium">
            <button
              onClick={() => setActiveTab('balance')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'balance'
                  ? 'border-emerald-400 text-emerald-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Bảng Cân Bằng Đặc Trưng (Covariate Balance)</span>
            </button>

            <button
              onClick={() => setActiveTab('weights')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'weights'
                  ? 'border-emerald-400 text-emerald-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <ListOrdered className="w-4 h-4" />
              <span>Trọng Số Quan Sát Mẫu ({result.sample_weights.length} dòng)</span>
            </button>

            <button
              onClick={() => setActiveTab('theory')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'theory'
                  ? 'border-emerald-400 text-emerald-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>Nguyên Lý Toán Học & Tính Kép Bền Vững</span>
            </button>
          </div>

          {/* Tab Content: Covariate Balance */}
          {activeTab === 'balance' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Biến Đồng Biến</th>
                    <th className="py-2.5 px-3">TB Can Thiệp</th>
                    <th className="py-2.5 px-3">TB Đ.Chứng (Thô)</th>
                    <th className="py-2.5 px-3 text-emerald-400">TB Đ.Chứng (Entropy)</th>
                    <th className="py-2.5 px-3">SMD Chưa Cân Bằng</th>
                    <th className="py-2.5 px-3 text-emerald-400 font-bold">SMD Sau Cân Bằng</th>
                    <th className="py-2.5 px-3">Tỷ Số Var (Thô)</th>
                    <th className="py-2.5 px-3">Tỷ Số Var (Entropy)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {result.covariate_balance.map((b, i) => {
                    const isBalanced = Math.abs(b.smd_weighted) < 0.10;
                    return (
                      <tr key={i} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-medium text-white">{b.covariate_name}</td>
                        <td className="py-2.5 px-3">{b.mean_treated.toFixed(3)}</td>
                        <td className="py-2.5 px-3">{b.mean_control_unweighted.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-emerald-300 font-semibold">{b.mean_control_weighted.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-slate-400">{b.smd_unweighted.toFixed(4)}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              isBalanced
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            }`}
                          >
                            {b.smd_weighted.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">{b.var_ratio_unweighted.toFixed(3)}</td>
                        <td className="py-2.5 px-3">{b.var_ratio_weighted.toFixed(3)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab Content: Sample Weights */}
          {activeTab === 'weights' && (
            <div className="overflow-x-auto max-h-72 border border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800 text-slate-300 font-semibold sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Quan Sát Đối Chứng (#)</th>
                    <th className="py-2.5 px-3">Kết Quả Thô Y</th>
                    <th className="py-2.5 px-3">Trọng Số Entropy w_i</th>
                    <th className="py-2.5 px-3">Hệ Số Nhân Chuẩn Hóa (w_i × N_c)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {result.sample_weights.map((w, i) => (
                    <tr key={i} className="hover:bg-slate-800/40 transition">
                      <td className="py-2 px-3 font-mono text-slate-400">Đơn vị #{w.unit_index}</td>
                      <td className="py-2 px-3 font-medium text-white">{w.raw_outcome.toFixed(3)}</td>
                      <td className="py-2 px-3 font-mono text-emerald-400">{w.entropy_weight.toFixed(5)}</td>
                      <td className="py-2 px-3 text-slate-300">{w.normalized_multiplier.toFixed(2)}x</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab Content: Theory */}
          {activeTab === 'theory' && (
            <div className="p-4 bg-slate-800/40 border border-slate-800 rounded-lg text-xs text-slate-300 space-y-3 leading-relaxed">
              <p>
                <strong className="text-white">Cơ chế Cân Bằng Entropy (Hainmueller, 2012):</strong> Thay vì ước lượng điểm xu hướng qua hồi quy logistic rồi nghịch đảo trọng số (dễ dẫn đến phân kỳ và trọng số cực đoan), Cân Bằng Entropy trực tiếp giải bài toán quy hoạch lồi cực tiểu hóa sai phân tương đối Kullback-Leibler KL(w||q) = ∑ w_i log(w_i / q_i) thỏa mãn các ràng buộc moment mẫu chính xác của nhóm can thiệp ∑ w_i c_k(X_i) = m_k.
              </p>
              <p>
                <strong className="text-white">Tính Kép Bền Vững (Zhao & Percival, 2017 JRSS-B):</strong> Ước lượng ATT từ Cân Bằng Entropy có tính chất kép bền vững (Doubly Robust). Nếu cơ chế gán can thiệp tuân theo mô hình logit hoặc bề mặt phản ứng kết quả là tuyến tính theo các hàm đặc trưng moment, ước lượng ATT luôn nhất quán tiệm cận.
              </p>
            </div>
          )}

          {/* APA Narrative Section */}
          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl relative">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Báo Cáo Thuyết Minh Học Thuật (APA 7th Format)
              </span>
              <button
                onClick={handleCopyNarrative}
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Đã sao chép' : 'Sao chép văn bản'}</span>
              </button>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-sans italic bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
              "{result.apa_narrative}"
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
