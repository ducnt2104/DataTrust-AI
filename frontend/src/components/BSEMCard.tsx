import React, { useState } from 'react';
import { api } from '../api/client';
import { BSEMResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface BSEMCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const BSEMCard: React.FC<BSEMCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter(
    (q) => q.question_type === 'number' || q.question_type === 'rating'
  );

  // Initialize two factors with default assignment if enough questions exist
  const [factors, setFactors] = useState<Array<{ name: string; itemIds: string[] }>>([
    {
      name: 'F1_TienDe',
      itemIds: numericQuestions.slice(0, 3).map((q) => q.id)
    },
    {
      name: 'F2_KetQua',
      itemIds: numericQuestions.slice(3, 6).map((q) => q.id)
    }
  ]);

  const [structuralSource, setStructuralSource] = useState<string>('F1_TienDe');
  const [structuralTarget, setStructuralTarget] = useState<string>('F2_KetQua');
  const [priorCrossLoadingSd, setPriorCrossLoadingSd] = useState<number>(0.01);
  const [iterations, setIterations] = useState<number>(800);
  const [burnin, setBurnin] = useState<number>(300);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BSEMResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'structural' | 'loadings' | 'sensitivity'>('structural');

  const addFactor = () => {
    const nextIdx = factors.length + 1;
    setFactors([...factors, { name: `F${nextIdx}_YeuTo`, itemIds: [] }]);
  };

  const removeFactor = (idx: number) => {
    if (factors.length <= 2) return;
    const newFactors = factors.filter((_, i) => i !== idx);
    setFactors(newFactors);
  };

  const updateFactorName = (idx: number, name: string) => {
    const newFactors = [...factors];
    newFactors[idx].name = name;
    setFactors(newFactors);
  };

  const toggleItemForFactor = (factorIdx: number, itemId: string) => {
    const newFactors = [...factors];
    const currentItems = newFactors[factorIdx].itemIds;
    if (currentItems.includes(itemId)) {
      newFactors[factorIdx].itemIds = currentItems.filter((id) => id !== itemId);
    } else {
      newFactors[factorIdx].itemIds = [...currentItems, itemId];
    }
    setFactors(newFactors);
  };

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Validate factors
      for (const f of factors) {
        if (f.itemIds.length < 2) {
          throw new Error(`Bien tiem an "${f.name}" can it nhat 2 bien quan sat.`);
        }
      }

      const measurementSpec: Record<string, string[]> = {};
      factors.forEach((f) => {
        measurementSpec[f.name] = f.itemIds;
      });

      const data = await api.runBSEMAnalysis(surveyId, {
        measurement_spec: measurementSpec,
        structural_regressions: [{ source: structuralSource, target: structuralTarget }],
        prior_cross_loading_sd: priorCrossLoadingSd,
        n_iterations: iterations,
        n_burnin: burnin,
        n_chains: 2,
        scope
      });

      setResult(data);
    } catch (err: any) {
      setError(err?.message || 'Co loi xay ra khi thuc hien mo hinh Bayes BSEM.');
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
    link.download = `bsem-analysis-${surveyId}.svg`;
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
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300">
              MCMC Gibbs Sampling &amp; Prior Sensitivity
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
              Muthén &amp; Asparouhov (2012) · Gelman et al. (2013)
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
            Mô Hình Cấu Trúc Tuyến Tính Bayes (Bayesian SEM / BSEM)
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1 max-w-3xl">
            Giải quyết bế tắc nhận diện mô hình SEM cổ điển bằng cách thay thế các ràng buộc zero cứng nhắc bằng phân phối tiên nghiệm co rút nhỏ 
            (Informative Small-Variance Priors N(0, σ²₀)) trên các hệ số tải chéo. Cung cấp chẩn đoán hội tụ Gelman-Rubin R-hat, 
            kích thước mẫu hiệu dụng ESS, độ tương thích Posterior Predictive p-value (PPP) và kiểm tra độ nhạy tiên nghiệm.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Input Configuration Panel */}
        <div className="lg:col-span-1 space-y-4 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Cấu Trúc Mô Hình BSEM</h3>
            <button
              onClick={addFactor}
              className="text-xs text-purple-600 dark:text-purple-400 hover:underline font-medium"
            >
              + Thêm Yếu Tố
            </button>
          </div>

          {/* Factor Definitions */}
          <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
            {factors.map((factor, fIdx) => (
              <div key={fIdx} className="p-2.5 bg-white dark:bg-slate-900 rounded-md border border-slate-200 dark:border-slate-700 text-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <input
                    type="text"
                    value={factor.name}
                    onChange={(e) => updateFactorName(fIdx, e.target.value)}
                    className="font-semibold text-xs bg-transparent border-b border-slate-300 dark:border-slate-700 focus:outline-none focus:border-purple-500 text-slate-900 dark:text-slate-100"
                    placeholder="Tên biến tiềm ẩn"
                  />
                  {factors.length > 2 && (
                    <button
                      onClick={() => removeFactor(fIdx)}
                      className="text-slate-400 hover:text-red-500 text-[10px]"
                    >
                      Xóa
                    </button>
                  )}
                </div>
                <div className="text-[11px] text-slate-500 mb-1">
                  Chọn chỉ báo chính ({factor.itemIds.length} đã chọn):
                </div>
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {numericQuestions.map((q) => (
                    <label
                      key={q.id}
                      className="flex items-center gap-1.5 text-[11px] text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/60 p-0.5 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={factor.itemIds.includes(q.id)}
                        onChange={() => toggleItemForFactor(fIdx, q.id)}
                        className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="truncate">{q.title}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Structural Path Selector */}
          <div className="p-2.5 bg-white dark:bg-slate-900 rounded-md border border-slate-200 dark:border-slate-700 space-y-2">
            <span className="text-xs font-semibold text-slate-900 dark:text-white block">Đường Dẫn Cấu Trúc (γ)</span>
            <div className="flex items-center gap-2 text-xs">
              <select
                value={structuralSource}
                onChange={(e) => setStructuralSource(e.target.value)}
                className="w-1/2 p-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-xs"
              >
                {factors.map((f) => (
                  <option key={f.name} value={f.name}>{f.name}</option>
                ))}
              </select>
              <span className="text-slate-400 font-bold">&rarr;</span>
              <select
                value={structuralTarget}
                onChange={(e) => setStructuralTarget(e.target.value)}
                className="w-1/2 p-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-xs"
              >
                {factors.map((f) => (
                  <option key={f.name} value={f.name}>{f.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Prior Settings */}
          <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-700">
            <div>
              <div className="flex justify-between items-center text-xs text-slate-700 dark:text-slate-300 mb-1">
                <span>Độ lệch chuẩn tiên nghiệm co rút (σ₀):</span>
                <span className="font-bold font-mono text-purple-600 dark:text-purple-400">{priorCrossLoadingSd}</span>
              </div>
              <select
                value={priorCrossLoadingSd}
                onChange={(e) => setPriorCrossLoadingSd(parseFloat(e.target.value))}
                className="w-full text-xs p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              >
                <option value={0.005}>0.005 (Co rút rất mạnh N(0, 0.000025))</option>
                <option value={0.01}>0.010 (Chuẩn Muthén-Asparouhov N(0, 0.0001))</option>
                <option value={0.05}>0.050 (Co rút vừa N(0, 0.0025))</option>
                <option value={0.10}>0.100 (Co rút nới lỏng N(0, 0.01))</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-slate-600 dark:text-slate-400 block mb-1">Số lượt Gibbs</label>
                <input
                  type="number"
                  value={iterations}
                  onChange={(e) => setIterations(parseInt(e.target.value) || 400)}
                  className="w-full p-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                />
              </div>
              <div>
                <label className="text-slate-600 dark:text-slate-400 block mb-1">Số lượt Burn-in</label>
                <input
                  type="number"
                  value={burnin}
                  onChange={(e) => setBurnin(parseInt(e.target.value) || 150)}
                  className="w-full p-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">Phạm Vi Mẫu</label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
                className="w-full text-xs p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              >
                <option value="all">Tất cả phản hồi hợp lệ</option>
                <option value="verified_clean">Chỉ phản hồi đã xác thực sạch</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-purple-600 hover:bg-purple-700 text-white font-medium text-xs rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Đang Lấy Mẫu MCMC Gibbs...</span>
              </>
            ) : (
              <span>Chạy Mô Hình Bayes BSEM</span>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Chưa có kết quả phân tích BSEM
              </p>
              <p className="text-xs mt-1 max-w-sm">
                Cấu hình ít nhất 2 biến tiềm ẩn và các biến chỉ báo, sau đó bấm &quot;Chạy Mô Hình Bayes BSEM&quot;.
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
                <div className="p-3 bg-purple-50 dark:bg-purple-950/40 rounded-lg border border-purple-200 dark:border-purple-800">
                  <span className="text-[11px] text-purple-600 dark:text-purple-400 block">Mô Hình Fit (PPP)</span>
                  <span className="text-lg font-bold text-purple-700 dark:text-purple-300 font-mono">
                    {result.sample_diagnostics.posterior_predictive_p_value.toFixed(3)}
                  </span>
                </div>
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block">Hội Tụ Gelman-Rubin</span>
                  <span className="text-lg font-bold text-emerald-700 dark:text-emerald-300 font-mono">
                    {result.structural_paths?.[0]?.gelman_rubin_r_hat?.toFixed(4) || '1.000'}
                  </span>
                </div>
                <div className="p-3 bg-amber-50 dark:bg-amber-950/40 rounded-lg border border-amber-200 dark:border-amber-800">
                  <span className="text-[11px] text-amber-600 dark:text-amber-400 block">Độ Nhạy Tiên Nghiệm</span>
                  <span className="text-xs font-bold text-amber-700 dark:text-amber-300 truncate block mt-1">
                    {result.sample_diagnostics.prior_robustness_status}
                  </span>
                </div>
              </div>

              {/* Status Badges */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2.5 py-1 rounded bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                  Độ Phù Hợp: <strong>{result.sample_diagnostics.model_fit_badge}</strong>
                </span>
                <span className="px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  Độ Bền Vững: <strong>{result.sample_diagnostics.prior_robustness_badge}</strong>
                </span>
                <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 font-mono">
                  MCMC: {result.sample_diagnostics.n_chains} chains × {result.sample_diagnostics.n_iterations} draws (burn-in: {result.sample_diagnostics.n_burnin})
                </span>
              </div>

              {/* Dual-Panel SVG Visualization */}
              {result.svg_chart && (
                <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-slate-50 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider">
                      Biểu Đồ Trực Quan BSEM: Chuỗi Gibbs &amp; Sơ Đồ Cấu Trúc
                    </h4>
                    <button
                      onClick={handleDownloadSVG}
                      className="px-2 py-1 text-xs font-medium text-purple-600 hover:text-purple-700 dark:text-purple-400 hover:underline flex items-center gap-1"
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

              {/* Sub-tabs for detailed results */}
              <div>
                <div className="flex border-b border-slate-200 dark:border-slate-700 mb-3 gap-4">
                  <button
                    onClick={() => setActiveTab('structural')}
                    className={`pb-2 text-xs font-semibold border-b-2 transition-colors ${
                      activeTab === 'structural'
                        ? 'border-purple-600 text-purple-600 dark:text-purple-400'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Đường Dẫn Cấu Trúc ({result.structural_paths?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab('loadings')}
                    className={`pb-2 text-xs font-semibold border-b-2 transition-colors ${
                      activeTab === 'loadings'
                        ? 'border-purple-600 text-purple-600 dark:text-purple-400'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Bảng Hệ Số Tải ({result.loadings?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab('sensitivity')}
                    className={`pb-2 text-xs font-semibold border-b-2 transition-colors ${
                      activeTab === 'sensitivity'
                        ? 'border-purple-600 text-purple-600 dark:text-purple-400'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Độ Nhạy Tiên Nghiệm ({result.prior_sensitivity?.length || 0})
                  </button>
                </div>

                {/* Tab 1: Structural Paths */}
                {activeTab === 'structural' && result.structural_paths && (
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full text-xs text-left text-slate-600 dark:text-slate-300">
                      <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        <tr>
                          <th className="py-2 px-3">Đường Dẫn</th>
                          <th className="py-2 px-3">Hậu Nghiệm γ</th>
                          <th className="py-2 px-3">SD</th>
                          <th className="py-2 px-3">95% Credible Interval</th>
                          <th className="py-2 px-3">R-hat</th>
                          <th className="py-2 px-3">ESS</th>
                          <th className="py-2 px-3">p-Bayes</th>
                          <th className="py-2 px-3">Ý Nghĩa</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono">
                        {result.structural_paths.map((sp, idx) => (
                          <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                              {sp.source_factor} &rarr; {sp.target_factor}
                            </td>
                            <td className="py-2 px-3 font-bold text-purple-600 dark:text-purple-400">
                              {sp.posterior_mean.toFixed(4)}
                            </td>
                            <td className="py-2 px-3">{sp.posterior_sd.toFixed(4)}</td>
                            <td className="py-2 px-3">[{sp.ci_lower.toFixed(3)}, {sp.ci_upper.toFixed(3)}]</td>
                            <td className="py-2 px-3">
                              <span className={sp.gelman_rubin_r_hat <= 1.1 ? 'text-emerald-600' : 'text-red-500'}>
                                {sp.gelman_rubin_r_hat.toFixed(4)}
                              </span>
                            </td>
                            <td className="py-2 px-3">{sp.effective_sample_size.toFixed(1)}</td>
                            <td className="py-2 px-3">{sp.bayesian_p_value.toFixed(4)}</td>
                            <td className="py-2 px-3 font-sans">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                sp.is_significant
                                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300'
                                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                              }`}>
                                {sp.is_significant ? 'Có ý nghĩa (p < .05)' : 'Chưa ý nghĩa'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Tab 2: Loadings Table */}
                {activeTab === 'loadings' && result.loadings && (
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden max-h-72 overflow-y-auto">
                    <table className="w-full text-xs text-left text-slate-600 dark:text-slate-300">
                      <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 sticky top-0">
                        <tr>
                          <th className="py-2 px-3">Biến Chỉ Báo</th>
                          <th className="py-2 px-3">Yếu Tố</th>
                          <th className="py-2 px-3">Loại Phân Phối Tiên Nghiệm</th>
                          <th className="py-2 px-3">Hậu Nghiệm λ</th>
                          <th className="py-2 px-3">SD</th>
                          <th className="py-2 px-3">95% CI</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono">
                        {result.loadings.map((load, idx) => (
                          <tr key={idx} className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 ${load.is_primary ? 'bg-purple-50/20 dark:bg-purple-950/10' : ''}`}>
                            <td className="py-2 px-3 font-sans font-medium text-slate-800 dark:text-slate-200">{load.item_title}</td>
                            <td className="py-2 px-3 font-sans">{load.factor_name}</td>
                            <td className="py-2 px-3 font-sans">
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${load.is_primary ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300'}`}>
                                {load.is_primary ? 'Chỉ báo chính' : 'Tải chéo co rút N(0, σ₀²)'}
                              </span>
                            </td>
                            <td className="py-2 px-3 font-bold">{load.posterior_mean.toFixed(4)}</td>
                            <td className="py-2 px-3">{load.posterior_sd.toFixed(4)}</td>
                            <td className="py-2 px-3">[{load.ci_lower.toFixed(3)}, {load.ci_upper.toFixed(3)}]</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Tab 3: Sensitivity */}
                {activeTab === 'sensitivity' && result.prior_sensitivity && (
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full text-xs text-left text-slate-600 dark:text-slate-300">
                      <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        <tr>
                          <th className="py-2 px-3">Độ Lệch Chuẩn Tiên Nghiệm (σ₀)</th>
                          <th className="py-2 px-3">Phương Sai Tiên Nghiệm (σ₀²)</th>
                          <th className="py-2 px-3">Ước Lượng Hậu Nghiệm γ</th>
                          <th className="py-2 px-3">Độ Trôi Tuyệt Đối (|Δγ|)</th>
                          <th className="py-2 px-3">Đánh Giá Tính Bền Vững</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono">
                        {result.prior_sensitivity.map((sens, idx) => (
                          <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-bold text-slate-900 dark:text-white">{sens.prior_sd}</td>
                            <td className="py-2 px-3">{sens.prior_variance.toFixed(6)}</td>
                            <td className="py-2 px-3 font-bold text-purple-600 dark:text-purple-400">{sens.posterior_mean_beta.toFixed(4)}</td>
                            <td className="py-2 px-3">{sens.absolute_drift_from_baseline.toFixed(4)}</td>
                            <td className="py-2 px-3 font-sans">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                sens.absolute_drift_from_baseline < 0.08
                                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300'
                                  : 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300'
                              }`}>
                                {sens.absolute_drift_from_baseline < 0.08 ? 'Vững chắc' : 'Độ lệch vừa'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* APA 7th Edition Narrative */}
              {result.apa_narrative && (
                <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                      <span>Văn Bản Thuyết Minh Chuẩn APA 7th Edition</span>
                    </h4>
                    <button
                      onClick={handleCopyNarrative}
                      className="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1"
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
