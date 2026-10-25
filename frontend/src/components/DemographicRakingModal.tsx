import React, { useState } from 'react';
import {
  X,
  Scale,
  Sparkles,
  Download,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  TrendingDown,
  RefreshCw,
  Sliders,
  FileSpreadsheet
} from 'lucide-react';
import { api } from '../api/client';
import {
  DemographicRakingResult,
  DemographicRakingRequest,
  QuestionStats
} from '../types/survey';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  surveyId: string;
  questions: QuestionStats[];
}

export const DemographicRakingModal: React.FC<Props> = ({
  isOpen,
  onClose,
  surveyId,
  questions
}) => {
  // Lọc các câu hỏi có options phân loại để làm biến nhân khẩu học
  const candidateQuestions = questions.filter(
    (q) => q.option_distribution && Object.keys(q.option_distribution).length >= 2 && Object.keys(q.option_distribution).length <= 15
  );

  const [selectedVarIds, setSelectedVarIds] = useState<string[]>(
    candidateQuestions.slice(0, 2).map((q) => q.question_id)
  );

  // Lưu target percentages cho từng category của từng biến: { [qid]: { [category]: target_pct_0_to_100 } }
  const [targetPercentages, setTargetPercentages] = useState<Record<string, Record<string, number>>>(() => {
    const initial: Record<string, Record<string, number>> = {};
    candidateQuestions.slice(0, 2).forEach((q) => {
      const cats = Object.keys(q.option_distribution || {});
      const equalPct = cats.length > 0 ? Math.round(100 / cats.length) : 0;
      initial[q.question_id] = {};
      cats.forEach((cat) => {
        initial[q.question_id][cat] = equalPct;
      });
    });
    return initial;
  });

  const [scope, setScope] = useState<'verified_clean' | 'all'>('verified_clean');
  const [maxIterations, setMaxIterations] = useState<number>(50);
  const [running, setRunning] = useState<boolean>(false);
  const [downloading, setDownloading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DemographicRakingResult | null>(null);

  if (!isOpen) return null;

  const handleToggleQuestion = (qid: string) => {
    if (selectedVarIds.includes(qid)) {
      setSelectedVarIds(selectedVarIds.filter((id) => id !== qid));
    } else {
      setSelectedVarIds([...selectedVarIds, qid]);
      if (!targetPercentages[qid]) {
        const q = candidateQuestions.find((item) => item.question_id === qid);
        const cats = Object.keys(q?.option_distribution || {});
        const equalPct = cats.length > 0 ? Math.round(100 / cats.length) : 0;
        const newTargets: Record<string, number> = {};
        cats.forEach((cat) => {
          newTargets[cat] = equalPct;
        });
        setTargetPercentages({ ...targetPercentages, [qid]: newTargets });
      }
    }
  };

  const handleUpdateTargetPct = (qid: string, cat: string, val: number) => {
    setTargetPercentages({
      ...targetPercentages,
      [qid]: {
        ...(targetPercentages[qid] || {}),
        [cat]: val
      }
    });
  };

  const handleRunRaking = async () => {
    if (selectedVarIds.length === 0) {
      setError('Vui lòng chọn ít nhất một biến nhân khẩu học để cân bằng trọng số.');
      return;
    }

    // Xây dựng target_margins chuyển đổi từ % (0-100) sang tỷ lệ thập phân (0.0 - 1.0)
    const targetMargins: Record<string, Record<string, number>> = {};
    for (const qid of selectedVarIds) {
      const q = candidateQuestions.find((item) => item.question_id === qid);
      const qKey = q?.question_title || qid;
      const catObj = targetPercentages[qid] || {};
      const totalPct = Object.values(catObj).reduce((a, b) => a + b, 0);

      if (totalPct <= 0) {
        setError(`Tổng tỷ lệ mục tiêu cho biến '${qKey}' phải lớn hơn 0.`);
        return;
      }

      targetMargins[qid] = {};
      for (const [cat, pct] of Object.entries(catObj)) {
        targetMargins[qid][cat] = pct / 100.0;
      }
    }

    try {
      setRunning(true);
      setError(null);
      const req: DemographicRakingRequest = {
        target_margins: targetMargins,
        scope,
        max_iterations: maxIterations,
        convergence_tol: 0.001,
        trim_min: 0.2,
        trim_max: 5.0
      };
      const res = await api.runDemographicRaking(surveyId, req);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi thực hiện thuật toán Raking.');
    } finally {
      setRunning(false);
    }
  };

  const handleDownloadCsv = async () => {
    if (!result) return;
    const targetMargins: Record<string, Record<string, number>> = {};
    for (const qid of selectedVarIds) {
      const catObj = targetPercentages[qid] || {};
      targetMargins[qid] = {};
      for (const [cat, pct] of Object.entries(catObj)) {
        targetMargins[qid][cat] = pct / 100.0;
      }
    }
    try {
      setDownloading(true);
      await api.downloadRakedCsv(surveyId, {
        target_margins: targetMargins,
        scope
      });
    } catch (err: any) {
      alert(err.message || 'Lỗi khi tải tệp CSV có trọng số.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto"
      role="dialog"
      aria-modal="true"
    >
      <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-900 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 border border-indigo-400/30 rounded-xl">
              <Scale className="w-5 h-5 text-indigo-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">
                  Cân Bằng Trọng Số Mẫu Nhân Khẩu Học (Demographic Raking / IPF)
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 font-mono font-bold">
                  Deming-Stephan IPF
                </span>
              </div>
              <p className="text-xs text-slate-300">
                Hiệu chỉnh sai lệch lấy mẫu bằng cách gán trọng số cá thể khớp với phân bố dân số học chuẩn
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs bg-slate-50/50">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* 1. Chọn biến nhân khẩu học & nhập Benchmark */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
              <span className="font-bold text-slate-800 text-xs flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                1. Chọn Biến Phân Tầng & Thiết Lập Tỷ Lệ Mục Tiêu Dân Số (%)
              </span>
              <div className="flex items-center gap-3 text-[11px] text-slate-500">
                <span>Phạm vi:</span>
                <select
                  value={scope}
                  onChange={(e) => setScope(e.target.value as any)}
                  className="p-1 bg-slate-50 border border-slate-200 rounded text-slate-800 font-semibold"
                >
                  <option value="verified_clean">Mẫu đã làm sạch (Verified Clean)</option>
                  <option value="all">Toàn bộ mẫu thu thập</option>
                </select>
              </div>
            </div>

            {candidateQuestions.length === 0 ? (
              <p className="text-slate-400 italic">
                Khảo sát chưa có câu hỏi trắc nghiệm nào phù hợp làm biến nhân khẩu học.
              </p>
            ) : (
              <div className="space-y-4">
                {candidateQuestions.map((q) => {
                  const isChecked = selectedVarIds.includes(q.question_id);
                  const cats = Object.keys(q.option_distribution || {});
                  const currentTargets = targetPercentages[q.question_id] || {};
                  const sumPct = Object.values(currentTargets).reduce((a, b) => a + b, 0);

                  return (
                    <div
                      key={q.question_id}
                      className={`p-3.5 rounded-xl border transition-all ${
                        isChecked ? 'bg-indigo-50/30 border-indigo-200' : 'bg-slate-50 border-slate-200 opacity-60'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleQuestion(q.question_id)}
                            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                          />
                          <span className="font-bold text-slate-900 text-xs">{q.question_title}</span>
                        </label>
                        {isChecked && (
                          <span
                            className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                              Math.abs(sumPct - 100) < 1
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            Tổng: {sumPct}% {Math.abs(sumPct - 100) >= 1 ? '(Khuyến nghị 100%)' : '✓'}
                          </span>
                        )}
                      </div>

                      {isChecked && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-100">
                          {cats.map((cat) => {
                            const unweightedCount = q.option_distribution?.[cat] || 0;
                            const unweightedPct =
                              q.total_answers > 0 ? Math.round((unweightedCount / q.total_answers) * 100) : 0;
                            const targetVal = currentTargets[cat] ?? 0;

                            return (
                              <div
                                key={cat}
                                className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs space-y-1"
                              >
                                <span className="text-[11px] font-bold text-slate-700 block truncate" title={cat}>
                                  {cat}
                                </span>
                                <span className="text-[10px] text-slate-400 block font-mono">
                                  Mẫu thực: {unweightedCount} ({unweightedPct}%)
                                </span>
                                <div className="flex items-center gap-1 pt-1">
                                  <input
                                    type="number"
                                    min={0}
                                    max={100}
                                    value={targetVal}
                                    onChange={(e) =>
                                      handleUpdateTargetPct(q.question_id, cat, Number(e.target.value))
                                    }
                                    className="w-16 p-1 bg-slate-50 border border-slate-200 rounded font-mono font-bold text-xs text-slate-800 text-center focus:outline-hidden"
                                  />
                                  <span className="text-slate-500 font-bold">%</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={handleRunRaking}
                disabled={running || selectedVarIds.length === 0}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-xs shadow-xs disabled:opacity-50 transition-all"
              >
                <Sparkles className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
                <span>{running ? 'Đang chạy thuật toán IPF...' : 'Chạy Cân Bằng Trọng Số (Run Raking)'}</span>
              </button>
            </div>
          </div>

          {/* 2. Kết quả Raking & Báo cáo hiệu chuẩn */}
          {result && (
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-5 animate-in fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <div>
                    <h4 className="font-bold text-slate-900 text-xs">
                      Kết Quả Hiệu Chuẩn Trọng Số Thống Kê (IPF Results)
                    </h4>
                    <span className="text-[11px] text-slate-500">
                      Hội tụ thành công sau {result.iterations} vòng lặp • Độ lệch biên: {result.max_discrepancy}
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleDownloadCsv}
                  disabled={downloading}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs transition-colors disabled:opacity-50"
                  title="Xuất bộ dữ liệu sạch kèm cột trọng số _statistical_weight_wi"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>{downloading ? 'Đang xuất CSV...' : 'Tải CSV Có Trọng Số (Weighted)'}</span>
                </button>
              </div>

              {/* 4 KPI Cards (Kish Neff, Deff, Sample Size, Efficiency) */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Cỡ Mẫu Danh Nghĩa (N)</span>
                  <span className="text-lg font-extrabold text-slate-900 font-mono">{result.sample_size}</span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Số quan sát thực</span>
                </div>

                <div className="p-3 bg-indigo-50/60 rounded-xl border border-indigo-200">
                  <span className="text-[10px] text-indigo-700 block uppercase font-bold">Cỡ Mẫu Hiệu Dụng (Neff)</span>
                  <span className="text-lg font-extrabold text-indigo-700 font-mono">{result.effective_sample_size_neff}</span>
                  <span className="text-[10px] text-indigo-500 block mt-0.5">Kish's Effective N</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Hệ Số Thiết Kế (Deff)</span>
                  <span className="text-lg font-extrabold text-slate-900 font-mono">{result.design_effect_deff}</span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Kish Design Effect</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Hiệu Suất Mẫu</span>
                  <span className="text-lg font-extrabold text-emerald-600 font-mono">{result.statistical_efficiency_pct}%</span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Neff / N</span>
                </div>
              </div>

              {/* Phân bố trọng số */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between text-[11px] font-mono text-slate-600">
                <span>Trọng số min: <strong className="text-slate-900">{result.weight_stats.min}</strong></span>
                <span>Trung bình: <strong className="text-slate-900">{result.weight_stats.mean}</strong></span>
                <span>Max: <strong className="text-slate-900">{result.weight_stats.max}</strong></span>
                <span>Độ lệch chuẩn: <strong className="text-slate-900">{result.weight_stats.std}</strong></span>
                <span>Giới hạn Trim: [{result.weight_stats.trim_bounds.join(', ')}]</span>
              </div>

              {/* Bảng so sánh chi tiết Trước vs Sau */}
              <div className="space-y-3">
                <span className="font-bold text-slate-800 text-xs block">
                  So Sánh Phân Bố Biên Trước & Sau Khi Cân Bằng Trọng Số
                </span>

                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100/80 text-slate-600 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">Biến / Nhóm Đối Tượng</th>
                        <th className="py-2.5 px-3 text-right">Mẫu Thực (N)</th>
                        <th className="py-2.5 px-3 text-right">Chưa Cân (%)</th>
                        <th className="py-2.5 px-3 text-right text-indigo-700">Mục Tiêu Dân Số (%)</th>
                        <th className="py-2.5 px-3 text-right text-emerald-700">Đã Cân Raking (%)</th>
                        <th className="py-2.5 px-3 text-right">Giảm Sai Lệch</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {result.marginal_comparisons.map((comp) => (
                        <React.Fragment key={comp.variable}>
                          <tr className="bg-slate-50/70 font-bold text-slate-900">
                            <td colSpan={6} className="py-2 px-3 text-indigo-900">
                              Biến: {comp.variable}
                            </td>
                          </tr>
                          {comp.categories.map((cat) => (
                            <tr key={cat.category} className="hover:bg-slate-50/50">
                              <td className="py-2 px-3 pl-6 font-medium text-slate-700">{cat.category}</td>
                              <td className="py-2 px-3 text-right font-mono text-slate-500">{cat.unweighted_count}</td>
                              <td className="py-2 px-3 text-right font-mono text-slate-600">{cat.unweighted_pct}%</td>
                              <td className="py-2 px-3 text-right font-mono font-bold text-indigo-700">
                                {cat.target_benchmark_pct}%
                              </td>
                              <td className="py-2 px-3 text-right font-mono font-bold text-emerald-700">
                                {cat.weighted_pct}%
                              </td>
                              <td className="py-2 px-3 text-right font-mono text-emerald-600">
                                -{cat.absolute_bias_reduction_pct}%
                              </td>
                            </tr>
                          ))}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Summary note */}
              <p className="text-[11px] text-slate-500 italic bg-slate-50 p-3 rounded-lg border border-slate-200">
                {result.summary}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 bg-white text-xs">
          <span className="text-slate-400 font-mono text-[10px]">
            DataTrust IPF Engine • AAPOR/ESOMAR Scientific Weighting
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
