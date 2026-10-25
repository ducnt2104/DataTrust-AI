import React, { useState, useEffect } from 'react';
import {
  BrainCircuit, Clock, AlertTriangle, CheckCircle2, Copy, Check,
  Zap, Info, TrendingDown, TrendingUp, HelpCircle, Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import { SurveyPacingReport, QuestionPacingAnalysis } from '../types/survey';

interface Props {
  surveyId: string;
}

export const CognitivePacingCard: React.FC<Props> = ({ surveyId }) => {
  const [data, setData] = useState<SurveyPacingReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [filterTier, setFilterTier] = useState<string>('all');

  useEffect(() => {
    loadPacingData();
  }, [surveyId]);

  const loadPacingData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getCognitivePacingAnalytics(surveyId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi tải dữ liệu gánh nặng nhận thức.');
    } finally {
      setLoading(false);
    }
  };

  const copyApa = () => {
    if (!data?.survey_level?.apa_interpretation) return;
    navigator.clipboard.writeText(data.survey_level.apa_interpretation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex items-center justify-center py-12 text-slate-400 text-xs gap-2">
        <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <span>Đang phân tích gánh nặng nhận thức &amp; nhịp độ trả lời...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-2 text-rose-600 text-xs font-semibold">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error || 'Chưa đủ dữ liệu để phân tích nhịp độ nhận thức.'}</span>
        </div>
      </div>
    );
  }

  const { survey_level, question_analyses } = data;
  const filteredQuestions = filterTier === 'all'
    ? question_analyses
    : question_analyses.filter(q => q.burden_tier.toLowerCase() === filterTier.toLowerCase());

  // Tính tỷ lệ phần trăm phân bố người trả lời
  const totalResp = survey_level.actual_sample_size || 1;
  const dist = survey_level.respondent_pacing_distribution;
  const pSpeeding = Math.round((dist.severe_speeding / totalResp) * 100);
  const pRushed = Math.round((dist.rushed / totalResp) * 100);
  const pOptimal = Math.round((dist.optimal / totalResp) * 100);
  const pDeliberate = Math.round((dist.deliberate / totalResp) * 100);

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Header */}
      <div className="p-6 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <h3 className="text-base font-extrabold tracking-tight">
              Gánh Nặng Nhận Thức &amp; Nhịp Độ Trả Lời (Cognitive Burden &amp; Pacing)
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 font-bold border border-indigo-400/20 font-mono">
              Couper • Krosnick • Dillman
            </span>
          </div>
          <p className="text-xs text-indigo-200/80">
            Đo lường thời gian đọc lý thuyết, phát hiện chọn lướt (Satisficing) và đường cong mệt mỏi nhận thức
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            onClick={copyApa}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs transition-colors border border-white/20 shadow-xs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Đã sao chép APA' : 'Sao chép APA 7th'}</span>
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Pacing Ratio */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Tỷ số Nhịp độ (Pacing)</span>
              <Clock className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-slate-900">
                {survey_level.overall_pacing_ratio}x
              </span>
              <span className="text-[11px] font-bold text-slate-500">
                (Thực tế / Lý thuyết)
              </span>
            </div>
            <div className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md inline-block border border-indigo-100">
              {survey_level.engagement_level}
            </div>
          </div>

          {/* Card 2: Expected vs Actual Duration */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Thời gian Đọc Lý thuyết</span>
              <Zap className="w-4 h-4 text-amber-600" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-slate-900">
                {survey_level.expected_reading_seconds}s
              </span>
              <span className="text-[11px] text-slate-500 font-semibold">
                (~{survey_level.expected_reading_minutes} phút)
              </span>
            </div>
            <div className="text-[11px] text-slate-600">
              Trung vị thực tế: <strong className="text-slate-800">{survey_level.actual_median_seconds}s</strong> (N={survey_level.actual_sample_size})
            </div>
          </div>

          {/* Card 3: Average Question Burden */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Điểm Gánh Nặng TB</span>
              <BrainCircuit className="w-4 h-4 text-teal-600" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-slate-900">
                {survey_level.average_question_burden}
              </span>
              <span className="text-xs text-slate-400 font-bold">/ 100</span>
            </div>
            <div className="text-[11px] text-slate-600">
              {survey_level.high_burden_questions_count > 0 ? (
                <span className="text-amber-700 font-bold">
                  ⚠️ {survey_level.high_burden_questions_count} câu hỏi tải trọng cao (≥ 50)
                </span>
              ) : (
                <span className="text-emerald-700 font-bold">
                  ✓ Toàn bộ câu hỏi tải trọng tối ưu
                </span>
              )}
            </div>
          </div>

          {/* Card 4: Cognitive Fatigue Risk */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Mệt Mỏi Nhận Thức</span>
              {survey_level.fatigue_risk ? (
                <TrendingDown className="w-4 h-4 text-rose-600" />
              ) : (
                <TrendingUp className="w-4 h-4 text-emerald-600" />
              )}
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-black text-slate-900">
                {survey_level.fatigue_risk ? 'Cảnh Báo' : 'An Toàn'}
              </span>
              <span className="text-[11px] font-mono text-slate-500">
                (Slope: {survey_level.fatigue_slope})
              </span>
            </div>
            <div className="text-[11px] text-slate-600 leading-snug truncate" title={survey_level.fatigue_note}>
              {survey_level.fatigue_note}
            </div>
          </div>
        </div>

        {/* Pacing Distribution Stacked Bar */}
        {survey_level.actual_sample_size > 0 && (
          <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">
                Phân Bố Mức Độ Tương Tác Nhận Thức (N = {survey_level.actual_sample_size})
              </span>
              <span className="text-[11px] text-slate-500">
                Phân loại theo ngưỡng Couper et al. (2001)
              </span>
            </div>

            {/* Multi-segment Progress Bar */}
            <div className="w-full h-3 rounded-full bg-slate-200 overflow-hidden flex shadow-inner">
              {pSpeeding > 0 && (
                <div
                  style={{ width: `${pSpeeding}%` }}
                  className="bg-rose-500 h-full transition-all duration-300"
                  title={`Severe Speeding (<0.30x): ${dist.severe_speeding} mẫu (${pSpeeding}%)`}
                />
              )}
              {pRushed > 0 && (
                <div
                  style={{ width: `${pRushed}%` }}
                  className="bg-amber-500 h-full transition-all duration-300"
                  title={`Rushed (0.30x-0.65x): ${dist.rushed} mẫu (${pRushed}%)`}
                />
              )}
              {pOptimal > 0 && (
                <div
                  style={{ width: `${pOptimal}%` }}
                  className="bg-emerald-500 h-full transition-all duration-300"
                  title={`Optimal (0.65x-1.80x): ${dist.optimal} mẫu (${pOptimal}%)`}
                />
              )}
              {pDeliberate > 0 && (
                <div
                  style={{ width: `${pDeliberate}%` }}
                  className="bg-indigo-500 h-full transition-all duration-300"
                  title={`Deliberate / Distracted (>1.80x): ${dist.deliberate} mẫu (${pDeliberate}%)`}
                />
              )}
            </div>

            {/* Legend */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
                <span className="text-slate-600">Chọn bừa / Vội vã (&lt;0.3x): <strong>{pSpeeding}%</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
                <span className="text-slate-600">Đọc lướt (0.3x–0.65x): <strong>{pRushed}%</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
                <span className="text-slate-600">Tập trung tối ưu: <strong>{pOptimal}%</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 shrink-0" />
                <span className="text-slate-600">Cân nhắc sâu / Phân tâm: <strong>{pDeliberate}%</strong></span>
              </div>
            </div>
          </div>
        )}

        {/* Cognitive Load Curve (SVG Visualization) */}
        {question_analyses.length >= 2 && (
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">
                Đường Cong Tải Trọng Nhận Thức Qua Các Câu Hỏi (Cognitive Load Curve)
              </span>
              <span className="text-[11px] text-slate-500">
                Trục tung: Điểm gánh nặng [0 - 100] • Trục hoành: Thứ tự câu hỏi #1 - #{question_analyses.length}
              </span>
            </div>

            <div className="w-full overflow-x-auto py-2">
              <svg viewBox={`0 0 ${Math.max(600, question_analyses.length * 70)} 120`} className="w-full h-28">
                {/* Horizontal guide lines */}
                <line x1="40" y1="20" x2={Math.max(600, question_analyses.length * 70)} y2="20" stroke="#fecdd3" strokeDasharray="3 3" />
                <text x="5" y="24" fill="#f43f5e" fontSize="9" fontWeight="bold">70+</text>

                <line x1="40" y1="50" x2={Math.max(600, question_analyses.length * 70)} y2="50" stroke="#fed7aa" strokeDasharray="3 3" />
                <text x="5" y="54" fill="#f59e0b" fontSize="9" fontWeight="bold">50</text>

                <line x1="40" y1="100" x2={Math.max(600, question_analyses.length * 70)} y2="100" stroke="#e2e8f0" />
                <text x="15" y="104" fill="#94a3b8" fontSize="9">0</text>

                {/* Connecting Trend Line */}
                {(() => {
                  const points = question_analyses.map((q, idx) => {
                    const x = 60 + idx * 65;
                    const y = 100 - (q.cognitive_burden_score / 100) * 80;
                    return `${x},${y}`;
                  }).join(' ');

                  return (
                    <polyline
                      fill="none"
                      stroke="#6366f1"
                      strokeWidth="2.5"
                      points={points}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  );
                })()}

                {/* Data Points */}
                {question_analyses.map((q, idx) => {
                  const x = 60 + idx * 65;
                  const y = 100 - (q.cognitive_burden_score / 100) * 80;
                  const color = q.burden_tier === 'Critical' ? '#f43f5e' : q.burden_tier === 'High' ? '#f59e0b' : '#10b981';

                  return (
                    <g key={q.id}>
                      <circle cx={x} cy={y} r="5" fill={color} stroke="#ffffff" strokeWidth="2" />
                      <text x={x} y="115" textAnchor="middle" fill="#64748b" fontSize="9" fontWeight="bold">
                        #{q.order_index}
                      </text>
                      <text x={x} y={y - 8} textAnchor="middle" fill="#334155" fontSize="9" fontWeight="bold">
                        {Math.round(q.cognitive_burden_score)}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>
        )}

        {/* Question-level Analysis Table */}
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h4 className="text-xs font-bold text-slate-800">
              Chi Tiết Đánh Giá Gánh Nặng &amp; Khuyến Nghị Tái Thiết Kế (Don Dillman Standard)
            </h4>

            {/* Filter Buttons */}
            <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-xl border border-slate-200 self-start">
              {['all', 'critical', 'high', 'moderate', 'low'].map(tier => (
                <button
                  key={tier}
                  type="button"
                  onClick={() => setFilterTier(tier)}
                  className={`px-2 py-0.5 text-[11px] font-bold rounded-lg transition-all ${
                    filterTier === tier
                      ? 'bg-white text-indigo-700 shadow-xs border border-indigo-200'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {tier === 'all' ? 'Tất cả' : tier === 'critical' ? '🔴 Quá tải' : tier === 'high' ? '🟠 Cao' : tier === 'moderate' ? 'Vừa' : '🟢 Thấp'}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-2xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/90 text-slate-600 border-b border-slate-200 font-bold">
                <tr>
                  <th className="py-2.5 px-3 w-12 text-center">#</th>
                  <th className="py-2.5 px-3">Câu hỏi khảo sát</th>
                  <th className="py-2.5 px-3 text-center">Dung lượng</th>
                  <th className="py-2.5 px-3 text-center">Thời gian đọc</th>
                  <th className="py-2.5 px-3 text-center">Tải nhận thức</th>
                  <th className="py-2.5 px-3">Cảnh báo &amp; Khuyến nghị Don Dillman</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredQuestions.map((q) => {
                  const badgeColor =
                    q.burden_tier === 'Critical'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : q.burden_tier === 'High'
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : q.burden_tier === 'Moderate'
                      ? 'bg-blue-50 text-blue-700 border-blue-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200';

                  return (
                    <tr key={q.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-2.5 px-3 text-center font-bold text-slate-500">
                        #{q.order_index}
                      </td>
                      <td className="py-2.5 px-3 max-w-xs">
                        <div className="font-semibold text-slate-800 truncate" title={q.title}>
                          {q.title}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          {q.question_type} • {q.num_options} lựa chọn
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-center font-mono">
                        <span className="font-bold text-slate-700">{q.total_words}</span>
                        <span className="text-[10px] text-slate-400 block">từ</span>
                      </td>
                      <td className="py-2.5 px-3 text-center font-mono">
                        <span className="font-bold text-indigo-700">{q.expected_reading_seconds}s</span>
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-bold border ${badgeColor}`}>
                          {q.cognitive_burden_score} • {q.burden_tier}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 max-w-sm">
                        {q.risk_factors.length > 0 ? (
                          <div className="space-y-1">
                            {q.risk_factors.map((rf, idx) => (
                              <div key={idx} className="text-[11px] font-semibold text-rose-700 flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3 shrink-0" />
                                <span>{rf}</span>
                              </div>
                            ))}
                            {q.redesign_recommendation && (
                              <div className="text-[11px] text-slate-600 bg-slate-50 p-1.5 rounded-lg border border-slate-200/80 leading-snug">
                                <Sparkles className="w-3 h-3 text-indigo-600 inline mr-1" />
                                <span>{q.redesign_recommendation}</span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-emerald-700 font-semibold text-[11px] flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3 shrink-0" /> Tối ưu, không có điểm nghẽn
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* APA Citation Box */}
        <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-200/80 text-xs space-y-1.5 text-indigo-950">
          <div className="flex items-center gap-1.5 font-bold text-indigo-900">
            <Info className="w-4 h-4 text-indigo-700 shrink-0" />
            <span>Diễn Giải Phương Pháp Luận Học Thuật (APA 7th Edition Ready):</span>
          </div>
          <p className="text-slate-700 text-xs leading-relaxed italic bg-white p-3 rounded-xl border border-indigo-100 shadow-xs">
            "{survey_level.apa_interpretation}"
          </p>
        </div>
      </div>
    </div>
  );
};
