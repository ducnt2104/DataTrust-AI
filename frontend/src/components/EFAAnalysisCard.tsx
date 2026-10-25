import React, { useEffect, useState } from 'react';
import {
  Layers,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  Info,
  TrendingUp,
  Sparkles,
  BarChart2,
  FileSpreadsheet,
  CheckCircle,
  HelpCircle
} from 'lucide-react';
import { api } from '../api/client';
import { EFAReport } from '../types/survey';

interface Props {
  surveyId: string;
}

export const EFAAnalysisCard: React.FC<Props> = ({ surveyId }) => {
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [rotation, setRotation] = useState<'varimax' | 'none'>('varimax');
  const [data, setData] = useState<EFAReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getExploratoryFactorAnalysis(surveyId, scope, rotation);
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Không thể tải phân tích nhân tố khám phá EFA.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [surveyId, scope, rotation]);

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
        <span>Đang tính toán phân rã trị riêng Jacobi & phép xoay Varimax...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-2 text-rose-600 text-xs font-semibold">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error || 'Lỗi không xác định khi chạy phân tích EFA.'}</span>
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
            <h4 className="text-sm font-semibold text-slate-900">Chưa đủ biến thang đo để chạy EFA</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              {data.message || 'Phân tích nhân tố khám phá (EFA) cần ít nhất 3 biến thang đo định lượng (Rating, Linear Scale, NPS, Likert) để tìm cấu trúc ẩn.'}
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
            <h4 className="text-sm font-semibold text-slate-900">Cỡ mẫu chưa đạt chuẩn phân tích EFA</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              {data.message || 'Cỡ mẫu hợp lệ cần đạt tối thiểu N >= 10 hoặc gấp đôi số biến quan sát để đảm bảo độ tin cậy của ma trận tương quan R.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const sampleSize = data.sample_size || 0;
  const kmo = data.kmo_overall || 0;
  const kmoVerdict = data.kmo_verdict || '';
  const isKmoOk = data.is_kmo_acceptable ?? false;
  const bartlettChi2 = data.bartlett_chi2 || 0;
  const bartlettDf = data.bartlett_df || 0;
  const bartlettP = data.bartlett_p_value || 0;
  const isBartlettSig = data.is_bartlett_significant ?? false;
  const factorsCount = data.factors_extracted_count || 1;
  const cumVarPct = data.cumulative_variance_extracted_pct || 0;
  const isVarOk = data.is_variance_sufficient ?? false;

  // Xử lý dữ liệu Scree Plot cho SVG
  const screeData = data.scree_plot_data || [];
  const maxEigen = Math.max(1.5, ...screeData.map(d => d.eigenvalue));
  const svgWidth = 520;
  const svgHeight = 160;
  const paddingX = 40;
  const paddingY = 25;
  const plotW = svgWidth - paddingX * 2;
  const plotH = svgHeight - paddingY * 2;

  const getX = (idx: number) => {
    if (screeData.length <= 1) return paddingX + plotW / 2;
    return paddingX + (idx / (screeData.length - 1)) * plotW;
  };
  const getY = (val: number) => {
    return paddingY + plotH - (val / maxEigen) * plotH;
  };

  const linePoints = screeData
    .map((d, i) => `${getX(i)},${getY(d.eigenvalue)}`)
    .join(' ');

  const kaiserY = getY(1.0);

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Top Header */}
      <div className="p-6 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="p-1.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <Layers className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold tracking-tight text-white">
              Phân Tích Nhân Tố Khám Phá (EFA &amp; Scree Plot)
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-400/20 text-[10px] font-medium">
              Kaiser (1974) • Cattell (1966) • Hair et al. (2010)
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
            Kiểm định tính phù hợp dữ liệu (KMO &amp; Bartlett), phân rã trị riêng thành phần chính, 
            và nhận diện cấu trúc nhân tố ẩn qua phép xoay trực giao Varimax.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center flex-wrap">
          {/* Scope Selector */}
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
              Đã làm sạch
            </button>
          </div>

          {/* Rotation Toggle */}
          <div className="inline-flex rounded-xl bg-slate-800/80 p-0.5 border border-slate-700/60 text-xs">
            <button
              onClick={() => setRotation('varimax')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                rotation === 'varimax'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Xoay Varimax
            </button>
            <button
              onClick={() => setRotation('none')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                rotation === 'none'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Chưa xoay
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

      {/* 4 Hero KPI Cards */}
      <div className="p-6 border-b border-slate-100 bg-slate-50/50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Hệ Số KMO</span>
              {isKmoOk ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              )}
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1.5">
              <span>{kmo.toFixed(3)}</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1.5">
              <span className={`font-semibold ${isKmoOk ? 'text-emerald-600' : 'text-amber-600'}`}>
                {kmoVerdict}
              </span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Kiểm Định Bartlett</span>
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              χ² = {bartlettChi2.toFixed(1)}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              df = {bartlettDf} | p {bartlettP < 0.001 ? '< .001' : `= ${bartlettP.toFixed(3)}`}
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Nhân Tố Trích Xuất (m)</span>
              <Layers className="w-3.5 h-3.5 text-indigo-600" />
            </div>
            <div className="text-2xl font-black text-indigo-600 tracking-tight">
              {factorsCount} <span className="text-xs font-normal text-slate-500">nhân tố</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Tiêu chuẩn Kaiser: λ &gt; 1.0
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Phương Sai Trích Lũy Kế</span>
              <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
              <span>{cumVarPct.toFixed(1)}%</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              {isVarOk ? (
                <span className="text-emerald-600 font-semibold">Đạt chuẩn &ge; 50% (Hair et al.)</span>
              ) : (
                <span className="text-amber-600 font-semibold">Chưa đạt ngưỡng 50%</span>
              )}
            </div>
          </div>
        </div>

        {/* Scree Plot Chart (Cattell 1966) */}
        <div className="mt-5 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-800 mb-2">
            <div className="flex items-center gap-1.5">
              <BarChart2 className="w-4 h-4 text-indigo-600" />
              <span>Biểu Đồ Scree Plot (Cattell 1966) &amp; Điểm Gãy Trị Riêng (Elbow Criterion)</span>
            </div>
            <span className="text-[11px] text-slate-500 font-normal">
              Đường nét đứt màu đỏ thể hiện ngưỡng Kaiser (Eigenvalue = 1.0)
            </span>
          </div>

          <div className="w-full overflow-x-auto flex justify-center py-2">
            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full max-w-2xl h-auto overflow-visible select-none"
            >
              {/* Trục hoành & trục tung */}
              <line
                x1={paddingX}
                y1={paddingY + plotH}
                x2={paddingX + plotW}
                y2={paddingY + plotH}
                stroke="#cbd5e1"
                strokeWidth="1.5"
              />
              <line
                x1={paddingX}
                y1={paddingY}
                x2={paddingX}
                y2={paddingY + plotH}
                stroke="#cbd5e1"
                strokeWidth="1.5"
              />

              {/* Đường ngưỡng Kaiser = 1.0 */}
              <line
                x1={paddingX}
                y1={kaiserY}
                x2={paddingX + plotW}
                y2={kaiserY}
                stroke="#f43f5e"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />
              <text
                x={paddingX + plotW - 4}
                y={kaiserY - 5}
                textAnchor="end"
                className="text-[9px] fill-rose-500 font-bold"
              >
                Ngưỡng Kaiser λ = 1.0
              </text>

              {/* Đường biểu diễn Scree Curve */}
              {screeData.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#4f46e5"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={linePoints}
                />
              )}

              {/* Các điểm dữ liệu trị riêng */}
              {screeData.map((d, i) => {
                const cx = getX(i);
                const cy = getY(d.eigenvalue);
                const isRetained = d.eigenvalue >= 1.0;

                return (
                  <g key={i} className="group">
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isRetained ? 5 : 3.5}
                      className={`${
                        isRetained
                          ? 'fill-indigo-600 stroke-white stroke-2'
                          : 'fill-slate-400 stroke-white stroke-2'
                      } cursor-pointer transition-transform group-hover:scale-125`}
                    />
                    <text
                      x={cx}
                      y={cy - 9}
                      textAnchor="middle"
                      className="text-[9px] fill-slate-700 font-bold font-mono"
                    >
                      {d.eigenvalue.toFixed(2)}
                    </text>
                    <text
                      x={cx}
                      y={paddingY + plotH + 16}
                      textAnchor="middle"
                      className="text-[10px] fill-slate-500 font-sans"
                    >
                      F{d.factor}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </div>

      {/* Main Table: Rotated Factor Matrix & Communalities */}
      <div className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 gap-2">
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Ma Trận Hệ Số Tải Nhân Tố ({rotation === 'varimax' ? 'Xoay Trực Giao Varimax' : 'Chưa Xoay'}) &amp; Độ Chung (h²)
            </h4>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Hệ số tải |λ| &ge; 0.50 (in đậm màu chàm) thể hiện mức độ tương quan thực tiễn cao (Hair et al. 2010).
            </p>
          </div>
          {data.weak_loadings_count !== undefined && data.weak_loadings_count > 0 && (
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200/60 font-medium self-start sm:self-auto">
              {data.weak_loadings_count} mục có hệ số tải yếu (&lt; 0.40)
            </span>
          )}
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-200/80">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Câu hỏi / Biến quan sát</th>
                <th className="py-2.5 px-3 text-center">MSA</th>
                {data.factors?.map((fName, fIdx) => (
                  <th key={fIdx} className="py-2.5 px-3 text-center">
                    {fName}
                  </th>
                ))}
                <th className="py-2.5 px-3 text-center">Độ chung (h²)</th>
                <th className="py-2.5 px-3 text-center">Nhân tố chính</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans text-xs">
              {data.items?.map((item) => {
                const isGoodComm = item.communality >= 0.40;

                return (
                  <tr key={item.question_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3 font-medium text-slate-900 max-w-[280px]">
                      <div className="truncate" title={item.question_title}>
                        <span className="text-slate-400 font-mono text-[11px] mr-1">#{item.order_index}</span>
                        {item.question_title}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono text-[11px]">
                      <span className={`${item.msa_index >= 0.5 ? 'text-slate-700' : 'text-amber-600 font-bold'}`}>
                        {item.msa_index.toFixed(3)}
                      </span>
                    </td>
                    {item.factor_loadings?.map((loading, fIdx) => {
                      const absLoad = Math.abs(loading);
                      const isStrong = absLoad >= 0.50;
                      const isModerate = absLoad >= 0.40 && absLoad < 0.50;

                      return (
                        <td key={fIdx} className="py-2.5 px-3 text-center font-mono text-xs">
                          {isStrong ? (
                            <span className="inline-block px-2 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 font-bold border border-indigo-200/60">
                              {loading >= 0 ? `+${loading.toFixed(3)}` : loading.toFixed(3)}
                            </span>
                          ) : isModerate ? (
                            <span className="inline-block px-2 py-0.5 rounded-lg bg-slate-100 text-slate-800 font-medium">
                              {loading >= 0 ? `+${loading.toFixed(3)}` : loading.toFixed(3)}
                            </span>
                          ) : (
                            <span className="text-slate-400">
                              {loading >= 0 ? `+${loading.toFixed(3)}` : loading.toFixed(3)}
                            </span>
                          )}
                        </td>
                      );
                    })}
                    <td className="py-2.5 px-3 text-center font-mono text-xs">
                      <span className={`inline-block px-2 py-0.5 rounded-lg text-[11px] font-semibold ${
                        isGoodComm ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                      }`}>
                        {item.communality.toFixed(3)}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-medium text-[11px] text-slate-700">
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                        {item.primary_factor}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Rotated Factor Variance Breakdown Strip */}
        {data.rotated_factor_variance && data.rotated_factor_variance.length > 0 && (
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {data.rotated_factor_variance.map((rf) => (
              <div key={rf.factor_index} className="p-3 bg-slate-50/80 rounded-xl border border-slate-200/70 text-xs">
                <div className="font-semibold text-slate-800">{rf.factor_name}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Tổng bình phương tải: <span className="font-mono font-medium text-slate-700">{rf.ss_loadings}</span>
                </div>
                <div className="text-[11px] text-indigo-600 font-semibold mt-0.5">
                  Giải thích: {rf.variance_pct}% phương sai
                </div>
              </div>
            ))}
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
