import React, { useEffect, useRef, useState } from 'react';
import { X, Copy, Check, ExternalLink, QrCode } from 'lucide-react';
import QRCode from 'qrcode';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  surveyTitle: string;
  publicSlug: string;
}

export const ShareModal: React.FC<Props> = ({ isOpen, onClose, surveyTitle, publicSlug }) => {
  const [copied, setCopied] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const fullUrl = `${window.location.origin}/s/${publicSlug}`;

  useEffect(() => {
    if (isOpen && canvasRef.current) {
      QRCode.toCanvas(canvasRef.current, fullUrl, {
        width: 220,
        margin: 2,
        color: {
          dark: '#0f172a',
          light: '#ffffff'
        }
      }, (err) => {
        if (err) console.error('Lỗi sinh mã QR:', err);
      });
    }
  }, [isOpen, fullUrl]);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(fullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-100 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-2">
            <QrCode className="w-5 h-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900">Chia sẻ cuộc khảo sát</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200/50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          <div>
            <h4 className="text-sm font-medium text-slate-500 mb-1">Khảo sát đã xuất bản:</h4>
            <p className="text-base font-semibold text-slate-900 line-clamp-1">{surveyTitle}</p>
          </div>

          {/* QR Code Preview */}
          <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-xl border border-slate-200/80">
            <canvas ref={canvasRef} className="rounded-lg shadow-xs" />
            <span className="text-xs text-slate-500 mt-2 font-medium">Quét bằng camera điện thoại hoặc ứng dụng</span>
          </div>

          {/* Link Box */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Đường liên kết trực tiếp</label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={fullUrl}
                className="flex-1 px-3 py-2 text-sm bg-slate-100 border border-slate-300 rounded-lg text-slate-800 font-mono select-all focus:outline-hidden"
              />
              <button
                onClick={handleCopy}
                className={`px-3.5 py-2 text-sm font-medium rounded-lg flex items-center gap-1.5 transition-all ${
                  copied
                    ? 'bg-emerald-600 text-white'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs'
                }`}
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Đã chép' : 'Sao chép'}</span>
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-2">
            <a
              href={fullUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              <span>Mở thử nghiệm tab mới</span>
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Đóng
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
