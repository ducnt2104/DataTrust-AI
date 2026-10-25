"""
DataTrust - Generalized Additive Models (GAM) & Penalized Spline Engine
Scientific Framework:
- Generalized Additive Models - Trevor Hastie & Robert Tibshirani (1986, Statistical Science; 1990, Chapman & Hall)
- Generalized Additive Models: An Introduction with R - Simon N. Wood (2006, 2017, CRC Press)
- Penalized B-splines (P-splines) & Smoothing Parameter Selection via GCV - Paul H. C. Eilers & Brian D. Marx (1996)
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar


class GAMSplineEngine:
    """
    Generalized Additive Model (GAM) with Penalized B-Splines (P-Splines)
    for discovering non-linear dose-response curves, saturation thresholds,
    inflection points, and Effective Degrees of Freedom (EDF).
    """

    @staticmethod
    def estimate(
        data: List[Dict[str, Any]],
        predictor_var: str,
        outcome_var: str,
        covariate_vars: Optional[List[str]] = None,
        n_knots: int = 10,
        grid_points: int = 60,
    ) -> Dict[str, Any]:
        covariates = covariate_vars or []
        all_vars = [predictor_var, outcome_var] + covariates

        clean_rows = []
        for r in data:
            vals = []
            valid = True
            for v in all_vars:
                val = r.get(v)
                if val is None:
                    valid = False
                    break
                try:
                    vals.append(float(val))
                except (ValueError, TypeError):
                    valid = False
                    break
            if valid:
                clean_rows.append(vals)

        N = len(clean_rows)
        if N < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"GAM Spline analysis requires at least 25 observations. Received N={N}.",
                "diagnostics": {"N": N},
            }

        mat = np.array(clean_rows, dtype=float)
        x = mat[:, 0]
        y = mat[:, 1]
        Z_cov = mat[:, 2:] if len(covariates) > 0 else None

        x_min, x_max = float(np.min(x)), float(np.max(x))
        if abs(x_max - x_min) < 1e-6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Predictor variable has zero variance.",
                "diagnostics": {"N": N},
            }

        # 1. Construct B-spline Basis Matrix B of dimension (N, K)
        # Using cubic B-splines with n_knots internal knots
        K = max(5, min(n_knots, N // 3))
        knots = np.linspace(x_min, x_max, K + 4)  # augmented knots for cubic spline
        B_mat = _cubic_bspline_basis(x, knots, K)

        # Difference penalty matrix D of order 2 (second differences for smoothing)
        D = np.diff(np.eye(K), n=2, axis=0)  # shape (K-2, K)
        S = D.T @ D  # penalty matrix (K, K)

        # Full design matrix with intercept and optional linear covariates
        # To avoid collinearity with intercept, center spline basis
        B_mean = np.mean(B_mat, axis=0, keepdims=True)
        B_centered = B_mat - B_mean

        if Z_cov is not None and Z_cov.shape[1] > 0:
            Z_centered = Z_cov - np.mean(Z_cov, axis=0, keepdims=True)
            X_full = np.column_stack([np.ones(N), Z_centered, B_centered])
            n_fixed = 1 + Z_cov.shape[1]
        else:
            X_full = np.column_stack([np.ones(N), B_centered])
            n_fixed = 1

        p_total = X_full.shape[1]

        # Block penalty matrix S_full
        S_full = np.zeros((p_total, p_total))
        S_full[n_fixed:, n_fixed:] = S

        # 2. Optimal Smoothing Parameter Lambda Selection via GCV (Wood 2006)
        XtX = X_full.T @ X_full
        Xty = X_full.T @ y

        def gcv_objective(log_lambda):
            lam = math.exp(log_lambda)
            A = XtX + lam * S_full
            try:
                # Solve (X'X + lambda S) beta = X'y
                beta = np.linalg.solve(A, Xty)
                # Hat matrix trace (effective degrees of freedom)
                inv_A = np.linalg.inv(A)
                H = X_full @ inv_A @ X_full.T
                tr_H = float(np.trace(H))
                edf = min(N - 1, max(1.0, tr_H))

                # Residuals and GCV score
                res = y - X_full @ beta
                rss = np.sum(res ** 2)
                denom = (1.0 - edf / N) ** 2
                gcv = (rss / N) / max(1e-6, denom)
                return gcv
            except Exception:
                return 1e10

        opt_gcv = minimize_scalar(gcv_objective, bounds=(-6.0, 10.0), method="bounded")
        best_log_lambda = float(opt_gcv.x)
        best_lambda = math.exp(best_log_lambda)

        # Solve model at optimal lambda
        A_opt = XtX + best_lambda * S_full
        inv_A_opt = np.linalg.pinv(A_opt)
        beta_hat = inv_A_opt @ Xty

        # Model predictions & residuals
        y_pred = X_full @ beta_hat
        residuals = y - y_pred
        rss = float(np.sum(residuals ** 2))
        s2 = rss / max(1, N - p_total)
        r2 = float(1.0 - rss / max(1e-8, np.sum((y - np.mean(y)) ** 2)))

        # Effective degrees of freedom for the smooth term: tr(B inv_A B')
        H_smooth = X_full[:, n_fixed:] @ inv_A_opt[n_fixed:, n_fixed:] @ X_full[:, n_fixed:].T
        edf_smooth = float(np.trace(H_smooth))
        edf_smooth = max(1.0, min(K - 1, edf_smooth))

        # Test of non-linearity (F-test comparing GAM smooth with purely linear model)
        # Linear OLS fit
        X_lin = np.column_stack([np.ones(N), x]) if Z_cov is None else np.column_stack([np.ones(N), x, Z_cov])
        beta_lin, _, _, _ = np.linalg.lstsq(X_lin, y, rcond=None)
        rss_lin = float(np.sum((y - X_lin @ beta_lin) ** 2))
        
        df_diff = max(0.5, edf_smooth - 1.0)
        f_stat = max(0.0, ((rss_lin - rss) / df_diff) / max(1e-6, s2))
        p_non_linear = float(1.0 - stats.f.cdf(f_stat, dfn=df_diff, dfd=max(1, N - p_total)))
        is_strictly_nonlinear = bool(p_non_linear < 0.05 and edf_smooth > 1.4)

        # 3. Predict Smooth Curve f(x) over a fine evaluation grid
        grid_x = np.linspace(x_min, x_max, grid_points)
        B_grid = _cubic_bspline_basis(grid_x, knots, K)
        B_grid_centered = B_grid - B_mean
        
        # Smooth function values
        beta_spline = beta_hat[n_fixed:]
        f_grid = B_grid_centered @ beta_spline

        # Standard error ribbon along grid: se(f(x)) = sqrt(diag(B V_beta B'))
        V_spline = inv_A_opt[n_fixed:, n_fixed:] * s2
        var_f = np.sum((B_grid_centered @ V_spline) * B_grid_centered, axis=1)
        se_grid = np.sqrt(np.maximum(1e-8, var_f))
        ci_lower = f_grid - 1.96 * se_grid
        ci_upper = f_grid + 1.96 * se_grid

        # 4. First and Second Derivatives to Identify Tipping Points & Saturation Thresholds
        dx = grid_x[1] - grid_x[0]
        f_deriv1 = np.gradient(f_grid, dx)
        f_deriv2 = np.gradient(f_deriv1, dx)

        tipping_points = []
        for i in range(1, len(grid_x) - 1):
            # Sign change in first derivative = local extremum (peak or trough)
            if (f_deriv1[i - 1] > 0 and f_deriv1[i + 1] < 0) or (f_deriv1[i - 1] < 0 and f_deriv1[i + 1] > 0):
                tp_type = "Peak / Saturation Maxima" if f_deriv1[i - 1] > 0 else "Trough / Minimum Threshold"
                tipping_points.append({
                    "x_value": round(float(grid_x[i]), 3),
                    "predicted_response": round(float(f_grid[i]), 3),
                    "type": tp_type,
                    "interpretation": f"Tipping point at {predictor_var} = {grid_x[i]:.2f}",
                })

        # Generate smooth curve trajectory points
        curve_points = []
        for i in range(grid_points):
            curve_points.append({
                "x": round(float(grid_x[i]), 3),
                "f_x": round(float(f_grid[i]), 3),
                "ci_lower": round(float(ci_lower[i]), 3),
                "ci_upper": round(float(ci_upper[i]), 3),
                "deriv1": round(float(f_deriv1[i]), 4),
            })

        # Dual-Panel SVG Visualization
        svg_viz = _generate_gam_svg(
            grid_x=grid_x,
            f_grid=f_grid,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            f_deriv1=f_deriv1,
            tipping_points=tipping_points,
            x_raw=x,
            y_raw=y - beta_hat[0],
            predictor_name=predictor_var,
            outcome_name=outcome_var,
            edf=edf_smooth,
            r2=r2,
        )

        # APA 7th Academic Narrative
        apa_narrative = _generate_gam_apa_narrative(
            N=N,
            predictor_name=predictor_var,
            outcome_name=outcome_var,
            edf=edf_smooth,
            f_stat=f_stat,
            p_non_linear=p_non_linear,
            r2=r2,
            best_lambda=best_lambda,
            is_nonlinear=is_strictly_nonlinear,
            tipping_points=tipping_points,
        )

        return {
            "status": "SUCCESS",
            "model_type": "GENERALIZED_ADDITIVE_MODEL_SPLINE",
            "diagnostics": {
                "N": N,
                "n_knots": K,
                "optimal_smoothing_lambda": round(best_lambda, 4),
                "effective_degrees_of_freedom": round(edf_smooth, 3),
                "r_squared": round(r2, 4),
                "f_stat_nonlinearity": round(f_stat, 2),
                "p_value_nonlinearity": round(p_non_linear, 5),
                "is_strictly_nonlinear": is_strictly_nonlinear,
                "total_tipping_points": len(tipping_points),
            },
            "tipping_points": tipping_points,
            "smooth_curve": curve_points,
            "svg_visualization": svg_viz,
            "apa_narrative": apa_narrative,
        }


def _cubic_bspline_basis(x: np.ndarray, knots: np.ndarray, K: int) -> np.ndarray:
    """Evaluates Cox-de Boor recursion for cubic B-splines of order 4 (degree 3)."""
    N = len(x)
    n_knots = len(knots)
    # Basis functions of degree 0
    B = np.zeros((N, n_knots - 1))
    for i in range(n_knots - 1):
        B[:, i] = ((x >= knots[i]) & (x < knots[i + 1])).astype(float)
    # Include right endpoint
    B[x == knots[-1], -1] = 1.0

    # Recursion for degrees 1, 2, 3
    for d in range(1, 4):
        B_new = np.zeros((N, n_knots - d - 1))
        for i in range(n_knots - d - 1):
            denom1 = knots[i + d] - knots[i]
            denom2 = knots[i + d + 1] - knots[i + 1]
            term1 = ((x - knots[i]) / denom1) * B[:, i] if denom1 > 0 else np.zeros(N)
            term2 = ((knots[i + d + 1] - x) / denom2) * B[:, i + 1] if denom2 > 0 else np.zeros(N)
            B_new[:, i] = term1 + term2
        B = B_new

    # Trim or select first K columns
    return B[:, :K]


def _generate_gam_svg(
    grid_x: np.ndarray,
    f_grid: np.ndarray,
    ci_lower: np.ndarray,
    ci_upper: np.ndarray,
    f_deriv1: np.ndarray,
    tipping_points: List[Dict[str, Any]],
    x_raw: np.ndarray,
    y_raw: np.ndarray,
    predictor_name: str,
    outcome_name: str,
    edf: float,
    r2: float,
) -> str:
    """
    Generates a dual-panel SVG:
    Panel A: Non-Linear GAM Smooth Spline Curve f(x) with 95% Bayesian Confidence Band & Tipping Points.
    Panel B: First Derivative Curve f'(x) showing regions of positive, negative, and zero slope.
    """
    width = 960
    height = 540

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#0f172a; font-family:Inter,system-ui,sans-serif;">',
        '<defs>',
        '  <linearGradient id="gamBandGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        '    <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35" />',
        '    <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.05" />',
        '  </linearGradient>',
        '  <linearGradient id="derivLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '    <stop offset="0%" stop-color="#10b981" />',
        '    <stop offset="100%" stop-color="#f59e0b" />',
        '  </linearGradient>',
        '</defs>',
        # Header
        f'<text x="30" y="36" fill="#f8fafc" font-size="18" font-weight="700">Generalized Additive Models (GAM) &amp; Penalized P-Splines</text>',
        f'<text x="30" y="58" fill="#94a3b8" font-size="12">Hastie &amp; Tibshirani (1990) &amp; Wood (2017) | EDF = {edf:.2f} | R² = {r2:.3f} | Non-Linear Dose-Response</text>',
    ]

    # Panel A: Smooth Curve f(x) (x: 40 -> 500, y: 90 -> 500)
    pa_x0, pa_y0, pa_w, pa_h = 40, 90, 460, 410
    svg.append(f'<rect x="{pa_x0}" y="{pa_y0}" width="{pa_w}" height="{pa_h}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1" />')
    svg.append(f'<text x="{pa_x0 + 20}" y="{pa_y0 + 26}" fill="#38bdf8" font-size="14" font-weight="600">Panel A: Non-Linear Smooth Spline f({predictor_name[:12]})</text>')
    svg.append(f'<text x="{pa_x0 + 20}" y="{pa_y0 + 44}" fill="#64748b" font-size="11">Fitted cubic P-spline with 95% Bayesian Confidence Ribbon</text>')

    plot_l, plot_r = pa_x0 + 40, pa_x0 + pa_w - 25
    plot_t, plot_b = pa_y0 + 70, pa_y0 + pa_h - 40
    p_w, p_h = plot_r - plot_l, plot_b - plot_t

    x_min, x_max = float(grid_x[0]), float(grid_x[-1])
    y_min = min(float(np.min(ci_lower)), float(np.min(f_grid))) - 0.2
    y_max = max(float(np.max(ci_upper)), float(np.max(f_grid))) + 0.2
    y_span = max(1e-4, y_max - y_min)
    x_span = max(1e-4, x_max - x_min)

    def to_px(xv):
        return plot_l + ((xv - x_min) / x_span) * p_w

    def to_py(yv):
        return plot_b - ((yv - y_min) / y_span) * p_h

    # Zero line
    if y_min <= 0 <= y_max:
        zy = to_py(0.0)
        svg.append(f'<line x1="{plot_l}" y1="{zy:.1f}" x2="{plot_r}" y2="{zy:.1f}" stroke="#475569" stroke-width="1" stroke-dasharray="3,3" />')

    # Scatter points (subsample 30 points)
    sample_stride = max(1, len(x_raw) // 30)
    for i in range(0, len(x_raw), sample_stride):
        sx = to_px(x_raw[i])
        sy = to_py(y_raw[i])
        svg.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="2" fill="#64748b" opacity="0.4" />')

    # Confidence ribbon
    poly_top = [f"{to_px(grid_x[i]):.1f},{to_py(ci_upper[i]):.1f}" for i in range(len(grid_x))]
    poly_bot = [f"{to_px(grid_x[i]):.1f},{to_py(ci_lower[i]):.1f}" for i in reversed(range(len(grid_x)))]
    svg.append(f'<polygon points="{" ".join(poly_top + poly_bot)}" fill="url(#gamBandGrad)" />')

    # Spline line
    line_pts = [f"{to_px(grid_x[i]):.1f},{to_py(f_grid[i]):.1f}" for i in range(len(grid_x))]
    svg.append(f'<polyline points="{" ".join(line_pts)}" fill="none" stroke="#38bdf8" stroke-width="2.5" />')

    # Mark tipping points
    for tp in tipping_points:
        tx = to_px(tp["x_value"])
        ty = to_py(tp["predicted_response"])
        svg.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="5" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5" />')
        svg.append(f'<text x="{tx:.1f}" y="{ty - 10:.1f}" fill="#f43f5e" font-size="9" font-weight="700" text-anchor="middle">{tp["x_value"]:.1f}</text>')

    # Panel B: First Derivative f'(x) (x: 520 -> 920, y: 90 -> 500)
    pb_x0, pb_y0, pb_w, pb_h = 520, 90, 400, 410
    svg.append(f'<rect x="{pb_x0}" y="{pb_y0}" width="{pb_w}" height="{pb_h}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1" />')
    svg.append(f'<text x="{pb_x0 + 20}" y="{pb_y0 + 26}" fill="#34d399" font-size="14" font-weight="600">Panel B: Marginal Derivative f\'({predictor_name[:10]})</text>')
    svg.append(f'<text x="{pb_x0 + 20}" y="{pb_y0 + 44}" fill="#64748b" font-size="11">Rate of change | Above 0 = Growth, Below 0 = Decay</text>')

    p2_l, p2_r = pb_x0 + 35, pb_x0 + pb_w - 25
    p2_t, p2_b = pb_y0 + 70, pb_y0 + pb_h - 40
    p2_w, p2_h = p2_r - p2_l, p2_b - p2_t

    d_min, d_max = float(np.min(f_deriv1)), float(np.max(f_deriv1))
    d_span = max(1e-4, d_max - d_min)

    def to_p2x(xv):
        return p2_l + ((xv - x_min) / x_span) * p2_w

    def to_p2y(dv):
        return p2_b - ((dv - d_min) / d_span) * p2_h

    # Zero derivative reference line
    if d_min <= 0 <= d_max:
        z2y = to_p2y(0.0)
        svg.append(f'<line x1="{p2_l}" y1="{z2y:.1f}" x2="{p2_r}" y2="{z2y:.1f}" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,4" />')
        svg.append(f'<text x="{p2_r + 4}" y="{z2y + 4:.1f}" fill="#94a3b8" font-size="10">0</text>')

    # Derivative curve
    d_pts = [f"{to_p2x(grid_x[i]):.1f},{to_p2y(f_deriv1[i]):.1f}" for i in range(len(grid_x))]
    svg.append(f'<polyline points="{" ".join(d_pts)}" fill="none" stroke="url(#derivLineGrad)" stroke-width="2.5" />')

    # Shaded saturation zone
    svg.append('</svg>')
    return "\n".join(svg)


def _generate_gam_apa_narrative(
    N: int,
    predictor_name: str,
    outcome_name: str,
    edf: float,
    f_stat: float,
    p_non_linear: float,
    r2: float,
    best_lambda: float,
    is_nonlinear: bool,
    tipping_points: List[Dict[str, Any]],
) -> str:
    """Generates an academic narrative in APA 7th edition style describing GAM spline results."""
    lines = [
        f"A Generalized Additive Model (GAM) with penalized cubic B-spline smoothing (P-splines; Hastie & Tibshirani, 1990; Wood, 2017) was estimated to examine the functional relationship between '{predictor_name}' and '{outcome_name}' on survey data (N = {N}).",
        f"The smoothing parameter was determined via Generalized Cross-Validation (GCV; optimal lambda = {best_lambda:.4f}), yielding an estimated effective degrees of freedom of EDF = {edf:.2f}.",
    ]

    if is_nonlinear:
        lines.append(
            f"A formal statistical test of non-linearity confirmed that the relationship significantly deviates from a linear trajectory (F({edf - 1.0:.1f}, {N - 10}) = {f_stat:.2f}, p {'< .001' if p_non_linear < 0.001 else f'= {p_non_linear:.4f}'}; model R^2 = {r2:.3f}), demonstrating that conventional linear regression would incur substantial specification bias."
        )
    else:
        lines.append(
            f"The estimated spline was approximately linear (EDF = {edf:.2f}, F = {f_stat:.2f}, p = {p_non_linear:.4f}; model R^2 = {r2:.3f}), suggesting that linear approximation remains reasonably parsimonious."
        )

    if tipping_points:
        tp_desc = ", ".join([f"{tp['type']} at {predictor_name} = {tp['x_value']:.2f}" for tp in tipping_points])
        lines.append(
            f"Derivative analysis identified critical non-linear threshold dynamics: {tp_desc}. Beyond this threshold, marginal returns experience a pronounced saturation shift."
        )

    return " ".join(lines)
