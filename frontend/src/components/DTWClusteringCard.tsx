import React, { useState } from 'react';
import { api } from '../api/client';
import { DTWClusteringResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface DTWClusteringCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const DTWClusteringCard: React.FC<DTWClusteringCardProps> = ({
  surveyId,
  questions
}) => {
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [nClusters, setNClusters] = useState<number>(3);
  const [customLabels, setCustomLabels] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DTWClusteringResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const toggleQuestion = (qId: string) => {
    if (selectedQuestions.includes(qId)) {
      setSelectedQuestions(selectedQuestions.filter(id => id !== qId));
    } else {
      setSelectedQuestions([...selectedQuestions, qId]);
    }
  };

  const handleSelectAllNumeric = () => {
    setSelectedQuestions(numericQuestions.map(q => q.id));
  };

  const handleClear = () => {
    setSelectedQuestions([]);
  };

  const handleRunAnalysis = async () => {
    if (selectedQuestions.length < 3) {
      setError('Vui lòng chọn tối thiểu 3 câu hỏi theo dõi thời gian/làn sóng theo thứ tự thời gian.');
      return;
    }

    const labelsList = customLabels.trim()
      ? customLabels.split(',').map(s => s.trim()).filter(s => s.length > 0)
      : undefined;

    setError(null);
    setLoading(true);

    try {
      const data = await api.runDTWClustering(surveyId, {
        time_series_question_ids: selectedQuestions,
        time_labels: labelsList,
        n_clusters: nClusters,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể thực hiện phân cụm quỹ đạo DTW.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích DTW.');
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
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-cyan-950 text-cyan-400 border border-cyan-800">
              DTW Alignment
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-indigo-950 text-indigo-400 border border-indigo-800">
              Sakoe & Chiba (1978)
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
              K-Medoids Trajectory
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">
            Phân Cụm Quỹ Đạo Thời Gian (Dynamic Time Warping Trajectory Clustering)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Đồng chỉnh phi tuyến các chuỗi phản hồi dọc (Panel Longitudinal Data) để phân nhóm các mẫu hình thái hành vi/tâm lý mà không bị ảnh hưởng bởi độ trễ pha thời gian.
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Số cụm quỹ đạo mục tiêu (k clusters)
          </label>
          <div className="flex gap-2">
            {[2, 3, 4, 5].map(num => (
              <button
                key={num}
                type="button"
                onClick={() => setNClusters(num)}
                className={`flex-1 py-2 text-xs font-semibold rounded-lg border transition-all ${
                  nClusters === num
                    ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600'
                }`}
              >
                {num} Cụm
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Nhãn các mốc thời gian tùy chọn (cách nhau bởi dấu phẩy, VD: T1, T2, T3, T4)
          </label>
          <input
            type="text"
            placeholder="VD: Quý 1, Quý 2, Quý 3, Quý 4"
            value={customLabels}
            onChange={(e) => setCustomLabels(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Time-series Question Selection */}
      <div className="mb-6 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-300">
            Các mốc chuỗi thời gian / Làn sóng (Time Points / Waves): {selectedQuestions.length} đã chọn (cần tối thiểu 3)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleSelectAllNumeric}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Chọn tất cả biến số
            </button>
            <span className="text-slate-600">|</span>
            <button
              type="button"
              onClick={handleClear}
              className="text-xs text-slate-400 hover:text-slate-300 transition-colors"
            >
              Bỏ chọn
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto pr-1">
          {numericQuestions.map(q => {
            const checked = selectedQuestions.includes(q.id);
            const order = selectedQuestions.indexOf(q.id);
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
                  onChange={() => toggleQuestion(q.id)}
                  className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                />
                <span className="truncate flex-1" title={q.title}>
                  {q.title}
                </span>
                {checked && (
                  <span className="px-1.5 py-0.2 rounded bg-indigo-800 text-[10px] font-bold text-white">
                    #{order + 1}
                  </span>
                )}
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
              <span>Đang tính ma trận DTW & phân cụm...</span>
            </>
          ) : (
            <span>Phân Cụm Quỹ Đạo DTW (Barycenter PAM)</span>
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
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Cỡ mẫu Panel N</div>
                <div className="text-base font-bold text-white mt-0.5">
                  {result.sample_diagnostics.n_total.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Số mốc thời gian T</div>
                <div className="text-base font-bold text-indigo-400 mt-0.5">
                  {result.sample_diagnostics.n_time_points}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Số cụm k</div>
                <div className="text-base font-bold text-emerald-400 mt-0.5">
                  {result.sample_diagnostics.n_clusters}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Cửa sổ Sakoe-Chiba</div>
                <div className="text-base font-bold text-slate-300 mt-0.5">
                  r = {result.sample_diagnostics.window_radius}
                </div>
              </div>
              <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Hệ số Silhouette DTW</div>
                <div className={`text-base font-bold mt-0.5 ${
                  result.sample_diagnostics.mean_silhouette_score >= 0.4 ? 'text-emerald-400' : 'text-amber-400'
                }`}>
                  {result.sample_diagnostics.mean_silhouette_score.toFixed(3)}
                </div>
              </div>
            </div>
          )}

          {/* Cluster Profile Cards */}
          {result.clusters && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {result.clusters.map((c) => (
                <div key={c.cluster_id} className="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: c.color }} />
                      <span className="text-xs font-bold text-white">Cụm {c.cluster_id}</span>
                    </div>
                    <span className="text-xs font-bold text-indigo-400">
                      {c.percentage}% (n={c.size})
                    </span>
                  </div>

                  <div className="text-xs font-semibold mb-2" style={{ color: c.color }}>
                    {c.archetype_title}
                  </div>

                  <div className="text-[11px] text-slate-400 mb-2">
                    Độ phân tán DTW: <span className="text-slate-300 font-mono">{c.within_cluster_dispersion.toFixed(3)}</span>
                  </div>

                  <div className="pt-2 border-t border-slate-850">
                    <div className="text-[10px] text-slate-500 uppercase font-semibold mb-1">
                      Quỹ đạo Trung tâm (Mean Barycenter):
                    </div>
                    <div className="flex justify-between text-[11px] font-mono text-slate-300">
                      {c.mean_trajectory.map((val, idx) => (
                        <div key={idx} className="text-center">
                          <div className="text-[9px] text-slate-500">{result.time_labels?.[idx] || `T${idx+1}`}</div>
                          <div>{val.toFixed(2)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* SVG Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Biểu Đồ Quỹ Đạo Đồng Chỉnh DTW & Trung Tâm Cụm (Centroid Spaghetti Plot)
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
