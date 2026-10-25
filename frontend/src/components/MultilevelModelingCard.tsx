import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  CheckCircle2,
  Copy,
  FolderGit2,
  GitBranch,
  HelpCircle,
  Info,
  Layers,
  LineChart,
  RefreshCw,
  Sliders,
  Sparkles,
  TrendingUp,
  Users
} from 'lucide-react';
import { api } from '../api/client';
import {
  MultilevelAnalysisResult,
  MultilevelClusterTrajectory
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface MultilevelModelingCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const MultilevelModelingCard: React.FC<MultilevelModelingCardProps> = ({ surveyId, questions }) => {
  const numericQuestions = questions.filter(q =>
    ['rating', 'linear_scale', 'nps', 'number', 'likert'].includes(q.question_type)
  );

  const clusterQuestions = questions.filter(q =>
    ['single_choice', 'dropdown', 'radio', 'text'].includes(q.question_type)
  );

  const [outcomeQId, setOutcomeQId] = useState<string>(numericQuestions[0]?.id || '');
  const [predictorQId, setPredictorQId] = useState<string>(numericQuestions[1]?.id || '');
  const [clusterQId, setClusterQId] = useState<string>(clusterQuestions[0]?.id || '');
  const [centering, setCentering] = useState<'grand_mean' | 'group_mean' | 'none'>('grand_mean');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'trajectories' | 'effects' | 'shrinkage'>('trajectories');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MultilevelAnalysisResult | null>(null);
  const [copied, setCopied] = useState(false);

  const handleRunAnalysis = async () => {
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả phụ thuộc (Y).');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runMultilevelAnalysis(surveyId, {
        outcome_question_id: outcomeQId,
        predictor_question_id: predictorQId || null,
        cluster_question_id: clusterQId || null,
        centering,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_CLUSTERS') {
        setError(res.message || 'Chưa đủ dữ liệu mẫu hoặc số cụm để phân tích đa cấp.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích mô hình đa cấp HLM.');
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
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
              <Layers className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-bold text-slate-800">
              Mô hình Tuyến tính Thứ bậc Đa cấp (Multilevel HLM / MLM)
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-indigo-100 text-indigo-700">
              Raudenbush & Bryk 2002
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Phân tích cấu trúc dữ liệu lồng ghép (người trả lời thuộc cụm địa bàn, trường học, điều tra viên). 
            Phân rã phương sai ICC, ước lượng hệ số chặn và độ dốc ngẫu nhiên (Random Intercepts & Slopes), 
            và co rút tham số Empirical Bayes (EB Shrinkage).
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading || !outcomeQId}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-semibold shadow-sm transition-all shadow-indigo-200"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Đang ước lượng HLM...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Ước lượng Mô hình Đa cấp
            </>
          )}
        </button>
      </div>

      {/* Parameter Controls */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 bg-slate-50/70 p-4 rounded-xl border border-slate-200/70">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Biến Phụ thuộc Y (Outcome) <span className="text-rose-500">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 30 ? q.title.slice(0, 30) + '...' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Biến Dự báo X (Predictor)
          </label>
          <select
            value={predictorQId}
            onChange={(e) => setPredictorQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Không chọn (Mô hình rỗng) --</option>
            {numericQuestions.filter(q => q.id !== outcomeQId).map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 30 ? q.title.slice(0, 30) + '...' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Biến Cụm Tầng 2 (Cluster / Group)
          </label>
          <select
            value={clusterQId}
            onChange={(e) => setClusterQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Mặc định (Điều tra viên / Nhóm) --</option>
            {clusterQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 30 ? q.title.slice(0, 30) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Chiến lược định tâm (Centering)
          </label>
          <select
            value={centering}
            onChange={(e) => setCentering(e.target.value as any)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="grand_mean">Định tâm tổng thể (Grand-Mean)</option>
            <option value="group_mean">Định tâm theo cụm (Group-Mean)</option>
            <option value="none">Giá trị thô (Raw / Uncentered)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Phạm vi dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Đã làm sạch chống gian lận (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Result presentation */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* ICC Card */}
            <div className="bg-gradient-to-br from-indigo-50/70 to-indigo-100/30 border border-indigo-200/80 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-700">Tương quan nội cụm (ICC)</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  result.null_model?.icc_tier === 'HIGH'
                    ? 'bg-rose-100 text-rose-700'
                    : result.null_model?.icc_tier === 'MODERATE'
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-emerald-100 text-emerald-700'
                }`}>
                  {result.null_model?.icc_label}
                </span>
              </div>
              <div className="text-2xl font-extrabold text-indigo-900 mt-2">
                {result.null_model?.icc !== undefined ? result.null_model.icc.toFixed(3) : '--'}
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                {result.null_model?.icc_percentage}% phương sai Y bắt nguồn từ dị biệt giữa các cụm
              </p>
            </div>

            {/* Sample & Clusters Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Quy mô mẫu & Cụm</span>
                <Users className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                N = {result.total_sample_size}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                J = {result.num_clusters} cụm (Cỡ cụm TB ñ = {result.average_cluster_size})
              </p>
            </div>

            {/* Snijders & Bosker R^2 Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Phương sai giải thích (R²)</span>
                <Award className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                {result.random_effects?.r2_level_1 !== undefined
                  ? `${(result.random_effects.r2_level_1 * 100).toFixed(1)}%`
                  : '--'}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                R² Tầng 1 (Cá nhân) | Tầng 2 (Cụm): {result.random_effects?.r2_level_2 !== undefined ? `${(result.random_effects.r2_level_2 * 100).toFixed(1)}%` : '--'}
              </p>
            </div>

            {/* Model Comparison LRT Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Kiểm định LRT (HLM vs OLS)</span>
                <GitBranch className="w-4 h-4 text-indigo-500" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                Δ-2LL = {result.model_comparison_ols_vs_hlm?.delta_deviance_chi2?.toFixed(2) || '--'}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                p = {result.model_comparison_ols_vs_hlm?.p_value?.toFixed(4) || '--'} {result.model_comparison_ols_vs_hlm?.is_hlm_significantly_better ? '(HLM vượt trội)' : '(Khác biệt không đáng kể)'}
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200">
            <button
              onClick={() => setActiveTab('trajectories')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'trajectories'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <LineChart className="w-3.5 h-3.5" />
              Đường Quỹ đạo Cụm (Trajectories)
            </button>
            <button
              onClick={() => setActiveTab('effects')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'effects'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              Hệ số Cố định & Ngẫu nhiên (Fixed & Random)
            </button>
            <button
              onClick={() => setActiveTab('shrinkage')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'shrinkage'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <FolderGit2 className="w-3.5 h-3.5" />
              Co rút Empirical Bayes (EB Shrinkage)
            </button>
          </div>

          {/* Tab 1: Cluster Trajectories Vector Visualizer */}
          {activeTab === 'trajectories' && (
            <div className="space-y-4">
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <div className="flex items-center justify-between mb-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-indigo-400"></span>
                    <span className="text-slate-200 font-semibold">
                      Quỹ đạo Tuyến tính của từng Cụm (Random Intercepts & Slopes)
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span className="inline-flex items-center gap-1">
                      <span className="w-3 h-0.5 border-t-2 border-dashed border-white"></span>
                      Đường trung bình tổng thể (Grand Mean)
                    </span>
                  </div>
                </div>

                <div className="relative w-full overflow-x-auto">
                  <svg
                    viewBox="0 0 600 320"
                    className="w-full h-72 rounded-lg bg-slate-950 shadow-inner"
                  >
                    {/* Grid lines */}
                    <line x1="60" y1="20" x2="60" y2="270" stroke="#334155" strokeWidth="1" />
                    <line x1="60" y1="270" x2="570" y2="270" stroke="#334155" strokeWidth="1" />
                    <line x1="60" y1="20" x2="570" y2="20" stroke="#1e293b" strokeDasharray="3 3" />
                    <line x1="60" y1="82" x2="570" y2="82" stroke="#1e293b" strokeDasharray="3 3" />
                    <line x1="60" y1="145" x2="570" y2="145" stroke="#1e293b" strokeDasharray="3 3" />
                    <line x1="60" y1="207" x2="570" y2="207" stroke="#1e293b" strokeDasharray="3 3" />

                    {/* Axis Labels */}
                    <text x="315" y="305" fill="#94a3b8" fontSize="11" textAnchor="middle">
                      Biến Dự báo X (Predictor)
                    </text>
                    <text
                      x="20"
                      y="150"
                      fill="#94a3b8"
                      fontSize="11"
                      textAnchor="middle"
                      transform="rotate(-90 20 150)"
                    >
                      Biến Phụ thuộc Y (Outcome)
                    </text>

                    {/* Cluster Trajectory Paths */}
                    {result.cluster_trajectories?.map((ct) => (
                      <path
                        key={ct.cluster_id}
                        d={ct.svg_path}
                        fill="none"
                        stroke={ct.color}
                        strokeWidth="2.5"
                        strokeOpacity="0.85"
                      />
                    ))}

                    {/* Grand Trajectory Path */}
                    {result.grand_trajectory_path && (
                      <path
                        d={result.grand_trajectory_path}
                        fill="none"
                        stroke="#ffffff"
                        strokeWidth="3.5"
                        strokeDasharray="6 4"
                      />
                    )}
                  </svg>
                </div>

                {/* Cluster Legend */}
                <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-slate-800">
                  {result.cluster_trajectories?.map((ct) => (
                    <div
                      key={ct.cluster_id}
                      className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/80 rounded-lg text-xs"
                    >
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: ct.color }}
                      ></span>
                      <span className="text-slate-200 font-medium">{ct.cluster_id}</span>
                      <span className="text-slate-400 text-[10px]">(n={ct.n_j})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Fixed and Random Effects Tables */}
          {activeTab === 'effects' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Fixed Effects */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
                  <h4 className="text-xs font-bold text-slate-800">
                    Hệ số Cố định (Fixed Effects - Level 1 & 2)
                  </h4>
                </div>
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2 px-3">Tham số</th>
                      <th className="py-2 px-3">Hệ số (γ)</th>
                      <th className="py-2 px-3">Sai số SE</th>
                      <th className="py-2 px-3">t-ratio</th>
                      <th className="py-2 px-3">p-value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    <tr>
                      <td className="py-2 px-3 font-medium">Hệ số chặn (γ₀₀)</td>
                      <td className="py-2 px-3 font-semibold text-slate-900">
                        {result.fixed_effects?.intercept_gamma_00?.toFixed(3)}
                      </td>
                      <td className="py-2 px-3">{result.fixed_effects?.se_gamma_00?.toFixed(3)}</td>
                      <td className="py-2 px-3">{result.fixed_effects?.t_gamma_00?.toFixed(2)}</td>
                      <td className="py-2 px-3">
                        <span className="font-semibold text-indigo-600">
                          {result.fixed_effects?.p_gamma_00?.toFixed(4)}
                        </span>
                      </td>
                    </tr>
                    {result.fixed_effects?.slope_gamma_10 !== null &&
                      result.fixed_effects?.slope_gamma_10 !== undefined && (
                        <tr>
                          <td className="py-2 px-3 font-medium">Độ dốc (γ₁₀)</td>
                          <td className="py-2 px-3 font-semibold text-slate-900">
                            {result.fixed_effects.slope_gamma_10.toFixed(3)}
                          </td>
                          <td className="py-2 px-3">{result.fixed_effects.se_gamma_10?.toFixed(3)}</td>
                          <td className="py-2 px-3">{result.fixed_effects.t_gamma_10?.toFixed(2)}</td>
                          <td className="py-2 px-3">
                            <span className="font-semibold text-indigo-600">
                              {result.fixed_effects.p_gamma_10?.toFixed(4)}
                            </span>
                          </td>
                        </tr>
                      )}
                  </tbody>
                </table>
              </div>

              {/* Random Effects */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
                  <h4 className="text-xs font-bold text-slate-800">
                    Thành phần Phương sai Ngẫu nhiên (Random Effects)
                  </h4>
                </div>
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2 px-3">Thành phần</th>
                      <th className="py-2 px-3">Ký hiệu</th>
                      <th className="py-2 px-3">Phương sai</th>
                      <th className="py-2 px-3">Độ lệch chuẩn (SD)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    <tr>
                      <td className="py-2 px-3 font-medium">Hệ số chặn tầng 2</td>
                      <td className="py-2 px-3">τ₀₀</td>
                      <td className="py-2 px-3 font-semibold text-slate-900">
                        {result.random_effects?.tau_00_intercept_var?.toFixed(4)}
                      </td>
                      <td className="py-2 px-3">
                        {result.random_effects?.tau_00_intercept_var !== undefined
                          ? Math.sqrt(result.random_effects.tau_00_intercept_var).toFixed(3)
                          : '--'}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-medium">Độ dốc tầng 2</td>
                      <td className="py-2 px-3">τ₁₁</td>
                      <td className="py-2 px-3 font-semibold text-slate-900">
                        {result.random_effects?.tau_11_slope_var?.toFixed(4)}
                      </td>
                      <td className="py-2 px-3">
                        {result.random_effects?.tau_11_slope_var !== undefined
                          ? Math.sqrt(result.random_effects.tau_11_slope_var).toFixed(3)
                          : '--'}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-medium">Phần dư tầng 1</td>
                      <td className="py-2 px-3">σ²</td>
                      <td className="py-2 px-3 font-semibold text-slate-900">
                        {result.random_effects?.sigma_sq_residual_var?.toFixed(4)}
                      </td>
                      <td className="py-2 px-3">
                        {result.random_effects?.sigma_sq_residual_var !== undefined
                          ? Math.sqrt(result.random_effects.sigma_sq_residual_var).toFixed(3)
                          : '--'}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 3: Empirical Bayes Shrinkage Table */}
          {activeTab === 'shrinkage' && (
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-800">
                    Ước lượng Co rút Bayes Thực nghiệm (Empirical Bayes Shrinkage Estimates)
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    Trọng số co rút λ càng thấp (cỡ mẫu nhỏ), ước lượng cụm càng được kéo về phía trung bình tổng thể γ₀₀.
                  </p>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Mã Cụm (Cluster)</th>
                      <th className="py-2.5 px-3">Mẫu n_j</th>
                      <th className="py-2.5 px-3">Trung bình thô Y</th>
                      <th className="py-2.5 px-3">EB Intercept (β̂₀ⱼ)</th>
                      <th className="py-2.5 px-3">EB Slope (β̂₁ⱼ)</th>
                      <th className="py-2.5 px-3">Độ tin cậy cụm (λ_j)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {result.cluster_trajectories?.map((ct) => (
                      <tr key={ct.cluster_id} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-semibold text-slate-900 flex items-center gap-1.5">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: ct.color }}
                          ></span>
                          {ct.cluster_id}
                        </td>
                        <td className="py-2 px-3">{ct.n_j}</td>
                        <td className="py-2 px-3">{ct.y_mean.toFixed(2)}</td>
                        <td className="py-2 px-3 font-semibold text-indigo-700">
                          {ct.eb_intercept.toFixed(3)}
                        </td>
                        <td className="py-2 px-3 text-slate-800">{ct.eb_slope.toFixed(3)}</td>
                        <td className="py-2 px-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-indigo-600 h-1.5 rounded-full"
                                style={{ width: `${ct.shrinkage_weight * 100}%` }}
                              ></div>
                            </div>
                            <span className="font-mono text-[10px] text-slate-600">
                              {(ct.shrinkage_weight * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-indigo-50/40 border border-indigo-100 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative || '')}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-white hover:bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-lg text-xs font-semibold shadow-xs transition-all"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Đã sao chép!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA 7th
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic bg-white/80 p-3 rounded-lg border border-indigo-100">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
