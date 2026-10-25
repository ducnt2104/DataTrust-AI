import React, { useState } from 'react';
import {
  ArrowLeftRight, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  RefreshCw, Copy, Check, Table, Calculator, Info, Zap
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, ScaleEquatingResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const ScaleEquatingCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc các câu hỏi định lượng / thang đo
  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  const [sourceId, setSourceId] = useState<string>(eligibleQuestions[0]?.question_id || '');
  const [targetId, setTargetId] = useState<string>(eligibleQuestions[1]?.question_id || '');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScaleEquatingResult | null>(null);
  const [copiedApa, setCopiedApa] = useState(false);

  // Quick Calculator State
  const [calcInput, setCalcInput] = useState<string>('3');

  const handleRunEquating = async () => {
    if (!sourceId || !targetId) {
      setError('Vui lòng chọn đầy đủ cả thang đo nguồn (X) và thang đo đích (Y).');
      return;
    }
    if (sourceId === targetId) {
      setError('Thang đo nguồn (X) và thang đo đích (Y) phải là hai câu hỏi khác nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runScaleEquating(surveyId, {
        source_question_id: sourceId,
        target_question_id: targetId,
        scope
      });
      if (res.status === 'ERROR' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không thể tính toán liên kết thang đo.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi kết nối máy chủ để thực hiện liên kết thang đo.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2000);
  };

  // Tính điểm nhanh cho Quick Calculator
  const getQuickConverted = () => {
    if (!result || !result.linear_equating) return null;
    const val = parseFloat(calcInput);
    if (isNaN(val)) return null;

    const alpha = result.linear_equating.slope_alpha;
    const beta = result.linear_equating.intercept_beta;
    const lin = alpha * val + beta;

    const bounds = result.descriptive_statistics?.y_scale.theoretical_range;
    const yMin = bounds ? bounds[0] : (result.descriptive_statistics?.y_scale.min_observed ?? lin);
    const yMax = bounds ? bounds[1] : (result.descriptive_statistics?.y_scale.max_observed ?? lin);

    const bounded = Math.min(Math.max(lin, yMin), yMax);
    return {
      raw: lin.toFixed(2),
      bounded: bounded.toFixed(2),
      rounded: Math.round(bounded)
    };
  };

  const quickConv = getQuickConverted();

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-50 border border-cyan-200/60 flex items-center justify-center text-cyan-600 shadow-xs">
            <ArrowLeftRight className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Chuẩn Hóa & Liên Kết Thang Đo (Score Equating & Concordance)
              </h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-200">
                Kolen & Brennan (2014)
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Quy đổi tương đương giữa các hệ thang đo khác biệt (Likert 5, Likert 7, NPS 0-10) bảo toàn phân phối thống kê
            </p>
          </div>
        </div>
      </div>

      {/* Selectors */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {/* Source Scale X */}
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700">Thang đo nguồn (X):</label>
            <select
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {eligibleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          {/* Target Scale Y */}
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700">Thang đo đích cần quy đổi (Y):</label>
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {eligibleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          {/* Scope */}
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700">Phạm vi dữ liệu:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value="all">Toàn bộ phản hồi (All)</option>
              <option value="verified_clean">Đã làm sạch & Xác thực (Clean)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-[11px] text-slate-500">
            Hỗ trợ cả phương pháp Linear Equating và Equipercentile Equating với hiệu chỉnh liên tục.
          </span>
          <button
            onClick={handleRunEquating}
            disabled={loading || !sourceId || !targetId || sourceId === targetId}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-600 text-white hover:bg-cyan-700 disabled:opacity-50 transition-all shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Đang tính toán...' : 'Tính toán hàm liên kết & Bảng quy đổi'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'OK' && (
        <div className="space-y-6">
          {/* Hero KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Hàm chuyển đổi tuyến tính</span>
              <div className="text-lg font-black text-slate-900 mt-1 font-mono truncate" title={result.linear_equating?.formula}>
                {result.linear_equating?.formula}
              </div>
              <span className="text-[11px] text-slate-500">
                Slope α = {result.linear_equating?.slope_alpha} | Intercept β = {result.linear_equating?.intercept_beta}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Cỡ mẫu tham gia</span>
              <div className="text-2xl font-black text-slate-900 mt-1">
                {result.sample_sizes?.x_count} ⟷ {result.sample_sizes?.y_count}
              </div>
              <span className="text-[11px] text-slate-500">
                Quan sát hợp lệ trên hai thang
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Sai lệch phân vị tối đa</span>
              <div className="text-2xl font-black text-cyan-600 mt-1">
                {result.discrepancy_analysis?.max_discrepancy}
              </div>
              <span className="text-[11px] text-slate-500">
                Trung bình lệch: {result.discrepancy_analysis?.mean_discrepancy} điểm
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Mức độ đồng quy</span>
              <div className="mt-1">
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                  result.discrepancy_analysis?.agreement_verdict === 'EXCELLENT'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                    : result.discrepancy_analysis?.agreement_verdict === 'MODERATE'
                    ? 'bg-amber-50 text-amber-700 border-amber-300'
                    : 'bg-rose-50 text-rose-700 border-rose-300'
                }`}>
                  {result.discrepancy_analysis?.agreement_verdict === 'EXCELLENT'
                    ? '✅ Đồng quy xuất sắc'
                    : result.discrepancy_analysis?.agreement_verdict === 'MODERATE'
                    ? '⚠️ Khác biệt vừa phải'
                    : '⛔ Phân kỳ lệch tâm'}
                </span>
              </div>
              <span className="text-[11px] text-slate-500 block mt-1 line-clamp-1" title={result.discrepancy_analysis?.agreement_narrative}>
                {result.discrepancy_analysis?.agreement_narrative}
              </span>
            </div>
          </div>

          {/* Quick Calculator Widget */}
          <div className="p-4 rounded-xl bg-cyan-50/60 border border-cyan-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-700">
                <Calculator className="w-4 h-4" />
              </div>
              <div>
                <span className="font-bold text-slate-900 block">Bộ chuyển đổi điểm nhanh 1-Click:</span>
                <span className="text-slate-600">Nhập điểm trên thang X để quy đổi ngay sang thang Y tương ứng</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-2.5 py-1">
                <span className="text-slate-500 font-medium">Điểm X:</span>
                <input
                  type="number"
                  value={calcInput}
                  onChange={(e) => setCalcInput(e.target.value)}
                  className="w-16 text-xs font-bold text-slate-900 focus:outline-none"
                  step="0.5"
                />
              </div>
              <ArrowRight className="w-4 h-4 text-cyan-600" />
              <div className="bg-white border border-cyan-300 px-3 py-1 rounded-lg text-cyan-950 font-bold shadow-2xs">
                {quickConv ? `${quickConv.bounded} điểm Y (làm tròn: ${quickConv.rounded})` : '...'}
              </div>
            </div>
          </div>

          {/* Concordance Conversion Table */}
          {result.concordance_table && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Table className="w-3.5 h-3.5 text-cyan-600" />
                  Bảng quy đổi tương đương hoàn chỉnh (Concordance Table)
                </h4>
                <span className="text-[11px] text-slate-500 font-mono">
                  {result.x_label} ⟷ {result.y_label}
                </span>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Điểm nguồn (X)</th>
                      <th className="py-2.5 px-3 text-right">Phân vị PR (%)</th>
                      <th className="py-2.5 px-3 text-right">Quy đổi Tuyến tính</th>
                      <th className="py-2.5 px-3 text-right">Quy đổi Phân vị</th>
                      <th className="py-2.5 px-3 text-center">Điểm Y làm tròn</th>
                      <th className="py-2.5 px-3 text-right">T-Score (50/10)</th>
                      <th className="py-2.5 px-3 text-center">Stanine (1-9)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.concordance_table.map((row) => (
                      <tr key={row.x_score} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-bold text-slate-900 font-mono">
                          {row.x_score}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-700">
                          {row.percentile_rank}%
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-700 font-medium">
                          {row.linear_equivalent}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-cyan-700">
                          {row.equipercentile_equivalent}
                        </td>
                        <td className="py-2 px-3 text-center font-bold">
                          <span className="px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-800 border border-cyan-200">
                            {row.equipercentile_rounded}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-600">
                          {row.t_score}
                        </td>
                        <td className="py-2 px-3 text-center font-mono font-medium text-slate-700">
                          {row.stanine}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">Đoạn văn trích dẫn khoa học chuẩn APA 7th Edition:</span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="flex items-center gap-1 text-cyan-700 hover:text-cyan-900 font-semibold text-xs"
                >
                  {copiedApa ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-cyan-600" />}
                  <span>{copiedApa ? 'Đã sao chép' : 'Sao chép văn bản'}</span>
                </button>
              </div>
              <p className="p-3 bg-white rounded-lg border border-slate-200/80 italic text-slate-700 leading-relaxed font-serif">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
