# -*- coding: utf-8 -*-
"""
Synthetic Difference-in-Differences (SDID) Advanced Engine
Methodology:
- Arkhangelsky, D., Athey, S., Hirshberg, D. A., Imbens, G. W., & Wager, S. (2021).
  Synthetic difference-in-differences.
  American Economic Review, 111(12), 4088-4118.
- Doudchenko, N., & Imbens, G. W. (2016).
  Balancing, regression, difference-in-differences and synthetic control methods: A synthesis.
  NBER Working Paper No. 22791.
"""

import numpy as np
from scipy import stats, optimize
from typing import Dict, List, Any, Optional, Tuple


class SDIDAdvancedEngine:
    """
    Synthetic Difference-in-Differences (SDID) Engine (Arkhangelsky et al. 2021).
    Merges Synthetic Control unit-weighting and Difference-in-Differences fixed effects,
    augmented with time-weights, achieving double-robustness against both parallel trends violations
    and convex hull failure.
    """

    @staticmethod
    def evaluate_sdid(
        y_matrix_flat: np.ndarray,
        unit_indices: np.ndarray,
        time_indices: np.ndarray,
        treatment_indicator: np.ndarray,
        zeta_regularization: Optional[float] = None,
        outcome_label: str = "Outcome Metric",
        unit_label: str = "Survey Unit",
        time_label: str = "Time Period"
    ) -> Dict[str, Any]:
        """
        Calculates SDID treatment effect, unit weights omega, time weights lambda,
        counterfactual trajectory, and placebo standard errors.
        """
        n = len(y_matrix_flat)
        if n < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát (N={n}) không đủ. Cần tối thiểu 20 quan sát dạng bảng.",
                "model_type": "SYNTHETIC_DID_ARKHANGELSKY_2021",
                "diagnostics": None,
                "unit_weights": None,
                "time_weights": None,
                "trajectories": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        unique_units = np.unique(unit_indices)
        unique_times = np.sort(np.unique(time_indices))

        N = len(unique_units)
        T = len(unique_times)

        if N < 4 or T < 3:
            return {
                "status": "INSUFFICIENT_DIMENSIONS",
                "message": f"Kích thước bảng dữ liệu (N={N} đơn vị, T={T} đợt) quá nhỏ. Cần tối thiểu N >= 4 và T >= 3.",
                "model_type": "SYNTHETIC_DID_ARKHANGELSKY_2021",
                "diagnostics": None,
                "unit_weights": None,
                "time_weights": None,
                "trajectories": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        u_map = {u: i for i, u in enumerate(unique_units)}
        t_map = {t: j for j, t in enumerate(unique_times)}

        Y = np.full((N, T), np.nan)
        W = np.zeros((N, T), dtype=int)

        for idx in range(n):
            u_i = u_map[unit_indices[idx]]
            t_j = t_map[time_indices[idx]]
            Y[u_i, t_j] = float(y_matrix_flat[idx])
            W[u_i, t_j] = 1 if float(treatment_indicator[idx]) > 0 else 0

        # Identify treated units and control units
        unit_treated_counts = np.sum(W, axis=1)
        treated_u_idx = np.where(unit_treated_counts > 0)[0]
        control_u_idx = np.where(unit_treated_counts == 0)[0]

        N_tr = len(treated_u_idx)
        N_co = len(control_u_idx)

        if N_tr == 0:
            return {
                "status": "NO_TREATED_UNITS",
                "message": "Không tìm thấy đơn vị nào được can thiệp trong mẫu khảo sát.",
                "model_type": "SYNTHETIC_DID_ARKHANGELSKY_2021",
                "diagnostics": None,
                "unit_weights": None,
                "time_weights": None,
                "trajectories": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        if N_co < 3:
            return {
                "status": "INSUFFICIENT_CONTROLS",
                "message": f"Số lượng đơn vị đối chứng thuần (N_co={N_co}) quá ít để tối ưu hóa trọng số tổng hợp SDID. Cần tối thiểu 3 đơn vị.",
                "model_type": "SYNTHETIC_DID_ARKHANGELSKY_2021",
                "diagnostics": None,
                "unit_weights": None,
                "time_weights": None,
                "trajectories": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        # Identify pre-treatment periods: periods where NO treated unit was treated yet
        treated_W_matrix = W[treated_u_idx, :]
        pre_t_mask = (np.sum(treated_W_matrix, axis=0) == 0)
        post_t_mask = ~pre_t_mask

        pre_t_idx = np.where(pre_t_mask)[0]
        post_t_idx = np.where(post_t_mask)[0]

        T_pre = len(pre_t_idx)
        T_post = len(post_t_idx)

        if T_pre < 2 or T_post < 1:
            return {
                "status": "INSUFFICIENT_TIME_WINDOW",
                "message": f"Số kỳ trước can thiệp (T_pre={T_pre}) hoặc sau can thiệp (T_post={T_post}) không đủ. Cần T_pre >= 2 và T_post >= 1.",
                "model_type": "SYNTHETIC_DID_ARKHANGELSKY_2021",
                "diagnostics": None,
                "unit_weights": None,
                "time_weights": None,
                "trajectories": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        # Handle missing entries in Y by median replacement on respective rows
        for i in range(N):
            row_vals = Y[i, ~np.isnan(Y[i, :])]
            med = float(np.median(row_vals)) if len(row_vals) > 0 else 0.0
            nan_cols = np.where(np.isnan(Y[i, :]))[0]
            for c in nan_cols:
                Y[i, c] = med

        # 1. Estimate Unit Weights omega via constrained quadratic program (Arkhangelsky et al. 2021 eq. 5)
        # Target: match average pre-treatment outcome of treated units
        Y_tr_pre_mean = np.mean(Y[treated_u_idx, :][:, pre_t_idx], axis=0)  # Shape (T_pre,)
        Y_co_pre = Y[control_u_idx, :][:, pre_t_idx]  # Shape (N_co, T_pre)

        # Estimate noise scale for L2 regularization
        first_diff = np.diff(Y_co_pre, axis=1)
        sigma_hat = float(np.std(first_diff) / np.sqrt(2.0)) if first_diff.size > 0 else 1.0

        if zeta_regularization is None or zeta_regularization <= 0:
            zeta = float((N_tr * T_post)**0.25 * sigma_hat)
        else:
            zeta = float(zeta_regularization)

        # Quadratic program for omega: min || omega_0 + Y_co_pre^T * omega - Y_tr_pre_mean ||_2^2 + zeta^2 ||omega||_2^2
        # Subject to omega >= 0, sum(omega) = 1
        def unit_obj(omega):
            # Centering offset omega_0 is analytical
            synth_pre = omega @ Y_co_pre  # (T_pre,)
            offset = np.mean(Y_tr_pre_mean - synth_pre)
            residuals = (offset + synth_pre) - Y_tr_pre_mean
            return float(np.sum(residuals**2) + (zeta**2) * np.sum(omega**2))

        init_omega = np.ones(N_co) / N_co
        bnds = [(0.0, 1.0) for _ in range(N_co)]
        cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})

        opt_omega = optimize.minimize(unit_obj, init_omega, bounds=bnds, constraints=cons, method='SLSQP')
        hat_omega = np.maximum(0.0, opt_omega.x)
        hat_omega /= max(np.sum(hat_omega), 1e-8)

        omega_0 = float(np.mean(Y_tr_pre_mean - (hat_omega @ Y_co_pre)))

        # 2. Estimate Time Weights lambda (Arkhangelsky et al. 2021 eq. 6)
        # Target: match post-treatment time average of control units
        Y_co_post_mean = np.mean(Y[control_u_idx, :][:, post_t_idx], axis=1)  # Shape (N_co,)
        Y_co_pre_units = Y[control_u_idx, :][:, pre_t_idx]  # Shape (N_co, T_pre)

        def time_obj(lam):
            synth_co = Y_co_pre_units @ lam  # (N_co,)
            offset_lam = np.mean(Y_co_post_mean - synth_co)
            resids = (offset_lam + synth_co) - Y_co_post_mean
            return float(np.sum(resids**2))

        init_lam = np.ones(T_pre) / T_pre
        bnds_lam = [(0.0, 1.0) for _ in range(T_pre)]
        cons_lam = ({'type': 'eq', 'fun': lambda l: np.sum(l) - 1.0})

        opt_lam = optimize.minimize(time_obj, init_lam, bounds=bnds_lam, constraints=cons_lam, method='SLSQP')
        hat_lambda = np.maximum(0.0, opt_lam.x)
        hat_lambda /= max(np.sum(hat_lambda), 1e-8)

        # 3. SDID Treatment Effect Estimator (Arkhangelsky et al. 2021 eq. 1)
        # hat_tau = (mean_tr_post - hat_lambda^T Y_tr_pre) - (hat_omega^T Y_co_post - hat_omega^T Y_co_pre hat_lambda)
        Y_tr_post_scalar = float(np.mean(Y[treated_u_idx, :][:, post_t_idx]))
        Y_tr_pre_weighted = float(np.sum((np.mean(Y[treated_u_idx, :][:, pre_t_idx], axis=0)) * hat_lambda))

        Y_co_post_weighted = float(np.sum(hat_omega * np.mean(Y[control_u_idx, :][:, post_t_idx], axis=1)))
        Y_co_pre_double_weighted = float(hat_omega @ Y_co_pre @ hat_lambda)

        tau_sdid = float((Y_tr_post_scalar - Y_tr_pre_weighted) - (Y_co_post_weighted - Y_co_pre_double_weighted))

        # Comparison standard DiD
        did_tr_diff = Y_tr_post_scalar - float(np.mean(Y[treated_u_idx, :][:, pre_t_idx]))
        did_co_diff = float(np.mean(Y[control_u_idx, :][:, post_t_idx])) - float(np.mean(Y[control_u_idx, :][:, pre_t_idx]))
        tau_did_standard = float(did_tr_diff - did_co_diff)

        # Comparison standard Synthetic Control (SC without time weights and without intercept)
        tau_sc_standard = float(Y_tr_post_scalar - Y_co_post_weighted)

        # 4. Standard Error via Jackknife / Placebo Block Permutation
        placebo_taus: List[float] = []
        if N_co >= 3:
            for k in range(N_co):
                # Leave control unit k out
                sub_co_idx = [control_u_idx[m] for m in range(N_co) if m != k]
                w_sub = np.delete(hat_omega, k)
                w_sub /= max(np.sum(w_sub), 1e-8)
                sub_co_post = float(np.sum(w_sub * np.mean(Y[sub_co_idx, :][:, post_t_idx], axis=1)))
                sub_co_pre = float(w_sub @ Y[sub_co_idx, :][:, pre_t_idx] @ hat_lambda)
                p_tau = (Y_tr_post_scalar - Y_tr_pre_weighted) - (sub_co_post - sub_co_pre)
                placebo_taus.append(p_tau)

            jackknife_var = float(((N_co - 1) / N_co) * np.sum((np.array(placebo_taus) - np.mean(placebo_taus))**2))
            se_sdid = float(np.sqrt(max(jackknife_var, 1e-6)))
        else:
            se_sdid = 0.5

        t_stat = float(tau_sdid / se_sdid) if se_sdid > 0 else 0.0
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(t_stat))))
        ci_low = float(tau_sdid - 1.96 * se_sdid)
        ci_high = float(tau_sdid + 1.96 * se_sdid)

        # 5. Trajectories across time
        # Actual Treated Mean over all T
        tr_mean_traj = [float(np.mean(Y[treated_u_idx, t_col])) for t_col in range(T)]
        # Standard Control Mean over all T
        co_mean_traj = [float(np.mean(Y[control_u_idx, t_col])) for t_col in range(T)]
        # Synthetic Control Trajectory (hat_omega @ Y_co)
        sc_traj = [float(hat_omega @ Y[control_u_idx, t_col]) for t_col in range(T)]
        # SDID Counterfactual Trajectory (sc_traj + omega_0)
        sdid_traj = [float(sc_traj[t_col] + omega_0) for t_col in range(T)]

        trajectory_data = [
            {
                "time_period": float(unique_times[t_col]),
                "is_post_treatment": bool(post_t_mask[t_col]),
                "treated_actual": round(tr_mean_traj[t_col], 4),
                "control_unweighted": round(co_mean_traj[t_col], 4),
                "synthetic_control": round(sc_traj[t_col], 4),
                "sdid_counterfactual": round(sdid_traj[t_col], 4)
            }
            for t_col in range(T)
        ]

        # Unit weights breakdown
        unit_weights_list = [
            {
                "unit_id": str(unique_units[control_u_idx[idx]]),
                "weight": round(float(hat_omega[idx]), 4),
                "percentage": round(float(hat_omega[idx]) * 100.0, 2)
            }
            for idx in range(N_co)
        ]
        unit_weights_list.sort(key=lambda x: x["weight"], reverse=True)

        # Time weights breakdown
        time_weights_list = [
            {
                "time_period": float(unique_times[pre_t_idx[idx]]),
                "weight": round(float(hat_lambda[idx]), 4),
                "percentage": round(float(hat_lambda[idx]) * 100.0, 2)
            }
            for idx in range(T_pre)
        ]

        diagnostics = {
            "n_units": N,
            "n_treated_units": N_tr,
            "n_control_units": N_co,
            "n_time_periods": T,
            "n_pre_periods": T_pre,
            "n_post_periods": T_post,
            "zeta_regularization": round(zeta, 4),
            "unit_intercept_omega0": round(omega_0, 4),
            "tau_sdid": round(tau_sdid, 4),
            "se_sdid": round(se_sdid, 4),
            "z_statistic": round(t_stat, 3),
            "p_value": round(p_val, 4),
            "ci_lower_95": round(ci_low, 4),
            "ci_upper_95": round(ci_high, 4),
            "is_statistically_significant": bool(p_val < 0.05),
            "tau_standard_did": round(tau_did_standard, 4),
            "tau_standard_sc": round(tau_sc_standard, 4),
            "did_bias_gap": round(tau_sdid - tau_did_standard, 4)
        }

        # 6. SVG Visualization
        svg_chart = generate_sdid_svg(
            trajectory_data=trajectory_data,
            unit_weights_list=unit_weights_list[:6],
            diagnostics=diagnostics,
            outcome_label=outcome_label
        )

        # 7. APA 7th Narrative
        apa_narrative = SDIDAdvancedEngine._generate_apa_narrative(
            diagnostics, outcome_label, unit_label, time_label
        )

        return {
            "status": "SUCCESS",
            "model_type": "SYNTHETIC_DID_ARKHANGELSKY_2021",
            "diagnostics": diagnostics,
            "unit_weights": unit_weights_list,
            "time_weights": time_weights_list,
            "trajectories": trajectory_data,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _generate_apa_narrative(
        diag: Dict[str, Any],
        outcome_label: str,
        unit_label: str,
        time_label: str
    ) -> str:
        """
        Generates APA 7th Edition narrative for SDID analysis.
        """
        sig_str = (
            f"có ý nghĩa thống kê ở mức 5% (z = {diag['z_statistic']:.2f}, p = {diag['p_value']:.4f})"
            if diag["is_statistically_significant"]
            else f"không có ý nghĩa thống kê ở mức 5% (z = {diag['z_statistic']:.2f}, p = {diag['p_value']:.4f})"
        )

        return (
            f"Ước lượng Khác biệt trong Khác biệt Tổng hợp (Synthetic Difference-in-Differences - SDID; "
            f"Arkhangelsky, Athey, Hirshberg, Imbens, & Wager, 2021) được thực hiện trên mẫu bảng gồm "
            f"N = {diag['n_units']} {unit_label} ({diag['n_treated_units']} đơn vị can thiệp và {diag['n_control_units']} đơn vị đối chứng) "
            f"qua T = {diag['n_time_periods']} {time_label} ({diag['n_pre_periods']} kỳ trước can thiệp và {diag['n_post_periods']} kỳ sau can thiệp) "
            f"cho biến kết quả {outcome_label}.\n\n"
            f"Hiệu ứng can thiệp tổng hợp SDID đạt \u03c4_SDID = {diag['tau_sdid']:.4f} "
            f"(SE = {diag['se_sdid']:.4f}, 95% CI [{diag['ci_lower_95']:.4f}, {diag['ci_upper_95']:.4f}]), {sig_str}.\n\n"
            f"Để so sánh phương pháp: Ước lượng DiD truyền thống đạt \u03c4_DiD = {diag['tau_standard_did']:.4f} "
            f"và Synthetic Control tiêu chuẩn đạt \u03c4_SC = {diag['tau_standard_sc']:.4f}. "
            f"Độ lệch điều chỉnh thiên lệch (Bias Correction Gap) giữa SDID và DiD tiêu chuẩn là \u0394 = {diag['did_bias_gap']:.4f}, "
            f"cho thấy việc tái cân bằng trọng số đơn vị \u03c9 và trọng số thời gian \u03bb đã loại bỏ sự vi phạm giả định xu hướng song song "
            f"và bù đắp chênh lệch cấp độ ban đầu \u03c9_0 = {diag['unit_intercept_omega0']:.4f}."
        )


def generate_sdid_svg(
    trajectory_data: List[Dict[str, Any]],
    unit_weights_list: List[Dict[str, Any]],
    diagnostics: Dict[str, Any],
    outcome_label: str
) -> str:
    """
    Renders scientific dual-panel SVG:
    Panel A: Time Trajectories (Actual Treated vs SDID Counterfactual vs Raw Control).
    Panel B: Top Control Unit Weights (Synthetic donor composition).
    """
    svg_w, svg_h = 960, 420
    pad = 55
    panel_w = (svg_w - 3 * pad) // 2
    panel_h = svg_h - 2 * pad

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;">')
    lines.append('<defs>')
    lines.append('  <linearGradient id="bgGradSD" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0f172a"/><stop offset="100%" stop-color="#1e293b"/></linearGradient>')
    lines.append('  <linearGradient id="barGradSD" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#10b981"/><stop offset="100%" stop-color="#059669"/></linearGradient>')
    lines.append('  <filter id="glowSD" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    lines.append('</defs>')

    # Background
    lines.append(f'<rect width="{svg_w}" height="{svg_h}" rx="12" fill="url(#bgGradSD)" stroke="#334155" stroke-width="1"/>')

    # ================= PANEL A: TIME TRAJECTORIES =================
    pa_x0, pa_y0 = pad, pad
    lines.append(f'<rect x="{pa_x0}" y="{pa_y0}" width="{panel_w}" height="{panel_h}" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{pa_x0 + 15}" y="{pa_y0 + 25}" fill="#38bdf8" font-size="13" font-weight="700">PANEL A: Quỹ đạo Thời gian &amp; Phản sự kiện SDID</text>')

    T_len = len(trajectory_data)
    if T_len > 1:
        all_vals = []
        for d in trajectory_data:
            all_vals.extend([d["treated_actual"], d["sdid_counterfactual"], d["control_unweighted"]])
        min_v = min(all_vals)
        max_v = max(all_vals)
        span_v = max(max_v - min_v, 1.0) * 1.25

        def map_x_a(idx):
            return pa_x0 + 40 + (idx / (T_len - 1)) * (panel_w - 70)

        def map_y_a(v):
            return pa_y0 + panel_h - 40 - ((v - min_v) / span_v) * (panel_h - 90)

        # Draw intervention vertical cutoff
        first_post_idx = next((i for i, d in enumerate(trajectory_data) if d["is_post_treatment"]), -1)
        if first_post_idx > 0:
            x_int = (map_x_a(first_post_idx - 1) + map_x_a(first_post_idx)) / 2.0
            lines.append(f'<line x1="{x_int}" y1="{pa_y0 + 40}" x2="{x_int}" y2="{pa_y0 + panel_h - 30}" stroke="#f59e0b" stroke-dasharray="3,3" stroke-width="1.5"/>')
            lines.append(f'<text x="{x_int - 4}" y="{pa_y0 + 48}" fill="#f59e0b" font-size="9" text-anchor="end">Tiền can thiệp</text>')
            lines.append(f'<text x="{x_int + 4}" y="{pa_y0 + 48}" fill="#10b981" font-size="9" text-anchor="start">Can thiệp</text>')

        # Trajectory 1: Control unweighted (dashed grey)
        pts_co = " ".join(f"{map_x_a(i):.1f},{map_y_a(d['control_unweighted']):.1f}" for i, d in enumerate(trajectory_data))
        lines.append(f'<polyline points="{pts_co}" fill="none" stroke="#64748b" stroke-dasharray="3,3" stroke-width="1.5" opacity="0.7"/>')

        # Trajectory 2: SDID Counterfactual (purple dotted line)
        pts_sdid = " ".join(f"{map_x_a(i):.1f},{map_y_a(d['sdid_counterfactual']):.1f}" for i, d in enumerate(trajectory_data))
        lines.append(f'<polyline points="{pts_sdid}" fill="none" stroke="#a855f7" stroke-dasharray="4,4" stroke-width="2"/>')

        # Trajectory 3: Treated Actual (solid emerald line)
        pts_tr = " ".join(f"{map_x_a(i):.1f},{map_y_a(d['treated_actual']):.1f}" for i, d in enumerate(trajectory_data))
        lines.append(f'<polyline points="{pts_tr}" fill="none" stroke="#10b981" stroke-width="2.5" filter="url(#glowSD)"/>')

        # Dots on treated
        for i, d in enumerate(trajectory_data):
            cx = map_x_a(i)
            cy_tr = map_y_a(d["treated_actual"])
            lines.append(f'<circle cx="{cx}" cy="{cy_tr}" r="4" fill="#10b981" stroke="#0f172a" stroke-width="1.5"/>')
            lines.append(f'<text x="{cx}" y="{pa_y0 + panel_h - 15}" fill="#94a3b8" font-size="10" text-anchor="middle">t={int(d["time_period"])}</text>')

        # Legend Panel A
        leg_y = pa_y0 + panel_h - 2
        lines.append(f'<line x1="{pa_x0 + 15}" y1="{leg_y}" x2="{pa_x0 + 35}" y2="{leg_y}" stroke="#10b981" stroke-width="2"/>')
        lines.append(f'<text x="{pa_x0 + 40}" y="{leg_y + 3}" fill="#cbd5e1" font-size="9">Can thiệp Thực tế</text>')
        lines.append(f'<line x1="{pa_x0 + 140}" y1="{leg_y}" x2="{pa_x0 + 160}" y2="{leg_y}" stroke="#a855f7" stroke-dasharray="4,4" stroke-width="2"/>')
        lines.append(f'<text x="{pa_x0 + 165}" y="{leg_y + 3}" fill="#cbd5e1" font-size="9">Phản sự kiện SDID</text>')

    # ================= PANEL B: TOP CONTROL UNIT WEIGHTS =================
    pb_x0, pb_y0 = pad * 2 + panel_w, pad
    lines.append(f'<rect x="{pb_x0}" y="{pb_y0}" width="{panel_w}" height="{panel_h}" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{pb_x0 + 15}" y="{pb_y0 + 25}" fill="#a855f7" font-size="13" font-weight="700">PANEL B: Phân bổ Trọng số Đơn vị Đối chứng (\u03c9_i)</text>')

    if len(unit_weights_list) > 0:
        bars = unit_weights_list[:6]
        max_pct = max(b["percentage"] for b in bars)
        max_pct = max(max_pct, 10.0) * 1.2
        bar_y0 = pb_y0 + 45
        bar_h = 24
        bar_gap = 12

        for idx, b in enumerate(bars):
            cy = bar_y0 + idx * (bar_h + bar_gap)
            bw = (b["percentage"] / max_pct) * (panel_w - 140)

            lines.append(f'<text x="{pb_x0 + 20}" y="{cy + 16}" fill="#94a3b8" font-size="10" font-weight="500">{b["unit_id"][:12]}</text>')
            lines.append(f'<rect x="{pb_x0 + 95}" y="{cy}" width="{bw}" height="{bar_h}" rx="4" fill="url(#barGradSD)" stroke="#10b981" stroke-width="1"/>')
            lines.append(f'<text x="{pb_x0 + 105 + bw}" y="{cy + 16}" fill="#10b981" font-size="10" font-weight="700">{b["percentage"]}%</text>')

        # Footer diagnostics
        lines.append(f'<text x="{pb_x0 + panel_w / 2}" y="{pb_y0 + panel_h - 10}" fill="#64748b" font-size="10" text-anchor="middle">Tổng trọng số: \u2211 \u03c9_i = 100% | L2 Regularization \u03b6 = {diagnostics["zeta_regularization"]}</text>')

    lines.append('</svg>')
    return "".join(lines)
