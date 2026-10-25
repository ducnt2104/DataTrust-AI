import React, { useState } from 'react';
import {
  ShieldAlert,
  Play,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Info,
  Copy,
  Sliders,
  Layers,
  Activity,
  Award,
  TrendingDown,
  TrendingUp,
  Percent,
  Search,
  Filter
} from 'lucide-react';
import { api } from '../api/client';
import { ConformalCounterfactualRequest, ConformalCounterfactualResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface ConformalCounterfactualCardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const ConformalCounterfactualCard: React.FC<ConformalCounterfactualCardProps> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [subgroupQId, setSubgroupQId] = useState<string>('');
  const [miscoverageAlpha, setMiscoverageAlpha] = useState<number>(0.10);
  const [calibrationRatio, setCalibrationRatio] = useState<number>(0.50);
  const [usePropensityWeighting, setUsePropensityWeighting] = useState<boolean>(true);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConformalCounterfactualResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [sampleSearch, setSampleSearch] = useState<string>('');
  const [sampleFilter, setSampleFilter] = useState<'all' | 'downside' | 'beneficial'>('all');

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId) {
      setError('Vui lòng chọn Biến kết quả (Y) và Biến can thiệp (W).');
      return;
    }
    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả và Biến can thiệp không được trùng lặp.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: ConformalCounterfactualRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      covariate_question_ids: selectedCovariates.filter(
        (id) => id !== outcomeQId && id !== treatmentQId && id !== subgroupQId
      ),
      miscoverage_alpha: miscoverageAlpha,
      calibration_ratio: calibrationRatio,
      use_propensity_weighting: usePropensityWeighting,
      subgroup_question_id: subgroupQId || undefined,
      scope: scope
    };

    try {
      const res = await api.runConformalCounterfactual(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể thực hiện phân tích Conformal Counterfactual.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng Conformal Counterfactual.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredIndividualSample = (result?.individual_predictions_sample || []).filter((u) => {
    if (sampleFilter === 'downside' && !u.downside_risk) return false;
    if (sampleFilter === 'beneficial' && u.ite_conformal_interval[0] <= 0) return false;
    if (sampleSearch) {
      const q = sampleSearch.toLowerCase();
      return (
        u.unit_id.toString().includes(q) ||
        u.risk_status.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-sky-50 dark:bg-sky-950/60 rounded-lg border border-sky-200 dark:border-sky-800">
            <ShieldAlert className="w-5 h-5 text-sky-600 dark:text-sky-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Conformal Counterfactual Risk Inference
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-sky-100 dark:bg-sky-900 text-sky-700 dark:text-sky-300">
                Chernozhukov &amp; Lei (2021)
              </span>
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Khoảng tin cậy phản thực nghiệm phân bố tự do (Distribution-Free Conformal Bands), kiểm soát rủi ro tổn hại cá thể và phân định chính sách.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !outcomeQId || !treatmentQId}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm ${
              loading || !outcomeQId || !treatmentQId
                ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
                : 'bg-sky-600 hover:bg-sky-700 text-white hover:shadow'
            }`}
          >
            {loading ? (
              <>
                <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                Đang hiệu chuẩn...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2 fill-current" />
                Ước lượng Conformal ITE
              </>
            )}
          </button>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50/70 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800">
        {/* Outcome Y */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Biến kết quả liên tục (Y):
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-sky-500"
          >
            <option value="">-- Chọn câu hỏi kết quả --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Treatment W */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Biến can thiệp (W):
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-sky-500"
          >
            <option value="">-- Chọn biến can thiệp (0 hoặc 1) --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Subgroup Optional */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Phân nhóm rủi ro (Subgroup - Tuỳ chọn):
          </label>
          <select
            value={subgroupQId}
            onChange={(e) => setSubgroupQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-sky-500"
          >
            <option value="">-- Tự động theo phân vị Propensity --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Miscoverage Alpha */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Mức độ tin cậy Conformal (1 - α):
          </label>
          <select
            value={miscoverageAlpha}
            onChange={(e) => setMiscoverageAlpha(parseFloat(e.target.value))}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-sky-500"
          >
            <option value={0.10}>90% Coverage (α = 0.10) [Khuyến nghị]</option>
            <option value={0.05}>95% Coverage (α = 0.05) [Nghiêm ngặt]</option>
            <option value={0.20}>80% Coverage (α = 0.20) [Băng hẹp]</option>
          </select>
        </div>

        {/* Calibration Ratio & Weights & Scope */}
        <div className="col-span-1 md:col-span-2 lg:col-span-4 flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-6">
            <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={usePropensityWeighting}
                onChange={(e) => setUsePropensityWeighting(e.target.checked)}
                className="rounded border-slate-300 text-sky-600 focus:ring-sky-500"
              />
              Trọng số Propensity Covariate Shift (Tibshirani et al. 2019)
            </label>

            <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
              <span>Tỷ lệ Calibration:</span>
              <select
                value={calibrationRatio}
                onChange={(e) => setCalibrationRatio(parseFloat(e.target.value))}
                className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 py-1"
              >
                <option value={0.30}>30% Calibration / 70% Train</option>
                <option value={0.50}>50% Calibration / 50% Train (Chuẩn)</option>
                <option value={0.60}>60% Calibration / 40% Train</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
            <span>Phạm vi:</span>
            <div className="inline-flex rounded-md shadow-sm">
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`px-2.5 py-1 text-xs font-medium rounded-l-md border ${
                  scope === 'all'
                    ? 'bg-sky-100 text-sky-700 border-sky-300 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-800'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                }`}
              >
                Tất cả
              </button>
              <button
                type="button"
                onClick={() => setScope('verified_clean')}
                className={`px-2.5 py-1 text-xs font-medium rounded-r-md border-t border-b border-r ${
                  scope === 'verified_clean'
                    ? 'bg-sky-100 text-sky-700 border-sky-300 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-800'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                }`}
              >
                Verified Clean
              </button>
            </div>
          </div>
        </div>

        {/* Covariates Multi-Select */}
        <div className="col-span-1 md:col-span-2 lg:col-span-4 space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Biến kiểm soát &amp; không đồng nhất (X):</span>
            <span className="text-slate-400 font-normal">Đã chọn {selectedCovariates.length} biến</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
            {questions
              .filter((q) => q.id !== outcomeQId && q.id !== treatmentQId && q.id !== subgroupQId)
              .map((q) => {
                const isSelected = selectedCovariates.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleCovariate(q.id)}
                    className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                      isSelected
                        ? 'bg-sky-50 dark:bg-sky-950/80 border-sky-300 dark:border-sky-700 text-sky-700 dark:text-sky-300 font-medium'
                        : 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
                    }`}
                  >
                    {q.title}
                  </button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/80 text-rose-700 dark:text-rose-300 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
          <div className="text-sm font-medium">{error}</div>
        </div>
      )}

      {/* Result Section */}
      {result && result.overall_summary && (
        <div className="space-y-6 pt-2">
          {/* KPI Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Bảo đảm Phủ Conformal</div>
              <div className="text-2xl font-bold text-sky-600 dark:text-sky-400 mt-1">
                {result.overall_summary.target_coverage_pct}%
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Băng ITE: &plusmn;{result.calibration_diagnostics?.ite_band_half_width ?? '0.00'}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">ATE Trung bình Mẫu</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                {result.overall_summary.estimated_ate.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                CI: [{result.overall_summary.ate_conformal_interval[0].toFixed(2)}, {result.overall_summary.ate_conformal_interval[1].toFixed(2)}]
              </div>
            </div>

            <div className="p-4 rounded-xl bg-rose-50/60 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900">
              <div className="text-xs text-rose-600 dark:text-rose-400 font-medium">Tỷ lệ Rủi ro Tổn hại</div>
              <div className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1 flex items-center gap-1">
                <TrendingDown className="w-5 h-5" />
                {(result.overall_summary.downside_risk_rate * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-rose-500 mt-0.5">
                {Math.round(result.overall_summary.downside_risk_rate * result.overall_summary.sample_size)} / {result.overall_summary.sample_size} cá thể
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900">
              <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Lợi ích Chắc chắn (Lower &gt; 0)</div>
              <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1">
                <TrendingUp className="w-5 h-5" />
                {(result.overall_summary.strictly_beneficial_rate * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-emerald-500 mt-0.5">
                Lợi ích tối thiểu &gt; 0
              </div>
            </div>

            <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900">
              <div className="text-xs text-amber-600 dark:text-amber-400 font-medium">CVaR (5% Đuôi rủi ro)</div>
              <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                {result.overall_summary.cvar_downside_5pct.toFixed(2)}
              </div>
              <div className="text-xs text-amber-500 mt-0.5">
                Expected Shortfall 5%
              </div>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-inner overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-2">
                <Activity className="w-4 h-4 text-sky-400" />
                Biểu đồ Phản thực nghiệm &amp; Khoảng ITE Cá thể (Conformal Prediction Bands)
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Subgroup Risk Profiles Table */}
          {result.subgroup_risk_profiles && result.subgroup_risk_profiles.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-sky-500" />
                Phân tích Rủi ro &amp; Khuyến nghị Chính sách theo Phân nhóm (Subgroups)
              </h4>
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold">
                    <tr>
                      <th className="px-4 py-3">Phân nhóm</th>
                      <th className="px-3 py-3 text-right">Số mẫu (N)</th>
                      <th className="px-3 py-3 text-right">ITE Trung bình</th>
                      <th className="px-3 py-3 text-right">Khoảng Conformal</th>
                      <th className="px-3 py-3 text-right">Lợi ích chắc chắn</th>
                      <th className="px-3 py-3 text-right">Rủi ro tổn hại</th>
                      <th className="px-4 py-3">Khuyến nghị phân bổ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900">
                    {result.subgroup_risk_profiles.map((sg, idx) => {
                      const isRollout = sg.recommendation_code === 'ROLLOUT';
                      const isContra = sg.recommendation_code === 'CONTRAINDICATED';
                      const isSafeguards = sg.recommendation_code === 'SAFEGUARDS';

                      const badgeCls = isRollout
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800'
                        : isContra
                        ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border-rose-300 dark:border-rose-800'
                        : isSafeguards
                        ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border-amber-300 dark:border-amber-800'
                        : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950/80 dark:text-indigo-300 border-indigo-300 dark:border-indigo-800';

                      return (
                        <tr key={idx} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                          <td className="px-4 py-2.5 font-medium text-slate-900 dark:text-slate-100">
                            {sg.group_name}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-600 dark:text-slate-400">
                            {sg.sample_size}
                          </td>
                          <td className="px-3 py-2.5 text-right font-bold text-slate-900 dark:text-slate-100">
                            {sg.mean_ite.toFixed(3)}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-600 dark:text-slate-400">
                            [{sg.mean_ite_lower.toFixed(2)}, {sg.mean_ite_upper.toFixed(2)}]
                          </td>
                          <td className="px-3 py-2.5 text-right font-semibold text-emerald-600 dark:text-emerald-400">
                            {(sg.strictly_beneficial_rate * 100).toFixed(1)}%
                          </td>
                          <td className="px-3 py-2.5 text-right font-semibold text-rose-600 dark:text-rose-400">
                            {(sg.downside_risk_rate * 100).toFixed(1)}%
                          </td>
                          <td className="px-4 py-2.5">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${badgeCls}`}>
                              {sg.policy_recommendation}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Individual Predictions Sample Table */}
          {result.individual_predictions_sample && result.individual_predictions_sample.length > 0 && (
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-sky-500" />
                  Mẫu Dự báo Phản thực nghiệm &amp; Khoảng ITE Cá thể
                </h4>

                <div className="flex items-center gap-2">
                  {/* Search */}
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
                    <input
                      type="text"
                      placeholder="Tìm ID / Trạng thái..."
                      value={sampleSearch}
                      onChange={(e) => setSampleSearch(e.target.value)}
                      className="text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                    />
                  </div>

                  {/* Filter */}
                  <div className="inline-flex rounded-md shadow-sm">
                    <button
                      type="button"
                      onClick={() => setSampleFilter('all')}
                      className={`px-2 py-1 text-xs font-medium rounded-l-md border ${
                        sampleFilter === 'all'
                          ? 'bg-sky-100 text-sky-700 border-sky-300 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-800'
                          : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      Tất cả
                    </button>
                    <button
                      type="button"
                      onClick={() => setSampleFilter('downside')}
                      className={`px-2 py-1 text-xs font-medium border-t border-b ${
                        sampleFilter === 'downside'
                          ? 'bg-rose-100 text-rose-700 border-rose-300 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-800'
                          : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      Có rủi ro
                    </button>
                    <button
                      type="button"
                      onClick={() => setSampleFilter('beneficial')}
                      className={`px-2 py-1 text-xs font-medium rounded-r-md border-t border-b border-r ${
                        sampleFilter === 'beneficial'
                          ? 'bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800'
                          : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      Chắc chắn lợi
                    </button>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 max-h-72 overflow-y-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="px-3 py-2.5">Unit ID</th>
                      <th className="px-3 py-2.5 text-center">W quan sát</th>
                      <th className="px-3 py-2.5 text-right">Y quan sát</th>
                      <th className="px-3 py-2.5 text-right">Propensity e(X)</th>
                      <th className="px-3 py-2.5 text-right">Dự báo Y(1)</th>
                      <th className="px-3 py-2.5 text-right">Dự báo Y(0)</th>
                      <th className="px-3 py-2.5 text-right">ITE Điểm</th>
                      <th className="px-3 py-2.5 text-right">Khoảng ITE Conformal</th>
                      <th className="px-3 py-2.5">Đánh giá Rủi ro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900 font-mono">
                    {filteredIndividualSample.map((u) => {
                      const isBeneficial = u.ite_conformal_interval[0] > 0;
                      const isHarmful = u.ite_conformal_interval[1] < 0;

                      return (
                        <tr key={u.unit_id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                          <td className="px-3 py-2 font-bold text-slate-900 dark:text-slate-100">
                            #{u.unit_id}
                          </td>
                          <td className="px-3 py-2 text-center">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                u.treatment_observed === 1
                                  ? 'bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300'
                                  : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                              }`}
                            >
                              {u.treatment_observed === 1 ? 'Treated' : 'Control'}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-right text-slate-800 dark:text-slate-200">
                            {u.outcome_observed.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right text-slate-600 dark:text-slate-400">
                            {u.propensity_score.toFixed(3)}
                          </td>
                          <td className="px-3 py-2 text-right text-sky-600 dark:text-sky-400">
                            {u.predicted_y1.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right text-slate-600 dark:text-slate-400">
                            {u.predicted_y0.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right font-bold text-slate-900 dark:text-slate-100">
                            {u.ite_point_estimate.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right font-bold">
                            <span
                              className={
                                isBeneficial
                                  ? 'text-emerald-600 dark:text-emerald-400'
                                  : isHarmful
                                  ? 'text-rose-600 dark:text-rose-400'
                                  : 'text-amber-600 dark:text-amber-400'
                              }
                            >
                              [{u.ite_conformal_interval[0].toFixed(2)}, {u.ite_conformal_interval[1].toFixed(2)}]
                            </span>
                          </td>
                          <td className="px-3 py-2 font-sans">
                            <span
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                isBeneficial
                                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                                  : isHarmful
                                  ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                                  : u.downside_risk
                                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                                  : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                              }`}
                            >
                              {u.risk_status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Calibration Diagnostics */}
          {result.calibration_diagnostics && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
              <div className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                <Info className="w-4 h-4 text-sky-500" />
                Thông số Hiệu chuẩn Conformal &amp; Trùng lắp Propensity (Diagnostics)
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-slate-600 dark:text-slate-400 pt-1">
                <div>
                  <span className="text-slate-400">Propensity AUC:</span>{' '}
                  <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                    {result.calibration_diagnostics.propensity_auc.toFixed(3)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Vùng chồng chéo:</span>{' '}
                  <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                    [{result.calibration_diagnostics.propensity_overlap_min.toFixed(2)}, {result.calibration_diagnostics.propensity_overlap_max.toFixed(2)}]
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Mẫu Calibration (T / C):</span>{' '}
                  <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                    {result.calibration_diagnostics.treated_calibration_size} / {result.calibration_diagnostics.control_calibration_size}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Ngưỡng non-conformity (Q1 / Q0):</span>{' '}
                  <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                    {result.calibration_diagnostics.treated_nonconformity_cutoff.toFixed(2)} / {result.calibration_diagnostics.control_nonconformity_cutoff.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-sky-50/50 dark:bg-sky-950/20 border border-sky-200 dark:border-sky-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-sky-900 dark:text-sky-300 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                  Báo cáo Thống kê &amp; Trình bày Chuẩn APA 7th
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="text-xs text-sky-700 dark:text-sky-300 hover:text-sky-900 dark:hover:text-sky-100 flex items-center gap-1 font-medium transition-colors"
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
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
              <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 italic font-serif">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
