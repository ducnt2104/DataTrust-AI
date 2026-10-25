import React, { useState } from 'react';
import {
  Trees,
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
  Filter,
  Sparkles,
  PieChart
} from 'lucide-react';
import { api } from '../api/client';
import { BCFRequest, BCFResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface BCFCardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const BCFCard: React.FC<BCFCardProps> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [nDraws, setNDraws] = useState<number>(500);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BCFResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [sampleSearch, setSampleSearch] = useState<string>('');

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId || selectedCovariates.length === 0) {
      setError('Vui lòng chọn Biến kết quả (Y), Biến can thiệp (W) và ít nhất 1 Biến kiểm soát/điều hòa (X).');
      return;
    }
    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả và Biến can thiệp không được trùng lặp.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: BCFRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      covariate_question_ids: selectedCovariates.filter(
        (id) => id !== outcomeQId && id !== treatmentQId
      ),
      n_posterior_draws: nDraws,
      alpha_ridge: 1.0,
      scope: scope
    };

    try {
      const res = await api.runBCF(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể thực hiện phân tích Bayesian Causal Forest.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng Bayesian Causal Forest.');
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

  const filteredIndividualSample = (result?.individual_sample || []).filter((u) => {
    if (sampleSearch) {
      const q = sampleSearch.toLowerCase();
      return u.unit_id.toString().includes(q);
    }
    return true;
  });

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-teal-50 dark:bg-teal-950/60 rounded-lg border border-teal-200 dark:border-teal-800">
            <Trees className="w-5 h-5 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Bayesian Causal Forest (BCF)
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300">
                Hahn, Murray, &amp; Carver (2020)
              </span>
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Phân tách hàm tiên lượng &mu;(X, &pi;) và hàm điều hòa can thiệp &tau;(X), triệt tiêu thiên lệch Regularization-Induced Confounding (RIC).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !outcomeQId || !treatmentQId || selectedCovariates.length === 0}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm ${
              loading || !outcomeQId || !treatmentQId || selectedCovariates.length === 0
                ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
                : 'bg-teal-600 hover:bg-teal-700 text-white hover:shadow'
            }`}
          >
            {loading ? (
              <>
                <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                Đang lấy mẫu hậu nghiệm...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2 fill-current" />
                Lấy mẫu Hậu nghiệm BCF
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
            Biến kết quả (Y):
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
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
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
          >
            <option value="">-- Chọn biến can thiệp (0 hoặc 1) --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Number of Posterior Draws */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Số mẫu hậu nghiệm (Draws):
          </label>
          <select
            value={nDraws}
            onChange={(e) => setNDraws(parseInt(e.target.value))}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
          >
            <option value={250}>250 mẫu (Nhanh)</option>
            <option value={500}>500 mẫu (Khuyến nghị)</option>
            <option value={1000}>1,000 mẫu (Chính xác cao)</option>
          </select>
        </div>

        {/* Scope */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Phạm vi dữ liệu:
          </label>
          <div className="inline-flex rounded-md shadow-sm w-full">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={`flex-1 px-3 py-2 text-xs font-medium rounded-l-md border ${
                scope === 'all'
                  ? 'bg-teal-100 text-teal-700 border-teal-300 dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
              }`}
            >
              Tất cả
            </button>
            <button
              type="button"
              onClick={() => setScope('verified_clean')}
              className={`flex-1 px-3 py-2 text-xs font-medium rounded-r-md border-t border-b border-r ${
                scope === 'verified_clean'
                  ? 'bg-teal-100 text-teal-700 border-teal-300 dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
              }`}
            >
              Verified Clean
            </button>
          </div>
        </div>

        {/* Covariates Multi-Select */}
        <div className="col-span-1 md:col-span-2 lg:col-span-4 space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Biến gây nhiễu &amp; điều hòa hiệu ứng (X):</span>
            <span className="text-slate-400 font-normal">Đã chọn {selectedCovariates.length} biến</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
            {questions
              .filter((q) => q.id !== outcomeQId && q.id !== treatmentQId)
              .map((q) => {
                const isSelected = selectedCovariates.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleCovariate(q.id)}
                    className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                      isSelected
                        ? 'bg-teal-50 dark:bg-teal-950/80 border-teal-300 dark:border-teal-700 text-teal-700 dark:text-teal-300 font-medium'
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-teal-50/70 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800">
              <div className="text-xs text-teal-700 dark:text-teal-300 font-semibold flex items-center justify-between">
                <span>ATE Hậu nghiệm (Posterior Mean)</span>
                <span className="text-[10px] bg-teal-200 dark:bg-teal-900 px-1.5 py-0.5 rounded text-teal-800 dark:text-teal-200">
                  {result.overall_summary.posterior_draws_count} Draws
                </span>
              </div>
              <div className="text-3xl font-extrabold text-teal-700 dark:text-teal-400 mt-1">
                {result.overall_summary.posterior_ate_mean.toFixed(3)}
              </div>
              <div className="text-xs text-teal-600 dark:text-teal-400 mt-1 font-mono">
                95% CI: [{result.overall_summary.posterior_ate_ci_95[0].toFixed(2)}, {result.overall_summary.posterior_ate_ci_95[1].toFixed(2)}]
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Xác suất Hiệu ứng Dương P(ATE &gt; 0)</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1 flex items-center gap-1.5">
                <Sparkles className="w-5 h-5 text-teal-500" />
                {(result.overall_summary.posterior_prob_positive_ate * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                SE hậu nghiệm: {result.overall_summary.posterior_ate_se.toFixed(3)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Độ biến thiên CATE (Heterogeneity SD)</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1 font-mono">
                {result.overall_summary.treatment_heterogeneity_sd.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Mức phân hóa hiệu ứng giữa các cá thể
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900">
              <div className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">RIC Triệt tiêu Confounding</div>
              <div className="text-lg font-bold text-indigo-700 dark:text-indigo-300 mt-1 flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                Đã chỉnh thiên lệch
              </div>
              <div className="text-xs text-indigo-500 mt-0.5">
                Đưa &pi;(X) vào hàm &mu;(X, &pi;)
              </div>
            </div>
          </div>

          {/* Bayesian Variance Decomposition Bar */}
          {result.overall_summary.variance_decomposition && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <PieChart className="w-4 h-4 text-teal-500" />
                  Phân rã Phương sai Hậu nghiệm (Bayesian Variance Decomposition)
                </span>
                <span className="text-slate-500">Tổng biến thiên kết quả Y</span>
              </div>

              {/* Progress bar */}
              <div className="w-full h-3 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${result.overall_summary.variance_decomposition.prognostic_baseline_pct}%` }}
                  className="bg-indigo-500 h-full"
                  title={`Tiên lượng nền (Prognostic): ${result.overall_summary.variance_decomposition.prognostic_baseline_pct}%`}
                />
                <div
                  style={{ width: `${result.overall_summary.variance_decomposition.treatment_effect_pct}%` }}
                  className="bg-teal-500 h-full"
                  title={`Hiệu ứng can thiệp (Treatment): ${result.overall_summary.variance_decomposition.treatment_effect_pct}%`}
                />
                <div
                  style={{ width: `${result.overall_summary.variance_decomposition.residual_noise_pct}%` }}
                  className="bg-slate-400 h-full"
                  title={`Nhiễu dư (Noise): ${result.overall_summary.variance_decomposition.residual_noise_pct}%`}
                />
              </div>

              {/* Legend */}
              <div className="flex flex-wrap items-center gap-6 pt-1 text-xs text-slate-600 dark:text-slate-400">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block" />
                  <span>Tiên lượng nền &mu;(X, &pi;): <strong>{result.overall_summary.variance_decomposition.prognostic_baseline_pct}%</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-teal-500 inline-block" />
                  <span>Biến thiên can thiệp &tau;(X): <strong>{result.overall_summary.variance_decomposition.treatment_effect_pct}%</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block" />
                  <span>Nhiễu ngẫu nhiên &epsilon;: <strong>{result.overall_summary.variance_decomposition.residual_noise_pct}%</strong></span>
                </div>
              </div>
            </div>
          )}

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-inner overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-2">
                <Activity className="w-4 h-4 text-teal-400" />
                Mật độ Hậu nghiệm ATE &amp; Phân nhóm Can thiệp Mục tiêu (BCF Posterior)
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Subgroups Table */}
          {result.subgroups && result.subgroups.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-teal-500" />
                Phân đoạn Mục tiêu Tối ưu được Phát hiện (Discovered Sub-populations)
              </h4>
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold">
                    <tr>
                      <th className="px-4 py-3">Tên Phân đoạn</th>
                      <th className="px-3 py-3">Quy tắc Phân hoạch</th>
                      <th className="px-3 py-3 text-right">Số mẫu (N)</th>
                      <th className="px-3 py-3 text-right">CATE Hậu nghiệm</th>
                      <th className="px-3 py-3 text-right">95% Credible Interval</th>
                      <th className="px-3 py-3 text-right">P(&tau; &gt; 0)</th>
                      <th className="px-4 py-3 text-center">Khuyến nghị Mục tiêu</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900">
                    {result.subgroups.map((sg, idx) => {
                      const isHigh = sg.targeting_tier === 'HIGH_PRIORITY';
                      const isContra = sg.targeting_tier === 'CONTRAINDICATED';

                      const badgeCls = isHigh
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800'
                        : isContra
                        ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border-rose-300 dark:border-rose-800'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border-amber-300 dark:border-amber-800';

                      return (
                        <tr key={idx} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                          <td className="px-4 py-2.5 font-medium text-slate-900 dark:text-slate-100">
                            {sg.segment_name}
                          </td>
                          <td className="px-3 py-2.5 font-mono text-slate-600 dark:text-slate-400">
                            {sg.rule}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-700 dark:text-slate-300">
                            {sg.sample_size}
                          </td>
                          <td className="px-3 py-2.5 text-right font-bold text-slate-900 dark:text-slate-100">
                            {sg.cate_mean.toFixed(3)}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-600 dark:text-slate-400">
                            [{sg.credible_interval_95[0].toFixed(2)}, {sg.credible_interval_95[1].toFixed(2)}]
                          </td>
                          <td className="px-3 py-2.5 text-right font-semibold text-teal-600 dark:text-teal-400">
                            {(sg.posterior_prob_positive * 100).toFixed(1)}%
                          </td>
                          <td className="px-4 py-2.5 text-center">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${badgeCls}`}>
                              {sg.targeting_tier}
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
          {result.individual_sample && result.individual_sample.length > 0 && (
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-teal-500" />
                  Mẫu Dự báo CATE Cá thể &amp; Điểm số Tiên lượng
                </h4>

                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
                  <input
                    type="text"
                    placeholder="Tìm ID cá thể..."
                    value={sampleSearch}
                    onChange={(e) => setSampleSearch(e.target.value)}
                    className="text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 max-h-72 overflow-y-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="px-3 py-2.5">Unit ID</th>
                      <th className="px-3 py-2.5 text-center">W quan sát</th>
                      <th className="px-3 py-2.5 text-right">Y quan sát</th>
                      <th className="px-3 py-2.5 text-right">Propensity &pi;(X)</th>
                      <th className="px-3 py-2.5 text-right">Tiên lượng &mu;(X, &pi;)</th>
                      <th className="px-3 py-2.5 text-right">CATE Hậu nghiệm</th>
                      <th className="px-3 py-2.5 text-right">95% Credible Interval</th>
                      <th className="px-3 py-2.5 text-right">P(&tau; &gt; 0)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900 font-mono">
                    {filteredIndividualSample.map((u) => {
                      const isPositive = u.cate_mean > 0;
                      return (
                        <tr key={u.unit_id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                          <td className="px-3 py-2 font-bold text-slate-900 dark:text-slate-100">
                            #{u.unit_id}
                          </td>
                          <td className="px-3 py-2 text-center">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                u.treatment_w === 1
                                  ? 'bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300'
                                  : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                              }`}
                            >
                              {u.treatment_w === 1 ? 'Treated' : 'Control'}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-right text-slate-800 dark:text-slate-200">
                            {u.outcome_y.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right text-slate-600 dark:text-slate-400">
                            {u.propensity_pi.toFixed(3)}
                          </td>
                          <td className="px-3 py-2 text-right text-indigo-600 dark:text-indigo-400">
                            {u.prognostic_mu.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right font-bold text-slate-900 dark:text-slate-100">
                            {u.cate_mean.toFixed(3)}
                          </td>
                          <td className="px-3 py-2 text-right text-slate-600 dark:text-slate-400">
                            [{u.cate_ci_95[0].toFixed(2)}, {u.cate_ci_95[1].toFixed(2)}]
                          </td>
                          <td className="px-3 py-2 text-right font-semibold text-teal-600 dark:text-teal-400">
                            {(u.prob_positive * 100).toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-teal-50/50 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-900 dark:text-teal-300 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  Báo cáo Thống kê &amp; Trình bày Chuẩn APA 7th
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="text-xs text-teal-700 dark:text-teal-300 hover:text-teal-900 dark:hover:text-teal-100 flex items-center gap-1 font-medium transition-colors"
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
