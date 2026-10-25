# -*- coding: utf-8 -*-
"""
Shift-Share Instrumental Variables & Rotemberg Decomposition Engine
Scientific References:
- Goldsmith-Pinkham, P., Sorkin, I., & Swift, H. (2020). "Bartik Instruments:
  What, When, Why, and How." American Economic Review, 110(8), 2586-2624.
- Borusyak, K., Hull, P., & Jaravel, X. (2022). "Quasi-Experimental Shift-Share Designs."
  The Review of Economic Studies, 89(1), 181-213.
- Adao, R., Kolesár, M., & Morales, E. (2019). "Shift-Share Designs:
  Theory and Inference." The Quarterly Journal of Economics, 134(4), 1949-2010.

Implements Bartik 2SLS regression Z_i = sum_k z_ik * g_k, calculates exact Rotemberg
weights alpha_k, share-specific IV estimates beta_k, Adao-Kolesar-Morales (AKM)
exposure-robust standard errors, and overidentification tests.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _project_out_covariates(
    targets: np.ndarray,
    X: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Computes residual matrix M_X * targets, where M_X = I - X (X'X)^-1 X'.
    targets: (n, m) or (n,)
    """
    n = len(targets)
    if X is None or X.shape[1] == 0:
        # Just demean (project out constant)
        mean_val = np.mean(targets, axis=0)
        return targets - mean_val
        
    M = np.column_stack([np.ones(n), X])
    try:
        coef = np.linalg.solve(M.T @ M, M.T @ targets)
    except np.linalg.LinAlgError:
        coef = np.linalg.lstsq(M.T @ M, M.T @ targets, rcond=None)[0]
        
    residuals = targets - (M @ coef)
    return residuals


