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
  Sliders,
  Sparkles,
  HelpCircle,
  Scissors,
  EyeOff,
  Filter,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import {
  PartialAttritionBoundsRequest,
  PartialAttritionBoundsResult
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const PartialAttritionBoundsCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentId, setTreatmentId] = useState<string>('');
  const [outcomeId, setOutcomeId] = useState<string>('');
  const [responseId, setResponseId] = useState<string>('');
  const [userYmin, setUserYmin] = useState<string>('');
  const [userYmax, setUserYmax] = useState<string>('');
  const [alpha, setAlpha] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PartialAttritionBoundsResult | null>(null);
  const [activeTab, setActiveTab] = useState<'chart' | 'table' | 'sensitivity' | 'apa'>('chart');
  const [copied, setCopied] = useState<boolean>(false);

  const candidateQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'single_choice'
  );

  const handleRun = async () => {
    if (!treatmentId) {
      setError('Vui lòng chọn biến Can thiệp / Phân bổ nhóm (Treatment D 0/1).');
      return;
    }
    if (!outcomeId) {
      setError('Vui lòng chọn biến Kết quả Causal (Outcome Y).');
      return;
    }
    if (treatmentId === outcomeId) {
      setError('Biến can thiệp và biến kết quả không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: PartialAttritionBoundsRequest = {
      treatment_question_id: treatmentId,
      outcome_question_id: outcomeId,
      response_question_id: responseId || undefined,
      user_ymin: userYmin ? parseFloat(userYmin) : undefined,
      user_ymax: userYmax ? parseFloat(userYmax) : undefined,
      alpha,
      scope,
    };

    try {
      const data = await api.runPartialAttritionBounds(surveyId, payload);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi thực thi phân tích Partial Attrition Bounds.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden mb-8">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 dark:border-slate-800 bg-gradient-to-r from-amber-50/50 via-orange-50/30 to-transparent dark:from-amber-950/20 dark:via-orange-950/10 dark:to-transparent">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-600 text-white shadow-md shadow-amber-500/20">
              <EyeOff className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Partial Identification & Non-Random Attrition Bounds Engine
                </h3>
                <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                  DataTrust Iteration 192
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Ước lượng khoảng chặn tác động nhân quả khi người trả lời bỏ dở khảo sát có chọn lọc bằng Horowitz-Manski (2000) Worst-Case Bounds, Lee (2009) Trimming & Manski-Pepper (2000) MTS
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Configuration Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 p-5 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
          {/* Treatment D */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Biến Can Thiệp Nhóm (Treatment D 0/1) *
            </label>
            <select
              value={treatmentId}
              onChange={(e) => setTreatmentId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-amber-500"
            >
              <option value="">-- Chọn biến can thiệp D --</option>
              {candidateQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Outcome Y */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Biến Kết Quả Đánh Giá (Outcome Y) *
            </label>
            <select
              value={outcomeId}
              onChange={(e) => setOutcomeId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-amber-500"
            >
              <option value="">-- Chọn biến kết quả Y --</option>
              {candidateQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Optional Response Status Question */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Chỉ Báo Hoàn Thành (Response R 0/1) (Tùy chọn)
            </label>
            <select
              value={responseId}
              onChange={(e) => setResponseId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-amber-500"
            >
              <option value="">-- Tự động nhận diện giá trị trống (Missing Y) --</option>
              {candidateQuestions
                .filter((q) => q.id !== treatmentId && q.id !== outcomeId)
                .map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title}
                  </option>
                ))}
            </select>
          </div>

          {/* User Ymin */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Cận Dưới Lý Thuyết (y_min) (Tùy chọn)
            </label>
            <input
              type="number"
              placeholder="Tự động lấy min(Y)"
              value={userYmin}
              onChange={(e) => setUserYmin(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-amber-500"
            />
          </div>

          {/* User Ymax */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Cận Trên Lý Thuyết (y_max) (Tùy chọn)
            </label>
            <input
              type="number"
              placeholder="Tự động lấy max(Y)"
              value={userYmax}
              onChange={(e) => setUserYmax(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-amber-500"
            />
          </div>

          {/* Alpha Level */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Mức Ý Nghĩa (\alpha)
            </label>
            <select
              value={alpha}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-amber-500"
            >
              <option value="0.05">\alpha = 0.05 (Khoảng tin cậy 95% Imbens-Manski)</option>
              <option value="0.01">\alpha = 0.01 (Khoảng tin cậy 99% Imbens-Manski)</option>
              <option value="0.10">\alpha = 0.10 (Khoảng tin cậy 90% Imbens-Manski)</option>
            </select>
          </div>

          {/* Scope and Action */}
          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Phạm vi dữ liệu:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2.5 py-1.5 text-slate-800 dark:text-slate-200"
            >
              <option value="all">Tất cả người trả lời</option>
              <option value="verified_clean">Chỉ mẫu Verified Clean</option>
            </select>
          </div>

          <div className="md:col-span-2 flex justify-end items-center gap-3">
            <button
              onClick={handleRun}
              disabled={loading || !treatmentId || !outcomeId}
              className="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-semibold text-sm shadow-md shadow-amber-500/20 flex items-center gap-2 transition-all"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Đang tính toán khoảng chặn...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Ước Lượng Chặn Attrition</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-400 flex items-center gap-3 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results View */}
        {result && (
          <div className="space-y-6">
            {/* KPI Stat Ribbon */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Cỡ Mẫu Khảo Sát</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  N = {result.sample_size}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  N_T = {result.sample_treatment}, N_C = {result.sample_control}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Tỷ Lệ Mất Dấu (Attrition)</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {(result.overall_attrition_rate * 100).toFixed(1)}%
                </div>
                <div className="text-[11px] mt-0.5">
                  T: {(result.response_rate_treatment * 100).toFixed(0)}% vs C: {(result.response_rate_control * 100).toFixed(0)}%
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Naive Complete-Case</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1 font-mono">
                  {result.naive_complete_case.ate > 0 ? '+' : ''}{result.naive_complete_case.ate.toFixed(3)}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Giả định MAR (bị chệch nếu non-random)
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Lee (2009) Bounds</span>
                <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                  [{result.lee_trimming_bounds.lower_bound.toFixed(2)}, {result.lee_trimming_bounds.upper_bound.toFixed(2)}]
                </div>
                <div className="text-[11px] mt-0.5">
                  {result.lee_trimming_bounds.straddles_zero ? (
                    <span className="text-amber-600 dark:text-amber-400 font-medium">Chứa điểm 0 (Chưa chắc chắn)</span>
                  ) : (
                    <span className="text-emerald-600 dark:text-emerald-400 font-medium">Loại trừ 0 (Vững trước attrition)</span>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 col-span-2 sm:col-span-4 lg:col-span-1">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Manski Worst-Case</span>
                <div className="text-sm font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                  [{result.manski_horowitz_bounds.lower_bound.toFixed(2)}, {result.manski_horowitz_bounds.upper_bound.toFixed(2)}]
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Độ rộng: {result.manski_horowitz_bounds.interval_width.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-700 space-x-4">
              <button
                onClick={() => setActiveTab('chart')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'chart'
                    ? 'border-amber-600 text-amber-700 dark:text-amber-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span>Biểu Đồ Trực Quan Hóa (Dual-Panel)</span>
              </button>
              <button
                onClick={() => setActiveTab('table')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'table'
                    ? 'border-amber-600 text-amber-700 dark:text-amber-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Bảng So Sánh Các Khoảng Chặn</span>
              </button>
              <button
                onClick={() => setActiveTab('sensitivity')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'sensitivity'
                    ? 'border-amber-600 text-amber-700 dark:text-amber-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <Activity className="w-4 h-4" />
                <span>Đường Nhạy Cảm Attrition (Sensitivity)</span>
              </button>
              <button
                onClick={() => setActiveTab('apa')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'apa'
                    ? 'border-amber-600 text-amber-700 dark:text-amber-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Báo Cáo Học Thuật APA 7th</span>
              </button>
            </div>

            {/* Tab 1: Vector Visualizer */}
            {activeTab === 'chart' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 overflow-x-auto shadow-inner">
                  <div
                    className="w-full flex justify-center"
                    dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                  />
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic">
                  * Panel A minh họa các khoảng chặn định danh một phần (Partial Identification Intervals) kèm khoảng tin cậy 95% Imbens & Manski (2004). Panel B biểu diễn tác động can thiệp ATE suy ra dưới các giả định trung bình khác nhau của nhóm bị mất dấu \mu_attrited.
                </div>
              </div>
            )}

            {/* Tab 2: Comparison Table */}
            {activeTab === 'table' && (
              <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 uppercase font-bold border-b border-slate-200 dark:border-slate-700">
                      <tr>
                        <th className="py-3 px-4">Phương Pháp Định Danh</th>
                        <th className="py-3 px-3 text-right">Cận Dưới (Lower)</th>
                        <th className="py-3 px-3 text-right">Cận Trên (Upper)</th>
                        <th className="py-3 px-3 text-right">Độ Rộng (Width)</th>
                        <th className="py-3 px-3 text-right">95% Imbens-Manski CI</th>
                        <th className="py-3 px-4">Giả Định Dữ Liệu Khuyết</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {/* Naive Row */}
                      <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">
                          Naive Complete-Case (MAR)
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.naive_complete_case.ate.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.naive_complete_case.ate.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-slate-400">
                          0.000 (Điểm)
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-slate-600 dark:text-slate-400">
                          [{result.naive_complete_case.ci_95[0].toFixed(3)}, {result.naive_complete_case.ci_95[1].toFixed(3)}]
                        </td>
                        <td className="py-3 px-4 text-slate-500 text-[11px]">
                          Giả định Missing At Random (MAR); chệch nếu attrition có chọn lọc.
                        </td>
                      </tr>

                      {/* Lee Row */}
                      <tr className="bg-emerald-50/40 dark:bg-emerald-950/20 font-semibold text-emerald-900 dark:text-emerald-200 hover:bg-emerald-50/60">
                        <td className="py-3 px-4 flex items-center gap-2">
                          <Scissors className="w-3.5 h-3.5 text-emerald-600" />
                          Lee (2009) Monotonic Trimming
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-sm">
                          {result.lee_trimming_bounds.lower_bound.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-sm">
                          {result.lee_trimming_bounds.upper_bound.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.lee_trimming_bounds.interval_width.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          [{result.lee_trimming_bounds.imbens_manski_ci_95[0].toFixed(3)}, {result.lee_trimming_bounds.imbens_manski_ci_95[1].toFixed(3)}]
                        </td>
                        <td className="py-3 px-4 text-emerald-800 dark:text-emerald-300 text-[11px] font-normal">
                          Cắt tỉa tỷ lệ dư thừa q = {(result.lee_trimming_bounds.trimming_ratio * 100).toFixed(1)}% theo giả định đơn điệu R(1) \ge R(0).
                        </td>
                      </tr>

                      {/* MTS Row */}
                      <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">
                          MTS Bounds (Manski & Pepper 2000)
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.mts_bounds.lower_bound.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.mts_bounds.upper_bound.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.mts_bounds.interval_width.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-slate-600 dark:text-slate-400">
                          [{result.mts_bounds.imbens_manski_ci_95[0].toFixed(3)}, {result.mts_bounds.imbens_manski_ci_95[1].toFixed(3)}]
                        </td>
                        <td className="py-3 px-4 text-slate-500 text-[11px]">
                          Giả định Monotone Treatment Selection (người chọn can thiệp có tiềm năng cao hơn).
                        </td>
                      </tr>

                      {/* Manski Row */}
                      <tr className="bg-amber-50/30 dark:bg-amber-950/20 hover:bg-amber-50/50">
                        <td className="py-3 px-4 font-semibold text-amber-900 dark:text-amber-200">
                          Horowitz-Manski (2000) Worst-Case
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.manski_horowitz_bounds.lower_bound.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.manski_horowitz_bounds.upper_bound.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {result.manski_horowitz_bounds.interval_width.toFixed(4)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-slate-600 dark:text-slate-400">
                          [{result.manski_horowitz_bounds.imbens_manski_ci_95[0].toFixed(3)}, {result.manski_horowitz_bounds.imbens_manski_ci_95[1].toFixed(3)}]
                        </td>
                        <td className="py-3 px-4 text-slate-500 text-[11px]">
                          Không đưa ra bất kỳ giả định nào về cơ chế mất dấu; cận trên/dưới trong khoảng [{result.outcome_bounds.ymin}, {result.outcome_bounds.ymax}].
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 3: Sensitivity */}
            {activeTab === 'sensitivity' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                    Bảng Phân Tích Độ Nhạy Theo Giá Trị Kỳ Vọng Nhóm Bỏ Dở (\mu_attrited)
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                    Bảng thể hiện mức tác động ATE suy ra tương ứng với các kịch bản trung bình của nhóm người trả lời bị mất dấu trong khoảng [{result.outcome_bounds.ymin}, {result.outcome_bounds.ymax}].
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-2 max-h-72 overflow-y-auto">
                    {result.sensitivity_grid.map((pt, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs"
                      >
                        <div className="text-slate-500 dark:text-slate-400 text-[10px]">
                          \mu_miss = {pt.mu_attrited.toFixed(2)}
                        </div>
                        <div className="font-mono font-bold text-slate-800 dark:text-white mt-0.5">
                          ATE = {pt.implied_ate > 0 ? '+' : ''}{pt.implied_ate.toFixed(3)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 4: APA Narrative */}
            {activeTab === 'apa' && (
              <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 relative">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Báo Cáo Học Thuật Chuẩn APA 7th Edition
                  </h4>
                  <button
                    onClick={handleCopyAPA}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 transition-colors flex items-center gap-1.5 text-xs font-medium"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-amber-600" />
                        <span className="text-amber-600 font-semibold">Đã copy</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy APA</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-serif">
                  {result.apa_narrative}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
