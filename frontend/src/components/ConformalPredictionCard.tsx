import React, { useState } from 'react';
import { api } from '../api/client';
import { ConformalPredictionResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface ConformalPredictionCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const ConformalPredictionCard: React.FC<ConformalPredictionCardProps> = ({
  surveyId,
  questions
}) => {
  const [targetQId, setTargetQId] = useState<string>('');
  const [selectedFeatureQIds, setSelectedFeatureQIds] = useState<string[]>([]);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [method, setMethod] = useState<'split_conformal' | 'locally_weighted'>('split_conformal');
  const [clampMin, setClampMin] = useState<string>('');
  const [clampMax, setClampMax] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConformalPredictionResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleFeature = (qid: string) => {
    if (selectedFeatureQIds.includes(qid)) {
      setSelectedFeatureQIds(selectedFeatureQIds.filter(id => id !== qid));
    } else {
      setSelectedFeatureQIds([...selectedFeatureQIds, qid]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!targetQId) {
      setError('Vui lòng chọn câu hỏi mục tiêu (Target Metric) cần dự báo khoảng rủi ro.');
      return;
    }
    if (selectedFeatureQIds.length === 0) {
      setError('Vui lòng chọn ít nhất một câu hỏi đặc trưng (Features / Covariates).');
      return;
    }
    if (selectedFeatureQIds.includes(targetQId)) {
      setError('Biến mục tiêu không thể đồng thời là biến đặc trưng dự báo.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runConformalPrediction(surveyId, {
        target_question_id: targetQId,
        feature_question_ids: selectedFeatureQIds,
        alpha,
        method,
        clamp_min: clampMin !== '' ? parseFloat(clampMin) : undefined,
        clamp_max: clampMax !== '' ? parseFloat(clampMax) : undefined,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể tính toán khoảng dự báo Conformal Prediction.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích Conformal Prediction.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
              Distribution-Free Risk Quantification
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Vovk et al. (2005) • Shafer &amp; Vovk (2008) • Angelopoulos &amp; Bates (2023)
            </span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Conformal Prediction &amp; Distribution-Free Risk Intervals
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Dự báo khoảng bất định phân phối tự do với bảo đảm toán học hữu hạn mẫu tuyệt đối: P(Y ∈ C(X)) ≥ 1 - α, không phụ thuộc vào giả định phân phối chuẩn hay tính đồng nhất phương sai.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến mục tiêu dự báo (Target Outcome) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={targetQId}
            onChange={(e) => setTargetQId(e.target.value)}
          >
            <option value="">-- Chọn biến mục tiêu số --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Phương pháp Conformal
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={method}
            onChange={(e) => setMethod(e.target.value as any)}
          >
            <option value="split_conformal">Split Conformal (Residual Cơ chuẩn)</option>
            <option value="locally_weighted">Locally-Weighted (Thích ứng Phương sai Dị biệt)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Mức tin cậy danh nghĩa (1 - α)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={alpha}
            onChange={(e) => setAlpha(parseFloat(e.target.value))}
          >
            <option value={0.01}>99% Coverage (α = 0.01)</option>
            <option value={0.05}>95% Coverage (α = 0.05 - Mặc định)</option>
            <option value={0.10}>90% Coverage (α = 0.10)</option>
            <option value={0.20}>80% Coverage (α = 0.20)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Phạm vi dữ liệu (Scope)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
          >
            <option value="all">Toàn bộ phản hồi (All)</option>
            <option value="verified_clean">Chỉ phản hồi sạch đã kiểm định (Clean)</option>
          </select>
        </div>
      </div>

      {/* Feature Selection & Clamping */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Chọn các biến đặc trưng (Features / Covariates) *
          </label>
          <div className="max-h-36 overflow-y-auto bg-slate-950 border border-slate-700 rounded-lg p-2.5 space-y-1.5">
            {numericQuestions.map(q => {
              if (q.id === targetQId) return null;
              const isChecked = selectedFeatureQIds.includes(q.id);
              return (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleFeature(q.id)}
                    className="rounded border-slate-700 text-emerald-500 focus:ring-emerald-500 bg-slate-900"
                  />
                  <span>{q.title}</span>
                </label>
              );
            })}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Ràng buộc biên giá trị thang đo (Tùy chọn)
          </label>
          <div className="grid grid-cols-2 gap-3 mt-1">
            <div>
              <span className="text-xs text-slate-400 mb-1 block">Cận dưới (Min Clamp):</span>
              <input
                type="number"
                placeholder="VD: 1.0 (Likert min)"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                value={clampMin}
                onChange={(e) => setClampMin(e.target.value)}
              />
            </div>
            <div>
              <span className="text-xs text-slate-400 mb-1 block">Cận trên (Max Clamp):</span>
              <input
                type="number"
                placeholder="VD: 5.0 hoặc 10.0"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                value={clampMax}
                onChange={(e) => setClampMax(e.target.value)}
              />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Áp dụng cắt biên để dải dự báo không vượt ra ngoài miền giá trị thực tế của thang đo khảo sát.
          </p>
        </div>
      </div>

      {/* Action Button */}
      <div className="mt-5 flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang tính toán phân vị hiệu chuẩn...</span>
            </>
          ) : (
            <>
              <span>Kiểm định Khoảng Rủi ro Conformal</span>
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Độ bao phủ Danh nghĩa</span>
              <span className="text-xl font-bold text-white font-mono">
                {Math.round((result.parameters?.nominal_coverage || 0.95) * 100)}%
              </span>
              <span className="text-[11px] text-slate-500 block">α = {result.parameters?.alpha}</span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Bao phủ Thực nghiệm Conformal</span>
              <span className="text-xl font-bold text-emerald-400 font-mono">
                {Math.round((result.evaluation_metrics?.conformal_coverage || 0) * 100)}%
              </span>
              <span className="text-[11px] text-emerald-500/80 block">Cam kết hữu hạn mẫu</span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Bao phủ Gaussian Chuẩn</span>
              <span className={`text-xl font-bold font-mono ${
                (result.evaluation_metrics?.gaussian_coverage || 0) < (result.evaluation_metrics?.conformal_coverage || 0)
                  ? 'text-rose-400'
                  : 'text-amber-400'
              }`}>
                {Math.round((result.evaluation_metrics?.gaussian_coverage || 0) * 100)}%
              </span>
              <span className="text-[11px] text-slate-500 block">Giả định cổ điển</span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Độ rộng TB Khoảng Tin cậy</span>
              <span className="text-xl font-bold text-sky-400 font-mono">
                {result.evaluation_metrics?.conformal_mean_width?.toFixed(2)}
              </span>
              <span className="text-[11px] text-slate-500 block">
                Trung vị: {result.evaluation_metrics?.conformal_median_width?.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Theoretical Guarantee Callout */}
          <div className="p-4 bg-emerald-950/20 border border-emerald-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="p-1.5 bg-emerald-500/10 rounded-md text-emerald-400 mt-0.5">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div className="text-sm">
                <h4 className="font-semibold text-emerald-300">
                  Chứng thực Toán học Hữu hạn Mẫu (Finite-Sample Marginal Validity)
                </h4>
                <p className="text-slate-300 mt-1 leading-relaxed">
                  Với phân vị hiệu chuẩn conformal <code className="text-emerald-400 font-mono">q̂_{'{1-α}'} = {result.parameters?.conformal_quantile?.toFixed(3)}</code> trên {result.sample_sizes?.calibration} mẫu hiệu chuẩn độc lập, xác suất người tham gia khảo sát mới rơi vào khoảng dự báo được bảo đảm tuyệt đối:
                </p>
                <div className="mt-1 font-mono text-xs text-emerald-200">
                  {result.parameters?.nominal_coverage} ≤ P(Y_{'{n+1}'} ∈ Ĉ(X_{'{n+1}'})) ≤ {result.parameters?.finite_sample_upper_bound}
                </div>
              </div>
            </div>
          </div>

          {/* SVG Visualizations */}
          {result.svg_chart && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-hidden">
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Calibration Curve Table */}
          {result.calibration_curve && result.calibration_curve.length > 0 && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2">
                Bảng Chuẩn hóa Độ bao phủ Đa mức (Calibration Reliability Schedule)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900 text-slate-400 font-medium">
                    <tr>
                      <th className="p-2">Mức ý nghĩa (α)</th>
                      <th className="p-2">Kỳ vọng Danh nghĩa (1 - α)</th>
                      <th className="p-2">Thực nghiệm Conformal</th>
                      <th className="p-2">Thực nghiệm Gaussian</th>
                      <th className="p-2">Ngưỡng Phân vị (q̂)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono">
                    {result.calibration_curve.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        <td className="p-2 text-slate-300">{row.alpha}</td>
                        <td className="p-2 text-slate-200 font-semibold">{Math.round(row.nominal_coverage * 100)}%</td>
                        <td className="p-2 text-emerald-400 font-bold">{Math.round(row.conformal_coverage * 100)}%</td>
                        <td className="p-2 text-rose-400">{Math.round(row.gaussian_coverage * 100)}%</td>
                        <td className="p-2 text-slate-400">{row.quantile_cutoff.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Out-of-Sample Predictions Sample */}
          {result.sample_predictions && result.sample_predictions.length > 0 && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2">
                Khoảng Dự báo Conformal Thực tế Ngoài Mẫu (Out-of-Sample Evaluation)
              </h4>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900 text-slate-400 font-medium sticky top-0">
                    <tr>
                      <th className="p-2">STT</th>
                      <th className="p-2">Thực tế (Y)</th>
                      <th className="p-2">Kỳ vọng (Ŷ)</th>
                      <th className="p-2">Cận dưới</th>
                      <th className="p-2">Cận trên</th>
                      <th className="p-2">Độ rộng</th>
                      <th className="p-2">Trạng thái Bao phủ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono">
                    {result.sample_predictions.map((p, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        <td className="p-2 text-slate-400">#{p.test_index + 1}</td>
                        <td className="p-2 text-white font-semibold">{p.actual_y.toFixed(2)}</td>
                        <td className="p-2 text-slate-300">{p.predicted_y.toFixed(2)}</td>
                        <td className="p-2 text-sky-400">{p.lower_bound.toFixed(2)}</td>
                        <td className="p-2 text-sky-400">{p.upper_bound.toFixed(2)}</td>
                        <td className="p-2 text-slate-400">{p.interval_width.toFixed(2)}</td>
                        <td className="p-2">
                          {p.is_covered ? (
                            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/20">
                              Đạt chuẩn (Covered)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 text-[10px] font-semibold border border-rose-500/20">
                              Ngoại lai (Outlier)
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

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-slate-200">
                  Báo cáo Phân tích Chuẩn APA 7th &amp; Khuyến nghị Quản trị Rủi ro
                </h4>
                <button
                  onClick={copyToClipboard}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded transition flex items-center gap-1.5 cursor-pointer"
                >
                  {copiedNarrative ? (
                    <>
                      <span className="text-emerald-400 font-medium">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <span>Sao chép Báo cáo</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-slate-300 space-y-2 whitespace-pre-line leading-relaxed font-sans bg-slate-900/50 p-4 rounded-lg border border-slate-800/60">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
