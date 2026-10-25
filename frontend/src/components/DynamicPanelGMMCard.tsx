import React, { useState } from 'react';
import { api } from '../api/client';
import { DynamicPanelGMMResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const DynamicPanelGMMCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [unitIdQid, setUnitIdQid] = useState<string>('');
  const [timeQid, setTimeQid] = useState<string>('');
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [method, setMethod] = useState<'system' | 'difference'>('system');
  const [twoStep, setTwoStep] = useState<boolean>(true);
  const [windmeijerCorrection, setWindmeijerCorrection] = useState<boolean>(true);
  const [maxInstrumentLags, setMaxInstrumentLags] = useState<number>(3);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DynamicPanelGMMResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!unitIdQid || !timeQid || !outcomeQid) {
      setError('Vui lòng chọn đầy đủ Biến định danh đơn vị (Unit ID), Biến thời gian (Wave/Time) và Biến kết quả (Outcome).');
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const data = await api.runDynamicPanelGMM(surveyId, {
        unit_id_question_id: unitIdQid,
        time_question_id: timeQid,
        outcome_question_id: outcomeQid,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        method,
        two_step: twoStep,
        windmeijer_correction: windmeijerCorrection,
        max_instrument_lags: maxInstrumentLags,
        scope
      });

      if (data.status === 'INSUFFICIENT_SAMPLE') {
        setError(data.message || 'Mẫu không đủ điều kiện cho Dynamic Panel GMM (cần ít nhất 15 đối tượng với ≥ 3 đợt khảo sát).');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực hiện phân tích Dynamic Panel GMM.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-4 mb-6 border-b border-slate-100 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-800">
              Dynamic Panel System & Difference GMM
            </h2>
            <span className="bg-indigo-50 text-indigo-700 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-indigo-200">
              Arellano-Bond & Blundell-Bond
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Ước lượng độ trễ tự hồi quy và biến ngoại sinh trong dữ liệu bảng dọc (Longitudinal Panel), hiệu chỉnh thiên lệch Nickell (1981) và sai số hữu hạn Windmeijer (2005).
          </p>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến định danh đơn vị (Unit / Respondent ID) <span className="text-red-500">*</span>
          </label>
          <select
            value={unitIdQid}
            onChange={e => setUnitIdQid(e.target.value)}
            className="w-full text-sm border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn câu hỏi định danh --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến thời gian / Đợt khảo sát (Wave / Time) <span className="text-red-500">*</span>
          </label>
          <select
            value={timeQid}
            onChange={e => setTimeQid(e.target.value)}
            className="w-full text-sm border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn đợt khảo sát --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kết quả phụ thuộc Y (Outcome) <span className="text-red-500">*</span>
          </label>
          <select
            value={outcomeQid}
            onChange={e => setOutcomeQid(e.target.value)}
            className="w-full text-sm border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Covariates multi-select */}
      <div className="mb-6">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">
          Biến giải thích kiểm soát ngoại sinh X (Tùy chọn)
        </label>
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-2 bg-slate-50 border border-slate-200 rounded-lg">
          {questions
            .filter(q => q.id !== unitIdQid && q.id !== timeQid && q.id !== outcomeQid)
            .map(q => {
              const isChecked = selectedCovariates.includes(q.id);
              return (
                <button
                  type="button"
                  key={q.id}
                  onClick={() => toggleCovariate(q.id)}
                  className={`text-xs px-2.5 py-1.5 rounded-md border transition-all text-left ${
                    isChecked
                      ? 'bg-indigo-600 text-white border-indigo-600 font-medium'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {q.title}
                </button>
              );
            })}
        </div>
      </div>

      {/* Advanced Method & Correction Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg border border-slate-100 mb-6 text-sm">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Phương pháp ước lượng</label>
          <select
            value={method}
            onChange={e => setMethod(e.target.value as any)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          >
            <option value="system">System GMM (Blundell-Bond 1998)</option>
            <option value="difference">Difference GMM (Arellano-Bond 1991)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Số bước ước lượng & Sai số</label>
          <div className="space-y-1 mt-1 text-xs">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={twoStep}
                onChange={e => setTwoStep(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span>Two-step GMM (Trọng số tối ưu)</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={windmeijerCorrection}
                onChange={e => setWindmeijerCorrection(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span>Hiệu chỉnh Windmeijer (2005)</span>
            </label>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Độ trễ công cụ tối đa (Max Lags)</label>
          <input
            type="number"
            min={1}
            max={8}
            value={maxInstrumentLags}
            onChange={e => setMaxInstrumentLags(parseInt(e.target.value, 10) || 3)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          />
          <span className="text-[10px] text-slate-500">Giảm thiểu bùng nổ biến công cụ (Roodman, 2009)</span>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Phạm vi mẫu phân tích</label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as any)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          >
            <option value="all">Tất cả phản hồi</option>
            <option value="verified_clean">Chỉ phản hồi đã xác minh sạch</option>
          </select>
        </div>
      </div>

      {/* Action CTA */}
      <button
        onClick={handleRunAnalysis}
        disabled={loading}
        className="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white text-sm font-semibold rounded-lg shadow-sm transition flex items-center justify-center gap-2 mb-6"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Đang ước lượng GMM & Kiểm định đặc tả...</span>
          </>
        ) : (
          <span>Ước lượng Mô hình Dynamic Panel GMM</span>
        )}
      </button>

      {/* Error alert */}
      {error && (
        <div className="p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Lỗi:</strong> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Diagnostic Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Đối tượng & Quan sát</div>
              <div className="text-lg font-bold text-slate-800 mt-1">
                N={result.diagnostics.num_panel_units} <span className="text-xs font-normal text-slate-500">({result.diagnostics.total_observations} obs)</span>
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">{result.diagnostics.time_waves} đợt sóng thời gian</div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Hệ số Tự hồi quy (alpha)</div>
              <div className="text-lg font-bold text-indigo-700 mt-1">
                {result.diagnostics.alpha_gmm}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">SE: {result.diagnostics.se_alpha_gmm}</div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Giới hạn Nickell (1981)</div>
              <div className="text-xs font-bold text-slate-800 mt-1.5 flex items-center gap-1.5">
                <span className="text-amber-600">FE: {result.diagnostics.alpha_fe_bound}</span>
                <span>≤ GMM ≤</span>
                <span className="text-blue-600">OLS: {result.diagnostics.alpha_ols_bound}</span>
              </div>
              <div className="mt-1">
                {result.diagnostics.nickell_bound_passed ? (
                  <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 text-emerald-800 rounded font-semibold">
                    Đạt điều kiện Nickell
                  </span>
                ) : (
                  <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-semibold">
                    Vượt biên Nickell
                  </span>
                )}
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Kiểm định Hansen & AR(2)</div>
              <div className="text-xs font-semibold text-slate-800 mt-1">
                Hansen p: <span className={result.diagnostics.hansen_valid ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{result.diagnostics.hansen_p_value}</span>
              </div>
              <div className="text-xs font-semibold text-slate-800 mt-0.5">
                AR(2) p: <span className={result.diagnostics.ar2_valid ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{result.diagnostics.ar2_p_value}</span>
              </div>
            </div>
          </div>

          {/* Parameters Table */}
          {result.parameters && result.parameters.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-slate-800 mb-2">Bảng Ước lượng Hệ số GMM</h3>
              <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-2.5">Tham số</th>
                      <th className="px-4 py-2.5">Hệ số (Coef)</th>
                      <th className="px-4 py-2.5">Sai số chuẩn (SE)</th>
                      <th className="px-4 py-2.5">z-stat</th>
                      <th className="px-4 py-2.5">p-value</th>
                      <th className="px-4 py-2.5">Khoảng tin cậy 95%</th>
                      <th className="px-4 py-2.5 text-center">Ý nghĩa</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.parameters.map((p, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                        <td className="px-4 py-2.5 font-semibold text-slate-800">{p.parameter}</td>
                        <td className="px-4 py-2.5 font-bold text-indigo-700">{p.estimate.toFixed(4)}</td>
                        <td className="px-4 py-2.5 text-slate-600">{p.std_error.toFixed(4)}</td>
                        <td className="px-4 py-2.5 text-slate-600">{p.z_statistic.toFixed(2)}</td>
                        <td className="px-4 py-2.5 font-semibold">
                          <span className={p.p_value < 0.05 ? 'text-emerald-700' : 'text-slate-600'}>
                            {p.p_value < 0.001 ? '< .001' : p.p_value.toFixed(3)}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-slate-600">
                          [{p.ci_lower.toFixed(3)}, {p.ci_upper.toFixed(3)}]
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          {p.is_significant ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                              Có ý nghĩa (p &lt; .05)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">
                              Không
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SVG Chart Visualization */}
          {result.svg_visualization && (
            <div className="mt-4">
              <h3 className="text-sm font-bold text-slate-800 mb-2">Đồ thị Kiểm định Giới hạn Nickell & Chẩn đoán Mô hình</h3>
              <div
                className="w-full overflow-x-auto p-4 bg-white border border-slate-200 rounded-lg shadow-sm"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-indigo-50/60 border border-indigo-100 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-indigo-900 uppercase tracking-wide">
                  Tường thuật Khoa học chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyToClipboard}
                  className="text-xs px-2.5 py-1 bg-white border border-indigo-200 hover:bg-indigo-50 text-indigo-700 font-medium rounded transition"
                >
                  {copied ? 'Đã sao chép!' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-serif italic">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
