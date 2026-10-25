import math
from typing import Dict, Any, List, Optional, Tuple

class TTestEngine:
    """
    Động cơ Kiểm định Giả thuyết Thống kê T-Test (Student's, Welch's & Paired T-Tests)
    và Ước lượng Kích thước Hiệu ứng (Cohen's d, Hedges' g) theo chuẩn APA 7th Edition.

    Cơ sở phương pháp luận:
    - Student (1908). The probable error of a mean. Biometrika.
    - Welch, B. L. (1947). The generalization of 'Student's' problem when several
      different population variances are involved. Biometrika.
    - Levene, H. (1960). Robust tests for equality of variances. Contributions to
      Probability and Statistics.
    - Brown, M. B., & Forsythe, A. B. (1974). Robust tests for the equality of
      variances. JASA.
    - Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences.
    - Hedges, L. V. (1981). Distribution theory for Glass's estimator of effect size.
    """

    @staticmethod
    def _betainc(a: float, b: float, x: float) -> float:
        """
        Hàm Beta không đầy đủ chính quy hóa I_x(a, b) dùng thuật toán liên phân số (Continued Fraction).
        Tính chính xác CDF của phân phối Student's t và phân phối Snedecor's F.
        """
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0

        # Khai triển hệ số đối xứng nếu x > (a + 1) / (a + b + 2)
        if x > (a + 1.0) / (a + b + 2.0):
            return 1.0 - TTestEngine._betainc(b, a, 1.0 - x)

        log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - log_beta) / a

        # Khai triển liên phân số Lentz's method
        tiny = 1e-30
        c = 1.0
        d = 1.0 - (a + b) * x / (a + 1.0)
        if abs(d) < tiny:
            d = tiny
        d = 1.0 / d
        f = d

        for m in range(1, 100):
            m2 = 2 * m
            # Chẵn
            num_even = (m * (b - m) * x) / ((a + m2 - 1.0) * (a + m2))
            d = 1.0 + num_even * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num_even / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            f *= (d * c)

            # Lẻ
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
    def _t_p_value(cls, t_stat: float, df: float) -> float:
        """Tính 2-tailed p-value cho phân phối Student's t với bậc tự do df"""
        if df <= 0.0:
            return 1.0
        t2 = t_stat * t_stat
        x = df / (df + t2)
        # 2-tailed p = I_x(df/2, 1/2)
        p = cls._betainc(df / 2.0, 0.5, x)
        return max(0.0, min(1.0, p))

    @classmethod
    def _f_p_value(cls, f_stat: float, df1: float, df2: float) -> float:
        """Tính p-value P(F >= f) cho phân phối Fisher-Snedecor F"""
        if f_stat <= 0.0 or df1 <= 0.0 or df2 <= 0.0:
            return 1.0
        x = df2 / (df2 + df1 * f_stat)
        p = cls._betainc(df2 / 2.0, df1 / 2.0, x)
        return max(0.0, min(1.0, p))

    @staticmethod
    def _t_critical_95(df: float) -> float:
        """Ước lượng giá trị t tới hạn ở mức ý nghĩa alpha = 0.05 (2-tailed)"""
        if df >= 120.0:
            return 1.960
        if df <= 1.0:
            return 12.706
        # Xấp xỉ theo công thức Hill (1970) cho phân vị Student's t
        a = 1.959963984540054
        return a + (a**3 + a) / (4.0 * df) + (5.0 * a**5 + 16.0 * a**3 + 3.0 * a) / (96.0 * df**2)

    @staticmethod
    def _compute_basic_stats(values: List[float]) -> Dict[str, float]:
        """Tính các chỉ số thống kê mô tả cơ bản: N, Mean, Variance, StdDev, Skewness, Kurtosis"""
        n = len(values)
        if n == 0:
            return {"n": 0, "mean": 0.0, "var": 0.0, "sd": 0.0, "se": 0.0, "median": 0.0, "skew": 0.0, "kurt": 0.0}

        mean_val = sum(values) / n
        sorted_vals = sorted(values)
        median_val = sorted_vals[n // 2] if n % 2 != 0 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

        if n < 2:
            return {"n": n, "mean": round(mean_val, 3), "var": 0.0, "sd": 0.0, "se": 0.0, "median": round(median_val, 3), "skew": 0.0, "kurt": 0.0}

        var_val = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        sd_val = math.sqrt(var_val)
        se_val = sd_val / math.sqrt(n)

        # Tính độ bất đối xứng Skewness và độ nhọn Kurtosis
        skew_val = 0.0
        kurt_val = 0.0
        if sd_val > 1e-9 and n >= 3:
            m3 = sum((x - mean_val) ** 3 for x in values) / n
            m2 = sum((x - mean_val) ** 2 for x in values) / n
            skew_val = m3 / (m2 ** 1.5) if m2 > 0 else 0.0

            if n >= 4:
                m4 = sum((x - mean_val) ** 4 for x in values) / n
                # Excess Kurtosis (so với phân phối chuẩn = 0)
                kurt_val = (m4 / (m2 ** 2)) - 3.0 if m2 > 0 else 0.0

        return {
            "n": n,
            "mean": round(mean_val, 3),
            "var": round(var_val, 4),
            "sd": round(sd_val, 3),
            "se": round(se_val, 3),
            "median": round(median_val, 3),
            "skew": round(skew_val, 3),
            "kurt": round(kurt_val, 3)
        }

    @classmethod
    def compute_independent_ttest(
        cls,
        group1_values: List[float],
        group2_values: List[float],
        group1_label: str = "Nhóm 1",
        group2_label: str = "Nhóm 2",
        variable_label: str = "Biến mục tiêu"
    ) -> Dict[str, Any]:
        """
        Kiểm định Independent Samples T-Test (Độc lập 2 nhóm):
        - Kiểm định tính đồng nhất phương sai Levene (Brown-Forsythe)
        - Student's T-Test (phương sai đồng nhất)
        - Welch's T-Test (phương sai không đồng nhất)
        - Kích thước hiệu ứng Cohen's d & Hedges' g
        - Khoảng tin cậy 95% chênh lệch trung bình
        - Diễn giải học thuật APA 7th Edition
        """
        n1 = len(group1_values)
        n2 = len(group2_values)

        if n1 < 2 or n2 < 2:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Mỗi nhóm cần ít nhất 2 quan sát để thực hiện t-test (Hiện có: {group1_label} N={n1}, {group2_label} N={n2})."
            }

        s1 = cls._compute_basic_stats(group1_values)
        s2 = cls._compute_basic_stats(group2_values)

        m1, v1, sd1 = s1["mean"], s1["var"], s1["sd"]
        m2, v2, sd2 = s2["mean"], s2["var"], s2["sd"]

        # 1. Kiểm định tính đồng nhất phương sai Levene (Brown-Forsythe median-based)
        med1 = s1["median"]
        med2 = s2["median"]
        z1 = [abs(x - med1) for x in group1_values]
        z2 = [abs(x - med2) for x in group2_values]
        mean_z1 = sum(z1) / n1
        mean_z2 = sum(z2) / n2
        all_z = z1 + z2
        grand_mean_z = sum(all_z) / (n1 + n2)

        ss_between = n1 * (mean_z1 - grand_mean_z)**2 + n2 * (mean_z2 - grand_mean_z)**2
        ss_within = sum((z - mean_z1)**2 for z in z1) + sum((z - mean_z2)**2 for z in z2)
        df_within = n1 + n2 - 2

        if ss_within > 1e-12:
            f_levene = (ss_between / 1.0) / (ss_within / df_within)
            p_levene = cls._f_p_value(f_levene, 1.0, float(df_within))
        else:
            f_levene = 0.0
            p_levene = 1.0

        equal_variance_assumed = p_levene >= 0.05

        # 2. Student's T-Test (Equal Variance)
        pooled_var = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
        pooled_sd = math.sqrt(pooled_var) if pooled_var > 0 else 1e-6
        se_student = pooled_sd * math.sqrt(1.0 / n1 + 1.0 / n2)
        diff_mean = m1 - m2
        t_student = diff_mean / se_student if se_student > 1e-12 else 0.0
        df_student = n1 + n2 - 2
        p_student = cls._t_p_value(t_student, float(df_student))

        # 3. Welch's T-Test (Unequal Variance)
        se_welch = math.sqrt((v1 / n1) + (v2 / n2)) if (v1 / n1 + v2 / n2) > 0 else 1e-6
        t_welch = diff_mean / se_welch if se_welch > 1e-12 else 0.0
        # Welch-Satterthwaite df
        num_ws = (v1 / n1 + v2 / n2) ** 2
        denom_ws = ((v1 / n1) ** 2) / (n1 - 1) + ((v2 / n2) ** 2) / (n2 - 1)
        df_welch = num_ws / denom_ws if denom_ws > 0 else float(df_student)
        p_welch = cls._t_p_value(t_welch, df_welch)

        # Quyết định kiểm định chính (Primary Test) dựa trên Levene
        active_t = t_student if equal_variance_assumed else t_welch
        active_df = df_student if equal_variance_assumed else df_welch
        active_p = p_student if equal_variance_assumed else p_welch
        active_se = se_student if equal_variance_assumed else se_welch
        test_method = "Student's t-test (Equal Variances)" if equal_variance_assumed else "Welch's t-test (Unequal Variances)"

        # 4. Kích thước hiệu ứng Cohen's d & Hedges' g
        cohen_d = diff_mean / pooled_sd if pooled_sd > 0 else 0.0
        # Hiệu chỉnh mẫu nhỏ Hedges' g
        hedges_j = 1.0 - (3.0 / (4.0 * (n1 + n2) - 9.0)) if (n1 + n2) > 3 else 1.0
        hedges_g = cohen_d * hedges_j

        abs_d = abs(cohen_d)
        if abs_d < 0.20:
            d_magnitude = "Không đáng kể (Trivial)"
        elif abs_d < 0.50:
            d_magnitude = "Nhỏ (Small)"
        elif abs_d < 0.80:
            d_magnitude = "Trung bình (Medium)"
        else:
            d_magnitude = "Lớn (Large)"

        # 5. Khoảng tin cậy 95% cho chênh lệch trung bình
        t_crit = cls._t_critical_95(active_df)
        margin = t_crit * active_se
        ci_lower = diff_mean - margin
        ci_upper = diff_mean + margin

        # 6. Diễn giải học thuật APA 7th Edition
        sig_text = "có ý nghĩa thống kê" if active_p < 0.05 else "không có ý nghĩa thống kê"
        p_apa = "< .001" if active_p < 0.001 else f"= {active_p:.3f}"
        apa_narrative = (
            f"Kiểm định {test_method} được tiến hành để so sánh {variable_label} giữa "
            f"{group1_label} (M = {m1:.2f}, SD = {sd1:.2f}, N = {n1}) và "
            f"{group2_label} (M = {m2:.2f}, SD = {sd2:.2f}, N = {n2}). "
            f"Kiểm định tính đồng nhất phương sai Levene cho kết quả F({1}, {df_within}) = {f_levene:.2f}, p = {p_levene:.3f} "
            f"({'thỏa mãn giả định phương sai đồng nhất' if equal_variance_assumed else 'vi phạm giả định phương sai đồng nhất, áp dụng hiệu chỉnh Welch'}). "
            f"Kết quả cho thấy chênh lệch điểm trung bình giữa hai nhóm là {sig_text}, "
            f"t({active_df:.1f}) = {active_t:.2f}, p {p_apa}, "
            f"với khoảng tin cậy 95% của chênh lệch trung bình [{ci_lower:.2f}, {ci_upper:.2f}]. "
            f"Kích thước hiệu ứng đạt Cohen's d = {cohen_d:.2f} ({d_magnitude}) và Hedges' g = {hedges_g:.2f}."
        )

        return {
            "status": "SUCCESS",
            "test_type": "independent",
            "test_method": test_method,
            "variable_label": variable_label,
            "group1": {"label": group1_label, **s1},
            "group2": {"label": group2_label, **s2},
            "mean_difference": round(diff_mean, 3),
            "std_error_difference": round(active_se, 3),
            "ci_95_lower": round(ci_lower, 3),
            "ci_95_upper": round(ci_upper, 3),
            "levene_test": {
                "f_stat": round(f_levene, 3),
                "df1": 1,
                "df2": df_within,
                "p_value": round(p_levene, 4),
                "equal_variances_assumed": equal_variance_assumed
            },
            "primary_test": {
                "t_stat": round(active_t, 3),
                "df": round(active_df, 1) if not equal_variance_assumed else int(active_df),
                "p_value": round(active_p, 6),
                "is_significant_05": active_p < 0.05,
                "is_significant_01": active_p < 0.01
            },
            "student_test": {
                "t_stat": round(t_student, 3),
                "df": df_student,
                "p_value": round(p_student, 6),
                "se": round(se_student, 3)
            },
            "welch_test": {
                "t_stat": round(t_welch, 3),
                "df": round(df_welch, 1),
                "p_value": round(p_welch, 6),
                "se": round(se_welch, 3)
            },
            "effect_size": {
                "cohen_d": round(cohen_d, 3),
                "hedges_g": round(hedges_g, 3),
                "magnitude": d_magnitude
            },
            "apa_interpretation": apa_narrative
        }

    @classmethod
    def compute_paired_ttest(
        cls,
        pairs: List[Tuple[float, float]],
        variable1_label: str = "Trước can thiệp (Pre-test)",
        variable2_label: str = "Sau can thiệp (Post-test)"
    ) -> Dict[str, Any]:
        """
        Kiểm định Paired Samples T-Test (Ghép cặp / Mẫu phụ thuộc):
        - So sánh Pre vs Post trên cùng một tập đối tượng
        - Tính chênh lệch từng cặp d_i = x_1i - x_2i
        - Hệ số tương quan Pearson r_12 giữa 2 lần đo
        - Kích thước hiệu ứng Cohen's d_z & Hedges' g
        - Khoảng tin cậy 95% chênh lệch trung bình
        - Diễn giải học thuật APA 7th Edition
        """
        n = len(pairs)
        if n < 2:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần ít nhất 2 cặp quan sát hợp lệ để thực hiện paired t-test (Hiện có N = {n})."
            }

        v1_list = [p[0] for p in pairs]
        v2_list = [p[1] for p in pairs]
        diffs = [p[0] - p[1] for p in pairs]

        s1 = cls._compute_basic_stats(v1_list)
        s2 = cls._compute_basic_stats(v2_list)
        s_diff = cls._compute_basic_stats(diffs)

        m1, sd1 = s1["mean"], s1["sd"]
        m2, sd2 = s2["mean"], s2["sd"]
        mean_diff = s_diff["mean"]
        sd_diff = s_diff["sd"]
        se_diff = s_diff["se"]

        # Hệ số tương quan Pearson giữa 2 lần đo
        if sd1 > 1e-9 and sd2 > 1e-9:
            cov = sum((v1_list[i] - m1) * (v2_list[i] - m2) for i in range(n)) / (n - 1)
            r_val = cov / (sd1 * sd2)
            r_val = max(-1.0, min(1.0, r_val))
        else:
            r_val = 0.0

        # Kiểm định t
        df = n - 1
        t_stat = mean_diff / se_diff if se_diff > 1e-12 else 0.0
        p_val = cls._t_p_value(t_stat, float(df))

        # Kích thước hiệu ứng Cohen's d_z
        cohen_dz = mean_diff / sd_diff if sd_diff > 1e-12 else 0.0
        hedges_j = 1.0 - (3.0 / (4.0 * df - 1.0)) if df > 1 else 1.0
        hedges_gz = cohen_dz * hedges_j

        abs_d = abs(cohen_dz)
        if abs_d < 0.20:
            d_magnitude = "Không đáng kể (Trivial)"
        elif abs_d < 0.50:
            d_magnitude = "Nhỏ (Small)"
        elif abs_d < 0.80:
            d_magnitude = "Trung bình (Medium)"
        else:
            d_magnitude = "Lớn (Large)"

        # Khoảng tin cậy 95%
        t_crit = cls._t_critical_95(float(df))
        margin = t_crit * se_diff
        ci_lower = mean_diff - margin
        ci_upper = mean_diff + margin

        sig_text = "có ý nghĩa thống kê" if p_val < 0.05 else "không có ý nghĩa thống kê"
        p_apa = "< .001" if p_val < 0.001 else f"= {p_val:.3f}"
        apa_narrative = (
            f"Kiểm định Paired-Samples T-Test được thực hiện để đánh giá sự thay đổi giữa "
            f"{variable1_label} (M = {m1:.2f}, SD = {sd1:.2f}) và "
            f"{variable2_label} (M = {m2:.2f}, SD = {sd2:.2f}) trên cỡ mẫu N = {n}. "
            f"Tương quan giữa hai lần đo đạt r = {r_val:.3f}. "
            f"Kết quả cho thấy sự chênh lệch điểm số trung bình (M_diff = {mean_diff:.2f}, SD_diff = {sd_diff:.2f}) "
            f"là {sig_text}, t({df}) = {t_stat:.2f}, p {p_apa}, "
            f"với khoảng tin cậy 95% [{ci_lower:.2f}, {ci_upper:.2f}]. "
            f"Kích thước hiệu ứng đạt Cohen's d_z = {cohen_dz:.2f} ({d_magnitude}) và Hedges' g_z = {hedges_gz:.2f}."
        )

        return {
            "status": "SUCCESS",
            "test_type": "paired",
            "test_method": "Paired Samples T-Test (Dependent)",
            "sample_size": n,
            "mean_difference": round(mean_diff, 3),
            "variable1": {"label": variable1_label, **s1},
            "variable2": {"label": variable2_label, **s2},
            "difference": s_diff,
            "pearson_r": round(r_val, 3),
            "t_stat": round(t_stat, 3),
            "degrees_of_freedom": df,
            "p_value": round(p_val, 6),
            "is_significant_05": p_val < 0.05,
            "is_significant_01": p_val < 0.01,
            "ci_95_lower": round(ci_lower, 3),
            "ci_95_upper": round(ci_upper, 3),
            "effect_size": {
                "cohen_d": round(cohen_dz, 3),
                "hedges_g": round(hedges_gz, 3),
                "magnitude": d_magnitude
            },
            "apa_interpretation": apa_narrative
        }
