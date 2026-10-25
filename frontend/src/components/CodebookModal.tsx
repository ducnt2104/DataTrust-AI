import React, { useEffect, useState, useMemo } from 'react';
import {
  X,
  BookOpen,
  Code2,
  Copy,
  Check,
  Download,
  Search,
  Layers,
  Database,
  FileCode,
  Tag,
  Loader2
} from 'lucide-react';
import { api } from '../api/client';
import { CodebookData, CodebookVariable } from '../types/survey';

interface CodebookModalProps {
  isOpen: boolean;
  onClose: () => void;
  surveyId: string;
  surveyTitle: string;
}

type TabType = 'dictionary' | 'spss' | 'stata' | 'sas' | 'r';

export const CodebookModal: React.FC<CodebookModalProps> = ({
  isOpen,
  onClose,
  surveyId,
  surveyTitle
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('dictionary');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [codebook, setCodebook] = useState<CodebookData | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [scaleFilter, setScaleFilter] = useState<string>('all');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

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

  useEffect(() => {
    if (!isOpen || !surveyId) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    api.getSurveyCodebook(surveyId, 'json')
      .then((data: CodebookData) => {
        if (mounted) {
          setCodebook(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Không thể tải Từ điển dữ liệu & Cú pháp.');
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [isOpen, surveyId]);

  const filteredVariables = useMemo(() => {
    if (!codebook?.variables) return [];
    return codebook.variables.filter((v: CodebookVariable) => {
      const matchSearch =
        v.variable_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        v.variable_label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        v.question_type.toLowerCase().includes(searchTerm.toLowerCase());

      const matchScale =
        scaleFilter === 'all' ||
        v.measurement_level.toLowerCase().includes(scaleFilter.toLowerCase());

      return matchSearch && matchScale;
    });
  }, [codebook, searchTerm, scaleFilter]);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  const downloadSyntax = (content: string, filename: string, mimeType: string = 'text/plain') => {
    const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="codebook-modal-title"
    >
      <div className="relative w-full max-w-5xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-linear-to-r from-slate-900 via-indigo-950 to-slate-900 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 border border-indigo-400/30 rounded-xl">
              <BookOpen className="w-5 h-5 text-indigo-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="codebook-modal-title" className="text-base font-bold text-white">
                  Từ Điển Dữ Liệu & Bộ Cú Pháp Học Thuật
                </h2>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/30 border border-indigo-400/30 text-indigo-200 font-mono font-semibold">
                  SPSS / Stata / SAS / R
                </span>
              </div>
              <p className="text-xs text-slate-300 truncate max-w-md">
                Khảo sát: {surveyTitle}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors focus:outline-hidden focus:ring-2 focus:ring-white/20"
            aria-label="Đóng cửa sổ"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 px-6 pt-3 border-b border-slate-200 bg-slate-50 text-xs font-semibold overflow-x-auto">
          <button
            onClick={() => setActiveTab('dictionary')}
            className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all shrink-0 ${
              activeTab === 'dictionary'
                ? 'border-indigo-600 text-indigo-700 font-bold bg-white rounded-t-lg'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-t-lg'
            }`}
          >
            <Database className="w-4 h-4" />
            Từ Điển Biến ({codebook?.variables_count || 0})
          </button>
          <button
            onClick={() => setActiveTab('spss')}
            className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all shrink-0 ${
              activeTab === 'spss'
                ? 'border-indigo-600 text-indigo-700 font-bold bg-white rounded-t-lg'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-t-lg'
            }`}
          >
            <FileCode className="w-4 h-4 text-emerald-600" />
            Cú Pháp SPSS (.sps)
          </button>
          <button
            onClick={() => setActiveTab('stata')}
            className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all shrink-0 ${
              activeTab === 'stata'
                ? 'border-indigo-600 text-indigo-700 font-bold bg-white rounded-t-lg'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-t-lg'
            }`}
          >
            <FileCode className="w-4 h-4 text-amber-600" />
            Cú Pháp Stata (.do)
          </button>
          <button
            onClick={() => setActiveTab('sas')}
            className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all shrink-0 ${
              activeTab === 'sas'
                ? 'border-indigo-600 text-indigo-700 font-bold bg-white rounded-t-lg'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-t-lg'
            }`}
          >
            <FileCode className="w-4 h-4 text-rose-600" />
            Cú Pháp SAS (.sas)
          </button>
          <button
            onClick={() => setActiveTab('r')}
            className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all shrink-0 ${
              activeTab === 'r'
                ? 'border-indigo-600 text-indigo-700 font-bold bg-white rounded-t-lg'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-t-lg'
            }`}
          >
            <Code2 className="w-4 h-4 text-blue-600" />
            Cú Pháp R Script (.R)
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mb-3" />
              <p className="text-sm font-medium">Đang khởi tạo từ điển dữ liệu & cú pháp phân tích...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
              <p className="font-semibold">Lỗi tải dữ liệu</p>
              <p className="text-xs mt-1">{error}</p>
            </div>
          ) : !codebook ? null : (
            <>
              {/* Tab 1: Data Dictionary */}
              {activeTab === 'dictionary' && (
                <div className="space-y-4">
                  {/* Filter Toolbar */}
                  <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-3 rounded-xl border border-slate-200">
                    <div className="relative w-full sm:w-72">
                      <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        placeholder="Tìm tên biến, nhãn hoặc loại câu hỏi..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-600 focus:bg-white transition-all"
                      />
                    </div>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <label className="text-xs font-semibold text-slate-600 whitespace-nowrap">
                        Thang đo:
                      </label>
                      <select
                        value={scaleFilter}
                        onChange={(e) => setScaleFilter(e.target.value)}
                        className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-hidden focus:border-indigo-600"
                      >
                        <option value="all">Tất cả thang đo</option>
                        <option value="nominal">Nominal (Định danh)</option>
                        <option value="ordinal">Ordinal (Thứ bậc / Likert)</option>
                        <option value="scale">Scale (Định lượng / Tỷ lệ)</option>
                        <option value="multiple">Multiple Response Set</option>
                      </select>
                    </div>
                  </div>

                  {/* Variables Table */}
                  <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-slate-100/80 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[11px]">
                            <th className="py-2.5 px-3 w-24">Tên Biến</th>
                            <th className="py-2.5 px-3 min-w-[200px]">Nhãn Câu Hỏi (Variable Label)</th>
                            <th className="py-2.5 px-3 w-28">Thang Đo</th>
                            <th className="py-2.5 px-3 w-24">Bắt Buộc</th>
                            <th className="py-2.5 px-3">Mã Hóa Giá Trị (Value Labels)</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {filteredVariables.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="py-8 text-center text-slate-400">
                                Không tìm thấy biến nào phù hợp với bộ lọc tìm kiếm.
                              </td>
                            </tr>
                          ) : (
                            filteredVariables.map((v) => (
                              <tr key={v.variable_name} className="hover:bg-slate-50/80 transition-colors">
                                <td className="py-2.5 px-3 font-mono font-bold text-indigo-700">
                                  {v.variable_name}
                                </td>
                                <td className="py-2.5 px-3 font-medium text-slate-900">
                                  {v.variable_label}
                                  <span className="block text-[10px] text-slate-400 font-mono mt-0.5">
                                    Type: {v.question_type}
                                  </span>
                                </td>
                                <td className="py-2.5 px-3">
                                  <span
                                    className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                      v.measurement_level.includes('Ordinal')
                                        ? 'bg-amber-100 text-amber-800'
                                        : v.measurement_level.includes('Scale')
                                        ? 'bg-emerald-100 text-emerald-800'
                                        : v.measurement_level.includes('Multiple')
                                        ? 'bg-purple-100 text-purple-800'
                                        : 'bg-blue-100 text-blue-800'
                                    }`}
                                  >
                                    {v.measurement_level}
                                  </span>
                                </td>
                                <td className="py-2.5 px-3">
                                  {v.is_required ? (
                                    <span className="text-emerald-700 font-semibold text-[11px]">Có</span>
                                  ) : (
                                    <span className="text-slate-400 text-[11px]">Không</span>
                                  )}
                                </td>
                                <td className="py-2.5 px-3">
                                  {Object.keys(v.value_labels).length > 0 ? (
                                    <div className="flex flex-wrap gap-1">
                                      {Object.entries(v.value_labels).map(([code, label]) => (
                                        <span
                                          key={code}
                                          className="inline-flex items-center gap-1 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded text-[10px] text-slate-700"
                                          title={`${code} = ${label}`}
                                        >
                                          <span className="font-mono font-bold text-slate-900">{code}:</span>
                                          <span className="truncate max-w-[140px]">{label}</span>
                                        </span>
                                      ))}
                                    </div>
                                  ) : (
                                    <span className="text-slate-400 italic text-[11px]">
                                      (Văn bản / Số liên tục)
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: SPSS Syntax */}
              {activeTab === 'spss' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-slate-200">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">
                        Cú Pháp Định Danh & Gán Nhãn Biến Cho IBM SPSS Statistics
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        Chạy cú pháp này trong SPSS Syntax Editor để tự động định dạng biến, thang đo và Missing Values (999).
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyToClipboard(codebook.spss_syntax, 'spss')}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                      >
                        {copiedKey === 'spss' ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-700 font-bold">Đã chép!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            Sao chép
                          </>
                        )}
                      </button>
                      <button
                        onClick={() =>
                          downloadSyntax(
                            codebook.spss_syntax,
                            `codebook_${surveyId.slice(0, 8)}.sps`
                          )
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Tải file .sps
                      </button>
                    </div>
                  </div>

                  <div className="relative bg-slate-950 text-slate-100 p-4 rounded-xl font-mono text-xs overflow-x-auto max-h-[500px] border border-slate-800 leading-relaxed shadow-inner">
                    <pre>{codebook.spss_syntax}</pre>
                  </div>
                </div>
              )}

              {/* Tab 3: Stata Do-File */}
              {activeTab === 'stata' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-slate-200">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">
                        Kịch Bản Stata Do-File (Variable Labels & Value Labels)
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        Sử dụng cho Stata 16/17/18 để chuẩn hóa cấu trúc dữ liệu khảo sát và định dạng biến phân loại.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyToClipboard(codebook.stata_syntax, 'stata')}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                      >
                        {copiedKey === 'stata' ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-700 font-bold">Đã chép!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            Sao chép
                          </>
                        )}
                      </button>
                      <button
                        onClick={() =>
                          downloadSyntax(
                            codebook.stata_syntax,
                            `codebook_${surveyId.slice(0, 8)}.do`
                          )
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Tải file .do
                      </button>
                    </div>
                  </div>

                  <div className="relative bg-slate-950 text-slate-100 p-4 rounded-xl font-mono text-xs overflow-x-auto max-h-[500px] border border-slate-800 leading-relaxed shadow-inner">
                    <pre>{codebook.stata_syntax}</pre>
                  </div>
                </div>
              )}

              {/* Tab: SAS Script */}
              {activeTab === 'sas' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-slate-200">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">
                        Kịch Bản SAS Syntax (Proc Format, Variable Labels &amp; Proc Means/Freq)
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        Sử dụng cho SAS 9.4 / SAS Viya / SAS Studio phục vụ nghiên cứu y sinh, thống kê dịch tễ và chính sách.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyToClipboard(codebook.sas_syntax || '', 'sas')}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                      >
                        {copiedKey === 'sas' ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-700 font-bold">Đã chép!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            Sao chép
                          </>
                        )}
                      </button>
                      <button
                        onClick={() =>
                          downloadSyntax(
                            codebook.sas_syntax || '',
                            `codebook_${surveyId.slice(0, 8)}.sas`
                          )
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Tải file .sas
                      </button>
                    </div>
                  </div>

                  <div className="relative bg-slate-950 text-slate-100 p-4 rounded-xl font-mono text-xs overflow-x-auto max-h-[500px] border border-slate-800 leading-relaxed shadow-inner">
                    <pre>{codebook.sas_syntax || '/* Đang chuẩn bị cú pháp SAS */'}</pre>
                  </div>
                </div>
              )}

              {/* Tab 4: R Script */}
              {activeTab === 'r' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-slate-200">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">
                        Mã Nguồn R Script (tidyverse / factor mutations)
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        Định nghĩa nhãn biến và chuyển đổi các cột định tính sang kiểu factor với đầy đủ levels và labels.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyToClipboard(codebook.r_script, 'r')}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                      >
                        {copiedKey === 'r' ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-700 font-bold">Đã chép!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            Sao chép
                          </>
                        )}
                      </button>
                      <button
                        onClick={() =>
                          downloadSyntax(
                            codebook.r_script,
                            `codebook_${surveyId.slice(0, 8)}.R`
                          )
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Tải file .R
                      </button>
                    </div>
                  </div>

                  <div className="relative bg-slate-950 text-slate-100 p-4 rounded-xl font-mono text-xs overflow-x-auto max-h-[500px] border border-slate-800 leading-relaxed shadow-inner">
                    <pre>{codebook.r_script}</pre>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 bg-white text-xs">
          <div className="flex items-center gap-2 text-slate-500">
            <Tag className="w-3.5 h-3.5 text-indigo-600" />
            <span>Tiêu chuẩn mã hóa biến nghiên cứu DataTrust</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors"
          >
            Đóng
          </button>
        </div>

      </div>
    </div>
  );
};
