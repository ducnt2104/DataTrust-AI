import React, { useState } from 'react';
import {
  Sparkles,
  Layers,
  Scale,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  Info,
  CheckSquare,
  Square,
  BarChart3,
  GitBranch
} from 'lucide-react';
import { api } from '../api/client';
import { LatentModerationResult } from '../types/survey';

interface LatentModerationCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const LatentModerationCard: React.FC<LatentModerationCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LatentModerationResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [predictorItemIds, setPredictorItemIds] = useState<string[]>([]);
  const [moderatorItemIds, setModeratorItemIds] = useState<string[]>([]);
  const [outcomeItemIds, setOutcomeItemIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'coefficients' | 'simple_slopes' | 'svg'>('coefficients');

  const togglePredictor = (qid: string) => {
    setPredictorItemIds(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const toggleModerator = (qid: string) => {
    setModeratorItemIds(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const toggleOutcome = (qid: string) => {
    setOutcomeItemIds(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (predictorItemIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 câu hỏi chỉ báo cho Biến độc lập tiềm ẩn (ξ₁).');
      return;
    }
    if (moderatorItemIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 câu hỏi chỉ báo cho Biến điều tiết tiềm ẩn (ξ₂).');
      return;
    }
    if (outcomeItemIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 câu hỏi chỉ báo cho Biến phụ thuộc tiềm ẩn (η).');
      return;
    }

    // Overlap checks
    const hasOverlap = (a: string[], b: string[]) => a.some(id => b.includes(id));
    if (hasOverlap(predictorItemIds, moderatorItemIds) || hasOverlap(predictorItemIds, outcomeItemIds) || hasOverlap(moderatorItemIds, outcomeItemIds)) {
      setError('Các câu hỏi chỉ báo không được trùng nhau giữa các nhân tố tiềm ẩn.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runLatentModeration(surveyId, {
        predictor_item_ids: predictorItemIds,
        moderator_item_ids: moderatorItemIds,
        outcome_item_ids: outcomeItemIds,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình cấu trúc tiềm ẩn LMS.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API Latent Moderated Structural Equations.');
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
          <div className="p-2 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400">
            <GitBranch className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Latent Moderated Structural Equations (LMS / QML)
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                Klein &amp; Moosbrugger (2000) · Marsh et al. (2004)
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Ước lượng tương tác phi tuyến giữa các biến tiềm ẩn <span className="font-mono text-purple-400">ξ₁ × ξ₂ → η</span>; triệt tiêu hoàn toàn hiện tượng suy giảm kích thước hiệu ứng (Attenuation Bias) do sai số đo lường khảo sát.
            </p>
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-purple-600/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Đang ước lượng LMS (QML)...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Ước lượng Tương Tác Tiềm Ẩn</span>
            </>
          )}
        </button>
      </div>

      {/* Item Selection Grids */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 py-5 border-b border-slate-800 text-xs">
        {/* Predictor Factor xi_1 */}
        <div className="space-y-2 bg-slate-800/30 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between">
            <label className="font-semibold text-sky-400">1. Nhân tố Độc lập Tiềm ẩn (ξ₁):</label>
            <span className="text-[11px] text-slate-400">Đã chọn: {predictorItemIds.length}</span>
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
            {questions.map((q) => {
              const isSel = predictorItemIds.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => togglePredictor(q.id)}
                  className={`w-full flex items-center gap-2 p-1.5 rounded text-left transition-colors cursor-pointer text-[11px] ${
                    isSel ? 'bg-sky-500/20 text-sky-300 font-medium' : 'text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  {isSel ? <CheckSquare className="w-3.5 h-3.5 text-sky-400 shrink-0" /> : <Square className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Moderator Factor xi_2 */}
        <div className="space-y-2 bg-slate-800/30 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between">
            <label className="font-semibold text-purple-400">2. Nhân tố Điều tiết Tiềm ẩn (ξ₂):</label>
            <span className="text-[11px] text-slate-400">Đã chọn: {moderatorItemIds.length}</span>
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
            {questions.map((q) => {
              const isSel = moderatorItemIds.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleModerator(q.id)}
                  className={`w-full flex items-center gap-2 p-1.5 rounded text-left transition-colors cursor-pointer text-[11px] ${
                    isSel ? 'bg-purple-500/20 text-purple-300 font-medium' : 'text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  {isSel ? <CheckSquare className="w-3.5 h-3.5 text-purple-400 shrink-0" /> : <Square className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Outcome Factor eta */}
        <div className="space-y-2 bg-slate-800/30 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between">
            <label className="font-semibold text-emerald-400">3. Nhân tố Kết quả Tiềm ẩn (η):</label>
            <span className="text-[11px] text-slate-400">Đã chọn: {outcomeItemIds.length}</span>
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
            {questions.map((q) => {
              const isSel = outcomeItemIds.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleOutcome(q.id)}
                  className={`w-full flex items-center gap-2 p-1.5 rounded text-left transition-colors cursor-pointer text-[11px] ${
                    isSel ? 'bg-emerald-500/20 text-emerald-300 font-medium' : 'text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  {isSel ? <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> : <Square className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Scope and Tip */}
      <div className="flex flex-col sm:flex-row items-center justify-between py-3 border-b border-slate-800 gap-4 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Phạm vi khảo sát:</span>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-purple-500 text-xs"
          >
            <option value="all">Tất cả phản hồi hợp lệ</option>
            <option value="verified_clean">Chỉ mẫu đã xác thực sạch (Verified Clean)</option>
          </select>
        </div>

        <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-purple-400" />
          <span>Theo Klein &amp; Muthén (2007), QML LMS tính toán độ dốc đơn giản (Simple Slopes) tại ±1 SD của biến điều tiết.</span>
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
              <span className="text-[11px] text-slate-400 block">Tương Tác Tiềm Ẩn (γ₃)</span>
              <span className={`text-lg font-bold ${result.diagnostics.has_significant_moderation ? 'text-purple-400' : 'text-slate-300'}`}>
                {result.diagnostics.latent_interaction_gamma.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {result.diagnostics.has_significant_moderation ? 'Có ý nghĩa (p < 0.05)' : 'Chưa có ý nghĩa (ns)'}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Hiệu Ứng Cohen's f²</span>
              <span className="text-lg font-bold text-emerald-400">
                {result.diagnostics.cohen_f2_effect_size.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5 truncate" title={result.diagnostics.f2_classification}>
                {result.diagnostics.f2_classification}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Hệ Số R² Tiềm Ẩn</span>
              <span className="text-lg font-bold text-sky-400">
                {(result.diagnostics.structural_r2 * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Phương sai biến kết quả η
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Mức Độ Phục Hồi Suy Giảm</span>
              <span className="text-lg font-bold text-amber-400">
                +{result.diagnostics.attenuation_bias_gap_pct.toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                So với Naive OLS: {result.diagnostics.naive_observed_interaction_gamma.toFixed(3)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Độ Tin Cậy Tiềm Ẩn (α)</span>
              <span className="text-base font-bold text-slate-200">
                {result.diagnostics.latent_predictor_reliability_alpha.toFixed(2)} | {result.diagnostics.latent_moderator_reliability_alpha.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                ξ₁ | ξ₂ (Cronbach's α)
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tương Quan Tiềm Ẩn (ϕ₁₂)</span>
              <span className="text-lg font-bold text-indigo-300">
                {result.diagnostics.latent_correlation_xi1_xi2.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Corr(ξ₁, ξ₂)
              </span>
            </div>
          </div>

          {/* Verdict Banner */}
          <div className={`p-4 rounded-xl border text-xs flex items-center justify-between gap-4 ${
            result.diagnostics.has_significant_moderation
              ? 'bg-purple-500/10 border-purple-500/20 text-purple-300'
              : 'bg-slate-800/60 border-slate-700 text-slate-300'
          }`}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-purple-400" />
              <span>
                <strong>Kết luận Điều tiết Tiềm ẩn:</strong> {result.diagnostics.has_significant_moderation
                  ? 'Phát hiện tác động điều tiết có ý nghĩa thống kê (p < 0.05). Mức độ ảnh hưởng của ξ₁ lên η thay đổi phụ thuộc vào giá trị của ξ₂.'
                  : 'Chưa phát hiện tác động điều tiết có ý nghĩa thống kê (p >= 0.05).'}
              </span>
            </div>
            {result.diagnostics.johnson_neyman_cutoffs.length > 0 && (
              <span className="text-[11px] font-mono opacity-80 shrink-0">
                JN Cutoffs: {result.diagnostics.johnson_neyman_cutoffs.join(', ')} SD
              </span>
            )}
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('coefficients')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'coefficients'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Hệ Số Cấu Trúc Tiềm Ẩn (LMS Parameters)
            </button>
            <button
              onClick={() => setActiveTab('simple_slopes')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'simple_slopes'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Phân Tích Độ Dốc Đơn Giản (Simple Slopes ±1 SD)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'svg'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Biểu Đồ Bề Mặt Tương Tác 3D &amp; Simple Slopes</span>
            </button>
          </div>

          {/* Tab 1: Coefficients */}
          {activeTab === 'coefficients' && result.coefficients && (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Tham Số Cấu Trúc</th>
                    <th className="py-2.5 px-3">Ý Nghĩa Phương Trình</th>
                    <th className="py-2.5 px-3 text-right">Ước Lượng (γ)</th>
                    <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-right">z-stat</th>
                    <th className="py-2.5 px-3 text-right">p-value</th>
                    <th className="py-2.5 px-3 text-center">Khoảng Tin Cậy 95%</th>
                    <th className="py-2.5 px-3 text-center">Trạng Thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.coefficients.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-bold text-purple-400">{row.parameter}</td>
                      <td className="py-2.5 px-3 font-sans text-white">{row.label}</td>
                      <td className="py-2.5 px-3 text-right text-emerald-400 font-semibold">{row.estimate.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-400">{row.standard_error.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-300">{row.z_statistic.toFixed(3)}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className={row.p_value < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                          {row.p_value < 0.001 ? '< 0.001' : row.p_value.toFixed(4)}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-center text-slate-400">
                        [{row.ci_95_lower.toFixed(3)}, {row.ci_95_upper.toFixed(3)}]
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {row.is_significant ? (
                          <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px]">
                            p &lt; 0.05
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400 text-[10px]">
                            ns
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Simple Slopes */}
          {activeTab === 'simple_slopes' && result.simple_slopes && (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Mức Độ Biến Điều Tiết (ξ₂)</th>
                    <th className="py-2.5 px-3 text-center">Giá Trị Chuẩn Hóa</th>
                    <th className="py-2.5 px-3 text-right">Độ Dốc Đơn Giản (Simple Slope)</th>
                    <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-right">z-stat</th>
                    <th className="py-2.5 px-3 text-right">p-value</th>
                    <th className="py-2.5 px-3 text-center">Khoảng Tin Cậy 95%</th>
                    <th className="py-2.5 px-3 text-center">Ý Nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.simple_slopes.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-sans font-medium text-white">{row.level_label}</td>
                      <td className="py-2.5 px-3 text-center text-slate-400">{row.moderator_value > 0 ? `+${row.moderator_value}` : row.moderator_value} SD</td>
                      <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">{row.simple_slope.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-400">{row.standard_error.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-300">{row.z_statistic.toFixed(3)}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className={row.p_value < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                          {row.p_value < 0.001 ? '< 0.001' : row.p_value.toFixed(4)}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-center text-slate-400">
                        [{row.ci_95_lower.toFixed(3)}, {row.ci_95_upper.toFixed(3)}]
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {row.is_significant ? (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">
                            p &lt; 0.05
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400 text-[10px]">
                            ns
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
                  <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                  Báo Cáo Học Thuật Chuẩn APA 7th (Latent Moderated Structural Equations LMS)
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-purple-300 transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-purple-400" /> : <Copy className="w-3.5 h-3.5" />}
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
