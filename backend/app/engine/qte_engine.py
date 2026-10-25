"""
DataTrust - Quantile Treatment Effects (QTE) & Distributional Treatment Effects Engine
======================================================================================
Implements Semiparametric Quantile Treatment Effects under Unconfoundedness:
- Firpo, S. (2007). Efficient semiparametric estimation of quantile treatment effects.
  Econometrica, 75(1), 259-276.
- Koenker, R., & Bassett, G. (1978). Regression quantiles. Econometrica, 46(1), 33-50.
- Abadie, A., Angrist, J., & Imbens, G. (2002). Instrumental variables estimates of the
  effect of subsidized training on the quantiles of trainee earnings. Econometrica, 70(1), 91-117.
- Chernozhukov, V., Fernandez-Val, I., & Melly, B. (2013). Inference on counterfactual
  distributions. Econometrica, 81(6), 2205-2268.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


class QTEEngine:
    """
    Quantile Treatment Effects & Counterfactual Distribution Estimator.
    """

    DEFAULT_QUANTILES = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]

    @classmethod
    def estimate(
        cls,
        outcomes: np.ndarray,
        treatment: np.ndarray,
        covariates: Optional[np.ndarray] = None,
        quantiles: Optional[List[float]] = None,
        alpha_trim: float = 0.05
    ) -> Dict[str, Any]:
        """
        Estimate Quantile Treatment Effects across specified quantiles.
        outcomes: N-vector of continuous outcome values Y
        treatment: N-vector of binary treatment indicator D in {0, 1}
        covariates: Optional N x K matrix of pre-treatment confounders X
        quantiles: List of quantiles to evaluate in (0, 1)
        alpha_trim: Trimming threshold for propensity score overlap [alpha, 1 - alpha]
        """
        Y = np.asarray(outcomes, dtype=float)
        D = np.asarray(treatment, dtype=int)

        if len(Y) != len(D):
            return {
                "status": "error",
                "message": "Độ dài mảng biến kết quả và biến can thiệp không trùng khớp."
            }

        N = len(Y)
        n_treat = int(np.sum(D == 1))
        n_ctrl = int(np.sum(D == 0))

        if n_treat < 10 or n_ctrl < 10:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 10 quan sát cho mỗi nhóm can thiệp và đối chứng (hiện có: {n_treat} can thiệp, {n_ctrl} đối chứng)."
            }

        if quantiles is None:
            quantiles = cls.DEFAULT_QUANTILES
        else:
            quantiles = sorted([float(q) for q in quantiles if 0.0 < q < 1.0])

        if len(quantiles) == 0:
            quantiles = cls.DEFAULT_QUANTILES

        # 1. Propensity Score Estimation if Covariates Present
        if covariates is not None and covariates.shape[1] > 0:
            X = np.asarray(covariates, dtype=float)
            propensity = cls._estimate_propensity(X, D)

            # Boundary trimming
            keep_idx = np.where((propensity >= alpha_trim) & (propensity <= 1.0 - alpha_trim))[0]
            if len(keep_idx) < 20:
                keep_idx = np.arange(N)  # Fallback to untrimmed if too few
            
            Y_eval = Y[keep_idx]
            D_eval = D[keep_idx]
            p_eval = propensity[keep_idx]
        else:
            Y_eval = Y
            D_eval = D
            p_eval = np.full(N, n_treat / N)
            keep_idx = np.arange(N)

        N_eval = len(Y_eval)
        N1 = int(np.sum(D_eval == 1))
        N0 = int(np.sum(D_eval == 0))

        # 2. Average Treatment Effect (ATE) Benchmark
        w1 = D_eval / np.maximum(1e-4, p_eval)
        w0 = (1.0 - D_eval) / np.maximum(1e-4, 1.0 - p_eval)
        ate = float(np.sum(w1 * Y_eval) / max(1e-6, np.sum(w1)) - np.sum(w0 * Y_eval) / max(1e-6, np.sum(w0)))

        # 3. Weighted Quantile Estimation for Treated Y(1) and Control Y(0)
        y1_vals = Y_eval[D_eval == 1]
        w1_vals = w1[D_eval == 1]
        w1_norm = w1_vals / np.sum(w1_vals)

        y0_vals = Y_eval[D_eval == 0]
        w0_vals = w0[D_eval == 0]
        w0_norm = w0_vals / np.sum(w0_vals)

        qte_results: List[Dict[str, Any]] = []
        q1_list: List[float] = []
        q0_list: List[float] = []
        effects: List[float] = []

        # Silverman's bandwidth rule of thumb for density estimation
        h1 = 1.06 * max(1e-4, np.std(y1_vals)) * (N1 ** (-0.2))
        h0 = 1.06 * max(1e-4, np.std(y0_vals)) * (N0 ** (-0.2))

        for q in quantiles:
            q1 = cls._weighted_quantile(y1_vals, w1_norm, q)
            q0 = cls._weighted_quantile(y0_vals, w0_norm, q)
            eff = float(q1 - q0)

            # Asymptotic density via Gaussian kernel
            f1 = max(1e-4, float(np.mean(stats.norm.pdf((y1_vals - q1) / h1) / h1)))
            f0 = max(1e-4, float(np.mean(stats.norm.pdf((y0_vals - q0) / h0) / h0)))

            # Asymptotic Variance (Firpo 2007)
            var_q1 = (q * (1.0 - q)) / (N1 * (f1 ** 2))
            var_q0 = (q * (1.0 - q)) / (N0 * (f0 ** 2))
            se = float(np.sqrt(max(1e-8, var_q1 + var_q0)))

            z_stat = float(eff / se) if se > 1e-12 else 0.0
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
            ci_lower = float(eff - 1.96 * se)
            ci_upper = float(eff + 1.96 * se)

            q1_list.append(q1)
            q0_list.append(q0)
            effects.append(eff)

            qte_results.append({
                "quantile": round(q, 2),
                "qte": round(eff, 4),
                "q_treated": round(q1, 4),
                "q_control": round(q0, 4),
                "std_error": round(se, 4),
                "z_statistic": round(z_stat, 4),
                "p_value": round(p_val, 4),
                "ci_95_lower": round(ci_lower, 4),
                "ci_95_upper": round(ci_upper, 4),
                "is_significant": bool(p_val < 0.05)
            })

        # 4. Distributional Inequality & Shape Diagnostics
        # Median effect QTE(0.50)
        median_qte = cls._interpolate_quantile_effect(quantiles, effects, 0.50)
        q75_eff = cls._interpolate_quantile_effect(quantiles, effects, 0.75)
        q25_eff = cls._interpolate_quantile_effect(quantiles, effects, 0.25)
        delta_iqr = float(q75_eff - q25_eff)

        q90_eff = cls._interpolate_quantile_effect(quantiles, effects, 0.90)
        q10_eff = cls._interpolate_quantile_effect(quantiles, effects, 0.10)
        delta_90_10 = float(q90_eff - q10_eff)

        # Constant Treatment Effect Test (Max Absolute Deviation from ATE)
        max_dev_ate = float(np.max(np.abs(np.array(effects) - ate)))
        is_heterogeneous = bool(max_dev_ate > 0.3 * max(1e-4, np.std(Y_eval)))

        if delta_iqr < -0.15 * max(1e-4, np.std(Y_eval)):
            inequality_verdict = "Thu hẹp bất bình đẳng (Compensatory / Compressive Effect - Người ở phân vị thấp được hưởng lợi nhiều hơn)."
        elif delta_iqr > 0.15 * max(1e-4, np.std(Y_eval)):
            inequality_verdict = "Gia tăng bất bình đẳng (Matthew Effect / Dispersive Effect - Người ở phân vị cao được hưởng lợi vượt trội)."
        else:
            inequality_verdict = "Tác động đồng đều (Uniform / Parallel Shift - Không làm biến dạng cấu trúc phân tán của tổng thể)."

        # 5. Dual-Panel Vector SVG Chart
        svg_chart = cls._generate_svg_chart(
            quantiles=quantiles,
            effects=effects,
            qte_results=qte_results,
            ate=ate,
            y1_vals=y1_vals,
            y0_vals=y0_vals
        )

        # 6. APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_obs=N_eval,
            n_treat=N1,
            n_ctrl=N0,
            ate=ate,
            median_qte=median_qte,
            delta_iqr=delta_iqr,
            delta_90_10=delta_90_10,
            qte_results=qte_results,
            inequality_verdict=inequality_verdict,
            is_heterogeneous=is_heterogeneous
        )

        return {
            "status": "success",
            "sample_size": N_eval,
            "treated_count": N1,
            "control_count": N0,
            "average_treatment_effect": round(ate, 4),
            "median_treatment_effect": round(median_qte, 4),
            "delta_iqr_effect": round(delta_iqr, 4),
            "delta_90_10_effect": round(delta_90_10, 4),
            "has_heterogeneous_distributional_effects": is_heterogeneous,
            "inequality_impact": inequality_verdict,
            "quantile_effects": qte_results,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _estimate_propensity(X: np.ndarray, D: np.ndarray) -> np.ndarray:
        N, K = X.shape
        # Standardize X
        mu = np.mean(X, axis=0)
        sigma = np.std(X, axis=0)
        sigma[sigma == 0] = 1.0
        X_std = (X - mu) / sigma
        X_design = np.column_stack([np.ones(N), X_std])

        # Regularized Newton-Raphson for Logistic Regression
        beta = np.zeros(K + 1)
        for _ in range(25):
            logits = np.clip(X_design @ beta, -15.0, 15.0)
            p = 1.0 / (1.0 + np.exp(-logits))
            grad = X_design.T @ (p - D) + 0.1 * beta
            W = p * (1.0 - p)
            H = (X_design.T * W) @ X_design + 0.1 * np.eye(K + 1)
            try:
                d_beta = np.linalg.solve(H, grad)
            except np.linalg.LinAlgError:
                break
            beta -= d_beta
            if np.max(np.abs(d_beta)) < 1e-5:
                break

        final_logits = np.clip(X_design @ beta, -15.0, 15.0)
        return 1.0 / (1.0 + np.exp(-final_logits))

    @staticmethod
    def _weighted_quantile(vals: np.ndarray, weights: np.ndarray, q: float) -> float:
        sorter = np.argsort(vals)
        s_vals = vals[sorter]
        s_weights = weights[sorter]
        cum_weights = np.cumsum(s_weights)
        idx = np.searchsorted(cum_weights, q)
        if idx >= len(s_vals):
            return float(s_vals[-1])
        return float(s_vals[idx])

    @staticmethod
    def _interpolate_quantile_effect(quantiles: List[float], effects: List[float], target_q: float) -> float:
        return float(np.interp(target_q, quantiles, effects))

    @classmethod
    def _generate_svg_chart(
        cls,
        quantiles: List[float],
        effects: List[float],
        qte_results: List[Dict[str, Any]],
        ate: float,
        y1_vals: np.ndarray,
        y0_vals: np.ndarray
    ) -> str:
        w, h = 900, 360
        margin_l, margin_r = 60, 480
        plot_w = 400
        plot_h = 240
        top = 50

        # Panel A Bounds
        all_lowers = [r["ci_95_lower"] for r in qte_results]
        all_uppers = [r["ci_95_upper"] for r in qte_results]
        min_eff = min(min(all_lowers), ate, 0.0)
        max_eff = max(max(all_uppers), ate, 0.0)
        eff_pad = 0.15 * (max_eff - min_eff + 1e-4)
        y_min = min_eff - eff_pad
        y_max = max_eff + eff_pad

        def to_x_a(q: float) -> float:
            return margin_l + ((q - 0.10) / 0.80) * plot_w

        def to_y_a(eff: float) -> float:
            return top + plot_h - ((eff - y_min) / max(1e-4, y_max - y_min)) * plot_h

        # Zero reference line
        y_zero = to_y_a(0.0)
        y_ate = to_y_a(ate)

        # Construct Confidence Ribbon path
        upper_pts = [f"{to_x_a(r['quantile']):.1f},{to_y_a(r['ci_95_upper']):.1f}" for r in qte_results]
        lower_pts = [f"{to_x_a(r['quantile']):.1f},{to_y_a(r['ci_95_lower']):.1f}" for r in reversed(qte_results)]
        ribbon_path = f"M {upper_pts[0]} L " + " L ".join(upper_pts[1:]) + " L " + " L ".join(lower_pts) + " Z"

        # Construct QTE trajectory line
        qte_pts = [f"{to_x_a(r['quantile']):.1f},{to_y_a(r['qte']):.1f}" for r in qte_results]
        qte_path = "M " + " L ".join(qte_pts)

        # Panel B: Cumulative Distribution Functions F(y)
        p2_l = 510
        p2_w = 340
        y_all = np.concatenate([y1_vals, y0_vals])
        y_grid_min = float(np.min(y_all))
        y_grid_max = float(np.max(y_all))
        y_grid = np.linspace(y_grid_min, y_grid_max, 50)

        cdf1 = [float(np.mean(y1_vals <= val)) for val in y_grid]
        cdf0 = [float(np.mean(y0_vals <= val)) for val in y_grid]

        def to_x_b(val: float) -> float:
            return p2_l + ((val - y_grid_min) / max(1e-4, y_grid_max - y_grid_min)) * p2_w

        def to_y_b(prob: float) -> float:
            return top + plot_h - prob * plot_h

        pts_cdf1 = [f"{to_x_b(val):.1f},{to_y_b(p):.1f}" for val, p in zip(y_grid, cdf1)]
        pts_cdf0 = [f"{to_x_b(val):.1f},{to_y_b(p):.1f}" for val, p in zip(y_grid, cdf0)]

        svg = f"""<svg width="100%" height="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; font-family:Inter,system-ui,sans-serif;">
  <defs>
    <linearGradient id="qteRibbon" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.08"/>
    </linearGradient>
  </defs>

  <!-- Panel A: QTE Curve & Confidence Band -->
  <text x="{margin_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel A: Đường cong Hiệu ứng Lượng vị (QTE) qua các Phân vị (95% CI)</text>
  
  <!-- Grid Lines & Axes Panel A -->
  <rect x="{margin_l}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>
  <line x1="{margin_l}" y1="{y_zero:.1f}" x2="{margin_l + plot_w}" y2="{y_zero:.1f}" stroke="#64748b" stroke-dasharray="4,4" stroke-width="1.2"/>
  <text x="{margin_l + plot_w - 5}" y="{y_zero - 4:.1f}" fill="#94a3b8" font-size="10" text-anchor="end">Hiệu ứng 0</text>

  <!-- ATE Constant Line -->
  <line x1="{margin_l}" y1="{y_ate:.1f}" x2="{margin_l + plot_w}" y2="{y_ate:.1f}" stroke="#f59e0b" stroke-dasharray="6,3" stroke-width="1.8"/>
  <text x="{margin_l + 8}" y="{y_ate - 4:.1f}" fill="#f59e0b" font-size="10" font-weight="bold">ATE = {ate:+.2f}</text>

  <!-- 95% Confidence Ribbon -->
  <path d="{ribbon_path}" fill="url(#qteRibbon)"/>

  <!-- QTE Main Trajectory Line -->
  <path d="{qte_path}" fill="none" stroke="#0ea5e9" stroke-width="2.6" stroke-linecap="round"/>

  <!-- Data Points -->
