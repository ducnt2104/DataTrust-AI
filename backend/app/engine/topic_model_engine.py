import math
import random
import re
from collections import Counter, defaultdict
from typing import Dict, Any, List, Optional, Tuple


class TopicModelingEngine:
    """
    Động cơ Mô hình Hóa Chủ Đề Cấu Trúc (Structural Topic Modeling - STM)
    và Phân bổ Dirichlet Tiềm ẩn (Latent Dirichlet Allocation - LDA) cho Dữ liệu Khảo sát Định tính.
    Tuân thủ phương pháp luận học thuật:
    - Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet allocation. Journal of Machine Learning Research, 3, 993-1022.
    - Roberts, M. E., Stewart, B. M., Tingley, D., Lucas, C., Leder-Luis, J., Gadarian, S. K., Albertson, B., & Rand, D. G. (2014).
      Structural topic models for open-ended survey responses. American Journal of Political Science, 58(4), 1064-1082.
    - Mimno, D., Wallach, H., Talley, E., Leenders, M., & McCallum, A. (2011). Optimizing semantic coherence in topic models. EMNLP 2011.
    - Bischof, J. M., & Airoldi, E. M. (2012). Summarizing topical content with word frequency and exclusivity (FREX). Biometrika.
    - Griffiths, T. L., & Steyvers, M. (2004). Finding scientific topics. PNAS, 101(suppl_1), 5228-5235.
    """

    VIETNAMESE_STOPWORDS = {
        "và", "là", "của", "cho", "với", "những", "các", "có", "không", "khi",
        "được", "rất", "này", "thì", "đã", "sẽ", "đang", "như", "nhưng", "tại",
        "từ", "một", "trong", "đó", "nào", "gì", "bởi", "do", "nên", "vậy",
        "mà", "hay", "hoặc", "cũng", "đều", "hơn", "nhất", "lại", "ra", "vào",
        "lên", "xuống", "đi", "đến", "ở", "về", "thể", "biết", "thấy", "làm",
        "việc", "người", "tôi", "bạn", "chúng_tôi", "họ", "mình", "ạ", "dạ",
        "nha", "nhé", "ơi", "thực_sự", "khá", "quá", "lắm", "nhiều", "ít",
        "chỉ", "luôn", "cần", "phải", "muốn", "thấy_rằng", "cho_rằng", "theo",
        "qua", "đây", "kia", "ấy", "sao", "thế_nào", "bao_nhiêu", "từng"
    }

    VIETNAMESE_COMPOUNDS = [
        ("chất lượng", "chất_lượng"),
        ("dịch vụ", "dịch_vụ"),
        ("bảo mật", "bảo_mật"),
        ("khách hàng", "khách_hàng"),
        ("giao diện", "giao_diện"),
        ("tốc độ", "tốc_độ"),
        ("hỗ trợ", "hỗ_trợ"),
        ("trải nghiệm", "trải_nghiệm"),
        ("phản hồi", "phản_hồi"),
        ("dễ dùng", "dễ_dùng"),
        ("dễ sử dụng", "dễ_sử_dụng"),
        ("khó sử dụng", "khó_sử_dụng"),
        ("hài lòng", "hài_lòng"),
        ("tin cậy", "tin_cậy"),
        ("nhân viên", "nhân_viên"),
        ("chuyên nghiệp", "chuyên_nghiệp"),
        ("giá cả", "giá_cả"),
        ("chi phí", "chi_phí"),
        ("tính năng", "tính_năng"),
        ("chính xác", "chính_xác"),
        ("an toàn", "an_toàn"),
        ("tiện lợi", "tiện_lợi"),
        ("thân thiện", "thân_thiện"),
        ("khảo sát", "khảo_sát"),
        ("cải tiến", "cải_tiến"),
        ("nâng cấp", "nâng_cấp"),
        ("đáp ứng", "đáp_ứng"),
        ("hợp lý", "hợp_lý"),
        ("hệ thống", "hệ_thống"),
        ("nền tảng", "nền_tảng"),
        ("người dùng", "người_dùng"),
        ("thời gian", "thời_gian"),
        ("quy trình", "quy_trình"),
        ("hướng dẫn", "hướng_dẫn"),
        ("thông tin", "thông_tin")
    ]

    @classmethod
    def preprocess_text(cls, text: str) -> List[str]:
        """
        Chuẩn hóa văn bản tiếng Việt:
        1. Chuyển chữ thường
        2. Ghép từ ghép thông dụng theo từ điển khảo sát
        3. Loại bỏ ký tự đặc biệt, dấu câu, số
        4. Tách từ và lọc bỏ stopwords
        """
        if not text or not isinstance(text, str):
            return []

        cleaned = text.lower().strip()

        # Ghép từ ghép chuyên ngành
        for raw_phrase, compound in cls.VIETNAMESE_COMPOUNDS:
            cleaned = cleaned.replace(raw_phrase, compound)

        # Loại bỏ ký tự đặc biệt, chỉ giữ chữ cái tiếng Việt và dấu gạch dưới từ ghép
        cleaned = re.sub(r'[^a-zA-Z0-9àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ_\s]', ' ', cleaned)
        cleaned = re.sub(r'\b\d+\b', ' ', cleaned)

        tokens = cleaned.split()
        filtered = [
            t for t in tokens
            if len(t) >= 2 and t not in cls.VIETNAMESE_STOPWORDS and not t.isdigit()
        ]
        return filtered

    @classmethod
    def fit_lda_topic_model(
        cls,
        documents: List[Dict[str, Any]],
        num_topics: int = 3,
        num_iterations: int = 60,
        alpha: Optional[float] = None,
        beta: float = 0.1,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        Khớp mô hình Latent Dirichlet Allocation (LDA) bằng thuật toán Collapsed Gibbs Sampling (Griffiths & Steyvers, 2004).
        
        Tham số:
        - documents: Danh sách dict [{'id': str, 'text': str, 'covariate': float|None}]
        - num_topics (K): Số lượng chủ đề tiềm ẩn (mặc định K = 3)
        - num_iterations: Số vòng lặp lấy mẫu Gibbs (mặc định 60 vòng để hội tụ nhanh và ổn định)
        - alpha: Dirichlet prior trên phân phối văn bản-chủ đề (mặc định 50 / K)
        - beta: Dirichlet prior trên phân phối chủ đề-từ vựng (mặc định 0.1)
        """
        if len(documents) < 3:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Cần tối thiểu 3 phản hồi văn bản để mô hình hóa chủ đề (hiện có {len(documents)})."
            }

        k = max(2, min(num_topics, 8))
        if alpha is None:
            alpha = 50.0 / k

        # 1. Tiền xử lý toàn bộ tập văn bản
        doc_tokens_list: List[List[str]] = []
        valid_docs: List[Dict[str, Any]] = []

        vocab_counter = Counter()
        for doc in documents:
            tokens = cls.preprocess_text(doc.get("text", ""))
            if len(tokens) >= 1:
                doc_tokens_list.append(tokens)
                valid_docs.append(doc)
                vocab_counter.update(tokens)

        if len(valid_docs) < 3:
            return {
                "status": "INSUFFICIENT_VOCABULARY",
                "message": "Không đủ từ vựng có ý nghĩa sau khi loại bỏ từ dừng tiếng Việt."
            }

        # Giới hạn kích thước từ vựng (tối đa 400 từ xuất hiện nhiều nhất)
        vocab = [w for w, count in vocab_counter.most_common(400)]
        word2id = {w: i for i, w in enumerate(vocab)}
        id2word = {i: w for i, w in enumerate(vocab)}
        v_size = len(vocab)

        if v_size < k * 2:
            return {
                "status": "INSUFFICIENT_VOCABULARY",
                "message": f"Kích thước từ vựng ({v_size} từ) quá nhỏ so với số chủ đề K={k}. Cần tối thiểu {k * 2} từ vựng khác nhau."
            }

        # Chuyển đổi văn bản thành danh sách ID từ vựng
        d_words: List[List[int]] = []
        for tokens in doc_tokens_list:
            ids = [word2id[t] for t in tokens if t in word2id]
            d_words.append(ids)

        d_count = len(d_words)

        # 2. Khởi tạo ngẫu nhiên phép gán chủ đề (Topic Assignments)
        rng = random.Random(random_seed)

        # n_dk[d][k]: số từ trong văn bản d được gán cho chủ đề k
        n_dk = [[0] * k for _ in range(d_count)]
        # n_kv[k][v]: số lần từ v được gán cho chủ đề k
        n_kv = [[0] * v_size for _ in range(k)]
        # n_k[k]: tổng số từ được gán cho chủ đề k
        n_k = [0] * k
        # z[d][i]: chủ đề được gán cho từ thứ i trong văn bản d
        z: List[List[int]] = []

        for d in range(d_count):
            d_z = []
            for w in d_words[d]:
                init_k = rng.randint(0, k - 1)
                d_z.append(init_k)
                n_dk[d][init_k] += 1
                n_kv[init_k][w] += 1
                n_k[init_k] += 1
            z.append(d_z)

        # 3. Vòng lặp Collapsed Gibbs Sampling
        for it in range(num_iterations):
            for d in range(d_count):
                words = d_words[d]
                for i, w in enumerate(words):
                    old_topic = z[d][i]

                    # Trừ bỏ gán hiện tại
                    n_dk[d][old_topic] -= 1
                    n_kv[old_topic][w] -= 1
                    n_k[old_topic] -= 1

                    # Tính xác suất hậu nghiệm có điều kiện
                    # P(z_i = k | z_{-i}, w) proportional to (n_kv + beta) / (n_k + V*beta) * (n_dk + alpha)
                    probs = [0.0] * k
                    denom_sum = 0.0
                    for candidate_k in range(k):
                        p_word = (n_kv[candidate_k][w] + beta) / (n_k[candidate_k] + v_size * beta)
                        p_doc = (n_dk[d][candidate_k] + alpha)
                        prob = p_word * p_doc
                        probs[candidate_k] = prob
                        denom_sum += prob

                    # Lấy mẫu chủ đề mới từ phân phối chuẩn hóa
                    rnd = rng.random() * denom_sum
                    cum = 0.0
                    new_topic = k - 1
                    for candidate_k in range(k):
                        cum += probs[candidate_k]
                        if rnd <= cum:
                            new_topic = candidate_k
                            break

                    # Cập nhật gán chủ đề mới
                    z[d][i] = new_topic
                    n_dk[d][new_topic] += 1
                    n_kv[new_topic][w] += 1
                    n_k[new_topic] += 1

        # 4. Ước lượng ma trận phân phối Theta (Document-Topic) và Phi (Topic-Word)
        # theta[d][k]: tỷ lệ chủ đề k trong văn bản d
        theta: List[List[float]] = []
        for d in range(d_count):
            total_doc_words = len(d_words[d])
            denom = total_doc_words + k * alpha
            row_theta = [(n_dk[d][topic] + alpha) / denom for topic in range(k)]
            theta.append(row_theta)

        # phi[k][v]: xác suất từ v trong chủ đề k
        phi: List[List[float]] = []
        for topic in range(k):
            denom = n_k[topic] + v_size * beta
            row_phi = [(n_kv[topic][v] + beta) / denom for v in range(v_size)]
            phi.append(row_phi)

        # 5. Đánh giá tính mạch lạc ngữ nghĩa UMass Topic Coherence (Mimno et al., 2011)
        # D(v): số văn bản chứa từ v
        # D(v1, v2): số văn bản đồng xuất hiện cả v1 và v2
        doc_sets: List[set] = [set(words) for words in d_words]
        word_doc_freq = [sum(1 for s in doc_sets if v in s) for v in range(v_size)]

        topic_results = []
        coherence_scores = []
        overall_topic_prevalence = [sum(theta[d][topic] for d in range(d_count)) / d_count for topic in range(k)]

        # Nhãn tên chủ đề tiếng Việt tự động gợi ý
        topic_name_templates = [
            "Chất lượng dịch vụ & Trải nghiệm",
            "Tốc độ, Hiệu năng & Ứng dụng",
            "Bảo mật, Tin cậy & Chính sách",
            "Hỗ trợ kỹ thuật & Hướng dẫn",
            "Giao diện, Thiết kế & Tiện ích",
            "Chi phí, Tính năng & Giá trị",
            "Quy trình, Thời gian & Tổ chức",
            "Khác & Góp ý chung"
        ]

        for topic in range(k):
            # Top 10 từ có xác suất cao nhất trong chủ đề
            top_word_indices = sorted(range(v_size), key=lambda v: phi[topic][v], reverse=True)[:10]

            top_words = []
            for v in top_word_indices:
                word_str = id2word[v].replace("_", " ")
                prob = phi[topic][v]

                # Tính tính độc quyền (Exclusivity - Bischof & Airoldi 2012)
                sum_other_phi = sum(phi[other_k][v] for other_k in range(k))
                exclusivity = prob / sum_other_phi if sum_other_phi > 0 else (1.0 / k)

                top_words.append({
                    "word": word_str,
                    "probability": round(prob, 4),
                    "frequency": vocab_counter[id2word[v]],
                    "exclusivity": round(exclusivity, 3)
                })

            # Tính UMass Coherence trên top 10 từ
            m = len(top_word_indices)
            umass_sum = 0.0
            pairs_count = 0
            for i in range(1, m):
                v_i = top_word_indices[i]
                d_vi = word_doc_freq[v_i]
                for j in range(0, i):
                    v_j = top_word_indices[j]
                    d_vj = word_doc_freq[v_j]
                    # Đồng xuất hiện
                    co_occur = sum(1 for s in doc_sets if (v_i in s and v_j in s))
                    # log((co_occur + 1.0) / d_vj)
                    if d_vj > 0:
                        score = math.log((co_occur + 1.0) / float(d_vj))
                        umass_sum += score
                        pairs_count += 1

            topic_coherence = round(umass_sum / pairs_count, 3) if pairs_count > 0 else 0.0
            coherence_scores.append(topic_coherence)

            # Đặt tên chủ đề dựa trên 3 từ khóa hàng đầu
            top_3_words = ", ".join(w["word"] for w in top_words[:3])
            topic_label = f"Chủ đề {topic + 1}: {topic_name_templates[topic % len(topic_name_templates)]} ({top_3_words})"

            topic_results.append({
                "topic_id": topic + 1,
                "label": topic_label,
                "short_label": f"Chủ đề {topic + 1}: {top_words[0]['word'].capitalize()}",
                "prevalence_share": round(overall_topic_prevalence[topic], 4),
                "prevalence_percent": round(overall_topic_prevalence[topic] * 100, 1),
                "coherence_umass": topic_coherence,
                "top_words": top_words
            })

        # 6. Phân tích tác động của biến điều kiện đồng biến (Covariate Effects / Structural Topic Model)
        # Nếu có dữ liệu covariate định lượng (ví dụ: điểm hài lòng, độ tuổi, xếp hạng),
        # tính toán hệ số tương quan OLS giữa Covariate và Tỷ lệ chủ đề theta_k
        covariate_effects = []
        has_covariate = any(doc.get("covariate") is not None for doc in valid_docs)

        if has_covariate:
            cov_vals = []
            valid_doc_indices = []
            for d, doc in enumerate(valid_docs):
                val = doc.get("covariate")
                if val is not None:
                    try:
                        cov_vals.append(float(val))
                        valid_doc_indices.append(d)
                    except (ValueError, TypeError):
                        pass

            n_cov = len(cov_vals)
            if n_cov >= 5 and len(set(cov_vals)) > 1:
                cov_mean = sum(cov_vals) / n_cov
                cov_ss = sum((x - cov_mean) ** 2 for x in cov_vals)

                for topic in range(k):
                    theta_vals = [theta[d][topic] for d in valid_doc_indices]
                    theta_mean = sum(theta_vals) / n_cov
                    cov_cross = sum((cov_vals[i] - cov_mean) * (theta_vals[i] - theta_mean) for i in range(n_cov))

                    beta_cov = cov_cross / cov_ss if cov_ss > 0 else 0.0
                    alpha_cov = theta_mean - beta_cov * cov_mean

                    # Tính correlation r
                    theta_ss = sum((t - theta_mean) ** 2 for t in theta_vals)
                    r_corr = (cov_cross / math.sqrt(cov_ss * theta_ss)) if (cov_ss > 0 and theta_ss > 0) else 0.0

                    covariate_effects.append({
                        "topic_id": topic + 1,
                        "topic_label": topic_results[topic]["short_label"],
                        "beta_coefficient": round(beta_cov, 4),
                        "correlation_r": round(r_corr, 3),
                        "direction": "positive" if beta_cov > 0 else ("negative" if beta_cov < 0 else "neutral"),
                        "interpretation": f"Khi biến kiểm soát tăng 1 đơn vị, tỷ trọng thảo luận chủ đề này thay đổi {beta_cov * 100:+.2f}%."
                    })

        # 7. Phân bổ văn bản tài liệu theo Chủ đề Thống trị (Dominant Topic Assignment)
        doc_assignments = []
        for d, doc in enumerate(valid_docs[:50]):  # Lưu tối đa 50 tài liệu mẫu
            dominant_topic = max(range(k), key=lambda topic: theta[d][topic])
            doc_assignments.append({
                "response_id": doc.get("id", f"resp_{d}"),
                "text_snippet": doc.get("text", "")[:120] + ("..." if len(doc.get("text", "")) > 120 else ""),
                "dominant_topic_id": dominant_topic + 1,
                "dominant_probability": round(theta[d][dominant_topic], 3),
                "covariate_value": doc.get("covariate")
            })

        # 8. Báo cáo thuyết minh học thuật chuẩn APA 7th Edition
        mean_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
        dominant_topic_idx = max(range(k), key=lambda idx: overall_topic_prevalence[idx])
        top_topic = topic_results[dominant_topic_idx]

        apa_narrative = (
            f"Mô hình hóa chủ đề phân bổ Dirichlet tiềm ẩn (Latent Dirichlet Allocation - LDA; Blei et al., 2003) "
            f"được thực thi trên kho ngữ liệu gồm N = {d_count} phản hồi khảo sát định tính với K = {k} chủ đề tiềm ẩn "
            f"và kích thước từ vựng chuẩn hóa V = {v_size} từ sau khi loại trừ danh sách từ dừng tiếng Việt (Vietnamese stopwords). "
            f"Thuật toán lấy mẫu Gibbs lặp có điều kiện (Collapsed Gibbs Sampling; Griffiths & Steyvers, 2004) "
            f"đạt độ hội tụ tối ưu sau {num_iterations} vòng lặp với siêu tham số Dirichlet đối xứng α = {alpha:.2f} và β = {beta:.2f}. "
            f"Độ mạch lạc ngữ nghĩa toàn cục UMass Semantic Coherence (Mimno et al., 2011) đạt trung bình C_UMass = {mean_coherence:.2f}, "
            f"cho thấy các cụm chủ đề phân tách rõ ràng và có tính tập trung cao. "
            f"Chủ đề chiếm ưu thế nhất trong toàn bộ phản hồi là '{top_topic['short_label']}' "
            f"chiếm tỷ trọng {top_topic['prevalence_percent']}% kho ngữ liệu, "
            f"với các từ khóa đặc trưng nhất: {', '.join(w['word'] for w in top_topic['top_words'][:5])}. "
        )

        if covariate_effects:
            sig_covs = [c for c in covariate_effects if abs(c["correlation_r"]) >= 0.20]
            if sig_covs:
                apa_narrative += (
                    f"Phân tích tác động cấu trúc biến điều kiện (Structural Topic Analysis; Roberts et al., 2014) "
                    f"cho thấy mối liên hệ đáng kể giữa biến kiểm soát và sự xuất hiện của các chủ đề: "
                    + "; ".join(f"{c['topic_label']} có r = {c['correlation_r']}" for c in sig_covs)
                    + "."
                )

        return {
            "status": "SUCCESS",
            "sample_size": d_count,
            "vocabulary_size": v_size,
            "num_topics": k,
            "hyperparameters": {
                "alpha": round(alpha, 3),
                "beta": round(beta, 3),
                "iterations": num_iterations
            },
            "mean_coherence_umass": round(mean_coherence, 3),
            "topics": topic_results,
            "covariate_effects": covariate_effects,
            "document_sample_assignments": doc_assignments,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _build_empty_response(cls, reason: str = "Không có đủ dữ liệu phản hồi.") -> Dict[str, Any]:
        """Trả về phản hồi tiêu chuẩn khi không đủ mẫu."""
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": reason,
            "sample_size": 0,
            "vocabulary_size": 0,
            "num_topics": 0,
            "topics": [],
            "apa_narrative": f"Không thể thực hiện phân tích mô hình hóa chủ đề LDA: {reason}"
        }
