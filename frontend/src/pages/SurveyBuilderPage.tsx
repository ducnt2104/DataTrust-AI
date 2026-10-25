import React, { useEffect, useState } from 'react';
import {
  Save,
  Send,
  Eye,
  Plus,
  Trash2,
  Copy,
  ChevronUp,
  ChevronDown,
  Sparkles,
  AlertTriangle,
  ArrowLeft,
  Settings,
  HelpCircle,
  CheckCircle2,
  Share2,
  Printer,
  GitFork,
  History,
  Clock,
  Cpu,
  FileJson,
  Network,
  Languages,
  Brain
} from 'lucide-react';
import { api } from '../api/client';
import { Question, QuestionType, Survey, LogicRule } from '../types/survey';
import { QuestionRenderer } from '../components/QuestionRenderer';
import { ShareModal } from '../components/ShareModal';
import { StatusBadge } from '../components/StatusBadge';
import { SurveyVersionHistoryModal } from '../components/SurveyVersionHistoryModal';
import { SurveySettingsModal } from '../components/SurveySettingsModal';
import { SurveyLogicSimulatorModal } from '../components/SurveyLogicSimulatorModal';
import { SurveyTranslationModal } from '../components/SurveyTranslationModal';
import { CognitivePretestModal } from '../components/CognitivePretestModal';

interface Props {
  surveyId?: string; // If 'new' or undefined, creates new survey
  onNavigate: (path: string) => void;
}

const QUESTION_TYPES: { type: QuestionType; label: string; desc: string }[] = [
  { type: 'single_choice', label: 'Trắc nghiệm (1 đáp án)', desc: 'Chọn 1 phương án duy nhất' },
  { type: 'multiple_choice', label: 'Nhiều lựa chọn', desc: 'Chọn một hoặc nhiều phương án' },
  { type: 'likert', label: 'Thang đo Likert', desc: '5 mức độ: Hoàn toàn không đồng ý -> Đồng ý' },
  { type: 'matrix', label: 'Ma trận nhiều hàng & cột', desc: 'Đánh giá nhiều tiêu chí trên cùng thang đo' },
  { type: 'ranking', label: 'Xếp hạng thứ tự ưu tiên', desc: 'Sắp xếp các mục theo độ ưu tiên' },
  { type: 'linear_scale', label: 'Thang điểm tuyến tính', desc: 'Đánh giá điểm số từ 1 đến 10' },
  { type: 'short_text', label: 'Trả lời ngắn', desc: 'Nhập họ tên, email hoặc từ khóa' },
  { type: 'long_text', label: 'Trả lời dài (Văn bản)', desc: 'Đóng góp ý kiến tự do, nhận xét' },
  { type: 'dropdown', label: 'Danh sách thả xuống', desc: 'Menu chọn lựa chọn' },
  { type: 'number', label: 'Số thực / Số nguyên', desc: 'Nhập số tuổi, thu nhập, số lượng' },
  { type: 'date', label: 'Ngày tháng', desc: 'Chọn ngày cụ thể' },
  { type: 'boolean', label: 'Đúng / Sai (Có / Không)', desc: 'Xác nhận nhị phân' }
];

