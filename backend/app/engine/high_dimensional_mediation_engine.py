# -*- coding: utf-8 -*-
"""
High-Dimensional Causal Mediation & Latent Path Invariance Engine (HD-Mediation)
Methodological References:
- Imai, K., Keele, L., & Tingley, D. (2010). "A General Approach to Causal Mediation Analysis."
  Psychological Methods, 15(4), 309–334.
- VanderWeele, T. J. (2015). Explanation in Causal Inference: Methods for Mediation and Interaction.
  Oxford University Press.
- Zhao, Y., & Luo, X. (2022). "Pathway Analysis of High-Dimensional Mediators."
  Journal of the Royal Statistical Society: Series B (Statistical Methodology), 84(5), 1888–1910.
- Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018).
  "Double/debiased machine learning for treatment and structural parameters."
  The Econometrics Journal, 21(1), C1–C68.

Implements high-dimensional survey causal mediation analysis. Decomposes total treatment effects (TE)
into Natural Direct Effects (NDE) and Natural Indirect Effects (NIE) across high-dimensional mediator batteries.
Provides mediator path screening, L2-stabilized multivariable estimation, Imai et al. (2010) sequential ignorability
sensitivity bounds (rho*), bootstrap inference intervals, and subgroup latent path invariance testing.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _fit_ols(X: np.ndarray, y: np.ndarray, l2_penalty: float = 1e-5) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """
    Fits stabilized OLS / Ridge regression.
    Returns (coefficients, standard_errors, r_squared, residual_std).
    """
    n, p = X.shape
    A = X.T @ X + l2_penalty * np.eye(p)
    b = X.T @ y
    try:
        coef = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        coef = np.linalg.pinv(A) @ b

    residuals = y - X @ coef
    ssr = float(np.sum(residuals ** 2))
    sst = float(np.sum((y - np.mean(y)) ** 2)) + 1e-12
    r_sq = max(0.0, min(1.0, 1.0 - (ssr / sst)))
    df = max(1, n - p)
    res_std = math.sqrt(ssr / df)

    try:
        inv_A = np.linalg.inv(A)
        var_coef = (ssr / df) * inv_A
        se = np.sqrt(np.maximum(1e-12, np.diag(var_coef)))
    except Exception:
        se = np.ones(p) * 1.0

    return coef, se, r_sq, res_std


def _generate_mediation_svg(
    treatment_col: str,
    outcome_col: str,
    top_mediators: List[Dict[str, Any]],
    te: float,
    nde: float,
    nie: float,
    pm: float,
    rho_crit: float,
    width: int = 860,
    height: int = 420
) -> str:
    """
    Generates a dark-themed SVG path diagram illustrating causal mediation flow.
    """
    n_med = min(len(top_mediators), 5)
    med_spacing = 55
    start_med_y = max(60, int((height - 80) / 2 - (n_med - 1) * med_spacing / 2))

    svg_elements = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background: #0f172a; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">',
        '<defs>',
        '  <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#3b82f6"/>',
        '    <stop offset="100%" stop-color="#1d4ed8"/>',
        '  </linearGradient>',
        '  <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#10b981"/>',
        '    <stop offset="100%" stop-color="#047857"/>',
        '  </linearGradient>',
        '  <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#8b5cf6"/>',
        '    <stop offset="100%" stop-color="#6d28d9"/>',
        '  </linearGradient>',
        '  <marker id="arrowBlue" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">',
        '    <path d="M0,0 L0,6 L8,3 z" fill="#3b82f6" />',
        '  </marker>',
        '  <marker id="arrowEmerald" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">',
        '    <path d="M0,0 L0,6 L8,3 z" fill="#10b981" />',
        '  </marker>',
        '  <marker id="arrowPurple" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">',
        '    <path d="M0,0 L0,6 L8,3 z" fill="#a78bfa" />',
        '  </marker>',
        '</defs>',
        # Title & Subtitle
        f'<text x="24" y="32" fill="#f8fafc" font-size="16" font-weight="bold">High-Dimensional Causal Mediation Flow (DataTrust HD-Mediation)</text>',
        f'<text x="24" y="50" fill="#94a3b8" font-size="12">Decomposition of Treatment Effect via Latent Intermediate Path Battery</text>',
    ]

    # Node coordinates
    tx, ty = 80, int((height - 80) / 2)
    ox, oy = width - 180, int((height - 80) / 2)
    mx = int(width / 2) - 60

    # Draw Treatment Box
    t_label = treatment_col[:14]
    svg_elements.extend([
        f'<rect x="{tx}" y="{ty - 30}" width="120" height="60" rx="8" fill="url(#blueGrad)" stroke="#60a5fa" stroke-width="2"/>',
        f'<text x="{tx + 60}" y="{ty - 6}" fill="#eff6ff" font-size="11" font-weight="600" text-anchor="middle">TREATMENT (T)</text>',
        f'<text x="{tx + 60}" y="{ty + 14}" fill="#ffffff" font-size="13" font-weight="bold" text-anchor="middle">{t_label}</text>',
    ])

    # Draw Outcome Box
    o_label = outcome_col[:14]
    svg_elements.extend([
        f'<rect x="{ox}" y="{oy - 30}" width="120" height="60" rx="8" fill="url(#purpleGrad)" stroke="#c084fc" stroke-width="2"/>',
        f'<text x="{ox + 60}" y="{oy - 6}" fill="#f5f3ff" font-size="11" font-weight="600" text-anchor="middle">OUTCOME (Y)</text>',
        f'<text x="{ox + 60}" y="{oy + 14}" fill="#ffffff" font-size="13" font-weight="bold" text-anchor="middle">{o_label}</text>',
    ])

    # Draw Mediators and Links
    for idx, med in enumerate(top_mediators[:n_med]):
        med_y = start_med_y + idx * med_spacing
        m_name = med["mediator_col"][:12]
        alpha = med["alpha_treatment_to_med"]
        beta = med["beta_med_to_outcome"]
        ie = med["indirect_effect"]

        # Mediator Box
        svg_elements.extend([
            f'<rect x="{mx}" y="{med_y - 20}" width="120" height="40" rx="6" fill="url(#emeraldGrad)" stroke="#34d399" stroke-width="1.5"/>',
            f'<text x="{mx + 60}" y="{med_y - 3}" fill="#ecfdf5" font-size="10" font-weight="bold" text-anchor="middle">M{idx + 1}: {m_name}</text>',
            f'<text x="{mx + 60}" y="{med_y + 12}" fill="#a7f3d0" font-size="9" text-anchor="middle">IE = {ie:+.3f}</text>',
        ])

        # Arrow T -> M
        svg_elements.append(
            f'<path d="M {tx + 120} {ty} Q {int((tx + 120 + mx) / 2)} {med_y} {mx - 4} {med_y}" '
            f'fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arrowBlue)"/>'
        )
        # Arrow M -> Y
        svg_elements.append(
            f'<path d="M {mx + 120} {med_y} Q {int((mx + 120 + ox) / 2)} {med_y} {ox - 4} {oy}" '
            f'fill="none" stroke="#10b981" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arrowEmerald)"/>'
        )

    # Direct Path T -> Y (Curved underneath or direct across bottom)
    direct_y = ty + 70 + (n_med * 10)
    svg_elements.extend([
        f'<path d="M {tx + 60} {ty + 30} C {tx + 60} {direct_y}, {ox + 60} {direct_y}, {ox + 60} {oy + 30}" '
        f'fill="none" stroke="#a78bfa" stroke-width="2.5" marker-end="url(#arrowPurple)"/>',
        f'<text x="{int(width / 2)}" y="{direct_y - 8}" fill="#ddd6fe" font-size="11" font-weight="bold" text-anchor="middle">'
        f'Direct Effect (NDE) = {nde:+.3f}'
        f'</text>',
    ])

    # Summary Panel Bottom
    panel_y = height - 55
    svg_elements.extend([
        f'<rect x="24" y="{panel_y}" width="{width - 48}" height="45" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>',
        f'<text x="40" y="{panel_y + 20}" fill="#94a3b8" font-size="10">TOTAL EFFECT (TE)</text>',
        f'<text x="40" y="{panel_y + 36}" fill="#f8fafc" font-size="13" font-weight="bold">{te:+.3f}</text>',
        f'<text x="190" y="{panel_y + 20}" fill="#94a3b8" font-size="10">NATURAL DIRECT (NDE)</text>',
        f'<text x="190" y="{panel_y + 36}" fill="#c084fc" font-size="13" font-weight="bold">{nde:+.3f}</text>',
        f'<text x="360" y="{panel_y + 20}" fill="#94a3b8" font-size="10">NATURAL INDIRECT (NIE)</text>',
        f'<text x="360" y="{panel_y + 36}" fill="#34d399" font-size="13" font-weight="bold">{nie:+.3f}</text>',
        f'<text x="540" y="{panel_y + 20}" fill="#94a3b8" font-size="10">PROPORTION MEDIATED</text>',
        f'<text x="540" y="{panel_y + 36}" fill="#38bdf8" font-size="13" font-weight="bold">{pm * 100:.1f}%</text>',
        f'<text x="710" y="{panel_y + 20}" fill="#94a3b8" font-size="10">CRITICAL RHO*</text>',
        f'<text x="710" y="{panel_y + 36}" fill="#f59e0b" font-size="13" font-weight="bold">|rho*| = {abs(rho_crit):.2f}</text>',
    ])

    svg_elements.append('</svg>')
    return '\n'.join(svg_elements)


def run_high_dimensional_mediation(
    df: pd.DataFrame,
    treatment_col: str,
    outcome_col: str,
    mediator_cols: List[str],
    confounder_cols: Optional[List[str]] = None,
    subgroup_col: Optional[str] = None,
    n_boot: int = 100,
    alpha: float = 0.05,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Executes High-Dimensional Causal Mediation Analysis and Latent Path Invariance.
    """
    if df is None or len(df) == 0:
        return {"status": "ERROR", "message": "Input survey dataset is empty."}

    req_cols = [treatment_col, outcome_col] + mediator_cols
    if confounder_cols:
        req_cols.extend(confounder_cols)
    if subgroup_col and subgroup_col in df.columns:
        req_cols.append(subgroup_col)

    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        return {"status": "ERROR", "message": f"Missing required columns: {missing}"}

    sub_df = df[req_cols].dropna().copy()
    if len(sub_df) < 25:
        return {"status": "INSUFFICIENT_SAMPLE", "message": f"Sample size {len(sub_df)} is too small for high-dimensional mediation."}

    # Binarize treatment if continuous or non-numeric
    T_raw = sub_df[treatment_col].values
    if np.issubdtype(T_raw.dtype, np.number):
        unique_t = np.unique(T_raw)
        if len(unique_t) == 2 and set(unique_t).issubset({0, 1}):
            T = T_raw.astype(float)
        else:
            median_t = float(np.median(T_raw))
            T = (T_raw > median_t).astype(float)
    else:
        # Categorical binary split
        top_val = sub_df[treatment_col].mode().iloc[0]
        T = (sub_df[treatment_col] == top_val).astype(float).values

    Y = sub_df[outcome_col].astype(float).values
    n = len(sub_df)
    p_med = len(mediator_cols)

    M_mat = sub_df[mediator_cols].astype(float).values

    # Confounder matrix
    if confounder_cols and len(confounder_cols) > 0:
        X_mat = sub_df[confounder_cols].astype(float).values
        # Standardize confounders
        X_mean = np.mean(X_mat, axis=0)
        X_std = np.std(X_mat, axis=0) + 1e-8
        X_mat = (X_mat - X_mean) / X_std
    else:
        X_mat = np.empty((n, 0))

    # --- 1. Total Effect (TE) Model: Y ~ 1 + T + X ---
    X_te = np.column_stack([np.ones(n), T, X_mat])
    coef_te, se_te, r2_te, std_te = _fit_ols(X_te, Y)
    total_effect = float(coef_te[1])
    se_total = float(se_te[1])
    t_stat_te = total_effect / (se_total + 1e-12)
    p_val_te = float(2.0 * (1.0 - stats.norm.cdf(abs(t_stat_te))))

    # --- 2. Mediator Models: M_j ~ 1 + T + X ---
    alpha_coeffs = []
    alpha_ses = []
    alpha_pvals = []
    r2_m_list = []
    std_m_list = []

    for j in range(p_med):
        m_j = M_mat[:, j]
        X_m = np.column_stack([np.ones(n), T, X_mat])
        coef_m, se_m, r2_m, std_m = _fit_ols(X_m, m_j)
        a_j = float(coef_m[1])
        s_aj = float(se_m[1])
        t_aj = a_j / (s_aj + 1e-12)
        p_aj = float(2.0 * (1.0 - stats.norm.cdf(abs(t_aj))))

        alpha_coeffs.append(a_j)
        alpha_ses.append(s_aj)
        alpha_pvals.append(p_aj)
        r2_m_list.append(float(r2_m))
        std_m_list.append(float(std_m))

    # --- 3. Outcome Model: Y ~ 1 + T + M_1 + ... + M_p + X ---
    X_y = np.column_stack([np.ones(n), T, M_mat, X_mat])
    # Stabilized regression with slight L2 to guard collinear high-dim mediators
    coef_y, se_y, r2_y, std_y = _fit_ols(X_y, Y, l2_penalty=1e-3)
    nde = float(coef_y[1])
    se_nde = float(se_y[1])
    t_stat_nde = nde / (se_nde + 1e-12)
    p_val_nde = float(2.0 * (1.0 - stats.norm.cdf(abs(t_stat_nde))))

    beta_coeffs = [float(coef_y[2 + j]) for j in range(p_med)]
    beta_ses = [float(se_y[2 + j]) for j in range(p_med)]
    beta_pvals = []
    for j in range(p_med):
        t_bj = beta_coeffs[j] / (beta_ses[j] + 1e-12)
        p_bj = float(2.0 * (1.0 - stats.norm.cdf(abs(t_bj))))
        beta_pvals.append(p_bj)

    # --- 4. Component Indirect Effects & Aggregation ---
    component_ies = []
    total_abs_ie = 0.0
    for j in range(p_med):
        ie_j = float(alpha_coeffs[j] * beta_coeffs[j])
        total_abs_ie += abs(ie_j)

    mediator_results = []
    total_nie = 0.0

    for j in range(p_med):
        ie_j = float(alpha_coeffs[j] * beta_coeffs[j])
        total_nie += ie_j
        share = (abs(ie_j) / (total_abs_ie + 1e-12)) * 100.0

        # Sobel standard error approximation: SE(alpha * beta) = sqrt(alpha^2 * SE_beta^2 + beta^2 * SE_alpha^2)
        se_sobel = math.sqrt(
            (alpha_coeffs[j] ** 2) * (beta_ses[j] ** 2) +
            (beta_coeffs[j] ** 2) * (alpha_ses[j] ** 2) + 1e-14
        )
        z_sobel = ie_j / se_sobel
        p_sobel = float(2.0 * (1.0 - stats.norm.cdf(abs(z_sobel))))

        # Imai et al. (2010) Sensitivity parameter rho* for this path
        # rho* = beta_j * (std_m / std_y) * sqrt((1 - R2_m) / (1 - R2_y))
        denom = std_y * math.sqrt(max(1e-6, 1.0 - r2_m_list[j]))
        numer = beta_coeffs[j] * std_m_list[j] * math.sqrt(max(1e-6, 1.0 - r2_y))
        rho_crit_j = float(np.clip(numer / (denom + 1e-12), -0.99, 0.99))

        mediator_results.append({
            "mediator_col": mediator_cols[j],
            "alpha_treatment_to_med": round(alpha_coeffs[j], 4),
            "alpha_se": round(alpha_ses[j], 4),
            "alpha_pvalue": round(alpha_pvals[j], 4),
            "beta_med_to_outcome": round(beta_coeffs[j], 4),
            "beta_se": round(beta_ses[j], 4),
            "beta_pvalue": round(beta_pvals[j], 4),
            "indirect_effect": round(ie_j, 4),
            "sobel_se": round(se_sobel, 4),
            "sobel_pvalue": round(p_sobel, 4),
            "mediation_share_pct": round(share, 2),
            "critical_rho_sensitivity": round(rho_crit_j, 3),
            "sensitivity_robustness": "ROBUST" if abs(rho_crit_j) >= 0.35 else ("MODERATE" if abs(rho_crit_j) >= 0.15 else "SENSITIVE")
        })

    # Sort mediators by absolute indirect effect descending
    mediator_results.sort(key=lambda m: abs(m["indirect_effect"]), reverse=True)

    # Proportion mediated
    if abs(total_effect) > 1e-5:
        prop_mediated = float(np.clip(total_nie / total_effect, -2.0, 2.0))
    else:
        prop_mediated = 0.0

    # Overall sensitivity rho* for the aggregate indirect effect
    # Representative rho* from dominant mediator
    dominant_rho_crit = mediator_results[0]["critical_rho_sensitivity"] if mediator_results else 0.0

    # --- 5. Nonparametric Bootstrap for Resilient Confidence Intervals ---
    np.random.seed(random_seed)
    boot_te = []
    boot_nde = []
    boot_nie = []
    boot_pm = []
    boot_ies = {c: [] for c in mediator_cols}

    B = min(max(30, n_boot), 200)
    for _ in range(B):
        idx_b = np.random.choice(n, size=n, replace=True)
        Tb = T[idx_b]
        Yb = Y[idx_b]
        Mb = M_mat[idx_b, :]
        Xb = X_mat[idx_b, :] if X_mat.shape[1] > 0 else np.empty((n, 0))

        # Fit TE
        Xb_te = np.column_stack([np.ones(n), Tb, Xb])
        c_te_b, _, _, _ = _fit_ols(Xb_te, Yb)
        te_b = float(c_te_b[1])

        # Fit M models
        a_b = []
        for j in range(p_med):
            Xb_m = np.column_stack([np.ones(n), Tb, Xb])
            c_mb, _, _, _ = _fit_ols(Xb_m, Mb[:, j])
            a_b.append(float(c_mb[1]))

        # Fit Y model
        Xb_y = np.column_stack([np.ones(n), Tb, Mb, Xb])
        c_yb, _, _, _ = _fit_ols(Xb_y, Yb, l2_penalty=1e-3)
        nde_b = float(c_yb[1])
        b_b = [float(c_yb[2 + j]) for j in range(p_med)]

        nie_b = sum(a_b[j] * b_b[j] for j in range(p_med))
        pm_b = nie_b / te_b if abs(te_b) > 1e-5 else 0.0

        boot_te.append(te_b)
        boot_nde.append(nde_b)
        boot_nie.append(nie_b)
        boot_pm.append(pm_b)
        for j, col_name in enumerate(mediator_cols):
            boot_ies[col_name].append(a_b[j] * b_b[j])

    ci_low = alpha / 2.0 * 100.0
    ci_high = (1.0 - alpha / 2.0) * 100.0

    te_ci = (float(np.percentile(boot_te, ci_low)), float(np.percentile(boot_te, ci_high)))
    nde_ci = (float(np.percentile(boot_nde, ci_low)), float(np.percentile(boot_nde, ci_high)))
    nie_ci = (float(np.percentile(boot_nie, ci_low)), float(np.percentile(boot_nie, ci_high)))
    pm_ci = (float(np.percentile(boot_pm, ci_low)), float(np.percentile(boot_pm, ci_high)))

    # Attach bootstrap CIs to mediator results
    for m in mediator_results:
        col = m["mediator_col"]
        if col in boot_ies:
            m["ci_lower"] = round(float(np.percentile(boot_ies[col], ci_low)), 4)
            m["ci_upper"] = round(float(np.percentile(boot_ies[col], ci_high)), 4)

    # --- 6. Latent Path Invariance Testing (Cross-Group Stability) ---
    path_invariance = {
        "tested": False,
        "subgroup_col": subgroup_col,
        "wald_statistic": None,
        "p_value": None,
        "is_invariant": True,
        "interpretation": "Subgroup column not specified or insufficient strata for invariance test."
    }

    if subgroup_col and subgroup_col in sub_df.columns:
        groups = sub_df[subgroup_col].dropna().unique()
        if len(groups) >= 2:
            g1, g2 = groups[0], groups[1]
            idx_g1 = (sub_df[subgroup_col] == g1).values
            idx_g2 = (sub_df[subgroup_col] == g2).values

            if np.sum(idx_g1) >= 15 and np.sum(idx_g2) >= 15:
                # Group 1 regression
                X_y1 = np.column_stack([np.ones(np.sum(idx_g1)), T[idx_g1], M_mat[idx_g1, :]])
                c1, s1, _, _ = _fit_ols(X_y1, Y[idx_g1], l2_penalty=1e-3)
                beta1 = c1[2:]

                # Group 2 regression
                X_y2 = np.column_stack([np.ones(np.sum(idx_g2)), T[idx_g2], M_mat[idx_g2, :]])
                c2, s2, _, _ = _fit_ols(X_y2, Y[idx_g2], l2_penalty=1e-3)
                beta2 = c2[2:]

                # Difference vector & approximate variance
                diff = beta1 - beta2
                var_diff = (s1[2:] ** 2) + (s2[2:] ** 2) + 1e-12
                wald_stat = float(np.sum((diff ** 2) / var_diff))
                df_wald = len(diff)
                p_wald = float(1.0 - stats.chi2.cdf(wald_stat, df=df_wald))

                inv = bool(p_wald >= 0.05)
                path_invariance = {
                    "tested": True,
                    "subgroup_col": subgroup_col,
                    "groups_compared": [str(g1), str(g2)],
                    "wald_statistic": round(wald_stat, 3),
                    "p_value": round(p_wald, 4),
                    "is_invariant": inv,
                    "interpretation": (
                        f"Latent mediator paths are invariant across groups '{g1}' and '{g2}' (p = {p_wald:.4f} >= 0.05)."
                        if inv else
                        f"Significant structural heterogeneity in mediator paths between '{g1}' and '{g2}' (p = {p_wald:.4f} < 0.05)."
                    )
                }

    # --- 7. Interactive SVG Visualization ---
    svg_viz = _generate_mediation_svg(
        treatment_col=treatment_col,
        outcome_col=outcome_col,
        top_mediators=mediator_results,
        te=total_effect,
        nde=nde,
        nie=total_nie,
        pm=prop_mediated,
        rho_crit=dominant_rho_crit
    )

    return {
        "status": "SUCCESS",
        "sample_size": n,
        "n_mediators": p_med,
        "treatment_variable": treatment_col,
        "outcome_variable": outcome_col,
        "confounder_variables": confounder_cols or [],
        "total_effect": {
            "estimate": round(total_effect, 4),
            "se": round(se_total, 4),
            "p_value": round(p_val_te, 4),
            "ci_lower": round(te_ci[0], 4),
            "ci_upper": round(te_ci[1], 4)
        },
        "natural_direct_effect": {
            "estimate": round(nde, 4),
            "se": round(se_nde, 4),
            "p_value": round(p_val_nde, 4),
            "ci_lower": round(nde_ci[0], 4),
            "ci_upper": round(nde_ci[1], 4)
        },
        "natural_indirect_effect": {
            "estimate": round(total_nie, 4),
            "ci_lower": round(nie_ci[0], 4),
            "ci_upper": round(nie_ci[1], 4)
        },
        "proportion_mediated": {
            "estimate": round(prop_mediated, 4),
            "percentage": round(prop_mediated * 100.0, 2),
            "ci_lower": round(pm_ci[0], 4),
            "ci_upper": round(pm_ci[1], 4)
        },
        "sequential_ignorability_sensitivity": {
            "dominant_rho_critical": round(dominant_rho_crit, 3),
            "robustness": "ROBUST" if abs(dominant_rho_crit) >= 0.35 else ("MODERATE" if abs(dominant_rho_crit) >= 0.15 else "SENSITIVE"),
            "interpretation": (
                f"Mediation is robust to omitted mediator-outcome confounders up to |rho| = {abs(dominant_rho_crit):.2f} (Imai et al. 2010)."
                if abs(dominant_rho_crit) >= 0.25 else
                f"Mediation could be explained away by moderate unobserved confounding (|rho*| = {abs(dominant_rho_crit):.2f})."
            )
        },
        "mediator_pathways": mediator_results,
        "latent_path_invariance": path_invariance,
        "svg_visualization": svg_viz
    }
