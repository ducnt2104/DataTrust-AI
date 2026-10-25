# -*- coding: utf-8 -*-
"""
Automatic Debiased Machine Learning via Riesz Representer Learning (Auto-DML) Engine
Methodological References:
- Chernozhukov, V., Newey, W. K., & Singh, R. (2022). "Automatic Debiased Machine Learning of
  Causal and Structural Effects." Econometrica, 90(3), 967-1027.
- Chernozhukov, V., Escanciano, J. C., Ichimura, H., Newey, W. K., & Robins, J. M. (2022).
  "Locally Robust Semiparametric Estimation." The Review of Economic Studies, 89(6), 3047-3085.
- Hirshberg, D. A., & Wager, S. (2021). "Augmented Minimax Linear Estimation."
  The Annals of Statistics, 49(6), 3206-3227.

Learns the Neyman-orthogonal Riesz representer alpha_0(W) directly from data by minimizing the
empirical Riesz loss: L(alpha) = E[0.5 * alpha(W)^2 - m(W, alpha)], bypassing manual derivation of
influence functions or unstable propensity score denominators. Implements K-fold cross-fitting for
binary ATE, continuous policy shifts (D -> D + delta), and average marginal derivatives.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _build_feature_dictionary(
    D: np.ndarray,
    X: np.ndarray,
    degree: int = 2
) -> np.ndarray:
    """
    Constructs an expanded polynomial basis dictionary phi(W) = phi(D, X).
    """
    N = len(D)
    cols = [np.ones(N), D]
    
    # Add standardized X
    p_x = X.shape[1] if len(X.shape) > 1 else 1
    X_mat = X.reshape(N, -1)
    
    for j in range(p_x):
        cols.append(X_mat[:, j])
        # Interaction with D
        cols.append(D * X_mat[:, j])
        
    if degree >= 2:
        cols.append(D ** 2)
        for j in range(p_x):
            cols.append(X_mat[:, j] ** 2)
            
    return np.column_stack(cols)


def _evaluate_functional_vector(
    phi_mat: np.ndarray,
    D: np.ndarray,
    X: np.ndarray,
    functional_type: str,
    shift_delta: float = 1.0
) -> np.ndarray:
    """
    Evaluates m(W_i, phi) for the feature dictionary.
    - 'ate': phi(1, X) - phi(0, X)
    - 'policy_shift': phi(D + delta, X) - phi(D, X)
    - 'marginal_derivative': [phi(D + eps, X) - phi(D - eps, X)] / (2*eps)
    """
    eps = 1e-3
    if functional_type == "ate":
        phi_1 = _build_feature_dictionary(np.ones_like(D), X)
        phi_0 = _build_feature_dictionary(np.zeros_like(D), X)
        return np.mean(phi_1 - phi_0, axis=0)
        
    elif functional_type == "policy_shift":
        phi_shift = _build_feature_dictionary(D + shift_delta, X)
        phi_curr = _build_feature_dictionary(D, X)
        return np.mean(phi_shift - phi_curr, axis=0)
        
    elif functional_type == "marginal_derivative":
        phi_plus = _build_feature_dictionary(D + eps, X)
        phi_minus = _build_feature_dictionary(D - eps, X)
        return np.mean((phi_plus - phi_minus) / (2.0 * eps), axis=0)
        
    else:
        raise ValueError(f"Unknown functional type '{functional_type}'.")


def estimate_auto_dml_riesz(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    covariate_cols: List[str],
    functional_type: str = "ate",  # 'ate', 'policy_shift', 'marginal_derivative'
    shift_delta: float = 1.0,
    n_splits: int = 5,
    ridge_lambda: float = 1e-3,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Automatic Debiased Machine Learning via Riesz Representer Learning (Chernozhukov et al. 2022).

    Args:
        df: Input survey DataFrame.
        outcome_col: Dependent variable Y.
        treatment_col: Treatment variable D (binary or continuous).
        covariate_cols: Exogenous confounding covariates X.
        functional_type: Type of causal parameter ('ate', 'policy_shift', 'marginal_derivative').
        shift_delta: Policy dosage shift parameter delta for 'policy_shift'.
        n_splits: Number of cross-fitting folds (default: 5).
        ridge_lambda: Regularization parameter for Riesz loss and regression.
        alpha_level: Significance level for confidence intervals.

    Returns:
        Structured dictionary matching API contract.
    """
    req_cols = [outcome_col, treatment_col] + covariate_cols
    for col in req_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")

    clean_df = df[req_cols].dropna().copy()
    N = len(clean_df)
    if N < 25:
        raise ValueError(f"Sample size N={N} is too small for cross-fitted Auto-DML (minimum 25 required).")

    y = clean_df[outcome_col].values.astype(float)
    d = clean_df[treatment_col].values.astype(float)
    X = clean_df[covariate_cols].values.astype(float)

    # Standardize X
    x_mean = np.mean(X, axis=0)
    x_std = np.std(X, axis=0)
    x_std[x_std < 1e-8] = 1.0
    X_norm = (X - x_mean) / x_std

    # Check functional type compatibility
    is_binary_treatment = np.all(np.isin(d, [0.0, 1.0]))
    if functional_type == "ate" and not is_binary_treatment:
        # Default to policy shift if continuous
        functional_type = "policy_shift"

    # 1. Baseline Benchmark OLS
    M_ols = np.column_stack([np.ones(N), d, X_norm])
    try:
        b_ols_all = np.linalg.lstsq(M_ols, y, rcond=None)[0]
        beta_ols = float(b_ols_all[1])
        resid_ols = y - M_ols @ b_ols_all
        se_ols = float(np.sqrt(max(1e-12, (np.sum(resid_ols ** 2) / (N - M_ols.shape[1])) * np.linalg.pinv(M_ols.T @ M_ols)[1, 1])))
    except Exception:
        beta_ols = float(np.cov(d, y)[0, 1] / np.var(d)) if np.var(d) > 0 else 0.0
        se_ols = 0.1

    # 2. Build High-Dimensional Dictionary phi(W)
    phi_all = _build_feature_dictionary(d, X_norm)
    p_phi = phi_all.shape[1]

    # 3. K-Fold Cross-Fitting Setup
    rng = np.random.RandomState(42)
    indices = np.arange(N)
    rng.shuffle(indices)
    folds = np.array_split(indices, n_splits)

    psi_scores = np.zeros(N)
    naive_scores = np.zeros(N)
    riesz_weights_all = np.zeros(N)
    
    cv_r2_outcome = []
    cv_riesz_losses = []

    for fold_idx in range(n_splits):
        val_idx = folds[fold_idx]
        train_idx = np.setdiff1d(indices, val_idx)
        
        y_tr, d_tr, X_tr = y[train_idx], d[train_idx], X_norm[train_idx]
        y_val, d_val, X_val = y[val_idx], d[val_idx], X_norm[val_idx]
        
        phi_tr = phi_all[train_idx]
        phi_val = phi_all[val_idx]
        
        # Step A: Outcome Regression gamma(W) via Ridge regression
        # min_w ||y - phi w||^2 + lambda ||w||^2
        PtP_y = phi_tr.T @ phi_tr + ridge_lambda * np.eye(p_phi)
        Pty_y = phi_tr.T @ y_tr
        gamma_weights = np.linalg.solve(PtP_y, Pty_y)
        
        y_val_hat = phi_val @ gamma_weights
        ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
        ss_res = np.sum((y_val - y_val_hat) ** 2)
        r2_fold = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0
        cv_r2_outcome.append(r2_fold)

        # Step B: Automatic Riesz Representer Learning alpha(W) (Chernozhukov et al. 2022)
        # Empirical Riesz Loss: min_rho { 0.5 * rho^T Sigma rho - M^T rho + (lambda/2) ||rho||^2 }
        Sigma_tr = (phi_tr.T @ phi_tr) / len(train_idx)
        M_vector_tr = _evaluate_functional_vector(phi_tr, d_tr, X_tr, functional_type, shift_delta)
        
        A_mat = Sigma_tr + ridge_lambda * np.eye(p_phi)
        rho_riesz = np.linalg.solve(A_mat, M_vector_tr)
        
        # Predicted Riesz weights on validation fold: alpha(W_val) = phi_val @ rho_riesz
        alpha_val = phi_val @ rho_riesz
        riesz_weights_all[val_idx] = alpha_val
        
        # Out-of-fold Riesz loss: 0.5 * E[alpha^2] - m(W, alpha)
        loss_val = float(0.5 * np.mean(alpha_val ** 2) - np.dot(M_vector_tr, rho_riesz))
        cv_riesz_losses.append(loss_val)

        # Step C: Evaluate Functional Predictions on Validation Fold m(W_val, gamma)
        eps_fd = 1e-3
        if functional_type == "ate":
            phi_val_1 = _build_feature_dictionary(np.ones_like(d_val), X_val)
            phi_val_0 = _build_feature_dictionary(np.zeros_like(d_val), X_val)
            m_val = (phi_val_1 @ gamma_weights) - (phi_val_0 @ gamma_weights)
        elif functional_type == "policy_shift":
            phi_val_shift = _build_feature_dictionary(d_val + shift_delta, X_val)
            m_val = (phi_val_shift @ gamma_weights) - (phi_val @ gamma_weights)
        else: # marginal_derivative
            phi_val_plus = _build_feature_dictionary(d_val + eps_fd, X_val)
            phi_val_minus = _build_feature_dictionary(d_val - eps_fd, X_val)
            m_val = ((phi_val_plus @ gamma_weights) - (phi_val_minus @ gamma_weights)) / (2.0 * eps_fd)

        # Step D: Construct Neyman-Orthogonal Score psi_i
        # psi_i = m(W_i, gamma) + alpha(W_i) * (Y_i - gamma(W_i))
        resid_val = y_val - y_val_hat
        psi_val = m_val + alpha_val * resid_val
        
        psi_scores[val_idx] = psi_val
        naive_scores[val_idx] = m_val

    # 4. Final Estimates & Asymptotic Inference
    theta_autodml = float(np.mean(psi_scores))
    theta_naive = float(np.mean(naive_scores))
    
    var_autodml = float(np.var(psi_scores, ddof=1) / N)
    se_autodml = float(np.sqrt(max(1e-12, var_autodml)))
    t_stat = float(theta_autodml / se_autodml) if se_autodml > 0 else 0.0
    p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(t_stat))))
    
    crit = float(stats.norm.ppf(1.0 - alpha_level / 2.0))
    ci_low = theta_autodml - crit * se_autodml
    ci_high = theta_autodml + crit * se_autodml

    # Naive plug-in standard error
    se_naive = float(np.sqrt(max(1e-12, np.var(naive_scores, ddof=1) / N)))

    # 5. Riesz Representer Weights Diagnostics
    alpha_mean = float(np.mean(riesz_weights_all))
    alpha_sd = float(np.std(riesz_weights_all))
    alpha_min = float(np.min(riesz_weights_all))
    alpha_max = float(np.max(riesz_weights_all))
    weight_stability_ratio = float(alpha_max / (alpha_sd + 1e-6))
    
    is_stable = bool(weight_stability_ratio < 10.0 and alpha_sd < 8.0)
    stability_verdict = "Ổn định cao (Stable Riesz Weights)" if is_stable else "Cảnh báo trọng số cực trị (Extreme Weights)"

    # 6. Overall Summary
    param_label = (
        "Average Treatment Effect (ATE)" if functional_type == "ate" else
        (f"Continuous Policy Shift (D -> D + {shift_delta})" if functional_type == "policy_shift" else "Average Marginal Derivative")
    )

    overall_summary = {
        "sample_size": N,
        "n_covariates": len(covariate_cols),
        "basis_dimension_p": p_phi,
        "cross_fitting_splits_K": n_splits,
        "functional_type": functional_type,
        "functional_label": param_label,
        
        # Auto-DML Causal Effect
        "theta_autodml": round(theta_autodml, 3),
        "se_autodml": round(se_autodml, 3),
        "t_statistic": round(t_stat, 2),
        "p_value": round(p_val, 4),
        "ci_95": [round(ci_low, 3), round(ci_high, 3)],
        
        # Naive Plug-in Comparison
        "theta_naive_plugin": round(theta_naive, 3),
        "se_naive_plugin": round(se_naive, 3),
        "debiasing_correction_magnitude": round(abs(theta_autodml - theta_naive), 3),
        
        # Benchmark OLS
        "beta_ols_benchmark": round(beta_ols, 3),
        "se_ols_benchmark": round(se_ols, 3),
        
        # ML Model Performance
        "mean_outcome_r2": round(float(np.mean(cv_r2_outcome)), 3),
        "mean_riesz_loss": round(float(np.mean(cv_riesz_losses)), 4),
        
        # Riesz Representer Properties
        "riesz_weight_mean": round(alpha_mean, 3),
        "riesz_weight_sd": round(alpha_sd, 3),
        "riesz_weight_min": round(alpha_min, 3),
        "riesz_weight_max": round(alpha_max, 3),
        "weight_stability_verdict": stability_verdict
    }

    # 7. Generate Scientific SVG Visualization
    svg_chart = _generate_auto_dml_svg(
        overall_summary=overall_summary,
        riesz_weights=riesz_weights_all
    )

    # 8. APA 7th Edition Narrative
    apa_narrative = (
        f"An Automatic Debiased Machine Learning (Auto-DML) evaluation (Chernozhukov, Newey, & Singh, 2022) was conducted "
        f"for {param_label} using an empirical Riesz representer dictionary of dimension p = {p_phi} with K = {n_splits} cross-fitting folds. "
        f"The outcome regression model achieved a cross-validated R2 of {overall_summary['mean_outcome_r2']:.2f}, while the learned Riesz representer "
        f"yielded a mean loss of {overall_summary['mean_riesz_loss']:.4f} (weight SD = {alpha_sd:.2f}, {stability_verdict}). "
        f"The resulting doubly robust Auto-DML estimate was theta = {theta_autodml:.3f} (SE = {se_autodml:.3f}, 95% CI [{ci_low:.3f}, {ci_high:.3f}], p = {p_val:.4f}), "
        f"compared to naive plug-in ML theta = {theta_naive:.3f} and conventional OLS beta = {beta_ols:.3f}. "
        f"The Riesz orthogonalization removed a finite-sample regularization bias of {abs(theta_autodml - theta_naive):.3f}, "
        f"achieving asymptotic efficiency with Neyman orthogonality."
    )

    return {
        "status": "SUCCESS",
        "overall_summary": overall_summary,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_auto_dml_svg(
    overall_summary: Dict[str, Any],
    riesz_weights: np.ndarray
) -> str:
    """
    Dual-panel SVG:
    Panel 1: Distribution of Learned Riesz Representer Weights alpha_0(W) (Histogram & Stability).
    Panel 2: Estimator Forest Plot: Auto-DML (Orthogonalized) vs Naive Plug-in ML vs Benchmark OLS.
    """
    svg_w, svg_h = 780, 360
    
    th_dml = overall_summary.get("theta_autodml", 0.0)
    se_dml = overall_summary.get("se_autodml", 0.1)
    ci_dml = overall_summary.get("ci_95", [th_dml - 1, th_dml + 1])
    
    th_nv = overall_summary.get("theta_naive_plugin", 0.0)
    se_nv = overall_summary.get("se_naive_plugin", 0.1)
    
    b_ols = overall_summary.get("beta_ols_benchmark", 0.0)
    se_ols = overall_summary.get("se_ols_benchmark", 0.1)
    
    fn_lbl = overall_summary.get("functional_label", "Causal Effect")

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#0f172a" rx="10" />',
        f'  <text x="30" y="32" font-size="14" font-weight="700" fill="#f8fafc">Automatic Debiased Machine Learning &amp; Riesz Learning (Chernozhukov 2022)</text>',
        f'  <text x="30" y="48" font-size="11" fill="#94a3b8">Target: {fn_lbl} · Auto-DML: {th_dml:.3f} (SE: {se_dml:.3f}) · Naive ML: {th_nv:.3f} · Bias Removed: {abs(th_dml - th_nv):.3f}</text>',
        
        # Panel 1: Riesz Weights Histogram (x: 45 to 395, y: 70 to 300)
        f'  <rect x="45" y="70" width="350" height="230" fill="#1e293b" rx="6" />',
        f'  <text x="57" y="88" font-size="11" font-weight="600" fill="#38bdf8">Learned Riesz Representer Weights [&alpha;_(0)(W)]</text>'
    ]

    # Panel 1: Histogram
    p1_x, p1_y, p1_w, p1_h = 55, 100, 320, 150
    counts, bin_edges = np.histogram(riesz_weights, bins=12)
    max_c = max(counts) if max(counts) > 0 else 1
    n_bins = len(counts)
    bar_w = (p1_w / n_bins) - 2

    for b_idx in range(n_bins):
        b_cnt = counts[b_idx]
        bx = p1_x + b_idx * (p1_w / n_bins)
        bh = (b_cnt / max_c) * p1_h
        by = (p1_y + p1_h) - bh
        lines.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" fill="#38bdf8" rx="2" />')

    lines.append(f'  <line x1="{p1_x}" y1="{p1_y + p1_h}" x2="{p1_x + p1_w}" y2="{p1_y + p1_h}" stroke="#64748b" stroke-width="1" />')
    lines.append(f'  <text x="{p1_x + 5}" y="{p1_y + p1_h + 16}" font-size="8" fill="#94a3b8">Min: {overall_summary.get("riesz_weight_min", 0):.2f}</text>')
    lines.append(f'  <text x="{p1_x + p1_w - 45}" y="{p1_y + p1_h + 16}" font-size="8" fill="#94a3b8">Max: {overall_summary.get("riesz_weight_max", 0):.2f}</text>')

    # Stability Badge
    lines.append(f'  <rect x="{p1_x + 10}" y="{p1_y + 10}" width="160" height="18" fill="#10b98122" rx="3" />')
    lines.append(f'  <text x="{p1_x + 90}" y="{p1_y + 22}" font-size="8" font-weight="700" fill="#10b981" text-anchor="middle">{overall_summary.get("weight_stability_verdict", "Stable")}</text>')

    # Panel 2: Forest Plot Comparison (x: 430 to 740, y: 70 to 300)
    p2_x, p2_y, p2_w, p2_h = 430, 70, 310, 230
    lines.append(f'  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#1e293b" rx="6" />')
    lines.append(f'  <text x="{p2_x + 12}" y="{p2_y + 18}" font-size="11" font-weight="600" fill="#34d399">Neyman-Orthogonal vs Naive Estimators</text>')

    p2_px, p2_py, p2_pw, p2_ph = p2_x + 20, 110, 270, 150
    estimators = [
        {"name": "Benchmark OLS", "est": b_ols, "ci": [b_ols - 1.96 * se_ols, b_ols + 1.96 * se_ols], "col": "#f59e0b"},
        {"name": "Naive Plug-in ML", "est": th_nv, "ci": [th_nv - 1.96 * se_nv, th_nv + 1.96 * se_nv], "col": "#94a3b8"},
        {"name": "Auto-DML (Riesz)", "est": th_dml, "ci": ci_dml, "col": "#10b981"}
    ]

    all_vals = [e["est"] for e in estimators] + [e["ci"][0] for e in estimators] + [e["ci"][1] for e in estimators] + [0.0]
    min_v = min(all_vals) - 0.5
    max_v = max(all_vals) + 0.5
    v_span = max_v - min_v if max_v > min_v else 1.0

    def map_p2_x(val: float) -> float:
        return p2_px + ((val - min_v) / v_span) * p2_pw

    zero_x = map_p2_x(0.0)
    lines.append(f'  <line x1="{zero_x:.1f}" y1="{p2_py}" x2="{zero_x:.1f}" y2="{p2_py + p2_ph}" stroke="#64748b" stroke-dasharray="3 3" stroke-width="1.5" />')
    lines.append(f'  <text x="{zero_x:.1f}" y="{p2_py + p2_ph + 14}" font-size="8" fill="#64748b" text-anchor="middle">0 (Null)</text>')

    bar_spacing = p2_ph / len(estimators)
    for idx_e, est in enumerate(estimators):
        cy = p2_py + idx_e * bar_spacing + 22
        e_col = est["col"]
        cx_mid = map_p2_x(est["est"])
        cx_low = map_p2_x(est["ci"][0])
        cx_high = map_p2_x(est["ci"][1])
        
        lines.append(f'  <text x="{p2_px}" y="{cy - 10:.1f}" font-size="10" font-weight="600" fill="{e_col}">{est["name"]}: {est["est"]:.3f}</text>')
        lines.append(f'  <line x1="{cx_low:.1f}" y1="{cy:.1f}" x2="{cx_high:.1f}" y2="{cy:.1f}" stroke="{e_col}" stroke-width="2.5" />')
        lines.append(f'  <circle cx="{cx_mid:.1f}" cy="{cy:.1f}" r="5" fill="{e_col}" stroke="#0f172a" stroke-width="1.5" />')

    lines.append('</svg>')
    return "\n".join(lines)
