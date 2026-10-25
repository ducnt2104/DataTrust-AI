import React, { useState } from 'react';
import {
  ShieldAlert,
  Play,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Info,
  Copy,
  Sliders,
  Percent,
  Layers,
  Activity,
  Award,
  Filter
} from 'lucide-react';
import { api } from '../api/client';
import { LeeBoundsRequest, LeeBoundsResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface LeeBoundsCardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const LeeBoundsCard: React.FC<LeeBoundsCardProps> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [responseQId, setResponseQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [nBootstraps, setNBootstraps] = useState<number>(300);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LeeBoundsResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId) {
      setError('Vui lòng chọn Biến kết quả (Y) và Biến can thiệp (T).');
      return;
    }
    if (outcomeQId === treatmentQId) {
      setError('Biến kết quả và biến can thiệp không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: LeeBoundsRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      response_question_id: responseQId || undefined,
      covariate_question_ids: selectedCovariates.filter((id) => id !== outcomeQId && id !== treatmentQId),
      alpha_level: 0.05,
      n_bootstraps: nBootstraps,
      scope
    };

    try {
      const data = await api.runLeeBounds(surveyId, payload);
      if (data.status === 'ERROR' || data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Không thể tính toán Lee Bounds.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối máy chủ khi tính toán Lee Bounds.');
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
    (q) => q.id !== outcomeQId && q.id !== treatmentQId && q.id !== responseQId
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-8 transition-all hover:border-emerald-200">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-950 via-teal-900 to-slate-950 px-6 py-5 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/30 text-emerald-200 border border-emerald-400/30 tracking-wide uppercase">
                Bảo vệ Hao hụt Dữ liệu
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">
                DataTrust Verified
              </span>
            </div>
            <h3 className="text-xl font-bold mt-1 text-white tracking-tight flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-emerald-400" />
              Non-random Survey Attrition &amp; Selection Bounds (Lee 2009 <i>Restud</i>)
            </h3>
            <p className="text-sm text-emerald-200/90 mt-1 max-w-3xl leading-relaxed">
              Thiết lập cận cận sắc nét phi tham số (Sharp Lee Bounds) và khoảng tin cậy Imbens-Manski (2004)
              cho hiệu ứng can thiệp trong điều kiện hao hụt mẫu hoặc tỷ lệ phản hồi khảo sát không ngẫu nhiên.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={loading || !outcomeQId || !treatmentQId}
              className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all shadow-sm ${
                loading || !outcomeQId || !treatmentQId
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950/20 active:scale-95'
              }`}
            >
              {loading ? (
                <>
                  <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                  Đang tính toán Bootstrap...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2 fill-current" />
                  Tính toán Lee Bounds (2009)
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
              <span>1. Biến kết quả theo dõi (Y)</span>
              <span className="text-emerald-600 font-mono">Outcome</span>
            </label>
            <select
              value={outcomeQId}
              onChange={(e) => setOutcomeQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">-- Chọn câu hỏi kết quả theo dõi --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title} {q.question_type ? `(${q.question_type})` : ''}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Dữ liệu có thể bị thiếu (missing) do người tham gia bỏ cuộc.</p>
          </div>

          {/* Treatment Question (T) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>2. Biến can thiệp / Nhóm (T)</span>
              <span className="text-amber-600 font-mono">Treatment</span>
            </label>
            <select
              value={treatmentQId}
              onChange={(e) => setTreatmentQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">-- Chọn biến can thiệp nhị phân --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === outcomeQId}>
                  {q.title}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Nhóm can thiệp (T=1) vs nhóm đối chứng (T=0).</p>
          </div>

          {/* Response Question (R) - Optional */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>3. Biến chỉ báo phản hồi (R)</span>
              <span className="text-slate-500 font-mono">Tùy chọn</span>
            </label>
            <select
              value={responseQId}
              onChange={(e) => setResponseQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">-- Tự động xác định qua giá trị thiếu Y --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === outcomeQId || q.id === treatmentQId}>
                  {q.title}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Nếu để trống, hệ thống tự nhận diện hao hụt từ câu trả lời rỗng.</p>
          </div>
        </div>

        {/* Covariates for Tightening & Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Biến phân tầng thắt chặt cận (Tightening Covariates X)</span>
              <span className="text-xs text-emerald-600 font-semibold">{selectedCovariates.length} đã chọn</span>
            </label>
            <div className="max-h-32 overflow-y-auto space-y-1.5 pr-2">
              {candidateCovariates.length === 0 ? (
                <p className="text-xs text-gray-400 italic">Không có câu hỏi bổ sung.</p>
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
                      className="rounded text-emerald-600 focus:ring-emerald-500 h-4 w-4"
                    />
                    <span className="truncate">{q.title}</span>
                  </label>
                ))
              )}
            </div>
            <p className="text-xs text-gray-400 mt-2">Cắt tỉa theo từng phân tầng để thu hẹp độ rộng khoảng [LB, UB].</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs space-y-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                Bootstrap Replications
              </label>
              <select
                value={nBootstraps}
                onChange={(e) => setNBootstraps(Number(e.target.value))}
                className="w-full text-xs border-gray-300 rounded-md focus:ring-emerald-500 focus:border-emerald-500"
              >
                <option value={100}>100 lần lặp (Nhanh)</option>
                <option value={300}>300 lần lặp (Tiêu chuẩn)</option>
                <option value={500}>500 lần lặp (Xuất bản)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                Phạm vi dữ liệu
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
                className="w-full text-xs border-gray-300 rounded-md focus:ring-emerald-500 focus:border-emerald-500"
              >
                <option value="all">Toàn bộ phản hồi</option>
                <option value="verified_clean">Chỉ mẫu sạch xác thực</option>
              </select>
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
            {/* Unconditional Bounds */}
            <div className="bg-gradient-to-br from-emerald-50 to-white p-4 rounded-xl border border-emerald-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Cận sắc nét Lee [LB, UB]</span>
                <Award className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-xl font-black text-emerald-950 mt-1 font-mono">
                [{result.bounds?.unconditional.lower_bound.toFixed(2)}, {result.bounds?.unconditional.upper_bound.toFixed(2)}]
              </div>
              <div className="text-xs text-emerald-600 mt-0.5">
                95% Imbens-Manski CI [{result.bounds?.unconditional.ci_lower.toFixed(2)}, {result.bounds?.unconditional.ci_upper.toFixed(2)}]
              </div>
            </div>

            {/* Trimming Fraction */}
            <div className="bg-gradient-to-br from-teal-50 to-white p-4 rounded-xl border border-teal-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-700 uppercase tracking-wider">Tỷ lệ Cắt gọt (Trimming q)</span>
                <Percent className="w-4 h-4 text-teal-500" />
              </div>
              <div className="text-2xl font-black text-teal-950 mt-1 font-mono">
                {((result.response_rates?.trimming_fraction_q ?? 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-teal-600 mt-0.5">
                Cắt đuôi nhóm {result.response_rates?.trimmed_group === 'treated' ? 'can thiệp' : 'đối chứng'}
              </div>
            </div>

            {/* Naive Estimate */}
            <div className="bg-gradient-to-br from-amber-50 to-white p-4 rounded-xl border border-amber-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">Ước lượng Ngây thơ (Naive)</span>
                <Activity className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-black text-amber-950 mt-1 font-mono">
                {result.naive_complete_case?.estimate.toFixed(3)}
              </div>
              <div className="text-xs text-amber-600 mt-0.5">
                Chỉ tính trên mẫu hoàn tất ({result.observed_sample_size}/{result.sample_size})
              </div>
            </div>

            {/* Robustness Verdict */}
            <div className={`p-4 rounded-xl border shadow-xs ${
              result.bounds?.unconditional.excludes_zero
                ? 'bg-gradient-to-br from-emerald-50 to-white border-emerald-200'
                : 'bg-gradient-to-br from-rose-50 to-white border-rose-200'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Độ vững trước Hao hụt</span>
                {result.bounds?.unconditional.excludes_zero ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-600" />
                )}
              </div>
              <div className={`text-base font-bold mt-2 ${
                result.bounds?.unconditional.excludes_zero ? 'text-emerald-900' : 'text-rose-900'
              }`}>
                {result.bounds?.unconditional.excludes_zero
                  ? 'BẢO TOÀN HIỆU ỨNG'
                  : 'NHẠY CẢM VỚI HAO HỤT'}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                {result.bounds?.unconditional.excludes_zero
                  ? 'Khoảng tin cậy loại trừ hoàn toàn giá trị 0'
                  : 'Khoảng tin cậy bao hàm giá trị 0 (chứa giả thuyết vô hiệu)'}
              </div>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
            <div className="px-5 py-3.5 bg-slate-50 border-b border-gray-200 flex items-center justify-between">
              <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <Sliders className="w-4 h-4 text-emerald-600" />
                Bảng So Sánh Cận Hiệu Ứng Can Thiệp (Sharp Bounds Comparison)
              </h4>
              <span className="text-xs text-gray-500 font-mono">N = {result.sample_size} | Responders = {result.observed_sample_size}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100/70 text-xs font-semibold text-slate-600 uppercase border-b border-gray-200">
                  <tr>
                    <th className="py-3 px-4">Quy cách Ước lượng</th>
                    <th className="py-3 px-4">Cận Dưới (LB)</th>
                    <th className="py-3 px-4">Cận Trên (UB)</th>
                    <th className="py-3 px-4">Độ rộng Khoảng</th>
                    <th className="py-3 px-4">Khoảng Tin Cậy 95%</th>
                    <th className="py-3 px-4 text-center">Kết luận Độ vững</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {/* Naive */}
                  {result.naive_complete_case && (
                    <tr className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-amber-900">Naive Complete-Case (Bỏ qua hao hụt)</td>
                      <td className="py-3 px-4 font-mono text-amber-800" colSpan={2}>
                        Điểm ước lượng: {result.naive_complete_case.estimate.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-500">0.0000</td>
                      <td className="py-3 px-4 font-mono text-xs text-gray-600">
                        [{result.naive_complete_case.ci_lower.toFixed(3)}, {result.naive_complete_case.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
                          Có thể chệch cao
                        </span>
                      </td>
                    </tr>
                  )}

                  {/* Sharp Unconditional Lee Bounds */}
                  {result.bounds?.unconditional && (
                    <tr className="bg-emerald-50/40 hover:bg-emerald-50/70 font-semibold">
                      <td className="py-3 px-4 text-emerald-950 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        Sharp Lee Bounds (Phi tham số không điều kiện)
                      </td>
                      <td className="py-3 px-4 font-mono text-emerald-800">{result.bounds.unconditional.lower_bound.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-emerald-800">{result.bounds.unconditional.upper_bound.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-700">
                        {(result.bounds.unconditional.upper_bound - result.bounds.unconditional.lower_bound).toFixed(4)}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-emerald-900">
                        [{result.bounds.unconditional.ci_lower.toFixed(3)}, {result.bounds.unconditional.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        {result.bounds.unconditional.excludes_zero ? (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                            Vững (Loại trừ 0)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800">
                            Chứa giá trị 0
                          </span>
                        )}
                      </td>
                    </tr>
                  )}

                  {/* Covariate-Tightened Lee Bounds */}
                  {result.bounds?.covariate_tightened.is_available && (
                    <tr className="hover:bg-slate-50 font-medium">
                      <td className="py-3 px-4 text-teal-950">Tightened Lee Bounds (Phân tầng Covariates)</td>
                      <td className="py-3 px-4 font-mono text-teal-800">{result.bounds.covariate_tightened.lower_bound.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-teal-800">{result.bounds.covariate_tightened.upper_bound.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-700">
                        {(result.bounds.covariate_tightened.upper_bound - result.bounds.covariate_tightened.lower_bound).toFixed(4)}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-teal-900">
                        [{result.bounds.covariate_tightened.ci_lower.toFixed(3)}, {result.bounds.covariate_tightened.ci_upper.toFixed(3)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-teal-100 text-teal-800">
                          Đã thắt chặt
                        </span>
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
                  <ShieldAlert className="w-4 h-4 text-emerald-600" />
                  Đồ Thị Khoa Học: Forest Plot So Sánh Cận &amp; Tỷ Lệ Hao Hụt Mẫu
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
                  <Info className="w-4 h-4 text-emerald-600" />
                  Thuyết Minh Học Thuật Chuẩn APA 7th Edition (Lee 2009)
                </h4>
                <button
                  onClick={handleCopyNarrative}
                  className="inline-flex items-center space-x-1.5 text-xs text-emerald-600 hover:text-emerald-800 font-medium px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 rounded-md transition-colors"
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
