import React, { useState } from 'react';
import {
  TargetedMaximumLikelihoodResult,
  TargetedMaximumLikelihoodRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Sparkles,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertCircle,
  Sliders,
  Activity,
  CheckCircle2,
  TrendingUp,
  Percent,
  Layers,
  Scale,
  Users,
  Target,
  BarChart2,
  HelpCircle,
  Filter,
  Zap,
  ShieldCheck
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

export const TargetedMaximumLikelihoodCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeId, setOutcomeId] = useState<string>(questions[0]?.id || '');
  const [treatmentId, setTreatmentId] = useState<string>(questions[1]?.id || questions[0]?.id || '');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TargetedMaximumLikelihoodResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState(false);
  const [activeTab, setActiveTab] = useState<'visualizer' | 'comparison' | 'diagnostics' | 'methodology'>('visualizer');

  const handleToggleCovariate = (id: string) => {
    setSelectedCovariates(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeId || !treatmentId) {
      setError('Please select both an outcome question and a treatment question.');
      return;
    }
    if (outcomeId === treatmentId) {
      setError('Outcome and treatment must be distinct survey questions.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: TargetedMaximumLikelihoodRequest = {
        outcome_question_id: outcomeId,
        treatment_question_id: treatmentId,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        scope
      };

      const res = await api.runTargetedMaximumLikelihood(surveyId, payload);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Insufficient data for TMLE estimation.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to execute Targeted Maximum Likelihood Estimation.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-teal-500/10 border border-teal-500/20 rounded-xl text-teal-400">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Targeted Maximum Likelihood Estimation (TMLE)
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  van der Laan & Rose (2011)
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Semiparametric doubly robust substitution estimator for Average Treatment Effect (ATE) with targeted fluctuation via clever covariates H(A, W) and Efficient Influence Curve (EIC) inference.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setResult(null);
              setError(null);
            }}
            disabled={loading || !result}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-white bg-slate-900/50 hover:bg-slate-900 border border-slate-700/60 rounded-lg transition-all disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 rounded-xl shadow-lg shadow-teal-900/30 transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Optimizing Submodel Fluctuation...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Estimate TMLE ATE
              </>
            )}
          </button>
        </div>
      </div>

      {/* Control Configuration Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-900/40 rounded-xl border border-slate-700/50 text-xs">
        {/* Outcome Selector */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-teal-400" />
            Outcome Variable (Y)
          </label>
          <select
            value={outcomeId}
            onChange={e => setOutcomeId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Treatment Selector */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            Treatment Indicator (A &isin; &#123;0, 1&#125;)
          </label>
          <select
            value={treatmentId}
            onChange={e => setTreatmentId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Scope Selector */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-purple-400" />
            Data Scope
          </label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as any)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Available Submissions</option>
            <option value="verified_clean">Verified Clean (Anti-Fraud Pass)</option>
          </select>
        </div>

        {/* Confounders Selection Checklist */}
        <div className="md:col-span-3 pt-2 border-t border-slate-800/80">
          <span className="text-slate-300 font-semibold block mb-1.5">Confounders & Pre-Treatment Baseline Covariates (W):</span>
          <div className="flex flex-wrap gap-2">
            {questions
              .filter(q => q.id !== outcomeId && q.id !== treatmentId)
              .map(q => {
                const isSelected = selectedCovariates.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => handleToggleCovariate(q.id)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                      isSelected
                        ? 'bg-teal-500/20 border-teal-500/50 text-teal-200'
                        : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {isSelected ? '✓ ' : '+ '}
                    {q.title.length > 30 ? q.title.slice(0, 30) + '...' : q.title}
                  </button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Key Metric KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Semiparametric Efficient ATE */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>TMLE Efficient ATE (&psi;)</span>
                <Sparkles className="w-4 h-4 text-teal-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight flex items-baseline gap-1.5">
                <span>{result.ate_tmle ? (result.ate_tmle.estimate > 0 ? '+' : '') + result.ate_tmle.estimate.toFixed(3) : 'N/A'}</span>
                <span className="text-xs text-slate-400">units</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>p = {result.ate_tmle?.p_value !== undefined ? (result.ate_tmle.p_value < 0.001 ? '< .001' : result.ate_tmle.p_value.toFixed(3)) : 'N/A'}</span>
                <span className="text-teal-400 font-medium">
                  {result.ate_tmle && result.ate_tmle.p_value < 0.05 ? 'Statistically Sig.' : 'Inconclusive'}
                </span>
              </div>
            </div>

            {/* Targeted Fluctuation Epsilon */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Submodel Fluctuation (&epsilon;)</span>
                <Activity className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {(result.targeted_fluctuation?.epsilon_fluctuation ?? 0) > 0 ? '+' : ''}{(result.targeted_fluctuation?.epsilon_fluctuation ?? 0).toFixed(4)}
              </div>
              <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> EIC Score Solved ({(result.targeted_fluctuation?.eic_mean_residual ?? 0).toFixed(5)})
              </div>
            </div>

            {/* Counterfactual Outcomes */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Counterfactual Means</span>
                <TrendingUp className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-lg font-bold text-white tracking-tight">
                E[Y(1)] = {result.ate_tmle?.ey1_counterfactual.toFixed(2)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                E[Y(0)] = {result.ate_tmle?.ey0_counterfactual.toFixed(2)}
              </div>
            </div>

            {/* Sample & Overlap */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Sample & Overlap</span>
                <Users className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.n_treated} Tr / {result.n_control} Co
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Positivity Risk: {result.propensity_diagnostics?.positivity_violation_risk}
              </div>
            </div>
          </div>

          {/* Interactive Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-700/60 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('visualizer')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'visualizer'
                  ? 'border-teal-400 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              Forest Plot & Overlap Visualizer
            </button>
            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'comparison'
                  ? 'border-teal-400 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Scale className="w-3.5 h-3.5" />
              Estimator Benchmarks (TMLE vs G-Comp vs IPTW)
            </button>
            <button
              onClick={() => setActiveTab('diagnostics')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'diagnostics'
                  ? 'border-teal-400 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Fluctuation & Score Diagnostics
            </button>
            <button
              onClick={() => setActiveTab('methodology')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'methodology'
                  ? 'border-teal-400 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5" />
              APA Narrative & Foundations
            </button>
          </div>

          {/* Tab 1: Visualizer */}
          {activeTab === 'visualizer' && (
            <div className="space-y-4">
              {result.svg_visualization && (
                <div
                  className="w-full overflow-x-auto bg-slate-900/60 p-4 rounded-xl border border-slate-700/60"
                  dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                />
              )}

              <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-700/40 text-xs text-slate-300 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>
                    TMLE is a substitution estimator that remains within parameter bounds and achieves the semiparametric efficiency bound.
                  </span>
                </div>
                <span className="text-[11px] text-slate-400">van der Laan & Rose (2011)</span>
              </div>
            </div>
          )}

          {/* Tab 2: Comparison */}
          {activeTab === 'comparison' && result.estimators_comparison && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Causal Estimation Method</th>
                    <th className="py-2.5 px-3">ATE Point Estimate</th>
                    <th className="py-2.5 px-3">Standard Error</th>
                    <th className="py-2.5 px-3">95% Confidence Interval</th>
                    <th className="py-2.5 px-3">p-value</th>
                    <th className="py-2.5 px-3">Efficiency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {result.estimators_comparison.map((est, idx) => (
                    <tr key={idx} className={`hover:bg-slate-800/40 transition-colors ${
                      est.is_semiparametric_efficient ? 'bg-teal-500/10' : ''
                    }`}>
                      <td className="py-2.5 px-3 font-semibold text-white flex items-center gap-2">
                        {est.is_semiparametric_efficient && <Sparkles className="w-3.5 h-3.5 text-teal-400" />}
                        {est.method}
                      </td>
                      <td className="py-2.5 px-3 font-bold text-teal-300">
                        {est.estimate > 0 ? `+${est.estimate.toFixed(4)}` : est.estimate.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">{est.se.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-slate-300">[{est.ci_95[0].toFixed(3)}, {est.ci_95[1].toFixed(3)}]</td>
                      <td className="py-2.5 px-3">
                        <span className={est.p_value < 0.05 ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                          {est.p_value < 0.001 ? '< .001' : est.p_value.toFixed(4)}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          est.is_semiparametric_efficient
                            ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                            : 'bg-slate-700/50 text-slate-400'
                        }`}>
                          {est.is_semiparametric_efficient ? 'Optimal Efficient' : 'Sub-Optimal'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Diagnostics */}
          {activeTab === 'diagnostics' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60 space-y-3">
                <h4 className="font-bold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-teal-400" />
                  Targeted Fluctuation & Score Equation
                </h4>
                <div className="space-y-1.5 font-mono text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Fluctuation Parameter (&epsilon;):</span>
                    <span className="text-white font-bold">{(result.targeted_fluctuation?.epsilon_fluctuation ?? 0).toFixed(5)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">EIC Mean Residual (score solver):</span>
                    <span className="text-emerald-400 font-bold">{(result.targeted_fluctuation?.eic_mean_residual ?? 0).toFixed(6)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">EIC Asymptotic Variance:</span>
                    <span>{(result.targeted_fluctuation?.eic_variance ?? 0).toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Score Equation Status:</span>
                    <span className="text-emerald-400 font-bold">Solved (&lt; 0.05 tolerance)</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60 space-y-3">
                <h4 className="font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-sky-400" />
                  Propensity Score Overlap & Positivity
                </h4>
                <div className="space-y-1.5 font-mono text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Minimum Propensity g(W):</span>
                    <span>{result.propensity_diagnostics?.min_propensity.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Maximum Propensity g(W):</span>
                    <span>{result.propensity_diagnostics?.max_propensity.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Mean Treated Propensity:</span>
                    <span className="text-sky-300">{result.propensity_diagnostics?.mean_treated_propensity.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Mean Control Propensity:</span>
                    <span className="text-slate-400">{result.propensity_diagnostics?.mean_control_propensity.toFixed(4)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: APA Narrative */}
          {activeTab === 'methodology' && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-300">APA 7th Academic Summary</span>
                  <button
                    onClick={handleCopyNarrative}
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-teal-400 hover:text-teal-300 bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/30 rounded-lg transition-all"
                  >
                    {copiedNarrative ? (
                      <>
                        <Check className="w-3.5 h-3.5" /> Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" /> Copy APA Narrative
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-serif italic">
                  &ldquo;{result.apa_narrative}&rdquo;
                </p>
              </div>

              <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-700/40 text-xs text-slate-400 space-y-2">
                <div className="font-semibold text-slate-200">Semiparametric & Targeted Learning Foundations:</div>
                <p>
                  1. <strong className="text-slate-300">Targeted Bias-Variance Trade-Off:</strong> Standard machine learning algorithms optimize for global prediction of the full outcome surface, which can sacrifice precision on the specific causal contrast of interest. TMLE introduces a targeted parametric fluctuation along the clever covariate H(A, W) specifically dedicated to removing residual confounding bias from the target parameter &psi; = E[Y(1) - Y(0)] (van der Laan & Rose, 2011).
                </p>
                <p>
                  2. <strong className="text-slate-300">Exact Parameter Bounds & Double Robustness:</strong> Unlike estimating equation or IPTW methods that can produce counterfactual probabilities outside [0, 1] or extreme variance when propensity weights approach zero, TMLE is a bounded substitution estimator guaranteed to adhere to the physical parameter space.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
