import React, { useState } from 'react';
import {
  HighDimensionalMediationResult,
  HighDimensionalMediationRequest,
  MediatorPathway
} from '../types/survey';
import { api } from '../api/client';
import {
  Network,
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
  Sparkles,
  ArrowRight
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

export const HighDimensionalMediationCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [mediatorQIds, setMediatorQIds] = useState<string[]>([]);
  const [confounderQIds, setConfounderQIds] = useState<string[]>([]);
  const [subgroupQId, setSubgroupQId] = useState<string>('');
  const [nBoot, setNBoot] = useState<number>(50);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<HighDimensionalMediationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const toggleMediator = (id: string) => {
    setMediatorQIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const toggleConfounder = (id: string) => {
    setConfounderQIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId || !outcomeQId) {
      setError('Vui lòng chọn biến Can thiệp (Treatment T) và biến Kết quả (Outcome Y).');
      return;
    }
    if (treatmentQId === outcomeQId) {
      setError('Biến Can thiệp và Biến Kết quả không được trùng nhau.');
      return;
    }
    if (mediatorQIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến Trung gian (Mediator battery).');
      return;
    }
    if (mediatorQIds.includes(treatmentQId) || mediatorQIds.includes(outcomeQId)) {
      setError('Biến Trung gian không được trùng với Can thiệp hoặc Kết quả.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: HighDimensionalMediationRequest = {
      treatment_question_id: treatmentQId,
      outcome_question_id: outcomeQId,
      mediator_question_ids: mediatorQIds,
      confounder_question_ids: confounderQIds.length > 0 ? confounderQIds : undefined,
      subgroup_question_id: subgroupQId || undefined,
      n_boot: nBoot,
      alpha_level: 0.05,
      scope: scope
    };

    try {
      const data = await api.runHighDimensionalMediation(surveyId, payload);
      if (data.status === 'ERROR') {
        setError(data.message || 'Lỗi trong quá trình tính toán High-Dimensional Mediation.');
      } else if (data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Số lượng mẫu khảo sát hợp lệ chưa đủ để phân tích trung gian đa chiều.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể kết nối đến máy chủ.');
    } finally {
      setLoading(false);
    }
  };

  const copyResults = () => {
    if (!result) return;
    const txt = JSON.stringify(result, null, 2);
    navigator.clipboard.writeText(txt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden mb-8">
      {/* Background ambient glow */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -ml-20 -mb-20" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5" />
              DataTrust Iteration 160
            </span>
            <span className="text-xs text-slate-400">
              Imai, Keele & Tingley (2010 JASA) • VanderWeele (2015) • Zhao & Luo (2022 JRSS-B)
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            High-Dimensional Causal Mediation & Latent Path Invariance
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Phân rã tác động nhân quả thành hiệu ứng trực tiếp (NDE) và gián tiếp (NIE) qua tập biến trung gian đa chiều, kiểm tra độ nhạy (rho*) và tính bất biến cấu trúc theo nhóm.
          </p>
        </div>

        {result && (
          <button
            onClick={copyResults}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Đã sao chép' : 'Sao chép kết quả'}
          </button>
        )}
      </div>

      {/* Control Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 relative z-10">
        {/* Treatment & Outcome */}
        <div className="space-y-3 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg">
          <div>
            <label className="text-xs font-semibold text-blue-400 block mb-1">
              Biến Can thiệp (Treatment T) *
            </label>
            <select
              value={treatmentQId}
              onChange={e => setTreatmentQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">-- Chọn câu hỏi can thiệp (0/1 hoặc liên tục) --</option>
              {questions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-purple-400 block mb-1">
              Biến Kết quả (Outcome Y) *
            </label>
            <select
              value={outcomeQId}
              onChange={e => setOutcomeQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
            >
              <option value="">-- Chọn câu hỏi kết quả (liên tục/điểm số) --</option>
              {numericQuestions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">
              Phân nhóm khảo sát (Subgroup Invariance)
            </label>
            <select
              value={subgroupQId}
              onChange={e => setSubgroupQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-slate-500"
            >
              <option value="">-- Tùy chọn (Kiểm định bất biến đường dẫn) --</option>
              {questions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Mediators Multi-select */}
        <div className="space-y-2 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg">
          <label className="text-xs font-semibold text-emerald-400 block flex items-center justify-between">
            <span>Tập biến Trung gian (Mediator Battery) *</span>
            <span className="text-[10px] text-slate-400 font-normal">
              Đã chọn: {mediatorQIds.length}
            </span>
          </label>
          <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
            {numericQuestions.map(q => {
              const isSelected = mediatorQIds.includes(q.id);
              return (
                <div
                  key={q.id}
                  onClick={() => toggleMediator(q.id)}
                  className={`flex items-center gap-2 p-1.5 rounded cursor-pointer text-xs transition ${
                    isSelected
                      ? 'bg-emerald-950/60 border border-emerald-600/50 text-emerald-200'
                      : 'hover:bg-slate-800/60 text-slate-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    readOnly
                    className="rounded border-slate-600 text-emerald-500 focus:ring-0 cursor-pointer"
                  />
                  <span className="truncate">{q.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Confounders & Params */}
        <div className="space-y-3 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg flex flex-col justify-between">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Biến Kiểm soát / Nhiễu (Confounders X)
            </label>
            <div className="max-h-24 overflow-y-auto space-y-1 pr-1">
              {numericQuestions.map(q => {
                const isSelected = confounderQIds.includes(q.id);
                return (
                  <div
                    key={q.id}
                    onClick={() => toggleConfounder(q.id)}
                    className={`flex items-center gap-2 p-1 rounded cursor-pointer text-[11px] transition ${
                      isSelected
                        ? 'bg-blue-950/60 border border-blue-600/50 text-blue-200'
                        : 'hover:bg-slate-800/60 text-slate-400'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      readOnly
                      className="rounded border-slate-600 text-blue-500 focus:ring-0 cursor-pointer"
                    />
                    <span className="truncate">{q.title}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
            <div className="flex-1">
              <label className="text-[10px] text-slate-400 block mb-0.5">Số lần Bootstrap (B)</label>
              <select
                value={nBoot}
                onChange={e => setNBoot(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300"
              >
                <option value={30}>30 (Nhanh)</option>
                <option value={50}>50 (Tiêu chuẩn)</option>
                <option value={100}>100 (Khuyến nghị)</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="text-[10px] text-slate-400 block mb-0.5">Phạm vi mẫu</label>
              <select
                value={scope}
                onChange={e => setScope(e.target.value as any)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300"
              >
                <option value="all">Tất cả</option>
                <option value="verified_clean">Đã kiểm duyệt sạch</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-purple-600 to-emerald-600 hover:from-purple-500 hover:to-emerald-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-purple-900/30 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                Đang ước lượng Mediation & Bootstrap...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Chạy phân tích Causal Mediation
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6 relative z-10 animate-in fade-in duration-300">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-slate-400 flex items-center gap-1">
                <BarChart3 className="w-3 h-3 text-blue-400" />
                Total Effect (TE)
              </span>
              <div className="text-lg font-bold text-white mt-0.5">
                {result.total_effect?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                p = {result.total_effect?.p_value?.toFixed(3) ?? '--'}
                {result.total_effect?.ci_lower !== undefined && (
                  <span className="block text-[9px] text-slate-500">
                    CI: [{result.total_effect.ci_lower.toFixed(2)}, {result.total_effect.ci_upper?.toFixed(2)}]
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-purple-300 flex items-center gap-1">
                <Activity className="w-3 h-3 text-purple-400" />
                Direct Effect (NDE)
              </span>
              <div className="text-lg font-bold text-purple-300 mt-0.5">
                {result.natural_direct_effect?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                p = {result.natural_direct_effect?.p_value?.toFixed(3) ?? '--'}
                {result.natural_direct_effect?.ci_lower !== undefined && (
                  <span className="block text-[9px] text-slate-500">
                    CI: [{result.natural_direct_effect.ci_lower.toFixed(2)}, {result.natural_direct_effect.ci_upper?.toFixed(2)}]
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-emerald-300 flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                Indirect Effect (NIE)
              </span>
              <div className="text-lg font-bold text-emerald-300 mt-0.5">
                {result.natural_indirect_effect?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                Qua {result.n_mediators} biến
                {result.natural_indirect_effect?.ci_lower !== undefined && (
                  <span className="block text-[9px] text-slate-500">
                    CI: [{result.natural_indirect_effect.ci_lower.toFixed(2)}, {result.natural_indirect_effect.ci_upper?.toFixed(2)}]
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-sky-300 flex items-center gap-1">
                <Percent className="w-3 h-3 text-sky-400" />
                Proportion Mediated
              </span>
              <div className="text-lg font-bold text-sky-300 mt-0.5">
                {result.proportion_mediated?.percentage?.toFixed(1) ?? '--'}%
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                Tỷ trọng gián tiếp
                {result.proportion_mediated?.ci_lower !== undefined && (
                  <span className="block text-[9px] text-slate-500">
                    CI: [{(result.proportion_mediated.ci_lower * 100).toFixed(0)}%, {(result.proportion_mediated.ci_upper! * 100).toFixed(0)}%]
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-amber-300 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-amber-400" />
                Sensitivity (rho*)
              </span>
              <div className="text-lg font-bold text-amber-300 mt-0.5">
                |rho*| = {Math.abs(result.sequential_ignorability_sensitivity?.dominant_rho_critical ?? 0).toFixed(2)}
              </div>
              <div className="mt-0.5">
                <span
                  className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                    result.sequential_ignorability_sensitivity?.robustness === 'ROBUST'
                      ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-700/50'
                      : result.sequential_ignorability_sensitivity?.robustness === 'MODERATE'
                      ? 'bg-amber-950/60 text-amber-300 border border-amber-700/50'
                      : 'bg-rose-950/60 text-rose-300 border border-rose-700/50'
                  }`}
                >
                  {result.sequential_ignorability_sensitivity?.robustness}
                </span>
              </div>
            </div>
          </div>

          {/* SVG Diagram Canvas */}
          {result.svg_visualization && (
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 shadow-inner">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                  Sơ đồ luồng nhân quả đa tầng (Causal Path Diagram)
                </span>
                <span className="text-[11px] text-slate-500">
                  DataTrust High-Dimensional Structural Vector
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Mediator Pathways Ranking Table */}
          <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl overflow-hidden">
            <div className="p-3.5 bg-slate-800/60 border-b border-slate-700/70 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                Bảng xếp hạng đóng góp của các biến trung gian (Component Pathways)
              </span>
              <span className="text-[11px] text-slate-400">
                Xếp hạng theo độ lớn hiệu ứng gián tiếp |IE|
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/50 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Thứ hạng / Biến trung gian</th>
                    <th className="py-2.5 px-3">T → M (alpha)</th>
                    <th className="py-2.5 px-3">M → Y (beta)</th>
                    <th className="py-2.5 px-3">Gián tiếp (IE = alpha*beta)</th>
                    <th className="py-2.5 px-3">Sobel p-val</th>
                    <th className="py-2.5 px-3">% Đóng góp</th>
                    <th className="py-2.5 px-3">Độ nhạy rho* (Imai 2010)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {result.mediator_pathways?.map((med: MediatorPathway, idx: number) => {
                    const qInfo = questions.find(q => q.id === med.mediator_col);
                    const qTitle = qInfo ? qInfo.title : med.mediator_col;
                    return (
                      <tr key={med.mediator_col} className="hover:bg-slate-800/30 transition">
                        <td className="py-2.5 px-3 font-medium text-white flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-slate-800 border border-slate-700 text-[10px] flex items-center justify-center text-slate-300">
                            {idx + 1}
                          </span>
                          <span className="truncate max-w-[200px]" title={qTitle}>
                            {qTitle}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-blue-300">
                          {med.alpha_treatment_to_med > 0 ? '+' : ''}{med.alpha_treatment_to_med.toFixed(3)}
                          <span className="text-[9px] text-slate-500 block">p={med.alpha_pvalue.toFixed(3)}</span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-emerald-300">
                          {med.beta_med_to_outcome > 0 ? '+' : ''}{med.beta_med_to_outcome.toFixed(3)}
                          <span className="text-[9px] text-slate-500 block">p={med.beta_pvalue.toFixed(3)}</span>
                        </td>
                        <td className="py-2.5 px-3 font-mono font-bold text-purple-300">
                          {med.indirect_effect > 0 ? '+' : ''}{med.indirect_effect.toFixed(3)}
                          {med.ci_lower !== undefined && (
                            <span className="text-[9px] text-slate-500 block">
                              [{med.ci_lower.toFixed(2)}, {med.ci_upper?.toFixed(2)}]
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-mono">
                          <span className={med.sobel_pvalue < 0.05 ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                            {med.sobel_pvalue.toFixed(3)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="flex items-center gap-1.5">
                            <div className="w-16 bg-slate-700/60 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-purple-500 h-full rounded-full"
                                style={{ width: `${Math.min(100, med.mediation_share_pct)}%` }}
                              />
                            </div>
                            <span className="font-mono text-xs">{med.mediation_share_pct.toFixed(1)}%</span>
                          </div>
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                              med.sensitivity_robustness === 'ROBUST'
                                ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-700/50'
                                : med.sensitivity_robustness === 'MODERATE'
                                ? 'bg-amber-950/60 text-amber-300 border border-amber-700/50'
                                : 'bg-rose-950/60 text-rose-300 border border-rose-700/50'
                            }`}
                          >
                            |rho*| = {Math.abs(med.critical_rho_sensitivity).toFixed(2)} ({med.sensitivity_robustness})
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Latent Path Invariance & Sensitivity Notes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Invariance Test */}
            <div className="bg-slate-800/40 border border-slate-800/80 p-4 rounded-xl">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-2">
                <Split className="w-3.5 h-3.5 text-blue-400" />
                Kiểm định tính bất biến cấu trúc (Latent Path Invariance)
              </span>
              {result.latent_path_invariance?.tested ? (
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Các nhóm so sánh:</span>
                    <span className="text-white font-medium">
                      {result.latent_path_invariance.groups_compared?.join(' vs ')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Wald Chi-square (χ²):</span>
                    <span className="font-mono text-slate-200">
                      {result.latent_path_invariance.wald_statistic?.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">p-value:</span>
                    <span className="font-mono text-slate-200">
                      {result.latent_path_invariance.p_value?.toFixed(4)}
                    </span>
                  </div>
                  <div className="pt-2 border-t border-slate-800">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        result.latent_path_invariance.is_invariant
                          ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-700/50'
                          : 'bg-rose-950/60 text-rose-300 border border-rose-700/50'
                      }`}
                    >
                      {result.latent_path_invariance.is_invariant
                        ? 'CẤU TRÚC ĐƯỜNG DẪN BẤT BIẾN (INVARIANT)'
                        : 'DỊ BIỆT CẤU TRÚC GIỮA CÁC NHÓM (HETEROGENEOUS)'}
                    </span>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {result.latent_path_invariance.interpretation}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  Chưa kích hoạt kiểm định phân nhóm. Chọn biến phân nhóm (Subgroup) ở bảng điều khiển để kiểm định tính bất biến của các hệ số beta giữa các phân khúc khảo sát.
                </p>
              )}
            </div>

            {/* Ignorability Sensitivity Note */}
            <div className="bg-slate-800/40 border border-slate-800/80 p-4 rounded-xl">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-2">
                <Compass className="w-3.5 h-3.5 text-amber-400" />
                Giả định Bỏ qua Tuần tự & Độ nhạy (Sequential Ignorability)
              </span>
              <p className="text-xs text-slate-300 leading-relaxed">
                {result.sequential_ignorability_sensitivity?.interpretation}
              </p>
              <div className="mt-3 p-2 rounded bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400">
                <span className="text-amber-300 font-semibold">Quy chuẩn học thuật: </span>
                Tham số |rho*| biểu thị tương quan dư tối thiểu giữa phương trình trung gian và phương trình kết quả đủ để làm triệt tiêu hiệu ứng gián tiếp NIE. Giá trị |rho*| &gt; 0.35 chứng minh kết luận nhân quả rất vững trước các biến nhiễu tiềm ẩn không quan sát được.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
