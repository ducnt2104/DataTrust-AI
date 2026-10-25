import React, { useState, useEffect } from 'react';
import {
  Scale, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  TrendingUp, Activity, Copy, Check, RefreshCw, BarChart2,
  HelpCircle, BookOpen, Layers, ShieldCheck, Zap, Info, Filter
} from 'lucide-react';
import { api } from '../api/client';
import {
  QuestionStats,
  MannWhitneyUResult,
  WilcoxonSignedRankResult,
  KruskalWallisResult
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const NonParametricTestsCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [activeTab, setActiveTab] = useState<'mann_whitney' | 'wilcoxon' | 'kruskal_wallis'>('mann_whitney');

  // Lọc các câu hỏi định lượng / thang đo (number, rating, nps, likert, linear_scale)
  const numericQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  // Lọc các câu hỏi phân loại / danh mục (single_choice, dropdown, boolean)
  const categoricalQuestions = questions.filter((q) =>
    ['single_choice', 'dropdown', 'boolean'].includes(q.question_type) ||
    (q.option_distribution && Object.keys(q.option_distribution).length > 0)
  );

  // 1. Mann-Whitney State
  const [mwuTargetId, setMwuTargetId] = useState<string>('');
  const [mwuGroupId, setMwuGroupId] = useState<string>('');
  const [mwuScope, setMwuScope] = useState<'all' | 'verified_clean'>('all');
  const [mwuResult, setMwuResult] = useState<MannWhitneyUResult | null>(null);
  const [mwuLoading, setMwuLoading] = useState<boolean>(false);
  const [mwuError, setMwuError] = useState<string | null>(null);

  // 2. Wilcoxon State
  const [wilQ1Id, setWilQ1Id] = useState<string>('');
  const [wilQ2Id, setWilQ2Id] = useState<string>('');
  const [wilScope, setWilScope] = useState<'all' | 'verified_clean'>('all');
  const [wilResult, setWilResult] = useState<WilcoxonSignedRankResult | null>(null);
  const [wilLoading, setWilLoading] = useState<boolean>(false);
  const [wilError, setWilError] = useState<string | null>(null);

  // 3. Kruskal-Wallis State
  const [kwTargetId, setKwTargetId] = useState<string>('');
  const [kwGroupId, setKwGroupId] = useState<string>('');
  const [kwScope, setKwScope] = useState<'all' | 'verified_clean'>('all');
  const [kwResult, setKwResult] = useState<KruskalWallisResult | null>(null);
  const [kwLoading, setKwLoading] = useState<boolean>(false);
  const [kwError, setKwError] = useState<string | null>(null);

  const [copied, setCopied] = useState<boolean>(false);

  // Khởi tạo mặc định
  useEffect(() => {
    if (numericQuestions.length > 0) {
      if (!mwuTargetId) setMwuTargetId(numericQuestions[0].question_id);
      if (!wilQ1Id) setWilQ1Id(numericQuestions[0].question_id);
      if (!kwTargetId) setKwTargetId(numericQuestions[0].question_id);
    }
    if (numericQuestions.length > 1) {
      if (!wilQ2Id) setWilQ2Id(numericQuestions[1].question_id);
    }
    if (categoricalQuestions.length > 0) {
      if (!mwuGroupId) setMwuGroupId(categoricalQuestions[0].question_id);
      if (!kwGroupId) setKwGroupId(categoricalQuestions[0].question_id);
    }
  }, [questions]);

  // Handlers
  const handleRunMannWhitney = async () => {
    if (!mwuTargetId || !mwuGroupId) return;
    try {
      setMwuLoading(true);
      setMwuError(null);
      const res = await api.runMannWhitneyU(surveyId, {
        target_question_id: mwuTargetId,
        grouping_question_id: mwuGroupId,
        scope: mwuScope
      });
      setMwuResult(res);
      if (res.status !== 'OK') {
        setMwuError(res.message || 'Lỗi phân tích Mann-Whitney U.');
      }
    } catch (err) {
      setMwuError(err instanceof Error ? err.message : 'Lỗi gọi API Mann-Whitney U.');
    } finally {
      setMwuLoading(false);
    }
  };

  const handleRunWilcoxon = async () => {
    if (!wilQ1Id || !wilQ2Id) return;
    if (wilQ1Id === wilQ2Id) {
      setWilError('Hai câu hỏi so sánh cặp không được trùng nhau.');
      return;
    }
    try {
      setWilLoading(true);
      setWilError(null);
      const res = await api.runWilcoxonSignedRank(surveyId, {
        question_id_1: wilQ1Id,
        question_id_2: wilQ2Id,
        scope: wilScope
      });
      setWilResult(res);
      if (res.status !== 'OK') {
        setWilError(res.message || 'Lỗi phân tích Wilcoxon Signed-Rank.');
      }
    } catch (err) {
      setWilError(err instanceof Error ? err.message : 'Lỗi gọi API Wilcoxon.');
    } finally {
      setWilLoading(false);
    }
  };

  const handleRunKruskalWallis = async () => {
    if (!kwTargetId || !kwGroupId) return;
    try {
      setKwLoading(true);
      setKwError(null);
      const res = await api.runKruskalWallis(surveyId, {
        target_question_id: kwTargetId,
        grouping_question_id: kwGroupId,
        scope: kwScope
      });
      setKwResult(res);
      if (res.status !== 'OK') {
        setKwError(res.message || 'Lỗi phân tích Kruskal-Wallis H.');
      }
    } catch (err) {
      setKwError(err instanceof Error ? err.message : 'Lỗi gọi API Kruskal-Wallis.');
    } finally {
      setKwLoading(false);
    }
  };

  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200/80 dark:border-slate-800 transition-all mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2.5 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-2xl shadow-sm">
              <Scale className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Kiểm Định Giả Thuyết Phi Tham Số (Non-Parametric Hypothesis Testing)
                <span className="text-2xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  Dành cho Thang đo Likert & Dữ liệu không phân phối chuẩn
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Kiểm định Mann-Whitney U (1947), Wilcoxon Signed-Rank (1945), Kruskal-Wallis H (1952), và So sánh cặp hậu nghiệm Dunn (1964)
              </p>
            </div>
          </div>
        </div>

        {/* 3 Main Tab Buttons */}
        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 rounded-2xl border border-slate-200/70 dark:border-slate-700">
          <button
            onClick={() => setActiveTab('mann_whitney')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'mann_whitney'
                ? 'bg-white dark:bg-slate-700 text-emerald-700 dark:text-emerald-300 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Mann-Whitney U (2 Nhóm)
          </button>
          <button
            onClick={() => setActiveTab('wilcoxon')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'wilcoxon'
                ? 'bg-white dark:bg-slate-700 text-emerald-700 dark:text-emerald-300 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Wilcoxon Cặp (Paired)
          </button>
          <button
            onClick={() => setActiveTab('kruskal_wallis')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'kruskal_wallis'
                ? 'bg-white dark:bg-slate-700 text-emerald-700 dark:text-emerald-300 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Kruskal-Wallis (k ≥ 3 Nhóm)
          </button>
        </div>
      </div>

      {/* =========================================================================
          TAB 1: MANN-WHITNEY U TEST
         ========================================================================= */}
      {activeTab === 'mann_whitney' && (
        <div className="mt-5 space-y-6">
          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-50/70 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Biến Mục Tiêu (Định Lượng / Likert)
              </label>
              <select
                value={mwuTargetId}
                onChange={(e) => setMwuTargetId(e.target.value)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                {numericQuestions.map((q) => (
                  <option key={`mwu-t-${q.question_id}`} value={q.question_id}>
                    {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Biến Phân Nhóm (Phân Loại / Danh Mục)
              </label>
              <select
                value={mwuGroupId}
                onChange={(e) => setMwuGroupId(e.target.value)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                {categoricalQuestions.map((q) => (
                  <option key={`mwu-g-${q.question_id}`} value={q.question_id}>
                    {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Phạm Vi Mẫu
              </label>
              <select
                value={mwuScope}
                onChange={(e) => setMwuScope(e.target.value as any)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="all">Tất cả mẫu (All)</option>
                <option value="verified_clean">Đã kiểm định (Clean)</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleRunMannWhitney}
                disabled={mwuLoading || !mwuTargetId || !mwuGroupId}
                className="w-full flex items-center justify-center gap-1.5 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${mwuLoading ? 'animate-spin' : ''}`} />
                <span>{mwuLoading ? 'Đang kiểm định...' : 'Kiểm Định Mann-Whitney U'}</span>
              </button>
            </div>
          </div>

          {mwuError && (
            <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 flex items-center gap-3 text-xs text-rose-800 dark:text-rose-200">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{mwuError}</span>
            </div>
          )}

          {mwuResult && mwuResult.status === 'OK' && mwuResult.statistics && mwuResult.groups && (
            <div className="space-y-6">
              {/* Hero Banner */}
              <div className="p-4 rounded-2xl border bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/80 dark:border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className={`p-2 rounded-xl ${mwuResult.statistics.is_significant ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}`}>
                    <CheckCircle2 className="w-5 h-5" />
                  </span>
                  <div>
                    <span className="text-xs font-bold text-slate-800 dark:text-white block">
                      {mwuResult.statistics.is_significant
                        ? `Khác biệt có ý nghĩa thống kê (p = ${mwuResult.statistics.p_value} < .05)`
                        : `Chưa có sự khác biệt ý nghĩa thống kê (p = ${mwuResult.statistics.p_value} ≥ .05)`}
                    </span>
                    <span className="text-2xs text-slate-500">
                      Nhóm có hạng vượt trội: <strong className="text-emerald-600">{mwuResult.conclusion?.higher_group}</strong> • Tổng cỡ mẫu N = {mwuResult.total_sample_size}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">Thống kê U</span>
                    <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                      {mwuResult.statistics.u_statistic}
                    </span>
                  </div>
                  <div className="h-7 w-px bg-slate-200 dark:bg-slate-700"></div>
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">z-statistic</span>
                    <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                      {mwuResult.statistics.z_statistic}
                    </span>
                  </div>
                  <div className="h-7 w-px bg-slate-200 dark:bg-slate-700"></div>
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">Rosenthal r</span>
                    <span className="text-base font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                      {mwuResult.effect_size?.rosenthal_r}
                    </span>
                  </div>
                </div>
              </div>

              {/* Group Comparison Table */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Group 1 */}
                <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
                  <span className="text-xs font-bold text-emerald-700 dark:text-emerald-300 block mb-2">
                    {mwuResult.groups.group1.name} (n = {mwuResult.groups.group1.descriptives.n})
                  </span>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                      <span className="text-3xs text-slate-400 block">Hạng TB (Mean Rank)</span>
                      <span className="font-extrabold text-slate-800 dark:text-slate-200 font-mono">
                        {mwuResult.groups.group1.mean_rank}
                      </span>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                      <span className="text-3xs text-slate-400 block">Trung vị (Median)</span>
                      <span className="font-extrabold text-slate-800 dark:text-slate-200 font-mono">
                        {mwuResult.groups.group1.descriptives.median}
                      </span>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                      <span className="text-3xs text-slate-400 block">Khoảng IQR</span>
                      <span className="font-extrabold text-slate-800 dark:text-slate-200 font-mono">
                        {mwuResult.groups.group1.descriptives.iqr}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Group 2 */}
                <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
                  <span className="text-xs font-bold text-teal-700 dark:text-teal-300 block mb-2">
                    {mwuResult.groups.group2.name} (n = {mwuResult.groups.group2.descriptives.n})
                  </span>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                      <span className="text-3xs text-slate-400 block">Hạng TB (Mean Rank)</span>
                      <span className="font-extrabold text-slate-800 dark:text-slate-200 font-mono">
                        {mwuResult.groups.group2.mean_rank}
                      </span>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                      <span className="text-3xs text-slate-400 block">Trung vị (Median)</span>
                      <span className="font-extrabold text-slate-800 dark:text-slate-200 font-mono">
                        {mwuResult.groups.group2.descriptives.median}
                      </span>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                      <span className="text-3xs text-slate-400 block">Khoảng IQR</span>
                      <span className="font-extrabold text-slate-800 dark:text-slate-200 font-mono">
                        {mwuResult.groups.group2.descriptives.iqr}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Effect Size & APA Narrative */}
              <div className="p-5 rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-slate-800 dark:text-white flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    Báo Cáo Diễn Giải Học Thuật Chuẩn APA 7th Edition
                  </span>
                  <button
                    onClick={() => handleCopyText(mwuResult.conclusion?.apa_narrative || '')}
                    className="flex items-center gap-1.5 px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 text-slate-700 dark:text-slate-300 rounded-xl text-2xs font-semibold shadow-2xs transition-all"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
                  </button>
                </div>
                <p className="font-serif text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-white dark:bg-slate-900/80 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                  {mwuResult.conclusion?.apa_narrative}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 2: WILCOXON SIGNED-RANK TEST
         ========================================================================= */}
      {activeTab === 'wilcoxon' && (
        <div className="mt-5 space-y-6">
          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-50/70 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Đo Lường 1 (Trước / Tiêu Chí A)
              </label>
              <select
                value={wilQ1Id}
                onChange={(e) => setWilQ1Id(e.target.value)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                {numericQuestions.map((q) => (
                  <option key={`wil-1-${q.question_id}`} value={q.question_id}>
                    {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Đo Lường 2 (Sau / Tiêu Chí B)
              </label>
              <select
                value={wilQ2Id}
                onChange={(e) => setWilQ2Id(e.target.value)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                {numericQuestions.map((q) => (
                  <option key={`wil-2-${q.question_id}`} value={q.question_id}>
                    {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Phạm Vi Mẫu
              </label>
              <select
                value={wilScope}
                onChange={(e) => setWilScope(e.target.value as any)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="all">Tất cả mẫu (All)</option>
                <option value="verified_clean">Đã kiểm định (Clean)</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleRunWilcoxon}
                disabled={wilLoading || !wilQ1Id || !wilQ2Id}
                className="w-full flex items-center justify-center gap-1.5 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${wilLoading ? 'animate-spin' : ''}`} />
                <span>{wilLoading ? 'Đang kiểm định...' : 'Kiểm Định Wilcoxon Cặp'}</span>
              </button>
            </div>
          </div>

          {wilError && (
            <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 flex items-center gap-3 text-xs text-rose-800 dark:text-rose-200">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{wilError}</span>
            </div>
          )}

          {wilResult && wilResult.status === 'OK' && wilResult.statistics && (
            <div className="space-y-6">
              {/* Hero Banner */}
              <div className="p-4 rounded-2xl border bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/80 dark:border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className={`p-2 rounded-xl ${wilResult.statistics.is_significant ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}`}>
                    <CheckCircle2 className="w-5 h-5" />
                  </span>
                  <div>
                    <span className="text-xs font-bold text-slate-800 dark:text-white block">
                      {wilResult.statistics.is_significant
                        ? `Sự thay đổi giữa 2 lần đo có ý nghĩa thống kê (p = ${wilResult.statistics.p_value} < .05)`
                        : `Chưa có sự thay đổi ý nghĩa thống kê (p = ${wilResult.statistics.p_value} ≥ .05)`}
                    </span>
                    <span className="text-2xs text-slate-500">
                      Tổng số cặp quan sát: {wilResult.total_pairs} • Cặp hiệu dụng: {wilResult.effective_pairs} ({wilResult.zero_differences_count} cặp hòa)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">Thống kê W</span>
                    <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                      {wilResult.statistics.w_statistic}
                    </span>
                  </div>
                  <div className="h-7 w-px bg-slate-200 dark:bg-slate-700"></div>
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">z-statistic</span>
                    <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                      {wilResult.statistics.z_statistic}
                    </span>
                  </div>
                  <div className="h-7 w-px bg-slate-200 dark:bg-slate-700"></div>
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">Rosenthal r</span>
                    <span className="text-base font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                      {wilResult.effect_size?.rosenthal_r}
                    </span>
                  </div>
                </div>
              </div>

              {/* Descriptives Box */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
                    {wilResult.samples?.sample1.name}
                  </span>
                  <span className="text-xl font-black text-slate-900 dark:text-white font-mono block">
                    Mdn = {wilResult.samples?.sample1.descriptives.median}
                  </span>
                  <span className="text-3xs text-slate-400">
                    Mean = {wilResult.samples?.sample1.descriptives.mean}, IQR = {wilResult.samples?.sample1.descriptives.iqr}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
                    {wilResult.samples?.sample2.name}
                  </span>
                  <span className="text-xl font-black text-slate-900 dark:text-white font-mono block">
                    Mdn = {wilResult.samples?.sample2.descriptives.median}
                  </span>
                  <span className="text-3xs text-slate-400">
                    Mean = {wilResult.samples?.sample2.descriptives.mean}, IQR = {wilResult.samples?.sample2.descriptives.iqr}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700">
                  <span className="text-xs font-bold text-emerald-700 dark:text-emerald-300 block mb-1">
                    Chênh Lệch (Differences)
                  </span>
                  <span className="text-xl font-black text-emerald-600 dark:text-emerald-400 font-mono block">
                    Δ Mdn = {wilResult.samples?.differences.median}
                  </span>
                  <span className="text-3xs text-slate-400">
                    W+ = {wilResult.statistics.w_plus}, W- = {wilResult.statistics.w_minus}
                  </span>
                </div>
              </div>

              {/* APA Narrative */}
              <div className="p-5 rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-slate-800 dark:text-white flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    Báo Cáo Diễn Giải Học Thuật Chuẩn APA 7th Edition
                  </span>
                  <button
                    onClick={() => handleCopyText(wilResult.conclusion?.apa_narrative || '')}
                    className="flex items-center gap-1.5 px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 text-slate-700 dark:text-slate-300 rounded-xl text-2xs font-semibold shadow-2xs transition-all"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
                  </button>
                </div>
                <p className="font-serif text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-white dark:bg-slate-900/80 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                  {wilResult.conclusion?.apa_narrative}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 3: KRUSKAL-WALLIS H TEST & DUNN'S POST-HOC
         ========================================================================= */}
      {activeTab === 'kruskal_wallis' && (
        <div className="mt-5 space-y-6">
          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-50/70 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Biến Mục Tiêu (Định Lượng / Thang Đo)
              </label>
              <select
                value={kwTargetId}
                onChange={(e) => setKwTargetId(e.target.value)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                {numericQuestions.map((q) => (
                  <option key={`kw-t-${q.question_id}`} value={q.question_id}>
                    {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Biến Phân Nhóm (k ≥ 3 Nhóm)
              </label>
              <select
                value={kwGroupId}
                onChange={(e) => setKwGroupId(e.target.value)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                {categoricalQuestions.map((q) => (
                  <option key={`kw-g-${q.question_id}`} value={q.question_id}>
                    {q.question_title.length > 40 ? `${q.question_title.substring(0, 40)}...` : q.question_title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                Phạm Vi Mẫu
              </label>
              <select
                value={kwScope}
                onChange={(e) => setKwScope(e.target.value as any)}
                className="w-full text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="all">Tất cả mẫu (All)</option>
                <option value="verified_clean">Đã kiểm định (Clean)</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleRunKruskalWallis}
                disabled={kwLoading || !kwTargetId || !kwGroupId}
                className="w-full flex items-center justify-center gap-1.5 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${kwLoading ? 'animate-spin' : ''}`} />
                <span>{kwLoading ? 'Đang kiểm định...' : 'Kiểm Định Kruskal-Wallis H'}</span>
              </button>
            </div>
          </div>

          {kwError && (
            <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 flex items-center gap-3 text-xs text-rose-800 dark:text-rose-200">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{kwError}</span>
            </div>
          )}

          {kwResult && kwResult.status === 'OK' && kwResult.statistics && (
            <div className="space-y-6">
              {/* Hero Banner */}
              <div className="p-4 rounded-2xl border bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/80 dark:border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className={`p-2 rounded-xl ${kwResult.statistics.is_significant ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}`}>
                    <CheckCircle2 className="w-5 h-5" />
                  </span>
                  <div>
                    <span className="text-xs font-bold text-slate-800 dark:text-white block">
                      {kwResult.statistics.is_significant
                        ? `Khác biệt giữa các nhóm có ý nghĩa thống kê (p = ${kwResult.statistics.p_value} < .05)`
                        : `Chưa ghi nhận sự khác biệt ý nghĩa thống kê (p = ${kwResult.statistics.p_value} ≥ .05)`}
                    </span>
                    <span className="text-2xs text-slate-500">
                      Số nhóm so sánh: k = {kwResult.k_groups} • Bậc tự do df = {kwResult.degrees_of_freedom} • Tổng N = {kwResult.total_sample_size}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">Thống kê H (Adj)</span>
                    <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                      {kwResult.statistics.h_adjusted}
                    </span>
                  </div>
                  <div className="h-7 w-px bg-slate-200 dark:bg-slate-700"></div>
                  <div className="text-right">
                    <span className="text-2xs font-bold text-slate-400 uppercase block">Epsilon² (ε²)</span>
                    <span className="text-base font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                      {kwResult.effect_size?.epsilon_squared}
                    </span>
                  </div>
                </div>
              </div>

              {/* Group Ranks Table */}
              <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 font-bold border-b border-slate-200 dark:border-slate-700">
                      <th className="py-3 px-4">Nhóm Đối Tượng</th>
                      <th className="py-3 px-3 text-right">Cỡ Mẫu (n)</th>
                      <th className="py-3 px-3 text-right">Tổng Hạng (Rank Sum)</th>
                      <th className="py-3 px-3 text-right text-emerald-700 dark:text-emerald-300">Hạng TB (Mean Rank)</th>
                      <th className="py-3 px-3 text-right">Trung Vị (Mdn)</th>
                      <th className="py-3 px-3 text-right">Khoảng IQR</th>
                      <th className="py-3 px-4 text-right">Trung Bình ± SD</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                    {kwResult.groups_summary?.map((g) => (
                      <tr key={`kw-gsum-${g.group_name}`} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">{g.group_name}</td>
                        <td className="py-3 px-3 text-right font-mono">{g.sample_size}</td>
                        <td className="py-3 px-3 text-right font-mono">{g.rank_sum}</td>
                        <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400">
                          {g.mean_rank}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">{g.median}</td>
                        <td className="py-3 px-3 text-right font-mono">{g.iqr}</td>
                        <td className="py-3 px-4 text-right font-mono text-slate-500">
                          {g.mean} ± {g.std}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Dunn's Post-Hoc Comparisons Table */}
              {kwResult.post_hoc_dunn_tests && kwResult.post_hoc_dunn_tests.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-800 dark:text-white mb-2 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-500" />
                    So Sánh Cặp Hậu Nghiệm Dunn's Test (Hiệu chỉnh Bonferroni)
                  </h4>
                  <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 font-bold border-b border-slate-200 dark:border-slate-700">
                          <th className="py-3 px-4">Cặp So Sánh</th>
                          <th className="py-3 px-3 text-right">Chênh Lệch Hạng TB</th>
                          <th className="py-3 px-3 text-right">Sai Số Chuẩn (SE)</th>
                          <th className="py-3 px-3 text-right">z-statistic</th>
                          <th className="py-3 px-3 text-right">p Chưa Hiệu Chỉnh</th>
                          <th className="py-3 px-3 text-right font-bold text-emerald-700 dark:text-emerald-300">p Bonferroni</th>
                          <th className="py-3 px-4 text-center">Kết Luận</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                        {kwResult.post_hoc_dunn_tests.map((pair) => (
                          <tr key={`dunn-${pair.comparison}`} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                            <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">{pair.comparison}</td>
                            <td className="py-3 px-3 text-right font-mono font-bold">{pair.mean_rank_diff}</td>
                            <td className="py-3 px-3 text-right font-mono text-slate-400">{pair.std_error}</td>
                            <td className="py-3 px-3 text-right font-mono">{pair.z_statistic}</td>
                            <td className="py-3 px-3 text-right font-mono text-slate-500">{pair.p_value_unadjusted}</td>
                            <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400">
                              {pair.p_value_bonferroni}
                            </td>
                            <td className="py-3 px-4 text-center">
                              {pair.is_significant_bonferroni ? (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-3xs font-bold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                                  Ý nghĩa (p &lt; .05)
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-3xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
                                  K.o ý nghĩa
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* APA Narrative */}
              <div className="p-5 rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-slate-800 dark:text-white flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    Báo Cáo Diễn Giải Học Thuật Chuẩn APA 7th Edition
                  </span>
                  <button
                    onClick={() => handleCopyText(kwResult.conclusion?.apa_narrative || '')}
                    className="flex items-center gap-1.5 px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 text-slate-700 dark:text-slate-300 rounded-xl text-2xs font-semibold shadow-2xs transition-all"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
                  </button>
                </div>
                <p className="font-serif text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-white dark:bg-slate-900/80 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                  {kwResult.conclusion?.apa_narrative}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
