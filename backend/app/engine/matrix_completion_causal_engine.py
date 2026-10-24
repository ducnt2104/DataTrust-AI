# -*- coding: utf-8 -*-
"""
Matrix Completion for Causal Panel Data with Nuclear Norm Regularization Engine
Methodology:
- Athey, S., Bayati, M., Doudchenko, N., Imbens, G., & Khosravi, K. (2021).
  Matrix completion methods for causal panel data.
  Journal of the American Statistical Association, 116(536), 1716-1730.
- Mazumder, R., Hastie, T., & Tibshirani, R. (2010).
  Spectral regularization algorithms for learning large incomplete matrices.
  Journal of Machine Learning Research, 11, 2287-2322.
- Candès, E. J., & Recht, B. (2009).
  Exact matrix completion via convex optimization.
  Foundations of Computational Mathematics, 9(6), 717-772.
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Any, Optional, Tuple


class MatrixCompletionCausalEngine:
    """
    Econometric engine for causal inference in longitudinal/panel surveys with arbitrary,
    unbalanced, and staggered treatment adoption patterns.
    Casts causal inference as a low-rank matrix completion problem with nuclear norm regularization,
    simultaneously accommodating complex unobserved unit confounders and time-varying latent factors.
    """

    @staticmethod
    def evaluate_matrix_completion(
        y_matrix_flat: np.ndarray,
        unit_indices: np.ndarray,
        time_indices: np.ndarray,
        treatment_indicator: np.ndarray,
        lambda_penalty: Optional[float] = None,
        max_rank: int = 5,
        max_iterations: int = 150,
        tolerance: float = 1e-5,
        outcome_label: str = "Outcome Metric",
        unit_label: str = "Survey Unit",
        time_label: str = "Time Wave"
    ) -> Dict[str, Any]:
        """
        Estimates the counterfactual matrix L = Y(0) via Soft-Impute Singular Value Thresholding.
        Computes cell-level causal effects tau_it = Y_it - L_it, overall ATT, and singular value spectrum.
        """
        n = len(y_matrix_flat)
        if n < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát (N={n}) không đủ. Cần tối thiểu 20 quan sát dạng bảng.",
                "model_type": "CAUSAL_MATRIX_COMPLETION_ATHEY_2021",
                "diagnostics": None,
                "cell_treatment_effects": None,
                "singular_value_spectrum": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        # 1. Map units and times to continuous matrix indices
        unique_units = np.unique(unit_indices)
        unique_times = np.sort(np.unique(time_indices))

        N = len(unique_units)
        T = len(unique_times)

        if N < 3 or T < 2:
            return {
                "status": "INSUFFICIENT_DIMENSIONS",
                "message": f"Kích thước ma trận (N={N} đơn vị, T={T} thời điểm) quá nhỏ. Cần tối thiểu N >= 3 và T >= 2.",
                "model_type": "CAUSAL_MATRIX_COMPLETION_ATHEY_2021",
                "diagnostics": None,
                "cell_treatment_effects": None,
                "singular_value_spectrum": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        u_map = {u: i for i, u in enumerate(unique_units)}
        t_map = {t: j for j, t in enumerate(unique_times)}

        # Build Y matrix and W (treatment mask)
        Y = np.full((N, T), np.nan)
        W = np.zeros((N, T), dtype=int)
        observed_mask = np.zeros((N, T), dtype=bool)

        for idx in range(n):
            u_i = u_map[unit_indices[idx]]
            t_j = t_map[time_indices[idx]]
            val = float(y_matrix_flat[idx])
            w_val = 1 if float(treatment_indicator[idx]) > 0 else 0

            Y[u_i, t_j] = val
            W[u_i, t_j] = w_val
            observed_mask[u_i, t_j] = True

        # Total treated cells
        n_treated = int(np.sum((W == 1) & observed_mask))
        n_control = int(np.sum((W == 0) & observed_mask))

        if n_treated == 0:
            return {
                "status": "NO_TREATED_CELLS",
                "message": "Không có quan sát nào được gán can thiệp (W=1) trong bảng dữ liệu.",
                "model_type": "CAUSAL_MATRIX_COMPLETION_ATHEY_2021",
                "diagnostics": None,
                "cell_treatment_effects": None,
                "singular_value_spectrum": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        if n_control < 5:
            return {
                "status": "INSUFFICIENT_CONTROLS",
                "message": "Số lượng quan sát đối chứng thuần (W=0) không đủ để huấn luyện ma trận nhân quả L(0). Cần tối thiểu 5 ô đối chứng.",
                "model_type": "CAUSAL_MATRIX_COMPLETION_ATHEY_2021",
                "diagnostics": None,
                "cell_treatment_effects": None,
                "singular_value_spectrum": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        # 2. Soft-Impute Algorithm (Nuclear Norm Regularization; Mazumder et al. 2010; Athey et al. 2021)
        # Omega: set of observed control cells (W == 0 and observed)
        omega = (W == 0) & observed_mask

        # Baseline mean imputation for initialization
        control_vals = Y[omega]
        mean_control = float(np.mean(control_vals))
        std_control = float(np.std(control_vals)) if len(control_vals) > 1 else 1.0

        # Automatic lambda tuning if not provided
        # By default lambda is proportional to top singular value of zero-filled control matrix
        Y_init = np.copy(Y)
        Y_init[~omega] = mean_control

        # Center data
        U_full, s_full, Vt_full = np.linalg.svd(Y_init, full_matrices=False)
        top_s = float(s_full[0]) if len(s_full) > 0 else 1.0

        if lambda_penalty is None or lambda_penalty <= 0:
            # Optimal nuclear norm shrinkage: ~ 1% - 2% of top singular value
            lambda_val = float(0.01 * top_s)
        else:
            lambda_val = float(lambda_penalty)

        # Soft-Impute iterative loop
        L_current = np.copy(Y_init)

        converged = False
        iteration = 0
        final_singular_values: np.ndarray = s_full

        for iteration in range(1, max_iterations + 1):
            # Form matrix Z = P_omega(Y) + P_omega_perp(L_current)
            Z = np.copy(L_current)
            Z[omega] = Y[omega]

            # SVD of Z
            try:
                U, s, Vt = np.linalg.svd(Z, full_matrices=False)
            except np.linalg.LinAlgError:
                break

            # Soft-threshold singular values: S_lambda(s) = max(0, s - lambda)
            s_thresh = np.maximum(0.0, s - lambda_val)

            # Restrict rank to max_rank if specified
            if max_rank > 0 and len(s_thresh) > max_rank:
                s_thresh[max_rank:] = 0.0

            # Reconstruct L_next
            L_next = (U * s_thresh) @ Vt

            # Check convergence in Frobenius norm
            denom = float(np.linalg.norm(L_current, 'fro'))
            diff = float(np.linalg.norm(L_next - L_current, 'fro'))
            rel_diff = diff / max(denom, 1e-8)

            L_current = L_next
            final_singular_values = s_thresh

            if rel_diff < tolerance:
                converged = True
                break

        # 3. Calculate Causal Treatment Effects
        # For all treated cells in T_set: tau_it = Y_it - L_it
        treated_mask = (W == 1) & observed_mask
        treated_u, treated_t = np.where(treated_mask)

        tau_cell_list: List[Dict[str, Any]] = []
        tau_values: List[float] = []

        for i, j in zip(treated_u, treated_t):
            y_obs = float(Y[i, j])
            y_cf = float(L_current[i, j])
            tau_ij = y_obs - y_cf
            tau_values.append(tau_ij)

            tau_cell_list.append({
                "unit_id": str(unique_units[i]),
                "time_period": float(unique_times[j]),
                "realized_outcome_y1": round(y_obs, 4),
                "imputed_counterfactual_y0": round(y_cf, 4),
                "treatment_effect_tau": round(tau_ij, 4)
            })

        overall_att = float(np.mean(tau_values)) if len(tau_values) > 0 else 0.0
        # Placebo standard error from control fit residual variance
        control_residuals = Y[omega] - L_current[omega]
        sigma2_control = float(np.mean(control_residuals**2)) if len(control_residuals) > 0 else 1.0
        att_se = float(np.sqrt(sigma2_control * (1.0 / max(len(tau_values), 1) + 1.0 / max(len(control_residuals), 1))))
        att_se = max(att_se, 1e-4)

        z_stat = float(overall_att / att_se)
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        ci_lower = float(overall_att - 1.96 * att_se)
        ci_upper = float(overall_att + 1.96 * att_se)

        # Singular value spectrum diagnostics
        nonzero_singular_values = [float(s) for s in final_singular_values if s > 1e-4]
        effective_rank = len(nonzero_singular_values)
        total_energy = float(np.sum(final_singular_values**2))
        top_energy_share = float(final_singular_values[0]**2 / max(total_energy, 1e-8)) if len(final_singular_values) > 0 else 0.0

        singular_spectrum = [
            {
                "rank_component": k + 1,
                "singular_value": round(float(final_singular_values[k]), 4),
                "variance_explained_ratio": round(float(final_singular_values[k]**2 / max(total_energy, 1e-8)), 4)
            }
            for k in range(min(len(final_singular_values), 8))
        ]

        # In-sample Root Mean Square Error on observed control cells
        rmse_control = float(np.sqrt(sigma2_control))

        diagnostics = {
            "n_units": N,
            "n_time_periods": T,
            "total_cells": N * T,
            "n_treated_cells": n_treated,
            "n_control_cells": n_control,
            "lambda_penalty": round(lambda_val, 4),
            "iterations_count": iteration,
            "is_converged": bool(converged),
            "effective_rank": effective_rank,
            "rmse_control_fit": round(rmse_control, 4),
            "overall_att": round(overall_att, 4),
            "att_se": round(att_se, 4),
            "z_statistic": round(z_stat, 3),
            "p_value": round(p_val, 4),
            "ci_lower_95": round(ci_lower, 4),
            "ci_upper_95": round(ci_upper, 4),
            "is_statistically_significant": bool(p_val < 0.05),
            "top_factor_variance_share": round(top_energy_share, 4)
        }

        # 4. Generate Scientific SVG Visualization
        svg_chart = generate_matrix_completion_svg(
            Y=Y,
            W=W,
            L=L_current,
            observed_mask=observed_mask,
            singular_values=final_singular_values,
            lambda_val=lambda_val,
            overall_att=overall_att,
            outcome_label=outcome_label
        )

        # 5. APA 7th Edition Narrative
        apa_narrative = MatrixCompletionCausalEngine._generate_apa_narrative(
            diagnostics, outcome_label, unit_label, time_label
        )

        return {
            "status": "SUCCESS",
            "model_type": "CAUSAL_MATRIX_COMPLETION_ATHEY_2021",
            "diagnostics": diagnostics,
            "cell_treatment_effects": tau_cell_list,
            "singular_value_spectrum": singular_spectrum,
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
        Generates formal APA 7th Edition narrative for Matrix Completion causal panel estimation.
        """
        sig_str = (
            f"có ý nghĩa thống kê ở mức 5% (z = {diag['z_statistic']:.2f}, p = {diag['p_value']:.4f})"
            if diag["is_statistically_significant"]
            else f"không có ý nghĩa thống kê ở mức 5% (z = {diag['z_statistic']:.2f}, p = {diag['p_value']:.4f})"
        )

        return (
            f"Mô hình Hoàn thiện Ma trận Nhân quả với Chính quy hóa Chuẩn Hạt nhân (Matrix Completion for Causal Panel Data; "
            f"Athey, Bayati, Doudchenko, Imbens, & Khosravi, 2021) được áp dụng để ước lượng các giá trị đối chứng phản sự kiện "
            f"chưa quan sát Y(0) trên ma trận kích thước {diag['n_units']} {unit_label} \u00d7 {diag['n_time_periods']} {time_label} "
            f"({diag['total_cells']} ô dữ liệu tổng thể; {diag['n_treated_cells']} ô can thiệp được phục dựng).\n\n"
            f"Thuật toán Soft-Impute SVT hội tụ sau {diag['iterations_count']} vòng lặp với hệ số phạt chuẩn hạt nhân "
            f"\u03bb = {diag['lambda_penalty']:.4f}, xác định hạng hiệu dụng (effective rank) là r = {diag['effective_rank']} "
            f"(nhân tố tiềm ẩn đầu tiên giải thích {diag['top_factor_variance_share']*100:.1f}% phương sai ma trận; "
            f"sai số khớp ô đối chứng RMSE = {diag['rmse_control_fit']:.4f}).\n\n"
            f"Hiệu ứng can thiệp trung bình trên đối tượng được xử lý (ATT) đạt \u03c4 = {diag['overall_att']:.4f} "
            f"(SE = {diag['att_se']:.4f}, 95% CI [{diag['ci_lower_95']:.4f}, {diag['ci_upper_95']:.4f}]), {sig_str}. "
            f"Phương pháp này bảo toàn tính hợp lệ suy diễn ngay cả khi quy trình can thiệp phân tầng không cân bằng và chịu tác động của các yếu tố gây nhiễu tiềm ẩn đa chiều."
        )