"""
        for r in qte_results:
            cx = to_x_a(r["quantile"])
            cy = to_y_a(r["qte"])
            dot_color = "#38bdf8" if r["is_significant"] else "#94a3b8"
            svg += f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{dot_color}" stroke="#0f172a" stroke-width="1.5"/>\n'
            svg += f'  <text x="{cx:.1f}" y="{top + plot_h + 16}" fill="#94a3b8" font-size="10" text-anchor="middle">q={r["quantile"]:.1f}</text>\n'

        svg += f"""
  <!-- Panel B: Counterfactual CDF Curves -->
  <text x="{p2_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel B: Hàm Phân phối Tích lũy (CDF) Nhóm Y(1) vs Y(0)</text>
  <rect x="{p2_l}" y="{top}" width="{p2_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>
  
  <path d="M {' L '.join(pts_cdf1)}" fill="none" stroke="#10b981" stroke-width="2.4"/>
  <path d="M {' L '.join(pts_cdf0)}" fill="none" stroke="#f43f5e" stroke-width="2" stroke-dasharray="4,3"/>

  <!-- CDF Axis Labels -->
  <text x="{p2_l + 10}" y="{top + 18}" fill="#10b981" font-size="11" font-weight="bold">— Can thiệp Y(1)</text>
  <text x="{p2_l + 130}" y="{top + 18}" fill="#f43f5e" font-size="11" font-weight="bold">--- Đối chứng Y(0)</text>
  <text x="{p2_l + p2_w / 2}" y="{top + plot_h + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">Thang đo biến kết quả (Outcome Y)</text>
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_obs: int,
        n_treat: int,
        n_ctrl: int,
        ate: float,
        median_qte: float,
        delta_iqr: float,
        delta_90_10: float,
        qte_results: List[Dict[str, Any]],
        inequality_verdict: str,
        is_heterogeneous: bool
    ) -> str:
        sig_count = sum(1 for r in qte_results if r["is_significant"])
        q10_res = next((r for r in qte_results if abs(r["quantile"] - 0.10) < 0.05), qte_results[0])
        q50_res = next((r for r in qte_results if abs(r["quantile"] - 0.50) < 0.05), qte_results[len(qte_results)//2])
        q90_res = next((r for r in qte_results if abs(r["quantile"] - 0.90) < 0.05), qte_results[-1])

        narrative = (
            f"Phân tích Hiệu ứng Can thiệp Lượng vị Bán tham số (Semiparametric Quantile Treatment Effects - QTE; Firpo, 2007) "
            f"đã được thực hiện trên mẫu khảo sát gồm N = {n_obs} quan sát (n_treat = {n_treat}, n_ctrl = {n_ctrl}) "
            f"nhằm bóc tách sự biến thiên không đồng nhất của chính sách/can thiệp trên toàn bộ phân phối biến kết quả.\n\n"
            f"Hiệu ứng can thiệp trung bình chung (Average Treatment Effect - ATE) đạt mức ATE = {ate:+.3f}. "
            f"Tuy nhiên, phân tích lượng vị chỉ ra rằng tác động của can thiệp {'có sự phân hóa sâu sắc' if is_heterogeneous else 'tương đối đồng đều'} "
            f"giữa các tầng phân vị: tại phân vị thấp (q = 0.10), hiệu ứng đạt QTE(0.10) = {q10_res['qte']:+.3f} "
            f"(SE = {q10_res['std_error']:.3f}, z = {q10_res['z_statistic']:.2f}, p = {q10_res['p_value']:.3f}); "
            f"tại trung vị (q = 0.50), hiệu ứng lượng vị là QTE(0.50) = {q50_res['qte']:+.3f} "
            f"(SE = {q50_res['std_error']:.3f}, z = {q50_res['z_statistic']:.2f}, p = {q50_res['p_value']:.3f}); "
            f"và tại nhóm phân vị cao (q = 0.90), hiệu ứng ghi nhận QTE(0.90) = {q90_res['qte']:+.3f} "
            f"(SE = {q90_res['std_error']:.3f}, z = {q90_res['z_statistic']:.2f}, p = {q90_res['p_value']:.3f}).\n\n"
            f"Đánh giá tác động đến mức độ bất bình đẳng và hình dạng phân phối (Koenker & Bassett, 1978; Chernozhukov et al., 2013): "
            f"chênh lệch khoảng liên tứ phân vị đạt ΔIQR = QTE(0.75) - QTE(0.25) = {delta_iqr:+.3f}, "
            f"và chênh lệch khoảng cách đuôi phân phối đạt Δ(90-10) = {delta_90_10:+.3f}. "
            f"Kết luận phân phối: {inequality_verdict} Tổng cộng {sig_count}/{len(qte_results)} mốc lượng vị đạt mức ý nghĩa thống kê p < .05."
        )
        return narrative
