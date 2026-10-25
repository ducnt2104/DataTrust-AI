import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  GitCompare,
  Layers,
  Network,
  Users,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  ExternalLink,
  Laptop,
  Globe,
  Clock,
  Sparkles,
  Info
} from 'lucide-react';
import { api } from '../api/client';
import type {
  PairwiseSimilarityAnalysisReport,
  PairwiseMatchMetric,
  CollusionRing,
  SimilarityMatrixNode
} from '../types/survey';

interface Props {
  surveyId: string;
}

export const PairwiseSimilarityCard: React.FC<Props> = ({ surveyId }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<PairwiseSimilarityAnalysisReport | null>(null);

  // Filter & control states
  const [threshold, setThreshold] = useState<number>(0.80);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'matrix' | 'rings' | 'pairs'>('rings');
  const [hoveredCell, setHoveredCell] = useState<{
    row: number;
    col: number;
    sim: number;
    nodeA: SimilarityMatrixNode;
    nodeB: SimilarityMatrixNode;
  } | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPairwiseSimilarityAnalysis(surveyId, {
        threshold,
        max_matrix_size: 40,
        scope
      });
      setReport(data);
    } catch (err: any) {
      setError(err?.message || 'Không thể tính toán ma trận tương đồng cặp.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (surveyId) {
      fetchAnalysis();
    }
  }, [surveyId, threshold, scope]);

  const handleCopyNarrative = () => {
    if (report?.academic_narrative) {
      navigator.clipboard.writeText(report.academic_narrative);
      setCopiedNarrative(true);
      setTimeout(() => setCopiedNarrative(false), 2000);
    }
  };

  const getHeatmapColor = (sim: number, isDiagonal: boolean) => {
    if (isDiagonal) return 'bg-indigo-600 text-white font-semibold';
    if (sim >= 0.95) return 'bg-rose-600 text-white font-bold hover:ring-2 hover:ring-rose-400';
    if (sim >= 0.85) return 'bg-rose-500 text-white font-medium hover:ring-2 hover:ring-rose-300';
    if (sim >= 0.75) return 'bg-amber-400 text-slate-900 font-medium hover:ring-2 hover:ring-amber-200';
    if (sim >= 0.50) return 'bg-amber-100 text-amber-900 hover:ring-2 hover:ring-amber-200';
    if (sim >= 0.30) return 'bg-slate-100 text-slate-750 hover:ring-2 hover:ring-slate-300';
    return 'bg-slate-50 text-slate-400 hover:ring-2 hover:ring-slate-200';
  };

  if (loading && !report) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center min-h-[320px]">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mb-3" />
        <p className="text-slate-600 font-medium">Đang đo khoảng cách Hamming & quét ma trận tương đồng cặp...</p>
        <p className="text-xs text-slate-400 mt-1">Thuật toán đối soát tổ hợp N × (N-1)/2 và phân tích vòng thông đồng</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-red-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-3 text-red-600 mb-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <h3 className="font-semibold text-base">Lỗi Phân Tích Ma Trận Tương Đồng</h3>
        </div>
        <p className="text-sm text-red-700 mb-4">{error}</p>
        <button
          onClick={fetchAnalysis}
          className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (!report || report.total_responses === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm text-center">
        <Layers className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800">Chưa Đủ Dữ Liệu Phản Hồi</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
          Cần tối thiểu từ 2 phản hồi trở lên để tính toán ma trận tương đồng cặp và phát hiện dấu hiệu lừa đảo/trùng lặp.
        </p>
      </div>
    );
  }

  const { summary, collusion_rings, high_risk_pairs, matrix_nodes, similarity_matrix } = report;

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 bg-gradient-to-r from-slate-50 via-white to-slate-50">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 flex-shrink-0">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900">
                  Ma Trận Tương Đồng Cặp & Mạng Lưới Thông Đồng
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
                  AAPOR & ISO 20252
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Quét toàn bộ tổ hợp cặp phản hồi, đo khoảng cách Hamming/Jaccard, phát hiện trùng lặp bot farm và chia sẻ thiết bị
              </p>
            </div>
          </div>

          {/* Interactive Controls */}
          <div className="flex items-center gap-3 flex-wrap">
            {/* Scope Filter */}
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
              <button
                onClick={() => setScope('all')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  scope === 'all'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Tất cả ({summary.total_responses})
              </button>
              <button
                onClick={() => setScope('verified_clean')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  scope === 'verified_clean'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Chỉ dữ liệu sạch
              </button>
            </div>

            {/* Threshold Slider */}
            <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs">
              <span className="text-slate-600 font-medium">Ngưỡng lọc S:</span>
              <input
                type="range"
                min="0.60"
                max="0.95"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-20 accent-indigo-600 cursor-pointer"
              />
              <span className="font-bold text-indigo-600 w-10 text-right">
                {Math.round(threshold * 100)}%
              </span>
            </div>

            <button
              onClick={fetchAnalysis}
              disabled={loading}
              className="p-2 border border-slate-200 rounded-lg hover:bg-slate-100 text-slate-600 transition"
              title="Tính toán lại"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* 4 KPI Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Tổng Cặp Đối Soát</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-slate-900">
                {summary.evaluated_pairs.toLocaleString()}
              </span>
              <span className="text-xs text-slate-500">từ {summary.total_responses} mẫu</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Cặp Tương Đồng Cao (≥ {Math.round(threshold * 100)}%)</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${summary.high_risk_pairs_count > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                {summary.high_risk_pairs_count}
              </span>
              <span className="text-xs text-slate-500">cặp nghi vấn</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Mạng Lưới Thông Đồng</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${summary.collusion_rings_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {summary.collusion_rings_count}
              </span>
              <span className="text-xs text-slate-500">({summary.collusion_nodes_count} phản hồi)</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Chỉ Số Liêm Chính Mẫu</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${
                summary.data_integrity_index >= 90
                  ? 'text-emerald-600'
                  : summary.data_integrity_index >= 75
                  ? 'text-amber-600'
                  : 'text-rose-600'
              }`}>
                {summary.data_integrity_index}%
              </span>
              <span className="text-xs text-slate-500">Cực đại S: {Math.round(summary.highest_similarity * 100)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs Switcher */}
      <div className="px-6 border-b border-slate-200 flex items-center gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('rings')}
          className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
            activeTab === 'rings'
              ? 'border-indigo-600 text-indigo-600 font-semibold'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Network className="w-4 h-4" />
          <span>Vòng Thông Đồng & Bot Rings</span>
          {collusion_rings.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-700">
              {collusion_rings.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('pairs')}
          className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
            activeTab === 'pairs'
              ? 'border-indigo-600 text-indigo-600 font-semibold'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <GitCompare className="w-4 h-4" />
          <span>Danh Sách Cặp Tương Đồng Cao</span>
          {high_risk_pairs.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
              {high_risk_pairs.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('matrix')}
          className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
            activeTab === 'matrix'
              ? 'border-indigo-600 text-indigo-600 font-semibold'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Ma Trận Nhiệt (Heatmap Matrix)</span>
          <span className="text-xs text-slate-400">({report.matrix_size}×{report.matrix_size})</span>
        </button>
      </div>

      {/* Tab 1: Collusion Rings */}
      {activeTab === 'rings' && (
        <div className="p-6 space-y-4">
          {collusion_rings.length === 0 ? (
            <div className="py-12 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
              <h4 className="font-semibold text-slate-800 text-base">Không Phát Hiện Mạng Lưới Gian Lận</h4>
              <p className="text-sm text-slate-500 mt-1 max-w-lg mx-auto">
                Không ghi nhận cụm phản hồi nào chia sẻ cùng thiết bị hoặc có mức tương đồng cao bất thường vượt ngưỡng {Math.round(threshold * 100)}%.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {collusion_rings.map((ring) => (
                <div
                  key={ring.ring_id}
                  className={`border rounded-xl p-5 transition shadow-xs ${
                    ring.threat_level === 'CRITICAL'
                      ? 'border-rose-300 bg-rose-50/40'
                      : ring.threat_level === 'HIGH'
                      ? 'border-amber-300 bg-amber-50/40'
                      : 'border-slate-300 bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${
                        ring.threat_level === 'CRITICAL'
                          ? 'bg-rose-600 text-white'
                          : ring.threat_level === 'HIGH'
                          ? 'bg-amber-600 text-white'
                          : 'bg-slate-700 text-white'
                      }`}>
                        {ring.ring_id}
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>{ring.member_count} Phản hồi liên kết</span>
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                            ring.threat_level === 'CRITICAL'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : ring.threat_level === 'HIGH'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-slate-100 text-slate-700 border border-slate-200'
                          }`}>
                            {ring.threat_level}
                          </span>
                        </h4>
                        <span className="text-xs text-slate-500">
                          Tương đồng nội bộ bình quân: <strong className="text-slate-800">{Math.round(ring.mean_internal_similarity * 100)}%</strong>
                        </span>
                      </div>
                    </div>

                    <a
                      href={`/surveys/${surveyId}/compare?id1=${ring.response_ids[0]}&id2=${ring.response_ids[1]}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-2.5 py-1 text-xs font-semibold rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 flex items-center gap-1 transition"
                    >
                      <GitCompare className="w-3.5 h-3.5" />
                      So sánh cặp
                    </a>
                  </div>

                  {/* Badges of collusion signals */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    {ring.has_shared_device && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                        <Laptop className="w-3.5 h-3.5" />
                        Chung thiết bị ({ring.shared_devices_count} máy)
                      </span>
                    )}
                    {ring.has_shared_ip && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200">
                        <Globe className="w-3.5 h-3.5" />
                        Chung dải IP ({ring.shared_ips_count} IP)
                      </span>
                    )}
                    {typeof ring.time_span_seconds === 'number' && ring.time_span_seconds <= 180 && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-orange-100 text-orange-800 border border-orange-200">
                        <Clock className="w-3.5 h-3.5" />
                        Nộp dồn dập ({ring.time_span_seconds}s)
                      </span>
                    )}
                  </div>

                  {/* List of Member response IDs */}
                  <div className="mt-3 bg-white/80 p-2.5 rounded-lg border border-slate-200/80">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                      Danh sách mã phản hồi:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {ring.response_ids.map((rid) => (
                        <a
                          key={rid}
                          href={`/surveys/${surveyId}/responses/${rid}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-0.5 rounded font-mono text-xs bg-slate-100 text-slate-700 hover:bg-indigo-100 hover:text-indigo-800 transition flex items-center gap-1"
                        >
                          {rid.slice(0, 8)}...
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      ))}
                    </div>
                  </div>

                  {/* Recommended Action */}
                  <div className="mt-3 flex items-start gap-2 text-xs text-slate-700 bg-white/60 p-2.5 rounded-lg border border-slate-200/60">
                    <Info className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-semibold text-slate-900">Khuyến nghị xử lý: </strong>
                      {ring.recommended_action}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: High Risk Pairs Table */}
      {activeTab === 'pairs' && (
        <div className="overflow-x-auto">
          {high_risk_pairs.length === 0 ? (
            <div className="py-12 text-center bg-slate-50">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm text-slate-600 font-medium">
                Không có cặp phản hồi nào đạt mức tương đồng ≥ {Math.round(threshold * 100)}%.
              </p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Cặp Phản Hồi</th>
                  <th className="py-3 px-4">Độ Tương Đồng</th>
                  <th className="py-3 px-4">Chi Tiết So Sánh</th>
                  <th className="py-3 px-4">Dấu Hiệu Gian Lận</th>
                  <th className="py-3 px-4">Thời Gian Cách Nhau</th>
                  <th className="py-3 px-4 text-right">Thao Tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {high_risk_pairs.map((p, idx) => (
                  <tr
                    key={`${p.response_id_a}-${p.response_id_b}-${idx}`}
                    className="hover:bg-slate-50/80 transition"
                  >
                    <td className="py-3.5 px-4 font-mono text-xs">
                      <div className="flex items-center gap-1.5">
                        <a
                          href={`/surveys/${surveyId}/responses/${p.response_id_a}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-1 rounded bg-slate-100 text-slate-700 hover:text-indigo-600 font-semibold"
                        >
                          {p.response_id_a.slice(0, 8)}
                        </a>
                        <span className="text-slate-400">↔</span>
                        <a
                          href={`/surveys/${surveyId}/responses/${p.response_id_b}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-1 rounded bg-slate-100 text-slate-700 hover:text-indigo-600 font-semibold"
                        >
                          {p.response_id_b.slice(0, 8)}
                        </a>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                          p.composite_similarity >= 0.95
                            ? 'bg-rose-100 text-rose-800'
                            : p.composite_similarity >= 0.85
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-indigo-100 text-indigo-800'
                        }`}>
                          {Math.round(p.composite_similarity * 100)}%
                        </span>
                        <span className="text-xs text-slate-500 font-medium">{p.badge}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-600">
                      <div>Đóng: {Math.round(p.closed_similarity * 100)}% ({p.closed_matches}/{p.closed_valid_comparisons} câu)</div>
                      {p.open_similarity > 0 && (
                        <div className="text-slate-500">Mở: {Math.round(p.open_similarity * 100)}%</div>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap gap-1">
                        {p.same_device && (
                          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-red-100 text-red-800">
                            Cùng Thiết Bị
                          </span>
                        )}
                        {p.same_ip && (
                          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-100 text-purple-800">
                            Cùng IP
                          </span>
                        )}
                        {p.rapid_succession && (
                          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-orange-100 text-orange-800">
                            Dồn Dập
                          </span>
                        )}
                        {!p.same_device && !p.same_ip && !p.rapid_succession && (
                          <span className="text-slate-400 text-xs">Không có dấu vết phần cứng</span>
                        )}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-600">
                      {p.time_delta_seconds !== null && p.time_delta_seconds !== undefined ? (
                        p.time_delta_seconds < 60 ? (
                          <span className="font-semibold text-rose-600">{p.time_delta_seconds}s</span>
                        ) : (
                          <span>{Math.round(p.time_delta_seconds / 60)} phút</span>
                        )
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <a
                        href={`/surveys/${surveyId}/compare?id1=${p.response_id_a}&id2=${p.response_id_b}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition"
                      >
                        <GitCompare className="w-3.5 h-3.5" />
                        So sánh đối đầu
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab 3: Heatmap Matrix */}
      {activeTab === 'matrix' && (
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs text-slate-500 font-medium">
              Ma trận hiển thị {report.matrix_size} phản hồi đầu tiên. Rê chuột vào từng ô để xem hệ số tương đồng và mã cặp.
            </span>
            <div className="flex items-center gap-2 text-xs">
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-slate-100 inline-block"></span> &lt; 50%</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-200 inline-block"></span> 50-74%</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-400 inline-block"></span> 75-84%</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-rose-500 inline-block"></span> 85-94%</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-rose-600 inline-block"></span> ≥ 95%</span>
            </div>
          </div>

          <div className="overflow-x-auto pb-4">
            <div className="inline-block min-w-full">
              <table className="border-collapse text-center">
                <thead>
                  <tr>
                    <th className="p-1 text-[10px] text-slate-400 font-normal">#</th>
                    {matrix_nodes.map((node, colIdx) => (
                      <th
                        key={node.id}
                        className={`p-1 text-[10px] font-mono transform -rotate-45 h-10 w-6 truncate ${
                          node.is_in_collusion_ring ? 'text-rose-600 font-bold' : 'text-slate-500'
                        }`}
                        title={`#${colIdx + 1} (${node.short_id})`}
                      >
                        {colIdx + 1}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {similarity_matrix.map((row, rowIdx) => (
                    <tr key={matrix_nodes[rowIdx]?.id || rowIdx}>
                      <td
                        className={`p-1 text-[10px] font-mono w-6 text-right pr-2 ${
                          matrix_nodes[rowIdx]?.is_in_collusion_ring ? 'text-rose-600 font-bold' : 'text-slate-500'
                        }`}
                        title={`#${rowIdx + 1} (${matrix_nodes[rowIdx]?.short_id})`}
                      >
                        {rowIdx + 1}
                      </td>
                      {row.map((sim, colIdx) => {
                        const isDiag = rowIdx === colIdx;
                        const cellColor = getHeatmapColor(sim, isDiag);
                        return (
                          <td
                            key={`${rowIdx}-${colIdx}`}
                            onMouseEnter={() => {
                              if (!isDiag) {
                                setHoveredCell({
                                  row: rowIdx,
                                  col: colIdx,
                                  sim,
                                  nodeA: matrix_nodes[rowIdx],
                                  nodeB: matrix_nodes[colIdx]
                                });
                              }
                            }}
                            onMouseLeave={() => setHoveredCell(null)}
                            className={`p-0 border border-white cursor-pointer transition-all ${cellColor}`}
                            style={{ width: '22px', height: '22px' }}
                          >
                            <span className="text-[9px] select-none">
                              {isDiag ? '•' : Math.round(sim * 100)}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Hovered Cell Detail Drawer */}
          {hoveredCell && (
            <div className="mt-4 p-3 bg-slate-900 text-white rounded-lg text-xs flex items-center justify-between gap-4 animate-in fade-in">
              <div className="flex items-center gap-3">
                <span className="font-mono bg-slate-800 px-2 py-1 rounded">
                  #{hoveredCell.row + 1} ({hoveredCell.nodeA.short_id}) ↔ #{hoveredCell.col + 1} ({hoveredCell.nodeB.short_id})
                </span>
                <span>
                  Hệ số tương đồng: <strong className="text-amber-400 font-bold text-sm">{Math.round(hoveredCell.sim * 100)}%</strong>
                </span>
              </div>
              <a
                href={`/surveys/${surveyId}/compare?id1=${hoveredCell.nodeA.id}&id2=${hoveredCell.nodeB.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded transition flex items-center gap-1"
              >
                <GitCompare className="w-3.5 h-3.5" />
                Mở so sánh chi tiết
              </a>
            </div>
          )}
        </div>
      )}

      {/* APA / ISO 20252 Academic Audit Paragraph */}
      <div className="p-6 bg-slate-50 border-t border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Trích dẫn học thuật (APA 7th & ISO 20252 Audit Paragraph)</span>
          </div>
          <button
            onClick={handleCopyNarrative}
            className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium transition"
          >
            {copiedNarrative ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-600">Đã sao chép</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Sao chép đoạn văn</span>
              </>
            )}
          </button>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed italic bg-white p-3.5 rounded-lg border border-slate-200 select-all font-serif">
          "{report.academic_narrative}"
        </p>
      </div>
    </div>
  );
};
