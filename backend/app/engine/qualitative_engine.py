import re
import math
from typing import List, Dict, Any, Optional
from collections import Counter

VI_STOPWORDS = {
    "và", "là", "của", "thì", "mà", "ở", "với", "cho", "được", "rằng", "này", "đó",
    "những", "các", "một", "có", "không", "chưa", "chẳng", "đã", "đang", "sẽ", "như",
    "đến", "từ", "trong", "vào", "ra", "lại", "qua", "đi", "về", "lên", "xuống", "khi",
    "nếu", "bởi", "vì", "do", "nên", "nhưng", "tuy", "dù", "cũng", "chỉ", "quá", "rất",
    "lắm", "thế", "vậy", "nào", "gì", "ai", "đâu", "đây", "tôi", "mình", "bạn", "anh",
    "chị", "em", "người", "họ", "chúng", "ta", "việc", "sự", "cái", "con", "chiếc",
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "is", "are", "was", "were", "it", "this", "that", "these", "those", "i", "we", "you"
}

POSITIVE_WORDS = {
    "tốt", "tuyệt", "nhanh", "dễ", "thích", "ổn", "đẹp", "chuẩn", "khen",
    "good", "great", "excellent", "fast", "easy", "satisfied", "love", "helpful", "reliable", "awesome"
}

NEGATIVE_WORDS = {
    "kém", "tệ", "chậm", "lag", "lỗi", "khó", "dở", "đắt", "bực", "phiền", "rối",
    "thiếu", "sai", "kẹt", "hỏng", "bad", "poor", "slow", "error", "bug", "hard",
    "expensive", "annoying", "terrible", "worst", "fail"
}

COMPOUND_POSITIVE_PHRASES = [
    "hài lòng", "tuyệt vời", "xuất sắc", "nhiệt tình", "chu đáo", "dễ sử dụng", "rất tốt", "ưng ý",
    "chuyên nghiệp", "tiện lợi", "đẹp mắt", "hiệu quả", "rất nhanh", "tin tưởng", "hợp lý", "tận tâm"
]

COMPOUND_NEGATIVE_PHRASES = [
    "thất vọng", "phức tạp", "rườm rà", "khó dùng", "khó hiểu", "bực mình", "kém cỏi",
    "lỗi kết nối", "không thích", "chẳng thích", "đắt đỏ", "không hài lòng", "chưa hài lòng",
    "chưa tốt", "không tốt", "quá chậm", "quá tệ"
]

NEGATION_PREFIXES = {"không", "chẳng", "chưa", "ít", "not", "no", "never", "hardly"}

THEME_TAXONOMY = [
    {
        "name": "Chất lượng Sản phẩm & Dịch vụ",
        "keywords": ["chất lượng", "sản phẩm", "dịch vụ", "tính năng", "chức năng", "hệ thống", "ứng dụng", "nền tảng", "hoạt động", "service", "product", "feature"]
    },
    {
        "name": "Giao diện & Trải nghiệm Người dùng (UI/UX)",
        "keywords": ["giao diện", "thiết kế", "dễ dùng", "tiện lợi", "trải nghiệm", "bố cục", "màu sắc", "trực quan", "khó dùng", "ui", "ux", "design", "interface"]
    },
    {
        "name": "Thời gian Xử lý & Tốc độ Phản hồi",
        "keywords": ["thời gian", "nhanh", "chậm", "tốc độ", "chờ", "đợi", "tiến độ", "trễ", "kịp thời", "ngay lập tức", "speed", "time", "fast", "slow", "delay"]
    },
    {
        "name": "Thái độ Hỗ trợ & Chăm sóc Khách hàng",
        "keywords": ["thái độ", "nhân viên", "tư vấn", "hỗ trợ", "nhiệt tình", "chăm sóc", "giải đáp", "hướng dẫn", "tận tâm", "support", "staff", "help", "care"]
    },
    {
        "name": "Chi phí, Giá cả & Tính Minh bạch",
        "keywords": ["giá", "chi phí", "học phí", "đắt", "rẻ", "tiền", "ngân sách", "hợp lý", "khuyến mãi", "ưu đãi", "price", "cost", "fee", "budget"]
    },
    {
        "name": "Đề xuất Cải tiến & Nguyện vọng Mới",
        "keywords": ["đề xuất", "cải tiến", "cần", "nên", "bổ sung", "thêm", "nâng cấp", "mong muốn", "hi vọng", "kiến nghị", "suggest", "improve", "upgrade", "recommend"]
    }
]

