import React, { useState } from 'react';
import { api } from '../api/client';
import { GaussianCopulaResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface GaussianCopulaCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const GaussianCopulaCard: React.FC<GaussianCopulaCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter(
    (q) => q.question_type === 'number' || q.question_type === 'rating'
  );

  const [endogQId, setEndogQId] = useState<string>(numericQuestions[0]?.id || '');
  const [outcomeQId, setOutcomeQId] = useState<string>(numericQuestions[1]?.id || '');
  const [selectedControls, setSelectedControls] = useState<string[]>([]);
  const [bootstraps, setBootstraps] = useState<number>(250);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GaussianCopulaResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleControl = (id: string) => {
    setSelectedControls((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleRunAnalysis = async () => {
    if (!endogQId || !outcomeQId) {
      setError('Vui long chon ca bien noi sinh va bien ket qua.');
      return;
    }
    if (endogQId === outcomeQId) {
      setError('Bien noi sinh va bien ket qua khong duoc trung nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.runGaussianCopulaAnalysis(surveyId, {
        endogenous_question_id: endogQId,
        outcome_question_id: outcomeQId,
        control_question_ids: selectedControls.filter((id) => id !== endogQId && id !== outcomeQId),
        n_bootstraps: bootstraps,
        scope
      });
      setResult(data);
    } catch (err: any) {
      setError(err?.message || 'Co loi xay ra khi thuc hien kiem dinh Gaussian Copula.');
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
    link.download = `gaussian-copula-${surveyId}.svg`;
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
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-cyan-100 text-cyan-800 dark:bg-cyan-900/50 dark:text-cyan-300">
              Instrument-Free Endogeneity Correction
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
              Park &amp; Gupta (2012) · Marketing Science
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
            Hiệu Chỉnh Biến Nội Sinh Không Cần Biến Công Cụ (Gaussian Copula)
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1 max-w-3xl">
            Giải quyết triệt để vấn đề sai lệch nội sinh (Endogeneity Bias) do biến tiềm ẩn bị bỏ sót (omitted variables) 
            hoặc sai số đo lường mà không cần tìm kiếm biến công cụ ngoại sinh (External Instrumental Variables). 
            Tận dụng đặc tính phân phối phi chuẩn của dữ liệu khảo sát để kiến tạo biến công cụ Gaussian Copula nội sinh chuẩn hóa.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Input Configuration Panel */}
        <div className="lg:col-span-1 space-y-4 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Cấu Hình Mô Hình Copula</h3>

          {/* Endogenous Regressor Selector */}
          <div>
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
              Biến Nghi Ngờ Nội Sinh (Endogenous P)
            </label>
            <select
              value={endogQId}
              onChange={(e) => setEndogQId(e.target.value)}
              className="w-full text-xs p-2 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            >
              <option value="">-- Chọn biến độc lập nội sinh --</option>
              {numericQuestions.map((q) => (
                <option key={q.id} value={q.id}>{q.title}</option>
              ))}
            </select>
          </div>

          {/* Outcome Variable Selector */}
          <div>
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
              Biến Phụ Thuộc / Kết Quả (Outcome Y)
            </label>
            <select
              value={outcomeQId}
              onChange={(e) => setOutcomeQId(e.target.value)}
              className="w-full text-xs p-2 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            >
              <option value="">-- Chọn biến phụ thuộc --</option>
              {numericQuestions.map((q) => (
                <option key={q.id} value={q.id}>{q.title}</option>
              ))}
            </select>
          </div>

          {/* Control Variables */}
          <div>
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
              Biến Kiểm Soát Bổ Sung (Covariates X)
            </label>
            <div className="max-h-32 overflow-y-auto space-y-1 border border-slate-200 dark:border-slate-700 rounded-md p-2 bg-white dark:bg-slate-900">
              {numericQuestions
                .filter((q) => q.id !== endogQId && q.id !== outcomeQId)
                .map((q) => (
                  <label
                    key={q.id}
                    className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 p-0.5 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={selectedControls.includes(q.id)}
                      onChange={() => toggleControl(q.id)}
                      className="rounded border-slate-300 text-cyan-600 focus:ring-cyan-500"
                    />
                    <span className="truncate">{q.title}</span>
                  </label>
                ))}
            </div>
          </div>

          {/* Bootstrap iterations & Scope */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label className="text-slate-600 dark:text-slate-400 block mb-1">Lượt Bootstrap</label>
              <select
                value={bootstraps}
                onChange={(e) => setBootstraps(parseInt(e.target.value))}
                className="w-full p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs"
              >
                <option value={100}>100 (Nhanh)</option>
                <option value={250}>250 (Chuẩn)</option>
                <option value={500}>500 (Độ tin cậy cao)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-600 dark:text-slate-400 block mb-1">Phạm Vi Mẫu</label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
                className="w-full p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs"
              >
                <option value="all">Tất cả mẫu</option>
                <option value="verified_clean">Chỉ mẫu sạch</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-700 text-white font-medium text-xs rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Đang Ước Lượng Copula...</span>
              </>
            ) : (
              <span>Chạy Hiệu Chỉnh Gaussian Copula</span>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Chưa có kết quả hiệu chỉnh nội sinh Copula
              </p>
              <p className="text-xs mt-1 max-w-sm">
                Chọn biến nội sinh nghi ngờ và biến kết quả, sau đó bấm &quot;Chạy Hiệu Chỉnh Gaussian Copula&quot;.
              </p>
            </div>
          )}

          {result && result.sample_diagnostics && (
            <div className="space-y-6">
              {/* Summary Stats Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Số Quan Sát (N)</span>
                  <span className="text-lg font-bold text-slate-900 dark:text-white font-mono">
                    {result.sample_diagnostics.n_observations}
                  </span>
                </div>
                <div className="p-3 bg-cyan-50 dark:bg-cyan-950/40 rounded-lg border border-cyan-200 dark:border-cyan-800">
                  <span className="text-[11px] text-cyan-600 dark:text-cyan-400 block">Kiểm Định Phi Chuẩn (JB)</span>
                  <span className="text-sm font-bold text-cyan-700 dark:text-cyan-300 font-mono">
                    p = {result.sample_diagnostics.jarque_bera_p_value.toFixed(4)}
                  </span>
                  <span className="text-[10px] text-cyan-500 block">
                    {result.sample_diagnostics.non_normality_satisfied ? 'Thỏa mãn điều kiện phi chuẩn' : 'Gần chuẩn (cảnh báo)'}
                  </span>
                </div>
                <div className="p-3 bg-purple-50 dark:bg-purple-950/40 rounded-lg border border-purple-200 dark:border-purple-800">
                  <span className="text-[11px] text-purple-600 dark:text-purple-400 block">Hệ Số Nội Sinh (ρ)</span>
                  <span className="text-lg font-bold text-purple-700 dark:text-purple-300 font-mono">
                    {result.copula_corrected?.copula_rho_parameter?.toFixed(4) || '0.0000'}
                  </span>
                  <span className="text-[10px] text-purple-500 block">
                    p = {result.copula_corrected?.p_value_rho?.toFixed(4)}
                  </span>
                </div>
                <div className="p-3 bg-amber-50 dark:bg-amber-950/40 rounded-lg border border-amber-200 dark:border-amber-800">
                  <span className="text-[11px] text-amber-600 dark:text-amber-400 block">Khoảng Sai Lệch OLS</span>
                  <span className="text-lg font-bold text-amber-700 dark:text-amber-300 font-mono">
                    {result.copula_corrected?.endogeneity_bias_gap?.toFixed(4)}
                  </span>
                  <span className="text-[10px] text-amber-600 dark:text-amber-400 block">
                    ({result.copula_corrected?.percentage_bias?.toFixed(1)}%)
                  </span>
                </div>
              </div>

              {/* Status Badges */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className={`px-2.5 py-1 rounded font-semibold border ${
                  result.copula_corrected?.is_endogeneity_significant
                    ? 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300 border-rose-200 dark:border-rose-800'
                    : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                }`}>
                  Chẩn Đoán: {result.sample_diagnostics.endogeneity_badge}
                </span>
                <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 font-mono">
                  Copula VIF: {result.sample_diagnostics.copula_vif.toFixed(2)} (&lt; 10 không cộng tuyến)
                </span>
              </div>

              {/* Comparison Table */}
              <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                <div className="px-4 py-2.5 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 font-semibold text-xs text-slate-800 dark:text-slate-200">
                  So Sánh Mô Hình: OLS Ngây Thơ (Bị Nội Sinh) vs Hiệu Chỉnh Gaussian Copula
                </div>
                <table className="w-full text-xs text-left text-slate-600 dark:text-slate-300">
                  <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300">
                    <tr>
                      <th className="py-2.5 px-3">Phương Pháp Ước Lượng</th>
                      <th className="py-2.5 px-3">Hệ Số Tác Động (β)</th>
                      <th className="py-2.5 px-3">Sai Số Chuẩn (SE)</th>
                      <th className="py-2.5 px-3">Khoảng Tin Cậy 95% CI</th>
                      <th className="py-2.5 px-3">R²</th>
                      <th className="py-2.5 px-3">Đánh Giá</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono">
                    <tr className="bg-amber-50/20 dark:bg-amber-950/10">
                      <td className="py-2.5 px-3 font-sans font-medium text-amber-800 dark:text-amber-300">
                        1. Naive OLS (Cổ điển)
                      </td>
                      <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                        {result.naive_ols?.beta.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-3">{result.naive_ols?.se.toFixed(4)}</td>
                      <td className="py-2.5 px-3">[{result.naive_ols?.ci_lower.toFixed(3)}, {result.naive_ols?.ci_upper.toFixed(3)}]</td>
                      <td className="py-2.5 px-3">{result.naive_ols?.r_squared.toFixed(3)}</td>
                      <td className="py-2.5 px-3 font-sans text-amber-700 dark:text-amber-400">
                        {result.copula_corrected?.is_endogeneity_significant ? 'Bị sai lệch nội sinh' : 'Chưa phát hiện sai lệch'}
                      </td>
                    </tr>
                    <tr className="bg-cyan-50/20 dark:bg-cyan-950/10">
                      <td className="py-2.5 px-3 font-sans font-medium text-cyan-800 dark:text-cyan-300">
                        2. Gaussian Copula (Park &amp; Gupta 2012)
                      </td>
                      <td className="py-2.5 px-3 font-bold text-cyan-600 dark:text-cyan-400">
                        {result.copula_corrected?.beta_copula.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-3">{result.copula_corrected?.se_bootstrap.toFixed(4)} (Boot)</td>
                      <td className="py-2.5 px-3">[{result.copula_corrected?.ci_lower_bootstrap.toFixed(3)}, {result.copula_corrected?.ci_upper_bootstrap.toFixed(3)}]</td>
                      <td className="py-2.5 px-3">{result.copula_corrected?.r_squared.toFixed(3)}</td>
                      <td className="py-2.5 px-3 font-sans text-emerald-600 dark:text-emerald-400 font-semibold">
                        Hiệu ứng nhân quả phi thiên lệch
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Dual-Panel SVG Visualization */}
              {result.svg_chart && (
                <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-slate-50 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider">
                      Biểu Đồ Trực Quan Gaussian Copula Dual-Panel
                    </h4>
                    <button
                      onClick={handleDownloadSVG}
                      className="px-2 py-1 text-xs font-medium text-cyan-600 hover:text-cyan-700 dark:text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Tải bản đồ SVG
                    </button>
                  </div>
                  <div
                    className="w-full overflow-x-auto flex justify-center"
                    dangerouslySetInnerHTML={{ __html: result.svg_chart }}
                  />
                </div>
              )}

              {/* APA 7th Edition Narrative */}
              {result.apa_narrative && (
                <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                      <span>Văn Bản Thuyết Minh Chuẩn APA 7th Edition</span>
                    </h4>
                    <button
                      onClick={handleCopyNarrative}
                      className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      {copied ? 'Đã sao chép!' : 'Sao chép'}
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
