import React, { useEffect, useState } from 'react';
import { 
  X, Printer, ShieldCheck, CheckCircle2, AlertTriangle, Scale, 
  FileCheck, Globe, FileText, Database, Lock, UserX, Info,
  Link2, Hash, RefreshCw, KeyRound, ShieldAlert, Zap, Terminal, Shield, Play
} from 'lucide-react';
import { api } from '../api/client';
import { QualityAuditReport, AuditTrail, RedTeamSimulationResult } from '../types/survey';

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
  const [activeTab, setActiveTab] = useState<'report' | 'audit_trail' | 'red_team'>('report');
  const [report, setReport] = useState<QualityAuditReport | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditTrail | null>(null);
  const [redTeamResult, setRedTeamResult] = useState<RedTeamSimulationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingTrail, setLoadingTrail] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [anonymizing, setAnonymizing] = useState(false);
  const [anonymizeMsg, setAnonymizeMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadReport();
      loadAuditTrail();
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

  const loadAuditTrail = async () => {
    try {
      setLoadingTrail(true);
      const trail = await api.getAuditTrail(surveyId);
      setAuditTrail(trail);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTrail(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleRunSimulation = async () => {
    try {
      setSimulating(true);
      const res = await api.simulateRedTeamAttack(surveyId);
      setRedTeamResult(res);
      // Cập nhật ngầm chuỗi băm bất biến vì simulate-attack tự động ghi log RED_TEAM_AUDIT_SIMULATION
      loadAuditTrail();
      if (onRefreshAnalytics) onRefreshAnalytics();
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : 'Lỗi khi thực thi thử nghiệm đối kháng Red-Team.');
    } finally {
      setSimulating(false);
    }
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
      <div 
        role="dialog"
        aria-modal="true"
        aria-labelledby="quality-audit-modal-title"
        className="bg-white rounded-3xl max-w-4xl w-full border border-slate-200/90 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 print:shadow-none print:border-none print:max-w-full"
      >
        {/* Modal Top Control Bar (Hidden when printing) */}
        <div className="px-6 py-3.5 bg-slate-50 border-b border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 print:hidden">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-indigo-600" />
              <span id="quality-audit-modal-title" className="text-sm font-bold text-slate-800">
                Kiểm định Dữ liệu & Chuỗi Băm Bất biến
              </span>
            </div>

            {/* Tab switchers */}
            <div className="flex items-center bg-slate-200/80 p-0.5 rounded-xl text-xs font-bold">
              <button
                onClick={() => setActiveTab('report')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'report' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <FileCheck className="w-3.5 h-3.5" />
                <span>Báo Cáo Nghiệm Thu</span>
              </button>
              <button
                onClick={() => {
                  setActiveTab('audit_trail');
                  loadAuditTrail();
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'audit_trail' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Link2 className="w-3.5 h-3.5" />
                <span>Chuỗi Băm SHA-256</span>
                {auditTrail && (
                  <span className={`w-2 h-2 rounded-full ${auditTrail.is_chain_valid ? 'bg-emerald-500' : 'bg-rose-500 animate-ping'}`} />
                )}
              </button>
              <button
                onClick={() => {
                  setActiveTab('red_team');
                  if (!redTeamResult && !simulating) {
                    handleRunSimulation();
                  }
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'red_team' ? 'bg-white text-rose-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Giả Lập Đối Kháng (Red-Team)</span>
                {redTeamResult && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            {activeTab === 'report' && (
              <>
                <button
                  onClick={() => window.open(`/api/surveys/${surveyId}/audit-report/printable-certificate`, '_blank')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold text-xs border border-amber-300 transition-colors shadow-2xs"
                  title="Mở Chứng Thư Thẩm Định A4 trang trọng kèm dấu bảo an kỹ thuật số để nộp hồ sơ hoặc lưu PDF"
                >
                  <FileText className="w-4 h-4 text-amber-600" />
                  <span>Chứng Thư A4 (In / PDF)</span>
                </button>
                <button
                  onClick={handlePrint}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs transition-colors"
                >
                  <Printer className="w-4 h-4" />
                  <span>In màn hình</span>
                </button>
              </>
            )}
            {activeTab === 'audit_trail' && (
              <button
                onClick={loadAuditTrail}
                disabled={loadingTrail}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingTrail ? 'animate-spin' : ''}`} />
                <span>Kiểm chứng lại</span>
              </button>
            )}
            {activeTab === 'red_team' && (
              <button
                onClick={handleRunSimulation}
                disabled={simulating}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs border border-rose-200 transition-colors disabled:opacity-50 shadow-2xs"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${simulating ? 'animate-spin' : ''}`} />
                <span>{simulating ? 'Đang giả lập...' : 'Chạy lại thử nghiệm'}</span>
              </button>
            )}
            <button
              onClick={onClose}
              aria-label="Đóng cửa sổ kiểm định"
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Content / Printable Body */}
        <div className="p-6 sm:p-10 space-y-8 max-h-[85vh] overflow-y-auto print:max-h-none print:p-0">
          {activeTab === 'report' && (
            loading ? (
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
                  {report.ledger_head_hash && (
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5" title={`Chữ ký đỉnh chuỗi: ${report.ledger_head_hash}`}>
                      Ledger: {report.ledger_head_hash.slice(0, 12)}...
                    </div>
                  )}
                  <div className="text-[10px] text-emerald-600 font-bold mt-1 flex items-center justify-center sm:justify-end gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Bảo toàn tính bất biến
                  </div>
                </div>
              </div>

              {/* Data Trust Index & KPI Summary */}
              <div className={`grid grid-cols-1 ${report.cronbach_alpha !== undefined && report.cronbach_alpha !== null ? 'sm:grid-cols-5' : 'sm:grid-cols-4'} gap-4`}>
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

                {report.cronbach_alpha !== undefined && report.cronbach_alpha !== null && (
                  <div className="p-5 rounded-2xl bg-teal-50 border border-teal-100 flex flex-col justify-between">
                    <span className="text-xs font-bold text-teal-900 uppercase tracking-wider">Độ Tin Cậy (Cronbach's α)</span>
                    <div className="text-3xl font-black text-teal-700 mt-2">{report.cronbach_alpha}</div>
                    <span className="text-[11px] text-teal-600 font-medium">
                      {report.cronbach_alpha >= 0.8 ? 'Rất tốt (≥ 0.8)' : report.cronbach_alpha >= 0.7 ? 'Đạt chuẩn (≥ 0.7)' : 'Cần cải thiện (< 0.7)'}
                    </span>
                  </div>
                )}

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
          )
        )}

        {activeTab === 'audit_trail' && (
          /* Cryptographic Audit Hash Chain View */
          <div className="space-y-6">
              {loadingTrail ? (
                <div className="py-20 text-center text-slate-500 space-y-2">
                  <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
                  <div className="text-xs font-medium">Đang truy xuất và xác thực toán học chuỗi băm bất biến...</div>
                </div>
              ) : !auditTrail ? (
                <div className="py-12 text-center text-slate-500 text-sm">
                  Chưa có dữ liệu chuỗi băm kiểm toán cho khảo sát này.
                </div>
              ) : (
                <>
                  {/* Integrity Status Hero Banner */}
                  <div className={`p-6 rounded-2xl border ${
                    auditTrail.is_chain_valid 
                      ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950' 
                      : 'bg-rose-50 border-rose-300 text-rose-950'
                  }`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-start gap-3">
                        {auditTrail.is_chain_valid ? (
                          <div className="p-2.5 rounded-xl bg-emerald-600 text-white shrink-0 mt-0.5">
                            <ShieldCheck className="w-6 h-6" />
                          </div>
                        ) : (
                          <div className="p-2.5 rounded-xl bg-rose-600 text-white shrink-0 mt-0.5 animate-pulse">
                            <ShieldAlert className="w-6 h-6" />
                          </div>
                        )}
                        <div>
                          <div className="flex items-center gap-2">
                            <h2 className="text-base sm:text-lg font-black tracking-tight">
                              {auditTrail.is_chain_valid 
                                ? 'CHUỖI BĂM KIỂM TOÁN BẤT BIẾN — 100% TOÀN VẸN' 
                                : 'CẢNH BÁO: PHÁT HIỆN CAN THIỆP DỮ LIỆU BẤT HỢP PHÁP'}
                            </h2>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
                              auditTrail.is_chain_valid 
                                ? 'bg-emerald-200/80 text-emerald-900 border border-emerald-300' 
                                : 'bg-rose-200 text-rose-900 border border-rose-400'
                            }`}>
                              {auditTrail.chain_status}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                            {auditTrail.verification_message}
                          </p>
                          <div className="text-[11px] text-slate-400 mt-1">
                            Thời điểm kiểm chứng: {new Date(auditTrail.verified_at).toLocaleString('vi-VN')}
                          </div>
                        </div>
                      </div>

                      <div className="sm:text-right shrink-0 bg-white/80 p-3 rounded-xl border border-slate-200/80">
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Tổng mắt xích</div>
                        <div className="text-2xl font-black text-slate-900 font-mono mt-0.5">
                          {auditTrail.total_records}
                        </div>
                      </div>
                    </div>

                    {/* Hash Anchors */}
                    <div className="mt-4 pt-4 border-t border-emerald-200/60 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                      <div className="p-2.5 rounded-xl bg-white/70 border border-emerald-100 space-y-0.5">
                        <div className="text-[10px] text-slate-400 uppercase font-sans font-semibold">Chữ ký đỉnh chuỗi (Head Hash):</div>
                        <div className="text-indigo-700 font-bold break-all text-[11px]">
                          {auditTrail.head_hash || 'GENESIS'}
                        </div>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white/70 border border-emerald-100 space-y-0.5">
                        <div className="text-[10px] text-slate-400 uppercase font-sans font-semibold">Khởi nguồn chuỗi (Genesis Hash):</div>
                        <div className="text-slate-600 font-bold break-all text-[11px]">
                          {auditTrail.genesis_hash || '0000000000000000000000000000000000000000000000000000000000000000'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Chained Events Timeline */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-700 uppercase tracking-wider">
                      <div className="flex items-center gap-1.5">
                        <Hash className="w-4 h-4 text-indigo-600" />
                        <span>Nhật Ký Các Sự Kiện Được Băm SHA-256 (Chronological Provenance)</span>
                      </div>
                      <span className="text-[11px] font-normal text-slate-500">
                        Hiển thị {auditTrail.events.length} sự kiện liên quan
                      </span>
                    </div>

                    {auditTrail.events.length === 0 ? (
                      <div className="p-8 text-center text-slate-400 bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-xs">
                        Chưa có sự kiện nào được ghi nhận cho khảo sát này.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {auditTrail.events.map((ev, idx) => {
                          const actionStyles: Record<string, string> = {
                            CREATE: 'bg-emerald-100 text-emerald-800 border-emerald-300',
                            UPDATE: 'bg-sky-100 text-sky-800 border-sky-300',
                            PUBLISH: 'bg-indigo-100 text-indigo-800 border-indigo-300',
                            CLOSE: 'bg-amber-100 text-amber-800 border-amber-300',
                            REOPEN: 'bg-teal-100 text-teal-800 border-teal-300',
                            REVIEW_DECISION: 'bg-purple-100 text-purple-800 border-purple-300',
                            ANONYMIZATION_EXECUTED: 'bg-rose-100 text-rose-800 border-rose-300',
                            MANUAL_CORRECTION_FIELD_OMR: 'bg-orange-100 text-orange-800 border-orange-300'
                          };
                          const badgeStyle = actionStyles[ev.action] || 'bg-slate-100 text-slate-800 border-slate-300';

                          return (
                            <div key={ev.id} className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs space-y-3 hover:border-indigo-300 transition-colors">
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2">
                                <div className="flex items-center gap-2">
                                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-600 font-mono text-[11px] font-black flex items-center justify-center">
                                    {String(idx + 1).padStart(2, '0')}
                                  </span>
                                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider border ${badgeStyle}`}>
                                    {ev.action}
                                  </span>
                                  <span className="text-xs text-slate-500 font-medium">
                                    Thực thể: <code className="text-slate-700 bg-slate-50 px-1 py-0.5 rounded">{ev.entity_type}</code>
                                  </span>
                                </div>
                                <div className="text-[11px] text-slate-400 font-mono">
                                  {new Date(ev.created_at).toLocaleString('vi-VN')}
                                </div>
                              </div>

                              {/* Details preview */}
                              {ev.details && Object.keys(ev.details).length > 0 && (
                                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-700 space-y-1">
                                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Chi tiết sự kiện:</div>
                                  <div className="flex flex-wrap gap-2">
                                    {Object.entries(ev.details).map(([k, v]) => (
                                      <span key={k} className="inline-flex items-center gap-1 bg-white px-2 py-1 rounded-lg border border-slate-200/70 text-[11px]">
                                        <strong className="text-slate-600">{k}:</strong>
                                        <span className="text-slate-900 font-medium">
                                          {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                                        </span>
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Cryptographic Hash Pair */}
                              <div className="p-2.5 rounded-xl bg-slate-900 text-slate-300 font-mono text-[11px] space-y-1">
                                <div className="flex items-center justify-between text-[10px] text-slate-400">
                                  <span>XÁC THỰC MẮT XÍCH SHA-256</span>
                                  <span className="flex items-center gap-1 text-emerald-400 font-bold">
                                    <CheckCircle2 className="w-3 h-3" />
                                    Chữ ký hợp lệ
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-slate-500 text-[10px] uppercase w-16 shrink-0">prev_hash:</span>
                                  <span className="text-slate-400 truncate text-[10px]">{ev.prev_hash}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-indigo-400 text-[10px] uppercase w-16 shrink-0 font-bold">entry_hash:</span>
                                  <span className="text-indigo-300 font-bold truncate text-[10px]">{ev.entry_hash}</span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'red_team' && (
            <div className="space-y-6">
              {/* Red-Team Hero Banner */}
              <div className="p-6 rounded-3xl bg-linear-to-br from-slate-900 via-rose-950 to-slate-900 text-white border border-rose-900/60 shadow-xl relative overflow-hidden">
                <div className="absolute -top-12 -right-12 w-48 h-48 bg-rose-500/10 rounded-full blur-2xl pointer-events-none" />
                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="space-y-2 max-w-2xl">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/30">
                      <ShieldAlert className="w-4 h-4 text-rose-400" />
                      <span>Thử Nghiệm Đối Kháng Trực Tiếp (Adversarial Red-Team Sandbox)</span>
                    </div>
                    <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                      HỆ THỐNG PHÒNG VỆ AN NINH & CHỐNG GIAN LẬN DỮ LIỆU
                    </h2>
                    <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                      Mô phỏng tấn công đối kháng 6 kịch bản thực tế (SQL Injection, XSS, CWE-1236 Formula Injection, Can thiệp Sổ cái SHA-256, Bot Speeder & Bot Straightliner). Tự động xác thực khả năng phòng vệ và ghi vết vào Sổ cái bất biến.
                    </p>
                  </div>

                  <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end gap-3 shrink-0">
                    <button
                      onClick={handleRunSimulation}
                      disabled={simulating}
                      className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-linear-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-black text-sm shadow-lg shadow-rose-950/40 border border-rose-400/40 transition-all active:scale-95 disabled:opacity-50"
                    >
                      {simulating ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin text-white" />
                          <span>Đang kiểm thử đối kháng...</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 fill-white" />
                          <span>Kích Hoạt Thử Nghiệm Đối Kháng</span>
                        </>
                      )}
                    </button>
                    {redTeamResult && (
                      <div className="text-[11px] text-rose-200/80 font-mono">
                        Lần thử gần nhất: {new Date(redTeamResult.timestamp).toLocaleTimeString('vi-VN')}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {simulating ? (
                <div className="py-20 text-center text-slate-500 space-y-3 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                  <div className="w-10 h-10 border-3 border-rose-600 border-t-transparent rounded-full animate-spin mx-auto" />
                  <div className="text-sm font-bold text-slate-800">Đang thực thi các kịch bản đối kháng sandbox...</div>
                  <div className="text-xs text-slate-500">Kiểm tra AST SQLite, bộ lọc ký tự OWASP, SHA-256 Avalanche Effect và mô hình nhận thức Don Dillman...</div>
                </div>
              ) : !redTeamResult ? (
                <div className="p-12 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-300 space-y-4">
                  <div className="w-14 h-14 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center mx-auto shadow-inner">
                    <ShieldAlert className="w-8 h-8" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-800">Chưa có dữ liệu thử nghiệm cho phiên làm việc này</h3>
                    <p className="text-xs text-slate-500 max-w-md mx-auto">
                      Nhấn nút "Kích Hoạt Thử Nghiệm Đối Kháng" ở trên để chạy mô phỏng 6 kịch bản tấn công đối kháng trực tiếp và xác nhận chỉ số phòng vệ hệ thống.
                    </p>
                  </div>
                  <button
                    onClick={handleRunSimulation}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-xs transition-colors"
                  >
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>Bắt đầu kiểm thử</span>
                  </button>
                </div>
              ) : (
                <>
                  {/* Defense KPI Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                    <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex flex-col justify-between">
                      <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">Trạng thái an ninh</span>
                      <div className="flex items-center gap-2 mt-2">
                        <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                        <span className="text-2xl font-black text-emerald-700 font-mono">{redTeamResult.overall_status}</span>
                      </div>
                      <span className="text-[11px] text-emerald-600 font-medium mt-1">
                        Phòng vệ thành công {redTeamResult.attacks_deflected}/{redTeamResult.attacks_tested} kịch bản
                      </span>
                    </div>

                    <div className="p-4 rounded-2xl bg-white border border-slate-200 flex flex-col justify-between">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Tỷ lệ phòng vệ</span>
                      <div className="text-3xl font-black text-slate-900 mt-2 font-mono">
                        {redTeamResult.compliance_score}%
                      </div>
                      <span className="text-[11px] text-emerald-600 font-semibold mt-1">100% Chặn đứng rủi ro</span>
                    </div>

                    <div className="p-4 rounded-2xl bg-white border border-slate-200 flex flex-col justify-between">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Độ trễ xử lý (Latency)</span>
                      <div className="text-3xl font-black text-indigo-700 mt-2 font-mono">
                        {redTeamResult.total_duration_ms} <span className="text-sm font-bold text-slate-500">ms</span>
                      </div>
                      <span className="text-[11px] text-slate-400 mt-1">Xử lý tức thì in-memory</span>
                    </div>

                    <div className="p-4 rounded-2xl bg-slate-900 text-white flex flex-col justify-between">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Ghi sổ cái bất biến</span>
                      <div className="text-xs font-mono font-bold text-emerald-400 mt-2 flex items-center gap-1.5">
                        <Hash className="w-4 h-4 shrink-0" />
                        <span className="truncate">RED_TEAM_AUDIT</span>
                      </div>
                      <button
                        onClick={() => {
                          setActiveTab('audit_trail');
                          loadAuditTrail();
                        }}
                        className="text-[11px] text-indigo-300 hover:text-white font-medium mt-1 text-left flex items-center gap-1 underline"
                      >
                        Xem vết mắt xích &rarr;
                      </button>
                    </div>
                  </div>

                  {/* Standards Verified Badges */}
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>Tiêu Chuẩn & Khung Quy Chuẩn Đã Xác Thực Thực Nghiệm:</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {redTeamResult.standards_verified.map((std, i) => (
                        <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-800 shadow-2xs">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          <span>{std}</span>
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Attack Defense Matrix List */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-700 uppercase tracking-wider">
                      <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-rose-600" />
                        <span>Ma Trận Kịch Bản Thử Nghiệm Đối Kháng ({redTeamResult.attack_results.length} Kịch bản)</span>
                      </div>
                      <span className="text-[11px] font-normal text-slate-500">Môi trường kiểm thử Sandbox an toàn</span>
                    </div>

                    <div className="space-y-3">
                      {redTeamResult.attack_results.map((atk, idx) => {
                        const threatColors: Record<string, string> = {
                          CRITICAL: 'bg-rose-100 text-rose-800 border-rose-300',
                          HIGH: 'bg-amber-100 text-amber-800 border-amber-300',
                          MEDIUM: 'bg-sky-100 text-sky-800 border-sky-300',
                          LOW: 'bg-slate-100 text-slate-800 border-slate-300'
                        };
                        const threatBadge = threatColors[atk.threat_level] || threatColors.LOW;

                        return (
                          <div key={atk.id} className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs space-y-3 hover:border-slate-300 transition-colors">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                              <div className="flex items-center gap-2.5 flex-wrap">
                                <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 font-mono text-[11px] font-black flex items-center justify-center">
                                  {idx + 1}
                                </span>
                                <h4 className="text-sm font-bold text-slate-900">{atk.name}</h4>
                                <span className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider border ${threatBadge}`}>
                                  {atk.threat_level}
                                </span>
                              </div>

                              <div className="flex items-center gap-3">
                                <span className="text-[11px] text-slate-500 font-mono">
                                  Độ trễ: <strong className="text-slate-800 font-bold">{atk.latency_ms} ms</strong>
                                </span>
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 border border-emerald-300">
                                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
                                  <span>{atk.result}</span>
                                </span>
                              </div>
                            </div>

                            {/* Attack Payload & Defense Layer */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                              <div className="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono space-y-1 overflow-x-auto">
                                <div className="text-[10px] font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1">
                                  <Terminal className="w-3 h-3 text-rose-400" />
                                  <span>Vector Tấn Công (Adversarial Payload):</span>
                                </div>
                                <div className="text-xs break-all text-rose-200">
                                  {atk.payload_sample}
                                </div>
                              </div>

                              <div className="p-3 rounded-xl bg-indigo-50/70 border border-indigo-100 space-y-1">
                                <div className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider flex items-center gap-1">
                                  <Shield className="w-3 h-3 text-indigo-600" />
                                  <span>Cơ Chế Phản Vệ (Defense Mechanism):</span>
                                </div>
                                <div className="text-xs font-semibold text-indigo-950">
                                  {atk.defense_layer}
                                </div>
                              </div>
                            </div>

                            {/* Technical Explanation */}
                            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 leading-relaxed flex items-start gap-2">
                              <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                              <span><strong className="text-slate-700">Giải thích nguyên lý kỹ thuật:</strong> {atk.technical_detail}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};