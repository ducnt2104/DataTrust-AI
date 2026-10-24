import React, { useState } from 'react';
import { api } from '../api/client';
import { RDDLocalRandomizationResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const RDDLocalRandomizationCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [runningQid, setRunningQid] = useState<string>('');
  const [cutoff, setCutoff] = useState<string>('0.0');
  const [windowHalfWidth, setWindowHalfWidth] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [nPermutations, setNPermutations] = useState<number>(300);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<RDDLocalRandomizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'balance' | 'bins'>('balance');

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'slider' ||
      q.question_type === 'short_text'
  );

  const toggleCovariate = (qid: string) => {
    if (selectedCovariates.includes(qid)) {
      setSelectedCovariates(selectedCovariates.filter((id) => id !== qid));
    } else {
      setSelectedCovariates([...selectedCovariates, qid]);
    }
  };

  const handleRun = async () => {
    if (!outcomeQid || !runningQid) {
      setError('Vui lòng chọn biến kết quả (Y) và biến chạy phân tầng (X).');
      return;
    }
    if (outcomeQid === runningQid) {
      setError('Biến kết quả và biến chạy không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.runRDDLocalRandomization(surveyId, {
        outcome_question_id: outcomeQid,
        running_question_id: runningQid,
        cutoff: parseFloat(cutoff) || 0.0,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        window_half_width: windowHalfWidth ? parseFloat(windowHalfWidth) : null,
        n_permutations: nPermutations,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_VARIATION') {
        setError(res.message || 'Không đủ điều kiện dữ liệu cho RDD Ngẫu nhiên hóa Cục bộ.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API RDD Local Randomization.');
    } finally {
      setLoading(false);
    }
  };

  const diag = result?.diagnostics;

  return (
    <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 mb-8 transition-all hover:shadow-lg">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
              Econometrics v3.20
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
              Cattaneo et al. (2015) JCA
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-100 text-cyan-800 border border-cyan-200">
              Discrete RDD Local Randomization
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Hồi quy Gián đoạn với Ngẫu nhiên hóa Cục bộ (Local Randomization RDD)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Khung phân tích suy diễn nhân quả chuyên biệt cho biến chạy rời rạc hoặc phân cụm thưa, sử dụng kiểm định hoán vị Fisher hữu hạn mẫu chính xác trong cửa sổ W*.
          </p>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5 p-4 bg-slate-50 rounded-lg border border-slate-200">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến kết quả Outcome (Y) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white p-2 border"
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến chạy phân tầng Running (X) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white p-2 border"
            value={runningQid}
            onChange={(e) => setRunningQid(e.target.value)}
          >
            <option value="">-- Chọn biến chạy X --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Ngưỡng cắt chính sách Cutoff (c)
          </label>
          <input
            type="number"
            step="any"
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white p-2 border"
            value={cutoff}
            onChange={(e) => setCutoff(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Bán kính Cửa sổ w (Tùy chọn)
          </label>
          <input
            type="number"
            step="any"
            min="0"
            placeholder="Tự động cân bằng đặc tính"
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white p-2 border"
            value={windowHalfWidth}
            onChange={(e) => setWindowHalfWidth(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Số lần hoán vị Permutations
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white p-2 border"
            value={nPermutations}
            onChange={(e) => setNPermutations(parseInt(e.target.value, 10))}
          >
            <option value="150">150 hoán vị (Nhanh)</option>
            <option value="300">300 hoán vị (Khuyến nghị)</option>
            <option value="500">500 hoán vị (Độ chính xác cao)</option>
            <option value="1000">1000 hoán vị (Chuẩn mực)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi làm sạch mẫu
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white p-2 border"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
          >
            <option value="all">Toàn bộ mẫu khảo sát (All)</option>
            <option value="verified_clean">Chỉ mẫu kiểm định đạt chuẩn (Verified Clean)</option>
          </select>
        </div>

        <div className="md:col-span-3">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Các biến đặc tính kiểm định cân bằng (Covariates Balance Testing)
          </label>
          <div className="max-h-24 overflow-y-auto border border-slate-300 rounded bg-white p-2 flex flex-wrap gap-2">
            {numericQuestions
              .filter((q) => q.id !== outcomeQid && q.id !== runningQid)
              .map((q, idx) => (
                <label key={q.id} className="inline-flex items-center gap-1.5 text-xs text-slate-700 bg-slate-50 hover:bg-slate-100 px-2 py-1 rounded border cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCovariates.includes(q.id)}
                    onChange={() => toggleCovariate(q.id)}
                    className="rounded text-amber-600 focus:ring-amber-500"
                  />
                  <span>{q.title || `Câu hỏi ${idx + 1}`}</span>
                </label>
              ))}
          </div>
        </div>
      </div>

      {/* Action Button */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={handleRun}
          disabled={loading}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
            loading
              ? 'bg-slate-400 cursor-not-allowed'
              : 'bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500'
          }`}
        >
          {loading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Đang xác định cửa sổ W* & kiểm định hoán vị...
            </>
          ) : (
            'Ước lượng RDD Ngẫu nhiên hóa Cục bộ'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm rounded">
          <p className="font-semibold">Thông báo:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Results View */}
      {result && diag && (
        <div className="mt-6 space-y-6">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
                Tác động Gián đoạn Trung bình (τ̂_LR)
              </span>
              <div className="text-2xl font-black text-amber-900 mt-1">
                {diag.tau_diff_means.toFixed(4)}
              </div>
              <div className="text-xs text-amber-600 mt-1">
                SE hoán vị: {diag.se_permutation.toFixed(4)} • p = {diag.permutation_p_value < 0.001 ? '< 0.001' : diag.permutation_p_value.toFixed(4)}
              </div>
              <div className="mt-2">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                    diag.is_statistically_significant
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-slate-100 text-slate-700 border border-slate-300'
                  }`}
                >
                  {diag.is_statistically_significant ? 'Ý nghĩa hoán vị (p < 0.05)' : 'Không có ý nghĩa'}
                </span>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Chênh lệch Trung vị (Medians)
              </span>
              <div className="text-2xl font-black text-slate-800 mt-1">
                {diag.tau_diff_medians.toFixed(4)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                95% CI: [{diag.ci_lower_95.toFixed(3)}, {diag.ci_upper_95.toFixed(3)}]
              </div>
              <div className="text-xs text-slate-600 mt-2">
                Kháng ngoại lai mạnh mẽ
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">
                Cửa sổ Ngẫu nhiên hóa W*
              </span>
              <div className="text-lg font-bold text-blue-900 mt-1">
                [{diag.window_lower.toFixed(2)}, {diag.window_upper.toFixed(2)}]
              </div>
              <div className="text-xs text-blue-700 mt-1">
                Bán kính w = {diag.window_half_width.toFixed(2)} | c = {diag.cutoff_c}
              </div>
              <div className="text-xs text-slate-600 mt-2">
                {diag.n_in_window} đối tượng ({diag.n_window_treated} can thiệp / {diag.n_window_control} đối chứng)
              </div>
            </div>

            <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-cyan-700 uppercase tracking-wider">
                So sánh RDD Tuyến tính Cục bộ
              </span>
              <div className="text-lg font-bold text-cyan-900 mt-1">
                {diag.tau_continuity_benchmark.toFixed(4)}
              </div>
              <div className="text-xs text-cyan-700 mt-1">
                Bias Gap: {diag.methodology_bias_gap > 0 ? `+${diag.methodology_bias_gap.toFixed(4)}` : diag.methodology_bias_gap.toFixed(4)}
              </div>
              <div className="text-xs text-slate-500 mt-2">
                Tổng mẫu khảo sát: N = {diag.sample_size}
              </div>
            </div>
          </div>

          {/* SVG Visualizations */}
          {result.svg_visualization && (
            <div className="bg-slate-900 p-4 rounded-xl shadow-inner border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-amber-300 uppercase tracking-wider">
                  Trực quan hóa Phân cụm Rời rạc & Phân phối Hoán vị Fisher (Dual-Panel Discrete RDD)
                </span>
                <span className="text-xs text-slate-400">Cattaneo, Frandsen, & Titiunik (2015)</span>
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Tab Navigation */}
          <div className="border-b border-slate-200">
            <nav className="-mb-px flex space-x-6">
              <button
                onClick={() => setActiveTab('balance')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'balance'
                    ? 'border-amber-600 text-amber-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Kiểm định Cân bằng Đặc tính trong Cửa sổ (Covariate Balance)
              </button>
              <button
                onClick={() => setActiveTab('bins')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'bins'
                    ? 'border-amber-600 text-amber-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Các Điểm Khối lượng Rời rạc (Discrete Mass Points of X)
              </button>
            </nav>
          </div>

          {/* Tab 1: Balance Table */}
          {activeTab === 'balance' && (
            <div className="overflow-x-auto">
              {result.balance_table && result.balance_table.length > 0 ? (
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Đặc tính Kiểm định</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-amber-700 uppercase">Trung bình Can thiệp</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Trung bình Đối chứng</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Chênh lệch</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">p-value</th>
                      <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Trạng thái Cân bằng</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.balance_table.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-4 py-2 font-medium text-slate-800">{row.covariate_name}</td>
                        <td className="px-4 py-2 text-right font-semibold text-amber-800">{row.mean_treated.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right text-slate-700">{row.mean_control.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right font-mono text-xs text-slate-700">{row.difference.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right font-semibold text-slate-700">
                          {row.p_value < 0.001 ? '< 0.001' : row.p_value.toFixed(4)}
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              row.is_balanced
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : 'bg-red-100 text-red-800 border border-red-300'
                            }`}
                          >
                            {row.is_balanced ? 'Cân bằng (p ≥ 0.10)' : 'Lệch (p < 0.10)'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-xs text-slate-500 italic p-3">
                  Chưa chọn biến đặc tính (covariates) nào để kiểm định cân bằng ngẫu nhiên hóa.
                </p>
              )}
            </div>
          )}

          {/* Tab 2: Discrete Bins */}
          {activeTab === 'bins' && result.discrete_bins && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Giá trị Điểm X</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Khoảng cách đến Ngưỡng (X - c)</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Trạng thái Can thiệp</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-blue-700 uppercase">Trong Cửa sổ W*</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Số quan sát</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-amber-700 uppercase">Trung bình Kết quả Y</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.discrete_bins.map((bin, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">{bin.x_value.toFixed(2)}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs text-slate-700">
                        {bin.centered_x > 0 ? `+${bin.centered_x.toFixed(2)}` : bin.centered_x.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs ${bin.is_treated ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'}`}>
                          {bin.is_treated ? 'Can thiệp (X ≥ c)' : 'Đối chứng (X < c)'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${bin.is_in_window ? 'bg-blue-100 text-blue-800 border border-blue-200' : 'bg-slate-50 text-slate-400'}`}>
                          {bin.is_in_window ? 'Thuộc W*' : 'Ngoài cửa sổ'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right font-semibold text-slate-700">{bin.count}</td>
                      <td className="px-4 py-2 text-right font-bold text-amber-800">{bin.mean_y.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Báo cáo Thuyết minh Khoa học chuẩn APA 7th
                </span>
                <button
                  onClick={() => {
                    if (result.apa_narrative) {
                      navigator.clipboard.writeText(result.apa_narrative);
                    }
                  }}
                  className="text-xs text-amber-600 hover:text-amber-800 font-medium"
                >
                  Sao chép thuyết minh
                </button>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed italic bg-white p-3 rounded border border-slate-200">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
