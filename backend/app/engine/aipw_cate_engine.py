"""
DataTrust - Augmented Inverse Probability Weighting (AIPW) & CATE Engine
========================================================================
Implements Doubly Robust (DR) Average Treatment Effect (ATE) and
Conditional Average Treatment Effects (CATE) heterogeneity estimation
for observational survey data.

Methodological references:
- Robins, J. M., Rotnitzky, A., & Zhao, L. P. (1994). Estimation of regression
  coefficients when some regressors are not always observed. JASA, 89(427), 846-866.
- Chernozhukov, V., et al. (2018). Double/debiased machine learning for treatment
  and structural parameters. The Econometrics Journal, 21(1), C1-C68.
- Athey, S., & Wager, S. (2019). Estimating treatment effects with causal forests:
  An application. Observational Studies, 5(2), 37-65.
- Crump, R. K., et al. (2009). Dealing with limited overlap in estimation of
  average treatment effects. Biometrika, 96(1), 187-199.
- Kennedy, E. H. (2023). Towards optimal doubly robust estimation of heterogeneous
  causal effects. Electronic Journal of Statistics, 17(2), 3008-3049.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import scipy.stats as stats
from scipy.optimize import minimize


class AIPWCATEEngine:
    """
    Doubly Robust AIPW & Heterogeneous CATE Estimator.
    """

    @staticmethod
    def _fit_logistic_propensity(
        X: np.ndarray,
        W: np.ndarray,
        l2_reg: float = 1e-4
    ) -> np.ndarray:
        """
        Fit logistic regression via L2-regularized maximum likelihood.
        """
        n, p = X.shape
        # Add intercept
        X_design = np.column_stack([np.ones(n), X])
        p_dim = p + 1

        def loss_and_grad(weights):
            logits = np.clip(X_design @ weights, -20.0, 20.0)
            probs = 1.0 / (1.0 + np.exp(-logits))
            probs = np.clip(probs, 1e-12, 1.0 - 1e-12)

            # Negative log-likelihood with L2 penalty (excluding intercept from penalty)
            nll = -np.sum(W * np.log(probs) + (1.0 - W) * np.log(1.0 - probs))
            reg = 0.5 * l2_reg * np.sum(weights[1:] ** 2)
            total_loss = nll + reg

            grad = X_design.T @ (probs - W)
            grad[1:] += l2_reg * weights[1:]
            return total_loss, grad

        init_w = np.zeros(p_dim)
        res = minimize(
            loss_and_grad,
            init_w,
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": 250, "ftol": 1e-7}
        )
        fitted_logits = np.clip(X_design @ res.x, -20.0, 20.0)
        return 1.0 / (1.0 + np.exp(-fitted_logits))

    @staticmethod
    def _fit_ridge_regression(
        X: np.ndarray,
        Y: np.ndarray,
        alpha: float = 1e-3
    ) -> np.ndarray:
        """
        Fit linear ridge regression: Y = X_design @ beta.
        """
        n, p = X.shape
        X_design = np.column_stack([np.ones(n), X])
        p_dim = p + 1
        A = X_design.T @ X_design + alpha * np.eye(p_dim)
        A[0, 0] -= alpha  # do not penalize intercept
        b = X_design.T @ Y
        return np.linalg.solve(A, b)

    @classmethod
    def estimate(
        cls,
        W: np.ndarray,
        Y: np.ndarray,
        X: np.ndarray,
        subgroups: Optional[List[str]] = None,
        trim_alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Run complete Doubly Robust AIPW and Subgroup CATE analysis.
        """
        N = len(W)
        if N < 10:
            return {
                "status": "insufficient_data",
                "message": "Cần tối thiểu 10 quan sát để ước lượng Doubly Robust AIPW."
            }

        W = np.asarray(W, dtype=float)
        Y = np.asarray(Y, dtype=float)
        X = np.asarray(X, dtype=float)

        n_treated = int(np.sum(W == 1))
        n_control = int(np.sum(W == 0))

        if n_treated < 3 or n_control < 3:
            return {
                "status": "insufficient_data",
                "message": "Cả nhóm can thiệp (W=1) và nhóm đối chứng (W=0) phải có ít nhất 3 quan sát."
            }

        # 1. Propensity Score Estimation
        propensity = cls._fit_logistic_propensity(X, W)

        # 2. Overlap & Trimming (Crump et al. 2009)
        keep_mask = (propensity >= trim_alpha) & (propensity <= 1.0 - trim_alpha)
        n_trimmed = int(np.sum(~keep_mask))

        if np.sum(keep_mask) < 8:
            # Fallback: if trimming removes too many, relax trim threshold
            keep_mask = (propensity >= 0.01) & (propensity <= 0.99)
            n_trimmed = int(np.sum(~keep_mask))

        W_trim = W[keep_mask]
        Y_trim = Y[keep_mask]
        X_trim = X[keep_mask]
        e_trim = np.clip(propensity[keep_mask], 0.01, 0.99)
        N_eff = len(W_trim)

        # 3. Outcome Regression Models
        # Separate models for W=1 and W=0
        mask_t = (W_trim == 1)
        mask_c = (W_trim == 0)

        if np.sum(mask_t) < 2 or np.sum(mask_c) < 2:
            return {
                "status": "insufficient_data",
                "message": "Sau khi cắt lọc overlap, không đủ dữ liệu cho cả hai nhóm."
            }

        beta_1 = cls._fit_ridge_regression(X_trim[mask_t], Y_trim[mask_t])
        beta_0 = cls._fit_ridge_regression(X_trim[mask_c], Y_trim[mask_c])

        X_design_trim = np.column_stack([np.ones(N_eff), X_trim])
        mu_1_hat = X_design_trim @ beta_1
        mu_0_hat = X_design_trim @ beta_0

        # 4. Doubly Robust Scores (Robins et al. 1994, Chernozhukov et al. 2018)
        # Gamma_i = mu_1(X_i) - mu_0(X_i) + W_i*(Y_i - mu_1(X_i))/e_i - (1 - W_i)*(Y_i - mu_0(X_i))/(1 - e_i)
        gamma = (
            (mu_1_hat - mu_0_hat)
            + (W_trim * (Y_trim - mu_1_hat) / e_trim)
            - ((1.0 - W_trim) * (Y_trim - mu_0_hat) / (1.0 - e_trim))
        )

        ate = float(np.mean(gamma))
        ate_var = float(np.var(gamma, ddof=1) / N_eff)
        ate_se = float(np.sqrt(ate_var))
        z_stat = float(ate / ate_se) if ate_se > 1e-12 else 0.0
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        ci_lower = float(ate - 1.96 * ate_se)
        ci_upper = float(ate + 1.96 * ate_se)

        # Naive difference-in-means for benchmark comparison
        naive_treated_mean = float(np.mean(Y[W == 1]))
        naive_control_mean = float(np.mean(Y[W == 0]))
        naive_diff = float(naive_treated_mean - naive_control_mean)

        # 5. Overlap Metrics
        prop_t = propensity[W == 1]
        prop_c = propensity[W == 0]
        overlap_min = max(float(np.min(prop_t)), float(np.min(prop_c)))
        overlap_max = min(float(np.max(prop_t)), float(np.max(prop_c)))
        is_strong_overlap = bool(overlap_min < 0.4 and overlap_max > 0.6)

        # 6. Subgroup CATE Analysis (Heterogeneity)
        subgroup_results: List[Dict[str, Any]] = []
        het_f_stat: Optional[float] = None
        het_p_value: Optional[float] = None
        is_heterogeneous: bool = False

        if subgroups is not None and len(subgroups) == N:
            subgroups_trim = [subgroups[i] for i, k in enumerate(keep_mask) if k]
            unique_groups = sorted(list(set(subgroups_trim)))

            if len(unique_groups) >= 2:
                group_gammas = []
                for g in unique_groups:
                    indices = [i for i, grp in enumerate(subgroups_trim) if grp == g]
                    n_g = len(indices)
                    if n_g >= 3:
                        g_gamma = gamma[indices]
                        group_gammas.append(g_gamma)
                        cate_g = float(np.mean(g_gamma))
                        var_g = float(np.var(g_gamma, ddof=1) / n_g)
                        se_g = float(np.sqrt(var_g))
                        subgroup_results.append({
                            "subgroup": str(g),
                            "sample_size": n_g,
                            "cate": round(cate_g, 4),
                            "se": round(se_g, 4),
                            "ci_lower": round(cate_g - 1.96 * se_g, 4),
                            "ci_upper": round(cate_g + 1.96 * se_g, 4),
                            "z_score": round(cate_g / se_g, 4) if se_g > 1e-12 else 0.0,
                            "p_value": round(float(2.0 * (1.0 - stats.norm.cdf(abs(cate_g / se_g)))), 4) if se_g > 1e-12 else 1.0
                        })

                if len(group_gammas) >= 2:
                    # One-way ANOVA on doubly robust pseudo-outcomes
                    try:
                        f_res = stats.f_oneway(*group_gammas)
                        het_f_stat = float(f_res.statistic) if not np.isnan(f_res.statistic) else None
                        het_p_value = float(f_res.pvalue) if not np.isnan(f_res.pvalue) else None
                        is_heterogeneous = bool(het_p_value is not None and het_p_value < 0.05)
                    except Exception:
                        het_f_stat = None
                        het_p_value = None

        # 7. Generate Vector SVG Dual-Panel Chart
        svg_chart = cls._generate_svg_chart(
            prop_t=prop_t,
            prop_c=prop_c,
            trim_alpha=trim_alpha,
            ate=ate,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            subgroup_results=subgroup_results
        )

        # 8. APA 7th Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            ate=ate,
            se=ate_se,
            z_stat=z_stat,
            p_val=p_val,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            naive_diff=naive_diff,
            n_total=N,
            n_eff=N_eff,
            n_trimmed=n_trimmed,
            het_f_stat=het_f_stat,
            het_p_value=het_p_value,
            is_heterogeneous=is_heterogeneous,
            subgroup_count=len(subgroup_results)
        )

        return {
            "status": "success",
            "ate": round(ate, 4),
            "se": round(ate_se, 4),
            "z_stat": round(z_stat, 4),
            "p_value": round(p_val, 4),
            "ci_95_lower": round(ci_lower, 4),
            "ci_95_upper": round(ci_upper, 4),
            "is_significant": bool(p_val < 0.05),
            "naive_difference": round(naive_diff, 4),
            "selection_bias_estimate": round(naive_diff - ate, 4),
            "total_sample_size": N,
            "effective_sample_size": N_eff,
            "trimmed_units_count": n_trimmed,
            "propensity_overlap": {
                "treated_mean": round(float(np.mean(prop_t)), 4),
                "control_mean": round(float(np.mean(prop_c)), 4),
                "overlap_range": [round(overlap_min, 4), round(overlap_max, 4)],
                "strong_overlap": is_strong_overlap
            },
            "subgroup_cate": subgroup_results,
            "heterogeneity_test": {
                "f_statistic": round(het_f_stat, 4) if het_f_stat is not None else None,
                "p_value": round(het_p_value, 4) if het_p_value is not None else None,
                "is_heterogeneous": is_heterogeneous
            },
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        prop_t: np.ndarray,
        prop_c: np.ndarray,
        trim_alpha: float,
        ate: float,
        ci_lower: float,
        ci_upper: float,
        subgroup_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate SVG Dual-Panel Chart:
        - Panel 1: Propensity Score Overlap Distribution (Histograms of e(X)).
        - Panel 2: Subgroup CATE Forest Plot with 95% Confidence Intervals.
        """
        w, h = 820, 520
        pad_l, pad_r, pad_t, pad_b = 80, 40, 50, 40
        p1_h = 190
        p2_y = pad_t + p1_h + 50
        p2_h = h - p2_y - pad_b

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'style="background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, '
            f'\'Segoe UI\', Roboto, sans-serif;">'
        ]

        # Chart Title
        svg_parts.append(
            f'<text x="{w/2}" y="28" text-anchor="middle" fill="#f8fafc" '
            f'font-size="14" font-weight="700" letter-spacing="0.5">'
            f'DOUBLY ROBUST (AIPW) & CATE HETEROGENEITY DIAGNOSTICS</text>'
        )

        # ---------------- Panel 1: Propensity Score Overlap ----------------
        p1_w = w - pad_l - pad_r
        svg_parts.append(
            f'<text x="{pad_l}" y="{pad_t - 10}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL A: Propensity Score Overlap e(X) — Crump Trim [α={trim_alpha}]</text>'
        )

        # Binning 10 bins in [0, 1]
        bins = np.linspace(0.0, 1.0, 11)
        hist_t, _ = np.histogram(prop_t, bins=bins, density=True)
        hist_c, _ = np.histogram(prop_c, bins=bins, density=True)
        max_dens = max(float(np.max(hist_t)), float(np.max(hist_c)), 0.1)

        # Trimming markers
        x_trim_l = pad_l + trim_alpha * p1_w
        x_trim_r = pad_l + (1.0 - trim_alpha) * p1_w
        svg_parts.append(
            f'<rect x="{x_trim_l}" y="{pad_t}" width="{x_trim_r - x_trim_l}" height="{p1_h}" '
            f'fill="#10b981" fill-opacity="0.06"/>'
        )
        svg_parts.append(
            f'<line x1="{x_trim_l}" y1="{pad_t}" x2="{x_trim_l}" y2="{pad_t + p1_h}" '
            f'stroke="#ef4444" stroke-dasharray="3,3" stroke-width="1.5"/>'
        )
        svg_parts.append(
            f'<line x1="{x_trim_r}" y1="{pad_t}" x2="{x_trim_r}" y2="{pad_t + p1_h}" '
            f'stroke="#ef4444" stroke-dasharray="3,3" stroke-width="1.5"/>'
        )

        # Draw histogram bars for Treated (emerald) & Control (indigo)
        bin_width_px = p1_w / 10.0
        for b_idx in range(10):
            bx = pad_l + b_idx * bin_width_px
            # Control bar (left half of bin)
            h_c_px = (hist_c[b_idx] / max_dens) * (p1_h - 20)
            by_c = pad_t + p1_h - h_c_px
            svg_parts.append(
                f'<rect x="{bx + 2}" y="{by_c}" width="{bin_width_px/2 - 3}" height="{h_c_px}" '
                f'fill="#6366f1" fill-opacity="0.75" rx="2"/>'
            )
            # Treated bar (right half of bin)
            h_t_px = (hist_t[b_idx] / max_dens) * (p1_h - 20)
            by_t = pad_t + p1_h - h_t_px
            svg_parts.append(
                f'<rect x="{bx + bin_width_px/2 + 1}" y="{by_t}" width="{bin_width_px/2 - 3}" height="{h_t_px}" '
                f'fill="#10b981" fill-opacity="0.75" rx="2"/>'
            )

        # Baseline axis
        svg_parts.append(
            f'<line x1="{pad_l}" y1="{pad_t + p1_h}" x2="{pad_l + p1_w}" y2="{pad_t + p1_h}" '
            f'stroke="#475569" stroke-width="1"/>'
        )
        # X-labels for Panel 1
        for b_val in [0.0, 0.25, 0.5, 0.75, 1.0]:
            bx_lbl = pad_l + b_val * p1_w
            svg_parts.append(
                f'<text x="{bx_lbl}" y="{pad_t + p1_h + 14}" text-anchor="middle" fill="#64748b" font-size="10">'
                f'{b_val:.2f}</text>'
            )

        # Legend Panel 1
        svg_parts.append(
            f'<circle cx="{w - 220}" cy="{pad_t - 13}" r="4" fill="#10b981"/>'
            f'<text x="{w - 210}" y="{pad_t - 10}" fill="#cbd5e1" font-size="10">Can thiệp (Treated)</text>'
            f'<circle cx="{w - 110}" cy="{pad_t - 13}" r="4" fill="#6366f1"/>'
            f'<text x="{w - 100}" y="{pad_t - 10}" fill="#cbd5e1" font-size="10">Đối chứng (Control)</text>'
        )

        # ---------------- Panel 2: Subgroup CATE Forest Plot ----------------
        svg_parts.append(
            f'<text x="{pad_l}" y="{p2_y - 12}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL B: Conditional Average Treatment Effect (CATE) Heterogeneity Forest Plot</text>'
        )

        # Determine domain for CATE axis
        all_vals = [ate, ci_lower, ci_upper, 0.0]
        for sg in subgroup_results:
            all_vals.extend([sg["cate"], sg["ci_lower"], sg["ci_upper"]])
        min_c = min(all_vals) - 0.2 * abs(min(all_vals) if min(all_vals) != 0 else 1.0)
        max_c = max(all_vals) + 0.2 * abs(max(all_vals) if max(all_vals) != 0 else 1.0)
        if min_c >= max_c:
            min_c, max_c = -1.0, 1.0

        def c_to_x(val: float) -> float:
            return pad_l + 120 + ((val - min_c) / (max_c - min_c)) * (p1_w - 140)

        # Zero reference line
        x_zero = c_to_x(0.0)
        svg_parts.append(
            f'<line x1="{x_zero}" y1="{p2_y}" x2="{x_zero}" y2="{p2_y + p2_h}" '
            f'stroke="#475569" stroke-dasharray="3,3" stroke-width="1.2"/>'
        )

        # Overall AIPW ATE reference line (amber)
        x_ate = c_to_x(ate)
        x_ate_l = c_to_x(ci_lower)
        x_ate_r = c_to_x(ci_upper)
        svg_parts.append(
            f'<rect x="{x_ate_l}" y="{p2_y}" width="{max(1.0, x_ate_r - x_ate_l)}" height="{p2_h}" '
            f'fill="#f59e0b" fill-opacity="0.08"/>'
        )
        svg_parts.append(
            f'<line x1="{x_ate}" y1="{p2_y}" x2="{x_ate}" y2="{p2_y + p2_h}" '
            f'stroke="#f59e0b" stroke-dasharray="4,2" stroke-width="1.5"/>'
        )

        # Subgroup rows
        n_rows = len(subgroup_results) + 1  # Subgroups + Overall
        row_height = min(32.0, p2_h / max(1, n_rows))

        # Overall row at top of panel 2
        y_overall = p2_y + row_height * 0.7
        svg_parts.append(
            f'<text x="{pad_l}" y="{y_overall + 4}" fill="#f59e0b" font-size="11" font-weight="700">'
            f'OVERALL (AIPW)</text>'
        )
        svg_parts.append(
            f'<line x1="{x_ate_l}" y1="{y_overall}" x2="{x_ate_r}" y2="{y_overall}" '
            f'stroke="#f59e0b" stroke-width="2.5"/>'
        )
        svg_parts.append(
            f'<polygon points="{x_ate},{y_overall-5} {x_ate+6},{y_overall} {x_ate},{y_overall+5} {x_ate-6},{y_overall}" '
            f'fill="#f59e0b"/>'
        )
        svg_parts.append(
            f'<text x="{pad_l + p1_w}" y="{y_overall + 4}" text-anchor="end" fill="#f59e0b" '
            f'font-size="10" font-family="monospace">'
            f'{ate:+.2f} [{ci_lower:.2f}, {ci_upper:.2f}]</text>'
        )

        for idx, sg in enumerate(subgroup_results):
            y_r = p2_y + (idx + 1.6) * row_height
            if y_r > p2_y + p2_h - 10:
                break
            x_pt = c_to_x(sg["cate"])
            x_l = c_to_x(sg["ci_lower"])
            x_r = c_to_x(sg["ci_upper"])

            # Label
            svg_parts.append(
                f'<text x="{pad_l}" y="{y_r + 4}" fill="#cbd5e1" font-size="10">'
                f'{sg["subgroup"][:16]} (n={sg["sample_size"]})</text>'
            )
            # CI bar
            svg_parts.append(
                f'<line x1="{x_l}" y1="{y_r}" x2="{x_r}" y2="{y_r}" stroke="#38bdf8" stroke-width="1.8"/>'
            )
            svg_parts.append(
                f'<line x1="{x_l}" y1="{y_r - 3}" x2="{x_l}" y2="{y_r + 3}" stroke="#38bdf8" stroke-width="1.5"/>'
            )
            svg_parts.append(
                f'<line x1="{x_r}" y1="{y_r - 3}" x2="{x_r}" y2="{y_r + 3}" stroke="#38bdf8" stroke-width="1.5"/>'
            )
            # Point
            pt_color = "#10b981" if sg["cate"] > 0 else "#f43f5e"
            svg_parts.append(
                f'<circle cx="{x_pt}" cy="{y_r}" r="3.5" fill="{pt_color}"/>'
            )
            # Numeric value
            svg_parts.append(
                f'<text x="{pad_l + p1_w}" y="{y_r + 4}" text-anchor="end" fill="#94a3b8" '
                f'font-size="9" font-family="monospace">'
                f'{sg["cate"]:+.2f} [{sg["ci_lower"]:.2f}, {sg["ci_upper"]:.2f}]</text>'
            )

        # Baseline axis for Panel 2
        y_axis2 = p2_y + p2_h
        svg_parts.append(
            f'<line x1="{pad_l + 120}" y1="{y_axis2}" x2="{pad_l + p1_w - 60}" y2="{y_axis2}" '
            f'stroke="#475569" stroke-width="1"/>'
        )
        for tick_val in np.linspace(min_c, max_c, 5):
            tx = c_to_x(tick_val)
            if pad_l + 115 <= tx <= pad_l + p1_w - 55:
                svg_parts.append(
                    f'<line x1="{tx}" y1="{y_axis2}" x2="{tx}" y2="{y_axis2 + 4}" stroke="#64748b"/>'
                    f'<text x="{tx}" y="{y_axis2 + 15}" text-anchor="middle" fill="#64748b" font-size="9">'
                    f'{tick_val:.2f}</text>'
                )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    @classmethod
    def _generate_apa_narrative(
        cls,
        ate: float,
        se: float,
        z_stat: float,
        p_val: float,
        ci_lower: float,
        ci_upper: float,
        naive_diff: float,
        n_total: int,
        n_eff: int,
        n_trimmed: int,
        het_f_stat: Optional[float],
        het_p_value: Optional[float],
        is_heterogeneous: bool,
        subgroup_count: int
    ) -> str:
        """
        Generate APA 7th Edition narrative for Doubly Robust AIPW and Heterogeneity results.
        """
        sig_str = (
            f"mang ý nghĩa thống kê cao (z = {z_stat:.2f}, p = {p_val:.4f})"
            if p_val < 0.05
            else f"chưa đạt ngưỡng ý nghĩa thống kê thông thường (z = {z_stat:.2f}, p = {p_val:.4f})"
        )

        trim_str = (
            f"Để đảm bảo giả định hỗ trợ chung (common support), {n_trimmed} quan sát vi phạm vùng biên "
            f"đã được cắt lọc theo quy chuẩn Crump et al. (2009), giữ lại cỡ mẫu hiệu dụng N_eff = {n_eff}."
            if n_trimmed > 0
            else f"Toàn bộ N = {n_total} quan sát thỏa mãn hoàn hảo giả định hỗ trợ chung (overlap)."
        )

        het_str = ""
        if het_f_stat is not None and het_p_value is not None:
            if is_heterogeneous:
                het_str = (
                    f" Kiểm định tính không đồng nhất giữa các phân nhóm (Omnibus ANOVA on DR Scores) "
                    f"cho thấy tác động can thiệp có sự phân hóa đáng kể giữa {subgroup_count} phân khúc "
                    f"(F = {het_f_stat:.2f}, p = {het_p_value:.4f}), xác nhận sự tồn tại của hiệu ứng CATE đa tầng."
                )
            else:
                het_str = (
                    f" Kiểm định tính không đồng nhất phân nhóm không phát hiện sự khác biệt có ý nghĩa thống kê "
                    f"(F = {het_f_stat:.2f}, p = {het_p_value:.4f}), ngụ ý hiệu ứng can thiệp tương đối đồng nhất."
                )

        narrative = (
            f"Phân tích tác động can thiệp theo phương pháp Trọng số Nghịch đảo Xác suất Tăng cường Kép "
            f"(Doubly Robust Augmented Inverse Probability Weighting - AIPW; Robins et al., 1994; "
            f"Chernozhukov et al., 2018) trên cỡ mẫu tổng thể N = {n_total}. {trim_str} "
            f"Kết quả ước lượng tác động can thiệp trung bình (ATE) đạt tau_AIPW = {ate:+.4f} "
            f"(SE = {se:.4f}, 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]), {sig_str}. "
            f"So với chênh lệch trung bình quan sát ngây thơ (Naive Difference = {naive_diff:+.4f}), "
            f"mô hình kép đã triệt tiêu độ lệch chọn lọc ước tính khoảng {naive_diff - ate:+.4f}.{het_str}"
        )
        return narrative
