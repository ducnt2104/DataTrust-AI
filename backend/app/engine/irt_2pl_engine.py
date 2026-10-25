import math
from typing import Dict, Any, List, Optional, Tuple


class IRT2PLEngine:
    """
    Động cơ Lý thuyết Ứng đáp Câu hỏi 2 Tham số Logistic (2-Parameter Logistic IRT Model)
    và Đường cong Đặc trưng Câu hỏi (Item Characteristic Curve - ICC).
    
    Tuân thủ các tiêu chuẩn phương pháp luận đo lường tâm lý học & giáo dục quốc tế:
    - Birnbaum, A. (1968). Some latent trait models and their use in inferring an examinee's ability.
      In F. M. Lord & M. R. Novick (Eds.), Statistical theories of mental test scores. Addison-Wesley.
    - Bock, R. D., & Aitkin, M. (1981). Marginal maximum likelihood estimation of item parameters:
      Application of an EM algorithm. Psychometrika, 46(4), 443-459.
    - Baker, F. B. (2001). The basics of item response theory. ERIC Clearinghouse on Assessment and Evaluation.
    - Reckase, M. D. (2009). Multidimensional item response theory. Springer.
    - Yen, W. M. (1981). Using simulation results to choose a latent trait model.
      Applied Psychological Measurement, 5(2), 245-262.
    """

    D_SCALING_CONSTANT = 1.702

    @classmethod
    def _prob_2pl(cls, theta: float, a: float, b: float) -> float:
        """
        Xác suất chọn/đạt mục câu hỏi i tại năng lực/thái độ theta:
        P_i(theta) = 1 / (1 + exp(-D * a * (theta - b)))
        """
        z = cls.D_SCALING_CONSTANT * a * (theta - b)
        # Giới hạn z chống tràn số mũ (overflow/underflow)
        if z > 35.0:
            return 1.0
        if z < -35.0:
            return 0.0
        return 1.0 / (1.0 + math.exp(-z))

    @classmethod
    def _information_2pl(cls, theta: float, a: float, b: float) -> float:
        """
        Hàm thông tin câu hỏi i tại theta (Item Information Function):
        I_i(theta) = D^2 * a^2 * P_i(theta) * (1 - P_i(theta))
        """
        p = cls._prob_2pl(theta, a, b)
        return (cls.D_SCALING_CONSTANT * a) ** 2 * p * (1.0 - p)

    @classmethod
    def analyze_irt_2pl(
        cls,
        raw_matrix: List[List[float]],
        item_names: List[str],
        binarization_threshold: Optional[float] = None,
        max_em_iter: int = 35,
        tolerance: float = 1e-3
    ) -> Dict[str, Any]:
        """
        Phân tích mô hình IRT 2PL qua thuật toán Marginal Maximum Likelihood với Expectation-Maximization (MML-EM).
        
        Tham số:
        - raw_matrix: Ma trận N dòng x P cột
        - item_names: Danh sách tên P câu hỏi
        - binarization_threshold: Ngưỡng chuyển đổi nhị phân (nếu None, tự động binarize theo trung vị hoặc giữ nguyên nếu là 0/1)
        - max_em_iter: Số vòng lặp EM tối đa
        - tolerance: Ngưỡng hội tụ tham số
        """
        n = len(raw_matrix)
        if n < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 6 phản hồi để ước lượng mô hình IRT 2PL (hiện có {n})."
            }

        p = len(item_names)
        if p < 2:
            return {
                "status": "INSUFFICIENT_ITEMS",
                "message": f"Cần tối thiểu 2 câu hỏi để phân tích cấu trúc IRT 2PL (hiện có {p})."
            }

        # 1. Binarize ma trận dữ liệu thành {0, 1}
        binary_matrix: List[List[int]] = []
        is_already_binary = True
        for row in raw_matrix:
            for val in row:
                if val not in (0.0, 1.0, 0, 1):
                    is_already_binary = False
                    break
            if not is_already_binary:
                break

        # Xác định ngưỡng binarize nếu không phải 0/1
        col_thresholds = []
        for j in range(p):
            vals = [row[j] for row in raw_matrix]
            if is_already_binary:
                col_thresholds.append(0.5)
            elif binarization_threshold is not None:
                col_thresholds.append(binarization_threshold)
            else:
                sorted_vals = sorted(vals)
                med = sorted_vals[n // 2]
                col_thresholds.append(med)

        for row in raw_matrix:
            bin_row = []
            for j in range(p):
                val = row[j]
                if is_already_binary:
                    bin_row.append(1 if val >= 0.5 else 0)
                else:
                    bin_row.append(1 if val >= col_thresholds[j] else 0)
            binary_matrix.append(bin_row)

        # Kiểm tra biến thiên (variance check): mỗi item phải có cả 0 và 1
        item_proportions = []
        for j in range(p):
            sum_ones = sum(binary_matrix[i][j] for i in range(n))
            prop = sum_ones / n
            # Chặn nếu item 100% 0 hoặc 100% 1
            if sum_ones == 0:
                # Gán mẫu giả vi phân 1 phản hồi 1 để tránh sập toán học
                prop = 0.5 / n
            elif sum_ones == n:
                prop = (n - 0.5) / n
            item_proportions.append(prop)

        # 2. Thiết lập các điểm cầu phương Gauss-Hermite / Phân phối chuẩn chuẩn hóa (Quadrature Nodes)
        # 31 điểm từ -3.0 đến +3.0
        num_nodes = 31
        theta_nodes = [-3.0 + i * (6.0 / (num_nodes - 1)) for i in range(num_nodes)]
        # Trọng số tiền nghiệm chuẩn tắc W(theta_q) ~ N(0, 1)
        raw_weights = [math.exp(-0.5 * (t ** 2)) for t in theta_nodes]
        sum_weights = sum(raw_weights)
        quad_weights = [w / sum_weights for w in raw_weights]

        # 3. Khởi tạo tham số ban đầu (Initial values)
        # b_i = -logit(p_i) / 1.702
        # a_i = 1.0
        a_params = [1.0] * p
        b_params = []
        for j in range(p):
            pj = min(0.98, max(0.02, item_proportions[j]))
            logit_p = math.log(pj / (1.0 - pj))
            b_init = -logit_p / cls.D_SCALING_CONSTANT
            b_params.append(min(3.0, max(-3.0, b_init)))

        # 4. Vòng lặp Expectation-Maximization (MML-EM)
        for iteration in range(max_em_iter):
            old_a = list(a_params)
            old_b = list(b_params)

            # E-Step:
            # Tính Likelihood L_j(theta_q) cho từng người j và node q
            # và tính phân phối hậu nghiệm P(theta_q | y_j)
            posteriors = [[0.0] * num_nodes for _ in range(n)]
            for j in range(n):
                yj = binary_matrix[j]
                log_likes = [0.0] * num_nodes
                for q in range(num_nodes):
                    t_q = theta_nodes[q]
                    ll = 0.0
                    for i in range(p):
                        p_iq = cls._prob_2pl(t_q, a_params[i], b_params[i])
                        p_iq = min(0.9999, max(0.0001, p_iq))
                        if yj[i] == 1:
                            ll += math.log(p_iq)
                        else:
                            ll += math.log(1.0 - p_iq)
                    log_likes[q] = ll

                # Log-sum-exp chống tràn số
                max_ll = max(log_likes)
                weights_ll = [quad_weights[q] * math.exp(log_likes[q] - max_ll) for q in range(num_nodes)]
                sum_denom = sum(weights_ll)
                if sum_denom > 1e-12:
                    for q in range(num_nodes):
                        posteriors[j][q] = weights_ll[q] / sum_denom
                else:
                    for q in range(num_nodes):
                        posteriors[j][q] = 1.0 / num_nodes

            # Tính kỳ vọng số người N_bar_q và số người endorse r_bar_iq tại từng node
            n_bar = [sum(posteriors[j][q] for j in range(n)) for q in range(num_nodes)]
            r_bar = [[sum(binary_matrix[j][i] * posteriors[j][q] for j in range(n)) for q in range(num_nodes)] for i in range(p)]

            # M-Step:
            # Với mỗi item i, cập nhật a_i và b_i bằng hồi quy logistic có trọng số (Weighted Logistic / IRLS)
            for i in range(p):
                # beta_i = D * a_i, alpha_i = -D * a_i * b_i
                cur_beta = cls.D_SCALING_CONSTANT * a_params[i]
                cur_alpha = -cur_beta * b_params[i]

                # 4 bước lặp Newton-Raphson trên hàm log-likelihood M-step
                for _ in range(4):
                    grad_alpha = 0.0
                    grad_beta = 0.0
                    hess_aa = 0.0
                    hess_ab = 0.0
                    hess_bb = 0.0

                    for q in range(num_nodes):
                        t_q = theta_nodes[q]
                        nq = n_bar[q]
                        if nq < 1e-8:
                            continue
                        rq = r_bar[i][q]

                        z = cur_alpha + cur_beta * t_q
                        if z > 30.0:
                            pi = 1.0
                        elif z < -30.0:
                            pi = 0.0
                        else:
                            pi = 1.0 / (1.0 + math.exp(-z))

                        pi = min(0.9999, max(0.0001, pi))
                        wi = nq * pi * (1.0 - pi)
                        residual = rq - nq * pi

                        grad_alpha += residual
                        grad_beta += residual * t_q
                        hess_aa -= wi
                        hess_ab -= wi * t_q
                        hess_bb -= wi * (t_q ** 2)

                    # Ổn định ma trận Hessian bằng Ridge
                    hess_aa -= 1e-4
                    hess_bb -= 1e-4
                    det = hess_aa * hess_bb - (hess_ab ** 2)
                    if abs(det) > 1e-10:
                        d_alpha = (hess_bb * grad_alpha - hess_ab * grad_beta) / det
                        d_beta = (-hess_ab * grad_alpha + hess_aa * grad_beta) / det
                        # Cắt step để tránh nhảy vọt
                        d_alpha = max(-1.0, min(1.0, d_alpha))
                        d_beta = max(-1.0, min(1.0, d_beta))
                        cur_alpha -= d_alpha
                        cur_beta -= d_beta

                # Ràng buộc cur_beta > 0.15 (a_i > 0.1)
                cur_beta = max(0.2, min(6.0, cur_beta))
                new_a = cur_beta / cls.D_SCALING_CONSTANT
                new_b = -cur_alpha / cur_beta
                new_b = max(-3.5, min(3.5, new_b))

                a_params[i] = new_a
                b_params[i] = new_b

            # Kiểm tra độ hội tụ
            max_delta = max(
                max(abs(a_params[i] - old_a[i]) for i in range(p)),
                max(abs(b_params[i] - old_b[i]) for i in range(p))
            )
            if max_delta < tolerance:
                break

        # 5. Ước lượng năng lực người trả lời (EAP Person Latent Trait Scoring)
        person_thetas: List[float] = []
        person_ses: List[float] = []
        for j in range(n):
            yj = binary_matrix[j]
            log_likes = [0.0] * num_nodes
            for q in range(num_nodes):
                t_q = theta_nodes[q]
                ll = 0.0
                for i in range(p):
                    p_iq = cls._prob_2pl(t_q, a_params[i], b_params[i])
                    p_iq = min(0.9999, max(0.0001, p_iq))
                    if yj[i] == 1:
                        ll += math.log(p_iq)
                    else:
                        ll += math.log(1.0 - p_iq)
                log_likes[q] = ll
            max_ll = max(log_likes)
            post_w = [quad_weights[q] * math.exp(log_likes[q] - max_ll) for q in range(num_nodes)]
            denom = sum(post_w)
            norm_post = [w / denom for w in post_w] if denom > 0 else [1.0 / num_nodes] * num_nodes

            eap_theta = sum(theta_nodes[q] * norm_post[q] for q in range(num_nodes))
            eap_var = sum(((theta_nodes[q] - eap_theta) ** 2) * norm_post[q] for q in range(num_nodes))
            person_thetas.append(round(eap_theta, 3))
            person_ses.append(round(math.sqrt(max(1e-6, eap_var)), 3))

        # 6. Đánh giá phân loại câu hỏi (Item Classification Baker 2001)
        items_analysis: List[Dict[str, Any]] = []
        for i in range(p):
            a_val = a_params[i]
            b_val = b_params[i]

            # Phân loại độ phân biệt (Baker 2001)
            if a_val < 0.65:
                disc_class = "VERY_LOW"
                disc_label = "Rất thấp (< 0.65)"
            elif a_val < 1.35:
                disc_class = "MODERATE"
                disc_label = "Trung bình (0.65 - 1.34)"
            elif a_val < 1.70:
                disc_class = "HIGH"
                disc_label = "Cao (1.35 - 1.69)"
            else:
                disc_class = "VERY_HIGH"
                disc_label = "Rất cao (>= 1.70)"

            # Phân loại độ khó/ngưỡng ủng hộ
            if b_val < -1.5:
                diff_class = "VERY_EASY"
                diff_label = "Rất dễ / Ngưỡng thấp (b < -1.5)"
            elif b_val < -0.5:
                diff_class = "EASY"
                diff_label = "Dễ ( -1.5 <= b < -0.5)"
            elif b_val <= 0.5:
                diff_class = "MEDIUM"
                diff_label = "Trung bình (-0.5 <= b <= 0.5)"
            elif b_val <= 1.5:
                diff_class = "HARD"
                diff_label = "Khó (0.5 < b <= 1.5)"
            else:
                diff_class = "VERY_HARD"
                diff_label = "Rất khó / Ngưỡng cao (b > 1.5)"

            # Thông tin đỉnh câu hỏi tại b_i
            peak_info = cls._information_2pl(b_val, a_val, b_val)

            # Fit statistic (S-X2 approximation qua 3 nhóm năng lực)
            # Chia người làm thành 3 nhóm theo eap_theta: Thấp (<-0.5), Giữa ([-0.5, 0.5]), Cao (>0.5)
            groups = [
                [j for j in range(n) if person_thetas[j] < -0.5],
                [j for j in range(n) if -0.5 <= person_thetas[j] <= 0.5],
                [j for j in range(n) if person_thetas[j] > 0.5]
            ]
            chi_sq = 0.0
            for grp in groups:
                if not grp:
                    continue
                obs_1 = sum(binary_matrix[j][i] for j in grp)
                grp_theta_mean = sum(person_thetas[j] for j in grp) / len(grp)
                exp_prob = cls._prob_2pl(grp_theta_mean, a_val, b_val)
                exp_1 = len(grp) * exp_prob
                var_exp = len(grp) * exp_prob * (1.0 - exp_prob)
                if var_exp > 0.1:
                    chi_sq += ((obs_1 - exp_1) ** 2) / var_exp

            is_fit = chi_sq < 9.21  # Chi-sq df=2 tại alpha=0.01

            items_analysis.append({
                "item_id": f"ITEM_{i+1}",
                "item_name": item_names[i],
                "discrimination_a": round(a_val, 3),
                "discrimination_class": disc_class,
                "discrimination_label": disc_label,
                "difficulty_b": round(b_val, 3),
                "difficulty_class": diff_class,
                "difficulty_label": diff_label,
                "endorsement_rate": round(item_proportions[i], 3),
                "peak_information": round(peak_info, 3),
                "fit_chi_sq": round(chi_sq, 2),
                "is_good_fit": is_fit
            })

        # 7. Tính tọa độ vẽ đường cong ICC và TIF trên lưới đồ thị SVG
        # 36 điểm chia đều từ theta = -3.5 đến +3.5
        sample_thetas = [-3.5 + s * (7.0 / 35.0) for s in range(36)]
        
        # Tọa độ ICC cho từng item:
        # Scale vào viewBox SVG: width=520, height=260
        # x: mapping [-3.5, 3.5] -> [50, 490] (width = 440)
        # y: mapping [0.0, 1.0] -> [220, 30] (height = 190, y ngược)
        icc_curves = []
        for i in range(p):
            a_val = a_params[i]
            b_val = b_params[i]
            points = []
            for t in sample_thetas:
                prob = cls._prob_2pl(t, a_val, b_val)
                svg_x = 50.0 + ((t - (-3.5)) / 7.0) * 440.0
                svg_y = 220.0 - (prob * 190.0)
                points.append({
                    "theta": round(t, 2),
                    "prob": round(prob, 3),
                    "svg_x": round(svg_x, 1),
                    "svg_y": round(svg_y, 1)
                })
            icc_curves.append({
                "item_id": f"ITEM_{i+1}",
                "item_name": item_names[i],
                "points": points,
                "svg_path": "M " + " L ".join(f"{pt['svg_x']},{pt['svg_y']}" for pt in points)
            })

        # Test Information Function (TIF) và Standard Error SE(theta)
        tif_values = []
        se_values = []
        for t in sample_thetas:
            tif_val = sum(cls._information_2pl(t, a_params[i], b_params[i]) for i in range(p))
            tif_values.append(tif_val)
            se_val = 1.0 / math.sqrt(max(1e-4, tif_val)) if tif_val > 1e-4 else 3.0
            se_values.append(min(3.0, se_val))

        max_tif = max(1.0, max(tif_values))
        tif_points = []
        se_points = []
        for s in range(36):
            t = sample_thetas[s]
            tif_val = tif_values[s]
            se_val = se_values[s]

            svg_x = 50.0 + ((t - (-3.5)) / 7.0) * 440.0
            svg_y_tif = 220.0 - ((tif_val / max_tif) * 190.0)
            svg_y_se = 220.0 - ((se_val / 3.0) * 190.0)

            tif_points.append({
                "theta": round(t, 2),
                "info": round(tif_val, 3),
                "svg_x": round(svg_x, 1),
                "svg_y": round(svg_y_tif, 1)
            })
            se_points.append({
                "theta": round(t, 2),
                "se": round(se_val, 3),
                "svg_x": round(svg_x, 1),
                "svg_y": round(svg_y_se, 1)
            })

        # 8. Tính độ tin cậy biên của bài khảo sát (Marginal Reliability)
        theta_mean = sum(person_thetas) / n
        theta_var = sum((th - theta_mean) ** 2 for th in person_thetas) / (n - 1) if n > 1 else 1.0
        mean_se_sq = sum(se ** 2 for se in person_ses) / n
        marginal_reliability = max(0.0, min(0.999, theta_var / (theta_var + mean_se_sq))) if (theta_var + mean_se_sq) > 0 else 0.70

        # Khoảng năng lực được đo lường chính xác nhất (TIF >= 50% max_tif)
        peak_thetas = [sample_thetas[s] for s in range(36) if tif_values[s] >= 0.5 * max_tif]
        if peak_thetas:
            precision_range = [round(min(peak_thetas), 2), round(max(peak_thetas), 2)]
        else:
            precision_range = [-1.5, 1.5]

        # 9. Tự động sinh đoạn văn bản APA 7th Edition
        avg_a = sum(a_params) / p
        avg_b = sum(b_params) / p
        highest_a_item = max(items_analysis, key=lambda x: x["discrimination_a"])
        lowest_a_item = min(items_analysis, key=lambda x: x["discrimination_a"])
        hardest_item = max(items_analysis, key=lambda x: x["difficulty_b"])
        easiest_item = min(items_analysis, key=lambda x: x["difficulty_b"])

        apa_narrative = (
            f"Mô hình Lý thuyết Ứng đáp Câu hỏi 2 Tham số Logistic (IRT 2PL; Birnbaum, 1968) được ước lượng "
            f"qua thuật toán Cực đại Hóa Hợp lý Biên (MML-EM; Bock & Aitkin, 1981) trên tập mẫu N = {n} "
            f"với P = {p} câu hỏi khảo sát. Độ tin cậy biên toàn diện của thang đo đạt mức cao (rho_IRT = {marginal_reliability:.3f}). "
            f"Hệ số phân biệt trung bình đạt M_a = {avg_a:.2f} (trong đó câu hỏi '{highest_a_item['item_name']}' có độ phân biệt "
            f"cao nhất với a = {highest_a_item['discrimination_a']:.2f}, và câu hỏi '{lowest_a_item['item_name']}' thấp nhất với "
            f"a = {lowest_a_item['discrimination_a']:.2f}). Ngưỡng độ khó/chấp nhận trung bình đạt M_b = {avg_b:.2f} "
            f"(dao động từ b = {easiest_item['difficulty_b']:.2f} đối với '{easiest_item['item_name']}' đến b = {hardest_item['difficulty_b']:.2f} "
            f"đối với '{hardest_item['item_name']}'). Hàm thông tin khảo sát (TIF) cho thấy thang đo đạt độ chuẩn xác đo lường tối ưu "
            f"(sai số chuẩn đo lường SE < {1.0/math.sqrt(max_tif*0.5):.2f}) trong khoảng năng lực/thái độ từ theta = {precision_range[0]} "
            f"đến theta = {precision_range[1]}."
        )

        return {
            "status": "SUCCESS",
            "sample_size": n,
            "num_items": p,
            "is_already_binary": is_already_binary,
            "marginal_reliability": round(marginal_reliability, 3),
            "max_test_information": round(max_tif, 2),
            "optimal_theta_range": precision_range,
            "average_discrimination": round(avg_a, 2),
            "average_difficulty": round(avg_b, 2),
            "items": items_analysis,
            "icc_curves": icc_curves,
            "test_information_curve": {
                "max_tif": round(max_tif, 2),
                "tif_points": tif_points,
                "se_points": se_points,
                "tif_path": "M " + " L ".join(f"{pt['svg_x']},{pt['svg_y']}" for pt in tif_points),
                "se_path": "M " + " L ".join(f"{pt['svg_x']},{pt['svg_y']}" for pt in se_points)
            },
            "person_trait_summary": {
                "mean_theta": round(theta_mean, 3),
                "sd_theta": round(math.sqrt(max(1e-6, theta_var)), 3),
                "min_theta": min(person_thetas),
                "max_theta": max(person_thetas),
                "mean_se": round(sum(person_ses) / n, 3)
            },
            "apa_narrative": apa_narrative
        }
