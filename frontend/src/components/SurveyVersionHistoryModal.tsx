import React, { useEffect, useState } from 'react';
import {
  X, History, Clock, FileText, CheckCircle2, RotateCcw,
  ChevronRight, Calendar, ArrowRight, Layers, Tag
} from 'lucide-react';
import { api } from '../api/client';

interface VersionItem {
  id: string;
  survey_id: string;
  version: number;
  title: string;
  description: string;
  questions_count: number;
  questions: any[];
  created_at: string;
}

interface Props {
  surveyId: string;
  currentVersion: number;
  isOpen: boolean;
  onClose: () => void;
  onRestoreQuestions?: (questions: any[]) => void;
}

export const SurveyVersionHistoryModal: React.FC<Props> = ({
  surveyId,
  currentVersion,
  isOpen,
  onClose,
  onRestoreQuestions
}) => {
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [selectedVer, setSelectedVer] = useState<VersionItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      loadVersions();
    }
  }, [isOpen, surveyId]);

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

  const loadVersions = async () => {
    try {
      setLoading(true);
      const data = await api.getSurveyVersions(surveyId);
      setVersions(data);
      if (data.length > 0) {
        // Mặc định chọn phiên bản mới nhất
        const cur = data.find(v => v.version === currentVersion) || data[data.length - 1];
        setSelectedVer(cur);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div 
        role="dialog"
        aria-modal="true"
        aria-labelledby="survey-version-history-modal-title"
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl overflow-hidden flex flex-col max-h-[88vh] animate-in fade-in zoom-in-95 duration-200"
      >
        
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 px-6 py-4 text-white flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/20 rounded-xl border border-indigo-400/30">
              <History className="w-6 h-6 text-indigo-300" />
            </div>
            <div>
              <h2 id="survey-version-history-modal-title" className="text-xl font-bold flex items-center gap-2">
                Lịch Sử Tiến Hóa Cấu Trúc Khảo Sát
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/30 border border-indigo-300/30 text-indigo-200 font-medium">
                  v{currentVersion} Hiện tại
                </span>
              </h2>
              <p className="text-xs text-indigo-200/80 mt-0.5">
                Theo dõi và kiểm chứng lịch sử thay đổi câu hỏi theo từng phiên bản (Schema Evolution &amp; Auditability)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng cửa sổ lịch sử phiên bản"
            className="p-1.5 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors focus:outline-hidden focus:ring-2 focus:ring-indigo-400"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body: 2 Columns */}
        <div className="flex-1 overflow-hidden flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-slate-200">
          
          {/* Left Column: Versions List */}
          <div className="w-full md:w-80 bg-slate-50/70 p-4 overflow-y-auto space-y-2 border-r border-slate-200">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-2 px-1">
              Các phiên bản đã lưu ({versions.length})
            </span>

            {loading ? (
              <div className="p-8 text-center text-slate-400 text-xs">Đang tải lịch sử...</div>
            ) : versions.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-xs">Chưa có lịch sử phiên bản nào.</div>
            ) : (
              versions.map((ver) => {
                const isSelected = selectedVer?.version === ver.version;
                const isCurrent = ver.version === currentVersion;
                return (
                  <button
                    key={ver.id}
                    onClick={() => setSelectedVer(ver)}
                    className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between ${
                      isSelected
                        ? 'border-indigo-500 bg-white ring-2 ring-indigo-500/10 shadow-xs'
                        : 'border-slate-200 hover:border-slate-300 bg-white/70'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-sm text-slate-900">Phiên bản v{ver.version}</span>
                        {isCurrent && (
                          <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.2 rounded-full">
                            Hiện tại
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                        <span className="flex items-center gap-1">
                          <Layers className="w-3 h-3 text-slate-400" />
                          {ver.questions_count} câu hỏi
                        </span>
                        <span>•</span>
                        <span>{new Date(ver.created_at).toLocaleDateString('vi-VN')}</span>
                      </div>
                    </div>
                    <ChevronRight className={`w-4 h-4 ${isSelected ? 'text-indigo-600' : 'text-slate-300'}`} />
                  </button>
                );
              })
            )}
          </div>

          {/* Right Column: Version Details & Question List */}
          <div className="flex-1 p-6 overflow-y-auto space-y-5 bg-white">
            {selectedVer ? (
              <>
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-slate-900">
                        Chi Tiết Phiên Bản v{selectedVer.version}
                      </h3>
                      {selectedVer.version === currentVersion ? (
                        <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold px-2 py-0.5 rounded-md">
                          Bản thiết kế đang mở
                        </span>
                      ) : (
                        <span className="text-xs bg-slate-100 text-slate-600 font-medium px-2 py-0.5 rounded-md">
                          Bản lưu lịch sử
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Thời điểm ghi nhận: {new Date(selectedVer.created_at).toLocaleString('vi-VN')}
                    </p>
                  </div>

                  {onRestoreQuestions && selectedVer.version !== currentVersion && (
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm(`Bạn có muốn nạp cấu trúc ${selectedVer.questions_count} câu hỏi từ phiên bản v${selectedVer.version} vào bảng thiết kế hiện tại không?`)) {
                          onRestoreQuestions(selectedVer.questions);
                          onClose();
                        }
                      }}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold rounded-xl border border-indigo-200 transition-colors shadow-2xs"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Nạp Cấu Trúc Bản Này</span>
                    </button>
                  )}
                </div>

                <div className="space-y-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                    Danh sách câu hỏi tại v{selectedVer.version} ({selectedVer.questions.length})
                  </span>

                  {selectedVer.questions.length === 0 ? (
                    <div className="p-6 text-center text-slate-400 text-xs bg-slate-50 rounded-xl">
                      Phiên bản này không có câu hỏi nào.
                    </div>
                  ) : (
                    selectedVer.questions.map((q: any, idx: number) => (
                      <div
                        key={q.id || idx}
                        className="p-3.5 bg-slate-50/70 rounded-xl border border-slate-200/80 space-y-1.5 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-800">
                            Câu {idx + 1}: {q.title}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600 font-mono text-[10px]">
                            {q.question_type}
                          </span>
                        </div>
                        {q.description && (
                          <p className="text-slate-500 text-[11px]">{q.description}</p>
                        )}
                        {q.options && Array.isArray(q.options) && q.options.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {q.options.map((opt: any, oIdx: number) => {
                              const label = typeof opt === 'string' ? opt : (opt.label || opt.text || JSON.stringify(opt));
                              return (
                                <span
                                  key={oIdx}
                                  className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600 text-[10px]"
                                >
                                  {label}
                                </span>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </>
            ) : (
              <div className="p-12 text-center text-slate-400 text-xs">
                Chọn một phiên bản bên trái để xem chi tiết cấu trúc câu hỏi.
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span>Chuẩn Don Dillman &amp; AAPOR: Dữ liệu câu hỏi phiên bản cũ được bảo toàn tính nguyên vẹn 100%</span>
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
