import React, { useState } from 'react';
import { api } from '../api/client';
import { CausalMediationSensitivityResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface CausalMediationSensitivityCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const CausalMediationSensitivityCard: React.FC<CausalMediationSensitivityCardProps> = ({
  surveyId,
  questions
}) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [mediatorQId, setMediatorQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalMediationSensitivityResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleCovariate = (qId: string) => {
    if (selectedCovariates.includes(qId)) {
      setSelectedCovariates(selectedCovariates.filter(id => id !== qId));
    } else {
      setSelectedCovariates([...selectedCovariates, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId) {
      setError('Vui lòng chọn biến can thiệp (Treatment Variable T).');
      return;
    }
    if (!mediatorQId) {
      setError('Vui lòng chọn biến trung gian (Mediator Variable M).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả (Outcome Variable Y).');
      return;
    }
    if (treatmentQId === mediatorQId || treatmentQId === outcomeQId || mediatorQId === outcomeQId) {
      setError('Biến can thiệp, biến trung gian và biến kết quả phải là các biến phân biệt khác nhau.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runCausalMediationSensitivity(surveyId, {
        treatment_question_id: treatmentQId,
        mediator_question_id: mediatorQId,
        outcome_question_id: outcomeQId,
        covariate_question_ids: selectedCovariates,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình trung gian nhân quả.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích trung gian nhân quả.');
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
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-indigo-950 text-indigo-400 border border-indigo-800">
              Causal Mediation
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
              Imai, Keele & Tingley (2010)
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
              Sensitivity Analysis
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">
            Trung Gian Nhân Quả & Kiểm Định Độ Nhạy với Nhiễu Tiềm Ẩn (Causal Mediation & Sensitivity)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Phân rã tác động nhân quả thành hiệu ứng gián tiếp (ACME) và trực tiếp (ADE); kiểm định tính vững chắc khi vi phạm giả định tuần tự bỏ qua (Sequential Ignorability) với tham số tương quan sai số rho = Corr(e_M, e_Y).
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">Tất cả mẫu phản hồi</option>
            <option value="verified_clean">Chỉ mẫu làm sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến can thiệp (Treatment T) <span className="text-rose-400">*</span>
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến can thiệp (0/1 hoặc nhóm) --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến trung gian (Mediator M) <span className="text-rose-400">*</span>
          </label>
          <select
            value={mediatorQId}
            onChange={(e) => setMediatorQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến trung gian định lượng --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến kết quả (Outcome Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến kết quả định lượng --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Covariates Selection */}
      <div className="mb-6 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-300">
            Hiệp biến kiểm soát tiền xử lý (Pre-treatment Covariates X): {selectedCovariates.length} đã chọn
          </span>
          <button
            type="button"
            onClick={() => setSelectedCovariates([])}
            className="text-xs text-slate-400 hover:text-slate-300 transition-colors"
          >
            Bỏ chọn tất cả
          </button>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-32 overflow-y-auto pr-1">
          {numericQuestions
            .filter(q => q.id !== treatmentQId && q.id !== mediatorQId && q.id !== outcomeQId)
            .map(q => {
              const checked = selectedCovariates.includes(q.id);
              return (
                <label
                  key={q.id}
                  className={`flex items-center gap-2 p-2 rounded text-xs cursor-pointer border transition-all ${
                    checked
                      ? 'bg-indigo-950/40 border-indigo-700 text-indigo-200'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleCovariate(q.id)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                  />
                  <span className="truncate" title={q.title}>
                    {q.title}
                  </span>
                </label>
              );
            })}
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium text-xs shadow-lg shadow-indigo-600/30 disabled:opacity-50 transition-all flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang phân tích trung gian & độ nhạy...</span>
            </>
          ) : (
            <span>Phân Tích ACME & Kiểm Định Độ Nhạy (Imai et al. 2010)</span>
          )}
        </button>

        {error && (
          <div className="text-xs text-rose-400 bg-rose-950/40 border border-rose-800 rounded px-3 py-1.5 max-w-md">
            {error}
          </div>
        )}
      </div>

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Diagnostic Metrics */}
          {result.sample_diagnostics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Cỡ mẫu N</div>
                <div className="text-base font-bold text-white mt-0.5">
                  {result.sample_diagnostics.n_total.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Nhóm Can Thiệp (T=1)</div>
                <div className="text-base font-bold text-indigo-400 mt-0.5">
                  {result.sample_diagnostics.n_treated.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Nhóm Đối Chứng (T=0)</div>
                <div className="text-base font-bold text-slate-300 mt-0.5">
                  {result.sample_diagnostics.n_control.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">R² Mô Hình Mediator</div>
                <div className="text-base font-bold text-emerald-400 mt-0.5">
                  {result.sample_diagnostics.r_squared_mediator_model.toFixed(3)}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">R² Mô Hình Outcome</div>
                <div className="text-base font-bold text-cyan-400 mt-0.5">
                  {result.sample_diagnostics.r_squared_outcome_model.toFixed(3)}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Tỷ Lệ Trung Gian</div>
                <div className="text-base font-bold text-amber-400 mt-0.5">
                  {(result.baseline_effects?.proportion_mediated ? result.baseline_effects.proportion_mediated * 100 : 0).toFixed(1)}%
                </div>
              </div>
            </div>
          )}

          {/* Baseline Effect Decomposition Cards */}
          {result.baseline_effects && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-950/70 border border-indigo-900/60 rounded-lg p-4">
                <div className="text-xs text-indigo-300 font-semibold mb-1">Hiệu ứng Gián tiếp (ACME δ)</div>
                <div className="text-2xl font-bold text-indigo-400">
                  {result.baseline_effects.acme.toFixed(4)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  SE: {result.baseline_effects.se_acme.toFixed(4)} · p = {result.baseline_effects.p_value.toFixed(4)}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  95% CI: [{result.baseline_effects.ci_95_lower.toFixed(3)}, {result.baseline_effects.ci_95_upper.toFixed(3)}]
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Hiệu ứng Trực tiếp (ADE ζ)</div>
                <div className="text-2xl font-bold text-emerald-400">
                  {result.baseline_effects.ade.toFixed(4)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  SE: {result.baseline_effects.se_ade.toFixed(4)} · p = {result.baseline_effects.p_ade.toFixed(4)}
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Tổng Hiệu ứng Can Thiệp (Total τ)</div>
                <div className="text-2xl font-bold text-white">
                  {result.baseline_effects.total_effect.toFixed(4)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  τ = ACME (δ) + ADE (ζ)
                </div>
              </div>

              <div className="bg-slate-950/70 border border-rose-950 rounded-lg p-4">
                <div className="text-xs text-rose-300 font-semibold mb-1">Ngưỡng Triệt Tiêu (Critical ρ*)</div>
                <div className="text-2xl font-bold text-rose-400">
                  {result.sensitivity_analysis?.critical_rho_threshold.toFixed(4)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Tương quan sai số tại đó ACME = 0
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  R*²_M × R*²_Y = {result.sensitivity_analysis?.r2_star_product.toFixed(4)}
                </div>
              </div>
            </div>
          )}

          {/* Path Estimates Detail */}
          {result.path_estimates && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-semibold text-indigo-300">Nhánh a (T → M)</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${result.path_estimates.path_a.is_significant ? 'bg-emerald-950 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                    {result.path_estimates.path_a.is_significant ? 'Ý nghĩa (p<0.05)' : 'Không ý nghĩa'}
                  </span>
                </div>
                <div className="text-lg font-bold text-white">
                  {result.path_estimates.path_a.coefficient.toFixed(4)}
                </div>
                <div className="text-[11px] text-slate-400">
                  SE: {result.path_estimates.path_a.se.toFixed(4)} · z = {result.path_estimates.path_a.z_stat.toFixed(2)} · p = {result.path_estimates.path_a.p_value.toFixed(4)}
                </div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-semibold text-emerald-300">Nhánh b (M → Y | T, X)</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${result.path_estimates.path_b.is_significant ? 'bg-emerald-950 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                    {result.path_estimates.path_b.is_significant ? 'Ý nghĩa (p<0.05)' : 'Không ý nghĩa'}
                  </span>
                </div>
                <div className="text-lg font-bold text-white">
                  {result.path_estimates.path_b.coefficient.toFixed(4)}
                </div>
                <div className="text-[11px] text-slate-400">
                  SE: {result.path_estimates.path_b.se.toFixed(4)} · z = {result.path_estimates.path_b.z_stat.toFixed(2)} · p = {result.path_estimates.path_b.p_value.toFixed(4)}
                </div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-semibold text-slate-300">Nhánh c' (T → Y | M, X)</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${result.path_estimates.path_c_prime.is_significant ? 'bg-emerald-950 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                    {result.path_estimates.path_c_prime.is_significant ? 'Ý nghĩa (p<0.05)' : 'Không ý nghĩa'}
                  </span>
                </div>
                <div className="text-lg font-bold text-white">
                  {result.path_estimates.path_c_prime.coefficient.toFixed(4)}
                </div>
                <div className="text-[11px] text-slate-400">
                  SE: {result.path_estimates.path_c_prime.se.toFixed(4)} · z = {result.path_estimates.path_c_prime.z_stat.toFixed(2)} · p = {result.path_estimates.path_c_prime.p_value.toFixed(4)}
                </div>
              </div>
            </div>
          )}

          {/* Robustness Assessment Banner */}
          {result.sensitivity_analysis && (
            <div className={`p-4 rounded-lg border ${
              result.sensitivity_analysis.robustness_level === 'HIGHLY_ROBUST'
                ? 'bg-emerald-950/30 border-emerald-800/80 text-emerald-200'
                : result.sensitivity_analysis.robustness_level === 'MODERATELY_ROBUST'
                ? 'bg-amber-950/30 border-amber-800/80 text-amber-200'
                : 'bg-rose-950/30 border-rose-800/80 text-rose-200'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-bold text-sm">
                  Đánh giá Tính Vững Chắc: {result.sensitivity_analysis.robustness_badge}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-black/40 font-mono">
                  |ρ*| = {Math.abs(result.sensitivity_analysis.critical_rho_threshold).toFixed(3)}
                </span>
              </div>
              <p className="text-xs leading-relaxed opacity-90">
                {result.sensitivity_analysis.robustness_description}
              </p>
            </div>
          )}

          {/* SVG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Sơ Đồ Đường Trung Gian & Đồ Thị Đường Cong Độ Nhạy ACME (Dual-Panel Causal Mediation)
              </h3>
              <div
                className="overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Sensitivity Curve Grid Table */}
          {result.sensitivity_analysis?.sensitivity_curve && (
            <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-slate-300 mb-3 uppercase tracking-wider">
                Bảng Biến Thiên Hiệu Ứng ACME Theo Tương Quan Nhiễu Tiềm Ẩn ρ ∈ [-0.8, +0.8]
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="pb-2 font-medium">Tương quan ρ</th>
                      <th className="pb-2 font-medium text-right">ACME δ(ρ)</th>
                      <th className="pb-2 font-medium text-right">SE</th>
                      <th className="pb-2 font-medium text-right">Khoảng tin cậy 95% CI</th>
                      <th className="pb-2 font-medium text-center">Trạng thái ý nghĩa</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {result.sensitivity_analysis.sensitivity_curve.map((pt, i) => (
                      <tr key={i} className={`hover:bg-slate-800/40 transition-colors ${pt.rho === 0.0 ? 'bg-indigo-950/30 font-semibold' : ''}`}>
                        <td className="py-1.5 font-mono text-[11px] text-slate-300">
                          {pt.rho > 0 ? `+${pt.rho.toFixed(1)}` : pt.rho.toFixed(1)} {pt.rho === 0.0 && '(Baseline)'}
                        </td>
                        <td className={`py-1.5 text-right font-mono text-[11px] ${pt.acme >= 0 ? 'text-indigo-400' : 'text-rose-400'}`}>
                          {pt.acme.toFixed(4)}
                        </td>
                        <td className="py-1.5 text-right font-mono text-[11px] text-slate-400">
                          {pt.se.toFixed(4)}
                        </td>
                        <td className="py-1.5 text-right font-mono text-[11px] text-slate-300">
                          [{pt.ci_lower.toFixed(3)}, {pt.ci_upper.toFixed(3)}]
                        </td>
                        <td className="py-1.5 text-center">
                          {pt.is_zero_in_ci ? (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-rose-950/60 text-rose-400 border border-rose-800/50">
                              Chứa 0 (Mất ý nghĩa)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
                              Khác 0 có ý nghĩa
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
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Tường Thuật Học Thuật Chuẩn APA 7th (Academic APA 7th Narrative)
                </h4>
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium transition-colors"
                >
                  {copiedNarrative ? (
                    <>
                      <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-emerald-400">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                      </svg>
                      <span>Sao chép đoạn trích</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/60 p-3 rounded border border-slate-800">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
