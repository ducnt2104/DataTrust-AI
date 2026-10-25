import React, { useState, useEffect, useMemo } from 'react';
import {
  Scale,
  Zap,
  Target,
  Activity,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Copy,
  Check,
  RefreshCw,
  Info,
  ChevronDown,
  ChevronUp,
  Sparkles,
  HelpCircle,
  TrendingUp,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { api } from '../api/client';
import { PowerAnalysisReport, PowerCurvePoint } from '../types/survey';

interface Props {
  surveyId: string;
}

export const SamplePowerAnalysisCard: React.FC<Props> = ({ surveyId }) => {
  const [report, setReport] = useState<PowerAnalysisReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Configuration controls
  const [scope, setScope] = useState<'verified_clean' | 'all'>('verified_clean');
  const [analysisType, setAnalysisType] = useState<'ttest' | 'correlation'>('ttest');
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95);
  const [marginOfError, setMarginOfError] = useState<number>(0.05);
  const [populationSize, setPopulationSize] = useState<string>('');
  const [effectSize, setEffectSize] = useState<number>(0.50);
  const [targetPower, setTargetPower] = useState<number>(0.80);
  const [alpha, setAlpha] = useState<number>(0.05);

  const [isParamsOpen, setIsParamsOpen] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    loadPowerAnalysis();
  }, [surveyId, scope, analysisType, confidenceLevel, marginOfError, populationSize, effectSize, targetPower, alpha]);

  const loadPowerAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const popNum = populationSize.trim() ? parseInt(populationSize.trim(), 10) : undefined;
      const data = await api.runPowerAnalysis(surveyId, {
        analysis_type: analysisType,
        confidence_level: confidenceLevel,
        margin_of_error: marginOfError,
        population_size: popNum && !isNaN(popNum) ? popNum : undefined,
        effect_size: effectSize,
        target_power: targetPower,
        alpha,
        scope
      });
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'Không thể tính toán lực thống kê.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!report?.adequacy.apa_narrative) return;
    navigator.clipboard.writeText(report.adequacy.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  // Generate SVG path for Power Curve
  const svgCurveData = useMemo(() => {
    if (!report || !report.power_curve || report.power_curve.length === 0) return null;

    const width = 580;
    const height = 180;
    const padding = { top: 20, right: 30, bottom: 30, left: 45 };

    const pts = report.power_curve;
    const minN = pts[0].n;
    const maxN = pts[pts.length - 1].n;

    const scaleX = (n: number) => padding.left + ((n - minN) / (maxN - minN)) * (width - padding.left - padding.right);
    const scaleY = (pwr: number) => height - padding.bottom - (pwr / 1.0) * (height - padding.top - padding.bottom);

    const pathD = pts.reduce((acc, pt, idx) => {
      const x = scaleX(pt.n);
      const y = scaleY(pt.power);
      return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');

    // Current N point
    const currN = report.current_sample_size;
    const currentPoint = pts.find(p => p.n >= currN) || pts[pts.length - 1];
    const currX = scaleX(Math.min(maxN, Math.max(minN, currN)));
    const currY = scaleY(currentPoint ? currentPoint.power : 0.8);

    // Target 80% line Y
    const y80 = scaleY(targetPower);

    return {
      width,
      height,
      padding,
      pathD,
      y80,
      currX,
      currY,
      currN,
      minN,
      maxN
    };
  }, [report, targetPower]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700">
            <Zap className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-extrabold text-slate-900 text-base">
                Kiểm Định Lực Thống Kê & Cỡ Mẫu (Statistical Power Analysis)
              </h3>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-wider border border-indigo-200">
                Cohen (1988) & Cochran (1977)
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Đánh giá Post-Hoc Power cho mẫu hiện tại, tính cỡ mẫu Cochran với hiệu chỉnh FPC, và vẽ đường cong độ nhạy
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {/* Scope Toggle */}
          <div className="flex items-center p-0.5 bg-slate-100 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setScope('verified_clean')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                scope === 'verified_clean'
                  ? 'bg-white text-indigo-900 shadow-2xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Chỉ tính trên các phản hồi hợp lệ đã thẩm định"
            >
              Hợp lệ
            </button>
            <button
              onClick={() => setScope('all')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                scope === 'all'
                  ? 'bg-white text-indigo-900 shadow-2xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Bao gồm toàn bộ phản hồi thô"
            >
              Tất cả
            </button>
          </div>

          <button
            onClick={() => setIsParamsOpen(!isParamsOpen)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-all"
          >
            <span>Tham số</span>
            {isParamsOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={loadPowerAnalysis}
            className="p-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
            title="Tính toán lại lực thống kê"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Config Drawer */}
      {isParamsOpen && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-slate-200/60 pb-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Tùy Chỉnh Giả Định Nghiên Cứu (A Priori Assumptions)
            </span>
            <span className="text-[11px] text-slate-500">
              Chuẩn mực: Mức ý nghĩa &alpha; = 0.05, Lực mục tiêu 1 - &beta; = 0.80
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Loại kiểm định mục tiêu:</label>
              <select
                value={analysisType}
                onChange={(e) => setAnalysisType(e.target.value as any)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white font-medium text-slate-800 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="ttest">T-Test 2 Nhóm (Cohen's d)</option>
                <option value="correlation">Tương quan Pearson r</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Độ tin cậy (1 - &alpha;):</label>
              <select
                value={confidenceLevel}
                onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white font-medium text-slate-800 focus:ring-2 focus:ring-indigo-500"
              >
                <option value={0.90}>90% (Z = 1.645)</option>
                <option value={0.95}>95% (Z = 1.960)</option>
                <option value={0.99}>99% (Z = 2.576)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Biên độ sai số mong muốn (e):</label>
              <select
                value={marginOfError}
                onChange={(e) => setMarginOfError(parseFloat(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white font-medium text-slate-800 focus:ring-2 focus:ring-indigo-500"
              >
                <option value={0.03}>&plusmn;3% (Nghiên cứu quy mô lớn)</option>
                <option value={0.05}>&plusmn;5% (Chuẩn Don Dillman)</option>
                <option value={0.08}>&plusmn;8% (Khảo sát sơ bộ)</option>
                <option value={0.10}>&plusmn;10% (Pilot Study)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Quy mô tổng thể (FPC):</label>
              <input
                type="number"
                placeholder="Để trống nếu vô hạn"
                value={populationSize}
                onChange={(e) => setPopulationSize(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white font-medium text-slate-800 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      {loading && !report && (
        <div className="p-8 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 text-indigo-600 animate-spin" />
          <span>Đang tính toán lực thống kê và kiểm định cỡ mẫu...</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
          <AlertOctagon className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {report && (
        <div className="space-y-6">
          {/* 4 Hero KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {/* Card 1: Sample Size & Status */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Cỡ Mẫu Hiện Tại (N)
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                    report.adequacy.status === 'ADEQUATE'
                      ? 'bg-emerald-100 text-emerald-800'
                      : report.adequacy.status === 'MODERATE'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {report.adequacy.status}
                </span>
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900 tracking-tight">
                  {report.current_sample_size}
                </span>
                <span className="text-xs text-slate-500 font-medium">phản hồi</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                {report.adequacy.rating}
              </p>
            </div>

            {/* Card 2: Achieved Margin of Error */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                Biên Độ Sai Số Đạt Được
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-indigo-700 tracking-tight">
                  {report.adequacy.achieved_margin_of_error_pct}
                </span>
                <span className="text-xs text-slate-500 font-medium">ở 95% CI</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                Mục tiêu Cochran: {report.cochran_estimation.margin_of_error_pct}
              </p>
            </div>

            {/* Card 3: Post-Hoc Power for Medium Effect */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                Lực Thống Kê (Medium Effect)
              </span>
              <div className="flex items-baseline gap-1.5">
                <span
                  className={`text-2xl font-black tracking-tight ${
                    report.adequacy.ttest_power.medium_d_05 >= 0.80
                      ? 'text-emerald-600'
                      : report.adequacy.ttest_power.medium_d_05 >= 0.50
                      ? 'text-amber-600'
                      : 'text-red-600'
                  }`}
                >
                  {(report.adequacy.ttest_power.medium_d_05 * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-500 font-medium">
                  {report.adequacy.ttest_power.medium_d_05 >= 0.80 ? '(Đạt chuẩn ≥ 80%)' : '(Chưa đạt)'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                Hiệu ứng lớn (d = 0.8): {(report.adequacy.ttest_power.large_d_08 * 100).toFixed(1)}%
              </p>
            </div>

            {/* Card 4: Recommended Sample Size */}
            <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 space-y-1">
              <span className="text-[11px] font-bold text-indigo-900 uppercase tracking-wider block">
                Khuyến Nghị Cochran (1977)
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-indigo-950 tracking-tight">
                  {report.cochran_estimation.required_sample_size}
                </span>
                <span className="text-xs text-indigo-700 font-medium">mẫu tối thiểu</span>
              </div>
              <p className="text-[11px] text-indigo-800 leading-tight">
                {report.cochran_estimation.fpc_applied ? 'Đã hiệu chỉnh FPC theo quy mô dân số' : 'Tổng thể vô hạn chuẩn Don Dillman'}
              </p>
            </div>
          </div>

          {/* Power Curve SVG Visualization */}
          {svgCurveData && (
            <div className="p-5 rounded-xl bg-slate-900 text-white space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-amber-400" />
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-200">
                    Đường Cong Lực Thống Kê (Statistical Power Curve vs Sample Size N)
                  </h4>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-0.5 bg-red-400 border-dashed" /> Ngưỡng chuẩn 80% (Cohen)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Mẫu thực tế (N = {report.current_sample_size})
                  </span>
                </div>
              </div>

              {/* Vector SVG */}
              <div className="w-full overflow-x-auto flex justify-center py-2">
                <svg
                  viewBox={`0 0 ${svgCurveData.width} ${svgCurveData.height}`}
                  className="w-full max-w-2xl h-auto"
                >
                  {/* Grid lines */}
                  <line
                    x1={svgCurveData.padding.left}
                    y1={svgCurveData.y80}
                    x2={svgCurveData.width - svgCurveData.padding.right}
                    y2={svgCurveData.y80}
                    stroke="#f87171"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={svgCurveData.width - svgCurveData.padding.right - 5}
                    y={svgCurveData.y80 - 6}
                    fill="#f87171"
                    fontSize="10"
                    textAnchor="end"
                    fontWeight="bold"
                  >
                    Target 80% Power
                  </text>

                  {/* Axis lines */}
                  <line
                    x1={svgCurveData.padding.left}
                    y1={svgCurveData.height - svgCurveData.padding.bottom}
                    x2={svgCurveData.width - svgCurveData.padding.right}
                    y2={svgCurveData.height - svgCurveData.padding.bottom}
                    stroke="#475569"
                    strokeWidth="1"
                  />
                  <line
                    x1={svgCurveData.padding.left}
                    y1={svgCurveData.padding.top}
                    x2={svgCurveData.padding.left}
                    y2={svgCurveData.height - svgCurveData.padding.bottom}
                    stroke="#475569"
                    strokeWidth="1"
                  />

                  {/* Y Axis Labels */}
                  <text x={svgCurveData.padding.left - 8} y={svgCurveData.padding.top + 5} fill="#94a3b8" fontSize="10" textAnchor="end">
                    100%
                  </text>
                  <text x={svgCurveData.padding.left - 8} y={svgCurveData.y80 + 3} fill="#94a3b8" fontSize="10" textAnchor="end">
                    80%
                  </text>
                  <text x={svgCurveData.padding.left - 8} y={svgCurveData.height - svgCurveData.padding.bottom} fill="#94a3b8" fontSize="10" textAnchor="end">
                    0%
                  </text>

                  {/* X Axis Labels */}
                  <text x={svgCurveData.padding.left} y={svgCurveData.height - svgCurveData.padding.bottom + 16} fill="#94a3b8" fontSize="10" textAnchor="middle">
                    {svgCurveData.minN}
                  </text>
                  <text x={svgCurveData.width - svgCurveData.padding.right} y={svgCurveData.height - svgCurveData.padding.bottom + 16} fill="#94a3b8" fontSize="10" textAnchor="middle">
                    {svgCurveData.maxN}
                  </text>

                  {/* Curve Line */}
                  <path
                    d={svgCurveData.pathD}
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  {/* Current N vertical line and marker */}
                  <line
                    x1={svgCurveData.currX}
                    y1={svgCurveData.currY}
                    x2={svgCurveData.currX}
                    y2={svgCurveData.height - svgCurveData.padding.bottom}
                    stroke="#34d399"
                    strokeWidth="1.5"
                    strokeDasharray="2 2"
                  />
                  <circle
                    cx={svgCurveData.currX}
                    cy={svgCurveData.currY}
                    r="5"
                    fill="#34d399"
                    stroke="#064e3b"
                    strokeWidth="2"
                  />
                  <text
                    x={svgCurveData.currX}
                    y={svgCurveData.currY - 10}
                    fill="#34d399"
                    fontSize="11"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    N={report.current_sample_size}
                  </text>
                </svg>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative Summary Box */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                <span>Đoạn Trích Dẫn Học Thuật Báo Cáo (APA 7th Edition Statement)</span>
              </span>
              <button
                onClick={handleCopyAPA}
                className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
                title="Sao chép đoạn trích dẫn APA vào bộ nhớ tạm"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Đã sao chép!' : 'Sao chép APA'}</span>
              </button>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed italic bg-white p-3 rounded-lg border border-slate-200 font-serif">
              "{report.adequacy.apa_narrative}"
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
