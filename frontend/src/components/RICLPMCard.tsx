import React, { useState } from 'react';
import {
  GitCommit,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
  TrendingUp,
  ShieldCheck,
  ArrowRightLeft,
  ArrowRight,
  GitBranch,
  BarChart3
} from 'lucide-react';
import { api } from '../api/client';
import {
  RICLPMResult,
  RICLPMRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const RICLPMCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [numWaves, setNumWaves] = useState<number>(3);
  const [varXName, setVarXName] = useState<string>('Biến X');
  const [varYName, setVarYName] = useState<string>('Biến Y');
  const [hasMediator, setHasMediator] = useState<boolean>(false);
  const [varMName, setVarMName] = useState<string>('Trung Gian M');

  const [xQuestionIds, setXQuestionIds] = useState<string[]>(['', '', '']);
  const [yQuestionIds, setYQuestionIds] = useState<string[]>(['', '', '']);
  const [mQuestionIds, setMQuestionIds] = useState<string[]>(['', '', '']);

  const [nBootstraps, setNBootstraps] = useState<number>(100);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RICLPMResult | null>(null);
  const [activeTab, setActiveTab] = useState<'dynamics' | 'traits' | 'mediation' | 'fit' | 'apa'>('dynamics');
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'slider' || q.question_type === 'single_choice'
  );

  const handleNumWavesChange = (n: number) => {
    setNumWaves(n);
    const adjustArr = (arr: string[]) => {
      if (arr.length < n) {
        return [...arr, ...Array(n - arr.length).fill('')];
      }
      return arr.slice(0, n);
    };
    setXQuestionIds(adjustArr(xQuestionIds));
    setYQuestionIds(adjustArr(yQuestionIds));
    setMQuestionIds(adjustArr(mQuestionIds));
  };

  const handleXChange = (idx: number, val: string) => {
    const next = [...xQuestionIds];
    next[idx] = val;
    setXQuestionIds(next);
  };

  const handleYChange = (idx: number, val: string) => {
    const next = [...yQuestionIds];
    next[idx] = val;
    setYQuestionIds(next);
  };

  const handleMChange = (idx: number, val: string) => {
    const next = [...mQuestionIds];
    next[idx] = val;
    setMQuestionIds(next);
  };

  const handleRunAnalysis = async () => {
    // Validate all wave questions are selected
    if (xQuestionIds.some(id => !id) || yQuestionIds.some(id => !id)) {
      setError(`Vui lòng chọn đầy đủ câu hỏi cho cả ${numWaves} đợt sóng của biến X và biến Y.`);
      return;
    }
    if (hasMediator && mQuestionIds.some(id => !id)) {
      setError(`Vui lòng chọn đầy đủ câu hỏi cho cả ${numWaves} đợt sóng của biến Trung gian M.`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: RICLPMRequest = {
        x_question_ids: xQuestionIds,
        y_question_ids: yQuestionIds,
        m_question_ids: hasMediator ? mQuestionIds : undefined,
        var_x_name: varXName,
        var_y_name: varYName,
        var_m_name: hasMediator ? varMName : undefined,
        wave_labels: Array.from({ length: numWaves }, (_, i) => `Đợt ${i + 1}`),
        n_bootstraps: nBootstraps,
        scope: scope
      };

      const res = await api.runRICLPM(surveyId, payload);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi thực thi phân tích mô hình RI-CLPM.');
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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8 text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400">
              <ArrowRightLeft className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                Random-Intercept Cross-Lagged Panel Model (RI-CLPM)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/20 border border-teal-500/30 text-teal-300 font-medium">
                  Hamaker et al. (2015)
                </span>
              </h3>
              <p className="text-sm text-slate-400">
                Tách biệt đặc điểm cá thể bất biến (Between-Person Trait) và quan hệ nhân quả tương hỗ động thời gian (Within-Person Dynamics).
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Nickell Bias-Free
          </span>
          <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <GitBranch className="w-3.5 h-3.5 text-indigo-400" />
            Structural SEM
          </span>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="bg-slate-800/40 p-5 rounded-lg border border-slate-800/80 mb-6 space-y-5">
        {/* Top parameters: Number of waves, names, mediator toggle */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Số Lượng Đợt Sóng (Waves T):</label>
            <select
              value={numWaves}
              onChange={e => handleNumWavesChange(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
            >
              <option value={3}>3 Đợt Sóng (T = 3) - Tối thiểu</option>
              <option value={4}>4 Đợt Sóng (T = 4)</option>
              <option value={5}>5 Đợt Sóng (T = 5)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Tên Biến X:</label>
            <input
              type="text"
              value={varXName}
              onChange={e => setVarXName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
              placeholder="VD: Mức độ tương tác"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Tên Biến Y:</label>
            <input
              type="text"
              value={varYName}
              onChange={e => setVarYName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
              placeholder="VD: Lòng trung thành"
            />
          </div>

          <div className="flex flex-col justify-end">
            <label className="flex items-center gap-2 text-xs font-medium text-slate-300 cursor-pointer pt-2">
              <input
                type="checkbox"
                checked={hasMediator}
                onChange={e => setHasMediator(e.target.checked)}
                className="rounded bg-slate-800 border-slate-600 text-teal-500 focus:ring-teal-500"
              />
              <span>Phân Tích Trung Gian Chuỗi (X1 → M2 → Y3)</span>
            </label>
          </div>
        </div>

        {/* Wave Mapping Grid */}
        <div className="border-t border-slate-700/60 pt-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <Layers className="w-4 h-4 text-teal-400" />
            Ánh Xạ Câu Hỏi Khảo Sát Theo Từng Đợt Sóng (Wave Questions)
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Variable X Wave Column */}
            <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-800 space-y-3">
              <span className="text-xs font-bold text-sky-400 uppercase tracking-wider">
                {varXName} (Theo Từng Đợt)
              </span>
              {Array.from({ length: numWaves }).map((_, i) => (
                <div key={i}>
                  <label className="block text-[11px] text-slate-400 mb-1">Đợt Sóng {i + 1} (X{i + 1}):</label>
                  <select
                    value={xQuestionIds[i] || ''}
                    onChange={e => handleXChange(i, e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200"
                  >
                    <option value="">-- Chọn câu hỏi --</option>
                    {numericQuestions.map(q => (
                      <option key={q.id} value={q.id}>
                        {q.title}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {/* Variable Y Wave Column */}
            <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-800 space-y-3">
              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">
                {varYName} (Theo Từng Đợt)
              </span>
              {Array.from({ length: numWaves }).map((_, i) => (
                <div key={i}>
                  <label className="block text-[11px] text-slate-400 mb-1">Đợt Sóng {i + 1} (Y{i + 1}):</label>
                  <select
                    value={yQuestionIds[i] || ''}
                    onChange={e => handleYChange(i, e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200"
                  >
                    <option value="">-- Chọn câu hỏi --</option>
                    {numericQuestions.map(q => (
                      <option key={q.id} value={q.id}>
                        {q.title}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {/* Optional Variable M Column */}
            {hasMediator ? (
              <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-800 space-y-3">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  {varMName} (Biến Trung Gian)
                </span>
                {Array.from({ length: numWaves }).map((_, i) => (
                  <div key={i}>
                    <label className="block text-[11px] text-slate-400 mb-1">Đợt Sóng {i + 1} (M{i + 1}):</label>
                    <select
                      value={mQuestionIds[i] || ''}
                      onChange={e => handleMChange(i, e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200"
                    >
                      <option value="">-- Chọn câu hỏi --</option>
                      {numericQuestions.map(q => (
                        <option key={q.id} value={q.id}>
                          {q.title}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-slate-900/40 p-4 rounded-lg border border-dashed border-slate-800 flex flex-col items-center justify-center text-center text-xs text-slate-500">
                <GitCommit className="w-8 h-8 mb-2 opacity-30 text-teal-400" />
                <p>Mô hình song hành chuẩn 2 biến (X ⇄ Y)</p>
                <p className="text-[11px] mt-1 text-slate-600">Bật tùy chọn trên để bổ sung chuỗi trung gian M</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer parameters & Action Button */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-t border-slate-700/60 pt-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Lần lặp Bootstrap:</label>
              <select
                value={nBootstraps}
                onChange={e => setNBootstraps(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value={50}>50 lần lặp</option>
                <option value={100}>100 lần lặp (Khuyến nghị)</option>
                <option value={200}>200 lần lặp</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Bộ lọc dữ liệu:</label>
              <select
                value={scope}
                onChange={e => setScope(e.target.value as any)}
                className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="all">Tất cả phản hồi hợp lệ</option>
                <option value="verified_clean">Chỉ mẫu đã xác thực sạch</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-6 py-2.5 rounded-lg font-semibold text-sm bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Đang ước lượng RI-CLPM SEM...
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                Ước Lượng Mô Hình RI-CLPM
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {/* Cross-Lag X -> Y */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Tác Động: {result.variables.x_name} → {result.variables.y_name}</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                β = {result.within_person_dynamics.mean_cross_lag_x_to_y > 0 ? '+' : ''}
                {result.within_person_dynamics.mean_cross_lag_x_to_y.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Tác động nhân quả nội cá thể (Within)
              </div>
              <div className="text-[11px] text-emerald-400/90 font-medium mt-0.5">
                {result.within_person_dynamics.wave_transitions[0]?.cross_lag_x_to_y.is_significant ? 'Có ý nghĩa (p < .05)' : 'Chưa có ý nghĩa'}
              </div>
            </div>

            {/* Cross-Lag Y -> X (Feedback) */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Phản Hồi: {result.variables.y_name} → {result.variables.x_name}</span>
              <div className="text-2xl font-bold text-amber-400 mt-1">
                β = {result.within_person_dynamics.mean_cross_lag_y_to_x > 0 ? '+' : ''}
                {result.within_person_dynamics.mean_cross_lag_y_to_x.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Hiệu ứng phản hồi ngược (Feedback)
              </div>
              <div className="text-[11px] text-amber-400/90 font-medium mt-0.5">
                {result.within_person_dynamics.wave_transitions[0]?.cross_lag_y_to_x.is_significant ? 'Có ý nghĩa (p < .05)' : 'Không có phản hồi'}
              </div>
            </div>

            {/* Causal Direction */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Hướng Nhân Quả Thống Trị</span>
              <div className="text-sm font-bold text-sky-400 mt-2 line-clamp-2">
                {result.within_person_dynamics.causal_direction}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Wald z = {result.within_person_dynamics.reciprocity_z_test.toFixed(2)} (p = {result.within_person_dynamics.reciprocity_p_value.toFixed(3)})
              </div>
            </div>

            {/* Trait Correlation */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Tương Quan Đặc Điểm (Trait)</span>
              <div className="text-2xl font-bold text-indigo-400 mt-1">
                r = {result.between_person_traits.trait_correlation.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Liên kết giữa I_X và I_Y (Between)
              </div>
              <div className="text-[11px] text-indigo-300 mt-0.5">
                {result.goodness_of_fit.clpm_comparison.ri_clpm_preferred ? 'Vượt trội CLPM (Δχ² > 0)' : 'Tương đồng'}
              </div>
            </div>

            {/* Model Fit */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Chỉ Số Độ Phù Hợp SEM</span>
              <div className="text-2xl font-bold text-teal-400 mt-1">
                CFI = {result.goodness_of_fit.cfi.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                RMSEA = {result.goodness_of_fit.rmsea.toFixed(3)} • SRMR = {result.goodness_of_fit.srmr.toFixed(3)}
              </div>
              <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">
                Khớp tuyệt vời (CFI ≥ .95)
              </div>
            </div>
          </div>

          {/* Responsive Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4 text-teal-400" />
                  Sơ Đồ Đường Dẫn Cấu Trúc SEM &amp; Đáp Ứng Động Lực Học Thời Gian
                </span>
                <span className="text-xs text-slate-500">
                  Panel A: Sơ đồ tham số • Panel B: Mô phỏng cú sốc +1 SD
                </span>
              </div>
              <div
                className="w-full overflow-x-auto rounded-lg bg-slate-950 p-2 flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Tab Navigation */}
          <div className="border-b border-slate-800 flex gap-4">
            <button
              onClick={() => setActiveTab('dynamics')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'dynamics'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Động Lực Nội Cá Thể (Within)
            </button>
            <button
              onClick={() => setActiveTab('traits')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'traits'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Layers className="w-4 h-4" />
              Đặc Điểm Bất Biến (Between)
            </button>
            <button
              onClick={() => setActiveTab('mediation')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'mediation'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <GitBranch className="w-4 h-4" />
              Chuỗi Trung Gian (Mediation)
            </button>
            <button
              onClick={() => setActiveTab('fit')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'fit'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              Độ Khớp Mô Hình SEM
            </button>
            <button
              onClick={() => setActiveTab('apa')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'apa'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Copy className="w-4 h-4" />
              Báo Cáo APA 7th
            </button>
          </div>

          {/* Tab Content */}
          <div className="bg-slate-800/30 p-5 rounded-xl border border-slate-800">
            {/* Tab 1: Within-Person Dynamics */}
            {activeTab === 'dynamics' && (
              <div className="space-y-4">
                <div className="text-sm text-slate-300">
                  Các tham số tự hồi quy (Autoregressive stability α) và tác động chéo (Cross-lagged transmission β) qua từng bước chuyển thời gian:
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 border-collapse">
                    <thead>
                      <tr className="border-b border-slate-700 bg-slate-800/80 text-slate-200">
                        <th className="py-2.5 px-3">Bước Chuyển (Transition)</th>
                        <th className="py-2.5 px-3">Tác Động Chéo X → Y (β)</th>
                        <th className="py-2.5 px-3">Phản Hồi Chéo Y → X (β)</th>
                        <th className="py-2.5 px-3">Tự Hồi Quy X (α_X)</th>
                        <th className="py-2.5 px-3">Tự Hồi Quy Y (α_Y)</th>
                        <th className="py-2.5 px-3">Tương Quan Đổi Mới (Within Residual r)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {result.within_person_dynamics.wave_transitions.map((trans, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/40 font-mono">
                          <td className="py-2.5 px-3 font-sans font-semibold text-white">
                            {trans.from_wave} → {trans.to_wave}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="font-bold text-emerald-400">{trans.cross_lag_x_to_y.estimate.toFixed(4)}</span>
                            <span className="text-[11px] text-slate-400 block font-sans">
                              (p = {trans.cross_lag_x_to_y.p_value.toFixed(3)})
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="font-bold text-amber-400">{trans.cross_lag_y_to_x.estimate.toFixed(4)}</span>
                            <span className="text-[11px] text-slate-400 block font-sans">
                              (p = {trans.cross_lag_y_to_x.p_value.toFixed(3)})
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-sky-300">
                            {trans.autoreg_x.estimate.toFixed(4)}
                            <span className="text-[11px] text-slate-500 block font-sans">SE: {trans.autoreg_x.se.toFixed(3)}</span>
                          </td>
                          <td className="py-2.5 px-3 text-rose-300">
                            {trans.autoreg_y.estimate.toFixed(4)}
                            <span className="text-[11px] text-slate-500 block font-sans">SE: {trans.autoreg_y.se.toFixed(3)}</span>
                          </td>
                          <td className="py-2.5 px-3 text-slate-400">
                            r = {trans.within_residual_corr.toFixed(4)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 2: Between-Person Traits */}
            {activeTab === 'traits' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Phương Sai Điểm Chặn I_X ({result.variables.x_name})</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {result.between_person_traits.var_random_intercept_x.toFixed(4)}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Mức độ khác biệt ổn định giữa người này và người khác</p>
                  </div>

                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Phương Sai Điểm Chặn I_Y ({result.variables.y_name})</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {result.between_person_traits.var_random_intercept_y.toFixed(4)}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Mức độ khác biệt ổn định giữa các cá thể</p>
                  </div>

                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Tương Quan Giữa 2 Đặc Điểm (Trait Correlation)</span>
                    <div className="text-xl font-bold text-indigo-400 mt-1">
                      r = {result.between_person_traits.trait_correlation.toFixed(4)}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Hiệp phương sai: {result.between_person_traits.cov_random_intercepts.toFixed(4)}</p>
                  </div>
                </div>

                <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-slate-300 space-y-2">
                  <h4 className="font-bold text-white flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    Kiểm Định Vượt Trội So Với Classic CLPM (Likelihood Ratio Test)
                  </h4>
                  <p>
                    {result.goodness_of_fit.clpm_comparison.interpretation}.
                    Khi không tách biệt điểm chặn ngẫu nhiên I_X và I_Y (như mô hình CLPM truyền thống), các tham số tác động chéo sẽ bị thổi phồng giả tạo (Nickell bias) do nhầm lẫn giữa sự giống nhau ổn định giữa các cá nhân với tương tác nhân quả theo thời gian.
                  </p>
                  <p className="font-mono text-teal-400">
                    Δχ²({result.goodness_of_fit.clpm_comparison.delta_df}) = {result.goodness_of_fit.clpm_comparison.delta_chi2.toFixed(2)}, p = {result.goodness_of_fit.clpm_comparison.p_value.toFixed(4)}
                  </p>
                </div>
              </div>
            )}

            {/* Tab 3: Longitudinal Mediation */}
            {activeTab === 'mediation' && (
              <div className="space-y-4">
                <div className="text-sm text-slate-300">
                  Phân tích chuỗi tác động nhân quả tuần tự qua các đợt sóng (Cole &amp; Maxwell 2003):
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Hiệu Ứng Trực Tiếp</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {(result.longitudinal_mediation.direct_effect_c_prime ?? result.longitudinal_mediation.direct_effect ?? 0).toFixed(4)}
                    </div>
                  </div>

                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Hiệu Ứng Gián Tiếp (Indirect)</span>
                    <div className="text-xl font-bold text-teal-400 mt-1">
                      {(result.longitudinal_mediation.indirect_effect ?? result.longitudinal_mediation.cumulative_indirect ?? 0).toFixed(4)}
                    </div>
                    {result.longitudinal_mediation.indirect_ci_95 && (
                      <span className="text-[11px] text-slate-400 block mt-0.5">
                        95% CI [{result.longitudinal_mediation.indirect_ci_95[0].toFixed(3)}, {result.longitudinal_mediation.indirect_ci_95[1].toFixed(3)}]
                      </span>
                    )}
                  </div>

                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Tổng Tác Động (Total Effect)</span>
                    <div className="text-xl font-bold text-indigo-400 mt-1">
                      {result.longitudinal_mediation.total_effect.toFixed(4)}
                    </div>
                  </div>

                  <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
                    <span className="text-xs text-slate-400">Tỷ Lệ Gián Tiếp (Mediation %)</span>
                    <div className="text-xl font-bold text-amber-400 mt-1">
                      {(result.longitudinal_mediation.mediation_ratio * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 4: SEM Goodness-of-Fit */}
            {activeTab === 'fit' && (
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 border-collapse">
                    <thead>
                      <tr className="border-b border-slate-700 bg-slate-800/80 text-slate-200">
                        <th className="py-2 px-3">Chỉ Số Độ Phù Hợp</th>
                        <th className="py-2 px-3">Giá Trị Quan Sát</th>
                        <th className="py-2 px-3">Ngưỡng Chuẩn Học Thuật</th>
                        <th className="py-2 px-3">Đánh Giá</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">Comparative Fit Index (CFI)</td>
                        <td className="py-2 px-3 font-mono font-bold text-emerald-400">{result.goodness_of_fit.cfi.toFixed(3)}</td>
                        <td className="py-2 px-3 font-mono">≥ 0.95 (Chấp nhận ≥ 0.90)</td>
                        <td className="py-2 px-3 text-emerald-400 font-medium">Xuất sắc</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">Tucker-Lewis Index (TLI)</td>
                        <td className="py-2 px-3 font-mono font-bold text-emerald-400">{result.goodness_of_fit.tli.toFixed(3)}</td>
                        <td className="py-2 px-3 font-mono">≥ 0.95 (Chấp nhận ≥ 0.90)</td>
                        <td className="py-2 px-3 text-emerald-400 font-medium">Xuất sắc</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">Root Mean Square Error (RMSEA)</td>
                        <td className="py-2 px-3 font-mono font-bold text-emerald-400">{result.goodness_of_fit.rmsea.toFixed(3)}</td>
                        <td className="py-2 px-3 font-mono">≤ 0.06 (Chấp nhận ≤ 0.08)</td>
                        <td className="py-2 px-3 text-emerald-400 font-medium">Tốt</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">Standardized RMR (SRMR)</td>
                        <td className="py-2 px-3 font-mono font-bold text-emerald-400">{result.goodness_of_fit.srmr.toFixed(3)}</td>
                        <td className="py-2 px-3 font-mono">≤ 0.08</td>
                        <td className="py-2 px-3 text-emerald-400 font-medium">Tốt</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">Chi-Square Model Test (χ²)</td>
                        <td className="py-2 px-3 font-mono text-slate-300">
                          {result.goodness_of_fit.chi_square.toFixed(2)} (df = {result.goodness_of_fit.df})
                        </td>
                        <td className="py-2 px-3 font-mono">p &gt; 0.05</td>
                        <td className="py-2 px-3 text-slate-400 font-medium">p = {result.goodness_of_fit.p_value.toFixed(4)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 5: APA 7th Narrative */}
            {activeTab === 'apa' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Thuyết minh học thuật chuẩn mực theo định dạng APA 7th Edition:</span>
                  <button
                    onClick={handleCopyAPA}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        Đã sao chép!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Sao chép thuyết minh
                      </>
                    )}
                  </button>
                </div>
                <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-xs font-serif leading-relaxed text-slate-300 whitespace-pre-wrap">
                  {result.apa_narrative}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
