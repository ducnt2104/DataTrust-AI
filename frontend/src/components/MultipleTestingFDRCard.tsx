import React, { useState } from 'react';
import { api } from '../api/client';
import { MultipleTestingFDRResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface MultipleTestingFDRCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const MultipleTestingFDRCard: React.FC<MultipleTestingFDRCardProps> = ({
  surveyId,
  questions
}) => {
  const [mode, setMode] = useState<'pairwise' | 'custom'>('pairwise');
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [customPValuesText, setCustomPValuesText] = useState<string>(
    '0.0001, 0.0032, 0.0120, 0.0240, 0.0380, 0.0490, 0.0750, 0.1200, 0.3500, 0.6200'
  );
  const [customLabelsText, setCustomLabelsText] = useState<string>(
    'H1_HocVan, H2_ThuNhap, H3_KinhNghiem, H4_DoTuoi, H5_GioiTinh, H6_KhuVuc, H7_DongLuc, H8_HaiLong, H9_GanKet, H10_CamKet'
  );
  const [fdrQ, setFdrQ] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MultipleTestingFDRResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    (q) => q.question_type === 'number' || q.question_type === 'rating'
  );

  const toggleQuestion = (id: string) => {
    setSelectedQuestions((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAllNumeric = () => {
    setSelectedQuestions(numericQuestions.map((q) => q.id));
  };

  const clearSelection = () => {
    setSelectedQuestions([]);
  };

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      if (mode === 'pairwise') {
        if (selectedQuestions.length < 2) {
          throw new Error('Vui long chon it nhat 2 cau hoi dinh luong de lap ma tran kiem dinh lap.');
        }
        const data = await api.runMultipleTestingFDR(surveyId, {
          question_ids: selectedQuestions,
          fdr_q: fdrQ,
          scope
        });
        setResult(data);
      } else {
        const pStrs = customPValuesText.split(/[, \n\t]+/).map((s) => s.trim()).filter(Boolean);
        const pVals = pStrs.map((s) => parseFloat(s)).filter((n) => !isNaN(n));
        if (pVals.length === 0) {
          throw new Error('Vui long nhap it nhat 1 gia tri p-value hop le.');
        }
        const lStrs = customLabelsText.split(/[, \n\t]+/).map((s) => s.trim()).filter(Boolean);
        const data = await api.runMultipleTestingFDR(surveyId, {
          custom_p_values: pVals,
          custom_labels: lStrs.length === pVals.length ? lStrs : undefined,
          fdr_q: fdrQ,
          scope
        });
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Co loi xay ra khi thuc hien kiem dinh lap.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyNarrative = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadSVG = () => {
    if (!result?.svg_chart) return;
    const blob = new Blob([result.svg_chart], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `multiple-testing-fdr-${surveyId}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm mb-8 transition-colors">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
              Econometric & Psychometric Rigor
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
              Benjamini & Hochberg (1995) · Storey (2002)
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:white mt-1">
            Hieu Chinh Kiem Dinh Lap & Ty Le Phat Hien Sai (FDR Matrix)
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1 max-w-3xl">
            Kiem soat ty le phat hien sai (False Discovery Rate - FDR) theo thuat toan buoc tang Benjamini-Hochberg (BH) va Benjamini-Yekutieli (BY). 
            Giai quyet triet de van de kiem dinh lap (Multiple Hypothesis Testing) va duong tinh gia (Type I Error) trong pin khao sat quy mo lon, 
            dong thoi tranh su bao thu cuc doan triet tieu phat hien cua hieu chinh Bonferroni co dien.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode('pairwise')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              mode === 'pairwise'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            Ma Tran Khao Sat Tu Dong
          </button>
          <button
            onClick={() => setMode('custom')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              mode === 'custom'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            Pin P-Values Tuy Chinh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Input Configuration Panel */}
        <div className="lg:col-span-1 space-y-4 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Cau Hinh Kiem Dinh</h3>

          {mode === 'pairwise' ? (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  Chon Cau Hoi Dinh Luong ({selectedQuestions.length} da chon)
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={selectAllNumeric}
                    className="text-xs text-amber-600 dark:text-amber-400 hover:underline"
                  >
                    Chon tat ca
                  </button>
                  <span className="text-slate-400">·</span>
                  <button
                    onClick={clearSelection}
                    className="text-xs text-slate-500 hover:underline"
                  >
                    Bo chon
                  </button>
                </div>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-1.5 border border-slate-200 dark:border-slate-700 rounded-md p-2 bg-white dark:bg-slate-900">
                {numericQuestions.length === 0 ? (
                  <p className="text-xs text-slate-500 italic p-1">Khong tim thay cau hoi dinh luong (number/rating).</p>
                ) : (
                  numericQuestions.map((q) => (
                    <label
                      key={q.id}
                      className="flex items-start gap-2 p-1 text-xs hover:bg-slate-100 dark:hover:bg-slate-800 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedQuestions.includes(q.id)}
                        onChange={() => toggleQuestion(q.id)}
                        className="rounded border-slate-300 text-amber-600 focus:ring-amber-500 mt-0.5"
                      />
                      <span className="text-slate-800 dark:text-slate-200 truncate">{q.title}</span>
                    </label>
                  ))
                )}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Luu y: He thong se tinh toan tat ca k*(k-1)/2 cap tuong quan va kiem dinh FDR dong thoi.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
                  Danh Sach P-Values Tho (phan tach bang dau phay hoac xuong dong)
                </label>
                <textarea
                  rows={3}
                  value={customPValuesText}
                  onChange={(e) => setCustomPValuesText(e.target.value)}
                  className="w-full text-xs font-mono p-2 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                  placeholder="0.001, 0.024, 0.048, 0.12..."
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
                  Nhan Gia Thuyet (tuy chon, phan tach bang dau phay)
                </label>
                <textarea
                  rows={2}
                  value={customLabelsText}
                  onChange={(e) => setCustomLabelsText(e.target.value)}
                  className="w-full text-xs font-mono p-2 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                  placeholder="H1, H2, H3..."
                />
              </div>
            </div>
          )}

          {/* FDR Target Q Slider */}
          <div>
            <div className="flex justify-between items-center text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              <span>Muc Y Nghia Muc Tieu FDR (Q):</span>
              <span className="font-bold font-mono text-amber-600 dark:text-amber-400">{fdrQ.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="0.20"
              step="0.01"
              value={fdrQ}
              onChange={(e) => setFdrQ(parseFloat(e.target.value))}
              className="w-full accent-amber-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>0.01 (Rat nghiem ngat)</span>
              <span>0.05 (Chuan)</span>
              <span>0.20 (Kham pha)</span>
            </div>
          </div>

          {/* Scope selection */}
          <div>
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">Pham Vi Mau</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
              className="w-full text-xs p-2 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            >
              <option value="all">Tat ca phan hoi hop le</option>
              <option value="verified_clean">Chi phan hoi da xac thuc sach (Verified Clean)</option>
            </select>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-amber-600 hover:bg-amber-700 text-white font-medium text-xs rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Dang Tinh Toan FDR...</span>
              </>
            ) : (
              <span>Chay Hieu Chinh FDR Matrix</span>
            )}
          </button>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded text-xs text-red-600 dark:text-red-400">
              {error}
            </div>
          )}
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-6">
          {!result && !loading && (
            <div className="h-full flex flex-col items-center justify-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg p-12 text-center text-slate-400">
              <svg className="w-12 h-12 mb-3 text-slate-300 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Chua co ket qua phan tich FDR Matrix
              </p>
              <p className="text-xs mt-1 max-w-sm">
                Chon it nhat 2 bien so hoac nhap day p-values, sau do nhan "Chay Hieu Chinh FDR Matrix" de xem ket qua.
              </p>
            </div>
          )}

          {result && result.sample_diagnostics && (
            <div className="space-y-6">
              {/* Summary Stats Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Tong So Gia Thuyet (m)</span>
                  <span className="text-lg font-bold text-slate-900 dark:text-white font-mono">
                    {result.sample_diagnostics.total_hypotheses_m}
                  </span>
                </div>
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block">Phat Hien BH FDR</span>
                  <span className="text-lg font-bold text-emerald-700 dark:text-emerald-300 font-mono">
                    {result.sample_diagnostics.bh_fdr_significant_count}
                  </span>
                </div>
                <div className="p-3 bg-purple-50 dark:bg-purple-950/40 rounded-lg border border-purple-200 dark:border-purple-800">
                  <span className="text-[11px] text-purple-600 dark:text-purple-400 block">Uoc Luong Null (pi_0)</span>
                  <span className="text-lg font-bold text-purple-700 dark:text-purple-300 font-mono">
                    {result.sample_diagnostics.estimated_pi_0_null_proportion}
                  </span>
                </div>
                <div className="p-3 bg-amber-50 dark:bg-amber-950/40 rounded-lg border border-amber-200 dark:border-amber-800">
                  <span className="text-[11px] text-amber-600 dark:text-amber-400 block">FDR Q-Threshold</span>
                  <span className="text-lg font-bold text-amber-700 dark:text-amber-300 font-mono">
                    {result.sample_diagnostics.fdr_target_q}
                  </span>
                </div>
              </div>

              {/* Discovery Breakdown Pills */}
              <div className="flex flex-wrap gap-2 text-xs">
                <div className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  Phat hien tho (p &lt; Q): <strong className="font-mono">{result.sample_diagnostics.raw_significant_count}</strong>
                </div>
                <div className="px-2.5 py-1 rounded bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  Giai cuu boi FDR (vs Bonferroni): <strong className="font-mono">+{result.sample_diagnostics.rescued_by_bh_count}</strong>
                </div>
                <div className="px-2.5 py-1 rounded bg-rose-100 dark:bg-rose-900/40 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
                  Duong tinh gia da loc: <strong className="font-mono">{result.sample_diagnostics.filtered_false_positives_count}</strong>
                </div>
                <div className="px-2.5 py-1 rounded bg-indigo-100 dark:bg-indigo-900/40 text-indigo-800 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  Vuot qua Bonferroni: <strong className="font-mono">{result.sample_diagnostics.bonferroni_significant_count}</strong>
                </div>
              </div>

              {/* SVG Dual-Panel Chart */}
              {result.svg_chart && (
                <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-slate-50 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider">
                      Bieu Do Phan Tich Truc Quan FDR Dual-Panel
                    </h4>
                    <button
                      onClick={handleDownloadSVG}
                      className="px-2 py-1 text-xs font-medium text-amber-600 hover:text-amber-700 dark:text-amber-400 hover:underline flex items-center gap-1"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Tai ban do SVG
                    </button>
                  </div>
                  <div
                    className="w-full overflow-x-auto flex justify-center"
                    dangerouslySetInnerHTML={{ __html: result.svg_chart }}
                  />
                </div>
              )}

              {/* Detailed Corrections Table */}
              {result.corrections && result.corrections.length > 0 && (
                <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                  <div className="px-4 py-3 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider">
                      Bang Xep Hang P-Values & Quyet Dinh Kiem Dinh (Rank-Ordered Corrections)
                    </h4>
                    <span className="text-xs text-slate-500 font-mono">
                      Tong: {result.corrections.length} gia thuyet
                    </span>
                  </div>
                  <div className="overflow-x-auto max-h-80">
                    <table className="w-full text-xs text-left text-slate-600 dark:text-slate-300">
                      <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 sticky top-0">
                        <tr>
                          <th className="py-2 px-3">Rank (i)</th>
                          <th className="py-2 px-3">Gia Thuyet / Cap Bien</th>
                          <th className="py-2 px-3">P-Value Tho</th>
                          <th className="py-2 px-3">Nguong BH (i/m*Q)</th>
                          <th className="py-2 px-3">BH q-Value</th>
                          <th className="py-2 px-3">BY Adjusted</th>
                          <th className="py-2 px-3">Bonferroni p</th>
                          <th className="py-2 px-3">Ket Luan</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono">
                        {result.corrections.map((row) => (
                          <tr
                            key={row.rank}
                            className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 ${
                              row.decision_status === 'SURVIVES_BONFERRONI'
                                ? 'bg-emerald-50/40 dark:bg-emerald-950/20'
                                : row.decision_status === 'DISCOVERED_BH_FDR'
                                ? 'bg-teal-50/40 dark:bg-teal-950/20'
                                : row.decision_status === 'FILTERED_FALSE_POSITIVE'
                                ? 'bg-rose-50/40 dark:bg-rose-950/20'
                                : ''
                            }`}
                          >
                            <td className="py-2 px-3 font-semibold text-slate-900 dark:text-white">#{row.rank}</td>
                            <td className="py-2 px-3 font-sans font-medium text-slate-800 dark:text-slate-200">{row.hypothesis}</td>
                            <td className="py-2 px-3">{row.raw_p_value.toFixed(5)}</td>
                            <td className="py-2 px-3 text-slate-500">{row.bh_critical_value.toFixed(5)}</td>
                            <td className="py-2 px-3 font-semibold text-amber-600 dark:text-amber-400">{row.bh_q_value.toFixed(5)}</td>
                            <td className="py-2 px-3 text-slate-500">{row.by_adjusted_p.toFixed(5)}</td>
                            <td className="py-2 px-3 text-slate-500">{row.bonferroni_p.toFixed(5)}</td>
                            <td className="py-2 px-3 font-sans">
                              <span
                                className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                                  row.decision_status === 'SURVIVES_BONFERRONI'
                                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300'
                                    : row.decision_status === 'DISCOVERED_BH_FDR'
                                    ? 'bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-300'
                                    : row.decision_status === 'FILTERED_FALSE_POSITIVE'
                                    ? 'bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-300'
                                    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                                }`}
                              >
                                {row.decision_badge}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* APA 7th Edition Narrative */}
              {result.apa_narrative && (
                <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                      <span>Van Ban Thuyet Minh Chuan APA 7th Edition</span>
                    </h4>
                    <button
                      onClick={handleCopyNarrative}
                      className="text-xs text-amber-600 dark:text-amber-400 hover:underline flex items-center gap-1"
                    >
                      {copied ? 'Da sao chep!' : 'Sao chep'}
                    </button>
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed italic bg-white dark:bg-slate-900 p-3 rounded border border-slate-200 dark:border-slate-800 font-serif">
                    {result.apa_narrative}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
