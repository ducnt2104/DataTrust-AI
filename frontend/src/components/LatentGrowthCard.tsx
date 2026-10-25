import React, { useState } from 'react';
import { api } from '../api/client';
import { LatentGrowthResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface LatentGrowthCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

export const LatentGrowthCard: React.FC<LatentGrowthCardProps> = ({
  surveyId,
  questions
}) => {
  const [waveQIds, setWaveQIds] = useState<string[]>(['', '', '']);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LatentGrowthResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const handleWaveChange = (index: number, val: string) => {
    const updated = [...waveQIds];
    updated[index] = val;
    setWaveQIds(updated);
  };

  const addWaveSlot = () => {
    if (waveQIds.length < 10) {
      setWaveQIds([...waveQIds, '']);
    }
  };

  const removeWaveSlot = (index: number) => {
    if (waveQIds.length > 3) {
      setWaveQIds(waveQIds.filter((_, i) => i !== index));
    }
  };

  const handleRunAnalysis = async () => {
    const cleanIds = waveQIds.filter(id => id.trim() !== '');
    if (cleanIds.length < 3) {
      setError('Vui lòng chọn tối thiểu 3 câu hỏi cho 3 đợt/làn sóng (waves) liên tiếp.');
      return;
    }

    // Check duplicates
    const uniqueIds = new Set(cleanIds);
    if (uniqueIds.size !== cleanIds.length) {
      setError('Các câu hỏi đợt khảo sát không được trùng lặp.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const timeScores = cleanIds.map((_, i) => i * 1.0);
      const waveLabels = cleanIds.map((_, i) => `Đợt ${i + 1}`);

      const data = await api.runLatentGrowthAnalysis(surveyId, {
        wave_question_ids: cleanIds,
        time_scores: timeScores,
        wave_labels: waveLabels,
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình Latent Growth Curve.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích LGCM.');
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
            <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 font-bold text-sm">
              LGCM
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Latent Growth Curve Modeling (Mô hình Quỹ đạo Tăng trưởng Tiềm ẩn)
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Ước lượng quỹ đạo tăng trưởng cá nhân theo thời gian, tách biệt điểm khởi đầu (Intercept) và tốc độ phát triển (Slope) - Meredith & Tisak (1990), Bollen & Curran (2006).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Bộ lọc dữ liệu:</span>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">Tất cả phản hồi hoàn thành</option>
            <option value="verified_clean">Chỉ mẫu sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="mt-6 space-y-4">
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Chọn các câu hỏi theo trình tự thời gian (Tối thiểu 3 Waves / Làn sóng):
        </label>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {waveQIds.map((qid, idx) => (
            <div key={idx} className="bg-slate-800/70 p-3 rounded-lg border border-slate-700/60 relative">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-emerald-400">
                  Làn sóng {idx + 1} (Wave {idx + 1}, t = {idx})
                </span>
                {waveQIds.length > 3 && (
                  <button
                    type="button"
                    onClick={() => removeWaveSlot(idx)}
                    className="text-slate-400 hover:text-red-400 text-xs px-1"
                    title="Xóa làn sóng này"
                  >
                    ✕
                  </button>
                )}
              </div>
              <select
                value={qid}
                onChange={(e) => handleWaveChange(idx, e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-emerald-500 focus:outline-none"
              >
                <option value="">-- Chọn câu hỏi đo lường --</option>
                {numericQuestions.map(q => (
                  <option key={q.id} value={q.id}>
                    {q.title} ({q.question_type})
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 pt-2">
          {waveQIds.length < 10 && (
            <button
              type="button"
              onClick={addWaveSlot}
              className="text-xs font-semibold px-3 py-2 bg-slate-800 text-emerald-400 hover:bg-slate-700 rounded-lg border border-emerald-500/30 transition-colors"
            >
              + Thêm Làn Sóng Tiếp Theo
            </button>
          )}

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs tracking-wide uppercase transition-all shadow-lg shadow-emerald-900/30 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Đang ước lượng mô hình LGCM...
              </>
            ) : (
              'Ước Lượng Mô Hình LGCM'
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
            {/* Intercept */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                Mức Khởi Điểm (Intercept)
              </span>
              <div className="text-2xl font-black text-white mt-1">
                {result.latent_means?.intercept_mean.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {result.latent_means?.intercept_se.toFixed(3)} | z = {result.latent_means?.intercept_z.toFixed(2)}
              </div>
              <div className="text-xs font-semibold text-emerald-400 mt-0.5">
                {result.latent_means && result.latent_means.intercept_p < 0.001 ? 'p < .001 (Ý nghĩa cao)' : `p = ${result.latent_means?.intercept_p.toFixed(3)}`}
              </div>
            </div>

            {/* Slope */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                Tốc Độ Tăng Trưởng (Slope)
              </span>
              <div className="text-2xl font-black text-emerald-400 mt-1">
                {result.latent_means
                  ? (result.latent_means.slope_mean > 0
                      ? `+${result.latent_means.slope_mean.toFixed(3)}`
                      : result.latent_means.slope_mean.toFixed(3))
                  : '0.000'}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {result.latent_means?.slope_se.toFixed(3)} | z = {result.latent_means?.slope_z.toFixed(2)}
              </div>
              <div className="text-xs font-semibold text-cyan-400 mt-0.5">
                {result.growth_dynamics?.direction} ({result.growth_dynamics?.has_significant_trajectory ? 'Có ý nghĩa' : 'Chưa có ý nghĩa'})
              </div>
            </div>

            {/* Intercept-Slope Correlation */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                Tương Quan Khởi Đầu - Tốc Độ
              </span>
              <div className="text-2xl font-black text-amber-400 mt-1">
                r = {result.latent_variances?.intercept_slope_correlation.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Cov(I, S): {result.latent_variances?.intercept_slope_covariance.toFixed(3)}
              </div>
              <div className="text-xs text-slate-300 mt-0.5">
                {result.latent_variances && result.latent_variances.intercept_slope_correlation < -0.2
                  ? 'Hiệu ứng trần (Ceiling / Thu hẹp khoảng cách)'
                  : (result.latent_variances && result.latent_variances.intercept_slope_correlation > 0.2
                    ? 'Hiệu ứng Matthew (Lợi thế tích lũy)'
                    : 'Tăng trưởng độc lập mức ban đầu')}
              </div>
            </div>

            {/* Fit Indices */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                Độ Phù Hợp Mô Hình
              </span>
              <div className="text-xl font-black text-white mt-1">
                CFI: <span className={result.model_fit?.is_good_fit ? 'text-emerald-400' : 'text-amber-400'}>{result.model_fit?.cfi.toFixed(3)}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                RMSEA: {result.model_fit?.rmsea.toFixed(3)} | TLI: {result.model_fit?.tli.toFixed(3)}
              </div>
              <div className="text-xs font-semibold mt-0.5 text-slate-300">
                χ²({result.model_fit?.degrees_of_freedom}) = {result.model_fit?.chi_square.toFixed(2)} (p = {result.model_fit?.p_value.toFixed(3)})
              </div>
            </div>
          </div>

          {/* Observed Wave Means Pill Bar */}
          {result.observed_wave_means && result.observed_wave_means.length > 0 && (
            <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/50 flex flex-wrap items-center gap-4 text-xs">
              <span className="font-semibold text-slate-300">Điểm trung bình quan sát qua các đợt:</span>
              {result.observed_wave_means.map((m, idx) => (
                <div key={idx} className="bg-slate-900 px-3 py-1 rounded border border-slate-700 text-slate-200">
                  <span className="text-emerald-400 font-bold">Đợt {idx + 1}:</span> {m.toFixed(2)}
                </div>
              ))}
              <span className="text-slate-400 ml-auto">
                Mẫu phân tích: <strong>{result.sample_size}</strong> cá nhân
              </span>
            </div>
          )}

          {/* Vector SVG Dual-Panel Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-inner">
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                Biểu đồ Quỹ đạo Tăng trưởng Cá nhân &amp; Đường Xu thế Dân số (95% CI)
              </div>
              <div
                className="w-full overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_chart }}
              />
            </div>
          )}

          {/* APA 7th Edition Academic Narrative */}
          {result.apa_narrative && (
            <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700/60 relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
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
              <li>Meredith, W., &amp; Tisak, J. (1990). Latent curve analysis. <em>Psychometrika</em>, 55(1), 107-122.</li>
              <li>Bollen, K. A., &amp; Curran, P. J. (2006). <em>Latent Curve Models: A Structural Equation Perspective</em>. John Wiley &amp; Sons.</li>
              <li>Preacher, K. J., et al. (2008). <em>Latent Growth Curve Modeling</em>. SAGE Publications.</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
