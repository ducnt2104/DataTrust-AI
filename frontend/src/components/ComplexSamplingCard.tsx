import React, { useState, useEffect } from 'react';
import {
  Layers, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  TrendingUp, Activity, Copy, Check, RefreshCw, BarChart2,
  BookOpen, ShieldCheck, Zap, Sliders, Filter, Network, Scale
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, ComplexSamplingResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const ComplexSamplingCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc các câu hỏi định lượng cho Target Y
  const scaleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  // Lọc tất cả câu hỏi phân loại / danh mục cho Cluster PSU và Stratum
  const clusterCandidateQuestions = questions.filter((q) =>
    ['multiple_choice', 'dropdown', 'single_choice', 'text', 'short_text'].includes(q.question_type) ||
    (q.option_distribution && Object.keys(q.option_distribution).length > 1)
  );

  // Lọc câu hỏi số cho Weight
  const weightCandidateQuestions = questions.filter((q) =>
    ['number'].includes(q.question_type)
  );

  const [targetId, setTargetId] = useState<string>('');
  const [clusterId, setClusterId] = useState<string>('');
  const [stratumId, setStratumId] = useState<string>('');
  const [weightId, setWeightId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [result, setResult] = useState<ComplexSamplingResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);

  // Khởi tạo mặc định
  useEffect(() => {
    if (scaleQuestions.length > 0 && (!targetId || !scaleQuestions.some(q => q.question_id === targetId))) {
      setTargetId(scaleQuestions[0].question_id);
    }
    if (clusterCandidateQuestions.length > 0 && (!clusterId || !clusterCandidateQuestions.some(q => q.question_id === clusterId))) {
      // Tìm câu hỏi có vẻ là cụm nhất hoặc câu hỏi thứ 2
      const candidate = clusterCandidateQuestions.find(q => q.question_id !== scaleQuestions[0]?.question_id) || clusterCandidateQuestions[0];
      setClusterId(candidate.question_id);
    }
  }, [questions]);

  const handleRunAnalysis = async () => {
    if (!targetId || !clusterId) {
      setError('Vui lòng chọn Biến mục tiêu Y và Biến đơn vị lấy mẫu cấp 1 (PSU/Cụm).');
      return;
    }
    if (targetId === clusterId) {
      setError('Biến mục tiêu Y và Biến cụm (PSU) không được trùng nhau.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runComplexSamplingAnalysis(surveyId, {
        target_question_id: targetId,
        cluster_question_id: clusterId,
        stratum_question_id: stratumId || undefined,
        weight_question_id: weightId || undefined,
        scope
      });

      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể thực hiện phân tích thiết kế mẫu phức hợp.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi gọi API phân tích thiết kế mẫu phức hợp.');
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
            <div className="p-2.5 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200/60 dark:border-indigo-800/40 rounded-xl text-indigo-600 dark:text-indigo-400 shadow-sm">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Thiết Kế Mẫu Phức Hợp Hai Giai Đoạn & Tuyến Tính Hóa Taylor
                <span className="text-xs px-2.5 py-0.5 font-medium rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  Horvitz-Thompson & Taylor Series Linearization
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Hiệu chỉnh sai số chuẩn và kiểm soát hiệu ứng thiết kế (DEFF, DEFT, ICC) khi mẫu khảo sát được thu thập theo Cụm (PSU), Phân tầng (Stratum) và Trọng số chọn mẫu.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-indigo-500" />
            Cochran (1977) & Kish (1965)
          </span>
        </div>
      </div>

      {/* Cấu hình Chọn Biến Thiết Kế Mẫu */}
      <div className="mt-6 bg-slate-50 dark:bg-slate-950/50 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              Biến Mục Tiêu Y (Thang đo) <span className="text-rose-500">*</span>
            </label>
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">-- Chọn biến mục tiêu Y --</option>
              {scaleQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              Cụm Lấy Mẫu Cấp 1 (PSU) <span className="text-rose-500">*</span>
            </label>
            <select
              value={clusterId}
              onChange={(e) => setClusterId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">-- Chọn biến Cụm/Trường/Xã --</option>
              {questions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              Phân Tầng (Stratum - Tùy chọn)
            </label>
            <select
              value={stratumId}
              onChange={(e) => setStratumId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">-- Không phân tầng (1 tầng chung) --</option>
              {questions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Trọng Số Chọn Mẫu (Tùy chọn)
            </label>
            <select
              value={weightId}
              onChange={(e) => setWeightId(e.target.value)}
              className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">-- Trọng số đều (Equal Weight = 1.0) --</option>
              {weightCandidateQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Cấu hình Phạm vi & Nút Chạy */}
        <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 dark:text-slate-400">Phạm vi kiểm tra:</span>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded px-2.5 py-1 text-slate-700 dark:text-slate-300"
            >
              <option value="all">Tất cả phản hồi hợp lệ</option>
              <option value="verified_clean">Chỉ mẫu đã xác thực sạch (Clean)</option>
            </select>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading || !targetId || !clusterId}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-2 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Đang tính toán ma trận Taylor...
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5" />
                Chạy Ước Lượng Phức Hợp (Horvitz-Thompson & Taylor)
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
          {/* 4 Hero KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Horvitz-Thompson Weighted Mean */}
            <div className="p-4 bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200/80 dark:border-indigo-900/60 rounded-xl">
              <span className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider block">
                Trung Bình Có Trọng Số (Horvitz-Thompson)
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                  {result.horvitz_thompson_estimates?.weighted_mean.toFixed(3)}
                </span>
                <span className={`text-xs font-semibold ${
                  (result.horvitz_thompson_estimates?.weighting_bias_shift ?? 0) >= 0 ? 'text-emerald-600' : 'text-amber-600'
                }`}>
                  &Delta;M: {(result.horvitz_thompson_estimates?.weighting_bias_shift ?? 0) > 0 ? '+' : ''}
                  {result.horvitz_thompson_estimates?.weighting_bias_shift.toFixed(3)}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 block">
                Trung bình gốc chưa cân trọng: {result.horvitz_thompson_estimates?.unweighted_mean.toFixed(3)}
              </span>
            </div>

            {/* Card 2: Taylor Linearization Complex SE */}
            <div className="p-4 bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/80 dark:border-blue-900/60 rounded-xl">
              <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider block">
                Sai Số Chuẩn Phức Hợp (Taylor SE)
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                  &plusmn;{result.taylor_linearization_variance?.complex_se.toFixed(4)}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 block">
                95% CI: [{result.taylor_linearization_variance?.ci_95_lower.toFixed(3)}, {result.taylor_linearization_variance?.ci_95_upper.toFixed(3)}] (df = {result.degrees_of_freedom})
              </span>
            </div>

            {/* Card 3: Design Effect (DEFF / DEFT) */}
            <div className="p-4 bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200/80 dark:border-purple-900/60 rounded-xl">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-purple-600 dark:text-purple-400 uppercase tracking-wider block">
                  Hiệu Ứng Thiết Kế (DEFF)
                </span>
                <span className="text-[10px] px-2 py-0.5 font-bold rounded-full bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300">
                  {result.design_effects?.rating}
                </span>
              </div>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                  {result.design_effects?.deff.toFixed(3)}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  (DEFT = {result.design_effects?.deft.toFixed(3)})
                </span>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 block">
                Tương quan nội cụm ICC: {result.design_effects?.icc.toFixed(4)}
              </span>
            </div>

            {/* Card 4: Effective Sample Size */}
            <div className="p-4 bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200/80 dark:border-emerald-900/60 rounded-xl">
              <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider block">
                Cỡ Mẫu Hiệu Dụng (Effective N)
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                  {result.design_effects?.effective_sample_size.toFixed(1)}
                </span>
                <span className="text-xs text-rose-600 font-semibold">
                  (-{result.design_effects?.efficiency_loss_pct.toFixed(1)}%)
                </span>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 block">
                Mẫu thực tế: N = {result.sample_size} ({result.psu_count} cụm PSU, {result.strata_count} phân tầng)
              </span>
            </div>
          </div>

          {/* Bảng Đối Chiếu Mẫu Phức Hợp vs Ngẫu Nhiên Đơn Giản (SRS) */}
          <div className="bg-slate-50/70 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <BarChart2 className="w-3.5 h-3.5 text-indigo-600" />
              So Sánh Độ Chính Xác: Mẫu Phức Hợp (Taylor Linearization) vs Mẫu Ngẫu Nhiên Đơn Giản (SRS)
            </h4>

            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-lg">
              <table className="w-full text-xs text-left text-slate-700 dark:text-slate-300">
                <thead className="bg-slate-100 dark:bg-slate-800/70 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3.5 py-2.5">Phương Pháp Ước Lượng</th>
                    <th className="px-3 py-2.5">Trung Bình (ȳ)</th>
                    <th className="px-3 py-2.5">Phương Sai (v)</th>
                    <th className="px-3 py-2.5">Sai Số Chuẩn (SE)</th>
                    <th className="px-3.5 py-2.5">Khoảng Tin Cậy 95% [Lower, Upper]</th>
                    <th className="px-3.5 py-2.5">Độ Phóng Đại Sai Số (Inflation)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                  <tr className="bg-indigo-50/30 dark:bg-indigo-950/20 font-medium">
                    <td className="px-3.5 py-2.5 flex items-center gap-2 text-indigo-700 dark:text-indigo-300 font-semibold">
                      <span className="w-2 h-2 rounded-full bg-indigo-600"></span>
                      Mẫu Phức Hợp (Two-Stage Cluster & Taylor)
                    </td>
                    <td className="px-3 py-2.5 font-mono">{result.horvitz_thompson_estimates?.weighted_mean.toFixed(3)}</td>
                    <td className="px-3 py-2.5 font-mono">{result.taylor_linearization_variance?.complex_variance.toFixed(6)}</td>
                    <td className="px-3 py-2.5 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                      {result.taylor_linearization_variance?.complex_se.toFixed(4)}
                    </td>
                    <td className="px-3.5 py-2.5 font-mono">
                      [{result.taylor_linearization_variance?.ci_95_lower.toFixed(3)}, {result.taylor_linearization_variance?.ci_95_upper.toFixed(3)}]
                    </td>
                    <td className="px-3.5 py-2.5 font-mono text-indigo-700 font-bold">
                      {result.srs_comparison?.se_inflation_ratio.toFixed(3)}x (Chuẩn)
                    </td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2.5 flex items-center gap-2 text-slate-500">
                      <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                      Giả Định Ngẫu Nhiên Đơn Giản (SRS - Bỏ qua cụm)
                    </td>
                    <td className="px-3 py-2.5 font-mono text-slate-500">{result.horvitz_thompson_estimates?.weighted_mean.toFixed(3)}</td>
                    <td className="px-3 py-2.5 font-mono text-slate-500">{result.srs_comparison?.srs_variance.toFixed(6)}</td>
                    <td className="px-3 py-2.5 font-mono text-slate-500">{result.srs_comparison?.srs_se.toFixed(4)}</td>
                    <td className="px-3.5 py-2.5 font-mono text-slate-500">
                      [{result.srs_comparison?.ci_95_lower.toFixed(3)}, {result.srs_comparison?.ci_95_upper.toFixed(3)}]
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-400">1.000x (Ảo giác chính xác)</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2.5 leading-relaxed">
              <strong>Giải thích học thuật:</strong> Nếu bỏ qua cấu trúc gom cụm (áp dụng SRS tiêu chuẩn), sai số chuẩn sẽ bị đánh giá thấp đi 
              (ước tính sai số lạc quan quá mức), dẫn đến khoảng tin cậy hẹp giả tạo và làm bùng nổ sai lầm Loại I (Type I error rate inflation).
            </p>
          </div>

          {/* Chi Tiết Phân Phối Cụm & Trọng Số */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50/50 dark:bg-slate-900/30 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                Đặc Điểm Phân Bổ Kích Thước Cụm (Cluster Sizes)
              </span>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Kích thước trung bình (m)</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">{result.cluster_size_summary?.mean_size.toFixed(2)}</span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Độ lệch chuẩn (SD)</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">{result.cluster_size_summary?.std_size.toFixed(2)}</span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Hệ số biến thiên CV(m)</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">{result.cluster_size_summary?.cv_size.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-slate-50/50 dark:bg-slate-900/30 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                Đặc Điểm Phân Bổ Trọng Số Thiết Kế (Sampling Weights)
              </span>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Dân số ước lượng (N̂)</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">{result.weight_summary?.total_population_estimate.toFixed(1)}</span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">Biến thiên trọng số CV(w)</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">{result.weight_summary?.cv_weight.toFixed(2)}</span>
                </div>
                <div className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] text-slate-400 block">DEFF do trọng số (Kish)</span>
                  <span className="font-bold text-slate-800 dark:text-white font-mono">{result.weight_summary?.kish_weight_deff.toFixed(3)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Bảng Phân Tích Chi Tiết Từng Cụm (Top Cụm PSU) */}
          {result.clusters_breakdown && result.clusters_breakdown.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-600" />
                Bảng Phân Bổ Số Liệu Theo Cụm (PSU Breakdown)
              </h4>
              <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm max-h-64 overflow-y-auto">
                <table className="w-full text-xs text-left text-slate-700 dark:text-slate-300">
                  <thead className="bg-slate-100 dark:bg-slate-800/70 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800 sticky top-0">
                    <tr>
                      <th className="px-3.5 py-2">Mã / Tên Cụm (PSU)</th>
                      <th className="px-3 py-2">Phân Tầng (Stratum)</th>
                      <th className="px-3 py-2 text-right">Số Quan Sát (m)</th>
                      <th className="px-3 py-2 text-right">Tổng Trọng Số</th>
                      <th className="px-3.5 py-2 text-right">Trung Bình Cụm</th>
                      <th className="px-3.5 py-2 text-right">Độ Lệch So Với Chung (&Delta;)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                    {result.clusters_breakdown.map((c, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="px-3.5 py-2 font-semibold text-slate-900 dark:text-white">
                          {c.cluster_id}
                        </td>
                        <td className="px-3 py-2 text-slate-500">
                          {c.stratum}
                        </td>
                        <td className="px-3 py-2 font-mono text-right">
                          {c.sample_size}
                        </td>
                        <td className="px-3 py-2 font-mono text-right text-slate-500">
                          {c.sum_weights.toFixed(2)}
                        </td>
                        <td className="px-3.5 py-2 font-mono text-right font-bold text-slate-800 dark:text-slate-200">
                          {c.cluster_mean.toFixed(3)}
                        </td>
                        <td className={`px-3.5 py-2 font-mono text-right font-semibold ${
                          c.deviation_from_mean >= 0 ? 'text-emerald-600' : 'text-amber-600'
                        }`}>
                          {c.deviation_from_mean > 0 ? '+' : ''}{c.deviation_from_mean.toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Trích Dẫn Chuẩn Học Thuật APA 7th Edition */}
          {result.apa_narrative && (
            <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                  <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                  Đoạn Trích Chuẩn Học Thuật APA 7th Edition (Publication-Ready)
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md shadow-2xs flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  {copiedApa ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-indigo-600" />
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
