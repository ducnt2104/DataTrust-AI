import React, { useState } from 'react';
import { 
  ArrowLeft, Download, Upload, FileText, CheckCircle2, ShieldCheck, 
  Database, Globe, Layers, AlertCircle, Info 
} from 'lucide-react';

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

        <div className="pt-2">
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
        </div>

        {importResult && (
          <div className="p-3 rounded-xl bg-emerald-50 text-emerald-800 text-xs font-medium flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{importResult}</span>
          </div>
        )}
      </div>
    </div>
  );
};