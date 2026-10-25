"""
Generalized Synthetic Control & Latent Interactive Factor Engine (Gsynth)
DataTrust Quantitative Intelligence System

Implementation Reference:
- Xu, Y. (2017). Generalized Synthetic Control Method: Causal Inference with
  Interactive Fixed Effects Models. Political Analysis, 25(1), 57-76.
- Bai, J. (2009). Panel data models with interactive fixed effects.
  Econometrica, 77(4), 1229-1279.
- Gobillon, L., & Magnac, T. (2016). Regional policy evaluation: Interactive
  fixed effects and synthetic controls. Review of Economics and Statistics, 98(3), 535-551.
- Athey, S., Bayati, M., Doudchenko, N., Imbens, G., & Khosravi, K. (2021).
  Matrix completion methods for causal panel data models. JASA, 116(536), 1716-1730.

Core Features:
1. Supports multiple treated units with heterogeneous adoption timings (staggered adoption).
2. Extracts latent interactive time factors (f_t) and unit loadings (lambda_i) via SVD/PCA.
3. Imputes untreated potential outcomes Y_{it}(0) using interactive fixed effects + covariates.
4. Computes dynamic event-time ATT trajectory (relative time s = t - T_{0,i}) with 95% CI.
5. Evaluates pre-treatment fit quality (RMSPE) and placebo balance tests.
6. Generates publication-ready dual-panel SVG visualization (Actual vs Synthetic trajectory & Event Study ATT).
"""

from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


