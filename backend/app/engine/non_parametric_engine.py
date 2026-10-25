import math
from typing import Dict, Any, List, Optional, Tuple

class NonParametricEngine:
    """
    Động cơ Kiểm định Giả thuyết Phi tham số (Non-Parametric Hypothesis Testing Engine)
    Tuân thủ các tiêu chuẩn phương pháp luận học thuật:
    - Mann, H. B., & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other.
    - Wilcoxon, F. (1945). Individual comparisons by ranking methods.
    - Kruskal, W. H., & Wallis, W. A. (1952). Use of ranks in one-criterion variance analysis.
    - Dunn, O. J. (1964). Multiple comparisons using rank sums.
    - Rosenthal, R. (1991). Meta-analytic procedures for social research (Effect size r = z / sqrt(N)).
    - Kerby, D. S. (2014). The simple difference formula: An approach to teaching nonparametric correlation.
    """

    @staticmethod
    def _rank_data(values: List[float]) -> Tuple[List[float], List[int]]:
        """
        Xếp hạng chuỗi dữ liệu kèm gán hạng trung bình (Fractional / Average Ranks) cho các giá trị hòa (Ties).
        Trả về (danh_sách_hạng, danh_sách_số_lượng_ties [t_1, t_2, ...]).
        """
        n = len(values)
        if n == 0:
            return [], []

        indexed = sorted([(val, i) for i, val in enumerate(values)], key=lambda x: x[0])
        ranks = [0.0] * n
        tie_counts: List[int] = []

        i = 0
        while i < n:
            val = indexed[i][0]
            j = i + 1
            while j < n and abs(indexed[j][0] - val) < 1e-12:
                j += 1

            count = j - i
            # Thứ hạng từ (i + 1) đến j (1-indexed)
            avg_rank = (i + 1 + j) / 2.0
            for k in range(i, j):
                orig_idx = indexed[k][1]
                ranks[orig_idx] = avg_rank

            if count > 1:
                tie_counts.append(count)

            i = j

        return ranks, tie_counts

    @staticmethod
    def _normal_cdf(z: float) -> float:
        """Hàm tích lũy chuẩn tắc phi(z) = 0.5 * (1 + erf(z / sqrt(2)))"""
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

    @classmethod
    def _normal_2tailed_p(cls, z: float) -> float:
        """Tính p-value 2 phía cho thống kê chuẩn z"""
        p = 2.0 * (1.0 - cls._normal_cdf(abs(z)))
        return max(0.0, min(1.0, p))

    @staticmethod
    def _chi_square_cdf(x: float, k: float) -> float:
        """Hàm tích lũy Chi-Square qua hàm Gamma không đầy đủ"""
        if x <= 0.0 or k <= 0.0:
            return 0.0
        a = 0.5 * k
        z = 0.5 * x
        if z < a + 1.0:
            sum_val = 1.0 / a
            term = 1.0 / a
            for n in range(1, 120):
                term *= z / (a + n)
                sum_val += term
                if abs(term) < abs(sum_val) * 1.0e-10:
                    break
            return sum_val * math.exp(-z + a * math.log(z) - math.lgamma(a))
        else:
            b0 = z + 1.0 - a
            c = 1.0 / 1.0e-30
            d = 1.0 / b0
            f = d
            for i in range(1, 120):
                an = -i * (i - a)
                b0 += 2.0
                d = an * d + b0
                if abs(d) < 1.0e-30:
                    d = 1.0e-30
                c = b0 + an / c
                if abs(c) < 1.0e-30:
                    c = 1.0e-30
                d = 1.0 / d
                delta = d * c
                f *= delta
                if abs(delta - 1.0) < 1.0e-10:
                    break
            return 1.0 - math.exp(-z + a * math.log(z) - math.lgamma(a)) * f

    @classmethod
    def _chi_square_p_value(cls, x: float, df: float) -> float:
        """Tính p-value P(Chi2 >= x) cho phân phối Chi-Square"""
        if x <= 0.0 or df <= 0.0:
            return 1.0
        cdf = cls._chi_square_cdf(x, df)
        return max(0.0, min(1.0, 1.0 - cdf))

    @staticmethod
    def _compute_descriptives(values: List[float]) -> Dict[str, Any]:
        """Tính toán trung vị (Median), Q1, Q3, IQR, Min, Max"""
        n = len(values)
        if n == 0:
            return {"n": 0, "median": 0.0, "q1": 0.0, "q3": 0.0, "iqr": 0.0, "mean": 0.0, "std": 0.0}

        sorted_v = sorted(values)
        mean_v = sum(sorted_v) / n
        var_v = sum((x - mean_v) ** 2 for x in sorted_v) / (n - 1) if n > 1 else 0.0
        std_v = math.sqrt(var_v)

        def percentile(p: float) -> float:
            idx = p * (n - 1)
            lower = int(math.floor(idx))
            upper = int(math.ceil(idx))
            weight = idx - lower
            return sorted_v[lower] * (1.0 - weight) + sorted_v[upper] * weight

        median_v = percentile(0.5)
        q1_v = percentile(0.25)
        q3_v = percentile(0.75)
        iqr_v = q3_v - q1_v

        return {
            "n": n,
            "mean": round(mean_v, 2),
            "std": round(std_v, 2),
            "median": round(median_v, 2),
            "q1": round(q1_v, 2),
            "q3": round(q3_v, 2),
            "iqr": round(iqr_v, 2),
            "min": round(sorted_v[0], 2),
            "max": round(sorted_v[-1], 2)
        }

    # -------------------------------------------------------------------------
    # 1. Mann-Whitney U Test (Hai nhóm độc lập)
    # -------------------------------------------------------------------------
    @classmethod
    def mann_whitney_u_test(
        cls,
        group1: List[float],
        group2: List[float],
        g1_name: str = "Nhóm 1",
        g2_name: str = "Nhóm 2"
    ) -> Dict[str, Any]:
        """
        Kiểm định U của Mann-Whitney (Wilcoxon Rank-Sum Test) cho 2 mẫu độc lập.
        Tương đương phi tham số của Independent Samples t-test.
        """
        n1 = len(group1)
        n2 = len(group2)
        if n1 < 2 or n2 < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Cần tối thiểu n >= 2 quan sát cho mỗi nhóm (hiện có n1={n1}, n2={n2})."
            }

        n_total = n1 + n2
        combined = list(group1) + list(group2)
        ranks, tie_counts = cls._rank_data(combined)

        r1 = sum(ranks[:n1])
        r2 = sum(ranks[n1:])

        mean_rank1 = round(r1 / n1, 2)
        mean_rank2 = round(r2 / n2, 2)

        u1 = n1 * n2 + (n1 * (n1 + 1)) / 2.0 - r1
        u2 = n1 * n2 + (n2 * (n2 + 1)) / 2.0 - r2
        u_stat = min(u1, u2)

        # Hiệu chỉnh ties cho phương sai của U
        tie_correction = sum((t ** 3 - t) for t in tie_counts) / (n_total * (n_total - 1)) if n_total > 1 else 0.0
        var_u = (n1 * n2 / 12.0) * (n_total + 1 - tie_correction)
        se_u = math.sqrt(max(1e-12, var_u))

        mean_u = (n1 * n2) / 2.0
        # Hiệu chỉnh tính liên tục (Continuity correction)
        diff = u_stat - mean_u
        z_stat = (abs(diff) - 0.5) / se_u if se_u > 0 else 0.0
        if diff < 0:
            z_stat = -z_stat

        p_value = cls._normal_2tailed_p(z_stat)

        # Kích thước tác động (Effect Sizes)
        # Rosenthal (1991): r = |z| / sqrt(N)
        rosenthal_r = round(abs(z_stat) / math.sqrt(n_total), 3) if n_total > 0 else 0.0
        # Rank-biserial correlation r_rb = 1 - 2*U1 / (n1*n2)
        rank_biserial = round((u2 - u1) / (n1 * n2), 3) if (n1 * n2) > 0 else 0.0
        # Common Language Effect Size (CLES / Probability of Superiority)
        cles = round((u1 / (n1 * n2)) * 100.0, 1) if (n1 * n2) > 0 else 50.0

        desc1 = cls._compute_descriptives(group1)
        desc2 = cls._compute_descriptives(group2)

        is_significant = p_value < 0.05
        higher_group = g1_name if mean_rank1 > mean_rank2 else g2_name

        apa_narrative = (
            f"Kiểm định phi tham số Mann-Whitney U được thực hiện để so sánh sự khác biệt về phân bố giữa "
            f"{g1_name} (Mdn = {desc1['median']}, IQR = {desc1['iqr']}, Mean Rank = {mean_rank1}) và "
            f"{g2_name} (Mdn = {desc2['median']}, IQR = {desc2['iqr']}, Mean Rank = {mean_rank2}). "
            f"Kết quả cho thấy sự khác biệt {'có ý nghĩa thống kê' if is_significant else 'không có ý nghĩa thống kê'}, "
            f"U = {round(u_stat, 2)}, z = {round(z_stat, 2)}, p = {round(p_value, 4)}, kích thước tác động Rosenthal r = {rosenthal_r} "
            f"(hệ số tương quan thứ bậc rank-biserial r_rb = {rank_biserial}, xác suất ưu trội CLES = {cles}%)."
        )

        return {
            "status": "OK",
            "test_type": "MANN_WHITNEY_U",
            "total_sample_size": n_total,
            "groups": {
                "group1": {
                    "name": g1_name,
                    "rank_sum": round(r1, 1),
                    "mean_rank": mean_rank1,
                    "descriptives": desc1
                },
                "group2": {
                    "name": g2_name,
                    "rank_sum": round(r2, 1),
                    "mean_rank": mean_rank2,
                    "descriptives": desc2
                }
            },
            "statistics": {
                "u_statistic": round(u_stat, 2),
                "u1": round(u1, 2),
                "u2": round(u2, 2),
                "expected_mean_u": round(mean_u, 2),
                "std_error_u": round(se_u, 3),
                "z_statistic": round(z_stat, 3),
                "p_value": round(p_value, 5),
                "is_significant": is_significant,
                "ties_count": sum(tie_counts)
            },
            "effect_size": {
                "rosenthal_r": rosenthal_r,
                "rosenthal_magnitude": (
                    "Lớn (Large)" if rosenthal_r >= 0.5 else
                    ("Trung bình (Medium)" if rosenthal_r >= 0.3 else
                    ("Nhỏ (Small)" if rosenthal_r >= 0.1 else "Không đáng kể (Negligible)"))
                ),
                "rank_biserial_correlation": rank_biserial,
                "common_language_effect_size_pct": cles
            },
            "conclusion": {
                "higher_group": higher_group,
                "is_significant": is_significant,
                "apa_narrative": apa_narrative
            }
        }

    # -------------------------------------------------------------------------
    # 2. Wilcoxon Signed-Rank Test (Cặp quan sát phụ thuộc)
    # -------------------------------------------------------------------------
    @classmethod
    def wilcoxon_signed_rank_test(
        cls,
        sample1: List[float],
        sample2: List[float],
        s1_name: str = "Đo lường 1",
        s2_name: str = "Đo lường 2"
    ) -> Dict[str, Any]:
        """
        Kiểm định hạng có dấu Wilcoxon (Wilcoxon Signed-Rank Test) cho các cặp quan sát phụ thuộc (Paired).
        Tương đương phi tham số của Paired Samples t-test.
        """
        n_pairs = len(sample1)
        if n_pairs != len(sample2):
            return {
                "status": "ERROR",
                "message": f"Số lượng quan sát không khớp: Mẫu 1 có {n_pairs}, Mẫu 2 có {len(sample2)}."
            }

        if n_pairs < 5:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Cần tối thiểu N >= 5 cặp quan sát để kiểm định Wilcoxon (hiện có N={n_pairs})."
            }

        diffs = [s1 - s2 for s1, s2 in zip(sample1, sample2)]
        non_zero_diffs = [d for d in diffs if abs(d) > 1e-12]
        zero_diffs_count = n_pairs - len(non_zero_diffs)

        nr = len(non_zero_diffs)
        if nr < 3:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": "Không đủ cặp quan sát có chênh lệch khác 0 để thực hiện kiểm định."
            }

        abs_diffs = [abs(d) for d in non_zero_diffs]
        ranks, tie_counts = cls._rank_data(abs_diffs)

        w_plus = sum(ranks[i] for i in range(nr) if non_zero_diffs[i] > 0)
        w_minus = sum(ranks[i] for i in range(nr) if non_zero_diffs[i] < 0)
        w_stat = min(w_plus, w_minus)

        expected_w = (nr * (nr + 1)) / 4.0

        # Hiệu chỉnh ties cho phương sai Wilcoxon
        tie_sum = sum((t ** 3 - t) for t in tie_counts)
        var_w = (nr * (nr + 1) * (2 * nr + 1) - 0.5 * tie_sum) / 24.0
        se_w = math.sqrt(max(1e-12, var_w))

        diff_w = w_plus - expected_w
        z_stat = (abs(diff_w) - 0.5) / se_w if se_w > 0 else 0.0
        if diff_w < 0:
            z_stat = -z_stat

        p_value = cls._normal_2tailed_p(z_stat)
        is_significant = p_value < 0.05

        # Effect sizes
        rosenthal_r = round(abs(z_stat) / math.sqrt(n_pairs), 3) if n_pairs > 0 else 0.0
        # Matched-pairs rank-biserial correlation (Kerby 2014)
        total_w = w_plus + w_minus
        matched_pairs_rb = round((w_plus - w_minus) / total_w, 3) if total_w > 0 else 0.0

        desc1 = cls._compute_descriptives(sample1)
        desc2 = cls._compute_descriptives(sample2)
        desc_diff = cls._compute_descriptives(diffs)

        apa_narrative = (
            f"Kiểm định hạng có dấu Wilcoxon Signed-Rank cho các cặp quan sát (N = {n_pairs}) so sánh giữa "
            f"{s1_name} (Mdn = {desc1['median']}, IQR = {desc1['iqr']}) và "
            f"{s2_name} (Mdn = {desc2['median']}, IQR = {desc2['iqr']}) cho thấy "
            f"sự khác biệt {'đạt ý nghĩa thống kê' if is_significant else 'chưa đạt ý nghĩa thống kê'}, "
            f"W = {round(w_stat, 2)} (W+ = {round(w_plus, 2)}, W- = {round(w_minus, 2)}), z = {round(z_stat, 2)}, "
            f"p = {round(p_value, 4)}, kích thước tác động Rosenthal r = {rosenthal_r} (tương quan thứ bậc cặp r_prb = {matched_pairs_rb}). "
            f"Số cặp chênh lệch bằng 0 bị loại trừ: {zero_diffs_count}."
        )

        return {
            "status": "OK",
            "test_type": "WILCOXON_SIGNED_RANK",
            "total_pairs": n_pairs,
            "effective_pairs": nr,
            "zero_differences_count": zero_diffs_count,
            "samples": {
                "sample1": {"name": s1_name, "descriptives": desc1},
                "sample2": {"name": s2_name, "descriptives": desc2},
                "differences": desc_diff
            },
            "statistics": {
                "w_statistic": round(w_stat, 2),
                "w_plus": round(w_plus, 2),
                "w_minus": round(w_minus, 2),
                "expected_mean_w": round(expected_w, 2),
                "std_error_w": round(se_w, 3),
                "z_statistic": round(z_stat, 3),
                "p_value": round(p_value, 5),
                "is_significant": is_significant,
                "ties_count": sum(tie_counts)
            },
            "effect_size": {
                "rosenthal_r": rosenthal_r,
                "rosenthal_magnitude": (
                    "Lớn (Large)" if rosenthal_r >= 0.5 else
                    ("Trung bình (Medium)" if rosenthal_r >= 0.3 else
                    ("Nhỏ (Small)" if rosenthal_r >= 0.1 else "Không đáng kể (Negligible)"))
                ),
                "matched_pairs_rank_biserial": matched_pairs_rb
            },
            "conclusion": {
                "is_significant": is_significant,
                "apa_narrative": apa_narrative
            }
        }

    # -------------------------------------------------------------------------
    # 3. Kruskal-Wallis H Test (Nhiều nhóm độc lập >= 3) & Dunn's Post-Hoc
    # -------------------------------------------------------------------------
    @classmethod
    def kruskal_wallis_h_test(
        cls,
        groups: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """
        Kiểm định Kruskal-Wallis H (One-Way Non-Parametric ANOVA) cho k >= 3 nhóm độc lập.
        Kèm so sánh cặp hậu nghiệm Dunn's Test với hiệu chỉnh Bonferroni.
        """
        k = len(groups)
        if k < 2:
            return {
                "status": "ERROR",
                "message": f"Kiểm định Kruskal-Wallis yêu cầu tối thiểu k >= 2 nhóm (hiện có k={k})."
            }

        group_names = list(groups.keys())
        all_vals: List[float] = []
        group_indices: List[int] = []

        for g_idx, g_name in enumerate(group_names):
            vals = groups[g_name]
            all_vals.extend(vals)
            group_indices.extend([g_idx] * len(vals))

        n_total = len(all_vals)
        if n_total < 5:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Tổng cỡ mẫu quá nhỏ N={n_total}. Cần tối thiểu N >= 5 quan sát."
            }

        ranks, tie_counts = cls._rank_data(all_vals)

        group_ranks: Dict[str, List[float]] = {name: [] for name in group_names}
        for i, g_idx in enumerate(group_indices):
            group_ranks[group_names[g_idx]].append(ranks[i])

        group_stats = []
        rank_sum_sq_div_n = 0.0

        for g_name in group_names:
            g_r = group_ranks[g_name]
            n_j = len(g_r)
            if n_j == 0:
                continue
            r_sum = sum(g_r)
            mean_r = r_sum / n_j
            rank_sum_sq_div_n += (r_sum ** 2) / n_j

            desc = cls._compute_descriptives(groups[g_name])
            group_stats.append({
                "group_name": g_name,
                "sample_size": n_j,
                "rank_sum": round(r_sum, 1),
                "mean_rank": round(mean_r, 2),
                "median": desc["median"],
                "iqr": desc["iqr"],
                "mean": desc["mean"],
                "std": desc["std"]
            })

        # Công thức H thô
        h_raw = (12.0 / (n_total * (n_total + 1))) * rank_sum_sq_div_n - 3.0 * (n_total + 1)

        # Hiệu chỉnh Ties
        tie_sum = sum((t ** 3 - t) for t in tie_counts)
        tie_denom = (n_total ** 3 - n_total)
        tie_correction = 1.0 - (tie_sum / tie_denom) if tie_denom > 0 else 1.0

        h_adj = h_raw / tie_correction if tie_correction > 1e-12 else h_raw
        df = k - 1
        p_value = cls._chi_square_p_value(h_adj, df)
        is_significant = p_value < 0.05

        # Epsilon-squared effect size: eps^2 = (H_adj - k + 1) / (N - k)
        eps_denom = n_total - k
        epsilon_squared = round(max(0.0, (h_adj - k + 1) / eps_denom), 3) if eps_denom > 0 else 0.0

        # -------------------------------------------------------------
        # So sánh cặp hậu nghiệm Dunn's Test với hiệu chỉnh Bonferroni
        # -------------------------------------------------------------
        dunn_pairs = []
        num_comparisons = (k * (k - 1)) // 2
        var_factor = (n_total * (n_total + 1) / 12.0) - (tie_sum / (12.0 * (n_total - 1))) if (n_total > 1) else 1.0

        for i in range(k):
            for j in range(i + 1, k):
                g1_name = group_names[i]
                g2_name = group_names[j]
                n1 = len(groups[g1_name])
                n2 = len(groups[g2_name])
                if n1 == 0 or n2 == 0:
                    continue

                mr1 = sum(group_ranks[g1_name]) / n1
                mr2 = sum(group_ranks[g2_name]) / n2
                diff_mr = mr1 - mr2

                se_dunn = math.sqrt(max(1e-12, var_factor * (1.0 / n1 + 1.0 / n2)))
                z_dunn = diff_mr / se_dunn if se_dunn > 0 else 0.0
                unadj_p = cls._normal_2tailed_p(z_dunn)
                bonferroni_p = min(1.0, unadj_p * num_comparisons)

                dunn_pairs.append({
                    "comparison": f"{g1_name} vs {g2_name}",
                    "group1": g1_name,
                    "group2": g2_name,
                    "mean_rank1": round(mr1, 2),
                    "mean_rank2": round(mr2, 2),
                    "mean_rank_diff": round(diff_mr, 2),
                    "std_error": round(se_dunn, 3),
                    "z_statistic": round(z_dunn, 3),
                    "p_value_unadjusted": round(unadj_p, 4),
                    "p_value_bonferroni": round(bonferroni_p, 4),
                    "is_significant_bonferroni": bonferroni_p < 0.05
                })

        apa_narrative = (
            f"Kiểm định phi tham số Kruskal-Wallis H được thực hiện để so sánh {k} nhóm độc lập (Tổng N = {n_total}). "
            f"Kết quả cho thấy sự khác biệt giữa các nhóm là {'có ý nghĩa thống kê' if is_significant else 'không có ý nghĩa thống kê'}, "
            f"H({df}) = {round(h_adj, 2)}, p = {round(p_value, 4)}, hệ số độ lớn tác động epsilon-squared ε² = {epsilon_squared}. "
        )
        if is_significant and dunn_pairs:
            sig_pairs = [p["comparison"] for p in dunn_pairs if p["is_significant_bonferroni"]]
            if sig_pairs:
                apa_narrative += f"So sánh cặp hậu nghiệm Dunn's test với hiệu chỉnh Bonferroni ghi nhận các cặp có sự khác biệt ý nghĩa bao gồm: {', '.join(sig_pairs)}."
            else:
                apa_narrative += "Tuy nhiên, hiệu chỉnh Bonferroni cho các so sánh cặp hậu nghiệm Dunn không ghi nhận cặp nào duy trì ý nghĩa thống kê ở mức α = .05."

        return {
            "status": "OK",
            "test_type": "KRUSKAL_WALLIS_H",
            "k_groups": k,
            "total_sample_size": n_total,
            "degrees_of_freedom": df,
            "statistics": {
                "h_raw": round(h_raw, 2),
                "h_adjusted": round(h_adj, 2),
                "tie_correction_factor": round(tie_correction, 4),
                "ties_count": sum(tie_counts),
                "p_value": round(p_value, 5),
                "is_significant": is_significant
            },
            "effect_size": {
                "epsilon_squared": epsilon_squared,
                "magnitude": (
                    "Lớn (Large)" if epsilon_squared >= 0.14 else
                    ("Trung bình (Medium)" if epsilon_squared >= 0.06 else
                    ("Nhỏ (Small)" if epsilon_squared >= 0.01 else "Không đáng kể (Negligible)"))
                )
            },
            "groups_summary": group_stats,
            "post_hoc_dunn_tests": dunn_pairs,
            "conclusion": {
                "is_significant": is_significant,
                "apa_narrative": apa_narrative
            }
        }
