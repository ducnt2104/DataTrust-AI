import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Compass,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Copy,
  Check,
  ExternalLink,
  GitCompare,
  Zap,
  ShieldAlert,
  Users,
  Navigation,
  Sparkles,
  Info
} from 'lucide-react';
import { api } from '../api/client';
import type {
  SpatialAnalysisReport,
  SpatialCluster,
  SpeedAnomaly,
  SpatialGpsPoint
} from '../types/survey';

interface Props {
  surveyId: string;
}

export const SpatialGeoAuditCard: React.FC<Props> = ({ surveyId }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<SpatialAnalysisReport | null>(null);

  // Filter & control states
  const [epsMeters, setEpsMeters] = useState<number>(75.0);
  const [minSamples, setMinSamples] = useState<number>(3);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'clusters' | 'speed' | 'map'>('clusters');
  const [hoveredPoint, setHoveredPoint] = useState<SpatialGpsPoint | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSpatialAnalysis(surveyId, {
        eps_meters: epsMeters,
        min_samples: minSamples,
        max_speed_kmh: 120.0,
        scope
      });
      setReport(data);
    } catch (err: any) {
      setError(err?.message || 'Không thể tính toán kiểm định không gian thực địa.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (surveyId) {
      fetchAnalysis();
    }
  }, [surveyId, epsMeters, minSamples, scope]);

  const handleCopyNarrative = () => {
    if (report?.academic_narrative) {
      navigator.clipboard.writeText(report.academic_narrative);
      setCopiedNarrative(true);
      setTimeout(() => setCopiedNarrative(false), 2000);
    }
  };

  if (loading && !report) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center min-h-[320px]">
        <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
        <p className="text-slate-600 font-medium">Đang tính toán phân cụm mật độ không gian DBSCAN...</p>
        <p className="text-xs text-slate-400 mt-1">Đo khoảng cách trắc địa Haversine, bóc tách cụm tĩnh và kiểm định vận tốc tức thời</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-red-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-3 text-red-600 mb-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <h3 className="font-semibold text-base">Lỗi Kiểm Định Không Gian</h3>
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
        <MapPin className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800">Chưa Có Dữ Liệu Phản Hồi</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
          Cần có phản hồi thu thập thực địa kèm tọa độ GPS để phân tích phân cụm mật độ và kiểm tra gian lận vị trí.
        </p>
      </div>
    );
  }

  const { summary, clusters, speed_anomalies, dispersion, gps_points, gps_coverage_pct } = report;

  // Compute normalized bounds for the 2D SVG map
  const bBox = dispersion.bounding_box;
  const latSpan = bBox ? Math.max(0.005, bBox.max_lat - bBox.min_lat) : 0.01;
  const lonSpan = bBox ? Math.max(0.005, bBox.max_lon - bBox.min_lon) : 0.01;

  const getSvgCoords = (lat: number, lon: number) => {
    if (!bBox) return { x: 200, y: 150 };
    // Padding 40px in a 600x350 viewBox
    const pad = 40;
    const width = 600 - pad * 2;
    const height = 350 - pad * 2;
    const x = pad + ((lon - bBox.min_lon) / lonSpan) * width;
    // Latitude decreases as Y increases
    const y = pad + ((bBox.max_lat - lat) / latSpan) * height;
    return { x, y };
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 bg-gradient-to-r from-slate-50 via-white to-slate-50">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 flex-shrink-0">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900">
                  Kiểm Định Không Gian Thực Địa & Gian Lận Tọa Độ GPS
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  ISO 20252 §4.5.3
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
                  DBSCAN & AAPOR
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Phân cụm mật độ DBSCAN phát hiện ngồi quán cà phê khai khống, rà soát vận tốc di chuyển bất khả thi và tính độ phân tán chuẩn
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

            {/* Radius Slider */}
            <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs">
              <span className="text-slate-600 font-medium">Bán kính ε:</span>
              <input
                type="range"
                min="30"
                max="250"
                step="10"
                value={epsMeters}
                onChange={(e) => setEpsMeters(parseFloat(e.target.value))}
                className="w-16 accent-emerald-600 cursor-pointer"
              />
              <span className="font-bold text-emerald-600 w-10 text-right">{epsMeters}m</span>
            </div>

            {/* Min Samples */}
            <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs">
              <span className="text-slate-600 font-medium">Min pts:</span>
              <select
                value={minSamples}
                onChange={(e) => setMinSamples(parseInt(e.target.value))}
                className="bg-white border border-slate-300 rounded px-1.5 py-0.5 font-bold text-slate-800"
              >
                <option value={2}>2</option>
                <option value={3}>3</option>
                <option value={4}>4</option>
                <option value={5}>5</option>
              </select>
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
            <span className="text-xs text-slate-500 font-medium">Tỷ Lệ Phủ Định Vị GPS</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${gps_coverage_pct >= 80 ? 'text-emerald-600' : 'text-amber-600'}`}>
                {gps_coverage_pct}%
              </span>
              <span className="text-xs text-slate-500">({summary.total_gps_points}/{summary.total_responses})</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${gps_coverage_pct}%` }} />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Cụm Mật Độ Tĩnh (Coffee-Shop)</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${summary.clusters_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {summary.clusters_count}
              </span>
              <span className="text-xs text-slate-500">cụm ({summary.suspicious_nodes_count} phiếu)</span>
            </div>
            <span className="text-[11px] text-slate-400 block mt-1">Bán kính ε = {epsMeters}m</span>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Vận Tốc Bất Thường (&gt; 120 km/h)</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${summary.speed_anomalies_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {summary.speed_anomalies_count}
              </span>
              <span className="text-xs text-slate-500">lần dịch chuyển</span>
            </div>
            <span className="text-[11px] text-slate-400 block mt-1">Nghi ngờ Fake GPS</span>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Độ Phân Tán Chuẩn (SDD)</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-slate-900">
                {dispersion.standard_distance_km} km
              </span>
            </div>
            <span className="text-[11px] text-indigo-600 font-medium truncate block mt-1" title={dispersion.territory_spread}>
              {dispersion.territory_spread}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs Switcher */}
      <div className="px-6 border-b border-slate-200 flex items-center gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('clusters')}
          className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
            activeTab === 'clusters'
              ? 'border-emerald-600 text-emerald-600 font-semibold'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Cụm Mật Độ Tĩnh (DBSCAN)</span>
          {clusters.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-700">
              {clusters.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('speed')}
          className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
            activeTab === 'speed'
              ? 'border-emerald-600 text-emerald-600 font-semibold'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Vận Tốc Bất Khả Thi (Teleportation)</span>
          {speed_anomalies.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-800">
              {speed_anomalies.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('map')}
          className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
            activeTab === 'map'
              ? 'border-emerald-600 text-emerald-600 font-semibold'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <MapPin className="w-4 h-4" />
          <span>Bản Đồ Điểm Tọa Độ Thực Địa</span>
          <span className="text-xs text-slate-400">({gps_points.length} điểm)</span>
        </button>
      </div>

      {/* Tab 1: DBSCAN Clusters */}
      {activeTab === 'clusters' && (
        <div className="p-6 space-y-4">
          {clusters.length === 0 ? (
            <div className="py-12 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
              <h4 className="font-semibold text-slate-800 text-base">Tọa Độ Thu Thập Phân Tán Độc Lập</h4>
              <p className="text-sm text-slate-500 mt-1 max-w-lg mx-auto">
                Không ghi nhận cụm phản hồi nào tụ tập mật độ bất thường trong bán kính {epsMeters}m. Dữ liệu thực địa đạt độ tản tự nhiên theo tiêu chuẩn ISO 20252.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {clusters.map((c) => (
                <div
                  key={c.cluster_id}
                  className={`border rounded-xl p-5 transition shadow-xs ${
                    c.threat_level === 'CRITICAL'
                      ? 'border-rose-300 bg-rose-50/40'
                      : c.threat_level === 'HIGH'
                      ? 'border-amber-300 bg-amber-50/40'
                      : 'border-slate-300 bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${
                        c.threat_level === 'CRITICAL'
                          ? 'bg-rose-600 text-white'
                          : c.threat_level === 'HIGH'
                          ? 'bg-amber-600 text-white'
                          : 'bg-slate-700 text-white'
                      }`}>
                        {c.cluster_id.replace('GEO-CLUSTER-', 'C')}
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>{c.member_count} Phiếu tại chỗ</span>
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                            c.threat_level === 'CRITICAL'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : 'bg-amber-100 text-amber-800 border border-amber-200'
                          }`}>
                            {c.threat_level}
                          </span>
                        </h4>
                        <span className="text-xs text-slate-500">
                          Tâm: {c.center_lat}, {c.center_lon} (Bán kính: <strong className="text-slate-800">{c.radius_meters}m</strong>)
                        </span>
                      </div>
                    </div>

                    {c.response_ids.length >= 2 && (
                      <a
                        href={`/surveys/${surveyId}/compare?id1=${c.response_ids[0]}&id2=${c.response_ids[1]}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2.5 py-1 text-xs font-semibold rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 flex items-center gap-1 transition"
                      >
                        <GitCompare className="w-3.5 h-3.5" />
                        So sánh cặp
                      </a>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 mt-3.5">
                    {c.is_suspicious_coffee_shop && (
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
                        Nghi vấn ngồi quán cà phê khai khống
                      </span>
                    )}
                    {c.enumerators_involved.length > 0 && (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        ĐTV: {c.enumerators_involved.join(', ')}
                      </span>
                    )}
                    {c.time_span_seconds > 0 && (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        Thời lượng: {Math.round(c.time_span_seconds / 60)} phút
                      </span>
                    )}
                  </div>

                  {/* List of Member response IDs */}
                  <div className="mt-3 bg-white/80 p-2.5 rounded-lg border border-slate-200/80">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                      Danh sách phản hồi trong cụm:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {c.response_ids.map((rid) => (
                        <a
                          key={rid}
                          href={`/surveys/${surveyId}/responses/${rid}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-0.5 rounded font-mono text-xs bg-slate-100 text-slate-700 hover:bg-emerald-100 hover:text-emerald-800 transition flex items-center gap-1"
                        >
                          {rid.slice(0, 8)}...
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      ))}
                    </div>
                  </div>

                  {/* Recommended Action */}
                  <div className="mt-3 flex items-start gap-2 text-xs text-slate-700 bg-white/60 p-2.5 rounded-lg border border-slate-200/60">
                    <Info className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-semibold text-slate-900">Khuyến nghị xử lý: </strong>
                      {c.recommended_action}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Speed Anomalies */}
      {activeTab === 'speed' && (
        <div className="overflow-x-auto">
          {speed_anomalies.length === 0 ? (
            <div className="py-12 text-center bg-slate-50">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm text-slate-600 font-medium">
                Không ghi nhận vận tốc di chuyển bất khả thi giữa các lần nộp (&gt; 120 km/h).
              </p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Điều Tra Viên / Thiết Bị</th>
                  <th className="py-3 px-4">Vận Tốc Tính Toán</th>
                  <th className="py-3 px-4">Khoảng Cách & Thời Gian</th>
                  <th className="py-3 px-4">Cặp Phản Hồi</th>
                  <th className="py-3 px-4">Đánh Giá Nguy Cơ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {speed_anomalies.map((anom, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4 font-medium text-slate-900">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-rose-600" />
                        <span className="font-mono text-xs">{anom.actor_id}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 font-mono font-bold text-rose-600">
                      {anom.speed_kmh} km/h
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-600">
                      <div>Cách nhau {anom.distance_km} km</div>
                      <div className="text-slate-400">trong {anom.time_delta_seconds} giây</div>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-xs">
                      <div className="flex items-center gap-1.5">
                        <a
                          href={`/surveys/${surveyId}/responses/${anom.response_id_from}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 hover:text-emerald-600"
                        >
                          {anom.response_id_from.slice(0, 8)}
                        </a>
                        <span>→</span>
                        <a
                          href={`/surveys/${surveyId}/responses/${anom.response_id_to}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 hover:text-emerald-600"
                        >
                          {anom.response_id_to.slice(0, 8)}
                        </a>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                        Nghi ngờ Fake GPS / Dịch chuyển tức thời
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab 3: Interactive SVG Spatial Map */}
      {activeTab === 'map' && (
        <div className="p-6">
          <div className="flex items-center justify-between mb-3 text-xs text-slate-500">
            <span>Sơ đồ phân tán tọa độ GPS thực địa. Điểm đỏ biểu thị phản hồi trong cụm mật độ tĩnh (DBSCAN).</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span> Phân tán tự nhiên
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-rose-600 inline-block"></span> Cụm tĩnh nghi vấn
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full border-2 border-indigo-600 border-dashed inline-block"></span> Bán kính chuẩn (SDD)
              </span>
            </div>
          </div>

          <div className="bg-slate-900 rounded-xl overflow-hidden relative border border-slate-800 shadow-inner">
            <svg viewBox="0 0 600 350" className="w-full h-80 select-none">
              {/* Background grid */}
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#334155" strokeWidth="0.5" />
                </pattern>
              </defs>
              <rect width="600" height="350" fill="#0f172a" />
              <rect width="600" height="350" fill="url(#grid)" />

              {/* Mean Center Crosshair */}
              {bBox && (
                (() => {
                  const center = getSvgCoords(dispersion.center_lat, dispersion.center_lon);
                  return (
                    <g>
                      <circle
                        cx={center.x}
                        cy={center.y}
                        r="35"
                        fill="none"
                        stroke="#6366f1"
                        strokeWidth="1.5"
                        strokeDasharray="4 3"
                        opacity="0.6"
                      />
                      <line x1={center.x - 12} y1={center.y} x2={center.x + 12} y2={center.y} stroke="#818cf8" strokeWidth="1.5" />
                      <line x1={center.x} y1={center.y - 12} x2={center.x} y2={center.y + 12} stroke="#818cf8" strokeWidth="1.5" />
                      <text x={center.x + 8} y={center.y - 8} fill="#a5b4fc" fontSize="9" fontFamily="monospace">
                        Tâm SDD
                      </text>
                    </g>
                  );
                })()
              )}

              {/* Data points */}
              {gps_points.map((p) => {
                const coord = getSvgCoords(p.lat, p.lon);
                const isClustered = p.is_clustered;
                return (
                  <g
                    key={p.id}
                    onMouseEnter={() => setHoveredPoint(p)}
                    onMouseLeave={() => setHoveredPoint(null)}
                    className="cursor-pointer"
                  >
                    {isClustered && (
                      <circle
                        cx={coord.x}
                        cy={coord.y}
                        r="9"
                        fill="#f43f5e"
                        opacity="0.3"
                        className="animate-pulse"
                      />
                    )}
                    <circle
                      cx={coord.x}
                      cy={coord.y}
                      r={isClustered ? 5 : 4}
                      fill={isClustered ? '#e11d48' : '#10b981'}
                      stroke="#ffffff"
                      strokeWidth="1.2"
                    />
                  </g>
                );
              })}
            </svg>

            {/* Hover details tooltip */}
            {hoveredPoint && (
              <div className="absolute bottom-3 left-3 bg-slate-800/95 backdrop-blur text-white p-3 rounded-lg border border-slate-700 text-xs shadow-lg animate-in fade-in max-w-xs">
                <div className="flex items-center justify-between gap-2 border-b border-slate-700 pb-1.5 mb-1.5">
                  <span className="font-mono font-bold text-emerald-400">
                    ID: {hoveredPoint.id.slice(0, 8)}
                  </span>
                  <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                    hoveredPoint.is_clustered ? 'bg-rose-900/80 text-rose-300' : 'bg-emerald-900/80 text-emerald-300'
                  }`}>
                    {hoveredPoint.is_clustered ? 'Cụm tĩnh' : 'Độc lập'}
                  </span>
                </div>
                <div className="text-slate-300 space-y-0.5 font-mono text-[11px]">
                  <div>Tọa độ: {hoveredPoint.lat}, {hoveredPoint.lon}</div>
                  {hoveredPoint.enumerator_id && <div>ĐTV: {hoveredPoint.enumerator_id}</div>}
                  <div>Thời gian: {hoveredPoint.submitted_at?.slice(11, 19)}</div>
                  <div>Chất lượng: {hoveredPoint.quality_score}/100</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* APA / ISO 20252 Academic Audit Paragraph */}
      <div className="p-6 bg-slate-50 border-t border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Trích dẫn kiểm toán thực địa (ISO 20252:2019 §4.5.3 & AAPOR Verification)</span>
          </div>
          <button
            onClick={handleCopyNarrative}
            className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 font-medium transition"
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
