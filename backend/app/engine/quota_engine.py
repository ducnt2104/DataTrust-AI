import math
from typing import Dict, Any, List, Optional, Tuple

class QuotaEngine:
    """
    Động cơ Quản lý Hạn ngạch Mẫu & Cân bằng Phân tầng Dân số học (Sampling Quotas & Demographic Balancing).
    Tuân thủ khuyến nghị phương pháp luận AAPOR (American Association for Public Opinion Research)
    và Tiêu chuẩn Thống kê Dân số học.
    """

    @staticmethod
    def evaluate_quotas(
        answers: Dict[str, Any],
        quota_rules: List[Dict[str, Any]],
        current_counts: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Đánh giá câu trả lời của phản hồi mới đối với các quy tắc hạn ngạch đang hoạt động.
        
        quota_rules cấu trúc:
        [
            {
                "id": "quota_gender_male",
                "name": "Nam giới",
                "question_id": "q_gender",
                "target_value": "Nam",
                "max_target": 100,
                "action": "flag_overflow" # hoặc "screen_out"
            }
        ]
        """
        matched_cells = []
        is_quota_full = False
        overflow_reasons = []

        for rule in quota_rules:
            qid = rule.get("question_id")
            target_val = rule.get("target_value")
            max_target = rule.get("max_target", 999999)
            action = rule.get("action", "flag_overflow")
            cell_id = rule.get("id", f"{qid}_{target_val}")

            resp_val = answers.get(qid)
            # Khớp câu trả lời
            is_match = False
            if isinstance(resp_val, list):
                is_match = target_val in resp_val
            elif resp_val is not None:
                is_match = str(resp_val).strip() == str(target_val).strip()

            if is_match:
                current_c = current_counts.get(cell_id, 0)
                matched_cells.append(cell_id)
                if current_c >= max_target:
                    is_quota_full = True
                    overflow_reasons.append(
                        f"Hạn ngạch '{rule.get('name', cell_id)}' đã đủ ({current_c}/{max_target})"
                    )

        return {
            "matched_cells": matched_cells,
            "is_quota_full": is_quota_full,
            "action": "screen_out" if is_quota_full and any(r.get("action") == "screen_out" for r in quota_rules) else "flag_overflow",
            "reasons": overflow_reasons
        }

    @staticmethod
    def compute_quota_progress(
        quota_rules: List[Dict[str, Any]],
        responses_answers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Tổng hợp tiến độ thu thập thực tế của từng ô hạn ngạch (Quota Cells).
        """
        # Đếm số lượng thực tế
        counts: Dict[str, int] = {}
        for rule in quota_rules:
            cell_id = rule.get("id", f"{rule.get('question_id')}_{rule.get('target_value')}")
            counts[cell_id] = 0

        for resp in responses_answers:
            ans_map = resp.get("answers", {})
            for rule in quota_rules:
                qid = rule.get("question_id")
                target_val = rule.get("target_value")
                cell_id = rule.get("id", f"{qid}_{target_val}")
                val = ans_map.get(qid)

                is_match = False
                if isinstance(val, list):
                    is_match = target_val in val
                elif val is not None:
                    is_match = str(val).strip() == str(target_val).strip()

                if is_match:
                    counts[cell_id] = counts.get(cell_id, 0) + 1

        results = []
        for rule in quota_rules:
            cell_id = rule.get("id", f"{rule.get('question_id')}_{rule.get('target_value')}")
            achieved = counts.get(cell_id, 0)
            target = rule.get("max_target", 100)
            pct = round((achieved / target * 100.0), 1) if target > 0 else 100.0
            
            status = "open"
            if achieved >= target:
                status = "filled"
            elif pct >= 85.0:
                status = "almost_full"

            results.append({
                "cell_id": cell_id,
                "name": rule.get("name", cell_id),
                "question_id": rule.get("question_id"),
                "target_value": rule.get("target_value"),
                "max_target": target,
                "achieved_count": achieved,
                "remaining_count": max(0, target - achieved),
                "completion_pct": pct,
                "status": status,
                "action": rule.get("action", "flag_overflow")
            })

        return results


class RakingEngine:
    """
    Thuật toán Cân bằng Trọng số Sau Thu thập (Post-Stratification Raking / Iterative Proportional Fitting - IPF).
    Theo nguyên lý Deming & Stephan (1940) và Kalton & Flores-Cervantes (2003).
    Dùng để điều chỉnh mẫu điều tra khớp với phân bố dân số chuẩn (Census Benchmarks).
    """

    @staticmethod
    def run_raking(
        sample_data: List[Dict[str, Any]],
        target_margins: Dict[str, Dict[str, float]],
        max_iterations: int = 50,
        convergence_tol: float = 1e-4,
        trim_min: float = 0.2,
        trim_max: float = 5.0
    ) -> Dict[str, Any]:
        """
        Thực hiện thuật toán IPF (Iterative Proportional Fitting):
        
        Args:
            sample_data: Danh sách các bản ghi mẫu, ví dụ:
                         [{"id": "resp_1", "gender": "Nam", "region": "Bắc"}, ...]
            target_margins: Tỷ lệ dân số chuẩn mục tiêu (tổng mỗi biến = 1.0), ví dụ:
                            {
                                "gender": {"Nam": 0.495, "Nữ": 0.505},
                                "region": {"Bắc": 0.35, "Trung": 0.20, "Nam": 0.45}
                            }
            max_iterations: Số vòng lặp tối đa.
            convergence_tol: Ngưỡng hội tụ (độ lệch lớn nhất giữa tỷ trọng mẫu đã cân và dân tộc mục tiêu).
            trim_min: Giới hạn dưới cắt xén trọng số (Weight Trimming) tránh trọng số cực tiểu.
            trim_max: Giới hạn trên cắt xén trọng số tránh trọng số cực đại thổi phồng phương sai.

        Returns:
            Dict chứa weights cho từng response_id, thông số Deff, Neff, và bảng so sánh trước/sau.
        """
        n = len(sample_data)
        if n == 0:
            return {
                "converged": False,
                "iterations": 0,
                "sample_size": 0,
                "effective_sample_size": 0.0,
                "design_effect": 1.0,
                "weights": {},
                "marginal_comparisons": [],
                "summary": "Không có mẫu dữ liệu để thực hiện cân bằng trọng số."
            }

        # Khởi tạo trọng số ban đầu w_i = 1.0
        weights: List[float] = [1.0] * n
        var_names = list(target_margins.keys())

        # Kiểm tra tính hợp lệ của target_margins (chuẩn hóa nếu tổng chưa chuẩn xác 1.0)
        norm_targets: Dict[str, Dict[str, float]] = {}
        for var, cat_probs in target_margins.items():
            tot = sum(cat_probs.values())
            if tot <= 0:
                continue
            norm_targets[var] = {k: v / tot for k, v in cat_probs.items()}

        converged = False
        last_max_diff = 1.0
        actual_iter = 0

        for it in range(max_iterations):
            actual_iter = it + 1
            max_diff = 0.0

            for var in var_names:
                cat_targets = norm_targets.get(var, {})
                # Tính tổng trọng số hiện tại cho từng nhóm
                current_cat_weights: Dict[str, float] = {cat: 0.0 for cat in cat_targets}
                for i, row in enumerate(sample_data):
                    val = str(row.get(var, "")).strip()
                    if val in current_cat_weights:
                        current_cat_weights[val] += weights[i]

                total_current_w = sum(current_cat_weights.values())
                if total_current_w <= 0:
                    continue

                # Cập nhật nhân tử điều chỉnh cho từng nhóm
                for cat, target_pct in cat_targets.items():
                    curr_sum = current_cat_weights.get(cat, 0.0)
                    desired_sum = target_pct * n
                    
                    if curr_sum > 0:
                        factor = desired_sum / curr_sum
                        diff = abs((curr_sum / total_current_w) - target_pct)
                        if diff > max_diff:
                            max_diff = diff

                        for i, row in enumerate(sample_data):
                            if str(row.get(var, "")).strip() == cat:
                                weights[i] *= factor

            # Trimming trọng số nếu vượt giới hạn nhằm kiểm soát phương sai
            mean_w = sum(weights) / n
            weights = [max(trim_min * mean_w, min(trim_max * mean_w, w)) for w in weights]
            # Chuẩn hóa lại tổng trọng số = n
            curr_tot = sum(weights)
            if curr_tot > 0:
                scale = n / curr_tot
                weights = [w * scale for w in weights]

            last_max_diff = max_diff
            if max_diff < convergence_tol:
                converged = True
                break

        # Thống kê phân bố trọng số
        w_min = min(weights)
        w_max = max(weights)
        w_mean = sum(weights) / n
        w_var = sum((w - w_mean) ** 2 for w in weights) / n
        w_std = math.sqrt(w_var)

        # Tính Kish's Design Effect (Deff) và Kish's Effective Sample Size (Neff)
        # Kish (1965): Deff = 1 + L = 1 + (CV_w)^2 = 1 + (Var(w) / Mean(w)^2)
        cv_squared = (w_std / w_mean) ** 2 if w_mean > 0 else 0.0
        deff = 1.0 + cv_squared
        neff = n / deff if deff > 0 else float(n)
        efficiency_pct = (neff / n) * 100.0

        # Tạo bảng so sánh chi tiết các phân phối biên (Marginal Comparisons)
        marginal_comparisons = []
        for var, cat_targets in norm_targets.items():
            # Đếm unweighted
            unweighted_counts: Dict[str, int] = {cat: 0 for cat in cat_targets}
            weighted_sums: Dict[str, float] = {cat: 0.0 for cat in cat_targets}

            for i, row in enumerate(sample_data):
                val = str(row.get(var, "")).strip()
                if val in unweighted_counts:
                    unweighted_counts[val] += 1
                    weighted_sums[val] += weights[i]

            cat_rows = []
            for cat, target_p in cat_targets.items():
                u_count = unweighted_counts.get(cat, 0)
                u_pct = (u_count / n * 100.0) if n > 0 else 0.0
                w_pct = (weighted_sums.get(cat, 0.0) / n * 100.0) if n > 0 else 0.0
                t_pct = target_p * 100.0

                cat_rows.append({
                    "category": cat,
                    "unweighted_count": u_count,
                    "unweighted_pct": round(u_pct, 2),
                    "target_benchmark_pct": round(t_pct, 2),
                    "weighted_pct": round(w_pct, 2),
                    "absolute_bias_reduction_pct": round(abs(u_pct - t_pct) - abs(w_pct - t_pct), 2)
                })

            marginal_comparisons.append({
                "variable": var,
                "categories": cat_rows
            })

        # Xây dựng từ điển weights theo response_id
        weight_map: Dict[str, float] = {}
        for i, row in enumerate(sample_data):
            resp_id = row.get("id", f"resp_{i}")
            weight_map[resp_id] = round(weights[i], 4)

        return {
            "converged": converged,
            "iterations": actual_iter,
            "max_discrepancy": round(last_max_diff, 6),
            "sample_size": n,
            "design_effect_deff": round(deff, 3),
            "effective_sample_size_neff": round(neff, 1),
            "statistical_efficiency_pct": round(efficiency_pct, 1),
            "weight_stats": {
                "min": round(w_min, 4),
                "max": round(w_max, 4),
                "mean": round(w_mean, 4),
                "std": round(w_std, 4),
                "trim_bounds": [trim_min, trim_max]
            },
            "weights": weight_map,
            "marginal_comparisons": marginal_comparisons,
            "summary": (
                f"Thuật toán IPF {'hội tụ thành công' if converged else 'hoàn thành'} sau {actual_iter} vòng lặp. "
                f"Cỡ mẫu danh nghĩa N={n}, Cỡ mẫu hiệu dụng của Kish Neff={round(neff, 1)} (Hiệu suất {round(efficiency_pct, 1)}%), "
                f"Hệ số thiết kế Deff={round(deff, 3)}. Độ lệch biên tối đa: {round(last_max_diff * 100, 3)}%."
            )
        }
