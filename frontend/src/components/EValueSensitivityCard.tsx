import React, { useState } from 'react';
import {
  ShieldAlert,
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
  Bookmark,
  Target
} from 'lucide-react';
import { api } from '../api/client';
import {
  EValueResult,
  EValueRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const EValueSensitivityCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [effectType, setEffectType] = useState<'OLS_CONTINUOUS' | 'RR' | 'OR' | 'HR'>('OLS_CONTINUOUS');
  const [selectionBiasRR, setSelectionBiasRR] = useState<number>(1.0);
  const [misclassificationRR, setMisclassificationRR] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EValueResult | null>(null);
  const [activeTab, setActiveTab] = useState<'multibias' | 'benchmarks' | 'theory'>('multibias');
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

    setLoading(true);
    setError(null);

    try {
      const payload: EValueRequest = {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        effect_type: effectType,
        selection_bias_rr: selectionBiasRR,
        misclassification_rr: misclassificationRR,
        scope
      };

      const res = await api.runEValueSensitivity(surveyId, payload);
      setResult(res);
      setShowConfig(false);
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực thi phân tích E-Value.');
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
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-white tracking-wide">
                Phân Tích Độ Nhạy Nhân Quả & Thang Đo E-Value (Causal Sensitivity Analysis)
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-full">
                VanderWeele & Ding (2017) • Multi-Bias Decomposition
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Định lượng cường độ tối thiểu mà yếu tố gây nhiễu chưa đo lường (unmeasured confounder) cần đạt với cả can thiệp và kết quả để làm biến mất hiệu ứng nhân quả, tích hợp phân rã sai lệch lựa chọn và sai số đo lường.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowConfig(!showConfig)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium border border-slate-700 transition"
        >
          <Sliders className="w-4 h-4 text-amber-400" />
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
                <Activity className="w-3.5 h-3.5 text-amber-400" />
                Biến Can thiệp (Treatment: Nhị phân hoặc Liên tục) *
              </label>
              <select
                value={treatmentQId}
                onChange={(e) => setTreatmentQId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition"
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
                <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                Biến Kết quả (Outcome Y) *
              </label>
              <select
                value={outcomeQId}
                onChange={(e) => setOutcomeQId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition"
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
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              Các biến Đồng biến Kiểm soát (Tùy chọn) ({selectedCovariates.length} đã chọn)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto p-2 bg-slate-900/60 rounded-lg border border-slate-800">
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
                          ? 'bg-amber-500/15 border-amber-500/40 text-amber-200'
                          : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="rounded border-slate-700 text-amber-500 focus:ring-0"
                      />
                      <span className="truncate" title={q.title}>
                        {q.title}
                      </span>
                    </label>
                  );
                })}
            </div>
          </div>

          {/* Hyperparameters & Multi-bias Knobs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2 border-t border-slate-800/80">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-amber-400" />
                Loại Thang Đo Hiệu Ứng (Effect Scale)
              </label>
              <select
                value={effectType}
                onChange={(e) => setEffectType(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition"
              >
                <option value="OLS_CONTINUOUS">Biến liên tục OLS (Cohen's d quy đổi RR)</option>
                <option value="RR">Tỷ số Rủi ro (Risk Ratio)</option>
                <option value="OR">Tỷ số Chênh (Odds Ratio)</option>
                <option value="HR">Tỷ số Nguy cơ (Hazard Ratio)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                Hệ Số Sai Lệch Lựa Chọn (B_S)
              </label>
              <input
                type="number"
                step="0.05"
                min="1.0"
                max="5.0"
                value={selectionBiasRR}
                onChange={(e) => setSelectionBiasRR(parseFloat(e.target.value) || 1.0)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                Hệ Số Sai Số Đo Lường (B_M)
              </label>
              <input
                type="number"
                step="0.05"
                min="1.0"
                max="5.0"
                value={misclassificationRR}
                onChange={(e) => setMisclassificationRR(parseFloat(e.target.value) || 1.0)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                Phạm Vi Phân Tích (Scope)
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition"
              >
                <option value="all">Toàn bộ phản hồi (All Valid)</option>
                <option value="verified_clean">Chỉ mẫu sạch (Verified Clean)</option>
              </select>
            </div>
          </div>

          {/* Action button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-medium shadow-lg shadow-amber-900/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang tính toán E-Value & Multi-Bias...</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-4 h-4" />
                  <span>Ước Lượng Thang Đo E-Value</span>
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
            {/* KPI 1: E-value for Point Estimate */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                E-Value (Điểm Ước Lượng)
              </div>
              <div className="text-2xl font-extrabold text-amber-400">
                {result.e_value_results.e_value_estimate.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                RR tương đương: {result.e_value_results.rr_equivalent.toFixed(2)}
              </div>
            </div>

            {/* KPI 2: E-value for CI limit */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                E-Value (Khoảng Tin Cậy 95%)
              </div>
              <div className="text-2xl font-extrabold text-sky-400">
                {result.e_value_results.e_value_ci.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Cận gần null: {result.e_value_results.ci_closest_to_null.toFixed(2)}
              </div>
            </div>

            {/* KPI 3: Remaining E-value */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                E-Value Sau Đa Sai Lệch
              </div>
              <div className="text-2xl font-extrabold text-emerald-400">
                {result.e_value_results.e_value_confounding_remaining.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Trừ B_S={result.e_value_results.selection_bias_factor} × B_M={result.e_value_results.misclassification_factor}
              </div>
            </div>

            {/* KPI 4: Point Estimate */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Ước Lượng Hiệu Ứng Gốc
              </div>
              <div className="text-xl font-extrabold text-white">
                {result.point_estimate.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {result.standard_error.toFixed(3)} (SD_Y={result.outcome_sd.toFixed(2)})
              </div>
            </div>

            {/* KPI 5: Robustness Rating */}
            <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Mức Độ Vững Chắc
              </div>
              <div className="text-xl font-extrabold text-emerald-400">
                {result.e_value_results.e_value_estimate >= 2.0 ? 'Rất Mạnh (Strong)' : (result.e_value_results.e_value_estimate >= 1.5 ? 'Trung Bình (Moderate)' : 'Nhạy Cảm (Sensitive)')}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                N={result.sample_size} quan sát
              </div>
            </div>
          </div>

          {/* Responsive Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-amber-400" />
                  Đồ Thị Vector Trực Quan Hóa E-Value (Bias Contour Curve & Benchmark Milestones)
                </h4>
                <span className="text-xs text-slate-500">
                  DataTrust Epidemiological Vector Engine
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
              onClick={() => setActiveTab('multibias')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'multibias'
                  ? 'border-amber-400 text-amber-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Phân Rã Đa Sai Lệch (Multi-Bias Decomposition)</span>
            </button>

            <button
              onClick={() => setActiveTab('benchmarks')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'benchmarks'
                  ? 'border-amber-400 text-amber-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Bookmark className="w-4 h-4" />
              <span>So Chuẩn Dịch Tễ Học (Epidemiological Benchmarks)</span>
            </button>

            <button
              onClick={() => setActiveTab('theory')}
              className={`pb-2.5 flex items-center gap-2 transition border-b-2 ${
                activeTab === 'theory'
                  ? 'border-amber-400 text-amber-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>Nguyên Lý Toán Học & Khuyến Nghị Xuất Bản</span>
            </button>
          </div>

          {/* Tab Content: Multi-Bias */}
          {activeTab === 'multibias' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Thành Phần Sai Lệch</th>
                    <th className="py-2.5 px-3">Ký Hiệu</th>
                    <th className="py-2.5 px-3">Hệ Số Rủi Ro RR</th>
                    <th className="py-2.5 px-3">Ý Nghĩa Thực Nghiệm</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  <tr className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-medium text-white">Yếu Tố Gây Nhiễu Chưa Đo Lường (Unmeasured Confounder)</td>
                    <td className="py-2.5 px-3 font-mono text-amber-400">E-Value</td>
                    <td className="py-2.5 px-3 font-bold text-amber-300">{result.e_value_results.e_value_estimate.toFixed(3)}</td>
                    <td className="py-2.5 px-3 text-slate-400">Tương quan tối thiểu với cả can thiệp và kết quả để làm mất hiệu ứng.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-medium text-white">Cận Khoảng Tin Cậy 95% CI (Statistical Uncertainty)</td>
                    <td className="py-2.5 px-3 font-mono text-sky-400">E-Value_CI</td>
                    <td className="py-2.5 px-3 font-bold text-sky-300">{result.e_value_results.e_value_ci.toFixed(3)}</td>
                    <td className="py-2.5 px-3 text-slate-400">Tương quan tối thiểu để đưa khoảng tin cậy 95% bao hàm giá trị null (RR=1.0).</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-medium text-white">Sai Lệch Lựa Chọn Mẫu (Selection Bias Factor)</td>
                    <td className="py-2.5 px-3 font-mono text-purple-400">B_S</td>
                    <td className="py-2.5 px-3">{result.e_value_results.selection_bias_factor.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-slate-400">Mức độ thiên lệch do quá trình thu thập hoặc lọc mẫu không ngẫu nhiên.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-medium text-white">Sai Số Đo Lường Biến Số (Differential Misclassification)</td>
                    <td className="py-2.5 px-3 font-mono text-rose-400">B_M</td>
                    <td className="py-2.5 px-3">{result.e_value_results.misclassification_factor.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-slate-400">Mức độ phân loại nhầm can thiệp hoặc kết quả giữa các nhóm.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 transition bg-slate-800/30">
                    <td className="py-2.5 px-3 font-semibold text-emerald-400">E-Value Gây Nhiễu Còn Lại Sau Đa Sai Lệch</td>
                    <td className="py-2.5 px-3 font-mono text-emerald-400">E_remaining</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-300">{result.e_value_results.e_value_confounding_remaining.toFixed(3)}</td>
                    <td className="py-2.5 px-3 text-slate-300">Độ mạnh gây nhiễu vẫn cần có sau khi đã trừ hao tổn thất do B_S và B_M.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Tab Content: Benchmarks */}
          {activeTab === 'benchmarks' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Nghiên Cứu Mốc So Chuẩn (Benchmark Confounder)</th>
                    <th className="py-2.5 px-3">Tỷ Số Rủi Ro Tương Quan (RR)</th>
                    <th className="py-2.5 px-3">So Sánh Với E-Value Của Nghiên Cứu Này ({result.e_value_results.e_value_estimate.toFixed(2)})</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {result.benchmarks.map((b, i) => {
                    const isExceeded = result.e_value_results.e_value_estimate >= b.rr_benchmark;
                    return (
                      <tr key={i} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-medium text-white">{b.name}</td>
                        <td className="py-2.5 px-3 font-bold text-amber-300">{b.rr_benchmark.toFixed(2)}x</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              isExceeded
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : 'bg-slate-800 text-slate-300 border border-slate-700'
                            }`}
                          >
                            {isExceeded
                              ? 'Vượt qua mốc này (Hiệu ứng vững chắc hơn mốc này)'
                              : 'Thấp hơn mốc này (Yếu tố cực mạnh như hút thuốc có thể giải thích)'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab Content: Theory */}
          {activeTab === 'theory' && (
            <div className="p-4 bg-slate-800/40 border border-slate-800 rounded-lg text-xs text-slate-300 space-y-3 leading-relaxed">
              <p>
                <strong className="text-white">Đột phá của Thang đo E-Value (VanderWeele & Ding, 2017):</strong> Trong các nghiên cứu quan sát, việc phản biện lại hoài nghi về "yếu tố gây nhiễu chưa đo lường" thường rất mơ hồ. Thang đo E-value cung cấp một ngưỡng giới hạn toán học chính xác không dựa trên giả định phân phối, định lượng cụ thể độ mạnh tối thiểu RR_UD và RR_UY mà một yếu tố gây nhiễu phải đạt được để xóa sổ hiệu ứng quan sát.
              </p>
              <p>
                <strong className="text-white">Khuyến nghị Báo cáo Khoa học Quốc tế (Annals of Internal Medicine):</strong> Báo cáo cả E-value cho điểm ước lượng và E-value cho cận khoảng tin cậy 95% gần giá trị null nhất. Nếu E-value_CI &gt; 1.5 đến 2.0, nghiên cứu được đánh giá là có độ tin cậy thực nghiệm rất cao trước các hoài nghi về nội sinh và biến ẩn.
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
                {copied ? <Check className="w-3.5 h-3.5 text-amber-400" /> : <Copy className="w-3.5 h-3.5" />}
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
