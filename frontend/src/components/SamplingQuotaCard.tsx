import React, { useState, useEffect } from 'react';
import {
  PieChart,
  Users,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Settings,
  RefreshCw,
  Sliders,
  ShieldCheck,
  X
} from 'lucide-react';
import { api } from '../api/client';
import { SamplingQuotaReport, SamplingQuotaRule, Question } from '../types/survey';

interface Props {
  surveyId: string;
  questions: Array<{ id: string; title: string; question_type: string; options?: string[] }>;
}

export const SamplingQuotaCard: React.FC<Props> = ({ surveyId, questions }) => {
  const [report, setReport] = useState<SamplingQuotaReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);
  const [rules, setRules] = useState<SamplingQuotaRule[]>([]);
  const [saving, setSaving] = useState<boolean>(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Form thêm rule mới
  const [newRuleName, setNewRuleName] = useState<string>('');
  const [selectedQuestionId, setSelectedQuestionId] = useState<string>('');
  const [targetValue, setTargetValue] = useState<string>('');
  const [maxTarget, setMaxTarget] = useState<number>(50);
  const [action, setAction] = useState<'flag_overflow' | 'screen_out'>('flag_overflow');

  useEffect(() => {
    loadQuotas();
  }, [surveyId]);

  const loadQuotas = async () => {
    try {
      setLoading(true);
      const data = await api.getSurveyQuotas(surveyId);
      setReport(data);
      // Nạp rules cho form cấu hình
      const currentRules: SamplingQuotaRule[] = data.cells.map((c) => ({
        id: c.cell_id,
        name: c.name,
        question_id: c.question_id,
        target_value: c.target_value,
        max_target: c.max_target,
        action: c.action
      }));
      setRules(currentRules);
    } catch (err: any) {
      console.error('Lỗi tải hạn ngạch mẫu:', err);
    } finally {
      setLoading(false);
    }
  };

  // Lọc các câu hỏi trắc nghiệm hỗ trợ chia hạn ngạch
  const choiceQuestions = questions.filter((q) =>
    ['single_choice', 'multiple_choice', 'dropdown'].includes(q.question_type)
  );

  const selectedQuestion = choiceQuestions.find((q) => q.id === selectedQuestionId);

  const handleAddRule = () => {
    if (!selectedQuestionId || !targetValue.trim()) {
      alert('Vui lòng chọn câu hỏi và phương án mục tiêu.');
      return;
    }
    const qTitle = selectedQuestion?.title || 'Nhóm';
    const ruleName = newRuleName.trim() || `${qTitle}: ${targetValue}`;
    const newRule: SamplingQuotaRule = {
      id: `quota_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      name: ruleName,
      question_id: selectedQuestionId,
      target_value: targetValue.trim(),
      max_target: maxTarget > 0 ? maxTarget : 50,
      action: action
    };
    setRules([...rules, newRule]);
    setNewRuleName('');
    setTargetValue('');
  };

  const handleRemoveRule = (index: number) => {
    const updated = [...rules];
    updated.splice(index, 1);
    setRules(updated);
  };

  const handleSaveQuotas = async () => {
    try {
      setSaving(true);
      setSaveMessage(null);
      await api.updateSurveyQuotas(surveyId, rules);
      setSaveMessage('✅ Đã lưu cấu hình hạn ngạch mẫu thành công!');
      await loadQuotas();
      setTimeout(() => {
        setIsConfigOpen(false);
        setSaveMessage(null);
      }, 1000);
    } catch (err: any) {
      setSaveMessage(`❌ Lỗi: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading && !report) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-2xs text-center text-slate-500 text-xs">
        Đang nạp dữ liệu hạn ngạch mẫu...
      </div>
    );
  }

  const cells = report?.cells || [];
  const hasQuotas = cells.length > 0;

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-600">
            <PieChart className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Kiểm Soát Hạn Ngạch Mẫu & Cân Bằng Phân Tầng
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 font-mono font-bold">
                AAPOR Quota Guard
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Kiểm soát tính đại diện nhân khẩu học (Giới tính, Độ tuổi, Địa lý) theo tiêu chuẩn khảo sát xã hội học
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadQuotas}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs flex items-center gap-1"
            title="Làm mới tiến độ hạn ngạch"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setIsConfigOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-xs font-semibold transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
            <span>Thiết Lập Hạn Ngạch</span>
          </button>
        </div>
      </div>

      {!hasQuotas ? (
        <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300 space-y-2">
          <Users className="w-8 h-8 mx-auto text-slate-400" />
          <h4 className="text-sm font-bold text-slate-700">Chưa thiết lập hạn ngạch cho khảo sát này</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Hạn ngạch mẫu giúp bạn đảm bảo cơ cấu người tham gia phản ánh chính xác phân bố dân số học mục tiêu, tránh thừa hoặc thiếu nhóm đối tượng.
          </p>
          <button
            onClick={() => setIsConfigOpen(true)}
            className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Thêm Hạn Ngạch Ngay</span>
          </button>
        </div>
      ) : (
        <>
          {/* Summary KPI Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
              <span className="text-[10px] text-slate-500 block">Số Ô Hạn Ngạch</span>
              <span className="text-base font-extrabold text-slate-900 font-mono">
                {report?.total_quota_cells} nhóm
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
              <span className="text-[10px] text-slate-500 block">Tiến Độ Toàn Cục</span>
              <span className="text-base font-extrabold text-indigo-600 font-mono">
                {report?.overall_completion_pct}%
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
              <span className="text-[10px] text-slate-500 block">Ô Đã Đầy Chỉ Tiêu</span>
              <span className="text-base font-extrabold text-emerald-600 font-mono">
                {report?.filled_cells} ô
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
              <span className="text-[10px] text-slate-500 block">Đã Thu Thập / Chỉ Tiêu</span>
              <span className="text-base font-extrabold text-slate-800 font-mono">
                {report?.overall_achieved_sum} / {report?.overall_target_sum}
              </span>
            </div>
          </div>

          {/* Quota Cells Progress List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
            {cells.map((cell) => {
              const isFilled = cell.status === 'filled';
              const isAlmost = cell.status === 'almost_full';
              return (
                <div
                  key={cell.cell_id}
                  className={`p-4 rounded-xl border transition-all ${
                    isFilled
                      ? 'bg-emerald-50/50 border-emerald-200'
                      : isAlmost
                      ? 'bg-amber-50/40 border-amber-200'
                      : 'bg-white border-slate-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-bold text-slate-900">{cell.name}</h4>
                        {isFilled ? (
                          <span className="text-[10px] px-1.5 py-0.2 rounded-sm bg-emerald-100 text-emerald-800 font-semibold border border-emerald-300">
                            Đã Đủ
                          </span>
                        ) : isAlmost ? (
                          <span className="text-[10px] px-1.5 py-0.2 rounded-sm bg-amber-100 text-amber-800 font-semibold border border-amber-300">
                            Sắp Đầy
                          </span>
                        ) : (
                          <span className="text-[10px] px-1.5 py-0.2 rounded-sm bg-slate-100 text-slate-600 font-semibold">
                            Đang Nhận
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-500 block">
                        Giá trị: <strong className="text-slate-700">"{cell.target_value}"</strong> • Quy tắc:{' '}
                        {cell.action === 'screen_out' ? 'Dừng nhận (Screen out)' : 'Ghi nhận vượt mức'}
                      </span>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-sm font-extrabold font-mono text-slate-900">
                        {cell.achieved_count} / {cell.max_target}
                      </span>
                      <span className="text-[10px] text-slate-400 block font-mono">
                        {cell.completion_pct}%
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden mt-3">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isFilled
                          ? 'bg-emerald-600'
                          : isAlmost
                          ? 'bg-amber-500'
                          : 'bg-indigo-600'
                      }`}
                      style={{ width: `${Math.min(100, cell.completion_pct)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1.5 font-mono">
                    <span>Còn thiếu: {cell.remaining_count} mẫu</span>
                    {cell.action === 'screen_out' && (
                      <span className="text-amber-700 font-sans">⚠️ Tự động ngắt khi đủ</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Configuration Modal */}
      {isConfigOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto"
          role="dialog"
          aria-modal="true"
        >
          <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-900 text-white">
              <div className="flex items-center gap-2.5">
                <Sliders className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold">Cấu Hình Hạn Ngạch Mẫu (Sampling Quotas)</h3>
              </div>
              <button
                onClick={() => setIsConfigOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              {saveMessage && (
                <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 font-medium">
                  {saveMessage}
                </div>
              )}

              {/* Form thêm Rule mới */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <h4 className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <Plus className="w-4 h-4 text-indigo-600" />
                  Thêm Ô Hạn Ngạch Nhân Khẩu Học Mới
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                      Câu hỏi nhân khẩu học:
                    </label>
                    <select
                      value={selectedQuestionId}
                      onChange={(e) => {
                        setSelectedQuestionId(e.target.value);
                        setTargetValue('');
                      }}
                      className="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden"
                    >
                      <option value="">-- Chọn câu hỏi trắc nghiệm --</option>
                      {choiceQuestions.map((q) => (
                        <option key={q.id} value={q.id}>
                          {q.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                      Phương án / Giá trị mục tiêu:
                    </label>
                    {selectedQuestion?.options && selectedQuestion.options.length > 0 ? (
                      <select
                        value={targetValue}
                        onChange={(e) => setTargetValue(e.target.value)}
                        className="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden"
                      >
                        <option value="">-- Chọn phương án --</option>
                        {selectedQuestion.options.map((opt: any) => {
                          const val = typeof opt === 'string' ? opt : opt.label || opt.text || '';
                          return (
                            <option key={val} value={val}>
                              {val}
                            </option>
                          );
                        })}
                      </select>
                    ) : (
                      <input
                        type="text"
                        placeholder="VD: Nam, Nữ, 18-24, v.v."
                        value={targetValue}
                        onChange={(e) => setTargetValue(e.target.value)}
                        className="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden"
                      />
                    )}
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                      Chỉ tiêu số lượng (N):
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={100000}
                      value={maxTarget}
                      onChange={(e) => setMaxTarget(Number(e.target.value))}
                      className="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 font-mono focus:outline-hidden"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                      Hành động khi đầy hạn ngạch:
                    </label>
                    <select
                      value={action}
                      onChange={(e) => setAction(e.target.value as any)}
                      className="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden"
                    >
                      <option value="flag_overflow">Gắn nhãn vượt hạn ngạch (Vẫn nhận dữ liệu)</option>
                      <option value="screen_out">Ngắt bài / Cảm ơn (Screen out - Không nhận)</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    onClick={handleAddRule}
                    type="button"
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-xs shadow-xs"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Thêm Vào Danh Sách
                  </button>
                </div>
              </div>

              {/* Danh sách các Rule hiện tại */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 text-xs">Danh Sách Hạn Ngạch Đang Thiết Lập ({rules.length})</h4>
                {rules.length === 0 ? (
                  <p className="text-slate-400 italic">Chưa có ô hạn ngạch nào trong danh sách.</p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {rules.map((r, idx) => (
                      <div
                        key={r.id || idx}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs"
                      >
                        <div className="space-y-0.5">
                          <span className="font-bold text-slate-800 block">{r.name}</span>
                          <span className="text-[10px] text-slate-500">
                            Giá trị: <strong>"{r.target_value}"</strong> | Chỉ tiêu: <strong>{r.max_target}</strong> | Hành động: {r.action === 'screen_out' ? 'Ngắt bài' : 'Gắn cờ'}
                          </span>
                        </div>
                        <button
                          onClick={() => handleRemoveRule(idx)}
                          className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Xóa ô hạn ngạch này"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 bg-slate-50">
              <button
                onClick={() => setIsConfigOpen(false)}
                className="px-4 py-1.5 bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-lg text-xs font-semibold"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleSaveQuotas}
                disabled={saving}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold shadow-xs disabled:opacity-50"
              >
                {saving ? 'Đang lưu...' : 'Lưu & Kích Hoạt Hạn Ngạch'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
