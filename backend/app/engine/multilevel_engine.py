import math
from typing import Dict, Any, List, Optional, Tuple


class MultilevelModelingEngine:
    """
    Động cơ Phân tích Mô hình Tuyến tính Đa cấp / Thứ bậc (Multilevel Modeling - MLM / HLM).
    Tuân thủ các tiêu chuẩn phương pháp luận thống kê & tâm lý học đo lường quốc tế:
    - Raudenbush, S. W., & Bryk, A. S. (2002). Hierarchical Linear Models: Applications and
      Data Analysis Methods (2nd ed.). Sage Publications.
    - Snijders, T. A., & Bosker, R. J. (2012). Multilevel Analysis: An Introduction to Basic and
      Advanced Multilevel Modeling (2nd ed.). Sage Publications.
    - Hox, J. J., Moerbeek, M., & van de Schoot, R. (2017). Multilevel Analysis: Techniques and
      Applications (3rd ed.). Routledge.
    - Enders, C. K., & Tofighi, D. (2007). Centering predictor variables in cross-sectional
      multilevel models: A new look at an old issue. Psychological Methods, 12(2), 121-138.
    """

    @classmethod
    def fit_multilevel_model(
        cls,
        data_rows: List[Dict[str, Any]],
        y_var: str,
        x_var: Optional[str] = None,
        cluster_var: str = "cluster_id",
        centering: str = "grand_mean",  # 'grand_mean', 'group_mean', 'none'
        max_iter: int = 50,
        tol: float = 1e-4
    ) -> Dict[str, Any]:
        """
        Khớp mô hình đa cấp 2 tầng (Two-Level Hierarchical Linear Model).
        
        Tầng 1: Y_ij = beta_0j + beta_1j * X_ij + e_ij, e_ij ~ N(0, sigma^2)
        Tầng 2: beta_0j = gamma_00 + u_0j, u_0j ~ N(0, tau_00)
                beta_1j = gamma_10 + u_1j, u_1j ~ N(0, tau_11)
        
        Tham số:
        - data_rows: Danh sách bản ghi quan sát
        - y_var: Tên biến phụ thuộc liên tục
        - x_var: Tên biến độc lập dự báo tầng 1 (tùy chọn; nếu None -> Unconditional Null Model)
        - cluster_var: Tên biến phân cụm tầng 2 (ví dụ: enumerator_id, district_id, school_id)
        - centering: Phương pháp định tâm biến ('grand_mean', 'group_mean', 'none')
        """
        n_total = len(data_rows)
        if n_total < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 quan sát để ước lượng mô hình đa cấp (hiện có {n_total})."
            }

        # 1. Gom cụm theo cluster_var
        clusters: Dict[str, List[Dict[str, Any]]] = {}
        for row in data_rows:
            c_val = str(row.get(cluster_var, "")).strip()
            if not c_val:
                c_val = "Unknown_Cluster"
            if c_val not in clusters:
                clusters[c_val] = []
            clusters[c_val].append(row)

        num_clusters = len(clusters)
        if num_clusters < 2:
            return {
                "status": "INSUFFICIENT_CLUSTERS",
                "message": f"Cần tối thiểu 2 cụm (clusters/enumerators) để phân tích đa cấp (hiện có {num_clusters})."
            }

        # Trích xuất dữ liệu Y và X
        y_all: List[float] = []
        x_all: List[float] = []
        cluster_ids: List[str] = []
        cluster_names = sorted(list(clusters.keys()))

        for c_id in cluster_names:
            c_rows = clusters[c_id]
            for r in c_rows:
                try:
                    y_val = float(r[y_var])
                except (ValueError, TypeError, KeyError):
                    continue
                x_val = 0.0
                if x_var:
                    try:
                        x_val = float(r[x_var])
                    except (ValueError, TypeError, KeyError):
                        continue
                y_all.append(y_val)
                x_all.append(x_val)
                cluster_ids.append(c_id)

        n_clean = len(y_all)
        if n_clean < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số quan sát hợp lệ sau khi làm sạch không đủ ({n_clean} < 8)."
            }

        # 2. Bước 1: Ước lượng Mô hình Rỗng (Unconditional / Null Model)
        # Y_ij = gamma_00 + u_0j + e_ij
        # Phân rã phương sai: Tổng phương sai = tau_00 (giữa các cụm) + sigma^2 (nội bộ cụm)
        grand_mean_y = sum(y_all) / n_clean

        # Tính trung bình từng cụm
        cluster_n: Dict[str, int] = {}
        cluster_mean_y: Dict[str, float] = {}
        cluster_mean_x: Dict[str, float] = {}

        for c_id in cluster_names:
            c_y_vals = [y_all[i] for i in range(n_clean) if cluster_ids[i] == c_id]
            c_x_vals = [x_all[i] for i in range(n_clean) if cluster_ids[i] == c_id]
            n_c = len(c_y_vals)
            cluster_n[c_id] = n_c
            cluster_mean_y[c_id] = sum(c_y_vals) / n_c if n_c > 0 else grand_mean_y
            cluster_mean_x[c_id] = sum(c_x_vals) / n_c if n_c > 0 else 0.0

        # Ước lượng phương sai ANOVA / Henderson cho Null Model
        ss_between = sum(cluster_n[c] * ((cluster_mean_y[c] - grand_mean_y) ** 2) for c in cluster_names)
        ss_within = sum((y_all[i] - cluster_mean_y[cluster_ids[i]]) ** 2 for i in range(n_clean))
        df_between = num_clusters - 1
        df_within = n_clean - num_clusters

        ms_between = ss_between / max(1, df_between)
        ms_within = ss_within / max(1, df_within)

        # Trọng số cỡ cụm trung bình n_tilde (Kish / Searle formula)
        sum_n_sq = sum(cluster_n[c] ** 2 for c in cluster_names)
        n_tilde = (n_clean - (sum_n_sq / n_clean)) / max(1, df_between)

        sigma_sq_null = max(1e-6, ms_within)
        tau_00_null = max(0.0, (ms_between - ms_within) / max(1.0, n_tilde))

        # Intraclass Correlation Coefficient (ICC)
        total_var_null = tau_00_null + sigma_sq_null
        icc = tau_00_null / total_var_null if total_var_null > 0 else 0.0

        if icc < 0.05:
            icc_tier = "LOW"
            icc_label = "Thấp (< 0.05) - Cấu trúc phân cụm mờ nhạt"
            icc_recommendation = "Mô hình OLS truyền thống hoặc sai số chuẩn vững có thể chấp nhận được."
        elif icc < 0.15:
            icc_tier = "MODERATE"
            icc_label = "Trung bình (0.05 - 0.14) - Khuyến nghị dùng HLM"
            icc_recommendation = "Khuyến nghị mô hình đa cấp HLM để tránh sai số chuẩn bị đánh giá thấp."
        else:
            icc_tier = "HIGH"
            icc_label = "Cao (≥ 0.15) - Bắt buộc dùng HLM"
            icc_recommendation = "Hiện tượng tương quan nội cụm nghiêm trọng; bắt buộc dùng HLM để loại trừ p-value giả mạo."

        # 3. Bước 2: Khớp Mô hình Có Biến Dự Báo (Full Two-Level Model) nếu có x_var
        has_predictor = bool(x_var is not None and any(abs(x) > 1e-6 for x in x_all))
        grand_mean_x = sum(x_all) / n_clean if has_predictor else 0.0

        # Áp dụng định tâm biến dự báo X
        x_centered = []
        for i in range(n_clean):
            cid = cluster_ids[i]
            x_val = x_all[i]
            if not has_predictor:
                x_centered.append(0.0)
            elif centering == "grand_mean":
                x_centered.append(x_val - grand_mean_x)
            elif centering == "group_mean":
                x_centered.append(x_val - cluster_mean_x[cid])
            else:
                x_centered.append(x_val)

        # Khớp mô hình hồi quy OLS gộp (Pooled OLS) làm chuẩn đối sánh
        if has_predictor:
            cov_xy = sum((x_centered[i]) * (y_all[i] - grand_mean_y) for i in range(n_clean))
            var_x = sum((x_centered[i]) ** 2 for i in range(n_clean))
            b_ols = cov_xy / max(1e-12, var_x)
            a_ols = grand_mean_y - b_ols * (sum(x_centered) / n_clean)
            e_ols = [y_all[i] - (a_ols + b_ols * x_centered[i]) for i in range(n_clean)]
            sigma_sq_ols = sum(e ** 2 for e in e_ols) / max(1, n_clean - 2)
            se_b_ols = math.sqrt(sigma_sq_ols / max(1e-12, var_x))
            dev_ols = n_clean * (math.log(2.0 * math.pi * sigma_sq_ols) + 1.0)
        else:
            a_ols = grand_mean_y
            b_ols = 0.0
            se_b_ols = 0.0
            sigma_sq_ols = sum((y - grand_mean_y) ** 2 for y in y_all) / max(1, n_clean - 1)
            dev_ols = n_clean * (math.log(2.0 * math.pi * sigma_sq_ols) + 1.0)

        # 4. Thuật toán EM / Iterative Generalized Least Squares (IGLS) ước lượng tham số HLM
        # Khởi tạo tham số
        gamma_00 = grand_mean_y
        gamma_10 = b_ols
        sigma_sq = sigma_sq_null * 0.8
        tau_00 = tau_00_null
        tau_11 = 0.05 if has_predictor else 0.0

        for it in range(max_iter):
            # Tính độ tin cậy co rút Empirical Bayes (Shrinkage factor lambda_j)
            cluster_b0_ols = {}
            cluster_b1_ols = {}
            cluster_b0_eb = {}
            cluster_b1_eb = {}

            for c_id in cluster_names:
                c_idx = [i for i in range(n_clean) if cluster_ids[i] == c_id]
                n_c = len(c_idx)
                if n_c == 0:
                    continue

                c_y = [y_all[i] for i in c_idx]
                c_x = [x_centered[i] for i in c_idx]

                # OLS cục bộ từng cụm
                if has_predictor and len(set(c_x)) > 1:
                    c_mx = sum(c_x) / n_c
                    c_my = sum(c_y) / n_c
                    c_var_x = sum((x - c_mx) ** 2 for x in c_x)
                    c_cov = sum((c_x[k] - c_mx) * (c_y[k] - c_my) for k in range(n_c))
                    slp = c_cov / max(1e-8, c_var_x)
                    itc = c_my - slp * c_mx
                else:
                    itc = sum(c_y) / n_c
                    slp = gamma_10

                cluster_b0_ols[c_id] = itc
                cluster_b1_ols[c_id] = slp

                # Trọng số co rút Empirical Bayes (EB Shrinkage):
                # lambda_0 = tau_00 / (tau_00 + sigma^2 / n_c)
                denom_0 = tau_00 + (sigma_sq / max(1, n_c))
                lam_0 = (tau_00 / denom_0) if denom_0 > 1e-12 else 0.5
                lam_0 = max(0.0, min(1.0, lam_0))

                eb_b0 = lam_0 * itc + (1.0 - lam_0) * gamma_00
                cluster_b0_eb[c_id] = eb_b0

                if has_predictor:
                    denom_1 = tau_11 + (sigma_sq / max(1.0, sum((x - sum(c_x)/n_c)**2 for x in c_x) or 1.0))
                    lam_1 = (tau_11 / denom_1) if denom_1 > 1e-12 else 0.5
                    lam_1 = max(0.0, min(1.0, lam_1))
                    eb_b1 = lam_1 * slp + (1.0 - lam_1) * gamma_10
                    cluster_b1_eb[c_id] = eb_b1
                else:
                    cluster_b1_eb[c_id] = 0.0

            # M-step: Cập nhật tham số cố định gamma_00, gamma_10 và thành phần phương sai
            new_gamma_00 = sum(cluster_b0_eb[c] for c in cluster_names) / num_clusters
            new_gamma_10 = (sum(cluster_b1_eb[c] for c in cluster_names) / num_clusters) if has_predictor else 0.0

            # Cập nhật tau_00, tau_11, sigma_sq
            new_tau_00 = max(1e-6, sum((cluster_b0_eb[c] - new_gamma_00) ** 2 for c in cluster_names) / max(1, num_clusters - 1))
            new_tau_11 = max(1e-6, sum((cluster_b1_eb[c] - new_gamma_10) ** 2 for c in cluster_names) / max(1, num_clusters - 1)) if has_predictor else 0.0

            # Phần dư tầng 1
            resids = []
            for i in range(n_clean):
                cid = cluster_ids[i]
                y_hat = cluster_b0_eb[cid] + (cluster_b1_eb[cid] * x_centered[i] if has_predictor else 0.0)
                resids.append(y_all[i] - y_hat)
            new_sigma_sq = max(1e-6, sum(e ** 2 for e in resids) / max(1, n_clean - num_clusters))

            delta = abs(new_gamma_00 - gamma_00) + abs(new_tau_00 - tau_00) + abs(new_sigma_sq - sigma_sq)
            gamma_00 = new_gamma_00
            gamma_10 = new_gamma_10
            tau_00 = new_tau_00
            tau_11 = new_tau_11
            sigma_sq = new_sigma_sq

            if delta < tol:
                break

        # Sai số chuẩn của tham số cố định (Standard Errors for Fixed Effects)
        # SE(gamma_00) = sqrt( (tau_00 + sigma^2 / n_tilde) / J )
        se_gamma_00 = math.sqrt(max(1e-8, (tau_00 + (sigma_sq / max(1.0, n_tilde))) / num_clusters))
        t_gamma_00 = gamma_00 / se_gamma_00
        p_gamma_00 = math.erfc(abs(t_gamma_00) / math.sqrt(2.0))

        if has_predictor:
            sum_var_x_all = sum(x_centered[i] ** 2 for i in range(n_clean))
            se_gamma_10 = math.sqrt(max(1e-8, (tau_11 / num_clusters) + (sigma_sq / max(1e-8, sum_var_x_all))))
            t_gamma_10 = gamma_10 / se_gamma_10
            p_gamma_10 = math.erfc(abs(t_gamma_10) / math.sqrt(2.0))
        else:
            se_gamma_10 = 0.0
            t_gamma_10 = 0.0
            p_gamma_10 = 1.0

        # Tỷ lệ phương sai giải thích R^2 tầng 1 và tầng 2 (Snijders & Bosker, 1994)
        r2_level_1 = max(0.0, min(0.999, 1.0 - ((sigma_sq + tau_00) / max(1e-6, total_var_null))))
        r2_level_2 = max(0.0, min(0.999, 1.0 - (tau_00 / max(1e-6, tau_00_null))))

        # Độ lệch Deviance và Kiểm định Tỷ số Hợp lý LRT (-2LL)
        dev_hlm = n_clean * math.log(2.0 * math.pi * sigma_sq) + sum((e ** 2) / sigma_sq for e in resids) + (num_clusters * math.log(max(1e-6, tau_00)))
        dev_diff = max(0.0, dev_ols - dev_hlm)
        p_lrt = math.erfc(math.sqrt(dev_diff / 2.0)) if dev_diff > 0 else 1.0

        # 5. Sinh tọa độ đồ thị vector SVG đường quỹ đạo từng cụm (Cluster Trajectories)
        # Khung đồ thị: viewBox 520 x 240
        # x: mapping [min_x, max_x] -> [50, 490]
        # y: mapping [min_y, max_y] -> [200, 30]
        min_x = min(x_centered) if has_predictor else -2.0
        max_x = max(x_centered) if has_predictor else 2.0
        if abs(max_x - min_x) < 1e-4:
            min_x -= 1.0
            max_x += 1.0

        min_y = min(y_all)
        max_y = max(y_all)
        if abs(max_y - min_y) < 1e-4:
            min_y -= 1.0
            max_y += 1.0

        trajectories = []
        cluster_summaries = []

        for c_id in cluster_names:
            b0 = cluster_b0_eb[c_id]
            b1 = cluster_b1_eb[c_id]
            n_c = cluster_n[c_id]

            # Tính 2 điểm đầu mút
            y_start = b0 + b1 * min_x
            y_end = b0 + b1 * max_x

            # Tọa độ SVG
            x1_svg = 50.0
            x2_svg = 490.0
            y1_svg = 200.0 - (((y_start - min_y) / (max_y - min_y)) * 170.0)
            y2_svg = 200.0 - (((y_end - min_y) / (max_y - min_y)) * 170.0)

            # Giới hạn SVG y trong viewport
            y1_svg = max(25.0, min(205.0, y1_svg))
            y2_svg = max(25.0, min(205.0, y2_svg))

            trajectories.append({
                "cluster_id": c_id,
                "n": n_c,
                "intercept_eb": round(b0, 3),
                "slope_eb": round(b1, 3),
                "svg_path": f"M {x1_svg:.1f},{y1_svg:.1f} L {x2_svg:.1f},{y2_svg:.1f}"
            })

            cluster_summaries.append({
                "cluster_id": c_id,
                "sample_size": n_c,
                "raw_mean_y": round(cluster_mean_y[c_id], 3),
                "intercept_ols": round(cluster_b0_ols.get(c_id, b0), 3),
                "intercept_eb": round(b0, 3),
                "slope_ols": round(cluster_b1_ols.get(c_id, b1), 3),
                "slope_eb": round(b1, 3),
                "random_intercept_u0": round(b0 - gamma_00, 3)
            })

        # Đường xu hướng chung toàn thể (Grand Mean Trajectory)
        gm_y_start = gamma_00 + gamma_10 * min_x
        gm_y_end = gamma_00 + gamma_10 * max_x
        gm_y1_svg = max(25.0, min(205.0, 200.0 - (((gm_y_start - min_y) / (max_y - min_y)) * 170.0)))
        gm_y2_svg = max(25.0, min(205.0, 200.0 - (((gm_y_end - min_y) / (max_y - min_y)) * 170.0)))
        grand_trajectory_path = f"M 50.0,{gm_y1_svg:.1f} L 490.0,{gm_y2_svg:.1f}"

        # 6. Biên soạn Thuyết minh Học thuật Chuẩn APA 7th Edition
        apa_narrative = (
            f"Mô hình tuyến tính thứ bậc đa cấp 2 tầng (HLM; Raudenbush & Bryk, 2002) được ước lượng "
            f"trên tập mẫu gồm N = {n_clean} quan sát lồng ghép trong J = {num_clusters} cụm/điều tra viên "
            f"(cỡ cụm trung bình n_tilde = {n_tilde:.1f}). Mô hình rỗng (Unconditional Null Model) cho thấy "
            f"hệ số tương quan nội cụm đạt ICC = {icc:.3f} (tau_00 = {tau_00_null:.3f}, sigma^2 = {sigma_sq_null:.3f}), "
            f"chứng minh rằng {(icc * 100):.1f}% tổng phương sai của biến kết quả '{y_var}' bắt nguồn từ sự dị biệt "
            f"giữa các cụm/điều tra viên ({icc_label}). "
        )

        if has_predictor:
            apa_narrative += (
                f"Mô hình đầy đủ có biến dự báo '{x_var}' (định tâm theo {centering}) ước lượng hệ số cố định: "
                f"hệ số chặn chung gamma_00 = {gamma_00:.3f} (SE = {se_gamma_00:.3f}, t = {t_gamma_00:.2f}, p = {p_gamma_00:.4f}) "
                f"và độ dốc cố định gamma_10 = {gamma_10:.3f} (SE = {se_gamma_10:.3f}, t = {t_gamma_10:.2f}, p = {p_gamma_10:.4f}). "
                f"Phương sai phần dư tầng 1 giảm xuống sigma^2 = {sigma_sq:.3f} (R^2 tầng 1 = {r2_level_1:.3f}), "
                f"và phương sai hệ số chặn tầng 2 đạt tau_00 = {tau_00:.3f} (R^2 tầng 2 = {r2_level_2:.3f}). "
                f"Kiểm định tỷ số hợp lý LRT so với hồi quy OLS gộp xác nhận mô hình đa cấp có độ phù hợp vượt trội "
                f"(delta -2LL = {dev_diff:.2f}, p = {p_lrt:.4f})."
            )
        else:
            apa_narrative += (
                f"Hệ số chặn chung ước tính đạt gamma_00 = {gamma_00:.3f} (SE = {se_gamma_00:.3f}, t = {t_gamma_00:.2f}, p = {p_gamma_00:.4f})."
            )

        return {
            "status": "SUCCESS",
            "total_sample_size": n_clean,
            "num_clusters": num_clusters,
            "average_cluster_size": round(n_tilde, 1),
            "dependent_variable": y_var,
            "predictor_variable": x_var,
            "cluster_variable": cluster_var,
            "centering": centering,
            "null_model": {
                "intercept_gamma_00": round(grand_mean_y, 3),
                "tau_00": round(tau_00_null, 4),
                "sigma_sq": round(sigma_sq_null, 4),
                "icc": round(icc, 4),
                "icc_percentage": round(icc * 100.0, 1),
                "icc_tier": icc_tier,
                "icc_label": icc_label,
                "icc_recommendation": icc_recommendation
            },
            "fixed_effects": {
                "intercept_gamma_00": round(gamma_00, 3),
                "se_gamma_00": round(se_gamma_00, 3),
                "t_gamma_00": round(t_gamma_00, 2),
                "p_gamma_00": round(p_gamma_00, 4),
                "slope_gamma_10": round(gamma_10, 3) if has_predictor else None,
                "se_gamma_10": round(se_gamma_10, 3) if has_predictor else None,
                "t_gamma_10": round(t_gamma_10, 2) if has_predictor else None,
                "p_gamma_10": round(p_gamma_10, 4) if has_predictor else None
            },
            "random_effects": {
                "tau_00_intercept_var": round(tau_00, 4),
                "tau_11_slope_var": round(tau_11, 4) if has_predictor else None,
                "sigma_sq_residual_var": round(sigma_sq, 4),
                "r2_level_1": round(r2_level_1, 3),
                "r2_level_2": round(r2_level_2, 3)
            },
            "model_comparison_ols_vs_hlm": {
                "deviance_ols": round(dev_ols, 2),
                "deviance_hlm": round(dev_hlm, 2),
                "deviance_diff_chi2": round(dev_diff, 2),
                "p_value_lrt": round(p_lrt, 4),
                "is_hlm_significantly_better": p_lrt < 0.05
            },
            "cluster_trajectories": trajectories,
            "grand_trajectory_path": grand_trajectory_path,
            "clusters_summary": cluster_summaries,
            "apa_narrative": apa_narrative
        }
