import React from 'react';
import { CircleDot, CheckCircle2, Lock, Archive } from 'lucide-react';

interface Props {
  status: 'draft' | 'published' | 'closed' | 'archived';
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  switch (status) {
    case 'published':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          Đang nhận phản hồi
        </span>
      );
    case 'closed':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-300">
          <Lock className="w-3 h-3 text-slate-500" />
          Đã kết thúc
        </span>
      );
    case 'archived':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-300">
          <Archive className="w-3 h-3 text-gray-500" />
          Đã lưu trữ
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
          <CircleDot className="w-3 h-3 text-blue-500" />
          Bản nháp
        </span>
      );
  }
};