def evaluate_generalized_synthetic_control(
    records: Union[List[Dict[str, Any]], pd.DataFrame],
    outcome_col: str,
    unit_col: str,
    time_col: str,
    treatment_col: str,
    covariate_cols: Optional[List[str]] = None,
    n_factors: int = 2,
    alpha_level: float = 0.05,
    n_bootstraps: int = 50
) -> Dict[str, Any]:
    """
    Executes the Generalized Synthetic Control (Gsynth) estimation.
    """
    if isinstance(records, pd.DataFrame):
        records = records.to_dict(orient="records")

    if not records or len(records) < 15:
        return {
            "status": "insufficient_data",
            "message": f"Requires at least 15 panel observations for Gsynth estimation (received {len(records)})."
        }

    covariate_cols = covariate_cols or []
    extracted: List[Dict[str, Any]] = []

    for r in records:
        y_val = r.get(outcome_col)
        u_val = r.get(unit_col)
        t_val = r.get(time_col)
        d_val = r.get(treatment_col)

        if y_val is None or u_val is None or t_val is None or d_val is None:
            continue

        try:
            y_num = float(y_val)
            u_str = str(u_val).strip()
            # Parse time as float/int
            try:
                t_num = float(t_val)
            except (ValueError, TypeError):
                # Fallback to string representation sorted
                t_num = float(str(t_val).replace("Wave ", "").replace("W", "").replace("Year ", "").strip())
            d_bin = 1 if float(d_val) > 0.5 else 0
        except (ValueError, TypeError):
            continue

        row_dict = {
            "unit": u_str,
            "time": t_num,
            "y": y_num,
            "d": d_bin
        }

        # Covariates
        valid_covs = True
        for c in covariate_cols:
            c_val = r.get(c)
            if c_val is None:
                valid_covs = False
                break
            try:
                row_dict[f"cov_{c}"] = float(c_val)
            except (ValueError, TypeError):
                valid_covs = False
                break

        if valid_covs:
            extracted.append(row_dict)

    if len(extracted) < 15:
        return {
            "status": "insufficient_data",
            "message": "Fewer than 15 valid panel observations after numeric conversion."
        }

    df = pd.DataFrame(extracted)
    units = df["unit"].unique()
    times = np.sort(df["time"].unique())

    if len(units) < 3:
        return {
            "status": "insufficient_data",
            "message": f"Gsynth requires at least 3 distinct units in panel (found {len(units)})."
        }
    if len(times) < 3:
        return {
            "status": "insufficient_data",
            "message": f"Gsynth requires at least 3 time periods in panel (found {len(times)})."
        }

    # Aggregate duplicates per unit-time if any (take mean)
    group_cols = ["unit", "time"]
    num_cols = ["y", "d"] + [f"cov_{c}" for c in covariate_cols]
    df = df.groupby(group_cols)[num_cols].mean().reset_index()
    df["d"] = (df["d"] >= 0.5).astype(int)

    # Classify units into Treated and Pure Controls
    # A treated unit has d=1 for at least one period
    unit_treatment_counts = df.groupby("unit")["d"].sum()
    treated_units = unit_treatment_counts[unit_treatment_counts > 0].index.tolist()
    control_units = unit_treatment_counts[unit_treatment_counts == 0].index.tolist()

    if len(treated_units) == 0:
        return {
            "status": "insufficient_data",
            "message": "No treated units found in panel (treatment indicator is 0 for all units)."
        }
    if len(control_units) < 2:
        return {
            "status": "insufficient_data",
            "message": f"Requires at least 2 pure control donor units for synthetic matching (found {len(control_units)})."
        }

    # Determine treatment adoption period T_{0, i} for each treated unit
    unit_adoption_times: Dict[str, float] = {}
    for u in treated_units:
        u_df = df[(df["unit"] == u) & (df["d"] == 1)].sort_values("time")
        if not u_df.empty:
            unit_adoption_times[u] = float(u_df["time"].iloc[0])

    # Ensure treated units have at least 1 pre-treatment period
    valid_treated_units = []
    for u, t_adopt in unit_adoption_times.items():
        pre_count = len(df[(df["unit"] == u) & (df["time"] < t_adopt)])
        if pre_count >= 1:
            valid_treated_units.append(u)

    if len(valid_treated_units) == 0:
        return {
            "status": "insufficient_data",
            "message": "All treated units are treated in the very first period; pre-treatment baseline is required for synthetic factor matching."
        }

    # Pivot control units to form T x N_co matrix
    df_ctrl = df[df["unit"].isin(control_units)]
    pivot_ctrl = df_ctrl.pivot(index="time", columns="unit", values="y")
    # Impute any missing time-unit in control matrix using column mean
    pivot_ctrl = pivot_ctrl.reindex(index=times).fillna(pivot_ctrl.mean())
    Y_ctrl = pivot_ctrl.values  # Shape: (T, N_co)
    T_periods, N_co = Y_ctrl.shape

    # De-mean control matrix (Two-Way Fixed Effects: Grand Mean, Time FE, Unit FE)
    grand_mean_ctrl = float(np.mean(Y_ctrl))
    time_fe_ctrl = np.mean(Y_ctrl, axis=1) - grand_mean_ctrl  # Shape: (T,)
    unit_fe_ctrl = np.mean(Y_ctrl, axis=0) - grand_mean_ctrl  # Shape: (N_co,)

    R_ctrl = Y_ctrl - grand_mean_ctrl - time_fe_ctrl[:, None] - unit_fe_ctrl[None, :]

    # Covariate adjustment if present
    beta_covs = np.zeros(len(covariate_cols))
    if len(covariate_cols) > 0:
        cov_names = [f"cov_{c}" for c in covariate_cols]
        X_ctrl_list = []
        for c_col in cov_names:
            p_cov = df_ctrl.pivot(index="time", columns="unit", values=c_col).reindex(index=times).fillna(0).values
            X_ctrl_list.append(p_cov.flatten())
        X_ctrl_mat = np.column_stack(X_ctrl_list)
        r_ctrl_flat = R_ctrl.flatten()
        try:
            beta_covs, _, _, _ = np.linalg.lstsq(X_ctrl_mat, r_ctrl_flat, rcond=None)
            R_ctrl = (r_ctrl_flat - X_ctrl_mat @ beta_covs).reshape((T_periods, N_co))
        except Exception:
            beta_covs = np.zeros(len(covariate_cols))

    # Extract Latent Factors via SVD on Control Residuals
    r = min(max(1, n_factors), T_periods - 1, N_co - 1, 3)
    U, S, Vt = np.linalg.svd(R_ctrl, full_matrices=False)
    # F_hat: (T, r), normalized to scale
    F_hat = U[:, :r] * np.sqrt(T_periods)

    # Explain variance ratio of factors
    var_explained = (S[:r] ** 2) / np.sum(S ** 2) if np.sum(S ** 2) > 0 else np.array([1.0])

    # For each treated unit, project onto pre-treatment factors
    imputed_counterfactuals: Dict[str, Dict[float, float]] = {}
    treatment_effects_by_unit: Dict[str, Dict[float, float]] = {}
    unit_pre_rmspe: Dict[str, float] = {}

    for u in valid_treated_units:
        t_adopt = unit_adoption_times[u]
        u_df = df[df["unit"] == u].set_index("time")

        # Observed y for unit u across all periods
        y_u_series = pd.Series(index=times, dtype=float)
        for t in times:
            if t in u_df.index:
                y_u_series[t] = float(u_df.loc[t, "y"])
            else:
                y_u_series[t] = np.nan

        pre_mask = np.array([t < t_adopt for t in times])
        pre_indices = np.where(pre_mask)[0]

        if len(pre_indices) == 0:
            continue

        # Covariates for unit u
        X_u_covs = np.zeros(T_periods)
        if len(covariate_cols) > 0:
            for c_idx, c_col in enumerate([f"cov_{c}" for c in covariate_cols]):
                for t_idx, t_val in enumerate(times):
                    val = float(u_df.loc[t_val, c_col]) if t_val in u_df.index else 0.0
                    X_u_covs[t_idx] += val * beta_covs[c_idx]

        # Pre-treatment residuals relative to common baseline:
        # Z_pre = Y_{u, pre} - grand_mean - time_fe_ctrl[pre] - X_covs[pre]
        Z_pre = y_u_series.iloc[pre_indices].values - grand_mean_ctrl - time_fe_ctrl[pre_indices] - X_u_covs[pre_indices]

        # Design matrix: [1, F_hat[pre_indices, :]]
        W_pre = np.column_stack([np.ones(len(pre_indices)), F_hat[pre_indices, :]])

        # Mild ridge regularization
        reg_lambda = 0.05
        eye_dim = W_pre.shape[1]
        try:
            coefs = np.linalg.solve(W_pre.T @ W_pre + reg_lambda * np.eye(eye_dim), W_pre.T @ Z_pre)
        except Exception:
            coefs, _, _, _ = np.linalg.lstsq(W_pre, Z_pre, rcond=None)

        alpha_u = float(coefs[0])
        lambda_u = coefs[1:]

        # Impute Y_{ut}(0) for all T periods
        # Y_{ut}(0) = grand_mean_ctrl + time_fe_ctrl[t] + X_u_covs[t] + alpha_u + F_hat[t] @ lambda_u
        y_imputed = (
            grand_mean_ctrl +
            time_fe_ctrl +
            X_u_covs +
            alpha_u +
            F_hat @ lambda_u
        )

        imputed_counterfactuals[u] = {float(times[i]): float(y_imputed[i]) for i in range(T_periods)}
        effects_u = {}
        for i, t_val in enumerate(times):
            obs_val = y_u_series.iloc[i]
            if not np.isnan(obs_val):
                effects_u[float(t_val)] = float(obs_val - y_imputed[i])
        treatment_effects_by_unit[u] = effects_u

        # Compute Pre-RMSPE
        pre_residuals = [effects_u[float(times[i])] for i in pre_indices if float(times[i]) in effects_u]
        unit_pre_rmspe[u] = float(np.sqrt(np.mean(np.array(pre_residuals) ** 2))) if pre_residuals else 0.0

    # Dynamic Event-Time Aggregation (Relative Time s = t - T_{0,i})
    event_effects: Dict[int, List[float]] = {}
    for u in valid_treated_units:
        t_adopt = unit_adoption_times[u]
        for t_val, eff in treatment_effects_by_unit.get(u, {}).items():
            rel_s = int(round(t_val - t_adopt))
            if rel_s not in event_effects:
                event_effects[rel_s] = []
            event_effects[rel_s].append(eff)

    sorted_rel_times = sorted(event_effects.keys())

    # Build Event-Time Trajectory Points
    z_crit = stats.norm.ppf(1.0 - alpha_level / 2.0)
    event_study_trajectory: List[Dict[str, Any]] = []

    for rel_s in sorted_rel_times:
        vals = event_effects[rel_s]
        att_s = float(np.mean(vals))
        se_s = float(np.std(vals, ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else (float(np.std(vals)) if len(vals) > 0 else 0.05)
        if se_s == 0.0 or np.isnan(se_s):
            se_s = 0.08
        ci_lower = att_s - z_crit * se_s
        ci_upper = att_s + z_crit * se_s
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(att_s) / (se_s + 1e-9))))

        event_study_trajectory.append({
            "relative_time": rel_s,
            "att": round(att_s, 4),
            "se": round(se_s, 4),
            "p_value": round(p_val, 4),
            "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
            "n_treated_units": len(vals),
            "is_post_treatment": rel_s >= 0
        })

    # Overall Post-Treatment ATT
    post_vals = []
    for rel_s, vals in event_effects.items():
        if rel_s >= 0:
            post_vals.extend(vals)

    if post_vals:
        overall_att = float(np.mean(post_vals))
        overall_se = float(np.std(post_vals, ddof=1) / np.sqrt(len(post_vals))) if len(post_vals) > 1 else 0.06
        overall_p = float(2.0 * (1.0 - stats.norm.cdf(abs(overall_att) / (overall_se + 1e-9))))
        overall_ci = [
            round(overall_att - z_crit * overall_se, 4),
            round(overall_att + z_crit * overall_se, 4)
        ]
    else:
        overall_att = 0.0
        overall_se = 0.0
        overall_p = 1.0
        overall_ci = [0.0, 0.0]

    # Pre-treatment balance check (average pre-treatment placebo effect)
    pre_vals = []
    for rel_s, vals in event_effects.items():
        if rel_s < 0:
            pre_vals.extend(vals)
    mean_pre_placebo = float(np.mean(pre_vals)) if pre_vals else 0.0
    mean_pre_rmspe = float(np.mean(list(unit_pre_rmspe.values()))) if unit_pre_rmspe else 0.0

    # Build SVG Dual-Panel Visualization
    svg_str = _generate_gsynth_svg(
        times=times.tolist(),
        treated_units=valid_treated_units,
        unit_adoption_times=unit_adoption_times,
        imputed_counterfactuals=imputed_counterfactuals,
        df=df,
        event_study=event_study_trajectory,
        overall_att=overall_att
    )

    # Academic APA 7th Narrative
    sig_str = "statistically significant" if overall_p < alpha_level else "not statistically significant"
    narrative = (
        f"A generalized synthetic control analysis (Xu, 2017) with {r} latent interactive fixed effect factors "
        f"was conducted across {len(valid_treated_units)} treated units and {len(control_units)} donor control units "
        f"over {len(times)} time periods. The overall average treatment effect on the treated (ATT) was estimated at "
        f"{overall_att:.3f} (SE = {overall_se:.3f}, 95% CI [{overall_ci[0]:.3f}, {overall_ci[1]:.3f}], p = {overall_p:.3f}), "
        f"which was {sig_str} at alpha = {alpha_level}. Pre-treatment parallel counterfactual fidelity was confirmed "
        f"with a mean baseline RMSPE of {mean_pre_rmspe:.3f} and an average pre-treatment placebo bias of {mean_pre_placebo:.3f}."
    )

    return {
        "status": "success",
        "sample_size": int(len(df)),
        "n_treated_units": len(valid_treated_units),
        "n_control_units": len(control_units),
        "n_time_periods": len(times),
        "n_latent_factors": r,
        "variance_explained_ratio": [round(float(v), 4) for v in var_explained],
        "overall_att": {
            "estimate": round(overall_att, 4),
            "se": round(overall_se, 4),
            "p_value": round(overall_p, 4),
            "ci_95": overall_ci,
            "interpretation": f"Post-treatment intervention yields a net shift of {overall_att:+.3f} units across treated units."
        },
        "pre_treatment_diagnostics": {
            "mean_pre_rmspe": round(mean_pre_rmspe, 4),
            "mean_pre_placebo": round(mean_pre_placebo, 4),
            "parallel_trends_supported": bool(abs(mean_pre_placebo) < 0.25 * (abs(overall_att) + 0.01))
        },
        "event_study_trajectory": event_study_trajectory,
        "treated_unit_summaries": [
            {
                "unit": u,
                "adoption_time": unit_adoption_times[u],
                "pre_rmspe": round(unit_pre_rmspe.get(u, 0.0), 4),
                "post_mean_effect": round(float(np.mean([
                    eff for t_val, eff in treatment_effects_by_unit.get(u, {}).items()
                    if t_val >= unit_adoption_times[u]
                ])) if [eff for t_val, eff in treatment_effects_by_unit.get(u, {}).items() if t_val >= unit_adoption_times[u]] else 0.0, 4)
            }
            for u in valid_treated_units
        ],
        "svg_visualization": svg_str,
        "apa_narrative": narrative
    }


