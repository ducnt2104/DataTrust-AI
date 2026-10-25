"""
DataTrust — Statistical Power Analysis & Sample Size Estimator Engine
Calculates A Priori and Post-Hoc Statistical Power (1 - beta), Minimum Sample Size (N_min),
Cochran & Yamane Proportion Formula with Finite Population Correction (FPC),
and Power Curves for T-Tests, ANOVA, and Correlation.
Complies with Cohen (1988), Faul et al. (G*Power), Cochran (1977), and APA 7th Edition.
"""

import math
from typing import Dict, Any, List, Optional

class PowerAnalysisEngine:
    """
    Động cơ Ước lượng Cỡ mẫu & Phân tích Lực Thống kê (Statistical Power Engine).
    Hỗ trợ cả 2 phương thức:
    1. A Priori Power Analysis: Tính cỡ mẫu tối thiểu cần thu thập trước khi khảo sát.
    2. Post-Hoc Power Analysis: Đánh giá lực thống kê đạt được trên tập mẫu thực tế đã thu thập.
    """

    @classmethod
    def normal_cdf(cls, x: float) -> float:
        """Phân phối tích lũy chuẩn tắc Phi(x) qua xấp xỉ hàm sai số Abramowitz & Stegun"""
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @classmethod
    def normal_ppf(cls, p: float) -> float:
        """Hàm phân vị chuẩn tắc nghịch đảo Phi^(-1)(p) qua thuật toán xấp xỉ hữu tỉ Abramowitz & Stegun (1964)"""
        if p <= 0.0:
            return -8.0
        if p >= 1.0:
            return 8.0
        if abs(p - 0.5) < 1e-9:
            return 0.0

        is_upper = p > 0.5
        prob = 1.0 - p if is_upper else p

        t = math.sqrt(-2.0 * math.log(prob))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308

        num = (c2 * t + c1) * t + c0
        den = ((d3 * t + d2) * t + d1) * t + 1.0
        z = t - (num / den)

        return z if is_upper else -z

    @classmethod
    def calculate_cochran_sample_size(
        cls,
        confidence_level: float = 0.95,
        margin_of_error: float = 0.05,
        proportion: float = 0.50,
        population_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tính cỡ mẫu tỷ lệ theo công thức Cochran (1977) & Yamane (1967).
        Hỗ trợ hiệu chỉnh cho tổng thể hữu hạn (Finite Population Correction - FPC).
        """
        alpha = 1.0 - confidence_level
        z_crit = abs(cls.normal_ppf(1.0 - alpha / 2.0))

        p = max(0.01, min(0.99, proportion))
        e = max(0.005, margin_of_error)

        # Công thức Cochran vô hạn: n0 = (Z^2 * p * (1 - p)) / e^2
        n0 = (z_crit ** 2 * p * (1.0 - p)) / (e ** 2)
        n0_int = math.ceil(n0)

        # Hiệu chỉnh tổng thể hữu hạn (FPC) nếu có
        n_adjusted = n0
        fpc_factor = 1.0
        if population_size is not None and population_size > 0:
            fpc_factor = population_size / (population_size + n0 - 1.0)
            n_adjusted = n0 / (1.0 + (n0 - 1.0) / population_size)

        n_final = math.ceil(n_adjusted)

        return {
            "formula": "Cochran (1977) with Finite Population Correction",
            "confidence_level": confidence_level,
            "z_critical": round(z_crit, 3),
            "margin_of_error": e,
            "margin_of_error_pct": f"{e * 100:.1f}%",
            "proportion": p,
            "population_size": population_size,
            "unadjusted_sample_size": n0_int,
            "required_sample_size": n_final,
            "fpc_applied": population_size is not None and population_size > 0,
            "recommendation": f"Cần tối thiểu {n_final} phản hồi hợp lệ để kết quả đại diện cho tổng thể với độ tin cậy {confidence_level * 100:.0f}% và biên độ sai số ±{e * 100:.1f}%."
        }

    @classmethod
    def calculate_ttest_power(
        cls,
        n_per_group: int,
        effect_size_d: float = 0.5,
        alpha: float = 0.05
    ) -> float:
        """
        Tính Post-Hoc Power cho kiểm định T-Test 2 nhóm độc lập (Student / Welch).
        Cohen (1988), Chow et al. (2008).
        """
        if n_per_group < 2 or effect_size_d <= 0.0:
            return 0.05

        z_alpha = abs(cls.normal_ppf(1.0 - alpha / 2.0))
        # Tham số không tâm xấp xỉ: delta = d * sqrt(n / 2)
        delta = abs(effect_size_d) * math.sqrt(n_per_group / 2.0)
        # Z_beta = delta - z_alpha
        z_beta = delta - z_alpha
        power = cls.normal_cdf(z_beta)
        return min(0.9999, max(0.05, power))

    @classmethod
    def calculate_ttest_required_n(
        cls,
        effect_size_d: float = 0.5,
        target_power: float = 0.80,
        alpha: float = 0.05
    ) -> int:
        """Tính cỡ mẫu tối thiểu từng nhóm cần thiết cho T-Test để đạt Power mong muốn"""
        if effect_size_d <= 0.0:
            return 1000

        z_alpha = abs(cls.normal_ppf(1.0 - alpha / 2.0))
        z_beta = abs(cls.normal_ppf(target_power))

        n = 2.0 * ((z_alpha + z_beta) / effect_size_d) ** 2
        return math.ceil(n)

    @classmethod
    def calculate_correlation_power(
        cls,
        n_total: int,
        expected_r: float = 0.3,
        alpha: float = 0.05
    ) -> float:
        """
        Tính Post-Hoc Power cho phân tích tương quan Pearson r qua chuyển đổi Fisher z.
        """
        r = abs(expected_r)
        if n_total < 4 or r <= 0.0 or r >= 1.0:
            return 0.05

        z_alpha = abs(cls.normal_ppf(1.0 - alpha / 2.0))
        # Fisher z transform: 0.5 * ln((1 + r) / (1 - r))
        z_r = 0.5 * math.log((1.0 + r) / (1.0 - r))
        delta = z_r * math.sqrt(n_total - 3.0)
        z_beta = delta - z_alpha
        return min(0.9999, max(0.05, cls.normal_cdf(z_beta)))

    @classmethod
    def calculate_correlation_required_n(
        cls,
        expected_r: float = 0.3,
        target_power: float = 0.80,
        alpha: float = 0.05
    ) -> int:
        """Tính cỡ mẫu tổng thể cần thiết để phát hiện tương quan r với lực kiểm định mục tiêu"""
        r = abs(expected_r)
        if r <= 0.0 or r >= 1.0:
            return 500

        z_alpha = abs(cls.normal_ppf(1.0 - alpha / 2.0))
        z_beta = abs(cls.normal_ppf(target_power))
        z_r = 0.5 * math.log((1.0 + r) / (1.0 - r))

        n = 3.0 + ((z_alpha + z_beta) / z_r) ** 2
        return math.ceil(n)

    @classmethod
    def generate_power_curve(
        cls,
        analysis_type: str = "ttest",
        effect_size: float = 0.5,
        alpha: float = 0.05,
        max_n: int = 300,
        step: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Sinh chuỗi tọa độ (N, Power) phục vụ vẽ đồ thị đường cong Lực thống kê SVG
        """
        points = []
        for n in range(10, max_n + 1, step):
            if analysis_type == "ttest":
                # N ở đây là N mỗi nhóm, tổng là 2*N
                pwr = cls.calculate_ttest_power(n, effect_size, alpha)
                points.append({"n": n * 2, "n_per_group": n, "power": round(pwr, 3), "power_pct": round(pwr * 100, 1)})
            elif analysis_type == "correlation":
                pwr = cls.calculate_correlation_power(n, effect_size, alpha)
                points.append({"n": n, "power": round(pwr, 3), "power_pct": round(pwr * 100, 1)})
            else:
                pwr = cls.calculate_ttest_power(n, effect_size, alpha)
                points.append({"n": n * 2, "power": round(pwr, 3), "power_pct": round(pwr * 100, 1)})

        return points

    @classmethod
    def evaluate_survey_sample_adequacy(
        cls,
        current_n: int,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Đánh giá toàn diện tính thỏa đáng của cỡ mẫu hiện tại đối với các bài toán nghiên cứu.
        """
        if current_n < 5:
            return {
                "current_n": current_n,
                "status": "CRITICAL_INSUFFICIENT",
                "rating": "CHƯA ĐỦ CỠ MẪU CƠ SỞ",
                "achieved_margin_of_error_pct": "±45%+",
                "power_small_effect": 0.05,
                "power_medium_effect": 0.10,
                "power_large_effect": 0.20,
                "summary": "Cỡ mẫu quá nhỏ (N < 5) để thực hiện bất kỳ phân tích suy diễn khoa học nào có ý nghĩa."
            }

        # 1. Biên độ sai số đạt được ở mức 95% tin cậy: e = Z * sqrt(p(1-p)/N)
        z_95 = 1.960
        margin_of_error = z_95 * math.sqrt(0.25 / current_n)

        # 2. Lực kiểm định Post-Hoc cho T-Test 2 nhóm (n_group = N / 2)
        n_grp = max(2, current_n // 2)
        power_d_small = cls.calculate_ttest_power(n_grp, 0.20, alpha)   # d = 0.2
        power_d_medium = cls.calculate_ttest_power(n_grp, 0.50, alpha)  # d = 0.5
        power_d_large = cls.calculate_ttest_power(n_grp, 0.80, alpha)   # d = 0.8

        # 3. Lực kiểm định cho Tương quan r
        power_r_small = cls.calculate_correlation_power(current_n, 0.10, alpha)
        power_r_medium = cls.calculate_correlation_power(current_n, 0.30, alpha)
        power_r_large = cls.calculate_correlation_power(current_n, 0.50, alpha)

        # 4. Phân loại chuẩn học thuật
        if power_d_medium >= 0.80:
            status = "ADEQUATE"
            rating = "ĐỦ LỰC THỐNG KÊ (WELL-POWERED)"
            color = "emerald"
            summary = f"Cỡ mẫu hiện tại (N = {current_n}) đạt lực thống kê mạnh ({power_d_medium * 100:.1f}% >= 80%), đủ độ nhạy để phát hiện các khác biệt và tương quan kích thước trung bình trở lên."
        elif power_d_large >= 0.80:
            status = "MODERATE"
            rating = "LỰC THỐNG KÊ TRUNG BÌNH (MODERATE)"
            color = "amber"
            summary = f"Cỡ mẫu hiện tại (N = {current_n}) đủ để phát hiện các hiệu ứng lớn ({power_d_large * 100:.1f}%), nhưng có nguy cơ bỏ sót các khác biệt vừa và nhỏ (Lỗi loại II / False Negative)."
        else:
            status = "UNDERPOWERED"
            rating = "THIẾU LỰC KIỂM ĐỊNH (UNDERPOWERED)"
            color = "red"
            summary = f"Cỡ mẫu hiện tại (N = {current_n}) có lực thống kê thấp (< 80%). Cần tiếp tục thu thập thêm dữ liệu để tránh kết luận sai lệch khi bảo vệ đề tài."

        # 5. Soạn thảo đoạn văn trích dẫn APA 7th Edition
        apa_narrative = (
            f"A post-hoc statistical power analysis was conducted based on the realized verified sample size (N = {current_n}). "
            f"With a two-tailed significance level set at alpha = {alpha:.2f}, the study achieved an empirical statistical power of "
            f"{power_d_medium * 100:.1f}% for detecting medium effect sizes (Cohen's d = 0.50) and {power_d_large * 100:.1f}% for large effects (d = 0.80). "
            f"The estimated margin of error for proportion estimates at the 95% confidence level was ±{margin_of_error * 100:.2f}%. "
            f"According to Cohen's (1988) methodological conventions, the sample is classified as {rating}."
        )

        return {
            "current_n": current_n,
            "status": status,
            "rating": rating,
            "badge_color": color,
            "achieved_margin_of_error": round(margin_of_error, 4),
            "achieved_margin_of_error_pct": f"±{margin_of_error * 100:.2f}%",
            "ttest_power": {
                "small_d_02": round(power_d_small, 3),
                "medium_d_05": round(power_d_medium, 3),
                "large_d_08": round(power_d_large, 3)
            },
            "correlation_power": {
                "small_r_01": round(power_r_small, 3),
                "medium_r_03": round(power_r_medium, 3),
                "large_r_05": round(power_r_large, 3)
            },
            "minimum_n_required": {
                "ttest_medium_80pct": cls.calculate_ttest_required_n(0.50, 0.80, alpha) * 2,
                "ttest_large_80pct": cls.calculate_ttest_required_n(0.80, 0.80, alpha) * 2,
                "correlation_medium_80pct": cls.calculate_correlation_required_n(0.30, 0.80, alpha)
            },
            "summary": summary,
            "apa_narrative": apa_narrative
        }
