import React, { useState } from 'react';
import { api } from '../api/client';
import { EVTAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface EVTCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const EVTCard: React.FC<EVTCardProps> = ({
  surveyId,
  questions
}) => {
  const [metricQId, setMetricQId] = useState<string>('');
  const [thresholdPct, setThresholdPct] = useState<number>(0.90);
  const [customThreshold, setCustomThreshold] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EVTAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!metricQId) {
      setError('Vui lòng chọn biến định lượng hoặc rủi ro (Metric Question).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runEVTAnalysis(surveyId, {
        metric_question_id: metricQId,
        threshold_percentile: thresholdPct,
        custom_threshold: customThreshold ? parseFloat(customThreshold) : undefined,
        alpha_levels: [0.95, 0.99, 0.995],
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình EVT.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích EVT.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 rounded-full">
              Extreme Risk &amp; Outlier Science
            </span>
            <span className="text-xs text-slate-400 font-mono">Pickands (1975) • Balkema &amp; de Haan (1974) • McNeil (2000)</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Extreme Value Theory (EVT) &amp; Survey Tail Risk Modeling
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Mô hình hóa phần đuôi cực đoan Peaks-Over-Threshold (POT) qua Phân phối Pareto Tổng quát (GPD), định lượng giá trị chịu rủi ro Value-at-Risk (VaR) và Kỳ vọng tổn thất đuôi Expected Shortfall (ES / CVaR).
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến đo lường / Tổn thất / Độ trễ (Metric) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-rose-500"
            value={metricQId}
            onChange={(e) => setMetricQId(e.target.value)}
          >
            <option value="">-- Chọn biến định lượng --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Ngưỡng bách phân vị vượt quá (Threshold Quantile)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-rose-500"
            value={thresholdPct}
            onChange={(e) => setThresholdPct(parseFloat(e.target.value))}
          >
            <option value="0.75">Top 25% cực đoan (Bách phân vị 75th)</option>
            <option value="0.80">Top 20% cực đoan (Bách phân vị 80th)</option>
            <option value="0.85">Top 15% cực đoan (Bách phân vị 85th)</option>
            <option value="0.90">Top 10% cực đoan (Bách phân vị 90th - Chuẩn)</option>
            <option value="0.95">Top 5% cực đoan (Bách phân vị 95th)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Ngưỡng tuyệt đối u tùy chọn (Custom Threshold)
          </label>
          <input
            type="number"
            step="any"
            placeholder="Để trống để dùng bách phân vị"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-rose-500"
            value={customThreshold}
            onChange={(e) => setCustomThreshold(e.target.value)}
          />
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-4">
          <label className="text-xs text-slate-400 flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="evt_scope"
              checked={scope === 'all'}
              onChange={() => setScope('all')}
              className="text-rose-500 focus:ring-rose-500 bg-slate-950 border-slate-700"
            />
            Toàn bộ phản hồi ({questions.length} câu)
          </label>
          <label className="text-xs text-slate-400 flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="evt_scope"
              checked={scope === 'verified_clean'}
              onChange={() => setScope('verified_clean')}
              className="text-rose-500 focus:ring-rose-500 bg-slate-950 border-slate-700"
            />
            Chỉ phản hồi đã làm sạch (Cleaned data)
          </label>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg shadow transition flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang ước lượng GPD &amp; VaR...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              Ước lượng Rủi ro Đuôi EVT
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg flex items-center gap-2">
          <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="mt-8 space-y-6">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Ngưỡng Phân định (u)</div>
              <div className="text-lg font-bold text-white mt-1">
                {result.threshold?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500">
                Nu = {result.exceedances_count} / {result.sample_size} ({((result.exceedance_probability || 0) * 100).toFixed(1)}%)
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Hệ số Đuôi (Shape ξ)</div>
              <div className="text-lg font-bold text-rose-400 mt-1">
                ξ = {result.shape_xi?.toFixed(4)}
              </div>
              <div className="text-xs font-mono text-slate-400">
                SE = {result.se_shape_xi?.toFixed(4)}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Hệ số Tỷ lệ (Scale σ)</div>
              <div className="text-lg font-bold text-amber-400 mt-1">
                σ = {result.scale_sigma?.toFixed(4)}
              </div>
              <div className="text-xs font-mono text-slate-400">
                SE = {result.se_scale_sigma?.toFixed(4)}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Độ phù hợp GPD (KS-Test)</div>
              <div className="text-lg font-bold text-emerald-400 mt-1">
                {result.gof_passed ? 'Tốt (Passed)' : 'Cảnh báo'}
              </div>
              <div className="text-xs font-mono text-slate-400">
                D = {result.gof_ks_statistic?.toFixed(3)}, p = {result.gof_ks_p_value?.toFixed(3)}
              </div>
            </div>
          </div>

          {/* Tail Classification Alert Banner */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-start gap-3">
            <span className="p-1.5 bg-rose-500/10 text-rose-400 rounded-md border border-rose-500/20 text-xs font-bold shrink-0">
              {result.tail_classification?.split(' ')[0]}
            </span>
            <div>
              <div className="text-xs font-semibold text-white">
                Phân loại Phân phối: {result.tail_classification}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {result.tail_interpretation}
              </p>
            </div>
          </div>

          {/* Risk Metrics Table (VaR & Expected Shortfall) */}
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center justify-between">
              <span>Bảng Chỉ số Rủi ro Đuôi Định lượng (Value-at-Risk &amp; Expected Shortfall)</span>
              <span className="text-xs text-slate-500 font-normal">
                Công thức Pickands (1975) &amp; McNeil &amp; Frey (2000)
              </span>
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="text-xs uppercase bg-slate-900/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Mức độ Tin cậy (Confidence Level p)</th>
                    <th className="py-2.5 px-3">Giá trị Chịu Rủi ro (Value-at-Risk - VaR_p)</th>
                    <th className="py-2.5 px-3">Kỳ vọng Tổn thất Đuôi (Expected Shortfall - ES_p)</th>
                    <th className="py-2.5 px-3">Ý nghĩa Quản trị &amp; Kiểm soát</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                  {result.risk_measures?.map((rm) => (
                    <tr key={rm.confidence_level}>
                      <td className="py-2.5 px-3 font-sans font-medium text-white">
                        {(rm.confidence_level * 100).toFixed(1)}% ({rm.confidence_level})
                      </td>
                      <td className="py-2.5 px-3 font-bold text-amber-400">
                        {rm.var_p.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-3 font-bold text-rose-400">
                        {rm.es_p !== null && rm.es_p !== undefined ? rm.es_p.toFixed(3) : 'Vô hạn (ξ ≥ 1.0)'}
                      </td>
                      <td className="py-2.5 px-3 font-sans text-slate-400">
                        Xác suất xuất hiện điểm vượt ngưỡng {rm.var_p.toFixed(2)} chỉ là {((1 - rm.confidence_level) * 100).toFixed(1)}%.
                        {rm.es_p && ` Khi xảy ra cực đoan, mức độ tác động trung bình là ${rm.es_p.toFixed(2)}.`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_chart && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2">
                Trực quan hóa Đồ thị Không gian Vector SVG Kép (Mean Excess &amp; Tail Survival)
              </h4>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-rose-400 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Tường thuật Khoa học Chuẩn APA 7th
                </h4>
                <button
                  onClick={copyToClipboard}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded transition flex items-center gap-1.5"
                >
                  {copiedNarrative ? (
                    <span className="text-emerald-400">Đã sao chép!</span>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                      </svg>
                      Sao chép APA
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed font-serif bg-slate-900/50 p-3 rounded border border-slate-800/80">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
