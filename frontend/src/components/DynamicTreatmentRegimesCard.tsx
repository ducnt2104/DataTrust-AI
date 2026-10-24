import React, { useState } from 'react';
import { DynamicTreatmentRegimesResult } from '../types/survey';
import { api } from '../api/client';

interface DynamicTreatmentRegimesCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const DynamicTreatmentRegimesCard: React.FC<DynamicTreatmentRegimesCardProps> = ({ surveyId, questions }) => {
  const [outcomeQid, setOutcomeQid] = useState<string>('');
  const [stage1ActionQid, setStage1ActionQid] = useState<string>('');
  const [stage2ActionQid, setStage2ActionQid] = useState<string>('');
  const [baselineQid, setBaselineQid] = useState<string>('');
  const [interimQid, setInterimQid] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DynamicTreatmentRegimesResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Numeric / Continuous questions for Outcome, Baseline, Interim
  const numericQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider'
  );

  // Binary / Categorical questions for Action 1 and Action 2
  const actionQuestions = questions.filter(
    (q) =>
      q.question_type === 'single_choice' ||
      q.question_type === 'dropdown' ||
      q.question_type === 'number' ||
      q.question_type === 'linear_scale'
  );

  const handleRun = async () => {
    if (!outcomeQid || !stage1ActionQid || !stage2ActionQid || !baselineQid || !interimQid) {
      setError('Vui lòng chọn đầy đủ cả 5 biến: Kết quả Y, Can thiệp S1, Nền tảng X1, Trạng thái giữa kỳ X2, và Can thiệp S2.');
      return;
    }

    const uniqueCheck = new Set([outcomeQid, stage1ActionQid, stage2ActionQid, baselineQid, interimQid]);
    if (uniqueCheck.size < 5) {
      setError('Các câu hỏi được chọn phải phân biệt hoàn toàn, không được trùng lặp.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runDynamicTreatmentRegimes(surveyId, {
        outcome_question_id: outcomeQid,
        stage1_action_question_id: stage1ActionQid,
        stage2_action_question_id: stage2ActionQid,
        baseline_covariate_question_id: baselineQid,
        interim_state_question_id: interimQid,
        scope
      });

      if (res.status === 'error' || res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'ESTIMATION_FAILED') {
        setError(res.message || 'Ước lượng chế độ can thiệp động thất bại.');
      } else {
        setResult(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi kết nối máy chủ khi tính toán Q-learning DTR.');
    } finally {
      setLoading(false);
    }
  };

  const copyNarrative = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-700/60 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
              Murphy 2003 &bull; Robins 2004 &bull; Schulte et al. 2014
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Sequential Q-Learning Backward Induction
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            Chế độ Can thiệp Động Đa Giai đoạn (Dynamic Treatment Regimes - DTR)
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Tối ưu hóa chính sách can thiệp thích ứng cá nhân hóa hai giai đoạn dựa trên quy nạp ngược Q-Learning.
          </p>
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Outcome Y */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Biến Kết quả Cuối kỳ (Outcome Y) *
          </label>
          <select
            value={outcomeQid}
            onChange={(e) => setOutcomeQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn câu hỏi đo lường kết quả Y --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Baseline X1 */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Biến Nền tảng Ban đầu (Baseline $X_1$) *
          </label>
          <select
            value={baselineQid}
            onChange={(e) => setBaselineQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến điều chỉnh Stage 1 --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Stage 1 Action A1 */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Can thiệp Giai đoạn 1 (Action $A_1$) *
          </label>
          <select
            value={stage1ActionQid}
            onChange={(e) => setStage1ActionQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn hành động can thiệp S1 --</option>
            {actionQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Interim State X2 */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Trạng thái Đo lường Giữa kỳ (Interim $X_2$) *
          </label>
          <select
            value={interimQid}
            onChange={(e) => setInterimQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn biến phản hồi giữa kỳ S2 --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Stage 2 Action A2 */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Can thiệp Giai đoạn 2 (Action $A_2$) *
          </label>
          <select
            value={stage2ActionQid}
            onChange={(e) => setStage2ActionQid(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Chọn hành động can thiệp S2 --</option>
            {actionQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        {/* Scope Filter */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
            Phạm vi Lọc Dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">Toàn bộ mẫu khảo sát (All)</option>
            <option value="verified_clean">Chỉ mẫu sạch đã kiểm định (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Run Action */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleRun}
          disabled={loading || !outcomeQid || !stage1ActionQid || !stage2ActionQid || !baselineQid || !interimQid}
          className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-medium text-sm transition shadow-sm flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang tối ưu hóa Q-Learning DTR...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Ước lượng Chính sách Thích ứng Tối ưu (Q-Learning d*)
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="space-y-6 pt-4 border-t border-slate-100 dark:border-slate-700/60">
          {/* Diagnostic Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200/80 dark:border-emerald-800/60">
              <span className="text-xs text-emerald-700 dark:text-emerald-400 font-medium">Chính sách Tối ưu V(d*)</span>
              <p className="text-lg font-bold text-emerald-800 dark:text-emerald-200 mt-0.5">
                {result.diagnostics.v_optimal.toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Luôn Can thiệp V(1,1)</span>
              <p className="text-base font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
                {result.diagnostics.v_always_treated.toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Không Can thiệp V(0,0)</span>
              <p className="text-base font-bold text-slate-700 dark:text-slate-300 mt-0.5">
                {result.diagnostics.v_never_treated.toFixed(3)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Giá trị Gia tăng (&Delta;V*)</span>
              <p className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                +{result.diagnostics.policy_value_gain.toFixed(3)} (+{result.diagnostics.policy_value_gain_pct.toFixed(1)}%)
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Ngưỡng Phân bổ S1 (X1*)</span>
              <p className="text-base font-bold text-blue-600 dark:text-blue-400 mt-0.5">
                {result.diagnostics.stage1_threshold.toFixed(2)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200/60 dark:border-slate-700">
              <span className="text-xs text-slate-500 dark:text-slate-400">Ngưỡng Thích ứng S2 (X2*)</span>
              <p className="text-base font-bold text-teal-600 dark:text-teal-400 mt-0.5">
                {result.diagnostics.stage2_threshold.toFixed(2)}
              </p>
            </div>
          </div>

          {/* Model Regression Diagnostics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Stage 1 Q-Model */}
            {result.stage1_model && (
              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-700 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Hàm Q Giai đoạn 1 ($Q_1(H_1, A_1)$)
                  </h4>
                  <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                    $R^2 = {result.stage1_model.r_squared.toFixed(3)}$
                  </span>
                </div>
                <div className="text-xs font-mono space-y-1 text-slate-600 dark:text-slate-300">
                  <div className="flex justify-between">
                    <span>Hệ số tương tác ($A_1 \times X_1$):</span>
                    <span className="font-bold text-indigo-600 dark:text-indigo-400">{result.stage1_model.interaction_a1_x1.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Sai số chuẩn SE:</span>
                    <span>{result.stage1_model.se_interaction.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Kiểm định $t$-stat (p-value):</span>
                    <span>{result.stage1_model.t_stat.toFixed(3)} (p = {result.stage1_model.p_value.toFixed(4)})</span>
                  </div>
                </div>
              </div>
            )}

            {/* Stage 2 Q-Model */}
            {result.stage2_model && (
              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-700 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Hàm Q Giai đoạn 2 ($Q_2(H_2, A_2)$)
                  </h4>
                  <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                    $R^2 = {result.stage2_model.r_squared.toFixed(3)}$
                  </span>
                </div>
                <div className="text-xs font-mono space-y-1 text-slate-600 dark:text-slate-300">
                  <div className="flex justify-between">
                    <span>Hệ số tương tác ($A_2 \times X_2$):</span>
                    <span className="font-bold text-teal-600 dark:text-teal-400">{result.stage2_model.interaction_a2_x2.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Sai số chuẩn SE:</span>
                    <span>{result.stage2_model.se_interaction.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Kiểm định $t$-stat (p-value):</span>
                    <span>{result.stage2_model.t_stat.toFixed(3)} (p = {result.stage2_model.p_value.toFixed(4)})</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* SVG Diagram */}
          {result.svg_visualization && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Sơ đồ Khoa học: Cây Quyết định DTR &amp; So sánh Kỳ vọng Chính sách
              </h4>
              <div
                className="w-full overflow-x-auto rounded-lg bg-slate-900 p-2 shadow-inner flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                  Bản tường trình Học thuật chuẩn APA 7th (Dynamic Treatment Regimes Q-Learning)
                </span>
                <button
                  onClick={copyNarrative}
                  className="px-2.5 py-1 text-xs font-medium rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 transition"
                >
                  {copied ? 'Đã sao chép!' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-400 font-serif italic">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
