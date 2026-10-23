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
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { Survey, EnumeratorAnalytics, EnumeratorMetrics } from '../types/survey';

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

  useEffect(() => {
    loadData();
  }, [surveyId]);

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

        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium self-start md:self-auto transition-all"
        >
          <RefreshCw className="w-4 h-4" /> Làm mới số liệu
        </button>
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
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
            {totalAnomalies > 0 ? 'Cần giám sát viên hậu kiểm lô phiếu' : 'Không có dấu hiệu bất thường'}
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Nguyên tắc kiểm soát</span>
            <CheckCircle className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="text-sm font-medium text-slate-700 leading-snug mt-1">
            Chỉ số Z-score variance & Tỷ lệ High-Risk theo AAPOR 2003
          </div>
        </div>
      </div>

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
                <th className="py-3.5 px-4 text-center">Đánh giá</th>
                <th className="py-3.5 px-4">Lý do cảnh báo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {filteredEnumerators.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
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
                    <td className="py-4 px-4 font-mono font-bold text-slate-900">
                      {e.enumerator_id}
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
    </div>
  );
}
