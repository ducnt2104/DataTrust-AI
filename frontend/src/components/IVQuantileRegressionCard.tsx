import React, { useState } from 'react';
import { api } from '../api/client';
import { IVQuantileRegressionResult, IVQuantileRegressionRequest } from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface Props {
  surveyId: string;
  questions: QuestionOption[];
}

export const IVQuantileRegressionCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [instrumentQId, setInstrumentQId] = useState<string>('');
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<IVQuantileRegressionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'likert'
  );

  const toggleCovariate = (id: string) => {
    if (covariateQIds.includes(id)) {
      setCovariateQIds(covariateQIds.filter((x) => x !== id));
    } else {
      setCovariateQIds([...covariateQIds, id]);
    }
  };

  const handleRun = async () => {
    if (!outcomeQId || !treatmentQId || !instrumentQId) {
      setError('Vui lòng chọn đầy đủ biến kết quả Y, biến can thiệp D và biến công cụ Z.');
      return;
    }
    if (treatmentQId === outcomeQId || instrumentQId === outcomeQId || treatmentQId === instrumentQId) {
      setError('Các biến kết quả, can thiệp và biến công cụ phải khác nhau.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const payload: IVQuantileRegressionRequest = {
        outcome_question_id: outcomeQId,
        treatment_question_id: treatmentQId,
        instrument_question_id: instrumentQId,
        covariate_question_ids: covariateQIds,
        quantiles: [0.10, 0.25, 0.50, 0.75, 0.90],
        grid_points: 80,
        scope,
      };
      const res = await api.runIVQuantileRegressionAnalysis(surveyId, payload);
      if (res.status === 'error' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không thể tính toán mô hình hồi quy phân vị biến công cụ IV-QR.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích IV-QR.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const medianQ = result?.quantile_estimates?.find((q) => Math.abs(q.quantile - 0.5) < 1e-4);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg text-lg font-bold">
              📊 IV-QR
            </span>
            <h3 className="text-xl font-bold text-slate-100">
              Instrumental Variable Quantile Regression (IV-QR)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Victor Chernozhukov &amp; Christian Hansen (2005, 2008) — Ước lượng tác động nhân quả phân vị phi tuyến hiệu chỉnh nội sinh &amp; phân tách dị biệt hóa đáp ứng qua các tầng phân vị.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          >
            <option value="all">Toàn bộ phản hồi (Tất cả)</option>
            <option value="verified_clean">Chỉ dữ liệu đã xác minh sạch</option>
          </select>
          <button
            onClick={handleRun}
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow transition-all flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Đang quét nghịch đảo phân vị...</span>
              </>
            ) : (
              <>
                <span>▶ Ước Lượng Phân Vị IV-QR</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Inputs Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-5 bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            1. Biến Kết quả (Outcome Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-emerald-500"
          >
            <option value="">-- Chọn biến phụ thuộc --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            2. Biến Can thiệp Nội sinh (Treatment D) <span className="text-rose-400">*</span>
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-emerald-500"
          >
            <option value="">-- Chọn biến can thiệp nội sinh --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            3. Biến Công cụ Ngoại sinh (Instrument Z) <span className="text-rose-400">*</span>
          </label>
          <select
            value={instrumentQId}
            onChange={(e) => setInstrumentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-emerald-500"
          >
            <option value="">-- Chọn biến công cụ ngoại sinh --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Covariates Multiselect */}
        <div className="md:col-span-3 mt-2">
          <label className="block text-xs font-semibold text-slate-300 mb-2">
            4. Biến Kiểm soát Ngoại sinh Bổ sung (Exogenous Covariates X):
          </label>
          <div className="flex flex-wrap gap-2">
            {numericQuestions
              .filter((q) => q.id !== outcomeQId && q.id !== treatmentQId && q.id !== instrumentQId)
              .map((q) => {
                const isSelected = covariateQIds.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleCovariate(q.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                      isSelected
                        ? 'bg-emerald-600/30 text-emerald-300 border-emerald-500 shadow-sm'
                        : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    {isSelected ? '✓ ' : '+ '} {q.title}
                  </button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-lg text-xs flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.summary && result.quantile_estimates && (
        <div className="space-y-6 mt-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Instrument Strength */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Độ Mạnh Biến Công Cụ
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span
                  className={`text-sm font-bold px-2 py-0.5 rounded ${
                    result.summary.instrument_strength === 'STRONG_INSTRUMENT'
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : 'bg-amber-500/20 text-amber-300'
                  }`}
                >
                  {result.summary.instrument_strength}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                F-stat (Tầng 1): {result.summary.instrument_f_stat.toFixed(2)} (Chuẩn &gt; 10.0)
              </p>
            </div>

            {/* Median Causal Effect */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Hiệu Ứng Trung Vị α(0.50)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-emerald-400">
                  {medianQ ? medianQ.iv_qr_estimate.toFixed(3) : result.summary.tsls_estimate.toFixed(3)}
                </span>
                <span className="text-xs text-slate-400">
                  95% CI: [{medianQ?.ci_lower.toFixed(2)}, {medianQ?.ci_upper.toFixed(2)}]
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Lệch nội sinh: Δ = {medianQ?.endogeneity_bias_gap.toFixed(3)}
              </p>
            </div>

            {/* Benchmark OLS vs 2SLS */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Đối Chiếu Trung Bình OLS vs 2SLS
              </span>
              <div className="mt-1 text-xs space-y-1">
                <div className="text-amber-400 font-mono">
                  OLS: β = {result.summary.ols_estimate.toFixed(3)} (SE {result.summary.ols_se.toFixed(2)})
                </div>
                <div className="text-sky-400 font-mono">
                  2SLS: α = {result.summary.tsls_estimate.toFixed(3)} (SE {result.summary.tsls_se.toFixed(2)})
                </div>
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                2SLS chỉ ước lượng trung bình cục bộ (LATE)
              </p>
            </div>

            {/* Quantile Heterogeneity */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Dị Biệt Hóa Phân Vị (90 - 10)
              </span>
              <div className="mt-1 text-2xl font-extrabold text-purple-400">
                {result.summary.interquantile_spread_90_10.toFixed(3)}
              </div>
              <p className="text-[11px] mt-1">
                <span
                  className={`font-semibold ${
                    result.summary.has_quantile_heterogeneity ? 'text-emerald-400' : 'text-slate-400'
                  }`}
                >
                  {result.summary.has_quantile_heterogeneity ? '✓ Có phân hóa rõ rệt' : 'Tác động đồng nhất'}
                </span>
              </p>
            </div>
          </div>

          {/* SVG Vector Chart Display */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-hidden shadow-inner">
              <div
                className="w-full flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Quantile Estimates Spectrum Table */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">
              Quang Phổ Tác Động Phân Vị Chernozhukov &amp; Hansen (2005)
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[10px]">
                  <tr>
                    <th className="px-3 py-2">Tầng Phân Vị (τ)</th>
                    <th className="px-3 py-2 text-right text-emerald-400">Hiệu Ứng IV-QR α(τ)</th>
                    <th className="px-3 py-2 text-right">Khoảng Tin Cậy Đảo Ngược 95% CI</th>
                    <th className="px-3 py-2 text-right text-slate-400">QR Ngây Thơ (Ngoại sinh)</th>
                    <th className="px-3 py-2 text-right text-amber-400">Sai Lệch Nội Sinh (Δ)</th>
                    <th className="px-3 py-2 text-center">Ý Nghĩa Thống Kê</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.quantile_estimates.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/50">
                      <td className="px-3 py-2 font-bold text-slate-100">
                        τ = {row.quantile.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono font-bold text-emerald-400">
                        {row.iv_qr_estimate.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-slate-300">
                        [{row.ci_lower.toFixed(3)}, {row.ci_upper.toFixed(3)}]
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-slate-400">
                        {row.exogenous_qr_estimate.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-amber-400">
                        {row.endogeneity_bias_gap.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            row.is_significant
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {row.is_significant ? 'Có ý nghĩa (p<.05)' : 'Chưa có ý nghĩa'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyNarrative}
                  className="px-2.5 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
                >
                  {copied ? '✓ Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/60 p-3 rounded border border-slate-800/80">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
