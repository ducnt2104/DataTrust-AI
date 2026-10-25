import React, { useState } from 'react';
import {
  SlidersHorizontal,
  Coins,
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  TrendingUp,
  Percent,
  CheckSquare
} from 'lucide-react';
import { api } from '../api/client';
import { ConjointChoiceResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const ConjointChoiceCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [choiceQid, setChoiceQid] = useState<string>('');
  const [selectedAttrQids, setSelectedAttrQids] = useState<string[]>([]);
  const [priceQid, setPriceQid] = useState<string>('');
  const [priceUnit, setPriceUnit] = useState<string>('mil VND');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ConjointChoiceResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'utilities' | 'wtp'>('utilities');

  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'single_choice'].includes(q.question_type)
  );

  const toggleAttribute = (qid: string) => {
    setSelectedAttrQids((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!choiceQid) {
      setError('Vui lòng chọn biến Chỉ Báo Lựa Chọn (Choice Indicator - 1/0).');
      return;
    }
    if (selectedAttrQids.length === 0) {
      setError('Vui lòng chọn ít nhất 1 thuộc tính sản phẩm/hồ sơ (Attributes).');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.runConjointChoice(surveyId, {
        choice_question_id: choiceQid,
        attribute_question_ids: selectedAttrQids,
        price_question_id: priceQid || undefined,
        price_unit: priceUnit,
        scope
      });
      if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Mẫu khảo sát không đủ điều kiện để ước lượng mô hình Conjoint Choice.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích Conjoint Choice.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-8 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute -top-24 -right-24 w-80 h-80 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 rounded-xl text-emerald-400">
              <SlidersHorizontal className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Phân Tích Kết Hợp &amp; Lựa Chọn Rời Rạc (Conjoint Choice / DCE)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium">
                  McFadden (1974) &amp; Train (2009)
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Ước lượng Độ hữu dụng từng phần (Part-Worth Utilities), Tầm quan trọng tương đối &amp; Độ sẵn sàng chi trả (WTP)
              </p>
            </div>
          </div>
        </div>

        {/* Scope Selector */}
        <div className="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 self-start md:self-auto">
          <button
            onClick={() => setScope('all')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              scope === 'all'
                ? 'bg-emerald-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Toàn bộ mẫu
          </button>
          <button
            onClick={() => setScope('verified_clean')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              scope === 'verified_clean'
                ? 'bg-teal-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Mẫu sạch đã kiểm duyệt
          </button>
        </div>
      </div>

      {/* Configuration Section */}
      <div className="mt-6 space-y-5 bg-slate-950/40 p-5 rounded-xl border border-slate-800/60">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Choice Question */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 block">
              Biến Chỉ Báo Lựa Chọn (Choice Indicator - 1 = Chọn, 0 = Bỏ qua):
            </label>
            <select
              value={choiceQid}
              onChange={(e) => setChoiceQid(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-emerald-500"
            >
              <option value="">-- Chọn câu hỏi chỉ báo lựa chọn --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Price Question (Optional) */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Biến Giá Cả / Chi Phí (Tùy chọn - để tính WTP):</span>
              <span className="text-[11px] text-slate-500 lowercase">Willingness-to-pay</span>
            </label>
            <div className="flex gap-2">
              <select
                value={priceQid}
                onChange={(e) => setPriceQid(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-emerald-500"
              >
                <option value="">-- Tự động nhận diện hoặc không tính WTP --</option>
                {eligibleQuestions
                  .filter((q) => q.id !== choiceQid)
                  .map((q) => (
                    <option key={q.id} value={q.id}>
                      {q.title}
                    </option>
                  ))}
              </select>
              <input
                type="text"
                placeholder="Đơn vị tiền (VND...)"
                value={priceUnit}
                onChange={(e) => setPriceUnit(e.target.value)}
                className="w-28 bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-emerald-500 text-center"
              />
            </div>
          </div>
        </div>

        {/* Attributes Multi-Select */}
        <div>
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Chọn các thuộc tính cấu thành sản phẩm/chính sách ({selectedAttrQids.length} đã chọn):</span>
            <span className="text-[11px] text-slate-500 lowercase">đánh giá mức độ quan trọng</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto pr-1">
            {eligibleQuestions
              .filter((q) => q.id !== choiceQid)
              .map((q) => {
                const isSelected = selectedAttrQids.includes(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => toggleAttribute(q.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border text-left flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-sm'
                        : 'bg-slate-800/50 text-slate-400 border-slate-700/50 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                    <span className="truncate max-w-[240px]">{q.title}</span>
                  </button>
                );
              })}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-3 border-t border-slate-800/60">
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !choiceQid || selectedAttrQids.length === 0}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-xs shadow-lg shadow-emerald-900/30 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Đang hồi quy McFadden MNL...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Phân Tích Conjoint Choice</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && (
        <div className="mt-6 space-y-6">
          {/* Top-line Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">McFadden Pseudo-R²</span>
              <span className="text-xl font-bold text-emerald-400 mt-1 block">
                {result.diagnostics?.mcfadden_pseudo_r2.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {result.diagnostics && result.diagnostics.mcfadden_pseudo_r2 >= 0.4
                  ? 'Mô hình xuất sắc (> .40)'
                  : (result.diagnostics && result.diagnostics.mcfadden_pseudo_r2 >= 0.2 ? 'Mô hình tốt (> .20)' : 'Mô hình chấp nhận được')}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Tổng Lựa Chọn Quan Sát (N)</span>
              <span className="text-xl font-bold text-teal-400 mt-1 block">
                {result.diagnostics?.N}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {result.diagnostics?.n_chosen} Chọn vs {result.diagnostics?.n_rejected} Bỏ qua
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Số Thuộc Tính Đánh Giá</span>
              <span className="text-xl font-bold text-cyan-400 mt-1 block">
                {result.diagnostics?.n_attributes}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Log-Likelihood: {result.diagnostics?.log_likelihood.toFixed(1)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Thuộc Tính Quan Trọng Nhất</span>
              <span className="text-sm font-bold text-violet-400 mt-1 block truncate">
                {result.part_worth_utilities && result.part_worth_utilities.length > 0
                  ? result.part_worth_utilities[0].attribute
                  : 'Không có'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Chiếm {result.part_worth_utilities && result.part_worth_utilities.length > 0
                  ? `${result.part_worth_utilities[0].relative_importance_pct.toFixed(1)}%`
                  : '0%'} tầm quan trọng
              </span>
            </div>
          </div>

          {/* SVG Visual Canvas */}
          {result.svg_visualization && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 overflow-hidden shadow-inner">
              <div
                className="w-full h-auto overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Details Tables with Navigation Tabs */}
          <div className="bg-slate-950/60 rounded-xl border border-slate-800 overflow-hidden">
            <div className="flex border-b border-slate-800 bg-slate-900/60 px-4 pt-2 gap-2">
              <button
                onClick={() => setActiveTab('utilities')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'utilities'
                    ? 'border-emerald-400 text-emerald-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Độ Hữu Dụng Từng Phần (Part-Worth Utilities)
              </button>
              <button
                onClick={() => setActiveTab('wtp')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'wtp'
                    ? 'border-emerald-400 text-emerald-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Sẵn Sàng Chi Trả WTP ({result.willingness_to_pay?.length || 0})
              </button>
            </div>

            <div className="p-4 overflow-x-auto">
              {activeTab === 'utilities' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Thuộc Tính Sản Phẩm / Dịch Vụ</th>
                      <th className="py-2.5 px-3 text-right">Hệ Số Hữu Dụng (β)</th>
                      <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                      <th className="py-2.5 px-3 text-right">t-stat</th>
                      <th className="py-2.5 px-3 text-right">p-value</th>
                      <th className="py-2.5 px-3 text-right">Khoảng Tin Cậy 95% CI</th>
                      <th className="py-2.5 px-3 text-right">Tầm Quan Trọng (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.part_worth_utilities?.map((pw, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{pw.attribute}</td>
                        <td className={`py-2.5 px-3 text-right font-mono font-bold ${pw.part_worth_utility >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {pw.part_worth_utility >= 0 ? `+${pw.part_worth_utility.toFixed(3)}` : pw.part_worth_utility.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{pw.se.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{pw.t_stat.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{pw.p_value < 0.001 ? '< .001' : pw.p_value.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                          [{pw.ci_95_lower.toFixed(2)}, {pw.ci_95_upper.toFixed(2)}]
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-violet-400">
                          {pw.relative_importance_pct.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'wtp' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Thuộc Tính</th>
                      <th className="py-2.5 px-3 text-right">Độ Sẵn Sàng Chi Trả (WTP)</th>
                      <th className="py-2.5 px-3 text-right">Sai Số Chuẩn Delta</th>
                      <th className="py-2.5 px-3 text-right">Khoảng Tin Cậy 95% CI</th>
                      <th className="py-2.5 px-3 text-center">Đơn Vị Tiền</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.willingness_to_pay && result.willingness_to_pay.length > 0 ? (
                      result.willingness_to_pay.map((w, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-2.5 px-3 font-medium text-slate-200">{w.attribute}</td>
                          <td className={`py-2.5 px-3 text-right font-mono font-bold ${w.wtp_estimate >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {w.wtp_estimate >= 0 ? `+${w.wtp_estimate.toFixed(2)}` : w.wtp_estimate.toFixed(2)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono text-slate-400">{w.wtp_se.toFixed(2)}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                            [{w.wtp_ci_lower.toFixed(2)}, {w.wtp_ci_upper.toFixed(2)}]
                          </td>
                          <td className="py-2.5 px-3 text-center text-slate-400 font-medium">{w.unit}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-4 text-center text-slate-500">
                          Chưa cấu hình biến giá cả để tính định giá Willingness-To-Pay.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Academic Manuscript Narrative (APA 7th) */}
          {result.apa_narrative && (
            <div className="bg-slate-950/80 p-5 rounded-xl border border-slate-800 relative">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                    Thuyết Minh Học Thuật (APA 7th Edition)
                  </span>
                </div>
                <button
                  onClick={handleCopyNarrative}
                  className="flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/60 p-4 rounded-lg border border-slate-800/80">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
