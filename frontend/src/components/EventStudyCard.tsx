import React, { useState } from 'react';
import { api } from '../api/client';
import { EventStudyAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface EventStudyCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const EventStudyCard: React.FC<EventStudyCardProps> = ({
  surveyId,
  questions
}) => {
  const [unitQId, setUnitQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatedUnitsInput, setTreatedUnitsInput] = useState<string>('');
  const [globalEventTime, setGlobalEventTime] = useState<string>('');
  const [maxLeads, setMaxLeads] = useState<number>(5);
  const [maxLags, setMaxLags] = useState<number>(5);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EventStudyAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!unitQId) {
      setError('Vui lòng chọn câu hỏi định danh đơn vị / đối tượng (Unit Identifier).');
      return;
    }
    if (!timeQId) {
      setError('Vui lòng chọn câu hỏi mốc thời gian / chuỗi kỳ khảo sát (Time / Period Question).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả đầu ra (Outcome Variable Y).');
      return;
    }
    if (!treatedUnitsInput.trim()) {
      setError('Vui lòng nhập danh sách các đơn vị nhận can thiệp (phân cách bằng dấu phẩy).');
      return;
    }
    if (!globalEventTime.trim()) {
      setError('Vui lòng nhập thời điểm bắt đầu có hiệu lực can thiệp (Event Time E_i).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const treatedUnitsList = treatedUnitsInput
        .split(',')
        .map(u => u.trim())
        .filter(u => u.length > 0);

      const parsedEventTime = isNaN(Number(globalEventTime.trim()))
        ? globalEventTime.trim()
        : Number(globalEventTime.trim());

      const data = await api.runEventStudyAnalysis(surveyId, {
        unit_question_id: unitQId,
        time_question_id: timeQId,
        outcome_question_id: outcomeQId,
        treated_units: treatedUnitsList,
        global_event_time: parsedEventTime,
        max_leads: maxLeads,
        max_lags: maxLags,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || `Lỗi ước lượng Event-Study: ${data.status}`);
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng mô hình Dynamic Event-Study.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Econometric Causal Engine
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Staggered DiD & Pre-Trends
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Nghiên cứu Sự kiện Động & Kiểm định Xu hướng Song song (Dynamic Event-Study)
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Phân tích tác động chính sách / can thiệp theo thời gian với mốc chuẩn hóa $k = -1$ theo phương pháp chuẩn mực của{' '}
            <strong className="text-slate-200">Hausman & Rapson (2018)</strong>,{' '}
            <strong className="text-slate-200">Sun & Abraham (2021)</strong> và{' '}
            <strong className="text-slate-200">Callaway & Sant'Anna (2021)</strong>. Kiểm định đồng thời tính hợp lệ của giả định xu hướng song song tiền can thiệp (Pre-Trends Wald Test) và lập hồ sơ động lực tích lũy sau can thiệp.
          </p>
        </div>
      </div>

      {/* Control Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 my-6">
        {/* Unit Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            1. Đơn vị / Chi nhánh (Unit ID) <span className="text-rose-400">*</span>
          </label>
          <select
            value={unitQId}
            onChange={(e) => setUnitQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi phân loại đơn vị --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Time Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            2. Kỳ / Mốc thời gian (Period/Wave) <span className="text-rose-400">*</span>
          </label>
          <select
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi thời gian --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            3. Biến kết quả (Outcome Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến kết quả số --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Treated Units */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            4. Đơn vị can thiệp (Treated Units) <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            value={treatedUnitsInput}
            onChange={(e) => setTreatedUnitsInput(e.target.value)}
            placeholder="Ví dụ: Chi nhánh 1, Chi nhánh 2"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Event Time */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            5. Kỳ bắt đầu can thiệp (k = 0) <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            value={globalEventTime}
            onChange={(e) => setGlobalEventTime(e.target.value)}
            placeholder="Ví dụ: 3 hoặc Wave 3"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Leads/Lags & Scope Settings */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-slate-800/40 border border-slate-700/60 rounded-lg mb-6">
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <span className="text-slate-300 font-medium">Bộ lọc dữ liệu:</span>
          <label className="inline-flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="radio"
              name="es-scope"
              checked={scope === 'all'}
              onChange={() => setScope('all')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            Toàn bộ phản hồi
          </label>
          <label className="inline-flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="radio"
              name="es-scope"
              checked={scope === 'verified_clean'}
              onChange={() => setScope('verified_clean')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            Chỉ phản hồi sạch (Verified Clean $\ge$ 0.70)
          </label>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg shadow-lg hover:shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Đang hồi quy TWFE & Wald Pre-trends...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              <span>Ước lượng Nghiên cứu Sự kiện Động</span>
            </>
          )}
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 mb-6 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-sm flex items-start gap-2">
          <svg className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>{error}</div>
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6">
          {/* Key Metrics Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Xu hướng Song song (Pre-trend)</span>
              <p className={`text-base font-bold mt-1 ${result.parallel_trends_supported ? 'text-emerald-400' : 'text-rose-400'}`}>
                {result.parallel_trends_supported ? 'Thỏa mãn' : 'Cảnh báo vi phạm'}
              </p>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Wald p = {result.pre_trend_p_value} ({result.pre_trend_p_value! >= 0.05 ? 'p >= .05' : 'p < .05'})
              </span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Tác động Hậu Can thiệp TB</span>
              <p className={`text-xl font-bold mt-1 ${Number(result.avg_post_treatment_effect) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {Number(result.avg_post_treatment_effect) >= 0 ? `+${result.avg_post_treatment_effect}` : result.avg_post_treatment_effect}
              </p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Average Dynamic Effect</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Tác động Tích lũy (Cumulative)</span>
              <p className={`text-xl font-bold mt-1 ${Number(result.cumulative_post_treatment_effect) >= 0 ? 'text-sky-400' : 'text-amber-400'}`}>
                {Number(result.cumulative_post_treatment_effect) >= 0 ? `+${result.cumulative_post_treatment_effect}` : result.cumulative_post_treatment_effect}
              </p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Sum over post-event lags</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Cửa sổ Sự kiện (Window)</span>
              <p className="text-xl font-bold text-indigo-400 mt-1">
                [{result.event_window_min}, +{result.event_window_max}]
              </p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Leads to Lags relative to k=0</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Quy mô Mẫu Panel</span>
              <p className="text-xl font-bold text-white mt-1">N = {result.sample_size}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {result.units_count} đơn vị × {result.periods_count} kỳ
              </span>
            </div>
          </div>

          {/* SVG Event Study Plot */}
          {result.svg_chart && (
            <div className="bg-slate-800/50 border border-slate-700/80 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">
                Biểu đồ Nghiên cứu Sự kiện Động (Dynamic Event-Study Leads & Lags Ribbon)
              </h3>
              <div
                className="overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Event Coefficients Table */}
          <div className="bg-slate-800/40 border border-slate-700/70 rounded-lg p-4">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Bảng Hệ số Tác động Sự kiện Động theo Mốc Thời gian Tương đối ($k = t - E_i$)
            </h4>
            <div className="overflow-x-auto max-h-72 overflow-y-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="text-[11px] text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700 sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Mốc tương đối ($k$)</th>
                    <th className="py-2.5 px-3">Phân loại</th>
                    <th className="py-2.5 px-3 text-right">Hệ số ($\beta_k$)</th>
                    <th className="py-2.5 px-3 text-right">Sai số chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-right">Giá trị $z$</th>
                    <th className="py-2.5 px-3 text-right">Mức ý nghĩa ($p$)</th>
                    <th className="py-2.5 px-3 text-right">95% CI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.event_coefficients && result.event_coefficients.map((row, idx) => (
                    <tr
                      key={idx}
                      className={row.is_reference ? 'bg-slate-800/80 font-medium' : (row.relative_period >= 0 ? 'bg-indigo-950/20' : 'hover:bg-slate-800/40')}
                    >
                      <td className="py-2.5 px-3 font-medium text-slate-200">{row.period_label}</td>
                      <td className="py-2.5 px-3">
                        {row.is_reference ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-700 text-slate-300">
                            Kỳ cơ sở tham chiếu
                          </span>
                        ) : row.is_lead ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            Tiền can thiệp (Lead)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            Hậu can thiệp (Lag)
                          </span>
                        )}
                      </td>
                      <td className={`py-2.5 px-3 text-right font-mono font-semibold ${row.is_reference ? 'text-slate-400' : (row.coefficient >= 0 ? 'text-emerald-400' : 'text-rose-400')}`}>
                        {row.is_reference ? '0.0000' : (row.coefficient > 0 ? `+${row.coefficient}` : row.coefficient)}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                        {row.is_reference ? '-' : row.std_error}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                        {row.is_reference ? '-' : row.z_statistic}
                      </td>
                      <td className={`py-2.5 px-3 text-right font-mono font-semibold ${row.is_reference ? 'text-slate-400' : (row.is_significant ? 'text-emerald-400' : 'text-slate-400')}`}>
                        {row.is_reference ? '-' : row.p_value}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                        {row.is_reference ? '[0.0, 0.0]' : `[${row.ci_95_lower}, ${row.ci_95_upper}]`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-lg p-5">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-700">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded border border-slate-600 transition-colors flex items-center gap-1.5"
                >
                  {copiedNarrative ? (
                    <>
                      <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-emerald-300">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>Sao chép APA</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed italic bg-slate-900/50 p-4 rounded border border-slate-800">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
