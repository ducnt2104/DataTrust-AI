import React, { useState, useEffect } from 'react';
import {
  GitFork,
  FlaskConical,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Copy,
  Check,
  RefreshCw,
  Info,
  Scale,
  TrendingUp,
  Percent,
  BarChart3,
  BookOpen
} from 'lucide-react';
import { api } from '../api/client';
import { SplitBallotReport } from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
  options?: string[];
}

interface Props {
  surveyId: string;
  questions: QuestionItem[];
}

export const SplitBallotExperimentCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [selectedQuestionId, setSelectedQuestionId] = useState<string>(questions[0]?.id || '');
  const [scope, setScope] = useState<'verified_clean' | 'all'>('verified_clean');
  const [report, setReport] = useState<SplitBallotReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    if (questions.length > 0 && !selectedQuestionId) {
      setSelectedQuestionId(questions[0].id);
    }
  }, [questions, selectedQuestionId]);

  useEffect(() => {
    if (selectedQuestionId) {
      loadSplitBallot();
    }
  }, [surveyId, selectedQuestionId, scope]);

  const loadSplitBallot = async () => {
    if (!selectedQuestionId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSplitBallotAnalysis(surveyId, selectedQuestionId, scope);
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'Không thể tải phân tích thử nghiệm tách phiếu.');
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!report?.apa_narrative) return;
    navigator.clipboard.writeText(report.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const distortionBadge = (level: string) => {
    switch (level) {
      case 'FRAME_ROBUST':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dot: 'bg-emerald-500',
          icon: CheckCircle2,
          text: 'Kháng đóng khung'
        };
      case 'MODERATELY_SENSITIVE':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          dot: 'bg-amber-500',
          icon: AlertTriangle,
          text: 'Nhạy cảm vừa phải'
        };
      case 'HIGHLY_PLASTIC':
      default:
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          dot: 'bg-rose-500',
          icon: AlertOctagon,
          text: 'Rất biến dạng'
        };
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-slate-100 gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-violet-50 text-violet-600 border border-violet-100 mt-0.5">
            <GitFork className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Thử Nghiệm Tách Phiếu & Khảo Nghiệm Từ Ngữ (Split-Ballot A/B Experiment)
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-violet-100 text-violet-800 rounded-full uppercase tracking-wider">
                Phương pháp luận Schuman & Presser
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Đo lường độ nhạy cảm của người trả lời trước các cách diễn đạt (Framing Effect) qua Welch's T-Test, Chi-Square và Chỉ số Biến Dạng Từ Ngữ (MWDI).
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Scope switch */}
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5 text-xs font-medium">
            <button
              onClick={() => setScope('verified_clean')}
              className={`px-3 py-1 rounded-md transition-all ${
                scope === 'verified_clean'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Dữ liệu sạch
            </button>
            <button
              onClick={() => setScope('all')}
              className={`px-3 py-1 rounded-md transition-all ${
                scope === 'all'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Tất cả phản hồi
            </button>
          </div>

          <button
            onClick={loadSplitBallot}
            disabled={loading}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Làm mới phân tích tách phiếu"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Target Question Selector */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 bg-slate-50/80 rounded-xl border border-slate-200/60">
        <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5 shrink-0">
          <FlaskConical className="w-4 h-4 text-violet-600" />
          <span>Câu hỏi mục tiêu thử nghiệm:</span>
        </label>
        <select
          value={selectedQuestionId}
          onChange={(e) => setSelectedQuestionId(e.target.value)}
          className="flex-1 max-w-xl text-xs bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-violet-500"
        >
          {questions.map((q, idx) => (
            <option key={q.id} value={q.id}>
              Câu {idx + 1}: {q.title} ({q.question_type})
            </option>
          ))}
        </select>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start gap-2">
          <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <strong>Không thể tính toán thử nghiệm:</strong> {error}
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && !report && (
        <div className="py-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-violet-600" />
          <span>Đang trích xuất dữ liệu phân nhánh và tính toán thống kê đối sánh...</span>
        </div>
      )}

      {/* Results View */}
      {report && (
        <div className="space-y-6">
          {/* 4 Hero KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Arms Count & Balance */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Phân nhánh thử nghiệm
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">{report.arms_count}</span>
                <span className="text-xs text-slate-500 font-medium">nhánh A/B</span>
              </div>
              <p className="text-[11px] text-slate-500 line-clamp-1">
                {report.arms_summary.map((a) => `${a.arm_id}: n=${a.total_responses}`).join(' | ')}
              </p>
            </div>

            {/* KPI 2: Statistical Significance */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Mức độ sai biệt ý kiến
              </span>
              <div className="flex items-baseline gap-1.5">
                {report.comparison.comparison_type === 'numeric' ? (
                  <>
                    <span className="text-2xl font-black text-slate-900">
                      d = {report.comparison.details?.cohens_d ?? 'N/A'}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">Cohen's d</span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl font-black text-slate-900">
                      V = {report.comparison.details?.cramer_v ?? 'N/A'}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">Cramér's V</span>
                  </>
                )}
              </div>
              <p className="text-[11px] font-semibold">
                {report.comparison.details?.is_significant ? (
                  <span className="text-rose-600 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> p = {report.comparison.details?.p_value} (Có ý nghĩa)
                  </span>
                ) : (
                  <span className="text-emerald-600 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> p = {report.comparison.details?.p_value} (Không khác biệt)
                  </span>
                )}
              </p>
            </div>

            {/* KPI 3: MWDI Distortion Tier */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Chỉ số biến dạng (MWDI)
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">
                  {report.distortion_index?.mwdi.toFixed(3) ?? '0.000'}
                </span>
                <span className="text-xs text-slate-400 font-normal">/ 1.000</span>
              </div>
              {(() => {
                const b = distortionBadge(report.distortion_index?.level);
                return (
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${b.bg}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${b.dot}`} />
                    {b.text}
                  </span>
                );
              })()}
            </div>

            {/* KPI 4: Completion Rate Parity */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Đồng đều phản hồi
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">
                  {report.arms_summary[0] && report.arms_summary[1]
                    ? `${Math.abs(report.arms_summary[0].response_rate_pct - report.arms_summary[1].response_rate_pct).toFixed(1)}%`
                    : '0%'}
                </span>
                <span className="text-xs text-slate-500 font-medium">chênh lệch tỷ lệ</span>
              </div>
              <p className="text-[11px] text-slate-500">
                {report.arms_summary.map((a) => `${a.arm_id}: ${a.response_rate_pct}%`).join(' vs ')}
              </p>
            </div>
          </div>

          {/* Detailed Arms Comparison Panel */}
          {report.comparison.comparison_type === 'numeric' && report.comparison.details?.is_sufficient && (
            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-4">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Scale className="w-4 h-4 text-violet-600" />
                <span>Kiểm định Welch's Independent Samples T-Test (Định lượng thang đo)</span>
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Arm A */}
                <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <span className="text-xs font-bold text-slate-800">Nhánh Thử Nghiệm A (Cơ sở)</span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md">
                      N = {report.comparison.details.arm_a.count}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Điểm Trung Bình (Mean)</span>
                      <strong className="text-base text-slate-900">{report.comparison.details.arm_a.mean}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Độ Lệch Chuẩn (SD)</span>
                      <strong className="text-base text-slate-700">{report.comparison.details.arm_a.std_dev}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Sai Số Chuẩn (SE)</span>
                      <strong className="text-base text-slate-700">{report.comparison.details.arm_a.standard_error}</strong>
                    </div>
                  </div>
                </div>

                {/* Arm B */}
                <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <span className="text-xs font-bold text-slate-800">Nhánh Thử Nghiệm B (Biến thể hành văn)</span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 bg-violet-100 text-violet-800 rounded-md">
                      N = {report.comparison.details.arm_b.count}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Điểm Trung Bình (Mean)</span>
                      <strong className="text-base text-violet-700">{report.comparison.details.arm_b.mean}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Độ Lệch Chuẩn (SD)</span>
                      <strong className="text-base text-slate-700">{report.comparison.details.arm_b.std_dev}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Sai Số Chuẩn (SE)</span>
                      <strong className="text-base text-slate-700">{report.comparison.details.arm_b.standard_error}</strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* Welch's test metrics row */}
              <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs flex flex-wrap items-center justify-between gap-4">
                <div>
                  <span className="text-slate-400 mr-1.5">Chênh lệch trung bình:</span>
                  <strong className="text-slate-900">{report.comparison.details.mean_difference}</strong>
                </div>
                <div>
                  <span className="text-slate-400 mr-1.5">Thống kê t:</span>
                  <strong className="text-slate-900">{report.comparison.details.t_statistic}</strong>
                </div>
                <div>
                  <span className="text-slate-400 mr-1.5">Bậc tự do (df):</span>
                  <strong className="text-slate-900">{report.comparison.details.degrees_of_freedom}</strong>
                </div>
                <div>
                  <span className="text-slate-400 mr-1.5">95% CI:</span>
                  <strong className="text-slate-900">
                    [{report.comparison.details.confidence_interval_95[0]}, {report.comparison.details.confidence_interval_95[1]}]
                  </strong>
                </div>
              </div>
            </div>
          )}

          {/* Detailed Categorical Options Comparison Panel */}
          {report.comparison.comparison_type === 'categorical' && report.comparison.details?.is_sufficient && (
            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4 text-violet-600" />
                  <span>Phân Bố Tỷ Lệ Lựa Chọn Phương Án (Chi-Square & Total Variation Distance)</span>
                </h4>
                <div className="text-xs font-semibold text-slate-600">
                  chi-square = {report.comparison.details.chi_square} (df={report.comparison.details.degrees_of_freedom}), TVD = {report.comparison.details.total_variation_distance}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse border border-slate-200 rounded-lg overflow-hidden bg-white">
                  <thead className="bg-slate-100 text-slate-700 font-bold">
                    <tr>
                      <th className="py-2.5 px-3 border border-slate-200">Phương án câu hỏi</th>
                      <th className="py-2.5 px-3 border border-slate-200 text-center">
                        Nhánh A ({report.comparison.details.arm_a_total})
                      </th>
                      <th className="py-2.5 px-3 border border-slate-200 text-center">
                        Nhánh B ({report.comparison.details.arm_b_total})
                      </th>
                      <th className="py-2.5 px-3 border border-slate-200 text-center">
                        Độ lệch tỷ lệ (Shift Delta)
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.comparison.details.option_comparison.map((opt: any) => {
                      const diff = opt.difference_pct;
                      const isShiftHigh = Math.abs(diff) >= 10.0;
                      return (
                        <tr key={opt.option} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2 px-3 border border-slate-200 font-medium text-slate-800">
                            {opt.option}
                          </td>
                          <td className="py-2 px-3 border border-slate-200 text-center">
                            <span className="font-semibold text-slate-900">{opt.prop_a}%</span>
                            <span className="text-[10px] text-slate-400 block font-mono">({opt.count_a})</span>
                          </td>
                          <td className="py-2 px-3 border border-slate-200 text-center">
                            <span className="font-semibold text-violet-700">{opt.prop_b}%</span>
                            <span className="text-[10px] text-slate-400 block font-mono">({opt.count_b})</span>
                          </td>
                          <td className="py-2 px-3 border border-slate-200 text-center">
                            <span
                              className={`inline-block px-2 py-0.5 rounded font-mono font-bold text-[11px] ${
                                isShiftHigh
                                  ? diff > 0
                                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                    : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {diff > 0 ? `+${diff}%` : `${diff}%`}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Insufficient sample notice if any */}
          {report.comparison.details && !report.comparison.details.is_sufficient && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center gap-2">
              <Info className="w-4 h-4 shrink-0 text-amber-600" />
              <span>{report.comparison.details.message || 'Cần thu thập thêm phản hồi cho từng nhóm thử nghiệm.'}</span>
            </div>
          )}

          {/* Scientific Interpretation & Recommendation */}
          <div className="p-4 rounded-xl bg-violet-50/60 border border-violet-100 space-y-2">
            <div className="flex items-center gap-2 text-violet-900 font-bold text-xs">
              <Sparkles className="w-4 h-4 text-violet-600" />
              <span>Khuyến nghị phương pháp học thuật: {report.distortion_index?.classification_title}</span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {report.distortion_index?.scientific_interpretation}
            </p>
            <p className="text-xs text-slate-600 italic">
              <strong>Hành động đề xuất:</strong> {report.distortion_index?.methodological_recommendation}
            </p>
          </div>

          {/* APA 7th Edition Narrative Citation Box */}
          <div className="p-4 rounded-xl bg-slate-900 text-slate-100 space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-300">
                <BookOpen className="w-4 h-4" />
                <span>Trích dẫn báo cáo khoa học (APA 7th Edition Manuscript Citation)</span>
              </div>
              <button
                onClick={handleCopyAPA}
                className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors border border-slate-700"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Đã sao chép</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao chép APA</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs font-mono text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800/80 leading-relaxed selection:bg-indigo-600 selection:text-white">
              {report.apa_narrative}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
