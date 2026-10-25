# -*- coding: utf-8 -*-
"""
Instrumental Variable Local Average Response Function (LARF) Engine
Scientific Reference:
- Abadie, A. (2003). "Semiparametric Instrumental Variable Estimation of Treatment Response Models."
  Econometrica, 71(1), 231-263.
- Frölich, M. (2007). "Nonparametric IV estimation of local average treatment effects with covariates."
  Journal of Econometrics, 139(1), 35-75.
- Imbens, G. W., & Angrist, J. D. (1994). "Identification and Estimation of Local Average Treatment Effects."
  Econometrica, 62(2), 467-475.

This engine identifies causal effects for non-linear and bounded survey response outcomes
under endogenous binary treatment with instrumental variables via Abadie's kappa weighting.
"""

from typing import List, Dict, Any, Optional
import math
import numpy as np
import pandas as pd
from scipy import stats


def _fit_logistic_propensity(X: np.ndarray, z: np.ndarray, max_iter: int = 50, l2_reg: float = 1e-4) -> np.ndarray:
    """
    Fits logistic regression for instrument propensity score P(Z=1|X) using Newton-Raphson.
    Returns predicted probabilities clipped to [0.01, 0.99].
    """
    n, k = X.shape
    beta = np.zeros(k)
    for _ in range(max_iter):
        eta = np.clip(X @ beta, -30.0, 30.0)
        p = 1.0 / (1.0 + np.exp(-eta))
        p_safe = np.clip(p, 1e-6, 1.0 - 1e-6)
        w = p_safe * (1.0 - p_safe)
        
        grad = X.T @ (p - z) + l2_reg * beta
        hess = X.T @ (w[:, None] * X) + l2_reg * np.eye(k)
        
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hess, grad, rcond=None)[0]
            
        beta -= step
        if np.max(np.abs(step)) < 1e-6:
            break
            
    eta_final = np.clip(X @ beta, -30.0, 30.0)
    p_final = 1.0 / (1.0 + np.exp(-eta_final))
    return np.clip(p_final, 0.01, 0.99)


def _fit_weighted_logit(X: np.ndarray, y: np.ndarray, weights: np.ndarray, max_iter: int = 60, l2_reg: float = 1e-4) -> np.ndarray:
    """
    Fits weighted logistic regression minimizing Abadie weighted cross-entropy.
    """
    n, k = X.shape
    beta = np.zeros(k)
    w_pos = np.clip(weights, 1e-8, None)
    
    for _ in range(max_iter):
        eta = np.clip(X @ beta, -30.0, 30.0)
        p = 1.0 / (1.0 + np.exp(-eta))
        p_safe = np.clip(p, 1e-6, 1.0 - 1e-6)
        
        # Weighted gradient and Hessian
        weights_grad = w_pos * (p - y)
        grad = X.T @ weights_grad + l2_reg * beta
        
        weights_hess = w_pos * (p_safe * (1.0 - p_safe))
        hess = X.T @ (weights_hess[:, None] * X) + l2_reg * np.eye(k)
        
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hess, grad, rcond=None)[0]
            
        beta -= step
        if np.max(np.abs(step)) < 1e-6:
            break
            
    return beta


