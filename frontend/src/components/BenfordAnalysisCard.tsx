import React, { useEffect, useState } from 'react';
import { BarChart3, AlertTriangle, CheckCircle2, Info, RefreshCw } from 'lucide-react';
import { api } from '../api/client';

interface Props {
  surveyId: string;
}

export const BenfordAnalysisCard: React.FC<Props> = ({ surveyId }) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBenford();
  }, [surveyId]);

  const loadBenford = async () => {
    try {
      setLoading(true);
      const res = await api.getBenfordAnalysis(surveyId);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-center text-slate-400 text-xs">
        <RefreshCw className="w-4 h-4 animate-spin mr-2" />
        Đang chạy kiểm định Benford's Law trên các trường số liệu...
      </div>
    );
  }

  if (!data || data.total_numeric_samples === 0) {
    return null; // Không hiển thị nếu khảo sát không có câu hỏi số liệu hoặc chưa có phản hồi số
  }

  const {
    total_numeric_samples,
    is_sample_sufficient,
    notice,
    chi_square_statistic,
    is_anomalous,
    significance_level,
    distribution
  } = data;

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-slate-900 text-base">
              Kiểm định Luật Benford trên số liệu (Benford's Law First-Digit Test)
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Phát hiện số liệu ngụy tạo / bịa đặt theo phương pháp Schräpler & Wagner (2012, AAPOR)
          </p>
        </div>

        <div className="flex items-center gap-2">
          {is_anomalous ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Bất thường ({significance_level})</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Khớp tự nhiên (χ² = {chi_square_statistic})</span>
            </span>
          )}
        </div>
      </div>

      {notice && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200/70 text-xs text-amber-800 flex items-start gap-2">
          <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span>{notice}</span>
        </div>
      )}

      {/* Grid of First Digits 1 to 9 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
          <span>Chữ số đầu tiên (First Digit d ∈ 1..9)</span>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-indigo-600 inline-block" /> Thực tế quan sát (%)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-slate-300 inline-block" /> Lý thuyết Benford (%)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-9 gap-2">
          {distribution.map((item: any) => {
            const isDiscrepant = Math.abs(item.difference) >= 10.0;
            return (
              <div
                key={item.digit}
                className={`p-3 rounded-xl border flex flex-col justify-between text-center transition-all ${
                  isDiscrepant
                    ? 'border-rose-200 bg-rose-50/40 ring-1 ring-rose-200'
                    : 'border-slate-100 bg-slate-50/70'
                }`}
              >
                <div className="text-sm font-black text-slate-900 font-mono">
                  {item.digit}
                </div>

                {/* Micro Bar Representation */}
                <div className="my-2 h-16 flex items-end justify-center gap-1 bg-white p-1 rounded-lg border border-slate-100">
                  <div
                    title={`Thực tế: ${item.observed_percentage}%`}
                    style={{ height: `${Math.min(100, item.observed_percentage * 2)}%` }}
                    className={`w-2.5 rounded-t-xs transition-all ${isDiscrepant ? 'bg-rose-600' : 'bg-indigo-600'}`}
                  />
                  <div
                    title={`Benford: ${item.benford_percentage}%`}
                    style={{ height: `${Math.min(100, item.benford_percentage * 2)}%` }}
                    className="w-2.5 bg-slate-300 rounded-t-xs"
                  />
                </div>

                <div className="text-[10px] space-y-0.5">
                  <div className="font-bold text-slate-800">{item.observed_percentage}%</div>
                  <div className="text-slate-400 font-mono text-[9px]">Lý thuyết: {item.benford_percentage}%</div>
                  <div className={`font-mono text-[9px] font-semibold ${isDiscrepant ? 'text-rose-600' : 'text-slate-500'}`}>
                    {item.difference > 0 ? `+${item.difference}%` : `${item.difference}%`}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Footer */}
      <div className="text-xs text-slate-500 bg-slate-50 p-3.5 rounded-xl border border-slate-200/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          Tổng số quan sát số học: <strong className="text-slate-800 font-mono">{total_numeric_samples}</strong> | Bậc tự do: <strong className="text-slate-800 font-mono">8</strong> | Thống kê Chi-Square: <strong className="text-slate-800 font-mono">χ² = {chi_square_statistic}</strong>
        </div>
        <div className="text-[11px] text-slate-400 italic">
          Ngưỡng p &lt; 0.05: χ² = 15.51 | p &lt; 0.01: χ² = 20.09
        </div>
      </div>
    </div>
  );
};