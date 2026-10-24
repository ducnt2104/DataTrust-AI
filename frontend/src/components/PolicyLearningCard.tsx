import React, { useState } from 'react';
import { api } from '../api/client';
import { PolicyLearningResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const PolicyLearningCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [primaryFeatureIdx, setPrimaryFeatureIdx] = useState<number>(0);
  const [nBootstraps, setNBootstraps] = useState<number>(200);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<PolicyLearningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'regimes' | 'allocations'>('regimes');

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
    if (!outcomeQid || !treatmentQid) {
      setError('Vui lòng chọn biến kết quả (Y) và biến can thiệp (W).');
      return;
    }
    if (outcomeQid === treatmentQid) {
      setError('Biến kết quả và biến can thiệp không được trùng nhau.');
      return;
    }
    if (selectedCovariates.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến đặc tính (Covariate) để phân tầng chính sách.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.runPolicyLearning(surveyId, {
        outcome_question_id: outcomeQid,
        treatment_question_id: treatmentQid,
        covariate_question_ids: selectedCovariates,
        primary_feature_idx: primaryFeatureIdx,
        n_bootstraps: nBootstraps,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_VARIATION') {
        setError(res.message || 'Không đủ điều kiện dữ liệu cho Học Chính sách Kép Vững.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Doubly Robust Policy Learning.');
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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              Econometrics v3.19
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-100 text-violet-800 border border-violet-200">
              Athey & Wager (2021) Econometrica
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
              Doubly Robust Policy Learning
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Học Chính sách Tối ưu Kép Vững (Doubly Robust Policy Learning)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Xác định quy tắc phân bổ can thiệp tối ưu hóa phúc lợi dân số dựa trên điểm AIPW (Doubly Robust Score), so sánh với các chế độ chính sách đại trà và hiện trạng.
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
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-white p-2 border"
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
            Chỉ báo Can thiệp Treatment (W) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-white p-2 border"
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
          >
            <option value="">-- Chọn biến can thiệp W --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Số mẫu tái chọn Bootstrap
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-white p-2 border"
            value={nBootstraps}
            onChange={(e) => setNBootstraps(parseInt(e.target.value, 10))}
          >
            <option value="100">100 mẫu Bootstrap (Nhanh)</option>
            <option value="200">200 mẫu Bootstrap (Khuyến nghị)</option>
            <option value="300">300 mẫu Bootstrap (Chuẩn mực)</option>
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Các biến đặc tính phân tầng chính sách (Covariates X) *
          </label>
          <div className="max-h-32 overflow-y-auto border border-slate-300 rounded bg-white p-2 space-y-1">
            {numericQuestions
              .filter((q) => q.id !== outcomeQid && q.id !== treatmentQid)
              .map((q, idx) => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-700 hover:bg-slate-50 p-1 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCovariates.includes(q.id)}
                    onChange={() => toggleCovariate(q.id)}
                    className="rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>{q.title || `Câu hỏi ${idx + 1}`}</span>
                </label>
              ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi làm sạch mẫu
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-white p-2 border"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
          >
            <option value="all">Toàn bộ mẫu khảo sát (All)</option>
            <option value="verified_clean">Chỉ mẫu kiểm định đạt chuẩn (Verified Clean)</option>
          </select>
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
              : 'bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500'
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
              Đang ước lượng điểm AIPW & học chính sách tối ưu...
            </>
          ) : (
            'Tối ưu Hóa Phân bổ Chính sách (Policy Learning)'
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
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
                Phúc lợi Tối ưu V(π*)
              </span>
              <div className="text-2xl font-black text-emerald-900 mt-1">
                {diag.optimal_welfare_value.toFixed(4)}
              </div>
              <div className="text-xs text-emerald-700 mt-1">
                Khuyến nghị: {diag.pct_recommended_treatment.toFixed(1)}% mẫu ({diag.n_recommended_treatment} đối tượng)
              </div>
              <div className="mt-2">
                <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Phân bổ cá thể hóa tối ưu
                </span>
              </div>
            </div>

            <div className="bg-violet-50 border border-violet-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-violet-700 uppercase tracking-wider">
                Thặng dư Phúc lợi Thuần (Gain)
              </span>
              <div className="text-2xl font-black text-violet-900 mt-1">
                +{diag.net_welfare_gain.toFixed(4)}
              </div>
              <div className="text-xs text-violet-600 mt-1">
                SE: {diag.se_gain.toFixed(4)} • p = {diag.p_value_gain < 0.001 ? '< 0.001' : diag.p_value_gain.toFixed(4)}
              </div>
              <div className="mt-2">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                    diag.is_significant_gain
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                  }`}
                >
                  {diag.is_significant_gain ? 'Thặng dư có ý nghĩa (p < 0.05)' : 'Chưa có ý nghĩa thống kê'}
                </span>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">
                Can thiệp Đại trà (Treat All)
              </span>
              <div className="text-2xl font-black text-blue-900 mt-1">
                {diag.treat_all_welfare_value.toFixed(4)}
              </div>
              <div className="text-xs text-blue-600 mt-1">
                Áp dụng 100% mẫu khảo sát
              </div>
              <div className="text-xs text-slate-500 mt-2">
                Chênh lệch: {(diag.optimal_welfare_value - diag.treat_all_welfare_value).toFixed(3)}
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Không Can thiệp / Hiện trạng
              </span>
              <div className="text-lg font-bold text-slate-800 mt-1">
                Treat None: {diag.treat_none_welfare_value.toFixed(4)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Hiện trạng W: {diag.observed_welfare_value.toFixed(4)}
              </div>
              <div className="text-xs text-slate-600 mt-2">
                Cỡ mẫu: N = {diag.sample_size}
              </div>
            </div>
          </div>

          {/* SVG Visualizations */}
          {result.svg_visualization && (
            <div className="bg-slate-900 p-4 rounded-xl shadow-inner border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider">
                  Trực quan hóa Điểm AIPW & So sánh Chế độ Chính sách (Dual-Panel Policy Learning)
                </span>
                <span className="text-xs text-slate-400">Athey & Wager (2021) Econometrica</span>
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
                onClick={() => setActiveTab('regimes')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'regimes'
                    ? 'border-emerald-600 text-emerald-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                So sánh Các Chế độ Chính sách (Policy Regimes)
              </button>
              <button
                onClick={() => setActiveTab('allocations')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'allocations'
                    ? 'border-emerald-600 text-emerald-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Phân bổ Khuyến nghị Từng Cá thể (Sample Allocations)
              </button>
            </nav>
          </div>

          {/* Tab 1: Regimes Comparison */}
          {activeTab === 'regimes' && result.regimes_comparison && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Chế độ Chính sách</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-emerald-700 uppercase">Phúc lợi Kỳ vọng V(π)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Tỷ lệ Can thiệp (%)</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Đặc điểm Phân bổ</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.regimes_comparison.map((r, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">{r.regime_name}</td>
                      <td className="px-4 py-2 text-right font-bold text-emerald-800">{r.expected_welfare.toFixed(4)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-slate-700">{r.treated_pct.toFixed(1)}%</td>
                      <td className="px-4 py-2 text-xs text-slate-600">{r.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Sample Allocations */}
          {activeTab === 'allocations' && result.sample_allocations && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Khách thể</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Đặc tính Phân tầng</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Can thiệp Thực tế</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-violet-700 uppercase">Điểm AIPW (Γ_i)</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-emerald-700 uppercase">Chính sách Tối ưu π*</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Trạng thái Khuyến nghị</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.sample_allocations.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">{item.respondent_id}</td>
                      <td className="px-4 py-2 text-right text-slate-700">{item.primary_feature_val.toFixed(2)}</td>
                      <td className="px-4 py-2 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs ${item.observed_treatment === 1 ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-600'}`}>
                          {item.observed_treatment === 1 ? 'Đã can thiệp' : 'Đối chứng'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right font-mono font-medium text-violet-800">
                        {item.aipw_score > 0 ? `+${item.aipw_score.toFixed(3)}` : item.aipw_score.toFixed(3)}
                      </td>
                      <td className="px-4 py-2 text-center font-bold text-emerald-800">
                        π* = {item.recommended_policy}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            item.recommended_policy === 1
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
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
                  className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
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
