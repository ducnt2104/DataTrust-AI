import React, { useEffect, useState } from 'react';
import { ArrowLeft, GitCompare, CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react';
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

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center text-slate-500 text-sm">
        Đang đối chiếu vector câu trả lời...
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
    similarity_percentage,
    matching_answers_count,
    total_questions_compared,
    questions_comparison
  } = data;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => onNavigate(`/surveys/${surveyId}/responses`)}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
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

      {/* Summary Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Độ tương đồng Hamming</span>
          <div className="text-3xl font-extrabold text-indigo-600">{similarity_percentage}%</div>
          <span className="text-xs text-slate-500">
            Trùng khớp {matching_answers_count} / {total_questions_compared} câu hỏi đóng
          </span>
        </div>

        <div className="space-y-1 p-3 bg-slate-50 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>Phản hồi A: #{resp1Id.slice(0, 8)}</span>
            <button
              onClick={() => onNavigate(`/surveys/${surveyId}/responses/${resp1Id}`)}
              className="text-indigo-600 hover:underline flex items-center gap-1"
            >
              <span>Xem</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <div className="text-lg font-bold text-slate-900">Rủi ro: {resp1_risk_score} / 100</div>
        </div>

        <div className="space-y-1 p-3 bg-slate-50 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>Phản hồi B: #{resp2Id.slice(0, 8)}</span>
            <button
              onClick={() => onNavigate(`/surveys/${surveyId}/responses/${resp2Id}`)}
              className="text-indigo-600 hover:underline flex items-center gap-1"
            >
              <span>Xem</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <div className="text-lg font-bold text-slate-900">Rủi ro: {resp2_risk_score} / 100</div>
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
              {questions_comparison.map((row: any, idx: number) => {
                const isMatch = row.is_match;
                return (
                  <tr
                    key={row.question_id || idx}
                    className={`transition-colors ${
                      isMatch ? 'bg-emerald-50/20' : 'bg-amber-50/20'
                    }`}
                  >
                    <td className="py-4 px-6">
                      <div className="font-semibold text-slate-900">{row.question_title}</div>
                      <span className="text-[11px] text-slate-400 font-mono">{row.question_type}</span>
                    </td>
                    <td className="py-4 px-6 font-medium text-slate-800">
                      {row.val_resp1 || <span className="text-slate-300 italic">(Bỏ trống)</span>}
                    </td>
                    <td className="py-4 px-6 font-medium text-slate-800">
                      {row.val_resp2 || <span className="text-slate-300 italic">(Bỏ trống)</span>}
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
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
