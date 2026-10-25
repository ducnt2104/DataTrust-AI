import React, { useState } from 'react';
import {
  QuantileSyntheticControlResult,
  QuantileSyntheticControlRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Scale,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertCircle,
  HelpCircle,
  Layers,
  Sparkles,
  BarChart3,
  TrendingUp,
  Percent,
  Compass
} from 'lucide-react';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface Props {
  surveyId: string;
  questions: QuestionSummary[];
}

export const QuantileSyntheticControlCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [unitQId, setUnitQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [treatedUnitId, setTreatedUnitId] = useState<string>('');
  const [treatmentTime, setTreatmentTime] = useState<string>('');
  const [selectedQuantiles, setSelectedQuantiles] = useState<number[]>([0.10, 0.25, 0.50, 0.75, 0.90]);
  const [regularizationLambda, setRegularizationLambda] = useState<number>(0.001);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<QuantileSyntheticControlResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Filter numeric questions for outcome
  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleToggleQuantile = (qVal: number) => {
    if (selectedQuantiles.includes(qVal)) {
      if (selectedQuantiles.length > 2) {
        setSelectedQuantiles(selectedQuantiles.filter(q => q !== qVal));
      }
    } else {
      setSelectedQuantiles([...selectedQuantiles, qVal].sort((a, b) => a - b));
    }
  };

  const handleRun = async () => {
    if (!outcomeQId || !unitQId || !timeQId || !treatedUnitId.trim() || !treatmentTime.trim()) {
      setError('Vui lòng chọn biến kết quả, biến định danh đơn vị, biến chuỗi thời gian, mã đơn vị can thiệp và mốc thời gian.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: QuantileSyntheticControlRequest = {
      outcome_question_id: outcomeQId,
      unit_question_id: unitQId,
      time_question_id: timeQId,
      treated_unit_id: treatedUnitId.trim(),
      treatment_time: isNaN(Number(treatmentTime)) ? treatmentTime.trim() : Number(treatmentTime),
      quantiles: selectedQuantiles,
      regularization_lambda: regularizationLambda,
      scope
    };

    try {
      const res = await api.runQuantileSyntheticControl(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể tính toán Quantile Synthetic Control.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Quantile Synthetic Control.');
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

  const summary = result?.overall_summary;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/60 rounded-lg text-indigo-600 dark:text-indigo-400">
              <Scale className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Quantile Synthetic Control &amp; Distributional Counterfactuals
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Gunsilius (2023, Econometrica) · Wasserstein Barycenter Optimization · Quantile Treatment Effects &tau;(u) · Gini Inequality Impacts
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
            Gunsilius 2023 Econometrica
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
            Wasserstein Distance
          </span>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Outcome */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến kết quả Y (Outcome)
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn câu hỏi điểm số / chỉ số --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Unit Identifier */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến đơn vị (Unit Identifier)
          </label>
          <select
            value={unitQId}
            onChange={(e) => setUnitQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn mã đơn vị / chi nhánh / tỉnh --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Time Wave Identifier */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến chuỗi thời gian (Time Wave / Period)
          </label>
          <select
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn đợt khảo sát / quý / tuần --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Treated Unit ID */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Mã đơn vị can thiệp (Treated Unit ID)
          </label>
          <input
            type="text"
            value={treatedUnitId}
            onChange={(e) => setTreatedUnitId(e.target.value)}
            placeholder="Ví dụ: Unit_A, ChiNhanh1, Hospital_X"
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          />
        </div>

        {/* Treatment Time */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Mốc thời gian can thiệp (Post &ge; Threshold)
          </label>
          <input
            type="text"
            value={treatmentTime}
            onChange={(e) => setTreatmentTime(e.target.value)}
            placeholder="Ví dụ: 3, 2024Q3, Wave_4"
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          />
        </div>

        {/* Scope */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Phạm vi dữ liệu (Scope)
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="all">Tất cả phản hồi hợp lệ (All)</option>
            <option value="verified_clean">Chỉ mẫu đã kiểm định sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Quantiles Selector */}
      <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-lg border border-slate-200 dark:border-slate-750">
        <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
          <Percent className="w-4 h-4 text-indigo-500" />
          Các phân vị phân phối u &isin; (0, 1) cần ước lượng hiệu ứng:
        </div>
        <div className="flex flex-wrap gap-3">
          {[0.05, 0.10, 0.20, 0.25, 0.50, 0.75, 0.80, 0.90, 0.95].map((qVal) => (
            <label
              key={qVal}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
                selectedQuantiles.includes(qVal)
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700'
              }`}
            >
              <input
                type="checkbox"
                className="hidden"
                checked={selectedQuantiles.includes(qVal)}
                onChange={() => handleToggleQuantile(qVal)}
              />
              P{(qVal * 100).toFixed(0)} ({qVal.toFixed(2)})
            </label>
          ))}
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          onClick={handleRun}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
        >
          {loading ? (
            <>
              <RotateCcw className="w-4 h-4 animate-spin" />
              Đang tối ưu Wasserstein Barycenter...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Ước lượng Quantile Synthetic Control
            </>
          )}
        </button>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 rounded-lg text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && summary && (
        <div className="space-y-6 pt-4 border-t border-slate-200 dark:border-slate-800">
          {/* Key Metric Tiles */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Median QTE &tau;(0.50)
              </span>
              <span className={`text-lg font-bold ${summary.median_qte_effect >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                {summary.median_qte_effect > 0 ? `+${summary.median_qte_effect.toFixed(2)}` : summary.median_qte_effect.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Mean QTE: {summary.mean_qte_effect.toFixed(2)}
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Tác động Gini (&Delta;Gini)
              </span>
              <span className={`text-lg font-bold ${summary.gini_impact <= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                {summary.gini_impact > 0 ? `+${summary.gini_impact.toFixed(4)}` : summary.gini_impact.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {summary.gini_impact <= 0 ? 'Giảm bất bình đẳng' : 'Mở rộng khoảng cách'}
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Pre-W2 Distance
              </span>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                {summary.pre_treatment_wasserstein_dist.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {summary.pre_treatment_periods} kỳ tiền can thiệp
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Độ nén IQR (&Delta;IQR)
              </span>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                {summary.iqr_impact > 0 ? `+${summary.iqr_impact.toFixed(2)}` : summary.iqr_impact.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                IQR: {summary.iqr_observed.toFixed(1)} vs {summary.iqr_counterfactual.toFixed(1)}
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Đơn vị đối chứng (Donors)
              </span>
              <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                J = {summary.n_valid_donors}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {summary.post_treatment_periods} kỳ hậu can thiệp
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 p-2">
              <div
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                className="w-full flex justify-center"
              />
            </div>
          )}

          {/* Donor Weights & Quantile Treatment Effects Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Donor Weights Table */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-indigo-500" />
                Trọng số Đơn vị Đối chứng Tối ưu (Optimal Donor Weights w_j)
              </h4>
              <div className="overflow-x-auto max-h-64">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-750 text-slate-600 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2">Đơn vị Đối chứng (Donor)</th>
                      <th className="p-2 text-right">Trọng số w</th>
                      <th className="p-2 text-right">Đóng góp (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {result.donor_weights && result.donor_weights.length > 0 ? (
                      result.donor_weights.map((dw, idx) => (
                        <tr key={idx} className="hover:bg-slate-100/50 dark:hover:bg-slate-700/40">
                          <td className="p-2 font-medium text-slate-800 dark:text-slate-200">
                            {dw.donor_unit}
                          </td>
                          <td className="p-2 text-right font-mono text-slate-600 dark:text-slate-300">
                            {dw.weight.toFixed(4)}
                          </td>
                          <td className="p-2 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                                {dw.weight_pct.toFixed(1)}%
                              </span>
                              <div className="w-12 bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
                                <div
                                  className="bg-indigo-600 h-1.5 rounded-full"
                                  style={{ width: `${Math.min(100, dw.weight_pct)}%` }}
                                />
                              </div>
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3} className="p-4 text-center text-slate-400">
                          Không có đơn vị đối chứng nào có trọng số đáng kể.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* QTE Table */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <BarChart3 className="w-4 h-4 text-emerald-500" />
                Hiệu ứng Phân vị Hậu Can thiệp (&tau;(u) across Quantiles)
              </h4>
              <div className="overflow-x-auto max-h-64">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-750 text-slate-600 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2">Phân vị</th>
                      <th className="p-2 text-right">Quan sát Q_obs</th>
                      <th className="p-2 text-right">Phản thực tế Q*</th>
                      <th className="p-2 text-right">Hiệu ứng &tau;(u)</th>
                      <th className="p-2">Ý nghĩa</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {result.quantile_treatment_effects?.map((qte, idx) => (
                      <tr key={idx} className="hover:bg-slate-100/50 dark:hover:bg-slate-700/40">
                        <td className="p-2 font-bold text-slate-800 dark:text-slate-200">
                          {qte.quantile_label}
                        </td>
                        <td className="p-2 text-right font-mono text-slate-600 dark:text-slate-300">
                          {qte.treated_observed.toFixed(2)}
                        </td>
                        <td className="p-2 text-right font-mono text-slate-600 dark:text-slate-300">
                          {qte.synthetic_counterfactual.toFixed(2)}
                        </td>
                        <td className={`p-2 text-right font-mono font-bold ${qte.treatment_effect_qte >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                          {qte.treatment_effect_qte > 0 ? `+${qte.treatment_effect_qte.toFixed(2)}` : qte.treatment_effect_qte.toFixed(2)}
                        </td>
                        <td className="p-2 text-[10px] text-slate-500 dark:text-slate-400">
                          {qte.interpretation}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* APA Narrative Block */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-indigo-500" />
                  Bản tường trình Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyAPA}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
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
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-serif italic">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
