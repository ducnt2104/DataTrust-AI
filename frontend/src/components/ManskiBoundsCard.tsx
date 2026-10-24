import React, { useState } from 'react';
import { ManskiBoundsResult } from '../types/survey';
import { api } from '../api/client';

interface ManskiBoundsCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const ManskiBoundsCard: React.FC<ManskiBoundsCardProps> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [responseIndQid, setResponseIndQid] = useState<string>('');
  const [supportMin, setSupportMin] = useState<string>('');
  const [supportMax, setSupportMax] = useState<string>('');
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ManskiBoundsResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Outcome: continuous / scale / rating
  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider'
  );

  // Treatment / Indicator questions
  const binaryOrChoiceQuestions = questions.filter(
    (q) =>
      q.question_type === 'single_choice' ||
      q.question_type === 'dropdown' ||
      q.question_type === 'number' ||
      q.question_type === 'linear_scale'
  );

  const handleRun = async () => {
    if (!outcomeQid || !treatmentQid) {
      setError('Vui lòng chọn cả Biến kết quả (Outcome) và Biến can thiệp (Treatment).');
      return;
    }
    if (outcomeQid === treatmentQid) {
      setError('Biến kết quả và Biến can thiệp không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const minVal = supportMin.trim() !== '' ? parseFloat(supportMin) : undefined;
      const maxVal = supportMax.trim() !== '' ? parseFloat(supportMax) : undefined;

      const res = await api.runManskiBounds(surveyId, {
        outcome_question_id: outcomeQid,
        treatment_question_id: treatmentQid,
        response_indicator_question_id: responseIndQid.trim() || undefined,
        support_min: isNaN(minVal as number) ? undefined : minVal,
        support_max: isNaN(maxVal as number) ? undefined : maxVal,
        confidence_level: confidenceLevel,
        scope
      });

      if (res.status === 'error' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Ước lượng biên Manski thất bại.');
      } else {
        setResult(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi kết nối máy chủ khi tính toán biên Manski.');
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
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-700/60 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
              Manski 1990 &bull; Manski &amp; Pepper 2000 &bull; Imbens &amp; Manski 2004
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Non-Parametric Partial Identification
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            Định lý Manski: Cận Xác định Bán phần &amp; Độ bền Mất mẫu (Worst-Case Bounds)
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Ước lượng khoảng hiệu ứng can thiệp ATE dưới dữ liệu khảo sát bị khuyết/mất mẫu (NMAR) mà không cần giả định phân phối bất khả kiểm chứng.
          </p>
        </div>
      </div>

      {/* Selectors Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Outcome Selector */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Biến Kết quả (Outcome Y) *
          </label>
          <select
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi đo lường kết quả --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Treatment Selector */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Biến Can thiệp (Treatment D) *
          </label>
          <select
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi phân nhóm Can thiệp --</option>
            {binaryOrChoiceQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Response Indicator Selector (Optional) */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Chỉ thị Phản hồi R (Tùy chọn)
          </label>
          <select
            value={responseIndQid}
            onChange={(e) => setResponseIndQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Tự động xác định từ câu trả lời khuyết --</option>
            {binaryOrChoiceQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Support Bounds Min */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Cận dưới Lý thuyết ($Y_{`\\min`}$)
          </label>
          <input
            type="number"
            step="any"
            value={supportMin}
            onChange={(e) => setSupportMin(e.target.value)}
            placeholder="Tự động từ min mẫu"
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Support Bounds Max */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Cận trên Lý thuyết ($Y_{`\\max`}$)
          </label>
          <input
            type="number"
            step="any"
            value={supportMax}
            onChange={(e) => setSupportMax(e.target.value)}
            placeholder="Tự động từ max mẫu"
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Scope Filter */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Phạm vi Lọc Dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">Toàn bộ mẫu hợp lệ (All Submissions)</option>
            <option value="verified_clean">Chỉ mẫu sạch đã kiểm định (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Action Button & Error */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleRun}
          disabled={loading || !outcomeQid || !treatmentQid}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-sm transition shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang ước lượng Cận Manski...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Ước lượng Cận Manski &amp; Phân tích Độ nhạy
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Results Display */}
      {result && result.diagnostics && (
        <div className="space-y-6 pt-4 border-t border-slate-100 dark:border-slate-700/60">
          {/* Key Metric Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Tổng mẫu N</span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-100 mt-0.5">
                {result.diagnostics.sample_size_total}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Tỷ lệ Mất mẫu</span>
              <p className="text-base font-bold text-amber-600 dark:text-amber-400 mt-0.5">
                {(result.diagnostics.missing_rate * 100).toFixed(1)}%
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Naive ATE (Ngây thơ)</span>
              <p className="text-base font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
                {result.diagnostics.naive_ate >= 0 ? `+${result.diagnostics.naive_ate.toFixed(3)}` : result.diagnostics.naive_ate.toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Cận MTS+MTR</span>
              <p className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                [{result.diagnostics.joint_mts_mtr_lower.toFixed(2)}, {result.diagnostics.joint_mts_mtr_upper.toFixed(2)}]
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Khoảng 95% IM-CI</span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-100 mt-0.5">
                [{result.diagnostics.ci_joint_lower_95.toFixed(2)}, {result.diagnostics.ci_joint_upper_95.toFixed(2)}]
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Điểm Gãy Dấu</span>
              <p className="text-base font-bold text-rose-600 dark:text-rose-400 mt-0.5">
                {result.diagnostics.breakdown_rate !== null && result.diagnostics.breakdown_rate !== undefined
                  ? `${(result.diagnostics.breakdown_rate * 100).toFixed(1)}%`
                  : 'Bền vững >50%'}
              </p>
            </div>
          </div>

          {/* Tier Hierarchy Table */}
          {result.tiers && (
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-800/80 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-4 py-3">Bậc Giả định Nhận dạng (Hierarchy)</th>
                    <th className="px-4 py-3">Cận Dưới (LB)</th>
                    <th className="px-4 py-3">Cận Trên (UB)</th>
                    <th className="px-4 py-3">Độ Rộng Biên (Width)</th>
                    <th className="px-4 py-3">Ý Nghĩa Khoa Học</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {result.tiers.map((t, idx) => (
                    <tr key={idx} className={idx === 3 ? 'bg-indigo-50/50 dark:bg-indigo-950/20 font-medium' : ''}>
                      <td className="px-4 py-2.5 font-medium flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${idx === 0 ? 'bg-slate-400' : idx === 1 ? 'bg-blue-400' : idx === 2 ? 'bg-teal-400' : 'bg-indigo-500'}`} />
                        {t.tier}
                      </td>
                      <td className="px-4 py-2.5 font-mono">{t.lower >= 0 ? `+${t.lower.toFixed(3)}` : t.lower.toFixed(3)}</td>
                      <td className="px-4 py-2.5 font-mono">{t.upper >= 0 ? `+${t.upper.toFixed(3)}` : t.upper.toFixed(3)}</td>
                      <td className="px-4 py-2.5 font-mono font-semibold">{t.width.toFixed(3)}</td>
                      <td className="px-4 py-2.5 text-xs text-slate-500 dark:text-slate-400">
                        {idx === 0 && 'Không đặt bất kỳ giả định nào về cơ chế khuyết NMAR.'}
                        {idx === 1 && 'Nhóm tự chọn can thiệp có tiềm năng không thấp hơn nhóm đối chứng.'}
                        {idx === 2 && 'Hiệu ứng can thiệp lên từng cá thể là không âm ($Y_i(1) \\ge Y_i(0)$).'}
                        {idx === 3 && 'Biên độ hẹp nhất kết hợp tính đơn điệu lựa chọn và đáp ứng.'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* SVG Visualizations */}
          {result.svg_visualization && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Đồ thị Khoa học: Phân cấp Biên Manski &amp; Đường cong Nhạy cảm Mất mẫu
              </h4>
              <div
                className="w-full overflow-x-auto rounded-lg bg-slate-900 p-2 shadow-inner flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative with Copy Button */}
          {result.apa_narrative && (
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                  Bản tường trình Học thuật chuẩn APA 7th (Non-Parametric Manski Bounds)
                </span>
                <button
                  onClick={copyNarrative}
                  className="px-2.5 py-1 text-xs font-medium rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 transition"
                >
                  {copied ? 'Đã sao chép!' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-400 font-serif italic">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
