import React, { useState } from 'react';
import {
  GitCommit,
  Scissors,
  BarChart3,
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  Layers,
  ArrowRight,
  Filter,
  Activity,
  Zap,
  HelpCircle,
  Cpu
} from 'lucide-react';
import { api } from '../api/client';
import {
  DiscreteRDHeapingResult,
  DiscreteRDHeapingRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const DiscreteRDHeapingCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [runningId, setRunningId] = useState<string>('');
  const [outcomeId, setOutcomeId] = useState<string>('');
  const [cutoff, setCutoff] = useState<number>(0.0);
  const [bandwidth, setBandwidth] = useState<string>('');
  const [kernel, setKernel] = useState<'triangular' | 'uniform' | 'epanechnikov'>('triangular');
  const [focalInterval, setFocalInterval] = useState<number>(5.0);
  const [nPermutations, setNPermutations] = useState<number>(500);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiscreteRDHeapingResult | null>(null);
  const [activeTab, setActiveTab] = useState<'honest_bounds' | 'heaping_diagnostics' | 'local_randomization' | 'apa'>('honest_bounds');
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'single_choice'
  );

  const handleRun = async () => {
    if (!runningId || !outcomeId) {
      setError('Vui lòng chọn cả biến Chạy X và biến Kết quả Y.');
      return;
    }
    if (runningId === outcomeId) {
      setError('Biến chạy X và biến kết quả Y không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: DiscreteRDHeapingRequest = {
      running_question_id: runningId,
      outcome_question_id: outcomeId,
      cutoff: Number(cutoff),
      bandwidth: bandwidth ? parseFloat(bandwidth) : undefined,
      kernel,
      focal_rounding_interval: Number(focalInterval),
      n_permutations: Number(nPermutations),
      scope,
    };

    try {
      const data = await api.runDiscreteRDHeaping(surveyId, payload);
      setResult(data);
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực thi phân tích Discrete RDD.');
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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <Scissors className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold tracking-tight text-white">
              Regression Discontinuity with Discrete Running Variables & Heaping Engine
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Ước lượng gián đoạn hồi quy với biến chạy rời rạc, làm tròn tập trung (Heaping) và khoảng tin cậy Minimax Honest (Kolesár & Rothe 2018 AER; Barreca et al. 2016)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
            Kolesár & Rothe 2018 AER
          </span>
          <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            Donut-Hole Robust
          </span>
        </div>
      </div>

      {/* Config Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Running Var X */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <GitCommit className="w-3.5 h-3.5 text-indigo-400" />
            Biến Chạy Rời Rạc X <span className="text-rose-400">*</span>
          </label>
          <select
            value={runningId}
            onChange={(e) => setRunningId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">-- Chọn biến Chạy X --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Var Y */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            Biến Kết Quả Y <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeId}
            onChange={(e) => setOutcomeId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="">-- Chọn biến Kết quả Y --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Cutoff c */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Scissors className="w-3.5 h-3.5 text-rose-400" />
            Điểm Ngưỡng Cutoff (c) <span className="text-rose-400">*</span>
          </label>
          <input
            type="number"
            step="any"
            value={cutoff}
            onChange={(e) => setCutoff(Number(e.target.value))}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
            placeholder="0.0"
          />
        </div>

        {/* Bandwidth h */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-amber-400" />
            Băng Thông (Bandwidth h)
          </label>
          <input
            type="number"
            step="any"
            value={bandwidth}
            onChange={(e) => setBandwidth(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
            placeholder="Tự động tối ưu (IK / RoT)"
          />
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-1">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Hàm Hạt Nhân (Kernel):</label>
          <select
            value={kernel}
            onChange={(e: any) => setKernel(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
          >
            <option value="triangular">Triangular (Tam giác - Tối ưu biên)</option>
            <option value="epanechnikov">Epanechnikov (Parabol)</option>
            <option value="uniform">Uniform (Đều)</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Khoảng Làm Tròn (Focal Interval):</label>
          <input
            type="number"
            step="any"
            min={1}
            value={focalInterval}
            onChange={(e) => setFocalInterval(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            placeholder="5.0"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Hoán Vị Ngẫu Nhiên Hóa (Permutations):</label>
          <input
            type="number"
            min={100}
            max={2000}
            value={nPermutations}
            onChange={(e) => setNPermutations(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Phạm Vi Dữ Liệu:</label>
          <select
            value={scope}
            onChange={(e: any) => setScope(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
          >
            <option value="all">Tất cả bản ghi</option>
            <option value="verified_clean">Chỉ bản ghi sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Run Button & Error */}
      <div className="flex items-center justify-between pt-2">
        {error && (
          <div className="flex items-center gap-2 text-rose-400 text-xs bg-rose-500/10 px-3 py-2 rounded-lg border border-rose-500/20">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
        <div className="ml-auto">
          <button
            onClick={handleRun}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg font-semibold text-sm bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Đang ước lượng Minimax Bounds & Heaping...</span>
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                <span>Thực thi Discrete RDD &amp; Honest Bounds</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results View */}
      {result && (
        <div className="mt-6 space-y-6 pt-6 border-t border-slate-800 animate-fadeIn">
          {/* Key Metric Badges */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {/* Conventional RD Jump */}
            <div className="bg-indigo-950/20 border border-indigo-500/30 rounded-lg p-3.5 relative overflow-hidden">
              <div className="text-xs text-indigo-400 font-medium">Bước Nhảy RD Truyền Thống</div>
              <div className="text-2xl font-bold text-white mt-1">
                τ = {result.conventional_rdd.tau_estimate.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                SE = {result.conventional_rdd.standard_error.toFixed(3)} • p = {result.conventional_rdd.p_value.toFixed(4)}
              </div>
            </div>

            {/* Discreteness Diagnostics */}
            <div className="bg-slate-800/40 border border-slate-700 rounded-lg p-3.5 relative overflow-hidden">
              <div className="text-xs text-slate-400 font-medium">Đặc Tính Tập Giá Trị (Support)</div>
              <div className="text-2xl font-bold text-white mt-1">
                {result.discreteness_diagnostics.num_support_points} Điểm
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">
                Khoảng cách ngưỡng: Δ = {result.discreteness_diagnostics.cutoff_gap.toFixed(3)}
              </div>
            </div>

            {/* Heaping Diagnostics */}
            <div className={`p-3.5 rounded-lg border ${
              result.discreteness_diagnostics.heaping_ratio > 1.3
                ? 'bg-amber-950/20 border-amber-500/30'
                : 'bg-emerald-950/20 border-emerald-500/30'
            }`}>
              <div className="text-xs text-slate-400 font-medium">Mức Độ Làm Tròn (Heaping Ratio)</div>
              <div className={`text-2xl font-bold mt-1 ${
                result.discreteness_diagnostics.heaping_ratio > 1.3 ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {result.discreteness_diagnostics.heaping_ratio.toFixed(2)}x
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                {result.discreteness_diagnostics.heaping_severity}
              </div>
            </div>

            {/* Donut Hole Robustness */}
            <div className={`p-3.5 rounded-lg border ${
              result.donut_hole_diagnostics.is_heaping_robust
                ? 'bg-emerald-950/20 border-emerald-500/30'
                : 'bg-rose-950/20 border-rose-500/30'
            }`}>
              <div className="text-xs text-slate-400 font-medium">Donut-Hole RDD (Barreca 2016)</div>
              <div className="text-2xl font-bold text-white mt-1">
                τ = {result.donut_hole_diagnostics.tau_donut.toFixed(3)}
              </div>
              <div className={`text-[11px] mt-0.5 ${
                result.donut_hole_diagnostics.is_heaping_robust ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {result.donut_hole_diagnostics.is_heaping_robust ? 'Bền vững với Heaping' : 'Cảnh báo sai lệch do làm tròn'}
              </div>
            </div>
          </div>

          {/* SVG Visualizer */}
          <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 overflow-hidden shadow-inner">
            <div
              className="w-full flex justify-center"
              dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
            />
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('honest_bounds')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'honest_bounds'
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Khoảng Tin Cậy Minimax Honest (Kolesár &amp; Rothe 2018)
            </button>
            <button
              onClick={() => setActiveTab('heaping_diagnostics')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'heaping_diagnostics'
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Chẩn Đoán Làm Tròn &amp; Donut-Hole
            </button>
            <button
              onClick={() => setActiveTab('local_randomization')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'local_randomization'
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              Ngẫu Nhiên Hóa Cục Bộ (Cattaneo 2015)
            </button>
            <button
              onClick={() => setActiveTab('apa')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'apa'
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Copy className="w-3.5 h-3.5" />
              Báo Cáo APA 7th
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'honest_bounds' && (
            <div className="space-y-4">
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-300 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Độ Cong Giới Hạn M (|f''| ≤ M)</th>
                      <th className="px-4 py-3 text-right">Sai Số Ước Lượng Tối Đa (Bias)</th>
                      <th className="px-4 py-3 text-right">Tỷ Số Bias / SE</th>
                      <th className="px-4 py-3 text-right">Giá Trị Tới Hạn cv</th>
                      <th className="px-4 py-3 text-right">Khoảng Tin Cậy 95% Honest</th>
                      <th className="px-4 py-3 text-center">Độ Rộng CI</th>
                      <th className="px-4 py-3 text-center">Ý Nghĩa Thống Kê</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                    {result.kolesar_rothe_honest_bounds.map((h, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-4 py-2.5 font-bold text-slate-200">M = {h.curvature_bound_m}</td>
                        <td className="px-4 py-2.5 text-right text-slate-400">{h.worst_case_bias.toFixed(4)}</td>
                        <td className="px-4 py-2.5 text-right text-slate-400">{h.bias_se_ratio.toFixed(2)}</td>
                        <td className="px-4 py-2.5 text-right font-mono text-indigo-400">{h.critical_value.toFixed(2)}</td>
                        <td className="px-4 py-2.5 text-right font-medium text-slate-200">
                          [{h.honest_ci_95[0].toFixed(3)}, {h.honest_ci_95[1].toFixed(3)}]
                        </td>
                        <td className="px-4 py-2.5 text-center text-slate-400">{h.honest_ci_length.toFixed(3)}</td>
                        <td className="px-4 py-2.5 text-center">
                          {h.contains_zero ? (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                              Chứa 0 (Không ý nghĩa)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                              Bác bỏ H0 (Ý nghĩa p &lt; 0.05)
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-[11px] text-slate-400">
                * Lưu ý phương pháp: Khi biến chạy có tính rời rạc, các phương pháp hồi quy đa thức cục bộ thông thường có thể sinh ra sai số chuẩn phi thực tế (Lee &amp; Card 2008 bị bác bỏ bởi Kolesár &amp; Rothe 2018 AER). Khung Minimax Honest đảm bảo xác suất bao phủ danh định 95% bằng cách hiệu chỉnh phân phối chuẩn gập (folded normal) theo độ cong cực đại M.
              </p>
            </div>
          )}

          {activeTab === 'heaping_diagnostics' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 space-y-3">
                <div className="font-semibold text-indigo-400 flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4" />
                  Đặc Trưng Tập Điểm Rời Rạc (Support Discreteness)
                </div>
                <div className="space-y-1.5 text-slate-300">
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Tổng số điểm hỗ trợ duy nhất:</span>
                    <span className="font-semibold">{result.discreteness_diagnostics.num_support_points} điểm</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Điểm hỗ trợ sát bên trái ngưỡng:</span>
                    <span className="font-semibold text-blue-400">{result.discreteness_diagnostics.closest_left_point}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Điểm hỗ trợ sát bên phải ngưỡng:</span>
                    <span className="font-semibold text-emerald-400">{result.discreteness_diagnostics.closest_right_point}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Khoảng cách gián đoạn giữa 2 điểm ngưỡng:</span>
                    <span className="font-semibold">{result.discreteness_diagnostics.cutoff_gap.toFixed(3)}</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 space-y-3">
                <div className="font-semibold text-amber-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  Kiểm Định Donut-Hole (Barreca et al. 2016)
                </div>
                <div className="space-y-1.5 text-slate-300">
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Số quan sát bị loại bỏ tại điểm tụ (Heaped):</span>
                    <span className="font-semibold">{result.donut_hole_diagnostics.dropped_observations}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Ước lượng τ sau khi loại bỏ điểm tụ:</span>
                    <span className="font-semibold text-indigo-400">{result.donut_hole_diagnostics.tau_donut.toFixed(3)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Độ lệch so với ước lượng chuẩn (Delta):</span>
                    <span className="font-semibold">{result.donut_hole_diagnostics.delta_from_baseline.toFixed(3)}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Đánh giá độ bền vững:</span>
                    <span className={`font-semibold ${result.donut_hole_diagnostics.is_heaping_robust ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {result.donut_hole_diagnostics.is_heaping_robust ? 'Bền vững (Không bị bóp méo bởi làm tròn)' : 'Nhạy cảm với làm tròn'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'local_randomization' && (
            <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 space-y-3 text-xs">
              <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <Zap className="w-4 h-4" />
                Suy Luận Ngẫu Nhiên Hóa Cục Bộ (Cattaneo, Frandsen, &amp; Titiunik 2015)
              </div>
              <p className="text-slate-400">
                Khi các quan sát phân bố trên các điểm rời rạc sát ngưỡng, mô hình coi các cá nhân trong cửa sổ sát ngưỡng như một thử nghiệm ngẫu nhiên thực sự và thực hiện kiểm định hoán vị Fisher chính xác.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-[11px]">Cửa sổ phân tích</div>
                  <div className="font-bold text-slate-200 mt-1">
                    [{result.local_randomization_inference.window_bounds[0]}, {result.local_randomization_inference.window_bounds[1]}]
                  </div>
                </div>
                <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-[11px]">Quan sát trong cửa sổ</div>
                  <div className="font-bold text-slate-200 mt-1">
                    {result.local_randomization_inference.window_observations} quan sát
                  </div>
                </div>
                <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-[11px]">Chênh lệch trung bình</div>
                  <div className="font-bold text-indigo-400 mt-1">
                    {result.local_randomization_inference.observed_mean_diff.toFixed(3)}
                  </div>
                </div>
                <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-[11px]">Fisher Exact p-value</div>
                  <div className={`font-bold mt-1 ${
                    result.local_randomization_inference.is_randomization_significant ? 'text-emerald-400' : 'text-slate-300'
                  }`}>
                    p = {result.local_randomization_inference.fisher_exact_p_value.toFixed(4)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'apa' && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">
                  Diễn giải kết quả chuẩn APA 7th Edition:
                </span>
                <button
                  onClick={handleCopyAPA}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-md transition-colors flex items-center gap-1.5"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép văn bản'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif bg-slate-900/60 p-4 rounded-lg border border-slate-800/80 italic">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
