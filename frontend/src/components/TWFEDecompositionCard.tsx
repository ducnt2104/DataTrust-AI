import React, { useState } from 'react';
import {
  TWFEDecompositionResult,
  TWFEDecompositionRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  GitCompare,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertTriangle,
  AlertCircle,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Sliders,
  Layers,
  Activity,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Percent,
  History
} from 'lucide-react';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface Props {
  surveyId: string;
  questions: QuestionSummary[];
}

export const TWFEDecompositionCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [unitQId, setUnitQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<TWFEDecompositionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleToggleCovariate = (qId: string) => {
    if (selectedCovariates.includes(qId)) {
      setSelectedCovariates(selectedCovariates.filter(id => id !== qId));
    } else {
      setSelectedCovariates([...selectedCovariates, qId]);
    }
  };

  const handleRun = async () => {
    if (!outcomeQId || !treatmentQId || !unitQId || !timeQId) {
      setError('Vui lòng chọn biến kết quả, biến can thiệp, biến đơn vị và biến chuỗi thời gian.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: TWFEDecompositionRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      unit_question_id: unitQId,
      time_question_id: timeQId,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      alpha_level: 0.05,
      scope
    };

    try {
      const res = await api.runTWFEDecomposition(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể phân rã mô hình Two-Way Fixed Effects.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API TWFE Decomposition.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const summary = result?.overall_summary;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-amber-50 dark:bg-amber-950/60 rounded-lg text-amber-600 dark:text-amber-400">
              <GitCompare className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Phân rã Two-Way Fixed Effects &amp; Chẩn đoán Trọng số Âm (de Chaisemartin 2020)
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            de Chaisemartin &amp; D'Haultfœuille (2020 AER; 2022 Restud) · Negative Weights &omega;_(i,t) · Minimal Heterogeneity SD &sigma;_fe · Robust DID_M Switcher Estimator
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
            AER 2020 Core Causal
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
            DID_M Robust
          </span>
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Outcome Y */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến kết quả Y (Outcome)
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn biến số đo lường --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Treatment D */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến can thiệp D (Treatment 0/1)
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn biến chỉ thị chính sách (0/1) --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Unit Identifier */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Mã định danh đơn vị (Unit i)
          </label>
          <select
            value={unitQId}
            onChange={(e) => setUnitQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn đơn vị / chi nhánh / cá thể --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Time Wave */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Chuỗi thời gian (Time Period t)
          </label>
          <select
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn đợt sóng / tháng / quý --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Covariates & Scope */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Covariates Checklist */}
        <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
          <span className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            Biến kiểm soát tùy chọn (Covariates X):
          </span>
          <div className="max-h-24 overflow-y-auto space-y-1 pr-1">
            {numericQuestions
              .filter(q => q.id !== outcomeQId && q.id !== treatmentQId && q.id !== unitQId && q.id !== timeQId)
              .map((q) => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCovariates.includes(q.id)}
                    onChange={() => handleToggleCovariate(q.id)}
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
          </div>
        </div>

        {/* Scope Selector */}
        <div className="flex flex-col justify-between">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Phạm vi mẫu phân tích (Scope)
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
            >
              <option value="all">Tất cả phản hồi hợp lệ (All)</option>
              <option value="verified_clean">Chỉ mẫu đã kiểm định sạch (Verified Clean)</option>
            </select>
          </div>

          <div className="flex justify-end pt-3">
            <button
              onClick={handleRun}
              disabled={loading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  Đang phân rã trọng số TWFE...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Phân rã TWFE &amp; Kiểm định DID_M
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 rounded-lg text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && summary && (
        <div className="space-y-6 pt-4 border-t border-slate-200 dark:border-slate-800">
          {/* Diagnostic Alert Banner */}
          <div
            className={`p-4 rounded-xl border flex items-start gap-3 text-xs leading-relaxed ${
              summary.twfe_validity_status === 'CRITICAL_BIAS_RISK'
                ? 'bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900 text-red-800 dark:text-red-200'
                : summary.twfe_validity_status === 'MODERATE_BIAS_RISK'
                ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-200'
                : 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-200'
            }`}
          >
            {summary.twfe_validity_status === 'CRITICAL_BIAS_RISK' ? (
              <ShieldAlert className="w-5 h-5 flex-shrink-0 text-red-600 dark:text-red-400 mt-0.5" />
            ) : summary.twfe_validity_status === 'MODERATE_BIAS_RISK' ? (
              <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            ) : (
              <ShieldCheck className="w-5 h-5 flex-shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5" />
            )}
            <div>
              <div className="font-bold flex items-center gap-2">
                <span>{summary.twfe_validity_status.replace(/_/g, ' ')}</span>
                <span className="font-normal text-[11px] opacity-80">
                  (W- = {summary.sum_negative_weights.toFixed(3)} | {summary.pct_negative_cells.toFixed(1)}% treated cells)
                </span>
              </div>
              <p className="mt-1">{summary.risk_interpretation}</p>
            </div>
          </div>

          {/* Key Metric Tiles */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                TWFE OLS &beta;
              </span>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                {summary.beta_twfe > 0 ? `+${summary.beta_twfe.toFixed(3)}` : summary.beta_twfe.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                SE: {summary.se_twfe.toFixed(3)} (p = {summary.p_value_twfe.toFixed(3)})
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Robust DID_M (Thuần nhất)
              </span>
              <span className={`text-lg font-bold ${summary.did_m_estimate >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                {summary.did_m_estimate > 0 ? `+${summary.did_m_estimate.toFixed(3)}` : summary.did_m_estimate.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                SE: {summary.se_did_m.toFixed(3)} (p = {summary.p_value_did_m.toFixed(3)})
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Tổng Trọng số Âm (W-)
              </span>
              <span className={`text-lg font-bold ${summary.sum_negative_weights < -0.1 ? 'text-red-600 dark:text-red-400' : 'text-slate-700 dark:text-slate-300'}`}>
                {summary.sum_negative_weights.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {summary.n_negative_cells} ô ({summary.pct_negative_cells.toFixed(1)}%)
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                &sigma;_fe (Ngưỡng Đảo Dấu)
              </span>
              <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                {summary.minimal_heterogeneity_sd_sigma_fe.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                SD cần thiết để &beta;_fe ngược dấu
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Placebo Xu hướng Song song
              </span>
              <span className={`text-lg font-bold ${summary.parallel_trends_pass ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                {summary.parallel_trends_pass ? 'Đạt (Pass)' : 'Vi phạm'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                p = {summary.placebo_p_value.toFixed(3)}
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 p-2">
              <div
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                className="w-full flex justify-center"
              />
            </div>
          )}

          {/* Detailed Tables: Period Switchers & Negative Weights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Period Switchers DID_M */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <History className="w-4 h-4 text-indigo-500" />
                Hiệu ứng Chuyển trạng thái theo Đợt sóng (Switchers DID_M,t)
              </h4>
              <div className="overflow-x-auto max-h-60">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-750 text-slate-600 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2">Kỳ (t)</th>
                      <th className="p-2 text-right">Switchers</th>
                      <th className="p-2 text-right">Stayers</th>
                      <th className="p-2 text-right">DID_M,t</th>
                      <th className="p-2 text-right">Placebo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {result.period_switchers && result.period_switchers.length > 0 ? (
                      result.period_switchers.map((ps, idx) => (
                        <tr key={idx} className="hover:bg-slate-100/50 dark:hover:bg-slate-700/40">
                          <td className="p-2 font-medium text-slate-800 dark:text-slate-200">
                            {ps.period}
                          </td>
                          <td className="p-2 text-right font-mono text-slate-600 dark:text-slate-300">
                            {ps.n_switchers}
                          </td>
                          <td className="p-2 text-right font-mono text-slate-600 dark:text-slate-300">
                            {ps.n_stayers}
                          </td>
                          <td className={`p-2 text-right font-mono font-bold ${ps.did_m_effect >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                            {ps.did_m_effect > 0 ? `+${ps.did_m_effect.toFixed(2)}` : ps.did_m_effect.toFixed(2)}
                          </td>
                          <td className="p-2 text-right font-mono text-slate-500">
                            {ps.placebo_pretrend_effect !== null ? ps.placebo_pretrend_effect?.toFixed(2) : '-'}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="p-4 text-center text-slate-400">
                          Không phát hiện nhóm đơn vị chuyển trạng thái (switchers) giữa các kỳ liên tiếp.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Top Negative Weights Table */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                Các Ô Nhận Trọng số Âm Nghiêm trọng nhất (&omega;_(i,t) &lt; 0)
              </h4>
              <div className="overflow-x-auto max-h-60">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-750 text-slate-600 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2">Đơn vị (Unit i)</th>
                      <th className="p-2">Kỳ (Time t)</th>
                      <th className="p-2 text-right">Trọng số &omega;</th>
                      <th className="p-2 text-right">Tỷ trọng (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {result.top_negative_weights && result.top_negative_weights.length > 0 ? (
                      result.top_negative_weights.map((nw, idx) => (
                        <tr key={idx} className="hover:bg-slate-100/50 dark:hover:bg-slate-700/40">
                          <td className="p-2 font-medium text-slate-800 dark:text-slate-200">
                            {nw.unit}
                          </td>
                          <td className="p-2 font-mono text-slate-600 dark:text-slate-300">
                            {nw.time_period}
                          </td>
                          <td className="p-2 text-right font-mono font-bold text-red-600 dark:text-red-400">
                            {nw.weight.toFixed(4)}
                          </td>
                          <td className="p-2 text-right font-mono text-red-500">
                            {nw.weight_pct.toFixed(2)}%
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-emerald-600 dark:text-emerald-400 font-medium">
                          Tuyệt vời: Không có ô nào nhận trọng số âm đáng kể (&omega; &ge; 0)!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* APA Narrative Block */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-750 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  Bản tường trình Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyAPA}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-600 dark:text-amber-400 hover:underline"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-serif italic">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
