import React, { useState } from 'react';
import {
  Trees,
  GitFork,
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
  Sliders,
  Copy,
  Check,
  TrendingUp,
  Layers,
  Users
} from 'lucide-react';
import { api } from '../api/client';
import { BARTCausalResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const BARTCausalCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [selectedCovQids, setSelectedCovQids] = useState<string[]>([]);
  const [nTrees, setNTrees] = useState<number>(50);
  const [nSamples, setNSamples] = useState<number>(150);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<BARTCausalResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'cate' | 'ite' | 'vip'>('cate');

  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'scale', 'slider', 'single_choice'].includes(q.question_type)
  );

  const toggleCovariate = (qid: string) => {
    setSelectedCovQids((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQid || !outcomeQid) {
      setError('Vui lòng chọn biến Can Thiệp (Treatment T) và biến Kết Quả (Outcome Y).');
      return;
    }
    if (treatmentQid === outcomeQid) {
      setError('Biến Can Thiệp và Kết Quả không thể trùng nhau.');
      return;
    }
    if (selectedCovQids.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến kiểm soát/điều tiết nền (Covariates).');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.runBARTCausal(surveyId, {
        treatment_question_id: treatmentQid,
        outcome_question_id: outcomeQid,
        covariate_question_ids: selectedCovQids,
        n_trees: nTrees,
        n_samples: nSamples,
        scope
      });
      if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Mẫu khảo sát không đủ điều kiện để ước lượng mô hình BART.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích BART Causal.');
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
      <div className="absolute -top-24 -right-24 w-80 h-80 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30 rounded-xl text-violet-400">
              <Trees className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Mô Hình Cây Hồi Quy Cộng Tính Bayes (BART Causal Inference)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/30 font-medium">
                  Chipman (2010) &amp; Hill (2011)
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Ước lượng phi tham số hiệu ứng can thiệp không đồng nhất (HTE) &amp; Phân rã CATE theo biến điều tiết
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
                ? 'bg-violet-600 text-white shadow'
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
          {/* Treatment Variable */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 block">
              Biến Can Thiệp / Thử Nghiệm (Treatment T - Nhị Phân 1/0):
            </label>
            <select
              value={treatmentQid}
              onChange={(e) => setTreatmentQid(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-violet-500"
            >
              <option value="">-- Chọn câu hỏi can thiệp --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === outcomeQid}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Outcome Variable */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 block">
              Biến Kết Quả Đích (Continuous Outcome Y):
            </label>
            <select
              value={outcomeQid}
              onChange={(e) => setOutcomeQid(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-violet-500"
            >
              <option value="">-- Chọn câu hỏi kết quả --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.id} value={q.id} disabled={q.id === treatmentQid}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Covariates / Moderators Multi-select */}
        <div>
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Chọn các biến kiểm soát &amp; điều tiết nền X ({selectedCovQids.length} đã chọn):</span>
            <span className="text-[11px] text-slate-500 lowercase">phân tích tác động không đồng nhất HTE</span>
          </label>
          <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto pr-1">
            {eligibleQuestions
              .filter((q) => q.id !== treatmentQid && q.id !== outcomeQid)
              .map((q) => {
                const isSelected = selectedCovQids.includes(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => toggleCovariate(q.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border text-left flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-violet-500/20 text-violet-300 border-violet-500/50 shadow-sm'
                        : 'bg-slate-800/50 text-slate-400 border-slate-700/50 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-violet-400' : 'bg-slate-600'}`} />
                    <span className="truncate max-w-[240px]">{q.title}</span>
                  </button>
                );
              })}
          </div>
        </div>

        {/* Hyperparameters & Action */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-3 border-t border-slate-800/60">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-slate-400" />
              <span className="text-xs text-slate-300 font-medium">Số lượng Cây (M):</span>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={nTrees}
                onChange={(e) => setNTrees(parseInt(e.target.value))}
                className="w-24 accent-violet-500 cursor-pointer"
              />
              <span className="text-xs font-mono text-violet-400 bg-violet-950/60 px-2 py-0.5 rounded border border-violet-800/50">
                {nTrees}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-300 font-medium">Mẫu MCMC Hậu Nghiệm:</span>
              <input
                type="range"
                min="50"
                max="300"
                step="25"
                value={nSamples}
                onChange={(e) => setNSamples(parseInt(e.target.value))}
                className="w-24 accent-violet-500 cursor-pointer"
              />
              <span className="text-xs font-mono text-violet-400 bg-violet-950/60 px-2 py-0.5 rounded border border-violet-800/50">
                {nSamples}
              </span>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading || !treatmentQid || !outcomeQid || selectedCovQids.length === 0}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-xs shadow-lg shadow-violet-900/30 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Đang hồi quy cây Bayes BART...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Ước Lượng Hiệu Ứng BART</span>
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
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Hiệu Ứng Trung Bình (ATE)</span>
              <span className="text-xl font-bold text-violet-400 mt-1 block">
                {result.treatment_effects?.ate?.estimate !== undefined
                  ? (result.treatment_effects.ate.estimate >= 0
                    ? `+${result.treatment_effects.ate.estimate.toFixed(3)}`
                    : result.treatment_effects.ate.estimate.toFixed(3))
                  : 'N/A'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                95% CrI [{result.treatment_effects?.ate?.ci_95_lower?.toFixed(2) ?? '-'}, {result.treatment_effects?.ate?.ci_95_upper?.toFixed(2) ?? '-'}]
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Hiệu Ứng Nhóm Nhận (ATT)</span>
              <span className="text-xl font-bold text-emerald-400 mt-1 block">
                {result.treatment_effects?.att.estimate !== undefined
                  ? (result.treatment_effects.att.estimate >= 0 ? `+${result.treatment_effects.att.estimate.toFixed(3)}` : result.treatment_effects.att.estimate.toFixed(3))
                  : 'N/A'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                N_treated = {result.diagnostics?.n_treated} người
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Độ Phân Tán Hiệu Ứng SD(τ)</span>
              <span className="text-xl font-bold text-amber-400 mt-1 block">
                {result.ite_distribution?.sd_tau.toFixed(3)}
              </span>
              <span className="text-[10px] mt-1 flex items-center gap-1 font-medium">
                {result.diagnostics?.has_significant_heterogeneity ? (
                  <span className="text-amber-400 flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" /> Tồn tại HTE đáng kể
                  </span>
                ) : (
                  <span className="text-slate-400">Hiệu ứng tương đối đồng nhất</span>
                )}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Biến Điều Tiết Hàng Đầu</span>
              <span className="text-sm font-bold text-pink-400 mt-1 block truncate">
                {result.variable_importance && result.variable_importance.length > 0
                  ? result.variable_importance[0].covariate
                  : 'Không có'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Ảnh hưởng {result.variable_importance && result.variable_importance.length > 0
                  ? `${(result.variable_importance[0].relative_importance * 100).toFixed(1)}%`
                  : '0%'}
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
                onClick={() => setActiveTab('cate')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'cate'
                    ? 'border-violet-400 text-violet-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Phân Rã CATE Theo Phân Nhóm ({result.subgroup_cate?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('ite')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'ite'
                    ? 'border-violet-400 text-violet-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Phân Phối Hiệu Ứng Cá Thể (ITE)
              </button>
              <button
                onClick={() => setActiveTab('vip')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                  activeTab === 'vip'
                    ? 'border-violet-400 text-violet-400 bg-slate-950/60'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Xếp Hạng Biến Điều Tiết ({result.variable_importance?.length || 0})
              </button>
            </div>

            <div className="p-4 overflow-x-auto">
              {activeTab === 'cate' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Biến Điều Tiết (Moderator)</th>
                      <th className="py-2.5 px-3">Phân Nhóm Con</th>
                      <th className="py-2.5 px-3 text-right">Số Mẫu (N)</th>
                      <th className="py-2.5 px-3 text-right">Ước Lượng CATE</th>
                      <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                      <th className="py-2.5 px-3 text-right">95% CrI Hậu Nghiệm</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.subgroup_cate && result.subgroup_cate.length > 0 ? (
                      result.subgroup_cate.map((sc, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-2.5 px-3 font-medium text-pink-300">{sc.moderator}</td>
                          <td className="py-2.5 px-3 font-semibold text-slate-200">{sc.subgroup}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-slate-400">{sc.n_respondents}</td>
                          <td className={`py-2.5 px-3 text-right font-mono font-bold ${sc.cate_estimate >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {sc.cate_estimate >= 0 ? `+${sc.cate_estimate.toFixed(3)}` : sc.cate_estimate.toFixed(3)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono text-slate-400">{sc.se.toFixed(3)}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                            [{sc.ci_95_lower.toFixed(2)}, {sc.ci_95_upper.toFixed(2)}]
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-4 text-center text-slate-500">
                          Không đủ dữ liệu phân nhóm con cho biến điều tiết.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {activeTab === 'ite' && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-2">
                  <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase">Phân vị 5% (P05)</span>
                    <span className="text-base font-mono font-bold text-slate-300 mt-1 block">
                      {result.ite_distribution?.p05.toFixed(3)}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase">Phân vị 25% (P25)</span>
                    <span className="text-base font-mono font-bold text-slate-300 mt-1 block">
                      {result.ite_distribution?.p25.toFixed(3)}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase">Trung Vị (Median)</span>
                    <span className="text-base font-mono font-bold text-violet-400 mt-1 block">
                      {result.ite_distribution?.median.toFixed(3)}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase">Phân vị 75% (P75)</span>
                    <span className="text-base font-mono font-bold text-slate-300 mt-1 block">
                      {result.ite_distribution?.p75.toFixed(3)}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase">Phân vị 95% (P95)</span>
                    <span className="text-base font-mono font-bold text-slate-300 mt-1 block">
                      {result.ite_distribution?.p95.toFixed(3)}
                    </span>
                  </div>
                </div>
              )}

              {activeTab === 'vip' && (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Tên Biến Điều Tiết (Covariate)</th>
                      <th className="py-2.5 px-3 text-right">Số Lần Tách Nhánh (Splits)</th>
                      <th className="py-2.5 px-3 text-right">Mức Độ Ảnh Hưởng Tương Đối</th>
                      <th className="py-2.5 px-3 text-center">Phân Loại Vai Trò</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.variable_importance?.map((vip, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-slate-200">{vip.covariate}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-400">{vip.split_count}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-semibold text-pink-400">
                          {(vip.relative_importance * 100).toFixed(1)}%
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {vip.is_primary_moderator ? (
                            <span className="px-2.5 py-0.5 rounded-full bg-pink-500/10 text-pink-400 text-[10px] font-semibold border border-pink-500/30">
                              Điều tiết chính (Primary)
                            </span>
                          ) : (
                            <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-medium">
                              Thứ yếu (Secondary)
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
                  <Info className="w-4 h-4 text-violet-400" />
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
