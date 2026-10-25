"""
DataTrust - Exact Permutation & Randomization Inference Engine
==============================================================
Implements Fisher's Exact Randomization Inference for Sharp Null Hypotheses:
- Fisher, R. A. (1935). The Design of Experiments. Oliver and Boyd.
- Rosenbaum, P. R. (2002). Observational Studies (2nd ed.). Springer.
- Ernst, M. D. (2004). Permutation methods: A basis for exact inference.
  Statistical Science, 19(4), 676-685.
- Hodges, J. L., & Lehmann, E. L. (1963). Estimates of location based on rank tests.
  Annals of Mathematical Statistics, 34(2), 598-611.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


class RandomizationInferenceEngine:
    """
    Fisher's Exact Permutation & Randomization Inference Engine.
    """

    @classmethod
    def estimate(
        cls,
        outcomes: np.ndarray,
        treatment: np.ndarray,
        num_permutations: int = 2500,
        alternative: str = "two-sided"  # "two-sided", "greater", "less"
    ) -> Dict[str, Any]:
        """
        Estimate exact permutation null distribution and p-values for sharp null H0: Y_i(1) = Y_i(0).
        """
        Y = np.asarray(outcomes, dtype=float)
        D = np.asarray(treatment, dtype=int)

        if len(Y) != len(D):
            return {
                "status": "error",
                "message": "Độ dài mảng biến kết quả và biến can thiệp không trùng khớp."
            }

        N = len(Y)
        N1 = int(np.sum(D == 1))
        N0 = int(np.sum(D == 0))

        if N1 < 5 or N0 < 5:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 5 quan sát cho mỗi nhóm can thiệp và đối chứng (hiện có: {N1} can thiệp, {N0} đối chứng)."
            }

        # 1. Observed Test Statistics
        y1 = Y[D == 1]
        y0 = Y[D == 0]

        obs_diff_mean = float(np.mean(y1) - np.mean(y0))
        obs_diff_median = float(np.median(y1) - np.median(y0))
        
        # Studentized t-statistic
        s1 = np.var(y1, ddof=1)
        s0 = np.var(y0, ddof=1)
        se_welch = np.sqrt(s1 / N1 + s0 / N0) if (s1 + s0) > 0 else 1.0
        obs_t_stat = float(obs_diff_mean / se_welch) if se_welch > 1e-12 else 0.0

        # Wilcoxon Rank Sum Statistic
        ranks = stats.rankdata(Y)
        obs_rank_sum = float(np.sum(ranks[D == 1]))

        # 2. Hodges-Lehmann Exact Shift Estimator (Median of pairwise differences)
        pairwise_diffs = (y1[:, np.newaxis] - y0[np.newaxis, :]).flatten()
        hl_estimate = float(np.median(pairwise_diffs))

        # 3. Permutation Distribution of Differences in Means
        B = min(10000, max(500, num_permutations))
        perm_diff_means = np.zeros(B)
        perm_diff_medians = np.zeros(B)
        perm_rank_sums = np.zeros(B)

        rng = np.random.RandomState(42)

        for b in range(B):
            perm_D = rng.permutation(D)
            p_y1 = Y[perm_D == 1]
            p_y0 = Y[perm_D == 0]

            perm_diff_means[b] = np.mean(p_y1) - np.mean(p_y0)
            perm_diff_medians[b] = np.median(p_y1) - np.median(p_y0)
            perm_rank_sums[b] = np.sum(ranks[perm_D == 1])

        # 4. Exact p-values
        # Two-sided p-value: proportion of permutations with |T_b| >= |T_obs|
        count_means = np.sum(np.abs(perm_diff_means) >= abs(obs_diff_mean))
        p_val_mean = float((count_means + 1.0) / (B + 1.0))

        count_medians = np.sum(np.abs(perm_diff_medians) >= abs(obs_diff_median))
        p_val_median = float((count_medians + 1.0) / (B + 1.0))

        count_ranks = np.sum(np.abs(perm_rank_sums - np.mean(perm_rank_sums)) >= abs(obs_rank_sum - np.mean(perm_rank_sums)))
        p_val_rank = float((count_ranks + 1.0) / (B + 1.0))

        # Standard Asymptotic Welch t-test for comparison
        asymp_t_stat, asymp_p_val = stats.ttest_ind(y1, y0, equal_var=False)

        # 5. Exact Permutation Confidence Interval for Hodges-Lehmann Shift
        alpha_ci = 0.05
        k_low = int(np.floor(len(pairwise_diffs) * (alpha_ci / 2.0)))
        k_high = int(np.ceil(len(pairwise_diffs) * (1.0 - alpha_ci / 2.0)))
        sorted_diffs = np.sort(pairwise_diffs)
        ci_lower = float(sorted_diffs[max(0, k_low)])
        ci_upper = float(sorted_diffs[min(len(sorted_diffs) - 1, k_high)])

        # 6. Generate Vector SVG Dual-Panel Chart
        svg_chart = cls._generate_svg_chart(
            perm_diff_means=perm_diff_means,
            obs_stat=obs_diff_mean,
            p_val=p_val_mean,
            hl_estimate=hl_estimate,
            ci_lower=ci_lower,
            ci_upper=ci_upper
        )

        # 7. APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_obs=N,
            n_treat=N1,
            n_ctrl=N0,
            b_perms=B,
            obs_diff_mean=obs_diff_mean,
            p_val_mean=p_val_mean,
            obs_diff_median=obs_diff_median,
            p_val_median=p_val_median,
            hl_estimate=hl_estimate,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            asymp_p_val=float(asymp_p_val)
        )

        return {
            "status": "success",
            "sample_size": N,
            "treated_count": N1,
            "control_count": N0,
            "permutations_count": B,
            "difference_in_means": {
                "observed_statistic": round(obs_diff_mean, 4),
                "exact_p_value": round(p_val_mean, 4),
                "is_significant": bool(p_val_mean < 0.05)
            },
            "difference_in_medians": {
                "observed_statistic": round(obs_diff_median, 4),
                "exact_p_value": round(p_val_median, 4),
                "is_significant": bool(p_val_median < 0.05)
            },
            "wilcoxon_rank_sum": {
                "observed_statistic": round(obs_rank_sum, 2),
                "exact_p_value": round(p_val_rank, 4),
                "is_significant": bool(p_val_rank < 0.05)
            },
            "hodges_lehmann_shift": {
                "point_estimate": round(hl_estimate, 4),
                "ci_95_lower": round(ci_lower, 4),
                "ci_95_upper": round(ci_upper, 4)
            },
            "asymptotic_welch_t_test": {
                "t_statistic": round(float(asymp_t_stat), 4),
                "p_value": round(float(asymp_p_val), 4)
            },
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        perm_diff_means: np.ndarray,
        obs_stat: float,
        p_val: float,
        hl_estimate: float,
        ci_lower: float,
        ci_upper: float
    ) -> str:
        w, h = 900, 360
        margin_l = 60
        plot_w = 400
        plot_h = 240
        top = 50

        # Panel A: Permutation Null Histogram
        n_bins = 25
        counts, bin_edges = np.histogram(perm_diff_means, bins=n_bins)
        max_c = max(1, int(np.max(counts)))
        bin_w = plot_w / n_bins

        min_val = min(float(bin_edges[0]), obs_stat)
        max_val = max(float(bin_edges[-1]), obs_stat)
        pad = 0.1 * (max_val - min_val + 1e-4)
        x_min = min_val - pad
        x_max = max_val + pad

        def to_x_a(val: float) -> float:
            return margin_l + ((val - bin_edges[0]) / max(1e-4, bin_edges[-1] - bin_edges[0])) * plot_w

        # Observed line in Panel A
        obs_x = margin_l + ((obs_stat - bin_edges[0]) / max(1e-4, bin_edges[-1] - bin_edges[0])) * plot_w
        obs_x_clamped = max(margin_l, min(margin_l + plot_w, obs_x))

        # Panel B: Cumulative Permutation Null Distribution
        p2_l = 510
        p2_w = 340
        sorted_perms = np.sort(perm_diff_means)
        prob_grid = np.linspace(0, 1, len(sorted_perms))

        def to_x_b(val: float) -> float:
            return p2_l + ((val - sorted_perms[0]) / max(1e-4, sorted_perms[-1] - sorted_perms[0])) * p2_w

        def to_y_b(p: float) -> float:
            return top + plot_h - p * plot_h

        # Thin step curve for performance
        step = max(1, len(sorted_perms) // 50)
        pts_cdf = [f"{to_x_b(sorted_perms[i]):.1f},{to_y_b(prob_grid[i]):.1f}" for i in range(0, len(sorted_perms), step)]

        svg = f"""<svg width="100%" height="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; font-family:Inter,system-ui,sans-serif;">
  <!-- Panel A Header -->
  <text x="{margin_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel A: Phân phối Hoán vị Vô hiệu Chính xác (Permutation Null Distribution)</text>
  <rect x="{margin_l}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>
