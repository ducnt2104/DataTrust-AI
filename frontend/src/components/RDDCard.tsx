import React, { useState } from 'react';
import { api } from '../api/client';
import { RDDAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface RDDCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const RDDCard: React.FC<RDDCardProps> = ({
  surveyId,
  questions
}) => {
  const [runningQId, setRunningQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [cutoffVal, setCutoffVal] = useState<number>(50.0);
  const [customBandwidth, setCustomBandwidth] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RDDAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericOrRatingQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!runningQId) {
      setError('Vui lòng chọn biến chỉ định phân loại (Running/Forcing Variable X).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả đầu ra (Outcome Variable Y).');
      return;
    }
    if (runningQId === outcomeQId) {
      setError('Biến chỉ định và biến kết quả không được trùng nhau.');
      return;
    }
    if (isNaN(cutoffVal)) {
      setError('Vui lòng nhập giá trị ngưỡng phân loại (Cutoff c) hợp lệ.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const bw = customBandwidth.trim() ? parseFloat(customBandwidth) : null;
      const data = await api.runRDDAnalysis(surveyId, {
        running_question_id: runningQId,
        outcome_question_id: outcomeQId,
        cutoff: cutoffVal,
        bandwidth: bw,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể thực thi phân tích RDD.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi hệ thống khi phân tích Sharp RDD.');
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
              Thiết kế Gián đoạn Hồi quy Sắc nét (Sharp Regression Discontinuity / RDD)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Quasi-Experiment
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
              Hahn et al. 2001 • Imbens 2012
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            "Tiêu chuẩn vàng" bán thực nghiệm để bóc tách tác động nhân quả cận biên (LATE) khi đối tượng được phân bổ
            can thiệp dựa trên một ngưỡng điểm cắt (Cutoff rule) trên biến liên tục.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
        {/* Running Question */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Biến Chỉ định (Running X) *
          </label>
          <select
            value={runningQId}
            onChange={e => setRunningQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến chỉ định --</option>
            {numericOrRatingQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 25 ? q.title.substring(0, 25) + '…' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Biến liên tục để phân loại can thiệp</p>
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
                {q.title.length > 25 ? q.title.substring(0, 25) + '…' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Biến đo lường hiệu quả chính sách</p>
        </div>

        {/* Cutoff Threshold */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Ngưỡng Phân loại (Cutoff c) *
          </label>
          <input
            type="number"
            step="any"
            value={cutoffVal}
            onChange={e => setCutoffVal(parseFloat(e.target.value))}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="Ví dụ: 50.0"
          />
          <p className="text-[11px] text-slate-500 mt-1">X ≥ c nhận can thiệp, X &lt; c đối chứng</p>
        </div>

        {/* Custom Bandwidth */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Dải thông h (Bandwidth)
          </label>
          <input
            type="number"
            step="any"
            value={customBandwidth}
            onChange={e => setCustomBandwidth(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="Tự động (IK 2012)"
          />
          <p className="text-[11px] text-slate-500 mt-1">Để trống để tối ưu hóa tự động</p>
        </div>

        {/* Scope */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi Khảo sát
          </label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as any)}
            className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">Toàn bộ phản hồi (All)</option>
            <option value="verified_clean">Chỉ mẫu sạch (Quality ≥ 0.70)</option>
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Lọc bỏ dữ liệu bất thường</p>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang tính toán IK Bandwidth & Local Polynomial...</span>
            </>
          ) : (
            <>
              <span>Ước lượng Tác động Cận ngưỡng (Run Sharp RDD)</span>
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
              <span className="text-xs text-slate-500 font-medium">Cỡ mẫu & Cửa sổ</span>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                N = {result.sample_size}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                N_hiệu_dụng = <strong className="text-indigo-700">{result.effective_sample_size}</strong> (trong cửa sổ h = {result.bandwidth?.toFixed(2)})
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
              <span className="text-xs text-emerald-800 font-bold uppercase tracking-wider">
                Tác động Cận biên (LATE τ_RDD)
              </span>
              <div className="text-2xl font-black text-emerald-950 mt-1">
                {result.treatment_effect_late?.tau_rdd != null && result.treatment_effect_late.tau_rdd > 0 ? '+' : ''}
                {result.treatment_effect_late?.tau_rdd.toFixed(3)}
              </div>
              <div className="text-xs text-emerald-800 font-medium mt-1">
                p = {result.treatment_effect_late?.p_value.toFixed(4)} • SE = {result.treatment_effect_late?.standard_error.toFixed(3)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Khoảng Tin cậy 95% CI</span>
              <div className="text-xl font-bold text-slate-800 mt-1.5 font-mono">
                [{result.treatment_effect_late?.ci_95_lower.toFixed(3)}, {result.treatment_effect_late?.ci_95_upper.toFixed(3)}]
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Thống kê z = {result.treatment_effect_late?.z_statistic.toFixed(2)}
              </div>
            </div>

            <div
              className={`p-4 rounded-xl border ${
                result.mccrary_manipulation_test?.has_manipulation
                  ? 'bg-rose-50 border-rose-300 text-rose-950'
                  : 'bg-emerald-50 border-emerald-300 text-emerald-950'
              }`}
            >
              <span className="text-xs font-bold uppercase tracking-wider">
                Kiểm định McCrary
              </span>
              <div className="text-lg font-black mt-1">
                {result.mccrary_manipulation_test?.has_manipulation ? 'Cảnh Báo Thao Túng' : 'Không Thao Túng (Hợp lệ)'}
              </div>
              <div className="text-xs font-medium mt-1">
                Δln(f) = {result.mccrary_manipulation_test?.log_difference.toFixed(3)} (p = {result.mccrary_manipulation_test?.p_value.toFixed(3)})
              </div>
            </div>
          </div>

          {/* RDD Causal Verdict Alert */}
          <div
            className={`p-4 rounded-xl border flex items-start gap-3 ${
              result.treatment_effect_late?.is_significant
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-amber-50 border-amber-300 text-amber-900'
            }`}
          >
            <div className="text-xl mt-0.5">
              {result.treatment_effect_late?.is_significant ? '✓' : 'ℹ'}
            </div>
            <div>
              <div className="font-bold text-sm">
                {result.treatment_effect_late?.is_significant
                  ? `Kết luận Nhân quả Cận ngưỡng: Can thiệp tạo ra bước nhảy gián đoạn có ý nghĩa thống kê (τ = ${result.treatment_effect_late?.tau_rdd.toFixed(3)}, p = ${result.treatment_effect_late?.p_value.toFixed(4)})`
                  : `Kết luận Nhân quả Cận ngưỡng: Chưa đủ bằng chứng chứng minh bước nhảy gián đoạn tại ngưỡng c = ${result.cutoff_threshold} (p = ${result.treatment_effect_late?.p_value.toFixed(4)})`}
              </div>
              <p className="text-xs mt-1 opacity-90">
                {result.mccrary_manipulation_test?.verdict}
              </p>
            </div>
          </div>

          {/* Vector SVG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-800">
                    Đồ thị Gián đoạn Hồi quy (RDD Binned Scatter & Local Polynomial Fit)
                  </h4>
                  <p className="text-xs text-slate-500">
                    Vùng bóng mờ xám thể hiện dải thông tối ưu [c - h, c + h]. Đường màu xanh lam và xanh ngọc thể hiện hàm hồi quy cục bộ 2 phía. Mũi tên đỏ đo lường bước nhảy LATE.
                  </p>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2 bg-white rounded-lg border border-slate-200"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
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
