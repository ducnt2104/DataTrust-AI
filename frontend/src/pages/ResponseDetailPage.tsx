import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Clock,
  GitCompare,
  Save,
  CheckCircle2,
  XCircle,
  HelpCircle
} from 'lucide-react';
import { api } from '../api/client';
import { ResponseDetail } from '../types/survey';
import { RiskBadge } from '../components/RiskBadge';

interface Props {
  surveyId: string;
  responseId: string;
  onNavigate: (path: string) => void;
}

export const ResponseDetailPage: React.FC<Props> = ({ surveyId, responseId, onNavigate }) => {
  const [detail, setDetail] = useState<ResponseDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Verification state
  const [reviewStatus, setReviewStatus] = useState<string>('unverified');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [updating, setUpdating] = useState(false);
  const [updateMsg, setUpdateMsg] = useState<string | null>(null);

  useEffect(() => {
    loadResponse();
  }, [surveyId, responseId]);

  const loadResponse = async () => {
    try {
      setLoading(true);
      const data = await api.getResponseDetail(surveyId, responseId);
      setDetail(data);
      setReviewStatus(data.review_status);
      setReviewNotes(data.review_notes || '');
    } catch (err) {
      console.error(err);
      alert('Không thể tải chi tiết phản hồi.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDecision = async () => {
    try {
      setUpdating(true);
      await api.updateReviewDecision(surveyId, responseId, reviewStatus, reviewNotes);
      setUpdateMsg('Đã ghi nhận quyết định xác minh thành công.');
      setTimeout(() => setUpdateMsg(null), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi cập nhật quyết định');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center text-slate-500 text-sm">
        Đang tải hồ sơ phản hồi...
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="p-8 text-center text-slate-500">
        Không tìm thấy phản hồi.
      </div>
    );
  }

  const { assessment } = detail;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/responses`)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Chi tiết phản hồi #{detail.id.slice(0, 8)}
              </h1>
              <RiskBadge score={detail.risk_score} level={detail.risk_level} />
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Khảo sát: {detail.survey_title} (v{detail.survey_version}) • Gửi lúc: {new Date(detail.submitted_at).toLocaleString()}
            </p>
          </div>
        </div>

        {assessment?.closest_match_response_id && (
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/compare?resp1=${detail.id}&resp2=${assessment.closest_match_response_id}`)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all"
          >
            <GitCompare className="w-4 h-4" />
            <span>So sánh với phản hồi tương đồng ({Math.round(assessment.highest_similarity * 100)}%)</span>
          </button>
        )}
      </div>

      {/* Grid: Quality Assessment & Verification Decision */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Quality Assessment & Flags */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Breakdown Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-indigo-600" />
                <span>Đánh giá rủi ro DataTrust AI (Explainable Breakdown)</span>
              </h3>
              <span className="text-xs font-semibold text-slate-500">
                Thời lượng làm: <strong className="text-slate-900">{detail.duration_seconds} giây</strong>
              </span>
            </div>

            {/* Source & Metadata Banner */}
            <div className="flex flex-wrap items-center gap-3 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-slate-700">
              <span>Nguồn thu thập: <strong className="text-slate-900">{detail.source === 'paper_scan' ? 'Phiếu giấy (Mobile OMR)' : detail.source === 'csv_import' ? 'Nhập từ CSV' : 'Biểu mẫu trực tuyến (Web)'}</strong></span>
              {detail.enumerator_id && <span>• Điều tra viên: <strong className="text-slate-900 font-mono">{detail.enumerator_id}</strong></span>}
              {detail.paper_form_id && <span>• Mã phiếu cứng: <strong className="text-slate-900 font-mono">{detail.paper_form_id}</strong></span>}
              {detail.omr_confidence !== undefined && detail.source === 'paper_scan' && (
                <span>• Độ tin cậy OMR: <strong className="text-emerald-700 font-mono">{Math.round(detail.omr_confidence * 100)}%</strong></span>
              )}
            </div>

            {assessment && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-[11px] text-slate-500 font-medium block">Trùng lặp (S_dup)</span>
                  <span className={`text-base font-bold ${assessment.score_dup > 50 ? 'text-rose-600' : 'text-slate-800'}`}>
                    {assessment.score_dup}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-[11px] text-slate-500 font-medium block">Mẫu trả lời (S_pat)</span>
                  <span className={`text-base font-bold ${assessment.score_pattern > 50 ? 'text-amber-600' : 'text-slate-800'}`}>
                    {assessment.score_pattern}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-[11px] text-slate-500 font-medium block">Logic chéo (S_logic)</span>
                  <span className={`text-base font-bold ${assessment.score_logic > 50 ? 'text-rose-600' : 'text-slate-800'}`}>
                    {assessment.score_logic}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-[11px] text-slate-500 font-medium block">Tốc độ (S_speed)</span>
                  <span className={`text-base font-bold ${assessment.score_speed > 50 ? 'text-amber-600' : 'text-slate-800'}`}>
                    {assessment.score_speed}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-[11px] text-slate-500 font-medium block">ĐTV/Nhóm (S_enum)</span>
                  <span className={`text-base font-bold ${(assessment.score_enum || 0) > 50 ? 'text-rose-600' : 'text-slate-800'}`}>
                    {assessment.score_enum || 0}
                  </span>
                </div>
              </div>
            )}

            {/* Flags list */}
            {assessment && assessment.flags.length > 0 ? (
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Các cờ cảnh báo phát hiện ({assessment.flags.length})
                </span>
                <div className="space-y-2">
                  {assessment.flags.map((flag, idx) => (
                    <div
                      key={idx}
                      className={`p-3.5 rounded-xl border text-xs space-y-1 ${
                        flag.severity === 'CRITICAL' || flag.severity === 'HIGH'
                          ? 'bg-rose-50/70 border-rose-200 text-rose-900'
                          : 'bg-amber-50/70 border-amber-200 text-amber-900'
                      }`}
                    >
                      <div className="flex items-center justify-between font-bold">
                        <span>[{flag.code}]</span>
                        <span className="uppercase text-[10px] tracking-wider px-2 py-0.5 rounded-full bg-white/70">
                          {flag.severity}
                        </span>
                      </div>
                      <p className="leading-relaxed">{flag.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-emerald-50 text-emerald-800 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Không phát hiện dấu hiệu bất thường nào. Dữ liệu tự nhiên và hợp lệ.</span>
              </div>
            )}
          </div>

          {/* Original Answers Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">
              Câu trả lời gốc từ người tham gia
            </h3>

            <div className="space-y-4">
              {detail.questions.map((q, idx) => {
                const ans = detail.answers[q.id];
                const displayVal = ans !== undefined && ans !== null ? (typeof ans === 'object' ? JSON.stringify(ans) : String(ans)) : '(Bỏ trống)';
                return (
                  <div key={q.id} className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200/60 space-y-1">
                    <span className="text-xs text-indigo-600 font-semibold block">
                      Câu {idx + 1}: {q.title}
                    </span>
                    <div className="text-sm font-medium text-slate-900 pt-0.5">
                      {displayVal}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): Human-in-the-Loop Review Decision */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4 sticky top-24">
            <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Quyết định xác minh (Human Review)</span>
            </h3>

            <p className="text-xs text-slate-500 leading-relaxed">
              Điểm rủi ro chỉ là chỉ báo gợi ý. Người quản trị có toàn quyền thẩm định bằng chứng và đưa ra quyết định chấp nhận hoặc loại bỏ.
            </p>

            {/* Status Options */}
            <div className="space-y-2">
              {[
                { id: 'verified_valid', label: 'Hợp lệ sau xác minh (Chấp thuận)', desc: 'Đưa vào bộ dữ liệu sạch chính thức' },
                { id: 'verified_fraud', label: 'Bị loại sau xác minh', desc: 'Loại bỏ khỏi báo cáo phân tích' },
                { id: 'under_review', label: 'Cần xem xét thêm', desc: 'Đang chờ đối chiếu thông tin' },
                { id: 'unverified', label: 'Chưa duyệt', desc: 'Trạng thái mặc định ban đầu' }
              ].map((opt) => (
                <label
                  key={opt.id}
                  className={`block p-3 rounded-xl border cursor-pointer text-xs transition-all ${
                    reviewStatus === opt.id
                      ? 'border-indigo-600 bg-indigo-50/60 text-indigo-950 font-semibold'
                      : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="review_decision"
                      value={opt.id}
                      checked={reviewStatus === opt.id}
                      onChange={(e) => setReviewStatus(e.target.value)}
                      className="w-3.5 h-3.5 text-indigo-600"
                    />
                    <span>{opt.label}</span>
                  </div>
                  <span className="block text-[11px] text-slate-400 mt-1 pl-5 font-normal">
                    {opt.desc}
                  </span>
                </label>
              ))}
            </div>

            {/* Review Notes */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
                Ghi chú thẩm định
              </label>
              <textarea
                rows={3}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Nhập lý do hoặc căn cứ quyết định..."
                className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-600 focus:outline-hidden"
              />
            </div>

            {updateMsg && (
              <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-medium">
                {updateMsg}
              </div>
            )}

            <button
              onClick={handleSaveDecision}
              disabled={updating}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{updating ? 'Đang lưu...' : 'Ghi nhận quyết định'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
