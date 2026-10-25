import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { PublicCertificateVerification } from '../types/survey';

interface Props {
  initialQuery?: string;
  onNavigate: (path: string) => void;
}

export const PublicCertificateVerifyPage: React.FC<Props> = ({ initialQuery = '', onNavigate }) => {
  const [queryInput, setQueryInput] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PublicCertificateVerification | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const performVerification = async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) {
      setError('Vui lòng nhập mã chứng thư, Survey ID, Slug hoặc mã băm SHA-256.');
      return;
    }
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const res = await api.verifyCertificate(trimmed);
      setData(res);
      // Cập nhật URL nếu cần thiết
      if (window.location.pathname !== `/verify/${trimmed}`) {
        window.history.replaceState({}, '', `/verify/${encodeURIComponent(trimmed)}`);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể xác minh chứng thư hoặc mã truy vấn không tồn tại.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      performVerification(initialQuery);
    }
  }, [initialQuery]);

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(label);
    setTimeout(() => setCopiedHash(null), 2500);
  };

  const handleCopyProof = () => {
    if (!data) return;
    const proofText = `=== DATATRUST DATA INTEGRITY CRYPTOGRAPHIC PROOF ===
Certificate ID : ${data.certificate_id}
Survey Title   : ${data.survey_title}
Survey ID      : ${data.survey_id}
Status         : ${data.status} (Valid: ${data.is_valid})
Issued At      : ${data.issued_at}
Trust Index    : ${data.trust_index}% (Clean: ${data.clean_responses}/${data.total_responses})
Cronbach Alpha : ${data.cronbach_alpha !== null && data.cronbach_alpha !== undefined ? data.cronbach_alpha.toFixed(3) : 'N/A'}
Ledger Head    : ${data.ledger_head_hash || 'N/A'}
Ledger Genesis : ${data.ledger_genesis_hash || 'N/A'}
Total Records  : ${data.total_audit_events} events
Verification URL: ${window.location.origin}/verify/${data.certificate_id}
Authority      : DataTrust Independent Verification Engine
Standards      : AAPOR (2016), US OMB (2006), Decree 356/2025/ND-CP
===================================================`;
    navigator.clipboard.writeText(proofText);
    setCopiedHash('proof');
    setTimeout(() => setCopiedHash(null), 2500);
  };

  const handleDownloadJson = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `datatrust_verification_${data.certificate_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Decorative background glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950/40 via-slate-950 to-slate-950 pointer-events-none" />

      {/* Main Container */}
      <div className="relative max-w-5xl mx-auto px-4 py-8 sm:py-12 flex-1 w-full">
        {/* Navigation Breadcrumb / Brand Bar */}
        <div className="flex items-center justify-between pb-6 border-b border-slate-800/80 mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/25 ring-1 ring-indigo-400/40">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                DataTrust <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold tracking-normal uppercase">Cổng Thẩm Định Công Khai</span>
              </h1>
              <p className="text-xs text-slate-400">Hệ thống Tra cứu Chứng chỉ & Xác thực Sổ cái Mật mã học Độc lập</p>
            </div>
          </div>

          <button
            onClick={() => onNavigate('/')}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/60"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Về Không Gian Quản Trị
          </button>
        </div>

        {/* Hero Section & Search Form */}
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-xs font-medium mb-3">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Xác thực Chuỗi Băm SHA-256 Light-Ledger Theo Thời Gian Thực
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Kiểm Chứng Tính Toàn Vẹn & Nguồn Gốc Dữ Liệu
          </h2>
          <p className="text-sm text-slate-400 mt-2">
            Dành cho Hội đồng Giám khảo (KHKT/ViSEF/ISEF), Ban Biên tập Tạp chí Khoa học và Chuyên gia thẩm định độc lập đối soát chữ ký điện tử.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              performVerification(queryInput);
            }}
            className="mt-6 flex flex-col sm:flex-row gap-2.5 justify-center"
          >
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="Nhập mã chứng thư (DT-CERT-2026-...), Survey ID, hoặc SHA-256 Hash..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-mono shadow-inner"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 flex-shrink-0"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Đang Thẩm Định...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Kiểm Tra Ngay
                </>
              )}
            </button>
          </form>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-rose-950/40 border border-rose-800/80 rounded-2xl p-5 mb-8 text-rose-200 flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-rose-900/60 flex items-center justify-center flex-shrink-0 text-rose-400">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-sm text-rose-300">Không Thể Xác Thực Chứng Thư</h3>
              <p className="text-xs text-rose-200/80 mt-1">{error}</p>
              <div className="mt-3 text-xs text-slate-400">
                Gợi ý: Kiểm tra lại mã chứng chỉ ghi trên bản in (dạng <code>DT-CERT-2026-XXXXXXXX</code>) hoặc quét trực tiếp mã QR ở chân chứng thư.
              </div>
            </div>
          </div>
        )}

        {/* Verified Result Card */}
        {data && (
          <div className="space-y-6">
            {/* Top Status Banner */}
            <div className={`p-6 rounded-2xl border ${data.is_valid ? 'bg-emerald-950/20 border-emerald-500/40' : 'bg-rose-950/30 border-rose-500/50'} relative overflow-hidden backdrop-blur-sm shadow-2xl`}>
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg ${data.is_valid ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/30 shadow-emerald-500/20' : 'bg-rose-500/10 text-rose-400 ring-1 ring-rose-500/30 shadow-rose-500/20'}`}>
                    {data.is_valid ? (
                      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    ) : (
                      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${data.is_valid ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'}`}>
                        {data.is_valid ? 'HỢP LỆ & TOÀN VẸN (CRYPTOGRAPHICALLY VERIFIED)' : 'CẢNH BÁO: PHÁT HIỆN SỰ THAY ĐỔI TRÁI PHÉP'}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-white mt-1">
                      Chứng Thư #{data.certificate_id}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {data.verification_verdict}
                    </p>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <a
                    href={data.printable_certificate_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 sm:flex-none px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors border border-slate-700 flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                    </svg>
                    Bản In A4
                  </a>
                  <button
                    onClick={handleCopyProof}
                    className="flex-1 sm:flex-none px-3.5 py-2 rounded-xl bg-indigo-600/80 hover:bg-indigo-600 text-xs font-semibold text-white transition-colors border border-indigo-500/30 flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                    {copiedHash === 'proof' ? 'Đã Sao Chép!' : 'Sao Chép Bằng Chứng'}
                  </button>
                  <button
                    onClick={handleDownloadJson}
                    className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors border border-slate-700"
                    title="Tải tệp JSON chứng chỉ"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Grid 2 Columns: Survey Metadata & Statistical Quality */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1: Survey Metadata */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-500" />
                    Hồ Sơ Nghiên Cứu Khảo Sát
                  </h4>
                  <span className="text-xs font-mono text-slate-400">v{data.certificate_id.split('-').pop()}</span>
                </div>
                <div className="mt-4 space-y-3 text-xs">
                  <div>
                    <span className="text-slate-400">Tiêu đề đề tài:</span>
                    <div className="font-semibold text-white text-sm mt-0.5">{data.survey_title}</div>
                  </div>
                  {data.survey_description && (
                    <div>
                      <span className="text-slate-400">Mô tả mục tiêu:</span>
                      <div className="text-slate-300 mt-0.5 line-clamp-2">{data.survey_description}</div>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div>
                      <span className="text-slate-400">Thời điểm chứng thực:</span>
                      <div className="text-slate-200 font-mono mt-0.5">{new Date(data.issued_at).toLocaleString('vi-VN')}</div>
                    </div>
                    <div>
                      <span className="text-slate-400">Đường dẫn làm bài:</span>
                      <div className="text-indigo-400 font-mono mt-0.5">/s/{data.public_slug || data.survey_id.slice(0, 8)}</div>
                    </div>
                  </div>
                  <div className="pt-2">
                    <span className="text-slate-400">Survey UUID:</span>
                    <div className="font-mono text-slate-300 bg-slate-950/80 p-2 rounded-lg border border-slate-800 mt-1 select-all break-all text-[11px]">
                      {data.survey_id}
                    </div>
                  </div>
                </div>
              </div>

              {/* Card 2: Scientific Quality Metrics */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg backdrop-blur-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      Chỉ Số Thẩm Định Lượng & Độ Tin Cậy
                    </h4>
                    <span className="text-xs font-bold text-emerald-400">{data.trust_index}% Mẫu Sạch</span>
                  </div>

                  {/* Trust Index Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-slate-400">Chỉ số Tin cậy Dữ liệu (Research Trust Index):</span>
                      <span className="font-bold text-white font-mono">{data.trust_index}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden p-0.5 ring-1 ring-slate-700">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-emerald-400 to-emerald-500 transition-all duration-1000 shadow-sm"
                        style={{ width: `${Math.min(100, Math.max(0, data.trust_index))}%` }}
                      />
                    </div>
                  </div>

                  {/* 3 Metric counters */}
                  <div className="grid grid-cols-3 gap-2 mt-5 text-center">
                    <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Quy Mô Mẫu (N)</div>
                      <div className="text-lg font-extrabold text-white font-mono mt-0.5">{data.total_responses}</div>
                    </div>
                    <div className="bg-emerald-950/20 p-3 rounded-xl border border-emerald-500/20">
                      <div className="text-[10px] text-emerald-400 uppercase font-semibold">Mẫu Hợp Lệ</div>
                      <div className="text-lg font-extrabold text-emerald-300 font-mono mt-0.5">{data.clean_responses}</div>
                    </div>
                    <div className="bg-rose-950/20 p-3 rounded-xl border border-rose-500/20">
                      <div className="text-[10px] text-rose-400 uppercase font-semibold">Mẫu Loại Trừ</div>
                      <div className="text-lg font-extrabold text-rose-300 font-mono mt-0.5">{data.excluded_responses}</div>
                    </div>
                  </div>
                </div>

                {/* Cronbach's Alpha Badge */}
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-300">Cronbach's Alpha (α):</span>
                    <span className="font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {data.cronbach_alpha !== null && data.cronbach_alpha !== undefined ? data.cronbach_alpha.toFixed(3) : 'Chưa áp dụng'}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 italic">
                    {data.reliability_verdict || 'Cần ≥ 2 câu hỏi thang đo'}
                  </span>
                </div>
              </div>
            </div>

            {/* Cryptographic Ledger Tamper-Evident Proof */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  Chứng Minh Mật Mã Học Chuỗi Khối Nhẹ (Lightweight Blockchain Ledger)
                </h4>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Tổng sự kiện bảo vệ:</span>
                  <span className="font-mono font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                    {data.total_audit_events} Bản ghi liên kết bất biến
                  </span>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {/* Head Hash */}
                <div>
                  <div className="flex justify-between items-center text-xs mb-1">
                    <span className="text-slate-400 font-semibold flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Mã Băm Đỉnh Chuỗi (Head Hash - Top of Merkle Chain):
                    </span>
                    <button
                      onClick={() => handleCopy(data.ledger_head_hash || '', 'head')}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                    >
                      {copiedHash === 'head' ? 'Đã chép!' : 'Sao chép'}
                    </button>
                  </div>
                  <div className="bg-slate-950/90 font-mono text-emerald-400 p-2.5 rounded-xl border border-slate-800 text-xs break-all select-all">
                    {data.ledger_head_hash || 'GENESIS_ROOT_0000000000000000000000000000000000000000000000000000000000000000'}
                  </div>
                </div>

                {/* Genesis Hash */}
                <div>
                  <div className="flex justify-between items-center text-xs mb-1">
                    <span className="text-slate-400 font-semibold flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                      Mã Băm Khởi Nguyên (Genesis Hash):
                    </span>
                    <button
                      onClick={() => handleCopy(data.ledger_genesis_hash || '', 'genesis')}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                    >
                      {copiedHash === 'genesis' ? 'Đã chép!' : 'Sao chép'}
                    </button>
                  </div>
                  <div className="bg-slate-950/90 font-mono text-indigo-300 p-2.5 rounded-xl border border-slate-800 text-xs break-all select-all">
                    {data.ledger_genesis_hash || '0000000000000000000000000000000000000000000000000000000000000000'}
                  </div>
                </div>
              </div>
            </div>

            {/* Compliance & Legal Declarations */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                Chuẩn Mực Khoa Học & Khung Pháp Lý Thẩm Định
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {data.compliance_standards.map((std, idx) => (
                  <div key={idx} className="flex items-start gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 text-xs text-slate-300">
                    <svg className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>{std}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