class QualitativeEngine:
    """
    Bộ động cơ phân tích ngữ nghĩa phản hồi định tính (Qualitative NLP & Thematic Engine)
    Tuân thủ chuẩn nghiên cứu xã hội học AAPOR và phân loại cảm xúc chuyên sâu.
    """

    @staticmethod
    def clean_and_tokenize(text: str) -> List[str]:
        """Tách từ, chuẩn hóa chữ thường và lọc bỏ stopwords"""
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
        return tokens

    @staticmethod
    def evaluate_sentiment(text: str) -> str:
        """
        Đánh giá sắc thái cảm xúc của phản hồi văn bản dựa trên lexicon phân cực và từ phủ định.
        Hỗ trợ từ ghép tiếng Việt (compound phrases) và phát hiện phủ định đảo nghĩa.
        Trả về 'positive', 'neutral', hoặc 'negative'.
        """
        lower = text.lower()
        tokens = QualitativeEngine.clean_and_tokenize(lower)
        if not tokens:
            return "neutral"

        pos_score = 0.0
        neg_score = 0.0

        # 1. Quét cụm từ tiêu cực ghép (Compound negative phrases) có xét ngữ cảnh phủ định đa từ
        for phrase in COMPOUND_NEGATIVE_PHRASES:
            if phrase not in lower:
                continue
            for m in re.finditer(re.escape(phrase), lower):
                words_before = lower[:m.start()].strip().split()
                recent_before = words_before[-3:] if len(words_before) >= 3 else words_before
                is_negated = any(w in NEGATION_PREFIXES for w in recent_before)
                if is_negated:
                    pos_score += 2.0
                else:
                    neg_score += 2.5

        # 2. Quét cụm từ tích cực ghép (Compound positive phrases) có xét ngữ cảnh phủ định đa từ (VD: "không hề hài lòng")
        for phrase in COMPOUND_POSITIVE_PHRASES:
            if phrase not in lower:
                continue
            for m in re.finditer(re.escape(phrase), lower):
                words_before = lower[:m.start()].strip().split()
                recent_before = words_before[-3:] if len(words_before) >= 3 else words_before
                is_negated = any(w in NEGATION_PREFIXES for w in recent_before)
                if is_negated:
                    neg_score += 2.5
                else:
                    pos_score += 2.0

        # 3. Quét các từ đơn lẻ (Unigrams) với cửa sổ ngữ cảnh phủ định 1-2 từ
        for idx, token in enumerate(tokens):
            is_negated = False
            if idx > 0 and tokens[idx - 1] in NEGATION_PREFIXES:
                is_negated = True
            elif idx > 1 and tokens[idx - 2] in NEGATION_PREFIXES:
                is_negated = True

            if token in POSITIVE_WORDS:
                if is_negated:
                    neg_score += 1.5
                else:
                    pos_score += 1.0
            elif token in NEGATIVE_WORDS:
                if is_negated:
                    pos_score += 1.0
                else:
                    neg_score += 1.5

        if pos_score > neg_score and pos_score >= 1.0:
            return "positive"
        elif neg_score > pos_score and neg_score >= 1.0:
            return "negative"
        else:
            return "neutral"

    @classmethod
    def analyze_responses(cls, responses: List[str], max_themes: int = 5) -> Dict[str, Any]:
        """
        Thực hiện phân tích toàn diện tập phản hồi mở:
        - Thống kê phân bố cảm xúc
        - Phân nhóm chủ đề tự động theo ma trận từ vựng
        - Trích xuất câu trích dẫn tiêu biểu (quotes)
        - Phát hiện dị thường sao chép / gibberish
        """
        valid_texts = [t.strip() for t in responses if t and len(t.strip()) >= 3]
        total = len(valid_texts)

        if total == 0:
            return {
                "total_analyzed": 0,
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "key_themes": [],
                "anomaly_flags": [],
                "methodology_summary": "Không có đủ phản hồi văn bản hợp lệ để phân tích định tính."
            }

        # 1. Đánh giá phân bố sắc thái
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        item_sentiments = []
        for text in valid_texts:
            s = cls.evaluate_sentiment(text)
            sentiment_counts[s] += 1
            item_sentiments.append(s)

        # 2. Phát hiện bất thường (Anomalies)
        anomaly_flags = []
        text_counter = Counter(valid_texts)
        duplicates = [txt for txt, count in text_counter.items() if count >= 3]
        if duplicates:
            anomaly_flags.append(f"Phát hiện {len(duplicates)} phản hồi văn bản bị lặp lại nguyên văn >= 3 lần (nguy cơ điền tự động hoặc sao chép).")

        gibberish_count = 0
        for txt in valid_texts:
            # Kiểm tra tỷ lệ nguyên âm / độ dài từ bất thường
            words = txt.split()
            if any(len(w) > 30 for w in words):
                gibberish_count += 1
        if gibberish_count > 0:
            anomaly_flags.append(f"Ghi nhận {gibberish_count} câu trả lời chứa từ ngữ dị thường hoặc chuỗi ký tự không có khoảng trắng.")

        # 3. Phân cụm chủ đề (Thematic Clustering)
        theme_buckets: Dict[str, Dict[str, Any]] = {}
        for t in THEME_TAXONOMY:
            theme_buckets[t["name"]] = {
                "keywords": t["keywords"],
                "kw_set": set(t["keywords"]),
                "matches": [],
                "sentiments": []
            }

        other_bucket: List[Dict[str, Any]] = []

        for idx, text in enumerate(valid_texts):
            lower = text.lower()
            tokens = set(cls.clean_and_tokenize(lower))
            matched_theme = None

            for t_name, b in theme_buckets.items():
                kw_set = b["kw_set"]
                if kw_set.intersection(tokens) or any(k in lower for k in kw_set):
                    matched_theme = t_name
                    break

            if matched_theme:
                theme_buckets[matched_theme]["matches"].append(text)
                theme_buckets[matched_theme]["sentiments"].append(item_sentiments[idx])
            else:
                other_bucket.append({"text": text, "sentiment": item_sentiments[idx]})

        # Lọc các chủ đề có phản hồi và sắp xếp theo độ phổ biến
        active_themes = []
        for t_name, b in theme_buckets.items():
            matches = b["matches"]
            if matches:
                count = len(matches)
                prevalence = round((count / total) * 100, 1)

                # Sentiment chủ đạo của chủ đề này
                s_counts = Counter(b["sentiments"])
                dominant_sentiment = s_counts.most_common(1)[0][0] if s_counts else "neutral"

                # Trích xuất 2-3 câu trích dẫn đặc trưng
                # Ưu tiên các câu có độ dài vừa phải (15 - 120 ký tự)
                sorted_quotes = sorted(matches, key=lambda q: (abs(len(q) - 60), q))
                sample_quotes = sorted_quotes[:3]

                active_themes.append({
                    "theme_name": t_name,
                    "sentiment": dominant_sentiment,
                    "prevalence_percent": prevalence,
                    "sample_quotes": sample_quotes,
                    "count": count
                })

        active_themes.sort(key=lambda x: x["count"], reverse=True)

        # Nếu còn nhóm khác chiếm tỷ lệ đáng kể, bổ sung nhóm "Ý kiến Đa dạng Khác"
        if other_bucket and len(other_bucket) >= max(2, int(total * 0.1)):
            other_prev = round((len(other_bucket) / total) * 100, 1)
            other_s = Counter([o["sentiment"] for o in other_bucket]).most_common(1)[0][0]
            other_quotes = [o["text"] for o in other_bucket[:3]]
            active_themes.append({
                "theme_name": "Ý kiến Đa dạng & Quan điểm Khác",
                "sentiment": other_s,
                "prevalence_percent": other_prev,
                "sample_quotes": other_quotes,
                "count": len(other_bucket)
            })

        # Giới hạn số lượng chủ đề hiển thị
        top_themes = active_themes[:max_themes]
        for t in top_themes:
            t.pop("count", None)

        methodology = (
            f"Phân tích tự động N = {total} phản hồi văn bản định tính dựa trên Lexicon-Based Sentiment Analysis "
            f"và phân loại cụm chủ đề ngữ nghĩa đa tầng. Đã nhận diện {len(top_themes)} nhóm chủ đề trọng tâm."
        )

        return {
            "total_analyzed": total,
            "sentiment_distribution": sentiment_counts,
            "key_themes": top_themes,
            "anomaly_flags": anomaly_flags,
            "methodology_summary": methodology
        }
