import React, { useEffect, useState } from 'react';
import { ShieldCheck, Plus, LayoutDashboard, FileText, Sparkles, Menu, X } from 'lucide-react';
import { api } from '../api/client';

interface Props {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Navbar: React.FC<Props> = ({ currentPath, onNavigate }) => {
  const [aiActive, setAiActive] = useState<boolean>(false);
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);

  useEffect(() => {
    api.getAiStatus()
      .then((res) => setAiActive(res.ai_active))
      .catch(() => setAiActive(false));
  }, []);

  const navItems = [
    { label: 'Bảng điều khiển', path: '/', icon: LayoutDashboard },
    { label: 'Khảo sát của tôi', path: '/surveys', icon: FileText }
  ];

  return (
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
                DataTrust <span className="text-indigo-600 font-extrabold">AI</span>
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
          <div className="hidden md:flex items-center gap-3">
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
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
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
  );
};
