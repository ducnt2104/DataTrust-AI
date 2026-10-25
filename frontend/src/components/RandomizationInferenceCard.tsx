import React, { useState } from 'react';
import { api } from '../api/client';
import { RandomizationInferenceResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface RandomizationInferenceCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const RandomizationInferenceCard: React.FC<RandomizationInferenceCardProps> = ({
  surveyId,
  questions
}) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [numPermutations, setNumPermutations] = useState<number>(2000);
  const [alternative, setAlternative] = useState<'two-sided' | 'greater' | 'less'>('two-sided');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RandomizationInferenceResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const treatmentQuestions = questions.filter(q =>
    ['single_choice', 'boolean', 'yes_no', 'number', 'rating'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả liên tục (Continuous Outcome Y).');
      return;
    }
    if (!treatmentQId) {
      setError('Vui lòng chọn biến phân bổ can thiệp (Binary Treatment D).');
      return;
    }
    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả và biến can thiệp không được trùng nhau.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runRandomizationInference(surveyId, {
        outcome_question_id: outcomeQId,
        treatment_question_id: treatmentQId,
        num_permutations: numPermutations,
        alternative,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể tính toán phân phối hoán vị ngẫu nhiên.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi thực hiện Randomization Inference.');
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
              Nonparametric & Exact Causal
            </span>
            <span className="text-xs text-slate-400 font-mono">Fisher (1935) • Rosenbaum (2002)</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Exact Permutation & Randomization Inference (Fisher's Sharp Null)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Kiểm định hoán vị chính xác (Exact Permutation Test), phân phối hoán vị mẫu hữu hạn, hiệu trung bình/trung vị và độ dịch chuyển vị trí Hodges-Lehmann với khoảng tin cậy chính xác 95%.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến kết quả phụ thuộc (Outcome Y) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
          >
            <option value="">-- Chọn biến định lượng --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến can thiệp (Binary Treatment D) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
          >
            <option value="">-- Chọn biến can thiệp nhị phân --</option>
            {treatmentQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Số lượng hoán vị Monte Carlo (B)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={numPermutations}
            onChange={(e) => setNumPermutations(Number(e.target.value))}
          >
            <option value="1000">1,000 lần hoán vị</option>
            <option value="2000">2,000 lần hoán vị (Khuyến nghị)</option>
            <option value="5000">5,000 lần hoán vị</option>
            <option value="10000">10,000 lần hoán vị (Độ chính xác cao)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Giả thuyết đối ngẫu (Alternative)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={alternative}
            onChange={(e) => setAlternative(e.target.value as any)}
          >
            <option value="two-sided">Hai phía (Two-sided: H1 ≠ 0)</option>
            <option value="greater">Phía trên (Greater: H1 &gt; 0)</option>
            <option value="less">Phía dưới (Less: H1 &lt; 0)</option>
          </select>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-4">
          <label className="text-xs text-slate-400 flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="ri_scope"
              checked={scope === 'all'}
              onChange={() => setScope('all')}
              className="text-emerald-500 focus:ring-emerald-500 bg-slate-950 border-slate-700"
            />
            Toàn bộ phản hồi ({questions.length} câu)
          </label>
          <label className="text-xs text-slate-400 flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="ri_scope"
              checked={scope === 'verified_clean'}
              onChange={() => setScope('verified_clean')}
              className="text-emerald-500 focus:ring-emerald-500 bg-slate-950 border-slate-700"
            />
            Chỉ phản hồi đã làm sạch (Cleaned data)
          </label>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg shadow transition flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang hoán vị dữ liệu...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Kiểm định Hoán vị Chính xác
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg flex items-center gap-2">
          <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="mt-8 space-y-6">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Mẫu can thiệp / Đối chứng</div>
              <div className="text-lg font-bold text-white mt-1">
                {result.treated_count} / {result.control_count}
              </div>
              <div className="text-xs text-slate-500">Tổng N = {result.sample_size}</div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Exact Diff-in-Means (P-value)</div>
              <div className="text-lg font-bold text-emerald-400 mt-1">
                {result.difference_in_means?.observed_statistic?.toFixed(3)}
              </div>
              <div className="text-xs font-mono text-slate-400">
                p_exact = {result.difference_in_means?.exact_p_value?.toFixed(4)}
                {result.difference_in_means?.is_significant && (
                  <span className="text-emerald-400 font-bold ml-1">*</span>
                )}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Exact Wilcoxon Rank Sum</div>
              <div className="text-lg font-bold text-teal-400 mt-1">
                W = {result.wilcoxon_rank_sum?.observed_statistic?.toFixed(1)}
              </div>
              <div className="text-xs font-mono text-slate-400">
                p_exact = {result.wilcoxon_rank_sum?.exact_p_value?.toFixed(4)}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-400">Hodges-Lehmann Shift (95% CI)</div>
              <div className="text-lg font-bold text-amber-400 mt-1">
                Δ = {result.hodges_lehmann_shift?.point_estimate?.toFixed(3)}
              </div>
              <div className="text-xs font-mono text-slate-400">
                [{result.hodges_lehmann_shift?.ci_95_lower?.toFixed(2)}, {result.hodges_lehmann_shift?.ci_95_upper?.toFixed(2)}]
              </div>
            </div>
          </div>

          {/* Detailed Statistics Comparison Table */}
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center justify-between">
              <span>Bảng So sánh Kiểm định Hoán vị Chính xác vs Chuẩn Asymptotic</span>
              <span className="text-xs text-slate-500 font-normal">
                B = {result.permutations_count?.toLocaleString()} permutations
              </span>
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="text-xs uppercase bg-slate-900/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Phương pháp / Thống kê</th>
                    <th className="py-2.5 px-3">Giá trị quan sát</th>
                    <th className="py-2.5 px-3">Exact P-value (Fisher)</th>
                    <th className="py-2.5 px-3">Asymptotic P-value (Welch)</th>
                    <th className="py-2.5 px-3">Ý nghĩa thống kê (α = 0.05)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                  <tr>
                    <td className="py-2.5 px-3 font-sans font-medium text-white">Hiệu số Trung bình (Difference in Means)</td>
                    <td className="py-2.5 px-3 text-emerald-400">{result.difference_in_means?.observed_statistic?.toFixed(4)}</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-400">{result.difference_in_means?.exact_p_value?.toFixed(4)}</td>
                    <td className="py-2.5 px-3 text-slate-400">{result.asymptotic_welch_t_test?.p_value?.toFixed(4)} (t = {result.asymptotic_welch_t_test?.t_statistic?.toFixed(3)})</td>
                    <td className="py-2.5 px-3 font-sans">
                      {result.difference_in_means?.is_significant ? (
                        <span className="text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Bác bỏ H₀</span>
                      ) : (
                        <span className="text-slate-500 bg-slate-800 px-2 py-0.5 rounded">Chấp nhận H₀</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans font-medium text-white">Hiệu số Trung vị (Difference in Medians)</td>
                    <td className="py-2.5 px-3 text-teal-400">{result.difference_in_medians?.observed_statistic?.toFixed(4)}</td>
                    <td className="py-2.5 px-3 font-bold text-teal-400">{result.difference_in_medians?.exact_p_value?.toFixed(4)}</td>
                    <td className="py-2.5 px-3 text-slate-500">— (Nonparametric)</td>
                    <td className="py-2.5 px-3 font-sans">
                      {result.difference_in_medians?.is_significant ? (
                        <span className="text-teal-400 font-semibold bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">Bác bỏ H₀</span>
                      ) : (
                        <span className="text-slate-500 bg-slate-800 px-2 py-0.5 rounded">Chấp nhận H₀</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans font-medium text-white">Xếp hạng Wilcoxon Rank Sum (W)</td>
                    <td className="py-2.5 px-3 text-cyan-400">{result.wilcoxon_rank_sum?.observed_statistic?.toFixed(1)}</td>
                    <td className="py-2.5 px-3 font-bold text-cyan-400">{result.wilcoxon_rank_sum?.exact_p_value?.toFixed(4)}</td>
                    <td className="py-2.5 px-3 text-slate-500">— (Rank exact)</td>
                    <td className="py-2.5 px-3 font-sans">
                      {result.wilcoxon_rank_sum?.is_significant ? (
                        <span className="text-cyan-400 font-semibold bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">Bác bỏ H₀</span>
                      ) : (
                        <span className="text-slate-500 bg-slate-800 px-2 py-0.5 rounded">Chấp nhận H₀</span>
                      )}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* SVG Null Distribution Visualizer */}
          {result.svg_chart && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2">
                Biểu đồ Phân phối Hoán vị Dưới Giả thuyết Không (Fisher Sharp Null Distribution)
              </h4>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Tường thuật Khoa học Chuẩn APA 7th
                </h4>
                <button
                  onClick={copyToClipboard}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded transition flex items-center gap-1.5"
                >
                  {copiedNarrative ? (
                    <span className="text-emerald-400">Đã sao chép!</span>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                      </svg>
                      Sao chép APA
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed font-serif bg-slate-900/50 p-3 rounded border border-slate-800/80">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
