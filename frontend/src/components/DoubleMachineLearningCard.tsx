import React, { useState } from 'react';
import { DoubleMachineLearningResult } from '../types/survey';
import { api } from '../api/client';

interface DoubleMachineLearningCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const DoubleMachineLearningCard: React.FC<DoubleMachineLearningCardProps> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [selectedCovQids, setSelectedCovQids] = useState<string[]>([]);
  const [nFolds, setNFolds] = useState<number>(5);
  const [alphaPenalty, setAlphaPenalty] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DoubleMachineLearningResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Numeric / Continuous questions for Outcome and Covariates
  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider'
  );

  // Treatment questions (Single choice, dropdown, binary, linear scale)
  const treatmentQuestions = questions.filter(
    (q) =>
      q.question_type === 'single_choice' ||
      q.question_type === 'dropdown' ||
      q.question_type === 'number' ||
      q.question_type === 'linear_scale'
  );

  // Potential covariates (exclude selected outcome and treatment)
  const availableCovariates = numericQuestions.filter(
    (q) => q.id !== outcomeQid && q.id !== treatmentQid
  );

  const toggleCovariate = (id: string) => {
    setSelectedCovQids((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAllCovariates = () => {
    setSelectedCovQids(availableCovariates.map((q) => q.id));
  };

  const clearAllCovariates = () => {
    setSelectedCovQids([]);
  };

  const handleRun = async () => {
    if (!outcomeQid || !treatmentQid) {
      setError('Vui lòng chọn cả Biến kết quả (Outcome) và Biến can thiệp (Treatment).');
      return;
    }
    if (outcomeQid === treatmentQid) {
      setError('Biến kết quả và Biến can thiệp không được trùng nhau.');
      return;
    }
    if (selectedCovQids.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến kiểm soát để khử thiên lệch bằng DML.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runDoubleMachineLearning(surveyId, {
        outcome_question_id: outcomeQid,
        treatment_question_id: treatmentQid,
        covariate_question_ids: selectedCovQids,
        n_folds: nFolds,
        alpha_penalty: alphaPenalty,
        scope
      });

      if (res.status === 'error' || res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'COLLINEARITY_ERROR') {
        setError(res.message || 'Ước lượng Double Machine Learning thất bại.');
      } else {
        setResult(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi kết nối máy chủ khi tính toán DML.');
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
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-700/60 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
              Chernozhukov et al. 2018 &bull; Robinson 1988
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Neyman Orthogonal Scores &bull; K-Fold Cross-Fitting
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            Double / Debiased Machine Learning (DML: Khử Thiên Lệch Nhân Quả)
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Ước lượng tác động can thiệp nhân quả có kiểm soát phi tham số không gian biến nhiễu chiều cao mà không bị thiên lệch chính quy hóa.
          </p>
        </div>
      </div>

      {/* Selectors Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Outcome Selector */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Biến Kết quả (Outcome Y) *
          </label>
          <select
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn câu hỏi đo lường Y --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Treatment Selector */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Biến Can thiệp (Treatment D) *
          </label>
          <select
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến can thiệp D --</option>
            {treatmentQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Cross-fitting folds */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Số Folds Phân mẫu Cross-Fitting (K)
          </label>
          <select
            value={nFolds}
            onChange={(e) => setNFolds(parseInt(e.target.value, 10))}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value={3}>3-Fold Cross-Fitting (Mẫu nhỏ)</option>
            <option value={5}>5-Fold Cross-Fitting (Tiêu chuẩn)</option>
            <option value={10}>10-Fold Cross-Fitting (Mẫu lớn)</option>
          </select>
        </div>

        {/* Scope Filter */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Phạm vi Lọc Dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">Toàn bộ mẫu khảo sát (All)</option>
            <option value="verified_clean">Chỉ mẫu sạch đã kiểm định (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Covariates Multi-select Section */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
            Tập biến kiểm soát gây nhiễu (High-Dimensional Covariates X) *
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAllCovariates}
              className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline font-medium"
            >
              Chọn tất cả ({availableCovariates.length})
            </button>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <button
              type="button"
              onClick={clearAllCovariates}
              className="text-xs text-slate-500 hover:underline font-medium"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-40 overflow-y-auto p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40">
          {availableCovariates.map((q) => {
            const isChecked = selectedCovQids.includes(q.id);
            return (
              <label
                key={q.id}
                className={`flex items-start gap-2.5 p-2 rounded cursor-pointer transition text-xs ${
                  isChecked
                    ? 'bg-emerald-50/80 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200 font-medium'
                    : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleCovariate(q.id)}
                  className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span className="line-clamp-2">{q.title}</span>
              </label>
            );
          })}
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleRun}
          disabled={loading || !outcomeQid || !treatmentQid || selectedCovQids.length === 0}
          className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-medium text-sm transition shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang ước lượng Double ML...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Ước lượng Tác động Nhân quả (Double ML &theta;&#770;)
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="space-y-6 pt-4 border-t border-slate-100 dark:border-slate-700/60">
          {/* Key Metric Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200/80 dark:border-emerald-800/60">
              <span className="text-xs text-emerald-700 dark:text-emerald-400 font-medium">Hiệu ứng Nhân quả &theta;&#770;</span>
              <p className="text-lg font-bold text-emerald-800 dark:text-emerald-200 mt-0.5">
                {result.diagnostics.theta_dml >= 0 ? `+${result.diagnostics.theta_dml.toFixed(3)}` : result.diagnostics.theta_dml.toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">95% CI Tiệm cận</span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                [{result.diagnostics.ci_lower_95.toFixed(2)}, {result.diagnostics.ci_upper_95.toFixed(2)}]
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Hồi quy OLS Ngây thơ</span>
              <p className="text-base font-bold text-amber-600 dark:text-amber-400 mt-0.5">
                {result.diagnostics.theta_naive_ols >= 0 ? `+${result.diagnostics.theta_naive_ols.toFixed(3)}` : result.diagnostics.theta_naive_ols.toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Thiên lệch Triệt tiêu</span>
              <p className="text-base font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
                &Delta; = {Math.abs(result.diagnostics.confounding_bias).toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Thống kê z (p-value)</span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                {result.diagnostics.z_statistic.toFixed(2)} (p={result.diagnostics.p_value.toFixed(3)})
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Ý nghĩa Thống kê</span>
              <p className={`text-base font-bold mt-0.5 ${result.diagnostics.is_statistically_significant ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500'}`}>
                {result.diagnostics.is_statistically_significant ? 'p < 0.05 (Ý nghĩa)' : 'Không ý nghĩa'}
              </p>
            </div>
          </div>

          {/* Confounding Covariates Ranking Table */}
          {result.confounding_covariates && (
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-800/80 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-4 py-3">Biến Kiểm soát (Covariate)</th>
                    <th className="px-4 py-3">Tương quan với Kết quả Corr(X, Y)</th>
                    <th className="px-4 py-3">Tương quan với Can thiệp Corr(X, D)</th>
                    <th className="px-4 py-3">Mức độ Gây nhiễu (Confounding Score)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {result.confounding_covariates.map((cv, idx) => (
                    <tr key={idx} className={idx === 0 ? 'bg-indigo-50/50 dark:bg-indigo-950/20 font-medium' : ''}>
                      <td className="px-4 py-2.5 font-medium">{cv.covariate}</td>
                      <td className="px-4 py-2.5 font-mono">{cv.corr_outcome >= 0 ? `+${cv.corr_outcome.toFixed(3)}` : cv.corr_outcome.toFixed(3)}</td>
                      <td className="px-4 py-2.5 font-mono">{cv.corr_treatment >= 0 ? `+${cv.corr_treatment.toFixed(3)}` : cv.corr_treatment.toFixed(3)}</td>
                      <td className="px-4 py-2.5 font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                        {cv.confounding_score.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* SVG Visualizations */}
          {result.svg_visualization && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Đồ thị Khoa học: Thặng dư Trực giao Robinson &amp; So sánh Khử Thiên lệch Forest Plot
              </h4>
              <div
                className="w-full overflow-x-auto rounded-lg bg-slate-900 p-2 shadow-inner flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                  Bản tường trình Học thuật chuẩn APA 7th (Double / Debiased Machine Learning)
                </span>
                <button
                  onClick={copyNarrative}
                  className="px-2.5 py-1 text-xs font-medium rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 transition"
                >
                  {copied ? 'Đã sao chép!' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-400 font-serif italic">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
