import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Eye,
  GitCompare,
  Download
} from 'lucide-react';
import { api } from '../api/client';
import { ResponseListItem } from '../types/survey';
import { RiskBadge } from '../components/RiskBadge';

interface Props {
  surveyId: string;
  onNavigate: (path: string) => void;
}

export const ResponsesListPage: React.FC<Props> = ({ surveyId, onNavigate }) => {
  const [responses, setResponses] = useState<ResponseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [reviewFilter, setReviewFilter] = useState<string>('all');
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  useEffect(() => {
    fetchResponses();
  }, [surveyId, riskFilter, reviewFilter]);

  const fetchResponses = async () => {
    try {
      setLoading(true);
      const rf = riskFilter === 'all' ? undefined : riskFilter;
      const vf = reviewFilter === 'all' ? undefined : reviewFilter;
      const data = await api.getResponses(surveyId, rf, vf);
      setResponses(data);
    } catch (err) {
      console.error(err);
      alert('Không thể tải danh sách phản hồi.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectForCompare = (id: string) => {
    if (selectedForCompare.includes(id)) {
      setSelectedForCompare(selectedForCompare.filter((x) => x !== id));
    } else {
      if (selectedForCompare.length >= 2) {
        setSelectedForCompare([selectedForCompare[1], id]);
      } else {
        setSelectedForCompare([...selectedForCompare, id]);
      }
    }
  };

  const handleRunCompare = () => {
    if (selectedForCompare.length === 2) {
      onNavigate(`/surveys/${surveyId}/compare?resp1=${selectedForCompare[0]}&resp2=${selectedForCompare[1]}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in duration-300">
      {/* Header */}
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
              Trung tâm rà soát dữ liệu (Review Center)
            </h1>
            <p className="text-sm text-slate-500">
              Quản lý danh sách phản hồi, kiểm tra bằng chứng cảnh báo và ghi nhận quyết định xác minh
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectedForCompare.length === 2 && (
            <button
              onClick={handleRunCompare}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all animate-bounce"
            >
              <GitCompare className="w-4 h-4" />
              <span>Đối chiếu 2 phản hồi đã chọn</span>
            </button>
          )}
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/export`)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Xuất dữ liệu</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
        {/* Risk Level Filter */}
        <div className="flex items-center gap-1 text-xs">
          <span className="font-semibold text-slate-500 mr-2 uppercase tracking-wider">Mức rủi ro:</span>
          {['all', 'high', 'medium', 'low'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setRiskFilter(lvl)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                riskFilter === lvl
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 hover:bg-slate-200/70 text-slate-600'
              }`}
            >
              {lvl === 'all' ? 'Tất cả' : lvl === 'high' ? 'Cao' : lvl === 'medium' ? 'Trung bình' : 'Thấp'}
            </button>
          ))}
        </div>

        {/* Verification Status Filter */}
        <div className="flex items-center gap-1 text-xs">
          <span className="font-semibold text-slate-500 mr-2 uppercase tracking-wider">Xác minh:</span>
          {[
            { id: 'all', label: 'Tất cả' },
            { id: 'unverified', label: 'Chưa duyệt' },
            { id: 'under_review', label: 'Đang xem xét' },
            { id: 'verified_valid', label: 'Hợp lệ' },
            { id: 'verified_fraud', label: 'Bị loại' }
          ].map((st) => (
            <button
              key={st.id}
              onClick={() => setReviewFilter(st.id)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                reviewFilter === st.id
                  ? 'bg-slate-800 text-white'
                  : 'bg-slate-100 hover:bg-slate-200/70 text-slate-600'
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {/* Responses Table */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500">
          Đang tải phản hồi...
        </div>
      ) : responses.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-dashed border-slate-300 space-y-2">
          <p className="text-sm font-semibold text-slate-700">Chưa có phản hồi nào phù hợp.</p>
          <p className="text-xs text-slate-400">Hãy chia sẻ link khảo sát để bắt đầu thu thập câu trả lời từ người tham gia.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50/80 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200/80">
                <tr>
                  <th className="py-3.5 px-4 w-10">Chọn</th>
                  <th className="py-3.5 px-4">Mã phản hồi</th>
                  <th className="py-3.5 px-4">Thời điểm gửi</th>
                  <th className="py-3.5 px-4">Thời lượng</th>
                  <th className="py-3.5 px-4">Điểm rủi ro</th>
                  <th className="py-3.5 px-4">Cờ cảnh báo</th>
                  <th className="py-3.5 px-4">Xác minh</th>
                  <th className="py-3.5 px-6 text-right">Chi tiết</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {responses.map((resp) => {
                  const isChecked = selectedForCompare.includes(resp.id);
                  return (
                    <tr
                      key={resp.id}
                      className={`hover:bg-slate-50/70 transition-colors ${
                        isChecked ? 'bg-indigo-50/30' : ''
                      }`}
                    >
                      <td className="py-4 px-4">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleSelectForCompare(resp.id)}
                          className="w-4 h-4 text-indigo-600 rounded-sm border-slate-300 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="py-4 px-4 font-mono text-xs font-bold text-slate-800">
                        {resp.id.slice(0, 8)}...
                      </td>
                      <td className="py-4 px-4 text-xs whitespace-nowrap text-slate-600">
                        {new Date(resp.submitted_at).toLocaleString()}
                      </td>
                      <td className="py-4 px-4 text-xs font-medium text-slate-700 whitespace-nowrap">
                        {resp.duration_seconds}s
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap">
                        <RiskBadge score={resp.risk_score} level={resp.risk_level} />
                      </td>
                      <td className="py-4 px-4 text-xs">
                        {resp.flags_count > 0 ? (
                          <div className="space-y-0.5">
                            <span className="inline-flex items-center gap-1 font-bold text-amber-700">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                              {resp.flags_count} cảnh báo
                            </span>
                            <p className="text-[11px] text-slate-500 line-clamp-1">
                              {resp.flags_summary[0]}
                            </p>
                          </div>
                        ) : (
                          <span className="text-emerald-600 font-medium text-xs flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Không có cờ
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap text-xs">
                        {resp.review_status === 'verified_valid' && (
                          <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                            Hợp lệ
                          </span>
                        )}
                        {resp.review_status === 'verified_fraud' && (
                          <span className="px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 font-semibold">
                            Bị loại
                          </span>
                        )}
                        {resp.review_status === 'under_review' && (
                          <span className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-semibold">
                            Đang xem xét
                          </span>
                        )}
                        {resp.review_status === 'unverified' && (
                          <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-medium">
                            Chưa duyệt
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-right whitespace-nowrap">
                        <button
                          onClick={() => onNavigate(`/surveys/${surveyId}/responses/${resp.id}`)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 transition-colors inline-flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Xem chi tiết</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
