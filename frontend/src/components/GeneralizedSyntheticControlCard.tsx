import React, { useState } from 'react';
import {
  GeneralizedSyntheticControlResult,
  GeneralizedSyntheticControlRequest
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
  Calendar,
  Building,
  Target,
  Zap,
  HelpCircle,
  Filter
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

export const GeneralizedSyntheticControlCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeId, setOutcomeId] = useState<string>(questions[0]?.id || '');
  const [unitId, setUnitId] = useState<string>(questions[1]?.id || questions[0]?.id || '');
  const [timeId, setTimeId] = useState<string>(questions[2]?.id || questions[0]?.id || '');
  const [treatmentId, setTreatmentId] = useState<string>(questions[3]?.id || questions[0]?.id || '');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [nFactors, setNFactors] = useState<number>(2);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GeneralizedSyntheticControlResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState(false);
  const [activeTab, setActiveTab] = useState<'visualizer' | 'event_study' | 'units' | 'methodology'>('visualizer');

  const handleToggleCovariate = (id: string) => {
    setSelectedCovariates(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeId || !unitId || !timeId || !treatmentId) {
      setError('Please select outcome, unit, time, and treatment questions.');
      return;
    }
    const distinctIds = new Set([outcomeId, unitId, timeId, treatmentId]);
    if (distinctIds.size < 4) {
      setError('Outcome, unit, time, and treatment variables must all be distinct questions.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: GeneralizedSyntheticControlRequest = {
        outcome_question_id: outcomeId,
        unit_question_id: unitId,
        time_question_id: timeId,
        treatment_question_id: treatmentId,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        n_factors: nFactors,
        scope
      };

      const res = await api.runGeneralizedSyntheticControl(surveyId, payload);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Insufficient panel structure for generalized synthetic control estimation.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to execute Generalized Synthetic Control estimation.');
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
            <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Generalized Synthetic Control & Latent Interactive Factors
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Gsynth (Xu 2017)
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates staggered adoption policies across multiple treated units with unobserved time-varying confounders modeled via latent interactive fixed effects (&lambda;<sub>i</sub>&prime; f<sub>t</sub>).
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
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 rounded-xl shadow-lg shadow-amber-900/30 transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Estimating Factors...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Estimate Gsynth ATT
              </>
            )}
          </button>
        </div>
      </div>

      {/* Configuration Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-slate-900/40 rounded-xl border border-slate-700/50 text-xs">
        {/* Outcome Selector */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-amber-400" />
            Outcome Variable (Y)
          </label>
          <select
            value={outcomeId}
            onChange={e => setOutcomeId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Unit Identifier */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Building className="w-3.5 h-3.5 text-sky-400" />
            Unit Identifier (i)
          </label>
          <select
            value={unitId}
            onChange={e => setUnitId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Time / Period */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-purple-400" />
            Time / Wave Indicator (t)
          </label>
          <select
            value={timeId}
            onChange={e => setTimeId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-purple-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Treatment Indicator */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-rose-400" />
            Treatment Indicator (D<sub>it</sub>)
          </label>
          <select
            value={treatmentId}
            onChange={e => setTreatmentId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-rose-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Advanced Options Row */}
        <div className="md:col-span-2 lg:col-span-4 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="text-slate-400 font-medium">Latent Factor Rank (r):</span>
            <select
              value={nFactors}
              onChange={e => setNFactors(parseInt(e.target.value) || 2)}
              className="bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200"
            >
              <option value={1}>r = 1 (Dominant Macro Trend)</option>
              <option value={2}>r = 2 (Two Interactive Factors)</option>
              <option value={3}>r = 3 (Three Factor Components)</option>
            </select>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-slate-400 font-medium">Data Scope:</span>
            <select
              value={scope}
              onChange={e => setScope(e.target.value as any)}
              className="bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200"
            >
              <option value="all">All Panel Records</option>
              <option value="verified_clean">Verified Clean (Anti-Fraud)</option>
            </select>
          </div>

          {/* Covariates checklist */}
          <div className="flex-1 min-w-[240px]">
            <span className="text-slate-400 font-medium mr-2">Time-Varying Covariates (X):</span>
            <div className="inline-flex flex-wrap gap-1.5 mt-1">
              {questions
                .filter(q => q.id !== outcomeId && q.id !== unitId && q.id !== timeId && q.id !== treatmentId)
                .slice(0, 5)
                .map(q => {
                  const isChecked = selectedCovariates.includes(q.id);
                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => handleToggleCovariate(q.id)}
                      className={`px-2 py-0.5 rounded text-[11px] border transition-all ${
                        isChecked
                          ? 'bg-amber-500/20 border-amber-500/50 text-amber-200'
                          : 'bg-slate-800/70 border-slate-700 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {isChecked ? '✓ ' : '+ '}
                      {q.title.length > 20 ? q.title.slice(0, 20) + '...' : q.title}
                    </button>
                  );
                })}
            </div>
          </div>
        </div>
      </div>

      {/* Error Notice */}
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
            {/* Overall ATT */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Overall Post-Treatment ATT</span>
                <Sparkles className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight flex items-baseline gap-1.5">
                <span>{result.overall_att ? (result.overall_att.estimate > 0 ? '+' : '') + result.overall_att.estimate.toFixed(3) : 'N/A'}</span>
                <span className="text-xs text-slate-400">units</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>p = {result.overall_att?.p_value !== undefined ? (result.overall_att.p_value < 0.001 ? '< .001' : result.overall_att.p_value.toFixed(3)) : 'N/A'}</span>
                <span className="text-amber-400 font-medium">
                  {result.overall_att && result.overall_att.p_value < 0.05 ? 'Statistically Sig.' : 'Inconclusive'}
                </span>
              </div>
            </div>

            {/* Pre-Treatment RMSPE */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Pre-Treatment RMSPE</span>
                <Activity className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.pre_treatment_diagnostics?.mean_pre_rmspe.toFixed(3) ?? 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Placebo bias: {result.pre_treatment_diagnostics?.mean_pre_placebo.toFixed(3)}
              </div>
            </div>

            {/* Panel Dimensions */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Panel Structure</span>
                <Building className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.n_treated_units} Tr / {result.n_control_units} Co
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Across {result.n_time_periods} periods (N={result.sample_size})
              </div>
            </div>

            {/* Latent Factor Model */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Factor Architecture</span>
                <Layers className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                r = {result.n_latent_factors}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Explained: {result.variance_explained_ratio?.map(v => (v * 100).toFixed(1) + '%').join(', ')}
              </div>
            </div>
          </div>

          {/* Interactive Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-700/60 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('visualizer')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'visualizer'
                  ? 'border-amber-400 text-amber-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              Trajectories & Event Study
            </button>
            <button
              onClick={() => setActiveTab('event_study')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'event_study'
                  ? 'border-amber-400 text-amber-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Dynamic Event Study Table
            </button>
            <button
              onClick={() => setActiveTab('units')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'units'
                  ? 'border-amber-400 text-amber-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Building className="w-3.5 h-3.5" />
              Treated Unit Summaries
            </button>
            <button
              onClick={() => setActiveTab('methodology')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'methodology'
                  ? 'border-amber-400 text-amber-400'
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
                    Interactive fixed effects model relaxes the parallel trends assumption by projecting unobserved time shocks onto donor loadings.
                  </span>
                </div>
                <span className="text-[11px] text-slate-400">Xu (2017 Political Analysis)</span>
              </div>
            </div>
          )}

          {/* Tab 2: Dynamic Event Study Table */}
          {activeTab === 'event_study' && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Relative Time (s = t - T₀)</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">ATT(s) Estimate</th>
                    <th className="py-2.5 px-3">Std. Error</th>
                    <th className="py-2.5 px-3">95% Confidence Interval</th>
                    <th className="py-2.5 px-3">p-value</th>
                    <th className="py-2.5 px-3">Active Units</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {result.event_study_trajectory?.map((pt, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-amber-300 font-semibold">
                        {pt.relative_time > 0 ? `+${pt.relative_time}` : pt.relative_time}
                      </td>
                      <td className="py-2 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          pt.is_post_treatment
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-slate-700/50 text-slate-300'
                        }`}>
                          {pt.is_post_treatment ? 'Post-Treatment' : 'Pre-Placebo'}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-semibold text-white">
                        {pt.att > 0 ? `+${pt.att.toFixed(3)}` : pt.att.toFixed(3)}
                      </td>
                      <td className="py-2 px-3 text-slate-400">{pt.se.toFixed(3)}</td>
                      <td className="py-2 px-3 text-slate-400">
                        [{pt.ci_95[0].toFixed(3)}, {pt.ci_95[1].toFixed(3)}]
                      </td>
                      <td className="py-2 px-3">
                        <span className={pt.p_value < 0.05 ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                          {pt.p_value < 0.001 ? '< .001' : pt.p_value.toFixed(3)}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-400">{pt.n_treated_units}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Treated Unit Summaries */}
          {activeTab === 'units' && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Treated Unit</th>
                    <th className="py-2.5 px-3">Adoption Wave (T₀)</th>
                    <th className="py-2.5 px-3">Pre-Treatment RMSPE</th>
                    <th className="py-2.5 px-3">Post-Treatment Mean Effect</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {result.treated_unit_summaries?.map((u, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-sky-300 font-semibold">{u.unit}</td>
                      <td className="py-2 px-3 text-purple-300">{u.adoption_time}</td>
                      <td className="py-2 px-3 text-slate-300">{u.pre_rmspe.toFixed(3)}</td>
                      <td className="py-2 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          u.post_mean_effect > 0
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : 'bg-rose-500/20 text-rose-300'
                        }`}>
                          {u.post_mean_effect > 0 ? '+' : ''}{u.post_mean_effect.toFixed(3)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: APA Narrative & Methodology */}
          {activeTab === 'methodology' && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-300">APA 7th Academic Summary</span>
                  <button
                    onClick={handleCopyNarrative}
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-amber-400 hover:text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-lg transition-all"
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
                <div className="font-semibold text-slate-200">Econometric & Methodological Foundations:</div>
                <p>
                  1. <strong className="text-slate-300">Overcoming Parallel Trends Violations:</strong> Standard Difference-in-Differences (DID) fails when unobserved confounding factors vary over time. Gsynth introduces latent factors f<sub>t</sub> and unit loadings &lambda;<sub>i</sub>, capturing dynamic macroeconomic, market, or cultural shifts without parametric misspecification (Xu, 2017).
                </p>
                <p>
                  2. <strong className="text-slate-300">Staggered Multi-Unit Adoption:</strong> Unlike classical synthetic controls that evaluate only one treated unit with uniform timing, Gsynth natively pools multiple treated units adopting policies at different calendar dates into a unified relative event-time framework (s = t - T₀).
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
