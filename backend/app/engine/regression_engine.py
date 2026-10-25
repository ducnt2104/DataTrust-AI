import math
from typing import Dict, Any, List, Optional, Tuple

class RegressionEngine:
    """
    Động cơ Hồi quy Tuyến tính Đa biến (Multiple Linear Regression OLS)
    kết hợp Chẩn đoán Đa cộng tuyến VIF & Tolerance, Hệ số Chuẩn hóa Beta,
    Kiểm định Omnibus F-test, và Báo cáo Diễn giải APA 7th Edition.

    Cơ sở phương pháp luận học thuật:
    - Legendre, A. M. (1805). Nouvelles méthodes pour la détermination des orbites des comètes (OLS).
    - Gauss, C. F. (1809). Theoria motus corporum coelestium.
    - Hair, J. F., Black, W. C., Babin, B. J., & Anderson, R. E. (2010). Multivariate Data Analysis.
    - Kline, R. B. (2015). Principles and Practice of Structural Equation Modeling.
    - Cohen, J., Cohen, P., West, S. G., & Aiken, L. S. (2003). Applied Multiple Regression/Correlation Analysis.
    """

    @staticmethod
    def _betainc(a: float, b: float, x: float) -> float:
        """Hàm Beta không đầy đủ chính quy hóa I_x(a, b) dùng liên phân số Lentz"""
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0

        if x > (a + 1.0) / (a + b + 2.0):
            return 1.0 - RegressionEngine._betainc(b, a, 1.0 - x)

        log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - log_beta) / a

        tiny = 1e-30
        c = 1.0
        d = 1.0 - (a + b) * x / (a + 1.0)
        if abs(d) < tiny:
            d = tiny
        d = 1.0 / d
        f = d

        for m in range(1, 100):
            m2 = 2 * m
            num_even = (m * (b - m) * x) / ((a + m2 - 1.0) * (a + m2))
            d = 1.0 + num_even * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num_even / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            f *= (d * c)

            num_odd = -((a + m) * (a + b + m) * x) / ((a + m2) * (a + m2 + 1.0))
            d = 1.0 + num_odd * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num_odd / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            del_val = d * c
            f *= del_val

            if abs(del_val - 1.0) < 1e-12:
                break

        return max(0.0, min(1.0, front * f))

    @classmethod
    def _f_p_value(cls, f_stat: float, df1: float, df2: float) -> float:
        """Tính p-value P(F >= f) cho phân phối Fisher-Snedecor F"""
        if f_stat <= 0.0 or df1 <= 0.0 or df2 <= 0.0:
            return 1.0
        x = df2 / (df2 + df1 * f_stat)
        p = cls._betainc(df2 / 2.0, df1 / 2.0, x)
        return max(0.0, min(1.0, p))

    @classmethod
    def _t_p_value_2tailed(cls, t_stat: float, df: float) -> float:
        """Tính p-value 2 phía cho phân phối Student's t"""
        if df <= 0:
            return 1.0
        t_abs = abs(t_stat)
        if t_abs < 1e-12:
            return 1.0
        x = df / (df + t_abs * t_abs)
        p = cls._betainc(df / 2.0, 0.5, x)
        return max(0.0, min(1.0, p))

    @staticmethod
    def _invert_matrix(A: List[List[float]], ridge: float = 1e-7) -> Optional[List[List[float]]]:
        """Đảo ma trận vuông thực bằng phép khử Gauss-Jordan kèm partial pivoting và ridge stabilization"""
        n = len(A)
        # Thêm ridge vào đường chéo để chống ma trận suy biến / kỳ dị
        M = [[A[i][j] + (ridge if i == j else 0.0) for j in range(n)] for i in range(n)]
        inv = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        for col in range(n):
            max_row = col
            max_val = abs(M[col][col])
            for r in range(col + 1, n):
                if abs(M[r][col]) > max_val:
                    max_val = abs(M[r][col])
                    max_row = r

            if max_val < 1e-12:
                return None

            M[col], M[max_row] = M[max_row], M[col]
            inv[col], inv[max_row] = inv[max_row], inv[col]

            pivot = M[col][col]
            for c in range(n):
                M[col][c] /= pivot
                inv[col][c] /= pivot

            for r in range(n):
                if r != col:
                    factor = M[r][col]
                    for c in range(n):
                        M[r][c] -= factor * M[col][c]
                        inv[r][c] -= factor * inv[col][c]

        return inv

    @classmethod
    def fit_ols(
        cls,
        X_matrix: List[List[float]],
        y_vector: List[float],
        predictor_labels: List[str],
        predictor_titles: List[str],
        dependent_title: str
    ) -> Dict[str, Any]:
        """
        Khớp mô hình hồi quy đa biến OLS: y = beta_0 + beta_1*X_1 + ... + beta_p*X_p
        X_matrix: N hàng, p cột (chưa bao gồm cột 1 cho hằng số beta_0)
        """
        N = len(y_vector)
        p = len(predictor_labels)

        if N <= p + 1:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu N >= {p + 2} quan sát để ước lượng mô hình hồi quy với {p} biến độc lập (hiện có N = {N})."
            }

        # 1. Thêm cột hằng số 1.0 vào ma trận thiết kế X_design (N x (p + 1))
        p_plus_1 = p + 1
        X_design = [[1.0] + list(X_matrix[i]) for i in range(N)]

        # 2. Tính X^T * X ((p+1) x (p+1)) và X^T * y ((p+1) x 1)
        XtX = [[0.0] * p_plus_1 for _ in range(p_plus_1)]
        Xty = [0.0] * p_plus_1

        for i in range(p_plus_1):
            for j in range(p_plus_1):
                s = sum(X_design[row][i] * X_design[row][j] for row in range(N))
                XtX[i][j] = s
            Xty[i] = sum(X_design[row][i] * y_vector[row] for row in range(N))

        # 3. Đảo ma trận (X^T * X)^(-1)
        inv_XtX = cls._invert_matrix(XtX)
        if inv_XtX is None:
            return {
                "status": "SINGULAR_MATRIX",
                "message": "Ma trận quan sát bị suy biến hoàn toàn (hoàn hảo cộng tuyến). Hãy loại bỏ bớt biến độc lập bị trùng lặp."
            }

        # 4. Ước lượng vector hệ số beta = (X^T * X)^(-1) * X^T * y
        beta = [0.0] * p_plus_1
        for i in range(p_plus_1):
            beta[i] = sum(inv_XtX[i][j] * Xty[j] for j in range(p_plus_1))

        # 5. Giá trị dự báo y_pred và phần dư residuals
        y_pred = []
        residuals = []
        for row in range(N):
            pred = sum(X_design[row][j] * beta[j] for j in range(p_plus_1))
            y_pred.append(pred)
            residuals.append(y_vector[row] - pred)

        mean_y = sum(y_vector) / N
        ss_tot = sum((y - mean_y)**2 for y in y_vector)
        ss_res = sum(r**2 for r in residuals)
        ss_reg = max(0.0, ss_tot - ss_res)

        df_reg = p
        df_res = N - p - 1
        df_tot = N - 1

        ms_reg = ss_reg / df_reg if df_reg > 0 else 0.0
        ms_res = ss_res / df_res if df_res > 0 else 0.0

        # Hệ số xác định R^2 và R^2 hiệu chỉnh
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
        r_squared = max(0.0, min(1.0, r_squared))
        r_squared_adj = 1.0 - (1.0 - r_squared) * (float(df_tot) / float(df_res)) if df_res > 0 else 0.0
        r_squared_adj = max(0.0, min(1.0, r_squared_adj))

        # Thống kê Omnibus F và p-value
        if ss_tot <= 1e-12:
            f_stat = 0.0
            p_val_model = 1.0
        elif ms_res <= 1e-12:
            f_stat = 999999.0
            p_val_model = 0.0
        else:
            f_stat = ms_reg / ms_res
            p_val_model = cls._f_p_value(f_stat, float(df_reg), float(df_res))

        std_err_est = math.sqrt(ms_res)

        # 6. Tính sai số chuẩn, thống kê t, p-value, và 95% CI cho từng hệ số
        # Độ lệch chuẩn của Y và từng biến X để tính hệ số chuẩn hóa Beta
        std_y = math.sqrt(ss_tot / df_tot) if df_tot > 0 else 1.0
        std_x = []
        for j in range(p):
            col_vals = [X_matrix[i][j] for i in range(N)]
            m_col = sum(col_vals) / N
            s_col = math.sqrt(sum((v - m_col)**2 for v in col_vals) / df_tot) if df_tot > 0 else 1.0
            std_x.append(s_col)

        # 7. Tính Variance Inflation Factor (VIF) cho từng biến độc lập X_j
        # VIF_j = 1 / (1 - R_j^2) từ hồi quy X_j theo các biến độc lập còn lại
        vif_list = []
        tolerance_list = []
        for j in range(p):
            if p == 1:
                vif_list.append(1.0)
                tolerance_list.append(1.0)
                continue

            # X_other là tất cả các cột trừ cột j
            X_other = []
            y_j = []
            for r in range(N):
                X_other.append([X_matrix[r][k] for k in range(p) if k != j])
                y_j.append(X_matrix[r][j])

            # Chạy hồi quy phụ để tính R_j^2
            sub_res = cls.fit_ols(
                X_matrix=X_other,
                y_vector=y_j,
                predictor_labels=[f"P_{k}" for k in range(p - 1)],
                predictor_titles=[f"Predictor_{k}" for k in range(p - 1)],
                dependent_title="Sub"
            )
            r2_j = sub_res.get("model_summary", {}).get("r_squared", 0.0)
            tol = max(1e-4, 1.0 - r2_j)
            vif = 1.0 / tol
            vif_list.append(round(vif, 2))
            tolerance_list.append(round(tol, 3))

        # 8. Lập bảng hệ số hồi quy (Coefficients Table)
        coefficients = []
        # Hệ số hằng số (Intercept / Constant)
        se_const = math.sqrt(max(0.0, ms_res * inv_XtX[0][0]))
        if se_const < 1e-12:
            t_const = 999999.0 if abs(beta[0]) > 1e-12 else 0.0
            p_const = 0.0 if abs(beta[0]) > 1e-12 else 1.0
        else:
            t_const = beta[0] / se_const
            p_const = cls._t_p_value_2tailed(t_const, float(df_res))
        margin_const = 1.96 * se_const

        coefficients.append({
            "term": "(Hằng số / Intercept)",
            "label": "CONST",
            "title": "Hệ số chặn mô hình",
            "b_unstandardized": round(beta[0], 3),
            "std_error": round(se_const, 3),
            "beta_standardized": 0.0,
            "t_stat": round(t_const, 3),
            "p_value": round(p_const, 4),
            "is_significant_05": p_const < 0.05,
            "is_significant_01": p_const < 0.01,
            "ci_95_lower": round(beta[0] - margin_const, 3),
            "ci_95_upper": round(beta[0] + margin_const, 3),
            "tolerance": 1.0,
            "vif": 1.0
        })

        sig_predictors = []
        for j in range(p):
            b_val = beta[j + 1]
            idx_in_inv = j + 1
            se_b = math.sqrt(max(0.0, ms_res * inv_XtX[idx_in_inv][idx_in_inv]))
            if se_b < 1e-12:
                t_b = 999999.0 if abs(b_val) > 1e-12 else 0.0
                p_b = 0.0 if abs(b_val) > 1e-12 else 1.0
            else:
                t_b = b_val / se_b
                p_b = cls._t_p_value_2tailed(t_b, float(df_res))

            # Hệ số chuẩn hóa beta_std = B * (SD_X / SD_Y)
            beta_std = b_val * (std_x[j] / std_y) if std_y > 1e-12 else 0.0
            margin_b = 1.96 * se_b

            is_sig = p_b < 0.05
            if is_sig:
                sig_predictors.append({
                    "title": predictor_titles[j],
                    "beta": beta_std,
                    "b": b_val,
                    "p": p_b
                })

            coefficients.append({
                "term": predictor_titles[j],
                "label": predictor_labels[j],
                "title": predictor_titles[j],
                "b_unstandardized": round(b_val, 3),
                "std_error": round(se_b, 3),
                "beta_standardized": round(beta_std, 3),
                "t_stat": round(t_b, 3),
                "p_value": round(p_b, 4),
                "is_significant_05": is_sig,
                "is_significant_01": p_b < 0.01,
                "ci_95_lower": round(b_val - margin_b, 3),
                "ci_95_upper": round(b_val + margin_b, 3),
                "tolerance": tolerance_list[j],
                "vif": vif_list[j]
            })

        # 9. Diễn giải học thuật APA 7th Edition
        p_model_str = "< .001" if p_val_model < 0.001 else f"= {p_val_model:.3f}"
        sig_model_text = "có ý nghĩa thống kê" if p_val_model < 0.05 else "không đạt ý nghĩa thống kê"

        if sig_predictors:
            # Sắp xếp các biến có ý nghĩa theo độ lớn beta chuẩn hóa
            sig_predictors.sort(key=lambda x: abs(x["beta"]), reverse=True)
            pred_descriptions = []
            for pred in sig_predictors:
                p_desc = "< .001" if pred["p"] < 0.001 else f"= {pred['p']:.3f}"
                pred_descriptions.append(f"'{pred['title']}' (β = {pred['beta']:.2f}, p {p_desc})")
            top_preds_desc = ", ".join(pred_descriptions)
            pred_text = f"Trong đó, các biến có đóng góp giải thích độc lập có ý nghĩa bao gồm: {top_preds_desc}."
        else:
            pred_text = "Không có biến độc lập nào đạt ý nghĩa thống kê ở mức alpha = .05."

        max_vif = max(vif_list) if vif_list else 1.0
        if max_vif >= 10.0:
            collin_text = f"Lưu ý: Mô hình vi phạm nghiêm trọng hiện tượng đa cộng tuyến (VIF max = {max_vif:.1f} >= 10.0), cần rà soát lại các biến độc lập."
        elif max_vif >= 5.0:
            collin_text = f"Chẩn đoán đa cộng tuyến ghi nhận mức độ vừa phải (VIF max = {max_vif:.1f} >= 5.0)."
        else:
            collin_text = f"Chẩn đoán đa cộng tuyến hoàn toàn đạt yêu cầu (tất cả VIF < {max_vif:.1f} <= 5.0, Tolerance > 0.20)."

        apa_narrative = (
            f"Mô hình hồi quy tuyến tính đa biến OLS được thực hiện nhằm dự báo '{dependent_title}' "
            f"từ {p} biến độc lập (Cỡ mẫu N = {N}). Kết quả phân tích phương sai tổng quát cho thấy mô hình là {sig_model_text}, "
            f"F({df_reg}, {df_res}) = {f_stat:.2f}, p {p_model_str}, "
            f"giải thích được R² = {r_squared:.3f} (R² hiệu chỉnh = {r_squared_adj:.3f}) phương sai của biến phụ thuộc. "
            f"{pred_text} "
            f"{collin_text}"
        )

        return {
            "status": "SUCCESS",
            "sample_size": N,
            "predictors_count": p,
            "dependent_title": dependent_title,
            "model_summary": {
                "r_squared": round(r_squared, 4),
                "r_squared_adjusted": round(r_squared_adj, 4),
                "std_error_of_estimate": round(std_err_est, 3),
                "f_stat": round(f_stat, 3),
                "df_regression": df_reg,
                "df_residual": df_res,
                "df_total": df_tot,
                "p_value": round(p_val_model, 6),
                "is_significant_05": p_val_model < 0.05,
                "is_significant_01": p_val_model < 0.01
            },
            "anova_table": {
                "ss_regression": round(ss_reg, 3),
                "df_regression": df_reg,
                "ms_regression": round(ms_reg, 3),
                "ss_residual": round(ss_res, 3),
                "df_residual": df_res,
                "ms_residual": round(ms_res, 3),
                "ss_total": round(ss_tot, 3),
                "df_total": df_tot,
                "f_stat": round(f_stat, 3),
                "p_value": round(p_val_model, 6)
            },
            "coefficients": coefficients,
            "max_vif": round(max_vif, 2),
            "multicollinearity_risk": "HIGH" if max_vif >= 10.0 else ("MODERATE" if max_vif >= 5.0 else "LOW"),
            "apa_interpretation": apa_narrative
        }
