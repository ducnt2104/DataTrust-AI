import React, { useState } from 'react';
import {
  DynamicSpatialPanelResult,
  DynamicSpatialPanelRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Globe2,
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
  MapPin,
  Clock,
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

export const DynamicSpatialPanelCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [regionQId, setRegionQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [latQId, setLatQId] = useState<string>('');
  const [lonQId, setLonQId] = useState<string>('');
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DynamicSpatialPanelResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const toggleCovariate = (id: string) => {
    setCovariateQIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !regionQId || !timeQId) {
      setError('Vui lòng chọn biến Kết quả Y, biến Khu vực địa lý, và biến Đợt khảo sát/Thời gian.');
      return;
    }
    if (outcomeQId === regionQId || outcomeQId === timeQId || regionQId === timeQId) {
      setError('Các biến kết quả, khu vực và thời gian không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: DynamicSpatialPanelRequest = {
      outcome_question_id: outcomeQId,
      region_question_id: regionQId,
      time_question_id: timeQId,
      covariate_question_ids: covariateQIds.length > 0 ? covariateQIds : undefined,
      lat_question_id: latQId || undefined,
      lon_question_id: lonQId || undefined,
      alpha_level: 0.05,
      scope: scope
    };

    try {
      const data = await api.runDynamicSpatialPanel(surveyId, payload);
      if (data.status === 'ERROR') {
        setError(data.message || 'Lỗi trong quá trình ước lượng Dynamic Spatial Panel.');
      } else if (data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Số lượng mẫu khảo sát hợp lệ chưa đủ để phân tích bảng không gian động.');
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
      <div className="absolute top-0 right-0 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none -ml-20 -mb-20" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30 flex items-center gap-1.5">
              <Globe2 className="w-3.5 h-3.5" />
              DataTrust Iteration 162
            </span>
            <span className="text-xs text-slate-400">
              Elhorst (2014) • Lee &amp; Yu (2010 Econometrica) • LeSage &amp; Pace (2009)
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Dynamic Spatial Panel Econometrics &amp; Spatio-Temporal Diffusion
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Ước lượng hồi quy tự tương quan không gian động đa đợt (trễ thời gian γ, trễ không gian ρ, lan truyền không-thời gian η) và phân rã số nhân tác động LeSage-Pace.
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
        {/* Core Dimensions */}
        <div className="space-y-3 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg">
          <div>
            <label className="text-xs font-semibold text-sky-400 block mb-1">
              Biến Kết quả (Outcome Y) *
            </label>
            <select
              value={outcomeQId}
              onChange={e => setOutcomeQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="">-- Chọn câu hỏi kết quả (liên tục/chỉ số) --</option>
              {numericQuestions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-emerald-400 block mb-1">
              Biến Khu vực / Địa bàn (Region ID) *
            </label>
            <select
              value={regionQId}
              onChange={e => setRegionQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">-- Chọn câu hỏi phân loại tỉnh/huyện/khu vực --</option>
              {questions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-amber-400 block mb-1">
              Biến Đợt khảo sát / Thời gian (Time Wave) *
            </label>
            <select
              value={timeQId}
              onChange={e => setTimeQId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            >
              <option value="">-- Chọn câu hỏi mốc thời gian/đợt khảo sát --</option>
              {questions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Coordinates & Covariates */}
        <div className="space-y-3 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg flex flex-col justify-between">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-slate-400 block mb-0.5">Vĩ độ (Latitude)</label>
              <select
                value={latQId}
                onChange={e => setLatQId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300"
              >
                <option value="">-- Tự động --</option>
                {numericQuestions.map(q => (
                  <option key={q.id} value={q.id}>{q.title}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-slate-400 block mb-0.5">Kinh độ (Longitude)</label>
              <select
                value={lonQId}
                onChange={e => setLonQId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300"
              >
                <option value="">-- Tự động --</option>
                {numericQuestions.map(q => (
                  <option key={q.id} value={q.id}>{q.title}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block flex items-center justify-between mb-1">
              <span>Biến Giải thích / Kiểm soát (Covariates X)</span>
              <span className="text-[10px] text-slate-400 font-normal">Đã chọn: {covariateQIds.length}</span>
            </label>
            <div className="max-h-24 overflow-y-auto space-y-1 pr-1">
              {numericQuestions.map(q => {
                const isSelected = covariateQIds.includes(q.id);
                return (
                  <div
                    key={q.id}
                    onClick={() => toggleCovariate(q.id)}
                    className={`flex items-center gap-2 p-1 rounded cursor-pointer text-[11px] transition ${
                      isSelected
                        ? 'bg-sky-950/60 border border-sky-600/50 text-sky-200'
                        : 'hover:bg-slate-800/60 text-slate-400'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      readOnly
                      className="rounded border-slate-600 text-sky-500 focus:ring-0 cursor-pointer"
                    />
                    <span className="truncate">{q.title}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Scope & Run Action */}
        <div className="space-y-3 bg-slate-800/40 border border-slate-800/80 p-3.5 rounded-lg flex flex-col justify-between">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Phạm vi Mẫu Phân tích
            </label>
            <select
              value={scope}
              onChange={e => setScope(e.target.value as any)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-300 mb-2"
            >
              <option value="all">Tất cả quan sát (Toàn bộ dữ liệu bảng)</option>
              <option value="verified_clean">Chỉ mẫu sạch đã kiểm duyệt</option>
            </select>
            <p className="text-[10px] text-slate-400">
              Động cơ tự động tính ma trận khoảng cách nghịch đảo chuẩn hóa theo hàng và áp dụng khử hiệu ứng cố định khu vực (FE De-meaning).
            </p>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-sky-600 to-amber-600 hover:from-sky-500 hover:to-amber-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-sky-900/30 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                Đang ước lượng Dynamic Spatial Panel...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Chạy phân tích Dynamic Spatial Panel
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
              <span className="text-[10px] uppercase font-semibold text-sky-300 flex items-center gap-1">
                <Clock className="w-3 h-3 text-sky-400" />
                Quán tính thời gian (γ)
              </span>
              <div className="text-lg font-bold text-sky-300 mt-0.5">
                {(result.spatio_temporal_parameters?.time_persistence_gamma?.estimate ?? 0) > 0 ? '+' : ''}
                {result.spatio_temporal_parameters?.time_persistence_gamma?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                p = {result.spatio_temporal_parameters?.time_persistence_gamma?.p_value?.toFixed(3) ?? '--'}
                <span className="block text-[9px] text-slate-500">
                  Half-life: {result.system_stability?.persistence_half_life_periods ?? '--'} kỳ
                </span>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-emerald-300 flex items-center gap-1">
                <Globe2 className="w-3 h-3 text-emerald-400" />
                Lan tỏa không gian (ρ)
              </span>
              <div className="text-lg font-bold text-emerald-300 mt-0.5">
                {(result.spatio_temporal_parameters?.contemporaneous_spatial_rho?.estimate ?? 0) > 0 ? '+' : ''}
                {result.spatio_temporal_parameters?.contemporaneous_spatial_rho?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                p = {result.spatio_temporal_parameters?.contemporaneous_spatial_rho?.p_value?.toFixed(3) ?? '--'}
                <span className="block text-[9px] text-slate-500">
                  Đồng thời qua ma trận W
                </span>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-purple-300 flex items-center gap-1">
                <Activity className="w-3 h-3 text-purple-400" />
                Không - Thời gian (η)
              </span>
              <div className="text-lg font-bold text-purple-300 mt-0.5">
                {(result.spatio_temporal_parameters?.spatio_temporal_diffusion_eta?.estimate ?? 0) > 0 ? '+' : ''}
                {result.spatio_temporal_parameters?.spatio_temporal_diffusion_eta?.estimate?.toFixed(3) ?? '--'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                p = {result.spatio_temporal_parameters?.spatio_temporal_diffusion_eta?.p_value?.toFixed(3) ?? '--'}
                <span className="block text-[9px] text-slate-500">
                  Trễ từ lân bang (W * Y_t-1)
                </span>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-amber-300 flex items-center gap-1">
                <Percent className="w-3 h-3 text-amber-400" />
                Long-Run Spillover
              </span>
              <div className="text-lg font-bold text-amber-300 mt-0.5">
                {result.long_run_impacts?.spillover_share_pct?.toFixed(1) ?? '--'}%
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                Tỷ trọng lan tỏa dài hạn
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/60 p-3 rounded-lg">
              <span className="text-[10px] uppercase font-semibold text-slate-300 flex items-center gap-1">
                {result.system_stability?.is_stable ? (
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-3 h-3 text-rose-400" />
                )}
                System Stability
              </span>
              <div
                className={`text-xs font-bold mt-1.5 px-2 py-0.5 rounded text-center ${
                  result.system_stability?.is_stable
                    ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-700/50'
                    : 'bg-rose-950/60 text-rose-300 border border-rose-700/50'
                }`}
              >
                {result.system_stability?.is_stable ? 'HỆ ỔN ĐỊNH (|λ| < 1)' : 'BÙNG NỔ'}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                |λ_max| = {result.system_stability?.max_eigen_modulus?.toFixed(3)}
              </div>
            </div>
          </div>

          {/* Dual Panel SVG Visualization */}
          {result.svg_visualization && (
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 shadow-inner">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                  Bản đồ Lan tỏa Không gian &amp; Số nhân Tác động LeSage-Pace
                </span>
                <span className="text-[11px] text-slate-500">
                  {result.n_regions} Khu vực • {result.n_time_periods} Đợt khảo sát
                </span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Multiplier Impact Comparison Table & Stability Interpretation */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Impact Decomposition Table */}
            <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5 mb-3">
                <Scale className="w-3.5 h-3.5 text-sky-400" />
                Bảng Phân rã Tác động Không gian LeSage-Pace Multipliers
              </span>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/50 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="py-2 px-3">Loại tác động</th>
                      <th className="py-2 px-3 text-sky-400">Ngắn hạn (Short-Run)</th>
                      <th className="py-2 px-3 text-amber-400">Dài hạn (Long-Run)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300 font-mono">
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 font-sans font-medium text-white">Tác động Trực tiếp (Direct)</td>
                      <td className="py-2 px-3 text-sky-300">{result.short_run_impacts?.direct?.toFixed(3)}</td>
                      <td className="py-2 px-3 text-amber-300">{result.long_run_impacts?.direct?.toFixed(3)}</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 font-sans font-medium text-white">Lan tỏa Lân bang (Indirect / Spillover)</td>
                      <td className="py-2 px-3 text-sky-300">{result.short_run_impacts?.indirect?.toFixed(3)}</td>
                      <td className="py-2 px-3 text-amber-300">{result.long_run_impacts?.indirect?.toFixed(3)}</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30 bg-slate-900/40 font-bold">
                      <td className="py-2 px-3 font-sans text-white">Tổng tác động (Total Impact)</td>
                      <td className="py-2 px-3 text-sky-400">{result.short_run_impacts?.total?.toFixed(3)}</td>
                      <td className="py-2 px-3 text-amber-400">{result.long_run_impacts?.total?.toFixed(3)}</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 font-sans text-slate-400">% Lan tỏa Mạng lưới</td>
                      <td className="py-2 px-3 text-slate-300">{result.short_run_impacts?.spillover_share_pct?.toFixed(1)}%</td>
                      <td className="py-2 px-3 text-slate-300">{result.long_run_impacts?.spillover_share_pct?.toFixed(1)}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Stability & Theoretical Context */}
            <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5 mb-2">
                  <Compass className="w-3.5 h-3.5 text-amber-400" />
                  Động thái Lan truyền Không - Thời gian &amp; Bán phân rã
                </span>
                <p className="text-xs text-slate-300 leading-relaxed mb-3">
                  {result.system_stability?.interpretation}
                </p>
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800">
                    <span className="text-slate-400">Thời gian bán phân rã quán tính (Half-life):</span>
                    <span className="font-mono text-sky-300 font-bold">{result.system_stability?.persistence_half_life_periods} đợt</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800">
                    <span className="text-slate-400">Số quan sát hiệu dụng sau khử cố định:</span>
                    <span className="font-mono text-white font-bold">{result.effective_panel_observations} quan sát</span>
                  </div>
                </div>
              </div>

              <div className="mt-3 p-2.5 rounded bg-slate-900/70 border border-slate-800 text-[11px] text-slate-400">
                <span className="text-amber-300 font-semibold">Ý nghĩa chính sách: </span>
                Số nhân dài hạn phản ánh toàn bộ hiệu ứng lan tỏa tích lũy qua thời gian và không gian. Khi $\rho + \eta &gt; 0$, các cú sốc chính sách hoặc đầu tư tại một địa phương sẽ kích hoạt hiệu ứng cộng hưởng lan tỏa sang toàn bộ các vùng lân cận.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