def _fit_weighted_ols(X: np.ndarray, y: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    Fits weighted least squares with weights.
    """
    w_sqrt = np.sqrt(np.clip(weights, 1e-8, None))[:, None]
    X_w = X * w_sqrt
    y_w = y * w_sqrt.ravel()
    try:
        beta = np.linalg.lstsq(X_w, y_w, rcond=None)[0]
    except Exception:
        beta = np.zeros(X.shape[1])
    return beta


def estimate_larf(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    instrument_col: str,
    covariate_cols: Optional[List[str]] = None,
    model_type: str = "logit",
    alpha_level: float = 0.05,
    n_bootstraps: int = 300,
    trim_negative: bool = False
) -> Dict[str, Any]:
    """
    Estimates the Instrumental Variable Local Average Response Function (LARF)
    according to Abadie (2003 Econometrica).
    """
    if covariate_cols is None:
        covariate_cols = []

    required_cols = [outcome_col, treatment_col, instrument_col] + covariate_cols
    for col in required_cols:
        if col not in df.columns:
            return {"status": "ERROR", "message": f"Column '{col}' not found in dataframe."}

    sub_df = df[required_cols].dropna().copy()
    n = len(sub_df)
    if n < 30:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": f"Sample size (N={n}) is insufficient for semi-parametric LARF estimation (minimum 30 required)."
        }

    y_raw = sub_df[outcome_col].astype(float).values
    d_raw = sub_df[treatment_col].astype(float).values
    z_raw = sub_df[instrument_col].astype(float).values

    # Binarize treatment and instrument if strictly binary or 0/1
    d = (d_raw > np.median(d_raw)).astype(float) if len(np.unique(d_raw)) > 2 else d_raw
    z = (z_raw > np.median(z_raw)).astype(float) if len(np.unique(z_raw)) > 2 else z_raw

    # Build covariate matrix with intercept
    if covariate_cols:
        X_cov = sub_df[covariate_cols].astype(float).values
        # Standardize covariates for stable logistic propensity fitting
        cov_mean = np.mean(X_cov, axis=0)
        cov_std = np.std(X_cov, axis=0)
        cov_std[cov_std == 0] = 1.0
        X_cov_norm = (X_cov - cov_mean) / cov_std
        X_prop = np.column_stack([np.ones(n), X_cov_norm])
    else:
        X_prop = np.ones((n, 1))

    # Step 1: Instrument Propensity Score e(X) = P(Z=1|X)
    e_hat = _fit_logistic_propensity(X_prop, z)

    # Step 2: Abadie Weight Kappa
    # kappa = 1 - (D*(1-Z))/(1-e) - ((1-D)*Z)/e
    term1 = (d * (1.0 - z)) / (1.0 - e_hat)
    term2 = ((1.0 - d) * z) / e_hat
    kappa = 1.0 - term1 - term2

    # Weight diagnostics
    pct_negative = float(np.mean(kappa < 0.0) * 100.0)
    p_complier = float(np.mean(kappa))
    if trim_negative:
        kappa_eff = np.maximum(0.0, kappa)
    else:
        kappa_eff = kappa

    # Check weak instrument or invalid compliance
    if p_complier <= 0.005:
        p_complier_safe = 0.01
    else:
        p_complier_safe = p_complier

    # Step 3: Model design matrices for outcome regression
    # Model includes [Intercept, D, X]
    X_model = np.column_stack([np.ones(n), d, X_prop[:, 1:]]) if X_prop.shape[1] > 1 else np.column_stack([np.ones(n), d])
    k_vars = X_model.shape[1]

    # Predict counterfactuals on compliers
    X_d1 = X_model.copy()
    X_d1[:, 1] = 1.0
    X_d0 = X_model.copy()
    X_d0[:, 1] = 0.0

    # 3A. Fit Point Estimates
    is_logit = (model_type.lower() == "logit")
    if is_logit:
        # Normalize y into [0, 1] if not strictly bounded
        y_scaled = (y_raw - np.min(y_raw)) / (np.max(y_raw) - np.min(y_raw) + 1e-12) if (np.max(y_raw) > 1.0 or np.min(y_raw) < 0.0) else y_raw
        beta_larf = _fit_weighted_logit(X_model, y_scaled, kappa_eff)
        p1 = 1.0 / (1.0 + np.exp(-np.clip(X_d1 @ beta_larf, -30.0, 30.0)))
        p0 = 1.0 / (1.0 + np.exp(-np.clip(X_d0 @ beta_larf, -30.0, 30.0)))
        w_sum = np.sum(kappa_eff) if np.sum(kappa_eff) > 0 else 1.0
        late_estimate = float(np.sum(kappa_eff * (p1 - p0)) / w_sum)
        e_y1_complier = float(np.sum(kappa_eff * p1) / w_sum)
        e_y0_complier = float(np.sum(kappa_eff * p0) / w_sum)

        # Naive Model (unweighted)
        beta_naive = _fit_weighted_logit(X_model, y_scaled, np.ones(n))
        p1_naive = 1.0 / (1.0 + np.exp(-np.clip(X_d1 @ beta_naive, -30.0, 30.0)))
        p0_naive = 1.0 / (1.0 + np.exp(-np.clip(X_d0 @ beta_naive, -30.0, 30.0)))
        naive_estimate = float(np.mean(p1_naive - p0_naive))

        # Intention to Treat (ITT) of Z on Y
        X_itt = np.column_stack([np.ones(n), z, X_prop[:, 1:]]) if X_prop.shape[1] > 1 else np.column_stack([np.ones(n), z])
        X_itt1 = X_itt.copy(); X_itt1[:, 1] = 1.0
        X_itt0 = X_itt.copy(); X_itt0[:, 1] = 0.0
        beta_itt = _fit_weighted_logit(X_itt, y_scaled, np.ones(n))
        p1_itt = 1.0 / (1.0 + np.exp(-np.clip(X_itt1 @ beta_itt, -30.0, 30.0)))
        p0_itt = 1.0 / (1.0 + np.exp(-np.clip(X_itt0 @ beta_itt, -30.0, 30.0)))
        itt_estimate = float(np.mean(p1_itt - p0_itt))
    else:
        y_scaled = y_raw
        beta_larf = _fit_weighted_ols(X_model, y_scaled, kappa_eff)
        late_estimate = float(beta_larf[1])
        e_y1_complier = float(np.mean(X_d1 @ beta_larf))
        e_y0_complier = float(np.mean(X_d0 @ beta_larf))

        # Naive OLS
        beta_naive = _fit_weighted_ols(X_model, y_scaled, np.ones(n))
        naive_estimate = float(beta_naive[1])

        # ITT OLS
        X_itt = np.column_stack([np.ones(n), z, X_prop[:, 1:]]) if X_prop.shape[1] > 1 else np.column_stack([np.ones(n), z])
        beta_itt = _fit_weighted_ols(X_itt, y_scaled, np.ones(n))
        itt_estimate = float(beta_itt[1])

    # Step 4: Non-parametric Bootstrap for Standard Errors & Confidence Intervals
    boot_lates = []
    boot_naives = []
    boot_itts = []
    boot_p_compliers = []

    rng = np.random.RandomState(42)
    for _ in range(n_bootstraps):
        idx = rng.choice(n, size=n, replace=True)
        b_y = y_scaled[idx]
        b_d = d[idx]
        b_z = z[idx]
        b_Xprop = X_prop[idx]

        # Fit propensity
        b_e = _fit_logistic_propensity(b_Xprop, b_z)
        b_t1 = (b_d * (1.0 - b_z)) / (1.0 - b_e)
        b_t2 = ((1.0 - b_d) * b_z) / b_e
        b_kappa = 1.0 - b_t1 - b_t2
        b_p_comp = float(np.mean(b_kappa))
        boot_p_compliers.append(b_p_comp)

        if trim_negative:
            b_kappa_eff = np.maximum(0.0, b_kappa)
        else:
            b_kappa_eff = b_kappa

        b_Xmodel = np.column_stack([np.ones(n), b_d, b_Xprop[:, 1:]]) if b_Xprop.shape[1] > 1 else np.column_stack([np.ones(n), b_d])
        b_Xd1 = b_Xmodel.copy(); b_Xd1[:, 1] = 1.0
        b_Xd0 = b_Xmodel.copy(); b_Xd0[:, 1] = 0.0

        if is_logit:
            b_beta_larf = _fit_weighted_logit(b_Xmodel, b_y, b_kappa_eff)
            bp1 = 1.0 / (1.0 + np.exp(-np.clip(b_Xd1 @ b_beta_larf, -30.0, 30.0)))
            bp0 = 1.0 / (1.0 + np.exp(-np.clip(b_Xd0 @ b_beta_larf, -30.0, 30.0)))
            bw_sum = np.sum(b_kappa_eff) if np.sum(b_kappa_eff) > 0 else 1.0
            boot_lates.append(float(np.sum(b_kappa_eff * (bp1 - bp0)) / bw_sum))

            b_beta_naive = _fit_weighted_logit(b_Xmodel, b_y, np.ones(n))
            bp1_naive = 1.0 / (1.0 + np.exp(-np.clip(b_Xd1 @ b_beta_naive, -30.0, 30.0)))
            bp0_naive = 1.0 / (1.0 + np.exp(-np.clip(b_Xd0 @ b_beta_naive, -30.0, 30.0)))
            boot_naives.append(float(np.mean(bp1_naive - bp0_naive)))

            b_Xitt = np.column_stack([np.ones(n), b_z, b_Xprop[:, 1:]]) if b_Xprop.shape[1] > 1 else np.column_stack([np.ones(n), b_z])
            b_Xitt1 = b_Xitt.copy(); b_Xitt1[:, 1] = 1.0
            b_Xitt0 = b_Xitt.copy(); b_Xitt0[:, 1] = 0.0
            b_beta_itt = _fit_weighted_logit(b_Xitt, b_y, np.ones(n))
            bp1_itt = 1.0 / (1.0 + np.exp(-np.clip(b_Xitt1 @ b_beta_itt, -30.0, 30.0)))
            bp0_itt = 1.0 / (1.0 + np.exp(-np.clip(b_Xitt0 @ b_beta_itt, -30.0, 30.0)))
            boot_itts.append(float(np.mean(bp1_itt - bp0_itt)))
        else:
            b_beta_larf = _fit_weighted_ols(b_Xmodel, b_y, b_kappa_eff)
            boot_lates.append(float(b_beta_larf[1]))

            b_beta_naive = _fit_weighted_ols(b_Xmodel, b_y, np.ones(n))
            boot_naives.append(float(b_beta_naive[1]))

            b_Xitt = np.column_stack([np.ones(n), b_z, b_Xprop[:, 1:]]) if b_Xprop.shape[1] > 1 else np.column_stack([np.ones(n), b_z])
            b_beta_itt = _fit_weighted_ols(b_Xitt, b_y, np.ones(n))
            boot_itts.append(float(b_beta_itt[1]))

    # Calculate standard errors and CI
    late_se = float(np.std(boot_lates, ddof=1)) if len(boot_lates) > 1 else 0.0
    late_ci_lower = float(np.percentile(boot_lates, 100.0 * (alpha_level / 2.0)))
    late_ci_upper = float(np.percentile(boot_lates, 100.0 * (1.0 - alpha_level / 2.0)))
    late_z = float(late_estimate / late_se) if late_se > 1e-8 else 0.0
    late_p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(late_z))))

    naive_se = float(np.std(boot_naives, ddof=1)) if len(boot_naives) > 1 else 0.0
    naive_ci_lower = float(np.percentile(boot_naives, 100.0 * (alpha_level / 2.0)))
    naive_ci_upper = float(np.percentile(boot_naives, 100.0 * (1.0 - alpha_level / 2.0)))
    naive_z = float(naive_estimate / naive_se) if naive_se > 1e-8 else 0.0
    naive_p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(naive_z))))

    itt_se = float(np.std(boot_itts, ddof=1)) if len(boot_itts) > 1 else 0.0
    itt_ci_lower = float(np.percentile(boot_itts, 100.0 * (alpha_level / 2.0)))
    itt_ci_upper = float(np.percentile(boot_itts, 100.0 * (1.0 - alpha_level / 2.0)))
    itt_z = float(itt_estimate / itt_se) if itt_se > 1e-8 else 0.0
    itt_p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(itt_z))))

    # Compliance diagnostics
    p_comp_se = float(np.std(boot_p_compliers, ddof=1)) if len(boot_p_compliers) > 1 else 0.0
    eff_n = float((np.sum(kappa_eff) ** 2) / (np.sum(kappa_eff ** 2) + 1e-12))

    # Construct variable names and coefficients table
    feature_names = ["Intercept", "Treatment (D)"] + covariate_cols
    coefficients_table = []
    for idx_feat, fname in enumerate(feature_names[:len(beta_larf)]):
        coefficients_table.append({
            "feature": fname,
            "coefficient": round(float(beta_larf[idx_feat]), 4)
        })

    # Generate Scientific SVG Visualization
    svg_chart = _generate_larf_svg(
        late_est=late_estimate, late_ci=(late_ci_lower, late_ci_upper),
        naive_est=naive_estimate, naive_ci=(naive_ci_lower, naive_ci_upper),
        itt_est=itt_estimate, itt_ci=(itt_ci_lower, itt_ci_upper),
        p_complier=p_complier, pct_negative=pct_negative,
        kappa=kappa
    )

    # Academic APA 7th Edition narrative
    apa_narrative = (
        f"A semiparametric Instrumental Variable Local Average Response Function (LARF; Abadie, 2003) "
        f"was estimated to evaluate the causal impact of '{treatment_col}' on '{outcome_col}' "
        f"leveraging '{instrument_col}' as an exogenous instrument across N = {n} respondents. "
        f"The estimated proportion of compliers in the surveyed population was P(c) = {p_complier:.1%} (SE = {p_comp_se:.3f}). "
        f"Among compliers, the Local Average Treatment Effect (LATE) on treatment response was "
        f"Δ = {late_estimate:.4f} (95% CI [{late_ci_lower:.4f}, {late_ci_upper:.4f}], z = {late_z:.2f}, p = {late_p_val:.4f}). "
        f"Expected counterfactual potential responses among compliers were E[Y(1)|c] = {e_y1_complier:.4f} and E[Y(0)|c] = {e_y0_complier:.4f}. "
        f"In contrast, the naive associative estimate unadjusted for endogeneity was {naive_estimate:.4f} "
        f"(95% CI [{naive_ci_lower:.4f}, {naive_ci_upper:.4f}], p = {naive_p_val:.4f}), demonstrating an endogeneity bias of "
        f"{(naive_estimate - late_estimate):.4f}. The Intention-to-Treat (ITT) effect of instrument assignment was "
        f"{itt_estimate:.4f} (95% CI [{itt_ci_lower:.4f}, {itt_ci_upper:.4f}]). "
        f"Abadie kappa diagnostic indicated {pct_negative:.1f}% negative sample weights, with an effective sample size of N_eff = {eff_n:.1f}."
    )

    return {
        "status": "SUCCESS",
        "model_type": f"LARF_{model_type.upper()}_ABADIE_2003",
        "sample_size": n,
        "effective_sample_size": round(eff_n, 1),
        "bootstrap_replications": n_bootstraps,
        "complier_probability": round(p_complier, 4),
        "complier_probability_se": round(p_comp_se, 4),
        "pct_negative_weights": round(pct_negative, 2),
        "potential_outcomes_compliers": {
            "e_y1_compliers": round(e_y1_complier, 4),
            "e_y0_compliers": round(e_y0_complier, 4)
        },
        "effects": {
            "late": {
                "estimate": round(late_estimate, 4),
                "std_error": round(late_se, 4),
                "z_stat": round(late_z, 3),
                "p_value": round(late_p_val, 4),
                "ci_lower": round(late_ci_lower, 4),
                "ci_upper": round(late_ci_upper, 4),
                "is_significant": bool(late_p_val < alpha_level)
            },
            "naive": {
                "estimate": round(naive_estimate, 4),
                "std_error": round(naive_se, 4),
                "z_stat": round(naive_z, 3),
                "p_value": round(naive_p_val, 4),
                "ci_lower": round(naive_ci_lower, 4),
                "ci_upper": round(naive_ci_upper, 4),
                "is_significant": bool(naive_p_val < alpha_level)
            },
            "itt": {
                "estimate": round(itt_estimate, 4),
                "std_error": round(itt_se, 4),
                "z_stat": round(itt_z, 3),
                "p_value": round(itt_p_val, 4),
                "ci_lower": round(itt_ci_lower, 4),
                "ci_upper": round(itt_ci_upper, 4),
                "is_significant": bool(itt_p_val < alpha_level)
            }
        },
        "model_coefficients": coefficients_table,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_larf_svg(
    late_est: float, late_ci: tuple,
    naive_est: float, naive_ci: tuple,
    itt_est: float, itt_ci: tuple,
    p_complier: float, pct_negative: float,
    kappa: np.ndarray
) -> str:
    """
    Constructs a dual-panel SVG visualizer:
    - Panel A: Forest Plot comparing LARF LATE (Compliers) vs ITT vs Naive Association with 95% CIs.
    - Panel B: Kappa Weight Density / Histogram showing compliance weight distribution.
    """
    svg_w, svg_h = 760, 320
    pad = 40

    # Range for forest plot
    all_vals = [late_est, late_ci[0], late_ci[1], naive_est, naive_ci[0], naive_ci[1], itt_est, itt_ci[0], itt_ci[1], 0.0]
    min_x = min(all_vals) - 0.08
    max_x = max(all_vals) + 0.08
    span_x = max(max_x - min_x, 1e-5)

    def to_fp_x(val):
        # Panel A spans x from 40 to 380
        return 40 + ((val - min_x) / span_x) * 320

    zero_x = to_fp_x(0.0)

    # Models: (Label, Est, CI_low, CI_high, Color, Y_pos)
    rows = [
        ("LARF LATE (Compliers)", late_est, late_ci[0], late_ci[1], "#4f46e5", 95),
        ("ITT (Z -> Y)", itt_est, itt_ci[0], itt_ci[1], "#0ea5e9", 155),
        ("Naive (Unweighted)", naive_est, naive_ci[0], naive_ci[1], "#f59e0b", 215)
    ]

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#f8fafc" rx="8" />',
        '  <!-- Panel A Header -->',
        '  <text x="40" y="32" font-size="13" font-weight="700" fill="#1e293b">PANEL A: Causal Response Forest Plot (95% CI)</text>',
        '  <text x="40" y="48" font-size="11" fill="#64748b">Comparing Local Average Response against ITT &amp; Naive Association</text>',
        '  <!-- Panel B Header -->',
        '  <text x="420" y="32" font-size="13" font-weight="700" fill="#1e293b">PANEL B: Abadie Kappa Weight Distribution</text>',
        f'  <text x="420" y="48" font-size="11" fill="#64748b">P(Compliers) = {p_complier:.1%} | Negative Weights = {pct_negative:.1f}%</text>',
        '  <line x1="400" y1="20" x2="400" y2="300" stroke="#e2e8f0" stroke-dasharray="4 4" stroke-width="1.5" />'
    ]

    # Panel A: Forest Plot
    # Zero reference line
    svg_lines.append(f'  <line x1="{zero_x:.1f}" y1="65" x2="{zero_x:.1f}" y2="250" stroke="#94a3b8" stroke-dasharray="2 2" stroke-width="1.5" />')
    svg_lines.append(f'  <text x="{zero_x:.1f}" y="265" font-size="10" fill="#64748b" text-anchor="middle">Null (0.0)</text>')

    for label, est, c_low, c_high, col, y_pos in rows:
        x_est = to_fp_x(est)
        x_low = to_fp_x(c_low)
        x_high = to_fp_x(c_high)

        svg_lines.append(f'  <text x="40" y="{y_pos - 12}" font-size="11" font-weight="600" fill="#334155">{label}</text>')
        # CI bar
        svg_lines.append(f'  <line x1="{x_low:.1f}" y1="{y_pos}" x2="{x_high:.1f}" y2="{y_pos}" stroke="{col}" stroke-width="3" stroke-linecap="round" />')
        svg_lines.append(f'  <line x1="{x_low:.1f}" y1="{y_pos - 5}" x2="{x_low:.1f}" y2="{y_pos + 5}" stroke="{col}" stroke-width="2" />')
        svg_lines.append(f'  <line x1="{x_high:.1f}" y1="{y_pos - 5}" x2="{x_high:.1f}" y2="{y_pos + 5}" stroke="{col}" stroke-width="2" />')
        # Point estimate marker
        svg_lines.append(f'  <circle cx="{x_est:.1f}" cy="{y_pos}" r="5.5" fill="{col}" stroke="#ffffff" stroke-width="1.5" />')
        # Value label
        svg_lines.append(f'  <text x="{x_high + 8:.1f}" y="{y_pos + 4}" font-size="10" font-weight="600" fill="{col}">{est:.3f}</text>')

    # Panel B: Histogram / Density of kappa
    # Kappa values typically range from negative to > 1
    k_min = max(-1.5, float(np.percentile(kappa, 1)))
    k_max = min(3.0, float(np.percentile(kappa, 99)))
    bins = np.linspace(k_min, k_max, 16)
    counts, edges = np.histogram(kappa, bins=bins)
    max_count = max(np.max(counts), 1)

    panel_b_x = 420
    panel_b_w = 300
    panel_b_y = 240
    panel_b_h = 160

    # Zero cutoff for negative weights in Panel B
    k_span = max(k_max - k_min, 1e-5)
    zero_k_x = panel_b_x + ((0.0 - k_min) / k_span) * panel_b_w

    if panel_b_x <= zero_k_x <= (panel_b_x + panel_b_w):
        svg_lines.append(f'  <line x1="{zero_k_x:.1f}" y1="70" x2="{zero_k_x:.1f}" y2="{panel_b_y}" stroke="#ef4444" stroke-dasharray="3 3" stroke-width="1.5" />')
        svg_lines.append(f'  <text x="{zero_k_x:.1f}" y="65" font-size="9" fill="#ef4444" text-anchor="middle">κ = 0</text>')

    # Draw bars
    bar_w = panel_b_w / len(counts)
    for idx_b, cnt in enumerate(counts):
        b_left = panel_b_x + idx_b * bar_w
        b_height = (cnt / max_count) * (panel_b_h - 20)
        b_top = panel_b_y - b_height
        is_neg = (edges[idx_b] < 0.0)
        bar_fill = "#fca5a5" if is_neg else "#a5b4fc"
        bar_stroke = "#ef4444" if is_neg else "#6366f1"
        svg_lines.append(f'  <rect x="{b_left + 1:.1f}" y="{b_top:.1f}" width="{bar_w - 2:.1f}" height="{b_height:.1f}" fill="{bar_fill}" stroke="{bar_stroke}" stroke-width="1" rx="2" />')

    # Baseline line for Panel B
    svg_lines.append(f'  <line x1="{panel_b_x}" y1="{panel_b_y}" x2="{panel_b_x + panel_b_w}" y2="{panel_b_y}" stroke="#94a3b8" stroke-width="1.5" />')
    svg_lines.append(f'  <text x="{panel_b_x}" y="{panel_b_y + 16}" font-size="9" fill="#64748b">{k_min:.1f}</text>')
    svg_lines.append(f'  <text x="{panel_b_x + panel_b_w / 2}" y="{panel_b_y + 16}" font-size="9" fill="#64748b" text-anchor="middle">Abadie Weight (κ)</text>')
    svg_lines.append(f'  <text x="{panel_b_x + panel_b_w}" y="{panel_b_y + 16}" font-size="9" fill="#64748b" text-anchor="end">{k_max:.1f}</text>')

    # Legend in Panel B
    svg_lines.append(f'  <rect x="420" y="275" width="12" height="12" fill="#a5b4fc" rx="2" />')
    svg_lines.append(f'  <text x="438" y="285" font-size="10" fill="#475569">Complier Weights (κ ≥ 0)</text>')
    svg_lines.append(f'  <rect x="580" y="275" width="12" height="12" fill="#fca5a5" rx="2" />')
    svg_lines.append(f'  <text x="598" y="285" font-size="10" fill="#475569">Negative Region (κ &lt; 0)</text>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)
