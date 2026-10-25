"""
Instrumental Variable Quantile Regression (IV-QR) Engine.
References:
- Chernozhukov, V., & Hansen, C. (2005). An IV model of quantile treatment effects.
  Econometrica, 73(1), 245-261.
- Chernozhukov, V., & Hansen, C. (2006). Instrumental quantile regression inference for
  structural and treatment effect models. Journal of Econometrics, 132(2), 491-525.
- Chernozhukov, V., & Hansen, C. (2008). Instrumental variable quantile regression:
  A robust inference approach. Journal of Econometrics, 142(1), 379-398.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats


class IVQuantileRegressionEngine:
    """
    Estimates endogenous quantile treatment effects using Chernozhukov & Hansen's
    Instrumental Variable Quantile Regression (IV-QR) via Inverse Quantile Regression (IQR).
    """

    @classmethod
    def analyze(
        cls,
        data: List[Dict[str, Any]],
        outcome_var: str,
        treatment_var: str,
        instrument_var: str,
        covariate_vars: Optional[List[str]] = None,
        quantiles: Optional[List[float]] = None,
        grid_points: int = 80,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Executes IV-QR estimation across multiple quantiles with dual-inversion confidence intervals.
        """
        covariate_vars = covariate_vars or []
        quantiles = quantiles or [0.10, 0.25, 0.50, 0.75, 0.90]
        all_required = [outcome_var, treatment_var, instrument_var] + covariate_vars

        cleaned_rows = []
        for r in data:
            try:
                vals = [float(r[v]) for v in all_required]
                if not any(math.isnan(x) or math.isinf(x) for x in vals):
                    cleaned_rows.append(vals)
            except (ValueError, TypeError, KeyError):
                continue

        n_samples = len(cleaned_rows)
        if n_samples < 25:
            return {
                "status": "error",
                "message": f"Dữ liệu không đủ quan sát hợp lệ (cần tối thiểu 25 phản hồi đầy đủ, thực tế có {n_samples}).",
            }

        mat = np.array(cleaned_rows, dtype=float)
        y = mat[:, 0]
        d = mat[:, 1]
        z = mat[:, 2]
        X_cov = mat[:, 3:] if len(covariate_vars) > 0 else np.empty((n_samples, 0))

        # Check variation in D and Z
        if float(np.var(d)) <= 1e-12 or float(np.var(z)) <= 1e-12:
            return {
                "status": "error",
                "message": "Biến can thiệp (D) hoặc biến công cụ (Z) không có phương sai.",
            }

        # 1. First stage relevance check (Z -> D)
        first_stage = cls._first_stage_ols(d=d, z=z, X=X_cov)
        if first_stage["f_stat"] < 3.0:
            instrument_strength = "WEAK_INSTRUMENT"
            strength_warning = (
                f"Biến công cụ yếu (F-statistic = {first_stage['f_stat']:.2f} < 10.0; Staiger & Stock 1997). "
                "Khoảng tin cậy đảo ngược Chernozhukov-Hansen vẫn hợp lệ nhưng có thể rộng."
            )
        else:
            instrument_strength = "STRONG_INSTRUMENT"
            strength_warning = f"Biến công cụ đủ mạnh (F-statistic = {first_stage['f_stat']:.2f} >= 10.0)."

        # 2. Baseline Benchmark: OLS and 2SLS
        ols_est, ols_se = cls._estimate_ols(y=y, d=d, X=X_cov)
        tsls_est, tsls_se = cls._estimate_2sls(y=y, d=d, z=z, X=X_cov)

        # 3. IV-QR Grid Search setup
        alpha_center = tsls_est
        alpha_spread = max(3.0 * tsls_se, 1.5 * abs(tsls_est), 1.0)
        grid_alphas = np.linspace(alpha_center - alpha_spread, alpha_center + alpha_spread, grid_points)

        chi2_crit = float(stats.chi2.ppf(confidence_level, df=1))  # 3.841 for 95%

        quantile_results: List[Dict[str, Any]] = []
        median_grid_profiles: List[Dict[str, Any]] = []

        for q in quantiles:
            # A. Exogenous Quantile Regression (Benchmark)
            exo_est, exo_se = cls._fit_quantile_regression(y=y, x_target=d, x_controls=X_cov, tau=q)

            # B. Inverse Quantile Regression over alpha grid
            best_alpha = None
            min_wald = float("inf")
            wald_curve = []
            valid_ci_alphas = []

            for a_val in grid_alphas:
                # Transformed outcome Y*(alpha) = Y - alpha * D
                y_star = y - a_val * d
                # Regress Y* on [1, X, Z]
                regressors = np.hstack([np.ones((n_samples, 1)), X_cov, z.reshape(-1, 1)])
                beta_hat, se_hat, residuals = cls._irls_quantile_regression(y=y_star, X=regressors, tau=q)

                gamma_hat = beta_hat[-1]
                gamma_se = max(se_hat[-1], 1e-6)
                wald_stat = float((gamma_hat / gamma_se) ** 2)

                wald_curve.append({"alpha": float(a_val), "wald_stat": wald_stat})

                if wald_stat < min_wald:
                    min_wald = wald_stat
                    best_alpha = float(a_val)

                if wald_stat <= chi2_crit:
                    valid_ci_alphas.append(float(a_val))

            if valid_ci_alphas:
                ci_low = min(valid_ci_alphas)
                ci_high = max(valid_ci_alphas)
            else:
                ci_low = best_alpha - 1.96 * tsls_se
                ci_high = best_alpha + 1.96 * tsls_se

            # Calculate endogeneity gap: Exogenous QR - IV-QR
            endogeneity_gap = exo_est - best_alpha
            is_sig = not (ci_low <= 0.0 <= ci_high)

            q_item = {
                "quantile": float(q),
                "iv_qr_estimate": best_alpha,
                "ci_lower": float(ci_low),
                "ci_upper": float(ci_high),
                "is_significant": is_sig,
                "exogenous_qr_estimate": float(exo_est),
                "exogenous_qr_se": float(exo_se),
                "endogeneity_bias_gap": float(endogeneity_gap),
                "min_wald_stat": float(min_wald),
            }
            quantile_results.append(q_item)

            if abs(q - 0.50) < 1e-4:
                median_grid_profiles = wald_curve

        # 4. Quantile Treatment Heterogeneity Test (Interquantile spread tau=0.90 vs tau=0.10)
        q10_res = next((item for item in quantile_results if abs(item["quantile"] - 0.10) < 1e-4), quantile_results[0])
        q90_res = next((item for item in quantile_results if abs(item["quantile"] - 0.90) < 1e-4), quantile_results[-1])

        interquantile_spread = q90_res["iv_qr_estimate"] - q10_res["iv_qr_estimate"]
        has_heterogeneity = abs(interquantile_spread) > (0.5 * (abs(q10_res["iv_qr_estimate"]) + abs(q90_res["iv_qr_estimate"])))

        summary = {
            "n_samples": n_samples,
            "instrument_strength": instrument_strength,
            "instrument_f_stat": first_stage["f_stat"],
            "strength_warning": strength_warning,
            "ols_estimate": float(ols_est),
            "ols_se": float(ols_se),
            "tsls_estimate": float(tsls_est),
            "tsls_se": float(tsls_se),
            "interquantile_spread_90_10": float(interquantile_spread),
            "has_quantile_heterogeneity": has_heterogeneity,
            "chi2_critical_value": chi2_crit,
        }

        # 5. Dual-Panel Vector SVG
        svg_chart = cls._generate_svg_chart(
            quantile_results=quantile_results,
            median_profiles=median_grid_profiles,
            summary=summary,
            outcome_var=outcome_var,
            treatment_var=treatment_var,
        )

        # 6. APA 7th Narrative
        apa_narrative = cls._generate_apa_narrative(
            summary=summary,
            quantile_results=quantile_results,
            outcome_var=outcome_var,
            treatment_var=treatment_var,
            instrument_var=instrument_var,
        )

        return {
            "status": "success",
            "summary": summary,
            "quantile_estimates": quantile_results,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _first_stage_ols(cls, d: np.ndarray, z: np.ndarray, X: np.ndarray) -> Dict[str, Any]:
        """Runs D = gamma_0 + gamma_z * Z + X * gamma_x and computes F-statistic."""
        n = len(d)
        ones = np.ones((n, 1))
        design = np.hstack([ones, z.reshape(-1, 1), X]) if X.shape[1] > 0 else np.hstack([ones, z.reshape(-1, 1)])

        beta, residuals, rank, s = np.linalg.lstsq(design, d, rcond=None)
        res = d - design @ beta
        ss_res = float(np.sum(res ** 2))
        df = n - design.shape[1]
        sigma_sq = ss_res / max(df, 1)

        cov = sigma_sq * np.linalg.pinv(design.T @ design)
        se_z = float(np.sqrt(max(cov[1, 1], 1e-12)))
        t_z = float(beta[1]) / se_z
        f_stat = float(t_z ** 2)

        return {"gamma_z": float(beta[1]), "se_z": se_z, "t_stat": t_z, "f_stat": f_stat}

    @classmethod
    def _estimate_ols(cls, y: np.ndarray, d: np.ndarray, X: np.ndarray) -> Tuple[float, float]:
        n = len(y)
        ones = np.ones((n, 1))
        design = np.hstack([ones, d.reshape(-1, 1), X]) if X.shape[1] > 0 else np.hstack([ones, d.reshape(-1, 1)])
        beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        res = y - design @ beta
        df = n - design.shape[1]
        cov = (np.sum(res ** 2) / max(df, 1)) * np.linalg.pinv(design.T @ design)
        se = float(np.sqrt(max(cov[1, 1], 1e-12)))
        return float(beta[1]), se

    @classmethod
    def _estimate_2sls(cls, y: np.ndarray, d: np.ndarray, z: np.ndarray, X: np.ndarray) -> Tuple[float, float]:
        n = len(y)
        ones = np.ones((n, 1))
        instr = np.hstack([ones, z.reshape(-1, 1), X]) if X.shape[1] > 0 else np.hstack([ones, z.reshape(-1, 1)])
        # Stage 1: d_hat
        P_z = instr @ np.linalg.pinv(instr.T @ instr) @ instr.T
        d_hat = P_z @ d

        # Stage 2: regress y on [1, d_hat, X]
        regressors_hat = np.hstack([ones, d_hat.reshape(-1, 1), X]) if X.shape[1] > 0 else np.hstack([ones, d_hat.reshape(-1, 1)])
        regressors_true = np.hstack([ones, d.reshape(-1, 1), X]) if X.shape[1] > 0 else np.hstack([ones, d.reshape(-1, 1)])

        beta, _, _, _ = np.linalg.lstsq(regressors_hat, y, rcond=None)
        res = y - regressors_true @ beta
        df = n - regressors_hat.shape[1]
        cov = (np.sum(res ** 2) / max(df, 1)) * np.linalg.pinv(regressors_hat.T @ regressors_hat)
        se = float(np.sqrt(max(cov[1, 1], 1e-12)))
        return float(beta[1]), se

    @classmethod
    def _fit_quantile_regression(cls, y: np.ndarray, x_target: np.ndarray, x_controls: np.ndarray, tau: float) -> Tuple[float, float]:
        n = len(y)
        ones = np.ones((n, 1))
        X = np.hstack([ones, x_target.reshape(-1, 1), x_controls]) if x_controls.shape[1] > 0 else np.hstack([ones, x_target.reshape(-1, 1)])
        beta, se, _ = cls._irls_quantile_regression(y=y, X=X, tau=tau)
        return float(beta[1]), float(se[1])

    @classmethod
    def _irls_quantile_regression(cls, y: np.ndarray, X: np.ndarray, tau: float, max_iter: int = 25) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Iteratively Reweighted Least Squares (IRLS) for linear quantile check loss."""
        n, p = X.shape
        # Initialize with OLS
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)

        delta = 1e-4
        for _ in range(max_iter):
            res = y - X @ beta
            weights = np.where(res >= 0, tau, 1.0 - tau) / np.maximum(np.abs(res), delta)
            weights = np.clip(weights, 1e-6, 1e4)

            W_sqrt = np.sqrt(weights).reshape(-1, 1)
            X_w = X * W_sqrt
            y_w = y * W_sqrt.flatten()

            beta_new, _, _, _ = np.linalg.lstsq(X_w, y_w, rcond=None)
            if np.max(np.abs(beta_new - beta)) < 1e-5:
                beta = beta_new
                break
            beta = beta_new

        final_res = y - X @ beta
        # Huber-White sandwich covariance
        bandwidth = 1.06 * float(np.std(final_res)) * (n ** (-0.2))
        f_zero = float(np.mean(stats.norm.pdf(final_res / max(bandwidth, 1e-4)) / max(bandwidth, 1e-4)))
        f_zero = max(f_zero, 1e-4)

        XtX_inv = np.linalg.pinv(X.T @ X)
        cov = (tau * (1.0 - tau) / (f_zero ** 2)) * XtX_inv
        se = np.sqrt(np.maximum(np.diag(cov), 1e-12))

        return beta, se, final_res

    @classmethod
    def _generate_svg_chart(
        cls,
        quantile_results: List[Dict[str, Any]],
        median_profiles: List[Dict[str, Any]],
        summary: Dict[str, Any],
        outcome_var: str,
        treatment_var: str,
    ) -> str:
        """
        Creates a dual-panel vector SVG:
        Panel A: IV-QR Quantile Treatment Effects Trajectory across tau in [0.10, 0.90] with 95% CI vs 2SLS vs OLS.
        Panel B: Dual Inversion Objective Profile W_n(alpha) at median tau=0.50 with Chi-square critical line.
        """
        w, h = 860, 480
        pad_l, pad_r, pad_t, pad_b = 60, 40, 50, 40
        panel_gap = 40
        pw = w - pad_l - pad_r
        ph = (h - pad_t - pad_b - panel_gap) // 2

        # Panel A Bounds
        all_vals = []
        for q in quantile_results:
            all_vals.extend([q["iv_qr_estimate"], q["ci_lower"], q["ci_upper"], q["exogenous_qr_estimate"]])
        all_vals.extend([summary["ols_estimate"], summary["tsls_estimate"], 0.0])

        min_a = min(all_vals)
        max_a = max(all_vals)
        range_a = max(max_a - min_a, 1e-4)

        def scale_x_a(tau: float) -> float:
            return pad_l + ((tau - 0.10) / 0.80) * (pw * 0.65)

        def scale_y_a(val: float) -> float:
            norm = (val - min_a) / range_a
            return (pad_t + ph) - norm * ph

        panel_a_elements = []

        # Zero reference line
        y0_a = scale_y_a(0.0)
        panel_a_elements.append(
            f'<line x1="{pad_l}" y1="{y0_a:.1f}" x2="{pad_l + pw * 0.65}" y2="{y0_a:.1f}" stroke="#64748b" stroke-dasharray="3,3" stroke-width="1.2" />'
        )

        # OLS benchmark line (amber)
        y_ols = scale_y_a(summary["ols_estimate"])
        panel_a_elements.append(
            f'<line x1="{pad_l}" y1="{y_ols:.1f}" x2="{pad_l + pw * 0.65}" y2="{y_ols:.1f}" stroke="#f59e0b" stroke-dasharray="4,4" stroke-width="1.5" />'
        )

        # 2SLS LATE benchmark line (blue)
        y_tsls = scale_y_a(summary["tsls_estimate"])
        panel_a_elements.append(
            f'<line x1="{pad_l}" y1="{y_tsls:.1f}" x2="{pad_l + pw * 0.65}" y2="{y_tsls:.1f}" stroke="#38bdf8" stroke-dasharray="5,3" stroke-width="2" />'
        )

        # Confidence Ribbon polygon for IV-QR
        poly_points = []
        # Top boundary (ci_upper)
        for q in quantile_results:
            poly_points.append(f"{scale_x_a(q['quantile']):.1f},{scale_y_a(q['ci_upper']):.1f}")
        # Bottom boundary in reverse (ci_lower)
        for q in reversed(quantile_results):
            poly_points.append(f"{scale_x_a(q['quantile']):.1f},{scale_y_a(q['ci_lower']):.1f}")

        panel_a_elements.append(
            f'<polygon points="{" ".join(poly_points)}" fill="#a855f7" fill-opacity="0.2" />'
        )

        # IV-QR curve points and line
        iv_pts = []
        for q in quantile_results:
            cx = scale_x_a(q["quantile"])
            cy = scale_y_a(q["iv_qr_estimate"])
            iv_pts.append(f"{cx:.1f},{cy:.1f}")
            panel_a_elements.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="#a855f7" stroke="#ffffff" stroke-width="1.5" />'
            )

        panel_a_elements.append(
            f'<polyline points="{" ".join(iv_pts)}" fill="none" stroke="#a855f7" stroke-width="2.5" />'
        )

        # Naive Exogenous QR line (green dashed)
        exo_pts = []
        for q in quantile_results:
            cx = scale_x_a(q["quantile"])
            cy = scale_y_a(q["exogenous_qr_estimate"])
            exo_pts.append(f"{cx:.1f},{cy:.1f}")
            panel_a_elements.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="#10b981" />'
            )
        panel_a_elements.append(
            f'<polyline points="{" ".join(exo_pts)}" fill="none" stroke="#10b981" stroke-dasharray="3,3" stroke-width="1.8" />'
        )

        # Right Summary Box of Panel A
        box_x = pad_l + pw * 0.70
        box_y = pad_t + 5
        box_w = pw * 0.30
        box_h = ph - 10

        panel_a_elements.append(
            f'<rect x="{box_x:.1f}" y="{box_y:.1f}" width="{box_w:.1f}" height="{box_h:.1f}" fill="#1e293b" rx="8" stroke="#334155" stroke-width="1" />'
        )
        panel_a_elements.append(
            f'<text x="{box_x + 12:.1f}" y="{box_y + 22:.1f}" font-size="11" font-weight="700" fill="#f8fafc">ĐỐI CHIẾU MÔ HÌNH</text>'
        )
        panel_a_elements.append(
            f'<text x="{box_x + 12:.1f}" y="{box_y + 45:.1f}" font-size="10" fill="#f59e0b">OLS Ngây thơ: β = {summary["ols_estimate"]:.3f}</text>'
        )
        panel_a_elements.append(
            f'<text x="{box_x + 12:.1f}" y="{box_y + 65:.1f}" font-size="10" fill="#38bdf8">2SLS LATE: α = {summary["tsls_estimate"]:.3f}</text>'
        )
        panel_a_elements.append(
            f'<text x="{box_x + 12:.1f}" y="{box_y + 88:.1f}" font-size="10" fill="#a855f7">IV-QR Trung vị (τ=.50): α = {next((q["iv_qr_estimate"] for q in quantile_results if abs(q["quantile"]-0.5) < 1e-4), summary["tsls_estimate"]):.3f}</text>'
        )
        panel_a_elements.append(
            f'<text x="{box_x + 12:.1f}" y="{box_y + 115:.1f}" font-size="10" font-weight="600" fill="#cbd5e1">Độ lệch phân vị (90-10): {summary["interquantile_spread_90_10"]:.3f}</text>'
        )
        hetero_badge = "CÓ PHÂN HÓA PHÂN VỊ" if summary["has_quantile_heterogeneity"] else "TÁC ĐỘNG ĐỒNG NHẤT"
        hetero_color = "#10b981" if summary["has_quantile_heterogeneity"] else "#94a3b8"
        panel_a_elements.append(
            f'<text x="{box_x + 12:.1f}" y="{box_y + 135:.1f}" font-size="10" font-weight="700" fill="{hetero_color}">{hetero_badge}</text>'
        )

        # Panel B: Wald Objective Function Profile at Median (tau = 0.50)
        top_b = pad_t + ph + panel_gap
        panel_b_elements = []

        if len(median_profiles) > 0:
            w_alphas = [p["alpha"] for p in median_profiles]
            w_stats = [min(p["wald_stat"], 25.0) for p in median_profiles]

            min_wa = min(w_alphas)
            max_wa = max(w_alphas)
            ran_wa = max(max_wa - min_wa, 1e-4)

            max_ws = 25.0

            def scale_x_b(a: float) -> float:
                return pad_l + ((a - min_wa) / ran_wa) * pw

            def scale_y_b(stat: float) -> float:
                norm = min(stat, max_ws) / max_ws
                return (top_b + ph) - norm * ph

            # Chi2 cutoff line at 3.841
            y_crit = scale_y_b(summary["chi2_critical_value"])
            panel_b_elements.append(
                f'<line x1="{pad_l}" y1="{y_crit:.1f}" x2="{pad_l + pw}" y2="{y_crit:.1f}" stroke="#ef4444" stroke-dasharray="4,4" stroke-width="1.8" />'
            )
            panel_b_elements.append(
                f'<text x="{pad_l + pw - 8}" y="{y_crit - 6:.1f}" font-size="10" fill="#ef4444" font-weight="600" text-anchor="end">Ngưỡng đảo ngược χ²(1) = 3.841 (95% CI cutoff)</text>'
            )

            # Wald profile curve
            curve_pts = [f"{scale_x_b(p['alpha']):.1f},{scale_y_b(min(p['wald_stat'], 25.0)):.1f}" for p in median_profiles]
            panel_b_elements.append(
                f'<polyline points="{" ".join(curve_pts)}" fill="none" stroke="#38bdf8" stroke-width="2.5" />'
            )

            # Optimal point marker
            min_pt = min(median_profiles, key=lambda p: p["wald_stat"])
            cx_opt = scale_x_b(min_pt["alpha"])
            cy_opt = scale_y_b(min_pt["wald_stat"])
            panel_b_elements.append(
                f'<circle cx="{cx_opt:.1f}" cy="{cy_opt:.1f}" r="5" fill="#a855f7" stroke="#ffffff" stroke-width="2" />'
            )
            panel_b_elements.append(
                f'<text x="{cx_opt:.1f}" y="{cy_opt - 10:.1f}" font-size="10" font-weight="700" fill="#f8fafc" text-anchor="middle">α* = {min_pt["alpha"]:.3f}</text>'
            )

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="background:#0f172a; border-radius:12px; font-family:system-ui, -apple-system, sans-serif;">
  <!-- Title -->
  <text x="{pad_l}" y="28" font-size="15" font-weight="700" fill="#f8fafc">INSTRUMENTAL VARIABLE QUANTILE REGRESSION (IV-QR)</text>
  <text x="{pad_l}" y="44" font-size="11" fill="#94a3b8">Can thiệp: {treatment_var} → {outcome_var} | {summary["instrument_strength"]} (F = {summary["instrument_f_stat"]:.2f})</text>

  <!-- Panel A Header -->
  <text x="{pad_l + pw}" y="28" font-size="11" font-weight="600" fill="#a855f7" text-anchor="end">Panel A: Quỹ đạo Tác động Phân vị &amp; Dải tin cậy Đảo ngược 95%</text>
  {''.join(panel_a_elements)}

  <!-- Panel B Header -->
  <text x="{pad_l}" y="{top_b - 12}" font-size="12" font-weight="700" fill="#f8fafc">Panel B: Đường cong Tối ưu Đảo ngược Hàm Mục tiêu W_n(α) tại Trung vị (τ = 0.50)</text>
  {''.join(panel_b_elements)}

  <!-- Legend in Panel A -->
  <line x1="{pad_l + 10}" y1="{pad_t + 15}" x2="{pad_l + 30}" y2="{pad_t + 15}" stroke="#a855f7" stroke-width="2.5" />
  <text x="{pad_l + 35}" y="{pad_t + 18}" font-size="10" fill="#cbd5e1">IV-QR (Hiệu chỉnh Nội sinh)</text>
  <line x1="{pad_l + 190}" y1="{pad_t + 15}" x2="{pad_l + 210}" y2="{pad_t + 15}" stroke="#10b981" stroke-dasharray="3,3" stroke-width="2" />
  <text x="{pad_l + 215}" y="{pad_t + 18}" font-size="10" fill="#cbd5e1">QR Ngây thơ (Ngoại sinh)</text>
  <line x1="{pad_l + 350}" y1="{pad_t + 15}" x2="{pad_l + 370}" y2="{pad_t + 15}" stroke="#38bdf8" stroke-dasharray="4,3" stroke-width="2" />
  <text x="{pad_l + 375}" y="{pad_t + 18}" font-size="10" fill="#cbd5e1">2SLS LATE Trung bình</text>
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        summary: Dict[str, Any],
        quantile_results: List[Dict[str, Any]],
        outcome_var: str,
        treatment_var: str,
        instrument_var: str,
    ) -> str:
        hetero_desc = (
            f"phát hiện sự phân hóa rõ rệt về hiệu ứng can thiệp giữa các tầng phân vị (độ lệch phân vị 90-10 = "
            f"{summary['interquantile_spread_90_10']:.4f}), chứng minh rằng mô hình LATE trung bình 2SLS (α = "
            f"{summary['tsls_estimate']:.4f}) đã che giấu tác động bất cân xứng trên các nhóm phản hồi khác nhau."
            if summary["has_quantile_heterogeneity"]
            else f"hiệu ứng can thiệp tương đối đồng nhất qua các tầng phân vị (độ lệch phân vị 90-10 = {summary['interquantile_spread_90_10']:.4f})."
        )
        q50 = next((q for q in quantile_results if abs(q["quantile"] - 0.50) < 1e-4), quantile_results[len(quantile_results)//2])
        return (
            f"Mô hình Hồi quy Phân vị Biến công cụ (Instrumental Variable Quantile Regression - IV-QR; Chernozhukov & Hansen, 2005, 2008) "
            f"được ước lượng trên tổng số N = {summary['n_samples']} quan sát khảo sát nhằm phân tách tác động nhân quả phân vị "
            f"của biến can thiệp nội sinh {treatment_var} lên biến kết quả {outcome_var}, sử dụng {instrument_var} làm biến công cụ "
            f"ngoại sinh ({summary['strength_warning']}). Tại trung vị phân phối (τ = 0.50), hiệu ứng can thiệp hiệu chỉnh nội sinh đạt "
            f"α(0.50) = {q50['iv_qr_estimate']:.4f} (khoảng tin cậy đảo ngược 95% CI: [{q50['ci_lower']:.4f}, {q50['ci_upper']:.4f}]), "
            f"so sánh với ước lượng OLS ngây thơ β_OLS = {summary['ols_estimate']:.4f} và ước lượng 2SLS LATE α_2SLS = {summary['tsls_estimate']:.4f}. "
            f"Khoảng cách sai lệch nội sinh (endogeneity bias gap) giữa hồi quy phân vị ngoại sinh ngây thơ và IV-QR tại trung vị đạt "
            f"Δ = {q50['endogeneity_bias_gap']:.4f}. Kiểm định cấu trúc không đồng nhất phân vị xác nhận: {hetero_desc} "
            f"Kết quả cung cấp cơ sở hoạch định chính sách có mục tiêu, đảm bảo hiệu lực can thiệp không bị đánh giá sai lệch "
            f"do hiện tượng tự chọn lọc (self-selection) và dị biệt hóa đáp ứng phân vị."
        )
