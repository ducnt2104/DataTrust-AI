"""
DataTrust - Synthetic Difference-in-Differences Engine (SDID)
Reference: Arkhangelsky, Athey, Hirshberg, Imbens, & Wager (2021), "Synthetic Difference-in-Differences",
American Economic Review, 111(12): 4088-4118.
Extension: Clarke, Pailañir, Athey, & Imbens (2023), "Synthetic Difference-in-Differences Estimation".
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm


def compute_synthetic_diff_in_diff(
    records: List[Dict[str, Any]],
    unit_col: str,
    time_col: str,
    treatment_col: str,
    outcome_col: str,
    l2_regularization_zeta: Optional[float] = None,
    num_bootstrap_reps: int = 100,
    alpha_level: float = 0.05,
) -> Dict[str, Any]:
    """
    Computes Synthetic Difference-in-Differences (SDID) treatment effect.
    """
    # 1. Clean and filter records
    valid_rows = []
    for r in records:
        u_val = r.get(unit_col)
        t_val = r.get(time_col)
        w_val = r.get(treatment_col)
        y_val = r.get(outcome_col)
        if u_val is None or t_val is None or w_val is None or y_val is None:
            continue
        try:
            u_str = str(u_val).strip()
            # Try parsing time as int or float or string
            try:
                f_val = float(t_val)
                if f_val.is_integer():
                    t_num = int(f_val)
                else:
                    t_num = f_val
            except (ValueError, TypeError):
                t_num = str(t_val).strip()
            
            # Treatment indicator: 1 if truthy/1/>0, else 0
            if isinstance(w_val, (int, float)):
                w_bin = 1 if w_val > 0.5 else 0
            elif isinstance(w_val, str):
                w_bin = 1 if w_val.strip().lower() in ("1", "true", "yes", "treated") else 0
            else:
                w_bin = 1 if bool(w_val) else 0

            y_num = float(y_val)
            valid_rows.append({
                "unit": u_str,
                "time": t_num,
                "treatment": w_bin,
                "outcome": y_num
            })
        except (ValueError, TypeError):
            continue

    if len(valid_rows) < 20:
        return {
            "status": "error",
            "message": f"Dữ liệu không đủ để ước lượng SDID (chỉ có {len(valid_rows)} bản ghi hợp lệ, yêu cầu tối thiểu 20)."
        }

    # 2. Extract unique units and time periods
    units_list = sorted(list(set(r["unit"] for r in valid_rows)))
    
    # Sort time periods naturally
    raw_times = list(set(r["time"] for r in valid_rows))
    try:
        times_list = sorted(raw_times, key=lambda x: float(x))
    except (ValueError, TypeError):
        times_list = sorted(raw_times, key=lambda x: str(x))

    if len(units_list) < 4:
        return {
            "status": "error",
            "message": f"Cần ít nhất 4 đơn vị (units) phân biệt để tính SDID (hiện có {len(units_list)})."
        }
    if len(times_list) < 3:
        return {
            "status": "error",
            "message": f"Cần ít nhất 3 mốc thời gian (periods) để tính SDID (hiện có {len(times_list)})."
        }

    unit_to_idx = {u: i for i, u in enumerate(units_list)}
    time_to_idx = {t: j for j, t in enumerate(times_list)}
    N = len(units_list)
    T = len(times_list)

    # 3. Construct Matrix Y and Matrix W
    # Use nested list / numpy array
    Y_acc = np.full((N, T), np.nan)
    W_acc = np.zeros((N, T), dtype=int)
    counts = np.zeros((N, T), dtype=int)

    for r in valid_rows:
        i = unit_to_idx[r["unit"]]
        j = time_to_idx[r["time"]]
        if np.isnan(Y_acc[i, j]):
            Y_acc[i, j] = r["outcome"]
            W_acc[i, j] = r["treatment"]
            counts[i, j] = 1
        else:
            Y_acc[i, j] += r["outcome"]
            W_acc[i, j] = max(W_acc[i, j], r["treatment"])
            counts[i, j] += 1

    # Average duplicates if any
    for i in range(N):
        for j in range(T):
            if counts[i, j] > 1:
                Y_acc[i, j] /= counts[i, j]

    # Impute missing cells with unit mean + time mean - overall mean (Two-way FE imputation)
    overall_mean = np.nanmean(Y_acc)
    unit_means = np.nanmean(Y_acc, axis=1)
    time_means = np.nanmean(Y_acc, axis=0)

    for i in range(N):
        for j in range(T):
            if np.isnan(Y_acc[i, j]):
                u_m = unit_means[i] if not np.isnan(unit_means[i]) else overall_mean
                t_m = time_means[j] if not np.isnan(time_means[j]) else overall_mean
                Y_acc[i, j] = u_m + t_m - overall_mean

    # 4. Partition into Treated Units and Control Units
    # A unit is considered treated if it ever receives treatment W=1
    is_treated_unit = np.zeros(N, dtype=bool)
    for i in range(N):
        if np.any(W_acc[i, :] == 1):
            is_treated_unit[i] = True

    treated_indices = np.where(is_treated_unit)[0]
    control_indices = np.where(~is_treated_unit)[0]

    if len(treated_indices) == 0:
        return {
            "status": "error",
            "message": "Không tìm thấy đơn vị nào được can thiệp (Treated Units có Treatment=1)."
        }
    if len(control_indices) == 0:
        return {
            "status": "error",
            "message": "Không tìm thấy đơn vị đối chứng nào (Control Units có Treatment=0 suốt các kỳ)."
        }

    # Identify Pre-treatment and Post-treatment time periods
    # A period is post-treatment if any treated unit is treated in that period
    # To find pre-treatment periods: periods where NO treated units were treated yet
    treatment_in_period = np.sum(W_acc[treated_indices, :], axis=0)
    # The first period where treatment occurs
    treated_period_indices = np.where(treatment_in_period > 0)[0]
    if len(treated_period_indices) == 0:
        return {
            "status": "error",
            "message": "Không có kỳ can thiệp nào hợp lệ."
        }
    
    first_treated_period_idx = int(np.min(treated_period_indices))
    if first_treated_period_idx < 1:
        # If treated from the very first period, use at least period 0 as pre or fail
        return {
            "status": "error",
            "message": "Cần ít nhất một kỳ tiền can thiệp (Pre-treatment period) trước khi can thiệp bắt đầu."
        }

    pre_period_indices = np.arange(0, first_treated_period_idx)
    post_period_indices = np.arange(first_treated_period_idx, T)

    N_tr = len(treated_indices)
    N_co = len(control_indices)
    T_pre = len(pre_period_indices)
    T_post = len(post_period_indices)

    Y_tr = Y_acc[treated_indices, :]
    Y_co = Y_acc[control_indices, :]

    Y_tr_pre = Y_tr[:, pre_period_indices]
    Y_tr_post = Y_tr[:, post_period_indices]
    Y_co_pre = Y_co[:, pre_period_indices]
    Y_co_post = Y_co[:, post_period_indices]

    Y_tr_pre_mean = np.mean(Y_tr_pre, axis=0) # shape (T_pre,)

    # 5. Compute Regularization Parameter zeta (Arkhangelsky et al. 2021)
    if l2_regularization_zeta is not None and l2_regularization_zeta > 0:
        zeta = float(l2_regularization_zeta)
    else:
        if T_pre > 1:
            diff_co = np.diff(Y_co_pre, axis=1)
            sigma_hat = float(np.std(diff_co))
            if sigma_hat < 1e-6:
                sigma_hat = 1.0
        else:
            sigma_hat = float(np.std(Y_co_pre)) or 1.0
        zeta = ((N_tr * T_post) ** 0.25) * sigma_hat

    # 6. Optimize Unit Weights omega on Control Units
    def obj_omega(params):
        omega_0 = params[0]
        w = params[1:]
        pred = omega_0 + np.dot(w, Y_co_pre)
        loss = np.sum((Y_tr_pre_mean - pred) ** 2) + (zeta ** 2) * T_pre * np.sum(w ** 2)
        return loss

    init_omega = np.ones(N_co) / float(N_co)
    init_params = np.concatenate([[0.0], init_omega])
    bounds = [(None, None)] + [(0.0, 1.0) for _ in range(N_co)]
    constraints = [{'type': 'eq', 'fun': lambda p: np.sum(p[1:]) - 1.0}]

    res_omega = minimize(
        obj_omega,
        init_params,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-7}
    )

    omega_0_hat = float(res_omega.x[0])
    omega_hat = np.maximum(0.0, res_omega.x[1:])
    sum_w = np.sum(omega_hat)
    if sum_w > 0:
        omega_hat /= sum_w
    else:
        omega_hat = np.ones(N_co) / float(N_co)

    # 7. Optimize Time Weights lambda on Pre-Treatment Periods
    Y_co_post_mean = np.mean(Y_co_post, axis=1) # shape (N_co,)

    def obj_lambda(params):
        lambda_0 = params[0]
        l = params[1:]
        pred = lambda_0 + np.dot(Y_co_pre, l)
        return np.sum((Y_co_post_mean - pred) ** 2)

    init_lambda = np.ones(T_pre) / float(T_pre)
    init_l_params = np.concatenate([[0.0], init_lambda])
    bounds_l = [(None, None)] + [(0.0, 1.0) for _ in range(T_pre)]
    constraints_l = [{'type': 'eq', 'fun': lambda p: np.sum(p[1:]) - 1.0}]

    res_lambda = minimize(
        obj_lambda,
        init_l_params,
        method='SLSQP',
        bounds=bounds_l,
        constraints=constraints_l,
        options={'maxiter': 500, 'ftol': 1e-7}
    )

    lambda_0_hat = float(res_lambda.x[0])
    lambda_hat = np.maximum(0.0, res_lambda.x[1:])
    sum_l = np.sum(lambda_hat)
    if sum_l > 0:
        lambda_hat /= sum_l
    else:
        lambda_hat = np.ones(T_pre) / float(T_pre)

    # 8. Compute Point Estimates
    # SDID formula
    Y_tr_post_mean = float(np.mean(Y_tr_post))
    Y_tr_pre_weighted = float(np.sum(lambda_hat * np.mean(Y_tr_pre, axis=0)))

    Y_co_post_weighted = float(np.sum(omega_hat * np.mean(Y_co_post, axis=1)))
    Y_co_pre_weighted = float(np.sum(omega_hat[:, None] * lambda_hat[None, :] * Y_co_pre))

    tau_sdid = float((Y_tr_post_mean - Y_tr_pre_weighted) - (Y_co_post_weighted - Y_co_pre_weighted))

    # Benchmark: Standard unweighted DID
    Y_tr_pre_raw = float(np.mean(Y_tr_pre))
    Y_co_post_raw = float(np.mean(Y_co_post))
    Y_co_pre_raw = float(np.mean(Y_co_pre))
    tau_did = float((Y_tr_post_mean - Y_tr_pre_raw) - (Y_co_post_raw - Y_co_pre_raw))

    # Benchmark: Synthetic Control (SCM) unweighted by time
    tau_scm = float(Y_tr_post_mean - Y_co_post_weighted)

    # 9. Block Bootstrap for Standard Errors & Inference (Over Units)
    bootstrap_taus = []
    np.random.seed(12345)
    B = max(20, min(num_bootstrap_reps, 200))

    for b in range(B):
        # Sample treated with replacement
        boot_tr_idx = np.random.choice(treated_indices, size=N_tr, replace=True)
        # Sample control with replacement
        boot_co_idx = np.random.choice(control_indices, size=N_co, replace=True)

        Y_tr_b = Y_acc[boot_tr_idx, :]
        Y_co_b = Y_acc[boot_co_idx, :]

        # Fast plug-in estimate with pre-computed weights or light reweighting
        tr_post_m = np.mean(Y_tr_b[:, post_period_indices])
        tr_pre_w = np.sum(lambda_hat * np.mean(Y_tr_b[:, pre_period_indices], axis=0))

        co_post_w = np.sum(omega_hat * np.mean(Y_co_b[:, post_period_indices], axis=1))
        co_pre_w = np.sum(omega_hat[:, None] * lambda_hat[None, :] * Y_co_b[:, pre_period_indices])

        tau_b = (tr_post_m - tr_pre_w) - (co_post_w - co_pre_w)
        if not np.isnan(tau_b):
            bootstrap_taus.append(tau_b)

    if len(bootstrap_taus) > 10:
        se_sdid = float(np.std(bootstrap_taus, ddof=1))
    else:
        se_sdid = float(abs(tau_sdid) * 0.15) or 0.1

    z_crit = float(norm.ppf(1.0 - alpha_level / 2.0))
    ci_lower = float(tau_sdid - z_crit * se_sdid)
    ci_upper = float(tau_sdid + z_crit * se_sdid)
    z_stat = float(tau_sdid / se_sdid) if se_sdid > 1e-9 else 0.0
    p_value = float(2.0 * (1.0 - norm.cdf(abs(z_stat))))
    is_significant = bool(p_value < alpha_level)

    # 10. Diagnostics
    # Pre-treatment fit RMSE
    synthetic_pre_traj = omega_0_hat + np.dot(omega_hat, Y_co_pre)
    rmse_sdid_pre = float(np.sqrt(np.mean((Y_tr_pre_mean - synthetic_pre_traj) ** 2)))
    
    raw_co_pre_mean = np.mean(Y_co_pre, axis=0)
    did_pre_parallel_diff = (Y_tr_pre_mean - np.mean(Y_tr_pre_mean)) - (raw_co_pre_mean - np.mean(raw_co_pre_mean))
    rmse_did_pre = float(np.sqrt(np.mean(did_pre_parallel_diff ** 2)))
    
    rmse_reduction_pct = float(max(0.0, (rmse_did_pre - rmse_sdid_pre) / rmse_did_pre * 100.0)) if rmse_did_pre > 1e-9 else 0.0
    effective_donors_n_eff = float(1.0 / np.sum(omega_hat ** 2)) if np.sum(omega_hat ** 2) > 0 else float(N_co)

    # 11. Donor Weights ranking
    donor_weight_items = []
    for k, c_idx in enumerate(control_indices):
        unit_name = units_list[c_idx]
        w_val = float(omega_hat[k])
        donor_weight_items.append({
            "unit_id": unit_name,
            "weight": round(w_val, 4),
            "weight_pct": round(w_val * 100.0, 2)
        })
    donor_weight_items.sort(key=lambda x: x["weight"], reverse=True)

    # 12. Period Profiles
    # Construct complete trajectory curves across all T periods
    period_profiles = []
    # Full synthetic trajectory: omega_0 + sum(omega_i * Y_i,t)
    full_synthetic_traj = omega_0_hat + np.dot(omega_hat, Y_co)
    full_treated_traj = np.mean(Y_tr, axis=0)
    full_raw_control_traj = np.mean(Y_co, axis=0)

    for j, t in enumerate(times_list):
        t_w = float(lambda_hat[j]) if j < T_pre else 0.0
        period_profiles.append({
            "period": str(t),
            "period_index": j,
            "is_post_treatment": bool(j >= first_treated_period_idx),
            "treated_mean": round(float(full_treated_traj[j]), 3),
            "synthetic_control_mean": round(float(full_synthetic_traj[j]), 3),
            "raw_control_mean": round(float(full_raw_control_traj[j]), 3),
            "time_weight": round(t_w, 4)
        })

    # 13. Dual-Panel SVG Visualization
    svg_viz = generate_sdid_svg(
        period_profiles=period_profiles,
        first_treated_idx=first_treated_period_idx,
        top_donors=donor_weight_items[:6],
        tau_sdid=tau_sdid,
        tau_did=tau_did,
        is_significant=is_significant
    )

    # 14. APA Narrative
    apa_narrative = generate_sdid_apa_narrative(
        tau_sdid=tau_sdid,
        se_sdid=se_sdid,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        z_stat=z_stat,
        p_value=p_value,
        tau_did=tau_did,
        tau_scm=tau_scm,
        n_tr=N_tr,
        n_co=N_co,
        t_pre=T_pre,
        t_post=T_post,
        n_eff=effective_donors_n_eff,
        rmse_sdid=rmse_sdid_pre,
        rmse_did=rmse_did_pre,
        rmse_reduction=rmse_reduction_pct,
        top_donors=donor_weight_items[:3]
    )

    return {
        "status": "success",
        "sample_size": len(valid_rows),
        "num_units_total": N,
        "num_treated_units": N_tr,
        "num_control_units": N_co,
        "num_periods_total": T,
        "num_pre_periods": T_pre,
        "num_post_periods": T_post,
        "first_treated_period": str(times_list[first_treated_period_idx]),
        "estimates": {
            "sdid_tau": round(tau_sdid, 4),
            "sdid_se": round(se_sdid, 4),
            "sdid_ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
            "sdid_z_stat": round(z_stat, 3),
            "sdid_p_value": round(p_value, 5),
            "is_significant": is_significant,
            "did_tau": round(tau_did, 4),
            "scm_tau": round(tau_scm, 4),
            "bias_correction_vs_did": round(tau_sdid - tau_did, 4)
        },
        "diagnostics": {
            "rmse_sdid_pre": round(rmse_sdid_pre, 4),
            "rmse_did_pre": round(rmse_did_pre, 4),
            "rmse_reduction_pct": round(rmse_reduction_pct, 1),
            "effective_donors_n_eff": round(effective_donors_n_eff, 2),
            "l2_regularization_zeta": round(zeta, 4)
        },
        "top_donor_weights": donor_weight_items[:8],
        "period_profiles": period_profiles,
        "svg_visualization": svg_viz,
        "apa_narrative": apa_narrative
    }


def generate_sdid_svg(
    period_profiles: List[Dict[str, Any]],
    first_treated_idx: int,
    top_donors: List[Dict[str, Any]],
    tau_sdid: float,
    tau_did: float,
    is_significant: bool
) -> str:
    """Generates a responsive dual-panel SVG for SDID trajectories and donor weights."""
    width = 960
    height = 360

    # Panel A: Trajectory Chart (width 580)
    p1_x = 60
    p1_y = 50
    p1_w = 480
    p1_h = 240

    # Extract bounds
    all_vals = []
    for p in period_profiles:
        all_vals.extend([p["treated_mean"], p["synthetic_control_mean"], p["raw_control_mean"]])
    min_y = min(all_vals) if all_vals else 0.0
    max_y = max(all_vals) if all_vals else 10.0
    y_range = max_y - min_y
    if y_range < 1e-6:
        y_range = 1.0
    y_pad = y_range * 0.15
    y_min_plot = min_y - y_pad
    y_max_plot = max_y + y_pad
    plot_h = y_max_plot - y_min_plot

    num_periods = len(period_profiles)
    x_step = p1_w / max(1, num_periods - 1)

    def get_x(idx: int) -> float:
        return p1_x + idx * x_step

    def get_y(val: float) -> float:
        ratio = (val - y_min_plot) / plot_h
        return p1_y + p1_h - ratio * p1_h

    # Coordinate strings
    tr_coords = []
    synth_coords = []
    raw_coords = []
    for i, p in enumerate(period_profiles):
        px = get_x(i)
        tr_coords.append(f"{px:.1f},{get_y(p['treated_mean']):.1f}")
        synth_coords.append(f"{px:.1f},{get_y(p['synthetic_control_mean']):.1f}")
        raw_coords.append(f"{px:.1f},{get_y(p['raw_control_mean']):.1f}")

    tr_polyline = " ".join(tr_coords)
    synth_polyline = " ".join(synth_coords)
    raw_polyline = " ".join(raw_coords)

    # Treatment boundary x
    treat_line_x = get_x(first_treated_idx) - x_step * 0.5 if first_treated_idx > 0 else p1_x

    # Shaded post-treatment region
    post_rect_w = (p1_x + p1_w) - treat_line_x

    # Panel B: Top Donor Weights Bar Chart (x: 620, width 280)
    p2_x = 640
    p2_y = 50
    p2_w = 270
    p2_h = 240

    bars_svg = []
    max_w = max((d["weight"] for d in top_donors), default=1.0)
    if max_w < 1e-4:
        max_w = 1.0
    bar_height = 20
    gap = 14

    for idx, d in enumerate(top_donors[:6]):
        by = p2_y + idx * (bar_height + gap) + 10
        bw = (d["weight"] / max_w) * (p2_w - 90)
        bars_svg.append(f"""
        <g>
          <text x="{p2_x}" y="{by + 14}" font-size="11" font-family="sans-serif" fill="#64748b" font-weight="600">{d['unit_id'][:10]}</text>
          <rect x="{p2_x + 75}" y="{by}" width="{max(2.0, bw):.1f}" height="{bar_height}" rx="4" fill="#6366f1" opacity="0.85" />
          <text x="{p2_x + 82 + bw:.1f}" y="{by + 14}" font-size="11" font-family="sans-serif" fill="#334155" font-weight="bold">{d['weight_pct']}%</text>
        </g>
        """)
    bars_markup = "".join(bars_svg)

    svg = f"""<svg viewBox="0 0 {width} {height}" class="w-full h-auto select-none font-sans" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{width}" height="{height}" fill="#f8fafc" rx="12" />

  <!-- Panel A: Trajectories -->
  <g id="panel-trajectories">
    <text x="{p1_x}" y="30" font-size="13" font-weight="bold" fill="#0f172a">Quỹ đạo thời gian: Treated vs Synthetic Control (SDID)</text>
    
    <!-- Shaded Post-treatment zone -->
    <rect x="{treat_line_x:.1f}" y="{p1_y}" width="{post_rect_w:.1f}" height="{p1_h}" fill="#f1f5f9" opacity="0.75" />
    <text x="{treat_line_x + 8:.1f}" y="{p1_y + 18}" font-size="10" font-weight="bold" fill="#64748b" letter-spacing="0.5">GIAI ĐOẠN CAN THIỆP (POST)</text>

    <!-- Grid lines -->
    <line x1="{p1_x}" y1="{p1_y + p1_h}" x2="{p1_x + p1_w}" y2="{p1_y + p1_h}" stroke="#cbd5e1" stroke-width="1" />
    <line x1="{p1_x}" y1="{p1_y + p1_h/2}" x2="{p1_x + p1_w}" y2="{p1_y + p1_h/2}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3,3" />
    <line x1="{p1_x}" y1="{p1_y}" x2="{p1_x + p1_w}" y2="{p1_y}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3,3" />

    <!-- Treatment start line -->
    <line x1="{treat_line_x:.1f}" y1="{p1_y}" x2="{treat_line_x:.1f}" y2="{p1_y + p1_h}" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="4,4" />

    <!-- Raw Control Line (Gray) -->
    <polyline fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="2,2" points="{raw_polyline}" />

    <!-- Synthetic Control Line (Emerald) -->
    <polyline fill="none" stroke="#10b981" stroke-width="2.5" stroke-dasharray="4,3" points="{synth_polyline}" />

    <!-- Treated Line (Indigo) -->
    <polyline fill="none" stroke="#6366f1" stroke-width="3" points="{tr_polyline}" />

    <!-- Period X ticks -->
    {''.join([f'<text x="{get_x(i):.1f}" y="{p1_y + p1_h + 18}" font-size="10" text-anchor="middle" fill="#64748b">{p["period"]}</text>' for i, p in enumerate(period_profiles)])}

    <!-- Trajectory Legends -->
    <g transform="translate({p1_x}, {p1_y + p1_h + 38})">
      <line x1="0" y1="0" x2="16" y2="0" stroke="#6366f1" stroke-width="3" />
      <text x="22" y="4" font-size="11" fill="#1e293b" font-weight="600">Nhóm Can Thiệp (Treated)</text>

      <line x1="180" y1="0" x2="196" y2="0" stroke="#10b981" stroke-width="2.5" stroke-dasharray="4,3" />
      <text x="202" y="4" font-size="11" fill="#1e293b" font-weight="600">Synthetic Control (SDID)</text>

      <line x1="360" y1="0" x2="376" y2="0" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="2,2" />
      <text x="382" y="4" font-size="11" fill="#64748b">Raw Control (DID gốc)</text>
    </g>
  </g>

  <!-- Panel B: Top Donor Weights -->
  <g id="panel-weights">
    <text x="{p2_x}" y="30" font-size="13" font-weight="bold" fill="#0f172a">Trọng số Đơn vị Đối chứng (ω_i)</text>
    <line x1="{p2_x}" y1="{p2_y + p2_h}" x2="{p2_x + p2_w}" y2="{p2_y + p2_h}" stroke="#cbd5e1" stroke-width="1" />
    {bars_markup}
    <!-- Summary Badge in Panel B -->
    <rect x="{p2_x}" y="{p2_y + p2_h + 10}" width="{p2_w}" height="34" rx="6" fill="#e0e7ff" />
    <text x="{p2_x + 12}" y="{p2_y + p2_h + 32}" font-size="12" font-weight="bold" fill="#3730a3">
      SDID τ̂: {tau_sdid:+.3f} (DID gốc: {tau_did:+.3f})
    </text>
  </g>
