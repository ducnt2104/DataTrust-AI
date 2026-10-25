import React, { useState, useEffect } from 'react';
import {
  MessageSquare, Sparkles, CheckCircle2, AlertTriangle,
  TrendingUp, TrendingDown, Activity, Copy, Check, RefreshCw,
  BarChart2, BookOpen, ShieldCheck, Zap, Sliders, Filter,
  FileText, Tag, Layers, Compass
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, TopicModelAnalysisResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const TopicModelingCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc câu hỏi văn bản định tính mở
  const textCandidateQuestions = questions.filter((q) =>
    ['long_text', 'short_text', 'text'].includes(q.question_type) ||
    (q.recent_text_samples && q.recent_text_samples.length > 0)
  );

  // Lọc câu hỏi đồng biến định lượng (Covariates)
  const covariateCandidateQuestions = questions.filter((q) =>
    ['rating', 'nps', 'number', 'likert', 'linear_scale'].includes(q.question_type)
  );

  const [textId, setTextId] = useState<string>('');
  const [covariateId, setCovariateId] = useState<string>('');
  const [numTopics, setNumTopics] = useState<number>(3);
  const [numIterations, setNumIterations] = useState<number>(60);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [result, setResult] = useState<TopicModelAnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);
  const [activeTopicTab, setActiveTopicTab] = useState<number>(1);

  // Khởi tạo mặc định
  useEffect(() => {
    if (textCandidateQuestions.length > 0 && !textId) {
      setTextId(textCandidateQuestions[0].question_id);
    }
    if (covariateCandidateQuestions.length > 0 && !covariateId) {
      setCovariateId(covariateCandidateQuestions[0].question_id);
    }
  }, [questions]);

  const handleRunAnalysis = async () => {
    if (!textId) {
      setError('Vui lòng chọn Câu hỏi văn bản mở để phân tích chủ đề.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runTopicModeling(surveyId, {
        text_question_id: textId,
        covariate_question_id: covariateId || undefined,
        num_topics: numTopics,
        num_iterations: numIterations,
        scope
      });

      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể thực hiện mô hình hóa chủ đề.');
      } else {
        setResult(res);
        if (res.topics && res.topics.length > 0) {
          setActiveTopicTab(res.topics[0].topic_id);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi gọi API phân tích mô hình hóa chủ đề LDA/STM.');
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
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-6 border-b border-slate-100 dark:border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 rounded-xl">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Mô Hình Hóa Chủ Đề Cấu Trúc (STM) & Phân Bổ Dirichlet Tiềm Ẩn (LDA)
                <span className="text-xs px-2.5 py-0.5 font-medium rounded-full bg-teal-100 dark:bg-teal-900/60 text-teal-700 dark:text-teal-300">
                  Blei et al. (2003) & Roberts et al. (2014)
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Khai phá chủ đề tiềm ẩn tự động trên phản hồi mở tiếng Việt qua thuật toán Collapsed Gibbs Sampling, đánh giá độ mạch lạc ngữ nghĩa UMass Coherence và tương quan biến điều kiện.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start lg:self-auto">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="px-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Chỉ phản hồi chuẩn hóa (Verified Clean)</option>
          </select>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-4 py-1.5 text-xs font-medium text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            Chạy Phân Tích STM / LDA
          </button>
        </div>
      </div>

      {/* Control Configuration Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 py-5 border-b border-slate-100 dark:border-slate-800">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
            Câu Hỏi Văn Bản Mở (Text Corpus)
          </label>
          <select
            value={textId}
            onChange={(e) => setTextId(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
          >
            {textCandidateQuestions.length === 0 ? (
              <option value="">(Không có câu hỏi văn bản nào)</option>
            ) : (
              textCandidateQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))
            )}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
            Biến Đồng Biến Điều Kiện (Tùy chọn - STM Covariate)
          </label>
          <select
            value={covariateId}
            onChange={(e) => setCovariateId(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
          >
            <option value="">(Không kiểm soát biến đồng biến)</option>
            {covariateCandidateQuestions.map((q) => (
              <option key={q.question_id} value={q.question_id}>
                {q.question_title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Số Chủ Đề Tiềm Ẩn (K Topics)
            </label>
            <span className="text-xs font-mono font-medium text-teal-600 dark:text-teal-400">
              K = {numTopics}
            </span>
          </div>
          <input
            type="range"
            min="2"
            max="6"
            step="1"
            value={numTopics}
            onChange={(e) => setNumTopics(parseInt(e.target.value))}
            className="w-full accent-teal-600 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>2 (Cơ bản)</span>
            <span>3 (Khuyến nghị)</span>
            <span>6 (Chuyên sâu)</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Vòng Lặp Gibbs Sampling
            </label>
            <span className="text-xs font-mono font-medium text-teal-600 dark:text-teal-400">
              {numIterations} vòng
            </span>
          </div>
          <input
            type="range"
            min="30"
            max="100"
            step="10"
            value={numIterations}
            onChange={(e) => setNumIterations(parseInt(e.target.value))}
            className="w-full accent-teal-600 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>30 vòng</span>
            <span>60 (Tối ưu)</span>
            <span>100 vòng</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="my-4 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="mt-6 space-y-6">
          {/* Hero KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Quy Mô Kho Ngữ Liệu (Corpus N)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {result.sample_size}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">văn bản</span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Kích thước từ vựng đã lọc: {result.vocabulary_size} từ
              </p>
            </div>

            <div className="p-4 rounded-xl bg-teal-50/50 dark:bg-teal-950/30 border border-teal-100 dark:border-teal-900/40">
              <span className="text-xs font-medium text-teal-700 dark:text-teal-300 block mb-1">
                Số Chủ Đề Khai Phá (K Topics)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-teal-600 dark:text-teal-400">
                  {result.num_topics}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300">
                  α = {result.hyperparameters?.alpha?.toFixed(2)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Collapsed Gibbs Sampling: {result.hyperparameters?.iterations} iterations
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Độ Mạch Lạc Ngữ Nghĩa UMass
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-800 dark:text-slate-200">
                  {result.mean_coherence_umass?.toFixed(2)}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  (result.mean_coherence_umass ?? -99) > -3.5
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                }`}>
                  {(result.mean_coherence_umass ?? -99) > -3.5 ? 'Tập trung cao' : 'Khá mạch lạc'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Mimno et al. (2011) Coherence Metric
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Tác Động Biến Điều Kiện (STM)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-800 dark:text-slate-200">
                  {result.covariate_effects && result.covariate_effects.length > 0
                    ? `${result.covariate_effects.length} chủ đề`
                    : 'Chưa gắn'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                {result.covariate_effects && result.covariate_effects.length > 0
                  ? 'Đã ước lượng tương quan OLS'
                  : 'Chọn biến điều kiện để đo độ nhạy'}
              </p>
            </div>
          </div>

          {/* Interactive Topic Explorer */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            {/* Tabs for topics */}
            <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 overflow-x-auto">
              {result.topics?.map((topic) => (
                <button
                  key={topic.topic_id}
                  onClick={() => setActiveTopicTab(topic.topic_id)}
                  className={`px-5 py-3 text-xs font-bold whitespace-nowrap transition-colors border-b-2 flex items-center gap-2 ${
                    activeTopicTab === topic.topic_id
                      ? 'border-teal-600 text-teal-600 dark:text-teal-400 bg-white dark:bg-slate-900'
                      : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  <Tag className="w-3.5 h-3.5" />
                  <span>{topic.short_label}</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-200 dark:bg-slate-700 font-mono">
                    {topic.prevalence_percent}%
                  </span>
                </button>
              ))}
            </div>

            {/* Active Topic Content */}
            {result.topics
              ?.filter((t) => t.topic_id === activeTopicTab)
              .map((topic) => (
                <div key={topic.topic_id} className="p-6 space-y-6">
                  {/* Topic Metadata & Prevalence Bar */}
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                        {topic.label}
                      </h4>
                      <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                        Độ mạch lạc: C_UMass = {topic.coherence_umass}
                      </span>
                    </div>

                    <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3 overflow-hidden flex">
                      <div
                        className="bg-teal-500 h-3 rounded-full transition-all"
                        style={{ width: `${Math.min(100, topic.prevalence_percent * 2)}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">
                      Chiếm {topic.prevalence_percent}% tỷ trọng kho ngữ liệu phản hồi
                    </span>
                  </div>

                  {/* Word Cloud / Keyword Tag Pills */}
                  <div>
                    <h5 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2.5 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-teal-500" />
                      Cụm Từ Khóa Tiềm Ẩn Đặc Trưng (Topic Word Cloud)
                    </h5>
                    <div className="flex flex-wrap gap-2.5 p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800">
                      {topic.top_words?.map((word, idx) => {
                        const isTop = idx < 3;
                        return (
                          <span
                            key={idx}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-transform hover:scale-105 ${
                              isTop
                                ? 'bg-teal-600 text-white font-bold shadow-sm'
                                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                            }`}
                          >
                            <span>{word.word}</span>
                            <span className="text-[10px] opacity-75 font-mono">
                              ({(word.probability * 100).toFixed(1)}%)
                            </span>
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {/* Detailed Word Probabilities Table */}
                  <div>
                    <h5 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2.5 flex items-center gap-1.5">
                      <BarChart2 className="w-3.5 h-3.5 text-teal-500" />
                      Bảng Phân Phối Xác Suất Từ Vựng & Độ Độc Quyền (Topic-Word Distribution Φ)
                    </h5>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 font-semibold">
                          <tr>
                            <th className="py-2.5 px-4">Từ Vựng Tiếng Việt</th>
                            <th className="py-2.5 px-3 text-right">Xác Suất Hậu Nghiệm (Φ)</th>
                            <th className="py-2.5 px-3 text-right">Tần Suất Xuất Hiện</th>
                            <th className="py-2.5 px-3 text-right">Độ Độc Quyền (FREX)</th>
                            <th className="py-2.5 px-4">Thanh Phân Bổ</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                          {topic.top_words?.map((w, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40">
                              <td className="py-2.5 px-4 font-sans font-medium text-slate-800 dark:text-slate-200">
                                {w.word}
                              </td>
                              <td className="py-2.5 px-3 text-right font-bold text-teal-600 dark:text-teal-400">
                                {w.probability.toFixed(4)}
                              </td>
                              <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                                {w.frequency} lần
                              </td>
                              <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                                {w.exclusivity.toFixed(2)}
                              </td>
                              <td className="py-2.5 px-4">
                                <div className="w-32 bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
                                  <div
                                    className="bg-teal-500 h-1.5 rounded-full"
                                    style={{ width: `${Math.min(100, w.probability * 300)}%` }}
                                  />
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ))}
          </div>

          {/* Covariate Structural Effects */}
          {result.covariate_effects && result.covariate_effects.length > 0 && (
            <div className="p-5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-800/30">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-teal-500" />
                Mối Tương Quan Cấu Trúc Giữa Biến Điều Kiện và Sự Xuất Hiện Chủ Đề (Roberts et al. 2014)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {result.covariate_effects.map((cov, idx) => (
                  <div key={idx} className="p-3.5 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                        {cov.topic_label}
                      </span>
                      <span className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[10px] font-bold ${
                        cov.direction === 'positive'
                          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                          : cov.direction === 'negative'
                          ? 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300'
                          : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                      }`}>
                        {cov.direction === 'positive' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        r = {cov.correlation_r > 0 ? '+' : ''}{cov.correlation_r.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      {cov.interpretation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Document Assignment Sample Accordion */}
          {result.document_sample_assignments && result.document_sample_assignments.length > 0 && (
            <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="px-5 py-3.5 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-teal-500" />
                  Mẫu Phân Bổ Chủ Đề Thống Trị Theo Từng Phản Hồi (Document-Topic Assignment θ)
                </h4>
                <span className="text-[11px] text-slate-500 dark:text-slate-400">
                  Hiển thị {result.document_sample_assignments.length} phản hồi
                </span>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-72 overflow-y-auto">
                {result.document_sample_assignments.map((doc, idx) => (
                  <div key={idx} className="p-3.5 hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <p className="text-xs text-slate-700 dark:text-slate-300 italic">
                        "{doc.text_snippet}"
                      </p>
                      {doc.covariate_value !== undefined && doc.covariate_value !== null && (
                        <span className="text-[10px] text-slate-400 font-mono">
                          Điểm kiểm soát: {doc.covariate_value}
                        </span>
                      )}
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 dark:bg-teal-950 text-teal-700 dark:text-teal-300">
                        Chủ đề {doc.dominant_topic_id}
                      </span>
                      <span className="block text-[10px] text-slate-400 font-mono mt-0.5">
                        θ = {(doc.dominant_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative Summary */}
          {result.apa_narrative && (
            <div className="p-5 rounded-xl border border-teal-100 dark:border-teal-900/50 bg-teal-50/30 dark:bg-teal-950/20">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  <h4 className="text-xs font-bold text-teal-900 dark:text-teal-200">
                    Báo Cáo Thuyết Minh Chuẩn APA 7th Edition & Đánh Giá Mạch Lạc Ngữ Nghĩa
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs rounded-md border border-teal-200 dark:border-teal-800 bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 hover:bg-teal-50 dark:hover:bg-slate-800 flex items-center gap-1 transition-colors"
                >
                  {copiedApa ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  {copiedApa ? 'Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 font-serif whitespace-pre-line">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
