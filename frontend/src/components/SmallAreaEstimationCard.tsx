import React, { useState } from 'react';
import { api } from '../api/client';
import { SmallAreaEstimationResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface SmallAreaEstimationCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const SmallAreaEstimationCard: React.FC<SmallAreaEstimationCardProps> = ({
  surveyId,
  questions
}) => {
  const [areaQId, setAreaQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [auxiliaryQIds, setAuxiliaryQIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SmallAreaEstimationResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleAuxiliaryQuestion = (qId: string) => {
    setAuxiliaryQIds(prev =>
      prev.includes(qId) ? prev.filter(id => id !== qId) : [...prev, qId]
    );
  };

  const handleRunAnalysis = async () => {
    if (!areaQId) {
      setError('Vui lòng chọn câu hỏi định danh tiểu vùng / khu vực / chi nhánh (Area Identifier).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả đầu ra (Outcome Variable Y).');
      return;
    }
    if (areaQId === outcomeQId) {
      setError('Biến tiểu vùng và biến kết quả không được trùng nhau.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runSmallAreaEstimation(surveyId, {
        area_question_id: areaQId,
        outcome_question_id: outcomeQId,
        auxiliary_question_ids: auxiliaryQIds.length > 0 ? auxiliaryQIds : undefined,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || `Lỗi ước lượng Tiểu vùng Fay-Herriot: ${data.status}`);
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng mô hình Small Area Estimation.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Survey Methodology
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Empirical Bayes EBLUP
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Ước lượng Tiểu vùng Fay-Herriot & Thu hẹp Sai số (Small Area Estimation - SAE)
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Khắc phục hiện tượng phương sai lấy mẫu lớn do cỡ mẫu nhỏ ở từng khu vực/phòng ban ($n_m &lt; 30$) theo phương pháp chuẩn mực của{' '}
            <strong className="text-slate-200">Fay & Herriot (1979)</strong>,{' '}
            <strong className="text-slate-200">Prasad & Rao (1990)</strong> và{' '}
            <strong className="text-slate-200">Rao & Molina (2015)</strong>. Tự động co rút (shrinkage) ước lượng trực tiếp về hồi quy tổng hợp và tính sai số chuẩn hiệu chỉnh bậc hai.
          </p>
        </div>
      </div>

      {/* Control Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
        {/* Area Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            1. Câu hỏi phân loại Tiểu vùng / Khu vực / Chi nhánh <span className="text-rose-400">*</span>
          </label>
          <select
            value={areaQId}
            onChange={(e) => setAreaQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi phân loại vùng / chi nhánh --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Question */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            2. Biến kết quả cần ước lượng (Outcome Variable Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến kết quả số --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Optional Auxiliary Covariates */}
      {numericQuestions.filter(q => q.id !== outcomeQId && q.id !== areaQId).length > 0 && (
        <div className="mb-6 bg-slate-800/30 border border-slate-700/50 rounded-lg p-3">
          <label className="block text-xs font-medium text-slate-300 mb-2">
            3. Biến hỗ trợ cấp tiểu vùng (Auxiliary Predictors X - Tùy chọn để tăng độ chính xác hồi quy):
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {numericQuestions
              .filter(q => q.id !== outcomeQId && q.id !== areaQId)
              .map((q) => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer bg-slate-800/50 p-2 rounded border border-slate-700/60">
                  <input
                    type="checkbox"
                    checked={auxiliaryQIds.includes(q.id)}
                    onChange={() => toggleAuxiliaryQuestion(q.id)}
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
          </div>
        </div>
      )}

      {/* Scope & Action Button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-slate-800/40 border border-slate-700/60 rounded-lg mb-6">
        <div className="flex items-center gap-4 text-xs">
          <span className="text-slate-300 font-medium">Bộ lọc dữ liệu:</span>
          <label className="inline-flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="radio"
              name="sae-scope"
              checked={scope === 'all'}
              onChange={() => setScope('all')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            Toàn bộ phản hồi
          </label>
          <label className="inline-flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="radio"
              name="sae-scope"
              checked={scope === 'verified_clean'}
              onChange={() => setScope('verified_clean')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            Chỉ phản hồi sạch (Verified Clean $\ge$ 0.70)
          </label>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg shadow-lg hover:shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Đang tính toán Fay-Herriot EBLUP & Prasad-Rao...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <span>Ước lượng Tiểu vùng Fay-Herriot</span>
            </>
          )}
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 mb-6 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-sm flex items-start gap-2">
          <svg className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>{error}</div>
        </div>
      )}

      {/* Results Section */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6">
          {/* Key Metrics Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Số Tiểu vùng (M)</span>
              <p className="text-2xl font-bold text-white mt-1">{result.area_count}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Tiểu vùng hợp lệ ($n_m \ge 2$)</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Phương sai Giữa các Vùng ($\sigma_v^2$)</span>
              <p className="text-2xl font-bold text-sky-400 mt-1">{result.between_area_variance_sigma_v2}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">REML model variance</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Trọng số Co rút Trung bình (Gamma-bar)</span>
              <p className="text-2xl font-bold text-indigo-400 mt-1">{result.mean_shrinkage_weight_gamma}</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">Tỷ lệ giữ lại ước lượng trực tiếp</span>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 rounded-lg p-3">
              <span className="text-xs text-slate-400">Mức tăng Hiệu quả Trung bình</span>
              <p className="text-2xl font-bold text-emerald-400 mt-1">+{result.mean_efficiency_gain_pct}%</p>
              <span className="text-[10px] text-slate-400 block mt-0.5">SE reduction (Prasad-Rao)</span>
            </div>
          </div>

          {/* SVG Shrinkage Forest Plot */}
          {result.svg_chart && (
            <div className="bg-slate-800/50 border border-slate-700/80 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">
                Biểu đồ Co rút Thu hẹp Sai số & Thu hẹp Khoảng tin cậy (Shrinkage Forest Plot)
              </h3>
              <div
                className="overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Main Area Estimates Table */}
          <div className="bg-slate-800/40 border border-slate-700/70 rounded-lg p-4">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Chi tiết Ước lượng Tiểu vùng EBLUP vs Ước lượng Trực tiếp
            </h4>
            <div className="overflow-x-auto max-h-80 overflow-y-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="text-[11px] text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700 sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Tiểu vùng</th>
                    <th className="py-2.5 px-3 text-right">Cỡ mẫu (nm)</th>
                    <th className="py-2.5 px-3 text-right">Trực tiếp (ym ± SE)</th>
                    <th className="py-2.5 px-3 text-right">Dự báo Hồi quy</th>
                    <th className="py-2.5 px-3 text-right">Trọng số Gamma_m</th>
                    <th className="py-2.5 px-3 text-right">EBLUP Shrunk (Theta-EB)</th>
                    <th className="py-2.5 px-3 text-right">95% CI EBLUP</th>
                    <th className="py-2.5 px-3 text-right">Hiệu quả tăng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.area_estimates && result.area_estimates.map((est, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="py-2.5 px-3 font-medium text-slate-200">{est.area_name}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-400">{est.sample_size}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-sky-300">
                        {est.direct_estimate} <span className="text-[10px] text-slate-400">±{est.direct_se}</span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-400">{est.synthetic_prediction}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-amber-300">{est.shrinkage_weight_gamma}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold text-emerald-400">
                        {est.eblup_estimate} <span className="text-[10px] text-emerald-300">±{est.eblup_se}</span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                        [{est.eblup_ci_lower}, {est.eblup_ci_upper}]
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold text-indigo-300">
                        +{est.efficiency_gain_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Regression Coefficients Table */}
          {result.regression_coefficients && result.regression_coefficients.length > 0 && (
            <div className="bg-slate-800/40 border border-slate-700/70 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Mô hình Hồi quy Tổng hợp Cấp Khu vực (GLS Linking Model: $x_m' \beta$)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="text-[11px] text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700">
                    <tr>
                      <th className="py-2 px-3">Thành phần</th>
                      <th className="py-2 px-3 text-right">Hệ số ($\beta$)</th>
                      <th className="py-2 px-3 text-right">Sai số chuẩn (SE)</th>
                      <th className="py-2 px-3 text-right">Giá trị $z$</th>
                      <th className="py-2 px-3 text-right">Mức ý nghĩa ($p$-value)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {result.regression_coefficients.map((rc, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 font-medium text-slate-200">{rc.term}</td>
                        <td className="py-2 px-3 text-right font-mono text-sky-300">{rc.coefficient}</td>
                        <td className="py-2 px-3 text-right font-mono text-slate-400">{rc.std_error}</td>
                        <td className="py-2 px-3 text-right font-mono">{rc.z_statistic}</td>
                        <td className={`py-2 px-3 text-right font-mono font-semibold ${rc.p_value < 0.05 ? 'text-emerald-400' : 'text-slate-400'}`}>
                          {rc.p_value}
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
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-lg p-5">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-700">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded border border-slate-600 transition-colors flex items-center gap-1.5"
                >
                  {copiedNarrative ? (
                    <>
                      <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-emerald-300">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>Sao chép APA</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed italic bg-slate-900/50 p-4 rounded border border-slate-800">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
