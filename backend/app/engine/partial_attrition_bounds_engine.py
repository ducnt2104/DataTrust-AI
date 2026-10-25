"""
Partial Identification & Non-Random Attrition Bounds Engine
============================================================
Mathematical & Econometric References:
- Horowitz, J. L., & Manski, C. F. (2000). Nonparametric analysis of randomized
  experiments with missing covariate and outcome data. Journal of the American
  Statistical Association, 95(449), 77-84.
- Manski, C. F. (1990). Nonparametric bounds on treatment effects. American
  Economic Review, 80(2), 319-323.
- Manski, C. F., & Pepper, J. V. (2000). Monotone instrumental variables: With an
  application to the returns to schooling. Econometrica, 68(5), 997-1010.
- Lee, D. S. (2009). Training, wages, and sample selection: Estimating sharp
  bounds on treatment effects. The Review of Economic Studies, 76(3), 1071-1102.
- Imbens, G. W., & Manski, C. F. (2004). Confidence intervals for partially
  identified parameters. Econometrica, 72(6), 1845-1857.
- Stoye, J. (2009). More on confidence intervals for partially identified
  parameters. Econometrica, 77(4), 1299-1315.

DataTrust Iteration 192.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


class PartialAttritionBoundsEngine:
    """
    Engine for bounding treatment effects under non-random survey attrition,
    selective non-response, and partial identification.
    """

    @classmethod
    def evaluate(
        cls,
        treatment: np.ndarray,
        outcome: np.ndarray,
        response_indicator: np.ndarray,
        treatment_name: str = "Treatment D",
        outcome_name: str = "Outcome Y",
        user_ymin: Optional[float] = None,
        user_ymax: Optional[float] = None,
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Calculates Manski-Horowitz worst-case bounds, Lee (2009) trimming bounds,
        MTS bounds, and Imbens-Manski confidence intervals.
        """
        N = len(treatment)
        if N < 20:
            raise ValueError(f"Cỡ mẫu quá nhỏ để ước lượng chặn định danh một phần (N={N} < 20).")

        treatment = treatment.astype(int)
        response_indicator = response_indicator.astype(int)

        # -------------------------------------------------------------
        # Step 1: Basic Sample Quantities & Attrition Rates
        # -------------------------------------------------------------
        mask_t1 = (treatment == 1)
        mask_t0 = (treatment == 0)

        n1 = int(np.sum(mask_t1))
        n0 = int(np.sum(mask_t0))

        if n1 < 5 or n0 < 5:
            raise ValueError(f"Số lượng quan sát trong mỗi nhóm can thiệp quá nhỏ (N1={n1}, N0={n0}).")

        # Response indicators
        r1 = response_indicator[mask_t1]
        r0 = response_indicator[mask_t0]

        n1_obs = int(np.sum(r1 == 1))
        n0_obs = int(np.sum(r0 == 1))

        if n1_obs < 3 or n0_obs < 3:
            raise ValueError(f"Số lượng quan sát có kết quả đo lường được quá nhỏ (N1_obs={n1_obs}, N0_obs={n0_obs}).")

        p1 = float(np.mean(r1))  # Response rate in treatment
        p0 = float(np.mean(r0))  # Response rate in control
        attrition_rate_t1 = 1.0 - p1
        attrition_rate_t0 = 1.0 - p0
        overall_attrition = float(1.0 - np.mean(response_indicator))

        # Observed outcomes
        y1_obs = outcome[mask_t1 & (response_indicator == 1)]
        y0_obs = outcome[mask_t0 & (response_indicator == 1)]

        # Determine bounds [ymin, ymax]
        obs_min = float(min(np.min(y1_obs), np.min(y0_obs)))
        obs_max = float(max(np.max(y1_obs), np.max(y0_obs)))

        ymin = user_ymin if user_ymin is not None else obs_min
        ymax = user_ymax if user_ymax is not None else obs_max
        if ymin >= ymax:
            raise ValueError(f"Cận dưới ymin ({ymin}) phải nhỏ hơn cận trên ymax ({ymax}).")

        # -------------------------------------------------------------
        # Step 2: Naive Complete-Case Benchmark (MAR assumption)
        # -------------------------------------------------------------
        mu1_naive = float(np.mean(y1_obs))
        mu0_naive = float(np.mean(y0_obs))
        naive_ate = float(mu1_naive - mu0_naive)

        var1 = float(np.var(y1_obs, ddof=1)) if len(y1_obs) > 1 else 0.0
        var0 = float(np.var(y0_obs, ddof=1)) if len(y0_obs) > 1 else 0.0
        se_naive = float(np.sqrt(var1 / n1_obs + var0 / n0_obs))
        z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))
        ci_naive = [float(naive_ate - z_crit * se_naive), float(naive_ate + z_crit * se_naive)]
        p_naive = float(2.0 * (1.0 - stats.norm.cdf(abs(naive_ate) / max(1e-9, se_naive))))

        # -------------------------------------------------------------
        # Step 3: Horowitz & Manski (2000) Worst-Case Bounds
        # -------------------------------------------------------------
        # E[Y | D=1] in [mu1_naive * p1 + ymin * (1-p1), mu1_naive * p1 + ymax * (1-p1)]
        ey1_lower = float(mu1_naive * p1 + ymin * (1.0 - p1))
        ey1_upper = float(mu1_naive * p1 + ymax * (1.0 - p1))

        ey0_lower = float(mu0_naive * p0 + ymin * (1.0 - p0))
        ey0_upper = float(mu0_naive * p0 + ymax * (1.0 - p0))

        # ATE = E[Y | D=1] - E[Y | D=0]
        manski_lower = float(ey1_lower - ey0_upper)
        manski_upper = float(ey1_upper - ey0_lower)
        manski_width = float(manski_upper - manski_lower)

        # Standard errors for extreme points
        # var(ey1_lower) approx p1^2 * var1/n1_obs + ...
        se_manski_l = float(np.sqrt((p1 ** 2) * (var1 / n1_obs) + (p0 ** 2) * (var0 / n0_obs)))
        se_manski_u = float(np.sqrt((p1 ** 2) * (var1 / n1_obs) + (p0 ** 2) * (var0 / n0_obs)))

        ci_im_manski = cls._compute_imbens_manski_ci(
            lower=manski_lower,
            upper=manski_upper,
            se_lower=se_manski_l,
            se_upper=se_manski_u,
            alpha=alpha,
        )

        # -------------------------------------------------------------
        # Step 4: Lee (2009) Monotonicity Trimming Bounds
        # -------------------------------------------------------------
        # Monotonicity assumption: R(1) >= R(0) or R(0) >= R(1)
        # If p1 >= p0, treatment induces response; trim treatment group
        # If p0 > p1, control has higher response; trim control group
        lee_monotonicity_direction = "D1 >= D0" if p1 >= p0 else "D0 > D1"

        if p1 >= p0:
            excess_ratio = float((p1 - p0) / max(1e-9, p1))
            # Trim excess_ratio proportion from y1_obs
            # Lower bound: trim top excess_ratio
            # Upper bound: trim bottom excess_ratio
            y1_sorted = np.sort(y1_obs)
            k_trim = int(np.floor(len(y1_sorted) * excess_ratio))
            if k_trim == 0:
                trimmed_for_low = y1_sorted
                trimmed_for_upp = y1_sorted
                mu1_trim_low = float(np.mean(y1_sorted))
                mu1_trim_upp = float(np.mean(y1_sorted))
            else:
                # Lower bound trims the highest values
                trimmed_for_low = y1_sorted[: len(y1_sorted) - k_trim]
                mu1_trim_low = float(np.mean(trimmed_for_low))
                # Upper bound trims the lowest values
                trimmed_for_upp = y1_sorted[k_trim:]
                mu1_trim_upp = float(np.mean(trimmed_for_upp))

            lee_lower = float(mu1_trim_low - mu0_naive)
            lee_upper = float(mu1_trim_upp - mu0_naive)
            var1_trim_low = float(np.var(trimmed_for_low, ddof=1)) if len(trimmed_for_low) > 1 else var1
            var1_trim_upp = float(np.var(trimmed_for_upp, ddof=1)) if len(trimmed_for_upp) > 1 else var1
            se_lee_l = float(np.sqrt(var1_trim_low / len(trimmed_for_low) + var0 / n0_obs))
            se_lee_u = float(np.sqrt(var1_trim_upp / len(trimmed_for_upp) + var0 / n0_obs))
        else:
            excess_ratio = float((p0 - p1) / max(1e-9, p0))
            y0_sorted = np.sort(y0_obs)
            k_trim = int(np.floor(len(y0_sorted) * excess_ratio))
            if k_trim == 0:
                trimmed_for_low_0 = y0_sorted
                trimmed_for_upp_0 = y0_sorted
                mu0_trim_low = float(np.mean(y0_sorted))
                mu0_trim_upp = float(np.mean(y0_sorted))
            else:
                # Lower bound for ATE = mu1 - mu0_trim_upp (so trim lowest from control)
                trimmed_for_upp_0 = y0_sorted[k_trim:]
                mu0_trim_upp = float(np.mean(trimmed_for_upp_0))
                # Upper bound for ATE = mu1 - mu0_trim_low (so trim highest from control)
                trimmed_for_low_0 = y0_sorted[: len(y0_sorted) - k_trim]
                mu0_trim_low = float(np.mean(trimmed_for_low_0))

            lee_lower = float(mu1_naive - mu0_trim_upp)
            lee_upper = float(mu1_naive - mu0_trim_low)
            var0_trim_low = float(np.var(trimmed_for_low_0, ddof=1)) if len(trimmed_for_low_0) > 1 else var0
            var0_trim_upp = float(np.var(trimmed_for_upp_0, ddof=1)) if len(trimmed_for_upp_0) > 1 else var0
            se_lee_l = float(np.sqrt(var1 / n1_obs + var0_trim_upp / len(trimmed_for_upp_0)))
            se_lee_u = float(np.sqrt(var1 / n1_obs + var0_trim_low / len(trimmed_for_low_0)))

        lee_width = float(lee_upper - lee_lower)
        ci_im_lee = cls._compute_imbens_manski_ci(
            lower=lee_lower,
            upper=lee_upper,
            se_lower=se_lee_l,
            se_upper=se_lee_u,
            alpha=alpha,
        )

        # -------------------------------------------------------------
        # Step 5: Manski & Pepper (2000) Monotone Treatment Selection (MTS) Bounds
        # -------------------------------------------------------------
        # Under MTS: E[Y(1) | D=1] >= E[Y(1) | D=0] and E[Y(0) | D=1] >= E[Y(0) | D=0]
        # This yields upper bound for ATE: Delta_U = E[Y | D=1, R=1] - ey0_lower
        mts_upper = float(min(manski_upper, mu1_naive - ey0_lower))
        mts_lower = float(manski_lower)  # MTS does not automatically tighten lower bound
        mts_width = float(mts_upper - mts_lower)
        ci_im_mts = cls._compute_imbens_manski_ci(
            lower=mts_lower,
            upper=mts_upper,
            se_lower=se_manski_l,
            se_upper=se_manski_u,
            alpha=alpha,
        )

        # -------------------------------------------------------------
        # Step 6: Sensitivity Analysis Grid
        # -------------------------------------------------------------
        # Evaluate estimated ATE as a function of the missing population mean
        # mu_missing in [ymin, ymax]
        grid_points = 25
        grid_mu = np.linspace(ymin, ymax, grid_points)
        sensitivity_curve: List[Dict[str, float]] = []

        for mu_miss in grid_mu:
            # Imputed E[Y|D=1] = p1 * mu1_naive + (1-p1) * mu_miss
            # Imputed E[Y|D=0] = p0 * mu0_naive + (1-p0) * mu_miss
            ate_imputed = (p1 * mu1_naive + (1.0 - p1) * mu_miss) - (p0 * mu0_naive + (1.0 - p0) * mu_miss)
            sensitivity_curve.append({
                "mu_attrited": round(float(mu_miss), 3),
                "implied_ate": round(float(ate_imputed), 4),
            })

        # Does the bounds include zero?
        manski_straddles_zero = bool(manski_lower <= 0.0 <= manski_upper)
        lee_straddles_zero = bool(lee_lower <= 0.0 <= lee_upper)

        # -------------------------------------------------------------
        # Step 7: Dual-Panel Responsive SVG Visualizer
        # -------------------------------------------------------------
        svg_chart = cls._render_dual_panel_svg(
            naive_ate=naive_ate,
            ci_naive=ci_naive,
            manski_bounds=[manski_lower, manski_upper],
            ci_im_manski=ci_im_manski,
            lee_bounds=[lee_lower, lee_upper],
            ci_im_lee=ci_im_lee,
            mts_bounds=[mts_lower, mts_upper],
            ci_im_mts=ci_im_mts,
            sensitivity_curve=sensitivity_curve,
            ymin=ymin,
            ymax=ymax,
            p1=p1,
            p0=p0,
        )

        # -------------------------------------------------------------
        # Step 8: APA 7th Edition Academic Narrative
        # -------------------------------------------------------------
        apa_narrative = (
            f"A nonparametric partial identification analysis of survey non-response and selective attrition "
            f"was conducted with total sample N = {N} (N_T = {n1}, N_C = {n0}). "
            f"Differential attrition was observed between study arms: the response rate was {p1 * 100:.1f}% "
            f"in the treatment group and {p0 * 100:.1f}% in the control group (differential gap = {abs(p1 - p0) * 100:.1f}%). "
            f"The naive complete-case estimator, assuming Missing At Random (MAR), yielded an Average Treatment Effect of "
            f"ATE = {naive_ate:.3f} (SE = {se_naive:.3f}, 95% CI [{ci_naive[0]:.3f}, {ci_naive[1]:.3f}], p = {p_naive:.4f}). "
            f"Without making missing-data ignorability assumptions, Horowitz & Manski (2000) worst-case bounds over the outcome range "
            f"[{ymin:.2f}, {ymax:.2f}] yielded sharp identification interval [{manski_lower:.3f}, {manski_upper:.3f}] "
            f"(width = {manski_width:.3f}; 95% Imbens-Manski CI [{ci_im_manski[0]:.3f}, {ci_im_manski[1]:.3f}]). "
            f"Under the Lee (2009) monotonic attrition condition with trimming proportion q = {excess_ratio:.3f}, "
            f"the trimmed bounding interval tightened substantially to [{lee_lower:.3f}, {lee_upper:.3f}] "
            f"(width = {lee_width:.3f}; 95% Imbens-Manski CI [{ci_im_lee[0]:.3f}, {ci_im_lee[1]:.3f}]), "
            f"{'excluding zero, confirming that causal sign is robust to selective attrition' if not lee_straddles_zero else 'straddling zero, indicating that causal sign is sensitive to worst-case non-random dropout'}. "
            f"Under Monotone Treatment Selection (Manski & Pepper, 2000), the upper bound was tightened to {mts_upper:.3f}."
        )

        return {
            "status": "success",
            "sample_size": N,
            "sample_treatment": n1,
            "sample_control": n0,
            "response_rate_treatment": round(p1, 4),
            "response_rate_control": round(p0, 4),
            "overall_attrition_rate": round(overall_attrition, 4),
            "outcome_bounds": {"ymin": round(ymin, 3), "ymax": round(ymax, 3)},
            "naive_complete_case": {
                "ate": round(naive_ate, 4),
                "std_error": round(se_naive, 4),
                "ci_95": [round(ci_naive[0], 4), round(ci_naive[1], 4)],
                "p_value": round(p_naive, 5),
                "assumes_mar": True,
            },
            "manski_horowitz_bounds": {
                "lower_bound": round(manski_lower, 4),
                "upper_bound": round(manski_upper, 4),
                "interval_width": round(manski_width, 4),
                "imbens_manski_ci_95": [round(ci_im_manski[0], 4), round(ci_im_manski[1], 4)],
                "straddles_zero": manski_straddles_zero,
            },
            "lee_trimming_bounds": {
                "lower_bound": round(lee_lower, 4),
                "upper_bound": round(lee_upper, 4),
                "interval_width": round(lee_width, 4),
                "trimming_ratio": round(excess_ratio, 4),
                "monotonicity_direction": lee_monotonicity_direction,
                "imbens_manski_ci_95": [round(ci_im_lee[0], 4), round(ci_im_lee[1], 4)],
                "straddles_zero": lee_straddles_zero,
            },
            "mts_bounds": {
                "lower_bound": round(mts_lower, 4),
                "upper_bound": round(mts_upper, 4),
                "interval_width": round(mts_width, 4),
                "imbens_manski_ci_95": [round(ci_im_mts[0], 4), round(ci_im_mts[1], 4)],
            },
            "sensitivity_grid": sensitivity_curve,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _compute_imbens_manski_ci(
        cls,
        lower: float,
        upper: float,
        se_lower: float,
        se_upper: float,
        alpha: float = 0.05,
    ) -> List[float]:
        """
        Computes Imbens & Manski (2004) / Stoye (2009) Confidence Intervals
        for partially identified parameters.
        Adjusts critical value c_alpha between z_{1-alpha} (when delta > 0)
        and z_{1-alpha/2} (when delta = 0).
        """
        width = max(0.0, upper - lower)
        max_se = max(1e-9, max(se_lower, se_upper))
        delta_std = width / max_se

        # Solve for c_alpha such that Phi(c_alpha + delta_std) - Phi(-c_alpha) = 1 - alpha
        # When delta_std is large (>3), c_alpha -> z_{1-alpha} = 1.645
        # When delta_std is zero, c_alpha -> z_{1-alpha/2} = 1.960
        if delta_std > 5.0:
            c_alpha = float(stats.norm.ppf(1.0 - alpha))
        elif delta_std < 0.01:
            c_alpha = float(stats.norm.ppf(1.0 - alpha / 2.0))
        else:
            # Simple root finding / interpolation
            def objective(c: float) -> float:
                return float(stats.norm.cdf(c + delta_std) - stats.norm.cdf(-c) - (1.0 - alpha))

            # Bracket between z_{1-alpha} and z_{1-alpha/2}
            c_low = float(stats.norm.ppf(1.0 - alpha))
            c_high = float(stats.norm.ppf(1.0 - alpha / 2.0))
            c_alpha = (c_low + c_high) / 2.0
            for _ in range(20):
                val = objective(c_alpha)
                if abs(val) < 1e-4:
                    break
                if val < 0:
                    c_low = c_alpha
                else:
                    c_high = c_alpha
                c_alpha = (c_low + c_high) / 2.0

        ci_l = lower - c_alpha * se_lower
        ci_u = upper + c_alpha * se_upper
        return [float(ci_l), float(ci_u)]

    @classmethod
    def _render_dual_panel_svg(
        cls,
        naive_ate: float,
        ci_naive: List[float],
        manski_bounds: List[float],
        ci_im_manski: List[float],
        lee_bounds: List[float],
        ci_im_lee: List[float],
        mts_bounds: List[float],
        ci_im_mts: List[float],
        sensitivity_curve: List[Dict[str, float]],
        ymin: float,
        ymax: float,
        p1: float,
        p0: float,
    ) -> str:
        """Renders dual-panel responsive SVG visualizer for partial identification."""
        width = 940
        height = 380
        p_w = 425
        p_h = 295
        margin = {"top": 45, "bottom": 35, "left": 140, "right": 25}

        # -------------------------------------------------------------
        # Panel A: Partially Identified Intervals Comparison
        # -------------------------------------------------------------
        pA_x = 25
        pA_y = 15
        x0_a = pA_x + margin["left"]
        y0_a = pA_y + margin["top"]
        iw_a = p_w - margin["left"] - margin["right"]
        ih_a = p_h - margin["top"] - margin["bottom"]

        all_vals = (
            ci_naive
            + manski_bounds
            + ci_im_manski
            + lee_bounds
            + ci_im_lee
            + mts_bounds
            + [0.0]
        )
        min_v = min(all_vals)
        max_v = max(all_vals)
        span_v = max(0.5, max_v - min_v)
        l_scale = min_v - 0.1 * span_v
        u_scale = max_v + 0.1 * span_v

        def map_x_a(v: float) -> float:
            return x0_a + ((v - l_scale) / (u_scale - l_scale)) * iw_a

        zero_x_a = map_x_a(0.0)

        # 4 rows: Naive MAR, Lee (2009) Trimming, MTS (2000), Manski (2000) Worst-Case
        models = [
            {
                "name": "Naive (MAR / Case-Delete)",
                "point": naive_ate,
                "interval": None,
                "ci": ci_naive,
                "color": "#94a3b8",
            },
            {
                "name": "Lee (2009) Monotone Trim",
                "point": None,
                "interval": lee_bounds,
                "ci": ci_im_lee,
                "color": "#10b981",
            },
            {
                "name": "MTS Bounds (Pepper 2000)",
                "point": None,
                "interval": mts_bounds,
                "ci": ci_im_mts,
                "color": "#38bdf8",
            },
            {
                "name": "Manski Worst-Case Bounds",
                "point": None,
                "interval": manski_bounds,
                "ci": ci_im_manski,
                "color": "#f59e0b",
            },
        ]

        row_h_a = ih_a / len(models)
        elements_a = []

        for i, m in enumerate(models):
            cy = y0_a + (i + 0.5) * row_h_a

            # CI line
            cx_ci_l = map_x_a(m["ci"][0])
            cx_ci_u = map_x_a(m["ci"][1])
            elements_a.append(
                f'<line x1="{cx_ci_l:.1f}" y1="{cy:.1f}" x2="{cx_ci_u:.1f}" y2="{cy:.1f}" '
                f'stroke="{m["color"]}" stroke-width="1.8" stroke-dasharray="3,3" opacity="0.6"/>'
            )
            elements_a.append(
                f'<line x1="{cx_ci_l:.1f}" y1="{cy-4:.1f}" x2="{cx_ci_l:.1f}" y2="{cy+4:.1f}" '
                f'stroke="{m["color"]}" stroke-width="1.5"/>'
            )
            elements_a.append(
                f'<line x1="{cx_ci_u:.1f}" y1="{cy-4:.1f}" x2="{cx_ci_u:.1f}" y2="{cy+4:.1f}" '
                f'stroke="{m["color"]}" stroke-width="1.5"/>'
            )

            # Identification interval or point
            if m["interval"] is not None:
                cx_l = map_x_a(m["interval"][0])
                cx_u = map_x_a(m["interval"][1])
                bw = max(2.0, cx_u - cx_l)
                elements_a.append(
                    f'<rect x="{cx_l:.1f}" y="{cy-6:.1f}" width="{bw:.1f}" height="12" '
                    f'fill="{m["color"]}" fill-opacity="0.25" stroke="{m["color"]}" stroke-width="2" rx="2"/>'
                )
            else:
                cx_pt = map_x_a(m["point"])
                elements_a.append(
                    f'<circle cx="{cx_pt:.1f}" cy="{cy:.1f}" r="4.5" fill="{m["color"]}" stroke="#ffffff" stroke-width="1.5"/>'
                )

            # Row label
            elements_a.append(
                f'<text x="{x0_a - 12:.1f}" y="{cy + 4:.1f}" fill="#cbd5e1" font-size="11" font-family="system-ui, sans-serif" '
                f'text-anchor="end">{m["name"]}</text>'
            )

        # -------------------------------------------------------------
        # Panel B: Sensitivity Curve to Attrited Mean
        # -------------------------------------------------------------
        pB_x = 490
        pB_y = 15
        x0_b = pB_x + 55
        y0_b = pB_y + margin["top"]
        iw_b = p_w - 55 - 20
        ih_b = p_h - margin["top"] - margin["bottom"]

        mu_min_b = ymin
        mu_max_b = ymax
        span_mu_b = max(1e-5, mu_max_b - mu_min_b)

        ate_vals_b = [pt["implied_ate"] for pt in sensitivity_curve]
        ate_min_b = min(ate_vals_b)
        ate_max_b = max(ate_vals_b)
        span_ate_b = max(0.5, ate_max_b - ate_min_b)

        def map_x_b(mu: float) -> float:
            return x0_b + ((mu - mu_min_b) / span_mu_b) * iw_b

        def map_y_b(ate: float) -> float:
            return y0_b + ih_b - ((ate - ate_min_b) / span_ate_b) * ih_b

        zero_y_b = map_y_b(0.0)

        path_points_b = []
        for pt in sensitivity_curve:
            bx = map_x_b(pt["mu_attrited"])
            by = map_y_b(pt["implied_ate"])
            path_points_b.append(f"{bx:.1f},{by:.1f}")
        polyline_b = " ".join(path_points_b)

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#0f172a; border-radius:12px; font-family:system-ui, -apple-system, sans-serif;">
  <defs>
    <linearGradient id="sensGradient" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#a855f7" />
    </linearGradient>
  </defs>

  <!-- Panel A Header -->
  <text x="{pA_x + 10}" y="{pA_y + 24}" fill="#ffffff" font-size="13" font-weight="700">Panel A: Khoảng Định Danh Một Phần (Partial Identification Intervals)</text>
  <text x="{pA_x + 10}" y="{pA_y + 38}" fill="#94a3b8" font-size="10">So sánh Naive vs Lee (2009) Trim vs MTS vs Manski (2000) Worst-Case (95% Imbens-Manski CIs)</text>

  <!-- Panel A Box & Zero Line -->
  <rect x="{x0_a}" y="{y0_a}" width="{iw_a}" height="{ih_a}" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1" rx="4"/>
  <line x1="{zero_x_a:.1f}" y1="{y0_a}" x2="{zero_x_a:.1f}" y2="{y0_a + ih_a}" stroke="#ef4444" stroke-width="1.2" stroke-dasharray="4,4"/>
  <text x="{zero_x_a:.1f}" y="{y0_a - 6}" fill="#ef4444" font-size="10" font-weight="600" text-anchor="middle">ATE = 0.0</text>

  <!-- Panel A Elements -->
  {''.join(elements_a)}

  <!-- Panel A X Axis -->
  <line x1="{x0_a}" y1="{y0_a + ih_a}" x2="{x0_a + iw_a}" y2="{y0_a + ih_a}" stroke="#475569" stroke-width="1"/>
  <text x="{x0_a}" y="{y0_a + ih_a + 18}" fill="#64748b" font-size="10" text-anchor="middle">{l_scale:.2f}</text>
  <text x="{x0_a + iw_a}" y="{y0_a + ih_a + 18}" fill="#64748b" font-size="10" text-anchor="middle">{u_scale:.2f}</text>
  <text x="{x0_a + iw_a / 2}" y="{y0_a + ih_a + 22}" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">Tác Động Can Thiệp (Average Treatment Effect \u0394)</text>

  <!-- Panel B Header -->
  <text x="{pB_x + 10}" y="{pB_y + 24}" fill="#ffffff" font-size="13" font-weight="700">Panel B: Đường Nhạy Cảm Attrition (Sensitivity Curve)</text>
  <text x="{pB_x + 10}" y="{pB_y + 38}" fill="#94a3b8" font-size="10">Tác động can thiệp ATE theo giả định trung bình nhóm mất dấu \u03bc_missing \u2208 [{ymin:.1f}, {ymax:.1f}]</text>

  <!-- Panel B Box & Axes -->
  <rect x="{x0_b}" y="{y0_b}" width="{iw_b}" height="{ih_b}" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1" rx="4"/>
  {f'<line x1="{x0_b}" y1="{zero_y_b:.1f}" x2="{x0_b + iw_b}" y2="{zero_y_b:.1f}" stroke="#ef4444" stroke-width="1" stroke-dasharray="3,3"/>' if y0_b <= zero_y_b <= y0_b + ih_b else ''}

  <!-- Panel B Polyline -->
  <polyline points="{polyline_b}" fill="none" stroke="url(#sensGradient)" stroke-width="2.5" stroke-linecap="round"/>

  <!-- Panel B Points -->
  <circle cx="{map_x_b(sensitivity_curve[0]['mu_attrited']):.1f}" cy="{map_y_b(sensitivity_curve[0]['implied_ate']):.1f}" r="4" fill="#38bdf8"/>
  <circle cx="{map_x_b(sensitivity_curve[-1]['mu_attrited']):.1f}" cy="{map_y_b(sensitivity_curve[-1]['implied_ate']):.1f}" r="4" fill="#a855f7"/>

  <!-- Panel B Axis Labels -->
  <line x1="{x0_b}" y1="{y0_b + ih_b}" x2="{x0_b + iw_b}" y2="{y0_b + ih_b}" stroke="#475569" stroke-width="1"/>
  <text x="{x0_b}" y="{y0_b + ih_b + 18}" fill="#64748b" font-size="10" text-anchor="middle">{mu_min_b:.1f}</text>
  <text x="{x0_b + iw_b}" y="{y0_b + ih_b + 18}" fill="#64748b" font-size="10" text-anchor="middle">{mu_max_b:.1f}</text>
  <text x="{x0_b + iw_b / 2}" y="{y0_b + ih_b + 22}" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">Trung Bình Nhóm Attrition (\u03bc_attrited)</text>

  <!-- Panel B Y-axis ticks -->
  <text x="{x0_b - 8}" y="{y0_b + 10}" fill="#64748b" font-size="9" text-anchor="end">{ate_max_b:.2f}</text>
  <text x="{x0_b - 8}" y="{y0_b + ih_b}" fill="#64748b" font-size="9" text-anchor="end">{ate_min_b:.2f}</text>
</svg>'''
        return svg


def run_partial_attrition_bounds_analysis(
    records: List[Dict[str, Any]],
    treatment_col: str,
    outcome_col: str,
    response_col: Optional[str] = None,
    user_ymin: Optional[float] = None,
    user_ymax: Optional[float] = None,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Helper function to parse records into numpy arrays and invoke PartialAttritionBoundsEngine.
    If response_col is None, treats None / NaN in outcome_col as unobserved (R=0).
    """
    treatment_list: List[int] = []
    outcome_list: List[float] = []
    response_list: List[int] = []

    for r in records:
        t_raw = r.get(treatment_col)
        if t_raw is None or str(t_raw).strip() == "":
            continue
        try:
            t_val = 1 if float(t_raw) > 0.5 else 0
        except (ValueError, TypeError):
            continue

        if response_col is not None:
            r_raw = r.get(response_col)
            try:
                r_val = 1 if float(r_raw) > 0.5 else 0
            except (ValueError, TypeError):
                r_val = 0
        else:
            y_check = r.get(outcome_col)
            r_val = 0 if (y_check is None or str(y_check).strip() == "" or str(y_check).lower() in ("nan", "none", "null")) else 1

        y_raw = r.get(outcome_col)
        if r_val == 1:
            try:
                y_val = float(y_raw)
            except (ValueError, TypeError):
                r_val = 0
                y_val = 0.0
        else:
            y_val = 0.0

        treatment_list.append(t_val)
        outcome_list.append(y_val)
        response_list.append(r_val)

    if len(treatment_list) < 20:
        raise ValueError(f"Không đủ dữ liệu hợp lệ để ước lượng chặn non-random attrition (N={len(treatment_list)} < 20).")

    return PartialAttritionBoundsEngine.evaluate(
        treatment=np.array(treatment_list),
        outcome=np.array(outcome_list),
        response_indicator=np.array(response_list),
        treatment_name=treatment_col,
        outcome_name=outcome_col,
        user_ymin=user_ymin,
        user_ymax=user_ymax,
        alpha=alpha,
    )
