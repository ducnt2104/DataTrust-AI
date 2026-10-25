import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Award,
  CheckCircle2,
  Copy,
  GitBranch,
  GitFork,
  Info,
  Layers,
  Network,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2
} from 'lucide-react';
import { api } from '../api/client';
import {
  SEMAnalysisResult,
  SEMPathSpec
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface SEMPathAnalysisCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const SEMPathAnalysisCard: React.FC<SEMPathAnalysisCardProps> = ({
  surveyId,
  questions
}) => {
  const [paths, setPaths] = useState<SEMPathSpec[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SEMAnalysisResult | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'diagram' | 'paths' | 'effects' | 'equations' | 'fit'>('diagram');

  // Lọc các câu hỏi có thể dùng làm biến số liên tục / rating / numeric
  const eligibleQuestions = questions.filter(
    (q) => ['rating', 'linear_scale', 'nps', 'number', 'single_choice', 'text'].includes(q.question_type)
  );

  const handleAddPath = () => {
    if (!selectedSource || !selectedTarget) {
      setError('Vui lòng chọn cả biến nguồn (nguyên nhân) và biến đích (kết quả).');
      return;
    }
    if (selectedSource === selectedTarget) {
      setError('Biến nguồn và biến đích không thể trùng nhau (tránh vòng lặp tự hồi quy).');
      return;
    }
    const exists = paths.some(
      (p) => p.source === selectedSource && p.target === selectedTarget
    );
    if (exists) {
      setError('Đường dẫn này đã được thêm trước đó.');
      return;
    }
    setError(null);
    setPaths([...paths, { source: selectedSource, target: selectedTarget }]);
    setSelectedSource('');
    setSelectedTarget('');
  };

  const handleRemovePath = (index: number) => {
    const updated = paths.filter((_, idx) => idx !== index);
    setPaths(updated);
  };

  const handleApplyPreset = () => {
    if (eligibleQuestions.length < 3) {
      setError('Cần ít nhất 3 câu hỏi để áp dụng mẫu Trung gian Cổ điển (X → M → Y).');
      return;
    }
    setError(null);
    const q0 = eligibleQuestions[0].id;
    const q1 = eligibleQuestions[1].id;
    const q2 = eligibleQuestions[2].id;
    setPaths([
      { source: q0, target: q1 },
      { source: q1, target: q2 },
      { source: q0, target: q2 }
    ]);
  };

  const handleClearPaths = () => {
    setPaths([]);
    setError(null);
  };

  const handleRunAnalysis = async () => {
    if (paths.length === 0) {
      setError('Vui lòng thiết lập ít nhất 1 đường dẫn cấu trúc.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.runSEMAnalysis(surveyId, {
        paths,
        scope
      });
      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể ước lượng mô hình SEM với cấu hình hiện tại.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng mô hình SEM.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyApa = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopiedApa(true);
      setTimeout(() => setCopiedApa(false), 2000);
    }
  };

  const getQuestionTitle = (qid: string) => {
    const q = questions.find((item) => item.id === qid);
    return q ? q.title : qid;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
      {/* Header */}
      <div className="p-6 bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-700/60 rounded-lg border border-indigo-500/40">
              <Network className="w-6 h-6 text-indigo-200" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-xl font-bold tracking-tight">
                  Mô hình Phương trình Cấu trúc & Đường dẫn (SEM)
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                  Wright 1934 • Jöreskog 1970
                </span>
              </div>
              <p className="text-sm text-indigo-200/80 mt-1">
                Phân tích đường dẫn hồi quy đồng thời, tác động trực tiếp/gián tiếp (Mediation) và chỉ số phù hợp (CFI, TLI, RMSEA, SRMR).
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex bg-indigo-950/60 p-1 rounded-lg border border-indigo-700/50 text-xs">
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  scope === 'all'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-indigo-300 hover:text-white'
                }`}
              >
                Tất cả mẫu
              </button>
              <button
                type="button"
                onClick={() => setScope('verified_clean')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  scope === 'verified_clean'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-indigo-300 hover:text-white'
                }`}
              >
                Dữ liệu sạch
              </button>
            </div>

            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={loading || paths.length === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white font-medium text-sm rounded-lg transition shadow-sm"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Đang ước lượng…' : 'Ước lượng SEM'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Path Builder Controls */}
      <div className="p-6 border-b border-slate-200 bg-slate-50/70">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
          <div className="flex items-center space-x-2 text-sm font-semibold text-slate-800">
            <GitFork className="w-4 h-4 text-indigo-600" />
            <span>Thiết lập Đường dẫn Cấu trúc (Structural Path Specification)</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handleApplyPreset}
              className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-md transition flex items-center space-x-1"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Áp dụng mẫu X → M → Y (Mediation)</span>
            </button>
            {paths.length > 0 && (
              <button
                type="button"
                onClick={handleClearPaths}
                className="px-3 py-1.5 text-xs font-medium text-rose-600 hover:text-rose-700 hover:bg-rose-50 border border-rose-200 rounded-md transition"
              >
                Xóa tất cả
              </button>
            )}
          </div>
        </div>

        {/* Add path form */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
          <div className="md:col-span-5">
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Biến Nguồn (Source / Dự báo)
            </label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white py-2 px-3"
            >
              <option value="">-- Chọn biến nguồn --</option>
              {eligibleQuestions.map((q) => (
                <option key={`src-${q.id}`} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-1 flex items-center justify-center py-2 text-slate-400">
            <ArrowRight className="w-5 h-5 hidden md:block" />
          </div>

          <div className="md:col-span-5">
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Biến Đích (Target / Kết quả nội sinh)
            </label>
            <select
              value={selectedTarget}
              onChange={(e) => setSelectedTarget(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white py-2 px-3"
            >
              <option value="">-- Chọn biến kết quả --</option>
              {eligibleQuestions.map((q) => (
                <option key={`tgt-${q.id}`} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-1">
            <button
              type="button"
              onClick={handleAddPath}
              className="w-full flex items-center justify-center py-2 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition"
              title="Thêm đường dẫn"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Active paths tags */}
        {paths.length > 0 ? (
          <div className="mt-4 pt-3 border-t border-slate-200/80">
            <span className="text-xs font-medium text-slate-500 block mb-2">
              Các đường dẫn đang hoạt động ({paths.length}):
            </span>
            <div className="flex flex-wrap gap-2">
              {paths.map((p, idx) => (
                <span
                  key={`${p.source}-${p.target}-${idx}`}
                  className="inline-flex items-center space-x-1.5 px-3 py-1 bg-white border border-indigo-200 rounded-full text-xs font-medium text-indigo-900 shadow-2xs"
                >
                  <span className="text-slate-700">{getQuestionTitle(p.source)}</span>
                  <ArrowRight className="w-3 h-3 text-indigo-500" />
                  <span className="text-indigo-800 font-semibold">{getQuestionTitle(p.target)}</span>
                  <button
                    type="button"
                    onClick={() => handleRemovePath(idx)}
                    className="ml-1 text-slate-400 hover:text-rose-600 transition"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic mt-3">
            Chưa có đường dẫn nào. Hãy chọn biến nguồn, biến đích và bấm dấu (+) hoặc áp dụng mẫu có sẵn.
          </p>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 mx-6 mt-6 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg flex items-start space-x-3 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Thông báo từ động cơ SEM:</span> {error}
          </div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="p-6 space-y-6">
          {/* Fit Indices Banner */}
          {result.fit_indices && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="text-xs text-slate-500 block font-medium">χ² (df; p)</span>
                <span className="text-sm font-bold text-slate-800">
                  {result.fit_indices.chi_square.toFixed(2)}{' '}
                  <span className="text-xs font-normal text-slate-500">
                    ({result.fit_indices.df}; p={result.fit_indices.p_value.toFixed(3)})
                  </span>
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">CFI</span>
                  <span
                    className={`text-2xs px-1.5 py-0.5 rounded font-bold ${
                      result.fit_indices.cfi >= 0.95
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {result.fit_indices.cfi >= 0.95 ? '≥ 0.95' : '< 0.95'}
                  </span>
                </div>
                <span className="text-base font-bold text-slate-900 mt-1 block">
                  {result.fit_indices.cfi.toFixed(3)}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">TLI</span>
                  <span
                    className={`text-2xs px-1.5 py-0.5 rounded font-bold ${
                      result.fit_indices.tli >= 0.95
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {result.fit_indices.tli >= 0.95 ? '≥ 0.95' : '< 0.95'}
                  </span>
                </div>
                <span className="text-base font-bold text-slate-900 mt-1 block">
                  {result.fit_indices.tli.toFixed(3)}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">RMSEA</span>
                  <span
                    className={`text-2xs px-1.5 py-0.5 rounded font-bold ${
                      result.fit_indices.rmsea <= 0.06
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {result.fit_indices.rmsea <= 0.06 ? '≤ 0.06' : '> 0.06'}
                  </span>
                </div>
                <span className="text-base font-bold text-slate-900 mt-1 block">
                  {result.fit_indices.rmsea.toFixed(3)}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">SRMR</span>
                  <span
                    className={`text-2xs px-1.5 py-0.5 rounded font-bold ${
                      result.fit_indices.srmr <= 0.08
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {result.fit_indices.srmr <= 0.08 ? '≤ 0.08' : '> 0.08'}
                  </span>
                </div>
                <span className="text-base font-bold text-slate-900 mt-1 block">
                  {result.fit_indices.srmr.toFixed(3)}
                </span>
              </div>

              <div className="p-3 bg-indigo-50/70 rounded-lg border border-indigo-200 flex flex-col justify-center">
                <span className="text-2xs text-indigo-700 font-semibold uppercase tracking-wider block">
                  Đánh giá độ phù hợp
                </span>
                <span className="text-xs font-bold text-indigo-900 mt-0.5 line-clamp-2">
                  {result.fit_indices.fit_assessment}
                </span>
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="border-b border-slate-200 flex space-x-6 text-sm font-medium">
            <button
              type="button"
              onClick={() => setActiveTab('diagram')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'diagram'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Network className="w-4 h-4" />
              <span>Sơ đồ Đường dẫn (Path Diagram)</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('paths')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'paths'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <GitBranch className="w-4 h-4" />
              <span>Hệ số Đường dẫn ({result.paths?.length || 0})</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('effects')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'effects'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Phân rã Tác động & Trung gian</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('equations')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'equations'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Phương trình R² ({result.equations?.length || 0})</span>
            </button>
          </div>

          {/* Tab Content: Vector SVG Diagram */}
          {activeTab === 'diagram' && result.svg_path_diagram && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Biểu đồ trực quan hóa đường dẫn cấu trúc (Structural DAG with R² & β):</span>
                <span className="flex items-center space-x-3">
                  <span className="flex items-center space-x-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-600 inline-block"></span>
                    <span>Ý nghĩa thống kê (p &lt; .05)</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block"></span>
                    <span>Không có ý nghĩa</span>
                  </span>
                </span>
              </div>
              <div
                className="w-full bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs p-2 flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_path_diagram }}
              />
            </div>
          )}

          {/* Tab Content: Path Parameters Table */}
          {activeTab === 'paths' && result.paths && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold text-slate-600">Đường dẫn</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">B (chưa chuẩn hóa)</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">SE</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">z-stat</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">p-value</th>
                    <th className="px-3 py-2 text-right font-semibold text-indigo-700">β (chuẩn hóa)</th>
                    <th className="px-3 py-2 text-center font-semibold text-slate-600">95% CI</th>
                    <th className="px-3 py-2 text-center font-semibold text-slate-600">Ý nghĩa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.paths.map((p, idx) => (
                    <tr key={`p-param-${idx}`} className="hover:bg-slate-50/80">
                      <td className="px-3 py-2.5 font-medium text-slate-900 flex items-center space-x-1.5">
                        <span className="text-slate-700">{p.source_label}</span>
                        <ArrowRight className="w-3 h-3 text-slate-400" />
                        <span className="text-indigo-900 font-semibold">{p.target_label}</span>
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-700">{p.unstandardized.toFixed(4)}</td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-500">{p.standard_error.toFixed(4)}</td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-700">{p.z_value.toFixed(3)}</td>
                      <td className="px-3 py-2.5 text-right font-mono font-medium">
                        <span className={p.p_value < 0.05 ? 'text-emerald-700 font-bold' : 'text-slate-500'}>
                          {p.p_value < 0.001 ? '< .001' : p.p_value.toFixed(4)}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-bold text-indigo-700">
                        {p.standardized.toFixed(4)}
                      </td>
                      <td className="px-3 py-2.5 text-center font-mono text-slate-500">
                        [{p.ci_95_lower.toFixed(3)}, {p.ci_95_upper.toFixed(3)}]
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-2xs font-semibold ${
                            p.is_significant
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {p.is_significant ? 'p < .05' : 'Không'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab Content: Decomposition of Effects & Mediation */}
          {activeTab === 'effects' && (
            <div className="space-y-6">
              {/* Indirect Effects (Mediation) */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                  <GitBranch className="w-4 h-4 text-indigo-600" />
                  <span>Tác động Gián tiếp & Kiểm định Trung gian (Sobel / Delta Method)</span>
                </h4>
                {result.indirect_effects && result.indirect_effects.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-xs">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-semibold text-slate-600">Chuỗi truyền (Mediation Path)</th>
                          <th className="px-3 py-2 text-right font-semibold text-slate-600">B_indirect</th>
                          <th className="px-3 py-2 text-right font-semibold text-slate-600">SE_sobel</th>
                          <th className="px-3 py-2 text-right font-semibold text-slate-600">z-stat</th>
                          <th className="px-3 py-2 text-right font-semibold text-slate-600">p-value</th>
                          <th className="px-3 py-2 text-right font-semibold text-indigo-700">β_indirect</th>
                          <th className="px-3 py-2 text-center font-semibold text-slate-600">Kết luận</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {result.indirect_effects.map((ind, idx) => (
                          <tr key={`ind-${idx}`} className="hover:bg-slate-50/80">
                            <td className="px-3 py-2.5 font-medium text-slate-900">{ind.path_str}</td>
                            <td className="px-3 py-2.5 text-right font-mono text-slate-700">{ind.unstandardized.toFixed(4)}</td>
                            <td className="px-3 py-2.5 text-right font-mono text-slate-500">{ind.standard_error.toFixed(4)}</td>
                            <td className="px-3 py-2.5 text-right font-mono text-slate-700">{ind.z_value.toFixed(3)}</td>
                            <td className="px-3 py-2.5 text-right font-mono font-medium">
                              <span className={ind.p_value < 0.05 ? 'text-emerald-700 font-bold' : 'text-slate-500'}>
                                {ind.p_value < 0.001 ? '< .001' : ind.p_value.toFixed(4)}
                              </span>
                            </td>
                            <td className="px-3 py-2.5 text-right font-mono font-bold text-indigo-700">
                              {ind.standardized.toFixed(4)}
                            </td>
                            <td className="px-3 py-2.5 text-center">
                              <span
                                className={`inline-flex px-2 py-0.5 rounded-full text-2xs font-semibold ${
                                  ind.is_significant
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-slate-100 text-slate-600'
                                }`}
                              >
                                {ind.is_significant ? 'Trung gian có ý nghĩa' : 'Không có ý nghĩa'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">
                    Không có chuỗi tác động gián tiếp nào (mô hình không có cấu trúc đa tầng trung gian).
                  </p>
                )}
              </div>

              {/* Total Effects */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                  <Layers className="w-4 h-4 text-indigo-600" />
                  <span>Tổng hợp Tác động (Direct, Indirect & Total Effects)</span>
                </h4>
                {result.total_effects && result.total_effects.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-xs">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-semibold text-slate-600">Cặp biến (X → Y)</th>
                          <th className="px-3 py-2 text-right font-semibold text-slate-600">Trực tiếp (Direct B)</th>
                          <th className="px-3 py-2 text-right font-semibold text-slate-600">Gián tiếp (Indirect B)</th>
                          <th className="px-3 py-2 text-right font-semibold text-slate-900 font-bold">Tổng thể (Total B)</th>
                          <th className="px-3 py-2 text-right font-semibold text-indigo-700 font-bold">Chuẩn hóa (Total β)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {result.total_effects.map((tot, idx) => (
                          <tr key={`tot-${idx}`} className="hover:bg-slate-50/80">
                            <td className="px-3 py-2 font-medium text-slate-900">
                              {tot.source_label} → {tot.target_label}
                            </td>
                            <td className="px-3 py-2 text-right font-mono text-slate-600">{tot.direct.toFixed(4)}</td>
                            <td className="px-3 py-2 text-right font-mono text-slate-600">{tot.indirect.toFixed(4)}</td>
                            <td className="px-3 py-2 text-right font-mono font-bold text-slate-900">{tot.total.toFixed(4)}</td>
                            <td className="px-3 py-2 text-right font-mono font-bold text-indigo-700">
                              {tot.standardized_total.toFixed(4)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab Content: Structural Equations R2 */}
          {activeTab === 'equations' && result.equations && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold text-slate-600">Biến nội sinh (Outcome)</th>
                    <th className="px-3 py-2 text-left font-semibold text-slate-600">Các biến dự báo</th>
                    <th className="px-3 py-2 text-right font-semibold text-indigo-700 font-bold">R²</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">R² hiệu chỉnh</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">Phương sai dư</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">F-statistic</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">p-value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.equations.map((eq, idx) => (
                    <tr key={`eq-${idx}`} className="hover:bg-slate-50/80">
                      <td className="px-3 py-2.5 font-bold text-slate-900">{eq.endogenous_label}</td>
                      <td className="px-3 py-2.5 text-slate-600">
                        {eq.predictors.join(', ')}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-bold text-indigo-700 text-sm">
                        {eq.r_squared.toFixed(4)}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-600">{eq.adj_r_squared.toFixed(4)}</td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-500">{eq.residual_variance.toFixed(4)}</td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-700">{eq.f_statistic.toFixed(2)}</td>
                      <td className="px-3 py-2.5 text-right font-mono font-medium">
                        <span className={eq.p_value < 0.05 ? 'text-emerald-700 font-bold' : 'text-slate-500'}>
                          {eq.p_value < 0.001 ? '< .001' : eq.p_value.toFixed(4)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* APA 7th Edition Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                  <Award className="w-4 h-4 text-indigo-600" />
                  <span>Thuyết minh Học thuật Chuẩn APA 7th Edition</span>
                </span>
                <button
                  type="button"
                  onClick={handleCopyApa}
                  className="flex items-center space-x-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium transition"
                >
                  {copiedApa ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-serif whitespace-pre-line bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
