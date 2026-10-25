import React, { useState } from 'react';
import {
  Grid,
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
  Table
} from 'lucide-react';
import { api } from '../api/client';
import {
  CausalMatrixCompletionResult,
  CausalMatrixCompletionRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const CausalMatrixCompletionCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [unitQId, setUnitQId] = useState<string>('');
  const [periodQId, setPeriodQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [lambdaNuc, setLambdaNuc] = useState<number>(0.2);
  const [maxIter, setMaxIter] = useState<number>(150);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalMatrixCompletionResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'heterogeneity' | 'eventstudy' | 'diagnostics'>('heterogeneity');

  const handleRun = async () => {
    if (!unitQId || !periodQId || !outcomeQId || !treatmentQId) {
      setError('Vui lòng chọn đầy đủ biến Đơn vị, Thời kỳ, Kết quả và Biến chỉ báo can thiệp.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: CausalMatrixCompletionRequest = {
      unit_question_id: unitQId,
      period_question_id: periodQId,
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      lambda_nuc: lambdaNuc,
      max_iter: maxIter,
      tol: 1e-4,
      scope
    };

    try {
      const res = await api.runCausalMatrixCompletion(surveyId, payload);
      if (res.status === 'success') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể ước lượng Causal Matrix Completion.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi endpoint Causal Matrix Completion.');
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
          <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <Grid className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">
                Causal Matrix Completion &amp; Nuclear Norm Regularization
              </h3>
              <span className="px-2 py-0.5 text-xs bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 rounded-full font-medium">
                Athey et al. 2021 JASA
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Hoàn thiện ma trận tiềm ẩn bằng chuẩn hạt nhân (Nuclear Norm SVT), xử lý tiếp nhận can thiệp so le (Staggered Adoption) và yếu tố cố định tương tác.
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
                Biến Đơn vị khảo sát (Unit ID) <span className="text-rose-400">*</span>
              </label>
              <select
                value={unitQId}
                onChange={(e) => setUnitQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">-- Chọn biến đơn vị / chi nhánh / tỉnh --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Biến Thời kỳ khảo sát (Period T) <span className="text-rose-400">*</span>
              </label>
              <select
                value={periodQId}
                onChange={(e) => setPeriodQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">-- Chọn biến thời kỳ / năm / đợt --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Biến Kết quả đo lường (Outcome Y) <span className="text-rose-400">*</span>
              </label>
              <select
                value={outcomeQId}
                onChange={(e) => setOutcomeQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
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
                Biến Chỉ báo Can thiệp (Treatment W) <span className="text-rose-400">*</span>
              </label>
              <select
                value={treatmentQId}
                onChange={(e) => setTreatmentQId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">-- Chọn biến can thiệp (1=Đã can thiệp, 0=Chưa) --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Hệ số Phạt Chuẩn Hạt Nhân (Nuclear Norm λ)
              </label>
              <input
                type="number"
                step="0.05"
                min="0.01"
                value={lambdaNuc}
                onChange={(e) => setLambdaNuc(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Số vòng lặp tối đa (Max Iterations)
              </label>
              <select
                value={maxIter}
                onChange={(e) => setMaxIter(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              >
                <option value={80}>80 vòng lặp</option>
                <option value={150}>150 vòng lặp (Khuyến nghị)</option>
                <option value={300}>300 vòng lặp (Hội tụ cao)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Phạm vi dữ liệu (Scope)
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="all">Toàn bộ phản hồi (All)</option>
                <option value="verified_clean">Chỉ tập mẫu sạch xác thực (Verified Clean)</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg transition shadow-md shadow-indigo-500/20"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  <span>Đang hoàn thiện ma trận hạt nhân...</span>
                </>
              ) : (
                <>
                  <Grid className="w-4 h-4" />
                  <span>Chạy Hoàn Thiện Ma Trận Nhân Quả (MC-NNM)</span>
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
              <span className="text-xs text-slate-400 font-medium">Hiệu ứng Can thiệp (ATT)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-white">
                  {result.estimates?.att !== undefined
                    ? (result.estimates.att > 0 ? `+${result.estimates.att.toFixed(4)}` : result.estimates.att.toFixed(4))
                    : '--'}
                </span>
                <span className="text-xs text-indigo-400 font-semibold">
                  (p = {result.estimates?.p_value.toFixed(4) || '--'})
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                95% CI: [{result.estimates?.ci_low?.toFixed(3)}, {result.estimates?.ci_high?.toFixed(3)}]
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Kích thước Bảng &amp; Hạng Ma trận</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-sky-400">
                  {result.dimensions?.units_count} × {result.dimensions?.periods_count}
                </span>
                <span className="text-xs text-emerald-400 font-semibold">
                  (Rank = {result.algorithm_convergence?.latent_rank || 1})
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Số chiều nhân tố tiềm ẩn low-rank được phát hiện
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Sai số Khớp Đối chứng (RMSE)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-emerald-400">
                  {result.algorithm_convergence?.control_rmse?.toFixed(4) || '--'}
                </span>
                <span className="text-xs text-slate-400">
                  ({result.algorithm_convergence?.iterations} iters)
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Trạng thái hội tụ: {result.algorithm_convergence?.converged ? 'Đã hội tụ' : 'Đạt giới hạn lặp'}
              </p>
            </div>

            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Phân bổ Ô Tiếp nhận So le</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold text-amber-400">
                  {result.adoption_counts?.treated_cells || 0} Ô can thiệp
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                So sánh với {result.adoption_counts?.control_cells || 0} ô đối chứng thực nghiệm
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
                onClick={() => setActiveTab('heterogeneity')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'heterogeneity'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Hiệu ứng Dị biệt theo Đơn vị ({result.unit_heterogeneity?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('eventstudy')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'eventstudy'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Quỹ đạo Động học Event-Study ({result.event_study_trajectory?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('diagnostics')}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === 'diagnostics'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                }`}
              >
                Thông số Ma trận Hạt nhân
              </button>
            </div>

            {/* Tab 1: Unit Heterogeneity */}
            {activeTab === 'heterogeneity' && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Đơn vị Khảo sát (Unit ID)</th>
                      <th className="py-2.5 px-3 text-right">Số chu kỳ đã can thiệp</th>
                      <th className="py-2.5 px-3 text-right">Hiệu ứng Riêng phần (Unit ATT)</th>
                      <th className="py-2.5 px-3">Trực quan hóa Mức độ Tác động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.unit_heterogeneity?.map((uh, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50 transition">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{uh.unit}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{uh.treated_periods_count}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-sky-300">
                          {uh.unit_att > 0 ? `+${uh.unit_att.toFixed(4)}` : uh.unit_att.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="w-36 bg-slate-800 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${uh.unit_att >= 0 ? 'bg-indigo-500' : 'bg-rose-500'}`}
                              style={{ width: `${Math.min(Math.abs(uh.unit_att) * 15, 100)}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 2: Event Study */}
            {activeTab === 'eventstudy' && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Thời gian sau Can thiệp (Event Time)</th>
                      <th className="py-2.5 px-3 text-right">Hiệu ứng Can thiệp τ(e)</th>
                      <th className="py-2.5 px-3 text-right">Khoảng tin cậy 95%</th>
                      <th className="py-2.5 px-3 text-right">Số đơn vị quan sát</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.event_study_trajectory?.map((es, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50 transition">
                        <td className="py-2 px-3 font-mono font-medium text-indigo-400">
                          Kỳ +{es.event_time}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-sky-300">
                          {es.att > 0 ? `+${es.att.toFixed(4)}` : es.att.toFixed(4)}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-400">
                          [{es.ci_low.toFixed(3)}, {es.ci_high.toFixed(3)}]
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-300">
                          {es.sample_count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 3: Diagnostics */}
            {activeTab === 'diagnostics' && (
              <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <span className="text-slate-400">Hệ số Phạt Chuẩn Hạt Nhân (λ):</span>
                    <p className="font-mono text-white font-semibold text-sm mt-0.5">{lambdaNuc}</p>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <span className="text-slate-400">Hạng Ma trận Tiềm ẩn (Low-Rank):</span>
                    <p className="font-mono text-emerald-400 font-semibold text-sm mt-0.5">
                      Rank = {result.algorithm_convergence?.latent_rank} (trên tối đa {Math.min(result.dimensions?.units_count || 1, result.dimensions?.periods_count || 1)})
                    </p>
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
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition (Athey et al. 2021)
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
