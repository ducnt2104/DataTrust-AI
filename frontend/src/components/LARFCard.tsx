import React, { useState } from 'react';
import {
  GitCommit,
  Play,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Info,
  Copy,
  Sliders,
  TrendingUp,
  Percent,
  Layers,
  Activity
} from 'lucide-react';
import { api } from '../api/client';
import { LARFRequest, LARFResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface LARFCardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const LARFCard: React.FC<LARFCardProps> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [instrumentQId, setInstrumentQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [modelType, setModelType] = useState<'logit' | 'linear'>('logit');
  const [nBootstraps, setNBootstraps] = useState<number>(300);
  const [trimNegative, setTrimNegative] = useState<boolean>(false);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LARFResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId || !instrumentQId) {
      setError('Vui lòng chọn đầy đủ Biến kết quả (Y), Biến can thiệp nội sinh (D) và Biến công cụ ngoại sinh (Z).');
      return;
    }
    if (outcomeQId === treatmentQId || outcomeQId === instrumentQId || treatmentQId === instrumentQId) {
      setError('Biến kết quả, biến can thiệp và biến công cụ phải là 3 câu hỏi riêng biệt.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: LARFRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      instrument_question_id: instrumentQId,
      covariate_question_ids: selectedCovariates.filter((id) => id !== outcomeQId && id !== treatmentQId && id !== instrumentQId),
      model_type: modelType,
      alpha_level: 0.05,
      n_bootstraps: nBootstraps,
      trim_negative: trimNegative,
      scope
    };

    try {
      const data = await api.runLARF(surveyId, payload);
      if (data.status === 'ERROR' || data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Không thể thực hiện ước lượng LARF.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối máy chủ khi tính toán LARF.');
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

  const candidateCovariates = questions.filter(
    (q) => q.id !== outcomeQId && q.id !== treatmentQId && q.id !== instrumentQId
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-8 transition-all hover:border-indigo-200">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 px-6 py-5 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 tracking-wide uppercase">
                Kinh tế lượng Bán tham số
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                DataTrust Verified
              </span>
            </div>
            <h3 className="text-xl font-bold mt-1 text-white tracking-tight flex items-center gap-2">
              <GitCommit className="w-5 h-5 text-indigo-400" />
              Instrumental Variable Local Average Response Function (LARF)
            </h3>
            <p className="text-sm text-indigo-200/90 mt-1 max-w-3xl leading-relaxed">
              Ước lượng hàm phản ứng nhân quả phi tuyến và bị chặn (Abadie 2003 <i>Econometrica</i>) dưới điều kiện
              can thiệp nội sinh với biến công cụ (IV) thông qua hàm trọng số Abadie Kappa $\kappa$.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={loading || !outcomeQId || !treatmentQId || !instrumentQId}
              className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all shadow-sm ${
                loading || !outcomeQId || !treatmentQId || !instrumentQId
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-950/20 active:scale-95'
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
                  Thực hiện LARF (Abadie 2003)
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="p-6 bg-slate-50 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Outcome Question (Y) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>1. Biến kết quả (Y)</span>
              <span className="text-indigo-600 font-mono">Outcome</span>
            </label>
            <select
              value={outcomeQId}
              onChange={(e) => setOutcomeQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">-- Chọn câu hỏi đo lường kết quả --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title} {q.question_type ? `(${q.question_type})` : ''}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Hỗ trợ biến nhị phân (0 hoặc 1), bị chặn [0, 1] hoặc liên tục.</p>
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
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">-- Chọn biến can thiệp nhị phân --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === outcomeQId || q.id === instrumentQId}>
                  {q.title}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Sự tuân thủ can thiệp bị nhiễu bởi yếu tố không quan sát được.</p>
          </div>

          {/* Instrument Question (Z) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>3. Biến công cụ ngoại sinh (Z)</span>
              <span className="text-emerald-600 font-mono">Instrument</span>
            </label>
            <select
              value={instrumentQId}
              onChange={(e) => setInstrumentQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">-- Chọn biến công cụ ngoại sinh --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === outcomeQId || q.id === treatmentQId}>
                  {q.title}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Thỏa mãn tính ngoại sinh và đơn điệu (Monotonicity / No-Defiers).</p>
          </div>
        </div>

        {/* Hyperparameters & Covariates Selection */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Covariates Multi-select */}
          <div className="md:col-span-2 bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Biến kiểm soát tiền can thiệp (X)</span>
              <span className="text-xs text-indigo-600 font-semibold">{selectedCovariates.length} đã chọn</span>
            </label>
            <div className="max-h-36 overflow-y-auto space-y-1.5 pr-2">
              {candidateCovariates.length === 0 ? (
                <p className="text-xs text-gray-400 italic">Chưa có biến kiểm soát bổ sung.</p>
              ) : (
                candidateCovariates.map((q) => (
                  <label
                    key={q.id}
                    className="flex items-center space-x-2 text-xs text-gray-700 hover:bg-slate-50 p-1.5 rounded cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedCovariates.includes(q.id)}
                      onChange={() => toggleCovariate(q.id)}
                      className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                    />
                    <span className="truncate">{q.title}</span>
                  </label>
                ))
              )}
            </div>
          </div>

          {/* Model Link & Hyperparameters */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs space-y-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                Link Function $\mu(D, X)$
              </label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value as 'logit' | 'linear')}
                className="w-full text-xs border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="logit">Logit Link (Binary / Bounded)</option>
                <option value="linear">Linear Link (Continuous / WLS)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                Bootstrap Replications
              </label>
              <select
                value={nBootstraps}
                onChange={(e) => setNBootstraps(Number(e.target.value))}
                className="w-full text-xs border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value={100}>100 lần lặp (Nhanh)</option>
                <option value={300}>300 lần lặp (Tiêu chuẩn)</option>
                <option value={500}>500 lần lặp (Xuất bản)</option>
              </select>
            </div>
          </div>

          {/* Additional Options */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs space-y-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                Phạm vi dữ liệu
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
                className="w-full text-xs border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">Toàn bộ phản hồi</option>
                <option value="verified_clean">Chỉ mẫu sạch (Loại gian lận)</option>
              </select>
            </div>

            <div className="pt-1">
              <label className="flex items-center space-x-2 text-xs text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={trimNegative}
                  onChange={(e) => setTrimNegative(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <span className="font-medium text-slate-800">Cắt trọng số âm ($\kappa^+ \ge 0$)</span>
              </label>
              <p className="text-[11px] text-gray-400 mt-1">Chiếu các giá trị kappa &lt; 0 về 0 theo Frölich (2007).</p>
            </div>
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
            <div className="bg-gradient-to-br from-indigo-50 to-white p-4 rounded-xl border border-indigo-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">Tỷ lệ Tuân thủ P(c)</span>
                <Percent className="w-4 h-4 text-indigo-500" />
              </div>
              <div className="text-2xl font-black text-indigo-950 mt-1">
                {((result.complier_probability ?? 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-indigo-600 mt-0.5">
                SE = {result.complier_probability_se?.toFixed(3)} (Compliers)
              </div>
            </div>

            <div className="bg-gradient-to-br from-emerald-50 to-white p-4 rounded-xl border border-emerald-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">LATE trên Compliers</span>
                <TrendingUp className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-black text-emerald-950 mt-1">
                {result.effects?.late.estimate !== undefined
                  ? `${result.effects.late.estimate > 0 ? '+' : ''}${result.effects.late.estimate.toFixed(4)}`
                  : 'N/A'}
              </div>
              <div className="text-xs text-emerald-600 mt-0.5">
                95% CI [{result.effects?.late.ci_lower?.toFixed(3)}, {result.effects?.late.ci_upper?.toFixed(3)}]
              </div>
            </div>

            <div className="bg-gradient-to-br from-amber-50 to-white p-4 rounded-xl border border-amber-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">Trọng số Âm Abadie</span>
                <Activity className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-black text-amber-950 mt-1">
                {result.pct_negative_weights?.toFixed(1)}%
              </div>
              <div className="text-xs text-amber-600 mt-0.5">
                Cỡ mẫu hữu hiệu N_eff = {result.effective_sample_size} / {result.sample_size}
              </div>
            </div>

            <div className="bg-gradient-to-br from-sky-50 to-white p-4 rounded-xl border border-sky-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-sky-700 uppercase tracking-wider">Phản ứng Tiềm năng E[Y|c]</span>
                <Layers className="w-4 h-4 text-sky-500" />
              </div>
              <div className="text-sm font-bold text-sky-950 mt-2 space-y-0.5">
                <div>E[Y(1)|c]: <span className="font-mono text-emerald-600">{result.potential_outcomes_compliers?.e_y1_compliers.toFixed(3)}</span></div>
                <div>E[Y(0)|c]: <span className="font-mono text-slate-600">{result.potential_outcomes_compliers?.e_y0_compliers.toFixed(3)}</span></div>
              </div>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
            <div className="px-5 py-3.5 bg-slate-50 border-b border-gray-200 flex items-center justify-between">
              <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                Bảng Đối Chiếu Ước Lượng Hiệu Ứng Can Thiệp (Comparative Treatment Response)
              </h4>
              <span className="text-xs text-gray-500 font-mono">N = {result.sample_size} | Bootstrap B = {result.bootstrap_replications}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100/70 text-xs font-semibold text-slate-600 uppercase border-b border-gray-200">
                  <tr>
                    <th className="py-3 px-4">Mô hình / Quy cách</th>
                    <th className="py-3 px-4">Ước lượng (Δ)</th>
                    <th className="py-3 px-4">Sai số chuẩn (SE)</th>
                    <th className="py-3 px-4">Z-statistic</th>
                    <th className="py-3 px-4">p-value</th>
                    <th className="py-3 px-4">Khoảng tin cậy 95% (CI)</th>
                    <th className="py-3 px-4 text-center">Ý nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {/* LARF LATE */}
                  {result.effects?.late && (
                    <tr className="bg-indigo-50/40 hover:bg-indigo-50/70 font-semibold">
                      <td className="py-3 px-4 text-indigo-900 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                        LARF LATE (Abadie 2003 - Nhóm Tuân thủ)
                      </td>
                      <td className="py-3 px-4 font-mono text-indigo-800">{result.effects.late.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.late.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.late.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.late.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.effects.late.ci_lower.toFixed(3)}, {result.effects.late.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        {result.effects.late.is_significant ? (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                            Có ý nghĩa (p &lt; 0.05)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600">
                            Không có ý nghĩa
                          </span>
                        )}
                      </td>
                    </tr>
                  )}

                  {/* ITT */}
                  {result.effects?.itt && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 text-slate-800">Intention-to-Treat (ITT: Z → Y)</td>
                      <td className="py-3 px-4 font-mono text-slate-800">{result.effects.itt.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.itt.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.itt.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.itt.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.effects.itt.ci_lower.toFixed(3)}, {result.effects.itt.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        {result.effects.itt.is_significant ? (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-sky-100 text-sky-800">
                            Có ý nghĩa
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600">
                            Không ý nghĩa
                          </span>
                        )}
                      </td>
                    </tr>
                  )}

                  {/* Naive */}
                  {result.effects?.naive && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 text-slate-800">Naive Unweighted (D → Y không hiệu chỉnh)</td>
                      <td className="py-3 px-4 font-mono text-amber-700">{result.effects.naive.estimate.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.naive.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.naive.z_stat.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{result.effects.naive.p_value.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.effects.naive.ci_lower.toFixed(3)}, {result.effects.naive.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        {result.effects.naive.is_significant ? (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
                            Có ý nghĩa
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600">
                            Không ý nghĩa
                          </span>
                        )}
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
                  <TrendingUp className="w-4 h-4 text-indigo-600" />
                  Đồ Thị Khoa Học: Forest Plot &amp; Phân Bổ Trọng Số Abadie Kappa
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
                  <Info className="w-4 h-4 text-indigo-600" />
                  Thuyết Minh Học Thuật Chuẩn APA 7th Edition (Abadie 2003)
                </h4>
                <button
                  onClick={handleCopyNarrative}
                  className="inline-flex items-center space-x-1.5 text-xs text-indigo-600 hover:text-indigo-800 font-medium px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 rounded-md transition-colors"
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
