import React, { useState } from 'react';
import {
  NetworkSpilloverResult,
  NetworkSpilloverRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Share2,
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
  ShieldAlert,
  Users,
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

export const NetworkSpilloverCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [clusterQId, setClusterQId] = useState<string>('');
  const [confounderQIds, setConfounderQIds] = useState<string[]>([]);
  const [spilloverThreshold, setSpilloverThreshold] = useState<number>(0.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<NetworkSpilloverResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const toggleConfounder = (id: string) => {
    setConfounderQIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId || !clusterQId) {
      setError('Vui lòng chọn biến Kết quả Y, biến Can thiệp cá thể Z, và biến Cụm/Đội nhóm/Mạng lưới.');
      return;
    }
    if (outcomeQId === treatmentQId || outcomeQId === clusterQId || treatmentQId === clusterQId) {
      setError('Các biến can thiệp, kết quả và cụm phân nhóm không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: NetworkSpilloverRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      cluster_question_id: clusterQId,
      covariate_question_ids: confounderQIds.length > 0 ? confounderQIds : undefined,
      spillover_threshold: spilloverThreshold,
      alpha_level: 0.05,
      scope: scope
    };

    try {
      const data = await api.runNetworkSpillover(surveyId, payload);
      if (data.status === 'ERROR') {
        setError(data.message || 'Lỗi trong quá trình ước lượng Network Spillover & SUTVA.');
      } else if (data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Số lượng mẫu khảo sát hợp lệ chưa đủ để phân tích mạng lưới can thiệp.');
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
      <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none -ml-20 -mb-20" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5" />
              DataTrust Iteration 161
            </span>
            <span className="text-xs text-slate-400">
              Hudgens & Halloran (2008 JASA) • Aronow & Samii (2017) • Sävje et al. (2021 JRSS-B)
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Causal Interference & Peer Spillover Network Engine (Network SUTVA)
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Bóc tách tác động nhân quả trực tiếp (ADE) so với hiệu ứng lây lan gián tiếp qua mạng lưới đồng nghiệp (AIE), kiểm định vi phạm giả định SUTVA và hồi quy liều lượng can thiệp nhóm.
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

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 relative z-10">
        {/* Core Variables */}
        <div className="space-y-3 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg">
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
            <label className="text-xs font-semibold text-blue-400 block mb-1">
              Biến Can thiệp cá thể (Treatment Z) *
            </label>
            <select
              value={treatmentQId}
              onChange={e => setTreatmentQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">-- Chọn câu hỏi can thiệp (0/1 hoặc phân loại) --</option>
              {questions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-amber-400 block mb-1">
              Biến Cụm / Đội nhóm / Mạng lưới (Cluster ID) *
            </label>
            <select
              value={clusterQId}
              onChange={e => setClusterQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            >
              <option value="">-- Chọn biến xác định đội ngũ/phòng ban/lớp học --</option>
              {questions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Confounders Multi-select */}
        <div className="space-y-2 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg">
          <label className="text-xs font-semibold text-slate-300 block flex items-center justify-between">
            <span>Biến Kiểm soát / Nhiễu (Confounders X)</span>
            <span className="text-[10px] text-slate-400 font-normal">
              Đã chọn: {confounderQIds.length}
            </span>
          </label>
          <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
            {numericQuestions.map(q => {
              const isSelected = confounderQIds.includes(q.id);
              return (
                <div
                  key={q.id}
                  onClick={() => toggleConfounder(q.id)}
                  className={`flex items-center gap-2 p-1.5 rounded cursor-pointer text-xs transition ${
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

        {/* Threshold & Submit */}
        <div className="space-y-3 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg flex flex-col justify-between">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Ngưỡng phơi nhiễm lan truyền (Spillover Threshold)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="0.5"
                step="0.05"
                value={spilloverThreshold}
                onChange={e => setSpilloverThreshold(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <span className="text-xs font-mono text-cyan-300 font-semibold min-w-[40px]">
                {(spilloverThreshold * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">
              {spilloverThreshold === 0
                ? 'Bất kỳ đồng nghiệp nào được can thiệp đều tính là phơi nhiễm lan truyền.'
                : `Cần tối thiểu ${(spilloverThreshold * 100).toFixed(0)}% đồng nghiệp được can thiệp để tính là phơi nhiễm.`}
            </p>
          </div>

          <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
            <div className="flex-1">
              <label className="text-[10px] text-slate-400 block mb-0.5">Phạm vi mẫu</label>
              <select
                value={scope}
                onChange={e => setScope(e.target.value as any)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300"
              >
                <option value="all">Tất cả phản hồi</option>
                <option value="verified_clean">Chỉ mẫu sạch đã duyệt</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-cyan-600 to-amber-600 hover:from-cyan-500 hover:to-amber-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-cyan-900/30 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                Đang ước lượng Causal Interference...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Chạy phân tích Network SUTVA
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
          {/* KPI Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-blue-300 flex items-center gap-1">
                <Activity className="w-3 h-3 text-blue-400" />
                Direct Effect (ADE)
              </span>
              <div className="text-lg font-bold text-blue-300 mt-0.5">
                {(result.average_direct_effect?.estimate ?? 0) > 0 ? '+' : ''}
                {result.average_direct_effect?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                p = {result.average_direct_effect?.p_value?.toFixed(3) ?? '--'}
                <span className="block text-[9px] text-slate-500">
                  CI: [{result.average_direct_effect?.ci_95[0]?.toFixed(2)}, {result.average_direct_effect?.ci_95[1]?.toFixed(2)}]
                </span>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-amber-300 flex items-center gap-1">
                <Share2 className="w-3 h-3 text-amber-400" />
                Spillover Effect (AIE)
              </span>
              <div className="text-lg font-bold text-amber-300 mt-0.5">
                {(result.average_spillover_effect?.estimate ?? 0) > 0 ? '+' : ''}
                {result.average_spillover_effect?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                p = {result.average_spillover_effect?.p_value?.toFixed(3) ?? '--'}
                <span className="block text-[9px] text-slate-500">
                  CI: [{result.average_spillover_effect?.ci_95[0]?.toFixed(2)}, {result.average_spillover_effect?.ci_95[1]?.toFixed(2)}]
                </span>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-purple-300 flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-purple-400" />
                Total Overall (OTE)
              </span>
              <div className="text-lg font-bold text-purple-300 mt-0.5">
                {(result.total_overall_effect?.estimate ?? 0) > 0 ? '+' : ''}
                {result.total_overall_effect?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                Tổng hợp cá thể + đồng nghiệp
                <span className="block text-[9px] text-slate-500">
                  CI: [{result.total_overall_effect?.ci_95[0]?.toFixed(2)}, {result.total_overall_effect?.ci_95[1]?.toFixed(2)}]
                </span>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-sky-300 flex items-center gap-1">
                <Percent className="w-3 h-3 text-sky-400" />
                Spillover Share
              </span>
              <div className="text-lg font-bold text-sky-300 mt-0.5">
                {result.spillover_share_pct?.toFixed(1) ?? '--'}%
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                Tỷ trọng lan truyền mạng lưới
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-slate-300 flex items-center gap-1">
                {result.sutva_test?.is_violated ? (
                  <ShieldAlert className="w-3 h-3 text-rose-400" />
                ) : (
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                )}
                SUTVA Status
              </span>
              <div
                className={`text-xs font-bold mt-1.5 px-2 py-0.5 rounded text-center ${
                  result.sutva_test?.is_violated
                    ? 'bg-rose-950/60 text-rose-300 border border-rose-700/50'
                    : 'bg-emerald-950/60 text-emerald-300 border border-emerald-700/50'
                }`}
              >
                {result.sutva_test?.is_violated ? 'VI PHẠM SUTVA' : 'SUTVA THỎA MÃN'}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                p = {result.sutva_test?.p_value?.toFixed(4)}
              </div>
            </div>
          </div>

          {/* SVG Network Graph */}
          {result.svg_visualization && (
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 shadow-inner">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  Sơ đồ Mạng lưới Can thiệp &amp; Cụm Phơi nhiễm (Interference Topology)
                </span>
                <span className="text-[11px] text-slate-500">
                  DataTrust Network SUTVA Visualizer • {result.n_clusters} Cụm đội ngũ
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* 4 Exposure States Breakdown Table & Dosage Regression */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 4-State Exposure Distribution */}
            <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5 mb-3">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                Phân bổ 4 Trạng thái Phơi nhiễm Causal Exposure
              </span>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2 rounded bg-slate-900/50 border border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-slate-500" />
                    <span className="text-slate-300 font-medium">Đối chứng Cô lập (0, 0)</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-white font-bold">{result.potential_outcome_means?.isolated_control?.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-500 block">N = {result.exposure_sample_sizes?.isolated_control}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-900/50 border border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-blue-500" />
                    <span className="text-blue-300 font-medium">Chỉ Can thiệp Trực tiếp (1, 0)</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-blue-300 font-bold">{result.potential_outcome_means?.direct_only?.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-500 block">N = {result.exposure_sample_sizes?.direct_only}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-900/50 border border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-amber-500" />
                    <span className="text-amber-300 font-medium">Chỉ Hưởng Lan truyền (0, 1)</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-amber-300 font-bold">{result.potential_outcome_means?.spillover_only?.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-500 block">N = {result.exposure_sample_sizes?.spillover_only}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-900/50 border border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-purple-500" />
                    <span className="text-purple-300 font-medium">Can thiệp Toàn phần (1, 1)</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-purple-300 font-bold">{result.potential_outcome_means?.joint_treated?.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-500 block">N = {result.exposure_sample_sizes?.joint_treated}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Continuous Peer Dosage Regression Card */}
            <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5 mb-2">
                  <Compass className="w-3.5 h-3.5 text-amber-400" />
                  Hồi quy Liều lượng Phơi nhiễm Nhóm (Neighborhood Dosage)
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {result.dosage_regression?.interpretation}
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Hệ số Can thiệp Trực tiếp (Z)</span>
                    <span className="text-sm font-bold font-mono text-blue-300">
                      {(result.dosage_regression?.direct_coefficient ?? 0) > 0 ? '+' : ''}
                      {result.dosage_regression?.direct_coefficient?.toFixed(3)}
                    </span>
                    <span className="text-[10px] text-slate-500 block">p = {result.dosage_regression?.direct_pvalue?.toFixed(3)}</span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Độ dốc Lan truyền Đồng nghiệp (S)</span>
                    <span className="text-sm font-bold font-mono text-amber-300">
                      {(result.dosage_regression?.peer_spillover_slope ?? 0) > 0 ? '+' : ''}
                      {result.dosage_regression?.peer_spillover_slope?.toFixed(3)}
                    </span>
                    <span className="text-[10px] text-slate-500 block">p = {result.dosage_regression?.spillover_pvalue?.toFixed(3)}</span>
                  </div>
                </div>
              </div>

              <div className="mt-3 p-2.5 rounded bg-slate-900/70 border border-slate-800 text-[11px] text-slate-400">
                <span className="text-amber-300 font-semibold">Ý nghĩa phương pháp luận: </span>
                Khi SUTVA bị vi phạm, việc bỏ qua hiệu ứng lan truyền sẽ gây đánh giá sai lệch tác động chính sách (underestimation nếu lan truyền cùng chiều, hoặc overestimation nếu hiệu ứng bù trừ cạnh tranh).
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
