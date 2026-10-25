import React, { useState } from 'react';
import {
  PieChart,
  Hash,
  Scale,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  Sparkles,
  RefreshCw,
  Info,
  CheckSquare,
  Square,
  BarChart3,
  Layers
} from 'lucide-react';
import { api } from '../api/client';
import { ZeroInflatedResult } from '../types/survey';

interface ZeroInflatedCountCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const ZeroInflatedCountCard: React.FC<ZeroInflatedCountCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ZeroInflatedResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [countQid, setCountQid] = useState<string>('');
  const [covariateQids, setCovariateQids] = useState<string[]>([]);
  const [inflationQids, setInflationQids] = useState<string[]>([]);
  const [modelType, setModelType] = useState<'ZIP' | 'ZINB'>('ZIP');
  const [useSeparateInflation, setUseSeparateInflation] = useState<boolean>(false);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'count_coeffs' | 'infl_coeffs' | 'frequency' | 'svg'>('count_coeffs');

  const toggleCovariate = (qid: string) => {
    setCovariateQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const toggleInflationCovariate = (qid: string) => {
    setInflationQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!countQid) {
      setError('Vui lòng chọn biến số đếm kết quả (Count Y: số lượt khám, phàn nàn, sự cố...).');
      return;
    }
    if (covariateQids.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến giải thích quá trình đếm (Count Covariates X).');
      return;
    }
    if (covariateQids.includes(countQid)) {
      setError('Biến số đếm kết quả không được nằm trong danh sách biến giải thích.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runZeroInflatedAnalysis(surveyId, {
        count_question_id: countQid,
        covariate_question_ids: covariateQids,
        inflation_covariate_question_ids: useSeparateInflation && inflationQids.length > 0 ? inflationQids : undefined,
        model_type: modelType,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình Zero-Inflated.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API Zero-Inflated Count Models.');
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-sky-500/10 border border-sky-500/20 rounded-xl text-sky-400">
            <Hash className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Zero-Inflated Count Regression Models (ZIP & ZINB)
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                Lambert (1992) · Greene (1994) · Vuong (1989)
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Phân tách quá trình tạo số liệu đếm có đột biến không: Quá trình Logit cho nhóm luôn bằng 0 (Structural Zeros) và quá trình Poisson / Âm nhị thức (Negative Binomial) cho tần suất biến cố.
            </p>
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-sky-600/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Đang ước lượng ZIP/ZINB (MLE)...</span>
            </>
          ) : (
            <>
              <Layers className="w-4 h-4" />
              <span>Chạy Hồi Quy Zero-Inflated</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 py-5 border-b border-slate-800 text-xs">
        {/* Count Question Y */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Biến Số Đếm (Count Y):</label>
          <select
            value={countQid}
            onChange={(e) => setCountQid(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">-- Chọn câu hỏi số đếm (0, 1, 2...) --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title.length > 45 ? `${q.title.slice(0, 45)}...` : q.title}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400">Số lần khám bệnh, số khiếu nại, số ngày vắng mặt.</p>
        </div>

        {/* Model Type */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Cơ Chế Phân Phối Đếm:</label>
          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              type="button"
              onClick={() => setModelType('ZIP')}
              className={`p-2 rounded-lg border text-center transition-colors cursor-pointer ${
                modelType === 'ZIP'
                  ? 'bg-sky-500/20 border-sky-500 text-sky-300 font-semibold'
                  : 'bg-slate-800/40 border-slate-700 text-slate-400 hover:bg-slate-800'
              }`}
            >
              ZIP (Poisson)
            </button>
            <button
              type="button"
              onClick={() => setModelType('ZINB')}
              className={`p-2 rounded-lg border text-center transition-colors cursor-pointer ${
                modelType === 'ZINB'
                  ? 'bg-sky-500/20 border-sky-500 text-sky-300 font-semibold'
                  : 'bg-slate-800/40 border-slate-700 text-slate-400 hover:bg-slate-800'
              }`}
            >
              ZINB (NegBinomial)
            </button>
          </div>
          <p className="text-[11px] text-slate-400">
            {modelType === 'ZIP' ? 'Giả định Var = Mean trong quá trình đếm.' : 'Cho phép quá phân tán Var > Mean (tham số α).'}
          </p>
        </div>

        {/* Scope */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Phạm vi Dữ liệu:</label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Chỉ mẫu sạch đã kiểm định (Verified Clean)</option>
          </select>
          <div className="pt-1">
            <button
              type="button"
              onClick={() => setUseSeparateInflation(prev => !prev)}
              className="flex items-center gap-1.5 text-slate-300 hover:text-white transition-colors cursor-pointer"
            >
              {useSeparateInflation ? (
                <CheckSquare className="w-3.5 h-3.5 text-sky-400" />
              ) : (
                <Square className="w-3.5 h-3.5 text-slate-500" />
              )}
              <span className="text-[11px]">Chỉ định biến đột biến không (Z) riêng biệt</span>
            </button>
          </div>
        </div>

        {/* Tip */}
        <div className="space-y-1.5 bg-slate-800/30 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
          <span>
            Kiểm định phi lồng ghép <strong>Vuong (1989)</strong> so sánh trực tiếp mô hình Zero-Inflated với Poisson tiêu chuẩn: Nếu <span className="text-sky-300 font-mono">z &gt; 1.96 (p &lt; 0.05)</span>, Zero-Inflation vượt trội có ý nghĩa thống kê.
          </span>
        </div>
      </div>

      {/* Count Covariates Selection (X) */}
      <div className="py-4 border-b border-slate-800">
        <label className="font-medium text-xs text-slate-300 flex items-center justify-between mb-2">
          <span>Chọn Các Biến Giải Thích Quá Trình Đếm (Count Covariates X):</span>
          <span className="text-slate-400 font-normal">Đã chọn: {covariateQids.length} biến</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto pr-1">
          {questions
            .filter((q) => q.id !== countQid)
            .map((q) => {
              const isSelected = covariateQids.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleCovariate(q.id)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors cursor-pointer border ${
                    isSelected
                      ? 'bg-sky-500/10 border-sky-500/30 text-sky-300'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  )}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
        </div>
      </div>

      {/* Inflation Covariates Selection (Z) if enabled */}
      {useSeparateInflation && (
        <div className="py-4 border-b border-slate-800">
          <label className="font-medium text-xs text-slate-300 flex items-center justify-between mb-2">
            <span>Chọn Biến Dự Báo Nhóm Luôn Bằng 0 (Zero-Inflation Predictors Z):</span>
            <span className="text-slate-400 font-normal">Đã chọn: {inflationQids.length} biến</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto pr-1">
            {questions
              .filter((q) => q.id !== countQid)
              .map((q) => {
                const isSelected = inflationQids.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleInflationCovariate(q.id)}
                    className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors cursor-pointer border ${
                      isSelected
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                        : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    {isSelected ? (
                      <CheckSquare className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    ) : (
                      <Square className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    )}
                    <span className="truncate">{q.title}</span>
                  </button>
                );
              })}
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="my-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="mt-6 space-y-6">
          {/* Key Metrics Banners */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tỷ Lệ Điểm 0 (Zero Rate)</span>
              <span className="text-lg font-bold text-sky-400">
                {result.diagnostics.zero_percentage.toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {result.diagnostics.zero_observations_count} / {result.diagnostics.sample_size} quan sát
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tỷ Số Phân Tán (Var/Mean)</span>
              <span className={`text-lg font-bold ${result.diagnostics.dispersion_ratio > 1.5 ? 'text-amber-400' : 'text-slate-200'}`}>
                {result.diagnostics.dispersion_ratio.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Mean: {result.diagnostics.sample_mean.toFixed(2)} · Var: {result.diagnostics.sample_variance.toFixed(2)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Kiểm Định Vuong (1989)</span>
              <span className={`text-lg font-bold ${result.diagnostics.vuong_favors_zero_inflation ? 'text-emerald-400' : 'text-slate-300'}`}>
                z = {result.diagnostics.vuong_test_z.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                p = {result.diagnostics.vuong_test_p < 0.001 ? '< 0.001' : result.diagnostics.vuong_test_p.toFixed(3)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Log-Likelihood ({result.diagnostics.model_type})</span>
              <span className="text-base font-bold text-slate-200">
                {result.diagnostics.log_likelihood_zi.toFixed(1)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Poisson LL: {result.diagnostics.log_likelihood_standard_poisson.toFixed(1)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tiêu Chuẩn AIC / BIC</span>
              <span className="text-base font-bold text-indigo-400">
                {result.diagnostics.aic_zi.toFixed(0)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                BIC: {result.diagnostics.bic_zi.toFixed(0)} (chuẩn tối ưu)
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tham Số Quá Phân Tán (α)</span>
              <span className="text-lg font-bold text-emerald-400">
                {result.diagnostics.dispersion_parameter_alpha !== null && result.diagnostics.dispersion_parameter_alpha !== undefined
                  ? result.diagnostics.dispersion_parameter_alpha.toFixed(3)
                  : 'N/A (Poisson)'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {result.diagnostics.dispersion_parameter_alpha ? 'Negative Binomial NB2' : 'Phân phối Poisson'}
              </span>
            </div>
          </div>

          {/* Verdict Banner */}
          <div className={`p-4 rounded-xl border text-xs flex items-center justify-between gap-4 ${
            result.diagnostics.vuong_favors_zero_inflation
              ? 'bg-sky-500/10 border-sky-500/20 text-sky-300'
              : 'bg-slate-800/60 border-slate-700 text-slate-300'
          }`}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-sky-400" />
              <span>
                <strong>Phán quyết Kiểm định Vuong:</strong> {result.diagnostics.vuong_verdict}
              </span>
            </div>
            <span className="text-[11px] font-mono opacity-80 shrink-0">
              ΔAIC = {(result.diagnostics.aic_standard_poisson - result.diagnostics.aic_zi).toFixed(1)}
            </span>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('count_coeffs')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'count_coeffs'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Hệ Số Quá Trình Đếm (Count Model & IRR)
            </button>
            <button
              onClick={() => setActiveTab('infl_coeffs')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'infl_coeffs'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Hệ Số Đột Biến Không (Zero Inflation Logit & OR)
            </button>
            <button
              onClick={() => setActiveTab('frequency')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'frequency'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              So Sánh Tần Suất Thực Tế vs Dự Báo
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'svg'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Biểu Đồ Trực Quan Hóa SVG</span>
            </button>
          </div>

          {/* Tab 1: Count Coefficients */}
          {activeTab === 'count_coeffs' && result.count_model_coefficients && (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Biến Giải Thích (Count X)</th>
                    <th className="py-2.5 px-3 text-right">Hệ Số (β)</th>
                    <th className="py-2.5 px-3 text-right">Tỷ Lệ Tần Suất Biến Cố (IRR)</th>
                    <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-right">z-stat</th>
                    <th className="py-2.5 px-3 text-right">p-value</th>
                    <th className="py-2.5 px-3 text-center">95% CI (IRR)</th>
                    <th className="py-2.5 px-3 text-center">Ý Nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.count_model_coefficients.map((row, idx) => {
                    const qObj = questions.find(q => q.id === row.variable);
                    const label = row.is_intercept ? 'Hằng số chặn (Intercept β₀)' : (qObj ? qObj.title : row.variable);
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-sans text-white font-medium">
                          {label}
                        </td>
                        <td className="py-2.5 px-3 text-right text-sky-400 font-semibold">
                          {row.coefficient.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">
                          {row.incidence_rate_ratio_irr.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-400">
                          {row.standard_error.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-300">
                          {row.z_statistic.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <span className={row.p_value < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                            {row.p_value < 0.001 ? '< 0.001' : row.p_value.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-center text-slate-400">
                          [{row.irr_95_lower.toFixed(3)}, {row.irr_95_upper.toFixed(3)}]
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {row.is_significant ? (
                            <span className="px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 text-[10px]">
                              p &lt; 0.05
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400 text-[10px]">
                              ns
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Inflation Coefficients */}
          {activeTab === 'infl_coeffs' && result.inflation_model_coefficients && (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Biến Dự Báo Điểm 0 (Zero Inflation Z)</th>
                    <th className="py-2.5 px-3 text-right">Hệ Số Logit (γ)</th>
                    <th className="py-2.5 px-3 text-right">Tỷ Số Tỷ Lệ Cược (Odds Ratio OR)</th>
                    <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-right">z-stat</th>
                    <th className="py-2.5 px-3 text-right">p-value</th>
                    <th className="py-2.5 px-3 text-center">95% CI (OR)</th>
                    <th className="py-2.5 px-3 text-center">Ý Nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.inflation_model_coefficients.map((row, idx) => {
                    const qObj = questions.find(q => q.id === row.variable);
                    const label = row.is_intercept ? 'Hằng số chặn (Intercept γ₀)' : (qObj ? qObj.title : row.variable);
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-sans text-white font-medium">
                          {label}
                        </td>
                        <td className="py-2.5 px-3 text-right text-amber-400 font-semibold">
                          {row.logit_coefficient.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-indigo-300 font-bold">
                          {row.odds_ratio.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-400">
                          {row.standard_error.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-300">
                          {row.z_statistic.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <span className={row.p_value < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                            {row.p_value < 0.001 ? '< 0.001' : row.p_value.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-center text-slate-400">
                          [{row.or_95_lower.toFixed(3)}, {row.or_95_upper.toFixed(3)}]
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {row.is_significant ? (
                            <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px]">
                              p &lt; 0.05
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400 text-[10px]">
                              ns
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Frequency Distribution */}
          {activeTab === 'frequency' && result.frequency_distribution && (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Mức Số Đếm (Count Value)</th>
                    <th className="py-2.5 px-3 text-right">Tần Suất Thực Tế (Observed)</th>
                    <th className="py-2.5 px-3 text-right">Tần Suất Dự Báo ({result.diagnostics.model_type})</th>
                    <th className="py-2.5 px-3 text-right">Chênh Lệch (Residual)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.frequency_distribution.counts.map((c, idx) => {
                    const obs = result.frequency_distribution!.observed_frequencies[idx];
                    const pred = result.frequency_distribution!.predicted_frequencies[idx];
                    const diff = obs - pred;
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2 px-3 font-bold text-white">Count = {c}</td>
                        <td className="py-2 px-3 text-right text-sky-400">{obs}</td>
                        <td className="py-2 px-3 text-right text-emerald-400">{pred.toFixed(2)}</td>
                        <td className={`py-2 px-3 text-right ${Math.abs(diff) > 2 ? 'text-amber-400 font-semibold' : 'text-slate-400'}`}>
                          {diff > 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: SVG Visualization */}
          {activeTab === 'svg' && result.svg_visualization && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col items-center justify-center overflow-hidden">
              <div
                className="w-full max-w-4xl flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-800/40 border border-slate-700/60 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                  Báo Cáo Học Thuật Chuẩn APA 7th (Zero-Inflated Count Regression)
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-sky-300 transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-sky-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép đoạn văn'}</span>
                </button>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line bg-slate-900/50 p-3 rounded-lg border border-slate-800/80">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
