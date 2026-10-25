import React, { useState } from 'react';
import { api } from '../api/client';
import { SDIDAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface SDIDCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const SDIDCard: React.FC<SDIDCardProps> = ({
  surveyId,
  questions
}) => {
  const [unitQId, setUnitQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatedUnitsInput, setTreatedUnitsInput] = useState<string>('');
  const [startTimeInput, setStartTimeInput] = useState<string>('');
  const [placeboReps, setPlaceboReps] = useState<number>(100);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SDIDAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!unitQId) {
      setError('Vui lòng chọn câu hỏi định danh đơn vị (Unit ID).');
      return;
    }
    if (!timeQId) {
      setError('Vui lòng chọn câu hỏi mốc thời gian / làn sóng (Time Period).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả (Outcome Y).');
      return;
    }
    if (!treatedUnitsInput.trim()) {
      setError('Vui lòng nhập danh sách mã các đơn vị can thiệp (cách nhau bởi dấu phẩy, VD: Region_1).');
      return;
    }
    if (!startTimeInput.trim()) {
      setError('Vui lòng nhập mốc thời gian bắt đầu can thiệp (VD: 3 hoặc 2024-Q3).');
      return;
    }

    const treatedList = treatedUnitsInput.split(',').map(s => s.trim()).filter(s => s.length > 0);
    if (treatedList.length === 0) {
      setError('Cần ít nhất một đơn vị can thiệp hợp lệ.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runSDIDAnalysis(surveyId, {
        unit_question_id: unitQId,
        time_question_id: timeQId,
        outcome_question_id: outcomeQId,
        treated_units: treatedList,
        treatment_start_time: isNaN(Number(startTimeInput)) ? startTimeInput : Number(startTimeInput),
        n_placebo_reps: placeboReps,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình SDID.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích SDID.');
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
              Doubly Weighted Panel Econometrics
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Arkhangelsky, Athey, Imbens &amp; Wager (AER, 2021)
            </span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Synthetic Difference-in-Differences (SDID)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Tổng hòa đột phá giữa Đối chứng Tổng hợp (SCM) và Khác biệt kép (DiD). Sử dụng trọng số đơn vị (ω) để tái tạo xu hướng song song hoàn hảo và trọng số thời gian (λ) để loại bỏ biến động vĩ mô theo thời gian.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Đơn vị khảo sát (Unit ID) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={unitQId}
            onChange={(e) => setUnitQId(e.target.value)}
          >
            <option value="">-- Chọn biến đơn vị (Vùng/Nhóm) --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Mốc thời gian / Đợt sóng (Time Wave) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
          >
            <option value="">-- Chọn mốc thời gian --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến kết quả đo lường (Outcome Y) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
          >
            <option value="">-- Chọn chỉ số kết quả số --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>
      </div>

      {/* Advanced Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Đơn vị can thiệp (Treated Units) *
          </label>
          <input
            type="text"
            placeholder="VD: Region_1, Region_2"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={treatedUnitsInput}
            onChange={(e) => setTreatedUnitsInput(e.target.value)}
          />
          <span className="text-[11px] text-slate-500 block mt-1">Cách nhau bởi dấu phẩy</span>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Thời điểm can thiệp (Start Time) *
          </label>
          <input
            type="text"
            placeholder="VD: 3 hoặc 2024-Q3"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={startTimeInput}
            onChange={(e) => setStartTimeInput(e.target.value)}
          />
          <span className="text-[11px] text-slate-500 block mt-1">Mốc bắt đầu giai đoạn hậu can thiệp</span>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Phạm vi dữ liệu (Scope)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
          >
            <option value="all">Toàn bộ phản hồi (All)</option>
            <option value="verified_clean">Chỉ phản hồi sạch đã kiểm định (Clean)</option>
          </select>
        </div>
      </div>

      {/* Action Button */}
      <div className="mt-5 flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang tối ưu hóa trọng số kép ω và λ...</span>
            </>
          ) : (
            <>
              <span>Ước lượng Tác động Can thiệp SDID</span>
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Tác động Nhân quả SDID (τ)</span>
              <span className="text-xl font-bold text-emerald-400 font-mono">
                {result.sdid_estimates?.tau_sdid?.toFixed(3)}
              </span>
              <span className="text-[11px] text-slate-500 block">
                SE: {result.sdid_estimates?.se_sdid?.toFixed(3)}
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Khoảng Tin cậy 95% CI</span>
              <span className="text-sm font-bold text-sky-400 font-mono mt-1 block">
                [{result.sdid_estimates?.ci_95_lower?.toFixed(3)}, {result.sdid_estimates?.ci_95_upper?.toFixed(3)}]
              </span>
              <span className="text-[11px] text-slate-500 block">
                p = {result.sdid_estimates?.p_value?.toFixed(4)}
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Đơn vị Can thiệp / Đối chứng</span>
              <span className="text-xl font-bold text-white font-mono">
                {result.sample_diagnostics?.n_treated_units} / {result.sample_diagnostics?.n_control_units}
              </span>
              <span className="text-[11px] text-slate-500 block">
                Tổng bản ghi: {result.sample_diagnostics?.total_panel_records}
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Kỳ Tiền / Hậu Can thiệp</span>
              <span className="text-xl font-bold text-purple-300 font-mono">
                T_pre: {result.sample_diagnostics?.t_pre_periods} | T_post: {result.sample_diagnostics?.t_post_periods}
              </span>
              <span className="text-[11px] text-slate-500 block">Mốc bắt đầu: {result.treatment_start_time}</span>
            </div>
          </div>

          {/* Model Comparison Grid */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-slate-200 mb-2">
              Đối chiếu Hiệu ứng Nhân quả giữa Các Trường phái (Estimator Comparison)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
              <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                <span className="text-slate-400 block font-sans">DiD Cổ điển (Unweighted):</span>
                <span className="text-lg font-bold text-slate-300 mt-1 block">
                  {result.comparison_estimates?.tau_did_unweighted?.toFixed(3)}
                </span>
                <span className="text-[11px] text-slate-500 font-sans block mt-0.5">Dễ chệch nếu vi phạm song song</span>
              </div>

              <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                <span className="text-slate-400 block font-sans">SCM Chuẩn (Không chỉnh dốc):</span>
                <span className="text-lg font-bold text-amber-400 mt-1 block">
                  {result.comparison_estimates?.tau_scm_standard?.toFixed(3)}
                </span>
                <span className="text-[11px] text-slate-500 font-sans block mt-0.5">Nhạy cảm với độ lệch chặn</span>
              </div>

              <div className="bg-emerald-950/20 p-3 rounded border border-emerald-500/30">
                <span className="text-emerald-300 block font-sans font-semibold">SDID Kép (Double Weighted):</span>
                <span className="text-lg font-bold text-emerald-400 mt-1 block">
                  {result.comparison_estimates?.tau_sdid_doubly_weighted?.toFixed(3)}
                </span>
                <span className="text-[11px] text-emerald-500/80 font-sans block mt-0.5">Tối ưu song song + khử biến thiên</span>
              </div>
            </div>
          </div>

          {/* Top Donor Weights Table */}
          {result.top_donor_weights && result.top_donor_weights.length > 0 && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2">
                Trọng số Đơn vị Đối chứng Đóng góp (Top Donor Pool Weights ω_i)
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
                {result.top_donor_weights.map((dw, idx) => (
                  <div key={idx} className="bg-slate-900/60 p-2 rounded border border-slate-800/80 flex justify-between items-center">
                    <span className="text-slate-300 truncate max-w-[110px]">{dw.unit}</span>
                    <span className="text-emerald-400 font-bold">{(dw.weight * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SVG Visualizations */}
          {result.svg_chart && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-hidden">
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-slate-200">
                  Báo cáo Phân tích Kinh tế lượng Chuẩn APA 7th &amp; Khuyến nghị Chính sách
                </h4>
                <button
                  onClick={copyToClipboard}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded transition flex items-center gap-1.5 cursor-pointer"
                >
                  {copiedNarrative ? (
                    <>
                      <span className="text-emerald-400 font-medium">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <span>Sao chép Báo cáo</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-slate-300 space-y-2 whitespace-pre-line leading-relaxed font-sans bg-slate-900/50 p-4 rounded-lg border border-slate-800/60">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
