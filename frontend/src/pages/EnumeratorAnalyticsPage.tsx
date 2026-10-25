import React, { useState, useEffect } from 'react';
import {
  Users,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  ChevronLeft,
  Search,
  Filter,
  BarChart2,
  Clock,
  ShieldAlert,
  ArrowRight,
  Download,
  MapPin,
  Navigation,
  Map,
  Compass,
  Layers,
  ExternalLink
} from 'lucide-react';
import { api } from '../api/client';
import { Survey, EnumeratorAnalytics, EnumeratorMetrics } from '../types/survey';
import { SpatialGeoAuditCard } from '../components/SpatialGeoAuditCard';

interface EnumeratorAnalyticsPageProps {
  surveyId: string;
  onNavigate: (path: string) => void;
}

export function EnumeratorAnalyticsPage({ surveyId, onNavigate }: EnumeratorAnalyticsPageProps) {
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [analytics, setAnalytics] = useState<EnumeratorAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterAnomalyOnly, setFilterAnomalyOnly] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<'table' | 'map'>('table');
  const [mapLayer, setMapLayer] = useState<'svg' | 'osm'>('svg');
  const [selectedEnumeratorId, setSelectedEnumeratorId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [surveyId]);

  useEffect(() => {
    if (analytics && analytics.enumerators.length > 0 && !selectedEnumeratorId) {
      const target = analytics.enumerators.find((e) => e.is_anomaly || (e.gps_points && e.gps_points.length > 0)) || analytics.enumerators[0];
      if (target) {
        setSelectedEnumeratorId(target.enumerator_id);
      }
    }
  }, [analytics, selectedEnumeratorId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sData, eData] = await Promise.all([
        api.getSurvey(surveyId),
        api.getEnumeratorAnalytics(surveyId)
      ]);
      setSurvey(sData);
      setAnalytics(eData);
    } catch (err: any) {
      setError(err.message || 'Không thể tải phân tích dữ liệu điều tra viên.');
    } finally {
      setLoading(false);
    }
  };

  const filteredEnumerators = (analytics?.enumerators || []).filter((e) => {
    const matchSearch = e.enumerator_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchFilter = filterAnomalyOnly ? e.is_anomaly : true;
    return matchSearch && matchFilter;
  });

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 flex flex-col items-center justify-center">
        <RefreshCw className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
        <p className="text-slate-600 font-medium">Đang tính toán phân bố thống kê và Z-score theo điều tra viên...</p>
      </div>
    );
  }

  const totalAnomalies = (analytics?.enumerators || []).filter((e) => e.is_anomaly).length;
  const gpsTrackedCount = (analytics?.enumerators || []).filter((e) => (e.gps_coverage_rate || 0) > 0).length;
  const gpsAnomalyCount = (analytics?.enumerators || []).filter((e) => e.impossible_speed_detected || e.stationary_cluster_detected).length;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/analytics`)}
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 font-medium mb-2 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> Quay lại Bảng phân tích khảo sát
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Giám Sát Bất Thường Theo Điều Tra Viên & Khu Vực
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
              Interviewer Anomaly Analysis
            </span>
          </div>
          <p className="text-slate-600 text-sm mt-1">
            Khảo sát: <strong className="text-slate-800">{survey?.title}</strong> • Kiểm định độ lệch chuẩn Z-score về phương sai câu trả lời và tỷ lệ cờ rủi ro
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
          {/* View Mode Switcher */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'table' ? 'bg-white text-indigo-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" /> Bảng Thống Kê
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'map' ? 'bg-white text-indigo-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Map className="w-3.5 h-3.5" /> Bản Đồ Thực Địa (GPS)
            </button>
          </div>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/enumerators/export`, '_blank')}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/80 rounded-lg text-sm font-semibold transition-all shadow-2xs"
          >
            <Download className="w-4 h-4" /> Xuất Báo Cáo CSV
          </button>
          <button
            onClick={loadData}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-all"
          >
            <RefreshCw className="w-4 h-4" /> Làm mới số liệu
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-600" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-xs text-red-600 hover:underline">
            Đóng
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-6">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Tổng điều tra viên</span>
            <Users className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="text-3xl font-black text-slate-900">{analytics?.total_enumerators || 0}</div>
          <p className="text-xs text-slate-500 mt-1">Cộng tác viên & kênh thu thập</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Tổng phiếu thực địa</span>
            <BarChart2 className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-3xl font-black text-slate-900">{analytics?.total_field_responses || 0}</div>
          <p className="text-xs text-slate-500 mt-1">Gồm trực tuyến và phiếu giấy OMR</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Cảnh báo bất thường</span>
            <ShieldAlert className="w-5 h-5 text-red-600" />
          </div>
          <div className="text-3xl font-black text-red-600">{totalAnomalies}</div>
          <p className="text-xs text-red-500 font-medium mt-1">
            {totalAnomalies > 0 ? 'Cần giám sát viên hậu kiểm' : 'Không có dấu hiệu bất thường'}
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Giám sát GPS</span>
            <MapPin className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="text-3xl font-black text-slate-900">
            {gpsTrackedCount}<span className="text-sm font-normal text-slate-500">/{analytics?.total_enumerators || 0}</span>
          </div>
          <p className={`text-xs font-medium mt-1 ${gpsAnomalyCount > 0 ? 'text-red-600 font-bold' : 'text-emerald-600'}`}>
            {gpsAnomalyCount > 0 ? `⚡ ${gpsAnomalyCount} ca tốc độ/cụm phi lý` : 'Tọa độ thực địa hợp lệ'}
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Nguyên tắc kiểm soát</span>
            <CheckCircle className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="text-sm font-medium text-slate-700 leading-snug mt-1">
            Z-score variance & Geofencing theo AAPOR 2003
          </div>
        </div>
      </div>

      {/* View Mode Switching: Table or Map */}
      {viewMode === 'map' ? (
        <div className="mt-8 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-slate-900">
                  Bản Đồ Lộ Trình Phỏng Vấn Thực Địa & Cụm Tọa Độ
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Kiểm định vận tốc di chuyển giữa các hộ, phát hiện GPS spoofing / teleportation và cụm tọa độ tĩnh
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Map Layer Switcher */}
              <div className="flex items-center bg-slate-100 p-0.5 rounded-xl text-xs font-semibold">
                <button
                  onClick={() => setMapLayer('svg')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${
                    mapLayer === 'svg' ? 'bg-white text-indigo-700 shadow-2xs font-bold' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Lưới SVG Offline
                </button>
                <button
                  onClick={() => setMapLayer('osm')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${
                    mapLayer === 'osm' ? 'bg-white text-indigo-700 shadow-2xs font-bold' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Bản Đồ Thực Địa (OSM)
                </button>
              </div>

              {/* Select Enumerator to inspect */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-600 shrink-0">Chọn ĐTV:</span>
                <select
                  value={selectedEnumeratorId || ''}
                  onChange={(e) => setSelectedEnumeratorId(e.target.value)}
                  className="text-xs font-semibold text-slate-800 bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 focus:border-indigo-600 focus:outline-hidden"
                >
                  {(analytics?.enumerators || []).map((e) => (
                    <option key={e.enumerator_id} value={e.enumerator_id}>
                      {e.is_anomaly ? '⚠️ ' : ''}{e.enumerator_id} ({e.gps_points?.length || 0} điểm GPS)
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Map visualization area */}
          {(() => {
            const currentEnum = (analytics?.enumerators || []).find((e) => e.enumerator_id === selectedEnumeratorId);
            const points = currentEnum?.gps_points || [];

            if (!currentEnum || !points || points.length === 0) {
              return (
                <div className="py-16 text-center text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  <MapPin className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="font-semibold text-sm">Chưa có dữ liệu tọa độ GPS cho điều tra viên này</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Dữ liệu phỏng vấn cần ghi nhận latitude/longitude từ trình duyệt hoặc thiết bị thu thập thực địa.
                  </p>
                </div>
              );
            }

            const lats = points.map((p) => p.lat);
            const lons = points.map((p) => p.lon);
            const minLat = Math.min(...lats);
            const maxLat = Math.max(...lats);
            const minLon = Math.min(...lons);
            const maxLon = Math.max(...lons);

            const latSpan = Math.max(0.0001, maxLat - minLat);
            const lonSpan = Math.max(0.0001, maxLon - minLon);

            const SVG_W = 760;
            const SVG_H = 420;
            const PAD_X = 60;
            const PAD_Y = 50;

            const projectX = (lon: number) => {
              if (lonSpan < 0.0002) return SVG_W / 2;
              return PAD_X + ((lon - minLon) / lonSpan) * (SVG_W - 2 * PAD_X);
            };

            const projectY = (lat: number) => {
              if (latSpan < 0.0002) return SVG_H / 2;
              return (SVG_H - PAD_Y) - ((lat - minLat) / latSpan) * (SVG_H - 2 * PAD_Y);
            };

            return (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* SVG Map Canvas */}
                <div className="lg:col-span-2 bg-slate-900 rounded-xl p-4 border border-slate-800 shadow-inner relative overflow-hidden flex flex-col justify-between">
                  {analytics?.geofence_setting?.enabled && (
                    <div className="flex flex-wrap items-center justify-between gap-2 p-2 rounded-lg bg-indigo-950/80 border border-indigo-800 text-[11px] text-indigo-200 mb-2">
                      <span className="flex items-center gap-1.5 font-medium">
                        <Compass className="w-3.5 h-3.5 text-indigo-400" />
                        Ranh giới khảo sát: <strong>{analytics.geofence_setting.location_name || 'Vùng khảo sát'}</strong> (Bán kính {analytics.geofence_setting.max_radius_km} km)
                      </span>
                      <span className={currentEnum.geofence_breach_count && currentEnum.geofence_breach_count > 0 ? 'text-rose-400 font-bold' : 'text-emerald-400 font-medium'}>
                        {currentEnum.geofence_breach_count && currentEnum.geofence_breach_count > 0 ? `⚠️ Có ${currentEnum.geofence_breach_count} điểm vi phạm` : '🟢 Trong phạm vi cho phép'}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2 mb-2">
                    <span className="font-mono flex items-center gap-1.5 text-indigo-400">
                      <Compass className="w-3.5 h-3.5" /> Khung tọa độ: {minLat.toFixed(4)}°N, {minLon.toFixed(4)}°E
                    </span>
                    <div className="flex items-center gap-3 text-[11px] flex-wrap">
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Bình thường</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" /> Tốc độ phi lý</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-amber-500" /> Tọa độ tĩnh</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-600 border border-rose-300" /> Vi phạm vùng</span>
                    </div>
                  </div>

                  {mapLayer === 'svg' ? (
                    <svg viewBox={`0 0 ${SVG_W} ${SVG_H}`} className="w-full h-auto">
                      <defs>
                        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                        </pattern>
                      <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 1 L 9 5 L 0 9 z" fill="#6366f1" />
                      </marker>
                      <marker id="arrow-fraud" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 1 L 9 5 L 0 9 z" fill="#f43f5e" />
                      </marker>
                    </defs>

                    <rect width={SVG_W} height={SVG_H} fill="url(#grid)" />

                    {/* Connecting path segments between consecutive interviews */}
                    {points.map((pt, idx) => {
                      if (idx === points.length - 1) return null;
                      const nextPt = points[idx + 1];
                      const x1 = projectX(pt.lon);
                      const y1 = projectY(pt.lat);
                      const x2 = projectX(nextPt.lon);
                      const y2 = projectY(nextPt.lat);
                      const isAnomaly = pt.is_speed_anomaly;

                      const midX = (x1 + x2) / 2;
                      const midY = (y1 + y2) / 2;

                      return (
                        <g key={`seg-${idx}`}>
                          <line
                            x1={x1}
                            y1={y1}
                            x2={x2}
                            y2={y2}
                            stroke={isAnomaly ? '#f43f5e' : '#6366f1'}
                            strokeWidth={isAnomaly ? 2.5 : 1.8}
                            strokeDasharray={isAnomaly ? '6 4' : undefined}
                            markerEnd={isAnomaly ? 'url(#arrow-fraud)' : 'url(#arrow)'}
                            className={isAnomaly ? 'animate-pulse' : ''}
                          />
                          {pt.speed_to_next_kmh !== undefined && pt.speed_to_next_kmh !== null && (
                            <g transform={`translate(${midX}, ${midY - 8})`}>
                              <rect
                                x="-28"
                                y="-9"
                                width="56"
                                height="18"
                                rx="4"
                                fill={isAnomaly ? '#be123c' : '#1e1b4b'}
                                stroke={isAnomaly ? '#f43f5e' : '#4338ca'}
                                strokeWidth="1"
                              />
                              <text
                                textAnchor="middle"
                                dy="3.5"
                                fontSize="9"
                                fontWeight="bold"
                                fill="#ffffff"
                                fontFamily="monospace"
                              >
                                {pt.speed_to_next_kmh} km/h
                              </text>
                            </g>
                          )}
                        </g>
                      );
                    })}

                    {/* Points */}
                    {points.map((pt, idx) => {
                      const cx = projectX(pt.lon);
                      const cy = projectY(pt.lat);
                      const isBreach = pt.is_geofence_breach;
                      const isFraud = pt.is_speed_anomaly || (pt.risk_score >= 70) || isBreach;
                      const isStationary = currentEnum?.stationary_cluster_detected;

                      return (
                        <g
                          key={`pt-${idx}`}
                          className="cursor-pointer group"
                        >
                          <title>{`Phiếu #${idx + 1} | Tọa độ: ${pt.lat}, ${pt.lon} | Rủi ro: ${pt.risk_score}${pt.distance_from_center_km !== undefined ? ` | Cách tâm: ${pt.distance_from_center_km}km` : ''}${isBreach ? ' ⚠️ (Vi phạm ranh giới)' : ''}`}</title>
                          {isBreach && (
                            <circle cx={cx} cy={cy} r="18" fill="rgba(244, 63, 94, 0.2)" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="3 2" className="animate-pulse" />
                          )}
                          {isFraud && !isBreach && (
                            <circle cx={cx} cy={cy} r="14" fill="rgba(244, 63, 94, 0.25)" className="animate-ping" />
                          )}
                          {isStationary && (
                            <circle cx={cx} cy={cy} r="16" fill="rgba(245, 158, 11, 0.2)" stroke="#f59e0b" strokeWidth="1" strokeDasharray="3 3" />
                          )}

                          <circle
                            cx={cx}
                            cy={cy}
                            r={isFraud ? '7' : '6'}
                            fill={isBreach ? '#be123c' : isFraud ? '#f43f5e' : isStationary ? '#f59e0b' : '#10b981'}
                            stroke="#ffffff"
                            strokeWidth="2"
                          />

                          <text
                            x={cx}
                            y={cy - 10}
                            textAnchor="middle"
                            fontSize="10"
                            fontWeight="bold"
                            fill="#ffffff"
                            fontFamily="monospace"
                          >
                            #{idx + 1}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                ) : (
                  <div className="relative w-full h-[400px] rounded-lg overflow-hidden bg-slate-950 flex flex-col justify-between my-1">
                    <iframe
                      title="OpenStreetMap"
                      className="w-full h-full border-0 rounded-lg opacity-90 hover:opacity-100 transition-opacity"
                      loading="lazy"
                      src={`https://www.openstreetmap.org/export/embed.html?bbox=${minLon - 0.005}%2C${minLat - 0.005}%2C${maxLon + 0.005}%2C${maxLat + 0.005}&layer=mapnik&marker=${(minLat + maxLat) / 2}%2C${(minLon + maxLon) / 2}`}
                    />
                    <div className="absolute bottom-2 right-2 bg-slate-900/90 backdrop-blur-xs px-2.5 py-1 rounded-md text-[10px] text-slate-300 flex items-center gap-1 shadow-md">
                      <a
                        href={`https://www.openstreetmap.org/?mlat=${(minLat + maxLat) / 2}&mlon=${(minLon + maxLon) / 2}#map=16/${(minLat + maxLat) / 2}/${(minLon + maxLon) / 2}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-indigo-400 flex items-center gap-1 font-semibold"
                      >
                        <span>Mở toàn màn hình OSM</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                )}

                  <div className="text-[11px] text-slate-400 flex items-center justify-between pt-2 border-t border-slate-800">
                    <span>Tọa độ min: {minLat.toFixed(4)}, {minLon.toFixed(4)}</span>
                    <span>Tọa độ max: {maxLat.toFixed(4)}, {maxLon.toFixed(4)}</span>
                  </div>
                </div>

                {/* Side inspection list */}
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                      <Navigation className="w-3.5 h-3.5 text-indigo-600" />
                      Lộ trình: {currentEnum.enumerator_id}
                    </h4>
                    <div className="text-xs text-slate-600 space-y-1">
                      <div>• Điểm phỏng vấn ghi nhận: <strong>{points.length} điểm</strong></div>
                      <div>• Độ phủ GPS: <strong>{Math.round((currentEnum.gps_coverage_rate || 0) * 100)}%</strong></div>
                      <div>• Bán kính hồi chuyển (Rg): <strong>{currentEnum.radius_of_gyration_km !== undefined && currentEnum.radius_of_gyration_km !== null ? `${currentEnum.radius_of_gyration_km} km` : '—'}</strong></div>
                      <div>• Diện tích bao phủ: <strong>{currentEnum.spatial_coverage_sqkm !== undefined && currentEnum.spatial_coverage_sqkm !== null ? `${currentEnum.spatial_coverage_sqkm} km²` : '—'}</strong></div>
                      <div>• Vận tốc tối đa: <strong className={currentEnum.impossible_speed_detected ? 'text-rose-600 font-bold' : ''}>
                        {currentEnum.max_speed_kmh ? `${currentEnum.max_speed_kmh} km/h` : '—'}
                      </strong></div>
                      {currentEnum.anomaly_reasons.length > 0 && (
                        <div className="pt-1 border-t border-slate-200 text-rose-700 font-medium">
                          ⚠️ {currentEnum.anomaly_reasons[0]}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* List of interview timeline */}
                  <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Nhật ký điểm phỏng vấn
                    </h4>
                    {points.map((pt, i) => (
                      <div
                        key={pt.response_id || i}
                        className={`p-2.5 rounded-lg border text-xs transition-all ${
                          pt.is_geofence_breach
                            ? 'bg-rose-50 border-rose-300 text-rose-950 shadow-2xs'
                            : pt.is_speed_anomaly
                            ? 'bg-rose-50 border-rose-200 text-rose-900'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center justify-between font-semibold">
                          <span className="flex items-center gap-1">
                            Phiếu #{i + 1} ({pt.submitted_at.slice(11, 19)})
                            {pt.is_geofence_breach && (
                              <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-rose-600 text-white">Vi phạm vùng</span>
                            )}
                          </span>
                          <span className={pt.risk_score >= 70 ? 'text-rose-600 font-bold' : 'text-slate-500'}>
                            Rủi ro: {pt.risk_score}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                          Tọa độ: {pt.lat}, {pt.lon}
                          {pt.distance_from_center_km !== undefined && (
                            <span className="text-slate-400 ml-1">({pt.distance_from_center_km} km từ tâm)</span>
                          )}
                        </div>
                        {pt.speed_to_next_kmh !== undefined && pt.speed_to_next_kmh !== null && (
                          <div className={`text-[11px] mt-1 font-semibold ${pt.is_speed_anomaly ? 'text-rose-600' : 'text-indigo-600'}`}>
                            Di chuyển tới #{i + 2}: {pt.speed_to_next_kmh} km/h
                            {pt.is_speed_anomaly ? ' ⚡ (Tốc độ phi lý)' : ''}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      ) : (
        <>
          {/* Filter and Search Bar */}
          <div className="mt-8 bg-white border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Tìm theo mã điều tra viên..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={filterAnomalyOnly}
                  onChange={(e) => setFilterAnomalyOnly(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 border-slate-300 focus:ring-indigo-500"
                />
                <span className="font-medium text-slate-800">Chỉ hiện người có dấu hiệu bất thường</span>
              </label>
            </div>
          </div>

      {/* Enumerators Table */}
      <div className="mt-6 bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                <th className="py-3.5 px-4">Điều tra viên</th>
                <th className="py-3.5 px-4 text-center">Số phiếu (Online / Giấy)</th>
                <th className="py-3.5 px-4 text-center">Tốc độ TB</th>
                <th className="py-3.5 px-4 text-center">Điểm rủi ro TB</th>
                <th className="py-3.5 px-4 text-center">Tỷ lệ rủi ro cao</th>
                <th className="py-3.5 px-4 text-center">Độ lệch Z-score</th>
                <th className="py-3.5 px-4 text-center">GPS Thực Địa</th>
                <th className="py-3.5 px-4 text-center">Đánh giá</th>
                <th className="py-3.5 px-4">Lý do cảnh báo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {filteredEnumerators.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    Không tìm thấy điều tra viên nào phù hợp với bộ lọc hiện tại.
                  </td>
                </tr>
              ) : (
                filteredEnumerators.map((e) => (
                  <tr
                    key={e.enumerator_id}
                    className={`hover:bg-slate-50/80 transition-colors ${
                      e.is_anomaly ? 'bg-red-50/30' : ''
                    }`}
                  >
                    <td
                      className="py-4 px-4 font-mono font-bold text-slate-900 cursor-pointer hover:text-indigo-600 transition-colors"
                      onClick={() => {
                        setSelectedEnumeratorId(e.enumerator_id);
                        setViewMode('map');
                      }}
                      title="Nhấn để xem lộ trình chi tiết trên bản đồ GPS"
                    >
                      <span className="inline-flex items-center gap-1.5">
                        {e.enumerator_id}
                        <Map className="w-3.5 h-3.5 text-indigo-500" />
                      </span>
                    </td>

                    <td className="py-4 px-4 text-center font-medium text-slate-800">
                      <span className="font-bold">{e.total_responses}</span>{' '}
                      <span className="text-xs text-slate-500">({e.online_count}w / {e.paper_count}p)</span>
                    </td>

                    <td className="py-4 px-4 text-center text-slate-700">
                      {e.avg_duration_seconds > 0 ? `${e.avg_duration_seconds}s` : '—'}
                    </td>

                    <td className="py-4 px-4 text-center">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold font-mono ${
                          e.avg_risk_score >= 70
                            ? 'bg-red-100 text-red-800'
                            : e.avg_risk_score >= 40
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {e.avg_risk_score}
                      </span>
                    </td>

                    <td className="py-4 px-4 text-center font-semibold">
                      <span
                        className={
                          e.high_risk_rate >= 0.4
                            ? 'text-red-600'
                            : e.high_risk_rate > 0
                            ? 'text-amber-600'
                            : 'text-slate-600'
                        }
                      >
                        {(e.high_risk_rate * 100).toFixed(0)}%
                      </span>
                    </td>

                    <td className="py-4 px-4 text-center font-mono text-xs">
                      <span
                        className={
                          e.variance_z_score < -1.75
                            ? 'text-red-700 font-bold bg-red-100 px-1.5 py-0.5 rounded'
                            : 'text-slate-700'
                        }
                      >
                        Z = {e.variance_z_score}
                      </span>
                    </td>

                    <td className="py-4 px-4 text-center">
                      {e.impossible_speed_detected ? (
                        <div>
                          <span
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800"
                            title={`Tốc độ đo được: ${e.max_speed_kmh} km/h - nghi vấn GPS spoofing`}
                          >
                            <Navigation className="w-3.5 h-3.5 text-red-600 animate-pulse" /> Phi lý ({e.max_speed_kmh} km/h)
                          </span>
                          {e.radius_of_gyration_km !== undefined && e.radius_of_gyration_km !== null && (
                            <span className="text-[11px] text-slate-500 block font-mono mt-0.5">
                              Rg: {e.radius_of_gyration_km} km
                            </span>
                          )}
                        </div>
                      ) : e.stationary_cluster_detected ? (
                        <div>
                          <span
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800"
                            title="Tất cả các phiếu thực địa xuất phát từ cùng một tọa độ tĩnh"
                          >
                            <MapPin className="w-3.5 h-3.5 text-amber-600" /> Tọa độ tĩnh (&lt;5m)
                          </span>
                          {e.radius_of_gyration_km !== undefined && e.radius_of_gyration_km !== null && (
                            <span className="text-[11px] text-slate-500 block font-mono mt-0.5">
                              Rg: {e.radius_of_gyration_km} km
                            </span>
                          )}
                        </div>
                      ) : (e.gps_coverage_rate || 0) > 0 ? (
                        <div>
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700">
                            <MapPin className="w-3.5 h-3.5 text-emerald-600" /> {Math.round((e.gps_coverage_rate || 0) * 100)}% GPS
                          </span>
                          {e.radius_of_gyration_km !== undefined && e.radius_of_gyration_km !== null && (
                            <span className="text-[11px] text-slate-500 block font-mono mt-0.5">
                              Rg: {e.radius_of_gyration_km} km ({e.spatial_coverage_sqkm || 0} km²)
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">Chưa có GPS</span>
                      )}
                      {e.geofence_breach_count !== undefined && e.geofence_breach_count > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 mt-1 block">
                          ⚠️ {e.geofence_breach_count} vi phạm vùng
                        </span>
                      )}
                    </td>

                    <td className="py-4 px-4 text-center">
                      {e.is_anomaly ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800">
                          <AlertTriangle className="w-3.5 h-3.5" /> Bất thường
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                          <CheckCircle className="w-3.5 h-3.5" /> Bình thường
                        </span>
                      )}
                    </td>

                    <td className="py-4 px-4 text-xs text-slate-600">
                      {e.anomaly_reasons.length > 0 ? (
                        <ul className="list-disc list-inside text-red-700 space-y-0.5">
                          {e.anomaly_reasons.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-slate-400 italic">Không có cảnh báo</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Kiểm định Không Gian Thực Địa, DBSCAN & Geo-Fencing (ISO 20252:2019 §4.5.3) */}
      <div className="mt-8">
        <SpatialGeoAuditCard surveyId={surveyId} />
      </div>
    </>
  )}
</div>
  );
}
