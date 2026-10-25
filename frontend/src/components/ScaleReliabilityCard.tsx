import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Copy,
  Download,
  Check,
  HelpCircle,
  Sliders,
  TrendingUp,
  Award
} from 'lucide-react';
import { api } from '../api/client';
import { ScaleReliabilityResult, ScaleItemStatistic } from '../types/survey';

interface Props {
  surveyId: string;
}

export const ScaleReliabilityCard: React.FC<Props> = ({ surveyId }) => {
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [data, setData] = useState<ScaleReliabilityResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const loadReliability = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getScaleReliability(surveyId, scope);
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Không thể tải phân tích độ tin cậy thang đo.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReliability();
  }, [surveyId, scope]);

  const generateMarkdownTable = (): string => {
    if (!data || !data.item_statistics) return '';
    let md = `### Phân Tích Độ Tin Cậy Thang Đo (Cronbach's Alpha Reliability Analysis)\n\n`;
    md += `- **Hệ số Cronbach's Alpha (α)**: ${data.cronbach_alpha ?? 'N/A'}\n`;
    md += `- **Standardized Alpha**: ${data.standardized_alpha ?? 'N/A'}\n`;
    md += `- **Cỡ mẫu (N)**: ${data.n_samples} | **Số mục thang đo (K)**: ${data.k_items}\n`;
    md += `- **Giá trị trung bình thang đo**: ${data.scale_mean} (Độ lệch chuẩn: ${data.scale_std_dev})\n`;
    md += `- **Đánh giá học thuật**: ${data.academic_rating}\n\n`;

    md += `| Mục thang đo | Trung bình | Độ lệch chuẩn | Tương quan Biến - Tổng (r_it) | Alpha nếu loại bỏ (α_del) | Đánh giá |\n`;
    md += `| :--- | :---: | :---: | :---: | :---: | :--- |\n`;
    for (const item of data.item_statistics) {
      const alphaDel = item.alpha_if_item_deleted !== null ? item.alpha_if_item_deleted.toFixed(4) : '—';
      md += `| **${item.item_title}** | ${item.item_mean} | ${item.item_std_dev} | ${item.corrected_item_total_correlation} | ${alphaDel} | ${item.recommendation} |\n`;
    }
    md += `\n*Ghi chú*: Tiêu chuẩn Nunnally & Bernstein (1994) và Hair et al. (2010) khuyến nghị r_it ≥ 0.30 và α ≥ 0.70.\n`;
    return md;
  };

  const handleCopyMarkdown = () => {
    const md = generateMarkdownTable();
    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const handleDownloadCsv = () => {
    if (!data || !data.item_statistics) return;
    const header = ['"STT"', '"Mã biến"', '"Tên câu hỏi"', '"Trung bình"', '"Độ lệch chuẩn"', '"Phương sai"', '"Trung bình nếu bỏ"', '"Tương quan Biến-Tổng (r_it)"', '"Alpha nếu bỏ"', '"Khuyến nghị"'].join(',');
    const rows = data.item_statistics.map((it, idx) => [
      idx + 1,
      `"${it.item_id}"`,
      `"${it.item_title.replace(/"/g, '""')}"`,
      it.item_mean,
      it.item_std_dev,
      it.item_variance,
      it.scale_mean_if_deleted,
      it.corrected_item_total_correlation,
      it.alpha_if_item_deleted !== null ? it.alpha_if_item_deleted : '""',
      `"${it.recommendation.replace(/"/g, '""')}"`
    ].join(','));
    const csvContent = '\uFEFF' + [header, ...rows].join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cronbach_alpha_reliability_${surveyId.slice(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!loading && data && !data.is_sufficient && data.k_items < 2) {
    return null; // Không hiển thị nếu khảo sát không có đủ 2 câu hỏi thang đo
  }

  const alpha = data?.cronbach_alpha;

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-slate-900 text-base">
              Kiểm Định Độ Tin Cậy Thang Đo (Cronbach's Alpha &amp; Item Analysis)
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Đánh giá tính nhất quán nội tại thang đo, hệ số tương quan biến - tổng (r-item-total) và Alpha nếu loại bỏ mục theo chuẩn SPSS / Nunnally (1994)
          </p>
        </div>

        {/* Scope selector */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-medium self-start sm:self-auto">
          <button
            onClick={() => setScope('all')}
            className={`px-3 py-1 rounded-lg transition-colors ${
              scope === 'all' ? 'bg-white shadow-xs text-indigo-700 font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Tất cả phản hồi
          </button>
          <button
            onClick={() => setScope('verified_clean')}
            className={`px-3 py-1 rounded-lg transition-colors ${
              scope === 'verified_clean' ? 'bg-white shadow-xs text-emerald-700 font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Chỉ mẫu sạch (Verified Clean)
          </button>
        </div>
      </div>

      {loading && (
        <div className="p-8 flex items-center justify-center text-slate-400 text-xs gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
          <span>Đang tính toán hệ số tương quan biến - tổng và độ tin cậy thang đo...</span>
        </div>
      )}

      {error && !loading && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {data && !loading && data.is_sufficient && (
        <div className="space-y-5 animate-in fade-in duration-200">
          {/* Key Metric Overview Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {/* Cronbach's Alpha Hero */}
            <div className={`p-4 rounded-xl border text-center col-span-2 sm:col-span-1 shadow-2xs ${
              (alpha ?? 0) >= 0.80 ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950' :
              (alpha ?? 0) >= 0.70 ? 'bg-teal-50/70 border-teal-200 text-teal-950' :
              (alpha ?? 0) >= 0.60 ? 'bg-amber-50/70 border-amber-200 text-amber-950' :
              'bg-rose-50/70 border-rose-200 text-rose-950'
            }`}>
              <span className="text-[11px] font-semibold block opacity-80">Cronbach's Alpha (α)</span>
              <span className="text-2xl font-extrabold block mt-0.5 font-mono">
                {alpha != null ? alpha.toFixed(3) : '—'}
              </span>
              <span className="text-[10px] font-bold block mt-1 uppercase tracking-tight">
                {(alpha ?? 0) >= 0.80 ? 'Xuất sắc' : (alpha ?? 0) >= 0.70 ? 'Đạt chuẩn' : (alpha ?? 0) >= 0.60 ? 'Khám phá' : 'Chưa đạt'}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
              <span className="text-[11px] font-medium text-slate-500 block">Standardized α</span>
              <span className="text-lg font-bold text-slate-800 block mt-1 font-mono">
                {data.standardized_alpha !== null ? data.standardized_alpha.toFixed(3) : '—'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Dựa trên ma trận r</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
              <span className="text-[11px] font-medium text-slate-500 block">Mục thang đo (K)</span>
              <span className="text-lg font-bold text-indigo-600 block mt-1">
                {data.k_items} câu hỏi
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">N = {data.n_samples} mẫu</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
              <span className="text-[11px] font-medium text-slate-500 block">Trung bình Thang đo</span>
              <span className="text-lg font-bold text-slate-800 block mt-1">
                {data.scale_mean}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Tổng điểm TB</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
              <span className="text-[11px] font-medium text-slate-500 block">Độ lệch chuẩn Thang đo</span>
              <span className="text-lg font-bold text-slate-800 block mt-1">
                {data.scale_std_dev}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">s² = {data.scale_variance}</span>
            </div>
          </div>

          {/* Academic Interpretation Banner with Copy/Download Buttons */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-indigo-50/50 border border-indigo-100 text-xs">
            <div className="flex items-start gap-2.5">
              <Award className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-indigo-950 block">
                  Đánh giá Tâm trắc học: {data.academic_rating}
                </span>
                <p className="text-slate-600 leading-relaxed mt-0.5">
                  {data.interpretation}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-center">
              <button
                type="button"
                onClick={handleCopyMarkdown}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-all shadow-2xs"
                title="Sao chép bảng kết quả theo định dạng chuẩn APA Markdown"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
                <span>{copied ? 'Đã sao chép' : 'Bảng APA'}</span>
              </button>
              <button
                type="button"
                onClick={handleDownloadCsv}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-all shadow-2xs"
                title="Tải bảng kết quả phân tích độ tin cậy dạng tệp CSV"
              >
                <Download className="w-3.5 h-3.5 text-slate-500" />
                <span>CSV</span>
              </button>
            </div>
          </div>

          {/* Item-Total Statistics Table */}
          <div className="overflow-x-auto border border-slate-200 rounded-xl shadow-xs">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100/90 text-slate-700 border-b border-slate-200 font-bold">
                  <th className="p-3 w-10 text-center border-r border-slate-200">#</th>
                  <th className="p-3 border-r border-slate-200 min-w-[200px]">Mục câu hỏi thang đo</th>
                  <th className="p-3 text-center border-r border-slate-200 min-w-[85px]">Mean (x̄)</th>
                  <th className="p-3 text-center border-r border-slate-200 min-w-[85px]">Std Dev (s)</th>
                  <th className="p-3 text-center border-r border-slate-200 min-w-[110px]">Mean nếu bỏ</th>
                  <th className="p-3 text-center border-r border-slate-200 min-w-[140px]" title="Tương quan giữa điểm mục này và tổng điểm các mục còn lại (Nunnally khuyến nghị >= 0.30)">
                    Tương quan Biến - Tổng (r<sub>it</sub>)
                  </th>
                  <th className="p-3 text-center border-r border-slate-200 min-w-[125px]" title="Cronbach's Alpha của thang đo nếu loại bỏ câu hỏi này">
                    Alpha nếu loại bỏ (α<sub>del</sub>)
                  </th>
                  <th className="p-3 text-center min-w-[140px]">Khuyến nghị hiệu chỉnh</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.item_statistics.map((item, idx) => {
                  const isGoodR = item.corrected_item_total_correlation >= 0.30;
                  const isLowR = item.corrected_item_total_correlation < 0.20;
                  const willIncreaseAlpha = item.alpha_if_item_deleted !== null && alpha != null && item.alpha_if_item_deleted > alpha + 0.03;

                  return (
                    <tr key={item.item_id || idx} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3 text-center font-bold text-slate-400 border-r border-slate-200">
                        {idx + 1}
                      </td>
                      <td className="p-3 font-semibold text-slate-800 border-r border-slate-200">
                        <span>{item.item_title}</span>
                        <span className="block text-[10px] text-slate-400 font-mono mt-0.5">
                          ID: {item.item_id.slice(0, 12)}...
                        </span>
                      </td>
                      <td className="p-3 text-center font-bold text-slate-700 border-r border-slate-200">
                        {item.item_mean}
                      </td>
                      <td className="p-3 text-center text-slate-600 border-r border-slate-200 font-mono">
                        {item.item_std_dev}
                      </td>
                      <td className="p-3 text-center text-slate-600 border-r border-slate-200 font-mono">
                        {item.scale_mean_if_deleted}
                      </td>
                      <td className="p-3 text-center border-r border-slate-200">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold font-mono ${
                          isGoodR ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
                          isLowR ? 'bg-rose-100 text-rose-800 border border-rose-300' :
                          'bg-amber-100 text-amber-800 border border-amber-300'
                        }`}>
                          {item.corrected_item_total_correlation.toFixed(3)}
                        </span>
                      </td>
                      <td className="p-3 text-center border-r border-slate-200 font-mono font-bold">
                        {item.alpha_if_item_deleted !== null ? (
                          <span className={willIncreaseAlpha ? 'text-rose-600 font-extrabold' : 'text-slate-700'}>
                            {item.alpha_if_item_deleted.toFixed(3)}
                            {willIncreaseAlpha && (
                              <span className="block text-[9px] text-rose-600 font-normal">Tăng khi bỏ</span>
                            )}
                          </span>
                        ) : (
                          <span className="text-slate-400">N/A (K=2)</span>
                        )}
                      </td>
                      <td className="p-3 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                          item.status === 'GOOD' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                          item.status === 'CONSIDER_REVISE' ? 'bg-rose-50 text-rose-700 border border-rose-200 font-bold' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {item.status === 'GOOD' ? 'Đạt chuẩn (r ≥ 0.30)' :
                           item.status === 'CONSIDER_REVISE' ? 'Cân nhắc loại bỏ' :
                           'Chấp nhận được'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Academic References Footnote */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-[11px] text-slate-500 space-y-1">
            <span className="font-bold text-slate-700 block">Tiêu chuẩn phương pháp luận đo lường:</span>
            <p>
              • <strong>Cronbach, L. J. (1951)</strong>: <em>Coefficient alpha and the internal structure of tests.</em> Psychometrika, 16(3), 297-334.<br />
              • <strong>Nunnally, J. C., &amp; Bernstein, I. H. (1994)</strong>: <em>Psychometric theory (3rd ed.)</em>: Khuyến nghị hệ số tương quan biến - tổng hiệu chỉnh r_it ≥ 0.30 để bảo toàn tính đơn chiều của thang đo.<br />
              • <strong>Hair, J. F., et al. (2010)</strong>: <em>Multivariate data analysis</em>: Cronbach's Alpha $\ge 0.70$ là ngưỡng quy chuẩn để công bố kết quả nghiên cứu khoa học.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
