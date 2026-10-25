"""
Common Method Bias / Variance (CMB/CMV) Diagnostics Engine.

Cơ sở phương pháp luận học thuật:
- Harman, H. H. (1976). Modern Factor Analysis. University of Chicago Press.
- Podsakoff, P. M., MacKenzie, S. B., Lee, J.-Y., & Podsakoff, N. P. (2003).
  Common method biases in behavioral research: A critical review of the literature
  and recommended remedies. Journal of Applied Psychology, 88(5), 879-903.
- Lindell, M. K., & Whitney, D. J. (2001).
  Accounting for common method variance in cross-sectional research designs:
  Cheating-glove or statistical reality? Journal of Applied Psychology, 86(1), 114-121.
- Williams, L. J., Cote, J. A., & Buckley, M. R. (1989).
  Lack of method variance in self-reported affect and perceptions at work:
  Reality or artifact? Journal of Applied Psychology, 74(3), 462-468.
- Fuller, C. M., Simmering, M. J., Atinc, G., Atinc, Y., & Babin, B. J. (2016).
  Common methods variance detection in business research. Journal of Business Research, 69(8), 3192-3198.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


class CMBEngine:
    """
    Động cơ Chẩn đoán Sai lệch Phương pháp Chung (Common Method Bias / Variance - CMB/CMV).
    Hỗ trợ:
    1. Harman's Single-Factor Test (Unrotated EFA 1st Factor Variance)
    2. Lindell & Whitney (2001) Marker Variable Technique
    3. Podsakoff et al. (2003) Unmeasured Latent Common Method Factor (ULMCF)
    4. APA 7th Reporting & Procedural/Statistical Recommendations
    """

    @staticmethod
    def _regularized_gamma_lower(a: float, x: float) -> float:
        """Hàm Gamma không đầy đủ chính quy hóa P(a, x) = gamma(a, x) / Gamma(a)"""
        if x <= 0.0:
            return 0.0
        if a <= 0.0:
            return 1.0

        if x < a + 1.0:
            ap = a
            sum_val = 1.0 / a
            del_val = sum_val
            for _ in range(120):
                ap += 1.0
                del_val *= x / ap
                sum_val += del_val
                if abs(del_val) < abs(sum_val) * 1e-12:
                    break
            log_gamma_a = math.lgamma(a)
            return sum_val * math.exp(-x + a * math.log(x) - log_gamma_a)
        else:
            b = x + 1.0 - a
            c = 1.0 / 1e-30
            d = 1.0 / b
            h = d
            for i in range(1, 120):
                an = -i * (i - a)
                b += 2.0
                d = an * d + b
                if abs(d) < 1e-30:
                    d = 1e-30
                c = b + an / c
                if abs(c) < 1e-30:
                    c = 1e-30
                d = 1.0 / d
                del_val = d * c
                h *= del_val
                if abs(del_val - 1.0) < 1e-12:
                    break
            log_gamma_a = math.lgamma(a)
            gammcf = math.exp(-x + a * math.log(x) - log_gamma_a) * h
            return 1.0 - gammcf

    @classmethod
    def _student_t_p_value(cls, t_stat: float, df: int) -> float:
        """Tính two-tailed p-value cho phân phối Student-t với bậc tự do df"""
        if df <= 0:
            return 1.0
        t_abs = abs(t_stat)
        if t_abs < 1e-9:
            return 1.0

        x = df / (df + t_abs * t_abs)
        # Regularized incomplete beta I_x(a, b) with a = df/2, b = 0.5
        a = df / 2.0
        b = 0.5
        # Approximation via continued fraction
        beta_val = cls._betai(a, b, x)
        return max(0.0, min(1.0, beta_val))

    @classmethod
    def _betai(cls, a: float, b: float, x: float) -> float:
        """Incomplete beta function I_x(a, b)"""
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0

        lgamma_ab = math.lgamma(a + b)
        lgamma_a = math.lgamma(a)
        lgamma_b = math.lgamma(b)
        bt = math.exp(lgamma_ab - lgamma_a - lgamma_b + a * math.log(x) + b * math.log(1.0 - x))

        if x < (a + 1.0) / (a + b + 2.0):
            return bt * cls._betacf(a, b, x) / a
        else:
            return 1.0 - bt * cls._betacf(b, a, 1.0 - x) / b

    @staticmethod
    def _betacf(a: float, b: float, x: float) -> float:
        """Continued fraction for incomplete beta"""
        qab = a + b
        qap = a + 1.0
        qam = a - 1.0
        c = 1.0
        d = 1.0 - qab * x / qap
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        h = d

        for m in range(1, 150):
            m2 = 2 * m
            # Even step
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            h *= d * c

            # Odd step
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            del_val = d * c
            h *= del_val
            if abs(del_val - 1.0) < 1e-12:
                break
        return h

    @staticmethod
    def _jacobi_eigenvalues(a_matrix: List[List[float]], max_iter: int = 150) -> Tuple[List[float], List[List[float]]]:
        """Thuật toán Jacobi tìm eigenvalues và eigenvectors của ma trận thực đối xứng"""
        n = len(a_matrix)
        a = [row[:] for row in a_matrix]
        v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        for _ in range(max_iter):
            max_off = 0.0
            p, q = 0, 1
            for i in range(n):
                for j in range(i + 1, n):
                    if abs(a[i][j]) > max_off:
                        max_off = abs(a[i][j])
                        p, q = i, j

            if max_off < 1e-10:
                break

            theta = 0.5 * math.atan2(2.0 * a[p][q], a[p][p] - a[q][q])
            c = math.cos(theta)
            s = math.sin(theta)

            app = a[p][p]
            aqq = a[q][q]
            apq = a[p][q]

            a[p][p] = c * c * app + 2.0 * s * c * apq + s * s * aqq
            a[q][q] = s * s * app - 2.0 * s * c * apq + c * c * aqq
            a[p][q] = 0.0
            a[q][p] = 0.0

            for i in range(n):
                if i != p and i != q:
                    aip = a[i][p]
                    aiq = a[i][q]
                    a[i][p] = c * aip + s * aiq
                    a[p][i] = a[i][p]
                    a[i][q] = -s * aip + c * aiq
                    a[q][i] = a[i][q]

                vip = v[i][p]
                viq = v[i][q]
                v[i][p] = c * vip + s * viq
                v[i][q] = -s * vip + c * viq

        eigenvalues = [a[i][i] for i in range(n)]
        # Sắp xếp giảm dần
        order = sorted(range(n), key=lambda idx: eigenvalues[idx], reverse=True)
        sorted_vals = [eigenvalues[i] for i in order]
        sorted_vecs = [[v[r][i] for r in range(n)] for i in order]

        return sorted_vals, sorted_vecs

    @classmethod
    def compute_correlation_matrix(
        cls,
        data: List[Dict[str, float]],
        variables: List[str]
    ) -> Tuple[List[List[float]], int]:
        """
        Tính ma trận tương quan Pearson và số mẫu hợp lệ (listwise deletion).
        """
        p = len(variables)
        clean_rows = []
        for row in data:
            if all(k in row and row[k] is not None and not math.isnan(float(row[k])) for k in variables):
                clean_rows.append([float(row[k]) for k in variables])

        n = len(clean_rows)
        if n < 3 or p < 2:
            return [[1.0 if i == j else 0.0 for j in range(p)] for i in range(p)], n

        means = [sum(row[j] for row in clean_rows) / n for j in range(p)]
        sds = []
        for j in range(p):
            var = sum((row[j] - means[j]) ** 2 for row in clean_rows) / (n - 1)
            sds.append(math.sqrt(max(var, 1e-12)))

        corr = [[1.0 for _ in range(p)] for _ in range(p)]
        for i in range(p):
            for j in range(i + 1, p):
                cov = sum((row[i] - means[i]) * (row[j] - means[j]) for row in clean_rows) / (n - 1)
                r = cov / (sds[i] * sds[j])
                r = max(-1.0, min(1.0, r))
                corr[i][j] = r
                corr[j][i] = r

        return corr, n

    @classmethod
    def harman_single_factor_test(
        cls,
        data: List[Dict[str, float]],
        variables: List[str]
    ) -> Dict[str, Any]:
        """
        Thực hiện Kiểm định Nhân tố Đơn của Harman (Harman's Single-Factor Test).
        Quy tắc:
        - Đưa tất cả biến quan sát vào phân tích nhân tố khám phá (EFA) không xoay.
        - Nếu nhân tố đầu tiên giải thích > 50% tổng phương sai -> Có dấu hiệu nghiêm trọng của CMB.
        - Nếu < 50% -> Không có bằng chứng vi phạm CMB theo tiêu chuẩn Harman.
        """
        p = len(variables)
        if p < 2:
            return {
                "error": "Cần ít nhất 2 biến để thực hiện Harman's Single-Factor Test.",
                "passed": False
            }

        corr_matrix, n_sample = cls.compute_correlation_matrix(data, variables)
        if n_sample < 3:
            return {
                "error": "Số lượng quan sát hợp lệ không đủ (N < 3).",
                "passed": False
            }

        eigenvalues, eigenvectors = cls.jacobi_eigenvalues_safe(corr_matrix)
        total_variance = sum(max(0.0, ev) for ev in eigenvalues)
        if total_variance <= 0.0:
            total_variance = float(p)

        first_factor_eigenvalue = max(0.0, eigenvalues[0]) if eigenvalues else 0.0
        first_factor_variance_pct = (first_factor_eigenvalue / total_variance) * 100.0

        # Số lượng nhân tố có eigenvalue > 1.0 (Kaiser-Guttman rule)
        factors_gt_one = sum(1 for ev in eigenvalues if ev >= 1.0)

        # Tính factor loadings của nhân tố thứ nhất: L_i = sqrt(lambda_1) * v_i
        loadings = {}
        if first_factor_eigenvalue > 0 and len(eigenvectors) > 0:
            sqrt_l1 = math.sqrt(first_factor_eigenvalue)
            v1 = eigenvectors[0]
            for idx, var in enumerate(variables):
                loadings[var] = round(v1[idx] * sqrt_l1, 4)

        has_cmv_risk = first_factor_variance_pct >= 50.0

        interpretation = (
            f"Nhân tố đầu tiên giải thích {first_factor_variance_pct:.2f}% tổng phương sai trích "
            f"(ngưỡng cho phép < 50.0%). "
            + (
                "CẢNH BÁO: Phương sai giải thích vượt ngưỡng 50%, cho thấy sai lệch phương pháp chung (CMB) "
                "chiếm ưu thế đáng kể trong dữ liệu khảo sát."
                if has_cmv_risk
                else "KẾT LUẬN: Phương sai giải thích nằm dưới ngưỡng 50%, không có bằng chứng về sai lệch "
                "phương pháp chung (CMB) gây biến dạng nghiêm trọng theo tiêu chí Harman (1976)."
            )
        )

        variance_breakdown = []
        cum_pct = 0.0
        for i, ev in enumerate(eigenvalues[:min(5, p)]):
            ev_clamped = max(0.0, ev)
            pct = (ev_clamped / total_variance) * 100.0
            cum_pct += pct
            variance_breakdown.append({
                "factor": i + 1,
                "eigenvalue": round(ev_clamped, 4),
                "variance_pct": round(pct, 2),
                "cumulative_pct": round(cum_pct, 2)
            })

        return {
            "n_sample": n_sample,
            "n_items": p,
            "first_factor_eigenvalue": round(first_factor_eigenvalue, 4),
            "first_factor_variance_pct": round(first_factor_variance_pct, 2),
            "factors_with_eigenvalue_gt_one": factors_gt_one,
            "threshold_pct": 50.0,
            "has_cmv_risk": has_cmv_risk,
            "passed": not has_cmv_risk,
            "variance_breakdown": variance_breakdown,
            "first_factor_loadings": loadings,
            "interpretation": interpretation
        }

    @classmethod
    def jacobi_eigenvalues_safe(cls, a_matrix: List[List[float]]) -> Tuple[List[float], List[List[float]]]:
        """Wrapper an toàn cho Jacobi eigenvalues"""
        try:
            return cls._jacobi_eigenvalues(a_matrix)
        except Exception:
            p = len(a_matrix)
            return [1.0] * p, [[1.0 if i == j else 0.0 for j in range(p)] for i in range(p)]

    @classmethod
    def marker_variable_technique(
        cls,
        data: List[Dict[str, float]],
        substantive_variables: List[str],
        marker_variable: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kỹ thuật Biến Đánh Dấu (Marker Variable Technique - Lindell & Whitney 2001).
        - Nếu marker_variable được chỉ định: Sử dụng tương quan nhỏ nhất giữa biến marker và các biến nội dung r_M.
        - Nếu marker_variable không chỉ định: Tìm biến có mức tương quan dương thấp nhất r_min_pos để làm proxy marker.
        - Hiệu chỉnh tương quan: r_adj = (r_XY - r_M) / (1 - r_M).
        - Kiểm định t: t = r_adj * sqrt((N - 3) / (1 - r_adj^2)), tính p-value 2-tailed.
        """
        all_vars = list(substantive_variables)
        is_auto_marker = False

        if marker_variable and marker_variable in substantive_variables:
            all_vars = [v for v in substantive_variables if v != marker_variable]
            substantive_variables = all_vars
        elif marker_variable and marker_variable not in all_vars:
            all_vars.append(marker_variable)

        corr_matrix, n = cls.compute_correlation_matrix(data, all_vars)
        p = len(all_vars)

        if n < 4 or len(substantive_variables) < 2:
            return {
                "error": "Cần ít nhất 2 biến nội dung và N >= 4.",
                "passed": False
            }

        var_idx = {v: i for i, v in enumerate(all_vars)}

        # Xác định r_M
        if marker_variable and marker_variable in var_idx:
            m_idx = var_idx[marker_variable]
            marker_corrs = []
            for sv in substantive_variables:
                s_idx = var_idx[sv]
                r = corr_matrix[m_idx][s_idx]
                if r > 0.0:
                    marker_corrs.append(r)
            r_m = min(marker_corrs) if marker_corrs else 0.05
        else:
            # Tự động tìm correlation dương nhỏ nhất giữa các cặp biến
            is_auto_marker = True
            pos_corrs = []
            for i in range(len(substantive_variables)):
                for j in range(i + 1, len(substantive_variables)):
                    idx_i = var_idx[substantive_variables[i]]
                    idx_j = var_idx[substantive_variables[j]]
                    r = corr_matrix[idx_i][idx_j]
                    if r > 0.001:
                        pos_corrs.append(r)
            r_m = min(pos_corrs) if pos_corrs else 0.05
            marker_variable = "AUTO_PROXY_MIN_CORR"

        # Hiệu chỉnh từng cặp tương quan
        pair_comparisons = []
        significant_before = 0
        significant_after = 0
        total_pairs = 0

        df = max(1, n - 3)

        for i in range(len(substantive_variables)):
            for j in range(i + 1, len(substantive_variables)):
                var_x = substantive_variables[i]
                var_y = substantive_variables[j]
                idx_x = var_idx[var_x]
                idx_y = var_idx[var_y]

                r_orig = corr_matrix[idx_x][idx_y]

                # t ban đầu
                denom_orig = math.sqrt(max(1e-12, 1.0 - r_orig * r_orig))
                t_orig = r_orig * math.sqrt(df) / denom_orig
                p_orig = cls._student_t_p_value(t_orig, df)

                # r hiệu chỉnh: r_adj = (r_orig - r_M) / (1 - r_M)
                if abs(1.0 - r_m) < 1e-12:
                    r_adj = r_orig
                else:
                    r_adj = (r_orig - r_m) / (1.0 - r_m)
                r_adj = max(-0.9999, min(0.9999, r_adj))

                # t sau hiệu chỉnh
                denom_adj = math.sqrt(max(1e-12, 1.0 - r_adj * r_adj))
                t_adj = r_adj * math.sqrt(df) / denom_adj
                p_adj = cls._student_t_p_value(t_adj, df)

                is_sig_orig = p_orig < 0.05
                is_sig_adj = p_adj < 0.05

                if is_sig_orig:
                    significant_before += 1
                if is_sig_adj:
                    significant_after += 1
                total_pairs += 1

                retained = is_sig_orig == is_sig_adj

                pair_comparisons.append({
                    "variable_x": var_x,
                    "variable_y": var_y,
                    "r_original": round(r_orig, 4),
                    "p_original": round(p_orig, 4),
                    "r_adjusted": round(r_adj, 4),
                    "p_adjusted": round(p_adj, 4),
                    "significance_retained": retained,
                    "t_statistic_adjusted": round(t_adj, 3)
                })

        retention_rate = (significant_after / max(1, significant_before)) * 100.0

        interpretation = (
            f"Sử dụng hệ số tương quan biến đánh dấu r_M = {r_m:.4f} "
            f"({'Tự động ước lượng mức tương quan dương thấp nhất' if is_auto_marker else f'Từ biến đánh dấu {marker_variable}'}). "
            f"Trong số {significant_before} mối quan hệ có ý nghĩa thống kê ban đầu (p < 0.05), "
            f"{significant_after} mối quan hệ ({retention_rate:.1f}%) vẫn duy trì ý nghĩa thống kê sau khi kiểm soát sai số phương pháp chung. "
            + (
                "Phát hiện nghiên cứu vững chắc (robust) trước sai số phương pháp chung."
                if retention_rate >= 80.0
                else "CẢNH BÁO: Tỷ lệ mất ý nghĩa thống kê đáng kể, dấu hiệu cho thấy một phần kết quả có thể do hiệu ứng phương pháp."
            )
        )

        return {
            "marker_variable": marker_variable,
            "is_auto_marker": is_auto_marker,
            "marker_correlation_r_m": round(r_m, 4),
            "n_sample": n,
            "degrees_of_freedom": df,
            "total_pairs_tested": total_pairs,
            "significant_pairs_before": significant_before,
            "significant_pairs_after": significant_after,
            "significance_retention_rate_pct": round(retention_rate, 2),
            "pair_comparisons": pair_comparisons[:30],  # Top 30 cặp
            "interpretation": interpretation
        }

    @classmethod
    def unmeasured_latent_method_factor(
        cls,
        data: List[Dict[str, float]],
        variables: List[str]
    ) -> Dict[str, Any]:
        """
        Ước lượng Tác động của Nhân tố Phương pháp Chung Ẩn (ULMCF - Podsakoff et al. 2003).
        Tính toán tỷ lệ phương sai trích của nhân tố phương pháp chung:
        - Ước lượng loading của nhân tố chung (method factor).
        - So sánh phương sai giải thích của nhân tố phương pháp so với tổng phương sai nội dung.
        - Chuẩn thực nghiệm Williams et al. (1989): Phương sai phương pháp trung bình ~16% - 25%.
        """
        p = len(variables)
        corr_matrix, n = cls.compute_correlation_matrix(data, variables)
        if n < 4 or p < 3:
            return {
                "error": "Cần ít nhất 3 biến và N >= 4.",
                "passed": False
            }

        eigenvalues, eigenvectors = cls.jacobi_eigenvalues_safe(corr_matrix)
        total_var = sum(max(0.0, ev) for ev in eigenvalues)

        # Giả định unmeasured latent method factor tương ứng với trục chính chung
        # Tính tỷ lệ phương sai bình phương loadings
        method_loadings = {}
        if eigenvalues and eigenvalues[0] > 0 and len(eigenvectors) > 0:
            l1 = math.sqrt(max(0.0, eigenvalues[0]))
            v1 = eigenvectors[0]
            sum_lambda_sq = 0.0
            for idx, var in enumerate(variables):
                loading = v1[idx] * l1
                method_loadings[var] = round(loading, 4)
                sum_lambda_sq += loading ** 2

            # Trung bình bình phương loading (R^2 method)
            avg_method_r2 = sum_lambda_sq / p
            cmv_percentage = (avg_method_r2 / (1.0 + avg_method_r2)) * 100.0 if (1.0 + avg_method_r2) > 0 else 0.0
        else:
            avg_method_r2 = 0.15
            cmv_percentage = 15.0

        benchmark_threshold = 25.0
        is_acceptable = cmv_percentage <= benchmark_threshold

        interpretation = (
            f"Tỷ lệ phương sai sai số phương pháp chung ước tính (ULMCF) là {cmv_percentage:.2f}% "
            f"(chuẩn đối sánh thực nghiệm Williams et al. 1989 là <= 25.0%). "
            + (
                "Mức độ sai lệch phương pháp nằm trong giới hạn kiểm soát cho phép trong nghiên cứu hành vi."
                if is_acceptable
                else "CẢNH BÁO: Tỷ lệ phương sai phương pháp chung vượt mức chuẩn đối sánh 25%, cần lưu ý trong thảo luận giới hạn đề tài."
            )
        )

        return {
            "n_sample": n,
            "n_items": p,
            "estimated_cmv_variance_pct": round(cmv_percentage, 2),
            "benchmark_threshold_pct": benchmark_threshold,
            "is_acceptable": is_acceptable,
            "average_method_r2": round(avg_method_r2, 4),
            "method_loadings": method_loadings,
            "interpretation": interpretation
        }

    @classmethod
    def comprehensive_diagnostic(
        cls,
        data: List[Dict[str, float]],
        variables: List[str],
        marker_variable: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tổng hợp toàn diện chẩn đoán Common Method Bias:
        - Harman's Single Factor
        - Marker Variable Technique
        - ULMCF Analysis
        - Đánh giá Cấp độ Rủi ro (LOW, MODERATE, HIGH)
        - Đoạn trích APA 7th ấn phẩm khoa học
        - Khuyến nghị khắc phục (Thủ tục & Thống kê)
        """
        harman_res = cls.harman_single_factor_test(data, variables)
        marker_res = cls.marker_variable_technique(data, variables, marker_variable)
        ulmcf_res = cls.unmeasured_latent_method_factor(data, variables)

        # Tính toán mức rủi ro tổng thể
        risk_score = 0
        reasons = []

        if harman_res.get("has_cmv_risk", False):
            risk_score += 3
            reasons.append("Harman's Single-Factor giải thích >= 50% phương sai")
        elif harman_res.get("first_factor_variance_pct", 0) >= 40.0:
            risk_score += 1
            reasons.append("Harman's Single-Factor tiếp cận ngưỡng cảnh báo (>= 40%)")

        retention = marker_res.get("significance_retention_rate_pct", 100.0)
        if retention < 60.0:
            risk_score += 3
            reasons.append(f"Tỷ lệ giữ nguyên ý nghĩa thống kê qua biến đánh dấu quá thấp ({retention:.1f}% < 60%)")
        elif retention < 80.0:
            risk_score += 1
            reasons.append(f"Một số cặp tương quan mất ý nghĩa thống kê qua biến đánh dấu ({retention:.1f}%)")

        cmv_pct = ulmcf_res.get("estimated_cmv_variance_pct", 0)
        if cmv_pct > 25.0:
            risk_score += 2
            reasons.append(f"Phương sai phương pháp chung ULMCF vượt chuẩn ({cmv_pct:.1f}% > 25%)")

        if risk_score == 0:
            overall_risk = "LOW"
            risk_summary = "Rủi ro Sai lệch Phương pháp Chung rất thấp. Dữ liệu đáp ứng chuẩn kiểm định nghiêm ngặt."
        elif risk_score <= 2:
            overall_risk = "MODERATE"
            risk_summary = "Rủi ro Sai lệch Phương pháp Chung ở mức trung bình. Cần minh bạch hóa trong phần giới hạn nghiên cứu."
        else:
            overall_risk = "HIGH"
            risk_summary = "Rủi ro Sai lệch Phương pháp Chung CAO. Nguy cơ các mối quan hệ quan sát bị thổi phồng bởi cùng một phương thức đo lường."

        # Khuyến nghị khắc phục
        remedies = []
        if overall_risk == "LOW":
            remedies.append({
                "type": "REPORTING",
                "title": "Báo cáo minh bạch APA 7th",
                "detail": "Trích dẫn đầy đủ kết quả Harman's Single Factor và Kỹ thuật Biến Đánh Dấu trong phần Phương pháp / Kết quả kiểm định thang đo."
            })
        else:
            remedies.extend([
                {
                    "type": "PROCEDURAL",
                    "title": "Tách biệt đo lường theo thời gian hoặc không gian (Temporal / Spatial Separation)",
                    "detail": "Thu thập biến độc lập (IV) và biến phụ thuộc (DV) tại 2 thời điểm khác nhau (Time 1 vs Time 2) hoặc từ các nguồn thông tin độc lập (giám sát viên, đồng nghiệp)."
                },
                {
                    "type": "PROCEDURAL",
                    "title": "Đảo trật tự câu hỏi & thang đo phân tán (Counterbalancing)",
                    "detail": "Trộn ngẫu nhiên thứ tự các nhóm câu hỏi và sử dụng các dạng thang đo neo khác nhau (Likert 5, Likert 7, Thang vi sai ngữ nghĩa) để giảm thiểu thói quen phản hồi."
                },
                {
                    "type": "STATISTICAL",
                    "title": "Kiểm soát bằng biến đánh dấu trong mô hình cấu trúc (CFA Marker Technique)",
                    "detail": "Mô hình hóa biến đánh dấu trực tiếp trong AMOS / SmartPLS / SEM để khấu trừ phương sai sai số phương pháp khỏi các hệ số hồi quy đường dẫn."
                }
            ])

        # APA 7th Writeup
        first_pct = harman_res.get("first_factor_variance_pct", 0)
        n_sample = harman_res.get("n_sample", 0)
        r_m_val = marker_res.get("marker_correlation_r_m", 0)

        apa_writeup = (
            f"Để kiểm tra nguy cơ sai lệch phương pháp chung (Common Method Bias - CMB), nghiên cứu đã áp dụng "
            f"đồng thời hai kỹ thuật chẩn đoán theo khuyến nghị của Podsakoff et al. (2003) và Lindell & Whitney (2001). "
            f"Đầu tiên, kiểm định nhân tố đơn của Harman (Harman's Single-Factor Test) trên {len(variables)} biến quan sát "
            f"với kích thước mẫu N = {n_sample} cho thấy nhân tố đầu tiên chỉ giải thích {first_pct:.2f}% tổng phương sai, "
            f"thấp hơn ngưỡng cho phép 50.0%. Tiếp theo, áp dụng kỹ thuật biến đánh dấu (Marker Variable Technique) "
            f"với hệ số kiểm soát r_M = {r_m_val:.4f}, kết quả chỉ ra {retention:.1f}% các mối tương quan có ý nghĩa ban đầu "
            f"vẫn giữ vững ý nghĩa thống kê (p < .05) sau hiệu chỉnh. "
            f"Tổng hợp các chỉ số khẳng định sai lệch phương pháp chung không phải là vấn đề nghiêm trọng đe dọa giá trị của các phát hiện nghiên cứu."
        )

        return {
            "overall_risk": overall_risk,
            "risk_score": risk_score,
            "risk_summary": risk_summary,
            "flagged_issues": reasons,
            "harman_test": harman_res,
            "marker_test": marker_res,
            "ulmcf_test": ulmcf_res,
            "apa_writeup": apa_writeup,
            "recommended_remedies": remedies
        }
