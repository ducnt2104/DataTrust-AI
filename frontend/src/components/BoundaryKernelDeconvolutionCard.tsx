import React, { useState } from 'react';
import {
  BoundaryKernelDeconvolutionResult,
  BoundaryKernelDeconvolutionRequest
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
  ShieldCheck,
  Target,
  BarChart2,
  HelpCircle,
  Filter,
  Maximize2
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

export const BoundaryKernelDeconvolutionCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [variableId, setVariableId] = useState<string>(questions[0]?.id || '');
  const [reliabilityRatio, setReliabilityRatio] = useState<number>(0.80);
  const [errorType, setErrorType] = useState<string>('gaussian');
  const [lowerBound, setLowerBound] = useState<number | undefined>(0.0);
  const [hasLowerBound, setHasLowerBound] = useState<boolean>(true);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BoundaryKernelDeconvolutionResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState(false);
  const [activeTab, setActiveTab] = useState<'visualizer' | 'moments' | 'density_grid' | 'methodology'>('visualizer');

  const handleRunAnalysis = async () => {
    if (!variableId) {
      setError('Please select a survey variable to deconvolve.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: BoundaryKernelDeconvolutionRequest = {
        variable_question_id: variableId,
        reliability_ratio: reliabilityRatio,
        error_type: errorType,
        lower_bound: hasLowerBound ? lowerBound : undefined,
        scope
      };

      const res = await api.runBoundaryKernelDeconvolution(surveyId, payload);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Insufficient numeric data for kernel deconvolution.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to execute Kernel Deconvolution.');
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
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Boundary Kernel Deconvolution & Noise Correction
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Delaigle & Meister (2008 JASA)
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Inverts measurement error convolution (W = X + U) via Fourier transformation to restore the true unattenuated latent distribution, correcting attenuation bias in survey regression slopes.
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
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl shadow-lg shadow-indigo-900/30 transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Inverting Fourier Kernel...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Deconvolve Noise
              </>
            )}
          </button>
        </div>
      </div>

      {/* Control Configuration Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-slate-900/40 rounded-xl border border-slate-700/50 text-xs">
        {/* Variable Selector */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-indigo-400" />
            Survey Metric (W = X + U)
          </label>
          <select
            value={variableId}
            onChange={e => setVariableId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Reliability Ratio Slider */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-sky-400" />
              Reliability Ratio (&rho;)
            </span>
            <span className="text-sky-400 font-mono font-bold">{(reliabilityRatio * 100).toFixed(0)}%</span>
          </label>
          <input
            type="range"
            min={0.50}
            max={0.95}
            step={0.05}
            value={reliabilityRatio}
            onChange={e => setReliabilityRatio(parseFloat(e.target.value))}
            className="w-full accent-indigo-500"
          />
          <span className="text-[10px] text-slate-400">Share of variance representing true signal</span>
        </div>

        {/* Error Structure Selector */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            Noise Distribution Structure
          </label>
          <select
            value={errorType}
            onChange={e => setErrorType(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-500"
          >
            <option value="gaussian">Gaussian Noise ~ N(0, &sigma;²)</option>
            <option value="laplace">Laplace (Heavy-Tailed Noise)</option>
          </select>
        </div>

        {/* Boundary Support Filter */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Support Boundary (X &ge; Bound)
          </label>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="hasBound"
              checked={hasLowerBound}
              onChange={e => setHasLowerBound(e.target.checked)}
              className="accent-indigo-500 rounded"
            />
            <label htmlFor="hasBound" className="text-slate-300 text-xs mr-2">Enforce</label>
            <input
              type="number"
              disabled={!hasLowerBound}
              value={lowerBound !== undefined ? lowerBound : 0.0}
              onChange={e => setLowerBound(parseFloat(e.target.value) || 0.0)}
              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-center disabled:opacity-40"
            />
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
            {/* Attenuation Factor */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Slope De-Attenuation Factor</span>
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight flex items-baseline gap-1.5">
                <span>{result.attenuation_correction_factor?.toFixed(2)}x</span>
                <span className="text-xs text-slate-400">multiplier</span>
              </div>
              <div className="text-[11px] text-emerald-400 mt-1">
                Multiplies naive regression slopes &beta;<sub>W</sub>
              </div>
            </div>

            {/* Variance Reduction */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Noise Variance Removed</span>
                <Percent className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.dispersion_metrics?.variance_reduction_percent.toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Noise SD &sigma;<sub>U</sub> = {result.dispersion_metrics?.noise_standard_deviation.toFixed(3)}
              </div>
            </div>

            {/* True Latent Standard Deviation */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Latent True Dispersion</span>
                <Activity className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.moments_comparison?.deconvoluted.std_dev.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Observed noisy SD: {result.moments_comparison?.observed.std_dev.toFixed(3)}
              </div>
            </div>

            {/* Optimal Fourier Bandwidth */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Fourier Bandwidth (h)</span>
                <Sliders className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.bandwidth?.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Sample N = {result.sample_size} valid records
              </div>
            </div>
          </div>

          {/* Interactive Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-700/60 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('visualizer')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'visualizer'
                  ? 'border-indigo-400 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              Density Comparison Visualizer
            </button>
            <button
              onClick={() => setActiveTab('moments')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'moments'
                  ? 'border-indigo-400 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Moments & Quantiles Comparison
            </button>
            <button
              onClick={() => setActiveTab('density_grid')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'density_grid'
                  ? 'border-indigo-400 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Density Profile Grid
            </button>
            <button
              onClick={() => setActiveTab('methodology')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'methodology'
                  ? 'border-indigo-400 text-indigo-400'
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
                    True density f<sub>X</sub>(x) exhibits a sharper, uninflated peak without boundary leakage below the true physical support limit.
                  </span>
                </div>
                <span className="text-[11px] text-slate-400">Delaigle & Meister (2008 JASA)</span>
              </div>
            </div>
          )}

          {/* Tab 2: Moments Table */}
          {activeTab === 'moments' && result.moments_comparison && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Statistical Moment / Quantile</th>
                    <th className="py-2.5 px-3">Observed Contaminated W</th>
                    <th className="py-2.5 px-3">Deconvoluted Latent X</th>
                    <th className="py-2.5 px-3">Noise Bias Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  <tr className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2 px-3 font-semibold text-slate-300">Mean (&mu;)</td>
                    <td className="py-2 px-3 text-amber-300">{result.moments_comparison.observed.mean.toFixed(3)}</td>
                    <td className="py-2 px-3 text-sky-300 font-bold">{result.moments_comparison.deconvoluted.mean.toFixed(3)}</td>
                    <td className="py-2 px-3 text-slate-400">
                      {(result.moments_comparison.observed.mean - result.moments_comparison.deconvoluted.mean).toFixed(3)}
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2 px-3 font-semibold text-slate-300">Standard Deviation (&sigma;)</td>
                    <td className="py-2 px-3 text-amber-300">{result.moments_comparison.observed.std_dev.toFixed(3)}</td>
                    <td className="py-2 px-3 text-sky-300 font-bold">{result.moments_comparison.deconvoluted.std_dev.toFixed(3)}</td>
                    <td className="py-2 px-3 text-emerald-400 font-bold">
                      -{(result.moments_comparison.observed.std_dev - result.moments_comparison.deconvoluted.std_dev).toFixed(3)} (Inflated)
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2 px-3 font-semibold text-slate-300">Skewness (&gamma;₁)</td>
                    <td className="py-2 px-3 text-amber-300">{result.moments_comparison.observed.skewness.toFixed(3)}</td>
                    <td className="py-2 px-3 text-sky-300 font-bold">{result.moments_comparison.deconvoluted.skewness.toFixed(3)}</td>
                    <td className="py-2 px-3 text-slate-400">
                      {(result.moments_comparison.observed.skewness - result.moments_comparison.deconvoluted.skewness).toFixed(3)}
                    </td>
                  </tr>
                  {['P10', 'P25', 'P50 (Median)', 'P75', 'P90'].map((label, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-slate-400">{label}</td>
                      <td className="py-2 px-3 text-amber-200">{result.moments_comparison?.observed.percentiles[idx].toFixed(3)}</td>
                      <td className="py-2 px-3 text-sky-200 font-semibold">{result.moments_comparison?.deconvoluted.percentiles[idx].toFixed(3)}</td>
                      <td className="py-2 px-3 text-slate-400">
                        {((result.moments_comparison?.observed.percentiles[idx] ?? 0) - (result.moments_comparison?.deconvoluted.percentiles[idx] ?? 0)).toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Grid */}
          {activeTab === 'density_grid' && result.density_profile && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Metric Value (x)</th>
                    <th className="py-2.5 px-3">Observed Density f_W(x)</th>
                    <th className="py-2.5 px-3">Deconvoluted Latent Density f_X(x)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {result.density_profile.map((pt, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-indigo-300">{pt.x.toFixed(2)}</td>
                      <td className="py-2 px-3 text-amber-300">{pt.f_observed.toFixed(5)}</td>
                      <td className="py-2 px-3 text-sky-300 font-semibold">{pt.f_deconvoluted.toFixed(5)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-lg transition-all"
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
                <div className="font-semibold text-slate-200">Econometric & Measurement Error Foundations:</div>
                <p>
                  1. <strong className="text-slate-300">Attenuation Bias in Regression Slopes:</strong> Classical measurement error in an explanatory variable biases OLS regression coefficients toward zero by a factor equal to the reliability ratio: &beta;<sub>W</sub> = &rho; &middot; &beta;<sub>X</sub>. Applying the de-attenuation multiplier 1/&rho; recovers the structural effect (Carroll et al., 2006).
                </p>
                <p>
                  2. <strong className="text-slate-300">Boundary Kernel Correction:</strong> Sinc or Fourier deconvolution often spills probability mass into negative territory for inherently non-negative survey questions (income, hours worked, counts). Reflection techniques and boundary renormalization prevent impossible negative values while preserving total mass.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
