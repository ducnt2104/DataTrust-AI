import React, { useState } from 'react';
import { api } from '../api/client';
import { GEEAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface GEECardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const GEECard: React.FC<GEECardProps> = ({
  surveyId,
  questions
}) => {
  const [clusterQId, setClusterQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [predictorQIds, setPredictorQIds] = useState<string[]>([]);
  const [family, setFamily] = useState<'gaussian' | 'binomial'>('gaussian');
  const [corstr, setCorstr] = useState<'exchangeable' | 'ar1' | 'independent'>('exchangeable');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GEEAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const allQuestions = questions;

  const togglePredictor = (qid: string) => {
    if (predictorQIds.includes(qid)) {
      setPredictorQIds(predictorQIds.filter(id => id !== qid));
    } else {
      setPredictorQIds([...predictorQIds, qid]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!clusterQId) {
      setError('Vui lòng chọn câu hỏi định danh đối tượng / cụm (Cluster ID).');
      return;
    }
    if (!timeQId) {
      setError('Vui lòng chọn câu hỏi mốc thời gian / làn sóng (Time / Wave).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả phụ thuộc (Outcome Y).');
      return;
    }
    if (predictorQIds.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến dự báo (Predictor X).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runGEEAnalysis(surveyId, {
        cluster_question_id: clusterQId,
        time_question_id: timeQId,
        outcome_question_id: outcomeQId,
        predictor_question_ids: predictorQIds.filter(id => id !== outcomeQId),
        family,
        corstr,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình GEE.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích GEE.');
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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-blue-500/10 text-blue-400 font-bold text-sm">
              GEE
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Generalized Estimating Equations (GEE - Mô hình Hồi quy Dân số Trung bình)
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Mô hình hóa tác động dân số trung bình (Population-Averaged Effects) trên dữ liệu bảng khảo sát lặp dọc, khắc phục tương quan nội cụm với sai số chuẩn vững Sandwich - Liang &amp; Zeger (1986), Diggle et al. (2002).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Bộ lọc dữ liệu:</span>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="all">Tất cả phản hồi hoàn thành</option>
            <option value="verified_clean">Chỉ mẫu sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Selectors Grid */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Cluster ID */}
        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            1. Mã Đối Tượng / Cụm (Cluster ID):
          </label>
          <select
            value={clusterQId}
            onChange={(e) => setClusterQId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 p-2.5 focus:border-blue-500 focus:outline-none"
          >
            <option value="">-- Chọn câu hỏi định danh cụm --</option>
            {allQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Time / Wave */}
        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            2. Mốc Thời Gian / Làn Sóng (Time / Wave):
          </label>
          <select
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 p-2.5 focus:border-blue-500 focus:outline-none"
          >
            <option value="">-- Chọn câu hỏi đợt khảo sát --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Y */}
        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            3. Biến Phụ Thuộc (Outcome Y):
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 p-2.5 focus:border-blue-500 focus:outline-none"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Predictors Multi-select */}
      <div className="mt-4 bg-slate-800/40 p-4 rounded-xl border border-slate-700/50">
        <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
          4. Biến Dự Báo (Predictors X):
        </label>
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-1">
          {numericQuestions
            .filter(q => q.id !== outcomeQId && q.id !== clusterQId && q.id !== timeQId)
            .map(q => {
              const isSelected = predictorQIds.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => togglePredictor(q.id)}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                    isSelected
                      ? 'bg-blue-500/20 border-blue-400 text-blue-300 font-semibold shadow-sm'
                      : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-200'
                  }`}
                >
                  {isSelected ? '✓ ' : '+ '}
                  {q.title}
                </button>
              );
            })}
        </div>
      </div>

      {/* GEE Model Specifications */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/60">
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Họ phân phối &amp; Hàm liên kết (Family / Link):
          </label>
          <select
            value={family}
            onChange={(e) => setFamily(e.target.value as any)}
            className="w-full bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-blue-500 focus:outline-none"
          >
            <option value="gaussian">Gaussian (Identity Link - Biến liên tục)</option>
            <option value="binomial">Binomial (Logit Link - Biến nhị phân 0/1)</option>
          </select>
        </div>

        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/60">
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Cấu trúc ma trận tương quan làm việc (Working Correlation):
          </label>
          <select
            value={corstr}
            onChange={(e) => setCorstr(e.target.value as any)}
            className="w-full bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-blue-500 focus:outline-none"
          >
            <option value="exchangeable">Exchangeable (Tương quan nội cụm đồng nhất - Khuyên dùng)</option>
            <option value="ar1">Autoregressive AR(1) (Tương quan suy giảm theo độ trễ thời gian)</option>
            <option value="independent">Independent (Độc lập / Naive GLM)</option>
          </select>
        </div>
      </div>

      {/* Action Button */}
      <div className="mt-5 flex justify-end">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs tracking-wide uppercase transition-all shadow-lg shadow-blue-900/30 disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Đang ước lượng mô hình GEE...
            </>
          ) : (
            'Ước Lượng Mô Hình GEE'
          )}
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mt-5 p-4 bg-red-950/40 border border-red-800/80 rounded-lg text-sm text-red-300 flex items-start gap-2">
          <span className="text-base">⚠️</span>
          <div>
            <div className="font-semibold">Thông báo phân tích:</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && result.status === 'success' && (
        <div className="mt-8 space-y-6">
          {/* Diagnostic KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Sample & Clusters */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                Quy Mô Khảo Sát Lặp
              </span>
              <div className="text-2xl font-black text-white mt-1">
                {result.clusters_count} đối tượng
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Tổng cộng {result.observations_count} lượt quan sát
              </div>
              <div className="text-xs text-blue-400 mt-0.5">
                TB: {(result.observations_count! / result.clusters_count!).toFixed(1)} lần đo / đối tượng
              </div>
            </div>

            {/* Correlation alpha */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-blue-400 tracking-wider">
                Hệ Số Tương Quan (α)
              </span>
              <div className="text-2xl font-black text-blue-300 mt-1">
                α = {result.estimated_correlation_parameter !== undefined && result.estimated_correlation_parameter > 0
                  ? `+${result.estimated_correlation_parameter.toFixed(3)}`
                  : result.estimated_correlation_parameter?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1 uppercase">
                Cấu trúc: {result.working_correlation_structure}
              </div>
              <div className="text-xs text-slate-300 mt-0.5">
                {result.estimated_correlation_parameter && Math.abs(result.estimated_correlation_parameter) > 0.2
                  ? 'Tương quan chuỗi thời gian đáng kể'
                  : 'Tương quan yếu'}
              </div>
            </div>

            {/* QIC */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-emerald-400 tracking-wider">
                Tiêu Chí Thông Tin QIC
              </span>
              <div className="text-2xl font-black text-emerald-300 mt-1">
                {result.qic?.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Pan (2001) Quasi-likelihood criterion
              </div>
              <div className="text-xs text-slate-300 mt-0.5">
                Càng nhỏ biểu thị mô hình càng tối ưu
              </div>
            </div>

            {/* Dispersion */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-amber-400 tracking-wider">
                Hệ Số Tán Xạ (ϕ)
              </span>
              <div className="text-2xl font-black text-amber-300 mt-1">
                ϕ = {result.dispersion_phi?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Phân phối: {result.family}
              </div>
              <div className="text-xs text-teal-400 mt-0.5">
                Sai số chuẩn vững Sandwich Huber-White
              </div>
            </div>
          </div>

          {/* Coefficients Table */}
          {result.coefficients && result.coefficients.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
              <div className="p-4 border-b border-slate-800 font-bold text-xs text-slate-300 uppercase tracking-wider">
                Bảng Hệ Số Hồi Quy GEE (Dân Số Trung Bình) &amp; Sai Số Chuẩn Vững Sandwich
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-800/70 text-slate-400 border-b border-slate-700/60 font-semibold">
                      <th className="py-2.5 px-4">Biến dự báo (Term)</th>
                      <th className="py-2.5 px-4">Hệ số β</th>
                      <th className="py-2.5 px-4">Robust SE (Sandwich)</th>
                      <th className="py-2.5 px-4">Naive SE</th>
                      <th className="py-2.5 px-4">Thống kê z</th>
                      <th className="py-2.5 px-4">p-value</th>
                      <th className="py-2.5 px-4">Khoảng tin cậy 95% (Sandwich)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.coefficients.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-4 font-semibold text-white">
                          {item.term}
                        </td>
                        <td className="py-2.5 px-4 font-black text-blue-300">
                          {item.estimate > 0 ? `+${item.estimate.toFixed(3)}` : item.estimate.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-4 font-mono text-emerald-400">{item.robust_se.toFixed(4)}</td>
                        <td className="py-2.5 px-4 font-mono text-slate-400">{item.naive_se.toFixed(4)}</td>
                        <td className="py-2.5 px-4 font-mono">{item.z_statistic.toFixed(2)}</td>
                        <td className="py-2.5 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              item.is_significant
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {item.p_value < 0.001 ? '< .001' : item.p_value.toFixed(3)}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 font-mono text-slate-400">
                          [{item.ci_95_lower.toFixed(3)}, {item.ci_95_upper.toFixed(3)}]
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Vector SVG Dual-Panel Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-inner">
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                Biểu đồ Không gian Ma trận Tương quan &amp; Đồ thị Rừng Hệ số GEE
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Edition Academic Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700/60 relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">
                  Diễn giải Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="text-xs px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
                >
                  {copiedNarrative ? '✓ Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed italic whitespace-pre-line">
                {result.apa_narrative}
              </p>
            </div>
          )}

          {/* Methodological Reference Note */}
          <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="font-semibold text-slate-300">Tài liệu tham khảo phương pháp:</div>
            <ul className="list-disc list-inside space-y-0.5 text-slate-400">
              <li>Liang, K. Y., &amp; Zeger, S. L. (1986). Longitudinal data analysis using generalized linear models. <em>Biometrika</em>, 73(1), 13-22.</li>
              <li>Diggle, P. J., Heagerty, P., Liang, K. Y., &amp; Zeger, S. L. (2002). <em>Analysis of Longitudinal Data</em> (2nd ed.). Oxford University Press.</li>
              <li>Pan, W. (2001). Akaike's information criterion in generalized estimating equations. <em>Biometrics</em>, 57(1), 120-125.</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
