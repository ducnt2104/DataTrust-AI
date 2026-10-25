import React, { useState } from 'react';
import { api } from '../api/client';
import { CausalForestAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface CausalForestCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const CausalForestCard: React.FC<CausalForestCardProps> = ({
  surveyId,
  questions
}) => {
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [nTrees, setNTrees] = useState<number>(40);
  const [minLeafSize, setMinLeafSize] = useState<number>(5);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalForestAnalysisResult | null>(null);
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
      setError('Vui lòng chọn biến can thiệp (Treatment Variable W).');
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
      setError('Vui lòng chọn ít nhất 1 biến đặc trưng / hiệp biến (Covariates X).');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runCausalForestAnalysis(surveyId, {
        treatment_question_id: treatmentQId,
        outcome_question_id: outcomeQId,
        feature_question_ids: selectedFeatures,
        n_trees: nTrees,
        min_leaf_size: minLeafSize,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể huấn luyện mô hình Causal Forest.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi ước lượng Causal Forest.');
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
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
              GRF Ensemble
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-indigo-950 text-indigo-400 border border-indigo-800">
              Athey, Tibshirani & Wager (2019)
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">
            Mô Hình Rừng Nhân Quả Suy Rộng (Generalized Causal Forest)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ước lượng tác động can thiệp không đồng nhất ở cấp độ cá thể (CATE $\hat\tau(X)$) bằng thuật toán Honest Causal Trees phân chia mẫu vô thiên lệch.
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Biến can thiệp (Treatment W) <span className="text-rose-400">*</span>
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

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Số cây (n_trees)
            </label>
            <input
              type="number"
              min={10}
              max={200}
              value={nTrees}
              onChange={(e) => setNTrees(parseInt(e.target.value) || 40)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Min Leaf Size
            </label>
            <input
              type="number"
              min={2}
              max={50}
              value={minLeafSize}
              onChange={(e) => setMinLeafSize(parseInt(e.target.value) || 5)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Feature Selection */}
      <div className="mb-6 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-300">
            Hiệp biến / Đặc trưng phân hóa (Covariates X): {selectedFeatures.length} đã chọn
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
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-40 overflow-y-auto pr-1">
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
              <span>Đang huấn luyện Causal Forest...</span>
            </>
          ) : (
            <span>Ước Lượng Hiệu Ứng CATE (Honest Forest)</span>
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
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Nhóm Can Thiệp (W=1)</div>
                <div className="text-base font-bold text-emerald-400 mt-0.5">
                  {result.sample_diagnostics.n_treated.toLocaleString()} ({result.sample_diagnostics.p_treated}%)
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Nhóm Đối Chứng (W=0)</div>
                <div className="text-base font-bold text-slate-300 mt-0.5">
                  {result.sample_diagnostics.n_control.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Số Đặc Trưng (X)</div>
                <div className="text-base font-bold text-indigo-300 mt-0.5">
                  {result.sample_diagnostics.n_features}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Số Cây (Trees)</div>
                <div className="text-base font-bold text-slate-200 mt-0.5">
                  {result.sample_diagnostics.n_trees}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Tác Động Dương</div>
                <div className="text-base font-bold text-cyan-400 mt-0.5">
                  {result.cate_summary?.p_positive_effect}%
                </div>
              </div>
            </div>
          )}

          {/* CATE Summary Cards */}
          {result.cate_summary && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Hiệu ứng Trung bình (Average Treatment Effect - ATE)</div>
                <div className="text-2xl font-bold text-indigo-400">
                  {result.cate_summary.mean_ate.toFixed(4)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  SE: {result.cate_summary.se_ate.toFixed(4)} · 95% CI: [{result.cate_summary.ci_95_lower.toFixed(4)}, {result.cate_summary.ci_95_upper.toFixed(4)}]
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Phân vị CATE (Median & IQR)</div>
                <div className="text-2xl font-bold text-emerald-400">
                  {result.cate_summary.median_cate.toFixed(4)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  IQR: {result.cate_summary.iqr_cate.toFixed(4)} · Khoảng giá trị: [{result.cate_summary.min_cate.toFixed(3)}, {result.cate_summary.max_cate.toFixed(3)}]
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Kiểm định Tính Không Đồng Nhất (Heterogeneity Test)</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-base font-bold ${result.cate_summary.has_heterogeneity ? 'text-amber-400' : 'text-slate-400'}`}>
                    {result.cate_summary.has_heterogeneity ? 'Có phân hóa (Heterogeneous)' : 'Đồng nhất (Homogeneous)'}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    p = {result.cate_summary.heterogeneity_p_value.toFixed(4)}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Var(CATE): {result.cate_summary.heterogeneity_variance.toFixed(4)}
                </div>
              </div>
            </div>
          )}

          {/* SVG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Biểu Đồ Phân Phối CATE & Tầm Quan Trọng Biến (GRF Diagnostic Chart)
              </h3>
              <div
                className="overflow-x-auto flex justify-center py-2"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Variable Importance & Distribution Tables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Variable Importance */}
            {result.variable_importance && result.variable_importance.length > 0 && (
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-slate-300 mb-3 uppercase tracking-wider">
                  Mức Độ Đóng Góp Vào Tính Phân Hóa (Variable Importance)
                </h4>
                <div className="space-y-2">
                  {result.variable_importance.map((v, i) => (
                    <div key={i} className="text-xs">
                      <div className="flex justify-between text-slate-300 mb-1">
                        <span className="font-medium truncate max-w-[200px]" title={v.feature}>{v.feature}</span>
                        <span className="text-indigo-400 font-semibold">{v.relative_pct}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-1.5 rounded-full transition-all"
                          style={{ width: `${v.relative_pct}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CATE Distribution Bins */}
            {result.cate_distribution && result.cate_distribution.length > 0 && (
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-slate-300 mb-3 uppercase tracking-wider">
                  Phân Bổ Tần Suất Hiệu Ứng CATE
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="pb-1.5 font-medium">Khoảng CATE</th>
                        <th className="pb-1.5 font-medium text-right">Số lượng</th>
                        <th className="pb-1.5 font-medium text-right">Tỷ lệ</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-850">
                      {result.cate_distribution.map((bin, i) => (
                        <tr key={i} className="text-slate-300">
                          <td className="py-1 text-slate-200 font-mono text-[11px]">{bin.bin_label}</td>
                          <td className="py-1 text-right font-medium">{bin.count}</td>
                          <td className="py-1 text-right text-indigo-400 font-semibold">{bin.pct}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

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
