import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  BarChart3,
  CheckCircle2,
  Clock,
  Compass,
  Copy,
  Layers,
  LineChart,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Users
} from 'lucide-react';
import { api } from '../api/client';
import {
  CompetingRisksAnalysisResult
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface CompetingRisksFrailtyCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const CompetingRisksFrailtyCard: React.FC<CompetingRisksFrailtyCardProps> = ({
  surveyId,
  questions
}) => {
  const [clusterQId, setClusterQId] = useState<string>('');
  const [eventQId, setEventQId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompetingRisksAnalysisResult | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'curves' | 'milestones' | 'frailty'>('curves');

  const categoricalQuestions = questions.filter((q) =>
    ['single_choice', 'dropdown', 'text'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.runCompetingRisksAnalysis(surveyId, {
        cluster_question_id: clusterQId || null,
        event_question_id: eventQId || null,
        scope
      });
      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể thực hiện phân tích nguy cơ cạnh tranh.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi phân tích nguy cơ cạnh tranh.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyApa = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopiedApa(true);
      setTimeout(() => setCopiedApa(false), 2000);
    }
  };

  const formatCauseLabel = (cause: string) => {
    const map: Record<string, string> = {
      voluntary_dropoff: 'Tự ý bỏ cuộc giữa chừng',
      quota_screenout: 'Hết hạn ngạch quota',
      fraud_rejected: 'Loại trừ do gian lận/chất lượng',
      completed: 'Hoàn thành khảo sát'
    };
    return map[cause] || cause;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
      {/* Header */}
      <div className="p-6 bg-gradient-to-r from-amber-900 via-amber-800 to-slate-900 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-amber-700/60 rounded-lg border border-amber-500/40">
              <LineChart className="w-6 h-6 text-amber-200" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-xl font-bold tracking-tight">
                  Nguy cơ Cạnh tranh & Mô hình Suy yếu (Competing Risks & Shared Frailty)
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/30 text-amber-200 border border-amber-400/30">
                  Fine & Gray 1999 • Hougaard 2000
                </span>
              </div>
              <p className="text-sm text-amber-200/80 mt-1">
                Phân định các nguyên nhân kết thúc khảo sát loại trừ lẫn nhau (Bỏ cuộc, Quota, Gian lận) và kiểm định tính không đồng nhất giữa các điều tra viên/thiết bị.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex bg-amber-950/60 p-1 rounded-lg border border-amber-700/50 text-xs">
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  scope === 'all'
                    ? 'bg-amber-600 text-white shadow-sm'
                    : 'text-amber-300 hover:text-white'
                }`}
              >
                Tất cả mẫu
              </button>
              <button
                type="button"
                onClick={() => setScope('verified_clean')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  scope === 'verified_clean'
                    ? 'bg-amber-600 text-white shadow-sm'
                    : 'text-amber-300 hover:text-white'
                }`}
              >
                Dữ liệu sạch
              </button>
            </div>

            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white font-medium text-sm rounded-lg transition shadow-sm"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Đang phân tích…' : 'Phân tích Nguy cơ'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="p-6 border-b border-slate-200 bg-slate-50/70">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center space-x-1.5">
              <Users className="w-3.5 h-3.5 text-amber-600" />
              <span>Biến Cụm Suy Yếu (Cluster / Điều tra viên / Thiết bị / Chi nhánh):</span>
            </label>
            <select
              value={clusterQId}
              onChange={(e) => setClusterQId(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white py-2 px-3"
            >
              <option value="">-- Mặc định (Tự động gom cụm theo Metadata) --</option>
              {categoricalQuestions.map((q) => (
                <option key={`cluster-${q.id}`} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
            <span className="text-2xs text-slate-500 mt-1 block">
              Dùng để ước lượng mô hình Shared Gamma Frailty đánh giá sai lệch theo điều tra viên hoặc thiết bị.
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center space-x-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              <span>Biến Phân loại Biến cố Kết thúc (Event / Tùy chọn):</span>
            </label>
            <select
              value={eventQId}
              onChange={(e) => setEventQId(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white py-2 px-3"
            >
              <option value="">-- Mặc định (Tự động nhận diện từ Sổ nhật ký Telemetry) --</option>
              {categoricalQuestions.map((q) => (
                <option key={`event-${q.id}`} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
            <span className="text-2xs text-slate-500 mt-1 block">
              Hệ thống tự động phát hiện Quota Screen-out, Gian lận tốc độ, và Bỏ dở giữa chừng từ telemetry.
            </span>
          </div>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 mx-6 mt-6 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg flex items-start space-x-3 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Thông báo từ động cơ:</span> {error}
          </div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="p-6 space-y-6">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs font-medium text-slate-500 block">Cỡ mẫu phân tích (N)</span>
              <span className="text-xl font-bold text-slate-900 mt-1 block">
                {result.sample_size} <span className="text-xs font-normal text-slate-500">phản hồi</span>
              </span>
            </div>

            <div className="p-4 bg-amber-50/70 rounded-xl border border-amber-200">
              <span className="text-xs font-medium text-amber-700 block">Số nguy cơ cạnh tranh</span>
              <span className="text-xl font-bold text-amber-900 mt-1 block">
                {result.competing_causes?.length || 0} <span className="text-xs font-normal text-amber-700">nguyên nhân</span>
              </span>
            </div>

            <div className="p-4 bg-indigo-50/70 rounded-xl border border-indigo-200">
              <span className="text-xs font-medium text-indigo-700 block">Phương sai Suy yếu (θ)</span>
              <span className="text-xl font-bold text-indigo-900 mt-1 block">
                {result.shared_frailty_model?.frailty_variance_theta.toFixed(3) || '0.000'}
              </span>
            </div>

            <div className="p-4 bg-emerald-50/70 rounded-xl border border-emerald-200">
              <span className="text-xs font-medium text-emerald-700 block">Kiểm định Dị biệt Cụm (LRT)</span>
              <span className="text-sm font-bold text-emerald-900 mt-1 block flex items-center space-x-1">
                <span>p = {result.shared_frailty_model?.p_value.toFixed(3)}</span>
                <span
                  className={`text-2xs px-1.5 py-0.5 rounded-full font-bold ml-1 ${
                    result.shared_frailty_model?.is_cluster_heterogeneity_significant
                      ? 'bg-rose-100 text-rose-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  {result.shared_frailty_model?.is_cluster_heterogeneity_significant
                    ? 'Có dị biệt'
                    : 'Đồng nhất'}
                </span>
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-slate-200 flex space-x-6 text-sm font-medium">
            <button
              type="button"
              onClick={() => setActiveTab('curves')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'curves'
                  ? 'border-b-2 border-amber-600 text-amber-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <LineChart className="w-4 h-4" />
              <span>Đường cong Tích lũy Biến cố (CIF Curves)</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('milestones')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'milestones'
                  ? 'border-b-2 border-amber-600 text-amber-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>Đánh giá Mốc Thời gian & Sai lệch KM</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('frailty')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'frailty'
                  ? 'border-b-2 border-amber-600 text-amber-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Suy yếu Cụm Điều tra viên ({result.shared_frailty_model?.clusters_count || 0})</span>
            </button>
          </div>

          {/* Tab Content: CIF SVG Curves */}
          {activeTab === 'curves' && result.svg_cif_chart && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Hàm Tích lũy Biến cố Phi tham số Aalen-Johansen (Cumulative Incidence Function):</span>
                <span className="text-2xs bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded">
                  Khắc phục triệt để sai lệch thổi phồng của Kaplan-Meier cổ điển
                </span>
              </div>
              <div
                className="w-full bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs p-2 flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_cif_chart }}
              />
            </div>
          )}

          {/* Tab Content: Milestone Evaluation & KM Bias */}
          {activeTab === 'milestones' && result.milestone_evaluations && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-slate-600">Mốc thời gian (giây)</th>
                      <th className="px-3 py-2 text-right font-semibold text-emerald-700">Tỷ lệ Hoàn thành S(t)</th>
                      <th className="px-3 py-2 text-left font-semibold text-slate-600">Nguyên nhân</th>
                      <th className="px-3 py-2 text-right font-semibold text-amber-700 font-bold">Xác suất CIF chuẩn</th>
                      <th className="px-3 py-2 text-right font-semibold text-slate-500">KM Cổ điển (1 - S_km)</th>
                      <th className="px-3 py-2 text-right font-semibold text-rose-700 font-bold">Độ lệch Thổi phồng (Bias)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.milestone_evaluations.map((ms, idx) => (
                      <React.Fragment key={`ms-${idx}`}>
                        {result.competing_causes?.map((c, cIdx) => {
                          const cifVal = ms.cumulative_incidence[c] || 0.0;
                          const naiveVal = ms.naive_kaplan_meier[c] || 0.0;
                          const biasVal = ms.km_overestimation_bias[c] || 0.0;
                          return (
                            <tr key={`ms-${idx}-${c}`} className="hover:bg-slate-50/80">
                              {cIdx === 0 && (
                                <td
                                  rowSpan={result.competing_causes?.length || 1}
                                  className="px-3 py-2.5 font-bold text-slate-900 border-r border-slate-200 bg-slate-50/50"
                                >
                                  {ms.time_seconds} giây
                                </td>
                              )}
                              {cIdx === 0 && (
                                <td
                                  rowSpan={result.competing_causes?.length || 1}
                                  className="px-3 py-2.5 text-right font-mono font-bold text-emerald-700 border-r border-slate-200 bg-slate-50/50"
                                >
                                  {(ms.overall_completion_rate * 100).toFixed(1)}%
                                </td>
                              )}
                              <td className="px-3 py-2 font-medium text-slate-800">
                                {formatCauseLabel(c)}
                              </td>
                              <td className="px-3 py-2 text-right font-mono font-bold text-amber-700">
                                {(cifVal * 100).toFixed(1)}%
                              </td>
                              <td className="px-3 py-2 text-right font-mono text-slate-500">
                                {(naiveVal * 100).toFixed(1)}%
                              </td>
                              <td className="px-3 py-2 text-right font-mono font-bold text-rose-600">
                                +{(biasVal * 100).toFixed(1)}%
                              </td>
                            </tr>
                          );
                        })}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Content: Cluster Frailty Estimates */}
          {activeTab === 'frailty' && result.shared_frailty_model && (
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-600 gap-2">
                <span>
                  Mô hình Shared Gamma Frailty:{' '}
                  <strong>θ = {result.shared_frailty_model.frailty_variance_theta.toFixed(3)}</strong> (LRT ={' '}
                  {result.shared_frailty_model.lrt_statistic.toFixed(2)}, p ={' '}
                  {result.shared_frailty_model.p_value.toFixed(4)})
                </span>
                <span className="text-2xs font-medium text-slate-500">
                  {result.shared_frailty_model.is_cluster_heterogeneity_significant
                    ? '⚠️ Tồn tại sự sai biệt đáng kể về tỷ lệ bỏ dở giữa các điều tra viên'
                    : '✅ Không phát hiện sai biệt bất thường giữa các cụm điều tra'}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-slate-600">Mã Cụm / Điều tra viên</th>
                      <th className="px-3 py-2 text-right font-semibold text-slate-600">Quy mô mẫu</th>
                      <th className="px-3 py-2 text-right font-semibold text-slate-600">Số ca bỏ cuộc</th>
                      <th className="px-3 py-2 text-right font-semibold text-slate-600">Tỷ lệ bỏ cuộc</th>
                      <th className="px-3 py-2 text-right font-semibold text-indigo-700 font-bold">Rủi ro Tương đối (w_i)</th>
                      <th className="px-3 py-2 text-center font-semibold text-slate-600">Đánh giá rủi ro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.shared_frailty_model.cluster_frailty_estimates.map((est, idx) => (
                      <tr key={`est-${idx}`} className="hover:bg-slate-50/80">
                        <td className="px-3 py-2.5 font-bold text-slate-900">{est.cluster_id}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-700">{est.sample_size}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-slate-700">{est.dropoffs}</td>
                        <td className="px-3 py-2.5 text-right font-mono font-medium text-slate-700">
                          {(est.dropoff_rate * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold text-indigo-700 text-sm">
                          {est.frailty_relative_risk.toFixed(3)}
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-full text-2xs font-semibold ${
                              est.frailty_relative_risk > 1.25
                                ? 'bg-rose-100 text-rose-800'
                                : est.frailty_relative_risk < 0.8
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {est.interpretation}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                  <Award className="w-4 h-4 text-amber-600" />
                  <span>Thuyết minh Học thuật Chuẩn APA 7th Edition</span>
                </span>
                <button
                  type="button"
                  onClick={handleCopyApa}
                  className="flex items-center space-x-1 text-xs text-amber-700 hover:text-amber-800 font-medium transition"
                >
                  {copiedApa ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-serif whitespace-pre-line bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
