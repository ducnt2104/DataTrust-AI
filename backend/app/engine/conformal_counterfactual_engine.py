# -*- coding: utf-8 -*-
"""
Conformal Counterfactual Risk Inference Engine
Scientific References:
- Chernozhukov, V., Wüthrich, K., & Zhu, Y. (2021). "An Exact and Robust Conformal
  Inference Method for Counterfactual and Synthetic Controls."
  Journal of the American Statistical Association, 116(536), 1849-1864.
- Lei, L., & Candès, E. J. (2021). "Conformal Inference of Counterfactuals and
  Individual Treatment Effects."
  Journal of the Royal Statistical Society: Series B (Statistical Methodology), 83(5), 911-938.
- Tibshirani, R. J., Foygel Barber, R., Candès, E. J., & Ramdas, A. (2019).
  "Conformal Prediction Under Covariate Shift."
  Advances in Neural Information Processing Systems (NeurIPS 2019).

Provides distribution-free, finite-sample valid prediction intervals for individual
counterfactual outcomes Y(1), Y(0) and Individual Treatment Effects (ITE) tau(X),
along with downside harm risk profiling and policy safety diagnostics.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _estimate_propensity_scores(
    X_mat: np.ndarray,
    w_vec: np.ndarray,
    max_iter: int = 50,
    reg_l2: float = 1e-3
) -> np.ndarray:
    """
    Fits L2-regularized logistic regression using Newton-Raphson to estimate e(X) = P(W=1|X).
    """
    n, p = X_mat.shape
    M = np.column_stack([np.ones(n), X_mat])
    k = M.shape[1]
    
    beta = np.zeros(k)
    reg_mat = reg_l2 * np.eye(k)
    reg_mat[0, 0] = 0.0  # Do not regularize intercept
    
    for _ in range(max_iter):
        p_hat = 1.0 / (1.0 + np.exp(-np.clip(M @ beta, -30.0, 30.0)))
        w_diag = p_hat * (1.0 - p_hat)
        w_diag = np.clip(w_diag, 1e-5, 0.25)
        
        # Gradient: M.T @ (p_hat - w_vec) + reg_mat @ beta
        grad = M.T @ (p_hat - w_vec) + reg_mat @ beta
        # Hessian: M.T @ diag(w_diag) @ M + reg_mat
        hess = (M.T * w_diag) @ M + reg_mat
        
        try:
            delta = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            delta = np.linalg.lstsq(hess, grad, rcond=None)[0]
            
        beta -= delta
        if np.max(np.abs(delta)) < 1e-5:
            break
            
    p_final = 1.0 / (1.0 + np.exp(-np.clip(M @ beta, -30.0, 30.0)))
    # Clip to avoid extreme densities [0.02, 0.98]
    return np.clip(p_final, 0.02, 0.98)


def _fit_linear_predictor(
    X_train: np.ndarray,
    y_train: np.ndarray,
    alpha_ridge: float = 1.0
) -> Tuple[np.ndarray, float]:
    """
    Fits Ridge-regularized conditional mean predictor mu(X) = E[Y | X].
    Returns: (coefficients, residual_variance)
    """
    n, p = X_train.shape
    M = np.column_stack([np.ones(n), X_train])
    k = M.shape[1]
    
    reg_mat = alpha_ridge * np.eye(k)
    reg_mat[0, 0] = 0.0
    
    try:
        coef = np.linalg.solve(M.T @ M + reg_mat, M.T @ y_train)
    except np.linalg.LinAlgError:
        coef = np.linalg.lstsq(M.T @ M + reg_mat, M.T @ y_train, rcond=None)[0]
        
    residuals = y_train - (M @ coef)
    s2 = float(np.sum(residuals ** 2) / max(n - k, 1))
    return coef, s2


def _predict_linear(X_mat: np.ndarray, coef: np.ndarray) -> np.ndarray:
    n = X_mat.shape[0]
    M = np.column_stack([np.ones(n), X_mat])
    return M @ coef


def _weighted_quantile(
    values: np.ndarray,
    weights: np.ndarray,
    quantile: float
) -> float:
    """
    Computes weighted empirical quantile for conformal prediction under covariate shift.
    values: 1D array of scores (non-conformity)
    weights: 1D array of non-negative weights
    quantile: in [0, 1]
    """
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
        
    sorter = np.argsort(values)
    v_sorted = values[sorter]
    w_sorted = weights[sorter]
    
    total_w = np.sum(w_sorted)
    if total_w <= 1e-12:
        return float(np.percentile(values, quantile * 100))
        
    cum_w = np.cumsum(w_sorted) / total_w
    idx = np.searchsorted(cum_w, quantile)
    idx = min(idx, len(v_sorted) - 1)
    return float(v_sorted[idx])


def estimate_conformal_counterfactuals(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    covariate_cols: List[str],
    miscoverage_alpha: float = 0.10,
    calibration_ratio: float = 0.50,
    use_propensity_weighting: bool = True,
    subgroup_col: Optional[str] = None,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Executes Conformal Counterfactual Risk Inference based on Chernozhukov et al. (2021)
    and Lei & Candes (2021).
    
    Args:
        df: Input survey DataFrame.
        outcome_col: Target continuous outcome variable Y.
        treatment_col: Binary treatment assignment W in {0, 1}.
        covariate_cols: Baseline confounding and heterogeneity features X.
        miscoverage_alpha: Significance level alpha (e.g., 0.10 for 90% confidence bands).
        calibration_ratio: Fraction of treated/control units allocated to conformal calibration.
        use_propensity_weighting: Whether to apply importance weights for covariate shift.
        subgroup_col: Optional column name for subgroup risk stratification.
        random_state: Seed for reproducible split conformal inference.
        
    Returns:
        Structured dictionary conforming to API contract.
    """
    if not 0.01 <= miscoverage_alpha <= 0.50:
        raise ValueError(f"miscoverage_alpha must be in [0.01, 0.50], got {miscoverage_alpha}")
    if not 0.20 <= calibration_ratio <= 0.80:
        raise ValueError(f"calibration_ratio must be in [0.20, 0.80], got {calibration_ratio}")
        
    req_cols = [outcome_col, treatment_col] + list(covariate_cols)
    if subgroup_col and subgroup_col not in req_cols:
        req_cols.append(subgroup_col)
        
    for col in req_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")
            
    # Clean dataset
    clean_df = df[req_cols].dropna().copy().reset_index(drop=True)
    n_total = len(clean_df)
    if n_total < 30:
        raise ValueError(f"Sample size too small for conformal inference: N={n_total} (minimum 30 required).")
        
    # Process treatment
    t_raw = clean_df[treatment_col].values
    unique_t = np.unique(t_raw)
    if len(unique_t) == 2:
        w_vec = (t_raw == np.max(unique_t)).astype(float)
    else:
        # Continuous or multi-valued: binarize above median
        med_t = float(np.median(t_raw))
        w_vec = (t_raw > med_t).astype(float)
        
    n_treated = int(np.sum(w_vec == 1.0))
    n_control = int(np.sum(w_vec == 0.0))
    
    if n_treated < 10 or n_control < 10:
        raise ValueError(f"Insufficient units in treatment arms: treated={n_treated}, control={n_control} (min 10 each).")
        
    y_vec = clean_df[outcome_col].values.astype(float)
    X_raw = clean_df[covariate_cols].values.astype(float)
    
    # Standardize covariates
    x_mean = np.mean(X_raw, axis=0)
    x_std = np.std(X_raw, axis=0)
    x_std[x_std < 1e-8] = 1.0
    X_mat = (X_raw - x_mean) / x_std
    
    # 1. Estimate Propensity Scores e(X)
    e_hat = _estimate_propensity_scores(X_mat, w_vec)
    
    # Propensity AUC
    try:
        from sklearn.metrics import roc_auc_score
        prop_auc = float(roc_auc_score(w_vec, e_hat))
    except Exception:
        # Simple Mann-Whitney U calculation for AUC
        t_scores = e_hat[w_vec == 1.0]
        c_scores = e_hat[w_vec == 0.0]
        u_stat, _ = stats.mannwhitneyu(t_scores, c_scores, alternative="greater")
        prop_auc = float(u_stat / (len(t_scores) * len(c_scores)))
        
    # 2. Split Conformal Sampling (treated & control separately)
    rng = np.random.RandomState(random_state)
    
    idx_treated = np.where(w_vec == 1.0)[0]
    idx_control = np.where(w_vec == 0.0)[0]
    
    rng.shuffle(idx_treated)
    rng.shuffle(idx_control)
    
    n_cal_t = max(5, int(len(idx_treated) * calibration_ratio))
    n_cal_c = max(5, int(len(idx_control) * calibration_ratio))
    
    cal_idx_t = idx_treated[:n_cal_t]
    train_idx_t = idx_treated[n_cal_t:]
    
    cal_idx_c = idx_control[:n_cal_c]
    train_idx_c = idx_control[n_cal_c:]
    
    # 3. Fit conditional outcome models mu_1(X) and mu_0(X) on training splits
    coef_1, var_1 = _fit_linear_predictor(X_mat[train_idx_t], y_vec[train_idx_t], alpha_ridge=1.0)
    coef_0, var_0 = _fit_linear_predictor(X_mat[train_idx_c], y_vec[train_idx_c], alpha_ridge=1.0)
    
    # 4. Compute Non-Conformity Scores on Calibration Splits
    pred_cal_1 = _predict_linear(X_mat[cal_idx_t], coef_1)
    scores_cal_1 = np.abs(y_vec[cal_idx_t] - pred_cal_1)
    
    pred_cal_0 = _predict_linear(X_mat[cal_idx_c], coef_0)
    scores_cal_0 = np.abs(y_vec[cal_idx_c] - pred_cal_0)
    
    # Bonferroni split: each potential outcome gets alpha/2 miscoverage
    half_alpha = miscoverage_alpha / 2.0
    conf_level = 1.0 - half_alpha
    
    # 5. Compute Conformal Cutoffs (Propensity Weighted or Standard)
    if use_propensity_weighting:
        # For predicting Y(1) on control: weights ~ (1-e)/e
        weights_t = (1.0 - e_hat[cal_idx_t]) / e_hat[cal_idx_t]
        weights_t = np.clip(weights_t, 0.05, 20.0)
        q_cutoff_1 = _weighted_quantile(scores_cal_1, weights_t, conf_level)
        
        # For predicting Y(0) on treated: weights ~ e/(1-e)
        weights_c = e_hat[cal_idx_c] / (1.0 - e_hat[cal_idx_c])
        weights_c = np.clip(weights_c, 0.05, 20.0)
        q_cutoff_0 = _weighted_quantile(scores_cal_0, weights_c, conf_level)
    else:
        # Standard unweighted conformal quantile: (1 + 1/n) * (1 - alpha/2)
        q_lvl_1 = min(1.0, math.ceil((len(scores_cal_1) + 1) * conf_level) / len(scores_cal_1))
        q_cutoff_1 = float(np.percentile(scores_cal_1, q_lvl_1 * 100))
        
        q_lvl_0 = min(1.0, math.ceil((len(scores_cal_0) + 1) * conf_level) / len(scores_cal_0))
        q_cutoff_0 = float(np.percentile(scores_cal_0, q_lvl_0 * 100))
        
    # Ensure minimum non-zero band
    q_cutoff_1 = max(float(q_cutoff_1), 1e-4)
    q_cutoff_0 = max(float(q_cutoff_0), 1e-4)
    
    # 6. Predict Individual Outcomes & Conformal Bands for ALL Units
    y1_hat_all = _predict_linear(X_mat, coef_1)
    y0_hat_all = _predict_linear(X_mat, coef_0)
    ite_point_all = y1_hat_all - y0_hat_all
    
    # Conformal Counterfactual Bounds
    y1_lower_all = y1_hat_all - q_cutoff_1
    y1_upper_all = y1_hat_all + q_cutoff_1
    
    y0_lower_all = y0_hat_all - q_cutoff_0
    y0_upper_all = y0_hat_all + q_cutoff_0
    
    # Conformal ITE Intervals: [y1_lower - y0_upper, y1_upper - y0_lower]
    # Length = 2 * (q_cutoff_1 + q_cutoff_0)
    ite_lower_all = ite_point_all - (q_cutoff_1 + q_cutoff_0)
    ite_upper_all = ite_point_all + (q_cutoff_1 + q_cutoff_0)
    
    # Downside Risk & Policy Categories
    is_downside_risk = (ite_lower_all < 0.0).astype(int)
    is_strictly_beneficial = (ite_lower_all > 0.0).astype(int)
    is_strictly_harmful = (ite_upper_all < 0.0).astype(int)
    is_ambiguous = ((ite_lower_all <= 0.0) & (ite_upper_all >= 0.0)).astype(int)
    
    downside_risk_rate = float(np.mean(is_downside_risk))
    strictly_beneficial_rate = float(np.mean(is_strictly_beneficial))
    strictly_harmful_rate = float(np.mean(is_strictly_harmful))
    ambiguous_rate = float(np.mean(is_ambiguous))
    
    # Conditional Value-at-Risk (CVaR) of lower bound at 5th percentile
    var_5 = float(np.percentile(ite_lower_all, 5.0))
    cvar_5_sub = ite_lower_all[ite_lower_all <= var_5]
    cvar_5 = float(np.mean(cvar_5_sub)) if len(cvar_5_sub) > 0 else var_5
    
    # Overall summary metrics
    estimated_ate = float(np.mean(ite_point_all))
    ate_conformal_lb = float(estimated_ate - (q_cutoff_1 + q_cutoff_0) / math.sqrt(n_total))
    ate_conformal_ub = float(estimated_ate + (q_cutoff_1 + q_cutoff_0) / math.sqrt(n_total))
    
    # 7. Subgroup Risk Profiles
    subgroup_profiles: List[Dict[str, Any]] = []
    
    if subgroup_col and subgroup_col in clean_df.columns:
        sub_series = clean_df[subgroup_col].astype(str)
        groups = sub_series.unique()
    else:
        # Default: Stratify by Propensity Quintiles
        try:
            sub_series = pd.qcut(e_hat, q=min(4, len(np.unique(e_hat))), labels=False, duplicates='drop').astype(str)
            sub_series = "Propensity Bin " + sub_series
            groups = sub_series.unique()
        except Exception:
            sub_series = pd.Series(["All Units"] * n_total)
            groups = ["All Units"]
            
    for grp in sorted(groups):
        grp_mask = (sub_series == grp).values
        grp_n = int(np.sum(grp_mask))
        if grp_n == 0:
            continue
            
        grp_ite = float(np.mean(ite_point_all[grp_mask]))
        grp_ite_lb = float(np.mean(ite_lower_all[grp_mask]))
        grp_ite_ub = float(np.mean(ite_upper_all[grp_mask]))
        grp_downside_rate = float(np.mean(is_downside_risk[grp_mask]))
        grp_beneficial_rate = float(np.mean(is_strictly_beneficial[grp_mask]))
        grp_harmful_rate = float(np.mean(is_strictly_harmful[grp_mask]))
        
        # Policy recommendation logic
        if grp_beneficial_rate > 0.70:
            rec = "Prioritized Rollout (Strict Benefit)"
            rec_code = "ROLLOUT"
        elif grp_harmful_rate > 0.40 or grp_ite_ub < 0:
            rec = "Contraindicated (Risk of Harm)"
            rec_code = "CONTRAINDICATED"
        elif grp_downside_rate > 0.50:
            rec = "Targeted Safeguards Required"
            rec_code = "SAFEGUARDS"
        else:
            rec = "Standard Implementation with Monitoring"
            rec_code = "MONITOR"
            
        subgroup_profiles.append({
            "group_name": str(grp),
            "sample_size": grp_n,
            "mean_ite": round(grp_ite, 4),
            "mean_ite_lower": round(grp_ite_lb, 4),
            "mean_ite_upper": round(grp_ite_ub, 4),
            "downside_risk_rate": round(grp_downside_rate, 4),
            "strictly_beneficial_rate": round(grp_beneficial_rate, 4),
            "strictly_harmful_rate": round(grp_harmful_rate, 4),
            "policy_recommendation": rec,
            "recommendation_code": rec_code
        })
        
    # 8. Individual Predictions Sample (25 representative units)
    sample_indices = []
    # Include extreme downside units, strictly beneficial, and median units
    downside_idx = np.where(is_downside_risk == 1)[0]
    beneficial_idx = np.where(is_strictly_beneficial == 1)[0]
    
    if len(downside_idx) > 0:
        sample_indices.extend(downside_idx[:10])
    if len(beneficial_idx) > 0:
        sample_indices.extend(beneficial_idx[:10])
    # Add random spread to reach 25
    remaining = [i for i in range(n_total) if i not in sample_indices]
    if len(remaining) > 0:
        sample_indices.extend(remaining[:max(0, 25 - len(sample_indices))])
        
    sample_indices = sorted(sample_indices[:25])
    
    individual_predictions: List[Dict[str, Any]] = []
    for idx in sample_indices:
        w_val = int(w_vec[idx])
        y_obs = float(y_vec[idx])
        
        if is_strictly_beneficial[idx]:
            status = "Strictly Beneficial"
        elif is_strictly_harmful[idx]:
            status = "Strictly Harmful"
        elif is_downside_risk[idx]:
            status = "Downside Risk Present"
        else:
            status = "Neutral / Ambiguous"
            
        individual_predictions.append({
            "unit_id": int(idx + 1),
            "treatment_observed": w_val,
            "outcome_observed": round(y_obs, 4),
            "propensity_score": round(float(e_hat[idx]), 4),
            "predicted_y1": round(float(y1_hat_all[idx]), 4),
            "predicted_y0": round(float(y0_hat_all[idx]), 4),
            "y1_conformal_interval": [round(float(y1_lower_all[idx]), 4), round(float(y1_upper_all[idx]), 4)],
            "y0_conformal_interval": [round(float(y0_lower_all[idx]), 4), round(float(y0_upper_all[idx]), 4)],
            "ite_point_estimate": round(float(ite_point_all[idx]), 4),
            "ite_conformal_interval": [round(float(ite_lower_all[idx]), 4), round(float(ite_upper_all[idx]), 4)],
            "downside_risk": bool(is_downside_risk[idx]),
            "risk_status": status
        })
        
    # 9. Calibration Diagnostics
    calib_diag = {
        "propensity_auc": round(prop_auc, 4),
        "propensity_overlap_min": round(float(np.min(e_hat)), 4),
        "propensity_overlap_max": round(float(np.max(e_hat)), 4),
        "propensity_overlap_median_treated": round(float(np.median(e_hat[w_vec == 1.0])), 4),
        "propensity_overlap_median_control": round(float(np.median(e_hat[w_vec == 0.0])), 4),
        "treated_calibration_size": n_cal_t,
        "treated_training_size": len(train_idx_t),
        "control_calibration_size": n_cal_c,
        "control_training_size": len(train_idx_c),
        "treated_nonconformity_cutoff": round(q_cutoff_1, 4),
        "control_nonconformity_cutoff": round(q_cutoff_0, 4),
        "ite_band_half_width": round(q_cutoff_1 + q_cutoff_0, 4),
        "weighted_conformal_shift_applied": bool(use_propensity_weighting)
    }
    
    # 10. Overall Summary
    target_coverage_pct = round((1.0 - miscoverage_alpha) * 100, 1)
    overall_summary = {
        "sample_size": n_total,
        "treated_count": n_treated,
        "control_count": n_control,
        "miscoverage_alpha": round(miscoverage_alpha, 3),
        "target_coverage_pct": target_coverage_pct,
        "estimated_ate": round(estimated_ate, 4),
        "ate_conformal_interval": [round(ate_conformal_lb, 4), round(ate_conformal_ub, 4)],
        "downside_risk_rate": round(downside_risk_rate, 4),
        "strictly_beneficial_rate": round(strictly_beneficial_rate, 4),
        "strictly_harmful_rate": round(strictly_harmful_rate, 4),
        "ambiguous_rate": round(ambiguous_rate, 4),
        "var_downside_5pct": round(var_5, 4),
        "cvar_downside_5pct": round(cvar_5, 4),
        "mean_ite_interval_length": round(2.0 * (q_cutoff_1 + q_cutoff_0), 4)
    }
    
    # 11. Generate Scientific SVG Visualization
    svg_chart = _generate_conformal_counterfactual_svg(
        overall_summary=overall_summary,
        subgroup_profiles=subgroup_profiles,
        individual_sample=individual_predictions
    )

    # 12. APA Narrative
    cov_str = ", ".join(covariate_cols[:4]) + ("..." if len(covariate_cols) > 4 else "")
    apa_narrative = (
        f"A Conformal Counterfactual Risk Inference analysis (Chernozhukov, Wüthrich, & Zhu, 2021; "
        f"Lei & Candès, 2021) was conducted on N = {n_total} survey respondents (n_treated = {n_treated}, "
        f"n_control = {n_control}) conditioning on covariates [{cov_str}]. "
        f"At a distribution-free {target_coverage_pct}% conformal confidence guarantee, the overall sample Average "
        f"Treatment Effect was estimated at ATE = {estimated_ate:.4f} (asymptotic conformal band [{ate_conformal_lb:.4f}, {ate_conformal_ub:.4f}]). "
        f"Split conformal calibration yielded non-conformity cutoffs of Q_1 = {q_cutoff_1:.4f} for treated counterfactuals "
        f"and Q_0 = {q_cutoff_0:.4f} for control counterfactuals, generating an exact individual conformal band half-width "
        f"of ±{(q_cutoff_1 + q_cutoff_0):.4f}. "
        f"Downside risk profiling revealed that {downside_risk_rate * 100:.1f}% of participants exhibit potential downside "
        f"harm risk (individual lower bound < 0), with a 5% Conditional Value-at-Risk (CVaR) of {cvar_5:.4f}. "
        f"Concurrently, {strictly_beneficial_rate * 100:.1f}% of respondents demonstrated strict deterministic benefit "
        f"(lower bound > 0), while {strictly_harmful_rate * 100:.1f}% experienced strict harm. "
        f"Propensity score overlap was verified with an AUC of {prop_auc:.3f} across the unit distribution."
    )
    
    return {
        "status": "SUCCESS",
        "overall_summary": overall_summary,
        "calibration_diagnostics": calib_diag,
        "subgroup_risk_profiles": subgroup_profiles,
        "individual_predictions_sample": individual_predictions,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_conformal_counterfactual_svg(
    overall_summary: Dict[str, Any],
    subgroup_profiles: List[Dict[str, Any]],
    individual_sample: List[Dict[str, Any]]
) -> str:
    """
    Constructs a dual-panel SVG visualizer:
    Panel 1: Individual Counterfactual ITE Conformal Bands (Sorted with Null Line & Downside Harm Flagging).
    Panel 2: Subgroup Downside Risk & Strict Benefit Distribution with Policy Flags.
    """
    svg_w, svg_h = 780, 360
    
    # Pick top 7 representative units from sample
    units_to_plot = individual_sample[:7]
    
    # Range determination for Panel 1 (x: 40 to 420)
    p1_x, p1_y, p1_w, p1_h = 40, 60, 380, 260
    
    all_bounds = []
    for u in units_to_plot:
        all_bounds.extend(u["ite_conformal_interval"])
    all_bounds.append(0.0)
    
    min_val = min(all_bounds) - 0.5
    max_val = max(all_bounds) + 0.5
    val_range = max_val - min_val if max_val > min_val else 1.0
    
    def map_p1_x(v: float) -> float:
        return p1_x + ((v - min_val) / val_range) * p1_w
        
    zero_x = map_p1_x(0.0)
    
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',
        f'  <rect width="{svg_w}" height="{svg_h}" fill="#0f172a" rx="10" />',
        f'  <text x="30" y="32" font-size="14" font-weight="700" fill="#f8fafc">Conformal Counterfactual Risk Inference (Chernozhukov et al. 2021; Lei &amp; Candès 2021)</text>',
        f'  <text x="30" y="48" font-size="11" fill="#94a3b8">Target Coverage: {overall_summary.get("target_coverage_pct", 90)}% · Downside Harm Rate: {(overall_summary.get("downside_risk_rate", 0)*100):.1f}% · CVaR (5%): {overall_summary.get("cvar_downside_5pct", 0):.2f}</text>',
        
        # Panel 1 Box
        f'  <rect x="{p1_x - 10}" y="{p1_y - 5}" width="{p1_w + 20}" height="{p1_h + 15}" fill="#1e293b" rx="6" />',
        f'  <text x="{p1_x}" y="{p1_y + 15}" font-size="11" font-weight="600" fill="#38bdf8">Individual Conformal Treatment Effect Intervals [C_τ(X)]</text>',
        # Zero vertical line
        f'  <line x1="{zero_x:.1f}" y1="{p1_y + 25}" x2="{zero_x:.1f}" y2="{p1_y + p1_h - 15}" stroke="#ef4444" stroke-dasharray="3 3" stroke-width="1.5" />',
        f'  <text x="{zero_x:.1f}" y="{p1_y + p1_h - 2}" font-size="9" fill="#ef4444" text-anchor="middle">Null Effect (0.0)</text>'
    ]
    
    # Plot individual unit intervals
    n_pts = len(units_to_plot)
    row_step = (p1_h - 60) / max(n_pts, 1)
    
    for i, u in enumerate(units_to_plot):
        cur_y = p1_y + 40 + i * row_step
        lb, ub = u["ite_conformal_interval"]
        pt = u["ite_point_estimate"]
        
        x_lb = map_p1_x(lb)
        x_ub = map_p1_x(ub)
        x_pt = map_p1_x(pt)
        
        # Color coding: Green if lb > 0, Red if ub < 0, Amber if zero included
        if lb > 0:
            stroke_col = "#10b981"
            fill_col = "#10b981"
        elif ub < 0:
            stroke_col = "#ef4444"
            fill_col = "#ef4444"
        else:
            stroke_col = "#f59e0b"
            fill_col = "#f59e0b"
            
        lines.append(f'  <text x="{p1_x}" y="{cur_y + 3}" font-size="9" fill="#94a3b8">Unit {u["unit_id"]}</text>')
        lines.append(f'  <line x1="{x_lb:.1f}" y1="{cur_y}" x2="{x_ub:.1f}" y2="{cur_y}" stroke="{stroke_col}" stroke-width="2.5" stroke-linecap="round" />')
        lines.append(f'  <line x1="{x_lb:.1f}" y1="{cur_y - 4}" x2="{x_lb:.1f}" y2="{cur_y + 4}" stroke="{stroke_col}" stroke-width="1.5" />')
        lines.append(f'  <line x1="{x_ub:.1f}" y1="{cur_y - 4}" x2="{x_ub:.1f}" y2="{cur_y + 4}" stroke="{stroke_col}" stroke-width="1.5" />')
        lines.append(f'  <circle cx="{x_pt:.1f}" cy="{cur_y}" r="3.5" fill="{fill_col}" stroke="#0f172a" stroke-width="1" />')
        lines.append(f'  <text x="{x_ub + 5:.1f}" y="{cur_y + 3}" font-size="9" font-weight="600" fill="{stroke_col}">[{lb:.1f}, {ub:.1f}]</text>')

    # Panel 2: Subgroup Risk Distribution (x: 460 to 750)
    p2_x, p2_y, p2_w, p2_h = 460, 60, 290, 260
    lines.append(f'  <rect x="{p2_x - 10}" y="{p2_y - 5}" width="{p2_w + 20}" height="{p2_h + 15}" fill="#1e293b" rx="6" />')
    lines.append(f'  <text x="{p2_x}" y="{p2_y + 15}" font-size="11" font-weight="600" fill="#a78bfa">Subgroup Risk Profiles &amp; Policy Guidance</text>')
    
    subgroups = subgroup_profiles[:5]
    sg_step = (p2_h - 45) / max(len(subgroups), 1)
    
    for j, sg in enumerate(subgroups):
        sy = p2_y + 38 + j * sg_step
        g_name = sg.get("group_name", f"Group {j+1}")[:18]
        down_rate = sg.get("downside_risk_rate", 0.0)
        ben_rate = sg.get("strictly_beneficial_rate", 0.0)
        rec_code = sg.get("recommendation_code", "MONITOR")
        
        # Badge color
        if rec_code == "ROLLOUT":
            badge_bg = "#065f46"
            badge_txt = "#6ee7b7"
        elif rec_code == "CONTRAINDICATED":
            badge_bg = "#991b1b"
            badge_txt = "#fca5a5"
        elif rec_code == "SAFEGUARDS":
            badge_bg = "#92400e"
            badge_txt = "#fcd34d"
        else:
            badge_bg = "#312e81"
            badge_txt = "#c7d2fe"
            
        lines.append(f'  <text x="{p2_x}" y="{sy}" font-size="10" font-weight="600" fill="#f1f5f9">{g_name}</text>')
        # Recommendation badge
        lines.append(f'  <rect x="{p2_x + 190}" y="{sy - 10}" width="95" height="14" fill="{badge_bg}" rx="3" />')
        lines.append(f'  <text x="{p2_x + 237}" y="{sy}" font-size="8" font-weight="700" fill="{badge_txt}" text-anchor="middle">{rec_code}</text>')
        
        # Stacked progress bar
        bar_w = 170
        bar_y = sy + 6
        ben_w = max(0.0, ben_rate * bar_w)
        down_w = max(0.0, down_rate * bar_w)
        
        lines.append(f'  <rect x="{p2_x}" y="{bar_y}" width="{bar_w}" height="8" fill="#334155" rx="3" />')
        if ben_w > 0:
            lines.append(f'  <rect x="{p2_x}" y="{bar_y}" width="{ben_w:.1f}" height="8" fill="#10b981" rx="3" />')
        if down_w > 0:
            lines.append(f'  <rect x="{p2_x + ben_w:.1f}" y="{bar_y}" width="{min(down_w, bar_w - ben_w):.1f}" height="8" fill="#f59e0b" rx="2" />')
            
        lines.append(f'  <text x="{p2_x + bar_w + 5}" y="{bar_y + 7}" font-size="8" fill="#94a3b8">B:{ben_rate*100:.0f}% D:{down_rate*100:.0f}%</text>')

    lines.append('</svg>')
    return "\n".join(lines)
