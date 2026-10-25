import React, { useState } from 'react';
import { api } from '../api/client';
import { MSMAnalysisResult } from '../types/survey';

interface SimpleQuestion {
  id: string;
  title: string;
  question_type: string;
}

interface MSMCardProps {
  surveyId: string;
  questions: SimpleQuestion[];
}

interface WaveSlot {
  treatmentQId: string;
  confounderQId: string;
}

export const MSMCard: React.FC<MSMCardProps> = ({
  surveyId,
  questions
}) => {
  const [waveSlots, setWaveSlots] = useState<WaveSlot[]>([
    { treatmentQId: '', confounderQId: '' },
    { treatmentQId: '', confounderQId: '' }
  ]);
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MSMAnalysisResult | null>(null);
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);

  const numericQuestions = questions.filter(q =>
    ['number', 'rating', 'scale', 'linear_scale', 'nps'].includes(q.question_type)
  );

  const binaryOrNumericQuestions = questions.filter(q =>
    ['single_choice', 'boolean', 'number', 'scale'].includes(q.question_type)
  );

  const handleSlotChange = (index: number, field: 'treatmentQId' | 'confounderQId', value: string) => {
    const updated = [...waveSlots];
    updated[index][field] = value;
    setWaveSlots(updated);
  };

  const addWaveSlot = () => {
    if (waveSlots.length < 8) {
      setWaveSlots([...waveSlots, { treatmentQId: '', confounderQId: '' }]);
    }
  };

  const removeWaveSlot = (index: number) => {
    if (waveSlots.length > 2) {
      setWaveSlots(waveSlots.filter((_, i) => i !== index));
    }
  };

  const handleRunAnalysis = async () => {
    if (!outcomeQId) {
      setError('Vui lòng chọn câu hỏi biến kết quả cuối cùng (Terminal Outcome Y).');
      return;
    }

    for (let i = 0; i < waveSlots.length; i++) {
      if (!waveSlots[i].treatmentQId) {
        setError(`Vui lòng chọn biến can thiệp cho Đợt ${i + 1}.`);
        return;
      }
      if (!waveSlots[i].confounderQId) {
        setError(`Vui lòng chọn biến nhiễu cho Đợt ${i + 1}.`);
        return;
      }
      if (waveSlots[i].treatmentQId === waveSlots[i].confounderQId) {
        setError(`Biến can thiệp và biến nhiễu ở Đợt ${i + 1} không được trùng nhau.`);
        return;
      }
    }

    setError(null);
    setLoading(true);

    try {
      const data = await api.runMSMAnalysis(surveyId, {
        treatment_question_ids: waveSlots.map(s => s.treatmentQId),
        confounder_question_ids: waveSlots.map(s => s.confounderQId),
        outcome_question_id: outcomeQId,
        wave_labels: waveSlots.map((_, i) => `Đợt ${i + 1}`),
        scope
      });

      if (data.status === 'success') {
        setResult(data);
      } else {
        setError(data.message || 'Không thể ước lượng mô hình MSM.');
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi phân tích MSM.');
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
            <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 font-bold text-sm">
              MSM-IPTW
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Marginal Structural Models (Mô hình Cấu trúc Biên &amp; Nhiễu Biến thiên Thời gian)
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Ước lượng tác động nhân quả không thiên lệch khi có tương tác phản hồi giữa can thiệp và biến nhiễu theo thời gian - Robins, Hernán &amp; Brumback (2000), Hernán &amp; Robins (2024).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Bộ lọc dữ liệu:</span>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">Tất cả phản hồi hoàn thành</option>
            <option value="verified_clean">Chỉ mẫu sạch (Verified Clean)</option>
          </select>
        </div>
      </div>

      {/* Terminal Outcome Selector */}
      <div className="mt-6 bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
        <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
          Biến Kết Quả Đích Cuối Cùng (Terminal Outcome Y - Sau toàn bộ các đợt theo dõi):
        </label>
        <select
          value={outcomeQId}
          onChange={(e) => setOutcomeQId(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 p-2.5 focus:border-indigo-500 focus:outline-none"
        >
          <option value="">-- Chọn câu hỏi biến kết quả đầu ra --</option>
          {numericQuestions.map(q => (
            <option key={q.id} value={q.id}>
              {q.title} ({q.question_type})
            </option>
          ))}
        </select>
      </div>

      {/* Dynamic Wave Slots */}
      <div className="mt-5 space-y-3">
        <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
          Cấu hình chuỗi can thiệp và biến nhiễu qua các đợt sóng (Tối thiểu 2 Waves):
        </label>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {waveSlots.map((slot, idx) => (
            <div key={idx} className="bg-slate-800/50 p-3.5 rounded-xl border border-slate-700/60 relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-indigo-400">
                  Làn Sóng {idx + 1} (Wave {idx + 1}, t = {idx})
                </span>
                {waveSlots.length > 2 && (
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

              {/* Treatment selector */}
              <div className="mb-2">
                <span className="text-[11px] text-slate-400 font-medium block mb-1">
                  Biến can thiệp A_{idx + 1} (Nhị phân 0/1):
                </span>
                <select
                  value={slot.treatmentQId}
                  onChange={(e) => handleSlotChange(idx, 'treatmentQId', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">-- Chọn biến can thiệp A --</option>
                  {binaryOrNumericQuestions.map(q => (
                    <option key={q.id} value={q.id}>
                      {q.title} ({q.question_type})
                    </option>
                  ))}
                </select>
              </div>

              {/* Confounder selector */}
              <div>
                <span className="text-[11px] text-slate-400 font-medium block mb-1">
                  Biến nhiễu L_{idx + 1} (Đo lường tại đợt {idx + 1}):
                </span>
                <select
                  value={slot.confounderQId}
                  onChange={(e) => handleSlotChange(idx, 'confounderQId', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">-- Chọn biến nhiễu L --</option>
                  {numericQuestions.map(q => (
                    <option key={q.id} value={q.id}>
                      {q.title} ({q.question_type})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 pt-2">
          {waveSlots.length < 8 && (
            <button
              type="button"
              onClick={addWaveSlot}
              className="text-xs font-semibold px-3 py-2 bg-slate-800 text-indigo-400 hover:bg-slate-700 rounded-lg border border-indigo-500/30 transition-colors"
            >
              + Thêm Đợt Khảo Sát Tiếp Theo
            </button>
          )}

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="px-6 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs tracking-wide uppercase transition-all shadow-lg shadow-indigo-900/30 disabled:opacity-50 flex items-center gap-2 ml-auto"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Đang ước lượng mô hình MSM...
              </>
            ) : (
              'Ước Lượng Mô Hình Cấu Trúc Biên'
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
            {/* MSM Causal Effect */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-emerald-400 tracking-wider">
                Hiệu Ứng Nhân Quả MSM (β)
              </span>
              <div className="text-2xl font-black text-emerald-300 mt-1">
                {result.causal_effect_per_wave !== undefined && result.causal_effect_per_wave > 0
                  ? `+${result.causal_effect_per_wave.toFixed(3)}`
                  : result.causal_effect_per_wave?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SE: {result.std_error?.toFixed(3)} | z = {result.z_statistic?.toFixed(2)}
              </div>
              <div className="text-xs font-semibold text-emerald-400 mt-0.5">
                {result.p_value !== undefined && result.p_value < 0.001 ? 'p < .001 (Ý nghĩa cao)' : `p = ${result.p_value?.toFixed(3)}`}
              </div>
            </div>

            {/* Naive OLS Effect */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-rose-400 tracking-wider">
                Hồi Quy Ngây Thơ (Naive OLS)
              </span>
              <div className="text-2xl font-black text-rose-300 mt-1">
                {result.naive_ols_effect !== undefined && result.naive_ols_effect > 0
                  ? `+${result.naive_ols_effect.toFixed(3)}`
                  : result.naive_ols_effect?.toFixed(3)}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                p = {result.naive_ols_p_value?.toFixed(3)} (Bị méo mó bởi collider)
              </div>
              <div className="text-xs font-semibold text-slate-400 mt-0.5">
                Thiếu kiểm soát trọng số SW
              </div>
            </div>

            {/* Confounding Bias % */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-amber-400 tracking-wider">
                Thiên Lệch Nhiễu Thời Gian
              </span>
              <div className="text-2xl font-black text-amber-300 mt-1">
                {result.confounding_bias_pct !== undefined && result.confounding_bias_pct > 0
                  ? `+${result.confounding_bias_pct.toFixed(1)}%`
                  : `${result.confounding_bias_pct?.toFixed(1)}%`}
              </div>
              <div className="text-xs text-slate-300 mt-1 leading-snug">
                {result.confounding_verdict}
              </div>
            </div>

            {/* Weight Diagnostics */}
            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/60">
              <span className="text-xs uppercase font-bold text-indigo-400 tracking-wider">
                Chất Lượng Trọng Số SW
              </span>
              <div className="text-xl font-black text-white mt-1">
                Mean: <span className="text-indigo-300">{result.stabilized_weights_diagnostics?.mean.toFixed(3)}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                SD: {result.stabilized_weights_diagnostics?.std.toFixed(3)} | Max: {result.stabilized_weights_diagnostics?.max.toFixed(2)}
              </div>
              <div className="text-xs font-semibold text-teal-400 mt-0.5">
                {result.stabilized_weights_diagnostics && Math.abs(result.stabilized_weights_diagnostics.mean - 1.0) < 0.2
                  ? 'Trọng số ổn định hoàn hảo'
                  : 'Trọng số chấp nhận được'}
              </div>
            </div>
          </div>

          {/* Sample Size Bar */}
          <div className="bg-slate-800/40 px-4 py-2.5 rounded-lg border border-slate-700/50 flex flex-wrap items-center justify-between text-xs text-slate-300">
            <div>
              Mẫu theo dõi dọc: <strong>{result.sample_size}</strong> cá nhân qua <strong>{result.waves_count}</strong> đợt khảo sát
            </div>
            <div className="text-slate-400 font-mono">
              Khoảng tin cậy 95% MSM: [{result.ci_95_lower?.toFixed(3)}, {result.ci_95_upper?.toFixed(3)}]
            </div>
          </div>

          {/* Vector SVG Dual-Panel Chart */}
          {result.svg_chart && (
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-inner">
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                Biểu đồ Phân phối Trọng số Ổn định &amp; Đường cong Đáp ứng Liều Causal MSM
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
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
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
              <li>Robins, J. M., Hernán, M. Á., &amp; Brumback, B. (2000). Marginal structural models and causal inference in epidemiology. <em>Epidemiology</em>, 11(5), 550-560.</li>
              <li>Hernán, M. Á., &amp; Robins, J. M. (2024). <em>Causal Inference: What If</em>. CRC Press.</li>
              <li>Cole, S. R., &amp; Hernán, M. Á. (2008). Constructing inverse probability weights for marginal structural models. <em>American Journal of Epidemiology</em>, 168(6), 656-664.</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
