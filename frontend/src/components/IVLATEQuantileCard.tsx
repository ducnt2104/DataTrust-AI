import React, { useState } from 'react';
import {
  GitFork,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  ShieldCheck,
  Sliders,
  Scale
} from 'lucide-react';
import { api } from '../api/client';
import {
  IVLATEQuantileResult,
  IVLATEQuantileRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const IVLATEQuantileCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [instrumentQId, setInstrumentQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [numQuantiles, setNumQuantiles] = useState<number>(19);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IVLATEQuantileResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'quantiles' | 'welfare' | 'monotonicity'>('quantiles');

  const handleToggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!outcomeQId || !treatmentQId || !instrumentQId) {
      setError('Vui lòng chọn đầy đủ Biến Kết quả (Y), Biến Can thiệp (D), và Biến Công cụ (Z).');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: IVLATEQuantileRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      instrument_question_id: instrumentQId,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      num_quantiles: numQuantiles,
      scope: scope
    };

    try {
      const res = await api.runIVLATEQuantileDecomposition(surveyId, payload);
      if (res.status === 'success') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể tính toán IV-LATE Quantile Decomposition.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích.');
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
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 mb-8 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-lg shadow-sm">
            <GitFork className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Phân rã Phân vị Hiệu ứng Cục bộ Biến công cụ (IV-LATE Quantile Decomposition)
              </h3>
              <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 rounded-full">
                Abadie (2002) • Frölich & Melly (2013)
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Ước lượng phi tham số hiệu ứng can thiệp trên phân phối nhóm tuân thủ (QTE-C) với trọng số Abadie Kappa, kiểm định đơn điệu Kitagawa và đánh giá phúc lợi phân phối
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowConfig(!showConfig)}
          className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title={showConfig ? 'Thu gọn cài đặt' : 'Mở rộng cài đặt'}
        >
          {showConfig ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {/* Configuration Form */}
      {showConfig && (
        <div className="bg-slate-50 dark:bg-slate-800/40 rounded-lg p-4 border border-slate-200 dark:border-slate-800 mb-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Kết quả (Outcome Y) *
              </label>
              <select
                value={outcomeQId}
                onChange={e => setOutcomeQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- Chọn biến Outcome Y --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Can thiệp (Treatment D: 0/1) *
              </label>
              <select
                value={treatmentQId}
                onChange={e => setTreatmentQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- Chọn biến can thiệp D --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Công cụ Ngoại sinh (Instrument Z: 0/1) *
              </label>
              <select
                value={instrumentQId}
                onChange={e => setInstrumentQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- Chọn biến công cụ Z --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Covariates multi-select */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Biến Kiểm soát Điều kiện Propensity P(Z=1|X) (Tùy chọn)
            </label>
            <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
              {questions
                .filter(q => q.id !== outcomeQId && q.id !== treatmentQId && q.id !== instrumentQId)
                .map(q => {
                  const isChecked = selectedCovariates.includes(q.id);
                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => handleToggleCovariate(q.id)}
                      className={`text-xs px-2.5 py-1 rounded-md border transition-all ${
                        isChecked
                          ? 'bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border-indigo-300 dark:border-indigo-700 font-medium'
                          : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-300'
                      }`}
                    >
                      {isChecked ? '✓ ' : '+ '}
                      {q.title}
                    </button>
                  );
                })}
              {questions.length <= 3 && (
                <span className="text-xs text-slate-400 italic">Cần ít nhất 4 biến trong khảo sát để chọn thêm biến kiểm soát.</span>
              )}
            </div>
          </div>

          {/* Hyperparameters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-200 dark:border-slate-700/60">
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Số điểm phân vị ước lượng (Grid Quantiles τ): {numQuantiles}
                </label>
                <span className="text-xs text-slate-400">τ ∈ [0.05, 0.95]</span>
              </div>
              <input
                type="range"
                min="5"
                max="35"
                step="2"
                value={numQuantiles}
                onChange={e => setNumQuantiles(parseInt(e.target.value, 10))}
                className="w-full accent-indigo-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Phạm vi dữ liệu phản hồi (Scope)
              </label>
              <select
                value={scope}
                onChange={e => setScope(e.target.value as any)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-indigo-500"
              >
                <option value="all">Tất cả phản hồi hợp lệ (Toàn bộ mẫu)</option>
                <option value="verified_clean">Chỉ phản hồi đã xác minh sạch (DataTrust Verified)</option>
              </select>
            </div>
          </div>

          {/* Action button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  <span>Đang tính toán IV-LATE Quantiles...</span>
                </>
              ) : (
                <>
                  <GitFork className="w-4 h-4" />
                  <span>Thực thi Phân rã IV-LATE Quantile</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">{error}</div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Tỷ trọng Compliers P(C)
              </span>
              <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                {result.complier_share !== undefined ? `${(result.complier_share * 100).toFixed(1)}%` : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Trọng số Abadie Kappa</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Mean LATE (Wald)
              </span>
              <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                {result.mean_late !== undefined ? `${result.mean_late > 0 ? '+' : ''}${result.mean_late.toFixed(4)}` : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Hiệu ứng trung bình</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Median QTE-C (τ = 0.50)
              </span>
              <div className="text-xl font-bold text-purple-600 dark:text-purple-400">
                {result.median_qte_complier !== undefined ? `${result.median_qte_complier > 0 ? '+' : ''}${result.median_qte_complier.toFixed(4)}` : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Hiệu ứng trung vị complier</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Kiểm định Kitagawa (2015)
              </span>
              <div className={`text-base font-bold flex items-center space-x-1 ${
                result.monotonicity_test?.passed
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-amber-600 dark:text-amber-400'
              }`}>
                {result.monotonicity_test?.passed ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-1 inline" />
                    <span>Hợp lệ (No Defiers)</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 mr-1 inline" />
                    <span>Cảnh báo Defiers</span>
                  </>
                )}
              </div>
              <span className="text-[10px] text-slate-400">
                Min Δf: {result.monotonicity_test?.min_density_difference.toFixed(4)}
              </span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Phúc lợi Phân phối
              </span>
              <div className="text-base font-bold text-blue-600 dark:text-blue-400">
                {result.complier_inequality?.first_order_stochastic_dominance ? 'FSD Thống trị' : 'Không thuần nhất'}
              </div>
              <span className="text-[10px] text-slate-400">
                ΔGini: {result.complier_inequality?.delta_gini_c !== undefined ? result.complier_inequality.delta_gini_c.toFixed(4) : '—'}
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/30 rounded-xl border border-slate-200 dark:border-slate-700 overflow-x-auto">
              <div
                className="w-full flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Tab Navigation */}
          <div className="border-b border-slate-200 dark:border-slate-800">
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveTab('quantiles')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'quantiles'
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Quỹ đạo Hiệu ứng Phân vị QTE-C (τ)
              </button>
              <button
                onClick={() => setActiveTab('welfare')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'welfare'
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Phân tích Bất bình đẳng & Trội Ngẫu nhiên (FSD)
              </button>
              <button
                onClick={() => setActiveTab('monotonicity')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'monotonicity'
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Kiểm định Đơn điệu Kitagawa & Chuẩn đoán Công cụ
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'quantiles' && result.quantile_curve && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400">
                    <th className="p-2.5 font-semibold">Phân vị (τ)</th>
                    <th className="p-2.5 font-semibold">Q₁ Tuân thủ (Can thiệp)</th>
                    <th className="p-2.5 font-semibold">Q₀ Tuân thủ (Đối chứng)</th>
                    <th className="p-2.5 font-semibold text-right">QTE-C(τ) = Q₁ - Q₀</th>
                    <th className="p-2.5 font-semibold text-center">Xu hướng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {result.quantile_curve.map((pt, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="p-2.5 font-mono font-medium">τ = {pt.tau.toFixed(2)}</td>
                      <td className="p-2.5 font-mono">{pt.q_treated_complier.toFixed(4)}</td>
                      <td className="p-2.5 font-mono">{pt.q_control_complier.toFixed(4)}</td>
                      <td className={`p-2.5 font-mono font-bold text-right ${
                        pt.qte_complier > 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : pt.qte_complier < 0
                          ? 'text-rose-600 dark:text-rose-400'
                          : 'text-slate-600'
                      }`}>
                        {pt.qte_complier > 0 ? '+' : ''}{pt.qte_complier.toFixed(4)}
                      </td>
                      <td className="p-2.5 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                          pt.qte_complier > (result.mean_late || 0)
                            ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300'
                            : 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300'
                        }`}>
                          {pt.qte_complier > (result.mean_late || 0) ? 'Trên TB' : 'Dưới TB'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'welfare' && result.complier_inequality && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-indigo-600 dark:text-indigo-400 font-semibold text-xs">
                  <Scale className="w-4 h-4" />
                  <span>Chỉ số Bất bình đẳng Gini Nhóm Tuân thủ</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Gini Đối chứng Complier:</span>
                    <span className="font-mono font-semibold">{result.complier_inequality.gini_control_c.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Gini Can thiệp Complier:</span>
                    <span className="font-mono font-semibold">{result.complier_inequality.gini_treated_c.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 font-bold">
                    <span className="text-slate-700 dark:text-slate-300">Biến thiên ΔGini:</span>
                    <span className={`font-mono ${
                      result.complier_inequality.delta_gini_c <= 0 ? 'text-emerald-600' : 'text-rose-600'
                    }`}>
                      {result.complier_inequality.delta_gini_c > 0 ? '+' : ''}{result.complier_inequality.delta_gini_c.toFixed(4)}
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 mt-2">
                  {result.complier_inequality.delta_gini_c <= 0
                    ? '✓ Chính sách giúp giảm bất bình đẳng phân phối nội bộ nhóm tuân thủ.'
                    : '⚠ Chính sách làm giãn cách phân phối và tăng phân hóa nội bộ nhóm tuân thủ.'}
                </p>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-purple-600 dark:text-purple-400 font-semibold text-xs">
                  <Sliders className="w-4 h-4" />
                  <span>Khoảng Tứ phân vị (IQR) & Trội Ngẫu nhiên (FSD)</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">IQR Đối chứng Complier:</span>
                    <span className="font-mono font-semibold">{result.complier_inequality.iqr_control_c.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">IQR Can thiệp Complier:</span>
                    <span className="font-mono font-semibold">{result.complier_inequality.iqr_treated_c.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 font-bold">
                    <span className="text-slate-700 dark:text-slate-300">Biến thiên ΔIQR:</span>
                    <span className={`font-mono ${
                      result.complier_inequality.delta_iqr_c <= 0 ? 'text-emerald-600' : 'text-rose-600'
                    }`}>
                      {result.complier_inequality.delta_iqr_c > 0 ? '+' : ''}{result.complier_inequality.delta_iqr_c.toFixed(4)}
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 mt-2">
                  {result.complier_inequality.first_order_stochastic_dominance
                    ? '★ First-Order Stochastic Dominance: Mọi phân vị của nhóm can thiệp đều vượt trội hơn nhóm đối chứng.'
                    : 'Hiệu ứng can thiệp biến thiên theo phân vị và không thuần nhất hoàn toàn.'}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'monotonicity' && result.monotonicity_test && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
              <div className="flex items-center space-x-2 font-semibold text-xs text-slate-800 dark:text-slate-200">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Kiểm định Tính Đơn điệu Không Defiers (Kitagawa 2015 Econometrica)</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Giả định cơ bản của LATE là tính đơn điệu (Monotonicity: D(1) ≥ D(0)), loại trừ sự tồn tại của nhóm chống đối (Defiers). 
                Kiểm định Kitagawa kiểm tra tính không âm của sai phân mật độ chung: 
                <code className="mx-1 px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">Δf₁(y) = f(y, D=1|Z=1) - f(y, D=1|Z=0) ≥ 0</code>
                và 
                <code className="mx-1 px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">Δf₀(y) = f(y, D=0|Z=0) - f(y, D=0|Z=1) ≥ 0</code>.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Trạng thái Kiểm định</span>
                  <span className={`text-xs font-bold ${
                    result.monotonicity_test.passed ? 'text-emerald-600' : 'text-amber-600'
                  }`}>
                    {result.monotonicity_test.passed ? 'Thỏa mãn Giả định Đơn điệu' : 'Có dấu hiệu Vi phạm'}
                  </span>
                </div>
                <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Mức vi phạm Mật độ Tối thiểu</span>
                  <span className="text-xs font-mono font-bold">
                    {result.monotonicity_test.min_density_difference.toFixed(6)}
                  </span>
                </div>
                <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Sự hiện diện của Defiers</span>
                  <span className={`text-xs font-bold ${
                    result.monotonicity_test.defiers_detected ? 'text-rose-600' : 'text-emerald-600'
                  }`}>
                    {result.monotonicity_test.defiers_detected ? 'Phát hiện Defiers' : 'Không phát hiện Defiers'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* APA Narrative Block */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                  <span>Tường thuật Học thuật Chuẩn APA 7th Edition (DataTrust)</span>
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center space-x-1 px-2.5 py-1 text-xs text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/60 rounded-md transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed italic border-l-2 border-indigo-500 pl-3">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default IVLATEQuantileCard;
