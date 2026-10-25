import React, { useEffect, useState, useRef } from 'react';
import { 
  ShieldCheck, Send, CheckCircle2, AlertCircle, Clock, ShieldAlert,
  Wifi, WifiOff, CloudUpload, RefreshCw, Languages
} from 'lucide-react';
import { api } from '../api/client';
import { Question, Survey } from '../types/survey';
import { QuestionRenderer } from '../components/QuestionRenderer';

interface Props {
  slug: string;
  onNavigate: (path: string) => void;
}

export const PublicSurveyPage: React.FC<Props> = ({ slug, onNavigate }) => {
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Multilingual i18n state
  const [currentLang, setCurrentLang] = useState<string>('vi');
  const [availableLanguages, setAvailableLanguages] = useState<string[]>(['vi']);

  // Form State
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submittedResponseId, setSubmittedResponseId] = useState<string | null>(null);
  const [recordedRisk, setRecordedRisk] = useState<{ score: number; level: string } | null>(null);
  const [draftRestored, setDraftRestored] = useState(false);

  // Offline-first outbox state
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [offlineQueueCount, setOfflineQueueCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [offlineSuccess, setOfflineSuccess] = useState(false);
  const [syncToast, setSyncToast] = useState<string | null>(null);

  const startTimeRef = useRef<string>(new Date().toISOString());

  const checkOfflineQueue = () => {
    try {
      const q = JSON.parse(localStorage.getItem(`datatrust_offline_outbox_${slug}`) || '[]');
      setOfflineQueueCount(Array.isArray(q) ? q.length : 0);
    } catch {
      setOfflineQueueCount(0);
    }
  };

  const syncOfflineSubmissions = async () => {
    const outboxKey = `datatrust_offline_outbox_${slug}`;
    let items: any[] = [];
    try {
      items = JSON.parse(localStorage.getItem(outboxKey) || '[]');
    } catch {
      return;
    }

    if (!Array.isArray(items) || items.length === 0) return;

    try {
      setIsSyncing(true);
      // Gửi mẻ phiếu ngoại tuyến qua API Atomic Batch Sync
      const batchResult = await api.batchSyncPublicResponses(slug, items);

      if (batchResult.success) {
        // Thu thập các client_uuid đã xử lý thành công hoặc đã bỏ qua trùng lặp
        const processedUuids = new Set<string>();
        for (const res of batchResult.results) {
          if (res.status === 'synced' || res.status === 'skipped_duplicate') {
            if (res.client_uuid) {
              processedUuids.add(res.client_uuid);
            }
          }
        }

        // Lọc lại các mục bị lỗi thực sự nếu có
        const remaining = items.filter(item => item.client_uuid && !processedUuids.has(item.client_uuid));
        localStorage.setItem(outboxKey, JSON.stringify(remaining));
        setOfflineQueueCount(remaining.length);
        window.dispatchEvent(new Event('datatrust_outbox_updated'));

        if (batchResult.synced_count > 0 || batchResult.duplicates_skipped > 0) {
          const detailMsg = batchResult.duplicates_skipped > 0
            ? `Đã đồng bộ ${batchResult.synced_count} phiếu mới, đối soát bỏ qua ${batchResult.duplicates_skipped} phiếu trùng lặp!`
            : `Đã đồng bộ thành công ${batchResult.synced_count} phiếu khảo sát từ hàng đợi thiết bị!`;
          setSyncToast(detailMsg);
          setTimeout(() => setSyncToast(null), 6000);
        }
      }
    } catch (err) {
      console.error("Batch sync offline error:", err);
      if (!navigator.onLine) {
        setSyncToast(`Thiết bị vẫn đang ngoại tuyến. ${items.length} phiếu đã được lưu bảo toàn và sẽ tự động gửi khi có mạng internet.`);
        setTimeout(() => setSyncToast(null), 5000);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    loadPublicSurvey();
    checkOfflineQueue();

    const handleOnline = () => {
      setIsOffline(false);
      syncOfflineSubmissions();
    };
    const handleOffline = () => {
      setIsOffline(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [slug]);

  const loadPublicSurvey = async (langToLoad: string = currentLang) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPublicSurvey(slug, langToLoad);
      setSurvey(data);
      if (data.available_languages) {
        setAvailableLanguages(data.available_languages);
      }
      if (data.current_language) {
        setCurrentLang(data.current_language);
      }
      startTimeRef.current = new Date().toISOString();

      // Tự động khôi phục bản nháp từ localStorage nếu có
      try {
        const saved = localStorage.getItem(`datatrust_draft_${slug}`);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && typeof parsed === 'object' && Object.keys(parsed).length > 0) {
            setAnswers(prev => ({ ...parsed, ...prev }));
            setDraftRestored(true);
            setTimeout(() => setDraftRestored(false), 5000);
          }
        }
      } catch {
        // bỏ qua nếu localStorage bị tắt hoặc lỗi
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : 'Không thể tải khảo sát.');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchLanguage = async (newLang: string) => {
    if (newLang === currentLang) return;
    await loadPublicSurvey(newLang);
  };

  // Tự động lưu nháp câu trả lời vào localStorage chống mất mát dữ liệu
  useEffect(() => {
    if (slug && Object.keys(answers).length > 0 && !submittedResponseId) {
      try {
        localStorage.setItem(`datatrust_draft_${slug}`, JSON.stringify(answers));
      } catch {
        // bỏ qua nếu vượt quota
      }
    }
  }, [answers, slug, submittedResponseId]);

  // Branching logic evaluation: Determines whether a question should be visible
  const isQuestionVisible = (q: Question): boolean => {
    if (!q.logic_rules || q.logic_rules.length === 0) return true;

    for (const rule of q.logic_rules) {
      const depAnswer = answers[rule.depends_on_question_id];
      const normDep = depAnswer !== undefined && depAnswer !== null ? String(depAnswer).trim().toLowerCase() : '';
      const normVal = String(rule.value).trim().toLowerCase();

      const conditionMet = rule.operator === 'equals' ? normDep === normVal : normDep !== normVal;

      if (rule.action === 'show' && !conditionMet) return false;
      if (rule.action === 'hide' && conditionMet) return false;
    }
    return true;
  };

  const handleAnswerChange = (questionId: string, val: any) => {
    setAnswers((prev) => ({ ...prev, [questionId]: val }));
    // Clear validation error when user inputs
    if (validationErrors[questionId]) {
      setValidationErrors((prev) => {
        const updated = { ...prev };
        delete updated[questionId];
        return updated;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!survey) return;

    // Validate required questions
    const visibleQuestions = survey.questions.filter(isQuestionVisible);
    const errors: Record<string, string> = {};

    for (const q of visibleQuestions) {
      if (q.is_required) {
        const val = answers[q.id];
        if (q.question_type === 'matrix') {
          const matrixRows = Array.isArray(q.options?.rows) ? q.options.rows : [];
          if (!val || typeof val !== 'object' || matrixRows.some((r: any) => !val[r.id])) {
            errors[q.id] = 'Vui lòng hoàn thành đánh giá cho tất cả các hàng trong ma trận.';
          }
        } else if (q.question_type === 'ranking') {
          if (!Array.isArray(val) || val.length === 0) {
            errors[q.id] = 'Vui lòng sắp xếp thứ tự ưu tiên cho câu hỏi này.';
          }
        } else if (
          val === undefined ||
          val === null ||
          (typeof val === 'string' && val.trim() === '') ||
          (Array.isArray(val) && val.length === 0)
        ) {
          errors[q.id] = 'Vui lòng hoàn thành câu hỏi bắt buộc này.';
        }
      }
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      // Scroll to the first error
      window.scrollTo({ top: 150, behavior: 'smooth' });
      return;
    }

    const submitTime = new Date().toISOString();
    const clientUuid = typeof crypto !== 'undefined' && crypto.randomUUID 
      ? crypto.randomUUID() 
      : ('off_' + Math.random().toString(36).substring(2) + Date.now());

    const clientMeta = {
      screen_width: window.innerWidth,
      screen_height: window.innerHeight,
      user_agent_short: navigator.userAgent.slice(0, 80)
    };

    const payload = {
      client_uuid: clientUuid,
      started_at: startTimeRef.current,
      submitted_at: submitTime,
      client_metadata: clientMeta,
      answers: answers
    };

    // Nếu thiết bị đang ngoại tuyến, lưu ngay vào Hàng đợi Thiết bị
    if (!navigator.onLine) {
      try {
        const outboxKey = `datatrust_offline_outbox_${slug}`;
        const existing = JSON.parse(localStorage.getItem(outboxKey) || '[]');
        existing.push(payload);
        localStorage.setItem(outboxKey, JSON.stringify(existing));
        try { localStorage.removeItem(`datatrust_draft_${slug}`); } catch {}
        setOfflineQueueCount(existing.length);
        window.dispatchEvent(new Event('datatrust_outbox_updated'));
        setOfflineSuccess(true);
        return;
      } catch (err) {
        console.error(err);
      }
    }

    try {
      setSubmitting(true);
      const result = await api.submitPublicSurvey(slug, payload);

      setSubmittedResponseId(result.response_id);
      try {
        localStorage.removeItem(`datatrust_draft_${slug}`);
      } catch {
        // ignore
      }
      if (result.risk_score !== undefined) {
        setRecordedRisk({ score: result.risk_score, level: result.risk_level || 'low' });
      }
    } catch (err) {
      // Nếu gặp lỗi kết nối mạng, chuyển sang lưu trữ ngoại tuyến an toàn
      const isNetworkIssue = !navigator.onLine || (err instanceof Error && (
        err.message.toLowerCase().includes('fetch') ||
        err.message.toLowerCase().includes('network') ||
        err.message.toLowerCase().includes('failed')
      ));

      if (isNetworkIssue) {
        try {
          const outboxKey = `datatrust_offline_outbox_${slug}`;
          const existing = JSON.parse(localStorage.getItem(outboxKey) || '[]');
          existing.push(payload);
          localStorage.setItem(outboxKey, JSON.stringify(existing));
          try { localStorage.removeItem(`datatrust_draft_${slug}`); } catch {}
          setOfflineQueueCount(existing.length);
          window.dispatchEvent(new Event('datatrust_outbox_updated'));
          setOfflineSuccess(true);
          return;
        } catch {
          // ignore
        }
      }
      alert(err instanceof Error ? err.message : 'Lỗi khi gửi phản hồi.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
        Đang tải biểu mẫu khảo sát...
      </div>
    );
  }

  // Handle Error (Closed, Draft, or Not Found)
  if (error || !survey) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 border border-slate-200 shadow-xl text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 mx-auto flex items-center justify-center">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Không thể mở cuộc khảo sát</h2>
          <p className="text-sm text-slate-600 leading-relaxed">{error}</p>
          <div className="pt-2">
            <button
              onClick={() => onNavigate('/')}
              className="px-5 py-2.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors"
            >
              Về trang chủ DataTrust
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Handle Offline Queue Saved Confirmation
  if (offlineSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-indigo-50/40 to-slate-50 flex items-center justify-center p-4">
        <div className="max-w-lg w-full bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-2xl text-center space-y-6 animate-in zoom-in-95 duration-300">
          <div className="w-16 h-16 rounded-full bg-amber-50 text-amber-600 mx-auto flex items-center justify-center shadow-inner">
            <WifiOff className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Đã lưu vào Hàng đợi Ngoại tuyến!
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              Thiết bị hiện đang ở khu vực ngoại tuyến. Phiếu khảo sát <span className="font-semibold text-slate-800">"{survey.title}"</span> đã được lưu trữ bảo toàn trên bộ nhớ thiết bị của bạn.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200/80 text-left text-xs space-y-2 text-amber-900">
            <div className="font-bold flex items-center gap-1.5">
              <CloudUpload className="w-4 h-4 text-amber-600" />
              <span>Cơ chế Tự động Đồng bộ (Auto-Sync Queue):</span>
            </div>
            <p className="text-amber-800 text-[11px] leading-relaxed">
              Dữ liệu sẽ tự động gửi lên máy chủ DataTrust ngay khi thiết bị có kết nối mạng internet trở lại. Số phiếu đang chờ trong hàng đợi: <strong>{offlineQueueCount} phiếu</strong>.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => {
                setAnswers({});
                setOfflineSuccess(false);
                setSubmittedResponseId(null);
                startTimeRef.current = new Date().toISOString();
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="w-full sm:w-auto px-6 py-3 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-all shadow-md"
            >
              Làm phiếu khảo sát tiếp theo
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Handle Successful Submission
  if (submittedResponseId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-indigo-50/40 to-slate-50 flex items-center justify-center p-4">
        <div className="max-w-lg w-full bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-2xl text-center space-y-6 animate-in zoom-in-95 duration-300">
          <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center shadow-inner">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Gửi phản hồi thành công!
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              Cảm ơn bạn đã tham gia cuộc khảo sát <span className="font-semibold text-slate-800">"{survey.title}"</span>. Câu trả lời của bạn đã được ghi nhận vào hệ thống một cách an toàn.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-left text-xs space-y-2">
            <div className="flex items-center justify-between text-slate-500">
              <span>Mã phản hồi định danh:</span>
              <span className="font-mono text-slate-800 select-all font-semibold">{submittedResponseId}</span>
            </div>
            <div className="flex items-center justify-between text-slate-500">
              <span>Thời điểm ghi nhận:</span>
              <span className="text-slate-800">{new Date().toLocaleTimeString()}</span>
            </div>
            <div className="flex items-center justify-between text-slate-500">
              <span>Kiểm định chất lượng DataTrust:</span>
              <span className="text-emerald-700 font-semibold flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Đã xác thực tính toàn vẹn
              </span>
            </div>
          </div>

          <button
            onClick={() => {
              setSubmittedResponseId(null);
              setAnswers({});
              startTimeRef.current = new Date().toISOString();
            }}
            className="w-full py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold transition-colors"
          >
            Gửi phản hồi khác
          </button>
        </div>
      </div>
    );
  }

  // Calculate Progress
  const visibleQuestions = survey.questions.filter(isQuestionVisible);
  const requiredCount = visibleQuestions.filter((q) => q.is_required).length;
  const answeredRequiredCount = visibleQuestions.filter(
    (q) => q.is_required && answers[q.id] !== undefined && answers[q.id] !== null && String(answers[q.id]).trim() !== ''
  ).length;
  const progressPercent = requiredCount > 0 ? Math.round((answeredRequiredCount / requiredCount) * 100) : 100;

  return (
    <div className="min-h-screen bg-slate-50/70 pb-24">
      {/* Top Floating Progress Bar */}
      <div className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-2.5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-5 h-5 text-indigo-600" />
              <span className="text-xs font-bold text-slate-800 tracking-tight hidden sm:inline">DataTrust Verification</span>
            </div>

            {/* Network status badge */}
            {isOffline ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200 animate-pulse">
                <WifiOff className="w-3 h-3" /> Ngoại tuyến
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <Wifi className="w-3 h-3" /> Trực tuyến
              </span>
            )}

            {/* Offline queue quick sync button in top bar */}
            {offlineQueueCount > 0 && (
              <button
                type="button"
                onClick={syncOfflineSubmissions}
                disabled={isSyncing}
                title="Bấm để đồng bộ ngay các phiếu đang lưu trong bộ nhớ máy"
                className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-800 bg-amber-100 hover:bg-amber-200 px-2.5 py-0.5 rounded-full transition-colors border border-amber-300 disabled:opacity-50"
              >
                <CloudUpload className="w-3 h-3 text-amber-700" />
                <span>{offlineQueueCount} chờ gửi</span>
                {isSyncing && <RefreshCw className="w-2.5 h-2.5 animate-spin ml-0.5" />}
              </button>
            )}
          </div>

          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Language Selector Pill */}
            {availableLanguages.length > 1 && (
              <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-xl border border-slate-200">
                {availableLanguages.map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => handleSwitchLanguage(l)}
                    className={`px-2 py-0.5 text-[11px] font-bold rounded-lg transition-all ${
                      currentLang === l
                        ? 'bg-white text-indigo-700 shadow-xs border border-indigo-200'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {l === 'vi' ? '🇻🇳 VI' : l === 'en' ? '🇬🇧 EN' : l.toUpperCase()}
                  </button>
                ))}
              </div>
            )}

            <span className="text-xs text-slate-500 font-medium">Tiến độ: {progressPercent}%</span>
            <div className="w-16 sm:w-28 h-2 rounded-full bg-slate-200 overflow-hidden">
              <div
                className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 pt-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Sync Success Toast */}
          {syncToast && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-2xl text-xs flex items-center justify-between gap-2 shadow-xs animate-in fade-in duration-200">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="font-semibold">{syncToast}</span>
              </div>
              <button
                type="button"
                onClick={() => setSyncToast(null)}
                className="text-emerald-700 hover:text-emerald-900 text-xs font-bold px-1.5 py-0.5 rounded-md hover:bg-emerald-100"
              >
                ✕
              </button>
            </div>
          )}

          {/* Offline Outbox Sync Banner */}
          {offlineQueueCount > 0 && (
            <div className="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-3 rounded-2xl text-xs flex items-center justify-between gap-3 animate-in fade-in duration-200">
              <div className="flex items-center gap-2">
                <CloudUpload className="w-4 h-4 text-amber-600 shrink-0" />
                <span>
                  Đang có <strong>{offlineQueueCount}</strong> phản hồi trong hàng đợi ngoại tuyến thiết bị.
                </span>
              </div>
              <button
                type="button"
                onClick={syncOfflineSubmissions}
                disabled={isSyncing}
                className="px-3 py-1 rounded-xl bg-amber-600 text-white font-bold text-[11px] hover:bg-amber-700 transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin' : ''}`} />
                <span>{isSyncing ? 'Đang đồng bộ...' : 'Đồng bộ ngay'}</span>
              </button>
            </div>
          )}

          {/* Network Status Notice */}
          {isOffline && (
            <div className="bg-slate-900 text-slate-200 px-4 py-2.5 rounded-2xl text-xs flex items-center gap-2 border border-slate-800">
              <WifiOff className="w-4 h-4 text-rose-400 shrink-0 animate-pulse" />
              <span>Chế độ ngoại tuyến: Câu trả lời sẽ được lưu an toàn trên máy và tự động đồng bộ khi có kết nối mạng.</span>
            </div>
          )}

          {/* Draft Restored Banner */}
          {draftRestored && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-2.5 rounded-2xl text-xs flex items-center gap-2 animate-in fade-in duration-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Đã tự động khôi phục các câu trả lời bạn đang điền trước đó.</span>
            </div>
          )}

          {/* Header Card */}
          <div className="bg-white p-6 sm:p-10 rounded-3xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="h-2 w-20 rounded-full bg-indigo-600" />
              {availableLanguages.length > 1 && (
                <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200">
                  <Languages className="w-3.5 h-3.5 text-indigo-600" />
                  <span className="font-semibold text-slate-700">
                    {currentLang === 'vi' ? '🇻🇳 Tiếng Việt' : currentLang === 'en' ? '🇬🇧 English' : currentLang.toUpperCase()}
                  </span>
                </div>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {survey.title}
            </h1>
            {survey.description && (
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
                {survey.description}
              </p>
            )}
            {survey.instructions && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 text-xs text-slate-500 leading-relaxed">
                {survey.instructions}
              </div>
            )}
            <div className="text-xs text-rose-500 font-medium flex items-center gap-1 pt-1">
              <span>* Biểu thị câu hỏi bắt buộc</span>
            </div>
          </div>

          {/* Questions Stream */}
          <div className="space-y-4">
            {visibleQuestions.map((q, idx) => (
              <QuestionRenderer
                key={q.id}
                question={q}
                index={idx}
                value={answers[q.id]}
                onChange={(val) => handleAnswerChange(q.id, val)}
                error={validationErrors[q.id]}
              />
            ))}
          </div>

          {/* Submit Action Box */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-slate-400 text-center sm:text-left">
              Bằng việc gửi phản hồi, bạn đồng ý với tiêu chuẩn kiểm định dữ liệu khách quan của DataTrust.
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full sm:w-auto px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-md shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 active:scale-98 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>{submitting ? 'Đang xác thực & gửi...' : 'Gửi phản hồi'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
