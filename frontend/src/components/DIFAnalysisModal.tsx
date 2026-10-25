import React, { useState } from 'react';
import {
  X,
  Scale,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Copy,
  Download,
  HelpCircle,
  Sparkles,
  ArrowRight,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import { api } from '../api/client';
import { DIFReport, DIFItemResult, QuestionStats } from '../types/survey';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  surveyId: string;
  questions: QuestionStats[];
}

export const DIFAnalysisModal: React.FC<Props> = ({
  isOpen,
  onClose,
  surveyId,
  questions
}) => {
  // Tìm các câu hỏi phân loại phù hợp làm grouping variable (có 2-10 options)
  const candidateGroupingQs = questions.filter(
    (q) => q.option_distribution && Object.keys(q.option_distribution).length >= 2 && Object.keys(q.option_distribution).length <= 10
  );

  const [selectedGroupingId, setSelectedGroupingId] = useState<string>(
    candidateGroupingQs.length > 0 ? candidateGroupingQs[0].question_id : ''
  );

  const selectedGroupingQ = candidateGroupingQs.find((q) => q.question_id === selectedGroupingId);
  const groupOptions = selectedGroupingQ?.option_distribution ? Object.keys(selectedGroupingQ.option_distribution) : [];

  const [referenceGroup, setReferenceGroup] = useState<string>(groupOptions[0] || '');
  const [focalGroup, setFocalGroup] = useState<string>(groupOptions[1] || '');
  const [scope, setScope] = useState<'verified_clean' | 'all'>('verified_clean');
  const [strataCount, setStrataCount] = useState<number>(4);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<DIFReport | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleRunDIF = async () => {
    if (!selectedGroupingId) {
      setError('Vui lòng chọn câu hỏi phân nhóm nhân khẩu học.');
      return;
    }
    if (!referenceGroup || !focalGroup) {
      setError('Vui lòng chọn đầy đủ Nhóm tham chiếu và Nhóm tâm điểm.');
      return;
    }
    if (referenceGroup === focalGroup) {
      setError('Nhóm tham chiếu và Nhóm tâm điểm phải khác nhau.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await api.getDIFAnalysis(
        surveyId,
        selectedGroupingId,
        referenceGroup,
        focalGroup,
        scope,
        strataCount
      );
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi tính toán kiểm định DIF.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (!report) return;
    const lines = [
      `### BÁO CÁO KIỂM ĐỊNH BẤT BIẾN ĐO LƯỜNG & HÀM MỤC SAI LỆCH (DIFFERENTIAL ITEM FUNCTIONING - DIF)`,
      `**Phương pháp:** Thống kê Mantel-Haenszel (Holland & Thayer, 1988) & Chuẩn ETS (Educational Testing Service)`,
      `**Biến phân nhóm:** ${report.grouping_variable_title} | **Tham chiếu (Ref):** ${report.reference_group} (N=${report.sample_reference}) | **Tâm điểm (Focal):** ${report.focal_group} (N=${report.sample_focal})`,
      `**Kết luận tổng quan:** ${report.summary}`,
      ``,
      `| Câu hỏi thang đo | Ngưỡng (M) | χ² MH | p-value | Tỷ số chênh (α) | Delta ETS (Δ) | Phân loại ETS | Nhóm ưu thế | Khuyến nghị hành động |`,
      `| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |`
    ];

    report.items.forEach((it) => {
      const clean_title = it.question_title.replace(/\|/g, '\\|');
      lines.push(
        `| ${clean_title} | ${it.median_threshold} | ${it.chi2_mh} | ${it.p_value} | ${it.alpha_odds_ratio} | ${it.delta_ets} | **Class ${it.ets_class}** | ${it.favored_group} | ${it.action_recommendation} |`
      );
    });

    navigator.clipboard.writeText(lines.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto"
      role="dialog"
      aria-modal="true"
    >
      <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-900 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 border border-indigo-400/30 rounded-xl">
              <Scale className="w-5 h-5 text-indigo-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">
                  Kiểm Định Bất Biến Đo Lường & Sai Lệch Câu Hỏi (DIF Engine)
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 font-mono font-bold">
                  Mantel-Haenszel & ETS Standard
                </span>
              </div>
              <p className="text-xs text-slate-300">
                Xác định câu hỏi thang đo có thiên vị bất công đối với một nhóm dân số học hay không
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs bg-slate-50/50">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* 1. Thiết lập biến phân nhóm và 2 nhóm đối chiếu */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4">
            <span className="font-bold text-slate-800 text-xs block">
              1. Lựa Chọn Cặp Nhóm Đối Kháng Để Thẩm Định Tính Công Bằng (DIF Parameters)
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                  Biến nhân khẩu học:
                </label>
                <select
                  value={selectedGroupingId}
                  onChange={(e) => {
                    setSelectedGroupingId(e.target.value);
                    const q = candidateGroupingQs.find((item) => item.question_id === e.target.value);
                    const opts = q?.option_distribution ? Object.keys(q.option_distribution) : [];
                    setReferenceGroup(opts[0] || '');
                    setFocalGroup(opts[1] || '');
                  }}
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:outline-hidden"
                >
                  {candidateGroupingQs.map((q) => (
                    <option key={q.question_id} value={q.question_id}>
                      {q.question_title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                  Nhóm tham chiếu (Reference):
                </label>
                <select
                  value={referenceGroup}
                  onChange={(e) => setReferenceGroup(e.target.value)}
                  className="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-800 focus:outline-hidden"
                >
                  {groupOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                  Nhóm tâm điểm (Focal):
                </label>
                <select
                  value={focalGroup}
                  onChange={(e) => setFocalGroup(e.target.value)}
                  className="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-800 focus:outline-hidden"
                >
                  {groupOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                  Phạm vi mẫu & Phân tầng:
                </label>
                <div className="flex items-center gap-1.5">
                  <select
                    value={scope}
                    onChange={(e) => setScope(e.target.value as any)}
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800"
                  >
                    <option value="verified_clean">Mẫu sạch</option>
                    <option value="all">Tất cả mẫu</option>
                  </select>
                  <select
                    value={strataCount}
                    onChange={(e) => setStrataCount(Number(e.target.value))}
                    className="w-20 p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono font-bold text-slate-800"
                    title="Số phân tầng điểm tổng (Quartiles / Quintiles)"
                  >
                    <option value={3}>3 tầng</option>
                    <option value={4}>4 tầng</option>
                    <option value={5}>5 tầng</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                onClick={handleRunDIF}
                disabled={loading}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-xs shadow-xs disabled:opacity-50 transition-all"
              >
                <Sparkles className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>{loading ? 'Đang phân tích Mantel-Haenszel...' : 'Chạy Kiểm Định DIF (Mantel-Haenszel)'}</span>
              </button>
            </div>
          </div>

          {/* 2. Kết Quả Kiểm Định */}
          {report && (
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4 animate-in fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
                <div className="flex items-center gap-2">
                  {report.overall_verdict === 'ĐẠT_CHUẨN_BẤT_BIẾN_ĐO_LƯỜNG' ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  ) : report.overall_verdict === 'CÓ_THIÊN_LỆCH_VỪA_PHẢI' ? (
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                  ) : (
                    <AlertOctagon className="w-5 h-5 text-rose-600" />
                  )}
                  <div>
                    <h4 className="font-bold text-slate-900 text-xs">
                      Kết Luận Bất Biến Đo Lường (Measurement Invariance Verdict)
                    </h4>
                    <span className="text-[11px] text-slate-500">
                      Mẫu đánh giá: {report.total_eval_sample} (Ref: {report.sample_reference} | Focal: {report.sample_focal}) • Phân tầng: {report.strata_count}
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleCopyMarkdown}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>{copied ? 'Đã sao chép!' : 'Sao Chép Bảng Báo Cáo APA'}</span>
                </button>
              </div>

              {/* Status Alert Banner */}
              <div
                className={`p-3.5 rounded-xl border flex items-start gap-3 ${
                  report.overall_verdict === 'ĐẠT_CHUẨN_BẤT_BIẾN_ĐO_LƯỜNG'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                    : report.overall_verdict === 'CÓ_THIÊN_LỆCH_VỪA_PHẢI'
                    ? 'bg-amber-50 border-amber-200 text-amber-900'
                    : 'bg-rose-50 border-rose-200 text-rose-900'
                }`}
              >
                <ShieldCheck className="w-5 h-5 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <span className="font-bold text-xs block">
                    {report.overall_verdict === 'ĐẠT_CHUẨN_BẤT_BIẾN_ĐO_LƯỜNG'
                      ? '100% CÂU HỎI ĐẠT CHUẨN CÔNG BẰNG ĐO LƯỜNG (CLASS A)'
                      : report.overall_verdict === 'CÓ_THIÊN_LỆCH_VỪA_PHẢI'
                      ? 'PHÁT HIỆN THIÊN LỆCH MỨC ĐỘ VỪA PHẢI (CLASS B)'
                      : 'CẢNH BÁO: PHÁT HIỆN THIÊN LỆCH NGHIÊM TRỌNG (CLASS C)'}
                  </span>
                  <p className="text-[11px] leading-relaxed">{report.summary}</p>
                </div>
              </div>

              {/* 3 ETS Class Breakdown Counters */}
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-200">
                  <span className="text-[10px] text-emerald-700 block uppercase font-bold">Class A (Công Bằng)</span>
                  <span className="text-xl font-extrabold text-emerald-700 font-mono">{report.class_a_count}</span>
                  <span className="text-[10px] text-emerald-600 block mt-0.5">|Δ| &lt; 1.0 hoặc p ≥ .05</span>
                </div>

                <div className="p-3 bg-amber-50/60 rounded-xl border border-amber-200">
                  <span className="text-[10px] text-amber-700 block uppercase font-bold">Class B (Vừa Phải)</span>
                  <span className="text-xl font-extrabold text-amber-700 font-mono">{report.class_b_count}</span>
                  <span className="text-[10px] text-amber-600 block mt-0.5">1.0 ≤ |Δ| &lt; 1.5</span>
                </div>

                <div className="p-3 bg-rose-50/60 rounded-xl border border-rose-200">
                  <span className="text-[10px] text-rose-700 block uppercase font-bold">Class C (Nghiêm Trọng)</span>
                  <span className="text-xl font-extrabold text-rose-700 font-mono">{report.class_c_count}</span>
                  <span className="text-[10px] text-rose-600 block mt-0.5">|Δ| ≥ 1.5 & p &lt; .05</span>
                </div>
              </div>

              {/* Items Table */}
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Câu Hỏi Thang Đo</th>
                      <th className="py-2.5 px-3 text-center">Ngưỡng (M)</th>
                      <th className="py-2.5 px-3 text-center font-mono">χ² MH (p)</th>
                      <th className="py-2.5 px-3 text-center font-mono">Odds (α)</th>
                      <th className="py-2.5 px-3 text-center font-mono">Delta ETS (Δ)</th>
                      <th className="py-2.5 px-3 text-center">Phân Loại ETS</th>
                      <th className="py-2.5 px-3 text-center">Nhóm Ưu Thế</th>
                      <th className="py-2.5 px-3">Khuyến Nghị Hành Động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {report.items.map((it) => (
                      <tr key={it.question_id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-medium text-slate-800 max-w-xs truncate" title={it.question_title}>
                          {it.question_title}
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono text-slate-500">
                          {it.median_threshold}
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono">
                          <span className={it.is_statistically_significant ? 'text-rose-600 font-bold' : 'text-slate-600'}>
                            {it.chi2_mh} (p={it.p_value})
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono text-slate-700">
                          {it.alpha_odds_ratio}
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono font-bold text-slate-800">
                          {it.delta_ets}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                              it.ets_class === 'A'
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : it.ets_class === 'B'
                                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                                : 'bg-rose-100 text-rose-800 border border-rose-300'
                            }`}
                          >
                            Class {it.ets_class}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-center text-slate-600 text-[11px]">
                          {it.favored_group}
                        </td>
                        <td className="py-2.5 px-3 text-slate-700 text-[11px]">
                          {it.action_recommendation}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Methodology footnote */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[10px] text-slate-500 space-y-1">
                <p>
                  <strong>Tài liệu tham chiếu chuẩn:</strong> Holland, P. W., & Thayer, D. T. (1988). Differential item functioning and the Mantel-Haenszel procedure. <em>Test validity</em>, 129-145.
                </p>
                <p>
                  Tiêu chuẩn phân loại 3 mức độ của Viện Khảo thí Giáo dục Hoa Kỳ (ETS): <strong>Class A</strong> (|Δ| &lt; 1.0 hoặc p ≥ .05, không thiên lệch đáng kể), <strong>Class B</strong> (1.0 ≤ |Δ| &lt; 1.5, thiên lệch vừa phải), <strong>Class C</strong> (|Δ| ≥ 1.5 và p &lt; .05, thiên lệch lớn).
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 bg-white text-xs">
          <span className="text-slate-400 font-mono text-[10px]">
            DataTrust Psychometric & Fairness Engine v1.0
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
