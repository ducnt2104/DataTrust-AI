import React, { useState } from 'react';
import { FiniteMixtureRaschResult } from '../types/survey';
import { api } from '../api/client';

interface FiniteMixtureRaschCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const FiniteMixtureRaschCard: React.FC<FiniteMixtureRaschCardProps> = ({ surveyId, questions }) => {
  const [selectedQids, setSelectedQids] = useState<string[]>([]);
  const [nClasses, setNClasses] = useState<number>(2);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FiniteMixtureRaschResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Eligible item questions (Likert, linear_scale, rating, number, single_choice)
  const eligibleQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'single_choice'
  );

  const toggleQuestion = (id: string) => {
    setSelectedQids((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    setSelectedQids(eligibleQuestions.map((q) => q.id));
  };

  const clearAll = () => {
    setSelectedQids([]);
  };

  const handleRun = async () => {
    if (selectedQids.length < 3) {
      setError('Vui lòng chọn tối thiểu 3 câu hỏi để ước lượng mô hình Rasch hỗn hợp.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runFiniteMixtureRasch(surveyId, {
        question_ids: selectedQids,
        n_classes: nClasses,
        scope
      });

      if (res.status === 'error' || res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_ITEMS') {
        setError(res.message || 'Ước lượng mô hình Rasch hỗn hợp thất bại.');
      } else {
        setResult(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi kết nối máy chủ khi tính toán FMRM.');
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
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-teal-100 text-teal-800 dark:bg-teal-900/50 dark:text-teal-300">
              Rost 1990 &bull; von Davier &amp; Rost 2007 &bull; Glas 2010
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Latent Class Item Response Theory (Mixture IRT)
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            Mô Hình Rasch Hỗn Hợp Hữu Hạn (Finite Mixture Rasch Models - FMRM)
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Phân rã tính không đồng nhất tiềm ẩn (Unobserved Heterogeneity) và thiên lệch chức năng câu hỏi (DIF) giữa các phân lớp người trả lời.
          </p>
        </div>
      </div>

      {/* Selectors & Controls */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
            Chọn các câu hỏi thang đo đánh giá (Tối thiểu 3 câu) *
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAll}
              className="text-xs text-teal-600 dark:text-teal-400 hover:underline font-medium"
            >
              Chọn tất cả ({eligibleQuestions.length})
            </button>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <button
              type="button"
              onClick={clearAll}
              className="text-xs text-slate-500 hover:underline font-medium"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        {/* Question checklist */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-48 overflow-y-auto p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40">
          {eligibleQuestions.map((q) => {
            const isChecked = selectedQids.includes(q.id);
            return (
              <label
                key={q.id}
                className={`flex items-start gap-2.5 p-2 rounded cursor-pointer transition text-xs ${
                  isChecked
                    ? 'bg-teal-50/80 dark:bg-teal-950/40 text-teal-900 dark:text-teal-200 font-medium'
                    : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleQuestion(q.id)}
                  className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span className="line-clamp-2">{q.title}</span>
              </label>
            );
          })}
        </div>

        {/* Hyperparameters: n_classes and scope */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Số lượng Phân lớp Tiềm ẩn ($G$)
            </label>
            <select
              value={nClasses}
              onChange={(e) => setNClasses(parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value={2}>2 Phân lớp (G = 2) - Chuẩn định / Thích ứng</option>
              <option value={3}>3 Phân lớp (G = 3) - Khắt khe / Trung dung / Dễ dãi</option>
              <option value={4}>4 Phân lớp (G = 4) - Phân hóa chuyên sâu</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Phạm vi Lọc Dữ liệu
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="all">Toàn bộ mẫu khảo sát (All)</option>
              <option value="verified_clean">Chỉ mẫu sạch đã kiểm định (Verified Clean)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Run Action Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleRun}
          disabled={loading || selectedQids.length < 3}
          className="px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium text-sm transition shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang ước lượng EM Mixture Rasch...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Phân tách Phân lớp Tiềm ẩn (FMRM EM)
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="space-y-6 pt-4 border-t border-slate-100 dark:border-slate-700/60">
          {/* Key Metric Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-teal-50 dark:bg-teal-950/30 border border-teal-200/80 dark:border-teal-800/60">
              <span className="text-xs text-teal-700 dark:text-teal-400 font-medium">Chỉ số Entropy</span>
              <p className="text-lg font-bold text-teal-800 dark:text-teal-200 mt-0.5">
                {result.diagnostics.entropy.toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Bayesian BIC</span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                {result.diagnostics.bic.toFixed(1)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Log-Likelihood</span>
              <p className="text-base font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
                {result.diagnostics.log_likelihood.toFixed(1)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Quy mô mẫu N</span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                {result.diagnostics.sample_size_total} ({result.diagnostics.sample_size} inf)
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Độ lệch DIF Cực đại</span>
              <p className="text-base font-bold text-amber-600 dark:text-amber-400 mt-0.5">
                &Delta;&beta; = {result.diagnostics.top_shift_magnitude.toFixed(2)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Chất lượng Phân tách</span>
              <p className={`text-base font-bold mt-0.5 ${result.diagnostics.is_well_separated ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400'}`}>
                {result.diagnostics.is_well_separated ? 'Rõ nét (>0.70)' : 'Trung bình'}
              </p>
            </div>
          </div>

          {/* Class Proportions Cards */}
          {result.class_proportions && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {result.class_proportions.map((cp) => (
                <div
                  key={cp.class_index}
                  className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      {cp.class_name}
                    </span>
                    <span className="text-xs font-mono font-bold text-teal-600 dark:text-teal-400">
                      {(cp.proportion * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 mt-2 overflow-hidden">
                    <div
                      className="bg-teal-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, cp.proportion * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Items Parameters by Class Table */}
          {result.items_parameters && (
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-800/80 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-4 py-3">Câu hỏi Khảo sát (Item)</th>
                    <th className="px-4 py-3">Độ khó Phân lớp 1 (&beta;1)</th>
                    <th className="px-4 py-3">Độ khó Phân lớp 2 (&beta;2)</th>
                    {result.diagnostics.n_classes >= 3 && <th className="px-4 py-3">Độ khó Phân lớp 3 (&beta;3)</th>}
                    {result.diagnostics.n_classes >= 4 && <th className="px-4 py-3">Độ khó Phân lớp 4 (&beta;4)</th>}
                    <th className="px-4 py-3">Độ dịch chuyển DIF (&Delta;&beta;)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {result.items_parameters.map((it, idx) => (
                    <tr key={idx} className={it.max_diff === result.diagnostics?.top_shift_magnitude ? 'bg-amber-50/50 dark:bg-amber-950/20 font-medium' : ''}>
                      <td className="px-4 py-2.5 font-medium">{it.item_title}</td>
                      <td className="px-4 py-2.5 font-mono">{it.beta_class_1 !== undefined ? (it.beta_class_1 >= 0 ? `+${it.beta_class_1.toFixed(3)}` : it.beta_class_1.toFixed(3)) : '-'}</td>
                      <td className="px-4 py-2.5 font-mono">{it.beta_class_2 !== undefined ? (it.beta_class_2 >= 0 ? `+${it.beta_class_2.toFixed(3)}` : it.beta_class_2.toFixed(3)) : '-'}</td>
                      {result.diagnostics?.n_classes && result.diagnostics.n_classes >= 3 && (
                        <td className="px-4 py-2.5 font-mono">{it.beta_class_3 !== undefined ? (it.beta_class_3 >= 0 ? `+${it.beta_class_3.toFixed(3)}` : it.beta_class_3.toFixed(3)) : '-'}</td>
                      )}
                      {result.diagnostics?.n_classes && result.diagnostics.n_classes >= 4 && (
                        <td className="px-4 py-2.5 font-mono">{it.beta_class_4 !== undefined ? (it.beta_class_4 >= 0 ? `+${it.beta_class_4.toFixed(3)}` : it.beta_class_4.toFixed(3)) : '-'}</td>
                      )}
                      <td className="px-4 py-2.5 font-mono font-semibold text-amber-600 dark:text-amber-400">
                        {it.max_diff.toFixed(3)}
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
                Đồ thị Khoa học: Quỹ đạo Độ khó Phân lớp &amp; Phổ Phân rã Entropy
              </h4>
              <div
                className="w-full overflow-x-auto rounded-lg bg-slate-900 p-2 shadow-inner flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                  Bản tường trình Học thuật chuẩn APA 7th (Finite Mixture Rasch Model)
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
