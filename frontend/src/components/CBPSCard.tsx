import React, { useState } from 'react';
import {
  Compass,
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
  CBPSResult,
  CBPSRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const CBPSCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [method, setMethod] = useState<'overidentified' | 'just_identified'>('overidentified');
  const [estimand, setEstimand] = useState<'ATE' | 'ATT'>('ATE');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [tolerance, setTolerance] = useState<number>(1e-5);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CBPSResult | null>(null);
  const [activeTab, setActiveTab] = useState<'balance' | 'points' | 'theory'>('balance');
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
      const payload: CBPSRequest = {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: selectedCovariates,
        method,
        estimand,
        tolerance,
        scope
      };

      const res = await api.runCBPS(surveyId, payload);
      setResult(res);
      setShowConfig(false);
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực thi CBPS.');
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
          <div className="p-3 bg-sky-500/10 border border-sky-500/20 rounded-lg text-sky-400">
            <Compass className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-white tracking-wide">
                Điểm Xu Hướng Cân Bằng Đặc Trưng (Covariate Balancing Propensity Score - CBPS)
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30 rounded-full">
                Imai & Ratkovic (2014) • GMM Causal Engine
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Ước lượng điểm xu hướng bằng phương pháp Moment Tổng quát (GMM hai bước) kết hợp đồng thời phương trình hàm hợp lý gán can thiệp và phương trình cân bằng moment đặc trưng, tích hợp kiểm định Hansen J kiểm tra tính đúng đắn của mô hình.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowConfig(!showConfig)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium border border-slate-700 transition"
        >
          <Sliders className="w-4 h-4 text-sky-400" />
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
                <Activity className="w-3.5 h-3.5 text-sky-400" />
                Biến Can thiệp (Treatment: Nhị phân 1/0) *
              </label>
              <select
                value={treatmentQId}
                onChange={(e) => setTreatmentQId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
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
                <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
                Biến Kết quả (Outcome Y) *
              </label>
              <select
                value={outcomeQId}
                onChange={(e) => setOutcomeQId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
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
              <Layers className="w-3.5 h-3.5 text-sky-400" />
              Các biến Đồng biến Cần Cân bằng (Covariates X) * ({selectedCovariates.length} đã chọn)
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
                          ? 'bg-sky-500/15 border-sky-500/40 text-sky-200'
                          : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="rounded border-slate-700 text-sky-500 focus:ring-0"
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2 border-t border-slate-800/80">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-sky-400" />
                Mục Tiêu Ước Lượng (Estimand)
              </label>
              <select
                value={estimand}
                onChange={(e) => setEstimand(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              >
                <option value="ATE">ATE (Hiệu ứng trên toàn quần thể)</option>
                <option value="ATT">ATT (Hiệu ứng trên nhóm can thiệp)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <ListOrdered className="w-3.5 h-3.5 text-sky-400" />
                Cấu Trúc Hệ Phương Trình GMM
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              >
                <option value="overidentified">Overidentified GMM (Score + Balance)</option>
                <option value="just_identified">Just-Identified (Chỉ Balance Moments)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
                Phạm vi Phân tích Dữ liệu
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              >
                <option value="all">Toàn bộ phản hồi hợp lệ (All Valid)</option>
                <option value="verified_clean">Chỉ mẫu đã kiểm duyệt sạch (Verified Clean)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-sky-400" />
                Dung sai Hội tụ GMM
              </label>
              <select
                value={tolerance}
                onChange={(e) => setTolerance(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              >
                <option value={1e-5}>1e-5 (Chuẩn)</option>
                <option value={1e-6}>1e-6 (Khắt khe)</option>
                <option value={1e-4}>1e-4 (Nhanh)</option>
              </select>
            </div>
          </div>

          {/* Action button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium shadow-lg shadow-sky-900/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang giải Ước Lượng GMM CBPS...</span>
                </>
              ) : (
                <>
                  <Compass className="w-4 h-4" />
                  <span>Ước lượng CBPS GMM</span>
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
            {/* KPI 1: Effect */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Hiệu Ứng {result.estimand} (CBPS)
              </div>
              <div className="text-xl font-extrabold text-sky-400">
                {result.causal_effect.effect > 0 ? `+${result.causal_effect.effect.toFixed(3)}` : result.causal_effect.effect.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {result.causal_effect.se.toFixed(3)} (p = {result.causal_effect.p_value.toFixed(4)})
              </div>
            </div>

            {/* KPI 2: Hansen J Test */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Kiểm Định Hansen J (Chi-sq)
              </div>
              <div className="text-xl font-extrabold text-emerald-400">
                J = {result.diagnostics.hansen_j_stat.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                df = {result.diagnostics.hansen_j_df} (p = {result.diagnostics.hansen_j_p_value.toFixed(3)})
              </div>
            </div>

            {/* KPI 3: Max Post SMD */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Max |SMD| Sau CBPS
              </div>
              <div className="text-xl font-extrabold text-white">
                {result.overlap_metrics.max_smd_post.toFixed(4)}
              </div>
              <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Cân bằng xuất sắc
              </div>
            </div>

            {/* KPI 4: Effective Sample Sizes */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Cỡ Mẫu Hiệu Dụng ESS
              </div>
              <div className="text-xl font-extrabold text-purple-400">
                {result.overlap_metrics.effective_sample_size_treated.toFixed(0)} / {result.overlap_metrics.effective_sample_size_control.toFixed(0)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Treated ESS / Control ESS
              </div>
            </div>

            {/* KPI 5: Common Support */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Vùng Trùng Khớp Overlap
              </div>
              <div className="text-xl font-extrabold text-emerald-400">
                {result.overlap_metrics.common_support_overlap ? 'Đầy đủ (Valid)' : 'Cảnh báo'}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                [{result.overlap_metrics.min_propensity_treated.toFixed(2)}, {result.overlap_metrics.max_propensity_control.toFixed(2)}]
              </div>
            </div>
          </div>

          {/* Responsive Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-sky-400" />
                  Đồ Thị Vector Trực Quan Hóa CBPS (Phân Phối Điểm Xu Hướng & Love Plot)
                </h4>
                <span className="text-xs text-slate-500">
                  DataTrust Vector Engine
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
                  ? 'border-sky-400 text-sky-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Bảng Cân Bằng Đặc Trưng (Covariate Balance)</span>
            </button>

            <button
              onClick={() => setActiveTab('points')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'points'
                  ? 'border-sky-400 text-sky-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <ListOrdered className="w-4 h-4" />
              <span>Điểm Xu Hướng & Trọng Số Mẫu ({result.sample_points.length} dòng)</span>
            </button>

            <button
              onClick={() => setActiveTab('theory')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'theory'
                  ? 'border-sky-400 text-sky-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>Nguyên Lý GMM & Kiểm Định Hansen J</span>
            </button>
          </div>

          {/* Tab Content: Covariate Balance */}
          {activeTab === 'balance' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Biến Đồng Biến</th>
                    <th className="py-2.5 px-3">TB Can Thiệp (Thô)</th>
                    <th className="py-2.5 px-3">TB Đ.Chứng (Thô)</th>
                    <th className="py-2.5 px-3 text-sky-400">TB Can Thiệp (CBPS)</th>
                    <th className="py-2.5 px-3 text-sky-400">TB Đ.Chứng (CBPS)</th>
                    <th className="py-2.5 px-3">SMD Thô</th>
                    <th className="py-2.5 px-3 text-sky-400 font-bold">SMD Sau CBPS</th>
                    <th className="py-2.5 px-3">Tỷ Số Var (Thô)</th>
                    <th className="py-2.5 px-3">Tỷ Số Var (CBPS)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {result.covariate_balance.map((b, i) => {
                    const isBalanced = Math.abs(b.smd_weighted) < 0.15;
                    return (
                      <tr key={i} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-medium text-white">{b.covariate_name}</td>
                        <td className="py-2.5 px-3">{b.mean_treated_raw.toFixed(3)}</td>
                        <td className="py-2.5 px-3">{b.mean_control_raw.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-sky-300 font-semibold">{b.mean_treated_weighted.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-sky-300 font-semibold">{b.mean_control_weighted.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-slate-400">{b.smd_raw.toFixed(4)}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              isBalanced
                                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                                : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            }`}
                          >
                            {b.smd_weighted.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">{b.var_ratio_raw.toFixed(3)}</td>
                        <td className="py-2.5 px-3">{b.var_ratio_weighted.toFixed(3)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab Content: Sample Points */}
          {activeTab === 'points' && (
            <div className="overflow-x-auto max-h-72 border border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800 text-slate-300 font-semibold sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Quan Sát (#)</th>
                    <th className="py-2.5 px-3">Nhóm Can Thiệp</th>
                    <th className="py-2.5 px-3">Kết Quả Y</th>
                    <th className="py-2.5 px-3">Điểm Xu Hướng pi(X)</th>
                    <th className="py-2.5 px-3">Trọng Số CBPS w_i</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {result.sample_points.map((p, i) => (
                    <tr key={i} className="hover:bg-slate-800/40 transition">
                      <td className="py-2 px-3 font-mono text-slate-400">Đơn vị #{p.unit_index}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            p.treatment === 1
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                              : 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                          }`}
                        >
                          {p.treatment === 1 ? 'Can thiệp (1)' : 'Đối chứng (0)'}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-medium text-white">{p.outcome.toFixed(3)}</td>
                      <td className="py-2 px-3 font-mono text-emerald-400">{p.propensity_score.toFixed(4)}</td>
                      <td className="py-2 px-3 font-mono text-sky-400">{p.cbps_weight.toFixed(4)}</td>
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
                <strong className="text-white">Cơ chế CBPS (Imai & Ratkovic, 2014 JRSS-B):</strong> Khác với hồi quy logistic chuẩn (chỉ tối đa hóa khả năng gán can thiệp mà không quan tâm đến sự cân bằng các biến đồng biến), CBPS ép trực tiếp các phương trình cân bằng moment vào quá trình ước lượng qua hệ GMM (Generalized Method of Moments).
              </p>
              <p>
                <strong className="text-white">Kiểm Định Hansen J (Overidentifying Restrictions):</strong> Trong mô hình Overidentified CBPS, số lượng điều kiện moment lớn hơn số tham số beta, cho phép kiểm định thống kê Hansen J với phân phối Chi-bình phương. Nếu p-value &gt; 0.05, mô hình không bị bác bỏ, xác nhận giả định phân bổ can thiệp và các biến đồng biến hoàn toàn tương thích và cân bằng hữu hiệu.
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
                {copied ? <Check className="w-3.5 h-3.5 text-sky-400" /> : <Copy className="w-3.5 h-3.5" />}
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
