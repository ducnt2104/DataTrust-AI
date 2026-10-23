import React, { useState, useEffect, useRef } from 'react';
import QRCode from 'qrcode';
import {
  FileText,
  Printer,
  Upload,
  CheckCircle,
  AlertTriangle,
  Camera,
  RefreshCw,
  Eye,
  Sliders,
  ShieldCheck,
  ChevronLeft,
  ArrowRight,
  Info
} from 'lucide-react';
import { api } from '../api/client';
import { Survey, PaperTemplateLayout, PaperScanResult } from '../types/survey';

interface PaperSurveyPageProps {
  surveyId: string;
  onNavigate: (path: string) => void;
}

export function PaperSurveyPage({ surveyId, onNavigate }: PaperSurveyPageProps) {
  const [activeTab, setActiveTab] = useState<'template' | 'scan' | 'verify'>('template');
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [template, setTemplate] = useState<PaperTemplateLayout | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Scan state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [scanning, setScanning] = useState<boolean>(false);
  const [scanResult, setScanResult] = useState<PaperScanResult | null>(null);

  // Manual correction state
  const [correctedAnswers, setCorrectedAnswers] = useState<Record<string, any>>({});
  const [correctionReasons, setCorrectionReasons] = useState<Record<string, string>>({});
  const [enumeratorId, setEnumeratorId] = useState<string>('DTV-FIELD-01');
  const [ingesting, setIngesting] = useState<boolean>(false);
  const [ingestSuccess, setIngestSuccess] = useState<string | null>(null);

  // QR Canvas Ref for Template
  const qrCanvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    loadData();
  }, [surveyId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sData, tData] = await Promise.all([
        api.getSurvey(surveyId),
        api.getPaperTemplate(surveyId)
      ]);
      setSurvey(sData);
      setTemplate(tData.layout);
    } catch (err: any) {
      setError(err.message || 'Không thể tải dữ liệu mẫu phiếu giấy.');
    } finally {
      setLoading(false);
    }
  };

  // Generate QR code onto canvas whenever template is ready
  useEffect(() => {
    if (template && qrCanvasRef.current) {
      const qrPayload = JSON.stringify({
        survey_id: surveyId,
        form_id: `FORM-${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
        enumerator_id: enumeratorId
      });
      QRCode.toCanvas(qrCanvasRef.current, qrPayload, {
        width: 140,
        margin: 1,
        color: { dark: '#0f172a', light: '#ffffff' }
      }).catch(console.error);
    }
  }, [template, enumeratorId, surveyId, activeTab]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setImagePreviewUrl(URL.createObjectURL(file));
      setScanResult(null);
      setIngestSuccess(null);
    }
  };

  const handleScanSubmit = async () => {
    if (!selectedFile) return;
    setScanning(true);
    setError(null);
    try {
      const result: PaperScanResult = await api.scanPaperImage(surveyId, selectedFile);
      setScanResult(result);
      setCorrectedAnswers(result.detected_answers || {});
      if (result.enumerator_id) {
        setEnumeratorId(result.enumerator_id);
      }
      setActiveTab('verify');
    } catch (err: any) {
      setError(err.message || 'Lỗi trong quá trình quét và xử lý ảnh phiếu.');
    } finally {
      setScanning(false);
    }
  };

  const handleIngest = async () => {
    if (!scanResult) return;
    setIngesting(true);
    setError(null);

    // Xây dựng danh sách manual corrections
    const corrections = [];
    for (const [qid, newVal] of Object.entries(correctedAnswers)) {
      const origVal = scanResult.detected_answers[qid];
      if (JSON.stringify(newVal) !== JSON.stringify(origVal)) {
        corrections.push({
          question_id: qid,
          original: origVal,
          corrected: newVal,
          reason: correctionReasons[qid] || 'Điều tra viên chỉnh sửa thủ công tại giao diện số hóa'
        });
      }
    }

    try {
      const res = await api.ingestPaperResponse(surveyId, {
        form_id: scanResult.form_id,
        enumerator_id: enumeratorId,
        answers: correctedAnswers,
        omr_confidence: scanResult.confidence_score,
        manual_corrections: corrections
      });
      setIngestSuccess(`Phiếu giấy đã được số hóa và ghi nhận thành công (Mã phản hồi: ${res.response_id.substring(0, 8)}...). Điểm rủi ro: ${res.risk_score} (${res.risk_level.toUpperCase()}).`);
    } catch (err: any) {
      setError(err.message || 'Không thể lưu kết quả số hóa vào cơ sở dữ liệu.');
    } finally {
      setIngesting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 flex flex-col items-center justify-center">
        <RefreshCw className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
        <p className="text-slate-600 font-medium">Đang chuẩn bị mẫu phiếu và mô-đun thị giác máy tính...</p>
      </div>
    );
  }

  if (error && !survey) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-800 flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-lg">Lỗi tải phân hệ số hóa phiếu</h3>
            <p className="mt-1 text-sm">{error}</p>
            <button
              onClick={() => onNavigate(`/surveys/${surveyId}/edit`)}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 font-medium"
            >
              Quay lại khảo sát
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Print CSS Injection */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          #printable-paper-sheet, #printable-paper-sheet * {
            visibility: visible;
          }
          #printable-paper-sheet {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            margin: 0;
            padding: 10mm;
            border: none;
            box-shadow: none;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>

      {/* Header */}
      <div className="no-print flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/edit`)}
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 font-medium mb-2 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> Quay lại Trình tạo khảo sát
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Phân Hệ Số Hóa Phiếu Khảo Sát Giấy (Mobile OMR & QR)
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              OpenCV OMR Ready
            </span>
          </div>
          <p className="text-slate-600 text-sm mt-1">
            Khảo sát: <strong className="text-slate-800">{survey?.title}</strong> • Chuẩn hóa phối cảnh 2D, giải mã QR và đọc ô tích quang học
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl self-start md:self-auto border border-slate-200">
          <button
            onClick={() => setActiveTab('template')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'template'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-4 h-4" /> Mẫu Phiếu Chuẩn
          </button>
          <button
            onClick={() => setActiveTab('scan')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'scan'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Camera className="w-4 h-4" /> Quét & Tải Ảnh
          </button>
          <button
            onClick={() => setActiveTab('verify')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'verify'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Sliders className="w-4 h-4" /> Xác Nhận OMR
          </button>
        </div>
      </div>

      {error && (
        <div className="no-print mt-6 bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-600" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-xs text-red-600 hover:underline">
            Đóng
          </button>
        </div>
      )}

      {ingestSuccess && (
        <div className="no-print mt-6 bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-600" />
            <span className="text-sm font-medium">{ingestSuccess}</span>
          </div>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/responses`)}
            className="text-xs font-semibold bg-emerald-600 text-white px-3 py-1.5 rounded-lg hover:bg-emerald-700"
          >
            Mở Trung Tâm Rà Soát
          </button>
        </div>
      )}

      {/* --- TAB 1: MẪU PHIẾU CHUẨN IN A4 --- */}
      {activeTab === 'template' && (
        <div className="mt-8">
          <div className="no-print bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 flex items-start gap-3">
            <Info className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-900">
              <strong className="font-semibold">Quy chuẩn in ấn phiếu thực địa:</strong> Mẫu phiếu được căn chỉnh theo chuẩn A4 với{' '}
              <strong>4 mốc vuông căn góc màu đen</strong> ở 4 góc giấy và <strong>mã QR định danh</strong> góc trên. Khi in, vui lòng chọn tỷ lệ 100% (Actual Size), không thu nhỏ để đảm bảo độ chính xác nắn phẳng phối cảnh của OpenCV.
            </div>
          </div>

          <div className="no-print flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-slate-700">Mã điều tra viên mặc định:</label>
              <input
                type="text"
                value={enumeratorId}
                onChange={(e) => setEnumeratorId(e.target.value)}
                className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-sm font-mono w-48 text-slate-800"
                placeholder="VD: DTV-01"
              />
            </div>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-semibold shadow-sm transition-all"
            >
              <Printer className="w-4 h-4" /> In Phiếu Chuẩn (A4)
            </button>
          </div>

          {/* A4 Sheet Container */}
          <div
            id="printable-paper-sheet"
            className="bg-white border-2 border-slate-300 rounded-lg p-10 max-w-4xl mx-auto shadow-md relative min-h-[1100px]"
          >
            {/* 4 Fiducial Markers at corners */}
            <div className="absolute top-4 left-4 w-10 h-10 bg-black"></div>
            <div className="absolute top-4 right-4 w-10 h-10 bg-black"></div>
            <div className="absolute bottom-4 right-4 w-10 h-10 bg-black"></div>
            <div className="absolute bottom-4 left-4 w-10 h-10 bg-black"></div>

            {/* Header with Title and QR */}
            <div className="flex justify-between items-start pt-6 px-6 pb-4 border-b-2 border-slate-800">
              <div className="max-w-[70%]">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  DATATRUST AI — PHIẾU KHẢO SÁT THỰC ĐỊA CHUẨN HÓA
                </div>
                <h2 className="text-2xl font-black text-slate-900 mt-1 uppercase tracking-tight">
                  {survey?.title}
                </h2>
                {survey?.description && (
                  <p className="text-xs text-slate-600 mt-1">{survey.description}</p>
                )}
                <div className="mt-3 flex items-center gap-4 text-xs font-mono text-slate-700">
                  <span>Mã khảo sát: <strong>{surveyId.substring(0, 8)}</strong></span>
                  <span>Mã ĐTV: <strong>{enumeratorId}</strong></span>
                  <span>Ngày: ____/____/2026</span>
                </div>
              </div>

              {/* QR Code Container */}
              <div className="text-center p-2 border border-slate-300 rounded bg-slate-50">
                <canvas ref={qrCanvasRef} className="w-28 h-28 mx-auto" />
                <span className="text-[10px] font-mono text-slate-500 block mt-0.5">MÃ ĐỊNH DANH PHIẾU</span>
              </div>
            </div>

            {/* Instructions */}
            <div className="px-6 py-3 bg-slate-100/70 border-b border-slate-200 text-xs text-slate-700">
              <strong>Hướng dẫn điền:</strong> Dùng bút mực đen hoặc xanh tô kín hoàn toàn vào ô tròn phương án bạn chọn: <span className="inline-block w-3.5 h-3.5 rounded-full bg-slate-800 align-middle mx-1"></span>. Không gạch chéo hoặc đánh dấu tích V ra ngoài ô tròn.
            </div>

            {/* Questions List with standard bubbles */}
            <div className="px-6 py-6 space-y-6">
              {template?.questions.map((q, idx) => (
                <div key={q.question_id} className="border-b border-slate-200 pb-4">
                  <div className="font-bold text-sm text-slate-900 mb-2">
                    Câu {idx + 1}. {q.title}
                  </div>

                  {/* Bubbles */}
                  <div className="flex flex-wrap items-center gap-6 mt-2">
                    {q.bubbles.map((b) => (
                      <div key={b.option_id} className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full border-2 border-slate-700 flex items-center justify-center font-bold text-[10px] text-slate-800">
                          {b.option_id.length <= 2 ? b.option_id.toUpperCase() : ''}
                        </div>
                        <span className="text-xs text-slate-800">{b.option_label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="px-6 pt-4 text-center text-[10px] text-slate-400 border-t border-slate-200 absolute bottom-6 left-0 right-0">
              DataTrust AI Paper Digitization Architecture • Form Version {template?.template_version || 1} • Không gấp hoặc làm rách 4 góc căn chỉnh
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 2: QUÉT & TẢI ẢNH PHIẾU --- */}
      {activeTab === 'scan' && (
        <div className="mt-8 max-w-3xl mx-auto">
          <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-2">
              Tải lên hoặc Chụp ảnh phiếu khảo sát
            </h3>
            <p className="text-sm text-slate-600 mb-6">
              Hệ thống sẽ tự động tìm 4 mốc góc, nắn phẳng phối cảnh 2D, đo độ nét Laplacian và đọc tỷ lệ pixel tô đen của từng ô tích.
            </p>

            {/* Dropzone */}
            <label className="border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-indigo-50/20 transition-all">
              <input
                type="file"
                accept="image/jpeg,image/png,image/jpg"
                capture="environment"
                onChange={handleFileChange}
                className="hidden"
              />
              <Upload className="w-12 h-12 text-slate-400 mb-3" />
              <span className="text-sm font-semibold text-slate-800">
                Chọn ảnh chụp phiếu hoặc kéo thả vào đây
              </span>
              <span className="text-xs text-slate-500 mt-1">
                Hỗ trợ định dạng JPG, PNG từ camera điện thoại hoặc máy quét
              </span>
            </label>

            {/* Preview & Action */}
            {imagePreviewUrl && (
              <div className="mt-6 border border-slate-200 rounded-xl p-4 bg-slate-50 flex flex-col sm:flex-row items-center gap-6">
                <img
                  src={imagePreviewUrl}
                  alt="Ảnh phiếu đã chọn"
                  className="w-36 h-48 object-cover rounded-lg border border-slate-300 shadow-sm"
                />
                <div className="flex-1 text-center sm:text-left">
                  <h4 className="font-semibold text-sm text-slate-900">
                    {selectedFile?.name || 'Ảnh phiếu khảo sát'}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Kích thước: {(selectedFile!.size / 1024).toFixed(1)} KB
                  </p>
                  <p className="text-xs text-emerald-600 font-medium mt-2 flex items-center gap-1 justify-center sm:justify-start">
                    <CheckCircle className="w-3.5 h-3.5" /> Sẵn sàng chạy mô-đun thị giác máy tính OpenCV
                  </p>

                  <button
                    onClick={handleScanSubmit}
                    disabled={scanning}
                    className="mt-4 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg text-sm font-semibold inline-flex items-center gap-2 shadow-sm transition-all"
                  >
                    {scanning ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" /> Đang căn chỉnh phối cảnh & đọc OMR...
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4" /> Quét & Nhận diện OMR
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- TAB 3: XÁC NHẬN SỐ HÓA & SỬA NHANH --- */}
      {activeTab === 'verify' && (
        <div className="mt-8">
          {!scanResult ? (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-12 text-center text-slate-500">
              <Camera className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <h3 className="font-semibold text-slate-800 text-base">Chưa có ảnh quét nào được nạp</h3>
              <p className="text-sm mt-1">Vui lòng chuyển qua tab "Quét & Tải Ảnh" để chụp hoặc tải ảnh phiếu giấy.</p>
              <button
                onClick={() => setActiveTab('scan')}
                className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
              >
                Tải ảnh ngay
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Left Column: Visual Overlay image from OpenCV */}
              <div className="lg:col-span-5 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                  <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                    <Eye className="w-5 h-5 text-indigo-600" /> Ảnh Lớp Phủ Minh Chứng (Overlay)
                  </h3>
                  <span className="text-xs px-2.5 py-1 rounded-full font-semibold bg-indigo-50 text-indigo-700">
                    Confidence: {(scanResult.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Quality Metrics */}
                <div className="grid grid-cols-2 gap-2 text-xs mb-4">
                  <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block">Độ nét (Laplacian):</span>
                    <strong className="text-slate-900 font-mono text-sm">
                      {scanResult.image_quality.laplacian_variance} ({scanResult.image_quality.sharpness_status})
                    </strong>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block">Độ sáng & Tương phản:</span>
                    <strong className="text-slate-900 font-mono text-sm">
                      {scanResult.image_quality.mean_brightness} / {scanResult.image_quality.contrast_std}
                    </strong>
                  </div>
                </div>

                {scanResult.overlay_image_base64 && (
                  <div className="border border-slate-300 rounded-xl overflow-hidden shadow-inner max-h-[600px] overflow-y-auto">
                    <img
                      src={scanResult.overlay_image_base64}
                      alt="Ảnh nhận diện ô tích OMR"
                      className="w-full h-auto object-contain"
                    />
                  </div>
                )}
                <p className="text-[11px] text-slate-500 mt-3 text-center">
                  Vòng tròn xanh lá: Ô nhận diện hợp lệ • Vòng tròn cam: Ô nghi ngờ độ tin cậy thấp
                </p>
              </div>

              {/* Right Column: Interactive Verification Table */}
              <div className="lg:col-span-7 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                    <div>
                      <h3 className="font-bold text-slate-900 text-base">
                        Đối Chiếu & Chỉnh Sửa Nhanh Tại Hiện Trường
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Mã phiếu: <strong className="text-slate-800">{scanResult.form_id}</strong> • Mọi thao tác sửa đều được lưu vết trong Nhật ký Kiểm toán (Audit Log)
                      </p>
                    </div>
                  </div>

                  {/* Questions list with detected answers and correction picker */}
                  <div className="space-y-4 max-h-[520px] overflow-y-auto pr-2">
                    {template?.questions.map((q, idx) => {
                      const detectedVal = scanResult.detected_answers[q.question_id];
                      const currentVal = correctedAnswers[q.question_id];
                      const conf = scanResult.question_confidences[q.question_id] || 0.8;
                      const isModified = JSON.stringify(currentVal) !== JSON.stringify(detectedVal);

                      return (
                        <div
                          key={q.question_id}
                          className={`p-4 rounded-xl border transition-all ${
                            isModified
                              ? 'bg-amber-50/60 border-amber-300'
                              : 'bg-slate-50/70 border-slate-200'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <span className="font-semibold text-sm text-slate-900">
                              Câu {idx + 1}. {q.title}
                            </span>
                            <span
                              className={`text-[11px] px-2 py-0.5 rounded font-mono font-medium ${
                                conf >= 0.75
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              Conf: {(conf * 100).toFixed(0)}%
                            </span>
                          </div>

                          {/* Bubble selector options */}
                          <div className="flex flex-wrap gap-2 mt-2">
                            {q.bubbles.map((b) => {
                              const isChecked = String(currentVal) === String(b.option_id);
                              return (
                                <button
                                  key={b.option_id}
                                  type="button"
                                  onClick={() => {
                                    setCorrectedAnswers((prev) => ({
                                      ...prev,
                                      [q.question_id]: b.option_id
                                    }));
                                  }}
                                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition-all ${
                                    isChecked
                                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                                  }`}
                                >
                                  <span
                                    className={`w-2.5 h-2.5 rounded-full ${
                                      isChecked ? 'bg-white' : 'border border-slate-400'
                                    }`}
                                  />
                                  {b.option_label}
                                </button>
                              );
                            })}
                          </div>

                          {isModified && (
                            <div className="mt-3 pt-2 border-t border-amber-200 flex items-center gap-2">
                              <span className="text-[11px] font-semibold text-amber-800">
                                Đã sửa thủ công (Gốc: {String(detectedVal)}):
                              </span>
                              <input
                                type="text"
                                placeholder="Lý do sửa (VD: người dân gạch xóa tô lại)"
                                value={correctionReasons[q.question_id] || ''}
                                onChange={(e) =>
                                  setCorrectionReasons((prev) => ({
                                    ...prev,
                                    [q.question_id]: e.target.value
                                  }))
                                }
                                className="flex-1 px-2.5 py-1 text-xs bg-white border border-amber-300 rounded text-slate-800"
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Ingestion Footer Button */}
                <div className="pt-6 border-t border-slate-200 mt-6 flex items-center justify-between">
                  <div className="text-xs text-slate-500">
                    Sau khi bấm nạp, dữ liệu sẽ chạy qua <strong>Quality Engine</strong> để đối chiếu trùng lặp và tính điểm rủi ro.
                  </div>
                  <button
                    onClick={handleIngest}
                    disabled={ingesting}
                    className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white rounded-xl text-sm font-bold inline-flex items-center gap-2 shadow-sm transition-all"
                  >
                    {ingesting ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" /> Đang nạp vào CSDL...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4" /> Xác Nhận & Nạp Vào CSDL
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
