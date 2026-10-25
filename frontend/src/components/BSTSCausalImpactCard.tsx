import React, { useState } from 'react';
import { api } from '../api/client';
import { BSTSCausalImpactResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface BSTSCausalImpactCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const BSTSCausalImpactCard: React.FC<BSTSCausalImpactCardProps> = ({
  surveyId,
  questions
}) => {
  const [timeQId, setTimeQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [interventionTime, setInterventionTime] = useState<string>('');
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BSTSCausalImpactResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleToggleCovariate = (qId: string) => {
    if (covariateQIds.includes(qId)) {
      setCovariateQIds(covariateQIds.filter(id => id !== qId));
    } else {
      setCovariateQIds([...covariateQIds, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!timeQId) {
      setError('Vui lòng chọn câu hỏi mốc thời gian / chuỗi kỳ khảo sát (Time / Period Question).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả chuỗi thời gian (Outcome Time Series Y).');
      return;
    }
    if (!interventionTime.trim()) {
      setError('Vui lòng nhập mốc thời gian bắt đầu can thiệp / sự kiện (Intervention Time Point).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const parsedTime = isNaN(Number(interventionTime.trim()))
        ? interventionTime.trim()
        : Number(interventionTime.trim());

      const res = await api.runBSTSCausalImpact(surveyId, {
        time_question_id: timeQId,
        outcome_question_id: outcomeQId,
        intervention_time: parsedTime,
        covariate_question_ids: covariateQIds.length > 0 ? covariateQIds : undefined,
        scope
      });

      setResult(res);
      if (res.status === 'insufficient_data') {
        setError(res.message || 'Không đủ dữ liệu chuỗi thời gian trước can thiệp để mô hình hóa trạng thái.');
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích BSTS Causal Impact.');
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
          <span className="p-2 bg-indigo-50 text-indigo-600 rounded-lg font-bold text-sm">
            BSTS
          </span>
          <div>
            <h3 className="text-lg font-bold text-slate-800">
              Bayesian Structural Time Series (BSTS) & Causal Impact
            </h3>
            <p className="text-xs text-slate-500">
              Ước lượng tác động nhân quả trên chuỗi thời gian bằng Lọc Kalman & Mô hình Không gian Trạng thái Bayes (Brodersen et al., 2015; Harvey, 1989).
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Time Variable */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Mốc thời gian / Chuỗi kỳ (Time)
          </label>
          <select
            value={timeQId}
            onChange={e => setTimeQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn mốc thời gian --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Variable */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kết quả theo dõi (Outcome Y)
          </label>
          <select
            value={outcomeQId}
            onChange={e => setOutcomeQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Intervention Time Point */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Thời điểm can thiệp (Intervention Time)
          </label>
          <input
            type="text"
            placeholder="VD: 2024-Q2 hoặc 10"
            value={interventionTime}
            onChange={e => setInterventionTime(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Optional Covariates & Scope */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Chuỗi kiểm soát / Đồng biến ngoại sinh (Tùy chọn - Synthetic Covariates)
          </label>
          <div className="max-h-28 overflow-y-auto border border-slate-200 rounded-lg p-2 space-y-1 bg-slate-50">
            {numericQuestions.filter(q => q.id !== outcomeQId && q.id !== timeQId).map(q => (
              <label key={q.id} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={covariateQIds.includes(q.id)}
                  onChange={() => handleToggleCovariate(q.id)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="truncate">{q.title}</span>
              </label>
            ))}
            {numericQuestions.filter(q => q.id !== outcomeQId && q.id !== timeQId).length === 0 && (
              <p className="text-xs text-slate-400 italic">Không có biến số phụ trợ nào khác.</p>
            )}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Phạm vi kiểm định dữ liệu (Data Cleaning Scope)
          </label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as 'all' | 'verified_clean')}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">Toàn bộ mẫu khảo sát (All Responses)</option>
            <option value="verified_clean">Chỉ mẫu đã kiểm định hợp lệ (Verified Clean Data Only)</option>
          </select>
          <p className="text-xs text-slate-400 mt-1">
            Khuyến nghị chọn "Chỉ mẫu đã kiểm định hợp lệ" để triệt tiêu nhiễu mẫu ảo và bất thường chuỗi thời gian.
          </p>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-lg transition-colors shadow-sm disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Đang giải không gian trạng thái Kalman...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Ước lượng Tác động Nhân quả (BSTS)</span>
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
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Tác động Điểm TB (Pointwise)</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.avg_pointwise_effect !== undefined
                  ? (result.avg_pointwise_effect >= 0 ? '+' : '') +
                    result.avg_pointwise_effect.toFixed(3)
                  : '--'}
              </div>
              <span className="text-[11px] text-slate-400">
                Kỳ can thiệp: {result.post_periods_count} mốc
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Tác động Tích lũy (Cumulative)</span>
              <div className="text-xl font-bold text-indigo-700 mt-1">
                {result.cumulative_effect !== undefined
                  ? (result.cumulative_effect >= 0 ? '+' : '') +
                    result.cumulative_effect.toFixed(2)
                  : '--'}
              </div>
              <span className="text-[11px] text-slate-400">
                Tổng biến thiên hậu can thiệp
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Tác động Tương đối (%)</span>
              <div
                className={`text-xl font-bold mt-1 ${
                  (result.relative_effect_pct || 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {result.relative_effect_pct !== undefined
                  ? (result.relative_effect_pct >= 0 ? '+' : '') +
                    result.relative_effect_pct.toFixed(2) +
                    '%'
                  : '--'}
              </div>
              <span className="text-[11px] text-slate-400">
                So với đối thực tế cơ sở
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Hậu nghiệm p-value</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.posterior_tail_p_value !== undefined
                  ? result.posterior_tail_p_value.toFixed(4)
                  : '--'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  result.is_significant ? 'text-emerald-600' : 'text-amber-600'
                }`}
              >
                {result.is_significant ? 'Ý nghĩa (p < 0.05)' : 'Chưa có ý nghĩa (p >= 0.05)'}
              </span>
            </div>
          </div>

          {/* Tri-Panel SVG Chart */}
          {result.svg_chart && (
            <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Đồ thị Động học Nhân quả 3 Tầng (Tri-Panel Causal Trajectory)
                </span>
                <span className="text-[11px] text-slate-400">
                  Panel 1: Thực tế vs Đối thực tế (CI 95%) | Panel 2: Điểm thời gian | Panel 3: Tích lũy
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Detailed Trajectory Table */}
          {result.trajectory && result.trajectory.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Bảng Chuỗi Thời gian Động học Thực tế & Ước lượng Đối thực tế
              </span>
              <div className="max-h-64 overflow-y-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold sticky top-0 border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Thời kỳ (t)</th>
                      <th className="p-2.5">Thực tế (Yt)</th>
                      <th className="p-2.5">Ước tính (Y_hat)</th>
                      <th className="p-2.5">Khoảng tin cậy 95%</th>
                      <th className="p-2.5">Tác động điểm (delta_t)</th>
                      <th className="p-2.5">Tác động tích lũy (Delta)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.trajectory.map((row, idx) => (
                      <tr
                        key={idx}
                        className={`hover:bg-slate-50 ${
                          String(row.period) === String(result.intervention_time)
                            ? 'bg-indigo-50/50 font-medium'
                            : ''
                        }`}
                      >
                        <td className="p-2.5 text-slate-800">
                          {row.period}
                          {String(row.period) === String(result.intervention_time) && (
                            <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded text-[10px]">
                              Can thiệp
                            </span>
                          )}
                        </td>
                        <td className="p-2.5 text-slate-700">{row.actual.toFixed(2)}</td>
                        <td className="p-2.5 text-slate-700">{row.counterfactual.toFixed(2)}</td>
                        <td className="p-2.5 text-slate-500 font-mono text-[11px]">
                          [{row.ci_95_lower.toFixed(2)}, {row.ci_95_upper.toFixed(2)}]
                        </td>
                        <td
                          className={`p-2.5 font-semibold ${
                            row.pointwise_impact > 0
                              ? 'text-emerald-600'
                              : row.pointwise_impact < 0
                              ? 'text-rose-600'
                              : 'text-slate-500'
                          }`}
                        >
                          {row.pointwise_impact > 0 ? '+' : ''}
                          {row.pointwise_impact.toFixed(2)}
                        </td>
                        <td className="p-2.5 text-indigo-600 font-medium">
                          {row.cumulative_impact > 0 ? '+' : ''}
                          {row.cumulative_impact.toFixed(2)}
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
                  className="text-xs text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
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
