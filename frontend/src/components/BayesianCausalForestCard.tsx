import React, { useState } from 'react';
import {
  Trees,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  ShieldCheck,
  Sliders,
  Scale,
  Sparkles,
  BarChart3
} from 'lucide-react';
import { api } from '../api/client';
import {
  BayesianCausalForestResult,
  BayesianCausalForestRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const BayesianCausalForestCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [numMCMCDraws, setNumMCMCDraws] = useState<number>(200);
  const [credibilityLevel, setCredibilityLevel] = useState<number>(0.95);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BayesianCausalForestResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'quintiles' | 'cate_sample' | 'diagnostics'>('quintiles');

  const handleToggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!treatmentQId || !outcomeQId) {
      setError('Vui lòng chọn đầy đủ Biến Can thiệp (D) và Biến Kết quả (Y).');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: BayesianCausalForestRequest = {
      treatment_question_id: treatmentQId,
      outcome_question_id: outcomeQId,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      num_mcmc_draws: numMCMCDraws,
      credibility_level: credibilityLevel,
      scope: scope
    };

    try {
      const res = await api.runBayesianCausalForest(surveyId, payload);
      if (res.status === 'success') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể thực thi Bayesian Causal Forests.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 mb-8 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-lg shadow-sm">
            <Trees className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Rừng Cây Nhân quả Bayes (Bayesian Causal Forests - BCF)
              </h3>
              <span className="px-2 py-0.5 text-xs font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 rounded-full">
                Hahn, Murray, & Carvalho (2020)
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Hồi quy cây phụ gia Bayes (BART) với tiên nghiệm trơn mục tiêu π̂(X) triệt tiêu hoàn toàn sai chệch do hiệu chỉnh gây ra (RIC), cung cấp phân phối hậu nghiệm đầy đủ cho ATE, ATT và CATE
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowConfig(!showConfig)}
          className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title={showConfig ? 'Thu gọn cài đặt' : 'Mở rộng cài đặt'}
        >
          {showConfig ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {/* Configuration Form */}
      {showConfig && (
        <div className="bg-slate-50 dark:bg-slate-800/40 rounded-lg p-4 border border-slate-200 dark:border-slate-800 mb-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Can thiệp (Treatment D: 0/1) *
              </label>
              <select
                value={treatmentQId}
                onChange={e => setTreatmentQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Chọn biến can thiệp D --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Kết quả (Outcome Y) *
              </label>
              <select
                value={outcomeQId}
                onChange={e => setOutcomeQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Chọn biến Outcome Y --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Covariates multi-select */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Biến Đặc trưng Kiểm soát X (Covariates cho Thành phần Tiên lượng μ(x) và Hiệu ứng τ(x))
            </label>
            <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
              {questions
                .filter(q => q.id !== treatmentQId && q.id !== outcomeQId)
                .map(q => {
                  const isChecked = selectedCovariates.includes(q.id);
                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => handleToggleCovariate(q.id)}
                      className={`text-xs px-2.5 py-1 rounded-md border transition-all ${
                        isChecked
                          ? 'bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700 font-medium'
                          : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-300'
                      }`}
                    >
                      {isChecked ? '✓ ' : '+ '}
                      {q.title}
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Hyperparameters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-200 dark:border-slate-700/60">
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Số lần Lấy mẫu Hậu nghiệm MCMC: {numMCMCDraws}
                </label>
              </div>
              <input
                type="range"
                min="50"
                max="350"
                step="25"
                value={numMCMCDraws}
                onChange={e => setNumMCMCDraws(parseInt(e.target.value, 10))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Độ tin cậy Hậu nghiệm Bayes (Credible Level)
              </label>
              <select
                value={credibilityLevel}
                onChange={e => setCredibilityLevel(parseFloat(e.target.value))}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-blue-500"
              >
                <option value={0.90}>90% BCI (Credible Interval)</option>
                <option value={0.95}>95% BCI (Chuẩn mực Khoa học)</option>
                <option value={0.99}>99% BCI (Nghiêm ngặt cao)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Phạm vi dữ liệu phản hồi (Scope)
              </label>
              <select
                value={scope}
                onChange={e => setScope(e.target.value as any)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tất cả phản hồi hợp lệ (Toàn bộ mẫu)</option>
                <option value="verified_clean">Chỉ phản hồi đã xác minh sạch (DataTrust Verified)</option>
              </select>
            </div>
          </div>

          {/* Action button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  <span>Đang tính toán MCMC BCF...</span>
                </>
              ) : (
                <>
                  <Trees className="w-4 h-4" />
                  <span>Thực thi Bayesian Causal Forests</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">{error}</div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                ATE Posterior Mean
              </span>
              <div className="text-xl font-bold text-blue-600 dark:text-blue-400">
                {result.ate_estimates?.posterior_mean !== undefined
                  ? `${result.ate_estimates.posterior_mean > 0 ? '+' : ''}${result.ate_estimates.posterior_mean.toFixed(4)}`
                  : '—'}
              </div>
              <span className="text-[10px] text-slate-400">
                SD: {result.ate_estimates?.posterior_sd.toFixed(4)}
              </span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                95% Bayesian Credible Interval
              </span>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200 mt-1">
                [{result.ate_estimates?.ci_lower_95.toFixed(3)}, {result.ate_estimates?.ci_upper_95.toFixed(3)}]
              </div>
              <span className="text-[10px] text-slate-400">Khoảng tin cậy hậu nghiệm</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Xác suất Hiệu ứng Dương
              </span>
              <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                {result.ate_estimates?.prob_positive_effect !== undefined
                  ? `${(result.ate_estimates.prob_positive_effect * 100).toFixed(1)}%`
                  : '—'}
              </div>
              <span className="text-[10px] text-slate-400">P(ATE &gt; 0 | Dữ liệu)</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                ATT Posterior Mean
              </span>
              <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                {result.att_estimates?.posterior_mean !== undefined
                  ? `${result.att_estimates.posterior_mean > 0 ? '+' : ''}${result.att_estimates.posterior_mean.toFixed(4)}`
                  : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Hiệu ứng nhóm can thiệp</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                MCMC Effective Sample Size
              </span>
              <div className="text-xl font-bold text-purple-600 dark:text-purple-400">
                {result.mcmc_diagnostics?.effective_sample_size || result.mcmc_draws_count}
              </div>
              <span className="text-[10px] text-slate-400">
                Tổng draws: {result.mcmc_draws_count}
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/30 rounded-xl border border-slate-200 dark:border-slate-700 overflow-x-auto">
              <div
                className="w-full flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Tab Navigation */}
          <div className="border-b border-slate-200 dark:border-slate-800">
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveTab('quintiles')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'quintiles'
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Dị biệt CATE theo Ngũ phân vị Điểm xu hướng π̂(X)
              </button>
              <button
                onClick={() => setActiveTab('cate_sample')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'cate_sample'
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Mẫu Ước lượng Cá thể CATE & Phân rã Tiên lượng
              </button>
              <button
                onClick={() => setActiveTab('diagnostics')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'diagnostics'
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Chuẩn đoán Hội tụ MCMC & Khử Nhiễu RIC
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'quintiles' && result.propensity_quintiles && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400">
                    <th className="p-2.5 font-semibold">Ngũ phân vị Điểm xu hướng</th>
                    <th className="p-2.5 font-semibold">Số lượng quan sát</th>
                    <th className="p-2.5 font-semibold">CATE Hậu nghiệm Trung bình</th>
                    <th className="p-2.5 font-semibold">95% BCI [Cận dưới, Cận trên]</th>
                    <th className="p-2.5 font-semibold text-center">So sánh với ATE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {result.propensity_quintiles.map((q) => (
                    <tr key={q.quintile} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="p-2.5 font-medium">{q.quintile_label}</td>
                      <td className="p-2.5 font-mono">{q.sample_count}</td>
                      <td className="p-2.5 font-mono font-bold text-blue-600 dark:text-blue-400">
                        {q.cate_mean > 0 ? '+' : ''}{q.cate_mean.toFixed(4)}
                      </td>
                      <td className="p-2.5 font-mono">
                        [{q.cate_ci_lower.toFixed(4)}, {q.cate_ci_upper.toFixed(4)}]
                      </td>
                      <td className="p-2.5 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                          q.cate_mean > (result.ate_estimates?.posterior_mean || 0)
                            ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300'
                            : 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300'
                        }`}>
                          {q.cate_mean > (result.ate_estimates?.posterior_mean || 0) ? 'Cao hơn ATE' : 'Thấp hơn ATE'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'cate_sample' && result.sample_cate_estimates && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400">
                    <th className="p-2.5 font-semibold">Quan sát</th>
                    <th className="p-2.5 font-semibold">Can thiệp (D)</th>
                    <th className="p-2.5 font-semibold">Điểm xu hướng π̂(X)</th>
                    <th className="p-2.5 font-semibold">Mức Tiên lượng μ̂(X, π̂)</th>
                    <th className="p-2.5 font-semibold">CATE Điểm</th>
                    <th className="p-2.5 font-semibold">95% BCI [τ_L, τ_U]</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {result.sample_cate_estimates.map((pt) => (
                    <tr key={pt.observation_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="p-2.5 font-mono font-medium">#{pt.observation_id}</td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          pt.treatment === 1
                            ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                        }`}>
                          {pt.treatment === 1 ? 'Treated (D=1)' : 'Control (D=0)'}
                        </span>
                      </td>
                      <td className="p-2.5 font-mono">{pt.propensity_score.toFixed(4)}</td>
                      <td className="p-2.5 font-mono">{pt.prognostic_baseline.toFixed(4)}</td>
                      <td className="p-2.5 font-mono font-bold text-blue-600 dark:text-blue-400">
                        {pt.cate_point_estimate > 0 ? '+' : ''}{pt.cate_point_estimate.toFixed(4)}
                      </td>
                      <td className="p-2.5 font-mono">
                        [{pt.cate_lower_bci.toFixed(4)}, {pt.cate_upper_bci.toFixed(4)}]
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'diagnostics' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 font-semibold text-xs">
                  <Activity className="w-4 h-4" />
                  <span>Chuẩn đoán Lấy mẫu Hậu nghiệm MCMC</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Số lần lấy mẫu MCMC (S):</span>
                    <span className="font-mono font-semibold">{result.mcmc_draws_count}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Kích thước mẫu hiệu dụng (ESS):</span>
                    <span className="font-mono font-semibold">{result.mcmc_diagnostics?.effective_sample_size}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Độ lệch chuẩn phần dư hậu nghiệm (σ̂):</span>
                    <span className="font-mono font-semibold">{result.mcmc_diagnostics?.residual_std.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Phương sai phần dư hậu nghiệm (σ̂²):</span>
                    <span className="font-mono font-semibold">{result.mcmc_diagnostics?.residual_variance.toFixed(4)}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 font-semibold text-xs">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Cơ chế Khử Nhiễu Regularization-Induced Confounding (RIC)</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Khi các biến kiểm soát có tác động tiên lượng mạnh đồng thời dự báo mạnh việc tiếp nhận can thiệp, 
                  các phương pháp học máy thông thường (BART chuẩn, Causal Forest thông thường) có xu hướng kéo lùi 
                  ước lượng hiệu ứng về 0 do áp đặt cùng một cơ chế phạt hiệu chỉnh lên toàn bộ bề mặt kỳ vọng có điều kiện.
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  <strong>Bayesian Causal Forests (Hahn et al. 2020)</strong> giải quyết triệt để vấn đề này bằng cách:
                  (1) Tách bạch hoàn toàn bề mặt tiên lượng <code className="px-1 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">μ(x, π̂(x))</code> 
                  và bề mặt can thiệp <code className="px-1 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">τ(x)</code>;
                  (2) Đưa điểm xu hướng <code className="px-1 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">π̂(x)</code> 
                  vào làm đầu vào trực tiếp cho hàm tiên lượng, đảm bảo ước lượng không chệch và khoảng tin cậy Bayes chính xác.
                </p>
              </div>
            </div>
          )}

          {/* APA Narrative Block */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                  <span>Tường thuật Học thuật Chuẩn APA 7th Edition (DataTrust)</span>
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center space-x-1 px-2.5 py-1 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/60 rounded-md transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed italic border-l-2 border-blue-500 pl-3">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default BayesianCausalForestCard;
