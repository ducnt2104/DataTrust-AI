import React, { useState } from 'react';
import {
  PieChart,
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
  TrendingUp,
  Scale,
  Users,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import type {
  RIFOaxacaDecompositionRequest,
  RIFOaxacaDecompositionResult
} from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface RIFOaxacaDecompositionCardProps {
  surveyId: string;
  questions: QuestionOption[];
}

export const RIFOaxacaDecompositionCard: React.FC<RIFOaxacaDecompositionCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'likert'].includes(q.question_type)
  );

  const [groupQId, setGroupQId] = useState<string>(
    questions[0]?.id || ''
  );
  const [outcomeQId, setOutcomeQId] = useState<string>(
    numericQuestions[0]?.id || ''
  );
  const [covariateQIds, setCovariateQIds] = useState<string[]>(
    numericQuestions.slice(1, 4).map((q) => q.id)
  );
  const [refGroupVal, setRefGroupVal] = useState<string>('');
  const [bootstrapReps, setBootstrapReps] = useState<number>(100);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RIFOaxacaDecompositionResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const toggleCovariate = (id: string) => {
    setCovariateQIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!groupQId || !outcomeQId) {
      setError('Vui lòng chọn biến phân nhóm (Group Variable) và biến kết quả (Outcome Variable).');
      return;
    }
    if (groupQId === outcomeQId) {
      setError('Biến phân nhóm và biến kết quả không được trùng nhau.');
      return;
    }
    if (covariateQIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến kiểm soát/đặc điểm (Covariate) để phân rã.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: RIFOaxacaDecompositionRequest = {
        group_question_id: groupQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: covariateQIds,
        reference_group_val: refGroupVal.trim() ? refGroupVal.trim() : undefined,
        target_quantiles: [0.10, 0.25, 0.50, 0.75, 0.90],
        num_bootstrap_reps: bootstrapReps,
        alpha_level: alphaLevel,
        scope
      };

      const res = await api.runRIFOaxacaDecomposition(surveyId, payload);
      setResult(res);
    } catch (err: any) {
      console.error('Error running RIF Oaxaca-Blinder decomposition:', err);
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Không thể thực hiện phân rã RIF Oaxaca-Blinder. Vui lòng kiểm tra lại cấu hình biến và số lượng mẫu của 2 nhóm.'
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
    a.download = `DataTrust_RIF_Oaxaca_Report_${surveyId}.md`;
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
          <div className="p-2.5 rounded-lg bg-teal-500/10 text-teal-600 dark:text-teal-400">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Distributional Oaxaca-Blinder &amp; RIF Decomposition Engine
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-teal-100 dark:bg-teal-950/70 text-teal-700 dark:text-teal-300">
                DataTrust Econometrica 2009
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Phân rã chênh lệch phân phối (Quantiles &amp; Median) thành thành phần Đặc điểm (Endowments) và Định giá/Hệ số (Wage Structure) (Firpo et al. 2009, 2018)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Đang phân rã RIF...' : 'Chạy Phân Rã RIF Oaxaca'}
          </button>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 my-6">
        {/* Group Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến phân nhóm so sánh (Group G) <span className="text-rose-500">*</span>
          </label>
          <select
            value={groupQId}
            onChange={(e) => setGroupQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-teal-500"
          >
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Giới tính (Nam/Nữ), khu vực (Thành thị/Nông thôn), phòng ban, hoặc thâm niên
          </p>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến kết quả định lượng (Outcome Y) <span className="text-rose-500">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-teal-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Thu nhập, mức độ hài lòng, doanh số, năng suất, điểm đánh giá
          </p>
        </div>

        {/* Reference Group Value */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Giá trị Nhóm Tham Chiếu (Group A Label)
          </label>
          <input
            type="text"
            placeholder="Tự động (VD: 1, Nam, Male, Urban)"
            value={refGroupVal}
            onChange={(e) => setRefGroupVal(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-teal-500"
          />
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Bỏ trống để tự động chọn nhóm đầu tiên làm nhóm chuẩn
          </p>
        </div>
      </div>

      {/* Covariates Checklist */}
      <div className="mb-6">
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-2">
          Các biến đặc điểm giải thích (Covariates X_k) <span className="text-rose-500">*</span>
        </label>
        <div className="flex flex-wrap gap-2 p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40">
          {numericQuestions.map((q) => {
            const isSelected = covariateQIds.includes(q.id);
            const isOutcomeOrGroup = q.id === outcomeQId || q.id === groupQId;
            return (
              <button
                key={q.id}
                type="button"
                disabled={isOutcomeOrGroup}
                onClick={() => toggleCovariate(q.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                  isSelected
                    ? 'bg-teal-600 text-white border-teal-600 shadow-xs'
                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:border-teal-500'
                } ${isOutcomeOrGroup ? 'opacity-40 cursor-not-allowed' : ''}`}
              >
                {isSelected && <Check className="w-3.5 h-3.5 inline mr-1" />}
                {q.title}
              </button>
            );
          })}
        </div>
      </div>

      {/* Secondary Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700/60 mb-6 text-sm">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
              Bootstrap Replicates:
            </span>
            <select
              value={bootstrapReps}
              onChange={(e) => setBootstrapReps(parseInt(e.target.value, 10))}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="50">50 lượt (Nhanh)</option>
              <option value="100">100 lượt (Chuẩn)</option>
              <option value="150">150 lượt (Chính xác cao)</option>
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
          <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Phạm vi:</span>
          <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-white dark:bg-slate-800">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                scope === 'all'
                  ? 'bg-teal-600 text-white shadow-sm'
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
                  ? 'bg-teal-600 text-white shadow-sm'
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
            <p className="font-semibold">Lỗi phân rã RIF Oaxaca-Blinder</p>
            <p className="mt-0.5 text-xs text-rose-700 dark:text-rose-400">{error}</p>
          </div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6">
          {/* 4 High-Impact KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Median Total Gap */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Tổng Chênh lệch Trung vị (Median Gap)</span>
                <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                  {result.group_a_label} vs {result.group_b_label}
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {(result.median_rif_estimates?.total_median_gap ?? 0) > 0 ? '+' : ''}
                {(result.median_rif_estimates?.total_median_gap ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Mean Gap: {(result.mean_decomposition?.total_mean_gap ?? 0).toFixed(2)} | Mẫu: {result.sample_size}
              </div>
            </div>

            {/* KPI 2: Explained Endowments */}
            <div className="p-4 rounded-xl bg-teal-50/60 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-teal-700 dark:text-teal-300 mb-1">
                <span>Đặc điểm Giải thích được (Endowments)</span>
                <span className="font-bold">
                  {(result.median_rif_estimates?.explained_pct ?? 0).toFixed(1)}%
                </span>
              </div>
              <div className="text-2xl font-black text-teal-900 dark:text-teal-200">
                {(result.median_rif_estimates?.explained_endowments ?? 0) > 0 ? '+' : ''}
                {(result.median_rif_estimates?.explained_endowments ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-teal-700 dark:text-teal-300 mt-1">
                Chênh lệch do khác biệt về trình độ, thâm niên, năng lực
              </div>
            </div>

            {/* KPI 3: Unexplained Structure / Coefficients */}
            <div className="p-4 rounded-xl bg-rose-50/60 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-rose-700 dark:text-rose-300 mb-1">
                <span>Định giá Chưa giải thích (Coefficients)</span>
                {getPValueBadge(result.median_rif_estimates?.unexplained_p_value)}
              </div>
              <div className="text-2xl font-black text-rose-900 dark:text-rose-200">
                {(result.median_rif_estimates?.unexplained_coefficients ?? 0) > 0 ? '+' : ''}
                {(result.median_rif_estimates?.unexplained_coefficients ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-rose-700 dark:text-rose-300 mt-1">
                Tỷ trọng: {(result.median_rif_estimates?.unexplained_pct ?? 0).toFixed(1)}% | SE: ±{(result.median_rif_estimates?.unexplained_se ?? 0).toFixed(3)}
              </div>
            </div>

            {/* KPI 4: Glass Ceiling Diagnostic */}
            <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-indigo-700 dark:text-indigo-300 mb-1">
                <span>Chẩn đoán Trần kính (Glass Ceiling)</span>
                <span className="font-semibold text-indigo-900 dark:text-indigo-200">
                  Δ_90 - Δ_10
                </span>
              </div>
              <div className="text-2xl font-black text-indigo-900 dark:text-indigo-200">
                {(result.glass_ceiling_diagnostics?.gap_p90_minus_p10 ?? 0) > 0 ? '+' : ''}
                {(result.glass_ceiling_diagnostics?.gap_p90_minus_p10 ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-indigo-700 dark:text-indigo-300 mt-1 truncate">
                {result.glass_ceiling_diagnostics?.diagnostic_label}
              </div>
            </div>
          </div>

          {/* SVG Visualizer Panel */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    Đường cong Chênh lệch Phân vị RIF &amp; Phân rã Đóng góp của Biến
                  </h4>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-indigo-600 rounded"></span>
                    <span className="text-slate-600 dark:text-slate-400">Total Gap</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-teal-600 rounded border-dashed border-b border-teal-600"></span>
                    <span className="text-slate-600 dark:text-slate-400">Explained (Đặc điểm)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-rose-600 rounded border-dashed border-b border-rose-600"></span>
                    <span className="text-slate-600 dark:text-slate-400">Unexplained (Định giá)</span>
                  </div>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Detailed Covariates Decomposition Table */}
          {result.detailed_covariates && result.detailed_covariates.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Bảng Phân rã Chi tiết Từng Biến Kiểm soát (Detailed Covariate Decomposition at Median)
                </h4>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {result.detailed_covariates.length} biến
                </span>
              </div>
              <div className="overflow-x-auto max-h-64">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-100/70 dark:bg-slate-800 text-slate-700 dark:text-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Tên Biến</th>
                      <th className="py-2.5 px-3 font-semibold">TB Nhóm A ({result.group_a_label})</th>
                      <th className="py-2.5 px-3 font-semibold">TB Nhóm B ({result.group_b_label})</th>
                      <th className="py-2.5 px-3 font-semibold">Chênh lệch TB (ΔX)</th>
                      <th className="py-2.5 px-3 font-semibold">Đặc điểm (Explained)</th>
                      <th className="py-2.5 px-3 font-semibold">Định giá (Unexplained)</th>
                      <th className="py-2.5 px-3 font-semibold">Tổng đóng góp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
                    {result.detailed_covariates.map((c) => (
                      <tr key={c.variable_name} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                          {c.variable_name}
                        </td>
                        <td className="py-2 px-3">{c.mean_group_a.toFixed(2)}</td>
                        <td className="py-2 px-3">{c.mean_group_b.toFixed(2)}</td>
                        <td className="py-2 px-3">{c.mean_diff.toFixed(2)}</td>
                        <td className="py-2 px-3 font-semibold text-teal-600 dark:text-teal-400">
                          {c.explained_effect > 0 ? '+' : ''}{c.explained_effect.toFixed(3)}
                        </td>
                        <td className="py-2 px-3 font-semibold text-rose-600 dark:text-rose-400">
                          {c.unexplained_effect > 0 ? '+' : ''}{c.unexplained_effect.toFixed(3)}
                        </td>
                        <td className="py-2 px-3 font-bold text-slate-900 dark:text-white">
                          {c.total_effect > 0 ? '+' : ''}{c.total_effect.toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Quantile Decomposition Curve Table */}
          {result.quantile_decomposition_curve && result.quantile_decomposition_curve.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Hồ sơ Phân rã Qua Các Mốc Phân vị (Quantile RIF Decomposition Profiles)
                </h4>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {result.quantile_decomposition_curve.length} phân vị
                </span>
              </div>
              <div className="overflow-x-auto max-h-60">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-100/70 dark:bg-slate-800 text-slate-700 dark:text-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Phân vị (Quantile)</th>
                      <th className="py-2.5 px-3 font-semibold">Nhóm A ({result.group_a_label})</th>
                      <th className="py-2.5 px-3 font-semibold">Nhóm B ({result.group_b_label})</th>
                      <th className="py-2.5 px-3 font-semibold">Tổng Chênh lệch (Total Gap)</th>
                      <th className="py-2.5 px-3 font-semibold">Đặc điểm (Explained)</th>
                      <th className="py-2.5 px-3 font-semibold">Tỷ lệ Explained %</th>
                      <th className="py-2.5 px-3 font-semibold">Định giá (Unexplained)</th>
                      <th className="py-2.5 px-3 font-semibold">Tỷ lệ Unexplained %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
                    {result.quantile_decomposition_curve.map((q) => (
                      <tr key={q.quantile} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                          p{Math.round(q.quantile * 100)} ({q.quantile === 0.5 ? 'Trung vị' : ''})
                        </td>
                        <td className="py-2 px-3">{q.group_a_val.toFixed(2)}</td>
                        <td className="py-2 px-3">{q.group_b_val.toFixed(2)}</td>
                        <td className="py-2 px-3 font-bold text-slate-900 dark:text-white">
                          {q.total_gap > 0 ? '+' : ''}{q.total_gap.toFixed(3)}
                        </td>
                        <td className="py-2 px-3 font-semibold text-teal-600 dark:text-teal-400">
                          {q.explained_gap > 0 ? '+' : ''}{q.explained_gap.toFixed(3)}
                        </td>
                        <td className="py-2 px-3">{q.explained_pct.toFixed(1)}%</td>
                        <td className="py-2 px-3 font-semibold text-rose-600 dark:text-rose-400">
                          {q.unexplained_gap > 0 ? '+' : ''}{q.unexplained_gap.toFixed(3)}
                        </td>
                        <td className="py-2 px-3">{q.unexplained_pct.toFixed(1)}%</td>
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
                  <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    Báo cáo khoa học chuẩn APA 7th &amp; Kinh tế lượng phân phối
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={copyNarrativeToClipboard}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition-colors"
                  >
                    {copiedNarrative ? <Check className="w-3.5 h-3.5 text-teal-600" /> : <Copy className="w-3.5 h-3.5" />}
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
