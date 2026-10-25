"""
DataTrust - Generalized Estimating Equations (GEE) Engine
=========================================================
Implements Generalized Estimating Equations for longitudinal repeated measures surveys:
- Liang, K. Y., & Zeger, S. L. (1986). Longitudinal data analysis using generalized
  linear models. Biometrika, 73(1), 13-22.
- Zeger, S. L., Liang, K. Y., & Albert, P. S. (1988). Models for longitudinal data:
  a generalized estimating equation approach. Biometrics, 44(4), 1049-1060.
- Diggle, P. J., Heagerty, P., Liang, K. Y., & Zeger, S. L. (2002). Analysis of
  Longitudinal Data (2nd ed.). Oxford University Press.
- Pan, W. (2001). Akaike's information criterion in generalized estimating equations.
  Biometrics, 57(1), 120-125.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


class GEEEngine:
    """
    Generalized Estimating Equations (GEE) Population-Averaged Longitudinal Estimator.
    """

    @classmethod
    def estimate(
        cls,
        cluster_ids: np.ndarray,      # M-vector of subject/cluster IDs
        time_points: np.ndarray,      # M-vector of wave indices (0, 1, 2, ...)
        outcomes: np.ndarray,         # M-vector of outcome Y
        predictors: np.ndarray,       # M x K design matrix of predictors X
        feature_names: Optional[List[str]] = None,
        family: str = "gaussian",     # "gaussian" or "binomial"
        corstr: str = "exchangeable"  # "exchangeable", "ar1", "independent"
    ) -> Dict[str, Any]:
        """
        Estimate GEE with robust sandwich standard errors.
        """
        Y = np.asarray(outcomes, dtype=float)
        X_raw = np.asarray(predictors, dtype=float)
        c_ids = np.asarray(cluster_ids)
        times = np.asarray(time_points, dtype=int)

        M = len(Y)
        if len(c_ids) != M or len(times) != M or len(X_raw) != M:
            return {
                "status": "error",
                "message": "Độ dài các mảng dữ liệu (cluster, time, outcome, predictors) không trùng khớp."
            }

        unique_clusters = np.unique(c_ids)
        N = len(unique_clusters)

        if N < 15:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 15 đối tượng/cụm (clusters) theo dõi lặp để ước lượng GEE (hiện có: {N})."
            }

        # Add intercept column
        if X_raw.ndim == 1:
            X_raw = X_raw[:, np.newaxis]
        K_pred = X_raw.shape[1]
        X = np.column_stack([np.ones(M), X_raw])
        K_total = K_pred + 1

        if feature_names is None or len(feature_names) != K_pred:
            feature_names = [f"X{i+1}" for i in range(K_pred)]
        all_feature_names = ["(Intercept)"] + feature_names

        # Organize by cluster
        cluster_indices: Dict[Any, List[int]] = {}
        for idx, cid in enumerate(c_ids):
            cluster_indices.setdefault(cid, []).append(idx)

        # 1. Initialize beta via naive OLS / GLM
        try:
            beta = np.linalg.lstsq(X, Y, rcond=None)[0]
        except np.linalg.LinAlgError:
            beta = np.zeros(K_total)

        phi = 1.0
        alpha_corr = 0.0

        # Iteratively Reweighted Quasi-Fisher Scoring (max 25 iterations)
        for it in range(25):
            # Compute fitted values & residuals
            if family == "binomial":
                eta = np.clip(X @ beta, -15.0, 15.0)
                mu = 1.0 / (1.0 + np.exp(-eta))
                mu = np.clip(mu, 1e-4, 1.0 - 1e-4)
                v = mu * (1.0 - mu)
            else:
                eta = X @ beta
                mu = eta
                v = np.ones(M)

            pearson_res = (Y - mu) / np.sqrt(v)

            # Update dispersion phi
            phi = max(1e-4, float(np.sum(pearson_res ** 2) / max(1, M - K_total)))

            # Update correlation parameter alpha
            if corstr == "exchangeable":
                num_alpha = 0.0
                denom_alpha = 0.0
                for cid, idxs in cluster_indices.items():
                    ni = len(idxs)
                    if ni > 1:
                        e_i = pearson_res[idxs]
                        for s in range(ni):
                            for t in range(s + 1, ni):
                                num_alpha += e_i[s] * e_i[t]
                                denom_alpha += 1.0
                if denom_alpha > 0:
                    alpha_corr = float(np.clip(num_alpha / (phi * denom_alpha), -0.95, 0.95))
                else:
                    alpha_corr = 0.0

            elif corstr == "ar1":
                num_alpha = 0.0
                denom_alpha = 0.0
                for cid, idxs in cluster_indices.items():
                    # Sort by time point
                    sorted_idxs = [x for _, x in sorted(zip(times[idxs], idxs))]
                    ni = len(sorted_idxs)
                    if ni > 1:
                        e_i = pearson_res[sorted_idxs]
                        for s in range(ni - 1):
                            num_alpha += e_i[s] * e_i[s + 1]
                            denom_alpha += 1.0
                if denom_alpha > 0:
                    alpha_corr = float(np.clip(num_alpha / (phi * denom_alpha), -0.95, 0.95))
                else:
                    alpha_corr = 0.0
            else:
                alpha_corr = 0.0

            # Compute Score U and Model Information M0
            M0 = np.zeros((K_total, K_total))
            U = np.zeros(K_total)

            for cid, idxs in cluster_indices.items():
                ni = len(idxs)
                X_i = X[idxs, :]
                y_i = Y[idxs]
                mu_i = mu[idxs]
                v_i = v[idxs]
                A_half = np.diag(np.sqrt(v_i))

                # Build working correlation matrix R_i
                if corstr == "exchangeable":
                    R_i = (1.0 - alpha_corr) * np.eye(ni) + alpha_corr * np.ones((ni, ni))
                elif corstr == "ar1":
                    t_i = times[idxs]
                    R_i = np.zeros((ni, ni))
                    for r1 in range(ni):
                        for r2 in range(ni):
                            R_i[r1, r2] = alpha_corr ** abs(t_i[r1] - t_i[r2])
                else:
                    R_i = np.eye(ni)

                try:
                    inv_R = np.linalg.inv(R_i)
                except np.linalg.LinAlgError:
                    inv_R = np.eye(ni)

                inv_A_half = np.diag(1.0 / np.maximum(1e-4, np.sqrt(v_i)))
                inv_V_i = (1.0 / phi) * (inv_A_half @ inv_R @ inv_A_half)

                # Canonical link derivative D_i = A_i @ X_i
                D_i = np.diag(v_i) @ X_i
                M0 += D_i.T @ inv_V_i @ D_i
                U += D_i.T @ inv_V_i @ (y_i - mu_i)

            try:
                inv_M0 = np.linalg.inv(M0)
                d_beta = inv_M0 @ U
                beta += d_beta
                if np.max(np.abs(d_beta)) < 1e-4:
                    break
            except np.linalg.LinAlgError:
                break

        # 2. Final Covariance Matrices: Model-based vs Robust Sandwich
        M1 = np.zeros((K_total, K_total))
        for cid, idxs in cluster_indices.items():
            ni = len(idxs)
            X_i = X[idxs, :]
            y_i = Y[idxs]
            mu_i = mu[idxs]
            v_i = v[idxs]
            A_half = np.diag(np.sqrt(v_i))

            if corstr == "exchangeable":
                R_i = (1.0 - alpha_corr) * np.eye(ni) + alpha_corr * np.ones((ni, ni))
            elif corstr == "ar1":
                t_i = times[idxs]
                R_i = np.zeros((ni, ni))
                for r1 in range(ni):
                    for r2 in range(ni):
                        R_i[r1, r2] = alpha_corr ** abs(t_i[r1] - t_i[r2])
            else:
                R_i = np.eye(ni)

            try:
                inv_R = np.linalg.inv(R_i)
            except np.linalg.LinAlgError:
                inv_R = np.eye(ni)

            inv_A_half = np.diag(1.0 / np.maximum(1e-4, np.sqrt(v_i)))
            inv_V_i = (1.0 / phi) * (inv_A_half @ inv_R @ inv_A_half)
            D_i = np.diag(v_i) @ X_i

            score_i = D_i.T @ inv_V_i @ (y_i - mu_i)
            M1 += np.outer(score_i, score_i)

        try:
            V_naive = np.linalg.inv(M0)
            V_robust = V_naive @ M1 @ V_naive
        except np.linalg.LinAlgError:
            V_naive = np.eye(K_total) * 0.1
            V_robust = np.eye(K_total) * 0.1

        se_naive = np.sqrt(np.maximum(1e-8, np.diag(V_naive)))
        se_robust = np.sqrt(np.maximum(1e-8, np.diag(V_robust)))

        # 3. Parameter Output Table
        coefficients_table = []
        for j in range(K_total):
            b = float(beta[j])
            se_r = float(se_robust[j])
            se_n = float(se_naive[j])
            z = float(b / se_r) if se_r > 1e-12 else 0.0
            p = float(2.0 * (1.0 - stats.norm.cdf(abs(z))))
            ci_l = float(b - 1.96 * se_r)
            ci_u = float(b + 1.96 * se_r)

            coefficients_table.append({
                "term": all_feature_names[j],
                "estimate": round(b, 4),
                "robust_se": round(se_r, 4),
                "naive_se": round(se_n, 4),
                "z_statistic": round(z, 4),
                "p_value": round(p, 4),
                "ci_95_lower": round(ci_l, 4),
                "ci_95_upper": round(ci_u, 4),
                "is_significant": bool(p < 0.05)
            })

        # 4. Pan's QIC (Quasi-likelihood Information Criterion)
        if family == "binomial":
            quasi_lik = float(np.sum(Y * np.log(np.maximum(1e-8, mu)) + (1.0 - Y) * np.log(np.maximum(1e-8, 1.0 - mu))))
        else:
            quasi_lik = -0.5 * float(np.sum((Y - mu) ** 2) / phi)

        trace_omega = float(np.trace(V_robust @ M0))
        qic = float(-2.0 * quasi_lik + 2.0 * trace_omega)

        # 5. Dual-Panel Vector SVG Chart
        svg_chart = cls._generate_svg_chart(
            coefficients=coefficients_table,
            alpha_corr=alpha_corr,
            corstr=corstr,
            family=family
        )

        # 6. APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_clusters=N,
            n_obs=M,
            family=family,
            corstr=corstr,
            alpha_corr=alpha_corr,
            coefficients=coefficients_table,
            qic=qic
        )

        return {
            "status": "success",
            "clusters_count": N,
            "observations_count": M,
            "family": family,
            "working_correlation_structure": corstr,
            "estimated_correlation_parameter": round(alpha_corr, 4),
            "dispersion_phi": round(phi, 4),
            "qic": round(qic, 3),
            "coefficients": coefficients_table,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        coefficients: List[Dict[str, Any]],
        alpha_corr: float,
        corstr: str,
        family: str
    ) -> str:
        w, h = 920, 360
        margin_l = 60
        plot_w = 400
        plot_h = 240
        top = 50

        # Panel A: Correlation Heatmap
        dim = 4
        cell_w = plot_w / dim
        cell_h = plot_h / dim

        corr_mat = np.zeros((dim, dim))
        for r in range(dim):
            for c in range(dim):
                if r == c:
                    corr_mat[r, c] = 1.0
                elif corstr == "ar1":
                    corr_mat[r, c] = alpha_corr ** abs(r - c)
                elif corstr == "exchangeable":
                    corr_mat[r, c] = alpha_corr
                else:
                    corr_mat[r, c] = 0.0

        svg = f"""<svg width="100%" height="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; font-family:Inter,system-ui,sans-serif;">
  <!-- Panel A Header -->
  <text x="{margin_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel A: Ma trận Tương quan Làm việc R(α) - {corstr.upper()} (α = {alpha_corr:+.3f})</text>
  <rect x="{margin_l}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>
