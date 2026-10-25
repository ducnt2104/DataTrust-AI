import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  CheckCircle2,
  Copy,
  FolderTree,
  GitCommit,
  Info,
  Layers,
  LineChart,
  PieChart,
  RefreshCw,
  Sliders,
  Sparkles,
  Table,
  TrendingUp,
  Users
} from 'lucide-react';
import { api } from '../api/client';
import {
  LCAAnalysisResult,
  LCAClassProfile,
  LCAModelComparisonItem
} from '../types/survey';

interface QuestionItem {
  id: string;
  title: string;
  question_type: string;
}

interface LatentClassAnalysisCardProps {
  surveyId: string;
  questions: QuestionItem[];
}

export const LatentClassAnalysisCard: React.FC<LatentClassAnalysisCardProps> = ({ surveyId, questions }) => {
  const eligibleQuestions = questions.filter(q =>
    ['single_choice', 'dropdown', 'radio', 'rating', 'likert', 'boolean'].includes(q.question_type)
  );

  const [selectedItemQIds, setSelectedItemQIds] = useState<string[]>(
    eligibleQuestions.slice(0, 4).map(q => q.id)
  );
  const [numClasses, setNumClasses] = useState<string>('auto');
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');
  const [activeTab, setActiveTab] = useState<'profile' | 'probabilities' | 'fit'>('profile');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LCAAnalysisResult | null>(null);
  const [copied, setCopied] = useState(false);

  const handleToggleItem = (qId: string) => {
    if (selectedItemQIds.includes(qId)) {
      setSelectedItemQIds(selectedItemQIds.filter(id => id !== qId));
    } else {
      setSelectedItemQIds([...selectedItemQIds, qId]);
    }
  };

  const handleRunAnalysis = async () => {
    if (selectedItemQIds.length < 3) {
      setError('Vui lòng chọn tối thiểu 3 câu hỏi chỉ báo để phân tích Lớp Ẩn LCA.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.runLCAAnalysis(surveyId, {
        item_question_ids: selectedItemQIds,
        num_classes: numClasses === 'auto' ? null : parseInt(numClasses, 10),
        scope
      });

      if (res.status === 'INSUFFICIENT_SAMPLE' || res.status === 'INSUFFICIENT_ITEMS' || res.status === 'INVALID_CATEGORIES') {
        setError(res.message || 'Chưa đủ dữ liệu mẫu hoặc số chỉ báo để ước lượng mô hình LCA.');
        setResult(null);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Không thể thực thi phân tích mô hình lớp ẩn LCA.');
    } finally {
      setLoading(false);
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
            <span className="p-2 bg-purple-50 text-purple-600 rounded-xl">
              <FolderTree className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-bold text-slate-800">
              Phân tích Lớp Ẩn (Latent Class Analysis - LCA)
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-purple-100 text-purple-700">
              Goodman 1974 · McLachlan 2000
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Mô hình hỗn hợp hữu hạn (Finite Mixture Modeling) phân đoạn người trả lời thành các phân khúc tiềm ẩn chưa quan sát được (latent typologies). 
            Ước lượng tỷ lệ phân bố lớp (prevalences), xác suất phản hồi có điều kiện, và tối ưu hóa số lớp qua tiêu chuẩn BIC và Entropy.
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading || selectedItemQIds.length < 3}
          className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-semibold shadow-sm transition-all shadow-purple-200"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Đang ước lượng LCA...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Ước lượng Lớp Ẩn LCA
            </>
          )}
        </button>
      </div>

      {/* Parameter Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50/70 p-4 rounded-xl border border-slate-200/70">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Số lớp phân đoạn (K Classes)
          </label>
          <select
            value={numClasses}
            onChange={(e) => setNumClasses(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="auto">Tự động tối ưu hóa (Duyệt K=2..4 theo BIC)</option>
            <option value="2">2 Lớp ẩn (K = 2)</option>
            <option value="3">3 Lớp ẩn (K = 3)</option>
            <option value="4">4 Lớp ẩn (K = 4)</option>
            <option value="5">5 Lớp ẩn (K = 5)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Phạm vi dữ liệu
          </label>
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full text-xs rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">Toàn bộ phản hồi</option>
            <option value="verified_clean">Đã làm sạch chống gian lận (Verified Clean)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Các câu hỏi chỉ báo phân đoạn ({selectedItemQIds.length} đã chọn) <span className="text-rose-500">*</span>
          </label>
          <div className="max-h-24 overflow-y-auto space-y-1 bg-white p-2 border border-slate-200 rounded-lg text-xs">
            {eligibleQuestions.map(q => (
              <label key={q.id} className="flex items-center gap-1.5 cursor-pointer hover:bg-slate-50 p-0.5 rounded">
                <input
                  type="checkbox"
                  checked={selectedItemQIds.includes(q.id)}
                  onChange={() => handleToggleItem(q.id)}
                  className="rounded text-purple-600 focus:ring-purple-500"
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
            {/* Optimal Classes Card */}
            <div className="bg-gradient-to-br from-purple-50/70 to-purple-100/30 border border-purple-200/80 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-purple-800">Số Lớp Tối ưu (K*)</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-200 text-purple-800">
                  Min BIC
                </span>
              </div>
              <div className="text-2xl font-extrabold text-purple-950 mt-2">
                K = {result.optimal_classes_count} Lớp Ẩn
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                Phân rã tốt nhất cấu trúc không quan sát được của dữ liệu
              </p>
            </div>

            {/* Entropy Quality Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Độ Phân tách Lớp (Entropy)</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  (result.entropy || 0) >= 0.80
                    ? 'bg-emerald-100 text-emerald-700'
                    : (result.entropy || 0) >= 0.60
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-rose-100 text-rose-700'
                }`}>
                  {result.entropy_quality}
                </span>
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                E = {result.entropy?.toFixed(3) || '--'}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Ngưỡng chuẩn Celeux-Soromenho: E ≥ 0.80 thể hiện phân lớp rõ rệt
              </p>
            </div>

            {/* Sample & Indicators Count */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Quy mô Mẫu & Chỉ báo</span>
                <Users className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mt-2">
                N = {result.sample_size}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {result.items_count} câu hỏi chỉ báo đa mức độ
              </p>
            </div>

            {/* Class Prevalences Breakdown Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Tỷ lệ Phân đoạn</span>
                <PieChart className="w-4 h-4 text-purple-500" />
              </div>
              <div className="flex items-center gap-2 mt-2">
                {result.class_profiles?.map((p) => (
                  <div key={p.class_index} className="flex-1">
                    <div className="text-xs font-bold text-slate-800">{p.prevalence_pct}%</div>
                    <div
                      className="h-1.5 rounded-full mt-1"
                      style={{ backgroundColor: p.color }}
                    ></div>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-slate-500 mt-2">
                Phân bổ xác suất tiền nghiệm (Prior Prevalences)
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200">
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'profile'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <LineChart className="w-3.5 h-3.5" />
              Hồ sơ Phân đoạn Lớp (Latent Profile Plot)
            </button>
            <button
              onClick={() => setActiveTab('probabilities')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'probabilities'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              Ma trận Xác suất Điều kiện (Item Probabilities)
            </button>
            <button
              onClick={() => setActiveTab('fit')}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'fit'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              So sánh Chỉ số Tiêu chuẩn (AIC / BIC / SABIC)
            </button>
          </div>

          {/* Tab 1: Profile Plot Vector SVG */}
          {activeTab === 'profile' && (
            <div className="space-y-4">
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <div className="flex items-center justify-between mb-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-purple-400"></span>
                    <span className="text-slate-200 font-semibold">
                      Đồ thị Tọa độ Song song Hồ sơ Xác suất của từng Lớp Ẩn (Profile Plot)
                    </span>
                  </div>
                  <span className="text-slate-400 text-[11px]">Trục Y: Xác suất chọn [0.0 - 1.0]</span>
                </div>

                {result.svg_profile_plot && (
                  <div
                    dangerouslySetInnerHTML={{ __html: result.svg_profile_plot }}
                    className="w-full overflow-x-auto"
                  />
                )}

                {/* Class Legend */}
                <div className="flex flex-wrap gap-3 mt-4 pt-3 border-t border-slate-800">
                  {result.class_profiles?.map((p) => (
                    <div
                      key={p.class_index}
                      className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/80 rounded-lg text-xs"
                    >
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: p.color }}
                      ></span>
                      <span className="text-slate-200 font-semibold">{p.class_name}</span>
                      <span className="text-purple-300 font-mono font-bold">{p.prevalence_pct}%</span>
                      <span className="text-slate-400 text-[10px]">(n = {p.assigned_count})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Item Probabilities Matrix */}
          {activeTab === 'probabilities' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.class_profiles?.map((p) => (
                <div key={p.class_index} className="border border-slate-200 rounded-xl overflow-hidden">
                  <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: p.color }}
                      ></span>
                      <h4 className="text-xs font-bold text-slate-800">{p.class_name}</h4>
                    </div>
                    <span className="text-xs font-extrabold text-purple-700">
                      {p.prevalence_pct}% (n = {p.assigned_count})
                    </span>
                  </div>

                  <div className="p-3 space-y-3">
                    {Object.entries(p.item_probabilities).map(([itemName, catDict]) => (
                      <div key={itemName} className="space-y-1.5 border-b border-slate-100 last:border-0 pb-2">
                        <span className="text-xs font-semibold text-slate-700 block truncate">
                          {itemName}
                        </span>
                        <div className="space-y-1">
                          {Object.entries(catDict).map(([cat, prob]) => (
                            <div key={cat} className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-500 truncate max-w-[160px]">{cat}:</span>
                              <div className="flex items-center gap-2">
                                <div className="w-20 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                  <div
                                    className="h-1.5 rounded-full"
                                    style={{
                                      width: `${prob * 100}%`,
                                      backgroundColor: p.color
                                    }}
                                  ></div>
                                </div>
                                <span className="font-mono text-slate-700 w-9 text-right font-semibold">
                                  {(prob * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 3: Model Selection Fit Table */}
          {activeTab === 'fit' && (
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
                <h4 className="text-xs font-bold text-slate-800">
                  Bảng So sánh Tiêu chuẩn Thông tin giữa các Mô hình Lớp Ẩn (Model Enumeration)
                </h4>
                <p className="text-[11px] text-slate-500">
                  Giải pháp có BIC thấp nhất và Entropy cao nhất được ưu tiên lựa chọn theo khuyến nghị học thuật.
                </p>
              </div>
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Số lớp (K)</th>
                    <th className="py-2.5 px-3">Log-Likelihood</th>
                    <th className="py-2.5 px-3">Số tham số (P)</th>
                    <th className="py-2.5 px-3">AIC</th>
                    <th className="py-2.5 px-3">BIC (Schwarz)</th>
                    <th className="py-2.5 px-3">SABIC</th>
                    <th className="py-2.5 px-3">Entropy (E)</th>
                    <th className="py-2.5 px-3">Đánh giá</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {result.model_selection_criteria?.map((m) => {
                    const isOptimal = m.num_classes === result.optimal_classes_count;
                    return (
                      <tr key={m.num_classes} className={isOptimal ? 'bg-purple-50/60 font-semibold' : 'hover:bg-slate-50/50'}>
                        <td className="py-2 px-3 flex items-center gap-1.5">
                          {isOptimal && <Award className="w-3.5 h-3.5 text-purple-600" />}
                          K = {m.num_classes} Lớp
                        </td>
                        <td className="py-2 px-3 font-mono">{m.log_likelihood}</td>
                        <td className="py-2 px-3">{m.num_parameters}</td>
                        <td className="py-2 px-3 font-mono">{m.aic}</td>
                        <td className={`py-2 px-3 font-mono ${isOptimal ? 'text-purple-700 font-bold' : ''}`}>
                          {m.bic}
                        </td>
                        <td className="py-2 px-3 font-mono">{m.sabic}</td>
                        <td className="py-2 px-3 font-mono">
                          <span className={m.entropy >= 0.8 ? 'text-emerald-700' : 'text-slate-700'}>
                            {m.entropy}
                          </span>
                        </td>
                        <td className="py-2 px-3">
                          {isOptimal ? (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-200 text-purple-800">
                              Tối ưu nhất (Best Fit)
                            </span>
                          ) : (
                            <span className="text-[10px] text-slate-400">Tham chiếu</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* APA 7th Edition Narrative */}
          {result.apa_narrative && (
            <div className="p-4 bg-purple-50/40 border border-purple-100 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-purple-950 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition
                </span>
                <button
                  onClick={() => copyToClipboard(result.apa_narrative || '')}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-white hover:bg-purple-50 border border-purple-200 text-purple-700 rounded-lg text-xs font-semibold shadow-xs transition-all"
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
              <p className="text-xs text-slate-700 leading-relaxed italic bg-white/80 p-3 rounded-lg border border-purple-100">
                "{result.apa_narrative}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
