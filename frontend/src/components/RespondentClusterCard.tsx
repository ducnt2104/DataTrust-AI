import React, { useState, useEffect, useMemo } from 'react';
import {
  Users2,
  PieChart,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Copy,
  Check,
  RefreshCw,
  Info,
  Layers,
  Activity,
  BookOpen,
  ArrowUpDown,
  BarChart2,
  TrendingUp,
  UserCheck
} from 'lucide-react';
import { api } from '../api/client';
import { ClusterAnalysisReport, ClusterPersona, ClusterFeatureImportance } from '../types/survey';

interface Props {
  surveyId: string;
}

export const RespondentClusterCard: React.FC<Props> = ({ surveyId }) => {
  const [report, setReport] = useState<ClusterAnalysisReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [scope, setScope] = useState<'verified_clean' | 'all'>('verified_clean');
  const [selectedK, setSelectedK] = useState<number | undefined>(undefined);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'personas' | 'features' | 'elbow'>('personas');

  useEffect(() => {
    loadClusterAnalysis();
  }, [surveyId, scope, selectedK]);

  const loadClusterAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getClusterAnalysis(surveyId, selectedK, scope);
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'Không thể thực thi phân tích phân cụm người trả lời.');
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!report?.apa_narrative) return;
    navigator.clipboard.writeText(report.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const qualityBadge = (level: string) => {
    switch (level) {
      case 'STRONG_CLUSTERING':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dot: 'bg-emerald-500',
          label: 'Phân cụm xuất sắc'
        };
      case 'ACCEPTABLE_CLUSTERING':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          dot: 'bg-amber-500',
          label: 'Phân cụm hợp lý'
        };
      case 'WEAK_CLUSTERING':
      default:
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          dot: 'bg-rose-500',
          label: 'Phân cụm yếu / Dữ liệu đồng nhất'
        };
    }
  };

  // SVG Elbow Curve coordinates
  const svgElbowData = useMemo(() => {
    if (!report?.elbow_curve || report.elbow_curve.length === 0) return null;
    const pts = report.elbow_curve;
    const width = 500;
    const height = 180;
    const padding = { top: 20, right: 30, bottom: 30, left: 50 };

    const minK = pts[0].k;
    const maxK = pts[pts.length - 1].k;
    const minW = Math.min(...pts.map((p) => p.wcss));
    const maxW = Math.max(...pts.map((p) => p.wcss));
    const rangeW = maxW - minW || 1.0;

    const scaleX = (kVal: number) =>
      padding.left + ((kVal - minK) / Math.max(1, maxK - minK)) * (width - padding.left - padding.right);
    const scaleY = (wcssVal: number) =>
      height - padding.bottom - ((wcssVal - minW) / rangeW) * (height - padding.top - padding.bottom);

    const pathD = pts.reduce((acc, pt, idx) => {
      const x = scaleX(pt.k);
      const y = scaleY(pt.wcss);
      return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');

    return { width, height, pts, scaleX, scaleY, pathD };
  }, [report?.elbow_curve]);

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-slate-100 gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-50 text-cyan-600 border border-cyan-100 mt-0.5">
            <Users2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Phân Cụm Người Trả Lời & Định Hình Phân Khúc (K-Means Typology Segmentation)
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-cyan-100 text-cyan-800 rounded-full uppercase tracking-wider">
                Thuật toán K-Means++ & Hệ số Silhouette
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Tự động phân nhóm đối tượng trả lời khảo sát thành các hồ sơ nhân vật (Personas) dựa trên độ tương đồng đa chiều và kiểm định ANOVA F-ratio.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* K Clusters Selector */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-500 font-medium">Số cụm K:</span>
            <select
              value={selectedK ?? ''}
              onChange={(e) => setSelectedK(e.target.value ? parseInt(e.target.value, 10) : undefined)}
              className="text-xs bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              <option value="">Tự động (Silhouette tối ưu)</option>
              <option value="2">K = 2 Cụm đối tượng</option>
              <option value="3">K = 3 Cụm đối tượng</option>
              <option value="4">K = 4 Cụm đối tượng</option>
              <option value="5">K = 5 Cụm đối tượng</option>
            </select>
          </div>

          {/* Scope switch */}
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5 text-xs font-medium">
            <button
              onClick={() => setScope('verified_clean')}
              className={`px-3 py-1 rounded-md transition-all ${
                scope === 'verified_clean'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Dữ liệu sạch
            </button>
            <button
              onClick={() => setScope('all')}
              className={`px-3 py-1 rounded-md transition-all ${
                scope === 'all'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Tất cả phản hồi
            </button>
          </div>

          <button
            onClick={loadClusterAnalysis}
            disabled={loading}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Phân cụm lại dữ liệu"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start gap-2">
          <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <strong>Không thể thực hiện phân tích phân cụm:</strong> {error}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && !report && (
        <div className="py-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-cyan-600" />
          <span>Đang chuẩn hóa ma trận Z-score, khởi tạo K-Means++ và tính hệ số Silhouette...</span>
        </div>
      )}

      {/* Results View */}
      {report && (
        <div className="space-y-6">
          {/* 4 Hero KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Clusters Count */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Quy mô phân khúc
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">K = {report.chosen_k}</span>
                <span className="text-xs text-slate-500 font-medium">phân cụm</span>
              </div>
              <p className="text-[11px] text-slate-500">
                N = {report.sample_size} người • {report.features_count} tiêu chí thang đo
              </p>
            </div>

            {/* KPI 2: Silhouette Score */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Hệ số tách biệt Silhouette
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">
                  s = {report.silhouette.overall_score.toFixed(2)}
                </span>
                <span className="text-xs text-slate-400 font-normal">/ 1.00</span>
              </div>
              {(() => {
                const b = qualityBadge(report.silhouette.quality_level);
                return (
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${b.bg}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${b.dot}`} />
                    {b.label}
                  </span>
                );
              })()}
            </div>

            {/* KPI 3: Inertia WCSS */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Độ nén nội cụm (WCSS)
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">{report.wcss.toFixed(1)}</span>
                <span className="text-xs text-slate-500 font-medium">inertia</span>
              </div>
              <p className="text-[11px] text-slate-500">
                Tổng bình phương khoảng cách tới tâm cụm K-Means
              </p>
            </div>

            {/* KPI 4: Top Differentiating Feature */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Tiêu chí phân hóa mạnh nhất
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-base font-black text-cyan-800 line-clamp-1" title={report.feature_importance[0]?.feature_name}>
                  {report.feature_importance[0]?.feature_name || 'N/A'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                ANOVA F = {report.feature_importance[0]?.f_ratio} (eta² = {report.feature_importance[0]?.eta_squared})
              </p>
            </div>
          </div>

          {/* Navigation Sub-Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            <button
              onClick={() => setActiveTab('personas')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'personas'
                  ? 'bg-cyan-50 text-cyan-800 border border-cyan-200 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Hồ sơ Phân khúc Đối tượng (Personas Archetypes)
            </button>
            <button
              onClick={() => setActiveTab('features')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'features'
                  ? 'bg-cyan-50 text-cyan-800 border border-cyan-200 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Bảng Phân Hóa Câu Hỏi (ANOVA F-Ratio)
            </button>
            <button
              onClick={() => setActiveTab('elbow')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'elbow'
                  ? 'bg-cyan-50 text-cyan-800 border border-cyan-200 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Đường Cong Khuỷu Tay (Elbow & Silhouette Curve)
            </button>
          </div>

          {/* Tab 1: Personas Archetypes */}
          {activeTab === 'personas' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {report.personas.map((persona) => (
                <div
                  key={persona.cluster_id}
                  className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 shadow-2xs space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-black text-cyan-700 bg-cyan-100 px-2 py-0.5 rounded">
                        {persona.cluster_code}
                      </span>
                      <span className="text-xs font-bold text-slate-700">
                        {persona.size} người ({persona.percentage}%)
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900 leading-snug">
                      {persona.name}
                    </h4>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {persona.archetype_description}
                    </p>
                  </div>

                  <div className="space-y-2 pt-2 border-t border-slate-200/60 text-xs">
                    {persona.high_traits.length > 0 && (
                      <div>
                        <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider block">
                          Điểm cao vượt trội:
                        </span>
                        <ul className="list-disc list-inside text-slate-700 text-[11px] space-y-0.5 mt-0.5">
                          {persona.high_traits.map((t, idx) => (
                            <li key={idx} className="line-clamp-1">{t}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {persona.low_traits.length > 0 && (
                      <div>
                        <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider block">
                          Điểm thấp / e ngại:
                        </span>
                        <ul className="list-disc list-inside text-slate-700 text-[11px] space-y-0.5 mt-0.5">
                          {persona.low_traits.map((t, idx) => (
                            <li key={idx} className="line-clamp-1">{t}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 2: Feature Importance (ANOVA F-Ratio) */}
          {activeTab === 'features' && (
            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <ArrowUpDown className="w-4 h-4 text-cyan-600" />
                  <span>Mức Độ Phân Hóa Giữa Các Cụm Đối Tượng (ANOVA F-Ratio & Eta-Squared)</span>
                </h4>
                <span className="text-[11px] text-slate-500">
                  F-ratio càng cao chứng tỏ câu hỏi phân tách các phân khúc càng mạnh mẽ
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse border border-slate-200 rounded-lg overflow-hidden bg-white">
                  <thead className="bg-slate-100 text-slate-700 font-bold">
                    <tr>
                      <th className="py-2.5 px-3 border border-slate-200">Tiêu chí khảo sát</th>
                      <th className="py-2.5 px-3 border border-slate-200 text-center font-mono">F-Ratio</th>
                      <th className="py-2.5 px-3 border border-slate-200 text-center font-mono">Eta² (η²)</th>
                      <th className="py-2.5 px-3 border border-slate-200 text-center font-mono">Toàn mẫu (M)</th>
                      {report.personas.map((p) => (
                        <th key={p.cluster_id} className="py-2.5 px-3 border border-slate-200 text-center font-mono">
                          {p.cluster_code} (M)
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.feature_importance.map((feat) => (
                      <tr key={feat.feature_index} className="hover:bg-slate-50 transition-colors">
                        <td className="py-2 px-3 border border-slate-200 font-medium text-slate-800">
                          {feat.feature_name}
                        </td>
                        <td className="py-2 px-3 border border-slate-200 text-center font-mono font-bold text-cyan-800">
                          {feat.f_ratio.toFixed(2)}
                        </td>
                        <td className="py-2 px-3 border border-slate-200 text-center font-mono text-slate-700">
                          {feat.eta_squared.toFixed(3)}
                        </td>
                        <td className="py-2 px-3 border border-slate-200 text-center font-mono text-slate-500">
                          {feat.grand_mean.toFixed(2)}
                        </td>
                        {feat.cluster_means.map((mVal, cIdx) => (
                          <td key={cIdx} className="py-2 px-3 border border-slate-200 text-center font-mono font-semibold text-slate-900">
                            {mVal.toFixed(2)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 3: Elbow Curve SVG */}
          {activeTab === 'elbow' && svgElbowData && (
            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-cyan-600" />
                    <span>Đường Cong Khuỷu Tay (Elbow WCSS vs K Clusters)</span>
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    Điểm khuỷu tay (Elbow point) nơi tốc độ suy giảm WCSS bắt đầu chậm lại đại diện cho số lượng cụm tối ưu.
                  </p>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col items-center">
                <svg
                  viewBox={`0 0 ${svgElbowData.width} ${svgElbowData.height}`}
                  className="w-full max-w-xl h-44 overflow-visible"
                >
                  {/* Grid Lines */}
                  {[0.25, 0.5, 0.75, 1.0].map((ratio) => {
                    const y = svgElbowData.height - 30 - ratio * (svgElbowData.height - 50);
                    return (
                      <line
                        key={ratio}
                        x1="50"
                        y1={y}
                        x2={svgElbowData.width - 30}
                        y2={y}
                        stroke="#f1f5f9"
                        strokeWidth="1"
                      />
                    );
                  })}

                  {/* Path */}
                  <path
                    d={svgElbowData.pathD}
                    fill="none"
                    stroke="#0891b2"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  {/* Points */}
                  {svgElbowData.pts.map((pt) => {
                    const cx = svgElbowData.scaleX(pt.k);
                    const cy = svgElbowData.scaleY(pt.wcss);
                    const isSelected = pt.k === report.chosen_k;
                    return (
                      <g key={pt.k}>
                        <circle
                          cx={cx}
                          cy={cy}
                          r={isSelected ? 6 : 4}
                          fill={isSelected ? '#0891b2' : '#ffffff'}
                          stroke="#0891b2"
                          strokeWidth="2"
                        />
                        <text
                          x={cx}
                          y={cy - 10}
                          textAnchor="middle"
                          className="text-[10px] font-mono font-bold fill-slate-700"
                        >
                          WCSS={pt.wcss.toFixed(0)} (s={pt.silhouette_score.toFixed(2)})
                        </text>
                        <text
                          x={cx}
                          y={svgElbowData.height - 12}
                          textAnchor="middle"
                          className="text-[10px] font-mono fill-slate-500 font-semibold"
                        >
                          K={pt.k}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative Citation Box */}
          <div className="p-4 rounded-xl bg-slate-900 text-slate-100 space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-cyan-300">
                <BookOpen className="w-4 h-4" />
                <span>Trích dẫn báo cáo khoa học (APA 7th Edition Cluster Analysis Statement)</span>
              </div>
              <button
                onClick={handleCopyAPA}
                className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors border border-slate-700"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Đã sao chép</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao chép APA</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs font-mono text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800/80 leading-relaxed selection:bg-cyan-600 selection:text-white">
              {report.apa_narrative}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
