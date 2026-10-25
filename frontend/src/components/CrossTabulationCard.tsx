import React, { useEffect, useState } from 'react';
import { Table, BarChart2, Info, CheckCircle2, AlertCircle, RefreshCw, Filter, Flame, Copy, Download, Check, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, CrosstabAnalysisResult, CrosstabCell } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

type HeatmapMode = 'counts' | 'row_pct' | 'residuals';

export const CrossTabulationCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc các câu hỏi có thể phân tích danh mục (single_choice, multiple_choice, rating, nps, dropdown)
  const eligibleQuestions = questions.filter((q) =>
    ['single_choice', 'multiple_choice', 'rating', 'nps', 'dropdown'].includes(q.question_type) ||
    (q.option_distribution && Object.keys(q.option_distribution).length > 0)
  );

  const [rowVarId, setRowVarId] = useState<string>('');
  const [colVarId, setColVarId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [heatmapMode, setHeatmapMode] = useState<HeatmapMode>('counts');
  const [data, setData] = useState<CrosstabAnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Khởi tạo mặc định chọn 2 câu hỏi đầu tiên
  useEffect(() => {
    if (eligibleQuestions.length >= 2) {
      if (!rowVarId || !eligibleQuestions.some(q => q.question_id === rowVarId)) {
        setRowVarId(eligibleQuestions[0].question_id);
      }
      if (!colVarId || colVarId === eligibleQuestions[0].question_id || !eligibleQuestions.some(q => q.question_id === colVarId)) {
        setColVarId(eligibleQuestions[1].question_id);
      }
    }
  }, [questions]);

  useEffect(() => {
    if (rowVarId && colVarId && rowVarId !== colVarId) {
      loadCrosstab();
    }
  }, [surveyId, rowVarId, colVarId, scope]);

  const loadCrosstab = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getCrosstabAnalysis(surveyId, rowVarId, colVarId, scope);
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Không thể tạo bảng chéo');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const generateMarkdownTable = (): string => {
    if (!data) return '';
    let md = `### Bảng Chéo (Cross-Tabulation): ${data.variable_row.title} × ${data.variable_col.title}\n\n`;
    md += `| ${data.variable_row.title} | ` + data.variable_col.categories.join(' | ') + ' | Tổng hàng |\n';
    md += '| :--- | ' + data.variable_col.categories.map(() => ':---:').join(' | ') + ' | :---: |\n';
    for (const r of data.variable_row.categories) {
      const rowCells = data.variable_col.categories.map(c => {
        const cell = data.matrix?.[r]?.[c] || { observed: 0, expected: 0, row_percentage: 0 };
        return `${cell.observed} (Exp: ${cell.expected}, ${cell.row_percentage}%)`;
      });
      const rTotal = data.variable_row.totals[r] || 0;
      md += `| **${r}** | ` + rowCells.join(' | ') + ` | **${rTotal}** |\n`;
    }
    const colTotals = data.variable_col.categories.map(c => `**${data.variable_col.totals[c] || 0}**`);
    md += `| **Tổng cột** | ` + colTotals.join(' | ') + ` | **N = ${data.total_valid_samples}** |\n\n`;
    md += `**Chỉ số thống kê**:\n`;
    md += `- Chi-Square (χ²): ${data.chi_square_statistic} (df = ${data.degrees_of_freedom}, p = ${data.p_value})\n`;
    md += `- Cramer's V: ${data.cramers_v} (${data.association_strength})\n`;
    md += `- Diễn giải: ${data.interpretation}\n`;
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
    if (!data) return;
    const header = [data.variable_row.title, ...data.variable_col.categories, 'Tổng hàng'].map(s => `"${s.replace(/"/g, '""')}"`).join(',');
    const rows = data.variable_row.categories.map(r => {
      const cells = data.variable_col.categories.map(c => {
        const cell = data.matrix?.[r]?.[c] || { observed: 0 };
        return cell.observed;
      });
      const rTotal = data.variable_row.totals[r] || 0;
      return [`"${r.replace(/"/g, '""')}"`, ...cells, rTotal].join(',');
    });
    const colTotals = ['"Tổng cột"', ...data.variable_col.categories.map(c => data.variable_col.totals[c] || 0), data.total_valid_samples].join(',');
    const csvContent = '\uFEFF' + [header, ...rows, colTotals].join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crosstab_${surveyId.slice(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getCellClasses = (cell: CrosstabCell) => {
    if (heatmapMode === 'row_pct') {
      const pct = cell.row_percentage;
      if (pct >= 70) return { bg: 'bg-indigo-600 text-white', sub: 'text-indigo-100', highlight: 'text-white' };
      if (pct >= 45) return { bg: 'bg-indigo-400 text-white', sub: 'text-indigo-100', highlight: 'text-white' };
      if (pct >= 25) return { bg: 'bg-indigo-100 text-indigo-950 border-indigo-200', sub: 'text-indigo-700', highlight: 'text-indigo-900 font-bold' };
      if (pct > 0) return { bg: 'bg-indigo-50/60 text-slate-800', sub: 'text-slate-500', highlight: 'text-indigo-700' };
      return { bg: 'bg-slate-50/40 text-slate-400', sub: 'text-slate-400', highlight: 'text-slate-400' };
    }
    if (heatmapMode === 'residuals') {
      const res = cell.pearson_residual ?? 0;
      if (res >= 2.0) return { bg: 'bg-emerald-600 text-white shadow-xs', sub: 'text-emerald-100', highlight: 'text-white font-extrabold' };
      if (res >= 1.0) return { bg: 'bg-emerald-100 text-emerald-950 border-emerald-300', sub: 'text-emerald-800', highlight: 'text-emerald-900 font-bold' };
      if (res <= -2.0) return { bg: 'bg-rose-600 text-white shadow-xs', sub: 'text-rose-100', highlight: 'text-white font-extrabold' };
      if (res <= -1.0) return { bg: 'bg-amber-100 text-amber-950 border-amber-300', sub: 'text-amber-800', highlight: 'text-amber-900 font-bold' };
      return { bg: 'bg-slate-50/60 text-slate-800', sub: 'text-slate-400', highlight: 'text-slate-700' };
    }
    return { bg: 'bg-white hover:bg-slate-50 text-slate-900', sub: 'text-slate-400', highlight: 'text-indigo-600' };
  };

  if (eligibleQuestions.length < 2) {
    return null; // Khảo sát cần ít nhất 2 câu hỏi định danh/thứ bậc để phân tích chéo
  }

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Table className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-slate-900 text-base">
              Phân tích chéo biến số & Kiểm định Chi-Square (Cross-Tabulation)
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Xác lập mối tương quan độc lập giữa 2 câu hỏi định danh / thứ bậc theo chuẩn Don Dillman &amp; AAPOR
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

      {/* Selectors for Row and Col Variables */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200/80">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Biến số Hàng (Row Variable X):
          </label>
          <select
            value={rowVarId}
            onChange={(e) => setRowVarId(e.target.value)}
            className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2 font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {eligibleQuestions.map((q) => (
              <option key={q.question_id} value={q.question_id} disabled={q.question_id === colVarId}>
                {q.question_title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Biến số Cột (Column Variable Y):
          </label>
          <select
            value={colVarId}
            onChange={(e) => setColVarId(e.target.value)}
            className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2 font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {eligibleQuestions.map((q) => (
              <option key={q.question_id} value={q.question_id} disabled={q.question_id === rowVarId}>
                {q.question_title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="p-8 flex items-center justify-center text-slate-400 text-xs gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
          <span>Đang tính toán tần số kỳ vọng và thống kê Chi-Square...</span>
        </div>
      )}

      {error && !loading && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-5 animate-in fade-in duration-200">
          {/* Key Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-slate-900 text-white rounded-xl text-center shadow-xs">
            <div>
              <span className="text-[11px] text-slate-400 block">Cỡ mẫu hợp lệ (N)</span>
              <span className="text-lg font-bold text-white">{data.total_valid_samples}</span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Thống kê Chi-Square (χ²)</span>
              <span className="text-lg font-bold text-amber-400">{data.chi_square_statistic}</span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Bậc tự do (df) / p-value</span>
              <span className="text-lg font-bold text-indigo-300">
                df={data.degrees_of_freedom} | p={data.p_value}
              </span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Hệ số liên kết Cramer's V</span>
              <span className="text-lg font-bold text-emerald-400">{data.cramers_v}</span>
            </div>
          </div>

          {/* Statistical Result Badge & Heatmap Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <div className="flex items-center gap-2 flex-wrap">
              {data.is_statistically_significant ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Mối liên hệ có ý nghĩa thống kê (p &lt; 0.05)
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-200 text-slate-700">
                  <Info className="w-3.5 h-3.5 text-slate-500" />
                  Chưa đủ bằng chứng bác bỏ giả thuyết độc lập (p ≥ 0.05)
                </span>
              )}
              <span className="text-slate-600 font-medium hidden sm:inline">• {data.association_strength}</span>
            </div>

            {/* Heatmap Visual Switcher & Exports */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Heatmap Mode Pill Group */}
              <div className="flex items-center gap-1 bg-white border border-slate-200 p-0.5 rounded-lg text-[11px]">
                <button
                  type="button"
                  onClick={() => setHeatmapMode('counts')}
                  className={`px-2 py-0.5 rounded font-medium transition-colors ${
                    heatmapMode === 'counts' ? 'bg-slate-900 text-white font-bold' : 'text-slate-600 hover:text-slate-900'
                  }`}
                  title="Hiển thị tần số đếm quan sát và kỳ vọng"
                >
                  Số đếm
                </button>
                <button
                  type="button"
                  onClick={() => setHeatmapMode('row_pct')}
                  className={`flex items-center gap-1 px-2 py-0.5 rounded font-medium transition-colors ${
                    heatmapMode === 'row_pct' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-600 hover:text-slate-900'
                  }`}
                  title="Bản đồ nhiệt theo tỷ lệ % theo hàng"
                >
                  <Flame className="w-3 h-3 text-amber-300" />
                  Nhiệt độ %
                </button>
                <button
                  type="button"
                  onClick={() => setHeatmapMode('residuals')}
                  className={`flex items-center gap-1 px-2 py-0.5 rounded font-medium transition-colors ${
                    heatmapMode === 'residuals' ? 'bg-emerald-700 text-white font-bold' : 'text-slate-600 hover:text-slate-900'
                  }`}
                  title="Bản đồ thặng dư Pearson chuẩn hóa (Residuals: > +2.0 vượt trội, < -2.0 thiếu hụt)"
                >
                  <Sparkles className="w-3 h-3 text-emerald-200" />
                  Thặng dư (Residuals)
                </button>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={handleCopyMarkdown}
                  className="flex items-center gap-1 px-2 py-1 rounded bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-[11px] font-medium transition-colors shadow-2xs"
                  title="Sao chép bảng định dạng Markdown"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-slate-500" />}
                  <span>{copied ? 'Đã sao chép' : 'Markdown'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleDownloadCsv}
                  className="flex items-center gap-1 px-2 py-1 rounded bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-[11px] font-medium transition-colors shadow-2xs"
                  title="Tải bảng dạng tệp CSV"
                >
                  <Download className="w-3 h-3 text-slate-500" />
                  <span>CSV</span>
                </button>
              </div>
            </div>
          </div>

          {/* Heatmap Legend */}
          {heatmapMode !== 'counts' && (
            <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg bg-indigo-50/50 border border-indigo-100 text-[11px]">
              <span className="font-semibold text-slate-700">
                {heatmapMode === 'row_pct' ? 'Thang đo nhiệt độ % Hàng:' : 'Thang đo Thặng Dư Pearson (Z-residual):'}
              </span>
              {heatmapMode === 'row_pct' ? (
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-slate-100 border border-slate-200"></span> 0%</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-indigo-100 border border-indigo-200"></span> 25%</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-indigo-400"></span> 50%</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-indigo-600"></span> ≥75% (Tập trung cao)</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-rose-600"></span> &lt; -2.0 (Thiếu hụt p&lt;0.05)</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-100 border border-amber-300"></span> -1.0</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-slate-100 border border-slate-200"></span> 0.0 (Kỳ vọng)</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-100 border border-emerald-300"></span> +1.0</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-600"></span> &gt; +2.0 (Vượt trội p&lt;0.05)</span>
                </div>
              )}
            </div>
          )}

          {data.notice && (
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center gap-2">
              <Info className="w-4 h-4 text-amber-600 shrink-0" />
              <span>{data.notice}</span>
            </div>
          )}

          {/* Contingency Table Grid with Heatmap Cells */}
          <div className="overflow-x-auto border border-slate-200 rounded-xl shadow-xs">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100/90 text-slate-700 border-b border-slate-200">
                  <th className="p-3 font-bold border-r border-slate-200 bg-slate-100">
                    {data.variable_row.title} \ {data.variable_col.title}
                  </th>
                  {data.variable_col.categories.map((c: string) => (
                    <th key={c} className="p-3 font-bold text-center border-r border-slate-200 min-w-[115px]">
                      {c}
                    </th>
                  ))}
                  <th className="p-3 font-bold text-center bg-slate-200/70 min-w-[95px]">
                    Tổng hàng (Row Total)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.variable_row.categories.map((r: string) => {
                  const rTotal = data.variable_row.totals[r] || 0;
                  return (
                    <tr key={r} className="transition-colors">
                      <td className="p-3 font-semibold text-slate-800 border-r border-slate-200 bg-slate-50/50">
                        {r}
                      </td>
                      {data.variable_col.categories.map((c: string) => {
                        const cell = data.matrix?.[r]?.[c] || { observed: 0, expected: 0, row_percentage: 0, column_percentage: 0, total_percentage: 0, pearson_residual: 0 };
                        const styles = getCellClasses(cell);
                        return (
                          <td
                            key={c}
                            className={`p-2.5 text-center border-r border-slate-200 transition-all ${styles.bg}`}
                            title={`Quan sát: ${cell.observed} | Kỳ vọng: ${cell.expected} | % Hàng: ${cell.row_percentage}% | % Cột: ${cell.column_percentage}% | Thặng dư Pearson: ${cell.pearson_residual ?? 0}`}
                          >
                            <div className="font-extrabold text-sm">{cell.observed}</div>
                            <div className={`text-[10px] mt-0.5 ${styles.sub}`}>
                              Exp: {cell.expected}
                            </div>
                            <div className={`text-[10px] font-semibold mt-0.5 ${styles.highlight}`}>
                              {cell.row_percentage}% hàng
                            </div>
                            {cell.pearson_residual !== undefined && (
                              <div className={`text-[9px] font-mono mt-0.5 opacity-80 ${styles.sub}`}>
                                {cell.pearson_residual > 0 ? `+${cell.pearson_residual}` : cell.pearson_residual} res
                              </div>
                            )}
                          </td>
                        );
                      })}
                      <td className="p-3 text-center font-bold text-slate-900 bg-slate-50/80">
                        {rTotal}
                        <span className="block text-[10px] font-normal text-slate-400">
                          {data.total_valid_samples > 0 ? Math.round((rTotal / data.total_valid_samples) * 100) : 0}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-slate-100 text-slate-900 font-bold border-t border-slate-200">
                  <td className="p-3 border-r border-slate-200">Tổng cột (Col Total)</td>
                  {data.variable_col.categories.map((c: string) => {
                    const cTotal = data.variable_col.totals[c] || 0;
                    return (
                      <td key={c} className="p-3 text-center border-r border-slate-200">
                        {cTotal}
                        <span className="block text-[10px] font-normal text-slate-500">
                          {data.total_valid_samples > 0 ? Math.round((cTotal / data.total_valid_samples) * 100) : 0}%
                        </span>
                      </td>
                    );
                  })}
                  <td className="p-3 text-center text-sm font-extrabold text-indigo-700 bg-indigo-50 border-l border-indigo-200">
                    N = {data.total_valid_samples}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Academic Interpretation */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs text-slate-700 space-y-1">
            <span className="font-bold text-slate-900 block">Diễn giải thống kê (Scientific Interpretation):</span>
            <p className="leading-relaxed">{data.interpretation}</p>
          </div>
        </div>
      )}
    </div>
  );
};
