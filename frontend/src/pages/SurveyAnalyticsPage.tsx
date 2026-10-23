import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Users,
  Clock,
  ShieldAlert,
  AlertTriangle,
  Download,
  CheckCircle2,
  HelpCircle,
  FileText,
  FileCheck
} from 'lucide-react';
import { api } from '../api/client';
import { SurveyAnalytics } from '../types/survey';
import { QualityAuditReportModal } from '../components/QualityAuditReportModal';
import { BenfordAnalysisCard } from '../components/BenfordAnalysisCard';

interface Props {
  surveyId: string;
  onNavigate: (path: string) => void;
}

export const SurveyAnalyticsPage: React.FC<Props> = ({ surveyId, onNavigate }) => {
  const [analytics, setAnalytics] = useState<SurveyAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, [surveyId]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await api.getSurveyAnalytics(surveyId);
      setAnalytics(data);
    } catch (err) {
      console.error(err);
      alert('Không thể tải báo cáo phân tích.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center text-slate-500 text-sm">
        Đang tổng hợp dữ liệu thống kê từ database...
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="p-8 text-center text-slate-500">
        Không có dữ liệu phân tích.
      </div>
    );
  }

  const {
    survey_title,
    total_responses,
    is_sample_size_sufficient,
    sample_size_notice,
    avg_duration_seconds,
    risk_distribution,
    review_distribution,
    questions_analytics
  } = analytics;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-300">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('/surveys')}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Báo cáo phân tích chất lượng
            </h1>
            <p className="text-sm text-slate-500 font-medium">
              Khảo sát: <span className="text-indigo-600 font-semibold">{survey_title}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setIsAuditModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 transition-all shadow-xs"
          >
            <FileCheck className="w-4 h-4 text-emerald-600" />
            <span>Báo cáo kiểm định độc lập</span>
          </button>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/enumerators`)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-all"
          >
            <Users className="w-4 h-4" />
            <span>Giám sát Điều tra viên</span>
          </button>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/responses`)}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all"
          >
            Xem danh sách phản hồi ({total_responses})
          </button>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/export`)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Xuất dữ liệu</span>
          </button>
        </div>
      </div>

      {/* Sample Size Warning if N < 5 */}
      {!is_sample_size_sufficient && (
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <h4 className="font-bold text-sm">Cảnh báo tính đại diện của mẫu (Data Integrity Guard)</h4>
            <p className="text-xs text-amber-800 leading-relaxed">
              {sample_size_notice || 'Cỡ mẫu hiện tại chưa đạt ngưỡng N >= 5 để đảm bảo ý nghĩa thống kê tổng thể.'} Các tỷ lệ phân phối dưới đây chỉ mang tính chất mô tả các phản hồi đã thu thập thực tế.
            </p>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tổng phản hồi đã lưu</span>
            <div className="text-3xl font-extrabold text-slate-900">{total_responses}</div>
            <span className="text-xs text-slate-400">100% dữ liệu thực</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Thời gian làm bài TB</span>
            <div className="text-3xl font-extrabold text-slate-900">{avg_duration_seconds}s</div>
            <span className="text-xs text-slate-400">Độ dài trung bình mỗi lượt</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Phân loại rủi ro</span>
            <div className="flex items-center gap-2 pt-1 text-sm font-bold">
              <span className="text-emerald-600">{risk_distribution['low'] || 0} thấp</span>
              <span>•</span>
              <span className="text-amber-600">{risk_distribution['medium'] || 0} vừa</span>
              <span>•</span>
              <span className="text-rose-600">{risk_distribution['high'] || 0} cao</span>
            </div>
            <span className="text-xs text-slate-400">Được phân tích tự động</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center text-amber-600">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Benford's Law First-Digit Statistical Analysis */}
      <BenfordAnalysisCard surveyId={surveyId} />

      {/* Per-Question Analytics */}
      <div className="space-y-6">
        <h2 className="text-lg font-bold text-slate-900">Chi tiết phân bố theo từng câu hỏi</h2>

        {questions_analytics.map((q, idx) => (
          <div
            key={q.question_id}
            className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
                  Câu hỏi {idx + 1} • {q.question_type}
                </span>
                <h3 className="text-base font-bold text-slate-900">{q.question_title}</h3>
              </div>
              <span className="text-xs text-slate-500 font-medium whitespace-nowrap bg-slate-100 px-2.5 py-1 rounded-full">
                {q.total_answers} câu trả lời
              </span>
            </div>

            {/* Option distribution bars */}
            {q.option_distribution && (
              <div className="space-y-3 pt-2">
                {Object.entries(q.option_distribution).map(([label, count]) => {
                  const percent = q.total_answers > 0 ? Math.round((count / q.total_answers) * 100) : 0;
                  return (
                    <div key={label} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-medium text-slate-700">
                        <span className="line-clamp-1">{label}</span>
                        <span className="text-slate-500 shrink-0 font-semibold">{count} ({percent}%)</span>
                      </div>
                      <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Numeric summary */}
            {q.stats_summary && q.stats_summary.min !== undefined && (
              <div className="grid grid-cols-3 gap-3 p-3 bg-slate-50 rounded-xl text-center text-xs">
                <div>
                  <span className="text-slate-400 block">Thấp nhất (Min)</span>
                  <span className="font-bold text-slate-800 text-sm">{q.stats_summary.min}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Trung bình (Avg)</span>
                  <span className="font-bold text-indigo-600 text-sm">{q.stats_summary.avg}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Cao nhất (Max)</span>
                  <span className="font-bold text-slate-800 text-sm">{q.stats_summary.max}</span>
                </div>
              </div>
            )}

            {/* Matrix summary */}
            {q.stats_summary?.matrix_distribution && (
              <div className="space-y-2 pt-1 overflow-x-auto">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Phân bố tần suất theo ma trận tiêu chí
                </span>
                <table className="w-full text-xs text-left border-collapse border border-slate-200 rounded-lg overflow-hidden">
                  <thead className="bg-slate-50 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3 border border-slate-200">Tiêu chí</th>
                      {Object.keys(Object.values(q.stats_summary.matrix_distribution)[0] || {}).map((col) => (
                        <th key={col} className="py-2.5 px-3 border border-slate-200 text-center">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {Object.entries(q.stats_summary.matrix_distribution).map(([rowLabel, colCounts]: [string, any]) => (
                      <tr key={rowLabel} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-medium text-slate-800 border border-slate-200">{rowLabel}</td>
                        {Object.entries(colCounts).map(([cLabel, count]: [string, any]) => (
                          <td key={cLabel} className="py-2.5 px-3 text-center border border-slate-200 font-semibold text-indigo-700">
                            {count}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Ranking summary */}
            {q.stats_summary?.ranking_averages && (
              <div className="space-y-2 pt-1">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Thứ hạng trung bình các mục ưu tiên (Số càng nhỏ biểu thị mức ưu tiên càng cao)
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {Object.entries(q.stats_summary.ranking_averages).map(([itemLabel, avgRank]: [string, any]) => (
                    <div key={itemLabel} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-800">{itemLabel}</span>
                      <span className="font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-200">
                        Hạng TB: {avgRank}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Text Samples */}
            {q.recent_text_samples && q.recent_text_samples.length > 0 && (
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Các câu trả lời mẫu gần đây
                </span>
                <div className="space-y-1.5">
                  {q.recent_text_samples.map((sample, sIdx) => (
                    <div key={sIdx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-xs text-slate-700 italic">
                      "{sample}"
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quality Audit Report & Legal Compliance Modal */}
      <QualityAuditReportModal
        surveyId={surveyId}
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        onRefreshAnalytics={loadAnalytics}
      />
    </div>
  );
};
