import React from 'react';
import { ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

interface Props {
  score: number;
  level?: 'low' | 'medium' | 'high';
  showLabel?: boolean;
}

export const RiskBadge: React.FC<Props> = ({ score, level, showLabel = true }) => {
  const effectiveLevel = level || (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');

  if (effectiveLevel === 'high') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
        <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
        <span>{score.toFixed(0)}</span>
        {showLabel && <span className="text-[10px] uppercase font-bold tracking-wider">Cao</span>}
      </span>
    );
  }

  if (effectiveLevel === 'medium') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        <Shield className="w-3.5 h-3.5 text-amber-600" />
        <span>{score.toFixed(0)}</span>
        {showLabel && <span className="text-[10px] uppercase font-bold tracking-wider">Trung bình</span>}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
      <span>{score.toFixed(0)}</span>
      {showLabel && <span className="text-[10px] uppercase font-bold tracking-wider">An toàn</span>}
    </span>
  );
};
