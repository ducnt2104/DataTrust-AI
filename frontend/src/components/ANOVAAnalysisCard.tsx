import React, { useState } from 'react';
import {
  Layers,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  Play,
  Info,
  Scale,
  Sparkles,
  TrendingUp,
  Table,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { OneWayANOVAReport } from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
  options?: any;
}

interface Props {
  surveyId: string;
  questions: QuestionItem[];
}

export const ANOVAAnalysisCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [groupingQId, setGroupingQId] = useState<string>('');
  const [targetQId, setTargetQId] = useState<string>('');
  const [result, setResult] = useState<OneWayANOVAReport | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Phân loại câu hỏi phân nhóm (định tính) và thang đo (định lượng)
  const categoricalQuestions = questions.filter(q =>
    ['single_choice', 'dropdown', 'boolean'].includes(q.question_type)
  );

  const scaleQuestions = questions.filter(q =>
    ['rating', 'linear_scale', 'number', 'nps', 'likert'].includes(q.question_type) ||
    (q.question_type === 'single_choice' && ['hài lòng', 'đồng ý', 'thang điểm', 'likert', 'mức độ'].some(k => q.title.toLowerCase().includes(k)))
  );

  const handleRunANOVA = async () => {
    if (!groupingQId || !targetQId) {
      setError('Vui lòng chọn đầy đủ biến phân nhóm (>= 3 nhóm) và biến thang đo mục tiêu.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runOneWayANOVA(surveyId, {
        grouping_question_id: groupingQId,
        target_question_id: targetQId,
        scope
      });
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi thực hiện phân tích One-Way ANOVA.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!result?.apa_interpretation) return;
    navigator.clipboard.writeText(result.apa_interpretation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mt-6">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 bg-gradient-to-r from-violet-50/50 via-purple-50/30 to-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-violet-600 text-white rounded-lg shadow-sm">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-800">
                  Phân tích Phương sai Một chiều (One-Way ANOVA & Tukey HSD)
                </h3>
                <span className="px-2 py-0.5 text-xs font-semibold bg-violet-100 text-violet-700 rounded-full">
                  Fisher (1925) & Tukey (1949)
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Kiểm định sai biệt trung bình giữa 3 nhóm trở lên, kiểm định tính đồng nhất phương sai Levene, đo kích thước hiệu ứng (η², ω²), và so sánh cặp hậu nghiệm Tukey-Kramer.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <label className="text-xs font-medium text-slate-600">Phạm vi:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500"
            >
              <option value="all">Tất cả phản hồi hợp lệ</option>
              <option value="verified_clean">Chỉ dữ liệu làm sạch (Clean)</option>
            </select>
          </div>
        </div>

        {/* Input Selectors */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4 bg-white/80 p-4 rounded-xl border border-violet-100/80">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              1. Biến phân loại / Phân nhóm (Categorical Factor - ≥ 3 nhóm):
            </label>
            <select
              value={groupingQId}
              onChange={(e) => {
                setGroupingQId(e.target.value);
                setResult(null);
              }}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2.5 font-medium text-slate-700 focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500"
            >
              <option value="">-- Chọn biến phân nhóm (Phòng ban, Trình độ, Chi nhánh...) --</option>
              {categoricalQuestions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              2. Biến đo lường mục tiêu (Dependent Variable - Thang đo liên tục):
            </label>
            <select
              value={targetQId}
              onChange={(e) => {
                setTargetQId(e.target.value);
                setResult(null);
              }}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2.5 font-medium text-slate-700 focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500"
            >
              <option value="">-- Chọn biến thang đo phụ thuộc (Điểm hài lòng, Hiệu suất...) --</option>
              {scaleQuestions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Execute Button */}
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-slate-500 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-violet-500" />
            Tự động loại bỏ mẫu khuyết (listwise deletion) và kiểm định phân phối Levene trước khi tính omnibus F.
          </p>
          <button
            onClick={handleRunANOVA}
            disabled={loading || !groupingQId || !targetQId}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Đang xử lý ANOVA & Tukey...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Thực hiện Kiểm định One-Way ANOVA
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2.5 text-rose-700 text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <div>
              <span className="font-semibold">Không thể thực hiện kiểm định:</span> {error}
            </div>
          </div>
        )}
      </div>

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="p-6 space-y-6">
          {/* Hero KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* F-Statistic Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Omnibus F-Statistic
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  {result.anova_table.f_stat.toFixed(2)}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  df({result.anova_table.df_between}, {result.anova_table.df_within})
                </span>
              </div>
              <div className="mt-2 text-xs">
                {result.anova_table.is_significant_05 ? (
                  <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                    <CheckCircle2 className="w-3 h-3" /> F vượt ngưỡng tới hạn
                  </span>
                ) : (
                  <span className="text-slate-500">Chưa vượt ngưỡng tới hạn</span>
                )}
              </div>
            </div>

            {/* P-Value Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                P-Value (Ý nghĩa tổng quát)
              </span>
              <div className="text-2xl font-black text-slate-900">
                {result.anova_table.p_value < 0.001
                  ? '< .001'
                  : result.anova_table.p_value.toFixed(4)}
              </div>
              <div className="mt-2">
                {result.anova_table.is_significant_05 ? (
                  <span className="px-2 py-0.5 text-[11px] font-bold bg-emerald-100 text-emerald-700 rounded-md">
                    Có ý nghĩa thống kê (p &lt; .05)
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[11px] font-semibold bg-slate-200 text-slate-600 rounded-md">
                    Không có ý nghĩa (p ≥ .05)
                  </span>
                )}
              </div>
            </div>

            {/* Eta-Squared (η²) Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Kích thước hiệu ứng (η²)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-violet-700">
                  {result.effect_size.eta_squared.toFixed(3)}
                </span>
                <span className="text-xs text-violet-600 font-medium">
                  Eta-Squared
                </span>
              </div>
              <div className="mt-2">
                <span className="px-2 py-0.5 text-[11px] font-semibold bg-violet-100 text-violet-800 rounded-md">
                  {result.effect_size.magnitude}
                </span>
              </div>
            </div>

            {/* Omega-Squared (ω²) Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Omega-Squared (ω²)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-800">
                  {result.effect_size.omega_squared.toFixed(3)}
                </span>
                <span className="text-xs text-slate-500">
                  K = {result.groups_count} nhóm
                </span>
              </div>
              <div className="mt-2 text-xs text-slate-500">
                Ước lượng ít thiên lệch cho tổng thể
              </div>
            </div>
          </div>

          {/* Levene's Test of Equal Variances */}
          <div className="bg-slate-50/70 border border-slate-200 rounded-xl p-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4 text-violet-600" />
                <span className="text-xs font-bold text-slate-800">
                  Kiểm định Tính đồng nhất Phương sai Levene (Brown-Forsythe Medians):
                </span>
                <span className="text-xs font-mono text-slate-600">
                  F({result.levene_test.df1}, {result.levene_test.df2}) = {result.levene_test.f_stat.toFixed(2)}, p = {result.levene_test.p_value.toFixed(3)}
                </span>
              </div>

              <div>
                {result.levene_test.equal_variances_assumed ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold bg-emerald-100 text-emerald-800 rounded-lg">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Thỏa mãn giả định phương sai đồng nhất (p ≥ .05)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold bg-amber-100 text-amber-800 rounded-lg">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    Lưu ý: Phương sai không đồng nhất (p &lt; .05)
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Group Descriptive Statistics */}
          <div>
            <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-violet-600" />
              Thống kê Mô tả Từng nhóm Đối tượng (Group Statistics)
              <span className="text-xs font-normal text-slate-500">
                (Tổng N = {result.total_sample_size}, Điểm TB Tổng thể = {result.grand_mean.toFixed(2)})
              </span>
            </h4>

            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Tên nhóm</th>
                    <th className="py-2.5 px-3 text-right">Cỡ mẫu (N)</th>
                    <th className="py-2.5 px-3 text-right">Trung bình (M)</th>
                    <th className="py-2.5 px-3 text-right">Độ lệch chuẩn (SD)</th>
                    <th className="py-2.5 px-3 text-right">Trung vị (Mdn)</th>
                    <th className="py-2.5 px-3 text-right">Sai số chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-center">95% CI cho Mean</th>
                    <th className="py-2.5 px-3 text-left">Phổ trực quan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  {result.group_statistics.map((g) => {
                    const pctOfMax = Math.min(100, Math.max(10, (g.mean / 5.0) * 100));
                    return (
                      <tr key={g.group_name} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-semibold text-slate-900">
                          {g.group_name}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono">{g.n}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-violet-700 font-mono">
                          {g.mean.toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-600">{g.std.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-600">{g.median.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-600">{g.std_error.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-center font-mono text-xs text-slate-600">
                          [{g.ci_95_lower.toFixed(2)}, {g.ci_95_upper.toFixed(2)}]
                        </td>
                        <td className="py-2.5 px-3 w-40">
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-violet-600 h-2 rounded-full transition-all"
                              style={{ width: `${pctOfMax}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Omnibus ANOVA Table */}
          <div>
            <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
              <Table className="w-4 h-4 text-violet-600" />
              Bảng Phân tích Phương sai Tổng quát (ANOVA Table)
            </h4>

            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Nguồn biến thiên (Source)</th>
                    <th className="py-2.5 px-3 text-right">Tổng bình phương (SS)</th>
                    <th className="py-2.5 px-3 text-right">Bậc tự do (df)</th>
                    <th className="py-2.5 px-3 text-right">Trung bình bình phương (MS)</th>
                    <th className="py-2.5 px-3 text-right">Thống kê F</th>
                    <th className="py-2.5 px-3 text-right">P-Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  <tr className="hover:bg-violet-50/30">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      Giữa các nhóm (Between Groups)
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono">{result.anova_table.ss_between.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{result.anova_table.df_between}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-semibold text-violet-700">
                      {result.anova_table.ms_between.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                      {result.anova_table.f_stat.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-violet-700">
                      {result.anova_table.p_value < 0.001
                        ? '< .001'
                        : result.anova_table.p_value.toFixed(4)}
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      Nội bộ nhóm (Within Groups / Residual)
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono">{result.anova_table.ss_within.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{result.anova_table.df_within}</td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-600">
                      {result.anova_table.ms_within.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                  </tr>
                  <tr className="bg-slate-50 font-bold border-t border-slate-200">
                    <td className="py-2.5 px-3 text-slate-900">Tổng cộng (Total)</td>
                    <td className="py-2.5 px-3 text-right font-mono">{result.anova_table.ss_total.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{result.anova_table.df_total}</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Tukey's HSD Post-Hoc Pairwise Comparisons */}
          <div>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
              <h4 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-violet-600" />
                Kiểm định Hậu nghiệm Tukey's HSD (Pairwise Comparisons)
              </h4>
              <span className="text-xs text-slate-500 font-mono">
                q_critical (α = .05) = {result.post_hoc_tukey[0]?.q_critical_05?.toFixed(2) || '3.31'}
              </span>
            </div>

            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Cặp so sánh</th>
                    <th className="py-2.5 px-3 text-right">Chênh lệch TB (ΔM)</th>
                    <th className="py-2.5 px-3 text-right">Sai số chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-right">Thống kê q</th>
                    <th className="py-2.5 px-3 text-center">95% CI cho Độ chênh</th>
                    <th className="py-2.5 px-3 text-center">Kết luận Ý nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  {result.post_hoc_tukey.map((p, idx) => (
                    <tr
                      key={idx}
                      className={p.is_significant ? 'bg-violet-50/20 hover:bg-violet-50/40' : 'hover:bg-slate-50/50'}
                    >
                      <td className="py-2.5 px-3 font-semibold text-slate-900 flex items-center gap-1.5">
                        <span>{p.group1}</span>
                        <ArrowRight className="w-3 h-3 text-slate-400" />
                        <span>{p.group2}</span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-800">
                        {p.mean_difference > 0 ? `+${p.mean_difference.toFixed(2)}` : p.mean_difference.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-600">{p.std_error.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-violet-700">
                        {p.q_stat.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-center font-mono text-slate-600">
                        [{p.ci_95_lower.toFixed(2)}, {p.ci_95_upper.toFixed(2)}]
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {p.is_significant ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-bold bg-emerald-100 text-emerald-800 rounded-md">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            Khác biệt có ý nghĩa (q ≥ q_crit)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-[11px] font-medium bg-slate-100 text-slate-600 rounded-md">
                            Không có ý nghĩa
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Edition Narrative */}
          <div className="bg-gradient-to-br from-violet-50/60 via-purple-50/30 to-white border border-violet-200/80 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-violet-600" />
                <h4 className="text-xs font-bold text-violet-900 uppercase tracking-wider">
                  Diễn giải Học thuật Chuẩn APA 7th Edition
                </h4>
              </div>
              <button
                onClick={handleCopyAPA}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-violet-50 text-violet-700 border border-violet-200 rounded-lg text-xs font-semibold transition-colors shadow-xs"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700">Đã sao chép!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao chép APA 7th</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-slate-800 leading-relaxed font-serif bg-white/70 p-3.5 rounded-lg border border-violet-100 italic">
              "{result.apa_interpretation}"
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="p-12 text-center text-slate-400">
          <Layers className="w-10 h-10 mx-auto mb-3 text-slate-300" />
          <p className="text-sm font-medium text-slate-600">
            Chưa có kết quả phân tích ANOVA
          </p>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
            Chọn biến phân nhóm có từ 3 nhóm trở lên (như phòng ban, chức vụ, vùng miền) và một câu hỏi thang đo để bắt đầu phân tích phương sai.
          </p>
        </div>
      )}
    </div>
  );
};
