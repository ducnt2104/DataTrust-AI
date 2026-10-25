# -*- coding: utf-8 -*-
"""
Causal Sensitivity Analysis & Omitted Variable Bias Contour Engine
Scientific References:
- Cinelli, C., & Hazlett, C. (2020). "Making sense of sensitivity: Extending
  omitted variable bias without making assumptions."
  Journal of the Royal Statistical Society: Series B (Statistical Methodology), 82(1), 39-67.
- Cinelli, C., & Hazlett, C. (2020). "sensemakr: Sensitivity Analysis for
  Omitted Variables in R and Stata."

Provides exact, distribution-free omitted variable bias formulas in terms of partial R2,
computes the Robustness Value (RV_q) and statistical significance Robustness Value (RV_alpha),
performs benchmark comparisons with observed covariates (1x, 2x, 3x multipliers),
and generates publication-grade sensitivity contour maps.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _compute_partial_r2(
    y: np.ndarray,
    d: np.ndarray,
    X: np.ndarray
) -> Tuple[float, float, float, float, int]:
    """
    Fits primary OLS regression: Y ~ D + X
    Returns:
        tau_hat: treatment coefficient
        se_tau: standard error of tau
        t_stat: t-statistic of tau
        r2_yd_x: partial R2 of treatment with outcome given covariates: R^2_{Y ~ D | X}
        df_error: residual degrees of freedom
    """
    n = len(y)
    p_x = X.shape[1] if X.ndim > 1 else 0
    
    # 1. Full model: Y on 1, D, X
    if p_x > 0:
        M_full = np.column_stack([np.ones(n), d, X])
    else:
        M_full = np.column_stack([np.ones(n), d])
        
    k = M_full.shape[1]
    df_error = n - k
    if df_error <= 2:
        raise ValueError(f"Insufficient degrees of freedom: df={df_error} (N={n}, predictors={k}).")
        
    beta_full, ss_res_full = np.linalg.lstsq(M_full, y, rcond=None)[:2]
    if len(ss_res_full) == 0:
        ss_res_full = np.sum((y - M_full @ beta_full) ** 2)
    else:
        ss_res_full = float(ss_res_full[0])
        
    sigma2 = ss_res_full / max(df_error, 1)
    
    try:
        inv_XtX = np.linalg.inv(M_full.T @ M_full)
    except np.linalg.LinAlgError:
        inv_XtX = np.linalg.pinv(M_full.T @ M_full)
        
    tau_hat = float(beta_full[1])
    se_tau = float(np.sqrt(max(1e-12, sigma2 * inv_XtX[1, 1])))
    t_stat = float(tau_hat / se_tau) if se_tau > 1e-12 else 0.0
    
    # 2. Restricted model: Y on 1, X (excluding D)
    if p_x > 0:
        M_rest = np.column_stack([np.ones(n), X])
    else:
        M_rest = np.ones((n, 1))
        
    beta_rest, ss_res_rest = np.linalg.lstsq(M_rest, y, rcond=None)[:2]
    if len(ss_res_rest) == 0:
        ss_res_rest = np.sum((y - M_rest @ beta_rest) ** 2)
    else:
        ss_res_rest = float(ss_res_rest[0])
        
    # Partial R2: R^2_{Y ~ D | X} = (SS_res_rest - SS_res_full) / SS_res_rest = t^2 / (t^2 + df)
    r2_yd_x = (t_stat ** 2) / (t_stat ** 2 + df_error)
    r2_yd_x = max(0.0, min(1.0, float(r2_yd_x)))
    
    return tau_hat, se_tau, t_stat, r2_yd_x, int(df_error)


def _compute_covariate_benchmarks(
    y: np.ndarray,
    d: np.ndarray,
    X: np.ndarray,
    covariate_names: List[str]
) -> List[Dict[str, Any]]:
    """
    Computes empirical partial R2 for each observed covariate X_j:
    - R^2_{D ~ X_j | X_{-j}}: strength of association with treatment
    - R^2_{Y ~ X_j | D, X_{-j}}: strength of association with outcome
    """
    n, p = X.shape
    benchmarks = []
    
    for j in range(p):
        col_name = covariate_names[j]
        xj = X[:, j]
        other_idx = [i for i in range(p) if i != j]
        
        # 1. R^2_{D ~ X_j | X_{-j}}
        if len(other_idx) > 0:
            M_x_other = np.column_stack([np.ones(n), X[:, other_idx]])
            M_d_full = np.column_stack([np.ones(n), xj, X[:, other_idx]])
        else:
            M_x_other = np.ones((n, 1))
            M_d_full = np.column_stack([np.ones(n), xj])
            
        beta_d_other, ss_d_other = np.linalg.lstsq(M_x_other, d, rcond=None)[:2]
        ss_d_other_val = float(ss_d_other[0]) if len(ss_d_other) > 0 else np.sum((d - M_x_other @ beta_d_other) ** 2)
        
        beta_d_full, ss_d_full = np.linalg.lstsq(M_d_full, d, rcond=None)[:2]
        ss_d_full_val = float(ss_d_full[0]) if len(ss_d_full) > 0 else np.sum((d - M_d_full @ beta_d_full) ** 2)
        
        r2_d_xj = max(0.0, min(0.999, (ss_d_other_val - ss_d_full_val) / max(ss_d_other_val, 1e-12)))
        
        # 2. R^2_{Y ~ X_j | D, X_{-j}}
        if len(other_idx) > 0:
            M_y_other = np.column_stack([np.ones(n), d, X[:, other_idx]])
            M_y_full = np.column_stack([np.ones(n), d, xj, X[:, other_idx]])
        else:
            M_y_other = np.column_stack([np.ones(n), d])
            M_y_full = np.column_stack([np.ones(n), d, xj])
            
        beta_y_other, ss_y_other = np.linalg.lstsq(M_y_other, y, rcond=None)[:2]
        ss_y_other_val = float(ss_y_other[0]) if len(ss_y_other) > 0 else np.sum((y - M_y_other @ beta_y_other) ** 2)
        
        beta_y_full, ss_y_full = np.linalg.lstsq(M_y_full, y, rcond=None)[:2]
        ss_y_full_val = float(ss_y_full[0]) if len(ss_y_full) > 0 else np.sum((y - M_y_full @ beta_y_full) ** 2)
        
        r2_y_xj = max(0.0, min(0.999, (ss_y_other_val - ss_y_full_val) / max(ss_y_other_val, 1e-12)))
        
        benchmarks.append({
            "covariate": col_name,
            "r2_d_given_x": round(float(r2_d_xj), 4),
            "r2_y_given_dx": round(float(r2_y_xj), 4)
        })
        
    return benchmarks


def _compute_adjusted_estimate_and_se(
    tau_hat: float,
    se_tau: float,
    df_error: int,
    r2_dz_x: float,
    r2_yz_dx: float
) -> Tuple[float, float, float]:
    """
    Cinelli & Hazlett (2020) exact formulas:
    bias = se_tau * sqrt(df) * sqrt( (r2_yz_dx * r2_dz_x) / (1 - r2_dz_x) )
    tau_adj = tau_hat - sign(tau_hat) * bias
    se_adj = se_tau * sqrt( ((1 - r2_yz_dx) / (1 - r2_dz_x)) * (df / (df - 1)) )
    """
    if r2_dz_x >= 1.0 or r2_yz_dx >= 1.0:
        return 0.0, 1e6, 0.0
        
    bias_factor = math.sqrt((r2_yz_dx * r2_dz_x) / max(1e-12, 1.0 - r2_dz_x))
    bias = se_tau * math.sqrt(df_error) * bias_factor
    
    # Conservative direction: confounder pulls estimate toward zero
    tau_adj = tau_hat - np.sign(tau_hat) * bias
    
    df_ratio = df_error / max(df_error - 1, 1)
    se_adj = se_tau * math.sqrt(max(1e-12, ((1.0 - r2_yz_dx) / max(1e-12, 1.0 - r2_dz_x)) * df_ratio))
    t_adj = tau_adj / se_adj if se_adj > 1e-12 else 0.0
    
    return float(tau_adj), float(se_adj), float(t_adj)


def _compute_robustness_value(
    t_stat: float,
    df_error: int,
    q: float = 1.0,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculates RV_q (bringing effect down by 100q%) and RV_alpha (bringing effect to insignificance).
    f_q = (q * |t|) / sqrt(df)
    RV_q = 0.5 * ( sqrt(f_q^4 + 4*f_q^2) - f_q^2 )
    """
    # 1. Point estimate robustness value RV_q
    f_q = (q * abs(t_stat)) / math.sqrt(df_error)
    rv_q = 0.5 * (math.sqrt(f_q ** 4 + 4.0 * (f_q ** 2)) - (f_q ** 2))
    rv_q = max(0.0, min(1.0, float(rv_q)))
    
    # 2. Significance robustness value RV_alpha
    t_crit = stats.t.ppf(1.0 - alpha / 2.0, df_error)
    if abs(t_stat) > t_crit:
        f_alpha = (abs(t_stat) - t_crit) / math.sqrt(df_error)
        rv_alpha = 0.5 * (math.sqrt(f_alpha ** 4 + 4.0 * (f_alpha ** 2)) - (f_alpha ** 2))
        rv_alpha = max(0.0, min(1.0, float(rv_alpha)))
    else:
        rv_alpha = 0.0
        
    return rv_q, rv_alpha


