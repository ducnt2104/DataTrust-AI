import React, { useState } from 'react';
import {
  ConformalOptimalTransportResult,
  ConformalOptimalTransportRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Boxes,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertCircle,
  Sparkles,
  Sliders,
  Layers,
  Activity,
  CheckCircle2,
  TrendingUp,
  Percent,
  Compass,
  Zap,
  BarChart3,
  Scale,
  ShieldCheck,
  ArrowRightLeft
} from 'lucide-react';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface Props {
  surveyId: string;
  questions: QuestionSummary[];
}

export const ConformalOptimalTransportCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [regEps, setRegEps] = useState<number>(0.05);
  const [kappa, setKappa] = useState<number>(0.50);
  const [conformalAlpha, setConformalAlpha] = useState<number>(0.10);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ConformalOptimalTransportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleToggleCovariate = (qId: string) => {
    if (selectedCovariates.includes(qId)) {
      setSelectedCovariates(selectedCovariates.filter(id => id !== qId));
    } else {
      setSelectedCovariates([...selectedCovariates, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId) {
      setError('Vui lòng chọn biến kết quả Y và biến can thiệp nhị phân D.');
      return;
    }

    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả Y và biến can thiệp D không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: ConformalOptimalTransportRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      reg_eps: regEps,
      covariate_weight_kappa: kappa,
      conformal_alpha: conformalAlpha,
      scope
    };

    try {
      const res = await api.runConformalOptimalTransport(surveyId, payload);
      if (res.status === 'ERROR') {
        setError(res.message || 'Lỗi khi thực hiện Conformal Optimal Transport.');
        setResult(null);
      } else if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Cỡ mẫu chưa đủ để thực hiện Optimal Transport.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối máy chủ.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setOutcomeQId('');
    setTreatmentQId('');
    setSelectedCovariates([]);
    setRegEps(0.05);
    setKappa(0.50);
    setConformalAlpha(0.10);
    setResult(null);
    setError(null);
  };

  const handleCopyNarrative = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const summ = result?.overall_summary;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400">
              <Boxes className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                Conformal Optimal Transport &amp; Distributional Alignment (COT-CDA)
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                  Cuturi (2013) NeurIPS · Courty (2017) TPAMI
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Vận chuyển khối lượng tối ưu Wasserstein entropy-regularized (Sinkhorn) giữa phân phối Can thiệp &amp; Đối chứng. Điền khuyết phản thực tế Monge kèm dải dự báo chuẩn Conformal hữu hạn mẫu.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700/80 rounded-lg transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Làm mới
          </button>
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !outcomeQId || !treatmentQId}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow transition-all"
          >
            {loading ? (
              <>
                <Activity className="w-3.5 h-3.5 animate-spin" />
                Đang hội tụ Sinkhorn &amp; Conformal...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Vận Chuyển Tối Ưu (COT)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        {/* Outcome Y */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
            1. Biến Kết Quả Y (Outcome)
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option value="">-- Chọn câu hỏi đo lường Y --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Biến liên tục để căn chỉnh phân phối.</span>
        </div>

        {/* Treatment D */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            2. Biến Phân Nhóm D (0/1)
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option value="">-- Chọn câu hỏi can thiệp D --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">1 = Nhóm Can Thiệp, 0 = Nhóm Đối Chứng.</span>
        </div>

        {/* Sinkhorn Regularization Epsilon */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-indigo-400" />
            3. Entropy Epsilon &amp; Kappa Trọng Số
          </label>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={regEps}
              onChange={(e) => setRegEps(parseFloat(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
            >
              <option value={0.01}>&epsilon; = 0.01 (Chặt)</option>
              <option value={0.05}>&epsilon; = 0.05 (Chuẩn)</option>
              <option value={0.10}>&epsilon; = 0.10 (Mịn)</option>
            </select>
            <select
              value={kappa}
              onChange={(e) => setKappa(parseFloat(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
            >
              <option value={0.0}>&kappa; = 0.0 (Chỉ Y)</option>
              <option value={0.5}>&kappa; = 0.5 (Y + X)</option>
              <option value={1.0}>&kappa; = 1.0 (X nặng)</option>
            </select>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">Thông số hội tụ thuật toán Sinkhorn.</span>
        </div>

        {/* Conformal Level & Scope */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            4. Độ Tin Cậy Conformal &amp; Mẫu
          </label>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={conformalAlpha}
              onChange={(e) => setConformalAlpha(parseFloat(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
            >
              <option value={0.10}>90% Coverage</option>
              <option value={0.05}>95% Coverage</option>
              <option value={0.20}>80% Coverage</option>
            </select>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
            >
              <option value="all">Tất cả mẫu</option>
              <option value="verified_clean">Chỉ mẫu sạch</option>
            </select>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">Bảo đảm phủ không phụ thuộc phân phối.</span>
        </div>
      </div>

      {/* Covariates Multi-select */}
      <div className="bg-slate-950/30 p-4 rounded-lg border border-slate-800/80 mb-6">
        <label className="text-xs font-semibold text-slate-300 flex items-center justify-between mb-2">
          <span className="flex items-center gap-1.5 text-purple-400">
            <Layers className="w-3.5 h-3.5" />
            Đồng Biến Kiểm Soát Không Gian Chi Phí X ({selectedCovariates.length} đã chọn)
          </span>
          <span className="text-[11px] text-slate-500">Tùy chọn ghép cặp đa chiều (Coupling Penalty)</span>
        </label>
        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-1">
          {numericQuestions
            .filter(q => q.id !== outcomeQId && q.id !== treatmentQId)
            .map(q => {
              const active = selectedCovariates.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => handleToggleCovariate(q.id)}
                  className={`px-2.5 py-1 rounded text-xs transition-colors flex items-center gap-1.5 ${
                    active
                      ? 'bg-purple-950/80 border border-purple-600/80 text-purple-300'
                      : 'bg-slate-800/80 border border-slate-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {active && <Check className="w-3 h-3 text-purple-400" />}
                  {q.title}
                </button>
              );
            })}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-red-950/50 border border-red-800/80 rounded-lg text-xs text-red-300 flex items-center gap-2 mb-6">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && summ && (
        <div className="space-y-6 pt-2">
          {/* Top 4 KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Wasserstein Distance */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-cyan-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400 block mb-1">
                Khoảng Cách Wasserstein-2 (W2)
              </span>
              <div className="text-2xl font-black text-slate-100">
                {summ.wasserstein_2_distance}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Độ lệch phân phối thực tế giữa 2 nhóm
              </div>
              <div className="text-[11px] text-cyan-400/90 font-mono mt-2">
                Chi phí vận chuyển khối lượng tối ưu
              </div>
            </div>

            {/* Optimal Transport ATE & ATT */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-blue-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-400 block mb-1">
                Hiệu Ứng Can Thiệp OT-ATE &amp; ATT
              </span>
              <div className="text-2xl font-black text-blue-300">
                {summ.optimal_transport_ate > 0 ? `+${summ.optimal_transport_ate}` : summ.optimal_transport_ate}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                OT-ATT: {summ.optimal_transport_att > 0 ? `+${summ.optimal_transport_att}` : summ.optimal_transport_att}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                OT-ATU: {summ.optimal_transport_atu > 0 ? `+${summ.optimal_transport_atu}` : summ.optimal_transport_atu}
              </div>
            </div>

            {/* Conformal Prediction Band */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-emerald-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 block mb-1">
                Dải Dung Sai Conformal ({summ.conformal_coverage_guarantee_pct}%)
              </span>
              <div className="text-2xl font-black text-emerald-300">
                &plusmn;{summ.conformal_half_width_delta}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Bảo đảm độ phủ phân phối hữu hạn mẫu
              </div>
              <div className="text-[11px] text-emerald-400/80 mt-2 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Không phụ thuộc phân phối (Distribution-free)</span>
              </div>
            </div>

            {/* Sample Balance */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Cỡ Mẫu Khảo Sát &amp; Phản Thực Tế
              </span>
              <div className="text-lg font-bold text-slate-200">
                N<sub>1</sub>={summ.n_treated} · N<sub>0</sub>={summ.n_control}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Điền khuyết: {summ.mean_outcome_control_counterfactual}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                Gốc Đối Chứng: {summ.mean_outcome_control_observed} · Can Thiệp: {summ.mean_outcome_treated}
              </div>
            </div>
          </div>

          {/* Quantile Shifts Table */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-slate-200">
                  Bảng Dịch Chuyển Phân Vị Phản Thực Tế (Quantile Counterfactual Shifts)
                </span>
              </div>
              <span className="text-[11px] text-slate-500">So sánh phân vị thực nghiệm vs phân vị tái tạo Monge</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Phân vị (Quantile)</th>
                    <th className="py-2.5 px-4">Đối Chứng Quan Sát Q(Y0)</th>
                    <th className="py-2.5 px-4">Đối Chứng Phản Thực Tế Q(Y1 cf)</th>
                    <th className="py-2.5 px-4">Can Thiệp Quan Sát Q(Y1)</th>
                    <th className="py-2.5 px-4">Dịch chuyển phân vị (&Delta;Q)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {summ.quantiles.map((q, idx) => (
                    <tr key={q} className="hover:bg-slate-800/40">
                      <td className="py-2 px-4 font-bold text-slate-300 font-sans">
                        {Math.round(q * 100)}% ({q === 0.5 ? 'Trung vị / Median' : `Phân vị ${Math.round(q * 100)}`})
                      </td>
                      <td className="py-2 px-4 text-rose-300">{summ.control_observed_quantiles[idx]}</td>
                      <td className="py-2 px-4 font-bold text-emerald-300">{summ.control_counterfactual_quantiles[idx]}</td>
                      <td className="py-2 px-4 text-cyan-300">{summ.treated_quantiles[idx]}</td>
                      <td className="py-2 px-4 font-bold text-slate-100">
                        {summ.counterfactual_quantile_shifts[idx] > 0
                          ? `+${summ.counterfactual_quantile_shifts[idx]}`
                          : summ.counterfactual_quantile_shifts[idx]}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Scientific Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-hidden shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-semibold text-slate-200">
                    Trực Quan Hóa Khoa Học: Ma Trận Ghép Cặp &Pi;* (Sinkhorn Heatmap) &amp; Đường Cong Phân Phối Tích Lũy CDF Kèm Dải Conformal
                  </span>
                </div>
                <span className="text-[11px] text-slate-500">Vector SVG 780x360</span>
              </div>
              <div
                className="w-full flex justify-center bg-slate-950 rounded-lg p-2 overflow-x-auto"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Báo Cáo Thuyết Minh Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyNarrative}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 bg-slate-800 px-2 py-1 rounded transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      Sao chép
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/80 p-3 rounded border border-slate-800/80">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
