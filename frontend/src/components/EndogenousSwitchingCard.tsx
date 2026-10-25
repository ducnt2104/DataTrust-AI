import React, { useState } from 'react';
import {
  ToggleLeft,
  ArrowRightLeft,
  Scale,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  Info,
  CheckSquare,
  Square,
  BarChart3,
  GitCompare,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import { EndogenousSwitchingResult } from '../types/survey';

interface EndogenousSwitchingCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const EndogenousSwitchingCard: React.FC<EndogenousSwitchingCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EndogenousSwitchingResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [covariateQids, setCovariateQids] = useState<string[]>([]);
  const [instrumentQids, setInstrumentQids] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'treatment_effects' | 'coefficients' | 'svg'>('treatment_effects');

  const toggleCovariate = (qid: string) => {
    setCovariateQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const toggleInstrument = (qid: string) => {
    setInstrumentQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!treatmentQid) {
      setError('Vui lòng chọn biến phân loại can thiệp nhị phân (Treatment I: 1=Có, 0=Không).');
      return;
    }
    if (!outcomeQid) {
      setError('Vui lòng chọn biến kết quả liên tục (Outcome Y: Thu nhập, năng suất, chi tiêu...).');
      return;
    }
    if (treatmentQid === outcomeQid) {
      setError('Biến can thiệp và biến kết quả không được trùng nhau.');
      return;
    }
    if (covariateQids.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến giải thích phương trình kết quả (Covariates X).');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runEndogenousSwitching(surveyId, {
        treatment_question_id: treatmentQid,
        outcome_question_id: outcomeQid,
        covariate_question_ids: covariateQids,
        instrument_question_ids: instrumentQids.length > 0 ? instrumentQids : undefined,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình Endogenous Switching Regression.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API Endogenous Switching Regression.');
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
          <div className="p-2 bg-teal-500/10 border border-teal-500/20 rounded-xl text-teal-400">
            <ArrowRightLeft className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Endogenous Switching Regression (ESR - FIML)
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
                Maddala (1983) · Lokshin &amp; Sajaia (2004)
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Phân rã tác động nhân quả phản thực tế (Counterfactual ATT &amp; ATU) có tự chọn lọc nội sinh; ước lượng đồng thời phương trình chọn lọc Probit và 2 phương trình kết quả riêng biệt theo chế độ (Regime 1 vs Regime 0).
            </p>
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-teal-600/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Đang tính FIML ESR...</span>
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4" />
              <span>Ước lượng Hồi Quy Chuyển Đổi</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 py-5 border-b border-slate-800 text-xs">
        {/* Treatment Question */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Biến Can Thiệp Nhị Phân (I ∈ &#123;0, 1&#125;):</label>
          <select
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500"
          >
            <option value="">-- Chọn biến can thiệp/áp dụng (I=1 vs I=0) --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title.length > 45 ? `${q.title.slice(0, 45)}...` : q.title}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400">Tham gia đào tạo, nhận trợ cấp, đổi mới công nghệ.</p>
        </div>

        {/* Outcome Question */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Biến Kết Quả Liên Tục (Outcome Y):</label>
          <select
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500"
          >
            <option value="">-- Chọn biến kết quả liên tục --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title.length > 45 ? `${q.title.slice(0, 45)}...` : q.title}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400">Thu nhập, sản lượng, điểm số thỏa dụng.</p>
        </div>

        {/* Scope */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Phạm vi Mẫu:</label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500"
          >
            <option value="all">Tất cả phản hồi hợp lệ</option>
            <option value="verified_clean">Chỉ mẫu đã xác thực sạch (Verified Clean)</option>
          </select>
          <p className="text-[11px] text-slate-400">Loại bỏ phản hồi bất thường nếu cần.</p>
        </div>

        {/* Info Tip */}
        <div className="space-y-1.5 bg-slate-800/30 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <Info className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
          <span>
            Theo Lokshin &amp; Sajaia (2004), hệ số tương quan <span className="text-teal-300 font-mono">ρ₁</span> và <span className="text-teal-300 font-mono">ρ₀</span> đo lường mức độ tự chọn lọc (self-selection bias) vào từng chế độ.
          </span>
        </div>
      </div>

      {/* Outcome Covariates Selection (X) */}
      <div className="py-4 border-b border-slate-800">
        <label className="font-medium text-xs text-slate-300 flex items-center justify-between mb-2">
          <span>Chọn Các Biến Giải Thích Trong Phương Trình Kết Quả (Covariates X):</span>
          <span className="text-slate-400 font-normal">Đã chọn: {covariateQids.length} biến</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto pr-1">
          {questions
            .filter((q) => q.id !== treatmentQid && q.id !== outcomeQid)
            .map((q) => {
              const isSelected = covariateQids.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleCovariate(q.id)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors cursor-pointer border ${
                    isSelected
                      ? 'bg-teal-500/10 border-teal-500/30 text-teal-300'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  )}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
        </div>
      </div>

      {/* Instrumental Variables Selection (Z) */}
      <div className="py-4 border-b border-slate-800">
        <label className="font-medium text-xs text-slate-300 flex items-center justify-between mb-2">
          <span>Biến Công Cụ Ràng Buộc Loại Trừ (Exclusion Restrictions Z - Chỉ tác động vào quyết định chọn lọc):</span>
          <span className="text-slate-400 font-normal">Đã chọn: {instrumentQids.length} biến (Tùy chọn)</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto pr-1">
          {questions
            .filter((q) => q.id !== treatmentQid && q.id !== outcomeQid)
            .map((q) => {
              const isSelected = instrumentQids.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleInstrument(q.id)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors cursor-pointer border ${
                    isSelected
                      ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  )}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="my-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="mt-6 space-y-6">
          {/* Key Metrics Banners */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tác Động Nhóm Can Thiệp (ATT)</span>
              <span className="text-lg font-bold text-emerald-400">
                {result.diagnostics.average_treatment_effect_treated_att > 0 ? `+${result.diagnostics.average_treatment_effect_treated_att.toFixed(3)}` : result.diagnostics.average_treatment_effect_treated_att.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                p = {result.diagnostics.att_p_value < 0.001 ? '< 0.001' : result.diagnostics.att_p_value.toFixed(4)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tác Động Nhóm Đối Chứng (ATU)</span>
              <span className="text-lg font-bold text-sky-400">
                {result.diagnostics.average_treatment_effect_untreated_atu > 0 ? `+${result.diagnostics.average_treatment_effect_untreated_atu.toFixed(3)}` : result.diagnostics.average_treatment_effect_untreated_atu.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                p = {result.diagnostics.atu_p_value < 0.001 ? '< 0.001' : result.diagnostics.atu_p_value.toFixed(4)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Không Đồng Nhất (TH)</span>
              <span className="text-lg font-bold text-indigo-300">
                {result.diagnostics.transitional_heterogeneity > 0 ? `+${result.diagnostics.transitional_heterogeneity.toFixed(3)}` : result.diagnostics.transitional_heterogeneity.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                ATT - ATU (Chênh lệch)
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tương Quan Chọn Lọc ρ₁</span>
              <span className={`text-base font-bold ${result.diagnostics.rho_1_treated_selection > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {result.diagnostics.rho_1_treated_selection.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {result.diagnostics.rho_1_treated_selection > 0 ? 'Tự chọn lọc tích cực' : 'Tự chọn lọc tiêu cực'}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tương Quan Chọn Lọc ρ₀</span>
              <span className="text-base font-bold text-slate-200">
                {result.diagnostics.rho_0_untreated_selection.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Regime 0 residual correlation
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Kiểm Định LR Tính Độc Lập</span>
              <span className={`text-base font-bold ${result.diagnostics.has_endogenous_selection ? 'text-teal-400' : 'text-slate-400'}`}>
                χ² = {result.diagnostics.lr_test_independence_stat.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                p = {result.diagnostics.lr_test_independence_pval < 0.001 ? '< 0.001' : result.diagnostics.lr_test_independence_pval.toFixed(3)}
              </span>
            </div>
          </div>

          {/* Verdict Banner */}
          <div className={`p-4 rounded-xl border text-xs flex items-center justify-between gap-4 ${
            result.diagnostics.has_endogenous_selection
              ? 'bg-teal-500/10 border-teal-500/20 text-teal-300'
              : 'bg-slate-800/60 border-slate-700 text-slate-300'
          }`}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-teal-400" />
              <span>
                <strong>Kiểm định Chọn lọc Nội sinh:</strong> {result.diagnostics.has_endogenous_selection
                  ? 'Bác bỏ tính ngoại sinh (p < 0.05). Sai lệch tự chọn lọc tồn tại có ý nghĩa thống kê; OLS tiêu chuẩn bị chệch và ESR là bắt buộc.'
                  : 'Chưa đủ bằng chứng bác bỏ tính ngoại sinh (p >= 0.05).'}
              </span>
            </div>
            <span className="text-[11px] font-mono opacity-80 shrink-0">
              Treated N₁ = {result.diagnostics.regime1_count} ({result.diagnostics.treatment_rate_pct.toFixed(1)}%) | Untreated N₀ = {result.diagnostics.regime0_count}
            </span>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('treatment_effects')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'treatment_effects'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Tác Động Xử Lý Nhân Quả (ATT &amp; ATU)
            </button>
            <button
              onClick={() => setActiveTab('coefficients')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'coefficients'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Hệ Số Theo Chế Độ (Regime 1 vs Regime 0)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'svg'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Biểu Đồ Trực Quan Hóa ESR</span>
            </button>
          </div>

          {/* Tab 1: Treatment Effects & Counterfactuals */}
          {activeTab === 'treatment_effects' && result.treatment_effects && (
            <div className="space-y-4">
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Chỉ Số Nhân Quả</th>
                      <th className="py-2.5 px-3">Mô Tả &amp; Ý Nghĩa Quyết Định</th>
                      <th className="py-2.5 px-3 text-right">Ước Lượng Hiệu Ứng</th>
                      <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                      <th className="py-2.5 px-3 text-right">t-stat</th>
                      <th className="py-2.5 px-3 text-right">p-value</th>
                      <th className="py-2.5 px-3 text-center">Khoảng Tin Cậy 95%</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-bold text-emerald-400">ATT (Treated Effect)</td>
                      <td className="py-2.5 px-3 font-sans text-white">Hiệu ứng trung bình đối với nhóm thực sự đã tham gia can thiệp</td>
                      <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">{result.treatment_effects.att.estimate.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-400">{result.treatment_effects.att.standard_error.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-300">{result.treatment_effects.att.t_statistic.toFixed(3)}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className={result.treatment_effects.att.p_value < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                          {result.treatment_effects.att.p_value < 0.001 ? '< 0.001' : result.treatment_effects.att.p_value.toFixed(4)}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-center text-slate-400">
                        [{result.treatment_effects.att.ci_95[0].toFixed(3)}, {result.treatment_effects.att.ci_95[1].toFixed(3)}]
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-bold text-sky-400">ATU (Untreated Effect)</td>
                      <td className="py-2.5 px-3 font-sans text-white">Hiệu ứng trung bình nếu mở rộng can thiệp sang nhóm đối chứng</td>
                      <td className="py-2.5 px-3 text-right text-sky-400 font-bold">{result.treatment_effects.atu.estimate.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-400">{result.treatment_effects.atu.standard_error.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-300">{result.treatment_effects.atu.t_statistic.toFixed(3)}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className={result.treatment_effects.atu.p_value < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                          {result.treatment_effects.atu.p_value < 0.001 ? '< 0.001' : result.treatment_effects.atu.p_value.toFixed(4)}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-center text-slate-400">
                        [{result.treatment_effects.atu.ci_95[0].toFixed(3)}, {result.treatment_effects.atu.ci_95[1].toFixed(3)}]
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-bold text-indigo-300">TH (Transitional Heterogeneity)</td>
                      <td className="py-2.5 px-3 font-sans text-white">Chênh lệch hiệu ứng xử lý giữa hai nhóm (ATT - ATU)</td>
                      <td className="py-2.5 px-3 text-right text-indigo-300 font-bold">{result.treatment_effects.transitional_heterogeneity.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-500">-</td>
                      <td className="py-2.5 px-3 text-right text-slate-500">-</td>
                      <td className="py-2.5 px-3 text-right text-slate-500">-</td>
                      <td className="py-2.5 px-3 text-center text-slate-500">-</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Coefficients Comparison */}
          {activeTab === 'coefficients' && result.coefficients && (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Biến Giải Thích (X)</th>
                    <th className="py-2.5 px-3 text-right">Chế Độ 1 (Treated β₁)</th>
                    <th className="py-2.5 px-3 text-right">SE (β₁)</th>
                    <th className="py-2.5 px-3 text-right">p-value (β₁)</th>
                    <th className="py-2.5 px-3 text-right">Chế Độ 0 (Untreated β₀)</th>
                    <th className="py-2.5 px-3 text-right">SE (β₀)</th>
                    <th className="py-2.5 px-3 text-right">p-value (β₀)</th>
                    <th className="py-2.5 px-3 text-right">Chênh Lệch (β₁ - β₀)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.coefficients.map((row, idx) => {
                    const qObj = questions.find(q => q.id === row.variable);
                    const label = row.is_intercept ? row.variable : (qObj ? qObj.title : row.variable);
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-sans text-white font-medium">{label}</td>
                        <td className="py-2.5 px-3 text-right text-emerald-400 font-semibold">{row.regime1_estimate.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-right text-slate-400">{row.regime1_se.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-right">
                          <span className={row.regime1_p < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                            {row.regime1_p < 0.001 ? '< 0.001' : row.regime1_p.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right text-sky-400 font-semibold">{row.regime0_estimate.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-right text-slate-400">{row.regime0_se.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-right">
                          <span className={row.regime0_p < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                            {row.regime0_p < 0.001 ? '< 0.001' : row.regime0_p.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right text-indigo-300">{row.coefficient_difference.toFixed(4)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: SVG Visualization */}
          {activeTab === 'svg' && result.svg_visualization && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col items-center justify-center overflow-hidden">
              <div
                className="w-full max-w-4xl flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-800/40 border border-slate-700/60 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                  Báo Cáo Học Thuật Chuẩn APA 7th (Endogenous Switching Regression ESR)
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-teal-300 transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép đoạn văn'}</span>
                </button>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line bg-slate-900/50 p-3 rounded-lg border border-slate-800/80">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
