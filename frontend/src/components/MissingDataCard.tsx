import React, { useState, useEffect } from 'react';
import {
  Layers, HelpCircle, CheckCircle2, AlertTriangle, ArrowRight,
  Sparkles, RefreshCw, Copy, Check, Filter, BarChart2,
  Table, Info, ShieldCheck, Zap
} from 'lucide-react';
import { api } from '../api/client';
import {
  QuestionStats,
  MissingDataDiagnosticsResult,
  MissingDataImputationResult
} from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const MissingDataCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [activeTab, setActiveTab] = useState<'diagnostics' | 'imputation'>('diagnostics');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([]);

  // Lọc danh sách câu hỏi định lượng / thang đo
  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  useEffect(() => {
    // Mặc định chọn tất cả câu hỏi định lượng
    if (eligibleQuestions.length > 0 && selectedQuestionIds.length === 0) {
      setSelectedQuestionIds(eligibleQuestions.map((q) => q.question_id));
    }
  }, [questions]);

  // Diagnostics State
  const [diagLoading, setDiagLoading] = useState(false);
  const [diagError, setDiagError] = useState<string | null>(null);
  const [diagResult, setDiagResult] = useState<MissingDataDiagnosticsResult | null>(null);
  const [copiedMcar, setCopiedMcar] = useState(false);

  // Imputation State
  const [imputeMethod, setImputeMethod] = useState<'em' | 'pmm' | 'hot_deck' | 'mean' | 'median'>('em');
  const [imputeLoading, setImputeLoading] = useState(false);
  const [imputeError, setImputeError] = useState<string | null>(null);
  const [imputeResult, setImputeResult] = useState<MissingDataImputationResult | null>(null);
  const [copiedApa, setCopiedApa] = useState(false);

  const toggleQuestion = (qid: string) => {
    setSelectedQuestionIds((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleSelectAll = () => {
    setSelectedQuestionIds(eligibleQuestions.map((q) => q.question_id));
  };

  const handleRunDiagnostics = async () => {
    if (selectedQuestionIds.length < 2) {
      setDiagError('Vui lòng chọn tối thiểu 2 biến số định lượng để phân tích mô thức khuyết thiếu.');
      return;
    }
    setDiagLoading(true);
    setDiagError(null);
    try {
      const res = await api.getMissingDataDiagnostics(surveyId, {
        question_ids: selectedQuestionIds,
        scope
      });
      if (res.status === 'ERROR' || res.status === 'INSUFFICIENT_VARIABLES' || res.status === 'INSUFFICIENT_SAMPLE') {
        setDiagError(res.message || 'Không thể thực hiện kiểm định mô thức khuyết thiếu.');
      } else {
        setDiagResult(res);
      }
    } catch (err: any) {
      setDiagError(err.message || 'Lỗi khi kết nối máy chủ để phân tích dữ liệu.');
    } finally {
      setDiagLoading(false);
    }
  };

  const handleRunImputation = async () => {
    if (selectedQuestionIds.length < 2) {
      setImputeError('Vui lòng chọn tối thiểu 2 biến số để thực hiện bù khuyết.');
      return;
    }
    setImputeLoading(true);
    setImputeError(null);
    try {
      const res = await api.runMissingDataImputation(surveyId, {
        question_ids: selectedQuestionIds,
        method: imputeMethod,
        scope
      });
      if (res.status === 'ERROR' || res.status === 'INSUFFICIENT_VARIABLES' || res.status === 'INSUFFICIENT_SAMPLE') {
        setImputeError(res.message || 'Không thể thực hiện thuật toán bù khuyết.');
      } else {
        setImputeResult(res);
      }
    } catch (err: any) {
      setImputeError(err.message || 'Lỗi khi thực thi thuật toán bù khuyết dữ liệu.');
    } finally {
      setImputeLoading(false);
    }
  };

  const copyToClipboard = (text: string, type: 'mcar' | 'apa') => {
    navigator.clipboard.writeText(text);
    if (type === 'mcar') {
      setCopiedMcar(true);
      setTimeout(() => setCopiedMcar(false), 2000);
    } else {
      setCopiedApa(true);
      setTimeout(() => setCopiedApa(false), 2000);
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200/60 flex items-center justify-center text-teal-600 shadow-xs">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Kiểm Định Mô Thức Khuyết Thiếu & Bù Khuyết Đa Phương Pháp
              </h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                Little's MCAR (1988)
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Phát hiện cấu trúc non-response, kiểm định giả định ngẫu nhiên MCAR/MAR/MNAR và bù khuyết EM / PMM / Hot-Deck
            </p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100/80 rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('diagnostics')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'diagnostics'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Mô Thức & Kiểm Định MCAR
          </button>
          <button
            onClick={() => setActiveTab('imputation')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'imputation'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Động Cơ Bù Khuyết (Imputation)
          </button>
        </div>
      </div>

      {/* Shared Configuration: Variable Selection & Scope */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-teal-600" />
            Chọn các biến tham gia phân tích ({selectedQuestionIds.length}/{eligibleQuestions.length})
          </span>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              className="text-xs text-teal-700 hover:underline font-medium"
            >
              Chọn tất cả
            </button>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Phạm vi:</span>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500"
              >
                <option value="all">Toàn bộ phản hồi (All)</option>
                <option value="verified_clean">Đã làm sạch & Xác thực (Clean)</option>
              </select>
            </div>
          </div>
        </div>

        {eligibleQuestions.length === 0 ? (
          <p className="text-xs text-amber-700 italic">
            Chưa tìm thấy câu hỏi dạng thang đo hoặc số liệu định lượng trong khảo sát này.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1 max-h-48 overflow-y-auto">
            {eligibleQuestions.map((q) => {
              const checked = selectedQuestionIds.includes(q.question_id);
              return (
                <label
                  key={q.question_id}
                  className={`flex items-start gap-2 p-2 rounded-lg border text-xs cursor-pointer transition-all ${
                    checked
                      ? 'bg-teal-50/50 border-teal-300 text-teal-950 font-medium'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleQuestion(q.question_id)}
                    className="mt-0.5 rounded text-teal-600 focus:ring-teal-500"
                  />
                  <span className="line-clamp-2 leading-tight">
                    {q.question_title}
                  </span>
                </label>
              );
            })}
          </div>
        )}
      </div>

      {/* TAB 1: DIAGNOSTICS & LITTLE'S MCAR TEST */}
      {activeTab === 'diagnostics' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-600">
              Kiểm tra xem dữ liệu bị khuyết có mang tính ngẫu nhiên hoàn toàn (MCAR) hay phụ thuộc vào các biến số khác (MAR/MNAR).
            </p>
            <button
              onClick={handleRunDiagnostics}
              disabled={diagLoading || selectedQuestionIds.length < 2}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50 transition-all shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${diagLoading ? 'animate-spin' : ''}`} />
              <span>{diagLoading ? 'Đang phân tích...' : 'Khảo sát mô thức & Chạy MCAR'}</span>
            </button>
          </div>

          {diagError && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{diagError}</span>
            </div>
          )}

          {diagResult && diagResult.status === 'OK' && (
            <div className="space-y-6">
              {/* Summary Stats Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">Tỷ lệ ô khuyết toàn bài</span>
                  <div className="text-2xl font-black text-slate-900 mt-1">
                    {diagResult.overall_missing_rate}%
                  </div>
                  <span className="text-[11px] text-slate-500">
                    {diagResult.total_missing_cells} / {diagResult.total_cells} ô dữ liệu
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">Phản hồi hoàn chỉnh 100%</span>
                  <div className="text-2xl font-black text-emerald-600 mt-1">
                    {diagResult.complete_cases_pct}%
                  </div>
                  <span className="text-[11px] text-slate-500">
                    {diagResult.complete_cases_count} / {diagResult.sample_size} người trả lời
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">Phản hồi có ô khuyết</span>
                  <div className="text-2xl font-black text-amber-600 mt-1">
                    {diagResult.incomplete_cases_count}
                  </div>
                  <span className="text-[11px] text-slate-500">
                    Cần xem xét cơ chế xử lý
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">Số tổ hợp mô thức</span>
                  <div className="text-2xl font-black text-teal-600 mt-1">
                    {diagResult.patterns_count}
                  </div>
                  <span className="text-[11px] text-slate-500">
                    Mô thức non-response
                  </span>
                </div>
              </div>

              {/* Little's MCAR Test Card */}
              {diagResult.littles_mcar_test && (
                <div className={`p-5 rounded-2xl border ${
                  diagResult.littles_mcar_test.applicable
                    ? diagResult.littles_mcar_test.is_mcar
                      ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                      : 'bg-amber-50/60 border-amber-200 text-amber-950'
                    : 'bg-slate-50 border-slate-200 text-slate-700'
                } space-y-3`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-teal-600" />
                      <h4 className="font-bold text-sm">
                        Kết quả Kiểm định Little's MCAR Test (1988)
                      </h4>
                    </div>
                    {diagResult.littles_mcar_test.applicable && (
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                        diagResult.littles_mcar_test.is_mcar
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                          : 'bg-amber-100 text-amber-900 border-amber-300'
                      }`}>
                        {diagResult.littles_mcar_test.is_mcar ? '✅ MCAR Thỏa Mãn' : '⚠️ Non-MCAR (MAR/MNAR)'}
                      </span>
                    )}
                  </div>

                  {diagResult.littles_mcar_test.applicable ? (
                    <>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                        <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200/60 text-xs">
                          <span className="text-slate-500 block">Thống kê Chi-Square (χ²)</span>
                          <span className="font-bold text-slate-900 text-sm font-mono">
                            {diagResult.littles_mcar_test.chi_square}
                          </span>
                        </div>
                        <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200/60 text-xs">
                          <span className="text-slate-500 block">Bậc tự do (df)</span>
                          <span className="font-bold text-slate-900 text-sm font-mono">
                            {diagResult.littles_mcar_test.df}
                          </span>
                        </div>
                        <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200/60 text-xs">
                          <span className="text-slate-500 block">Mức ý nghĩa (p-value)</span>
                          <span className="font-bold text-slate-900 text-sm font-mono">
                            {diagResult.littles_mcar_test.p_value}
                          </span>
                        </div>
                      </div>

                      <p className="text-xs leading-relaxed text-slate-800">
                        {diagResult.littles_mcar_test.conclusion}
                      </p>

                      {diagResult.littles_mcar_test.apa_writeup && (
                        <div className="flex items-center justify-between p-2.5 bg-white/90 rounded-xl border border-slate-200 text-xs text-slate-700">
                          <span className="font-mono text-[11px]">{diagResult.littles_mcar_test.apa_writeup}</span>
                          <button
                            onClick={() => copyToClipboard(diagResult.littles_mcar_test!.apa_writeup!, 'mcar')}
                            className="flex items-center gap-1 text-teal-700 hover:text-teal-900 font-semibold text-[11px] shrink-0 ml-2"
                          >
                            {copiedMcar ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                            <span>{copiedMcar ? 'Đã chép' : 'Chép APA'}</span>
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-slate-600">
                      {diagResult.littles_mcar_test.reason || diagResult.littles_mcar_test.conclusion}
                    </p>
                  )}
                </div>
              )}

              {/* Table of Variable Non-Response Rates */}
              {diagResult.variables_summary && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Thống kê tỷ lệ khuyết thiếu theo từng biến số
                  </h4>
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                        <tr>
                          <th className="py-2.5 px-3">Tên biến / Câu hỏi</th>
                          <th className="py-2.5 px-3 text-right">Quan sát</th>
                          <th className="py-2.5 px-3 text-right">Khuyết</th>
                          <th className="py-2.5 px-3 text-right">Tỷ lệ khuyết (%)</th>
                          <th className="py-2.5 px-3 text-right">Trung bình</th>
                          <th className="py-2.5 px-3 text-right">Độ lệch chuẩn</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {diagResult.variables_summary.map((v) => (
                          <tr key={v.variable} className="hover:bg-slate-50/50">
                            <td className="py-2 px-3 font-medium text-slate-900 max-w-xs truncate" title={v.variable}>
                              {v.variable}
                            </td>
                            <td className="py-2 px-3 text-right text-slate-700">{v.observed_count}</td>
                            <td className="py-2 px-3 text-right font-medium text-amber-700">{v.missing_count}</td>
                            <td className="py-2 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded-full font-bold ${
                                v.missing_pct === 0
                                  ? 'bg-emerald-50 text-emerald-700'
                                  : v.missing_pct > 15
                                  ? 'bg-rose-50 text-rose-700'
                                  : 'bg-amber-50 text-amber-700'
                              }`}>
                                {v.missing_pct}%
                              </span>
                            </td>
                            <td className="py-2 px-3 text-right text-slate-700 font-mono">{v.mean ?? 'N/A'}</td>
                            <td className="py-2 px-3 text-right text-slate-700 font-mono">{v.std ?? 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Missing Data Patterns Matrix */}
              {diagResult.patterns && diagResult.patterns.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Các tổ hợp mô thức khuyết thiếu (Distinct Missing Patterns)
                  </h4>
                  <div className="space-y-2">
                    {diagResult.patterns.map((p) => (
                      <div
                        key={p.pattern_id}
                        className={`p-3 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
                          p.is_complete
                            ? 'bg-emerald-50/40 border-emerald-200'
                            : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{p.pattern_id}</span>
                            <span className="font-mono text-[11px] text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                              {p.case_count} ca ({p.percentage}%)
                            </span>
                            {p.is_complete && (
                              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                                Đầy đủ 100%
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            Quan sát: <span className="text-slate-800 font-medium">{p.observed_variables.length}</span> biến | Khuyết: <span className="text-amber-700 font-medium">{p.missing_variables.length}</span> biến
                          </div>
                        </div>

                        {/* Badges for missing variables in this pattern */}
                        <div className="flex flex-wrap items-center gap-1.5 self-start sm:self-auto">
                          {p.missing_variables.length === 0 ? (
                            <span className="text-[11px] text-emerald-600 font-medium">
                              Không có biến bị khuyết
                            </span>
                          ) : (
                            p.missing_variables.map((mv) => (
                              <span
                                key={mv}
                                className="text-[10px] font-semibold px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 truncate max-w-[150px]"
                                title={mv}
                              >
                                ✕ {mv}
                              </span>
                            ))
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: MULTIPLE IMPUTATION ENGINE */}
      {activeTab === 'imputation' && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-200 text-xs text-teal-950 space-y-2">
            <h4 className="font-bold flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-teal-600" />
              Chọn thuật toán bù khuyết dữ liệu (Imputation Algorithm)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
              <label className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                imputeMethod === 'em' ? 'bg-white border-teal-500 shadow-xs' : 'bg-white/60 border-slate-200 hover:bg-white'
              }`}>
                <input
                  type="radio"
                  name="impute_method"
                  value="em"
                  checked={imputeMethod === 'em'}
                  onChange={() => setImputeMethod('em')}
                  className="hidden"
                />
                <span className="font-bold text-teal-900 block">✨ EM (Kỳ vọng cực đại)</span>
                <span className="text-[11px] text-slate-500 mt-0.5 block leading-tight">
                  Tối ưu hóa hợp lý cực đại, khuyến nghị cho dữ liệu MAR.
                </span>
              </label>

              <label className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                imputeMethod === 'pmm' ? 'bg-white border-teal-500 shadow-xs' : 'bg-white/60 border-slate-200 hover:bg-white'
              }`}>
                <input
                  type="radio"
                  name="impute_method"
                  value="pmm"
                  checked={imputeMethod === 'pmm'}
                  onChange={() => setImputeMethod('pmm')}
                  className="hidden"
                />
                <span className="font-bold text-teal-900 block">🎯 PMM (Ghép giá trị dự báo)</span>
                <span className="text-[11px] text-slate-500 mt-0.5 block leading-tight">
                  Khớp nhà tài trợ gần nhất, bảo toàn giá trị rời rạc 1-5.
                </span>
              </label>

              <label className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                imputeMethod === 'hot_deck' ? 'bg-white border-teal-500 shadow-xs' : 'bg-white/60 border-slate-200 hover:bg-white'
              }`}>
                <input
                  type="radio"
                  name="impute_method"
                  value="hot_deck"
                  checked={imputeMethod === 'hot_deck'}
                  onChange={() => setImputeMethod('hot_deck')}
                  className="hidden"
                />
                <span className="font-bold text-teal-900 block">👥 Hot-Deck (Donor gần nhất)</span>
                <span className="text-[11px] text-slate-500 mt-0.5 block leading-tight">
                  Sao chép từ người trả lời có khoảng cách đặc trưng tối thiểu.
                </span>
              </label>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Quá trình bù khuyết sẽ tự động kiểm soát cận biên thang đo và bảo toàn phương sai.
            </span>
            <button
              onClick={handleRunImputation}
              disabled={imputeLoading || selectedQuestionIds.length < 2}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50 transition-all shadow-xs"
            >
              <Sparkles className={`w-3.5 h-3.5 ${imputeLoading ? 'animate-spin' : ''}`} />
              <span>{imputeLoading ? 'Đang bù khuyết...' : 'Thực hiện bù khuyết dữ liệu'}</span>
            </button>
          </div>

          {imputeError && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{imputeError}</span>
            </div>
          )}

          {imputeResult && imputeResult.status === 'OK' && (
            <div className="space-y-6">
              {/* Imputation Summary Badge */}
              <div className="p-4 rounded-xl bg-teal-50 border border-teal-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div className="space-y-0.5">
                  <span className="font-bold text-teal-900 text-sm">
                    {imputeResult.method_label}
                  </span>
                  <p className="text-teal-800">
                    Đã bù khuyết thành công <strong>{imputeResult.imputed_cells_count}</strong> ô dữ liệu ({imputeResult.imputed_cells_pct}% tổng thể) trên {imputeResult.sample_size} ca.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-white text-teal-800 font-bold rounded-lg border border-teal-200 shadow-2xs">
                    Kiểm toán SHA-256 đã niêm phong
                  </span>
                </div>
              </div>

              {/* Pre vs Post Diagnostics Table */}
              {imputeResult.comparison && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    So sánh chỉ số thống kê trước và sau khi bù khuyết
                  </h4>
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                        <tr>
                          <th className="py-2.5 px-3">Tên biến</th>
                          <th className="py-2.5 px-3 text-right">Ô được bù</th>
                          <th className="py-2.5 px-3 text-right">Mean ban đầu</th>
                          <th className="py-2.5 px-3 text-right">Mean sau bù</th>
                          <th className="py-2.5 px-3 text-right">Độ lệch Mean (%)</th>
                          <th className="py-2.5 px-3 text-right">Std ban đầu</th>
                          <th className="py-2.5 px-3 text-right">Std sau bù</th>
                          <th className="py-2.5 px-3 text-center">Bảo toàn phương sai</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {imputeResult.comparison.map((c) => (
                          <tr key={c.variable} className="hover:bg-slate-50/50">
                            <td className="py-2 px-3 font-medium text-slate-900 max-w-xs truncate" title={c.variable}>
                              {c.variable}
                            </td>
                            <td className="py-2 px-3 text-right font-semibold text-teal-700">{c.missing_cells_imputed}</td>
                            <td className="py-2 px-3 text-right text-slate-700 font-mono">{c.original_mean}</td>
                            <td className="py-2 px-3 text-right text-slate-900 font-bold font-mono">{c.imputed_mean}</td>
                            <td className="py-2 px-3 text-right font-mono">
                              <span className={Math.abs(c.mean_delta_pct) < 5 ? 'text-emerald-600' : 'text-amber-600'}>
                                {c.mean_delta_pct > 0 ? `+${c.mean_delta_pct}%` : `${c.mean_delta_pct}%`}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-right text-slate-700 font-mono">{c.original_std}</td>
                            <td className="py-2 px-3 text-right text-slate-900 font-mono">{c.imputed_std}</td>
                            <td className="py-2 px-3 text-center">
                              <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                                c.preservation_status === 'HIGH'
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : 'bg-amber-50 text-amber-700 border border-amber-200'
                              }`}>
                                {c.preservation_status === 'HIGH' ? 'Bảo toàn cao' : 'Biến thiên vừa'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* APA 7th Narrative with Copy Button */}
              {imputeResult.apa_writeup && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">Đoạn văn học thuật chuẩn APA 7th Edition:</span>
                    <button
                      onClick={() => copyToClipboard(imputeResult.apa_writeup!, 'apa')}
                      className="flex items-center gap-1 text-teal-700 hover:text-teal-900 font-semibold text-xs"
                    >
                      {copiedApa ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedApa ? 'Đã sao chép' : 'Sao chép văn bản'}</span>
                    </button>
                  </div>
                  <p className="p-3 bg-white rounded-lg border border-slate-200/80 italic text-slate-700 leading-relaxed font-serif">
                    "{imputeResult.apa_writeup}"
                  </p>
                </div>
              )}
            </div>
          )}

          {imputeResult && imputeResult.status === 'NO_MISSING_DATA' && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <span>{imputeResult.message}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