def estimate_causal_sensitivity_bias(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    covariate_cols: Optional[List[str]] = None,
    q_reduction: float = 1.0,
    alpha_level: float = 0.05,
    benchmark_covariates: Optional[List[str]] = None,
    benchmark_multipliers: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Executes Causal Sensitivity Analysis & Omitted Variable Bias Contours (Cinelli & Hazlett 2020).
    
    Args:
        df: Input survey DataFrame.
        outcome_col: Target continuous outcome variable Y.
        treatment_col: Treatment indicator or continuous exposure D.
        covariate_cols: Baseline observed controls X.
        q_reduction: Target reduction percentage (1.0 = reduce estimate completely to 0.0).
        alpha_level: Significance level (default 0.05 for 95% confidence).
        benchmark_covariates: Specific covariates to benchmark unobserved confounders against.
        benchmark_multipliers: Multipliers of covariate strength (default: [1.0, 2.0, 3.0]).
        
    Returns:
        Structured dictionary matching API contract.
    """
    if covariate_cols is None:
        covariate_cols = []
    if benchmark_multipliers is None:
        benchmark_multipliers = [1.0, 2.0, 3.0]
        
    req_cols = [outcome_col, treatment_col] + list(covariate_cols)
    for col in req_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")
            
    clean_df = df[req_cols].dropna().copy().reset_index(drop=True)
    n = len(clean_df)
    if n < 25:
        raise ValueError(f"Sample size too small for sensitivity analysis: N={n} (minimum 25 required).")
        
    y_vec = clean_df[outcome_col].values.astype(float)
    d_vec = clean_df[treatment_col].values.astype(float)
    
    if len(covariate_cols) > 0:
        X_mat = clean_df[covariate_cols].values.astype(float)
    else:
        X_mat = np.empty((n, 0))
        
    # 1. Baseline Primary OLS Regression
    tau_hat, se_tau, t_stat, r2_yd_x, df_error = _compute_partial_r2(y_vec, d_vec, X_mat)
    p_value = 2.0 * (1.0 - stats.t.cdf(abs(t_stat), df_error))
    
    # 2. Robustness Values
    rv_q, rv_alpha = _compute_robustness_value(t_stat, df_error, q=q_reduction, alpha=alpha_level)
    
    # 3. Covariate Benchmarks (if covariates present)
    benchmark_list = []
    benchmark_scenarios = []
    
    if len(covariate_cols) > 0:
        all_benchmarks = _compute_covariate_benchmarks(y_vec, d_vec, X_mat, covariate_cols)
        
        # Filter to requested benchmarks or top 3 highest partial R2
        if benchmark_covariates:
            selected_benchmarks = [b for b in all_benchmarks if b["covariate"] in benchmark_covariates]
        else:
            # Sort by max(r2_d, r2_y) descending, pick top 3
            sorted_b = sorted(all_benchmarks, key=lambda b: max(b["r2_d_given_x"], b["r2_y_given_dx"]), reverse=True)
            selected_benchmarks = sorted_b[:3]
            
        benchmark_list = all_benchmarks
        
        # Generate multiplier scenarios for each benchmark
        for b in selected_benchmarks:
            cov_name = b["covariate"]
            base_r2_d = b["r2_d_given_x"]
            base_r2_y = b["r2_y_given_dx"]
            
            for m in benchmark_multipliers:
                r2_dz = min(0.95, base_r2_d * m)
                r2_yz = min(0.95, base_r2_y * m)
                
                tau_adj, se_adj, t_adj = _compute_adjusted_estimate_and_se(
                    tau_hat, se_tau, df_error, r2_dz, r2_yz
                )
                
                # Check significance
                t_crit = stats.t.ppf(1.0 - alpha_level / 2.0, df_error - 1)
                is_still_sig = abs(t_adj) >= t_crit
                ci_adj = [round(tau_adj - t_crit * se_adj, 4), round(tau_adj + t_crit * se_adj, 4)]
                
                # Overturned if signs differ or CI includes 0
                is_overturned = (np.sign(tau_adj) != np.sign(tau_hat)) or not is_still_sig
                
                benchmark_scenarios.append({
                    "covariate": cov_name,
                    "multiplier": float(m),
                    "r2_dz_x": round(r2_dz, 4),
                    "r2_yz_dx": round(r2_yz, 4),
                    "adjusted_estimate": round(tau_adj, 4),
                    "adjusted_se": round(se_adj, 4),
                    "adjusted_t": round(t_adj, 4),
                    "adjusted_ci": ci_adj,
                    "remains_significant": bool(is_still_sig),
                    "is_overturned": bool(is_overturned)
                })

    # 4. Sensitivity Contour Grid for Visualization (40 x 40 points)
    grid_res = 35
    max_r2_axis = max(0.35, min(0.85, max(rv_q * 1.5, 0.30)))
    r2_grid = np.linspace(0.0, max_r2_axis, grid_res)
    
    contour_matrix = np.zeros((grid_res, grid_res))
    t_matrix = np.zeros((grid_res, grid_res))
    
    for r_i, r_d in enumerate(r2_grid):
        for c_j, r_y in enumerate(r2_grid):
            adj_tau, adj_se, adj_t = _compute_adjusted_estimate_and_se(
                tau_hat, se_tau, df_error, float(r_d), float(r_y)
            )
            contour_matrix[r_i, c_j] = adj_tau
            t_matrix[r_i, c_j] = adj_t
            
    # 5. Extreme Confounder Scenarios
    # Scenario: Confounder explains 100% of residual outcome variance (r2_yz_dx = 1.0)
    # What r2_dz_x is needed to reduce estimate to 0?
    # f^2 = (t^2 / df) = (r2_dz / (1 - r2_dz)) => r2_dz = t^2 / (t^2 + df) = r2_yd_x!
    r2_dz_extreme_to_zero = float(r2_yd_x)
    
    # 6. Overall Summary
    t_crit = stats.t.ppf(1.0 - alpha_level / 2.0, df_error)
    baseline_ci = [round(tau_hat - t_crit * se_tau, 4), round(tau_hat + t_crit * se_tau, 4)]
    
    overall_summary = {
        "sample_size": n,
        "residual_df": df_error,
        "baseline_estimate": round(tau_hat, 4),
        "baseline_se": round(se_tau, 4),
        "baseline_t": round(t_stat, 4),
        "baseline_p_value": round(float(p_value), 5),
        "baseline_ci": baseline_ci,
        "partial_r2_treatment": round(float(r2_yd_x), 4),
        "robustness_value_q": round(rv_q, 4),
        "robustness_value_alpha": round(rv_alpha, 4),
        "target_reduction_q": round(q_reduction, 2),
        "significance_alpha": round(alpha_level, 3),
        "extreme_r2_dz_needed_to_zero": round(r2_dz_extreme_to_zero, 4)
    }
    
    # 7. Generate Scientific SVG Contour Chart
    svg_chart = _generate_sensitivity_contour_svg(
        overall_summary=overall_summary,
        benchmark_scenarios=benchmark_scenarios,
        r2_grid=r2_grid,
        contour_matrix=contour_matrix,
        max_r2=max_r2_axis
    )
    
    # 8. APA 7th Narrative
    cov_str = ", ".join(covariate_cols[:3]) + ("..." if len(covariate_cols) > 3 else "") if covariate_cols else "None"
    apa_narrative = (
        f"A formal Causal Sensitivity Analysis for Omitted Variable Bias (Cinelli & Hazlett, 2020) was conducted "
        f"on the relationship between '{treatment_col}' and '{outcome_col}' (N = {n}, df = {df_error}, covariates: [{cov_str}]). "
        f"The baseline estimated treatment effect is tau = {tau_hat:.4f} (SE = {se_tau:.4f}, t = {t_stat:.2f}, p = {p_value:.4f}, "
        f"95% CI [{baseline_ci[0]:.4f}, {baseline_ci[1]:.4f}]), explaining a partial R^2 of {r2_yd_x * 100:.2f}% of residual outcome variance. "
        f"The Robustness Value for point identification was RV_(q={q_reduction:.1f}) = {rv_q * 100:.1f}%, indicating that unobserved confounding "
        f"would need to explain at least {rv_q * 100:.1f}% of residual variance in both treatment assignment and outcome to reduce the causal estimate to zero. "
        f"Furthermore, the Robustness Value for statistical significance at alpha = {alpha_level} was RV_alpha = {rv_alpha * 100:.1f}%. "
        f"Under an extreme scenario where an unobserved confounder explains 100% of outcome residual variance, it would still need to explain "
        f"{r2_dz_extreme_to_zero * 100:.2f}% of treatment variance to nullify the effect."
    )
    
    return {
        "status": "SUCCESS",
        "overall_summary": overall_summary,
        "covariate_benchmarks": benchmark_list,
        "benchmark_scenarios": benchmark_scenarios,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_sensitivity_contour_svg(
    overall_summary: Dict[str, Any],
    benchmark_scenarios: List[Dict[str, Any]],
    r2_grid: np.ndarray,
    contour_matrix: np.ndarray,
    max_r2: float
) -> str:
    """
    Constructs a dual-panel SVG visualizer:
    Panel 1: Sensitivity Contour Map (R^2_{Y~Z|D,X} vs R^2_{D~Z|X}) with Critical Zero-Curve & Benchmark Points.
    Panel 2: Robustness Metrics & Covariate Multiplier Survival Table.
    """
    svg_w, svg_h = 780, 360
    
    # Panel 1: Contour Plot (x: 40 to 390, y: 65 to 300)
    p1_x, p1_y, p1_w, p1_h = 50, 70, 340, 230
    
    tau_base = overall_summary.get("baseline_estimate", 1.0)
    rv_q = overall_summary.get("robustness_value_q", 0.15)
    rv_alpha = overall_summary.get("robustness_value_alpha", 0.10)
    
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#0f172a" rx="10" />',
        f'  <text x="30" y="32" font-size="14" font-weight="700" fill="#f8fafc">Causal Sensitivity &amp; Omitted Variable Bias (Cinelli &amp; Hazlett 2020)</text>',
        f'  <text x="30" y="48" font-size="11" fill="#94a3b8">Robustness Value RV_q: {(rv_q * 100):.1f}% · RV_α: {(rv_alpha * 100):.1f}% · Baseline Effect: {tau_base:.3f}</text>',
        
        # Panel 1 Border
        f'  <rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" fill="#1e293b" rx="6" />',
        f'  <text x="{p1_x + 10}" y="{p1_y + 18}" font-size="11" font-weight="600" fill="#38bdf8">Sensitivity Contour (Adjusted Estimate τ)</text>',
        
        # Axis labels
        f'  <text x="{p1_x + p1_w / 2}" y="{p1_y + p1_h + 20}" font-size="10" fill="#94a3b8" text-anchor="middle">Hypothetical Partial R² with Treatment: R²(D ~ Z | X)</text>',
        f'  <text x="{p1_x - 12}" y="{p1_y + p1_h / 2}" font-size="10" fill="#94a3b8" text-anchor="middle" transform="rotate(-90 {p1_x - 12} {p1_y + p1_h / 2})">R²(Y ~ Z | D, X)</text>'
    ]
    
    # Coordinate mapper
    def map_coords(r_d: float, r_y: float) -> Tuple[float, float]:
        cx = p1_x + (min(r_d, max_r2) / max_r2) * p1_w
        cy = (p1_y + p1_h) - (min(r_y, max_r2) / max_r2) * p1_h
        return cx, cy
        
    # Draw contour lines for 75%, 50%, 25%, 0% of baseline effect
    percentages = [0.75, 0.50, 0.25, 0.0]
    colors = ["#38bdf8", "#818cf8", "#f59e0b", "#ef4444"]
    
    for pct, col in zip(percentages, colors):
        # Curve where adjusted estimate reaches pct * tau_base
        pts = []
        d_vals = np.linspace(0.005, max_r2 * 0.95, 30)
        for d_v in d_vals:
            # bias needed = (1 - pct) * |tau_base|
            # bias = se * sqrt(df) * sqrt( (ry * rd) / (1 - rd) )
            se = overall_summary.get("baseline_se", 0.1)
            df_err = overall_summary.get("residual_df", 30)
            target_bias = (1.0 - pct) * abs(tau_base)
            
            denom = (se * math.sqrt(df_err)) ** 2
            if denom > 1e-12:
                ry_needed = (target_bias ** 2 / denom) * ((1.0 - d_v) / d_v)
                if 0.0 <= ry_needed <= max_r2:
                    cx, cy = map_coords(d_v, ry_needed)
                    pts.append(f"{cx:.1f},{cy:.1f}")
                    
        if len(pts) > 1:
            poly_str = " ".join(pts)
            dash = ' stroke-dasharray="3 3"' if pct == 0.0 else ''
            lines.append(f'  <polyline points="{poly_str}" fill="none" stroke="{col}" stroke-width="{2 if pct==0.0 else 1.5}"{dash} />')
            first_x, first_y = [float(c) for c in pts[-1].split(",")]
            lbl = f"{(pct * 100):.0f}%" if pct > 0 else "Null (0)"
            lines.append(f'  <text x="{first_x + 3:.1f}" y="{first_y + 3:.1f}" font-size="8" font-weight="700" fill="{col}">{lbl}</text>')

    # Plot RV_q intersection point (rv_q, rv_q)
    rv_cx, rv_cy = map_coords(rv_q, rv_q)
    lines.append(f'  <circle cx="{rv_cx:.1f}" cy="{rv_cy:.1f}" r="5" fill="#ef4444" stroke="#ffffff" stroke-width="1.5" />')
    lines.append(f'  <text x="{rv_cx + 8:.1f}" y="{rv_cy + 4:.1f}" font-size="9" font-weight="700" fill="#ef4444">RV={rv_q*100:.1f}%</text>')

    # Plot Benchmark Covariates on Contour Map
    benchmark_points = benchmark_scenarios[:4]
    bm_cols = ["#10b981", "#06b6d4", "#a855f7", "#ec4899"]
    
    for idx_bm, bm in enumerate(benchmark_points):
        bm_cx, bm_cy = map_coords(bm["r2_dz_x"], bm["r2_yz_dx"])
        bm_col = bm_cols[idx_bm % len(bm_cols)]
        lines.append(f'  <circle cx="{bm_cx:.1f}" cy="{bm_cy:.1f}" r="4" fill="{bm_col}" stroke="#0f172a" stroke-width="1" />')
        lines.append(f'  <text x="{bm_cx + 6:.1f}" y="{bm_cy + 3:.1f}" font-size="8" font-weight="600" fill="{bm_col}">{bm["covariate"][:8]} ({bm["multiplier"]:.0f}x)</text>')

    # Panel 2: Benchmark Survival Table & Diagnostics (x: 430 to 740, y: 70 to 300)
    p2_x, p2_y, p2_w, p2_h = 430, 70, 320, 230
    lines.append(f'  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#1e293b" rx="6" />')
    lines.append(f'  <text x="{p2_x + 12}" y="{p2_y + 18}" font-size="11" font-weight="600" fill="#a78bfa">Benchmark Covariate Sensitivity Scenarios</text>')
    
    row_y = p2_y + 40
    lines.append(f'  <text x="{p2_x + 12}" y="{row_y}" font-size="9" font-weight="700" fill="#64748b">Covariate</text>')
    lines.append(f'  <text x="{p2_x + 95}" y="{row_y}" font-size="9" font-weight="700" fill="#64748b">Mult</text>')
    lines.append(f'  <text x="{p2_x + 135}" y="{row_y}" font-size="9" font-weight="700" fill="#64748b">Adj τ</text>')
    lines.append(f'  <text x="{p2_x + 195}" y="{row_y}" font-size="9" font-weight="700" fill="#64748b">Adj t</text>')
    lines.append(f'  <text x="{p2_x + 245}" y="{row_y}" font-size="9" font-weight="700" fill="#64748b">Verdict</text>')
    
    scenarios_to_show = benchmark_scenarios[:6]
    for k, sc in enumerate(scenarios_to_show):
        cur_row = row_y + 18 + k * 24
        is_sig = sc.get("remains_significant", True)
        is_ot = sc.get("is_overturned", False)
        
        v_col = "#ef4444" if is_ot else "#10b981"
        v_text = "OVERTURNED" if is_ot else "ROBUST"
        
        cov_disp = sc.get("covariate", "Cov")[:11]
        lines.append(f'  <text x="{p2_x + 12}" y="{cur_row}" font-size="9" fill="#f1f5f9">{cov_disp}</text>')
        lines.append(f'  <text x="{p2_x + 95}" y="{cur_row}" font-size="9" font-mono fill="#94a3b8">{sc.get("multiplier", 1):.0f}x</text>')
        lines.append(f'  <text x="{p2_x + 135}" y="{cur_row}" font-size="9" font-mono font-weight="600" fill="#f8fafc">{sc.get("adjusted_estimate", 0):.2f}</text>')
        lines.append(f'  <text x="{p2_x + 195}" y="{cur_row}" font-size="9" font-mono fill="#94a3b8">{sc.get("adjusted_t", 0):.2f}</text>')
        lines.append(f'  <rect x="{p2_x + 242}" y="{cur_row - 9}" width="65" height="13" fill="{v_col}22" rx="2" />')
        lines.append(f'  <text x="{p2_x + 274}" y="{cur_row}" font-size="8" font-weight="700" fill="{v_col}" text-anchor="middle">{v_text}</text>')

    lines.append('</svg>')
    return "\n".join(lines)
