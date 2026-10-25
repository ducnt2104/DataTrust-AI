import React, { useState } from 'react';
import {
  Layers,
  BarChart3,
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  Activity,
  ArrowRight,
  GitBranch,
  Sliders,
  Sparkles,
  HelpCircle,
  LayoutGrid
} from 'lucide-react';
import { api } from '../api/client';
import {
  FactorialConjointAMCEResult,
  FactorialConjointAMCERequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const FactorialConjointAMCECard: React.FC<Props> = ({ surveyId, questions }) => {
  const [choiceId, setChoiceId] = useState<string>('');
  const [attributeIds, setAttributeIds] = useState<string[]>([]);
  const [positionId, setPositionId] = useState<string>('');
  const [taskId, setTaskId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FactorialConjointAMCEResult | null>(null);
  const [activeTab, setActiveTab] = useState<'amce' | 'marginal_means' | 'validity' | 'apa'>('amce');
  const [copied, setCopied] = useState<boolean>(false);

  const candidateQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'dropdown'
  );

  const handleToggleAttribute = (qid: string) => {
    if (attributeIds.includes(qid)) {
      setAttributeIds(attributeIds.filter((id) => id !== qid));
    } else {
      setAttributeIds([...attributeIds, qid]);
    }
  };

  const handleRun = async () => {
    if (!choiceId) {
      setError('Vui lòng chọn biến Kết quả Lựa chọn (Choice Outcome 0/1 hoặc Rating).');
      return;
    }
    if (attributeIds.length === 0) {
      setError('Vui lòng chọn ít nhất một biến Thuộc tính Conjoint (Attributes).');
      return;
    }
    if (attributeIds.includes(choiceId)) {
      setError('Biến kết quả lựa chọn không được trùng với các biến thuộc tính.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: FactorialConjointAMCERequest = {
      choice_question_id: choiceId,
      attribute_question_ids: attributeIds,
      position_question_id: positionId || undefined,
      task_question_id: taskId || undefined,
      scope,
    };

    try {
      const data = await api.runFactorialConjointAMCE(surveyId, payload);
      setResult(data);
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực thi phân tích Factorial Conjoint AMCE.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-teal-500/10 text-teal-400 rounded-lg">
              <LayoutGrid className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold tracking-tight text-white">
              Factorial Conjoint Experiment Analysis &amp; AMCE Engine
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Ước lượng phi tham số Average Marginal Component Effects (AMCE), Marginal Means (MM) &amp; Sai số chuẩn gom cụm (Hainmueller et al. 2014; Leeper et al. 2020)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 font-medium">
            Hainmueller et al. 2014
          </span>
          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
            Marginal Means Parity
          </span>
        </div>
      </div>

      {/* Config Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Choice Outcome */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
            Biến Quyết Định Lựa Chọn (0/1 hoặc Rating) <span className="text-rose-400">*</span>
          </label>
          <select
            value={choiceId}
            onChange={(e) => setChoiceId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
          >
            <option value="">-- Chọn biến Lựa chọn --</option>
            {candidateQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Position Question */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            Vị Trí Profile (Tùy chọn: 1 hoặc 2)
          </label>
          <select
            value={positionId}
            onChange={(e) => setPositionId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">-- Không có (Bỏ qua Profile Order test) --</option>
            {candidateQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Task Question */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            Thứ Tự Tác Vụ / Vòng Chọn (Tùy chọn)
          </label>
          <select
            value={taskId}
            onChange={(e) => setTaskId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="">-- Không có (Bỏ qua Fatigue test) --</option>
            {candidateQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Attributes Multi-Select */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-amber-400" />
          Các Biến Thuộc Tính Conjoint (Chọn 2 hoặc nhiều hơn) <span className="text-rose-400">*</span>
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-36 overflow-y-auto p-2 bg-slate-950/60 rounded-lg border border-slate-800">
          {candidateQuestions
            .filter((q) => q.id !== choiceId && q.id !== positionId && q.id !== taskId)
            .map((q) => {
              const isSelected = attributeIds.includes(q.id);
              return (
                <button
                  type="button"
                  key={q.id}
                  onClick={() => handleToggleAttribute(q.id)}
                  className={`text-left text-xs px-2.5 py-1.5 rounded-md border transition-colors flex items-center justify-between ${
                    isSelected
                      ? 'bg-teal-500/20 border-teal-500/50 text-teal-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate pr-1">{q.title}</span>
                  {isSelected && <Check className="w-3 h-3 flex-shrink-0" />}
                </button>
              );
            })}
        </div>
      </div>

      {/* Scope & Run Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2 bg-slate-950/40 p-2 rounded-lg border border-slate-800">
          <label className="text-xs text-slate-300">Dữ liệu:</label>
          <select
            value={scope}
            onChange={(e: any) => setScope(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
          >
            <option value="all">Tất cả bản ghi</option>
            <option value="verified_clean">Chỉ bản ghi sạch (Verified Clean)</option>
          </select>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-rose-400 text-xs bg-rose-500/10 px-3 py-2 rounded-lg border border-rose-500/20">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          onClick={handleRun}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg font-semibold text-sm bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white shadow-lg shadow-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all self-end"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Đang tính toán AMCE &amp; Clustered SEs...</span>
            </>
          ) : (
            <>
              <Activity className="w-4 h-4" />
              <span>Thực thi Factorial Conjoint Analysis</span>
            </>
          )}
        </button>
      </div>

      {/* Results View */}
      {result && (
        <div className="mt-6 space-y-6 pt-6 border-t border-slate-800 animate-fadeIn">
          {/* Key Metric Badges */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {/* Total Profile Rows */}
            <div className="bg-teal-950/20 border border-teal-500/30 rounded-lg p-3.5 relative overflow-hidden">
              <div className="text-xs text-teal-400 font-medium">Hồ Sơ Đã Đánh Giá (M)</div>
              <div className="text-2xl font-bold text-white mt-1">
                {result.sample_size_profiles.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Từ N = {result.respondent_count} người trả lời
              </div>
            </div>

            {/* Evaluated Attributes */}
            <div className="bg-blue-950/20 border border-blue-500/30 rounded-lg p-3.5 relative overflow-hidden">
              <div className="text-xs text-blue-400 font-medium">Thuộc Tính Nghiên Cứu</div>
              <div className="text-2xl font-bold text-white mt-1">
                {result.attributes_evaluated.length} Thuộc tính
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Ước lượng phi tham số (Hainmueller)
              </div>
            </div>

            {/* Profile Order Diagnostic */}
            <div className={`p-3.5 rounded-lg border ${
              result.validity_diagnostics.profile_order?.order_bias_detected
                ? 'bg-rose-950/20 border-rose-500/30'
                : 'bg-emerald-950/20 border-emerald-500/30'
            }`}>
              <div className="text-xs text-slate-400 font-medium">Hiệu Ứng Vị Trí (Order Bias)</div>
              <div className={`text-2xl font-bold mt-1 ${
                result.validity_diagnostics.profile_order?.order_bias_detected ? 'text-rose-400' : 'text-emerald-400'
              }`}>
                {result.validity_diagnostics.profile_order ? (result.validity_diagnostics.profile_order.order_bias_detected ? 'Thiên Lệch' : 'Độc Lập') : 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                {result.validity_diagnostics.profile_order ? `Δ = ${result.validity_diagnostics.profile_order.order_difference.toFixed(3)} (p = ${result.validity_diagnostics.profile_order.p_value.toFixed(3)})` : 'Chưa chọn biến vị trí'}
              </div>
            </div>

            {/* Task Fatigue Diagnostic */}
            <div className={`p-3.5 rounded-lg border ${
              result.validity_diagnostics.task_fatigue?.fatigue_detected
                ? 'bg-amber-950/20 border-amber-500/30'
                : 'bg-emerald-950/20 border-emerald-500/30'
            }`}>
              <div className="text-xs text-slate-400 font-medium">Hiệu Ứng Mệt Mỏi (Fatigue)</div>
              <div className={`text-2xl font-bold mt-1 ${
                result.validity_diagnostics.task_fatigue?.fatigue_detected ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {result.validity_diagnostics.task_fatigue ? (result.validity_diagnostics.task_fatigue.fatigue_detected ? 'Phát Hiện' : 'Ổn Định') : 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                {result.validity_diagnostics.task_fatigue ? `Slope = ${result.validity_diagnostics.task_fatigue.task_slope.toFixed(4)}` : 'Chưa chọn biến vòng chọn'}
              </div>
            </div>
          </div>

          {/* SVG Visualizer */}
          <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 overflow-hidden shadow-inner">
            <div
              className="w-full flex justify-center"
              dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
            />
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('amce')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'amce'
                  ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Bảng Ước Lượng AMCE (Tác Động Biên)
            </button>
            <button
              onClick={() => setActiveTab('marginal_means')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'marginal_means'
                  ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              Trung Bình Biên (Marginal Means)
            </button>
            <button
              onClick={() => setActiveTab('validity')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'validity'
                  ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Kiểm Định Hiệu Lực Nội Tại
            </button>
            <button
              onClick={() => setActiveTab('apa')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'apa'
                  ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Copy className="w-3.5 h-3.5" />
              Báo Cáo APA 7th
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'amce' && (
            <div className="space-y-4">
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-300 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Thuộc Tính (Attribute)</th>
                      <th className="px-4 py-3">Mức Độ (Level)</th>
                      <th className="px-4 py-3 text-right">Hệ Số AMCE</th>
                      <th className="px-4 py-3 text-right">SE Gom Cụm</th>
                      <th className="px-4 py-3 text-right">z-statistic</th>
                      <th className="px-4 py-3 text-right">p-value</th>
                      <th className="px-4 py-3 text-right">95% Clustered CI</th>
                      <th className="px-4 py-3 text-center">Ý Nghĩa Thống Kê</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                    {Object.entries(result.amce_estimates).map(([attrName, rows]) =>
                      rows.map((r, idx) => (
                        <tr key={`${attrName}_${idx}`} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-4 py-2.5 font-bold text-slate-200">{idx === 0 ? attrName : ''}</td>
                          <td className="px-4 py-2.5 font-medium text-slate-300">
                            {r.level}
                            {r.is_reference && (
                              <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-normal">
                                Cơ sở (Reference)
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2.5 text-right font-mono font-bold text-slate-100">
                            {r.is_reference ? '0.000' : `${r.estimate > 0 ? '+' : ''}${r.estimate.toFixed(3)}`}
                          </td>
                          <td className="px-4 py-2.5 text-right text-slate-400">
                            {r.is_reference ? '-' : r.std_error.toFixed(3)}
                          </td>
                          <td className="px-4 py-2.5 text-right text-slate-400">
                            {r.is_reference ? '-' : r.z_statistic.toFixed(2)}
                          </td>
                          <td className="px-4 py-2.5 text-right text-slate-400">
                            {r.is_reference ? '-' : r.p_value.toFixed(4)}
                          </td>
                          <td className="px-4 py-2.5 text-right font-mono text-slate-300">
                            {r.is_reference ? '[0.000, 0.000]' : `[${r.ci_95[0].toFixed(3)}, ${r.ci_95[1].toFixed(3)}]`}
                          </td>
                          <td className="px-4 py-2.5 text-center">
                            {r.is_reference ? (
                              <span className="text-slate-500 text-[11px]">-</span>
                            ) : r.is_significant ? (
                              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                Có ý nghĩa (p &lt; 0.05)
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-400">
                                Chưa có ý nghĩa
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'marginal_means' && (
            <div className="space-y-4">
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-300 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Thuộc Tính</th>
                      <th className="px-4 py-3">Mức Độ</th>
                      <th className="px-4 py-3 text-right">Trung Bình Biên (MM)</th>
                      <th className="px-4 py-3 text-right">SE Gom Cụm</th>
                      <th className="px-4 py-3 text-right">95% Clustered CI</th>
                      <th className="px-4 py-3 text-right">Số Hồ Sơ (Profiles)</th>
                      <th className="px-4 py-3 text-center">Độ Lệch Ngang Giá (vs 0.50)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                    {Object.entries(result.marginal_means).map(([attrName, rows]) =>
                      rows.map((r, idx) => (
                        <tr key={`${attrName}_mm_${idx}`} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-4 py-2.5 font-bold text-slate-200">{idx === 0 ? attrName : ''}</td>
                          <td className="px-4 py-2.5 font-medium text-slate-300">{r.level}</td>
                          <td className="px-4 py-2.5 text-right font-mono font-bold text-teal-400">
                            {r.marginal_mean.toFixed(3)}
                          </td>
                          <td className="px-4 py-2.5 text-right text-slate-400">{r.std_error.toFixed(3)}</td>
                          <td className="px-4 py-2.5 text-right font-mono text-slate-300">
                            [{r.ci_95[0].toFixed(3)}, {r.ci_95[1].toFixed(3)}]
                          </td>
                          <td className="px-4 py-2.5 text-right text-slate-400">{r.profile_count}</td>
                          <td className="px-4 py-2.5 text-center">
                            <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                              r.relative_to_parity > 0.03
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : r.relative_to_parity < -0.03
                                ? 'bg-rose-500/20 text-rose-400'
                                : 'bg-slate-800 text-slate-400'
                            }`}>
                              {r.relative_to_parity > 0 ? '+' : ''}{r.relative_to_parity.toFixed(3)}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              <p className="text-[11px] text-slate-400">
                * Ưu điểm của Marginal Means (Leeper et al. 2020): Khác với AMCE phụ thuộc vào mức cơ sở được chọn ngẫu nhiên, Marginal Means phản ánh xác suất lựa chọn tuyệt đối của từng mức độ khi phân bổ ngẫu nhiên đều các thuộc tính khác.
              </p>
            </div>
          )}

          {activeTab === 'validity' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 space-y-3">
                <div className="font-semibold text-teal-400 flex items-center gap-1.5">
                  <Sliders className="w-4 h-4" />
                  Kiểm Định Thiên Lệch Vị Trí (Profile Order Bias)
                </div>
                {result.validity_diagnostics.profile_order ? (
                  <div className="space-y-2 text-slate-300">
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Tỷ lệ chọn Profile Vị trí 1 (Trái/Trên):</span>
                      <span className="font-semibold font-mono text-slate-100">
                        {result.validity_diagnostics.profile_order.position_1_choice_rate.toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Tỷ lệ chọn Profile Vị trí 2 (Phải/Dưới):</span>
                      <span className="font-semibold font-mono text-slate-100">
                        {result.validity_diagnostics.profile_order.position_2_choice_rate.toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Độ chênh lệch vị trí (Position Difference):</span>
                      <span className="font-semibold font-mono text-slate-100">
                        {result.validity_diagnostics.profile_order.order_difference.toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-400">Kết luận kiểm định:</span>
                      <span className={`font-semibold ${
                        result.validity_diagnostics.profile_order.order_bias_detected ? 'text-rose-400' : 'text-emerald-400'
                      }`}>
                        {result.validity_diagnostics.profile_order.interpretation}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-400">Không có dữ liệu vị trí profile để kiểm tra thiên lệch thứ tự.</p>
                )}
              </div>

              <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 space-y-3">
                <div className="font-semibold text-purple-400 flex items-center gap-1.5">
                  <Activity className="w-4 h-4" />
                  Kiểm Định Mệt Mỏi &amp; Tác Động Lan Truyền (Task Carryover)
                </div>
                {result.validity_diagnostics.task_fatigue ? (
                  <div className="space-y-2 text-slate-300">
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Số vòng tác vụ lựa chọn (Choice Tasks):</span>
                      <span className="font-semibold">{result.validity_diagnostics.task_fatigue.num_tasks} vòng</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Hệ số xu hướng theo vòng (Task Slope):</span>
                      <span className="font-semibold font-mono text-slate-100">
                        {result.validity_diagnostics.task_fatigue.task_slope.toFixed(5)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">p-value kiểm định xu hướng:</span>
                      <span className="font-semibold font-mono text-slate-100">
                        p = {result.validity_diagnostics.task_fatigue.p_value.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-400">Kết luận kiểm định:</span>
                      <span className={`font-semibold ${
                        result.validity_diagnostics.task_fatigue.fatigue_detected ? 'text-amber-400' : 'text-emerald-400'
                      }`}>
                        {result.validity_diagnostics.task_fatigue.interpretation}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-400">Không có dữ liệu số thứ tự vòng tác vụ để kiểm tra hiệu ứng mệt mỏi.</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'apa' && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">
                  Diễn giải kết quả chuẩn APA 7th Edition:
                </span>
                <button
                  onClick={handleCopyAPA}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-md transition-colors flex items-center gap-1.5"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép văn bản'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif bg-slate-900/60 p-4 rounded-lg border border-slate-800/80 italic">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
