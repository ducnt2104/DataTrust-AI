import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Copy,
  GitBranch,
  GitCompare,
  Info,
  Layers,
  LineChart,
  RefreshCw,
  Scale,
  Sliders,
  Sparkles,
  TrendingUp,
  Users
} from 'lucide-react';
import { api } from '../api/client';
import { DiDAnalysisResult } from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface DifferenceInDifferencesCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const DifferenceInDifferencesCard: React.FC<DifferenceInDifferencesCardProps> = ({ surveyId, questions }) => {
  const numericQuestions = questions.filter(q =>
    ['rating', 'linear_scale', 'nps', 'number'].includes(q.question_type)
  );

  const categoricalQuestions = questions.filter(q =>
    ['single_choice', 'dropdown', 'radio', 'text', 'boolean'].includes(q.question_type)
  );

  const [outcomeQId, setOutcomeQId] = useState<string>(numericQuestions[0]?.id || '');
  const [treatmentQId, setTreatmentQId] = useState<string>(categoricalQuestions[0]?.id || '');
  const [timeQId, setTimeQId] = useState<string>(categoricalQuestions[1]?.id || '');
  const [treatmentVal, setTreatmentVal] = useState<string>('');
  const [postVal, setPostVal] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'trajectory' | 'cells' | 'regression'>('trajectory');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiDAnalysisResult | null>(null);
  const [copied, setCopied] = useState(false);

  const handleRunAnalysis = async () => {
    if (!outcomeQId || !treatmentQId || !timeQId) {
      setError('Vui lòng chọn đầy đủ biến kết quả Y, biến nhóm can thiệp và biến thời điểm.');
      return;
    }
    if (treatmentQId === timeQId) {
      setError('Biến nhóm can thiệp và biến thời điểm phải là hai câu hỏi phân loại khác nhau.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runDiDAnalysis(surveyId, {
        outcome_question_id: outcomeQId,
        treatment_question_id: treatmentQId,
        time_question_id: timeQId,
        treatment_value: treatmentVal.trim() || null,
        post_value: postVal.trim() || null,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INVALID_TREATMENT_GROUPS' || res.status === 'INVALID_TIME_PERIODS' || res.status === 'EMPTY_CELL') {
        setError(res.message || 'Chưa đủ dữ liệu mẫu tại 4 ô 2x2 để phân tích DiD.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích Difference-in-Differences.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-teal-50 text-teal-600 rounded-xl">
              <Scale className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-bold text-slate-800">
              Khác biệt trong Khác biệt (Difference-in-Differences - DiD)
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-teal-100 text-teal-700">
              Card & Krueger 1994 · Nobel 2021
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Phương pháp đánh giá tác động nhân quả chính sách (Policy Impact Evaluation). 
            Bóc tách hiệu ứng can thiệp thuần túy (ATT) bằng cách loại trừ đồng thời độ lệch chọn ban đầu (selection bias) 
            và xu thế biến thiên tự nhiên theo thời gian (macroeconomic drift).
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading || !outcomeQId || !treatmentQId || !timeQId}
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-semibold shadow-sm transition-all shadow-teal-200"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Đang ước lượng DiD...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Ước lượng Tác động DiD
            </>
          )}
        </button>
      </div>

      {/* Parameter Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-50/70 p-4 rounded-xl border border-slate-200/70">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Biến Kết quả Đo lường Y <span className="text-rose-500">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 32 ? q.title.slice(0, 32) + '...' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Biến Nhóm Can thiệp D (Treatment vs Control) <span className="text-rose-500">*</span>
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {categoricalQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 32 ? q.title.slice(0, 32) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Biến Thời điểm T (Pre vs Post) <span className="text-rose-500">*</span>
          </label>
          <select
            value={timeQId}
            onChange={(e) => setTimeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {categoricalQuestions.filter(q => q.id !== treatmentQId).map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 32 ? q.title.slice(0, 32) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Phạm vi dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Đã làm sạch chống gian lận (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Result presentation */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Treatment Effect ATT Card */}
            <div className="bg-gradient-to-br from-teal-50/70 to-teal-100/30 border border-teal-200/80 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-teal-800">Tác động Nhân quả (ATT)</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  result.did_treatment_effect?.is_statistically_significant
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  {result.did_treatment_effect?.is_statistically_significant ? 'Có ý nghĩa (p < .05)' : 'Không có ý nghĩa'}
                </span>
              </div>
              <div className="text-2xl font-extrabold text-teal-950 mt-2">
                δ = {result.did_treatment_effect?.att_estimate !== undefined
                  ? (result.did_treatment_effect.att_estimate > 0 ? `+${result.did_treatment_effect.att_estimate}` : result.did_treatment_effect.att_estimate)
                  : '--'}
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                SE = {result.did_treatment_effect?.std_error} | t = {result.did_treatment_effect?.t_statistic} (p = {result.did_treatment_effect?.p_value})
              </p>
            </div>

            {/* Relative Gain % Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Mức Thay đổi Thuần Túy</span>
                <TrendingUp className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                {result.did_treatment_effect?.relative_gain_pct !== undefined
                  ? (result.did_treatment_effect.relative_gain_pct > 0 ? `+${result.did_treatment_effect.relative_gain_pct}%` : `${result.did_treatment_effect.relative_gain_pct}%`)
                  : '--'}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                So với quỹ đạo phản thực tế giả định ({result.cell_means_2x2?.counterfactual_post})
              </p>
            </div>

            {/* Sample Size across cells */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Tổng Mẫu Quan sát</span>
                <Users className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                N = {result.sample_size}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Phân bổ đều qua 4 ô 2x2 (Treatment/Control × Pre/Post)
              </p>
            </div>

            {/* Natural Drift & Selection Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Xu thế Tự nhiên & Lệch ban đầu</span>
                <GitBranch className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-xs font-mono font-semibold text-slate-800 mt-2 space-y-1">
                <div>Lệch chọn cơ sở (β₁): {result.regression_coefficients?.baseline_selection_beta_1}</div>
                <div>Xu thế chung (β₂): {result.regression_coefficients?.time_trend_drift_beta_2}</div>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Mô hình TWFE đạt R² = {result.regression_coefficients?.r_squared}
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200">
            <button
              onClick={() => setActiveTab('trajectory')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'trajectory'
                  ? 'border-teal-600 text-teal-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <LineChart className="w-3.5 h-3.5" />
              Đồ thị Quỹ đạo DiD (Causal Trajectory)
            </button>
            <button
              onClick={() => setActiveTab('cells')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'cells'
                  ? 'border-teal-600 text-teal-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <GitCompare className="w-3.5 h-3.5" />
              Bảng Phân rã 2x2 Cell Means
            </button>
            <button
              onClick={() => setActiveTab('regression')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'regression'
                  ? 'border-teal-600 text-teal-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              Hệ số Hồi quy Hai chiều Cố định (TWFE)
            </button>
          </div>

          {/* Tab 1: Trajectory Vector SVG */}
          {activeTab === 'trajectory' && (
            <div className="space-y-4">
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <div className="flex items-center justify-between mb-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-teal-400"></span>
                    <span className="text-slate-200 font-semibold">
                      Quỹ đạo Thực tế vs Phản thực tế (Parallel Trends Counterfactual)
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-[11px]">
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <span className="w-2.5 h-0.5 bg-emerald-500"></span>
                      Can thiệp ({result.groups?.treatment_name})
                    </span>
                    <span className="flex items-center gap-1 text-sky-400 font-semibold">
                      <span className="w-2.5 h-0.5 bg-sky-500"></span>
                      Đối chứng ({result.groups?.control_name})
                    </span>
                    <span className="flex items-center gap-1 text-purple-300 font-semibold">
                      <span className="w-2.5 h-0.5 border-t border-dashed border-purple-400"></span>
                      Phản thực tế
                    </span>
                  </div>
                </div>

                {result.svg_trajectory_chart && (
                  <div
                    dangerouslySetInnerHTML={{ __html: result.svg_trajectory_chart }}
                    className="w-full overflow-x-auto"
                  />
                )}
              </div>
            </div>
          )}

          {/* Tab 2: 2x2 Cell Means Table */}
          {activeTab === 'cells' && result.cell_means_2x2 && (
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
                <h4 className="text-xs font-bold text-slate-800">
                  Bảng Phân rã Trung bình 2x2 Cell Means (Card & Krueger 1994)
                </h4>
                <p className="text-[11px] text-slate-500">
                  Hiệu ứng DiD = (Sau_Treatment - Trước_Treatment) - (Sau_Control - Trước_Control)
                </p>
              </div>
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Phân nhóm</th>
                    <th className="py-2.5 px-3">Trước can thiệp (Pre)</th>
                    <th className="py-2.5 px-3">Sau can thiệp (Post)</th>
                    <th className="py-2.5 px-3">Chênh lệch theo thời gian (Δ)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  <tr>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      Nhóm Đối chứng ({result.groups?.control_name})
                    </td>
                    <td className="py-2.5 px-3">
                      {result.cell_means_2x2.control_pre.mean} <span className="text-[10px] text-slate-400">(n={result.cell_means_2x2.control_pre.n})</span>
                    </td>
                    <td className="py-2.5 px-3">
                      {result.cell_means_2x2.control_post.mean} <span className="text-[10px] text-slate-400">(n={result.cell_means_2x2.control_post.n})</span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-sky-700">
                      {result.cell_means_2x2.control_post.diff}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      Nhóm Can thiệp ({result.groups?.treatment_name})
                    </td>
                    <td className="py-2.5 px-3">
                      {result.cell_means_2x2.treat_pre.mean} <span className="text-[10px] text-slate-400">(n={result.cell_means_2x2.treat_pre.n})</span>
                    </td>
                    <td className="py-2.5 px-3">
                      {result.cell_means_2x2.treat_post.mean} <span className="text-[10px] text-slate-400">(n={result.cell_means_2x2.treat_post.n})</span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-emerald-700">
                      {result.cell_means_2x2.treat_post.diff}
                    </td>
                  </tr>
                  <tr className="bg-teal-50/60 font-bold">
                    <td className="py-2.5 px-3 text-teal-950">
                      Hiệu ứng Can thiệp DiD (Δ Treat - Δ Control)
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">--</td>
                    <td className="py-2.5 px-3 text-slate-400">
                      Phản thực tế: {result.cell_means_2x2.counterfactual_post}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-teal-700 text-sm">
                      {result.did_treatment_effect?.att_estimate}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: TWFE Regression Table */}
          {activeTab === 'regression' && result.regression_coefficients && (
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
                <h4 className="text-xs font-bold text-slate-800">
                  Ước lượng Hồi quy Tuyến tính OLS Hai chiều Cố định (TWFE Specification)
                </h4>
                <p className="text-[11px] text-slate-500 font-mono">
                  Y = β₀ + β₁·Treated + β₂·Post + δ·(Treated × Post) + ε
                </p>
              </div>
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Hệ số</th>
                    <th className="py-2.5 px-3">Ý nghĩa kinh tế / chính sách</th>
                    <th className="py-2.5 px-3">Ước lượng (β)</th>
                    <th className="py-2.5 px-3">Sai số SE</th>
                    <th className="py-2.5 px-3">Thống kê t</th>
                    <th className="py-2.5 px-3">p-value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  <tr>
                    <td className="py-2 px-3 font-mono font-bold">β₀ (Intercept)</td>
                    <td className="py-2 px-3">Mức kết quả cơ sở (Control Pre)</td>
                    <td className="py-2 px-3 font-mono font-semibold">{result.regression_coefficients.intercept_beta_0}</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-mono font-bold">β₁ (Treated)</td>
                    <td className="py-2 px-3">Độ lệch lựa chọn ban đầu trước can thiệp</td>
                    <td className="py-2 px-3 font-mono font-semibold">{result.regression_coefficients.baseline_selection_beta_1}</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-mono font-bold">β₂ (Post)</td>
                    <td className="py-2 px-3">Xu thế thời gian chung (macro trend)</td>
                    <td className="py-2 px-3 font-mono font-semibold">{result.regression_coefficients.time_trend_drift_beta_2}</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                    <td className="py-2 px-3 text-slate-400">--</td>
                  </tr>
                  <tr className="bg-teal-50/60 font-bold">
                    <td className="py-2 px-3 font-mono text-teal-800">δ (Interaction)</td>
                    <td className="py-2 px-3 text-teal-900">Tác động can thiệp nhân quả thuần túy (ATT)</td>
                    <td className="py-2 px-3 font-mono text-teal-700 text-sm">
                      {result.regression_coefficients.interaction_att_delta}
                    </td>
                    <td className="py-2 px-3 font-mono">{result.did_treatment_effect?.std_error}</td>
                    <td className="py-2 px-3 font-mono">{result.did_treatment_effect?.t_statistic}</td>
                    <td className="py-2 px-3 font-mono text-teal-700">
                      {result.did_treatment_effect?.p_value}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-teal-50/40 border border-teal-100 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-950 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-teal-600" />
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative || '')}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-white hover:bg-teal-50 border border-teal-200 text-teal-700 rounded-lg text-xs font-semibold shadow-xs transition-all"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Đã sao chép!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA 7th
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic bg-white/80 p-3 rounded-lg border border-teal-100">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
