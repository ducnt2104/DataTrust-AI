import math
import numpy as np
import scipy.stats as stats
from typing import Dict, Any, List, Optional, Tuple


class QuantileRegressionEngine:
    """
    Động cơ Hồi quy Phân vị & Hiệu ứng Phân phối Có điều kiện (Quantile Regression & Distributional Effects Engine)
    phục vụ phân tích sự không đồng nhất của tác động khảo sát trên toàn bộ phổ phân vị của biến kết quả
    (ví dụ: tác động can thiệp lên nhóm điểm thấp tau=0.10 so với trung vị tau=0.50 và nhóm xuất sắc tau=0.90).
    
    Tuân thủ phương pháp luận kinh tế lượng chuẩn mực quốc tế:
    - Koenker, R., & Bassett, G. (1978). Regression quantiles. Econometrica, 46(1), 33-50.
    - Koenker, R. (2005). Quantile Regression. Cambridge University Press.
    - Angrist, J. D., & Pischke, J. S. (2009). Mostly Harmless Econometrics (Ch. 7). Princeton University Press.
    - Portnoy, S., & Koenker, R. (1997). The Gaussian hare and the Laplacian tortoise: Computability of squared-error
      versus absolute-error estimators. Statistical Science, 12(4), 279-300.
    """

    @staticmethod
    def _pinball_loss(u: np.ndarray, tau: float) -> float:
        """Hàm mất mát Pinball Loss / Check Function rho_tau(u) = u * (tau - I(u < 0))"""
        return float(np.sum(np.where(u >= 0, tau * u, (tau - 1.0) * u)))

    @classmethod
    def _fit_single_quantile_irls(
        cls,
        X: np.ndarray,
        y: np.ndarray,
        tau: float,
        max_iter: int = 60,
        tol: float = 1e-6,
        delta: float = 1e-4
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Khớp mô hình hồi quy phân vị tau thông qua thuật toán Huber-Smoothed IRLS
        (Iteratively Reweighted Least Squares; Koenker 2005).
        """
        n, k = X.shape
        # Khởi tạo từ OLS
        try:
            beta = np.linalg.solve(X.T @ X + 1e-6 * np.eye(k), X.T @ y)
        except np.linalg.LinAlgError:
            beta = np.linalg.pinv(X.T @ X + 1e-6 * np.eye(k)) @ (X.T @ y)

        for _ in range(max_iter):
            r = y - X @ beta
            # Trọng số trơn theo hàm xấp xỉ đạo hàm của Pinball Loss
            # w_i = (tau - 0.5) / r + 0.5 / |r|_delta
            abs_r = np.maximum(np.abs(r), delta)
            w = np.abs(tau - (r < 0).astype(float)) / abs_r

            W = np.clip(w, 1e-5, 1e5)
            XW = X * W[:, None]

            try:
                beta_new = np.linalg.solve(X.T @ XW + 1e-6 * np.eye(k), X.T @ (W * y))
            except np.linalg.LinAlgError:
                beta_new = np.linalg.pinv(X.T @ XW + 1e-6 * np.eye(k)) @ (X.T @ (W * y))

            if np.max(np.abs(beta_new - beta)) < tol:
                beta = beta_new
                break
            beta = beta_new

        residuals = y - X @ beta
        loss = cls._pinball_loss(residuals, tau)
        return beta, residuals, loss

    @classmethod
    def _estimate_quantile_se_koenker(
        cls,
        X: np.ndarray,
        residuals: np.ndarray,
        tau: float,
        h_bandwidth: Optional[float] = None
    ) -> np.ndarray:
        """
        Ước lượng ma trận hiệp phương sai tiệm cận Sandwich của Koenker (2005):
        Cov(beta) = tau * (1 - tau) * (X^T f(0) X)^-1 (X^T X) (X^T f(0) X)^-1
        với f(0) ước lượng qua mật độ Kernel của thặng dư tại 0 theo dải thông Hall-Sheather hoặc Silverman.
        """
        n, k = X.shape
        std_r = float(np.std(residuals, ddof=1)) if n > 1 else 1.0
        iqr_r = float(np.percentile(residuals, 75.0) - np.percentile(residuals, 25.0))
        scale_est = min(std_r, iqr_r / 1.34) if iqr_r > 1e-6 else std_r

        # Dải thông Hall-Sheather (1988) cho phân vị
        z_tau = stats.norm.ppf(tau)
        phi_z = stats.norm.pdf(z_tau)
        if h_bandwidth is None:
            denom_band = (2.0 * z_tau ** 2 + 1.0) * phi_z ** 4
            if denom_band > 1e-6 and scale_est > 1e-6:
                h = n ** (-1.0 / 3.0) * stats.norm.ppf(0.975) ** (2.0 / 3.0) * ((1.5 * scale_est) / denom_band) ** (1.0 / 3.0)
            else:
                h = 1.06 * scale_est * (n ** (-0.2))
        else:
            h = h_bandwidth

        h = max(1e-4, h)

        # Mật độ f_i(0) xấp xỉ qua kernel chuẩn
        f0_weights = stats.norm.pdf(residuals / h) / h
        D = X.T @ (f0_weights[:, None] * X) / n + 1e-6 * np.eye(k)
        Omega = (X.T @ X) / n

        try:
            D_inv = np.linalg.inv(D)
        except np.linalg.LinAlgError:
            D_inv = np.linalg.pinv(D)

        cov_matrix = (tau * (1.0 - tau) / n) * (D_inv @ Omega @ D_inv)
        se = np.sqrt(np.maximum(1e-8, np.diag(cov_matrix)))
        return se

    @classmethod
    def fit_quantile_regression(
        cls,
        data_rows: List[Dict[str, Any]],
        predictor_key: str,
        outcome_key: str,
        covariate_keys: Optional[List[str]] = None,
        quantiles: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Khớp mô hình hồi quy phân vị đa ngưỡng tau và so sánh với mô hình OLS trung bình.
        """
        if labels is None:
            labels = {}
        if covariate_keys is None:
            covariate_keys = []
        if quantiles is None:
            quantiles = [0.10, 0.25, 0.50, 0.75, 0.90]

        # Sắp xếp và làm sạch danh sách phân vị
        clean_quantiles = sorted(list(set([round(float(q), 2) for q in quantiles if 0.01 <= float(q) <= 0.99])))
        if not clean_quantiles:
            clean_quantiles = [0.10, 0.25, 0.50, 0.75, 0.90]

        # 1. Trích xuất mảng dữ liệu sạch
        clean_rows = []
        for r in data_rows:
            xv = r.get(predictor_key)
            yv = r.get(outcome_key)
            if xv is None or yv is None or xv == "" or yv == "":
                continue
            try:
                xf = float(xv)
                yf = float(yv)
            except (ValueError, TypeError):
                continue

            cov_vals = []
            valid_covs = True
            for ck in covariate_keys:
                cv = r.get(ck)
                if cv is None or cv == "":
                    valid_covs = False
                    break
                try:
                    cov_vals.append(float(cv))
                except (ValueError, TypeError):
                    valid_covs = False
                    break

            if valid_covs:
                clean_rows.append((xf, yf, cov_vals))

        n_samples = len(clean_rows)
        if n_samples < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 16 quan sát hợp lệ để ước lượng hồi quy phân vị (hiện có {n_samples})."
            }

        x_main = np.array([r[0] for r in clean_rows], dtype=float)
        y_arr = np.array([r[1] for r in clean_rows], dtype=float)

        if len(covariate_keys) > 0:
            cov_mat = np.array([r[2] for r in clean_rows], dtype=float)
            X_design = np.column_stack([np.ones(n_samples), x_main, cov_mat])
        else:
            X_design = np.column_stack([np.ones(n_samples), x_main])

        n, k = X_design.shape

        # 2. Khớp mô hình OLS Trung bình làm mốc đối sánh chuẩn (Conditional Mean Baseline)
        try:
            beta_ols = np.linalg.solve(X_design.T @ X_design + 1e-6 * np.eye(k), X_design.T @ y_arr)
        except np.linalg.LinAlgError:
            beta_ols = np.linalg.pinv(X_design.T @ X_design + 1e-6 * np.eye(k)) @ (X_design.T @ y_arr)

        res_ols = y_arr - X_design @ beta_ols
        sigma2_ols = float(np.sum(res_ols ** 2) / (n - k)) if n > k else 1.0
        cov_ols = sigma2_ols * np.linalg.pinv(X_design.T @ X_design)
        se_ols = np.sqrt(np.maximum(1e-8, np.diag(cov_ols)))
        slope_ols = float(beta_ols[1])
        se_slope_ols = float(se_ols[1])
        t_ols = slope_ols / se_slope_ols if se_slope_ols > 0 else 0.0
        p_ols = float(2.0 * (1.0 - stats.t.cdf(abs(t_ols), max(1, n - k))))
        r2_ols = float(1.0 - np.sum(res_ols ** 2) / np.sum((y_arr - np.mean(y_arr)) ** 2)) if np.var(y_arr) > 1e-8 else 0.0

        # 3. Ước lượng Hồi quy Phân vị cho từng ngưỡng tau
        quantile_results = []
        slope_process = []  # Lưu (tau, slope, se, ci_low, ci_high) cho process plot

        # Tính tổng mất mát của mô hình chỉ có hằng số (Null model) cho pseudo R^1
        for tau in clean_quantiles:
            beta_q, res_q, loss_q = cls._fit_single_quantile_irls(X_design, y_arr, tau)
            se_q = cls._estimate_quantile_se_koenker(X_design, res_q, tau)

            # Pseudo R^1 (Koenker & Machado 1999): R^1(tau) = 1 - loss_full / loss_null
            q_median_y = float(np.percentile(y_arr, tau * 100))
            loss_null = cls._pinball_loss(y_arr - q_median_y, tau)
            pseudo_r1 = max(0.0, 1.0 - loss_q / loss_null) if loss_null > 1e-6 else 0.0

            slope_q = float(beta_q[1])
            se_slope_q = float(se_q[1])
            t_stat_q = slope_q / se_slope_q if se_slope_q > 0 else 0.0
            p_val_q = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat_q), max(1, n - k))))
            ci_low_q = float(slope_q - 1.96 * se_slope_q)
            ci_high_q = float(slope_q + 1.96 * se_slope_q)

            quantile_results.append({
                "tau": tau,
                "intercept": round(float(beta_q[0]), 4),
                "slope": round(slope_q, 4),
                "standard_error": round(se_slope_q, 4),
                "t_statistic": round(t_stat_q, 3),
                "p_value": round(p_val_q, 4),
                "ci_95_lower": round(ci_low_q, 4),
                "ci_95_upper": round(ci_high_q, 4),
                "is_significant": bool(p_val_q < 0.05),
                "pseudo_r1": round(pseudo_r1, 4),
                "pinball_loss": round(loss_q, 4)
            })

            slope_process.append({
                "tau": tau,
                "slope": slope_q,
                "se": se_slope_q,
                "ci_low": ci_low_q,
                "ci_high": ci_high_q
            })

        # 4. Kiểm định Sự Không Đồng Nhất Phân Vị (Interquantile Effect Heterogeneity Test)
        # So sánh chênh lệch giữa phân vị thấp (tau=0.10 hoặc tau min) và phân vị cao (tau=0.90 hoặc tau max)
        q_low_res = quantile_results[0]
        q_high_res = quantile_results[-1]
        interquantile_diff = q_high_res["slope"] - q_low_res["slope"]
        se_diff = math.sqrt(q_low_res["standard_error"] ** 2 + q_high_res["standard_error"] ** 2)
        z_hetero = interquantile_diff / se_diff if se_diff > 0 else 0.0
        p_hetero = float(2.0 * (1.0 - stats.norm.cdf(abs(z_hetero))))
        has_significant_heterogeneity = bool(p_hetero < 0.05)

        # 5. Tạo đồ thị Vector SVG Koenker Quantile Process Plot
        svg_process_plot = cls._generate_process_plot_svg(
            slope_process=slope_process,
            slope_ols=slope_ols,
            se_slope_ols=se_slope_ols,
            pred_label=labels.get(predictor_key, predictor_key),
            out_label=labels.get(outcome_key, outcome_key)
        )

        # 6. Soạn thảo Thuyết minh Học thuật Chuẩn APA 7th Edition
        apa_narrative = cls._generate_quantile_apa_narrative(
            sample_size=n_samples,
            predictor_label=labels.get(predictor_key, predictor_key),
            outcome_label=labels.get(outcome_key, outcome_key),
            slope_ols=slope_ols,
            se_slope_ols=se_slope_ols,
            p_ols=p_ols,
            quantile_results=quantile_results,
            interquantile_diff=interquantile_diff,
            z_hetero=z_hetero,
            p_hetero=p_hetero,
            has_significant_heterogeneity=has_significant_heterogeneity
        )

        return {
            "status": "SUCCESS",
            "sample_size": n_samples,
            "covariates_count": len(covariate_keys),
            "ols_baseline": {
                "slope": round(slope_ols, 4),
                "standard_error": round(se_slope_ols, 4),
                "t_statistic": round(t_ols, 3),
                "p_value": round(p_ols, 4),
                "is_significant": bool(p_ols < 0.05),
                "r_squared": round(r2_ols, 4)
            },
            "quantile_estimates": quantile_results,
            "heterogeneity_test": {
                "tau_comparison": f"tau={q_low_res['tau']} vs tau={q_high_res['tau']}",
                "slope_difference": round(interquantile_diff, 4),
                "standard_error": round(se_diff, 4),
                "z_statistic": round(z_hetero, 3),
                "p_value": round(p_hetero, 4),
                "has_significant_heterogeneity": has_significant_heterogeneity
            },
            "svg_process_plot": svg_process_plot,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_process_plot_svg(
        cls,
        slope_process: List[Dict[str, Any]],
        slope_ols: float,
        se_slope_ols: float,
        pred_label: str,
        out_label: str
    ) -> str:
        """Tạo đồ họa Vector SVG Koenker Process Plot biểu diễn hệ số góc theo từng phân vị tau"""
        svg_width = 820
        svg_height = 430
        margin_left = 80
        margin_right = 50
        margin_top = 40
        margin_bottom = 60

        plot_w = svg_width - margin_left - margin_right
        plot_h = svg_height - margin_top - margin_bottom

        # Trục X từ tau = 0.0 đến tau = 1.0
        # Trục Y bao phủ toàn bộ khoảng CI của các phân vị và OLS
        all_y_vals = []
        for it in slope_process:
            all_y_vals.extend([it["ci_low"], it["ci_high"], it["slope"]])
        all_y_vals.extend([slope_ols - 1.96 * se_slope_ols, slope_ols + 1.96 * se_slope_ols, slope_ols, 0.0])

        y_min = min(all_y_vals)
        y_max = max(all_y_vals)
        y_span = max(0.5, y_max - y_min)
        y_plot_min = y_min - 0.1 * y_span
        y_plot_max = y_max + 0.1 * y_span

        def to_x(tau_val: float) -> float:
            return margin_left + tau_val * plot_w

        def to_y(val: float) -> float:
            return margin_top + plot_h - ((val - y_plot_min) / (y_plot_max - y_plot_min)) * plot_h

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" style="font-family: Inter, system-ui, -apple-system, sans-serif;">',
            f'  <rect width="{svg_width}" height="{svg_height}" fill="#f8fafc" rx="12" stroke="#e2e8f0" stroke-width="1.5" />',
            '  <!-- Đường mức 0 (Zero baseline) -->'
        ]

        # Vạch Y = 0 nếu nằm trong phạm vi
        if y_plot_min <= 0.0 <= y_plot_max:
            y_zero = to_y(0.0)
            svg_lines.append(
                f'  <line x1="{margin_left}" y1="{y_zero:.1f}" x2="{margin_left + plot_w}" y2="{y_zero:.1f}" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="3 3" />'
            )

        # Lưới tọa độ ngang Y
        for y_tick in np.linspace(y_plot_min, y_plot_max, 5):
            y_pos = to_y(float(y_tick))
            svg_lines.append(
                f'  <line x1="{margin_left}" y1="{y_pos:.1f}" x2="{margin_left + plot_w}" y2="{y_pos:.1f}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3" />'
            )
            svg_lines.append(
                f'  <text x="{margin_left - 10}" y="{y_pos + 4:.1f}" font-size="10.5" fill="#64748b" text-anchor="end">{y_tick:.2f}</text>'
            )

        # Lưới tọa độ dọc X (tau từ 0.1 đến 0.9)
        for tau_tick in [0.1, 0.25, 0.5, 0.75, 0.9]:
            x_pos = to_x(tau_tick)
            svg_lines.append(
                f'  <line x1="{x_pos:.1f}" y1="{margin_top}" x2="{x_pos:.1f}" y2="{margin_top + plot_h}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3" />'
            )
            svg_lines.append(
                f'  <text x="{x_pos:.1f}" y="{margin_top + plot_h + 18}" font-size="10.5" fill="#64748b" text-anchor="middle">τ = {tau_tick:.2f}</text>'
            )

        # 1. Dải băng tin cậy 95% OLS (Vùng xám mờ nằm ngang)
        y_ols_low = to_y(slope_ols - 1.96 * se_slope_ols)
        y_ols_high = to_y(slope_ols + 1.96 * se_slope_ols)
        y_ols_mid = to_y(slope_ols)
        svg_lines.append(
            f'  <rect x="{margin_left}" y="{y_ols_high:.1f}" width="{plot_w}" height="{abs(y_ols_low - y_ols_high):.1f}" fill="#cbd5e1" fill-opacity="0.35" />'
        )
        svg_lines.append(
            f'  <line x1="{margin_left}" y1="{y_ols_mid:.1f}" x2="{margin_left + plot_w}" y2="{y_ols_mid:.1f}" stroke="#dc2626" stroke-width="1.8" stroke-dasharray="5 3" />'
        )

        # 2. Dải băng tin cậy 95% Quantile Regression (Polygon bóng xanh)
        band_pts = []
        for it in slope_process:
            band_pts.append(f"{to_x(it['tau']):.1f},{to_y(it['ci_high']):.1f}")
        for it in reversed(slope_process):
            band_pts.append(f"{to_x(it['tau']):.1f},{to_y(it['ci_low']):.1f}")
        svg_lines.append(
            f'  <polygon points="{" ".join(band_pts)}" fill="#a5b4fc" fill-opacity="0.45" stroke="none" />'
        )

        # 3. Đường quỹ đạo hệ số góc hồi quy phân vị (Quantile Process Line)
        path_d = []
        for idx, it in enumerate(slope_process):
            cmd = "M" if idx == 0 else "L"
            path_d.append(f"{cmd} {to_x(it['tau']):.1f} {to_y(it['slope']):.1f}")
        svg_lines.append(
            f'  <path d="{" ".join(path_d)}" fill="none" stroke="#4f46e5" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />'
        )

        # 4. Các điểm nút phân vị (Dots)
        for it in slope_process:
            px, py = to_x(it["tau"]), to_y(it["slope"])
            svg_lines.append(
                f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#4338ca" stroke="#312e81" stroke-width="1.2" />'
            )
            # Nhãn số
            svg_lines.append(
                f'  <text x="{px:.1f}" y="{py - 8:.1f}" font-size="9" font-weight="700" fill="#312e81" text-anchor="middle">{it["slope"]:.2f}</text>'
            )

        # Trục chính
        svg_lines.append(
            f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{margin_left + plot_w}" y2="{margin_top + plot_h}" stroke="#334155" stroke-width="1.5" />'
        )
        svg_lines.append(
            f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="#334155" stroke-width="1.5" />'
        )

        # Tiêu đề trục
        svg_lines.append(
            f'  <text x="{margin_left + plot_w / 2}" y="{svg_height - 15}" font-size="11.5" font-weight="600" fill="#334155" text-anchor="middle">Phân vị của biến kết quả (Quantile Level τ)</text>'
        )
        svg_lines.append(
            f'  <text x="22" y="{margin_top + plot_h / 2}" font-size="11.5" font-weight="600" fill="#334155" text-anchor="middle" transform="rotate(-90 22 {margin_top + plot_h / 2})">Hệ số tác động β(τ)</text>'
        )

        # Chú thích Legend
        leg_y = margin_top - 15
        svg_lines.append('  <g id="legend">')
        svg_lines.append(
            f'  <line x1="{margin_left + 10}" y1="{leg_y}" x2="{margin_left + 35}" y2="{leg_y}" stroke="#4f46e5" stroke-width="2.5" />'
        )
        svg_lines.append(
            f'  <text x="{margin_left + 42}" y="{leg_y + 3}" font-size="10.5" font-weight="600" fill="#3730a3">Quỹ đạo Hệ số Phân vị β(τ)</text>'
        )
        svg_lines.append(
            f'  <rect x="{margin_left + 220}" y="{leg_y - 6}" width="16" height="12" fill="#a5b4fc" fill-opacity="0.6" />'
        )
        svg_lines.append(
            f'  <text x="{margin_left + 242}" y="{leg_y + 3}" font-size="10.5" fill="#475569">95% CI Phân vị</text>'
        )
        svg_lines.append(
            f'  <line x1="{margin_left + 350}" y1="{leg_y}" x2="{margin_left + 375}" y2="{leg_y}" stroke="#dc2626" stroke-width="1.8" stroke-dasharray="4 2" />'
        )
        svg_lines.append(
            f'  <text x="{margin_left + 382}" y="{leg_y + 3}" font-size="10.5" font-weight="500" fill="#991b1b">Hồi quy Trung bình OLS (β_mean = {slope_ols:.2f})</text>'
        )
        svg_lines.append('  </g>')

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    @classmethod
    def _generate_quantile_apa_narrative(
        cls,
        sample_size: int,
        predictor_label: str,
        outcome_label: str,
        slope_ols: float,
        se_slope_ols: float,
        p_ols: float,
        quantile_results: List[Dict[str, Any]],
        interquantile_diff: float,
        z_hetero: float,
        p_hetero: float,
        has_significant_heterogeneity: bool
    ) -> str:
        """Tạo đoạn báo cáo học thuật chuẩn mực APA 7th Edition"""
        p_ols_str = "p < .001" if p_ols < 0.001 else f"p = {p_ols:.3f}"
        p_het_str = "p < .001" if p_hetero < 0.001 else f"p = {p_hetero:.3f}"

        # Tìm phân vị trung vị tau = 0.50
        med_res = next((it for it in quantile_results if abs(it["tau"] - 0.50) < 1e-4), quantile_results[len(quantile_results) // 2])
        low_res = quantile_results[0]
        high_res = quantile_results[-1]

        hetero_desc = (
            f"Kiểm định so sánh chênh lệch hệ số giữa phân vị cao (τ = {high_res['tau']}) và phân vị thấp (τ = {low_res['tau']}) "
            f"xác nhận sự không đồng nhất tác động có ý nghĩa thống kê rõ rệt, Δβ = {interquantile_diff:.3f}, "
            f"z = {z_hetero:.2f}, {p_het_str}. Điều này chứng minh rằng việc chỉ dựa vào ước lượng trung bình OLS sẽ che giấu đi "
            f"sự khác biệt quan trọng giữa các phân khúc đối tượng thụ hưởng."
            if has_significant_heterogeneity else
            f"Kiểm định chênh lệch hệ số phân vị không phát hiện sự không đồng nhất có ý nghĩa thống kê, "
            f"Δβ = {interquantile_diff:.3f}, z = {z_hetero:.2f}, {p_het_str}, cho thấy tác động của biến dự báo tương đối đồng đều trên toàn bộ phổ phân vị."
        )

        narrative = (
            f"Mô hình Hồi quy Phân vị (Quantile Regression; Koenker & Bassett, 1978; Koenker, 2005) được ước lượng "
            f"trên cỡ mẫu N = {sample_size} nhằm đánh giá tác động của '{predictor_label}' lên các ngưỡng phân vị khác nhau "
            f"của biến kết quả '{outcome_label}'.\n\n"
            f"Mô hình hồi quy trung bình OLS ghi nhận hệ số góc β_OLS = {slope_ols:.3f} (SE = {se_slope_ols:.3f}, {p_ols_str}). "
            f"Trong khi đó, phân tích phân vị bóc tách chi tiết: tại ngưỡng phân vị thấp τ = {low_res['tau']}, hệ số ghi nhận "
            f"β({low_res['tau']:.2f}) = {low_res['slope']:.3f} (SE = {low_res['standard_error']:.3f}, p = {low_res['p_value']:.3f}); "
            f"tại trung vị τ = {med_res['tau']}, hệ số đạt β({med_res['tau']:.2f}) = {med_res['slope']:.3f} "
            f"(SE = {med_res['standard_error']:.3f}, p = {med_res['p_value']:.3f}); và tại ngưỡng cao τ = {high_res['tau']}, "
            f"hệ số ghi nhận β({high_res['tau']:.2f}) = {high_res['slope']:.3f} (SE = {high_res['standard_error']:.3f}, p = {high_res['p_value']:.3f}).\n\n"
            f"{hetero_desc}"
        )

        return narrative
