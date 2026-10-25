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
  EyeOff,
  Lock,
  Flame,
  Scale,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import {
  RandomizedResponseRequest,
  RandomizedResponseResult
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const RandomizedResponseCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [rrtQuestionId, setRrtQuestionId] = useState<string>('');
  const [modelType, setModelType] = useState<'crosswise' | 'warner' | 'unrelated'>('crosswise');
  const [pRandomizer, setPRandomizer] = useState<number>(0.70);
  const [pUnrelated, setPUnrelated] = useState<number>(0.50);
  const [directQuestionId, setDirectQuestionId] = useState<string>('');
  const [covariateIds, setCovariateIds] = useState<string[]>([]);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RandomizedResponseResult | null>(null);
  const [activeTab, setActiveTab] = useState<'chart' | 'sdb' | 'logistic' | 'apa'>('chart');
  const [copied, setCopied] = useState<boolean>(false);

  const candidateQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider'
  );

  const handleToggleCovariate = (qid: string) => {
    if (covariateIds.includes(qid)) {
      setCovariateIds(covariateIds.filter((id) => id !== qid));
    } else {
      setCovariateIds([...covariateIds, qid]);
    }
  };

  const handleRun = async () => {
    if (!rrtQuestionId) {
      setError('Vui lòng chọn câu hỏi khảo sát ngẫu nhiên hóa (RRT Question).');
      return;
    }
    if (directQuestionId && directQuestionId === rrtQuestionId) {
      setError('Câu hỏi đối chứng trực tiếp không được trùng với câu hỏi RRT.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: RandomizedResponseRequest = {
      rrt_question_id: rrtQuestionId,
      model_type: modelType,
      p_randomizer: pRandomizer,
      p_unrelated: modelType === 'unrelated' ? pUnrelated : undefined,
      direct_question_id: directQuestionId || undefined,
      covariate_question_ids: covariateIds.length > 0 ? covariateIds : undefined,
      alpha,
      scope,
    };

    try {
      const data = await api.runRandomizedResponse(surveyId, payload);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi thực thi phân tích Randomized Response.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden mb-8">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 dark:border-slate-800 bg-gradient-to-r from-violet-50/50 via-purple-50/30 to-transparent dark:from-violet-950/20 dark:via-purple-950/10 dark:to-transparent">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-violet-600 text-white shadow-md shadow-violet-500/20">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Randomized Response Technique (RRT) & Crosswise Sensitive Item Prevalence Engine
                </h3>
                <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-violet-100 text-violet-800 dark:bg-violet-900/50 dark:text-violet-300 border border-violet-200 dark:border-violet-800">
                  DataTrust Iteration 193
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Ước lượng tỷ lệ vi phạm, gian lận và hành vi nhạy cảm bảo vệ tuyệt đối quyền riêng tư (Warner 1965; Yu et al. 2008; Jann et al. 2012) và đo lường khoảng cách Social Desirability Bias (SDB)
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Configuration Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 p-5 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
          {/* RRT Question */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Câu Hỏi Nhạy Cảm Ngẫu Nhiên Hóa (RRT Item) *
            </label>
            <select
              value={rrtQuestionId}
              onChange={(e) => setRrtQuestionId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-violet-500"
            >
              <option value="">-- Chọn câu hỏi RRT (0/1) --</option>
              {candidateQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          {/* Model Type */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Mô Hình Kỹ Thuật (RRT Model)
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value as any)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-violet-500"
            >
              <option value="crosswise">Mô hình Crosswise (Yu et al. 2008; Jann 2012 - Khuyên dùng)</option>
              <option value="warner">Mô hình Warner (1965) Cổ Điển</option>
              <option value="unrelated">Mô hình Câu Hỏi Không Liên Quan (Horvitz-Simmons 1967)</option>
            </select>
          </div>

          {/* Probability p */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Xác Suất Ngẫu Nhiên Hóa (p)
            </label>
            <select
              value={pRandomizer}
              onChange={(e) => setPRandomizer(parseFloat(e.target.value))}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-violet-500"
            >
              <option value="0.70">p = 0.70 (Khuyên dùng cho Crosswise: Cân bằng bảo mật & chính xác)</option>
              <option value="0.75">p = 0.75 (Chính xác thống kê cao hơn, VIF = 4.0x)</option>
              <option value="0.80">p = 0.80 (Phương sai thấp hơn, VIF = 2.78x)</option>
              <option value="0.65">p = 0.65 (Bảo mật riêng tư tối đa, VIF = 11.1x)</option>
            </select>
          </div>

          {/* Direct Benchmark Question (Optional) */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Câu Hỏi Đối Chứng Trực Tiếp (Direct Question) (Tùy chọn)
            </label>
            <select
              value={directQuestionId}
              onChange={(e) => setDirectQuestionId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-violet-500"
            >
              <option value="">-- Không có (Chỉ ước lượng RRT) --</option>
              {candidateQuestions
                .filter((q) => q.id !== rrtQuestionId)
                .map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.title}
                  </option>
                ))}
            </select>
            <p className="text-[11px] text-slate-500 mt-1">
              Dùng để tính Social Desirability Bias gap: \Delta_SDB = \pi_RRT - \pi_Direct
            </p>
          </div>

          {/* Covariates Multi-selector */}
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
              Biến Nhân Khẩu Học & Dự Báo (RRT Logistic Regression Covariates) (Tùy chọn)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {candidateQuestions
                .filter((q) => q.id !== rrtQuestionId && q.id !== directQuestionId)
                .map((q) => {
                  const isChecked = covariateIds.includes(q.id);
                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => handleToggleCovariate(q.id)}
                      className={`text-left px-3 py-2 rounded-lg text-xs font-medium border transition-colors flex items-center justify-between ${
                        isChecked
                          ? 'bg-violet-50 border-violet-500 text-violet-800 dark:bg-violet-950/40 dark:border-violet-600 dark:text-violet-300'
                          : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span className="truncate pr-2">{q.title}</span>
                      {isChecked && <Check className="w-3.5 h-3.5 text-violet-600 dark:text-violet-400 shrink-0" />}
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Scope and Action */}
          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Phạm vi:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2.5 py-1.5 text-slate-800 dark:text-slate-200"
            >
              <option value="all">Tất cả người trả lời</option>
              <option value="verified_clean">Chỉ mẫu Verified Clean</option>
            </select>
          </div>

          <div className="md:col-span-2 flex justify-end items-center gap-3">
            <button
              onClick={handleRun}
              disabled={loading || !rrtQuestionId}
              className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-semibold text-sm shadow-md shadow-violet-500/20 flex items-center gap-2 transition-all"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Đang khử chệch SDB...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Ước Lượng Tỷ Lệ Nhạy Cảm (RRT)</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-400 flex items-center gap-3 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results View */}
        {result && (
          <div className="space-y-6">
            {/* KPI Stat Ribbon */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Cỡ Mẫu Khảo Sát</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  N = {result.sample_size}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  p = {result.randomization_probability.toFixed(2)} ({result.model_type})
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Khẳng Định Thô (\lambda)</span>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1 font-mono">
                  {(result.observed_affirmative_rate * 100).toFixed(1)}%
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Tỷ lệ trả lời 1 trên bảng hỏi
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Hiện Nhiễm Thật (\pi)</span>
                <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                  {(result.estimated_prevalence * 100).toFixed(1)}%
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  95% CI: [{(result.ci_95[0] * 100).toFixed(1)}%, {(result.ci_95[1] * 100).toFixed(1)}%]
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Khoảng Cách SDB (\Delta)</span>
                <div className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                  {result.social_desirability_diagnostics
                    ? `${result.social_desirability_diagnostics.sdb_gap_percentage_points > 0 ? '+' : ''}${result.social_desirability_diagnostics.sdb_gap_percentage_points.toFixed(1)}%`
                    : 'N/A'}
                </div>
                <div className="text-[11px] mt-0.5">
                  {result.social_desirability_diagnostics?.significant_underreporting ? (
                    <span className="text-red-600 dark:text-red-400 font-medium">Under-reporting p &lt; 0.05</span>
                  ) : (
                    <span className="text-slate-500">Chưa đối chứng</span>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 col-span-2 sm:col-span-4 lg:col-span-1">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Bảo Vệ Riêng Tư</span>
                <div className="text-sm font-bold text-violet-600 dark:text-violet-400 mt-1">
                  VIF: {result.variance_inflation_factor.toFixed(1)}x
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Không thể truy ngược cá nhân
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-700 space-x-4">
              <button
                onClick={() => setActiveTab('chart')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'chart'
                    ? 'border-violet-600 text-violet-700 dark:text-violet-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span>Biểu Đồ Trực Quan Hóa (Dual-Panel)</span>
              </button>
              <button
                onClick={() => setActiveTab('sdb')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'sdb'
                    ? 'border-violet-600 text-violet-700 dark:text-violet-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <Scale className="w-4 h-4" />
                <span>Chẩn Đoán Sai Lệch Mong Muốn Xã Hội (SDB)</span>
              </button>
              {result.rrt_logistic_regression && (
                <button
                  onClick={() => setActiveTab('logistic')}
                  className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'logistic'
                      ? 'border-violet-600 text-violet-700 dark:text-violet-400'
                      : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                  }`}
                >
                  <Activity className="w-4 h-4" />
                  <span>Hồi Quy Logistic RRT</span>
                </button>
              )}
              <button
                onClick={() => setActiveTab('apa')}
                className={`pb-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'apa'
                    ? 'border-violet-600 text-violet-700 dark:text-violet-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Báo Cáo Học Thuật APA 7th</span>
              </button>
            </div>

            {/* Tab 1: Vector Visualizer */}
            {activeTab === 'chart' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 overflow-x-auto shadow-inner">
                  <div
                    className="w-full flex justify-center"
                    dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                  />
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic">
                  * Panel A minh họa tỷ lệ hiện nhiễm thực tế đã khử chệch (\pi) so với báo cáo trực tiếp. Panel B biểu diễn đường cong đánh đổi giữa mức độ bảo vệ quyền riêng tư và hệ số phóng đại phương sai (VIF) theo tham số ngẫu nhiên hóa p.
                </div>
              </div>
            )}

            {/* Tab 2: SDB Diagnostics */}
            {activeTab === 'sdb' && (
              <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 space-y-4">
                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Đo Lường Khoảng Cách Gian Lận / Né Tránh (Social Desirability Bias Gap)
                </h4>
                {result.social_desirability_diagnostics ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-2">
                      <div className="text-xs text-slate-500">So Sánh Tỷ Lệ Thừa Nhận</div>
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span>Hỏi trực tiếp (Direct):</span>
                        <span className="font-mono text-red-600">{(result.social_desirability_diagnostics.direct_prevalence * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span>Ngẫu nhiên hóa (RRT):</span>
                        <span className="font-mono text-emerald-600">{(result.estimated_prevalence * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center text-sm font-bold pt-2 border-t border-slate-200 dark:border-slate-700">
                        <span>Khoảng chênh lệch (SDB Gap):</span>
                        <span className="font-mono text-amber-600">+{result.social_desirability_diagnostics.sdb_gap_percentage_points.toFixed(1)}% điểm</span>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-2 text-xs">
                      <div className="text-slate-500 font-semibold">Kiểm Định Thống Kê Under-Reporting</div>
                      <div className="flex justify-between">
                        <span>Z-Statistic:</span>
                        <span className="font-mono font-bold">{result.social_desirability_diagnostics.z_statistic.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>P-Value (1-sided):</span>
                        <span className="font-mono">{result.social_desirability_diagnostics.p_value_underreporting.toFixed(4)}</span>
                      </div>
                      <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                        {result.social_desirability_diagnostics.significant_underreporting ? (
                          <span className="text-red-600 dark:text-red-400 font-semibold">
                            Phát hiện hiện tượng che giấu/né tránh có ý nghĩa thống kê (p &lt; 0.05). Hỏi trực tiếp làm giảm nghiêm trọng tính trung thực của khảo sát.
                          </span>
                        ) : (
                          <span className="text-slate-600 dark:text-slate-300">
                            Không có bằng chứng thống kê rõ rệt về sai lệch che giấu ở mức ý nghĩa 5%.
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    Chưa chọn câu hỏi đối chứng trực tiếp. Hãy chọn một câu hỏi đối chứng ở phần thiết lập để đo lường khoảng cách SDB.
                  </p>
                )}
              </div>
            )}

            {/* Tab 3: Logistic Regression */}
            {activeTab === 'logistic' && result.rrt_logistic_regression && (
              <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 uppercase font-bold border-b border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="py-3 px-4">Biến Số</th>
                      <th className="py-3 px-3 text-right">Hệ Số (\beta)</th>
                      <th className="py-3 px-3 text-right">Sai Số Chuẩn (SE)</th>
                      <th className="py-3 px-3 text-right">Z-Stat</th>
                      <th className="py-3 px-3 text-right">P-Value</th>
                      <th className="py-3 px-4 text-right">Tỷ Số Chênh (Odds Ratio)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {result.rrt_logistic_regression.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">{row.term}</td>
                        <td className="py-3 px-3 text-right font-mono">{row.coefficient.toFixed(4)}</td>
                        <td className="py-3 px-3 text-right font-mono text-slate-500">{row.std_error.toFixed(4)}</td>
                        <td className="py-3 px-3 text-right font-mono">{row.z_statistic.toFixed(2)}</td>
                        <td className="py-3 px-3 text-right font-mono">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[11px] ${
                              row.p_value < 0.05
                                ? 'bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300 font-bold'
                                : 'text-slate-500'
                            }`}
                          >
                            {row.p_value.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-violet-700 dark:text-violet-300">
                          {row.odds_ratio != null ? `${row.odds_ratio.toFixed(2)}x` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 4: APA Narrative */}
            {activeTab === 'apa' && (
              <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 relative">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Báo Cáo Học Thuật Chuẩn APA 7th Edition
                  </h4>
                  <button
                    onClick={handleCopyAPA}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 transition-colors flex items-center gap-1.5 text-xs font-medium"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-violet-600" />
                        <span className="text-violet-600 font-semibold">Đã copy</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy APA</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-serif">
                  {result.apa_narrative}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
