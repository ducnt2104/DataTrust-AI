import React, { useState } from 'react';
import { api } from '../api/client';
import { IV2SLSResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface IV2SLSCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const IV2SLSCard: React.FC<IV2SLSCardProps> = ({
  surveyId,
  questions
}) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [endogQId, setEndogQId] = useState<string>('');
  const [instrumentQIds, setInstrumentQIds] = useState<string[]>([]);
  const [controlQIds, setControlQIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IV2SLSResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleToggleInstrument = (qId: string) => {
    if (instrumentQIds.includes(qId)) {
      setInstrumentQIds(instrumentQIds.filter(id => id !== qId));
    } else {
      setInstrumentQIds([...instrumentQIds, qId]);
    }
  };

  const handleToggleControl = (qId: string) => {
    if (controlQIds.includes(qId)) {
      setControlQIds(controlQIds.filter(id => id !== qId));
    } else {
      setControlQIds([...controlQIds, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả đầu ra (Outcome Variable Y).');
      return;
    }
    if (!endogQId) {
      setError('Vui lòng chọn biến dự báo có nghi vấn nội sinh (Endogenous Regressor X).');
      return;
    }
    if (instrumentQIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến công cụ ngoại sinh (Instrument Z).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await api.runIV2SLSAnalysis(surveyId, {
        outcome_question_id: outcomeQId,
        endogenous_question_id: endogQId,
        instrument_question_ids: instrumentQIds,
        control_question_ids: controlQIds.length > 0 ? controlQIds : undefined,
        scope
      });

      setResult(res);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không đủ dữ liệu quan sát hợp lệ để thực hiện hồi quy 2SLS.');
      } else if (res.status === 'collinear_instruments') {
        setError(res.message || 'Ma trận biến công cụ bị phụ thuộc tuyến tính hoặc suy biến.');
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích hồi quy biến công cụ 2SLS.');
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
          <span className="p-2 bg-cyan-50 text-cyan-600 rounded-lg font-bold text-sm">
            2SLS
          </span>
          <div>
            <h3 className="text-lg font-bold text-slate-800">
              Instrumental Variables (2SLS) & Weak Instrument Diagnostics
            </h3>
            <p className="text-xs text-slate-500">
              Hồi quy Biến Công cụ Bình phương Tối thiểu Hai Giai đoạn (2SLS) triệt tiêu thiên lệch nội sinh kèm chẩn đoán công cụ yếu Stock-Yogo (2005) & kiểm định Wu-Hausman.
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Outcome Y */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kết quả phụ thuộc (Outcome Y)
          </label>
          <select
            value={outcomeQId}
            onChange={e => setOutcomeQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Endogenous Regressor X */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến nội sinh cần xử lý (Endogenous Predictor X)
          </label>
          <select
            value={endogQId}
            onChange={e => setEndogQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <option value="">-- Chọn biến dự báo nội sinh --</option>
            {numericQuestions
              .filter(q => q.id !== outcomeQId)
              .map(q => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* Instruments & Controls Checkboxes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Excluded Instruments Z */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến công cụ ngoại sinh (Instruments Z — Chọn ít nhất 1):
          </label>
          <div className="max-h-28 overflow-y-auto border border-slate-200 rounded-lg p-2.5 space-y-1 bg-slate-50">
            {numericQuestions
              .filter(q => q.id !== outcomeQId && q.id !== endogQId && !controlQIds.includes(q.id))
              .map(q => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={instrumentQIds.includes(q.id)}
                    onChange={() => handleToggleInstrument(q.id)}
                    className="rounded text-cyan-600 focus:ring-cyan-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
          </div>
        </div>

        {/* Exogenous Controls W */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kiểm soát ngoại sinh bổ sung (Controls W — Tùy chọn):
          </label>
          <div className="max-h-28 overflow-y-auto border border-slate-200 rounded-lg p-2.5 space-y-1 bg-slate-50">
            {numericQuestions
              .filter(q => q.id !== outcomeQId && q.id !== endogQId && !instrumentQIds.includes(q.id))
              .map(q => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={controlQIds.includes(q.id)}
                    onChange={() => handleToggleControl(q.id)}
                    className="rounded text-cyan-600 focus:ring-cyan-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
          </div>
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
          className="w-full md:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-sm rounded-lg transition-colors shadow-sm disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Đang hồi quy hai giai đoạn (2SLS)...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <span>Ước lượng Biến Công cụ (2SLS)</span>
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
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-cyan-50/50 border border-cyan-200 rounded-xl">
              <span className="text-xs text-cyan-800 font-medium">Hệ số Không chệch 2SLS (β)</span>
              <div className="text-xl font-bold text-cyan-700 mt-1">
                {result.iv_estimate?.beta !== undefined
                  ? (result.iv_estimate.beta >= 0 ? '+' : '') + result.iv_estimate.beta.toFixed(3)
                  : '--'}
              </div>
              <span className="text-[11px] text-cyan-600">
                SE = {result.iv_estimate?.se?.toFixed(3)} | p = {result.iv_estimate?.p_value?.toFixed(4)}
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Hệ số OLS Bị chệch</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.ols_benchmark?.beta !== undefined
                  ? (result.ols_benchmark.beta >= 0 ? '+' : '') + result.ols_benchmark.beta.toFixed(3)
                  : '--'}
              </div>
              <span className="text-[11px] text-rose-600 font-medium">
                Độ lệch nội sinh: {result.ols_benchmark?.bias_difference !== undefined ? (result.ols_benchmark.bias_difference >= 0 ? '+' : '') + result.ols_benchmark.bias_difference.toFixed(3) : '--'}
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Thống kê First-Stage F</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.first_stage_diagnostics?.f_statistic?.toFixed(1) || '--'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  !result.first_stage_diagnostics?.is_weak_instrument
                    ? 'text-emerald-600'
                    : 'text-rose-600'
                }`}
              >
                {!result.first_stage_diagnostics?.is_weak_instrument
                  ? 'Công cụ mạnh (F ≥ 10)'
                  : 'Công cụ yếu (F < 10)'}
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Kiểm định Wu-Hausman</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.wu_hausman_test?.p_value !== undefined
                  ? `p = ${result.wu_hausman_test.p_value.toFixed(3)}`
                  : '--'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  result.wu_hausman_test?.is_endogenous ? 'text-cyan-700' : 'text-slate-500'
                }`}
              >
                {result.wu_hausman_test?.is_endogenous
                  ? 'Có nội sinh (Cần 2SLS)'
                  : 'Chưa thấy nội sinh'}
              </span>
            </div>
          </div>

          {/* Overidentification Sargan Card if L > 1 */}
          {result.sargan_hansen_overid_test && result.sargan_hansen_overid_test.j_statistic !== undefined && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs">
              <span className="text-slate-600 font-medium">
                Kiểm định Nhận diện Thừa Sargan-Hansen (J-Test): J = {result.sargan_hansen_overid_test.j_statistic?.toFixed(3)}, p = {result.sargan_hansen_overid_test.p_value?.toFixed(4)}
              </span>
              <span
                className={`px-2 py-0.5 rounded font-semibold ${
                  result.sargan_hansen_overid_test.instruments_valid
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-rose-100 text-rose-800'
                }`}
              >
                {result.sargan_hansen_overid_test.instruments_valid
                  ? 'Công cụ thỏa mãn giả định loại trừ (Exclusion Valid)'
                  : 'Vi phạm giả định loại trừ'}
              </span>
            </div>
          )}

          {/* Dual-Panel SVG Chart */}
          {result.svg_chart && (
            <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Đồ thị Vector Động học 2SLS: Độ mạnh Giai đoạn 1 & So sánh Hệ số OLS vs 2SLS
                </span>
                <span className="text-[11px] text-slate-400">
                  Panel A: First-Stage Fit & F-Gauge | Panel B: Forest Plot Hệ số cấu trúc CI 95%
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Detailed Coefficients Comparison Table */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
              Bảng Đối sánh Thông số Ước lượng (2SLS vs OLS Benchmark)
            </span>
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-2.5">Phương pháp ước lượng</th>
                    <th className="p-2.5">Hệ số góc (β)</th>
                    <th className="p-2.5">Sai số chuẩn (SE)</th>
                    <th className="p-2.5">Thống kê kiểm định</th>
                    <th className="p-2.5">Khoảng tin cậy 95% CI</th>
                    <th className="p-2.5">p-value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="bg-cyan-50/30">
                    <td className="p-2.5 font-bold text-cyan-800">
                      2SLS (Hiệu chỉnh Biến công cụ)
                    </td>
                    <td className="p-2.5 font-bold text-cyan-700">
                      {result.iv_estimate?.beta !== undefined
                        ? (result.iv_estimate.beta >= 0 ? '+' : '') + result.iv_estimate.beta.toFixed(4)
                        : '--'}
                    </td>
                    <td className="p-2.5 text-slate-700">{result.iv_estimate?.se?.toFixed(4)}</td>
                    <td className="p-2.5 text-slate-700">z = {result.iv_estimate?.z_stat?.toFixed(2)}</td>
                    <td className="p-2.5 font-mono text-slate-600 text-[11px]">
                      [{result.iv_estimate?.ci_95_lower?.toFixed(3)}, {result.iv_estimate?.ci_95_upper?.toFixed(3)}]
                    </td>
                    <td className="p-2.5 font-semibold text-emerald-600">
                      {result.iv_estimate?.p_value?.toFixed(4)}
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold text-amber-800">
                      OLS (Hồi quy chuẩn OLS)
                    </td>
                    <td className="p-2.5 font-semibold text-amber-700">
                      {result.ols_benchmark?.beta !== undefined
                        ? (result.ols_benchmark.beta >= 0 ? '+' : '') + result.ols_benchmark.beta.toFixed(4)
                        : '--'}
                    </td>
                    <td className="p-2.5 text-slate-600">{result.ols_benchmark?.se?.toFixed(4)}</td>
                    <td className="p-2.5 text-slate-600">t = {result.ols_benchmark?.t_stat?.toFixed(2)}</td>
                    <td className="p-2.5 font-mono text-slate-500 text-[11px]">
                      [{((result.ols_benchmark?.beta || 0) - 1.96 * (result.ols_benchmark?.se || 0)).toFixed(3)}, {((result.ols_benchmark?.beta || 0) + 1.96 * (result.ols_benchmark?.se || 0)).toFixed(3)}]
                    </td>
                    <td className="p-2.5 text-slate-600">
                      {result.ols_benchmark?.p_value?.toFixed(4)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Tường trình Khoa học Tiêu chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="text-xs text-cyan-600 hover:text-cyan-700 font-medium flex items-center gap-1"
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
