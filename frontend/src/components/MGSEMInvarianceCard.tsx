import React, { useState } from 'react';
import {
  GitCompare,
  Layers,
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  TrendingUp,
  ShieldCheck,
  Scale
} from 'lucide-react';
import { api } from '../api/client';
import { MGSEMInvarianceResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const MGSEMInvarianceCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [groupQid, setGroupQid] = useState<string>('');
  const [selectedIndQids, setSelectedIndQids] = useState<string[]>([]);
  const [refGroup, setRefGroup] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MGSEMInvarianceResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'hierarchy' | 'latent' | 'indicators'>('hierarchy');

  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'single_choice'].includes(q.question_type)
  );

  const toggleIndicator = (qid: string) => {
    setSelectedIndQids((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!groupQid) {
      setError('Vui lòng chọn biến Phân Nhóm (Grouping Variable, ví dụ: Vùng miền, Giới tính, Ngành nghề).');
      return;
    }
    if (selectedIndQids.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 biến chỉ báo đo lường (Indicators).');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.runMGSEMInvariance(surveyId, {
        group_question_id: groupQid,
        indicator_question_ids: selectedIndQids,
        reference_group: refGroup.trim() || undefined,
        scope
      });
      if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Mẫu khảo sát không đủ điều kiện để kiểm định bất biến đa nhóm MG-SEM.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi kiểm định bất biến đa nhóm MG-SEM.');
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
      <div className="absolute -top-24 -right-24 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 border border-blue-500/30 rounded-xl text-blue-400">
              <GitCompare className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Bất Biến Đo Lường Đa Nhóm &amp; Khác Biệt Điểm Tiềm Ẩn (MG-SEM)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30 font-medium">
                  Meredith (1993) &amp; Byrne (2013)
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Kiểm định bất biến 4 cấp độ (Configural, Metric, Scalar, Strict) &amp; So sánh điểm số biến tiềm ẩn không thiên lệch
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
                ? 'bg-blue-600 text-white shadow'
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
          {/* Group Question */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 block">
              Biến Phân Nhóm Khảo Sát (Grouping Variable):
            </label>
            <select
              value={groupQid}
              onChange={(e) => setGroupQid(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-blue-500"
            >
              <option value="">-- Chọn câu hỏi phân nhóm (Vùng, Giới, v.v.) --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Reference Group Input (Optional) */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Nhóm Cơ Sở / Đối Sánh (Reference Group - α = 0):</span>
              <span className="text-[11px] text-slate-500 lowercase">mặc định tự chọn nhóm 1</span>
            </label>
            <input
              type="text"
              placeholder="Nhập tên nhóm mốc (để trống: tự động)"
              value={refGroup}
              onChange={(e) => setRefGroup(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Indicators Multi-select */}
        <div>
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Chọn các biến chỉ báo đo lường khái niệm tiềm ẩn ({selectedIndQids.length} đã chọn):</span>
            <span className="text-[11px] text-slate-500 lowercase">tối thiểu 2 câu hỏi thang đo CFA</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto pr-1">
            {eligibleQuestions
              .filter((q) => q.id !== groupQid)
              .map((q) => {
                const isSelected = selectedIndQids.includes(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => toggleIndicator(q.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border text-left flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-blue-500/20 text-blue-300 border-blue-500/50 shadow-sm'
                        : 'bg-slate-800/50 text-slate-400 border-slate-700/50 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-blue-400' : 'bg-slate-600'}`} />
                    <span className="truncate max-w-[240px]">{q.title}</span>
                  </button>
                );
              })}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-3 border-t border-slate-800/60">
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !groupQid || selectedIndQids.length < 2}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-xs shadow-lg shadow-blue-900/30 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Đang kiểm định MG-SEM...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Kiểm Định Bất Biến Đa Nhóm</span>
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
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Mức Độ Bất Biến</span>
              <span className="text-xl font-bold mt-1 block">
                {result.diagnostics?.scalar_supported ? (
                  <span className="text-emerald-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-5 h-5" /> Scalar Invariant
                  </span>
                ) : (result.diagnostics?.metric_supported ? (
                  <span className="text-amber-400 flex items-center gap-1.5">
                    <Scale className="w-5 h-5" /> Metric Invariant
                  </span>
                ) : (
                  <span className="text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-5 h-5" /> Configural Only
                  </span>
                ))}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {result.diagnostics?.scalar_supported
                  ? 'Đạt chuẩn so sánh điểm số tiềm ẩn'
                  : 'Cảnh báo sai lệch điểm chặn indicator'}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Chênh Lệch Điểm Tiềm Ẩn (Δα)</span>
              <span className="text-xl font-bold text-blue-400 mt-1 block">
                {result.latent_means_comparison?.latent_mean_comp !== undefined
                  ? (result.latent_means_comparison.latent_mean_comp >= 0
                    ? `+${result.latent_means_comparison.latent_mean_comp.toFixed(3)}`
                    : result.latent_means_comparison.latent_mean_comp.toFixed(3))
                  : 'N/A'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {result.latent_means_comparison?.comparison_group} vs {result.latent_means_comparison?.reference_group} (α=0)
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Độ Lớn Hiệu Ứng Cohen's d</span>
              <span className="text-xl font-bold text-pink-400 mt-1 block">
                {result.latent_means_comparison?.cohens_d !== undefined
                  ? (result.latent_means_comparison.cohens_d >= 0
                    ? `+${result.latent_means_comparison.cohens_d.toFixed(2)}`
                    : result.latent_means_comparison.cohens_d.toFixed(2))
                  : 'N/A'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {result.latent_means_comparison && Math.abs(result.latent_means_comparison.cohens_d) >= 0.8
                  ? 'Hiệu ứng lớn (|d| ≥ 0.8)'
                  : (result.latent_means_comparison && Math.abs(result.latent_means_comparison.cohens_d) >= 0.5 ? 'Hiệu ứng vừa (|d| ≥ 0.5)' : 'Hiệu ứng nhỏ')}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Kích Thước Mẫu Hai Nhóm</span>
              <span className="text-sm font-bold text-slate-200 mt-1 block">
                N₁ = {result.diagnostics?.N1} | N₂ = {result.diagnostics?.N2}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Tổng N = {result.diagnostics?.N_total} quan sát hoàn chỉnh
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
                onClick={() => setActiveTab('hierarchy')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'hierarchy'
                    ? 'border-blue-400 text-blue-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Cấp Bậc Bất Biến Đo Lường (Hierarchy Steps)
              </button>
              <button
                onClick={() => setActiveTab('latent')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'latent'
                    ? 'border-blue-400 text-blue-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                So Sánh Điểm Tiềm Ẩn (Latent Means)
              </button>
              <button
                onClick={() => setActiveTab('indicators')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'indicators'
                    ? 'border-blue-400 text-blue-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Hệ Số Từng Biến Chỉ Báo ({result.indicator_parameters?.length || 0})
              </button>
            </div>

            <div className="p-4 overflow-x-auto">
              {activeTab === 'hierarchy' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Mô Hình Cấp Bậc</th>
                      <th className="py-2.5 px-3 text-right">χ²</th>
                      <th className="py-2.5 px-3 text-right">df</th>
                      <th className="py-2.5 px-3 text-right">CFI</th>
                      <th className="py-2.5 px-3 text-right">RMSEA</th>
                      <th className="py-2.5 px-3 text-right">Δχ² (df)</th>
                      <th className="py-2.5 px-3 text-right">ΔCFI</th>
                      <th className="py-2.5 px-3 text-center">Đánh Giá (Cheung &amp; Rensvold)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.invariance_hierarchy?.map((step, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-semibold text-slate-200">{step.model}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">{step.chi2.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{step.df}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-cyan-400">{step.cfi.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">{step.rmsea.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                          {idx === 0 ? '-' : `${step.delta_chi2.toFixed(2)} (${step.delta_df})`}
                        </td>
                        <td className={`py-2.5 px-3 text-right font-mono font-bold ${Math.abs(step.delta_cfi) <= 0.010 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {idx === 0 ? '-' : (step.delta_cfi >= 0 ? `+${step.delta_cfi.toFixed(3)}` : step.delta_cfi.toFixed(3))}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                            step.status.includes('Supported')
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          }`}>
                            {step.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'latent' && result.latent_means_comparison && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div>
                        <span className="text-slate-500 block">Nhóm Mốc Đối Sánh (α = 0):</span>
                        <span className="text-slate-200 font-bold mt-0.5 block">{result.latent_means_comparison.reference_group}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Nhóm So Sánh:</span>
                        <span className="text-pink-400 font-bold mt-0.5 block">{result.latent_means_comparison.comparison_group}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Chênh Lệch Tiềm Ẩn (Δα):</span>
                        <span className="text-blue-400 font-mono font-bold mt-0.5 block">
                          {result.latent_means_comparison.latent_mean_comp >= 0
                            ? `+${result.latent_means_comparison.latent_mean_comp.toFixed(3)}`
                            : result.latent_means_comparison.latent_mean_comp.toFixed(3)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Kiểm Định Ý Nghĩa z (p-value):</span>
                        <span className="text-slate-200 font-mono font-bold mt-0.5 block">
                          z = {result.latent_means_comparison.z_stat.toFixed(2)} (p = {result.latent_means_comparison.p_value.toFixed(4)})
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                    <Info className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    <span className="text-slate-300">
                      Khoảng tin cậy 95% CI của chênh lệch biến tiềm ẩn: <strong className="text-white">[{result.latent_means_comparison.ci_95_lower.toFixed(3)}, {result.latent_means_comparison.ci_95_upper.toFixed(3)}]</strong>. Cohen's d = <strong className="text-pink-400">{result.latent_means_comparison.cohens_d.toFixed(2)}</strong>.
                    </span>
                  </div>
                </div>
              )}

              {activeTab === 'indicators' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Biến Chỉ Báo (Indicator)</th>
                      <th className="py-2.5 px-3 text-right">Tải Nhóm 1 (λ₁)</th>
                      <th className="py-2.5 px-3 text-right">Tải Nhóm 2 (λ₂)</th>
                      <th className="py-2.5 px-3 text-right">Chênh Lệch Tải |Δλ|</th>
                      <th className="py-2.5 px-3 text-right">Chặn Nhóm 1 (τ₁)</th>
                      <th className="py-2.5 px-3 text-right">Chặn Nhóm 2 (τ₂)</th>
                      <th className="py-2.5 px-3 text-center">Bất Biến Điểm Chặn</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.indicator_parameters?.map((ip, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{ip.indicator}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-blue-300">{ip.loading_g1.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-pink-300">{ip.loading_g2.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{ip.loading_diff.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">{ip.intercept_g1.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">{ip.intercept_g2.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-center">
                          {ip.is_scalar_invariant ? (
                            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30">
                              Đồng nhất (Scalar OK)
                            </span>
                          ) : (
                            <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[10px] font-medium border border-amber-500/30">
                              Lệch điểm chặn
                            </span>
                          )}
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
                  <Info className="w-4 h-4 text-blue-400" />
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
