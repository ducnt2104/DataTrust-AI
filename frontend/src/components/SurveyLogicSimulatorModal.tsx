import React, { useEffect, useState, useMemo } from 'react';
import {
  X,
  GitBranch,
  Network,
  Share2,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Info,
  ShieldCheck,
  Layers,
  Eye,
  Play,
  RotateCcw,
  ArrowRight,
  Sparkles,
  Download,
  Check,
  RefreshCw,
  HelpCircle,
  Clock,
  ArrowDownRight
} from 'lucide-react';
import { api } from '../api/client';
import {
  SurveyLogicReport,
  LogicNode,
  LogicEdge,
  LogicIssue,
  LogicSamplePath,
  SurveySimulationReport
} from '../types/survey';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  surveyId: string;
  surveyTitle: string;
}

type TabType = 'graph' | 'diagnostics' | 'simulator' | 'paths';

export const SurveyLogicSimulatorModal: React.FC<Props> = ({
  isOpen,
  onClose,
  surveyId,
  surveyTitle
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('graph');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<SurveyLogicReport | null>(null);

  // Selected node for inspector
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Interactive Simulator state
  const [simAnswers, setSimAnswers] = useState<Record<string, any>>({});
  const [simResult, setSimResult] = useState<SurveySimulationReport | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  // Keyboard escape listener
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Load logic validation on mount or surveyId change
  useEffect(() => {
    if (!isOpen || !surveyId) return;
    loadLogicReport();
  }, [isOpen, surveyId]);

  const loadLogicReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.validateSurveyLogic(surveyId);
      setReport(data);
      if (data.nodes.length > 0 && !selectedNodeId) {
        setSelectedNodeId(data.nodes[0].id);
      }
      // Khởi tạo câu trả lời mô phỏng ban đầu
      runSimulation({});
    } catch (err: any) {
      setError(err.message || 'Không thể tải báo cáo logic rẽ nhánh.');
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async (answers: Record<string, any>) => {
    try {
      setSimulating(true);
      const res = await api.simulateSurveyLogic(surveyId, answers);
      setSimResult(res);
    } catch (err) {
      console.warn('Lỗi mô phỏng logic:', err);
    } finally {
      setSimulating(false);
    }
  };

  const handleAnswerChange = (questionId: string, value: any) => {
    const updated = { ...simAnswers, [questionId]: value };
    setSimAnswers(updated);
    runSimulation(updated);
  };

  const handleResetSimulation = () => {
    setSimAnswers({});
    runSimulation({});
  };

  const selectedNode = useMemo(() => {
    if (!report || !selectedNodeId) return null;
    return report.nodes.find(n => n.id === selectedNodeId) || report.nodes[0] || null;
  }, [report, selectedNodeId]);

  const handleExportJson = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DataTrust_Logic_Report_${surveyId.slice(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200">
      <div
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-6 py-4.5 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950 text-white flex items-center justify-between border-b border-indigo-900/40 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-600/30 border border-indigo-500/40 text-indigo-300">
              <Network className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-extrabold tracking-tight text-white">
                  Mô Phỏng & Kiểm Định Logic Rẽ Nhánh (DAG Simulator)
                </h2>
                {report && (
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase border ${
                      report.status === 'OPTIMAL'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : report.status === 'WARNING'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-red-500/20 text-red-300 border-red-500/40'
                    }`}
                  >
                    {report.status === 'OPTIMAL' ? (
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-3 h-3 text-amber-400" />
                    )}
                    {report.status} • {report.health_score}/100
                  </span>
                )}
              </div>
              <p className="text-xs text-indigo-200/80 truncate max-w-xl font-medium mt-0.5">
                Khảo sát: <span className="text-white font-semibold">{surveyTitle}</span> — Kiểm tra chu trình phụ thuộc & bẫy ngõ cụt
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            title="Đóng modal (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar & KPI Stats Bar */}
        {report && (
          <div className="px-6 py-3 bg-slate-50 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 shrink-0">
            {/* Tab Navigation */}
            <div className="flex items-center gap-1 bg-slate-200/60 p-0.5 rounded-xl text-xs font-semibold">
              <button
                type="button"
                onClick={() => setActiveTab('graph')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'graph'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Network className="w-3.5 h-3.5 text-indigo-600" />
                <span>Sơ Đồ Dòng Chảy DAG</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('diagnostics')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'diagnostics'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <AlertOctagon className="w-3.5 h-3.5 text-amber-600" />
                <span>
                  Chẩn Đoán Lỗi ({report.issues.length})
                </span>
                {report.issues.length > 0 && (
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                )}
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('simulator')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'simulator'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Play className="w-3.5 h-3.5 text-emerald-600" />
                <span>Chạy Thử Nghiệm Thực Tế</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('paths')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'paths'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <GitBranch className="w-3.5 h-3.5 text-violet-600" />
                <span>Lộ Trình Khả Dĩ ({report.topology.all_paths_count})</span>
              </button>
            </div>

            {/* Quick KPIs */}
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-slate-500 text-[11px]">Tổng câu:</span>
                <strong className="text-slate-900">{report.topology.node_count}</strong>
              </div>

              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-slate-500 text-[11px]">Điểm rẽ nhánh:</span>
                <strong className="text-indigo-600">{report.topology.branch_points_count}</strong>
              </div>

              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-slate-500 text-[11px]">Độ phức tạp McCabe:</span>
                <strong className="text-slate-900">M = {report.topology.cyclomatic_complexity}</strong>
              </div>

              <button
                onClick={loadLogicReport}
                className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:text-slate-900 transition-colors shadow-2xs"
                title="Quét lại toàn bộ hệ thống logic"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={handleExportJson}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs text-[11px] font-semibold"
                title="Xuất kết quả chẩn đoán logic dạng JSON"
              >
                <Download className="w-3.5 h-3.5 text-slate-500" />
                <span>JSON</span>
              </button>
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-hidden relative bg-slate-100 flex flex-col">
          {loading && (
            <div className="absolute inset-0 bg-white/80 backdrop-blur-2xs z-20 flex flex-col items-center justify-center p-6 text-center">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mb-3" />
              <h3 className="font-bold text-slate-800 text-sm">
                Đang xây dựng đồ thị DAG và kiểm định logic rẽ nhánh...
              </h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md">
                Thuật toán Tarjan 3-Coloring đang quét tìm chu trình lặp vô tận, bẫy ngõ cụt và tính toán các lộ trình trải nghiệm khảo sát.
              </p>
            </div>
          )}

          {error && (
            <div className="p-8 text-center m-auto max-w-md">
              <div className="p-3 rounded-full bg-red-100 text-red-600 w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <AlertOctagon className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base mb-1">Lỗi kiểm định logic</h3>
              <p className="text-xs text-slate-600 mb-4">{error}</p>
              <button
                onClick={loadLogicReport}
                className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition-all shadow-xs"
              >
                Thử lại
              </button>
            </div>
          )}

          {!loading && !error && report && (
            <>
              {/* TAB 1: Visual DAG Flow Graph */}
              {activeTab === 'graph' && (
                <div className="flex-1 overflow-auto p-4 sm:p-6 flex flex-col lg:flex-row gap-6">
                  {/* Left: Flowchart of Question Nodes */}
                  <div className="flex-1 bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4 overflow-auto max-h-[calc(92vh-220px)]">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <Network className="w-4 h-4 text-indigo-600" />
                          <span>Dòng Chảy Khảo Sát (Directed Flow)</span>
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Nhấp vào từng câu hỏi để kiểm tra các điều kiện rẽ nhánh và cạnh liên kết
                        </p>
                      </div>

                      <div className="flex items-center gap-3 text-[11px] font-medium text-slate-600">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" /> Tuyến tính
                        </span>
                        <span className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Rẽ nhánh
                        </span>
                        <span className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Lỗi chu trình
                        </span>
                      </div>
                    </div>

                    {/* Nodes Vertical Flow */}
                    <div className="space-y-3 pt-2">
                      {report.nodes.map((node: LogicNode, idx: number) => {
                        const isSelected = selectedNodeId === node.id;
                        const hasRules = node.rule_count > 0;
                        const isCycle = node.status === 'cycle';
                        const isUnreachable = node.status === 'unreachable';
                        const isInversion = node.status === 'inversion';

                        // Find incoming conditional edges
                        const incomingConditions = report.edges.filter(
                          e => e.target === node.id && e.type === 'conditional'
                        );

                        return (
                          <div key={node.id} className="relative">
                            {/* Connector line from previous question */}
                            {idx > 0 && (
                              <div className="flex items-center justify-center my-1.5">
                                <div className="h-4 w-0.5 bg-slate-300" />
                              </div>
                            )}

                            {/* Node Card */}
                            <div
                              onClick={() => setSelectedNodeId(node.id)}
                              className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start justify-between gap-4 ${
                                isSelected
                                  ? 'border-indigo-600 bg-indigo-50/40 ring-2 ring-indigo-200 shadow-sm'
                                  : isCycle
                                  ? 'border-red-400 bg-red-50/50 hover:bg-red-50'
                                  : isUnreachable
                                  ? 'border-amber-300 bg-amber-50/40 border-dashed hover:bg-amber-50'
                                  : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <div
                                  className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                                    isCycle
                                      ? 'bg-red-600 text-white'
                                      : isSelected
                                      ? 'bg-indigo-600 text-white'
                                      : 'bg-slate-100 text-slate-700'
                                  }`}
                                >
                                  {node.order_index + 1}
                                </div>

                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="text-xs font-bold text-slate-900 leading-snug">
                                      {node.title}
                                    </h4>
                                    {node.is_required && (
                                      <span className="text-[10px] text-red-500 font-bold">*</span>
                                    )}
                                  </div>

                                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                                    <span className="capitalize font-mono bg-slate-100 px-1.5 py-0.5 rounded text-[10px]">
                                      {node.question_type}
                                    </span>

                                    {hasRules && (
                                      <span className="inline-flex items-center gap-1 text-indigo-700 bg-indigo-100/70 px-2 py-0.5 rounded-full font-semibold text-[10px]">
                                        <GitBranch className="w-3 h-3" />
                                        {node.rule_count} quy tắc rẽ nhánh
                                      </span>
                                    )}

                                    {isCycle && (
                                      <span className="inline-flex items-center gap-1 text-red-700 bg-red-100 px-2 py-0.5 rounded-full font-bold text-[10px]">
                                        <AlertOctagon className="w-3 h-3" />
                                        Vòng lặp vô tận
                                      </span>
                                    )}

                                    {isUnreachable && (
                                      <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full font-bold text-[10px]">
                                        <AlertTriangle className="w-3 h-3" />
                                        Không tiếp cận được
                                      </span>
                                    )}

                                    {isInversion && (
                                      <span className="inline-flex items-center gap-1 text-orange-700 bg-orange-100 px-2 py-0.5 rounded-full font-bold text-[10px]">
                                        <ArrowRight className="w-3 h-3" />
                                        Nghịch đảo thời gian
                                      </span>
                                    )}
                                  </div>

                                  {/* Incoming Branch Condition pill */}
                                  {incomingConditions.map((edge, cIdx) => (
                                    <div
                                      key={cIdx}
                                      className="inline-flex items-center gap-1.5 text-[10px] text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg mt-1 font-medium"
                                    >
                                      <ArrowDownRight className="w-3 h-3 text-emerald-600 shrink-0" />
                                      <span>{edge.label}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              <div className="shrink-0 text-slate-400">
                                <ArrowRight className="w-4 h-4" />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Right: Selected Node Inspector Drawer */}
                  <div className="w-full lg:w-96 bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4 shrink-0 flex flex-col">
                    <div className="border-b border-slate-100 pb-3">
                      <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                        <Info className="w-4 h-4 text-indigo-600" />
                        <span>Chi Tiết Nút Khảo Sát</span>
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Thuộc tính logic và quy tắc điều kiện của câu hỏi được chọn
                      </p>
                    </div>

                    {selectedNode ? (
                      <div className="space-y-4 flex-1 overflow-auto">
                        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-indigo-700">
                              Câu hỏi #{selectedNode.order_index + 1}
                            </span>
                            <span className="text-[10px] bg-slate-200 px-2 py-0.5 rounded font-mono text-slate-700">
                              ID: {selectedNode.id.slice(0, 10)}...
                            </span>
                          </div>
                          <h4 className="text-sm font-extrabold text-slate-900 leading-snug">
                            {selectedNode.title}
                          </h4>
                          <div className="flex items-center gap-2 text-xs text-slate-600">
                            <span>Loại: <strong>{selectedNode.question_type}</strong></span>
                            <span>•</span>
                            <span>Bắt buộc: <strong>{selectedNode.is_required ? 'Có' : 'Không'}</strong></span>
                          </div>
                        </div>

                        {/* Rules Inspector */}
                        <div className="space-y-2">
                          <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                            Quy Tắc Rẽ Nhánh ({selectedNode.rules.length})
                          </label>

                          {selectedNode.rules.length === 0 ? (
                            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
                              Câu hỏi này không có điều kiện phụ thuộc. Luôn hiển thị theo thứ tự tuyến tính.
                            </div>
                          ) : (
                            <div className="space-y-2.5">
                              {selectedNode.rules.map((rule: any, rIdx: number) => {
                                const depNode = report.nodes.find(n => n.id === rule.depends_on_question_id);
                                return (
                                  <div
                                    key={rIdx}
                                    className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-200/70 text-xs text-slate-800 space-y-1.5"
                                  >
                                    <div className="flex items-center justify-between">
                                      <span className="font-bold text-indigo-900 text-[11px] uppercase tracking-wide">
                                        Quy tắc #{rIdx + 1} • {rule.action.toUpperCase()}
                                      </span>
                                      <span className="text-[10px] bg-indigo-200/60 text-indigo-900 px-1.5 py-0.5 rounded font-semibold">
                                        Toán tử: {rule.operator}
                                      </span>
                                    </div>

                                    <div className="text-xs leading-relaxed text-slate-700">
                                      Phụ thuộc vào: <strong className="text-slate-900">{depNode ? depNode.title : rule.depends_on_question_id}</strong>
                                    </div>

                                    <div className="text-[11px] text-slate-600">
                                      Giá trị kích hoạt: <code className="bg-white px-1.5 py-0.5 rounded border border-indigo-200 font-mono text-indigo-700 font-bold">"{rule.value}"</code>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>

                        {/* Health status summary */}
                        <div className="p-3.5 rounded-xl border text-xs space-y-1 bg-slate-50 border-slate-200">
                          <span className="font-bold text-slate-800 block text-[11px]">
                            Trạng thái toán học:
                          </span>
                          <p className="text-slate-600 leading-relaxed text-[11px]">
                            {selectedNode.status === 'cycle'
                              ? 'Nút nằm trong chu trình phụ thuộc vô tận (Cyclic Loop). Khảo sát sẽ bị treo.'
                              : selectedNode.status === 'unreachable'
                              ? 'Nút không thể tiếp cận được từ gốc khảo sát.'
                              : 'Nút hợp lệ, không có lỗi cấu trúc đồ thị.'}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center text-slate-400 text-xs text-center p-6">
                        Chọn một câu hỏi từ danh sách bên trái để xem thuộc tính.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: Diagnostics & Issues List */}
              {activeTab === 'diagnostics' && (
                <div className="flex-1 overflow-auto p-4 sm:p-6 space-y-4">
                  <div className="max-w-4xl mx-auto space-y-4">
                    {/* Summary Card */}
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-2">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-extrabold text-slate-900 text-base">
                          Đánh Giá Độ An Toàn & Chuẩn Mực Rẽ Nhánh
                        </h3>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {report.summary}
                      </p>
                    </div>

                    {/* Issues List */}
                    {report.issues.length === 0 ? (
                      <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
                        <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                          <Check className="w-6 h-6" />
                        </div>
                        <h4 className="font-bold text-slate-900 text-base">
                          Cấu trúc logic hoàn hảo 100%!
                        </h4>
                        <p className="text-xs text-slate-500 max-w-md mx-auto">
                          Không phát hiện vòng lặp vô tận (Cycles), câu hỏi mồ côi (Unreachable traps) hay tham chiếu gãy. Khảo sát sẵn sàng phát hành an toàn.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {report.issues.map((issue: LogicIssue, iIdx: number) => {
                          const isCrit = issue.severity === 'CRITICAL';
                          const isHigh = issue.severity === 'HIGH';

                          return (
                            <div
                              key={iIdx}
                              className={`p-5 rounded-2xl border shadow-xs space-y-3 transition-all ${
                                isCrit
                                  ? 'bg-red-50/70 border-red-300'
                                  : isHigh
                                  ? 'bg-amber-50/70 border-amber-300'
                                  : 'bg-white border-slate-200'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex items-center gap-2.5">
                                  <div
                                    className={`p-2 rounded-xl text-white ${
                                      isCrit ? 'bg-red-600' : isHigh ? 'bg-amber-600' : 'bg-slate-700'
                                    }`}
                                  >
                                    <AlertOctagon className="w-4 h-4" />
                                  </div>
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span
                                        className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                                          isCrit
                                            ? 'bg-red-200 text-red-900'
                                            : isHigh
                                            ? 'bg-amber-200 text-amber-900'
                                            : 'bg-slate-200 text-slate-800'
                                        }`}
                                      >
                                        {issue.severity} • {issue.type}
                                      </span>
                                    </div>
                                    <h4 className="font-bold text-slate-900 text-sm mt-0.5">
                                      {issue.title}
                                    </h4>
                                  </div>
                                </div>
                              </div>

                              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                                {issue.description}
                              </p>

                              <div className="p-3 rounded-xl bg-white/80 border border-slate-200 text-xs text-slate-800 flex items-start gap-2">
                                <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                                <div>
                                  <strong className="text-indigo-950 font-bold block">
                                    Khuyến nghị khắc phục chuẩn hóa:
                                  </strong>
                                  <span className="text-slate-600 mt-0.5 block">
                                    {issue.recommendation}
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 3: Interactive Test Runner */}
              {activeTab === 'simulator' && (
                <div className="flex-1 overflow-auto p-4 sm:p-6 flex flex-col lg:flex-row gap-6">
                  {/* Left: Input Simulated Answers */}
                  <div className="w-full lg:w-1/2 bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4 overflow-auto max-h-[calc(92vh-220px)]">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <Play className="w-4 h-4 text-emerald-600" />
                          <span>Mô Phỏng Trả Lời Trực Tiếp</span>
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Chọn các phương án trả lời để kiểm chứng trải nghiệm người dùng thực tế
                        </p>
                      </div>

                      <button
                        onClick={handleResetSimulation}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:text-slate-900 text-xs font-semibold shadow-2xs"
                        title="Xóa toàn bộ câu trả lời mô phỏng"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Đặt lại</span>
                      </button>
                    </div>

                    <div className="space-y-4 pt-1">
                      {report.nodes.map((node: LogicNode) => {
                        const isHiddenInSim = simResult?.hidden_questions.includes(node.id);
                        const currVal = simAnswers[node.id] || '';

                        return (
                          <div
                            key={node.id}
                            className={`p-4 rounded-xl border transition-all ${
                              isHiddenInSim
                                ? 'bg-slate-50 border-slate-200 opacity-50'
                                : 'bg-white border-slate-200/90 shadow-2xs'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2 mb-2">
                              <span className="text-xs font-bold text-slate-900">
                                #{node.order_index + 1}. {node.title}
                              </span>
                              {isHiddenInSim && (
                                <span className="text-[10px] font-bold text-slate-500 bg-slate-200 px-2 py-0.5 rounded-full">
                                  ĐÃ BỊ ẨN
                                </span>
                              )}
                            </div>

                            {/* Options Input */}
                            <div className="space-y-1.5">
                              <input
                                type="text"
                                placeholder="Nhập câu trả lời giả định..."
                                value={currVal}
                                onChange={(e) => handleAnswerChange(node.id, e.target.value)}
                                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500 font-medium text-slate-800"
                              />

                              {/* Quick click suggestions for known rule values */}
                              {node.rules.length > 0 && (
                                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                                  <span className="text-[10px] text-slate-400">Gợi ý thử:</span>
                                  {node.rules.map((r: any, idx: number) => (
                                    <button
                                      key={idx}
                                      type="button"
                                      onClick={() => handleAnswerChange(r.depends_on_question_id, r.value)}
                                      className="text-[10px] bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-2 py-0.5 rounded border border-indigo-200 font-semibold"
                                    >
                                      Đặt Q#{r.depends_on_question_id.slice(0, 4)} = "{r.value}"
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Right: Real-time Simulation Output */}
                  <div className="w-full lg:w-1/2 bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4 overflow-auto max-h-[calc(92vh-220px)] flex flex-col">
                    <div className="border-b border-slate-100 pb-3">
                      <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-indigo-600" />
                        <span>Kết Quả Kiểm Thử Luồng Khảo Sát</span>
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Phân tích trực tiếp các câu hỏi xuất hiện và lý do ẩn giấu
                      </p>
                    </div>

                    {simResult && (
                      <div className="space-y-4 flex-1">
                        {/* Gauge Cards */}
                        <div className="grid grid-cols-3 gap-3">
                          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-center">
                            <span className="text-[10px] text-emerald-700 font-bold block uppercase">
                              Hiển thị
                            </span>
                            <strong className="text-lg font-extrabold text-emerald-950">
                              {simResult.visible_count}
                            </strong>
                          </div>

                          <div className="p-3 rounded-xl bg-slate-100 border border-slate-200 text-center">
                            <span className="text-[10px] text-slate-600 font-bold block uppercase">
                              Bị Ẩn / Bỏ qua
                            </span>
                            <strong className="text-lg font-extrabold text-slate-800">
                              {simResult.hidden_count}
                            </strong>
                          </div>

                          <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-center">
                            <span className="text-[10px] text-indigo-700 font-bold block uppercase">
                              Tỷ lệ trải nghiệm
                            </span>
                            <strong className="text-lg font-extrabold text-indigo-950">
                              {simResult.completion_ratio}%
                            </strong>
                          </div>
                        </div>

                        {/* Breadcrumbs Route */}
                        <div className="p-4 rounded-xl bg-slate-900 text-white space-y-2">
                          <span className="text-[11px] font-bold text-indigo-300 block uppercase tracking-wider">
                            Lộ Trình Thực Tế Người Dùng Trải Qua:
                          </span>
                          <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono font-bold">
                            {simResult.visible_questions.map((qid, idx) => {
                              const qNode = report.nodes.find(n => n.id === qid);
                              return (
                                <React.Fragment key={qid}>
                                  <span className="px-2 py-1 rounded bg-indigo-600/40 border border-indigo-400/40 text-indigo-100 text-[11px]">
                                    #{qNode ? qNode.order_index + 1 : idx + 1}
                                  </span>
                                  {idx < simResult.visible_questions.length - 1 && (
                                    <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                                  )}
                                </React.Fragment>
                              );
                            })}
                          </div>
                        </div>

                        {/* Skipped Reasons list */}
                        {simResult.hidden_count > 0 && (
                          <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                              Chi Tiết Các Câu Hỏi Bị Ẩn & Lý Do:
                            </label>

                            <div className="space-y-2">
                              {simResult.hidden_questions.map((hid) => {
                                const hNode = report.nodes.find(n => n.id === hid);
                                const reason = simResult.skipped_reasons[hid] || 'Không thỏa mãn điều kiện hiển thị.';

                                return (
                                  <div
                                    key={hid}
                                    className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1"
                                  >
                                    <div className="flex items-center gap-2">
                                      <span className="w-2 h-2 rounded-full bg-slate-400" />
                                      <strong className="text-slate-900">
                                        #{hNode ? hNode.order_index + 1 : '?'}: {hNode ? hNode.title : hid}
                                      </strong>
                                    </div>
                                    <p className="text-slate-600 pl-4 text-[11px]">
                                      {reason}
                                    </p>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 4: All Valid Paths Enumeration */}
              {activeTab === 'paths' && (
                <div className="flex-1 overflow-auto p-4 sm:p-6 space-y-4">
                  <div className="max-w-4xl mx-auto space-y-4">
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-2">
                      <div className="flex items-center gap-2">
                        <GitBranch className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-extrabold text-slate-900 text-base">
                          Danh Sách Các Kịch Bản Khảo Sát Khả Dĩ
                        </h3>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        Hệ thống tự động duyệt cây phân nhánh để tính toán mọi phương án lộ trình mà các nhóm đối tượng người trả lời khác nhau có thể trải qua.
                      </p>
                    </div>

                    <div className="space-y-3">
                      {report.paths.map((p: LogicSamplePath, pIdx: number) => (
                        <div
                          key={p.path_id}
                          className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-3"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-center gap-2.5">
                              <span className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center font-bold text-xs text-indigo-700">
                                {pIdx + 1}
                              </span>
                              <div>
                                <h4 className="font-bold text-slate-900 text-sm">
                                  {p.name}
                                </h4>
                                <span className="text-[11px] text-slate-500 font-medium">
                                  {p.description}
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center gap-2 text-xs">
                              <span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-800 font-semibold text-[11px]">
                                {p.length} câu hỏi ({p.completion_percentage}%)
                              </span>
                            </div>
                          </div>

                          {/* Path sequence breadcrumb */}
                          <div className="flex flex-wrap items-center gap-1.5 p-3 rounded-xl bg-slate-50 border border-slate-200/70 text-xs">
                            {p.question_ids.map((qid, qIdx) => {
                              const qNode = report.nodes.find(n => n.id === qid);
                              return (
                                <React.Fragment key={qid}>
                                  <span className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-800 font-medium text-[11px]">
                                    #{qNode ? qNode.order_index + 1 : qIdx + 1}: {qNode ? qNode.title.slice(0, 16) + '...' : qid}
                                  </span>
                                  {qIdx < p.question_ids.length - 1 && (
                                    <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                                  )}
                                </React.Fragment>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-white border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>
              Chuẩn mực thiết kế: Don Dillman Tailored Design & AAPOR Standard Questionnaire Verification.
            </span>
          </div>

          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-all shadow-xs"
          >
            Đóng Trình Mô Phỏng
          </button>
        </div>
      </div>
    </div>
  );
};
