import React, { useEffect, useState } from 'react';
import {
  FileText,
  CheckCircle2,
  Users,
  ShieldAlert,
  Plus,
  ArrowRight,
  ExternalLink,
  BarChart3,
  Sparkles,
  Share2
} from 'lucide-react';
import { api } from '../api/client';
import { SurveyListItem } from '../types/survey';
import { StatusBadge } from '../components/StatusBadge';
import { RiskBadge } from '../components/RiskBadge';
import { ShareModal } from '../components/ShareModal';

interface Props {
  onNavigate: (path: string) => void;
}

export const DashboardPage: React.FC<Props> = ({ onNavigate }) => {
  const [surveys, setSurveys] = useState<SurveyListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [shareSurvey, setShareSurvey] = useState<{ title: string; slug: string } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.getSurveys();
      setSurveys(data);
    } catch (err) {
      console.error('Lỗi tải dữ liệu dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const totalSurveys = surveys.length;
  const activeSurveys = surveys.filter((s) => s.status === 'published').length;
  const totalResponses = surveys.reduce((acc, s) => acc + s.responses_count, 0);
  const avgRisk = totalSurveys > 0
    ? (surveys.reduce((acc, s) => acc + s.avg_risk_score, 0) / totalSurveys)
    : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-300">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-xl">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold border border-indigo-500/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Nền tảng kiểm định chất lượng khảo sát thế hệ mới</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            DataTrust AI Workspace
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Tạo biểu mẫu chuyên nghiệp, phát hành liên kết khảo sát thực và tự động phát hiện phản hồi bất thường, gian lận bằng AI & thuật toán thống kê.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => onNavigate('/surveys/new')}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-md shadow-indigo-600/30 transition-all active:scale-98"
          >
            <Plus className="w-4 h-4" />
            <span>Tạo khảo sát mới</span>
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Total Surveys */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tổng số khảo sát</span>
            <div className="text-2xl sm:text-3xl font-bold text-slate-900">{totalSurveys}</div>
            <span className="text-xs text-slate-500">Khảo sát trong hệ thống</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        {/* Active Published */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Đang nhận phản hồi</span>
            <div className="text-2xl sm:text-3xl font-bold text-emerald-600">{activeSurveys}</div>
            <span className="text-xs text-slate-500">Đã xuất bản liên kết</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Real Responses */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Phản hồi thực tế</span>
            <div className="text-2xl sm:text-3xl font-bold text-slate-900">{totalResponses}</div>
            <span className="text-xs text-slate-500">Đã lưu vào cơ sở dữ liệu</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Users className="w-6 h-6" />
          </div>
        </div>

        {/* Quality Risk Index */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Chỉ số rủi ro TB</span>
            <div className="text-2xl sm:text-3xl font-bold text-slate-900">{avgRisk.toFixed(1)} <span className="text-xs text-slate-400 font-normal">/ 100</span></div>
            <span className="text-xs text-slate-500">Heuristic Risk Score</span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center text-amber-600">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Main Content: Recent Surveys */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Khảo sát gần đây</h2>
            <p className="text-xs text-slate-500">Danh sách các biểu mẫu và số liệu phản hồi thu thập thực tế</p>
          </div>
          {surveys.length > 0 && (
            <button
              onClick={() => onNavigate('/surveys')}
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              <span>Xem tất cả</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>

        {loading ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500">
            Đang tải dữ liệu...
          </div>
        ) : surveys.length === 0 ? (
          /* Empty State */
          <div className="p-12 text-center bg-white rounded-3xl border border-dashed border-slate-300 space-y-4">
            <div className="w-16 h-16 rounded-full bg-indigo-50 text-indigo-600 mx-auto flex items-center justify-center">
              <FileText className="w-8 h-8" />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h3 className="text-base font-semibold text-slate-900">Chưa có cuộc khảo sát nào</h3>
              <p className="text-sm text-slate-500">
                Hãy bắt đầu tạo khảo sát đầu tiên của bạn hoặc sử dụng trợ lý AI để thiết kế các câu hỏi nghiên cứu chuẩn xác.
              </p>
            </div>
            <button
              onClick={() => onNavigate('/surveys/new')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Tạo khảo sát đầu tiên</span>
            </button>
          </div>
        ) : (
          /* Table of Surveys */
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50/80 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200/80">
                  <tr>
                    <th className="py-3.5 px-6">Tiêu đề khảo sát</th>
                    <th className="py-3.5 px-4">Trạng thái</th>
                    <th className="py-3.5 px-4">Câu hỏi</th>
                    <th className="py-3.5 px-4">Phản hồi</th>
                    <th className="py-3.5 px-4">Rủi ro TB</th>
                    <th className="py-3.5 px-6 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {surveys.slice(0, 6).map((survey) => (
                    <tr key={survey.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-4 px-6">
                        <div className="font-semibold text-slate-900 hover:text-indigo-600 cursor-pointer line-clamp-1"
                             onClick={() => onNavigate(`/surveys/${survey.id}/edit`)}>
                          {survey.title}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          Phiên bản v{survey.version} • Slug: /{survey.public_slug}
                        </div>
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap">
                        <StatusBadge status={survey.status} />
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap font-medium text-slate-700">
                        {survey.questions_count} câu
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className="font-semibold text-slate-900">{survey.responses_count}</span>
                        <span className="text-xs text-slate-400 ml-1">phản hồi</span>
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap">
                        <RiskBadge score={survey.avg_risk_score} />
                      </td>
                      <td className="py-4 px-6 text-right whitespace-nowrap space-x-2">
                        {survey.status === 'published' && (
                          <button
                            title="Chia sẻ link & mã QR"
                            onClick={() => setShareSurvey({ title: survey.title, slug: survey.public_slug })}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                          >
                            <Share2 className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          title="Báo cáo phân tích"
                          onClick={() => onNavigate(`/surveys/${survey.id}/analytics`)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                        >
                          <BarChart3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => onNavigate(`/surveys/${survey.id}/edit`)}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 transition-colors"
                        >
                          Chỉnh sửa
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Share Modal */}
      {shareSurvey && (
        <ShareModal
          isOpen={true}
          onClose={() => setShareSurvey(null)}
          surveyTitle={shareSurvey.title}
          publicSlug={shareSurvey.slug}
        />
      )}
    </div>
  );
};
