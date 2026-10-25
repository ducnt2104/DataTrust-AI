import React, { useState } from 'react';
import {
  Percent,
  TrendingUp,
  BarChart2,
  ShieldCheck,
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
import { FractionalResponseResult } from '../types/survey';

interface FractionalResponseCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const FractionalResponseCard: React.FC<FractionalResponseCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FractionalResponseResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [covariateQids, setCovariateQids] = useState<string[]>([]);
  const [link, setLink] = useState<'logit' | 'probit' | 'cloglog'>('logit');
  const [scaleFromPct, setScaleFromPct] = useState<boolean>(true);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'coefficients' | 'svg'>('coefficients');

  const toggleCovariate = (qid: string) => {
    setCovariateQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!outcomeQid) {
      setError('Vui lòng chọn biến kết quả tỷ lệ/phần trăm (Outcome Rate).');
      return;
    }
    if (covariateQids.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến giải thích (Covariates).');
      return;
    }
    if (covariateQids.includes(outcomeQid)) {
      setError('Biến kết quả không được nằm trong danh sách biến giải thích.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runFractionalResponse(surveyId, {
        outcome_question_id: outcomeQid,
        covariate_question_ids: covariateQids,
        link,
        scale_from_percentage: scaleFromPct,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình Fractional Response.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API Fractional Response.');
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
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
            <Percent className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Fractional Response QMLE Regression
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Papke &amp; Wooldridge (1996, 2008)
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Hồi quy Biến Tỷ lệ &amp; Phần trăm Bị chặn [0, 1] với Sai số Chuẩn Vững Sandwich Huber-White &amp; Hiệu ứng Biên AME
            </p>
          </div>
        </div>
      </div>

      {/* Config Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6">
        {/* Outcome & Covariates Selection */}
        <div className="lg:col-span-2 space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
              1. Biến Kết Quả Tỷ Lệ / Phần Trăm Bị Chặn [0, 1] (Outcome Rate Y)
            </label>
            <select
              value={outcomeQid}
              onChange={(e) => setOutcomeQid(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="">-- Chọn câu hỏi tỷ lệ (e.g. % ngân sách, điểm chuẩn hóa, mức độ) --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
              2. Các Biến Giải Thích (Covariates X)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
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
                        ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300'
                        : 'hover:bg-slate-800/80 text-slate-300'
                    }`}
                  >
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-emerald-400 flex-shrink-0" />
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

        {/* Parameters & Execution */}
        <div className="space-y-4 bg-slate-800/40 border border-slate-800 p-4 rounded-xl">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
              Hàm Liên Kết (Link Function G)
            </label>
            <select
              value={link}
              onChange={(e) => setLink(e.target.value as any)}
              className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="logit">Logit Sigmoid: G(z) = 1 / (1 + e^-z)</option>
              <option value="probit">Probit Normal CDF: G(z) = Φ(z)</option>
              <option value="cloglog">Complementary Log-Log: G(z) = 1 - exp(-exp(z))</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-2.5 bg-slate-950/60 border border-slate-800 rounded-lg">
            <span className="text-xs text-slate-300">Tự động chuẩn hóa nếu &gt;1.0 (0-100%)</span>
            <input
              type="checkbox"
              checked={scaleFromPct}
              onChange={(e) => setScaleFromPct(e.target.checked)}
              className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500 border-slate-700 bg-slate-900"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Phạm vi khảo sát</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  scope === 'all'
                    ? 'bg-emerald-600/20 border-emerald-500 text-emerald-300'
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
            className="w-full py-2.5 px-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Đang tối ưu Quasi-Likelihood...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Ước lượng Fractional QMLE
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
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Pseudo-R² McFadden</span>
              <span className="text-base font-bold text-emerald-400 mt-1 block">
                {result.diagnostics.mcfadden_pseudo_r2.toFixed(4)}
              </span>
              <span className="text-[9px] text-slate-500">Mức độ giải thích tỷ lệ</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Cực trị Biên 0.0</span>
              <span className="text-base font-bold text-sky-400 mt-1 block">
                {result.diagnostics.boundary_zeros}
              </span>
              <span className="text-[9px] text-slate-500">Điểm mass point tại 0</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Cực trị Biên 1.0</span>
              <span className="text-base font-bold text-indigo-400 mt-1 block">
                {result.diagnostics.boundary_ones}
              </span>
              <span className="text-[9px] text-slate-500">Điểm mass point tại 1</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Lỗi Ngoài Biên OLS</span>
              <span className={`text-base font-bold mt-1 block ${result.diagnostics.ols_out_of_bounds_count > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
                {result.diagnostics.ols_out_of_bounds_count} vi phạm
              </span>
              <span className="text-[9px] text-slate-500">Dự báo OLS &lt;0 hoặc &gt;1</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Kiểm định RESET</span>
              <span className={`text-base font-bold mt-1 block ${result.diagnostics.reset_passed ? 'text-emerald-400' : 'text-amber-400'}`}>
                p = {result.diagnostics.reset_test_pval.toFixed(3)}
              </span>
              <span className="text-[9px] text-slate-500">{result.diagnostics.reset_passed ? 'Đạt dạng hàm' : 'Cần hàm bậc cao'}</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Cỡ mẫu (N)</span>
              <span className="text-base font-bold text-slate-200 mt-1 block">
                {result.diagnostics.n_samples}
              </span>
              <span className="text-[9px] text-slate-500">Quan sát đầy đủ</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('coefficients')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'coefficients'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Hệ số Hồi quy &amp; Hiệu ứng Biên (AME)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'svg'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Đồ thị Vector SVG (Sigmoid vs OLS)
            </button>
          </div>

          {/* Table Tab */}
          {activeTab === 'coefficients' && result.coefficients && (
            <div className="bg-slate-800/40 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4">Biến số</th>
                    <th className="py-2.5 px-4">Hệ số (β)</th>
                    <th className="py-2.5 px-4">Robust SE</th>
                    <th className="py-2.5 px-4">z-stat</th>
                    <th className="py-2.5 px-4">p-value</th>
                    <th className="py-2.5 px-4">95% CI</th>
                    <th className="py-2.5 px-4">Hiệu ứng Biên AME</th>
                    <th className="py-2.5 px-4">Hiệu ứng tại TB (MEM)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.coefficients.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 font-semibold text-white">
                        {c.variable}
                        {c.is_intercept && <span className="ml-2 text-[10px] text-slate-500 font-normal">(Base)</span>}
                      </td>
                      <td className={`py-2.5 px-4 font-bold ${c.estimate >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {c.estimate >= 0 ? `+${c.estimate.toFixed(4)}` : c.estimate.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-4 text-slate-300 font-mono">{c.robust_se.toFixed(4)}</td>
                      <td className="py-2.5 px-4 text-slate-300 font-mono">{c.z_statistic.toFixed(2)}</td>
                      <td className={`py-2.5 px-4 font-bold ${c.is_significant ? 'text-amber-400' : 'text-slate-400'}`}>
                        {c.p_value < 0.001 ? '<0.001' : c.p_value.toFixed(4)}
                        {c.is_significant && <span className="ml-1 text-emerald-400 font-black">***</span>}
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 font-mono text-[11px]">
                        [{c.ci_95_lower.toFixed(3)}, {c.ci_95_upper.toFixed(3)}]
                      </td>
                      <td className="py-2.5 px-4 font-bold text-sky-400">
                        {c.average_marginal_effect !== null && c.average_marginal_effect !== undefined ? (
                          <>
                            {c.average_marginal_effect >= 0 ? `+${c.average_marginal_effect.toFixed(4)}` : c.average_marginal_effect.toFixed(4)}
                            <span className="block text-[10px] text-slate-500 font-normal">
                              ({(c.average_marginal_effect * 100).toFixed(2)}% điểm)
                            </span>
                          </>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 text-purple-300 font-mono">
                        {c.marginal_effect_at_mean !== null && c.marginal_effect_at_mean !== undefined ? (
                          c.marginal_effect_at_mean.toFixed(4)
                        ) : (
                          <span className="text-slate-600">—</span>
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
                  <Info className="w-4 h-4 text-emerald-400" />
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
