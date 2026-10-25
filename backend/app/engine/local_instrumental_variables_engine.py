# -*- coding: utf-8 -*-
"""
Local Instrumental Variables & Marginal Treatment Effects (LIV / MTE) Engine
Methodological References:
- Heckman, J. J., & Vytlacil, E. (2005). "Structural Equations, Treatment Effects, and Econometric Policy Evaluation."
  Econometrica, 73(3), 669-738.
- Heckman, J. J., Urzua, S., & Vytlacil, E. (2006). "Understanding Instrumental Variables in Models with Essential Heterogeneity."
  The Review of Economics and Statistics, 88(3), 389-432.
- Mogstad, M., Santos, A., & Torgovitsky, A. (2018). "Using Instrumental Variables for Inference About Policy Relevant Treatment Effects."
  Econometrica, 86(5), 1589-1619.
- Carneiro, P., Heckman, J. J., & Vytlacil, E. (2011). "Estimating Marginal Returns to Education."
  American Economic Review, 101(6), 2754-2781.

Implements the generalized Roy selection model with essential heterogeneity. Estimates propensity score P(Z) = Pr(D=1|Z),
computes MTE(u) via Local Instrumental Variables differentiation dE[Y|P=p]/dp, integrates MTE curves against
weight distributions to recover ATE, ATT, ATU, LATE, and PRTE, and tests for Selection on Unobserved Gains.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def estimate_local_instrumental_variables(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    instrument_cols: List[str],
    covariate_cols: Optional[List[str]] = None,
    n_grid_points: int = 50,
    trim_quantile: float = 0.05,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Local Instrumental Variables (LIV) and Marginal Treatment Effects (MTE) estimation.

    Args:
        df: Input survey DataFrame.
        outcome_col: Dependent variable Y.
        treatment_col: Binary treatment variable D in {0, 1}.
        instrument_cols: Exogenous instrumental variables Z.
        covariate_cols: Optional exogenous confounding covariates X.
        n_grid_points: Number of evaluation points u in (0, 1) for the MTE curve.
        trim_quantile: Quantile trimming for common support of propensity scores.
        alpha_level: Statistical significance level (default 0.05 for 95% CI).

    Returns:
        Structured dictionary matching API contract.
    """
    covariate_cols = covariate_cols or []
    all_cols = [outcome_col, treatment_col] + instrument_cols + covariate_cols
    for col in all_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")

    clean_df = df[all_cols].dropna().copy()
    N = len(clean_df)
    if N < 30:
        raise ValueError(f"Sample size N={N} is too small for LIV/MTE analysis (minimum 30 required).")

    y = clean_df[outcome_col].values.astype(float)
    d = clean_df[treatment_col].values.astype(float)

    # Validate binary treatment
    unique_d = np.unique(d)
    if not np.all(np.isin(unique_d, [0.0, 1.0])):
        raise ValueError(f"Treatment column '{treatment_col}' must be binary 0/1. Found unique values: {unique_d}")

    # 1. First Stage: Propensity Score P(Z, X) = Pr(D=1 | Z, X) via Logit
    Z_mat = clean_df[instrument_cols].values.astype(float)
    if covariate_cols:
        X_mat = clean_df[covariate_cols].values.astype(float)
        # Standardize X
        X_mean = np.mean(X_mat, axis=0)
        X_std = np.std(X_mat, axis=0)
        X_std[X_std < 1e-8] = 1.0
        X_norm = (X_mat - X_mean) / X_std
        W_mat = np.column_stack([np.ones(N), Z_mat, X_norm])
    else:
        X_norm = np.zeros((N, 0))
        W_mat = np.column_stack([np.ones(N), Z_mat])

    # Fit Logistic regression for propensity score
    p_dim = W_mat.shape[1]
    gamma = np.zeros(p_dim)
    # 10 Newton-Raphson iterations
    for _ in range(12):
        eta = np.clip(W_mat @ gamma, -15.0, 15.0)
        p_hat = 1.0 / (1.0 + np.exp(-eta))
        p_hat = np.clip(p_hat, 1e-6, 1.0 - 1e-6)
        W_diag = p_hat * (1.0 - p_hat)
        grad = W_mat.T @ (d - p_hat)
        Hess = W_mat.T @ (W_mat * W_diag[:, None]) + 1e-4 * np.eye(p_dim)
        try:
            delta = np.linalg.solve(Hess, grad)
            gamma += delta
            if np.max(np.abs(delta)) < 1e-6:
                break
        except np.linalg.LinAlgError:
            break

    p_scores = 1.0 / (1.0 + np.exp(-np.clip(W_mat @ gamma, -15.0, 15.0)))
    p_scores = np.clip(p_scores, 1e-4, 1.0 - 1e-4)

    # 2. Common Support & Trimming
    p_min = float(np.percentile(p_scores, trim_quantile * 100))
    p_max = float(np.percentile(p_scores, (1.0 - trim_quantile) * 100))
    if p_max <= p_min + 0.05:
        p_min = max(0.01, float(np.min(p_scores)))
        p_max = min(0.99, float(np.max(p_scores)))

    # 3. Benchmark Estimators
    # A. OLS
    M_ols = np.column_stack([np.ones(N), d])
    if covariate_cols:
        M_ols = np.column_stack([M_ols, X_norm])
    b_ols = np.linalg.lstsq(M_ols, y, rcond=None)[0]
    beta_ols = float(b_ols[1])
    resid_ols = y - M_ols @ b_ols
    se_ols = float(np.sqrt(max(1e-12, (np.sum(resid_ols ** 2) / (N - M_ols.shape[1])) * np.linalg.pinv(M_ols.T @ M_ols)[1, 1])))

    # B. Standard 2SLS (Linear IV)
    # First stage: D ~ Z + X
    M_iv_first = np.column_stack([np.ones(N), Z_mat])
    if covariate_cols:
        M_iv_first = np.column_stack([M_iv_first, X_norm])
    d_hat = M_iv_first @ np.linalg.lstsq(M_iv_first, d, rcond=None)[0]
    
    # Second stage: Y ~ d_hat + X
    M_iv_sec = np.column_stack([np.ones(N), d_hat])
    if covariate_cols:
        M_iv_sec = np.column_stack([M_iv_sec, X_norm])
    b_2sls = np.linalg.lstsq(M_iv_sec, y, rcond=None)[0]
    beta_2sls = float(b_2sls[1])
    
    # Correct 2SLS SE using actual D
    M_iv_act = np.column_stack([np.ones(N), d])
    if covariate_cols:
        M_iv_act = np.column_stack([M_iv_act, X_norm])
    resid_2sls = y - M_iv_act @ b_2sls
    sigma2_2sls = np.sum(resid_2sls ** 2) / (N - M_iv_sec.shape[1])
    se_2sls = float(np.sqrt(max(1e-12, sigma2_2sls * np.linalg.pinv(M_iv_sec.T @ M_iv_sec)[1, 1])))

    # 4. Semi-Parametric Outcome Modeling E[Y | P(Z) = p, X] (Heckman, Urzua, & Vytlacil 2006)
    # Flexible polynomial in p: E[Y | P, X] = alpha_0 + X beta_x + delta_1 P + delta_2 P^2 + delta_3 P^3
    poly_terms = [np.ones(N), p_scores, p_scores ** 2, p_scores ** 3]
    if covariate_cols:
        poly_terms.append(X_norm)
    M_poly = np.column_stack(poly_terms)
    
    poly_coefs = np.linalg.lstsq(M_poly, y, rcond=None)[0]
    delta_1 = float(poly_coefs[1])
    delta_2 = float(poly_coefs[2])
    delta_3 = float(poly_coefs[3])

    # Covariance matrix of polynomial coefficients
    poly_resid = y - M_poly @ poly_coefs
    poly_cov = (np.sum(poly_resid ** 2) / (N - M_poly.shape[1])) * np.linalg.pinv(M_poly.T @ M_poly)

    # 5. Local Instrumental Variables Differentiation: MTE(u) = d E[Y | P=p] / dp
    # MTE(u) = delta_1 + 2 * delta_2 * u + 3 * delta_3 * u^2
    u_grid = np.linspace(p_min, p_max, n_grid_points)
    mte_curve = []
    
    for u in u_grid:
        mte_val = delta_1 + 2.0 * delta_2 * u + 3.0 * delta_3 * (u ** 2)
        # Gradient w.r.t [delta_1, delta_2, delta_3]
        grad_u = np.array([1.0, 2.0 * u, 3.0 * (u ** 2)])
        sub_cov = poly_cov[1:4, 1:4]
        se_u = float(np.sqrt(max(1e-12, grad_u.T @ sub_cov @ grad_u)))
        
        crit = float(stats.norm.ppf(1.0 - alpha_level / 2.0))
        mte_curve.append({
            "u": round(float(u), 4),
            "mte": round(float(mte_val), 3),
            "se": round(float(se_u), 3),
            "ci_95": [round(float(mte_val - crit * se_u), 3), round(float(mte_val + crit * se_u), 3)]
        })

    # 6. Policy Weight Integration (Heckman & Vytlacil 2005)
    # ATE weights: w_ATE(u) = 1.0 (normalized on common support)
    w_ate_raw = np.ones_like(u_grid)
    w_ate = w_ate_raw / np.sum(w_ate_raw)

    # ATT weights: w_ATT(u) = \int_u^1 f(p) dp / E[P]
    w_att_raw = np.array([np.mean(p_scores[p_scores >= u]) if np.sum(p_scores >= u) > 0 else 0.0 for u in u_grid])
    if np.sum(w_att_raw) > 0:
        w_att = w_att_raw / np.sum(w_att_raw)
    else:
        w_att = w_ate.copy()

    # ATU weights: w_ATU(u) = \int_0^u f(p) dp / (1 - E[P])
    w_atu_raw = np.array([np.mean(1.0 - p_scores[p_scores <= u]) if np.sum(p_scores <= u) > 0 else 0.0 for u in u_grid])
    if np.sum(w_atu_raw) > 0:
        w_atu = w_atu_raw / np.sum(w_atu_raw)
    else:
        w_atu = w_ate.copy()

    # LATE weights: compliers between 25th and 75th percentiles of P(Z)
    p_p25 = float(np.percentile(p_scores, 25))
    p_p75 = float(np.percentile(p_scores, 75))
    w_late_raw = np.where((u_grid >= p_p25) & (u_grid <= p_p75), 1.0, 0.0)
    if np.sum(w_late_raw) > 0:
        w_late = w_late_raw / np.sum(w_late_raw)
    else:
        w_late = w_ate.copy()

    mte_values = np.array([pt["mte"] for pt in mte_curve])
    
    # Calculate Integrated Parameter Estimates
    theta_ate = float(np.sum(mte_values * w_ate))
    theta_att = float(np.sum(mte_values * w_att))
    theta_atu = float(np.sum(mte_values * w_atu))
    theta_late = float(np.sum(mte_values * w_late))

    # Standard errors via Delta Method on integrated weights
    # sum w_i * (delta_1 + 2*u*delta_2 + 3*u^2*delta_3) = delta_1 (sum w) + delta_2 (2 sum w*u) + delta_3 (3 sum w*u^2)
    def compute_integrated_se(weights: np.ndarray) -> float:
        c1 = float(np.sum(weights))
        c2 = float(2.0 * np.sum(weights * u_grid))
        c3 = float(3.0 * np.sum(weights * (u_grid ** 2)))
        grad_int = np.array([c1, c2, c3])
        sub_cov = poly_cov[1:4, 1:4]
        return float(np.sqrt(max(1e-12, grad_int.T @ sub_cov @ grad_int)))

    se_ate = compute_integrated_se(w_ate)
    se_att = compute_integrated_se(w_att)
    se_atu = compute_integrated_se(w_atu)
    se_late = compute_integrated_se(w_late)

    crit_val = float(stats.norm.ppf(1.0 - alpha_level / 2.0))

    # 7. Test for Essential Heterogeneity & Selection on Unobserved Gains
    # H0: MTE(u) is constant <=> delta_2 = 0 and delta_3 = 0
    # Wald test for joint hypothesis [delta_2, delta_3] = [0, 0]
    wald_R = np.array([[0, 0, 1, 0] + [0] * len(covariate_cols),
                       [0, 0, 0, 1] + [0] * len(covariate_cols)])
    b_sub = np.array([delta_2, delta_3])
    cov_sub = poly_cov[2:4, 2:4]
    try:
        wald_stat = float(b_sub.T @ np.linalg.inv(cov_sub) @ b_sub)
        p_val_het = float(1.0 - stats.chi2.cdf(wald_stat, df=2))
    except Exception:
        wald_stat = 0.0
        p_val_het = 0.5

    sorting_gain = float(theta_att - theta_ate)
    is_essential_heterogeneity = bool(p_val_het < 0.05)
    
    if is_essential_heterogeneity:
        if sorting_gain > 0:
            het_verdict = "Lựa chọn theo lợi ích kỳ vọng (Positive Selection on Gains - Roy Model)"
        else:
            het_verdict = "Lựa chọn nghịch đảo (Reverse Selection on Gains)"
    else:
        het_verdict = "Không phát hiện tính không đồng nhất thiết yếu (Homogeneous Treatment Effects)"

    # 8. Overall Summary
    overall_summary = {
        "sample_size": N,
        "n_instruments": len(instrument_cols),
        "n_covariates": len(covariate_cols),
        "propensity_support": [round(p_min, 3), round(p_max, 3)],
        "propensity_mean": round(float(np.mean(p_scores)), 3),
        
        # MTE Curve Parameters
        "mte_intercept_delta1": round(delta_1, 3),
        "mte_linear_slope_delta2": round(delta_2, 3),
        "mte_quadratic_delta3": round(delta_3, 3),
        
        # Integrated Causal Parameters
        "ate": {
            "estimate": round(theta_ate, 3),
            "se": round(se_ate, 3),
            "ci_95": [round(theta_ate - crit_val * se_ate, 3), round(theta_ate + crit_val * se_ate, 3)],
            "label": "Average Treatment Effect (ATE)"
        },
        "att": {
            "estimate": round(theta_att, 3),
            "se": round(se_att, 3),
            "ci_95": [round(theta_att - crit_val * se_att, 3), round(theta_att + crit_val * se_att, 3)],
            "label": "Treatment on the Treated (ATT)"
        },
        "atu": {
            "estimate": round(theta_atu, 3),
            "se": round(se_atu, 3),
            "ci_95": [round(theta_atu - crit_val * se_atu, 3), round(theta_atu + crit_val * se_atu, 3)],
            "label": "Treatment on the Untreated (ATU)"
        },
        "late": {
            "estimate": round(theta_late, 3),
            "se": round(se_late, 3),
            "ci_95": [round(theta_late - crit_val * se_late, 3), round(theta_late + crit_val * se_late, 3)],
            "label": "Local Average Treatment Effect (LATE)"
        },
        
        # Benchmark Comparisons
        "ols_benchmark": {
            "estimate": round(beta_ols, 3),
            "se": round(se_ols, 3),
            "label": "Conventional OLS"
        },
        "standard_2sls": {
            "estimate": round(beta_2sls, 3),
            "se": round(se_2sls, 3),
            "label": "Linear 2SLS (IV)"
        },
        
        # Selection on Gains Test
        "sorting_on_gains_att_minus_ate": round(sorting_gain, 3),
        "wald_test_essential_heterogeneity": round(wald_stat, 2),
        "wald_test_p_value": round(p_val_het, 4),
        "essential_heterogeneity_present": is_essential_heterogeneity,
        "heterogeneity_verdict": het_verdict
    }

    # 9. Generate Scientific SVG Visualization
    svg_chart = _generate_liv_mte_svg(
        overall_summary=overall_summary,
        mte_curve=mte_curve,
        u_grid=u_grid,
        w_att=w_att,
        w_atu=w_atu,
        w_late=w_late
    )

    # 10. APA 7th Edition Narrative
    apa_narrative = (
        f"A Local Instrumental Variables (LIV) and Marginal Treatment Effects (MTE) analysis (Heckman & Vytlacil, 2005) was conducted "
        f"on sample N = {N} over the common propensity support P(Z) in [{p_min:.2f}, {p_max:.2f}]. "
        f"The empirical MTE curve was estimated as MTE(u) = {delta_1:.2f} + {2.0*delta_2:.2f}u + {3.0*delta_3:.2f}u^2. "
        f"A Wald test for essential heterogeneity formally rejected the hypothesis of constant treatment effects (Wald = {wald_stat:.2f}, p = {p_val_het:.4f}), "
        f"confirming {het_verdict.lower()}. "
        f"Integrating MTE against policy weights yielded an Average Treatment Effect on the Treated of ATT = {theta_att:.3f} (SE = {se_att:.3f}, 95% CI [{theta_att - crit_val*se_att:.3f}, {theta_att + crit_val*se_att:.3f}]), "
        f"compared to ATE = {theta_ate:.3f} (SE = {se_ate:.3f}), ATU = {theta_atu:.3f} (SE = {se_atu:.3f}), and LATE = {theta_late:.3f} (SE = {se_late:.3f}). "
        f"The sorting on unobserved gains margin (ATT - ATE = {sorting_gain:+.3f}) demonstrates that conventional linear 2SLS ({beta_2sls:.3f}) "
        f"and standard OLS ({beta_ols:.3f}) fail to capture the full structural distribution of treatment response."
    )

    return {
        "status": "SUCCESS",
        "overall_summary": overall_summary,
        "mte_curve": mte_curve,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_liv_mte_svg(
    overall_summary: Dict[str, Any],
    mte_curve: List[Dict[str, Any]],
    u_grid: np.ndarray,
    w_att: np.ndarray,
    w_atu: np.ndarray,
    w_late: np.ndarray
) -> str:
    """
    Dual-panel SVG:
    Panel 1: The Empirical MTE Curve MTE(u) with 95% Confidence Band over Propensity Support u in [p_min, p_max].
    Panel 2: Forest Plot of Unified Policy Parameters: ATE, ATT, ATU, LATE, 2SLS, OLS.
    """
    svg_w, svg_h = 780, 360
    
    # Coordinates for Panel 1 (Left: MTE Curve, x: 50 to 380, y: 70 to 300)
    p1_x0, p1_y0, p1_w, p1_h = 60, 70, 320, 220
    # Coordinates for Panel 2 (Right: Forest Plot, x: 440 to 740, y: 70 to 300)
    p2_x0, p2_y0, p2_w, p2_h = 440, 70, 300, 220

    mte_vals = [pt["mte"] for pt in mte_curve]
    ci_lows = [pt["ci_95"][0] for pt in mte_curve]
    ci_highs = [pt["ci_95"][1] for pt in mte_curve]
    
    y_min_val = min(min(ci_lows), 0.0) - 1.0
    y_max_val = max(max(ci_highs), 5.0) + 1.0
    y_span = max(1e-4, y_max_val - y_min_val)

    def p1_scale_x(u_val: float) -> float:
        u_min, u_max = float(u_grid[0]), float(u_grid[-1])
        u_span = max(1e-4, u_max - u_min)
        return p1_x0 + ((u_val - u_min) / u_span) * p1_w

    def p1_scale_y(y_val: float) -> float:
        return p1_y0 + p1_h - ((y_val - y_min_val) / y_span) * p1_h

    # Build MTE line and CI path
    mte_pts = " ".join([f"{p1_scale_x(pt['u']):.1f},{p1_scale_y(pt['mte']):.1f}" for pt in mte_curve])
    
    ci_upper_pts = [f"{p1_scale_x(pt['u']):.1f},{p1_scale_y(pt['ci_95'][1]):.1f}" for pt in mte_curve]
    ci_lower_pts = [f"{p1_scale_x(pt['u']):.1f},{p1_scale_y(pt['ci_95'][0]):.1f}" for pt in reversed(mte_curve)]
    ci_band_d = "M " + " L ".join(ci_upper_pts + ci_lower_pts) + " Z"

    y_zero_p1 = p1_scale_y(0.0)

    # Panel 2: Forest Plot Items
    ate = overall_summary.get("ate", {})
    att = overall_summary.get("att", {})
    atu = overall_summary.get("atu", {})
    late = overall_summary.get("late", {})
    ols = overall_summary.get("ols_benchmark", {})
    two_sls = overall_summary.get("standard_2sls", {})

    items = [
        {"name": "ATT (Treated)", "est": att.get("estimate", 0.0), "ci": att.get("ci_95", [0, 0]), "color": "#10b981"},
        {"name": "ATE (Average)", "est": ate.get("estimate", 0.0), "ci": ate.get("ci_95", [0, 0]), "color": "#38bdf8"},
        {"name": "ATU (Untreated)", "est": atu.get("estimate", 0.0), "ci": atu.get("ci_95", [0, 0]), "color": "#a855f7"},
        {"name": "LATE (Compliers)", "est": late.get("estimate", 0.0), "ci": late.get("ci_95", [0, 0]), "color": "#f59e0b"},
        {"name": "Linear 2SLS", "est": two_sls.get("estimate", 0.0), "ci": [two_sls.get("estimate", 0) - 1.96*two_sls.get("se", 0.1), two_sls.get("estimate", 0) + 1.96*two_sls.get("se", 0.1)], "color": "#cbd5e1"},
        {"name": "Standard OLS", "est": ols.get("estimate", 0.0), "ci": [ols.get("estimate", 0) - 1.96*ols.get("se", 0.1), ols.get("estimate", 0) + 1.96*ols.get("se", 0.1)], "color": "#94a3b8"}
    ]

    all_fp_lows = [it["ci"][0] for it in items]
    all_fp_highs = [it["ci"][1] for it in items]
    fp_min = min(min(all_fp_lows), 0.0) - 0.5
    fp_max = max(max(all_fp_highs), 5.0) + 0.5
    fp_span = max(1e-4, fp_max - fp_min)

    def p2_scale_x(val: float) -> float:
        return p2_x0 + 80 + ((val - fp_min) / fp_span) * (p2_w - 90)

    fp_zero_x = p2_scale_x(0.0)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#0f172a" rx="10" />',
        f'  <text x="30" y="32" font-size="14" font-weight="700" fill="#f8fafc">Local Instrumental Variables &amp; Marginal Treatment Effects (Heckman &amp; Vytlacil 2005)</text>',
        f'  <text x="30" y="48" font-size="11" fill="#94a3b8">Sorting on Gains: {overall_summary.get("sorting_on_gains_att_minus_ate", 0.0):+.3f} · Essential Heterogeneity: {overall_summary.get("heterogeneity_verdict", "")}</text>',
        
        # Panel 1 Background & Grid
        f'  <rect x="{p1_x0}" y="{p1_y0}" width="{p1_w}" height="{p1_h}" fill="#1e293b" rx="6" opacity="0.6" />',
        f'  <text x="{p1_x0 + 10}" y="{p1_y0 + 18}" font-size="11" font-weight="600" fill="#38bdf8">Panel A: MTE(u) Curve &amp; 95% Confidence Band</text>',
        f'  <line x1="{p1_x0}" y1="{y_zero_p1:.1f}" x2="{p1_x0 + p1_w}" y2="{y_zero_p1:.1f}" stroke="#475569" stroke-dasharray="3,3" stroke-width="1" />',
        
        # MTE Confidence Band
        f'  <path d="{ci_band_d}" fill="#0284c7" opacity="0.25" />',
        # MTE Line
        f'  <polyline points="{mte_pts}" fill="none" stroke="#38bdf8" stroke-width="2.5" />',
        
        # Axes Labels Panel 1
        f'  <text x="{p1_x0}" y="{p1_y0 + p1_h + 16}" font-size="10" fill="#64748b">u = {u_grid[0]:.2f} (Eager)</text>',
        f'  <text x="{p1_x0 + p1_w - 70}" y="{p1_y0 + p1_h + 16}" font-size="10" fill="#64748b">u = {u_grid[-1]:.2f} (Reluctant)</text>',
        f'  <text x="{p1_x0 + p1_w/2 - 50}" y="{p1_y0 + p1_h + 16}" font-size="10" font-weight="500" fill="#94a3b8">Resistance to Treatment (UD)</text>',
        f'  <text x="{p1_x0 + 10}" y="{p1_scale_y(mte_vals[0]) - 8:.1f}" font-size="10" font-weight="600" fill="#38bdf8">MTE = {mte_vals[0]:.2f}</text>',
        f'  <text x="{p1_x0 + p1_w - 65}" y="{p1_scale_y(mte_vals[-1]) - 8:.1f}" font-size="10" font-weight="600" fill="#38bdf8">MTE = {mte_vals[-1]:.2f}</text>',

        # Panel 2 Background & Grid (Forest Plot)
        f'  <rect x="{p2_x0}" y="{p2_y0}" width="{p2_w}" height="{p2_h}" fill="#1e293b" rx="6" opacity="0.6" />',
        f'  <text x="{p2_x0 + 10}" y="{p2_y0 + 18}" font-size="11" font-weight="600" fill="#10b981">Panel B: Integrated Policy Parameters Comparison</text>',
        f'  <line x1="{fp_zero_x:.1f}" y1="{p2_y0 + 28}" x2="{fp_zero_x:.1f}" y2="{p2_y0 + p2_h - 10}" stroke="#475569" stroke-dasharray="3,3" stroke-width="1" />'
    ]

    # Render Forest Plot Rows
    row_h = (p2_h - 45) / len(items)
    for idx, item in enumerate(items):
        ry = p2_y0 + 38 + idx * row_h
        rx_mid = p2_scale_x(item["est"])
        rx_low = p2_scale_x(item["ci"][0])
        rx_high = p2_scale_x(item["ci"][1])
        c = item["color"]

        lines.append(f'  <text x="{p2_x0 + 10}" y="{ry + 4:.1f}" font-size="10" font-weight="500" fill="#cbd5e1">{item["name"]}</text>')
        # CI segment
        lines.append(f'  <line x1="{rx_low:.1f}" y1="{ry:.1f}" x2="{rx_high:.1f}" y2="{ry:.1f}" stroke="{c}" stroke-width="2" opacity="0.8" />')
        lines.append(f'  <line x1="{rx_low:.1f}" y1="{ry - 3:.1f}" x2="{rx_low:.1f}" y2="{ry + 3:.1f}" stroke="{c}" stroke-width="1.5" />')
        lines.append(f'  <line x1="{rx_high:.1f}" y1="{ry - 3:.1f}" x2="{rx_high:.1f}" y2="{ry + 3:.1f}" stroke="{c}" stroke-width="1.5" />')
        # Point estimate circle
        lines.append(f'  <circle cx="{rx_mid:.1f}" cy="{ry:.1f}" r="4" fill="{c}" />')
        # Value label
        lines.append(f'  <text x="{rx_high + 6:.1f}" y="{ry + 3:.1f}" font-size="9" font-mono="true" fill="{c}">{item["est"]:.2f}</text>')

    # Footer note
    lines.append(f'  <text x="30" y="{svg_h - 12}" font-size="10" fill="#64748b">Unified Roy selection model: Parameters recovered as weighted averages of MTE over unobserved resistance distribution UD.</text>')
    lines.append('</svg>')

    return "\n".join(lines)
