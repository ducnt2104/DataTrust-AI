import React, { useState } from 'react';
import {
  NestedLogitResult,
  NestedLogitRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Network,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertTriangle,
  AlertCircle,
  ShieldCheck,
  Sparkles,
  Sliders,
  Layers,
  Activity,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Percent,
  Compass,
  GitBranch,
  Split
} from 'lucide-react';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface Props {
  surveyId: string;
  questions: QuestionSummary[];
}

export const NestedLogitCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [choiceQId, setChoiceQId] = useState<string>('');
  const [alternativeQId, setAlternativeQId] = useState<string>('');
  const [nestQId, setNestQId] = useState<string>('');
  const [choiceIdQId, setChoiceIdQId] = useState<string>('');
  const [selectedAttributes, setSelectedAttributes] = useState<string[]>([]);
  const [costQId, setCostQId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<NestedLogitResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleToggleAttribute = (qId: string) => {
    if (selectedAttributes.includes(qId)) {
      setSelectedAttributes(selectedAttributes.filter(id => id !== qId));
    } else {
      setSelectedAttributes([...selectedAttributes, qId]);
    }
  };

  const handleRun = async () => {
    if (!choiceQId || !alternativeQId || !nestQId || !choiceIdQId) {
      setError('Vui lòng chọn biến lựa chọn (1/0), biến phương án, biến tổ (nest) và biến mã tình huống.');
      return;
    }
    if (selectedAttributes.length === 0 && !costQId) {
      setError('Vui lòng chọn ít nhất 1 thuộc tính hoặc biến chi phí của phương án.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: NestedLogitRequest = {
      choice_question_id: choiceQId,
      alternative_question_id: alternativeQId,
      nest_question_id: nestQId,
      choice_id_question_id: choiceIdQId,
      attribute_question_ids: selectedAttributes,
      cost_question_id: costQId || undefined,
      alpha_level: 0.05,
      scope
    };

    try {
      const res = await api.runNestedLogit(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể ước lượng mô hình Nested Logit.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Nested Logit.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const summary = result?.overall_summary;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-emerald-50 dark:bg-emerald-950/60 rounded-lg text-emerald-600 dark:text-emerald-400">
              <Network className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Mô hình Lựa chọn Cấu trúc Nested Logit &amp; Độ co giãn Thay thế
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            McFadden (1978 Nobel Prize) · Train (2009) · Khắc phục Nghịch lý IIA (Red Bus / Blue Bus) · Hệ số phân kỳ &lambda;_m &isin; (0, 1] · Tương quan sai số trong tổ
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
            McFadden 1978 Nobel Prize
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
            GEV Architecture
          </span>
        </div>
      </div>

      {/* Main Structural Form */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Choice Indicator */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến lựa chọn (Choice 1/0)
          </label>
          <select
            value={choiceQId}
            onChange={(e) => setChoiceQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn biến chỉ thị chọn --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Alternative Identifier */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Phương án lựa chọn (Alternative)
          </label>
          <select
            value={alternativeQId}
            onChange={(e) => setAlternativeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn tên phương án --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Nest Partition */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Nhóm cấu trúc tổ (Nest Category)
          </label>
          <select
            value={nestQId}
            onChange={(e) => setNestQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn phân nhóm tổ --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Situation / Commuter ID */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Mã tình huống (Situation / User ID)
          </label>
          <select
            value={choiceIdQId}
            onChange={(e) => setChoiceIdQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn mã định danh tình huống --</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Attributes & Cost & Scope */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Attributes Checklist */}
        <div>
          <span className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            Các thuộc tính phương án (Attributes):
          </span>
          <div className="max-h-24 overflow-y-auto space-y-1 bg-slate-50 dark:bg-slate-800/50 p-2 rounded-lg border border-slate-200 dark:border-slate-700">
            {numericQuestions
              .filter(q => q.id !== choiceQId && q.id !== costQId)
              .map((q) => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedAttributes.includes(q.id)}
                    onChange={() => handleToggleAttribute(q.id)}
                    className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
          </div>
        </div>

        {/* Cost / Price */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến chi phí / giá tiền (Cost / Price)
          </label>
          <select
            value={costQId}
            onChange={(e) => setCostQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Không chọn (Tùy chọn) --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
          <span className="text-[10px] text-slate-400 mt-1 block">
            Dùng để tính độ co giãn chéo và thặng dư tiêu dùng (Welfare).
          </span>
        </div>

        {/* Scope & Run Button */}
        <div className="flex flex-col justify-between">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Phạm vi mẫu (Scope)
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
            >
              <option value="all">Tất cả phản hồi hợp lệ (All)</option>
              <option value="verified_clean">Chỉ mẫu đã kiểm định sạch (Verified Clean)</option>
            </select>
          </div>

          <div className="flex justify-end pt-3">
            <button
              onClick={handleRun}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  Đang tối ưu hàm hợp lý cấu trúc...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Ước lượng Mô hình Nested Logit
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 rounded-lg text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && summary && (
        <div className="space-y-6 pt-4 border-t border-slate-200 dark:border-slate-800">
          {/* Key Metric Tiles */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Log-Likelihood ln L
              </span>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                {summary.log_likelihood_nested_logit.toFixed(1)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                MNL ln L: {summary.log_likelihood_mnl_baseline.toFixed(1)}
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                McFadden Pseudo R&sup2;
              </span>
              <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                {summary.mcfadden_pseudo_r2.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Độ phù hợp mô hình cấu trúc
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Kiểm định IIA (LR Test)
              </span>
              <span className={`text-lg font-bold ${summary.iia_assumption_rejected ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-700 dark:text-slate-300'}`}>
                &chi;&sup2; = {summary.lr_test_iia_statistic.toFixed(1)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                p = {summary.lr_test_iia_p_value.toFixed(3)} ({summary.iia_assumption_rejected ? 'Bác bỏ IIA' : 'Duy trì IIA'})
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Cấu trúc Tổ (Nests)
              </span>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                M = {summary.n_nests}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {summary.n_alternatives} phương án lựa chọn
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Số tình huống (N)
              </span>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                N = {summary.n_choice_situations}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Quyết định lựa chọn quan sát
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 p-2">
              <div
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                className="w-full flex justify-center"
              />
            </div>
          )}

          {/* Elasticity Insight Alert */}
          {result.elasticity_comparison && (
            <div className="p-4 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900 flex items-start gap-3 text-xs leading-relaxed text-indigo-950 dark:text-indigo-200">
              <Split className="w-5 h-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">
                  Phá vỡ Nghịch lý IIA (Substitution Divergence Multiplier: {result.elasticity_comparison.within_nest_divergence_multiplier}x)
                </span>
                <p className="mt-1">{result.elasticity_comparison.interpretation}</p>
              </div>
            </div>
          )}

          {/* Detailed Tables: Nests & Coefficients */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Nests Diagnostics */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <GitBranch className="w-4 h-4 text-emerald-500" />
                Hệ số Phân kỳ của Tổ (&lambda;_m) &amp; Tương quan Nội tổ (&rho;)
              </h4>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-750 text-slate-600 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2">Tên tổ (Nest)</th>
                      <th className="p-2">Phương án</th>
                      <th className="p-2 text-right">&lambda;_m (SE)</th>
                      <th className="p-2 text-right">Tương quan &rho;</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {result.nests?.map((nest, idx) => (
                      <tr key={idx} className="hover:bg-slate-100/50 dark:hover:bg-slate-700/40">
                        <td className="p-2 font-bold text-slate-800 dark:text-slate-200">
                          {nest.nest_name}
                        </td>
                        <td className="p-2 text-[11px] text-slate-500 truncate max-w-[130px]">
                          {nest.alternatives.join(', ')}
                        </td>
                        <td className="p-2 text-right font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                          {nest.dissimilarity_lambda.toFixed(3)} ({nest.se_lambda.toFixed(3)})
                        </td>
                        <td className="p-2 text-right font-mono">
                          {nest.intra_nest_correlation_rho.toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Coefficients Table */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-blue-500" />
                Hệ số Hữu dụng Thuộc tính (Structural Utility Coefficients &beta;)
              </h4>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-750 text-slate-600 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2">Thuộc tính</th>
                      <th className="p-2 text-right">Hệ số &beta;</th>
                      <th className="p-2 text-right">SE</th>
                      <th className="p-2 text-right">t-stat</th>
                      <th className="p-2 text-right">p-value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {result.coefficients?.map((coef, idx) => (
                      <tr key={idx} className="hover:bg-slate-100/50 dark:hover:bg-slate-700/40">
                        <td className="p-2 font-medium text-slate-800 dark:text-slate-200">
                          {coef.parameter}
                        </td>
                        <td className={`p-2 text-right font-mono font-bold ${coef.coefficient >= 0 ? 'text-blue-600 dark:text-blue-400' : 'text-amber-600 dark:text-amber-400'}`}>
                          {coef.coefficient > 0 ? `+${coef.coefficient.toFixed(3)}` : coef.coefficient.toFixed(3)}
                        </td>
                        <td className="p-2 text-right font-mono text-slate-500">{coef.se.toFixed(3)}</td>
                        <td className="p-2 text-right font-mono">{coef.t_statistic.toFixed(2)}</td>
                        <td className="p-2 text-right font-mono">{coef.p_value.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* APA Narrative Block */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-750 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-emerald-500" />
                  Bản tường trình Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyAPA}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-serif italic">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
