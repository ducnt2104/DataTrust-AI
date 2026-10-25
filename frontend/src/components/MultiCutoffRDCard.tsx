import React, { useState } from 'react';
import {
  MultiCutoffRDResult,
  MultiCutoffRDRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  GitFork,
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
  Split,
  MapPin,
  Sparkles
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

export const MultiCutoffRDCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [runningQId, setRunningQId] = useState<string>('');
  const [groupQId, setGroupQId] = useState<string>('');
  const [cutoffQId, setCutoffQId] = useState<string>('');
  const [bandwidthVal, setBandwidthVal] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MultiCutoffRDResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !runningQId) {
      setError('Vui lòng chọn biến kết quả Y và biến chỉ số gán ngưỡng (Running variable X).');
      return;
    }

    if (outcomeQId === runningQId) {
      setError('Biến kết quả Y và biến gán ngưỡng X không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: MultiCutoffRDRequest = {
      outcome_question_id: outcomeQId,
      running_question_id: runningQId,
      cutoff_question_id: cutoffQId || undefined,
      group_question_id: groupQId || undefined,
      bandwidth: bandwidthVal ? parseFloat(bandwidthVal) : undefined,
      alpha_level: 0.05,
      scope
    };

    try {
      const res = await api.runMultiCutoffRD(surveyId, payload);
      if (res.status === 'ERROR') {
        setError(res.message || 'Lỗi khi thực hiện Multi-Cutoff RD.');
        setResult(null);
      } else if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Cỡ mẫu chưa đủ để thực hiện Multi-Cutoff RD.');
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
    setOutcomeQId('');
    setRunningQId('');
    setGroupQId('');
    setCutoffQId('');
    setBandwidthVal('');
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
            <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400">
              <GitFork className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                Multi-Cutoff Regression Discontinuity &amp; Boundary Treatment Effects
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-950/80 text-rose-400 border border-rose-800/60">
                  Cattaneo et al. (2015) · Bertanha (2020) JASA
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Thiết kế Hồi quy Gián đoạn đa ngưỡng (nhiều địa bàn, hạn mức hoặc thang điểm). Chuẩn hóa biến chạy (X - c<sub>g</sub>), ước lượng hiệu ứng biên gộp &tau;<sub>pooled</sub> và kiểm định tính bất biến qua các ngưỡng.
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
            disabled={loading || !outcomeQId || !runningQId}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow transition-all"
          >
            {loading ? (
              <>
                <Activity className="w-3.5 h-3.5 animate-spin" />
                Đang chuẩn hóa đa ngưỡng &amp; Ước lượng...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Ước Lượng Multi-Cutoff RD
              </>
            )}
          </button>
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Outcome Y */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-rose-400" />
            1. Biến Kết Quả Y (Outcome)
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-rose-500"
          >
            <option value="">-- Chọn câu hỏi đo lường Y --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Biến phụ thuộc liên tục cần đánh giá bước nhảy.</span>
        </div>

        {/* Running Variable X */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-sky-400" />
            2. Biến Gán Ngưỡng X (Running Score)
          </label>
          <select
            value={runningQId}
            onChange={(e) => setRunningQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-rose-500"
          >
            <option value="">-- Chọn biến chỉ số X --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Biến quyết định điều kiện hưởng chính sách.</span>
        </div>

        {/* Group / Region Column */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-amber-400" />
            3. Phân Nhóm Địa Bàn / Chính Sách
          </label>
          <select
            value={groupQId}
            onChange={(e) => setGroupQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-rose-500"
          >
            <option value="">-- Tự động theo phân vị (Default) --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-500 mt-1 block">Nhóm phân loại ngưỡng (Vùng, Tỉnh, Ngành).</span>
        </div>

        {/* Bandwidth & Scope */}
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-purple-400" />
            4. Băng Thông h &amp; Phạm Vi
          </label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              step="0.5"
              placeholder="Tự động (CCT)"
              value={bandwidthVal}
              onChange={(e) => setBandwidthVal(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 text-right"
            />
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
            >
              <option value="all">Tất cả mẫu</option>
              <option value="verified_clean">Chỉ mẫu sạch</option>
            </select>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">Bán kính cục bộ hạt nhân tam giác quanh ngưỡng.</span>
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
            {/* Pooled Boundary Effect */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-rose-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-rose-400 block mb-1">
                Hiệu Ứng Biên Gộp &tau;<sub>pooled</sub>
              </span>
              <div className="text-2xl font-black text-slate-100">
                {summ.tau_pooled > 0 ? `+${summ.tau_pooled}` : summ.tau_pooled}
              </div>
              <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <span>SE: {summ.se_pooled}</span>
                <span>·</span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                  summ.p_value_pooled < 0.05 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-slate-800 text-slate-400'
                }`}>
                  p = {summ.p_value_pooled}
                </span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-2">
                95% CI: [{summ.ci_95_pooled[0]}, {summ.ci_95_pooled[1]}]
              </div>
            </div>

            {/* Cutoff Invariance Test */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-purple-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-purple-400 block mb-1">
                Kiểm Định Bất Biến Ngưỡng
              </span>
              <div className="text-sm font-bold text-slate-100 mt-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-purple-400" />
                <span className="truncate">{summ.heterogeneity_verdict}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Wald Stat: {summ.wald_test_heterogeneity} · p = {summ.p_value_heterogeneity}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                {summ.is_cutoff_heterogeneous ? 'Hiệu ứng phụ thuộc vào ngưỡng' : 'Đồng nhất qua các ngưỡng'}
              </div>
            </div>

            {/* McCrary Manipulation Test */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-emerald-500/30 relative overflow-hidden shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 block mb-1">
                Kiểm Định Thao Túng McCrary
              </span>
              <div className="text-sm font-bold text-slate-100 mt-1 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="truncate">{summ.manipulation_verdict}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                z = {summ.mccrary_z_statistic} · p = {summ.mccrary_p_value}
              </div>
              <div className="text-[11px] text-emerald-400/80 mt-2">
                {summ.is_manipulation_suspected ? 'Cảnh báo dịch chuyển mật độ' : 'Quần thể phân bổ ngẫu nhiên hợp lệ'}
              </div>
            </div>

            {/* Fronts & Effective N */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Quy Mô Biên &amp; Mẫu Hiệu Quả
              </span>
              <div className="text-xl font-bold text-slate-200">
                G = {summ.n_distinct_cutoffs} Ngưỡng Phân Khác
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Mẫu hiệu dụng trong băng thông: N<sub>eff</sub> = {summ.effective_n_pooled}
              </div>
              <div className="text-[11px] text-slate-500 mt-2">
                Băng thông tối ưu: h = {summ.bandwidth_h}
              </div>
            </div>
          </div>

          {/* Cutoff Specific Estimates Table */}
          {result.cutoff_summaries && result.cutoff_summaries.length > 0 && (
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Scale className="w-4 h-4 text-rose-400" />
                  <span className="text-xs font-bold text-slate-200">
                    Bảng Ước Lượng Hiệu Ứng Theo Từng Ngưỡng Chính Sách &tau;(c<sub>g</sub>)
                  </span>
                </div>
                <span className="text-[11px] text-slate-500">Hồi quy tuyến tính cục bộ hạt nhân tam giác</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-4">Ngưỡng chính sách (c)</th>
                      <th className="py-2.5 px-4">Cỡ mẫu cụm</th>
                      <th className="py-2.5 px-4">Mẫu hiệu quả (N_eff)</th>
                      <th className="py-2.5 px-4">Ước lượng &tau;(c)</th>
                      <th className="py-2.5 px-4">Sai số chuẩn (SE)</th>
                      <th className="py-2.5 px-4">t-statistic</th>
                      <th className="py-2.5 px-4">p-value</th>
                      <th className="py-2.5 px-4">Khoảng tin cậy 95%</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {result.cutoff_summaries.map(c => (
                      <tr key={c.cutoff_value} className="hover:bg-slate-800/40">
                        <td className="py-2 px-4 font-bold text-rose-300 font-sans">
                          Ngưỡng c = {c.cutoff_value}
                        </td>
                        <td className="py-2 px-4 text-slate-400">{c.sample_size}</td>
                        <td className="py-2 px-4 text-slate-400">{c.effective_n}</td>
                        <td className="py-2 px-4 font-bold text-slate-100">
                          {c.tau_estimate > 0 ? `+${c.tau_estimate}` : c.tau_estimate}
                        </td>
                        <td className="py-2 px-4 text-slate-400">{c.se}</td>
                        <td className="py-2 px-4 text-slate-400">{c.t_statistic}</td>
                        <td className="py-2 px-4">
                          <span className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                            c.p_value < 0.05 ? 'bg-emerald-950 text-emerald-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {c.p_value}
                          </span>
                        </td>
                        <td className="py-2 px-4 text-slate-400">[{c.ci_95[0]}, {c.ci_95[1]}]</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Scientific Dual-Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-hidden shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-rose-400" />
                  <span className="text-xs font-semibold text-slate-200">
                    Trực Quan Hóa Khoa Học: Điểm Binned Scatter Gián Đoạn Chuẩn Hóa &amp; Biểu Đồ Rừng So Sánh Ngưỡng
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
