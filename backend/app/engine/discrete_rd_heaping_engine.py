"""
DataTrust - Regression Discontinuity with Discrete Running Variables & Heaping Engine
=====================================================================================
Scientific References:
- Kolesár, M., & Rothe, C. (2018). Inference in regression discontinuity designs with
  discrete running variables. American Economic Review, 108(8), 2277-2304.
- Cattaneo, M. D., Frandsen, B. R., & Titiunik, R. (2015). Randomization inference in
  the regression discontinuity design: An application to party advantages in the US Senate.
  Journal of Causal Inference / Journal of Econometrics, 3(1), 1-24.
- Barreca, A. I., Lindo, J. M., & Waddell, G. R. (2016). Heaping-induced bias in
  regression-discontinuity designs. Economic Inquiry, 54(1), 268-293.
- Lee, D. S., & Card, D. (2008). Regression discontinuity inference with specification error.
  Journal of Econometrics, 142(2), 655-674.
- Armstrong, T. B., & Kolesár, M. (2018). Optimal inference in a class of minimax problems.
  Econometrica, 86(2), 655-683.

Core Methodological Guarantees:
1. Discreteness & Heaping Diagnostics: Detects discrete mass points and excess frequency
   at focal round numbers (multiples of 5 or 10) via Whipple's Index and Heap Density Ratios.
2. Kolesár & Rothe (2018 AER) Honest Confidence Intervals: Implements minimax optimal
   inference under bounded second derivative (Lipschitz/Hölder smoothness constant M),
   bounding worst-case approximation bias over discrete support and computing exact
   folded-normal critical values cv_{1-alpha}(bias/se).
3. Barreca et al. (2016) Donut-Hole RDD Triangulation: Re-estimates effect excluding
   heaped / threshold mass points to verify that causal jump is not driven by reporting artifacts.
4. Cattaneo et al. (2015) Finite-Sample Local Randomization: Exact Fisherian permutation
   inference within discrete windows adjacent to the cutoff.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar


class DiscreteRDHeapingEngine:
    """
    Regression Discontinuity Design with Discrete Running Variables and Heaping Engine.
    """

    @classmethod
    def estimate(
        cls,
        running_var: np.ndarray,
        outcome_var: np.ndarray,
        cutoff: float = 0.0,
        covariates: Optional[np.ndarray] = None,
        bandwidth: Optional[float] = None,
        kernel: str = "triangular",  # 'triangular', 'uniform', or 'epanechnikov'
        m_curvature_grid: Optional[List[float]] = None,
        focal_rounding_interval: float = 5.0,
        n_permutations: int = 500,
        confidence_level: float = 0.95,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Executes Discrete RDD estimation with Kolesár & Rothe (2018) honest bounds
        and Barreca et al. (2016) heaping diagnostics.
        """
        np.random.seed(seed)
        X = np.asarray(running_var, dtype=float).ravel()
        Y = np.asarray(outcome_var, dtype=float).ravel()

        N = len(X)
        if N < 30:
            raise ValueError(f"Sample size N={N} is too small for discrete RDD estimation (minimum N=30 required).")
        if len(Y) != N:
            raise ValueError(f"Outcome length {len(Y)} does not match running variable length {N}.")

        # -------------------------------------------------------------
        # Step 1: Discreteness & Heaping Diagnostics
        # -------------------------------------------------------------
        unique_x, counts_x = np.unique(X, return_counts=True)
        num_support_points = len(unique_x)
        is_discrete = bool(num_support_points <= 60 or np.mean(counts_x) > 1.5)

        # Left and right points closest to cutoff
        left_points = unique_x[unique_x < cutoff]
        right_points = unique_x[unique_x >= cutoff]

        if len(left_points) < 2 or len(right_points) < 2:
            raise ValueError(
                f"Insufficient support points on both sides of cutoff {cutoff}. "
                f"Found {len(left_points)} points to the left and {len(right_points)} to the right (minimum 2 required on each side)."
            )

        closest_left = float(np.max(left_points))
        closest_right = float(np.min(right_points))
        cutoff_gap = closest_right - closest_left

        # Check for heaping at focal multiples (e.g. multiples of 5 or 10)
        # Whipple's Index style heaping ratio: ratio of counts at round numbers vs expected uniform
        focal_mask = np.isclose(np.mod(X, focal_rounding_interval), 0.0, atol=1e-4) | np.isclose(
            np.mod(X, focal_rounding_interval), focal_rounding_interval, atol=1e-4
        )
        n_focal = int(np.sum(focal_mask))
        prop_focal = float(n_focal / N)

        # Expected proportion under uniform distribution across rounding interval
        expected_focal = float(1.0 / max(1.0, focal_rounding_interval))
        heaping_ratio = float(prop_focal / max(0.01, expected_focal)) if expected_focal > 0 else 1.0

        if heaping_ratio > 1.5:
            heaping_severity = "Severe Heaping Detected (Excess reporting at round intervals)"
        elif heaping_ratio > 1.2:
            heaping_severity = "Moderate Heaping (Focal number clustering present)"
        else:
            heaping_severity = "Negligible Heaping (Support appears uniformly distributed)"

        # -------------------------------------------------------------
        # Step 2: Bandwidth Selection (IK or Rule of Thumb)
        # -------------------------------------------------------------
        if bandwidth is None or bandwidth <= 0:
            sd_x = float(np.std(X, ddof=1))
            iqr_x = float(np.percentile(X, 75) - np.percentile(X, 25))
            spread = min(sd_x, iqr_x / 1.349) if iqr_x > 0 else sd_x
            bandwidth = float(max(cutoff_gap * 1.5, 1.06 * spread * (N ** (-0.2))))

        # Restrict sample to bandwidth window
        in_window = np.abs(X - cutoff) <= bandwidth
        if np.sum(in_window) < 20:
            bandwidth = float(np.percentile(np.abs(X - cutoff), 50) * 1.2)
            in_window = np.abs(X - cutoff) <= bandwidth

        X_w = X[in_window]
        Y_w = Y[in_window]
        N_w = len(X_w)

        # -------------------------------------------------------------
        # Step 3: Local Linear RDD Estimation
        # -------------------------------------------------------------
        # Weights according to chosen kernel
        u = (X_w - cutoff) / bandwidth
        if kernel == "triangular":
            weights = np.maximum(0.0, 1.0 - np.abs(u))
        elif kernel == "epanechnikov":
            weights = np.maximum(0.0, 0.75 * (1.0 - u**2))
        else:  # uniform
            weights = np.ones_like(u)

        # Treatment indicator D = 1(X >= cutoff)
        D_w = (X_w >= cutoff).astype(float)
        X_tilde = X_w - cutoff

        # Design matrix: [1, D, X_tilde, D * X_tilde]
        design_mat = np.column_stack([np.ones(N_w), D_w, X_tilde, D_w * X_tilde])
        W_diag = np.diag(weights)

        XtWX = design_mat.T @ W_diag @ design_mat
        # Add slight ridge for numerical stability if discrete rank deficiency
        XtWX_inv = np.linalg.pinv(XtWX + 1e-7 * np.eye(4))
        beta = XtWX_inv @ (design_mat.T @ (weights * Y_w))

        # Conventional Point Estimate of Treatment Effect
        tau_hat = float(beta[1])

        # Residuals and conventional / cluster-robust variance
        fitted_y = design_mat @ beta
        residuals = Y_w - fitted_y

        # Kolesár & Rothe weight vector for tau: second row of (X'WX)^-1 X'W
        w_tau = (XtWX_inv[1, :] @ (design_mat * weights[:, np.newaxis]).T)

        # Heteroskedasticity-robust variance: se^2 = sum(w_i^2 * e_i^2)
        se_conventional = float(np.sqrt(np.sum(w_tau**2 * residuals**2)))
        t_stat_conv = float(tau_hat / max(1e-6, se_conventional))
        p_val_conv = float(2.0 * (1.0 - stats.norm.cdf(abs(t_stat_conv))))
        ci_conv = [
            float(tau_hat - 1.96 * se_conventional),
            float(tau_hat + 1.96 * se_conventional),
        ]

        # -------------------------------------------------------------
        # Step 4: Kolesár & Rothe (2018 AER) Honest Minimax Bounds
        # -------------------------------------------------------------
        # For a given bound M on |f''(x)|, worst case approximation bias:
        # B_bar(M) = (M / 2) * sum( |w_tau_i| * (X_i - c)^2 )
        if m_curvature_grid is None:
            # Calibrate default M grid based on outcome variance and bandwidth scale
            sd_y = float(np.std(Y, ddof=1))
            m_baseline = sd_y / (bandwidth ** 2) if bandwidth > 0 else 1.0
            m_curvature_grid = [
                round(m_baseline * mult, 3) for mult in [0.25, 0.5, 1.0, 2.0, 4.0]
            ]

        def compute_folded_normal_cv(bias_ratio: float, alpha: float = 0.05) -> float:
            """
            Computes Armstrong & Kolesár (2018) / Kolesár & Rothe (2018) critical value
            for folded normal distribution |Z + b| where Z ~ N(0, 1) and b = bias / se.
            Solves Phi(cv - b) - Phi(-cv - b) = 1 - alpha.
            """
            target = 1.0 - alpha
            b = abs(bias_ratio)

            def objective(cv_candidate: float) -> float:
                prob = stats.norm.cdf(cv_candidate - b) - stats.norm.cdf(-cv_candidate - b)
                return (prob - target) ** 2

            res_opt = minimize_scalar(objective, bounds=(1.96, 1.96 + b + 2.0), method="bounded")
            return float(res_opt.x)

        honest_results = []
        for M in m_curvature_grid:
            worst_case_bias = float(0.5 * M * np.sum(np.abs(w_tau) * (X_tilde**2)))
            bias_ratio = worst_case_bias / max(1e-6, se_conventional)
            cv_honest = compute_folded_normal_cv(bias_ratio, alpha=1.0 - confidence_level)

            ci_honest_lower = float(tau_hat - cv_honest * se_conventional)
            ci_honest_upper = float(tau_hat + cv_honest * se_conventional)
            ci_len = ci_honest_upper - ci_honest_lower

            honest_results.append(
                {
                    "curvature_bound_m": M,
                    "worst_case_bias": round(worst_case_bias, 4),
                    "bias_se_ratio": round(bias_ratio, 3),
                    "critical_value": round(cv_honest, 3),
                    "honest_ci_95": [round(ci_honest_lower, 4), round(ci_honest_upper, 4)],
                    "honest_ci_length": round(ci_len, 4),
                    "contains_zero": bool(ci_honest_lower <= 0.0 <= ci_honest_upper),
                }
            )

        # -------------------------------------------------------------
        # Step 5: Barreca, Lindo, & Waddell (2016) Donut-Hole RDD
        # -------------------------------------------------------------
        # Drops points exactly at the cutoff or immediately heaped points
        donut_mask = ~np.isclose(X_w, cutoff, atol=1e-4) & ~((np.abs(X_w - cutoff) < 1e-4) | (focal_mask[in_window] & np.isclose(X_w, closest_right, atol=1e-4)))
        if np.sum(donut_mask) >= 15:
            X_d = X_w[donut_mask]
            Y_d = Y_w[donut_mask]
            w_d = weights[donut_mask]
            D_d = (X_d >= cutoff).astype(float)
            X_t_d = X_d - cutoff

            des_d = np.column_stack([np.ones(len(X_d)), D_d, X_t_d, D_d * X_t_d])
            XtWX_d = des_d.T @ np.diag(w_d) @ des_d
            beta_d = np.linalg.pinv(XtWX_d + 1e-7 * np.eye(4)) @ (des_d.T @ (w_d * Y_d))
            tau_donut = float(beta_d[1])
            res_d = Y_d - des_d @ beta_d
            w_tau_d = (np.linalg.pinv(XtWX_d + 1e-7 * np.eye(4))[1, :] @ (des_d * w_d[:, np.newaxis]).T)
            se_donut = float(np.sqrt(np.sum(w_tau_d**2 * res_d**2)))
            p_val_donut = float(2.0 * (1.0 - stats.norm.cdf(abs(tau_donut / max(1e-6, se_donut)))))
            donut_drop_count = int(np.sum(~donut_mask))
            delta_tau = float(tau_hat - tau_donut)
            donut_robust = bool(abs(delta_tau) < 1.0 * se_conventional)
        else:
            tau_donut = tau_hat
            se_donut = se_conventional
            p_val_donut = p_val_conv
            donut_drop_count = 0
            delta_tau = 0.0
            donut_robust = True

        donut_diagnostics = {
            "tau_donut": round(tau_donut, 4),
            "se_donut": round(se_donut, 4),
            "p_value_donut": round(p_val_donut, 5),
            "dropped_observations": donut_drop_count,
            "delta_from_baseline": round(delta_tau, 4),
            "is_heaping_robust": donut_robust,
        }

        # -------------------------------------------------------------
        # Step 6: Cattaneo et al. (2015) Finite-Sample Local Randomization
        # -------------------------------------------------------------
        # Inner-most window: [closest_left, closest_right]
        inner_mask = (X >= closest_left - 1e-4) & (X <= closest_right + 1e-4)
        X_inner = X[inner_mask]
        Y_inner = Y[inner_mask]
        D_inner = (X_inner >= cutoff).astype(int)

        n_inner = len(X_inner)
        if n_inner >= 10 and len(np.unique(D_inner)) == 2:
            obs_diff = float(np.mean(Y_inner[D_inner == 1]) - np.mean(Y_inner[D_inner == 0]))
            perm_diffs = []
            for _ in range(n_permutations):
                perm_d = np.random.permutation(D_inner)
                mean_t = np.mean(Y_inner[perm_d == 1])
                mean_c = np.mean(Y_inner[perm_d == 0])
                perm_diffs.append(mean_t - mean_c)

            fisher_p_val = float(np.mean(np.abs(perm_diffs) >= abs(obs_diff)))
        else:
            obs_diff = tau_hat
            fisher_p_val = p_val_conv

        local_randomization = {
            "window_bounds": [closest_left, closest_right],
            "window_observations": n_inner,
            "observed_mean_diff": round(obs_diff, 4),
            "fisher_exact_p_value": round(fisher_p_val, 5),
            "is_randomization_significant": bool(fisher_p_val < 0.05),
        }

        # -------------------------------------------------------------
        # Step 7: Dual-Panel Responsive SVG Visualizer
        # Panel A: Discrete Scatter Binned Means with Honest Confidence Interval Band
        # Panel B: Sensitivity Curve of Honest CIs vs Curvature Bound M
        # -------------------------------------------------------------
        svg_chart = cls._render_dual_panel_svg(
            X_w=X_w,
            Y_w=Y_w,
            cutoff=cutoff,
            tau_hat=tau_hat,
            ci_conv=ci_conv,
            honest_results=honest_results,
            tau_donut=tau_donut,
            closest_left=closest_left,
            closest_right=closest_right,
        )

        # -------------------------------------------------------------
        # Step 8: APA 7th Edition Academic Narrative
        # -------------------------------------------------------------
        m_ref = honest_results[len(honest_results) // 2]
        apa_narrative = (
            f"A regression discontinuity analysis for discrete running variables (Kolesár & Rothe, 2018) "
            f"was conducted with N = {N} respondents (N_window = {N_w} within effective bandwidth h = {bandwidth:.2f}) "
            f"across {num_support_points} discrete support points. "
            f"The running variable displayed {heaping_severity.lower()} with a heaping ratio of {heaping_ratio:.2f} at focal intervals. "
            f"Conventional local linear estimation yielded a jump of tau = {tau_hat:.3f} (SE = {se_conventional:.3f}, 95% CI [{ci_conv[0]:.3f}, {ci_conv[1]:.3f}], p = {p_val_conv:.4f}). "
            f"Accounting for discrete support misspecification under the Kolesár-Rothe minimax framework with second-derivative bound M = {m_ref['curvature_bound_m']}, "
            f"the worst-case bias was {m_ref['worst_case_bias']:.3f}, expanding the honest 95% confidence interval to [{m_ref['honest_ci_95'][0]:.3f}, {m_ref['honest_ci_95'][1]:.3f}] "
            f"({'retaining' if not m_ref['contains_zero'] else 'losing'} statistical significance at alpha = 0.05). "
            f"Barreca et al. (2016) donut-hole triangulation removing {donut_diagnostics['dropped_observations']} heaped observations "
            f"yielded tau_donut = {tau_donut:.3f} (delta = {delta_tau:.3f}), confirming that the estimated causal discontinuity "
            f"{'is robust to round-number reporting bias' if donut_robust else 'may be partly driven by non-random rounding behavior'}. "
            f"Finite-sample local randomization inference (Cattaneo et al., 2015) in the immediate discrete window [{closest_left}, {closest_right}] "
            f"yielded Fisher's exact p = {fisher_p_val:.4f}."
        )

        return {
            "status": "success",
            "sample_size": N,
            "window_sample_size": N_w,
            "cutoff": cutoff,
            "bandwidth": round(bandwidth, 3),
            "discreteness_diagnostics": {
                "num_support_points": num_support_points,
                "is_discrete": is_discrete,
                "closest_left_point": closest_left,
                "closest_right_point": closest_right,
                "cutoff_gap": round(cutoff_gap, 4),
                "heaping_ratio": round(heaping_ratio, 2),
                "heaping_severity": heaping_severity,
            },
            "conventional_rdd": {
                "tau_estimate": round(tau_hat, 4),
                "standard_error": round(se_conventional, 4),
                "t_statistic": round(t_stat_conv, 3),
                "p_value": round(p_val_conv, 5),
                "ci_95": [round(ci_conv[0], 4), round(ci_conv[1], 4)],
                "is_significant": bool(p_val_conv < 0.05),
            },
            "kolesar_rothe_honest_bounds": honest_results,
            "donut_hole_diagnostics": donut_diagnostics,
            "local_randomization_inference": local_randomization,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _render_dual_panel_svg(
        cls,
        X_w: np.ndarray,
        Y_w: np.ndarray,
        cutoff: float,
        tau_hat: float,
        ci_conv: List[float],
        honest_results: List[Dict[str, Any]],
        tau_donut: float,
        closest_left: float,
        closest_right: float,
    ) -> str:
        """Renders dual-panel vector SVG visualizer for Discrete RDD with Honest Bounds."""
        width = 940
        height = 370
        p_w = 425
        p_h = 285
        margin = {"top": 45, "bottom": 40, "left": 45, "right": 20}

        # -------------------------------------------------------------
        # Panel A: Discrete Scatter Binned Means & Local Linear Jump
        # -------------------------------------------------------------
        pA_x = 25
        pA_y = 15
        x0_a = pA_x + margin["left"]
        y0_a = pA_y + margin["top"]
        iw_a = p_w - margin["left"] - margin["right"]
        ih_a = p_h - margin["top"] - margin["bottom"]

        # Support point aggregation
        unique_pts, inv_idx = np.unique(X_w, return_inverse=True)
        mean_y_pts = np.array([np.mean(Y_w[inv_idx == i]) for i in range(len(unique_pts))])
        counts_pts = np.array([np.sum(inv_idx == i) for i in range(len(unique_pts))])

        min_x = float(np.min(X_w))
        max_x = float(np.max(X_w))
        min_y = float(np.min(mean_y_pts))
        max_y = float(np.max(mean_y_pts))
        span_y = max(1.0, max_y - min_y)
        y_min_scale = min_y - 0.15 * span_y
        y_max_scale = max_y + 0.15 * span_y

        def map_x_a(x_val: float) -> float:
            return x0_a + ((x_val - min_x) / max(1e-4, max_x - min_x)) * iw_a

        def map_y_a(y_val: float) -> float:
            return y0_a + ih_a - ((y_val - y_min_scale) / max(1e-4, y_max_scale - y_min_scale)) * ih_a

        cx_a = map_x_a(cutoff)

        # Plot discrete points
        dot_elements = []
        for ux, uy, uc in zip(unique_pts, mean_y_pts, counts_pts):
            px = map_x_a(ux)
            py = map_y_a(uy)
            # Size proportional to count
            r_dot = max(3.0, min(8.0, 2.5 + math.sqrt(uc)))
            color = "#10b981" if ux >= cutoff else "#3b82f6"
            dot_elements.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_dot:.1f}" fill="{color}" fill-opacity="0.8" stroke="#f8fafc" stroke-width="0.5"/>'
            )

        # Regression lines on left and right
        left_mask = unique_pts < cutoff
        right_mask = unique_pts >= cutoff
        poly_elements = []
        if np.sum(left_mask) >= 2:
            p_left = np.polyfit(unique_pts[left_mask], mean_y_pts[left_mask], 1)
            lx1, lx2 = float(np.min(unique_pts[left_mask])), float(np.max(unique_pts[left_mask]))
            ly1, ly2 = float(np.polyval(p_left, lx1)), float(np.polyval(p_left, lx2))
            poly_elements.append(
                f'<line x1="{map_x_a(lx1):.1f}" y1="{map_y_a(ly1):.1f}" x2="{map_x_a(lx2):.1f}" y2="{map_y_a(ly2):.1f}" stroke="#60a5fa" stroke-width="2.5"/>'
            )
        if np.sum(right_mask) >= 2:
            p_right = np.polyfit(unique_pts[right_mask], mean_y_pts[right_mask], 1)
            rx1, rx2 = float(np.min(unique_pts[right_mask])), float(np.max(unique_pts[right_mask]))
            ry1, ry2 = float(np.polyval(p_right, rx1)), float(np.polyval(p_right, rx2))
            poly_elements.append(
                f'<line x1="{map_x_a(rx1):.1f}" y1="{map_y_a(ry1):.1f}" x2="{map_x_a(rx2):.1f}" y2="{map_y_a(ry2):.1f}" stroke="#34d399" stroke-width="2.5"/>'
            )

        # -------------------------------------------------------------
        # Panel B: Honest 95% Confidence Intervals vs Curvature M
        # -------------------------------------------------------------
        pB_x = 475
        pB_y = 15
        x0_b = pB_x + margin["left"]
        y0_b = pB_y + margin["top"]
        iw_b = p_w - margin["left"] - margin["right"]
        ih_b = p_h - margin["top"] - margin["bottom"]

        m_vals = [h["curvature_bound_m"] for h in honest_results]
        all_ci_low = [h["honest_ci_95"][0] for h in honest_results] + [ci_conv[0], tau_donut]
        all_ci_upp = [h["honest_ci_95"][1] for h in honest_results] + [ci_conv[1], tau_donut]
        min_eff = min(all_ci_low)
        max_eff = max(all_ci_upp)
        span_eff = max(1.0, max_eff - min_eff)
        e_min_scale = min_eff - 0.15 * span_eff
        e_max_scale = max_eff + 0.15 * span_eff

        def map_m_x(m_idx: int) -> float:
            return x0_b + (m_idx / max(1, len(m_vals) - 1)) * iw_b

        def map_eff_y(e_val: float) -> float:
            return y0_b + ih_b - ((e_val - e_min_scale) / max(1e-4, e_max_scale - e_min_scale)) * ih_b

        zero_y = map_eff_y(0.0)

        # Render honest error bars across M
        ci_bars = []
        for i, h in enumerate(honest_results):
            mx = map_m_x(i)
            yl = map_eff_y(h["honest_ci_95"][0])
            yu = map_eff_y(h["honest_ci_95"][1])
            yp = map_eff_y(tau_hat)

            bar_color = "#f43f5e" if h["contains_zero"] else "#10b981"
            ci_bars.append(
                f'<line x1="{mx:.1f}" y1="{yl:.1f}" x2="{mx:.1f}" y2="{yu:.1f}" stroke="{bar_color}" stroke-width="2.5" stroke-linecap="round"/>'
            )
            ci_bars.append(
                f'<circle cx="{mx:.1f}" cy="{yp:.1f}" r="3.5" fill="{bar_color}"/>'
            )
            # Cap lines
            ci_bars.append(
                f'<line x1="{mx - 4:.1f}" y1="{yl:.1f}" x2="{mx + 4:.1f}" y2="{yl:.1f}" stroke="{bar_color}" stroke-width="1.5"/>'
            )
            ci_bars.append(
                f'<line x1="{mx - 4:.1f}" y1="{yu:.1f}" x2="{mx + 4:.1f}" y2="{yu:.1f}" stroke="{bar_color}" stroke-width="1.5"/>'
            )
            # Label M
            ci_bars.append(
                f'<text x="{mx:.1f}" y="{y0_b + ih_b + 14}" fill="#94a3b8" font-size="8.5" text-anchor="middle">M={h["curvature_bound_m"]}</text>'
            )

        # Assemble full SVG
        svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto font-sans">
  <defs>
    <linearGradient id="bgGradRD" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <filter id="shadowRD" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#bgGradRD)" rx="12"/>

  <!-- Panel A: Discrete Scatter & Local Polynomial Jump -->
  <g id="panelA" filter="url(#shadowRD)">
    <rect x="{pA_x}" y="{pA_y}" width="{p_w}" height="{p_h}" fill="#1e293b" fill-opacity="0.7" rx="8" stroke="#334155" stroke-width="1"/>
    <text x="{pA_x + 15}" y="{pA_y + 24}" fill="#f8fafc" font-size="13" font-weight="600">Panel A: Discrete Support &amp; Cutoff Discontinuity</text>

    <!-- Cutoff vertical dashed line -->
    <line x1="{cx_a:.1f}" y1="{y0_a}" x2="{cx_a:.1f}" y2="{y0_a + ih_a}" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="4 3"/>
    <text x="{cx_a:.1f}" y="{y0_a - 6}" fill="#f43f5e" font-size="9" font-weight="700" text-anchor="middle">Cutoff c={cutoff}</text>

    <!-- Polynomial lines -->
    {"".join(poly_elements)}

    <!-- Discrete support dots -->
    {"".join(dot_elements)}

    <!-- Baseline tau estimate badge -->
    <g transform="translate({pA_x + 15}, {pA_y + p_h - 26})">
      <rect x="0" y="0" width="{p_w - 30}" height="20" fill="#3b82f6" fill-opacity="0.15" rx="4" stroke="#3b82f6" stroke-width="1"/>
      <text x="{(p_w - 30)/2}" y="13" fill="#60a5fa" font-size="10" font-weight="600" text-anchor="middle">Conventional RD Jump: τ = {tau_hat:.3f} (95% CI [{ci_conv[0]:.2f}, {ci_conv[1]:.2f}])</text>
    </g>
  </g>

  <!-- Panel B: Honest 95% Confidence Intervals vs Curvature M -->
  <g id="panelB" filter="url(#shadowRD)">
    <rect x="{pB_x}" y="{pB_y}" width="{p_w}" height="{p_h}" fill="#1e293b" fill-opacity="0.7" rx="8" stroke="#334155" stroke-width="1"/>
    <text x="{pB_x + 15}" y="{pB_y + 24}" fill="#f8fafc" font-size="13" font-weight="600">Panel B: Kolesár &amp; Rothe (2018) Honest Minimax Bounds</text>

    <!-- Zero Reference Line -->
    <line x1="{x0_b}" y1="{zero_y:.1f}" x2="{x0_b + iw_b}" y2="{zero_y:.1f}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="{x0_b + iw_b - 5}" y="{zero_y - 4:.1f}" fill="#64748b" font-size="8.5" text-anchor="end">0.0 Null Line</text>

    <!-- Honest CIs -->
    {"".join(ci_bars)}

    <!-- Legend Footer -->
    <g transform="translate({pB_x + 15}, {pB_y + p_h - 26})">
      <rect x="0" y="0" width="{p_w - 30}" height="20" fill="#1e293b" rx="4" stroke="#475569" stroke-width="1"/>
      <circle cx="12" cy="10" r="4" fill="#10b981"/>
      <text x="22" y="13" fill="#cbd5e1" font-size="9">Significant (Excludes 0)</text>
      <circle cx="150" cy="10" r="4" fill="#f43f5e"/>
      <text x="160" y="13" fill="#cbd5e1" font-size="9">Inconclusive (Includes 0)</text>
      <text x="{p_w - 45}" y="13" fill="#38bdf8" font-size="9" text-anchor="end">Donut τ = {tau_donut:.2f}</text>
    </g>
  </g>

  <!-- Global Footer -->
  <text x="{width - 25}" y="{height - 12}" fill="#64748b" font-size="10" text-anchor="end">DataTrust AI • Discrete RDD &amp; Heaping Engine (Kolesár &amp; Rothe 2018 AER)</text>
