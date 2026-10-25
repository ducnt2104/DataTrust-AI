import React, { useState } from 'react';
import { api } from '../api/client';
import { GTheoryAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface GTheoryCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const GTheoryCard: React.FC<GTheoryCardProps> = ({
  surveyId,
  questions
}) => {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [raterQId, setRaterQId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GTheoryAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  // Lọc các câu hỏi đánh giá dạng rating, scale, number
  const ratingOrNumericQuestions = questions.filter(q =>
    ['rating', 'scale', 'linear_scale', 'number', 'nps'].includes(q.question_type)
  );

  const toggleItem = (qid: string) => {
    setSelectedItems(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const selectAllRatingItems = () => {
    setSelectedItems(ratingOrNumericQuestions.map(q => q.id));
  };

  const clearSelectedItems = () => {
    setSelectedItems([]);
  };

  const handleRunAnalysis = async () => {
    if (selectedItems.length < 2) {
      setError('Vui lòng chọn ít nhất 2 câu hỏi (items) để phân rã phương sai đo lường G-Theory.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await api.runGTheoryAnalysis(surveyId, {
        item_question_ids: selectedItems,
        rater_question_id: raterQId ? raterQId : null,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể thực thi phân tích G-Theory.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi hệ thống khi phân tích G-Theory.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2500);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg font-bold text-slate-800">
              Lý thuyết Khái quát hóa Đo lường (G-Theory: G-Study & D-Study)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Psychometrics
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
              Cronbach et al. 1972 • Brennan 2001
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Vượt qua giới hạn của Cronbach's Alpha bằng cách phân rã phương sai đo lường thành các nguồn độc lập
            (Cá thể p, Câu hỏi i, Tương tác pi,e) trong G-Study, đồng thời dự báo số lượng câu hỏi tối ưu qua D-Study.
          </p>
        </div>
      </div>

      {/* Item Selection & Controls */}
      <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Chọn Các Câu Hỏi Đánh Giá Thang Đo (Items Facet) *
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAllRatingItems}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              Chọn tất cả ({ratingOrNumericQuestions.length})
            </button>
            <span className="text-slate-300">|</span>
            <button
              type="button"
              onClick={clearSelectedItems}
              className="text-xs text-slate-500 hover:text-slate-700"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-48 overflow-y-auto p-1">
          {ratingOrNumericQuestions.map(q => {
            const isChecked = selectedItems.includes(q.id);
            return (
              <label
                key={q.id}
                onClick={() => toggleItem(q.id)}
                className={`flex items-start gap-2 p-2 rounded border cursor-pointer transition-colors text-xs ${
                  isChecked
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-950 font-medium'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => {}}
                  className="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="truncate" title={q.title}>
                  {q.title}
                </span>
              </label>
            );
          })}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-200">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Diện Mạo Người Đánh Giá / Điều Tra Viên (Rater Facet - Tùy chọn)
            </label>
            <select
              value={raterQId}
              onChange={e => setRaterQId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Không phân rã rater (Thiết kế p x i) --</option>
              {questions
                .filter(q => !selectedItems.includes(q.id))
                .map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title}
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Phạm Vi Lọc Phản Hồi
            </label>
            <select
              value={scope}
              onChange={e => setScope(e.target.value as any)}
              className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="all">Toàn bộ phản hồi (All)</option>
              <option value="verified_clean">Chỉ mẫu sạch (Quality ≥ 0.70)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang phân rã phương sai G-Study & D-Study...</span>
            </>
          ) : (
            <>
              <span>Phân Rã Phương Sai G-Study & Tối Ưu D-Study</span>
            </>
          )}
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
          <span className="font-bold">Lỗi:</span> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6 pt-2">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Thiết kế Đo lường</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                {result.design_type}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                N = {result.sample_size} người • K = {result.items_count} câu hỏi
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Phương sai Chân trị (Universe σ²_p)</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                {result.current_design_metrics?.universe_score_variance.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Chiếm {result.variance_components?.[0]?.percent.toFixed(1)}% tổng phương sai
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200">
              <span className="text-xs text-indigo-700 font-bold uppercase tracking-wider">
                Hệ số G (Relative Eρ²)
              </span>
              <div className="text-2xl font-black text-indigo-950 mt-1">
                {result.current_design_metrics?.g_coefficient_relative.toFixed(3)}
              </div>
              <div className="text-xs text-indigo-700 mt-1 font-medium">
                {result.current_design_metrics && result.current_design_metrics.g_coefficient_relative >= 0.80
                  ? 'Đạt chuẩn so sánh tương đối (≥ .80)'
                  : 'Cần tăng câu hỏi (< .80)'}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
              <span className="text-xs text-emerald-800 font-bold uppercase tracking-wider">
                Hệ số Phi (Absolute Φ)
              </span>
              <div className="text-2xl font-black text-emerald-950 mt-1">
                {result.current_design_metrics?.phi_coefficient_absolute.toFixed(3)}
              </div>
              <div className="text-xs text-emerald-800 mt-1 font-medium">
                {result.current_design_metrics && result.current_design_metrics.phi_coefficient_absolute >= 0.80
                  ? 'Đạt chuẩn tiêu chí tuyệt đối (≥ .80)'
                  : 'Tiêu chí tuyệt đối cần tối ưu (< .80)'}
              </div>
            </div>
          </div>

          {/* Vector SVG Dual Panel Chart */}
          {result.svg_chart && (
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-white rounded-lg border border-slate-200"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* G-Study ANOVA Table */}
          {result.variance_components && (
            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Bảng Phân Rã Thành Phần Phương Sai G-Study (ANOVA Variance Components)
                </span>
                <span className="text-xs text-slate-500">Brennan (2001) Formulation</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold">Nguồn Phương Sai (Source)</th>
                      <th className="px-3 py-2 text-left font-semibold">Ý Nghĩa Đo Lường</th>
                      <th className="px-3 py-2 text-right font-semibold">Bậc Tự Do (df)</th>
                      <th className="px-3 py-2 text-right font-semibold">Tổng Bình Phương (SS)</th>
                      <th className="px-3 py-2 text-right font-semibold">Mean Square (MS)</th>
                      <th className="px-3 py-2 text-right font-semibold">Ước Lượng σ²</th>
                      <th className="px-3 py-2 text-right font-semibold">Tỷ Lệ (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.variance_components.map(vc => (
                      <tr key={vc.source} className="hover:bg-slate-50">
                        <td className="px-3 py-2.5 font-bold text-slate-800">{vc.source}</td>
                        <td className="px-3 py-2.5 text-slate-600">{vc.label}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">{vc.df}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">{vc.ss.toFixed(3)}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">{vc.ms.toFixed(3)}</td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold text-indigo-900">
                          {vc.variance.toFixed(4)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold text-emerald-700">
                          {vc.percent.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* D-Study Decision Optimization Table */}
          {result.d_study_projections && (
            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Nghiên Cứu Quyết Định D-Study (Kịch Bản Tối Ưu Hóa Số Lượng Câu Hỏi)
                </span>
                <span className="text-xs text-slate-500">Ngưỡng chuẩn vàng: Eρ² ≥ 0.80 & Φ ≥ 0.80</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      <th className="px-3 py-2 text-center font-semibold">Số Câu Hỏi (n_i')</th>
                      <th className="px-3 py-2 text-right font-semibold">Phương Sai Sai Số Tương Đối (σ²_δ)</th>
                      <th className="px-3 py-2 text-right font-semibold">Phương Sai Sai Số Tuyệt Đối (σ²_Δ)</th>
                      <th className="px-3 py-2 text-right font-semibold">SEM Tương Đối</th>
                      <th className="px-3 py-2 text-right font-semibold">Hệ Số G (Eρ²)</th>
                      <th className="px-3 py-2 text-right font-semibold">Hệ Số Phi (Φ)</th>
                      <th className="px-3 py-2 text-center font-semibold">Khuyến Nghị Thiết Kế</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.d_study_projections.map(row => (
                      <tr
                        key={row.n_items}
                        className={`hover:bg-slate-50 ${
                          row.n_items === result.items_count ? 'bg-indigo-50/50 font-semibold' : ''
                        }`}
                      >
                        <td className="px-3 py-2.5 text-center font-mono">
                          {row.n_items} câu {row.n_items === result.items_count && '(Hiện tại)'}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">{row.relative_error_var.toFixed(4)}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">{row.absolute_error_var.toFixed(4)}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">{row.sem_relative.toFixed(3)}</td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold text-indigo-900">
                          {row.g_coefficient.toFixed(3)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold text-emerald-800">
                          {row.phi_coefficient.toFixed(3)}
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          {row.is_acceptable_norm && row.is_acceptable_criterion ? (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                              Tối ưu toàn diện (≥ .80)
                            </span>
                          ) : row.is_acceptable_norm ? (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-100 text-indigo-800">
                              Đạt chuẩn tương đối
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-800">
                              Chưa đạt chuẩn ({'<'} .80)
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Academic Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Thuyết Minh Báo Cáo Học Thuật (Định dạng APA 7th Edition)
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-slate-900 bg-white border border-slate-200 rounded hover:bg-slate-50 transition-colors shadow-2xs"
                >
                  {copiedNarrative ? '✓ Đã sao chép' : 'Sao chép văn bản'}
                </button>
              </div>
              <div className="p-3 bg-white rounded-lg border border-slate-200 text-slate-700 font-serif text-sm leading-relaxed whitespace-pre-line">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
