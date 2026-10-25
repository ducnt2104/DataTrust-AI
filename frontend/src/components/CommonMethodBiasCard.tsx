import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, ShieldCheck, Sparkles, AlertTriangle, RefreshCw,
  Copy, Check, Table, Filter, Layers, Percent, Activity,
  BookOpen, HelpCircle, ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, CommonMethodBiasResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const CommonMethodBiasCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc các biến dạng thang đo / định lượng
  const scaleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  const [selectedItemIds, setSelectedItemIds] = useState<string[]>([]);
  const [markerQuestionId, setMarkerQuestionId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  useEffect(() => {
    if (scaleQuestions.length >= 2 && selectedItemIds.length === 0) {
      setSelectedItemIds(scaleQuestions.map((q) => q.question_id));
    }
  }, [questions]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CommonMethodBiasResult | null>(null);
  const [copiedApa, setCopiedApa] = useState(false);
  const [activeTab, setActiveTab] = useState<'harman' | 'marker' | 'ulmcf' | 'remedies'>('harman');

  const toggleItem = (qid: string) => {
    setSelectedItemIds((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleSelectAll = () => {
    setSelectedItemIds(scaleQuestions.map((q) => q.question_id));
  };

  const handleRunCMB = async () => {
    if (selectedItemIds.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 câu hỏi thang đo để chẩn đoán Common Method Bias.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runCommonMethodBias(surveyId, {
        scale_question_ids: selectedItemIds,
        marker_question_id: markerQuestionId || undefined,
        scope
      });

      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể thực hiện chẩn đoán sai lệch phương pháp chung.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi kết nối máy chủ để thực hiện chẩn đoán CMB.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2000);
  };

  const getRiskBadge = (risk?: string) => {
    switch (risk) {
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5" />
            Rủi ro Thấp (Low CMB Risk)
          </span>
        );
      case 'MODERATE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" />
            Rủi ro Trung bình (Moderate Risk)
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5" />
            Rủi ro Cao (High CMB Threat)
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200/60 flex items-center justify-center text-indigo-600 shadow-xs">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-800">
                Chẩn đoán Sai lệch Phương pháp Chung (Common Method Bias - CMB/CMV)
              </h3>
              <span className="px-2 py-0.5 text-[11px] font-semibold bg-indigo-100 text-indigo-700 rounded-md">
                Podsakoff & Lindell
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Kiểm định Harman's Single Factor, Kỹ thuật Biến Đánh Dấu (Marker Variable) và ULMCF theo chuẩn APA 7th
            </p>
          </div>
        </div>

        {result && (
          <div className="flex items-center gap-2 self-start sm:self-auto">
            {getRiskBadge(result.overall_risk)}
          </div>
        )}
      </div>

      {/* Control Panel */}
      <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/60 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Biến đánh dấu */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-indigo-500" />
              Biến Đánh Dấu (Marker Variable - Lindell & Whitney 2001)
            </label>
            <select
              value={markerQuestionId}
              onChange={(e) => setMarkerQuestionId(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white py-2 px-3 shadow-2xs"
            >
              <option value="">-- Tự động tìm correlation dương nhỏ nhất (Proxy Marker) --</option>
              {scaleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-500 mt-1">
              Biến lý thuyết không liên quan tới các biến nội dung chính để ước lượng phương sai sai số phương pháp chung.
            </p>
          </div>

          {/* Scope */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              Phạm vi dữ liệu phản hồi
            </label>
            <div className="flex items-center gap-3 mt-1">
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="cmb_scope"
                  value="all"
                  checked={scope === 'all'}
                  onChange={() => setScope('all')}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                Tất cả phản hồi
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="cmb_scope"
                  value="verified_clean"
                  checked={scope === 'verified_clean'}
                  onChange={() => setScope('verified_clean')}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                Chỉ mẫu sạch (Verified Clean)
              </label>
            </div>
          </div>
        </div>

        {/* Danh sách câu hỏi chỉ báo */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              Chọn các câu hỏi thang đo đưa vào kiểm định ({selectedItemIds.length}/{scaleQuestions.length} câu)
            </span>
            <button
              type="button"
              onClick={handleSelectAll}
              className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800 underline"
            >
              Chọn tất cả
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-36 overflow-y-auto p-2 bg-white rounded-lg border border-slate-200/80">
            {scaleQuestions.map((q) => {
              const isChecked = selectedItemIds.includes(q.question_id);
              const isMarker = markerQuestionId === q.question_id;
              return (
                <label
                  key={q.question_id}
                  className={`flex items-start gap-2 p-2 rounded-md text-xs cursor-pointer border transition-colors ${
                    isChecked
                      ? 'bg-indigo-50/60 border-indigo-200 text-slate-800'
                      : 'bg-white border-slate-100 text-slate-600 hover:bg-slate-50'
                  } ${isMarker ? 'ring-1 ring-amber-400' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleItem(q.question_id)}
                    className="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <div className="truncate">
                    <span className="font-medium truncate block">{q.question_title}</span>
                    <span className="text-[10px] text-slate-400">
                      Loại: {q.question_type} {isMarker ? '(Marker)' : ''}
                    </span>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-2">
          <button
            onClick={handleRunCMB}
            disabled={loading || selectedItemIds.length < 2}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-all shadow-xs"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            Chẩn đoán Toàn diện Common Method Bias
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
      {result && (
        <div className="space-y-6 pt-2">
          {/* Executive Summary Card */}
          <div className={`p-4 rounded-xl border ${
            result.overall_risk === 'LOW'
              ? 'bg-emerald-50/40 border-emerald-200 text-emerald-900'
              : result.overall_risk === 'MODERATE'
              ? 'bg-amber-50/40 border-amber-200 text-amber-900'
              : 'bg-rose-50/40 border-rose-200 text-rose-900'
          }`}>
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                {result.overall_risk === 'LOW' ? (
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                )}
              </div>
              <div className="flex-1">
                <h4 className="text-xs font-bold uppercase tracking-wider">
                  Đánh giá Tổng thể: {result.risk_summary}
                </h4>
                {result.flagged_issues && result.flagged_issues.length > 0 && (
                  <ul className="mt-2 text-xs space-y-1 list-disc list-inside opacity-90">
                    {result.flagged_issues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-200">
            <button
              onClick={() => setActiveTab('harman')}
              className={`py-2 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'harman'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Percent className="w-3.5 h-3.5" />
              1. Harman's Single-Factor ({result.harman_test?.first_factor_variance_pct ?? 0}%)
            </button>
            <button
              onClick={() => setActiveTab('marker')}
              className={`py-2 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'marker'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              2. Kỹ thuật Biến Đánh Dấu (r_M = {result.marker_test?.marker_correlation_r_m ?? 0})
            </button>
            <button
              onClick={() => setActiveTab('ulmcf')}
              className={`py-2 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'ulmcf'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              3. Mô hình ULMCF ({result.ulmcf_test?.estimated_cmv_variance_pct ?? 0}%)
            </button>
            <button
              onClick={() => setActiveTab('remedies')}
              className={`py-2 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'remedies'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              4. Khuyến nghị & APA 7th
            </button>
          </div>

          {/* Tab 1: Harman's Single Factor */}
          {activeTab === 'harman' && result.harman_test && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">Phương sai Nhân tố 1</div>
                  <div className={`text-2xl font-bold mt-1 ${
                    result.harman_test.has_cmv_risk ? 'text-rose-600' : 'text-emerald-600'
                  }`}>
                    {result.harman_test.first_factor_variance_pct}%
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Ngưỡng tối đa cho phép: &lt; 50.0%</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">Trị riêng (Eigenvalue) Factor 1</div>
                  <div className="text-2xl font-bold text-slate-800 mt-1">
                    {result.harman_test.first_factor_eigenvalue}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Số nhân tố có Eigenvalue &ge; 1.0: {result.harman_test.factors_with_eigenvalue_gt_one}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">Kết luận Harman (1976)</div>
                  <div className={`text-sm font-bold mt-2 ${
                    result.harman_test.passed ? 'text-emerald-700' : 'text-rose-700'
                  }`}>
                    {result.harman_test.passed ? 'ĐẠT TIÊU CHUẨN' : 'VI PHẠM (CMB CAO)'}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Cỡ mẫu: N = {result.harman_test.n_sample}</div>
                </div>
              </div>

              {/* Bảng phân rã phương sai */}
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Nhân tố (Factor)</th>
                      <th className="py-2.5 px-3">Trị riêng (Eigenvalue)</th>
                      <th className="py-2.5 px-3">% Phương sai trích</th>
                      <th className="py-2.5 px-3">% Tích lũy (Cumulative %)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {result.harman_test.variance_breakdown.map((row) => (
                      <tr key={row.factor} className={row.factor === 1 ? 'bg-indigo-50/40 font-medium' : ''}>
                        <td className="py-2 px-3">Nhân tố {row.factor}</td>
                        <td className="py-2 px-3 font-mono">{row.eigenvalue}</td>
                        <td className="py-2 px-3 font-mono">{row.variance_pct}%</td>
                        <td className="py-2 px-3 font-mono">{row.cumulative_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200/60 leading-relaxed">
                {result.harman_test.interpretation}
              </p>
            </div>
          )}

          {/* Tab 2: Marker Variable Technique */}
          {activeTab === 'marker' && result.marker_test && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">Hệ số tương quan Marker (r_M)</div>
                  <div className="text-2xl font-bold text-indigo-600 mt-1">
                    {result.marker_test.marker_correlation_r_m}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {result.marker_test.is_auto_marker ? 'Tự động ước lượng (Min r+)' : 'Từ biến đánh dấu chọn lọc'}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">Tỷ lệ duy trì ý nghĩa thống kê</div>
                  <div className="text-2xl font-bold text-slate-800 mt-1">
                    {result.marker_test.significance_retention_rate_pct}%
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {result.marker_test.significant_pairs_after}/{result.marker_test.significant_pairs_before} cặp giữ vững p &lt; .05
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">Độ tin cậy mối quan hệ</div>
                  <div className="text-sm font-bold text-emerald-700 mt-2">
                    {result.marker_test.significance_retention_rate_pct >= 80 ? 'VỮNG CHẮC (ROBUST)' : 'BỊ ẢNH HƯỞNG'}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Tổng số cặp kiểm định: {result.marker_test.total_pairs_tested}
                  </div>
                </div>
              </div>

              {/* Bảng so sánh tương quan trước vs sau hiệu chỉnh */}
              <div className="overflow-x-auto rounded-xl border border-slate-200 max-h-72">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">Cặp biến quan sát</th>
                      <th className="py-2.5 px-3">r ban đầu</th>
                      <th className="py-2.5 px-3">p ban đầu</th>
                      <th className="py-2.5 px-3">r hiệu chỉnh (r_adj)</th>
                      <th className="py-2.5 px-3">p hiệu chỉnh</th>
                      <th className="py-2.5 px-3">Duy trì ý nghĩa</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {result.marker_test.pair_comparisons.map((pair, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/60">
                        <td className="py-2 px-3 font-medium">
                          {pair.variable_x} &harr; {pair.variable_y}
                        </td>
                        <td className="py-2 px-3 font-mono">{pair.r_original}</td>
                        <td className="py-2 px-3 font-mono">{pair.p_original}</td>
                        <td className="py-2 px-3 font-mono font-semibold text-indigo-600">{pair.r_adjusted}</td>
                        <td className="py-2 px-3 font-mono">{pair.p_adjusted}</td>
                        <td className="py-2 px-3">
                          {pair.significance_retained ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700">
                              <Check className="w-3 h-3" /> Giữ nguyên
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-700">
                              Mất ý nghĩa
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200/60 leading-relaxed">
                {result.marker_test.interpretation}
              </p>
            </div>
          )}

          {/* Tab 3: ULMCF Model */}
          {activeTab === 'ulmcf' && result.ulmcf_test && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">Ước tính Phương sai Phương pháp (ULMCF)</div>
                  <div className={`text-2xl font-bold mt-1 ${
                    result.ulmcf_test.is_acceptable ? 'text-emerald-600' : 'text-rose-600'
                  }`}>
                    {result.ulmcf_test.estimated_cmv_variance_pct}%
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Chuẩn đối sánh Williams et al. (1989): &le; {result.ulmcf_test.benchmark_threshold_pct}%
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-medium text-slate-500">R^2 Trung bình Nhân tố Phương pháp</div>
                  <div className="text-2xl font-bold text-slate-800 mt-1">
                    {result.ulmcf_test.average_method_r2}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Độ biến thiên giải thích bởi nhân tố phương pháp chung ẩn
                  </div>
                </div>
              </div>

              {/* Bảng loadings của method factor */}
              <div>
                <h5 className="text-xs font-semibold text-slate-700 mb-2">
                  Tải lượng nhân tố phương pháp chung (Method Loadings) theo từng câu hỏi
                </h5>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                  {Object.entries(result.ulmcf_test.method_loadings).map(([varName, loading]) => (
                    <div key={varName} className="p-2.5 rounded-lg border border-slate-200 bg-white">
                      <div className="text-[11px] text-slate-500 truncate font-medium">{varName}</div>
                      <div className="text-sm font-bold text-slate-800 font-mono mt-0.5">&lambda; = {loading}</div>
                    </div>
                  ))}
                </div>
              </div>

              <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200/60 leading-relaxed">
                {result.ulmcf_test.interpretation}
              </p>
            </div>
          )}

          {/* Tab 4: Remedies & APA 7th */}
          {activeTab === 'remedies' && (
            <div className="space-y-4">
              {/* APA 7th Writeup */}
              {result.apa_writeup && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                      Đoạn Trích Minh Bạch APA 7th cho Báo cáo / Luận văn
                    </span>
                    <button
                      onClick={() => copyToClipboard(result.apa_writeup!)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-md shadow-2xs hover:bg-slate-50"
                    >
                      {copiedApa ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                      {copiedApa ? 'Đã sao chép' : 'Sao chép APA'}
                    </button>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed italic border-l-2 border-indigo-400 pl-3 bg-white/60 p-2.5 rounded">
                    "{result.apa_writeup}"
                  </p>
                </div>
              )}

              {/* Khuyến nghị khắc phục */}
              {result.recommended_remedies && result.recommended_remedies.length > 0 && (
                <div className="space-y-2">
                  <h5 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    Khuyến nghị Kiểm soát & Khắc phục Sai lệch Phương pháp (Podsakoff et al. 2003)
                  </h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.recommended_remedies.map((rem, idx) => (
                      <div key={idx} className="p-3 rounded-xl border border-slate-200 bg-white shadow-2xs">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                            rem.type === 'PROCEDURAL'
                              ? 'bg-blue-100 text-blue-700'
                              : rem.type === 'STATISTICAL'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}>
                            {rem.type === 'PROCEDURAL' ? 'Biện pháp Thủ tục' : rem.type === 'STATISTICAL' ? 'Biện pháp Thống kê' : 'Báo cáo'}
                          </span>
                          <span className="text-xs font-semibold text-slate-800">{rem.title}</span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">{rem.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
