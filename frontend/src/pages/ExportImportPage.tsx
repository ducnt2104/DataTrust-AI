import React, { useState } from 'react';
import { 
  ArrowLeft, Download, Upload, FileText, CheckCircle2, ShieldCheck, 
  Database, Globe, Layers, AlertCircle, Info, FileSpreadsheet, Code2, FileCode,
  Archive, PackageCheck, Check, Printer, BookOpen, Sparkles
} from 'lucide-react';
import { CodebookModal } from '../components/CodebookModal';
import { AcademicManuscriptModal } from '../components/AcademicManuscriptModal';

interface Props {
  surveyId: string;
  onNavigate: (path: string) => void;
}

export const ExportImportPage: React.FC<Props> = ({ surveyId, onNavigate }) => {
  const [scope, setScope] = useState<'verified_clean' | 'reviewed' | 'raw'>('verified_clean');
  const [sourceFilter, setSourceFilter] = useState<'all' | 'online_form' | 'paper_scan' | 'csv_import'>('all');
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<string | null>(null);
  const [showCodebookModal, setShowCodebookModal] = useState(false);
  const [showManuscriptModal, setShowManuscriptModal] = useState(false);

  const handleDownload = () => {
    let url = `/api/surveys/${surveyId}/export?scope=${scope}&format=${format}`;
    if (sourceFilter !== 'all') {
      url += `&source=${sourceFilter}`;
    }
    window.open(url, '_blank');
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setImporting(true);
      setImportResult(null);
      const res = await fetch(`/api/surveys/${surveyId}/import/csv`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Lỗi nhập file');
      setImportResult(data.message);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi nhập CSV');
    } finally {
      setImporting(false);
      e.target.value = '';
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => onNavigate(`/surveys/${surveyId}/analytics`)}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="Quay lại phân tích khảo sát"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Xuất & Nhập dữ liệu khảo sát
          </h1>
          <p className="text-sm text-slate-500">
            Tải về bộ dữ liệu đã kiểm định hoặc nhập tệp phản hồi ngoại tuyến với truy xuất nguồn gốc
          </p>
        </div>
      </div>

      {/* Export Section */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Download className="w-5 h-5 text-indigo-600" />
          <h2 className="font-bold text-slate-900 text-base">Xuất tập dữ liệu (Data Export)</h2>
        </div>

        {/* Scope selector */}
        <div className="space-y-3">
          <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
            1. Chọn phạm vi dữ liệu xuất (Data Scope)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              {
                id: 'verified_clean',
                title: 'Verified Clean Dataset',
                subtitle: 'Khuyến nghị cho nghiên cứu',
                desc: 'Chỉ bao gồm các phản hồi đã được con người duyệt hợp lệ hoặc có điểm rủi ro thấp an toàn.'
              },
              {
                id: 'reviewed',
                title: 'Reviewed Responses',
                subtitle: 'Đã qua rà soát',
                desc: 'Bao gồm tất cả các phản hồi đã có quyết định thẩm định chính thức của người quản trị.'
              },
              {
                id: 'raw',
                title: 'Raw All Responses',
                subtitle: 'Toàn bộ phản hồi thô',
                desc: 'Xuất toàn bộ phản hồi gốc chưa qua chọn lọc, bao gồm cả các phản hồi bị gắn cờ rủi ro.'
              }
            ].map((opt) => (
              <label
                key={opt.id}
                className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                  scope === opt.id
                    ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-100'
                    : 'border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900">{opt.title}</span>
                    <input
                      type="radio"
                      name="export_scope"
                      value={opt.id}
                      checked={scope === opt.id}
                      onChange={() => setScope(opt.id as any)}
                      className="w-4 h-4 text-indigo-600"
                    />
                  </div>
                  <span className="text-[11px] font-semibold text-indigo-600 block mt-0.5">
                    {opt.subtitle}
                  </span>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed">{opt.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Source Channel Selector */}
        <div className="space-y-3">
          <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
            2. Nguồn dữ liệu (Source Channel)
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {[
              { id: 'all', label: 'Tất cả nguồn', icon: Layers },
              { id: 'online_form', label: 'Trực tuyến', icon: Globe },
              { id: 'paper_scan', label: 'Phiếu giấy OMR', icon: FileText },
              { id: 'csv_import', label: 'Tệp CSV', icon: Database },
            ].map((src) => {
              const Icon = src.icon;
              return (
                <label
                  key={src.id}
                  className={`flex items-center gap-2 p-3 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                    sourceFilter === src.id
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-900 ring-2 ring-indigo-100'
                      : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="export_source"
                    value={src.id}
                    checked={sourceFilter === src.id}
                    onChange={() => setSourceFilter(src.id as any)}
                    className="w-3.5 h-3.5 text-indigo-600"
                  />
                  <Icon className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>{src.label}</span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Format Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
            3. Định dạng tệp xuất
          </label>
          <div className="flex items-center gap-3">
            {[
              { id: 'csv', label: 'CSV (Tương thích Microsoft Excel tiếng Việt UTF-8 BOM)' },
              { id: 'json', label: 'JSON (Đầy đủ thuộc tính & siêu dữ liệu cho API)' }
            ].map((fmt) => (
              <label
                key={fmt.id}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                  format === fmt.id
                    ? 'border-indigo-600 bg-indigo-50 text-indigo-900'
                    : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <input
                  type="radio"
                  name="export_format"
                  value={fmt.id}
                  checked={format === fmt.id}
                  onChange={() => setFormat(fmt.id as any)}
                  className="w-3.5 h-3.5 text-indigo-600"
                />
                <span>{fmt.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Download Action */}
        <button
          onClick={handleDownload}
          className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm transition-all"
        >
          <Download className="w-4 h-4" />
          <span>Tải xuống tệp dữ liệu ({scope.toUpperCase()})</span>
        </button>
      </div>

      {/* Import Section */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Upload className="w-5 h-5 text-indigo-600" />
          <h2 className="font-bold text-slate-900 text-base">Nhập dữ liệu từ tệp CSV bên ngoài (Import)</h2>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          Bạn có thể nhập danh sách câu trả lời thu thập từ Google Forms, Excel hoặc khảo sát ngoại tuyến. Hệ thống sẽ tự động ánh xạ tiêu đề cột với câu hỏi tương ứng, gán nhãn nguồn <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-[11px] text-slate-800">csv_import</code> và kích hoạt trọn vẹn Quality Engine để sàng lọc bất thường.
        </p>

        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs text-slate-600 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong>Nguyên tắc bảo toàn dữ liệu:</strong> Dữ liệu nhập vào sẽ được phân tích qua 7 tầng kiểm định chất lượng (tốc độ, độ lặp, mẫu trả lời, logic, nội dung mở) tương đương với các phản hồi trực tuyến.
          </div>
        </div>

        <div className="pt-2 flex flex-wrap items-center gap-3">
          <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-dashed border-indigo-400 bg-indigo-50/40 hover:bg-indigo-50 text-indigo-700 text-xs font-semibold cursor-pointer transition-all">
            <Upload className="w-4 h-4" />
            <span>{importing ? 'Đang đọc và phân tích tệp...' : 'Chọn tệp CSV để nhập'}</span>
            <input
              type="file"
              accept=".csv"
              disabled={importing}
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          <button
            type="button"
            onClick={() => window.open(`/api/surveys/${surveyId}/import/template`, '_blank')}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-all shadow-2xs"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Tải Tệp Mẫu CSV (.csv)</span>
          </button>
        </div>

        {importResult && (
          <div className="p-3 rounded-xl bg-emerald-50 text-emerald-800 text-xs font-medium flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{importResult}</span>
          </div>
        )}
      </div>

      {/* Complete Academic Research Dossier (.ZIP) Section */}
      <div className="bg-gradient-to-br from-indigo-900 via-slate-900 to-slate-950 p-6 sm:p-8 rounded-2xl border border-indigo-700/50 shadow-md text-white space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-indigo-800/60 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-600/30 border border-indigo-500/40 text-indigo-300">
              <PackageCheck className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold tracking-wider uppercase mb-1">
                <Check className="w-3 h-3" /> Chuẩn Don Dillman & AAPOR
              </div>
              <h2 className="font-bold text-white text-lg tracking-tight">
                Trọn Bộ Hồ Sơ Nghiên Cứu Khoa Học (Academic Research Dossier)
              </h2>
            </div>
          </div>
          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/export/academic-dossier?scope=${scope}`, '_blank')}
            className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white font-bold text-xs shadow-lg shadow-indigo-500/25 transition-all shrink-0 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Archive className="w-4 h-4" />
            <span>Tải Trọn Gói Dossier (.ZIP)</span>
          </button>
        </div>

        <p className="text-xs text-indigo-200/90 leading-relaxed">
          Gói lưu trữ nén chuẩn mực phục vụ bảo vệ luận văn, đề tài nghiên cứu khoa học (KHKT, ISEF, ViSEF), nộp hội đồng đạo đức nghiên cứu hoặc công bố bài báo quốc tế. Đã tích hợp sẵn bộ mã hóa biến số, cú pháp phần mềm và chứng chỉ xác thực chữ ký số SHA-256 bất biến.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="font-bold text-indigo-300 flex items-center gap-1.5">
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" /> 2 Tập Dữ Liệu CSV
            </span>
            <p className="text-[11px] text-slate-300">
              <code>dataset_clean.csv</code> (mã hóa biến VAR001...) và <code>dataset_labeled.csv</code> (tiêu đề đầy đủ), có UTF-8 BOM.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="font-bold text-indigo-300 flex items-center gap-1.5">
              <Code2 className="w-4 h-4 text-blue-400" /> IBM SPSS & Script R
            </span>
            <p className="text-[11px] text-slate-300">
              <code>spss_syntax.sps</code> nạp biến/nhãn tự động và <code>run_analysis.R</code> tính hệ số độ tin cậy Cronbach's Alpha.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="font-bold text-indigo-300 flex items-center gap-1.5">
              <FileCode className="w-4 h-4 text-amber-400" /> Phân Tích Python
            </span>
            <p className="text-[11px] text-slate-300">
              <code>analyze_data.py</code> tự động tạo thống kê mô tả, phân tích tần số và ma trận tương quan bằng Pandas/NumPy.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="font-bold text-indigo-300 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> Chứng Chỉ Băm SHA-256
            </span>
            <p className="text-[11px] text-slate-300">
              <code>INTEGRITY_CERTIFICATE_SHA256.json</code> chứa vân tay số đối soát bảo vệ tính toàn vẹn toán học chống giả mạo.
            </p>
          </div>
        </div>
      </div>

      {/* Academic Research Manuscript Section */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 rounded-2xl border border-indigo-700/50 shadow-md text-white space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-indigo-800/60 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-violet-600/30 border border-violet-500/40 text-violet-300">
              <FileText className="w-6 h-6 text-violet-400" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 text-[10px] font-bold tracking-wider uppercase mb-1">
                <Sparkles className="w-3 h-3" /> Chuẩn Bài Báo Khoa Học (Peer-Review Manuscript)
              </div>
              <h2 className="font-bold text-white text-lg tracking-tight">
                Bản Thảo Nghiên Cứu Khoa Học Tự Động (Scientific Manuscript)
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowManuscriptModal(true)}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs shadow-md transition-all shrink-0 hover:scale-[1.02]"
              title="Mở studio tương tác xem trước A4, in ấn, xem Markdown và LaTeX Overleaf"
            >
              <BookOpen className="w-4 h-4 text-violet-200" />
              <span>Academic Manuscript Studio</span>
            </button>
            <button
              onClick={() => window.open(`/api/surveys/${surveyId}/export/manuscript?format=html&scope=${scope}`, '_blank')}
              className="flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-indigo-500/80 hover:bg-indigo-400 text-white font-bold text-xs shadow-md transition-all shrink-0 hover:scale-[1.02]"
              title="Xem và in ấn bản thảo theo định dạng khổ A4 trong tab mới"
            >
              <Printer className="w-4 h-4" />
              <span>In Nhanh (A4)</span>
            </button>
          </div>
        </div>

        <p className="text-xs text-indigo-200/90 leading-relaxed">
          Tự động biên soạn hoàn chỉnh toàn bộ bài báo nghiên cứu thực nghiệm bao gồm Tóm tắt (Abstract), Phương pháp luận Don Dillman, Bảng từ điển biến số, Kiểm định chất lượng 7 tầng, Hệ số tin cậy thang đo Cronbach's Alpha, Phễu rơi rụng nhận thức, Phân tích chéo Chi-Square, Phân tích cảm xúc định tính và Chứng chỉ băm bất biến SHA-256.
        </p>

        <div className="flex flex-wrap items-center gap-3 pt-1">
          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/export/manuscript?format=markdown&scope=${scope}`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all border border-white/20"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            <span>Tải Bản Thảo Markdown (.md)</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/export/manuscript?format=latex&scope=${scope}`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all border border-white/20"
          >
            <Download className="w-4 h-4 text-indigo-400" />
            <span>Tải Mã Nguồn LaTeX / Overleaf (.tex)</span>
          </button>
        </div>
      </div>

      {/* Individual Academic Codebook & Data Dictionary Section */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <FileSpreadsheet className="w-5 h-5 text-indigo-600" />
          <h2 className="font-bold text-slate-900 text-base">
            Tải riêng lẻ Cú pháp SPSS / R / Codebook JSON
          </h2>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          Tự động sinh nhãn biến (Variable Labels), nhãn phương án (Value Labels), định nghĩa giá trị khuyết thiếu (Missing Values) và phân loại thang đo (Nominal, Ordinal, Scale) chuẩn bị sẵn sàng cho các phần mềm phân tích thống kê chuyên dụng (SPSS, R, Stata, Python).
        </p>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            onClick={() => setShowCodebookModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-xs"
          >
            <BookOpen className="w-4 h-4" />
            <span>Mở Từ Điển Dữ Liệu & Cú Pháp Trực Tuyến</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/codebook?format=spss`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition-all border border-indigo-200/80"
          >
            <Code2 className="w-4 h-4" />
            <span>Tải Cú pháp SPSS (.sps)</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/codebook?format=stata`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-bold transition-all border border-emerald-300/80"
          >
            <Code2 className="w-4 h-4" />
            <span>Tải Do-File Stata (.do)</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/codebook?format=r`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold transition-all border border-blue-200/80"
          >
            <FileCode className="w-4 h-4" />
            <span>Tải Script R (.R Syntax)</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/paper/printable-html`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-bold transition-all border border-amber-300/80"
            title="Mở mẫu in phiếu khảo sát giấy chuẩn A4 kèm QR code và mốc căn góc OMR"
          >
            <Printer className="w-4 h-4 text-amber-700" />
            <span>Mẫu Phiếu Giấy OMR A4 (In / PDF)</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/audit-report/printable-certificate`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-800 text-xs font-bold transition-all border border-purple-300/80 shadow-2xs"
            title="Mở chứng thư thẩm định độ tin cậy và toàn vẹn dữ liệu chuẩn A4 có dấu số để kẹp hồ sơ đề tài"
          >
            <ShieldCheck className="w-4 h-4 text-purple-700" />
            <span>Chứng Thư Kiểm Định A4 (In / PDF)</span>
          </button>

          <button
            onClick={() => window.open(`/api/surveys/${surveyId}/codebook?format=json`, '_blank')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-bold transition-all border border-slate-200"
          >
            <Download className="w-4 h-4" />
            <span>Xem Từ điển Dữ liệu JSON</span>
          </button>
        </div>
      </div>

      <CodebookModal
        isOpen={showCodebookModal}
        onClose={() => setShowCodebookModal(false)}
        surveyId={surveyId}
        surveyTitle="Khảo sát Nghiên cứu"
      />

      <AcademicManuscriptModal
        isOpen={showManuscriptModal}
        onClose={() => setShowManuscriptModal(false)}
        surveyId={surveyId}
        surveyTitle="Khảo sát Nghiên cứu"
      />
    </div>
  );
};
