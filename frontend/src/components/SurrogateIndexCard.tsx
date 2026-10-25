import React, { useState } from 'react';
import {
  Compass,
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
  TrendingUp,
  Percent,
  Clock
} from 'lucide-react';
import { api } from '../api/client';
import { SurrogateIndexRequest, SurrogateIndexResult } from '../types/survey';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface SurrogateIndexCardProps {
  surveyId: string;
  questions: QuestionSummary[];
}

export const SurrogateIndexCard: React.FC<SurrogateIndexCardProps> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedSurrogates, setSelectedSurrogates] = useState<string[]>([]);
  const [longtermOutcomeQId, setLongtermOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [ridgeLambda, setRidgeLambda] = useState<number>(1.0);
  const [nBootstraps, setNBootstraps] = useState<number>(300);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SurrogateIndexResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleSurrogate = (qid: string) => {
    setSelectedSurrogates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId || !longtermOutcomeQId || selectedSurrogates.length === 0) {
      setError('Vui lòng chọn Biến can thiệp (W), Kết quả dài hạn (Y) và ít nhất 1 Biến đại diện ngắn hạn (S).');
      return;
    }
    if (treatmentQId === longtermOutcomeQId || selectedSurrogates.includes(treatmentQId) || selectedSurrogates.includes(longtermOutcomeQId)) {
      setError('Biến can thiệp, kết quả dài hạn và các biến đại diện ngắn hạn không được trùng lặp.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: SurrogateIndexRequest = {
      treatment_question_id: treatmentQId,
      surrogate_question_ids: selectedSurrogates,
      longterm_outcome_question_id: longtermOutcomeQId,
      covariate_question_ids: selectedCovariates.filter(
        (id) => id !== treatmentQId && id !== longtermOutcomeQId && !selectedSurrogates.includes(id)
      ),
      alpha_level: 0.05,
      n_bootstraps: nBootstraps,
      ridge_lambda: ridgeLambda,
      scope
    };

    try {
      const data = await api.runSurrogateIndex(surveyId, payload);
      if (data.status === 'ERROR' || data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Không thể tính toán Surrogate Index.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối máy chủ khi tính toán Surrogate Index.');
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
    (q) => q.id !== treatmentQId && q.id !== longtermOutcomeQId
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-8 transition-all hover:border-cyan-200">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-cyan-950 via-teal-900 to-slate-950 px-6 py-5 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-cyan-500/30 text-cyan-200 border border-cyan-400/30 tracking-wide uppercase">
                Đánh giá Causal Dài hạn
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                DataTrust Verified
              </span>
            </div>
            <h3 className="text-xl font-bold mt-1 text-white tracking-tight flex items-center gap-2">
              <Compass className="w-5 h-5 text-cyan-400" />
              Surrogate Index &amp; Long-Term Causal Evaluation (Athey et al. 2019 <i>Econometrica</i>)
            </h3>
            <p className="text-sm text-cyan-200/90 mt-1 max-w-3xl leading-relaxed">
              Giải quyết bài toán khoảng cách thời gian (Horizon Gap) bằng cách kết hợp mẫu thử nghiệm ngắn hạn
              với mẫu quan sát theo dõi dài hạn để dự phóng chính xác tác động can thiệp $\tau_Y$.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={loading || !treatmentQId || !longtermOutcomeQId || selectedSurrogates.length === 0}
              className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all shadow-sm ${
                loading || !treatmentQId || !longtermOutcomeQId || selectedSurrogates.length === 0
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-950/20 active:scale-95'
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
                  Ước lượng Surrogate Index (2019)
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="p-6 bg-slate-50 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Treatment Question (W) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>1. Biến can thiệp / Thử nghiệm (W)</span>
              <span className="text-amber-600 font-mono">Treatment</span>
            </label>
            <select
              value={treatmentQId}
              onChange={(e) => setTreatmentQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-cyan-500 focus:border-cyan-500"
            >
              <option value="">-- Chọn biến can thiệp nhị phân --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === longtermOutcomeQId}>
                  {q.title}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Chính sách, chương trình đào tạo hoặc khuyến khích thử nghiệm.</p>
          </div>

          {/* Long-term Outcome (Y) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>2. Biến kết quả dài hạn mục tiêu (Y)</span>
              <span className="text-cyan-600 font-mono">Long-Term Outcome</span>
            </label>
            <select
              value={longtermOutcomeQId}
              onChange={(e) => setLongtermOutcomeQId(e.target.value)}
              className="w-full text-sm border-gray-300 rounded-md shadow-xs focus:ring-cyan-500 focus:border-cyan-500"
            >
              <option value="">-- Chọn biến kết quả dài hạn quan sát trong mẫu theo dõi --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === treatmentQId}>
                  {q.title}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">Đo lường sau nhiều năm (thu nhập tích lũy, sức khỏe mãn tính, giá trị trọn đời).</p>
          </div>
        </div>

        {/* Surrogates and Covariates selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Surrogates (S) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>3. Các biến đại diện trung gian ngắn hạn (Surrogates S)</span>
              <span className="text-xs text-cyan-600 font-semibold">{selectedSurrogates.length} đã chọn</span>
            </label>
            <div className="max-h-36 overflow-y-auto space-y-1.5 pr-2">
              {candidateQuestions.map((q) => (
                <label
                  key={q.id}
                  className="flex items-center space-x-2 text-xs text-gray-700 hover:bg-slate-50 p-1.5 rounded cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedSurrogates.includes(q.id)}
                    onChange={() => toggleSurrogate(q.id)}
                    className="rounded text-cyan-600 focus:ring-cyan-500 h-4 w-4"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Các câu hỏi ngắn hạn đo lường ngay sau can thiệp (điểm thi, mức độ gắn kết ban đầu).</p>
          </div>

          {/* Covariates (X) */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>4. Biến kiểm soát nền tảng (Covariates X)</span>
              <span className="text-xs text-slate-600 font-semibold">{selectedCovariates.length} đã chọn</span>
            </label>
            <div className="max-h-36 overflow-y-auto space-y-1.5 pr-2">
              {candidateQuestions
                .filter((q) => !selectedSurrogates.includes(q.id))
                .map((q) => (
                  <label
                    key={q.id}
                    className="flex items-center space-x-2 text-xs text-gray-700 hover:bg-slate-50 p-1.5 rounded cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedCovariates.includes(q.id)}
                      onChange={() => toggleCovariate(q.id)}
                      className="rounded text-slate-600 focus:ring-slate-500 h-4 w-4"
                    />
                    <span className="truncate">{q.title}</span>
                  </label>
                ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Đặc điểm tiền can thiệp quan sát chung trong cả hai tập dữ liệu.</p>
          </div>
        </div>

        {/* Hyperparameters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white p-3 rounded-lg border border-gray-200">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
              Hệ số phạt Ridge (lambda)
            </label>
            <select
              value={ridgeLambda}
              onChange={(e) => setRidgeLambda(Number(e.target.value))}
              className="w-full text-xs border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500"
            >
              <option value={0.1}>lambda = 0.1 (Phạt nhẹ)</option>
              <option value={1.0}>lambda = 1.0 (Tiêu chuẩn)</option>
              <option value={5.0}>lambda = 5.0 (Co cụm vừa)</option>
              <option value={10.0}>lambda = 10.0 (Bảo thủ cao)</option>
            </select>
          </div>

          <div className="bg-white p-3 rounded-lg border border-gray-200">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
              Bootstrap Replications
            </label>
            <select
              value={nBootstraps}
              onChange={(e) => setNBootstraps(Number(e.target.value))}
              className="w-full text-xs border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500"
            >
              <option value={100}>100 lần lặp (Nhanh)</option>
              <option value={300}>300 lần lặp (Tiêu chuẩn)</option>
              <option value={500}>500 lần lặp (Xuất bản)</option>
            </select>
          </div>

          <div className="bg-white p-3 rounded-lg border border-gray-200">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
              Phạm vi dữ liệu
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
              className="w-full text-xs border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500"
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
            {/* Long-Term Effect */}
            <div className="bg-gradient-to-br from-cyan-50 to-white p-4 rounded-xl border border-cyan-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cyan-700 uppercase tracking-wider">Hiệu ứng Dài hạn tau_Y</span>
                <Clock className="w-4 h-4 text-cyan-500" />
              </div>
              <div className="text-2xl font-black text-cyan-950 mt-1 font-mono">
                {result.longterm_treatment_effect?.estimate !== undefined
                  ? `${result.longterm_treatment_effect.estimate > 0 ? '+' : ''}${result.longterm_treatment_effect.estimate.toFixed(3)}`
                  : 'N/A'}
              </div>
              <div className="text-xs text-cyan-600 mt-0.5">
                95% CI [{result.longterm_treatment_effect?.ci_lower.toFixed(2)}, {result.longterm_treatment_effect?.ci_upper.toFixed(2)}]
              </div>
            </div>

            {/* R-squared */}
            <div className="bg-gradient-to-br from-emerald-50 to-white p-4 rounded-xl border border-emerald-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Độ khớp Chỉ số R²</span>
                <Percent className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-black text-emerald-950 mt-1 font-mono">
                {((result.surrogate_index_fit?.r_squared ?? 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-emerald-600 mt-0.5">
                R² của mô hình r(S, X) trên tập quan sát
              </div>
            </div>

            {/* Sample Sizes */}
            <div className="bg-gradient-to-br from-indigo-50 to-white p-4 rounded-xl border border-indigo-100 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">Quy mô Hai Mẫu</span>
                <Layers className="w-4 h-4 text-indigo-500" />
              </div>
              <div className="text-sm font-bold text-indigo-950 mt-2 space-y-0.5">
                <div>N_thử nghiệm: <span className="font-mono text-cyan-700">{result.sample_sizes?.experimental_sample}</span></div>
                <div>N_theo dõi: <span className="font-mono text-indigo-700">{result.sample_sizes?.observational_sample}</span></div>
              </div>
            </div>

            {/* Surrogacy Status */}
            <div className="bg-gradient-to-br from-slate-50 to-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Kiểm định Tính Đại Diện</span>
                <Activity className="w-4 h-4 text-slate-500" />
              </div>
              <div className="text-xs font-bold mt-2 text-slate-800 truncate" title={result.surrogacy_validation?.risk_status}>
                {result.surrogacy_validation?.risk_status.split('(')[0]}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                Kiểm định Prentice: Y độc lập W | S, X
              </div>
            </div>
          </div>

          {/* Surrogate Decomposition Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
            <div className="px-5 py-3.5 bg-slate-50 border-b border-gray-200 flex items-center justify-between">
              <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-600" />
                Phân Rã Đóng Góp Của Từng Biến Đại Diện Ngắn Hạn (Surrogate Decomposition)
              </h4>
              <span className="text-xs text-gray-500 font-mono">Ridge lambda = {result.surrogate_index_fit?.ridge_lambda}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100/70 text-xs font-semibold text-slate-600 uppercase border-b border-gray-200">
                  <tr>
                    <th className="py-3 px-4">Biến Đại diện Ngắn hạn (S_k)</th>
                    <th className="py-3 px-4">Tác động Ngắn hạn của W</th>
                    <th className="py-3 px-4">Sai số chuẩn (SE)</th>
                    <th className="py-3 px-4">Trọng số trong Chỉ số r(S, X)</th>
                    <th className="py-3 px-4 text-center">Đóng góp Dự phóng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {result.surrogate_decomposition?.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-800">{item.surrogate_name}</td>
                      <td className="py-3 px-4 font-mono text-cyan-800 font-bold">{item.treatment_effect.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-gray-600">{item.std_error.toFixed(4)}</td>
                      <td className="py-3 px-4 font-mono text-indigo-700 font-semibold">{item.surrogate_weight_in_index.toFixed(4)}</td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-cyan-50 text-cyan-800 border border-cyan-200">
                          {(item.treatment_effect * item.surrogate_weight_in_index).toFixed(3)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Scientific SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
              <div className="px-5 py-3.5 bg-slate-50 border-b border-gray-200">
                <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-cyan-600" />
                  Đồ Thị Khoa Học: Forest Plot Hiệu Ứng Dài Hạn &amp; Trọng Số Chỉ Số Đại Diện
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
                  <Info className="w-4 h-4 text-cyan-600" />
                  Thuyết Minh Học Thuật Chuẩn APA 7th Edition (Athey et al. 2019)
                </h4>
                <button
                  onClick={handleCopyNarrative}
                  className="inline-flex items-center space-x-1.5 text-xs text-cyan-600 hover:text-cyan-800 font-medium px-2.5 py-1 bg-cyan-50 hover:bg-cyan-100 rounded-md transition-colors"
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
