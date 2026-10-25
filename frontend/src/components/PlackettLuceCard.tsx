import React, { useState } from 'react';
import { PlackettLuceResult } from '../types/survey';
import { api } from '../api/client';

interface PlackettLuceCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const PlackettLuceCard: React.FC<PlackettLuceCardProps> = ({ surveyId, questions }) => {
  const [mode, setMode] = useState<'ranking_q' | 'multi_items'>('ranking_q');
  const [rankingQid, setRankingQid] = useState<string>('');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlackettLuceResult | null>(null);

  // Dedicated ranking questions
  const rankingQuestions = questions.filter((q) => q.question_type === 'ranking');

  // Rating/number/scale questions for multi-item implied ranking
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
    if (mode === 'ranking_q' && !rankingQid) {
      setError('Vui lòng chọn câu hỏi xếp hạng thứ tự.');
      return;
    }
    if (mode === 'multi_items' && selectedItems.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 câu hỏi đánh giá thuộc tính để suy diễn thứ bậc xếp hạng.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runPlackettLuce(surveyId, {
        ranking_question_id: mode === 'ranking_q' ? rankingQid : undefined,
        item_question_ids: mode === 'multi_items' ? selectedItems : undefined,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình Plackett-Luce với dữ liệu hiện tại.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích Plackett-Luce.');
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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-500/20 text-violet-400 border border-violet-500/30">
              Rank-Ordered Choice Logit
            </span>
            <span className="text-xs text-slate-400 font-mono">Luce 1959; Plackett 1975; Hunter 2004 MM</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Mô Hình Lựa Chọn Xếp Hạng Plackett-Luce (Rank-Ordered Choice Model)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Ước lượng độ hữu dụng tiềm ẩn (Latent Worth) và xác suất thắng đối đầu trực diện (Head-to-Head Win Probability) từ dữ liệu xếp hạng khảo sát.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={handleRunAnalysis}
          disabled={loading || (mode === 'ranking_q' && !rankingQid) || (mode === 'multi_items' && selectedItems.length < 2)}
          className="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium rounded-lg text-sm transition-all shadow-lg shadow-violet-900/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang Tối Ưu Hóa MM...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
              </svg>
              <span>Ước Lượng Mô Hình Plackett-Luce</span>
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
              1. Chế Độ Dữ Liệu Xếp Hạng
            </label>
            <div className="flex flex-col gap-2">
              <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                <input
                  type="radio"
                  name="pl_mode"
                  checked={mode === 'ranking_q'}
                  onChange={() => setMode('ranking_q')}
                  className="text-violet-500 focus:ring-0"
                />
                <span>Câu hỏi xếp hạng thứ tự (Ranking Question)</span>
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                <input
                  type="radio"
                  name="pl_mode"
                  checked={mode === 'multi_items'}
                  onChange={() => setMode('multi_items')}
                  className="text-violet-500 focus:ring-0"
                />
                <span>Đánh giá điểm số nhiều tiêu chí (Implied Ranking)</span>
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
                    ? 'bg-violet-600 text-white border-violet-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Tất cả mẫu
              </button>
              <button
                onClick={() => setScope('verified_clean')}
                className={`flex-1 py-1.5 px-3 rounded text-xs font-medium border transition-all ${
                  scope === 'verified_clean'
                    ? 'bg-violet-600 text-white border-violet-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Mẫu sạch đã xác thực
              </button>
            </div>
          </div>
        </div>

        {/* Input Selector based on Mode */}
        <div className="md:col-span-2">
          {mode === 'ranking_q' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                2. Chọn Câu Hỏi Xếp Hạng (Ranking Question)
              </label>
              {rankingQuestions.length > 0 ? (
                <select
                  value={rankingQid}
                  onChange={(e) => setRankingQid(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500"
                >
                  <option value="">-- Chọn câu hỏi xếp hạng --</option>
                  {rankingQuestions.map((q) => (
                    <option key={q.id} value={q.id}>
                      {q.title}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="p-3 bg-slate-900 border border-slate-800 rounded text-xs text-amber-400">
                  Chưa có câu hỏi kiểu 'ranking' trong khảo sát này. Bạn có thể chuyển sang chế độ "Đánh giá điểm số nhiều tiêu chí" ở cột bên trái để phân tích các câu hỏi thang điểm Likert/Rating.
                </div>
              )}
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  2. Chọn Các Câu Hỏi Đánh Giá Thuộc Tính (M &ge; 2)
                </label>
                <button
                  onClick={() => {
                    if (selectedItems.length === ratingQuestions.length) {
                      setSelectedItems([]);
                    } else {
                      setSelectedItems(ratingQuestions.map((q) => q.id));
                    }
                  }}
                  className="text-xs text-violet-400 hover:text-violet-300 underline font-medium"
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
                          ? 'bg-violet-950/50 border-violet-500/60 text-violet-200'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="rounded border-slate-700 text-violet-500 focus:ring-0 focus:ring-offset-0 bg-slate-800 cursor-pointer"
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
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Cỡ Mẫu Xếp Hạng (N)</div>
              <div className="text-lg font-bold text-white mt-0.5">{result.diagnostics.sample_size}</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Số Phương Án (M)</div>
              <div className="text-lg font-bold text-violet-400 mt-0.5">{result.diagnostics.n_items} Phương Án</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">McFadden Pseudo-R²</div>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">
                {(result.diagnostics.mcfadden_pseudo_r2 * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Kiểm Định LR Chi²</div>
              <div className="text-lg font-bold text-slate-200 mt-0.5">
                {result.diagnostics.lr_chi_square.toFixed(1)}
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Ý Nghĩa Mô Hình (p)</div>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">
                {result.diagnostics.p_value < 0.001 ? '< .001' : result.diagnostics.p_value.toFixed(4)}
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Hội Tụ Thuật Toán MM</div>
              <div className="text-xs font-semibold text-emerald-400 mt-1">
                {result.diagnostics.converged ? '✅ Hội tụ toàn cục' : '⚠️ Cần thêm vòng lặp'}
              </div>
            </div>
          </div>

          {/* SVG Dual-Panel: Latent Worth + Pairwise Win Heatmap */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Biểu Đồ Giá Trị Tiềm Ẩn &amp; Ma Trận Xác Suất Thắng Đối Đầu (Head-to-Head)
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
                Bảng Thông Số Giá Trị Tiềm Ẩn &amp; Khoảng Tin Cậy 95% CI
              </h4>
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase font-mono">
                  <tr>
                    <th className="py-2.5 px-3">Thứ Hạng</th>
                    <th className="py-2.5 px-3">Tên Phương Án</th>
                    <th className="py-2.5 px-3">Tỷ Trọng Tiềm Ẩn (w %)</th>
                    <th className="py-2.5 px-3">Khoảng Tin Cậy 95% CI</th>
                    <th className="py-2.5 px-3">Hữu Dụng Log-Worth (γ)</th>
                    <th className="py-2.5 px-3">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3">Thống Kê Wald (z)</th>
                    <th className="py-2.5 px-3">Giá Trị p</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.items.map((it, idx) => (
                    <tr key={it.item_id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-violet-400">#{idx + 1}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{it.item_name}</td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-violet-300">{it.worth_percentage}%</span>
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-violet-400 rounded-full"
                              style={{ width: `${Math.min(100, it.worth_percentage)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        [{it.ci_lower.toFixed(1)}% — {it.ci_upper.toFixed(1)}%]
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-200">
                        {it.utility_log_worth >= 0 ? `+${it.utility_log_worth.toFixed(3)}` : it.utility_log_worth.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{it.std_error.toFixed(3)}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">{it.z_statistic.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-mono">
                        <span className={it.p_value < 0.05 ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                          {it.p_value < 0.001 ? '< .001' : it.p_value.toFixed(4)}
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
              <div className="flex items-center gap-2 text-violet-400 font-semibold mb-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span>Báo Cáo Học Thuật Chuẩn APA 7th Edition (Plackett-Luce Choice Model)</span>
              </div>
              <p className="whitespace-pre-line">{result.apa_narrative}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
