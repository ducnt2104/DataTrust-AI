import React, { useState } from 'react';
import {
  ShieldAlert,
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
  Scale,
  Maximize2
} from 'lucide-react';
import { api } from '../api/client';
import {
  ConformalCausalResult,
  ConformalCausalRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const ConformalCausalCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [calibrationRatio, setCalibrationRatio] = useState<number>(0.4);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConformalCausalResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'ite_sample' | 'subgroups' | 'methodology'>('ite_sample');

  const handleToggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!treatmentQId || !outcomeQId) {
      setError('Vui lòng chọn đầy đủ Biến Can thiệp (D) và Biến Kết quả (Y).');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: ConformalCausalRequest = {
      treatment_question_id: treatmentQId,
      outcome_question_id: outcomeQId,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      alpha: alpha,
      calibration_ratio: calibrationRatio,
      scope: scope
    };

    try {
      const res = await api.runConformalCausalInference(surveyId, payload);
      if (res.status === 'success') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể thực hiện Conformal Causal Inference.');
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
          <div className="p-2.5 bg-gradient-to-br from-teal-500 to-emerald-600 text-white rounded-lg shadow-sm">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Suy luận Nhân quả Conformal & Dải Dự báo Phản thực tế (Conformal Causal Inference)
              </h3>
              <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 rounded-full">
                Chernozhukov (2021) • Lei & Candès (2021)
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Dải dự báo khoảng tin cậy mẫu hữu hạn (finite-sample) phi phân phối (distribution-free) cho kết quả phản thực tế Y(0), Y(1) và hiệu ứng cá thể ITE với bảo đảm xác suất bao phủ 1-α
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Can thiệp (Treatment D: 0/1) *
              </label>
              <select
                value={treatmentQId}
                onChange={e => setTreatmentQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
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
                Biến Kết quả (Outcome Y) *
              </label>
              <select
                value={outcomeQId}
                onChange={e => setOutcomeQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">-- Chọn biến Outcome Y --</option>
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
              Biến Đặc trưng Kiểm soát X (Covariates cho Mô hình Tiềm năng & Propensity Weighting)
            </label>
            <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
              {questions
                .filter(q => q.id !== treatmentQId && q.id !== outcomeQId)
                .map(q => {
                  const isChecked = selectedCovariates.includes(q.id);
                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => handleToggleCovariate(q.id)}
                      className={`text-xs px-2.5 py-1 rounded-md border transition-all ${
                        isChecked
                          ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700 font-medium'
                          : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-300'
                      }`}
                    >
                      {isChecked ? '✓ ' : '+ '}
                      {q.title}
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Hyperparameters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-200 dark:border-slate-700/60">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Mức sai số danh nghĩa (Mức Alpha α)
              </label>
              <select
                value={alpha}
                onChange={e => setAlpha(parseFloat(e.target.value))}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
              >
                <option value={0.10}>α = 0.10 (Bao phủ danh nghĩa 90%)</option>
                <option value={0.05}>α = 0.05 (Bao phủ danh nghĩa 95%)</option>
                <option value={0.01}>α = 0.01 (Bao phủ danh nghĩa 99%)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Tỷ lệ tập Hiệu chuẩn (Calibration Split): {Math.round(calibrationRatio * 100)}%
                </label>
              </div>
              <input
                type="range"
                min="0.2"
                max="0.5"
                step="0.05"
                value={calibrationRatio}
                onChange={e => setCalibrationRatio(parseFloat(e.target.value))}
                className="w-full accent-emerald-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Phạm vi dữ liệu phản hồi (Scope)
              </label>
              <select
                value={scope}
                onChange={e => setScope(e.target.value as any)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
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
              className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  <span>Đang tính toán Dải Conformal Causal...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Thực thi Conformal Causal Inference</span>
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
                Bao phủ Danh nghĩa
              </span>
              <div className="text-xl font-bold text-teal-600 dark:text-teal-400">
                {result.nominal_coverage !== undefined ? `${(result.nominal_coverage * 100).toFixed(0)}%` : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Mục tiêu 1 - α</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Bao phủ Thực nghiệm
              </span>
              <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                {result.empirical_calibration_coverage !== undefined ? `${(result.empirical_calibration_coverage * 100).toFixed(1)}%` : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Tập kiểm định calibration</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Conformal ATE
              </span>
              <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                {result.treatment_effect_summary?.ate_conformal !== undefined ? `${result.treatment_effect_summary.ate_conformal > 0 ? '+' : ''}${result.treatment_effect_summary.ate_conformal.toFixed(4)}` : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Hiệu ứng trung bình</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Độ rộng Dải ITE
              </span>
              <div className="text-xl font-bold text-slate-800 dark:text-slate-200">
                {result.treatment_effect_summary?.avg_width_ite !== undefined ? result.treatment_effect_summary.avg_width_ite.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Độ bất định cá thể</span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Ý nghĩa Thống kê ITE
              </span>
              <div className="text-base font-bold text-emerald-600 dark:text-emerald-400">
                {result.treatment_effect_summary?.sig_positive_ite_pct !== undefined ? `${result.treatment_effect_summary.sig_positive_ite_pct.toFixed(1)}%` : '—'}
              </div>
              <span className="text-[10px] text-slate-400">Quan sát ITE &gt; 0</span>
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
                onClick={() => setActiveTab('ite_sample')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'ite_sample'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Mẫu Khoảng Tin cậy Cá thể Conformal ITE [τ_L, τ_U]
              </button>
              <button
                onClick={() => setActiveTab('subgroups')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'subgroups'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Ngưỡng Cắt Nonconformity & Phân chia Tập dữ liệu
              </button>
              <button
                onClick={() => setActiveTab('methodology')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'methodology'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Cơ sở Khoa học & Bảo đảm Mẫu hữu hạn
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'ite_sample' && result.sample_ite_points && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400">
                    <th className="p-2.5 font-semibold">Quan sát</th>
                    <th className="p-2.5 font-semibold">Nhóm Can thiệp (D)</th>
                    <th className="p-2.5 font-semibold">Kết quả Thực tế (Y)</th>
                    <th className="p-2.5 font-semibold">Dự báo ITE</th>
                    <th className="p-2.5 font-semibold">Khoảng Conformal [τ_L, τ_U]</th>
                    <th className="p-2.5 font-semibold">Độ rộng dải</th>
                    <th className="p-2.5 font-semibold text-center">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {result.sample_ite_points.map((pt) => (
                    <tr key={pt.observation_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="p-2.5 font-mono font-medium">#{pt.observation_id}</td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          pt.treatment === 1
                            ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                        }`}>
                          {pt.treatment === 1 ? 'Treated (D=1)' : 'Control (D=0)'}
                        </span>
                      </td>
                      <td className="p-2.5 font-mono">{pt.factual_outcome.toFixed(4)}</td>
                      <td className="p-2.5 font-mono font-bold text-teal-600 dark:text-teal-400">
                        {pt.predicted_ite > 0 ? '+' : ''}{pt.predicted_ite.toFixed(4)}
                      </td>
                      <td className="p-2.5 font-mono">
                        [{pt.ite_lower_bound.toFixed(4)}, {pt.ite_upper_bound.toFixed(4)}]
                      </td>
                      <td className="p-2.5 font-mono">{pt.band_width.toFixed(4)}</td>
                      <td className="p-2.5 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                          pt.significant
                            ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                        }`}>
                          {pt.significant ? 'Có ý nghĩa (Tách biệt 0)' : 'Chứa 0'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'subgroups' && result.subgroup_counts && result.conformal_cutoffs && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-teal-600 dark:text-teal-400 font-semibold text-xs">
                  <Layers className="w-4 h-4" />
                  <span>Phân chia Mẫu Dữ liệu (Sample Splits)</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Tổng mẫu hợp lệ (N):</span>
                    <span className="font-mono font-semibold">{result.sample_size}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Tập Huấn luyện Mô hình Cơ sở (Proper Training):</span>
                    <span className="font-mono font-semibold">{result.subgroup_counts.training_set}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Tập Hiệu chuẩn Conformal (Calibration Set):</span>
                    <span className="font-mono font-semibold">{result.subgroup_counts.calibration_set}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Số quan sát Nhóm Can thiệp (D=1):</span>
                    <span className="font-mono font-semibold">{result.subgroup_counts.treated}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Số quan sát Nhóm Đối chứng (D=0):</span>
                    <span className="font-mono font-semibold">{result.subgroup_counts.control}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 font-semibold text-xs">
                  <Maximize2 className="w-4 h-4" />
                  <span>Ngưỡng Cắt Điểm Nonconformity (Conformal Cutoffs)</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Ngưỡng sai số Conformal cho Y(0) (q̂₀):</span>
                    <span className="font-mono font-semibold">{result.conformal_cutoffs.cutoff_q0.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Ngưỡng sai số Conformal cho Y(1) (q̂₁):</span>
                    <span className="font-mono font-semibold">{result.conformal_cutoffs.cutoff_q1.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Tỷ lệ bao phủ kiểm định Đối chứng:</span>
                    <span className="font-mono font-semibold">{(result.conformal_cutoffs.coverage_control * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Tỷ lệ bao phủ kiểm định Can thiệp:</span>
                    <span className="font-mono font-semibold">{(result.conformal_cutoffs.coverage_treated * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'methodology' && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
              <div className="flex items-center space-x-2 font-semibold text-xs text-slate-800 dark:text-slate-200">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Bảo đảm Mẫu hữu hạn & Trọng số Dịch chuyển Phân phối (Covariate Shift Weighting)</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Các phương pháp suy luận nhân quả truyền thống (OLS, Matching, G-Computation) phụ thuộc vào định lý giới hạn trung tâm tiệm cận (Asymptotic CLT) 
                hoặc giả định sai số chuẩn Gauss, thường bị sai lệch nghiêm trọng khi cỡ mẫu nhỏ hoặc phân phối có đuôi nặng.
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Theo định lý của <strong>Chernozhukov, Wüthrich, & Zhu (2021 JASA)</strong> và <strong>Lei & Candès (2021 JRSS-B)</strong>, 
                phương pháp Conformal Causal Inference đạt xác suất bao phủ chính xác trong mẫu hữu hạn:
                <code className="mx-1 px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">
                  P(Y_i(d) ∈ Ĉ_d(X_i)) ≥ 1 - α
                </code>
                mà không cần bất kỳ giả định tham số nào về phân phối của Y hay cấu trúc mô hình máy học. 
                Sự thiên lệch gán ngẫu nhiên (Covariate Shift) được xử lý thông qua trọng số tỷ số hợp lý:
                <code className="mx-1 px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">
                  w_i(x) = e(x) / (1 - e(x))
                </code>
                cho phép chuyển giao phân vị không chệch giữa nhóm đối chứng và can thiệp.
              </p>
            </div>
          )}

          {/* APA Narrative Block */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Tường thuật Học thuật Chuẩn APA 7th Edition (DataTrust)</span>
                </span>
                <button
                  onClick={copyNarrative}
                  className="flex items-center space-x-1 px-2.5 py-1 text-xs text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/60 rounded-md transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép APA'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed italic border-l-2 border-emerald-500 pl-3">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default ConformalCausalCard;
