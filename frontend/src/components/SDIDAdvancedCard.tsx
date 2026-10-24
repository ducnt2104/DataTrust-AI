import React, { useState } from 'react';
import { api } from '../api/client';
import { SDIDAdvancedResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const SDIDAdvancedCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [unitQid, setUnitQid] = useState<string>('');
  const [timeQid, setTimeQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [zetaRegularization, setZetaRegularization] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SDIDAdvancedResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'trajectories' | 'unit_weights' | 'time_weights'>('trajectories');

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
      setError('Vui lòng chọn đầy đủ 4 biến: Kết quả (Y), Đơn vị (U), Thời gian (T), và Chỉ báo can thiệp (W).');
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
      const res = await api.runSDIDAdvanced(surveyId, {
        outcome_question_id: outcomeQid,
        unit_question_id: unitQid,
        time_question_id: timeQid,
        treatment_question_id: treatmentQid,
        zeta_regularization: zetaRegularization ? parseFloat(zetaRegularization) : null,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_UNITS' || res.status === 'INSUFFICIENT_TIME_PERIODS' || res.status === 'NO_TREATED_OR_CONTROL_UNITS') {
        setError(res.message || 'Không đủ điều kiện dữ liệu cho Synthetic DiD.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Synthetic Difference-in-Differences.');
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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-100 text-violet-800 border border-violet-200">
              Econometrics v3.16
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
              Arkhangelsky et al. (2021) AER
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-100 text-teal-800 border border-teal-200">
              Double-Robust Synthetic DiD
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Khác biệt kép Tổng hợp Nâng cao (Synthetic Difference-in-Differences - SDID)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Kết hợp điểm mạnh của DiD (bất biến chuyển dịch mức nền) và Synthetic Control (trọng số đơn vị đối chứng tối ưu), bổ sung trọng số chuỗi thời gian nhằm triệt tiêu chệch xu hướng vi phạm giả định song song.
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
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-violet-500 focus:ring-violet-500 bg-white p-2 border"
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
            Mã đơn vị / Khách thể Unit (i) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-violet-500 focus:ring-violet-500 bg-white p-2 border"
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
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-violet-500 focus:ring-violet-500 bg-white p-2 border"
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
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-violet-500 focus:ring-violet-500 bg-white p-2 border"
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
            Hệ số phạt L2 Zeta (Tùy chọn)
          </label>
          <input
            type="number"
            step="0.001"
            min="0"
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-violet-500 focus:ring-violet-500 bg-white p-2 border"
            placeholder="Mặc định: Tự điều chỉnh phân tán sai phân"
            value={zetaRegularization}
            onChange={(e) => setZetaRegularization(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi làm sạch mẫu
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-violet-500 focus:ring-violet-500 bg-white p-2 border"
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
              : 'bg-violet-600 hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500'
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
              Đang tối ưu hóa trọng số lồi & ước lượng SDID...
            </>
          ) : (
            'Ước lượng Tác động Can thiệp SDID'
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
            <div className="bg-violet-50 border border-violet-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-violet-700 uppercase tracking-wider">
                Ước lượng Tác động SDID (ATT)
              </span>
              <div className="text-2xl font-black text-violet-900 mt-1">
                {diag.tau_sdid.toFixed(4)}
              </div>
              <div className="text-xs text-violet-600 mt-1 flex items-center gap-1">
                <span>SE: {diag.se_sdid.toFixed(4)}</span>
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
                Khoảng tin cậy 95% (CI)
              </span>
              <div className="text-lg font-bold text-slate-800 mt-1">
                [{diag.ci_lower_95.toFixed(3)}, {diag.ci_upper_95.toFixed(3)}]
              </div>
              <div className="text-xs text-slate-500 mt-1">
                z-stat: {diag.z_statistic.toFixed(2)}
              </div>
              <div className="text-xs text-slate-500 mt-2">
                Độ rộng CI: {(diag.ci_upper_95 - diag.ci_lower_95).toFixed(3)}
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">
                So sánh DiD Truyền thống
              </span>
              <div className="text-lg font-bold text-blue-900 mt-1">
                {diag.tau_standard_did.toFixed(4)}
              </div>
              <div className="text-xs text-blue-700 mt-1">
                Độ lệch DiD: {diag.did_bias_gap > 0 ? `+${diag.did_bias_gap.toFixed(4)}` : diag.did_bias_gap.toFixed(4)}
              </div>
              <div className="text-xs text-slate-500 mt-2">
                SC chuẩn: {diag.tau_standard_sc.toFixed(4)}
              </div>
            </div>

            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
                Quy mô Bảng Dữ liệu & Tham số
              </span>
              <div className="text-sm font-semibold text-emerald-900 mt-1">
                {diag.n_treated_units} Can thiệp / {diag.n_control_units} Đối chứng
              </div>
              <div className="text-xs text-emerald-700 mt-1">
                {diag.n_pre_periods} Tiền kỳ / {diag.n_post_periods} Hậu kỳ
              </div>
              <div className="text-xs text-slate-600 mt-2">
                Dịch mức ω₀: {diag.unit_intercept_omega0.toFixed(3)} | ζ: {diag.zeta_regularization.toFixed(3)}
              </div>
            </div>
          </div>

          {/* SVG Visualizations */}
          {result.svg_visualization && (
            <div className="bg-slate-900 p-4 rounded-xl shadow-inner border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-violet-300 uppercase tracking-wider">
                  Biểu đồ Phân tích Nhân quả Tổng hợp Kép SDID (Dual-Panel Trajectory & Unit Weights)
                </span>
                <span className="text-xs text-slate-400">Arkhangelsky et al. (2021) AER</span>
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
                onClick={() => setActiveTab('trajectories')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'trajectories'
                    ? 'border-violet-600 text-violet-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Quỹ đạo Thời gian & Đối chứng (Trajectories)
              </button>
              <button
                onClick={() => setActiveTab('unit_weights')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'unit_weights'
                    ? 'border-violet-600 text-violet-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Trọng số Đơn vị Đối chứng (Unit Weights ω̂)
              </button>
              <button
                onClick={() => setActiveTab('time_weights')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'time_weights'
                    ? 'border-violet-600 text-violet-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Trọng số Thời gian Tiền kỳ (Time Weights λ̂)
              </button>
            </nav>
          </div>

          {/* Tab 1: Trajectories */}
          {activeTab === 'trajectories' && result.trajectories && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Mốc Thời gian (t)</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Giai đoạn</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-violet-700 uppercase">Can thiệp Thực tế Y(1)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-emerald-700 uppercase">Đối chứng Phản sự kiện SDID Ŷ(0)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-blue-700 uppercase">Synthetic Control Chuẩn</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Đối chứng Thô Không trọng số</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-amber-700 uppercase">Chênh lệch (Tác động)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.trajectories.map((row) => {
                    const diff = row.treated_actual - row.sdid_counterfactual;
                    return (
                      <tr key={row.time_period} className="hover:bg-slate-50">
                        <td className="px-4 py-2 font-medium text-slate-800">Kỳ {row.time_period}</td>
                        <td className="px-4 py-2 text-center">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              row.is_post_treatment
                                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {row.is_post_treatment ? 'Hậu can thiệp' : 'Tiền can thiệp'}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right font-semibold text-violet-800">{row.treated_actual.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right font-semibold text-emerald-800">{row.sdid_counterfactual.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right text-blue-800">{row.synthetic_control.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right text-slate-600">{row.control_unweighted.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right font-bold text-amber-800">
                          {row.is_post_treatment ? (diff > 0 ? `+${diff.toFixed(3)}` : diff.toFixed(3)) : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Unit Weights */}
          {activeTab === 'unit_weights' && result.unit_weights && (
            <div className="space-y-4">
              <p className="text-xs text-slate-500">
                Trọng số đơn vị tối ưu hóa lồi có ràng buộc (SLSQP Quadratic Programming với phạt L2 Zeta) cho các đơn vị đối chứng (Donor pool). Tổng trọng số bằng 1.0.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.unit_weights.map((uw) => (
                  <div key={uw.unit_id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-center text-sm font-medium text-slate-800">
                      <span>Đơn vị: {uw.unit_id}</span>
                      <span className="text-violet-700 font-bold">{(uw.percentage).toFixed(1)}% (ω = {uw.weight.toFixed(4)})</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 mt-2 overflow-hidden">
                      <div
                        className="bg-violet-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(100, Math.max(0, uw.percentage))}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 3: Time Weights */}
          {activeTab === 'time_weights' && result.time_weights && (
            <div className="space-y-4">
              <p className="text-xs text-slate-500">
                Trọng số chuỗi thời gian tiền kỳ tối ưu hóa lồi (Time weights λ̂). Các mốc thời gian có trọng số cao nhất đóng vai trò quan trọng nhất trong việc căn chỉnh xu hướng thời gian trước can thiệp.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.time_weights.map((tw) => (
                  <div key={tw.time_period} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-center text-sm font-medium text-slate-800">
                      <span>Mốc thời gian: Kỳ {tw.time_period}</span>
                      <span className="text-teal-700 font-bold">{(tw.percentage).toFixed(1)}% (λ = {tw.weight.toFixed(4)})</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 mt-2 overflow-hidden">
                      <div
                        className="bg-teal-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(100, Math.max(0, tw.percentage))}%` }}
                      ></div>
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
                  className="text-xs text-violet-600 hover:text-violet-800 font-medium"
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