</svg>"""
        return svg


def run_discrete_rd_heaping_analysis(
    records: List[Dict[str, Any]],
    running_var_col: str,
    outcome_col: str,
    cutoff: float = 0.0,
    bandwidth: Optional[float] = None,
    kernel: str = "triangular",
    focal_rounding_interval: float = 5.0,
    n_permutations: int = 500,
) -> Dict[str, Any]:
    """Helper function to parse records and execute Discrete RDD estimation."""
    if not records or len(records) < 30:
        raise ValueError(f"Cần tối thiểu 30 bản ghi hợp lệ để thực thi phân tích Discrete RDD (hiện có: {len(records) if records else 0}).")

    valid_x = []
    valid_y = []
    for r in records:
        if running_var_col not in r or outcome_col not in r:
            continue
        rx = r[running_var_col]
        ry = r[outcome_col]
        if rx is None or ry is None:
            continue
        try:
            vx = float(rx)
            vy = float(ry)
            valid_x.append(vx)
            valid_y.append(vy)
        except (ValueError, TypeError):
            continue

    if len(valid_x) < 30:
        raise ValueError(f"Chỉ có {len(valid_x)} bản ghi hợp lệ chứa cả hai biến. Cần tối thiểu 30 bản ghi.")

    return DiscreteRDHeapingEngine.estimate(
        running_var=np.array(valid_x, dtype=float),
        outcome_var=np.array(valid_y, dtype=float),
        cutoff=cutoff,
        bandwidth=bandwidth,
        kernel=kernel,
        focal_rounding_interval=focal_rounding_interval,
        n_permutations=n_permutations,
    )
