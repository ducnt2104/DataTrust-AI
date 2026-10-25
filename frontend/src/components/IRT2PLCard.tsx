import React, { useState } from 'react';
import {
  Activity,
  Award,
  BarChart3,
  CheckCircle2,
  Copy,
  HelpCircle,
  Info,
  Layers,
  LineChart,
  RefreshCw,
  Sliders,
  Sparkles,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { api } from '../api/client';
import {
  IRT2PLAnalysisResult,
  IRTItemResult,
  IRTICCCurve
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface IRT2PLCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const IRT2PLCard: React.FC<IRT2PLCardProps> = ({ surveyId, questions }) => {
  const eligibleQuestions = questions.filter(q =>
    ['number', 'rating', 'nps', 'likert', 'linear_scale', 'single_choice', 'boolean'].includes(q.question_type)
  );

  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>(() =>
    eligibleQuestions.slice(0, 5).map(q => q.id)
  );
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [maxIter, setMaxIter] = useState<number>(35);
  const [activeTab, setActiveTab] = useState<'icc' | 'tif' | 'items' | 'traits'>('icc');
  const [focusedItemId, setFocusedItemId] = useState<string | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<IRT2PLAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const handleRunAnalysis = async () => {
    if (selectedQuestionIds.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 câu hỏi định lượng để ước lượng mô hình IRT 2PL.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.runIRT2PLAnalysis(surveyId, {
        question_ids: selectedQuestionIds,
        scope,
        max_em_iter: maxIter
      });
      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Không thể ước lượng mô hình IRT 2PL.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi hệ thống khi ước lượng mô hình IRT 2PL.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAPA = () => {
    if (!result?.apa_narrative) return;
    navigator.clipboard.writeText(result.apa_narrative);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleQuestionSelection = (qid: string) => {
    setSelectedQuestionIds(prev =>
      prev.includes(qid) ? prev.filter(id => id !== qid) : [...prev, qid]
    );
  };

  const selectAllEligible = () => {
    setSelectedQuestionIds(eligibleQuestions.map(q => q.id));
  };

  // Bảng màu cho các đường cong ICC của từng item
  const curveColors = [
    '#3b82f6', // Blue
    '#10b981', // Emerald
    '#f59e0b', // Amber
    '#8b5cf6', // Violet
    '#ec4899', // Pink
    '#06b6d4', // Cyan
    '#f97316', // Orange
    '#14b8a6'  // Teal
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
              <LineChart className="w-5 h-5" />
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Lý Thuyết Ứng Đáp Câu Hỏi 2 Tham Số Logistic (IRT 2PL & ICC)
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium border border-indigo-500/30">
              Birnbaum 1968
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Ước lượng độ phân biệt câu hỏi (<span className="text-indigo-400 font-semibold">a</span>), độ khó/ngưỡng ủng hộ (<span className="text-emerald-400 font-semibold">b</span>) qua thuật toán Marginal Maximum Likelihood EM (Bock & Aitkin, 1981), dựng Đường cong đặc trưng ICC và Hàm thông tin khảo sát TIF.
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading || selectedQuestionIds.length < 2}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium rounded-lg shadow-lg shadow-indigo-500/25 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Đang tính toán MML-EM...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Ước Lượng IRT 2PL</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration Controls */}
      <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-slate-300 font-medium">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <span>Chọn câu hỏi đưa vào mô hình đo lường ({selectedQuestionIds.length}/{eligibleQuestions.length})</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={selectAllEligible}
              className="text-xs text-indigo-400 hover:text-indigo-300 underline underline-offset-2"
            >
              Chọn tất cả
            </button>
            <span className="text-slate-600">|</span>
            <button
              onClick={() => setSelectedQuestionIds([])}
              className="text-xs text-slate-400 hover:text-slate-300 underline underline-offset-2"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        {/* Question Pills */}
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-1 custom-scrollbar">
          {eligibleQuestions.map(q => {
            const isSelected = selectedQuestionIds.includes(q.id);
            return (
              <button
                key={q.id}
                onClick={() => toggleQuestionSelection(q.id)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition text-left flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200'
                    : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:border-slate-600'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-indigo-400' : 'bg-slate-500'}`} />
                <span className="max-w-[200px] truncate">{q.title}</span>
              </button>
            );
          })}
        </div>

        {/* Scope and Iteration options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-800/60">
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400 font-medium">Phạm vi mẫu:</label>
            <select
              value={scope}
              onChange={e => setScope(e.target.value as any)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-2.5 py-1.5 focus:border-indigo-500 focus:outline-none"
            >
              <option value="all">Toàn bộ phản hồi (All responses)</option>
              <option value="verified_clean">Chỉ mẫu sạch đã kiểm định (Verified clean)</option>
            </select>
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400 font-medium">Số vòng lặp EM:</label>
            <input
              type="number"
              min={15}
              max={60}
              value={maxIter}
              onChange={e => setMaxIter(Math.max(15, Math.min(60, Number(e.target.value))))}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-2.5 py-1.5 w-20 focus:border-indigo-500 focus:outline-none"
            />
            <span className="text-xs text-slate-500">(15 - 60 iterations)</span>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg text-sm text-rose-300 flex items-start gap-2.5">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Empty State when no result yet */}
      {!result && !loading && !error && (
        <div className="p-10 border border-dashed border-slate-800 rounded-xl text-center space-y-3">
          <Activity className="w-10 h-10 mx-auto text-slate-600" />
          <h4 className="text-base font-semibold text-slate-300">Chưa có kết quả ước lượng IRT 2PL</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Chọn các câu hỏi thang đo ở trên và nhấp "Ước Lượng IRT 2PL" để chạy giải thuật Marginal Maximum Likelihood EM, tính toán độ phân biệt và độ khó câu hỏi.
          </p>
        </div>
      )}

      {/* Results Content */}
      {result && (
        <div className="space-y-6">
          {/* Hero KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Độ tin cậy biên IRT</span>
                <Award className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-black text-emerald-400">
                {result.marginal_reliability?.toFixed(3)}
              </div>
              <div className="text-[11px] text-slate-400">
                {result.marginal_reliability && result.marginal_reliability >= 0.8
                  ? '🌟 Xuất sắc (≥ 0.80)'
                  : result.marginal_reliability && result.marginal_reliability >= 0.7
                  ? '✅ Tốt (≥ 0.70)'
                  : '⚠️ Chấp nhận được'}
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Độ phân biệt TB (M_a)</span>
                <TrendingUp className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-black text-indigo-400">
                {result.average_discrimination?.toFixed(2)}
              </div>
              <div className="text-[11px] text-slate-400">
                {result.average_discrimination && result.average_discrimination >= 1.35
                  ? 'Cao (Baker 2001)'
                  : 'Trung bình (0.65 - 1.34)'}
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Độ khó TB (M_b)</span>
                <BarChart3 className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-black text-amber-400">
                {result.average_difficulty?.toFixed(2)}
              </div>
              <div className="text-[11px] text-slate-400">
                Thang chuẩn tắc [-3.0, +3.0]
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-1">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Vùng đo lường tối ưu</span>
                <Info className="w-4 h-4 text-violet-400" />
              </div>
              <div className="text-lg font-black text-violet-400">
                [{result.optimal_theta_range?.[0]}, {result.optimal_theta_range?.[1]}]
              </div>
              <div className="text-[11px] text-slate-400">
                Thông tin đỉnh TIF: {result.max_test_information?.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 gap-2">
            <button
              onClick={() => setActiveTab('icc')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition border-b-2 flex items-center gap-2 ${
                activeTab === 'icc'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <LineChart className="w-4 h-4" />
              <span>Đường Cong Đặc Trưng (ICC)</span>
            </button>
            <button
              onClick={() => setActiveTab('tif')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition border-b-2 flex items-center gap-2 ${
                activeTab === 'tif'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              <span>Hàm Thông Tin Khảo Sát (TIF)</span>
            </button>
            <button
              onClick={() => setActiveTab('items')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition border-b-2 flex items-center gap-2 ${
                activeTab === 'items'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Tham Số Câu Hỏi (a & b)</span>
            </button>
            <button
              onClick={() => setActiveTab('traits')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition border-b-2 flex items-center gap-2 ${
                activeTab === 'traits'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Phân Phối Năng Lực Ẩn (EAP)</span>
            </button>
          </div>

          {/* TAB 1: ICC CURVES */}
          {activeTab === 'icc' && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
                <span>Đường cong Item Characteristic Curve (P_i(θ) vs θ từ -3.5 đến +3.5)</span>
                <span className="text-slate-500">Nhấp vào câu hỏi bên dưới để làm nổi bật đường cong</span>
              </div>

              {/* Item Legend Filters */}
              <div className="flex flex-wrap gap-2">
                {result.icc_curves?.map((curve, idx) => {
                  const color = curveColors[idx % curveColors.length];
                  const isFocused = focusedItemId === curve.item_id;
                  return (
                    <button
                      key={curve.item_id}
                      onClick={() => setFocusedItemId(isFocused ? null : curve.item_id)}
                      className={`text-xs px-2.5 py-1 rounded border flex items-center gap-1.5 transition ${
                        isFocused
                          ? 'border-white bg-slate-800 text-white font-bold shadow-md'
                          : 'border-slate-800 bg-slate-950/60 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                      <span className="max-w-[160px] truncate">{curve.item_name}</span>
                    </button>
                  );
                })}
              </div>

              {/* Vector SVG Chart */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-x-auto">
                <svg viewBox="0 0 520 260" className="w-full max-w-2xl mx-auto h-auto">
                  {/* Grid Lines & Labels */}
                  {/* Y Axis Grid (0.0, 0.25, 0.5, 0.75, 1.0) */}
                  {[0.0, 0.25, 0.5, 0.75, 1.0].map(pVal => {
                    const y = 220 - pVal * 190;
                    return (
                      <g key={pVal}>
                        <line x1="50" y1={y} x2="490" y2={y} stroke="#334155" strokeDasharray="2 2" strokeWidth="0.8" />
                        <text x="42" y={y + 3} fill="#94a3b8" fontSize="9" textAnchor="end">
                          {pVal.toFixed(2)}
                        </text>
                      </g>
                    );
                  })}

                  {/* X Axis Grid (theta = -3, -2, -1, 0, 1, 2, 3) */}
                  {[-3, -2, -1, 0, 1, 2, 3].map(t => {
                    const x = 50 + ((t - (-3.5)) / 7.0) * 440;
                    return (
                      <g key={t}>
                        <line x1={x} y1="30" x2={x} y2="220" stroke="#334155" strokeDasharray="2 2" strokeWidth="0.8" />
                        <text x={x} y="235" fill="#94a3b8" fontSize="9" textAnchor="middle">
                          {t > 0 ? `+${t}` : t}
                        </text>
                      </g>
                    );
                  })}

                  {/* Axis Baseline */}
                  <line x1="50" y1="220" x2="490" y2="220" stroke="#64748b" strokeWidth="1.2" />
                  <line x1="50" y1="30" x2="50" y2="220" stroke="#64748b" strokeWidth="1.2" />

                  {/* Axis Titles */}
                  <text x="270" y="252" fill="#cbd5e1" fontSize="10" textAnchor="middle" fontWeight="600">
                    Năng Lực / Thái Độ Ẩn (Latent Trait θ)
                  </text>
                  <text x="18" y="125" fill="#cbd5e1" fontSize="10" textAnchor="middle" transform="rotate(-90, 18, 125)" fontWeight="600">
                    Xác Suất P(θ)
                  </text>

                  {/* ICC Paths */}
                  {result.icc_curves?.map((curve, idx) => {
                    const color = curveColors[idx % curveColors.length];
                    const isFocused = focusedItemId === curve.item_id;
                    const isOtherFocused = focusedItemId !== null && !isFocused;

                    return (
                      <g key={curve.item_id}>
                        <path
                          d={curve.svg_path}
                          fill="none"
                          stroke={color}
                          strokeWidth={isFocused ? 3.0 : 1.8}
                          opacity={isOtherFocused ? 0.25 : 1.0}
                          className="transition-all duration-200"
                        />
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          )}

          {/* TAB 2: TEST INFORMATION FUNCTION (TIF) */}
          {activeTab === 'tif' && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
                <span>Hàm Thông Tin Bài Khảo Sát TIF I(θ) và Sai Số Chuẩn SE(θ)</span>
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <span className="w-3 h-0.5 bg-emerald-400" /> Thông tin I(θ) (Trục trái)
                  </span>
                  <span className="flex items-center gap-1.5 text-rose-400">
                    <span className="w-3 h-0.5 border-t border-dashed border-rose-400" /> Sai số SE(θ) (Trục phải)
                  </span>
                </div>
              </div>

              {/* Vector SVG Chart for TIF & SE */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-x-auto">
                <svg viewBox="0 0 520 260" className="w-full max-w-2xl mx-auto h-auto">
                  {/* Optimal Zone Highlight */}
                  {result.optimal_theta_range && (
                    <rect
                      x={50 + ((result.optimal_theta_range[0] - (-3.5)) / 7.0) * 440}
                      y="30"
                      width={((result.optimal_theta_range[1] - result.optimal_theta_range[0]) / 7.0) * 440}
                      height="190"
                      fill="#10b981"
                      fillOpacity="0.08"
                    />
                  )}

                  {/* Grid Lines */}
                  {[0.0, 0.25, 0.5, 0.75, 1.0].map(pVal => {
                    const y = 220 - pVal * 190;
                    const maxTif = result.test_information_curve?.max_tif ?? 1.0;
                    return (
                      <g key={pVal}>
                        <line x1="50" y1={y} x2="490" y2={y} stroke="#334155" strokeDasharray="2 2" strokeWidth="0.8" />
                        <text x="42" y={y + 3} fill="#10b981" fontSize="9" textAnchor="end">
                          {(pVal * maxTif).toFixed(1)}
                        </text>
                        <text x="498" y={y + 3} fill="#f43f5e" fontSize="9" textAnchor="start">
                          {(pVal * 3.0).toFixed(1)}
                        </text>
                      </g>
                    );
                  })}

                  {/* X Axis Grid */}
                  {[-3, -2, -1, 0, 1, 2, 3].map(t => {
                    const x = 50 + ((t - (-3.5)) / 7.0) * 440;
                    return (
                      <g key={t}>
                        <line x1={x} y1="30" x2={x} y2="220" stroke="#334155" strokeDasharray="2 2" strokeWidth="0.8" />
                        <text x={x} y="235" fill="#94a3b8" fontSize="9" textAnchor="middle">
                          {t > 0 ? `+${t}` : t}
                        </text>
                      </g>
                    );
                  })}

                  {/* Baselines */}
                  <line x1="50" y1="220" x2="490" y2="220" stroke="#64748b" strokeWidth="1.2" />
                  <line x1="50" y1="30" x2="50" y2="220" stroke="#64748b" strokeWidth="1.2" />
                  <line x1="490" y1="30" x2="490" y2="220" stroke="#64748b" strokeWidth="1.2" />

                  {/* Paths */}
                  {result.test_information_curve && (
                    <>
                      <path
                        d={result.test_information_curve.tif_path}
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="2.5"
                      />
                      <path
                        d={result.test_information_curve.se_path}
                        fill="none"
                        stroke="#f43f5e"
                        strokeWidth="1.8"
                        strokeDasharray="4 3"
                      />
                    </>
                  )}

                  {/* Axis Title */}
                  <text x="270" y="252" fill="#cbd5e1" fontSize="10" textAnchor="middle" fontWeight="600">
                    Năng Lực / Thái Độ Ẩn (Latent Trait θ)
                  </text>
                </svg>
              </div>
            </div>
          )}

          {/* TAB 3: ITEM PARAMETERS TABLE */}
          {activeTab === 'items' && (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/40">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-slate-400 uppercase text-[11px] font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3">Mã & Câu Hỏi</th>
                    <th className="p-3 text-right">Tỷ Lệ Chọn (p)</th>
                    <th className="p-3 text-right">Độ Phân Biệt (a)</th>
                    <th className="p-3">Phân Loại Baker</th>
                    <th className="p-3 text-right">Độ Khó (b)</th>
                    <th className="p-3">Ngưỡng Khó</th>
                    <th className="p-3 text-right">Thông Tin Đỉnh</th>
                    <th className="p-3 text-center">Độ Phù Hợp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {result.items?.map(it => (
                    <tr key={it.item_id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3 font-sans text-slate-200">
                        <span className="font-bold text-indigo-400 mr-2">{it.item_id}</span>
                        {it.item_name}
                      </td>
                      <td className="p-3 text-right text-slate-300">{(it.endorsement_rate * 100).toFixed(1)}%</td>
                      <td className="p-3 text-right font-bold text-indigo-300">{it.discrimination_a.toFixed(2)}</td>
                      <td className="p-3 font-sans">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          it.discrimination_class === 'VERY_HIGH'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : it.discrimination_class === 'HIGH'
                            ? 'bg-blue-500/10 text-blue-300 border border-blue-500/20'
                            : 'bg-slate-700/30 text-slate-300'
                        }`}>
                          {it.discrimination_label}
                        </span>
                      </td>
                      <td className="p-3 text-right font-bold text-amber-300">{it.difficulty_b.toFixed(2)}</td>
                      <td className="p-3 font-sans">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                          {it.difficulty_label}
                        </span>
                      </td>
                      <td className="p-3 text-right text-slate-300">{it.peak_information.toFixed(2)}</td>
                      <td className="p-3 text-center font-sans">
                        {it.is_good_fit ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400 text-[10px]">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Phù hợp
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-400 text-[10px]">
                            <AlertTriangle className="w-3.5 h-3.5" /> Chú ý
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 4: PERSON TRAIT DISTRIBUTION (EAP) */}
          {activeTab === 'traits' && result.person_trait_summary && (
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-4">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                <span>Thống Kê Điểm Năng Lực / Thái Độ Ẩn (Expected A Posteriori - EAP θ)</span>
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-lg">
                  <div className="text-[11px] text-slate-400">Trung bình (M_θ)</div>
                  <div className="text-lg font-bold text-white">{result.person_trait_summary.mean_theta.toFixed(3)}</div>
                </div>
                <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-lg">
                  <div className="text-[11px] text-slate-400">Độ lệch chuẩn (SD_θ)</div>
                  <div className="text-lg font-bold text-white">{result.person_trait_summary.sd_theta.toFixed(3)}</div>
                </div>
                <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-lg">
                  <div className="text-[11px] text-slate-400">Điểm tối thiểu</div>
                  <div className="text-lg font-bold text-rose-400">{result.person_trait_summary.min_theta.toFixed(2)}</div>
                </div>
                <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-lg">
                  <div className="text-[11px] text-slate-400">Điểm tối đa</div>
                  <div className="text-lg font-bold text-emerald-400">{result.person_trait_summary.max_theta.toFixed(2)}</div>
                </div>
                <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-lg">
                  <div className="text-[11px] text-slate-400">Sai số chuẩn TB (SE_θ)</div>
                  <div className="text-lg font-bold text-indigo-400">{result.person_trait_summary.mean_se.toFixed(3)}</div>
                </div>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative Summary */}
          {result.apa_narrative && (
            <div className="bg-indigo-950/20 border border-indigo-500/20 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 bg-indigo-500/20 text-indigo-400 rounded">
                    <Sparkles className="w-4 h-4" />
                  </span>
                  <h4 className="text-sm font-bold text-white">Thuyết Minh Học Thuật Chuẩn APA 7th Edition</h4>
                </div>
                <button
                  onClick={handleCopyAPA}
                  className="flex items-center gap-1.5 px-3 py-1 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 rounded text-xs transition border border-indigo-500/30"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
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
              <p className="text-xs text-slate-300 leading-relaxed font-serif bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
                {result.apa_narrative}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
