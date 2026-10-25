import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Copy,
  DollarSign,
  Info,
  Layers,
  LineChart,
  Percent,
  Play,
  Plus,
  RefreshCw,
  ShoppingBag,
  Sliders,
  Sparkles,
  Trash2,
  TrendingUp,
  Zap
} from 'lucide-react';
import { api } from '../api/client';
import {
  ConjointAnalysisResult,
  ConjointImportanceItem,
  ConjointSimulationResult
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface ConjointAnalysisCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const ConjointAnalysisCard: React.FC<ConjointAnalysisCardProps> = ({ surveyId, questions }) => {
  const numericQuestions = questions.filter(q =>
    ['rating', 'linear_scale', 'nps', 'number'].includes(q.question_type)
  );

  const categoricalQuestions = questions.filter(q =>
    ['single_choice', 'dropdown', 'radio', 'likert', 'text'].includes(q.question_type)
  );

  const [ratingQId, setRatingQId] = useState<string>(numericQuestions[0]?.id || '');
  const [selectedAttrQIds, setSelectedAttrQIds] = useState<string[]>(
    categoricalQuestions.slice(0, 3).map(q => q.id)
  );
  const [priceQId, setPriceQId] = useState<string>('');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'importance' | 'part_worth' | 'wtp' | 'simulator'>('importance');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConjointAnalysisResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Market Simulator State
  const [simProfiles, setSimProfiles] = useState<Array<{ id: string; attributes: Record<string, string> }>>([
    { id: 'Phương án A', attributes: {} },
    { id: 'Phương án B', attributes: {} }
  ]);
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState<ConjointSimulationResult | null>(null);

  const handleToggleAttr = (qId: string) => {
    if (selectedAttrQIds.includes(qId)) {
      setSelectedAttrQIds(selectedAttrQIds.filter(id => id !== qId));
    } else {
      setSelectedAttrQIds([...selectedAttrQIds, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!ratingQId) {
      setError('Vui lòng chọn câu hỏi đánh giá mức độ ưa thích (Rating).');
      return;
    }
    if (selectedAttrQIds.length < 2) {
      setError('Vui lòng chọn tối thiểu 2 câu hỏi làm thuộc tính sản phẩm/chính sách.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runConjointAnalysis(surveyId, {
        rating_question_id: ratingQId,
        attribute_question_ids: selectedAttrQIds,
        price_question_id: priceQId || null,
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_ATTRIBUTES') {
        setError(res.message || 'Chưa đủ dữ liệu mẫu hoặc số thuộc tính để phân tích Conjoint.');
        setResult(null);
      } else {
        setResult(res);
        // Khởi tạo các giá trị mặc định cho simulator nếu có part_worth_utilities
        if (res.part_worth_utilities) {
          const attrs = Object.keys(res.part_worth_utilities);
          const initialProfA: Record<string, string> = {};
          const initialProfB: Record<string, string> = {};
          attrs.forEach(attr => {
            const levels = Object.keys(res.part_worth_utilities![attr]);
            if (levels.length > 0) {
              initialProfA[attr] = levels[0];
              initialProfB[attr] = levels[levels.length - 1];
            }
          });
          setSimProfiles([
            { id: 'Hồ sơ Sản phẩm A', attributes: initialProfA },
            { id: 'Hồ sơ Sản phẩm B', attributes: initialProfB }
          ]);
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích đánh đổi Conjoint.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    if (!result || !result.part_worth_utilities) return;
    try {
      setSimLoading(true);
      const simRes = await api.runConjointSimulation(surveyId, {
        rating_question_id: ratingQId,
        attribute_question_ids: selectedAttrQIds,
        candidate_profiles: simProfiles,
        scope
      });
      setSimResult(simRes);
    } catch (err: any) {
      setError(err?.message || 'Không thể mô phỏng thị phần lựa chọn.');
    } finally {
      setSimLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
              <ShoppingBag className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-bold text-slate-800">
              Phân tích Đánh đổi Lựa chọn Conjoint Analysis (CBC / DCE)
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-emerald-100 text-emerald-700">
              McFadden 1974 · Nobel 2000
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Ước lượng tiện ích từng phần (Part-Worth Utilities), xác định trọng số quyết định của từng thuộc tính (Relative Importance %), 
            ước tính độ sẵn sàng chi trả (Willingness to Pay - WTP), và mô phỏng thị phần cạnh tranh (Market Share Simulator).
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading || !ratingQId || selectedAttrQIds.length < 2}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-semibold shadow-sm transition-all shadow-emerald-200"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Đang ước lượng Conjoint...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Ước lượng Tiện ích Conjoint
            </>
          )}
        </button>
      </div>

      {/* Parameter Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-50/70 p-4 rounded-xl border border-slate-200/70">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Biến Đánh giá / Sở thích (Rating) <span className="text-rose-500">*</span>
          </label>
          <select
            value={ratingQId}
            onChange={(e) => setRatingQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {numericQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 32 ? q.title.slice(0, 32) + '...' : q.title} ({q.question_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Thuộc tính Giá (để tính WTP)
          </label>
          <select
            value={priceQId}
            onChange={(e) => setPriceQId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">-- Không có thuộc tính giá --</option>
            {categoricalQuestions.map(q => (
              <option key={q.id} value={q.id}>
                {q.title.length > 32 ? q.title.slice(0, 32) + '...' : q.title}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Phạm vi dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Đã làm sạch chống gian lận (Verified Clean)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Thuộc tính sản phẩm ({selectedAttrQIds.length} đã chọn)
          </label>
          <div className="max-h-24 overflow-y-auto space-y-1 bg-white p-2 border border-slate-200 rounded-lg text-xs">
            {categoricalQuestions.map(q => (
              <label key={q.id} className="flex items-center gap-1.5 cursor-pointer hover:bg-slate-50 p-0.5 rounded">
                <input
                  type="checkbox"
                  checked={selectedAttrQIds.includes(q.id)}
                  onChange={() => handleToggleAttr(q.id)}
                  className="rounded text-emerald-600 focus:ring-emerald-500"
                />
                <span className="truncate text-slate-700">{q.title}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Result presentation */}
      {result && result.status === 'SUCCESS' && (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Top Attribute Card */}
            <div className="bg-gradient-to-br from-emerald-50/70 to-emerald-100/30 border border-emerald-200/80 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-800">Yếu tố Chi phối Hàng đầu</span>
                <Award className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-xl font-extrabold text-emerald-950 mt-2 truncate">
                {result.importance_ranking?.[0]?.attribute || '--'}
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                Chiếm {result.importance_ranking?.[0]?.importance_pct}% tỷ trọng quyết định (Mức tốt nhất: {result.importance_ranking?.[0]?.best_level})
              </p>
            </div>

            {/* Model Fit R^2 Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Độ phù hợp Mô hình (R²)</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                  {result.model_fit?.fit_quality}
                </span>
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                {result.model_fit?.r_squared !== undefined ? `${(result.model_fit.r_squared * 100).toFixed(1)}%` : '--'}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                R² Hiệu chỉnh: {(result.model_fit?.adjusted_r_squared || 0) * 100}% | RMSE: {result.model_fit?.rmse}
              </p>
            </div>

            {/* Sample & Attributes Count */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Quy mô Thực nghiệm</span>
                <Layers className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                N = {result.sample_size}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {result.attributes_count} thuộc tính | {result.parameters_estimated} tham số tiện ích
              </p>
            </div>

            {/* Baseline Utility */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Tiện ích Cơ sở (Intercept)</span>
                <Zap className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                β₀ = {result.overall_utility_intercept?.toFixed(3) || '0.000'}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Điểm tiện ích trung bình khi hiệu ứng các thuộc tính bù trừ (Effects Coding = 0)
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200">
            <button
              onClick={() => setActiveTab('importance')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'importance'
                  ? 'border-emerald-600 text-emerald-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Tỷ trọng Độ Quan trọng (Relative Importance)
            </button>
            <button
              onClick={() => setActiveTab('part_worth')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'part_worth'
                  ? 'border-emerald-600 text-emerald-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              Tiện ích Từng phần (Part-Worth Utilities)
            </button>
            {result.willingness_to_pay && result.willingness_to_pay.length > 0 && (
              <button
                onClick={() => setActiveTab('wtp')}
                className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeTab === 'wtp'
                    ? 'border-emerald-600 text-emerald-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <DollarSign className="w-3.5 h-3.5" />
                Sẵn sàng Chi trả (WTP)
              </button>
            )}
            <button
              onClick={() => setActiveTab('simulator')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'simulator'
                  ? 'border-emerald-600 text-emerald-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Play className="w-3.5 h-3.5" />
              Mô phỏng Thị phần (Market Simulator)
            </button>
          </div>

          {/* Tab 1: Relative Importance */}
          {activeTab === 'importance' && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <h4 className="text-xs font-bold text-slate-800 mb-2">
                  Biểu đồ Phân bổ Độ Quan trọng Tương đối giữa các Thuộc tính (%)
                </h4>
                {result.svg_importance_chart && (
                  <div
                    dangerouslySetInnerHTML={{ __html: result.svg_importance_chart }}
                    className="w-full overflow-x-auto"
                  />
                )}
              </div>

              {/* Ranking Table */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Thứ hạng</th>
                      <th className="py-2.5 px-3">Thuộc tính</th>
                      <th className="py-2.5 px-3">Trọng số (%)</th>
                      <th className="py-2.5 px-3">Biên độ Tiện ích (Range)</th>
                      <th className="py-2.5 px-3">Mức Tối ưu Nhất</th>
                      <th className="py-2.5 px-3">Mức Kém Nhất</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {result.importance_ranking?.map((item, idx) => (
                      <tr key={item.attribute} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-bold text-slate-500">#{idx + 1}</td>
                        <td className="py-2 px-3 font-semibold text-slate-900">{item.attribute}</td>
                        <td className="py-2 px-3">
                          <span className="font-extrabold text-emerald-600">
                            {item.importance_pct}%
                          </span>
                        </td>
                        <td className="py-2 px-3">{item.range}</td>
                        <td className="py-2 px-3 font-medium text-emerald-700">
                          {item.best_level}
                        </td>
                        <td className="py-2 px-3 text-slate-500">{item.worst_level}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Part-Worth Utilities */}
          {activeTab === 'part_worth' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.part_worth_utilities &&
                Object.entries(result.part_worth_utilities).map(([attr, levels]) => (
                  <div key={attr} className="border border-slate-200 rounded-xl overflow-hidden">
                    <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800">{attr}</span>
                      <span className="text-[10px] font-semibold text-slate-500">
                        {Object.keys(levels).length} mức độ
                      </span>
                    </div>
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-100/50 text-slate-600 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-2 px-3">Mức độ (Level)</th>
                          <th className="py-2 px-3">Tiện ích Từng phần (β)</th>
                          <th className="py-2 px-3">Tác động</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {Object.entries(levels).map(([lvl, uVal]) => (
                          <tr key={lvl}>
                            <td className="py-2 px-3 font-medium text-slate-800">{lvl}</td>
                            <td className="py-2 px-3 font-mono font-semibold">
                              {uVal > 0 ? `+${uVal.toFixed(3)}` : uVal.toFixed(3)}
                            </td>
                            <td className="py-2 px-3">
                              {uVal > 0 ? (
                                <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                                  Tích cực (+)
                                </span>
                              ) : uVal < 0 ? (
                                <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700">
                                  Tiêu cực (-)
                                </span>
                              ) : (
                                <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                                  Trung hòa
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
            </div>
          )}

          {/* Tab 3: Willingness to Pay */}
          {activeTab === 'wtp' && result.willingness_to_pay && (
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
                <h4 className="text-xs font-bold text-slate-800">
                  Định giá Sẵn sàng Chi trả (Willingness-to-Pay - WTP; Hensher et al., 2005)
                </h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Giá trị gia tăng tương đương bằng tiền mà người tiêu dùng chấp nhận trả thêm để nâng cấp từng thuộc tính.
                </p>
              </div>
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Thuộc tính</th>
                    <th className="py-2.5 px-3">Mức độ</th>
                    <th className="py-2.5 px-3">Tiện ích β</th>
                    <th className="py-2.5 px-3">Định giá WTP Thặng dư</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {result.willingness_to_pay.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="py-2 px-3 font-semibold text-slate-900">{item.attribute}</td>
                      <td className="py-2 px-3">{item.level}</td>
                      <td className="py-2 px-3 font-mono">{item.part_worth.toFixed(3)}</td>
                      <td className="py-2 px-3">
                        <span className={`font-mono font-bold ${item.wtp_valuation >= 0 ? 'text-emerald-700' : 'text-rose-600'}`}>
                          {item.wtp_valuation >= 0 ? `+${item.wtp_valuation}` : item.wtp_valuation}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: Market Share Simulator */}
          {activeTab === 'simulator' && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">
                      Mô phỏng Thị phần Lựa chọn (Choice Share Market Simulator)
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      Thiết lập các cấu hình sản phẩm đối đầu để dự báo xác suất lựa chọn theo mô hình Logit.
                    </p>
                  </div>
                  <button
                    onClick={handleRunSimulation}
                    disabled={simLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition-all"
                  >
                    {simLoading ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Đang tính thị phần...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5" />
                        Chạy Mô phỏng
                      </>
                    )}
                  </button>
                </div>

                {/* Profiles Configuration */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {simProfiles.map((prof, pIdx) => (
                    <div key={prof.id} className="bg-white p-3 rounded-lg border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                        <span className="text-xs font-bold text-slate-800">{prof.id}</span>
                        <span className="text-[10px] font-semibold text-emerald-600">Phương án #{pIdx + 1}</span>
                      </div>
                      <div className="space-y-2">
                        {result.part_worth_utilities &&
                          Object.entries(result.part_worth_utilities).map(([attr, levels]) => (
                            <div key={attr} className="flex items-center justify-between gap-2 text-xs">
                              <span className="text-slate-600 truncate max-w-[120px]">{attr}:</span>
                              <select
                                value={prof.attributes[attr] || Object.keys(levels)[0]}
                                onChange={(e) => {
                                  const updated = [...simProfiles];
                                  updated[pIdx].attributes[attr] = e.target.value;
                                  setSimProfiles(updated);
                                }}
                                className="text-xs rounded border border-slate-300 bg-white py-1 px-1.5 text-slate-700 max-w-[180px]"
                              >
                                {Object.keys(levels).map(lvl => (
                                  <option key={lvl} value={lvl}>{lvl}</option>
                                ))}
                              </select>
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Simulation Output */}
              {simResult && simResult.market_shares && (
                <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
                  <h4 className="text-xs font-bold text-slate-800">
                    Kết quả Dự báo Thị phần (Forecasted Choice Shares)
                  </h4>
                  <div className="space-y-3">
                    {simResult.market_shares.map((share, idx) => (
                      <div key={share.profile_id} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-800">{share.profile_id}</span>
                          <span className="font-mono font-bold text-emerald-600">
                            {share.choice_share_pct}% (Tiện ích U = {share.total_utility})
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                          <div
                            className={`h-2.5 rounded-full transition-all ${
                              idx === 0 ? 'bg-emerald-600' : idx === 1 ? 'bg-indigo-600' : 'bg-amber-500'
                            }`}
                            style={{ width: `${share.choice_share_pct}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-emerald-50/40 border border-emerald-100 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-950 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative || '')}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-white hover:bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg text-xs font-semibold shadow-xs transition-all"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Đã sao chép!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Sao chép APA 7th
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic bg-white/80 p-3 rounded-lg border border-emerald-100">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
