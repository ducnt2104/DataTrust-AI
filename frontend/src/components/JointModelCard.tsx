import React, { useState } from 'react';
import { api } from '../api/client';
import { JointModelAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface JointModelCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const JointModelCard: React.FC<JointModelCardProps> = ({
  surveyId,
  questions
}) => {
  const [subjectQId, setSubjectQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [eventQId, setEventQId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JointModelAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const categoricalQuestions = questions.filter(q =>
    ['single_choice', 'boolean', 'yes_no', 'number'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!subjectQId) {
      setError('Vui lòng chọn câu hỏi định danh đối tượng / mã người trả lời (Subject ID).');
      return;
    }
    if (!timeQId) {
      setError('Vui lòng chọn câu hỏi mốc thời gian / làn sóng khảo sát (Time / Wave).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả dọc theo dõi (Longitudinal Outcome).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runJointModelAnalysis(surveyId, {
        subject_question_id: subjectQId,
        time_question_id: timeQId,
        outcome_question_id: outcomeQId,
        event_question_id: eventQId || undefined,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình liên kết Joint Model.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích Joint Modeling.');
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
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded-full">
              Longitudinal &amp; Survival Coupling
            </span>
            <span className="text-xs text-slate-400 font-mono">Wulfsohn &amp; Tsiatis (1997) • Henderson (2000) • Rizopoulos (2012)</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Joint Modeling of Longitudinal Trajectories &amp; Panel Attrition
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Mô hình hóa đồng thời quỹ đạo tăng trưởng tiềm ẩn (LMM) và nguy cơ rời bỏ khảo sát (Cox PH), hiệu chỉnh triệt để thiên lệch sống sót (Survivorship Bias) khi sự hao hụt mẫu có tính quy luật nội sinh.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Định danh đối tượng (Subject ID) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            value={subjectQId}
            onChange={(e) => setSubjectQId(e.target.value)}
          >
            <option value="">-- Chọn mã người trả lời --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Làn sóng / Mốc thời gian (Time / Wave) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
          >
            <option value="">-- Chọn mốc thời gian số --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến kết quả dọc (Outcome y) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
          >
            <option value="">-- Chọn điểm số đo lường --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Chỉ báo bỏ cuộc (Attrition Event - Tùy chọn)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            value={eventQId}
            onChange={(e) => setEventQId(e.target.value)}
          >
            <option value="">-- Tự động suy luận từ làn sóng cuối --</option>
            {categoricalQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-4">
          <label className="text-xs text-slate-400 flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="jm_scope"
              checked={scope === 'all'}
              onChange={() => setScope('all')}
              className="text-indigo-500 focus:ring-indigo-500 bg-slate-950 border-slate-700"
            />
            Toàn bộ phản hồi ({questions.length} câu)
          </label>
          <label className="text-xs text-slate-400 flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="jm_scope"
              checked={scope === 'verified_clean'}
              onChange={() => setScope('verified_clean')}
              className="text-indigo-500 focus:ring-indigo-500 bg-slate-950 border-slate-700"
            />
            Chỉ phản hồi đã làm sạch (Cleaned data)
          </label>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg shadow transition flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang ước lượng Joint Model...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Ước lượng Mô hình Liên kết JM
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
              <div className="text-xs text-slate-400">Số Đối tượng / Lượt đo</div>
              <div className="text-lg font-bold text-white mt-1">
                N = {result.sample_size}
              </div>
              <div className="text-xs text-slate-500">
                Tổng cộng {result.total_longitudinal_observations} lượt quan sát
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Hao hụt mẫu (Bỏ cuộc / Còn lại)</div>
              <div className="text-lg font-bold text-rose-400 mt-1">
                {result.events_attrited_count} / {result.censored_retained_count}
              </div>
              <div className="text-xs text-slate-500">
                Tỷ lệ thất thoát: {(((result.events_attrited_count || 0) / (result.sample_size || 1)) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Tham số Liên kết (Association α)</div>
              <div className="text-lg font-bold text-indigo-400 mt-1">
                α = {result.survival_submodel?.association_alpha?.toFixed(3)}
              </div>
              <div className="text-xs font-mono text-slate-400">
                p = {result.survival_submodel?.p_value?.toFixed(4)}
                {result.survival_submodel?.is_significant && (
                  <span className="text-indigo-400 font-bold ml-1">*</span>
                )}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Tỷ số Nguy cơ Hazard Ratio (HR)</div>
              <div className="text-lg font-bold text-amber-400 mt-1">
                HR = {result.survival_submodel?.hazard_ratio?.toFixed(3)}
              </div>
              <div className="text-xs font-mono text-slate-400">
                [{result.survival_submodel?.ci_95_lower?.toFixed(2)}, {result.survival_submodel?.ci_95_upper?.toFixed(2)}]
              </div>
            </div>
          </div>

          {/* Attrition Diagnosis Banner */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-start gap-3">
            <span className={`p-1.5 rounded-md border text-xs font-bold shrink-0 ${
              result.attrition_diagnostics?.is_non_ignorable
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
            }`}>
              {result.attrition_diagnostics?.is_non_ignorable ? 'Non-ignorable Attrition' : 'Ignorable Attrition (MAR)'}
            </span>
            <div>
              <div className="text-xs font-semibold text-white">
                Chẩn đoán Cơ chế Hao hụt Mẫu Khảo sát: {result.attrition_diagnostics?.is_non_ignorable ? 'Thất thoát mang tính thông tin / Phi ngẫu nhiên' : 'Thất thoát ngẫu nhiên (MAR)'}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {result.attrition_diagnostics?.interpretation}
              </p>
            </div>
          </div>

          {/* Submodels Summary Table */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-3">
                Phân mô hình Dọc (Longitudinal LMM Submodel)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300 font-mono">
                  <tbody className="divide-y divide-slate-800/60">
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Điểm chặn trung bình (Fixed Intercept β₀)</td>
                      <td className="py-2 text-right font-bold text-white">{result.longitudinal_submodel?.intercept_fixed?.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Tốc độ biến thiên (Fixed Slope β₁)</td>
                      <td className="py-2 text-right font-bold text-white">{result.longitudinal_submodel?.slope_fixed?.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Độ lệch chuẩn phần dư (Residual σₑ)</td>
                      <td className="py-2 text-right text-slate-300">{result.longitudinal_submodel?.residual_std_sigma_e?.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Độ lệch chuẩn ngẫu nhiên chặn (Random σ_b0)</td>
                      <td className="py-2 text-right text-indigo-400">{result.longitudinal_submodel?.random_intercept_std?.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Độ lệch chuẩn ngẫu nhiên dốc (Random σ_b1)</td>
                      <td className="py-2 text-right text-indigo-400">{result.longitudinal_submodel?.random_slope_std?.toFixed(4)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-3">
                Phân mô hình Sống sót (Survival Submodel with Latent Link)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300 font-mono">
                  <tbody className="divide-y divide-slate-800/60">
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Tham số liên kết (Association α)</td>
                      <td className="py-2 text-right font-bold text-indigo-400">{result.survival_submodel?.association_alpha?.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Sai số chuẩn (Standard Error SE_α)</td>
                      <td className="py-2 text-right text-slate-400">{result.survival_submodel?.se_alpha?.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Thống kê Wald (z-statistic)</td>
                      <td className="py-2 text-right text-slate-300">{result.survival_submodel?.z_statistic?.toFixed(3)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Mức ý nghĩa thống kê (p-value)</td>
                      <td className="py-2 text-right font-bold text-amber-400">{result.survival_submodel?.p_value?.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-400 font-sans">Tỷ số nguy cơ (Hazard Ratio HR)</td>
                      <td className="py-2 text-right font-bold text-rose-400">{result.survival_submodel?.hazard_ratio?.toFixed(3)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_chart && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2">
                Trực quan hóa Đồ thị Không gian Vector SVG Kép (Longitudinal Trajectories &amp; Survival Curves)
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
                <h4 className="text-sm font-semibold text-indigo-400 flex items-center gap-2">
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
