import React, { useState, useEffect } from 'react';
import {
  Grid,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  Info,
  TrendingUp,
  Table,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { CorrelationMatrixReport, CorrelationMatrixCell } from '../types/survey';

interface Props {
  surveyId: string;
}

export const CorrelationMatrixCard: React.FC<Props> = ({ surveyId }) => {
  const [method, setMethod] = useState<'pearson' | 'spearman'>('pearson');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [report, setReport] = useState<CorrelationMatrixReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [hoveredCell, setHoveredCell] = useState<{
    row: number;
    col: number;
    cell: CorrelationMatrixCell;
    var1_title: string;
    var2_title: string;
  } | null>(null);
  const [filterMode, setFilterMode] = useState<'all' | 'significant' | 'strong'>('all');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getCorrelationMatrix(surveyId, { method, scope });
      setReport(res);
    } catch (err: any) {
      setError(err?.message || 'Không thể tải dữ liệu phân tích tương quan.');
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [surveyId, method, scope]);

  const handleCopyAPA = () => {
    if (!report?.apa_interpretation) return;
    navigator.clipboard.writeText(report.apa_interpretation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  // Helper hàm sinh màu cho ô heatmap dựa trên hệ số tương quan r
  const getCellBgColor = (r: number) => {
    if (r === 1.0) return 'bg-indigo-600 text-white font-black';
    if (r > 0) {
      if (r >= 0.8) return 'bg-indigo-500 text-white font-bold';
      if (r >= 0.6) return 'bg-indigo-400 text-white font-semibold';
      if (r >= 0.4) return 'bg-indigo-200 text-indigo-950 font-medium';
      if (r >= 0.2) return 'bg-indigo-100 text-indigo-900';
      return 'bg-indigo-50/60 text-slate-700';
    } else if (r < 0) {
      const absR = Math.abs(r);
      if (absR >= 0.8) return 'bg-rose-500 text-white font-bold';
      if (absR >= 0.6) return 'bg-rose-400 text-white font-semibold';
      if (absR >= 0.4) return 'bg-rose-200 text-rose-950 font-medium';
      if (absR >= 0.2) return 'bg-rose-100 text-rose-900';
      return 'bg-rose-50/60 text-slate-700';
    }
    return 'bg-slate-50 text-slate-400';
  };

  const getSigStars = (cell: CorrelationMatrixCell) => {
    if (cell.correlation === 1.0) return '';
    if (cell.is_significant_001) return '***';
    if (cell.is_significant_01) return '**';
    if (cell.is_significant_05) return '*';
    return '';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mt-6">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 bg-gradient-to-r from-indigo-50/40 via-sky-50/20 to-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-indigo-600 text-white rounded-lg shadow-sm">
              <Grid className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-800">
                  Ma trận Tương quan Đôi (Bivariate Correlation Matrix & Heatmap)
                </h3>
                <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-100 text-indigo-700 rounded-full">
                  Pearson (1895) & Spearman (1904)
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Kiểm định tương quan tuyến tính (r) & thứ bậc (ρ), khoảng tin cậy 95% Fisher z, biểu đồ nhiệt trực quan và sàng lọc nguy cơ đa cộng tuyến.
              </p>
            </div>
          </div>

          {/* Controls: Method & Scope */}
          <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
            {/* Method switcher */}
            <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-semibold">
              <button
                onClick={() => setMethod('pearson')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  method === 'pearson'
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Pearson (r)
              </button>
              <button
                onClick={() => setMethod('spearman')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  method === 'spearman'
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Spearman (ρ)
              </button>
            </div>

            {/* Scope select */}
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            >
              <option value="all">Tất cả phản hồi hợp lệ</option>
              <option value="verified_clean">Chỉ dữ liệu làm sạch (Clean)</option>
            </select>

            {/* Refresh */}
            <button
              onClick={loadData}
              disabled={loading}
              className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
              title="Tải lại ma trận tương quan"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Body Content */}
      <div className="p-6">
        {loading && (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400">
            <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-xs font-medium text-slate-600">Đang tính toán ma trận tương quan đôi & khoảng tin cậy 95%...</p>
          </div>
        )}

        {error && !loading && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3 text-rose-700 text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
            <div>
              <span className="font-semibold">Lỗi phân tích:</span> {error}
            </div>
          </div>
        )}

        {report && report.status === 'INSUFFICIENT_VARIABLES' && !loading && (
          <div className="p-8 text-center text-slate-400">
            <Grid className="w-10 h-10 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-semibold text-slate-700">Chưa đủ biến thang đo định lượng</p>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              {report.message || 'Khảo sát cần có tối thiểu 2 câu hỏi dạng thang đo (Rating, Likert, NPS) để xây dựng ma trận tương quan đôi.'}
            </p>
          </div>
        )}

        {report && report.status === 'SUCCESS' && !loading && (
          <div className="space-y-6">
            {/* Hero KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Total Variables */}
              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Số Biến Phân Tích (K)
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-900">
                    {report.variables_count}
                  </span>
                  <span className="text-xs text-slate-500">biến thang đo</span>
                </div>
                <div className="mt-2 text-xs text-slate-600">
                  Tổng {report.total_pairs_count} cặp tương quan đôi
                </div>
              </div>

              {/* Significant Pairs Rate */}
              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Tỷ Lệ Đạt Ý Nghĩa (p &lt; .05)
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-emerald-600">
                    {report.total_pairs_count > 0
                      ? ((report.significant_pairs_count / report.total_pairs_count) * 100).toFixed(0)
                      : 0}%
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    ({report.significant_pairs_count}/{report.total_pairs_count})
                  </span>
                </div>
                <div className="mt-2 text-xs">
                  {report.significant_pairs_count > 0 ? (
                    <span className="inline-flex items-center gap-1 font-semibold text-emerald-700">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Có liên hệ thống kê
                    </span>
                  ) : (
                    <span className="text-slate-500">Chưa ghi nhận cặp ý nghĩa</span>
                  )}
                </div>
              </div>

              {/* Strongest Correlation Pair */}
              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Tương Quan Cao Nhất
                </span>
                {report.high_correlations.length > 0 ? (
                  <>
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-black text-indigo-700 font-mono">
                        {report.high_correlations[0].correlation > 0 ? '+' : ''}
                        {report.high_correlations[0].correlation.toFixed(2)}
                      </span>
                      <span className="text-xs font-medium text-indigo-600">
                        {report.high_correlations[0].strength.split(' ')[0]}
                      </span>
                    </div>
                    <div className="mt-2 text-[11px] text-slate-600 truncate" title={`${report.high_correlations[0].var1_title} ↔ ${report.high_correlations[0].var2_title}`}>
                      {report.high_correlations[0].var1_title} ↔ {report.high_correlations[0].var2_title}
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-2xl font-black text-slate-400 font-mono">—</div>
                    <div className="mt-2 text-xs text-slate-500">Chưa có cặp |r| ≥ .50</div>
                  </>
                )}
              </div>

              {/* Multicollinearity Warning KPI */}
              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Đa Cộng Tuyến (|r| ≥ .85)
                </span>
                <div className="flex items-baseline gap-2">
                  <span className={`text-2xl font-black ${report.multicollinearity_warnings.length > 0 ? 'text-amber-600' : 'text-slate-800'}`}>
                    {report.multicollinearity_warnings.length}
                  </span>
                  <span className="text-xs text-slate-500">cặp vi phạm</span>
                </div>
                <div className="mt-2 text-xs">
                  {report.multicollinearity_warnings.length > 0 ? (
                    <span className="inline-flex items-center gap-1 font-bold text-amber-700">
                      <AlertTriangle className="w-3 h-3 text-amber-600" /> Nguy cơ đa cộng tuyến
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 font-semibold text-emerald-700">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> An toàn cho hồi quy
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Multicollinearity Caution Alert Banner */}
            {report.multicollinearity_warnings.length > 0 && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold text-amber-900">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  Cảnh Báo Đa Cộng Tuyến Nghiêm Trọng (Multicollinearity Screening - Tabachnick & Fidell, 2019):
                </div>
                <p className="text-amber-800">
                  Hệ thống phát hiện {report.multicollinearity_warnings.length} cặp biến có tương quan rất cao (|r| ≥ 0.85). Hiện tượng này có thể gây sai lệch ước lượng hệ số hồi quy (thổi phồng sai số chuẩn và đảo lộn dấu trọng số beta). Khuyến nghị kiểm tra VIF (Variance Inflation Factor) hoặc gộp thang đo trước khi hồi quy OLS/SEM.
                </p>
                <div className="space-y-1">
                  {report.multicollinearity_warnings.map((w, wIdx) => (
                    <div key={wIdx} className="bg-white/80 p-2 rounded-lg border border-amber-200 flex items-center justify-between">
                      <span className="font-semibold text-slate-800 truncate mr-2">
                        {w.var1_title} ↔ {w.var2_title}
                      </span>
                      <span className="font-mono font-bold text-amber-700 px-2 py-0.5 bg-amber-100 rounded">
                        r = {w.correlation.toFixed(2)} (p &lt; .001)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Interactive Correlation Heatmap Matrix */}
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <h4 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-indigo-600" />
                  Ma Trận Nhiệt Trực Quan (Interactive Correlation Heatmap)
                </h4>
                <div className="flex items-center gap-4 text-[11px] text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-indigo-600 inline-block" />
                    <span>Dương (+1)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-slate-100 border border-slate-200 inline-block" />
                    <span>0</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-rose-500 inline-block" />
                    <span>Âm (-1)</span>
                  </div>
                  <span className="font-mono text-slate-400">
                    * p &lt; .05, ** p &lt; .01, *** p &lt; .001
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white p-3">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr>
                      <th className="p-2 border border-slate-200 bg-slate-50 text-left font-semibold text-slate-600 min-w-44">
                        Biến quan sát
                      </th>
                      {report.variables.map((v, colIdx) => (
                        <th
                          key={v.id}
                          className="p-2 border border-slate-200 bg-slate-50 text-center font-bold text-slate-700 min-w-20"
                          title={`${v.label}: ${v.title}`}
                        >
                          <div className="font-mono text-[11px] text-indigo-700">{v.label}</div>
                          <div className="text-[10px] text-slate-400 font-normal">M={v.mean.toFixed(1)}</div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.matrix.map((rowCells, rIdx) => {
                      const rowVar = report.variables[rIdx];
                      return (
                        <tr key={rowVar.id} className="hover:bg-slate-50/50">
                          {/* Row Header */}
                          <td className="p-2 border border-slate-200 bg-slate-50 font-medium text-slate-800">
                            <div className="font-mono font-bold text-indigo-700 text-[11px]">{rowVar.label}</div>
                            <div className="text-slate-600 line-clamp-1 text-[11px]" title={rowVar.title}>
                              {rowVar.title}
                            </div>
                          </td>

                          {/* Matrix Cells */}
                          {rowCells.map((cell, cIdx) => {
                            const isDiag = rIdx === cIdx;
                            const sigStars = getSigStars(cell);
                            const bgClass = getCellBgColor(cell.correlation);

                            return (
                              <td
                                key={cIdx}
                                onMouseEnter={() => {
                                  setHoveredCell({
                                    row: rIdx,
                                    col: cIdx,
                                    cell,
                                    var1_title: rowVar.title,
                                    var2_title: report.variables[cIdx].title
                                  });
                                }}
                                onMouseLeave={() => setHoveredCell(null)}
                                className={`p-2 border border-slate-200 text-center cursor-pointer transition-all duration-150 ${bgClass} hover:ring-2 hover:ring-indigo-500 hover:z-10`}
                              >
                                <div className="font-mono text-xs">
                                  {cell.correlation > 0 && !isDiag ? `+${cell.correlation.toFixed(2)}` : cell.correlation.toFixed(2)}
                                </div>
                                {sigStars && (
                                  <div className="text-[10px] leading-3 font-black text-amber-300">
                                    {sigStars}
                                  </div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Cell Inspector / Hover Tooltip Bar */}
              {hoveredCell && (
                <div className="mt-3 p-3 bg-indigo-50/70 border border-indigo-200 rounded-xl text-xs flex flex-col md:flex-row md:items-center justify-between gap-2 shadow-xs animate-in fade-in duration-200">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-indigo-900">Chi tiết tương quan:</span>
                    <span className="font-medium text-slate-800">
                      "{hoveredCell.var1_title}"
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="font-medium text-slate-800">
                      "{hoveredCell.var2_title}"
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-slate-700 font-mono">
                    <span>
                      {method === 'pearson' ? 'r' : 'ρ'} = <strong className="text-indigo-700">{hoveredCell.cell.correlation.toFixed(3)}</strong>
                    </span>
                    <span>
                      p = <strong>{hoveredCell.cell.p_value < 0.001 ? '< .001' : hoveredCell.cell.p_value.toFixed(4)}</strong>
                    </span>
                    <span>
                      95% CI: <strong>[{hoveredCell.cell.ci_95_lower.toFixed(2)}, {hoveredCell.cell.ci_95_upper.toFixed(2)}]</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded bg-white text-indigo-800 font-sans font-semibold text-[11px] border border-indigo-100">
                      {hoveredCell.cell.strength}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* High Correlations Ranking Table */}
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <h4 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Table className="w-4 h-4 text-indigo-600" />
                  Bảng Xếp Hạng Các Cặp Tương Quan (Ranked Correlation Pairs)
                </h4>

                <div className="flex items-center gap-1.5 text-xs">
                  <button
                    onClick={() => setFilterMode('all')}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
                      filterMode === 'all' ? 'bg-indigo-100 text-indigo-800' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Tất cả ({report.high_correlations.length})
                  </button>
                  <button
                    onClick={() => setFilterMode('significant')}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
                      filterMode === 'significant' ? 'bg-indigo-100 text-indigo-800' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Có ý nghĩa (p &lt; .05)
                  </button>
                  <button
                    onClick={() => setFilterMode('strong')}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
                      filterMode === 'strong' ? 'bg-indigo-100 text-indigo-800' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Mạnh (|r| ≥ .60)
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Cặp thang đo khảo sát</th>
                      <th className="py-2.5 px-3 text-right">Hệ số tương quan ({method === 'pearson' ? 'r' : 'ρ'})</th>
                      <th className="py-2.5 px-3 text-right">Mức ý nghĩa (p)</th>
                      <th className="py-2.5 px-3 text-center">95% CI (Fisher z)</th>
                      <th className="py-2.5 px-3 text-left">Độ mạnh mối quan hệ</th>
                      <th className="py-2.5 px-3 text-center">Đánh giá</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                    {report.high_correlations
                      .filter((p) => {
                        if (filterMode === 'significant') return p.p_value < 0.05;
                        if (filterMode === 'strong') return Math.abs(p.correlation) >= 0.60;
                        return true;
                      })
                      .map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50">
                          <td className="py-2.5 px-3 font-semibold text-slate-900 flex items-center gap-1.5">
                            <span className="truncate max-w-xs">{p.var1_title}</span>
                            <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                            <span className="truncate max-w-xs">{p.var2_title}</span>
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono font-bold text-indigo-700">
                            {p.correlation > 0 ? `+${p.correlation.toFixed(3)}` : p.correlation.toFixed(3)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono">
                            {p.p_value < 0.001 ? '< .001' : p.p_value.toFixed(4)}
                          </td>
                          <td className="py-2.5 px-3 text-center font-mono text-slate-600">
                            [{p.ci_95_lower.toFixed(2)}, {p.ci_95_upper.toFixed(2)}]
                          </td>
                          <td className="py-2.5 px-3 text-slate-700">
                            {p.strength}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            {Math.abs(p.correlation) >= 0.85 ? (
                              <span className="px-2 py-0.5 text-[11px] font-bold bg-amber-100 text-amber-800 rounded-md">
                                Đa cộng tuyến
                              </span>
                            ) : p.p_value < 0.05 ? (
                              <span className="px-2 py-0.5 text-[11px] font-semibold bg-emerald-100 text-emerald-800 rounded-md">
                                Có ý nghĩa
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 text-[11px] text-slate-500 bg-slate-100 rounded-md">
                                Không ý nghĩa
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* APA 7th Edition Narrative Summary */}
            <div className="bg-gradient-to-br from-indigo-50/60 via-purple-50/30 to-white border border-indigo-200/80 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider">
                    Diễn giải Học thuật Chuẩn APA 7th Edition
                  </h4>
                </div>
                <button
                  onClick={handleCopyAPA}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-semibold transition-colors shadow-xs"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-700">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép APA 7th</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-800 leading-relaxed font-serif bg-white/70 p-3.5 rounded-lg border border-indigo-100 italic">
                "{report.apa_interpretation}"
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
