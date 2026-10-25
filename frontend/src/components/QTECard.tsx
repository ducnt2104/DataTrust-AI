import React, { useState } from 'react';
import { api } from '../api/client';
import { QTEResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface QTECardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const QTECard: React.FC<QTECardProps> = ({
  surveyId,
  questions
}) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QTEResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const binaryOrNumericQuestions = questions.filter(q =>
    ['single_choice', 'boolean', 'number', 'scale'].includes(q.question_type)
  );

  const toggleCovariate = (qid: string) => {
    if (covariateQIds.includes(qid)) {
      setCovariateQIds(covariateQIds.filter(id => id !== qid));
    } else {
      setCovariateQIds([...covariateQIds, qid]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả (Outcome Y).');
      return;
    }
    if (!treatmentQId) {
      setError('Vui lòng chọn câu hỏi biến can thiệp / chính sách (Treatment D).');
      return;
    }
    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả và biến can thiệp không được trùng nhau.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runQTEAnalysis(surveyId, {
        outcome_question_id: outcomeQId,
        treatment_question_id: treatmentQId,
        covariate_question_ids: covariateQIds.filter(id => id !== outcomeQId && id !== treatmentQId),
        quantiles: [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90],
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình QTE.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích QTE.');
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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-sky-500/10 text-sky-400 font-bold text-sm">
              QTE
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Quantile Treatment Effects (Hiệu ứng Can thiệp Lượng vị &amp; Tác động Bất bình đẳng)
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Bóc tách tác động nhân quả không đồng nhất của chính sách trên toàn bộ phân phối biến kết quả (Firpo, 2007; Koenker &amp; Bassett, 1978; Chernozhukov et al., 2013).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Bộ lọc dữ liệu:</span>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500"
          >
            <option value="all">Tất cả phản hồi hoàn thành</option>
            <option value="verified_clean">Chỉ mẫu sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Selectors */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Outcome Y */}
        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            1. Biến Kết Quả Đánh Giá (Outcome Y - Liên tục):
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 p-2.5 focus:border-sky-500 focus:outline-none"
          >
            <option value="">-- Chọn câu hỏi biến kết quả --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Treatment D */}
        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            2. Biến Can Thiệp / Chính Sách (Treatment D - Nhị phân 0/1):
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 p-2.5 focus:border-sky-500 focus:outline-none"
          >
            <option value="">-- Chọn câu hỏi phân nhóm can thiệp --</option>
            {binaryOrNumericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Confounder Multi-select */}
      <div className="mt-4 bg-slate-800/40 p-4 rounded-xl border border-slate-700/50">
        <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
          3. Biến Kiểm Soát / Nhiễu (Confounders X - Dùng cho trọng số nghịch đảo xu hướng IPW, tùy chọn):
        </label>
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-1">
          {numericQuestions
            .filter(q => q.id !== outcomeQId && q.id !== treatmentQId)
            .map(q => {
              const isSelected = covariateQIds.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleCovariate(q.id)}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                    isSelected
                      ? 'bg-sky-500/20 border-sky-400 text-sky-300 font-semibold shadow-sm'
                      : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-200'
                  }`}
                >
                  {isSelected ? '✓ ' : '+ '}
                  {q.title}
                </button>
              );
            })}
        </div>
      </div>

      {/* Action Button */}
      <div className="mt-5 flex justify-end">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-6 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs tracking-wide uppercase transition-all shadow-lg shadow-sky-900/30 disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Đang ước lượng QTE bán tham số...
            </>
          ) : (
            'Ước Lượng Quantile Treatment Effects'
          )}
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mt-5 p-4 bg-red-950/40 border border-red-800/80 rounded-lg text-sm text-red-300 flex items-start gap-2">
          <span className="text-base">⚠️</span>
          <div>
            <div className="font-semibold">Thông báo phân tích:</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && result.status === 'success' && (
        <div className="mt-8 space-y-6">
          {/* Diagnostic KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* ATE */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-amber-400 tracking-wider">
                Hiệu Ứng Trung Bình (ATE)
              </span>
              <div className="text-2xl font-black text-amber-300 mt-1">
                {result.average_treatment_effect !== undefined && result.average_treatment_effect > 0
                  ? `+${result.average_treatment_effect.toFixed(3)}`
                  : result.average_treatment_effect?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Kỳ vọng trung bình toàn bộ mẫu (E[Y(1) - Y(0)])
              </div>
            </div>

            {/* Median QTE */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-sky-400 tracking-wider">
                Hiệu Ứng Trung Vị (QTE q = 0.50)
              </span>
              <div className="text-2xl font-black text-sky-300 mt-1">
                {result.median_treatment_effect !== undefined && result.median_treatment_effect > 0
                  ? `+${result.median_treatment_effect.toFixed(3)}`
                  : result.median_treatment_effect?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Tác động lên người trả lời điển hình ở vị trí giữa
              </div>
            </div>

            {/* Delta IQR */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-emerald-400 tracking-wider">
                Dịch Chuyển IQR (ΔIQR)
              </span>
              <div className="text-2xl font-black text-emerald-300 mt-1">
                {result.delta_iqr_effect !== undefined && result.delta_iqr_effect > 0
                  ? `+${result.delta_iqr_effect.toFixed(3)}`
                  : result.delta_iqr_effect?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                QTE(0.75) - QTE(0.25) | Δ(90-10): {result.delta_90_10_effect?.toFixed(3)}
              </div>
            </div>

            {/* Inequality Impact Badge */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                Phân Loại Tác Động Bất Bình Đẳng
              </span>
              <div className="text-sm font-bold text-white mt-2 leading-tight">
                {result.inequality_impact}
              </div>
              <div className="text-xs font-semibold text-slate-400 mt-1">
                Phân hóa: {result.has_heterogeneous_distributional_effects ? 'Không đồng nhất (p < .05)' : 'Đồng đều'}
              </div>
            </div>
          </div>

          {/* Sample Size Bar */}
          <div className="bg-slate-800/40 px-4 py-2.5 rounded-lg border border-slate-700/50 flex flex-wrap items-center justify-between text-xs text-slate-300">
            <div>
              Tổng mẫu phân tích: <strong>{result.sample_size}</strong> quan sát
              (Can thiệp: <strong className="text-emerald-400">{result.treated_count}</strong>,
              Đối chứng: <strong className="text-rose-400">{result.control_count}</strong>)
            </div>
            <div className="text-slate-400">
              Phương pháp: Bán tham số Firpo (2007) + Silverman Kernel Density
            </div>
          </div>

          {/* Quantile Details Table */}
          {result.quantile_effects && result.quantile_effects.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
              <div className="p-4 border-b border-slate-800 font-bold text-xs text-slate-300 uppercase tracking-wider">
                Bảng Ước Lượng Hiệu Ứng Lượng Vị Chi Tiết Qua Từng Mốc Phân Vị
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-800/70 text-slate-400 border-b border-slate-700/60 font-semibold">
                      <th className="py-2.5 px-4">Phân vị (Quantile)</th>
                      <th className="py-2.5 px-4">Hiệu ứng QTE</th>
                      <th className="py-2.5 px-4">Lượng vị Can thiệp q₁</th>
                      <th className="py-2.5 px-4">Lượng vị Đối chứng q₀</th>
                      <th className="py-2.5 px-4">Sai số chuẩn (SE)</th>
                      <th className="py-2.5 px-4">Thống kê z</th>
                      <th className="py-2.5 px-4">p-value</th>
                      <th className="py-2.5 px-4">Khoảng tin cậy 95%</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.quantile_effects.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-4 font-bold text-sky-400">
                          q = {item.quantile.toFixed(2)}
                        </td>
                        <td className="py-2.5 px-4 font-black text-white">
                          {item.qte > 0 ? `+${item.qte.toFixed(3)}` : item.qte.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-4 text-emerald-400">{item.q_treated.toFixed(3)}</td>
                        <td className="py-2.5 px-4 text-rose-400">{item.q_control.toFixed(3)}</td>
                        <td className="py-2.5 px-4 text-slate-400">{item.std_error.toFixed(4)}</td>
                        <td className="py-2.5 px-4 font-mono">{item.z_statistic.toFixed(2)}</td>
                        <td className="py-2.5 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              item.is_significant
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {item.p_value < 0.001 ? '< .001' : item.p_value.toFixed(3)}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 font-mono text-slate-400">
                          [{item.ci_95_lower.toFixed(2)}, {item.ci_95_upper.toFixed(2)}]
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Vector SVG Dual-Panel Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-inner">
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                Biểu đồ Phân tích Không gian Lượng vị &amp; Hàm Tích lũy (Counterfactual CDFs)
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Edition Academic Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700/60 relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-sky-400 uppercase tracking-wider">
                  Diễn giải Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="text-xs px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
                >
                  {copiedNarrative ? '✓ Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed italic whitespace-pre-line">
                {result.apa_narrative}
              </p>
            </div>
          )}

          {/* Methodological Reference Note */}
          <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="font-semibold text-slate-300">Tài liệu tham khảo phương pháp:</div>
            <ul className="list-disc list-inside space-y-0.5 text-slate-400">
              <li>Firpo, S. (2007). Efficient semiparametric estimation of quantile treatment effects. <em>Econometrica</em>, 75(1), 259-276.</li>
              <li>Koenker, R., &amp; Bassett, G. (1978). Regression quantiles. <em>Econometrica</em>, 46(1), 33-50.</li>
              <li>Chernozhukov, V., Fernandez-Val, I., &amp; Melly, B. (2013). Inference on counterfactual distributions. <em>Econometrica</em>, 81(6), 2205-2268.</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
