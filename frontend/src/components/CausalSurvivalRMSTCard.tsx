import React, { useState } from 'react';
import {
  Clock,
  Activity,
  Layers,
  Sliders,
  Copy,
  Check,
  Download,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  Percent,
  Calendar,
  Sparkles,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react';
import { api } from '../api/client';
import type {
  CausalSurvivalRMSTRequest,
  CausalSurvivalRMSTResult
} from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface CausalSurvivalRMSTCardProps {
  surveyId: string;
  questions: QuestionOption[];
}

export const CausalSurvivalRMSTCard: React.FC<CausalSurvivalRMSTCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'likert'].includes(q.question_type)
  );

  const [timeQId, setTimeQId] = useState<string>(
    numericQuestions[0]?.id || ''
  );
  const [eventQId, setEventQId] = useState<string>(
    numericQuestions[1]?.id || numericQuestions[0]?.id || ''
  );
  const [treatmentQId, setTreatmentQId] = useState<string>(
    numericQuestions[2]?.id || numericQuestions[0]?.id || ''
  );
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [tauHorizon, setTauHorizon] = useState<string>('');
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalSurvivalRMSTResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const toggleCovariate = (id: string) => {
    setCovariateQIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!timeQId || !eventQId || !treatmentQId) {
      setError('Vui lòng chọn biến thời gian (T), biến sự kiện (Event), và biến can thiệp (Treatment).');
      return;
    }
    if (timeQId === eventQId || timeQId === treatmentQId || eventQId === treatmentQId) {
      setError('Các biến thời gian, sự kiện và can thiệp không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const parsedTau = tauHorizon ? parseFloat(tauHorizon) : undefined;
      const payload: CausalSurvivalRMSTRequest = {
        time_question_id: timeQId,
        event_question_id: eventQId,
        treatment_question_id: treatmentQId,
        covariate_question_ids: covariateQIds.filter(
          (id) => id !== timeQId && id !== eventQId && id !== treatmentQId
        ),
        tau_horizon: (parsedTau && !isNaN(parsedTau) && parsedTau > 0) ? parsedTau : undefined,
        alpha_level: alphaLevel,
        scope
      };

      const res = await api.runCausalSurvivalRMST(surveyId, payload);
      if (res.status === 'insufficient_data' || res.status === 'imbalanced_treatment' || res.status === 'ERROR') {
        setError(res.message || 'Lỗi phân tích Causal Survival RMST.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể kết nối đến máy chủ.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  const downloadSVG = () => {
    if (!result?.svg_visualization) return;
    const blob = new Blob([result.svg_visualization], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DataTrust_Causal_Survival_RMST_${surveyId}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-white tracking-tight">
                Causal Survival Analysis &amp; RMST Engine
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30">
                Royston &amp; Parmar (2013)
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-0.5">
              Counterfactual Restricted Mean Survival Time (RMST) free of proportional hazards assumptions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-teal-400" />
            Doubly Robust IPCW
          </span>
        </div>
      </div>

      {/* Input Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 bg-slate-900/50 p-5 rounded-xl border border-slate-700/50">
        {/* Time Variable T */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span>Survival / Tenure Time (T)</span>
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          </label>
          <select
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Event Indicator */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-amber-400">Event Indicator (1=Event, 0=Censored)</span>
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          </label>
          <select
            value={eventQId}
            onChange={(e) => setEventQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Treatment Indicator A */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-sky-400">Treatment Arm (1=Intervention, 0=Control)</span>
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Covariates Z Multi-select */}
        <div className="md:col-span-3 space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Baseline Confounder Covariates (X)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-36 overflow-y-auto p-2 bg-slate-800/70 border border-slate-700 rounded-lg">
            {numericQuestions
              .filter((q) => q.id !== timeQId && q.id !== eventQId && q.id !== treatmentQId)
              .map((q) => (
                <label
                  key={q.id}
                  className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer p-1.5 rounded hover:bg-slate-700/50"
                >
                  <input
                    type="checkbox"
                    checked={covariateQIds.includes(q.id)}
                    onChange={() => toggleCovariate(q.id)}
                    className="rounded border-slate-600 text-teal-600 focus:ring-teal-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
            {numericQuestions.filter((q) => q.id !== timeQId && q.id !== eventQId && q.id !== treatmentQId).length === 0 && (
              <span className="text-xs text-slate-500 italic p-1">Không có biến kiểm soát bổ sung</span>
            )}
          </div>
        </div>

        {/* Horizon Tau, Alpha, Scope, Run button */}
        <div className="md:col-span-3 flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800">
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5" />
              <span>Horizon (&tau;):</span>
              <input
                type="number"
                step="any"
                placeholder="Auto (90th pct)"
                value={tauHorizon}
                onChange={(e) => setTauHorizon(e.target.value)}
                className="w-28 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white placeholder-slate-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <span>Significance &alpha;:</span>
              <select
                value={alphaLevel}
                onChange={(e) => setAlphaLevel(Number(e.target.value))}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white"
              >
                <option value={0.01}>0.01 (99% CI)</option>
                <option value={0.05}>0.05 (95% CI)</option>
                <option value={0.10}>0.10 (90% CI)</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span>Scope:</span>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white"
              >
                <option value="all">Tất cả phản hồi</option>
                <option value="verified_clean">Đã kiểm định sạch (Clean only)</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-700 text-white text-sm font-semibold rounded-xl shadow-lg shadow-teal-600/30 transition-all flex items-center gap-2 ml-auto"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Đang phân tích RMST...</span>
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                <span>Ước Lượng RMST Nhân Quả</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6 pt-2">
          {/* 4 Highlight KPI Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Causal RMST Difference */}
            <div className="p-4 bg-slate-900/60 border border-teal-500/40 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Causal RMST Difference (&Delta;&mu;)</span>
                {result.causal_rmst_difference?.is_significant ? (
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-4 h-4 text-slate-500" />
                )}
              </div>
              <div className="text-2xl font-bold text-teal-300 tracking-tight">
                {(result.causal_rmst_difference?.estimate ?? 0) > 0 ? '+' : ''}{result.causal_rmst_difference?.estimate.toFixed(2)}
                <span className="text-xs text-slate-400 font-normal ml-1">time units</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>95% CI: [{result.causal_rmst_difference?.ci_95[0].toFixed(2)}, {result.causal_rmst_difference?.ci_95[1].toFixed(2)}]</span>
                <span className={result.causal_rmst_difference?.is_significant ? 'text-emerald-400 font-bold' : ''}>
                  p = {result.causal_rmst_difference?.p_value.toFixed(4)}
                </span>
              </div>
            </div>

            {/* Counterfactual RMST Means */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Counterfactual RMST (&tau; = {result.tau_horizon?.toFixed(1)})</span>
                <TrendingUp className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight flex items-baseline gap-2">
                <span className="text-sky-400">{result.rmst_treated?.toFixed(2)}</span>
                <span className="text-slate-500 text-sm">vs</span>
                <span className="text-amber-400">{result.rmst_control?.toFixed(2)}</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>Treated (N1={result.n_treated})</span>
                <span>Control (N0={result.n_control})</span>
              </div>
            </div>

            {/* RMST Ratio & RMTL Reduction */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>RMST Ratio / RMTL Reduction</span>
                <Percent className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-indigo-300 tracking-tight">
                {result.rmst_ratio?.toFixed(3)}x
              </div>
              <div className="text-[11px] text-emerald-400 mt-1 flex items-center justify-between font-semibold">
                <span>Time Lost (RMTL):</span>
                <span>{result.rmtl_metrics?.rmtl_reduction_pct.toFixed(1)}% reduction</span>
              </div>
            </div>

            {/* Milestone Survival at tau */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Milestone S(&tau;) Risk Diff</span>
                <Calendar className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-emerald-300 tracking-tight">
                {(result.milestone_survival_tau?.risk_difference ?? 0) > 0 ? '+' : ''}
                {((result.milestone_survival_tau?.risk_difference ?? 0) * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>S₁(&tau;): {((result.milestone_survival_tau?.survival_treated ?? 0) * 100).toFixed(1)}%</span>
                <span>S₀(&tau;): {((result.milestone_survival_tau?.survival_control ?? 0) * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-teal-400" />
                  Counterfactual Survival Curves S(t) &amp; Shaded RMST Gain
                </h4>
                <button
                  onClick={downloadSVG}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download SVG</span>
                </button>
              </div>
              <div
                className="w-full overflow-hidden rounded-xl border border-slate-700/80 bg-slate-900/60 p-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Milestone Trajectory Table */}
          {result.curve_points && result.curve_points.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-teal-400" />
                Milestone Survival Trajectory Table Across Follow-up Horizon [0, {result.tau_horizon?.toFixed(1)}]
              </h4>
              <div className="overflow-x-auto rounded-xl border border-slate-700/70">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="py-2.5 px-3">Time (t)</th>
                      <th className="py-2.5 px-3">Treated Survival S₁(t)</th>
                      <th className="py-2.5 px-3">Control Survival S₀(t)</th>
                      <th className="py-2.5 px-3">Survival Difference &Delta;S(t)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-900/40 font-mono">
                    {result.curve_points.map((pt, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 text-white font-bold">{pt.time.toFixed(1)}</td>
                        <td className="py-2 px-3 text-sky-400">{(pt.survival_treated * 100).toFixed(1)}%</td>
                        <td className="py-2 px-3 text-amber-400">{(pt.survival_control * 100).toFixed(1)}%</td>
                        <td className="py-2 px-3 font-semibold text-emerald-400">
                          {pt.survival_difference > 0 ? '+' : ''}{(pt.survival_difference * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Thuyết Minh Khoa Học (APA 7th Edition Standard)
                </span>
                <button
                  onClick={copyNarrative}
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded border border-slate-700 flex items-center gap-1.5 transition-colors"
                >
                  {copiedNarrative ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">Đã chép</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Sao chép APA</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-950/40 p-3 rounded-lg border border-slate-800/80">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
