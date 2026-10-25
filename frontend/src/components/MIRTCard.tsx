import React, { useState } from 'react';
import {
  Compass,
  Crosshair,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Sparkles,
  RefreshCw,
  Info,
  CheckSquare,
  Square
} from 'lucide-react';
import { api } from '../api/client';
import { MIRTResult } from '../types/survey';

interface MIRTCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const MIRTCard: React.FC<MIRTCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MIRTResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Configuration
  const [selectedItemIds, setSelectedItemIds] = useState<string[]>([]);
  const [nDimensions, setNDimensions] = useState<number>(2);
  const [dim1Name, setDim1Name] = useState<string>('Năng lực Phân tích');
  const [dim2Name, setDim2Name] = useState<string>('Năng lực Ngôn ngữ');
  const [dim3Name, setDim3Name] = useState<string>('Tư duy Không gian');
  const [maxIter, setMaxIter] = useState<number>(30);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'items' | 'svg'>('items');

  const toggleItem = (qid: string) => {
    setSelectedItemIds(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const selectAll = () => {
    setSelectedItemIds(questions.map(q => q.id));
  };

  const clearAll = () => {
    setSelectedItemIds([]);
  };

  const handleRun = async () => {
    if (selectedItemIds.length < 3) {
      setError('Cần chọn tối thiểu 3 câu hỏi khảo sát để phân tích MIRT đa chiều.');
      return;
    }

    setLoading(true);
    setError(null);

    const dimNames = nDimensions === 2 ? [dim1Name, dim2Name] : [dim1Name, dim2Name, dim3Name];

    try {
      const data = await api.runMIRTAnalysis(surveyId, {
        item_question_ids: selectedItemIds,
        n_dimensions: nDimensions,
        dimension_names: dimNames,
        max_em_iter: maxIter,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình MIRT.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gọi API MIRT.');
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
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-slate-100 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-sky-500/10 border border-sky-500/20 rounded-xl text-sky-400">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Multidimensional Item Response Theory (MIRT)
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                Reckase (2009) · M2PL
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Lý thuyết Ứng đáp Câu hỏi Đa chiều: Phân biệt Đa chiều (MDISC), Độ khó (MID) &amp; Góc Đo lường Chỉ hướng qua MMLE-EM
            </p>
          </div>
        </div>
      </div>

      {/* Config Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6">
        {/* Items Selection */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-sky-400" />
              Chọn các Câu hỏi / Mục Khảo sát (Tối thiểu 3 items)
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={selectAll}
                className="text-xs text-sky-400 hover:text-sky-300 transition"
              >
                Chọn tất cả ({questions.length})
              </button>
              <span className="text-slate-600">|</span>
              <button
                type="button"
                onClick={clearAll}
                className="text-xs text-slate-400 hover:text-slate-300 transition"
              >
                Bỏ chọn
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
            {questions.map((q) => {
              const isSelected = selectedItemIds.includes(q.id);
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => toggleItem(q.id)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left text-xs transition ${
                    isSelected
                      ? 'bg-sky-500/20 border border-sky-500/40 text-sky-300'
                      : 'hover:bg-slate-800/80 text-slate-300'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4 text-sky-400 flex-shrink-0" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  )}
                  <span className="truncate">{q.title}</span>
                </button>
              );
            })}
          </div>
          <span className="text-[11px] text-slate-500 block">
            Đã chọn {selectedItemIds.length}/{questions.length} câu hỏi.
          </span>
        </div>

        {/* Dimension & EM Settings */}
        <div className="space-y-4 bg-slate-800/40 border border-slate-800 p-4 rounded-xl">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
              Số Chiều Năng Lực Tiềm Ẩn (Dimensions D)
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setNDimensions(2)}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  nDimensions === 2
                    ? 'bg-sky-600/20 border-sky-500 text-sky-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                2 Chiều (2D Planar)
              </button>
              <button
                type="button"
                onClick={() => setNDimensions(3)}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  nDimensions === 3
                    ? 'bg-sky-600/20 border-sky-500 text-sky-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                3 Chiều (3D Spatial)
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-[11px] text-slate-400 block mb-0.5">Tên Chiều 1 (Trait 1)</label>
              <input
                type="text"
                value={dim1Name}
                onChange={(e) => setDim1Name(e.target.value)}
                className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="text-[11px] text-slate-400 block mb-0.5">Tên Chiều 2 (Trait 2)</label>
              <input
                type="text"
                value={dim2Name}
                onChange={(e) => setDim2Name(e.target.value)}
                className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded-lg text-white"
              />
            </div>
            {nDimensions === 3 && (
              <div>
                <label className="text-[11px] text-slate-400 block mb-0.5">Tên Chiều 3 (Trait 3)</label>
                <input
                  type="text"
                  value={dim3Name}
                  onChange={(e) => setDim3Name(e.target.value)}
                  className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded-lg text-white"
                />
              </div>
            )}
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Phạm vi khảo sát</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  scope === 'all'
                    ? 'bg-sky-600/20 border-sky-500 text-sky-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                Tất cả (All)
              </button>
              <button
                type="button"
                onClick={() => setScope('verified_clean')}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  scope === 'verified_clean'
                    ? 'bg-emerald-600/20 border-emerald-500 text-emerald-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                Đã làm sạch
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleRun}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-sky-500/20 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Đang hội tụ MMLE-EM đa chiều...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Ước lượng MIRT 2PL
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mt-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && result.diagnostics && (
        <div className="mt-8 space-y-6 pt-6 border-t border-slate-800">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Số Mục Đo (J)</span>
              <span className="text-base font-bold text-sky-400 mt-1 block">
                {result.diagnostics.n_items}
              </span>
              <span className="text-[9px] text-slate-500">Mục hỏi M2PL</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Chiều Tiềm Ẩn (D)</span>
              <span className="text-base font-bold text-indigo-400 mt-1 block">
                {result.diagnostics.n_dimensions}D
              </span>
              <span className="text-[9px] text-slate-500">Không gian năng lực</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Hội Tụ MMLE-EM</span>
              <span className="text-base font-bold text-emerald-400 mt-1 block">
                {result.diagnostics.em_iterations} vòng
              </span>
              <span className="text-[9px] text-slate-500">{result.diagnostics.converged ? 'Đã hội tụ' : 'Gần hội tụ'}</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Log-Likelihood</span>
              <span className="text-base font-bold text-slate-200 mt-1 block">
                {result.diagnostics.log_likelihood.toFixed(1)}
              </span>
              <span className="text-[9px] text-slate-500">AIC: {result.diagnostics.aic.toFixed(0)}</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Tương Quan Chiều</span>
              <span className="text-base font-bold text-amber-400 mt-1 block">
                {result.diagnostics.trait_correlations && result.diagnostics.trait_correlations.length > 0
                  ? `r = ${result.diagnostics.trait_correlations[0].correlation_r.toFixed(2)}`
                  : 'Độc lập'}
              </span>
              <span className="text-[9px] text-slate-500">Hiệp phương sai EAP</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Cỡ Mẫu (N)</span>
              <span className="text-base font-bold text-purple-400 mt-1 block">
                {result.diagnostics.n_samples}
              </span>
              <span className="text-[9px] text-slate-500">Người trả lời</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('items')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'items'
                  ? 'bg-sky-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Thông số Câu hỏi Đa chiều (MDISC &amp; MID)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'svg'
                  ? 'bg-sky-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Không Gian Vector Thuộc Tính (SVG Vector Space)
            </button>
          </div>

          {/* Table Tab */}
          {activeTab === 'items' && result.item_parameters && (
            <div className="bg-slate-800/40 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4">Câu hỏi / Mục đo</th>
                    <th className="py-2.5 px-4">Độ Dốc (Slopes a)</th>
                    <th className="py-2.5 px-4">Phân biệt Đa chiều (MDISC)</th>
                    <th className="py-2.5 px-4">Độ khó Đa chiều (MID)</th>
                    <th className="py-2.5 px-4">Góc Đo Lường (α)</th>
                    <th className="py-2.5 px-4">RMSEA Độ Khớp</th>
                    <th className="py-2.5 px-4">Đánh Giá</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.item_parameters.map((it, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 font-semibold text-white">{it.item_name}</td>
                      <td className="py-2.5 px-4 font-mono text-slate-300">
                        [{it.slopes_a.map(a => a.toFixed(2)).join(', ')}]
                      </td>
                      <td className="py-2.5 px-4 font-bold text-sky-400">
                        {it.mdisc.toFixed(3)}
                        <span className="block text-[10px] text-slate-500 font-normal">
                          {it.mdisc_classification}
                        </span>
                      </td>
                      <td className={`py-2.5 px-4 font-bold ${it.mid >= 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {it.mid >= 0 ? `+${it.mid.toFixed(3)}` : it.mid.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-4 text-purple-300 font-mono text-[11px]">
                        [{it.directional_angles_deg.map(deg => `${deg}°`).join(', ')}]
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 font-mono">
                        {it.item_rmsea.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                          it.item_fit_verdict.includes('TỐT')
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}>
                          {it.item_fit_verdict}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* SVG Tab */}
          {activeTab === 'svg' && result.svg_visualization && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl overflow-x-auto">
              <div
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                className="w-full flex justify-center"
              />
            </div>
          )}

          {/* APA 7th Academic Narrative */}
          {result.apa_narrative && (
            <div className="p-5 bg-slate-800/30 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Info className="w-4 h-4 text-sky-400" />
                  Báo cáo Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={copyNarrative}
                  className="inline-flex items-center gap-1.5 px-3 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Sao chép APA</span>
                    </>
                  )}
                </button>
              </div>

              <div className="text-xs text-slate-300 leading-relaxed space-y-2 whitespace-pre-line font-serif italic bg-slate-900/60 p-4 rounded-lg border border-slate-800/60">
                {result.apa_narrative}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
