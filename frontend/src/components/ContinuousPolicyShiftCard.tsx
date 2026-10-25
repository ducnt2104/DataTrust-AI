import React, { useState } from 'react';
import {
  ContinuousPolicyShiftResult,
  ContinuousPolicyShiftRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  TrendingUp,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertCircle,
  Sliders,
  Activity,
  CheckCircle2,
  Percent,
  Sparkles,
  ArrowRight,
  HelpCircle,
  Filter,
  BarChart2,
  Zap,
  Target
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

export const ContinuousPolicyShiftCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeId, setOutcomeId] = useState<string>(questions[0]?.id || '');
  const [treatmentId, setTreatmentId] = useState<string>(questions[1]?.id || questions[0]?.id || '');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [gridPoints, setGridPoints] = useState<number>(25);
  const [shiftDelta, setShiftDelta] = useState<number>(1.0);
  const [customBandwidth, setCustomBandwidth] = useState<number>(0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ContinuousPolicyShiftResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState(false);
  const [activeTab, setActiveTab] = useState<'curve' | 'policy' | 'table' | 'methodology'>('curve');

  const handleToggleCovariate = (id: string) => {
    setSelectedCovariates(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeId || !treatmentId) {
      setError('Please select both an outcome variable and a continuous treatment variable.');
      return;
    }
    if (outcomeId === treatmentId) {
      setError('Outcome and continuous treatment must be distinct survey questions.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: ContinuousPolicyShiftRequest = {
        outcome_question_id: outcomeId,
        treatment_question_id: treatmentId,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        grid_points: gridPoints,
        shift_delta: shiftDelta,
        bandwidth: customBandwidth > 0 ? customBandwidth : undefined,
        scope
      };

      const res = await api.runContinuousPolicyShift(surveyId, payload);
      if (res.status === 'insufficient_data') {
        setError(res.message || 'Insufficient continuous response data for doubly robust kernel smoothing.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to compute continuous policy shift and dosage response curve.');
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

  // Helper for responsive SVG curve if dose_response_curve is present
  const renderDoseResponseSVG = () => {
    if (!result?.dose_response_curve || result.dose_response_curve.length === 0) return null;

    const points = result.dose_response_curve;
    const minDose = Math.min(...points.map(p => p.dosage_level));
    const maxDose = Math.max(...points.map(p => p.dosage_level));
    const minResp = Math.min(...points.map(p => p.ci_95[0]));
    const maxResp = Math.max(...points.map(p => p.ci_95[1]));

    const width = 640;
    const height = 280;
    const padX = 55;
    const padY = 35;

    const scaleX = (d: number) =>
      padX + ((d - minDose) / (maxDose - minDose || 1)) * (width - 2 * padX);
    const scaleY = (r: number) =>
      height - padY - ((r - minResp) / (maxResp - minResp || 1)) * (height - 2 * padY);

    // Build ribbon path
    const upperPath = points
      .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${scaleX(p.dosage_level).toFixed(1)} ${scaleY(p.ci_95[1]).toFixed(1)}`)
      .join(' ');
    const lowerPath = [...points]
      .reverse()
      .map(p => `L ${scaleX(p.dosage_level).toFixed(1)} ${scaleY(p.ci_95[0]).toFixed(1)}`)
      .join(' ');
    const ribbonPath = `${upperPath} ${lowerPath} Z`;

    // Main line path
    const linePath = points
      .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${scaleX(p.dosage_level).toFixed(1)} ${scaleY(p.outcome_estimate).toFixed(1)}`)
      .join(' ');

    return (
      <div className="w-full overflow-x-auto bg-slate-900/60 p-4 rounded-xl border border-slate-700/60">
        <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center justify-between">
          <span>Doubly Robust Dose-Response Curve (DRC) with 95% Confidence Band</span>
          <span className="text-emerald-400">Bandwidth h = {result.bandwidth?.toFixed(3)}</span>
        </div>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full max-w-2xl mx-auto block">
          <defs>
            <linearGradient id="drcRibbon" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={padX} y1={scaleY(minResp)} x2={width - padX} y2={scaleY(minResp)} stroke="#334155" strokeDasharray="3 3" />
          <line x1={padX} y1={scaleY(maxResp)} x2={width - padX} y2={scaleY(maxResp)} stroke="#334155" strokeDasharray="3 3" />
          <line x1={padX} y1={scaleY((minResp + maxResp) / 2)} x2={width - padX} y2={scaleY((minResp + maxResp) / 2)} stroke="#334155" strokeDasharray="3 3" />

          {/* 95% CI Ribbon */}
          <path d={ribbonPath} fill="url(#drcRibbon)" />

          {/* Dose Response Line */}
          <path d={linePath} fill="none" stroke="#38bdf8" strokeWidth="2.5" />

          {/* Points */}
          {points.map((p, idx) => (
            <circle
              key={idx}
              cx={scaleX(p.dosage_level)}
              cy={scaleY(p.outcome_estimate)}
              r="3.5"
              fill="#0ea5e9"
              stroke="#e0f2fe"
              strokeWidth="1.5"
            />
          ))}

          {/* Current Mean Marker */}
          {result.treatment_support?.current_mean !== undefined && (
            <g>
              <line
                x1={scaleX(result.treatment_support.current_mean)}
                y1={padY}
                x2={scaleX(result.treatment_support.current_mean)}
                y2={height - padY}
                stroke="#f59e0b"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
              <text
                x={scaleX(result.treatment_support.current_mean) + 4}
                y={padY + 14}
                fill="#fbbf24"
                fontSize="10"
                fontWeight="bold"
              >
                Current Mean ({result.treatment_support.current_mean.toFixed(2)})
              </text>
            </g>
          )}

          {/* Optimal Dosage Marker */}
          {result.treatment_support?.optimal_dosage !== undefined && (
            <g>
              <line
                x1={scaleX(result.treatment_support.optimal_dosage)}
                y1={padY}
                x2={scaleX(result.treatment_support.optimal_dosage)}
                y2={height - padY}
                stroke="#10b981"
                strokeWidth="2"
                strokeDasharray="2 2"
              />
              <text
                x={scaleX(result.treatment_support.optimal_dosage) + 4}
                y={height - padY - 8}
                fill="#34d399"
                fontSize="10"
                fontWeight="bold"
              >
                Optimal Peak ({result.treatment_support.optimal_dosage.toFixed(2)})
              </text>
            </g>
          )}

          {/* Axes */}
          <line x1={padX} y1={height - padY} x2={width - padX} y2={height - padY} stroke="#94a3b8" strokeWidth="1.5" />
          <line x1={padX} y1={padY} x2={padX} y2={height - padY} stroke="#94a3b8" strokeWidth="1.5" />

          {/* Axis Labels */}
          <text x={width / 2} y={height - 8} fill="#94a3b8" fontSize="11" textAnchor="middle">
            Continuous Treatment Dosage (A)
          </text>
          <text
            x={12}
            y={height / 2}
            fill="#94a3b8"
            fontSize="11"
            textAnchor="middle"
            transform={`rotate(-90, 12, ${height / 2})`}
          >
            Estimated Response E[Y(a)]
          </text>
        </svg>
      </div>
    );
  };

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-sky-500/10 border border-sky-500/20 rounded-xl text-sky-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Continuous Policy Shift & Doubly Robust Dosage Response
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  Kennedy (2017) DML
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates arbitrary continuous treatment levels, counterfactual policy interventions (A + &delta;), and optimal dosages using doubly robust kernel-weighted transformations.
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
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-500 hover:to-cyan-500 rounded-xl shadow-lg shadow-sky-900/30 transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Computing DML Surface...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Estimate Policy Shift
              </>
            )}
          </button>
        </div>
      </div>

      {/* Control Configuration Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 p-4 bg-slate-900/40 rounded-xl border border-slate-700/50 text-xs">
        {/* Outcome Selector */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-sky-400" />
            Outcome Variable (Y)
          </label>
          <select
            value={outcomeId}
            onChange={e => setOutcomeId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
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
            Continuous Treatment (A)
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

        {/* Policy Shift Delta Slider */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-emerald-400" />
              Policy Shift (&delta;)
            </span>
            <span className="text-emerald-400 font-mono">+{shiftDelta.toFixed(1)}</span>
          </label>
          <input
            type="range"
            min={0.1}
            max={5.0}
            step={0.1}
            value={shiftDelta}
            onChange={e => setShiftDelta(parseFloat(e.target.value))}
            className="w-full accent-emerald-500"
          />
          <span className="text-[10px] text-slate-400">Hypothetical increase per respondent</span>
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

        {/* Advanced Settings Row */}
        <div className="md:col-span-3 lg:col-span-4 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="text-slate-400 font-medium">Grid Points:</span>
            <input
              type="number"
              min={10}
              max={50}
              value={gridPoints}
              onChange={e => setGridPoints(parseInt(e.target.value) || 25)}
              className="w-16 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-center"
            />
          </div>

          <div className="flex items-center gap-3">
            <span className="text-slate-400 font-medium">Custom Bandwidth h:</span>
            <input
              type="number"
              step={0.05}
              min={0}
              placeholder="Auto (Silverman)"
              value={customBandwidth || ''}
              onChange={e => setCustomBandwidth(parseFloat(e.target.value) || 0)}
              className="w-28 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-center"
            />
            <span className="text-[10px] text-slate-500">(0 = automatic Gaussian kernel plug-in)</span>
          </div>

          {/* Confounders Selection Checklist */}
          <div className="flex-1 min-w-[240px]">
            <span className="text-slate-400 font-medium mr-2">Confounders (W):</span>
            <div className="inline-flex flex-wrap gap-1.5 mt-1">
              {questions
                .filter(q => q.id !== outcomeId && q.id !== treatmentId)
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
                          ? 'bg-sky-500/20 border-sky-500/50 text-sky-200'
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

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Key KPI Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Policy Shift Effect */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Average Policy Effect</span>
                <Sparkles className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight flex items-baseline gap-1.5">
                <span>{result.policy_shift ? (result.policy_shift.average_policy_effect > 0 ? '+' : '') + result.policy_shift.average_policy_effect.toFixed(3) : 'N/A'}</span>
                <span className="text-xs text-slate-400">units</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                <span>p = {result.policy_shift?.p_value !== undefined ? (result.policy_shift.p_value < 0.001 ? '< .001' : result.policy_shift.p_value.toFixed(3)) : 'N/A'}</span>
                <span className="text-emerald-400 font-medium">
                  {result.policy_shift && result.policy_shift.p_value < 0.05 ? 'Statistically Sig.' : 'Inconclusive'}
                </span>
              </div>
            </div>

            {/* Current Mean */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Current Mean Dosage</span>
                <Activity className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.treatment_support?.current_mean.toFixed(2) ?? 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Range: [{result.treatment_support?.min_evaluated.toFixed(1)}, {result.treatment_support?.max_evaluated.toFixed(1)}]
              </div>
            </div>

            {/* Optimal Counterfactual Dosage */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Optimal Peak Dosage</span>
                <Target className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight text-sky-400">
                {result.treatment_support?.optimal_dosage.toFixed(2) ?? 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Yields maximum predicted outcome
              </div>
            </div>

            {/* Kernel Bandwidth & Sample */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Kernel Bandwidth (h)</span>
                <Sliders className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.bandwidth?.toFixed(3) ?? 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                N = {result.sample_size} valid observations
              </div>
            </div>
          </div>

          {/* Interactive Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-700/60 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('curve')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'curve'
                  ? 'border-sky-400 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              Dose-Response Curve
            </button>
            <button
              onClick={() => setActiveTab('policy')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'policy'
                  ? 'border-sky-400 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              Policy Shift (&Delta; = +{result.policy_shift?.delta_shift})
            </button>
            <button
              onClick={() => setActiveTab('table')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'table'
                  ? 'border-sky-400 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Dosage Grid Table
            </button>
            <button
              onClick={() => setActiveTab('methodology')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'methodology'
                  ? 'border-sky-400 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5" />
              APA Narrative & Foundations
            </button>
          </div>

          {/* Tab 1: Curve */}
          {activeTab === 'curve' && (
            <div className="space-y-4">
              {renderDoseResponseSVG()}

              <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-700/40 text-xs text-slate-300 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>
                    Nonparametric Doubly Robust Pseudo-Outcome regression: protects against either propensity or outcome model misspecification.
                  </span>
                </div>
                <span className="text-[11px] text-slate-400">Kennedy et al. (2017 JASA)</span>
              </div>
            </div>
          )}

          {/* Tab 2: Policy Counterfactual */}
          {activeTab === 'policy' && (
            <div className="p-5 bg-slate-900/60 rounded-xl border border-slate-700/60 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-sky-400" />
                  Counterfactual Policy Intervention: E[Y(A + &delta;)] - E[Y(A)]
                </h4>
                <span className="text-xs px-2.5 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono">
                  &delta; = +{result.policy_shift?.delta_shift}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {result.policy_shift?.interpretation}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-2">
                <div className="p-3 bg-slate-800/80 rounded-lg border border-slate-700">
                  <span className="text-slate-400 block mb-0.5">Average Treatment Effect (&Delta;):</span>
                  <span className="text-base font-bold text-white">
                    {result.policy_shift?.average_policy_effect.toFixed(4)}
                  </span>
                </div>
                <div className="p-3 bg-slate-800/80 rounded-lg border border-slate-700">
                  <span className="text-slate-400 block mb-0.5">Standard Error (SE):</span>
                  <span className="text-base font-bold text-white">
                    {result.policy_shift?.se.toFixed(4)}
                  </span>
                </div>
                <div className="p-3 bg-slate-800/80 rounded-lg border border-slate-700">
                  <span className="text-slate-400 block mb-0.5">95% Confidence Interval:</span>
                  <span className="text-base font-bold text-white">
                    [{result.policy_shift?.ci_95[0].toFixed(3)}, {result.policy_shift?.ci_95[1].toFixed(3)}]
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Grid Table */}
          {activeTab === 'table' && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Dosage Level (a)</th>
                    <th className="py-2.5 px-3">E[Y(a)] Response</th>
                    <th className="py-2.5 px-3">95% CI Lower</th>
                    <th className="py-2.5 px-3">95% CI Upper</th>
                    <th className="py-2.5 px-3">Marginal Derivative &mu;'(a)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {result.dose_response_curve?.map((pt, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-sky-300">{pt.dosage_level.toFixed(2)}</td>
                      <td className="py-2 px-3 font-semibold text-white">{pt.outcome_estimate.toFixed(3)}</td>
                      <td className="py-2 px-3 text-slate-400">{pt.ci_95[0].toFixed(3)}</td>
                      <td className="py-2 px-3 text-slate-400">{pt.ci_95[1].toFixed(3)}</td>
                      <td className="py-2 px-3">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          pt.marginal_derivative > 0
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : 'bg-rose-500/20 text-rose-300'
                        }`}>
                          {pt.marginal_derivative > 0 ? '+' : ''}{pt.marginal_derivative.toFixed(4)}
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
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-sky-400 hover:text-sky-300 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 rounded-lg transition-all"
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
                <div className="font-semibold text-slate-200">Econometric & Causal Foundations:</div>
                <p>
                  1. <strong className="text-slate-300">Doubly Robust Transformation:</strong> Constructs transformed pseudo-outcomes
                  &xi;(Y, A, X) = &mu;(A, X) + (Y - &mu;(A, X)) * g(A) / f(A|X). Even if the conditional density f(A|X) or the outcome surface &mu;(A, X) is misspecified, the dosage response estimate converges at the nonparametric rate &radic;n.
                </p>
                <p>
                  2. <strong className="text-slate-300">Continuous Shift Counterfactuals:</strong> Unlike binary treatment models that force an artificial 0/1 binarization, policy shifts evaluate natural reforms such as increasing educational intervention or incentive bonuses by &delta; units across heterogeneous populations (Kennedy et al., 2017).
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
