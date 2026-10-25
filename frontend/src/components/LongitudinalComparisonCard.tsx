import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  ArrowRight,
  GitCompare,
  Copy,
  Download,
  Check,
  Filter,
  AlertCircle,
  HelpCircle,
  Sparkles,
  BarChart2
} from 'lucide-react';
import { api } from '../api/client';
import { LongitudinalWaveComparisonResult, LongitudinalItemComparison } from '../types/survey';

interface Props {
  currentSurveyId: string;
  currentSurveyTitle: string;
}

export const LongitudinalComparisonCard: React.FC<Props> = ({ currentSurveyId, currentSurveyTitle }) => {
  const [surveysList, setSurveysList] = useState<Array<{ id: string; title: string; version: number }>>([]);
  const [selectedCompareId, setSelectedCompareId] = useState<string>('');
  const [scope, setScope] = useState<'verified_clean' | 'all'>('verified_clean');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LongitudinalWaveComparisonResult | null>(null);
  const [filterMode, setFilterMode] = useState<'all' | 'significant' | 'large_effect' | 'scale_only'>('all');
  const [copiedType, setCopiedType] = useState<string | null>(null);

  useEffect(() => {
    // Nạp danh sách các khảo sát khác trong không gian làm việc
    api.getSurveys()
      .then((res) => {
        const others = (Array.isArray(res) ? res : [])
          .filter((s: any) => s.id !== currentSurveyId)
          .map((s: any) => ({ id: s.id, title: s.title, version: s.version }));
        setSurveysList(others);
        if (others.length > 0 && !selectedCompareId) {
          setSelectedCompareId(others[0].id);
        }
      })
      .catch((err) => console.error('Lỗi nạp danh sách khảo sát:', err));
  }, [currentSurveyId]);

  const handleRunComparison = async () => {
    if (!selectedCompareId) {
      setError('Vui lòng chọn khảo sát đối chứng để so sánh xu hướng.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLongitudinalAnalysis(currentSurveyId, selectedCompareId, scope);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Không thể tính toán so sánh xu hướng giữa hai đợt khảo sát.');
    } finally {
      setLoading(false);
    }
  };

  const filteredItems = (result?.items || []).filter((item) => {
    if (filterMode === 'significant') return item.is_statistically_significant;
    if (filterMode === 'large_effect') return item.cohens_d !== null && item.cohens_d !== undefined && Math.abs(item.cohens_d) >= 0.8;
    if (filterMode === 'scale_only') return item.is_scale;
    return true;
  });

  const handleCopyMarkdown = () => {
    if (!result) return;
    const lines = [
      `### BẢNG SO SÁNH XU HƯỚNG DỌC THEO ĐỢT (LONGITUDINAL WAVE-OVER-WAVE COMPARISON)`,
      `**Đợt 1 (Baseline):** ${result.wave1_survey.title} (N = ${result.wave1_survey.total_responses})  `,
      `**Đợt 2 (Current):** ${result.wave2_survey.title} (N = ${result.wave2_survey.total_responses})  `,
      `**Phạm vi:** \`${scope.toUpperCase()}\` | **Số câu hỏi tương ứng:** ${result.matched_questions_count}  `,
      `**Kết luận tổng quan:** ${result.comparative_summary}  `,
      ``,
      `| Câu hỏi / Chỉ tiêu | Đợt 1 (M₁ ± SD₁) | Đợt 2 (M₂ ± SD₂) | Độ lệch (ΔM) | % Biến thiên | Cohen's d | Mức ý nghĩa | Trình bày chuẩn APA 7th |`,
      `| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |`
    ];

    result.items.forEach((item) => {
      const m1_str = item.mean_wave1 !== null ? `${item.mean_wave1} ± ${item.std_wave1 || 0}` : `N = ${item.n_wave1}`;
      const m2_str = item.mean_wave2 !== null ? `${item.mean_wave2} ± ${item.std_wave2 || 0}` : `N = ${item.n_wave2}`;
      const delta_str = item.mean_shift !== null && item.mean_shift !== undefined ? `${item.mean_shift > 0 ? '+' : ''}${item.mean_shift}` : 'N/A';
      const pct_str = item.percent_change !== null && item.percent_change !== undefined ? `${item.percent_change > 0 ? '+' : ''}${item.percent_change}%` : 'N/A';
      const d_str = item.cohens_d !== null && item.cohens_d !== undefined ? `${item.cohens_d}` : 'N/A';
      const clean_title = item.title.replace(/\|/g, '\\|');
      lines.push(
        `| ${clean_title} | ${m1_str} | ${m2_str} | ${delta_str} | ${pct_str} | ${d_str} | ${item.significance_label} | \`${item.apa_summary}\` |`
      );
    });

    navigator.clipboard.writeText(lines.join('\n'));
    setCopiedType('markdown');
    setTimeout(() => setCopiedType(null), 2500);
  };

  const handleDownloadCsv = () => {
    if (!result) return;
    const header = ['Question_Title', 'Type', 'N_Wave1', 'N_Wave2', 'Mean_Wave1', 'SD_Wave1', 'Mean_Wave2', 'SD_Wave2', 'Mean_Shift', 'Percent_Change', 'Cohens_d', 'Effect_Magnitude', 't_statistic', 'df', 'p_value', 'Significant', 'APA_Summary'];
    const rows = [header.join(',')];

    result.items.forEach((item) => {
      const esc = (t: string) => `"${(t || '').replace(/"/g, '""')}"`;
      rows.push([
        esc(item.title),
        esc(item.question_type),
        item.n_wave1,
        item.n_wave2,
        item.mean_wave1 ?? '',
        item.std_wave1 ?? '',
        item.mean_wave2 ?? '',
        item.std_wave2 ?? '',
        item.mean_shift ?? '',
        item.percent_change ?? '',
        item.cohens_d ?? '',
        esc(item.effect_size),
        item.t_statistic ?? '',
        item.degrees_of_freedom ?? '',
        item.p_value ?? '',
        item.is_statistically_significant ? 'YES' : 'NO',
        esc(item.apa_summary)
      ].join(','));
    });

    const bom = '\uFEFF';
    const blob = new Blob([bom + rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `longitudinal_wave_comparison_${currentSurveyId.slice(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <GitCompare className="w-5 h-5" />
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Phân Tích Xu Hướng Dọc & Độ Lớn Hiệu Ứng (Longitudinal Wave Comparison)
            </h3>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
              Cohen's d & Welch's t-test
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Đối soát trực tiếp giữa 2 đợt khảo sát (Pre-test vs Post-test hoặc Wave 1 vs Wave 2) để phát hiện sự dịch chuyển điểm số có ý nghĩa thống kê.
          </p>
        </div>

        {/* Survey Picker & Trigger */}
        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={selectedCompareId}
            onChange={(e) => setSelectedCompareId(e.target.value)}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 max-w-[220px]"
          >
            <option value="">-- Chọn Khảo Sát Đợt 1 --</option>
            {surveysList.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title} (v{s.version})
              </option>
            ))}
          </select>

          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="verified_clean">Mẫu sạch</option>
            <option value="all">Tất cả mẫu</option>
          </select>

          <button
            onClick={handleRunComparison}
            disabled={loading || !selectedCompareId}
            className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
          >
            {loading ? (
              <span className="flex items-center gap-1">
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Đang xử lý...
              </span>
            ) : (
              <>
                <GitCompare className="w-3.5 h-3.5" />
                So Sánh Xu Hướng
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="mt-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* When no comparison run yet */}
      {!result && !loading && !error && (
        <div className="py-8 text-center text-xs text-slate-400">
          Chọn một khảo sát đợt trước (Baseline / Wave 1) từ danh sách bên trên và nhấn{' '}
          <strong className="text-indigo-600 dark:text-indigo-400 font-semibold">"So Sánh Xu Hướng"</strong> để chạy đối soát ma trận.
        </div>
      )}

      {/* Comparison Results */}
      {result && (
        <div className="mt-5 space-y-5">
          {/* Wave Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80">
              <span className="text-[10px] uppercase font-bold text-slate-400">Đợt 1 (Khảo Sát Đối Chứng)</span>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate mt-0.5">
                {result.wave1_survey.title}
              </div>
              <div className="flex items-center gap-2 mt-2 text-xs">
                <span className="text-slate-500">Mẫu: <strong className="text-slate-800 dark:text-white font-mono">{result.wave1_survey.total_responses}</strong></span>
                <span className="text-slate-300">|</span>
                <span className="text-slate-500">Tin cậy: <strong className="text-emerald-600 font-mono">{result.wave1_survey.trust_index}%</strong></span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/80">
              <span className="text-[10px] uppercase font-bold text-indigo-500 dark:text-indigo-400">Đợt 2 (Khảo Sát Hiện Tại)</span>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate mt-0.5">
                {result.wave2_survey.title}
              </div>
              <div className="flex items-center gap-2 mt-2 text-xs">
                <span className="text-slate-500">Mẫu: <strong className="text-slate-800 dark:text-white font-mono">{result.wave2_survey.total_responses}</strong></span>
                <span className="text-slate-300">|</span>
                <span className="text-slate-500">Tin cậy: <strong className="text-emerald-600 font-mono">{result.wave2_survey.trust_index}%</strong></span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">Độ Lệch Điểm Thang Đo Tổng Thể</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-xl font-extrabold text-slate-900 dark:text-white font-mono">
                  {result.overall_scale_delta !== null && result.overall_scale_delta !== undefined ? `${result.overall_scale_delta > 0 ? '+' : ''}${result.overall_scale_delta}` : 'N/A'}
                </span>
                {result.overall_scale_delta !== null && result.overall_scale_delta !== undefined && (
                  <span className={`text-xs font-bold flex items-center ${result.overall_scale_delta >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {result.overall_scale_delta >= 0 ? <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> : <TrendingDown className="w-3.5 h-3.5 mr-0.5" />}
                    {result.overall_scale_mean_wave1} → {result.overall_scale_mean_wave2}
                  </span>
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1">{result.matched_questions_count} câu hỏi khớp tương ứng</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">Phân Phối Xu Hướng</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                  +{result.items_increased_count} Tăng (p &lt; .05)
                </span>
                <span className="text-xs font-bold text-slate-600 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                  {result.items_stable_count} Ổn định
                </span>
                {result.items_decreased_count > 0 && (
                  <span className="text-xs font-bold text-rose-600 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded border border-rose-200 dark:border-rose-800">
                    -{result.items_decreased_count} Giảm
                  </span>
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 truncate">{result.comparative_summary}</span>
            </div>
          </div>

          {/* Action Bar & Filter Tabs */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 text-xs">
              <button
                onClick={() => setFilterMode('all')}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${filterMode === 'all' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400'}`}
              >
                Tất cả ({result.items.length})
              </button>
              <button
                onClick={() => setFilterMode('significant')}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${filterMode === 'significant' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400'}`}
              >
                Ý nghĩa (p &lt; .05)
              </button>
              <button
                onClick={() => setFilterMode('large_effect')}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${filterMode === 'large_effect' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400'}`}
              >
                Hiệu ứng lớn (|d| ≥ 0.8)
              </button>
              <button
                onClick={() => setFilterMode('scale_only')}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${filterMode === 'scale_only' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400'}`}
              >
                Thang đo số
              </button>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                onClick={handleCopyMarkdown}
                className="flex-1 sm:flex-none px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-medium text-slate-700 dark:text-slate-200 transition-colors flex items-center justify-center gap-1.5 border border-slate-200 dark:border-slate-700"
              >
                {copiedType === 'markdown' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedType === 'markdown' ? 'Đã Sao Chép!' : 'Sao Chép Bảng APA'}
              </button>
              <button
                onClick={handleDownloadCsv}
                className="flex-1 sm:flex-none px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-medium text-slate-700 dark:text-slate-200 transition-colors flex items-center justify-center gap-1.5 border border-slate-200 dark:border-slate-700"
              >
                <Download className="w-3.5 h-3.5" />
                Tải CSV
              </button>
            </div>
          </div>

          {/* Matrix Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="py-3 px-3.5 min-w-[200px]">Câu Hỏi / Chỉ Tiêu Khảo Sát</th>
                  <th className="py-3 px-3 min-w-[90px]">Đợt 1 (Baseline)</th>
                  <th className="py-3 px-3 min-w-[90px]">Đợt 2 (Current)</th>
                  <th className="py-3 px-3 min-w-[80px]">Độ Lệch (ΔM)</th>
                  <th className="py-3 px-3 min-w-[95px]">Cohen's d</th>
                  <th className="py-3 px-3 min-w-[120px]">Kiểm Định Welch's t</th>
                  <th className="py-3 px-3 min-w-[160px]">Trình Bày Chuẩn APA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                {filteredItems.map((item, idx) => {
                  const hasIncrease = item.trend_direction === 'INCREASED';
                  const hasDecrease = item.trend_direction === 'DECREASED';

                  return (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-3.5">
                        <div className="font-semibold text-slate-900 dark:text-white line-clamp-2">
                          {item.title}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] text-slate-400 font-mono uppercase bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                            {item.question_type}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            N1 = {item.n_wave1}, N2 = {item.n_wave2}
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-3 font-mono">
                        {item.is_scale && item.mean_wave1 !== null ? (
                          <div>
                            <span className="font-bold text-slate-800 dark:text-slate-200">{item.mean_wave1}</span>
                            <span className="text-[10px] text-slate-400 block">±{item.std_wave1}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400">N={item.n_wave1}</span>
                        )}
                      </td>

                      <td className="py-3 px-3 font-mono">
                        {item.is_scale && item.mean_wave2 !== null ? (
                          <div>
                            <span className="font-bold text-slate-800 dark:text-slate-200">{item.mean_wave2}</span>
                            <span className="text-[10px] text-slate-400 block">±{item.std_wave2}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400">N={item.n_wave2}</span>
                        )}
                      </td>

                      <td className="py-3 px-3 font-mono">
                        {item.is_scale && item.mean_shift !== null && item.mean_shift !== undefined ? (
                          <div className={`font-bold flex items-center ${hasIncrease ? 'text-emerald-600' : hasDecrease ? 'text-rose-600' : 'text-slate-600 dark:text-slate-300'}`}>
                            {hasIncrease && <TrendingUp className="w-3.5 h-3.5 mr-0.5" />}
                            {hasDecrease && <TrendingDown className="w-3.5 h-3.5 mr-0.5" />}
                            {item.mean_shift > 0 ? `+${item.mean_shift}` : item.mean_shift}
                          </div>
                        ) : (
                          <span className="text-slate-400 text-[11px]">{item.significance_label}</span>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        {item.cohens_d !== null && item.cohens_d !== undefined ? (
                          <div>
                            <span className={`font-mono font-bold px-1.5 py-0.5 rounded text-[11px] ${Math.abs(item.cohens_d) >= 0.8 ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300' : Math.abs(item.cohens_d) >= 0.5 ? 'bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                              d = {item.cohens_d > 0 ? `+${item.cohens_d}` : item.cohens_d}
                            </span>
                            <span className="text-[10px] text-slate-400 block mt-0.5 truncate max-w-[110px]" title={item.effect_size}>
                              {item.effect_size.split('(')[0]}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-[10px]">Định danh</span>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        {item.t_statistic !== null ? (
                          <div>
                            <span className="font-mono text-slate-800 dark:text-slate-200">t = {item.t_statistic}</span>
                            <span className={`text-[10px] font-semibold block ${item.is_statistically_significant ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}`}>
                              {item.significance_label}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Tần số %</span>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <div className="font-mono text-[11px] text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 px-2 py-1 rounded border border-slate-200 dark:border-slate-700/60 select-all">
                          {item.apa_summary}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
