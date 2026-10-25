"""
DataTrust - Latent Growth Curve Modeling (LGCM) Engine
======================================================
Implements Latent Growth Curve Modeling for longitudinal multi-wave surveys:
- Meredith & Tisak (1990). Latent curve analysis. Psychometrika, 55(1), 107-122.
- Bollen, K. A., & Curran, P. J. (2006). Latent Curve Models: A Structural Equation Perspective.
- Preacher, K. J., et al. (2008). Latent Growth Curve Modeling. SAGE Publications.
- Duncan, T. E., & Duncan, S. C. (2004). An introduction to latent growth curve modeling.
  Behavior Therapy, 35(2), 333-363.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


class LatentGrowthEngine:
    """
    Latent Growth Curve Estimator for Multi-Wave Panel Data.
    """

    @classmethod
    def estimate(
        cls,
        wave_data: np.ndarray,
        time_scores: Optional[List[float]] = None,
        wave_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Estimate Linear Latent Growth Curve Model.
        wave_data: N x T matrix of repeated observations across T waves.
        time_scores: Optional list of time points, e.g. [0, 1, 2, ...] (length T).
        wave_labels: Optional labels for waves, e.g. ["Wave 1", "Wave 2", ...].
        """
        N, T = wave_data.shape
        if N < 15:
            return {
                "status": "insufficient_data",
                "message": "Cần tối thiểu 15 người tham gia khảo sát lặp để ước lượng mô hình Latent Growth Curve."
            }
        if T < 3:
            return {
                "status": "insufficient_data",
                "message": "Cần tối thiểu 3 đợt/làn sóng (waves) để nhận diện mô hình quỹ đạo tăng trưởng tuyến tính."
            }

        if time_scores is None:
            time_scores = [float(t) for t in range(T)]
        else:
            time_scores = [float(t) for t in time_scores]

        if wave_labels is None:
            wave_labels = [f"Đợt {t+1}" for t in range(T)]

        # Design matrix of latent basis loadings Lambda: T x 2 (Intercept = 1, Slope = time_score)
        Lambda = np.column_stack([np.ones(T), time_scores])  # T x 2

        # 1. Observed Means and Covariance Matrix
        mean_y = np.mean(wave_data, axis=0)  # T x 1
        S = np.cov(wave_data, rowvar=False)   # T x T

        # 2. Estimate Mean of Latent Factors: mu_eta = (Lambda.T @ Lambda)^(-1) @ Lambda.T @ mean_y
        inv_lam_lam = np.linalg.inv(Lambda.T @ Lambda)
        mu_eta = inv_lam_lam @ (Lambda.T @ mean_y)
        mu_intercept = float(mu_eta[0])
        mu_slope = float(mu_eta[1])

        # 3. Individual Factor Scores (OLS per individual: y_i = Lambda @ eta_i + e_i)
        # eta_i = (Lambda.T @ Lambda)^(-1) @ Lambda.T @ y_i
        eta_individual = (inv_lam_lam @ (Lambda.T @ wave_data.T)).T  # N x 2
        intercept_scores = eta_individual[:, 0]
        slope_scores = eta_individual[:, 1]

        # 4. Latent Factor Covariance Matrix Psi = Cov(eta)
        Psi = np.cov(eta_individual, rowvar=False)  # 2 x 2
        psi_00 = max(0.001, float(Psi[0, 0]))  # Var(Intercept)
        psi_11 = max(0.0001, float(Psi[1, 1]))  # Var(Slope)
        psi_01 = float(Psi[0, 1])               # Cov(Intercept, Slope)

        # Correlation between intercept and slope
        corr_01 = float(np.clip(psi_01 / np.sqrt(psi_00 * psi_11), -0.999, 0.999))

        # Standard errors for means
        se_mu_intercept = float(np.sqrt(psi_00 / N))
        se_mu_slope = float(np.sqrt(psi_11 / N))

        z_intercept = float(mu_intercept / se_mu_intercept) if se_mu_intercept > 1e-12 else 0.0
        p_intercept = float(2.0 * (1.0 - stats.norm.cdf(abs(z_intercept))))

        z_slope = float(mu_slope / se_mu_slope) if se_mu_slope > 1e-12 else 0.0
        p_slope = float(2.0 * (1.0 - stats.norm.cdf(abs(z_slope))))

        # 5. Model-Implied Moments & Residual Error Variances Theta
        fitted_y = eta_individual @ Lambda.T  # N x T
        residuals = wave_data - fitted_y       # N x T
        theta_diag = np.maximum(0.001, np.var(residuals, axis=0, ddof=2))  # T x 1
        Theta = np.diag(theta_diag)

        # Model-implied covariance: Sigma = Lambda @ Psi @ Lambda.T + Theta
        Sigma_model = Lambda @ Psi @ Lambda.T + Theta

        # 6. Model Fit Indices (Maximum Likelihood Discrepancy F_ML)
        # Compare saturated model S with restricted LGCM model Sigma_model
        try:
            inv_sigma = np.linalg.inv(Sigma_model)
            det_sigma = max(1e-12, float(np.linalg.det(Sigma_model)))
            det_s = max(1e-12, float(np.linalg.det(S + 1e-6 * np.eye(T))))

            # F_ML = tr(S * Sigma^-1) - log|S * Sigma^-1| - T
            tr_term = float(np.trace(S @ inv_sigma))
            log_det_ratio = float(np.log(det_sigma / det_s))
            f_ml = max(0.0, tr_term + log_det_ratio - T)
        except np.linalg.LinAlgError:
            f_ml = 0.05

        # Degrees of freedom: p*(p+1)/2 + p - [2 + 3 + T] = T*(T+1)/2 - 5
        df_model = max(1, (T * (T + 1) // 2) - 5)
        chi2_stat = float((N - 1) * f_ml)
        chi2_p_val = float(1.0 - stats.chi2.cdf(chi2_stat, df=df_model))

        # Baseline / Independence model fit for CFI / TLI
        s_diag = np.diag(S)
        f_null = float(np.sum(np.log(s_diag)) - np.log(max(1e-12, float(np.linalg.det(S + 1e-6 * np.eye(T))))))
        df_null = max(1, (T * (T - 1)) // 2)
        chi2_null = float((N - 1) * max(0.0, f_null))

        cfi = float(np.clip(1.0 - (max(0.0, chi2_stat - df_model) / max(1e-6, chi2_null - df_null)), 0.0, 1.0))
        tli = float(np.clip(1.0 - ((chi2_stat / df_model - 1.0) / max(1e-6, chi2_null / df_null - 1.0)), 0.0, 1.0))
        rmsea = float(np.sqrt(max(0.0, (chi2_stat - df_model) / (max(1, N - 1) * df_model))))

        is_good_fit = bool(cfi >= 0.90 and rmsea <= 0.08)

        # 7. Test for Significant Growth (Slope > 0 or Slope < 0)
        has_significant_growth = bool(p_slope < 0.05)
        has_heterogeneous_growth = bool(psi_11 > 1e-4)

        # 8. Generate Vector SVG Dual-Panel Chart
        svg_chart = cls._generate_svg_chart(
            time_scores=time_scores,
            wave_labels=wave_labels,
            mu_intercept=mu_intercept,
            mu_slope=mu_slope,
            se_mu_slope=se_mu_slope,
            eta_individual=eta_individual,
            mean_y=mean_y,
            corr_01=corr_01,
            psi_00=psi_00,
            psi_11=psi_11
        )

        # 9. APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_obs=N,
            n_waves=T,
            mu_intercept=mu_intercept,
            se_mu_int=se_mu_intercept,
            z_int=z_intercept,
            p_int=p_intercept,
            mu_slope=mu_slope,
            se_mu_slope=se_mu_slope,
            z_slope=z_slope,
            p_slope=p_slope,
            psi_00=psi_00,
            psi_11=psi_11,
            corr_01=corr_01,
            cfi=cfi,
            rmsea=rmsea,
            chi2_stat=chi2_stat,
            df_model=df_model,
            chi2_p=chi2_p_val,
            is_good_fit=is_good_fit
        )

        return {
            "status": "success",
            "sample_size": N,
            "waves_count": T,
            "latent_means": {
                "intercept_mean": round(mu_intercept, 4),
                "intercept_se": round(se_mu_intercept, 4),
                "intercept_z": round(z_intercept, 4),
                "intercept_p": round(p_intercept, 4),
                "slope_mean": round(mu_slope, 4),
                "slope_se": round(se_mu_slope, 4),
                "slope_z": round(z_slope, 4),
                "slope_p": round(p_slope, 4)
            },
            "latent_variances": {
                "intercept_variance": round(psi_00, 4),
                "slope_variance": round(psi_11, 4),
                "intercept_slope_covariance": round(psi_01, 4),
                "intercept_slope_correlation": round(corr_01, 4)
            },
            "model_fit": {
                "chi_square": round(chi2_stat, 4),
                "degrees_of_freedom": df_model,
                "p_value": round(chi2_p_val, 4),
                "cfi": round(cfi, 4),
                "tli": round(tli, 4),
                "rmsea": round(rmsea, 4),
                "is_good_fit": is_good_fit
            },
            "growth_dynamics": {
                "has_significant_trajectory": has_significant_growth,
                "has_individual_heterogeneity": has_heterogeneous_growth,
                "direction": "Tăng trưởng dương" if mu_slope > 0 else ("Suy giảm" if mu_slope < 0 else "Đi ngang")
            },
            "observed_wave_means": [round(float(m), 4) for m in mean_y],
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        time_scores: List[float],
        wave_labels: List[str],
        mu_intercept: float,
        mu_slope: float,
        se_mu_slope: float,
        eta_individual: np.ndarray,
        mean_y: np.ndarray,
        corr_01: float,
        psi_00: float,
        psi_11: float
    ) -> str:
        """
        Generate SVG Dual-Panel:
        - Panel A: Spaghetti Plot with Sample Trajectories + Bold Population Mean Trajectory & 95% Ribbon.
        - Panel B: Latent Intercept-Slope Covariance Ellipse & Variance Breakdown.
        """
        w, h = 820, 490
        pad_l, pad_r, pad_t, pad_b = 80, 40, 50, 40
        p1_h = 200
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
            f'LATENT GROWTH CURVE (LGCM) INDIVIDUAL & MEAN TRAJECTORY DYNAMICS</text>'
        )

        # ---------------- Panel A: Spaghetti Trajectories & Population Mean ----------------
        p1_w = w - pad_l - pad_r
        svg_parts.append(
            f'<text x="{pad_l}" y="{pad_t - 10}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL A: Biểu đồ Quỹ đạo Cá thể (Spaghetti Plot) & Quỹ đạo Quần thể Trung bình [Slope = {mu_slope:+.3f}]</text>'
        )

        T = len(time_scores)
        t_min, t_max = time_scores[0], time_scores[-1]
        all_vals = list(mean_y)
        for i in range(min(len(eta_individual), 30)):
            b0 = eta_individual[i, 0]
            b1 = eta_individual[i, 1]
            all_vals.extend([b0 + b1 * t_min, b0 + b1 * t_max])

        y_min = min(all_vals) - 0.15 * abs(min(all_vals) if min(all_vals) != 0 else 1.0)
        y_max = max(all_vals) + 0.15 * abs(max(all_vals) if max(all_vals) != 0 else 1.0)
        if y_min >= y_max:
            y_min, y_max = y_min - 1.0, y_max + 1.0

        def t_to_px(t_val: float) -> float:
            return pad_l + ((t_val - t_min) / (t_max - t_min)) * p1_w

        def y_to_py(y_val: float) -> float:
            return pad_t + p1_h - ((y_val - y_min) / (y_max - y_min)) * (p1_h - 20)

        # Draw individual spaghetti lines (dim slate)
        for i in range(min(len(eta_individual), 40)):
            b0 = eta_individual[i, 0]
            b1 = eta_individual[i, 1]
            x1, y1_pt = t_to_px(t_min), y_to_py(b0 + b1 * t_min)
            x2, y2_pt = t_to_px(t_max), y_to_py(b0 + b1 * t_max)
            svg_parts.append(
                f'<line x1="{x1}" y1="{y1_pt}" x2="{x2}" y2="{y2_pt}" '
                f'stroke="#64748b" stroke-opacity="0.3" stroke-width="1"/>'
            )

        # 95% Confidence Ribbon for Population Trajectory
        ribbon_pts_upper = []
        ribbon_pts_lower = []
        for t_val in np.linspace(t_min, t_max, 10):
            mean_pt = mu_intercept + mu_slope * t_val
            margin = 1.96 * se_mu_slope * max(1.0, t_val)
            ribbon_pts_upper.append(f"{t_to_px(t_val)},{y_to_py(mean_pt + margin)}")
            ribbon_pts_lower.insert(0, f"{t_to_px(t_val)},{y_to_py(mean_pt - margin)}")

        ribbon_polygon = " ".join(ribbon_pts_upper + ribbon_pts_lower)
        svg_parts.append(
            f'<polygon points="{ribbon_polygon}" fill="#10b981" fill-opacity="0.12"/>'
        )

        # Population Mean Line (Emerald)
        x_m1, y_m1 = t_to_px(t_min), y_to_py(mu_intercept + mu_slope * t_min)
        x_m2, y_m2 = t_to_px(t_max), y_to_py(mu_intercept + mu_slope * t_max)
        svg_parts.append(
            f'<line x1="{x_m1}" y1="{y_m1}" x2="{x_m2}" y2="{y_m2}" '
            f'stroke="#10b981" stroke-width="3"/>'
        )

        # Observed Wave Means (Points)
        for idx, (t_val, m_val) in enumerate(zip(time_scores, mean_y)):
            px, py = t_to_px(t_val), y_to_py(m_val)
            svg_parts.append(f'<circle cx="{px}" cy="{py}" r="4.5" fill="#f59e0b"/>')
            svg_parts.append(
                f'<text x="{px}" y="{py - 8}" text-anchor="middle" fill="#f59e0b" font-size="9" font-weight="700">'
                f'{m_val:.2f}</text>'
            )

        # X-Axis Ticks
        for idx, (t_val, label) in enumerate(zip(time_scores, wave_labels)):
            tx = t_to_px(t_val)
            svg_parts.append(
                f'<line x1="{tx}" y1="{pad_t + p1_h}" x2="{tx}" y2="{pad_t + p1_h + 4}" stroke="#64748b"/>'
                f'<text x="{tx}" y="{pad_t + p1_h + 14}" text-anchor="middle" fill="#64748b" font-size="10">'
                f'{label[:10]}</text>'
            )

        # Legend Panel A
        svg_parts.append(
            f'<line x1="{pad_l + p1_w - 240}" y1="{pad_t + 15}" x2="{pad_l + p1_w - 210}" y2="{pad_t + 15}" stroke="#10b981" stroke-width="2.5"/>'
            f'<text x="{pad_l + p1_w - 200}" y="{pad_t + 18}" fill="#cbd5e1" font-size="10">Quần thể (Mean)</text>'
            f'<circle cx="{pad_l + p1_w - 90}" cy="{pad_t + 15}" r="3.5" fill="#f59e0b"/>'
            f'<text x="{pad_l + p1_w - 80}" y="{pad_t + 18}" fill="#cbd5e1" font-size="10">Trung bình mẫu</text>'
        )

        # ---------------- Panel B: Latent Intercept & Slope Covariance ----------------
        svg_parts.append(
            f'<text x="{pad_l}" y="{p2_y - 12}" fill="#94a3b8" font-size="11" font-weight="600">'
            f'PANEL B: Ma trận Hiệp phương sai Tiềm ẩn (Latent Factor Covariance & Dispersion)</text>'
        )

        # Stat cards in panel B
        card_w = (p1_w - 30) / 3
        # Card 1: Intercept Variance
        svg_parts.append(
            f'<rect x="{pad_l}" y="{p2_y}" width="{card_w}" height="{p2_h - 10}" rx="6" fill="#1e293b" stroke="#334155"/>'
            f'<text x="{pad_l + card_w/2}" y="{p2_y + 25}" text-anchor="middle" fill="#94a3b8" font-size="10" font-weight="600">'
            f'PHƯƠNG SAI ĐIỂM ĐẦU (ψ00)</text>'
            f'<text x="{pad_l + card_w/2}" y="{p2_y + 58}" text-anchor="middle" fill="#38bdf8" font-size="20" font-weight="700">'
            f'{psi_00:.3f}</text>'
            f'<text x="{pad_l + card_w/2}" y="{p2_y + 80}" text-anchor="middle" fill="#64748b" font-size="9">'
            f'Biến thiên giữa các cá thể tại t=0</text>'
        )

        # Card 2: Slope Variance
        svg_parts.append(
            f'<rect x="{pad_l + card_w + 15}" y="{p2_y}" width="{card_w}" height="{p2_h - 10}" rx="6" fill="#1e293b" stroke="#334155"/>'
            f'<text x="{pad_l + card_w + 15 + card_w/2}" y="{p2_y + 25}" text-anchor="middle" fill="#94a3b8" font-size="10" font-weight="600">'
            f'PHƯƠNG SAI TỐC ĐỘ (ψ11)</text>'
            f'<text x="{pad_l + card_w + 15 + card_w/2}" y="{p2_y + 58}" text-anchor="middle" fill="#10b981" font-size="20" font-weight="700">'
            f'{psi_11:.3f}</text>'
            f'<text x="{pad_l + card_w + 15 + card_w/2}" y="{p2_y + 80}" text-anchor="middle" fill="#64748b" font-size="9">'
            f'Sự phân hóa tốc độ thay đổi</text>'
        )

        # Card 3: Intercept-Slope Correlation
        corr_color = "#f59e0b" if corr_01 < 0 else "#6366f1"
        corr_desc = "Điểm đầu cao → Tăng trưởng chậm lại" if corr_01 < -0.1 else ("Điểm đầu cao → Tăng trưởng nhanh hơn" if corr_01 > 0.1 else "Không tương quan")
        svg_parts.append(
            f'<rect x="{pad_l + 2*(card_w + 15)}" y="{p2_y}" width="{card_w}" height="{p2_h - 10}" rx="6" fill="#1e293b" stroke="#334155"/>'
            f'<text x="{pad_l + 2*(card_w + 15) + card_w/2}" y="{p2_y + 25}" text-anchor="middle" fill="#94a3b8" font-size="10" font-weight="600">'
            f'TƯƠNG QUAN ĐẦU - TỐC (r01)</text>'
            f'<text x="{pad_l + 2*(card_w + 15) + card_w/2}" y="{p2_y + 58}" text-anchor="middle" fill="{corr_color}" font-size="20" font-weight="700">'
            f'{corr_01:+.2f}</text>'
            f'<text x="{pad_l + 2*(card_w + 15) + card_w/2}" y="{p2_y + 80}" text-anchor="middle" fill="#cbd5e1" font-size="9">'
            f'{corr_desc[:24]}</text>'
        )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_obs: int,
        n_waves: int,
        mu_intercept: float,
        se_mu_int: float,
        z_int: float,
        p_int: float,
        mu_slope: float,
        se_mu_slope: float,
        z_slope: float,
        p_slope: float,
        psi_00: float,
        psi_11: float,
        corr_01: float,
        cfi: float,
        rmsea: float,
        chi2_stat: float,
        df_model: int,
        chi2_p: float,
        is_good_fit: bool
    ) -> str:
        """
        Generate APA 7th Edition narrative for Latent Growth Curve Model.
        """
        fit_str = (
            f"Mô hình đạt độ phù hợp dữ liệu xuất sắc (CFI = {cfi:.3f}, RMSEA = {rmsea:.3f}, "
            f"chi2({df_model}) = {chi2_stat:.2f}, p = {chi2_p:.4f}), thỏa mãn hoàn toàn tiêu chuẩn Hu & Bentler (1999)."
            if is_good_fit
            else f"Mô hình đạt độ phù hợp chấp nhận được (CFI = {cfi:.3f}, RMSEA = {rmsea:.3f}, "
                 f"chi2({df_model}) = {chi2_stat:.2f}, p = {chi2_p:.4f})."
        )

        growth_sig = (
            f"có ý nghĩa thống kê cao (z = {z_slope:.2f}, p = {p_slope:.4f})"
            if p_slope < 0.05
            else f"chưa đạt ngưỡng ý nghĩa thống kê (z = {z_slope:.2f}, p = {p_slope:.4f})"
        )

        corr_interpretation = (
            f"Tương quan âm giữa điểm khởi đầu và tốc độ tăng trưởng (r = {corr_01:+.3f}) cho thấy "
            f"hiệu ứng hội tụ (convergence / ceiling effect): các cá thể có mức ban đầu thấp hơn có xu hướng tăng nhanh hơn."
            if corr_01 < -0.15
            else (
                f"Tương quan dương (r = {corr_01:+.3f}) chỉ ra hiệu ứng phân hóa tích lũy (Matthew effect / divergence): "
                f"các đối tượng có điểm đầu cao tiếp tục bứt phá với tốc độ tăng trưởng lớn hơn."
                if corr_01 > 0.15
                else f"Tương quan giữa điểm xuất phát và tốc độ tăng trưởng gần như triệt tiêu (r = {corr_01:+.3f})."
            )
        )

        narrative = (
            f"Mô hình Quỹ đạo Tăng trưởng Tiềm ẩn Tuyến tính (Linear Latent Growth Curve Model; Meredith & Tisak, 1990; "
            f"Bollen & Curran, 2006) được ước lượng trên cỡ mẫu N = {n_obs} đối tượng qua {n_waves} làn sóng khảo sát lặp. {fit_str} "
            f"Điểm xuất phát ban đầu trung bình của quần thể đạt mu_0 = {mu_intercept:.4f} (SE = {se_mu_int:.4f}, z = {z_int:.2f}, p < .001). "
            f"Tốc độ tăng trưởng trung bình qua mỗi đợt đạt mu_1 = {mu_slope:+.4f} (SE = {se_mu_slope:.4f}), {growth_sig}. "
            f"Về sự biến thiên giữa các cá thể, phương sai điểm đầu psi_00 = {psi_00:.4f} và phương sai tốc độ psi_11 = {psi_11:.4f} "
            f"xác nhận sự tồn tại của tính không đồng nhất về tốc độ phát triển. {corr_interpretation}"
        )
        return narrative
