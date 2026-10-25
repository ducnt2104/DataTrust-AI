import React, { useState } from 'react';
import { LatentProfileResult } from '../types/survey';
import { api } from '../api/client';

interface LatentProfileCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string }>;
}

export const LatentProfileCard: React.FC<LatentProfileCardProps> = ({ surveyId, questions }) => {
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>([]);
  const [nProfiles, setNProfiles] = useState<number | undefined>(undefined);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LatentProfileResult | null>(null);

  // Eligible indicators (numeric, scales, likert, or ordered ordinal)
  const eligibleQuestions = questions.filter(
    (q) =>
      q.question_type === 'linear_scale' ||
      q.question_type === 'likert' ||
      q.question_type === 'number' ||
      q.question_type === 'matrix' ||
      q.question_type === 'ranking' ||
      q.question_type === 'single_choice' ||
      q.question_type === 'dropdown'
  );

  const toggleIndicator = (qid: string) => {
    setSelectedIndicators((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const selectAllEligible = () => {
    if (selectedIndicators.length === eligibleQuestions.length) {
      setSelectedIndicators([]);
    } else {
      setSelectedIndicators(eligibleQuestions.map((q) => q.id));
    }
  };

  const handleRunAnalysis = async () => {
    if (selectedIndicators.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 biến chỉ báo để ước lượng mô hình LPA.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.runLatentProfile(surveyId, {
        indicator_question_ids: selectedIndicators,
        n_profiles: nProfiles,
        max_profiles: 4,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình hồ sơ tiềm ẩn với dữ liệu hiện tại.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi gửi yêu cầu phân tích LPA.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Person-Centered GMM
            </span>
            <span className="text-xs text-slate-400 font-mono">McLachlan & Peel 2000; Collins & Lanza 2010</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Phân Tích Hồ Sơ Tiềm Ẩn (Latent Profile Analysis - LPA)
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Phân đoạn đối tượng phi giám sát dựa trên mô hình hỗn hợp Gauss đa biến, phân tách các phân đoạn ngầm và đánh giá độ chính xác qua Entropy.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={handleRunAnalysis}
          disabled={loading || selectedIndicators.length < 2}
          className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium rounded-lg text-sm transition-all shadow-lg shadow-emerald-900/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Đang Ước Lượng EM...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Chạy Phân Tích LPA</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-6 p-4 bg-slate-950/60 rounded-lg border border-slate-800/80">
        {/* Indicators Selector */}
        <div className="md:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Chọn Các Biến Chỉ Báo Thang Đo (P &ge; 2)
            </label>
            <button
              onClick={selectAllEligible}
              className="text-xs text-emerald-400 hover:text-emerald-300 underline font-medium"
            >
              {selectedIndicators.length === eligibleQuestions.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1">
            {eligibleQuestions.map((q) => {
              const isSelected = selectedIndicators.includes(q.id);
              return (
                <div
                  key={q.id}
                  onClick={() => toggleIndicator(q.id)}
                  className={`p-2.5 rounded-md border text-xs cursor-pointer transition-all flex items-center gap-2 ${
                    isSelected
                      ? 'bg-emerald-950/50 border-emerald-500/60 text-emerald-200'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}}
                    className="rounded border-slate-700 text-emerald-500 focus:ring-0 focus:ring-offset-0 bg-slate-800 cursor-pointer"
                  />
                  <span className="truncate">{q.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Number of Classes & Scope */}
        <div className="space-y-4 flex flex-col justify-between">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Số Lượng Hồ Sơ (Classes K)
            </label>
            <select
              value={nProfiles === undefined ? 'auto' : nProfiles}
              onChange={(e) => setNProfiles(e.target.value === 'auto' ? undefined : parseInt(e.target.value, 10))}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="auto">Tự động chọn K tối ưu (BIC + Entropy)</option>
              <option value="2">Cố định K = 2 lớp</option>
              <option value="3">Cố định K = 3 lớp</option>
              <option value="4">Cố định K = 4 lớp</option>
              <option value="5">Cố định K = 5 lớp</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Phạm Vi Dữ Liệu
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setScope('all')}
                className={`flex-1 py-1.5 px-3 rounded text-xs font-medium border transition-all ${
                  scope === 'all'
                    ? 'bg-emerald-600 text-white border-emerald-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Tất cả mẫu
              </button>
              <button
                onClick={() => setScope('verified_clean')}
                className={`flex-1 py-1.5 px-3 rounded text-xs font-medium border transition-all ${
                  scope === 'verified_clean'
                    ? 'bg-emerald-600 text-white border-emerald-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Mẫu sạch đã xác thực
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 mb-6 rounded-lg bg-red-950/40 border border-red-500/50 text-red-200 text-sm flex items-center gap-3">
          <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Results Display */}
      {result && result.diagnostics && (
        <div className="space-y-6">
          {/* Key Metrics Dashboard */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Cỡ Mẫu (N)</div>
              <div className="text-lg font-bold text-white mt-0.5">{result.diagnostics.sample_size}</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Số Lớp Tối Ưu (K)</div>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">{result.diagnostics.optimal_n_classes} Hồ Sơ</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Chỉ Số Entropy (E)</div>
              <div className={`text-lg font-bold mt-0.5 ${result.diagnostics.entropy >= 0.8 ? 'text-emerald-400' : (result.diagnostics.entropy >= 0.65 ? 'text-amber-400' : 'text-red-400')}`}>
                {result.diagnostics.entropy.toFixed(3)}
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Độ Phân Tách</div>
              <div className="text-sm font-semibold text-slate-200 mt-1">
                {result.diagnostics.separation_quality} ({result.diagnostics.is_well_separated ? 'Sắc nét' : 'Trung bình'})
              </div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Tiêu Chuẩn BIC</div>
              <div className="text-lg font-bold text-slate-200 mt-0.5">{result.diagnostics.bic.toFixed(1)}</div>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-xs">Sample-Adj BIC</div>
              <div className="text-lg font-bold text-slate-200 mt-0.5">{result.diagnostics.sabic.toFixed(1)}</div>
            </div>
          </div>

          {/* Model Comparison Table (Class Enumeration) */}
          {result.model_comparison && result.model_comparison.length > 0 && (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 overflow-x-auto">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Bảng So Sánh Chỉ Số Phù Hợp Các Mô Hình (Class Enumeration: K=2..{result.model_comparison.length + 1})
              </h4>
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase font-mono">
                  <tr>
                    <th className="py-2 px-3">Số Lớp (K)</th>
                    <th className="py-2 px-3">Log-Likelihood</th>
                    <th className="py-2 px-3">Số Tham Số (M)</th>
                    <th className="py-2 px-3">AIC</th>
                    <th className="py-2 px-3">BIC</th>
                    <th className="py-2 px-3">SABIC</th>
                    <th className="py-2 px-3">Entropy</th>
                    <th className="py-2 px-3">Min Class %</th>
                    <th className="py-2 px-3">Đánh Giá</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.model_comparison.map((m) => {
                    const isSelected = m.n_classes === result.diagnostics?.optimal_n_classes;
                    return (
                      <tr key={m.n_classes} className={isSelected ? 'bg-emerald-950/40 text-emerald-200 font-semibold' : 'hover:bg-slate-900/50'}>
                        <td className="py-2 px-3 flex items-center gap-1.5">
                          {isSelected && <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />}
                          K = {m.n_classes}
                        </td>
                        <td className="py-2 px-3">{m.log_likelihood}</td>
                        <td className="py-2 px-3">{m.num_params}</td>
                        <td className="py-2 px-3">{m.aic}</td>
                        <td className="py-2 px-3">{m.bic}</td>
                        <td className="py-2 px-3">{m.sabic}</td>
                        <td className="py-2 px-3">
                          <span className={m.entropy >= 0.8 ? 'text-emerald-400' : 'text-slate-300'}>
                            {m.entropy.toFixed(3)}
                          </span>
                        </td>
                        <td className="py-2 px-3">{m.min_class_pct}%</td>
                        <td className="py-2 px-3">
                          {isSelected ? (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              Mô hình Tối ưu
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[10px]">Ứng viên</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* SVG Latent Profile Plot & Distribution */}
          {result.svg_visualization && (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Đồ Thị Quỹ Đạo Điểm Chuẩn Hóa Hồ Sơ &amp; Thước Đo Phân Tách
              </h4>
              <div
                className="w-full flex justify-center overflow-x-auto"
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
              />
            </div>
          )}

          {/* Profiles Breakdown */}
          {result.profiles && result.profiles.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Đặc Điểm Chi Tiết Từng Phân Đoạn Tiềm Ẩn (Profiles Breakdown)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.profiles.map((p) => (
                  <div key={p.profile_id} className="p-4 bg-slate-950/70 border border-slate-800 rounded-lg">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 mb-3">
                      <div>
                        <span className="text-xs font-mono font-semibold text-emerald-400 mr-2">Hồ Sơ {p.profile_id}</span>
                        <h5 className="text-sm font-bold text-white inline">{p.name}</h5>
                      </div>
                      <span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-xs font-semibold">
                        {p.percentage}% (n = {p.size})
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 mb-3 bg-slate-900/60 p-2 rounded">
                      <span>Xác suất hậu nghiệm TB (AvePP):</span>
                      <span className="font-semibold text-emerald-400">{(p.average_posterior_prob * 100).toFixed(1)}%</span>
                    </div>

                    <div className="space-y-1.5">
                      {p.item_statistics.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs">
                          <span className="text-slate-300 truncate max-w-[180px]">{item.indicator}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-400">TB: {item.mean.toFixed(2)}</span>
                            <span
                              className={`px-1.5 py-0.2 rounded font-mono text-[10px] ${
                                item.z_score >= 0.3
                                  ? 'bg-blue-950/60 text-blue-300 border border-blue-800/50'
                                  : item.z_score <= -0.3
                                  ? 'bg-rose-950/60 text-rose-300 border border-rose-800/50'
                                  : 'bg-slate-800 text-slate-400'
                              }`}
                            >
                              {item.z_score >= 0 ? `+${item.z_score.toFixed(2)}z` : `${item.z_score.toFixed(2)}z`}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Academic APA Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-950/90 rounded-lg border border-slate-800 text-slate-300 text-xs leading-relaxed space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span>Báo Cáo Học Thuật Chuẩn APA 7th Edition (Latent Profile Analysis)</span>
              </div>
              <p className="whitespace-pre-line">{result.apa_narrative}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
