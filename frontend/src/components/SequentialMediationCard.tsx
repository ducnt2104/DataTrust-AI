import React, { useState } from 'react';
import { api } from '../api/client';
import { SequentialMediationResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const SequentialMediationCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQid, setTreatmentQid] = useState<string>('');
  const [mediator1Qid, setMediator1Qid] = useState<string>('');
  const [mediator2Qid, setMediator2Qid] = useState<string>('');
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [nBootstraps, setNBootstraps] = useState<number>(500);
  const [alphaLevel, setAlphaLevel] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SequentialMediationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const toggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQid || !mediator1Qid || !mediator2Qid || !outcomeQid) {
      setError('Vui lòng chọn đầy đủ 4 biến: Biến can thiệp T, Biến trung gian M1, Biến trung gian M2 và Biến kết quả Y.');
      return;
    }
    const qidSet = new Set([treatmentQid, mediator1Qid, mediator2Qid, outcomeQid]);
    if (qidSet.size < 4) {
      setError('Bốn biến T, M1, M2 và Y phải là các câu hỏi khác nhau.');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const data = await api.runSequentialMediation(surveyId, {
        treatment_question_id: treatmentQid,
        mediator1_question_id: mediator1Qid,
        mediator2_question_id: mediator2Qid,
        outcome_question_id: outcomeQid,
        covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
        n_bootstraps: nBootstraps,
        alpha_level: alphaLevel,
        scope
      });

      if (data.status === 'INSUFFICIENT_SAMPLE' || data.status === 'ERROR') {
        setError(data.message || 'Lỗi khi thực hiện phân tích Sequential Mediation.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi thực hiện phân tích trung gian tuần tự.');
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
              Sequential Causal Mediation & Path Decomposition
            </h2>
            <span className="bg-purple-50 text-purple-700 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-purple-200">
              Hayes Model 6 · Imai & Yamamoto 2013
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Phân tích cơ chế nhân quả dạng chuỗi xích (Chained Mechanism) với yếu tố gây nhiễu trung gian: Phân rã hiệu ứng trực tiếp, hai đường dẫn đơn lập và đường dẫn tuần tự (T → M1 → M2 → Y).
          </p>
        </div>
      </div>

      {/* Primary Variable Selectors */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến can thiệp T (Treatment) <span className="text-red-500">*</span>
          </label>
          <select
            value={treatmentQid}
            onChange={e => setTreatmentQid(e.target.value)}
            className="w-full text-xs border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-purple-500"
          >
            <option value="">-- Chọn biến can thiệp T --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Trung gian 1 (M1 - Cấp 1) <span className="text-red-500">*</span>
          </label>
          <select
            value={mediator1Qid}
            onChange={e => setMediator1Qid(e.target.value)}
            className="w-full text-xs border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-purple-500"
          >
            <option value="">-- Chọn biến trung gian M1 --</option>
            {questions
              .filter(q => q.id !== treatmentQid)
              .map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Trung gian 2 (M2 - Cấp 2) <span className="text-red-500">*</span>
          </label>
          <select
            value={mediator2Qid}
            onChange={e => setMediator2Qid(e.target.value)}
            className="w-full text-xs border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-purple-500"
          >
            <option value="">-- Chọn biến trung gian M2 --</option>
            {questions
              .filter(q => q.id !== treatmentQid && q.id !== mediator1Qid)
              .map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Biến kết quả Y (Outcome) <span className="text-red-500">*</span>
          </label>
          <select
            value={outcomeQid}
            onChange={e => setOutcomeQid(e.target.value)}
            className="w-full text-xs border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:bg-white focus:ring-2 focus:ring-purple-500"
          >
            <option value="">-- Chọn biến kết quả Y --</option>
            {questions
              .filter(q => q.id !== treatmentQid && q.id !== mediator1Qid && q.id !== mediator2Qid)
              .map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* Covariates Multi-select (X) */}
      <div className="mb-6">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">
          Biến hiệp biến kiểm soát ngoại sinh X (Exogenous Controls, Tùy chọn)
        </label>
        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-slate-50 border border-slate-200 rounded-lg">
          {questions
            .filter(q => q.id !== treatmentQid && q.id !== mediator1Qid && q.id !== mediator2Qid && q.id !== outcomeQid)
            .map(q => {
              const isChecked = selectedCovariates.includes(q.id);
              return (
                <button
                  type="button"
                  key={q.id}
                  onClick={() => toggleCovariate(q.id)}
                  className={`text-xs px-2.5 py-1.5 rounded-md border transition-all text-left ${
                    isChecked
                      ? 'bg-purple-600 text-white border-purple-600 font-medium'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {isChecked ? '✓ ' : '+ '}
                  {q.title}
                </button>
              );
            })}
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg border border-slate-100 mb-6 text-sm">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Số lần lặp Bootstrap (Resamples)</label>
          <input
            type="number"
            min={100}
            max={2000}
            step={50}
            value={nBootstraps}
            onChange={e => setNBootstraps(parseInt(e.target.value, 10) || 500)}
            className="w-full text-xs border border-slate-200 rounded p-2 bg-white"
          />
          <span className="text-[10px] text-slate-500">Khuyến nghị ≥ 500 lần lặp phân vị</span>
        </div>

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
        className="w-full sm:w-auto px-6 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white text-sm font-semibold rounded-lg shadow-sm transition flex items-center justify-center gap-2 mb-6"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Đang ước lượng Bootstrap {nBootstraps} lần lặp...</span>
          </>
        ) : (
          <span>Phân tích Trung gian Tuần tự & Phân rã Đường dẫn Causal</span>
        )}
      </button>

      {/* Error display */}
      {error && (
        <div className="p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Lỗi:</strong> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.effects && (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Đường dẫn Tuần tự (Sequential)</div>
              <div className="text-lg font-bold text-indigo-700 mt-1">
                {result.effects.indirect_sequential_m1_m2.estimate.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                {result.effects.indirect_sequential_m1_m2.is_significant ? (
                  <span className="text-emerald-700 font-bold">★ Có ý nghĩa thống kê</span>
                ) : (
                  <span>Không có ý nghĩa</span>
                )}
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Tổng Hiệu ứng Gián tiếp</div>
              <div className="text-lg font-bold text-emerald-700 mt-1">
                {result.effects.indirect_total.estimate.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Chiếm {(result.proportions?.proportion_mediated_total ?? 0) * 100 > 0 ? ((result.proportions?.proportion_mediated_total ?? 0) * 100).toFixed(1) : 0}% tổng hiệu ứng
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Hiệu ứng Trực tiếp (c')</div>
              <div className="text-lg font-bold text-amber-700 mt-1">
                {result.effects.direct_effect.estimate.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                SE={result.effects.direct_effect.bootstrap_se.toFixed(3)}
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-medium">Tổng Hiệu ứng Causal (TE)</div>
              <div className="text-lg font-bold text-slate-800 mt-1">
                {result.effects.total_effect.estimate.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                N={result.sample_size} ({result.bootstrap_replications} boot)
              </div>
            </div>
          </div>

          {/* Path-Specific Decomposition Table */}
          <div>
            <h3 className="text-sm font-bold text-slate-800 mb-2">Bảng Phân rã Hiệu ứng theo Đường dẫn (Path-Specific Effects)</h3>
            <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2.5">Đường dẫn Causal</th>
                    <th className="px-4 py-2.5">Công thức Đại số</th>
                    <th className="px-4 py-2.5">Hệ số (Est)</th>
                    <th className="px-4 py-2.5">Sai số Bootstrap</th>
                    <th className="px-4 py-2.5">Khoảng Tin Cậy 95%</th>
                    <th className="px-4 py-2.5 text-center">Ý nghĩa Thống kê</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="bg-indigo-50/40">
                    <td className="px-4 py-2.5 font-bold text-indigo-950">Đường dẫn Tuần tự (Chained Path)</td>
                    <td className="px-4 py-2.5 font-mono text-indigo-800">a1 × d21 × b2</td>
                    <td className="px-4 py-2.5 font-bold text-indigo-700">{result.effects.indirect_sequential_m1_m2.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.effects.indirect_sequential_m1_m2.bootstrap_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">[{result.effects.indirect_sequential_m1_m2.ci_lower.toFixed(3)}, {result.effects.indirect_sequential_m1_m2.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      {result.effects.indirect_sequential_m1_m2.is_significant ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Có ý nghĩa</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">Không</span>
                      )}
                    </td>
                  </tr>

                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">Đường dẫn Đơn lập 1 (T → M1 → Y)</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">a1 × b1</td>
                    <td className="px-4 py-2.5 font-bold text-emerald-700">{result.effects.indirect_path1_m1.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.effects.indirect_path1_m1.bootstrap_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">[{result.effects.indirect_path1_m1.ci_lower.toFixed(3)}, {result.effects.indirect_path1_m1.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      {result.effects.indirect_path1_m1.is_significant ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Có ý nghĩa</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">Không</span>
                      )}
                    </td>
                  </tr>

                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">Đường dẫn Đơn lập 2 (T → M2 → Y)</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">a2 × b2</td>
                    <td className="px-4 py-2.5 font-bold text-blue-700">{result.effects.indirect_path2_m2.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.effects.indirect_path2_m2.bootstrap_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">[{result.effects.indirect_path2_m2.ci_lower.toFixed(3)}, {result.effects.indirect_path2_m2.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      {result.effects.indirect_path2_m2.is_significant ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Có ý nghĩa</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">Không</span>
                      )}
                    </td>
                  </tr>

                  <tr className="bg-slate-50/50">
                    <td className="px-4 py-2.5 font-bold text-slate-900">Tổng Hiệu ứng Gián tiếp (Total Indirect)</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">IE1 + IE2 + IE_seq</td>
                    <td className="px-4 py-2.5 font-bold text-purple-700">{result.effects.indirect_total.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.effects.indirect_total.bootstrap_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">[{result.effects.indirect_total.ci_lower.toFixed(3)}, {result.effects.indirect_total.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      {result.effects.indirect_total.is_significant ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Có ý nghĩa</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">Không</span>
                      )}
                    </td>
                  </tr>

                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-800">Hiệu ứng Trực tiếp (Direct Effect)</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">c'</td>
                    <td className="px-4 py-2.5 font-bold text-amber-700">{result.effects.direct_effect.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.effects.direct_effect.bootstrap_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">[{result.effects.direct_effect.ci_lower.toFixed(3)}, {result.effects.direct_effect.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      {result.effects.direct_effect.is_significant ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Có ý nghĩa</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">Không</span>
                      )}
                    </td>
                  </tr>

                  <tr className="bg-slate-100 font-bold">
                    <td className="px-4 py-2.5 text-slate-900">Tổng Hiệu ứng Can thiệp (Total Effect)</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">c' + IE_total</td>
                    <td className="px-4 py-2.5 text-slate-900">{result.effects.total_effect.estimate.toFixed(4)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{result.effects.total_effect.bootstrap_se.toFixed(4)}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-700">[{result.effects.total_effect.ci_lower.toFixed(3)}, {result.effects.total_effect.ci_upper.toFixed(3)}]</td>
                    <td className="px-4 py-2.5 text-center">
                      {result.effects.total_effect.is_significant ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Có ý nghĩa</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">Không</span>
                      )}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* SVG Diagram & Forest Plot */}
          {result.svg_visualization && (
            <div className="mt-4">
              <h3 className="text-sm font-bold text-slate-800 mb-2">Sơ đồ Đường dẫn Nhân quả & Biểu đồ Forest Plot Phân vị Bootstrap</h3>
              <div
                className="w-full overflow-x-auto p-4 bg-white border border-slate-200 rounded-lg shadow-sm"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-purple-50/60 border border-purple-100 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-purple-900 uppercase tracking-wide">
                  Tường thuật Khoa học chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyToClipboard}
                  className="text-xs px-2.5 py-1 bg-white border border-purple-200 hover:bg-purple-50 text-purple-700 font-medium rounded transition"
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
