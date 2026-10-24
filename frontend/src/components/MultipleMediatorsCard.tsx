import React, { useState } from 'react';
import { api } from '../api/client';
import { MultipleMediatorsResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const MultipleMediatorsCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [mediator1Qid, setMediator1Qid] = useState<string>('');
  const [mediator2Qid, setMediator2Qid] = useState<string>('');
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [nBootstraps, setNBootstraps] = useState<number>(300);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MultipleMediatorsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'effects' | 'paths'>('effects');

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'slider' ||
      q.question_type === 'short_text'
  );

  const handleRun = async () => {
    if (!treatmentQid || !mediator1Qid || !mediator2Qid || !outcomeQid) {
      setError('Vui lòng chọn đầy đủ 4 biến: Can thiệp (X), Trung gian 1 (M1), Trung gian 2 (M2), và Kết quả (Y).');
      return;
    }
    const selected = [treatmentQid, mediator1Qid, mediator2Qid, outcomeQid];
    if (new Set(selected).size !== 4) {
      setError('Các biến chọn phải là các câu hỏi khác nhau.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.runMultipleMediators(surveyId, {
        treatment_question_id: treatmentQid,
        mediator1_question_id: mediator1Qid,
        mediator2_question_id: mediator2Qid,
        outcome_question_id: outcomeQid,
        n_bootstraps: nBootstraps,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'ZERO_VARIANCE') {
        setError(res.message || 'Không đủ điều kiện dữ liệu cho Phân tích Trung gian Đa biến Tuần tự.');
      }
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Multiple Sequential Mediators.');
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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-pink-100 text-pink-800 border border-pink-200">
              Econometrics v3.18
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
              VanderWeele (2014) AJE
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">
              Sequential Path-Specific Mediation
            </span>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">
              Phân tích Trung gian Causal Đa biến Tuần tự (Multiple Sequential Mediators)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Bóc tách tổng tác động nhân quả thành tác động trực tiếp thuần (PDE) và các tác động gián tiếp đặc thù qua từng kênh trung gian M1, M2 và chuỗi tuần tự M1 → M2.
          </p>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5 p-4 bg-slate-50 rounded-lg border border-slate-200">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến can thiệp Treatment (X) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-pink-500 focus:ring-pink-500 bg-white p-2 border"
            value={treatmentQid}
            onChange={(e) => setTreatmentQid(e.target.value)}
          >
            <option value="">-- Chọn biến can thiệp X --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến trung gian 1 Mediator 1 (M1) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-pink-500 focus:ring-pink-500 bg-white p-2 border"
            value={mediator1Qid}
            onChange={(e) => setMediator1Qid(e.target.value)}
          >
            <option value="">-- Chọn biến trung gian M1 --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến trung gian 2 Mediator 2 (M2) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-pink-500 focus:ring-pink-500 bg-white p-2 border"
            value={mediator2Qid}
            onChange={(e) => setMediator2Qid(e.target.value)}
          >
            <option value="">-- Chọn biến trung gian M2 --</option>
            {numericQuestions.map((q, idx) => (
              <option key={q.id} value={q.id}>
                {q.title || `Câu hỏi ${idx + 1}`} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Biến kết quả Outcome (Y) *
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-pink-500 focus:ring-pink-500 bg-white p-2 border"
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
            Số mẫu tái chọn Bootstrap
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-pink-500 focus:ring-pink-500 bg-white p-2 border"
            value={nBootstraps}
            onChange={(e) => setNBootstraps(parseInt(e.target.value, 10))}
          >
            <option value="150">150 mẫu Bootstrap (Nhanh)</option>
            <option value="300">300 mẫu Bootstrap (Khuyến nghị)</option>
            <option value="500">500 mẫu Bootstrap (Độ chính xác cao)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Phạm vi làm sạch mẫu
          </label>
          <select
            className="w-full text-sm border-slate-300 rounded-md shadow-sm focus:border-pink-500 focus:ring-pink-500 bg-white p-2 border"
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
              : 'bg-pink-600 hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500'
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
              Đang ước lượng Bootstrap & bóc tách tác động...
            </>
          ) : (
            'Phân tích Trung gian Đa biến Tuần tự'
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
            <div className="bg-sky-50 border border-sky-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-sky-700 uppercase tracking-wider">
                Tổng Tác động (Total Effect TE)
              </span>
              <div className="text-2xl font-black text-sky-900 mt-1">
                {diag.total_effect.toFixed(4)}
              </div>
              <div className="text-xs text-sky-600 mt-1">
                Cỡ mẫu N = {diag.sample_size} | {diag.n_bootstraps} Bootstraps
              </div>
              <div className="mt-2">
                <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-sky-100 text-sky-800 border border-sky-300">
                  Tổng hợp trực tiếp + gián tiếp
                </span>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Tác động Trực tiếp Thuần (PDE)
              </span>
              <div className="text-2xl font-black text-slate-800 mt-1">
                {diag.direct_effect.toFixed(4)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Kênh trực tiếp X → Y (không qua M)
              </div>
              <div className="text-xs text-slate-600 mt-2">
                Tỷ trọng: {(100.0 - diag.proportion_mediated_pct).toFixed(1)}% tổng tác động
              </div>
            </div>

            <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-pink-700 uppercase tracking-wider">
                Tổng Gián tiếp (TIE)
              </span>
              <div className="text-2xl font-black text-pink-900 mt-1">
                {diag.total_indirect_effect.toFixed(4)}
              </div>
              <div className="text-xs text-pink-600 mt-1">
                Tỷ lệ trung gian: {diag.proportion_mediated_pct.toFixed(1)}%
              </div>
              <div className="mt-2">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                    diag.is_full_mediation
                      ? 'bg-purple-100 text-purple-800 border border-purple-300'
                      : (diag.is_partial_mediation ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-slate-100 text-slate-700')
                  }`}
                >
                  {diag.is_full_mediation ? 'Trung gian Toàn phần' : (diag.is_partial_mediation ? 'Trung gian Một phần' : 'Không có trung gian')}
                </span>
              </div>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-purple-700 uppercase tracking-wider">
                Kênh Tuần tự (X → M1 → M2 → Y)
              </span>
              <div className="text-2xl font-black text-purple-900 mt-1">
                {diag.nie_seq.toFixed(4)}
              </div>
              <div className="text-xs text-purple-600 mt-1">
                Tỷ trọng chuỗi: {diag.proportion_seq_pct.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-600 mt-2">
                M1 độc lập: {diag.nie_m1.toFixed(3)} | M2: {diag.nie_m2.toFixed(3)}
              </div>
            </div>
          </div>

          {/* SVG Visualizations */}
          {result.svg_visualization && (
            <div className="bg-slate-900 p-4 rounded-xl shadow-inner border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-pink-300 uppercase tracking-wider">
                  Sơ đồ Đường dẫn Cấu trúc & Phân rã Tác động Causal Mediation (Dual-Panel DAG & Forest Plot)
                </span>
                <span className="text-xs text-slate-400">VanderWeele (2014); Steen et al. (2012)</span>
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
                onClick={() => setActiveTab('effects')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'effects'
                    ? 'border-pink-600 text-pink-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Bảng Phân rã Tác động Causal (Effects Decomposition)
              </button>
              <button
                onClick={() => setActiveTab('paths')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'paths'
                    ? 'border-pink-600 text-pink-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Hệ số Đường dẫn Cấu trúc (Path Coefficients)
              </button>
            </nav>
          </div>

          {/* Tab 1: Effects Decomposition */}
          {activeTab === 'effects' && result.effects_summary && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Loại Tác động</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-pink-700 uppercase">Ước lượng Điểm</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Sai số Chuẩn (SE)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Khoảng Tin cậy 95% (CI)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-purple-700 uppercase">Tỷ lệ (%)</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-slate-600 uppercase">Ý nghĩa Thống kê</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.effects_summary.map((eff, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">{eff.effect_name}</td>
                      <td className="px-4 py-2 text-right font-bold text-pink-800">{eff.stats.estimate.toFixed(4)}</td>
                      <td className="px-4 py-2 text-right text-slate-600">{eff.stats.se.toFixed(4)}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs text-slate-700">
                        [{eff.stats.ci_lower_95.toFixed(3)}, {eff.stats.ci_upper_95.toFixed(3)}]
                      </td>
                      <td className="px-4 py-2 text-right font-semibold text-purple-800">{eff.proportion_pct.toFixed(1)}%</td>
                      <td className="px-4 py-2 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            eff.stats.is_significant
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {eff.stats.is_significant ? 'Ý nghĩa (p < 0.05)' : 'Không có ý nghĩa'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 2: Path Coefficients */}
          {activeTab === 'paths' && result.path_coefficients && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase">Đường dẫn Mô hình</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-700 uppercase">Hệ số Đường dẫn (β)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">Sai số Chuẩn (SE)</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-slate-600 uppercase">p-value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.path_coefficients.map((p, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">{p.path}</td>
                      <td className="px-4 py-2 text-right font-bold text-pink-800">{p.estimate.toFixed(4)}</td>
                      <td className="px-4 py-2 text-right text-slate-600">{p.se.toFixed(4)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-slate-700">
                        {p.p_value < 0.001 ? '< 0.001' : p.p_value.toFixed(4)}
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
                  className="text-xs text-pink-600 hover:text-pink-800 font-medium"
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
