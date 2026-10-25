import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Plus,
  LayoutDashboard,
  FileText,
  Sparkles,
  Menu,
  X,
  Wifi,
  WifiOff,
  CloudUpload,
  HardDrive
} from 'lucide-react';
import { api } from '../api/client';
import { OfflineSyncModal } from './OfflineSyncModal';

interface Props {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Navbar: React.FC<Props> = ({ currentPath, onNavigate }) => {
  const [aiActive, setAiActive] = useState<boolean>(false);
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [pendingOutboxCount, setPendingOutboxCount] = useState<number>(0);
  const [showSyncModal, setShowSyncModal] = useState<boolean>(false);

  const calculatePendingCount = () => {
    try {
      let count = 0;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('datatrust_offline_outbox_')) {
          const raw = localStorage.getItem(key);
          if (raw) {
            const arr = JSON.parse(raw);
            if (Array.isArray(arr)) {
              count += arr.length;
            }
          }
        }
      }
      setPendingOutboxCount(count);
    } catch {
      setPendingOutboxCount(0);
    }
  };

  useEffect(() => {
    api.getAiStatus()
      .then((res) => setAiActive(res.ai_active))
      .catch(() => setAiActive(false));

    calculatePendingCount();

    const handleOnline = () => {
      setIsOnline(true);
      calculatePendingCount();
    };
    const handleOffline = () => {
      setIsOnline(false);
      calculatePendingCount();
    };
    const handleOutboxUpdate = () => {
      calculatePendingCount();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('storage', handleOutboxUpdate);
    window.addEventListener('datatrust_outbox_updated', handleOutboxUpdate);

    const interval = setInterval(calculatePendingCount, 4000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('storage', handleOutboxUpdate);
      window.removeEventListener('datatrust_outbox_updated', handleOutboxUpdate);
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    { label: 'Bảng điều khiển', path: '/', icon: LayoutDashboard },
    { label: 'Khảo sát của tôi', path: '/surveys', icon: FileText },
    { label: 'Tra cứu chứng thư', path: '/verify', icon: ShieldCheck }
  ];

  return (
    <>
      <nav className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div
              onClick={() => onNavigate('/')}
              className="flex items-center gap-2.5 cursor-pointer select-none group"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-200 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <span className="text-lg font-bold bg-gradient-to-r from-slate-900 to-indigo-900 bg-clip-text text-transparent">
                  DataTrust
                </span>
                <span className="block text-[10px] text-slate-500 font-medium tracking-tight -mt-0.5">
                  Survey & Quality Assurance
                </span>
              </div>
            </div>

            {/* Desktop Nav Items */}
            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPath === item.path;
                return (
                  <button
                    key={item.path}
                    onClick={() => onNavigate(item.path)}
                    className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 font-semibold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Right Action buttons */}
            <div className="hidden md:flex items-center gap-2.5">
              {/* Field Offline Sync & Connectivity Pill */}
              {!isOnline ? (
                <button
                  type="button"
                  onClick={() => setShowSyncModal(true)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-300 hover:bg-rose-100 transition-all shadow-2xs animate-pulse"
                  title="Thiết bị đang ngoại tuyến. Bấm để quản lý hàng đợi và sao lưu JSON an toàn."
                >
                  <WifiOff className="w-3.5 h-3.5 text-rose-600" />
                  <span>Ngoại tuyến {pendingOutboxCount > 0 ? `(${pendingOutboxCount})` : ''}</span>
                </button>
              ) : pendingOutboxCount > 0 ? (
                <button
                  type="button"
                  onClick={() => setShowSyncModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300 hover:bg-amber-100 transition-all shadow-2xs"
                  title="Có phiếu khảo sát thực địa đang chờ đồng bộ. Bấm để đồng bộ ngay."
                >
                  <CloudUpload className="w-3.5 h-3.5 text-amber-600 animate-bounce" />
                  <span>{pendingOutboxCount} chờ đồng bộ</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setShowSyncModal(true)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-slate-500 hover:text-slate-800 hover:bg-slate-100 border border-slate-200 transition-all"
                  title="Hàng đợi ngoại tuyến & Bộ đệm thực địa. Bấm để xem chi tiết."
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  <span className="hidden xl:inline text-[11px] text-slate-600 font-semibold">Trực tuyến</span>
                  <span className="text-[11px] text-slate-400">Bộ đệm</span>
                </button>
              )}

              {/* AI Status Pill */}
              <div
                title={aiActive ? "Gemini AI API đang hoạt động" : "Heuristic Deterministic Survey Engine đang hoạt động"}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                  aiActive
                    ? 'bg-violet-50 text-violet-700 border-violet-200'
                    : 'bg-slate-100 text-slate-600 border-slate-200'
                }`}
              >
                <Sparkles className={`w-3.5 h-3.5 ${aiActive ? 'text-violet-600 animate-pulse' : 'text-slate-500'}`} />
                <span>{aiActive ? 'Gemini AI Active' : 'Heuristic Engine'}</span>
              </div>

              {/* Create Survey Button */}
              <button
                onClick={() => onNavigate('/surveys/new')}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm hover:shadow-md transition-all active:scale-98"
              >
                <Plus className="w-4 h-4" />
                <span>Tạo khảo sát</span>
              </button>
            </div>

            {/* Mobile hamburger */}
            <div className="flex md:hidden items-center gap-2">
              {/* Mobile offline/sync badge shortcut */}
              {(!isOnline || pendingOutboxCount > 0) && (
                <button
                  type="button"
                  onClick={() => setShowSyncModal(true)}
                  className={`p-1.5 rounded-lg text-xs font-bold flex items-center gap-1 ${
                    !isOnline ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-800'
                  }`}
                  aria-label="Quản lý đồng bộ ngoại tuyến"
                >
                  {!isOnline ? <WifiOff className="w-4 h-4" /> : <CloudUpload className="w-4 h-4" />}
                  {pendingOutboxCount > 0 && <span>{pendingOutboxCount}</span>}
                </button>
              )}

              <button
                onClick={() => setMobileOpen(!mobileOpen)}
                aria-label="Mở menu"
                className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
              >
                {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Drawer */}
        {mobileOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPath === item.path;
              return (
                <button
                  key={item.path}
                  onClick={() => {
                    onNavigate(item.path);
                    setMobileOpen(false);
                  }}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium ${
                    isActive ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}

            {/* Mobile Offline Sync button */}
            <button
              onClick={() => {
                setShowSyncModal(true);
                setMobileOpen(false);
              }}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium bg-slate-50 text-slate-700 border border-slate-200"
            >
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-indigo-600" />
                <span>Bộ đệm thực địa &amp; Ngoại tuyến</span>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                !isOnline ? 'bg-rose-100 text-rose-700' :
                pendingOutboxCount > 0 ? 'bg-amber-100 text-amber-800' :
                'bg-emerald-100 text-emerald-800'
              }`}>
                {!isOnline ? 'Ngoại tuyến' : `${pendingOutboxCount} chờ gửi`}
              </span>
            </button>

            <button
              onClick={() => {
                onNavigate('/surveys/new');
                setMobileOpen(false);
              }}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Tạo khảo sát mới</span>
            </button>
          </div>
        )}
      </nav>

      {/* Offline Sync & Outbox Management Modal */}
      <OfflineSyncModal
        isOpen={showSyncModal}
        onClose={() => setShowSyncModal(false)}
        onSyncComplete={() => calculatePendingCount()}
      />
    </>
  );
};
