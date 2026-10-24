import React, { useState } from 'react';
import { StochasticDominanceResult } from '../types/survey';
import { api } from '../api/client';

interface StochasticDominanceCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const StochasticDominanceCard: React.FC<StochasticDominanceCardProps> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [groupQid, setGroupQid] = useState<string>('');
  const [groupALabel, setGroupALabel] = useState<string>('');
  const [groupBLabel, setGroupBLabel] = useState<string>('');
  const [nGridPoints, setNGridPoints] = useState<number>(50);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StochasticDominanceResult | null>(null);
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

  // Group: single_choice / dropdown / boolean
  const groupQuestions = questions.filter(
    (q) =>
      q.question_type === 'single_choice' ||
      q.question_type === 'dropdown' ||
      q.question_type === 'likert' ||
      q.question_type === 'linear_scale'
  );

  const handleRun = async () => {
    if (!outcomeQid || !groupQid) {
      setError('Vui lòng chọn cả Biến kết quả (Outcome) và Biến phân nhóm (Group).');
      return;
    }
    if (outcomeQid === groupQid) {
      setError('Biến kết quả và Biến phân nhóm không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runStochasticDominance(surveyId, {
        outcome_question_id: outcomeQid,
        group_question_id: groupQid,
        group_a_label: groupALabel.trim() || undefined,
        group_b_label: groupBLabel.trim() || undefined,
        n_grid_points: nGridPoints,
        scope
      });

      if (res.status === 'error') {
        setError(res.message || 'Kiểm định vượt trội ngẫu nhiên thất bại.');
      } else {
        setResult(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi kết nối máy chủ khi tính toán vượt trội ngẫu nhiên.');
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
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
              Hadar &amp; Russell 1969 &bull; Davidson &amp; Duclos 2000
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              First- &amp; Second-Order Stochastic Dominance (FSD &amp; SSD)
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            Kiểm định Vượt trội Ngẫu nhiên &amp; Bất bình đẳng Phân phối (Stochastic Dominance)
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            So sánh toàn diện phân phối trải nghiệm khách hàng/điểm đánh giá giữa 2 nhóm theo tiêu chuẩn tối đa hóa hữu dụng kỳ vọng (FSD) và né tránh rủi ro (SSD).
          </p>
        </div>
      </div>

      {/* Selectors Form */}
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Biến kết quả / Thang đo đánh giá (Outcome Variable Y):
            </label>
            <select
              value={outcomeQid}
              onChange={(e) => setOutcomeQid(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            >
              <option value="">-- Chọn câu hỏi đo lường kết quả (Likert / Rating / Điểm) --</option>
              {numericQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type.replace('_', ' ')})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Biến phân chia 2 nhóm so sánh (Grouping Variable / Treatment):
            </label>
            <select
              value={groupQid}
              onChange={(e) => setGroupQid(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            >
              <option value="">-- Chọn câu hỏi phân nhóm (Phân khúc / Giới tính / Can thiệp) --</option>
              {groupQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type.replace('_', ' ')})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Custom Group Labels & Grid Options */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Nhãn Tên Nhóm A (Tùy chọn):
            </label>
            <input
              type="text"
              value={groupALabel}
              onChange={(e) => setGroupALabel(e.target.value)}
              placeholder="Ví dụ: Khách VIP / Can thiệp"
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Nhãn Tên Nhóm B (Tùy chọn):
            </label>
            <input
              type="text"
              value={groupBLabel}
              onChange={(e) => setGroupBLabel(e.target.value)}
              placeholder="Ví dụ: Khách Thường / Đối chứng"
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Độ phân giải lưới (Grid Points):
            </label>
            <select
              value={nGridPoints}
              onChange={(e) => setNGridPoints(Number(e.target.value))}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            >
              <option value={30}>30 điểm (Nhanh)</option>
              <option value={50}>50 điểm (Khuyến nghị chuẩn)</option>
              <option value={80}>80 điểm (Độ mịn cao)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Phạm vi lọc phản hồi:
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            >
              <option value="all">Tất cả phản hồi hợp lệ (All)</option>
              <option value="verified_clean">Chỉ phản hồi sạch (Verified Clean)</option>
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={handleRun}
          disabled={loading || !outcomeQid || !groupQid}
          className="w-full sm:w-auto px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang tính tích phân FSD &amp; SSD Davidson &amp; Duclos...
            </>
          ) : (
            'Kiểm định Vượt trội Ngẫu nhiên (FSD &amp; SSD)'
          )}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-300">
          <strong>Lỗi:</strong> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="space-y-6 pt-4 border-t border-slate-100 dark:border-slate-700/60">
          {/* Key Metrics Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Quy mô mẫu (N_A vs N_B)</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100">
                {result.diagnostics.sample_size_a} vs {result.diagnostics.sample_size_b}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Điểm trung bình (Mean)</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100">
                {result.diagnostics.mean_a.toFixed(2)} vs {result.diagnostics.mean_b.toFixed(2)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Hệ số Bất bình đẳng Gini</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100">
                {result.diagnostics.gini_a.toFixed(3)} vs {result.diagnostics.gini_b.toFixed(3)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Kolmogorov-Smirnov D</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100">
                {result.diagnostics.ks_statistic.toFixed(3)} (p={result.diagnostics.ks_p_value.toFixed(3)})
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Vượt trội Bậc 1 (FSD)</span>
              <span className={`text-xs font-bold ${
                result.diagnostics.fsd_dominant_group === 'A' ? 'text-emerald-600 dark:text-emerald-400' :
                result.diagnostics.fsd_dominant_group === 'B' ? 'text-indigo-600 dark:text-indigo-400' :
                'text-amber-500'
              }`}>
                {result.diagnostics.fsd_conclusion}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Vượt trội Bậc 2 (SSD - Né rủi ro)</span>
              <span className={`text-xs font-bold ${
                result.diagnostics.ssd_dominant_group === 'A' ? 'text-emerald-600 dark:text-emerald-400' :
                result.diagnostics.ssd_dominant_group === 'B' ? 'text-indigo-600 dark:text-indigo-400' :
                'text-amber-500'
              }`}>
                {result.diagnostics.ssd_conclusion}
              </span>
            </div>
          </div>

          {/* SVG Scientific Visualization */}
          {result.svg_visualization && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Đồ thị Hàm Phân phối Tích lũy CDF &amp; Đường cong Chênh lệch Tích phân Bậc 2:
              </h4>
              <div
                className="overflow-x-auto p-4 bg-slate-900 rounded-xl border border-slate-800 flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Grid Evaluation Thresholds Table */}
          {result.grid_thresholds && result.grid_thresholds.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Bảng Giá trị Phân phối Tích lũy và Tích phân Bậc 2 theo Ngưỡng Điểm đánh giá (y):
              </h4>
              <div className="overflow-x-auto border border-slate-200 dark:border-slate-700 rounded-lg max-h-56">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-50 dark:bg-slate-700/50 text-slate-700 dark:text-slate-200 font-semibold border-b border-slate-200 dark:border-slate-700 sticky top-0">
                    <tr>
                      <th className="p-2.5">Ngưỡng (y)</th>
                      <th className="p-2.5 text-right">F_A(y)</th>
                      <th className="p-2.5 text-right">F_B(y)</th>
                      <th className="p-2.5 text-right">FSD Chênh lệch (F_B - F_A)</th>
                      <th className="p-2.5 text-right">Tích phân D_A^(2)</th>
                      <th className="p-2.5 text-right">Tích phân D_B^(2)</th>
                      <th className="p-2.5 text-right">SSD Chênh lệch (D_B - D_A)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
                    {result.grid_thresholds.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-700/20">
                        <td className="p-2.5 font-medium text-slate-900 dark:text-white">
                          {row.threshold.toFixed(2)}
                        </td>
                        <td className="p-2.5 text-right font-mono text-emerald-600 dark:text-emerald-400">
                          {row.cdf_a.toFixed(3)}
                        </td>
                        <td className="p-2.5 text-right font-mono text-indigo-600 dark:text-indigo-400">
                          {row.cdf_b.toFixed(3)}
                        </td>
                        <td className={`p-2.5 text-right font-mono font-semibold ${row.fsd_diff_b_minus_a >= 0 ? 'text-emerald-600' : 'text-rose-500'}`}>
                          {row.fsd_diff_b_minus_a >= 0 ? '+' : ''}{row.fsd_diff_b_minus_a.toFixed(3)}
                        </td>
                        <td className="p-2.5 text-right font-mono text-slate-500">
                          {row.d2_integral_a.toFixed(3)}
                        </td>
                        <td className="p-2.5 text-right font-mono text-slate-500">
                          {row.d2_integral_b.toFixed(3)}
                        </td>
                        <td className={`p-2.5 text-right font-mono font-semibold ${row.ssd_diff_b_minus_a >= 0 ? 'text-emerald-600' : 'text-rose-500'}`}>
                          {row.ssd_diff_b_minus_a >= 0 ? '+' : ''}{row.ssd_diff_b_minus_a.toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Narrative Callout */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Báo cáo Thuyết minh Chuẩn APA 7th (Methodological Narrative)
                </span>
                <button
                  type="button"
                  onClick={copyNarrative}
                  className="px-2.5 py-1 text-xs bg-white dark:bg-slate-700 hover:bg-slate-100 border border-slate-200 dark:border-slate-600 rounded text-slate-700 dark:text-slate-300 transition-colors"
                >
                  {copied ? '✓ Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed italic bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
