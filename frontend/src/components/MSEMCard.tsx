import React, { useState } from 'react';
import { api } from '../api/client';
import { MSEMAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface MSEMCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const MSEMCard: React.FC<MSEMCardProps> = ({
  surveyId,
  questions
}) => {
  const [clusterQId, setClusterQId] = useState<string>('');
  const [xQId, setXQId] = useState<string>('');
  const [mQId, setMQId] = useState<string>('');
  const [yQId, setYQId] = useState<string>('');
  const [mcSims, setMcSims] = useState<number>(2000);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MSEMAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleRunAnalysis = async () => {
    if (!clusterQId) {
      setError('Vui lòng chọn câu hỏi phân nhóm / đơn vị (Cluster ID).');
      return;
    }
    if (!xQId) {
      setError('Vui lòng chọn biến tiền đề độc lập (Predictor X).');
      return;
    }
    if (!mQId) {
      setError('Vui lòng chọn biến trung gian (Mediator M).');
      return;
    }
    if (!yQId) {
      setError('Vui lòng chọn biến kết quả phụ thuộc (Outcome Y).');
      return;
    }

    const selected = [clusterQId, xQId, mQId, yQId];
    if (new Set(selected).size < 4) {
      setError('Bốn biến số (Cụm, X, M, Y) phải là 4 câu hỏi phân biệt, không được trùng lặp.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runMSEMAnalysis(surveyId, {
        cluster_question_id: clusterQId,
        x_question_id: xQId,
        m_question_id: mQId,
        y_question_id: yQId,
        n_mc_sims: mcSims,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình cấu trúc đa cấp MSEM.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích MSEM.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30 rounded-full">
              Multilevel SEM (1-1-1 Mediation)
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Preacher, Zyphur &amp; Zhang (2010) • Muthén (1994) • Asparouhov (2008)
            </span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Multilevel Structural Equation Modeling (MSEM)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Phân rã hiệp phương sai trực giao hai cấp độ (Within cá nhân vs Between tổ chức), triệt tiêu hoàn toàn thiên lệch gộp (Conflation Bias) của các mô hình HLM truyền thống khi đánh giá tác động trung gian đa cấp.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến phân cụm (Cluster ID) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            value={clusterQId}
            onChange={(e) => setClusterQId(e.target.value)}
          >
            <option value="">-- Chọn đơn vị / phòng ban --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Tiền đề độc lập (Predictor X) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            value={xQId}
            onChange={(e) => setXQId(e.target.value)}
          >
            <option value="">-- Chọn biến X --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến trung gian (Mediator M) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            value={mQId}
            onChange={(e) => setMQId(e.target.value)}
          >
            <option value="">-- Chọn biến M --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Kết quả phụ thuộc (Outcome Y) *
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            value={yQId}
            onChange={(e) => setYQId(e.target.value)}
          >
            <option value="">-- Chọn biến Y --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>{q.title} ({q.question_type})</option>
            ))}
          </select>
        </div>
      </div>

      {/* Advanced Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Số lần mô phỏng Monte Carlo (Indirect CI)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            value={mcSims}
            onChange={(e) => setMcSims(parseInt(e.target.value))}
          >
            <option value={1000}>1,000 lần lặp</option>
            <option value={2000}>2,000 lần lặp (Khuyến nghị chuẩn Preacher)</option>
            <option value={5000}>5,000 lần lặp (Độ chính xác cao)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Phạm vi dữ liệu (Scope)
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
          >
            <option value="all">Toàn bộ phản hồi (All)</option>
            <option value="verified_clean">Chỉ phản hồi sạch đã kiểm định (Clean)</option>
          </select>
        </div>
      </div>

      {/* Action Button */}
      <div className="mt-5 flex items-center justify-between">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-purple-500/20 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang phân rã hiệp phương sai đa cấp...</span>
            </>
          ) : (
            <>
              <span>Ước lượng Mô hình MSEM</span>
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Quy mô mẫu</span>
              <span className="text-xl font-bold text-white font-mono">
                {result.sample_diagnostics?.n_total}
              </span>
              <span className="text-[11px] text-slate-500 block">
                {result.sample_diagnostics?.n_clusters} cụm (TB: {result.sample_diagnostics?.avg_cluster_size})
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Tương quan Nội cụm (ICC)</span>
              <span className="text-xl font-bold text-purple-400 font-mono">
                {result.intraclass_correlations?.icc_y?.toFixed(3)}
              </span>
              <span className="text-[11px] text-slate-500 block">
                X: {result.intraclass_correlations?.icc_x?.toFixed(2)} | M: {result.intraclass_correlations?.icc_m?.toFixed(2)}
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Trung gian Within (Cá nhân)</span>
              <span className="text-xl font-bold text-sky-400 font-mono">
                {result.level1_within_submodel?.indirect_effect?.toFixed(3)}
              </span>
              <span className="text-[11px] text-sky-500/80 block">
                p = {result.level1_within_submodel?.p_indirect?.toFixed(4)}
              </span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-center">
              <span className="text-xs text-slate-400 block">Trung gian Between (Tổ chức)</span>
              <span className="text-xl font-bold text-purple-300 font-mono">
                {result.level2_between_submodel?.indirect_effect?.toFixed(3)}
              </span>
              <span className="text-[11px] text-purple-400/80 block">
                p = {result.level2_between_submodel?.p_indirect?.toFixed(4)}
              </span>
            </div>
          </div>

          {/* Conflation Bias Diagnostic Banner */}
          <div className={`p-4 rounded-lg border ${
            result.conflation_test?.is_conflated
              ? 'bg-amber-950/20 border-amber-500/30'
              : 'bg-emerald-950/20 border-emerald-500/30'
          }`}>
            <div className="flex items-start gap-3">
              <div className={`p-1.5 rounded-md mt-0.5 ${
                result.conflation_test?.is_conflated
                  ? 'bg-amber-500/10 text-amber-400'
                  : 'bg-emerald-500/10 text-emerald-400'
              }`}>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="text-sm">
                <h4 className={`font-semibold ${
                  result.conflation_test?.is_conflated ? 'text-amber-300' : 'text-emerald-300'
                }`}>
                  Kiểm định Thiên lệch Gộp (Conflation Bias Test: ab_Between - ab_Within = {result.conflation_test?.diff_between_within?.toFixed(3)})
                </h4>
                <p className="text-slate-300 mt-1 leading-relaxed">
                  {result.conflation_test?.interpretation}
                </p>
                <div className="mt-1 font-mono text-xs text-slate-400">
                  95% Monte Carlo CI: [{result.conflation_test?.ci_95_lower?.toFixed(3)}, {result.conflation_test?.ci_95_upper?.toFixed(3)}]
                </div>
              </div>
            </div>
          </div>

          {/* Submodels Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Within Submodel */}
            <div className="bg-slate-950/80 border border-sky-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-sm font-semibold text-sky-400">
                  Level 1: Phân mô hình Within-Cluster (Vi mô)
                </h4>
                <span className="text-[11px] font-mono text-slate-400">Cá nhân i trong Cụm j</span>
              </div>
              <div className="mt-3 space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Đường a (X_W → M_W):</span>
                  <span className="text-white font-semibold">{result.level1_within_submodel?.a_path?.toFixed(3)} (SE: {result.level1_within_submodel?.se_a?.toFixed(3)}, p: {result.level1_within_submodel?.p_a?.toFixed(3)})</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Đường b (M_W → Y_W):</span>
                  <span className="text-white font-semibold">{result.level1_within_submodel?.b_path?.toFixed(3)} (SE: {result.level1_within_submodel?.se_b?.toFixed(3)}, p: {result.level1_within_submodel?.p_b?.toFixed(3)})</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Đường trực tiếp c' (X_W → Y_W):</span>
                  <span className="text-white font-semibold">{result.level1_within_submodel?.c_prime_path?.toFixed(3)} (SE: {result.level1_within_submodel?.se_c_prime?.toFixed(3)})</span>
                </div>
                <div className="flex justify-between py-1.5 bg-sky-950/20 px-2 rounded mt-2">
                  <span className="text-sky-300 font-sans font-medium">Tác động Gián tiếp (ab_W):</span>
                  <span className="text-sky-400 font-bold">{result.level1_within_submodel?.indirect_effect?.toFixed(3)} [{result.level1_within_submodel?.ci_95_lower?.toFixed(3)}, {result.level1_within_submodel?.ci_95_upper?.toFixed(3)}]</span>
                </div>
              </div>
            </div>

            {/* Between Submodel */}
            <div className="bg-slate-950/80 border border-purple-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-sm font-semibold text-purple-400">
                  Level 2: Phân mô hình Between-Cluster (Vĩ mô)
                </h4>
                <span className="text-[11px] font-mono text-slate-400">Bối cảnh Cụm j</span>
              </div>
              <div className="mt-3 space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Đường a (X_B → M_B):</span>
                  <span className="text-white font-semibold">{result.level2_between_submodel?.a_path?.toFixed(3)} (SE: {result.level2_between_submodel?.se_a?.toFixed(3)}, p: {result.level2_between_submodel?.p_a?.toFixed(3)})</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Đường b (M_B → Y_B):</span>
                  <span className="text-white font-semibold">{result.level2_between_submodel?.b_path?.toFixed(3)} (SE: {result.level2_between_submodel?.se_b?.toFixed(3)}, p: {result.level2_between_submodel?.p_b?.toFixed(3)})</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Đường trực tiếp c' (X_B → Y_B):</span>
                  <span className="text-white font-semibold">{result.level2_between_submodel?.c_prime_path?.toFixed(3)} (SE: {result.level2_between_submodel?.se_c_prime?.toFixed(3)})</span>
                </div>
                <div className="flex justify-between py-1.5 bg-purple-950/20 px-2 rounded mt-2">
                  <span className="text-purple-300 font-sans font-medium">Tác động Gián tiếp (ab_B):</span>
                  <span className="text-purple-400 font-bold">{result.level2_between_submodel?.indirect_effect?.toFixed(3)} [{result.level2_between_submodel?.ci_95_lower?.toFixed(3)}, {result.level2_between_submodel?.ci_95_upper?.toFixed(3)}]</span>
                </div>
              </div>
            </div>
          </div>

          {/* Model Fit Diagnostics */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-300">
            <div><span className="text-slate-500">CFI:</span> <span className="text-emerald-400 font-bold">{result.fit_indices?.cfi}</span></div>
            <div><span className="text-slate-500">RMSEA:</span> <span className="text-emerald-400 font-bold">{result.fit_indices?.rmsea}</span></div>
            <div><span className="text-slate-500">SRMR Within:</span> <span className="text-sky-400">{result.fit_indices?.srmr_within}</span></div>
            <div><span className="text-slate-500">SRMR Between:</span> <span className="text-purple-400">{result.fit_indices?.srmr_between}</span></div>
          </div>

          {/* SVG Visualizations */}
          {result.svg_chart && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-hidden">
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-slate-200">
                  Báo cáo Phân tích Chuẩn APA 7th &amp; Khuyến nghị Học thuật
                </h4>
                <button
                  onClick={copyToClipboard}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded transition flex items-center gap-1.5 cursor-pointer"
                >
                  {copiedNarrative ? (
                    <>
                      <span className="text-emerald-400 font-medium">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <span>Sao chép Báo cáo</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-slate-300 space-y-2 whitespace-pre-line leading-relaxed font-sans bg-slate-900/50 p-4 rounded-lg border border-slate-800/60">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
