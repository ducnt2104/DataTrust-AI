# -*- coding: utf-8 -*-
"""
Quantile Synthetic Control & Distributional Counterfactuals Engine
Scientific References:
- Gunsilius, F. F. (2023). "A Path-Based Approach to Distributional Synthetic Controls."
  Econometrica, 91(4), 1369-1406.
- Chernozhukov, V., Kasahara, H., & Schrimpf, P. (2020). "Causal Impact of Masks, Policies,
  and Behavior on Early COVID-19 Pandemic in the U.S." Journal of Econometrics, 220(1), 23-62.
- Abadie, A., Diamond, A., & Hainmueller, J. (2010). "Synthetic Control Methods for
  Comparative Case Studies." Journal of the American Statistical Association, 105(490), 493-505.

Extends synthetic control methods from scalar mean matching to the full empirical quantile
process and distribution via Wasserstein metric minimization. Estimates post-intervention
Quantile Treatment Effects (QTE) tau(u), counterfactual CDFs, and Gini inequality shifts.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats, optimize


def _compute_gini_coefficient(y_sample: np.ndarray) -> float:
    """
    Computes exact Gini inequality coefficient for a sample of non-negative values.
    """
    y = np.sort(np.asarray(y_sample, dtype=float))
    # Shift if negative values exist
    min_val = np.min(y)
    if min_val < 0:
        y = y - min_val
    n = len(y)
    if n == 0 or np.sum(y) == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return float((2.0 * np.sum(index * y) - (n + 1) * np.sum(y)) / (n * np.sum(y)))


def _fit_quantile_synthetic_weights(
    Q_treated_pre: np.ndarray,
    Q_donors_pre: np.ndarray,
    reg_lambda: float = 1e-3
) -> np.ndarray:
    """
    Minimizes pre-intervention Wasserstein distance between treated quantile matrix
    and synthetic combination of donor quantile matrices.
    Q_treated_pre: (T_pre * n_quantiles,)
    Q_donors_pre: (T_pre * n_quantiles, J_donors)
    Constraints: w >= 0, sum(w) = 1.
    """
    J = Q_donors_pre.shape[1]
    
    # Quadratic programming objective: 0.5 * w' (D'D + reg*I) w - w' (D' y)
    DtD = Q_donors_pre.T @ Q_donors_pre + reg_lambda * np.eye(J)
    Dty = Q_donors_pre.T @ Q_treated_pre
    
    def loss(w):
        return 0.5 * w.T @ DtD @ w - w.T @ Dty
        
    def jac(w):
        return DtD @ w - Dty
        
    bounds = [(0.0, 1.0) for _ in range(J)]
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
    w0 = np.ones(J) / J
    
    res = optimize.minimize(
        loss,
        w0,
        jac=jac,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 300, 'ftol': 1e-9}
    )
    
    weights = res.x
    weights[weights < 1e-4] = 0.0
    if np.sum(weights) > 0:
        weights = weights / np.sum(weights)
    else:
        weights = w0
    return weights


def estimate_quantile_synthetic_control(
    df: pd.DataFrame,
    outcome_col: str,
    unit_col: str,
    time_col: str,
    treated_unit_id: Any,
    treatment_time: Any,
    quantiles: Optional[List[float]] = None,
    regularization_lambda: float = 1e-3,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Quantile Synthetic Control and Distributional Counterfactual Estimation (Gunsilius 2023).
    
    Args:
        df: Input panel/longitudinal survey DataFrame.
        outcome_col: Numerical outcome variable Y.
        unit_col: Unit identifier column (e.g. branch, state, department).
        time_col: Time period / wave indicator.
        treated_unit_id: ID of the treated unit.
        treatment_time: Time threshold marking start of treatment (post if time >= treatment_time).
        quantiles: List of quantiles u in (0, 1) to evaluate.
        regularization_lambda: L2 penalty parameter for donor weights.
        alpha_level: Significance level.
        
    Returns:
        Structured dictionary matching API contract.
    """
    if quantiles is None:
        quantiles = [0.10, 0.25, 0.50, 0.75, 0.90]
    quantiles = sorted(list(set(quantiles)))
    
    req_cols = [outcome_col, unit_col, time_col]
    for col in req_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")
            
    clean_df = df[req_cols].dropna().copy()
    clean_df[unit_col] = clean_df[unit_col].astype(str)
    
    treated_id_str = str(treated_unit_id)
    unique_units = clean_df[unit_col].unique()
    if treated_id_str not in unique_units:
        raise ValueError(f"Treated unit '{treated_unit_id}' not found in unit column.")
        
    donor_units = [u for u in unique_units if u != treated_id_str]
    J = len(donor_units)
    if J < 2:
        raise ValueError(f"Insufficient donor units for synthetic control: J={J} (minimum 2 required).")
        
    unique_times = sorted(clean_df[time_col].unique())
    pre_times = [t for t in unique_times if t < treatment_time]
    post_times = [t for t in unique_times if t >= treatment_time]
    
    if len(pre_times) < 1:
        raise ValueError("At least 1 pre-treatment time period is required.")
    if len(post_times) < 1:
        raise ValueError("At least 1 post-treatment time period is required.")
        
    n_q = len(quantiles)
    
    # 1. Compute empirical quantiles Q(u) for each unit and time period
    # Map: (unit, time) -> array of length n_q
    q_dict = {}
    for (u_val, t_val), group in clean_df.groupby([unit_col, time_col]):
        vals = group[outcome_col].values.astype(float)
        if len(vals) > 0:
            q_dict[(u_val, t_val)] = np.percentile(vals, [q * 100 for q in quantiles])
        else:
            q_dict[(u_val, t_val)] = np.zeros(n_q)
            
    # Check if treated unit has pre and post observations
    for t_val in pre_times + post_times:
        if (treated_id_str, t_val) not in q_dict:
            raise ValueError(f"Treated unit has missing observations at time wave '{t_val}'.")
            
    # 2. Build Pre-treatment Quantile Matrices
    # Treated pre-vector: length T_pre * n_q
    y_pre_blocks = []
    for t_val in pre_times:
        y_pre_blocks.append(q_dict[(treated_id_str, t_val)])
    Q_treated_pre = np.concatenate(y_pre_blocks)
    
    # Donors pre-matrix: (T_pre * n_q, J)
    D_pre_cols = []
    valid_donors = []
    for d_u in donor_units:
        # Check if donor has all pre-times
        has_all_pre = all((d_u, t_val) in q_dict for t_val in pre_times)
        has_all_post = all((d_u, t_val) in q_dict for t_val in post_times)
        if has_all_pre and has_all_post:
            d_blocks = []
            for t_val in pre_times:
                d_blocks.append(q_dict[(d_u, t_val)])
            D_pre_cols.append(np.concatenate(d_blocks))
            valid_donors.append(d_u)
            
    if len(valid_donors) < 2:
        raise ValueError(f"Insufficient donors with complete panel records: {len(valid_donors)} valid donors.")
        
    Q_donors_pre = np.column_stack(D_pre_cols)
    J_valid = len(valid_donors)
    
    # 3. Fit Synthetic Quantile Weights via Wasserstein minimization
    donor_weights = _fit_quantile_synthetic_weights(
        Q_treated_pre, Q_donors_pre, reg_lambda=regularization_lambda
    )
    
    # Pre-treatment Wasserstein distance
    synth_pre_q = Q_donors_pre @ donor_weights
    pre_wasserstein_dist = float(np.sqrt(np.mean((Q_treated_pre - synth_pre_q) ** 2)))
    
    # 4. Post-treatment Counterfactual Quantiles & Quantile Treatment Effects (QTE)
    # Average across post-treatment periods
    treated_post_vals = clean_df[(clean_df[unit_col] == treated_id_str) & (clean_df[time_col].isin(post_times))][outcome_col].values.astype(float)
    
    # Treated observed post quantiles
    q_treated_post = np.percentile(treated_post_vals, [q * 100 for q in quantiles])
    
    # Donors post quantiles
    D_post_quantiles = []
    for d_u in valid_donors:
        d_post_vals = clean_df[(clean_df[unit_col] == d_u) & (clean_df[time_col].isin(post_times))][outcome_col].values.astype(float)
        D_post_quantiles.append(np.percentile(d_post_vals, [q * 100 for q in quantiles]))
    Q_donors_post = np.column_stack(D_post_quantiles)
    
    # Synthetic Counterfactual post quantiles: Q*(u) = sum_j w_j Q_j(u)
    q_counterfactual_post = Q_donors_post @ donor_weights
    
    # Quantile Treatment Effects: tau(u) = Q_obs(u) - Q_synth(u)
    qte_vector = q_treated_post - q_counterfactual_post
    
    # 5. Distributional Inequality & Shape Metrics
    gini_obs = _compute_gini_coefficient(treated_post_vals)
    # Approximate counterfactual Gini from synthetic quantiles
    gini_synth = _compute_gini_coefficient(q_counterfactual_post)
    gini_diff = gini_obs - gini_synth
    
    # IQR Impact
    p25_obs = float(np.percentile(treated_post_vals, 25))
    p75_obs = float(np.percentile(treated_post_vals, 75))
    iqr_obs = p75_obs - p25_obs
    
    p25_synth = float(q_counterfactual_post[quantiles.index(0.25)]) if 0.25 in quantiles else float(np.interp(0.25, quantiles, q_counterfactual_post))
    p75_synth = float(q_counterfactual_post[quantiles.index(0.75)]) if 0.75 in quantiles else float(np.interp(0.75, quantiles, q_counterfactual_post))
    iqr_synth = p75_synth - p25_synth
    iqr_diff = iqr_obs - iqr_synth
    
    # P90 / P10 ratio
    p10_obs = float(np.percentile(treated_post_vals, 10))
    p90_obs = float(np.percentile(treated_post_vals, 90))
    ratio_obs = (p90_obs / p10_obs) if abs(p10_obs) > 1e-6 else np.nan
    
    p10_synth = float(q_counterfactual_post[quantiles.index(0.10)]) if 0.10 in quantiles else float(np.interp(0.10, quantiles, q_counterfactual_post))
    p90_synth = float(q_counterfactual_post[quantiles.index(0.90)]) if 0.90 in quantiles else float(np.interp(0.90, quantiles, q_counterfactual_post))
    ratio_synth = (p90_synth / p10_synth) if abs(p10_synth) > 1e-6 else np.nan
    
    # 6. Quantile Treatment Effects Table
    qte_table = []
    for idx_q, q_lvl in enumerate(quantiles):
        tau_u = float(qte_vector[idx_q])
        q_obs_val = float(q_treated_post[idx_q])
        q_cf_val = float(q_counterfactual_post[idx_q])
        
        # Narrative interpretation
        if q_lvl <= 0.25:
            interp = "Lower Tail (Safety Net / Floor)"
        elif q_lvl >= 0.75:
            interp = "Upper Tail (High Performer Ceiling)"
        else:
            interp = "Median / Core Distribution"
            
        qte_table.append({
            "quantile": round(float(q_lvl), 2),
            "quantile_label": f"P{(int(q_lvl * 100))}",
            "treated_observed": round(q_obs_val, 3),
            "synthetic_counterfactual": round(q_cf_val, 3),
            "treatment_effect_qte": round(tau_u, 3),
            "interpretation": interp
        })
        
    # 7. Donor Weights Summary
    donor_weight_items = []
    for d_idx, d_name in enumerate(valid_donors):
        w_val = float(donor_weights[d_idx])
        if w_val > 0.001:
            donor_weight_items.append({
                "donor_unit": d_name,
                "weight": round(w_val, 4),
                "weight_pct": round(w_val * 100, 2)
            })
    donor_weight_items.sort(key=lambda item: item["weight"], reverse=True)
    
    # 8. Overall Summary
    mean_qte = float(np.mean(qte_vector))
    median_qte = float(np.median(qte_vector))
    
    overall_summary = {
        "treated_unit": treated_id_str,
        "treatment_time": str(treatment_time),
        "n_valid_donors": J_valid,
        "pre_treatment_periods": len(pre_times),
        "post_treatment_periods": len(post_times),
        "pre_treatment_wasserstein_dist": round(pre_wasserstein_dist, 4),
        "mean_qte_effect": round(mean_qte, 3),
        "median_qte_effect": round(median_qte, 3),
        "gini_observed": round(float(gini_obs), 4),
        "gini_counterfactual": round(float(gini_synth), 4),
        "gini_impact": round(float(gini_diff), 4),
        "iqr_observed": round(float(iqr_obs), 3),
        "iqr_counterfactual": round(float(iqr_synth), 3),
        "iqr_impact": round(float(iqr_diff), 3),
        "p90_p10_ratio_observed": round(float(ratio_obs), 3) if not np.isnan(ratio_obs) else None,
        "p90_p10_ratio_counterfactual": round(float(ratio_synth), 3) if not np.isnan(ratio_synth) else None
    }
    
    # 9. Generate Scientific SVG Visualization
    svg_chart = _generate_quantile_synthetic_svg(
        overall_summary=overall_summary,
        qte_table=qte_table,
        donor_weight_items=donor_weight_items
    )
    
    # 10. APA 7th Edition Narrative
    top_donor = donor_weight_items[0]["donor_unit"] if donor_weight_items else "None"
    top_donor_wt = donor_weight_items[0]["weight_pct"] if donor_weight_items else 0.0
    
    apa_narrative = (
        f"A Quantile Synthetic Control analysis (Gunsilius, 2023; Chernozhukov et al., 2020) was evaluated "
        f"for treated unit '{treated_id_str}' at intervention threshold '{treatment_time}' using J = {J_valid} donor units. "
        f"The synthetic quantile barycenter achieved a pre-treatment Wasserstein-2 matching distance of {pre_wasserstein_dist:.4f}, "
        f"with primary donor weight driven by '{top_donor}' ({top_donor_wt:.1f}%). "
        f"Across post-treatment periods, the median Quantile Treatment Effect was tau(0.50) = {median_qte:.3f} "
        f"(mean QTE = {mean_qte:.3f}). "
        f"Distributional shape evaluation showed a Gini inequality shift of {gini_diff:+.4f} "
        f"(observed Gini = {gini_obs:.4f} vs counterfactual Gini = {gini_synth:.4f}) and an Interquartile Range (IQR) "
        f"compression of {iqr_diff:+.3f}, demonstrating that the intervention "
        f"{'compressed outcome inequality across the distribution' if gini_diff < 0 else 'expanded upper-tail dispersion'}."
    )
    
    return {
        "status": "SUCCESS",
        "overall_summary": overall_summary,
        "donor_weights": donor_weight_items,
        "quantile_treatment_effects": qte_table,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_quantile_synthetic_svg(
    overall_summary: Dict[str, Any],
    qte_table: List[Dict[str, Any]],
    donor_weight_items: List[Dict[str, Any]]
) -> str:
    """
    Dual-panel SVG visualizer:
    Panel 1: Post-Treatment Empirical Quantile Curves (Observed vs Synthetic Counterfactual).
    Panel 2: Quantile Treatment Effects tau(u) Curve across Percentiles with Gini Impact Badge.
    """
    svg_w, svg_h = 780, 360
    
    unit_name = overall_summary.get("treated_unit", "Treated Unit")
    gini_diff = overall_summary.get("gini_impact", 0.0)
    med_qte = overall_summary.get("median_qte_effect", 0.0)
    
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#0f172a" rx="10" />',
        f'  <text x="30" y="32" font-size="14" font-weight="700" fill="#f8fafc">Quantile Synthetic Control &amp; Distributional Impacts (Gunsilius 2023)</text>',
        f'  <text x="30" y="48" font-size="11" fill="#94a3b8">Unit: {unit_name} · Median QTE: {med_qte:.2f} · Gini Shift: {gini_diff:+.4f} · Pre-W2 Distance: {overall_summary.get("pre_treatment_wasserstein_dist", 0):.3f}</text>',
        
        # Panel 1: Observed vs Synthetic Quantile Curves (x: 45 to 395, y: 70 to 300)
        f'  <rect x="45" y="70" width="350" height="230" fill="#1e293b" rx="6" />',
        f'  <text x="57" y="88" font-size="11" font-weight="600" fill="#38bdf8">Post-Treatment Quantile Barycenter Comparison</text>'
    ]
    
    # Coordinate mapping for Panel 1
    p1_x, p1_y, p1_w, p1_h = 55, 100, 320, 180
    
    all_q_vals = []
    for item in qte_table:
        all_q_vals.append(item["treated_observed"])
        all_q_vals.append(item["synthetic_counterfactual"])
        
    min_q = min(all_q_vals) - 0.5
    max_q = max(all_q_vals) + 0.5
    q_span = max_q - min_q if max_q > min_q else 1.0
    
    def map_p1(u_val: float, q_val: float) -> Tuple[float, float]:
        cx = p1_x + u_val * p1_w
        cy = (p1_y + p1_h) - ((q_val - min_q) / q_span) * p1_h
        return cx, cy
        
    # Draw curves
    pts_obs = []
    pts_synth = []
    for item in qte_table:
        u_val = item["quantile"]
        cx_o, cy_o = map_p1(u_val, item["treated_observed"])
        cx_s, cy_s = map_p1(u_val, item["synthetic_counterfactual"])
        pts_obs.append(f"{cx_o:.1f},{cy_o:.1f}")
        pts_synth.append(f"{cx_s:.1f},{cy_s:.1f}")
        
    poly_obs = " ".join(pts_obs)
    poly_synth = " ".join(pts_synth)
    
    # Synthetic curve (dashed violet)
    lines.append(f'  <polyline points="{poly_synth}" fill="none" stroke="#a78bfa" stroke-width="2.5" stroke-dasharray="4 3" />')
    # Observed curve (solid sky blue)
    lines.append(f'  <polyline points="{poly_obs}" fill="none" stroke="#38bdf8" stroke-width="2.5" />')
    
    # Legend Panel 1
    lines.append(f'  <circle cx="{p1_x + 10}" cy="{p1_y + 15}" r="4" fill="#38bdf8" />')
    lines.append(f'  <text x="{p1_x + 20}" y="{p1_y + 18}" font-size="9" font-weight="600" fill="#38bdf8">Treated Observed Q(u)</text>')
    lines.append(f'  <line x1="{p1_x + 160}" y1="{p1_y + 15}" x2="{p1_x + 180}" y2="{p1_y + 15}" stroke="#a78bfa" stroke-width="2" stroke-dasharray="3 2" />')
    lines.append(f'  <text x="{p1_x + 188}" y="{p1_y + 18}" font-size="9" font-weight="600" fill="#a78bfa">Synthetic Q*(u)</text>')

    # Panel 2: Quantile Treatment Effects tau(u) (x: 430 to 740, y: 70 to 300)
    p2_x, p2_y, p2_w, p2_h = 430, 70, 310, 230
    lines.append(f'  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#1e293b" rx="6" />')
    lines.append(f'  <text x="{p2_x + 12}" y="{p2_y + 18}" font-size="11" font-weight="600" fill="#34d399">Quantile Treatment Effect Curve [&tau;(u)]</text>')
    
    p2_px, p2_py, p2_pw, p2_ph = p2_x + 15, 100, 280, 180
    tau_vals = [item["treatment_effect_qte"] for item in qte_table]
    all_tau_bounds = tau_vals + [0.0]
    min_tau = min(all_tau_bounds) - 0.2
    max_tau = max(all_tau_bounds) + 0.2
    tau_span = max_tau - min_tau if max_tau > min_tau else 1.0
    
    def map_p2(u_val: float, t_val: float) -> Tuple[float, float]:
        cx = p2_px + u_val * p2_pw
        cy = (p2_py + p2_ph) - ((t_val - min_tau) / tau_span) * p2_ph
        return cx, cy
        
    # Zero line
    zero_cx1, zero_cy = map_p2(0.0, 0.0)
    zero_cx2, _ = map_p2(1.0, 0.0)
    lines.append(f'  <line x1="{zero_cx1:.1f}" y1="{zero_cy:.1f}" x2="{zero_cx2:.1f}" y2="{zero_cy:.1f}" stroke="#ef4444" stroke-dasharray="2 2" stroke-width="1.5" />')
    lines.append(f'  <text x="{zero_cx2 - 25:.1f}" y="{zero_cy - 4:.1f}" font-size="8" fill="#ef4444">Null (0)</text>')
    
    # QTE Points and line
    pts_qte = []
    for item in qte_table:
        cx_t, cy_t = map_p2(item["quantile"], item["treatment_effect_qte"])
        pts_qte.append(f"{cx_t:.1f},{cy_t:.1f}")
        
    poly_qte = " ".join(pts_qte)
    lines.append(f'  <polyline points="{poly_qte}" fill="none" stroke="#10b981" stroke-width="2.5" />')
    
    for item in qte_table:
        cx_t, cy_t = map_p2(item["quantile"], item["treatment_effect_qte"])
        tau_val = item["treatment_effect_qte"]
        dot_col = "#10b981" if tau_val >= 0 else "#f59e0b"
        lines.append(f'  <circle cx="{cx_t:.1f}" cy="{cy_t:.1f}" r="4" fill="{dot_col}" stroke="#0f172a" stroke-width="1" />')
        lines.append(f'  <text x="{cx_t:.1f}" y="{cy_t - 8:.1f}" font-size="8" font-weight="700" fill="#f1f5f9" text-anchor="middle">{tau_val:.1f}</text>')

    # Bottom inequality badge
    ineq_col = "#10b981" if gini_diff <= 0 else "#f59e0b"
    ineq_txt = "INEQUALITY COMPRESSED" if gini_diff <= 0 else "DISPERSION EXPANDED"
    lines.append(f'  <rect x="{p2_x + 12}" y="{p2_y + p2_h - 22}" width="150" height="14" fill="{ineq_col}22" rx="3" />')
    lines.append(f'  <text x="{p2_x + 87}" y="{p2_y + p2_h - 12}" font-size="8" font-weight="700" fill="{ineq_col}" text-anchor="middle">{ineq_txt} (ΔGini: {gini_diff:+.3f})</text>')

    lines.append('</svg>')
    return "\n".join(lines)
