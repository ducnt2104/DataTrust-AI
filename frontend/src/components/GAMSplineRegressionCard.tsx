import React, { useState } from 'react';
import { api } from '../api/client';
import { GAMSplineAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface GAMSplineRegressionCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const GAMSplineRegressionCard: React.FC<GAMSplineRegressionCardProps> = ({
  surveyId,
  questions
}) => {
  const [predictorQId, setPredictorQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [nKnots, setNKnots] = useState<number>(5);
  const [smoothingPenalty, setSmoothingPenalty] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GAMSplineAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  // Lọc các câu hỏi có thể chuyển đổi thành điểm số định lượng
  const numericOrRatingQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!predictorQId) {
      setError('Vui lòng chọn biến dự báo (Predictor X).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả (Outcome Y).');
      return;
    }
    if (predictorQId === outcomeQId) {
      setError('Biến dự báo và biến kết quả không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await api.runGAMSplineAnalysis(surveyId, {
        predictor_question_id: predictorQId,
        outcome_question_id: outcomeQId,
        n_knots: nKnots,
        smoothing_penalty: smoothingPenalty,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể thực thi phân tích GAM Spline.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi hệ thống khi phân tích GAM Spline.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2500);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg font-bold text-slate-800">
              Mô hình GAM & Hồi quy Spline Trơn (Generalized Additive Models)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Non-Linear Spline
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
              Hastie & Tibshirani 1990 • Wood 2017
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Bóc tách và kiểm định quan hệ phi tuyến tính phức tạp (đường cong liều lượng Dose-Response, mệt mỏi trả lời,
            điểm bão hòa hiệu suất) bằng hàm cơ sở Natural Cubic Spline và kiểm định F phi tuyến.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
        {/* Predictor Question */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Biến Dự báo (Predictor X) *
          </label>
          <select
            value={predictorQId}
            onChange={e => setPredictorQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến dự báo --</option>
            {numericOrRatingQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 30 ? q.title.substring(0, 30) + '…' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Trục hoành X (thời lượng, tuổi, điểm...)</p>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Biến Kết quả (Outcome Y) *
          </label>
          <select
            value={outcomeQId}
            onChange={e => setOutcomeQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {numericOrRatingQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 30 ? q.title.substring(0, 30) + '…' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Trục tung Y (sự hài lòng, độ chính xác...)</p>
        </div>

        {/* Number of Knots */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Số Mốc Spline (Knots K)
          </label>
          <select
            value={nKnots}
            onChange={e => setNKnots(parseInt(e.target.value, 10))}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value={3}>3 Mốc (Uốn lượn cơ bản)</option>
            <option value={4}>4 Mốc (Phân vị chuẩn)</option>
            <option value={5}>5 Mốc (Khuyến nghị chuẩn Wood)</option>
            <option value={6}>6 Mốc (Độ cong chi tiết)</option>
            <option value={7}>7 Mốc (Đa cực trị phức tạp)</option>
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Vị trí mốc đặt theo phân vị phân bố</p>
        </div>

        {/* Smoothing Penalty Lambda */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Hệ số Phạt Trơn (λ)
          </label>
          <select
            value={smoothingPenalty}
            onChange={e => setSmoothingPenalty(parseFloat(e.target.value))}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value={0.1}>λ = 0.1 (Rất mềm, uốn mạnh)</option>
            <option value={0.5}>λ = 0.5 (Mềm, bám sát mẫu)</option>
            <option value={1.0}>λ = 1.0 (Cân bằng chuẩn mực)</option>
            <option value={2.0}>λ = 2.0 (Khá cứng, triệt nhiễu)</option>
            <option value={5.0}>λ = 5.0 (Rất cứng, tiệm cận đường thẳng)</option>
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Ngăn chặn hiện tượng quá khớp (overfitting)</p>
        </div>

        {/* Scope */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi Phân tích
          </label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as any)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">Toàn bộ phản hồi (All)</option>
            <option value="verified_clean">Chỉ mẫu sạch (Quality ≥ 0.70)</option>
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Lọc bỏ phản hồi bất thường trước khi khớp</p>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang tính toán Natural Spline & GCV...</span>
            </>
          ) : (
            <>
              <span>Ước lượng Đường cong Phi tuyến (Fit GAM Spline)</span>
            </>
          )}
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
          <span className="font-bold">Lỗi:</span> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6 pt-2">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Cỡ mẫu & Mốc Knots</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                N = {result.sample_size}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Số mốc Knots: <strong className="text-emerald-700">{result.knots_count}</strong>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Bậc Tự do Hiệu dụng (EDF)</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                {result.gam_spline_model?.effective_degrees_of_freedom.toFixed(2)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {result.gam_spline_model && result.gam_spline_model.effective_degrees_of_freedom > 2.2
                  ? 'Độ cong phi tuyến rõ rệt (EDF > 2)'
                  : 'Xấp xỉ tuyến tính (EDF ≈ 2)'}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200">
              <span className="text-xs text-indigo-700 font-medium">Hệ số R² Giải thích</span>
              <div className="text-2xl font-bold text-indigo-900 mt-1">
                {result.gam_spline_model ? (result.gam_spline_model.r_squared * 100).toFixed(1) : 0}%
              </div>
              <div className="text-xs text-indigo-700 mt-1">
                Tuyến tính: {result.linear_baseline ? (result.linear_baseline.r_squared * 100).toFixed(1) : 0}% • GCV ={' '}
                {result.gam_spline_model?.gcv_score.toFixed(3)}
              </div>
            </div>

            <div
              className={`p-4 rounded-xl border ${
                result.nonlinearity_test?.is_significant_nonlinearity
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                  : 'bg-slate-50 border-slate-200 text-slate-800'
              }`}
            >
              <span className="text-xs font-bold uppercase tracking-wider">
                Kiểm định Phi tuyến (F-Test)
              </span>
              <div className="text-2xl font-black mt-1">
                F = {result.nonlinearity_test?.f_statistic.toFixed(2)}
              </div>
              <div className="text-xs font-medium mt-1">
                p = {result.nonlinearity_test?.p_value.toFixed(4)}{' '}
                {result.nonlinearity_test?.is_significant_nonlinearity ? '(p < .05: Đạt)' : '(Không có ý nghĩa)'}
              </div>
            </div>
          </div>

          {/* Non-linearity Verdict Alert */}
          <div
            className={`p-4 rounded-xl border flex items-start gap-3 ${
              result.nonlinearity_test?.is_significant_nonlinearity
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-amber-50 border-amber-300 text-amber-900'
            }`}
          >
            <div className="text-xl mt-0.5">
              {result.nonlinearity_test?.is_significant_nonlinearity ? '✓' : 'ℹ'}
            </div>
            <div>
              <div className="font-bold text-sm">
                {result.nonlinearity_test?.is_significant_nonlinearity
                  ? 'Phát hiện Mối quan hệ Phi tuyến tính có ý nghĩa thống kê rõ rệt'
                  : 'Mối quan hệ không thể hiện sự uốn lượn phi tuyến đáng kể'}
              </div>
              <p className="text-xs mt-1 opacity-90">
                {result.nonlinearity_test?.is_significant_nonlinearity
                  ? 'Mô hình hồi quy tuyến tính cổ điển OLS đã bỏ sót cấu trúc cong quan trọng của dữ liệu. Khuyến nghị sử dụng kết quả GAM Spline để thuyết minh chính sách và đưa ra khuyến nghị thực tế.'
                  : 'Giả định quan hệ tuyến tính thẳng là chấp nhận được, việc áp dụng mô hình phi tuyến tính không cải thiện đáng kể phương sai giải thích so với đường thẳng.'}
              </p>
            </div>
          </div>

          {/* Vector SVG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-800">
                    Đồ thị Đường cong Hồi quy GAM Spline & Dải băng Tin cậy 95% CI
                  </h4>
                  <p className="text-xs text-slate-500">
                    Đường màu xanh ngọc biểu diễn hàm trơn f(X), vùng bóng mờ biểu diễn khoảng tin cậy 95%, các đường đứt nét là vị trí mốc Knots.
                  </p>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-white rounded-lg border border-slate-200"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Turning Points Table */}
          {result.turning_points && result.turning_points.length > 0 && (
            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Các Điểm Uốn & Điểm Cực Trị Nhận Diện Được (Turning Points / Thresholds)
                </span>
                <span className="text-xs text-slate-500">f'(X) = 0</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      <th className="px-4 py-2 text-left font-semibold">Loại Điểm Uốn</th>
                      <th className="px-4 py-2 text-right font-semibold">Tọa độ Ngưỡng X</th>
                      <th className="px-4 py-2 text-right font-semibold">Giá trị Dự báo Y</th>
                      <th className="px-4 py-2 text-left font-semibold">Ý nghĩa Quản trị / Nghiên cứu</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.turning_points.map((tp, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-bold text-amber-800">{tp.point_type}</td>
                        <td className="px-4 py-2.5 text-right font-mono font-bold text-slate-800">
                          {tp.x_value.toFixed(2)}
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono text-emerald-700 font-semibold">
                          {tp.predicted_y.toFixed(2)}
                        </td>
                        <td className="px-4 py-2.5 text-slate-600">
                          {tp.point_type.includes('Cực đại')
                            ? 'Ngưỡng tối ưu - gia tăng thêm giá trị X sẽ bắt đầu gây suy giảm Y (quy luật hiệu suất giảm dần).'
                            : 'Điểm chạm đáy - sau ngưỡng này phản hồi bắt đầu có dấu hiệu hồi phục.'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Academic Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Thuyết Minh Báo Cáo Học Thuật (Định dạng APA 7th Edition)
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-slate-900 bg-white border border-slate-200 rounded hover:bg-slate-50 transition-colors shadow-2xs"
                >
                  {copiedNarrative ? '✓ Đã sao chép' : 'Sao chép văn bản'}
                </button>
              </div>
              <div className="p-3 bg-white rounded-lg border border-slate-200 text-slate-700 font-serif text-sm leading-relaxed whitespace-pre-line">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
