import React, { useState } from 'react';
import { api } from '../api/client';
import { CausalDAGResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface CausalDAGCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const CausalDAGCard: React.FC<CausalDAGCardProps> = ({
  surveyId,
  questions
}) => {
  const [selectedQIds, setSelectedQIds] = useState<string[]>([]);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [maxCondSize, setMaxCondSize] = useState<number>(2);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CausalDAGResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleQuestion = (qid: string) => {
    if (selectedQIds.includes(qid)) {
      setSelectedQIds(selectedQIds.filter(id => id !== qid));
    } else {
      setSelectedQIds([...selectedQIds, qid]);
    }
  };

  const selectAll = () => {
    setSelectedQIds(numericQuestions.map(q => q.id));
  };

  const clearAll = () => {
    setSelectedQIds([]);
  };

  const handleRunAnalysis = async () => {
    if (selectedQIds.length < 3) {
      setError('Vui lòng chọn tối thiểu 3 câu hỏi để suy diễn cấu trúc mạng lưới nhân quả DAG.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runCausalDAGAnalysis(surveyId, {
        question_ids: selectedQIds,
        alpha,
        max_cond_size: maxCondSize,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể suy diễn cấu trúc đồ thị nhân quả DAG.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích Causal DAG.');
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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-teal-500/10 text-teal-400 font-bold text-sm">
              PC-DAG
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Causal DAG &amp; Structure Learning (Mạng lưới Đồ thị Nhân quả Có hướng - Thuật toán PC)
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Suy diễn hướng tác động nhân quả trực tiếp (X → Y) từ dữ liệu khảo sát quan sát, tách biệt nguyên nhân gốc, biến trung gian và kết quả hạ nguồn (Spirtes et al., 2000; Pearl, 2009; Meek, 1995).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Bộ lọc dữ liệu:</span>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-teal-500"
          >
            <option value="all">Tất cả phản hồi hoàn thành</option>
            <option value="verified_clean">Chỉ mẫu sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="mt-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Chọn các biến/mục hỏi đưa vào mạng lưới nhân quả (Tối thiểu 3 biến):
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAll}
              className="text-xs text-teal-400 hover:text-teal-300 underline"
            >
              Chọn tất cả
            </button>
            <span className="text-slate-600">|</span>
            <button
              type="button"
              onClick={clearAll}
              className="text-xs text-slate-400 hover:text-slate-300 underline"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        {/* Question Selector Pills */}
        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-2 bg-slate-800/40 rounded-xl border border-slate-700/60">
          {numericQuestions.map(q => {
            const isSelected = selectedQIds.includes(q.id);
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => toggleQuestion(q.id)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all text-left ${
                  isSelected
                    ? 'bg-teal-500/20 border-teal-400 text-teal-300 font-semibold shadow-sm'
                    : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-200'
                }`}
              >
                {isSelected ? '✓ ' : '+ '}
                {q.title}
              </button>
            );
          })}
        </div>

        {/* Hyperparameters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/60">
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Ngưỡng kiểm định độc lập có điều kiện (α Significance Level):
            </label>
            <select
              value={alpha}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-teal-500 focus:outline-none"
            >
              <option value={0.01}>α = 0.01 (Nghiêm ngặt - Chỉ giữ liên kết rất mạnh)</option>
              <option value={0.05}>α = 0.05 (Chuẩn mực khoa học xã hội &amp; tâm trắc)</option>
              <option value={0.10}>α = 0.10 (Mở rộng - Giữ thêm các liên kết tiềm năng)</option>
            </select>
          </div>

          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/60">
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Cỡ tập hợp điều kiện tối đa (|S| Conditioning Set Size):
            </label>
            <select
              value={maxCondSize}
              onChange={(e) => setMaxCondSize(parseInt(e.target.value, 10))}
              className="w-full bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-teal-500 focus:outline-none"
            >
              <option value={1}>|S| ≤ 1 (Nhanh - Kiểm soát 1 biến đồng thời)</option>
              <option value={2}>|S| ≤ 2 (Khuyến nghị - Kiểm soát cặp biến đồng thời)</option>
              <option value={3}>|S| ≤ 3 (Chuyên sâu - Kiểm soát bộ 3 biến đồng thời)</option>
            </select>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-2">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-6 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs tracking-wide uppercase transition-all shadow-lg shadow-teal-900/30 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Đang suy diễn đồ thị nhân quả DAG...
              </>
            ) : (
              'Suy Diễn Đồ Thị Nhân Quả DAG'
            )}
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mt-5 p-4 bg-red-950/40 border border-red-800/80 rounded-lg text-sm text-red-300 flex items-start gap-2">
          <span className="text-base">⚠️</span>
          <div>
            <div className="font-semibold">Thông báo phân tích:</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && result.status === 'success' && (
        <div className="mt-8 space-y-6">
          {/* Diagnostic KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Total Edges */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                Quy Mô Mạng Lưới
              </span>
              <div className="text-2xl font-black text-white mt-1">
                {result.edges_count} liên kết
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {result.directed_edges_count} có hướng (→) | {result.undirected_edges_count} vô hướng (—)
              </div>
              <div className="text-xs text-teal-400 mt-0.5">
                {result.variables_count} nút biến khảo sát
              </div>
            </div>

            {/* Root Causes */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-emerald-400 tracking-wider">
                Động Lực Gốc (Root Drivers)
              </span>
              <div className="text-2xl font-black text-emerald-300 mt-1">
                {result.root_causes?.length || 0} biến
              </div>
              <div className="text-xs text-slate-400 mt-1 line-clamp-1" title={result.root_causes?.join(', ')}>
                {result.root_causes && result.root_causes.length > 0 ? result.root_causes.join(', ') : 'Không có nút gốc đơn lẻ'}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Kích hoạt luồng tác động ban đầu
              </div>
            </div>

            {/* Mediators */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-sky-400 tracking-wider">
                Biến Trung Gian (Mediators)
              </span>
              <div className="text-2xl font-black text-sky-300 mt-1">
                {result.mediators?.length || 0} biến
              </div>
              <div className="text-xs text-slate-400 mt-1 line-clamp-1" title={result.mediators?.join(', ')}>
                {result.mediators && result.mediators.length > 0 ? result.mediators.join(', ') : 'Không có nút trung gian'}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Cầu nối truyền dẫn hiệu ứng gián tiếp
              </div>
            </div>

            {/* Sink Outcomes */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-amber-400 tracking-wider">
                Kết Quả Hạ Nguồn (Sinks)
              </span>
              <div className="text-2xl font-black text-amber-300 mt-1">
                {result.sink_outcomes?.length || 0} biến
              </div>
              <div className="text-xs text-slate-400 mt-1 line-clamp-1" title={result.sink_outcomes?.join(', ')}>
                {result.sink_outcomes && result.sink_outcomes.length > 0 ? result.sink_outcomes.join(', ') : 'Không có nút hạ nguồn'}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Chỉ số đầu ra chịu tác động tổng hợp
              </div>
            </div>
          </div>

          {/* Vector SVG DAG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-inner">
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                Sơ đồ Trực quan Mạng lưới Nhân quả Có hướng (DAG Topological Graph)
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* Causal Edges Table */}
          {result.edges && result.edges.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
              <div className="p-4 border-b border-slate-800 font-bold text-xs text-slate-300 uppercase tracking-wider">
                Danh Sách Các Mối Quan Hệ Nhân Quả Khám Phá Được (Edge List)
              </div>
              <div className="overflow-x-auto max-h-60 overflow-y-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead className="sticky top-0 bg-slate-800/90 backdrop-blur z-10">
                    <tr className="text-slate-400 border-b border-slate-700/60 font-semibold">
                      <th className="py-2 px-4">Chiều tác động</th>
                      <th className="py-2 px-4">Loại liên kết</th>
                      <th className="py-2 px-4">Nguồn (Source)</th>
                      <th className="py-2 px-4">Đích (Target)</th>
                      <th className="py-2 px-4">Hệ số tương quan bán phần</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {result.edges.map((e, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2 px-4 font-mono font-bold text-teal-400">
                          {e.direction}
                        </td>
                        <td className="py-2 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              e.type === 'directed'
                                ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                                : 'bg-slate-800 text-slate-400 border border-slate-700'
                            }`}
                          >
                            {e.type === 'directed' ? 'Có hướng (→)' : 'Vô hướng (—)'}
                          </span>
                        </td>
                        <td className="py-2 px-4 text-slate-200">{e.source_name}</td>
                        <td className="py-2 px-4 text-slate-200">{e.target_name}</td>
                        <td className="py-2 px-4 font-mono text-emerald-400">{e.weight > 0 ? `+${e.weight.toFixed(3)}` : e.weight.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Academic Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700/60 relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-teal-400 uppercase tracking-wider">
                  Diễn giải Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="text-xs px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
                >
                  {copiedNarrative ? '✓ Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed italic whitespace-pre-line">
                {result.apa_narrative}
              </p>
            </div>
          )}

          {/* Methodological Reference Note */}
          <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="font-semibold text-slate-300">Tài liệu tham khảo phương pháp:</div>
            <ul className="list-disc list-inside space-y-0.5 text-slate-400">
              <li>Spirtes, P., Glymour, C. N., &amp; Scheines, R. (2000). <em>Causation, Prediction, and Search</em> (2nd ed.). MIT Press.</li>
              <li>Pearl, J. (2009). <em>Causality: Models, Reasoning, and Inference</em> (2nd ed.). Cambridge University Press.</li>
              <li>Kalisch, M., &amp; Bühlmann, P. (2007). Estimating high-dimensional directed acyclic graphs with the PC-algorithm. <em>Journal of Machine Learning Research</em>, 8, 613-636.</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
