import React, { useEffect, useState, useRef, useMemo } from 'react';
import {
  X,
  BookOpen,
  FileText,
  Code2,
  Printer,
  Copy,
  Check,
  Download,
  ExternalLink,
  ShieldCheck,
  Layers,
  Sparkles,
  RefreshCw,
  Eye,
  FileCheck2,
  PackageCheck,
  AlertCircle
} from 'lucide-react';
import { api } from '../api/client';

interface AcademicManuscriptModalProps {
  isOpen: boolean;
  onClose: () => void;
  surveyId: string;
  surveyTitle: string;
}

type TabType = 'html' | 'markdown' | 'latex';
type ScopeType = 'verified_clean' | 'all';

export const AcademicManuscriptModal: React.FC<AcademicManuscriptModalProps> = ({
  isOpen,
  onClose,
  surveyId,
  surveyTitle
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('html');
  const [scope, setScope] = useState<ScopeType>('verified_clean');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Content cache per scope & format
  const [contents, setContents] = useState<{
    [key: string]: string; // key: `${scope}_${format}`
  }>({});

  const [copied, setCopied] = useState<boolean>(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Keyboard escape listener
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Load content when tab or scope changes
  useEffect(() => {
    if (!isOpen || !surveyId) return;

    const cacheKey = `${scope}_${activeTab}`;
    if (contents[cacheKey]) {
      setLoading(false);
      setError(null);
      return;
    }

    let mounted = true;
    setLoading(true);
    setError(null);

    api.getManuscript(surveyId, activeTab, scope)
      .then((text: string) => {
        if (mounted) {
          setContents(prev => ({ ...prev, [cacheKey]: text }));
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || 'Không thể tải bản thảo nghiên cứu.');
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [isOpen, surveyId, activeTab, scope, contents]);

  const currentContent = contents[`${scope}_${activeTab}`] || '';

  // Calculate statistics from the text
  const textStats = useMemo(() => {
    if (!currentContent) return { words: 0, chars: 0, lines: 0, readTime: 0 };
    const chars = currentContent.length;
    const words = currentContent.trim().split(/\s+/).filter(Boolean).length;
    const lines = currentContent.split('\n').length;
    const readTime = Math.max(1, Math.ceil(words / 220));
    return { words, chars, lines, readTime };
  }, [currentContent]);

  const handleCopy = () => {
    if (!currentContent) return;
    navigator.clipboard.writeText(currentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handlePrint = () => {
    if (activeTab === 'html' && iframeRef.current && iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.focus();
      iframeRef.current.contentWindow.print();
    } else {
      // Open HTML format in a new window for printing
      const printUrl = `/api/surveys/${surveyId}/export/manuscript?format=html&scope=${scope}`;
      window.open(printUrl, '_blank');
    }
  };

  const handleDownloadFile = () => {
    if (!currentContent) return;
    const extensions: Record<TabType, string> = {
      html: 'html',
      markdown: 'md',
      latex: 'tex'
    };
    const mimeTypes: Record<TabType, string> = {
      html: 'text/html;charset=utf-8',
      markdown: 'text/markdown;charset=utf-8',
      latex: 'application/x-tex;charset=utf-8'
    };

    const ext = extensions[activeTab];
    const mime = mimeTypes[activeTab];
    const blob = new Blob([currentContent], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const safeTitle = surveyTitle.replace(/[^a-zA-Z0-9_\u00C0-\u1EF9]/g, '_').slice(0, 32);
    a.download = `DataTrust_Manuscript_${safeTitle}_${scope}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleRefresh = () => {
    const cacheKey = `${scope}_${activeTab}`;
    setContents(prev => {
      const copy = { ...prev };
      delete copy[cacheKey];
      return copy;
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200">
      <div
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-6 py-4.5 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex items-center justify-between border-b border-indigo-900/50 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/20 border border-indigo-400/30 text-indigo-300">
              <BookOpen className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-extrabold tracking-tight text-white">
                  Academic Manuscript Studio
                </h2>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold tracking-wide uppercase border border-emerald-500/30">
                  <ShieldCheck className="w-3 h-3" /> Don Dillman & AAPOR
                </span>
              </div>
              <p className="text-xs text-indigo-200/80 truncate max-w-xl font-medium mt-0.5">
                Khảo sát: <span className="text-white font-semibold">{surveyTitle}</span> — Tự động biên tập chuẩn công bố khoa học
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            title="Đóng modal (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar & Filters */}
        <div className="px-6 py-3 bg-slate-50 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 shrink-0">
          {/* Format Tabs & Scope Selector */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Scope Selector */}
            <div className="flex items-center p-0.5 bg-slate-200/70 rounded-xl text-xs font-semibold">
              <button
                type="button"
                onClick={() => setScope('verified_clean')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  scope === 'verified_clean'
                    ? 'bg-white text-indigo-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Chỉ sử dụng các phản hồi hợp lệ đã vượt qua 7 tầng kiểm định chất lượng"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>Mẫu Hợp Lệ (Verified Clean)</span>
              </button>
              <button
                type="button"
                onClick={() => setScope('all')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  scope === 'all'
                    ? 'bg-white text-indigo-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Bao gồm toàn bộ phản hồi thô (bao gồm cả phản hồi bị gắn cờ rủi ro)"
              >
                <Layers className="w-3.5 h-3.5 text-slate-500" />
                <span>Tất Cả Mẫu Thô (Raw All)</span>
              </button>
            </div>

            <div className="h-5 w-px bg-slate-300 hidden sm:block" />

            {/* Tab Buttons */}
            <div className="flex items-center gap-1 bg-slate-200/50 p-0.5 rounded-xl text-xs font-semibold">
              <button
                type="button"
                onClick={() => setActiveTab('html')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'html'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Eye className="w-3.5 h-3.5 text-violet-600" />
                <span>Xem Trước Khổ A4 (HTML)</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('markdown')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'markdown'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-emerald-600" />
                <span>Markdown (.md)</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('latex')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'latex'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Code2 className="w-3.5 h-3.5 text-indigo-600" />
                <span>LaTeX / Overleaf (.tex)</span>
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              className="p-2 rounded-xl border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors shadow-2xs"
              title="Làm mới lại dữ liệu bản thảo"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>

            {activeTab === 'html' ? (
              <button
                onClick={handlePrint}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-white hover:bg-slate-900 transition-all shadow-xs"
                title="Mở hộp thoại in ấn hoặc lưu sang PDF chuẩn A4"
              >
                <Printer className="w-3.5 h-3.5 text-slate-300" />
                <span>In / Lưu PDF</span>
              </button>
            ) : null}

            <button
              onClick={handleCopy}
              disabled={loading || !currentContent}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-all shadow-xs disabled:opacity-50"
              title="Sao chép toàn bộ nội dung của tab hiện tại vào bộ nhớ tạm"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700 font-bold">Đã sao chép!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-500" />
                  <span>Sao chép {activeTab.toUpperCase()}</span>
                </>
              )}
            </button>

            <button
              onClick={handleDownloadFile}
              disabled={loading || !currentContent}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 transition-all shadow-xs disabled:opacity-50"
              title="Tải tệp tin về máy tính"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Tải .{activeTab === 'latex' ? 'tex' : activeTab === 'markdown' ? 'md' : 'html'}</span>
            </button>

            <button
              onClick={() => window.open(`/api/surveys/${surveyId}/export/academic-dossier?scope=${scope}`, '_blank')}
              className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-all shadow-xs"
              title="Tải trọn bộ 8 tệp hồ sơ khoa học (.ZIP) bao gồm SPSS, R, Python, Codebook và Dữ liệu"
            >
              <PackageCheck className="w-3.5 h-3.5" />
              <span>Dossier (.ZIP)</span>
            </button>
          </div>
        </div>

        {/* Quick Stats Bar */}
        <div className="px-6 py-2 bg-slate-100/70 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-600 shrink-0 font-medium">
          <div className="flex items-center gap-4">
            <span>
              Phạm vi: <strong className="text-slate-800">{scope === 'verified_clean' ? 'Dữ liệu Hợp Lệ (Verified Clean)' : 'Toàn Bộ Dữ Liệu Thô (Raw All)'}</strong>
            </span>
            <span className="text-slate-300">•</span>
            <span>
              Độ dài bài báo: <strong className="text-slate-800">{textStats.words.toLocaleString()} từ</strong> (~{textStats.chars.toLocaleString()} ký tự)
            </span>
            <span className="text-slate-300">•</span>
            <span>
              Thời gian đọc ước tính: <strong className="text-slate-800">~{textStats.readTime} phút</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-indigo-700">
            <Sparkles className="w-3 h-3 text-indigo-500" />
            <span className="text-[10px] font-semibold uppercase tracking-wider">
              Bao gồm: Abstract • Don Dillman • 7-Layer Quality • Cronbach's Alpha • EFA • Correlation • Regression OLS • Mahalanobis • SHA-256 Ledger
            </span>
          </div>
        </div>

        {/* Main Content Viewer */}
        <div className="flex-1 overflow-hidden relative bg-slate-100 flex flex-col">
          {loading && (
            <div className="absolute inset-0 bg-white/80 backdrop-blur-2xs z-20 flex flex-col items-center justify-center p-6 text-center">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mb-3" />
              <h3 className="font-bold text-slate-800 text-sm">
                Đang biên soạn bản thảo nghiên cứu khoa học...
              </h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md">
                Hệ thống đang tích hợp số liệu thống kê mô tả, kiểm định độ tin cậy Cronbach, phân tích nhân tố EFA, ma trận tương quan, hồi quy OLS và đối chiếu chuỗi băm SHA-256.
              </p>
            </div>
          )}

          {error && (
            <div className="p-8 text-center m-auto max-w-md">
              <div className="p-3 rounded-full bg-red-100 text-red-600 w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base mb-1">Không thể tải bản thảo</h3>
              <p className="text-xs text-slate-600 mb-4">{error}</p>
              <button
                onClick={handleRefresh}
                className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition-all shadow-xs"
              >
                Thử lại
              </button>
            </div>
          )}

          {!loading && !error && (
            <>
              {/* HTML Tab (Rendered in isolated iframe for true A4 pagination preview) */}
              {activeTab === 'html' && (
                <div className="flex-1 w-full h-full p-4 sm:p-6 overflow-auto flex justify-center bg-slate-200/80">
                  <div className="w-full max-w-4xl bg-white rounded-xl shadow-xl border border-slate-300 overflow-hidden flex flex-col min-h-[600px] max-h-[calc(92vh-190px)]">
                    <iframe
                      ref={iframeRef}
                      title="Academic Manuscript Preview"
                      srcDoc={currentContent}
                      className="w-full flex-1 border-0 bg-white"
                      sandbox="allow-same-origin allow-scripts allow-modals"
                    />
                  </div>
                </div>
              )}

              {/* Markdown Tab */}
              {activeTab === 'markdown' && (
                <div className="flex-1 overflow-auto p-4 sm:p-6 bg-slate-900 text-slate-100">
                  <div className="max-w-5xl mx-auto space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-emerald-400" />
                        <span className="font-mono text-slate-300">datatrust_manuscript.md</span>
                        <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                          {textStats.lines.toLocaleString()} dòng
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500">
                        Chuẩn Markdown quốc tế (GitHub Flavored & KaTeX Math notation)
                      </span>
                    </div>

                    <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-200 leading-relaxed overflow-x-auto whitespace-pre-wrap selection:bg-indigo-700 selection:text-white">
                      {currentContent}
                    </pre>
                  </div>
                </div>
              )}

              {/* LaTeX Tab */}
              {activeTab === 'latex' && (
                <div className="flex-1 overflow-auto p-4 sm:p-6 bg-slate-950 text-slate-100">
                  <div className="max-w-5xl mx-auto space-y-4">
                    {/* LaTeX Help Guide Banner */}
                    <div className="p-4 rounded-xl bg-indigo-950/70 border border-indigo-800/80 text-xs text-indigo-200 flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 font-bold text-white">
                          <Code2 className="w-4 h-4 text-indigo-400" />
                          <span>Mã nguồn LaTeX Compilable (Overleaf / TeXLive Ready)</span>
                        </div>
                        <p className="text-slate-300 leading-relaxed">
                          Tệp mã nguồn LaTeX đã cấu hình sẵn sàng biên dịch với các gói chuẩn: <code className="bg-indigo-900/60 px-1 py-0.5 rounded text-indigo-200 font-mono">article, amsmath, booktabs, hyperref, xcolor</code>. Bạn có thể sao chép trực tiếp vào một dự án Overleaf mới để xuất PDF chất lượng nhà xuất bản.
                        </p>
                      </div>

                      <a
                        href="https://www.overleaf.com"
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shrink-0 transition-all shadow-xs"
                      >
                        <span>Mở Overleaf</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
                      <div className="flex items-center gap-2">
                        <Code2 className="w-4 h-4 text-indigo-400" />
                        <span className="font-mono text-slate-300">datatrust_manuscript.tex</span>
                        <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                          {textStats.lines.toLocaleString()} dòng
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500">
                        Enc: UTF-8 • Compiler: pdflatex / xelatex
                      </span>
                    </div>

                    <pre className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-indigo-100 leading-relaxed overflow-x-auto whitespace-pre-wrap selection:bg-indigo-700 selection:text-white">
                      {currentContent}
                    </pre>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-white border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <FileCheck2 className="w-4 h-4 text-indigo-600" />
            <span>
              Bản quyền học thuật: DataTrust Research Framework — Tuân thủ chuẩn minh bạch AAPOR Disclosure và Nghị định 356/2025/NĐ-CP.
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-all shadow-2xs"
            >
              Đóng Studio
            </button>
            <button
              onClick={handleDownloadFile}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Tải Bản Thảo Hiện Tại</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
