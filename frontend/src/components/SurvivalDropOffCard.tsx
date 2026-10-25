import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  CheckCircle2,
  Clock,
  Compass,
  Copy,
  Info,
  Layers,
  LineChart,
  RefreshCw,
  Sliders,
  Sparkles,
  TrendingDown,
  Users
} from 'lucide-react';
import { api } from '../api/client';
import {
  SurvivalAnalysisResult,
  SurvivalMilestone,
  SurvivalStep
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface SurvivalDropOffCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const SurvivalDropOffCard: React.FC<SurvivalDropOffCardProps> = ({ surveyId, questions }) => {
  const categoricalQuestions = questions.filter(q =>
    ['single_choice', 'boolean', 'rating', 'likert'].includes(q.question_type)
  );

  const [groupingQuestionId, setGroupingQuestionId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'km' | 'milestones' | 'comparison'>('km');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SurvivalAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runSurvivalDropOffAnalysis(surveyId, {
        grouping_question_id: groupingQuestionId || undefined,
        scope
      });
      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể thực hiện phân tích sống sót.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi kết nối khi phân tích sống sót.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-rose-500/10 text-rose-400 rounded-lg border border-rose-500/20">
              <Clock className="w-5 h-5" />
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Phân Tích Sống Sót & Thời Gian Bỏ Dở (Kaplan-Meier & Cox HR)
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-medium border border-rose-500/30">
              Kaplan & Meier 1958
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Mô hình hóa thời gian duy trì tham gia khảo sát (Time-to-Event Survival Analysis) với biến cố kiểm duyệt (Right-Censoring), kiểm định Log-Rank Mantel-Cox so sánh thiết bị/nhóm, và ước lượng tỷ số nguy cơ tức thời (Cox Hazard Ratio).
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white font-medium rounded-lg shadow-lg shadow-rose-500/25 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Đang tính toán S(t)...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Ước Lượng Sống Sót</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Controls */}
      <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-rose-400" />
              <span>Biến phân nhóm so sánh (Grouping Variable):</span>
            </label>
            <select
              value={groupingQuestionId}
              onChange={e => setGroupingQuestionId(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-3 py-2 focus:border-rose-500 focus:outline-none"
            >
              <option value="">Tự động: Thiết bị truy cập (Mobile vs Desktop) hoặc Nhánh A/B</option>
              {categoricalQuestions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-rose-400" />
              <span>Phạm vi kiểm định dữ liệu (Scope):</span>
            </label>
            <select
              value={scope}
              onChange={e => setScope(e.target.value as any)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-3 py-2 focus:border-rose-500 focus:outline-none"
            >
              <option value="all">Toàn bộ phản hồi (All responses)</option>
              <option value="verified_clean">Chỉ mẫu sạch đã kiểm định (Verified clean)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg text-sm text-rose-300 flex items-start gap-2.5">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Empty State when no result yet */}
      {!result && !loading && !error && (
        <div className="p-10 border border-dashed border-slate-800 rounded-xl text-center space-y-3">
          <Clock className="w-10 h-10 mx-auto text-slate-600" />
          <h4 className="text-base font-semibold text-slate-300">Chưa có kết quả phân tích sống sót</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Nhấp "Ước Lượng Sống Sót" để phân tích đường cong duy trì Kaplan-Meier S(t), xác định điểm rơi rụng theo thời gian thực địa và kiểm định tỷ số nguy cơ Cox.
          </p>
        </div>
      )}

      {/* Results Content */}
      {result && (
        <div className="space-y-6">
          {/* Hero KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Tỷ lệ hoàn thành</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-black text-emerald-400">
                {result.overall_completion_rate?.toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-400">
                {result.completed_count}/{result.total_participants} người tham gia
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Tỷ lệ bỏ dở</span>
                <TrendingDown className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-2xl font-black text-rose-400">
                {result.overall_drop_off_rate?.toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-400">
                {result.drop_off_count} trường hợp rơi rụng
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Thời gian duy trì trung vị</span>
                <Clock className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-xl font-black text-amber-400">
                {result.overall_km?.median_survival_time != null
                  ? `${result.overall_km.median_survival_time.toFixed(0)}s`
                  : '> 50% hoàn tất'}
              </div>
              <div className="text-[11px] text-slate-400">
                {result.overall_km?.median_survival_time != null
                  ? `~${(result.overall_km.median_survival_time / 60).toFixed(1)} phút`
                  : 'S(t) không giảm dưới 0.5'}
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Tỷ số nguy cơ Cox (HR)</span>
                <Info className="w-4 h-4 text-violet-400" />
              </div>
              <div className="text-2xl font-black text-violet-400">
                {result.cox_hazard_ratio ? `${result.cox_hazard_ratio.hazard_ratio.toFixed(2)}x` : 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400">
                {result.cox_hazard_ratio
                  ? `95% CI [${result.cox_hazard_ratio.ci_95_lower}, ${result.cox_hazard_ratio.ci_95_upper}]`
                  : 'Cần 2 nhóm để tính'}
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 gap-2">
            <button
              onClick={() => setActiveTab('km')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition border-b-2 flex items-center gap-2 ${
                activeTab === 'km'
                  ? 'border-rose-500 text-rose-400 bg-rose-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <LineChart className="w-4 h-4" />
              <span>Đường Cong Sống Sót Kaplan-Meier</span>
            </button>
            <button
              onClick={() => setActiveTab('milestones')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition border-b-2 flex items-center gap-2 ${
                activeTab === 'milestones'
                  ? 'border-rose-500 text-rose-400 bg-rose-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Award className="w-4 h-4" />
              <span>Mốc Thời Gian Then Chốt</span>
            </button>
            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition border-b-2 flex items-center gap-2 ${
                activeTab === 'comparison'
                  ? 'border-rose-500 text-rose-400 bg-rose-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>So Sánh Nhóm (Log-Rank Test)</span>
            </button>
          </div>

          {/* TAB 1: KM CURVE */}
          {activeTab === 'km' && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
                <span>Hàm Sống Sót Bậc Thang S(t) = P(Thời gian duy trì &gt; t) theo giây</span>
                <span className="text-slate-500">
                  Thời gian quan sát tối đa: {result.overall_km?.max_observed_time}s (~{((result.overall_km?.max_observed_time ?? 0)/60).toFixed(1)} phút)
                </span>
              </div>

              {/* Vector SVG Chart for KM */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-x-auto">
                <svg viewBox="0 0 520 240" className="w-full max-w-2xl mx-auto h-auto">
                  {/* Grid Lines */}
                  {[0.0, 0.25, 0.5, 0.75, 1.0].map(pVal => {
                    const y = 200 - pVal * 170;
                    return (
                      <g key={pVal}>
                        <line x1="50" y1={y} x2="490" y2={y} stroke="#334155" strokeDasharray="2 2" strokeWidth="0.8" />
                        <text x="42" y={y + 3} fill="#94a3b8" fontSize="9" textAnchor="end">
                          {pVal.toFixed(2)}
                        </text>
                      </g>
                    );
                  })}

                  {/* 50% Threshold Reference Line */}
                  <line x1="50" y1="115" x2="490" y2="115" stroke="#f59e0b" strokeDasharray="3 3" strokeWidth="1.0" />
                  <text x="495" y="118" fill="#f59e0b" fontSize="8" textAnchor="start">
                    Mdn (50%)
                  </text>

                  {/* X Axis Grid (5 ticks across max_observed_time) */}
                  {[0.0, 0.25, 0.5, 0.75, 1.0].map((frac, idx) => {
                    const maxT = result.overall_km?.max_observed_time ?? 100;
                    const t = frac * maxT;
                    const x = 50 + frac * 440;
                    return (
                      <g key={idx}>
                        <line x1={x} y1="30" x2={x} y2="200" stroke="#334155" strokeDasharray="2 2" strokeWidth="0.8" />
                        <text x={x} y="215" fill="#94a3b8" fontSize="9" textAnchor="middle">
                          {t.toFixed(0)}s
                        </text>
                      </g>
                    );
                  })}

                  {/* Baselines */}
                  <line x1="50" y1="200" x2="490" y2="200" stroke="#64748b" strokeWidth="1.2" />
                  <line x1="50" y1="30" x2="50" y2="200" stroke="#64748b" strokeWidth="1.2" />

                  {/* Overall KM Path */}
                  {result.overall_km?.svg_path && (
                    <path
                      d={result.overall_km.svg_path}
                      fill="none"
                      stroke="#f43f5e"
                      strokeWidth="2.5"
                    />
                  )}

                  {/* Group 1 & Group 2 comparison paths if available */}
                  {result.group_comparison && (
                    <>
                      <path
                        d={result.group_comparison.group_1.svg_path}
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="1.8"
                        strokeDasharray="4 2"
                      />
                      <path
                        d={result.group_comparison.group_2.svg_path}
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="1.8"
                        strokeDasharray="4 2"
                      />
                    </>
                  )}

                  {/* Axis Title */}
                  <text x="270" y="232" fill="#cbd5e1" fontSize="10" textAnchor="middle" fontWeight="600">
                    Thời Gian Trôi Qua Từ Khi Bắt Đầu (Giây)
                  </text>
                  <text x="18" y="115" fill="#cbd5e1" fontSize="10" textAnchor="middle" transform="rotate(-90, 18, 115)" fontWeight="600">
                    Xác Suất Sống Sót S(t)
                  </text>
                </svg>
              </div>

              {/* Chart Legend */}
              <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-slate-300">
                <span className="flex items-center gap-2">
                  <span className="w-4 h-0.5 bg-rose-500" /> Toàn bộ khảo sát S(t)
                </span>
                {result.group_comparison && (
                  <>
                    <span className="flex items-center gap-2 text-blue-400">
                      <span className="w-4 h-0.5 border-t border-dashed border-blue-400" /> Nhóm {result.group_comparison.group_1.name}
                    </span>
                    <span className="flex items-center gap-2 text-emerald-400">
                      <span className="w-4 h-0.5 border-t border-dashed border-emerald-400" /> Nhóm {result.group_comparison.group_2.name}
                    </span>
                  </>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: MILESTONES */}
          {activeTab === 'milestones' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                {result.milestones?.map(m => (
                  <div key={m.time_seconds} className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-2">
                    <div className="text-xs text-slate-400 flex items-center justify-between">
                      <span className="font-bold text-white">Mốc {m.time_minutes} phút</span>
                      <span>({m.time_seconds}s)</span>
                    </div>
                    <div className="text-2xl font-black text-rose-400">
                      {m.retention_percentage}%
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Tỷ lệ duy trì sống sót
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-rose-500 h-1.5 rounded-full"
                        style={{ width: `${m.retention_percentage}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-500 flex justify-between">
                      <span>Rơi rụng: {m.dropout_percentage}%</span>
                      <span>S(t) = {m.survival_probability}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: GROUP COMPARISON & LOG-RANK TEST */}
          {activeTab === 'comparison' && (
            <div className="space-y-4">
              {result.log_rank_test ? (
                <div className="space-y-4">
                  <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <Users className="w-4 h-4 text-indigo-400" />
                        <span>Kiểm Định Log-Rank (Mantel-Cox) So Sánh 2 Nhóm</span>
                      </h4>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        result.log_rank_test.is_statistically_significant
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}>
                        {result.log_rank_test.is_statistically_significant
                          ? 'Khác biệt có ý nghĩa (p < 0.05)'
                          : 'Không khác biệt có ý nghĩa (p ≥ 0.05)'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-[11px] text-slate-400">Thống kê Chi-Square</div>
                        <div className="text-lg font-bold text-white">{result.log_rank_test.chi2_statistic}</div>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-[11px] text-slate-400">Bậc tự do (df)</div>
                        <div className="text-lg font-bold text-white">{result.log_rank_test.degrees_of_freedom}</div>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-[11px] text-slate-400">Mức ý nghĩa (p-value)</div>
                        <div className={`text-lg font-bold ${result.log_rank_test.p_value < 0.05 ? 'text-rose-400' : 'text-slate-300'}`}>
                          {result.log_rank_test.p_value}
                        </div>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-[11px] text-slate-400">Tỷ số nguy cơ Cox (HR)</div>
                        <div className="text-lg font-bold text-violet-400">
                          {result.cox_hazard_ratio ? `${result.cox_hazard_ratio.hazard_ratio}x` : 'N/A'}
                        </div>
                      </div>
                    </div>

                    {result.cox_hazard_ratio && (
                      <div className="p-3 bg-violet-950/20 border border-violet-500/20 rounded-lg text-xs text-violet-200">
                        {result.cox_hazard_ratio.risk_interpretation}
                      </div>
                    )}
                  </div>

                  {/* Comparison Breakdown Table */}
                  {result.group_comparison && (
                    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/40">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-slate-900/80 text-slate-400 uppercase text-[11px] font-semibold border-b border-slate-800">
                          <tr>
                            <th className="p-3">Nhóm Đối Tượng</th>
                            <th className="p-3 text-right">Quy Mô Mẫu (N)</th>
                            <th className="p-3 text-right">Số Ca Bỏ Dở</th>
                            <th className="p-3 text-right">Số Ca Kỳ Vọng</th>
                            <th className="p-3 text-right">Thời Gian Trung Vị (Mdn)</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          <tr>
                            <td className="p-3 font-semibold text-blue-400">{result.group_comparison.group_1.name}</td>
                            <td className="p-3 text-right font-mono">{result.group_comparison.group_1.sample_size}</td>
                            <td className="p-3 text-right font-mono text-rose-400">{result.log_rank_test.observed_events_1}</td>
                            <td className="p-3 text-right font-mono text-slate-400">{result.log_rank_test.expected_events_1}</td>
                            <td className="p-3 text-right font-mono text-amber-400">
                              {result.group_comparison.group_1.median_survival != null
                                ? `${result.group_comparison.group_1.median_survival}s`
                                : '> 50%'}
                            </td>
                          </tr>
                          <tr>
                            <td className="p-3 font-semibold text-emerald-400">{result.group_comparison.group_2.name}</td>
                            <td className="p-3 text-right font-mono">{result.group_comparison.group_2.sample_size}</td>
                            <td className="p-3 text-right font-mono text-rose-400">{result.log_rank_test.observed_events_2}</td>
                            <td className="p-3 text-right font-mono text-slate-400">{result.log_rank_test.expected_events_2}</td>
                            <td className="p-3 text-right font-mono text-amber-400">
                              {result.group_comparison.group_2.median_survival != null
                                ? `${result.group_comparison.group_2.median_survival}s`
                                : '> 50%'}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-6 border border-slate-800 rounded-xl text-center text-xs text-slate-400">
                  Chưa có thông tin so sánh 2 nhóm. Chọn một câu hỏi phân loại (ví dụ: Thiết bị hoặc Nhân khẩu học) trong thanh cấu hình và nhấn "Ước Lượng Sống Sót" để kích hoạt kiểm định Log-Rank.
                </div>
              )}
            </div>
          )}

          {/* APA 7th Edition Narrative Summary */}
          {result.apa_narrative && (
            <div className="bg-rose-950/20 border border-rose-500/20 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 bg-rose-500/20 text-rose-400 rounded">
                    <Sparkles className="w-4 h-4" />
                  </span>
                  <h4 className="text-sm font-bold text-white">Thuyết Minh Học Thuật Chuẩn APA 7th Edition</h4>
                </div>
                <button
                  onClick={handleCopyAPA}
                  className="flex items-center gap-1.5 px-3 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 rounded text-xs transition border border-rose-500/30"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
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
              <p className="text-xs text-slate-300 leading-relaxed font-serif bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
