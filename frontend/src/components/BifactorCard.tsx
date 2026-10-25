import React, { useState } from 'react';
import { api } from '../api/client';
import { BifactorAnalysisResult, BifactorSubscaleInput } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface BifactorCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const BifactorCard: React.FC<BifactorCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const [subscales, setSubscales] = useState<BifactorSubscaleInput[]>([
    { subscale_name: 'Tiểu thang đo 1', question_ids: [] },
    { subscale_name: 'Tiểu thang đo 2', question_ids: [] }
  ]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BifactorAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const handleAddSubscale = () => {
    setSubscales([
      ...subscales,
      { subscale_name: `Tiểu thang đo ${subscales.length + 1}`, question_ids: [] }
    ]);
  };

  const handleRemoveSubscale = (index: number) => {
    if (subscales.length <= 2) return;
    setSubscales(subscales.filter((_, i) => i !== index));
  };

  const handleSubscaleNameChange = (index: number, name: string) => {
    const updated = [...subscales];
    updated[index].subscale_name = name;
    setSubscales(updated);
  };

  const handleToggleItemInSubscale = (subscaleIndex: number, qId: string) => {
    const updated = [...subscales];
    const currentQIds = updated[subscaleIndex].question_ids;
    if (currentQIds.includes(qId)) {
      updated[subscaleIndex].question_ids = currentQIds.filter(id => id !== qId);
    } else {
      // Remove from any other subscale first to keep partition disjoint
      updated.forEach((sub, sIdx) => {
        if (sIdx !== subscaleIndex) {
          sub.question_ids = sub.question_ids.filter(id => id !== qId);
        }
      });
      updated[subscaleIndex].question_ids = [...currentQIds, qId];
    }
    setSubscales(updated);
  };

  const handleRunAnalysis = async () => {
    // Validation
    const emptySubscales = subscales.filter(s => s.question_ids.length === 0);
    if (emptySubscales.length > 0) {
      setError(`Tiểu thang đo "${emptySubscales[0].subscale_name}" chưa được gán câu hỏi nào.`);
      return;
    }

    const totalSelected = subscales.reduce((acc, s) => acc + s.question_ids.length, 0);
    if (totalSelected < 4) {
      setError('Cần chọn tổng cộng tối thiểu 4 câu hỏi trên toàn bộ các tiểu thang đo.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await api.runBifactorAnalysis(surveyId, {
        subscales,
        scope
      });

      setResult(res);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không đủ dữ liệu phản hồi hợp lệ để phân tích Bifactor.');
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích mô hình Bifactor.');
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
      <div className="border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2">
          <span className="p-2 bg-purple-50 text-purple-600 rounded-lg font-bold text-sm">
            BIFACTOR
          </span>
          <div>
            <h3 className="text-lg font-bold text-slate-800">
              Bifactor Psychometric Modeling & Omega Hierarchical (ω_h)
            </h3>
            <p className="text-xs text-slate-500">
              Phân rã Mô hình Trực giao Bifactor, kiểm định tính Đơn chiều Thực chất (Essential Unidimensionality), hệ số Omega Phân cấp (ω_h) & Tỷ lệ Phương sai Chung (ECV) theo Reise (2012) & Rodriguez et al. (2016).
            </p>
          </div>
        </div>
      </div>

      {/* Subscale Configuration Builder */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
            Cấu hình Phân bổ Các Tiểu thang đo (Subscale Mapping)
          </span>
          <button
            type="button"
            onClick={handleAddSubscale}
            className="text-xs px-2.5 py-1 bg-purple-50 text-purple-700 hover:bg-purple-100 font-semibold rounded-lg transition-colors border border-purple-200 flex items-center gap-1"
          >
            <span>+ Thêm tiểu thang đo</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {subscales.map((sub, sIdx) => (
            <div key={sIdx} className="p-3.5 border border-slate-200 rounded-xl bg-slate-50/50 space-y-2.5">
              <div className="flex items-center justify-between gap-2">
                <input
                  type="text"
                  value={sub.subscale_name}
                  onChange={e => handleSubscaleNameChange(sIdx, e.target.value)}
                  className="text-xs font-bold text-slate-800 bg-white border border-slate-200 rounded-md px-2.5 py-1 flex-1 focus:ring-1 focus:ring-purple-500 focus:outline-none"
                />
                {subscales.length > 2 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveSubscale(sIdx)}
                    className="text-xs text-rose-500 hover:text-rose-700 font-bold px-1.5 py-0.5"
                  >
                    ✕ Xóa
                  </button>
                )}
              </div>

              <div className="text-[11px] text-slate-500">
                Chọn các câu hỏi thuộc tiểu thang đo này ({sub.question_ids.length} đã chọn):
              </div>

              <div className="max-h-32 overflow-y-auto border border-slate-200 rounded-lg p-2 bg-white space-y-1">
                {numericQuestions.map(q => {
                  const isChecked = sub.question_ids.includes(q.id);
                  return (
                    <label
                      key={q.id}
                      className="flex items-center gap-2 text-xs text-slate-700 hover:bg-slate-50 p-1 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggleItemInSubscale(sIdx, q.id)}
                        className="rounded text-purple-600 focus:ring-purple-500"
                      />
                      <span className="truncate">{q.title}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scope & Action Button */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-2">
        <div className="flex items-center gap-2 text-xs text-slate-600 w-full md:w-auto">
          <span>Phạm vi:</span>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as 'all' | 'verified_clean')}
            className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 focus:bg-white"
          >
            <option value="all">Toàn bộ mẫu khảo sát</option>
            <option value="verified_clean">Chỉ mẫu đã kiểm định hợp lệ</option>
          </select>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="w-full md:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold text-sm rounded-lg transition-colors shadow-sm disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Đang tính toán mô hình Bifactor Schmid-Leiman...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
              </svg>
              <span>Phân tích Mô hình Bifactor (ω_h & ECV)</span>
            </>
          )}
        </button>
      </div>

      {/* Error notification */}
      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
          <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Recommendation Banner */}
          {result.recommendation && (
            <div
              className={`p-4 rounded-xl border flex items-start gap-3 ${
                result.is_essentially_unidimensional
                  ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                  : 'bg-amber-50/70 border-amber-200 text-amber-900'
              }`}
            >
              <div
                className={`p-1.5 rounded-lg font-bold text-xs ${
                  result.is_essentially_unidimensional ? 'bg-emerald-200 text-emerald-800' : 'bg-amber-200 text-amber-800'
                }`}
              >
                {result.is_essentially_unidimensional ? 'ĐƠN CHIỀU (UNIDIMENSIONAL)' : 'ĐA CHIỀU (MULTIDIMENSIONAL)'}
              </div>
              <div className="text-xs font-medium leading-relaxed">
                {result.recommendation}
              </div>
            </div>
          )}

          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-purple-50/50 border border-purple-200 rounded-xl">
              <span className="text-xs text-purple-800 font-medium">Omega Phân cấp (ω_h)</span>
              <div className="text-xl font-bold text-purple-700 mt-1">
                {result.omega_hierarchical !== undefined ? result.omega_hierarchical.toFixed(3) : '--'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  (result.omega_hierarchical || 0) >= 0.80 ? 'text-emerald-600' : 'text-amber-600'
                }`}
              >
                {(result.omega_hierarchical || 0) >= 0.80 ? 'Vượt chuẩn (≥ 0.80)' : 'Dưới ngưỡng (< 0.80)'}
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Phương sai Chung (ECV)</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.explained_common_variance !== undefined
                  ? `${(result.explained_common_variance * 100).toFixed(1)}%`
                  : '--'}
              </div>
              <span className="text-[11px] text-slate-500">
                Tỷ lệ biến thiên do G giải thích
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Tương quan Thuần (PUC)</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.percent_uncontaminated_correlations !== undefined
                  ? `${(result.percent_uncontaminated_correlations * 100).toFixed(1)}%`
                  : '--'}
              </div>
              <span className="text-[11px] text-slate-500">
                Tương quan giữa các tiểu thang
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Độ tin cậy Tổng thể (ω_total)</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.omega_total !== undefined ? result.omega_total.toFixed(3) : '--'}
              </div>
              <span className="text-[11px] text-slate-500">
                Gồm cả nhân tố G và tiểu thang
              </span>
            </div>
          </div>

          {/* Bifactor Vector SVG Diagram */}
          {result.svg_chart && (
            <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Sơ đồ Cấu trúc Phân rã Trực giao Bifactor (Schmid-Leiman Decomposition)
                </span>
                <span className="text-[11px] text-slate-400">
                  Nhân tố chung G (Tím) phân tách độc lập với các Tiểu thang đo S_k
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Subscale Viability Table */}
          {result.subscale_metrics && result.subscale_metrics.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Bảng Đánh giá Tính Độc lập của Từng Tiểu thang đo (Subscale Viability)
              </span>
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Tiểu thang đo (Subscale)</th>
                      <th className="p-2.5">Số mục (Items)</th>
                      <th className="p-2.5">Độ tin cậy thô (ω_s)</th>
                      <th className="p-2.5">Độ tin cậy độc lập (ω_hs)</th>
                      <th className="p-2.5">Khả năng báo cáo độc lập</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.subscale_metrics.map((s, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="p-2.5 font-bold text-slate-800">{s.subscale}</td>
                        <td className="p-2.5 text-slate-600">{s.item_count}</td>
                        <td className="p-2.5 text-slate-700">{s.omega_subscale_total.toFixed(3)}</td>
                        <td className="p-2.5 font-bold text-purple-700">
                          {s.omega_hierarchical_subscale.toFixed(3)}
                        </td>
                        <td className="p-2.5">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              s.viable_as_independent_scale
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {s.viable_as_independent_scale
                              ? 'Có giá trị độc lập (ω_hs ≥ 0.50)'
                              : 'Bị chi phối bởi G (ω_hs < 0.50)'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Item-Level Diagnostics Table */}
          {result.item_diagnostics && result.item_diagnostics.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Bảng Tải trọng Từng Mục & Chỉ số I-ECV (Item-level Explained Common Variance)
              </span>
              <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold sticky top-0 border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Câu hỏi / Mục</th>
                      <th className="p-2.5">Tiểu thang</th>
                      <th className="p-2.5">Tải trọng G (λ_G)</th>
                      <th className="p-2.5">Tải trọng Nhóm (λ_S)</th>
                      <th className="p-2.5">Phương sai sai số (u²)</th>
                      <th className="p-2.5">I-ECV</th>
                      <th className="p-2.5">Trụ cột G (Anchor)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.item_diagnostics.map((it, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="p-2.5 font-medium text-slate-800">{it.label}</td>
                        <td className="p-2.5 text-slate-500">{it.subscale}</td>
                        <td className="p-2.5 font-bold text-purple-700">{it.loading_general.toFixed(3)}</td>
                        <td className="p-2.5 text-slate-600">{it.loading_subscale.toFixed(3)}</td>
                        <td className="p-2.5 text-slate-500">{it.uniqueness.toFixed(3)}</td>
                        <td className="p-2.5 font-semibold text-slate-700">
                          {(it.item_ecv * 100).toFixed(1)}%
                        </td>
                        <td className="p-2.5">
                          {it.is_general_anchor ? (
                            <span className="px-1.5 py-0.5 bg-purple-100 text-purple-800 rounded font-semibold text-[10px]">
                              Anchor (I-ECV ≥ 80%)
                            </span>
                          ) : (
                            <span className="text-slate-400 text-[10px]">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Tường trình Khoa học Tiêu chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="text-xs text-purple-600 hover:text-purple-700 font-medium flex items-center gap-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                  <span>{copiedNarrative ? 'Đã sao chép!' : 'Sao chép APA'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic bg-white p-3 rounded-lg border border-slate-200">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
