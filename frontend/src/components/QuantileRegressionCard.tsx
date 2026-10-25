import React, { useState } from 'react';
import { api } from '../api/client';
import { QuantileRegressionResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface QuantileRegressionCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const QuantileRegressionCard: React.FC<QuantileRegressionCardProps> = ({
  surveyId,
  questions
}) => {
  const [predictorQId, setPredictorQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [selectedQuantiles, setSelectedQuantiles] = useState<number[]>([0.10, 0.25, 0.50, 0.75, 0.90]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QuantileRegressionResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericOrRatingQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const toggleQuantile = (qVal: number) => {
    setSelectedQuantiles(prev => {
      const exists = prev.includes(qVal);
      const next = exists ? prev.filter(v => v !== qVal) : [...prev, qVal];
      return next.sort((a, b) => a - b);
    });
  };

  const handleRunAnalysis = async () => {
    if (!predictorQId) {
      setError('Vui lòng chọn biến dự báo (Predictor X).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả (Outcome Y).');
      return;
    }
    if (predictorQId === outcomeQId) {
      setError('Biến dự báo và biến kết quả không được trùng nhau.');
      return;
    }
    if (selectedQuantiles.length === 0) {
      setError('Vui lòng chọn ít nhất một ngưỡng phân vị tau.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await api.runQuantileRegressionAnalysis(surveyId, {
        predictor_question_id: predictorQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: selectedCovariates,
        quantiles: selectedQuantiles,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể thực thi phân tích hồi quy phân vị.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi hệ thống khi phân tích Hồi quy Phân vị.');
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
              Hồi quy Phân vị & Hiệu ứng Phân phối (Quantile Regression)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Distributional Effects
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
              Koenker & Bassett 1978 • Koenker 2005
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Bóc tách tác động không đồng nhất của biến can thiệp/dự báo trên từng phân vị khác nhau của biến kết quả
            (nhóm điểm thấp τ=0.10, nhóm trung vị τ=0.50, nhóm xuất sắc τ=0.90) thay vì chỉ nhìn vào trung bình OLS đơn lẻ.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
        {/* Predictor Question */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Biến Dự báo (Predictor X) *
          </label>
          <select
            value={predictorQId}
            onChange={e => setPredictorQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến dự báo --</option>
            {numericOrRatingQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 30 ? q.title.substring(0, 30) + '…' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
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
                {q.title.length > 30 ? q.title.substring(0, 30) + '…' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Quantile Selectors */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Các Ngưỡng Phân Vị (Quantiles τ)
          </label>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {[0.10, 0.25, 0.50, 0.75, 0.90].map(tau => {
              const isSelected = selectedQuantiles.includes(tau);
              return (
                <button
                  key={tau}
                  type="button"
                  onClick={() => toggleQuantile(tau)}
                  className={`px-2 py-1 rounded text-xs font-semibold border transition-colors ${
                    isSelected
                      ? 'bg-indigo-600 border-indigo-700 text-white shadow-2xs'
                      : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  τ = {tau.toFixed(2)}
                </button>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">0.50 = Trung vị (Median Regression)</p>
        </div>

        {/* Scope */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi Khảo sát
          </label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as any)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">Toàn bộ phản hồi (All)</option>
            <option value="verified_clean">Chỉ mẫu sạch (Quality ≥ 0.70)</option>
          </select>
        </div>
      </div>

      {/* Covariates Controls (Optional) */}
      <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
          Biến Đồng biến Kiểm soát (Optional Covariates)
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-36 overflow-y-auto p-1">
          {numericOrRatingQuestions
            .filter(q => q.id !== predictorQId && q.id !== outcomeQId)
            .map(q => {
              const isChecked = selectedCovariates.includes(q.id);
              return (
                <label
                  key={q.id}
                  onClick={() => toggleCovariate(q.id)}
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
              <span>Đang tính toán Quantile IRLS & Sandwich SE...</span>
            </>
          ) : (
            <>
              <span>Ước lượng Hồi quy Phân vị (Fit Quantile Regression)</span>
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
              <span className="text-xs text-slate-500 font-medium">Cỡ mẫu & Phân vị</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                N = {result.sample_size}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {result.quantile_estimates?.length} ngưỡng phân vị • {result.covariates_count} biến kiểm soát
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Hồi quy Trung bình OLS</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                β_mean = {result.ols_baseline?.slope.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                SE = {result.ols_baseline?.standard_error.toFixed(3)} • p = {result.ols_baseline?.p_value.toFixed(3)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200">
              <span className="text-xs text-indigo-700 font-medium">Hồi quy Trung vị (Median τ=0.50)</span>
              <div className="text-2xl font-bold text-indigo-950 mt-1">
                {(() => {
                  const med = result.quantile_estimates?.find(q => Math.abs(q.tau - 0.50) < 0.01);
                  return med ? `β = ${med.slope.toFixed(3)}` : 'N/A';
                })()}
              </div>
              <div className="text-xs text-indigo-700 mt-1">Kháng ngoại lai mạnh mẽ (L1 Norm)</div>
            </div>

            <div
              className={`p-4 rounded-xl border ${
                result.heterogeneity_test?.has_significant_heterogeneity
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                  : 'bg-slate-50 border-slate-200 text-slate-800'
              }`}
            >
              <span className="text-xs font-bold uppercase tracking-wider">
                Chênh lệch Phân vị (Δβ)
              </span>
              <div className="text-2xl font-black mt-1">
                {result.heterogeneity_test?.slope_difference != null && result.heterogeneity_test.slope_difference > 0 ? '+' : ''}
                {result.heterogeneity_test?.slope_difference.toFixed(3)}
              </div>
              <div className="text-xs font-medium mt-1">
                p = {result.heterogeneity_test?.p_value.toFixed(3)}{' '}
                {result.heterogeneity_test?.has_significant_heterogeneity ? '(Không đồng nhất)' : '(Đồng nhất)'}
              </div>
            </div>
          </div>

          {/* Heterogeneity Verdict Alert */}
          <div
            className={`p-4 rounded-xl border flex items-start gap-3 ${
              result.heterogeneity_test?.has_significant_heterogeneity
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-slate-50 border-slate-200 text-slate-800'
            }`}
          >
            <div className="text-xl mt-0.5">
              {result.heterogeneity_test?.has_significant_heterogeneity ? '✓' : 'ℹ'}
            </div>
            <div>
              <div className="font-bold text-sm">
                {result.heterogeneity_test?.has_significant_heterogeneity
                  ? `Sự Không Đồng Nhất Phân Vị Có Ý Nghĩa Thống Kê (z = ${result.heterogeneity_test?.z_statistic.toFixed(2)}, p = ${result.heterogeneity_test?.p_value.toFixed(3)})`
                  : `Tác Động Tương Đối Đồng Đều Trên Toàn Phổ Phân Vị (p = ${result.heterogeneity_test?.p_value.toFixed(3)})`}
              </div>
              <p className="text-xs mt-1 opacity-90">
                {result.heterogeneity_test?.has_significant_heterogeneity
                  ? 'Biến dự báo tác động với cường độ khác biệt đáng kể giữa các nhóm đối tượng (ví dụ: nhóm có kết quả thấp so với nhóm có kết quả cao). Việc xem xét từng phân vị là thiết yếu để thiết kế chính sách nhắm mục tiêu.'
                  : 'Hệ số tác động không biến thiên quá lớn giữa các phân vị, mô hình hồi quy trung bình OLS cung cấp một bức tranh tổng quát tương đối thỏa đáng.'}
              </p>
            </div>
          </div>

          {/* Vector SVG Koenker Process Plot */}
          {result.svg_process_plot && (
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-800">
                    Đồ thị Quỹ đạo Hệ số Phân vị (Koenker Process Plot)
                  </h4>
                  <p className="text-xs text-slate-500">
                    Đường màu tím biểu diễn hệ số β(τ) cùng dải tin cậy 95% CI theo phân vị τ, so sánh với đường nét đứt đỏ của OLS Mean.
                  </p>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-white rounded-lg border border-slate-200"
                dangerouslySetInnerHTML={{ __html: result.svg_process_plot }}
              />
            </div>
          )}

          {/* Quantile Estimates Table */}
          {result.quantile_estimates && result.quantile_estimates.length > 0 && (
            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Bảng Chi Tiết Ước Lượng Hồi Quy Phân Vị (Quantile Parameter Estimates)
                </span>
                <span className="text-xs text-slate-500">Sandwich Standard Errors (Koenker 2005)</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      <th className="px-3 py-2 text-center font-semibold">Phân Vị (τ)</th>
                      <th className="px-3 py-2 text-right font-semibold">Hệ Số Góc β(τ)</th>
                      <th className="px-3 py-2 text-right font-semibold">Sai Số Chuẩn (SE)</th>
                      <th className="px-3 py-2 text-right font-semibold">Thống Kê t</th>
                      <th className="px-3 py-2 text-right font-semibold">p-value</th>
                      <th className="px-3 py-2 text-center font-semibold">95% Confidence Interval</th>
                      <th className="px-3 py-2 text-right font-semibold">Pseudo R¹</th>
                      <th className="px-3 py-2 text-center font-semibold">Ý Nghĩa (.05)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.quantile_estimates.map(q => (
                      <tr key={q.tau} className="hover:bg-slate-50">
                        <td className="px-3 py-2.5 text-center font-mono font-bold text-indigo-900">
                          τ = {q.tau.toFixed(2)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold text-slate-800">
                          {q.slope > 0 ? '+' : ''}{q.slope.toFixed(4)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">
                          {q.standard_error.toFixed(4)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-600">
                          {q.t_statistic.toFixed(3)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono font-medium text-slate-800">
                          {q.p_value.toFixed(4)}
                        </td>
                        <td className="px-3 py-2.5 text-center font-mono text-slate-600">
                          [{q.ci_95_lower.toFixed(3)}, {q.ci_95_upper.toFixed(3)}]
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono text-emerald-700 font-medium">
                          {(q.pseudo_r1 * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          {q.is_significant ? (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                              Có ý nghĩa
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-600">
                              Không
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
