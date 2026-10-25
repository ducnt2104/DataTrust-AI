import React, { useState } from 'react';
import { Sparkles, MessageSquare, ThumbsUp, ThumbsDown, Minus, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { AIQualitativeAnalysis } from '../types/survey';

interface Props {
  surveyId: string;
}

export const AIQualitativeInsightsCard: React.FC<Props> = ({ surveyId }) => {
  const [data, setData] = useState<AIQualitativeAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.analyzeQualitativeResponses(surveyId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Không thể phân tích dữ liệu định tính');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-violet-50 text-violet-600 border border-violet-100">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm">AI Qualitative Analysis & Sentiment Insights</h3>
            <p className="text-xs text-slate-500">Phân tích sắc thái tình cảm & trích xuất chủ đề từ phản hồi văn bản mở</p>
          </div>
        </div>

        <button
          onClick={fetchAnalysis}
          disabled={loading}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-violet-600 text-white hover:bg-violet-700 shadow-2xs transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Đang phân tích...' : data ? 'Cập nhật phân tích' : 'Chạy phân tích AI'}</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
          {error}
        </div>
      )}

      {!data && !loading && !error && (
        <div className="text-center py-6 text-slate-400 space-y-2">
          <MessageSquare className="w-8 h-8 mx-auto text-slate-300" />
          <p className="text-xs">Nhấn nút "Chạy phân tích AI" để tự động phân cụm ngữ nghĩa và phân loại sắc thái câu trả lời tự do.</p>
        </div>
      )}

      {data && (
        <div className="space-y-4 animate-in fade-in duration-200 text-xs">
          {/* Sentiment overview */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200/80 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100 text-emerald-700">
                <ThumbsUp className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-emerald-800 tracking-wider">Tích cực (Positive)</span>
                <div className="text-base font-bold text-emerald-950">{data.sentiment_distribution.positive} phản hồi</div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-200/80 text-slate-600">
                <Minus className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wider">Trung lập (Neutral)</span>
                <div className="text-base font-bold text-slate-900">{data.sentiment_distribution.neutral} phản hồi</div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-rose-50/70 border border-rose-200/80 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-rose-100 text-rose-700">
                <ThumbsDown className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-rose-800 tracking-wider">Tiêu cực (Negative)</span>
                <div className="text-base font-bold text-rose-950">{data.sentiment_distribution.negative} phản hồi</div>
              </div>
            </div>
          </div>

          {/* Key themes */}
          {data.key_themes.length > 0 && (
            <div className="space-y-2 pt-1">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                Chủ đề then chốt được trích xuất (Key Extracted Themes)
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {data.key_themes.map((theme, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 text-xs">{theme.theme_name}</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                        theme.sentiment === 'positive'
                          ? 'bg-emerald-100 text-emerald-800'
                          : theme.sentiment === 'negative'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-200 text-slate-700'
                      }`}>
                        {theme.sentiment} • ~{theme.prevalence_percent}%
                      </span>
                    </div>
                    {theme.sample_quotes.length > 0 && (
                      <div className="space-y-1">
                        {theme.sample_quotes.map((q, qIdx) => (
                          <div key={qIdx} className="text-slate-600 italic text-[11px] bg-white p-2 rounded-lg border border-slate-200/60">
                            "{q}"
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Anomaly warnings if any */}
          {data.anomaly_flags && data.anomaly_flags.length > 0 && data.anomaly_flags[0] !== 'NO_DATA' && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-xs text-amber-900">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <span>Cảnh báo dữ liệu văn bản bất thường (Text Anomalies):</span>
              </div>
              <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                {data.anomaly_flags.map((flag, fIdx) => (
                  <li key={fIdx}>{flag}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="text-[11px] text-slate-400 italic pt-1 border-t border-slate-100">
            {data.methodology_summary}
          </div>
        </div>
      )}
    </div>
  );
};
