"""
DataTrust - Panel Vector Autoregression (PVAR) & Granger Causality Engine
========================================================================
Implements Panel VAR estimation with Helmert forward orthogonal deviations,
Panel Granger causality Wald tests, Cholesky orthogonalized impulse response
functions (OIRF), and Forecast Error Variance Decomposition (FEVD).

Methodological references:
- Holtz-Eakin, D., Newey, W., & Rosen, H. S. (1988). Estimating vector
  autoregressions with panel data. Econometrica, 56(6), 1371-1395.
- Arellano, M., & Bover, O. (1995). Another look at the instrumental variable
  estimation of error-components models. Journal of Econometrics, 68(1), 29-51.
- Abrigo, M. R., & Love, I. (2016). Estimation of panel vector autoregression in Stata.
  The Stata Journal, 16(3), 778-804.
- Granger, C. W. J. (1969). Investigating causal relations by econometric models
  and cross-spectral methods. Econometrica, 37(3), 424-438.
- Sims, C. A. (1980). Macroeconomics and reality. Econometrica, 48(1), 1-48.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


class PanelVAREngine:
    """
    Panel Vector Autoregression & Dynamic Granger Causality Estimator.
    """

    @classmethod
    def estimate(
        cls,
        panel_rows: List[Dict[str, Any]],
        unit_col: str,
        time_col: str,
        var1_col: str,
        var2_col: str,
        lags: int = 1,
        irf_horizons: int = 6
    ) -> Dict[str, Any]:
        """
        Estimate 2-variable Panel VAR(1).
        panel_rows: list of dict records.
        """
        if len(panel_rows) < 15:
            return {
                "status": "insufficient_data",
                "message": "Cần tối thiểu 15 bản ghi dữ liệu bảng (panel) để ước lượng Panel VAR."
            }

        # 1. Group records by unit
        units_dict: Dict[str, List[Tuple[float, float, float]]] = {}
        for r in panel_rows:
            u = str(r.get(unit_col, "")).strip()
            t_raw = r.get(time_col)
            v1_raw = r.get(var1_col)
            v2_raw = r.get(var2_col)
            if not u or t_raw is None or v1_raw is None or v2_raw is None:
                continue
            try:
                t = float(t_raw)
                v1 = float(v1_raw)
                v2 = float(v2_raw)
                if u not in units_dict:
                    units_dict[u] = []
                units_dict[u].append((t, v1, v2))
            except (ValueError, TypeError):
                continue

        # Filter units with at least lags + 2 time periods
        min_periods = lags + 2
        valid_units = {u: sorted(rows, key=lambda x: x[0]) for u, rows in units_dict.items() if len(rows) >= min_periods}

        if len(valid_units) < 3:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 3 đơn vị bảng có ít nhất {min_periods} mốc thời gian liên tiếp."
            }

        # 2. Helmert Forward Orthogonal Deviations Transformation (Arellano & Bover 1995)
        # For each unit i and time t: y*_it = c_t * (y_it - mean_{s > t} y_is)
        # where c_t = sqrt((T - t) / (T - t + 1))
        # Build transformed regression data: Y*_t on Y*_{t-1}
        Y_lhs_list = []
        Y_rhs_list = []

        total_obs_count = 0
        for u, series in valid_units.items():
            T_i = len(series)
            vals = np.array([[row[1], row[2]] for row in series])  # T_i x 2

            # Helmert transformation
            helmert_vals = np.zeros((T_i - 1, 2))
            for t in range(T_i - 1):
                c_t = np.sqrt((T_i - t - 1) / (T_i - t))
                future_mean = np.mean(vals[t + 1:], axis=0)
                helmert_vals[t] = c_t * (vals[t] - future_mean)

            # Construct lag pairs (for lag=1)
            # LHS: t = 1 .. T_i - 2
            # RHS: t = 0 .. T_i - 3
            if len(helmert_vals) >= 2:
                for t in range(1, len(helmert_vals)):
                    Y_lhs_list.append(helmert_vals[t])
                    Y_rhs_list.append(helmert_vals[t - 1])
                    total_obs_count += 1

        if len(Y_lhs_list) < 10:
            return {
                "status": "insufficient_data",
                "message": "Không đủ số quan sát sau phép biến đổi trực giao Helmert để ước lượng PVAR."
            }

        Y_lhs = np.array(Y_lhs_list)  # M x 2
        Y_rhs = np.array(Y_rhs_list)  # M x 2
        M = len(Y_lhs)

        # 3. OLS / GMM Equation-by-Equation Estimation on Helmert Data
        # Equation 1: y1_t = a11 * y1_{t-1} + a12 * y2_{t-1} + e1
        # Equation 2: y2_t = a21 * y1_{t-1} + a22 * y2_{t-1} + e2
        # A = (Y_rhs.T @ Y_rhs)^(-1) @ Y_rhs.T @ Y_lhs  (2 x 2)
        xtx_inv = np.linalg.inv(Y_rhs.T @ Y_rhs + 1e-6 * np.eye(2))
        A_matrix = xtx_inv @ (Y_rhs.T @ Y_lhs)  # shape (2, 2)
        # Note: A_matrix[:, 0] are coeffs for Y1 eq; A_matrix[:, 1] for Y2 eq.
        a11, a12 = float(A_matrix[0, 0]), float(A_matrix[1, 0])
        a21, a22 = float(A_matrix[0, 1]), float(A_matrix[1, 1])

        # Residuals
        residuals = Y_lhs - (Y_rhs @ A_matrix)  # M x 2
        sigma_sq_1 = float(np.sum(residuals[:, 0] ** 2) / (M - 2))
        sigma_sq_2 = float(np.sum(residuals[:, 1] ** 2) / (M - 2))

        # Covariance matrices of coefficients
        cov_eq1 = sigma_sq_1 * xtx_inv
        cov_eq2 = sigma_sq_2 * xtx_inv
        se_a11, se_a12 = float(np.sqrt(max(1e-12, cov_eq1[0, 0]))), float(np.sqrt(max(1e-12, cov_eq1[1, 1])))
        se_a21, se_a22 = float(np.sqrt(max(1e-12, cov_eq2[0, 0]))), float(np.sqrt(max(1e-12, cov_eq2[1, 1])))

        # 4. Stability Condition Check (Modulus of Eigenvalues < 1)
        # Companion matrix for VAR(1) is A.T
        A_comp = A_matrix.T  # shape (2, 2): row 0 is [a11, a12], row 1 is [a21, a22]
        eigvals = np.linalg.eigvals(A_comp)
        moduli = [float(np.abs(ev)) for ev in eigvals]
        max_modulus = float(max(moduli))
        is_stable = bool(max_modulus < 1.0)

        # 5. Panel Granger Causality Wald Tests (Holtz-Eakin et al. 1988)
        # Test 1: Does Var2 Granger-cause Var1? (H0: a12 = 0)
        wald_2_to_1 = float((a12 / se_a12) ** 2) if se_a12 > 1e-12 else 0.0
        p_2_to_1 = float(1.0 - stats.chi2.cdf(wald_2_to_1, df=1))
        causes_2_to_1 = bool(p_2_to_1 < 0.05)

        # Test 2: Does Var1 Granger-cause Var2? (H0: a21 = 0)
        wald_1_to_2 = float((a21 / se_a21) ** 2) if se_a21 > 1e-12 else 0.0
        p_1_to_2 = float(1.0 - stats.chi2.cdf(wald_1_to_2, df=1))
        causes_1_to_2 = bool(p_1_to_2 < 0.05)

        causality_type = "Không có quan hệ nhân quả Granger"
        if causes_1_to_2 and causes_2_to_1:
            causality_type = "Tương tác phản hồi hai chiều (Bidirectional Feedback)"
        elif causes_1_to_2 and not causes_2_to_1:
            causality_type = f"Nhân quả một chiều: {var1_col} → {var2_col}"
        elif causes_2_to_1 and not causes_1_to_2:
            causality_type = f"Nhân quả một chiều: {var2_col} → {var1_col}"

        # 6. Orthogonalized Impulse Response Functions (OIRF; Cholesky Decomposition)
        Sigma_resid = np.cov(residuals, rowvar=False)  # 2 x 2
        try:
            P_chol = np.linalg.cholesky(Sigma_resid)
        except np.linalg.LinAlgError:
            # Regularize if not strictly positive definite
            Sigma_resid += 1e-5 * np.eye(2)
            P_chol = np.linalg.cholesky(Sigma_resid)

        # Trace OIRF across horizons 0 .. irf_horizons
        oirf_1_to_2 = []  # response of Var2 to shock in Var1
        oirf_2_to_1 = []  # response of Var1 to shock in Var2
        oirf_1_to_1 = []
        oirf_2_to_2 = []

        curr_phi = np.eye(2)
        for h in range(irf_horizons + 1):
            psi_h = curr_phi @ P_chol
            oirf_1_to_1.append(float(psi_h[0, 0]))
            oirf_2_to_1.append(float(psi_h[0, 1]))
            oirf_1_to_2.append(float(psi_h[1, 0]))
            oirf_2_to_2.append(float(psi_h[1, 1]))
            curr_phi = curr_phi @ A_comp

        # 7. Forecast Error Variance Decomposition (FEVD) at horizon 5
        # Proportion of variance of Var1 explained by Var2, and vice versa
        total_var1_h = sum(oirf_1_to_1[h]**2 + oirf_2_to_1[h]**2 for h in range(min(len(oirf_1_to_1), 6)))
        total_var2_h = sum(oirf_1_to_2[h]**2 + oirf_2_to_2[h]**2 for h in range(min(len(oirf_1_to_2), 6)))
        fevd_var1_from_var2 = float(sum(oirf_2_to_1[h]**2 for h in range(min(len(oirf_2_to_1), 6))) / total_var1_h * 100.0) if total_var1_h > 0 else 0.0
        fevd_var2_from_var1 = float(sum(oirf_1_to_2[h]**2 for h in range(min(len(oirf_1_to_2), 6))) / total_var2_h * 100.0) if total_var2_h > 0 else 0.0

        # 8. Generate Vector SVG Dual-Panel Chart
        svg_chart = cls._generate_svg_chart(
            var1_name=var1_col,
            var2_name=var2_col,
            oirf_1_to_2=oirf_1_to_2,
            oirf_2_to_1=oirf_2_to_1,
            wald_1_to_2=wald_1_to_2,
            p_1_to_2=p_1_to_2,
            wald_2_to_1=wald_2_to_1,
            p_2_to_1=p_2_to_1,
            is_stable=is_stable,
            max_modulus=max_modulus
        )

        # 9. APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_units=len(valid_units),
            total_obs=M,
            var1_name=var1_col,
            var2_name=var2_col,
            a11=a11,
            a12=a12,
            a21=a21,
            a22=a22,
            wald_1_to_2=wald_1_to_2,
            p_1_to_2=p_1_to_2,
            wald_2_to_1=wald_2_to_1,
            p_2_to_1=p_2_to_1,
            causality_type=causality_type,
            fevd_1_from_2=fevd_var1_from_var2,
            fevd_2_from_1=fevd_var2_from_var1,
            is_stable=is_stable,
            max_modulus=max_modulus
        )

        return {
            "status": "success",
            "panel_units_count": len(valid_units),
            "effective_observations": M,
            "lags": lags,
            "var1_name": var1_col,
            "var2_name": var2_col,
            "is_stable": is_stable,
            "stability_max_modulus": round(max_modulus, 4),
            "causality_conclusion": causality_type,
            "equations": {
                "eq_var1": {
                    "dependent_var": var1_col,
                    "coeff_self_lag": round(a11, 4),
                    "se_self_lag": round(se_a11, 4),
                    "coeff_cross_lag": round(a12, 4),
                    "se_cross_lag": round(se_a12, 4)
                },
                "eq_var2": {
                    "dependent_var": var2_col,
                    "coeff_cross_lag": round(a21, 4),
                    "se_cross_lag": round(se_a21, 4),
                    "coeff_self_lag": round(a22, 4),
                    "se_self_lag": round(se_a22, 4)
                }
            },
            "granger_causality": {
                "var1_causes_var2": {
                    "wald_chi2": round(wald_1_to_2, 4),
                    "p_value": round(p_1_to_2, 4),
                    "is_significant": causes_1_to_2
                },
                "var2_causes_var1": {
                    "wald_chi2": round(wald_2_to_1, 4),
                    "p_value": round(p_2_to_1, 4),
                    "is_significant": causes_2_to_1
                }
            },
            "fevd_horizon_5": {
                "var1_explained_by_var2_pct": round(fevd_var1_from_var2, 2),
                "var2_explained_by_var1_pct": round(fevd_var2_from_var1, 2)
            },
            "oirf_trajectory": {
                "response_of_var2_to_var1": [round(x, 4) for x in oirf_1_to_2],
                "response_of_var1_to_var2": [round(x, 4) for x in oirf_2_to_1]
            },
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        var1_name: str,
        var2_name: str,
        oirf_1_to_2: List[float],
        oirf_2_to_1: List[float],
        wald_1_to_2: float,
        p_1_to_2: float,
        wald_2_to_1: float,
        p_2_to_1: float,
        is_stable: bool,
        max_modulus: float
    ) -> str:
        """
        Generate SVG Dual-Panel:
        - Panel A: Orthogonalized Impulse Response Functions (OIRF) across Horizons.
        - Panel B: Directional Granger Causality Network Diagram.
        """
        w, h = 820, 480
        pad_l, pad_r, pad_t, pad_b = 80, 40, 50, 40
        p1_h = 190
        p2_y = pad_t + p1_h + 50
        p2_h = h - p2_y - pad_b

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'style="background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, '
            f'\'Segoe UI\', Roboto, sans-serif;">'
        ]

        # Title
        svg_parts.append(
            f'<text x="{w/2}" y="28" text-anchor="middle" fill="#f8fafc" '
            f'font-size="14" font-weight="700" letter-spacing="0.5">'
            f'PANEL VAR & DYNAMIC GRANGER CAUSALITY DECOMPOSITION</text>'
        )

        # Stability Indicator
        stab_color = "#10b981" if is_stable else "#ef4444"
        stab_text = f"Ổn định (|λ|_max = {max_modulus:.2f} < 1)" if is_stable else f"Không ổn định (|λ| = {max_modulus:.2f})"
        svg_parts.append(
            f'<rect x="{w - 230}" y="12" width="210" height="24" rx="6" fill="#1e293b" stroke="#334155"/>'
            f'<circle cx="{w - 215}" cy="24" r="4" fill="{stab_color}"/>'
            f'<text x="{w - 120}" y="28" text-anchor="middle" fill="#cbd5e1" font-size="10" font-weight="600">'
            f'{stab_text}</text>'
        )

        # ---------------- Panel A: OIRF Impulse Responses ----------------
        p1_w = w - pad_l - pad_r
        svg_parts.append(
            f'<text x="{pad_l}" y="{pad_t - 10}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL A: Hàm Phản ứng Đẩy Trực giao (Orthogonalized IRF: Horizons h = 0 .. {len(oirf_1_to_2)-1})</text>'
        )

        all_irfs = oirf_1_to_2 + oirf_2_to_1 + [0.0]
        min_irf = min(all_irfs) - 0.1 * abs(min(all_irfs) if min(all_irfs) != 0 else 1.0)
        max_irf = max(all_irfs) + 0.1 * abs(max(all_irfs) if max(all_irfs) != 0 else 1.0)
        if min_irf >= max_irf:
            min_irf, max_irf = -0.5, 0.5

        def h_to_px(hor: int) -> float:
            return pad_l + (hor / (len(oirf_1_to_2) - 1)) * p1_w

        def irf_to_py(val: float) -> float:
            return pad_t + p1_h - ((val - min_irf) / (max_irf - min_irf)) * (p1_h - 20)

        # Zero reference line
        y_zero = irf_to_py(0.0)
        svg_parts.append(
            f'<line x1="{pad_l}" y1="{y_zero}" x2="{pad_l + p1_w}" y2="{y_zero}" '
            f'stroke="#475569" stroke-dasharray="3,3" stroke-width="1"/>'
        )

        # Path 1: Response of Var2 to Shock in Var1 (Cyan)
        pts_1_2 = " ".join(f"{h_to_px(idx)},{irf_to_py(val)}" for idx, val in enumerate(oirf_1_to_2))
        svg_parts.append(
            f'<polyline points="{pts_1_2}" fill="none" stroke="#06b6d4" stroke-width="2.5"/>'
        )
        for idx, val in enumerate(oirf_1_to_2):
            svg_parts.append(f'<circle cx="{h_to_px(idx)}" cy="{irf_to_py(val)}" r="3.5" fill="#06b6d4"/>')

        # Path 2: Response of Var1 to Shock in Var2 (Emerald)
        pts_2_1 = " ".join(f"{h_to_px(idx)},{irf_to_py(val)}" for idx, val in enumerate(oirf_2_to_1))
        svg_parts.append(
            f'<polyline points="{pts_2_1}" fill="none" stroke="#10b981" stroke-width="2.5" stroke-dasharray="5,3"/>'
        )
        for idx, val in enumerate(oirf_2_to_1):
            svg_parts.append(f'<circle cx="{h_to_px(idx)}" cy="{irf_to_py(val)}" r="3.5" fill="#10b981"/>')

        # X-Axis Ticks
        for hor in range(len(oirf_1_to_2)):
            hx = h_to_px(hor)
            svg_parts.append(
                f'<line x1="{hx}" y1="{pad_t + p1_h}" x2="{hx}" y2="{pad_t + p1_h + 4}" stroke="#64748b"/>'
                f'<text x="{hx}" y="{pad_t + p1_h + 14}" text-anchor="middle" fill="#64748b" font-size="10">'
                f't+{hor}</text>'
            )

        # Legend Panel A
        svg_parts.append(
            f'<circle cx="{pad_l + p1_w - 280}" cy="{pad_t + 15}" r="4" fill="#06b6d4"/>'
            f'<text x="{pad_l + p1_w - 270}" y="{pad_t + 18}" fill="#cbd5e1" font-size="10">'
            f'Cú sốc {var1_name[:10]} → {var2_name[:10]}</text>'
            f'<circle cx="{pad_l + p1_w - 120}" cy="{pad_t + 15}" r="4" fill="#10b981"/>'
            f'<text x="{pad_l + p1_w - 110}" y="{pad_t + 18}" fill="#cbd5e1" font-size="10">'
            f'Cú sốc {var2_name[:10]} → {var1_name[:10]}</text>'
        )

        # ---------------- Panel B: Directional Granger Causality Network ----------------
        svg_parts.append(
            f'<text x="{pad_l}" y="{p2_y - 12}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL B: Sơ đồ Mạng lưới Kiểm định Nhân quả Granger (Granger Causality Network)</text>'
        )

        box_w, box_h = 160, 50
        n1_x, n1_y = pad_l + 80, p2_y + p2_h / 2 - box_h / 2
        n2_x, n2_y = pad_l + p1_w - 80 - box_w, p2_y + p2_h / 2 - box_h / 2

        # Node 1 Box
        svg_parts.append(
            f'<rect x="{n1_x}" y="{n1_y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="#1e293b" stroke="#06b6d4" stroke-width="2"/>'
            f'<text x="{n1_x + box_w/2}" y="{n1_y + 30}" text-anchor="middle" fill="#f8fafc" '
            f'font-size="12" font-weight="700">{var1_name[:18]}</text>'
        )

        # Node 2 Box
        svg_parts.append(
            f'<rect x="{n2_x}" y="{n2_y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="#1e293b" stroke="#10b981" stroke-width="2"/>'
            f'<text x="{n2_x + box_w/2}" y="{n2_y + 30}" text-anchor="middle" fill="#f8fafc" '
            f'font-size="12" font-weight="700">{var2_name[:18]}</text>'
        )

        # Arrow 1: Node 1 -> Node 2 (Top curved arrow)
        arrow1_color = "#06b6d4" if p_1_to_2 < 0.05 else "#475569"
        arrow1_dash = "" if p_1_to_2 < 0.05 else 'stroke-dasharray="4,3"'
        y_arrow1 = n1_y + 12
        svg_parts.append(
            f'<line x1="{n1_x + box_w + 10}" y1="{y_arrow1}" x2="{n2_x - 15}" y2="{y_arrow1}" '
            f'stroke="{arrow1_color}" stroke-width="2.5" {arrow1_dash}/>'
            f'<polygon points="{n2_x - 15},{y_arrow1-4} {n2_x - 5},{y_arrow1} {n2_x - 15},{y_arrow1+4}" '
            f'fill="{arrow1_color}"/>'
            f'<text x="{(n1_x + box_w + n2_x)/2}" y="{y_arrow1 - 6}" text-anchor="middle" '
            f'fill="{arrow1_color}" font-size="10" font-weight="600">'
            f'Wald χ² = {wald_1_to_2:.2f} (p = {p_1_to_2:.3f})</text>'
        )

        # Arrow 2: Node 2 -> Node 1 (Bottom arrow)
        arrow2_color = "#10b981" if p_2_to_1 < 0.05 else "#475569"
        arrow2_dash = "" if p_2_to_1 < 0.05 else 'stroke-dasharray="4,3"'
        y_arrow2 = n1_y + box_h - 12
        svg_parts.append(
            f'<line x1="{n2_x - 10}" y1="{y_arrow2}" x2="{n1_x + box_w + 15}" y2="{y_arrow2}" '
            f'stroke="{arrow2_color}" stroke-width="2.5" {arrow2_dash}/>'
            f'<polygon points="{n1_x + box_w + 15},{y_arrow2-4} {n1_x + box_w + 5},{y_arrow2} {n1_x + box_w + 15},{y_arrow2+4}" '
            f'fill="{arrow2_color}"/>'
            f'<text x="{(n1_x + box_w + n2_x)/2}" y="{y_arrow2 + 15}" text-anchor="middle" '
            f'fill="{arrow2_color}" font-size="10" font-weight="600">'
            f'Wald χ² = {wald_2_to_1:.2f} (p = {p_2_to_1:.3f})</text>'
        )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_units: int,
        total_obs: int,
        var1_name: str,
        var2_name: str,
        a11: float,
        a12: float,
        a21: float,
        a22: float,
        wald_1_to_2: float,
        p_1_to_2: float,
        wald_2_to_1: float,
        p_2_to_1: float,
        causality_type: str,
        fevd_1_from_2: float,
        fevd_2_from_1: float,
        is_stable: bool,
        max_modulus: float
    ) -> str:
        """
        Generate APA 7th Edition narrative for Panel VAR & Granger Causality.
        """
        stab_str = (
            f"Mô hình đạt điều kiện ổn định động học với giá trị trị tuyệt đối riêng lớn nhất |lambda|_max = {max_modulus:.3f} < 1.0."
            if is_stable
            else f"Cảnh báo: Mô hình tiến gần hoặc vượt ranh giới ổn định (|lambda|_max = {max_modulus:.3f} >= 1.0)."
        )

        narrative = (
            f"Mô hình Tự hồi quy Vector Dữ liệu Bảng (Panel VAR; Holtz-Eakin et al., 1988; Abrigo & Love, 2016) "
            f"được ước lượng trên mẫu N = {n_units} đơn vị khảo sát lặp với tổng số M = {total_obs} quan sát hiệu dụng "
            f"sau biến đổi trực giao Helmert (Arellano & Bover, 1995) để triệt tiêu hiệu ứng cố định cá thể. {stab_str} "
            f"Kết quả kiểm định nhân quả Granger (Panel Granger Causality Wald test): "
            f"Tác động trễ từ {var1_name} lên {var2_name} đạt Wald chi2(1) = {wald_1_to_2:.2f} (p = {p_1_to_2:.4f}, a21 = {a21:+.3f}); "
            f"tác động trễ từ {var2_name} lên {var1_name} đạt Wald chi2(1) = {wald_2_to_1:.2f} (p = {p_2_to_1:.4f}, a12 = {a12:+.3f}). "
            f"Kết luận cấu trúc nhân quả: {causality_type}. "
            f"Phân rã phương sai sai số dự báo (FEVD ở bước 5) chỉ ra rằng {fevd_2_from_1:.1f}% biến thiên tương lai của {var2_name} "
            f"được giải thích bởi cú sốc từ {var1_name}, trong khi {fevd_1_from_2:.1f}% biến thiên của {var1_name} do {var2_name} giải thích."
        )
        return narrative
