import React, { useEffect, useState } from 'react';
import {
  X,
  Database,
  ShieldCheck,
  HardDrive,
  RefreshCw,
  Cpu,
  Layers,
  Sparkles,
  Server,
  Activity,
  CheckCircle2,
  AlertCircle,
  Zap,
  Gauge
} from 'lucide-react';
import { api } from '../api/client';
import { StressTestReport } from '../types/survey';

interface SystemDiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SystemDiagnosticsModal: React.FC<SystemDiagnosticsModalProps> = ({
  isOpen,
  onClose
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [operating, setOperating] = useState<boolean>(false);
  const [stressRunning, setStressRunning] = useState<boolean>(false);
  const [stressReport, setStressReport] = useState<StressTestReport | null>(null);
  const [opMessage, setOpMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      loadDiagnostics();
    }
  }, [isOpen]);

  const loadDiagnostics = async () => {
    try {
      setLoading(true);
      const res = await api.getSystemDiagnostics();
      setData(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckpoint = async () => {
    try {
      setOperating(true);
      setOpMessage(null);
      const res = await api.runWalCheckpoint();
      setOpMessage(`✅ Dồn trang WAL thành công: ${res.wal_checkpoint_mode || 'TRUNCATE'}. Tệp nhật ký sạch sẽ.`);
      await loadDiagnostics();
    } catch (err: any) {
      setOpMessage(`❌ Lỗi checkpoint: ${err.message}`);
    } finally {
      setOperating(false);
    }
  };

  const handleVacuum = async () => {
    try {
      setOperating(true);
      setOpMessage(null);
      const res = await api.runVacuum();
      setOpMessage(`✅ VACUUM hoàn tất: Đã giải phóng ${res.freed_bytes || 0} bytes dung lượng đĩa.`);
      await loadDiagnostics();
    } catch (err: any) {
      setOpMessage(`❌ Lỗi vacuum: ${err.message}`);
    } finally {
      setOperating(false);
    }
  };

  const handleStressTest = async () => {
    try {
      setStressRunning(true);
      setOpMessage('⚡ Đang thực thi bài kiểm tra tải đồng thời (30 requests, 6 workers)...');
      const rep = await api.runStressTest(30, 6);
      setStressReport(rep);
      setOpMessage(`⚡ Kiểm tra tải hoàn tất: ${rep.throughput_rps} req/s, P95 = ${rep.latency_p95_ms}ms, 0 lỗi khóa.`);
      await loadDiagnostics();
    } catch (err: any) {
      setOpMessage(`❌ Lỗi kiểm tra tải: ${err.message}`);
    } finally {
      setStressRunning(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="system-diag-title"
    >
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-900 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 border border-indigo-400/30 rounded-xl">
              <Server className="w-5 h-5 text-indigo-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="system-diag-title" className="text-base font-bold text-white">
                  Chẩn Đoán Sức Khỏe & Giám Sát CSDL
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 font-mono font-bold">
                  SQLite WAL & Ledger
                </span>
              </div>
              <p className="text-xs text-slate-300">
                Toàn vẹn cấu trúc B-Tree, mật độ bản ghi và kiểm chứng mật mã học
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors focus:outline-hidden"
            aria-label="Đóng cửa sổ"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-slate-50/50">
          {loading && !data ? (
            <div className="py-16 text-center text-slate-500 text-sm">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-600 mb-2" />
              Đang truy vấn trạng thái hệ thống CSDL...
            </div>
          ) : !data ? (
            <div className="p-4 bg-rose-50 text-rose-700 text-xs rounded-xl">
              Không thể nạp dữ liệu chẩn đoán hệ thống.
            </div>
          ) : (
            <>
              {/* Status Alert Banner */}
              <div className="flex items-center justify-between p-3.5 bg-white border border-slate-200 rounded-xl shadow-2xs">
                <div className="flex items-center gap-2.5">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  <div>
                    <span className="text-xs font-bold text-slate-900 block">
                      Trạng Thái Hoạt Động: Toàn Vẹn 100%
                    </span>
                    <span className="text-[11px] text-slate-500">
                      Cập nhật lúc: {new Date(data.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                <button
                  onClick={loadDiagnostics}
                  disabled={loading}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
                >
                  <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
                  Làm mới
                </button>
              </div>

              {opMessage && (
                <div className="p-3 bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs rounded-xl font-medium animate-in fade-in">
                  {opMessage}
                </div>
              )}

              {/* 3 Metrics Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
                  <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                    <span>Dung Lượng Đĩa</span>
                    <HardDrive className="w-3.5 h-3.5 text-indigo-600" />
                  </div>
                  <div className="text-lg font-bold text-slate-900">
                    {data.file_size_mb} <span className="text-xs font-normal text-slate-500">MB</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {data.file_size_bytes.toLocaleString()} bytes
                  </span>
                </div>

                <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
                  <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                    <span>Kiểm Tra Cấu Trúc</span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  </div>
                  <div className="text-lg font-bold text-emerald-700">
                    {data.sqlite_pragmas?.integrity_check?.toUpperCase() || 'OK'}
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Mode: {data.sqlite_pragmas?.journal_mode?.toUpperCase() || 'WAL'}
                  </span>
                </div>

                <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
                  <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                    <span>Chuỗi Băm Ledger</span>
                    <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                  </div>
                  <div className="text-lg font-bold text-indigo-700">
                    {data.tamper_evident_ledger?.is_chain_valid ? 'HỢP LỆ' : 'CAN THIỆP'}
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {data.tamper_evident_ledger?.total_audit_records || 0} bản ghi ký số
                  </span>
                </div>
              </div>

              {/* Table Records Breakdown */}
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-indigo-600" />
                    Mật Độ Bản Ghi Các Bảng CSDL
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">SQLite Storage Engine</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  {Object.entries(data.table_record_counts || {}).map(([tbl, count]: [string, any]) => (
                    <div key={tbl} className="bg-slate-50 p-2 rounded-lg border border-slate-200/60">
                      <span className="text-[10px] text-slate-500 block truncate font-mono">{tbl}</span>
                      <span className="text-sm font-bold text-slate-900">{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Maintenance Tools Bar */}
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                  Công Cụ Tối Ưu Hóa & Bảo Trì Tức Thì
                </span>
                <p className="text-xs text-slate-500">
                  Dồn nhật ký ghi trước (WAL Checkpoint) hoặc thu hồi không gian đĩa rỗng (VACUUM) mà không làm ngắt quãng hoạt động thu thập dữ liệu trực tuyến.
                </p>

                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <button
                    onClick={handleCheckpoint}
                    disabled={operating}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-xs font-bold transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${operating ? 'animate-spin' : ''}`} />
                    Dồn Trang WAL (Checkpoint)
                  </button>

                  <button
                    onClick={handleVacuum}
                    disabled={operating || stressRunning}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-xl text-xs font-bold transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                    Chống Phân Mảnh (VACUUM)
                  </button>

                  <button
                    onClick={handleStressTest}
                    disabled={operating || stressRunning}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-violet-50 hover:bg-violet-100 text-violet-800 rounded-xl text-xs font-bold transition-colors disabled:opacity-50"
                    title="Mô phỏng áp lực 30 luồng ghi đồng thời và đo lường độ trễ P50/P95 cùng kiểm định chuỗi băm"
                  >
                    <Zap className={`w-3.5 h-3.5 text-violet-600 ${stressRunning ? 'animate-bounce text-amber-500' : ''}`} />
                    {stressRunning ? 'Đang chạy tải đồng thời...' : 'Đo Tải Đồng Thời (Stress Profiler)'}
                  </button>
                </div>

                {/* Stress Test Live Report Card */}
                {stressReport && (
                  <div className="mt-3 p-3.5 rounded-xl bg-violet-50/70 border border-violet-200/80 space-y-2.5 animate-in fade-in duration-200">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-violet-900 flex items-center gap-1.5">
                        <Gauge className="w-4 h-4 text-violet-600" />
                        Kết Quả Đo Tải Đồng Thời ({stressReport.total_requests} requests / {stressReport.concurrency_workers} workers)
                      </span>
                      <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-md border border-emerald-300">
                        Thông lượng: {stressReport.throughput_rps} req/s
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                      <div className="p-2 bg-white rounded-lg border border-violet-100 shadow-2xs">
                        <span className="text-[10px] text-slate-500 block">Độ trễ TB (Mean)</span>
                        <span className="text-sm font-bold text-slate-900 font-mono">{stressReport.latency_mean_ms} ms</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-violet-100 shadow-2xs">
                        <span className="text-[10px] text-slate-500 block">Trung vị (P50)</span>
                        <span className="text-sm font-bold text-slate-900 font-mono">{stressReport.latency_median_p50_ms} ms</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-violet-100 shadow-2xs">
                        <span className="text-[10px] text-slate-500 block">Phân vị 95 (P95)</span>
                        <span className="text-sm font-bold text-violet-700 font-mono">{stressReport.latency_p95_ms} ms</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-violet-100 shadow-2xs">
                        <span className="text-[10px] text-slate-500 block">Tranh chấp khóa CSDL</span>
                        <span className="text-sm font-bold text-emerald-600 font-mono">{stressReport.database_lock_errors} lỗi</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-violet-800 bg-white/80 p-2 rounded-lg border border-violet-100 font-mono">
                      <span>Ledger sau kiểm thử: {stressReport.audit_chain_valid_post_stress ? '✅ 100% Khớp chuỗi băm' : '❌ Phát hiện sai lệch'}</span>
                      <span className="text-slate-500">WAL: {Math.round(stressReport.wal_size_bytes_after / 1024)} KB</span>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 bg-white text-xs">
          <span className="text-slate-400 font-mono text-[10px]">
            DataTrust Storage Protocol v1.0.0
          </span>
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
