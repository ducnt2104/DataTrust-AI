"""
DataTrust - Instrumental Variables Two-Stage Least Squares (2SLS) Engine
=======================================================================
Implements 2SLS estimation for endogenous survey predictors with
rigorous weak instrument diagnostics and specification testing.

Methodological references:
- Wright, P. G. (1928). The Tariff on Animal and Vegetable Oils. Macmillan.
- Angrist, J. D., & Imbens, G. W. (1995). Identification and estimation of
  local average treatment effects. Econometrica, 62(2), 467-475.
- Staiger, D., & Stock, J. H. (1997). Instrumental variables regression with weak
  instruments. Econometrica, 65(3), 557-586.
- Stock, J. H., & Yogo, M. (2005). Testing for weak instruments in linear IV
  regression. In Identification and Inference for Econometric Models, pp. 80-108.
- Hausman, J. A. (1978). Specification tests in econometrics. Econometrica, 46(6), 1251-1271.
- Sargan, J. D. (1958). The estimation of economic relationships using instrumental
  variables. Econometrica, 26(3), 393-415.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import scipy.stats as stats


class IV2SLSEngine:
    """
    Two-Stage Least Squares (2SLS) & Weak Instrument Diagnostics Estimator.
    """

    @classmethod
    def estimate(
        cls,
        Y: np.ndarray,
        X_endog: np.ndarray,
        Z_instruments: np.ndarray,
        W_controls: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Run complete 2SLS regression with first-stage F-test, Wu-Hausman, and Sargan J-test.
        """
        N = len(Y)
        if N < 12:
            return {
                "status": "insufficient_data",
                "message": "Cần tối thiểu 12 quan sát hợp lệ để thực hiện hồi quy biến công cụ 2SLS."
            }

        Y = np.asarray(Y, dtype=float).reshape(N, 1)
        X = np.asarray(X_endog, dtype=float).reshape(N, 1)
        Z = np.asarray(Z_instruments, dtype=float)
        if Z.ndim == 1:
            Z = Z.reshape(N, 1)
        L = Z.shape[1]  # number of excluded instruments

        if W_controls is not None and len(W_controls) > 0:
            W = np.asarray(W_controls, dtype=float)
            if W.ndim == 1:
                W = W.reshape(N, 1)
            K_exog = W.shape[1]
            Z_full = np.column_stack([np.ones(N), W, Z])
            X_full = np.column_stack([np.ones(N), W, X])
            Z_restricted = np.column_stack([np.ones(N), W])
        else:
            K_exog = 0
            Z_full = np.column_stack([np.ones(N), Z])
            X_full = np.column_stack([np.ones(N), X])
            Z_restricted = np.ones((N, 1))

        # Check for collinearity / full rank
        if np.linalg.matrix_rank(Z_full) < Z_full.shape[1]:
            return {
                "status": "collinear_instruments",
                "message": "Ma trận biến công cụ bị phụ thuộc tuyến tính hoặc suy biến."
            }

        # ---------------- STAGE 1: First-Stage Regression ----------------
        # X = Z_full @ gamma + v
        gamma_hat = np.linalg.lstsq(Z_full, X, rcond=None)[0]
        X_hat = Z_full @ gamma_hat
        v_hat = X - X_hat

        # Restricted model (excluding instruments Z)
        gamma_restr = np.linalg.lstsq(Z_restricted, X, rcond=None)[0]
        X_restr_hat = Z_restricted @ gamma_restr

        rss_unrestr = float(np.sum(v_hat ** 2))
        rss_restr = float(np.sum((X - X_restr_hat) ** 2))
        df_num = L
        df_denom = N - Z_full.shape[1]

        if rss_unrestr > 1e-12 and df_denom > 0:
            first_stage_f = float(((rss_restr - rss_unrestr) / df_num) / (rss_unrestr / df_denom))
            first_stage_p = float(1.0 - stats.f.cdf(first_stage_f, df_num, df_denom))
        else:
            first_stage_f = 0.0
            first_stage_p = 1.0

        is_weak_instrument = bool(first_stage_f < 10.0)
        stock_yogo_10_crit = 16.38 if L == 1 else (19.93 if L == 2 else 22.30)
        stock_yogo_15_crit = 8.96 if L == 1 else (11.59 if L == 2 else 12.83)

        # ---------------- STAGE 2: 2SLS Structural Estimation ----------------
        # Design matrix using fitted X_hat
        if W_controls is not None and len(W_controls) > 0:
            X_stage2 = np.column_stack([np.ones(N), W, X_hat])
        else:
            X_stage2 = np.column_stack([np.ones(N), X_hat])

        beta_2sls = np.linalg.lstsq(X_stage2, Y, rcond=None)[0]

        # Crucial: True structural residuals MUST use original X, not X_hat!
        structural_residuals = Y - (X_full @ beta_2sls)
        sigma2_2sls = float(np.sum(structural_residuals ** 2) / (N - X_full.shape[1]))

        # Covariance matrix: sigma2 * (X_stage2.T @ X_stage2)^(-1)
        xtx_inv = np.linalg.inv(X_stage2.T @ X_stage2)
        cov_2sls = sigma2_2sls * xtx_inv
        se_2sls = np.sqrt(np.maximum(1e-14, np.diag(cov_2sls)))

        # Parameter of interest: endogenous regressor beta_1 (the last column of X_full)
        endog_idx = -1
        b_iv = float(beta_2sls[endog_idx, 0])
        se_iv = float(se_2sls[endog_idx])
        z_iv = float(b_iv / se_iv) if se_iv > 1e-12 else 0.0
        p_iv = float(2.0 * (1.0 - stats.norm.cdf(abs(z_iv))))
        ci_iv_lower = float(b_iv - 1.96 * se_iv)
        ci_iv_upper = float(b_iv + 1.96 * se_iv)

        # ---------------- OLS Benchmark Regression ----------------
        beta_ols = np.linalg.lstsq(X_full, Y, rcond=None)[0]
        ols_residuals = Y - (X_full @ beta_ols)
        sigma2_ols = float(np.sum(ols_residuals ** 2) / (N - X_full.shape[1]))
        cov_ols = sigma2_ols * np.linalg.inv(X_full.T @ X_full)
        se_ols = np.sqrt(np.maximum(1e-14, np.diag(cov_ols)))
        b_ols = float(beta_ols[endog_idx, 0])
        se_ols_val = float(se_ols[endog_idx])
        t_ols = float(b_ols / se_ols_val) if se_ols_val > 1e-12 else 0.0
        p_ols = float(2.0 * (1.0 - stats.t.cdf(abs(t_ols), df=N - X_full.shape[1])))

        # ---------------- Wu-Hausman Endogeneity Test ----------------
        # Regress Y on X_full and first-stage residuals v_hat
        X_hausman = np.column_stack([X_full, v_hat])
        beta_hausman = np.linalg.lstsq(X_hausman, Y, rcond=None)[0]
        res_h = Y - (X_hausman @ beta_hausman)
        sigma2_h = float(np.sum(res_h ** 2) / (N - X_hausman.shape[1]))
        cov_h = sigma2_h * np.linalg.inv(X_hausman.T @ X_hausman)
        delta_v = float(beta_hausman[-1, 0])
        se_delta_v = float(np.sqrt(np.maximum(1e-14, cov_h[-1, -1])))
        t_hausman = float(delta_v / se_delta_v) if se_delta_v > 1e-12 else 0.0
        p_hausman = float(2.0 * (1.0 - stats.t.cdf(abs(t_hausman), df=N - X_hausman.shape[1])))
        is_endogenous = bool(p_hausman < 0.05)

        # ---------------- Sargan-Hansen Overidentification Test ----------------
        sargan_stat: Optional[float] = None
        sargan_p: Optional[float] = None
        sargan_valid: Optional[bool] = None

        if L > 1:
            # Regress structural residuals e* on all instruments and controls Z_full
            res_sargan_regr = np.linalg.lstsq(Z_full, structural_residuals, rcond=None)[0]
            e_hat_sargan = Z_full @ res_sargan_regr
            ss_tot_sargan = float(np.sum((structural_residuals - np.mean(structural_residuals)) ** 2))
            ss_exp_sargan = float(np.sum((e_hat_sargan - np.mean(structural_residuals)) ** 2))
            r2_sargan = max(0.0, min(1.0, ss_exp_sargan / ss_tot_sargan)) if ss_tot_sargan > 1e-12 else 0.0
            sargan_stat = float(N * r2_sargan)
            df_sargan = L - 1
            sargan_p = float(1.0 - stats.chi2.cdf(sargan_stat, df=df_sargan))
            sargan_valid = bool(sargan_p >= 0.05)

        # ---------------- Generate Vector SVG ----------------
        svg_chart = cls._generate_svg_chart(
            Z_first=Z[:, 0],
            X_endog=X[:, 0],
            first_stage_f=first_stage_f,
            b_iv=b_iv,
            se_iv=se_iv,
            ci_iv_lower=ci_iv_lower,
            ci_iv_upper=ci_iv_upper,
            b_ols=b_ols,
            se_ols=se_ols_val
        )

        # ---------------- APA 7th Edition Narrative ----------------
        apa_narrative = cls._generate_apa_narrative(
            n_obs=N,
            l_instruments=L,
            first_stage_f=first_stage_f,
            first_stage_p=first_stage_p,
            is_weak=is_weak_instrument,
            b_iv=b_iv,
            se_iv=se_iv,
            z_iv=z_iv,
            p_iv=p_iv,
            ci_iv_lower=ci_iv_lower,
            ci_iv_upper=ci_iv_upper,
            b_ols=b_ols,
            se_ols=se_ols_val,
            p_ols=p_ols,
            t_hausman=t_hausman,
            p_hausman=p_hausman,
            is_endog=is_endogenous,
            sargan_stat=sargan_stat,
            sargan_p=sargan_p,
            sargan_valid=sargan_valid
        )

        return {
            "status": "success",
            "sample_size": N,
            "instruments_count": L,
            "iv_estimate": {
                "beta": round(b_iv, 4),
                "se": round(se_iv, 4),
                "z_stat": round(z_iv, 4),
                "p_value": round(p_iv, 4),
                "ci_95_lower": round(ci_iv_lower, 4),
                "ci_95_upper": round(ci_iv_upper, 4),
                "is_significant": bool(p_iv < 0.05)
            },
            "ols_benchmark": {
                "beta": round(b_ols, 4),
                "se": round(se_ols_val, 4),
                "t_stat": round(t_ols, 4),
                "p_value": round(p_ols, 4),
                "bias_difference": round(b_ols - b_iv, 4)
            },
            "first_stage_diagnostics": {
                "f_statistic": round(first_stage_f, 4),
                "p_value": round(first_stage_p, 4),
                "is_weak_instrument": is_weak_instrument,
                "staiger_stock_rule_of_thumb": 10.0,
                "stock_yogo_10_pct_critical_value": stock_yogo_10_crit,
                "stock_yogo_15_pct_critical_value": stock_yogo_15_crit
            },
            "wu_hausman_test": {
                "t_statistic": round(t_hausman, 4),
                "p_value": round(p_hausman, 4),
                "is_endogenous": is_endogenous
            },
            "sargan_hansen_overid_test": {
                "j_statistic": round(sargan_stat, 4) if sargan_stat is not None else None,
                "p_value": round(sargan_p, 4) if sargan_p is not None else None,
                "instruments_valid": sargan_valid,
                "degrees_of_freedom": L - 1 if L > 1 else None
            },
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        Z_first: np.ndarray,
        X_endog: np.ndarray,
        first_stage_f: float,
        b_iv: float,
        se_iv: float,
        ci_iv_lower: float,
        ci_iv_upper: float,
        b_ols: float,
        se_ols: float
    ) -> str:
        """
        Generate SVG Dual-Panel Chart:
        - Panel 1: First-Stage Strength Scatter & Regression Fit with F-Gauge.
        - Panel 2: 2SLS vs OLS Estimate Forest Plot with 95% Confidence Intervals.
        """
        w, h = 820, 480
        pad_l, pad_r, pad_t, pad_b = 80, 40, 50, 40
        p1_h = 180
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
            f'INSTRUMENTAL VARIABLES (2SLS) & WEAK INSTRUMENT DIAGNOSTICS</text>'
        )

        # ---------------- Panel 1: First-Stage Instrument Strength ----------------
        p1_w = w - pad_l - pad_r
        f_badge_color = "#10b981" if first_stage_f >= 10.0 else "#ef4444"
        f_badge_text = "MẠNH (F ≥ 10)" if first_stage_f >= 10.0 else "YẾU (F < 10)"

        svg_parts.append(
            f'<text x="{pad_l}" y="{pad_t - 10}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL A: Giai đoạn 1 (First-Stage Fit: Z → X) — First-Stage F = {first_stage_f:.2f} '
            f'[{f_badge_text}]</text>'
        )

        min_z, max_z = float(np.min(Z_first)), float(np.max(Z_first))
        min_x, max_x = float(np.min(X_endog)), float(np.max(X_endog))
        if min_z >= max_z:
            min_z, max_z = min_z - 1.0, max_z + 1.0
        if min_x >= max_x:
            min_x, max_x = min_x - 1.0, max_x + 1.0

        def z_to_px(z_val: float) -> float:
            return pad_l + ((z_val - min_z) / (max_z - min_z)) * (p1_w - 180)

        def x_to_py(x_val: float) -> float:
            return pad_t + p1_h - ((x_val - min_x) / (max_x - min_x)) * (p1_h - 20)

        # Draw scatter points
        for zv, xv in zip(Z_first[:100], X_endog[:100]):
            svg_parts.append(
                f'<circle cx="{z_to_px(zv)}" cy="{x_to_py(xv)}" r="3" fill="#38bdf8" fill-opacity="0.6"/>'
            )

        # Draw regression line
        poly = np.polyfit(Z_first, X_endog, 1)
        x1_line = np.polyval(poly, min_z)
        x2_line = np.polyval(poly, max_z)
        svg_parts.append(
            f'<line x1="{z_to_px(min_z)}" y1="{x_to_py(x1_line)}" '
            f'x2="{z_to_px(max_z)}" y2="{x_to_py(x2_line)}" '
            f'stroke="#06b6d4" stroke-width="2.5"/>'
        )

        # F-Statistic Instrument Strength Gauge (on right side of Panel 1)
        gauge_x = w - pad_r - 140
        gauge_y = pad_t + 10
        svg_parts.append(
            f'<rect x="{gauge_x}" y="{gauge_y}" width="130" height="150" rx="8" '
            f'fill="#1e293b" stroke="#334155" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{gauge_x + 65}" y="{gauge_y + 24}" text-anchor="middle" fill="#94a3b8" '
            f'font-size="10" font-weight="600">FIRST-STAGE F</text>'
        )
        svg_parts.append(
            f'<text x="{gauge_x + 65}" y="{gauge_y + 58}" text-anchor="middle" fill="{f_badge_color}" '
            f'font-size="22" font-weight="800">{first_stage_f:.1f}</text>'
        )
        svg_parts.append(
            f'<line x1="{gauge_x + 15}" y1="{gauge_y + 75}" x2="{gauge_x + 115}" y2="{gauge_y + 75}" '
            f'stroke="#475569" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{gauge_x + 65}" y="{gauge_y + 96}" text-anchor="middle" fill="#cbd5e1" font-size="9">'
            f'Staiger-Stock: 10.0</text>'
        )
        svg_parts.append(
            f'<text x="{gauge_x + 65}" y="{gauge_y + 114}" text-anchor="middle" fill="#cbd5e1" font-size="9">'
            f'Stock-Yogo 10%: 16.4</text>'
        )
        svg_parts.append(
            f'<rect x="{gauge_x + 20}" y="{gauge_y + 124}" width="90" height="18" rx="4" fill="{f_badge_color}" fill-opacity="0.2"/>'
            f'<text x="{gauge_x + 65}" y="{gauge_y + 137}" text-anchor="middle" fill="{f_badge_color}" font-size="9" font-weight="700">'
            f'{f_badge_text}</text>'
        )

        # Baseline axis for Panel 1
        svg_parts.append(
            f'<line x1="{pad_l}" y1="{pad_t + p1_h}" x2="{pad_l + p1_w - 170}" y2="{pad_t + p1_h}" '
            f'stroke="#475569" stroke-width="1"/>'
        )

        # ---------------- Panel 2: 2SLS vs OLS Forest Plot ----------------
        svg_parts.append(
            f'<text x="{pad_l}" y="{p2_y - 12}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL B: So sánh Hệ số Ước lượng 2SLS (Không chệch) vs OLS (Có thiên lệch chọn lọc)</text>'
        )

        # Domain for beta
        ci_ols_l = b_ols - 1.96 * se_ols
        ci_ols_u = b_ols + 1.96 * se_ols
        all_betas = [b_iv, ci_iv_lower, ci_iv_upper, b_ols, ci_ols_l, ci_ols_u, 0.0]
        min_b = min(all_betas) - 0.2 * abs(min(all_betas) if min(all_betas) != 0 else 1.0)
        max_b = max(all_betas) + 0.2 * abs(max(all_betas) if max(all_betas) != 0 else 1.0)
        if min_b >= max_b:
            min_b, max_b = -1.0, 1.0

        def b_to_px(b_val: float) -> float:
            return pad_l + 140 + ((b_val - min_b) / (max_b - min_b)) * (p1_w - 200)

        # Zero reference line
        x_zero = b_to_px(0.0)
        svg_parts.append(
            f'<line x1="{x_zero}" y1="{p2_y}" x2="{x_zero}" y2="{p2_y + p2_h}" '
            f'stroke="#475569" stroke-dasharray="3,3" stroke-width="1.2"/>'
        )

        # Row 1: 2SLS Estimate (Emerald)
        y_r1 = p2_y + 35
        x_iv_pt = b_to_px(b_iv)
        x_iv_l = b_to_px(ci_iv_lower)
        x_iv_r = b_to_px(ci_iv_upper)

        svg_parts.append(
            f'<text x="{pad_l}" y="{y_r1 + 4}" fill="#10b981" font-size="12" font-weight="700">'
            f'2SLS (IV Corrected)</text>'
        )
        svg_parts.append(
            f'<line x1="{x_iv_l}" y1="{y_r1}" x2="{x_iv_r}" y2="{y_r1}" stroke="#10b981" stroke-width="2.5"/>'
        )
        svg_parts.append(
            f'<line x1="{x_iv_l}" y1="{y_r1 - 4}" x2="{x_iv_l}" y2="{y_r1 + 4}" stroke="#10b981" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<line x1="{x_iv_r}" y1="{y_r1 - 4}" x2="{x_iv_r}" y2="{y_r1 + 4}" stroke="#10b981" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<circle cx="{x_iv_pt}" cy="{y_r1}" r="5" fill="#10b981"/>'
        )
        svg_parts.append(
            f'<text x="{pad_l + p1_w}" y="{y_r1 + 4}" text-anchor="end" fill="#10b981" '
            f'font-size="11" font-family="monospace" font-weight="600">'
            f'{b_iv:+.3f} [{ci_iv_lower:.2f}, {ci_iv_upper:.2f}] (SE={se_iv:.2f})</text>'
        )

        # Row 2: OLS Benchmark (Amber)
        y_r2 = p2_y + 75
        x_ols_pt = b_to_px(b_ols)
        x_ols_l = b_to_px(ci_ols_l)
        x_ols_r = b_to_px(ci_ols_u)

        svg_parts.append(
            f'<text x="{pad_l}" y="{y_r2 + 4}" fill="#f59e0b" font-size="12" font-weight="600">'
            f'OLS (Biased Base)</text>'
        )
        svg_parts.append(
            f'<line x1="{x_ols_l}" y1="{y_r2}" x2="{x_ols_r}" y2="{y_r2}" stroke="#f59e0b" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<circle cx="{x_ols_pt}" cy="{y_r2}" r="4.5" fill="#f59e0b"/>'
        )
        svg_parts.append(
            f'<text x="{pad_l + p1_w}" y="{y_r2 + 4}" text-anchor="end" fill="#f59e0b" '
            f'font-size="11" font-family="monospace">'
            f'{b_ols:+.3f} [{ci_ols_l:.2f}, {ci_ols_u:.2f}] (SE={se_ols:.2f})</text>'
        )

        # Baseline axis for Panel 2
        y_axis2 = p2_y + p2_h - 10
        svg_parts.append(
            f'<line x1="{pad_l + 130}" y1="{y_axis2}" x2="{pad_l + p1_w - 100}" y2="{y_axis2}" '
            f'stroke="#475569" stroke-width="1"/>'
        )
        for tick_b in np.linspace(min_b, max_b, 5):
            tx = b_to_px(tick_b)
            if pad_l + 125 <= tx <= pad_l + p1_w - 95:
                svg_parts.append(
                    f'<line x1="{tx}" y1="{y_axis2}" x2="{tx}" y2="{y_axis2 + 4}" stroke="#64748b"/>'
                    f'<text x="{tx}" y="{y_axis2 + 15}" text-anchor="middle" fill="#64748b" font-size="9">'
                    f'{tick_b:.2f}</text>'
                )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_obs: int,
        l_instruments: int,
        first_stage_f: float,
        first_stage_p: float,
        is_weak: bool,
        b_iv: float,
        se_iv: float,
        z_iv: float,
        p_iv: float,
        ci_iv_lower: float,
        ci_iv_upper: float,
        b_ols: float,
        se_ols: float,
        p_ols: float,
        t_hausman: float,
        p_hausman: float,
        is_endog: bool,
        sargan_stat: Optional[float],
        sargan_p: Optional[float],
        sargan_valid: Optional[bool]
    ) -> str:
        """
        Generate APA 7th Edition narrative for 2SLS IV results.
        """
        weak_str = (
            f"Thống kê F ở giai đoạn một đạt F = {first_stage_f:.2f} (p = {first_stage_p:.4f}), "
            f"vượt ngưỡng chuẩn mực 10.0 theo nguyên tắc Staiger & Stock (1997), xác nhận biến công cụ có "
            f"độ liên kết mạnh và không vi phạm điều kiện yếu (weak instruments)."
            if not is_weak
            else f"Cảnh báo: Thống kê F ở giai đoạn một chỉ đạt F = {first_stage_f:.2f} (< 10.0), "
                 f"chỉ ra biến công cụ có độ liên kết yếu (weak instrument) theo tiêu chuẩn Stock & Yogo (2005), "
                 f"khiến sai số chuẩn và khoảng tin cậy của ước lượng 2SLS có thể bị nới rộng."
        )

        hausman_str = (
            f"Kiểm định tính nội sinh Wu-Hausman bác bỏ giả thuyết vô hiệu (t = {t_hausman:.2f}, p = {p_hausman:.4f}), "
            f"chứng minh biến dự báo có tính nội sinh thực sự và ước lượng OLS bị thiên lệch có ý nghĩa thống kê, "
            f"khẳng định tính cần thiết của phương pháp 2SLS."
            if is_endog
            else f"Kiểm định Wu-Hausman chưa bác bỏ tính ngoại sinh (t = {t_hausman:.2f}, p = {p_hausman:.4f}), "
                 f"cho thấy sự khác biệt giữa ước lượng 2SLS và OLS chưa đạt ngưỡng ý nghĩa thống kê."
        )

        sargan_str = ""
        if sargan_stat is not None and sargan_p is not None:
            if sargan_valid:
                sargan_str = (
                    f" Kiểm định ràng buộc nhận diện thừa Sargan-Hansen xác nhận tính hợp lệ của hệ biến công cụ "
                    f"(J = {sargan_stat:.2f}, df = {l_instruments - 1}, p = {sargan_p:.4f} ≥ .05), không vi phạm "
                    f"giả định loại trừ (exclusion restriction)."
                )
            else:
                sargan_str = (
                    f" Kiểm định Sargan-Hansen nghi vấn tính hợp lệ của biến công cụ (J = {sargan_stat:.2f}, "
                    f"p = {sargan_p:.4f} < .05), ngụ ý có ít nhất một công cụ tương quan với phần dư cấu trúc."
                )

        sig_str = (
            f"mang ý nghĩa thống kê cao (z = {z_iv:.2f}, p = {p_iv:.4f})"
            if p_iv < 0.05
            else f"chưa đạt ngưỡng ý nghĩa thống kê (z = {z_iv:.2f}, p = {p_iv:.4f})"
        )

        narrative = (
            f"Mô hình hồi quy biến công cụ bình phương tối thiểu hai giai đoạn (2SLS; Angrist & Imbens, 1995; "
            f"Wright, 1928) được ước lượng trên mẫu khảo sát N = {n_obs} với L = {l_instruments} biến công cụ. "
            f"{weak_str} {hausman_str} Ước lượng hệ số cấu trúc không chệch bằng 2SLS đạt beta_2SLS = {b_iv:+.4f} "
            f"(SE = {se_iv:.4f}, 95% CI [{ci_iv_lower:.4f}, {ci_iv_upper:.4f}]), {sig_str}. "
            f"So với ước lượng OLS thông thường (beta_OLS = {b_ols:+.4f}, SE = {se_ols:.4f}), "
            f"ước lượng 2SLS đã hiệu chỉnh độ lệch nội sinh {b_ols - b_iv:+.4f}.{sargan_str}"
        )
        return narrative
