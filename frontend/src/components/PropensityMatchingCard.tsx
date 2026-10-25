import React, { useState, useEffect } from 'react';
import {
  Layers, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  TrendingUp, Activity, Copy, Check, RefreshCw, BarChart2,
  BookOpen, ShieldCheck, Zap, Sliders, Filter, Scale, GitCompare,
  Percent, Crosshair
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, PSMAnalysisResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const PropensityMatchingCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc câu hỏi biến kết quả Y (Outcome - định lượng)
  const outcomeCandidateQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  // Lọc câu hỏi biến can thiệp Z (Treatment - nhị phân / phân loại)
  const treatmentCandidateQuestions = questions.filter((q) =>
    ['single_choice', 'dropdown', 'multiple_choice', 'number'].includes(q.question_type) ||
    (q.option_distribution && Object.keys(q.option_distribution).length >= 2)
  );

  // Lọc câu hỏi đồng biến X (Covariates - định lượng hoặc thang đo)
  const covariateCandidateQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type)
  );

  const [treatmentId, setTreatmentId] = useState<string>('');
  const [treatmentValue, setTreatmentValue] = useState<string>('1');
  const [outcomeId, setOutcomeId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [caliperFactor, setCaliperFactor] = useState<number>(0.20);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [result, setResult] = useState<PSMAnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);

  // Khởi tạo mặc định
  useEffect(() => {
    if (treatmentCandidateQuestions.length > 0 && !treatmentId) {
      setTreatmentId(treatmentCandidateQuestions[0].question_id);
    }
    if (outcomeCandidateQuestions.length > 0 && !outcomeId) {
      const cand = outcomeCandidateQuestions.find(q => q.question_id !== treatmentCandidateQuestions[0]?.question_id) || outcomeCandidateQuestions[0];
      setOutcomeId(cand.question_id);
    }
    if (covariateCandidateQuestions.length > 0 && selectedCovariates.length === 0) {
      // Chọn 2-3 biến đồng biến đầu tiên không trùng Y và Z
      const initialCovs = covariateCandidateQuestions
        .filter(q => q.question_id !== treatmentId && q.question_id !== outcomeId)
        .slice(0, 3)
        .map(q => q.question_id);
      setSelectedCovariates(initialCovs);
    }
  }, [questions]);

  const toggleCovariate = (qid: string) => {
    if (selectedCovariates.includes(qid)) {
      setSelectedCovariates(selectedCovariates.filter(id => id !== qid));
    } else {
      setSelectedCovariates([...selectedCovariates, qid]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!treatmentId || !outcomeId) {
      setError('Vui lòng chọn Biến can thiệp (Treatment) và Biến kết quả (Outcome).');
      return;
    }
    if (treatmentId === outcomeId) {
      setError('Biến can thiệp và Biến kết quả không được trùng nhau.');
      return;
    }
    if (selectedCovariates.length === 0) {
      setError('Vui lòng chọn ít nhất 1 Biến kiểm soát đồng biến (Covariate).');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runPropensityMatching(surveyId, {
        treatment_question_id: treatmentId,
        treatment_value: treatmentValue,
        outcome_question_id: outcomeId,
        covariate_question_ids: selectedCovariates,
        caliper_factor: caliperFactor,
        scope
      });

      if (res.status !== 'SUCCESS') {
        setError(res.apa_narrative || 'Không thể thực hiện phân tích so khớp điểm xu hướng.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi gọi API phân tích so khớp điểm xu hướng PSM.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2000);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm mb-8 transition-colors">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-6 border-b border-slate-100 dark:border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 rounded-xl">
              <Crosshair className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Suy Luận Nhân Quả: So Khớp Điểm Xu Hướng (PSM) & Trọng Số IPW
                <span className="text-xs px-2.5 py-0.5 font-medium rounded-full bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300">
                  Rosenbaum & Rubin (1983)
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Đánh giá tác động can thiệp nhân quả (ATT) trên dữ liệu quan sát bằng cách khử độ lệch chọn mẫu (selection bias) qua Greedy Nearest Neighbor Matching (Austin 2011) và Inverse Probability Weighting.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start lg:self-auto">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="px-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Chỉ phản hồi chuẩn hóa (Verified Clean)</option>
          </select>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-4 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <PlayIcon className="w-3.5 h-3.5" />}
            Chạy Phân Tích PSM
          </button>
        </div>
      </div>

      {/* Control Configuration Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 py-5 border-b border-slate-100 dark:border-slate-800">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
            Biến Can Thiệp Z (Treatment)
          </label>
          <select
            value={treatmentId}
            onChange={(e) => setTreatmentId(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            {treatmentCandidateQuestions.map((q) => (
              <option key={q.question_id} value={q.question_id}>
                {q.question_title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
            Giá Trị Nhóm Can Thiệp (Treatment Value)
          </label>
          <input
            type="text"
            value={treatmentValue}
            onChange={(e) => setTreatmentValue(e.target.value)}
            placeholder="1 hoặc mã lựa chọn"
            className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
            Biến Kết Quả Y (Outcome)
          </label>
          <select
            value={outcomeId}
            onChange={(e) => setOutcomeId(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            {outcomeCandidateQuestions.map((q) => (
              <option key={q.question_id} value={q.question_id}>
                {q.question_title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Độ rộng Caliper (Austin 2011)
            </label>
            <span className="text-xs font-mono font-medium text-indigo-600 dark:text-indigo-400">
              {caliperFactor.toFixed(2)} × SD(logit)
            </span>
          </div>
          <input
            type="range"
            min="0.05"
            max="0.50"
            step="0.05"
            value={caliperFactor}
            onChange={(e) => setCaliperFactor(parseFloat(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>0.05 (Chặt chẽ)</span>
            <span>0.20 (Khuyến nghị Austin)</span>
            <span>0.50 (Mở rộng)</span>
          </div>
        </div>
      </div>

      {/* Covariates Multi-Selection Area */}
      <div className="py-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-indigo-500" />
            Các Biến Kiểm Soát Đồng Biến X (Covariates to Balance)
          </label>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Đã chọn {selectedCovariates.length} biến
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {covariateCandidateQuestions
            .filter(q => q.question_id !== treatmentId && q.question_id !== outcomeId)
            .map((q) => {
              const isSelected = selectedCovariates.includes(q.question_id);
              return (
                <button
                  key={q.question_id}
                  type="button"
                  onClick={() => toggleCovariate(q.question_id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3" />}
                  {q.question_title}
                </button>
              );
            })}
        </div>
      </div>

      {error && (
        <div className="my-4 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="mt-6 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Số Cặp So Khớp (Matched Pairs)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {result.matched_pairs_count}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  / {result.sample_treated} can thiệp
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Tỷ lệ ghép thành công: {result.sample_treated ? Math.round(((result.matched_pairs_count || 0) / result.sample_treated) * 100) : 0}%
              </p>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40">
              <span className="text-xs font-medium text-indigo-700 dark:text-indigo-300 block mb-1">
                Tác Động Can Thiệp (ATT Matched)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                  {result.matched_att && result.matched_att.estimate > 0 ? '+' : ''}
                  {result.matched_att ? result.matched_att.estimate.toFixed(3) : '—'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  result.matched_att?.is_significant
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                }`}>
                  {result.matched_att?.is_significant ? 'p < 0.05' : 'p ≥ 0.05'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                95% CI: [{result.matched_att?.ci_95_lower?.toFixed(2) ?? '—'}, {result.matched_att?.ci_95_upper?.toFixed(2) ?? '—'}]
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Đối Sánh Trọng Số IPW ATT
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-800 dark:text-slate-200">
                  {result.ipw_att && result.ipw_att.estimate > 0 ? '+' : ''}
                  {result.ipw_att ? result.ipw_att.estimate.toFixed(3) : '—'}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  (SE: {result.ipw_att?.se?.toFixed(3) ?? '—'})
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Chênh lệch thô chưa ghép: {result.unadjusted_effect?.raw_difference?.toFixed(3) ?? '—'}
              </p>
            </div>

            <div className={`p-4 rounded-xl border ${
              result.balance_summary?.all_balanced
                ? 'bg-emerald-50/50 dark:bg-emerald-950/30 border-emerald-100 dark:border-emerald-900/40'
                : 'bg-amber-50/50 dark:bg-amber-950/30 border-amber-100 dark:border-amber-900/40'
            }`}>
              <span className={`text-xs font-medium block mb-1 ${
                result.balance_summary?.all_balanced
                  ? 'text-emerald-700 dark:text-emerald-300'
                  : 'text-amber-700 dark:text-amber-300'
              }`}>
                Chẩn Đoán Cân Bằng Đồng Biến
              </span>
              <div className="flex items-baseline gap-2">
                <span className={`text-2xl font-bold ${
                  result.balance_summary?.all_balanced
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-amber-600 dark:text-amber-400'
                }`}>
                  {result.balance_summary?.balanced_covariates ?? 0} / {result.balance_summary?.total_covariates ?? 0}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">đạt chuẩn</span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Độ lệch tối đa: |SMD| = {result.balance_summary?.max_matched_smd?.toFixed(3) ?? '0.000'} (&lt;0.10)
              </p>
            </div>
          </div>

          {/* Covariate Balance Diagnostics Table */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-3.5 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-500" />
                Bảng Kiểm Định Cân Bằng Đồng Biến Trước vs Sau So Khớp (Austin 2011)
              </h4>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                Ngưỡng đạt: |SMD| &lt; 0.10 & 0.50 &le; VR &le; 2.0
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/50 dark:bg-slate-800/40 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 font-semibold">
                  <tr>
                    <th className="py-2.5 px-4">Biến Đồng Biến (Covariate)</th>
                    <th className="py-2.5 px-3 text-right">Treated Mean</th>
                    <th className="py-2.5 px-3 text-right">Control Mean</th>
                    <th className="py-2.5 px-3 text-right">Raw SMD</th>
                    <th className="py-2.5 px-3 text-right">Matched SMD</th>
                    <th className="py-2.5 px-3 text-right">Matched VR</th>
                    <th className="py-2.5 px-3 text-right">% Giảm Độ Lệch</th>
                    <th className="py-2.5 px-4 text-center">Trạng Thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                  {result.covariate_balance?.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 px-4 font-sans font-medium text-slate-800 dark:text-slate-200">
                        {row.covariate}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                        {row.matched_treated_mean.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                        {row.matched_control_mean.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-amber-600 dark:text-amber-400">
                        {row.raw_smd > 0 ? '+' : ''}{row.raw_smd.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-indigo-600 dark:text-indigo-400">
                        {row.matched_smd > 0 ? '+' : ''}{row.matched_smd.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                        {row.matched_variance_ratio.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-emerald-600 dark:text-emerald-400 font-semibold">
                        {row.pct_bias_reduction.toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-4 text-center font-sans">
                        {row.is_balanced ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                            <CheckCircle2 className="w-3 h-3" /> Cân bằng
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                            <AlertTriangle className="w-3 h-3" /> Lệch
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Visual Diagnostics: Love Plot & Common Support Histogram */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Vector Love Plot */}
            <div className="p-5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-800/30">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-indigo-500" />
                  Biểu Đồ Love Plot: Chuẩn Hóa Chênh Lệch Trung Bình (|SMD|)
                </h4>
                <div className="flex items-center gap-3 text-[11px]">
                  <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" /> Trước ghép (Raw)
                  </span>
                  <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Sau ghép (Matched)
                  </span>
                </div>
              </div>

              {/* Love Plot SVG */}
              <div className="h-64 w-full flex flex-col justify-center">
                <svg viewBox="0 0 450 180" className="w-full h-full overflow-visible">
                  {/* Background Threshold Band [-0.10, +0.10] */}
                  {/* Scale: x=0 is center at 225px, scale = 150px per 0.5 SMD */}
                  <rect x="195" y="10" width="60" height="150" fill="currentColor" className="text-emerald-500/10 dark:text-emerald-400/10" rx="4" />
                  <line x1="225" y1="10" x2="225" y2="160" stroke="currentColor" className="text-slate-300 dark:text-slate-600" strokeDasharray="3 3" />
                  <line x1="195" y1="10" x2="195" y2="160" stroke="currentColor" className="text-emerald-400/60 dark:text-emerald-500/40" strokeDasharray="2 2" />
                  <line x1="255" y1="10" x2="255" y2="160" stroke="currentColor" className="text-emerald-400/60 dark:text-emerald-500/40" strokeDasharray="2 2" />

                  {/* Threshold labels */}
                  <text x="195" y="172" textAnchor="middle" fontSize="9" className="fill-emerald-600 font-mono">-0.10</text>
                  <text x="225" y="172" textAnchor="middle" fontSize="9" className="fill-slate-400 font-mono">0.0</text>
                  <text x="255" y="172" textAnchor="middle" fontSize="9" className="fill-emerald-600 font-mono">+0.10</text>

                  {/* Covariate points */}
                  {result.love_plot?.map((item, idx) => {
                    const y = 30 + idx * 35;
                    const rawX = Math.max(20, Math.min(430, 225 + (item.raw_smd / 0.5) * 150));
                    const matchedX = Math.max(20, Math.min(430, 225 + (item.matched_smd / 0.5) * 150));

                    return (
                      <g key={idx}>
                        {/* Connecting line */}
                        <line x1={rawX} y1={y} x2={matchedX} y2={y} stroke="currentColor" className="text-slate-300 dark:text-slate-600" strokeWidth="1.5" />
                        
                        {/* Covariate label */}
                        <text x="15" y={y - 8} fontSize="10" className="fill-slate-700 dark:fill-slate-300 font-medium font-sans">
                          {item.covariate}
                        </text>

                        {/* Raw point */}
                        <circle cx={rawX} cy={y} r="5" className="fill-amber-500 stroke-white dark:stroke-slate-900" strokeWidth="1.5" />

                        {/* Matched point */}
                        <circle cx={matchedX} cy={y} r="5" className="fill-emerald-500 stroke-white dark:stroke-slate-900" strokeWidth="1.5" />
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>

            {/* Common Support Overlap Distribution */}
            <div className="p-5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-800/30">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                  <Percent className="w-4 h-4 text-indigo-500" />
                  Vùng Hỗ Trợ Chung (Common Support Propensity Overlap)
                </h4>
                <div className="flex items-center gap-3 text-[11px]">
                  <span className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400">
                    <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500 inline-block" /> Treated
                  </span>
                  <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
                    <span className="w-2.5 h-2.5 rounded-sm bg-slate-400 inline-block" /> Control
                  </span>
                </div>
              </div>

              <div className="space-y-2 mt-4">
                {result.common_support_overlap?.map((bin, idx) => {
                  const maxCount = Math.max(
                    ...result.common_support_overlap!.map(b => Math.max(b.treated_count, b.control_count)),
                    1
                  );
                  const treatedPct = (bin.treated_count / maxCount) * 100;
                  const controlPct = (bin.control_count / maxCount) * 100;

                  return (
                    <div key={idx} className="flex items-center gap-2 text-[11px]">
                      <span className="w-20 font-mono text-slate-500 dark:text-slate-400 text-right shrink-0">
                        {bin.bin_label}
                      </span>
                      <div className="flex-1 space-y-1">
                        <div className="w-full bg-slate-200 dark:bg-slate-700/60 rounded-full h-2 overflow-hidden flex">
                          <div
                            className="bg-indigo-500 h-2 rounded-full transition-all"
                            style={{ width: `${treatedPct}%` }}
                          />
                        </div>
                        <div className="w-full bg-slate-200 dark:bg-slate-700/60 rounded-full h-2 overflow-hidden flex">
                          <div
                            className="bg-slate-400 dark:bg-slate-500 h-2 rounded-full transition-all"
                            style={{ width: `${controlPct}%` }}
                          />
                        </div>
                      </div>
                      <span className="w-12 text-slate-600 dark:text-slate-300 font-mono text-right text-[10px] shrink-0">
                        {bin.treated_count} / {bin.control_count}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* APA 7th Edition Narrative Summary */}
          {result.apa_narrative && (
            <div className="p-5 rounded-xl border border-indigo-100 dark:border-indigo-900/50 bg-indigo-50/30 dark:bg-indigo-950/20">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <h4 className="text-xs font-bold text-indigo-900 dark:text-indigo-200">
                    Báo Cáo Thuyết Minh Chuẩn APA 7th Edition & Khuyến Nghị Học Thuật
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs rounded-md border border-indigo-200 dark:border-indigo-800 bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-slate-800 flex items-center gap-1 transition-colors"
                >
                  {copiedApa ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  {copiedApa ? 'Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 font-serif whitespace-pre-line">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

function PlayIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  );
}
