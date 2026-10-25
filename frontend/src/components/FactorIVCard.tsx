import React, { useState } from 'react';
import {
  FactorIVResult,
  FactorIVRequest
} from '../types/survey';
import { api } from '../api/client';
import {
  Cpu,
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertTriangle,
  AlertCircle,
  ShieldCheck,
  Sparkles,
  Sliders,
  Layers,
  Activity,
  BarChart2,
  TrendingDown,
  TrendingUp,
  Percent,
  Compass,
  Database
} from 'lucide-react';

interface QuestionSummary {
  id: string;
  title: string;
  question_type?: string;
}

interface Props {
  surveyId: string;
  questions: QuestionSummary[];
}

export const FactorIVCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [outcomeQId, setOutcomeQId] = useState<string>('');
  const [treatmentQId, setTreatmentQId] = useState<string>('');
  const [selectedInstruments, setSelectedInstruments] = useState<string[]>([]);
  const [selectedCovariates, setSelectedCovariates] = useState<string[]>([]);
  const [nFactorsOverride, setNFactorsOverride] = useState<string>('auto');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<FactorIVResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const numericQuestions = questions.filter(
    q => q.question_type === 'number' || q.question_type === 'rating' || q.question_type === 'scale'
  );

  const handleToggleInstrument = (qId: string) => {
    if (selectedInstruments.includes(qId)) {
      setSelectedInstruments(selectedInstruments.filter(id => id !== qId));
    } else {
      setSelectedInstruments([...selectedInstruments, qId]);
    }
  };

  const handleToggleCovariate = (qId: string) => {
    if (selectedCovariates.includes(qId)) {
      setSelectedCovariates(selectedCovariates.filter(id => id !== qId));
    } else {
      setSelectedCovariates([...selectedCovariates, qId]);
    }
  };

  const handleSelectAllInstruments = () => {
    const candidates = numericQuestions
      .filter(q => q.id !== outcomeQId && q.id !== treatmentQId)
      .map(q => q.id);
    setSelectedInstruments(candidates);
  };

  const handleClearInstruments = () => {
    setSelectedInstruments([]);
  };

  const handleRun = async () => {
    if (!outcomeQId || !treatmentQId) {
      setError('Vui lòng chọn biến kết quả Y và biến can thiệp nội sinh D.');
      return;
    }
    if (selectedInstruments.length < 2) {
      setError('Factor IV yêu cầu tối thiểu 2 biến công cụ ứng viên (K >= 2).');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: FactorIVRequest = {
      outcome_question_id: outcomeQId,
      treatment_question_id: treatmentQId,
      instrument_question_ids: selectedInstruments,
      covariate_question_ids: selectedCovariates.length > 0 ? selectedCovariates : undefined,
      n_factors: nFactorsOverride === 'auto' ? undefined : parseInt(nFactorsOverride, 10),
      alpha_level: 0.05,
      scope
    };

    try {
      const res = await api.runFactorIV(surveyId, payload);
      if (res.status === 'SUCCESS') {
        setResult(res);
      } else {
        setError(res.message || 'Không thể ước lượng Factor Instrumental Variables.');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi gọi API Factor IV.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (result?.apa_narrative) {
      navigator.clipboard.writeText(result.apa_narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const summary = result?.overall_summary;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-teal-50 dark:bg-teal-950/60 rounded-lg text-teal-600 dark:text-teal-400">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Công cụ Nhân tố &amp; Hồi quy 2SLS Thành phần Chính (Factor IV / PC-2SLS)
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Bai &amp; Ng (2010 Econometric Theory) · Stock &amp; Watson (2002) · Bai-Ng IC_p1 Factor Selection · Giải quyết "Lời nguyền Nhiều Công cụ" (Many Instruments Bias)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-100 text-teal-800 dark:bg-teal-900/50 dark:text-teal-300">
            Bai &amp; Ng 2010
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
            Dimension Reduction
          </span>
        </div>
      </div>

      {/* Main Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Outcome Y */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến kết quả Y (Outcome)
          </label>
          <select
            value={outcomeQId}
            onChange={(e) => setOutcomeQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn biến kết quả --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Treatment D */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến can thiệp nội sinh D (Treatment)
          </label>
          <select
            value={treatmentQId}
            onChange={(e) => setTreatmentQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="">-- Chọn biến can thiệp nội sinh --</option>
            {numericQuestions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>

        {/* Number of Factors Override */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Số lượng Nhân tố ẩn (r*)
          </label>
          <select
            value={nFactorsOverride}
            onChange={(e) => setNFactorsOverride(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="auto">Tự động tối ưu (Bai-Ng 2002 IC_p1)</option>
            <option value="1">1 Nhân tố (Factor F1)</option>
            <option value="2">2 Nhân tố (Factors F1, F2)</option>
            <option value="3">3 Nhân tố (Factors F1..F3)</option>
            <option value="4">4 Nhân tố (Factors F1..F4)</option>
            <option value="5">5 Nhân tố (Factors F1..F5)</option>
          </select>
        </div>
      </div>

      {/* Instruments Multi-select Checklist */}
      <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-lg border border-slate-200 dark:border-slate-750 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Database className="w-4 h-4 text-teal-500" />
            Tập biến công cụ ứng viên (Candidate Instruments Z_1..Z_K) · Đã chọn: {selectedInstruments.length} biến:
          </span>
          <div className="flex items-center gap-2 text-[11px]">
            <button
              onClick={handleSelectAllInstruments}
              className="text-teal-600 dark:text-teal-400 hover:underline font-medium"
            >
              Chọn tất cả
            </button>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <button
              onClick={handleClearInstruments}
              className="text-slate-500 hover:underline font-medium"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-36 overflow-y-auto p-1">
          {numericQuestions
            .filter(q => q.id !== outcomeQId && q.id !== treatmentQId)
            .map((q) => (
              <label
                key={q.id}
                className={`flex items-center gap-2 p-2 rounded-lg border text-xs cursor-pointer transition-colors ${
                  selectedInstruments.includes(q.id)
                    ? 'bg-teal-50 dark:bg-teal-950/40 border-teal-300 dark:border-teal-800 text-teal-900 dark:text-teal-200'
                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedInstruments.includes(q.id)}
                  onChange={() => handleToggleInstrument(q.id)}
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span className="truncate">{q.title}</span>
              </label>
            ))}
        </div>
      </div>

      {/* Covariates & Scope & Action */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Covariates */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Biến kiểm soát ngoại sinh X (Tùy chọn)
          </label>
          <div className="max-h-24 overflow-y-auto space-y-1 bg-slate-50 dark:bg-slate-800/50 p-2 rounded-lg border border-slate-200 dark:border-slate-700">
            {numericQuestions
              .filter(q => q.id !== outcomeQId && q.id !== treatmentQId && !selectedInstruments.includes(q.id))
              .map((q) => (
                <label key={q.id} className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCovariates.includes(q.id)}
                    onChange={() => handleToggleCovariate(q.id)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span className="truncate">{q.title}</span>
                </label>
              ))}
          </div>
        </div>

        {/* Scope */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Phạm vi dữ liệu (Scope)
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2"
          >
            <option value="all">Tất cả phản hồi hợp lệ (All)</option>
            <option value="verified_clean">Chỉ mẫu đã kiểm định sạch (Verified Clean)</option>
          </select>
        </div>

        {/* Run Button */}
        <div className="flex items-end justify-end">
          <button
            onClick={handleRun}
            disabled={loading}
            className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <RotateCcw className="w-4 h-4 animate-spin" />
                Đang trích xuất nhân tố &amp; chạy 2SLS...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Ước lượng Factor IV (PC-2SLS)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 rounded-lg text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && summary && (
        <div className="space-y-6 pt-4 border-t border-slate-200 dark:border-slate-800">
          {/* Key Metric Tiles */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Factor 2SLS &beta;_FIV
              </span>
              <span className={`text-lg font-bold ${summary.beta_factor_iv >= 0 ? 'text-teal-600 dark:text-teal-400' : 'text-amber-600 dark:text-amber-400'}`}>
                {summary.beta_factor_iv > 0 ? `+${summary.beta_factor_iv.toFixed(3)}` : summary.beta_factor_iv.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                SE: {summary.se_factor_iv.toFixed(3)} (p = {summary.p_value_factor_iv.toFixed(3)})
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                First-Stage F-Statistic
              </span>
              <span className={`text-lg font-bold ${summary.is_weak_instrument ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                F = {summary.first_stage_f_statistic.toFixed(1)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {summary.is_weak_instrument ? 'Công cụ yếu (< 10)' : 'Stock-Yogo Đạt (>= 10)'}
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Số Nhân tố Tối ưu (r*)
              </span>
              <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                r* = {summary.n_factors_r} / {summary.n_candidate_instruments_K}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Giải thích {summary.total_variance_explained_pct.toFixed(1)}% biến thiên
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Độ chệch OLS (Endogeneity)
              </span>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                &Delta; = {summary.endogeneity_gap.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Hausman p = {summary.hausman_p_value.toFixed(3)} ({summary.endogeneity_detected ? 'Nội sinh' : 'Ngoại sinh'})
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-750">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                Sargan Overid J-Test
              </span>
              <span className={`text-lg font-bold ${summary.overidentification_valid ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                {summary.overidentification_valid ? 'Hợp lệ (Pass)' : 'Nghi ngờ'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                J = {summary.sargan_j_statistic.toFixed(2)} (p = {summary.sargan_p_value.toFixed(3)})
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          {result.svg_visualization && (
            <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 p-2">
              <div
                dangerouslySetInnerHTML={{ __html: result.svg_visualization }}
                className="w-full flex justify-center"
              />
            </div>
          )}

          {/* Detailed Tables: Factor Loadings & Criteria */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Factor Summaries */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-teal-500" />
                Các Nhân tố Trích xuất (Extracted Factor Instruments)
              </h4>
              <div className="space-y-3">
                {result.factor_summaries?.map((fac, idx) => (
                  <div key={idx} className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-teal-600 dark:text-teal-400">{fac.factor_name}</span>
                      <span className="font-mono text-slate-500">
                        Eigenvalue: {fac.eigenvalue.toFixed(2)} ({fac.variance_explained_pct.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
                      <span className="font-medium text-slate-700 dark:text-slate-300">Biến đóng góp mạnh nhất:</span>{' '}
                      {fac.top_loading_instruments.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Bai-Ng Selection Table */}
            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-750">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-3">
                <BarChart2 className="w-4 h-4 text-indigo-500" />
                Tiêu chuẩn Lựa chọn Số lượng Nhân tố (Bai &amp; Ng 2002 Criteria)
              </h4>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-750 text-slate-600 dark:text-slate-300 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2">k</th>
                      <th className="p-2 text-right">V(k)</th>
                      <th className="p-2 text-right">IC_p1</th>
                      <th className="p-2 text-right">PC_p1</th>
                      <th className="p-2 text-right">Var %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {result.criteria_table?.map((row, idx) => (
                      <tr
                        key={idx}
                        className={`hover:bg-slate-100/50 dark:hover:bg-slate-700/40 ${
                          row.k === summary.n_factors_r ? 'bg-teal-50/60 dark:bg-teal-950/30 font-semibold' : ''
                        }`}
                      >
                        <td className="p-2">
                          k = {row.k} {row.k === summary.n_factors_r && <span className="text-teal-600 text-[10px] ml-1">(Opt)</span>}
                        </td>
                        <td className="p-2 text-right font-mono">{row.v_k.toFixed(3)}</td>
                        <td className="p-2 text-right font-mono text-teal-600 dark:text-teal-400">{row.ic_p1.toFixed(3)}</td>
                        <td className="p-2 text-right font-mono text-slate-500">{row.pc_p1.toFixed(3)}</td>
                        <td className="p-2 text-right font-mono">{row.variance_explained_pct.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* APA Narrative Block */}
          {result.apa_narrative && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-teal-500" />
                  Bản tường trình Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={handleCopyAPA}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-600 dark:text-teal-400 hover:underline"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-serif italic">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