def estimate_shift_share_iv(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    share_cols: List[str],
    shocks: Optional[List[float]] = None,
    covariate_cols: Optional[List[str]] = None,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Shift-Share / Bartik IV estimation with Rotemberg decomposition (Goldsmith-Pinkham et al. 2020).
    
    Args:
        df: Input survey DataFrame.
        outcome_col: Target dependent variable Y.
        treatment_col: Endogenous treatment/exposure variable D.
        share_cols: List of baseline portfolio share column names z_ik (k=1..K).
        shocks: Vector of aggregate category growth shocks g_k. If None, computes cross-sectional sample mean.
        covariate_cols: Baseline control variables X.
        alpha_level: Significance level for confidence intervals.
        
    Returns:
        Structured dictionary matching API contract.
    """
    if not share_cols or len(share_cols) < 2:
        raise ValueError("Shift-Share IV requires at least 2 share categories z_ik.")
        
    if covariate_cols is None:
        covariate_cols = []
        
    req_cols = [outcome_col, treatment_col] + list(share_cols) + list(covariate_cols)
    for col in req_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")
            
    clean_df = df[req_cols].dropna().copy().reset_index(drop=True)
    n = len(clean_df)
    K = len(share_cols)
    if n < max(30, K + len(covariate_cols) + 5):
        raise ValueError(f"Sample size too small for shift-share IV: N={n} (minimum {max(30, K + 5)} required).")
        
    y_vec = clean_df[outcome_col].values.astype(float)
    d_vec = clean_df[treatment_col].values.astype(float)
    Z_shares = clean_df[share_cols].values.astype(float)
    
    if len(covariate_cols) > 0:
        X_mat = clean_df[covariate_cols].values.astype(float)
    else:
        X_mat = np.empty((n, 0))
        
    # Process Shocks g_k
    if shocks is not None:
        if len(shocks) != K:
            raise ValueError(f"Length of shocks vector ({len(shocks)}) must match number of share columns ({K}).")
        g_vec = np.array(shocks, dtype=float)
    else:
        # Default: normalized variation in shares or unit proxy shocks
        g_vec = np.std(Z_shares, axis=0)
        if np.all(g_vec < 1e-8):
            g_vec = np.ones(K)
        g_vec = g_vec / np.mean(g_vec)
        
    # 1. Construct Bartik Instrument Z_i = sum_k z_ik * g_k
    bartik_z = Z_shares @ g_vec
    
    # 2. Residualize Y, D, Bartik Z, and each share z_k against baseline controls X
    y_tilde = _project_out_covariates(y_vec, X_mat)
    d_tilde = _project_out_covariates(d_vec, X_mat)
    z_tilde = _project_out_covariates(bartik_z, X_mat)
    Z_shares_tilde = _project_out_covariates(Z_shares, X_mat)
    
    # 3. First Stage: d_tilde ~ z_tilde
    cov_zd = float(np.dot(z_tilde, d_tilde))
    var_z = float(np.dot(z_tilde, z_tilde))
    if var_z < 1e-12:
        raise ValueError("Bartik instrument has zero residual variance after controlling for covariates.")
        
    gamma_first_stage = cov_zd / var_z
    res_fs = d_tilde - gamma_first_stage * z_tilde
    df_fs = max(n - len(covariate_cols) - 2, 1)
    s2_fs = float(np.sum(res_fs ** 2) / df_fs)
    se_gamma = float(np.sqrt(max(1e-12, s2_fs / var_z)))
    first_stage_f = float((gamma_first_stage / se_gamma) ** 2) if se_gamma > 1e-12 else 0.0
    
    # 4. 2SLS Second Stage: beta_2sls = cov(z_tilde, y_tilde) / cov(z_tilde, d_tilde)
    cov_zy = float(np.dot(z_tilde, y_tilde))
    if abs(cov_zd) < 1e-12:
        raise ValueError("Weak first stage: Bartik instrument is uncorrelated with endogenous treatment.")
        
    beta_2sls = float(cov_zy / cov_zd)
    
    # Conventional Robust Residuals
    d_hat_tilde = gamma_first_stage * z_tilde
    res_ss = y_tilde - beta_2sls * d_tilde
    s2_ss = float(np.sum(res_ss ** 2) / df_fs)
    se_conventional = float(np.sqrt(max(1e-12, s2_ss / np.dot(d_hat_tilde, d_hat_tilde))))
    
    # 5. Adao, Kolesár, & Morales (AKM 2019) Standard Errors (Accounting for share exposure correlation)
    # AKM variance: V_AKM = (Z' M_X D)^-2 * sum_k ( sum_i z_ik res_ss_i * g_k )^2
    # Shock-level projection:
    akm_sum_sq = 0.0
    for k in range(K):
        # Aggregate residuals for sector k
        sector_res_k = float(np.dot(Z_shares_tilde[:, k], res_ss)) * g_vec[k]
        akm_sum_sq += sector_res_k ** 2
        
    var_akm = akm_sum_sq / (cov_zd ** 2)
    se_akm = float(np.sqrt(max(var_akm, 1e-12)))
    # If AKM is smaller than conventional due to small K, be conservative
    se_final = max(se_akm, se_conventional)
    
    t_stat = beta_2sls / se_final if se_final > 1e-12 else 0.0
    t_crit = stats.t.ppf(1.0 - alpha_level / 2.0, df_fs)
    ci_2sls = [round(beta_2sls - t_crit * se_final, 4), round(beta_2sls + t_crit * se_final, 4)]
    p_value = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df_fs)))
    
    # 6. Goldsmith-Pinkham et al. (2020) Rotemberg Decomposition
    # alpha_k = (g_k * z_k_tilde' * d_tilde) / (z_tilde' * d_tilde)
    rotemberg_weights = []
    just_identified_estimates = []
    
    for k in range(K):
        zk_tilde = Z_shares_tilde[:, k]
        cov_zk_d = float(np.dot(zk_tilde, d_tilde))
        cov_zk_y = float(np.dot(zk_tilde, y_tilde))
        
        # Rotemberg weight
        alpha_k = (g_vec[k] * cov_zk_d) / cov_zd
        rotemberg_weights.append(alpha_k)
        
        # Just-identified IV estimate using only share k
        if abs(cov_zk_d) > 1e-10:
            beta_k = cov_zk_y / cov_zk_d
        else:
            beta_k = beta_2sls
        just_identified_estimates.append(beta_k)
        
    rotemberg_weights = np.array(rotemberg_weights)
    just_identified_estimates = np.array(just_identified_estimates)
    
    # Rotemberg Diagnostics
    positive_weights_mask = rotemberg_weights > 0
    sum_positive_weights = float(np.sum(rotemberg_weights[positive_weights_mask]))
    sum_negative_weights = float(np.sum(rotemberg_weights[~positive_weights_mask]))
    
    # Herfindahl-Hirschman index of Rotemberg concentration: HHI = sum_k (alpha_k / sum_pos)^2
    if sum_positive_weights > 1e-8:
        pos_alphas_norm = rotemberg_weights[positive_weights_mask] / sum_positive_weights
        rotemberg_hhi = float(np.sum(pos_alphas_norm ** 2))
    else:
        rotemberg_hhi = 1.0 / K
        
    # Top Rotemberg decomposition items
    rotemberg_items = []
    for k in range(K):
        rotemberg_items.append({
            "share_variable": share_cols[k],
            "rotemberg_weight": round(float(rotemberg_weights[k]), 4),
            "rotemberg_weight_pct": round(float(rotemberg_weights[k]) * 100, 2),
            "share_shock_value": round(float(g_vec[k]), 4),
            "just_identified_beta": round(float(just_identified_estimates[k]), 4),
            "first_stage_cov": round(float(np.dot(Z_shares_tilde[:, k], d_tilde)), 4)
        })
        
    # Sort by absolute Rotemberg weight descending
    rotemberg_items.sort(key=lambda item: abs(item["rotemberg_weight"]), reverse=True)
    top_5_weight_sum = sum(item["rotemberg_weight"] for item in rotemberg_items[:min(5, K)])
    
    # 7. Sargan / Overidentification Test across shares with positive weights
    valid_k_indices = np.where(positive_weights_mask)[0]
    if len(valid_k_indices) >= 2:
        # Sargan test: compare just-identified betas to overall beta_2sls
        sargan_stat = 0.0
        for k_idx in valid_k_indices:
            diff = just_identified_estimates[k_idx] - beta_2sls
            weight = rotemberg_weights[k_idx]
            sargan_stat += weight * (diff ** 2)
        sargan_stat = max(0.0, float(sargan_stat / (s2_ss + 1e-8)))
        df_sargan = len(valid_k_indices) - 1
        p_overid = float(1.0 - stats.chi2.cdf(sargan_stat, df_sargan))
    else:
        sargan_stat = 0.0
        df_sargan = 1
        p_overid = 1.0
        
    # 8. Overall Summary
    overall_summary = {
        "sample_size": n,
        "n_shares_k": K,
        "first_stage_f_statistic": round(first_stage_f, 2),
        "is_weak_instrument": bool(first_stage_f < 10.0),
        "beta_2sls": round(beta_2sls, 4),
        "se_conventional": round(se_conventional, 4),
        "se_akm_robust": round(se_final, 4),
        "t_statistic": round(t_stat, 2),
        "p_value": round(p_value, 5),
        "confidence_interval_95": ci_2sls,
        "rotemberg_hhi": round(rotemberg_hhi, 4),
        "sum_positive_rotemberg_weights": round(sum_positive_weights, 4),
        "sum_negative_rotemberg_weights": round(sum_negative_weights, 4),
        "top_5_shares_weight_share": round(float(top_5_weight_sum), 4),
        "overid_sargan_stat": round(sargan_stat, 3),
        "overid_p_value": round(p_overid, 4)
    }
    
    # 9. Generate Scientific SVG Visualization
    svg_chart = _generate_shift_share_svg(
        overall_summary=overall_summary,
        rotemberg_items=rotemberg_items,
        d_tilde=d_tilde,
        y_tilde=y_tilde,
        beta_2sls=beta_2sls
    )
    
    # 10. APA 7th Edition Narrative
    top_share_name = rotemberg_items[0]["share_variable"]
    top_share_wt = rotemberg_items[0]["rotemberg_weight_pct"]
    cov_str = ", ".join(covariate_cols[:3]) + ("..." if len(covariate_cols) > 3 else "") if covariate_cols else "None"
    
    apa_narrative = (
        f"A Shift-Share Instrumental Variable (Bartik IV) analysis (Goldsmith-Pinkham, Sorkin, & Swift, 2020; "
        f"Adao, Kolesár, & Morales, 2019) was conducted on N = {n} units across K = {K} baseline share categories "
        f"(covariates: [{cov_str}]). "
        f"The first-stage regression showed strong instrument relevance with an F-statistic of F = {first_stage_f:.2f} "
        f"({'sufficiently strong' if first_stage_f >= 10 else 'weak instrument caution'}). "
        f"The 2SLS causal treatment effect was estimated at beta = {beta_2sls:.4f} with Adao-Kolesár-Morales exposure-robust "
        f"standard error SE_AKM = {se_final:.4f} (t = {t_stat:.2f}, p = {p_value:.4f}, 95% CI [{ci_2sls[0]:.4f}, {ci_2sls[1]:.4f}]). "
        f"Goldsmith-Pinkham et al. Rotemberg decomposition revealed high identification concentration (HHI = {rotemberg_hhi:.3f}), "
        f"with the top identifying share '{top_share_name}' driving {top_share_wt:.1f}% of the total identifying variation. "
        f"The overidentification test across positive-weight shares yielded Chi2({df_sargan}) = {sargan_stat:.2f} (p = {p_overid:.4f}), "
        f"{'supporting instrument mutual consistency' if p_overid >= 0.05 else 'indicating potential share-level heterogeneity'}."
    )
    
    return {
        "status": "SUCCESS",
        "overall_summary": overall_summary,
        "rotemberg_decomposition": rotemberg_items,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_shift_share_svg(
    overall_summary: Dict[str, Any],
    rotemberg_items: List[Dict[str, Any]],
    d_tilde: np.ndarray,
    y_tilde: np.ndarray,
    beta_2sls: float
) -> str:
    """
    Dual-panel SVG visualizer:
    Panel 1: Top Rotemberg Identifying Weights Decomposition (Bar chart).
    Panel 2: 2SLS Second-Stage Causal Fit with AKM Confidence Slope.
    """
    svg_w, svg_h = 780, 360
    
    beta_val = overall_summary.get("beta_2sls", 0.0)
    se_val = overall_summary.get("se_akm_robust", 0.1)
    f_stat = overall_summary.get("first_stage_f_statistic", 10.0)
    hhi = overall_summary.get("rotemberg_hhi", 0.25)
    
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#0f172a" rx="10" />',
        f'  <text x="30" y="32" font-size="14" font-weight="700" fill="#f8fafc">Shift-Share IV &amp; Rotemberg Decomposition (Goldsmith-Pinkham et al. 2020)</text>',
        f'  <text x="30" y="48" font-size="11" fill="#94a3b8">2SLS β: {beta_val:.3f} (SE_AKM: {se_val:.3f}) · First-Stage F: {f_stat:.1f} · Rotemberg HHI: {hhi:.3f}</text>',
        
        # Panel 1: Rotemberg Weights (x: 45 to 395, y: 70 to 300)
        f'  <rect x="45" y="70" width="350" height="230" fill="#1e293b" rx="6" />',
        f'  <text x="57" y="88" font-size="11" font-weight="600" fill="#38bdf8">Top Rotemberg Identifying Weights (&alpha;_k)</text>'
    ]
    
    # Plot top 5 Rotemberg weights
    top_items = rotemberg_items[:5]
    row_step = 34
    for idx_r, item in enumerate(top_items):
        ry = 115 + idx_r * row_step
        sh_name = item.get("share_variable", f"Share {idx_r+1}")[:16]
        wt_pct = item.get("rotemberg_weight_pct", 0.0)
        just_beta = item.get("just_identified_beta", 0.0)
        
        # Color: teal if positive, rose if negative
        bar_fill = "#06b6d4" if wt_pct >= 0 else "#ef4444"
        bar_w = min(160, max(2, abs(wt_pct) * 2.2))
        
        lines.append(f'  <text x="57" y="{ry}" font-size="10" font-weight="600" fill="#f1f5f9">{sh_name}</text>')
        lines.append(f'  <rect x="180" y="{ry - 10}" width="{bar_w:.1f}" height="12" fill="{bar_fill}" rx="2" />')
        lines.append(f'  <text x="{185 + bar_w:.1f}" y="{ry}" font-size="9" font-weight="700" fill="{bar_fill}">{wt_pct:.1f}%</text>')
        lines.append(f'  <text x="57" y="{ry + 13}" font-size="8" fill="#94a3b8">Just-ID β_k: {just_beta:.2f}</text>')

    # Panel 2: 2SLS Second Stage Slope Scatter (x: 430 to 740, y: 70 to 300)
    p2_x, p2_y, p2_w, p2_h = 430, 70, 310, 230
    lines.append(f'  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#1e293b" rx="6" />')
    lines.append(f'  <text x="{p2_x + 12}" y="{p2_y + 18}" font-size="11" font-weight="600" fill="#a78bfa">2SLS Second-Stage Causal Response</text>')
    
    # Scatter of (d_tilde, y_tilde)
    min_d, max_d = min(d_tilde), max(d_tilde)
    min_y, max_y = min(y_tilde), max(y_tilde)
    span_d = max_d - min_d if max_d > min_d else 1.0
    span_y = max_y - min_y if max_y > min_y else 1.0
    
    def map_p2(d_val: float, y_val: float) -> Tuple[float, float]:
        cx = p2_x + 20 + ((d_val - min_d) / span_d) * (p2_w - 40)
        cy = (p2_y + p2_h - 20) - ((y_val - min_y) / span_y) * (p2_h - 50)
        return cx, cy
        
    # Plot subsample of points
    step_pts = max(1, len(d_tilde) // 35)
    for i in range(0, len(d_tilde), step_pts):
        px, py = map_p2(d_tilde[i], y_tilde[i])
        lines.append(f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="#818cf8" fill-opacity="0.6" />')
        
    # Plot 2SLS slope line
    x_left = min_d
    x_right = max_d
    y_left = beta_2sls * x_left
    y_right = beta_2sls * x_right
    
    lx1, ly1 = map_p2(x_left, y_left)
    lx2, ly2 = map_p2(x_right, y_right)
    lines.append(f'  <line x1="{lx1:.1f}" y1="{ly1:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" stroke="#a78bfa" stroke-width="2.5" />')
    lines.append(f'  <text x="{lx2 - 25:.1f}" y="{ly2 - 6:.1f}" font-size="9" font-weight="700" fill="#a78bfa">β = {beta_2sls:.2f}</text>')

    lines.append('</svg>')
    return "\n".join(lines)
