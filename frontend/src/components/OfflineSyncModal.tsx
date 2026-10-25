import React, { useEffect, useState } from 'react';
import {
  X,
  Wifi,
  WifiOff,
  CloudUpload,
  Download,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  Layers,
  FileText,
  ShieldCheck,
  HardDrive
} from 'lucide-react';
import { api } from '../api/client';

interface OutboxGroup {
  slug: string;
  items: any[];
  earliestTime?: string;
  latestTime?: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSyncComplete?: () => void;
}

export const OfflineSyncModal: React.FC<Props> = ({ isOpen, onClose, onSyncComplete }) => {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [outboxGroups, setOutboxGroups] = useState<OutboxGroup[]>([]);
  const [totalDrafts, setTotalDrafts] = useState<number>(0);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncStatusMsg, setSyncStatusMsg] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  const scanLocalStorage = () => {
    try {
      const groups: OutboxGroup[] = [];
      let draftsCount = 0;

      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (!key) continue;

        if (key.startsWith('datatrust_offline_outbox_')) {
          const slug = key.replace('datatrust_offline_outbox_', '');
          try {
            const raw = localStorage.getItem(key);
            const parsed = raw ? JSON.parse(raw) : [];
            if (Array.isArray(parsed) && parsed.length > 0) {
              const timestamps = parsed
                .map((item: any) => item.submitted_at)
                .filter(Boolean)
                .sort();

              groups.push({
                slug,
                items: parsed,
                earliestTime: timestamps[0],
                latestTime: timestamps[timestamps.length - 1]
              });
            }
          } catch (e) {
            console.error('Error parsing outbox key:', key, e);
          }
        } else if (key.startsWith('datatrust_draft_')) {
          draftsCount++;
        }
      }

      setOutboxGroups(groups);
      setTotalDrafts(draftsCount);
    } catch (err) {
      console.error('Error scanning local storage:', err);
    }
  };

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    const handleOutboxUpdated = () => scanLocalStorage();

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('storage', handleOutboxUpdated);
    window.addEventListener('datatrust_outbox_updated', handleOutboxUpdated);

    if (isOpen) {
      scanLocalStorage();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('storage', handleOutboxUpdated);
      window.removeEventListener('datatrust_outbox_updated', handleOutboxUpdated);
    };
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const totalPendingResponses = outboxGroups.reduce((acc, g) => acc + g.items.length, 0);

  const handleSyncAll = async () => {
    if (!navigator.onLine) {
      setSyncStatusMsg({
        type: 'error',
        text: 'Thiết bị vẫn đang ngoại tuyến. Vui lòng kết nối Internet (WiFi / 4G) để đồng bộ dữ liệu.'
      });
      return;
    }

    if (totalPendingResponses === 0) {
      setSyncStatusMsg({
        type: 'info',
        text: 'Hàng đợi ngoại tuyến đang trống. Tất cả dữ liệu đã được bảo toàn trên máy chủ.'
      });
      return;
    }

    setIsSyncing(true);
    setSyncStatusMsg(null);

    let totalSynced = 0;
    let totalDuplicatesSkipped = 0;
    let errorsCount = 0;

    for (const group of outboxGroups) {
      const outboxKey = `datatrust_offline_outbox_${group.slug}`;
      try {
        const res = await api.batchSyncPublicResponses(group.slug, group.items);
        if (res.success) {
          totalSynced += res.synced_count;
          totalDuplicatesSkipped += res.duplicates_skipped;

          // Remove processed items
          const processedUuids = new Set<string>();
          for (const item of res.results) {
            if ((item.status === 'synced' || item.status === 'skipped_duplicate') && item.client_uuid) {
              processedUuids.add(item.client_uuid);
            }
          }

          const remaining = group.items.filter((item: any) => item.client_uuid && !processedUuids.has(item.client_uuid));
          if (remaining.length > 0) {
            localStorage.setItem(outboxKey, JSON.stringify(remaining));
          } else {
            localStorage.removeItem(outboxKey);
          }
        }
      } catch (err) {
        console.error(`Failed to sync group ${group.slug}:`, err);
        errorsCount++;
      }
    }

    scanLocalStorage();
    window.dispatchEvent(new Event('datatrust_outbox_updated'));
    setIsSyncing(false);

    if (errorsCount === 0) {
      setSyncStatusMsg({
        type: 'success',
        text: `Đồng bộ thành công ${totalSynced} phiếu khảo sát thực địa! (Đối soát bỏ qua ${totalDuplicatesSkipped} phiếu trùng lặp).`
      });
      if (onSyncComplete) onSyncComplete();
    } else {
      setSyncStatusMsg({
        type: 'error',
        text: `Đã đồng bộ ${totalSynced} phiếu, tuy nhiên có ${errorsCount} khảo sát gặp lỗi đường truyền. Các phiếu còn lại vẫn được lưu an toàn.`
      });
    }
  };

  const handleExportBackupJson = () => {
    const backupData = {
      app: 'DataTrust',
      exported_at: new Date().toISOString(),
      user_agent: navigator.userAgent,
      total_pending_surveys: outboxGroups.length,
      total_pending_responses: totalPendingResponses,
      outboxes: outboxGroups
    };

    const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `datatrust_outbox_backup_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClearAllOutbox = () => {
    if (window.confirm('CẢNH BÁO: Bạn có chắc chắn muốn xóa toàn bộ hàng đợi ngoại tuyến trên thiết bị này? Thao tác này chỉ nên thực hiện sau khi đã xuất tệp dự phòng JSON.')) {
      for (const group of outboxGroups) {
        localStorage.removeItem(`datatrust_offline_outbox_${group.slug}`);
      }
      scanLocalStorage();
      window.dispatchEvent(new Event('datatrust_outbox_updated'));
      setSyncStatusMsg({
        type: 'info',
        text: 'Đã dọn sạch hàng đợi ngoại tuyến trên thiết bị.'
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="offline-sync-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div
        className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h2 id="offline-sync-modal-title" className="text-base font-bold text-slate-900">
                Quản Lý Đồng Bộ Ngoại Tuyến Thực Địa
              </h2>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                  isOnline ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800 animate-pulse'
                }`}>
                  {isOnline ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                  {isOnline ? 'Đang có kết nối Internet' : 'Thiết bị đang Ngoại tuyến'}
                </span>
                <span className="text-slate-400 text-xs">• Don Dillman Continuity Standard</span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng cửa sổ"
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors focus:ring-2 focus:ring-indigo-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Status Alert Banner */}
          {syncStatusMsg && (
            <div className={`p-4 rounded-xl text-xs flex items-start gap-2.5 ${
              syncStatusMsg.type === 'success' ? 'bg-emerald-50 text-emerald-900 border border-emerald-200' :
              syncStatusMsg.type === 'error' ? 'bg-rose-50 text-rose-900 border border-rose-200' :
              'bg-indigo-50 text-indigo-900 border border-indigo-200'
            }`}>
              {syncStatusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /> :
               syncStatusMsg.type === 'error' ? <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" /> :
               <ShieldCheck className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />}
              <span className="font-medium leading-relaxed">{syncStatusMsg.text}</span>
            </div>
          )}

          {/* KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold text-slate-500 block">Phiếu chờ đồng bộ</span>
              <div className="flex items-baseline gap-1.5 mt-1">
                <span className="text-2xl font-extrabold text-indigo-600">{totalPendingResponses}</span>
                <span className="text-xs text-slate-500 font-medium">phiếu</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold text-slate-500 block">Khảo sát có hàng đợi</span>
              <div className="flex items-baseline gap-1.5 mt-1">
                <span className="text-2xl font-extrabold text-slate-900">{outboxGroups.length}</span>
                <span className="text-xs text-slate-500 font-medium">khảo sát</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold text-slate-500 block">Bản nháp đang điền dở</span>
              <div className="flex items-baseline gap-1.5 mt-1">
                <span className="text-2xl font-extrabold text-amber-600">{totalDrafts}</span>
                <span className="text-xs text-slate-500 font-medium">bản nháp</span>
              </div>
            </div>
          </div>

          {/* Outbox List Breakdown */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              Chi Tiết Hàng Đợi Từng Khảo Sát
            </h3>

            {outboxGroups.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                <p className="text-xs font-semibold text-slate-800">Không có phiếu khảo sát nào đang chờ gửi</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Mọi phản hồi thu thập thực địa trên thiết bị này đều đã được đồng bộ an toàn lên máy chủ.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {outboxGroups.map((group) => (
                  <div
                    key={group.slug}
                    className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-slate-900 font-mono">
                          /s/{group.slug}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700">
                          {group.items.length} phiếu chờ
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px] text-slate-400">
                        {group.earliestTime && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-400" />
                            Thu thập từ: {new Date(group.earliestTime).toLocaleTimeString('vi-VN')}
                          </span>
                        )}
                        {group.latestTime && (
                          <span>
                            đến {new Date(group.latestTime).toLocaleTimeString('vi-VN')}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-auto">
                      <span className="text-[11px] text-slate-500 font-medium">
                        Cơ chế: Idempotent Atomic Batch
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Scientific Field Resilience Note */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-[11px] text-slate-600 leading-relaxed space-y-1">
            <span className="font-bold text-slate-800 block">Bảo toàn dữ liệu điều tra thực địa (AAPOR &amp; Dillman):</span>
            <p>
              Dữ liệu được lưu trữ trên LocalStorage theo mã định danh duy nhất (UUID) của từng phiếu.
              Khi thiết bị kết nối mạng trở lại, API Atomic Batch Sync sẽ tự động đối soát tránh trùng lặp bản ghi ngay cả khi đường truyền bị ngắt giữa chừng.
            </p>
          </div>
        </div>

        {/* Modal Footer Controls */}
        <div className="p-5 border-t border-slate-100 bg-slate-50/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleExportBackupJson}
              disabled={totalPendingResponses === 0}
              className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-2xs"
              title="Xuất tệp JSON dự phòng trước khi xóa hoặc sao lưu"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Sao lưu JSON</span>
            </button>

            {totalPendingResponses > 0 && (
              <button
                type="button"
                onClick={handleClearAllOutbox}
                className="flex items-center justify-center p-2 rounded-xl text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-colors"
                title="Xóa hàng đợi ngoại tuyến"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-200/70 transition-colors"
            >
              Đóng
            </button>

            <button
              type="button"
              onClick={handleSyncAll}
              disabled={isSyncing || totalPendingResponses === 0 || !isOnline}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm active:scale-98"
            >
              {isSyncing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Đang đồng bộ...</span>
                </>
              ) : (
                <>
                  <CloudUpload className="w-4 h-4" />
                  <span>Đồng bộ tất cả ngay ({totalPendingResponses})</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
