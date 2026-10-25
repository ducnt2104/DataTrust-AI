import React, { useState } from 'react';
import { api } from '../api/client';
import { DynamicFactorModelResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface DynamicFactorModelCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const DynamicFactorModelCard: React.FC<DynamicFactorModelCardProps> = ({
  surveyId,
  questions
}) => {
  const numericQuestions = questions.filter(
    (q) => q.question_type === 'number' || q.question_type === 'rating'
  );

  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(
    numericQuestions.slice(0, 4).map((q) => q.id)
  );
  const [waveQId, setWaveQId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DynamicFactorModelResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'trajectory' | 'decomposition'>('trajectory');

  const toggleIndicator = (id: string) => {
    setSelectedIndicators((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    setSelectedIndicators(numericQuestions.map((q) => q.id));
  };

  const clearSelection = () => {
    setSelectedIndicators([]);
  };

  const handleRunAnalysis = async () => {
    if (selectedIndicators.length < 2) {
      setError('Vui lòng chọn ít nhất 2 biến chỉ báo theo dõi chuỗi thời gian.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.runDynamicFactorAnalysis(surveyId, {
        indicator_question_ids: selectedIndicators,
        wave_question_id: waveQId ? waveQId : undefined,
        scope
      });
      setResult(data);
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực hiện mô hình nhân tố động.');
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
    link.download = `dynamic-factor-model-${surveyId}.svg`;
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
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300">
              Longitudinal Signal Extraction
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
              Stock &amp; Watson (2002) · Durbin &amp; Koopman (2012)
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
            Mô Hình Nhân Tố Động Chuỗi Thời Gian (Dynamic Factor Model / DFM)
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1 max-w-3xl">
            Tách biệt xu hướng vĩ mô thực cốt lõi khỏi nhiễu ngẫu nhiên đặc thù của từng đợt khảo sát lặp (Repeated Waves). 
            Áp dụng thuật toán Lọc Kalman tiến và Làm mượt Rauch-Tung-Striebel (RTS) lùi trong không gian trạng thái (State-Space), 
            cung cấp phân rã phương sai tín hiệu/nhiễu và khoảng tin cậy 95% chuẩn mực.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Input Configuration Panel */}
        <div className="lg:col-span-1 space-y-4 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Cấu Hình Nhân Tố Động</h3>

          {/* Indicator Variables Checklist */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Biến Chỉ Báo Theo Dõi ({selectedIndicators.length} đã chọn)
              </label>
              <div className="flex gap-2">
                <button
                  onClick={selectAll}
                  className="text-xs text-sky-600 dark:text-sky-400 hover:underline"
                >
                  Tất cả
                </button>
                <span className="text-slate-400">·</span>
                <button
                  onClick={clearSelection}
                  className="text-xs text-slate-500 hover:underline"
                >
                  Bỏ chọn
                </button>
              </div>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1.5 border border-slate-200 dark:border-slate-700 rounded-md p-2 bg-white dark:bg-slate-900">
              {numericQuestions.map((q) => (
                <label
                  key={q.id}
                  className="flex items-start gap-2 p-1 text-xs hover:bg-slate-100 dark:hover:bg-slate-800 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedIndicators.includes(q.id)}
                    onChange={() => toggleIndicator(q.id)}
                    className="rounded border-slate-300 text-sky-600 focus:ring-sky-500 mt-0.5"
                  />
                  <span className="text-slate-800 dark:text-slate-200 truncate">{q.title}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Wave identifier question */}
          <div>
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
              Câu Hỏi Xác Định Đợt Khảo Sát (Tùy chọn)
            </label>
            <select
              value={waveQId}
              onChange={(e) => setWaveQId(e.target.value)}
              className="w-full text-xs p-2 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            >
              <option value="">-- Tự động phân đoạn theo thời gian gửi (Tự động) --</option>
              {questions.map((q) => (
                <option key={q.id} value={q.id}>{q.title}</option>
              ))}
            </select>
            <p className="text-[11px] text-slate-500 mt-1">
              Nếu để trống, hệ thống sẽ tự động phân chia phản hồi theo trình tự thời gian nộp bài.
            </p>
          </div>

          {/* Scope selection */}
          <div>
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">Phạm Vi Mẫu</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
              className="w-full text-xs p-2 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            >
              <option value="all">Tất cả phản hồi hợp lệ</option>
              <option value="verified_clean">Chỉ phản hồi đã xác thực sạch</option>
            </select>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Đang Lọc Kalman &amp; RTS Smoother...</span>
              </>
            ) : (
              <span>Chạy Mô Hình Nhân Tố Động DFM</span>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Chưa có kết quả phân tích DFM
              </p>
              <p className="text-xs mt-1 max-w-sm">
                Chọn ít nhất 2 biến chỉ báo theo dõi chuỗi đợt khảo sát, sau đó bấm &quot;Chạy Mô Hình Nhân Tố Động DFM&quot;.
              </p>
            </div>
          )}

          {result && result.sample_diagnostics && (
            <div className="space-y-6">
              {/* Summary Stats Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Số Đợt Khảo Sát (T)</span>
                  <span className="text-lg font-bold text-slate-900 dark:text-white font-mono">
                    {result.sample_diagnostics.total_waves_t}
                  </span>
                </div>
                <div className="p-3 bg-sky-50 dark:bg-sky-950/40 rounded-lg border border-sky-200 dark:border-sky-800">
                  <span className="text-[11px] text-sky-600 dark:text-sky-400 block">Số Biến Chỉ Báo (P)</span>
                  <span className="text-lg font-bold text-sky-700 dark:text-sky-300 font-mono">
                    {result.sample_diagnostics.total_indicators_p}
                  </span>
                </div>
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block">Quán Tính Chuỗi AR(1)</span>
                  <span className="text-lg font-bold text-emerald-700 dark:text-emerald-300 font-mono">
                    {result.sample_diagnostics.ar1_persistence.toFixed(3)}
                  </span>
                </div>
                <div className="p-3 bg-purple-50 dark:bg-purple-950/40 rounded-lg border border-purple-200 dark:border-purple-800">
                  <span className="text-[11px] text-purple-600 dark:text-purple-400 block">Tỷ Lệ Tín Hiệu Cốt Lõi</span>
                  <span className="text-lg font-bold text-purple-700 dark:text-purple-300 font-mono">
                    {(result.sample_diagnostics.overall_signal_variance_share * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* State Space Filter Badge */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2.5 py-1 rounded bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300 border border-sky-200 dark:border-sky-800 font-mono">
                  Thuật toán: {result.sample_diagnostics.state_space_filter}
                </span>
                <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 font-mono">
                  Tổng quan sát n = {result.sample_diagnostics.total_observations}
                </span>
              </div>

              {/* Dual-Panel SVG Visualization */}
              {result.svg_chart && (
                <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-slate-50 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider">
                      Biểu Đồ Trực Quan DFM: Quỹ Đạo Lọc Kalman &amp; Phân Rã Phương Sai
                    </h4>
                    <button
                      onClick={handleDownloadSVG}
                      className="px-2 py-1 text-xs font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 hover:underline flex items-center gap-1"
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
                    onClick={() => setActiveTab('trajectory')}
                    className={`pb-2 text-xs font-semibold border-b-2 transition-colors ${
                      activeTab === 'trajectory'
                        ? 'border-sky-600 text-sky-600 dark:text-sky-400'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Bảng Quỹ Đạo Theo Đợt ({result.trajectory?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab('decomposition')}
                    className={`pb-2 text-xs font-semibold border-b-2 transition-colors ${
                      activeTab === 'decomposition'
                        ? 'border-sky-600 text-sky-600 dark:text-sky-400'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Phân Rã Phương Sai ({result.variance_decomposition?.length || 0})
                  </button>
                </div>

                {/* Tab 1: Trajectory Points Table */}
                {activeTab === 'trajectory' && result.trajectory && (
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full text-xs text-left text-slate-600 dark:text-slate-300">
                      <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        <tr>
                          <th className="py-2 px-3">Đợt (Wave)</th>
                          <th className="py-2 px-3">Cỡ Mẫu (Nt)</th>
                          <th className="py-2 px-3">Lọc Kalman (at|t)</th>
                          <th className="py-2 px-3">Làm Mượt RTS (ft|T)</th>
                          <th className="py-2 px-3">Sai Số Chuẩn (SE)</th>
                          <th className="py-2 px-3">Khoảng Tin Cậy 95% CI</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono">
                        {result.trajectory.map((pt, idx) => (
                          <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-sans font-medium text-slate-900 dark:text-white">
                              Đợt {pt.wave_label}
                            </td>
                            <td className="py-2 px-3">{pt.sample_size}</td>
                            <td className="py-2 px-3 text-purple-600 dark:text-purple-400">{pt.filtered_state.toFixed(4)}</td>
                            <td className="py-2 px-3 font-bold text-sky-600 dark:text-sky-400">{pt.smoothed_factor.toFixed(4)}</td>
                            <td className="py-2 px-3">{pt.standard_error.toFixed(4)}</td>
                            <td className="py-2 px-3">[{pt.ci_lower_95.toFixed(3)}, {pt.ci_upper_95.toFixed(3)}]</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Tab 2: Variance Decomposition Table */}
                {activeTab === 'decomposition' && result.variance_decomposition && (
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full text-xs text-left text-slate-600 dark:text-slate-300">
                      <thead className="text-[11px] uppercase bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        <tr>
                          <th className="py-2 px-3">Biến Chỉ Báo</th>
                          <th className="py-2 px-3">Hệ Số Tải (λ)</th>
                          <th className="py-2 px-3">Tỷ Lệ Tín Hiệu Chung (R²)</th>
                          <th className="py-2 px-3">Nhiễu Đặc Thù</th>
                          <th className="py-2 px-3">Tỷ Số Tín Hiệu / Nhiễu (SNR)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono">
                        {result.variance_decomposition.map((row, idx) => (
                          <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-sans font-medium text-slate-800 dark:text-slate-200">{row.title}</td>
                            <td className="py-2 px-3">{row.loading_lambda.toFixed(4)}</td>
                            <td className="py-2 px-3 font-bold text-emerald-600 dark:text-emerald-400">
                              {(row.common_variance_share_r2 * 100).toFixed(1)}%
                            </td>
                            <td className="py-2 px-3 text-slate-500">
                              {(row.idiosyncratic_noise_share * 100).toFixed(1)}%
                            </td>
                            <td className="py-2 px-3 font-bold text-sky-600 dark:text-sky-400">
                              {row.signal_to_noise_ratio.toFixed(2)}x
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
                      className="text-xs text-sky-600 dark:text-sky-400 hover:underline flex items-center gap-1"
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
