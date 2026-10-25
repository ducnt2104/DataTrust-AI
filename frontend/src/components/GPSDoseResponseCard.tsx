import React, { useState } from 'react';
import {
  TrendingUp,
  Activity,
  Gauge,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  Info,
  CheckSquare,
  Square,
  BarChart3,
  Sliders,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import { GPSDoseResponseResult } from '../types/survey';

interface GPSDoseResponseCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const GPSDoseResponseCard: React.FC<GPSDoseResponseCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GPSDoseResponseResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [covariateQids, setCovariateQids] = useState<string[]>([]);
  const [nGridPoints, setNGridPoints] = useState<number>(30);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'dose_response' | 'marginal_effects' | 'svg'>('dose_response');

  const toggleCovariate = (qid: string) => {
    setCovariateQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!treatmentQid) {
      setError('Vui lòng chọn biến can thiệp liên tục (Continuous Dosage T: số giờ đào tạo, mức trợ cấp, liều lượng...).');
      return;
    }
    if (!outcomeQid) {
      setError('Vui lòng chọn biến kết quả liên tục (Outcome Y).');
      return;
    }
    if (treatmentQid === outcomeQid) {
      setError('Biến can thiệp và biến kết quả không được trùng nhau.');
      return;
    }
    if (covariateQids.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến kiểm soát gây nhiễu (Confounders X).');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runGPSDoseResponse(surveyId, {
        treatment_question_id: treatmentQid,
        outcome_question_id: outcomeQid,
        covariate_question_ids: covariateQids,
        n_grid_points: nGridPoints,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng hàm liều lượng - phản hồi GPS.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API Generalized Propensity Score.');
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Generalized Propensity Score (GPS) Causal Dose-Response
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                Hirano &amp; Imbens (2004) · Imai &amp; van Dyk (2004)
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Phân tích nhân quả cho can thiệp liên tục: Ước lượng hàm phản hồi trung bình <span className="font-mono text-cyan-400">μ(t) = E[Y(t)]</span> và đạo hàm tác động biên <span className="font-mono text-cyan-400">dμ(t)/dt</span> để tìm liều lượng tối ưu.
            </p>
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Đang tính toán GPS (ADRF)...</span>
            </>
          ) : (
            <>
              <TrendingUp className="w-4 h-4" />
              <span>Ước lượng Hàm Liều Lượng</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 py-5 border-b border-slate-800 text-xs">
        {/* Treatment Question */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Biến Can Thiệp Liên Tục (Dosage T):</label>
          <select
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">-- Chọn biến can thiệp liên tục (Giờ, Tiền, Liều...) --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title.length > 45 ? `${q.title.slice(0, 45)}...` : q.title}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400">Số giờ đào tạo, số tiền ưu đãi, thời gian tiếp xúc.</p>
        </div>

        {/* Outcome Question */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Biến Kết Quả (Outcome Y):</label>
          <select
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title.length > 45 ? `${q.title.slice(0, 45)}...` : q.title}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400">Doanh thu, năng suất, điểm đánh giá hiệu quả.</p>
        </div>

        {/* Grid points & Scope */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="font-medium text-slate-300">Độ Phân Giải Lưới (Grid Points):</label>
            <span className="text-cyan-400 font-mono">{nGridPoints} mốc</span>
          </div>
          <select
            value={nGridPoints}
            onChange={(e) => setNGridPoints(Number(e.target.value))}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value={20}>20 mốc liều lượng (Nhanh)</option>
            <option value={30}>30 mốc liều lượng (Chuẩn mực)</option>
            <option value={50}>50 mốc liều lượng (Chi tiết cao)</option>
          </select>
          <p className="text-[11px] text-slate-400">Độ mịn của đường cong phản hồi trung bình.</p>
        </div>

        {/* Info Tip */}
        <div className="space-y-1.5 bg-slate-800/30 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <span>
            Khác với PSM nhị phân, <strong>GPS</strong> cho phép đánh giá quy luật <em>lợi nhuận cận biên giảm dần</em> và xác định điểm liều lượng tối ưu <span className="font-mono text-cyan-300">t*</span> nơi đạo hàm <span className="font-mono text-cyan-300">dμ/dt = 0</span>.
          </span>
        </div>
      </div>

      {/* Covariates Selection (X) */}
      <div className="py-4 border-b border-slate-800">
        <label className="font-medium text-xs text-slate-300 flex items-center justify-between mb-2">
          <span>Chọn Các Biến Kiểm Soát Gây Nhiễu (Confounders X):</span>
          <span className="text-slate-400 font-normal">Đã chọn: {covariateQids.length} biến</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto pr-1">
          {questions
            .filter((q) => q.id !== treatmentQid && q.id !== outcomeQid)
            .map((q) => {
              const isSelected = covariateQids.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleCovariate(q.id)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors cursor-pointer border ${
                    isSelected
                      ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  )}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="my-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="mt-6 space-y-6">
          {/* Key Metrics Banners */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Liều Lượng Đỉnh Tối Ưu (t*)</span>
              <span className="text-lg font-bold text-cyan-400">
                {result.diagnostics.optimal_dosage_peak.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Điểm uốn dμ/dt = 0
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Kết Quả Đỉnh μ(t*)</span>
              <span className="text-lg font-bold text-emerald-400">
                {result.diagnostics.peak_expected_outcome.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Cơ sở ban đầu: {result.diagnostics.baseline_expected_outcome.toFixed(2)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Lợi Ích Ròng Nhân Quả</span>
              <span className="text-lg font-bold text-indigo-300">
                +{result.diagnostics.net_causal_gain_at_optimal.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Mức tăng tối đa
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Dải Liều Lượng Can Thiệp</span>
              <span className="text-base font-bold text-slate-200">
                {result.diagnostics.treatment_min.toFixed(1)} - {result.diagnostics.treatment_max.toFixed(1)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                TB: {result.diagnostics.treatment_mean.toFixed(1)} ± {result.diagnostics.treatment_sd.toFixed(1)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Độ Khớp Mô Hình Can Thiệp</span>
              <span className="text-base font-bold text-sky-400">
                {(result.diagnostics.treatment_model_r2 * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                GPS R² (σ = {result.diagnostics.treatment_model_sigma.toFixed(2)})
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Độ Khớp Mô Hình Kết Quả</span>
              <span className="text-base font-bold text-emerald-400">
                {(result.diagnostics.outcome_model_r2 * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Outcome R² (Flexible quadratic)
              </span>
            </div>
          </div>

          {/* Verdict Banner */}
          <div className="p-4 rounded-xl border bg-cyan-500/10 border-cyan-500/20 text-cyan-300 text-xs flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-cyan-400" />
              <span>
                <strong>Khuyến nghị Liều lượng Tối ưu:</strong> Điểm liều lượng hiệu quả cao nhất đạt được tại <span className="font-mono font-bold">{result.diagnostics.optimal_dosage_peak.toFixed(2)}</span> đơn vị. Vượt quá ngưỡng này, lợi nhuận cận biên chuyển sang chiều hướng giảm dần hoặc âm.
              </span>
            </div>
            <span className="text-[11px] font-mono opacity-80 shrink-0">
              N = {result.diagnostics.sample_size} | K = {result.diagnostics.n_covariates}
            </span>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('dose_response')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'dose_response'
                  ? 'border-cyan-500 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Hàm Phản Hồi Trung Bình (ADRF μ(t))
            </button>
            <button
              onClick={() => setActiveTab('marginal_effects')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'marginal_effects'
                  ? 'border-cyan-500 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Tác Động Biên Cận (Marginal Return dμ/dt)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'svg'
                  ? 'border-cyan-500 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Biểu Đồ Đường Cong Phản Hồi &amp; Tác Động Biên</span>
            </button>
          </div>

          {/* Tab 1: Dose Response Table */}
          {activeTab === 'dose_response' && result.dose_response_curve && (
            <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-80 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800 sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Mốc Liều Lượng Can Thiệp (t)</th>
                    <th className="py-2.5 px-3 text-right">Kỳ Vọng Kết Quả Nhân Quả μ(t)</th>
                    <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-center">Khoảng Tin Cậy 95%</th>
                    <th className="py-2.5 px-3 text-center">Vị Trí So Với Đỉnh</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.dose_response_curve.map((row, idx) => {
                    const isPeak = Math.abs(row.dosage_t - result.diagnostics!.optimal_dosage_peak) < 0.05;
                    return (
                      <tr key={idx} className={isPeak ? 'bg-cyan-500/10' : 'hover:bg-slate-800/30'}>
                        <td className="py-2 px-3 font-bold text-white">t = {row.dosage_t.toFixed(2)}</td>
                        <td className="py-2 px-3 text-right text-emerald-400 font-semibold">{row.expected_outcome_mu.toFixed(3)}</td>
                        <td className="py-2 px-3 text-right text-slate-400">{row.standard_error.toFixed(3)}</td>
                        <td className="py-2 px-3 text-center text-slate-400">[{row.ci_95_lower.toFixed(2)}, {row.ci_95_upper.toFixed(2)}]</td>
                        <td className="py-2 px-3 text-center">
                          {isPeak ? (
                            <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-sans text-[10px] font-bold">
                              Đỉnh Tối Ưu (Optimal)
                            </span>
                          ) : row.dosage_t < result.diagnostics!.optimal_dosage_peak ? (
                            <span className="text-slate-400 text-[10px] font-sans">Giai đoạn tăng trưởng</span>
                          ) : (
                            <span className="text-amber-400 text-[10px] font-sans">Lợi nhuận giảm dần</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Marginal Effects Table */}
          {activeTab === 'marginal_effects' && result.marginal_effects_curve && (
            <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-80 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800 sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Mốc Liều Lượng Can Thiệp (t)</th>
                    <th className="py-2.5 px-3 text-right">Tác Động Biên dμ(t)/dt</th>
                    <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-center">Khoảng Tin Cậy 95%</th>
                    <th className="py-2.5 px-3 text-center">Chiều Hướng Lợi Nhuận</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.marginal_effects_curve.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 font-bold text-white">t = {row.dosage_t.toFixed(2)}</td>
                      <td className={`py-2 px-3 text-right font-semibold ${row.marginal_treatment_effect > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {row.marginal_treatment_effect > 0 ? `+${row.marginal_treatment_effect.toFixed(4)}` : row.marginal_treatment_effect.toFixed(4)}
                      </td>
                      <td className="py-2 px-3 text-right text-slate-400">{row.standard_error.toFixed(4)}</td>
                      <td className="py-2 px-3 text-center text-slate-400">[{row.ci_95_lower.toFixed(3)}, {row.ci_95_upper.toFixed(3)}]</td>
                      <td className="py-2 px-3 text-center font-sans">
                        {row.marginal_treatment_effect > 0.05 ? (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">
                            Lợi nhuận biên dương
                          </span>
                        ) : row.marginal_treatment_effect < -0.05 ? (
                          <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 text-[10px]">
                            Lợi nhuận biên âm (quá liều)
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[10px]">
                            Tiệm cận bão hòa (dμ/dt ≈ 0)
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: SVG Visualizations */}
          {activeTab === 'svg' && result.svg_visualization && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col items-center justify-center overflow-hidden">
              <div
                className="w-full max-w-4xl flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-800/40 border border-slate-700/60 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  Báo Cáo Học Thuật Chuẩn APA 7th (Generalized Propensity Score Dose-Response)
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-cyan-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép đoạn văn'}</span>
                </button>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line bg-slate-900/50 p-3 rounded-lg border border-slate-800/80">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
