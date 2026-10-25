import React, { useState } from 'react';
import { api } from '../api/client';
import { IPWAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface IPWDoublyRobustCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const IPWDoublyRobustCard: React.FC<IPWDoublyRobustCardProps> = ({
  surveyId,
  questions
}) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [weightScheme, setWeightScheme] = useState<'ate' | 'att' | 'overlap' | 'stabilized'>('ate');
  const [trimWeights, setTrimWeights] = useState<boolean>(true);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IPWAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  // Lọc các câu hỏi phù hợp
  const numericOrRatingQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId) {
      setError('Vui lòng chọn biến can thiệp (Treatment Variable D).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả đầu ra (Outcome Variable Y).');
      return;
    }
    if (treatmentQId === outcomeQId) {
      setError('Biến can thiệp và biến kết quả không được trùng nhau.');
      return;
    }
    if (selectedCovariates.length === 0) {
      setError('Vui lòng chọn ít nhất một biến đồng biến (Covariate X) để cân bằng mẫu.');
      return;
    }
    if (selectedCovariates.includes(treatmentQId) || selectedCovariates.includes(outcomeQId)) {
      setError('Biến đồng biến không được trùng với biến can thiệp hoặc biến kết quả.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await api.runIPWAnalysis(surveyId, {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: selectedCovariates,
        weight_scheme: weightScheme,
        trim_weights: trimWeights,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể thực thi phân tích IPW.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi hệ thống khi phân tích IPW & Doubly Robust.');
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
              Trọng số IPW & Ước lượng Vững Kép (Doubly Robust / AIPW)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Causal Inference
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
              Robins 1994 • Austin 2015
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Suy diễn tác động nhân quả thuần túy từ dữ liệu khảo sát quan sát, khử nhiễu thiên lệch chọn lọc (Selection Bias)
            qua Trọng số Xác suất Nghịch đảo và Hồi quy Vững Kép (AIPW).
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
        {/* Treatment Question */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Biến Can thiệp (Treatment D) *
          </label>
          <select
            value={treatmentQId}
            onChange={e => setTreatmentQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến can thiệp --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 35 ? q.title.substring(0, 35) + '…' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Giá trị 1/True/Có = Can thiệp, 0 = Đối chứng</p>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Biến Kết quả (Outcome Y) *
          </label>
          <select
            value={outcomeQId}
            onChange={e => setOutcomeQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {numericOrRatingQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 35 ? q.title.substring(0, 35) + '…' : q.title}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Biến định lượng liên tục hoặc thang đo</p>
        </div>

        {/* Weight Scheme */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Lược đồ Trọng số (Scheme)
          </label>
          <select
            value={weightScheme}
            onChange={e => setWeightScheme(e.target.value as any)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="ate">ATE (Hiệu ứng Trung bình Toàn thể)</option>
            <option value="att">ATT (Hiệu ứng trên Nhóm Can thiệp)</option>
            <option value="overlap">OVERLAP (Trọng số Chồng lấn Li 2018)</option>
            <option value="stabilized">STABILIZED (Trọng số Ổn định Hernán)</option>
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Xác định tổng thể mục tiêu suy diễn</p>
        </div>

        {/* Scope & Options */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi & Cắt lọc Trọng số
          </label>
          <div className="space-y-2">
            <select
              value={scope}
              onChange={e => setScope(e.target.value as any)}
              className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="all">Toàn bộ phản hồi (All)</option>
              <option value="verified_clean">Chỉ mẫu sạch (Quality ≥ 0.70)</option>
            </select>
            <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={trimWeights}
                onChange={e => setTrimWeights(e.target.checked)}
                className="rounded text-emerald-600 focus:ring-emerald-500"
              />
              <span>Cắt tỉa trọng số ngoại lai (Trim 1%-99%)</span>
            </label>
          </div>
        </div>
      </div>

      {/* Covariates Selector */}
      <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
          Chọn Biến Đồng biến Gây nhiễu (Confounders / Covariates X) *
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-44 overflow-y-auto p-1">
          {numericOrRatingQuestions
            .filter(q => q.id !== treatmentQId && q.id !== outcomeQId)
            .map(q => {
              const isChecked = selectedCovariates.includes(q.id);
              return (
                <label
                  key={q.id}
                  onClick={() => toggleCovariate(q.id)}
                  className={`flex items-start gap-2 p-2 rounded border cursor-pointer transition-colors text-xs ${
                    isChecked
                      ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-medium'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}}
                    className="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="truncate" title={q.title}>
                    {q.title}
                  </span>
                </label>
              );
            })}
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Đã chọn: <strong className="text-emerald-700">{selectedCovariates.length}</strong> biến đồng biến gây nhiễu.
        </p>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang tính toán Propensity Score & AIPW...</span>
            </>
          ) : (
            <>
              <span>Ước lượng Tác động Nhân quả (Run Causal Inference)</span>
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
              <span className="text-xs text-slate-500 font-medium">Cỡ mẫu Phân tích</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                N = {result.sample_size}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Can thiệp: <strong className="text-emerald-700">{result.treated_count}</strong> | Đối chứng:{' '}
                <strong className="text-slate-700">{result.control_count}</strong>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Chênh lệch Thô (Unadjusted)</span>
              <div className="text-2xl font-bold text-slate-700 mt-1">
                {result.unadjusted_effect?.difference_in_means != null && result.unadjusted_effect.difference_in_means > 0 ? '+' : ''}
                {result.unadjusted_effect?.difference_in_means?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                SE = {result.unadjusted_effect?.standard_error?.toFixed(3)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200">
              <span className="text-xs text-indigo-700 font-medium">Ước lượng Hajek IPW</span>
              <div className="text-2xl font-bold text-indigo-900 mt-1">
                {result.ipw_estimator?.treatment_effect != null && result.ipw_estimator.treatment_effect > 0 ? '+' : ''}
                {result.ipw_estimator?.treatment_effect?.toFixed(3)}
              </div>
              <div className="text-xs text-indigo-700 mt-1">
                p = {result.ipw_estimator?.p_value?.toFixed(3)} • SE = {result.ipw_estimator?.standard_error?.toFixed(3)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
              <span className="text-xs text-emerald-800 font-bold uppercase tracking-wider">
                Ước lượng Vững Kép (AIPW)
              </span>
              <div className="text-2xl font-black text-emerald-900 mt-1">
                {result.doubly_robust_estimator?.treatment_effect != null && result.doubly_robust_estimator.treatment_effect > 0 ? '+' : ''}
                {result.doubly_robust_estimator?.treatment_effect?.toFixed(3)}
              </div>
              <div className="text-xs text-emerald-800 font-medium mt-1">
                95% CI [{result.doubly_robust_estimator?.ci_95_lower?.toFixed(3)}, {result.doubly_robust_estimator?.ci_95_upper?.toFixed(3)}]
              </div>
            </div>
          </div>

          {/* Causal Verdict Alert */}
          <div
            className={`p-4 rounded-xl border flex items-start gap-3 ${
              result.doubly_robust_estimator?.is_significant
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-amber-50 border-amber-300 text-amber-900'
            }`}
          >
            <div className="text-xl mt-0.5">
              {result.doubly_robust_estimator?.is_significant ? '✓' : 'ℹ'}
            </div>
            <div>
              <div className="font-bold text-sm">
                {result.doubly_robust_estimator?.is_significant
                  ? `Kết luận Nhân quả: Tác động có ý nghĩa thống kê (τ = ${result.doubly_robust_estimator?.treatment_effect.toFixed(3)}, p = ${result.doubly_robust_estimator?.p_value.toFixed(3)})`
                  : `Kết luận Nhân quả: Chưa đủ bằng chứng thống kê bác bỏ giả thuyết vô hiệu H0 (p = ${result.doubly_robust_estimator?.p_value.toFixed(3)})`}
              </div>
              <p className="text-xs mt-1 opacity-90">
                Ước lượng Vững Kép (Doubly Robust / AIPW) bảo đảm tính vững chắc ngay cả khi mô hình Propensity Score
                hoặc mô hình Hồi quy Kết quả bị sai đặc tả một phần (Robins et al., 1994).
              </p>
            </div>
          </div>

          {/* Vector SVG Love Plot */}
          {result.svg_love_plot && (
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-800">
                    Biểu đồ Cân bằng Mẫu (Love Plot) - ASMD Diagnostic
                  </h4>
                  <p className="text-xs text-slate-500">
                    So sánh Chênh lệch Trung bình Chuẩn hóa Tuyệt đối (Absolute SMD) trước và sau khi gán trọng số IPW.
                  </p>
                </div>
                {result.covariate_balance?.all_balanced_under_0_10 ? (
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                    Cân bằng Xuất sắc (All ASMD ≤ 0.10)
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
                    ASMD_max = {result.covariate_balance?.maximum_weighted_asmd.toFixed(3)}
                  </span>
                )}
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-white rounded-lg border border-slate-200"
                dangerouslySetInnerHTML={{ __html: result.svg_love_plot }}
              />
            </div>
          )}

          {/* Covariate Balance Table */}
          {result.covariate_balance?.diagnostics && (
            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Bảng Chi Tiết Chỉ Số Cân Bằng Đồng Biến (Covariate Balance Diagnostics)
                </span>
                <span className="text-xs text-slate-500">Ngưỡng chuẩn vàng: ASMD ≤ 0.10 (Austin 2009)</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold">Biến Đồng Biến (Covariate)</th>
                      <th className="px-3 py-2 text-right font-semibold">ASMD Thô (Raw)</th>
                      <th className="px-3 py-2 text-right font-semibold">ASMD Trọng số (IPW)</th>
                      <th className="px-3 py-2 text-right font-semibold">Cải Thiện (%)</th>
                      <th className="px-3 py-2 text-right font-semibold">Variance Ratio</th>
                      <th className="px-3 py-2 text-center font-semibold">Trạng Thái Cân Bằng</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.covariate_balance.diagnostics.map(it => (
                      <tr key={it.covariate_key} className="hover:bg-slate-50">
                        <td className="px-3 py-2.5 font-medium text-slate-800">{it.covariate_label}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">{it.raw_asmd.toFixed(4)}</td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold text-slate-800">
                          {it.weighted_asmd.toFixed(4)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono text-emerald-700 font-medium">
                          +{it.improvement_pct.toFixed(1)}%
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">
                          {it.weighted_variance_ratio.toFixed(3)}
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          {it.is_balanced ? (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                              Đạt (≤ 0.10)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-800">
                              Lưu ý ({'>'} 0.10)
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
