import React, { useState } from 'react';
import {
  Sliders, Sparkles, CheckCircle2, AlertTriangle, RefreshCw,
  Copy, Check, Table, Filter, Layers, Percent, Activity,
  BookOpen, ArrowRight, TrendingUp
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, ModerationAnalysisResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const ModerationAnalysisCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc các câu hỏi thang đo / định lượng
  const scaleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  const [xId, setXId] = useState<string>(scaleQuestions[0]?.question_id || '');
  const [wId, setWId] = useState<string>(scaleQuestions[1]?.question_id || '');
  const [yId, setYId] = useState<string>(scaleQuestions[2]?.question_id || '');
  const [centerVars, setCenterVars] = useState<boolean>(true);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ModerationAnalysisResult | null>(null);
  const [copiedApa, setCopiedApa] = useState(false);

  const handleRunModeration = async () => {
    if (!xId || !wId || !yId) {
      setError('Vui lòng chọn đầy đủ 3 biến: Độc lập (X), Điều tiết (W) và Phụ thuộc (Y).');
      return;
    }
    if (new Set([xId, wId, yId]).size < 3) {
      setError('Ba biến X, W và Y phải là ba câu hỏi phân biệt, không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runModerationAnalysis(surveyId, {
        independent_question_id: xId,
        moderator_question_id: wId,
        dependent_question_id: yId,
        center_variables: centerVars,
        scope
      });

      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể thực hiện phân tích điều tiết.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi kết nối máy chủ khi thực hiện phân tích điều tiết.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2000);
  };

  // Helper tính toán tọa độ SVG cho đồ thị tương tác 2D
  const renderInteractionPlot = () => {
    if (!result?.interaction_plot?.lines || result.interaction_plot.lines.length < 3) return null;

    const lines = result.interaction_plot.lines;
    const xLow = lines[0].point_low_x.x;
    const xHigh = lines[0].point_high_x.x;

    // Tìm min và max Y dự báo qua tất cả các điểm
    let allY: number[] = [];
    lines.forEach((l) => {
      allY.push(l.point_low_x.y_pred, l.point_high_x.y_pred);
    });
    const minY = Math.floor(Math.min(...allY) - 0.5);
    const maxY = Math.ceil(Math.max(...allY) + 0.5);

    const svgWidth = 440;
    const svgHeight = 220;
    const padding = { top: 25, right: 35, bottom: 40, left: 55 };

    const plotW = svgWidth - padding.left - padding.right;
    const plotH = svgHeight - padding.top - padding.bottom;

    const scaleX = (val: number) => {
      if (Math.abs(xHigh - xLow) < 1e-6) return padding.left + plotW / 2;
      return padding.left + ((val - xLow) / (xHigh - xLow)) * plotW;
    };

    const scaleY = (val: number) => {
      if (Math.abs(maxY - minY) < 1e-6) return padding.top + plotH / 2;
      return padding.top + plotH - ((val - minY) / (maxY - minY)) * plotH;
    };

    const colors = {
      LOW: '#3b82f6', // blue-500
      MEAN: '#64748b', // slate-500
      HIGH: '#8b5cf6' // purple-500
    };

    return (
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
            Đồ thị Hiệu ứng Tương tác 2D (Interaction Slopes Plot)
          </span>
          <div className="flex items-center gap-3 text-[11px]">
            <span className="flex items-center gap-1 font-medium text-blue-600">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" /> Low W (-1 SD)
            </span>
            <span className="flex items-center gap-1 font-medium text-slate-600">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500 inline-block" /> Mean W
            </span>
            <span className="flex items-center gap-1 font-medium text-purple-600">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block" /> High W (+1 SD)
            </span>
          </div>
        </div>

        <div className="w-full flex justify-center bg-white p-2 rounded-lg border border-slate-200/60 shadow-2xs">
          <svg width={svgWidth} height={svgHeight} className="overflow-visible">
            {/* Grid lines ngang */}
            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
              const yVal = minY + (maxY - minY) * pct;
              const yPos = scaleY(yVal);
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={yPos}
                    x2={svgWidth - padding.right}
                    y2={yPos}
                    stroke="#e2e8f0"
                    strokeDasharray="3 3"
                  />
                  <text
                    x={padding.left - 8}
                    y={yPos + 3}
                    textAnchor="end"
                    className="text-[10px] fill-slate-400 font-mono"
                  >
                    {yVal.toFixed(1)}
                  </text>
                </g>
              );
            })}

            {/* Trục X nhãn */}
            <text
              x={scaleX(xLow)}
              y={svgHeight - padding.bottom + 18}
              textAnchor="middle"
              className="text-[11px] fill-slate-600 font-medium"
            >
              Thấp (-1 SD: {xLow.toFixed(1)})
            </text>
            <text
              x={scaleX(xHigh)}
              y={svgHeight - padding.bottom + 18}
              textAnchor="middle"
              className="text-[11px] fill-slate-600 font-medium"
            >
              Cao (+1 SD: {xHigh.toFixed(1)})
            </text>

            <text
              x={svgWidth / 2}
              y={svgHeight - 6}
              textAnchor="middle"
              className="text-[11px] fill-slate-500 font-semibold"
            >
              Biến độc lập (X): {result.variables?.independent_x.title}
            </text>

            {/* Trục Y nhãn quay 90 độ */}
            <text
              x={-svgHeight / 2}
              y={14}
              textAnchor="middle"
              transform="rotate(-90)"
              className="text-[11px] fill-slate-500 font-semibold"
            >
              Biến phụ thuộc (Y): {result.variables?.dependent_y.title}
            </text>

            {/* Vẽ 3 đường hồi quy */}
            {lines.map((line) => {
              const x1 = scaleX(line.point_low_x.x);
              const y1 = scaleY(line.point_low_x.y_pred);
              const x2 = scaleX(line.point_high_x.x);
              const y2 = scaleY(line.point_high_x.y_pred);
              const color = colors[line.level] || '#64748b';

              return (
                <g key={line.level}>
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={color}
                    strokeWidth={line.level === 'MEAN' ? 2 : 2.5}
                    strokeDasharray={line.level === 'LOW' ? '4 2' : undefined}
                  />
                  <circle cx={x1} cy={y1} r={4} fill={color} />
                  <circle cx={x2} cy={y2} r={4} fill={color} />
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-violet-50 border border-violet-200/60 flex items-center justify-center text-violet-600 shadow-xs">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-800">
                Phân tích Tác động Điều tiết & Tương tác (PROCESS Model 1 - Hayes 2018)
              </h3>
              <span className="px-2 py-0.5 text-[11px] font-semibold bg-violet-100 text-violet-700 rounded-md">
                Simple Slopes & Johnson-Neyman
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Đánh giá điều kiện hóa: Mối quan hệ giữa X và Y thay đổi như thế nào theo từng mức độ của biến điều tiết W
            </p>
          </div>
        </div>

        {result && (
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border self-start sm:self-auto ${
            result.moderation_effect?.is_significant
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : 'bg-slate-100 text-slate-700 border-slate-200'
          }`}>
            {result.moderation_effect?.is_significant ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-slate-500" />
            )}
            {result.moderation_effect?.verdict_badge}
          </span>
        )}
      </div>

      {/* Control Panel */}
      <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/60 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Biến Độc Lập X */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Biến Độc Lập (Independent Variable - X)
            </label>
            <select
              value={xId}
              onChange={(e) => setXId(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 bg-white py-2 px-3 shadow-2xs"
            >
              {scaleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          {/* Biến Điều Tiết W */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Biến Điều Tiết (Moderator Variable - W)
            </label>
            <select
              value={wId}
              onChange={(e) => setWId(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 bg-white py-2 px-3 shadow-2xs"
            >
              {scaleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          {/* Biến Phụ Thuộc Y */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Biến Phụ Thuộc (Dependent Variable - Y)
            </label>
            <select
              value={yId}
              onChange={(e) => setYId(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 bg-white py-2 px-3 shadow-2xs"
            >
              {scaleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Cấu hình nâng cao & Bộ lọc */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-slate-200/50">
          <div className="flex flex-wrap items-center gap-6">
            <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={centerVars}
                onChange={(e) => setCenterVars(e.target.checked)}
                className="rounded text-violet-600 focus:ring-violet-500"
              />
              <span className="font-medium">Chuẩn hóa Mean-Centering (Aiken & West 1991)</span>
            </label>

            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500">Phạm vi:</span>
              <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="mod_scope"
                  value="all"
                  checked={scope === 'all'}
                  onChange={() => setScope('all')}
                  className="text-violet-600 focus:ring-violet-500"
                />
                Tất cả
              </label>
              <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="mod_scope"
                  value="verified_clean"
                  checked={scope === 'verified_clean'}
                  onChange={() => setScope('verified_clean')}
                  className="text-violet-600 focus:ring-violet-500"
                />
                Mẫu sạch
              </label>
            </div>
          </div>

          <button
            onClick={handleRunModeration}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-all shadow-xs"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            Chạy Phân Tích Điều Tiết
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Result Display */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6 pt-2">
          {/* Hero KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-[11px] font-medium text-slate-500">Gia tăng phương sai (&Delta;R&sup2;)</div>
              <div className="text-2xl font-bold text-violet-600 mt-1">
                {(result.moderation_effect?.delta_r_squared ?? 0 * 100).toFixed(4)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                F_change = {result.moderation_effect?.delta_f_stat} (p = {result.moderation_effect?.delta_p_value})
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-[11px] font-medium text-slate-500">Hệ số tương tác (b&sup3; X*W)</div>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                {result.moderation_effect?.interaction_b}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                t = {result.moderation_effect?.interaction_t} (p = {result.moderation_effect?.interaction_p})
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-[11px] font-medium text-slate-500">R&sup2; Toàn mô hình (Model 2)</div>
              <div className="text-2xl font-bold text-slate-800 mt-1">
                {result.model_2_moderation?.r_squared}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                F = {result.model_2_moderation?.f_stat} (p = {result.model_2_moderation?.p_value})
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-[11px] font-medium text-slate-500">Kết luận Điều Tiết (Hayes)</div>
              <div className={`text-sm font-bold mt-2 ${
                result.moderation_effect?.is_significant ? 'text-emerald-700' : 'text-slate-600'
              }`}>
                {result.moderation_effect?.is_significant ? 'CÓ Ý NGHĨA THỐNG KÊ' : 'KHÔNG CÓ Ý NGHĨA'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Cỡ mẫu hợp lệ: N = {result.sample_size}</div>
            </div>
          </div>

          {/* Simple Slopes Analysis Table */}
          {result.simple_slopes && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-violet-600" />
                  Phân tích Độ dốc Đơn (Simple Slopes Analysis / Pick-a-Point - Aiken & West 1991)
                </h4>
                <span className="text-[11px] text-slate-500">
                  Tác động có điều kiện của X lên Y tại 3 mức của biến điều tiết W
                </span>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Mức điều tiết (Moderator Level)</th>
                      <th className="py-2.5 px-3">Giá trị W</th>
                      <th className="py-2.5 px-3">Độ dốc (Conditional Slope)</th>
                      <th className="py-2.5 px-3">Sai số chuẩn (SE)</th>
                      <th className="py-2.5 px-3">t-statistic</th>
                      <th className="py-2.5 px-3">p-value</th>
                      <th className="py-2.5 px-3">95% CI</th>
                      <th className="py-2.5 px-3">Ý nghĩa thống kê</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {result.simple_slopes.map((row) => (
                      <tr key={row.level} className="hover:bg-slate-50/60">
                        <td className="py-2 px-3 font-medium">{row.label}</td>
                        <td className="py-2 px-3 font-mono">{row.w_value}</td>
                        <td className="py-2 px-3 font-mono font-bold text-violet-700">{row.slope}</td>
                        <td className="py-2 px-3 font-mono">{row.std_error}</td>
                        <td className="py-2 px-3 font-mono">{row.t_stat}</td>
                        <td className="py-2 px-3 font-mono">{row.p_value}</td>
                        <td className="py-2 px-3 font-mono text-slate-500">
                          [{row.ci_95_lower}, {row.ci_95_upper}]
                        </td>
                        <td className="py-2 px-3">
                          {row.is_significant ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
                              <Check className="w-3 h-3" /> p &lt; .05
                            </span>
                          ) : (
                            <span className="text-[11px] text-slate-400">Không ý nghĩa</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 2D Interaction Plot & Johnson-Neyman Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* SVG Plot */}
            {renderInteractionPlot()}

            {/* Johnson-Neyman Card */}
            {result.johnson_neyman && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-3">
                <div>
                  <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 mb-2">
                    <Layers className="w-3.5 h-3.5 text-violet-600" />
                    Kỹ thuật Johnson-Neyman (1936; Bauer & Curran 2005)
                  </h4>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Xác định điểm chuyển tiếp liên tục trên trục W nơi tác động của X lên Y chuyển từ không có ý nghĩa sang có ý nghĩa thống kê (p &lt; 0.05).
                  </p>

                  <div className="mt-3 p-3 bg-white rounded-lg border border-slate-200/80 space-y-1.5">
                    <div className="text-xs font-semibold text-slate-700">
                      Điểm chuyển tiếp trong miền quan sát:
                    </div>
                    <div className="text-sm font-bold text-violet-700 font-mono">
                      {result.johnson_neyman.points_within_observed_range.length > 0
                        ? result.johnson_neyman.points_within_observed_range.join(', ')
                        : 'Không có điểm chuyển tiếp trong miền quan sát'}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Miền giá trị của biến điều tiết W: [{result.johnson_neyman.observed_moderator_range[0]}, {result.johnson_neyman.observed_moderator_range[1]}]
                    </div>
                  </div>
                </div>

                <div className="p-2.5 bg-violet-50/70 border border-violet-200/60 rounded-lg text-xs text-violet-900 font-medium">
                  Tỷ lệ mẫu nằm trong vùng có ý nghĩa: {result.johnson_neyman.percent_sample_significant}%
                </div>
              </div>
            )}
          </div>

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-violet-600" />
                  Đoạn Trích Minh Bạch APA 7th Edition cho Luận văn & Báo cáo
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-md shadow-2xs hover:bg-slate-50"
                >
                  {copiedApa ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                  {copiedApa ? 'Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed italic border-l-2 border-violet-400 pl-3 bg-white/60 p-2.5 rounded">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
