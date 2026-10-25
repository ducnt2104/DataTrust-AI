import React, { useState } from 'react';
import {
  MapPin,
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
  Compass,
  Radio
} from 'lucide-react';
import { api } from '../api/client';
import {
  SpatialDIDResult,
  SpatialDIDRequest
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{
    id: string;
    title: string;
    question_type: string;
  }>;
}

export const SpatialDIDCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [latQId, setLatQId] = useState<string>('');
  const [lonQId, setLonQId] = useState<string>('');
  const [timeQId, setTimeQId] = useState<string>('');
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [weightType, setWeightType] = useState<'inverse_distance' | 'knn'>('inverse_distance');
  const [knnK, setKnnK] = useState<number>(5);
  const [distancePower, setDistancePower] = useState<number>(1.0);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SpatialDIDResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'effects' | 'spatial_weights' | 'sutva'>('effects');

  const handleToggleCovariate = (qid: string) => {
    setSelectedCovariates(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const handleRun = async () => {
    if (!treatmentQId || !outcomeQId || !latQId || !lonQId) {
      setError('Vui lòng chọn đầy đủ Biến Can thiệp (D), Biến Kết quả (Y), Vĩ độ (Latitude), và Kinh độ (Longitude).');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: SpatialDIDRequest = {
      treatment_question_id: treatmentQId,
      outcome_question_id: outcomeQId,
      lat_field: latQId,
      lon_field: lonQId,
      time_question_id: timeQId || undefined,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      weight_type: weightType,
      knn_k: knnK,
      power: distancePower,
      scope: scope
    };

    try {
      const res = await api.runSpatialDiffInDiff(surveyId, payload);
      if (res.status === 'success') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể thực thi Spatial Difference-in-Differences.');
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
          <div className="p-2.5 bg-gradient-to-br from-emerald-500 to-teal-700 text-white rounded-lg shadow-sm">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Sai phân Không gian Bán tham số & Hiệu ứng Tràn lan (Spatial Difference-in-Differences)
              </h3>
              <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 rounded-full">
                Delgado & Florax (2015) • Butts (2021)
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Phân rã tác động can thiệp thành Hiệu ứng Trực tiếp (Direct ATT) và Hiệu ứng Tràn lan Không gian (Spillover ATT) qua ma trận trọng số địa lý W, hóa giải vi phạm giả định SUTVA
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Vĩ độ Tọa độ (Latitude) *
              </label>
              <select
                value={latQId}
                onChange={e => setLatQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">-- Chọn trường Vĩ độ --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Kinh độ Tọa độ (Longitude) *
              </label>
              <select
                value={lonQId}
                onChange={e => setLonQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">-- Chọn trường Kinh độ --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Time period and Covariates */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Thời kỳ Khảo sát / Thời gian (Tùy chọn cho Panel DiD)
              </label>
              <select
                value={timeQId}
                onChange={e => setTimeQId(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">-- Không sử dụng (Hồi quy Sai phân Cắt ngang) --</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Biến Kiểm soát Bổ sung X (Tùy chọn)
              </label>
              <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto p-1.5 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                {questions
                  .filter(q => q.id !== treatmentQId && q.id !== outcomeQId && q.id !== latQId && q.id !== lonQId)
                  .map(q => {
                    const isChecked = selectedCovariates.includes(q.id);
                    return (
                      <button
                        key={q.id}
                        type="button"
                        onClick={() => handleToggleCovariate(q.id)}
                        className={`text-xs px-2 py-0.5 rounded-md border transition-all ${
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
          </div>

          {/* Spatial Weights Hyperparameters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2 border-t border-slate-200 dark:border-slate-700/60">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Loại Ma trận Không gian W
              </label>
              <select
                value={weightType}
                onChange={e => setWeightType(e.target.value as any)}
                className="w-full text-xs rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-2 border focus:ring-2 focus:ring-emerald-500"
              >
                <option value="inverse_distance">Nghịch đảo Khoảng cách (1/d^p)</option>
                <option value="knn">K Láng giềng Gần nhất (KNN)</option>
              </select>
            </div>

            {weightType === 'knn' ? (
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Số láng giềng gần nhất (k): {knnK}
                </label>
                <input
                  type="range"
                  min="2"
                  max="15"
                  step="1"
                  value={knnK}
                  onChange={e => setKnnK(parseInt(e.target.value, 10))}
                  className="w-full accent-emerald-600 mt-2"
                />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Lũy thừa Khoảng cách (Power p): {distancePower}
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.5"
                  value={distancePower}
                  onChange={e => setDistancePower(parseFloat(e.target.value))}
                  className="w-full accent-emerald-600 mt-2"
                />
              </div>
            )}

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

            <div className="flex items-end">
              <button
                onClick={handleRun}
                disabled={loading}
                className="w-full flex items-center justify-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    <span>Đang tính toán Spatial-DiD...</span>
                  </>
                ) : (
                  <>
                    <Compass className="w-4 h-4" />
                    <span>Thực thi Spatial Difference-in-Differences</span>
                  </>
                )}
              </button>
            </div>
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
                Hiệu ứng Trực tiếp (Direct ATT)
              </span>
              <div className="text-xl font-bold text-blue-600 dark:text-blue-400">
                {result.direct_effect?.estimate !== undefined
                  ? `${result.direct_effect.estimate > 0 ? '+' : ''}${result.direct_effect.estimate.toFixed(4)}`
                  : '—'}
              </div>
              <span className="text-[10px] text-slate-400">
                p = {result.direct_effect?.p_value.toFixed(4)} (SE: {result.direct_effect?.std_error.toFixed(3)})
              </span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Hiệu ứng Tràn lan (Spillover ATT)
              </span>
              <div className="text-xl font-bold text-purple-600 dark:text-purple-400">
                {result.spillover_effect?.estimate !== undefined
                  ? `${result.spillover_effect.estimate > 0 ? '+' : ''}${result.spillover_effect.estimate.toFixed(4)}`
                  : '—'}
              </div>
              <span className="text-[10px] text-slate-400">
                p = {result.spillover_effect?.p_value.toFixed(4)} (Lan tỏa láng giềng W·D)
              </span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Tổng Tác động (Total Impact)
              </span>
              <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                {result.total_impact?.estimate !== undefined
                  ? `${result.total_impact.estimate > 0 ? '+' : ''}${result.total_impact.estimate.toFixed(4)}`
                  : '—'}
              </div>
              <span className="text-[10px] text-slate-400">
                Trực tiếp + Tràn lan không gian
              </span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Moran's I Phần dư
              </span>
              <div className={`text-xl font-bold ${
                result.morans_i_diagnostic?.residual_autocorrelation_cleared ? 'text-emerald-600' : 'text-amber-600'
              }`}>
                {result.morans_i_diagnostic?.moran_i !== undefined ? result.morans_i_diagnostic.moran_i.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400">
                z = {result.morans_i_diagnostic?.z_score.toFixed(2)} (p = {result.morans_i_diagnostic?.p_value.toFixed(3)})
              </span>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Độ phù hợp Mô hình (R²)
              </span>
              <div className="text-xl font-bold text-slate-800 dark:text-slate-200">
                {result.model_fit?.r_squared !== undefined ? result.model_fit.r_squared.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400">
                N = {result.sample_size} (DF: {result.model_fit?.degrees_of_freedom})
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
                onClick={() => setActiveTab('effects')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'effects'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Bảng Phân rã Hiệu ứng Trực tiếp & Lan tỏa
              </button>
              <button
                onClick={() => setActiveTab('spatial_weights')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'spatial_weights'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Cấu hình Ma trận Trọng số Không gian W
              </button>
              <button
                onClick={() => setActiveTab('sutva')}
                className={`py-2 px-3 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === 'sutva'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                Chuẩn đoán Vi phạm SUTVA & Cơ chế Lan tỏa
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'effects' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400">
                    <th className="p-2.5 font-semibold">Thành phần Hiệu ứng</th>
                    <th className="p-2.5 font-semibold">Hệ số Ước lượng (β̂)</th>
                    <th className="p-2.5 font-semibold">Sai số chuẩn HC1 (SE)</th>
                    <th className="p-2.5 font-semibold">Giá trị kiểm định t</th>
                    <th className="p-2.5 font-semibold">P-value</th>
                    <th className="p-2.5 font-semibold">Khoảng Tin cậy 95% CI</th>
                    <th className="p-2.5 font-semibold text-center">Ý nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="p-2.5 font-medium text-blue-600 dark:text-blue-400 flex items-center space-x-1.5">
                      <Radio className="w-3.5 h-3.5" />
                      <span>Hiệu ứng Trực tiếp (Direct ATT: τ_dir)</span>
                    </td>
                    <td className="p-2.5 font-mono font-bold">
                      {result.direct_effect?.estimate !== undefined ? `${result.direct_effect.estimate > 0 ? '+' : ''}${result.direct_effect.estimate.toFixed(4)}` : '—'}
                    </td>
                    <td className="p-2.5 font-mono">{result.direct_effect?.std_error.toFixed(4)}</td>
                    <td className="p-2.5 font-mono">{result.direct_effect?.t_statistic.toFixed(3)}</td>
                    <td className="p-2.5 font-mono">{result.direct_effect?.p_value.toFixed(4)}</td>
                    <td className="p-2.5 font-mono">[{result.direct_effect?.ci_lower.toFixed(4)}, {result.direct_effect?.ci_upper.toFixed(4)}]</td>
                    <td className="p-2.5 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        (result.direct_effect?.p_value || 1) < 0.05
                          ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                      }`}>
                        {(result.direct_effect?.p_value || 1) < 0.05 ? 'Có ý nghĩa (p < .05)' : 'Không có ý nghĩa'}
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="p-2.5 font-medium text-purple-600 dark:text-purple-400 flex items-center space-x-1.5">
                      <Compass className="w-3.5 h-3.5" />
                      <span>Hiệu ứng Tràn lan (Spatial Spillover: τ_spill)</span>
                    </td>
                    <td className="p-2.5 font-mono font-bold">
                      {result.spillover_effect?.estimate !== undefined ? `${result.spillover_effect.estimate > 0 ? '+' : ''}${result.spillover_effect.estimate.toFixed(4)}` : '—'}
                    </td>
                    <td className="p-2.5 font-mono">{result.spillover_effect?.std_error.toFixed(4)}</td>
                    <td className="p-2.5 font-mono">{result.spillover_effect?.t_statistic.toFixed(3)}</td>
                    <td className="p-2.5 font-mono">{result.spillover_effect?.p_value.toFixed(4)}</td>
                    <td className="p-2.5 font-mono">[{result.spillover_effect?.ci_lower.toFixed(4)}, {result.spillover_effect?.ci_upper.toFixed(4)}]</td>
                    <td className="p-2.5 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        (result.spillover_effect?.p_value || 1) < 0.05
                          ? 'bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                      }`}>
                        {(result.spillover_effect?.p_value || 1) < 0.05 ? 'Tràn lan có ý nghĩa' : 'Không đáng kể'}
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors bg-slate-50/50 dark:bg-slate-800/20 font-semibold">
                    <td className="p-2.5 font-bold text-emerald-600 dark:text-emerald-400 flex items-center space-x-1.5">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>Tổng Tác động Toàn phần (Total Marginal Impact)</span>
                    </td>
                    <td className="p-2.5 font-mono font-bold text-emerald-600 dark:text-emerald-400">
                      {result.total_impact?.estimate !== undefined ? `${result.total_impact.estimate > 0 ? '+' : ''}${result.total_impact.estimate.toFixed(4)}` : '—'}
                    </td>
                    <td className="p-2.5 font-mono">{result.total_impact?.std_error.toFixed(4)}</td>
                    <td className="p-2.5 font-mono">{result.total_impact?.t_statistic.toFixed(3)}</td>
                    <td className="p-2.5 font-mono">{result.total_impact?.p_value.toFixed(4)}</td>
                    <td className="p-2.5 font-mono">[{result.total_impact?.ci_lower.toFixed(4)}, {result.total_impact?.ci_upper.toFixed(4)}]</td>
                    <td className="p-2.5 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        (result.total_impact?.p_value || 1) < 0.05
                          ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                      }`}>
                        {(result.total_impact?.p_value || 1) < 0.05 ? 'Tổng tác động có ý nghĩa' : 'Không có ý nghĩa'}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'spatial_weights' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-teal-600 dark:text-teal-400 font-semibold text-xs">
                  <Compass className="w-4 h-4" />
                  <span>Đặc tính Ma trận Trọng số Không gian W</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Cơ chế suy giảm khoảng cách:</span>
                    <span className="font-mono font-semibold">{result.weights_type === 'knn' ? 'K Láng giềng gần nhất' : 'Nghịch đảo Khoảng cách Euclide (1/d^p)'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Chuẩn hóa hàng (Row-Standardization):</span>
                    <span className="font-semibold text-emerald-600">Đã áp dụng (Σ W_ij = 1)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Đường chéo chính (Zero Diagonal):</span>
                    <span className="font-semibold text-emerald-600">W_ii = 0 (Không tự lan tỏa)</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Số chiều ma trận không gian:</span>
                    <span className="font-mono font-semibold">{result.sample_size} × {result.sample_size}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 font-semibold text-xs">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Chuẩn đoán Khử Nhiễu Moran's I</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Chỉ số Moran's I phần dư:</span>
                    <span className="font-mono font-semibold">{result.morans_i_diagnostic?.moran_i.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Giá trị chuẩn hóa Z-score:</span>
                    <span className="font-mono font-semibold">{result.morans_i_diagnostic?.z_score.toFixed(3)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-700">
                    <span className="text-slate-500">Mức ý nghĩa P-value:</span>
                    <span className="font-mono font-semibold">{result.morans_i_diagnostic?.p_value.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Trạng thái Tự tương quan Phần dư:</span>
                    <span className={`font-semibold ${
                      result.morans_i_diagnostic?.residual_autocorrelation_cleared ? 'text-emerald-600' : 'text-amber-600'
                    }`}>
                      {result.morans_i_diagnostic?.residual_autocorrelation_cleared
                        ? 'Sạch hoàn toàn (Không còn tương quan không gian)'
                        : 'Còn tự tương quan phần dư'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sutva' && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
              <div className="flex items-center space-x-2 font-semibold text-xs text-slate-800 dark:text-slate-200">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Hóa giải Vi phạm Giả định SUTVA (Stable Unit Treatment Value Assumption)</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Mô hình Difference-in-Differences truyền thống phụ thuộc hoàn toàn vào giả định SUTVA: <em>can thiệp áp dụng lên một đơn vị không ảnh hưởng đến kết quả tiềm năng của đơn vị khác</em>.
                Trong các khảo sát địa lý hoặc mạng lưới chi nhánh, khi một chi nhánh áp dụng chính sách khuyến mại, khách hàng từ các khu vực lân cận có thể chuyển dịch đến chi nhánh đó (hiệu ứng hút khách), 
                làm sai lệch nghiêm trọng nhóm đối chứng và dẫn đến ước lượng ATT sai lệch đáng kể.
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                <strong>Semiparametric Spatial-DiD (Delgado & Florax 2015; Butts 2021)</strong> đưa biến độ trễ không gian của can thiệp <code className="px-1 bg-slate-200 dark:bg-slate-700 rounded font-mono text-[11px]">(W·D)_i = Σ_j w_ij D_j</code> vào mô hình hồi quy. 
                Điều này cho phép tách bạch hoàn toàn mức độ hiệu ứng can thiệp thực tế của chính đơn vị đó với mức độ chịu tác động lan tỏa từ các đơn vị láng giềng xung quanh.
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
export default SpatialDIDCard;
