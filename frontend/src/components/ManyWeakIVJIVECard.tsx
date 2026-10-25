import React, { useState } from 'react';
import {
  Layers,
  BarChart3,
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  Activity,
  Sliders,
  Sparkles,
  HelpCircle,
  Cpu,
  Zap,
  Flame,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import {
  ManyWeakIVJIVERequest,
  ManyWeakIVJIVEResult
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const ManyWeakIVJIVECard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentId, setTreatmentId] = useState<string>('');
  const [outcomeId, setOutcomeId] = useState<string>('');
  const [instrumentIds, setInstrumentIds] = useState<string[]>([]);
  const [covariateIds, setCovariateIds] = useState<string[]>([]);
  const [fullerA, setFullerA] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ManyWeakIVJIVEResult | null>(null);
  const [activeTab, setActiveTab] = useState<'forest' | 'table' | 'diagnostics' | 'apa'>('forest');
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'single_choice'
  );

  const handleToggleInstrument = (qid: string) => {
    if (instrumentIds.includes(qid)) {
      setInstrumentIds(instrumentIds.filter((id) => id !== qid));
    } else {
      setInstrumentIds([...instrumentIds, qid]);
    }
  };

  const handleToggleCovariate = (qid: string) => {
    if (covariateIds.includes(qid)) {
      setCovariateIds(covariateIds.filter((id) => id !== qid));
    } else {
      setCovariateIds([...covariateIds, qid]);
    }
  };

  const handleRun = async () => {
    if (!treatmentId) {
      setError('Vui lòng chọn biến Nội sinh Can thiệp (Endogenous Treatment D).');
      return;
    }
    if (!outcomeId) {
      setError('Vui lòng chọn biến Kết quả Causal (Outcome Y).');
      return;
    }
    if (treatmentId === outcomeId) {
      setError('Biến can thiệp và biến kết quả không được trùng nhau.');
      return;
    }
    if (instrumentIds.length === 0) {
      setError('Vui lòng chọn ít nhất một Biến Công cụ Ngoại sinh (Instrument Z).');
      return;
    }
    if (instrumentIds.includes(treatmentId) || instrumentIds.includes(outcomeId)) {
      setError('Biến công cụ không được trùng với biến can thiệp hoặc kết quả.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: ManyWeakIVJIVERequest = {
      treatment_question_id: treatmentId,
      outcome_question_id: outcomeId,
      instrument_question_ids: instrumentIds,
      covariate_question_ids: covariateIds.length > 0 ? covariateIds : undefined,
      fuller_a: fullerA,
      scope,
    };

    try {
      const data = await api.runManyWeakIVJIVE(surveyId, payload);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi thực thi phân tích Many-Weak-IV JIVE.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden mb-8">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 dark:border-slate-800 bg-gradient-to-r from-emerald-50/50 via-teal-50/30 to-transparent dark:from-emerald-950/20 dark:via-teal-950/10 dark:to-transparent">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-600 text-white shadow-md shadow-emerald-500/20">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Many-Weak-IV Robust JIVE, LIML & Fuller (1977) Engine
                </h3>
                <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  DataTrust Iteration 191
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Khắc phục chệch mẫu hữu hạn (Finite-Sample Leverage Bias) của 2SLS khi có nhiều biến công cụ yếu bằng Jackknife IV (Angrist et al. 1999; Chao et al. 2012) & Fuller (1977) Modified LIML
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Configuration Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 p-5 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
          {/* Treatment D */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Biến Nội Sinh Can Thiệp (D) *
            </label>
            <select
              value={treatmentId}
              onChange={(e) => setTreatmentId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Chọn biến nội sinh D --</option>
              {numericQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Outcome Y */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Biến Kết Quả (Outcome Y) *
            </label>
            <select
              value={outcomeId}
              onChange={(e) => setOutcomeId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Chọn biến kết quả Y --</option>
              {numericQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Fuller Constant a */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Hệ số Fuller (a) (Fuller 1977)
            </label>
            <select
              value={fullerA}
              onChange={(e) => setFullerA(parseFloat(e.target.value))}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500"
            >
              <option value="1.0">a = 1.0 (Optimal MSE, Fuller 1977 Khuyên dùng)</option>
              <option value="2.0">a = 2.0 (Khử chệch bậc hai - Higher Order Unbiasedness)</option>
              <option value="4.0">a = 4.0 (Bảo toàn phương sai tối thiểu)</option>
            </select>
          </div>

          {/* Instruments (Z) */}
          <div className="md:col-span-2 lg:col-span-3">
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Tập Hợp Biến Công Cụ Ngoại Sinh (Instruments Z_1, ..., Z_K) * (Chọn 1 hoặc nhiều)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {numericQuestions
                .filter((q) => q.id !== treatmentId && q.id !== outcomeId)
                .map((q) => {
                  const isChecked = instrumentIds.includes(q.id);
                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => handleToggleInstrument(q.id)}
                      className={`text-left px-3 py-2 rounded-lg text-xs font-medium border transition-colors flex items-center justify-between ${
                        isChecked
                          ? 'bg-emerald-50 border-emerald-500 text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-600 dark:text-emerald-300'
                          : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span className="truncate pr-2">{q.title}</span>
                      {isChecked && <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />}
                    </button>
                  );
                })}
            </div>
            {instrumentIds.length === 0 && (
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                Vui lòng chọn ít nhất 1 biến công cụ để ước lượng mô hình causal IV.
              </p>
            )}
          </div>

          {/* Covariates (W) */}
          <div className="md:col-span-2 lg:col-span-3">
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Biến Kiểm Soát Cơ Sở (Covariates W) (Tùy chọn)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {numericQuestions
                .filter((q) => q.id !== treatmentId && q.id !== outcomeId && !instrumentIds.includes(q.id))
                .map((q) => {
                  const isChecked = covariateIds.includes(q.id);
                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => handleToggleCovariate(q.id)}
                      className={`text-left px-3 py-2 rounded-lg text-xs font-medium border transition-colors flex items-center justify-between ${
                        isChecked
                          ? 'bg-teal-50 border-teal-500 text-teal-800 dark:bg-teal-950/40 dark:border-teal-600 dark:text-teal-300'
                          : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span className="truncate pr-2">{q.title}</span>
                      {isChecked && <Check className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />}
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Scope and Action */}
          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Phạm vi mẫu:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2.5 py-1.5 text-slate-800 dark:text-slate-200"
            >
              <option value="all">Tất cả phản hồi hợp lệ</option>
              <option value="verified_clean">Chỉ phản hồi Verified Clean</option>
            </select>
          </div>

          <div className="md:col-span-2 flex justify-end items-center gap-3">
            <button
              onClick={handleRun}
              disabled={loading || !treatmentId || !outcomeId || instrumentIds.length === 0}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold text-sm shadow-md shadow-emerald-500/20 flex items-center gap-2 transition-all"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Đang ước lượng JIVE & LIML...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Chạy Ước Lượng Many-Weak-IV</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-400 flex items-center gap-3 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results View */}
        {result && (
          <div className="space-y-6">
            {/* KPI Stat Ribbon */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Mẫu Phân Tích</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  N = {result.sample_size}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  K = {result.instruments_count} IVs, L = {result.covariates_count} controls
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">First-Stage F-Stat</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  F = {result.first_stage_diagnostics.f_statistic.toFixed(2)}
                </div>
                <div className="text-[11px] mt-0.5">
                  {result.first_stage_diagnostics.weak_instrument ? (
                    <span className="text-amber-600 dark:text-amber-400 font-medium">Yếu (&lt; {result.first_stage_diagnostics.stock_yogo_10pct_critical_value})</span>
                  ) : (
                    <span className="text-emerald-600 dark:text-emerald-400 font-medium">Mạnh (Stock-Yogo OK)</span>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Mean Leverage (h_ii)</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {result.first_stage_diagnostics.mean_leverage.toFixed(3)}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Max = {result.first_stage_diagnostics.max_leverage.toFixed(3)}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Sargan Hansen J-Test</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {result.overidentification_test.sargan_statistic !== null && result.overidentification_test.sargan_statistic !== undefined
                    ? `J = ${result.overidentification_test.sargan_statistic.toFixed(2)}`
                    : 'N/A (K=1)'}
                </div>
                <div className="text-[11px] mt-0.5">
                  {result.overidentification_test.p_value !== null && result.overidentification_test.p_value !== undefined ? (
                    result.overidentification_test.exogeneity_rejected ? (
                      <span className="text-red-600 dark:text-red-400 font-medium">Bác bỏ ngoại sinh (p &lt; 0.05)</span>
                    ) : (
                      <span className="text-emerald-600 dark:text-emerald-400 font-medium">Hợp lệ (p = {result.overidentification_test.p_value.toFixed(3)})</span>
                    )
                  ) : (
                    <span className="text-slate-500">Chính xác định danh</span>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 col-span-2 sm:col-span-4 lg:col-span-1">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">JIVE vs 2SLS Bias</span>
                <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  Khử Triệt Để Leverage
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Leave-one-out orthogonal
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-700 space-x-4">
              <button
                onClick={() => setActiveTab('forest')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'forest'
                    ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span>Biểu Đồ So Sánh & Leverage (Dual-Panel)</span>
              </button>
              <button
                onClick={() => setActiveTab('table')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'table'
                    ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Bảng So Sánh 5 Ước Lượng</span>
              </button>
              <button
                onClick={() => setActiveTab('diagnostics')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'diagnostics'
                    ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Chẩn Đoán Biến Công Cụ & Ngoại Sinh</span>
              </button>
              <button
                onClick={() => setActiveTab('apa')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'apa'
                    ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Báo Cáo Học Thuật APA 7th</span>
              </button>
            </div>

            {/* Tab 1: Vector Visualizer */}
            {activeTab === 'forest' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 overflow-x-auto shadow-inner">
                  <div
                    className="w-full flex justify-center"
                    dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                  />
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic">
                  * Panel A minh họa khoảng tin cậy 95% của OLS, 2SLS, JIVE, LIML và Fuller (1977). Khi F &lt; 10, 2SLS bị kéo mạnh về OLS do chệch đòn bẩy mẫu hữu hạn h_ii; JIVE và Fuller loại bỏ hoàn toàn tương quan nội sinh này.
                </div>
              </div>
            )}

            {/* Tab 2: Comparison Table */}
            {activeTab === 'table' && (
              <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 uppercase font-bold border-b border-slate-200 dark:border-slate-700">
                      <tr>
                        <th className="py-3 px-4">Phương Pháp Ước Lượng</th>
                        <th className="py-3 px-3 text-right">Hệ Số (\beta)</th>
                        <th className="py-3 px-3 text-right">Sai Số Chuẩn (SE)</th>
                        <th className="py-3 px-3 text-right">Khoảng Tin Cậy 95%</th>
                        <th className="py-3 px-3 text-right">Z-Stat</th>
                        <th className="py-3 px-3 text-right">P-Value</th>
                        <th className="py-3 px-4">Đặc Tính Kinh Tế Lượng</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {result.estimator_comparisons.map((row, idx) => (
                        <tr
                          key={idx}
                          className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                            row.estimator.includes('JIVE')
                              ? 'bg-emerald-50/40 dark:bg-emerald-950/20 font-semibold text-emerald-900 dark:text-emerald-200'
                              : row.estimator.includes('Fuller')
                              ? 'bg-amber-50/30 dark:bg-amber-950/20'
                              : ''
                          }`}
                        >
                          <td className="py-3 px-4 flex items-center gap-2">
                            {row.estimator.includes('JIVE') && (
                              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                            )}
                            {row.estimator}
                          </td>
                          <td className="py-3 px-3 text-right font-mono text-sm">
                            {row.estimate.toFixed(4)}
                          </td>
                          <td className="py-3 px-3 text-right font-mono text-slate-500">
                            {row.std_error.toFixed(4)}
                          </td>
                          <td className="py-3 px-3 text-right font-mono text-slate-600 dark:text-slate-400">
                            [{row.ci_95[0].toFixed(3)}, {row.ci_95[1].toFixed(3)}]
                          </td>
                          <td className="py-3 px-3 text-right font-mono text-slate-600 dark:text-slate-400">
                            {row.z_statistic.toFixed(2)}
                          </td>
                          <td className="py-3 px-3 text-right font-mono">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[11px] ${
                                row.p_value < 0.05
                                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                                  : 'text-slate-500'
                              }`}
                            >
                              {row.p_value.toFixed(4)}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-500 dark:text-slate-400 text-[11px]">
                            {row.notes}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 3: Diagnostics */}
            {activeTab === 'diagnostics' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-white">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <h4>Kiểm Định Nhận Diện Giai Đoạn 1 (First-Stage Identification)</h4>
                  </div>
                  <ul className="text-xs space-y-2 text-slate-600 dark:text-slate-300">
                    <li className="flex justify-between border-b border-slate-100 dark:border-slate-700 pb-1.5">
                      <span>Cragg-Donald Wald F-Statistic:</span>
                      <span className="font-mono font-bold">{result.first_stage_diagnostics.f_statistic.toFixed(2)}</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-100 dark:border-slate-700 pb-1.5">
                      <span>Ngưỡng Stock & Yogo (10% Maximal Bias):</span>
                      <span className="font-mono">{result.first_stage_diagnostics.stock_yogo_10pct_critical_value.toFixed(2)}</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-100 dark:border-slate-700 pb-1.5">
                      <span>Đánh Giá Cường Độ Biến Công Cụ:</span>
                      <span className={`font-semibold ${result.first_stage_diagnostics.weak_instrument ? 'text-amber-600' : 'text-emerald-600'}`}>
                        {result.first_stage_diagnostics.weak_instrument ? 'Biến công cụ yếu (Weak IV)' : 'Nhận diện mạnh (Strong IV)'}
                      </span>
                    </li>
                    <li className="flex justify-between pt-1">
                      <span>Mức Độ Đòn Bẩy Trung Bình (Mean h_ii):</span>
                      <span className="font-mono">{result.first_stage_diagnostics.mean_leverage.toFixed(4)}</span>
                    </li>
                  </ul>
                </div>

                <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-white">
                    <Activity className="w-4 h-4 text-teal-600" />
                    <h4>Kiểm Định Ngoại Sinh Quá Nhận Diện (Sargan-Hansen J-Test)</h4>
                  </div>
                  <ul className="text-xs space-y-2 text-slate-600 dark:text-slate-300">
                    <li className="flex justify-between border-b border-slate-100 dark:border-slate-700 pb-1.5">
                      <span>Thống Kê Sargan J:</span>
                      <span className="font-mono font-bold">
                        {result.overidentification_test.sargan_statistic !== null && result.overidentification_test.sargan_statistic !== undefined
                          ? result.overidentification_test.sargan_statistic.toFixed(3)
                          : 'N/A'}
                      </span>
                    </li>
                    <li className="flex justify-between border-b border-slate-100 dark:border-slate-700 pb-1.5">
                      <span>Bậc Tự Do (Degrees of Freedom df = K - 1):</span>
                      <span className="font-mono">{result.overidentification_test.df ?? '0'}</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-100 dark:border-slate-700 pb-1.5">
                      <span>P-Value:</span>
                      <span className="font-mono">
                        {result.overidentification_test.p_value !== null && result.overidentification_test.p_value !== undefined
                          ? result.overidentification_test.p_value.toFixed(4)
                          : 'N/A'}
                      </span>
                    </li>
                    <li className="flex justify-between pt-1">
                      <span>Kết Luận Giả Thuyết Ngoại Sinh:</span>
                      <span className={`font-semibold ${result.overidentification_test.exogeneity_rejected ? 'text-red-600' : 'text-emerald-600'}`}>
                        {result.overidentification_test.exogeneity_rejected ? 'Bác bỏ giả thuyết ngoại sinh' : 'Không có bằng chứng vi phạm ngoại sinh'}
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            )}

            {/* Tab 4: APA Narrative */}
            {activeTab === 'apa' && (
              <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 relative">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Báo Cáo Học Thuật Chuẩn APA 7th Edition
                  </h4>
                  <button
                    onClick={handleCopyAPA}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 transition-colors flex items-center gap-1.5 text-xs font-medium"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="text-emerald-600 font-semibold">Đã copy</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy APA</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-serif">
                  {result.apa_narrative}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