def generate_matrix_completion_svg(
    Y: np.ndarray,
    W: np.ndarray,
    L: np.ndarray,
    observed_mask: np.ndarray,
    singular_values: np.ndarray,
    lambda_val: float,
    overall_att: float,
    outcome_label: str
) -> str:
    """
    Renders scientific dual-panel SVG:
    Panel A: Heatmap grid of Matrix Panel (observed control, observed treated, imputed counterfactual Y(0)).
    Panel B: Singular Value Decay Scree Plot with nuclear norm soft-thresholding cutoff lambda.
    """
    svg_w, svg_h = 960, 420
    pad = 55
    panel_w = (svg_w - 3 * pad) // 2
    panel_h = svg_h - 2 * pad

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;">')
    lines.append('<defs>')
    lines.append('  <linearGradient id="bgGradMC" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0f172a"/><stop offset="100%" stop-color="#1e293b"/></linearGradient>')
    lines.append('  <linearGradient id="barGradMC" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#0284c7"/></linearGradient>')
    lines.append('</defs>')

    # Background
    lines.append(f'<rect width="{svg_w}" height="{svg_h}" rx="12" fill="url(#bgGradMC)" stroke="#334155" stroke-width="1"/>')

    # ================= PANEL A: MATRIX GRID HEATMAP =================
    pa_x0, pa_y0 = pad, pad
    lines.append(f'<rect x="{pa_x0}" y="{pa_y0}" width="{panel_w}" height="{panel_h}" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{pa_x0 + 15}" y="{pa_y0 + 25}" fill="#38bdf8" font-size="13" font-weight="700">PANEL A: Bản đồ Nhiệt Ma trận Bảng N \u00d7 T (Athey et al. 2021)</text>')

    N, T = Y.shape
    # Display up to 10 rows and 8 cols
    disp_rows = min(N, 10)
    disp_cols = min(T, 8)

    grid_x0 = pa_x0 + 40
    grid_y0 = pa_y0 + 50
    cell_w = (panel_w - 60) / disp_cols
    cell_h = (panel_h - 100) / disp_rows

    for i in range(disp_rows):
        for j in range(disp_cols):
            cx = grid_x0 + j * cell_w
            cy = grid_y0 + i * cell_h

            if not observed_mask[i, j]:
                fill_color = "#334155"  # Unobserved
                label_text = "N/A"
            elif W[i, j] == 1:
                fill_color = "#10b981"  # Treated (reconstructed Y(0))
                label_text = "W=1"
            else:
                fill_color = "#0284c7"  # Control (observed Y(0))
                label_text = "W=0"

            lines.append(f'<rect x="{cx + 1}" y="{cy + 1}" width="{cell_w - 2}" height="{cell_h - 2}" rx="3" fill="{fill_color}" fill-opacity="0.75" stroke="#475569" stroke-width="1"/>')
            if cell_w > 28 and cell_h > 18:
                lines.append(f'<text x="{cx + cell_w / 2}" y="{cy + cell_h / 2 + 3.5}" fill="#ffffff" font-size="9" font-weight="600" text-anchor="middle">{label_text}</text>')

    # Legend for Panel A
    leg_y = pa_y0 + panel_h - 22
    lines.append(f'<rect x="{pa_x0 + 20}" y="{leg_y}" width="12" height="12" rx="2" fill="#0284c7" fill-opacity="0.8"/>')
    lines.append(f'<text x="{pa_x0 + 36}" y="{leg_y + 10}" fill="#cbd5e1" font-size="10">Đối chứng (Y(0) Quan sát)</text>')

    lines.append(f'<rect x="{pa_x0 + 195}" y="{leg_y}" width="12" height="12" rx="2" fill="#10b981" fill-opacity="0.8"/>')
    lines.append(f'<text x="{pa_x0 + 211}" y="{leg_y + 10}" fill="#cbd5e1" font-size="10">Can thiệp (Phục dựng Y(0))</text>')

    # ================= PANEL B: SINGULAR VALUE SCREE PLOT =================
    pb_x0, pb_y0 = pad * 2 + panel_w, pad
    lines.append(f'<rect x="{pb_x0}" y="{pb_y0}" width="{panel_w}" height="{panel_h}" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{pb_x0 + 15}" y="{pb_y0 + 25}" fill="#a855f7" font-size="13" font-weight="700">PANEL B: Phổ Giá trị Kỳ dị &amp; Ngưỡng Thu nhỏ \u03bb</text>')

    s_vals = singular_values[:min(len(singular_values), 8)]
    if len(s_vals) > 0:
        max_s = max(float(np.max(s_vals)), lambda_val * 1.5, 1.0)
        chart_x0 = pb_x0 + 45
        chart_y0 = pb_y0 + 55
        chart_w = panel_w - 70
        chart_h = panel_h - 95

        col_w = chart_w / len(s_vals)

        # Draw lambda threshold line
        y_lambda = chart_y0 + chart_h - (lambda_val / max_s) * chart_h
        lines.append(f'<line x1="{chart_x0}" y1="{y_lambda}" x2="{chart_x0 + chart_w}" y2="{y_lambda}" stroke="#f43f5e" stroke-dasharray="4,4" stroke-width="1.5"/>')
        lines.append(f'<text x="{chart_x0 + chart_w - 5}" y="{y_lambda - 5}" fill="#f43f5e" font-size="10" text-anchor="end" font-weight="600">Ngưỡng \u03bb = {lambda_val:.2f}</text>')

        for idx, s in enumerate(s_vals):
            bx = chart_x0 + idx * col_w + col_w * 0.15
            bw = col_w * 0.7
            bh = (float(s) / max_s) * chart_h
            by = chart_y0 + chart_h - bh

            fill_c = "url(#barGradMC)" if float(s) > 0.01 else "#475569"

            lines.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="3" fill="{fill_c}" stroke="#38bdf8" stroke-width="1"/>')
            lines.append(f'<text x="{bx + bw / 2}" y="{by - 4}" fill="#38bdf8" font-size="9" text-anchor="middle">{float(s):.1f}</text>')
            lines.append(f'<text x="{bx + bw / 2}" y="{chart_y0 + chart_h + 15}" fill="#94a3b8" font-size="10" text-anchor="middle">r_{idx+1}</text>')

        lines.append(f'<text x="{pb_x0 + panel_w / 2}" y="{pb_y0 + panel_h - 5}" fill="#64748b" font-size="10" text-anchor="middle">Bậc Giá trị Kỳ dị (Singular Value Components)</text>')

    lines.append('</svg>')
    return "".join(lines)
