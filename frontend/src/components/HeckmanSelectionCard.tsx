import React, { useState } from 'react';
import {
  Filter,
  GitPullRequest,
  Scale,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  Sparkles,
  RefreshCw,
  Info,
  CheckSquare,
  Square
} from 'lucide-react';
import { api } from '../api/client';
import { HeckmanSelectionResult } from '../types/survey';

interface HeckmanSelectionCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const HeckmanSelectionCard: React.FC<HeckmanSelectionCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HeckmanSelectionResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [selectionQid, setSelectionQid] = useState<string>('');
  const [covariateQids, setCovariateQids] = useState<string[]>([]);
  const [exclusionQids, setExclusionQids] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'comparison' | 'svg'>('comparison');

  const toggleCovariate = (qid: string) => {
    setCovariateQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const toggleExclusion = (qid: string) => {
    setExclusionQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!outcomeQid) {
      setError('Vui lòng chọn biến kết quả có điều kiện (Outcome Y).');
      return;
    }
    if (covariateQids.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến giải thích (Outcome Covariates).');
      return;
    }
    if (covariateQids.includes(outcomeQid)) {
      setError('Biến kết quả không được nằm trong danh sách biến giải thích.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runHeckmanSelection(surveyId, {
        outcome_question_id: outcomeQid,
        selection_indicator_question_id: selectionQid || undefined,
        outcome_covariate_question_ids: covariateQids,
        exclusion_restriction_question_ids: exclusionQids.length > 0 ? exclusionQids : undefined,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình chọn mẫu Heckman.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API Heckman Selection.');
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400">
            <Filter className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Heckman Two-Step Sample Selection Correction
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Heckman (1979) · Nobel 2000
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Khử Thiên Lệch Chọn Mẫu Phi Ngẫu Nhiên &amp; Mất Dấu Khảo Sát qua Tỷ Số Nghịch Đảo Mills (IMR λ) &amp; Sai Số Chuẩn Greene
            </p>
          </div>
        </div>
      </div>

      {/* Config Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6">
        {/* Outcome & Selection Variable Selector */}
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
                1. Biến Kết Quả Bị Khuyết / Chọn Lọc (Outcome Y)
              </label>
              <select
                value={outcomeQid}
                onChange={(e) => setOutcomeQid(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">-- Chọn câu hỏi kết quả (e.g. Thu nhập, Đánh giá chi tiết) --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
                2. Chỉ Báo Tham Gia (Selection Indicator S, Tùy chọn)
              </label>
              <select
                value={selectionQid}
                onChange={(e) => setSelectionQid(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">-- Tự động xác định theo trạng thái điền/trống của Y --</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Covariates in Outcome Equation */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
              3. Các Biến Giải Thích Trong Phương Trình Kết Quả (Outcome Covariates X)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
              {questions.map((q) => {
                const isSelected = covariateQids.includes(q.id);
                const isOutcome = q.id === outcomeQid;
                return (
                  <button
                    key={q.id}
                    type="button"
                    disabled={isOutcome}
                    onClick={() => toggleCovariate(q.id)}
                    className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition ${
                      isOutcome
                        ? 'opacity-40 cursor-not-allowed text-slate-500'
                        : isSelected
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-300'
                        : 'hover:bg-slate-800/80 text-slate-300'
                    }`}
                  >
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    )}
                    <span className="truncate">{q.title}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Exclusion Restrictions */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
              4. Biến Ràng Buộc Loại Trừ (Exclusion Restrictions Z_excl - Chỉ ảnh hưởng Chọn mẫu)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-36 overflow-y-auto p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
              {questions.map((q) => {
                const isSelected = exclusionQids.includes(q.id);
                const isOutcome = q.id === outcomeQid;
                const isCovariate = covariateQids.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    disabled={isOutcome || isCovariate}
                    onClick={() => toggleExclusion(q.id)}
                    className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition ${
                      isOutcome || isCovariate
                        ? 'opacity-40 cursor-not-allowed text-slate-500'
                        : isSelected
                        ? 'bg-indigo-500/20 border border-indigo-500/40 text-indigo-300'
                        : 'hover:bg-slate-800/80 text-slate-300'
                    }`}
                  >
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    )}
                    <span className="truncate">{q.title}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Execution & Scope */}
        <div className="space-y-4 bg-slate-800/40 border border-slate-800 p-4 rounded-xl">
          <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-400 space-y-1.5">
            <span className="font-semibold text-slate-200 block">Quy chuẩn Loại trừ (Exclusion Restriction):</span>
            <p className="text-[11px] leading-relaxed">
              Theo Wooldridge (2010), việc có ít nhất 1 biến ràng buộc loại trừ Z giúp tránh hiện tượng đa cộng tuyến nghiêm trọng giữa Inverse Mills Ratio λ và các biến X.
            </p>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Phạm vi khảo sát</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  scope === 'all'
                    ? 'bg-amber-600/20 border-amber-500 text-amber-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                Tất cả (All)
              </button>
              <button
                type="button"
                onClick={() => setScope('verified_clean')}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  scope === 'verified_clean'
                    ? 'bg-emerald-600/20 border-emerald-500 text-emerald-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                Đã làm sạch
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleRun}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Đang khử thiên lệch chọn mẫu...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Ước lượng Heckman Two-Step
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mt-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && result.diagnostics && (
        <div className="mt-8 space-y-6 pt-6 border-t border-slate-800">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Hệ số IMR (β_λ)</span>
              <span className="text-base font-bold text-amber-400 mt-1 block">
                {result.diagnostics.inverse_mills_ratio_coef >= 0 ? `+${result.diagnostics.inverse_mills_ratio_coef.toFixed(3)}` : result.diagnostics.inverse_mills_ratio_coef.toFixed(3)}
              </span>
              <span className="text-[9px] text-slate-500">t = {result.diagnostics.imr_t_statistic.toFixed(2)}</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Tương Quan Sai Số (ρ)</span>
              <span className="text-base font-bold text-sky-400 mt-1 block">
                {result.diagnostics.rho_correlation.toFixed(3)}
              </span>
              <span className="text-[9px] text-slate-500">Corr(u, e)</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Kiểm Định Thiên Lệch</span>
              <span className={`text-base font-bold mt-1 block ${result.diagnostics.has_selection_bias ? 'text-rose-400' : 'text-emerald-400'}`}>
                p = {result.diagnostics.imr_p_value.toFixed(4)}
              </span>
              <span className="text-[9px] text-slate-500">
                {result.diagnostics.has_selection_bias ? 'Có thiên lệch chọn mẫu' : 'Không có thiên lệch'}
              </span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Mẫu Quan Sát (N_1)</span>
              <span className="text-base font-bold text-emerald-400 mt-1 block">
                {result.diagnostics.n_selected_observed} / {result.diagnostics.n_total_observations}
              </span>
              <span className="text-[9px] text-slate-500">Tỷ lệ: {result.diagnostics.selection_rate_pct.toFixed(1)}%</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Ràng Buộc Loại Trừ</span>
              <span className={`text-base font-bold mt-1 block ${result.diagnostics.has_valid_exclusion ? 'text-emerald-400' : 'text-amber-400'}`}>
                {result.diagnostics.exclusion_restrictions.length} biến Z
              </span>
              <span className="text-[9px] text-slate-500">{result.diagnostics.has_valid_exclusion ? 'Đạt chuẩn nhận dạng' : 'Chỉ nhận dạng dạng hàm'}</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Kết Luận Học Thuật</span>
              <span className="text-xs font-bold text-slate-200 mt-1 block truncate">
                {result.diagnostics.selection_verdict}
              </span>
              <span className="text-[9px] text-slate-500">Heckman Two-Step</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'comparison'
                  ? 'bg-amber-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Đối Chiếu Naive OLS vs Heckman (Khử Thiên Lệch)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'svg'
                  ? 'bg-amber-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Đồ Thị Vector SVG (Đường Cong Mills &amp; Forest Plot)
            </button>
          </div>

          {/* Table Tab */}
          {activeTab === 'comparison' && result.coefficients_comparison && (
            <div className="bg-slate-800/40 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4">Biến số</th>
                    <th className="py-2.5 px-4">Naive OLS (Có thiên lệch)</th>
                    <th className="py-2.5 px-4">Heckman (Đã hiệu chỉnh)</th>
                    <th className="py-2.5 px-4">Greene SE</th>
                    <th className="py-2.5 px-4">z-stat</th>
                    <th className="py-2.5 px-4">p-value</th>
                    <th className="py-2.5 px-4">Khoảng Lệch Thiên Lệch (Δ)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.coefficients_comparison.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 font-semibold text-white">
                        {c.variable}
                        {c.is_intercept && <span className="ml-2 text-[10px] text-slate-500 font-normal">(Base)</span>}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-400">
                        {c.ols_estimate.toFixed(4)} <span className="text-[10px] text-slate-600">(±{c.ols_se.toFixed(3)})</span>
                      </td>
                      <td className={`py-2.5 px-4 font-bold ${c.heckman_estimate >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {c.heckman_estimate >= 0 ? `+${c.heckman_estimate.toFixed(4)}` : c.heckman_estimate.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-4 text-slate-300 font-mono">{c.heckman_se.toFixed(4)}</td>
                      <td className="py-2.5 px-4 text-slate-300 font-mono">{c.z_statistic.toFixed(2)}</td>
                      <td className={`py-2.5 px-4 font-bold ${c.is_significant ? 'text-amber-400' : 'text-slate-400'}`}>
                        {c.p_value < 0.001 ? '<0.001' : c.p_value.toFixed(4)}
                        {c.is_significant && <span className="ml-1 text-emerald-400 font-black">***</span>}
                      </td>
                      <td className={`py-2.5 px-4 font-bold ${Math.abs(c.selection_bias_gap) > 0.1 ? 'text-rose-400' : 'text-slate-400'}`}>
                        {c.selection_bias_gap >= 0 ? `+${c.selection_bias_gap.toFixed(4)}` : c.selection_bias_gap.toFixed(4)}
                        {Math.abs(c.selection_bias_gap) > 0.1 && (
                          <span className="block text-[9px] text-rose-500 font-normal">Thiên lệch đáng kể</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* SVG Tab */}
          {activeTab === 'svg' && result.svg_visualization && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl overflow-x-auto">
              <div
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                className="w-full flex justify-center"
              />
            </div>
          )}

          {/* APA 7th Academic Narrative */}
          {result.apa_narrative && (
            <div className="p-5 bg-slate-800/30 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Info className="w-4 h-4 text-amber-400" />
                  Báo cáo Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyNarrative}
                  className="inline-flex items-center gap-1.5 px-3 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép APA</span>
                    </>
                  )}
                </button>
              </div>

              <div className="text-xs text-slate-300 leading-relaxed space-y-2 whitespace-pre-line font-serif italic bg-slate-900/60 p-4 rounded-lg border border-slate-800/60">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
