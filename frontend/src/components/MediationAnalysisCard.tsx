import React, { useState, useEffect } from 'react';
import {
  GitMerge, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  TrendingUp, Activity, Copy, Check, RefreshCw, BarChart2,
  HelpCircle, BookOpen, Layers, ShieldCheck, Zap, Info
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, MediationAnalysisResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const MediationAnalysisCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc các câu hỏi định lượng (number, rating, nps, likert, linear_scale)
  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  const [xId, setXId] = useState<string>('');
  const [mId, setMId] = useState<string>('');
  const [yId, setYId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [bootSamples, setBootSamples] = useState<number>(1000);

  const [result, setResult] = useState<MediationAnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'diagram' | 'steps' | 'tests'>('diagram');

  // Khởi tạo mặc định 3 câu hỏi đầu tiên
  useEffect(() => {
    if (eligibleQuestions.length >= 3) {
      if (!xId || !eligibleQuestions.some(q => q.question_id === xId)) {
        setXId(eligibleQuestions[0].question_id);
      }
      if (!mId || mId === eligibleQuestions[0].question_id || !eligibleQuestions.some(q => q.question_id === mId)) {
        setMId(eligibleQuestions[1].question_id);
      }
      if (!yId || yId === eligibleQuestions[0].question_id || yId === eligibleQuestions[1].question_id || !eligibleQuestions.some(q => q.question_id === yId)) {
        setYId(eligibleQuestions[2].question_id);
      }
    }
  }, [questions]);

  const handleRunAnalysis = async () => {
    if (!xId || !mId || !yId) {
      setError('Vui lòng chọn đầy đủ 3 biến: Biến độc lập (X), Biến trung gian (M) và Biến phụ thuộc (Y).');
      return;
    }
    if (new Set([xId, mId, yId]).size < 3) {
      setError('Ba biến được chọn phải là 3 câu hỏi hoàn toàn phân biệt.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runMediationAnalysis(surveyId, {
        x_question_id: xId,
        m_question_id: mId,
        y_question_id: yId,
        scope,
        bootstrap_samples: bootSamples
      });
      setResult(res);
      if (res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Cỡ mẫu chưa đủ N >= 10 để chạy phân tích tác động trung gian.');
      } else if (res.status === 'ERROR') {
        setError(res.message || 'Không thể tính toán mô hình trung gian.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lỗi khi gọi API phân tích tác động trung gian.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!result?.conclusion?.apa_narrative) return;
    navigator.clipboard.writeText(result.conclusion.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const getMediationBadge = (type?: string) => {
    switch (type) {
      case 'FULL_MEDIATION':
        return {
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800',
          dot: 'bg-emerald-500',
          title: 'Trung gian toàn phần (Full Mediation)'
        };
      case 'COMPLEMENTARY_PARTIAL_MEDIATION':
        return {
          bg: 'bg-purple-50 text-purple-800 border-purple-300 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800',
          dot: 'bg-purple-500',
          title: 'Trung gian một phần tương hỗ (Complementary)'
        };
      case 'COMPETITIVE_PARTIAL_MEDIATION':
        return {
          bg: 'bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800',
          dot: 'bg-amber-500',
          title: 'Trung gian một phần triệt tiêu (Competitive Suppressor)'
        };
      case 'DIRECT_ONLY':
        return {
          bg: 'bg-blue-50 text-blue-800 border-blue-300 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800',
          dot: 'bg-blue-500',
          title: 'Chỉ có tác động trực tiếp (Direct-only Non-mediation)'
        };
      case 'NO_EFFECT':
        return {
          bg: 'bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
          dot: 'bg-slate-400',
          title: 'Không có tác động (No Effect)'
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700',
          dot: 'bg-slate-400',
          title: 'Chưa xác định'
        };
    }
  };

  const badge = getMediationBadge(result?.conclusion?.mediation_type);

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200/80 dark:border-slate-800 transition-all mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl shadow-sm">
              <GitMerge className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Phân Tích Tác Động Trung Gian & Mô Hình Đường Dẫn (Mediation & Path Analysis)
                <span className="text-2xs font-semibold px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                  PROCESS Model 4
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Quy trình kiểm định 4 bước Baron & Kenny (1986), Kiểm định Sobel (1982), Resampling Bootstrap 95% CI (Preacher & Hayes 2008), và Tỷ lệ VAF (Hair et al. 2017)
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading || eligibleQuestions.length < 3}
            className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Đang phân tích Bootstrap...' : 'Khớp Mô Hình Trung Gian'}</span>
          </button>
        </div>
      </div>

      {/* Selectors Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 py-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20 -mx-6 sm:-mx-8 px-6 sm:px-8">
        {/* Predictor X */}
        <div>
          <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            Biến Độc Lập (X - Predictor)
          </label>
          <select
            value={xId}
            onChange={(e) => setXId(e.target.value)}
            disabled={loading || eligibleQuestions.length < 3}
            className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
          >
            {eligibleQuestions.map((q) => (
              <option key={`x-${q.question_id}`} value={q.question_id}>
                {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
              </option>
            ))}
          </select>
        </div>

        {/* Mediator M */}
        <div>
          <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
            Biến Trung Gian (M - Mediator)
          </label>
          <select
            value={mId}
            onChange={(e) => setMId(e.target.value)}
            disabled={loading || eligibleQuestions.length < 3}
            className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
          >
            {eligibleQuestions.map((q) => (
              <option key={`m-${q.question_id}`} value={q.question_id}>
                {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Y */}
        <div>
          <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Biến Phụ Thuộc (Y - Outcome)
          </label>
          <select
            value={yId}
            onChange={(e) => setYId(e.target.value)}
            disabled={loading || eligibleQuestions.length < 3}
            className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
          >
            {eligibleQuestions.map((q) => (
              <option key={`y-${q.question_id}`} value={q.question_id}>
                {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
              </option>
            ))}
          </select>
        </div>

        {/* Filters & Bootstrap Options */}
        <div className="flex gap-2">
          <div className="flex-1">
            <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
              Phạm Vi Mẫu
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              disabled={loading}
              className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
            >
              <option value="all">Tất cả (All)</option>
              <option value="verified_clean">Đã kiểm định (Clean)</option>
            </select>
          </div>

          <div className="w-24">
            <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
              Bootstrap
            </label>
            <select
              value={bootSamples}
              onChange={(e) => setBootSamples(Number(e.target.value))}
              disabled={loading}
              className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-2 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
            >
              <option value={500}>500 mẫu</option>
              <option value={1000}>1000 mẫu</option>
              <option value={2000}>2000 mẫu</option>
            </select>
          </div>
        </div>
      </div>

      {/* Validation or Error Message */}
      {eligibleQuestions.length < 3 && (
        <div className="mt-6 p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 flex items-center gap-3 text-xs text-amber-800 dark:text-amber-200">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
          <span>Cần tối thiểu 3 câu hỏi định lượng (Thang đo Likert, Điểm số, Đánh giá hoặc Số thực) để thiết lập mô hình đường dẫn trung gian.</span>
        </div>
      )}

      {error && (
        <div className="mt-6 p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 flex items-center gap-3 text-xs text-rose-800 dark:text-rose-200">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Analysis Results */}
      {result && result.status === 'OK' && result.effects_summary && result.conclusion && (
        <div className="mt-6 space-y-6">
          {/* Hero Banner: Conclusion Badge & VAF Summary */}
          <div className="p-5 rounded-2xl border bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/80 dark:border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${badge.bg}`}>
                  <span className={`w-2 h-2 rounded-full ${badge.dot}`}></span>
                  {badge.title}
                </span>
                <span className="text-xs font-semibold text-slate-500">
                  Cỡ mẫu hợp lệ N = {result.sample_size}
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed max-w-3xl">
                {result.conclusion.description}
              </p>
            </div>

            {/* VAF Gauge Indicator */}
            <div className="shrink-0 bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center gap-4 min-w-[200px]">
              <div className="flex-1">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-2xs font-bold text-slate-500 uppercase">Tỷ Lệ VAF</span>
                  <span className="text-xs font-extrabold text-purple-600 dark:text-purple-400">
                    {result.effects_summary.vaf_percent}%
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, result.effects_summary.vaf_percent))}%` }}
                  />
                </div>
                <div className="flex justify-between text-3xs text-slate-400 mt-1">
                  <span>0% (Không)</span>
                  <span>20% - 80% (Một phần)</span>
                  <span>&gt;80% (Toàn phần)</span>
                </div>
              </div>
            </div>
          </div>

          {/* 4 Effect Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Effect c */}
            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Tác Động Tổng Thể (Path c)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-800 dark:text-white">
                  {result.effects_summary.total_effect_c}
                </span>
                <span className="text-xs font-bold text-purple-600">
                  {result.steps?.[0]?.is_significant ? 'Ý nghĩa (p < .05)' : 'Không ý nghĩa'}
                </span>
              </div>
              <span className="text-3xs text-slate-400 block mt-1">
                X → Y (Chưa kiểm soát biến trung gian M)
              </span>
            </div>

            {/* Path a */}
            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Đường Dẫn a (X → M)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-800 dark:text-white">
                  {result.steps?.[1]?.coefficient}
                </span>
                <span className="text-xs font-bold text-indigo-600">
                  β = {result.steps?.[1]?.std_beta}
                </span>
              </div>
              <span className="text-3xs text-slate-400 block mt-1">
                R² = {result.steps?.[1]?.r_squared} (t = {result.steps?.[1]?.t_stat}, p = {result.steps?.[1]?.p_value})
              </span>
            </div>

            {/* Path b */}
            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Đường Dẫn b (M → Y | X)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-800 dark:text-white">
                  {result.steps?.[2]?.path_b?.coefficient}
                </span>
                <span className="text-xs font-bold text-indigo-600">
                  β = {result.steps?.[2]?.path_b?.std_beta}
                </span>
              </div>
              <span className="text-3xs text-slate-400 block mt-1">
                Kiểm soát X: t = {result.steps?.[2]?.path_b?.t_stat}, p = {result.steps?.[2]?.path_b?.p_value}
              </span>
            </div>

            {/* Indirect Effect a*b */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border border-purple-200 dark:border-purple-800/60">
              <span className="text-2xs font-bold text-purple-700 dark:text-purple-300 uppercase tracking-wider block mb-1">
                Tác Động Gián Tiếp (a × b)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-purple-900 dark:text-purple-100">
                  {result.effects_summary.indirect_effect_ab}
                </span>
                <span className="text-xs font-bold text-purple-600 dark:text-purple-400">
                  Sobel z = {result.significance_tests?.sobel_test?.z_stat}
                </span>
              </div>
              <span className="text-3xs text-purple-700/80 dark:text-purple-300/80 block mt-1">
                Bootstrap 95% CI [{result.significance_tests?.bootstrap_resampling?.ci_lower}, {result.significance_tests?.bootstrap_resampling?.ci_upper}]
              </span>
            </div>
          </div>

          {/* Subtabs Selector */}
          <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('diagram')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'diagram'
                  ? 'bg-purple-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
            >
              Sơ Đồ Đường Dẫn (Path Diagram)
            </button>
            <button
              onClick={() => setActiveTab('steps')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'steps'
                  ? 'bg-purple-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
            >
              Bảng Hồi Quy 3 Bước (Baron & Kenny)
            </button>
            <button
              onClick={() => setActiveTab('tests')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'tests'
                  ? 'bg-purple-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
            >
              Kiểm Định Sobel & Bootstrap CI
            </button>
          </div>

          {/* Tab 1: Path Diagram */}
          {activeTab === 'diagram' && (
            <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800 shadow-inner flex flex-col items-center">
              <div className="w-full max-w-xl">
                <svg viewBox="0 0 520 280" className="w-full h-auto">
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 1 L 10 5 L 0 9 z" fill="#a855f7" />
                    </marker>
                    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
                    </marker>
                    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 1 L 10 5 L 0 9 z" fill="#3b82f6" />
                    </marker>
                    <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="50%" stopColor="#a855f7" />
                      <stop offset="100%" stopColor="#10b981" />
                    </linearGradient>
                  </defs>

                  {/* Path a: X -> M */}
                  <path
                    d="M 120 210 Q 180 100 230 75"
                    fill="none"
                    stroke="#a855f7"
                    strokeWidth="2.5"
                    markerEnd="url(#arrow)"
                  />
                  <rect x="130" y="115" width="85" height="24" rx="6" fill="#1e1b4b" stroke="#6366f1" strokeWidth="1" />
                  <text x="172" y="131" textAnchor="middle" fill="#c7d2fe" fontSize="10" fontWeight="bold">
                    a = {result.steps?.[1]?.coefficient} {result.steps?.[1]?.is_significant ? '***' : ''}
                  </text>

                  {/* Path b: M -> Y */}
                  <path
                    d="M 290 75 Q 340 100 400 210"
                    fill="none"
                    stroke="#a855f7"
                    strokeWidth="2.5"
                    markerEnd="url(#arrow)"
                  />
                  <rect x="305" y="115" width="85" height="24" rx="6" fill="#1e1b4b" stroke="#6366f1" strokeWidth="1" />
                  <text x="347" y="131" textAnchor="middle" fill="#c7d2fe" fontSize="10" fontWeight="bold">
                    b = {result.steps?.[2]?.path_b?.coefficient} {result.steps?.[2]?.path_b?.is_significant ? '***' : ''}
                  </text>

                  {/* Path c': X -> Y Direct */}
                  <path
                    d="M 140 230 L 380 230"
                    fill="none"
                    stroke={result.steps?.[2]?.path_c_prime?.is_significant ? "#10b981" : "#64748b"}
                    strokeWidth="2"
                    strokeDasharray={result.steps?.[2]?.path_c_prime?.is_significant ? "none" : "5,5"}
                    markerEnd="url(#arrow-green)"
                  />
                  <rect x="210" y="218" width="100" height="24" rx="6" fill="#0f172a" stroke="#475569" strokeWidth="1" />
                  <text x="260" y="234" textAnchor="middle" fill="#cbd5e1" fontSize="10" fontWeight="bold">
                    c' = {result.steps?.[2]?.path_c_prime?.coefficient} ({result.steps?.[2]?.path_c_prime?.is_significant ? 'sig' : 'ns'})
                  </text>

                  {/* Total Effect c Arc below */}
                  <path
                    d="M 140 245 Q 260 275 380 245"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="1.5"
                    strokeDasharray="4,4"
                  />
                  <text x="260" y="272" textAnchor="middle" fill="#93c5fd" fontSize="9">
                    Tác động tổng thể: c = {result.effects_summary.total_effect_c} (R² = {result.steps?.[0]?.r_squared})
                  </text>

                  {/* Node X */}
                  <g transform="translate(80, 230)">
                    <rect x="-60" y="-22" width="120" height="44" rx="12" fill="#1e293b" stroke="#3b82f6" strokeWidth="2" />
                    <text x="0" y="-3" textAnchor="middle" fill="#93c5fd" fontSize="11" fontWeight="bold">Biến Độc Lập (X)</text>
                    <text x="0" y="13" textAnchor="middle" fill="#cbd5e1" fontSize="8">
                      {result.variables?.x.label ? (result.variables.x.label.substring(0, 18) + (result.variables.x.label.length > 18 ? '..' : '')) : 'X'}
                    </text>
                  </g>

                  {/* Node M */}
                  <g transform="translate(260, 60)">
                    <rect x="-65" y="-22" width="130" height="44" rx="12" fill="#1e293b" stroke="#a855f7" strokeWidth="2" />
                    <text x="0" y="-3" textAnchor="middle" fill="#d8b4fe" fontSize="11" fontWeight="bold">Biến Trung Gian (M)</text>
                    <text x="0" y="13" textAnchor="middle" fill="#cbd5e1" fontSize="8">
                      {result.variables?.m.label ? (result.variables.m.label.substring(0, 20) + (result.variables.m.label.length > 20 ? '..' : '')) : 'M'}
                    </text>
                  </g>

                  {/* Node Y */}
                  <g transform="translate(440, 230)">
                    <rect x="-60" y="-22" width="120" height="44" rx="12" fill="#1e293b" stroke="#10b981" strokeWidth="2" />
                    <text x="0" y="-3" textAnchor="middle" fill="#6ee7b7" fontSize="11" fontWeight="bold">Biến Phụ Thuộc (Y)</text>
                    <text x="0" y="13" textAnchor="middle" fill="#cbd5e1" fontSize="8">
                      {result.variables?.y.label ? (result.variables.y.label.substring(0, 18) + (result.variables.y.label.length > 18 ? '..' : '')) : 'Y'}
                    </text>
                  </g>
                </svg>
              </div>

              <div className="flex items-center gap-6 text-2xs text-slate-400 mt-2">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-purple-500 inline-block"></span>
                  Đường dẫn gián tiếp (Indirect: a, b)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-emerald-500 inline-block"></span>
                  Đường dẫn trực tiếp (Direct: c')
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 border-t border-dashed border-blue-400 inline-block"></span>
                  Tác động tổng thể (Total: c)
                </span>
              </div>
            </div>
          )}

          {/* Tab 2: Steps Table */}
          {activeTab === 'steps' && (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 font-bold border-b border-slate-200 dark:border-slate-700">
                    <th className="py-3 px-4">Bước Kiểm Định</th>
                    <th className="py-3 px-4">Phương Trình Hồi Quy</th>
                    <th className="py-3 px-3 text-right">R²</th>
                    <th className="py-3 px-3 text-right">Hệ Số B</th>
                    <th className="py-3 px-3 text-right">Beta (β)</th>
                    <th className="py-3 px-3 text-right">SE</th>
                    <th className="py-3 px-3 text-right">t-stat</th>
                    <th className="py-3 px-4 text-right">p-value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {/* Step 1 */}
                  <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                      Bước 1: Tác động tổng thể (c)
                    </td>
                    <td className="py-3 px-4 font-mono text-2xs">{result.steps?.[0]?.formula}</td>
                    <td className="py-3 px-3 text-right font-mono">{result.steps?.[0]?.r_squared}</td>
                    <td className="py-3 px-3 text-right font-mono font-bold">{result.steps?.[0]?.coefficient}</td>
                    <td className="py-3 px-3 text-right font-mono">{result.steps?.[0]?.std_beta}</td>
                    <td className="py-3 px-3 text-right font-mono text-slate-400">{result.steps?.[0]?.se}</td>
                    <td className="py-3 px-3 text-right font-mono">{result.steps?.[0]?.t_stat}</td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-indigo-600">
                      {result.steps?.[0]?.p_value}
                    </td>
                  </tr>

                  {/* Step 2 */}
                  <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                      Bước 2: Tác động lên M (a)
                    </td>
                    <td className="py-3 px-4 font-mono text-2xs">{result.steps?.[1]?.formula}</td>
                    <td className="py-3 px-3 text-right font-mono">{result.steps?.[1]?.r_squared}</td>
                    <td className="py-3 px-3 text-right font-mono font-bold">{result.steps?.[1]?.coefficient}</td>
                    <td className="py-3 px-3 text-right font-mono">{result.steps?.[1]?.std_beta}</td>
                    <td className="py-3 px-3 text-right font-mono text-slate-400">{result.steps?.[1]?.se}</td>
                    <td className="py-3 px-3 text-right font-mono">{result.steps?.[1]?.t_stat}</td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-indigo-600">
                      {result.steps?.[1]?.p_value}
                    </td>
                  </tr>

                  {/* Step 3 - Path c' */}
                  <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 bg-purple-50/20 dark:bg-purple-950/10">
                    <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                      Bước 3a: Tác động trực tiếp (c')
                    </td>
                    <td className="py-3 px-4 font-mono text-2xs" rowSpan={2}>
                      {result.steps?.[2]?.formula}
                    </td>
                    <td className="py-3 px-3 text-right font-mono" rowSpan={2}>
                      {result.steps?.[2]?.r_squared} (ΔR² = {result.steps?.[2]?.delta_r_squared})
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold">
                      {result.steps?.[2]?.path_c_prime?.coefficient}
                    </td>
                    <td className="py-3 px-3 text-right font-mono">
                      {result.steps?.[2]?.path_c_prime?.std_beta}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-400">
                      {result.steps?.[2]?.path_c_prime?.se}
                    </td>
                    <td className="py-3 px-3 text-right font-mono">
                      {result.steps?.[2]?.path_c_prime?.t_stat}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-indigo-600">
                      {result.steps?.[2]?.path_c_prime?.p_value}
                    </td>
                  </tr>

                  {/* Step 3 - Path b */}
                  <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 bg-purple-50/20 dark:bg-purple-950/10">
                    <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                      Bước 3b: Đường dẫn từ M (b)
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold">
                      {result.steps?.[2]?.path_b?.coefficient}
                    </td>
                    <td className="py-3 px-3 text-right font-mono">
                      {result.steps?.[2]?.path_b?.std_beta}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-400">
                      {result.steps?.[2]?.path_b?.se}
                    </td>
                    <td className="py-3 px-3 text-right font-mono">
                      {result.steps?.[2]?.path_b?.t_stat}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-indigo-600">
                      {result.steps?.[2]?.path_b?.p_value}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Statistical Tests */}
          {activeTab === 'tests' && result.significance_tests && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Sobel, Aroian, Goodman */}
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60">
                <h4 className="text-xs font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-500" />
                  Kiểm Định Tiệm Cận (Asymptotic Tests)
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
                    <div>
                      <span className="font-semibold text-xs block text-slate-800 dark:text-slate-200">Sobel Test (1982)</span>
                      <span className="text-3xs text-slate-400">z = a×b / √(b²s_a² + a²s_b²)</span>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-xs font-bold block text-purple-600 dark:text-purple-400">
                        z = {result.significance_tests.sobel_test.z_stat}
                      </span>
                      <span className="text-3xs font-semibold text-slate-500">
                        p = {result.significance_tests.sobel_test.p_value} {result.significance_tests.sobel_test.is_significant ? '(Có ý nghĩa)' : '(K.o ý nghĩa)'}
                      </span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
                    <div>
                      <span className="font-semibold text-xs block text-slate-800 dark:text-slate-200">Aroian Test (1947)</span>
                      <span className="text-3xs text-slate-400">Bổ sung số hạng s_a²s_b²</span>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-xs font-bold block text-slate-700 dark:text-slate-300">
                        z = {result.significance_tests.aroian_test.z_stat}
                      </span>
                      <span className="text-3xs font-semibold text-slate-500">
                        p = {result.significance_tests.aroian_test.p_value}
                      </span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
                    <div>
                      <span className="font-semibold text-xs block text-slate-800 dark:text-slate-200">Goodman Test (1960)</span>
                      <span className="text-3xs text-slate-400">Trừ bớt số hạng s_a²s_b²</span>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-xs font-bold block text-slate-700 dark:text-slate-300">
                        z = {result.significance_tests.goodman_test.z_stat}
                      </span>
                      <span className="text-3xs font-semibold text-slate-500">
                        p = {result.significance_tests.goodman_test.p_value}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bootstrap Resampling */}
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60">
                <h4 className="text-xs font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  Kiểm Định Tái Lấy Mẫu Không Tham Số (Bootstrap Resampling)
                </h4>
                <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-800/50 mb-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-2xs font-bold text-emerald-800 dark:text-emerald-200 uppercase">
                      Khoảng Tin Cậy 95% Bootstrap
                    </span>
                    <span className="text-xs font-black text-emerald-700 dark:text-emerald-300 font-mono">
                      [{result.significance_tests.bootstrap_resampling.ci_lower}, {result.significance_tests.bootstrap_resampling.ci_upper}]
                    </span>
                  </div>
                  <p className="text-3xs text-emerald-700 dark:text-emerald-300">
                    {result.significance_tests.bootstrap_resampling.is_significant
                      ? '✓ Khoảng tin cậy 95% hoàn toàn không chứa giá trị 0. Tác động gián tiếp có ý nghĩa thống kê ở mức α = 0.05.'
                      : '✗ Khoảng tin cậy 95% chứa giá trị 0. Chưa đủ bằng chứng bác bỏ giả thuyết H0 về tác động trung gian.'}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
                    <span className="text-3xs text-slate-400 block">Số vòng lặp tái lấy mẫu</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200 font-mono">
                      B = {result.significance_tests.bootstrap_resampling.bootstrap_samples}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
                    <span className="text-3xs text-slate-400 block">Sai số chuẩn Bootstrap (SE)</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200 font-mono">
                      {result.significance_tests.bootstrap_resampling.se_boot}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Academic Narrative APA 7th */}
          <div className="p-5 rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                Diễn Giải Học Thuật Chuẩn APA 7th Edition
              </span>
              <button
                onClick={handleCopyAPA}
                className="flex items-center gap-1.5 px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 text-slate-700 dark:text-slate-300 rounded-xl text-2xs font-semibold shadow-2xs transition-all"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
              </button>
            </div>
            <pre className="font-serif text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap bg-white dark:bg-slate-900/80 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
              {result.conclusion.apa_narrative}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