export const SurveyBuilderPage: React.FC<Props> = ({ surveyId, onNavigate }) => {
  const isNew = !surveyId || surveyId === 'new';

  const [survey, setSurvey] = useState<Survey>({
    id: '',
    title: 'Khảo sát chưa đặt tên',
    description: '',
    instructions: 'Vui lòng hoàn thành tất cả các câu hỏi bắt buộc được đánh dấu (*).',
    status: 'draft',
    public_slug: '',
    version: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    questions: []
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string>('Đã lưu');
  const [viewMode, setViewMode] = useState<'edit' | 'preview'>('edit');
  const [previewAnswers, setPreviewAnswers] = useState<Record<string, any>>({});
  const [shareOpen, setShareOpen] = useState(false);

  // AI Modal States
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [aiModalTab, setAiModalTab] = useState<'GENERATE' | 'HISTORY'>('GENERATE');
  const [aiSessions, setAiSessions] = useState<any[]>([]);
  const [aiSessionsLoading, setAiSessionsLoading] = useState(false);
  const [selectedSessionDetail, setSelectedSessionDetail] = useState<any | null>(null);
  const [aiTopic, setAiTopic] = useState('');
  const [aiAudience, setAiAudience] = useState('');
  const [aiObjectives, setAiObjectives] = useState('');
  const [aiQuestionCount, setAiQuestionCount] = useState(7);
  const [aiPreferredTypes, setAiPreferredTypes] = useState<string[]>(['single_choice', 'likert', 'matrix', 'ranking', 'linear_scale']);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiGenStage, setAiGenStage] = useState<'IDLE' | 'ANALYZING' | 'STRUCTURING' | 'VALIDATING' | 'READY'>('IDLE');
  const [aiStatusInfo, setAiStatusInfo] = useState<any>(null);
  const [generatedDraftPreview, setGeneratedDraftPreview] = useState<any>(null);

  // AI Audit State
  const [auditIssues, setAuditIssues] = useState<any[]>([]);
  const [auditOpen, setAuditOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [openLogicIndex, setOpenLogicIndex] = useState<number | null>(null);
  const [isVersionModalOpen, setIsVersionModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isLogicSimulatorOpen, setIsLogicSimulatorOpen] = useState(false);
  const [isTranslationModalOpen, setIsTranslationModalOpen] = useState(false);
  const [isCognitivePretestOpen, setIsCognitivePretestOpen] = useState(false);

  useEffect(() => {
    if (isNew) {
      initNewSurvey();
    } else {
      loadSurvey(surveyId);
    }
  }, [surveyId]);

  const initNewSurvey = async () => {
    try {
      setLoading(true);
      const newSurv = await api.createSurvey({
        title: 'Khảo sát nghiên cứu mới',
        description: 'Mô tả mục tiêu của cuộc khảo sát này'
      });
      // Bổ sung 1 câu hỏi mẫu mặc định
      const defaultQ: Question = {
        id: crypto.randomUUID(),
        order_index: 0,
        question_type: 'single_choice',
        title: 'Bạn thuộc nhóm đối tượng nào?',
        description: 'Vui lòng chọn câu trả lời phù hợp nhất',
        is_required: true,
        options: [
          { id: 'opt_1', label: 'Học sinh / Sinh viên' },
          { id: 'opt_2', label: 'Người đi làm' },
          { id: 'opt_3', label: 'Khác' }
        ],
        logic_rules: []
      };
      const updated = await api.updateSurvey(newSurv.id, { questions: [defaultQ] });
      setSurvey(updated);
    } catch (err) {
      console.error(err);
      alert('Lỗi tạo khảo sát mới');
    } finally {
      setLoading(false);
    }
  };

  const loadSurvey = async (id: string) => {
    try {
      setLoading(true);
      const data = await api.getSurvey(id);
      setSurvey(data);
    } catch (err) {
      console.error(err);
      alert('Không thể tải khảo sát.');
    } finally {
      setLoading(false);
    }
  };

  const saveSurvey = async (showNotification = true) => {
    if (!survey.id) return;
    try {
      setSaving(true);
      setSaveStatus('Đang lưu...');
      const updated = await api.updateSurvey(survey.id, {
        title: survey.title,
        description: survey.description,
        instructions: survey.instructions,
        questions: survey.questions
      });
      setSurvey(updated);
      setSaveStatus('Đã lưu mọi thay đổi');
    } catch (err) {
      console.error(err);
      setSaveStatus('Lỗi lưu');
      if (showNotification) alert('Lỗi khi lưu khảo sát.');
    } finally {
      setSaving(false);
      setTimeout(() => setSaveStatus('Đã lưu'), 2500);
    }
  };

  const handlePublish = async () => {
    if (survey.questions.length === 0) {
      alert('Khảo sát phải có ít nhất một câu hỏi trước khi xuất bản.');
      return;
    }
    // Lưu trước khi xuất bản
    await saveSurvey(false);

    try {
      const pub = await api.publishSurvey(survey.id);
      setSurvey((prev) => ({ ...prev, status: 'published' }));
      setShareOpen(true);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi xuất bản');
    }
  };

  const handleApplyCognitiveFix = (questionId: string, newTitle: string, newOptions?: any[]) => {
    setSurvey((prev) => {
      const updated = prev.questions.map((q) => {
        if (q.id === questionId) {
          return {
            ...q,
            title: newTitle,
            options: newOptions !== undefined ? newOptions : q.options
          };
        }
        return q;
      });
      return { ...prev, questions: updated };
    });
    setToastMessage('Đã tự động tối ưu hóa câu hỏi theo chuẩn nhận thức Dillman/Tourangeau!');
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleApplyAllCognitiveFixes = (fixedQuestions: Question[]) => {
    setSurvey((prev) => ({ ...prev, questions: fixedQuestions }));
    setToastMessage(`Đã cập nhật toàn bộ ${fixedQuestions.length} câu hỏi theo chuẩn nhận thức!`);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // --- Question Manipulation ---
  const addQuestion = (type: QuestionType) => {
    let defaultOptions = [
      { id: 'opt_1', label: 'Tùy chọn 1' },
      { id: 'opt_2', label: 'Tùy chọn 2' }
    ];

    if (type === 'likert') {
      defaultOptions = [
        { id: '1', label: '1 - Rất không hài lòng' },
        { id: '2', label: '2 - Không hài lòng' },
        { id: '3', label: '3 - Trung lập' },
        { id: '4', label: '4 - Hài lòng' },
        { id: '5', label: '5 - Rất hài lòng' }
      ];
    } else if (type === 'matrix') {
      defaultOptions = {
        rows: [
          { id: 'r1', label: 'Tiêu chí 1' },
          { id: 'r2', label: 'Tiêu chí 2' },
          { id: 'r3', label: 'Tiêu chí 3' }
        ],
        columns: [
          { id: 'c1', label: 'Kém' },
          { id: 'c2', label: 'Bình thường' },
          { id: 'c3', label: 'Tốt' }
        ]
      } as any;
    } else if (type === 'ranking') {
      defaultOptions = [
        { id: 'rank_1', label: 'Mục ưu tiên A' },
        { id: 'rank_2', label: 'Mục ưu tiên B' },
        { id: 'rank_3', label: 'Mục ưu tiên C' }
      ];
    } else if (type === 'linear_scale') {
      defaultOptions = [
        { id: 'min', label: '1 (Thấp)' },
        { id: 'max', label: '10 (Cao)' }
      ];
    } else if (type === 'short_text' || type === 'long_text' || type === 'number' || type === 'date' || type === 'boolean') {
      defaultOptions = [];
    }

    const newQ: Question = {
      id: crypto.randomUUID(),
      order_index: survey.questions.length,
      question_type: type,
      title: `Câu hỏi mới số ${survey.questions.length + 1}`,
      description: '',
      is_required: false,
      options: defaultOptions,
      logic_rules: []
    };

    setSurvey((prev) => ({
      ...prev,
      questions: [...prev.questions, newQ]
    }));
  };

  const updateQuestion = (index: number, updates: Partial<Question>) => {
    setSurvey((prev) => {
      const qList = [...prev.questions];
      qList[index] = { ...qList[index], ...updates };
      return { ...prev, questions: qList };
    });
  };

  const deleteQuestion = (index: number) => {
    setSurvey((prev) => {
      const qList = prev.questions.filter((_, i) => i !== index);
      return { ...prev, questions: qList };
    });
  };

  const duplicateQuestion = (index: number) => {
    const original = survey.questions[index];
    const copy: Question = {
      ...original,
      id: crypto.randomUUID(),
      title: `${original.title} (Bản sao)`,
      order_index: survey.questions.length
    };
    setSurvey((prev) => {
      const qList = [...prev.questions];
      qList.splice(index + 1, 0, copy);
      return { ...prev, questions: qList };
    });
  };

  const moveQuestion = (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= survey.questions.length) return;

    setSurvey((prev) => {
      const qList = [...prev.questions];
      const temp = qList[index];
      qList[index] = qList[targetIndex];
      qList[targetIndex] = temp;
      return { ...prev, questions: qList };
    });
  };

  // Option actions
  const addOption = (qIndex: number) => {
    const q = survey.questions[qIndex];
    const newOpt = {
      id: `opt_${(q.options?.length || 0) + 1}_${Date.now().toString().slice(-4)}`,
      label: `Tùy chọn ${(q.options?.length || 0) + 1}`
    };
    updateQuestion(qIndex, { options: [...(q.options || []), newOpt] });
  };

  const updateOptionLabel = (qIndex: number, optIndex: number, newLabel: string) => {
    const q = survey.questions[qIndex];
    const newOpts = [...(q.options || [])];
    newOpts[optIndex] = { ...newOpts[optIndex], label: newLabel };
    updateQuestion(qIndex, { options: newOpts });
  };

  const deleteOption = (qIndex: number, optIndex: number) => {
    const q = survey.questions[qIndex];
    const newOpts = (q.options || []).filter((_: any, i: number) => i !== optIndex);
    updateQuestion(qIndex, { options: newOpts });
  };

  // Logic rules handlers (Branching / Skip Logic)
  const addLogicRule = (qIndex: number) => {
    const q = survey.questions[qIndex];
    const antecedent = survey.questions[qIndex - 1];
    if (!antecedent) return;

    const defaultVal = Array.isArray(antecedent.options) && antecedent.options.length > 0
      ? (antecedent.options[0].label || antecedent.options[0].id || '')
      : '';

    const newRule: LogicRule = {
      depends_on_question_id: antecedent.id,
      operator: 'equals',
      value: defaultVal,
      action: 'show'
    };
    updateQuestion(qIndex, { logic_rules: [...(q.logic_rules || []), newRule] });
  };

  const updateLogicRule = (qIndex: number, ruleIdx: number, patch: Partial<LogicRule>) => {
    const q = survey.questions[qIndex];
    const updated = [...(q.logic_rules || [])];
    updated[ruleIdx] = { ...updated[ruleIdx], ...patch };
    updateQuestion(qIndex, { logic_rules: updated });
  };

  const deleteLogicRule = (qIndex: number, ruleIdx: number) => {
    const q = survey.questions[qIndex];
    const updated = (q.logic_rules || []).filter((_, i) => i !== ruleIdx);
    updateQuestion(qIndex, { logic_rules: updated });
  };

  // AI Generation & Telemetry Handlers
  const openAIModal = async () => {
    setAiModalOpen(true);
    setAiModalTab('GENERATE');
    setGeneratedDraftPreview(null);
    setSelectedSessionDetail(null);
    setAiGenStage('IDLE');
    try {
      const status = await api.getAiStatus();
      setAiStatusInfo(status);
    } catch {
      // ignore
    }
  };

  const fetchAiSessions = async () => {
    setAiSessionsLoading(true);
    try {
      const list = await api.getAiSessions(20);
      setAiSessions(list);
    } catch (err) {
      console.error('Lỗi tải danh sách phiên AI:', err);
    } finally {
      setAiSessionsLoading(false);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    try {
      const detail = await api.getAiSessionDetail(sessionId);
      setSelectedSessionDetail(detail);
    } catch {
      alert('Không thể tải chi tiết phiên sinh AI này.');
    }
  };

  const handleApplySessionDraft = (draft: any) => {
    if (draft && draft.title && draft.questions) {
      setGeneratedDraftPreview(draft);
      setAiModalTab('GENERATE');
      setSelectedSessionDetail(null);
    } else {
      alert('Bản nháp của phiên này không có dữ liệu câu hỏi hợp lệ.');
    }
  };

  const handleAIGenerate = async () => {
    if (!aiTopic.trim()) {
      alert('Vui lòng nhập chủ đề khảo sát.');
      return;
    }
    try {
      setAiGenerating(true);
      setAiGenStage('ANALYZING');

      // Cập nhật trạng thái tiến trình
      setTimeout(() => setAiGenStage('STRUCTURING'), 300);
      setTimeout(() => setAiGenStage('VALIDATING'), 600);

      const res = await api.generateSurveyDraft({
        topic: aiTopic,
        audience: aiAudience,
        research_objectives: aiObjectives,
        target_question_count: aiQuestionCount,
        preferred_question_types: aiPreferredTypes,
        expected_time_minutes: 5,
        strict_scientific_mode: true
      });

      if (res && res.questions) {
        setGeneratedDraftPreview(res);
        setAiGenStage('READY');
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi sinh bản nháp bằng AI');
      setAiGenStage('IDLE');
    } finally {
      setAiGenerating(false);
    }
  };

  const handleApplyDraft = () => {
    if (!generatedDraftPreview || !generatedDraftPreview.questions) return;
    const formattedQuestions: Question[] = generatedDraftPreview.questions.map((q: any, i: number) => ({
      id: q.id || crypto.randomUUID(),
      order_index: i,
      question_type: q.question_type || 'single_choice',
      title: q.title || `Câu hỏi ${i + 1}`,
      description: q.description || '',
      is_required: Boolean(q.is_required),
      options: q.options || [],
      logic_rules: q.logic_rules || []
    }));

    setSurvey((prev) => ({
      ...prev,
      title: generatedDraftPreview.title || prev.title,
      description: generatedDraftPreview.description || prev.description,
      instructions: generatedDraftPreview.instructions || prev.instructions,
      questions: formattedQuestions
    }));
    setAiModalOpen(false);
    setGeneratedDraftPreview(null);
  };

  // AI Audit Handler
  const handleAIAudit = async () => {
    try {
      const res = await api.auditQuestions(survey.questions, survey.id);
      setAuditIssues(res.issues || []);
      setAuditOpen(true);
    } catch (err) {
      alert('Không thể thực hiện kiểm định AI.');
    }
  };

  // Auto-fix handler for AI audit
  const handleApplyAutoFix = (issue: any) => {
    if (!issue.question_id || !issue.auto_fix_title) return;
    const qIdx = survey.questions.findIndex((q) => q.id === issue.question_id);
    if (qIdx !== -1) {
      updateQuestion(qIdx, { title: issue.auto_fix_title });
      setAuditIssues((prev) => prev.filter((i) => i !== issue));
      setToastMessage(`Đã chuẩn hóa câu hỏi thành công.`);
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  const handleApplyAllAutoFixes = () => {
    let currentQuestions = [...survey.questions];
    let appliedCount = 0;
    auditIssues.forEach((issue) => {
      if (issue.question_id && issue.auto_fix_title) {
        const qIdx = currentQuestions.findIndex((q) => q.id === issue.question_id);
        if (qIdx !== -1) {
          currentQuestions[qIdx] = { ...currentQuestions[qIdx], title: issue.auto_fix_title };
          appliedCount++;
        }
      }
    });
    if (appliedCount > 0) {
      setSurvey((prev) => ({ ...prev, questions: currentQuestions }));
      setAuditIssues((prev) => prev.filter((i) => !i.auto_fix_title));
      setToastMessage(`Đã tự động chuẩn hóa toàn bộ ${appliedCount} câu hỏi đạt chuẩn AAPOR.`);
      setTimeout(() => setToastMessage(null), 3500);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center text-slate-500 text-sm">
        Đang khởi tạo trình thiết kế khảo sát...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/60 pb-24">
      {/* Top Action Bar */}
      <div className="sticky top-16 z-30 bg-white border-b border-slate-200 px-4 sm:px-8 py-3 flex flex-wrap items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('/surveys')}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-900 line-clamp-1 max-w-xs sm:max-w-md">
                {survey.title || 'Khảo sát chưa đặt tên'}
              </span>
              <StatusBadge status={survey.status} />
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {saveStatus} • v{survey.version}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* AI Survey Assistant Button */}
          <button
            onClick={openAIModal}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-violet-50 text-violet-700 hover:bg-violet-100 border border-violet-200 transition-all shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-violet-600" />
            <span>AI Soạn thảo</span>
          </button>

          {/* AI Question Audit */}
          <button
            onClick={handleAIAudit}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 transition-all"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Kiểm định</span>
          </button>

          {/* Lịch sử phiên bản (Version History) */}
          {!isNew && (
            <button
              onClick={() => setIsVersionModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 transition-all"
              title="Xem lịch sử tiến hóa cấu trúc câu hỏi theo từng phiên bản"
            >
              <History className="w-3.5 h-3.5 text-slate-600" />
              <span>Lịch sử v{survey.version}</span>
            </button>
          )}

          {/* Cài đặt khảo sát & Cảnh báo Webhook */}
          {!isNew && (
            <button
              onClick={() => setIsSettingsModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 transition-all"
              title="Cài đặt ngưỡng kiểm định chất lượng và cấu hình Anomaly Webhook"
            >
              <Settings className="w-3.5 h-3.5 text-slate-600" />
              <span>Cài đặt</span>
            </button>
          )}

          {/* Logic Branching & DAG Simulator Button */}
          {!isNew && (
            <button
              onClick={() => setIsLogicSimulatorOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-all shadow-2xs"
              title="Kiểm định đồ thị rẽ nhánh DAG, quét chu trình lặp vô tận và mô phỏng luồng trải nghiệm"
            >
              <Network className="w-3.5 h-3.5 text-indigo-600" />
              <span>Logic DAG</span>
            </button>
          )}

          {/* Bản địa hóa & Đa ngôn ngữ (Multilingual Studio) */}
          {!isNew && (
            <button
              onClick={() => setIsTranslationModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-all shadow-2xs"
              title="Bản địa hóa khảo sát sang tiếng Anh, Nhật, Trung với từ điển học thuật offline"
            >
              <Languages className="w-3.5 h-3.5 text-emerald-600" />
              <span>Đa ngôn ngữ</span>
            </button>
          )}

          {/* Thử nghiệm nhận thức Dillman/Tourangeau (Cognitive Pre-Testing) */}
          <button
            onClick={() => setIsCognitivePretestOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 transition-all shadow-2xs"
            title="Thử nghiệm nhận thức Dillman/Tourangeau: Phát hiện câu hỏi định hướng, phức hợp, mệt mỏi nhận thức và mô phỏng nhân khẩu"
          >
            <Brain className="w-3.5 h-3.5 text-purple-600" />
            <span>Tiền kiểm nhận thức</span>
          </button>

          {/* Preview / Edit Toggle */}
          <button
            onClick={() => setViewMode(viewMode === 'edit' ? 'preview' : 'edit')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              viewMode === 'preview'
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>{viewMode === 'preview' ? 'Thoát xem trước' : 'Xem trước'}</span>
          </button>

          {/* Save Button */}
          <button
            onClick={() => saveSurvey(true)}
            disabled={saving}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-all disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Lưu</span>
          </button>

          {/* Paper Survey Button */}
          {survey.id && survey.id !== 'new' && (
            <button
              onClick={() => onNavigate(`/surveys/${survey.id}/paper`)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 shadow-xs transition-all"
              title="Mẫu in A4 & Quét phiếu OMR"
            >
              <Printer className="w-3.5 h-3.5 text-slate-500" />
              <span>Phiếu giấy A4 & OMR</span>
            </button>
          )}

          {/* Publish / Share Button */}
          {survey.status === 'published' ? (
            <button
              onClick={() => setShareOpen(true)}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-xs transition-all"
            >
              <Share2 className="w-3.5 h-3.5" />
              <span>Link & QR</span>
            </button>
          ) : (
            <button
              onClick={handlePublish}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-xs transition-all active:scale-98"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Xuất bản</span>
            </button>
          )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-8 space-y-6">
        {/* PREVIEW MODE */}
        {viewMode === 'preview' ? (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs font-medium flex items-center justify-between">
              <span>Đang ở chế độ Xem trước trải nghiệm của người tham gia</span>
              <button
                onClick={() => setViewMode('edit')}
                className="font-bold underline"
              >
                Quay lại chỉnh sửa
              </button>
            </div>

            {/* Header info */}
            <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
              <h1 className="text-2xl font-bold text-slate-900">{survey.title}</h1>
              {survey.description && <p className="text-sm text-slate-600">{survey.description}</p>}
              {survey.instructions && (
                <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-200/60 mt-3">
                  {survey.instructions}
                </div>
              )}
            </div>

            {/* Questions preview */}
            <div className="space-y-4">
              {survey.questions.map((q, idx) => (
                <QuestionRenderer
                  key={q.id}
                  question={q}
                  index={idx}
                  value={previewAnswers[q.id]}
                  onChange={(val) => setPreviewAnswers({ ...previewAnswers, [q.id]: val })}
                />
              ))}
            </div>
          </div>
        ) : (
          /* EDIT MODE */
          <div className="space-y-6">
            {/* Survey Title & Header Box */}
            <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  Tiêu đề cuộc khảo sát
                </label>
                <input
                  type="text"
                  value={survey.title}
                  onChange={(e) => setSurvey({ ...survey, title: e.target.value })}
                  placeholder="Nhập tiêu đề khảo sát..."
                  className="w-full text-xl sm:text-2xl font-extrabold text-slate-900 border-b border-transparent hover:border-slate-300 focus:border-indigo-600 focus:outline-hidden pb-1 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  Mô tả / Mục tiêu nghiên cứu
                </label>
                <input
                  type="text"
                  value={survey.description}
                  onChange={(e) => setSurvey({ ...survey, description: e.target.value })}
                  placeholder="Thêm mô tả ngắn gọn về mục đích khảo sát..."
                  className="w-full text-sm text-slate-600 border-b border-transparent hover:border-slate-300 focus:border-indigo-600 focus:outline-hidden pb-1 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  Hướng dẫn làm bài cho người tham gia
                </label>
                <input
                  type="text"
                  value={survey.instructions}
                  onChange={(e) => setSurvey({ ...survey, instructions: e.target.value })}
                  placeholder="Ví dụ: Vui lòng trả lời trung thực..."
                  className="w-full text-xs text-slate-500 border-b border-transparent hover:border-slate-300 focus:border-indigo-600 focus:outline-hidden pb-1 transition-all"
                />
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-4">
              {survey.questions.map((q, qIndex) => (
                <div
                  key={q.id}
                  className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4 hover:border-indigo-200 transition-all"
                >
                  {/* Question Header & Order */}
                  <div className="flex items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2 flex-1">
                      <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold flex items-center justify-center">
                        {qIndex + 1}
                      </span>
                      <select
                        value={q.question_type}
                        onChange={(e) => updateQuestion(qIndex, { question_type: e.target.value as QuestionType })}
                        className="text-xs font-semibold text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:border-indigo-600 focus:outline-hidden"
                      >
                        {QUESTION_TYPES.map((t) => (
                          <option key={t.type} value={t.type}>
                            {t.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-1 text-slate-400">
                      <button
                        title="Di chuyển lên"
                        disabled={qIndex === 0}
                        onClick={() => moveQuestion(qIndex, 'up')}
                        className="p-1 hover:text-slate-700 disabled:opacity-30"
                      >
                        <ChevronUp className="w-4 h-4" />
                      </button>
                      <button
                        title="Di chuyển xuống"
                        disabled={qIndex === survey.questions.length - 1}
                        onClick={() => moveQuestion(qIndex, 'down')}
                        className="p-1 hover:text-slate-700 disabled:opacity-30"
                      >
                        <ChevronDown className="w-4 h-4" />
                      </button>
                      <button
                        title="Nhân bản câu hỏi"
                        onClick={() => duplicateQuestion(qIndex)}
                        className="p-1 hover:text-indigo-600"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        title="Xóa câu hỏi"
                        onClick={() => deleteQuestion(qIndex)}
                        className="p-1 hover:text-rose-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Title & Description Inputs */}
                  <div className="space-y-2">
                    {/* Active Logic Badge */}
                    {q.logic_rules && q.logic_rules.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 py-1 px-2.5 bg-amber-50/90 border border-amber-200/90 rounded-lg text-xs text-amber-900">
                        <GitFork className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        <span className="font-semibold text-[11px] uppercase tracking-wider">Rẽ nhánh:</span>
                        {q.logic_rules.map((rule, rIdx) => {
                          const depQ = survey.questions.find((x) => x.id === rule.depends_on_question_id);
                          const depIndex = depQ ? survey.questions.indexOf(depQ) + 1 : '?';
                          return (
                            <span key={rIdx} className="bg-white/90 px-2 py-0.5 rounded border border-amber-200 text-[11px] font-mono">
                              {rule.action === 'show' ? 'Hiện' : 'Ẩn'} khi Câu #{depIndex} {rule.operator === 'equals' ? '==' : '≠'} "{rule.value}"
                            </span>
                          );
                        })}
                      </div>
                    )}
                    <input
                      type="text"
                      value={q.title}
                      onChange={(e) => updateQuestion(qIndex, { title: e.target.value })}
                      placeholder="Nhập nội dung câu hỏi..."
                      className="w-full text-base font-semibold text-slate-900 border-b border-slate-200 focus:border-indigo-600 focus:outline-hidden py-1 transition-all"
                    />
                    <input
                      type="text"
                      value={q.description || ''}
                      onChange={(e) => updateQuestion(qIndex, { description: e.target.value })}
                      placeholder="Mô tả bổ sung hoặc gợi ý làm bài (tùy chọn)..."
                      className="w-full text-xs text-slate-500 border-b border-transparent hover:border-slate-200 focus:border-indigo-600 focus:outline-hidden py-0.5 transition-all"
                    />
                  </div>

                  {/* Options Management (if choice or likert) */}
                  {(q.question_type === 'single_choice' ||
                    q.question_type === 'multiple_choice' ||
                    q.question_type === 'dropdown' ||
                    q.question_type === 'likert') && (
                    <div className="space-y-2 pt-2">
                      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                        Các phương án lựa chọn
                      </label>
                      <div className="space-y-2">
                        {q.options?.map((opt: any, optIdx: number) => (
                          <div key={opt.id || optIdx} className="flex items-center gap-2">
                            <span className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px] text-slate-400">
                              {optIdx + 1}
                            </span>
                            <input
                              type="text"
                              value={opt.label}
                              onChange={(e) => updateOptionLabel(qIndex, optIdx, e.target.value)}
                              className="flex-1 text-sm px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-600 focus:outline-hidden"
                            />
                            {q.options.length > 2 && (
                              <button
                                onClick={() => deleteOption(qIndex, optIdx)}
                                className="text-slate-400 hover:text-rose-600 p-1"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={() => addOption(qIndex)}
                        className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 pt-1"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Thêm tùy chọn</span>
                      </button>
                    </div>
                  )}

                  {/* Ranking Options Editor */}
                  {q.question_type === 'ranking' && (
                    <div className="space-y-2 pt-2">
                      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                        Các mục cần xếp hạng thứ tự ưu tiên
                      </label>
                      <div className="space-y-2">
                        {Array.isArray(q.options) && q.options.map((opt: any, optIdx: number) => (
                          <div key={opt.id || optIdx} className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-[10px] text-slate-500 font-bold shrink-0">
                              #{optIdx + 1}
                            </span>
                            <input
                              type="text"
                              value={opt.label}
                              onChange={(e) => updateOptionLabel(qIndex, optIdx, e.target.value)}
                              className="flex-1 text-sm px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-600 focus:outline-hidden"
                            />
                            {q.options.length > 2 && (
                              <button
                                onClick={() => deleteOption(qIndex, optIdx)}
                                className="text-slate-400 hover:text-rose-600 p-1"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={() => addOption(qIndex)}
                        className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 pt-1"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Thêm mục xếp hạng</span>
                      </button>
                    </div>
                  )}

                  {/* Matrix Rows & Columns Editor */}
                  {q.question_type === 'matrix' && (() => {
                    const matrixOpts = (q.options && typeof q.options === 'object' && !Array.isArray(q.options))
                      ? q.options
                      : { rows: [{ id: 'r1', label: 'Tiêu chí 1' }, { id: 'r2', label: 'Tiêu chí 2' }], columns: [{ id: 'c1', label: 'Kém' }, { id: 'c2', label: 'Tốt' }] };
                    const rows = matrixOpts.rows || [];
                    const cols = matrixOpts.columns || [];

                    const updateMatrix = (newRows: any[], newCols: any[]) => {
                      updateQuestion(qIndex, { options: { rows: newRows, columns: newCols } });
                    };

                    return (
                      <div className="space-y-4 pt-2">
                        {/* Rows editor */}
                        <div className="space-y-2">
                          <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
                            Các hàng (Tiêu chí / Khía cạnh đánh giá)
                          </label>
                          <div className="space-y-2">
                            {rows.map((row: any, rIdx: number) => (
                              <div key={row.id || rIdx} className="flex items-center gap-2">
                                <span className="text-xs font-mono text-slate-400 w-6">R{rIdx + 1}</span>
                                <input
                                  type="text"
                                  value={row.label}
                                  onChange={(e) => {
                                    const nRows = [...rows];
                                    nRows[rIdx] = { ...nRows[rIdx], label: e.target.value };
                                    updateMatrix(nRows, cols);
                                  }}
                                  className="flex-1 text-sm px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-600 focus:outline-hidden"
                                />
                                {rows.length > 1 && (
                                  <button
                                    onClick={() => {
                                      const nRows = rows.filter((_: any, i: number) => i !== rIdx);
                                      updateMatrix(nRows, cols);
                                    }}
                                    className="text-slate-400 hover:text-rose-600 p-1"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              const nRows = [...rows, { id: `r_${Date.now().toString().slice(-4)}`, label: `Tiêu chí ${rows.length + 1}` }];
                              updateMatrix(nRows, cols);
                            }}
                            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 pt-1"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            <span>Thêm hàng</span>
                          </button>
                        </div>

                        {/* Columns editor */}
                        <div className="space-y-2 pt-2 border-t border-slate-100">
                          <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
                            Các cột (Thang đo / Mức đánh giá)
                          </label>
                          <div className="space-y-2">
                            {cols.map((col: any, cIdx: number) => (
                              <div key={col.id || cIdx} className="flex items-center gap-2">
                                <span className="text-xs font-mono text-slate-400 w-6">C{cIdx + 1}</span>
                                <input
                                  type="text"
                                  value={col.label}
                                  onChange={(e) => {
                                    const nCols = [...cols];
                                    nCols[cIdx] = { ...nCols[cIdx], label: e.target.value };
                                    updateMatrix(rows, nCols);
                                  }}
                                  className="flex-1 text-sm px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-600 focus:outline-hidden"
                                />
                                {cols.length > 2 && (
                                  <button
                                    onClick={() => {
                                      const nCols = cols.filter((_: any, i: number) => i !== cIdx);
                                      updateMatrix(rows, nCols);
                                    }}
                                    className="text-slate-400 hover:text-rose-600 p-1"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              const nCols = [...cols, { id: `c_${Date.now().toString().slice(-4)}`, label: `Mức ${cols.length + 1}` }];
                              updateMatrix(rows, nCols);
                            }}
                            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 pt-1"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            <span>Thêm cột</span>
                          </button>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Question Options Footer (Required toggle & Logic button) */}
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={q.is_required}
                        onChange={(e) => updateQuestion(qIndex, { is_required: e.target.checked })}
                        className="w-4 h-4 text-indigo-600 rounded-sm border-slate-300 focus:ring-indigo-500"
                      />
                      <span className="font-medium">Bắt buộc trả lời</span>
                    </label>

                    {/* Logic Branching rule toggle button */}
                    {qIndex > 0 && (
                      <button
                        type="button"
                        onClick={() => setOpenLogicIndex(openLogicIndex === qIndex ? null : qIndex)}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                          (q.logic_rules || []).length > 0
                            ? 'bg-amber-100/80 text-amber-900 hover:bg-amber-200/80'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        <GitFork className="w-3.5 h-3.5 text-amber-600" />
                        {(q.logic_rules || []).length > 0
                          ? `${(q.logic_rules || []).length} quy tắc rẽ nhánh`
                          : 'Thêm rẽ nhánh (Skip logic)'}
                      </button>
                    )}
                  </div>

                  {/* Expandable Logic Builder Panel */}
                  {openLogicIndex === qIndex && qIndex > 0 && (
                    <div className="mt-3 p-4 bg-amber-50/50 border border-amber-200/80 rounded-xl space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900">
                          <GitFork className="w-4 h-4 text-amber-600" />
                          <span>Cấu hình Điều kiện Rẽ nhánh & Bỏ qua (Skip Logic)</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => addLogicRule(qIndex)}
                          className="text-xs font-semibold text-amber-700 hover:text-amber-900 flex items-center gap-1"
                        >
                          <Plus className="w-3.5 h-3.5" /> Thêm điều kiện
                        </button>
                      </div>

                      {(!q.logic_rules || q.logic_rules.length === 0) ? (
                        <p className="text-xs text-amber-700/80 italic">
                          Chưa có điều kiện nào. Nhấn "+ Thêm điều kiện" để câu hỏi này chỉ hiển thị khi người tham gia thỏa mãn câu trả lời trước đó.
                        </p>
                      ) : (
                        <div className="space-y-2">
                          {q.logic_rules.map((rule, rIdx) => {
                            const availableAntecedents = survey.questions.slice(0, qIndex);
                            const currentDepQ = availableAntecedents.find((x) => x.id === rule.depends_on_question_id) || availableAntecedents[0];

                            return (
                              <div key={rIdx} className="flex flex-wrap items-center gap-2 p-2.5 bg-white rounded-lg border border-amber-200 text-xs">
                                <span className="font-semibold text-slate-700">Quy tắc #{rIdx + 1}:</span>
                                
                                <select
                                  value={rule.action}
                                  onChange={(e) => updateLogicRule(qIndex, rIdx, { action: e.target.value as any })}
                                  className="px-2 py-1 bg-slate-50 border border-slate-300 rounded font-medium"
                                >
                                  <option value="show">Hiển thị nếu</option>
                                  <option value="hide">Ẩn nếu</option>
                                </select>

                                <select
                                  value={rule.depends_on_question_id}
                                  onChange={(e) => updateLogicRule(qIndex, rIdx, { depends_on_question_id: e.target.value })}
                                  className="px-2 py-1 bg-slate-50 border border-slate-300 rounded max-w-[200px] truncate"
                                >
                                  {availableAntecedents.map((ant, antIdx) => (
                                    <option key={ant.id} value={ant.id}>
                                      Câu #{antIdx + 1}: {ant.title || 'Chưa đặt tiêu đề'}
                                    </option>
                                  ))}
                                </select>

                                <select
                                  value={rule.operator}
                                  onChange={(e) => updateLogicRule(qIndex, rIdx, { operator: e.target.value as any })}
                                  className="px-2 py-1 bg-slate-50 border border-slate-300 rounded"
                                >
                                  <option value="equals">Bằng (=)</option>
                                  <option value="not_equals">Khác (≠)</option>
                                </select>

                                {Array.isArray(currentDepQ?.options) && currentDepQ.options.length > 0 ? (
                                  <select
                                    value={rule.value}
                                    onChange={(e) => updateLogicRule(qIndex, rIdx, { value: e.target.value })}
                                    className="px-2 py-1 bg-slate-50 border border-slate-300 rounded flex-1 min-w-[120px]"
                                  >
                                    <option value="">-- Chọn đáp án mục tiêu --</option>
                                    {currentDepQ.options.map((opt: any, oIdx: number) => (
                                      <option key={opt.id || oIdx} value={opt.label || opt.id}>
                                        {opt.label || opt.id}
                                      </option>
                                    ))}
                                  </select>
                                ) : (
                                  <input
                                    type="text"
                                    placeholder="Giá trị so sánh..."
                                    value={rule.value}
                                    onChange={(e) => updateLogicRule(qIndex, rIdx, { value: e.target.value })}
                                    className="px-2 py-1 bg-slate-50 border border-slate-300 rounded flex-1 min-w-[120px]"
                                  />
                                )}

                                <button
                                  type="button"
                                  onClick={() => deleteLogicRule(qIndex, rIdx)}
                                  className="text-slate-400 hover:text-rose-600 p-1"
                                  title="Xóa quy tắc này"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Add Question Palette */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Thêm câu hỏi mới vào khảo sát
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {QUESTION_TYPES.map((t) => (
                  <button
                    key={t.type}
                    onClick={() => addQuestion(t.type)}
                    className="flex flex-col items-start p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/40 text-left transition-all group"
                  >
                    <span className="text-xs font-bold text-slate-800 group-hover:text-indigo-700">
                      + {t.label}
                    </span>
                    <span className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                      {t.desc}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Enhanced AI Survey Generator Modal */}
      {aiModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-100 overflow-hidden flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-violet-50/70">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-lg bg-violet-600 text-white">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">AI Survey Assistant & Methodology Engine</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    {aiStatusInfo?.provider_available === 'Google Gemini API' ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        ● Gemini 2.5/2.0 API ({aiStatusInfo?.configured_model || 'Cloud'})
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-violet-700 bg-violet-100/70 px-2 py-0.5 rounded-full border border-violet-200">
                        ● Deterministic Scientific Archetypes (Local Engine)
                      </span>
                    )}
                    <span className="text-[10px] text-slate-400">12 question types</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setAiModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            {/* Modal Tabs Header */}
            <div className="flex border-b border-slate-200 bg-slate-50/80 px-6 pt-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => { setAiModalTab('GENERATE'); setSelectedSessionDetail(null); }}
                className={`px-3 py-2 font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                  aiModalTab === 'GENERATE'
                    ? 'border-violet-600 text-violet-700 bg-white rounded-t-lg'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Thiết Kế Khảo Sát Mới</span>
              </button>
              <button
                type="button"
                onClick={() => { setAiModalTab('HISTORY'); fetchAiSessions(); }}
                className={`px-3 py-2 font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                  aiModalTab === 'HISTORY'
                    ? 'border-violet-600 text-violet-700 bg-white rounded-t-lg'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <History className="w-3.5 h-3.5" />
                <span>Nhật Ký & Đo Lường AI Telemetry</span>
                {aiSessions.length > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full bg-violet-100 text-violet-700 text-[10px] font-mono">
                    {aiSessions.length}
                  </span>
                )}
              </button>
            </div>

            <div className="p-6 space-y-4 overflow-y-auto flex-1 text-xs">
              {aiModalTab === 'HISTORY' ? (
                /* History & Telemetry Tab View */
                <div>
                  {selectedSessionDetail ? (
                    /* Detailed Inspection View of a Session */
                    <div className="space-y-4 animate-in fade-in duration-200">
                      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                        <button
                          type="button"
                          onClick={() => setSelectedSessionDetail(null)}
                          className="flex items-center gap-1 text-slate-600 hover:text-slate-900 font-semibold"
                        >
                          <ArrowLeft className="w-3.5 h-3.5" />
                          <span>Quay lại danh sách phiên</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleApplySessionDraft(selectedSessionDetail.generated_survey_json)}
                          className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-xs transition-all"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Nạp Bản Nháp Này Vào Bảng Thiết Kế</span>
                        </button>
                      </div>

                      {/* Session Metadata Card */}
                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[10px] text-slate-500">
                            Session ID: {selectedSessionDetail.id}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            selectedSessionDetail.status === 'SUCCESS'
                              ? 'bg-emerald-100 text-emerald-800'
                              : selectedSessionDetail.status === 'FALLBACK_APPLIED'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}>
                            {selectedSessionDetail.status}
                          </span>
                        </div>
                        <div className="font-bold text-slate-900 text-sm">
                          {selectedSessionDetail.topic}
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px] text-slate-600 border-t border-slate-200/60">
                          <div>
                            <span className="block text-slate-400 text-[10px]">Mô hình AI:</span>
                            <span className="font-semibold text-slate-800">{selectedSessionDetail.model_name || 'N/A'}</span>
                          </div>
                          <div>
                            <span className="block text-slate-400 text-[10px]">Nhà cung cấp:</span>
                            <span className="font-semibold text-slate-800">{selectedSessionDetail.provider_type || 'N/A'}</span>
                          </div>
                          <div>
                            <span className="block text-slate-400 text-[10px]">Độ trễ xử lý:</span>
                            <span className="font-semibold text-slate-800">{selectedSessionDetail.duration_ms ? `${selectedSessionDetail.duration_ms} ms` : 'N/A'}</span>
                          </div>
                          <div>
                            <span className="block text-slate-400 text-[10px]">Thời điểm tạo:</span>
                            <span className="font-semibold text-slate-800">
                              {selectedSessionDetail.created_at ? new Date(selectedSessionDetail.created_at).toLocaleTimeString('vi-VN') : 'N/A'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Scientific Validation Report */}
                      {selectedSessionDetail.validation_report_json && (
                        <div className="p-3.5 rounded-xl bg-violet-50/60 border border-violet-200/80 space-y-2">
                          <div className="flex items-center justify-between text-violet-900 font-bold text-xs">
                            <span className="flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-violet-600" />
                              Báo Cáo Kiểm Định Phương Pháp (AAPOR / Don Dillman)
                            </span>
                            <span className="font-mono text-xs bg-violet-100 px-2 py-0.5 rounded-md text-violet-800">
                              Điểm khách quan: {selectedSessionDetail.validation_report_json.objectivity_score}/100
                            </span>
                          </div>
                          <div className="text-[11px] text-violet-700">
                            {selectedSessionDetail.validation_report_json.issues?.length === 0 ? (
                              <span className="text-emerald-700 font-medium">✓ Đạt chuẩn khách quan khoa học, không phát hiện câu hỏi dẫn dắt hoặc thiên kiến.</span>
                            ) : (
                              <span>Phát hiện {selectedSessionDetail.validation_report_json.issues?.length} điểm cần lưu ý về cấu trúc câu hỏi.</span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Preview Generated Questions */}
                      {selectedSessionDetail.generated_survey_json?.questions && (
                        <div className="space-y-2">
                          <div className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                            Danh sách câu hỏi đã sinh ({selectedSessionDetail.generated_survey_json.questions.length} câu):
                          </div>
                          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                            {selectedSessionDetail.generated_survey_json.questions.map((q: any, idx: number) => (
                              <div key={idx} className="p-2.5 rounded-xl bg-white border border-slate-200/80 space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-700">
                                    {q.question_type}
                                  </span>
                                  <span className="font-medium text-slate-900 truncate">
                                    {idx + 1}. {q.title}
                                  </span>
                                </div>
                                {q.options && q.options.length > 0 && (
                                  <div className="text-[11px] text-slate-500 pl-4">
                                    Phương án ({q.options.length}): {q.options.slice(0, 4).map((o: any) => typeof o === 'string' ? o : o.label).join(' • ')}
                                    {q.options.length > 4 && ' ...'}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    /* Session List View */
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-slate-600 text-[11px]">
                        <span>Danh sách 20 phiên sinh AI gần nhất kèm chỉ số độ trễ và kiểm định:</span>
                        <button
                          type="button"
                          onClick={fetchAiSessions}
                          className="text-violet-600 hover:text-violet-800 font-bold"
                        >
                          Làm mới
                        </button>
                      </div>

                      {aiSessionsLoading ? (
                        <div className="text-center py-8 text-slate-400">
                          Đang tải dữ liệu telemetry AI...
                        </div>
                      ) : aiSessions.length === 0 ? (
                        <div className="text-center py-8 rounded-xl bg-slate-50 border border-slate-200 text-slate-400">
                          Chưa có phiên sinh khảo sát AI nào được ghi nhận.
                        </div>
                      ) : (
                        <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                          {aiSessions.map((s: any) => (
                            <div
                              key={s.id}
                              onClick={() => handleSelectSession(s.id)}
                              className="p-3 rounded-xl bg-white border border-slate-200 hover:border-violet-400 hover:shadow-xs transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                            >
                              <div className="space-y-0.5 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold ${
                                    s.status === 'SUCCESS'
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : s.status === 'FALLBACK_APPLIED'
                                      ? 'bg-amber-100 text-amber-800'
                                      : 'bg-rose-100 text-rose-800'
                                  }`}>
                                    {s.status}
                                  </span>
                                  <span className="font-bold text-slate-900 text-xs truncate">
                                    {s.topic}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2 text-[10px] text-slate-400">
                                  <span>{s.model_name || 'Archetype'} ({s.provider_type})</span>
                                  <span>•</span>
                                  <span>{s.duration_ms ? `${s.duration_ms} ms` : 'N/A'}</span>
                                  <span>•</span>
                                  <span>{new Date(s.created_at).toLocaleString('vi-VN')}</span>
                                </div>
                              </div>
                              <button
                                type="button"
                                className="px-3 py-1.5 rounded-lg bg-violet-50 hover:bg-violet-100 text-violet-700 font-semibold text-[11px] shrink-0 self-end sm:self-auto"
                              >
                                Xem & Nạp lại
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                /* Generate Tab View */
                <>
              {/* Progress Stepper during generation */}
              {aiGenerating && (
                <div className="p-4 rounded-xl bg-violet-50/60 border border-violet-200/80 space-y-3 animate-pulse">
                  <div className="flex items-center justify-between text-violet-900 font-semibold text-xs">
                    <span>Tiến trình thiết kế khảo sát khoa học:</span>
                    <span className="font-mono text-[11px]">
                      {aiGenStage === 'ANALYZING' && 'Bước 1/3: Phân tích mục tiêu'}
                      {aiGenStage === 'STRUCTURING' && 'Bước 2/3: Lập cấu trúc bảng hỏi'}
                      {aiGenStage === 'VALIDATING' && 'Bước 3/3: Kiểm định tính khách quan'}
                    </span>
                  </div>
                  <div className="w-full bg-violet-200/60 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-violet-600 h-1.5 rounded-full transition-all duration-300"
                      style={{
                        width:
                          aiGenStage === 'ANALYZING'
                            ? '35%'
                            : aiGenStage === 'STRUCTURING'
                            ? '70%'
                            : '95%'
                      }}
                    />
                  </div>
                  <p className="text-violet-700 text-[11px] italic">
                    {aiGenStage === 'ANALYZING' && 'Đang phân tích đối tượng và trích xuất chỉ số nghiên cứu theo tiêu chuẩn AAPOR...'}
                    {aiGenStage === 'STRUCTURING' && 'Đang sinh cấu trúc câu hỏi đa dạng (Likert, Matrix tiêu chí, Ranking thứ tự)...'}
                    {aiGenStage === 'VALIDATING' && 'Đang loại trừ câu hỏi kép, câu hỏi dẫn dắt và chuẩn hóa phương án...'}
                  </p>
                </div>
              )}

              {/* Preview mode if generated */}
              {generatedDraftPreview ? (
                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-emerald-50/80 border border-emerald-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-900 text-xs">
                        ✓ Bản nháp đã sẵn sàng ({generatedDraftPreview.questions?.length || 0} câu hỏi)
                      </span>
                      {generatedDraftPreview.ai_metadata?.validation && (
                        <span className="text-[10px] font-mono text-emerald-800 bg-emerald-100/80 px-2 py-0.5 rounded-md">
                          Tính khách quan: {generatedDraftPreview.ai_metadata.validation.objectivity_score}/100
                        </span>
                      )}
                    </div>
                    <div className="font-semibold text-slate-800 text-sm">{generatedDraftPreview.title}</div>
                    <div className="text-slate-600 text-[11px]">{generatedDraftPreview.description}</div>
                  </div>

                  <div className="border border-slate-200 rounded-xl p-3 bg-slate-50/50 max-h-56 overflow-y-auto space-y-2">
                    <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                      Danh sách câu hỏi dự kiến áp dụng:
                    </div>
                    {generatedDraftPreview.questions?.map((q: any, i: number) => (
                      <div key={i} className="p-2 bg-white rounded-lg border border-slate-200/80 flex items-start gap-2">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-600 shrink-0 mt-0.5">
                          {q.question_type}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="text-slate-800 font-medium text-xs truncate">{q.title}</div>
                          {q.description && <div className="text-slate-400 text-[10px] truncate">{q.description}</div>}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2 flex justify-between items-center">
                    <button
                      onClick={() => setGeneratedDraftPreview(null)}
                      className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl"
                    >
                      ← Chỉnh sửa thông số
                    </button>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setAiModalOpen(false)}
                        className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                      >
                        Đóng
                      </button>
                      <button
                        onClick={handleApplyDraft}
                        className="px-5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs transition-all flex items-center gap-1.5"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Áp dụng vào bảng thiết kế</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* Form Input Mode */
                <div className="space-y-3.5">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Chủ đề nghiên cứu / Mục tiêu khảo sát (*)
                    </label>
                    <input
                      type="text"
                      placeholder="Ví dụ: Đánh giá sự hài lòng và mức độ gắn kết của nhân viên công nghệ thông tin"
                      value={aiTopic}
                      onChange={(e) => setAiTopic(e.target.value)}
                      className="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-violet-600 focus:outline-hidden"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1">
                        Đối tượng tham gia
                      </label>
                      <input
                        type="text"
                        placeholder="Ví dụ: Lập trình viên, kỹ sư DevOps từ 1-5 năm kinh nghiệm"
                        value={aiAudience}
                        onChange={(e) => setAiAudience(e.target.value)}
                        className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-violet-600 focus:outline-hidden"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1">
                        Số lượng câu hỏi mong muốn
                      </label>
                      <select
                        value={aiQuestionCount}
                        onChange={(e) => setAiQuestionCount(Number(e.target.value))}
                        className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-violet-600 focus:outline-hidden"
                      >
                        <option value={5}>5 câu (Khảo sát nhanh 2-3 phút)</option>
                        <option value={7}>7 câu (Tiêu chuẩn cân bằng 5 phút)</option>
                        <option value={10}>10 câu (Nghiên cứu chuyên sâu 8-10 phút)</option>
                        <option value={12}>12 câu (Toàn diện học thuật)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Mục tiêu nghiên cứu hoặc Giả thuyết cần kiểm định (Tùy chọn)
                    </label>
                    <textarea
                      rows={2}
                      placeholder="Ví dụ: Cần so sánh chế độ đãi ngộ so với lộ trình thăng tiến và đo lường chỉ số eNPS"
                      value={aiObjectives}
                      onChange={(e) => setAiObjectives(e.target.value)}
                      className="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-violet-600 focus:outline-hidden resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                      Định dạng câu hỏi ưu tiên bao hàm:
                    </label>
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        { id: 'matrix', label: 'Ma trận tiêu chí (Matrix)' },
                        { id: 'ranking', label: 'Xếp hạng ưu tiên (Ranking)' },
                        { id: 'likert', label: 'Thang đo Likert 5 mức' },
                        { id: 'linear_scale', label: 'Thang điểm NPS (1-10)' },
                        { id: 'single_choice', label: 'Trắc nghiệm đơn' },
                        { id: 'long_text', label: 'Đóng góp mở' }
                      ].map((type) => {
                        const isSelected = aiPreferredTypes.includes(type.id);
                        return (
                          <button
                            key={type.id}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                setAiPreferredTypes(aiPreferredTypes.filter((t) => t !== type.id));
                              } else {
                                setAiPreferredTypes([...aiPreferredTypes, type.id]);
                              }
                            }}
                            className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${
                              isSelected
                                ? 'bg-violet-600 text-white border-violet-600'
                                : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                            }`}
                          >
                            {isSelected ? '✓ ' : '+ '}
                            {type.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="pt-2 flex justify-end gap-2 border-t border-slate-100">
                    <button
                      onClick={() => setAiModalOpen(false)}
                      className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                    >
                      Hủy
                    </button>
                    <button
                      disabled={aiGenerating}
                      onClick={handleAIGenerate}
                      className="px-5 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-700 rounded-xl shadow-xs transition-all disabled:opacity-50 flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{aiGenerating ? 'Đang phân tích...' : 'Thiết kế khảo sát ngay'}</span>
                    </button>
                  </div>
                </div>
              )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Enhanced AI Audit Issues Drawer / Modal */}
      {auditOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-100 overflow-hidden flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-amber-50/60">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Báo cáo kiểm định chất lượng câu hỏi</h3>
                  <p className="text-[10px] text-slate-500">Phát hiện câu hỏi dẫn dắt, câu hỏi kép và thiên lệch phương án</p>
                </div>
              </div>
              <button onClick={() => setAuditOpen(false)} className="text-slate-400 hover:text-slate-600 p-1 rounded-lg">
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto flex-1 text-xs">
              {auditIssues.length === 0 ? (
                <div className="text-center py-6 text-slate-600 space-y-2">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
                  <p className="text-sm font-semibold text-slate-800">Tất cả câu hỏi đều đạt chuẩn khoa học!</p>
                  <p className="text-xs text-slate-400">Không phát hiện câu hỏi dẫn dắt hoặc thiên lệch định dạng.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between bg-amber-100/60 text-amber-900 p-2.5 rounded-xl text-[11px] font-medium">
                    <span>Phát hiện <strong>{auditIssues.length}</strong> vấn đề có thể làm méo mó dữ liệu:</span>
                    <div className="flex items-center gap-2">
                      {auditIssues.filter((i) => i.auto_fix_title).length > 1 && (
                        <button
                          onClick={handleApplyAllAutoFixes}
                          className="px-2 py-0.5 text-[10px] font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-md transition-colors flex items-center gap-1 shadow-2xs"
                        >
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Sửa tất cả ({auditIssues.filter((i) => i.auto_fix_title).length})</span>
                        </button>
                      )}
                      <span className="font-mono text-[10px] bg-amber-200/80 px-2 py-0.5 rounded-md">AAPOR Standard</span>
                    </div>
                  </div>

                  {auditIssues.map((issue, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200 text-xs space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-bold text-amber-950 text-xs line-clamp-1">{issue.question_title}</div>
                        <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 bg-amber-200 text-amber-900 rounded-md shrink-0">
                          {issue.issue_type}
                        </span>
                      </div>
                      <div className="text-amber-800 text-[11px] leading-relaxed">{issue.explanation}</div>
                      <div className="text-slate-600 italic text-[11px]">💡 Gợi ý: {issue.suggestion}</div>
                      
                      {issue.auto_fix_title && (
                        <div className="pt-1 flex items-center justify-between border-t border-amber-200/60">
                          <span className="text-[10px] text-slate-500 italic truncate max-w-xs">
                            Sửa thành: "{issue.auto_fix_title}"
                          </span>
                          <button
                            onClick={() => handleApplyAutoFix(issue)}
                            className="px-2.5 py-1 text-[11px] font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 shadow-2xs transition-all shrink-0 flex items-center gap-1"
                          >
                            <span>✓ Tự động sửa</span>
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="pt-2 flex justify-end border-t border-slate-100">
                <button
                  onClick={() => setAuditOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-xl"
                >
                  Đã hiểu
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Share Modal with Real QR Code */}
      {shareOpen && (
        <ShareModal
          isOpen={true}
          onClose={() => setShareOpen(false)}
          surveyTitle={survey.title}
          publicSlug={survey.public_slug}
        />
      )}

      {/* Survey Version History Modal */}
      {isVersionModalOpen && survey.id && (
        <SurveyVersionHistoryModal
          isOpen={true}
          onClose={() => setIsVersionModalOpen(false)}
          surveyId={survey.id}
          currentVersion={survey.version}
          onRestoreQuestions={(restoredQuestions) => {
            setSurvey((prev) => ({ ...prev, questions: restoredQuestions }));
            setSaveStatus('Chưa lưu');
            setToastMessage(`Đã nạp cấu trúc ${restoredQuestions.length} câu hỏi từ phiên bản lịch sử vào bảng thiết kế!`);
            setTimeout(() => setToastMessage(null), 5000);
          }}
        />
      )}

      {/* Survey Settings & Webhook Alert Modal */}
      {isSettingsModalOpen && survey.id && (
        <SurveySettingsModal
          isOpen={true}
          onClose={() => setIsSettingsModalOpen(false)}
          surveyId={survey.id}
          currentSettings={survey.settings || {}}
          onSaveSettings={async (updatedSettings) => {
            await api.updateSurvey(survey.id, { settings: updatedSettings });
            setSurvey((prev) => ({ ...prev, settings: updatedSettings }));
            setToastMessage('Đã lưu cấu hình khảo sát và webhook thành công!');
            setTimeout(() => setToastMessage(null), 4000);
          }}
        />
      )}

      {/* Survey Logic & DAG Branching Simulator Modal */}
      {isLogicSimulatorOpen && survey.id && (
        <SurveyLogicSimulatorModal
          isOpen={true}
          onClose={() => setIsLogicSimulatorOpen(false)}
          surveyId={survey.id}
          surveyTitle={survey.title}
        />
      )}

      {/* Multilingual Localization Studio Modal */}
      {isTranslationModalOpen && survey.id && (
        <SurveyTranslationModal
          isOpen={true}
          onClose={() => setIsTranslationModalOpen(false)}
          surveyId={survey.id}
          onSuccess={() => loadSurvey(survey.id)}
        />
      )}

      {/* Cognitive Pre-Testing & Ambiguity Diagnostics Modal */}
      {isCognitivePretestOpen && (
        <CognitivePretestModal
          isOpen={true}
          onClose={() => setIsCognitivePretestOpen(false)}
          surveyId={survey.id || undefined}
          surveyTitle={survey.title}
          questions={survey.questions}
          onApplyFix={handleApplyCognitiveFix}
          onApplyAllFixes={handleApplyAllCognitiveFixes}
        />
      )}

      {/* Floating Toast Feedback */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900/95 text-white px-4 py-3 rounded-2xl shadow-xl border border-slate-700/80 text-xs flex items-center gap-2.5 transition-all animate-in fade-in slide-in-from-bottom-2 duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="font-medium">{toastMessage}</span>
        </div>
      )}
    </div>
  );
};
