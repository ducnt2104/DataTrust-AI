import React, { useEffect, useState, useMemo } from 'react';
import { 
  ArrowLeft, GitCompare, CheckCircle2, AlertTriangle, ExternalLink, 
  FileText, Globe, User, Clock, ShieldAlert, Filter, CheckCircle, HelpCircle
} from 'lucide-react';
import { api } from '../api/client';

interface Props {
  surveyId: string;
  resp1Id: string;
  resp2Id: string;
  onNavigate: (path: string) => void;
}

export const ResponseComparePage: React.FC<Props> = ({ surveyId, resp1Id, resp2Id, onNavigate }) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterMode, setFilterMode] = useState<'all' | 'diff' | 'match'>('all');

  useEffect(() => {
    loadComparison();
  }, [surveyId, resp1Id, resp2Id]);

  const loadComparison = async () => {
    try {
      setLoading(true);
      const res = await api.compareResponses(surveyId, resp1Id, resp2Id);
      setData(res);
    } catch (err) {
      console.error(err);
      alert('Không thể so sánh 2 phản hồi.');
    } finally {
      setLoading(false);
    }
  };

  const filteredQuestions = useMemo(() => {
    if (!data?.questions_comparison) return [];
    if (filterMode === 'diff') return data.questions_comparison.filter((q: any) => !q.is_match);
    if (filterMode === 'match') return data.questions_comparison.filter((q: any) => q.is_match);
    return data.questions_comparison;
  }, [data, filterMode]);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center text-slate-500 gap-3">
        <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium">Đang đối chiếu vector câu trả lời...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-slate-500">
        Không có dữ liệu đối chiếu.
      </div>
    );
  }

  const {
    survey_title,
    resp1_risk_score,
    resp2_risk_score,
    resp1_meta,
    resp2_meta,
    similarity_percentage,
    matching_answers_count,
    total_questions_compared,
    questions_comparison
  } = data;

  const renderSourceBadge = (source?: string) => {
    if (source === 'paper_scan') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          <FileText className="w-3 h-3" /> Phiếu giấy OMR
        </span>
      );
    }
    if (source === 'csv_import') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-50 text-sky-700 border border-sky-200">
          <FileText className="w-3 h-3" /> Tệp CSV
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <Globe className="w-3 h-3" /> Trực tuyến
      </span>
    );
  };

  const renderRiskBadge = (score: number) => {
    if (score >= 60) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-700">
          Nguy cơ cao ({score})
        </span>
      );
    }
    if (score >= 30) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800">
          Trung bình ({score})
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">
        An toàn ({score})
      </span>
    );
  };

  const renderReviewStatus = (status?: string) => {
    switch (status) {
      case 'verified_valid':
        return <span className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Đã duyệt hợp lệ</span>;
      case 'verified_fraud':
        return <span className="text-[11px] font-semibold text-rose-700 flex items-center gap-1"><ShieldAlert className="w-3 h-3" /> Đã loại bỏ (Gian lận)</span>;
      case 'under_review':
        return <span className="text-[11px] font-semibold text-amber-700 flex items-center gap-1"><Clock className="w-3 h-3" /> Đang thẩm định</span>;
      case 'inconclusive':
        return <span className="text-[11px] font-semibold text-slate-700 flex items-center gap-1"><HelpCircle className="w-3 h-3" /> Chưa đủ kết luận</span>;
      default:
        return <span className="text-[11px] font-medium text-slate-500">Chưa thẩm định</span>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/responses`)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            title="Quay lại danh sách phản hồi"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <GitCompare className="w-6 h-6 text-indigo-600" />
              <span>Đối sánh phản hồi song song (Side-by-Side Comparison)</span>
            </h1>
            <p className="text-sm text-slate-500">
              Khảo sát: <strong className="text-slate-800">{survey_title}</strong>
            </p>
          </div>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl self-start sm:self-auto text-xs font-medium">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterMode === 'all' ? 'bg-white shadow-xs text-indigo-700 font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Tất cả ({questions_comparison?.length || 0})
          </button>
          <button
            onClick={() => setFilterMode('diff')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterMode === 'diff' ? 'bg-white shadow-xs text-rose-700 font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Khác biệt ({questions_comparison?.filter((q: any) => !q.is_match).length || 0})
          </button>
          <button
            onClick={() => setFilterMode('match')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterMode === 'match' ? 'bg-white shadow-xs text-emerald-700 font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Trùng khớp ({questions_comparison?.filter((q: any) => q.is_match).length || 0})
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric Card */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Độ tương đồng Hamming (Hamming Similarity)
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className={`text-3xl font-black ${similarity_percentage >= 80 ? 'text-rose-600' : similarity_percentage >= 50 ? 'text-amber-600' : 'text-indigo-600'}`}>
                {similarity_percentage}%
              </span>
              <span className="text-xs text-slate-500 font-medium">
                ({matching_answers_count} / {total_questions_compared} câu đóng)
              </span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500">
            {similarity_percentage >= 90 ? (
              <span className="text-rose-600 font-semibold flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Khả năng cao là phản hồi bản sao hoặc sao chép
              </span>
            ) : similarity_percentage >= 60 ? (
              <span className="text-amber-600 font-medium">
                Tương đồng đáng kể giữa hai đối tượng trả lời
              </span>
            ) : (
              <span className="text-slate-500">
                Phân bố câu trả lời có tính độc lập cao
              </span>
            )}
          </div>
        </div>

        {/* Response A Card */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">
              Phản hồi A: #{resp1Id.slice(0, 8)}
            </span>
            <button
              onClick={() => onNavigate(`/surveys/${surveyId}/responses/${resp1Id}`)}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1"
            >
              <span>Chi tiết</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {renderSourceBadge(resp1_meta?.source)}
            {renderRiskBadge(resp1_risk_score)}
          </div>
          <div className="space-y-1 text-xs text-slate-500 pt-1">
            {resp1_meta?.enumerator_id && (
              <div className="flex items-center gap-1 text-slate-700 font-medium">
                <User className="w-3 h-3 text-slate-400" />
                <span>Điều tra viên: <strong className="font-mono">{resp1_meta.enumerator_id}</strong></span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>Thời lượng: <strong>{resp1_meta?.duration_seconds ?? 'N/A'}s</strong></span>
            </div>
            <div>Trạng thái: {renderReviewStatus(resp1_meta?.review_status)}</div>
          </div>
        </div>

        {/* Response B Card */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">
              Phản hồi B: #{resp2Id.slice(0, 8)}
            </span>
            <button
              onClick={() => onNavigate(`/surveys/${surveyId}/responses/${resp2Id}`)}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1"
            >
              <span>Chi tiết</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {renderSourceBadge(resp2_meta?.source)}
            {renderRiskBadge(resp2_risk_score)}
          </div>
          <div className="space-y-1 text-xs text-slate-500 pt-1">
            {resp2_meta?.enumerator_id && (
              <div className="flex items-center gap-1 text-slate-700 font-medium">
                <User className="w-3 h-3 text-slate-400" />
                <span>Điều tra viên: <strong className="font-mono">{resp2_meta.enumerator_id}</strong></span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>Thời lượng: <strong>{resp2_meta?.duration_seconds ?? 'N/A'}s</strong></span>
            </div>
            <div>Trạng thái: {renderReviewStatus(resp2_meta?.review_status)}</div>
          </div>
        </div>
      </div>

      {/* Side-by-side Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3.5 px-6 w-1/3">Nội dung câu hỏi</th>
                <th className="py-3.5 px-6 w-1/4">Phản hồi A (#{resp1Id.slice(0, 6)})</th>
                <th className="py-3.5 px-6 w-1/4">Phản hồi B (#{resp2Id.slice(0, 6)})</th>
                <th className="py-3.5 px-4 text-center">Trạng thái</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredQuestions.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-400 text-sm">
                    Không có câu hỏi nào khớp với bộ lọc đã chọn.
                  </td>
                </tr>
              ) : (
                filteredQuestions.map((row: any, idx: number) => {
                  const isMatch = row.is_match;
                  return (
                    <tr
                      key={row.question_id || idx}
                      className={`transition-colors ${
                        isMatch ? 'bg-emerald-50/15' : 'bg-amber-50/15'
                      }`}
                    >
                      <td className="py-4 px-6">
                        <div className="font-semibold text-slate-900">{row.question_title}</div>
                        <span className="text-[11px] text-slate-400 font-mono">{row.question_type}</span>
                      </td>
                      <td className="py-4 px-6 font-medium text-slate-800">
                        {row.val_resp1 ? (
                          <span className={isMatch ? 'text-emerald-900 font-semibold' : 'text-slate-800'}>
                            {row.val_resp1}
                          </span>
                        ) : (
                          <span className="text-slate-300 italic">(Bỏ trống)</span>
                        )}
                      </td>
                      <td className="py-4 px-6 font-medium text-slate-800">
                        {row.val_resp2 ? (
                          <span className={isMatch ? 'text-emerald-900 font-semibold' : 'text-slate-800'}>
                            {row.val_resp2}
                          </span>
                        ) : (
                          <span className="text-slate-300 italic">(Bỏ trống)</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-center whitespace-nowrap">
                        {isMatch ? (
                          <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100/70 px-2.5 py-1 rounded-full">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Trùng
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-bold text-amber-700 bg-amber-100/70 px-2.5 py-1 rounded-full">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            Khác biệt
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};