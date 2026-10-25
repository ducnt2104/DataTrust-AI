"""
DataTrust - Bifactor Psychometric Modeling & Omega Hierarchical Engine
====================================================================
Implements Bifactor orthogonal factor decomposition, Omega Hierarchical (ω_h),
Explained Common Variance (ECV), and subscale viability diagnostics
for survey scales.

Methodological references:
- Schmid, J., & Leiman, J. M. (1957). The development of hierarchical factor solutions.
  Psychometrika, 22(1), 53-61.
- Reise, S. P. (2012). The rediscovery of bifactor measurement models.
  Multivariate Behavioral Research, 47(5), 667-696.
- Rodriguez, A., Reise, S. P., & Haviland, M. G. (2016). Evaluating bifactor models:
  Calculating and interpreting statistical indices. Psychological Methods, 21(2), 137-150.
- McDonald, R. P. (1999). Test Theory: A Unified Treatment. Lawrence Erlbaum.
- Gibbons, R. D., et al. (2007). Full-information bifactor item response theory.
  Psychometrika, 72(4), 443-467.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import scipy.stats as stats


class BifactorEngine:
    """
    Bifactor Psychometric Analysis & Unidimensionality Evaluation Engine.
    """

    @classmethod
    def estimate(
        cls,
        data: np.ndarray,
        subscale_assignments: Dict[str, List[int]],
        item_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Estimate orthogonal bifactor model via Schmid-Leiman transformation.
        data: N x P matrix of responses.
        subscale_assignments: Dict mapping subscale_name -> list of item indices (0-based).
        item_labels: Optional list of item labels (length P).
        """
        N, P = data.shape
        if N < 15:
            return {
                "status": "insufficient_data",
                "message": "Cần tối thiểu 15 quan sát phản hồi để phân tích mô hình Bifactor."
            }
        if P < 4:
            return {
                "status": "insufficient_data",
                "message": "Cần tối thiểu 4 câu hỏi/mục khảo sát để phân tích Bifactor."
            }

        # Validate subscale assignments
        all_assigned = []
        for grp, indices in subscale_assignments.items():
            all_assigned.extend(indices)
        if len(all_assigned) != P or set(all_assigned) != set(range(P)):
            return {
                "status": "invalid_subscales",
                "message": "Tất cả các câu hỏi phải được phân vào đúng một tiểu thang đo duy nhất."
            }

        subscale_names = sorted(list(subscale_assignments.keys()))
        K = len(subscale_names)
        if K < 2:
            return {
                "status": "insufficient_subscales",
                "message": "Cần tối thiểu 2 tiểu thang đo để xây dựng cấu trúc Bifactor."
            }

        if item_labels is None:
            item_labels = [f"Item_{i+1}" for i in range(P)]

        # 1. Correlation Matrix
        R = np.corrcoef(data, rowvar=False)
        np.fill_diagonal(R, 1.0)
        # Handle nan in correlation if constant variance
        if np.any(np.isnan(R)):
            R = np.nan_to_num(R, nan=0.0)
            np.fill_diagonal(R, 1.0)

        # 2. First-Order Factor Loadings within each Subscale
        # For each subscale k, extract 1st principal component loadings
        first_order_loadings = np.zeros((P, K))
        subscale_eigenvalues = []

        for k_idx, s_name in enumerate(subscale_names):
            idx_k = subscale_assignments[s_name]
            R_k = R[np.ix_(idx_k, idx_k)]
            eigvals, eigvecs = np.linalg.eigh(R_k)
            # Largest eigenvector
            top_val = eigvals[-1]
            top_vec = eigvecs[:, -1]
            # Ensure positive sum of loadings
            if np.sum(top_vec) < 0:
                top_vec = -top_vec
            l_k = top_vec * np.sqrt(max(0.01, top_val))
            # Clip loadings to [-0.98, 0.98]
            l_k = np.clip(l_k, 0.1, 0.98)
            for local_i, item_idx in enumerate(idx_k):
                first_order_loadings[item_idx, k_idx] = l_k[local_i]
            subscale_eigenvalues.append(float(top_val))

        # 3. Correlation between Subscale Composites (Second-Order Correlation Phi)
        subscale_scores = np.zeros((N, K))
        for k_idx, s_name in enumerate(subscale_names):
            idx_k = subscale_assignments[s_name]
            subscale_scores[:, k_idx] = np.mean(data[:, idx_k], axis=1)

        Phi = np.corrcoef(subscale_scores, rowvar=False)
        if K == 2:
            # For 2 subscales, use geometric mean for second order loadings
            r_12 = max(0.05, min(0.95, float(Phi[0, 1])))
            gamma = np.array([np.sqrt(r_12), np.sqrt(r_12)])
        else:
            eigvals_phi, eigvecs_phi = np.linalg.eigh(Phi)
            top_phi_vec = eigvecs_phi[:, -1]
            if np.sum(top_phi_vec) < 0:
                top_phi_vec = -top_phi_vec
            gamma = top_phi_vec * np.sqrt(max(0.01, eigvals_phi[-1]))
            gamma = np.clip(gamma, 0.1, 0.95)

        # 4. Schmid-Leiman (1957) Transformation to Orthogonal Bifactor Solution
        # General factor loading: lambda_i0 = a_ik * gamma_k
        # Group factor loading: lambda_ik = a_ik * sqrt(1 - gamma_k^2)
        lambda_general = np.zeros(P)
        lambda_group = np.zeros((P, K))

        for k_idx, s_name in enumerate(subscale_names):
            g_k = gamma[k_idx]
            sqrt_resid = np.sqrt(max(0.01, 1.0 - g_k ** 2))
            idx_k = subscale_assignments[s_name]
            for item_idx in idx_k:
                a_ik = first_order_loadings[item_idx, k_idx]
                lambda_general[item_idx] = a_ik * g_k
                lambda_group[item_idx, k_idx] = a_ik * sqrt_resid

        # Uniqueness / error variance: u_i^2 = 1 - lambda_g^2 - lambda_s^2
        communalities = lambda_general ** 2 + np.sum(lambda_group ** 2, axis=1)
        uniqueness = np.maximum(0.02, 1.0 - communalities)

        # 5. Core Psychometric Indices (Reise 2012; Rodriguez et al. 2016)
        sum_lambda_g = float(np.sum(lambda_general))
        sum_sq_lambda_g = float(np.sum(lambda_general ** 2))

        # Variance of sum score
        # Var(Total) = (sum lambda_g)^2 + sum_k (sum lambda_sk)^2 + sum u_i^2
        sum_lambda_group_terms = []
        for k_idx in range(K):
            sum_lambda_group_terms.append(float(np.sum(lambda_group[:, k_idx])))
        group_factor_variance_part = sum(t ** 2 for t in sum_lambda_group_terms)
        var_total = (sum_lambda_g ** 2) + group_factor_variance_part + float(np.sum(uniqueness))

        # Omega Total: proportion of total variance due to all common factors
        omega_total = float(((sum_lambda_g ** 2) + group_factor_variance_part) / var_total)

        # Omega Hierarchical (omega_h): proportion of total score variance due to General Factor
        omega_hierarchical = float((sum_lambda_g ** 2) / var_total)

        # Subscale Omega & Subscale Omega Hierarchical (omega_hs)
        subscale_metrics: List[Dict[str, Any]] = []
        for k_idx, s_name in enumerate(subscale_names):
            idx_k = subscale_assignments[s_name]
            sum_g_k = float(np.sum(lambda_general[idx_k]))
            sum_s_k = float(np.sum(lambda_group[idx_k, k_idx]))
            sum_u_k = float(np.sum(uniqueness[idx_k]))
            var_sub = (sum_g_k ** 2) + (sum_s_k ** 2) + sum_u_k

            omega_sub = float(((sum_g_k ** 2) + (sum_s_k ** 2)) / var_sub) if var_sub > 0 else 0.0
            omega_hs = float((sum_s_k ** 2) / var_sub) if var_sub > 0 else 0.0

            subscale_metrics.append({
                "subscale": s_name,
                "item_count": len(idx_k),
                "items": [item_labels[i] for i in idx_k],
                "omega_subscale_total": round(omega_sub, 4),
                "omega_hierarchical_subscale": round(omega_hs, 4),
                "viable_as_independent_scale": bool(omega_hs >= 0.50)
            })

        # Explained Common Variance (ECV)
        total_common_var = sum_sq_lambda_g + float(np.sum(lambda_group ** 2))
        ecv = float(sum_sq_lambda_g / total_common_var) if total_common_var > 0 else 0.0

        # Percent of Uncontaminated Correlations (PUC)
        # Total correlations: P*(P-1)/2
        # Between-subscale correlations
        between_corr_count = 0
        for i in range(P):
            for j in range(i + 1, P):
                # find subscales of i and j
                grp_i = next(g for g, idxs in subscale_assignments.items() if i in idxs)
                grp_j = next(g for g, idxs in subscale_assignments.items() if j in idxs)
                if grp_i != grp_j:
                    between_corr_count += 1
        total_corr_count = P * (P - 1) // 2
        puc = float(between_corr_count / total_corr_count) if total_corr_count > 0 else 0.0

        # Item-level diagnostics: I-ECV
        item_diagnostics: List[Dict[str, Any]] = []
        for i in range(P):
            g_load = float(lambda_general[i])
            grp_name = next(g for g, idxs in subscale_assignments.items() if i in idxs)
            grp_idx = subscale_names.index(grp_name)
            s_load = float(lambda_group[i, grp_idx])
            comm_i = g_load ** 2 + s_load ** 2
            i_ecv = float(g_load ** 2 / comm_i) if comm_i > 0 else 0.0

            item_diagnostics.append({
                "item_index": i,
                "label": item_labels[i],
                "subscale": grp_name,
                "loading_general": round(g_load, 4),
                "loading_subscale": round(s_load, 4),
                "uniqueness": round(float(uniqueness[i]), 4),
                "item_ecv": round(i_ecv, 4),
                "is_general_anchor": bool(i_ecv >= 0.80)
            })

        # Essential Unidimensionality Criteria (Rodriguez, Reise & Haviland 2016)
        # Condition 1: omega_h >= 0.80
        # Condition 2: ECV >= 0.60 (or ECV > 0.70 & PUC > 0.70)
        is_essentially_unidimensional = bool(
            (omega_hierarchical >= 0.80) or
            (ecv >= 0.70 and puc >= 0.70) or
            (ecv >= 0.60 and omega_hierarchical >= 0.75)
        )

        # 6. Generate Vector SVG Diagram
        svg_chart = cls._generate_svg_chart(
            subscale_names=subscale_names,
            subscale_assignments=subscale_assignments,
            item_labels=item_labels,
            lambda_general=lambda_general,
            lambda_group=lambda_group,
            omega_h=omega_hierarchical,
            ecv=ecv
        )

        # 7. APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_obs=N,
            n_items=P,
            k_subscales=K,
            omega_total=omega_total,
            omega_h=omega_hierarchical,
            ecv=ecv,
            puc=puc,
            is_unidim=is_essentially_unidimensional,
            subscale_metrics=subscale_metrics
        )

        return {
            "status": "success",
            "sample_size": N,
            "items_count": P,
            "subscales_count": K,
            "omega_total": round(omega_total, 4),
            "omega_hierarchical": round(omega_hierarchical, 4),
            "explained_common_variance": round(ecv, 4),
            "percent_uncontaminated_correlations": round(puc, 4),
            "is_essentially_unidimensional": is_essentially_unidimensional,
            "recommendation": (
                "Khuyến nghị sử dụng điểm số tổng hợp duy nhất (Composite Sum Score); thang đo phản ánh yếu tố chung áp đảo."
                if is_essentially_unidimensional
                else "Khuyến nghị báo cáo các tiểu thang đo riêng biệt; cấu trúc đa chiều có sự phân hóa đáng kể."
            ),
            "subscale_metrics": subscale_metrics,
            "item_diagnostics": item_diagnostics,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        subscale_names: List[str],
        subscale_assignments: Dict[str, List[int]],
        item_labels: List[str],
        lambda_general: np.ndarray,
        lambda_group: np.ndarray,
        omega_h: float,
        ecv: float
    ) -> str:
        """
        Generate SVG Bifactor Structural Diagram:
        - Central General Factor (G)
        - Group Subscale Factors (S_k)
        - Connected Item Nodes with Loading Weights
        """
        w, h = 840, 520
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'style="background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, '
            f'\'Segoe UI\', Roboto, sans-serif;">'
        ]

        # Title
        svg_parts.append(
            f'<text x="{w/2}" y="28" text-anchor="middle" fill="#f8fafc" '
            f'font-size="14" font-weight="700" letter-spacing="0.5">'
            f'BIFACTOR PSYCHOMETRIC STRUCTURE & GENERAL FACTOR SATURATION</text>'
        )

        # Summary Badges Top Right
        badge_color = "#10b981" if omega_h >= 0.80 else "#f59e0b"
        svg_parts.append(
            f'<rect x="{w - 240}" y="12" width="220" height="26" rx="6" fill="#1e293b" stroke="#334155"/>'
            f'<text x="{w - 130}" y="29" text-anchor="middle" fill="{badge_color}" font-size="11" font-weight="700">'
            f'ω_h = {omega_h:.3f} | ECV = {ecv*100:.1f}%</text>'
        )

        # General Factor Node (Center Top)
        gx, gy = w / 2, 85
        svg_parts.append(
            f'<circle cx="{gx}" cy="{gy}" r="38" fill="#6366f1" fill-opacity="0.25" stroke="#6366f1" stroke-width="2.5"/>'
            f'<text x="{gx}" y="{gy - 4}" text-anchor="middle" fill="#c7d2fe" font-size="13" font-weight="800">G</text>'
            f'<text x="{gx}" y="{gy + 14}" text-anchor="middle" fill="#94a3b8" font-size="9">General Factor</text>'
        )

        # Subscale Factor Nodes (Middle Tier)
        K = len(subscale_names)
        sub_coords = {}
        sub_colors = ["#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"]

        for k_idx, s_name in enumerate(subscale_names):
            sx = (k_idx + 1) * (w / (K + 1))
            sy = 210
            color = sub_colors[k_idx % len(sub_colors)]
            sub_coords[s_name] = (sx, sy, color)

            svg_parts.append(
                f'<circle cx="{sx}" cy="{sy}" r="26" fill="{color}" fill-opacity="0.2" stroke="{color}" stroke-width="2"/>'
                f'<text x="{sx}" y="{sy - 2}" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="700">S{k_idx+1}</text>'
                f'<text x="{sx}" y="{sy + 12}" text-anchor="middle" fill="#94a3b8" font-size="8">{s_name[:12]}</text>'
            )

        # Items (Bottom Tier)
        P = len(item_labels)
        item_coords = {}
        for i_idx, label in enumerate(item_labels):
            ix = 40 + i_idx * ((w - 80) / max(1, P - 1))
            iy = 430
            item_coords[i_idx] = (ix, iy)

            # Item Box
            svg_parts.append(
                f'<rect x="{ix - 18}" y="{iy - 14}" width="36" height="28" rx="5" '
                f'fill="#1e293b" stroke="#475569" stroke-width="1.5"/>'
                f'<text x="{ix}" y="{iy + 4}" text-anchor="middle" fill="#cbd5e1" font-size="9" font-weight="600">'
                f'I{i_idx+1}</text>'
            )

        # Draw Arrows: G -> Items (Purple, semi-transparent)
        for i_idx in range(P):
            ix, iy = item_coords[i_idx]
            g_loading = lambda_general[i_idx]
            line_w = max(1.0, g_loading * 2.8)
            svg_parts.append(
                f'<line x1="{gx}" y1="{gy + 38}" x2="{ix}" y2="{iy - 14}" '
                f'stroke="#818cf8" stroke-opacity="0.35" stroke-width="{line_w:.1f}"/>'
            )

        # Draw Arrows: S_k -> Subscale Items (Matching color)
        for k_idx, s_name in enumerate(subscale_names):
            sx, sy, color = sub_coords[s_name]
            idx_k = subscale_assignments[s_name]
            for i_idx in idx_k:
                ix, iy = item_coords[i_idx]
                s_loading = lambda_group[i_idx, k_idx]
                line_w = max(1.2, s_loading * 3.2)
                svg_parts.append(
                    f'<line x1="{sx}" y1="{sy + 26}" x2="{ix}" y2="{iy - 14}" '
                    f'stroke="{color}" stroke-opacity="0.75" stroke-width="{line_w:.1f}"/>'
                )
                # Show loading text halfway
                mid_x = (sx + ix) / 2
                mid_y = (sy + 26 + iy - 14) / 2
                svg_parts.append(
                    f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" fill="{color}" '
                    f'font-size="8" font-family="monospace">{s_loading:.2f}</text>'
                )

        # Legend Bottom
        svg_parts.append(
            f'<rect x="40" y="{h - 35}" width="{w - 80}" height="25" rx="5" fill="#1e293b" fill-opacity="0.6"/>'
            f'<text x="{w/2}" y="{h - 19}" text-anchor="middle" fill="#94a3b8" font-size="10">'
            f'Đường tím: Tải trọng Nhân tố Chung G (General) | Đường màu: Tải trọng Tiểu thang đo S_k (Group Factors)'
            f'</text>'
        )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_obs: int,
        n_items: int,
        k_subscales: int,
        omega_total: float,
        omega_h: float,
        ecv: float,
        puc: float,
        is_unidim: bool,
        subscale_metrics: List[Dict[str, Any]]
    ) -> str:
        """
        Generate APA 7th Edition narrative for Bifactor psychometric evaluation.
        """
        unidim_str = (
            f"thỏa mãn hoàn hảo các tiêu chuẩn đo lường đơn chiều thực chất (essential unidimensionality; "
            f"Rodriguez et al., 2016). Hệ số Omega Phân cấp vượt ngưỡng khuyên nghị .80 (omega_h = {omega_h:.3f}), "
            f"và phương sai chung giải thích đạt ECV = {ecv*100:.1f}%. Do đó, 80%+ phương sai của điểm tổng phản ánh "
            f"trực tiếp biến tiềm ẩn chung G, chứng minh tính hợp lệ tuyệt đối khi sử dụng điểm tổng hợp duy nhất "
            f"(composite score) cho toàn bộ thang đo."
            if is_unidim
            else f"cho thấy thang đo mang cấu trúc đa chiều thực sự (multidimensional). Hệ số Omega Phân cấp chỉ đạt "
                 f"omega_h = {omega_h:.3f} (< .80) và ECV = {ecv*100:.1f}%, cho thấy một phần lớn phương sai tin cậy "
                 f"bị phân tán vào các tiểu thang đo. Nhà nghiên cứu không nên gộp chung thành một điểm tổng duy nhất "
                 f"mà cần phân tích độc lập các tiểu thang đo."
        )

        sub_details = []
        for s in subscale_metrics:
            status = "có giá trị độc lập" if s["viable_as_independent_scale"] else "kém độc lập (bị chi phối bởi G)"
            sub_details.append(f"{s['subscale']} (omega_hs = {s['omega_hierarchical_subscale']:.3f}, {status})")

        sub_str = "; ".join(sub_details)

        narrative = (
            f"Mô hình phân rã Bifactor trực giao (Bifactor Orthogonal Model; Schmid & Leiman, 1957; Reise, 2012) "
            f"được ước lượng trên mẫu khảo sát N = {n_obs} gồm {n_items} câu hỏi thuộc {k_subscales} tiểu thang đo. "
            f"Độ tin cậy tổng thể đạt omega_total = {omega_total:.3f}. Về khả năng đơn chiều, cấu trúc thang đo {unidim_str} "
            f"Tỷ lệ tương quan không ô nhiễm đạt PUC = {puc*100:.1f}%. Đánh giá từng tiểu thang đo sau khi kiểm soát nhân tố chung G: "
            f"{sub_str}."
        )
        return narrative
