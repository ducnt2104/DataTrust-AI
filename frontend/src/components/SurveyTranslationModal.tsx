import React, { useState, useEffect } from 'react';
import {
  X,
  Languages,
  Sparkles,
  Save,
  Check,
  AlertCircle,
  RefreshCw,
  Globe2,
  CheckCircle2,
  FileText,
  ListFilter
} from 'lucide-react';
import { api } from '../api/client';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  surveyId: string;
  onSuccess?: () => void;
}

const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'Tiếng Anh (English)', flag: '🇬🇧' },
  { code: 'ja', label: 'Tiếng Nhật (日本語)', flag: '🇯🇵' },
  { code: 'zh', label: 'Tiếng Trung (中文)', flag: '🇨🇳' }
];

export const SurveyTranslationModal: React.FC<Props> = ({
  isOpen,
  onClose,
  surveyId,
  onSuccess
}) => {
  const [selectedLang, setSelectedLang] = useState<string>('en');
  const [loading, setLoading] = useState<boolean>(true);
  const [translating, setTranslating] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>(['vi']);
  const [allTranslations, setAllTranslations] = useState<Record<string, any>>({});
  const [currentTranslation, setCurrentTranslation] = useState<any>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadTranslations();
    }
  }, [isOpen, surveyId]);

  useEffect(() => {
    if (allTranslations && allTranslations[selectedLang]) {
      setCurrentTranslation(JSON.parse(JSON.stringify(allTranslations[selectedLang])));
    } else {
      setCurrentTranslation(null);
    }
  }, [selectedLang, allTranslations]);

  const loadTranslations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getSurveyTranslations(surveyId);
      setAvailableLanguages(res.available_languages || ['vi']);
      setAllTranslations(res.translations || {});
      if (res.translations && res.translations[selectedLang]) {
        setCurrentTranslation(JSON.parse(JSON.stringify(res.translations[selectedLang])));
      } else {
        setCurrentTranslation(null);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể tải dữ liệu bản dịch.');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoTranslate = async () => {
    try {
      setTranslating(true);
      setError(null);
      const res = await api.autoTranslateSurvey(surveyId, selectedLang);
      setCurrentTranslation(res.translation);
      setAllTranslations((prev) => ({
        ...prev,
        [selectedLang]: res.translation
      }));
      if (!availableLanguages.includes(selectedLang)) {
        setAvailableLanguages((prev) => [...prev, selectedLang]);
      }
      setToastMessage(`Đã tự động dịch sang ${SUPPORTED_LANGUAGES.find((l) => l.code === selectedLang)?.label} thành công!`);
      setTimeout(() => setToastMessage(null), 3000);
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.message || 'Lỗi khi tự động dịch.');
    } finally {
      setTranslating(false);
    }
  };

  const handleSaveTranslation = async () => {
    if (!currentTranslation) return;
    try {
      setSaving(true);
      setError(null);
      await api.updateSurveyTranslation(surveyId, selectedLang, currentTranslation);
      setAllTranslations((prev) => ({
        ...prev,
        [selectedLang]: currentTranslation
      }));
      if (!availableLanguages.includes(selectedLang)) {
        setAvailableLanguages((prev) => [...prev, selectedLang]);
      }
      setToastMessage('Đã lưu bản dịch thành công!');
      setTimeout(() => setToastMessage(null), 3000);
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.message || 'Lỗi khi lưu bản dịch.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-200 flex items-center justify-between shrink-0 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
              <Languages className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">
                  Bản Địa Hóa & Đa Ngôn Ngữ (Multilingual Localization Studio)
                </h3>
                <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-100 text-indigo-800 rounded-full">
                  i18n Offline Lexicon
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Quản lý các bản dịch câu hỏi, hướng dẫn và nhãn thang đo. Người tham gia có thể chọn ngôn ngữ trực tiếp trên link khảo sát công khai.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Language Selection & Action Bar */}
        <div className="px-6 py-3.5 bg-white border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600 flex items-center gap-1">
              <Globe2 className="w-4 h-4 text-indigo-600" /> Ngôn ngữ đích:
            </span>
            <div className="inline-flex rounded-xl bg-slate-100 p-0.5 text-xs font-semibold">
              {SUPPORTED_LANGUAGES.map((lang) => {
                const isActivated = availableLanguages.includes(lang.code);
                const isSelected = selectedLang === lang.code;
                return (
                  <button
                    key={lang.code}
                    onClick={() => setSelectedLang(lang.code)}
                    className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-white text-indigo-700 shadow-xs border border-indigo-100 font-bold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <span>{lang.flag}</span>
                    <span>{lang.label}</span>
                    {isActivated && (
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" title="Đã có bản dịch" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleAutoTranslate}
              disabled={translating}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-violet-50 text-violet-700 hover:bg-violet-100 border border-violet-200 rounded-xl transition-all shadow-xs disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${translating ? 'animate-spin' : 'text-violet-600'}`} />
              <span>{translating ? 'Đang dịch thuật ngữ...' : 'Tự động dịch học thuật'}</span>
            </button>

            {currentTranslation && (
              <button
                onClick={handleSaveTranslation}
                disabled={saving}
                className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl transition-all shadow-sm disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'Đang lưu...' : 'Lưu bản dịch'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Toast / Error alerts */}
        {toastMessage && (
          <div className="mx-6 mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2 animate-in fade-in">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{toastMessage}</span>
          </div>
        )}

        {error && (
          <div className="mx-6 mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Modal Body: Editor Container */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {loading ? (
            <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
              <RefreshCw className="w-5 h-5 animate-spin text-indigo-600" />
              <span>Đang tải các gói ngôn ngữ...</span>
            </div>
          ) : !currentTranslation ? (
            <div className="py-16 text-center text-slate-500 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 mx-auto flex items-center justify-center text-slate-400">
                <Globe2 className="w-6 h-6" />
              </div>
              <div className="max-w-sm mx-auto space-y-1">
                <h4 className="text-sm font-bold text-slate-800">
                  Chưa có bản dịch {SUPPORTED_LANGUAGES.find((l) => l.code === selectedLang)?.label}
                </h4>
                <p className="text-xs text-slate-500">
                  Bấm nút "Tự động dịch học thuật" bên trên để hệ thống tự động biên dịch toàn bộ tiêu đề, chỉ dẫn và thang đo Likert sang ngôn ngữ này.
                </p>
              </div>
              <button
                onClick={handleAutoTranslate}
                disabled={translating}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-indigo-600 text-white rounded-xl shadow-md hover:bg-indigo-700 transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Bắt đầu tự động dịch</span>
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Meta information section */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-4">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <span>Tiêu đề & Hướng dẫn khảo sát ({selectedLang.toUpperCase()})</span>
                </h4>

                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 block mb-1">
                      Tiêu đề khảo sát (Survey Title):
                    </label>
                    <input
                      type="text"
                      value={currentTranslation.title || ''}
                      onChange={(e) =>
                        setCurrentTranslation({ ...currentTranslation, title: e.target.value })
                      }
                      className="w-full text-xs font-medium bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700 block mb-1">
                      Mô tả nghiên cứu (Description):
                    </label>
                    <textarea
                      rows={2}
                      value={currentTranslation.description || ''}
                      onChange={(e) =>
                        setCurrentTranslation({ ...currentTranslation, description: e.target.value })
                      }
                      className="w-full text-xs bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700 block mb-1">
                      Hướng dẫn điền phiếu (Instructions):
                    </label>
                    <input
                      type="text"
                      value={currentTranslation.instructions || ''}
                      onChange={(e) =>
                        setCurrentTranslation({ ...currentTranslation, instructions: e.target.value })
                      }
                      className="w-full text-xs bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              </div>

              {/* Questions translation list */}
              {currentTranslation.questions && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <ListFilter className="w-4 h-4 text-indigo-600" />
                    <span>Nội dung chi tiết từng câu hỏi & phương án ({Object.keys(currentTranslation.questions).length} câu)</span>
                  </h4>

                  {Object.entries(currentTranslation.questions).map(([qid, qData]: [string, any], idx) => (
                    <div
                      key={qid}
                      className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-2xs space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider">
                          Câu hỏi {idx + 1}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">ID: {qid}</span>
                      </div>

                      <div>
                        <label className="text-xs font-medium text-slate-700 block mb-1">
                          Tiêu đề câu hỏi (Question Text):
                        </label>
                        <input
                          type="text"
                          value={qData.title || ''}
                          onChange={(e) => {
                            const updated = { ...currentTranslation };
                            updated.questions[qid].title = e.target.value;
                            setCurrentTranslation(updated);
                          }}
                          className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>

                      {/* Options translation if present */}
                      {qData.options && Array.isArray(qData.options) && qData.options.length > 0 && (
                        <div className="space-y-1.5 pt-1">
                          <span className="text-[11px] font-semibold text-slate-600 block">
                            Các phương án lựa chọn (Options):
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {qData.options.map((opt: any, optIdx: number) => {
                              const optLabel = typeof opt === 'string' ? opt : opt.label || '';
                              return (
                                <div key={optIdx} className="flex items-center gap-1.5">
                                  <span className="text-[10px] font-mono text-slate-400 w-5">#{optIdx + 1}</span>
                                  <input
                                    type="text"
                                    value={optLabel}
                                    onChange={(e) => {
                                      const updated = { ...currentTranslation };
                                      if (typeof updated.questions[qid].options[optIdx] === 'string') {
                                        updated.questions[qid].options[optIdx] = e.target.value;
                                      } else {
                                        updated.questions[qid].options[optIdx].label = e.target.value;
                                      }
                                      setCurrentTranslation(updated);
                                    }}
                                    className="flex-1 text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                  />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between shrink-0">
          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>
              Các ngôn ngữ khả dụng trên link khảo sát: <strong>{availableLanguages.join(', ').toUpperCase()}</strong>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Đóng
            </button>
            {currentTranslation && (
              <button
                onClick={handleSaveTranslation}
                disabled={saving}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl transition-all shadow-sm disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'Đang lưu...' : 'Lưu bản dịch'}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
