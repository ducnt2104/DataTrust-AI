import React, { useState } from 'react';
import {
  Layers,
  BarChart3,
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  Activity,
  Sliders,
  Sparkles,
  HelpCircle,
  GitCommit,
  Users,
  Compass,
  Zap,
  Target
} from 'lucide-react';
import { api } from '../api/client';
import {
  MELSMAnalysisRequest,
  MELSMAnalysisResult
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const MELSMCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [subjectQuestionId, setSubjectQuestionId] = useState<string>('');
  const [outcomeQuestionId, setOutcomeQuestionId] = useState<string>('');
  const [locationCovariateIds, setLocationCovariateIds] = useState<string[]>([]);
  const [scaleCovariateIds, setScaleCovariateIds] = useState<string[]>([]);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MELSMAnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<'charts' | 'models' | 'typology' | 'apa'>('charts');
  const [copied, setCopied] = useState<boolean>(false);

  const candidateQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'text'
  );

  const handleToggleLocCovariate = (qid: string) => {
    if (locationCovariateIds.includes(qid)) {
      setLocationCovariateIds(locationCovariateIds.filter((id) => id !== qid));
    } else {
      setLocationCovariateIds([...locationCovariateIds, qid]);
    }
  };

  const handleToggleScaleCovariate = (qid: string) => {
    if (scaleCovariateIds.includes(qid)) {
      setScaleCovariateIds(scaleCovariateIds.filter((id) => id !== qid));
    } else {
      setScaleCovariateIds([...scaleCovariateIds, qid]);
    }
  };

  const handleRun = async () => {
    if (!subjectQuestionId) {
      setError('Vui lòng chọn biến định danh đối tượng (Subject ID / Cluster ID).');
      return;
    }
    if (!outcomeQuestionId) {
      setError('Vui lòng chọn biến kết quả liên tục (Outcome Question y_ij).');
      return;
    }
    if (subjectQuestionId === outcomeQuestionId) {
      setError('Biến định danh đối tượng không được trùng với biến kết quả.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: MELSMAnalysisRequest = {
      subject_question_id: subjectQuestionId,
      outcome_question_id: outcomeQuestionId,
      location_covariate_ids: locationCovariateIds.length > 0 ? locationCovariateIds : undefined,
      scale_covariate_ids: scaleCovariateIds.length > 0 ? scaleCovariateIds : undefined,
      alpha,
      scope,
    };

    try {
      const data = await api.runMELSM(surveyId, payload);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi thực thi phân tích mô hình MELSM.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Mô Hình Vị Trí & Quy Mô Hỗn Hợp (MELSM)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">
                  Hedeker et al. (2008, 2012)
                </span>
              </h2>
              <p className="text-sm text-slate-400 mt-0.5">
                Đồng thời mô hình hóa điểm trung bình (Location) và phương sai biến động nội tại (Within-Person Scale) của người trả lời
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-3 py-1 bg-slate-800 border border-slate-700/60 rounded-lg text-slate-300 font-mono">
            Iteration 194
          </span>
        </div>
      </div>

      {/* Control Panel */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Subject ID Question */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            Biến Đối Tượng / Respondent ID *
          </label>
          <select
            value={subjectQuestionId}
            onChange={(e) => setSubjectQuestionId(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
          >
            <option value="">-- Chọn biến đối tượng (Cluster) --</option>
            {candidateQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Định danh các lần đánh giá lặp lại của cùng 1 người</p>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            Biến Kết Quả Đánh Giá (y_ij) *
          </label>
          <select
            value={outcomeQuestionId}
            onChange={(e) => setOutcomeQuestionId(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
          >
            <option value="">-- Chọn biến kết quả liên tục --</option>
            {candidateQuestions
              .filter((q) => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'slider')
              .map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">Điểm số liên tục đo lường qua các thời điểm</p>
        </div>

        {/* Alpha & Scope */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-amber-400" />
            Mức Ý Nghĩa (&alpha;) &amp; Lọc Dữ Liệu
          </label>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={alpha}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value={0.01}>1% (99% CI)</option>
              <option value={0.05}>5% (95% CI)</option>
              <option value={0.10}>10% (90% CI)</option>
            </select>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="all">Toàn bộ mẫu</option>
              <option value="verified_clean">Mẫu sạch</option>
            </select>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Độ tin cậy kiểm định Likelihood Ratio</p>
        </div>

        {/* Action Button */}
        <div className="flex flex-col justify-end">
          <button
            onClick={handleRun}
            disabled={loading || !subjectQuestionId || !outcomeQuestionId}
            className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white font-medium px-4 py-2.5 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 transition-all duration-200"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Đang Ước Lượng...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-indigo-200" />
                <span>Chạy Phân Tích MELSM</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Covariates Multi-Select Expanders */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-800/60">
        {/* Location Covariates */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
            Biến Giải Thích Vị Trí (Location Predictors X)
          </label>
          <p className="text-[11px] text-slate-500 mb-2">Các biến tác động làm thay đổi điểm trung bình đánh giá</p>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto p-1.5 bg-slate-800/40 border border-slate-700/50 rounded-xl">
            {candidateQuestions
              .filter((q) => q.id !== subjectQuestionId && q.id !== outcomeQuestionId)
              .map((q) => {
                const isSelected = locationCovariateIds.includes(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => handleToggleLocCovariate(q.id)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-sky-500/20 border-sky-500/50 text-sky-200 font-medium'
                        : 'bg-slate-800 border-slate-700/60 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    {isSelected ? '✓ ' : '+ '}
                    {q.title}
                  </button>
                );
              })}
          </div>
        </div>

        {/* Scale Covariates */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            Biến Giải Thích Quy Mô (Scale Predictors W)
          </label>
          <p className="text-[11px] text-slate-500 mb-2">Các biến tác động làm thay đổi độ ổn định / phương sai sai số</p>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto p-1.5 bg-slate-800/40 border border-slate-700/50 rounded-xl">
            {candidateQuestions
              .filter((q) => q.id !== subjectQuestionId && q.id !== outcomeQuestionId)
              .map((q) => {
                const isSelected = scaleCovariateIds.includes(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => handleToggleScaleCovariate(q.id)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-purple-500/20 border-purple-500/50 text-purple-200 font-medium'
                        : 'bg-slate-800 border-slate-700/60 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    {isSelected ? '✓ ' : '+ '}
                    {q.title}
                  </button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mt-4 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-semibold text-rose-300">Không thể ước lượng MELSM</div>
            <div className="text-xs text-rose-400/90 mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && result.status === 'success' && (
        <div className="mt-6 space-y-6">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {/* KPI 1: Samples & Subjects */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 flex items-center gap-1.5 font-medium">
                <Users className="w-3.5 h-3.5 text-indigo-400" />
                Mẫu &amp; Đối Tượng
              </span>
              <div className="text-xl font-bold text-white mt-1">
                N={result.sample_size_total} <span className="text-xs text-indigo-400 font-normal">(J={result.sample_size_subjects})</span>
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">
                {(result.sample_size_total / result.sample_size_subjects).toFixed(1)} lần lặp / người
              </p>
            </div>

            {/* KPI 2: Fixed Location Intercept */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 flex items-center gap-1.5 font-medium">
                <Target className="w-3.5 h-3.5 text-sky-400" />
                Điểm Mean Cố Định (&beta;₀)
              </span>
              <div className="text-xl font-bold text-sky-300 mt-1 font-mono">
                {result.location_fixed_effects[0]?.coefficient?.toFixed(3) ?? '-'}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">
                SE = {result.location_fixed_effects[0]?.std_error?.toFixed(3)}
              </p>
            </div>

            {/* KPI 3: Random Location SD */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 flex items-center gap-1.5 font-medium">
                <Compass className="w-3.5 h-3.5 text-emerald-400" />
                Vị Trí Giữa Các Người (&sigma;ᵤ)
              </span>
              <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">
                {result.random_effects_variance_components.between_subject_mean_sd_sigma_u.toFixed(3)}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">Độ phân tán mức trung bình</p>
            </div>

            {/* KPI 4: Random Scale Volatility */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 flex items-center gap-1.5 font-medium">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Biến Động Nội Tại (&sigma;<sub>&omega;</sub>)
              </span>
              <div className="text-xl font-bold text-amber-300 mt-1 font-mono flex items-center gap-1.5">
                {result.random_effects_variance_components.between_subject_scale_sd_sigma_omega.toFixed(3)}
                {result.scale_heterogeneity_test.heterogeneity_significant && (
                  <span className="text-[10px] px-1.5 py-0.2 bg-amber-500/20 text-amber-300 rounded border border-amber-500/40">
                    p&lt;0.05
                  </span>
                )}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">
                LRT &chi;&sup2; = {result.scale_heterogeneity_test.lrt_statistic.toFixed(2)}
              </p>
            </div>

            {/* KPI 5: Location-Scale Correlation */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 flex items-center gap-1.5 font-medium">
                <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
                Tương Quan Vị Trí - Quy Mô (&rho;)
              </span>
              <div className={`text-xl font-bold mt-1 font-mono ${
                result.random_effects_variance_components.location_scale_correlation_rho >= 0 ? 'text-rose-400' : 'text-emerald-400'
              }`}>
                {result.random_effects_variance_components.location_scale_correlation_rho >= 0 ? '+' : ''}
                {result.random_effects_variance_components.location_scale_correlation_rho.toFixed(3)}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">
                {result.random_effects_variance_components.location_scale_correlation_rho < 0
                  ? 'Điểm cao ít biến động hơn'
                  : 'Điểm cao biến động mạnh hơn'}
              </p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('charts')}
              className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'charts'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Biểu Đồ Hai Chiều &amp; Phân Nhóm (SVG)
            </button>
            <button
              onClick={() => setActiveTab('models')}
              className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'models'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Layers className="w-4 h-4" />
              Bảng Hồi Quy Vị Trí &amp; Quy Mô
            </button>
            <button
              onClick={() => setActiveTab('typology')}
              className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'typology'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Compass className="w-4 h-4" />
              Phân Loại Tính Nhất Quán (Typology)
            </button>
            <button
              onClick={() => setActiveTab('apa')}
              className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'apa'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Copy className="w-4 h-4" />
              Báo Cáo Học Thuật APA 7th
            </button>
          </div>

          {/* Tab 1: Charts (SVG) */}
          {activeTab === 'charts' && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl overflow-x-auto flex justify-center">
                <div
                  className="w-full max-w-4xl"
                  dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-400 bg-slate-800/30 p-3.5 rounded-xl border border-slate-800">
                <div>
                  <strong className="text-slate-200">Panel A: Phân Phối Hai Chiều Empirical Bayes (EB):</strong> Mỗi chấm tròn tương ứng với 1 đối tượng, biểu diễn mối tương quan giữa điểm hài lòng trung bình (u<sub>i</sub>) và độ rung lắc/biến động phương sai nội tại (&omega;<sub>i</sub>).
                </div>
                <div>
                  <strong className="text-slate-200">Panel B: Phân Tầng 4 Góc Phần Tư:</strong> Phân chia tập khách hàng/người khảo sát thành 4 phân khúc chiến lược (Cao/Thấp &times; Ổn Định/Biến Động) để đưa ra hành động quản trị tối ưu.
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Fixed Effects Tables */}
          {activeTab === 'models' && (
            <div className="space-y-6">
              {/* Location Sub-Model */}
              <div>
                <h3 className="text-sm font-semibold text-sky-400 mb-2 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Mô Hình Vị Trí (Location Sub-Model) — Dự Báo Điểm Trung Bình &beta;
                </h3>
                <div className="overflow-x-auto border border-slate-800 rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800 text-slate-300">
                      <tr>
                        <th className="p-2.5">Tham Số (Predictor)</th>
                        <th className="p-2.5">Hệ Số (&beta;)</th>
                        <th className="p-2.5">Sai Số Chuẩn (SE)</th>
                        <th className="p-2.5">z-Statistic</th>
                        <th className="p-2.5">p-Value</th>
                        <th className="p-2.5">Khoảng Tin Cậy 95%</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {result.location_fixed_effects.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="p-2.5 font-medium text-white">{row.parameter}</td>
                          <td className="p-2.5 font-mono text-sky-300">{row.coefficient?.toFixed(4)}</td>
                          <td className="p-2.5 font-mono">{row.std_error.toFixed(4)}</td>
                          <td className="p-2.5 font-mono">{row.z_statistic.toFixed(3)}</td>
                          <td className="p-2.5 font-mono">
                            <span className={row.p_value < 0.05 ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                              {row.p_value < 0.0001 ? '<0.0001' : row.p_value.toFixed(4)}
                            </span>
                          </td>
                          <td className="p-2.5 font-mono text-slate-400">
                            [{row.ci_95[0].toFixed(3)}, {row.ci_95[1].toFixed(3)}]
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Scale Sub-Model */}
              <div>
                <h3 className="text-sm font-semibold text-purple-400 mb-2 flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Mô Hình Quy Mô (Scale Sub-Model) — Dự Báo Phương Sai Biến Động log(&sigma;&sup2;) &tau;
                </h3>
                <div className="overflow-x-auto border border-slate-800 rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800 text-slate-300">
                      <tr>
                        <th className="p-2.5">Tham Số (Predictor)</th>
                        <th className="p-2.5">Hệ Số log-Variance (&tau;)</th>
                        <th className="p-2.5">Tỷ Lệ Phương Sai exp(&tau;)</th>
                        <th className="p-2.5">Sai Số Chuẩn (SE)</th>
                        <th className="p-2.5">z-Statistic</th>
                        <th className="p-2.5">p-Value</th>
                        <th className="p-2.5">Khoảng Tin Cậy 95%</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {result.scale_fixed_effects.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="p-2.5 font-medium text-white">{row.parameter}</td>
                          <td className="p-2.5 font-mono text-purple-300">{row.coefficient_log_variance?.toFixed(4)}</td>
                          <td className="p-2.5 font-mono text-amber-300">
                            {row.variance_ratio != null ? `${row.variance_ratio.toFixed(2)}x` : '-'}
                          </td>
                          <td className="p-2.5 font-mono">{row.std_error.toFixed(4)}</td>
                          <td className="p-2.5 font-mono">{row.z_statistic.toFixed(3)}</td>
                          <td className="p-2.5 font-mono">
                            <span className={row.p_value < 0.05 ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                              {row.p_value < 0.0001 ? '<0.0001' : row.p_value.toFixed(4)}
                            </span>
                          </td>
                          <td className="p-2.5 font-mono text-slate-400">
                            [{row.ci_95[0].toFixed(3)}, {row.ci_95[1].toFixed(3)}]
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Typology Breakdown */}
          {activeTab === 'typology' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Quadrant 1: High/Stable */}
                <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-emerald-300 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      Cao - Ổn Định (High Mean / Stable)
                    </h4>
                    <span className="text-xl font-bold font-mono text-emerald-400">
                      {result.subject_consistency_typology.high_mean_stable}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
                    Nhóm khách hàng/đối tượng lý tưởng nhất: Có đánh giá tích cực liên tục và độ biến động cảm xúc rất thấp qua thời gian. Đây là tập hạt nhân trung thành.
                  </p>
                </div>

                {/* Quadrant 2: High/Volatile */}
                <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-amber-300 flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 text-amber-400" />
                      Cao - Biến Động (High Mean / Volatile)
                    </h4>
                    <span className="text-xl font-bold font-mono text-amber-400">
                      {result.subject_consistency_typology.high_mean_volatile}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
                    Điểm đánh giá trung bình cao nhưng mức độ rung lắc lớn. Nhóm này rất nhạy cảm với trải nghiệm từng phiên; một sự cố nhỏ có thể kéo tụt độ thỏa mãn.
                  </p>
                </div>

                {/* Quadrant 3: Low/Stable */}
                <div className="bg-sky-950/20 border border-sky-500/30 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-sky-300 flex items-center gap-1.5">
                      <Target className="w-4 h-4 text-sky-400" />
                      Thấp - Ổn Định (Low Mean / Stable)
                    </h4>
                    <span className="text-xl font-bold font-mono text-sky-400">
                      {result.subject_consistency_typology.low_mean_stable}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
                    Đánh giá thấp nhưng cực kỳ kiên định. Đây là nhóm có định kiến cố hữu hoặc gặp lỗi trải nghiệm mang tính hệ thống kéo dài, cần can thiệp giải pháp triệt để.
                  </p>
                </div>

                {/* Quadrant 4: Low/Volatile */}
                <div className="bg-rose-950/20 border border-rose-500/30 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-rose-300 flex items-center gap-1.5">
                      <Zap className="w-4 h-4 text-rose-400" />
                      Thấp - Biến Động (Low Mean / Volatile)
                    </h4>
                    <span className="text-xl font-bold font-mono text-rose-400">
                      {result.subject_consistency_typology.low_mean_volatile}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
                    Nhóm báo động đỏ cao nhất: Vừa có điểm trung bình thấp, vừa có tâm lý bấp bênh và bức xúc bất thường. Có nguy cơ rời bỏ dịch vụ hoặc lan truyền tiêu cực ngay lập tức.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: APA 7th Academic Narrative */}
          {activeTab === 'apa' && (
            <div className="space-y-4">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 relative">
                <button
                  onClick={() => copyToClipboard(result.apa_narrative)}
                  className="absolute top-3 right-3 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg flex items-center gap-1.5 border border-slate-700 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Đã chép</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép APA</span>
                    </>
                  )}
                </button>
                <div className="text-xs font-semibold text-indigo-400 mb-2">
                  Bản Thảo Báo Cáo Học Thuật (APA 7th Edition Format):
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-serif pr-20">
                  {result.apa_narrative}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
