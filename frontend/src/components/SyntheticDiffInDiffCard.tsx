import React, { useState } from 'react';
import {
  TrendingUp,
  Layers,
  Sliders,
  Copy,
  Check,
  Download,
  AlertCircle,
  HelpCircle,
  BarChart3,
  RefreshCw,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  Percent,
  Calendar,
  Clock,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import type {
  SyntheticDiffInDiffRequest,
  SyntheticDiffInDiffResult
} from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface SyntheticDiffInDiffCardProps {
  surveyId: string;
  questions: QuestionOption[];
}

export const SyntheticDiffInDiffCard: React.FC<SyntheticDiffInDiffCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'likert'].includes(q.question_type)
  );

  const [unitQId, setUnitQId] = useState<string>(
    questions[0]?.id || ''
  );
  const [timeQId, setTimeQId] = useState<string>(
    numericQuestions[0]?.id || questions[1]?.id || ''
  );
  const [treatmentQId, setTreatmentQId] = useState<string>(
    numericQuestions[1]?.id || questions[2]?.id || ''
  );
  const [outcomeQId, setOutcomeQId] = useState<string>(
    numericQuestions[2]?.id || numericQuestions[0]?.id || ''
  );

  const [zetaRegularization, setZetaRegularization] = useState<string>('');
  const [bootstrapReps, setBootstrapReps] = useState<number>(100);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SyntheticDiffInDiffResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const handleRunAnalysis = async () => {
    if (!unitQId || !timeQId || !treatmentQId || !outcomeQId) {
      setError('Vui lòng chọn đầy đủ 4 biến: Đơn vị (Unit), Thời gian (Time), Can thiệp (Treatment), và Kết quả (Outcome).');
      return;
    }
    if (new Set([unitQId, timeQId, treatmentQId, outcomeQId]).size < 4) {
      setError('Các biến phân tích không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: SyntheticDiffInDiffRequest = {
        unit_question_id: unitQId,
        time_question_id: timeQId,
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        l2_regularization_zeta: zetaRegularization.trim() ? parseFloat(zetaRegularization) : undefined,
        num_bootstrap_reps: bootstrapReps,
        alpha_level: alphaLevel,
        scope
      };

      const res = await api.runSyntheticDiffInDiff(surveyId, payload);
      setResult(res);
    } catch (err: any) {
      console.error('Error running Synthetic Difference-in-Differences analysis:', err);
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Không thể thực hiện ước lượng SDID. Vui lòng kiểm tra lại cấu hình panel và các kỳ quan sát.'
      );
    } finally {
      setLoading(false);
    }
  };

  const copyNarrativeToClipboard = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  const downloadNarrative = () => {
    if (!result?.apa_narrative) return;
    const blob = new Blob([result.apa_narrative], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DataTrust_SDID_Report_${surveyId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getPValueBadge = (pval?: number) => {
    if (pval === undefined || pval === null) return null;
    if (pval < 0.001) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
          p &lt; .001 ***
        </span>
      );
    }
    if (pval < 0.01) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
          p = {pval.toFixed(3)} **
        </span>
      );
    }
    if (pval < 0.05) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
          p = {pval.toFixed(3)} *
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
        p = {pval.toFixed(3)} (n.s.)
      </span>
    );
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 mb-8 transition-colors">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-200 dark:border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Synthetic Difference-in-Differences Engine (SDID)
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300">
                DataTrust AER 2021
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Kết hợp trọng số đơn vị đối chứng (Synthetic Control ω_i) và trọng số thời gian (DID λ_t) với chính quy hóa L2 (Arkhangelsky et al. 2021)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Đang giải tối ưu hóa SDID...' : 'Chạy Mô Hình SDID'}
          </button>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
        {/* Unit Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Đơn vị quan sát (Unit ID i) <span className="text-rose-500">*</span>
          </label>
          <select
            value={unitQId}
            onChange={(e) => setUnitQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-emerald-500"
          >
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Đơn vị định danh cá nhân, cửa hàng, chi nhánh, hoặc tỉnh/thành
          </p>
        </div>

        {/* Time Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Mốc thời gian (Time Period t) <span className="text-rose-500">*</span>
          </label>
          <select
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-emerald-500"
          >
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Năm, quý, tháng, đợt sóng khảo sát (Wave), hoặc vòng lặp
          </p>
        </div>

        {/* Treatment Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến Can thiệp (Treatment W_it) <span className="text-rose-500">*</span>
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-emerald-500"
          >
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            1 nếu đơn vị nhận can thiệp tại kỳ t, 0 nếu đối chứng
          </p>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến Kết quả (Outcome Y_it) <span className="text-rose-500">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-emerald-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Chỉ số định lượng quan sát: doanh thu, năng suất, điểm đánh giá
          </p>
        </div>
      </div>

      {/* Advanced Parameters Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700/60 mb-6 text-sm">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
              Chính quy hóa L2 (Zeta ζ):
            </span>
            <input
              type="text"
              placeholder="Tự động (Arkhangelsky)"
              value={zetaRegularization}
              onChange={(e) => setZetaRegularization(e.target.value)}
              className="w-36 text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Bootstrap Blocks:</span>
            <select
              value={bootstrapReps}
              onChange={(e) => setBootstrapReps(parseInt(e.target.value, 10))}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="50">50 lượt (Nhanh)</option>
              <option value="100">100 lượt (Chuẩn)</option>
              <option value="200">200 lượt (Độ chính xác cao)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Mức ý nghĩa α:</span>
            <select
              value={alphaLevel}
              onChange={(e) => setAlphaLevel(parseFloat(e.target.value))}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="0.05">α = 0.05 (CI 95%)</option>
              <option value="0.01">α = 0.01 (CI 99%)</option>
              <option value="0.10">α = 0.10 (CI 90%)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Phạm vi dữ liệu:</span>
          <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-white dark:bg-slate-800">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                scope === 'all'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
              }`}
            >
              Tất cả
            </button>
            <button
              type="button"
              onClick={() => setScope('verified_clean')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                scope === 'verified_clean'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
              }`}
            >
              <ShieldCheck className="w-3 h-3 inline mr-1" />
              Đã làm sạch
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-start gap-3 p-4 mb-6 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Lỗi ước lượng SDID</p>
            <p className="mt-0.5 text-xs text-rose-700 dark:text-rose-400">{error}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'success' && (
        <div className="space-y-6">
          {/* 4 KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: SDID ATT */}
            <div className="p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-emerald-700 dark:text-emerald-300 mb-1">
                <span className="font-semibold">Hiệu ứng Can thiệp (SDID τ̂)</span>
                {getPValueBadge(result.estimates?.sdid_p_value)}
              </div>
              <div className="text-2xl font-black text-emerald-900 dark:text-emerald-200">
                {(result.estimates?.sdid_tau ?? 0) > 0 ? '+' : ''}
                {(result.estimates?.sdid_tau ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                SE: ±{(result.estimates?.sdid_se ?? 0).toFixed(3)} | 95% CI: [
                {(result.estimates?.sdid_ci_95?.[0] ?? 0).toFixed(2)},{' '}
                {(result.estimates?.sdid_ci_95?.[1] ?? 0).toFixed(2)}]
              </div>
            </div>

            {/* KPI 2: DID Comparison & Bias Correction */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>So với DID Gốc (Không trọng số)</span>
                <span className="text-[11px] font-medium text-indigo-600 dark:text-indigo-400">
                  DID: {(result.estimates?.did_tau ?? 0).toFixed(3)}
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {(result.estimates?.bias_correction_vs_did ?? 0) > 0 ? '+' : ''}
                {(result.estimates?.bias_correction_vs_did ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Độ chệch xu hướng song song được SDID triệt tiêu
              </div>
            </div>

            {/* KPI 3: Pre-treatment RMSE Improvement */}
            <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-indigo-700 dark:text-indigo-300 mb-1">
                <span>Cải thiện Khớp Tiền Can thiệp</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  -{(result.diagnostics?.rmse_reduction_pct ?? 0).toFixed(1)}% RMSE
                </span>
              </div>
              <div className="text-2xl font-black text-indigo-900 dark:text-indigo-200">
                {(result.diagnostics?.rmse_sdid_pre ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
                Pre-RMSE SDID (so với DID gốc: {(result.diagnostics?.rmse_did_pre ?? 0).toFixed(3)})
              </div>
            </div>

            {/* KPI 4: Effective Donors & Pool */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Đơn vị Đối chứng Hiệu dụng</span>
                <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300">
                  N_pool = {result.num_control_units}
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {(result.diagnostics?.effective_donors_n_eff ?? 0).toFixed(1)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                N_eff = 1 / Σ ω_i² (Mức phân tán trọng số đối chứng)
              </div>
            </div>
          </div>

          {/* SVG Visualizer Panel */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    Quỹ đạo Can thiệp vs Đối chứng Tổng hợp &amp; Phân bổ Trọng số Donor
                  </h4>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-indigo-600 rounded"></span>
                    <span className="text-slate-600 dark:text-slate-400">Treated</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-emerald-500 rounded border-dashed border-b border-emerald-500"></span>
                    <span className="text-slate-600 dark:text-slate-400">Synthetic Control</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-slate-400 rounded border-dotted border-b border-slate-400"></span>
                    <span className="text-slate-500 dark:text-slate-500">DID Gốc</span>
                  </div>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Top Donor Weights Table */}
          {result.top_donor_weights && result.top_donor_weights.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Trọng số Đơn vị Đối chứng Hàng đầu (Donor Pool Weights ω_i)
                </h4>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Chính quy hóa L2 ζ = {(result.diagnostics?.l2_regularization_zeta ?? 0).toFixed(4)}
                </span>
              </div>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-100/70 dark:bg-slate-800 text-slate-700 dark:text-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Đơn vị Đối chứng (Donor Unit)</th>
                      <th className="py-2.5 px-3 font-semibold">Trọng số Tuyệt đối (ω_i)</th>
                      <th className="py-2.5 px-3 font-semibold">Tỷ trọng Đóng góp (%)</th>
                      <th className="py-2.5 px-3 font-semibold w-1/3">Thanh Tỷ lệ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
                    {result.top_donor_weights.map((d) => (
                      <tr key={d.unit_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                          {d.unit_id}
                        </td>
                        <td className="py-2 px-3">{d.weight.toFixed(4)}</td>
                        <td className="py-2 px-3 font-semibold text-emerald-600 dark:text-emerald-400">
                          {d.weight_pct.toFixed(2)}%
                        </td>
                        <td className="py-2 px-3">
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                            <div
                              className="bg-emerald-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${Math.min(100, Math.max(2, d.weight_pct))}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Period Trajectory Table */}
          {result.period_profiles && result.period_profiles.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Bảng Quỹ đạo Trung bình Theo Kỳ (Period Trajectory Profiles)
                </h4>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Kỳ bắt đầu can thiệp: <strong className="text-rose-600 dark:text-rose-400">{result.first_treated_period}</strong>
                </span>
              </div>
              <div className="overflow-x-auto max-h-60">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-100/70 dark:bg-slate-800 text-slate-700 dark:text-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Kỳ (Period)</th>
                      <th className="py-2.5 px-3 font-semibold">Giai đoạn</th>
                      <th className="py-2.5 px-3 font-semibold">Treated Ȳ</th>
                      <th className="py-2.5 px-3 font-semibold">Synthetic Control Ŷ</th>
                      <th className="py-2.5 px-3 font-semibold">DID Gốc (Raw Control)</th>
                      <th className="py-2.5 px-3 font-semibold">Trọng số Thời gian (λ_t)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
                    {result.period_profiles.map((p) => (
                      <tr key={p.period} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                          {p.period}
                        </td>
                        <td className="py-2 px-3 font-sans">
                          {p.is_post_treatment ? (
                            <span className="px-2 py-0.5 text-[11px] font-semibold rounded bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                              Post (Can thiệp)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 text-[11px] font-semibold rounded bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                              Pre (Tiền)
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-3 font-semibold text-indigo-600 dark:text-indigo-400">
                          {p.treated_mean.toFixed(2)}
                        </td>
                        <td className="py-2 px-3 font-semibold text-emerald-600 dark:text-emerald-400">
                          {p.synthetic_control_mean.toFixed(2)}
                        </td>
                        <td className="py-2 px-3 text-slate-500">{p.raw_control_mean.toFixed(2)}</td>
                        <td className="py-2 px-3">
                          {p.time_weight > 0 ? (
                            <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                              {(p.time_weight * 100).toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA Scientific Narrative Box */}
          {result.apa_narrative && (
            <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    Báo cáo khoa học chuẩn APA 7th &amp; Kinh tế lượng can thiệp
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={copyNarrativeToClipboard}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition-colors"
                  >
                    {copiedNarrative ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedNarrative ? 'Đã sao chép' : 'Sao chép APA'}
                  </button>
                  <button
                    onClick={downloadNarrative}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Tải Markdown
                  </button>
                </div>
              </div>
              <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans whitespace-pre-wrap bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
