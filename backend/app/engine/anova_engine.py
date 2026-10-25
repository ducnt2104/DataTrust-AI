import math
from typing import Dict, Any, List, Optional, Tuple

class ANOVAEngine:
    """
    Động cơ Phân tích Phương sai Một chiều (One-Way ANOVA)
    kết hợp Kiểm định Hậu nghiệm Tukey's HSD (Honestly Significant Difference),
    Kiểm định Phương sai Levene, và Đo lường Kích thước Hiệu ứng (Eta-Squared, Omega-Squared).

    Cơ sở phương pháp luận học thuật:
    - Fisher, R. A. (1925). Statistical Methods for Research Workers.
    - Tukey, J. W. (1949). Comparing individual means in the analysis of variance. Biometrics.
    - Kramer, C. Y. (1956). Extension of multiple range tests to group means with unequal numbers of replications. Biometrics.
    - Levene, H. (1960). Robust tests for equality of variances.
    - Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences.
    - Olejnik, S., & Algina, J. (2003). Generalized eta and omega squared statistics. Psychological Methods.
    """

    @staticmethod
    def _betainc(a: float, b: float, x: float) -> float:
        """Hàm Beta không đầy đủ chính quy hóa I_x(a, b) dùng liên phân số Lentz's method"""
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0

        if x > (a + 1.0) / (a + b + 2.0):
            return 1.0 - ANOVAEngine._betainc(b, a, 1.0 - x)

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

    @staticmethod
    def _studentized_range_q_crit(k: int, df_within: float, alpha: float = 0.05) -> float:
        """
        Xấp xỉ giá trị tới hạn Studentized Range q_crit cho kiểm định Tukey's HSD (alpha = 0.05).
        Công thức xấp xỉ Lund & Lund (1983) và Copenhaver & Holland (1988).
        """
        # Giá trị phân vị chuẩn z tương ứng cho k nhóm
        # Với k từ 2 đến 10 và df >= 10
        k_clamped = max(2, min(k, 15))
        # Bảng tham chiếu chính xác cho df vô hạn
        q_inf_table = {
            2: 2.772, 3: 3.314, 4: 3.633, 5: 3.858,
            6: 4.030, 7: 4.170, 8: 4.286, 9: 4.387, 10: 4.474
        }
        q_inf = q_inf_table.get(k_clamped, 2.772 + 0.8 * math.log(float(k_clamped)))

        if df_within >= 120:
            return q_inf

        # Hiệu chỉnh bậc tự do hữu hạn
        adj = (q_inf**2 + 2.0) / (4.0 * df_within)
        return q_inf + adj

    @staticmethod
    def _compute_stats(values: List[float]) -> Dict[str, float]:
        """Tính thống kê mô tả cho một nhóm: N, Mean, Var, SD, SE, Median"""
        n = len(values)
        if n == 0:
            return {"n": 0, "mean": 0.0, "var": 0.0, "sd": 0.0, "se": 0.0, "median": 0.0}

        mean_val = sum(values) / n
        sorted_vals = sorted(values)
        med = sorted_vals[n // 2] if n % 2 != 0 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

        if n < 2:
            return {"n": n, "mean": round(mean_val, 3), "var": 0.0, "sd": 0.0, "se": 0.0, "median": round(med, 3)}

        var_val = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        sd_val = math.sqrt(var_val)
        se_val = sd_val / math.sqrt(n)

        return {
            "n": n,
            "mean": round(mean_val, 3),
            "var": round(var_val, 4),
            "sd": round(sd_val, 3),
            "se": round(se_val, 3),
            "median": round(med, 3)
        }

    @classmethod
    def compute_oneway_anova(
        cls,
        groups_data: Dict[str, List[float]],
        grouping_label: str = "Biến phân nhóm",
        variable_label: str = "Biến đo lường"
    ) -> Dict[str, Any]:
        """
        Thực hiện toàn bộ quy trình Phân tích Phương sai Một chiều (One-Way ANOVA):
        1. Thống kê mô tả từng nhóm
        2. Kiểm định tính đồng nhất phương sai Levene cho K nhóm
        3. Bảng ANOVA Tổng quát: SS_between, SS_within, SS_total, MS, F-statistic, p-value
        4. Kích thước hiệu ứng Eta-Squared (eta^2) & Omega-Squared (omega^2)
        5. Kiểm định hậu nghiệm Tukey's HSD (Tukey-Kramer pairwise comparisons)
        6. Đoạn văn bản diễn giải học thuật APA 7th Edition
        """
        # Lọc các nhóm có dữ liệu
        valid_groups = {k: v for k, v in groups_data.items() if len(v) > 0}
        k = len(valid_groups)

        if k < 2:
            return {
                "status": "INSUFFICIENT_GROUPS",
                "message": f"Phân tích ANOVA cần ít nhất 2 nhóm để so sánh (Hiện có {k} nhóm hợp lệ)."
            }

        total_n = sum(len(v) for v in valid_groups.values())
        if total_n < k + 1:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Tổng cỡ mẫu (N = {total_n}) phải lớn hơn số nhóm (K = {k}) để tính phương sai trong nhóm."
            }

        # 1. Thống kê mô tả từng nhóm
        group_stats = []
        all_values = []
        for grp_name, vals in valid_groups.items():
            st = cls._compute_stats(vals)
            group_stats.append({"group_name": grp_name, **st})
            all_values.extend(vals)

        grand_mean = sum(all_values) / total_n

        # 2. Kiểm định Levene cho K nhóm (Brown-Forsythe biến thể trung vị)
        z_groups = []
        all_z = []
        for grp_name, vals in valid_groups.items():
            st = next(g for g in group_stats if g["group_name"] == grp_name)
            med = st["median"]
            z_vals = [abs(x - med) for x in vals]
            z_groups.append(z_vals)
            all_z.extend(z_vals)

        grand_mean_z = sum(all_z) / total_n
        ss_between_z = sum(len(z_vals) * (sum(z_vals) / len(z_vals) - grand_mean_z)**2 for z_vals in z_groups)
        ss_within_z = sum(sum((z - sum(z_vals)/len(z_vals))**2 for z in z_vals) for z_vals in z_groups)

        df_between_levene = k - 1
        df_within_levene = total_n - k

        if ss_within_z > 1e-12 and df_within_levene > 0:
            ms_between_z = ss_between_z / df_between_levene
            ms_within_z = ss_within_z / df_within_levene
            f_levene = ms_between_z / ms_within_z
            p_levene = cls._f_p_value(f_levene, float(df_between_levene), float(df_within_levene))
        else:
            f_levene = 0.0
            p_levene = 1.0

        equal_variance_assumed = p_levene >= 0.05

        # 3. Tính toán bảng One-Way ANOVA
        ss_between = sum(len(vals) * (sum(vals) / len(vals) - grand_mean)**2 for vals in valid_groups.values())
        ss_within = sum(sum((x - sum(vals) / len(vals))**2 for x in vals) for vals in valid_groups.values())
        ss_total = ss_between + ss_within

        df_between = k - 1
        df_within = total_n - k
        df_total = total_n - 1

        ms_between = ss_between / df_between if df_between > 0 else 0.0
        ms_within = ss_within / df_within if df_within > 0 else 1e-6

        f_stat = ms_between / ms_within if ms_within > 1e-12 else 0.0
        p_val = cls._f_p_value(f_stat, float(df_between), float(df_within))

        is_significant_05 = p_val < 0.05
        is_significant_01 = p_val < 0.01

        # 4. Kích thước hiệu ứng Eta-Squared & Omega-Squared
        eta_squared = ss_between / ss_total if ss_total > 1e-12 else 0.0
        # Omega-Squared: ít thiên lệch hơn với mẫu hữu hạn
        num_omega = ss_between - df_between * ms_within
        denom_omega = ss_total + ms_within
        omega_squared = num_omega / denom_omega if denom_omega > 1e-12 else 0.0
        omega_squared = max(0.0, omega_squared)

        # Đánh giá độ lớn Eta-Squared (Cohen 1988)
        if eta_squared < 0.01:
            eta_magnitude = "Không đáng kể (Trivial)"
        elif eta_squared < 0.06:
            eta_magnitude = "Nhỏ (Small)"
        elif eta_squared < 0.14:
            eta_magnitude = "Trung bình (Medium)"
        else:
            eta_magnitude = "Lớn (Large)"

        # 5. Kiểm định hậu nghiệm Tukey's HSD (Tukey-Kramer pairwise tests)
        q_crit = cls._studentized_range_q_crit(k, float(df_within), alpha=0.05)
        post_hoc_pairs = []
        group_keys = list(valid_groups.keys())

        for i in range(k):
            for j in range(i + 1, k):
                g1_name = group_keys[i]
                g2_name = group_keys[j]
                st1 = next(g for g in group_stats if g["group_name"] == g1_name)
                st2 = next(g for g in group_stats if g["group_name"] == g2_name)

                m1 = st1["mean"]
                m2 = st2["mean"]
                n1 = st1["n"]
                n2 = st2["n"]

                diff = m1 - m2
                # Sai số chuẩn theo công thức Tukey-Kramer cho cỡ mẫu không đều
                se_tukey = math.sqrt((ms_within / 2.0) * (1.0 / n1 + 1.0 / n2)) if ms_within > 0 else 1e-6
                q_stat = abs(diff) / se_tukey if se_tukey > 1e-12 else 0.0

                # Khoảng tin cậy Tukey 95%
                margin_tukey = (q_crit / math.sqrt(2.0)) * se_tukey * math.sqrt(2.0)
                ci_low = diff - margin_tukey
                ci_up = diff + margin_tukey

                # Ý nghĩa thống kê Tukey (q >= q_crit)
                is_pair_sig = q_stat >= q_crit

                post_hoc_pairs.append({
                    "comparison": f"{g1_name} vs {g2_name}",
                    "group1": g1_name,
                    "group2": g2_name,
                    "mean1": m1,
                    "mean2": m2,
                    "mean_difference": round(diff, 3),
                    "std_error": round(se_tukey, 3),
                    "q_stat": round(q_stat, 3),
                    "q_critical_05": round(q_crit, 3),
                    "is_significant": is_pair_sig,
                    "ci_95_lower": round(ci_low, 3),
                    "ci_95_upper": round(ci_up, 3)
                })

        # Sắp xếp các cặp so sánh theo độ lệch tuyệt đối giảm dần
        post_hoc_pairs.sort(key=lambda x: abs(x["mean_difference"]), reverse=True)

        # 6. Diễn giải học thuật APA 7th Edition
        sig_text = "có ý nghĩa thống kê" if is_significant_05 else "không có ý nghĩa thống kê"
        p_apa = "< .001" if p_val < 0.001 else f"= {p_val:.3f}"

        # Tìm các cặp khác biệt có ý nghĩa
        sig_pair_names = [p["comparison"] for p in post_hoc_pairs if p["is_significant"]]
        if sig_pair_names:
            post_hoc_desc = (
                f"Kiểm định hậu nghiệm Tukey's HSD (q_crit = {q_crit:.2f}) chỉ ra rằng có sự khác biệt có ý nghĩa thống kê "
                f"giữa các cặp nhóm: {', '.join(sig_pair_names)}."
            )
        else:
            post_hoc_desc = "Kiểm định hậu nghiệm Tukey's HSD cho thấy không có cặp nhóm nào đạt khác biệt có ý nghĩa ở mức alpha = .05."

        apa_narrative = (
            f"Phân tích phương sai một chiều (One-Way ANOVA) được thực hiện để đánh giá ảnh hưởng của "
            f"'{grouping_label}' lên '{variable_label}' qua K = {k} nhóm đối tượng (Tổng N = {total_n}). "
            f"Kiểm định Levene cho kết quả F({df_between_levene}, {df_within_levene}) = {f_levene:.2f}, p = {p_levene:.3f} "
            f"({'thỏa mãn giả định phương sai đồng nhất' if equal_variance_assumed else 'lưu ý phương sai giữa các nhóm có sự chênh lệch'}). "
            f"Kết quả phân tích tổng quát cho thấy sự khác biệt giữa các nhóm là {sig_text}, "
            f"F({df_between}, {df_within}) = {f_stat:.2f}, p {p_apa}, "
            f"với kích thước hiệu ứng đạt Eta-squared η² = {eta_squared:.3f} ({eta_magnitude}) "
            f"và Omega-squared ω² = {omega_squared:.3f}. "
            f"{post_hoc_desc}"
        )

        return {
            "status": "SUCCESS",
            "grouping_label": grouping_label,
            "variable_label": variable_label,
            "total_sample_size": total_n,
            "groups_count": k,
            "grand_mean": round(grand_mean, 3),
            "group_statistics": group_stats,
            "levene_test": {
                "f_stat": round(f_levene, 3),
                "df1": df_between_levene,
                "df2": df_within_levene,
                "p_value": round(p_levene, 4),
                "equal_variances_assumed": equal_variance_assumed
            },
            "anova_table": {
                "ss_between": round(ss_between, 3),
                "df_between": df_between,
                "ms_between": round(ms_between, 3),
                "ss_within": round(ss_within, 3),
                "df_within": df_within,
                "ms_within": round(ms_within, 3),
                "ss_total": round(ss_total, 3),
                "df_total": df_total,
                "f_stat": round(f_stat, 3),
                "p_value": round(p_val, 6),
                "is_significant_05": is_significant_05,
                "is_significant_01": is_significant_01
            },
            "effect_size": {
                "eta_squared": round(eta_squared, 4),
                "omega_squared": round(omega_squared, 4),
                "magnitude": eta_magnitude
            },
            "post_hoc_tukey": post_hoc_pairs,
            "apa_interpretation": apa_narrative
        }
