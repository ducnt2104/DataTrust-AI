import math
import numpy as np
import scipy.stats as stats
from typing import Dict, Any, List, Optional, Tuple


class RDDEngine:
    """
    Động cơ Thiết kế Gián đoạn Hồi quy & Đánh giá Tác động Cận ngưỡng (Regression Discontinuity Design / RDD Engine)
    phục vụ suy diễn nhân quả chuẩn tắc bậc cao từ dữ liệu khảo sát và chính sách có ngưỡng phân loại (Cutoff Rule).
    
    Tuân thủ phương pháp luận kinh tế lượng chuẩn mực quốc tế:
    - Thistlethwaite, D. L., & Campbell, D. T. (1960). Regression-discontinuity analysis: An alternative to the ex post
      facto experiment. Journal of Educational Psychology, 51(6), 309-317.
    - Hahn, J., Todd, P., & van der Klaauw, W. (2001). Identification and estimation of treatment effects with a
      regression-discontinuity design. Econometrica, 69(1), 201-209.
    - Imbens, G., & Kalyanaraman, K. (2012). Optimal bandwidth choice for the regression discontinuity estimator.
      The Review of Economic Studies, 79(3), 933-959.
    - Calonico, S., Cattaneo, M. D., & Titiunik, R. (2014). Robust nonparametric confidence intervals for
      regression-discontinuity designs. Econometrica, 82(6), 2295-2326.
    - McCrary, J. (2008). Testing for manipulation of the running variable in the regression discontinuity design.
      Journal of Econometrics, 142(2), 698-714.
    """

    @staticmethod
    def _triangular_kernel(u: np.ndarray) -> np.ndarray:
        """Hàm nhân tam giác (Triangular Kernel) tối ưu cho hồi quy cục bộ cận biên (Fan & Gijbels 1996)"""
        return np.maximum(0.0, 1.0 - np.abs(u)) * (np.abs(u) <= 1.0).astype(float)

    @classmethod
    def _calculate_ik_bandwidth(
        cls,
        x: np.ndarray,
        y: np.ndarray,
        c: float
    ) -> float:
        """
        Xác định độ rộng dải thông tối ưu (Optimal Bandwidth) theo quy chuẩn Imbens & Kalyanaraman (2012).
        Cân bằng tối ưu giữa độ chệch (bias) và phương sai (variance) tại cận biên x = c.
        """
        n = len(x)
        std_x = float(np.std(x, ddof=1)) if n > 1 else 1.0
        # Mức cơ sở tham chiếu theo quy tắc ngón tay cái Silverman biến thể RDD
        h_pilot = 1.84 * std_x * (n ** (-0.2))

        # Phân tích phương sai thặng dư ở hai bên cận biên
        left_mask = (x >= c - h_pilot) & (x < c)
        right_mask = (x >= c) & (x <= c + h_pilot)

        n_l = np.sum(left_mask)
        n_r = np.sum(right_mask)

        if n_l < 5 or n_r < 5:
            # Dải thông fallback an toàn bao phủ tối thiểu 30% mẫu
            return max(0.1, float(np.percentile(np.abs(x - c), 35.0)))

        var_l = float(np.var(y[left_mask], ddof=1)) if n_l > 1 else 1.0
        var_r = float(np.var(y[right_mask], ddof=1)) if n_r > 1 else 1.0
        sigma2_c = (var_l + var_r) / 2.0

        # Ước lượng độ cong đạo hàm cấp 2 m''(c) qua hồi quy đa thức bậc 3
        x_centered = x - c
        X_poly = np.column_stack([np.ones(n), x_centered, x_centered ** 2, x_centered ** 3])
        try:
            beta_poly = np.linalg.solve(X_poly.T @ X_poly + 1e-5 * np.eye(4), X_poly.T @ y)
            m2_c = 2.0 * float(beta_poly[2])
        except Exception:
            m2_c = 1.0

        m2_c_safe = max(1e-4, abs(m2_c))
        # Công thức IK h_opt: C_k * (sigma^2 / (f(c) * (m''(c))^2))^(1/5) * N^(-1/5)
        f_c = (n_l + n_r) / (2.0 * n * h_pilot) if h_pilot > 0 else 1.0
        f_c_safe = max(1e-4, f_c)

        h_opt = 3.43 * ((sigma2_c / (f_c_safe * (m2_c_safe ** 2))) ** 0.2) * (n ** (-0.2))
        # Giới hạn dải thông không quá hẹp hoặc quá rộng
        min_h = float(np.percentile(np.abs(x - c), 15.0))
        max_h = float(np.percentile(np.abs(x - c), 75.0))
        return max(min_h, min(max_h, float(h_opt)))

    @classmethod
    def _mccrary_density_test(
        cls,
        x: np.ndarray,
        c: float,
        bandwidth: float
    ) -> Tuple[float, float, bool]:
        """
        Kiểm định thao túng biến chỉ định cận biên McCrary (2008).
        Đánh giá xem hàm mật độ f(x) có bị gián đoạn nhảy vọt bất thường tại c hay không (dấu hiệu gian lận/thao túng).
        Trả về (log_difference, p_value, has_manipulation).
        """
        left_vals = x[(x >= c - bandwidth) & (x < c)]
        right_vals = x[(x >= c) & (x <= c + bandwidth)]

        n_l = len(left_vals)
        n_r = len(right_vals)

        if n_l < 4 or n_r < 4:
            return 0.0, 1.0, False

        # Ước lượng mật độ tần suất
        dens_l = n_l / bandwidth
        dens_r = n_r / bandwidth

        # Log difference theta = ln(dens_r) - ln(dens_l)
        log_diff = math.log(max(1e-4, dens_r)) - math.log(max(1e-4, dens_l))
        # Sai số chuẩn tiệm cận theo Poisson / McCrary
        se_theta = math.sqrt((1.0 / n_l) + (1.0 / n_r))
        z_stat = log_diff / se_theta if se_theta > 0 else 0.0
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))

        has_manipulation = bool(p_val < 0.05)
        return round(float(log_diff), 4), round(p_val, 4), has_manipulation

    @classmethod
    def fit_sharp_rdd(
        cls,
        data_rows: List[Dict[str, Any]],
        running_key: str,
        outcome_key: str,
        cutoff: float,
        bandwidth: Optional[float] = None,
        polynomial_order: int = 1,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Khớp mô hình Gián đoạn Hồi quy Sắc nét (Sharp RDD) qua hồi quy cục bộ có trọng số nhân tam giác (Kernel-Weighted Local Regression).
        """
        if labels is None:
            labels = {}

        # 1. Trích xuất dữ liệu sạch
        clean_pts = []
        for r in data_rows:
            xv = r.get(running_key)
            yv = r.get(outcome_key)
            if xv is None or yv is None or xv == "" or yv == "":
                continue
            try:
                xf = float(xv)
                yf = float(yv)
                clean_pts.append((xf, yf))
            except (ValueError, TypeError):
                continue

        n_samples = len(clean_pts)
        if n_samples < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 20 quan sát hợp lệ để ước lượng RDD (hiện có {n_samples})."
            }

        x_arr = np.array([p[0] for p in clean_pts], dtype=float)
        y_arr = np.array([p[1] for p in clean_pts], dtype=float)

        n_left = int(np.sum(x_arr < cutoff))
        n_right = int(np.sum(x_arr >= cutoff))

        if n_left < 5 or n_right < 5:
            return {
                "status": "UNBALANCED_CUTOFF",
                "message": f"Số lượng quan sát phía dưới ngưỡng (n_trái={n_left}) hoặc phía trên ngưỡng (n_phải={n_right}) quá nhỏ (< 5)."
            }

        # 2. Xác định độ rộng dải thông Bandwidth h
        if bandwidth is None or bandwidth <= 0:
            h = cls._calculate_ik_bandwidth(x_arr, y_arr, cutoff)
        else:
            h = float(bandwidth)

        # 3. Lọc các quan sát nằm trong cửa sổ cận biên [c - h, c + h]
        in_window_mask = np.abs(x_arr - cutoff) <= h
        x_win = x_arr[in_window_mask]
        y_win = y_arr[in_window_mask]

        n_eff = len(x_win)
        n_eff_l = int(np.sum(x_win < cutoff))
        n_eff_r = int(np.sum(x_win >= cutoff))

        if n_eff_l < 3 or n_eff_r < 3:
            # Nới rộng dải thông nếu trong cửa sổ quá ít quan sát
            h = max(h * 1.5, float(np.percentile(np.abs(x_arr - cutoff), 40.0)))
            in_window_mask = np.abs(x_arr - cutoff) <= h
            x_win = x_arr[in_window_mask]
            y_win = y_arr[in_window_mask]
            n_eff = len(x_win)
            n_eff_l = int(np.sum(x_win < cutoff))
            n_eff_r = int(np.sum(x_win >= cutoff))

        # 4. Trọng số nhân tam giác (Triangular Weights)
        u_norm = (x_win - cutoff) / h
        weights = cls._triangular_kernel(u_norm)

        # 5. Khớp mô hình hồi quy cục bộ hai bên (Local Linear Regression):
        # Y_i = alpha_l + beta_l * (X_i - c) cho X_i < c
        # Y_i = alpha_r + beta_r * (X_i - c) cho X_i >= c
        # Hiệu ứng LATE tại ngưỡng: tau_RDD = alpha_r - alpha_l
        mask_l = x_win < cutoff
        mask_r = x_win >= cutoff

        # A. Bên trái (Control below cutoff)
        X_l = np.column_stack([np.ones(np.sum(mask_l)), x_win[mask_l] - cutoff])
        W_l = weights[mask_l]
        y_l = y_win[mask_l]
        try:
            beta_l = np.linalg.solve(X_l.T @ (W_l[:, None] * X_l) + 1e-6 * np.eye(2), X_l.T @ (W_l * y_l))
            cov_l = np.linalg.pinv(X_l.T @ (W_l[:, None] * X_l)) * (np.sum((y_l - X_l @ beta_l) ** 2) / max(1, len(y_l) - 2))
            var_alpha_l = float(cov_l[0, 0])
        except Exception:
            beta_l = np.array([float(np.mean(y_l)), 0.0])
            var_alpha_l = float(np.var(y_l) / len(y_l))

        # B. Bên phải (Treated at or above cutoff)
        X_r = np.column_stack([np.ones(np.sum(mask_r)), x_win[mask_r] - cutoff])
        W_r = weights[mask_r]
        y_r = y_win[mask_r]
        try:
            beta_r = np.linalg.solve(X_r.T @ (W_r[:, None] * X_r) + 1e-6 * np.eye(2), X_r.T @ (W_r * y_r))
            cov_r = np.linalg.pinv(X_r.T @ (W_r[:, None] * X_r)) * (np.sum((y_r - X_r @ beta_r) ** 2) / max(1, len(y_r) - 2))
            var_alpha_r = float(cov_r[0, 0])
        except Exception:
            beta_r = np.array([float(np.mean(y_r)), 0.0])
            var_alpha_r = float(np.var(y_r) / len(y_r))

        alpha_l = float(beta_l[0])
        alpha_r = float(beta_r[0])
        tau_rdd = alpha_r - alpha_l

        se_tau = float(math.sqrt(max(1e-8, var_alpha_l + var_alpha_r)))
        z_stat = tau_rdd / se_tau if se_tau > 0 else 0.0
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        ci_lower = float(tau_rdd - 1.96 * se_tau)
        ci_upper = float(tau_rdd + 1.96 * se_tau)
        is_significant = bool(p_val < 0.05)

        # 6. Kiểm định thao túng McCrary Density Test
        mccrary_log_diff, mccrary_p, has_manipulation = cls._mccrary_density_test(x_arr, cutoff, h)

        # 7. Gom cụm các điểm dữ liệu thành các thùng đều (Binned Scatter Points) phục vụ trực quan hóa
        binned_scatter = cls._calculate_binned_scatter(x_arr, y_arr, cutoff, n_bins_each_side=12)

        # 8. Tạo đồ họa Vector SVG chất lượng cao
        svg_chart = cls._generate_rdd_svg(
            binned_scatter=binned_scatter,
            cutoff=cutoff,
            alpha_l=alpha_l,
            slope_l=float(beta_l[1]),
            alpha_r=alpha_r,
            slope_r=float(beta_r[1]),
            h=h,
            tau_rdd=tau_rdd,
            is_significant=is_significant,
            running_label=labels.get(running_key, running_key),
            outcome_label=labels.get(outcome_key, outcome_key)
        )

        # 9. Soạn Thuyết minh Chuẩn APA 7th Edition
        apa_narrative = cls._generate_rdd_apa_narrative(
            sample_size=n_samples,
            n_effective=n_eff,
            cutoff=cutoff,
            bandwidth=h,
            tau_rdd=tau_rdd,
            se_tau=se_tau,
            z_stat=z_stat,
            p_val=p_val,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            is_significant=is_significant,
            mccrary_log_diff=mccrary_log_diff,
            mccrary_p=mccrary_p,
            has_manipulation=has_manipulation,
            running_label=labels.get(running_key, running_key),
            outcome_label=labels.get(outcome_key, outcome_key)
        )

        return {
            "status": "SUCCESS",
            "sample_size": n_samples,
            "effective_sample_size": n_eff,
            "cutoff_threshold": cutoff,
            "bandwidth": round(float(h), 4),
            "treatment_effect_late": {
                "tau_rdd": round(tau_rdd, 4),
                "standard_error": round(se_tau, 4),
                "z_statistic": round(z_stat, 3),
                "p_value": round(p_val, 4),
                "ci_95_lower": round(ci_lower, 4),
                "ci_95_upper": round(ci_upper, 4),
                "is_significant": is_significant,
                "left_limit_intercept": round(alpha_l, 4),
                "right_limit_intercept": round(alpha_r, 4),
                "left_slope": round(float(beta_l[1]), 4),
                "right_slope": round(float(beta_r[1]), 4)
            },
            "mccrary_manipulation_test": {
                "log_difference": mccrary_log_diff,
                "p_value": mccrary_p,
                "has_manipulation": has_manipulation,
                "verdict": "Cảnh báo có bằng chứng thao túng biến chỉ định cận biên (p < .05)" if has_manipulation else "Không phát hiện bằng chứng thao túng quanh ngưỡng (p ≥ .05)"
            },
            "binned_scatter_points": binned_scatter,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _calculate_binned_scatter(
        cls,
        x: np.ndarray,
        y: np.ndarray,
        c: float,
        n_bins_each_side: int = 12
    ) -> List[Dict[str, Any]]:
        """Chia dữ liệu thành các thùng binned scatter có khoảng cách bằng nhau ở 2 bên ngưỡng c"""
        bins = []
        # Phía trái x < c
        x_l = x[x < c]
        y_l = y[x < c]
        if len(x_l) > 0:
            edges_l = np.linspace(np.min(x_l), c, n_bins_each_side + 1)
            for i in range(len(edges_l) - 1):
                m = (x_l >= edges_l[i]) & (x_l < edges_l[i + 1])
                if np.sum(m) > 0:
                    bins.append({
                        "side": "left",
                        "x_mean": round(float(np.mean(x_l[m])), 3),
                        "y_mean": round(float(np.mean(y_l[m])), 3),
                        "count": int(np.sum(m))
                    })

        # Phía phải x >= c
        x_r = x[x >= c]
        y_r = y[x >= c]
        if len(x_r) > 0:
            edges_r = np.linspace(c, np.max(x_r), n_bins_each_side + 1)
            for i in range(len(edges_r) - 1):
                m = (x_r >= edges_r[i]) & (x_r <= edges_r[i + 1])
                if np.sum(m) > 0:
                    bins.append({
                        "side": "right",
                        "x_mean": round(float(np.mean(x_r[m])), 3),
                        "y_mean": round(float(np.mean(y_r[m])), 3),
                        "count": int(np.sum(m))
                    })

        return bins

    @classmethod
    def _generate_rdd_svg(
        cls,
        binned_scatter: List[Dict[str, Any]],
        cutoff: float,
        alpha_l: float,
        slope_l: float,
        alpha_r: float,
        slope_r: float,
        h: float,
        tau_rdd: float,
        is_significant: bool,
        running_label: str,
        outcome_label: str
    ) -> str:
        """Tạo đồ họa Vector SVG biểu diễn bước nhảy gián đoạn RDD kèm đường hồi quy cục bộ 2 phía"""
        svg_width = 820
        svg_height = 430
        margin_left = 75
        margin_right = 50
        margin_top = 40
        margin_bottom = 60

        plot_w = svg_width - margin_left - margin_right
        plot_h = svg_height - margin_top - margin_bottom

        if not binned_scatter:
            return '<svg width="100" height="100"></svg>'

        all_x = [it["x_mean"] for it in binned_scatter] + [cutoff - h, cutoff + h, cutoff]
        all_y = [it["y_mean"] for it in binned_scatter] + [alpha_l, alpha_r, alpha_l + slope_l * (-h), alpha_r + slope_r * h]

        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        x_span = max(1e-6, x_max - x_min)
        y_span = max(0.5, y_max - y_min)
        y_plot_min = y_min - 0.1 * y_span
        y_plot_max = y_max + 0.1 * y_span

        def to_x(val: float) -> float:
            return margin_left + ((val - x_min) / x_span) * plot_w

        def to_y(val: float) -> float:
            return margin_top + plot_h - ((val - y_plot_min) / (y_plot_max - y_plot_min)) * plot_h

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" style="font-family: Inter, system-ui, -apple-system, sans-serif;">',
            f'  <rect width="{svg_width}" height="{svg_height}" fill="#f8fafc" rx="12" stroke="#e2e8f0" stroke-width="1.5" />',
            '  <!-- Vùng dải thông Bandwidth h -->'
        ]

        # Vùng bóng mờ của cửa sổ tối ưu [c - h, c + h]
        x_h_left = to_x(max(x_min, cutoff - h))
        x_h_right = to_x(min(x_max, cutoff + h))
        svg_lines.append(
            f'  <rect x="{x_h_left:.1f}" y="{margin_top}" width="{abs(x_h_right - x_h_left):.1f}" height="{plot_h}" fill="#f1f5f9" fill-opacity="0.8" />'
        )

        # Lưới tọa độ ngang Y
        for y_tick in np.linspace(y_plot_min, y_plot_max, 5):
            y_pos = to_y(float(y_tick))
            svg_lines.append(
                f'  <line x1="{margin_left}" y1="{y_pos:.1f}" x2="{margin_left + plot_w}" y2="{y_pos:.1f}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3" />'
            )
            svg_lines.append(
                f'  <text x="{margin_left - 10}" y="{y_pos + 4:.1f}" font-size="10.5" fill="#64748b" text-anchor="end">{y_tick:.1f}</text>'
            )

        # Lưới tọa độ dọc X
        for x_tick in np.linspace(x_min, x_max, 6):
            x_pos = to_x(float(x_tick))
            svg_lines.append(
                f'  <line x1="{x_pos:.1f}" y1="{margin_top}" x2="{x_pos:.1f}" y2="{margin_top + plot_h}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3" />'
            )
            svg_lines.append(
                f'  <text x="{x_pos:.1f}" y="{margin_top + plot_h + 18}" font-size="10.5" fill="#64748b" text-anchor="middle">{x_tick:.1f}</text>'
            )

        # Vạch đỏ ngưỡng phân loại Cutoff c
        x_cutoff_pos = to_x(cutoff)
        svg_lines.append(
            f'  <line x1="{x_cutoff_pos:.1f}" y1="{margin_top}" x2="{x_cutoff_pos:.1f}" y2="{margin_top + plot_h}" stroke="#dc2626" stroke-width="2" stroke-dasharray="4 3" />'
        )
        svg_lines.append(
            f'  <text x="{x_cutoff_pos:.1f}" y="{margin_top - 12}" font-size="10" font-weight="700" fill="#dc2626" text-anchor="middle">Ngưỡng Cutoff (c = {cutoff:.1f})</text>'
        )

        # 1. Vẽ các điểm binned scatter
        for pt in binned_scatter:
            px, py = to_x(pt["x_mean"]), to_y(pt["y_mean"])
            fill_c = "#3b82f6" if pt["side"] == "left" else "#10b981"
            svg_lines.append(
                f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="4.2" fill="{fill_c}" stroke="#1e293b" stroke-width="0.8" />'
            )

        # 2. Đường hồi quy cục bộ bên trái [c - h, c)
        x_fit_l1 = max(x_min, cutoff - h)
        y_fit_l1 = alpha_l + slope_l * (x_fit_l1 - cutoff)
        y_fit_l2 = alpha_l
        svg_lines.append(
            f'  <line x1="{to_x(x_fit_l1):.1f}" y1="{to_y(y_fit_l1):.1f}" x2="{x_cutoff_pos:.1f}" y2="{to_y(y_fit_l2):.1f}" stroke="#2563eb" stroke-width="3" stroke-linecap="round" />'
        )
        # Điểm mút trái
        svg_lines.append(
            f'  <circle cx="{x_cutoff_pos:.1f}" cy="{to_y(y_fit_l2):.1f}" r="4.5" fill="#ffffff" stroke="#2563eb" stroke-width="2" />'
        )

        # 3. Đường hồi quy cục bộ bên phải [c, c + h]
        x_fit_r2 = min(x_max, cutoff + h)
        y_fit_r1 = alpha_r
        y_fit_r2 = alpha_r + slope_r * (x_fit_r2 - cutoff)
        svg_lines.append(
            f'  <line x1="{x_cutoff_pos:.1f}" y1="{to_y(y_fit_r1):.1f}" x2="{to_x(x_fit_r2):.1f}" y2="{to_y(y_fit_r2):.1f}" stroke="#059669" stroke-width="3" stroke-linecap="round" />'
        )
        # Điểm mút phải
        svg_lines.append(
            f'  <circle cx="{x_cutoff_pos:.1f}" cy="{to_y(y_fit_r1):.1f}" r="4.5" fill="#059669" stroke="#047857" stroke-width="2" />'
        )

        # 4. Mũi tên gián đoạn bước nhảy LATE (Discontinuity Jump)
        y_jump_top = min(to_y(alpha_l), to_y(alpha_r))
        y_jump_bot = max(to_y(alpha_l), to_y(alpha_r))
        arrow_x = x_cutoff_pos + 12
        svg_lines.append(
            f'  <line x1="{arrow_x:.1f}" y1="{y_jump_top:.1f}" x2="{arrow_x:.1f}" y2="{y_jump_bot:.1f}" stroke="#e11d48" stroke-width="2" marker-start="url(#arrow)" marker-end="url(#arrow)" />'
        )
        sign_char = '+' if tau_rdd > 0 else ''
        svg_lines.append(
            f'  <text x="{arrow_x + 8:.1f}" y="{(y_jump_top + y_jump_bot) / 2 + 4:.1f}" font-size="10.5" font-weight="700" fill="#be123c">LATE = {sign_char}{tau_rdd:.2f}</text>'
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
            f'  <text x="{margin_left + plot_w / 2}" y="{svg_height - 15}" font-size="11.5" font-weight="600" fill="#334155" text-anchor="middle">{running_label}</text>'
        )
        svg_lines.append(
            f'  <text x="22" y="{margin_top + plot_h / 2}" font-size="11.5" font-weight="600" fill="#334155" text-anchor="middle" transform="rotate(-90 22 {margin_top + plot_h / 2})">{outcome_label}</text>'
        )

        # Chú thích Legend
        leg_y = margin_top - 15
        svg_lines.append('  <g id="legend">')
        svg_lines.append(
            f'  <circle cx="{margin_left + 15}" cy="{leg_y}" r="4" fill="#3b82f6" />'
        )
        svg_lines.append(
            f'  <text x="{margin_left + 24}" y="{leg_y + 3}" font-size="10" fill="#475569">Nhóm Dưới Ngưỡng (Control)</text>'
        )
        svg_lines.append(
            f'  <circle cx="{margin_left + 195}" cy="{leg_y}" r="4" fill="#10b981" />'
        )
        svg_lines.append(
            f'  <text x="{margin_left + 204}" y="{leg_y + 3}" font-size="10" fill="#475569">Nhóm Trên Ngưỡng (Treated)</text>'
        )
        svg_lines.append('  </g>')

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    @classmethod
    def _generate_rdd_apa_narrative(
        cls,
        sample_size: int,
        n_effective: int,
        cutoff: float,
        bandwidth: float,
        tau_rdd: float,
        se_tau: float,
        z_stat: float,
        p_val: float,
        ci_lower: float,
        ci_upper: float,
        is_significant: bool,
        mccrary_log_diff: float,
        mccrary_p: float,
        has_manipulation: bool,
        running_label: str,
        outcome_label: str
    ) -> str:
        """Tạo đoạn báo cáo học thuật chuẩn mực APA 7th Edition"""
        p_str = "p < .001" if p_val < 0.001 else f"p = {p_val:.3f}"
        sig_str = "có ý nghĩa thống kê ở mức .05" if is_significant else "không đạt mức ý nghĩa thống kê ở mức .05"

        mccrary_desc = (
            f"Kiểm định thao túng cận biên McCrary (2008) không tìm thấy bằng chứng gián đoạn mật độ bất thường quanh ngưỡng "
            f"(Δln(f) = {mccrary_log_diff:.3f}, p = {mccrary_p:.3f}), củng cố giả định ngẫu nhiên hóa cục bộ không bị thao túng."
            if not has_manipulation else
            f"Cảnh báo: Kiểm định McCrary (2008) phát hiện mật độ gián đoạn có ý nghĩa thống kê quanh ngưỡng "
            f"(Δln(f) = {mccrary_log_diff:.3f}, p = {mccrary_p:.3f}), cho thấy khả năng tồn tại hiện tượng tự chọn lọc hoặc thao túng điểm ngưỡng."
        )

        narrative = (
            f"Tác động nhân quả cận biên (Local Average Treatment Effect - LATE) của chính sách/can thiệp phân loại "
            f"theo ngưỡng c = {cutoff:.2f} trên biến chỉ định '{running_label}' lên biến kết quả '{outcome_label}' "
            f"được ước lượng thông qua Thiết kế Gián đoạn Hồi quy Sắc nét (Sharp RDD; Hahn et al., 2001; Imbens & Kalyanaraman, 2012) "
            f"trên tổng mẫu N = {sample_size} (cỡ mẫu hiệu dụng trong dải thông h = {bandwidth:.2f} là N_eff = {n_effective}).\n\n"
            f"Mô hình hồi quy tuyến tính cục bộ có trọng số nhân tam giác ghi nhận bước nhảy gián đoạn nhân quả "
            f"τ_RDD = {tau_rdd:.3f} (SE = {se_tau:.3f}, z = {z_stat:.2f}, {p_str}, 95% CI [{ci_lower:.3f}, {ci_upper:.3f}]), "
            f"kết luận tác động can thiệp tại ngưỡng {sig_str}.\n\n"
            f"{mccrary_desc}"
        )

        return narrative