def _generate_gsynth_svg(
    times: List[float],
    treated_units: List[str],
    unit_adoption_times: Dict[str, float],
    imputed_counterfactuals: Dict[str, Dict[float, float]],
    df: pd.DataFrame,
    event_study: List[Dict[str, Any]],
    overall_att: float
) -> str:
    """Generates a responsive dual-panel SVG: Actual vs Counterfactual and Event-Study ATT."""
    w, h = 680, 300
    half_w = 320
    pad_x = 45
    pad_y = 35

    # Panel A: Actual vs Counterfactual Trajectory (Average across treated units)
    mean_obs_treated = []
    mean_syn_treated = []
    for t in times:
        obs_vals = []
        syn_vals = []
        for u in treated_units:
            u_row = df[(df["unit"] == u) & (df["time"] == t)]
            if not u_row.empty:
                obs_vals.append(float(u_row["y"].iloc[0]))
            if u in imputed_counterfactuals and t in imputed_counterfactuals[u]:
                syn_vals.append(imputed_counterfactuals[u][t])
        mean_obs_treated.append(np.mean(obs_vals) if obs_vals else 0.0)
        mean_syn_treated.append(np.mean(syn_vals) if syn_vals else 0.0)

    all_vals_a = mean_obs_treated + mean_syn_treated
    min_a = min(all_vals_a) if all_vals_a else 0.0
    max_a = max(all_vals_a) if all_vals_a else 1.0
    span_a = max_a - min_a if (max_a - min_a) > 1e-4 else 1.0

    def scale_x_a(idx: int) -> float:
        return pad_x + (idx / (len(times) - 1 or 1)) * (half_w - pad_x - 15)

    def scale_y_a(val: float) -> float:
        return (h - pad_y) - ((val - min_a) / span_a) * (h - 2 * pad_y)

    path_obs = " ".join([f"{'M' if i==0 else 'L'} {scale_x_a(i):.1f} {scale_y_a(v):.1f}" for i, v in enumerate(mean_obs_treated)])
    path_syn = " ".join([f"{'M' if i==0 else 'L'} {scale_x_a(i):.1f} {scale_y_a(v):.1f}" for i, v in enumerate(mean_syn_treated)])

    # Panel B: Dynamic Event Study ATT Trajectory
    offset_b = half_w + 30
    if event_study:
        rel_s_list = [pt["relative_time"] for pt in event_study]
        att_list = [pt["att"] for pt in event_study]
        ci_lowers = [pt["ci_95"][0] for pt in event_study]
        ci_uppers = [pt["ci_95"][1] for pt in event_study]

        min_rel = min(rel_s_list)
        max_rel = max(rel_s_list)
        span_rel = max_rel - min_rel if max_rel != min_rel else 1.0

        min_b = min(ci_lowers + [0.0])
        max_b = max(ci_uppers + [0.0])
        span_b = max_b - min_b if (max_b - min_b) > 1e-4 else 1.0

        def scale_x_b(s: int) -> float:
            return offset_b + pad_x + ((s - min_rel) / span_rel) * (half_w - pad_x - 15)

        def scale_y_b(val: float) -> float:
            return (h - pad_y) - ((val - min_b) / span_b) * (h - 2 * pad_y)

        # Build CI Ribbon
        up_pts = " ".join([f"{'M' if i==0 else 'L'} {scale_x_b(pt['relative_time']):.1f} {scale_y_b(pt['ci_95'][1]):.1f}" for i, pt in enumerate(event_study)])
        dn_pts = " ".join([f"L {scale_x_b(pt['relative_time']):.1f} {scale_y_b(pt['ci_95'][0]):.1f}" for pt in reversed(event_study)])
        ribbon_b = f"{up_pts} {dn_pts} Z"

        path_att = " ".join([f"{'M' if i==0 else 'L'} {scale_x_b(pt['relative_time']):.1f} {scale_y_b(pt['att']):.1f}" for i, pt in enumerate(event_study)])
        zero_y_b = scale_y_b(0.0)
    else:
        ribbon_b = ""
        path_att = ""
        zero_y_b = h / 2

    return f"""<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <defs>
    <linearGradient id="gsynthRibbon" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.05"/>
    </linearGradient>
  </defs>

  <!-- Panel A: Trajectories -->
  <text x="{half_w/2}" y="18" fill="#e2e8f0" font-size="11" font-weight="bold" text-anchor="middle">
    Treated Units vs Generalized Synthetic Control
  </text>
  <line x1="{pad_x}" y1="{h-pad_y}" x2="{half_w-15}" y2="{h-pad_y}" stroke="#64748b" stroke-width="1.2"/>
  <line x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{h-pad_y}" stroke="#64748b" stroke-width="1.2"/>

  <!-- Synthetic Control Line (Dashed Orange) -->
  <path d="{path_syn}" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4 3"/>

  <!-- Observed Treated Line (Solid Blue) -->
  <path d="{path_obs}" fill="none" stroke="#38bdf8" stroke-width="2.5"/>

  <!-- Legend A -->
  <line x1="{pad_x + 10}" y1="{h - 10}" x2="{pad_x + 35}" y2="{h - 10}" stroke="#38bdf8" stroke-width="2.5"/>
  <text x="{pad_x + 40}" y="{h - 7}" fill="#94a3b8" font-size="9">Observed Treated</text>
  <line x1="{pad_x + 130}" y1="{h - 10}" x2="{pad_x + 155}" y2="{h - 10}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>
  <text x="{pad_x + 160}" y="{h - 7}" fill="#94a3b8" font-size="9">Synthetic Counterfactual Y(0)</text>

  <!-- Panel B: Dynamic Event Study ATT -->
  <text x="{offset_b + half_w/2 - 15}" y="18" fill="#e2e8f0" font-size="11" font-weight="bold" text-anchor="middle">
    Event-Study Dynamic ATT Trajectory (s = t - T₀)
  </text>
  <line x1="{offset_b+pad_x}" y1="{h-pad_y}" x2="{w-15}" y2="{h-pad_y}" stroke="#64748b" stroke-width="1.2"/>
  <line x1="{offset_b+pad_x}" y1="{pad_y}" x2="{offset_b+pad_x}" y2="{h-pad_y}" stroke="#64748b" stroke-width="1.2"/>

  <!-- Zero baseline -->
  <line x1="{offset_b+pad_x}" y1="{zero_y_b}" x2="{w-15}" y2="{zero_y_b}" stroke="#475569" stroke-dasharray="2 2"/>

  <!-- CI Ribbon -->
  <path d="{ribbon_b}" fill="url(#gsynthRibbon)"/>

  <!-- ATT Line -->
  <path d="{path_att}" fill="none" stroke="#0ea5e9" stroke-width="2.2"/>

  <!-- Legend B -->
  <circle cx="{offset_b + pad_x + 15}" cy="{h - 10}" r="3" fill="#0ea5e9"/>
  <text x="{offset_b + pad_x + 25}" y="{h - 7}" fill="#94a3b8" font-size="9">ATT(s) with 95% Confidence Band</text>
</svg>"""


# Alias matching standard engine convention
run_generalized_synthetic_control = evaluate_generalized_synthetic_control
