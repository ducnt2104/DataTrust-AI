# -*- coding: utf-8 -*-
"""
Surrogate Index & Long-Term Causal Evaluation from Short-Term Proxies Engine
Scientific References:
- Athey, S., Chetty, R., Imbens, G. W., & Kang, H. (2019). "The Surrogate Index:
  Combining Experimental and Observational Data to Estimate Long-Term Treatment Effects."
  Econometrica, 88(6), 2401-2435.
- Prentice, R. L. (1989). "Surrogate endpoints in clinical trials: definition and
  operational criteria." Statistics in Medicine, 8(4), 431-440.

Estimates long-term treatment effects by constructing a Surrogate Index r(S, X)
from short-term intermediate survey questions and projecting long-term counterfactuals.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _fit_ridge_surrogate_index(
    S_mat: np.ndarray,
    X_mat: np.ndarray,
    y_obs: np.ndarray,
    alpha_ridge: float = 1.0
) -> Tuple[np.ndarray, float, float]:
    """
    Fits surrogate index model r(S, X) = E[Y | S, X] on observational sample
    using ridge-regularized least squares.
    Returns: (coefficients, r_squared, residual_variance)
    """
    n, p_s = S_mat.shape
    p_x = X_mat.shape[1] if X_mat.ndim > 1 else 0
    
    if p_x > 0:
        M = np.column_stack([np.ones(n), S_mat, X_mat])
    else:
        M = np.column_stack([np.ones(n), S_mat])
        
    k = M.shape[1]
    # Penalize all coefficients except intercept
    reg_matrix = alpha_ridge * np.eye(k)
    reg_matrix[0, 0] = 0.0
    
    try:
        coef = np.linalg.solve(M.T @ M + reg_matrix, M.T @ y_obs)
    except np.linalg.LinAlgError:
        coef = np.linalg.lstsq(M.T @ M + reg_matrix, M.T @ y_obs, rcond=None)[0]
        
    y_pred = M @ coef
    ss_tot = np.sum((y_obs - np.mean(y_obs)) ** 2) + 1e-12
    ss_res = np.sum((y_obs - y_pred) ** 2)
    r2 = max(0.0, 1.0 - (ss_res / ss_tot))
    s2 = ss_res / max(n - k, 1)
    
    return coef, float(r2), float(s2)


def estimate_surrogate_index(
    df: pd.DataFrame,
    treatment_col: str,
    surrogate_cols: List[str],
    longterm_outcome_col: str,
    covariate_cols: Optional[List[str]] = None,
    sample_indicator_col: Optional[str] = None,
    alpha_level: float = 0.05,
    n_bootstraps: int = 300,
    ridge_lambda: float = 1.0
) -> Dict[str, Any]:
    """
    Estimates the long-term causal effect using the Athey et al. (2019) Surrogate Index framework.
    - If sample_indicator_col is provided: 1 = experimental sample, 0 = observational sample.
    - If sample_indicator_col is None: splits or identifies experimental vs observational based
      on where long-term outcome Y is observed vs where treatment W is assigned.
    """
    if covariate_cols is None:
        covariate_cols = []

    req_cols = [treatment_col, longterm_outcome_col] + surrogate_cols + covariate_cols
    for col in req_cols:
        if col not in df.columns:
            return {"status": "ERROR", "message": f"Column '{col}' not found in dataframe."}

    sub_df = df.copy()
    n_total = len(sub_df)
    if n_total < 40:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": f"Sample size (N={n_total}) is insufficient for Surrogate Index estimation (minimum 40 required)."
        }

    # Identify samples:
    # Experimental sample: treatment is assigned, surrogates are observed.
    # Observational sample: surrogates and long-term Y are observed.
    if sample_indicator_col and sample_indicator_col in sub_df.columns:
        is_exp = (sub_df[sample_indicator_col] == 1)
        is_obs = (sub_df[sample_indicator_col] == 0)
    else:
        # Default partition: rows where long-term Y is observed form the observational/follow-up sample.
        # Entire sample or randomized subset forms the experimental sample.
        has_y = sub_df[longterm_outcome_col].notna()
        is_obs = has_y
        is_exp = sub_df[treatment_col].notna()

    n_exp = int(np.sum(is_exp))
    n_obs = int(np.sum(is_obs))

    if n_exp < 20 or n_obs < 20:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": f"Both experimental sample (N={n_exp}) and observational sample (N={n_obs}) must have at least 20 observations."
        }

    # Extract experimental sample data
    df_exp = sub_df[is_exp].copy()
    t_raw_exp = df_exp[treatment_col].dropna().values
    if len(np.unique(t_raw_exp)) <= 2:
        t_exp = (df_exp[treatment_col] == np.max(t_raw_exp)).astype(float).values
    else:
        t_exp = (df_exp[treatment_col] > np.median(t_raw_exp)).astype(float).values
    S_exp = df_exp[surrogate_cols].astype(float).values
    X_exp = df_exp[covariate_cols].astype(float).values if covariate_cols else np.empty((n_exp, 0))

    # Extract observational sample data
    df_obs = sub_df[is_obs].dropna(subset=[longterm_outcome_col] + surrogate_cols).copy()
    y_obs = df_obs[longterm_outcome_col].astype(float).values
    S_obs = df_obs[surrogate_cols].astype(float).values
    X_obs = df_obs[covariate_cols].astype(float).values if covariate_cols else np.empty((len(df_obs), 0))

    # Standardize surrogates and covariates for stable fitting
    s_mean = np.mean(S_obs, axis=0)
    s_std = np.std(S_obs, axis=0)
    s_std[s_std == 0] = 1.0

    S_obs_std = (S_obs - s_mean) / s_std
    S_exp_std = (S_exp - s_mean) / s_std

    if X_obs.shape[1] > 0:
        x_mean = np.mean(X_obs, axis=0)
        x_std = np.std(X_obs, axis=0)
        x_std[x_std == 0] = 1.0
        X_obs_std = (X_obs - x_mean) / x_std
        X_exp_std = (X_exp - x_mean) / x_std
    else:
        X_obs_std = np.empty((len(df_obs), 0))
        X_exp_std = np.empty((n_exp, 0))

    # Step 1: Fit Surrogate Index r(S, X) on Observational Sample
    coef_r, r2_index, s2_index = _fit_ridge_surrogate_index(S_obs_std, X_obs_std, y_obs, alpha_ridge=ridge_lambda)

    # Step 2: Predict Surrogate Index in Experimental Sample
    if X_exp_std.shape[1] > 0:
        M_exp = np.column_stack([np.ones(n_exp), S_exp_std, X_exp_std])
    else:
        M_exp = np.column_stack([np.ones(n_exp), S_exp_std])

    r_hat_exp = M_exp @ coef_r

    # Long-term treatment effect estimate on experimental sample
    t1_mask = (t_exp == 1.0)
    t0_mask = (t_exp == 0.0)

    if np.sum(t1_mask) == 0 or np.sum(t0_mask) == 0:
        return {"status": "ERROR", "message": "Experimental sample lacks treated or control units."}

    tau_longterm = float(np.mean(r_hat_exp[t1_mask]) - np.mean(r_hat_exp[t0_mask]))

    # Step 3: Compute Individual Short-Term Surrogate Effects
    surrogate_effects = []
    for idx_s, scol in enumerate(surrogate_cols):
        s_vals = S_exp[:, idx_s]
        s_t1 = s_vals[t1_mask]
        s_t0 = s_vals[t0_mask]
        diff_s = float(np.mean(s_t1) - np.mean(s_t0))
        se_s = float(np.sqrt(np.var(s_t1, ddof=1)/len(s_t1) + np.var(s_t0, ddof=1)/len(s_t0)))
        surrogate_effects.append({
            "surrogate_name": scol,
            "treatment_effect": round(diff_s, 4),
            "std_error": round(se_s, 4),
            "surrogate_weight_in_index": round(float(coef_r[1 + idx_s]), 4)
        })

    # Step 4: Two-Sample Bootstrap Inference
    boot_taus = []
    rng = np.random.RandomState(42)

    for _ in range(n_bootstraps):
        # Resample observational sample
        idx_b_obs = rng.choice(len(df_obs), size=len(df_obs), replace=True)
        b_S_obs = S_obs_std[idx_b_obs]
        b_X_obs = X_obs_std[idx_b_obs] if X_obs_std.shape[1] > 0 else np.empty((len(df_obs), 0))
        b_y_obs = y_obs[idx_b_obs]

        b_coef, _, _ = _fit_ridge_surrogate_index(b_S_obs, b_X_obs, b_y_obs, alpha_ridge=ridge_lambda)

        # Resample experimental sample
        idx_b_exp = rng.choice(n_exp, size=n_exp, replace=True)
        b_t_exp = t_exp[idx_b_exp]
        b_M_exp = M_exp[idx_b_exp]

        b_r_hat = b_M_exp @ b_coef
        b_t1 = (b_t_exp == 1.0)
        b_t0 = (b_t_exp == 0.0)

        if np.sum(b_t1) > 0 and np.sum(b_t0) > 0:
            boot_taus.append(float(np.mean(b_r_hat[b_t1]) - np.mean(b_r_hat[b_t0])))

    se_longterm = float(np.std(boot_taus, ddof=1)) if len(boot_taus) > 1 else 0.05
    ci_low = float(np.percentile(boot_taus, 100.0 * (alpha_level / 2.0)))
    ci_high = float(np.percentile(boot_taus, 100.0 * (1.0 - alpha_level / 2.0)))
    z_stat = float(tau_longterm / se_longterm) if se_longterm > 1e-8 else 0.0
    p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))

    # Surrogacy Validation Check:
    # If treatment is observed in observational sample with long-term Y, test direct effect W -> Y | S, X
    surrogacy_violation_risk = "LOW_RISK"
    direct_effect_p = None
    if treatment_col in df_obs.columns:
        t_raw_obs = df_obs[treatment_col].dropna().values
        if len(np.unique(t_raw_obs)) <= 2:
            t_obs = (df_obs[treatment_col] == np.max(t_raw_obs)).astype(float).values
        else:
            t_obs = (df_obs[treatment_col] > np.median(t_raw_obs)).astype(float).values
        M_val = np.column_stack([np.ones(len(df_obs)), t_obs, S_obs_std])
        try:
            val_coef = np.linalg.lstsq(M_val, y_obs, rcond=None)[0]
            val_res = y_obs - (M_val @ val_coef)
            val_s2 = np.sum(val_res ** 2) / max(len(df_obs) - M_val.shape[1], 1)
            val_var = val_s2 * np.linalg.pinv(M_val.T @ M_val)[1, 1]
            val_se = math.sqrt(max(val_var, 1e-8))
            val_z = val_coef[1] / val_se
            direct_effect_p = float(2.0 * (1.0 - stats.norm.cdf(abs(val_z))))
            if direct_effect_p < 0.05:
                surrogacy_violation_risk = "MODERATE_RISK (Direct treatment effect on Y detected after conditioning on surrogates; surrogacy assumption partially violated)"
            else:
                surrogacy_violation_risk = "SURROGACY_SATISFIED (Direct treatment effect is statistically zero; surrogacy condition holds)"
        except Exception:
            surrogacy_violation_risk = "NOT_EVALUATED"

    # Generate Scientific SVG Visualization
    svg_chart = _generate_surrogate_svg(
        tau_longterm=tau_longterm, ci_low=ci_low, ci_high=ci_high,
        surrogate_effects=surrogate_effects,
        r2_index=r2_index,
        n_exp=n_exp, n_obs=n_obs
    )

    # Academic APA 7th Edition narrative
    apa_narrative = (
        f"A Surrogate Index causal framework (Athey, Chetty, Imbens, & Kang, 2019) was estimated to evaluate the "
        f"long-term treatment effect of '{treatment_col}' on '{longterm_outcome_col}' by combining an experimental survey sample "
        f"(N_exp = {n_exp}) with an observational follow-up sample (N_obs = {n_obs}) using {len(surrogate_cols)} short-term surrogates "
        f"({', '.join(surrogate_cols)}). "
        f"The fitted surrogate index model accounted for {r2_index:.1%} of variation in the long-term outcome (R^2 = {r2_index:.3f}). "
        f"The projected long-term Average Treatment Effect was tau_Y = {tau_longterm:.4f} "
        f"(Two-sample bootstrap 95% CI [{ci_low:.4f}, {ci_high:.4f}], z = {z_stat:.2f}, p = {p_val:.4f}). "
        f"Surrogacy diagnostic assessment: {surrogacy_violation_risk}."
    )

    return {
        "status": "SUCCESS",
        "model_type": "SURROGATE_INDEX_ATHEY_CHETTY_IMBENS_2019",
        "sample_sizes": {
            "experimental_sample": n_exp,
            "observational_sample": n_obs,
            "total": n_total
        },
        "bootstrap_replications": n_bootstraps,
        "surrogate_index_fit": {
            "r_squared": round(r2_index, 4),
            "ridge_lambda": ridge_lambda
        },
        "longterm_treatment_effect": {
            "estimate": round(tau_longterm, 4),
            "std_error": round(se_longterm, 4),
            "z_stat": round(z_stat, 3),
            "p_value": round(p_val, 4),
            "ci_lower": round(ci_low, 4),
            "ci_upper": round(ci_high, 4),
            "is_significant": bool(p_val < alpha_level)
        },
        "surrogate_decomposition": surrogate_effects,
        "surrogacy_validation": {
            "risk_status": surrogacy_violation_risk,
            "direct_effect_p_value": round(direct_effect_p, 4) if direct_effect_p is not None else None
        },
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_surrogate_svg(
    tau_longterm: float, ci_low: float, ci_high: float,
    surrogate_effects: List[Dict[str, Any]],
    r2_index: float,
    n_exp: int, n_obs: int
) -> str:
    """
    Constructs a dual-panel SVG visualizer:
    - Panel A: Forest Plot comparing Long-term Effect vs Individual Surrogate Effects with 95% CIs.
    - Panel B: Surrogate Relative Weight Contributions to the Long-Term Index r(S, X).
    """
    svg_w, svg_h = 760, 320

    # Scale for Forest Plot Panel A (x spans from 40 to 390)
    all_vals = [tau_longterm, ci_low, ci_high, 0.0]
    for se in surrogate_effects:
        all_vals.extend([se["treatment_effect"], se["treatment_effect"] - 1.96*se["std_error"], se["treatment_effect"] + 1.96*se["std_error"]])

    min_x = min(all_vals) - 0.2
    max_x = max(all_vals) + 0.2
    span_x = max(max_x - min_x, 1e-4)

    def to_fp_x(val):
        return 40 + ((val - min_x) / span_x) * 350

    zero_x = to_fp_x(0.0)

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#f8fafc" rx="8" />',
        '  <!-- Panel A Header -->',
        '  <text x="40" y="32" font-size="13" font-weight="700" fill="#1e293b">PANEL A: Projected Long-Term vs Short-Term Effects</text>',
        '  <text x="40" y="48" font-size="11" fill="#64748b">Athey et al. (2019) Surrogate Index vs Intermediate Proxies</text>',
        '  <!-- Panel B Header -->',
        '  <text x="440" y="32" font-size="13" font-weight="700" fill="#1e293b">PANEL B: Surrogate Predictive Weights in r(S, X)</text>',
        f'  <text x="440" y="48" font-size="11" fill="#64748b">Observational R² = {r2_index:.1%} (N_obs = {n_obs})</text>',
        '  <line x1="415" y1="20" x2="415" y2="300" stroke="#e2e8f0" stroke-dasharray="4 4" stroke-width="1.5" />'
    ]

    # Panel A Zero Line
    svg_lines.append(f'  <line x1="{zero_x:.1f}" y1="65" x2="{zero_x:.1f}" y2="280" stroke="#94a3b8" stroke-dasharray="2 2" stroke-width="1.5" />')
    svg_lines.append(f'  <text x="{zero_x:.1f}" y="295" font-size="10" fill="#64748b" text-anchor="middle">Null (0.0)</text>')

    # Row 1: Long-term Treatment Effect (Prominent Indigo)
    y_r1 = 95
    x_tau = to_fp_x(tau_longterm)
    x_low = to_fp_x(ci_low)
    x_high = to_fp_x(ci_high)
    svg_lines.append(f'  <text x="40" y="{y_r1 - 12}" font-size="11" font-weight="700" fill="#4f46e5">Long-Term Causal Effect (τ_Y)</text>')
    svg_lines.append(f'  <line x1="{x_low:.1f}" y1="{y_r1}" x2="{x_high:.1f}" y2="{y_r1}" stroke="#4f46e5" stroke-width="3" stroke-linecap="round" />')
    svg_lines.append(f'  <line x1="{x_low:.1f}" y1="{y_r1 - 5}" x2="{x_low:.1f}" y2="{y_r1 + 5}" stroke="#4f46e5" stroke-width="2" />')
    svg_lines.append(f'  <line x1="{x_high:.1f}" y1="{y_r1 - 5}" x2="{x_high:.1f}" y2="{y_r1 + 5}" stroke="#4f46e5" stroke-width="2" />')
    svg_lines.append(f'  <circle cx="{x_tau:.1f}" cy="{y_r1}" r="6" fill="#4f46e5" stroke="#ffffff" stroke-width="2" />')
    svg_lines.append(f'  <text x="{x_high + 8:.1f}" y="{y_r1 + 4}" font-size="11" font-weight="700" fill="#4f46e5">{tau_longterm:.3f}</text>')

    # Subsequent rows: Individual surrogates
    cur_y = 150
    for idx_s, se in enumerate(surrogate_effects[:3]):
        s_name = se["surrogate_name"]
        if len(s_name) > 22:
            s_name = s_name[:20] + ".."
        s_val = se["treatment_effect"]
        s_low = to_fp_x(s_val - 1.96 * se["std_error"])
        s_high = to_fp_x(s_val + 1.96 * se["std_error"])
        s_pt = to_fp_x(s_val)

        svg_lines.append(f'  <text x="40" y="{cur_y - 10}" font-size="10" font-weight="600" fill="#475569">Proxy S{idx_s + 1}: {s_name}</text>')
        svg_lines.append(f'  <line x1="{s_low:.1f}" y1="{cur_y}" x2="{s_high:.1f}" y2="{cur_y}" stroke="#0ea5e9" stroke-width="2" />')
        svg_lines.append(f'  <circle cx="{s_pt:.1f}" cy="{cur_y}" r="4.5" fill="#0ea5e9" stroke="#ffffff" stroke-width="1.5" />')
        svg_lines.append(f'  <text x="{s_high + 8:.1f}" y="{cur_y + 4}" font-size="10" font-weight="600" fill="#0ea5e9">{s_val:.2f}</text>')
        cur_y += 45

    # Panel B: Surrogate Relative Weights Bar Chart
    p2_x, p2_y, p2_w = 440, 80, 280
    weights = [abs(se["surrogate_weight_in_index"]) for se in surrogate_effects]
    max_w = max(max(weights) if weights else 1.0, 1e-4)

    b_y = p2_y
    for idx_s, se in enumerate(surrogate_effects[:5]):
        w_val = se["surrogate_weight_in_index"]
        bar_len = (abs(w_val) / max_w) * (p2_w - 70)
        s_label = se["surrogate_name"]
        if len(s_label) > 18:
            s_label = s_label[:16] + ".."

        svg_lines.append(f'  <text x="{p2_x}" y="{b_y + 14}" font-size="10" font-weight="600" fill="#334155">{s_label}</text>')
        svg_lines.append(f'  <rect x="{p2_x + 90}" y="{b_y}" width="{p2_w - 90}" height="18" fill="#e2e8f0" rx="3" />')
        svg_lines.append(f'  <rect x="{p2_x + 90}" y="{b_y}" width="{max(bar_len, 2.0):.1f}" height="18" fill="#6366f1" rx="3" />')
        svg_lines.append(f'  <text x="{p2_x + 95 + bar_len:.1f}" y="{b_y + 13}" font-size="9" font-weight="700" fill="#4f46e5">{w_val:.2f}</text>')
        b_y += 38

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)
