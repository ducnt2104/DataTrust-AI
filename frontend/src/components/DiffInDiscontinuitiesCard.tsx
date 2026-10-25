import React, { useState } from 'react';
import {
  Scissors,
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
  ArrowRight,
  Maximize2
} from 'lucide-react';
import { api } from '../api/client';
import type {
  DiffInDiscontinuitiesRequest,
  DiffInDiscontinuitiesResult
} from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface DiffInDiscontinuitiesCardProps {
  surveyId: string;
  questions: QuestionOption[];
}

export const DiffInDiscontinuitiesCard: React.FC<DiffInDiscontinuitiesCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'likert'].includes(q.question_type)
  );

  const [runningQId, setRunningQId] = useState<string>(
    numericQuestions[0]?.id || ''
  );
  const [cutoffVal, setCutoffVal] = useState<number>(50.0);
  const [periodQId, setPeriodQId] = useState<string>(
    questions[1]?.id || ''
  );
  const [outcomeQId, setOutcomeQId] = useState<string>(
    numericQuestions[1]?.id || numericQuestions[0]?.id || ''
  );
  const [unitQId, setUnitQId] = useState<string>('');
  const [postPeriodVal, setPostPeriodVal] = useState<string>('');
  const [bandwidthVal, setBandwidthVal] = useState<string>('');
  const [kernelType, setKernelType] = useState<'triangular' | 'epanechnikov' | 'uniform'>('triangular');
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiffInDiscontinuitiesResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const handleRunAnalysis = async () => {
    if (!runningQId || !periodQId || !outcomeQId) {
      setError('Vui lòng chọn đầy đủ biến điểm chạy (Running Variable), biến thời kỳ (Period), và biến kết quả (Outcome).');
      return;
    }
    if (runningQId === periodQId || runningQId === outcomeQId || periodQId === outcomeQId) {
      setError('Các biến phân tích không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: DiffInDiscontinuitiesRequest = {
        running_question_id: runningQId,
        cutoff: cutoffVal,
        period_question_id: periodQId,
        outcome_question_id: outcomeQId,
        unit_question_id: unitQId ? unitQId : undefined,
        post_period_val: postPeriodVal.trim() ? postPeriodVal.trim() : undefined,
        bandwidth: bandwidthVal.trim() ? parseFloat(bandwidthVal) : undefined,
        kernel_type: kernelType,
        alpha_level: alphaLevel,
        scope
      };

      const res = await api.runDiffInDiscontinuities(surveyId, payload);
      setResult(res);
    } catch (err: any) {
      console.error('Error running Difference-in-Discontinuities analysis:', err);
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Không thể thực hiện ước lượng Diff-in-Disc. Vui lòng kiểm tra lại ngưỡng cutoff và số lượng quan sát ở hai bên ngưỡng.'
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
    a.download = `DataTrust_Diff_In_Disc_Report_${surveyId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getPValueBadge = (pval?: number) => {
    if (pval === undefined || pval === null) return null;
    if (pval < 0.001) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
          p &lt; .001 ***
        </span>
      );
    }
    if (pval < 0.01) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
          p = {pval.toFixed(3)} **
        </span>
      );
    }
    if (pval < 0.05) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400">
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
          <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400">
            <Scissors className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Difference-in-Discontinuities Design Engine (Diff-in-Disc / RD-DID)
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-purple-100 dark:bg-purple-950/70 text-purple-700 dark:text-purple-300">
                DataTrust AER 2016
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Kết hợp Hồi quy Đứt gãy (RDD) và Sai phân Kép (DID) để khử hoàn toàn bước nhảy nền cố hữu tại ngưỡng cutoff (Grembi, Nannicini, &amp; Troiano 2016)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Đang ước lượng Diff-in-Disc...' : 'Chạy Mô Hình Diff-in-Disc'}
          </button>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
        {/* Running Variable */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Điểm chạy (Running Variable X) <span className="text-rose-500">*</span>
          </label>
          <select
            value={runningQId}
            onChange={(e) => setRunningQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-purple-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Điểm số, dân số, doanh số, diện tích, thâm niên quyết định can thiệp
          </p>
        </div>

        {/* Cutoff Threshold */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Ngưỡng Cutoff (c) <span className="text-rose-500">*</span>
          </label>
          <input
            type="number"
            step="any"
            value={cutoffVal}
            onChange={(e) => setCutoffVal(parseFloat(e.target.value))}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-purple-500"
          />
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Giá trị ranh giới bắt đầu áp dụng chính sách (X &ge; c)
          </p>
        </div>

        {/* Period Variable */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Thời kỳ (Period t) <span className="text-rose-500">*</span>
          </label>
          <select
            value={periodQId}
            onChange={(e) => setPeriodQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-purple-500"
          >
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Giai đoạn Pre (trước chính sách) vs Post (sau chính sách)
          </p>
        </div>

        {/* Outcome Variable */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến Kết quả (Outcome Y) <span className="text-rose-500">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-purple-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Chỉ số đo lường hiệu quả chịu tác động của chính sách
          </p>
        </div>
      </div>

      {/* Advanced Parameters Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700/60 mb-6 text-sm">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
              Độ rộng băng (Bandwidth h):
            </span>
            <input
              type="text"
              placeholder="Tự động (IK/CCT)"
              value={bandwidthVal}
              onChange={(e) => setBandwidthVal(e.target.value)}
              className="w-32 text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Hàm nhân (Kernel):</span>
            <select
              value={kernelType}
              onChange={(e) => setKernelType(e.target.value as any)}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="triangular">Tam giác (Triangular - Tối ưu biên)</option>
              <option value="epanechnikov">Epanechnikov (Parabolic)</option>
              <option value="uniform">Đồng đều (Uniform)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Cụm (Cluster Unit):</span>
            <select
              value={unitQId}
              onChange={(e) => setUnitQId(e.target.value)}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="">Không phân cụm (HC1)</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Phạm vi:</span>
          <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-white dark:bg-slate-800">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                scope === 'all'
                  ? 'bg-purple-600 text-white shadow-sm'
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
                  ? 'bg-purple-600 text-white shadow-sm'
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
            <p className="font-semibold">Lỗi ước lượng Diff-in-Disc</p>
            <p className="mt-0.5 text-xs text-rose-700 dark:text-rose-400">{error}</p>
          </div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6">
          {/* 4 High-Impact KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Diff-in-Disc Causal Effect */}
            <div className="p-4 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-purple-700 dark:text-purple-300 mb-1">
                <span className="font-bold">Hiệu ứng Can thiệp (Diff-in-Disc τ̂)</span>
                {getPValueBadge(result.estimates?.p_value)}
              </div>
              <div className="text-2xl font-black text-purple-900 dark:text-purple-200">
                {(result.estimates?.diff_in_disc_tau ?? 0) > 0 ? '+' : ''}
                {(result.estimates?.diff_in_disc_tau ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
                SE: ±{(result.estimates?.se ?? 0).toFixed(3)} | t = {(result.estimates?.t_stat ?? 0).toFixed(2)}
              </div>
            </div>

            {/* KPI 2: Baseline Pre-existing Confounder */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Bước nhảy Nền Tiền Can thiệp (γ̂₀)</span>
                <span className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">
                  {((result.estimates?.baseline_pre_p_value ?? 1) < 0.05) ? 'Nhiễu cấu trúc *' : 'Không có nhiễu'}
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {(result.estimates?.baseline_pre_jump_gamma0 ?? 0) > 0 ? '+' : ''}
                {(result.estimates?.baseline_pre_jump_gamma0 ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Pre-Jump Placebo Test: p = {(result.estimates?.baseline_pre_p_value ?? 0).toFixed(3)}
              </div>
            </div>

            {/* KPI 3: Naive Post-RD Comparison */}
            <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-amber-700 dark:text-amber-300 mb-1">
                <span>So với RDD Đơn thuần (Naive RD)</span>
                <span className="font-semibold text-amber-800 dark:text-amber-300">
                  RD: {(result.estimates?.naive_post_rd_tau ?? 0).toFixed(3)}
                </span>
              </div>
              <div className="text-2xl font-black text-amber-900 dark:text-amber-200">
                {(result.estimates?.bias_correction_delta ?? 0) > 0 ? '+' : ''}
                {(result.estimates?.bias_correction_delta ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                Độ chệch được Diff-in-Disc triệt tiêu thành công
              </div>
            </div>

            {/* KPI 4: Bandwidth & McCrary Sorting Diagnostics */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Độ rộng Băng &amp; Thao túng Mật độ</span>
                <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                  h* = {(result.diagnostics?.optimal_bandwidth_h ?? 0).toFixed(2)}
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                N_h = {result.sample_size_effective_h}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">
                McCrary Test: {result.diagnostics?.mccrary_sorting_detected ? 'Cảnh báo Sorting ⚠️' : 'Mật độ chuẩn (Không sorting)'}
              </div>
            </div>
          </div>

          {/* SVG Visualizer Panel */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    Đồ thị Đứt gãy So sánh Pre-Policy vs Post-Policy &amp; Độ nhạy Dải băng
                  </h4>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-purple-600 rounded"></span>
                    <span className="text-slate-600 dark:text-slate-400">Post-Policy (Hậu can thiệp)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-slate-500 rounded border-dashed border-b border-slate-500"></span>
                    <span className="text-slate-600 dark:text-slate-400">Pre-Policy (Tiền can thiệp)</span>
                  </div>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Bandwidth Sensitivity Robustness Table */}
          {result.bandwidth_sensitivity && result.bandwidth_sensitivity.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Kiểm định Độ nhạy Bền vững Theo Độ rộng Băng (Bandwidth Robustness Matrix)
                </h4>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Kernel: {result.diagnostics?.kernel_type}
                </span>
              </div>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-100/70 dark:bg-slate-800 text-slate-700 dark:text-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Tỷ lệ Băng (Bandwidth Scale)</th>
                      <th className="py-2.5 px-3 font-semibold">Độ rộng h</th>
                      <th className="py-2.5 px-3 font-semibold">Ước lượng Diff-in-Disc (τ̂)</th>
                      <th className="py-2.5 px-3 font-semibold">Sai số chuẩn (SE)</th>
                      <th className="py-2.5 px-3 font-semibold">Khoảng tin cậy 95% CI</th>
                      <th className="py-2.5 px-3 font-semibold">Trị số p (p-value)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
                    {result.bandwidth_sensitivity.map((b) => (
                      <tr key={b.multiplier} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                          {b.multiplier}x h* {b.multiplier === 1.0 ? '(Chuẩn)' : ''}
                        </td>
                        <td className="py-2 px-3">{b.bandwidth.toFixed(2)}</td>
                        <td className="py-2 px-3 font-bold text-purple-600 dark:text-purple-400">
                          {b.tau_estimate > 0 ? '+' : ''}{b.tau_estimate.toFixed(4)}
                        </td>
                        <td className="py-2 px-3">±{b.se.toFixed(4)}</td>
                        <td className="py-2 px-3">[{b.ci_95[0].toFixed(3)}, {b.ci_95[1].toFixed(3)}]</td>
                        <td className="py-2 px-3">{getPValueBadge(b.p_value)}</td>
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
                  <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    Báo cáo khoa học chuẩn APA 7th &amp; Kinh tế lượng bán thực nghiệm
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={copyNarrativeToClipboard}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition-colors"
                  >
                    {copiedNarrative ? <Check className="w-3.5 h-3.5 text-purple-600" /> : <Copy className="w-3.5 h-3.5" />}
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
