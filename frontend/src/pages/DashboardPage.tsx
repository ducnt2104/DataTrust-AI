import React, { useEffect, useState, useMemo } from 'react';
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
  Share2,
  Camera,
  UserCheck,
  Search,
  Filter,
  Copy,
  Trash2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Clock,
  Activity,
  FlaskConical
} from 'lucide-react';
import { api } from '../api/client';
import { SurveyListItem } from '../types/survey';
import { StatusBadge } from '../components/StatusBadge';
import { RiskBadge } from '../components/RiskBadge';
import { ShareModal } from '../components/ShareModal';
import { SystemDiagnosticsModal } from '../components/SystemDiagnosticsModal';

interface Props {
  onNavigate: (path: string) => void;
}

export const DashboardPage: React.FC<Props> = ({ onNavigate }) => {
  const [surveys, setSurveys] = useState<SurveyListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [shareSurvey, setShareSurvey] = useState<{ title: string; slug: string } | null>(null);

  // Filter, Search, Sort & Pagination state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'published' | 'draft' | 'closed'>('all');
  const [sortBy, setSortBy] = useState<'newest' | 'responses' | 'risk'>('newest');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const [actionToast, setActionToast] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);
  const [showDiagModal, setShowDiagModal] = useState(false);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const showToast = (msg: string) => {
    setActionToast(msg);
    setTimeout(() => setActionToast(null), 4500);
  };

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

  const handleDuplicate = async (surveyId: string, title: string) => {
    try {
      setActingId(surveyId);
      const newSurvey = await api.duplicateSurvey(surveyId);
      await loadData();
      showToast(`Đã nhân bản "${title}" thành công! Bản sao mới: "${newSurvey.title}"`);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi nhân bản khảo sát');
    } finally {
      setActingId(null);
    }
  };

  const handleDelete = async (surveyId: string, title: string) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn cuộc khảo sát "${title}" không? Hành động này sẽ xóa các câu hỏi và phản hồi liên quan.`)) {
      return;
    }
    try {
      setActingId(surveyId);
      await api.deleteSurvey(surveyId);
      await loadData();
      showToast(`Đã xóa cuộc khảo sát "${title}" thành công.`);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi xóa khảo sát');
    } finally {
      setActingId(null);
    }
  };

  const handleSeedAcademicDemo = async () => {
    try {
      setSeeding(true);
      const res = await api.seedAcademicDemo();
      await loadData();
      showToast(`🧪 ${res.message} (Chỉ số tin cậy: ${res.data_trust_index}%, Cronbach's α: ${res.cronbach_alpha ?? 'N/A'})`);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi khởi tạo bộ dữ liệu nghiên cứu mẫu');
    } finally {
      setSeeding(false);
    }
  };

  const filteredSurveys = useMemo(() => {
    return surveys
      .filter((s) => {
        if (statusFilter !== 'all' && s.status !== statusFilter) return false;
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          return s.title.toLowerCase().includes(q) || s.public_slug.toLowerCase().includes(q);
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'responses') return b.responses_count - a.responses_count;
        if (sortBy === 'risk') return b.avg_risk_score - a.avg_risk_score;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [surveys, statusFilter, searchQuery, sortBy]);

  const totalPages = Math.ceil(filteredSurveys.length / pageSize) || 1;
  const paginatedSurveys = filteredSurveys.slice((currentPage - 1) * pageSize, currentPage * pageSize);

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
            DataTrust Workspace
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Tạo biểu mẫu chuyên nghiệp, phát hành liên kết khảo sát thực và tự động phát hiện phản hồi bất thường, gian lận bằng AI & thuật toán thống kê.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleSeedAcademicDemo}
            disabled={seeding}
            className="flex items-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-semibold shadow-md shadow-emerald-950/40 transition-all border border-emerald-400/30 active:scale-98 disabled:opacity-50"
            title="Khởi tạo Khảo sát Nghiên cứu Khoa học Mẫu & Bộ Dữ liệu Thực nghiệm 35 phản hồi chuẩn Don Dillman & AAPOR 2003"
          >
            {seeding ? (
              <RefreshCw className="w-4 h-4 text-emerald-200 animate-spin" />
            ) : (
              <FlaskConical className="w-4 h-4 text-emerald-200" />
            )}
            <span>{seeding ? 'Đang tạo mẫu...' : 'Dữ liệu mẫu nghiên cứu (35N)'}</span>
          </button>

          <button
            onClick={() => setShowDiagModal(true)}
            className="flex items-center gap-1.5 px-4 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm font-semibold transition-all border border-white/15 active:scale-98"
            title="Kiểm tra chẩn đoán sức khỏe CSDL, B-Tree và chuỗi băm bất biến"
          >
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>Giám sát CSDL</span>
          </button>

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

      {/* Main Content: Survey List with Search & Advanced Filter */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Danh mục khảo sát</h2>
            <p className="text-xs text-slate-500">Tìm kiếm, phân loại trạng thái, quản lý và nhân bản biểu mẫu</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigate('/surveys/new')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Tạo khảo sát</span>
            </button>
          </div>
        </div>

        {/* Action Toast Feedback */}
        {actionToast && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold flex items-center gap-2 animate-in fade-in duration-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionToast}</span>
          </div>
        )}

        {/* Search, Filter & Sort Controls */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200/80 shadow-xs">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Tìm theo tiêu đề hoặc liên kết slug..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium text-slate-800"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-medium overflow-x-auto">
            <button
              onClick={() => { setStatusFilter('all'); setCurrentPage(1); }}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
                statusFilter === 'all' ? 'bg-white shadow-xs text-indigo-700 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Tất cả ({surveys.length})
            </button>
            <button
              onClick={() => { setStatusFilter('published'); setCurrentPage(1); }}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
                statusFilter === 'published' ? 'bg-white shadow-xs text-emerald-700 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Đang mở ({surveys.filter((s) => s.status === 'published').length})
            </button>
            <button
              onClick={() => { setStatusFilter('draft'); setCurrentPage(1); }}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
                statusFilter === 'draft' ? 'bg-white shadow-xs text-amber-700 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Bản nháp ({surveys.filter((s) => s.status === 'draft').length})
            </button>
            <button
              onClick={() => { setStatusFilter('closed'); setCurrentPage(1); }}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
                statusFilter === 'closed' ? 'bg-white shadow-xs text-slate-800 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Đã đóng ({surveys.filter((s) => s.status === 'closed').length})
            </button>
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs text-slate-500 font-medium">Sắp xếp:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="newest">Mới tạo gần đây</option>
              <option value="responses">Nhiều phản hồi nhất</option>
              <option value="risk">Rủi ro cao nhất</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500 text-xs">
            Đang tải dữ liệu khảo sát...
          </div>
        ) : filteredSurveys.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-3xl border border-dashed border-slate-300 space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h3 className="text-sm font-semibold text-slate-900">Không tìm thấy cuộc khảo sát nào</h3>
              <p className="text-xs text-slate-500">
                {searchQuery || statusFilter !== 'all'
                  ? 'Thử thay đổi từ khóa tìm kiếm hoặc bỏ bộ lọc trạng thái để xem thêm.'
                  : 'Hãy bắt đầu tạo cuộc khảo sát đầu tiên của bạn.'}
              </p>
            </div>
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
                  {paginatedSurveys.map((survey) => (
                    <tr key={survey.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-4 px-6">
                        <div
                          className="font-semibold text-slate-900 hover:text-indigo-600 cursor-pointer line-clamp-1"
                          onClick={() => onNavigate(`/surveys/${survey.id}/edit`)}
                        >
                          {survey.title}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          v{survey.version} • /{survey.public_slug}
                        </div>
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap">
                        <StatusBadge status={survey.status} />
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap font-medium text-slate-700 text-xs">
                        {survey.questions_count} câu
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className="font-semibold text-slate-900">{survey.responses_count}</span>
                        <span className="text-xs text-slate-400 ml-1">phiếu</span>
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap">
                        <RiskBadge score={survey.avg_risk_score} />
                      </td>
                      <td className="py-4 px-6 text-right whitespace-nowrap space-x-1">
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
                          title="Mẫu phiếu giấy & Quét OMR"
                          onClick={() => onNavigate(`/surveys/${survey.id}/paper`)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                        >
                          <Camera className="w-4 h-4" />
                        </button>
                        <button
                          title="Giám sát Điều tra viên"
                          onClick={() => onNavigate(`/surveys/${survey.id}/enumerators`)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                        >
                          <UserCheck className="w-4 h-4" />
                        </button>
                        <button
                          title="Nhân bản khảo sát (1-Click Clone)"
                          disabled={actingId === survey.id}
                          onClick={() => handleDuplicate(survey.id, survey.title)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-50"
                        >
                          {actingId === survey.id ? (
                            <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          title="Xóa cuộc khảo sát"
                          disabled={actingId === survey.id}
                          onClick={() => handleDelete(survey.id, survey.title)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => onNavigate(`/surveys/${survey.id}/edit`)}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 transition-colors ml-1"
                        >
                          Sửa
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="p-3.5 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-600">
                <div>
                  Hiển thị{' '}
                  <strong>{(currentPage - 1) * pageSize + 1}</strong> -{' '}
                  <strong>{Math.min(currentPage * pageSize, filteredSurveys.length)}</strong> trên{' '}
                  <strong>{filteredSurveys.length}</strong> cuộc khảo sát
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="px-2 font-medium">
                    Trang {currentPage} / {totalPages}
                  </span>
                  <button
                    disabled={currentPage >= totalPages}
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
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

      {/* System Diagnostics & Storage Health Modal */}
      <SystemDiagnosticsModal
        isOpen={showDiagModal}
        onClose={() => setShowDiagModal(false)}
      />
    </div>
  );
};
