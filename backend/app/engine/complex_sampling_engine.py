"""
Complex Survey Sampling Design & Weighting Analysis Engine.
Horvitz-Thompson Ratio Estimator & Taylor Series Linearization Variance Estimation.

Cơ sở phương pháp luận học thuật:
- Horvitz, D. G., & Thompson, D. J. (1952). A generalization of sampling without replacement from a finite universe. JASA, 47(260), 663-685.
- Cochran, W. G. (1977). Sampling Techniques (3rd ed.). John Wiley & Sons.
- Kish, L. (1965). Survey Sampling. John Wiley & Sons.
- Wolter, K. M. (2007). Introduction to Variance Estimation (2nd ed.). Springer.
- Heeringa, S. G., West, B. T., & Berglund, P. A. (2017). Applied Survey Data Analysis (2nd ed.). CRC Press / Chapman & Hall.
"""

import math
from typing import Dict, List, Any, Optional, Tuple


class ComplexSamplingEngine:
    @staticmethod
    def _t_critical_95(df: float) -> float:
        """Giá trị tới hạn t ở mức ý nghĩa alpha = 0.05 (2-tailed) theo bậc tự do df."""
        if df >= 120.0:
            return 1.960
        if df <= 1.0:
            return 12.706
        t_table = {
            2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
            10: 2.228, 12: 2.179, 14: 2.145, 16: 2.120, 18: 2.101, 20: 2.086, 25: 2.060,
            30: 2.042, 40: 2.021, 50: 2.009, 60: 2.000, 80: 1.990, 100: 1.984
        }
        int_df = int(round(df))
        if int_df in t_table:
            return t_table[int_df]
        keys = sorted(t_table.keys())
        for idx in range(len(keys) - 1):
            if keys[idx] <= int_df <= keys[idx + 1]:
                k1, k2 = keys[idx], keys[idx + 1]
                v1, v2 = t_table[k1], t_table[k2]
                return v1 + (v2 - v1) * (int_df - k1) / (k2 - k1)
        return 1.960

    @classmethod
    def analyze_complex_design(
        cls,
        records: List[Dict[str, Any]],
        target_title: str = "Biến mục tiêu Y",
        cluster_title: str = "Cụm (PSU)",
        stratum_title: Optional[str] = "Phân tầng (Stratum)",
        weight_title: Optional[str] = "Trọng số (Weight)"
    ) -> Dict[str, Any]:
        """
        Thực thi phân tích thiết kế mẫu phức hợp hai giai đoạn (Two-Stage Cluster Sampling):
        1. Ước lượng Trung bình và Tổng có trọng số Horvitz-Thompson.
        2. Ước lượng Sai số chuẩn phức hợp bằng Tuyến tính hóa chuỗi Taylor (Taylor Series Linearization).
        3. Tính toán Hiệu ứng thiết kế (DEFF, DEFT) và Hệ số tương quan nội cụm (ICC / Kish's roh).
        4. Xác định Cỡ mẫu hiệu dụng (Effective Sample Size n_eff) và độ suy giảm hiệu quả do gom cụm.
        5. So sánh với Giả định Lấy mẫu ngẫu nhiên đơn giản (SRS).
        6. Tự động sinh đoạn trích chuẩn học thuật APA 7th Edition.
        """
        # 1. Lọc và kiểm định dữ liệu đầu vào
        valid_records = []
        for r in records:
            y_raw = r.get("target_val")
            c_raw = r.get("cluster_val")
            s_raw = r.get("stratum_val", "Stratum_1")
            w_raw = r.get("weight_val", 1.0)

            if y_raw is None or c_raw is None:
                continue
            try:
                y = float(y_raw)
                w = float(w_raw) if w_raw is not None else 1.0
                if w <= 0.0 or math.isnan(w) or math.isinf(w):
                    w = 1.0
                c = str(c_raw).strip()
                s = str(s_raw).strip() if s_raw else "Stratum_1"
                if not c:
                    continue
                valid_records.append({"y": y, "c": c, "s": s, "w": w})
            except (ValueError, TypeError):
                continue

        n = len(valid_records)
        if n < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N = {n}) không đủ để phân tích thiết kế mẫu phức hợp (tối thiểu N >= 5)."
            }

        # 2. Kiểm tra phương sai biến mục tiêu
        y_vals = [r["y"] for r in valid_records]
        mean_raw = sum(y_vals) / n
        var_raw = sum((y - mean_raw) ** 2 for y in y_vals) / (n - 1)
        if var_raw < 1e-7:
            return {
                "status": "ZERO_VARIANCE",
                "message": "Biến mục tiêu không có phương sai (tất cả các quan sát đều mang giá trị tương đương)."
            }

        # 3. Phân nhóm theo Tầng (Stratum) và Cụm (PSU)
        strata_dict: Dict[str, Dict[str, List[Dict[str, float]]]] = {}
        all_psus = set()
        for r in valid_records:
            s = r["s"]
            c = r["c"]
            all_psus.add((s, c))
            if s not in strata_dict:
                strata_dict[s] = {}
            if c not in strata_dict[s]:
                strata_dict[s][c] = []
            strata_dict[s][c].append({"y": r["y"], "w": r["w"]})

        num_strata = len(strata_dict)
        total_psus = len(all_psus)

        if total_psus < 2:
            return {
                "status": "INSUFFICIENT_CLUSTERS",
                "message": f"Số lượng đơn vị lấy mẫu cấp 1 (PSU/Cụm) tìm thấy là {total_psus}. Thiết kế mẫu cụm yêu cầu tối thiểu 2 cụm độc lập để ước lượng phương sai nội tầng/liên tầng."
            }

        # Bậc tự do mẫu phức hợp: df = sum(n_h - 1) = total_psus - num_strata
        df_complex = max(1, total_psus - num_strata)

        # 4. Ước lượng Horvitz-Thompson: Tổng và Trung bình có trọng số
        sum_weights = sum(r["w"] for r in valid_records)
        sum_wy = sum(r["w"] * r["y"] for r in valid_records)
        y_bar_weighted = sum_wy / sum_weights

        # Thống kê phân phối trọng số
        w_vals = [r["w"] for r in valid_records]
        w_mean = sum_weights / n
        w_var = sum((w - w_mean) ** 2 for w in w_vals) / (n - 1) if n > 1 else 0.0
        w_sd = math.sqrt(w_var)
        cv_weights = (w_sd / w_mean) if w_mean > 0 else 0.0
        # Kish's weighting design effect: deff_w = 1 + cv^2 = n * sum(w^2) / (sum w)^2
        sum_w_sq = sum(w ** 2 for w in w_vals)
        deff_weight_only = (n * sum_w_sq) / (sum_weights ** 2) if sum_weights > 0 else 1.0

        # Thống kê phân phối kích thước cụm (Cluster sizes)
        cluster_sizes = []
        for s, clusters in strata_dict.items():
            for c, obs in clusters.items():
                cluster_sizes.append(len(obs))

        m_bar = n / total_psus  # Kích thước cụm trung bình
        m_var = sum((m - m_bar) ** 2 for m in cluster_sizes) / (len(cluster_sizes) - 1) if len(cluster_sizes) > 1 else 0.0
        m_sd = math.sqrt(m_var)
        cv_cluster_size = (m_sd / m_bar) if m_bar > 0 else 0.0

        # 5. Tuyến tính hóa chuỗi Taylor ước lượng Phương sai Phức hợp (Taylor Series Linearization)
        # Biến số tuyến tính hóa tỷ số (Taylor linearized proxy):
        # z_{hij} = w_{hij} * (y_{hij} - y_bar_w) / sum_weights
        # z_{hi.} = sum_{j} z_{hij}
        # z_bar_{h..} = (1 / n_h) * sum_{i=1}^{n_h} z_{hi.}
        # v_h = (n_h / (n_h - 1)) * sum_{i=1}^{n_h} (z_{hi.} - z_bar_{h..})^2
        var_complex = 0.0
        lonely_psu_detected = False

        cluster_details: List[Dict[str, Any]] = []

        for s, clusters in strata_dict.items():
            n_h = len(clusters)
            # Tính z_{hi.} cho từng cụm trong tầng
            z_cluster_totals: List[float] = []
            for c, obs in clusters.items():
                c_sum_z = sum((r["w"] * (r["y"] - y_bar_weighted)) / sum_weights for r in obs)
                c_sum_w = sum(r["w"] for r in obs)
                c_mean_y = sum(r["w"] * r["y"] for r in obs) / c_sum_w if c_sum_w > 0 else 0.0
                z_cluster_totals.append(c_sum_z)

                cluster_details.append({
                    "stratum": s,
                    "cluster_id": c,
                    "sample_size": len(obs),
                    "sum_weights": round(c_sum_w, 3),
                    "cluster_mean": round(c_mean_y, 3),
                    "deviation_from_mean": round(c_mean_y - y_bar_weighted, 3)
                })

            if n_h > 1:
                z_bar_h = sum(z_cluster_totals) / n_h
                ss_h = sum((z_hi - z_bar_h) ** 2 for z_hi in z_cluster_totals)
                v_h = (n_h / (n_h - 1)) * ss_h
            else:
                # Lonely PSU: 1 cụm trong tầng -> quy ước chuẩn thế giới (center at zero / overall mean)
                lonely_psu_detected = True
                v_h = sum(z_hi ** 2 for z_hi in z_cluster_totals)

            var_complex += v_h

        se_complex = math.sqrt(max(1e-12, var_complex))

        # 6. Chuẩn ngẫu nhiên đơn giản (Simple Random Sampling - SRS Benchmark)
        # v_srs = var_raw / n
        var_srs = var_raw / n
        se_srs = math.sqrt(max(1e-12, var_srs))

        # 7. Hiệu ứng Thiết kế (Design Effect - DEFF, DEFT) và Tương quan nội cụm (ICC)
        deff = var_complex / var_srs if var_srs > 0 else 1.0
        deft = math.sqrt(max(0.0, deff))

        # Intraclass Correlation Coefficient (ICC / Kish's Roh):
        # DEFF = 1 + (m_bar - 1) * ICC -> ICC = (DEFF - 1) / (m_bar - 1)
        if m_bar > 1.0:
            icc = (deff - 1.0) / (m_bar - 1.0)
            icc = max(-0.1, min(1.0, icc))
        else:
            icc = 0.0

        # Cỡ mẫu hiệu dụng (Effective Sample Size):
        # n_eff = n / DEFF
        n_effective = n / deff if deff > 0 else float(n)
        efficiency_loss_pct = max(0.0, ((n - n_effective) / n) * 100.0)

        # 8. Khoảng tin cậy 95% phức hợp vs SRS
        t_crit = cls._t_critical_95(float(df_complex))
        margin_of_error_complex = t_crit * se_complex
        ci_lower_complex = y_bar_weighted - margin_of_error_complex
        ci_upper_complex = y_bar_weighted + margin_of_error_complex

        margin_of_error_srs = 1.960 * se_srs
        ci_lower_srs = y_bar_weighted - margin_of_error_srs
        ci_upper_srs = y_bar_weighted + margin_of_error_srs

        # Phân loại mức độ hiệu ứng thiết kế (Design Effect Impact)
        if deff < 1.05:
            deff_rating = "KHÔNG ĐÁNG KỂ"
            deff_desc = "Tác động gom cụm rất thấp (DEFF ~ 1.0). Mẫu cụm có độ chính xác gần như tương đương lấy mẫu ngẫu nhiên đơn giản."
        elif deff <= 1.50:
            deff_rating = "VỪA PHẢI"
            deff_desc = "Hiệu ứng thiết kế ở mức chấp nhận được trong điều tra xã hội học (1.0 < DEFF <= 1.5). Sai số chuẩn tăng nhẹ."
        elif deff <= 2.50:
            deff_rating = "ĐÁNG CHÚ Ý"
            deff_desc = "Độ tương đồng trong cùng cụm làm giảm phương sai hiệu dụng (1.5 < DEFF <= 2.5). Cần duy trì hiệu chỉnh trọng số phức hợp."
        else:
            deff_rating = "CAO NGUY CƠ"
            deff_desc = "Hiệu ứng gom cụm rất lớn (DEFF > 2.5). Phương sai mẫu thực tế cao gấp nhiều lần so với SRS, cần mở rộng số lượng cụm (PSU) trong các đợt khảo sát tiếp theo."

        # 9. Đoạn trích APA 7th Edition
        apa_narrative = (
            f"Phân tích mẫu khảo sát phức hợp hai giai đoạn (Two-Stage Complex Survey Design) được thực hiện "
            f"cho biến mục tiêu '{target_title}' với cỡ mẫu N = {n} quan sát, phân bổ trên {num_strata} phân tầng "
            f"và {total_psus} đơn vị lấy mẫu cấp 1 (PSU/{cluster_title}), kích thước cụm trung bình m = {m_bar:.2f} "
            f"(SD = {m_sd:.2f}, CV = {cv_cluster_size:.2f}). "
            f"Ước lượng trung bình có trọng số Horvitz-Thompson đạt M = {y_bar_weighted:.3f} "
            f"(so với trung bình không trọng số M = {mean_raw:.3f}, độ lệch trọng số Delta M = {y_bar_weighted - mean_raw:+.3f}). "
            f"Sai số chuẩn hiệu chỉnh qua Tuyến tính hóa chuỗi Taylor (Taylor Series Linearization, df = {df_complex}) "
            f"đạt SE = {se_complex:.4f} (95% CI [{ci_lower_complex:.3f}, {ci_upper_complex:.3f}]), "
            f"so với SE = {se_srs:.4f} nếu giả định lấy mẫu ngẫu nhiên đơn giản (SRS). "
            f"Hiệu ứng thiết kế tổng hợp đạt DEFF = {deff:.3f} (DEFT = {deft:.3f}), "
            f"hệ số tương quan nội cụm đạt ICC (Kish's rho) = {icc:.4f}. "
            f"Cỡ mẫu hiệu dụng thực tế tương đương n_eff = {n_effective:.1f} quan sát "
            f"(suy giảm {efficiency_loss_pct:.1f}% hiệu năng do hiệu ứng đồng nhất nội cụm)."
        )

        return {
            "status": "SUCCESS",
            "sample_size": n,
            "strata_count": num_strata,
            "psu_count": total_psus,
            "degrees_of_freedom": df_complex,
            "cluster_size_summary": {
                "mean_size": round(m_bar, 2),
                "std_size": round(m_sd, 2),
                "min_size": min(cluster_sizes),
                "max_size": max(cluster_sizes),
                "cv_size": round(cv_cluster_size, 3)
            },
            "weight_summary": {
                "total_population_estimate": round(sum_weights, 2),
                "mean_weight": round(w_mean, 3),
                "std_weight": round(w_sd, 3),
                "cv_weight": round(cv_weights, 3),
                "kish_weight_deff": round(deff_weight_only, 3)
            },
            "horvitz_thompson_estimates": {
                "weighted_mean": round(y_bar_weighted, 4),
                "unweighted_mean": round(mean_raw, 4),
                "weighting_bias_shift": round(y_bar_weighted - mean_raw, 4),
                "weighted_total": round(sum_wy, 2)
            },
            "taylor_linearization_variance": {
                "complex_variance": round(var_complex, 6),
                "complex_se": round(se_complex, 4),
                "t_critical_95": round(t_crit, 3),
                "ci_95_lower": round(ci_lower_complex, 4),
                "ci_95_upper": round(ci_upper_complex, 4),
                "margin_of_error": round(margin_of_error_complex, 4),
                "lonely_psu_detected": lonely_psu_detected
            },
            "srs_comparison": {
                "srs_variance": round(var_srs, 6),
                "srs_se": round(se_srs, 4),
                "ci_95_lower": round(ci_lower_srs, 4),
                "ci_95_upper": round(ci_upper_srs, 4),
                "se_inflation_ratio": round(se_complex / se_srs, 3) if se_srs > 0 else 1.0
            },
            "design_effects": {
                "deff": round(deff, 3),
                "deft": round(deft, 3),
                "icc": round(icc, 4),
                "effective_sample_size": round(n_effective, 1),
                "efficiency_loss_pct": round(efficiency_loss_pct, 1),
                "rating": deff_rating,
                "interpretation": deff_desc
            },
            "clusters_breakdown": cluster_details[:50],  # Top 50 cụm đại diện
            "apa_narrative": apa_narrative
        }
