import React, { useState } from 'react';
import {
  GitFork,
  Play,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Info,
  Copy,
  Sliders,
  Layers,
  Activity,
  Award,
  TrendingDown,
  TrendingUp,
  Percent,
  Search,
  Filter,
  PieChart,
  ShieldCheck,
  Target
} from 'lucide-react';
import { api } from '../api/client';
import { ShiftShareIVRequest, ShiftShareIVResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface ShiftShareIVCardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const ShiftShareIVCard: React.FC<ShiftShareIVCardProps> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedShares, setSelectedShares] = useState<string[]>([]);
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ShiftShareIVResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleShare = (qid: string) => {
    setSelectedShares((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId || selectedShares.length < 2) {
      setError('Vui lòng chọn Biến kết quả (Y), Biến nội sinh (D) và ít nhất 2 Biến tỷ trọng thành phần (Shares z_ik).');
      return;
    }
    if (outcomeQId === treatmentQId || selectedShares.includes(outcomeQId) || selectedShares.includes(treatmentQId)) {
      setError('Biến kết quả, biến nội sinh và các biến tỷ trọng không được trùng lặp.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: ShiftShareIVRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      share_question_ids: selectedShares,
      covariate_question_ids: selectedCovariates.filter(
        (id) => id !== outcomeQId && id !== treatmentQId && !selectedShares.includes(id)
      ),
      alpha_level: alphaLevel,
      scope: scope
    };

    try {
      const res = await api.runShiftShareIV(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể thực hiện phân tích Shift-Share IV.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng Shift-Share IV.');
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
    <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-cyan-50 dark:bg-cyan-950/60 rounded-lg border border-cyan-200 dark:border-cyan-800">
            <GitFork className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Shift-Share / Bartik Instrumental Variables
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-cyan-100 dark:bg-cyan-900 text-cyan-700 dark:text-cyan-300">
                Goldsmith-Pinkham et al. (2020 AER)
              </span>
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Phân rã trọng số Rotemberg xác định ngành/thành phần chủ đạo và ước lượng sai số chuẩn Adao-Kolesár-Morales (AKM) chống tương quan phơi nhiễm.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !outcomeQId || !treatmentQId || selectedShares.length < 2}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm ${
              loading || !outcomeQId || !treatmentQId || selectedShares.length < 2
                ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
                : 'bg-cyan-600 hover:bg-cyan-700 text-white hover:shadow'
            }`}
          >
            {loading ? (
              <>
                <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                Đang phân rã Rotemberg...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2 fill-current" />
                Ước lượng Bartik 2SLS
              </>
            )}
          </button>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50/70 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800">
        {/* Outcome Y */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Biến kết quả (Y):
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-cyan-500"
          >
            <option value="">-- Chọn câu hỏi kết quả --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Treatment D */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Biến nội sinh (Endogenous D):
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-cyan-500"
          >
            <option value="">-- Chọn biến nội sinh --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Alpha Level */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Mức ý nghĩa thống kê (α):
          </label>
          <select
            value={alphaLevel}
            onChange={(e) => setAlphaLevel(parseFloat(e.target.value))}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-cyan-500"
          >
            <option value={0.05}>α = 0.05 (95% CI)</option>
            <option value={0.01}>α = 0.01 (99% CI)</option>
            <option value={0.10}>α = 0.10 (90% CI)</option>
          </select>
        </div>

        {/* Scope */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Phạm vi phản hồi:
          </label>
          <div className="inline-flex rounded-md shadow-sm w-full">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={`flex-1 px-3 py-2 text-xs font-medium rounded-l-md border ${
                scope === 'all'
                  ? 'bg-cyan-100 text-cyan-700 border-cyan-300 dark:bg-cyan-950 dark:text-cyan-300 dark:border-cyan-800'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
              }`}
            >
              Tất cả
            </button>
            <button
              type="button"
              onClick={() => setScope('verified_clean')}
              className={`flex-1 px-3 py-2 text-xs font-medium rounded-r-md border-t border-b border-r ${
                scope === 'verified_clean'
                  ? 'bg-cyan-100 text-cyan-700 border-cyan-300 dark:bg-cyan-950 dark:text-cyan-300 dark:border-cyan-800'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
              }`}
            >
              Verified Clean
            </button>
          </div>
        </div>

        {/* Shares Multi-Select */}
        <div className="col-span-1 md:col-span-2 space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Tập biến tỷ trọng thành phần (Shares z_ik - Tối thiểu 2 biến):</span>
            <span className="text-cyan-600 font-bold">Đã chọn {selectedShares.length} shares</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
            {questions
              .filter((q) => q.id !== outcomeQId && q.id !== treatmentQId)
              .map((q) => {
                const isSelected = selectedShares.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleShare(q.id)}
                    className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                      isSelected
                        ? 'bg-cyan-50 dark:bg-cyan-950/80 border-cyan-300 dark:border-cyan-700 text-cyan-700 dark:text-cyan-300 font-medium'
                        : 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
                    }`}
                  >
                    {q.title}
                  </button>
                );
              })}
          </div>
        </div>

        {/* Covariates Multi-Select */}
        <div className="col-span-1 md:col-span-2 space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Biến kiểm soát nền (Controls X):</span>
            <span className="text-slate-400 font-normal">Đã chọn {selectedCovariates.length} biến</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
            {questions
              .filter((q) => q.id !== outcomeQId && q.id !== treatmentQId && !selectedShares.includes(q.id))
              .map((q) => {
                const isSelected = selectedCovariates.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleCovariate(q.id)}
                    className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                      isSelected
                        ? 'bg-indigo-50 dark:bg-indigo-950/80 border-indigo-300 dark:border-indigo-700 text-indigo-700 dark:text-indigo-300 font-medium'
                        : 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
                    }`}
                  >
                    {q.title}
                  </button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/80 text-rose-700 dark:text-rose-300 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
          <div className="text-sm font-medium">{error}</div>
        </div>
      )}

      {/* Result Section */}
      {result && result.overall_summary && (
        <div className="space-y-6 pt-2">
          {/* KPI Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-cyan-50/70 dark:bg-cyan-950/40 border border-cyan-200 dark:border-cyan-800">
              <div className="text-xs text-cyan-700 dark:text-cyan-300 font-semibold flex items-center justify-between">
                <span>Ước lượng 2SLS (&beta;_Bartik)</span>
                <span className="text-[10px] bg-cyan-200 dark:bg-cyan-900 px-1.5 py-0.5 rounded text-cyan-800 dark:text-cyan-200 font-mono">
                  {result.overall_summary.n_shares_k} Shares
                </span>
              </div>
              <div className="text-3xl font-extrabold text-cyan-700 dark:text-cyan-400 mt-1">
                {result.overall_summary.beta_2sls.toFixed(3)}
              </div>
              <div className="text-xs text-cyan-600 dark:text-cyan-400 mt-1 font-mono">
                95% CI: [{result.overall_summary.confidence_interval_95[0].toFixed(2)}, {result.overall_summary.confidence_interval_95[1].toFixed(2)}]
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium flex items-center justify-between">
                <span>First-Stage F-Statistic</span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                    result.overall_summary.first_stage_f_statistic >= 10
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                  }`}
                >
                  {result.overall_summary.first_stage_f_statistic >= 10 ? 'Strong IV' : 'Weak IV'}
                </span>
              </div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1 font-mono">
                {result.overall_summary.first_stage_f_statistic.toFixed(2)}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Ngưỡng Staiger-Stock (F &ge; 10)
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900">
              <div className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">Sai số Chuẩn AKM Robust</div>
              <div className="text-2xl font-bold text-indigo-700 dark:text-indigo-300 mt-1 font-mono">
                {result.overall_summary.se_akm_robust.toFixed(3)}
              </div>
              <div className="text-xs text-indigo-500 mt-0.5">
                Conventional SE: {result.overall_summary.se_conventional.toFixed(3)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Độ tập trung Rotemberg (HHI)</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1 font-mono">
                {result.overall_summary.rotemberg_hhi.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Top 5 shares: {(result.overall_summary.top_5_shares_weight_share * 100).toFixed(1)}% quyền số
              </div>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-inner overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Phân rã Trọng số Rotemberg &amp; Độ dốc Đáp ứng Nhân quả 2SLS (Goldsmith-Pinkham et al. 2020)
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Rotemberg Decomposition Table */}
          {result.rotemberg_decomposition && result.rotemberg_decomposition.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-500" />
                Bảng Phân rã Trọng số Rotemberg (&alpha;_k) &amp; Ước lượng Thành phần (Just-Identified &beta;_k)
              </h4>
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold">
                    <tr>
                      <th className="px-4 py-3">Biến Tỷ trọng Thành phần (Share)</th>
                      <th className="px-3 py-3 text-right">Trọng số Rotemberg (&alpha;_k)</th>
                      <th className="px-3 py-3 text-right">Tỷ trọng Quyền số (%)</th>
                      <th className="px-3 py-3 text-right">Cú sốc Ngành (Shock g_k)</th>
                      <th className="px-3 py-3 text-right">Ước lượng Riêng phần (&beta;_k)</th>
                      <th className="px-3 py-3 text-right">Hiệp phương sai Stage 1</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900 font-mono">
                    {result.rotemberg_decomposition.map((item, idx) => {
                      const isNegative = item.rotemberg_weight < 0;
                      return (
                        <tr key={idx} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                          <td className="px-4 py-2.5 font-sans font-medium text-slate-900 dark:text-slate-100">
                            {item.share_variable}
                          </td>
                          <td
                            className={`px-3 py-2.5 text-right font-bold ${
                              isNegative ? 'text-rose-600 dark:text-rose-400' : 'text-cyan-700 dark:text-cyan-300'
                            }`}
                          >
                            {item.rotemberg_weight.toFixed(4)}
                          </td>
                          <td className="px-3 py-2.5 text-right font-semibold text-slate-700 dark:text-slate-300">
                            {item.rotemberg_weight_pct.toFixed(2)}%
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-600 dark:text-slate-400">
                            {item.share_shock_value.toFixed(3)}
                          </td>
                          <td className="px-3 py-2.5 text-right font-bold text-slate-900 dark:text-slate-100">
                            {item.just_identified_beta.toFixed(3)}
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-600 dark:text-slate-400">
                            {item.first_stage_cov.toFixed(3)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Overidentification & Monotonicity Diagnostics Panel */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
            <div className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-500" />
              Kiểm định Tính đồng nhất &amp; Tính Ngoại sinh (Overidentification Diagnostics)
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-slate-600 dark:text-slate-400 pt-1">
              <div>
                <span className="text-slate-400">Kiểm định Sargan (&chi;²):</span>{' '}
                <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                  {result.overall_summary.overid_sargan_stat.toFixed(2)} (p = {result.overall_summary.overid_p_value.toFixed(4)})
                </span>
              </div>
              <div>
                <span className="text-slate-400">Kết luận Sargan:</span>{' '}
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  {result.overall_summary.overid_p_value >= 0.05 ? 'Nhất quán (p &ge; 0.05)' : 'Không đồng nhất'}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Tổng quyền số dương:</span>{' '}
                <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                  {(result.overall_summary.sum_positive_rotemberg_weights * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-slate-400">Tổng quyền số âm:</span>{' '}
                <span
                  className={`font-mono font-semibold ${
                    result.overall_summary.sum_negative_rotemberg_weights < 0
                      ? 'text-rose-600 dark:text-rose-400'
                      : 'text-slate-800 dark:text-slate-200'
                  }`}
                >
                  {(result.overall_summary.sum_negative_rotemberg_weights * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-cyan-50/50 dark:bg-cyan-950/20 border border-cyan-200 dark:border-cyan-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cyan-900 dark:text-cyan-300 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                  Báo cáo Thống kê &amp; Trình bày Chuẩn APA 7th
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="text-xs text-cyan-700 dark:text-cyan-300 hover:text-cyan-900 dark:hover:text-cyan-100 flex items-center gap-1 font-medium transition-colors"
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                      Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 italic font-serif">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
