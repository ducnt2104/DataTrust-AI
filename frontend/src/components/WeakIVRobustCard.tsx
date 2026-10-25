import React, { useState } from 'react';
import { api } from '../api/client';
import { WeakIVRobustResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const WeakIVRobustCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [endogenousQid, setEndogenousQid] = useState<string>('');
  const [selectedInstruments, setSelectedInstruments] = useState<string[]>([]);
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [gridPoints, setGridPoints] = useState<number>(120);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<WeakIVRobustResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleInstrument = (qid: string) => {
    setSelectedInstruments(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQid || !endogenousQid) {
      setError('Vui lòng chọn Biến kết quả (Outcome) và Biến nội sinh (Endogenous Regressor).');
      return;
    }
    if (selectedInstruments.length === 0) {
      setError('Vui lòng chọn ít nhất một Biến công cụ (Instrument Variable Z).');
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const data = await api.runWeakIVRobust(surveyId, {
        outcome_question_id: outcomeQid,
        endogenous_question_id: endogenousQid,
        instrument_question_ids: selectedInstruments,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        alpha_level: alphaLevel,
        grid_points: gridPoints,
        scope
      });

      if (data.status === 'INSUFFICIENT_SAMPLE' || data.status === 'ERROR') {
        setError(data.message || 'Lỗi khi thực hiện phân tích Weak-IV.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực hiện phân tích Weak-IV Robust.');
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

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'STRONG_IDENTIFICATION':
        return (
          <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-0.5 rounded-full font-bold border border-emerald-300">
            Công cụ mạnh vững chắc (F_eff ≥ 23.1)
          </span>
        );
      case 'MODERATE_IDENTIFICATION':
        return (
          <span className="bg-blue-100 text-blue-800 text-xs px-2.5 py-0.5 rounded-full font-bold border border-blue-300">
            Công cụ trung bình (F ≥ 10)
          </span>
        );
      case 'WEAK_IDENTIFICATION':
        return (
          <span className="bg-amber-100 text-amber-800 text-xs px-2.5 py-0.5 rounded-full font-bold border border-amber-300">
            Công cụ yếu cảnh báo (Wald CI bị méo)
          </span>
        );
      default:
        return (
          <span className="bg-rose-100 text-rose-800 text-xs px-2.5 py-0.5 rounded-full font-bold border border-rose-300">
            Công cụ cực yếu / Chưa định danh
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-4 mb-6 border-b border-slate-100 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-800">
              Weak-Instrument Robust Inference & Identification
            </h2>
            <span className="bg-emerald-50 text-emerald-700 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
              Moreira CLR · Anderson-Rubin
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Suy diễn nhân quả vững trước biến công cụ yếu: Đảo ngược nghiệm Anderson-Rubin (1949), kiểm định tỷ số hợp lý có điều kiện Moreira (2003) và thống kê hiệu quả Montiel Olea & Pflueger (2013).
          </p>
        </div>
      </div>

      {/* Primary Variable Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kết quả phụ thuộc Y (Outcome) <span className="text-red-500">*</span>
          </label>
          <select
            value={outcomeQid}
            onChange={e => setOutcomeQid(e.target.value)}
            className="w-full text-sm border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến can thiệp nội sinh Y_endog (Endogenous Predictor) <span className="text-red-500">*</span>
          </label>
          <select
            value={endogenousQid}
            onChange={e => setEndogenousQid(e.target.value)}
            className="w-full text-sm border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến nội sinh cần khắc phục chệch --</option>
            {questions
              .filter(q => q.id !== outcomeQid)
              .map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* Instruments Multi-select (Z) */}
      <div className="mb-6">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">
          Biến công cụ ngoại sinh loại trừ Z (Instrumental Variables) <span className="text-red-500">*</span>
        </label>
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-2 bg-slate-50 border border-slate-200 rounded-lg">
          {questions
            .filter(q => q.id !== outcomeQid && q.id !== endogenousQid)
            .map(q => {
              const isChecked = selectedInstruments.includes(q.id);
              return (
                <button
                  type="button"
                  key={q.id}
                  onClick={() => toggleInstrument(q.id)}
                  className={`text-xs px-2.5 py-1.5 rounded-md border transition-all text-left ${
                    isChecked
                      ? 'bg-emerald-600 text-white border-emerald-600 font-medium'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {isChecked ? '✓ ' : '+ '}
                  {q.title}
                </button>
              );
            })}
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          Đã chọn: {selectedInstruments.length} biến công cụ. (Khuyến nghị ≥ 2 công cụ để kiểm định quá đồng nhất).
        </p>
      </div>

      {/* Covariates Multi-select (X) */}
      <div className="mb-6">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">
          Biến hiệp biến kiểm soát ngoại sinh X (Exogenous Controls, Tùy chọn)
        </label>
        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-slate-50 border border-slate-200 rounded-lg">
          {questions
            .filter(q => q.id !== outcomeQid && q.id !== endogenousQid && !selectedInstruments.includes(q.id))
            .map(q => {
              const isChecked = selectedCovariates.includes(q.id);
              return (
                <button
                  type="button"
                  key={q.id}
                  onClick={() => toggleCovariate(q.id)}
                  className={`text-xs px-2.5 py-1.5 rounded-md border transition-all text-left ${
                    isChecked
                      ? 'bg-slate-700 text-white border-slate-700 font-medium'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {q.title}
                </button>
              );
            })}
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg border border-slate-100 mb-6 text-sm">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Mức ý nghĩa thống kê (alpha)</label>
          <select
            value={alphaLevel}
            onChange={e => setAlphaLevel(parseFloat(e.target.value) || 0.05)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          >
            <option value={0.01}>alpha = 0.01 (Độ tin cậy 99%)</option>
            <option value={0.05}>alpha = 0.05 (Độ tin cậy 95%)</option>
            <option value={0.10}>alpha = 0.10 (Độ tin cậy 90%)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Độ phân giải lưới đảo nghiệm</label>
          <input
            type="number"
            min={60}
            max={300}
            value={gridPoints}
            onChange={e => setGridPoints(parseInt(e.target.value, 10) || 120)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          />
          <span className="text-[10px] text-slate-500">Số điểm lưới tìm nghiệm Moreira CLR & K-test</span>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Phạm vi dữ liệu khảo sát</label>
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
        className="w-full sm:w-auto px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white text-sm font-semibold rounded-lg shadow-sm transition flex items-center justify-center gap-2 mb-6"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Đang đảo nghiệm AR & Tính toán Moreira CLR...</span>
          </>
        ) : (
          <span>Thực thi Kiểm định Weak-IV & Ước lượng Moreira CLR</span>
        )}
      </button>

      {/* Error display */}
      {error && (
        <div className="p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Lỗi:</strong> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && result.estimates && (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Diagnostic Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Độ mạnh Công cụ (Effective F)</div>
              <div className="text-lg font-bold text-slate-800 mt-1">
                F_eff = {result.diagnostics.effective_f}
              </div>
              <div className="mt-1">{getStatusBadge(result.diagnostics.identification_status)}</div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Hồi quy Bước 1 (First-Stage)</div>
              <div className="text-lg font-bold text-emerald-700 mt-1">
                F = {result.diagnostics.first_stage_f}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                p = {result.diagnostics.first_stage_p < 0.001 ? '< .001' : result.diagnostics.first_stage_p} ({result.diagnostics.num_instruments} instruments)
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Kiểm định Anderson-Rubin (H0: beta=0)</div>
              <div className="text-lg font-bold text-blue-700 mt-1">
                AR F = {result.diagnostics.ar_null_zero_f_stat}
              </div>
              <div className="text-[11px] text-slate-600 mt-0.5 font-semibold">
                p = {result.diagnostics.ar_null_zero_p_value < 0.001 ? '< .001' : result.diagnostics.ar_null_zero_p_value} (Exact Size)
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">So sánh Ước lượng 2SLS vs OLS</div>
              <div className="text-xs font-bold text-slate-800 mt-1.5 flex flex-col gap-0.5">
                <span className="text-emerald-700">2SLS: {result.estimates.beta_2sls} (SE: {result.estimates.se_2sls})</span>
                <span className="text-amber-600">OLS: {result.estimates.beta_ols} (SE: {result.estimates.se_ols})</span>
              </div>
            </div>
          </div>

          {/* Confidence Intervals Comparison Table */}
          <div>
            <h3 className="text-sm font-bold text-slate-800 mb-2">So sánh Khoảng Tin Cậy 95% (Robust vs Conventional)</h3>
            <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2.5">Phương pháp Ước lượng / Kiểm định</th>
                    <th className="px-4 py-2.5">Loại Khoảng Tin Cậy</th>
                    <th className="px-4 py-2.5">Khoảng Tin Cậy 95%</th>
                    <th className="px-4 py-2.5">Đặc tính Lý thuyết</th>
                    <th className="px-4 py-2.5 text-center">Trạng thái Khuyên dùng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="bg-emerald-50/40">
                    <td className="px-4 py-2.5 font-bold text-emerald-900">Moreira (2003) CLR</td>
                    <td className="px-4 py-2.5 text-slate-700">Kiểm định Tỷ số Hợp lý Có điều kiện</td>
                    <td className="px-4 py-2.5 font-bold text-emerald-800">
                      {result.estimates.clr_ci_95 ? `[${result.estimates.clr_ci_95[0]}, ${result.estimates.clr_ci_95[1]}]` : 'Không xác định'}
                    </td>
                    <td className="px-4 py-2.5 text-slate-600">Mạnh nhất bất biến (Uniformly Most Powerful Invariant)</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-200 text-emerald-900">
                        Khuyên dùng Hàng đầu
                      </span>
                    </td>
                  </tr>

                  <tr className="bg-blue-50/30">
                    <td className="px-4 py-2.5 font-bold text-blue-900">Anderson-Rubin (1949) AR</td>
                    <td className="px-4 py-2.5 text-slate-700">Đảo nghiệm Phương trình Bậc hai Exact</td>
                    <td className="px-4 py-2.5 font-bold text-blue-800">
                      {result.estimates.ar_ci_95 && result.estimates.ar_ci_95.length > 0
                        ? result.estimates.ar_ci_95.map(iv => `[${iv[0]}, ${iv[1]}]`).join(' U ')
                        : result.estimates.ar_ci_type}
                    </td>
                    <td className="px-4 py-2.5 text-slate-600">Đúng kích thước mẫu hữu hạn tuyệt đối (Exact Finite-Sample)</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                        Chuẩn Mực Tuyệt Đối
                      </span>
                    </td>
                  </tr>

                  {result.estimates.kleibergen_k_ci_95 && (
                    <tr className="bg-purple-50/20">
                      <td className="px-4 py-2.5 font-bold text-purple-900">Kleibergen (2002) K-Test</td>
                      <td className="px-4 py-2.5 text-slate-700">Lagrange Multiplier Score Test</td>
                      <td className="px-4 py-2.5 font-bold text-purple-800">
                        [{result.estimates.kleibergen_k_ci_95[0]}, {result.estimates.kleibergen_k_ci_95[1]}]
                      </td>
                      <td className="px-4 py-2.5 text-slate-600">Tiệm cận Chi2(1) không phụ thuộc số công cụ</td>
                      <td className="px-4 py-2.5 text-center">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-purple-100 text-purple-800">
                          Hợp lệ
                        </span>
                      </td>
                    </tr>
                  )}

                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">Standard 2SLS (Wald)</td>
                    <td className="px-4 py-2.5 text-slate-700">Wald t-statistic tiệm cận</td>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">
                      [{result.estimates.wald_ci_95[0]}, {result.estimates.wald_ci_95[1]}]
                    </td>
                    <td className="px-4 py-2.5 text-slate-600">Bị méo kích thước nặng nề khi công cụ yếu (F &lt; 10)</td>
                    <td className="px-4 py-2.5 text-center">
                      {result.diagnostics.effective_f < 10 ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800">
                          Cảnh báo Không Tin Cậy
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">
                          Khả dụng
                        </span>
                      )}
                    </td>
                  </tr>

                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-600">Baseline OLS</td>
                    <td className="px-4 py-2.5 text-slate-500">Bình phương tối thiểu thông thường</td>
                    <td className="px-4 py-2.5 text-slate-600">
                      [{result.estimates.beta_ols - 1.96 * result.estimates.se_ols}, {result.estimates.beta_ols + 1.96 * result.estimates.se_ols}]
                    </td>
                    <td className="px-4 py-2.5 text-slate-500">Chệch do biến nội sinh / yếu tố gây nhiễu chưa quan sát</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800">
                        Đối chứng thiên lệch
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* SVG Chart Visualization */}
          {result.svg_visualization && (
            <div className="mt-4">
              <h3 className="text-sm font-bold text-slate-800 mb-2">Đồ thị Đường Đảo Nghiệm AR/CLR & So sánh Khoảng Tin Cậy Forest Plot</h3>
              <div
                className="w-full overflow-x-auto p-4 bg-white border border-slate-200 rounded-lg shadow-sm"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-emerald-50/60 border border-emerald-100 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-emerald-900 uppercase tracking-wide">
                  Tường thuật Kinh tế lượng chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyToClipboard}
                  className="text-xs px-2.5 py-1 bg-white border border-emerald-200 hover:bg-emerald-50 text-emerald-700 font-medium rounded transition"
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
