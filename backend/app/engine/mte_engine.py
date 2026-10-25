# -*- coding: utf-8 -*-
"""
Marginal Treatment Effects (MTE) and Local Instrumental Variables (LIV) Engine
Scientific References:
- Heckman, J. J., & Vytlacil, E. (1999). "Local instrumental variables and latency
  formulation for calculating marginal treatment effects." PNAS, 96(8), 4730-4734.
- Heckman, J. J., & Vytlacil, E. (2005). "Structural Equations, Treatment Effects,
  and Econometric Policy Evaluation." Econometrica, 73(3), 669-738.
- Carneiro, P., Heckman, J. J., & Vytlacil, E. (2011). "Estimating Marginal Returns
  to Education." American Economic Review, 101(6), 2754-2781.
- Brinch, C. N., Mogstad, M., & Wiswall, M. (2017). "Beyond LATE with a Discrete
  Instrument." Journal of Political Economy, 125(4), 985-1039.

Identifies the Marginal Treatment Effect (MTE) curve over unobserved resistance to
treatment U_D in (0, 1) and integrates MTE to derive unified causal parameters:
ATE, ATT, ATU, LATE, and Policy-Relevant Treatment Effect (PRTE).
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _fit_propensity_probit(Z_mat: np.ndarray, d: np.ndarray, max_iter: int = 50) -> np.ndarray:
    """
    Fits probit model for treatment propensity P(D=1|Z) using Newton-Raphson.
    Returns estimated probabilities P in [0.01, 0.99].
    """
    n, k = Z_mat.shape
    beta = np.zeros(k)
    for _ in range(max_iter):
        eta = np.clip(Z_mat @ beta, -5.0, 5.0)
        phi = stats.norm.pdf(eta)
        Phi = np.clip(stats.norm.cdf(eta), 1e-5, 1.0 - 1e-5)
        
        # Probit log-likelihood score
        lambda_val = np.where(d == 1, phi / Phi, -phi / (1.0 - Phi))
        grad = Z_mat.T @ lambda_val
        
        # Expected Hessian (information matrix)
        w = (phi ** 2) / (Phi * (1.0 - Phi) + 1e-12)
        hess = Z_mat.T @ (w[:, None] * Z_mat) + 1e-4 * np.eye(k)
        
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hess, grad, rcond=None)[0]
            
        beta += step
        if np.max(np.abs(step)) < 1e-5:
            break
            
    eta_final = np.clip(Z_mat @ beta, -5.0, 5.0)
    p_hat = stats.norm.cdf(eta_final)
    return np.clip(p_hat, 0.01, 0.99)


def _fit_polynomial_outcome_model(
    y: np.ndarray,
    p: np.ndarray,
    X: np.ndarray,
    poly_degree: int = 3
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Fits semiparametric outcome model:
    E[Y | X, P] = X*beta_x + sum_{k=1}^K gamma_k * P^k
    Returns coefficients, design matrix, and residual variance.
    """
    n = len(y)
    p_powers = [p ** k for k in range(1, poly_degree + 1)]
    poly_mat = np.column_stack(p_powers)
    
    # Full design matrix [Intercept, X, P, P^2, P^3...]
    M = np.column_stack([np.ones(n), X, poly_mat])
    
    try:
        coef = np.linalg.lstsq(M, y, rcond=None)[0]
    except Exception:
        coef = np.zeros(M.shape[1])
        
    residuals = y - (M @ coef)
    dof = max(n - M.shape[1], 1)
    s2 = np.sum(residuals ** 2) / dof
    return coef, M, float(s2)


def _compute_mte_at_grid(
    coef: np.ndarray,
    u_grid: np.ndarray,
    poly_degree: int = 3,
    x_dim: int = 0
) -> np.ndarray:
    """
    Evaluates MTE(u) = d E[Y|P=u]/du for given polynomial coefficients.
    gamma_1 + 2*gamma_2*u + 3*gamma_3*u^2 + ...
    """
    # Poly coefficients start after Intercept (1) and X (x_dim)
    poly_start = 1 + x_dim
    gammas = coef[poly_start:poly_start + poly_degree]
    
    mte_vals = np.zeros_like(u_grid, dtype=float)
    for k in range(1, len(gammas) + 1):
        mte_vals += k * gammas[k - 1] * (u_grid ** (k - 1))
        
    return mte_vals