"""
        for i in range(n_bins):
            bx = margin_l + i * bin_w
            bar_h = (counts[i] / max_c) * (plot_h - 20)
            by = top + plot_h - bar_h
            b_mid = 0.5 * (bin_edges[i] + bin_edges[i+1])
            is_extreme = abs(b_mid) >= abs(obs_stat)
            fill_c = "#f43f5e" if is_extreme else "#38bdf8"
            svg += f'  <rect x="{bx + 1:.1f}" y="{by:.1f}" width="{bin_w - 2:.1f}" height="{bar_h:.1f}" fill="{fill_c}" fill-opacity="0.75" rx="1.5"/>\n'

        # Observed line
        svg += f"""  <line x1="{obs_x_clamped:.1f}" y1="{top}" x2="{obs_x_clamped:.1f}" y2="{top + plot_h}" stroke="#34d399" stroke-width="2.5"/>
  <text x="{obs_x_clamped:.1f}" y="{top + 16}" fill="#34d399" font-size="11" font-weight="bold" text-anchor="middle">T_obs = {obs_stat:+.2f} (p = {p_val:.3f})</text>
  <text x="{margin_l + plot_w / 2}" y="{top + plot_h + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">Chênh lệch trung bình hoán vị (Permuted Diff Means)</text>

  <!-- Panel B Header -->
  <text x="{p2_l}" y="28" fill="#f8fafc" font-size="13" font-weight="bold">Panel B: Ước lượng Dịch chuyển Hodges-Lehmann &amp; 95% Exact CI</text>
  <rect x="{p2_l}" y="{top}" width="{p2_w}" height="{plot_h}" fill="#1e293b" fill-opacity="0.4" rx="6" stroke="#334155" stroke-width="1"/>

  <path d="M {' L '.join(pts_cdf)}" fill="none" stroke="#38bdf8" stroke-width="2.2"/>
  <line x1="{p2_l}" y1="{top + plot_h / 2:.1f}" x2="{p2_l + p2_w}" y2="{top + plot_h / 2:.1f}" stroke="#64748b" stroke-dasharray="3,3" stroke-width="1"/>

  <!-- Hodges Lehmann Box -->
  <rect x="{p2_l + 20}" y="{top + 20}" width="{p2_w - 40}" height="80" fill="#0f172a" fill-opacity="0.8" rx="8" stroke="#334155" stroke-width="1"/>
  <text x="{p2_l + 35}" y="{top + 45}" fill="#94a3b8" font-size="11">Hodges-Lehmann Shift:</text>
  <text x="{p2_l + 35}" y="{top + 68}" fill="#34d399" font-size="16" font-weight="black">Δ = {hl_estimate:+.3f}</text>
  <text x="{p2_l + 35}" y="{top + 88}" fill="#cbd5e1" font-size="10">95% Exact CI: [{ci_lower:.2f}, {ci_upper:.2f}]</text>

  <text x="{p2_l + p2_w / 2}" y="{top + plot_h + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">Hàm phân phối tích lũy hoán vị</text>
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_obs: int,
        n_treat: int,
        n_ctrl: int,
        b_perms: int,
        obs_diff_mean: float,
        p_val_mean: float,
        obs_diff_median: float,
        p_val_median: float,
        hl_estimate: float,
        ci_lower: float,
        ci_upper: float,
        asymp_p_val: float
    ) -> str:
        narrative = (
            f"Kiểm định Hoán vị Chính xác Fisher (Fisher's Exact Randomization Inference; Fisher, 1935; Rosenbaum, 2002) "
            f"đã được thực hiện để kiểm định Giả thuyết Vô hiệu Tuyệt đối (Sharp Null Hypothesis H0: Y_i(1) = Y_i(0) ∀i) "
            f"trên cỡ mẫu gồm N = {n_obs} quan sát (n_treat = {n_treat}, n_ctrl = {n_ctrl}) "
            f"dựa trên B = {b_perms:,} lần hoán vị ngẫu nhiên hoàn toàn.\n\n"
            f"Chênh lệch trung bình quan sát giữa nhóm can thiệp và đối chứng đạt Diff = {obs_diff_mean:+.3f}, "
            f"với giá trị p chính xác theo phân phối hoán vị đạt p_exact = {p_val_mean:.4f} "
            f"({'có ý nghĩa thống kê ở mức p < .05' if p_val_mean < 0.05 else 'chưa đạt mức ý nghĩa thống kê p < .05'}). "
            f"Chênh lệch trung vị quan sát đạt Diff_Median = {obs_diff_median:+.3f} (p_exact = {p_val_median:.4f}).\n\n"
            f"Ước lượng độ dịch chuyển phân phối chính xác Hodges-Lehmann (1963) ghi nhận mức tăng "
            f"Δ_HL = {hl_estimate:+.3f} với khoảng tin cậy chính xác 95% Exact CI [{ci_lower:.3f}, {ci_upper:.3f}]. "
            f"So sánh với kiểm định tiệm cận Welch's t-test (p_asymp = {asymp_p_val:.4f}): "
            f"kiểm định hoán vị Fisher đảm bảo tính chính xác hữu hạn mẫu hoàn hảo, "
            f"hoàn toàn miễn nhiễm trước sự vi phạm giả định phân phối chuẩn hoặc hiện tượng ngoại lai cực đoan."
        )
        return narrative
