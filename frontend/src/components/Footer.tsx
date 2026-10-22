import React from 'react';
import { ShieldCheck, Database, Award } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-slate-200/80 bg-white py-8 text-slate-500 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-indigo-600" />
          <span className="font-semibold text-slate-800">DataTrust AI Platform</span>
          <span>•</span>
          <span>Hệ thống tạo khảo sát và sàng lọc dữ liệu bất thường</span>
        </div>

        <div className="flex items-center gap-6 text-slate-500">
          <span className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span>SQLite WAL Storage</span>
          </span>
          <span className="flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-emerald-500" />
            <span>Zero-Fabrication Integrity</span>
          </span>
          <span>v1.0.0 Production</span>
        </div>
      </div>
    </footer>
  );
};
