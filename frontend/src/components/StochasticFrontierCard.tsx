import React, { useState } from 'react';
import {
  Factory,
  Gauge,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  Sparkles,
  RefreshCw,
  Info,
  CheckSquare,
  Square,
  BarChart3
} from 'lucide-react';
import { api } from '../api/client';
import { StochasticFrontierResult } from '../types/survey';

interface StochasticFrontierCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const StochasticFrontierCard: React.FC<StochasticFrontierCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StochasticFrontierResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [outputQid, setOutputQid] = useState<string>('');
  const [inputQids, setInputQids] = useState<string[]>([]);
  const [logTransform, setLogTransform] = useState<boolean>(true);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'coefficients' | 'efficiency' | 'svg'>('coefficients');

  const toggleInput = (qid: string) => {
    setInputQids(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!outputQid) {
      setError('Vui lòng chọn biến đầu ra sản xuất / doanh thu (Output Y).');
      return;
    }
    if (inputQids.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến đầu vào nguồn lực (Capital, Labor, Materials...).');
      return;
    }
    if (inputQids.includes(outputQid)) {
      setError('Biến đầu ra không được nằm trong danh sách biến đầu vào.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runStochasticFrontier(surveyId, {
        output_question_id: outputQid,
        input_question_ids: inputQids,
        log_transform: logTransform,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình Stochastic Frontier Analysis.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API Stochastic Frontier.');
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
            <Factory className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Stochastic Frontier Analysis & Technical Efficiency
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Aigner, Lovell & Schmidt (1977) · JLMS (1982)
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Phân rã kinh tế lượng vi mô: Biên sản xuất tối đa lý thuyết, sai số ngẫu nhiên <span className="font-mono text-emerald-400">v ~ N(0, σ_v²)</span> và độ kém hiệu quả kỹ thuật <span className="font-mono text-emerald-400">u ~ Half-Normal(0, σ_u²)</span>.
            </p>
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Đang tính toán SFA (MLE)...</span>
            </>
          ) : (
            <>
              <Gauge className="w-4 h-4" />
              <span>Ước lượng Biên Kỹ thuật</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 py-5 border-b border-slate-800 text-xs">
        {/* Output Question Y */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300 flex items-center gap-1.5">
            <span>Biến Đầu Ra Sản Xuất (Y):</span>
          </label>
          <select
            value={outputQid}
            onChange={(e) => setOutputQid(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="">-- Chọn biến đầu ra (Doanh thu/Sản lượng) --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title.length > 45 ? `${q.title.slice(0, 45)}...` : q.title}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400">Doanh thu, sản lượng, điểm số hiệu quả.</p>
        </div>

        {/* Specification & Log Transform */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Dạng Hàm Sản Xuất:</label>
          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={() => setLogTransform(prev => !prev)}
              className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors cursor-pointer"
            >
              {logTransform ? (
                <CheckSquare className="w-4 h-4 text-emerald-400" />
              ) : (
                <Square className="w-4 h-4 text-slate-500" />
              )}
              <span className="font-medium text-slate-200">
                Log-Log Cobb-Douglas (ln Y = β₀ + Σ β_k ln X_k)
              </span>
            </button>
          </div>
          <p className="text-[11px] text-slate-400">Tự động chuyển đổi log tự nhiên để hệ số β là độ co giãn (elasticity).</p>
        </div>

        {/* Scope */}
        <div className="space-y-1.5">
          <label className="font-medium text-slate-300">Phạm vi Mẫu:</label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">Tất cả phản hồi hợp lệ</option>
            <option value="verified_clean">Chỉ mẫu đã xác thực sạch (Verified Clean)</option>
          </select>
          <p className="text-[11px] text-slate-400">Loại bỏ phản hồi bất thường / gian lận nếu cần.</p>
        </div>

        {/* Help Tip */}
        <div className="space-y-1.5 bg-slate-800/30 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <span>
            Theo JLMS (1982), Technical Efficiency <span className="text-emerald-300 font-mono">TE_i = exp(-E[u|ε]) ∈ (0, 100%]</span>. Doanh nghiệp đạt 100% nằm trên đường biên tối ưu công nghệ.
          </span>
        </div>
      </div>

      {/* Input Questions Selection */}
      <div className="py-4 border-b border-slate-800">
        <label className="font-medium text-xs text-slate-300 flex items-center justify-between mb-2">
          <span>Chọn Các Biến Đầu Vào Nguồn Lực (Input Variables X_k):</span>
          <span className="text-slate-400 font-normal">Đã chọn: {inputQids.length} biến</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-36 overflow-y-auto pr-1">
          {questions
            .filter((q) => q.id !== outputQid)
            .map((q) => {
              const isSelected = inputQids.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleInput(q.id)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors cursor-pointer border ${
                    isSelected
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  )}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="my-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="mt-6 space-y-6">
          {/* Key Metrics Banners */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Hiệu Quả TB (Mean TE)</span>
              <span className="text-lg font-bold text-emerald-400">
                {result.diagnostics.mean_technical_efficiency_pct.toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Trung vị: {result.diagnostics.median_technical_efficiency_pct.toFixed(1)}%
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Biên Độ Hiệu Quả</span>
              <span className="text-base font-bold text-slate-200">
                {result.diagnostics.min_technical_efficiency_pct.toFixed(1)}% - {result.diagnostics.max_technical_efficiency_pct.toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Độ lệch chuẩn: ±{result.diagnostics.std_technical_efficiency_pct.toFixed(1)}%
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Tỷ Số Lambda (λ = σ_u/σ_v)</span>
              <span className="text-lg font-bold text-amber-400">
                {result.diagnostics.lambda_ratio.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                γ (phần kém hiệu quả): {(result.diagnostics.gamma_variance_share * 100).toFixed(1)}%
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Quy Mô Sản Xuất (RTS)</span>
              <span className="text-lg font-bold text-indigo-400">
                {result.diagnostics.returns_to_scale.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5 truncate" title={result.diagnostics.rts_verdict}>
                {result.diagnostics.returns_to_scale > 1.02 ? 'Tăng theo quy mô (IRS)' : result.diagnostics.returns_to_scale < 0.98 ? 'Giảm theo quy mô (DRS)' : 'Quy mô không đổi (CRS)'}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Kiểm Định LR (u &gt; 0)</span>
              <span className={`text-base font-bold ${result.diagnostics.has_inefficiency ? 'text-emerald-400' : 'text-slate-400'}`}>
                LR = {result.diagnostics.lr_test_stat.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                p = {result.diagnostics.lr_test_pval < 0.001 ? '< 0.001' : result.diagnostics.lr_test_pval.toFixed(3)}
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Độ Lệch Phần Dư OLS</span>
              <span className={`text-base font-bold ${result.diagnostics.ols_residual_skewness < 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {result.diagnostics.ols_residual_skewness.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {result.diagnostics.ols_residual_skewness < 0 ? 'Lệch trái (Đúng chuẩn SFA)' : 'Lệch phải (Cần kiểm tra)'}
              </span>
            </div>
          </div>

          {/* Verdict Banner */}
          <div className={`p-4 rounded-xl border text-xs flex items-center justify-between gap-4 ${
            result.diagnostics.has_inefficiency
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
              : 'bg-slate-800/60 border-slate-700 text-slate-300'
          }`}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>
                <strong>Kết luận Kiểm định Giả thuyết:</strong> {result.diagnostics.inefficiency_verdict} (Số quan sát N = {result.diagnostics.n_units}, Biến đầu vào K = {result.diagnostics.n_inputs}).
              </span>
            </div>
            <span className="text-[11px] font-mono opacity-80 shrink-0">
              SFA LL = {result.diagnostics.sfa_log_likelihood.toFixed(2)} vs OLS LL = {result.diagnostics.ols_log_likelihood.toFixed(2)}
            </span>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('coefficients')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'coefficients'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Hệ Số Biên Sản Xuất & Độ Co Giãn
            </button>
            <button
              onClick={() => setActiveTab('efficiency')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'efficiency'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Điểm Hiệu Quả Kỹ Thuật Cá Thể (JLMS)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'svg'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Biểu Đồ Trực Quan Hóa SFA</span>
            </button>
          </div>

          {/* Tab 1: Coefficients */}
          {activeTab === 'coefficients' && result.coefficients && (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Biến Giải Thích</th>
                    <th className="py-2.5 px-3 text-right">Hệ Số Biên (β)</th>
                    <th className="py-2.5 px-3 text-right">Độ Co Giãn (Elasticity)</th>
                    <th className="py-2.5 px-3 text-right">Sai Số Chuẩn (SE)</th>
                    <th className="py-2.5 px-3 text-right">t-stat</th>
                    <th className="py-2.5 px-3 text-right">p-value</th>
                    <th className="py-2.5 px-3 text-center">Khoảng Tin Cậy 95%</th>
                    <th className="py-2.5 px-3 text-center">Ý Nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {result.coefficients.map((row, idx) => {
                    const qObj = questions.find(q => q.id === row.variable);
                    const label = row.is_intercept ? 'Hằng số chặn (Intercept β₀)' : (qObj ? qObj.title : row.variable);
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-sans text-white font-medium">
                          {label}
                        </td>
                        <td className="py-2.5 px-3 text-right text-emerald-400 font-semibold">
                          {row.frontier_coefficient.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-indigo-300">
                          {row.elasticity_estimate.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-400">
                          {row.standard_error.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-300">
                          {row.t_statistic.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <span className={row.p_value < 0.05 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                            {row.p_value < 0.001 ? '< 0.001' : row.p_value.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-center text-slate-400">
                          [{row.ci_95_lower.toFixed(3)}, {row.ci_95_upper.toFixed(3)}]
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {row.is_significant ? (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">
                              p &lt; 0.05
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400 text-[10px]">
                              ns
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Individual Efficiency Sample */}
          {activeTab === 'efficiency' && result.individual_efficiency_sample && (
            <div className="space-y-4">
              <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-80 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">STT Đơn vị (#)</th>
                      <th className="py-2.5 px-3 text-right">Độ Kém Hiệu Quả (u_i)</th>
                      <th className="py-2.5 px-3 text-right">Điểm Hiệu Quả Kỹ Thuật (TE_i)</th>
                      <th className="py-2.5 px-3">Thanh Tiến Trình Hiệu Quả</th>
                      <th className="py-2.5 px-3 text-center">Xếp Loại</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {result.individual_efficiency_sample.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2 px-3 text-slate-400">Unit #{row.unit_index}</td>
                        <td className="py-2 px-3 text-right text-amber-400">{row.technical_inefficiency_u.toFixed(4)}</td>
                        <td className="py-2 px-3 text-right font-bold text-emerald-400">{row.technical_efficiency_pct.toFixed(2)}%</td>
                        <td className="py-2 px-3">
                          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                            <div
                              className={`h-full ${
                                row.technical_efficiency_pct >= 90
                                  ? 'bg-emerald-500'
                                  : row.technical_efficiency_pct >= 75
                                  ? 'bg-indigo-500'
                                  : row.technical_efficiency_pct >= 60
                                  ? 'bg-amber-500'
                                  : 'bg-rose-500'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(0, row.technical_efficiency_pct))}%` }}
                            />
                          </div>
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                            row.technical_efficiency_pct >= 90
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : row.technical_efficiency_pct >= 75
                              ? 'bg-indigo-500/20 text-indigo-300'
                              : row.technical_efficiency_pct >= 60
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-rose-500/20 text-rose-300'
                          }`}>
                            {row.technical_efficiency_pct >= 90
                              ? 'Xuất sắc'
                              : row.technical_efficiency_pct >= 75
                              ? 'Khá'
                              : row.technical_efficiency_pct >= 60
                              ? 'Trung bình'
                              : 'Kém'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 3: SVG Visualization */}
          {activeTab === 'svg' && result.svg_visualization && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col items-center justify-center overflow-hidden">
              <div
                className="w-full max-w-4xl flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-800/40 border border-slate-700/60 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  Báo Cáo Học Thuật Chuẩn APA 7th (Stochastic Frontier Production Benchmark)
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-emerald-300 transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép đoạn văn'}</span>
                </button>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line bg-slate-900/50 p-3 rounded-lg border border-slate-800/80">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
