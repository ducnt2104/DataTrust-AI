import React, { useState } from 'react';
import { api } from '../api/client';
import { SyntheticControlAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface SyntheticControlCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const SyntheticControlCard: React.FC<SyntheticControlCardProps> = ({
  surveyId,
  questions
}) => {
  const [unitQId, setUnitQId] = useState<string>('');
  const [periodQId, setPeriodQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatedUnitName, setTreatedUnitName] = useState<string>('');
  const [treatmentPeriodVal, setTreatmentPeriodVal] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SyntheticControlAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!unitQId) {
      setError('Vui lòng chọn câu hỏi định danh đơn vị / khu vực (Unit / Entity Identifier).');
      return;
    }
    if (!periodQId) {
      setError('Vui lòng chọn câu hỏi chuỗi thời gian / kỳ khảo sát (Period / Wave Variable).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả đầu ra (Outcome Variable Y).');
      return;
    }
    if (!treatedUnitName.trim()) {
      setError('Vui lòng nhập tên hoặc giá trị của đơn vị nhận can thiệp (Treated Unit).');
      return;
    }
    if (!treatmentPeriodVal.trim()) {
      setError('Vui lòng nhập thời điểm bắt đầu có hiệu lực can thiệp (Treatment Period T0).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      // Parse treatment period as number if possible
      const parsedPeriod = isNaN(Number(treatmentPeriodVal.trim()))
        ? treatmentPeriodVal.trim()
        : Number(treatmentPeriodVal.trim());

      const data = await api.runSyntheticControlAnalysis(surveyId, {
        unit_question_id: unitQId,
        period_question_id: periodQId,
        outcome_question_id: outcomeQId,
        treated_unit: treatedUnitName.trim(),
        treatment_period: parsedPeriod,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || `Lỗi ước lượng Synthetic Control: ${data.status}`);
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng mô hình Synthetic Control.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Econometric Causal Engine
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Comparative Case Studies
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Kiểm chứng Tổng hợp (Synthetic Control Method - SCM)
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Thiết kế đánh giá tác động chính sách / can thiệp trên dữ liệu khảo sát lặp/chuỗi thời gian theo phương pháp luận chuẩn mực của{' '}
            <strong className="text-slate-200">Abadie & Gardeazabal (2003)</strong>,{' '}
            <strong className="text-slate-200">Abadie, Diamond & Hainmueller (2010)</strong> và{' '}
            <strong className="text-slate-200">Abadie (2021)</strong>. Tự động tối ưu hóa tổ hợp lồi các đơn vị đối chứng ($W \ge 0, \sum W_j = 1$) và kiểm định hoán vị không gian (In-Space Placebo Permutation Test).
          </p>
        </div>
      </div>

      {/* Control Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 my-6">
        {/* Unit Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            1. Đơn vị / Khu vực (Unit Identifier) <span className="text-rose-400">*</span>
          </label>
          <select
            value={unitQId}
            onChange={(e) => setUnitQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi phân loại đơn vị --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Period Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            2. Kỳ khảo sát / Chuỗi thời gian <span className="text-rose-400">*</span>
          </label>
          <select
            value={periodQId}
            onChange={(e) => setPeriodQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi kỳ/thời gian --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            3. Biến kết quả (Outcome Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến kết quả số --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Treated Unit Name & Period */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            4. Đơn vị can thiệp (Treated Unit) <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            value={treatedUnitName}
            onChange={(e) => setTreatedUnitName(e.target.value)}
            placeholder="Ví dụ: Region_A hoặc Chi nhánh 1"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Treatment Period */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            5. Kỳ bắt đầu can thiệp (T0) <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            value={treatmentPeriodVal}
            onChange={(e) => setTreatmentPeriodVal(e.target.value)}
            placeholder="Ví dụ: 4 hoặc Wave 4"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Scope & Action Button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-slate-800/40 border border-slate-700/60 rounded-lg mb-6">
        <div className="flex items-center gap-4 text-xs">
          <span className="text-slate-300 font-medium">Bộ lọc dữ liệu:</span>
          <label className="inline-flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="radio"
              name="scm-scope"
              checked={scope === 'all'}
              onChange={() => setScope('all')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            Toàn bộ phản hồi
          </label>
          <label className="inline-flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="radio"
              name="scm-scope"
              checked={scope === 'verified_clean'}
              onChange={() => setScope('verified_clean')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            Chỉ phản hồi sạch (Verified Clean $\ge$ 0.70)
          </label>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg shadow-lg hover:shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Đang giải quy hoạch lồi SCM & Placebo...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Ước lượng Tác động Kiểm chứng Tổng hợp</span>
            </>
          )}
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 mb-6 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-sm flex items-start gap-2">
          <svg className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>{error}</div>
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6">
          {/* Key Metrics Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Tác động Trung bình ATT</span>
              <p className={`text-xl font-bold mt-1 ${Number(result.att_effect) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {Number(result.att_effect) >= 0 ? `+${result.att_effect}` : result.att_effect}
              </p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Hậu can thiệp (Post-T0)</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Sai số Khớp Pre (RMSPE)</span>
              <p className="text-xl font-bold text-sky-400 mt-1">{result.rmspe_pre}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Pre-intervention fit</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Sai số Hậu Can thiệp</span>
              <p className="text-xl font-bold text-indigo-400 mt-1">{result.rmspe_post}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Post-intervention RMSPE</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Tỷ số RMSPE Ratio</span>
              <p className="text-xl font-bold text-amber-400 mt-1">{result.rmspe_ratio}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Post / Pre Error</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Kiểm định Placebo (p)</span>
              <p className={`text-xl font-bold mt-1 ${result.is_significant ? 'text-emerald-400' : 'text-slate-300'}`}>
                p = {result.empirical_p_value}
              </p>
              <span className={`text-[10px] font-medium block mt-0.5 ${result.is_significant ? 'text-emerald-300' : 'text-slate-400'}`}>
                {result.is_significant ? 'Ý nghĩa (p < .05)' : 'Không có ý nghĩa'}
              </span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Số Đơn vị Đối chứng</span>
              <p className="text-xl font-bold text-purple-400 mt-1">{result.donor_pool_count}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Valid Donors Pool</span>
            </div>
          </div>

          {/* Dual Panel SVG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-800/50 border border-slate-700/80 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">
                Trực quan hóa Diễn tiến Đối chứng Tổng hợp & Kiểm định Hoán vị Placebo
              </h3>
              <div
                className="overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Donor Weights Table & Pre-treatment Balance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Donor Weights */}
            <div className="bg-slate-800/40 border border-slate-700/70 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Trọng số Đơn vị Đối chứng Tối ưu ($W_j \ge 0, \sum W_j = 1$)
              </h4>
              <div className="overflow-x-auto max-h-60 overflow-y-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="text-[11px] text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700">
                    <tr>
                      <th className="py-2 px-3">Đơn vị Đối chứng</th>
                      <th className="py-2 px-3 text-right">Trọng số ($w_j$)</th>
                      <th className="py-2 px-3 text-right">Đóng góp (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {result.top_donor_weights && result.top_donor_weights.map((dw, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 font-medium text-slate-200">{dw.donor_name}</td>
                        <td className="py-2 px-3 text-right font-mono text-sky-300">{dw.weight}</td>
                        <td className="py-2 px-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <span className="font-mono text-slate-200">{dw.weight_percentage}%</span>
                            <div className="w-14 bg-slate-700 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-indigo-500 h-1.5 rounded-full"
                                style={{ width: `${Math.min(100, dw.weight_percentage)}%` }}
                              ></div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pre-treatment Balance Table */}
            <div className="bg-slate-800/40 border border-slate-700/70 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Cân bằng Tiền Can thiệp (Pre-Intervention Balance)
              </h4>
              <div className="overflow-x-auto max-h-60 overflow-y-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="text-[11px] text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700">
                    <tr>
                      <th className="py-2 px-3">Kỳ (Period)</th>
                      <th className="py-2 px-3 text-right">Thực tế ($Y_1$)</th>
                      <th className="py-2 px-3 text-right">Synthetic</th>
                      <th className="py-2 px-3 text-right">Donor Mean</th>
                      <th className="py-2 px-3 text-right">Chênh lệch</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {result.balance_table && result.balance_table.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 font-medium text-slate-200">{row.period}</td>
                        <td className="py-2 px-3 text-right font-mono">{row.treated_value}</td>
                        <td className="py-2 px-3 text-right font-mono text-sky-300">{row.synthetic_value}</td>
                        <td className="py-2 px-3 text-right font-mono text-slate-400">{row.donor_mean_value}</td>
                        <td className={`py-2 px-3 text-right font-mono ${Math.abs(row.difference) < 0.5 ? 'text-emerald-400' : 'text-amber-400'}`}>
                          {row.difference > 0 ? `+${row.difference}` : row.difference}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Trajectory Table */}
          <div className="bg-slate-800/40 border border-slate-700/70 rounded-lg p-4">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Chi tiết Diễn tiến Toàn chuỗi Thời gian (Trajectory & Effect Gaps)
            </h4>
            <div className="overflow-x-auto max-h-60 overflow-y-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="text-[11px] text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700">
                  <tr>
                    <th className="py-2 px-3">Kỳ khảo sát</th>
                    <th className="py-2 px-3">Giai đoạn</th>
                    <th className="py-2 px-3 text-right">Thực tế ({result.treated_unit})</th>
                    <th className="py-2 px-3 text-right">Synthetic Control</th>
                    <th className="py-2 px-3 text-right">Khoảng cách Tác động (Gap)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.trajectory && result.trajectory.map((tp, idx) => (
                    <tr key={idx} className={tp.is_post_treatment ? 'bg-indigo-950/20' : 'hover:bg-slate-800/40'}>
                      <td className="py-2 px-3 font-medium text-slate-200">{tp.period}</td>
                      <td className="py-2 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tp.is_post_treatment ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-700 text-slate-300'}`}>
                          {tp.is_post_treatment ? 'Hậu can thiệp (Post)' : 'Tiền can thiệp (Pre)'}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right font-mono font-medium text-white">{tp.actual_treated}</td>
                      <td className="py-2 px-3 text-right font-mono text-sky-300">{tp.synthetic_control}</td>
                      <td className={`py-2 px-3 text-right font-mono font-semibold ${tp.gap >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {tp.gap > 0 ? `+${tp.gap}` : tp.gap}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Edition Academic Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-lg p-5">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-700">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded border border-slate-600 transition-colors flex items-center gap-1.5"
                >
                  {copiedNarrative ? (
                    <>
                      <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-emerald-300">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>Sao chép APA</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed italic bg-slate-900/50 p-4 rounded border border-slate-800">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
