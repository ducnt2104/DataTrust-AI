import React, { useState } from 'react';
import { api } from '../api/client';
import { TMLEAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface TMLECardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const TMLECard: React.FC<TMLECardProps> = ({
  surveyId,
  questions
}) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariateQIds, setSelectedCovariateQIds] = useState<string[]>([]);
  const [gbound, setGbound] = useState<number>(0.025);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TMLEAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const binaryOrChoiceQuestions = questions.filter(q =>
    ['single_choice', 'boolean', 'yes_no', 'number'].includes(q.question_type)
  );

  const toggleCovariate = (qid: string) => {
    if (selectedCovariateQIds.includes(qid)) {
      setSelectedCovariateQIds(selectedCovariateQIds.filter(id => id !== qid));
    } else {
      setSelectedCovariateQIds([...selectedCovariateQIds, qid]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId) {
      setError('Vui lòng chọn câu hỏi biến can thiệp (Treatment Variable A).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả (Outcome Variable Y).');
      return;
    }
    if (treatmentQId === outcomeQId) {
      setError('Biến can thiệp và biến kết quả không được trùng nhau.');
      return;
    }
    if (selectedCovariateQIds.includes(treatmentQId) || selectedCovariateQIds.includes(outcomeQId)) {
      setError('Biến kiểm soát gây nhiễu (Covariates) không được trùng với biến can thiệp hoặc biến kết quả.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runTMLEAnalysis(surveyId, {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: selectedCovariateQIds,
        gbound,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình nhân quả mục tiêu TMLE.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích TMLE.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
              Semiparametric Doubly Robust Estimator
            </span>
            <span className="text-xs text-slate-400 font-mono">
              van der Laan &amp; Rose (2011) • Gruber (2012) • Schuler &amp; Rose (2017)
            </span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Targeted Maximum Likelihood Estimation (TMLE)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Ước lượng tác động nhân quả mục tiêu (ATE) kết hợp mô hình điểm xu hướng g(W) và mô hình kỳ vọng Q(A,W). Đạt cận dưới hiệu quả bán tham số Cramér-Rao và bảo toàn tính không chệch ngay cả khi một trong hai mô hình thành phần bị xác định sai (Double Robustness).
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến can thiệp (Treatment A) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
          >
            <option value="">-- Chọn biến can thiệp nhị phân --</option>
            {binaryOrChoiceQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến kết quả (Outcome Y) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
          >
            <option value="">-- Chọn biến đo lường kết quả --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Cắt xén biên Propensity (gbound)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={gbound}
            onChange={(e) => setGbound(parseFloat(e.target.value))}
          >
            <option value={0.01}>0.01 (Mở rộng biên)</option>
            <option value={0.025}>0.025 (Chuẩn van der Laan)</option>
            <option value={0.05}>0.05 (Chống ngoại lai nặng)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Phạm vi dữ liệu (Scope)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
          >
            <option value="all">Toàn bộ phản hồi (All)</option>
            <option value="verified_clean">Chỉ phản hồi sạch đã kiểm định (Clean)</option>
          </select>
        </div>
      </div>

      {/* Covariates Multi-Select */}
      <div className="mt-4">
        <label className="block text-xs font-medium text-slate-300 mb-1">
          Chọn các biến kiểm soát gây nhiễu (Pre-treatment Confounders W)
        </label>
        <div className="max-h-36 overflow-y-auto bg-slate-950 border border-slate-700 rounded-lg p-2.5 space-y-1.5">
          {numericQuestions.map(q => {
            if (q.id === treatmentQId || q.id === outcomeQId) return null;
            const isChecked = selectedCovariateQIds.includes(q.id);
            return (
              <label key={q.id} className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleCovariate(q.id)}
                  className="rounded border-slate-700 text-emerald-500 focus:ring-emerald-500 bg-slate-900"
                />
                <span>{q.title}</span>
              </label>
            );
          })}
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Các biến đặc trưng tiền can thiệp được đưa đồng thời vào mô hình xác suất can thiệp g(W) và mô hình kỳ vọng kết quả Q(A,W).
        </p>
      </div>

      {/* Action Button */}
      <div className="mt-5 flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang tối ưu hàm ảnh hưởng EIC và tham số ε...</span>
            </>
          ) : (
            <>
              <span>Ước lượng Tác động Nhân quả TMLE</span>
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Tác động Nhân quả TMLE (ATE)</span>
              <span className="text-xl font-bold text-emerald-400 font-mono">
                {result.targeted_parameters?.targeted_tmle_ate?.toFixed(3)}
              </span>
              <span className="text-[11px] text-slate-500 block">
                SE: {result.targeted_parameters?.se_tmle?.toFixed(3)}
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Khoảng Tin cậy 95% Wald CI</span>
              <span className="text-sm font-bold text-sky-400 font-mono mt-1 block">
                [{result.targeted_parameters?.ci_95_lower?.toFixed(3)}, {result.targeted_parameters?.ci_95_upper?.toFixed(3)}]
              </span>
              <span className="text-[11px] text-slate-500 block">
                p = {result.targeted_parameters?.p_value?.toFixed(4)}
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Tham số Dao động Mục tiêu (ε)</span>
              <span className="text-xl font-bold text-purple-400 font-mono">
                {result.targeted_parameters?.fluctuation_epsilon?.toFixed(5)}
              </span>
              <span className="text-[11px] text-slate-500 block">Clever Covariate MLE</span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Tỷ lệ Can thiệp / Đối chứng</span>
              <span className="text-xl font-bold text-white font-mono">
                {result.sample_diagnostics?.n_treated} / {result.sample_diagnostics?.n_control}
              </span>
              <span className="text-[11px] text-slate-500 block">
                Tổng N: {result.sample_diagnostics?.n_total} ({( (result.sample_diagnostics?.treated_ratio || 0) * 100 ).toFixed(1)}%)
              </span>
            </div>
          </div>

          {/* Positivity / Overlap Callout */}
          <div className={`p-4 rounded-lg border ${
            result.sample_diagnostics?.positivity_violation_risk
              ? 'bg-amber-950/20 border-amber-500/30'
              : 'bg-emerald-950/20 border-emerald-500/30'
          }`}>
            <div className="flex items-start gap-3">
              <div className={`p-1.5 rounded-md mt-0.5 ${
                result.sample_diagnostics?.positivity_violation_risk
                  ? 'bg-amber-500/10 text-amber-400'
                  : 'bg-emerald-500/10 text-emerald-400'
              }`}>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div className="text-sm">
                <h4 className={`font-semibold ${
                  result.sample_diagnostics?.positivity_violation_risk ? 'text-amber-300' : 'text-emerald-300'
                }`}>
                  Chẩn đoán Vùng Hỗ trợ Chung (Common Support &amp; Positivity Assumption)
                </h4>
                <p className="text-slate-300 mt-1 leading-relaxed">
                  Phổ điểm xu hướng dao động từ <code className="text-emerald-400 font-mono">g(W) = {result.sample_diagnostics?.min_propensity_score?.toFixed(3)}</code> đến <code className="text-emerald-400 font-mono">{result.sample_diagnostics?.max_propensity_score?.toFixed(3)}</code>.
                  {result.sample_diagnostics?.positivity_violation_risk
                    ? ' Cảnh báo: Điểm xu hướng tiệm cận biên cực đoan. Cơ chế cắt xén biên đã được kích hoạt để kiểm soát phương sai của Clever Covariate.'
                    : ' Vùng hỗ trợ chung hoàn toàn đạt chuẩn nhận dạng nhân quả không thiên lệch.'}
                </p>
              </div>
            </div>
          </div>

          {/* Estimator Comparison Table */}
          {result.estimator_comparisons && result.estimator_comparisons.length > 0 && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2">
                Bảng Đối chiếu Đa Ước lượng Tác động Nhân quả (Estimator Comparison Matrix)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900 text-slate-400 font-medium">
                    <tr>
                      <th className="p-2.5">Phương pháp Ước lượng</th>
                      <th className="p-2.5">Hiệu ứng ATE</th>
                      <th className="p-2.5">Khoảng Tin cậy 95% CI</th>
                      <th className="p-2.5">Đánh giá Rủi ro Thiên lệch (Bias &amp; Variance)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono">
                    {result.estimator_comparisons.map((row, idx) => (
                      <tr key={idx} className={row.name.includes('TMLE') ? 'bg-emerald-950/20 text-white font-semibold' : 'hover:bg-slate-900/40'}>
                        <td className="p-2.5 font-sans font-medium text-slate-200">{row.name}</td>
                        <td className={`p-2.5 font-bold ${row.name.includes('TMLE') ? 'text-emerald-400' : 'text-slate-200'}`}>
                          {row.ate.toFixed(3)}
                        </td>
                        <td className="p-2.5 text-sky-400">[{row.ci_lower.toFixed(3)}, {row.ci_upper.toFixed(3)}]</td>
                        <td className="p-2.5 font-sans text-xs text-slate-400">{row.bias_risk}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SVG Visualizations */}
          {result.svg_chart && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-hidden">
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-slate-200">
                  Báo cáo Phân tích Nhân quả Chuẩn APA 7th &amp; Khuyến nghị Can thiệp
                </h4>
                <button
                  onClick={copyToClipboard}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded transition flex items-center gap-1.5 cursor-pointer"
                >
                  {copiedNarrative ? (
                    <>
                      <span className="text-emerald-400 font-medium">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <span>Sao chép Báo cáo</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-slate-300 space-y-2 whitespace-pre-line leading-relaxed font-sans bg-slate-900/50 p-4 rounded-lg border border-slate-800/60">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
