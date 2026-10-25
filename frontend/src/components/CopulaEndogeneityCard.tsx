import React, { useState } from 'react';
import {
  GitCommit,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Layers,
  ArrowRightLeft,
  Sliders,
  Copy,
  Check,
  Download,
  AlertCircle,
  HelpCircle,
  BarChart3,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import type {
  CopulaEndogeneityRequest,
  CopulaEndogeneityResult
} from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface CopulaEndogeneityCardProps {
  surveyId: string;
  questions: QuestionOption[];
}

export const CopulaEndogeneityCard: React.FC<CopulaEndogeneityCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'likert'].includes(q.question_type)
  );

  const [outcomeQId, setOutcomeQId] = useState<string>(
    numericQuestions[0]?.id || ''
  );
  const [endogenousQId, setEndogenousQId] = useState<string>(
    numericQuestions[1]?.id || numericQuestions[0]?.id || ''
  );
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [copulaFamily, setCopulaFamily] = useState<'gaussian' | 'clayton'>('gaussian');
  const [bootstrapReps, setBootstrapReps] = useState<number>(100);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CopulaEndogeneityResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const toggleCovariate = (id: string) => {
    setCovariateQIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !endogenousQId) {
      setError('Vui lòng chọn biến kết quả và biến nội sinh.');
      return;
    }
    if (outcomeQId === endogenousQId) {
      setError('Biến kết quả và biến nội sinh không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: CopulaEndogeneityRequest = {
        outcome_question_id: outcomeQId,
        endogenous_question_id: endogenousQId,
        covariate_question_ids: covariateQIds.filter(
          (id) => id !== outcomeQId && id !== endogenousQId
        ),
        copula_family: copulaFamily,
        bootstrap_replications: bootstrapReps,
        alpha_level: alphaLevel,
        scope
      };

      const res = await api.runCopulaEndogeneity(surveyId, payload);
      if (res.status === 'insufficient_data' || res.status === 'zero_variance' || res.status === 'ERROR') {
        setError(res.message || 'Lỗi phân tích Copula Endogeneity.');
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
    a.download = `DataTrust_Copula_Endogeneity_${surveyId}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
            <GitCommit className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-white tracking-tight">
                Copula-Based Endogeneity Correction Engine
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Park &amp; Gupta (2012)
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-0.5">
              Instrument-free causal estimation via non-Gaussian copula transformations and higher-order moments
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            No Instruments Needed
          </span>
        </div>
      </div>

      {/* Input Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 bg-slate-900/50 p-5 rounded-xl border border-slate-700/50">
        {/* Outcome Variable Y */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span>Outcome Variable (Y)</span>
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Endogenous Regressor P */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-amber-400">Endogenous Regressor (P)</span>
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          </label>
          <select
            value={endogenousQId}
            onChange={(e) => setEndogenousQId(e.target.value)}
            className="w-full bg-slate-800 border border-amber-500/40 rounded-lg px-3 py-2 text-sm text-amber-200 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Copula Family */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span>Copula Transformation</span>
          </label>
          <select
            value={copulaFamily}
            onChange={(e) => setCopulaFamily(e.target.value as any)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="gaussian">Gaussian Copula (Standard Park &amp; Gupta)</option>
            <option value="clayton">Clayton Copula (Asymmetric Lower-Tail)</option>
          </select>
        </div>

        {/* Covariates Z Multi-select */}
        <div className="md:col-span-3 space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Exogenous Control Covariates (Z)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-36 overflow-y-auto p-2 bg-slate-800/70 border border-slate-700 rounded-lg">
            {numericQuestions
              .filter((q) => q.id !== outcomeQId && q.id !== endogenousQId)
              .map((q) => (
                <label
                  key={q.id}
                  className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer p-1.5 rounded hover:bg-slate-700/50"
                >
                  <input
                    type="checkbox"
                    checked={covariateQIds.includes(q.id)}
                    onChange={() => toggleCovariate(q.id)}
                    className="rounded border-slate-600 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
            {numericQuestions.filter((q) => q.id !== outcomeQId && q.id !== endogenousQId).length === 0 && (
              <span className="text-xs text-slate-500 italic p-1">Không có biến kiểm soát bổ sung</span>
            )}
          </div>
        </div>

        {/* Bootstrap Reps, Alpha, Scope, Run button */}
        <div className="md:col-span-3 flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800">
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5" />
              <span>Bootstrap:</span>
              <select
                value={bootstrapReps}
                onChange={(e) => setBootstrapReps(Number(e.target.value))}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white"
              >
                <option value={40}>40 reps (Fast)</option>
                <option value={100}>100 reps (Standard)</option>
                <option value={200}>200 reps (Deep)</option>
              </select>
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
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 ml-auto"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Đang ước lượng Copula...</span>
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                <span>Ước Lượng Nhân Quả Copula</span>
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
            {/* Naive OLS */}
            <div className="p-4 bg-slate-900/60 border border-amber-500/30 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Naive OLS Effect</span>
                <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider">Uncorrected</span>
              </div>
              <div className="text-2xl font-bold text-amber-300 tracking-tight">
                {result.naive_ols?.estimate.toFixed(4)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>SE: {result.naive_ols?.se?.toFixed(4)}</span>
                <span>p = {result.naive_ols?.p_value.toFixed(4)}</span>
              </div>
            </div>

            {/* Copula Corrected */}
            <div className="p-4 bg-slate-900/60 border border-indigo-500/40 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Copula Causal Effect</span>
                <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider">Park &amp; Gupta</span>
              </div>
              <div className="text-2xl font-bold text-indigo-300 tracking-tight">
                {result.copula_augmented?.estimate.toFixed(4)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>Boot SE: {result.copula_augmented?.se_bootstrap?.toFixed(4)}</span>
                <span>p = {result.copula_augmented?.p_value.toFixed(4)}</span>
              </div>
            </div>

            {/* Endogeneity Test Lambda */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Endogeneity Test (&lambda;)</span>
                {result.endogeneity_test?.is_endogenous ? (
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                ) : (
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                )}
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {(result.endogeneity_test?.lambda_pstar ?? 0) > 0 ? '+' : ''}{result.endogeneity_test?.lambda_pstar.toFixed(4)}
              </div>
              <div className="text-[11px] mt-1 font-semibold">
                {result.endogeneity_test?.is_endogenous ? (
                  <span className="text-rose-400">Endogeneity Detected (p &lt; 0.05)</span>
                ) : (
                  <span className="text-emerald-400">Exogenous (OLS Consistent)</span>
                )}
              </div>
            </div>

            {/* Implied Correlation rho & Bias */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Implied &rho;(P, &epsilon;) / Bias</span>
                <ArrowRightLeft className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-sky-300 tracking-tight">
                &rho; = {result.endogeneity_test?.implied_rho.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>Bias: {(result.bias_correction?.absolute_bias ?? 0) > 0 ? '+' : ''}{(result.bias_correction?.absolute_bias ?? 0).toFixed(4)}</span>
                <span>({(result.bias_correction?.relative_bias_pct ?? 0).toFixed(1)}%)</span>
              </div>
            </div>
          </div>

          {/* Non-Normality Diagnostics Card */}
          <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-700/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500/10 rounded-lg text-indigo-400">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">
                  Identification Condition: Non-Normality Diagnostics
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Shapiro-Wilk W = {result.non_normality_diagnostics?.shapiro_w.toFixed(4)} (p = {result.non_normality_diagnostics?.shapiro_p.toFixed(4)}) &bull; Skewness = {result.non_normality_diagnostics?.skewness.toFixed(3)} &bull; Excess Kurtosis = {result.non_normality_diagnostics?.kurtosis.toFixed(3)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className={`text-xs px-3 py-1 rounded-full font-semibold border ${
                result.non_normality_diagnostics?.is_non_normal
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              }`}>
                {result.non_normality_diagnostics?.status_label}
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  Visual Causal Comparison &amp; Distribution Transformation
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

          {/* Comparative Table */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Structural Parameters Comparison Table
            </h4>
            <div className="overflow-x-auto rounded-xl border border-slate-700/70">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Estimator</th>
                    <th className="py-2.5 px-3">Estimate (&beta;)</th>
                    <th className="py-2.5 px-3">Asymptotic SE</th>
                    <th className="py-2.5 px-3">Bootstrap SE</th>
                    <th className="py-2.5 px-3">95% Conf. Interval</th>
                    <th className="py-2.5 px-3">t-stat</th>
                    <th className="py-2.5 px-3">p-value</th>
                    <th className="py-2.5 px-3">R&sup2;</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                  {/* Naive OLS */}
                  <tr className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-semibold text-amber-300 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                      Naive OLS (Uncorrected)
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-white">
                      {result.naive_ols?.estimate.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      {result.naive_ols?.se?.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-500">-</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      [{result.naive_ols?.ci_95[0].toFixed(4)}, {result.naive_ols?.ci_95[1].toFixed(4)}]
                    </td>
                    <td className="py-2.5 px-3 font-mono">{result.naive_ols?.t_stat.toFixed(3)}</td>
                    <td className="py-2.5 px-3 font-mono">{result.naive_ols?.p_value.toFixed(4)}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">{result.naive_ols?.r2.toFixed(3)}</td>
                  </tr>

                  {/* Copula Corrected */}
                  <tr className="hover:bg-slate-800/40 bg-indigo-500/5">
                    <td className="py-2.5 px-3 font-semibold text-indigo-300 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                      Copula-Augmented (Park &amp; Gupta)
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-400">
                      {result.copula_augmented?.estimate.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      {result.copula_augmented?.se_asymptotic?.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-indigo-300 font-semibold">
                      {result.copula_augmented?.se_bootstrap?.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      [{result.copula_augmented?.ci_95[0].toFixed(4)}, {result.copula_augmented?.ci_95[1].toFixed(4)}]
                    </td>
                    <td className="py-2.5 px-3 font-mono">{result.copula_augmented?.t_stat.toFixed(3)}</td>
                    <td className="py-2.5 px-3 font-mono">{result.copula_augmented?.p_value.toFixed(4)}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">{result.copula_augmented?.r2.toFixed(3)}</td>
                  </tr>

                  {/* Endogeneity Regressor P* */}
                  <tr className="hover:bg-slate-800/40 border-t-2 border-slate-700/60">
                    <td className="py-2.5 px-3 font-semibold text-slate-400">
                      Copula Control Term (P* &lambda;)
                    </td>
                    <td className="py-2.5 px-3 font-mono text-white">
                      {(result.endogeneity_test?.lambda_pstar ?? 0) > 0 ? '+' : ''}{result.endogeneity_test?.lambda_pstar.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      {result.endogeneity_test?.se_lambda.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      {result.endogeneity_test?.se_bootstrap.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      [{result.endogeneity_test?.ci_95[0].toFixed(4)}, {result.endogeneity_test?.ci_95[1].toFixed(4)}]
                    </td>
                    <td className="py-2.5 px-3 font-mono">{result.endogeneity_test?.t_stat.toFixed(3)}</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-amber-400">
                      {result.endogeneity_test?.p_value.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-500">-</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

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
