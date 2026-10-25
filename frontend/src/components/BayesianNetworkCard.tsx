import React, { useState } from 'react';
import { BayesianNetworkResult } from '../types/survey';
import { api } from '../api/client';

interface BayesianNetworkCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const BayesianNetworkCard: React.FC<BayesianNetworkCardProps> = ({ surveyId, questions }) => {
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [maxParents, setMaxParents] = useState<number>(3);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BayesianNetworkResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Filter numeric/scale/rating questions for continuous Gaussian Bayesian Network
  const validQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'rating' ||
      q.question_type === 'slider' ||
      q.question_type === 'matrix'
  );

  const toggleQuestion = (qid: string) => {
    setSelectedQuestions((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const selectAll = () => {
    if (selectedQuestions.length === validQuestions.length) {
      setSelectedQuestions([]);
    } else {
      setSelectedQuestions(validQuestions.map((q) => q.id));
    }
  };

  const handleRun = async () => {
    if (selectedQuestions.length < 2) {
      setError('Vui lòng chọn ít nhất 2 biến số để học cấu trúc mạng Bayes DAG.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runBayesianNetwork(surveyId, {
        question_ids: selectedQuestions,
        max_parents: maxParents,
        scope
      });

      if (res.status === 'error') {
        setError(res.message || 'Học cấu trúc mạng Bayes thất bại.');
      } else {
        setResult(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Lỗi kết nối máy chủ khi tính toán mạng Bayes.');
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
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
              Heckerman 1995 &bull; Scutari 2010
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Score-Based Hill-Climbing BIC &bull; DAG
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            Học Cấu trúc Mạng Bayes Gaussian (Bayesian Network DAG Learning)
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Khám phá quan hệ phụ thuộc có hướng (DAG), phân loại vai trò topo (Root Cause, Mediator, Sink) và xác định Markov Blanket độc lập có điều kiện.
          </p>
        </div>
      </div>

      {/* Configuration */}
      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              Chọn các biến số khảo sát tham gia mạng (Tối thiểu 2 biến):
            </label>
            {validQuestions.length > 0 && (
              <button
                type="button"
                onClick={selectAll}
                className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                {selectedQuestions.length === validQuestions.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
              </button>
            )}
          </div>

          {validQuestions.length === 0 ? (
            <p className="text-xs text-amber-600 dark:text-amber-400 italic">
              Không tìm thấy câu hỏi dạng thang đo số (Likert, rating, number) trong khảo sát.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 max-h-56 overflow-y-auto p-2 border border-slate-200 dark:border-slate-700 rounded-lg">
              {validQuestions.map((q) => {
                const isSelected = selectedQuestions.includes(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => toggleQuestion(q.id)}
                    className={`flex items-start text-left gap-2 p-2 rounded-md text-xs transition-colors ${
                      isSelected
                        ? 'bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-300 dark:border-indigo-700 text-indigo-900 dark:text-indigo-200'
                        : 'bg-slate-50 dark:bg-slate-700/50 border border-transparent text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      readOnly
                      className="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{q.title}</div>
                      <span className="text-[10px] text-slate-400 capitalize">
                        {q.question_type.replace('_', ' ')}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Parameters row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Số nút cha tối đa mỗi nút (Max Parents In-Degree):
            </label>
            <select
              value={maxParents}
              onChange={(e) => setMaxParents(Number(e.target.value))}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            >
              <option value={1}>1 (Cây / Tree Structure đơn giản)</option>
              <option value={2}>2 (Giới hạn 2 cha / Sparse DAG)</option>
              <option value={3}>3 (Khuyến nghị mặc định / Balanced)</option>
              <option value={4}>4 (Mạng phức tạp / High Degree)</option>
              <option value={5}>5 (Không giới hạn chặt / Dense)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Phạm vi lọc phản hồi:
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'all' | 'verified_clean')}
              className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-slate-800 dark:text-slate-200"
            >
              <option value="all">Tất cả phản hồi hợp lệ (All Valid)</option>
              <option value="verified_clean">Chỉ phản hồi sạch đã kiểm định (Verified Clean)</option>
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={handleRun}
          disabled={loading || selectedQuestions.length < 2}
          className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Đang tối ưu cấu trúc DAG Hill-Climbing...
            </>
          ) : (
            'Học cấu trúc Mạng Bayes DAG'
          )}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-300">
          <strong>Lỗi:</strong> {error}
        </div>
      )}

      {/* Results View */}
      {result && result.diagnostics && (
        <div className="space-y-6 pt-4 border-t border-slate-100 dark:border-slate-700/60">
          {/* Diagnostic Metrics Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Kích thước mẫu N</span>
              <span className="text-base font-bold text-slate-800 dark:text-slate-100">
                {result.diagnostics.sample_size}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Số nút (Nodes)</span>
              <span className="text-base font-bold text-slate-800 dark:text-slate-100">
                {result.diagnostics.n_nodes}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Số cạnh có hướng</span>
              <span className="text-base font-bold text-indigo-600 dark:text-indigo-400">
                {result.diagnostics.total_edges}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Mật độ mạng Density</span>
              <span className="text-base font-bold text-slate-800 dark:text-slate-100">
                {(result.diagnostics.graph_density * 100).toFixed(1)}%
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Điểm BIC Tối ưu</span>
              <span className="text-base font-bold text-slate-800 dark:text-slate-100">
                {result.diagnostics.final_bic_score.toFixed(1)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/40 border border-slate-200 dark:border-slate-600/50">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block">Tính phi chu trình (DAG)</span>
              <span className={`text-base font-bold ${result.diagnostics.is_acyclic ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500'}`}>
                {result.diagnostics.is_acyclic ? '✓ Hợp lệ (DAG)' : '✗ Chu trình'}
              </span>
            </div>
          </div>

          {/* SVG Graph Visualization */}
          {result.svg_visualization && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Sơ đồ Mạng Bayes DAG & Bảng Markov Blanket Độc lập Có điều kiện:
              </h4>
              <div
                className="overflow-x-auto p-4 bg-slate-900 rounded-xl border border-slate-800 flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Topological Node Roles Table */}
          {result.nodes && result.nodes.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Phân loại Vai trò Topo và Không gian Markov Blanket (Tập can thiệp độc lập):
              </h4>
              <div className="overflow-x-auto border border-slate-200 dark:border-slate-700 rounded-lg">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-50 dark:bg-slate-700/50 text-slate-700 dark:text-slate-200 font-semibold border-b border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="p-2.5">Biến số (Node)</th>
                      <th className="p-2.5">Vai trò Topo</th>
                      <th className="p-2.5 text-center">Bậc vào (In)</th>
                      <th className="p-2.5 text-center">Bậc ra (Out)</th>
                      <th className="p-2.5">Biến cha (Parents)</th>
                      <th className="p-2.5">Biến con (Children)</th>
                      <th className="p-2.5">Markov Blanket MB(X)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
                    {result.nodes.map((n, idx) => {
                      let roleBadge = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
                      if (n.topological_role === 'Root Cause') {
                        roleBadge = 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 font-bold';
                      } else if (n.topological_role === 'Target Sink') {
                        roleBadge = 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300 font-bold';
                      } else if (n.topological_role === 'Mediator') {
                        roleBadge = 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300 font-bold';
                      }

                      return (
                        <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-700/20">
                          <td className="p-2.5 font-medium text-slate-900 dark:text-white">
                            {n.label}
                          </td>
                          <td className="p-2.5">
                            <span className={`px-2 py-0.5 rounded text-[11px] ${roleBadge}`}>
                              {n.topological_role}
                            </span>
                          </td>
                          <td className="p-2.5 text-center font-mono">{n.in_degree}</td>
                          <td className="p-2.5 text-center font-mono">{n.out_degree}</td>
                          <td className="p-2.5">
                            {n.parents.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {n.parents.map((p, pIdx) => (
                                  <span key={pIdx} className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-[10px]">
                                    {p}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">Không có (Gốc)</span>
                            )}
                          </td>
                          <td className="p-2.5">
                            {n.children.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {n.children.map((c, cIdx) => (
                                  <span key={cIdx} className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-[10px]">
                                    {c}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">Không có (Đích)</span>
                            )}
                          </td>
                          <td className="p-2.5">
                            {n.markov_blanket.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {n.markov_blanket.map((mb, mbIdx) => (
                                  <span key={mbIdx} className="px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 text-[10px]">
                                    {mb}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">Độc lập hoàn toàn</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Directed Edges Table */}
          {result.edges && result.edges.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Danh sách Cạnh có Hướng & Hệ số Tác động Chuẩn hóa (&beta;):
              </h4>
              <div className="overflow-x-auto border border-slate-200 dark:border-slate-700 rounded-lg max-h-60">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-50 dark:bg-slate-700/50 text-slate-700 dark:text-slate-200 font-semibold border-b border-slate-200 dark:border-slate-700 sticky top-0">
                    <tr>
                      <th className="p-2.5">Nút nguồn (From)</th>
                      <th className="p-2.5">Chiều hướng</th>
                      <th className="p-2.5">Nút đích (To)</th>
                      <th className="p-2.5 text-right">Hệ số &beta; (Chuẩn hóa)</th>
                      <th className="p-2.5 text-center">Mức độ tương tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
                    {result.edges.map((e, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-700/20">
                        <td className="p-2.5 font-medium text-slate-900 dark:text-white">
                          {e.from_node}
                        </td>
                        <td className="p-2.5 text-indigo-500 font-bold">&rarr;</td>
                        <td className="p-2.5 font-medium text-slate-900 dark:text-white">
                          {e.to_node}
                        </td>
                        <td className="p-2.5 text-right font-mono font-semibold">
                          {e.standardized_path_coeff >= 0 ? '+' : ''}
                          {e.standardized_path_coeff.toFixed(4)}
                        </td>
                        <td className="p-2.5 text-center">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                            e.relationship_type.includes('Strong Positive')
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                              : e.relationship_type.includes('Moderate Positive')
                              ? 'bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-300'
                              : e.relationship_type.includes('Negative')
                              ? 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
                              : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                          }`}>
                            {e.relationship_type}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Narrative Callout */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Báo cáo Thuyết minh Chuẩn APA 7th (Methodological Narrative)
                </span>
                <button
                  type="button"
                  onClick={copyNarrative}
                  className="px-2.5 py-1 text-xs bg-white dark:bg-slate-700 hover:bg-slate-100 border border-slate-200 dark:border-slate-600 rounded text-slate-700 dark:text-slate-300 transition-colors"
                >
                  {copied ? '✓ Đã sao chép' : 'Sao chép APA'}
                </button>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed italic bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
