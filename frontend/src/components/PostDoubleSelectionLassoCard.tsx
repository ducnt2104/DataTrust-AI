import React, { useState } from 'react';
import { api } from '../api/client';
import { PostDoubleSelectionLassoResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const PostDoubleSelectionLassoCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [selectedControls, setSelectedControls] = useState<string[]>([]);
  const [cvFolds, setCvFolds] = useState<number>(5);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<PostDoubleSelectionLassoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleControl = (qid: string) => {
    setSelectedControls(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const selectAllCandidates = () => {
    const candidates = questions
      .filter(q => q.id !== outcomeQid && q.id !== treatmentQid)
      .map(q => q.id);
    setSelectedControls(candidates);
  };

  const clearCandidates = () => {
    setSelectedControls([]);
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQid || !treatmentQid) {
      setError('Vui lòng chọn Biến kết quả (Outcome) và Biến can thiệp (Treatment).');
      return;
    }
    if (selectedControls.length === 0) {
      setError('Vui lòng chọn ít nhất một Biến kiểm soát ứng viên (Candidate Control).');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const data = await api.runPostDoubleSelectionLasso(surveyId, {
        outcome_question_id: outcomeQid,
        treatment_question_id: treatmentQid,
        candidate_control_question_ids: selectedControls,
        cv_folds: cvFolds,
        alpha_level: alphaLevel,
        scope
      });

      if (data.status === 'INSUFFICIENT_SAMPLE' || data.status === 'ERROR') {
        setError(data.message || 'Lỗi khi thực hiện phân tích Post-Double-Selection Lasso.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực hiện phân tích Post-Double-Selection Lasso.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-4 mb-6 border-b border-slate-100 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-800">
              High-Dimensional Post-Double-Selection (PDS) Lasso
            </h2>
            <span className="bg-emerald-50 text-emerald-700 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
              Belloni, Chernozhukov, &amp; Hansen 2014
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Học máy trực giao Neyman ước lượng hiệu ứng nhân quả trong tập dữ liệu khảo sát nhiều chiều: Loại bỏ hoàn toàn thiên lệch biến bị bỏ sót (Omitted Variable Bias) thông qua cơ chế chọn lọc kép (Double Regularization).
          </p>
        </div>
      </div>

      {/* Primary Variable Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kết quả phụ thuộc Y (Outcome) <span className="text-red-500">*</span>
          </label>
          <select
            value={outcomeQid}
            onChange={e => setOutcomeQid(e.target.value)}
            className="w-full text-sm border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến can thiệp D (Treatment / Policy) <span className="text-red-500">*</span>
          </label>
          <select
            value={treatmentQid}
            onChange={e => setTreatmentQid(e.target.value)}
            className="w-full text-sm border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến can thiệp D --</option>
            {questions
              .filter(q => q.id !== outcomeQid)
              .map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* Candidate Controls Multi-Select */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-1.5">
          <label className="block text-xs font-semibold text-slate-600">
            Tập hợp Biến kiểm soát ứng viên nhiều chiều X (Candidate Controls) <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllCandidates}
              className="text-[11px] text-emerald-700 hover:text-emerald-800 font-medium underline"
            >
              Chọn tất cả
            </button>
            <span className="text-slate-300">|</span>
            <button
              type="button"
              onClick={clearCandidates}
              className="text-[11px] text-slate-500 hover:text-slate-600 underline"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
          {questions
            .filter(q => q.id !== outcomeQid && q.id !== treatmentQid)
            .map(q => {
              const isChecked = selectedControls.includes(q.id);
              return (
                <button
                  type="button"
                  key={q.id}
                  onClick={() => toggleControl(q.id)}
                  className={`text-xs px-2.5 py-1.5 rounded-md border transition-all text-left ${
                    isChecked
                      ? 'bg-emerald-600 text-white border-emerald-600 font-medium'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {isChecked ? '✓ ' : '+ '}
                  {q.title}
                </button>
              );
            })}
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          Đã chọn: {selectedControls.length} biến kiểm soát tiềm năng. PDS Lasso sẽ tự động chọn tập con tối ưu bằng chuẩn hóa L1.
        </p>
      </div>

      {/* Advanced Settings */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg border border-slate-100 mb-6 text-sm">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Số phân chia Cross-Validation (K-Folds)</label>
          <select
            value={cvFolds}
            onChange={e => setCvFolds(parseInt(e.target.value, 10) || 5)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          >
            <option value={3}>3-Fold CV (Nhanh)</option>
            <option value={5}>5-Fold CV (Chuẩn mực)</option>
            <option value={10}>10-Fold CV (Chính xác cao)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Mức ý nghĩa thống kê (alpha)</label>
          <select
            value={alphaLevel}
            onChange={e => setAlphaLevel(parseFloat(e.target.value) || 0.05)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          >
            <option value={0.01}>alpha = 0.01 (Độ tin cậy 99%)</option>
            <option value={0.05}>alpha = 0.05 (Độ tin cậy 95%)</option>
            <option value={0.10}>alpha = 0.10 (Độ tin cậy 90%)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Phạm vi dữ liệu khảo sát</label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as any)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          >
            <option value="all">Tất cả phản hồi</option>
            <option value="verified_clean">Chỉ phản hồi đã xác minh sạch</option>
          </select>
        </div>
      </div>

      {/* Action CTA */}
      <button
        onClick={handleRunAnalysis}
        disabled={loading}
        className="w-full sm:w-auto px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white text-sm font-semibold rounded-lg shadow-sm transition flex items-center justify-center gap-2 mb-6"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Đang thực thi Double Lasso CV &amp; Hồi quy Post-OLS...</span>
          </>
        ) : (
          <span>Thực thi Lựa chọn Kép Post-Double-Selection Lasso</span>
        )}
      </button>

      {/* Error display */}
      {error && (
        <div className="p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Lỗi:</strong> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && result.estimates && (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Tập Hợp Chọn Lọc (Union Set)</div>
              <div className="text-lg font-bold text-emerald-800 mt-1">
                {result.diagnostics.union_selected_controls} <span className="text-xs font-normal text-slate-500">/ {result.diagnostics.total_candidate_controls} biến</span>
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Giảm {(result.diagnostics.dimension_reduction_ratio * 100).toFixed(1)}% số chiều dữ liệu
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Lasso Bước 1 (Outcome Y)</div>
              <div className="text-lg font-bold text-blue-700 mt-1">
                {result.diagnostics.selected_by_outcome_model} biến
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                lambda_Y = {result.diagnostics.lambda_y_cross_validated}
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Lasso Bước 2 (Treatment D)</div>
              <div className="text-lg font-bold text-purple-700 mt-1">
                {result.diagnostics.selected_by_treatment_model} biến
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                lambda_D = {result.diagnostics.lambda_d_cross_validated}
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Hiệu ứng Causal PDS Lasso</div>
              <div className="text-lg font-bold text-emerald-700 mt-1">
                alpha = {result.estimates.post_double_selection_lasso.estimate.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 font-semibold">
                SE={result.estimates.post_double_selection_lasso.robust_se.toFixed(3)} · {result.estimates.post_double_selection_lasso.is_significant ? 'p < .05 (Ý nghĩa)' : 'p ≥ .05'}
              </div>
            </div>
          </div>

          {/* Estimates Comparison Table */}
          <div>
            <h3 className="text-sm font-bold text-slate-800 mb-2">So sánh Mô hình Ước lượng (Post-Double-Selection vs Benchmarks)</h3>
            <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2.5">Mô hình Phân tích</th>
                    <th className="px-4 py-2.5">Hệ số Causal (alpha)</th>
                    <th className="px-4 py-2.5">Sai số Chuẩn Robust (SE)</th>
                    <th className="px-4 py-2.5">z-stat</th>
                    <th className="px-4 py-2.5">p-value</th>
                    <th className="px-4 py-2.5">Khoảng Tin Cậy 95%</th>
                    <th className="px-4 py-2.5 text-center">Đánh giá Lý thuyết</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="bg-emerald-50/50 font-bold">
                    <td className="px-4 py-2.5 text-emerald-950">Post-Double-Selection Lasso (BCH 2014)</td>
                    <td className="px-4 py-2.5 text-emerald-800 font-mono text-sm">{result.estimates.post_double_selection_lasso.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-700 font-mono">{result.estimates.post_double_selection_lasso.robust_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-700">{result.estimates.post_double_selection_lasso.z_statistic.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-emerald-700">{result.estimates.post_double_selection_lasso.p_value < 0.001 ? '< .001' : result.estimates.post_double_selection_lasso.p_value.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">[{result.estimates.post_double_selection_lasso.ci_lower.toFixed(3)}, {result.estimates.post_double_selection_lasso.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-200 text-emerald-900">Chuẩn Mực Vàng Causal</span>
                    </td>
                  </tr>

                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">Naive Single-Selection Lasso (Chỉ chọn trên Y)</td>
                    <td className="px-4 py-2.5 font-mono text-rose-700 font-semibold">{result.estimates.naive_single_selection_lasso.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600 font-mono">{result.estimates.naive_single_selection_lasso.robust_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.estimates.naive_single_selection_lasso.z_statistic.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.estimates.naive_single_selection_lasso.p_value < 0.001 ? '< .001' : result.estimates.naive_single_selection_lasso.p_value.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">[{result.estimates.naive_single_selection_lasso.ci_lower.toFixed(3)}, {result.estimates.naive_single_selection_lasso.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-rose-100 text-rose-800">Nguy cơ Chệch Biến Bỏ Sót</span>
                    </td>
                  </tr>

                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">Unadjusted Base OLS (Không biến kiểm soát)</td>
                    <td className="px-4 py-2.5 font-mono text-amber-700 font-semibold">{result.estimates.unadjusted_base_ols.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600 font-mono">{result.estimates.unadjusted_base_ols.robust_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.estimates.unadjusted_base_ols.z_statistic.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.estimates.unadjusted_base_ols.p_value < 0.001 ? '< .001' : result.estimates.unadjusted_base_ols.p_value.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">[{result.estimates.unadjusted_base_ols.ci_lower.toFixed(3)}, {result.estimates.unadjusted_base_ols.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800">Thiên lệch Gây nhiễu Nặng</span>
                    </td>
                  </tr>

                  {result.estimates.saturated_full_ols.estimate !== undefined && (
                    <tr>
                      <td className="px-4 py-2.5 font-semibold text-slate-700">Saturated Full OLS (Tất cả biến kiểm soát)</td>
                      <td className="px-4 py-2.5 font-mono text-slate-700">{result.estimates.saturated_full_ols.estimate.toFixed(4)}</td>
                      <td className="px-4 py-2.5 text-slate-600 font-mono">{result.estimates.saturated_full_ols.robust_se?.toFixed(4)}</td>
                      <td className="px-4 py-2.5 text-slate-600">{result.estimates.saturated_full_ols.z_statistic?.toFixed(2)}</td>
                      <td className="px-4 py-2.5 text-slate-600">{result.estimates.saturated_full_ols.p_value && result.estimates.saturated_full_ols.p_value < 0.001 ? '< .001' : result.estimates.saturated_full_ols.p_value?.toFixed(4)}</td>
                      <td className="px-4 py-2.5 font-mono text-slate-600">[{result.estimates.saturated_full_ols.ci_lower?.toFixed(3)}, {result.estimates.saturated_full_ols.ci_upper?.toFixed(3)}]</td>
                      <td className="px-4 py-2.5 text-center">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">Phương sai Thổi phồng</span>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="mt-4">
              <h3 className="text-sm font-bold text-slate-800 mb-2">Bảng Phân loại Chọn lọc Biến &amp; Biểu đồ Forest Plot So sánh Mô hình</h3>
              <div
                className="w-full overflow-x-auto p-4 bg-white border border-slate-200 rounded-lg shadow-sm"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-emerald-50/60 border border-emerald-100 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-emerald-900 uppercase tracking-wide">
                  Tường thuật Kinh tế lượng chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyToClipboard}
                  className="text-xs px-2.5 py-1 bg-white border border-emerald-200 hover:bg-emerald-50 text-emerald-700 font-medium rounded transition"
                >
                  {copied ? 'Đã sao chép!' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-serif italic">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
