import React, { useState } from 'react';
import {
  TrendingUp,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  Play,
  Info,
  Table,
  ShieldCheck,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { LinearRegressionReport } from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface Props {
  surveyId: string;
  questions: QuestionItem[];
}

export const LinearRegressionCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [dependentQId, setDependentQId] = useState<string>('');
  const [selectedPredictorIds, setSelectedPredictorIds] = useState<string[]>([]);
  const [report, setReport] = useState<LinearRegressionReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Lọc các câu hỏi dạng thang đo định lượng phù hợp cho biến phụ thuộc và độc lập
  const scaleQuestions = questions.filter(q =>
    ['rating', 'linear_scale', 'number', 'nps', 'likert'].includes(q.question_type) ||
    (q.question_type === 'single_choice' && ['hài lòng', 'đồng ý', 'thang điểm', 'likert', 'mức độ', 'điểm'].some(k => q.title.toLowerCase().includes(k)))
  );

  const handleTogglePredictor = (qId: string) => {
    setSelectedPredictorIds(prev =>
      prev.includes(qId) ? prev.filter(id => id !== qId) : [...prev, qId]
    );
    setReport(null);
  };

  const handleSelectAllPredictors = () => {
    const available = scaleQuestions.filter(q => q.id !== dependentQId).map(q => q.id);
    setSelectedPredictorIds(available);
    setReport(null);
  };

  const handleClearPredictors = () => {
    setSelectedPredictorIds([]);
    setReport(null);
  };

  const handleRunRegression = async () => {
    if (!dependentQId) {
      setError('Vui lòng chọn biến phụ thuộc mục tiêu (Y).');
      return;
    }
    if (selectedPredictorIds.length === 0) {
      setError('Vui lòng chọn tối thiểu 1 biến độc lập dự báo (X).');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runLinearRegression(surveyId, {
        dependent_question_id: dependentQId,
        predictor_question_ids: selectedPredictorIds,
        scope
      });
      setReport(res);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi khớp mô hình hồi quy OLS.');
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!report?.apa_interpretation) return;
    navigator.clipboard.writeText(report.apa_interpretation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mt-6">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 bg-gradient-to-r from-teal-50/50 via-cyan-50/30 to-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-teal-600 text-white rounded-lg shadow-sm">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-800">
                  Hồi quy Tuyến tính Đa biến OLS (Multiple Linear Regression & VIF)
                </h3>
                <span className="px-2 py-0.5 text-xs font-semibold bg-teal-100 text-teal-800 rounded-full">
                  Legendre (1805) & Hair et al. (2010)
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Mô hình hóa tác động dự báo đa biến, phân tích phương sai mô hình (F-test), hệ số chuẩn hóa Beta (β), và chẩn đoán đa cộng tuyến VIF/Tolerance.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <label className="text-xs font-medium text-slate-600">Phạm vi:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
            >
              <option value="all">Tất cả phản hồi hợp lệ</option>
              <option value="verified_clean">Chỉ dữ liệu làm sạch (Clean)</option>
            </select>
          </div>
        </div>

        {/* Input Selectors */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4 bg-white/80 p-4 rounded-xl border border-teal-100/80">
          {/* Dependent Variable Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              1. Biến phụ thuộc mục tiêu (Dependent Variable - Y):
            </label>
            <select
              value={dependentQId}
              onChange={(e) => {
                const newDep = e.target.value;
                setDependentQId(newDep);
                // Loại biến phụ thuộc khỏi danh sách độc lập nếu đang chọn
                setSelectedPredictorIds(prev => prev.filter(id => id !== newDep));
                setReport(null);
              }}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2.5 font-medium text-slate-700 focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
            >
              <option value="">-- Chọn biến mục tiêu cần giải thích / dự báo --</option>
              {scaleQuestions.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          {/* Predictors Multi-Select */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-700">
                2. Các biến độc lập dự báo (Predictors - X₁...Xₚ):
              </label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleSelectAllPredictors}
                  disabled={!dependentQId}
                  className="text-[11px] font-semibold text-teal-700 hover:text-teal-900 disabled:opacity-50"
                >
                  Chọn tất cả
                </button>
                <span className="text-slate-300">|</span>
                <button
                  type="button"
                  onClick={handleClearPredictors}
                  className="text-[11px] font-semibold text-slate-500 hover:text-slate-700"
                >
                  Xóa chọn
                </button>
              </div>
            </div>

            <div className="max-h-36 overflow-y-auto p-2 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
              {scaleQuestions
                .filter(q => q.id !== dependentQId)
                .map(q => {
                  const isChecked = selectedPredictorIds.includes(q.id);
                  return (
                    <label
                      key={q.id}
                      className={`flex items-center gap-2 p-1.5 rounded cursor-pointer text-xs transition-colors ${
                        isChecked ? 'bg-teal-50 text-teal-900 font-semibold' : 'text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleTogglePredictor(q.id)}
                        className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                      />
                      <span className="truncate">{q.title}</span>
                    </label>
                  );
                })}
              {scaleQuestions.length <= 1 && (
                <p className="text-xs text-slate-400 p-2 text-center">
                  Cần tối thiểu 2 câu hỏi thang đo để thực hiện hồi quy.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Execute Button */}
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-slate-500 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-teal-600" />
            Tự động tính ma trận nghịch đảo bình phương cực tiểu OLS, chuẩn hóa hệ số Beta và kiểm định VIF từng biến.
          </p>
          <button
            onClick={handleRunRegression}
            disabled={loading || !dependentQId || selectedPredictorIds.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Đang khớp mô hình OLS...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Khớp Mô Hình Hồi Quy ({selectedPredictorIds.length} biến độc lập)
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2.5 text-rose-700 text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <div>
              <span className="font-semibold">Lỗi hồi quy:</span> {error}
            </div>
          </div>
        )}
      </div>

      {/* Results View */}
      {report && report.status === 'SUCCESS' && (
        <div className="p-6 space-y-6">
          {/* Hero KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* R-Squared Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Hệ Số Xác Định (R²)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-teal-700">
                  {report.model_summary.r_squared.toFixed(3)}
                </span>
                <span className="text-xs text-teal-600 font-medium">
                  ({(report.model_summary.r_squared * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="mt-2 text-xs text-slate-500">
                Phương sai của Y được giải thích bởi mô hình
              </div>
            </div>

            {/* Adjusted R-Squared Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                R² Hiệu Chỉnh (Adjusted R²)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-800">
                  {report.model_summary.r_squared_adjusted.toFixed(3)}
                </span>
                <span className="text-xs text-slate-500">
                  p = {report.predictors_count}
                </span>
              </div>
              <div className="mt-2 text-xs text-slate-500">
                Hiệu chỉnh phạt theo số biến độc lập
              </div>
            </div>

            {/* Model F-Statistic Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Thống Kê F & Mức Ý Nghĩa
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  {report.model_summary.f_stat.toFixed(2)}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  df({report.model_summary.df_regression}, {report.model_summary.df_residual})
                </span>
              </div>
              <div className="mt-2">
                {report.model_summary.is_significant_05 ? (
                  <span className="px-2 py-0.5 text-[11px] font-bold bg-emerald-100 text-emerald-800 rounded-md">
                    Có ý nghĩa (p &lt; .05)
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[11px] font-semibold bg-slate-200 text-slate-600 rounded-md">
                    Không có ý nghĩa
                  </span>
                )}
              </div>
            </div>

            {/* Standard Error of Estimate Card */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Sai Số Chuẩn Ước Lượng (Se)
              </span>
              <div className="text-2xl font-black text-slate-800">
                {report.model_summary.std_error_of_estimate.toFixed(3)}
              </div>
              <div className="mt-2 text-xs text-slate-500">
                Cỡ mẫu phân tích: N = {report.sample_size}
              </div>
            </div>
          </div>

          {/* Multicollinearity VIF Diagnostic Banner */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {report.multicollinearity_risk === 'LOW' ? (
                  <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0" />
                ) : (
                  <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0" />
                )}
                <div>
                  <h4 className="text-xs font-bold text-slate-800">
                    Chẩn đoán Đa cộng tuyến (VIF & Tolerance - Hair et al. 2010):
                  </h4>
                  <p className="text-xs text-slate-600 mt-0.5">
                    Giá trị VIF lớn nhất ghi nhận: <strong className="font-mono text-slate-900">{report.max_vif.toFixed(2)}</strong>.
                    {report.multicollinearity_risk === 'LOW' && ' Tất cả các biến độc lập đều có VIF < 5.0 (Tolerance > 0.20), hoàn toàn đạt chuẩn cho suy luận mô hình.'}
                    {report.multicollinearity_risk === 'MODERATE' && ' Ghi nhận biến có VIF từ 5.0 đến 10.0, mức độ đa cộng tuyến trung bình.'}
                    {report.multicollinearity_risk === 'HIGH' && ' Cảnh báo: VIF >= 10.0 biểu thị đa cộng tuyến nghiêm trọng. Khuyến nghị loại bỏ bớt biến trùng lặp.'}
                  </p>
                </div>
              </div>

              <div>
                <span
                  className={`px-2.5 py-1 text-xs font-bold rounded-lg inline-block ${
                    report.multicollinearity_risk === 'LOW'
                      ? 'bg-emerald-100 text-emerald-800'
                      : report.multicollinearity_risk === 'MODERATE'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  Nguy cơ đa cộng tuyến: {report.multicollinearity_risk}
                </span>
              </div>
            </div>
          </div>

          {/* Regression Coefficients Table */}
          <div>
            <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
              <Table className="w-4 h-4 text-teal-600" />
              Bảng Hệ Số Hồi Quy (Coefficients Table)
            </h4>

            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Biến (Model Term)</th>
                    <th className="py-2.5 px-3 text-right">Hệ số B (Chưa chuẩn hóa)</th>
                    <th className="py-2.5 px-3 text-right">Sai số chuẩn (SE_B)</th>
                    <th className="py-2.5 px-3 text-right">Beta chuẩn hóa (β)</th>
                    <th className="py-2.5 px-3 text-right">Thống kê t</th>
                    <th className="py-2.5 px-3 text-right">P-Value</th>
                    <th className="py-2.5 px-3 text-center">95% CI cho B</th>
                    <th className="py-2.5 px-3 text-center">Tolerance</th>
                    <th className="py-2.5 px-3 text-center">VIF</th>
                    <th className="py-2.5 px-3 text-center">Ý nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  {report.coefficients.map((c, idx) => {
                    const isConst = idx === 0;
                    return (
                      <tr key={idx} className={isConst ? 'bg-slate-50/70 font-semibold' : 'hover:bg-slate-50/50'}>
                        <td className="py-2.5 px-3">
                          <div className="text-slate-900 font-semibold">{c.term}</div>
                          {!isConst && <div className="text-[10px] text-slate-400 font-mono">{c.label}</div>}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                          {c.b_unstandardized > 0 ? `+${c.b_unstandardized.toFixed(3)}` : c.b_unstandardized.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-600">
                          {c.std_error.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-teal-700">
                          {isConst ? '—' : c.beta_standardized.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono">
                          {c.t_stat.toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono">
                          {c.p_value < 0.001 ? '< .001' : c.p_value.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono text-slate-600 text-[11px]">
                          [{c.ci_95_lower.toFixed(2)}, {c.ci_95_upper.toFixed(2)}]
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono text-slate-600">
                          {isConst ? '—' : c.tolerance.toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono">
                          {isConst ? (
                            '—'
                          ) : (
                            <span
                              className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                                c.vif < 5.0 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {c.vif.toFixed(2)}
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {c.is_significant_05 ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-bold bg-emerald-100 text-emerald-800 rounded-md">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              p &lt; .05
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 text-[11px] text-slate-500 bg-slate-100 rounded-md">
                              k.ý.nghĩa
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

          {/* Model ANOVA Table */}
          <div>
            <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
              <Table className="w-4 h-4 text-teal-600" />
              Bảng Phân Tích Phương Sai Mô Hình (Model ANOVA Table)
            </h4>

            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Nguồn biến thiên (Source)</th>
                    <th className="py-2.5 px-3 text-right">Tổng bình phương (SS)</th>
                    <th className="py-2.5 px-3 text-right">Bậc tự do (df)</th>
                    <th className="py-2.5 px-3 text-right">Trung bình bình phương (MS)</th>
                    <th className="py-2.5 px-3 text-right">Thống kê F</th>
                    <th className="py-2.5 px-3 text-right">P-Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  <tr className="hover:bg-teal-50/20">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">Hồi quy (Regression)</td>
                    <td className="py-2.5 px-3 text-right font-mono">{report.anova_table.ss_regression.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{report.anova_table.df_regression}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-semibold text-teal-700">{report.anova_table.ms_regression.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">{report.anova_table.f_stat.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-teal-700">
                      {report.anova_table.p_value < 0.001 ? '< .001' : report.anova_table.p_value.toFixed(4)}
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">Phần dư (Residual)</td>
                    <td className="py-2.5 px-3 text-right font-mono">{report.anova_table.ss_residual.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{report.anova_table.df_residual}</td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-600">{report.anova_table.ms_residual.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                  </tr>
                  <tr className="bg-slate-50 font-bold border-t border-slate-200">
                    <td className="py-2.5 px-3 text-slate-900">Tổng cộng (Total)</td>
                    <td className="py-2.5 px-3 text-right font-mono">{report.anova_table.ss_total.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{report.anova_table.df_total}</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">—</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Edition Narrative Summary */}
          <div className="bg-gradient-to-br from-teal-50/60 via-cyan-50/30 to-white border border-teal-200/80 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-600" />
                <h4 className="text-xs font-bold text-teal-900 uppercase tracking-wider">
                  Diễn giải Học thuật Chuẩn APA 7th Edition
                </h4>
              </div>
              <button
                onClick={handleCopyAPA}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-teal-50 text-teal-700 border border-teal-200 rounded-lg text-xs font-semibold transition-colors shadow-xs"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700">Đã sao chép!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao chép APA 7th</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-slate-800 leading-relaxed font-serif bg-white/70 p-3.5 rounded-lg border border-teal-100 italic">
              "{report.apa_interpretation}"
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!report && !loading && !error && (
        <div className="p-12 text-center text-slate-400">
          <TrendingUp className="w-10 h-10 mx-auto mb-3 text-slate-300" />
          <p className="text-sm font-medium text-slate-600">
            Chưa có kết quả hồi quy OLS
          </p>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
            Chọn 1 biến phụ thuộc mục tiêu (Y) và 1 hoặc nhiều biến độc lập (X) từ danh sách câu hỏi thang đo để bắt đầu phân tích hồi quy đa biến.
          </p>
        </div>
      )}
    </div>
  );
};
