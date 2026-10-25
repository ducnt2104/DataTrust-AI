import React, { useState } from 'react';
import {
  Sliders,
  Cpu,
  Layers,
  DollarSign,
  TrendingUp,
  BarChart3,
  Info,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  Plus,
  Trash2,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import { Question, ConjointHBResult } from '../types/survey';

interface ConjointHBCardProps {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type?: any }>;
}

export const ConjointHBCard: React.FC<ConjointHBCardProps> = ({ surveyId, questions }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConjointHBResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [scope, setScope] = useState<'all' | 'verified_clean'>('all');

  // Attribute configurations
  const [attributes, setAttributes] = useState<Array<{ name: string; levels: string[] }>>([
    { name: 'Thương hiệu', levels: ['Apple', 'Samsung', 'Xiaomi'] },
    { name: 'Bộ nhớ trong', levels: ['128GB', '256GB', '512GB'] },
    { name: 'Giá bán', levels: ['15 triệu', '20 triệu', '25 triệu'] }
  ]);

  const [priceAttribute, setPriceAttribute] = useState<string>('Giá bán');
  const [mcmcDraws, setMcmcDraws] = useState<number>(500);
  const [burnIn, setBurnIn] = useState<number>(150);
  const [activeTab, setActiveTab] = useState<'importance' | 'utilities' | 'wtp' | 'simulator' | 'svg'>('importance');

  // Presets
  const loadPreset = (preset: 'tech' | 'saas' | 'policy') => {
    if (preset === 'tech') {
      setAttributes([
        { name: 'Thương hiệu', levels: ['Apple', 'Samsung', 'Xiaomi'] },
        { name: 'Bộ nhớ trong', levels: ['128GB', '256GB', '512GB'] },
        { name: 'Giá bán', levels: ['15 triệu', '20 triệu', '25 triệu'] }
      ]);
      setPriceAttribute('Giá bán');
    } else if (preset === 'saas') {
      setAttributes([
        { name: 'Gói dịch vụ', levels: ['Cơ bản', 'Tiêu chuẩn', 'Doanh nghiệp'] },
        { name: 'Hỗ trợ kỹ thuật', levels: ['Email 24h', 'Hotline 24/7', 'Kỹ sư chuyên trách'] },
        { name: 'Giá thuê bao', levels: ['200k/tháng', '500k/tháng', '1200k/tháng'] }
      ]);
      setPriceAttribute('Giá thuê bao');
    } else {
      setAttributes([
        { name: 'Chính sách bảo hiểm', levels: ['BHYT công', 'Bảo hiểm hỗn hợp', 'Bảo hiểm quốc tế'] },
        { name: 'Mức trợ cấp', levels: ['50%', '75%', '100%'] },
        { name: 'Phí đóng góp', levels: ['100k/tháng', '250k/tháng', '500k/tháng'] }
      ]);
      setPriceAttribute('Phí đóng góp');
    }
  };

  const handleAddAttribute = () => {
    setAttributes(prev => [...prev, { name: `Thuộc tính ${prev.length + 1}`, levels: ['Mức 1', 'Mức 2'] }]);
  };

  const handleRemoveAttribute = (idx: number) => {
    setAttributes(prev => prev.filter((_, i) => i !== idx));
  };

  const handleUpdateLevels = (idx: number, levelsStr: string) => {
    const splitted = levelsStr.split(',').map(s => s.trim()).filter(Boolean);
    setAttributes(prev => prev.map((a, i) => i === idx ? { ...a, levels: splitted } : a));
  };

  const handleRunAnalysis = async () => {
    if (attributes.length < 2) {
      setError('Cần tối thiểu 2 thuộc tính để phân tích Conjoint HB.');
      return;
    }
    for (const a of attributes) {
      if (a.levels.length < 2) {
        setError(`Thuộc tính "${a.name}" cần tối thiểu 2 mức độ (levels).`);
        return;
      }
    }

    setLoading(true);
    setError(null);

    const config: Record<string, string[]> = {};
    attributes.forEach(a => {
      config[a.name] = a.levels;
    });

    try {
      const data = await api.runConjointHBAnalysis(surveyId, {
        attributes_config: config,
        price_attribute: priceAttribute && config[priceAttribute] ? priceAttribute : undefined,
        n_draws: mcmcDraws,
        burn_in: burnIn,
        scope
      });

      if (data.status !== 'SUCCESS') {
        setError(data.message || 'Phân tích Conjoint HB không thành công.');
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi kết nối khi chạy phân tích Conjoint HB.');
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
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Choice-Based Conjoint (CBC) with Hierarchical Bayes (HB)
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Rossi, Allenby &amp; McCulloch (2005)
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Mô hình Phân tích Đánh đổi Lựa chọn Đa thuộc tính &amp; Tiện ích Từng phần Ngẫu nhiên qua MCMC Bayes Phân tầng
              </p>
            </div>
          </div>
        </div>

        {/* Quick Presets */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Hồ sơ mẫu:</span>
          <button
            onClick={() => loadPreset('tech')}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            Smartphone
          </button>
          <button
            onClick={() => loadPreset('saas')}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            SaaS B2B
          </button>
          <button
            onClick={() => loadPreset('policy')}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            Bảo hiểm
          </button>
        </div>
      </div>

      {/* Config Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6">
        {/* Attributes & Levels Editor */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-indigo-400" />
              Cấu hình Thuộc tính &amp; Các Mức độ (Attributes &amp; Levels)
            </label>
            <button
              onClick={handleAddAttribute}
              className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition"
            >
              <Plus className="w-3.5 h-3.5" /> Thêm thuộc tính
            </button>
          </div>

          <div className="space-y-2.5">
            {attributes.map((attr, idx) => (
              <div key={idx} className="p-3 bg-slate-800/60 border border-slate-800 rounded-xl flex items-center gap-3">
                <input
                  type="text"
                  value={attr.name}
                  onChange={(e) => {
                    const val = e.target.value;
                    setAttributes(prev => prev.map((a, i) => i === idx ? { ...a, name: val } : a));
                  }}
                  className="w-1/3 px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500 font-medium"
                  placeholder="Tên thuộc tính"
                />
                <input
                  type="text"
                  value={attr.levels.join(', ')}
                  onChange={(e) => handleUpdateLevels(idx, e.target.value)}
                  className="flex-1 px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="Các mức độ (phân tách bởi dấu phẩy)"
                />
                {attributes.length > 2 && (
                  <button
                    onClick={() => handleRemoveAttribute(idx)}
                    className="p-1.5 text-slate-400 hover:text-rose-400 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Parameters & Scope */}
        <div className="space-y-4 bg-slate-800/40 border border-slate-800 p-4 rounded-xl">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-1.5">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              Thuộc tính Giá (để tính WTP)
            </label>
            <select
              value={priceAttribute}
              onChange={(e) => setPriceAttribute(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">-- Không chọn (Bỏ qua WTP) --</option>
              {attributes.map((a, i) => (
                <option key={i} value={a.name}>{a.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Số lượt MCMC</label>
              <input
                type="number"
                min={200}
                max={2000}
                step={100}
                value={mcmcDraws}
                onChange={(e) => setMcmcDraws(parseInt(e.target.value) || 500)}
                className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Lượt Burn-in</label>
              <input
                type="number"
                min={50}
                max={1000}
                step={50}
                value={burnIn}
                onChange={(e) => setBurnIn(parseInt(e.target.value) || 150)}
                className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Phạm vi phản hồi</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setScope('all')}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  scope === 'all'
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                Tất cả (All)
              </button>
              <button
                onClick={() => setScope('verified_clean')}
                className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                  scope === 'verified_clean'
                    ? 'bg-emerald-600/20 border-emerald-500 text-emerald-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                Đã làm sạch
              </button>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Đang chạy MCMC Bayes Phân tầng...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Ước lượng Conjoint HB (MCMC)
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
          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Hit Rate (Chính xác)</span>
              <span className="text-base font-bold text-emerald-400 mt-1 block">
                {result.diagnostics.hit_rate_pct.toFixed(1)}%
              </span>
              <span className="text-[9px] text-slate-500">Dự đoán lựa chọn</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Pseudo-R² McFadden</span>
              <span className="text-base font-bold text-sky-400 mt-1 block">
                {result.diagnostics.mcfadden_pseudo_r2.toFixed(4)}
              </span>
              <span className="text-[9px] text-slate-500">Độ phù hợp Discrete Choice</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">MCMC Acceptance</span>
              <span className="text-base font-bold text-amber-400 mt-1 block">
                {(result.diagnostics.mcmc_acceptance_rate * 100).toFixed(1)}%
              </span>
              <span className="text-[9px] text-slate-500">Tỷ lệ chấp nhận chuỗi</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Log-Likelihood</span>
              <span className="text-base font-bold text-slate-200 mt-1 block">
                {result.diagnostics.log_likelihood.toFixed(1)}
              </span>
              <span className="text-[9px] text-slate-500">Hội tụ cực đại</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Người tham gia (N)</span>
              <span className="text-base font-bold text-indigo-400 mt-1 block">
                {result.diagnostics.n_respondents}
              </span>
              <span className="text-[9px] text-slate-500">Cá thể có hồ sơ</span>
            </div>

            <div className="p-3.5 bg-slate-800/40 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Số quan sát (T)</span>
              <span className="text-base font-bold text-purple-400 mt-1 block">
                {result.diagnostics.n_total_observations}
              </span>
              <span className="text-[9px] text-slate-500">Lựa chọn đánh giá</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('importance')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'importance'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Tỷ trọng Thuộc tính (%)
            </button>
            <button
              onClick={() => setActiveTab('utilities')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'utilities'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Tiện ích Từng phần (Part-Worths)
            </button>
            {result.willingness_to_pay && (
              <button
                onClick={() => setActiveTab('wtp')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                  activeTab === 'wtp'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                Sẵn sàng Chi trả (WTP)
              </button>
            )}
            <button
              onClick={() => setActiveTab('simulator')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'simulator'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Mô phỏng Thị phần (Simulator)
            </button>
            <button
              onClick={() => setActiveTab('svg')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'svg'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Biểu đồ Vector SVG
            </button>
          </div>

          {/* Tab 1: Relative Importance */}
          {activeTab === 'importance' && result.attribute_importance && (
            <div className="space-y-4">
              <div className="bg-slate-800/40 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-2.5 px-4">Xếp hạng</th>
                      <th className="py-2.5 px-4">Thuộc tính</th>
                      <th className="py-2.5 px-4">Tỷ trọng Tương đối (%)</th>
                      <th className="py-2.5 px-4">Độ lệch chuẩn (SD)</th>
                      <th className="py-2.5 px-4">Thanh tỷ trọng</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {result.attribute_importance.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 font-bold text-slate-400">#{idx + 1}</td>
                        <td className="py-2.5 px-4 font-semibold text-white">{item.attribute}</td>
                        <td className="py-2.5 px-4 font-bold text-sky-400">{item.relative_importance_pct.toFixed(2)}%</td>
                        <td className="py-2.5 px-4 text-slate-400">±{item.importance_sd_pct.toFixed(2)}%</td>
                        <td className="py-2.5 px-4 w-1/3">
                          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                            <div
                              className="bg-gradient-to-r from-sky-500 to-indigo-500 h-2 rounded-full"
                              style={{ width: `${Math.min(100, item.relative_importance_pct)}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Part-Worth Utilities */}
          {activeTab === 'utilities' && result.part_worth_utilities && (
            <div className="bg-slate-800/40 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4">Thuộc tính</th>
                    <th className="py-2.5 px-4">Mức độ (Level)</th>
                    <th className="py-2.5 px-4">Tiện ích (Part-Worth μ)</th>
                    <th className="py-2.5 px-4">95% Bayesian Credible Interval</th>
                    <th className="py-2.5 px-4">Ghi chú</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.part_worth_utilities.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 text-slate-300 font-medium">{item.attribute}</td>
                      <td className="py-2.5 px-4 text-white font-semibold">{item.level}</td>
                      <td className={`py-2.5 px-4 font-bold ${item.part_worth_utility >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {item.part_worth_utility >= 0 ? `+${item.part_worth_utility.toFixed(4)}` : item.part_worth_utility.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 font-mono text-[11px]">
                        [{item.bci_95_lower.toFixed(3)}, {item.bci_95_upper.toFixed(3)}]
                      </td>
                      <td className="py-2.5 px-4">
                        {item.is_reference ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-700/60 text-slate-400">
                            Reference (Effects Coding ∑=0)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            MCMC Estimated
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: WTP */}
          {activeTab === 'wtp' && result.willingness_to_pay && (
            <div className="space-y-4">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-between text-xs text-emerald-300">
                <div>
                  <span className="font-semibold block">Hệ số co giãn giá (Marginal Utility of Price):</span>
                  <span className="font-mono text-white mt-0.5 block">
                    α = {result.willingness_to_pay.marginal_utility_of_price.toFixed(6)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-slate-400 block">Khoảng biến thiên giá:</span>
                  <span className="font-semibold text-white">
                    {result.willingness_to_pay.price_range[0]} → {result.willingness_to_pay.price_range[1]}
                  </span>
                </div>
              </div>

              <div className="bg-slate-800/40 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-2.5 px-4">Thuộc tính</th>
                      <th className="py-2.5 px-4">Mức độ (Level)</th>
                      <th className="py-2.5 px-4">Chênh lệch Tiện ích (ΔU)</th>
                      <th className="py-2.5 px-4">Sẵn sàng Chi trả (WTP quy đổi)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {result.willingness_to_pay.wtp_estimates.map((w, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-300">{w.attribute}</td>
                        <td className="py-2.5 px-4 text-white font-semibold">{w.level}</td>
                        <td className="py-2.5 px-4 font-mono text-slate-300">{w.utility_gain_vs_ref.toFixed(4)}</td>
                        <td className={`py-2.5 px-4 font-bold ${w.wtp_currency >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {w.wtp_currency >= 0 ? `+${w.wtp_currency.toLocaleString()}` : w.wtp_currency.toLocaleString()} đơn vị
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 4: Market Simulator */}
          {activeTab === 'simulator' && result.market_simulations && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {result.market_simulations.map((sim, idx) => (
                  <div key={idx} className="p-4 bg-slate-800/50 border border-slate-800 rounded-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{sim.scenario_name}</span>
                      <span className="text-sm font-black text-sky-400">
                        {sim.predicted_choice_share_pct.toFixed(1)}%
                      </span>
                    </div>

                    <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
                      <div
                        className="bg-gradient-to-r from-sky-500 to-indigo-500 h-2.5 rounded-full"
                        style={{ width: `${sim.predicted_choice_share_pct}%` }}
                      />
                    </div>

                    <div className="pt-2 border-t border-slate-800/60 space-y-1 text-[11px]">
                      {Object.entries(sim.attributes).map(([k, v], i) => (
                        <div key={i} className="flex justify-between text-slate-400">
                          <span>{k}:</span>
                          <span className="text-slate-200 font-medium">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 5: SVG Vector Visualizer */}
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
