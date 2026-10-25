# -*- coding: utf-8 -*-
"""
Non-random Survey Attrition and Selection Bounds Engine (Lee Bounds)
Scientific References:
- Lee, D. S. (2009). "Training, Wages, and Sample Selection: Estimating Sharp Bounds
  on Treatment Effects." The Review of Economic Studies, 76(3), 1071-1102.
- Horowitz, J. L., & Manski, C. F. (2000). "Nonparametric analysis of randomized
  experiments with missing covariate and outcome data." JASA, 95(449), 77-84.
- Imbens, G. W., & Manski, C. F. (2004). "Confidence Intervals for Partially Identified
  Parameters." Econometrica, 72(6), 1845-1857.
- Stoye, J. (2009). "More on confidence intervals for partially identified parameters."
  Econometrica, 77(4), 1299-1315.

Computes sharp non-parametric bounds on treatment effects under non-random survey attrition,
loss to follow-up, or selective response reporting, with optional covariate tightening.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats, optimize


def _compute_imbens_manski_critical_value(
    delta_lb: float,
    delta_ub: float,
    se_lb: float,
    se_ub: float,
    alpha: float = 0.05
) -> float:
    """
    Computes Imbens-Manski (2004) / Stoye (2009) critical value c_alpha
    for partially identified parameter intervals:
    Phi(c + (UB - LB)/max(se_lb, se_ub)) - Phi(-c) = 1 - alpha
    """
    width = max(delta_ub - delta_lb, 0.0)
    max_se = max(se_lb, se_ub, 1e-8)
    ratio = width / max_se

    def obj(c):
        return stats.norm.cdf(c + ratio) - stats.norm.cdf(-c) - (1.0 - alpha)

    # Initial bounds for solver: between z_{1-alpha} (one-sided) and z_{1-alpha/2} (two-sided)
    z_one = stats.norm.ppf(1.0 - alpha)
    z_two = stats.norm.ppf(1.0 - alpha / 2.0)

    if ratio > 5.0:
        return float(z_one)
    elif ratio < 1e-4:
        return float(z_two)

    try:
        sol = optimize.brentq(obj, z_one - 0.5, z_two + 0.5)
        return float(sol)
    except Exception:
        return float(z_two)


def _compute_single_cell_lee_bounds(
    y_t: np.ndarray,
    y_c: np.ndarray,
    r_t: float,
    r_c: float
) -> Tuple[float, float, float]:
    """
    Computes unconditional Lee bounds for a single cell:
    - y_t: Observed outcomes for treated group with R=1
    - y_c: Observed outcomes for control group with R=1
    - r_t: Response rate in treated group P(R=1|T=1)
    - r_c: Response rate in control group P(R=1|T=0)
    Returns: (lower_bound, upper_bound, trimming_fraction_q)
    """
    if len(y_t) == 0 or len(y_c) == 0:
        return 0.0, 0.0, 0.0

    if r_t >= r_c:
        # Treatment has higher response rate -> Trim treated group
        q = max((r_t - r_c) / (r_t + 1e-12), 0.0)
        q = min(q, 0.95)
        
        # Lower bound: drop top q-quantile of y_t
        cutoff_upper = np.percentile(y_t, 100.0 * (1.0 - q))
        trimmed_y_t_lower = y_t[y_t <= cutoff_upper]
        mean_t_lb = float(np.mean(trimmed_y_t_lower)) if len(trimmed_y_t_lower) > 0 else float(np.mean(y_t))
        
        # Upper bound: drop bottom q-quantile of y_t
        cutoff_lower = np.percentile(y_t, 100.0 * q)
        trimmed_y_t_upper = y_t[y_t >= cutoff_lower]
        mean_t_ub = float(np.mean(trimmed_y_t_upper)) if len(trimmed_y_t_upper) > 0 else float(np.mean(y_t))
        
        mean_c = float(np.mean(y_c))
        delta_lb = mean_t_lb - mean_c
        delta_ub = mean_t_ub - mean_c
    else:
        # Control has higher response rate -> Trim control group
        q = max((r_c - r_t) / (r_c + 1e-12), 0.0)
        q = min(q, 0.95)
        
        # Lower bound: drop bottom q-quantile of y_c (maximizing mean_c)
        cutoff_lower = np.percentile(y_c, 100.0 * q)
        trimmed_y_c_lower = y_c[y_c >= cutoff_lower]
        mean_c_ub = float(np.mean(trimmed_y_c_lower)) if len(trimmed_y_c_lower) > 0 else float(np.mean(y_c))
        
        # Upper bound: drop top q-quantile of y_c (minimizing mean_c)
        cutoff_upper = np.percentile(y_c, 100.0 * (1.0 - q))
        trimmed_y_c_upper = y_c[y_c <= cutoff_upper]
        mean_c_lb = float(np.mean(trimmed_y_c_upper)) if len(trimmed_y_c_upper) > 0 else float(np.mean(y_c))
        
        mean_t = float(np.mean(y_t))
        delta_lb = mean_t - mean_c_ub
        delta_ub = mean_t - mean_c_lb

    return delta_lb, delta_ub, q


def estimate_lee_bounds(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    response_col: Optional[str] = None,
    covariate_cols: Optional[List[str]] = None,
    alpha_level: float = 0.05,
    n_bootstraps: int = 300
) -> Dict[str, Any]:
    """
    Estimates sharp non-parametric Lee Bounds (Lee 2009) with Imbens-Manski confidence intervals.
    """
    if covariate_cols is None:
        covariate_cols = []

    if outcome_col not in df.columns:
        return {"status": "ERROR", "message": f"Outcome column '{outcome_col}' not found in dataframe."}
    if treatment_col not in df.columns:
        return {"status": "ERROR", "message": f"Treatment column '{treatment_col}' not found in dataframe."}

    req_cols = [outcome_col, treatment_col]
    if response_col and response_col in df.columns:
        req_cols.append(response_col)
    req_cols.extend([c for c in covariate_cols if c in df.columns])

    sub_df = df[req_cols].copy()
    n_total = len(sub_df)
    if n_total < 30:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": f"Sample size (N={n_total}) is insufficient for Lee Bounds estimation (minimum 30 required)."
        }

    # Binarize treatment
    t_raw = sub_df[treatment_col].dropna().values
    t_median = np.median(t_raw) if len(t_raw) > 0 else 0.5
    d = (sub_df[treatment_col] > t_median).astype(int).values

    # Determine response indicator R
    if response_col and response_col in sub_df.columns:
        r_raw = sub_df[response_col].values
        r = (r_raw == 1) | (r_raw == True) | (r_raw == '1')
    else:
        # If response_col not explicitly provided, attrition is identified by missing outcome
        r = sub_df[outcome_col].notna().values

    r = r.astype(int)

    # Response rates
    n_t_total = int(np.sum(d == 1))
    n_c_total = int(np.sum(d == 0))

    if n_t_total == 0 or n_c_total == 0:
        return {
            "status": "ERROR",
            "message": "Both treatment and control groups must have at least one observation."
        }

    r_t = float(np.mean(r[d == 1]))
    r_c = float(np.mean(r[d == 0]))

    # Observed outcomes where R=1
    valid_mask = (r == 1) & sub_df[outcome_col].notna()
    y_observed = sub_df.loc[valid_mask, outcome_col].astype(float).values
    d_observed = d[valid_mask]

    y_t = y_observed[d_observed == 1]
    y_c = y_observed[d_observed == 0]

    if len(y_t) < 5 or len(y_c) < 5:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": "Not enough observed respondents with completed survey responses in treatment or control."
        }

    # 1. Naive Complete-Case Estimate (ignoring non-random attrition)
    naive_diff = float(np.mean(y_t) - np.mean(y_c))
    naive_se = float(np.sqrt(np.var(y_t, ddof=1) / len(y_t) + np.var(y_c, ddof=1) / len(y_c)))
    naive_ci_low = float(naive_diff - 1.96 * naive_se)
    naive_ci_high = float(naive_diff + 1.96 * naive_se)
    naive_p = float(2.0 * (1.0 - stats.norm.cdf(abs(naive_diff / (naive_se + 1e-12)))))

    # 2. Unconditional Lee Bounds
    delta_lb, delta_ub, trim_q = _compute_single_cell_lee_bounds(y_t, y_c, r_t, r_c)

    # 3. Covariate-Tightened Lee Bounds (if covariates provided)
    has_covariates = bool(covariate_cols)
    tightened_lb = delta_lb
    tightened_ub = delta_ub

    if has_covariates:
        # Bin first covariate into tertiles or categories
        cov_col = covariate_cols[0]
        cov_vals = sub_df[cov_col].dropna().values
        if len(cov_vals) > 0:
            if len(np.unique(cov_vals)) <= 4:
                strata = sub_df[cov_col].astype(str)
            else:
                strata = pd.qcut(sub_df[cov_col].rank(method='first'), q=3, labels=["Stratum_1", "Stratum_2", "Stratum_3"])
            
            strata_lbs = []
            strata_ubs = []
            strata_weights = []

            for s_val in strata.dropna().unique():
                s_mask = (strata == s_val)
                s_d = d[s_mask]
                s_r = r[s_mask]
                s_valid = (s_mask & valid_mask)
                s_yt = sub_df.loc[s_valid & (d == 1), outcome_col].astype(float).values
                s_yc = sub_df.loc[s_valid & (d == 0), outcome_col].astype(float).values

                if len(s_yt) >= 3 and len(s_yc) >= 3 and np.sum(s_d == 1) > 0 and np.sum(s_d == 0) > 0:
                    s_rt = float(np.mean(s_r[s_d == 1]))
                    s_rc = float(np.mean(s_r[s_d == 0]))
                    s_lb, s_ub, _ = _compute_single_cell_lee_bounds(s_yt, s_yc, s_rt, s_rc)
                    # Weight by proportion of responders in this stratum
                    s_wt = len(s_yt) + len(s_yc)
                    strata_lbs.append(s_lb)
                    strata_ubs.append(s_ub)
                    strata_weights.append(s_wt)

            if strata_weights and sum(strata_weights) > 0:
                weights_arr = np.array(strata_weights, dtype=float) / sum(strata_weights)
                tightened_lb = float(np.sum(np.array(strata_lbs) * weights_arr))
                tightened_ub = float(np.sum(np.array(strata_ubs) * weights_arr))
                # Ensure tightening respects containment
                tightened_lb = max(tightened_lb, delta_lb)
                tightened_ub = min(tightened_ub, delta_ub)

    # 4. Bootstrap Inference for Bounds & Imbens-Manski Confidence Intervals
    boot_lbs = []
    boot_ubs = []
    boot_naives = []

    rng = np.random.RandomState(42)
    indices = np.arange(n_total)

    for _ in range(n_bootstraps):
        b_idx = rng.choice(indices, size=n_total, replace=True)
        b_d = d[b_idx]
        b_r = r[b_idx]
        b_valid = valid_mask[b_idx]
        b_y = sub_df.iloc[b_idx][outcome_col].values

        b_rt = float(np.mean(b_r[b_d == 1])) if np.sum(b_d == 1) > 0 else r_t
        b_rc = float(np.mean(b_r[b_d == 0])) if np.sum(b_d == 0) > 0 else r_c

        b_yt = b_y[b_valid & (b_d == 1)].astype(float)
        b_yc = b_y[b_valid & (b_d == 0)].astype(float)

        if len(b_yt) >= 2 and len(b_yc) >= 2:
            boot_naives.append(float(np.mean(b_yt) - np.mean(b_yc)))
            b_lb, b_ub, _ = _compute_single_cell_lee_bounds(b_yt, b_yc, b_rt, b_rc)
            boot_lbs.append(b_lb)
            boot_ubs.append(b_ub)

    se_lb = float(np.std(boot_lbs, ddof=1)) if len(boot_lbs) > 1 else 0.05
    se_ub = float(np.std(boot_ubs, ddof=1)) if len(boot_ubs) > 1 else 0.05

    # Imbens-Manski critical value
    c_alpha = _compute_imbens_manski_critical_value(delta_lb, delta_ub, se_lb, se_ub, alpha=alpha_level)
    im_ci_low = float(delta_lb - c_alpha * se_lb)
    im_ci_high = float(delta_ub + c_alpha * se_ub)

    # Tightened CI
    c_alpha_tight = _compute_imbens_manski_critical_value(tightened_lb, tightened_ub, se_lb, se_ub, alpha=alpha_level)
    tight_ci_low = float(tightened_lb - c_alpha_tight * se_lb)
    tight_ci_high = float(tightened_ub + c_alpha_tight * se_ub)

    # Zero coverage / statistical significance
    # Bounds strictly rule out zero if [CI_low, CI_high] does not contain 0
    excludes_zero = bool(im_ci_low > 0 or im_ci_high < 0)

    # Generate Scientific SVG Visualization
    svg_chart = _generate_lee_bounds_svg(
        delta_lb=delta_lb, delta_ub=delta_ub, im_ci=(im_ci_low, im_ci_high),
        tight_lb=tightened_lb, tight_ub=tightened_ub, tight_ci=(tight_ci_low, tight_ci_high),
        naive_est=naive_diff, naive_ci=(naive_ci_low, naive_ci_high),
        r_t=r_t, r_c=r_c, trim_q=trim_q,
        has_covariates=has_covariates
    )

    # Academic APA 7th Edition narrative
    trimmed_group_name = "treated" if r_t >= r_c else "control"
    apa_narrative = (
        f"Non-random survey attrition and sample selection were evaluated using sharp non-parametric Lee Bounds (Lee, 2009) "
        f"for outcome '{outcome_col}' under treatment '{treatment_col}' across N = {n_total} surveyed respondents. "
        f"Response rates were {r_t:.1%} in the treatment group (N = {n_t_total}) and {r_c:.1%} in the control group (N = {n_c_total}), "
        f"yielding a differential response rate of {abs(r_t - r_c):.1%} and a trimming proportion of q = {trim_q:.1%} in the {trimmed_group_name} arm. "
        f"The naive complete-case estimate unadjusted for selective attrition was Δ = {naive_diff:.4f} (95% CI [{naive_ci_low:.4f}, {naive_ci_high:.4f}]). "
        f"In contrast, the sharp unconditional Lee bounds on the average treatment effect for always-reporters were "
        f"[{delta_lb:.4f}, {delta_ub:.4f}], with Imbens-Manski (2004) 95% confidence interval [{im_ci_low:.4f}, {im_ci_high:.4f}]. "
    )
    if has_covariates:
        apa_narrative += (
            f"Conditioning on baseline covariates ({', '.join(covariate_cols)}) tightened the bounds to "
            f"[{tightened_lb:.4f}, {tightened_ub:.4f}] (Tightened 95% CI [{tight_ci_low:.4f}, {tight_ci_high:.4f}]). "
        )
    if excludes_zero:
        apa_narrative += "Because the 95% confidence interval strictly excludes zero, the causal treatment effect is robust to non-random attrition."
    else:
        apa_narrative += "Because the 95% confidence interval includes zero, selective attrition cannot be ruled out as an alternative explanation for observed differences."

    return {
        "status": "SUCCESS",
        "model_type": "LEE_BOUNDS_RESTUD_2009",
        "sample_size": n_total,
        "observed_sample_size": len(y_observed),
        "bootstrap_replications": n_bootstraps,
        "response_rates": {
            "treated_response_rate": round(r_t, 4),
            "control_response_rate": round(r_c, 4),
            "differential_response_rate": round(abs(r_t - r_c), 4),
            "trimming_fraction_q": round(trim_q, 4),
            "trimmed_group": trimmed_group_name
        },
        "bounds": {
            "unconditional": {
                "lower_bound": round(delta_lb, 4),
                "upper_bound": round(delta_ub, 4),
                "se_lower": round(se_lb, 4),
                "se_upper": round(se_ub, 4),
                "im_critical_value": round(c_alpha, 3),
                "ci_lower": round(im_ci_low, 4),
                "ci_upper": round(im_ci_high, 4),
                "excludes_zero": excludes_zero
            },
            "covariate_tightened": {
                "lower_bound": round(tightened_lb, 4),
                "upper_bound": round(tightened_ub, 4),
                "ci_lower": round(tight_ci_low, 4),
                "ci_upper": round(tight_ci_high, 4),
                "is_available": has_covariates
            }
        },
        "naive_complete_case": {
            "estimate": round(naive_diff, 4),
            "std_error": round(naive_se, 4),
            "ci_lower": round(naive_ci_low, 4),
            "ci_upper": round(naive_ci_high, 4),
            "p_value": round(naive_p, 4)
        },
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_lee_bounds_svg(
    delta_lb: float, delta_ub: float, im_ci: tuple,
    tight_lb: float, tight_ub: float, tight_ci: tuple,
    naive_est: float, naive_ci: tuple,
    r_t: float, r_c: float, trim_q: float,
    has_covariates: bool
) -> str:
    """
    Constructs a dual-panel SVG visualizer:
    - Panel A: Forest Plot of Treatment Effect Bounds (Naive vs Unconditional vs Tightened) with 95% CIs.
    - Panel B: Attrition & Trimming Breakdown (Response rates, excess response q).
    """
    svg_w, svg_h = 760, 320

    # Bounds scale for Panel A (x spans from 40 to 390)
    all_vals = [delta_lb, delta_ub, im_ci[0], im_ci[1], naive_est, naive_ci[0], naive_ci[1], 0.0]
    if has_covariates:
        all_vals.extend([tight_lb, tight_ub, tight_ci[0], tight_ci[1]])

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
        '  <text x="40" y="32" font-size="13" font-weight="700" fill="#1e293b">PANEL A: Sharp Bounds vs Naive Estimate (95% CI)</text>',
        '  <text x="40" y="48" font-size="11" fill="#64748b">Lee (2009) Non-parametric Trimming Bounds under Attrition</text>',
        '  <!-- Panel B Header -->',
        '  <text x="440" y="32" font-size="13" font-weight="700" fill="#1e293b">PANEL B: Survey Response Rates &amp; Trimming</text>',
        f'  <text x="440" y="48" font-size="11" fill="#64748b">Trimming Fraction q = {trim_q:.1%} in Group with Higher Retention</text>',
        '  <line x1="415" y1="20" x2="415" y2="300" stroke="#e2e8f0" stroke-dasharray="4 4" stroke-width="1.5" />'
    ]

    # Panel A: Zero reference line
    svg_lines.append(f'  <line x1="{zero_x:.1f}" y1="65" x2="{zero_x:.1f}" y2="250" stroke="#94a3b8" stroke-dasharray="2 2" stroke-width="1.5" />')
    svg_lines.append(f'  <text x="{zero_x:.1f}" y="265" font-size="10" fill="#64748b" text-anchor="middle">Null (0.0)</text>')

    # Row 1: Naive Complete Case
    y_r1 = 95
    x_naive = to_fp_x(naive_est)
    x_n_low = to_fp_x(naive_ci[0])
    x_n_high = to_fp_x(naive_ci[1])
    svg_lines.append(f'  <text x="40" y="{y_r1 - 12}" font-size="11" font-weight="600" fill="#f59e0b">Naive (Complete-Case Only)</text>')
    svg_lines.append(f'  <line x1="{x_n_low:.1f}" y1="{y_r1}" x2="{x_n_high:.1f}" y2="{y_r1}" stroke="#f59e0b" stroke-width="2.5" />')
    svg_lines.append(f'  <circle cx="{x_naive:.1f}" cy="{y_r1}" r="5" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5" />')
    svg_lines.append(f'  <text x="{x_n_high + 8:.1f}" y="{y_r1 + 4}" font-size="10" font-weight="600" fill="#f59e0b">{naive_est:.2f}</text>')

    # Row 2: Unconditional Lee Bounds
    y_r2 = 160
    x_lb = to_fp_x(delta_lb)
    x_ub = to_fp_x(delta_ub)
    x_im_low = to_fp_x(im_ci[0])
    x_im_high = to_fp_x(im_ci[1])
    svg_lines.append(f'  <text x="40" y="{y_r2 - 12}" font-size="11" font-weight="600" fill="#4f46e5">Sharp Lee Bounds (Unconditional)</text>')
    # Imbens-Manski CI thin line
    svg_lines.append(f'  <line x1="{x_im_low:.1f}" y1="{y_r2}" x2="{x_im_high:.1f}" y2="{y_r2}" stroke="#818cf8" stroke-width="1.5" stroke-dasharray="3 2" />')
    svg_lines.append(f'  <line x1="{x_im_low:.1f}" y1="{y_r2 - 4}" x2="{x_im_low:.1f}" y2="{y_r2 + 4}" stroke="#818cf8" stroke-width="1.5" />')
    svg_lines.append(f'  <line x1="{x_im_high:.1f}" y1="{y_r2 - 4}" x2="{x_im_high:.1f}" y2="{y_r2 + 4}" stroke="#818cf8" stroke-width="1.5" />')
    # Point identified interval (thick band)
    svg_lines.append(f'  <rect x="{x_lb:.1f}" y="{y_r2 - 5}" width="{max(x_ub - x_lb, 2.0):.1f}" height="10" fill="#4f46e5" rx="3" />')
    svg_lines.append(f'  <text x="{x_im_high + 8:.1f}" y="{y_r2 + 4}" font-size="10" font-weight="600" fill="#4f46e5">[{delta_lb:.2f}, {delta_ub:.2f}]</text>')

    # Row 3: Tightened Lee Bounds (or placeholder)
    y_r3 = 225
    if has_covariates:
        x_t_lb = to_fp_x(tight_lb)
        x_t_ub = to_fp_x(tight_ub)
        x_t_low = to_fp_x(tight_ci[0])
        x_t_high = to_fp_x(tight_ci[1])
        svg_lines.append(f'  <text x="40" y="{y_r3 - 12}" font-size="11" font-weight="600" fill="#10b981">Tightened Lee Bounds (Covariates)</text>')
        svg_lines.append(f'  <line x1="{x_t_low:.1f}" y1="{y_r3}" x2="{x_t_high:.1f}" y2="{y_r3}" stroke="#34d399" stroke-width="1.5" stroke-dasharray="3 2" />')
        svg_lines.append(f'  <rect x="{x_t_lb:.1f}" y="{y_r3 - 5}" width="{max(x_t_ub - x_t_lb, 2.0):.1f}" height="10" fill="#10b981" rx="3" />')
        svg_lines.append(f'  <text x="{x_t_high + 8:.1f}" y="{y_r3 + 4}" font-size="10" font-weight="600" fill="#10b981">[{tight_lb:.2f}, {tight_ub:.2f}]</text>')
    else:
        svg_lines.append(f'  <text x="40" y="{y_r3}" font-size="10" fill="#94a3b8" italic="true">Chưa chọn biến kiểm soát để thắt chặt cận (Tightening Covariates)</text>')

    # Panel B: Response Rates Comparison
    p2_x, p2_y, p2_w, p2_h = 440, 80, 280, 180
    bar_h = 24

    # Treated Response Bar
    svg_lines.append(f'  <text x="{p2_x}" y="{p2_y}" font-size="11" font-weight="600" fill="#334155">Treated Retention: P(R=1|T=1)</text>')
    svg_lines.append(f'  <rect x="{p2_x}" y="{p2_y + 8}" width="{p2_w}" height="{bar_h}" fill="#e2e8f0" rx="4" />')
    svg_lines.append(f'  <rect x="{p2_x}" y="{p2_y + 8}" width="{p2_w * r_t:.1f}" height="{bar_h}" fill="#6366f1" rx="4" />')
    svg_lines.append(f'  <text x="{p2_x + p2_w * r_t - 8:.1f}" y="{p2_y + 24}" font-size="10" font-weight="700" fill="#ffffff" text-anchor="end">{r_t:.1%}</text>')

    # Control Response Bar
    y_c_bar = p2_y + 55
    svg_lines.append(f'  <text x="{p2_x}" y="{y_c_bar}" font-size="11" font-weight="600" fill="#334155">Control Retention: P(R=1|T=0)</text>')
    svg_lines.append(f'  <rect x="{p2_x}" y="{y_c_bar + 8}" width="{p2_w}" height="{bar_h}" fill="#e2e8f0" rx="4" />')
    svg_lines.append(f'  <rect x="{p2_x}" y="{y_c_bar + 8}" width="{p2_w * r_c:.1f}" height="{bar_h}" fill="#94a3b8" rx="4" />')
    svg_lines.append(f'  <text x="{p2_x + p2_w * r_c - 8:.1f}" y="{y_c_bar + 24}" font-size="10" font-weight="700" fill="#ffffff" text-anchor="end">{r_c:.1%}</text>')

    # Trimming fraction info box
    y_info = p2_y + 115
    svg_lines.append(f'  <rect x="{p2_x}" y="{y_info}" width="{p2_w}" height="55" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1" rx="6" />')
    svg_lines.append(f'  <text x="{p2_x + 12}" y="{y_info + 20}" font-size="11" font-weight="700" fill="#0f172a">Trimming Ratio (q): {trim_q:.1%}</text>')
    svg_lines.append(f'  <text x="{p2_x + 12}" y="{y_info + 38}" font-size="10" fill="#64748b">Cắt {trim_q:.1%} đuôi phân phối để triệt tiêu chệch hao hụt mẫu</text>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)
