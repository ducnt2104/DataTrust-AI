import React, { useState, useEffect } from 'react';
import {
  X, Brain, Sparkles, AlertTriangle, CheckCircle2, Clock, Users,
  TrendingUp, Award, HelpCircle, ArrowRight, Check, RefreshCw,
  BookOpen, ShieldCheck, AlertCircle, Zap, Eye, ChevronRight
} from 'lucide-react';
import { api } from '../api/client';
import { Question, CognitivePretestReport, CognitiveIssue } from '../types/survey';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  surveyId?: string;
  surveyTitle: string;
  questions: Question[];
  onApplyFix?: (questionId: string, newTitle: string, newOptions?: any[]) => void;
  onApplyAllFixes?: (fixedQuestions: Question[]) => void;
}

export const CognitivePretestModal: React.FC<Props> = ({
  isOpen,
  onClose,
  surveyId,
  surveyTitle,
  questions,
  onApplyFix,
  onApplyAllFixes
}) => {
  const [activeTab, setActiveTab] = useState<'issues' | 'personas' | 'fatigue'>('issues');
  const [report, setReport] = useState<CognitivePretestReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [appliedIssues, setAppliedIssues] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      runAudit();
    }
  }, [isOpen, surveyId, questions]);

  const runAudit = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      // Ưu tiên chạy pretest trên bản thảo câu hỏi hiện thời
      const res = await api.runDraftCognitivePretest({
        survey_id: surveyId,
        title: surveyTitle,
        questions: questions
      });
      setReport(res);
      setAppliedIssues(new Set());
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Lỗi khi thực hiện kiểm nghiệm nhận thức bảng hỏi.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplySingleFix = (issue: CognitiveIssue) => {
    if (!issue.auto_fix_title && !issue.suggested_options) return;
    if (onApplyFix) {
      onApplyFix(
        issue.question_id,
        issue.auto_fix_title || issue.question_title,
        issue.suggested_options || undefined
      );
    }
    setAppliedIssues(prev => new Set(prev).add(issue.question_id + issue.issue_type));
  };

  const handleApplyAll = () => {
    if (!report || !onApplyFix) return;
    const autoFixable = report.issues.filter(i => i.auto_fix_title || i.suggested_options);
    if (!window.confirm(`Bạn có chắc chắn muốn áp dụng tự động toàn bộ ${autoFixable.length} gợi ý chuẩn hóa học thuật?`)) {
      return;
    }

    const newApplied = new Set<string>();
    autoFixable.forEach(issue => {
      onApplyFix(
        issue.question_id,
        issue.auto_fix_title || issue.question_title,
        issue.suggested_options || undefined
      );
      newApplied.add(issue.question_id + issue.issue_type);
    });
    setAppliedIssues(newApplied);
  };

  if (!isOpen) return null;

  const autoFixableCount = report?.issues.filter(i => (i.auto_fix_title || i.suggested_options) && !appliedIssues.has(i.question_id + i.issue_type)).length || 0;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="cognitive-pretest-title"
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-5xl overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in zoom-in-95 duration-200"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-700 via-indigo-700 to-indigo-800 px-6 py-4 text-white flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-white/10 rounded-xl backdrop-blur-md">
              <Brain className="w-6 h-6 text-purple-200 animate-pulse" />
            </div>
            <div>
              <h2 id="cognitive-pretest-title" className="text-xl font-bold flex items-center gap-2">
                Thử Nghiệm Nhận Thức Bảng Hỏi & Chẩn Đoán Mơ Hồ
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/30 border border-purple-300/30 text-purple-100 font-medium">
                  Tourangeau & Don Dillman Standards
                </span>
              </h2>
              <p className="text-xs text-purple-100/90 mt-0.5">
                Kiểm định tiền xuất bản: Phát hiện câu hỏi dẫn dắt, ghép đôi, phủ định kép và giả lập phản ứng người tham gia
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng cửa sổ thử nghiệm nhận thức"
            className="p-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors focus:outline-hidden focus:ring-2 focus:ring-white/50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-slate-700">
          {errorMsg && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3">
              <RefreshCw className="w-8 h-8 text-purple-600 animate-spin" />
              <p className="text-sm font-semibold text-slate-600">
                Đang phân tích độ dễ đọc, quét mơ hồ cấu trúc và giả lập Persona nhận thức...
              </p>
            </div>
          ) : report ? (
            <>
              {/* Top Scoreboard Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {/* 1. Design Quality Score */}
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50/50 p-4 rounded-xl border border-purple-200 shadow-xs">
                  <span className="text-xs font-semibold text-purple-800 block">Điểm Thiết Kế (SDQI)</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-2xl font-black text-purple-900">{report.design_quality_score}</span>
                    <span className="text-xs text-purple-600">/ 100</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-bold ml-auto ${
                      report.academic_grade === 'A+' ? 'bg-emerald-100 text-emerald-800' :
                      report.academic_grade === 'A' ? 'bg-teal-100 text-teal-800' :
                      report.academic_grade === 'B' ? 'bg-amber-100 text-amber-800' :
                      'bg-rose-100 text-rose-800'
                    }`}>
                      Hạng {report.academic_grade}
                    </span>
                  </div>
                </div>

                {/* 2. Readability Ease */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <span className="text-xs text-slate-500 block">Độ Dễ Đọc (Flesch)</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-2xl font-black text-slate-900">{report.readability_score}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                      report.readability_level === 'EASY' ? 'bg-emerald-100 text-emerald-700' :
                      report.readability_level === 'MODERATE' ? 'bg-blue-100 text-blue-700' :
                      'bg-amber-100 text-amber-700'
                    }`}>
                      {report.readability_level === 'EASY' ? 'Dễ hiểu' : report.readability_level === 'MODERATE' ? 'Trung bình' : 'Hàn lâm'}
                    </span>
                  </div>
                </div>

                {/* 3. Duration */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <span className="text-xs text-slate-500 block">Thời Gian Ước Tính</span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-2xl font-black text-slate-900">{report.estimated_duration_minutes}</span>
                    <span className="text-xs text-slate-500">phút</span>
                  </div>
                </div>

                {/* 4. Words & Questions */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <span className="text-xs text-slate-500 block">Quy Mô Bảng Hỏi</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-2xl font-black text-slate-900">{report.total_questions}</span>
                    <span className="text-xs text-slate-500">câu ({report.total_words} từ)</span>
                  </div>
                </div>

                {/* 5. Issues Count */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <span className="text-xs text-slate-500 block">Vấn Đề Phát Hiện</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className={`text-2xl font-black ${report.critical_issues_count > 0 ? 'text-rose-600' : (report.total_issues_count > 0 ? 'text-amber-600' : 'text-emerald-600')}`}>
                      {report.total_issues_count}
                    </span>
                    <span className="text-xs text-slate-400">
                      ({report.critical_issues_count} nghiêm trọng)
                    </span>
                  </div>
                </div>
              </div>

              {/* Methodological Summary Alert */}
              <div className={`p-4 rounded-xl border text-xs leading-relaxed flex items-start gap-3 ${
                report.academic_grade === 'A+' || report.academic_grade === 'A'
                  ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                  : 'bg-amber-50/70 border-amber-200 text-amber-900'
              }`}>
                <ShieldCheck className="w-5 h-5 shrink-0 mt-0.5 text-purple-600" />
                <div>
                  <span className="font-bold block mb-0.5">Nhận định kiểm định nhận thức:</span>
                  <span>{report.methodological_summary}</span>
                </div>
              </div>

              {/* Navigation Tabs Header */}
              <div className="border-b border-slate-200 flex items-center justify-between">
                <div className="flex space-x-1">
                  <button
                    onClick={() => setActiveTab('issues')}
                    className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                      activeTab === 'issues'
                        ? 'border-purple-600 text-purple-700 bg-purple-50/30'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <AlertTriangle className="w-4 h-4" />
                    <span>Lỗi Cấu Trúc & Thiên Lệch ({report.total_issues_count})</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('personas')}
                    className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                      activeTab === 'personas'
                        ? 'border-purple-600 text-purple-700 bg-purple-50/30'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <Users className="w-4 h-4" />
                    <span>Giả Lập Persona Nhận Thức (3)</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('fatigue')}
                    className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                      activeTab === 'fatigue'
                        ? 'border-purple-600 text-purple-700 bg-purple-50/30'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <TrendingUp className="w-4 h-4" />
                    <span>Đường Cong Mệt Mỏi Nhận Thức</span>
                  </button>
                </div>

                {activeTab === 'issues' && autoFixableCount > 0 && onApplyFix && (
                  <button
                    onClick={handleApplyAll}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-all"
                  >
                    <Zap className="w-3.5 h-3.5 fill-white" />
                    <span>Tự động sửa toàn bộ ({autoFixableCount})</span>
                  </button>
                )}
              </div>

              {/* Tab 1: Issues Diagnostics */}
              {activeTab === 'issues' && (
                <div className="space-y-3.5 animate-in fade-in duration-200">
                  {report.issues.length === 0 ? (
                    <div className="py-12 text-center bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
                      <h4 className="text-sm font-bold text-slate-900">Không phát hiện lỗi cấu trúc câu hỏi!</h4>
                      <p className="text-xs text-slate-500 max-w-md mx-auto">
                        Bảng hỏi tuân thủ đầy đủ các nguyên tắc thiết kế câu hỏi đơn biến, trung lập ngữ nghĩa và không mồi chài theo chuẩn AAPOR.
                      </p>
                    </div>
                  ) : (
                    report.issues.map((issue, idx) => {
                      const isApplied = appliedIssues.has(issue.question_id + issue.issue_type);
                      return (
                        <div
                          key={`${issue.question_id}_${idx}`}
                          className={`p-4 rounded-xl border transition-all ${
                            isApplied
                              ? 'bg-emerald-50/40 border-emerald-300 opacity-80'
                              : issue.severity === 'CRITICAL'
                              ? 'bg-rose-50/30 border-rose-200 hover:border-rose-300'
                              : 'bg-amber-50/30 border-amber-200 hover:border-amber-300'
                          }`}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                            <div className="flex items-center gap-2">
                              <span className="w-6 h-6 rounded-md bg-slate-800 text-white text-xs font-bold flex items-center justify-center">
                                Q{issue.question_order}
                              </span>
                              <span className="text-xs font-bold text-slate-900">
                                {issue.question_title}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                                issue.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' :
                                issue.severity === 'WARNING' ? 'bg-amber-100 text-amber-800' :
                                'bg-slate-100 text-slate-700'
                              }`}>
                                {issue.severity}
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-purple-100 text-purple-800">
                                {issue.issue_type}
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-slate-100 text-slate-600">
                                {issue.cognitive_dimension}
                              </span>
                            </div>
                          </div>

                          <p className="text-xs text-slate-700 mb-2 leading-relaxed">
                            {issue.explanation}
                          </p>

                          <div className="text-[11px] text-slate-500 mb-3 italic flex items-center gap-1.5">
                            <BookOpen className="w-3.5 h-3.5 text-purple-500 shrink-0" />
                            <span>{issue.academic_rule}</span>
                          </div>

                          {/* Auto-fix suggestion box */}
                          {(issue.auto_fix_title || issue.suggested_options) && (
                            <div className="bg-white p-3 rounded-lg border border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs">
                              <div>
                                <span className="text-[11px] text-purple-700 font-bold block mb-1">
                                  Đề xuất viết lại theo chuẩn Don Dillman:
                                </span>
                                {issue.auto_fix_title && (
                                  <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                                    <ArrowRight className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                                    <span>{issue.auto_fix_title}</span>
                                  </div>
                                )}
                                {issue.suggested_options && (
                                  <div className="mt-1 text-slate-600 text-[11px]">
                                    Phương án neo tần suất: {issue.suggested_options.map(o => `"${o.label}"`).join(', ')}
                                  </div>
                                )}
                              </div>

                              {onApplyFix && (
                                <button
                                  type="button"
                                  onClick={() => handleApplySingleFix(issue)}
                                  disabled={isApplied}
                                  className={`shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                    isApplied
                                      ? 'bg-emerald-100 text-emerald-800 cursor-default'
                                      : 'bg-purple-600 hover:bg-purple-700 text-white shadow-xs'
                                  }`}
                                >
                                  {isApplied ? (
                                    <>
                                      <Check className="w-3.5 h-3.5" />
                                      <span>Đã áp dụng</span>
                                    </>
                                  ) : (
                                    <>
                                      <Zap className="w-3.5 h-3.5" />
                                      <span>Áp dụng gợi ý</span>
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {/* Tab 2: Persona Simulations */}
              {activeTab === 'personas' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-in fade-in duration-200">
                  {report.personas.map((persona) => (
                    <div
                      key={persona.persona_id}
                      className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between space-y-4"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                            persona.overall_difficulty_rating === 'SMOOTH' ? 'bg-emerald-100 text-emerald-800' :
                            persona.overall_difficulty_rating === 'ACCEPTABLE' ? 'bg-blue-100 text-blue-800' :
                            persona.overall_difficulty_rating === 'CHALLENGING' ? 'bg-amber-100 text-amber-800' :
                            'bg-rose-100 text-rose-800'
                          }`}>
                            {persona.overall_difficulty_rating}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">
                            ~{Math.round(persona.predicted_completion_time_sec)}s
                          </span>
                        </div>

                        <h4 className="text-sm font-bold text-slate-900 mb-1">
                          {persona.persona_name}
                        </h4>
                        <p className="text-xs text-purple-700 font-medium mb-3">
                          {persona.persona_demographic}
                        </p>
                        <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                          {persona.cognitive_style}
                        </p>

                        <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs space-y-1.5 mb-3">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Nguy cơ bỏ dở:</span>
                            <span className={`font-bold ${persona.predicted_dropout_probability > 0.4 ? 'text-rose-600' : 'text-slate-900'}`}>
                              {Math.round(persona.predicted_dropout_probability * 100)}%
                            </span>
                          </div>
                          {persona.bottleneck_question_ids.length > 0 && (
                            <div className="pt-1 border-t border-slate-200/60">
                              <span className="text-slate-500 text-[11px] block">Câu hỏi nghẽn nhận thức:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {persona.bottleneck_question_ids.map(qid => (
                                  <span key={qid} className="text-[10px] bg-slate-200 text-slate-800 px-1.5 py-0.5 rounded-sm font-mono">
                                    {qid}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="bg-purple-50/60 p-3 rounded-lg border border-purple-100 text-xs italic text-purple-950">
                        &ldquo;{persona.qualitative_feedback}&rdquo;
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 3: Fatigue Curve */}
              {activeTab === 'fatigue' && (
                <div className="space-y-4 bg-white p-5 rounded-xl border border-slate-200 animate-in fade-in duration-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">
                        Mô Phỏng Đường Cong Mệt Mỏi & Nguy Cơ Bỏ Cuộc (Cumulative Dropout Forecast)
                      </h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Tính toán sự suy giảm độ tập trung nhận thức qua từng câu hỏi dựa trên thời lượng đọc và độ phức tạp
                      </p>
                    </div>
                    <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1 rounded-full font-medium">
                      Thời lượng ước tính: {report.estimated_duration_minutes} phút
                    </span>
                  </div>

                  <div className="space-y-2 pt-2">
                    {report.fatigue_curve.map((point) => (
                      <div key={point.question_index} className="flex items-center gap-3 text-xs">
                        <span className="w-7 text-right font-bold text-slate-600 shrink-0">
                          Q{point.question_index}
                        </span>
                        <div className="flex-1 bg-slate-100 h-5 rounded-md overflow-hidden relative flex">
                          <div
                            style={{ width: `${point.fatigue_percentage}%` }}
                            className={`h-full transition-all duration-500 ${
                              point.fatigue_percentage > 70 ? 'bg-rose-500' :
                              point.fatigue_percentage > 45 ? 'bg-amber-500' :
                              'bg-indigo-500'
                            }`}
                          />
                          <span className="absolute inset-0 flex items-center justify-between px-2 text-[10px] text-slate-800 font-semibold mix-blend-difference text-white">
                            <span>{point.question_title}</span>
                            <span>{point.cumulative_time_seconds}s</span>
                          </span>
                        </div>
                        <span className="w-16 text-right font-mono text-[11px] text-slate-500 shrink-0">
                          {point.fatigue_percentage}% mệt
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
                    <span>* Điểm bão hòa nhận thức xảy ra khi thời gian vượt quá 3 phút hoặc số lượng câu hỏi &gt; 15 câu.</span>
                    <span className="font-bold text-purple-700">Khuyến nghị độ dài lý tưởng: 5 - 12 câu</span>
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 px-6 py-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Chuẩn mực thiết kế AAPOR & ISO 20252:2019 Section 4.3</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={runAudit}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Chẩn đoán lại</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-900 text-white font-semibold transition-all"
            >
              Đóng
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
