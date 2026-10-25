import React, { useState } from 'react';
import {
  Network,
  GitFork,
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sliders,
  Copy,
  Check
} from 'lucide-react';
import { api } from '../api/client';
import { CausalDiscoveryResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const CausalDiscoveryCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [selectedVarQids, setSelectedVarQids] = useState<string[]>([]);
  const [pruneThreshold, setPruneThreshold] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<CausalDiscoveryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'edges' | 'anm' | 'nongaussian'>('edges');

  // Filter numeric, rating, scale, or slider questions
  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'single_choice'].includes(q.question_type)
  );

  const toggleVariable = (qid: string) => {
    setSelectedVarQids((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (selectedVarQids.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 biến khảo sát để khám phá đồ thị nhân quả.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.runCausalDiscovery(surveyId, {
        variable_question_ids: selectedVarQids,
        prune_threshold: pruneThreshold,
        scope
      });
      if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Mẫu khảo sát không đủ điều kiện để khám phá cấu trúc nhân quả.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích khám phá cấu trúc nhân quả DAG.');
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
      <div className="absolute -top-24 -right-24 w-80 h-80 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 rounded-xl text-cyan-400">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Khám Phá Cấu Trúc Đồ Thị Nhân Quả DAG (LiNGAM &amp; ANM)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-medium">
                  Shimizu (2006) &amp; Hoyer (2009)
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Xác định hướng nhân quả không phụ thuộc vào giả định Gaussian thông qua FastICA &amp; Mô hình Nhiễu Cộng tính
              </p>
            </div>
          </div>
        </div>

        {/* Scope Pill */}
        <div className="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 self-start md:self-auto">
          <button
            onClick={() => setScope('all')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              scope === 'all'
                ? 'bg-cyan-600 text-white shadow'
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
        <div>
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Chọn các biến khảo sát tham gia đồ thị nhân quả ({selectedVarQids.length} đã chọn):</span>
            <span className="text-[11px] text-slate-500 lowercase">tối thiểu 2 biến liên tục / thang đo</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-44 overflow-y-auto pr-1">
            {eligibleQuestions.map((q) => {
              const isSelected = selectedVarQids.includes(q.id);
              return (
                <button
                  key={q.id}
                  onClick={() => toggleVariable(q.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border text-left flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-sm'
                      : 'bg-slate-800/50 text-slate-400 border-slate-700/50 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-cyan-400' : 'bg-slate-600'}`} />
                  <span className="truncate max-w-[240px]">{q.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Slider & Action */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-3 border-t border-slate-800/60">
          <div className="flex items-center gap-3">
            <Sliders className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-300 font-medium">Ngưỡng tỉa cạnh (Prune Threshold):</span>
            <input
              type="range"
              min="0.01"
              max="0.25"
              step="0.01"
              value={pruneThreshold}
              onChange={(e) => setPruneThreshold(parseFloat(e.target.value))}
              className="w-28 accent-cyan-500 cursor-pointer"
            />
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
              {pruneThreshold.toFixed(2)}
            </span>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading || selectedVarQids.length < 2}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-xs shadow-lg shadow-cyan-900/30 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Đang khám phá DAG &amp; FastICA...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Khám Phá Cấu Trúc Nhân Quả</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="mt-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="mt-6 space-y-6">
          {/* Causal Order Banner */}
          {result.causal_order && result.causal_order.length > 0 && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/40 via-blue-950/40 to-slate-900 border border-cyan-800/40">
              <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <GitFork className="w-4 h-4" />
                <span>Thứ Tự Topo Nhân Quả Được Xác Định (Topological Causal Ordering):</span>
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-1">
                {result.causal_order.map((varName, idx) => (
                  <React.Fragment key={idx}>
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/90 border border-cyan-500/30 text-slate-200 text-xs font-semibold shadow-sm">
                      <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-[10px] font-bold">
                        {idx + 1}
                      </span>
                      <span>{varName}</span>
                    </div>
                    {idx < (result.causal_order?.length || 0) - 1 && (
                      <ArrowRight className="w-3.5 h-3.5 text-cyan-500 flex-shrink-0" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* Diagnostics Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Kích Thước Mẫu N</span>
              <span className="text-xl font-bold text-white mt-1 block">{result.diagnostics?.N}</span>
              <span className="text-[10px] text-slate-500 mt-1 block">Quan sát hoàn chỉnh</span>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Số Biến Tham Gia p</span>
              <span className="text-xl font-bold text-cyan-400 mt-1 block">{result.diagnostics?.p}</span>
              <span className="text-[10px] text-slate-500 mt-1 block">Khung đồ thị DAG</span>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Đường Dẫn Nhân Quả</span>
              <span className="text-xl font-bold text-emerald-400 mt-1 block">
                {result.diagnostics?.total_directed_edges}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">Cạnh có hướng đã tỉa</span>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Biến Phi Gauss</span>
              <span className="text-xl font-bold text-blue-400 mt-1 block">
                {result.diagnostics?.non_gaussian_variables_count} / {result.diagnostics?.p}
              </span>
              <span className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Đạt định danh Shimizu
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
                onClick={() => setActiveTab('edges')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'edges'
                    ? 'border-cyan-400 text-cyan-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Đường Dẫn Nhân Quả Có Hướng ({result.directed_edges?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('anm')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'anm'
                    ? 'border-cyan-400 text-cyan-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Kiểm Định Nhiễu Độc Lập ANM
              </button>
              <button
                onClick={() => setActiveTab('nongaussian')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'nongaussian'
                    ? 'border-cyan-400 text-cyan-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Kiểm Tra Điều Kiện Phi Gauss
              </button>
            </div>

            <div className="p-4 overflow-x-auto">
              {activeTab === 'edges' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Căn Nguyên (Nguyên Nhân)</th>
                      <th className="py-2.5 px-3">Kết Cục (Hệ Quả)</th>
                      <th className="py-2.5 px-3 text-right">Hệ Số Trực Tiếp (β)</th>
                      <th className="py-2.5 px-3 text-right">Tổng Hiệu Ứng</th>
                      <th className="py-2.5 px-3 text-right">t-statistic</th>
                      <th className="py-2.5 px-3 text-right">p-value</th>
                      <th className="py-2.5 px-3 text-center">Ý Nghĩa (α = .05)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.directed_edges?.map((edge, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-cyan-300">{edge.from}</td>
                        <td className="py-2.5 px-3 font-medium text-blue-300">{edge.to}</td>
                        <td className={`py-2.5 px-3 text-right font-mono font-bold ${edge.path_coefficient >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {edge.path_coefficient >= 0 ? `+${edge.path_coefficient.toFixed(3)}` : edge.path_coefficient.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-200">
                          {edge.total_effect >= 0 ? `+${edge.total_effect.toFixed(3)}` : edge.total_effect.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{edge.t_statistic.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{edge.p_value < 0.001 ? '< .001' : edge.p_value.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-center">
                          {edge.is_significant ? (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30">
                              Có ý nghĩa
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full bg-slate-700/40 text-slate-400 text-[10px] font-medium">
                              Không ý nghĩa
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'anm' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Cạnh Nhân Quả</th>
                      <th className="py-2.5 px-3 text-right">Tương Quan Dư - Nguyên Nhân (ρ)</th>
                      <th className="py-2.5 px-3 text-right">p-value Độc Lập</th>
                      <th className="py-2.5 px-3 text-center">Xác Nhận Chiều Nhân Quả ANM</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.anm_diagnostics?.map((anm, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-cyan-300">{anm.edge}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">{anm.residual_cause_corr.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{anm.independence_p_value.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-center">
                          {anm.anm_noise_independent ? (
                            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30 inline-flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Độc lập (Không đảo chiều)
                            </span>
                          ) : (
                            <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[10px] font-medium border border-amber-500/30">
                              Dư lượng tương quan
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'nongaussian' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Biến Khảo Sát</th>
                      <th className="py-2.5 px-3 text-right">Độ Lệch (Skewness)</th>
                      <th className="py-2.5 px-3 text-right">Độ Nhọn Vượt (Kurtosis)</th>
                      <th className="py-2.5 px-3 text-right">Thống Kê K² Omnibus</th>
                      <th className="py-2.5 px-3 text-right">p-value Phân Phối Chuẩn</th>
                      <th className="py-2.5 px-3 text-center">Điều Kiện Định Danh LiNGAM</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.non_gaussianity_tests?.map((t, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{t.variable}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">{t.skewness.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">{t.excess_kurtosis.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{t.omnibus_stat.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{t.p_value.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-center">
                          {t.is_non_gaussian ? (
                            <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 text-[10px] font-semibold border border-cyan-500/30 inline-flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Phi Gauss (Đạt Định Danh)
                            </span>
                          ) : (
                            <span className="px-2.5 py-0.5 rounded-full bg-slate-700/40 text-slate-400 text-[10px] font-medium">
                              Gần chuẩn (Gaussian)
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
                  <Info className="w-4 h-4 text-cyan-400" />
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
