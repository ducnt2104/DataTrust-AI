import React, { useState } from 'react';
import { MaxDiffResult } from '../types/survey';
import { api } from '../api/client';

interface MaxDiffCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const MaxDiffCard: React.FC<MaxDiffCardProps> = ({ surveyId, questions }) => {
  const [mode, setMode] = useState<'best_worst_pair' | 'multi_items'>('best_worst_pair');
  const [bestQid, setBestQid] = useState<string>('');
  const [worstQid, setWorstQid] = useState<string>('');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MaxDiffResult | null>(null);

  // Single choice questions for Best/Worst selection
  const choiceQuestions = questions.filter(
    (q) => q.question_type === 'single_choice' || q.question_type === 'dropdown'
  );

  // Rating/number/scale questions for multi-item implied MaxDiff
  const ratingQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'rating'
  );

  const toggleItem = (qid: string) => {
    setSelectedItems((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (mode === 'best_worst_pair' && (!bestQid || !worstQid)) {
      setError('Vui lòng chọn cả hai câu hỏi: Lựa chọn Tốt nhất (Best) và Kém nhất (Worst).');
      return;
    }
    if (mode === 'best_worst_pair' && bestQid === worstQid) {
      setError('Câu hỏi Best và Worst phải là hai câu hỏi phân biệt.');
      return;
    }
    if (mode === 'multi_items' && selectedItems.length < 3) {
      setError('Vui lòng chọn tối thiểu 3 câu hỏi thuộc tính để đánh đổi Best-Worst.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runMaxDiff(surveyId, {
        best_question_id: mode === 'best_worst_pair' ? bestQid : undefined,
        worst_question_id: mode === 'best_worst_pair' ? worstQid : undefined,
        item_question_ids: mode === 'multi_items' ? selectedItems : undefined,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình MaxDiff với dữ liệu hiện tại.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích MaxDiff.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
              Best-Worst Scaling Case 1
            </span>
            <span className="text-xs text-slate-400 font-mono">Finn & Louviere 1992; Marley & Louviere 2005</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Đo Lường Khoảng Cách Cực Đại MaxDiff (Best-Worst Scaling)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Triệt tiêu hoàn toàn thiên lệch thang đo (Scale Bias) và hiệu ứng trần (Ceiling Effect) bằng cách buộc người trả lời đánh đổi trực tiếp giữa Best và Worst.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={handleRunAnalysis}
          disabled={loading || (mode === 'best_worst_pair' && (!bestQid || !worstQid)) || (mode === 'multi_items' && selectedItems.length < 3)}
          className="px-5 py-2.5 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white font-medium rounded-lg text-sm transition-all shadow-lg shadow-rose-900/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang Tối Ưu Hóa MaxDiff MNL...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              <span>Ước Lượng Mô Hình MaxDiff</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-6 p-4 bg-slate-950/60 rounded-lg border border-slate-800/80">
        {/* Mode & Scope Selector */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              1. Chế Độ Thu Thập MaxDiff
            </label>
            <div className="flex flex-col gap-2">
              <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                <input
                  type="radio"
                  name="md_mode"
                  checked={mode === 'best_worst_pair'}
                  onChange={() => setMode('best_worst_pair')}
                  className="text-rose-500 focus:ring-0"
                />
                <span>Cặp câu hỏi Best - Worst riêng biệt</span>
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                <input
                  type="radio"
                  name="md_mode"
                  checked={mode === 'multi_items'}
                  onChange={() => setMode('multi_items')}
                  className="text-rose-500 focus:ring-0"
                />
                <span>Đánh đổi từ bộ tiêu chí đánh giá điểm số (M &ge; 3)</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Phạm Vi Dữ Liệu
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setScope('all')}
                className={`flex-1 py-1.5 px-3 rounded text-xs font-medium border transition-all ${
                  scope === 'all'
                    ? 'bg-rose-600 text-white border-rose-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Tất cả mẫu
              </button>
              <button
                onClick={() => setScope('verified_clean')}
                className={`flex-1 py-1.5 px-3 rounded text-xs font-medium border transition-all ${
                  scope === 'verified_clean'
                    ? 'bg-rose-600 text-white border-rose-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Mẫu sạch đã xác thực
              </button>
            </div>
          </div>
        </div>

        {/* Input Controls */}
        <div className="md:col-span-2">
          {mode === 'best_worst_pair' ? (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  2a. Câu Hỏi Chọn Phương Án TỐT NHẤT (Most Preferred / Best)
                </label>
                <select
                  value={bestQid}
                  onChange={(e) => setBestQid(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                >
                  <option value="">-- Chọn câu hỏi Best --</option>
                  {choiceQuestions.map((q) => (
                    <option key={q.id} value={q.id}>
                      {q.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  2b. Câu Hỏi Chọn Phương Án KÉM NHẤT (Least Preferred / Worst)
                </label>
                <select
                  value={worstQid}
                  onChange={(e) => setWorstQid(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                >
                  <option value="">-- Chọn câu hỏi Worst --</option>
                  {choiceQuestions
                    .filter((q) => q.id !== bestQid)
                    .map((q) => (
                      <option key={q.id} value={q.id}>
                        {q.title}
                      </option>
                    ))}
                </select>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  2. Chọn Các Câu Hỏi Thuộc Tính (M &ge; 3)
                </label>
                <button
                  onClick={() => {
                    if (selectedItems.length === ratingQuestions.length) {
                      setSelectedItems([]);
                    } else {
                      setSelectedItems(ratingQuestions.map((q) => q.id));
                    }
                  }}
                  className="text-xs text-rose-400 hover:text-rose-300 underline font-medium"
                >
                  {selectedItems.length === ratingQuestions.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1">
                {ratingQuestions.map((q) => {
                  const isSelected = selectedItems.includes(q.id);
                  return (
                    <div
                      key={q.id}
                      onClick={() => toggleItem(q.id)}
                      className={`p-2.5 rounded-md border text-xs cursor-pointer transition-all flex items-center gap-2 ${
                        isSelected
                          ? 'bg-rose-950/50 border-rose-500/60 text-rose-200'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="rounded border-slate-700 text-rose-500 focus:ring-0 focus:ring-offset-0 bg-slate-800 cursor-pointer"
                      />
                      <span className="truncate">{q.title}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 mb-6 rounded-lg bg-red-950/40 border border-red-500/50 text-red-200 text-sm flex items-center gap-3">
          <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && result.diagnostics && (
        <div className="space-y-6">
          {/* Key Metrics Dashboard */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Tổng Số Nhiệm Vụ (T)</div>
              <div className="text-lg font-bold text-white mt-0.5">{result.diagnostics.n_tasks} Lượt Đánh Đổi</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Số Phương Án (M)</div>
              <div className="text-lg font-bold text-rose-400 mt-0.5">{result.diagnostics.n_items} Thuộc Tính</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">McFadden Pseudo-R²</div>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">
                {(result.diagnostics.mcfadden_pseudo_r2 * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Hàm Log-Likelihood</div>
              <div className="text-lg font-bold text-slate-200 mt-0.5">
                {result.diagnostics.log_likelihood.toFixed(1)}
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Hội Tụ Thuật Toán MNL</div>
              <div className="text-xs font-semibold text-emerald-400 mt-1">
                {result.diagnostics.converged ? '✅ Hội tụ thành công' : '⚠️ Chưa hội tụ tối ưu'}
              </div>
            </div>
          </div>

          {/* SVG Dual-Panel: Preference Share + Best vs Worst Scatter Grid */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Biểu Đồ Thị Phần Ưu Tiên Chuẩn Hóa &amp; Lưới Phân Bổ Best vs Worst
              </h4>
              <div
                className="w-full flex justify-center overflow-x-auto"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Items Breakdown Table */}
          {result.items && result.items.length > 0 && (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 overflow-x-auto">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Bảng Thống Số Điểm Hữu Dụng &amp; Tỷ Lệ Lựa Chọn Best-Worst
              </h4>
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase font-mono">
                  <tr>
                    <th className="py-2.5 px-3">Thứ Hạng</th>
                    <th className="py-2.5 px-3">Tên Thuộc Tính</th>
                    <th className="py-2.5 px-3">Thị Phần Ưu Tiên (P %)</th>
                    <th className="py-2.5 px-3">Độ Hữu Dụng (β)</th>
                    <th className="py-2.5 px-3">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3">Thống Kê Wald (z)</th>
                    <th className="py-2.5 px-3">Tỷ Lệ Best (%)</th>
                    <th className="py-2.5 px-3">Tỷ Lệ Worst (%)</th>
                    <th className="py-2.5 px-3">Điểm Đếm (B-W)/A</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.items.map((it, idx) => (
                    <tr key={it.item_id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-rose-400">#{idx + 1}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{it.item_name}</td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-rose-300">{it.preference_share_pct}%</span>
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-rose-400 rounded-full"
                              style={{ width: `${Math.min(100, it.preference_share_pct)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-200">
                        {it.raw_utility >= 0 ? `+${it.raw_utility.toFixed(3)}` : it.raw_utility.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{it.std_error.toFixed(3)}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">{it.z_statistic.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-400 font-semibold">{it.best_rate_pct}%</td>
                      <td className="py-2.5 px-3 font-mono text-rose-400">{it.worst_rate_pct}%</td>
                      <td className="py-2.5 px-3 font-mono">
                        <span className={it.counting_score >= 0 ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                          {it.counting_score >= 0 ? `+${it.counting_score.toFixed(3)}` : it.counting_score.toFixed(3)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Academic APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-950/90 rounded-lg border border-slate-800 text-slate-300 text-xs leading-relaxed space-y-2">
              <div className="flex items-center gap-2 text-rose-400 font-semibold mb-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span>Báo Cáo Học Thuật Chuẩn APA 7th Edition (MaxDiff Best-Worst Scaling)</span>
              </div>
              <p className="whitespace-pre-line">{result.apa_narrative}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
