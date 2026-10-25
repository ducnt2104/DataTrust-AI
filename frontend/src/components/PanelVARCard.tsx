import React, { useState } from 'react';
import { api } from '../api/client';
import { PanelVARResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface PanelVARCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const PanelVARCard: React.FC<PanelVARCardProps> = ({
  surveyId,
  questions
}) => {
  const [unitQId, setUnitQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [var1QId, setVar1QId] = useState<string>('');
  const [var2QId, setVar2QId] = useState<string>('');
  const [lags, setLags] = useState<number>(1);
  const [horizons, setHorizons] = useState<number>(6);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PanelVARResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!unitQId) {
      setError('Vui lòng chọn câu hỏi định danh đơn vị bảng (Panel Unit / Entity ID).');
      return;
    }
    if (!timeQId) {
      setError('Vui lòng chọn câu hỏi mốc thời gian / kỳ khảo sát (Time / Wave Question).');
      return;
    }
    if (!var1QId) {
      setError('Vui lòng chọn biến nội sinh thứ nhất (Variable 1).');
      return;
    }
    if (!var2QId) {
      setError('Vui lòng chọn biến nội sinh thứ hai (Variable 2).');
      return;
    }
    if (var1QId === var2QId) {
      setError('Hai biến nội sinh trong hệ thống Panel VAR phải khác nhau.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await api.runPanelVARAnalysis(surveyId, {
        unit_question_id: unitQId,
        time_question_id: timeQId,
        var1_question_id: var1QId,
        var2_question_id: var2QId,
        lags,
        irf_horizons: horizons,
        scope
      });

      setResult(res);
      if (res.status === 'insufficient_data' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không đủ dữ liệu bảng lặp qua các mốc thời gian để ước lượng Panel VAR.');
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích Panel VAR.');
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
      <div className="border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2">
          <span className="p-2 bg-teal-50 text-teal-600 rounded-lg font-bold text-sm">
            PVAR
          </span>
          <div>
            <h3 className="text-lg font-bold text-slate-800">
              Panel Vector Autoregression (Panel VAR) & Granger Causality
            </h3>
            <p className="text-xs text-slate-500">
              Ước lượng Tự hồi quy Vector Dữ liệu Bảng (Panel VAR) triệt tiêu hiệu ứng cố định qua biến đổi trực giao Helmert, kiểm định nhân quả động Granger & hàm phản ứng đẩy OIRF (Holtz-Eakin et al., 1988; Abrigo & Love, 2016).
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Panel Unit */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Đơn vị bảng (Entity ID)
          </label>
          <select
            value={unitQId}
            onChange={e => setUnitQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">-- Chọn đơn vị bảng --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Time / Wave */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Mốc thời gian / Đợt (Time)
          </label>
          <select
            value={timeQId}
            onChange={e => setTimeQId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">-- Chọn mốc thời gian --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Endogenous Variable 1 */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến nội sinh 1 (Variable 1)
          </label>
          <select
            value={var1QId}
            onChange={e => setVar1QId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">-- Chọn biến 1 --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Endogenous Variable 2 */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến nội sinh 2 (Variable 2)
          </label>
          <select
            value={var2QId}
            onChange={e => setVar2QId(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">-- Chọn biến 2 --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Scope, Lag, and Action Button */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-1">
        <div className="flex items-center gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-1.5">
            <span>Bậc trễ (Lags):</span>
            <input
              type="number"
              min="1"
              max="3"
              value={lags}
              onChange={e => setLags(parseInt(e.target.value) || 1)}
              className="w-14 text-xs border border-slate-200 rounded-md px-2 py-1 bg-slate-50 focus:bg-white"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span>Số kỳ phản ứng (IRF Horizons):</span>
            <input
              type="number"
              min="2"
              max="12"
              value={horizons}
              onChange={e => setHorizons(parseInt(e.target.value) || 6)}
              className="w-14 text-xs border border-slate-200 rounded-md px-2 py-1 bg-slate-50 focus:bg-white"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span>Phạm vi:</span>
            <select
              value={scope}
              onChange={e => setScope(e.target.value as 'all' | 'verified_clean')}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1 bg-slate-50 focus:bg-white"
            >
              <option value="all">Toàn bộ mẫu khảo sát</option>
              <option value="verified_clean">Chỉ mẫu đã kiểm định hợp lệ</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="w-full md:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm rounded-lg transition-colors shadow-sm disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Đang tính toán Panel VAR & Granger...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              <span>Ước lượng Động học Panel VAR</span>
            </>
          )}
        </button>
      </div>

      {/* Error notification */}
      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
          <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Causality Conclusion Banner */}
          {result.causality_conclusion && (
            <div className="p-4 rounded-xl border bg-teal-50/70 border-teal-200 text-teal-900 flex items-start gap-3">
              <div className="p-1.5 bg-teal-200 text-teal-800 rounded-lg font-bold text-xs uppercase">
                KẾT LUẬN NHÂN QUẢ ĐỘNG HỌC
              </div>
              <div className="text-xs font-semibold leading-relaxed">
                {result.causality_conclusion}
              </div>
            </div>
          )}

          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Độ ổn định Hệ động lực</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                |λ|_max = {result.stability_max_modulus?.toFixed(3) || '--'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  result.is_stable ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {result.is_stable ? 'Hệ thống ổn định (< 1.0)' : 'Hệ thống bùng nổ (≥ 1.0)'}
              </span>
            </div>

            <div className="p-4 bg-cyan-50/50 border border-cyan-200 rounded-xl">
              <span className="text-xs text-cyan-800 font-medium">Granger: {result.var1_name?.slice(0, 10)} → {result.var2_name?.slice(0, 10)}</span>
              <div className="text-xl font-bold text-cyan-700 mt-1">
                χ² = {result.granger_causality?.var1_causes_var2?.wald_chi2?.toFixed(2) || '--'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  result.granger_causality?.var1_causes_var2?.is_significant
                    ? 'text-emerald-600'
                    : 'text-slate-500'
                }`}
              >
                p = {result.granger_causality?.var1_causes_var2?.p_value?.toFixed(4)}{' '}
                {result.granger_causality?.var1_causes_var2?.is_significant ? '(Ý nghĩa)' : '(K.Ý nghĩa)'}
              </span>
            </div>

            <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl">
              <span className="text-xs text-emerald-800 font-medium">Granger: {result.var2_name?.slice(0, 10)} → {result.var1_name?.slice(0, 10)}</span>
              <div className="text-xl font-bold text-emerald-700 mt-1">
                χ² = {result.granger_causality?.var2_causes_var1?.wald_chi2?.toFixed(2) || '--'}
              </div>
              <span
                className={`text-[11px] font-semibold ${
                  result.granger_causality?.var2_causes_var1?.is_significant
                    ? 'text-emerald-600'
                    : 'text-slate-500'
                }`}
              >
                p = {result.granger_causality?.var2_causes_var1?.p_value?.toFixed(4)}{' '}
                {result.granger_causality?.var2_causes_var1?.is_significant ? '(Ý nghĩa)' : '(K.Ý nghĩa)'}
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs text-slate-500 font-medium">Cỡ mẫu & Đơn vị Bảng</span>
              <div className="text-xl font-bold text-slate-800 mt-1">
                {result.panel_units_count} đơn vị
              </div>
              <span className="text-[11px] text-slate-500">
                {result.effective_observations} quan sát hiệu dụng (Helmert)
              </span>
            </div>
          </div>

          {/* Dual-Panel SVG Chart */}
          {result.svg_chart && (
            <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Đồ thị Vector Động học Panel VAR & Sơ đồ Mạng lưới Granger
                </span>
                <span className="text-[11px] text-slate-400">
                  Panel A: Quỹ đạo Phản ứng Đẩy OIRF | Panel B: Mạng lưới tác động có hướng
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Dynamic Equations Table */}
          {result.equations && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Hệ Phương trình Tự hồi quy Động (Autoregressive System Equations)
              </span>
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Phương trình (Biến phụ thuộc)</th>
                      <th className="p-2.5">Hệ số trễ tự thân (Lag 1)</th>
                      <th className="p-2.5">Hệ số trễ biến chéo (Cross-Lag 1)</th>
                      <th className="p-2.5">Đóng góp phương sai FEVD (Bước 5)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr className="hover:bg-slate-50">
                      <td className="p-2.5 font-bold text-cyan-800">{result.var1_name}</td>
                      <td className="p-2.5 text-slate-700">
                        {result.equations.eq_var1.coeff_self_lag >= 0 ? '+' : ''}
                        {result.equations.eq_var1.coeff_self_lag.toFixed(3)} (SE ={' '}
                        {result.equations.eq_var1.se_self_lag.toFixed(3)})
                      </td>
                      <td className="p-2.5 font-bold text-cyan-700">
                        {result.equations.eq_var1.coeff_cross_lag >= 0 ? '+' : ''}
                        {result.equations.eq_var1.coeff_cross_lag.toFixed(3)} (SE ={' '}
                        {result.equations.eq_var1.se_cross_lag.toFixed(3)})
                      </td>
                      <td className="p-2.5 text-slate-600 font-medium">
                        {result.fevd_horizon_5?.var1_explained_by_var2_pct.toFixed(1)}% giải thích bởi {result.var2_name}
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="p-2.5 font-bold text-emerald-800">{result.var2_name}</td>
                      <td className="p-2.5 text-slate-700">
                        {result.equations.eq_var2.coeff_self_lag >= 0 ? '+' : ''}
                        {result.equations.eq_var2.coeff_self_lag.toFixed(3)} (SE ={' '}
                        {result.equations.eq_var2.se_self_lag.toFixed(3)})
                      </td>
                      <td className="p-2.5 font-bold text-emerald-700">
                        {result.equations.eq_var2.coeff_cross_lag >= 0 ? '+' : ''}
                        {result.equations.eq_var2.coeff_cross_lag.toFixed(3)} (SE ={' '}
                        {result.equations.eq_var2.se_cross_lag.toFixed(3)})
                      </td>
                      <td className="p-2.5 text-slate-600 font-medium">
                        {result.fevd_horizon_5?.var2_explained_by_var1_pct.toFixed(1)}% giải thích bởi {result.var1_name}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Tường trình Khoa học Tiêu chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                  <span>{copiedNarrative ? 'Đã sao chép!' : 'Sao chép APA'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic bg-white p-3 rounded-lg border border-slate-200">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
