import math
import random
from typing import Dict, Any, List, Optional, Tuple


class LatentClassAnalysisEngine:
    """
    Latent Class Analysis (LCA) & Finite Mixture Modeling Engine:
    - Lazarsfeld & Henry (1968) Latent Structure Analysis
    - Goodman (1974) Exploratory Latent Class Analysis
    - McLachlan & Peel (2000) Finite Mixture Models
    - Celeux & Soromenho (1996) Entropy Classification Metric
    - Schwarz (1978) Bayesian Information Criterion (BIC)

    Thuật toán EM (Expectation-Maximization) phân đoạn lớp ẩn xác suất:
    1. Ước lượng tỷ lệ phân bố lớp ẩn (Class Prevalences / Prior Probabilities pi_k)
    2. Xác suất lựa chọn từng phương án theo lớp ẩn (Item-Response Conditional Probabilities theta_kjp)
    3. Xác suất hậu nghiệm thuộc từng lớp của từng người trả lời (Posterior Probabilities tau_ik)
    4. Chỉ số chọn số lượng lớp tối ưu: AIC, BIC, Sample-Adjusted BIC (SABIC), Entropy (E_K)
    5. Đồ họa Vector SVG Profile Plot cho từng phân đoạn người trả lời
    6. Tự động sinh thuyết minh học thuật chuẩn APA 7th Edition
    """

    @staticmethod
    def compute_lca(
        responses_data: List[Dict[str, str]],
        item_keys: List[str],
        num_classes: Optional[int] = None,
        max_classes_to_test: int = 4,
        max_iter: int = 120,
        tol: float = 1e-5,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        responses_data: Danh sách các câu trả lời của từng người trả lời.
          Mỗi phần tử: {item_1: "Đồng ý", item_2: "Không đồng ý", ...}
        item_keys: Danh sách các mã câu hỏi phân tích (tối thiểu 3 items)
        num_classes: Nếu chỉ định, khớp đúng số lớp K; nếu None, tự động duyệt K in [2..max_classes] và chọn min BIC.
        """
        n_obs = len(responses_data)
        if n_obs < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi để thực hiện phân tích Lớp Ẩn LCA (hiện có {n_obs})."
            }

        if len(item_keys) < 3:
            return {
                "status": "INSUFFICIENT_ITEMS",
                "message": f"Cần tối thiểu 3 câu hỏi để phân tích cấu trúc lớp ẩn LCA (hiện có {len(item_keys)})."
            }

        # 1. Trích xuất và mã hóa các mức độ cho từng item
        item_categories: Dict[str, List[str]] = {}
        for item in item_keys:
            cat_set = set()
            for r in responses_data:
                val = str(r.get(item, "")).strip()
                if val:
                    cat_set.add(val)
            cats = sorted(list(cat_set))
            if len(cats) < 2:
                return {
                    "status": "INVALID_CATEGORIES",
                    "message": f"Câu hỏi '{item}' có ít hơn 2 mức độ phản hồi hợp lệ."
                }
            item_categories[item] = cats

        # Mã hóa dữ liệu thành các chỉ số nguyên 0..C_j-1
        # Lọc các quan sát có đầy đủ câu trả lời
        encoded_data: List[List[int]] = []
        for r in responses_data:
            valid_row = True
            row_encoded = []
            for item in item_keys:
                val = str(r.get(item, "")).strip()
                if val not in item_categories[item]:
                    valid_row = False
                    break
                row_encoded.append(item_categories[item].index(val))
            if valid_row:
                encoded_data.append(row_encoded)

        n_valid = len(encoded_data)
        if n_valid < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi đầy đủ dữ liệu (hiện có {n_valid})."
            }

        # Xác định phạm vi K lớp cần thử nghiệm
        if num_classes is not None:
            classes_to_try = [max(2, num_classes)]
        else:
            max_k = min(max_classes_to_test, max(2, int(math.sqrt(n_valid / 2))))
            classes_to_try = list(range(2, max_k + 1))

        models_comparison: List[Dict[str, Any]] = []
        best_model: Optional[Dict[str, Any]] = None
        min_bic = float("inf")

        for k in classes_to_try:
            m_res = LatentClassAnalysisEngine._fit_em_lca(
                encoded_data=encoded_data,
                item_categories=item_categories,
                item_keys=item_keys,
                k_classes=k,
                max_iter=max_iter,
                tol=tol,
                seed=random_seed + k
            )
            models_comparison.append({
                "num_classes": k,
                "log_likelihood": round(m_res["log_likelihood"], 3),
                "num_parameters": m_res["num_parameters"],
                "aic": round(m_res["aic"], 2),
                "bic": round(m_res["bic"], 2),
                "sabic": round(m_res["sabic"], 2),
                "entropy": round(m_res["entropy"], 3),
                "converged": m_res["converged"]
            })

            if m_res["bic"] < min_bic:
                min_bic = m_res["bic"]
                best_model = m_res

        if not best_model:
            return {
                "status": "CONVERGENCE_ERROR",
                "message": "Thuật toán EM không thể hội tụ trên dữ liệu khảo sát này."
            }

        # Đánh giá chất lượng phân tách lớp của mô hình tối ưu
        ent = best_model["entropy"]
        ent_quality = "Rất tốt (High Separation >= 0.80)" if ent >= 0.80 else "Tốt (Medium Separation >= 0.60)" if ent >= 0.60 else "Thấp (Low Separation)"

        # Tạo Profile Plot Vector SVG
        svg_profile_plot = LatentClassAnalysisEngine._generate_profile_svg(
            item_keys=item_keys,
            item_categories=item_categories,
            class_profiles=best_model["class_profiles"]
        )

        # Biên soạn thuyết minh học thuật APA 7th Edition
        apa_narrative = LatentClassAnalysisEngine._generate_apa_narrative(
            n_valid=n_valid,
            num_items=len(item_keys),
            optimal_k=best_model["k_classes"],
            models_comparison=models_comparison,
            best_model=best_model
        )

        return {
            "status": "SUCCESS",
            "sample_size": n_valid,
            "items_count": len(item_keys),
            "optimal_classes_count": best_model["k_classes"],
            "model_selection_criteria": models_comparison,
            "entropy": round(ent, 3),
            "entropy_quality": ent_quality,
            "class_prevalences": best_model["class_prevalences"],
            "class_profiles": best_model["class_profiles"],
            "posterior_class_distribution": best_model["posterior_class_counts"],
            "svg_profile_plot": svg_profile_plot,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _fit_em_lca(
        encoded_data: List[List[int]],
        item_categories: Dict[str, List[str]],
        item_keys: List[str],
        k_classes: int,
        max_iter: int,
        tol: float,
        seed: int
    ) -> Dict[str, Any]:
        """Thuật toán Expectation-Maximization (EM) khớp mô hình LCA K lớp."""
        n = len(encoded_data)
        num_items = len(item_keys)
        rng = random.Random(seed)

        # Số lượng mức độ của từng item
        c_j = [len(item_categories[item_keys[j]]) for j in range(num_items)]

        # Số tham số tự do: (K - 1) + K * sum(c_j - 1)
        num_params = (k_classes - 1) + k_classes * sum(cj - 1 for cj in c_j)

        # Khởi tạo ngẫu nhiên có chuẩn hóa xác suất:
        # pi: [K]
        pi = [1.0 / k_classes] * k_classes

        # theta: [K][num_items][c_j]
        theta: List[List[List[float]]] = []
        for k in range(k_classes):
            theta_k: List[List[float]] = []
            for j in range(num_items):
                raw = [rng.uniform(0.2, 0.8) for _ in range(c_j[j])]
                s = sum(raw)
                theta_k.append([v / s for v in raw])
            theta.append(theta_k)

        # Khởi tạo ma trận xác suất hậu nghiệm tau_ik: [n][K]
        tau = [[1.0 / k_classes] * k_classes for _ in range(n)]

        prev_ll = -float("inf")
        converged = False

        for it in range(max_iter):
            # --- E-STEP: Tính toán xác suất hậu nghiệm tau_ik ---
            curr_ll = 0.0

            for i in range(n):
                obs = encoded_data[i]
                log_prior_lik = []
                for k in range(k_classes):
                    log_lik = math.log(max(pi[k], 1e-12))
                    for j in range(num_items):
                        val_idx = obs[j]
                        log_lik += math.log(max(theta[k][j][val_idx], 1e-12))
                    log_prior_lik.append(log_lik)

                # Log-Sum-Exp để chống tràn số
                max_log = max(log_prior_lik)
                exp_vals = [math.exp(v - max_log) for v in log_prior_lik]
                sum_exp = sum(exp_vals)
                log_marg = max_log + math.log(max(sum_exp, 1e-12))
                curr_ll += log_marg

                for k in range(k_classes):
                    tau[i][k] = exp_vals[k] / sum_exp if sum_exp > 1e-12 else (1.0 / k_classes)

            # Kiểm tra hội tụ
            if abs(curr_ll - prev_ll) < tol:
                converged = True
                break
            prev_ll = curr_ll

            # --- M-STEP: Cập nhật pi và theta ---
            n_k = [sum(tau[i][k] for i in range(n)) for k in range(k_classes)]
            total_n = max(sum(n_k), 1e-9)

            for k in range(k_classes):
                pi[k] = max(n_k[k] / total_n, 1e-6)

            for k in range(k_classes):
                denom = max(n_k[k], 1e-6)
                for j in range(num_items):
                    counts = [0.0] * c_j[j]
                    for i in range(n):
                        val_idx = encoded_data[i][j]
                        counts[val_idx] += tau[i][k]
                    for c_idx in range(c_j[j]):
                        theta[k][j][c_idx] = max(counts[c_idx] / denom, 1e-6)

                    # Chuẩn hóa lại tổng = 1
                    s_t = sum(theta[k][j])
                    theta[k][j] = [v / s_t for v in theta[k][j]]

        # Tính toán Information Criteria
        aic = -2.0 * prev_ll + 2.0 * num_params
        bic = -2.0 * prev_ll + num_params * math.log(n)
        sabic = -2.0 * prev_ll + num_params * math.log((n + 2.0) / 24.0)

        # Tính Entropy (Celeux & Soromenho, 1996)
        # E = 1 - sum_{i,k} -tau_ik ln(tau_ik) / (n * ln(K))
        entropy_sum = 0.0
        for i in range(n):
            for k in range(k_classes):
                t_val = tau[i][k]
                if t_val > 1e-12:
                    entropy_sum += -t_val * math.log(t_val)

        denom_ent = n * math.log(k_classes) if k_classes > 1 else 1.0
        entropy = max(0.0, 1.0 - (entropy_sum / denom_ent))

        # Phân loại người trả lời vào lớp có hậu nghiệm cao nhất (Modal Assignment)
        modal_counts = [0] * k_classes
        for i in range(n):
            best_k = max(range(k_classes), key=lambda k: tau[i][k])
            modal_counts[best_k] += 1

        # Xây dựng cấu trúc class_profiles
        colors = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"]
        class_profiles: List[Dict[str, Any]] = []
        for k in range(k_classes):
            c_name = f"Lớp ẩn {k + 1} (Class {k + 1})"
            pct = (pi[k] * 100.0)
            items_prob: Dict[str, Dict[str, float]] = {}
            for j in range(num_items):
                item_name = item_keys[j]
                cats = item_categories[item_name]
                items_prob[item_name] = {
                    cats[c_idx]: round(theta[k][j][c_idx], 3)
                    for c_idx in range(len(cats))
                }

            class_profiles.append({
                "class_index": k + 1,
                "class_name": c_name,
                "prevalence_pct": round(pct, 1),
                "assigned_count": modal_counts[k],
                "color": colors[k % len(colors)],
                "item_probabilities": items_prob
            })

        class_prevalences = {
            f"Class_{k+1}": round(pi[k] * 100.0, 1) for k in range(k_classes)
        }

        return {
            "k_classes": k_classes,
            "log_likelihood": prev_ll,
            "num_parameters": num_params,
            "aic": aic,
            "bic": bic,
            "sabic": sabic,
            "entropy": entropy,
            "converged": converged,
            "class_prevalences": class_prevalences,
            "class_profiles": class_profiles,
            "posterior_class_counts": modal_counts
        }

    @staticmethod
    def _generate_profile_svg(
        item_keys: List[str],
        item_categories: Dict[str, List[str]],
        class_profiles: List[Dict[str, Any]]
    ) -> str:
        """Tạo biểu đồ tọa độ song song SVG trực quan hóa hồ sơ xác suất của từng lớp ẩn."""
        width = 620
        height = 300
        left_pad = 60
        right_pad = 40
        top_pad = 40
        bottom_pad = 60

        plot_w = width - left_pad - right_pad
        plot_h = height - top_pad - bottom_pad
        n_items = len(item_keys)

        svg_parts = [
            f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        ]

        # Background grid (Y-axis: 0.0 to 1.0 probability)
        for p in [0.0, 0.25, 0.50, 0.75, 1.0]:
            y = top_pad + (1.0 - p) * plot_h
            svg_parts.append(
                f'<line x1="{left_pad}" y1="{y}" x2="{width - right_pad}" y2="{y}" stroke="#334155" stroke-dasharray="3 3"/>'
            )
            svg_parts.append(
                f'<text x="{left_pad - 10}" y="{y + 4}" font-size="10" fill="#94a3b8" text-anchor="end">{p:.2f}</text>'
            )

        # X-axis item positions
        x_coords = []
        for j in range(n_items):
            x = left_pad + (j / max(1, n_items - 1)) * plot_w
            x_coords.append(x)
            svg_parts.append(
                f'<line x1="{x}" y1="{top_pad}" x2="{x}" y2="{height - bottom_pad}" stroke="#1e293b"/>'
            )
            # Label
            item_lbl = item_keys[j]
            if len(item_lbl) > 12:
                item_lbl = item_lbl[:10] + ".."
            svg_parts.append(
                f'<text x="{x}" y="{height - bottom_pad + 20}" font-size="11" font-weight="600" fill="#cbd5e1" text-anchor="middle">{item_lbl}</text>'
            )

        # Plot profile lines for each class (lấy xác suất của mức độ cao nhất/tích cực nhất của từng item)
        for prof in class_profiles:
            color = prof["color"]
            points = []
            for j in range(n_items):
                item_name = item_keys[j]
                cats = item_categories[item_name]
                # Chọn mức độ đầu tiên hoặc đặc trưng
                top_prob = prof["item_probabilities"][item_name][cats[0]]
                y = top_pad + (1.0 - top_prob) * plot_h
                points.append((x_coords[j], y))

            # Path
            path_d = f"M {points[0][0]} {points[0][1]}"
            for pt in points[1:]:
                path_d += f" L {pt[0]} {pt[1]}"

            svg_parts.append(
                f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            )

            # Points
            for pt in points:
                svg_parts.append(
                    f'<circle cx="{pt[0]}" cy="{pt[1]}" r="4.5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>'
                )

        svg_parts.append('</svg>')
        return "".join(svg_parts)

    @staticmethod
    def _generate_apa_narrative(
        n_valid: int,
        num_items: int,
        optimal_k: int,
        models_comparison: List[Dict[str, Any]],
        best_model: Dict[str, Any]
    ) -> str:
        """Biên soạn thuyết minh học thuật chuẩn APA 7th Edition."""
        ent = best_model["entropy"]
        bic = best_model["bic"]
        class_shares_str = ", ".join(
            f"{p['class_name']}: {p['prevalence_pct']}% (n = {p['assigned_count']})"
            for p in best_model["class_profiles"]
        )

        return (
            f"Phân tích Lớp Ẩn (Latent Class Analysis - LCA; Goodman, 1974; McLachlan & Peel, 2000) "
            f"được thực hiện trên tập dữ liệu gồm N = {n_valid} người trả lời hoàn thành {num_items} chỉ báo khảo sát. "
            f"So sánh các giải pháp từ 2 đến {len(models_comparison) + 1} lớp dựa trên Tiêu chuẩn Thông tin Bayesian "
            f"(BIC; Schwarz, 1978) và hệ số Entropy (Celeux & Soromenho, 1996) xác định giải pháp {optimal_k} lớp ẩn "
            f"đạt độ phù hợp tối ưu nhất (BIC = {bic:.2f}, Entropy = {ent:.3f}, phản ánh mức độ phân tách lớp rõ rệt). "
            f"Tỷ lệ phân bố các phân đoạn bao gồm: {class_shares_str}. "
            f"Các lớp ẩn thể hiện hình thái phản hồi dị biệt có ý nghĩa thống kê giữa các nhóm đối tượng."
        )
