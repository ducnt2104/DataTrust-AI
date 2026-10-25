import React, { useState } from 'react';
import {
  LocalInstrumentalVariablesResult,
  LocalInstrumentalVariablesRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  GitMerge,
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
  ArrowRight
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

export const LocalInstrumentalVariablesCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedInstruments, setSelectedInstruments] = useState<string[]>([]);
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [nGridPoints, setNGridPoints] = useState<number>(40);
  const [trimQuantile, setTrimQuantile] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<LocalInstrumentalVariablesResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleToggleInstrument = (qId: string) => {
    if (selectedInstruments.includes(qId)) {
      setSelectedInstruments(selectedInstruments.filter(id => id !== qId));
    } else {
      setSelectedInstruments([...selectedInstruments, qId]);
    }
  };

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

    if (selectedInstruments.length === 0) {
      setError('Vui lòng chọn ít nhất một biến công cụ (Instrument Z).');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: LocalInstrumentalVariablesRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      instrument_question_ids: selectedInstruments,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      n_grid_points: nGridPoints,
      trim_quantile: trimQuantile,
      alpha_level: 0.05,
      scope
    };

    try {
      const res = await api.runLocalInstrumentalVariables(surveyId, payload);
      if (res.status === 'ERROR') {
        setError(res.message || 'Lỗi khi thực hiện ước lượng LIV / MTE.');
        setResult(null);
      } else if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Cỡ mẫu chưa đủ để thực hiện ước lượng LIV/MTE.');
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
    setSelectedInstruments([]);
    setSelectedCovariates([]);
    setNGridPoints(40);
    setTrimQuantile(0.05);
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
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
              <GitMerge className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                Local Instrumental Variables &amp; Marginal Treatment Effects (LIV / MTE)
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                  Heckman &amp; Vytlacil (2005) Econometrica
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Mô hình lựa chọn Roy tổng quát với Tính không đồng nhất thiết yếu (Essential Heterogeneity). Ước lượng đường cong MTE(u) và hợp nhất toàn bộ các tham số chính sách (ATE, ATT, ATU, LATE, PRTE).
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
            disabled={loading || !outcomeQId || !treatmentQId || selectedInstruments.length === 0}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow transition-all"
          >
            {loading ? (
              <>
                <Activity className="w-3.5 h-3.5 animate-spin" />
                Đang vi phân LIV &amp; Tích phân...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Ước lượng LIV &amp; MTE
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
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            1. Biến Kết Quả Y (Outcome)
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">-- Chọn câu hỏi đo lường Y --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Biến số liên tục (e.g. Thu nhập, Hiệu quả, Điểm số).</span>
        </div>

        {/* Treatment D */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            2. Can Thiệp Nhị Phân D (0/1)
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">-- Chọn câu hỏi can thiệp D --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Giá trị nhị phân (0 = Đối chứng, 1 = Can thiệp).</span>
        </div>

        {/* MTE Resolution */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-sky-400" />
            3. Độ Phân Giải MTE Curve
          </label>
          <select
            value={nGridPoints}
            onChange={(e) => setNGridPoints(parseInt(e.target.value, 10))}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200"
          >
            <option value={30}>30 điểm đánh giá (Nhanh)</option>
            <option value={40}>40 điểm đánh giá (Chuẩn)</option>
            <option value={60}>60 điểm đánh giá (Chi tiết cao)</option>
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Lưới điểm kháng cự U<sub>D</sub> &isin; (0, 1).</span>
        </div>

        {/* Trimming & Scope */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-purple-400" />
            4. Hỗ Trợ Chung &amp; Phạm Vi
          </label>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={trimQuantile}
              onChange={(e) => setTrimQuantile(parseFloat(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
            >
              <option value={0.02}>Xén 2%</option>
              <option value={0.05}>Xén 5% (Chuẩn)</option>
              <option value={0.10}>Xén 10%</option>
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
          <span className="text-[11px] text-slate-500 mt-1 block">Loại bỏ đuôi mật độ xác suất cực trị.</span>
        </div>
      </div>

      {/* Instruments & Covariates Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Instruments Z */}
        <div className="bg-slate-950/30 p-4 rounded-lg border border-slate-800/80">
          <label className="text-xs font-semibold text-slate-300 flex items-center justify-between mb-2">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <Zap className="w-3.5 h-3.5" />
              Biến Công Cụ Ngoại Sinh Z ({selectedInstruments.length} đã chọn)
            </span>
            <span className="text-[11px] text-slate-500">Tạo dịch chuyển xu hướng P(Z)</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-1">
            {numericQuestions
              .filter(q => q.id !== outcomeQId && q.id !== treatmentQId && !selectedCovariates.includes(q.id))
              .map(q => {
                const active = selectedInstruments.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => handleToggleInstrument(q.id)}
                    className={`px-2.5 py-1 rounded text-xs transition-colors flex items-center gap-1.5 ${
                      active
                        ? 'bg-emerald-950/80 border border-emerald-600/80 text-emerald-300'
                        : 'bg-slate-800/80 border border-slate-700 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {active && <Check className="w-3 h-3 text-emerald-400" />}
                    {q.title}
                  </button>
                );
              })}
          </div>
        </div>

        {/* Covariates X */}
        <div className="bg-slate-950/30 p-4 rounded-lg border border-slate-800/80">
          <label className="text-xs font-semibold text-slate-300 flex items-center justify-between mb-2">
            <span className="flex items-center gap-1.5 text-purple-400">
              <Layers className="w-3.5 h-3.5" />
              Đồng Biến Kiểm Soát Confounding X ({selectedCovariates.length} đã chọn)
            </span>
            <span className="text-[11px] text-slate-500">Tùy chọn</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-1">
            {numericQuestions
              .filter(q => q.id !== outcomeQId && q.id !== treatmentQId && !selectedInstruments.includes(q.id))
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
            {/* ATT vs ATE */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-emerald-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 block mb-1">
                ATT (Nhóm Nhận Can Thiệp)
              </span>
              <div className="text-2xl font-black text-slate-100">
                {summ.att.estimate > 0 ? `+${summ.att.estimate}` : summ.att.estimate}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {summ.att.se} · ATE: {summ.ate.estimate}
              </div>
              <div className="text-[11px] text-emerald-400/90 font-mono mt-2 flex items-center gap-1">
                <span>Sorting: {summ.sorting_on_gains_att_minus_ate > 0 ? `+${summ.sorting_on_gains_att_minus_ate}` : summ.sorting_on_gains_att_minus_ate}</span>
              </div>
            </div>

            {/* LATE (Compliers) */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-amber-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-400 block mb-1">
                LATE (Nhóm Tuân Thủ Biên)
              </span>
              <div className="text-2xl font-black text-amber-300">
                {summ.late.estimate > 0 ? `+${summ.late.estimate}` : summ.late.estimate}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {summ.late.se} · 2SLS: {summ.standard_2sls.estimate}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                Hợp nhất trong vùng biến thiên của Z
              </div>
            </div>

            {/* Essential Heterogeneity Verdict */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-sky-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block mb-1">
                Kiểm Định Tính Không Đồng Nhất
              </span>
              <div className="text-sm font-bold text-slate-100 mt-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-sky-400" />
                <span className="truncate">{summ.heterogeneity_verdict}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Wald Stat: {summ.wald_test_essential_heterogeneity}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                p-value: {summ.wald_test_p_value} ({summ.essential_heterogeneity_present ? 'Bác bỏ giả định đồng nhất' : 'Chưa đủ bằng chứng'})
              </div>
            </div>

            {/* Propensity Common Support */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Vùng Hỗ Trợ Chung Propensity P(Z)
              </span>
              <div className="text-xl font-black text-slate-200">
                [{summ.propensity_support[0]}, {summ.propensity_support[1]}]
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Mean P(Z): {summ.propensity_mean}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                N = {summ.sample_size} bản ghi khảo sát
              </div>
            </div>
          </div>

          {/* Unified Causal Parameter Comparison Table */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-slate-200">
                  Bảng So Sánh Toàn Bộ Các Tham Số Chính Sách Nhân Quả (Unified Policy Parameters)
                </span>
              </div>
              <span className="text-[11px] text-slate-500">Tích phân MTE(u) theo trọng số Heckman-Vytlacil</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Tham số chính sách</th>
                    <th className="py-2.5 px-4">Ước lượng</th>
                    <th className="py-2.5 px-4">Sai số chuẩn (SE)</th>
                    <th className="py-2.5 px-4">Khoảng tin cậy 95%</th>
                    <th className="py-2.5 px-4">Ý nghĩa kinh tế lượng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr className="hover:bg-slate-800/40">
                    <td className="py-2 px-4 font-semibold text-emerald-300 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      ATT (Average Effect on the Treated)
                    </td>
                    <td className="py-2 px-4 font-mono font-bold text-slate-100">{summ.att.estimate}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">{summ.att.se}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">[{summ.att.ci_95?.[0]}, {summ.att.ci_95?.[1]}]</td>
                    <td className="py-2 px-4 text-slate-400">Lợi ích thực tế của những cá nhân chủ động tham gia can thiệp</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40">
                    <td className="py-2 px-4 font-semibold text-sky-300 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-sky-400" />
                      ATE (Average Treatment Effect)
                    </td>
                    <td className="py-2 px-4 font-mono font-bold text-slate-100">{summ.ate.estimate}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">{summ.ate.se}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">[{summ.ate.ci_95?.[0]}, {summ.ate.ci_95?.[1]}]</td>
                    <td className="py-2 px-4 text-slate-400">Hiệu ứng trung bình nếu áp dụng ngẫu nhiên trên toàn bộ quần thể</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40">
                    <td className="py-2 px-4 font-semibold text-purple-300 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-purple-400" />
                      ATU (Treatment Effect on Untreated)
                    </td>
                    <td className="py-2 px-4 font-mono font-bold text-slate-100">{summ.atu.estimate}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">{summ.atu.se}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">[{summ.atu.ci_95?.[0]}, {summ.atu.ci_95?.[1]}]</td>
                    <td className="py-2 px-4 text-slate-400">Hiệu ứng tiềm năng nếu nhóm chưa tham gia được mở rộng can thiệp</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40">
                    <td className="py-2 px-4 font-semibold text-amber-300 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-amber-400" />
                      LATE (Local Average Treatment Effect)
                    </td>
                    <td className="py-2 px-4 font-mono font-bold text-slate-100">{summ.late.estimate}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">{summ.late.se}</td>
                    <td className="py-2 px-4 font-mono text-slate-400">[{summ.late.ci_95?.[0]}, {summ.late.ci_95?.[1]}]</td>
                    <td className="py-2 px-4 text-slate-400">Hiệu ứng trên nhóm đối tượng thay đổi hành vi nhờ biến công cụ Z</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 text-slate-400">
                    <td className="py-2 px-4 font-semibold text-slate-300 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-slate-400" />
                      Linear 2SLS (Conventional IV)
                    </td>
                    <td className="py-2 px-4 font-mono text-slate-200">{summ.standard_2sls.estimate}</td>
                    <td className="py-2 px-4 font-mono">{summ.standard_2sls.se}</td>
                    <td className="py-2 px-4 font-mono">-</td>
                    <td className="py-2 px-4">Ước lượng bình phương bé nhất 2 giai đoạn truyền thống</td>
                  </tr>
                  <tr className="hover:bg-slate-800/40 text-slate-400">
                    <td className="py-2 px-4 font-semibold text-slate-400 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-slate-500" />
                      Conventional OLS Benchmark
                    </td>
                    <td className="py-2 px-4 font-mono text-slate-300">{summ.ols_benchmark.estimate}</td>
                    <td className="py-2 px-4 font-mono">{summ.ols_benchmark.se}</td>
                    <td className="py-2 px-4 font-mono">-</td>
                    <td className="py-2 px-4">Hồi quy tuyến tính trực tiếp (chưa hiệu chỉnh chọn mẫu &amp; nội sinh)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Scientific Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-hidden shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-slate-200">
                    Trực Quan Hóa Khoa Học: Đường Cong MTE(u) &amp; Biểu Đồ Rừng Hợp Nhất Tham Số Chính Sách
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
