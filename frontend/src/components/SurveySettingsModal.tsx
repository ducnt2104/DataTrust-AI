import React, { useState, useEffect } from 'react';
import {
  X, BellRing, ShieldCheck, KeyRound, Play, CheckCircle2,
  AlertTriangle, Sliders, Globe, Lock, Clock, Info, Check, AlertCircle,
  MapPin, Compass, Navigation, Languages, Sparkles
} from 'lucide-react';
import { api } from '../api/client';

interface Props {
  surveyId: string;
  isOpen: boolean;
  onClose: () => void;
  currentSettings?: Record<string, any>;
  onSaveSettings: (settings: Record<string, any>) => Promise<void>;
}

export const SurveySettingsModal: React.FC<Props> = ({
  surveyId,
  isOpen,
  onClose,
  currentSettings = {},
  onSaveSettings
}) => {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [speederThreshold, setSpeederThreshold] = useState(10);
  const [straightliningTolerance, setStraightliningTolerance] = useState(85);

  // Geofence states
  const [geofenceEnabled, setGeofenceEnabled] = useState(false);
  const [geofenceLat, setGeofenceLat] = useState<number | string>('');
  const [geofenceLon, setGeofenceLon] = useState<number | string>('');
  const [geofenceRadius, setGeofenceRadius] = useState<number>(5.0);
  const [geofenceLocationName, setGeofenceLocationName] = useState<string>('');
  const [gettingLocation, setGettingLocation] = useState(false);

  const [testingWebhook, setTestingWebhook] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    status_code?: number;
    latency_ms: number;
    message: string;
  } | null>(null);

  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Translation states
  const [translating, setTranslating] = useState(false);
  const [translateResult, setTranslateResult] = useState<string | null>(null);
  const [translations, setTranslations] = useState<Record<string, any>>({});

  useEffect(() => {
    if (isOpen) {
      setWebhookUrl(currentSettings.alert_webhook_url || currentSettings.webhook_url || '');
      setWebhookSecret(currentSettings.webhook_secret || '');
      setTranslations(currentSettings.translations || {});
      const qs = currentSettings.quality_settings || {};
      setSpeederThreshold(qs.speeder_min_seconds || 10);
      setStraightliningTolerance(Math.round((qs.straightlining_threshold || 0.85) * 100));

      const geo = qs.geofence || {};
      setGeofenceEnabled(Boolean(geo.enabled));
      setGeofenceLat(geo.target_lat !== undefined && geo.target_lat !== null ? geo.target_lat : '');
      setGeofenceLon(geo.target_lon !== undefined && geo.target_lon !== null ? geo.target_lon : '');
      setGeofenceRadius(geo.max_radius_km || 5.0);
      setGeofenceLocationName(geo.location_name || '');

      setTestResult(null);
      setSavedSuccess(false);
    }
  }, [isOpen, currentSettings]);

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Trình duyệt của bạn không hỗ trợ định vị GPS.');
      return;
    }
    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeofenceLat(Number(pos.coords.latitude.toFixed(6)));
        setGeofenceLon(Number(pos.coords.longitude.toFixed(6)));
        setGettingLocation(false);
      },
      (err) => {
        alert(`Không thể lấy tọa độ GPS: ${err.message}`);
        setGettingLocation(false);
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  };

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

  const handleTestWebhook = async () => {
    if (!webhookUrl || !webhookUrl.startsWith('http')) {
      alert('Vui lòng nhập URL Webhook hợp lệ bắt đầu bằng http:// hoặc https://');
      return;
    }

    try {
      setTestingWebhook(true);
      setTestResult(null);
      const res = await api.testSurveyWebhook(surveyId, {
        webhook_url: webhookUrl,
        webhook_secret: webhookSecret || undefined
      });
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        success: false,
        latency_ms: 0,
        message: err.message || 'Lỗi kết nối máy chủ.'
      });
    } finally {
      setTestingWebhook(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const updatedSettings = {
        ...currentSettings,
        alert_webhook_url: webhookUrl.trim(),
        webhook_secret: webhookSecret.trim(),
        quality_settings: {
          speeder_min_seconds: speederThreshold,
          straightlining_threshold: straightliningTolerance / 100.0,
          geofence: {
            enabled: geofenceEnabled,
            target_lat: geofenceLat !== '' ? parseFloat(String(geofenceLat)) : null,
            target_lon: geofenceLon !== '' ? parseFloat(String(geofenceLon)) : null,
            max_radius_km: Number(geofenceRadius),
            location_name: geofenceLocationName.trim() || undefined
          }
        }
      };
      await onSaveSettings(updatedSettings);
      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 1200);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi lưu cấu hình khảo sát.');
    } finally {
      setSaving(false);
    }
  };

  const handleAutoTranslate = async (targetLang: string = 'en') => {
    try {
      setTranslating(true);
      setTranslateResult(null);
      const res = await api.autoTranslateSurvey(surveyId, targetLang);
      setTranslations(prev => ({ ...prev, [targetLang]: res }));
      setTranslateResult(`Đã tự động dịch thành công sang ${targetLang === 'en' ? 'Tiếng Anh' : targetLang.toUpperCase()} (${Object.keys(res.questions || {}).length} câu hỏi).`);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi tự động dịch khảo sát.');
    } finally {
      setTranslating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="survey-settings-modal-title"
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 px-6 py-4 text-white flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/20 rounded-xl border border-indigo-400/30">
              <Sliders className="w-5 h-5 text-indigo-300" />
            </div>
            <div>
              <h2 id="survey-settings-modal-title" className="text-lg font-bold">
                Cài Đặt Nâng Cao &amp; Cảnh Báo Webhook
              </h2>
              <p className="text-xs text-indigo-200/80 mt-0.5">
                Cấu hình thông báo tự động và ngưỡng độ nhạy kiểm định dữ liệu
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng cửa sổ cài đặt"
            className="p-1.5 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors focus:outline-hidden focus:ring-2 focus:ring-indigo-400"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-slate-700">
          
          {/* Section 1: Real-time Webhook Dispatcher */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BellRing className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Phát Tán Cảnh Báo Anomaly Webhook (Thời Gian Thực)
                </h3>
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-semibold font-mono">
                RFC 2104 HMAC-SHA256
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Tự động gửi HTTP POST payload đến máy chủ bên ngoài (Slack, Microsoft Teams, Discord hoặc hệ thống SIEM) ngay khi phát hiện phản hồi có điểm rủi ro cao (&ge; 70) hoặc xuất hiện gian lận tốc độ, cụm tọa độ tĩnh. Luồng phát tán ngầm không gây trễ giao diện (0ms latency).
            </p>

            <div className="space-y-3 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Webhook Endpoint URL:
                </label>
                <div className="relative">
                  <Globe className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="url"
                    placeholder="https://hooks.slack.com/services/... hoặc https://api.yourdomain.com/webhook"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:outline-hidden focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Khóa Bí Mật Ký Số (Webhook Secret Token - Tùy chọn):
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    placeholder="Nhập secret key để tạo chữ ký X-DataTrust-Signature-256"
                    value={webhookSecret}
                    onChange={(e) => setWebhookSecret(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:outline-hidden focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600"
                  />
                </div>
              </div>

              {/* Ping Test Button & Result */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleTestWebhook}
                  disabled={testingWebhook || !webhookUrl}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs border border-indigo-200 transition-colors disabled:opacity-50"
                >
                  <Play className={`w-3.5 h-3.5 ${testingWebhook ? 'animate-spin' : ''}`} />
                  <span>{testingWebhook ? 'Đang gửi gói tin thử nghiệm...' : 'Kiểm Tra Kết Nối (Ping Webhook)'}</span>
                </button>

                {testResult && (
                  <div className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
                    testResult.success 
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' 
                      : 'bg-rose-50 text-rose-800 border border-rose-200'
                  }`}>
                    {testResult.success ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span>Thành công ({testResult.latency_ms}ms) — Mã HTTP {testResult.status_code}</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                        <span>Thất bại: {testResult.message}</span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Section 2: Quality Engine Threshold Tuning */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">
                Ngưỡng Độ Nhạy Động Cơ Kiểm Định (Quality Screening Thresholds)
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white p-3.5 rounded-lg border border-slate-200 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">Ngưỡng nộp vội (Speeders):</span>
                  <span className="font-mono font-bold text-indigo-600">&lt; {speederThreshold} giây</span>
                </div>
                <input
                  type="range"
                  min="3"
                  max="30"
                  step="1"
                  value={speederThreshold}
                  onChange={(e) => setSpeederThreshold(parseInt(e.target.value, 10))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
                <span className="text-[11px] text-slate-400 block">
                  Phiếu hoàn thành dưới {speederThreshold}s sẽ bị phạt điểm tốc độ.
                </span>
              </div>

              <div className="bg-white p-3.5 rounded-lg border border-slate-200 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">Độ nghi vấn điền thẳng (Straightlining):</span>
                  <span className="font-mono font-bold text-indigo-600">&ge; {straightliningTolerance}%</span>
                </div>
                <input
                  type="range"
                  min="60"
                  max="95"
                  step="5"
                  value={straightliningTolerance}
                  onChange={(e) => setStraightliningTolerance(parseInt(e.target.value, 10))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
                <span className="text-[11px] text-slate-400 block">
                  Tỷ lệ chọn cùng một cột phương án liên tục.
                </span>
              </div>
            </div>
          </div>

          {/* Section 3: Geofencing Field Sampling Boundary */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Ranh Giới Địa Lý Thu Thập Thực Địa (Geofencing Compliance)
                </h3>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={geofenceEnabled}
                  onChange={(e) => setGeofenceEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-300 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600"></div>
                <span className="ml-2 text-xs font-semibold text-slate-700">
                  {geofenceEnabled ? 'Đang bật' : 'Tắt'}
                </span>
              </label>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Tự động đối soát tọa độ GPS của người điền phiếu hoặc điều tra viên theo công thức trắc địa Haversine. Các phiếu nộp ngoài bán kính cho phép sẽ bị gắn cờ cảnh báo rủi ro <code className="bg-white px-1 py-0.5 rounded text-rose-700 border border-rose-200">FLAG_GEOFENCE_BREACH</code>.
            </p>

            {geofenceEnabled && (
              <div className="space-y-3 pt-2 border-t border-slate-200/80">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <span className="text-xs font-bold text-slate-800">Tọa độ tâm nghiên cứu (Center Point):</span>
                  <button
                    type="button"
                    onClick={handleGetCurrentLocation}
                    disabled={gettingLocation}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-300 transition-colors disabled:opacity-50"
                  >
                    <Navigation className={`w-3.5 h-3.5 ${gettingLocation ? 'animate-spin' : ''}`} />
                    <span>{gettingLocation ? 'Đang xác định GPS...' : 'Lấy tọa độ hiện tại (GPS)'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Vĩ độ (Latitude):
                    </label>
                    <input
                      type="number"
                      step="0.000001"
                      placeholder="VD: 21.028511"
                      value={geofenceLat}
                      onChange={(e) => setGeofenceLat(e.target.value)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Kinh độ (Longitude):
                    </label>
                    <input
                      type="number"
                      step="0.000001"
                      placeholder="VD: 105.854212"
                      value={geofenceLon}
                      onChange={(e) => setGeofenceLon(e.target.value)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Bán kính cho phép (km):
                    </label>
                    <input
                      type="number"
                      min="0.1"
                      max="200"
                      step="0.5"
                      value={geofenceRadius}
                      onChange={(e) => setGeofenceRadius(parseFloat(e.target.value) || 1.0)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Tên địa bàn (Gợi nhớ):
                    </label>
                    <input
                      type="text"
                      placeholder="VD: Bệnh viện Bạch Mai / Quận Cầu Giấy"
                      value={geofenceLocationName}
                      onChange={(e) => setGeofenceLocationName(e.target.value)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Section 4: Multilingual Translation & i18n */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Languages className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Đa Ngôn Ngữ &amp; Bản Địa Hóa (Multilingual Survey / i18n)
                </h3>
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-semibold font-mono">
                Academic Lexicon Engine
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Tự động dịch biểu mẫu khảo sát sang tiếng Anh với từ điển học thuật xã hội học (Likert CSAT, mức độ đồng ý, tần suất, nhân khẩu học và chỉ dẫn khoa học). Người tham gia làm bài có thể chuyển đổi ngôn ngữ linh hoạt trên thanh tiêu đề công khai.
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs font-semibold text-slate-600">Ngôn ngữ khả dụng:</span>
              <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800 border border-emerald-200">
                🇻🇳 Tiếng Việt (Gốc)
              </span>
              {Object.keys(translations).map(lang => (
                <span key={lang} className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-lg bg-indigo-100 text-indigo-800 border border-indigo-200">
                  {lang === 'en' ? '🇬🇧 English' : lang.toUpperCase()}
                </span>
              ))}
            </div>

            <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => handleAutoTranslate('en')}
                disabled={translating}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition-colors shadow-xs disabled:opacity-50"
              >
                {translating ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5 text-indigo-200" />
                )}
                <span>{translating ? 'Đang dịch thuật...' : '1-Click Tự Động Dịch Sang Tiếng Anh'}</span>
              </button>

              {translateResult && (
                <div className="text-xs text-emerald-700 font-semibold flex items-center gap-1.5 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 animate-in fade-in">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>{translateResult}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            {savedSuccess ? (
              <span className="text-emerald-600 font-bold flex items-center gap-1">
                <Check className="w-4 h-4" /> Đã lưu cài đặt thành công!
              </span>
            ) : (
              <span>Cấu hình có hiệu lực ngay lập tức cho các phản hồi tiếp theo.</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors"
            >
              Hủy
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              {saving ? <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : null}
              <span>Lưu Cài Đặt</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
