import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  Binary,
  CheckCircle2,
  Compass,
  Copy,
  Cpu,
  Layers,
  LineChart,
  RefreshCw,
  Sliders,
  Sparkles,
  Zap
} from 'lucide-react';
import { api } from '../api/client';
import {
  IRT4PLAnalysisResult
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface IRT4PLAnalysisCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const IRT4PLAnalysisCard: React.FC<IRT4PLAnalysisCardProps> = ({
  surveyId,
  questions
}) => {
  const [selectedQIds, setSelectedQIds] = useState<string[]>([]);
  const [modelType, setModelType] = useState<'3pl' | '4pl'>('4pl');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IRT4PLAnalysisResult | null>(null);
  const [copiedApa, setCopiedApa] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'curves' | 'parameters' | 'tif' | 'cat'>('curves');

  const eligibleQuestions = questions.filter((q) =>
    ['rating', 'linear_scale', 'nps', 'number', 'single_choice'].includes(q.question_type)
  );

  const handleToggleQuestion = (qid: string) => {
    if (selectedQIds.includes(qid)) {
      setSelectedQIds(selectedQIds.filter((id) => id !== qid));
    } else {
      setSelectedQIds([...selectedQIds, qid]);
    }
  };

  const handleSelectAll = () => {
    setSelectedQIds(eligibleQuestions.map((q) => q.id));
  };

  const handleClearAll = () => {
    setSelectedQIds([]);
  };

  const handleRunAnalysis = async () => {
    if (selectedQIds.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 câu hỏi để phân tích mô hình IRT.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.runIRT4PLAnalysis(surveyId, {
        question_ids: selectedQIds,
        model_type: modelType,
        scope
      });
      if (res.status !== 'SUCCESS') {
        setError(res.message || 'Không thể ước lượng mô hình IRT 3PL/4PL.');
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi ước lượng mô hình IRT.');
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

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
      {/* Header */}
      <div className="p-6 bg-gradient-to-r from-violet-900 via-purple-900 to-slate-900 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-violet-700/60 rounded-lg border border-violet-500/40">
              <Binary className="w-6 h-6 text-violet-200" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-xl font-bold tracking-tight">
                  Lý thuyết Ứng đáp Câu hỏi 3PL & 4PL (Item Response Theory)
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-500/30 text-violet-200 border border-violet-400/30">
                  Birnbaum 1968 • Lord 1980 • Magis 2013
                </span>
              </div>
              <p className="text-sm text-violet-200/80 mt-1">
                Ước lượng độ phân biệt (a), độ khó (b), đoán mò (c) và bất cẩn (d), kèm Hàm thông tin bài test (TIF) và mô phỏng thích ứng CAT.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex bg-violet-950/60 p-1 rounded-lg border border-violet-700/50 text-xs">
              <button
                type="button"
                onClick={() => setModelType('4pl')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  modelType === '4pl'
                    ? 'bg-violet-600 text-white shadow-sm'
                    : 'text-violet-300 hover:text-white'
                }`}
              >
                Mô hình 4PL (a,b,c,d)
              </button>
              <button
                type="button"
                onClick={() => setModelType('3pl')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  modelType === '3pl'
                    ? 'bg-violet-600 text-white shadow-sm'
                    : 'text-violet-300 hover:text-white'
                }`}
              >
                Mô hình 3PL (d=1.0)
              </button>
            </div>

            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={loading || selectedQIds.length < 2}
              className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white font-medium text-sm rounded-lg transition shadow-sm"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Đang ước lượng…' : `Ước lượng ${modelType.toUpperCase()}`}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Question Selection Checklist */}
      <div className="p-6 border-b border-slate-200 bg-slate-50/70">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-700">
            <Sliders className="w-3.5 h-3.5 text-violet-600" />
            <span>Chọn các câu hỏi đưa vào kiểm định IRT ({selectedQIds.length} đã chọn):</span>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <button
              type="button"
              onClick={handleSelectAll}
              className="text-violet-600 hover:text-violet-700 font-medium transition"
            >
              Chọn tất cả
            </button>
            <span className="text-slate-300">|</span>
            <button
              type="button"
              onClick={handleClearAll}
              className="text-slate-500 hover:text-rose-600 font-medium transition"
            >
              Bỏ chọn
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {eligibleQuestions.map((q) => {
            const isChecked = selectedQIds.includes(q.id);
            return (
              <label
                key={`q-${q.id}`}
                className={`flex items-start space-x-2.5 p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                  isChecked
                    ? 'bg-violet-50/80 border-violet-300 text-violet-950 font-medium'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => handleToggleQuestion(q.id)}
                  className="rounded text-violet-600 focus:ring-violet-500 mt-0.5"
                />
                <span className="line-clamp-2">{q.title}</span>
              </label>
            );
          })}
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 mx-6 mt-6 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg flex items-start space-x-3 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Thông báo từ động cơ IRT:</span> {error}
          </div>
        </div>
      )}

      {/* Results View */}
      {result && result.status === 'SUCCESS' && (
        <div className="p-6 space-y-6">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs font-medium text-slate-500 block">Cỡ mẫu & Số câu hỏi</span>
              <span className="text-xl font-bold text-slate-900 mt-1 block">
                N = {result.sample_size} <span className="text-xs font-normal text-slate-500">({result.items_count} items)</span>
              </span>
            </div>

            <div className="p-4 bg-violet-50/70 rounded-xl border border-violet-200">
              <span className="text-xs font-medium text-violet-700 block">Mô hình & Ngưỡng nhị phân</span>
              <span className="text-xl font-bold text-violet-900 mt-1 block">
                {result.model_type} <span className="text-xs font-normal text-violet-700">(≥ {result.binarization_threshold})</span>
              </span>
            </div>

            <div className="p-4 bg-emerald-50/70 rounded-xl border border-emerald-200">
              <span className="text-xs font-medium text-emerald-700 block">Đỉnh Thông tin TIF (I_max)</span>
              <span className="text-xl font-bold text-emerald-900 mt-1 block">
                {result.test_information_function?.peak_information.toFixed(2)}{' '}
                <span className="text-xs font-normal text-emerald-700">
                  (tại θ = {(result.test_information_function?.peak_theta ?? 0) > 0 ? '+' : ''}{result.test_information_function?.peak_theta})
                </span>
              </span>
            </div>

            <div className="p-4 bg-indigo-50/70 rounded-xl border border-indigo-200">
              <span className="text-xs font-medium text-indigo-700 block">Sai số Đo lường Nhỏ nhất (SE_min)</span>
              <span className="text-xl font-bold text-indigo-900 mt-1 block">
                {result.test_information_function?.minimum_standard_error.toFixed(3)}
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-slate-200 flex space-x-6 text-sm font-medium">
            <button
              type="button"
              onClick={() => setActiveTab('curves')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'curves'
                  ? 'border-b-2 border-violet-600 text-violet-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <LineChart className="w-4 h-4" />
              <span>Đường cong Đặc trưng ICC</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('parameters')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'parameters'
                  ? 'border-b-2 border-violet-600 text-violet-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Sliders className="w-4 h-4" />
              <span>Tham số Câu hỏi ({result.items_parameters?.length || 0})</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('tif')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'tif'
                  ? 'border-b-2 border-violet-600 text-violet-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Hàm Thông tin Bài Test (TIF)</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('cat')}
              className={`pb-3 transition flex items-center space-x-1.5 ${
                activeTab === 'cat'
                  ? 'border-b-2 border-violet-600 text-violet-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Mô phỏng Thích ứng CAT</span>
            </button>
          </div>

          {/* Tab Content: ICC Curves SVG */}
          {activeTab === 'curves' && result.svg_curves && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Đường cong đặc trưng câu hỏi (Item Characteristic Curves - ICC):</span>
                <span className="text-2xs bg-violet-50 text-violet-800 border border-violet-200 px-2 py-0.5 rounded">
                  Mô hình {result.model_type} Logistic với D = 1.702
                </span>
              </div>
              <div
                className="w-full bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs p-2 flex justify-center"
                dangerouslySetInnerHTML={{ __html: result.svg_curves }}
              />
            </div>
          )}

          {/* Tab Content: Item Parameters Table */}
          {activeTab === 'parameters' && result.items_parameters && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold text-slate-600">Câu hỏi</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">Tỷ lệ đúng</th>
                    <th className="px-3 py-2 text-right font-semibold text-violet-700 font-bold">Phân biệt (a)</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-700 font-bold">Độ khó (b)</th>
                    <th className="px-3 py-2 text-right font-semibold text-amber-700 font-bold">Đoán mò (c)</th>
                    <th className="px-3 py-2 text-right font-semibold text-rose-700 font-bold">Bất cẩn (d)</th>
                    <th className="px-3 py-2 text-center font-semibold text-slate-600">Phân loại chất lượng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.items_parameters.map((it, idx) => (
                    <tr key={`it-${idx}`} className="hover:bg-slate-50/80">
                      <td className="px-3 py-2.5 font-medium text-slate-900">{it.item_name}</td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-600">
                        {(it.proportion_correct * 100).toFixed(1)}%
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-bold text-violet-700 text-sm">
                        {it.discrimination_a.toFixed(3)}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-bold text-slate-800">
                        {it.difficulty_b > 0 ? '+' : ''}{it.difficulty_b.toFixed(3)}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono text-amber-700">
                        {it.guessing_c.toFixed(3)}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono text-rose-700">
                        {it.inattention_d.toFixed(3)}
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-2xs font-semibold ${
                            it.discrimination_a >= 1.35
                              ? 'bg-emerald-100 text-emerald-800'
                              : it.discrimination_a >= 0.8
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {it.quality_tier}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab Content: TIF Table */}
          {activeTab === 'tif' && result.test_information_function && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-slate-600">Năng lực ngầm (θ)</th>
                      <th className="px-3 py-2 text-right font-semibold text-emerald-700 font-bold">Lượng Thông tin I(θ)</th>
                      <th className="px-3 py-2 text-right font-semibold text-slate-700">Sai số chuẩn SE(θ)</th>
                      <th className="px-3 py-2 text-right font-semibold text-indigo-700 font-bold">Độ tin cậy R(θ)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.test_information_function.theta_grid.map((th, idx) => {
                      const infoVal = result.test_information_function?.information_values[idx] || 0;
                      const seVal = result.test_information_function?.standard_errors[idx] || 0;
                      const relVal = result.test_information_function?.conditional_reliabilities[idx] || 0;
                      return (
                        <tr key={`tif-row-${idx}`} className="hover:bg-slate-50/80">
                          <td className="px-3 py-2 font-mono font-medium text-slate-800">
                            {th > 0 ? '+' : ''}{th.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono font-bold text-emerald-700">
                            {infoVal.toFixed(3)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono text-slate-600">{seVal.toFixed(3)}</td>
                          <td className="px-3 py-2 text-right font-mono font-bold text-indigo-700">
                            {(relVal * 100).toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Content: CAT Adaptive Simulation */}
          {activeTab === 'cat' && result.cat_simulation && (
            <div className="space-y-4">
              <div className="p-3 bg-violet-50/60 rounded-lg border border-violet-200 text-xs text-violet-900 flex items-center justify-between">
                <span>
                  Mô phỏng quy trình kiểm tra thích ứng máy tính (CAT): Tự động chọn câu hỏi tối đa hóa thông tin Fisher I(θ)
                </span>
                <span className="text-2xs font-semibold px-2 py-0.5 rounded bg-violet-200/80 text-violet-950">
                  θ_thực_tế = +0.50
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-3 py-2 text-center font-semibold text-slate-600">Bước (Step)</th>
                      <th className="px-3 py-2 text-left font-semibold text-slate-600">Câu hỏi được chọn tối ưu</th>
                      <th className="px-3 py-2 text-right font-semibold text-slate-600">Độ khó câu (b)</th>
                      <th className="px-3 py-2 text-center font-semibold text-slate-600">Kết quả thí sinh</th>
                      <th className="px-3 py-2 text-right font-semibold text-violet-700 font-bold">Năng lực sơ bộ (θ)</th>
                      <th className="px-3 py-2 text-right font-semibold text-emerald-700 font-bold">Sai số SE(θ)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.cat_simulation.map((step) => (
                      <tr key={`cat-${step.step}`} className="hover:bg-slate-50/80">
                        <td className="px-3 py-2 text-center font-bold text-slate-700">{step.step}</td>
                        <td className="px-3 py-2 font-medium text-slate-900">{step.item_name}</td>
                        <td className="px-3 py-2 text-right font-mono text-slate-600">
                          {step.item_difficulty_b > 0 ? '+' : ''}{step.item_difficulty_b.toFixed(2)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-full text-2xs font-bold ${
                              step.simulated_response === 1
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {step.simulated_response === 1 ? 'Đúng (1)' : 'Sai (0)'}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right font-mono font-bold text-violet-700 text-sm">
                          {step.provisional_theta > 0 ? '+' : ''}{step.provisional_theta.toFixed(3)}
                        </td>
                        <td className="px-3 py-2 text-right font-mono font-bold text-emerald-700">
                          {step.measurement_se.toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* APA 7th Edition Narrative Box */}
          {result.apa_narrative && (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                  <Award className="w-4 h-4 text-violet-600" />
                  <span>Thuyết minh Đo lường Tâm lý Chuẩn APA 7th Edition</span>
                </span>
                <button
                  type="button"
                  onClick={handleCopyApa}
                  className="flex items-center space-x-1 text-xs text-violet-700 hover:text-violet-800 font-medium transition"
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
