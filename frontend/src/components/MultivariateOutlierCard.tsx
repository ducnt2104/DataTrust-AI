import React, { useEffect, useState } from 'react';
import {
  Crosshair,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  Info,
  ShieldAlert,
  SlidersHorizontal,
  ChevronRight,
  TrendingUp,
  FileSpreadsheet
} from 'lucide-react';
import { api } from '../api/client';
import { MultivariateOutlierReport, MultivariateOutlierItem } from '../types/survey';

interface Props {
  surveyId: string;
}

export const MultivariateOutlierCard: React.FC<Props> = ({ surveyId }) => {
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [data, setData] = useState<MultivariateOutlierReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<MultivariateOutlierItem | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getMultivariateOutliers(surveyId, scope);
      setData(res);
      if (res.outliers_summary && res.outliers_summary.length > 0) {
        setSelectedItem(res.outliers_summary[0]);
      } else {
        setSelectedItem(null);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể tải phân tích dị biệt đa biến.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [surveyId, scope]);

  const copyApa = () => {
    if (!data?.apa_interpretation) return;
    navigator.clipboard.writeText(data.apa_interpretation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex items-center justify-center py-12 text-slate-400 text-xs gap-2">
        <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <span>Đang tính toán ma trận hiệp phương sai & khoảng cách Mahalanobis...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-2 text-rose-600 text-xs font-semibold">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error || 'Lỗi không xác định khi phân tích dị biệt đa biến.'}</span>
        </div>
      </div>
    );
  }

  if (data.status === 'INSUFFICIENT_VARIABLES') {
    return (
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-2xl bg-amber-50 text-amber-600">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900">Chưa đủ biến thang đo định lượng</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              {data.message || 'Kiểm định Mahalanobis cần ít nhất 2 câu hỏi dạng thang đo (Rating, Linear Scale, NPS, Likert) để tính toán hiệp phương sai đa chiều.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (data.status === 'INSUFFICIENT_SAMPLE') {
    return (
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-2xl bg-indigo-50 text-indigo-600">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900">Cỡ mẫu chưa đạt ngưỡng phân tích đa biến</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              {data.message || 'Số lượng phản hồi hợp lệ phải lớn hơn số biến thang đo (N > p) để đảm bảo tính khả nghịch của ma trận hiệp phương sai.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const sampleSize = data.sample_size || 0;
  const df = data.degrees_of_freedom || 0;
  const totalOutliers = data.total_outliers_count || 0;
  const extremeCount = data.extreme_outliers_count || 0;
  const moderateCount = data.moderate_outliers_count || 0;
  const normalCount = Math.max(0, sampleSize - totalOutliers);
  const outlierRate = data.outlier_rate_pct || 0;

  const normalPct = sampleSize > 0 ? Math.round((normalCount / sampleSize) * 100) : 0;
  const moderatePct = sampleSize > 0 ? Math.round((moderateCount / sampleSize) * 100) : 0;
  const extremePct = sampleSize > 0 ? Math.round((extremeCount / sampleSize) * 100) : 0;

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Top Header */}
      <div className="p-6 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="p-1.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <Crosshair className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold tracking-tight text-white">
              Phát Hiện Dị Biệt Đa Biến (Mahalanobis Distance D² &amp; Chi-Square)
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-400/20 text-[10px] font-medium">
              Tabachnick &amp; Fidell (2019)
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
            Nhận diện các mẫu phản hồi dị biệt đa biến (Multivariate Outliers) có vector đánh giá bất thường 
            so với tâm phân phối dữ liệu dựa trên khoảng cách Mahalanobis và phân phối Chi-Square bậc tự do df = {df}.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center">
          <div className="inline-flex rounded-xl bg-slate-800/80 p-0.5 border border-slate-700/60 text-xs">
            <button
              onClick={() => setScope('all')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                scope === 'all'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Toàn bộ mẫu
            </button>
            <button
              onClick={() => setScope('verified_clean')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                scope === 'verified_clean'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Mẫu đã làm sạch
            </button>
          </div>
          <button
            onClick={loadData}
            title="Tải lại phân tích"
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/60"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 4 KPI Metrics */}
      <div className="p-6 border-b border-slate-100 bg-slate-50/50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Điểm Dị Biệt Đa Biến</span>
              <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1.5">
              <span>{totalOutliers}</span>
              <span className="text-xs font-semibold text-slate-400">/ {sampleSize}</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1.5">
              <span className={`font-semibold ${outlierRate > 5 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {outlierRate}%
              </span>
              <span>(Cực đoan: {extremeCount}, Vừa: {moderateCount})</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Số Biến Thang Đo (p)</span>
              <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-500" />
            </div>
            <div className="text-2xl font-black text-indigo-600 tracking-tight">
              {df} <span className="text-xs font-normal text-slate-500">biến</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Bậc tự do phân phối df = {df}
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Khoảng cách D² Trung bình</span>
              <TrendingUp className="w-3.5 h-3.5 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {data.mean_d2}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Trung vị: {data.median_d2} | Max: {data.max_d2}
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Ngưỡng Tới Hạn χ² (p &lt; .001)</span>
              <Crosshair className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {data.critical_chi2_001}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Chuẩn Tabachnick &amp; Fidell
            </div>
          </div>
        </div>

        {/* Multivariate Spectrum Bar */}
        <div className="mt-5 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2">
            <span>Phổ Phân Phối Khoảng Cách Mahalanobis (N = {sampleSize})</span>
            <span className="text-[11px] text-slate-400 font-normal">
              {normalCount} Bình thường ({normalPct}%) • {moderateCount} Bất thường vừa ({moderatePct}%) • {extremeCount} Dị biệt cực đoan ({extremePct}%)
            </span>
          </div>
          <div className="w-full h-3 rounded-full overflow-hidden flex bg-slate-100">
            <div
              style={{ width: `${normalPct}%` }}
              className="bg-emerald-500 transition-all duration-500"
              title={`Bình thường: ${normalCount} (${normalPct}%)`}
            />
            <div
              style={{ width: `${moderatePct}%` }}
              className="bg-amber-500 transition-all duration-500"
              title={`Bất thường vừa phải: ${moderateCount} (${moderatePct}%)`}
            />
            <div
              style={{ width: `${extremePct}%` }}
              className="bg-rose-500 transition-all duration-500"
              title={`Dị biệt cực đoan: ${extremeCount} (${extremePct}%)`}
            />
          </div>
          <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-500">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              <span>Bình thường (p &ge; .01)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
              <span>Bất thường vừa phải (.001 &le; p &lt; .01)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
              <span>Dị biệt cực đoan (p &lt; .001)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area: Table of Top Outliers + Vector Inspector */}
      <div className="p-6">
        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Bảng Danh Sách Các Phản Hồi Có Khoảng Cách Mahalanobis Lớn Nhất (Top Outliers)</span>
          <span className="text-[11px] font-normal text-slate-400">
            Xếp hạng theo D² giảm dần
          </span>
        </h4>

        {(!data.outliers_summary || data.outliers_summary.length === 0) ? (
          <div className="py-8 text-center text-xs text-slate-400">
            Không có phản hồi nào được tìm thấy.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Table */}
            <div className="lg:col-span-8 overflow-x-auto rounded-2xl border border-slate-200/80">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Phản hồi ID</th>
                    <th className="py-2.5 px-3 text-right">Khoảng cách D²</th>
                    <th className="py-2.5 px-3 text-right">p-value (χ²)</th>
                    <th className="py-2.5 px-3">Phân loại</th>
                    <th className="py-2.5 px-3 text-right">Thời gian</th>
                    <th className="py-2.5 px-3 text-center">Xem</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {data.outliers_summary.slice(0, 15).map((item) => {
                    const isSelected = selectedItem?.response_id === item.response_id;
                    const isExtreme = item.outlier_tier === 'Extreme Anomaly';
                    const isModerate = item.outlier_tier === 'Moderate Outlier';

                    return (
                      <tr
                        key={item.response_id}
                        onClick={() => setSelectedItem(item)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-indigo-50/70'
                            : isExtreme
                            ? 'bg-rose-50/30 hover:bg-rose-50/50'
                            : isModerate
                            ? 'bg-amber-50/20 hover:bg-amber-50/40'
                            : 'hover:bg-slate-50/60'
                        }`}
                      >
                        <td className="py-2 px-3 font-medium text-slate-900 truncate max-w-[130px]" title={item.response_id}>
                          {item.response_id.substring(0, 8)}...
                        </td>
                        <td className="py-2 px-3 text-right font-bold text-slate-900">
                          {item.d2_mahalanobis.toFixed(2)}
                        </td>
                        <td className="py-2 px-3 text-right">
                          <span className={`font-semibold ${
                            isExtreme ? 'text-rose-600' : isModerate ? 'text-amber-600' : 'text-slate-500'
                          }`}>
                            {item.p_value < 0.0001 ? '< .0001' : item.p_value.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2 px-3 font-sans">
                          {isExtreme ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-100 text-rose-700 border border-rose-200">
                              Dị biệt cực đoan
                            </span>
                          ) : isModerate ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700 border border-amber-200">
                              Bất thường vừa
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-600">
                              Bình thường
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-right text-slate-500">
                          {Math.round(item.duration_seconds)}s
                        </td>
                        <td className="py-2 px-3 text-center">
                          <button
                            type="button"
                            className="p-1 rounded-md text-slate-400 hover:text-indigo-600 transition-colors"
                          >
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Selected Observation Vector Inspector */}
            <div className="lg:col-span-4 bg-slate-50/70 p-4 rounded-2xl border border-slate-200/80">
              <h5 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>Vector Câu Trả Lời x_i</span>
                {selectedItem && (
                  <span className="font-mono text-[10px] text-indigo-600">
                    ID: {selectedItem.response_id.substring(0, 8)}
                  </span>
                )}
              </h5>

              {selectedItem ? (
                <div className="space-y-3">
                  <div className="p-3 bg-white rounded-xl border border-slate-200/80 text-xs">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-slate-500 text-[11px]">Khoảng cách D²:</span>
                      <span className="font-bold font-mono text-slate-900">{selectedItem.d2_mahalanobis}</span>
                    </div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-slate-500 text-[11px]">Độ dài khoảng cách D:</span>
                      <span className="font-semibold font-mono text-slate-900">{selectedItem.distance_d}</span>
                    </div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-slate-500 text-[11px]">Chi-Square p-value:</span>
                      <span className="font-semibold font-mono text-rose-600">{selectedItem.p_value}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500 text-[11px]">Trạng thái kiểm định:</span>
                      <span className="text-[11px] font-semibold text-slate-700">{selectedItem.review_status}</span>
                    </div>
                  </div>

                  <div className="text-[11px] font-semibold text-slate-700">
                    Chi tiết giá trị các biến thang đo:
                  </div>

                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {data.scale_variable_titles?.map((title, idx) => {
                      const val = selectedItem.answers_vector?.[idx];
                      return (
                        <div key={idx} className="bg-white p-2.5 rounded-xl border border-slate-200/70 text-xs flex items-center justify-between gap-2">
                          <span className="text-slate-600 truncate text-[11px]" title={title}>
                            {idx + 1}. {title}
                          </span>
                          <span className="font-mono font-bold px-2 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200/60 text-xs shrink-0">
                            {val !== undefined ? val : '—'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  Nhấp vào một dòng trong bảng để xem vector câu trả lời chi tiết.
                </div>
              )}
            </div>
          </div>
        )}

        {/* APA 7th Edition Academic Narrative */}
        {data.apa_interpretation && (
          <div className="mt-6 bg-slate-50 rounded-2xl p-4 border border-slate-200/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <FileSpreadsheet className="w-3.5 h-3.5 text-indigo-600" />
                Diễn Giải Học Thuật Theo Chuẩn APA 7th Edition
              </span>
              <button
                onClick={copyApa}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-100 transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-600" />
                    <span className="text-emerald-700">Đã sao chép</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 text-slate-400" />
                    <span>Sao chép trích dẫn</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed font-serif italic bg-white p-3 rounded-xl border border-slate-200/60">
              "{data.apa_interpretation}"
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
