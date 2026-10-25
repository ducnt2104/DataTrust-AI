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
  Download,
  FileText,
  Globe,
  Sparkles,
  FlaskConical,
  Network,
  ShieldAlert,
  RotateCcw
} from 'lucide-react';
import { api } from '../api/client';
import { ResponseListItem } from '../types/survey';
import { RiskBadge } from '../components/RiskBadge';
import { DataCleansingModal } from '../components/DataCleansingModal';
import { PairwiseSimilarityCard } from '../components/PairwiseSimilarityCard';

interface Props {
  surveyId: string;
  onNavigate: (path: string) => void;
}

export const ResponsesListPage: React.FC<Props> = ({ surveyId, onNavigate }) => {
  const [responses, setResponses] = useState<ResponseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [reviewFilter, setReviewFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [batchActing, setBatchActing] = useState<boolean>(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [isCleansingOpen, setIsCleansingOpen] = useState<boolean>(false);
  const [seeding, setSeeding] = useState<boolean>(false);
  const [showSimilarityMatrix, setShowSimilarityMatrix] = useState<boolean>(false);
  const [quarantining, setQuarantining] = useState<boolean>(false);
  const [restoring, setRestoring] = useState<boolean>(false);

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

  const handleSeedResponses = async () => {
    try {
      setSeeding(true);
      const res = await api.seedSurveyResponses(surveyId, 15);
      await fetchResponses();
      setToastMsg(`🧪 ${res.message}`);
      setTimeout(() => setToastMsg(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi nạp phản hồi mẫu');
    } finally {
      setSeeding(false);
    }
  };

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((x) => x !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleSelectAllFiltered = () => {
    const filtered = responses.filter((r) => {
      if (sourceFilter === 'all') return true;
      return (r.source || 'online_form') === sourceFilter;
    });
    if (selectedIds.length === filtered.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filtered.map((r) => r.id));
    }
  };

  const handleSelectAllClean = () => {
    const clean = responses.filter((r) => {
      const matchSource = sourceFilter === 'all' || (r.source || 'online_form') === sourceFilter;
      return matchSource && r.risk_level === 'low';
    });
    setSelectedIds(clean.map((r) => r.id));
  };

  const handleBatchDecision = async (status: string, label: string) => {
    if (selectedIds.length === 0) return;
    try {
      setBatchActing(true);
      const res = await api.batchUpdateReviewDecision(
        surveyId,
        selectedIds,
        status,
        `Thẩm định hàng loạt (${label}) lúc ${new Date().toLocaleTimeString('vi-VN')}`
      );
      setToastMsg(res.message);
      setTimeout(() => setToastMsg(null), 4000);
      setSelectedIds([]);
      await fetchResponses();
    } catch (err: any) {
      alert(err.message || 'Lỗi khi cập nhật trạng thái hàng loạt');
    } finally {
      setBatchActing(false);
    }
  };

  const handleRunCompare = () => {
    if (selectedIds.length === 2) {
      onNavigate(`/surveys/${surveyId}/compare?resp1=${selectedIds[0]}&resp2=${selectedIds[1]}`);
    }
  };

  const fraudCount = responses.filter(r => r.review_status === 'verified_fraud').length;

  const handleBatchQuarantine = async () => {
    if (!window.confirm('Kích hoạt quy trình cách ly gian lận tự động (Collusion Rings, Coffee-Shop GPS, Speeders)? Tất cả phản hồi bất thường sẽ được chuyển sang trạng thái Bị Loại (verified_fraud) và ghi nhận vào chuỗi băm kiểm toán SHA-256.')) {
      return;
    }
    try {
      setQuarantining(true);
      const res = await api.batchQuarantineAnomalies(surveyId, {
        quarantine_syndicates: true,
        quarantine_coffee_shop: true,
        quarantine_impossible_velocity: true,
        quarantine_speeders: true,
        quarantine_straightlining: true,
        min_risk_score: 75.0,
        action: 'verified_fraud',
        dry_run: false
      });
      setToastMsg(`Đã cách ly thành công ${res.quarantined_count} phiếu bất thường trên tổng số ${res.total_evaluated} phiếu!`);
      fetchResponses();
    } catch (err: any) {
      alert(err.message || 'Lỗi khi cách ly gian lận');
    } finally {
      setQuarantining(false);
    }
  };

  const handleBatchRestore = async () => {
    if (!window.confirm('Khôi phục toàn bộ phiếu đã bị cách ly/bị loại về trạng thái Chưa duyệt (unverified)? Hành động này sẽ được ghi nhận vào nhật ký kiểm toán bất biến.')) {
      return;
    }
    try {
      setRestoring(true);
      const res = await api.batchRestoreQuarantined(surveyId, {
        restore_to_status: 'unverified',
        reason: 'Khôi phục hàng loạt bởi kiểm toán viên'
      });
      setToastMsg(`Đã khôi phục thành công ${res.restored_count} phiếu về trạng thái Chưa duyệt!`);
      fetchResponses();
    } catch (err: any) {
      alert(err.message || 'Lỗi khi khôi phục');
    } finally {
      setRestoring(false);
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
          {selectedIds.length === 2 && (
            <button
              onClick={handleRunCompare}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all animate-bounce"
            >
              <GitCompare className="w-4 h-4" />
              <span>Đối chiếu 2 phản hồi đã chọn</span>
            </button>
          )}
          <button
            onClick={handleSeedResponses}
            disabled={seeding}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 transition-all disabled:opacity-50"
            title="Nạp 15 phản hồi mẫu thực tế vào khảo sát này để thử nghiệm đối soát và kiểm định"
          >
            <FlaskConical className="w-4 h-4 text-teal-600" />
            <span>{seeding ? 'Đang nạp...' : 'Nạp 15 mẫu (Seed)'}</span>
          </button>
          <button
            onClick={handleBatchQuarantine}
            disabled={quarantining}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 transition-all disabled:opacity-50"
            title="Quét và cách ly tự động toàn bộ mạng lưới thông đồng, cụm quán cà phê, và phản hồi siêu tốc"
          >
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <span>{quarantining ? 'Đang cách ly...' : 'Cách ly gian lận (AI)'}</span>
          </button>
          {fraudCount > 0 && (
            <button
              onClick={handleBatchRestore}
              disabled={restoring}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition-all disabled:opacity-50"
              title="Khôi phục các phiếu đã bị loại về trạng thái Chưa duyệt"
            >
              <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
              <span>{restoring ? 'Đang khôi phục...' : `Khôi phục (${fraudCount})`}</span>
            </button>
          )}
          <button
            onClick={() => setIsCleansingOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-all"
          >
            <Sparkles className="w-4 h-4 text-emerald-200" />
            <span>Làm sạch dữ liệu tự động</span>
          </button>
          <button
            onClick={() => setShowSimilarityMatrix(!showSimilarityMatrix)}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all ${
              showSimilarityMatrix
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                : 'bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border-indigo-200'
            }`}
            title="Quét ma trận tương đồng cặp và phát hiện mạng lưới thông đồng (bot farm, chung thiết bị/IP)"
          >
            <Network className="w-4 h-4" />
            <span>{showSimilarityMatrix ? 'Đóng Ma Trận Tương Đồng' : 'Ma Trận & Bot Rings'}</span>
          </button>
          <button
            onClick={() => onNavigate(`/surveys/${surveyId}/export`)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Xuất dữ liệu</span>
          </button>
        </div>
      </div>

      {/* Expandable Pairwise Similarity Matrix & Collusion Syndicate Engine */}
      {showSimilarityMatrix && (
        <div className="animate-in fade-in slide-in-from-top-2 duration-300">
          <PairwiseSimilarityCard surveyId={surveyId} />
        </div>
      )}

      {/* Toast Notification */}
      {toastMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold flex items-center gap-2 animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Batch Review Action Bar */}
      {selectedIds.length > 0 && (
        <div className="bg-slate-900 text-white p-3.5 px-5 rounded-2xl flex flex-wrap items-center justify-between gap-3 shadow-lg border border-slate-800 animate-in slide-in-from-top duration-200">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold">
              Đã chọn <span className="text-emerald-300 font-mono text-sm">{selectedIds.length}</span> phản hồi:
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleBatchDecision('verified_valid', 'Duyệt hợp lệ')}
              disabled={batchActing}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-xs transition-all disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{batchActing ? 'Đang cập nhật...' : `Duyệt Hợp Lệ (${selectedIds.length})`}</span>
            </button>
            <button
              onClick={() => handleBatchDecision('verified_fraud', 'Đánh dấu loại bỏ')}
              disabled={batchActing}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-xs transition-all disabled:opacity-50"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Đánh Dấu Bị Loại</span>
            </button>
            <button
              onClick={() => handleBatchDecision('under_review', 'Chuyển xem xét')}
              disabled={batchActing}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold shadow-xs transition-all disabled:opacity-50"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Cần Xem Xét Lại</span>
            </button>
            {selectedIds.length === 2 && (
              <button
                onClick={handleRunCompare}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-xs transition-all"
              >
                <GitCompare className="w-3.5 h-3.5" />
                <span>Đối Chiếu Cạnh Nhau</span>
              </button>
            )}
            <button
              onClick={() => setSelectedIds([])}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
            >
              Bỏ chọn
            </button>
          </div>
        </div>
      )}

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

        {/* Source Filter */}
        <div className="flex items-center gap-1 text-xs">
          <span className="font-semibold text-slate-500 mr-2 uppercase tracking-wider">Nguồn:</span>
          {[
            { id: 'all', label: 'Tất cả' },
            { id: 'online_form', label: 'Trực tuyến' },
            { id: 'paper_scan', label: 'Phiếu giấy' },
            { id: 'csv_import', label: 'Tệp CSV' }
          ].map((src) => (
            <button
              key={src.id}
              onClick={() => setSourceFilter(src.id)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                sourceFilter === src.id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 hover:bg-slate-200/70 text-slate-600'
              }`}
            >
              {src.label}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Select Bar */}
      <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 px-1 gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={handleSelectAllFiltered}
            className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition-all"
          >
            {selectedIds.length > 0 && selectedIds.length === responses.filter(r => sourceFilter === 'all' || (r.source || 'online_form') === sourceFilter).length
              ? 'Bỏ chọn tất cả'
              : `Chọn tất cả (${responses.filter(r => sourceFilter === 'all' || (r.source || 'online_form') === sourceFilter).length})`}
          </button>
          <button
            onClick={handleSelectAllClean}
            className="px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold border border-emerald-200 transition-all flex items-center gap-1.5"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Chọn nhanh phản hồi an toàn (Low Risk)</span>
          </button>
        </div>
        <div>
          <span>Tổng số: <strong className="text-slate-800">{responses.length}</strong> phản hồi</span>
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
                  <th className="py-3.5 px-4 w-10">
                    <input
                      type="checkbox"
                      checked={
                        responses.length > 0 &&
                        selectedIds.length === responses.filter(r => sourceFilter === 'all' || (r.source || 'online_form') === sourceFilter).length
                      }
                      onChange={handleSelectAllFiltered}
                      className="w-4 h-4 text-indigo-600 rounded-sm border-slate-300 focus:ring-indigo-500 cursor-pointer"
                      title="Chọn / Bỏ chọn tất cả"
                    />
                  </th>
                  <th className="py-3.5 px-4">Mã phản hồi</th>
                  <th className="py-3.5 px-4">Nguồn</th>
                  <th className="py-3.5 px-4">Thời điểm gửi</th>
                  <th className="py-3.5 px-4">Thời lượng</th>
                  <th className="py-3.5 px-4">Điểm rủi ro</th>
                  <th className="py-3.5 px-4">Cờ cảnh báo</th>
                  <th className="py-3.5 px-4">Xác minh</th>
                  <th className="py-3.5 px-6 text-right">Chi tiết</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {responses
                  .filter((r) => {
                    if (sourceFilter === 'all') return true;
                    return (r.source || 'online_form') === sourceFilter;
                  })
                  .map((resp) => {
                  const isChecked = selectedIds.includes(resp.id);
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
                          onChange={() => toggleSelect(resp.id)}
                          className="w-4 h-4 text-indigo-600 rounded-sm border-slate-300 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="py-4 px-4 font-mono text-xs font-bold text-slate-800">
                        {resp.id.slice(0, 8)}...
                      </td>
                      <td className="py-4 px-4 text-xs whitespace-nowrap">
                        {resp.source === 'paper_scan' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                            <FileText className="w-3 h-3" /> Phiếu giấy {resp.enumerator_id ? `(${resp.enumerator_id})` : ''}
                          </span>
                        ) : resp.source === 'csv_import' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 font-semibold">
                            Tệp CSV
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                            <Globe className="w-3 h-3" /> Trực tuyến
                          </span>
                        )}
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

      {/* Modal Làm sạch Dữ liệu Tự động */}
      <DataCleansingModal
        surveyId={surveyId}
        isOpen={isCleansingOpen}
        onClose={() => setIsCleansingOpen(false)}
        onSuccess={() => {
          fetchResponses();
          setToastMsg('Quy trình làm sạch dữ liệu tự động đã được áp dụng và lưu vết kiểm toán thành công!');
          setTimeout(() => setToastMsg(null), 6000);
        }}
      />
    </div>
  );
};
