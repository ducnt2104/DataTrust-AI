import React, { useState } from 'react';
import { api } from '../api/client';
import { ExtremeBoundsResult, ExtremeBoundsRequest } from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface Props {
  surveyId: string;
  questions: QuestionOption[];
}

export const ExtremeBoundsAnalysisCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [focusQId, setFocusQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [candidateQIds, setCandidateQIds] = useState<string[]>([]);
  const [freeQIds, setFreeQIds] = useState<string[]>([]);
  const [maxControls, setMaxControls] = useState<number>(4);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ExtremeBoundsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Filter numeric questions
  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'likert'
  );

  const toggleCandidate = (id: string) => {
    if (candidateQIds.includes(id)) {
      setCandidateQIds(candidateQIds.filter((x) => x !== id));
    } else {
      setCandidateQIds([...candidateQIds, id]);
    }
  };

  const handleRun = async () => {
    if (!focusQId || !outcomeQId) {
      setError('Vui lòng chọn cả biến trọng tâm (Focus P) và biến kết quả (Outcome Y).');
      return;
    }
    if (focusQId === outcomeQId) {
      setError('Biến trọng tâm và biến kết quả không được trùng nhau.');
      return;
    }
    if (candidateQIds.length === 0) {
      setError('Cần chọn tối thiểu 1 biến kiểm soát ứng viên (Candidate Controls).');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const payload: ExtremeBoundsRequest = {
        focus_question_id: focusQId,
        outcome_question_id: outcomeQId,
        candidate_question_ids: candidateQIds,
        free_question_ids: freeQIds,
        max_controls_per_model: maxControls,
        scope,
      };
      const res = await api.runExtremeBoundsAnalysis(surveyId, payload);
      if (res.status === 'error' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không thể tính toán phân tích cực trị EBA.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích EBA.');
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

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg text-lg font-bold">
              ⚡ EBA
            </span>
            <h3 className="text-xl font-bold text-slate-100">
              Extreme Bound Analysis (EBA) Specification Curve Engine
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Kiểm định độ nhạy &amp; tính vững chắc chống thao túng khai thác dữ liệu (p-hacking) theo tiêu chuẩn Edward Leamer (1983) &amp; Xavier Sala-i-Martin (1997).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
          >
            <option value="all">Toàn bộ phản hồi (Tất cả)</option>
            <option value="verified_clean">Chỉ dữ liệu đã xác minh sạch</option>
          </select>
          <button
            onClick={handleRun}
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow transition-all flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Đang quét mô hình...</span>
              </>
            ) : (
              <>
                <span>▶ Quét Toàn Bộ Tổ Hợp Mô Hình</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Selectors Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-5 bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            1. Biến Trọng tâm (Focus Variable P) <span className="text-rose-400">*</span>
          </label>
          <select
            value={focusQId}
            onChange={(e) => setFocusQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500"
          >
            <option value="">-- Chọn biến độc lập trọng tâm --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            2. Biến Kết quả (Outcome Variable Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500"
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
            3. Giới hạn số biến kiểm soát / mô hình
          </label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={1}
              max={6}
              value={maxControls}
              onChange={(e) => setMaxControls(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <span className="text-xs font-bold text-indigo-400 bg-indigo-950/80 px-2.5 py-1 rounded border border-indigo-800">
              {maxControls} biến
            </span>
          </div>
        </div>

        {/* Candidate Controls Multiselect */}
        <div className="md:col-span-3 mt-2">
          <label className="block text-xs font-semibold text-slate-300 mb-2">
            4. Bể Biến Kiểm soát Ứng viên (Candidate Controls Pool Z) — Tổ hợp sinh không gian mô hình:
          </label>
          <div className="flex flex-wrap gap-2">
            {numericQuestions
              .filter((q) => q.id !== focusQId && q.id !== outcomeQId)
              .map((q) => {
                const isSelected = candidateQIds.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleCandidate(q.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                      isSelected
                        ? 'bg-indigo-600/30 text-indigo-300 border-indigo-500 shadow-sm'
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
      {result && result.summary && (
        <div className="space-y-6 mt-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Leamer Verdict */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Tiêu Chuẩn Leamer (1983)
              </span>
              <div className="mt-1 flex items-center gap-2">
                <span
                  className={`text-sm font-bold px-2.5 py-0.5 rounded-full ${
                    result.summary.leamer_verdict === 'ROBUST_POSITIVE'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : result.summary.leamer_verdict === 'ROBUST_NEGATIVE'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  {result.summary.leamer_verdict}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Khoảng cực trị: [{result.summary.leamer_lower_bound.toFixed(3)},{' '}
                {result.summary.leamer_upper_bound.toFixed(3)}]
              </p>
            </div>

            {/* Sala-i-Martin Gauge */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Sala-i-Martin CDF(0)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-indigo-400">
                  {(result.summary.sala_i_martin_cdf * 100).toFixed(1)}%
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    result.summary.sala_i_martin_verdict === 'ROBUST'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  {result.summary.sala_i_martin_verdict}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Trọng số R²: {(result.summary.sala_i_martin_weighted_cdf * 100).toFixed(1)}%
              </p>
            </div>

            {/* Models Evaluated */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Mô hình đã quét (OLS)
              </span>
              <div className="mt-1 text-2xl font-extrabold text-slate-100">
                {result.summary.total_models_evaluated}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Có ý nghĩa (p&lt;.05): {(result.summary.significant_models_fraction * 100).toFixed(1)}%
              </p>
            </div>

            {/* Beta Spectrum */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Hệ số Trung bình β_mean
              </span>
              <div className="mt-1 text-2xl font-extrabold text-emerald-400">
                {result.summary.mean_beta.toFixed(3)}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Min: {result.summary.min_beta.toFixed(3)} | Max: {result.summary.max_beta.toFixed(3)}
              </p>
            </div>
          </div>

          {/* SVG Chart Vector Display */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-hidden shadow-inner">
              <div
                className="w-full flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Extreme Model Controls Table */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">
              Mô hình Biên Cực Trị (Extreme Boundary Models)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-900/90 rounded-lg border border-slate-800">
                <span className="font-semibold text-rose-400">Mô hình cho Hệ số Thấp nhất (β_min):</span>
                <div className="mt-1 text-slate-300 font-mono">
                  β = {result.summary.min_beta.toFixed(4)}
                </div>
                <div className="mt-1 text-slate-400 text-[11px]">
                  Biến kiểm soát: {result.summary.min_beta_model_controls.length > 0
                    ? result.summary.min_beta_model_controls.join(', ')
                    : '(Không có biến kiểm soát - Hồi quy đơn)'}
                </div>
              </div>

              <div className="p-3 bg-slate-900/90 rounded-lg border border-slate-800">
                <span className="font-semibold text-emerald-400">Mô hình cho Hệ số Cao nhất (β_max):</span>
                <div className="mt-1 text-slate-300 font-mono">
                  β = {result.summary.max_beta.toFixed(4)}
                </div>
                <div className="mt-1 text-slate-400 text-[11px]">
                  Biến kiểm soát: {result.summary.max_beta_model_controls.length > 0
                    ? result.summary.max_beta_model_controls.join(', ')
                    : '(Không có biến kiểm soát - Hồi quy đơn)'}
                </div>
              </div>
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
