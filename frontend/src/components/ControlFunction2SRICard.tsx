import React, { useState } from 'react';
import {
  GitMerge,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
  TrendingUp,
  ShieldCheck,
  Sliders,
  BarChart3,
  Scale,
  Binary
} from 'lucide-react';
import { api } from '../api/client';
import {
  ControlFunction2SRIResult,
  ControlFunction2SRIRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const ControlFunction2SRICard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [instrumentQIds, setInstrumentQIds] = useState<string[]>([]);
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [outcomeFamily, setOutcomeFamily] = useState<'logistic' | 'linear' | 'poisson'>('logistic');
  const [nBootstraps, setNBootstraps] = useState<number>(100);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ControlFunction2SRIResult | null>(null);
  const [activeTab, setActiveTab] = useState<'effects' | 'firstStage' | 'models' | 'theory' | 'apa'>('effects');
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'slider' || q.question_type === 'single_choice'
  );

  const handleInstrumentToggle = (qid: string) => {
    if (instrumentQIds.includes(qid)) {
      setInstrumentQIds(instrumentQIds.filter(id => id !== qid));
    } else {
      setInstrumentQIds([...instrumentQIds, qid]);
    }
  };

  const handleCovariateToggle = (qid: string) => {
    if (covariateQIds.includes(qid)) {
      setCovariateQIds(covariateQIds.filter(id => id !== qid));
    } else {
      setCovariateQIds([...covariateQIds, qid]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId || !outcomeQId) {
      setError('Vui lòng chọn đầy đủ biến Can thiệp (D) và biến Kết quả (Y).');
      return;
    }
    if (instrumentQIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến Công cụ ngoại sinh (Instrument Z) để nhận dạng mô hình.');
      return;
    }
    if (treatmentQId === outcomeQId || instrumentQIds.includes(treatmentQId) || instrumentQIds.includes(outcomeQId)) {
      setError('Biến can thiệp, kết quả và công cụ ngoại sinh phải hoàn toàn phân biệt.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: ControlFunction2SRIRequest = {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        instrument_question_ids: instrumentQIds,
        covariate_question_ids: covariateQIds.length > 0 ? covariateQIds : undefined,
        outcome_family: outcomeFamily,
        n_bootstraps: nBootstraps,
        scope: scope
      };

      const res = await api.runControlFunction2SRI(surveyId, payload);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi thực thi phân tích Two-Stage Residual Inclusion (2SRI).');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8 text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <GitMerge className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                Two-Stage Residual Inclusion (2SRI) &amp; Control Function Causal Engine
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-medium">
                  Terza et al. (2008)
                </span>
              </h3>
              <p className="text-sm text-slate-400">
                Ước lượng tác động nhân quả phi tuyến khi có nội sinh bằng hàm kiểm soát và phần dư giai đoạn một (Wooldridge 2010 MIT Press).
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Double Consistency
          </span>
          <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-blue-400" />
            Hausman Endogeneity Test
          </span>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-6 bg-slate-800/40 p-5 rounded-lg border border-slate-800/80">
        {/* Treatment Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
            <Binary className="w-3.5 h-3.5 text-indigo-400" />
            Biến Can Thiệp Nội Sinh (D) *
          </label>
          <select
            value={treatmentQId}
            onChange={e => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi can thiệp (D) --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            Biến Kết Quả Cần Đánh Giá (Y) *
          </label>
          <select
            value={outcomeQId}
            onChange={e => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi kết quả (Y) --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Model Family */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-purple-400" />
            Cấu Trúc Mô Hình Kết Quả (Family)
          </label>
          <select
            value={outcomeFamily}
            onChange={e => setOutcomeFamily(e.target.value as any)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="logistic">Logistic (Kết quả nhị phân 0 / 1)</option>
            <option value="linear">Tuyến tính OLS (Kết quả liên tục)</option>
            <option value="poisson">Poisson (Kết quả đếm không âm)</option>
          </select>
        </div>

        {/* Excluded Instruments (Z) */}
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            Biến Công Cụ Ngoại Sinh Loại Trừ (Instruments Z) * (Chọn ít nhất 1)
          </label>
          <div className="max-h-28 overflow-y-auto bg-slate-900 border border-slate-700 rounded-lg p-2.5 space-y-1.5">
            {numericQuestions
              .filter(q => q.id !== treatmentQId && q.id !== outcomeQId)
              .map(q => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={instrumentQIds.includes(q.id)}
                    onChange={() => handleInstrumentToggle(q.id)}
                    className="rounded bg-slate-800 border-slate-600 text-indigo-500 focus:ring-indigo-500"
                  />
                  <span>{q.title}</span>
                </label>
              ))}
          </div>
        </div>

        {/* Exogenous Covariates (X) */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            Biến Kiểm Soát Ngoại Sinh (Covariates X)
          </label>
          <div className="max-h-28 overflow-y-auto bg-slate-900 border border-slate-700 rounded-lg p-2.5 space-y-1.5">
            {numericQuestions
              .filter(q => q.id !== treatmentQId && q.id !== outcomeQId && !instrumentQIds.includes(q.id))
              .map(q => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={covariateQIds.includes(q.id)}
                    onChange={() => handleCovariateToggle(q.id)}
                    className="rounded bg-slate-800 border-slate-600 text-indigo-500 focus:ring-indigo-500"
                  />
                  <span>{q.title}</span>
                </label>
              ))}
          </div>
        </div>

        {/* Bootstrap replications & Scope */}
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Mẫu Bootstrap (SE):</label>
            <select
              value={nBootstraps}
              onChange={e => setNBootstraps(Number(e.target.value))}
              className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value={50}>50 lần lặp</option>
              <option value={100}>100 lần lặp (Khuyến nghị)</option>
              <option value={200}>200 lần lặp (Độ chính xác cao)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Bộ lọc mẫu:</label>
            <select
              value={scope}
              onChange={e => setScope(e.target.value as any)}
              className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="all">Tất cả phản hồi hợp lệ</option>
              <option value="verified_clean">Chỉ mẫu đã xác thực sạch</option>
            </select>
          </div>
        </div>

        <div className="md:col-span-2 flex items-end justify-end">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full md:w-auto px-6 py-2.5 rounded-lg font-semibold text-sm bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Đang ước lượng 2SRI &amp; Control Function...
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                Ước Lượng Tác Động Nhân Quả (2SRI)
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {/* ATE Card */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">ATE (Trung Bình Toàn Dân Số)</span>
              <div className="text-2xl font-bold text-indigo-400 mt-1">
                {result.causal_effects.ate.estimate > 0 ? '+' : ''}
                {result.causal_effects.ate.estimate.toFixed(4)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                95% CI [{result.causal_effects.ate.ci_lower.toFixed(3)}, {result.causal_effects.ate.ci_upper.toFixed(3)}]
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                p = {result.causal_effects.ate.p_value.toFixed(4)}
              </div>
            </div>

            {/* ATT Card */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">ATT (Nhóm Can Thiệp)</span>
              <div className="text-2xl font-bold text-purple-400 mt-1">
                {result.causal_effects.att.estimate > 0 ? '+' : ''}
                {result.causal_effects.att.estimate.toFixed(4)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                95% CI [{result.causal_effects.att.ci_lower.toFixed(3)}, {result.causal_effects.att.ci_upper.toFixed(3)}]
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                p = {result.causal_effects.att.p_value.toFixed(4)}
              </div>
            </div>

            {/* First Stage F Card */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Độ Mạnh Công Cụ (F-Stat)</span>
              <div className={`text-2xl font-bold mt-1 ${result.first_stage.weak_instrument ? 'text-amber-400' : 'text-emerald-400'}`}>
                {result.first_stage.f_statistic.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {result.first_stage.weak_instrument ? 'Cảnh báo IV yếu (F < 10)' : 'Công cụ mạnh (F ≥ 10)'}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                R² = {result.first_stage.r_squared.toFixed(3)} • {result.first_stage.instrument_count} IVs
              </div>
            </div>

            {/* Endogeneity Test Card */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Kiểm Định Nội Sinh (ρ)</span>
              <div className={`text-2xl font-bold mt-1 ${result.endogeneity_test.is_endogenous ? 'text-rose-400' : 'text-blue-400'}`}>
                {result.endogeneity_test.residual_coefficient_rho.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                z = {result.endogeneity_test.z_statistic.toFixed(2)} (p = {result.endogeneity_test.p_value.toFixed(3)})
              </div>
              <div className={`text-[11px] font-semibold mt-0.5 ${result.endogeneity_test.is_endogenous ? 'text-rose-300' : 'text-slate-400'}`}>
                {result.endogeneity_test.is_endogenous ? 'Nội sinh có ý nghĩa (p < .05)' : 'Chưa bác bỏ ngoại sinh'}
              </div>
            </div>

            {/* Sample & Family Card */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Quy Mô &amp; Phân Phối</span>
              <div className="text-2xl font-bold text-slate-200 mt-1">
                N = {result.sample_size}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Can thiệp: {result.treated_count} • Đối chứng: {result.control_count}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 capitalize">
                {result.outcome_family} • {result.treatment_type}
              </div>
            </div>
          </div>

          {/* Responsive Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  Đồ Thị Vector Kép: Phân Phối Phần Dư Kiểm Soát &amp; Đối Chiếu Mô Hình
                </span>
                <span className="text-xs text-slate-500">
                  Panel A: û Residuals • Panel B: Naive vs 2SPS vs 2SRI
                </span>
              </div>
              <div
                className="w-full overflow-x-auto rounded-lg bg-slate-950 p-2 flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Tab Navigation */}
          <div className="border-b border-slate-800 flex gap-4">
            <button
              onClick={() => setActiveTab('effects')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'effects'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Hiệu Ứng Causal &amp; ASF
            </button>
            <button
              onClick={() => setActiveTab('firstStage')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'firstStage'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Cpu className="w-4 h-4" />
              Độ Mạnh Biến Công Cụ
            </button>
            <button
              onClick={() => setActiveTab('models')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'models'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Scale className="w-4 h-4" />
              So Sánh Mô Hình (Naive vs 2SPS vs 2SRI)
            </button>
            <button
              onClick={() => setActiveTab('theory')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'theory'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              Cơ Sở Phương Pháp Luận
            </button>
            <button
              onClick={() => setActiveTab('apa')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'apa'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Copy className="w-4 h-4" />
              Thuyết Minh APA 7th
            </button>
          </div>

          {/* Tab Content */}
          <div className="bg-slate-800/30 p-5 rounded-xl border border-slate-800">
            {/* Tab 1: Causal Effects */}
            {activeTab === 'effects' && (
              <div className="space-y-4">
                <div className="text-sm text-slate-300">
                  Ước lượng thông qua hàm cấu trúc trung bình (Average Structural Function - ASF) tích phân phân phối sai số kiểm soát:
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 border-collapse">
                    <thead>
                      <tr className="border-b border-slate-700 bg-slate-800/80 text-slate-200">
                        <th className="py-2.5 px-3">Chỉ Số Hiệu Ứng</th>
                        <th className="py-2.5 px-3">Ước Lượng Điểm</th>
                        <th className="py-2.5 px-3">Sai Số Chuẩn (Bootstrap SE)</th>
                        <th className="py-2.5 px-3">Khoảng Tin Cậy 95% CI</th>
                        <th className="py-2.5 px-3">Giá Trị p</th>
                        <th className="py-2.5 px-3">Ý Nghĩa Thống Kê</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      <tr className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 font-semibold text-indigo-300">ATE (Trung Bình Toàn Dân Số)</td>
                        <td className="py-2 px-3 font-mono font-bold text-white">{result.causal_effects.ate.estimate.toFixed(4)}</td>
                        <td className="py-2 px-3 font-mono">{result.causal_effects.ate.bootstrap_se.toFixed(4)}</td>
                        <td className="py-2 px-3 font-mono">[{result.causal_effects.ate.ci_lower.toFixed(4)}, {result.causal_effects.ate.ci_upper.toFixed(4)}]</td>
                        <td className="py-2 px-3 font-mono">{result.causal_effects.ate.p_value.toFixed(4)}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${result.causal_effects.ate.p_value < 0.05 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300'}`}>
                            {result.causal_effects.ate.p_value < 0.05 ? 'Có ý nghĩa (p < .05)' : 'Không ý nghĩa'}
                          </span>
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 font-semibold text-purple-300">ATT (Trung Bình Nhóm Can Thiệp)</td>
                        <td className="py-2 px-3 font-mono font-bold text-white">{result.causal_effects.att.estimate.toFixed(4)}</td>
                        <td className="py-2 px-3 font-mono">{result.causal_effects.att.bootstrap_se.toFixed(4)}</td>
                        <td className="py-2 px-3 font-mono">[{result.causal_effects.att.ci_lower.toFixed(4)}, {result.causal_effects.att.ci_upper.toFixed(4)}]</td>
                        <td className="py-2 px-3 font-mono">{result.causal_effects.att.p_value.toFixed(4)}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${result.causal_effects.att.p_value < 0.05 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300'}`}>
                            {result.causal_effects.att.p_value < 0.05 ? 'Có ý nghĩa (p < .05)' : 'Không ý nghĩa'}
                          </span>
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 text-slate-400">Hệ số Cấu trúc Mô hình (α_2SRI)</td>
                        <td className="py-2 px-3 font-mono text-slate-300">{result.causal_effects.structural_alpha.toFixed(4)}</td>
                        <td className="py-2 px-3 font-mono">{result.causal_effects.structural_alpha_se.toFixed(4)}</td>
                        <td className="py-2 px-3 text-slate-500">-</td>
                        <td className="py-2 px-3 text-slate-500">-</td>
                        <td className="py-2 px-3 text-slate-500">Hệ số log-odds / Poisson / OLS</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 2: First Stage */}
            {activeTab === 'firstStage' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Thống Kê Kiểm Định F Giai Đoạn 1</span>
                    <div className="text-xl font-bold text-white mt-1">{result.first_stage.f_statistic.toFixed(3)}</div>
                    <p className="text-xs text-slate-400 mt-1">Ngưỡng Stock-Yogo: F ≥ 10.0</p>
                  </div>
                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Hệ Số Xác Định R² Giai Đoạn 1</span>
                    <div className="text-xl font-bold text-white mt-1">{result.first_stage.r_squared.toFixed(4)}</div>
                    <p className="text-xs text-slate-400 mt-1">Độ giải thích biến thiên can thiệp</p>
                  </div>
                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Trạng Thái Nhận Dạng IV</span>
                    <div className={`text-xl font-bold mt-1 ${result.first_stage.weak_instrument ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {result.first_stage.weak_instrument ? 'Công Cụ Yếu (Weak IV)' : 'Công Cụ Mạnh (Strong IV)'}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Số công cụ loại trừ: {result.first_stage.instrument_count}</p>
                  </div>
                </div>

                <div className="text-xs text-slate-400">
                  Danh sách biến công cụ sử dụng trong giai đoạn 1: {result.first_stage.instruments.join(', ')}.
                </div>
              </div>
            )}

            {/* Tab 3: Model Comparison */}
            {activeTab === 'models' && (
              <div className="space-y-4">
                <div className="text-sm text-slate-300">
                  Đối chiếu giữa các mô hình ước lượng để đánh giá mức độ khử thiên lệch của Two-Stage Residual Inclusion (2SRI) so với Two-Stage Predictor Substitution (2SPS) và mô hình hồi quy ngoại sinh chuẩn:
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 border-collapse">
                    <thead>
                      <tr className="border-b border-slate-700 bg-slate-800/80 text-slate-200">
                        <th className="py-2.5 px-3">Mô Hình</th>
                        <th className="py-2.5 px-3">Hệ Số Can Thiệp (Coeff)</th>
                        <th className="py-2.5 px-3">Đánh Giá Thiên Lệch Học Thuật</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {result.model_comparison.map((m, idx) => (
                        <tr key={idx} className={idx === 2 ? 'bg-indigo-950/30' : 'hover:bg-slate-800/40'}>
                          <td className="py-2.5 px-3 font-semibold text-white flex items-center gap-2">
                            {idx === 2 && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                            {m.model}
                          </td>
                          <td className="py-2.5 px-3 font-mono font-bold text-slate-200">
                            {m.treatment_coefficient.toFixed(4)}
                          </td>
                          <td className="py-2.5 px-3 text-slate-300">
                            <span className={`px-2 py-0.5 rounded text-[11px] ${
                              idx === 2 ? 'bg-emerald-500/20 text-emerald-300 font-semibold' : 'bg-slate-700 text-slate-300'
                            }`}>
                              {m.bias_risk}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 4: Theory */}
            {activeTab === 'theory' && (
              <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
                <h4 className="font-bold text-sm text-white flex items-center gap-2">
                  <Scale className="w-4 h-4 text-indigo-400" />
                  Tại Sao Two-Stage Predictor Substitution (2SPS) Thất Bại Trong Mô Hình Phi Tuyến?
                </h4>
                <p>
                  Trong kinh tế lượng tuyến tính, phương pháp 2SLS thay thế biến nội sinh D bằng giá trị dự báo D̂. Tuy nhiên, theo chứng minh định lượng của <strong>Terza, Basu, &amp; Rathouz (2008 J. Health Econ)</strong> và <strong>Wooldridge (2010)</strong>, đối với các mô hình cấu trúc phi tuyến (như Logistic, Probit, Poisson, Negative Binomial):
                </p>
                <div className="p-3 bg-slate-900 border border-slate-800 rounded font-mono text-[11px] text-amber-300">
                  E[Y | X, D] ≠ G(X'β + α · D̂)
                </div>
                <p>
                  Việc thay thế D bằng D̂ (2SPS) dẫn đến ước lượng <em>không nhất quán tiệm cận (asymptotically inconsistent)</em> và làm sai lệch dấu của hiệu ứng nhân quả.
                </p>

                <h4 className="font-bold text-sm text-white pt-2">
                  Giải Pháp Kiểm Soát Phần Dư (Two-Stage Residual Inclusion - 2SRI)
                </h4>
                <p>
                  Thay vì thay thế D, phương pháp 2SRI giữ nguyên D quan sát được và bổ sung trực tiếp phần dư giai đoạn một û vào phương trình cấu trúc giai đoạn hai:
                </p>
                <div className="p-3 bg-slate-900 border border-slate-800 rounded font-mono text-[11px] text-emerald-300">
                  E[Y | D, X, û] = G(α · D + X'β + ρ · û)
                </div>
                <p>
                  Thuật toán này bảo đảm hai ưu điểm vượt trội:
                </p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><strong>Kiểm định nội sinh chính xác (Exact Hausman-type Test):</strong> Hệ số ρ đo lường tương quan giữa sai số can thiệp và sai số kết quả. Kiểm định t đối với H₀: ρ = 0 là kiểm định chính xác xem can thiệp có thực sự nội sinh hay không.</li>
                  <li><strong>Hàm Cấu Trúc Trung Bình (Average Structural Function - ASF):</strong> Bằng cách tích phân loại bỏ phần dư û theo Blundell &amp; Powell (2004), ASF thu được hiệu ứng can thiệp nhân quả phi thiên lệch (unconfounded ATE &amp; ATT).</li>
                </ul>
              </div>
            )}

            {/* Tab 5: APA Narrative */}
            {activeTab === 'apa' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Thuyết minh học thuật chuẩn mực theo định dạng APA 7th Edition:</span>
                  <button
                    onClick={handleCopyAPA}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        Đã sao chép!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Sao chép thuyết minh
                      </>
                    )}
                  </button>
                </div>
                <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-xs font-serif leading-relaxed text-slate-300 whitespace-pre-wrap">
                  {result.apa_narrative}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