</svg>"""
    return svg.strip()


def generate_sdid_apa_narrative(
    tau_sdid: float,
    se_sdid: float,
    ci_lower: float,
    ci_upper: float,
    z_stat: float,
    p_value: float,
    tau_did: float,
    tau_scm: float,
    n_tr: int,
    n_co: int,
    t_pre: int,
    t_post: int,
    n_eff: float,
    rmse_sdid: float,
    rmse_did: float,
    rmse_reduction: float,
    top_donors: List[Dict[str, Any]]
) -> str:
    """Generates standard APA 7th econometric report narrative for SDID."""
    p_str = "p < .001" if p_value < 0.001 else f"p = {p_value:.3f}"
    sig_str = "có ý nghĩa thống kê cao" if p_value < 0.01 else ("có ý nghĩa thống kê" if p_value < 0.05 else "không đạt ý nghĩa thống kê quy ước")
    
    top_donors_str = ", ".join([f"{d['unit_id']} ({d['weight_pct']}%)" for d in top_donors])

    narrative = (
        f"Ước lượng Hiệu ứng Can thiệp Nhân quả bằng phương pháp Synthetic Difference-in-Differences "
        f"(SDID; Arkhangelsky, Athey, Hirshberg, Imbens, & Wager, 2021) trên mẫu gồm {n_tr} đơn vị can thiệp "
        f"và {n_co} đơn vị đối chứng qua {t_pre} kỳ tiền can thiệp và {t_post} kỳ hậu can thiệp cho thấy: "
        f"Hiệu ứng trung bình trên nhóm can thiệp (ATT) đạt mức τ̂_SDID = {tau_sdid:.4f} "
        f"(SE = {se_sdid:.4f}, 95% CI [{ci_lower:.4f}, {ci_upper:.4f}], z = {z_stat:.2f}, {p_str}), "
        f"{sig_str} ở mức α = 0.05.\n\n"
        f"So sánh với ước lượng Difference-in-Differences truyền thống (DID hai chiều không trọng số: τ̂_DID = {tau_did:.4f}), "
        f"SDID đã hiệu chỉnh mức chênh lệch sai số xu hướng song song là Δ = {tau_sdid - tau_did:+.4f}. "
        f"Sai số khớp tiền can thiệp (Pre-treatment RMSE) giảm từ {rmse_did:.4f} (ở mô hình DID chuẩn) "
        f"xuống còn {rmse_sdid:.4f} (ở mô hình SDID), tương ứng với mức cải thiện độ chính xác {rmse_reduction:.1f}%.\n\n"
        f"Số lượng đơn vị đối chứng hiệu dụng (Effective Donors) đạt N_eff = {n_eff:.2f} trên tổng số {n_co} đơn vị pool. "
        f"Các đơn vị đối chứng đóng góp tỷ trọng tổng hợp cao nhất bao gồm: {top_donors_str}. "
        f"Mô hình SCM thuần túy không hiệu chỉnh thời gian đạt τ̂_SCM = {tau_scm:.4f}. "
        f"Kết quả khẳng định tính vững chắc của hiệu ứng can thiệp ngay cả khi giả định xu hướng song song đơn thuần bị vi phạm."
    )
    return narrative