def estimate_mte(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    instrument_cols: List[str],
    covariate_cols: Optional[List[str]] = None,
    poly_degree: int = 3,
    alpha_level: float = 0.05,
    n_bootstraps: int = 300,
    policy_shift_pct: float = 0.15
) -> Dict[str, Any]:
    """
    Estimates Marginal Treatment Effects (MTE) and derived causal parameters.
    """
    if covariate_cols is None:
        covariate_cols = []

    req_cols = [outcome_col, treatment_col] + instrument_cols + covariate_cols
    for col in req_cols:
        if col not in df.columns:
            return {"status": "ERROR", "message": f"Column '{col}' not found in dataframe."}

    sub_df = df[req_cols].dropna().copy()
    n = len(sub_df)
    if n < 40:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": f"Sample size (N={n}) is insufficient for semi-parametric MTE estimation (minimum 40 required)."
        }

    y = sub_df[outcome_col].astype(float).values
    d_raw = sub_df[treatment_col].astype(float).values
    d = (d_raw > np.median(d_raw)).astype(float) if len(np.unique(d_raw)) > 2 else d_raw

    # Build instrument matrix Z [Intercept, Instruments, Covariates]
    Z_inst = sub_df[instrument_cols].astype(float).values
    if covariate_cols:
        X_cov = sub_df[covariate_cols].astype(float).values
        cov_mean = np.mean(X_cov, axis=0)
        cov_std = np.std(X_cov, axis=0)
        cov_std[cov_std == 0] = 1.0
        X_cov_norm = (X_cov - cov_mean) / cov_std
        Z_full = np.column_stack([np.ones(n), Z_inst, X_cov_norm])
        X_eval = X_cov_norm
    else:
        Z_full = np.column_stack([np.ones(n), Z_inst])
        X_eval = np.empty((n, 0))

    # Step 1: Propensity Score Estimation P(D=1|Z, X)
    p_hat = _fit_propensity_probit(Z_full, d)

    # Determine common support bounds
    p_t = p_hat[d == 1]
    p_c = p_hat[d == 0]
    p_min_support = max(float(np.percentile(p_hat, 2)), 0.05)
    p_max_support = min(float(np.percentile(p_hat, 98)), 0.95)

    # Grid for MTE evaluation
    u_grid = np.linspace(p_min_support, p_max_support, 50)

    # Step 2: Fit Semiparametric Polynomial Outcome Model
    coef, M_mat, s2 = _fit_polynomial_outcome_model(y, p_hat, X_eval, poly_degree=poly_degree)
    mte_point = _compute_mte_at_grid(coef, u_grid, poly_degree=poly_degree, x_dim=X_eval.shape[1])

    # Step 3: Compute Integrated Causal Parameters
    # Grid step du
    du = u_grid[1] - u_grid[0]

    # Weights across the grid
    # ATE: Uniform weight
    w_ate = np.ones_like(u_grid)
    w_ate /= (np.sum(w_ate) * du + 1e-12)

    # ATT: w_att(u) = Pr(P > u) / E[P]
    p_mean = np.mean(p_hat)
    w_att = np.array([np.mean(p_hat > u) / (p_mean + 1e-12) for u in u_grid])
    w_att_sum = np.sum(w_att) * du
    w_att = w_att / (w_att_sum + 1e-12) if w_att_sum > 0 else w_ate

    # ATU: w_atu(u) = Pr(P <= u) / (1 - E[P])
    w_atu = np.array([np.mean(p_hat <= u) / (1.0 - p_mean + 1e-12) for u in u_grid])
    w_atu_sum = np.sum(w_atu) * du
    w_atu = w_atu / (w_atu_sum + 1e-12) if w_atu_sum > 0 else w_ate

    # LATE between 25th and 75th percentiles of propensity
    p25 = float(np.percentile(p_hat, 25))
    p75 = float(np.percentile(p_hat, 75))
    w_late = np.where((u_grid >= p25) & (u_grid <= p75), 1.0, 0.0)
    w_late_sum = np.sum(w_late) * du
    w_late = w_late / (w_late_sum + 1e-12) if w_late_sum > 0 else w_ate

    # Policy-Relevant Treatment Effect (PRTE): shifting propensity by +policy_shift_pct
    p_star = np.clip(p_hat * (1.0 + policy_shift_pct), 0.0, 1.0)
    delta_p_mean = np.mean(p_star) - p_mean
    if abs(delta_p_mean) > 1e-5:
        w_prte = np.array([(np.mean(p_hat <= u) - np.mean(p_star <= u)) / delta_p_mean for u in u_grid])
        w_prte = np.maximum(0.0, w_prte)
        w_prte_sum = np.sum(w_prte) * du
        w_prte = w_prte / (w_prte_sum + 1e-12) if w_prte_sum > 0 else w_ate
    else:
        w_prte = w_ate

    # Point estimates of integrated parameters
    ate_est = float(np.sum(mte_point * w_ate) * du)
    att_est = float(np.sum(mte_point * w_att) * du)
    atu_est = float(np.sum(mte_point * w_atu) * du)
    late_est = float(np.sum(mte_point * w_late) * du)
    prte_est = float(np.sum(mte_point * w_prte) * du)

    # Step 4: Bootstrap Inference for MTE Curve and Parameters
    boot_mte = []
    boot_ate = []
    boot_att = []
    boot_atu = []
    boot_late = []
    boot_prte = []

    rng = np.random.RandomState(42)
    for _ in range(n_bootstraps):
        idx = rng.choice(n, size=n, replace=True)
        b_y = y[idx]
        b_d = d[idx]
        b_Z = Z_full[idx]
        b_X = X_eval[idx]

        b_p_hat = _fit_propensity_probit(b_Z, b_d)
        b_coef, _, _ = _fit_polynomial_outcome_model(b_y, b_p_hat, b_X, poly_degree=poly_degree)
        b_mte = _compute_mte_at_grid(b_coef, u_grid, poly_degree=poly_degree, x_dim=b_X.shape[1])
        boot_mte.append(b_mte)

        # Integrated parameters
        b_p_mean = np.mean(b_p_hat)
        b_w_att = np.array([np.mean(b_p_hat > u) / (b_p_mean + 1e-12) for u in u_grid])
        b_w_att_sum = np.sum(b_w_att) * du
        b_w_att = b_w_att / (b_w_att_sum + 1e-12) if b_w_att_sum > 0 else w_ate

        b_w_atu = np.array([np.mean(b_p_hat <= u) / (1.0 - b_p_mean + 1e-12) for u in u_grid])
        b_w_atu_sum = np.sum(b_w_atu) * du
        b_w_atu = b_w_atu / (b_w_atu_sum + 1e-12) if b_w_atu_sum > 0 else w_ate

        boot_ate.append(float(np.sum(b_mte * w_ate) * du))
        boot_att.append(float(np.sum(b_mte * b_w_att) * du))
        boot_atu.append(float(np.sum(b_mte * b_w_atu) * du))
        boot_late.append(float(np.sum(b_mte * w_late) * du))
        boot_prte.append(float(np.sum(b_mte * w_prte) * du))

    # MTE confidence bands
    boot_mte_mat = np.array(boot_mte)
    mte_ci_lower = np.percentile(boot_mte_mat, 100.0 * (alpha_level / 2.0), axis=0)
    mte_ci_upper = np.percentile(boot_mte_mat, 100.0 * (1.0 - alpha_level / 2.0), axis=0)
    mte_se = np.std(boot_mte_mat, axis=0, ddof=1)

    def calc_inference(est_val, boot_arr):
        se = float(np.std(boot_arr, ddof=1)) if len(boot_arr) > 1 else 0.0
        c_low = float(np.percentile(boot_arr, 100.0 * (alpha_level / 2.0)))
        c_high = float(np.percentile(boot_arr, 100.0 * (1.0 - alpha_level / 2.0)))
        z_stat = float(est_val / se) if se > 1e-8 else 0.0
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        return {
            "estimate": round(est_val, 4),
            "std_error": round(se, 4),
            "z_stat": round(z_stat, 3),
            "p_value": round(p_val, 4),
            "ci_lower": round(c_low, 4),
            "ci_upper": round(c_high, 4),
            "is_significant": bool(p_val < alpha_level)
        }

    parameters_summary = {
        "ate": calc_inference(ate_est, boot_ate),
        "att": calc_inference(att_est, boot_att),
        "atu": calc_inference(atu_est, boot_atu),
        "late": calc_inference(late_est, boot_late),
        "prte": calc_inference(prte_est, boot_prte)
    }

    # Format MTE curve points
    mte_curve = []
    for idx_u in range(len(u_grid)):
        mte_curve.append({
            "u_d": round(float(u_grid[idx_u]), 3),
            "mte": round(float(mte_point[idx_u]), 4),
            "std_error": round(float(mte_se[idx_u]), 4),
            "ci_lower": round(float(mte_ci_lower[idx_u]), 4),
            "ci_upper": round(float(mte_ci_upper[idx_u]), 4),
            "w_att": round(float(w_att[idx_u]), 4),
            "w_atu": round(float(w_atu[idx_u]), 4)
        })

    # Selection sorting diagnosis (Heckman selection direction)
    # If MTE decreases with U_D -> Positive selection on gains (Roy model)
    slope_mte = float(np.polyfit(u_grid, mte_point, 1)[0])
    if slope_mte < -0.05:
        selection_pattern = "POSITIVE_SELECTION_ON_GAINS (Roy selection: individuals with low resistance have higher causal returns)"
    elif slope_mte > 0.05:
        selection_pattern = "NEGATIVE_SELECTION_ON_GAINS (Reverse selection: individuals with high resistance have higher causal returns)"
    else:
        selection_pattern = "HOMOGENEOUS_RETURNS (Flat MTE curve across unobserved resistance spectrum)"

    # Generate Scientific SVG Visualization
    svg_chart = _generate_mte_svg(
        u_grid=u_grid,
        mte_point=mte_point,
        mte_ci_lower=mte_ci_lower,
        mte_ci_upper=mte_ci_upper,
        w_att=w_att,
        w_atu=w_atu,
        params=parameters_summary,
        selection_pattern=selection_pattern
    )

    # Academic APA 7th Edition narrative
    apa_narrative = (
        f"A semiparametric Marginal Treatment Effects (MTE) framework (Heckman & Vytlacil, 1999, 2005) "
        f"was estimated to evaluate treatment response heterogeneity for '{treatment_col}' on '{outcome_col}' "
        f"across N = {n} respondents using instrumental variables ({', '.join(instrument_cols)}). "
        f"The propensity score common support spanned U_D in [{p_min_support:.2f}, {p_max_support:.2f}]. "
        f"The derived Average Treatment Effect across the population was ATE = {ate_est:.4f} "
        f"(95% CI [{parameters_summary['ate']['ci_lower']:.4f}, {parameters_summary['ate']['ci_upper']:.4f}], p = {parameters_summary['ate']['p_value']:.4f}). "
        f"Among treated respondents, the Average Treatment Effect on the Treated was ATT = {att_est:.4f} "
        f"(95% CI [{parameters_summary['att']['ci_lower']:.4f}, {parameters_summary['att']['ci_upper']:.4f}]), whereas the return for untreated non-adopters "
        f"was ATU = {atu_est:.4f} (95% CI [{parameters_summary['atu']['ci_lower']:.4f}, {parameters_summary['atu']['ci_upper']:.4f}]). "
        f"The LATE among marginal compliers was {late_est:.4f}. Under a simulated {int(policy_shift_pct*100)}% expansion policy, "
        f"the Policy-Relevant Treatment Effect was PRTE = {prte_est:.4f}. "
        f"The MTE curve slope (slope = {slope_mte:.3f}) diagnosed: {selection_pattern}."
    )

    return {
        "status": "SUCCESS",
        "model_type": "MARGINAL_TREATMENT_EFFECTS_HECKMAN_VYTLACIL_2005",
        "sample_size": n,
        "bootstrap_replications": n_bootstraps,
        "polynomial_degree": poly_degree,
        "common_support": {
            "p_min": round(p_min_support, 3),
            "p_max": round(p_max_support, 3)
        },
        "selection_sorting_pattern": selection_pattern,
        "mte_slope": round(slope_mte, 4),
        "parameters": parameters_summary,
        "mte_curve": mte_curve,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_mte_svg(
    u_grid: np.ndarray,
    mte_point: np.ndarray,
    mte_ci_lower: np.ndarray,
    mte_ci_upper: np.ndarray,
    w_att: np.ndarray,
    w_atu: np.ndarray,
    params: Dict[str, Any],
    selection_pattern: str
) -> str:
    """
    Constructs a dual-panel SVG visualizer:
    - Panel A: MTE Curve across U_D with 95% Confidence Band & Policy Parameters (ATE, ATT, ATU).
    - Panel B: Integration Weights w_ATT(u) and w_ATU(u) over unobserved resistance spectrum.
    """
    svg_w, svg_h = 780, 340

    # Panel A coordinates
    p1_x, p1_y, p1_w, p1_h = 50, 60, 360, 220
    # Panel B coordinates
    p2_x, p2_y, p2_w, p2_h = 470, 60, 270, 220

    # Scales for Panel A
    all_y = list(mte_point) + list(mte_ci_lower) + list(mte_ci_upper) + [0.0]
    min_y = min(all_y) - 0.2
    max_y = max(all_y) + 0.2
    span_y = max(max_y - min_y, 1e-4)

    min_u = float(u_grid[0])
    max_u = float(u_grid[-1])
    span_u = max(max_u - min_u, 1e-4)

    def to_p1_x(u):
        return p1_x + ((u - min_u) / span_u) * p1_w

    def to_p1_y(val):
        return p1_y + p1_h - ((val - min_y) / span_y) * p1_h

    # Build MTE path & polygon
    mte_points_str = " ".join([f"{to_p1_x(u):.1f},{to_p1_y(v):.1f}" for u, v in zip(u_grid, mte_point)])
    ci_poly_top = " ".join([f"{to_p1_x(u):.1f},{to_p1_y(v):.1f}" for u, v in zip(u_grid, mte_ci_upper)])
    ci_poly_bot = " ".join([f"{to_p1_x(u):.1f},{to_p1_y(v):.1f}" for u, v in reversed(list(zip(u_grid, mte_ci_lower)))])
    ci_polygon = f"{ci_poly_top} {ci_poly_bot}"

    zero_y = to_p1_y(0.0)

    # Panel B scales for weights
    max_w = max(np.max(w_att), np.max(w_atu), 1.0)
    def to_p2_y(w):
        return p2_y + p2_h - (w / max_w) * p2_h

    att_path = " ".join([f"{p2_x + ((u - min_u)/span_u)*p2_w:.1f},{to_p2_y(w):.1f}" for u, w in zip(u_grid, w_att)])
    atu_path = " ".join([f"{p2_x + ((u - min_u)/span_u)*p2_w:.1f},{to_p2_y(w):.1f}" for u, w in zip(u_grid, w_atu)])

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#f8fafc" rx="8" />',
        '  <!-- Panel A Header -->',
        '  <text x="50" y="30" font-size="13" font-weight="700" fill="#1e293b">PANEL A: Marginal Treatment Effect Curve Δ^MTE(u_D)</text>',
        f'  <text x="50" y="46" font-size="11" fill="#64748b">Causal Effect over Resistance to Treatment U_D with 95% Bootstrap CI</text>',
        '  <!-- Panel B Header -->',
        '  <text x="470" y="30" font-size="13" font-weight="700" fill="#1e293b">PANEL B: Policy Integration Weights</text>',
        '  <text x="470" y="46" font-size="11" fill="#64748b">Comparison of w_ATT(u) vs w_ATU(u)</text>',
        '  <line x1="440" y1="20" x2="440" y2="310" stroke="#e2e8f0" stroke-dasharray="4 4" stroke-width="1.5" />'
    ]

    # Panel A Axis & Reference
    svg_lines.append(f'  <rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" fill="#ffffff" stroke="#cbd5e1" stroke-width="1" rx="4" />')
    if p1_y <= zero_y <= (p1_y + p1_h):
        svg_lines.append(f'  <line x1="{p1_x}" y1="{zero_y:.1f}" x2="{p1_x + p1_w}" y2="{zero_y:.1f}" stroke="#94a3b8" stroke-dasharray="2 2" stroke-width="1.5" />')
        svg_lines.append(f'  <text x="{p1_x + 8}" y="{zero_y - 4:.1f}" font-size="9" fill="#94a3b8">Null Effect (0.0)</text>')

    # Confidence Band & MTE Curve
    svg_lines.append(f'  <polygon points="{ci_polygon}" fill="#c7d2fe" fill-opacity="0.5" />')
    svg_lines.append(f'  <polyline points="{mte_points_str}" fill="none" stroke="#4f46e5" stroke-width="3" stroke-linecap="round" />')

    # ATE and ATT horizontal reference lines in Panel A
    ate_val = params["ate"]["estimate"]
    att_val = params["att"]["estimate"]
    y_ate = to_p1_y(ate_val)
    y_att = to_p1_y(att_val)

    if p1_y <= y_ate <= (p1_y + p1_h):
        svg_lines.append(f'  <line x1="{p1_x}" y1="{y_ate:.1f}" x2="{p1_x + p1_w}" y2="{y_ate:.1f}" stroke="#0ea5e9" stroke-dasharray="3 3" stroke-width="1.5" />')
        svg_lines.append(f'  <text x="{p1_x + p1_w - 60}" y="{y_ate - 3:.1f}" font-size="9" font-weight="600" fill="#0ea5e9">ATE = {ate_val:.2f}</text>')

    if p1_y <= y_att <= (p1_y + p1_h):
        svg_lines.append(f'  <line x1="{p1_x}" y1="{y_att:.1f}" x2="{p1_x + p1_w}" y2="{y_att:.1f}" stroke="#10b981" stroke-dasharray="3 3" stroke-width="1.5" />')
        svg_lines.append(f'  <text x="{p1_x + p1_w - 60}" y="{y_att + 11:.1f}" font-size="9" font-weight="600" fill="#10b981">ATT = {att_val:.2f}</text>')

    # X axis labels Panel A
    svg_lines.append(f'  <text x="{p1_x}" y="{p1_y + p1_h + 16}" font-size="9" fill="#64748b">{min_u:.2f} (Eager)</text>')
    svg_lines.append(f'  <text x="{p1_x + p1_w / 2}" y="{p1_y + p1_h + 16}" font-size="9" fill="#64748b" text-anchor="middle">Unobserved Resistance to Treatment (U_D)</text>')
    svg_lines.append(f'  <text x="{p1_x + p1_w}" y="{p1_y + p1_h + 16}" font-size="9" fill="#64748b" text-anchor="end">{max_u:.2f} (Reluctant)</text>')

    # Panel B: Weights Plot
    svg_lines.append(f'  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#ffffff" stroke="#cbd5e1" stroke-width="1" rx="4" />')
    svg_lines.append(f'  <polyline points="{att_path}" fill="none" stroke="#10b981" stroke-width="2.5" />')
    svg_lines.append(f'  <polyline points="{atu_path}" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="4 2" />')

    # Legend in Panel B
    svg_lines.append(f'  <line x1="{p2_x + 15}" y1="{p2_y + 20}" x2="{p2_x + 35}" y2="{p2_y + 20}" stroke="#10b981" stroke-width="2.5" />')
    svg_lines.append(f'  <text x="{p2_x + 42}" y="{p2_y + 24}" font-size="10" font-weight="600" fill="#10b981">w_ATT(u) (Treated Weight)</text>')

    svg_lines.append(f'  <line x1="{p2_x + 15}" y1="{p2_y + 40}" x2="{p2_x + 35}" y2="{p2_y + 40}" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="4 2" />')
    svg_lines.append(f'  <text x="{p2_x + 42}" y="{p2_y + 44}" font-size="10" font-weight="600" fill="#f59e0b">w_ATU(u) (Untreated Weight)</text>')

    # X axis labels Panel B
    svg_lines.append(f'  <text x="{p2_x}" y="{p2_y + p2_h + 16}" font-size="9" fill="#64748b">{min_u:.2f}</text>')
    svg_lines.append(f'  <text x="{p2_x + p2_w / 2}" y="{p2_y + p2_h + 16}" font-size="9" fill="#64748b" text-anchor="middle">Resistance (U_D)</text>')
    svg_lines.append(f'  <text x="{p2_x + p2_w}" y="{p2_y + p2_h + 16}" font-size="9" fill="#64748b" text-anchor="end">{max_u:.2f}</text>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)
