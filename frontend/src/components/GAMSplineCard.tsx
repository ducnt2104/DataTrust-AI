import React, { useState } from 'react';
import {
  Activity,
  TrendingUp,
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
  Sliders,
  Copy,
  Check,
  Target,
  Maximize2
} from 'lucide-react';
import { api } from '../api/client';
import { GAMSplineResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const GAMSplineCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [predictorQid, setPredictorQid] = useState<string>('');
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [selectedCovQids, setSelectedCovQids] = useState<string[]>([]);
  const [nKnots, setNKnots] = useState<number>(10);
  const [gridPoints, setGridPoints] = useState<number>(60);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<GAMSplineResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'tipping' | 'curve'>('tipping');

  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'single_choice'].includes(q.question_type)
  );

  const toggleCovariate = (qid: string) => {
    setSelectedCovQids((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!predictorQid || !outcomeQid) {
      setError('Vui lòng chọn biến Dự Báo (Predictor X) và biến Kết Quả (Outcome Y).');
      return;
    }
    if (predictorQid === outcomeQid) {
      setError('Biến Dự Báo và Kết Quả không thể trùng nhau.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.runGAMSpline(surveyId, {
        predictor_question_id: predictorQid,
        outcome_question_id: outcomeQid,
        covariate_question_ids: selectedCovQids.length > 0 ? selectedCovQids : undefined,
        n_knots: nKnots,
        grid_points: gridPoints,
        scope
      });
      if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Mẫu khảo sát không đủ điều kiện để ước lượng mô hình GAM Spline.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích GAM Spline.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-8 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute -top-24 -right-24 w-80 h-80 bg-teal-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-gradient-to-br from-teal-500/20 to-cyan-500/20 border border-teal-500/30 rounded-xl text-teal-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Mô Hình Cộng Tính Khái Quát &amp; Đường Cong Trơn (GAM &amp; P-Splines)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/30 font-medium">
                  Hastie &amp; Tibshirani (1990) &amp; Wood (2017)
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Phát hiện mối quan hệ phi tuyến, điểm bão hòa (Tipping Points) &amp; Bậc tự do hiệu dụng (EDF)
              </p>
            </div>
          </div>
        </div>

        {/* Scope Selector */}
        <div className="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 self-start md:self-auto">
          <button
            onClick={() => setScope('all')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              scope === 'all'
                ? 'bg-teal-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Toàn bộ mẫu
          </button>
          <button
            onClick={() => setScope('verified_clean')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              scope === 'verified_clean'
                ? 'bg-emerald-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Mẫu sạch đã kiểm duyệt
          </button>
        </div>
      </div>

      {/* Configuration Section */}
      <div className="mt-6 space-y-5 bg-slate-950/40 p-5 rounded-xl border border-slate-800/60">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Predictor X */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 block">
              Biến Dự Báo Liên Tục (Continuous Predictor X):
            </label>
            <select
              value={predictorQid}
              onChange={(e) => setPredictorQid(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-teal-500"
            >
              <option value="">-- Chọn câu hỏi biến giải thích X --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === outcomeQid}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Outcome Y */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 block">
              Biến Kết Quả Liên Tục (Continuous Outcome Y):
            </label>
            <select
              value={outcomeQid}
              onChange={(e) => setOutcomeQid(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-teal-500"
            >
              <option value="">-- Chọn câu hỏi biến kết quả Y --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === predictorQid}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Covariates Multi-select */}
        <div>
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Chọn các biến kiểm soát tuyến tính Z (Tùy chọn, {selectedCovQids.length} đã chọn):</span>
            <span className="text-[11px] text-slate-500 lowercase">kiểm soát nhiễu nền</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto pr-1">
            {eligibleQuestions
              .filter((q) => q.id !== predictorQid && q.id !== outcomeQid)
              .map((q) => {
                const isSelected = selectedCovQids.includes(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => toggleCovariate(q.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border text-left flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-teal-500/20 text-teal-300 border-teal-500/50 shadow-sm'
                        : 'bg-slate-800/50 text-slate-400 border-slate-700/50 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-teal-400' : 'bg-slate-600'}`} />
                    <span className="truncate max-w-[240px]">{q.title}</span>
                  </button>
                );
              })}
          </div>
        </div>

        {/* Sliders & Action Button */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-3 border-t border-slate-800/60">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-slate-400" />
              <span className="text-xs text-slate-300 font-medium">Số Điểm Nút (Knots K):</span>
              <input
                type="range"
                min="5"
                max="20"
                step="1"
                value={nKnots}
                onChange={(e) => setNKnots(parseInt(e.target.value))}
                className="w-24 accent-teal-500 cursor-pointer"
              />
              <span className="text-xs font-mono text-teal-400 bg-teal-950/60 px-2 py-0.5 rounded border border-teal-800/50">
                {nKnots}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-300 font-medium">Lưới Điểm Đánh Giá:</span>
              <input
                type="range"
                min="30"
                max="100"
                step="10"
                value={gridPoints}
                onChange={(e) => setGridPoints(parseInt(e.target.value))}
                className="w-24 accent-teal-500 cursor-pointer"
              />
              <span className="text-xs font-mono text-teal-400 bg-teal-950/60 px-2 py-0.5 rounded border border-teal-800/50">
                {gridPoints}
              </span>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading || !predictorQid || !outcomeQid}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-xs shadow-lg shadow-teal-900/30 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Đang khớp đường cong P-Splines GCV...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Khám Phá Đường Cong Phi Tuyến</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && (
        <div className="mt-6 space-y-6">
          {/* Top-line Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Bậc Tự Do Hiệu Dụng (EDF)</span>
              <span className="text-xl font-bold text-teal-400 mt-1 block">
                {result.diagnostics?.effective_degrees_of_freedom.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {result.diagnostics && result.diagnostics.effective_degrees_of_freedom > 2.5
                  ? 'Đường cong phức tạp (EDF > 2.5)'
                  : (result.diagnostics && result.diagnostics.effective_degrees_of_freedom > 1.5 ? 'Đường cong chữ U / Đảo ngược' : 'Gần như tuyến tính')}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Kiểm Định Phi Tuyến F</span>
              <span className="text-xl font-bold mt-1 block">
                {result.diagnostics?.is_strictly_nonlinear ? (
                  <span className="text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-5 h-5" /> Phi Tuyến Có Ý Nghĩa
                  </span>
                ) : (
                  <span className="text-slate-400">Tuyến Tính Chấp Nhận Được</span>
                )}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                F = {result.diagnostics?.f_stat_nonlinearity.toFixed(2)} (p = {result.diagnostics?.p_value_nonlinearity.toFixed(4)})
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Hệ Số R² Mô Hình</span>
              <span className="text-xl font-bold text-cyan-400 mt-1 block">
                {result.diagnostics?.r_squared.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Tối ưu Lambda GCV: {result.diagnostics?.optimal_smoothing_lambda.toFixed(3)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Điểm Bão Hòa / Đảo Chiều</span>
              <span className="text-xl font-bold text-rose-400 mt-1 block">
                {result.diagnostics?.total_tipping_points} Điểm
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Ngưỡng chuyển giao f'(x) = 0
              </span>
            </div>
          </div>

          {/* SVG Visual Canvas */}
          {result.svg_visualization && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 overflow-hidden shadow-inner">
              <div
                className="w-full h-auto overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Details Tables with Navigation Tabs */}
          <div className="bg-slate-950/60 rounded-xl border border-slate-800 overflow-hidden">
            <div className="flex border-b border-slate-800 bg-slate-900/60 px-4 pt-2 gap-2">
              <button
                onClick={() => setActiveTab('tipping')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'tipping'
                    ? 'border-teal-400 text-teal-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Các Điểm Đảo Chiều &amp; Ngưỡng Bão Hòa ({result.tipping_points?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('curve')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'curve'
                    ? 'border-teal-400 text-teal-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Lưới Quỹ Đạo Đường Cong Trơn ({result.smooth_curve?.length || 0} điểm)
              </button>
            </div>

            <div className="p-4 overflow-x-auto">
              {activeTab === 'tipping' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Tọa Độ Ngưỡng (X)</th>
                      <th className="py-2.5 px-3 text-right">Phản Ứng Kỳ Vọng f(X)</th>
                      <th className="py-2.5 px-3">Phân Loại Điểm Đảo Chiều</th>
                      <th className="py-2.5 px-3">Ý Nghĩa Thực Tiễn</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.tipping_points && result.tipping_points.length > 0 ? (
                      result.tipping_points.map((tp, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-2.5 px-3 font-mono font-bold text-teal-300">{tp.x_value.toFixed(2)}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-cyan-300">{tp.predicted_response.toFixed(3)}</td>
                          <td className="py-2.5 px-3 font-semibold text-rose-400">{tp.type}</td>
                          <td className="py-2.5 px-3 text-slate-400">{tp.interpretation}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="py-4 text-center text-slate-500">
                          Đường cong trơn đơn điệu, không phát hiện điểm đảo chiều cực trị trong miền giá trị khảo sát.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {activeTab === 'curve' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Mốc Dự Báo (X)</th>
                      <th className="py-2.5 px-3 text-right">Hàm Trơn f(X)</th>
                      <th className="py-2.5 px-3 text-right">95% CI Dưới</th>
                      <th className="py-2.5 px-3 text-right">95% CI Trên</th>
                      <th className="py-2.5 px-3 text-right">Đạo Hàm Biên f'(X)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.smooth_curve?.slice(0, 15).map((pt, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-mono text-slate-200">{pt.x.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-teal-400">{pt.f_x.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{pt.ci_lower.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{pt.ci_upper.toFixed(3)}</td>
                        <td className={`py-2.5 px-3 text-right font-mono font-semibold ${pt.deriv1 >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {pt.deriv1 >= 0 ? `+${pt.deriv1.toFixed(3)}` : pt.deriv1.toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Academic Manuscript Narrative (APA 7th) */}
          {result.apa_narrative && (
            <div className="bg-slate-950/80 p-5 rounded-xl border border-slate-800 relative">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-teal-400" />
                  <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                    Thuyết Minh Học Thuật (APA 7th Edition)
                  </span>
                </div>
                <button
                  onClick={handleCopyNarrative}
                  className="flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/60 p-4 rounded-lg border border-slate-800/80">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
