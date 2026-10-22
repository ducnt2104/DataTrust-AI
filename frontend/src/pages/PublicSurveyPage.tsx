import React, { useEffect, useState, useRef } from 'react';
import { ShieldCheck, Send, CheckCircle2, AlertCircle, Clock, ShieldAlert } from 'lucide-react';
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

  // Form State
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submittedResponseId, setSubmittedResponseId] = useState<string | null>(null);
  const [recordedRisk, setRecordedRisk] = useState<{ score: number; level: string } | null>(null);

  const startTimeRef = useRef<string>(new Date().toISOString());

  useEffect(() => {
    loadPublicSurvey();
  }, [slug]);

  const loadPublicSurvey = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPublicSurvey(slug);
      setSurvey(data);
      startTimeRef.current = new Date().toISOString();
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : 'Không thể tải khảo sát.');
    } finally {
      setLoading(false);
    }
  };

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
        if (
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

    try {
      setSubmitting(true);
      const submitTime = new Date().toISOString();
      const clientMeta = {
        screen_width: window.innerWidth,
        screen_height: window.innerHeight,
        user_agent_short: navigator.userAgent.slice(0, 80)
      };

      const result = await api.submitPublicSurvey(slug, {
        started_at: startTimeRef.current,
        submitted_at: submitTime,
        client_metadata: clientMeta,
        answers: answers
      });

      setSubmittedResponseId(result.response_id);
      if (result.risk_score !== undefined) {
        setRecordedRisk({ score: result.risk_score, level: result.risk_level || 'low' });
      }
    } catch (err) {
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
              Về trang chủ DataTrust AI
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
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-2.5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-600" />
            <span className="text-xs font-bold text-slate-800 tracking-tight">DataTrust AI Verification</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 font-medium">Tiến độ: {progressPercent}%</span>
            <div className="w-24 sm:w-32 h-2 rounded-full bg-slate-200 overflow-hidden">
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
          {/* Header Card */}
          <div className="bg-white p-6 sm:p-10 rounded-3xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="h-2 w-20 rounded-full bg-indigo-600" />
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
              Bằng việc gửi phản hồi, bạn đồng ý với tiêu chuẩn kiểm định dữ liệu khách quan của DataTrust AI.
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
