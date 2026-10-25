import React, { useState } from 'react';
import {
  Users,
  PieChart,
  BarChart3,
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Copy,
  Check,
  Layers,
  ArrowRight,
  Filter,
  Activity,
  Award
} from 'lucide-react';
import { api } from '../api/client';
import {
  AbadieComplierResult,
  AbadieComplierRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const AbadieComplierProfilingCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentId, setTreatmentId] = useState<string>('');
  const [instrumentId, setInstrumentId] = useState<string>('');
  const [covariateIds, setCovariateIds] = useState<string[]>([]);
  const [outcomeId, setOutcomeId] = useState<string>('');
  const [estimatePropensity, setEstimatePropensity] = useState<boolean>(true);
  const [nBootstraps, setNBootstraps] = useState<number>(150);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AbadieComplierResult | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'profiles' | 'late' | 'apa'>('overview');
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'slider' || q.question_type === 'single_choice'
  );

  const handleToggleCovariate = (qid: string) => {
    if (covariateIds.includes(qid)) {
      setCovariateIds(covariateIds.filter(id => id !== qid));
    } else {
      setCovariateIds([...covariateIds, qid]);
    }
  };

  const handleRun = async () => {
    if (!treatmentId || !instrumentId) {
      setError('Vui lòng chọn cả biến Can thiệp D (0/1) và biến Công cụ Khuyến khích Z (0/1).');
      return;
    }
    if (treatmentId === instrumentId) {
      setError('Biến can thiệp D và biến công cụ Z không được trùng nhau.');
      return;
    }
    if (covariateIds.length === 0) {
      setError('Vui lòng chọn ít nhất một biến nhân khẩu học / kiểm soát X để định danh Complier.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: AbadieComplierRequest = {
      treatment_question_id: treatmentId,
      instrument_question_id: instrumentId,
      covariate_question_ids: covariateIds,
      outcome_question_id: outcomeId || undefined,
      estimate_instrument_propensity: estimatePropensity,
      n_bootstraps: nBootstraps,
      scope,
    };

    try {
      const data = await api.runAbadieComplierProfiling(surveyId, payload);
      setResult(data);
      if (data.late_causal_effect) {
        setActiveTab('overview');
      }
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực thi Abadie Complier Profiling.');
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
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold tracking-tight text-white">
              Abadie (2003) Complier Profiling & Compliance Typology Engine
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Phân rã nhóm tuân thủ (Compliers, Always-Takers, Never-Takers) & Định danh nhân khẩu học dưới trọng số kappa phi tham số (Abadie 2003; Marbach & Hangartner 2020)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            Econometric IV
          </span>
          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
            Kappa-Weighting
          </span>
        </div>
      </div>

      {/* Config Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Treatment D */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Biến Can Thiệp D (Nhị phân 0/1) <span className="text-rose-400">*</span>
          </label>
          <select
            value={treatmentId}
            onChange={(e) => setTreatmentId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="">-- Chọn biến Can thiệp D --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Instrument Z */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            Biến Công Cụ Khuyến Khích Z (Nhị phân 0/1) <span className="text-rose-400">*</span>
          </label>
          <select
            value={instrumentId}
            onChange={(e) => setInstrumentId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">-- Chọn biến Công cụ Z --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Y */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
            Biến Kết Quả Y (Tùy chọn cho LATE)
          </label>
          <select
            value={outcomeId}
            onChange={(e) => setOutcomeId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="">-- Không có (Chỉ định danh Complier) --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Covariates Selection */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-amber-400" />
          Các Biến Nhân Khẩu Học & Đặc Trưng X (Chọn để lập hồ sơ Complier) <span className="text-rose-400">*</span>
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-36 overflow-y-auto p-2 bg-slate-950/60 rounded-lg border border-slate-800">
          {numericQuestions
            .filter((q) => q.id !== treatmentId && q.id !== instrumentId && q.id !== outcomeId)
            .map((q) => {
              const isSelected = covariateIds.includes(q.id);
              return (
                <button
                  type="button"
                  key={q.id}
                  onClick={() => handleToggleCovariate(q.id)}
                  className={`text-left text-xs px-2.5 py-1.5 rounded-md border transition-colors flex items-center justify-between ${
                    isSelected
                      ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate pr-1">{q.title}</span>
                  {isSelected && <Check className="w-3 h-3 flex-shrink-0" />}
                </button>
              );
            })}
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800">
          <input
            type="checkbox"
            id="estPropensity"
            checked={estimatePropensity}
            onChange={(e) => setEstimatePropensity(e.target.checked)}
            className="rounded border-slate-700 text-emerald-600 focus:ring-emerald-500 bg-slate-900"
          />
          <label htmlFor="estPropensity" className="text-xs text-slate-300 select-none">
            Ước lượng Propensity Score $\pi(X) = P(Z=1|X)$ (Logit)
          </label>
        </div>

        <div className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800">
          <label className="text-xs text-slate-300">Bootstrap SE:</label>
          <input
            type="number"
            min={30}
            max={500}
            value={nBootstraps}
            onChange={(e) => setNBootstraps(Number(e.target.value))}
            className="w-20 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 text-center"
          />
        </div>

        <div className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800">
          <label className="text-xs text-slate-300">Dữ liệu:</label>
          <select
            value={scope}
            onChange={(e: any) => setScope(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
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
            className="px-5 py-2.5 rounded-lg font-semibold text-sm bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Đang phân rã Typology & Weights...</span>
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                <span>Thực thi Complier Profiling</span>
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
            {/* Compliers */}
            <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-lg p-3.5 relative overflow-hidden">
              <div className="text-xs text-emerald-400 font-medium">Tỷ Lệ Compliers</div>
              <div className="text-2xl font-bold text-white mt-1">
                {(result.compliance_typology.p_compliers * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-emerald-400/80 mt-0.5">
                ~{result.compliance_typology.complier_count_est} quan sát (N = {result.sample_size})
              </div>
            </div>

            {/* Always-Takers */}
            <div className="bg-blue-950/20 border border-blue-500/30 rounded-lg p-3.5 relative overflow-hidden">
              <div className="text-xs text-blue-400 font-medium">Always-Takers</div>
              <div className="text-2xl font-bold text-white mt-1">
                {(result.compliance_typology.p_always_takers * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-blue-400/80 mt-0.5">
                ~{result.compliance_typology.always_taker_count_est} quan sát
              </div>
            </div>

            {/* Never-Takers */}
            <div className="bg-slate-800/40 border border-slate-700 rounded-lg p-3.5 relative overflow-hidden">
              <div className="text-xs text-slate-400 font-medium">Never-Takers</div>
              <div className="text-2xl font-bold text-white mt-1">
                {(result.compliance_typology.p_never_takers * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                ~{result.compliance_typology.never_taker_count_est} quan sát
              </div>
            </div>

            {/* Instrument F-Stat */}
            <div className={`p-3.5 rounded-lg border ${
              result.compliance_typology.weak_instrument
                ? 'bg-rose-950/20 border-rose-500/30'
                : 'bg-emerald-950/20 border-emerald-500/30'
            }`}>
              <div className="text-xs text-slate-400 font-medium">Độ Mạnh Công Cụ (Wald F)</div>
              <div className={`text-2xl font-bold mt-1 ${
                result.compliance_typology.weak_instrument ? 'text-rose-400' : 'text-emerald-400'
              }`}>
                {result.compliance_typology.first_stage_f.toFixed(2)}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                {result.compliance_typology.weak_instrument ? 'Cảnh báo: Yếu (F < 10)' : 'Đạt chuẩn Stock-Yogo (F ≥ 10)'}
              </div>
            </div>
          </div>

          {/* LATE Effect Summary (if outcome was provided) */}
          {result.late_causal_effect && (
            <div className="bg-gradient-to-r from-purple-950/30 via-slate-900 to-indigo-950/30 border border-purple-500/30 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-purple-400" />
                  <span className="text-sm font-bold text-white">
                    Local Average Treatment Effect (LATE) trên Compliers:
                  </span>
                  <span className="text-base font-extrabold text-purple-300">
                    τ = {result.late_causal_effect.late_estimate.toFixed(3)}
                  </span>
                  {result.late_causal_effect.is_significant && (
                    <span className="text-xs px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full font-semibold">
                      Ý nghĩa thống kê (p &lt; 0.05)
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400">
                  SE = {result.late_causal_effect.bootstrap_se.toFixed(3)} • 95% CI [{result.late_causal_effect.ci_95[0].toFixed(3)}, {result.late_causal_effect.ci_95[1].toFixed(3)}] • p = {result.late_causal_effect.p_value.toFixed(4)}
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs bg-slate-950/60 px-3 py-2 rounded-lg border border-purple-500/20">
                <div>
                  <span className="text-slate-400">E[Y(1)|C]: </span>
                  <span className="font-bold text-emerald-400">{result.late_causal_effect.complier_treated_mean_ey1.toFixed(3)}</span>
                </div>
                <div className="border-l border-slate-700 pl-4">
                  <span className="text-slate-400">E[Y(0)|C]: </span>
                  <span className="font-bold text-rose-400">{result.late_causal_effect.complier_control_mean_ey0.toFixed(3)}</span>
                </div>
              </div>
            </div>
          )}

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
              onClick={() => setActiveTab('overview')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'overview'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <PieChart className="w-3.5 h-3.5" />
              Tổng Quan Typology
            </button>
            <button
              onClick={() => setActiveTab('profiles')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'profiles'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Chi Tiết Hồ Sơ Complier ({result.feature_profiles.length} biến)
            </button>
            <button
              onClick={() => setActiveTab('apa')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'apa'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Copy className="w-3.5 h-3.5" />
              Báo Cáo APA 7th
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-4 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2">
                  <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Nhóm Compliers (Tuân thủ)
                  </div>
                  <p className="text-slate-400">
                    Đối tượng chỉ tiếp nhận can thiệp khi được khuyến khích ($D(1) = 1, D(0) = 0$). Đây là phân lớp duy nhất xác định được hiệu ứng nhân quả LATE của công cụ.
                  </p>
                </div>
                <div className="p-4 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2">
                  <div className="font-semibold text-blue-400 flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4" />
                    Nhóm Always-Takers (Luôn tiếp nhận)
                  </div>
                  <p className="text-slate-400">
                    Đối tượng sẽ luôn tiếp nhận can thiệp bất kể có nhận được khuyến khích hay không ($D(1) = 1, D(0) = 1$).
                  </p>
                </div>
                <div className="p-4 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2">
                  <div className="font-semibold text-slate-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    Nhóm Never-Takers (Không tiếp nhận)
                  </div>
                  <p className="text-slate-400">
                    Đối tượng không bao giờ tiếp nhận can thiệp dù được khuyến khích tối đa ($D(1) = 0, D(0) = 0$).
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'profiles' && (
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 text-slate-300 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Biến / Đặc trưng X</th>
                    <th className="px-4 py-3 text-right">Trung bình Tổng thể (Pop)</th>
                    <th className="px-4 py-3 text-right">Trung bình Complier (κ-Weight)</th>
                    <th className="px-4 py-3 text-center">Tỷ Lệ Tương Đối (Ratio)</th>
                    <th className="px-4 py-3 text-right">95% CI Bootstrap</th>
                    <th className="px-4 py-3">Phân loại Đại diện</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                  {result.feature_profiles.map((f, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-2.5 font-medium text-slate-200">{f.feature_name}</td>
                      <td className="px-4 py-2.5 text-right text-slate-400">{f.population_mean.toFixed(3)}</td>
                      <td className="px-4 py-2.5 text-right font-semibold text-emerald-400">{f.complier_mean.toFixed(3)}</td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={`px-2 py-0.5 rounded font-bold ${
                          f.relative_likelihood_ratio > 1.15
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : f.relative_likelihood_ratio < 0.85
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : 'bg-slate-800 text-slate-300'
                        }`}>
                          {f.relative_likelihood_ratio.toFixed(2)}x
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-right text-slate-400">
                        [{f.ci_95[0].toFixed(3)}, {f.ci_95[1].toFixed(3)}]
                      </td>
                      <td className="px-4 py-2.5 text-slate-300">{f.representation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
