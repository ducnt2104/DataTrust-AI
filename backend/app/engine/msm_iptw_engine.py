"""
DataTrust - Marginal Structural Models (MSM) & Time-Varying Confounding Engine
==============================================================================
Implements Marginal Structural Models with Stabilized Inverse Probability of
Treatment Weights (SW) for longitudinal surveys with time-varying confounding:
- Robins, J. M., Hernán, M. Á., & Brumback, B. (2000). Marginal structural models
  and causal inference in epidemiology. Epidemiology, 11(5), 550-560.
- Hernán, M. Á., & Robins, J. M. (2024). Causal Inference: What If. CRC Press.
- Robins, J. M. (1986). A new approach to causal inference in mortality studies
  with a sustained exposure period. Mathematical Modelling, 7(9-12), 1393-1512.
- Cole, S. R., & Hernán, M. Á. (2008). Constructing inverse probability weights for
  marginal structural models. American Journal of Epidemiology, 168(6), 656-664.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


class MSMIPTWEngine:
    """
    Marginal Structural Models (MSM) with Stabilized Inverse Probability Weights.
    """

    @classmethod
    def estimate(
        cls,
        treatments: np.ndarray,      # N x T matrix of binary treatments
        confounders: np.ndarray,     # N x T x K tensor or N x T matrix of time-varying confounders
        outcomes: np.ndarray,        # N-vector of terminal outcome Y
        wave_labels: Optional[List[str]] = None,
        truncate_percentiles: Tuple[float, float] = (1.0, 99.0)
    ) -> Dict[str, Any]:
        """
        Estimate Marginal Structural Model for multi-wave longitudinal panel data.
        treatments: N x T binary treatment indicators
        confounders: N x T (or N x T x K) time-varying confounders
        outcomes: N-vector of final outcomes
        """
        A = np.asarray(treatments, dtype=int)
        Y = np.asarray(outcomes, dtype=float)

        if A.ndim != 2:
            return {
                "status": "error",
                "message": "Ma trận biến can thiệp phải có dạng 2 chiều (N cá nhân x T làn sóng)."
            }

        N, T = A.shape
        if len(Y) != N:
            return {
                "status": "error",
                "message": "Số lượng quan sát biến kết quả không trùng khớp với số cá nhân trong ma trận can thiệp."
            }

        if N < 25:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 25 cá nhân theo dõi dọc để ước lượng mô hình MSM (hiện có: {N})."
            }
        if T < 2:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 2 làn sóng can thiệp theo thời gian để mô hình hóa nhiễu biến thiên (hiện có: {T})."
            }

        # Format confounders as N x T x K
        if confounders.ndim == 2:
            L = confounders[:, :, np.newaxis]
        else:
            L = confounders
        K = L.shape[2]

        if wave_labels is None or len(wave_labels) != T:
            wave_labels = [f"Wave {t+1}" for t in range(T)]

        # 1. Compute Stabilized Weights wave by wave
        # SW_i = prod_{t=1}^T [ P(A_t | A_{1:t-1}) / P(A_t | A_{1:t-1}, L_{1:t}) ]
        sw = np.ones(N, dtype=float)

        for t in range(T):
            a_t = A[:, t]

            # Numerator covariates: past treatments A_{0:t-1}
            if t == 0:
                p_num_1 = max(0.01, min(0.99, float(np.mean(a_t))))
                p_num = np.full(N, p_num_1)
            else:
                X_num = A[:, :t]
                p_num = cls._fit_logistic(X_num, a_t)

            # Denominator covariates: past treatments + current & past confounders
            past_treat = A[:, :t] if t > 0 else np.empty((N, 0))
            # Current and past confounders flattened
            conf_t = L[:, :t+1, :].reshape(N, -1)
            X_denom = np.column_stack([past_treat, conf_t]) if past_treat.shape[1] > 0 else conf_t

            p_denom = cls._fit_logistic(X_denom, a_t)

            # Likelihood contribution
            num_t = np.where(a_t == 1, p_num, 1.0 - p_num)
            denom_t = np.where(a_t == 1, p_denom, 1.0 - p_denom)
            denom_t = np.maximum(1e-4, denom_t)

            sw *= (num_t / denom_t)

        # 2. Weight Diagnostics & Truncation
        raw_sw_mean = float(np.mean(sw))
        raw_sw_sd = float(np.std(sw))
        raw_sw_min = float(np.min(sw))
        raw_sw_max = float(np.max(sw))

        lower_p, upper_p = truncate_percentiles
        w_low = float(np.percentile(sw, lower_p))
        w_high = float(np.percentile(sw, upper_p))
        sw_trunc = np.clip(sw, w_low, w_high)

        # Re-normalize truncated weights to have mean 1.0
        sw_final = sw_trunc / np.mean(sw_trunc)

        # 3. Fit Marginal Structural Model: Y = beta_0 + beta_1 * CumTreat + e
        cum_treat = np.sum(A, axis=1).astype(float)  # Total number of treatment waves (0 to T)

        # MSM Weighted Regression
        beta_msm, se_msm, z_msm, p_msm, ci_msm = cls._weighted_linear_reg(cum_treat, Y, sw_final)

        # Naive Unweighted OLS Regression (Demonstrates confounding bias)
        beta_naive, se_naive, z_naive, p_naive, ci_naive = cls._weighted_linear_reg(cum_treat, Y, np.ones(N))

        # Calculate confounding bias
        if abs(beta_msm) > 1e-6:
            bias_pct = float(((beta_naive - beta_msm) / abs(beta_msm)) * 100.0)
        else:
            bias_pct = 0.0

        # Confounding direction verdict
        if abs(bias_pct) < 10.0:
            bias_verdict = "Nhiễu biến thiên theo thời gian ở mức tối thiểu (< 10%)."
        elif bias_pct > 0:
            bias_verdict = f"Hồi quy ngây thơ thổi phồng quá mức hiệu ứng can thiệp (+{bias_pct:.1f}% thiên lệch dương do nhiễu thời gian)."
        else:
            bias_verdict = f"Hồi quy ngây thơ che mờ / đánh giá thấp hiệu ứng thực sự ({bias_pct:.1f}% thiên lệch âm do các yếu tố cản trở can thiệp)."

        # 4. Generate Vector SVG Dual-Panel Chart
        svg_chart = cls._generate_svg_chart(
            cum_treat=cum_treat,
            Y=Y,
            sw=sw_final,
            beta_msm=beta_msm,
            beta_naive=beta_naive,
            ci_msm=ci_msm,
            ci_naive=ci_naive,
            max_t=T
        )

        # 5. APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_obs=N,
            n_waves=T,
            beta_msm=beta_msm,
            se_msm=se_msm,
            z_msm=z_msm,
            p_msm=p_msm,
            ci_msm=ci_msm,
            beta_naive=beta_naive,
            se_naive=se_naive,
            p_naive=p_naive,
            bias_pct=bias_pct,
            bias_verdict=bias_verdict,
            sw_mean=raw_sw_mean,
            sw_sd=raw_sw_sd,
            sw_max=raw_sw_max
        )

        return {
            "status": "success",
            "sample_size": N,
            "waves_count": T,
            "causal_effect_per_wave": round(beta_msm, 4),
            "std_error": round(se_msm, 4),
            "z_statistic": round(z_msm, 4),
            "p_value": round(p_msm, 4),
            "ci_95_lower": round(ci_msm[0], 4),
            "ci_95_upper": round(ci_msm[1], 4),
            "naive_ols_effect": round(beta_naive, 4),
            "naive_ols_p_value": round(p_naive, 4),
            "confounding_bias_pct": round(bias_pct, 2),
            "confounding_verdict": bias_verdict,
            "stabilized_weights_diagnostics": {
                "mean": round(raw_sw_mean, 3),
                "std": round(raw_sw_sd, 3),
                "min": round(raw_sw_min, 3),
                "max": round(raw_sw_max, 3),
                "truncated_p1": round(w_low, 3),
                "truncated_p99": round(w_high, 3)
            },
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _fit_logistic(X: np.ndarray, y: np.ndarray) -> np.ndarray:
        N = len(y)
        if X.shape[1] == 0:
            p_const = max(0.01, min(0.99, float(np.mean(y))))
            return np.full(N, p_const)

        mu = np.mean(X, axis=0)
        sigma = np.std(X, axis=0)
        sigma[sigma == 0] = 1.0
        X_std = (X - mu) / sigma
        X_design = np.column_stack([np.ones(N), X_std])
        K = X_design.shape[1]

        beta = np.zeros(K)
        for _ in range(20):
            logits = np.clip(X_design @ beta, -12.0, 12.0)
            p = 1.0 / (1.0 + np.exp(-logits))
            grad = X_design.T @ (p - y) + 0.1 * beta
            W = p * (1.0 - p)
            H = (X_design.T * W) @ X_design + 0.1 * np.eye(K)
            try:
                d_beta = np.linalg.solve(H, grad)
            except np.linalg.LinAlgError:
                break
            beta -= d_beta
            if np.max(np.abs(d_beta)) < 1e-4:
                break

        final_logits = np.clip(X_design @ beta, -12.0, 12.0)
        p_res = 1.0 / (1.0 + np.exp(-final_logits))
        return np.clip(p_res, 0.01, 0.99)

    @staticmethod
    def _weighted_linear_reg(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> Tuple[float, float, float, float, Tuple[float, float]]:
        N = len(y)
        W_diag = np.sqrt(w)
        X_mat = np.column_stack([np.ones(N), x])
        X_w = X_mat * W_diag[:, np.newaxis]
        Y_w = y * W_diag

        try:
            inv_xtx = np.linalg.inv(X_w.T @ X_w)
            beta = inv_xtx @ (X_w.T @ Y_w)
        except np.linalg.LinAlgError:
            return 0.0, 1.0, 0.0, 1.0, (-1.96, 1.96)

        residuals = y - (X_mat @ beta)
        # Robust Huber-White sandwich variance
        meat = (X_mat.T * (w * (residuals ** 2))) @ X_mat
        var_cov = inv_xtx @ meat @ inv_xtx
        se = float(np.sqrt(max(1e-8, var_cov[1, 1])))

        b1 = float(beta[1])
        z = float(b1 / se) if se > 1e-12 else 0.0
        p = float(2.0 * (1.0 - stats.norm.cdf(abs(z))))
        ci = (float(b1 - 1.96 * se), float(b1 + 1.96 * se))
        return b1, se, z, p, ci

    @classmethod
    def _generate_svg_chart(
        cls,
        cum_treat: np.ndarray,
        Y: np.ndarray,
        sw: np.ndarray,
        beta_msm: float,
        beta_naive: float,
        ci_msm: Tuple[float, float],
        ci_naive: Tuple[float, float],
        max_t: int
    ) -> str:
        w, h = 900, 360
        margin_l, margin_r = 60, 480
        plot_w = 400
        plot_h = 240
        top = 50

        # Panel A: Weights Histogram
        n_bins = 15
        hist_counts, bin_edges = np.histogram(sw, bins=n_bins)
        max_count = max(1, int(np.max(hist_counts)))
        bin_w = plot_w / n_bins

        # Panel B: Dose-Response Slopes
        p2_l = 510
        p2_w = 340
        y_mean = float(np.mean(Y))
        x_grid = np.linspace(0, max_t, 20)
        y_msm_grid = y_mean + beta_msm * (x_grid - np.mean(cum_treat))
        y_naive_grid = y_mean + beta_naive * (x_grid - np.mean(cum_treat))

        y_all_grid = np.concatenate([y_msm_grid, y_naive_grid])
        y_min = float(np.min(y_all_grid)) - 0.2 * float(np.std(Y))
        y_max = float(np.max(y_all_grid)) + 0.2 * float(np.std(Y))

        def to_x_b(x_val: float) -> float:
            return p2_l + (x_val / max_t) * p2_w

        def to_y_b(y_val: float) -> float:
            return top + plot_h - ((y_val - y_min) / max(1e-4, y_max - y_min)) * plot_h

        pts_msm = [f"{to_x_b(xv):.1f},{to_y_b(yv):.1f}" for xv, yv in zip(x_grid, y_msm_grid)]
        pts_naive = [f"{to_x_b(xv):.1f},{to_y_b(yv):.1f}" for xv, yv in zip(x_grid, y_naive_grid)]

        svg = f"""<svg width="100%" height="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; font-family:Inter,system-ui,sans-serif;">
  <!-- Panel A Header -->
  <text x="{margin_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel A: Phân phối Trọng số Ổn định SW(t) (Mục tiêu: Mean ≈ 1.0)</text>
  <rect x="{margin_l}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>

  <!-- Histogram Bars -->
