import React, { useState } from 'react';
import { api } from '../api/client';
import { RegressionKinkResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const RegressionKinkCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [runningQid, setRunningQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [cutoff, setCutoff] = useState<number>(50.0);
  const [bandwidth, setBandwidth] = useState<string>('');
  const [polynomialOrder, setPolynomialOrder] = useState<number>(1);
  const [knownKinkSlope, setKnownKinkSlope] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<RegressionKinkResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filter numeric questions
  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'slider'
  );

  const handleRun = async () => {
    if (!outcomeQid || !runningQid) {
      setError('Vui lòng chọn Biến kết quả (Y) và Biến gán chạy (Running Variable X).');
      return;
    }
    if (outcomeQid === runningQid) {
      setError('Biến kết quả và Biến gán chạy không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.runRegressionKink(surveyId, {
        outcome_question_id: outcomeQid,
        running_question_id: runningQid,
        cutoff: Number(cutoff),
        treatment_question_id: treatmentQid ? treatmentQid : null,
        bandwidth: bandwidth ? parseFloat(bandwidth) : null,
        polynomial_order: polynomialOrder,
        known_kink_slope: knownKinkSlope,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'ERROR') {
        setError(res.message || 'Lỗi khi thực thi hồi quy Regression Kink Design.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi không xác định khi gọi API RKD.');
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
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              Econometrics v3.15
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
              Card, Lee, Pei, & Weber (2015)
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Thiết kế Gãy Hồi quy (Regression Kink Design - RKD)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Nhận diện đạo hàm hiệu ứng nhân quả cục bộ (Marginal Policy Effect) khi biến gán thay đổi độ dốc tại điểm ngưỡng c mà không có bước nhảy đột ngột.
          </p>
        </div>
      </div>

      {/* Control Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-5 p-4 bg-slate-50 rounded-lg border border-slate-200">
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
            Biến gán chạy (Running Var X) *
          </label>
          <select
            value={runningQid}
            onChange={(e) => setRunningQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Chọn biến chạy X --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến xử lý D (Fuzzy RKD)
          </label>
          <select
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="">-- Để trống nếu là Sharp RKD --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Ngưỡng gãy (Cutoff c) *
          </label>
          <input
            type="number"
            step="any"
            value={cutoff}
            onChange={(e) => setCutoff(parseFloat(e.target.value) || 0)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Băng thông h (Bandwidth)
          </label>
          <input
            type="number"
            step="any"
            placeholder="Tự động (Silverman ROT)"
            value={bandwidth}
            onChange={(e) => setBandwidth(e.target.value)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Bậc đa thức (Order)
          </label>
          <select
            value={polynomialOrder}
            onChange={(e) => setPolynomialOrder(parseInt(e.target.value, 10))}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value={1}>Bậc 1 (Tuyến tính - Local Linear)</option>
            <option value={2}>Bậc 2 (Bậc hai - Local Quadratic)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Độ dốc gãy đã biết (Sharp k)
          </label>
          <input
            type="number"
            step="any"
            value={knownKinkSlope}
            onChange={(e) => setKnownKinkSlope(parseFloat(e.target.value) || 1.0)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white p-2"
          >
            <option value="all">Tất cả phản hồi</option>
            <option value="verified_clean">Chỉ mẫu đã xác thực sạch</option>
          </select>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
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
              Đang ước lượng RKD...
            </>
          ) : (
            'Thực thi Ước lượng RKD'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
          <strong>Lỗi thực thi:</strong> {error}
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && diag && (
        <div className="mt-6 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl">
              <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wide">
                Đạo hàm Causal Effect (\u03c4_RKD)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-emerald-900">
                  {diag.tau_rkd.toFixed(4)}
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
                SE: {diag.se_rkd.toFixed(4)} | 95% CI: [{diag.ci_lower_95.toFixed(3)}, {diag.ci_upper_95.toFixed(3)}]
              </p>
            </div>

            <div className="p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl">
              <span className="text-xs font-semibold text-indigo-800 uppercase tracking-wide">
                Độ gãy dốc Outcome (\u0394\u03b2_Y)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-indigo-900">
                  {diag.delta_slope_outcome.toFixed(4)}
                </span>
              </div>
              <p className="text-xs text-indigo-700 mt-1">
                Dốc trái: {diag.left_slope.toFixed(3)} \u2192 Dốc phải: {diag.right_slope.toFixed(3)}
              </p>
            </div>

            <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-xl">
              <span className="text-xs font-semibold text-amber-800 uppercase tracking-wide">
                Kiểm định McCrary Smoothness
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-amber-900">
                  p = {diag.mccrary_p_value.toFixed(4)}
                </span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  diag.is_density_smooth
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {diag.is_density_smooth ? 'Mật độ trơn (Hợp lệ)' : 'Có dấu hiệu dồn cụm'}
                </span>
              </div>
              <p className="text-xs text-amber-700 mt-1">
                Kiểm tra giả định không thao túng biến gán tại ngưỡng c = {diag.cutoff}
              </p>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                Mẫu hiệu dụng / Băng thông
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  {diag.effective_sample_size}
                </span>
                <span className="text-xs text-slate-500">/ {diag.sample_size_total} tổng mẫu</span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Băng thông h = \u00b1{diag.bandwidth.toFixed(3)} quanh ngưỡng c
              </p>
            </div>
          </div>

          {/* Dual Panel SVG Chart */}
          {result.svg_visualization && (
            <div className="border border-slate-200 rounded-xl p-4 bg-white overflow-hidden shadow-sm">
              <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                Trực quan hóa Điểm Gãy Bán thực nghiệm & Kiểm định Mật độ Chạy
              </h4>
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-slate-50/50 rounded-lg"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Binned Scatter Table */}
          {result.binned_scatter && result.binned_scatter.length > 0 && (
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
              <div className="p-4 bg-slate-50 border-b border-slate-200">
                <h4 className="text-sm font-bold text-slate-800">
                  Dữ liệu Điểm gom Cục bộ (Local Binned Scatter Data)
                </h4>
              </div>
              <div className="overflow-x-auto max-h-60">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-100 text-slate-600 uppercase font-semibold">
                    <tr>
                      <th className="px-4 py-2 text-left">Phía ngưỡng</th>
                      <th className="px-4 py-2 text-right">Tâm Bin (Running X)</th>
                      <th className="px-4 py-2 text-right">Trung bình Y</th>
                      <th className="px-4 py-2 text-right">Số lượng quan sát</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {result.binned_scatter.map((b, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                        <td className="px-4 py-1.5 font-medium">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            b.side === 'left' ? 'bg-blue-50 text-blue-700' : 'bg-emerald-50 text-emerald-700'
                          }`}>
                            {b.side === 'left' ? 'Bên trái (X < c)' : 'Bên phải (X \u2265 c)'}
                          </span>
                        </td>
                        <td className="px-4 py-1.5 text-right font-mono">{b.bin_center.toFixed(2)}</td>
                        <td className="px-4 py-1.5 text-right font-mono">{b.mean_outcome.toFixed(3)}</td>
                        <td className="px-4 py-1.5 text-right font-mono">{b.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

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
