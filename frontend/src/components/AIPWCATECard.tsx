import React, { useState } from 'react';
import { api } from '../api/client';
import { AIPWCATEResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface AIPWCATECardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const AIPWCATECard: React.FC<AIPWCATECardProps> = ({
  surveyId,
  questions
}) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [treatmentValue, setTreatmentValue] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [confounderQIds, setConfounderQIds] = useState<string[]>([]);
  const [subgroupQId, setSubgroupQId] = useState<string>('');
  const [trimAlpha, setTrimAlpha] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIPWCATEResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleToggleConfounder = (qId: string) => {
    if (confounderQIds.includes(qId)) {
      setConfounderQIds(confounderQIds.filter(id => id !== qId));
    } else {
      setConfounderQIds([...confounderQIds, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId) {
      setError('Vui lòng chọn câu hỏi can thiệp / phân nhóm chính sách (Treatment W).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả đầu ra (Outcome Variable Y).');
      return;
    }
    if (confounderQIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến đồng biến gây nhiễu (Confounders X) để hiệu chỉnh xu hướng.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await api.runAIPWCATEAnalysis(surveyId, {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        confounder_question_ids: confounderQIds,
        subgroup_question_id: subgroupQId ? subgroupQId : undefined,
        treatment_value: treatmentValue.trim() ? treatmentValue.trim() : undefined,
        trim_alpha: trimAlpha,
        scope
      });

      setResult(res);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không đủ dữ liệu hợp lệ để ước lượng Doubly Robust AIPW.');
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích Doubly Robust AIPW & CATE.');
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
          <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg font-bold text-sm">
            AIPW
          </span>
          <div>
            <h3 className="text-lg font-bold text-slate-800">
              Doubly Robust (AIPW) & CATE Heterogeneity Analysis
            </h3>
            <p className="text-xs text-slate-500">
              Ước lượng Tác động Can thiệp Kép Vững (Doubly Robust) và Phân tích Không đồng nhất Phân khúc (CATE) theo Robins et al. (1994), Chernozhukov et al. (2018) & Athey & Wager (2019).
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Treatment Question */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến can thiệp / Phân nhóm (Treatment W)
          </label>
          <select
            value={treatmentQId}
            onChange={e => setTreatmentQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến can thiệp --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Giá trị gán W=1 (tùy chọn: VD Có, 1)"
            value={treatmentValue}
            onChange={e => setTreatmentValue(e.target.value)}
            className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 mt-1.5 bg-slate-50 focus:bg-white"
          />
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kết quả đầu ra (Outcome Y)
          </label>
          <select
            value={outcomeQId}
            onChange={e => setOutcomeQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <div className="mt-1.5 flex items-center justify-between text-xs text-slate-500">
            <span>Ngưỡng cắt lọc biên (Crump α):</span>
            <span className="font-semibold">{trimAlpha}</span>
          </div>
          <input
            type="range"
            min="0.01"
            max="0.15"
            step="0.01"
            value={trimAlpha}
            onChange={e => setTrimAlpha(parseFloat(e.target.value))}
            className="w-full accent-emerald-600 cursor-pointer"
          />
        </div>

        {/* Subgroup / Segmentation */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến phân khúc / Tiểu nhóm CATE (Tùy chọn)
          </label>
          <select
            value={subgroupQId}
            onChange={e => setSubgroupQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Không phân nhóm (Chỉ tính ATE) --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>

          <label className="block text-xs font-semibold text-slate-600 mt-2 mb-1">
            Phạm vi kiểm định dữ liệu
          </label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as 'all' | 'verified_clean')}
            className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 focus:bg-white"
          >
            <option value="all">Toàn bộ mẫu khảo sát</option>
            <option value="verified_clean">Chỉ mẫu đã kiểm định hợp lệ</option>
          </select>
        </div>
      </div>

      {/* Confounder Multi-Select */}
      <div>
        <label className="block text-xs font-semibold text-slate-600 mb-1">
          Các biến đồng biến gây nhiễu cần hiệu chỉnh (Confounders X — Propensity & Outcome Models):
        </label>
        <div className="max-h-28 overflow-y-auto border border-slate-200 rounded-lg p-2.5 grid grid-cols-1 md:grid-cols-2 gap-2 bg-slate-50">
          {numericQuestions
            .filter(q => q.id !== outcomeQId && q.id !== treatmentQId)
            .map(q => (
              <label key={q.id} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={confounderQIds.includes(q.id)}
                  onChange={() => handleToggleConfounder(q.id)}
                  className="rounded text-emerald-600 focus:ring-emerald-500"
                />
                <span className="truncate">{q.title}</span>
              </label>
            ))}
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm rounded-lg transition-colors shadow-sm disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Đang tính toán Doubly Robust AIPW & CATE...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Ước lượng Tác động Kép Vững (AIPW)</span>
            </>
          )}
        </button>

        {result && (
          <span
            className={`text-xs px-3 py-1 rounded-full font-medium ${
              result.status === 'success'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}
          >
            Trạng thái: {result.status.toUpperCase()}
          </span>
        )}
      </div>

      {/* Error display */}
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
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl">
              <span className="text-xs text-emerald-800 font-medium">Tác động TB Kép Vững (AIPW ATE)</span>
              <div className="text-xl font-bold text-emerald-700 mt-1">
                {result.ate !== undefined ? (result.ate >= 0 ? '+' : '') + result.ate.toFixed(3) : '--'}
              </div>
              <span className="text-[11px] text-emerald-600">
                SE = {result.se?.toFixed(3)} | 95% CI [{result.ci_95_lower?.toFixed(2)}, {result.ci_95_upper?.toFixed(2)}]
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Chênh lệch ngây thơ (Naive)</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.naive_difference !== undefined
                  ? (result.naive_difference >= 0 ? '+' : '') + result.naive_difference.toFixed(3)
                  : '--'}
              </div>
              <span className="text-[11px] text-rose-600 font-medium">
                Thiên lệch chọn lọc: {result.selection_bias_estimate !== undefined ? (result.selection_bias_estimate >= 0 ? '+' : '') + result.selection_bias_estimate.toFixed(3) : '--'}
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Cỡ mẫu & Hỗ trợ chung</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.effective_sample_size} / {result.total_sample_size}
              </div>
              <span className="text-[11px] text-slate-500">
                Cắt lọc {result.trimmed_units_count} mẫu biên (Crump Trim)
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Kiểm định Không đồng nhất</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.heterogeneity_test?.p_value !== undefined
                  ? `p = ${result.heterogeneity_test.p_value.toFixed(3)}`
                  : 'N/A'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  result.heterogeneity_test?.is_heterogeneous ? 'text-amber-600' : 'text-slate-500'
                }`}
              >
                {result.heterogeneity_test?.is_heterogeneous
                  ? 'Phân hóa CATE có ý nghĩa'
                  : 'Tác động đồng nhất'}
              </span>
            </div>
          </div>

          {/* Dual-Panel SVG Chart */}
          {result.svg_chart && (
            <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Đồ thị Vector Động học Kép: Phân bố Overlap e(X) & Forest Plot CATE
                </span>
                <span className="text-[11px] text-slate-400">
                  Panel A: Trùng lặp xác suất khuynh hướng | Panel B: Hiệu ứng phân nhóm kẹp CI 95%
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Subgroup CATE Table */}
          {result.subgroup_cate && result.subgroup_cate.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Bảng Ước lượng Tác động Phân khúc (Conditional Average Treatment Effects - CATE)
              </span>
              <div className="max-h-64 overflow-y-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold sticky top-0 border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Phân khúc (Subgroup)</th>
                      <th className="p-2.5">Cỡ mẫu (n)</th>
                      <th className="p-2.5">Ước tính CATE</th>
                      <th className="p-2.5">Sai số chuẩn (SE)</th>
                      <th className="p-2.5">Khoảng tin cậy 95% CI</th>
                      <th className="p-2.5">z-score</th>
                      <th className="p-2.5">p-value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.subgroup_cate.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="p-2.5 font-semibold text-slate-800">{row.subgroup}</td>
                        <td className="p-2.5 text-slate-600">{row.sample_size}</td>
                        <td
                          className={`p-2.5 font-bold ${
                            row.cate > 0 ? 'text-emerald-600' : row.cate < 0 ? 'text-rose-600' : 'text-slate-600'
                          }`}
                        >
                          {row.cate > 0 ? '+' : ''}
                          {row.cate.toFixed(3)}
                        </td>
                        <td className="p-2.5 text-slate-600">{row.se.toFixed(3)}</td>
                        <td className="p-2.5 font-mono text-slate-500 text-[11px]">
                          [{row.ci_lower.toFixed(2)}, {row.ci_upper.toFixed(2)}]
                        </td>
                        <td className="p-2.5 text-slate-600">{row.z_score.toFixed(2)}</td>
                        <td className="p-2.5 font-medium">
                          <span
                            className={
                              row.p_value < 0.05
                                ? 'text-emerald-600 font-semibold'
                                : 'text-slate-500'
                            }
                          >
                            {row.p_value.toFixed(4)}
                          </span>
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
                  className="text-xs text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1"
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
