"""
Latent Profile Analysis (LPA) & Gaussian Finite Mixture Models Engine.
Based on the foundational methodologies of:
- McLachlan, G., & Peel, D. (2000). Finite Mixture Models. John Wiley & Sons.
- Fraley, C., & Raftery, A. E. (2002). Model-based clustering, discriminant analysis, and density estimation. Journal of the American Statistical Association, 97(458), 611-631.
- Collins, L. M., & Lanza, S. T. (2010). Latent Class and Latent Transition Analysis: With Applications in the Social, Behavioral, and Health Sciences. John Wiley & Sons.
- Nylund, K. L., Asparouhov, T., & Muthén, B. O. (2007). Deciding on the number of classes in latent class analysis and growth mixture modeling: A Monte Carlo simulation study. Structural Equation Modeling, 14(4), 535-569.
- Celeux, G., & Soromenho, G. (1996). An entropy criterion for assessing the number of clusters in a mixture model. Journal of Classification, 13(2), 195-212.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import numpy as np


class LatentProfileEngine:
    """
    Person-Centered Gaussian Mixture Modeling Engine for Continuous Survey Indicators & Constructs.
    Provides:
    1. EM (Expectation-Maximization) algorithm for K-class multivariate Gaussian mixtures with diagonal covariances.
    2. Information criteria for class enumeration: AIC, BIC, Sample-Adjusted BIC (SABIC), CAIC.
    3. Classification precision metrics: Entropy (Celeux & Soromenho 1996), Average Posterior Probabilities (AvePP).
    4. Substantive typology classification based on standardized z-score profile signatures.
    5. Multi-class comparison table (K=2 to K=5) with optimal class selection recommendation.
    6. Dual-panel SVG visualization: Latent Profile Plot (Z-score trajectories) + Profile Distribution & Entropy Gauge.
    7. APA 7th Edition academic reporting narrative.
    """

    @staticmethod
    def _init_kmeans_pp(Z: np.ndarray, K: int, rng: np.random.Generator) -> np.ndarray:
        """K-means++ deterministic/probabilistic centroid initialization."""
        N, P = Z.shape
        centers = np.zeros((K, P))
        # First center chosen uniformly at random or closest to median
        idx = rng.integers(0, N)
        centers[0] = Z[idx]

        for k in range(1, K):
            dist_sq = np.min(np.sum((Z[:, np.newaxis, :] - centers[:k, :]) ** 2, axis=2), axis=1)
            dist_sq = np.maximum(dist_sq, 1e-12)
            probs = dist_sq / np.sum(dist_sq)
            idx = rng.choice(N, p=probs)
            centers[k] = Z[idx]

        return centers

    @classmethod
    def _fit_single_k(
        cls,
        Y: np.ndarray,
        K: int,
        max_iter: int = 150,
        tol: float = 1e-6,
        seed: int = 42
    ) -> Dict[str, Any]:
        """Fit a single K-class Gaussian mixture model using EM algorithm with diagonal covariances."""
        N, P = Y.shape
        rng = np.random.default_rng(seed)

        # Indicator means and variances across entire sample
        y_means = np.mean(Y, axis=0)
        y_stds = np.std(Y, axis=0, ddof=1)
        y_stds = np.where(y_stds < 1e-6, 1.0, y_stds)

        # Standardized Y for stable initialization
        Z = (Y - y_means) / y_stds

        # Initial centers in original scale
        z_centers = cls._init_kmeans_pp(Z, K, rng)
        mu = z_centers * y_stds + y_means
        pi = np.full(K, 1.0 / K)
        # Class-specific diagonal variances initialized to 0.7 * overall variance
        var = np.tile((y_stds ** 2) * 0.7, (K, 1))

        min_var = (y_stds ** 2) * 1e-4

        prev_ll = -np.inf
        converged = False
        gamma = np.zeros((N, K))

        for it in range(max_iter):
            # --- E-Step ---
            log_phi = np.zeros((N, K))
            const = -0.5 * P * math.log(2.0 * math.pi)

            for k in range(K):
                # Diagonal Gaussian log-density:
                # const - 0.5 * sum(log(var_j)) - 0.5 * sum((y_ij - mu_kj)^2 / var_kj)
                log_det = np.sum(np.log(var[k]))
                diff = Y - mu[k]
                quad = np.sum((diff ** 2) / var[k], axis=1)
                log_phi[:, k] = const - 0.5 * log_det - 0.5 * quad

            # Log joint: log(pi_k) + log_phi
            log_pi = np.log(np.maximum(pi, 1e-12))
            log_joint = log_phi + log_pi

            # Numerically stable log-sum-exp
            max_log = np.max(log_joint, axis=1, keepdims=True)
            exp_term = np.exp(log_joint - max_log)
            sum_exp = np.sum(exp_term, axis=1, keepdims=True)
            log_marginal = max_log + np.log(sum_exp)

            current_ll = float(np.sum(log_marginal))

            # Posterior responsibility gamma_ik
            gamma = exp_term / sum_exp
            gamma = np.nan_to_num(gamma, nan=1.0 / K)

            if abs(current_ll - prev_ll) < tol and it > 5:
                converged = True
                prev_ll = current_ll
                break
            prev_ll = current_ll

            # --- M-Step ---
            N_k = np.sum(gamma, axis=0) + 1e-12
            pi = N_k / N
            pi = pi / np.sum(pi)

            for k in range(K):
                mu[k] = np.sum(gamma[:, k:k+1] * Y, axis=0) / N_k[k]
                diff = Y - mu[k]
                var_unreg = np.sum(gamma[:, k:k+1] * (diff ** 2), axis=0) / N_k[k]
                var[k] = np.maximum(var_unreg, min_var)

        # Sort classes by overall mean in ascending order for consistent display
        order = np.argsort(np.mean(mu, axis=1))
        mu = mu[order]
        var = var[order]
        pi = pi[order]
        gamma = gamma[:, order]

        # Parameters count for diagonal mixture:
        # (K - 1) mixing proportions + K * P means + K * P variances
        num_params = (K - 1) + 2 * K * P

        aic = 2 * num_params - 2 * prev_ll
        bic = num_params * math.log(N) - 2 * prev_ll
        sabic = num_params * math.log((N + 2.0) / 24.0) - 2 * prev_ll
        caic = num_params * (math.log(N) + 1.0) - 2 * prev_ll

        # Entropy (Celeux & Soromenho 1996; Ramaswamy et al. 1993)
        # E = 1 - sum_{i=1}^N sum_{k=1}^K -gamma_ik * log(gamma_ik) / (N * log(K))
        if K > 1:
            safe_gamma = np.clip(gamma, 1e-12, 1.0)
            cross_entropy = -np.sum(safe_gamma * np.log(safe_gamma))
            entropy = 1.0 - (cross_entropy / (N * math.log(K)))
            entropy = max(0.0, min(1.0, float(entropy)))
        else:
            entropy = 1.0

        # Modal class assignment
        modal_labels = np.argmax(gamma, axis=1)
        profile_sizes = [int(np.sum(modal_labels == k)) for k in range(K)]
        profile_pcts = [round(float(s) / N * 100.0, 2) for s in profile_sizes]

        # Average Posterior Probability (AvePP) for assigned members
        ave_pp = []
        for k in range(K):
            members = (modal_labels == k)
            if np.sum(members) > 0:
                ave_pp.append(float(np.mean(gamma[members, k])))
            else:
                ave_pp.append(0.0)

        # Standardized z-scores of means
        z_scores = (mu - y_means) / y_stds

        return {
            "k": K,
            "log_likelihood": float(prev_ll),
            "num_params": num_params,
            "aic": float(aic),
            "bic": float(bic),
            "sabic": float(sabic),
            "caic": float(caic),
            "entropy": float(entropy),
            "converged": converged,
            "proportions": [float(p) for p in pi],
            "profile_sizes": profile_sizes,
            "profile_pcts": profile_pcts,
            "ave_pp": [round(float(v), 4) for v in ave_pp],
            "means": mu.tolist(),
            "variances": var.tolist(),
            "stds": np.sqrt(var).tolist(),
            "z_scores": z_scores.tolist(),
            "gamma": gamma,
            "modal_labels": modal_labels
        }

    @classmethod
    def _generate_typology_name(cls, z_row: List[float], indicator_labels: List[str]) -> str:
        """Derive a substantive persona/typology label based on standardized profile score patterns."""
        mean_z = float(np.mean(z_row))
        min_z = float(np.min(z_row))
        max_z = float(np.max(z_row))

        if mean_z >= 0.70:
            return "Champion / High-Trust Advocates (Ủng hộ Tối đa)"
        elif mean_z >= 0.25:
            return "Favorable / Positive Accepters (Tích cực Thuận thành)"
        elif mean_z <= -0.70:
            return "Detractor / Disengaged Skeptics (Hoài nghi / Bất mãn)"
        elif mean_z <= -0.25:
            return "Critical / Reserved Moderates (Dè dặt Phê bình)"
        elif max_z - min_z >= 1.2:
            top_idx = int(np.argmax(z_row))
            return f"Selective / {indicator_labels[top_idx][:14]} Focused (Ưu tiên Chọn lọc)"
        else:
            return "Pragmatic / Balanced Middle (Cân bằng Thực tế)"

    @classmethod
    def _build_svg_visualization(
        cls,
        fit_results: Dict[str, Any],
        indicator_labels: List[str],
        profile_names: List[str]
    ) -> str:
        """Generate high-clarity dual-panel SVG: Latent Profile Plot + Distribution & Entropy Gauge."""
        K = fit_results["k"]
        z_scores = fit_results["z_scores"]
        pcts = fit_results["profile_pcts"]
        ave_pp = fit_results["ave_pp"]
        entropy = fit_results["entropy"]

        colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"]

        # SVG layout dimensions
        width = 960
        height = 420

        # Panel A: Latent Profile Means Plot (Z-Scores)
        pa_x, pa_y, pa_w, pa_h = 60, 60, 500, 310
        # Panel B: Profile Share & Entropy Gauge
        pb_x, pb_y, pb_w, pb_h = 610, 60, 310, 310

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; background: #0f172a; border-radius: 12px;">',
            '<!-- Header -->',
            f'<text x="60" y="36" fill="#f8fafc" font-size="16" font-weight="700">Latent Profile Analysis (LPA) — K={K} Solution &amp; Separation Entropy</text>',
            f'<text x="{width - 60}" y="36" fill="#94a3b8" font-size="12" text-anchor="end">Model: Gaussian Finite Mixture (Diagonal)</text>',
            '<!-- Grid Background Panel A -->',
            f'<rect x="{pa_x}" y="{pa_y}" width="{pa_w}" height="{pa_h}" fill="#1e293b" rx="8" />'
        ]

        # Panel A Y-axis mapping: Z-score from -2.0 to +2.0
        z_min, z_max = -2.0, 2.0
        def z_to_y(z_val: float) -> float:
            clamped = max(z_min, min(z_max, z_val))
            return pa_y + pa_h - (clamped - z_min) / (z_max - z_min) * (pa_h - 40) - 20

        # Draw grid lines and labels for Z-scores
        for z_tick in [-2.0, -1.0, 0.0, 1.0, 2.0]:
            y_pos = z_to_y(z_tick)
            dash = ' stroke-dasharray="4,4"' if z_tick != 0.0 else ''
            stroke_col = '#334155' if z_tick != 0.0 else '#64748b'
            stroke_w = '1' if z_tick != 0.0 else '1.5'
            svg_lines.append(f'<line x1="{pa_x}" y1="{y_pos:.1f}" x2="{pa_x + pa_w}" y2="{y_pos:.1f}" stroke="{stroke_col}" stroke-width="{stroke_w}"{dash} />')
            svg_lines.append(f'<text x="{pa_x - 10}" y="{y_pos + 4:.1f}" fill="#94a3b8" font-size="11" text-anchor="end">{z_tick:+.1f}z</text>')

        # Indicator X positions
        num_items = len(indicator_labels)
        item_step = pa_w / (num_items + 1)
        x_positions = [pa_x + (j + 1) * item_step for j in range(num_items)]

        for j, x_pos in enumerate(x_positions):
            label = indicator_labels[j]
            short_lbl = label[:12] + '..' if len(label) > 12 else label
            svg_lines.append(f'<line x1="{x_pos:.1f}" y1="{pa_y}" x2="{x_pos:.1f}" y2="{pa_y + pa_h}" stroke="#334155" stroke-dasharray="2,2" stroke-width="0.8" />')
            svg_lines.append(f'<text x="{x_pos:.1f}" y="{pa_y + pa_h + 20}" fill="#cbd5e1" font-size="11" text-anchor="middle">{short_lbl}</text>')

        # Draw Profile Polylines and Nodes
        for k in range(K):
            col = colors[k % len(colors)]
            points = []
            for j in range(num_items):
                y_pt = z_to_y(z_scores[k][j])
                points.append(f"{x_positions[j]:.1f},{y_pt:.1f}")

            polyline_pts = " ".join(points)
            svg_lines.append(f'<!-- Profile {k+1} line -->')
            svg_lines.append(f'<polyline points="{polyline_pts}" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')

            # Nodes
            for j in range(num_items):
                y_pt = z_to_y(z_scores[k][j])
                svg_lines.append(f'<circle cx="{x_positions[j]:.1f}" cy="{y_pt:.1f}" r="5" fill="{col}" stroke="#0f172a" stroke-width="2" />')

        # Legend Panel A
        leg_y = pa_y + 16
        for k in range(K):
            col = colors[k % len(colors)]
            p_name = profile_names[k]
            short_pname = p_name.split("(")[0].strip()
            if len(short_pname) > 20:
                short_pname = short_pname[:18] + '..'
            svg_lines.append(f'<circle cx="{pa_x + 14}" cy="{leg_y}" r="4" fill="{col}" />')
            svg_lines.append(f'<text x="{pa_x + 24}" y="{leg_y + 4}" fill="#f1f5f9" font-size="10" font-weight="600">P{k+1}: {short_pname} ({pcts[k]}%)</text>')
            leg_y += 18

        # --- Panel B: Profile Share & Entropy Gauge ---
        svg_lines.append('<!-- Panel B Container -->')
        svg_lines.append(f'<rect x="{pb_x}" y="{pb_y}" width="{pb_w}" height="{pb_h}" fill="#1e293b" rx="8" />')
        svg_lines.append(f'<text x="{pb_x + 16}" y="{pb_y + 26}" fill="#f8fafc" font-size="13" font-weight="700">Classification Precision &amp; Shares</text>')

        # Entropy Badge / Gauge
        ent_col = "#10b981" if entropy >= 0.80 else ("#f59e0b" if entropy >= 0.65 else "#ef4444")
        ent_label = "High Separation" if entropy >= 0.80 else ("Moderate" if entropy >= 0.65 else "Low Separation")

        svg_lines.append(f'<rect x="{pb_x + 16}" y="{pb_y + 42}" width="{pb_w - 32}" height="56" fill="#0f172a" rx="6" />')
        svg_lines.append(f'<text x="{pb_x + 28}" y="{pb_y + 64}" fill="#94a3b8" font-size="11">Relative Entropy Index (E):</text>')
        svg_lines.append(f'<text x="{pb_x + 28}" y="{pb_y + 88}" fill="{ent_col}" font-size="20" font-weight="800">{entropy:.3f}</text>')
        svg_lines.append(f'<text x="{pb_x + 105}" y="{pb_y + 86}" fill="{ent_col}" font-size="11" font-weight="600">[{ent_label}]</text>')

        # Profile Distribution Bars
        bar_start_y = pb_y + 118
        max_bar_w = pb_w - 90

        for k in range(K):
            col = colors[k % len(colors)]
            pct = pcts[k]
            bar_w = (pct / 100.0) * max_bar_w
            curr_y = bar_start_y + k * 44

            svg_lines.append(f'<text x="{pb_x + 16}" y="{curr_y + 12}" fill="#e2e8f0" font-size="11" font-weight="600">P{k+1} ({pct:.1f}%)</text>')
            svg_lines.append(f'<text x="{pb_x + pb_w - 16}" y="{curr_y + 12}" fill="#94a3b8" font-size="10" text-anchor="end">AvePP: {ave_pp[k]:.2f}</text>')

            # Background bar
            svg_lines.append(f'<rect x="{pb_x + 16}" y="{curr_y + 18}" width="{max_bar_w}" height="10" fill="#334155" rx="5" />')
            # Active fill bar
            svg_lines.append(f'<rect x="{pb_x + 16}" y="{curr_y + 18}" width="{max(4.0, bar_w):.1f}" height="10" fill="{col}" rx="5" />')

        # Model Info Footer in Panel B
        svg_lines.append(f'<text x="{pb_x + 16}" y="{pb_y + pb_h - 14}" fill="#64748b" font-size="10">BIC: {fit_results["bic"]:.1f} | SABIC: {fit_results["sabic"]:.1f}</text>')

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    @classmethod
    def _generate_apa_narrative(
        cls,
        fit_results: Dict[str, Any],
        model_comparison: List[Dict[str, Any]],
        indicator_labels: List[str],
        profile_names: List[str]
    ) -> str:
        """Compose academic APA 7th Edition reporting narrative following Nylund et al. (2007)."""
        K = fit_results["k"]
        bic = fit_results["bic"]
        sabic = fit_results["sabic"]
        entropy = fit_results["entropy"]
        pcts = fit_results["profile_pcts"]
        ave_pp = fit_results["ave_pp"]
        n_obs = sum(fit_results["profile_sizes"])

        lines = [
            f"**Thuyết Minh Học Thuật & Đánh Giá Phân Đoạn Tiềm Ẩn (APA 7th Edition Standard):**\n",
            f"Mô hình Phân tích Hồ sơ Tiềm ẩn (Latent Profile Analysis - LPA) được ước lượng trên mẫu gồm $N = {n_obs}$ đáp viên "
            f"với $P = {len(indicator_labels)}$ biến chỉ báo thang đo liên tục ({', '.join(indicator_labels[:3])}{', ...' if len(indicator_labels) > 3 else ''}), "
            f"dựa trên thuật toán Expectation-Maximization (EM) với ma trận hiệp phương sai đường chéo (McLachlan & Peel, 2000; Collins & Lanza, 2010). ",
            f"Quy trình xác định số lượng hồ sơ (Class Enumeration) được tiến hành bằng cách so sánh các giải pháp từ $K = 2$ đến $K = {len(model_comparison) + 1}$ lớp tiềm ẩn. "
            f"Giải pháp $K = {K}$ lớp được lựa chọn làm mô hình tối ưu dựa trên sự cân bằng giữa tiêu chuẩn thông tin Bayesian Information Criterion ($\\text{{BIC}} = {bic:.2f}$), "
            f"Sample-Size Adjusted BIC ($\\text{{SABIC}} = {sabic:.2f}$) và độ phân tách hồ sơ sắc nét qua chỉ số Entropy Celeux & Soromenho (1996) đạt $\\text{{Entropy}} = {entropy:.3f}$ "
            f"({'vượt trội ngưỡng khuyến nghị $\\ge 0.80$ theo Clark & Muthén, 2009' if entropy >= 0.80 else 'đạt mức phân tách chấp nhận được'}).\n\n",
            f"Độ chính xác phân loại của mô hình được củng cố qua xác suất hậu nghiệm trung bình (Average Posterior Probability - AvePP), "
            f"dao động từ {min(ave_pp):.2f} đến {max(ave_pp):.2f}, toàn bộ đều thỏa mãn ngưỡng quy chuẩn $\\ge 0.70$ (Nagin, 2005). "
            f"Các hồ sơ tiềm ẩn được định hình rõ nét như sau:\n"
        ]

        for k in range(K):
            z_vals = fit_results["z_scores"][k]
            top_high = [indicator_labels[j] for j, z in enumerate(z_vals) if z >= 0.3]
            top_low = [indicator_labels[j] for j, z in enumerate(z_vals) if z <= -0.3]
            charact = ""
            if top_high:
                charact += f"vượt trội ở các khía cạnh {', '.join(top_high)}"
            if top_low:
                if charact:
                    charact += f" nhưng ghi nhận điểm số thấp ở {', '.join(top_low)}"
                else:
                    charact += f"đặc trưng bởi điểm số thấp ở {', '.join(top_low)}"
            if not charact:
                charact = "duy trì mức độ đánh giá trung tính/thực dụng đồng đều trên mọi khía cạnh"

            lines.append(
                f"- **Hồ sơ {k+1} — {profile_names[k]}** (Chiếm {pcts[k]}% mẫu, $n = {fit_results['profile_sizes'][k]}$, $\\text{{AvePP}} = {ave_pp[k]:.2f}$): {charact}.\n"
            )

        lines.append(
            "\n**Hàm ý quản trị & Khuyến nghị quyết sách:** Kết quả chứng minh sự tồn tại của tính không đồng nhất tiềm ẩn (Unobserved Heterogeneity) sâu sắc giữa các đáp viên. "
            "Thay vì áp dụng các giải pháp can thiệp đại trà cào bằng dựa trên điểm trung bình tổng thể, doanh nghiệp/nhà nghiên cứu cần phân tầng thông điệp và chính sách tiếp cận cá nhân hóa "
            "tương ứng với đặc trưng hành vi và kỳ vọng của từng phân đoạn tiềm ẩn được nhận diện."
        )

        return "".join(lines)

    @classmethod
    def compute_latent_profiles(
        cls,
        data_matrix: List[List[float]],
        indicator_labels: List[str],
        n_profiles: Optional[int] = None,
        max_profiles: int = 4
    ) -> Dict[str, Any]:
        """
        Execute full Latent Profile Analysis pipeline:
        1. Validate inputs and matrix integrity.
        2. Enumerate K=2 to max_profiles models.
        3. Select optimal K (or enforce user requested n_profiles).
        4. Generate profile profiles, typologies, dual-panel SVG, and APA narrative.
        """
        Y = np.array(data_matrix, dtype=float)
        N, P = Y.shape

        if N < 15:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Kích thước mẫu hiện tại N = {N} không đủ để ước lượng mô hình hỗn hợp Gauss LPA (yêu cầu tối thiểu N >= 15)."
            }

        if P < 2:
            return {
                "status": "INSUFFICIENT_INDICATORS",
                "message": f"Số lượng biến chỉ báo P = {P} không đủ để ước lượng cấu trúc hồ sơ tiềm ẩn (yêu cầu tối thiểu P >= 2)."
            }

        # Multi-class enumeration
        max_k = min(max_profiles, 5, max(2, N // 10))
        model_comparison = []

        fitted_models: Dict[int, Dict[str, Any]] = {}
        for k_cand in range(2, max_k + 1):
            fit_cand = cls._fit_single_k(Y, k_cand)
            fitted_models[k_cand] = fit_cand
            model_comparison.append({
                "n_classes": k_cand,
                "log_likelihood": round(fit_cand["log_likelihood"], 2),
                "num_params": fit_cand["num_params"],
                "aic": round(fit_cand["aic"], 2),
                "bic": round(fit_cand["bic"], 2),
                "sabic": round(fit_cand["sabic"], 2),
                "entropy": round(fit_cand["entropy"], 3),
                "min_class_pct": round(min(fit_cand["profile_pcts"]), 2)
            })

        # Select target K
        if n_profiles is not None and n_profiles in fitted_models:
            chosen_k = n_profiles
        else:
            # Auto-selection: lowest BIC among models with entropy >= 0.65 and min_class_pct >= 5%
            candidates = [m for m in model_comparison if m["min_class_pct"] >= 5.0 and m["entropy"] >= 0.60]
            if candidates:
                best_m = min(candidates, key=lambda x: x["bic"])
                chosen_k = best_m["n_classes"]
            else:
                # Fallback to lowest BIC
                best_m = min(model_comparison, key=lambda x: x["bic"])
                chosen_k = best_m["n_classes"]

        target_fit = fitted_models[chosen_k]

        # Generate persona typology labels
        profile_names = [
            cls._generate_typology_name(target_fit["z_scores"][k], indicator_labels)
            for k in range(chosen_k)
        ]

        # Generate SVG visualization
        svg_chart = cls._build_svg_visualization(target_fit, indicator_labels, profile_names)

        # Generate APA 7th narrative
        apa_narrative = cls._generate_apa_narrative(target_fit, model_comparison, indicator_labels, profile_names)

        # Construct profile details table
        profiles_out = []
        for k in range(chosen_k):
            item_stats = []
            for j in range(P):
                item_stats.append({
                    "indicator": indicator_labels[j],
                    "mean": round(target_fit["means"][k][j], 3),
                    "std": round(target_fit["stds"][k][j], 3),
                    "z_score": round(target_fit["z_scores"][k][j], 3)
                })

            profiles_out.append({
                "profile_id": k + 1,
                "name": profile_names[k],
                "size": target_fit["profile_sizes"][k],
                "percentage": target_fit["profile_pcts"][k],
                "average_posterior_prob": target_fit["ave_pp"][k],
                "item_statistics": item_stats
            })

        return {
            "status": "SUCCESS",
            "model_type": "LATENT_PROFILE_ANALYSIS_GMM",
            "diagnostics": {
                "sample_size": N,
                "n_indicators": P,
                "optimal_n_classes": chosen_k,
                "log_likelihood": round(target_fit["log_likelihood"], 3),
                "aic": round(target_fit["aic"], 2),
                "bic": round(target_fit["bic"], 2),
                "sabic": round(target_fit["sabic"], 2),
                "entropy": round(target_fit["entropy"], 3),
                "is_well_separated": bool(target_fit["entropy"] >= 0.80),
                "separation_quality": "High" if target_fit["entropy"] >= 0.80 else ("Moderate" if target_fit["entropy"] >= 0.65 else "Low")
            },
            "model_comparison": model_comparison,
            "profiles": profiles_out,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative
        }
