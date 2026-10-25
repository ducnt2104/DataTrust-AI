import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Download,
  FileCode,
  Copy,
  Check,
  Palette,
  Eye,
  BarChart2,
  TrendingDown,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import { SurveyAnalytics, QuestionStats } from '../types/survey';
import {
  generateRiskDistributionSvg,
  generateFunnelChartSvg,
  generateQuestionDistributionSvg,
  rasterizeSvgToPng,
  downloadBlob,
  downloadSvgFile,
  generateLatexPgfplotsSnippet
} from '../utils/academicChartSvg';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  analytics: SurveyAnalytics;
  initialQuestionId?: string | null;
}

export const AcademicChartExportModal: React.FC<Props> = ({
  isOpen,
  onClose,
  analytics,
  initialQuestionId
}) => {
  const [chartType, setChartType] = useState<'risk' | 'funnel' | 'question'>(
    initialQuestionId ? 'question' : 'risk'
  );
  const [selectedQuestionId, setSelectedQuestionId] = useState<string>(
    initialQuestionId || (analytics.questions_analytics[0]?.question_id || '')
  );
  const [theme, setTheme] = useState<'modern' | 'monochrome'>('modern');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [activeTab, setActiveTab] = useState<'preview' | 'latex'>('preview');
  const [isExportingPng, setIsExportingPng] = useState(false);
  const [copiedType, setCopiedType] = useState<'svg' | 'latex' | null>(null);

  useEffect(() => {
    if (initialQuestionId) {
      setChartType('question');
      setSelectedQuestionId(initialQuestionId);
    }
  }, [initialQuestionId]);

  // Hỗ trợ phím Escape để đóng modal
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const selectedQuestion: QuestionStats | undefined = useMemo(() => {
    return analytics.questions_analytics.find(q => q.question_id === selectedQuestionId) || analytics.questions_analytics[0];
  }, [analytics.questions_analytics, selectedQuestionId]);

  // Sinh chuỗi SVG tương ứng với lựa chọn hiện tại
  const currentSvg = useMemo(() => {
    const opts = {
      theme,
      includeMetadata,
      surveyTitle: analytics.survey_title
    };

    if (chartType === 'risk') {
      return generateRiskDistributionSvg(
        analytics.risk_distribution,
        analytics.total_responses,
        opts
      );
    } else if (chartType === 'funnel') {
      return generateFunnelChartSvg(
        analytics.funnel_analytics || [],
        analytics.overall_completion_rate || 100,
        opts
      );
    } else if (chartType === 'question' && selectedQuestion) {
      return generateQuestionDistributionSvg(
        selectedQuestion.question_title,
        selectedQuestion.question_type,
        selectedQuestion.option_distribution || {},
        selectedQuestion.total_answers,
        opts
      );
    }

    return '';
  }, [chartType, selectedQuestion, theme, includeMetadata, analytics]);

  // Sinh mã LaTeX Pgfplots
  const latexSnippet = useMemo(() => {
    if (chartType === 'risk') {
      const low = analytics.risk_distribution.low || 0;
      const med = analytics.risk_distribution.medium || 0;
      const high = analytics.risk_distribution.high || 0;
      const total = analytics.total_responses || 1;
      return generateLatexPgfplotsSnippet('risk', {
        low_pct: Math.round((low / total) * 100),
        med_pct: Math.round((med / total) * 100),
        high_pct: Math.round((high / total) * 100),
        total
      }, analytics.survey_title);
    } else if (chartType === 'question' && selectedQuestion) {
      return generateLatexPgfplotsSnippet(
        'question',
        selectedQuestion.option_distribution || {},
        selectedQuestion.question_title
      );
    }
    return '% Đồ thị Phễu hoàn thành hiện được khuyến nghị xuất dạng Vector SVG.';
  }, [chartType, selectedQuestion, analytics]);

  if (!isOpen) return null;

  const handleDownloadSvg = () => {
    const filename = `datatrust_chart_${chartType}_${Date.now()}.svg`;
    downloadSvgFile(currentSvg, filename);
  };

  const handleDownloadPng = async () => {
    try {
      setIsExportingPng(true);
      const blob = await rasterizeSvgToPng(currentSvg, 840, 500, 3); // 3x scale = 2520x1500 (300 DPI)
      const filename = `datatrust_chart_${chartType}_300dpi_${Date.now()}.png`;
      downloadBlob(blob, filename);
    } catch (err) {
      console.error(err);
      alert('Không thể tạo file PNG. Vui lòng tải file vector SVG thay thế.');
    } finally {
      setIsExportingPng(false);
    }
  };

  const handleCopySvg = () => {
    navigator.clipboard.writeText(currentSvg);
    setCopiedType('svg');
    setTimeout(() => setCopiedType(null), 2000);
  };

  const handleCopyLatex = () => {
    navigator.clipboard.writeText(latexSnippet);
    setCopiedType('latex');
    setTimeout(() => setCopiedType(null), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="academic-chart-title"
    >
      <div className="relative w-full max-w-5xl bg-white rounded-3xl shadow-2xl border border-slate-200/80 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-2xs">
              <BarChart2 className="w-5 h-5" />
            </div>
            <div>
              <h2 id="academic-chart-title" className="text-lg font-bold text-slate-900">
                Xuất Bản Biểu Đồ Nghiên Cứu Khoa Học (Academic Chart Export Hub)
              </h2>
              <p className="text-xs text-slate-500">
                Chuẩn hóa đồ thị xuất bản: Vector SVG (vô hạn DPI, tương thích LaTeX/Typst) & PNG 300 DPI chất lượng cao.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng cửa sổ xuất biểu đồ"
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors focus:ring-2 focus:ring-indigo-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body: Controls & Preview */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Top Controls Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
            {/* Control 1: Loại biểu đồ */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <BarChart2 className="w-3.5 h-3.5 text-indigo-600" />
                Loại biểu đồ khoa học:
              </label>
              <select
                value={chartType}
                onChange={(e) => setChartType(e.target.value as any)}
                className="w-full text-xs font-semibold bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 shadow-2xs"
              >
                <option value="risk">Phân bố Mức độ Rủi ro & Độ tin cậy</option>
                <option value="funnel">Phễu Hoàn thành Don Dillman (Drop-off)</option>
                <option value="question">Phân bố Tần số Theo Câu hỏi</option>
              </select>
            </div>

            {/* Control 2: Chọn câu hỏi (nếu chọn loại question) */}
            {chartType === 'question' ? (
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">Chọn câu hỏi hiển thị:</label>
                <select
                  value={selectedQuestionId}
                  onChange={(e) => setSelectedQuestionId(e.target.value)}
                  className="w-full text-xs font-semibold bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 shadow-2xs truncate"
                >
                  {analytics.questions_analytics.map((q, idx) => (
                    <option key={q.question_id} value={q.question_id}>
                      Câu {idx + 1}: {q.question_title.substring(0, 45)}...
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <Palette className="w-3.5 h-3.5 text-indigo-600" />
                  Bảng màu xuất bản (Theme):
                </label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value as any)}
                  className="w-full text-xs font-semibold bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 shadow-2xs"
                >
                  <option value="modern">Hiện đại (Modern DataTrust — Màu đầy đủ)</option>
                  <option value="monochrome">Đơn sắc in ấn (Grayscale — Kỷ yếu / IEEE)</option>
                </select>
              </div>
            )}

            {/* Control 3: Ghi chú chú dẫn & Chuyển tab */}
            <div className="space-y-1.5 flex flex-col justify-end">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700 select-none pb-2">
                <input
                  type="checkbox"
                  checked={includeMetadata}
                  onChange={(e) => setIncludeMetadata(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span>Đính kèm nguồn Don Dillman & AAPOR</span>
              </label>

              {/* Tab Selector */}
              <div className="flex rounded-xl bg-slate-200/70 p-1 text-xs font-bold">
                <button
                  onClick={() => setActiveTab('preview')}
                  className={`flex-1 py-1 px-3 rounded-lg transition-all ${
                    activeTab === 'preview' ? 'bg-white text-indigo-600 shadow-2xs' : 'text-slate-600'
                  }`}
                >
                  Xem Trước Biểu Đồ
                </button>
                <button
                  onClick={() => setActiveTab('latex')}
                  className={`flex-1 py-1 px-3 rounded-lg transition-all ${
                    activeTab === 'latex' ? 'bg-white text-indigo-600 shadow-2xs' : 'text-slate-600'
                  }`}
                >
                  Mã LaTeX (.tex)
                </button>
              </div>
            </div>
          </div>

          {/* Main Display Pane */}
          {activeTab === 'preview' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="font-semibold flex items-center gap-1.5">
                  <Eye className="w-4 h-4 text-indigo-600" />
                  Khung xem trước biểu đồ Vector (Responsive SVG):
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  Kích thước chuẩn xuất: 840 x 500 px
                </span>
              </div>

              {/* Rendered SVG Preview */}
              <div
                className="w-full bg-slate-100/60 border border-slate-200 rounded-2xl p-4 flex items-center justify-center overflow-x-auto shadow-inner min-h-[380px]"
                dangerouslySetInnerHTML={{ __html: currentSvg }}
              />
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="font-semibold flex items-center gap-1.5">
                  <FileCode className="w-4 h-4 text-indigo-600" />
                  Mã nguồn TikZ / PGFPlots tương thích Overleaf / LaTeX:
                </span>
                <button
                  onClick={handleCopyLatex}
                  className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-all"
                >
                  {copiedType === 'latex' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedType === 'latex' ? 'Đã sao chép!' : 'Sao chép LaTeX'}</span>
                </button>
              </div>

              <pre className="p-4 rounded-2xl bg-slate-900 text-slate-200 font-mono text-xs overflow-x-auto max-h-[380px] leading-relaxed selection:bg-indigo-600">
                {latexSnippet}
              </pre>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopySvg}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-100 rounded-xl transition-all shadow-2xs"
            >
              {copiedType === 'svg' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedType === 'svg' ? 'Đã sao chép mã SVG!' : 'Sao chép mã SVG'}</span>
            </button>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleDownloadSvg}
              className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-bold text-slate-800 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl transition-all shadow-xs"
              title="Tải tệp SVG vô hạn DPI, thích hợp phóng to in ấn khổ lớn hoặc nhúng vào LaTeX"
            >
              <Download className="w-4 h-4 text-indigo-600" />
              <span>Tải Vector SVG (.svg)</span>
            </button>

            <button
              onClick={handleDownloadPng}
              disabled={isExportingPng}
              className="flex items-center gap-1.5 px-5 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-all shadow-sm disabled:opacity-50"
              title="Tải ảnh PNG 300 DPI kích thước 2520x1500 phù hợp chèn vào Word, PowerPoint hoặc Kỷ yếu"
            >
              <Download className={`w-4 h-4 ${isExportingPng ? 'animate-bounce' : ''}`} />
              <span>{isExportingPng ? 'Đang tạo PNG 300 DPI...' : 'Tải PNG 300 DPI (.png)'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
