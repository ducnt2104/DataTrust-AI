import React, { useState } from 'react';
import {
  TrendingUp,
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
  ArrowRight,
  Filter
} from 'lucide-react';
import { api } from '../api/client';
import { MTERequest, MTEResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface MTECardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const MTECard: React.FC<MTECardProps> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedInstruments, setSelectedInstruments] = useState<string[]>([]);
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [polyDegree, setPolyDegree] = useState<number>(3);
  const [nBootstraps, setNBootstraps] = useState<number>(300);
  const [policyShiftPct, setPolicyShiftPct] = useState<number>(0.15);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MTEResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleInstrument = (qid: string) => {
    setSelectedInstruments((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId || selectedInstruments.length === 0) {
      setError('Vui lòng chọn Biến kết quả (Y), Biến can thiệp nội sinh (D) và ít nhất 1 Biến công cụ ngoại sinh (Z).');
      return;
    }
    if (outcomeQId === treatmentQId || selectedInstruments.includes(outcomeQId) || selectedInstruments.includes(treatmentQId)) {
      setError('Biến kết quả, biến can thiệp và các biến công cụ không được trùng lặp.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: MTERequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      instrument_question_ids: selectedInstruments,
      covariate_question_ids: selectedCovariates.filter(
        (id) => id !== outcomeQId && id !== treatmentQId && !selectedInstruments.includes(id)
      ),
      poly_degree: polyDegree,
      alpha_level: 0.05,
      n_bootstraps: nBootstraps,
      policy_shift_pct: policyShiftPct,
      scope
    };

    try {
      const data = await api.runMTE(surveyId, payload);
      if (data.status === 'ERROR' || data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Không thể tính toán Marginal Treatment Effects.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối máy chủ khi tính toán MTE.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const candidateQuestions = questions.filter(
    (q) => q.id !== outcomeQId && q.id !== treatmentQId
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-8 transition-all hover:border-violet-200">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-violet-950 via-purple-900 to-indigo-950 px-6 py-5 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-violet-500/30 text-violet-200 border border-violet-400/30 tracking-wide uppercase">
                Kinh tế lượng Cấu trúc Nobel
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                DataTrust Verified
              </span>
            </div>
            <h3 className="text-xl font-bold mt-1 text-white tracking-tight flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-violet-400" />
              Marginal Treatment Effects &amp; Local Instrumental Variables (MTE / LIV)
            </h3>
            <p className="text-sm text-violet-200/90 mt-1 max-w-3xl leading-relaxed">
              Khung lý thuyết Heckman &amp; Vytlacil (1999, 2005 <i>Econometrica</i>) thống nhất toàn bộ các tham số nhân quả
              (ATE, ATT, ATU, LATE, PRTE) dưới sự bất đồng nhất phản ứng điều trị và tự lựa chọn (Roy Selection).
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={loading || !outcomeQId || !treatmentQId || selectedInstruments.length === 0}
              className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all shadow-sm ${
                loading || !outcomeQId || !treatmentQId || selectedInstruments.length === 0
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  : 'bg-violet-600 hover:bg-violet-500 text-white shadow-violet-950/20 active:scale-95'
              }`}
            >
              {loading ? (
                <>
                  <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                  Đang ước lượng Bootstrap...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2 fill-current" />
                  Ước lượng MTE (Heckman 2005)
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="p-6 bg-slate-50 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Outcome Question (Y) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>1. Biến kết quả (Y)</span>
              <span className="text-violet-600 font-mono">Outcome</span>
            </label>
            <select
              value={outcomeQId}
              onChange={(e) => setOutcomeQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-violet-500 focus:border-violet-500"
            >
              <option value="">-- Chọn câu hỏi đo lường kết quả --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title} {q.question_type ? `(${q.question_type})` : ''}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Biến thu nhập, điểm hiệu suất, hoặc chỉ số hài lòng.</p>
          </div>

          {/* Treatment Question (D) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>2. Biến can thiệp nội sinh (D)</span>
              <span className="text-amber-600 font-mono">Endogenous</span>
            </label>
            <select
              value={treatmentQId}
              onChange={(e) => setTreatmentQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-violet-500 focus:border-violet-500"
            >
              <option value="">-- Chọn biến can thiệp nhị phân --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === outcomeQId}>
                  {q.title}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Cá nhân tự quyết định tham gia dựa trên lợi ích và kháng cự.</p>
          </div>
        </div>

        {/* Instruments and Covariates selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Instruments (Z) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>3. Biến công cụ ngoại sinh (Z)</span>
              <span className="text-xs text-emerald-600 font-semibold">{selectedInstruments.length} đã chọn</span>
            </label>
            <div className="max-h-36 overflow-y-auto space-y-1.5 pr-2">
              {candidateQuestions.map((q) => (
                <label
                  key={q.id}
                  className="flex items-center space-x-2 text-xs text-gray-700 hover:bg-slate-50 p-1.5 rounded cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedInstruments.includes(q.id)}
                    onChange={() => toggleInstrument(q.id)}
                    className="rounded text-emerald-600 focus:ring-emerald-500 h-4 w-4"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Hỗ trợ đa biến công cụ dịch chuyển xác suất tham gia P(Z).</p>
          </div>

          {/* Covariates (X) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>4. Biến kiểm soát tiền can thiệp (X)</span>
              <span className="text-xs text-violet-600 font-semibold">{selectedCovariates.length} đã chọn</span>
            </label>
            <div className="max-h-36 overflow-y-auto space-y-1.5 pr-2">
              {candidateQuestions
                .filter((q) => !selectedInstruments.includes(q.id))
                .map((q) => (
                  <label
                    key={q.id}
                    className="flex items-center space-x-2 text-xs text-gray-700 hover:bg-slate-50 p-1.5 rounded cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedCovariates.includes(q.id)}
                      onChange={() => toggleCovariate(q.id)}
                      className="rounded text-violet-600 focus:ring-violet-500 h-4 w-4"
                    />
                    <span className="truncate">{q.title}</span>
                  </label>
                ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Được chuẩn hóa và đưa vào hàm xu hướng và phương trình kết quả.</p>
          </div>
        </div>

        {/* Hyperparameters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-3 rounded-lg border border-gray-200">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
              Bậc Đa thức (Polynomial Degree)
            </label>
            <select
              value={polyDegree}
              onChange={(e) => setPolyDegree(Number(e.target.value))}
              className="w-full text-xs border-gray-300 rounded-md focus:ring-violet-500 focus:border-violet-500"
            >
              <option value={2}>Bậc 2 (Quadratic / MTE Tuyến tính)</option>
              <option value={3}>Bậc 3 (Cubic / Khuyến nghị)</option>
              <option value={4}>Bậc 4 (Quartic / Phi tuyến cao)</option>
            </select>
          </div>

          <div className="bg-white p-3 rounded-lg border border-gray-200">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
              Bootstrap Replications
            </label>
            <select
              value={nBootstraps}
              onChange={(e) => setNBootstraps(Number(e.target.value))}
              className="w-full text-xs border-gray-300 rounded-md focus:ring-violet-500 focus:border-violet-500"
            >
              <option value={100}>100 lần lặp (Nhanh)</option>
              <option value={300}>300 lần lặp (Tiêu chuẩn)</option>
              <option value={500}>500 lần lặp (Xuất bản)</option>
            </select>
          </div>

          <div className="bg-white p-3 rounded-lg border border-gray-200">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
              Dịch chuyển Chính sách (PRTE)
            </label>
            <select
              value={policyShiftPct}
              onChange={(e) => setPolicyShiftPct(Number(e.target.value))}
              className="w-full text-xs border-gray-300 rounded-md focus:ring-violet-500 focus:border-violet-500"
            >
              <option value={0.1}>+10% Mở rộng khuyến khích</option>
              <option value={0.15}>+15% Mở rộng (Tiêu chuẩn)</option>
              <option value={0.2}>+20% Mở rộng khuyến khích</option>
              <option value={0.3}>+30% Mở rộng mạnh</option>
            </select>
          </div>

          <div className="bg-white p-3 rounded-lg border border-gray-200">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
              Phạm vi dữ liệu
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
              className="w-full text-xs border-gray-300 rounded-md focus:ring-violet-500 focus:border-violet-500"
            >
              <option value="all">Toàn bộ phản hồi</option>
              <option value="verified_clean">Chỉ mẫu sạch xác thực</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 mx-6 mt-6 bg-rose-50 border border-rose-200 rounded-lg flex items-center space-x-3 text-rose-700">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Result Display */}
      {result && result.status === 'SUCCESS' && (
        <div className="p-6 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* ATE */}
            <div className="bg-gradient-to-br from-violet-50 to-white p-4 rounded-xl border border-violet-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-violet-700 uppercase tracking-wider">ATE (Quần thể)</span>
                <Award className="w-4 h-4 text-violet-500" />
              </div>
              <div className="text-2xl font-black text-violet-950 mt-1">
                {result.parameters?.ate.estimate !== undefined
                  ? `${result.parameters.ate.estimate > 0 ? '+' : ''}${result.parameters.ate.estimate.toFixed(3)}`
                  : 'N/A'}
              </div>
              <div className="text-xs text-violet-600 mt-0.5">
                95% CI [{result.parameters?.ate.ci_lower.toFixed(2)}, {result.parameters?.ate.ci_upper.toFixed(2)}]
              </div>
            </div>

            {/* ATT */}
            <div className="bg-gradient-to-br from-emerald-50 to-white p-4 rounded-xl border border-emerald-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">ATT (Nhóm Điều trị)</span>
                <TrendingUp className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-black text-emerald-950 mt-1">
                {result.parameters?.att.estimate !== undefined
                  ? `${result.parameters.att.estimate > 0 ? '+' : ''}${result.parameters.att.estimate.toFixed(3)}`
                  : 'N/A'}
              </div>
              <div className="text-xs text-emerald-600 mt-0.5">
                95% CI [{result.parameters?.att.ci_lower.toFixed(2)}, {result.parameters?.att.ci_upper.toFixed(2)}]
              </div>
            </div>

            {/* ATU */}
            <div className="bg-gradient-to-br from-amber-50 to-white p-4 rounded-xl border border-amber-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">ATU (Nhóm Chưa Điều trị)</span>
                <Activity className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-black text-amber-950 mt-1">
                {result.parameters?.atu.estimate !== undefined
                  ? `${result.parameters.atu.estimate > 0 ? '+' : ''}${result.parameters.atu.estimate.toFixed(3)}`
                  : 'N/A'}
              </div>
              <div className="text-xs text-amber-600 mt-0.5">
                95% CI [{result.parameters?.atu.ci_lower.toFixed(2)}, {result.parameters?.atu.ci_upper.toFixed(2)}]
              </div>
            </div>

            {/* PRTE */}
            <div className="bg-gradient-to-br from-sky-50 to-white p-4 rounded-xl border border-sky-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-sky-700 uppercase tracking-wider">PRTE (Hiệu ứng Chính sách)</span>
                <Layers className="w-4 h-4 text-sky-500" />
              </div>
              <div className="text-2xl font-black text-sky-950 mt-1">
                {result.parameters?.prte.estimate !== undefined
                  ? `${result.parameters.prte.estimate > 0 ? '+' : ''}${result.parameters.prte.estimate.toFixed(3)}`
                  : 'N/A'}
              </div>
              <div className="text-xs text-sky-600 mt-0.5">
                Mở rộng {intPolicyShift(policyShiftPct)}% xác suất tham gia
              </div>
            </div>
          </div>

          {/* Selection Sorting Banner */}
          <div className="bg-slate-100 p-3.5 rounded-lg border border-slate-200 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs text-slate-800">
              <Filter className="w-4 h-4 text-violet-600" />
              <span className="font-semibold">Mô hình Lựa chọn Roy (Selection Sorting):</span>
              <span className="font-mono text-violet-900 bg-violet-100/70 px-2 py-0.5 rounded">
                {result.selection_sorting_pattern}
              </span>
            </div>
            <div className="text-xs text-slate-500 font-mono">
              Hỗ trợ chung P(Z): [{result.common_support?.p_min.toFixed(2)}, {result.common_support?.p_max.toFixed(2)}]
            </div>
          </div>

          {/* Unified Parameters Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
            <div className="px-5 py-3.5 bg-slate-50 border-b border-gray-200 flex items-center justify-between">
              <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <Sliders className="w-4 h-4 text-violet-600" />
                Hệ Thống Tham Số Causal Thống Nhất Tích Phân từ MTE (Heckman &amp; Vytlacil 2005)
              </h4>
              <span className="text-xs text-gray-500 font-mono">N = {result.sample_size} | Bootstrap B = {result.bootstrap_replications}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100/70 text-xs font-semibold text-slate-600 uppercase border-b border-gray-200">
                  <tr>
                    <th className="py-3 px-4">Tham số Causal</th>
                    <th className="py-3 px-4">Hàm Trọng số Tích phân w(u)</th>
                    <th className="py-3 px-4">Ước lượng (Δ)</th>
                    <th className="py-3 px-4">Sai số chuẩn (SE)</th>
                    <th className="py-3 px-4">z-statistic</th>
                    <th className="py-3 px-4">p-value</th>
                    <th className="py-3 px-4">Khoảng tin cậy 95%</th>
                    <th className="py-3 px-4 text-center">Ý nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {/* ATE */}
                  {result.parameters?.ate && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-900">ATE (Average Treatment Effect)</td>
                      <td className="py-3 px-4 text-xs font-mono text-gray-500">w_ATE(u) = 1 (Đồng đều)</td>
                      <td className="py-3 px-4 font-mono font-bold text-violet-800">{result.parameters.ate.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.ate.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.ate.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.ate.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.parameters.ate.ci_lower.toFixed(3)}, {result.parameters.ate.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        <SignificanceBadge isSig={result.parameters.ate.is_significant} />
                      </td>
                    </tr>
                  )}

                  {/* ATT */}
                  {result.parameters?.att && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-900">ATT (Effect on the Treated)</td>
                      <td className="py-3 px-4 text-xs font-mono text-gray-500">w_ATT(u) = Pr(P &gt; u) / E[P]</td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-800">{result.parameters.att.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.att.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.att.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.att.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.parameters.att.ci_lower.toFixed(3)}, {result.parameters.att.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        <SignificanceBadge isSig={result.parameters.att.is_significant} />
                      </td>
                    </tr>
                  )}

                  {/* ATU */}
                  {result.parameters?.atu && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-900">ATU (Effect on the Untreated)</td>
                      <td className="py-3 px-4 text-xs font-mono text-gray-500">w_ATU(u) = Pr(P ≤ u) / (1 - E[P])</td>
                      <td className="py-3 px-4 font-mono font-bold text-amber-800">{result.parameters.atu.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.atu.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.atu.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.atu.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.parameters.atu.ci_lower.toFixed(3)}, {result.parameters.atu.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        <SignificanceBadge isSig={result.parameters.atu.is_significant} />
                      </td>
                    </tr>
                  )}

                  {/* LATE */}
                  {result.parameters?.late && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-900">LATE (Interquartile Compliers)</td>
                      <td className="py-3 px-4 text-xs font-mono text-gray-500">1/(p_75 - p_25) trên [p_25, p_75]</td>
                      <td className="py-3 px-4 font-mono font-bold text-sky-800">{result.parameters.late.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.late.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.late.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.late.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.parameters.late.ci_lower.toFixed(3)}, {result.parameters.late.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        <SignificanceBadge isSig={result.parameters.late.is_significant} />
                      </td>
                    </tr>
                  )}

                  {/* PRTE */}
                  {result.parameters?.prte && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-900">PRTE (Policy-Relevant Effect)</td>
                      <td className="py-3 px-4 text-xs font-mono text-gray-500">(F_P(u) - F_P*(u)) / ΔE[P]</td>
                      <td className="py-3 px-4 font-mono font-bold text-indigo-800">{result.parameters.prte.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.prte.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.prte.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.parameters.prte.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.parameters.prte.ci_lower.toFixed(3)}, {result.parameters.prte.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        <SignificanceBadge isSig={result.parameters.prte.is_significant} />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Scientific SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
              <div className="px-5 py-3.5 bg-slate-50 border-b border-gray-200">
                <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-violet-600" />
                  Đồ Thị Khoa Học: Đường Cong MTE và Trọng Số Tích Phân w_ATT(u) / w_ATU(u)
                </h4>
              </div>
              <div
                className="p-4 flex justify-center bg-slate-900/5 overflow-x-auto"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Academic APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 rounded-xl border border-gray-200 p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-2">
                  <Info className="w-4 h-4 text-violet-600" />
                  Thuyết Minh Học Thuật Chuẩn APA 7th Edition (Heckman &amp; Vytlacil 2005)
                </h4>
                <button
                  onClick={handleCopyNarrative}
                  className="inline-flex items-center space-x-1.5 text-xs text-violet-600 hover:text-violet-800 font-medium px-2.5 py-1 bg-violet-50 hover:bg-violet-100 rounded-md transition-colors"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>{copied ? 'Đã sao chép!' : 'Sao chép văn bản'}</span>
                </button>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed font-serif bg-white p-4 rounded-lg border border-gray-200 shadow-2xs">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const SignificanceBadge: React.FC<{ isSig?: boolean }> = ({ isSig }) => {
  if (isSig) {
    return (
      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
        p &lt; 0.05
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600">
      Không ý nghĩa
    </span>
  );
};

function intPolicyShift(val: number): number {
  return Math.round(val * 100);
}
