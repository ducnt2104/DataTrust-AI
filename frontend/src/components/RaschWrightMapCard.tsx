import React, { useState, useEffect } from 'react';
import {
  SlidersHorizontal,
  Target,
  Scale,
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
  BarChart2
} from 'lucide-react';
import { api } from '../api/client';
import { RaschModelReport, RaschItemCalibration } from '../types/survey';

interface Props {
  surveyId: string;
}

export const RaschWrightMapCard: React.FC<Props> = ({ surveyId }) => {
  const [report, setReport] = useState<RaschModelReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [scope, setScope] = useState<'verified_clean' | 'all'>('verified_clean');
  const [copied, setCopied] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<RaschItemCalibration | null>(null);

  useEffect(() => {
    loadRaschAnalysis();
  }, [surveyId, scope]);

  const loadRaschAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRaschAnalysis(surveyId, scope);
      setReport(data);
      if (data.item_calibrations.length > 0) {
        setSelectedItem(data.item_calibrations[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể hiệu chuẩn mô hình Rasch 1-PL.');
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

  const targetingBadge = (evalType: string) => {
    switch (evalType) {
      case 'EXCELLENT_TARGETING':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dot: 'bg-emerald-500',
          label: 'Nhắm mục tiêu xuất sắc'
        };
      case 'QUESTIONNAIRE_TOO_EASY':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          dot: 'bg-amber-500',
          label: 'Bảng hỏi hơi dễ'
        };
      case 'QUESTIONNAIRE_TOO_DIFFICULT':
      default:
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          dot: 'bg-rose-500',
          label: 'Bảng hỏi quá khó'
        };
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-slate-100 gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-teal-50 text-teal-600 border border-teal-100 mt-0.5">
            <SlidersHorizontal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Mô Hình Đo Lường Rasch 1-PL & Bản Đồ Wright Map (Item Response Theory)
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-teal-100 text-teal-800 rounded-full uppercase tracking-wider">
                Tiêu chuẩn Viện Khảo thí Hoa Kỳ ETS & Rasch 1960
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Ước lượng độ khó câu hỏi (b_i) trên cùng trục logit với năng lực người trả lời (θ_n), đánh giá tính tương thích đo lường Infit/Outfit MNSQ (Wright & Linacre, 1994).
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
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
            onClick={loadRaschAnalysis}
            disabled={loading}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Hiệu chuẩn lại mô hình Rasch"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-teal-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start gap-2">
          <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <strong>Không thể hiệu chuẩn mô hình Rasch:</strong> {error}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && !report && (
        <div className="py-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-teal-600" />
          <span>Đang thực hiện lặp Joint Maximum Likelihood Estimation (JMLE) và xây dựng Wright Map...</span>
        </div>
      )}

      {/* Results View */}
      {report && (
        <div className="space-y-6">
          {/* 4 Hero KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Item Count & Calibration */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Quy mô thang đo Rasch
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">{report.item_count}</span>
                <span className="text-xs text-slate-500 font-medium">câu hỏi mục tiêu</span>
              </div>
              <p className="text-[11px] text-slate-500">
                N = {report.sample_size} người • {report.convergence.iterations} vòng lặp JMLE ({report.convergence.converged ? 'Hội tụ' : 'Đạt max'})
              </p>
            </div>

            {/* KPI 2: Separation Reliability */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Độ tin cậy phân tách (Reliability)
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">
                  R = {report.reliability.item_reliability}
                </span>
                <span className="text-xs text-slate-500 font-medium">Item R</span>
              </div>
              <p className="text-[11px] text-slate-500">
                Chỉ số phân tách: {report.reliability.item_separation_index} • Person R: {report.reliability.person_reliability}
              </p>
            </div>

            {/* KPI 3: Targeting Alignment */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Độ nhắm mục tiêu (Targeting)
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">
                  {report.targeting.targeting_gap_logit > 0 ? `+${report.targeting.targeting_gap_logit}` : report.targeting.targeting_gap_logit}
                </span>
                <span className="text-xs text-slate-500 font-medium">logits gap</span>
              </div>
              {(() => {
                const b = targetingBadge(report.targeting.targeting_evaluation);
                return (
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${b.bg}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${b.dot}`} />
                    {b.label}
                  </span>
                );
              })()}
            </div>

            {/* KPI 4: Measurement Fit Quality */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Độ phù hợp thang đo (Fit Rate)
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-black text-slate-900">
                  {Math.round(
                    (report.item_calibrations.filter((i) => i.fit_status === 'OPTIMAL_FIT').length /
                      report.item_calibrations.length) *
                      100
                  )}%
                </span>
                <span className="text-xs text-slate-500 font-medium">Infit [0.7 - 1.3]</span>
              </div>
              <p className="text-[11px] text-slate-500">
                {report.item_calibrations.filter((i) => i.fit_status === 'OPTIMAL_FIT').length}/{report.item_calibrations.length} câu hỏi đạt chuẩn hữu ích đo lường
              </p>
            </div>
          </div>

          {/* Wright Map (Person-Item Map Visualizer) */}
          <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-200/60 gap-2">
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <BarChart2 className="w-4 h-4 text-teal-600" />
                  <span>Bản Đồ Wright Map (Person-Item Alignment Map)</span>
                </h4>
                <p className="text-[11px] text-slate-500">
                  Trực quan hóa sự phân bố đồng quy giữa Năng lực Người trả lời (trái) và Độ khó Câu hỏi (phải) trên thang Logit.
                </p>
              </div>
              <div className="text-[11px] text-slate-600 bg-white px-2.5 py-1 rounded-lg border border-slate-200 font-medium self-start sm:self-auto">
                θ Trung bình = <strong className="text-teal-700">{report.reliability.person_mean_theta} logits</strong> (Gốc chuẩn b = 0.00)
              </div>
            </div>

            {/* Dual Column Ladder Map */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-1">
              {/* Header Titles */}
              <div className="grid grid-cols-12 text-[11px] font-bold text-slate-600 pb-2 border-b border-slate-100">
                <div className="col-span-5 text-right pr-4">Năng Lực Người Trả Lời (θ)</div>
                <div className="col-span-2 text-center font-mono">Logit</div>
                <div className="col-span-5 pl-4">Độ Khó Câu Hỏi (b_i)</div>
              </div>

              {/* Ladder Rows */}
              {[...report.wright_map].reverse().map((bucket) => {
                return (
                  <div
                    key={bucket.logit_level}
                    className="grid grid-cols-12 items-center text-xs py-1 hover:bg-slate-50/80 rounded transition-colors group"
                  >
                    {/* Left: Person Density */}
                    <div className="col-span-5 flex items-center justify-end gap-2 pr-4">
                      {bucket.person_count > 0 && (
                        <span className="text-[10px] text-slate-400 font-mono">
                          {bucket.person_count} ({bucket.person_percent}%)
                        </span>
                      )}
                      <div className="w-24 sm:w-36 h-2 bg-slate-100 rounded-full overflow-hidden flex justify-end">
                        <div
                          className="h-full bg-gradient-to-l from-teal-500 to-teal-300 rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(100, bucket.person_percent * 2.5)}%` }}
                        />
                      </div>
                    </div>

                    {/* Center: Logit Tick */}
                    <div className="col-span-2 text-center">
                      <span className="inline-block px-2 py-0.5 text-[10px] font-mono font-semibold text-slate-600 bg-slate-100 rounded">
                        {bucket.logit_level > 0 ? `+${bucket.logit_level.toFixed(1)}` : bucket.logit_level.toFixed(1)}
                      </span>
                    </div>

                    {/* Right: Items at this logit level */}
                    <div className="col-span-5 flex flex-wrap items-center gap-1.5 pl-4">
                      {bucket.items.map((itemCode) => {
                        const itemObj = report.item_calibrations.find((i) => i.item_code === itemCode);
                        return (
                          <button
                            key={itemCode}
                            onClick={() => itemObj && setSelectedItem(itemObj)}
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-all shadow-2xs ${
                              selectedItem?.item_code === itemCode
                                ? 'bg-teal-600 text-white ring-2 ring-teal-400 ring-offset-1'
                                : 'bg-teal-50 text-teal-800 border border-teal-200 hover:bg-teal-100'
                            }`}
                            title={`${itemObj?.title} (b = ${itemObj?.difficulty_logit} logits, Infit = ${itemObj?.infit_mnsq})`}
                          >
                            {itemCode}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Item Quick Inspection Drawer */}
            {selectedItem && (
              <div className="p-3.5 bg-teal-50/70 border border-teal-200 rounded-xl text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-teal-800 bg-white px-2 py-0.5 rounded border border-teal-200 text-[11px]">
                      {selectedItem.item_code}
                    </span>
                    <strong className="text-slate-900 text-xs">{selectedItem.title}</strong>
                  </div>
                  <p className="text-[11px] text-slate-600">
                    Độ khó: <strong className="text-teal-900">{selectedItem.difficulty_logit} logits</strong> (SE = {selectedItem.standard_error}) • Infit MNSQ: <strong className="text-slate-900">{selectedItem.infit_mnsq}</strong> • Outfit MNSQ: <strong className="text-slate-900">{selectedItem.outfit_mnsq}</strong>
                  </p>
                </div>
                <div className="shrink-0">
                  <span
                    className={`inline-block px-2.5 py-1 text-[11px] font-semibold rounded-lg border ${
                      selectedItem.fit_status === 'OPTIMAL_FIT'
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                        : selectedItem.fit_status === 'UNDERFIT_NOISY'
                        ? 'bg-rose-100 text-rose-800 border-rose-300'
                        : 'bg-amber-100 text-amber-800 border-amber-300'
                    }`}
                  >
                    {selectedItem.fit_label}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Item Fit Statistics Table (Infit & Outfit MNSQ) */}
          <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-3">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Scale className="w-4 h-4 text-teal-600" />
              <span>Bảng Thống Kê Tham Số Câu Hỏi (Rasch Item Calibration & Quality Indices)</span>
            </h4>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse border border-slate-200 rounded-lg overflow-hidden bg-white">
                <thead className="bg-slate-100 text-slate-700 font-bold">
                  <tr>
                    <th className="py-2.5 px-3 border border-slate-200">Mã</th>
                    <th className="py-2.5 px-3 border border-slate-200">Nội dung câu hỏi</th>
                    <th className="py-2.5 px-3 border border-slate-200 text-center">Độ khó (b_i)</th>
                    <th className="py-2.5 px-3 border border-slate-200 text-center">Sai số (SE)</th>
                    <th className="py-2.5 px-3 border border-slate-200 text-center">Infit MNSQ</th>
                    <th className="py-2.5 px-3 border border-slate-200 text-center">Outfit MNSQ</th>
                    <th className="py-2.5 px-3 border border-slate-200 text-center">Đánh giá chất lượng</th>
                  </tr>
                </thead>
                <tbody>
                  {report.item_calibrations.map((item) => (
                    <tr
                      key={item.question_id}
                      onClick={() => setSelectedItem(item)}
                      className={`hover:bg-teal-50/40 cursor-pointer transition-colors ${
                        selectedItem?.question_id === item.question_id ? 'bg-teal-50/80 font-medium' : ''
                      }`}
                    >
                      <td className="py-2 px-3 border border-slate-200 font-mono font-bold text-teal-700">
                        {item.item_code}
                      </td>
                      <td className="py-2 px-3 border border-slate-200 text-slate-900 max-w-sm line-clamp-1">
                        {item.title}
                      </td>
                      <td className="py-2 px-3 border border-slate-200 text-center font-mono font-bold text-slate-900">
                        {item.difficulty_logit > 0 ? `+${item.difficulty_logit.toFixed(2)}` : item.difficulty_logit.toFixed(2)}
                      </td>
                      <td className="py-2 px-3 border border-slate-200 text-center font-mono text-slate-500">
                        {item.standard_error.toFixed(2)}
                      </td>
                      <td className="py-2 px-3 border border-slate-200 text-center font-mono">
                        <span
                          className={
                            item.infit_mnsq < 0.7 || item.infit_mnsq > 1.3 ? 'text-rose-600 font-bold' : 'text-slate-800'
                          }
                        >
                          {item.infit_mnsq.toFixed(2)}
                        </span>
                      </td>
                      <td className="py-2 px-3 border border-slate-200 text-center font-mono">
                        <span
                          className={
                            item.outfit_mnsq < 0.7 || item.outfit_mnsq > 1.3 ? 'text-rose-600 font-bold' : 'text-slate-800'
                          }
                        >
                          {item.outfit_mnsq.toFixed(2)}
                        </span>
                      </td>
                      <td className="py-2 px-3 border border-slate-200 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            item.fit_status === 'OPTIMAL_FIT'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : item.fit_status === 'UNDERFIT_NOISY'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                          }`}
                        >
                          {item.fit_status === 'OPTIMAL_FIT'
                            ? 'Tối ưu [0.7-1.3]'
                            : item.fit_status === 'UNDERFIT_NOISY'
                            ? 'Nhiễu (> 1.3)'
                            : 'Dư thừa (< 0.7)'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Edition Narrative Citation Box */}
          <div className="p-4 rounded-xl bg-slate-900 text-slate-100 space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-teal-300">
                <BookOpen className="w-4 h-4" />
                <span>Trích dẫn báo cáo đo lường tâm trắc học (APA 7th Edition Rasch Measurement Statement)</span>
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
            <p className="text-xs font-mono text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800/80 leading-relaxed selection:bg-teal-600 selection:text-white">
              {report.apa_narrative}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
