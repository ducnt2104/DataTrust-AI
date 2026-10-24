import React, { useState } from 'react';
import { api } from '../api/client';
import { StaggeredDIDResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const StaggeredDIDCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [unitQid, setUnitQid] = useState<string>('');
  const [timeQid, setTimeQid] = useState<string>('');
  const [timingQid, setTimingQid] = useState<string>('');
  const [controlGroupType, setControlGroupType] = useState<'never_treated' | 'not_yet_treated'>('never_treated');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<StaggeredDIDResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'event_study' | 'group_time' | 'bacon'>('event_study');

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'slider' ||
      q.question_type === 'short_text'
  );

  const handleRun = async () => {
    if (!outcomeQid || !unitQid || !timeQid || !timingQid) {
      setError('Vui lòng chọn đầy đủ 4 biến: Kết quả (Y), Đơn vị (U), Mốc thời gian (T), và Thời điểm can thiệp (G).');
      return;
    }
    const selected = [outcomeQid, unitQid, timeQid, timingQid];
    if (new Set(selected).size !== 4) {
      setError('Các biến chọn phải là các câu hỏi khác nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.runStaggeredDID(surveyId, {
        outcome_question_id: outcomeQid,
        unit_question_id: unitQid,
        time_question_id: timeQid,
        treatment_timing_question_id: timingQid,
        control_group_type: controlGroupType,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_TIME_PERIODS' || res.status === 'NO_TREATED_UNITS') {
        setError(res.message || 'Không đủ điều kiện dữ liệu để ước lượng Staggered DiD.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Staggered DiD.');
    } finally {
      setLoading(false);
    }
  };

  const diag = result?.diagnostics;

  return (
    <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 mb-8 transition-all hover:shadow-lg">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              Econometrics v3.15
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
              Callaway & Sant'Anna (2021)
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">
              Goodman-Bacon (2021)
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Difference-in-Differences Phân tầng Thời gian (Staggered DiD)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Ước lượng tác động can thiệp phi tham số nhóm - thời gian ATT(g,t) và phân rã trọng số Goodman-Bacon, loại bỏ hoàn toàn thiên lệch trọng số âm trong hồi quy Two-Way Fixed Effects (TWFE).
          </p>
        </div>
      </div>

      {/* Control Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5 p-4 bg-slate-50 rounded-lg border border-slate-200">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến kết quả (Outcome Y) *
          </label>
          <select
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Mã đơn vị quan sát (Unit ID) *
          </label>
          <select
            value={unitQid}
            onChange={(e) => setUnitQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến đơn vị khảo sát --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Đợt / Mốc thời gian (Wave T) *
          </label>
          <select
            value={timeQid}
            onChange={(e) => setTimeQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến đợt khảo sát T --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Thời điểm can thiệp (Timing Cohort G) *
          </label>
          <select
            value={timingQid}
            onChange={(e) => setTimingQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến thời điểm can thiệp G --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Nhóm đối chứng so sánh (Control Group)
          </label>
          <select
            value={controlGroupType}
            onChange={(e) => setControlGroupType(e.target.value as any)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="never_treated">Nhóm chưa từng can thiệp (Never-treated)</option>
            <option value="not_yet_treated">Nhóm chưa can thiệp tại t (Not-yet-treated)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi làm sạch dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="all">Tất cả quan sát</option>
            <option value="verified_clean">Chỉ mẫu đã xác thực sạch</option>
          </select>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={handleRun}
          disabled={loading}
          className="inline-flex items-center px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm rounded-lg shadow-sm transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              Đang ước lượng Staggered DiD...
            </>
          ) : (
            'Thực thi Ước lượng Staggered DiD'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
          <strong>Lỗi ước lượng:</strong> {error}
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && diag && (
        <div className="mt-6 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl">
              <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wide">
                Tác động Gộp Overall ATT (\u03c4_CS)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-emerald-900">
                  {diag.overall_att.toFixed(4)}
                </span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  diag.is_statistically_significant
                    ? 'bg-emerald-200 text-emerald-900'
                    : 'bg-slate-200 text-slate-700'
                }`}>
                  p = {diag.overall_p_value < 0.001 ? '< 0.001' : diag.overall_p_value.toFixed(4)}
                </span>
              </div>
              <p className="text-xs text-emerald-700 mt-1">
                SE: {diag.overall_se.toFixed(4)} | 95% CI: [{diag.ci_lower_95.toFixed(3)}, {diag.ci_upper_95.toFixed(3)}]
              </p>
            </div>

            <div className="p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl">
              <span className="text-xs font-semibold text-indigo-800 uppercase tracking-wide">
                Kiểm định Xu hướng Song song
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-indigo-900">
                  p = {diag.pre_trends_p_value.toFixed(4)}
                </span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  diag.parallel_trends_supported
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-rose-100 text-rose-800'
                }`}>
                  {diag.parallel_trends_supported ? 'Thỏa mãn (Valid)' : 'Bác bỏ'}
                </span>
              </div>
              <p className="text-xs text-indigo-700 mt-1">
                Wald \u03c7\u00b2: {diag.pre_trends_wald_stat.toFixed(2)} | Giả định trước can thiệp
              </p>
            </div>

            <div className="p-4 bg-purple-50/70 border border-purple-200 rounded-xl">
              <span className="text-xs font-semibold text-purple-800 uppercase tracking-wide">
                Độ lệch TWFE Bias Gap
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-purple-900">
                  {diag.twfe_bias_gap.toFixed(4)}
                </span>
              </div>
              <p className="text-xs text-purple-700 mt-1">
                Hệ số OLS TWFE: {diag.twfe_naive_beta.toFixed(3)} (SE: {diag.twfe_naive_se.toFixed(3)})
              </p>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                Mẫu Bảng / Đoàn hệ Can thiệp
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  {diag.n_units}
                </span>
                <span className="text-xs text-slate-500">đơn vị / {diag.n_time_periods} đợt</span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {diag.n_cohorts} đoàn hệ | {diag.n_never_treated_units} đối chứng thuần
              </p>
            </div>
          </div>

          {/* Dual Panel SVG Chart */}
          {result.svg_visualization && (
            <div className="border border-slate-200 rounded-xl p-4 bg-white overflow-hidden shadow-sm">
              <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                Nghiên cứu Biến cố Động ATT(e) &amp; Phân rã Trọng số Goodman-Bacon
              </h4>
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-slate-50/50 rounded-lg"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Sub-tabs: Event Study vs Group-Time vs Bacon Decomposition */}
          <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
            <div className="flex border-b border-slate-200 bg-slate-50 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('event_study')}
                className={`px-4 py-3 border-b-2 transition-colors ${
                  activeTab === 'event_study'
                    ? 'border-emerald-500 text-emerald-700 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Hiệu ứng Biến cố Động ATT(e)
              </button>
              <button
                onClick={() => setActiveTab('group_time')}
                className={`px-4 py-3 border-b-2 transition-colors ${
                  activeTab === 'group_time'
                    ? 'border-emerald-500 text-emerald-700 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Chi tiết Nhóm - Thời điểm ATT(g, t)
              </button>
              <button
                onClick={() => setActiveTab('bacon')}
                className={`px-4 py-3 border-b-2 transition-colors ${
                  activeTab === 'bacon'
                    ? 'border-emerald-500 text-emerald-700 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Phân rã Goodman-Bacon (2x2 DiD)
              </button>
            </div>

            <div className="p-4">
              {activeTab === 'event_study' && result.event_study_effects && (
                <div className="overflow-x-auto max-h-64">
                  <table className="min-w-full divide-y divide-slate-200 text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold uppercase">
                      <tr>
                        <th className="px-4 py-2 text-left">Thời gian biến cố (e = t - g)</th>
                        <th className="px-4 py-2 text-right">Ước lượng ATT(e)</th>
                        <th className="px-4 py-2 text-right">Sai số chuẩn (SE)</th>
                        <th className="px-4 py-2 text-right">Giá trị p</th>
                        <th className="px-4 py-2 text-right">Khoảng tin cậy 95%</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {result.event_study_effects.map((item, idx) => (
                        <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                          <td className="px-4 py-1.5 font-medium">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              item.is_pre_period ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'
                            }`}>
                              {item.is_pre_period ? `Tiền can thiệp (${item.event_time})` : `Hậu can thiệp (+${item.event_time})`}
                            </span>
                          </td>
                          <td className="px-4 py-1.5 text-right font-mono font-bold">{item.att.toFixed(4)}</td>
                          <td className="px-4 py-1.5 text-right font-mono text-slate-500">{item.se.toFixed(4)}</td>
                          <td className="px-4 py-1.5 text-right font-mono">
                            <span className={item.p_value < 0.05 ? 'text-emerald-600 font-bold' : 'text-slate-500'}>
                              {item.p_value < 0.001 ? '< 0.001' : item.p_value.toFixed(4)}
                            </span>
                          </td>
                          <td className="px-4 py-1.5 text-right font-mono text-slate-600">
                            [{item.ci_lower_95.toFixed(3)}, {item.ci_upper_95.toFixed(3)}]
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'group_time' && result.group_time_effects && (
                <div className="overflow-x-auto max-h-64">
                  <table className="min-w-full divide-y divide-slate-200 text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold uppercase">
                      <tr>
                        <th className="px-4 py-2 text-left">Đoàn hệ (g)</th>
                        <th className="px-4 py-2 text-left">Thời điểm (t)</th>
                        <th className="px-4 py-2 text-right">ATT(g, t)</th>
                        <th className="px-4 py-2 text-right">SE</th>
                        <th className="px-4 py-2 text-right">Giá trị p</th>
                        <th className="px-4 py-2 text-right">Mẫu treated / control</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {result.group_time_effects.map((item, idx) => (
                        <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                          <td className="px-4 py-1.5 font-medium">Đoàn hệ g = {item.cohort_g}</td>
                          <td className="px-4 py-1.5 text-slate-600">t = {item.calendar_time_t}</td>
                          <td className="px-4 py-1.5 text-right font-mono font-bold">{item.att.toFixed(4)}</td>
                          <td className="px-4 py-1.5 text-right font-mono text-slate-500">{item.se.toFixed(4)}</td>
                          <td className="px-4 py-1.5 text-right font-mono">{item.p_value.toFixed(4)}</td>
                          <td className="px-4 py-1.5 text-right font-mono text-slate-500">{item.n_treated} / {item.n_control}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'bacon' && result.bacon_decomposition && (
                <div className="space-y-3">
                  <div className="p-3 bg-purple-50 rounded-lg text-xs text-purple-800 flex justify-between items-center">
                    <span>Tổng số phép so sánh 2x2: <strong>{result.bacon_decomposition.n_comparisons}</strong></span>
                    <span>Tỷ lệ trọng số âm tiềm ẩn: <strong>{result.bacon_decomposition.pct_negative_weights}%</strong></span>
                  </div>
                  <div className="overflow-x-auto max-h-56">
                    <table className="min-w-full divide-y divide-slate-200 text-xs">
                      <thead className="bg-slate-100 text-slate-600 font-semibold uppercase">
                        <tr>
                          <th className="px-4 py-2 text-left">Phân loại so sánh</th>
                          <th className="px-4 py-2 text-left">Nhóm can thiệp vs Đối chứng</th>
                          <th className="px-4 py-2 text-right">Ước lượng 2x2</th>
                          <th className="px-4 py-2 text-right">Trọng số phân rã</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {result.bacon_decomposition.components.map((c, idx) => (
                          <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                            <td className="px-4 py-1.5 font-medium text-slate-800">{c.comparison_type}</td>
                            <td className="px-4 py-1.5 text-slate-600 font-mono">g={c.group_k} vs {c.group_u}</td>
                            <td className="px-4 py-1.5 text-right font-mono font-bold">{c.estimate.toFixed(4)}</td>
                            <td className="px-4 py-1.5 text-right font-mono text-purple-700">{((c.weight_share || 0) * 100).toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* APA 7th Scientific Narrative */}
          {result.apa_narrative && (
            <div className="p-5 bg-gradient-to-r from-slate-50 to-indigo-50/30 border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"></path>
                  </svg>
                  Tường thuật Khoa học Chuẩn APA 7th (Academic Findings Report)
                </h4>
                <button
                  onClick={() => navigator.clipboard.writeText(result.apa_narrative || '')}
                  className="text-xs text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
                >
                  Sao chép văn bản
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-serif whitespace-pre-line bg-white/70 p-3 rounded-lg border border-slate-200/80">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
