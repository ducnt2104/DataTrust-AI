import React, { useState } from 'react';
import {
  DPMDeconvolutionResult,
  DPMDeconvolutionRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Sparkles,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertCircle,
  Sliders,
  Layers,
  Activity,
  CheckCircle2,
  TrendingUp,
  Percent,
  Compass,
  BarChart3,
  Scale,
  ShieldCheck,
  Filter,
  Minimize2
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

export const DPMDeconvolutionCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [targetQId, setTargetQId] = useState<string>('');
  const [replicateQId, setReplicateQId] = useState<string>('');
  const [errorVarRatio, setErrorVarRatio] = useState<number>(0.25);
  const [maxComponents, setMaxComponents] = useState<number>(6);
  const [dpAlpha, setDpAlpha] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DPMDeconvolutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleRunAnalysis = async () => {
    if (!targetQId) {
      setError('Vui lòng chọn biến số đo lường khảo sát Y cần tách nhiễu.');
      return;
    }

    if (replicateQId && targetQId === replicateQId) {
      setError('Biến câu hỏi lặp lại không được trùng với biến số chính.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: DPMDeconvolutionRequest = {
      target_question_id: targetQId,
      replicate_question_id: replicateQId || undefined,
      error_variance_ratio: errorVarRatio,
      max_components: maxComponents,
      dp_alpha: dpAlpha,
      scope
    };

    try {
      const res = await api.runDPMDeconvolution(surveyId, payload);
      if (res.status === 'ERROR') {
        setError(res.message || 'Lỗi khi thực hiện DPM Deconvolution.');
        setResult(null);
      } else if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Cỡ mẫu chưa đủ để thực hiện Deconvolution.');
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
    setTargetQId('');
    setReplicateQId('');
    setErrorVarRatio(0.25);
    setMaxComponents(6);
    setDpAlpha(1.0);
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
            <div className="p-2.5 bg-teal-500/10 border border-teal-500/20 rounded-lg text-teal-400">
              <Filter className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                Bayesian Dirichlet Process Mixture Density Deconvolution (DPM-DD)
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-teal-950/80 text-teal-400 border border-teal-800/60">
                  Ferguson (1973) · Escobar &amp; West (1995) JASA
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Khử nhiễu đo lường khảo sát phi tham số Y = X* + &epsilon;. Khôi phục hàm mật độ thực tế f<sub>0</sub>(X*), độ tin cậy R và nén phân vị mà không bị dao động xác suất âm (Fourier oscillation artifacts).
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
            disabled={loading || !targetQId}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow transition-all"
          >
            {loading ? (
              <>
                <Activity className="w-3.5 h-3.5 animate-spin" />
                Đang lấy mẫu DPM &amp; Tách nhiễu...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Tách Nhiễu Mật Độ
              </>
            )}
          </button>
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Target Variable Y */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-teal-400" />
            1. Biến Đo Lường Nhiễu Y
          </label>
          <select
            value={targetQId}
            onChange={(e) => setTargetQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500"
          >
            <option value="">-- Chọn câu hỏi đo lường Y --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Biến số liên tục có thể chứa sai số đo lường.</span>
        </div>

        {/* Optional Replicate Variable Y_rep */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-sky-400" />
            2. Biến Đo Lặp Lại (Tùy chọn)
          </label>
          <select
            value={replicateQId}
            onChange={(e) => setReplicateQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500"
          >
            <option value="">-- Không có (Dùng tỷ lệ giả định) --</option>
            {numericQuestions.filter(q => q.id !== targetQId).map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Dùng để ước lượng &sigma;<sub>&epsilon;</sub><sup>2</sup> trực tiếp từ dữ liệu.</span>
        </div>

        {/* Noise Ratio (if no replicate) */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Percent className="w-3.5 h-3.5 text-amber-400" />
            3. Tỷ Lệ Nhiễu Giả Định ({Math.round(errorVarRatio * 100)}%)
          </label>
          <input
            type="range"
            min="0.05"
            max="0.60"
            step="0.05"
            disabled={!!replicateQId}
            value={errorVarRatio}
            onChange={(e) => setErrorVarRatio(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-teal-500 mt-2 disabled:opacity-40"
          />
          <div className="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>5% (Ít nhiễu)</span>
            <span>25% (Chuẩn)</span>
            <span>60% (Nhiều nhiễu)</span>
          </div>
        </div>

        {/* Max Components & Alpha */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-purple-400" />
            4. Cụm Tiềm Ẩn K &amp; Phạm Vi Mẫu
          </label>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={maxComponents}
              onChange={(e) => setMaxComponents(parseInt(e.target.value, 10))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
            >
              <option value={4}>K = 4 Cụm</option>
              <option value={5}>K = 5 Cụm</option>
              <option value={6}>K = 6 Cụm (Chuẩn)</option>
              <option value={8}>K = 8 Cụm</option>
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
          <span className="text-[11px] text-slate-500 mt-1 block">Tham số Dirichlet Stick-Breaking.</span>
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
            {/* Reliability Ratio */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-teal-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-teal-400 block mb-1">
                Hệ Số Tin Cậy Đo Lường R
              </span>
              <div className="text-2xl font-black text-slate-100">
                {summ.reliability_ratio}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Var(X*) / Var(Y) = {Math.round(summ.reliability_ratio * 100)}%
              </div>
              <div className="text-[11px] text-teal-400/90 font-mono mt-2">
                Nhiễu chiếm: {summ.variance_reduction_pct}% tổng biến thiên
              </div>
            </div>

            {/* Noise SD */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-amber-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-400 block mb-1">
                Độ Lệch Chuẩn Nhiễu &sigma;<sub>&epsilon;</sub>
              </span>
              <div className="text-2xl font-black text-amber-300">
                {summ.measurement_error_sd}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Phương sai nhiễu: {summ.measurement_error_variance}
              </div>
              <div className="text-[11px] text-slate-500 mt-2 truncate">
                {summ.measurement_error_source}
              </div>
            </div>

            {/* True Latent SD vs Observed */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-sky-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block mb-1">
                Độ Biến Thiên Thực Tế &sigma;<sub>X*</sub>
              </span>
              <div className="text-2xl font-black text-sky-300">
                {summ.latent_true_sd}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Quan sát bị thổi phồng: &sigma;<sub>Y</sub> = {summ.observed_sd}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                Đã co gọn phương sai về thực tế
              </div>
            </div>

            {/* Shannon Entropy Reduction */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-emerald-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 block mb-1">
                Mức Giảm Entropy Thông Tin (&Delta;H)
              </span>
              <div className="text-2xl font-black text-emerald-300">
                {summ.entropy_reduction > 0 ? `+${summ.entropy_reduction}` : summ.entropy_reduction} nats
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Từ {summ.entropy_observed} &rarr; {summ.entropy_deconvolved}
              </div>
              <div className="text-[11px] text-emerald-400/80 mt-2 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Thu được phân phối sắc nét hơn</span>
              </div>
            </div>
          </div>

          {/* Quantile Error Compression Table */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4 text-teal-400" />
                <span className="text-xs font-bold text-slate-200">
                  Bảng Co Gọn Phân Vị Khử Nhiễu Đo Lường (Quantile Error Compression)
                </span>
              </div>
              <span className="text-[11px] text-slate-500">Hiệu chỉnh độ lệch các phân vị cực trị</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Phân vị (Quantile)</th>
                    <th className="py-2.5 px-4">Giá trị quan sát nhiễu Q(Y)</th>
                    <th className="py-2.5 px-4">Giá trị thực tế sau tách nhiễu Q(X*)</th>
                    <th className="py-2.5 px-4">Mức co gọn sai số (&Delta;Q)</th>
                    <th className="py-2.5 px-4">Ý nghĩa thống kê</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {summ.quantiles_evaluated.map((q, idx) => (
                    <tr key={q} className="hover:bg-slate-800/40">
                      <td className="py-2 px-4 font-bold text-slate-300 font-sans">
                        {Math.round(q * 100)}% ({q === 0.5 ? 'Trung vị / Median' : `Phân vị ${Math.round(q * 100)}`})
                      </td>
                      <td className="py-2 px-4 text-rose-300">{summ.quantiles_observed[idx]}</td>
                      <td className="py-2 px-4 font-bold text-teal-300">{summ.quantiles_deconvolved[idx]}</td>
                      <td className="py-2 px-4 font-bold text-slate-100">
                        {summ.quantile_compression_delta[idx] > 0
                          ? `+${summ.quantile_compression_delta[idx]}`
                          : summ.quantile_compression_delta[idx]}
                      </td>
                      <td className="py-2 px-4 text-slate-400 font-sans">
                        {idx < 2 ? 'Kéo lên về trung tâm (loại bỏ đuôi âm ảo)' : (idx > 2 ? 'Kéo xuống về trung tâm (loại bỏ đuôi dương ảo)' : 'Điểm cân bằng trung tâm')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Component Profiles Table */}
          {result.components && (
            <div className="bg-slate-950/40 border border-slate-800 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-300 block mb-3">
                Cấu Trúc Hỗn Hợp Dirichlet Process ({result.components.length} Thành Phần Tiềm Ẩn):
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {result.components.map(c => (
                  <div key={c.component_id} className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
                    <span className="text-[10px] font-semibold text-teal-400 block mb-1">Cụm C{c.component_id}</span>
                    <div className="text-base font-bold text-slate-200">{Math.round(c.weight * 100)}%</div>
                    <div className="text-[11px] text-slate-400 mt-1 font-mono">&mu; = {c.mean}</div>
                    <div className="text-[10px] text-slate-500 font-mono">&tau; = {c.sd_latent}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scientific Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-hidden shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-teal-400" />
                  <span className="text-xs font-semibold text-slate-200">
                    Trực Quan Hóa Khoa Học: Phân Phối Mật Độ Trước &amp; Sau Tách Nhiễu và Trọng Số Stick-Breaking
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
