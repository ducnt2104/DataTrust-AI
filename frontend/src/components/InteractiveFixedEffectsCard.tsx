import React, { useState } from 'react';
import { api } from '../api/client';
import { InteractiveFixedEffectsResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const InteractiveFixedEffectsCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [unitQid, setUnitQid] = useState<string>('');
  const [timeQid, setTimeQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [numFactors, setNumFactors] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<InteractiveFixedEffectsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'cell_effects' | 'scree_spectrum' | 'latent_factors'>('cell_effects');

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
      const res = await api.runInteractiveFixedEffects(surveyId, {
        outcome_question_id: outcomeQid,
        unit_question_id: unitQid,
        time_question_id: timeQid,
        treatment_question_id: treatmentQid,
        num_factors: numFactors ? parseInt(numFactors, 10) : null,
        scope
      });

      if (
        res.status === 'INSUFFICIENT_SAMPLE' ||
        res.status === 'INSUFFICIENT_UNITS' ||
        res.status === 'INSUFFICIENT_TIME_PERIODS' ||
        res.status === 'NO_TREATED_CELLS' ||
        res.status === 'INSUFFICIENT_CONTROLS'
      ) {
        setError(res.message || 'Không đủ điều kiện dữ liệu cho Mô hình Interactive Fixed Effects.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Interactive Fixed Effects.');
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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
              Econometrics v3.17
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">
              Bai (2009) Econometrica
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800 border border-sky-200">
              Interactive Fixed Effects & Factors
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Mô hình Tác động Cố định Tương tác (Interactive Fixed Effects - IFE)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Ước lượng tác động can thiệp nhân quả dưới cấu trúc nhân tố tiềm ẩn đa chiều và phụ thuộc chéo (Cross-Sectional Dependence). Bóc tách các cú sốc vĩ mô có tác động không đồng nhất lên các đơn vị khảo sát.
          </p>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5 p-4 bg-slate-50 rounded-lg border border-slate-200">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến kết quả Outcome (Y) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white p-2 border"
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Mã định danh đơn vị Unit (i) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white p-2 border"
            value={unitQid}
            onChange={(e) => setUnitQid(e.target.value)}
          >
            <option value="">-- Chọn biến định danh Unit --</option>
            {questions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Mốc thời gian Time Period (t) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white p-2 border"
            value={timeQid}
            onChange={(e) => setTimeQid(e.target.value)}
          >
            <option value="">-- Chọn mốc thời gian --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Chỉ báo Can thiệp Treatment (W) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white p-2 border"
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
          >
            <option value="">-- Chọn biến can thiệp W --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Số lượng nhân tố tiềm ẩn (Tùy chọn)
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white p-2 border"
            value={numFactors}
            onChange={(e) => setNumFactors(e.target.value)}
          >
            <option value="">Tự động tối ưu hóa (Bai-Ng 2002 IC)</option>
            <option value="1">1 Nhân tố tiềm ẩn (r = 1)</option>
            <option value="2">2 Nhân tố tiềm ẩn (r = 2)</option>
            <option value="3">3 Nhân tố tiềm ẩn (r = 3)</option>
            <option value="4">4 Nhân tố tiềm ẩn (r = 4)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi làm sạch mẫu
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white p-2 border"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
          >
            <option value="all">Toàn bộ mẫu khảo sát (All)</option>
            <option value="verified_clean">Chỉ mẫu kiểm định đạt chuẩn (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Action Button */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={handleRun}
          disabled={loading}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
            loading
              ? 'bg-slate-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
          }`}
        >
          {loading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Đang ước lượng ALS & ma trận nhân tố IFE...
            </>
          ) : (
            'Ước lượng Tác động Nhân tố Tương tác (IFE)'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm rounded">
          <p className="font-semibold">Thông báo:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Results View */}
      {result && diag && (
        <div className="mt-6 space-y-6">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">
                Ước lượng Tác động IFE (ATT)
              </span>
              <div className="text-2xl font-black text-indigo-900 mt-1">
                {diag.tau_ife.toFixed(4)}
              </div>
              <div className="text-xs text-indigo-600 mt-1 flex items-center gap-1">
                <span>SE: {diag.se_ife.toFixed(4)}</span>
                <span>•</span>
                <span>p: {diag.p_value < 0.001 ? '< 0.001' : diag.p_value.toFixed(4)}</span>
              </div>
              <div className="mt-2">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                    diag.is_statistically_significant
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                  }`}
                >
                  {diag.is_statistically_significant ? 'Ý nghĩa thống kê (p < 0.05)' : 'Không có ý nghĩa (p ≥ 0.05)'}
                </span>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                So sánh Two-Way Fixed Effects
              </span>
              <div className="text-lg font-bold text-slate-800 mt-1">
                TWFE: {diag.tau_twfe.toFixed(4)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Độ lệch Bias: {diag.factor_bias_gap > 0 ? `+${diag.factor_bias_gap.toFixed(4)}` : diag.factor_bias_gap.toFixed(4)}
              </div>
              <div className="text-xs text-indigo-700 font-medium mt-2">
                95% CI: [{diag.ci_lower_95.toFixed(3)}, {diag.ci_upper_95.toFixed(3)}]
              </div>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-purple-700 uppercase tracking-wider">
                Cấu trúc Nhân tố Tiềm ẩn (r*)
              </span>
              <div className="text-lg font-bold text-purple-900 mt-1">
                r = {diag.num_factors_selected} Nhân tố
              </div>
              <div className="text-xs text-purple-700 mt-1">
                Phương sai giải thích: {diag.total_variance_explained_pct.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-500 mt-2">
                {diag.n_treated_cells} Ô can thiệp / {diag.n_control_cells} Đối chứng
              </div>
            </div>

            <div className="bg-sky-50 border border-sky-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-sky-700 uppercase tracking-wider">
                Kiểm định Pesaran (2004) CD
              </span>
              <div className="text-lg font-bold text-sky-900 mt-1">
                CD = {diag.pesaran_cd_statistic.toFixed(2)}
              </div>
              <div className="text-xs text-sky-700 mt-1">
                p-value: {diag.pesaran_cd_p_value < 0.001 ? '< 0.001' : diag.pesaran_cd_p_value.toFixed(4)}
              </div>
              <div className="mt-2">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                    diag.cross_sectional_dependence_purged
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                  }`}
                >
                  {diag.cross_sectional_dependence_purged ? 'Triệt tiêu phụ thuộc chéo' : 'Còn phụ thuộc chéo'}
                </span>
              </div>
            </div>
          </div>

          {/* SVG Visualizations */}
          {result.svg_visualization && (
            <div className="bg-slate-900 p-4 rounded-xl shadow-inner border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">
                  Trực quan hóa Nhân tố Tiềm ẩn IFE (Dual-Panel Scree Spectrum & Factor Dynamics)
                </span>
                <span className="text-xs text-slate-400">Bai (2009) Econometrica</span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Tab Navigation */}
          <div className="border-b border-slate-200">
            <nav className="-mb-px flex space-x-6">
              <button
                onClick={() => setActiveTab('cell_effects')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'cell_effects'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Tác động Can thiệp Cục bộ (Cell Effects τ̂_it)
              </button>
              <button
                onClick={() => setActiveTab('scree_spectrum')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'scree_spectrum'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Phổ Giá trị Kỳ dị & Tiêu chuẩn Bai-Ng (Scree Spectrum)
              </button>
              <button
                onClick={() => setActiveTab('latent_factors')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'latent_factors'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Chuỗi Nhân tố Tiềm ẩn Chung (Factor Trajectories f_t)
              </button>
            </nav>
          </div>

          {/* Tab 1: Cell Effects */}
          {activeTab === 'cell_effects' && result.cell_effects && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Mã Đơn vị (i)</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Mốc Thời gian (t)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-indigo-700 uppercase">Y(1) Thực tế Quan sát</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-emerald-700 uppercase">Y(0) Phục dựng Phản sự kiện IFE</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-purple-700 uppercase">Tác động Can thiệp τ̂_it</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.cell_effects.map((cell, idx) => (
                    <tr key={`${cell.unit_id}-${cell.time_period}-${idx}`} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">{cell.unit_id}</td>
                      <td className="px-4 py-2 text-center text-slate-600">Kỳ {cell.time_period}</td>
                      <td className="px-4 py-2 text-right font-semibold text-indigo-800">{cell.observed_y.toFixed(3)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-emerald-800">{cell.counterfactual_y0.toFixed(3)}</td>
                      <td className="px-4 py-2 text-right font-bold text-purple-800">
                        {cell.treatment_effect > 0 ? `+${cell.treatment_effect.toFixed(3)}` : cell.treatment_effect.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Scree Spectrum */}
          {activeTab === 'scree_spectrum' && result.scree_spectrum && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Thứ tự Nhân tố</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Giá trị Riêng (Eigenvalue)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-indigo-700 uppercase">Phương sai Giải thích (%)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-purple-700 uppercase">Phương sai Tích lũy (%)</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Lựa chọn Mô hình</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.scree_spectrum.map((s) => (
                    <tr key={s.factor_number} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">Nhân tố F{s.factor_number}</td>
                      <td className="px-4 py-2 text-right text-slate-700">{s.eigenvalue.toFixed(4)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-indigo-800">{s.variance_pct.toFixed(2)}%</td>
                      <td className="px-4 py-2 text-right font-semibold text-purple-800">{s.cumulative_pct.toFixed(2)}%</td>
                      <td className="px-4 py-2 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            s.is_selected
                              ? 'bg-indigo-100 text-indigo-800 border border-indigo-300'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {s.is_selected ? 'Được chọn (r*)' : 'Bỏ qua'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Latent Factors */}
          {activeTab === 'latent_factors' && result.latent_factors && (
            <div className="space-y-4">
              <p className="text-xs text-slate-500">
                Các chuỗi thời gian của nhân tố tiềm ẩn chung (Common Factors f_t) phản ánh các cú sốc vĩ mô toàn hệ thống qua các mốc thời gian khảo sát.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.latent_factors.map((f) => (
                  <div key={f.factor_index} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-center text-sm font-semibold text-indigo-900 mb-2">
                      <span>Nhân tố F{f.factor_index}</span>
                      <span className="text-xs text-purple-700 font-bold">{f.variance_explained_pct.toFixed(1)}% phương sai</span>
                    </div>
                    <div className="space-y-1">
                      {f.series.map((item) => (
                        <div key={item.time_period} className="flex justify-between text-xs text-slate-700 py-0.5 border-b border-slate-100">
                          <span>Kỳ t = {item.time_period}</span>
                          <span className="font-mono font-medium">{item.value > 0 ? `+${item.value.toFixed(4)}` : item.value.toFixed(4)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Báo cáo Thuyết minh Khoa học chuẩn APA 7th
                </span>
                <button
                  onClick={() => {
                    if (result.apa_narrative) {
                      navigator.clipboard.writeText(result.apa_narrative);
                    }
                  }}
                  className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  Sao chép thuyết minh
                </button>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed italic bg-white p-3 rounded border border-slate-200">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
