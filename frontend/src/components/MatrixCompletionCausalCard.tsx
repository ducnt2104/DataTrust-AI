import React, { useState } from 'react';
import { api } from '../api/client';
import { MatrixCompletionCausalResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const MatrixCompletionCausalCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [unitQid, setUnitQid] = useState<string>('');
  const [timeQid, setTimeQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [lambdaPenalty, setLambdaPenalty] = useState<string>('');
  const [maxRank, setMaxRank] = useState<number>(3);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MatrixCompletionCausalResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'cell_effects' | 'singular_spectrum'>('cell_effects');

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'slider' ||
      q.question_type === 'short_text'
  );

  const handleRun = async () => {
    if (!outcomeQid || !unitQid || !timeQid || !treatmentQid) {
      setError('Vui lòng chọn đầy đủ 4 biến: Kết quả (Y), Đơn vị (U), Mốc thời gian (T), và Chỉ báo can thiệp (W).');
      return;
    }
    const selected = [outcomeQid, unitQid, timeQid, treatmentQid];
    if (new Set(selected).size !== 4) {
      setError('Các biến chọn phải là các câu hỏi khác nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.runMatrixCompletionCausal(surveyId, {
        outcome_question_id: outcomeQid,
        unit_question_id: unitQid,
        time_question_id: timeQid,
        treatment_question_id: treatmentQid,
        lambda_penalty: lambdaPenalty ? parseFloat(lambdaPenalty) : null,
        max_rank: maxRank,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_DIMENSIONS' || res.status === 'NO_TREATED_CELLS' || res.status === 'INSUFFICIENT_CONTROLS') {
        setError(res.message || 'Không đủ điều kiện dữ liệu cho Hoàn thiện Ma trận Nhân quả.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Matrix Completion.');
    } finally {
      setLoading(false);
    }
  };

  const diag = result?.diagnostics;

  return (
    <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 mb-8 transition-all hover:shadow-lg">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              Econometrics v3.15
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
              Athey et al. (2021) JASA
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-100 text-cyan-800 border border-cyan-200">
              Nuclear Norm Soft-Impute
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Hoàn thiện Ma trận Nhân quả (Causal Matrix Completion)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Phục dựng các giá trị đối chứng phản sự kiện chưa quan sát Y(0) thông qua tối ưu hóa lồi chuẩn hạt nhân, ước lượng tác động chính sách trên dữ liệu bảng phân tầng và không cân bằng.
          </p>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5 p-4 bg-slate-50 rounded-lg border border-slate-200">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến kết quả (Outcome Y) *
          </label>
          <select
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Mã đơn vị quan sát (Unit ID) *
          </label>
          <select
            value={unitQid}
            onChange={(e) => setUnitQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến đơn vị khảo sát --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Mốc / Đợt thời gian (Wave T) *
          </label>
          <select
            value={timeQid}
            onChange={(e) => setTimeQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến thời điểm T --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Chỉ báo Can thiệp (Treatment W) *
          </label>
          <select
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến can thiệp (1 vs 0) --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Hệ số phạt chuẩn hạt nhân (\u03bb)
          </label>
          <input
            type="number"
            step="any"
            placeholder="Tự động (Optimal SVT)"
            value={lambdaPenalty}
            onChange={(e) => setLambdaPenalty(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Hạng ma trận tối đa (Max Rank)
          </label>
          <input
            type="number"
            min={1}
            max={20}
            value={maxRank}
            onChange={(e) => setMaxRank(parseInt(e.target.value, 10) || 3)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          />
        </div>
      </div>

      <div className="mt-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Phạm vi:</label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="text-xs border-slate-300 rounded shadow-sm bg-white p-1"
          >
            <option value="all">Tất cả quan sát</option>
            <option value="verified_clean">Chỉ mẫu đã xác thực sạch</option>
          </select>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="inline-flex items-center px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm rounded-lg shadow-sm transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              Đang hoàn thiện ma trận...
            </>
          ) : (
            'Thực thi Hoàn thiện Ma trận'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
          <strong>Lỗi ước lượng:</strong> {error}
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && diag && (
        <div className="mt-6 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl">
              <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wide">
                Hiệu ứng Causal ATT (\u03c4_MC)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-emerald-900">
                  {diag.overall_att.toFixed(4)}
                </span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  diag.is_statistically_significant
                    ? 'bg-emerald-200 text-emerald-900'
                    : 'bg-slate-200 text-slate-700'
                }`}>
                  p = {diag.p_value < 0.001 ? '< 0.001' : diag.p_value.toFixed(4)}
                </span>
              </div>
              <p className="text-xs text-emerald-700 mt-1">
                SE: {diag.att_se.toFixed(4)} | 95% CI: [{diag.ci_lower_95.toFixed(3)}, {diag.ci_upper_95.toFixed(3)}]
              </p>
            </div>

            <div className="p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl">
              <span className="text-xs font-semibold text-indigo-800 uppercase tracking-wide">
                Hạng Hiệu dụng (Effective Rank r)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-indigo-900">
                  r = {diag.effective_rank}
                </span>
                <span className="text-xs text-indigo-700 font-medium">
                  ({(diag.top_factor_variance_share * 100).toFixed(1)}% phương sai)
                </span>
              </div>
              <p className="text-xs text-indigo-700 mt-1">
                Thu nhỏ chuẩn hạt nhân \u03bb = {diag.lambda_penalty.toFixed(3)}
              </p>
            </div>

            <div className="p-4 bg-cyan-50/70 border border-cyan-200 rounded-xl">
              <span className="text-xs font-semibold text-cyan-800 uppercase tracking-wide">
                Khớp Đối chứng RMSE
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-cyan-900">
                  {diag.rmse_control_fit.toFixed(4)}
                </span>
                <span className="text-xs text-cyan-700">
                  ({diag.iterations_count} vòng lặp)
                </span>
              </div>
              <p className="text-xs text-cyan-700 mt-1">
                Hội tụ Frobenius: {diag.is_converged ? 'Đã hội tụ' : 'Tối đa vòng'}
              </p>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                Ma trận Bảng / Ô Phục dựng
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  {diag.n_treated_cells}
                </span>
                <span className="text-xs text-slate-500">/ {diag.total_cells} tổng ô</span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {diag.n_units} đơn vị \u00d7 {diag.n_time_periods} đợt | {diag.n_control_cells} đối chứng
              </p>
            </div>
          </div>

          {/* Dual Panel SVG Chart */}
          {result.svg_visualization && (
            <div className="border border-slate-200 rounded-xl p-4 bg-white overflow-hidden shadow-sm">
              <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                Bản đồ Ma trận Bảng &amp; Phổ Giá trị Kỳ dị Thu nhỏ \u03bb (Athey et al. 2021)
              </h4>
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-slate-50/50 rounded-lg"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Sub-tabs: Cell Treatment Effects vs Singular Spectrum */}
          <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
            <div className="flex border-b border-slate-200 bg-slate-50 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('cell_effects')}
                className={`px-4 py-3 border-b-2 transition-colors ${
                  activeTab === 'cell_effects'
                    ? 'border-emerald-500 text-emerald-700 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Chi tiết Từng Ô Can thiệp (\u03c4_it = Y1 - Y0_hat)
              </button>
              <button
                onClick={() => setActiveTab('singular_spectrum')}
                className={`px-4 py-3 border-b-2 transition-colors ${
                  activeTab === 'singular_spectrum'
                    ? 'border-emerald-500 text-emerald-700 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Phổ Giá trị Kỳ dị &amp; Phương sai Giải thích
              </button>
            </div>

            <div className="p-4">
              {activeTab === 'cell_effects' && result.cell_treatment_effects && (
                <div className="overflow-x-auto max-h-64">
                  <table className="min-w-full divide-y divide-slate-200 text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold uppercase">
                      <tr>
                        <th className="px-4 py-2 text-left">Mã Đơn vị</th>
                        <th className="px-4 py-2 text-left">Đợt thời gian</th>
                        <th className="px-4 py-2 text-right">Quan sát Y(1)</th>
                        <th className="px-4 py-2 text-right">Phản sự kiện Phục dựng Y(0)</th>
                        <th className="px-4 py-2 text-right">Hiệu ứng Can thiệp \u03c4_it</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {result.cell_treatment_effects.map((c, idx) => (
                        <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                          <td className="px-4 py-1.5 font-medium">{c.unit_id}</td>
                          <td className="px-4 py-1.5 text-slate-600">t = {c.time_period}</td>
                          <td className="px-4 py-1.5 text-right font-mono">{c.realized_outcome_y1.toFixed(3)}</td>
                          <td className="px-4 py-1.5 text-right font-mono text-indigo-700">{c.imputed_counterfactual_y0.toFixed(3)}</td>
                          <td className="px-4 py-1.5 text-right font-mono font-bold text-emerald-700">
                            {c.treatment_effect_tau > 0 ? `+${c.treatment_effect_tau.toFixed(4)}` : c.treatment_effect_tau.toFixed(4)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'singular_spectrum' && result.singular_value_spectrum && (
                <div className="overflow-x-auto max-h-64">
                  <table className="min-w-full divide-y divide-slate-200 text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold uppercase">
                      <tr>
                        <th className="px-4 py-2 text-left">Thành phần Kỳ dị</th>
                        <th className="px-4 py-2 text-right">Giá trị Kỳ dị (\u03c3_k)</th>
                        <th className="px-4 py-2 text-right">Tỷ trọng Phương sai</th>
                        <th className="px-4 py-2 text-right">Đánh giá Nén</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {result.singular_value_spectrum.map((item, idx) => (
                        <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                          <td className="px-4 py-1.5 font-medium">Bậc {item.rank_component}</td>
                          <td className="px-4 py-1.5 text-right font-mono font-bold">{item.singular_value.toFixed(4)}</td>
                          <td className="px-4 py-1.5 text-right font-mono text-cyan-700">{(item.variance_explained_ratio * 100).toFixed(1)}%</td>
                          <td className="px-4 py-1.5 text-right">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              item.singular_value > 0.01 ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                            }`}>
                              {item.singular_value > 0.01 ? 'Nhân tố hữu hiệu' : 'Đã thu nhỏ về 0'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* APA 7th Scientific Narrative */}
          {result.apa_narrative && (
            <div className="p-5 bg-gradient-to-r from-slate-50 to-indigo-50/30 border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"></path>
                  </svg>
                  Tường thuật Khoa học Chuẩn APA 7th (Academic Findings Report)
                </h4>
                <button
                  onClick={() => navigator.clipboard.writeText(result.apa_narrative || '')}
                  className="text-xs text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
                >
                  Sao chép văn bản
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-serif whitespace-pre-line bg-white/70 p-3 rounded-lg border border-slate-200/80">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
