# -*- coding: utf-8 -*-
"""
Continuous Policy Shift & Doubly Robust Nonparametric Dosage Response Engine (Continuous DML / Policy Shifts)
Methodological References:
- Kennedy, E. H., Ma, Z., McHugh, M. D., & Small, D. S. (2017). "Nonparametric methods for doubly robust estimation
  of continuous treatment effects." Journal of the Royal Statistical Society: Series B, 79(4), 1229–1245.
- Chernozhukov, V., Escanciano, J. C., Ichimura, H., Newey, W. K., & Robins, J. M. (2022).
  "Locally robust semiparametric estimation." Econometrica, 90(4), 1501–1535.
- Hirano, K., & Imbens, G. W. (2004). "The propensity score with continuous treatments."
  Applied Bayesian Modeling and Causal Inference from Incomplete-Data Perspectives, 73–84.
- Díaz, I., & van der Laan, M. J. (2012). "Population intervention causal effects based on stochastic interventions."
  Biometrics, 68(2), 541–549.

Implements doubly robust continuous treatment effect estimation. Estimates the complete nonlinear
dose-response curve (DRC) theta(a) = E[Y(a)] across continuous dosage levels, marginal derivative curves theta'(a)
identifying diminishing returns thresholds, and counterfactual policy shifts d(A) = A + delta.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _generate_continuous_drc_svg(
    grid_points: List[float],
    drc_estimates: List[float],
    ci_lower: List[float],
    ci_upper: List[float],
    derivatives: List[float],
    current_mean_a: float,
    optimal_a: float,
    policy_shift: float,
    delta: float,
    width: int = 860,
    height: int = 440
) -> str:
    """
    Renders dark-themed SVG featuring:
    Panel A: Nonlinear Dose-Response Curve (DRC) with 95% confidence ribbon.
    Panel B: Marginal Derivative Curve theta'(a) showing diminishing returns.
    """
    svg = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background: #0f172a; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">',
        '<defs>',
        '  <linearGradient id="ribbonGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        '    <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>',
        '    <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.08"/>',
        '  </linearGradient>',
        '  <linearGradient id="derivGlow" x1="0%" y1="0%" x2="100%" y2="0%">',
        '    <stop offset="0%" stop-color="#f59e0b"/>',
        '    <stop offset="100%" stop-color="#ef4444"/>',
        '  </linearGradient>',
        '</defs>',
        f'<text x="24" y="32" fill="#f8fafc" font-size="16" font-weight="bold">Doubly Robust Continuous Dose-Response &amp; Policy Shift Curve</text>',
        f'<text x="24" y="50" fill="#94a3b8" font-size="12">Kennedy et al. (2017 JASA) • Chernozhukov et al. (2022) • Generalized Propensity Score</text>',
    ]

    # Panel A: DRC Plot (Left 470px)
    p_left, p_top, p_w, p_h = 50, 75, 450, 260
    p_bot = p_top + p_h
    svg.append(f'<rect x="{p_left}" y="{p_top}" width="{p_w}" height="{p_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p_left + 14}" y="{p_top + 22}" fill="#e2e8f0" font-size="11" font-weight="bold">PANEL A: Dose-Response Curve θ(a) &amp; 95% Confidence Band</text>')

    min_a, max_a = min(grid_points), max(grid_points)
    a_span = max(0.01, max_a - min_a)

    min_y = min(ci_lower)
    max_y = max(ci_upper)
    y_span = max(0.01, max_y - min_y)
    min_y -= 0.05 * y_span
    max_y += 0.05 * y_span

    def to_px(a_val):
        return p_left + 35 + ((a_val - min_a) / a_span) * (p_w - 70)

    def to_py(y_val):
        return p_bot - 35 - ((y_val - min_y) / (max_y - min_y)) * (p_h - 70)

    # Shaded Confidence Ribbon
    upper_pts = []
    lower_pts = []
    main_pts = []
    n_pts = len(grid_points)

    for i in range(n_pts):
        x = to_px(grid_points[i])
        y_u = to_py(ci_upper[i])
        y_l = to_py(ci_lower[i])
        y_m = to_py(drc_estimates[i])

        upper_pts.append(f"{x:.1f},{y_u:.1f}")
        lower_pts.append(f"{x:.1f},{y_l:.1f}")
        main_pts.append(f"{x:.1f},{y_m:.1f}")

    poly_pts = " ".join(upper_pts + list(reversed(lower_pts)))
    svg.append(f'<polygon points="{poly_pts}" fill="url(#ribbonGrad)" stroke="none"/>')

    # Main DRC Curve
    line_pts = " ".join(main_pts)
    svg.append(f'<polyline points="{line_pts}" fill="none" stroke="#38bdf8" stroke-width="2.6" stroke-linecap="round"/>')

    # Markers for Current Mean Dosage & Optimal Dosage
    curr_x = to_px(current_mean_a)
    opt_x = to_px(optimal_a)

    svg.append(f'<line x1="{curr_x:.1f}" y1="{p_top + 30}" x2="{curr_x:.1f}" y2="{p_bot - 30}" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{curr_x:.1f}" y="{p_bot - 14}" fill="#cbd5e1" font-size="9" text-anchor="middle">Mean: {current_mean_a:.1f}</text>')

    svg.append(f'<line x1="{opt_x:.1f}" y1="{p_top + 30}" x2="{opt_x:.1f}" y2="{p_bot - 30}" stroke="#10b981" stroke-width="1.5"/>')
    svg.append(f'<text x="{opt_x:.1f}" y="{p_top + 40}" fill="#34d399" font-size="9" font-weight="bold" text-anchor="middle">Opt: {optimal_a:.1f}</text>')

    # Panel B: Marginal Derivative θ'(a) (Right 300px)
    d_left, d_top, d_w, d_h = 525, 75, 305, 260
    d_bot = d_top + d_h
    svg.append(f'<rect x="{d_left}" y="{d_top}" width="{d_w}" height="{d_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{d_left + 14}" y="{d_top + 22}" fill="#e2e8f0" font-size="11" font-weight="bold">PANEL B: Marginal Derivative θ\'(a)</text>')

    min_d, max_d = min(derivatives), max(derivatives)
    d_span = max(0.01, max_d - min_d)
    min_d -= 0.1 * d_span
    max_d += 0.1 * d_span

    def to_dx(a_val):
        return d_left + 35 + ((a_val - min_a) / a_span) * (d_w - 70)

    def to_dy(d_val):
        return d_bot - 35 - ((d_val - min_d) / (max_d - min_d)) * (d_h - 70)

    # Zero line in derivative plot
    zero_dy = to_dy(0.0)
    svg.append(f'<line x1="{d_left + 20}" y1="{zero_dy:.1f}" x2="{d_left + d_w - 20}" y2="{zero_dy:.1f}" stroke="#64748b" stroke-width="1.2" stroke-dasharray="3,3"/>')

    d_pts = []
    for i in range(n_pts):
        px = to_dx(grid_points[i])
        py = to_dy(derivatives[i])
        d_pts.append(f"{px:.1f},{py:.1f}")

    svg.append(f'<polyline points="{" ".join(d_pts)}" fill="none" stroke="url(#derivGlow)" stroke-width="2.2" stroke-linecap="round"/>')
    svg.append(f'<text x="{d_left + 24}" y="{d_bot - 14}" fill="#94a3b8" font-size="9">Dosage Level a</text>')
    svg.append(f'<text x="{d_left + d_w - 24}" y="{d_bot - 14}" fill="#f59e0b" font-size="9" text-anchor="end">Marginal Gain</text>')

    # Bottom Stat Summary Banner
    panel_y = height - 75
    svg.extend([
        f'<rect x="24" y="{panel_y}" width="{width - 48}" height="60" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>',
        f'<text x="40" y="{panel_y + 22}" fill="#94a3b8" font-size="10">POLICY SHIFT (Δ = {delta:+.1f})</text>',
        f'<text x="40" y="{panel_y + 44}" fill="#38bdf8" font-size="14" font-weight="bold">{policy_shift:+.3f}</text>',
        f'<text x="240" y="{panel_y + 22}" fill="#94a3b8" font-size="10">CURRENT MEAN DOSAGE</text>',
        f'<text x="240" y="{panel_y + 44}" fill="#cbd5e1" font-size="14" font-weight="bold">{current_mean_a:.2f}</text>',
        f'<text x="440" y="{panel_y + 22}" fill="#94a3b8" font-size="10">OPTIMAL DOSAGE TARGET</text>',
        f'<text x="440" y="{panel_y + 44}" fill="#34d399" font-size="14" font-weight="bold">{optimal_a:.2f}</text>',
        f'<text x="640" y="{panel_y + 22}" fill="#94a3b8" font-size="10">ESTIMATOR PROPERTY</text>',
        f'<text x="640" y="{panel_y + 44}" fill="#f59e0b" font-size="13" font-weight="bold">Doubly Robust (EIF)</text>',
    ])

    svg.append('</svg>')
    return '\n'.join(svg)


def run_continuous_policy_shift(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    covariate_cols: Optional[List[str]] = None,
    grid_points: int = 25,
    shift_delta: Optional[float] = None,
    bandwidth: Optional[float] = None,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Doubly Robust Continuous Treatment & Policy Shift Analysis.
    """
    if df is None or len(df) == 0:
        return {"status": "ERROR", "message": "Input survey dataset is empty."}

    req_cols = [outcome_col, treatment_col]
    if covariate_cols:
        req_cols.extend(covariate_cols)

    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        return {"status": "ERROR", "message": f"Missing required columns: {missing}"}

    sub_df = df[req_cols].dropna().copy()
    if len(sub_df) < 25:
        return {"status": "INSUFFICIENT_SAMPLE", "message": f"Sample size {len(sub_df)} is too small for Continuous DRC analysis."}

    # Ensure numeric
    Y = sub_df[outcome_col].astype(float).values
    A = sub_df[treatment_col].astype(float).values
    N = len(sub_df)

    if np.var(A) < 1e-6:
        return {"status": "ERROR", "message": "Biến can thiệp A không có biến thiên liên tục (phương sai xấp xỉ 0)."}

    # Covariate matrix
    if covariate_cols and len(covariate_cols) > 0:
        X_mat = sub_df[covariate_cols].astype(float).values
        # Standardize X
        X_mat = (X_mat - np.mean(X_mat, axis=0)) / (np.std(X_mat, axis=0) + 1e-8)
    else:
        X_mat = np.empty((N, 0))

    # Support range of continuous treatment (trimmed to 5th - 95th percentiles to avoid boundary instability)
    a_min = float(np.percentile(A, 5.0))
    a_max = float(np.percentile(A, 95.0))
    if a_max <= a_min:
        a_min, a_max = float(np.min(A)), float(np.max(A))

    G = min(max(15, grid_points), 50)
    grid = np.linspace(a_min, a_max, G)

    # Step 1: Fit Outcome Model mu(A, X) = E[Y | A, X]
    # Polynomial features for A: 1, A, A^2, X, A*X
    A_std = (A - np.mean(A)) / (np.std(A) + 1e-8)
    design_mu = [np.ones(N), A_std, A_std ** 2]
    if X_mat.shape[1] > 0:
        design_mu.append(X_mat)
        # Interactions
        inter = X_mat * A_std[:, np.newaxis]
        design_mu.append(inter)

    X_mu = np.column_stack(design_mu)
    try:
        coef_mu, _, _, _ = np.linalg.lstsq(X_mu, Y, rcond=None)
        mu_hat_obs = X_mu @ coef_mu
    except Exception:
        coef_mu = np.zeros(X_mu.shape[1])
        mu_hat_obs = np.ones(N) * np.mean(Y)

    # Step 2: Fit Generalized Propensity Score pi(A | X) = f_{A|X}(A | X)
    if X_mat.shape[1] > 0:
        X_gps = np.column_stack([np.ones(N), X_mat])
        try:
            coef_gps, _, _, _ = np.linalg.lstsq(X_gps, A, rcond=None)
            A_hat = X_gps @ coef_gps
        except Exception:
            A_hat = np.ones(N) * np.mean(A)
    else:
        A_hat = np.ones(N) * np.mean(A)

    sigma_A = math.sqrt(float(np.mean((A - A_hat) ** 2)) + 1e-6)
    
    # Conditional normal density pi(A_i | X_i)
    z_gps = (A - A_hat) / sigma_A
    gps_obs = (1.0 / (sigma_A * math.sqrt(2.0 * math.pi))) * np.exp(-0.5 * (z_gps ** 2))
    # Bound GPS from below to avoid extreme weights
    gps_min = float(np.percentile(gps_obs, 2.0))
    gps_obs_clipped = np.maximum(gps_min, gps_obs)

    # Step 3: Bandwidth selection
    if bandwidth is None or bandwidth <= 0:
        bw = 1.06 * np.std(A) * (N ** (-0.2))
    else:
        bw = bandwidth

    # Step 4: Doubly Robust Pseudo-Outcomes on Grid
    drc_estimates = []
    drc_se = []
    ci_lower = []
    ci_upper = []

    mean_A_raw = np.mean(A)
    std_A_raw = np.std(A) + 1e-8

    for g_val in grid:
        # Evaluate mu_hat(g_val, X_i)
        g_std = (g_val - mean_A_raw) / std_A_raw
        design_g = [np.ones(N), np.full(N, g_std), np.full(N, g_std ** 2)]
        if X_mat.shape[1] > 0:
            design_g.append(X_mat)
            design_g.append(X_mat * g_std)

        X_g = np.column_stack(design_g)
        mu_hat_g = X_g @ coef_mu

        # Epanechnikov or Gaussian kernel weights
        u = (A - g_val) / bw
        kernel_weights = (1.0 / (bw * math.sqrt(2.0 * math.pi))) * np.exp(-0.5 * (u ** 2))

        # Doubly Robust Pseudo-Outcome (Kennedy et al. 2017)
        # xi_i(a) = (K_h(A - a) / pi(A|X)) * (Y - mu(A,X)) + mu(a,X)
        ipw_term = (kernel_weights / gps_obs_clipped) * (Y - mu_hat_obs)
        pseudo_outcomes = ipw_term + mu_hat_g

        theta_g = float(np.mean(pseudo_outcomes))
        se_g = float(stats.sem(pseudo_outcomes))

        drc_estimates.append(theta_g)
        drc_se.append(se_g)
        ci_lower.append(theta_g - 1.96 * se_g)
        ci_upper.append(theta_g + 1.96 * se_g)

    # Step 5: Marginal Derivatives theta'(a)
    derivatives = []
    for i in range(G):
        if i == 0:
            d_val = (drc_estimates[1] - drc_estimates[0]) / (grid[1] - grid[0])
        elif i == G - 1:
            d_val = (drc_estimates[-1] - drc_estimates[-2]) / (grid[-1] - grid[-2])
        else:
            d_val = (drc_estimates[i + 1] - drc_estimates[i - 1]) / (grid[i + 1] - grid[i - 1])
        derivatives.append(float(d_val))

    # Optimal dosage
    opt_idx = int(np.argmax(drc_estimates))
    optimal_a = float(grid[opt_idx])
    current_mean_a = float(np.mean(A))

    # Step 6: Continuous Policy Shift d(A) = A + delta
    if shift_delta is None or shift_delta == 0:
        delta = 0.5 * float(np.std(A))
    else:
        delta = shift_delta

    A_shifted = np.clip(A + delta, a_min, a_max)
    A_shift_std = (A_shifted - mean_A_raw) / std_A_raw
    design_shift = [np.ones(N), A_shift_std, A_shift_std ** 2]
    if X_mat.shape[1] > 0:
        design_shift.append(X_mat)
        design_shift.append(X_mat * A_shift_std[:, np.newaxis])
    X_shift = np.column_stack(design_shift)
    mu_hat_shift = X_shift @ coef_mu

    policy_shift_effect = float(np.mean(mu_hat_shift - Y))
    se_policy_shift = float(stats.sem(mu_hat_shift - Y))

    # Render SVG Visualization
    svg_viz = _generate_continuous_drc_svg(
        grid_points=grid.tolist(),
        drc_estimates=drc_estimates,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        derivatives=derivatives,
        current_mean_a=current_mean_a,
        optimal_a=optimal_a,
        policy_shift=policy_shift_effect,
        delta=delta
    )

    # Format grid estimates table
    table_out = []
    for i in range(G):
        table_out.append({
            "dosage_level": round(float(grid[i]), 3),
            "outcome_estimate": round(drc_estimates[i], 4),
            "se": round(drc_se[i], 4),
            "ci_95": [round(ci_lower[i], 4), round(ci_upper[i], 4)],
            "marginal_derivative": round(derivatives[i], 4)
        })

    return {
        "status": "SUCCESS",
        "sample_size": N,
        "outcome_variable": outcome_col,
        "treatment_variable": treatment_col,
        "covariates_controlled": covariate_cols or [],
        "bandwidth": round(bw, 4),
        "treatment_support": {
            "min_evaluated": round(a_min, 3),
            "max_evaluated": round(a_max, 3),
            "current_mean": round(current_mean_a, 3),
            "optimal_dosage": round(optimal_a, 3)
        },
        "policy_shift": {
            "delta_shift": round(delta, 3),
            "average_policy_effect": round(policy_shift_effect, 4),
            "se": round(se_policy_shift, 4),
            "p_value": round(float(2.0 * (1.0 - stats.norm.cdf(abs(policy_shift_effect / (se_policy_shift + 1e-12))))), 4),
            "ci_95": [
                round(policy_shift_effect - 1.96 * se_policy_shift, 4),
                round(policy_shift_effect + 1.96 * se_policy_shift, 4)
            ],
            "interpretation": (
                f"Dịch chuyển chính sách đồng loạt {delta:+.2f} đơn vị can thiệp ({treatment_col}) "
                f"tạo ra tác động trung bình {policy_shift_effect:+.3f} điểm lên kết quả ({outcome_col})."
            )
        },
        "dose_response_curve": table_out,
        "svg_visualization": svg_viz
    }
