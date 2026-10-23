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
  Printer
} from 'lucide-react';
import { api } from '../api/client';
import { Question, QuestionType, Survey } from '../types/survey';
import { QuestionRenderer } from '../components/QuestionRenderer';
import { ShareModal } from '../components/ShareModal';
import { StatusBadge } from '../components/StatusBadge';

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
  const [aiTopic, setAiTopic] = useState('');
  const [aiAudience, setAiAudience] = useState('');
  const [aiGenerating, setAiGenerating] = useState(false);

  // AI Audit State
  const [auditIssues, setAuditIssues] = useState<any[]>([]);
  const [auditOpen, setAuditOpen] = useState(false);

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

  // AI Generation Handler
  const handleAIGenerate = async () => {
    if (!aiTopic.trim()) {
      alert('Vui lòng nhập chủ đề khảo sát.');
      return;
    }
    try {
      setAiGenerating(true);
      const res = await api.generateSurveyDraft(aiTopic, aiAudience);
      if (res && res.questions) {
        const formattedQuestions: Question[] = res.questions.map((q: any, i: number) => ({
          id: crypto.randomUUID(),
          order_index: i,
          question_type: q.question_type || 'single_choice',
          title: q.title || `Câu hỏi ${i + 1}`,
          description: q.description || '',
          is_required: Boolean(q.is_required),
          options: q.options || [],
          logic_rules: []
        }));

        setSurvey((prev) => ({
          ...prev,
          title: res.title || prev.title,
          description: res.description || prev.description,
          instructions: res.instructions || prev.instructions,
          questions: formattedQuestions
        }));
        setAiModalOpen(false);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi sinh bản nháp bằng AI');
    } finally {
      setAiGenerating(false);
    }
  };

  // AI Audit Handler
  const handleAIAudit = async () => {
    try {
      const res = await api.auditQuestions(survey.questions);
      setAuditIssues(res.issues || []);
      setAuditOpen(true);
    } catch (err) {
      alert('Không thể thực hiện kiểm định AI.');
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
            onClick={() => setAiModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-violet-50 text-violet-700 hover:bg-violet-100 border border-violet-200 transition-all"
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

                  {/* Question Options Footer (Required toggle) */}
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

                    {/* Logic Branching rule display indicator */}
                    {qIndex > 0 && (
                      <span className="text-[11px] text-slate-400">
                        {q.logic_rules?.length ? `Đã cấu hình ${q.logic_rules.length} quy tắc rẽ nhánh` : 'Chưa rẽ nhánh'}
                      </span>
                    )}
                  </div>
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

      {/* AI Survey Generator Modal */}
      {aiModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-violet-50/60">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-violet-600" />
                <h3 className="font-bold text-slate-900">AI Survey Assistant</h3>
              </div>
              <button onClick={() => setAiModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Chủ đề khảo sát mong muốn
                </label>
                <input
                  type="text"
                  placeholder="Ví dụ: Đánh giá chất lượng dịch vụ vận tải công cộng tại TP.HCM"
                  value={aiTopic}
                  onChange={(e) => setAiTopic(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-violet-600 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Đối tượng tham gia (Tùy chọn)
                </label>
                <input
                  type="text"
                  placeholder="Ví dụ: Học sinh, sinh viên, người đi làm thường xuyên"
                  value={aiAudience}
                  onChange={(e) => setAiAudience(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-violet-600 focus:outline-hidden"
                />
              </div>

              <p className="text-xs text-slate-500 leading-relaxed">
                AI sẽ tự động thiết kế dàn câu hỏi khoa học (nhân khẩu học, thang đo Likert, câu hỏi trắc nghiệm, và đóng góp mở) đảm bảo độ tin cậy và không thiên lệch.
              </p>

              <div className="pt-2 flex justify-end gap-2">
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
                  <span>{aiGenerating ? 'Đang phân tích & sinh câu hỏi...' : 'Tạo dàn ý khảo sát'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Audit Issues Drawer / Modal */}
      {auditOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-amber-50/60">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <h3 className="font-bold text-slate-900">Báo cáo kiểm định câu hỏi</h3>
              </div>
              <button onClick={() => setAuditOpen(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              {auditIssues.length === 0 ? (
                <div className="text-center py-6 text-slate-600 space-y-2">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
                  <p className="text-sm font-semibold">Tất cả câu hỏi đều đạt chuẩn khoa học!</p>
                  <p className="text-xs text-slate-400">Không phát hiện câu hỏi dẫn dắt hoặc thiên lệch định dạng.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-slate-600">
                    Phát hiện <span className="font-bold text-amber-700">{auditIssues.length}</span> vấn đề có thể ảnh hưởng đến tính khách quan:
                  </p>
                  {auditIssues.map((issue, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-amber-50/50 border border-amber-200 text-xs space-y-1">
                      <div className="font-bold text-amber-900 line-clamp-1">{issue.question_title}</div>
                      <div className="text-amber-800">{issue.explanation}</div>
                      <div className="text-slate-600 italic">💡 Gợi ý: {issue.suggestion}</div>
                    </div>
                  ))}
                </div>
              )}

              <div className="pt-2 flex justify-end">
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
    </div>
  );
};
