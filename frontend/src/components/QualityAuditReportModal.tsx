import React, { useEffect, useState } from 'react';
import { 
  X, Printer, ShieldCheck, CheckCircle2, AlertTriangle, Scale, 
  FileCheck, Globe, FileText, Database, Lock, UserX, Info 
} from 'lucide-react';
import { api } from '../api/client';
import { QualityAuditReport } from '../types/survey';

interface Props {
  surveyId: string;
  isOpen: boolean;
  onClose: () => void;
  onRefreshAnalytics?: () => void;
}

export const QualityAuditReportModal: React.FC<Props> = ({
  surveyId,
  isOpen,
  onClose,
  onRefreshAnalytics
}) => {
  const [report, setReport] = useState<QualityAuditReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [anonymizing, setAnonymizing] = useState(false);
  const [anonymizeMsg, setAnonymizeMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadReport();
    }
  }, [isOpen, surveyId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const data = await api.getQualityAuditReport(surveyId);
      setReport(data);
    } catch (err) {
      console.error(err);
      alert('Không thể tải báo cáo kiểm định chất lượng.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleAnonymize = async () => {
    if (!window.confirm('Bạn có chắc chắn muốn thực thi ẩn danh hóa toàn bộ thông tin định danh (IP, User-Agent, Text) của các phản hồi theo Nghị định 356/2025/NĐ-CP? Hành động này sẽ được ghi vào nhật ký kiểm toán bất biến.')) {
      return;
    }

    try {
      setAnonymizing(true);
      setAnonymizeMsg(null);
      const res = await api.anonymizeSurveyResponses(surveyId, {
        anonymize_client_metadata: true,
        mask_text_answers: true,
        operator_notes: 'Thực thi nghiệm thu đề tài nghiên cứu khoa học'
      });
      setAnonymizeMsg(res.message);
      loadReport();
      if (onRefreshAnalytics) onRefreshAnalytics();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi khi ẩn danh hóa');
    } finally {
      setAnonymizing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 print:p-0 print:bg-white print:static">
      <div className="bg-white rounded-3xl max-w-4xl w-full border border-slate-200/90 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 print:shadow-none print:border-none print:max-w-full">
        {/* Modal Top Control Bar (Hidden when printing) */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between print:hidden">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-600" />
            <span className="text-sm font-bold text-slate-800">
              Báo cáo Kiểm định Chất lượng Dữ liệu & Tuân thủ Pháp lý (Evidence-Based Audit Report)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs transition-colors"
            >
              <Printer className="w-4 h-4" />
              <span>In báo cáo / Lưu PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Content / Printable Body */}
        <div className="p-6 sm:p-10 space-y-8 max-h-[85vh] overflow-y-auto print:max-h-none print:p-0">
          {loading ? (
            <div className="py-20 text-center text-slate-500 space-y-2">
              <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
              <div className="text-xs font-medium">Đang tổng hợp bằng chứng kiểm định và tạo mã băm...</div>
            </div>
          ) : !report ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              Không có dữ liệu báo cáo kiểm định.
            </div>
          ) : (
            <>
              {/* Header Certificate */}
              <div className="border-b-2 border-indigo-600 pb-6 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div>
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold tracking-wide uppercase">
                    <FileCheck className="w-4 h-4" />
                    <span>Chứng nhận Kiểm định Chất lượng Dữ liệu</span>
                  </div>
                  <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-2 tracking-tight">
                    DATA INTEGRITY & FRAUD AUDIT REPORT
                  </h1>
                  <p className="text-sm text-slate-600 mt-1">
                    Khảo sát: <strong className="text-slate-900">{report.survey_title}</strong> (ID: {report.survey_id})
                  </p>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Thời điểm kết xuất: {new Date(report.generated_at).toLocaleString('vi-VN')}
                  </div>
                </div>

                <div className="bg-slate-50 border border-slate-200/90 rounded-2xl p-4 text-center sm:text-right shrink-0">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Mã băm kiểm định SHA-256</div>
                  <div className="font-mono text-sm font-black text-indigo-700 mt-0.5 tracking-wider">{report.audit_hash}</div>
                  <div className="text-[10px] text-emerald-600 font-bold mt-1 flex items-center justify-center sm:justify-end gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Bảo toàn tính bất biến
                  </div>
                </div>
              </div>

              {/* Data Trust Index & KPI Summary */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="p-5 rounded-2xl bg-indigo-50 border border-indigo-100 flex flex-col justify-between">
                  <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider">Chỉ số Tin cậy Dữ liệu (DTI)</span>
                  <div className="text-3xl font-black text-indigo-700 mt-2">{report.data_trust_index}%</div>
                  <span className="text-[11px] text-indigo-600 font-medium mt-1">
                    {report.data_trust_index >= 90 ? 'Độ tin cậy xuất sắc' : report.data_trust_index >= 75 ? 'Độ tin cậy khá' : 'Cần rà soát tăng cường'}
                  </span>
                </div>

                <div className="p-5 rounded-2xl bg-white border border-slate-200 flex flex-col justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tổng mẫu thu thập</span>
                  <div className="text-3xl font-extrabold text-slate-900 mt-2">{report.total_collected}</div>
                  <span className="text-[11px] text-slate-400">100% dữ liệu quan hệ</span>
                </div>

                <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-100 flex flex-col justify-between">
                  <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider">Mẫu sạch đã kiểm chứng</span>
                  <div className="text-3xl font-black text-emerald-700 mt-2">{report.verified_clean_count}</div>
                  <span className="text-[11px] text-emerald-600 font-medium">Sẵn sàng xuất cho SPSS/R/Python</span>
                </div>

                <div className="p-5 rounded-2xl bg-rose-50 border border-rose-100 flex flex-col justify-between">
                  <span className="text-xs font-bold text-rose-900 uppercase tracking-wider">Nguy cơ cao gắn cờ</span>
                  <div className="text-3xl font-black text-rose-700 mt-2">{report.risk_breakdown?.high || 0}</div>
                  <span className="text-[11px] text-rose-600 font-medium">Đã phát hiện và cách ly</span>
                </div>
              </div>

              {/* Multi-channel Source Breakdown */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200/90 space-y-3">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-indigo-600" />
                  <span>Kênh thu thập & Số hóa (Collection Modalities)</span>
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-emerald-600" />
                      <span className="text-xs font-medium text-slate-700">Khảo sát trực tuyến:</span>
                    </div>
                    <span className="text-xs font-bold text-slate-900 font-mono">{report.source_breakdown?.online_form || 0} phản hồi</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-amber-600" />
                      <span className="text-xs font-medium text-slate-700">Số hóa phiếu giấy OMR:</span>
                    </div>
                    <span className="text-xs font-bold text-slate-900 font-mono">{report.source_breakdown?.paper_scan || 0} phản hồi</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4 text-sky-600" />
                      <span className="text-xs font-medium text-slate-700">Tệp CSV ngoại tuyến:</span>
                    </div>
                    <span className="text-xs font-bold text-slate-900 font-mono">{report.source_breakdown?.csv_import || 0} phản hồi</span>
                  </div>
                </div>
              </div>

              {/* Fraud Screening Signals (7 Layers) */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200/90 space-y-4">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span>Chi tiết 6 nhóm tín hiệu sàng lọc bất thường (Data Quality Engine 7 Layers)</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { label: 'Làm bài siêu tốc (Speeding)', count: report.fraud_signals.speeding, desc: 'T < 2.2s/câu hỏi' },
                    { label: 'Chọn 1 đáp án (Straightlining)', count: report.fraud_signals.straightlining, desc: 'Điền qua loa ma trận/Likert' },
                    { label: 'Trùng lặp đáp án (Duplicates)', count: report.fraud_signals.duplicate, desc: 'Hamming Similarity ≥ 85%' },
                    { label: 'Vi phạm logic chéo (Contradiction)', count: report.fraud_signals.logic_violation, desc: 'Mâu thuẫn điều kiện ràng buộc' },
                    { label: 'Văn bản vô nghĩa (Gibberish)', count: report.fraud_signals.gibberish_text, desc: 'Entropy Shannon ký tự thấp' },
                    { label: 'Bất thường ĐTV (Enumerator)', count: report.fraud_signals.enumerator_anomaly, desc: 'Z-score phương sai bất thường' }
                  ].map((sig, i) => (
                    <div key={i} className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col justify-between">
                      <div className="text-xs font-semibold text-slate-700">{sig.label}</div>
                      <div className="mt-2 flex items-baseline justify-between">
                        <span className={`text-xl font-black ${sig.count > 0 ? 'text-rose-600' : 'text-slate-400'}`}>
                          {sig.count}
                        </span>
                        <span className="text-[10px] text-slate-400">{sig.desc}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Legal & Ethical Compliance Banner */}
              <div className="p-5 rounded-2xl bg-slate-900 text-white space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Scale className="w-5 h-5 text-indigo-400" />
                    <h3 className="text-sm font-bold text-white">Tuân thủ Đạo đức Nghiên cứu & Pháp luật Bảo vệ Dữ liệu Cá nhân</h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    NGHỊ ĐỊNH 356/2025/NĐ-CP COMPLIANT
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {report.compliance_statement.principles_applied.map((p, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 space-y-1">
                      <div className="font-bold text-indigo-300 flex items-center gap-1.5">
                        <Lock className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        <span>{p.principle}</span>
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">{p.description}</p>
                    </div>
                  ))}
                </div>

                {/* Right to Erasure / Anonymization Action (Hidden when printing) */}
                <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 print:hidden">
                  <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                    <Info className="w-4 h-4 text-indigo-400 shrink-0" />
                    <span>Sau khi hoàn tất nghiệm thu, bạn có thể thực thi ẩn danh hóa toàn bộ thông tin PII.</span>
                  </div>
                  <button
                    onClick={handleAnonymize}
                    disabled={anonymizing}
                    className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all disabled:opacity-50"
                  >
                    <UserX className="w-4 h-4" />
                    <span>{anonymizing ? 'Đang xử lý...' : 'Thực thi Ẩn danh hóa PII'}</span>
                  </button>
                </div>

                {anonymizeMsg && (
                  <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2 print:hidden">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{anonymizeMsg}</span>
                  </div>
                )}
              </div>

              {/* Methodology Citations */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/70 text-xs text-slate-500 space-y-2">
                <div className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">
                  Cơ sở khoa học và Tiêu chuẩn trích dẫn (Academic Citations):
                </div>
                <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed">
                  {report.methodology_citations.map((cite, idx) => (
                    <li key={idx}>{cite}</li>
                  ))}
                </ul>
              </div>

              {/* Signatures for Formal Submission */}
              <div className="hidden print:grid grid-cols-2 pt-8 text-center text-xs text-slate-800">
                <div className="space-y-12">
                  <div className="font-bold">ĐẠI DIỆN ĐƠN VỊ THU THẬP & SỐ HÓA</div>
                  <div className="italic text-slate-400">(Ký và ghi rõ họ tên)</div>
                </div>
                <div className="space-y-12">
                  <div className="font-bold">CHUYÊN VIÊN KIỂM ĐỊNH CHẤT LƯỢNG</div>
                  <div className="italic text-slate-400">(Ký và ghi rõ họ tên)</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};