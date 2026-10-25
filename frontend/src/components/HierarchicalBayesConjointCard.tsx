import React, { useState } from 'react';
import {
  HierarchicalBayesConjointResult,
  HierarchicalBayesConjointRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  PieChart,
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
  DollarSign,
  ShoppingCart,
  Users,
  Target,
  BarChart2,
  Sparkles,
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

export const HierarchicalBayesConjointCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [choiceId, setChoiceId] = useState<string>(questions[0]?.id || '');
  const [respondentId, setRespondentId] = useState<string>(questions[1]?.id || questions[0]?.id || '');
  const [selectedAttributes, setSelectedAttributes] = useState<string[]>(
    questions.slice(2, 4).map(q => q.id)
  );
  const [priceId, setPriceId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HierarchicalBayesConjointResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState(false);
  const [activeTab, setActiveTab] = useState<'visualizer' | 'part_worths' | 'wtp' | 'simulator' | 'methodology'>('visualizer');

  const handleToggleAttribute = (id: string) => {
    setSelectedAttributes(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!choiceId || !respondentId) {
      setError('Please select both a choice selection question and a respondent identifier question.');
      return;
    }
    if (selectedAttributes.length === 0) {
      setError('Please select at least one product attribute for conjoint estimation.');
      return;
    }
    if (selectedAttributes.includes(choiceId) || selectedAttributes.includes(respondentId)) {
      setError('Attributes must be distinct from the choice and respondent questions.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: HierarchicalBayesConjointRequest = {
        choice_question_id: choiceId,
        respondent_question_id: respondentId,
        attribute_question_ids: selectedAttributes,
        price_question_id: priceId || undefined,
        scope
      };

      const res = await api.runHierarchicalBayesConjoint(surveyId, payload);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Insufficient conjoint choice task data.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to execute Conjoint Hierarchical Bayes estimation.');
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

  // Helper to find top attribute
  const topAttribute = result?.attribute_importance
    ? Object.entries(result.attribute_importance).sort((a, b) => b[1].mean_importance - a[1].mean_importance)[0]
    : null;

  const topSimulatorProduct = result?.market_simulation
    ? [...result.market_simulation].sort((a, b) => b.share_of_preference - a.share_of_preference)[0]
    : null;

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
              <ShoppingCart className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Choice-Based Conjoint Hierarchical Bayes (CBC-HB)
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  HB Choice Simulator
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Estimates respondent-level part-worth utilities (&beta;<sub>i</sub> ~ &Nu;(&mu;, &Sigma;)), Willingness-to-Pay (WTP), and counterfactual market share allocations under competitive choice dynamics.
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
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-xl shadow-lg shadow-emerald-900/30 transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Estimating Utilities...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Run CBC-HB Analysis
              </>
            )}
          </button>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-slate-900/40 rounded-xl border border-slate-700/50 text-xs">
        {/* Choice Selection Question */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            Choice Selection (1/0 or rating)
          </label>
          <select
            value={choiceId}
            onChange={e => setChoiceId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Respondent ID Question */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-sky-400" />
            Respondent Identifier
          </label>
          <select
            value={respondentId}
            onChange={e => setRespondentId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
          >
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 40 ? q.title.slice(0, 40) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Price Variable (Optional) */}
        <div>
          <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-amber-400" />
            Continuous Price (Optional for WTP)
          </label>
          <select
            value={priceId}
            onChange={e => setPriceId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-500"
          >
            <option value="">(None - Estimate Part-Worths Only)</option>
            {questions
              .filter(q => q.id !== choiceId && q.id !== respondentId)
              .map(q => (
                <option key={q.id} value={q.id}>
                  {q.title.length > 35 ? q.title.slice(0, 35) + '...' : q.title}
                </option>
              ))}
          </select>
        </div>

        {/* Data Scope */}
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
            <option value="verified_clean">Verified Clean (Anti-Fraud)</option>
          </select>
        </div>

        {/* Attribute Multi-Select Row */}
        <div className="md:col-span-2 lg:col-span-4 pt-2 border-t border-slate-800/80">
          <span className="text-slate-300 font-semibold block mb-1.5">Product Attributes for Discrete Choice Evaluation:</span>
          <div className="flex flex-wrap gap-2">
            {questions
              .filter(q => q.id !== choiceId && q.id !== respondentId && q.id !== priceId)
              .map(q => {
                const isSelected = selectedAttributes.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => handleToggleAttribute(q.id)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                      isSelected
                        ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-200'
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
            {/* Top Driving Attribute */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Top Driver of Choice</span>
                <Sparkles className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-xl font-bold text-white tracking-tight truncate">
                {topAttribute ? topAttribute[0].replace(/_/g, ' ') : 'N/A'}
              </div>
              <div className="text-[11px] text-emerald-400 mt-1 font-semibold">
                {topAttribute ? `${topAttribute[1].mean_importance.toFixed(1)}% Relative Importance` : ''}
              </div>
            </div>

            {/* Market Simulator Leader */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Simulated Market Leader</span>
                <TrendingUp className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-xl font-bold text-white tracking-tight truncate">
                {topSimulatorProduct?.product_name ?? 'N/A'}
              </div>
              <div className="text-[11px] text-sky-400 mt-1 font-semibold">
                {topSimulatorProduct ? `${topSimulatorProduct.share_of_preference.toFixed(1)}% Preference Share` : ''}
              </div>
            </div>

            {/* Respondent Pool */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Respondent Pool (N)</span>
                <Users className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.n_respondents}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Across {result.sample_size} total choice decisions
              </div>
            </div>

            {/* Attributes Evaluated */}
            <div className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Attributes Evaluated</span>
                <Layers className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {result.attribute_importance ? Object.keys(result.attribute_importance).length : 0}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                {result.part_worth_utilities?.length || 0} discrete levels calibrated
              </div>
            </div>
          </div>

          {/* Interactive Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-700/60 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('visualizer')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'visualizer'
                  ? 'border-emerald-400 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              Importance & Market Share Chart
            </button>
            <button
              onClick={() => setActiveTab('part_worths')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'part_worths'
                  ? 'border-emerald-400 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              Part-Worth Utilities Table
            </button>
            {result.wtp_estimates && Object.keys(result.wtp_estimates).length > 0 && (
              <button
                onClick={() => setActiveTab('wtp')}
                className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'wtp'
                    ? 'border-emerald-400 text-emerald-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <DollarSign className="w-3.5 h-3.5" />
                Willingness-to-Pay (WTP)
              </button>
            )}
            <button
              onClick={() => setActiveTab('simulator')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'simulator'
                  ? 'border-emerald-400 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShoppingCart className="w-3.5 h-3.5" />
              Market Choice Simulator
            </button>
            <button
              onClick={() => setActiveTab('methodology')}
              className={`px-3 py-2 border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'methodology'
                  ? 'border-emerald-400 text-emerald-400'
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
                    Hierarchical Bayes shrinks sparse individual choice responses toward the population mean (&mu;, &Sigma;), preventing overfitting.
                  </span>
                </div>
                <span className="text-[11px] text-slate-400">Rossi, Allenby, & McCulloch (2005)</span>
              </div>
            </div>
          )}

          {/* Tab 2: Part-Worth Utilities */}
          {activeTab === 'part_worths' && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Attribute</th>
                    <th className="py-2.5 px-3">Level / Feature</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Mean Part-Worth Utility (&beta;)</th>
                    <th className="py-2.5 px-3">Standard Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {result.part_worth_utilities?.map((pw, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-emerald-300 font-semibold">
                        {pw.attribute.replace(/_/g, ' ')}
                      </td>
                      <td className="py-2 px-3 text-white">
                        {pw.level.replace('_', ' ')}
                      </td>
                      <td className="py-2 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          pw.is_reference
                            ? 'bg-slate-700/60 text-slate-300'
                            : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {pw.is_reference ? 'Reference Level' : 'Estimated'}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-semibold">
                        {pw.is_reference ? '0.0000' : (pw.mean_part_worth > 0 ? `+${pw.mean_part_worth.toFixed(4)}` : pw.mean_part_worth.toFixed(4))}
                      </td>
                      <td className="py-2 px-3 text-slate-400">
                        {pw.is_reference ? '—' : pw.se.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: WTP Estimates */}
          {activeTab === 'wtp' && result.wtp_estimates && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Attribute</th>
                    <th className="py-2.5 px-3">Feature Level</th>
                    <th className="py-2.5 px-3">Mean WTP ($)</th>
                    <th className="py-2.5 px-3">Median WTP ($)</th>
                    <th className="py-2.5 px-3">95% Credible Interval</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {Object.entries(result.wtp_estimates).map(([key, wtp], idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-amber-300 font-semibold">
                        {wtp.attribute.replace(/_/g, ' ')}
                      </td>
                      <td className="py-2 px-3 text-white">
                        {wtp.level.replace('_', ' ')}
                      </td>
                      <td className="py-2 px-3 font-bold text-emerald-400">
                        ${wtp.mean_wtp > 0 ? `+${wtp.mean_wtp.toFixed(2)}` : wtp.mean_wtp.toFixed(2)}
                      </td>
                      <td className="py-2 px-3 text-slate-300">
                        ${wtp.median_wtp.toFixed(2)}
                      </td>
                      <td className="py-2 px-3 text-slate-400">
                        [${wtp.ci_95[0].toFixed(2)}, ${wtp.ci_95[1].toFixed(2)}]
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: Simulator */}
          {activeTab === 'simulator' && (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Product Profile Offering</th>
                    <th className="py-2.5 px-3">Share of Preference (Logit)</th>
                    <th className="py-2.5 px-3">First Choice Share</th>
                    <th className="py-2.5 px-3">Mean Net Utility</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono">
                  {result.market_simulation?.map((sim, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3 text-sky-300 font-semibold">{sim.product_name}</td>
                      <td className="py-2 px-3 font-bold text-white">
                        <span className="text-emerald-400">{sim.share_of_preference.toFixed(1)}%</span>
                      </td>
                      <td className="py-2 px-3 text-slate-300">
                        {sim.first_choice_share.toFixed(1)}%
                      </td>
                      <td className="py-2 px-3 text-slate-400">
                        {sim.mean_utility > 0 ? `+${sim.mean_utility.toFixed(3)}` : sim.mean_utility.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 5: APA Narrative */}
          {activeTab === 'methodology' && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-700/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-300">APA 7th Academic Summary</span>
                  <button
                    onClick={handleCopyNarrative}
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-lg transition-all"
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
                <div className="font-semibold text-slate-200">Econometric & Marketing Science Foundations:</div>
                <p>
                  1. <strong className="text-slate-300">Hierarchical Bayes Preference Shrinkage:</strong> Unlike aggregate logit which assumes homogeneous consumers or unconstrained individual logit which suffers from severe overfitting, CBC-HB assumes individual utilities follow a multivariate normal prior &beta;<sub>i</sub> ~ &Nu;(&mu;, &Sigma;), shrinking noisy respondent responses toward the population mean (Rossi et al., 2005).
                </p>
                <p>
                  2. <strong className="text-slate-300">Willingness-to-Pay (WTP) Derivation:</strong> WTP represents the monetary value consumers attach to a feature level, calculated by taking the ratio of the feature part-worth utility to the continuous negative price coefficient (-&beta;<sub>k</sub> / &beta;<sub>price</sub>).
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