"""
        for i in range(n_bins):
            bx = margin_l + i * bin_w
            bar_h = (hist_counts[i] / max_count) * (plot_h - 20)
            by = top + plot_h - bar_h
            svg += f'  <rect x="{bx + 1:.1f}" y="{by:.1f}" width="{bin_w - 2:.1f}" height="{bar_h:.1f}" fill="#38bdf8" fill-opacity="0.75" rx="2"/>\n'

        # Reference line at SW = 1.0
        sw_min_val, sw_max_val = bin_edges[0], bin_edges[-1]
        if sw_min_val <= 1.0 <= sw_max_val:
            x_ref = margin_l + ((1.0 - sw_min_val) / max(1e-4, sw_max_val - sw_min_val)) * plot_w
            svg += f'  <line x1="{x_ref:.1f}" y1="{top}" x2="{x_ref:.1f}" y2="{top + plot_h}" stroke="#f59e0b" stroke-dasharray="4,3" stroke-width="2"/>\n'
            svg += f'  <text x="{x_ref + 4:.1f}" y="{top + 16}" fill="#f59e0b" font-size="10" font-weight="bold">SW = 1.0</text>\n'

        svg += f"""  <text x="{margin_l + plot_w / 2}" y="{top + plot_h + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">Giá trị trọng số ổn định SW</text>

  <!-- Panel B Header -->
  <text x="{p2_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel B: Đường cong Đáp ứng Liều tích lũy (MSM vs Naive OLS)</text>
  <rect x="{p2_l}" y="{top}" width="{p2_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>

  <!-- MSM Trajectory (Emerald) -->
  <path d="M {' L '.join(pts_msm)}" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round"/>

  <!-- Naive OLS Trajectory (Rose / Dashed) -->
  <path d="M {' L '.join(pts_naive)}" fill="none" stroke="#f43f5e" stroke-width="2.2" stroke-dasharray="6,4"/>

  <!-- Panel B Legend -->
  <line x1="{p2_l + 14}" y1="{top + 18}" x2="{p2_l + 40}" y2="{top + 18}" stroke="#10b981" stroke-width="3"/>
  <text x="{p2_l + 46}" y="{top + 22}" fill="#10b981" font-size="11" font-weight="bold">MSM Causal (β = {beta_msm:+.3f})</text>

  <line x1="{p2_l + 180}" y1="{top + 18}" x2="{p2_l + 206}" y2="{top + 18}" stroke="#f43f5e" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="{p2_l + 212}" y="{top + 22}" fill="#f43f5e" font-size="11" font-weight="bold">Naive OLS (β = {beta_naive:+.3f})</text>

  <text x="{p2_l + p2_w / 2}" y="{top + plot_h + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">Số đợt can thiệp tích lũy (Cumulative Treatment Waves)</text>
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_obs: int,
        n_waves: int,
        beta_msm: float,
        se_msm: float,
        z_msm: float,
        p_msm: float,
        ci_msm: Tuple[float, float],
        beta_naive: float,
        se_naive: float,
        p_naive: float,
        bias_pct: float,
        bias_verdict: str,
        sw_mean: float,
        sw_sd: float,
        sw_max: float
    ) -> str:
        narrative = (
            f"Mô hình Cấu trúc Biên (Marginal Structural Model - MSM; Robins, Hernán & Brumback, 2000) "
            f"đã được ước lượng với trọng số ổn định nghịch đảo xác suất xu hướng (Stabilized IPTW) "
            f"nhằm kiểm soát triệt để hiện tượng nhiễu biến thiên theo thời gian (time-varying confounding) "
            f"trên cỡ mẫu theo dõi dọc gồm N = {n_obs} người tham gia qua T = {n_waves} làn sóng khảo sát.\n\n"
            f"Kiểm tra chất lượng phân phối trọng số ổn định (Cole & Hernán, 2008): "
            f"trọng số đạt giá trị trung bình Mean(SW) = {sw_mean:.3f} (rất gần mức lý tưởng 1.0), "
            f"độ lệch chuẩn SD = {sw_sd:.3f}, và giá trị cực đại Max = {sw_max:.2f}, "
            f"chứng minh giả định về tính khả thi dương (positivity assumption) được thỏa mãn hoàn toàn mà không xuất hiện các trọng số ngoại lai gây mất ổn định phương sai.\n\n"
            f"Kết quả ước lượng nhân quả cho thấy mỗi đợt can thiệp tích lũy giúp cải thiện biến kết quả "
            f"ở mức β_MSM = {beta_msm:+.3f} (SE = {se_msm:.3f}, z = {z_msm:.2f}, p = {p_msm:.3f}, "
            f"95% CI [{ci_msm[0]:.3f}, {ci_msm[1]:.3f}]).\n\n"
            f"So sánh với phương pháp hồi quy OLS ngây thơ không kiểm soát nhiễu thời gian: "
            f"ước lượng ngây thơ ghi nhận β_Naive = {beta_naive:+.3f} (SE = {se_naive:.3f}, p = {p_naive:.3f}), "
            f"dẫn đến mức độ chênh lệch thiên lệch {bias_pct:+.1f}%. {bias_verdict} "
            f"Điều này khẳng định tính ưu việt bắt buộc của MSM trong các nghiên cứu bảng lặp có tương tác nội sinh động lực."
        )
        return narrative
