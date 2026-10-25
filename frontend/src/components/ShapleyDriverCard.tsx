import React, { useState } from 'react';
import { ShapleyDriverResult } from '../types/survey';
import { api } from '../api/client';

interface ShapleyDriverCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const ShapleyDriverCard: React.FC<ShapleyDriverCardProps> = ({ surveyId, questions }) => {
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>([]);
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ShapleyDriverResult | null>(null);

  // Eligible questions (numeric, scales, likert, ranking, single choice)
  const eligibleQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'matrix' ||
      q.question_type === 'ranking' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'dropdown'
  );

  const toggleDriver = (qid: string) => {
    setSelectedDrivers((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const selectAllEligible = () => {
    const withoutOutcome = eligibleQuestions.filter((q) => q.id !== outcomeQid);
    if (selectedDrivers.length === withoutOutcome.length) {
      setSelectedDrivers([]);
    } else {
      setSelectedDrivers(withoutOutcome.map((q) => q.id));
    }
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQid) {
      setError('Vui lòng chọn 1 biến mục tiêu kết quả (Outcome Y) để phân tích động lực.');
      return;
    }
    if (selectedDrivers.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 biến thuộc tính động lực (Predictors X).');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runShapleyDrivers(surveyId, {
        driver_question_ids: selectedDrivers,
        outcome_question_id: outcomeQid,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng phân rã Shapley với dữ liệu hiện tại.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích Shapley KDA.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              Cooperative Game Theory
            </span>
            <span className="text-xs text-slate-400 font-mono">Lipovetsky & Conklin 2001; Lundberg & Lee 2017</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Phân Tích Động Lực Trọng Yếu &amp; Hồi Quy Shapley (Key Driver Analysis - KDA)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Phân rã đóng góp thực chất vào $R^2$ qua lý thuyết trò chơi liên minh, triệt tiêu đa cộng tuyến và thiết lập ma trận ưu tiên hành động (IPA Matrix).
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={handleRunAnalysis}
          disabled={loading || selectedDrivers.length < 2 || !outcomeQid}
          className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-lg text-sm transition-all shadow-lg shadow-cyan-900/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang Phân Rã 2^P Liên Minh...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Phân Tích Động Lực Shapley</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-6 p-4 bg-slate-950/60 rounded-lg border border-slate-800/80">
        {/* Outcome Selector */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              1. Biến Kết Quả Trọng Tâm (Outcome Y)
            </label>
            <select
              value={outcomeQid}
              onChange={(e) => {
                const newOutcome = e.target.value;
                setOutcomeQid(newOutcome);
                setSelectedDrivers((prev) => prev.filter((id) => id !== newOutcome));
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">-- Chọn biến kết quả (CSAT/NPS/Loyalty) --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Phạm Vi Dữ Liệu
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setScope('all')}
                className={`flex-1 py-1.5 px-3 rounded text-xs font-medium border transition-all ${
                  scope === 'all'
                    ? 'bg-cyan-600 text-white border-cyan-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Tất cả mẫu
              </button>
              <button
                onClick={() => setScope('verified_clean')}
                className={`flex-1 py-1.5 px-3 rounded text-xs font-medium border transition-all ${
                  scope === 'verified_clean'
                    ? 'bg-cyan-600 text-white border-cyan-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Mẫu sạch đã xác thực
              </button>
            </div>
          </div>
        </div>

        {/* Drivers Multi-Selection */}
        <div className="md:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              2. Chọn Các Thuộc Tính Động Lực (Drivers X, P &ge; 2)
            </label>
            <button
              onClick={selectAllEligible}
              className="text-xs text-cyan-400 hover:text-cyan-300 underline font-medium"
            >
              {selectedDrivers.length === eligibleQuestions.filter((q) => q.id !== outcomeQid).length
                ? 'Bỏ chọn tất cả'
                : 'Chọn tất cả'}
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1">
            {eligibleQuestions
              .filter((q) => q.id !== outcomeQid)
              .map((q) => {
                const isSelected = selectedDrivers.includes(q.id);
                return (
                  <div
                    key={q.id}
                    onClick={() => toggleDriver(q.id)}
                    className={`p-2.5 rounded-md border text-xs cursor-pointer transition-all flex items-center gap-2 ${
                      isSelected
                        ? 'bg-cyan-950/50 border-cyan-500/60 text-cyan-200'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="rounded border-slate-700 text-cyan-500 focus:ring-0 focus:ring-offset-0 bg-slate-800 cursor-pointer"
                    />
                    <span className="truncate">{q.title}</span>
                  </div>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 mb-6 rounded-lg bg-red-950/40 border border-red-500/50 text-red-200 text-sm flex items-center gap-3">
          <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && result.diagnostics && (
        <div className="space-y-6">
          {/* Key Metrics Dashboard */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Cỡ Mẫu (N)</div>
              <div className="text-lg font-bold text-white mt-0.5">{result.diagnostics.sample_size}</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Số Động Lực (P)</div>
              <div className="text-lg font-bold text-cyan-400 mt-0.5">{result.diagnostics.n_drivers} Thuộc Tính</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Hệ Số R² Tổng Thể</div>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">
                {(result.diagnostics.full_model_r2 * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Tổng Đóng Góp ΔR²</div>
              <div className="text-lg font-bold text-slate-200 mt-0.5">
                {result.diagnostics.sum_shapley_contributions.toFixed(3)}
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">VIF Lớn Nhất</div>
              <div className={`text-lg font-bold mt-0.5 ${result.diagnostics.has_multicollinearity ? 'text-amber-400' : 'text-slate-200'}`}>
                {result.diagnostics.max_vif.toFixed(1)}
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Đa Cộng Tuyến</div>
              <div className="text-xs font-semibold text-slate-200 mt-1">
                {result.diagnostics.has_multicollinearity ? '⚠️ Đã triệt tiêu (VIF>5)' : '✅ Thấp (VIF≤5)'}
              </div>
            </div>
          </div>

          {/* SVG Dual-Panel: Waterfall + IPA Matrix */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Biểu Đồ Trọng Số Shapley &amp; Ma Trận Quyết Định Hành Động (IPA Matrix)
              </h4>
              <div
                className="w-full flex justify-center overflow-x-auto"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Drivers Breakdown Table */}
          {result.drivers && result.drivers.length > 0 && (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 overflow-x-auto">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Bảng Phân Hạng Động Lực Trọng Yếu &amp; Khuyến Nghị Hành Động
              </h4>
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase font-mono">
                  <tr>
                    <th className="py-2.5 px-3">Thứ Hạng</th>
                    <th className="py-2.5 px-3">Tên Thuộc Tính Động Lực</th>
                    <th className="py-2.5 px-3">Tầm Quan Trọng (W %)</th>
                    <th className="py-2.5 px-3">Đóng Góp ΔR²</th>
                    <th className="py-2.5 px-3">Điểm Đánh Giá TB</th>
                    <th className="py-2.5 px-3">Tương Quan Pearson</th>
                    <th className="py-2.5 px-3">VIF</th>
                    <th className="py-2.5 px-3">Phân Vùng Chiến Lược (IPA)</th>
                    <th className="py-2.5 px-3">Mức Độ Cấp Bách</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.drivers.map((d, idx) => (
                    <tr key={d.driver_id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">#{idx + 1}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{d.driver_name}</td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-cyan-300">{d.importance_share_pct}%</span>
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-cyan-400 rounded-full"
                              style={{ width: `${Math.min(100, d.importance_share_pct)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 font-mono">{d.shapley_r2_contribution.toFixed(4)}</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-200">{d.performance_mean.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-mono">{d.bivariate_correlation >= 0 ? `+${d.bivariate_correlation.toFixed(2)}` : d.bivariate_correlation.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{d.vif.toFixed(1)}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            d.strategic_quadrant === 'Q1_CONCENTRATE_HERE'
                              ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                              : d.strategic_quadrant === 'Q2_KEEP_UP'
                              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                              : d.strategic_quadrant === 'Q4_OVERKILL'
                              ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}
                        >
                          {d.strategic_label}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        {d.action_urgency === 'High' ? (
                          <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-bold">
                            Khẩn cấp
                          </span>
                        ) : d.action_urgency === 'Medium' ? (
                          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] font-medium">
                            Trung bình
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                            Thấp
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Academic APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-950/90 rounded-lg border border-slate-800 text-slate-300 text-xs leading-relaxed space-y-2">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold mb-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span>Báo Cáo Học Thuật Chuẩn APA 7th Edition (Key Driver Analysis)</span>
              </div>
              <p className="whitespace-pre-line">{result.apa_narrative}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
