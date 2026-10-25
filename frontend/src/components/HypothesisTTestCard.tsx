import React, { useState } from 'react';
import {
  Split,
  GitCommit,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  Play,
  Info,
  Scale,
  Sparkles,
  TrendingUp,
  FileSpreadsheet,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { IndependentTTestReport, PairedTTestReport } from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
  options?: any;
}

interface Props {
  surveyId: string;
  questions: QuestionItem[];
}

export const HypothesisTTestCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [activeTab, setActiveTab] = useState<'independent' | 'paired'>('independent');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  // Independent T-Test State
  const [groupingQId, setGroupingQId] = useState<string>('');
  const [group1Val, setGroup1Val] = useState<string>('');
  const [group2Val, setGroup2Val] = useState<string>('');
  const [targetQId, setTargetQId] = useState<string>('');
  const [indepResult, setIndepResult] = useState<IndependentTTestReport | null>(null);

  // Paired T-Test State
  const [preQId, setPreQId] = useState<string>('');
  const [postQId, setPostQId] = useState<string>('');
  const [pairedResult, setPairedResult] = useState<PairedTTestReport | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Phân loại câu hỏi định tính (phân nhóm) và định lượng (thang đo)
  const categoricalQuestions = questions.filter(q =>
    ['single_choice', 'dropdown', 'boolean'].includes(q.question_type)
  );

  const scaleQuestions = questions.filter(q =>
    ['rating', 'linear_scale', 'number', 'nps', 'likert'].includes(q.question_type) ||
    (q.question_type === 'single_choice' && ['hài lòng', 'đồng ý', 'thang điểm', 'likert', 'mức độ'].some(k => q.title.toLowerCase().includes(k)))
  );

  // Trích xuất các options của câu hỏi phân nhóm đang chọn
  const selectedGroupingQ = questions.find(q => q.id === groupingQId);
  const availableGroupOptions: string[] = React.useMemo(() => {
    if (!selectedGroupingQ) return [];
    const opts = selectedGroupingQ.options;
    if (Array.isArray(opts)) {
      return opts.map(o => (typeof o === 'string' ? o : o.label || o.id || ''));
    }
    return [];
  }, [selectedGroupingQ]);

  const handleRunIndependentTTest = async () => {
    if (!groupingQId || !group1Val || !group2Val || !targetQId) {
      setError('Vui lòng chọn đầy đủ biến phân nhóm, 2 nhóm so sánh và biến đo lường mục tiêu.');
      return;
    }
    if (group1Val === group2Val) {
      setError('Hai nhóm so sánh phải khác nhau (ví dụ: Nam vs Nữ, Thực nghiệm vs Đối chứng).');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runIndependentTTest(surveyId, {
        grouping_question_id: groupingQId,
        group1_value: group1Val,
        group2_value: group2Val,
        target_question_id: targetQId,
        scope
      });
      setIndepResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi thực hiện Independent T-Test.');
      setIndepResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPairedTTest = async () => {
    if (!preQId || !postQId) {
      setError('Vui lòng chọn cả biến đo lường Trước can thiệp (Pre) và Sau can thiệp (Post).');
      return;
    }
    if (preQId === postQId) {
      setError('Biến Pre và Post phải là 2 câu hỏi khác nhau.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runPairedTTest(surveyId, {
        pre_question_id: preQId,
        post_question_id: postQId,
        scope
      });
      setPairedResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi thực hiện Paired T-Test.');
      setPairedResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyApa = (text?: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Top Header */}
      <div className="p-6 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="p-1.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <Scale className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold tracking-tight text-white">
              Kiểm Định Giả Thuyết T-Test &amp; Kích Thước Hiệu Ứng
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-400/20 text-[10px] font-medium">
              Student (1908) • Welch (1947) • Cohen's d (1988)
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
            Kiểm định sự khác biệt có ý nghĩa thống kê giữa hai nhóm độc lập (Levene &amp; Welch correction) 
            hoặc giữa hai lần đo ghép cặp lặp lại (Pre-Post Intervention) theo chuẩn APA 7th Edition.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-2 self-start sm:self-center">
          <div className="inline-flex rounded-xl bg-slate-800/80 p-0.5 border border-slate-700/60 text-xs">
            <button
              onClick={() => { setActiveTab('independent'); setError(null); }}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'independent'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Split className="w-3.5 h-3.5" />
              <span>2 Nhóm Độc Lập</span>
            </button>
            <button
              onClick={() => { setActiveTab('paired'); setError(null); }}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'paired'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <GitCommit className="w-3.5 h-3.5" />
              <span>Ghép Cặp (Pre-Post)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Control Drawer */}
      <div className="p-6 border-b border-slate-100 bg-slate-50/50">
        {activeTab === 'independent' ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Biến phân nhóm */}
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Biến Phân Nhóm (Categorical)
                </label>
                <select
                  value={groupingQId}
                  onChange={(e) => {
                    setGroupingQId(e.target.value);
                    setGroup1Val('');
                    setGroup2Val('');
                  }}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="">-- Chọn câu hỏi phân nhóm --</option>
                  {categoricalQuestions.map(q => (
                    <option key={q.id} value={q.id}>{q.title}</option>
                  ))}
                </select>
              </div>

              {/* Nhóm 1 */}
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Nhóm 1 (Group 1)
                </label>
                <select
                  value={group1Val}
                  onChange={(e) => setGroup1Val(e.target.value)}
                  disabled={!groupingQId}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800 disabled:opacity-50"
                >
                  <option value="">-- Chọn nhóm 1 --</option>
                  {availableGroupOptions.map((opt, i) => (
                    <option key={i} value={opt}>{opt}</option>
                  ))}
                </select>
              </div>

              {/* Nhóm 2 */}
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Nhóm 2 (Group 2)
                </label>
                <select
                  value={group2Val}
                  onChange={(e) => setGroup2Val(e.target.value)}
                  disabled={!groupingQId}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800 disabled:opacity-50"
                >
                  <option value="">-- Chọn nhóm 2 --</option>
                  {availableGroupOptions.map((opt, i) => (
                    <option key={i} value={opt}>{opt}</option>
                  ))}
                </select>
              </div>

              {/* Biến đo lường mục tiêu */}
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Biến Đo Lường (Continuous)
                </label>
                <select
                  value={targetQId}
                  onChange={(e) => setTargetQId(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800"
                >
                  <option value="">-- Chọn biến thang đo --</option>
                  {scaleQuestions.map(q => (
                    <option key={q.id} value={q.id}>{q.title}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium">Phạm vi:</span>
                <button
                  type="button"
                  onClick={() => setScope('all')}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    scope === 'all' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >
                  Toàn bộ phản hồi
                </button>
                <button
                  type="button"
                  onClick={() => setScope('verified_clean')}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    scope === 'verified_clean' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >
                  Mẫu đã làm sạch
                </button>
              </div>

              <button
                onClick={handleRunIndependentTTest}
                disabled={loading || !groupingQId || !group1Val || !group2Val || !targetQId}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                <span>Chạy Independent T-Test</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Đo Lường Lần 1: Trước Can Thiệp (Pre-test)
                </label>
                <select
                  value={preQId}
                  onChange={(e) => setPreQId(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800"
                >
                  <option value="">-- Chọn câu hỏi trước can thiệp --</option>
                  {scaleQuestions.map(q => (
                    <option key={q.id} value={q.id}>{q.title}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Đo Lường Lần 2: Sau Can Thiệp (Post-test)
                </label>
                <select
                  value={postQId}
                  onChange={(e) => setPostQId(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800"
                >
                  <option value="">-- Chọn câu hỏi sau can thiệp --</option>
                  {scaleQuestions.map(q => (
                    <option key={q.id} value={q.id}>{q.title}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium">Phạm vi:</span>
                <button
                  type="button"
                  onClick={() => setScope('all')}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    scope === 'all' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >
                  Toàn bộ phản hồi
                </button>
                <button
                  type="button"
                  onClick={() => setScope('verified_clean')}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    scope === 'verified_clean' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >
                  Mẫu đã làm sạch
                </button>
              </div>

              <button
                onClick={handleRunPairedTTest}
                disabled={loading || !preQId || !postQId}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                <span>Chạy Paired T-Test</span>
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 rounded-xl bg-rose-50 text-rose-700 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results Content Area */}
      <div className="p-6">
        {activeTab === 'independent' ? (
          indepResult ? (
            <div className="space-y-6">
              {/* 4 Hero KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Thống Kê t &amp; Bậc Tự Do</span>
                    <Scale className="w-3.5 h-3.5 text-indigo-500" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    t = {indepResult.primary_test.t_stat.toFixed(2)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    df = {indepResult.primary_test.df} ({indepResult.test_method})
                  </div>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Mức Ý Nghĩa p-value</span>
                    {indepResult.primary_test.is_significant_05 ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Info className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    p {indepResult.primary_test.p_value < 0.001 ? '< .001' : `= ${indepResult.primary_test.p_value.toFixed(3)}`}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {indepResult.primary_test.is_significant_01 ? (
                      <span className="text-emerald-600 font-semibold">Ý nghĩa cao (p &lt; .01)</span>
                    ) : indepResult.primary_test.is_significant_05 ? (
                      <span className="text-emerald-600 font-semibold">Có ý nghĩa (p &lt; .05)</span>
                    ) : (
                      <span className="text-slate-400">Không có ý nghĩa (p &ge; .05)</span>
                    )}
                  </div>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Kích Thước Hiệu Ứng (d)</span>
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    d = {indepResult.effect_size.cohen_d.toFixed(2)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    <span className="font-semibold text-indigo-600">{indepResult.effect_size.magnitude}</span> (g = {indepResult.effect_size.hedges_g.toFixed(2)})
                  </div>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Chênh Lệch Trung Bình (ΔM)</span>
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    {indepResult.mean_difference > 0 ? `+${indepResult.mean_difference}` : indepResult.mean_difference}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    95% CI: [{indepResult.ci_95_lower}, {indepResult.ci_95_upper}]
                  </div>
                </div>
              </div>

              {/* Group Comparison & Levene Test Box */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Group 1 Stats */}
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs">
                  <div className="font-bold text-slate-800 text-sm mb-2">{indepResult.group1.label}</div>
                  <div className="space-y-1 text-slate-600">
                    <div className="flex justify-between"><span>Cỡ mẫu (N):</span><span className="font-mono font-bold text-slate-900">{indepResult.group1.n}</span></div>
                    <div className="flex justify-between"><span>Điểm trung bình (M):</span><span className="font-mono font-bold text-indigo-600">{indepResult.group1.mean}</span></div>
                    <div className="flex justify-between"><span>Độ lệch chuẩn (SD):</span><span className="font-mono">{indepResult.group1.sd}</span></div>
                    <div className="flex justify-between"><span>Sai số chuẩn (SE):</span><span className="font-mono">{indepResult.group1.se}</span></div>
                  </div>
                </div>

                {/* Group 2 Stats */}
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs">
                  <div className="font-bold text-slate-800 text-sm mb-2">{indepResult.group2.label}</div>
                  <div className="space-y-1 text-slate-600">
                    <div className="flex justify-between"><span>Cỡ mẫu (N):</span><span className="font-mono font-bold text-slate-900">{indepResult.group2.n}</span></div>
                    <div className="flex justify-between"><span>Điểm trung bình (M):</span><span className="font-mono font-bold text-indigo-600">{indepResult.group2.mean}</span></div>
                    <div className="flex justify-between"><span>Độ lệch chuẩn (SD):</span><span className="font-mono">{indepResult.group2.sd}</span></div>
                    <div className="flex justify-between"><span>Sai số chuẩn (SE):</span><span className="font-mono">{indepResult.group2.se}</span></div>
                  </div>
                </div>

                {/* Levene's Test Diagnostics */}
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs">
                  <div className="font-bold text-slate-800 text-sm mb-2 flex items-center justify-between">
                    <span>Kiểm Định Phương Sai Levene</span>
                    <Info className="w-3.5 h-3.5 text-slate-400" />
                  </div>
                  <div className="space-y-1 text-slate-600">
                    <div className="flex justify-between"><span>Thống kê F:</span><span className="font-mono font-bold">{indepResult.levene_test.f_stat}</span></div>
                    <div className="flex justify-between"><span>p-value Levene:</span><span className="font-mono">{indepResult.levene_test.p_value}</span></div>
                    <div className="mt-2 pt-2 border-t border-slate-200">
                      {indepResult.levene_test.equal_variances_assumed ? (
                        <span className="text-emerald-700 font-semibold block text-[11px]">
                          ✓ Đồng nhất phương sai (Student t)
                        </span>
                      ) : (
                        <span className="text-amber-700 font-semibold block text-[11px]">
                          ⚠️ Phương sai không đồng nhất (Welch t)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* APA Narrative */}
              <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/80">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <FileSpreadsheet className="w-3.5 h-3.5 text-indigo-600" />
                    Báo Cáo Diễn Giải Học Thuật Theo Chuẩn APA 7th Edition
                  </span>
                  <button
                    onClick={() => copyApa(indepResult.apa_interpretation)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-100 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-600" />
                        <span className="text-emerald-700">Đã sao chép</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3 text-slate-400" />
                        <span>Sao chép trích dẫn</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed font-serif italic bg-white p-3 rounded-xl border border-slate-200/60">
                  "{indepResult.apa_interpretation}"
                </p>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-slate-400">
              Vui lòng chọn biến phân nhóm và biến thang đo, sau đó bấm <strong>"Chạy Independent T-Test"</strong> để bắt đầu.
            </div>
          )
        ) : (
          pairedResult ? (
            <div className="space-y-6">
              {/* 4 Hero KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Thống Kê t (Ghép Cặp)</span>
                    <Scale className="w-3.5 h-3.5 text-indigo-500" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    t = {pairedResult.t_stat.toFixed(2)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    df = {pairedResult.degrees_of_freedom} (N = {pairedResult.sample_size})
                  </div>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Mức Ý Nghĩa p-value</span>
                    {pairedResult.is_significant_05 ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Info className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    p {pairedResult.p_value < 0.001 ? '< .001' : `= ${pairedResult.p_value.toFixed(3)}`}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {pairedResult.is_significant_01 ? (
                      <span className="text-emerald-600 font-semibold">Ý nghĩa cao (p &lt; .01)</span>
                    ) : pairedResult.is_significant_05 ? (
                      <span className="text-emerald-600 font-semibold">Có ý nghĩa (p &lt; .05)</span>
                    ) : (
                      <span className="text-slate-400">Không có ý nghĩa (p &ge; .05)</span>
                    )}
                  </div>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Kích Thước Hiệu Ứng (d_z)</span>
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    d_z = {pairedResult.effect_size.cohen_d.toFixed(2)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    <span className="font-semibold text-indigo-600">{pairedResult.effect_size.magnitude}</span>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Chênh Lệch Trung Bình (ΔM)</span>
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 tracking-tight">
                    {pairedResult.mean_difference > 0 ? `+${pairedResult.mean_difference}` : pairedResult.mean_difference}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Tương quan Pearson: r = {pairedResult.pearson_r}
                  </div>
                </div>
              </div>

              {/* Pre vs Post Comparison Strip */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs">
                  <div className="font-bold text-slate-800 text-sm mb-2">{pairedResult.variable2.label}</div>
                  <div className="space-y-1 text-slate-600">
                    <div className="flex justify-between"><span>Điểm trung bình (M):</span><span className="font-mono font-bold text-slate-900">{pairedResult.variable2.mean}</span></div>
                    <div className="flex justify-between"><span>Độ lệch chuẩn (SD):</span><span className="font-mono">{pairedResult.variable2.sd}</span></div>
                    <div className="flex justify-between"><span>Sai số chuẩn (SE):</span><span className="font-mono">{pairedResult.variable2.se}</span></div>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-50/50 border border-indigo-200/70 text-xs">
                  <div className="font-bold text-indigo-900 text-sm mb-2">{pairedResult.variable1.label}</div>
                  <div className="space-y-1 text-slate-600">
                    <div className="flex justify-between"><span>Điểm trung bình (M):</span><span className="font-mono font-bold text-indigo-600">{pairedResult.variable1.mean}</span></div>
                    <div className="flex justify-between"><span>Độ lệch chuẩn (SD):</span><span className="font-mono">{pairedResult.variable1.sd}</span></div>
                    <div className="flex justify-between"><span>Sai số chuẩn (SE):</span><span className="font-mono">{pairedResult.variable1.se}</span></div>
                  </div>
                </div>
              </div>

              {/* APA Narrative */}
              <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/80">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <FileSpreadsheet className="w-3.5 h-3.5 text-indigo-600" />
                    Báo Cáo Diễn Giải Học Thuật Theo Chuẩn APA 7th Edition
                  </span>
                  <button
                    onClick={() => copyApa(pairedResult.apa_interpretation)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-100 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-600" />
                        <span className="text-emerald-700">Đã sao chép</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3 text-slate-400" />
                        <span>Sao chép trích dẫn</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed font-serif italic bg-white p-3 rounded-xl border border-slate-200/60">
                  "{pairedResult.apa_interpretation}"
                </p>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-slate-400">
              Vui lòng chọn biến Trước can thiệp và Sau can thiệp, sau đó bấm <strong>"Chạy Paired T-Test"</strong> để bắt đầu.
            </div>
          )
        )}
      </div>
    </div>
  );
};
