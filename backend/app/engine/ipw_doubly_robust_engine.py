import math
import numpy as np
import scipy.stats as stats
from typing import Dict, Any, List, Optional, Tuple


class IPWDoublyRobustEngine:
    """
    Động cơ Trọng số Xác suất Nghịch đảo & Ước lượng Vững Kép (IPW & Doubly Robust / AIPW Engine)
    phục vụ suy diễn nhân quả từ dữ liệu khảo sát quan sát (Observational Survey Causal Inference).
    
    Tuân thủ phương pháp luận kinh tế lượng & thống kê dịch tễ học quốc tế:
    - Rosenbaum, P. R., & Rubin, D. B. (1983). The central role of the propensity score in observational studies.
      Biometrika, 70(1), 41-55.
    - Robins, J. M., Rotnitzky, A., & Zhao, L. P. (1994). Estimation of regression coefficients when some regressors
      are not always observed. JASA, 89(427), 846-866.
    - Lunceford, J. K., & Davidian, M. (2004). Stratification and weighting via the propensity score: A review and
      practical guide. Statistics in Medicine, 23(19), 2937-2960.
    - Austin, P. C., & Stuart, E. A. (2015). Moving towards best practice when using inverse probability of treatment
      weighting (IPTW). Statistics in Medicine, 34(28), 3661-3679.
    - Bang, H., & Robins, J. M. (2005). Doubly robust estimation in missing data and causal inference models.
      Biometrics, 61(4), 962-972.
    - Li, F., Morgan, K. L., & Zaslavsky, A. M. (2018). Balancing covariates via propensity score weighting.
      JASA, 113(521), 390-400.
    """

    @staticmethod
    def _sigmoid(z: float) -> float:
        if z >= 35.0:
            return 1.0 - 1e-15
        elif z <= -35.0:
            return 1e-15
        return 1.0 / (1.0 + math.exp(-z))

    @classmethod
    def _fit_logistic_regression(
        cls,
        X: np.ndarray,
        y: np.ndarray,
        max_iter: int = 50,
        tol: float = 1e-6,
        ridge_lambda: float = 1e-4
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Khớp mô hình Logistic hồi quy Propensity Score qua thuật toán IRLS (Iteratively Reweighted Least Squares).
        X: (N, K) ma trận thiết kế có cột 1 cho intercept
        y: (N,) vector nhị phân can thiệp {0, 1}
        """
        n, k = X.shape
        beta = np.zeros(k)

        for _ in range(max_iter):
            p = np.array([cls._sigmoid(float(z)) for z in X @ beta])
            p_safe = np.clip(p, 1e-6, 1.0 - 1e-6)
            W = p_safe * (1.0 - p_safe)

            grad = X.T @ (y - p_safe) - ridge_lambda * beta
            H = X.T @ (W[:, None] * X) + ridge_lambda * np.eye(k)

            try:
                delta = np.linalg.solve(H, grad)
            except np.linalg.LinAlgError:
                delta = np.linalg.pinv(H) @ grad

            beta += delta
            if np.max(np.abs(delta)) < tol:
                break

        fitted_p = np.array([cls._sigmoid(float(z)) for z in X @ beta])
        return beta, fitted_p

    @classmethod
    def _fit_ols(cls, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Hồi quy tuyến tính OLS thông thường: beta = (X^T X)^-1 X^T y"""
        k = X.shape[1]
        try:
            return np.linalg.solve(X.T @ X + 1e-6 * np.eye(k), X.T @ y)
        except np.linalg.LinAlgError:
            return np.linalg.pinv(X.T @ X + 1e-6 * np.eye(k)) @ (X.T @ y)

    @classmethod
    def estimate_causal_effects(
        cls,
        data_rows: List[Dict[str, Any]],
        treatment_key: str,
        outcome_key: str,
        covariate_keys: List[str],
        treatment_value: Optional[str] = None,
        weight_scheme: str = "ate",  # "ate", "att", "overlap", "stabilized"
        trim_weights: bool = True,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Ước lượng tác động nhân quả qua Trọng số IPW và Ước lượng Vững Kép (Doubly Robust / AIPW).
        """
        if labels is None:
            labels = {}

        if not covariate_keys:
            return {
                "status": "INVALID_SPECIFICATION",
                "message": "Cần khai báo ít nhất một biến đồng biến (covariate) để cân bằng xác suất can thiệp."
            }

        # 1. Trích xuất mảng dữ liệu sạch
        clean_data = []
        for row in data_rows:
            d_val = row.get(treatment_key)
            y_val = row.get(outcome_key)
            if d_val is None or y_val is None or d_val == "" or y_val == "":
                continue

            try:
                y_float = float(y_val)
            except (ValueError, TypeError):
                continue

            # Xử lý treatment nhị phân
            if treatment_value is not None:
                d_binary = 1 if str(d_val).strip() == str(treatment_value).strip() else 0
            else:
                # Tự động: nếu là số >= 1 hoặc chuỗi yes/true/treated
                s_d = str(d_val).strip().lower()
                d_binary = 1 if s_d in ["1", "true", "yes", "treated", "can_thiep"] else 0

            # Covariates
            cov_vals = []
            valid_covs = True
            for ck in covariate_keys:
                cv = row.get(ck)
                if cv is None or cv == "":
                    valid_covs = False
                    break
                try:
                    cov_vals.append(float(cv))
                except (ValueError, TypeError):
                    valid_covs = False
                    break

            if valid_covs:
                clean_data.append({
                    "d": d_binary,
                    "y": y_float,
                    "x": cov_vals
                })

        n_samples = len(clean_data)
        if n_samples < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 16 bản ghi hợp lệ để ước lượng IPW và Doubly Robust (hiện có {n_samples})."
            }

        y_arr = np.array([item["y"] for item in clean_data], dtype=float)
        d_arr = np.array([item["d"] for item in clean_data], dtype=int)
        x_raw = np.array([item["x"] for item in clean_data], dtype=float)

        n_treated = int(np.sum(d_arr))
        n_control = n_samples - n_treated

        if n_treated < 5 or n_control < 5:
            return {
                "status": "UNBALANCED_TREATMENT",
                "message": f"Số lượng quan sát nhóm can thiệp (n={n_treated}) hoặc nhóm đối chứng (n={n_control}) quá nhỏ (< 5)."
            }

        # 2. Ước lượng Propensity Score e_i qua Logistic Regression
        # Chuẩn hóa ma trận thiết kế có cột intercept 1
        X_design = np.column_stack([np.ones(n_samples), x_raw])
        beta_ps, p_scores = cls._fit_logistic_regression(X_design, d_arr)

        # Tránh các giá trị xác suất quá sát 0 hoặc 1 (Trimming / Clamping)
        p_scores_safe = np.clip(p_scores, 0.01, 0.99)
        p_marginal = n_treated / n_samples

        # 3. Tính toán Trọng số IPW theo cơ chế được chọn
        scheme = weight_scheme.lower()
        if scheme == "att":
            # w_i = D_i + (1 - D_i) * (e_i / (1 - e_i))
            weights = np.where(d_arr == 1, 1.0, p_scores_safe / (1.0 - p_scores_safe))
        elif scheme == "overlap" or scheme == "ato":
            # Li, Morgan & Zaslavsky (2018): w_i = D_i * (1 - e_i) + (1 - D_i) * e_i
            weights = np.where(d_arr == 1, 1.0 - p_scores_safe, p_scores_safe)
        elif scheme == "stabilized":
            # Hernán & Robins (2006): w_i = D * (p_marg / e) + (1-D) * ((1-p_marg)/(1-e))
            weights = np.where(d_arr == 1, p_marginal / p_scores_safe, (1.0 - p_marginal) / (1.0 - p_scores_safe))
        else:
            # Mặc định ATE: w_i = D / e + (1 - D) / (1 - e)
            scheme = "ate"
            weights = np.where(d_arr == 1, 1.0 / p_scores_safe, 1.0 / (1.0 - p_scores_safe))

        # Trimming trọng số tại bách phân vị 1% và 99% nếu bật
        if trim_weights:
            w_p01 = np.percentile(weights, 1.0)
            w_p99 = np.percentile(weights, 99.0)
            weights = np.clip(weights, w_p01, w_p99)

        # 4. Ước lượng Causal Treatment Effects:
        # A. Hiệu ứng thô ban đầu (Unadjusted Difference in Means)
        mean_y_treated_raw = float(np.mean(y_arr[d_arr == 1]))
        mean_y_control_raw = float(np.mean(y_arr[d_arr == 0]))
        raw_diff = mean_y_treated_raw - mean_y_control_raw
        raw_se = float(math.sqrt(np.var(y_arr[d_arr == 1], ddof=1) / n_treated + np.var(y_arr[d_arr == 0], ddof=1) / n_control))

        # B. Hajek Normalized IPW Estimator (Horvitz-Thompson biến thể chuẩn hóa)
        w_treated = weights * d_arr
        w_control = weights * (1 - d_arr)

        sum_w_t = np.sum(w_treated)
        sum_w_c = np.sum(w_control)

        mu_1_ipw = float(np.sum(w_treated * y_arr) / sum_w_t) if sum_w_t > 0 else 0.0
        mu_0_ipw = float(np.sum(w_control * y_arr) / sum_w_c) if sum_w_c > 0 else 0.0
        tau_ipw = mu_1_ipw - mu_0_ipw

        # Sai số chuẩn Lunceford & Davidian (2004) cho IPW
        phi_1 = (d_arr * weights * (y_arr - mu_1_ipw)) / (sum_w_t / n_samples)
        phi_0 = ((1 - d_arr) * weights * (y_arr - mu_0_ipw)) / (sum_w_c / n_samples)
        ipw_var = np.var(phi_1 - phi_0, ddof=1) / n_samples
        ipw_se = float(math.sqrt(max(1e-6, ipw_var)))
        ipw_z = tau_ipw / ipw_se if ipw_se > 0 else 0.0
        ipw_p = float(2.0 * (1.0 - stats.norm.cdf(abs(ipw_z))))

        # C. Ước lượng Vững Kép (Doubly Robust / Augmented IPW - AIPW; Robins et al. 1994, Bang & Robins 2005)
        # Khớp mô hình kết quả Outcome Regression m_1(X) và m_0(X)
        X_t = X_design[d_arr == 1]
        y_t = y_arr[d_arr == 1]
        beta_m1 = cls._fit_ols(X_t, y_t)

        X_c = X_design[d_arr == 0]
        y_c = y_arr[d_arr == 0]
        beta_m0 = cls._fit_ols(X_c, y_c)

        m1_pred = X_design @ beta_m1
        m0_pred = X_design @ beta_m0

        # Công thức AIPW:
        # gamma_1 = m_1(X) + D * (Y - m_1(X)) / e
        # gamma_0 = m_0(X) + (1 - D) * (Y - m_0(X)) / (1 - e)
        gamma_1 = m1_pred + (d_arr * (y_arr - m1_pred)) / p_scores_safe
        gamma_0 = m0_pred + ((1 - d_arr) * (y_arr - m0_pred)) / (1.0 - p_scores_safe)

        tau_dr = float(np.mean(gamma_1 - gamma_0))
        dr_var = np.var(gamma_1 - gamma_0, ddof=1) / n_samples
        dr_se = float(math.sqrt(max(1e-6, dr_var)))
        dr_z = tau_dr / dr_se if dr_se > 0 else 0.0
        dr_p = float(2.0 * (1.0 - stats.norm.cdf(abs(dr_z))))

        dr_ci_low = float(tau_dr - 1.96 * dr_se)
        dr_ci_high = float(tau_dr + 1.96 * dr_se)

        # 5. Đánh giá Cân bằng Đồng biến (Covariate Balance Diagnostics & Love Plot Metrics)
        # Tính ASMD (Absolute Standardized Mean Difference) trước và sau khi gán trọng số
        balance_diagnostics = []
        for idx_c, ck in enumerate(covariate_keys):
            cov_col = x_raw[:, idx_c]
            c_treated_raw = cov_col[d_arr == 1]
            c_control_raw = cov_col[d_arr == 0]

            s_pool = math.sqrt((np.var(c_treated_raw, ddof=1) + np.var(c_control_raw, ddof=1)) / 2.0)
            if s_pool < 1e-6:
                s_pool = 1.0

            # Raw ASMD
            raw_smd = abs(np.mean(c_treated_raw) - np.mean(c_control_raw)) / s_pool

            # Weighted ASMD
            mean_c_t_w = np.sum(w_treated * cov_col) / sum_w_t if sum_w_t > 0 else 0.0
            mean_c_c_w = np.sum(w_control * cov_col) / sum_w_c if sum_w_c > 0 else 0.0
            weighted_smd = abs(mean_c_t_w - mean_c_c_w) / s_pool

            # Variance ratio sau trọng số
            var_t_w = np.sum(w_treated * (cov_col - mean_c_t_w) ** 2) / sum_w_t if sum_w_t > 0 else 1.0
            var_c_w = np.sum(w_control * (cov_col - mean_c_c_w) ** 2) / sum_w_c if sum_w_c > 0 else 1.0
            var_ratio_w = var_t_w / var_c_w if var_c_w > 1e-6 else 1.0

            balance_diagnostics.append({
                "covariate_key": ck,
                "covariate_label": labels.get(ck, ck),
                "raw_asmd": round(float(raw_smd), 4),
                "weighted_asmd": round(float(weighted_smd), 4),
                "weighted_variance_ratio": round(float(var_ratio_w), 3),
                "is_balanced": bool(weighted_smd <= 0.10),
                "improvement_pct": round(float(max(0.0, (raw_smd - weighted_smd) / raw_smd * 100.0)), 1) if raw_smd > 1e-6 else 0.0
            })

        max_weighted_asmd = max(it["weighted_asmd"] for it in balance_diagnostics)
        all_balanced = bool(all(it["is_balanced"] for it in balance_diagnostics))

        # 6. Tạo Đồ họa Vector SVG Love Plot (Biểu đồ Cân bằng Mẫu)
        svg_love_plot = cls._generate_love_plot_svg(
            diagnostics=balance_diagnostics
        )

        # 7. Soạn Thuyết minh Học thuật Chuẩn APA 7th Edition
        apa_narrative = cls._generate_ipw_apa_narrative(
            sample_size=n_samples,
            n_treated=n_treated,
            n_control=n_control,
            scheme=scheme.upper(),
            raw_diff=raw_diff,
            tau_ipw=tau_ipw,
            ipw_se=ipw_se,
            ipw_p=ipw_p,
            tau_dr=tau_dr,
            dr_se=dr_se,
            dr_p=dr_p,
            dr_ci_low=dr_ci_low,
            dr_ci_high=dr_ci_high,
            max_weighted_asmd=max_weighted_asmd,
            all_balanced=all_balanced,
            treatment_label=labels.get(treatment_key, treatment_key),
            outcome_label=labels.get(outcome_key, outcome_key)
        )

        return {
            "status": "SUCCESS",
            "sample_size": n_samples,
            "treated_count": n_treated,
            "control_count": n_control,
            "weight_scheme": scheme.upper(),
            "unadjusted_effect": {
                "difference_in_means": round(raw_diff, 4),
                "standard_error": round(raw_se, 4),
                "treated_mean": round(mean_y_treated_raw, 4),
                "control_mean": round(mean_y_control_raw, 4)
            },
            "ipw_estimator": {
                "treatment_effect": round(tau_ipw, 4),
                "standard_error": round(ipw_se, 4),
                "z_value": round(ipw_z, 3),
                "p_value": round(ipw_p, 4),
                "is_significant": bool(ipw_p < 0.05)
            },
            "doubly_robust_estimator": {
                "treatment_effect": round(tau_dr, 4),
                "standard_error": round(dr_se, 4),
                "z_value": round(dr_z, 3),
                "p_value": round(dr_p, 4),
                "ci_95_lower": round(dr_ci_low, 4),
                "ci_95_upper": round(dr_ci_high, 4),
                "is_significant": bool(dr_p < 0.05)
            },
            "covariate_balance": {
                "all_balanced_under_0_10": bool(all_balanced),
                "maximum_weighted_asmd": round(max_weighted_asmd, 4),
                "diagnostics": balance_diagnostics
            },
            "svg_love_plot": svg_love_plot,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_love_plot_svg(cls, diagnostics: List[Dict[str, Any]]) -> str:
        """Tạo biểu đồ Love Plot Vector SVG chuẩn mực so sánh ASMD trước và sau gán trọng số"""
        svg_width = 820
        svg_height = max(360, 100 + len(diagnostics) * 40)
        margin_left = 180
        margin_right = 60
        margin_top = 40
        margin_bottom = 60

        plot_w = svg_width - margin_left - margin_right
        plot_h = svg_height - margin_top - margin_bottom

        # Trục X từ 0.0 đến max(ASMD) + 0.1, tối thiểu 0.40
        max_smd_val = max(max(it["raw_asmd"], it["weighted_asmd"]) for it in diagnostics) if diagnostics else 0.4
        x_max = max(0.40, math.ceil(max_smd_val * 10) / 10 + 0.05)

        def to_x(val: float) -> float:
            return margin_left + (val / x_max) * plot_w

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" style="font-family: Inter, system-ui, -apple-system, sans-serif;">',
            f'  <rect width="{svg_width}" height="{svg_height}" fill="#f8fafc" rx="12" stroke="#e2e8f0" stroke-width="1.5" />',
            '  <!-- Đường ngưỡng chuẩn mực ASMD = 0.10 (Austin 2009) -->'
        ]

        # Vạch đỏ ngưỡng 0.10
        x_thresh = to_x(0.10)
        svg_lines.append(
            f'  <line x1="{x_thresh:.1f}" y1="{margin_top}" x2="{x_thresh:.1f}" y2="{margin_top + plot_h}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 3" />'
        )
        svg_lines.append(
            f'  <text x="{x_thresh:.1f}" y="{margin_top - 10}" font-size="9.5" font-weight="700" fill="#dc2626" text-anchor="middle">Ngưỡng chuẩn (ASMD ≤ 0.10)</text>'
        )

        # Lưới tọa độ X
        for x_t in np.linspace(0.0, x_max, 5):
            x_pos = to_x(float(x_t))
            svg_lines.append(
                f'  <line x1="{x_pos:.1f}" y1="{margin_top}" x2="{x_pos:.1f}" y2="{margin_top + plot_h}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3" />'
            )
            svg_lines.append(
                f'  <text x="{x_pos:.1f}" y="{margin_top + plot_h + 18}" font-size="10.5" fill="#64748b" text-anchor="middle">{x_t:.2f}</text>'
            )

        # Trục chính
        svg_lines.append(
            f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{margin_left + plot_w}" y2="{margin_top + plot_h}" stroke="#475569" stroke-width="1.5" />'
        )
        svg_lines.append(
            f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="#475569" stroke-width="1.5" />'
        )

        svg_lines.append(
            f'  <text x="{margin_left + plot_w / 2}" y="{svg_height - 15}" font-size="11.5" font-weight="600" fill="#334155" text-anchor="middle">Chênh lệch Trung bình Chuẩn hóa Tuyệt đối (Absolute SMD)</text>'
        )

        # Vẽ từng hàng biến đồng biến (Covariate)
        row_step = plot_h / (len(diagnostics) + 1)
        for idx, it in enumerate(diagnostics):
            y_pos = margin_top + (idx + 1) * row_step
            lbl = it["covariate_label"]
            if len(lbl) > 22:
                lbl = lbl[:20] + "…"

            # Đường gióng ngang
            svg_lines.append(
                f'  <line x1="{margin_left}" y1="{y_pos:.1f}" x2="{margin_left + plot_w}" y2="{y_pos:.1f}" stroke="#f1f5f9" stroke-width="1" />'
            )
            # Tên biến bên trái
            svg_lines.append(
                f'  <text x="{margin_left - 12}" y="{y_pos + 4:.1f}" font-size="11" font-weight="500" fill="#1e293b" text-anchor="end">{lbl}</text>'
            )

            # Điểm Raw ASMD (Vòng tròn đỏ rỗng)
            rx = to_x(it["raw_asmd"])
            svg_lines.append(
                f'  <circle cx="{rx:.1f}" cy="{y_pos:.1f}" r="5" fill="#fecaca" stroke="#dc2626" stroke-width="1.5" />'
            )

            # Điểm Weighted ASMD (Hình quả trám xanh ngọc đặc)
            wx = to_x(it["weighted_asmd"])
            d_path = f"M {wx:.1f} {y_pos - 6:.1f} L {wx + 6:.1f} {y_pos:.1f} L {wx:.1f} {y_pos + 6:.1f} L {wx - 6:.1f} {y_pos:.1f} Z"
            svg_lines.append(
                f'  <path d="{d_path}" fill="#059669" stroke="#047857" stroke-width="1.5" />'
            )

            # Mũi tên kết nối thể hiện độ cải thiện nếu raw > weighted
            if rx > wx + 8:
                svg_lines.append(
                    f'  <line x1="{rx - 6:.1f}" y1="{y_pos:.1f}" x2="{wx + 8:.1f}" y2="{y_pos:.1f}" stroke="#cbd5e1" stroke-width="1.2" stroke-dasharray="2 2" />'
                )

        # Chú thích Legend
        svg_lines.append('  <g id="legend">')
        leg_y = margin_top - 15
        # Raw
        svg_lines.append(
            f'  <circle cx="{margin_left + 15}" cy="{leg_y}" r="4.5" fill="#fecaca" stroke="#dc2626" stroke-width="1.5" />'
        )
        svg_lines.append(
            f'  <text x="{margin_left + 26}" y="{leg_y + 3}" font-size="10.5" fill="#475569">Mẫu thô chưa cân bằng (Unadjusted)</text>'
        )
        # Weighted
        svg_lines.append(
            f'  <path d="M {margin_left + 230} {leg_y - 4.5} L {margin_left + 234.5} {leg_y} L {margin_left + 230} {leg_y + 4.5} L {margin_left + 225.5} {leg_y} Z" fill="#059669" />'
        )
        svg_lines.append(
            f'  <text x="{margin_left + 242}" y="{leg_y + 3}" font-size="10.5" font-weight="600" fill="#065f46">Mẫu sau gán trọng số IPW</text>'
        )
        svg_lines.append('  </g>')

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    @classmethod
    def _generate_ipw_apa_narrative(
        cls,
        sample_size: int,
        n_treated: int,
        n_control: int,
        scheme: str,
        raw_diff: float,
        tau_ipw: float,
        ipw_se: float,
        ipw_p: float,
        tau_dr: float,
        dr_se: float,
        dr_p: float,
        dr_ci_low: float,
        dr_ci_high: float,
        max_weighted_asmd: float,
        all_balanced: bool,
        treatment_label: str,
        outcome_label: str
    ) -> str:
        """Tạo đoạn báo cáo học thuật chuẩn mực theo định dạng APA 7th Edition"""
        p_str = "p < .001" if dr_p < 0.001 else f"p = {dr_p:.3f}"
        sig_str = "có ý nghĩa thống kê ở mức .05" if dr_p < 0.05 else "không đạt mức ý nghĩa thống kê ở mức .05"

        balance_desc = (
            f"Tất cả các biến đồng biến được kiểm định đều đạt độ cân bằng xuất sắc sau khi gán trọng số với "
            f"chênh lệch chuẩn hóa tuyệt đối tối đa ASMD_max = {max_weighted_asmd:.3f} ≤ 0.10 (Austin & Stuart, 2015)."
            if all_balanced else
            f"Mô hình đạt độ cân bằng cải thiện với ASMD_max = {max_weighted_asmd:.3f}."
        )

        narrative = (
            f"Tác động nhân quả của '{treatment_label}' lên biến kết quả '{outcome_label}' được ước lượng "
            f"thông qua phương pháp Trọng số Xác suất Nghịch đảo ({scheme}; Rosenbaum & Rubin, 1983) "
            f"và Ước lượng Vững Kép (Doubly Robust / Augmented IPW; Robins et al., 1994; Bang & Robins, 2005) "
            f"trên tổng mẫu N = {sample_size} (gồm n_can_thiệp = {n_treated} và n_đối_chứng = {n_control}).\n\n"
            f"Trước khi hiệu chỉnh, chênh lệch trung bình thô ghi nhận Δ_thô = {raw_diff:.3f}. "
            f"{balance_desc}\n\n"
            f"Ước lượng Trọng số Nghịch đảo chuẩn hóa (Hajek IPW) ghi nhận tác động nhân quả τ_IPW = {tau_ipw:.3f} "
            f"(SE = {ipw_se:.3f}, p = {ipw_p:.3f}). "
            f"Ước lượng Vững Kép (AIPW) bảo đảm tính vững chắc ngay cả khi mô hình điểm xu hướng hoặc mô hình hồi quy kết quả "
            f"bị sai lệch một phần, mang lại ước lượng tác động thuần túy τ_DR = {tau_dr:.3f} (SE = {dr_se:.3f}, {p_str}, "
            f"95% CI [{dr_ci_low:.3f}, {dr_ci_high:.3f}]), kết luận tác động này {sig_str}."
        )

        return narrative
