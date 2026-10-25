import React, { useState } from 'react';
import { api } from '../api/client';
import { CausalTreeAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface CausalTreeCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const CausalTreeCard: React.FC<CausalTreeCardProps> = ({
  surveyId,
  questions
}) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [maxDepth, setMaxDepth] = useState<number>(3);
  const [minLeafSize, setMinLeafSize] = useState<number>(5);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalTreeAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleFeature = (qId: string) => {
    if (selectedFeatures.includes(qId)) {
      setSelectedFeatures(selectedFeatures.filter(id => id !== qId));
    } else {
      setSelectedFeatures([...selectedFeatures, qId]);
    }
  };

  const handleSelectAllFeatures = () => {
    const candidateIds = questions
      .filter(q => q.id !== treatmentQId && q.id !== outcomeQId)
      .map(q => q.id);
    setSelectedFeatures(candidateIds);
  };

  const handleClearFeatures = () => {
    setSelectedFeatures([]);
  };

  const handleRunAnalysis = async () => {
    if (!treatmentQId) {
      setError('Vui lòng chọn biến can thiệp (Treatment Variable T).');
      return;
    }
    if (!outcomeQId) {
      setError('Vui lòng chọn biến kết quả liên tục (Outcome Variable Y).');
      return;
    }
    if (treatmentQId === outcomeQId) {
      setError('Biến can thiệp và biến kết quả không được trùng nhau.');
      return;
    }
    if (selectedFeatures.length === 0) {
      setError('Vui lòng chọn ít nhất 1 biến hiệp biến/đặc trưng để phân nhánh cây (Features X).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runCausalTreeAnalysis(surveyId, {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        feature_question_ids: selectedFeatures,
        max_depth: maxDepth,
        min_leaf_size: minLeafSize,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể huấn luyện Cây Tương Tác Nhân Quả.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích Cây Nhân Quả.');
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

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case 'STRONG_POSITIVE_RESPONDERS':
        return { label: 'Phản Hồi Rất Tích Cực (p<0.05)', color: 'bg-emerald-950 text-emerald-400 border-emerald-800' };
      case 'ADVERSE_BACKFIRE_RESPONDERS':
        return { label: 'Phản Tác Dụng / Tiêu Cực (Backfire)', color: 'bg-rose-950 text-rose-400 border-rose-800' };
      case 'MODERATE_POSITIVE':
        return { label: 'Xu Hướng Tích Cực Nhẹ', color: 'bg-indigo-950 text-indigo-300 border-indigo-800' };
      case 'MODERATE_NEGATIVE':
        return { label: 'Xu Hướng Suy Giảm Nhẹ', color: 'bg-amber-950 text-amber-300 border-amber-800' };
      default:
        return { label: 'Không Có Hiệu Ứng Rõ Rệt', color: 'bg-slate-800 text-slate-400 border-slate-700' };
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-indigo-950 text-indigo-400 border border-indigo-800">
              Honest Causal Trees
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
              Athey & Imbens (PNAS 2016)
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-purple-950 text-purple-400 border border-purple-800">
              Subgroup Identification
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">
            Cây Tương Tác Nhân Quả & Phân Khúc Trung Thực (Honest Causal Interaction Trees)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tự động tìm kiếm các quy tắc phân đoạn đối tượng tối ưu hóa sự khác biệt tác động can thiệp (treatment effect heterogeneity) bằng thuật toán phân chia mẫu trung thực (Honest Sample Splitting).
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">Tất cả mẫu phản hồi</option>
            <option value="verified_clean">Chỉ mẫu làm sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến can thiệp (Treatment T) <span className="text-rose-400">*</span>
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến can thiệp (0/1 hoặc nhóm) --</option>
            {questions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến kết quả (Outcome Y) <span className="text-rose-400">*</span>
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">-- Chọn biến kết quả định lượng --</option>
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Độ sâu tối đa (Max Depth)
          </label>
          <select
            value={maxDepth}
            onChange={(e) => setMaxDepth(parseInt(e.target.value))}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          >
            <option value={2}>2 tầng (Tối đa 4 lá)</option>
            <option value={3}>3 tầng (Tối đa 8 lá)</option>
            <option value={4}>4 tầng (Tối đa 16 lá)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Cỡ lá tối thiểu (Min Leaf Size)
          </label>
          <input
            type="number"
            min={3}
            max={50}
            value={minLeafSize}
            onChange={(e) => setMinLeafSize(parseInt(e.target.value) || 5)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Feature Selection */}
      <div className="mb-6 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-300">
            Hiệp biến / Tiêu chí phân đoạn (Features X): {selectedFeatures.length} đã chọn
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleSelectAllFeatures}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Chọn tất cả
            </button>
            <span className="text-slate-600">|</span>
            <button
              type="button"
              onClick={handleClearFeatures}
              className="text-xs text-slate-400 hover:text-slate-300 transition-colors"
            >
              Bỏ chọn
            </button>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-36 overflow-y-auto pr-1">
          {questions
            .filter(q => q.id !== treatmentQId && q.id !== outcomeQId)
            .map(q => {
              const checked = selectedFeatures.includes(q.id);
              return (
                <label
                  key={q.id}
                  className={`flex items-center gap-2 p-2 rounded text-xs cursor-pointer border transition-all ${
                    checked
                      ? 'bg-indigo-950/40 border-indigo-700 text-indigo-200'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleFeature(q.id)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                  />
                  <span className="truncate" title={q.title}>
                    {q.title}
                  </span>
                </label>
              );
            })}
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium text-xs shadow-lg shadow-indigo-600/30 disabled:opacity-50 transition-all flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang xây dựng Cây Causal Tree trung thực...</span>
            </>
          ) : (
            <span>Nhận Diện Phân Khúc (Honest Causal Tree)</span>
          )}
        </button>

        {error && (
          <div className="text-xs text-rose-400 bg-rose-950/40 border border-rose-800 rounded px-3 py-1.5 max-w-md">
            {error}
          </div>
        )}
      </div>

      {/* Results View */}
      {result && result.status === 'success' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Diagnostic Metrics */}
          {result.sample_diagnostics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Cỡ mẫu N</div>
                <div className="text-base font-bold text-white mt-0.5">
                  {result.sample_diagnostics.n_total.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Tập Cấu Trúc (J_tr)</div>
                <div className="text-base font-bold text-indigo-300 mt-0.5">
                  {result.sample_diagnostics.n_training_structure.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Tập Ước Lượng (J_est)</div>
                <div className="text-base font-bold text-emerald-300 mt-0.5">
                  {result.sample_diagnostics.n_estimation_honest.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Số Phân Khúc (Leaves)</div>
                <div className="text-base font-bold text-cyan-400 mt-0.5">
                  {result.sample_diagnostics.n_subgroups}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Hiệu Ứng Toàn Mẫu (ATE)</div>
                <div className="text-base font-bold text-white mt-0.5">
                  {result.sample_diagnostics.ate_overall.toFixed(3)}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Số Lượng Can Thiệp</div>
                <div className="text-base font-bold text-indigo-400 mt-0.5">
                  {result.sample_diagnostics.n_treated_total} / {result.sample_diagnostics.n_control_total}
                </div>
              </div>
            </div>
          )}

          {/* Subgroup Cards */}
          {result.subgroups && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {result.subgroups.map((leaf) => {
                const badge = getCategoryBadge(leaf.category);
                return (
                  <div key={leaf.leaf_id} className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-400">
                        Phân Khúc #{leaf.leaf_id}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${badge.color}`}>
                        {badge.label}
                      </span>
                    </div>

                    <div className="text-xs font-mono text-indigo-300 font-semibold mb-3 p-2 bg-slate-900 rounded border border-slate-800 truncate" title={leaf.rule}>
                      {leaf.rule}
                    </div>

                    <div className="flex items-baseline justify-between mb-1">
                      <span className="text-xs text-slate-400">Hiệu ứng can thiệp (τ):</span>
                      <span className={`text-xl font-bold font-mono ${leaf.tau_subgroup >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {leaf.tau_subgroup > 0 ? `+${leaf.tau_subgroup.toFixed(4)}` : leaf.tau_subgroup.toFixed(4)}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-400 space-y-0.5">
                      <div>SE: {leaf.se.toFixed(4)} · p-value: {leaf.p_value.toFixed(4)}</div>
                      <div>95% CI: [{leaf.ci_lower.toFixed(3)}, {leaf.ci_upper.toFixed(3)}]</div>
                      <div className="text-slate-500 pt-1">
                        Cỡ mẫu: n={leaf.n_total} (Treated: {leaf.n_treated}, Control: {leaf.n_control})
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* SVG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Sơ Đồ Cây Quyết Định & Biểu Đồ Rừng Hiệu Ứng (Honest Tree & Forest Plot)
              </h3>
              <div
                className="overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Tường Thuật Học Thuật Chuẩn APA 7th (Academic APA 7th Narrative)
                </h4>
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium transition-colors"
                >
                  {copiedNarrative ? (
                    <>
                      <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-emerald-400">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                      </svg>
                      <span>Sao chép đoạn trích</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-serif italic bg-slate-900/60 p-3 rounded border border-slate-800">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
