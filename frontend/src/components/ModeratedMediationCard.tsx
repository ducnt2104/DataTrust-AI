import React, { useState, useEffect } from 'react';
import {
  GitMerge, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  TrendingUp, Activity, Copy, Check, RefreshCw, BarChart2,
  BookOpen, Layers, ShieldCheck, Zap, Sliders, Filter
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, ModeratedMediationResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const ModeratedMediationCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc các câu hỏi định lượng thang đo
  const eligibleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  const [xId, setXId] = useState<string>('');
  const [mId, setMId] = useState<string>('');
  const [wId, setWId] = useState<string>('');
  const [yId, setYId] = useState<string>('');
  const [centerVars, setCenterVars] = useState<boolean>(true);
  const [bootSamples, setBootSamples] = useState<number>(500);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [result, setResult] = useState<ModeratedMediationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);

  // Khởi tạo mặc định 4 biến nếu có đủ câu hỏi
  useEffect(() => {
    if (eligibleQuestions.length >= 4) {
      if (!xId || !eligibleQuestions.some(q => q.question_id === xId)) {
        setXId(eligibleQuestions[0].question_id);
      }
      if (!mId || !eligibleQuestions.some(q => q.question_id === mId) || mId === eligibleQuestions[0].question_id) {
        setMId(eligibleQuestions[1].question_id);
      }
      if (!wId || !eligibleQuestions.some(q => q.question_id === wId) || wId === eligibleQuestions[0].question_id || wId === eligibleQuestions[1].question_id) {
        setWId(eligibleQuestions[2].question_id);
      }
      if (!yId || !eligibleQuestions.some(q => q.question_id === yId) || yId === eligibleQuestions[0].question_id || yId === eligibleQuestions[1].question_id || yId === eligibleQuestions[2].question_id) {
        setYId(eligibleQuestions[3].question_id);
      }
    }
  }, [questions]);

  const handleRunAnalysis = async () => {
    if (!xId || !mId || !wId || !yId) {
      setError('Vui lòng chọn đầy đủ 4 biến: Độc lập (X), Trung gian (M), Điều tiết (W) và Phụ thuộc (Y).');
      return;
    }
    if (new Set([xId, mId, wId, yId]).size < 4) {
      setError('Bốn biến X, M, W và Y phải là 4 câu hỏi hoàn toàn phân biệt.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runModeratedMediation(surveyId, {
        independent_question_id: xId,
        mediator_question_id: mId,
        moderator_question_id: wId,
        dependent_question_id: yId,
        center_variables: centerVars,
        num_bootstrap: bootSamples,
        scope
      });

      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể tính toán mô hình trung gian bị điều tiết.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi gọi API phân tích trung gian bị điều tiết.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2000);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm mb-8 transition-colors">
      {/* Tiêu đề & Giới thiệu phương pháp luận */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-6 border-b border-slate-100 dark:border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 rounded-xl text-emerald-600 dark:text-emerald-400 shadow-sm">
              <GitMerge className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Kiểm Định Tác Động Trung Gian Bị Điều Tiết (Moderated Mediation)
                <span className="text-xs px-2.5 py-0.5 font-medium rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  PROCESS Model 7 (Hayes 2018)
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Đánh giá tác động gián tiếp của X lên Y thông qua biến trung gian M khi mối quan hệ X → M bị điều tiết bởi biến W (Bootstrap phi tham số 95% CI).
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            Index of Moderated Mediation (&omega; = a₃ &middot; b)
          </span>
        </div>
      </div>

      {/* Cấu hình Chọn Biến Nghiên Cứu */}
      <div className="mt-6 bg-slate-50 dark:bg-slate-950/50 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              Biến Độc Lập (X)
            </label>
            <select
              value={xId}
              onChange={(e) => setXId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Chọn biến X --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              Biến Trung Gian (M)
            </label>
            <select
              value={mId}
              onChange={(e) => setMId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Chọn biến M --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              Biến Điều Tiết (W)
            </label>
            <select
              value={wId}
              onChange={(e) => setWId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Chọn biến W --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Biến Phụ Thuộc (Y)
            </label>
            <select
              value={yId}
              onChange={(e) => setYId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Chọn biến Y --</option>
              {eligibleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Bộ tùy chọn kỹ thuật OLS & Bootstrap */}
        <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-5">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-600 dark:text-slate-300 select-none">
              <input
                type="checkbox"
                checked={centerVars}
                onChange={(e) => setCenterVars(e.target.checked)}
                className="rounded border-slate-300 dark:border-slate-700 text-emerald-600 focus:ring-emerald-500"
              />
              <span className="font-medium">Chuẩn hóa trung bình (Mean-Centering X & W)</span>
              <span className="text-[10px] text-slate-400">(Tránh đa cộng tuyến VIF)</span>
            </label>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 dark:text-slate-400">Tái lấy mẫu:</span>
              <select
                value={bootSamples}
                onChange={(e) => setBootSamples(Number(e.target.value))}
                className="text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-slate-700 dark:text-slate-300"
              >
                <option value={200}>200 mẫu (Nhanh)</option>
                <option value={500}>500 mẫu (Khuyến nghị)</option>
                <option value={1000}>1,000 mẫu (Xuất bản chuẩn)</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 dark:text-slate-400">Phạm vi:</span>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-slate-700 dark:text-slate-300"
              >
                <option value="all">Tất cả phản hồi hợp lệ</option>
                <option value="verified_clean">Chỉ mẫu đã xác thực sạch (Clean)</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading || eligibleQuestions.length < 4}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-2 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Đang chạy Bootstrap...
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5" />
                Chạy Kiểm Định PROCESS Model 7
              </>
            )}
          </button>
        </div>
      </div>

      {/* Thông báo lỗi nếu có */}
      {error && (
        <div className="mt-4 p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 rounded-xl flex items-center gap-2 text-rose-700 dark:text-rose-300 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Kết Quả Phân Tích */}
      {result && result.status === 'SUCCESS' && (
        <div className="mt-6 space-y-6">
          {/* Banner Tóm Tắt Chỉ Số Trung Gian Bị Điều Tiết (Index of Moderated Mediation) */}
          {result.index_of_moderated_mediation && (
            <div className={`p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
              result.index_of_moderated_mediation.is_significant
                ? 'bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800/60'
                : 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800'
            }`}>
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${
                  result.index_of_moderated_mediation.is_significant
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-400 text-white'
                }`}>
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                      Chỉ Số Trung Gian Bị Điều Tiết (Index of Moderated Mediation):
                    </span>
                    <span className={`text-xs px-2.5 py-0.5 font-bold rounded-full ${
                      result.index_of_moderated_mediation.is_significant
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200'
                        : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                    }`}>
                      {result.index_of_moderated_mediation.verdict_badge}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-xs text-slate-600 dark:text-slate-400">
                    <span>
                      &omega; = <strong className="text-slate-900 dark:text-white">{result.index_of_moderated_mediation.index_omega.toFixed(4)}</strong>
                    </span>
                    <span>
                      BootSE = <strong>{result.index_of_moderated_mediation.bootstrap_se.toFixed(4)}</strong>
                    </span>
                    <span>
                      95% BootCI: <strong className="text-slate-900 dark:text-white">[{result.index_of_moderated_mediation.boot_ci_95_lower.toFixed(4)}, {result.index_of_moderated_mediation.boot_ci_95_upper.toFixed(4)}]</strong>
                    </span>
                    <span className="text-slate-400">
                      (N = {result.sample_size}, {result.bootstrap_samples_executed} mẫu Bootstrap)
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Quy chuẩn kiểm định</span>
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {result.index_of_moderated_mediation.is_significant
                    ? 'CI 95% không chứa 0 → Tác động ý nghĩa'
                    : 'CI 95% chứa 0 → Không có điều tiết'}
                </span>
              </div>
            </div>
          )}

          {/* Sơ đồ Đường dẫn Khái niệm & Thống kê (Conceptual & Statistical Diagram) */}
          <div className="bg-slate-50/60 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-600" />
              Sơ Đồ Đường Dẫn Thống Kê (Statistical Path Diagram)
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center text-center">
              {/* Box X */}
              <div className="p-3 bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/60 rounded-xl">
                <span className="text-[10px] font-bold text-blue-600 uppercase">Biến Độc Lập</span>
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-1 line-clamp-2">
                  {result.variables?.independent_x.title}
                </p>
                <span className="text-[10px] text-slate-400 mt-1 block">
                  M = {result.variables?.independent_x.mean.toFixed(2)} (SD = {result.variables?.independent_x.std.toFixed(2)})
                </span>
              </div>

              {/* Đường dẫn X*W -> M */}
              <div className="p-3 bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-900/60 rounded-xl">
                <span className="text-[10px] font-bold text-purple-600 uppercase">Biến Điều Tiết (W)</span>
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-1 line-clamp-2">
                  {result.variables?.moderator_w.title}
                </p>
                <div className="mt-2 pt-2 border-t border-purple-200/60 dark:border-purple-900/40 text-[10px] text-purple-700 dark:text-purple-300">
                  Tương tác a₃ (X&middot;W): <strong>{result.stage1_mediator_model?.coefficients.interaction_a3_XW.toFixed(4)}</strong>
                </div>
              </div>

              {/* Box M */}
              <div className="p-3 bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 rounded-xl">
                <span className="text-[10px] font-bold text-amber-600 uppercase">Biến Trung Gian</span>
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-1 line-clamp-2">
                  {result.variables?.mediator_m.title}
                </p>
                <div className="mt-2 pt-2 border-t border-amber-200/60 dark:border-amber-900/40 text-[10px] text-amber-700 dark:text-amber-300">
                  Hệ số b (M &rarr; Y): <strong>{result.stage2_dependent_model?.coefficients.mediator_path_b.toFixed(4)}</strong>
                </div>
              </div>

              {/* Box Y */}
              <div className="p-3 bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/60 rounded-xl">
                <span className="text-[10px] font-bold text-emerald-600 uppercase">Biến Phụ Thuộc</span>
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-1 line-clamp-2">
                  {result.variables?.dependent_y.title}
                </p>
                <div className="mt-2 pt-2 border-t border-emerald-200/60 dark:border-emerald-900/40 text-[10px] text-emerald-700 dark:text-emerald-300">
                  Trực tiếp c' (X &rarr; Y): <strong>{result.stage2_dependent_model?.coefficients.direct_path_c_prime.toFixed(4)}</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Bảng Tác Động Gián Tiếp Có Điều Kiện (Conditional Indirect Effects) */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
              Tác Động Gián Tiếp Có Điều Kiện Tại Các Mức Của Biến Điều Tiết W (Pick-A-Point: Mean &plusmn; 1SD)
            </h4>
            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
              <table className="w-full text-xs text-left text-slate-700 dark:text-slate-300">
                <thead className="bg-slate-100 dark:bg-slate-800/70 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3.5 py-2.5">Mức Độ W</th>
                    <th className="px-3 py-2.5">Giá Trị W (Gốc)</th>
                    <th className="px-3 py-2.5">Đường dẫn a (X&rarr;M)</th>
                    <th className="px-3 py-2.5">Đường dẫn b (M&rarr;Y)</th>
                    <th className="px-3.5 py-2.5 font-bold text-emerald-700 dark:text-emerald-300">Tác động Gián tiếp (a&middot;b)</th>
                    <th className="px-3 py-2.5">BootSE</th>
                    <th className="px-3.5 py-2.5">95% BootCI [Lower, Upper]</th>
                    <th className="px-3.5 py-2.5 text-center">Ý Nghĩa Thống Kê</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                  {result.conditional_indirect_effects?.map((cond, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-3.5 py-2.5 font-semibold text-slate-900 dark:text-white">
                        {cond.label}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-slate-600 dark:text-slate-400">
                        {cond.w_value.toFixed(2)}
                      </td>
                      <td className="px-3 py-2.5 font-mono">
                        {cond.conditional_a.toFixed(4)}
                      </td>
                      <td className="px-3 py-2.5 font-mono">
                        {cond.b_path.toFixed(4)}
                      </td>
                      <td className="px-3.5 py-2.5 font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        {cond.indirect_effect.toFixed(4)}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-slate-500">
                        {cond.bootstrap_se.toFixed(4)}
                      </td>
                      <td className="px-3.5 py-2.5 font-mono text-slate-700 dark:text-slate-300">
                        [{cond.boot_ci_95_lower.toFixed(4)}, {cond.boot_ci_95_upper.toFixed(4)}]
                      </td>
                      <td className="px-3.5 py-2.5 text-center">
                        {cond.is_significant ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                            Có ý nghĩa (p &lt; .05)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
                            Không ý nghĩa
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Tóm tắt Hai Mô Hình Hồi Quy Stage 1 và Stage 2 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Giai đoạn 1 */}
            <div className="p-4 bg-slate-50/50 dark:bg-slate-900/30 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Giai Đoạn 1: Mô Hình Biến Trung Gian M
              </span>
              <p className="text-xs font-mono text-slate-800 dark:text-slate-200 mt-1">
                {result.stage1_mediator_model?.formula}
              </p>
              <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">R²</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">
                    {result.stage1_mediator_model?.r_squared.toFixed(4)}
                  </span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">F-stat</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">
                    {result.stage1_mediator_model?.f_stat.toFixed(2)}
                  </span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">p-value</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">
                    {result.stage1_mediator_model?.p_value.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>

            {/* Giai đoạn 2 */}
            <div className="p-4 bg-slate-50/50 dark:bg-slate-900/30 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Giai Đoạn 2: Mô Hình Biến Phụ Thuộc Y
              </span>
              <p className="text-xs font-mono text-slate-800 dark:text-slate-200 mt-1">
                {result.stage2_dependent_model?.formula}
              </p>
              <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">R²</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">
                    {result.stage2_dependent_model?.r_squared.toFixed(4)}
                  </span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">F-stat</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">
                    {result.stage2_dependent_model?.f_stat.toFixed(2)}
                  </span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">p-value</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">
                    {result.stage2_dependent_model?.p_value.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Trích Dẫn Chuẩn Học Thuật APA 7th Edition */}
          {result.apa_narrative && (
            <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                  <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
                  Đoạn Trích Chuẩn Học Thuật APA 7th Edition (Publication-Ready)
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md shadow-2xs flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  {copiedApa ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      Đã chép!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép đoạn trích
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed italic bg-white dark:bg-slate-900 p-3.5 rounded-lg border border-slate-200/60 dark:border-slate-800">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
