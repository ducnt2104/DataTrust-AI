import React, { useState, useEffect } from 'react';
import {
  Share2, Sparkles, CheckCircle2, AlertTriangle, ArrowRight,
  TrendingUp, Activity, Copy, Check, RefreshCw, BarChart2,
  BookOpen, ShieldCheck, Zap, Sliders, Filter, Network, Radio
} from 'lucide-react';
import { api } from '../api/client';
import { QuestionStats, PsychometricNetworkResult } from '../types/survey';

interface Props {
  surveyId: string;
  questions: QuestionStats[];
}

export const PsychometricNetworkCard: React.FC<Props> = ({ surveyId, questions }) => {
  // Lọc câu hỏi định lượng cho mạng lưới
  const scaleCandidateQuestions = questions.filter((q) =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale'].includes(q.question_type) ||
    (q.stats_summary && (q.stats_summary.count ?? 0) > 0)
  );

  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [threshold, setThreshold] = useState<number>(0.05);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [result, setResult] = useState<PsychometricNetworkResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);
  const [hoveredEdge, setHoveredEdge] = useState<any | null>(null);

  // Mặc định chọn tất cả câu hỏi định lượng (tối đa 10)
  useEffect(() => {
    if (scaleCandidateQuestions.length >= 3 && selectedQuestions.length === 0) {
      setSelectedQuestions(scaleCandidateQuestions.slice(0, 8).map(q => q.question_id));
    }
  }, [questions]);

  const toggleQuestion = (qid: string) => {
    if (selectedQuestions.includes(qid)) {
      if (selectedQuestions.length <= 3) {
        setError('Mạng lưới cần tối thiểu 3 câu hỏi định lượng.');
        return;
      }
      setSelectedQuestions(selectedQuestions.filter(id => id !== qid));
    } else {
      setSelectedQuestions([...selectedQuestions, qid]);
    }
  };

  const handleRunAnalysis = async () => {
    if (selectedQuestions.length < 3) {
      setError('Cần chọn tối thiểu 3 câu hỏi định lượng để thiết lập mạng lưới đồ thị.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.runPsychometricNetwork(surveyId, {
        question_ids: selectedQuestions,
        regularization_threshold: threshold,
        scope
      });

      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể thực hiện phân tích mạng lưới tâm lý học.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi khi gọi API phân tích mạng lưới GGM.');
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
            <div className="p-2.5 bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400 rounded-xl">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Mạng Lưới Tâm Lý Học Đo Lường (Psychometric Network) & Mô Hình Đồ Thị GGM
                <span className="text-xs px-2.5 py-0.5 font-medium rounded-full bg-cyan-100 dark:bg-cyan-900/60 text-cyan-700 dark:text-cyan-300">
                  Borsboom & Cramer (2013) & Epskamp et al. (2018)
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Mô hình hóa các mục khảo sát như một hệ thống mạng lưới tương tác động qua tương quan riêng phần (Partial Correlation), bố trí lực lò xo Fruchterman-Reingold và đánh giá chỉ số trung tâm (Node Centrality).
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start lg:self-auto">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="px-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/20"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Chỉ phản hồi chuẩn hóa (Verified Clean)</option>
          </select>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-4 py-1.5 text-xs font-medium text-white bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <PlayIcon className="w-3.5 h-3.5" />}
            Vẽ Mạng Lưới GGM
          </button>
        </div>
      </div>

      {/* Control Configuration Area */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-5 border-b border-slate-100 dark:border-slate-800">
        <div className="md:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-500" />
              Chọn Các Câu Hỏi Thang Đo Tham Gia Mạng Lưới (Nodes)
            </label>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Đã chọn {selectedQuestions.length} / {scaleCandidateQuestions.length} câu hỏi
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {scaleCandidateQuestions.map((q) => {
              const isSelected = selectedQuestions.includes(q.question_id);
              return (
                <button
                  key={q.question_id}
                  type="button"
                  onClick={() => toggleQuestion(q.question_id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-cyan-600 text-white shadow-sm font-semibold'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3" />}
                  {q.question_title}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Ngưỡng Lọc Cạnh Rời Rạc (|r_partial|)
            </label>
            <span className="text-xs font-mono font-medium text-cyan-600 dark:text-cyan-400">
              |r| &ge; {threshold.toFixed(2)}
            </span>
          </div>
          <input
            type="range"
            min="0.00"
            max="0.25"
            step="0.01"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-full accent-cyan-600 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>0.00 (Tất cả cạnh)</span>
            <span>0.05 (Khuyến nghị Epskamp)</span>
            <span>0.25 (Cạnh rất mạnh)</span>
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
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Số Nút Mạng Lưới (Nodes P)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {result.num_nodes}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  / N = {result.sample_size} mẫu
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Số cạnh có thể: {result.possible_edges}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-cyan-50/50 dark:bg-cyan-950/30 border border-cyan-100 dark:border-cyan-900/40">
              <span className="text-xs font-medium text-cyan-700 dark:text-cyan-300 block mb-1">
                Số Cạnh Hoạt Động (Active Edges E)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-cyan-600 dark:text-cyan-400">
                  {result.num_edges}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-cyan-100 dark:bg-cyan-900 text-cyan-700 dark:text-cyan-300">
                  {result.density_percent}% mật độ
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Độ thưa thớt (Sparsity): {result.sparsity_percent}%
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Trọng Số Cạnh TB (|w_ij|)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-800 dark:text-slate-200">
                  {result.mean_weight?.toFixed(3)}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  (Partial r)
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Kiểm định tương quan riêng phần
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                Nút Trung Tâm Cốt Lõi (Core Node)
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400 truncate max-w-[180px]">
                  {result.most_central_node}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Cường độ liên kết (Strength) cao nhất
              </p>
            </div>
          </div>

          {/* Force-Directed SVG Network Graph */}
          <div className="p-5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-800/30">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <Share2 className="w-4 h-4 text-cyan-500" />
                Đồ Thị Không Gian Vector Mạng Lưới (Fruchterman-Reingold Force-Directed Layout)
              </h4>
              <div className="flex items-center gap-4 text-[11px]">
                <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                  <span className="w-3 h-1 rounded bg-emerald-500 inline-block" /> Tương quan riêng phần dương (+)
                </span>
                <span className="flex items-center gap-1.5 text-rose-600 dark:text-rose-400">
                  <span className="w-3 h-1 rounded bg-rose-500 inline-block" /> Tương quan riêng phần âm (-)
                </span>
              </div>
            </div>

            {/* SVG Visualizer Canvas */}
            <div className="relative w-full h-96 flex items-center justify-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-inner">
              <svg viewBox="0 0 500 360" className="w-full h-full">
                {/* Edges */}
                {result.edges?.map((edge, idx) => {
                  const srcNode = result.nodes?.find(n => n.id === edge.source);
                  const tgtNode = result.nodes?.find(n => n.id === edge.target);
                  if (!srcNode || !tgtNode) return null;

                  const isPositive = edge.edge_type === 'positive';
                  const strokeWidth = Math.max(1.0, Math.min(6.0, edge.abs_weight * 8.0));
                  const strokeColor = isPositive ? '#10b981' : '#f43f5e';
                  const opacity = Math.max(0.3, Math.min(0.9, edge.abs_weight * 1.5));

                  return (
                    <line
                      key={idx}
                      x1={srcNode.x}
                      y1={srcNode.y}
                      x2={tgtNode.x}
                      y2={tgtNode.y}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      strokeOpacity={opacity}
                      className="cursor-pointer transition-all hover:stroke-amber-400"
                      onMouseEnter={() => setHoveredEdge(edge)}
                      onMouseLeave={() => setHoveredEdge(null)}
                    />
                  );
                })}

                {/* Nodes */}
                {result.nodes?.map((node) => {
                  // Kích thước vòng tròn tỷ lệ với Strength
                  const r = Math.max(14, Math.min(26, 16 + (node.z_strength || 0) * 3));
                  return (
                    <g key={node.id} className="cursor-pointer group">
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={r}
                        className="fill-cyan-600 dark:fill-cyan-500 stroke-white dark:stroke-slate-900 transition-transform group-hover:scale-110"
                        strokeWidth="2.5"
                      />
                      {/* Node index */}
                      <text
                        x={node.x}
                        y={node.y + 4}
                        textAnchor="middle"
                        fontSize="11"
                        className="fill-white font-bold font-mono pointer-events-none select-none"
                      >
                        {node.id + 1}
                      </text>
                      {/* Node label */}
                      <text
                        x={node.x}
                        y={node.y + r + 13}
                        textAnchor="middle"
                        fontSize="10"
                        className="fill-slate-700 dark:fill-slate-300 font-semibold font-sans pointer-events-none select-none"
                      >
                        {node.name.length > 20 ? node.name.slice(0, 18) + '...' : node.name}
                      </text>
                    </g>
                  );
                })}
              </svg>

              {/* Edge Hover Inspector Tooltip */}
              {hoveredEdge && (
                <div className="absolute bottom-3 left-3 p-3 bg-slate-900/90 text-white rounded-lg text-xs shadow-lg backdrop-blur-sm pointer-events-none">
                  <div className="font-semibold text-cyan-300">
                    {hoveredEdge.source_name} ↔ {hoveredEdge.target_name}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span>Tương quan riêng phần (r_partial):</span>
                    <span className="font-mono font-bold text-amber-300">
                      {hoveredEdge.weight > 0 ? '+' : ''}{hoveredEdge.weight}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Node Centrality Table */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-3.5 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-500" />
                Bảng Chỉ Số Trung Tâm Mạng Lưới (Node Centrality Metrics; Robinaugh et al. 2016)
              </h4>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                Giá trị z-score chuẩn hóa trung bình = 0.0, độ lệch chuẩn = 1.0
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/50 dark:bg-slate-800/40 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 font-semibold">
                  <tr>
                    <th className="py-2.5 px-4 w-12 text-center">Nút</th>
                    <th className="py-2.5 px-4">Tên Câu Hỏi Khảo Sát</th>
                    <th className="py-2.5 px-3 text-right">Strength (Cường độ)</th>
                    <th className="py-2.5 px-3 text-right">z(Strength)</th>
                    <th className="py-2.5 px-3 text-right">Expected Influence</th>
                    <th className="py-2.5 px-3 text-right">Closeness</th>
                    <th className="py-2.5 px-3 text-right">Betweenness</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                  {result.nodes?.map((node) => {
                    const isCentral = node.name === result.most_central_node;
                    return (
                      <tr
                        key={node.id}
                        className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors ${
                          isCentral ? 'bg-cyan-50/30 dark:bg-cyan-950/20' : ''
                        }`}
                      >
                        <td className="py-2.5 px-4 text-center font-bold text-cyan-600 dark:text-cyan-400">
                          {node.id + 1}
                        </td>
                        <td className="py-2.5 px-4 font-sans font-medium text-slate-800 dark:text-slate-200 flex items-center gap-2">
                          <span>{node.name}</span>
                          {isCentral && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                              Core Node
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-800 dark:text-slate-200">
                          {node.strength.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-cyan-600 dark:text-cyan-400">
                          {node.z_strength > 0 ? '+' : ''}{node.z_strength.toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                          {node.expected_influence.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                          {node.closeness.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">
                          {node.betweenness.toFixed(1)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* APA 7th Edition Narrative Summary */}
          {result.apa_narrative && (
            <div className="p-5 rounded-xl border border-cyan-100 dark:border-cyan-900/50 bg-cyan-50/30 dark:bg-cyan-950/20">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                  <h4 className="text-xs font-bold text-cyan-900 dark:text-cyan-200">
                    Báo Cáo Thuyết Minh Chuẩn APA 7th Edition & Đánh Giá Mạng Lưới Tâm Lý Học
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={() => copyToClipboard(result.apa_narrative!)}
                  className="px-2.5 py-1 text-xs rounded-md border border-cyan-200 dark:border-cyan-800 bg-white dark:bg-slate-900 text-cyan-700 dark:text-cyan-300 hover:bg-cyan-50 dark:hover:bg-slate-800 flex items-center gap-1 transition-colors"
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

function PlayIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  );
}
