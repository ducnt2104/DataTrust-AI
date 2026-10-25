import React, { useState } from 'react';
import { api } from '../api/client';
import { SpatialEconometricsResult, SpatialEconometricsRequest } from '../types/survey';

interface QuestionOption {
  id: string;
  title: string;
  question_type: string;
}

interface Props {
  surveyId: string;
  questions: QuestionOption[];
}

export const SpatialEconometricsCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [covariateQIds, setCovariateQIds] = useState<string[]>([]);
  const [weightsType, setWeightsType] = useState<'inverse_distance' | 'knn'>('inverse_distance');
  const [knnK, setKnnK] = useState<number>(5);
  const [distancePower, setDistancePower] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SpatialEconometricsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'likert'
  );

  const toggleCovariate = (id: string) => {
    if (covariateQIds.includes(id)) {
      setCovariateQIds(covariateQIds.filter((x) => x !== id));
    } else {
      setCovariateQIds([...covariateQIds, id]);
    }
  };

  const handleRun = async () => {
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả cần kiểm định không gian (Outcome Y).');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const payload: SpatialEconometricsRequest = {
        outcome_question_id: outcomeQId,
        covariate_question_ids: covariateQIds,
        weights_type: weightsType,
        knn_k: knnK,
        distance_power: distancePower,
        scope,
      };
      const res = await api.runSpatialEconometricsAnalysis(surveyId, payload);
      if (res.status === 'error' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không thể tính toán mô hình kinh tế lượng không gian.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích không gian.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-purple-500/10 text-purple-400 rounded-lg text-lg font-bold">
              🗺️ SAR
            </span>
            <h3 className="text-xl font-bold text-slate-100">
              Spatial Econometrics &amp; Moran's I Autoregressive Engine
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Kiểm định tự tương quan không gian Moran's I &amp; Ước lượng Mô hình Tự hồi quy Không gian (SAR) phân rã hiệu ứng lan tỏa (Spatial Spillovers) theo Luc Anselin (1988) &amp; James LeSage (2009).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2 outline-none focus:border-purple-500"
          >
            <option value="all">Toàn bộ phản hồi (Tất cả)</option>
            <option value="verified_clean">Chỉ dữ liệu đã xác minh sạch</option>
          </select>
          <button
            onClick={handleRun}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow transition-all flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Đang phân tích không gian...</span>
              </>
            ) : (
              <>
                <span>▶ Kiểm Định Không Gian &amp; Chạy SAR</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Inputs Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-5 bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            1. Biến Kết quả (Outcome Variable Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-purple-500"
          >
            <option value="">-- Chọn biến phụ thuộc --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            2. Loại Ma trận Trọng số Không gian (W Matrix)
          </label>
          <select
            value={weightsType}
            onChange={(e) => setWeightsType(e.target.value as any)}
            className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-purple-500"
          >
            <option value="inverse_distance">Nghịch đảo Khoảng cách Trắc địa (Inverse Distance 1/d^α)</option>
            <option value="knn">K Láng giềng Gần nhất (K-Nearest Neighbors)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            {weightsType === 'knn' ? '3. Số láng giềng k' : '3. Bậc khoảng cách α (Distance Power)'}
          </label>
          {weightsType === 'knn' ? (
            <input
              type="number"
              min={2}
              max={20}
              value={knnK}
              onChange={(e) => setKnnK(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-purple-500"
            />
          ) : (
            <input
              type="number"
              step="0.5"
              min={0.5}
              max={3.0}
              value={distancePower}
              onChange={(e) => setDistancePower(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg p-2.5 outline-none focus:border-purple-500"
            />
          )}
        </div>

        {/* Covariates Multiselect */}
        <div className="md:col-span-3 mt-2">
          <label className="block text-xs font-semibold text-slate-300 mb-2">
            4. Các biến Giải thích Độc lập (Covariates X) — Tính toán hiệu ứng trực tiếp &amp; lan tỏa:
          </label>
          <div className="flex flex-wrap gap-2">
            {numericQuestions
              .filter((q) => q.id !== outcomeQId)
              .map((q) => {
                const isSelected = covariateQIds.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleCovariate(q.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                      isSelected
                        ? 'bg-purple-600/30 text-purple-300 border-purple-500 shadow-sm'
                        : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    {isSelected ? '✓ ' : '+ '} {q.title}
                  </button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-lg text-xs flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.morans_i && result.spatial_lag_model && (
        <div className="space-y-6 mt-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Moran's I */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Chỉ số Moran's I
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-purple-400">
                  {result.morans_i.morans_i.toFixed(3)}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    result.morans_i.is_significant
                      ? 'bg-purple-500/20 text-purple-300'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  p = {result.morans_i.p_value.toFixed(4)}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                z = {result.morans_i.z_score.toFixed(2)} | {result.morans_i.classification}
              </p>
            </div>

            {/* Spatial Autoregressive rho */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Hệ số Lan tỏa Không gian ρ (SAR)
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-cyan-400">
                  {result.spatial_lag_model.rho.toFixed(3)}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    result.spatial_lag_model.is_rho_significant
                      ? 'bg-cyan-500/20 text-cyan-300'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  SE = {result.spatial_lag_model.rho_standard_error.toFixed(3)}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                R² = {result.spatial_lag_model.r_squared.toFixed(3)} | p = {result.spatial_lag_model.rho_p_value.toFixed(4)}
              </p>
            </div>

            {/* LM Diagnostics Recommendation */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Mô hình Khuyến nghị (Anselin LM)
              </span>
              <div className="mt-1">
                <span className="text-sm font-bold text-amber-400 block truncate">
                  {result.lm_diagnostics?.recommended_model || 'SAR'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                LM-Lag: {result.lm_diagnostics?.lm_lag_stat.toFixed(1)} | LM-Error: {result.lm_diagnostics?.lm_error_stat.toFixed(1)}
              </p>
            </div>

            {/* Moran Quadrants */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Phân bổ Góc phần tư Không gian
              </span>
              <div className="mt-2 grid grid-cols-2 gap-1 text-[11px]">
                <div className="text-emerald-400">
                  HH: {result.morans_i.quadrants.high_high}
                </div>
                <div className="text-sky-400">
                  LL: {result.morans_i.quadrants.low_low}
                </div>
                <div className="text-rose-400">
                  HL: {result.morans_i.quadrants.high_low}
                </div>
                <div className="text-amber-400">
                  LH: {result.morans_i.quadrants.low_high}
                </div>
              </div>
            </div>
          </div>

          {/* SVG Vector Chart Display */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-hidden shadow-inner">
              <div
                className="w-full flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Impact Decomposition Table */}
          {result.spatial_lag_model.impact_decomposition.length > 0 && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">
                Bảng Phân rã Hiệu ứng Tác động LeSage &amp; Pace (2009)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[10px]">
                    <tr>
                      <th className="px-3 py-2">Biến Giải thích</th>
                      <th className="px-3 py-2 text-right">Hệ số β</th>
                      <th className="px-3 py-2 text-right text-sky-400">Tác động Trực tiếp (Direct)</th>
                      <th className="px-3 py-2 text-right text-purple-400">Lan tỏa Không gian (Spillover)</th>
                      <th className="px-3 py-2 text-right text-slate-100">Tổng Tác động (Total)</th>
                      <th className="px-3 py-2 text-right">Tỷ lệ Lan tỏa %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {result.spatial_lag_model.impact_decomposition.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50">
                        <td className="px-3 py-2 font-medium text-slate-200">{row.variable}</td>
                        <td className="px-3 py-2 text-right font-mono">{row.coefficient.toFixed(4)}</td>
                        <td className="px-3 py-2 text-right font-mono text-sky-400">{row.direct_impact.toFixed(4)}</td>
                        <td className="px-3 py-2 text-right font-mono text-purple-400">{row.indirect_spillover_impact.toFixed(4)}</td>
                        <td className="px-3 py-2 text-right font-mono font-bold text-slate-100">{row.total_impact.toFixed(4)}</td>
                        <td className="px-3 py-2 text-right font-mono text-purple-300">{(row.spillover_ratio * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyNarrative}
                  className="px-2.5 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
                >
                  {copied ? '✓ Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/60 p-3 rounded border border-slate-800/80">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
