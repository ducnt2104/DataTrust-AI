import React, { useState } from 'react';
import {
  Network,
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
  Cpu,
  Boxes,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import type {
  ClusterDMLRequest,
  ClusterDMLResult
} from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface ClusterDMLCardProps {
  surveyId: string;
  questions: QuestionOption[];
}

export const ClusterDMLCard: React.FC<ClusterDMLCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'likert'].includes(q.question_type)
  );

  const [clusterQId, setClusterQId] = useState<string>(
    questions[0]?.id || ''
  );
  const [treatmentQId, setTreatmentQId] = useState<string>(
    numericQuestions[0]?.id || questions[1]?.id || ''
  );
  const [outcomeQId, setOutcomeQId] = useState<string>(
    numericQuestions[1]?.id || numericQuestions[0]?.id || ''
  );
  const [covariateQIds, setCovariateQIds] = useState<string[]>(
    numericQuestions.slice(2, 5).map((q) => q.id)
  );

  const [nSplits, setNSplits] = useState<number>(5);
  const [mlModel, setMlModel] = useState<'random_forest' | 'gradient_boost' | 'ridge'>('random_forest');
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ClusterDMLResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const toggleCovariate = (id: string) => {
    setCovariateQIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!clusterQId || !treatmentQId || !outcomeQId) {
      setError('Vui lòng chọn đầy đủ biến cụm (Cluster ID), biến can thiệp (Treatment), và biến kết quả (Outcome).');
      return;
    }
    if (clusterQId === treatmentQId || clusterQId === outcomeQId || treatmentQId === outcomeQId) {
      setError('Các biến phân tích không được trùng nhau.');
      return;
    }
    if (covariateQIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến kiểm soát (Covariate) để điều chỉnh phi tuyến.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: ClusterDMLRequest = {
        cluster_question_id: clusterQId,
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: covariateQIds,
        n_splits: nSplits,
        ml_model: mlModel,
        alpha_level: alphaLevel,
        scope
      };

      const res = await api.runClusterDML(surveyId, payload);
      setResult(res);
    } catch (err: any) {
      console.error('Error running Cluster-DML analysis:', err);
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Không thể thực hiện ước lượng Cluster-DML. Vui lòng kiểm tra lại số lượng cụm độc lập (tối thiểu 4 cụm).'
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
    a.download = `DataTrust_Cluster_DML_Report_${surveyId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getPValueBadge = (pval?: number) => {
    if (pval === undefined || pval === null) return null;
    if (pval < 0.001) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
          p &lt; .001 ***
        </span>
      );
    }
    if (pval < 0.01) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
          p = {pval.toFixed(3)} **
        </span>
      );
    }
    if (pval < 0.05) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400">
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
          <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <Boxes className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Cluster-Robust Double Machine Learning Engine (Cluster-DML)
              </h3>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-100 dark:bg-blue-950/70 text-blue-700 dark:text-blue-300">
                DataTrust JoE 2022
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Phân chia cụm chéo (Cluster-Split Cross-Fitting) và ước lượng sai số chuẩn vững trước tự tương quan nội cụm (Chiang, Kato, Ma, &amp; Sasaki 2022)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Đang phân chia cụm chéo DML...' : 'Chạy Mô Hình Cluster-DML'}
          </button>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 my-6">
        {/* Cluster Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến định danh Cụm (Cluster ID c) <span className="text-rose-500">*</span>
          </label>
          <select
            value={clusterQId}
            onChange={(e) => setClusterQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Phòng ban, chi nhánh, trường học, tỉnh/thành, hoặc nhóm phỏng vấn viên
          </p>
        </div>

        {/* Treatment Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến Can thiệp (Treatment D) <span className="text-rose-500">*</span>
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Biến can thiệp nhị phân (1/0) hoặc liên tục
          </p>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
            Biến Kết quả (Outcome Y) <span className="text-rose-500">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Chỉ số đo lường định lượng cần phân tích tác động
          </p>
        </div>
      </div>

      {/* Covariates Checklist */}
      <div className="mb-6">
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-2">
          Các biến kiểm soát phi tuyến (Covariates X_k) <span className="text-rose-500">*</span>
        </label>
        <div className="flex flex-wrap gap-2 p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40">
          {numericQuestions.map((q) => {
            const isSelected = covariateQIds.includes(q.id);
            const isRestricted = q.id === outcomeQId || q.id === treatmentQId || q.id === clusterQId;
            return (
              <button
                key={q.id}
                type="button"
                disabled={isRestricted}
                onClick={() => toggleCovariate(q.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                  isSelected
                    ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:border-blue-500'
                } ${isRestricted ? 'opacity-40 cursor-not-allowed' : ''}`}
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
            <Cpu className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Thuật toán ML:</span>
            <select
              value={mlModel}
              onChange={(e) => setMlModel(e.target.value as any)}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="random_forest">Random Forest (Rừng ngẫu nhiên)</option>
              <option value="gradient_boost">Gradient Boosting (Tăng cường độ dốc)</option>
              <option value="ridge">Ridge Regression (Hồi quy L2)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Số Folds Cụm (K):</span>
            <select
              value={nSplits}
              onChange={(e) => setNSplits(parseInt(e.target.value, 10))}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="3">3 Folds Cụm</option>
              <option value="4">4 Folds Cụm</option>
              <option value="5">5 Folds Cụm (Chuẩn)</option>
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
                  ? 'bg-blue-600 text-white shadow-sm'
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
                  ? 'bg-blue-600 text-white shadow-sm'
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
            <p className="font-semibold">Lỗi ước lượng Cluster-DML</p>
            <p className="mt-0.5 text-xs text-rose-700 dark:text-rose-400">{error}</p>
          </div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6">
          {/* 4 High-Impact KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Cluster-Robust Causal Effect */}
            <div className="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-blue-700 dark:text-blue-300 mb-1">
                <span className="font-bold">Hiệu ứng Can thiệp (Cluster-DML θ̂)</span>
                {getPValueBadge(result.estimates?.p_value_cluster)}
              </div>
              <div className="text-2xl font-black text-blue-900 dark:text-blue-200">
                {(result.estimates?.theta ?? 0) > 0 ? '+' : ''}
                {(result.estimates?.theta ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                SE Vững: ±{(result.estimates?.se_cluster ?? 0).toFixed(3)} | t = {(result.estimates?.t_stat_cluster ?? 0).toFixed(2)}
              </div>
            </div>

            {/* KPI 2: SE Inflation Factor */}
            <div className="p-4 rounded-xl bg-rose-50/60 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 shadow-xs">
              <div className="flex items-center justify-between text-xs text-rose-700 dark:text-rose-300 mb-1">
                <span>Hệ số Giãn Sai số (SE Inflation)</span>
                <span className="text-[11px] font-bold text-rose-700 dark:text-rose-400">
                  SE_c / SE_naive
                </span>
              </div>
              <div className="text-2xl font-black text-rose-900 dark:text-rose-200">
                {(result.estimates?.se_inflation_ratio ?? 0).toFixed(2)}x
              </div>
              <div className="text-xs text-rose-700 dark:text-rose-300 mt-1">
                Naive SE: ±{(result.estimates?.se_naive ?? 0).toFixed(3)} (Bị thu hẹp giả tạo)
              </div>
            </div>

            {/* KPI 3: Intra-Cluster Correlation (ICC) */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Tương quan Nội cụm (ICC)</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {result.diagnostics?.num_clusters} Cụm
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {(result.diagnostics?.intra_cluster_correlation_icc ?? 0).toFixed(3)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Quy mô TB: {(result.diagnostics?.avg_cluster_size ?? 0).toFixed(1)} mẫu/cụm (Min {result.diagnostics?.min_cluster_size}, Max {result.diagnostics?.max_cluster_size})
              </div>
            </div>

            {/* KPI 4: ML Nuisance Predictability */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>Độ chính xác Nuisance ML</span>
                <span className="text-[11px] font-medium uppercase text-slate-600 dark:text-slate-300">
                  {result.diagnostics?.ml_algorithm}
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                R²_Y = {(result.diagnostics?.r2_outcome_ml ?? 0).toFixed(2)}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                R²_D = {(result.diagnostics?.r2_treatment_ml ?? 0).toFixed(2)} | {result.diagnostics?.k_folds} Folds Cụm
              </div>
            </div>
          </div>

          {/* SVG Visualizer Panel */}
          {result.svg_visualization && (
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    So sánh Forest Plot (Cluster-DML vs Naive) &amp; Đòn bẩy Điểm số Cụm
                  </h4>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-blue-600 rounded"></span>
                    <span className="text-slate-600 dark:text-slate-400">Cluster-Robust</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-orange-500 rounded"></span>
                    <span className="text-slate-600 dark:text-slate-400">Naive I.I.D.</span>
                  </div>
                </div>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Cluster Profiles Table */}
          {result.cluster_profiles && result.cluster_profiles.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Hồ sơ Đòn bẩy Điểm số Từng Cụm (Cluster Leverage &amp; Score Contribution ψ_c)
                </h4>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {result.cluster_profiles.length} cụm quan sát
                </span>
              </div>
              <div className="overflow-x-auto max-h-60">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-100/70 dark:bg-slate-800 text-slate-700 dark:text-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Tên Cụm (Cluster ID)</th>
                      <th className="py-2.5 px-3 font-semibold">Quy mô mẫu (N_c)</th>
                      <th className="py-2.5 px-3 font-semibold">TB Can thiệp D̄_c</th>
                      <th className="py-2.5 px-3 font-semibold">TB Kết quả Ȳ_c</th>
                      <th className="py-2.5 px-3 font-semibold">Điểm số Cụm (ψ_c)</th>
                      <th className="py-2.5 px-3 font-semibold">Tỷ trọng Phương sai</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
                    {result.cluster_profiles.map((cp) => (
                      <tr key={cp.cluster_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                          {cp.cluster_id}
                        </td>
                        <td className="py-2 px-3">{cp.sample_size}</td>
                        <td className="py-2 px-3">{cp.treatment_mean.toFixed(2)}</td>
                        <td className="py-2 px-3">{cp.outcome_mean.toFixed(2)}</td>
                        <td className="py-2 px-3 font-bold text-blue-600 dark:text-blue-400">
                          {cp.cluster_score > 0 ? '+' : ''}{cp.cluster_score.toFixed(3)}
                        </td>
                        <td className="py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">
                          {cp.contribution_pct.toFixed(2)}%
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
                  <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    Báo cáo khoa học chuẩn APA 7th &amp; Kinh tế lượng học máy
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={copyNarrativeToClipboard}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition-colors"
                  >
                    {copiedNarrative ? <Check className="w-3.5 h-3.5 text-blue-600" /> : <Copy className="w-3.5 h-3.5" />}
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
