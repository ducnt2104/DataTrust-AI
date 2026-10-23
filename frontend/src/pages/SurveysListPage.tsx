import React, { useEffect, useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  BarChart3,
  Users,
  Share2,
  Trash2,
  Lock,
  Edit3,
  Camera,
  UserCheck,
  RotateCcw,
  Copy
} from 'lucide-react';
import { api } from '../api/client';
import { SurveyListItem } from '../types/survey';
import { StatusBadge } from '../components/StatusBadge';
import { RiskBadge } from '../components/RiskBadge';
import { ShareModal } from '../components/ShareModal';

interface Props {
  onNavigate: (path: string) => void;
}

export const SurveysListPage: React.FC<Props> = ({ onNavigate }) => {
  const [surveys, setSurveys] = useState<SurveyListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [shareSurvey, setShareSurvey] = useState<{ title: string; slug: string } | null>(null);

  useEffect(() => {
    fetchSurveys();
  }, []);

  const fetchSurveys = async () => {
    try {
      setLoading(true);
      const data = await api.getSurveys();
      setSurveys(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSurvey = async (id: string) => {
    if (window.confirm('Bạn có chắc chắn muốn đóng khảo sát này? Người dùng sẽ không thể gửi thêm phản hồi.')) {
      try {
        await api.closeSurvey(id);
        fetchSurveys();
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Lỗi đóng khảo sát');
      }
    }
  };

  const handleReopenSurvey = async (id: string) => {
    if (window.confirm('Bạn có muốn mở lại khảo sát này để tiếp tục nhận phản hồi công khai?')) {
      try {
        await api.reopenSurvey(id);
        fetchSurveys();
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Lỗi mở lại khảo sát');
      }
    }
  };

  const handleDuplicateSurvey = async (id: string) => {
    try {
      const dup = await api.duplicateSurvey(id);
      fetchSurveys();
      alert(`Đã nhân bản thành công! Bản nháp mới: "${dup.title}"`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi nhân bản khảo sát');
    }
  };

  const handleDeleteSurvey = async (id: string) => {
    if (window.confirm('Hành động này sẽ xóa vĩnh viễn cuộc khảo sát và toàn bộ phản hồi liên quan. Bạn có chắc không?')) {
      try {
        await api.deleteSurvey(id);
        fetchSurveys();
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Lỗi xóa khảo sát');
      }
    }
  };

  const filteredSurveys = surveys.filter((s) => {
    const matchesSearch = s.title.toLowerCase().includes(search.toLowerCase()) ||
                          s.description.toLowerCase().includes(search.toLowerCase()) ||
                          s.public_slug.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = selectedStatus === 'all' || s.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Khảo sát của tôi</h1>
          <p className="text-sm text-slate-500">Quản lý các cuộc khảo sát, kiểm tra liên kết công khai và theo dõi dữ liệu thu thập</p>
        </div>
        <button
          onClick={() => onNavigate('/surveys/new')}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-xs transition-all active:scale-98 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo khảo sát</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Tìm theo tiêu đề, mô tả hoặc slug..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-600 focus:outline-hidden transition-all"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
          {[
            { id: 'all', label: 'Tất cả' },
            { id: 'published', label: 'Đang mở' },
            { id: 'draft', label: 'Bản nháp' },
            { id: 'closed', label: 'Đã đóng' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedStatus(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                selectedStatus === tab.id
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200/70 text-slate-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* List / Table */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500">
          Đang tải danh sách khảo sát...
        </div>
      ) : filteredSurveys.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-dashed border-slate-300 space-y-3">
          <p className="text-slate-500 text-sm">Không tìm thấy cuộc khảo sát nào phù hợp với bộ lọc.</p>
          <button
            onClick={() => { setSearch(''); setSelectedStatus('all'); }}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
          >
            Đặt lại bộ lọc
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSurveys.map((survey) => (
            <div
              key={survey.id}
              className="bg-white rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden group"
            >
              <div className="p-6 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <StatusBadge status={survey.status} />
                  <RiskBadge score={survey.avg_risk_score} />
                </div>

                <div>
                  <h3
                    onClick={() => onNavigate(`/surveys/${survey.id}/edit`)}
                    className="text-base font-bold text-slate-900 group-hover:text-indigo-600 cursor-pointer line-clamp-1 transition-colors"
                  >
                    {survey.title}
                  </h3>
                  <p className="text-xs text-slate-500 line-clamp-2 mt-1">
                    {survey.description || 'Chưa có mô tả cho khảo sát này.'}
                  </p>
                </div>

                <div className="pt-2 flex items-center justify-between text-xs text-slate-500 border-t border-slate-100">
                  <span>{survey.questions_count} câu hỏi</span>
                  <span className="font-semibold text-slate-900 flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-indigo-500" />
                    {survey.responses_count} phản hồi
                  </span>
                </div>
              </div>

              {/* Action Buttons Footer */}
              <div className="px-6 py-3 bg-slate-50/70 border-t border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-1">
                  <button
                    title="Chỉnh sửa câu hỏi"
                    onClick={() => onNavigate(`/surveys/${survey.id}/edit`)}
                    className="p-1.5 rounded-lg text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    title="Xem phản hồi thu thập"
                    onClick={() => onNavigate(`/surveys/${survey.id}/responses`)}
                    className="p-1.5 rounded-lg text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    <Users className="w-4 h-4" />
                  </button>
                  <button
                    title="Phân tích chất lượng"
                    onClick={() => onNavigate(`/surveys/${survey.id}/analytics`)}
                    className="p-1.5 rounded-lg text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    <BarChart3 className="w-4 h-4" />
                  </button>
                  <button
                    title="Mẫu phiếu giấy & Quét OMR"
                    onClick={() => onNavigate(`/surveys/${survey.id}/paper`)}
                    className="p-1.5 rounded-lg text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                  >
                    <Camera className="w-4 h-4" />
                  </button>
                  <button
                    title="Giám sát Điều tra viên & Khu vực"
                    onClick={() => onNavigate(`/surveys/${survey.id}/enumerators`)}
                    className="p-1.5 rounded-lg text-slate-600 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                  >
                    <UserCheck className="w-4 h-4" />
                  </button>
                  <button
                    title="Nhân bản khảo sát (Duplicate)"
                    onClick={() => handleDuplicateSurvey(survey.id)}
                    className="p-1.5 rounded-lg text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  {survey.status === 'published' && (
                    <button
                      title="Lấy link & mã QR"
                      onClick={() => setShareSurvey({ title: survey.title, slug: survey.public_slug })}
                      className="p-1.5 rounded-lg text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                    >
                      <Share2 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                <div className="flex items-center gap-1">
                  {survey.status === 'closed' && (
                    <button
                      title="Mở lại khảo sát"
                      onClick={() => handleReopenSurvey(survey.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  )}
                  {survey.status === 'published' && (
                    <button
                      title="Đóng khảo sát"
                      onClick={() => handleCloseSurvey(survey.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                    >
                      <Lock className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    title="Xóa khảo sát"
                    onClick={() => handleDeleteSurvey(survey.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

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