"""
        for r in range(dim):
            for c in range(dim):
                val = corr_mat[r, c]
                cx = margin_l + c * cell_w
                cy = top + r * cell_h
                # Color intensity
                alpha_opac = max(0.1, min(0.9, abs(val)))
                fill_color = "#38bdf8" if val >= 0 else "#f43f5e"
                svg += f'  <rect x="{cx + 1:.1f}" y="{cy + 1:.1f}" width="{cell_w - 2:.1f}" height="{cell_h - 2:.1f}" fill="{fill_color}" fill-opacity="{alpha_opac:.2f}" rx="3"/>\n'
                svg += f'  <text x="{cx + cell_w / 2:.1f}" y="{cy + cell_h / 2 + 4:.1f}" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">{val:.2f}</text>\n'

        # Panel B: Forest Plot of Coefficients
        p2_l = 510
        p2_w = 350
        n_terms = len(coefficients)
        row_h = plot_h / max(1, n_terms)

        all_l = [c["ci_95_lower"] for c in coefficients]
        all_u = [c["ci_95_upper"] for c in coefficients]
        min_v = min(min(all_l), 0.0)
        max_v = max(max(all_u), 0.0)
        pad = 0.2 * (max_v - min_v + 1e-4)
        x_min = min_v - pad
        x_max = max_v + pad

        def to_x_forest(val: float) -> float:
            return p2_l + 70 + ((val - x_min) / max(1e-4, x_max - x_min)) * (p2_w - 70)

        x_zero = to_x_forest(0.0)

        svg += f"""
  <!-- Panel B Header -->
  <text x="{p2_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel B: Biểu đồ Rừng (Forest Plot) Hệ số GEE kèm 95% Sandwich CI</text>
  <rect x="{p2_l}" y="{top}" width="{p2_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>
  <line x1="{x_zero:.1f}" y1="{top}" x2="{x_zero:.1f}" y2="{top + plot_h}" stroke="#64748b" stroke-dasharray="4,4" stroke-width="1.2"/>
