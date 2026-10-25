import React, { useState, useEffect } from 'react';
import {
  X, Filter, Sparkles, CheckCircle2, AlertTriangle, Clock,
  ShieldCheck, ArrowRight, TrendingUp, Sliders, Play, RotateCcw,
  Zap, Award, AlertCircle, Share2, MapPin, Gauge
} from 'lucide-react';
import { api } from '../api/client';
import { CleansingCriteria, CleansingReport } from '../types/survey';

interface Props {
  surveyId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const PRESET_AAPOR: CleansingCriteria = {
  exclude_speeders: true,
  speeder_min_seconds: 10,
  exclude_straightlining: true,
  straightlining_threshold: 0.85,
  exclude_logic_contradictions: true,
  exclude_high_risk: false,
  min_omr_confidence: 0.70,
  exclude_unverified_enumerator: false,
  exclude_collusion_syndicates: true,
  exclude_coffee_shop_congregations: true,
  exclude_impossible_travel: true,
  exclude_geofence_violations: false
};

const PRESET_STRICT: CleansingCriteria = {
  exclude_speeders: true,
  speeder_min_seconds: 15,
  exclude_straightlining: true,
  straightlining_threshold: 0.80,
  exclude_logic_contradictions: true,
  exclude_high_risk: true,
  min_omr_confidence: 0.80,
  exclude_unverified_enumerator: true,
  exclude_collusion_syndicates: true,
  exclude_coffee_shop_congregations: true,
  exclude_impossible_travel: true,
  exclude_geofence_violations: true
};

const PRESET_LENIENT: CleansingCriteria = {
  exclude_speeders: true,
  speeder_min_seconds: 5,
  exclude_straightlining: false,
  straightlining_threshold: 0.90,
  exclude_logic_contradictions: true,
  exclude_high_risk: false,
  min_omr_confidence: 0.60,
  exclude_unverified_enumerator: false,
  exclude_collusion_syndicates: false,
  exclude_coffee_shop_congregations: false,
  exclude_impossible_travel: false,
  exclude_geofence_violations: false
};

export const DataCleansingModal: React.FC<Props> = ({
  surveyId,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [preset, setPreset] = useState<'aapor' | 'strict' | 'lenient' | 'custom'>('aapor');
  const [criteria, setCriteria] = useState<CleansingCriteria>(PRESET_AAPOR);
  const [report, setReport] = useState<CleansingReport | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSelectPreset = (p: 'aapor' | 'strict' | 'lenient') => {
    setPreset(p);
    if (p === 'aapor') setCriteria(PRESET_AAPOR);
    if (p === 'strict') setCriteria(PRESET_STRICT);
    if (p === 'lenient') setCriteria(PRESET_LENIENT);
    setReport(null);
    setApplySuccess(null);
  };

  const handlePreview = async () => {
    try {
      setLoadingPreview(true);
      setErrorMsg(null);
      setApplySuccess(null);
      const res = await api.previewDataCleansing(surveyId, criteria);
      setReport(res);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Lỗi khi mô phỏng quy trình làm sạch dữ liệu.');
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleApply = async () => {
    if (!window.confirm('Bạn có chắc chắn muốn áp dụng quy trình làm sạch này? Trạng thái thẩm định của các phiếu vi phạm sẽ được cập nhật thành Bị Loại (Fraud/Excluded) kèm lý do chi tiết, và ghi nhận vào chuỗi băm kiểm toán SHA-256.')) {
      return;
    }

    try {
      setApplying(true);
      setErrorMsg(null);
      const res = await api.applyDataCleansing(surveyId, criteria);
      setApplySuccess(`Đã áp dụng thành công! Đã loại trừ ${res.rejected_count} phiếu rác, công nhận ${res.verified_clean_count} phiếu sạch. Mã kiểm toán: ${res.audit_log_id.slice(0, 8)}...`);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Lỗi khi thực thi làm sạch dữ liệu.');
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div 
        role="dialog"
        aria-modal="true"
        aria-labelledby="data-cleansing-modal-title"
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in zoom-in-95 duration-200"
      >
        
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-600 to-teal-700 px-6 py-4 text-white flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/10 rounded-xl backdrop-blur-md">
              <Sparkles className="w-6 h-6 text-emerald-200" />
            </div>
            <div>
              <h2 id="data-cleansing-modal-title" className="text-xl font-bold flex items-center gap-2">
                Quy Trình Làm Sạch Dữ Liệu Tự Động
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/30 border border-emerald-300/30 text-emerald-100 font-medium">
                  AAPOR & Dillman Standards
                </span>
              </h2>
              <p className="text-xs text-emerald-100/90 mt-0.5">
                Loại bỏ speeders, straightlining và mâu thuẫn logic với khả năng kiểm chứng trước tác động
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng cửa sổ làm sạch dữ liệu"
            className="p-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors focus:outline-hidden focus:ring-2 focus:ring-white/50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-slate-700">
          
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {applySuccess && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-sm flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <p className="font-semibold">Làm sạch dữ liệu hoàn tất</p>
                <p className="text-xs text-emerald-700 mt-0.5">{applySuccess}</p>
              </div>
            </div>
          )}

          {/* Preset Buttons */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">
              Bộ tiêu chuẩn loại trừ mẫu (Exclusion Criteria Presets)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => handleSelectPreset('aapor')}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  preset === 'aapor'
                    ? 'border-emerald-500 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold text-slate-900">Chuẩn AAPOR / Dillman</span>
                  <Award className={`w-4 h-4 ${preset === 'aapor' ? 'text-emerald-600' : 'text-slate-400'}`} />
                </div>
                <p className="text-xs text-slate-500">
                  Khuyên dùng cho nghiên cứu học thuật. Speeders &lt; 10s, thẳng hàng &gt; 85%, mâu thuẫn logic.
                </p>
              </button>

              <button
                type="button"
                onClick={() => handleSelectPreset('strict')}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  preset === 'strict'
                    ? 'border-emerald-500 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold text-slate-900">Nghiêm ngặt (Strict)</span>
                  <ShieldCheck className={`w-4 h-4 ${preset === 'strict' ? 'text-emerald-600' : 'text-slate-400'}`} />
                </div>
                <p className="text-xs text-slate-500">
                  Kiểm soát cao độ: Speeders &lt; 15s, thẳng hàng &gt; 80%, rủi ro cao, OMR &lt; 80%.
                </p>
              </button>

              <button
                type="button"
                onClick={() => handleSelectPreset('lenient')}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  preset === 'lenient'
                    ? 'border-emerald-500 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold text-slate-900">Linh hoạt (Permissive)</span>
                  <Sliders className={`w-4 h-4 ${preset === 'lenient' ? 'text-emerald-600' : 'text-slate-400'}`} />
                </div>
                <p className="text-xs text-slate-500">
                  Dành cho tập mẫu nhỏ: Chỉ loại người làm dưới 5s và vi phạm mâu thuẫn câu hỏi.
                </p>
              </button>
            </div>
          </div>

          {/* Rules Configuration */}
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4 space-y-3.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-emerald-600" />
              Chi tiết quy tắc lọc loại trừ
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {/* Rule 1: Speeders */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_speeders}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_speeders: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Loại bỏ người làm siêu tốc (Speeders)</span>
                </label>
                {criteria.exclude_speeders && (
                  <div className="flex items-center justify-between text-slate-600 pt-1 border-t border-slate-100">
                    <span>Ngưỡng tối thiểu:</span>
                    <div className="flex items-center gap-1.5 font-bold text-slate-900">
                      <input
                        type="number"
                        min="3"
                        max="120"
                        value={criteria.speeder_min_seconds}
                        onChange={(e) => {
                          setCriteria(prev => ({ ...prev, speeder_min_seconds: Number(e.target.value) }));
                          setPreset('custom');
                        }}
                        className="w-16 px-2 py-0.5 border border-slate-300 rounded text-right"
                      />
                      <span>giây</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Rule 2: Straightlining */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_straightlining}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_straightlining: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Loại bỏ hoa văn rập khuôn (Straightlining)</span>
                </label>
                {criteria.exclude_straightlining && (
                  <div className="flex items-center justify-between text-slate-600 pt-1 border-t border-slate-100">
                    <span>Ngưỡng trùng lặp thang đo:</span>
                    <span className="font-bold text-slate-900">&ge; {Math.round(criteria.straightlining_threshold * 100)}%</span>
                  </div>
                )}
              </div>

              {/* Rule 3: Logic Contradictions */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_logic_contradictions}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_logic_contradictions: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Loại bỏ mâu thuẫn logic chéo</span>
                </label>
                <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  Phát hiện câu trả lời mâu thuẫn giữa các biến phụ thuộc (Logic Rules)
                </p>
              </div>

              {/* Rule 4: High Risk Cutoff */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_high_risk}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_high_risk: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Loại bỏ điểm rủi ro tổng hợp cao</span>
                </label>
                <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  Loại tất cả phiếu có Điểm Rủi ro &ge; 70.0 (High Risk)
                </p>
              </div>

              {/* Rule 5: OMR Confidence */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="text-slate-800 font-semibold block">
                  Độ tin cậy quét phiếu giấy (OMR Confidence)
                </label>
                <div className="flex items-center justify-between text-slate-600 pt-1 border-t border-slate-100">
                  <span>Ngưỡng nhận diện tối thiểu:</span>
                  <span className="font-bold text-slate-900">&ge; {Math.round(criteria.min_omr_confidence * 100)}%</span>
                </div>
              </div>

              {/* Rule 6: Unverified Enumerator */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_unverified_enumerator}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_unverified_enumerator: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Yêu cầu có mã Điều tra viên (Field Surveys)</span>
                </label>
                <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  Loại trừ các phiếu không có định danh điều tra viên thực địa
                </p>
              </div>

              {/* Rule 7: Collusion Syndicates */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_collusion_syndicates ?? true}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_collusion_syndicates: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="flex items-center gap-1.5">
                    <Share2 className="w-3.5 h-3.5 text-indigo-600" />
                    Mạng lưới thông đồng / Sao chép
                  </span>
                </label>
                <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  Loại trừ phản hồi thuộc vòng thông đồng, trùng lặp thiết bị / IP
                </p>
              </div>

              {/* Rule 8: Coffee-Shop Congregation */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_coffee_shop_congregations ?? true}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_coffee_shop_congregations: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-rose-600" />
                    Gian lận GPS quán cà phê (DBSCAN)
                  </span>
                </label>
                <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  Phát hiện tụ tập mật độ cao tại 1 tọa độ tĩnh nghi vấn khai khống
                </p>
              </div>

              {/* Rule 9: Impossible Travel */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_impossible_travel ?? true}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_impossible_travel: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="flex items-center gap-1.5">
                    <Gauge className="w-3.5 h-3.5 text-amber-600" />
                    Vận tốc phi thực tế / GPS giả mạo
                  </span>
                </label>
                <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  Loại bỏ các phiếu có vận tốc di chuyển liên tiếp &gt; 120 km/h
                </p>
              </div>

              {/* Rule 10: Geofence Breach */}
              <div className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={criteria.exclude_geofence_violations ?? false}
                    onChange={(e) => {
                      setCriteria(prev => ({ ...prev, exclude_geofence_violations: e.target.checked }));
                      setPreset('custom');
                    }}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="flex items-center gap-1.5">
                    <Filter className="w-3.5 h-3.5 text-teal-600" />
                    Vi phạm ranh giới địa bàn (Geofence)
                  </span>
                </label>
                <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  Loại trừ các phiếu thu thập nằm ngoài ranh giới bản đồ đa giác
                </p>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={handlePreview}
                disabled={loadingPreview}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
              >
                {loadingPreview ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin" />
                    <span>Đang mô phỏng...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Mô Phỏng Trước Tác Động (Preview Cleansing)</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Simulation Results Section */}
          {report && (
            <div className="border border-emerald-200 bg-emerald-50/40 rounded-xl p-5 space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-emerald-900 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Kết quả mô phỏng làm sạch ({report.clean_percentage}% mẫu sạch đạt chuẩn)
                </h3>
                <span className="text-xs bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full font-medium">
                  {report.total_responses} phiếu được đánh giá
                </span>
              </div>

              {/* 3 KPI summary boxes */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs text-slate-500 block">Tổng phiếu đầu vào</span>
                  <span className="text-2xl font-black text-slate-900">{report.total_responses}</span>
                </div>
                <div className="bg-white p-3.5 rounded-xl border border-emerald-200 shadow-sm">
                  <span className="text-xs text-emerald-700 font-semibold block">Mẫu sạch giữ lại (Verified)</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-black text-emerald-600">{report.clean_responses_count}</span>
                    <span className="text-xs text-emerald-700 font-bold">({report.clean_percentage}%)</span>
                  </div>
                </div>
                <div className="bg-white p-3.5 rounded-xl border border-rose-200 shadow-sm">
                  <span className="text-xs text-rose-700 font-semibold block">Phiếu bị loại trừ (Excluded)</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-black text-rose-600">{report.total_responses - report.clean_responses_count}</span>
                    <span className="text-xs text-rose-700 font-bold">({Math.round((report.total_responses - report.clean_responses_count) / Math.max(1, report.total_responses) * 100)}%)</span>
                  </div>
                </div>
              </div>

              {/* Breakdown by rule */}
              <div className="bg-white p-4 rounded-xl border border-slate-200">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3">
                  Phân rã phiếu bị loại theo quy tắc vi phạm
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Nộp siêu tốc:</span>
                    <span className="text-sm font-bold text-amber-600">{report.flagged_speeders}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Thẳng hàng / Rập khuôn:</span>
                    <span className="text-sm font-bold text-amber-600">{report.flagged_straightlining}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Mâu thuẫn logic:</span>
                    <span className="text-sm font-bold text-rose-600">{report.flagged_contradictions}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Điểm rủi ro cao:</span>
                    <span className="text-sm font-bold text-rose-600">{report.flagged_high_risk}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Mạng lưới thông đồng:</span>
                    <span className="text-sm font-bold text-indigo-600">{report.flagged_collusion_syndicates ?? 0}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Cụm GPS quán cà phê:</span>
                    <span className="text-sm font-bold text-rose-600">{report.flagged_coffee_shop ?? 0}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Vận tốc phi lý (&gt;120km/h):</span>
                    <span className="text-sm font-bold text-amber-600">{report.flagged_impossible_travel ?? 0}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block">Vi phạm Geofence:</span>
                    <span className="text-sm font-bold text-teal-600">{report.flagged_geofence_violations ?? 0}</span>
                  </div>
                </div>
                {report.overlap_count > 0 && (
                  <p className="text-[11px] text-slate-400 mt-2 italic">
                    * Có {report.overlap_count} phiếu vi phạm đồng thời nhiều hơn 1 quy tắc lọc.
                  </p>
                )}
              </div>

              {/* Comparative Before vs After */}
              <div className="bg-white p-4 rounded-xl border border-emerald-200">
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 mb-3 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                  Đối chiếu chỉ số chất lượng: Trước vs Sau khi làm sạch
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block">Thời gian làm bài TB:</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-slate-400 line-through">{report.pre_avg_duration}s</span>
                      <ArrowRight className="w-3 h-3 text-emerald-600" />
                      <span className="text-sm font-bold text-emerald-700">{report.post_avg_duration}s</span>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block">Điểm rủi ro trung bình:</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-slate-400 line-through">{report.pre_avg_risk}/100</span>
                      <ArrowRight className="w-3 h-3 text-emerald-600" />
                      <span className="text-sm font-bold text-emerald-700">{report.post_avg_risk}/100</span>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block">Độ tin cậy Cronbach&apos;s Alpha:</span>
                    {report.cronbach_alpha_pre !== null && report.cronbach_alpha_post !== null ? (
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-slate-400 line-through">&alpha; = {report.cronbach_alpha_pre}</span>
                        <ArrowRight className="w-3 h-3 text-emerald-600" />
                        <span className="text-sm font-bold text-emerald-700">&alpha; = {report.cronbach_alpha_post}</span>
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-400 italic block mt-1">Không đủ &ge;2 câu thang đo</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handleApply}
                  disabled={applying}
                  className="inline-flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50"
                >
                  {applying ? (
                    <>
                      <RotateCcw className="w-4 h-4 animate-spin" />
                      <span>Đang cập nhật CSDL...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-5 h-5 text-emerald-200" />
                      <span>Xác Nhận &amp; Áp Dụng Làm Sạch CSDL</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Mọi thao tác làm sạch được ghi vào Chuỗi Băm Kiểm Toán Bất Biến SHA-256</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors"
          >
            Đóng
          </button>
        </div>

      </div>
    </div>
  );
};
