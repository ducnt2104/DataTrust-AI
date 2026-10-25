import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  RefreshCw, Copy, Check, Table, Filter, Layers, CheckCheck, Info
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, MeasurementInvarianceResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const MeasurementInvarianceCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc biến phân nhóm (categorical)
  const categoricalQuestions = questions.filter((q) =>
    ['single_choice', 'dropdown', 'boolean'].includes(q.question_type) ||
    (q.option_distribution && Object.keys(q.option_distribution).length > 0)
  );

  // Lọc biến thang đo chỉ báo (numeric / scale)
  const scaleQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  const [groupingId, setGroupingId] = useState<string>(categoricalQuestions[0]?.question_id || '');
  const [selectedItemIds, setSelectedItemIds] = useState<string[]>([]);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  useEffect(() => {
    if (scaleQuestions.length >= 2 && selectedItemIds.length === 0) {
      setSelectedItemIds(scaleQuestions.slice(0, 4).map((q) => q.question_id));
    }
  }, [questions]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MeasurementInvarianceResult | null>(null);
  const [copiedApa, setCopiedApa] = useState(false);

  const toggleItem = (qid: string) => {
    setSelectedItemIds((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleSelectAll = () => {
    setSelectedItemIds(scaleQuestions.map((q) => q.question_id));
  };

  const handleRunInvariance = async () => {
    if (!groupingId) {
      setError('Vui lòng chọn biến phân nhóm nhân khẩu học.');
      return;
    }
    if (selectedItemIds.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 câu hỏi chỉ báo thang đo.');
      return;
    }
    if (selectedItemIds.includes(groupingId)) {
      setError('Biến phân nhóm không thể đồng thời là câu hỏi chỉ báo thang đo.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runMeasurementInvariance(surveyId, {
        grouping_question_id: groupingId,
        scale_question_ids: selectedItemIds,
        scope
      });
      if (res.status === 'ERROR' || res.status === 'INSUFFICIENT_GROUPS' || res.status === 'INSUFFICIENT_ITEMS' || res.status === 'INSUFFICIENT_SAMPLE') {
        setError(res.message || 'Không thể thực hiện kiểm định bất biến đo lường.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi kết nối máy chủ để thực hiện kiểm định bất biến.');
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
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200/60 flex items-center justify-center text-purple-600 shadow-xs">
            <CheckCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Kiểm Định Bất Biến Đo Lường Đa Nhóm (Measurement Invariance)
              </h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                CFA 4 Cấp Bậc
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Đánh giá tính tương đương của thang đo (Configural, Metric, Scalar, Strict) theo chuẩn Cheung & Rensvold (2002) và Chen (2007)
            </p>
          </div>
        </div>
      </div>

      {/* Selectors */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Grouping Question */}
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700">Biến phân nhóm so sánh (Grouping Variable):</label>
            <select
              value={groupingId}
              onChange={(e) => setGroupingId(e.target.value)}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-purple-500"
            >
              {categoricalQuestions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.question_title} ({q.question_type})
                </option>
              ))}
            </select>
          </div>

          {/* Scope */}
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700">Phạm vi dữ liệu:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="w-full text-xs bg-white border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-purple-500"
            >
              <option value="all">Toàn bộ phản hồi (All)</option>
              <option value="verified_clean">Đã làm sạch & Xác thực (Clean)</option>
            </select>
          </div>
        </div>

        {/* Scale Indicators */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-purple-600" />
              Chọn các câu hỏi chỉ báo thang đo ({selectedItemIds.length}/{scaleQuestions.length}):
            </span>
            <button
              onClick={handleSelectAll}
              className="text-xs text-purple-700 hover:underline font-medium"
            >
              Chọn tất cả chỉ báo
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto">
            {scaleQuestions.map((q) => {
              const isChecked = selectedItemIds.includes(q.question_id);
              const isGroupVar = q.question_id === groupingId;
              return (
                <label
                  key={q.question_id}
                  className={`flex items-start gap-2 p-2 rounded-lg border text-xs cursor-pointer transition-all ${
                    isGroupVar
                      ? 'opacity-40 pointer-events-none bg-slate-100'
                      : isChecked
                      ? 'bg-purple-50/50 border-purple-300 text-purple-950 font-medium'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    disabled={isGroupVar}
                    onChange={() => toggleItem(q.question_id)}
                    className="mt-0.5 rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span className="line-clamp-2 leading-tight">
                    {q.question_title}
                  </span>
                </label>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-[11px] text-slate-500">
            Tiêu chuẩn chấp nhận bất biến: ΔCFI ≥ -0.010 và ΔRMSEA ≤ +0.015 (Cheung & Rensvold, Chen).
          </span>
          <button
            onClick={handleRunInvariance}
            disabled={loading || !groupingId || selectedItemIds.length < 2}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 transition-all shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Đang kiểm định...' : 'Kiểm định 4 cấp bậc bất biến'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'OK' && (
        <div className="space-y-6">
          {/* Hero Verdict Banner */}
          <div className={`p-5 rounded-2xl border ${
            result.highest_level_achieved === 'STRICT_INVARIANCE' || result.highest_level_achieved === 'SCALAR_INVARIANCE'
              ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950'
              : result.highest_level_achieved === 'METRIC_INVARIANCE'
              ? 'bg-amber-50/70 border-amber-300 text-amber-950'
              : 'bg-rose-50/70 border-rose-300 text-rose-950'
          } space-y-2`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-purple-600 shrink-0" />
                <h4 className="font-extrabold text-sm">
                  Cấp bậc bất biến cao nhất: {result.verdict_badge}
                </h4>
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-white/90 shadow-2xs">
                {result.k_groups} nhóm (N = {result.total_sample_size}) | {result.items_count} chỉ báo
              </span>
            </div>
            <p className="text-xs leading-relaxed font-medium">
              {result.recommendation}
            </p>
          </div>

          {/* 4-Level Model Comparison Table */}
          {result.models_summary && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-purple-600" />
                Bảng so sánh 4 mô hình thứ bậc bất biến (Hierarchical Invariance Models)
              </h4>

              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Mô hình thứ bậc</th>
                      <th className="py-2.5 px-3 text-right">χ² (df)</th>
                      <th className="py-2.5 px-3 text-right">p-value</th>
                      <th className="py-2.5 px-3 text-right">CFI</th>
                      <th className="py-2.5 px-3 text-right">RMSEA</th>
                      <th className="py-2.5 px-3 text-right">Δχ² (Δdf)</th>
                      <th className="py-2.5 px-3 text-right">ΔCFI</th>
                      <th className="py-2.5 px-3 text-right">ΔRMSEA</th>
                      <th className="py-2.5 px-3 text-center">Kết luận</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.models_summary.map((m) => (
                      <tr key={m.level} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-bold text-slate-900">
                          {m.model}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-700">
                          {m.chi_square} ({m.df})
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-700">
                          {m.p_value}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-semibold text-slate-900">
                          {m.cfi}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-700">
                          {m.rmsea}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-600">
                          {m.delta_chi2 !== null ? `${m.delta_chi2} (${m.delta_df})` : '—'}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold">
                          {m.delta_cfi !== null ? (
                            <span className={m.delta_cfi >= -0.010 ? 'text-emerald-600' : 'text-rose-600'}>
                              {m.delta_cfi > 0 ? `+${m.delta_cfi}` : m.delta_cfi}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold">
                          {m.delta_rmsea !== null ? (
                            <span className={m.delta_rmsea <= 0.015 ? 'text-emerald-600' : 'text-rose-600'}>
                              {m.delta_rmsea > 0 ? `+${m.delta_rmsea}` : m.delta_rmsea}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                            m.supported
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}>
                            {m.supported ? 'Thỏa mãn' : 'Bị bác bỏ'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Item Stability Matrix */}
          {result.item_details && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <Table className="w-3.5 h-3.5 text-purple-600" />
                Độ ổn định tải trọng và hệ số chặn theo từng câu hỏi (Item Parameter Stability)
              </h4>

              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Chỉ báo câu hỏi</th>
                      <th className="py-2.5 px-3">Tải trọng theo nhóm (λ)</th>
                      <th className="py-2.5 px-3">Hệ số chặn theo nhóm (τ)</th>
                      <th className="py-2.5 px-3 text-right">Độ lệch tối đa</th>
                      <th className="py-2.5 px-3 text-center">Đánh giá câu hỏi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.item_details.map((it) => (
                      <tr key={it.item_name} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-medium text-slate-900 max-w-xs truncate" title={it.item_name}>
                          {it.item_name}
                        </td>
                        <td className="py-2 px-3 font-mono text-slate-700">
                          {Object.entries(it.loadings).map(([g, val]) => `${g}: ${val}`).join(' | ')}
                        </td>
                        <td className="py-2 px-3 font-mono text-slate-700">
                          {Object.entries(it.intercepts).map(([g, val]) => `${g}: ${val}`).join(' | ')}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-purple-700">
                          {it.max_loading_discrepancy}
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                            it.is_stable
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-amber-50 text-amber-700 border border-amber-200'
                          }`}>
                            {it.is_stable ? 'Ổn định' : 'Chệch tải trọng'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Narrative */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">Đoạn văn trích dẫn khoa học chuẩn APA 7th Edition:</span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="flex items-center gap-1 text-purple-700 hover:text-purple-900 font-semibold text-xs"
                >
                  {copiedApa ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-purple-600" />}
                  <span>{copiedApa ? 'Đã sao chép' : 'Sao chép văn bản'}</span>
                </button>
              </div>
              <p className="p-3 bg-white rounded-lg border border-slate-200/80 italic text-slate-700 leading-relaxed font-serif">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