"""
        for i, coef in enumerate(coefficients):
            cy = top + i * row_h + row_h / 2
            x_est = to_x_forest(coef["estimate"])
            x_low = to_x_forest(coef["ci_95_lower"])
            x_high = to_x_forest(coef["ci_95_upper"])
            dot_color = "#34d399" if coef["is_significant"] else "#94a3b8"

            lbl = coef["term"][:10]
            svg += f'  <text x="{p2_l + 65}" y="{cy + 4:.1f}" fill="#cbd5e1" font-size="10" text-anchor="end">{lbl}</text>\n'
            svg += f'  <line x1="{x_low:.1f}" y1="{cy:.1f}" x2="{x_high:.1f}" y2="{cy:.1f}" stroke="{dot_color}" stroke-width="2"/>\n'
            svg += f'  <circle cx="{x_est:.1f}" cy="{cy:.1f}" r="4" fill="{dot_color}" stroke="#0f172a" stroke-width="1.5"/>\n'

        svg += """
  <!-- Legend -->
  <g transform="translate(510, 325)">
    <circle cx="10" cy="10" r="4" fill="#34d399"/>
    <text x="20" y="14" fill="#94a3b8" font-size="10">Có ý nghĩa thống kê (p &lt; .05)</text>
    <circle cx="170" cy="10" r="4" fill="#94a3b8"/>
    <text x="180" y="14" fill="#94a3b8" font-size="10">Không có ý nghĩa</text>
  </g>
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_clusters: int,
        n_obs: int,
        family: str,
        corstr: str,
        alpha_corr: float,
        coefficients: List[Dict[str, Any]],
        qic: float
    ) -> str:
        sig_terms = [c for c in coefficients if c["term"] != "(Intercept)" and c["is_significant"]]
        sig_str = ", ".join([f"{c['term']} (β = {c['estimate']:+.3f}, p = {c['p_value']:.3f})" for c in sig_terms]) if sig_terms else "không có biến dự báo nào đạt ý nghĩa thống kê p < .05"

        narrative = (
            f"Mô hình Phương trình Ước lượng Tổng quát (Generalized Estimating Equations - GEE; Liang & Zeger, 1986) "
            f"đã được áp dụng trên mẫu khảo sát lặp dọc gồm M = {n_obs} quan sát lồng ghép trong N = {n_clusters} đối tượng/cụm "
            f"với hàm phân phối {family} và cấu trúc ma trận tương quan làm việc {corstr} (Liang & Zeger, 1986; Diggle et al., 2002).\n\n"
            f"Hệ số tương quan nội cụm ước lượng đạt α = {alpha_corr:+.3f}, "
            f"cho thấy sự phụ thuộc tương quan đáng kể giữa các lần đo lặp của cùng một cá nhân. "
            f"Tiêu chí thông tin bán hợp lý đạt QIC = {qic:.2f} (Pan, 2001).\n\n"
            f"Ước lượng sai số chuẩn vững dạng bánh kẹp (Huber-White Sandwich Standard Errors) cho thấy: "
            f"các biến có tác động dân số trung bình (population-averaged effects) có ý nghĩa thống kê gồm: {sig_str}. "
            f"Sai số chuẩn vững đảm bảo suy luận thống kê duy trì tính nhất quán tiệm cận "
            f"ngay cả khi cấu trúc tương quan làm việc bị chỉ định sai lệch."
        )
        return narrative
