import math
import json
import re
import statistics
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple

class QualityEngine:
    """
    DataTrust Quality Assurance & Fraud Screening Engine.
    Thực hiện đánh giá chất lượng phản hồi đa tầng bằng các thuật toán tất định:
    - Layer A: Validation & Completeness
    - Layer B: Hamming Distance Vectorization (Trùng lặp / Gần trùng lặp)
    - Layer C: Response Pattern Anomalies (Straightlining, Shannon Entropy)
    - Layer D: Cross-Question Logic Consistency
    - Layer E: Timing & Submission Speed (Speeding detection)
    - Layer F: Open-Ended Text Repetition & Gibberish
    - Layer G: Composite Explainable Heuristic Risk Score (0 - 100)
    """

    DEFAULT_WEIGHTS = {
        "dup": 0.35,
        "pat": 0.25,
        "logic": 0.25,
        "enum": 0.15,
        "speed": 0.15
    }

    @staticmethod
    def normalize_value(val: Any, q_type: str = "") -> str:
        """Chuẩn hóa giá trị trả lời để so sánh vector"""
        if val is None:
            return ""
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, list):
            if q_type == "ranking":
                # Đối với câu hỏi xếp hạng, thứ tự là thông tin quyết định
                cleaned = [str(x).strip().lower() for x in val if x is not None]
                return ">".join(cleaned)
            # Với multiple choice, sắp xếp để so sánh tập hợp
            cleaned = sorted([str(x).strip().lower() for x in val if x is not None])
            return "|".join(cleaned)
        if isinstance(val, dict):
            # Với matrix: sắp xếp key và value
            items = sorted([f"{k}:{v}" for k, v in val.items()])
            return ";".join(items)
        return str(val).strip().lower()

    @staticmethod
    def compute_benford_analysis(numbers: List[Any]) -> Dict[str, Any]:
        """
        Kiểm định Luật Benford (Benford's Law First-Digit Test) trên các câu hỏi số học
        để phát hiện số liệu ngụy tạo / bịa đặt bởi con người (Schräpler & Wagner 2012, AAPOR 2003).
        """
        digits = []
        for n in numbers:
            try:
                val = abs(float(n))
                if val > 0:
                    # Lấy chữ số đầu tiên khác 0
                    s = f"{val:.10e}"
                    first_digit = int(s[0])
                    if 1 <= first_digit <= 9:
                        digits.append(first_digit)
            except Exception:
                continue

        n_samples = len(digits)
        is_sample_sufficient = n_samples >= 30

        benford_probs = {d: math.log10(1.0 + 1.0 / d) for d in range(1, 10)}
        counts = {d: digits.count(d) for d in range(1, 10)}
        
        distribution = []
        chi_square = 0.0

        for d in range(1, 10):
            obs_cnt = counts[d]
            obs_pct = round((obs_cnt / n_samples * 100), 2) if n_samples > 0 else 0.0
            exp_pct = round(benford_probs[d] * 100, 2)
            exp_cnt = n_samples * benford_probs[d]
            
            if exp_cnt > 0:
                chi_square += ((obs_cnt - exp_cnt) ** 2) / exp_cnt

            distribution.append({
                "digit": d,
                "observed_count": obs_cnt,
                "observed_percentage": obs_pct,
                "benford_percentage": exp_pct,
                "difference": round(obs_pct - exp_pct, 2)
            })

        chi_square = round(chi_square, 2)
        is_anomalous = False
        significance_level = "Bình thường (Khớp quy luật tự nhiên)"
        if is_sample_sufficient:
            if chi_square >= 20.09:
                is_anomalous = True
                significance_level = "p < 0.01 (Độ lệch nghiêm trọng, nghi ngờ số liệu tự bịa đặt)"
            elif chi_square >= 15.51:
                is_anomalous = True
                significance_level = "p < 0.05 (Độ lệch có ý nghĩa thống kê)"

        return {
            "total_numeric_samples": n_samples,
            "is_sample_sufficient": is_sample_sufficient,
            "notice": None if is_sample_sufficient else f"Cần tối thiểu N >= 30 mẫu số liệu để kiểm định Benford đạt ý nghĩa thống kê (hiện có N = {n_samples}).",
            "chi_square_statistic": chi_square,
            "degrees_of_freedom": 8,
            "is_anomalous": is_anomalous,
            "significance_level": significance_level,
            "distribution": distribution
        }

    @staticmethod
    def _chi2_pvalue(chi2: float, df: int) -> float:
        """Tính p-value cho phân phối Chi-Square bằng khai triển chuỗi Gamma chính xác cao"""
        if df <= 0 or chi2 <= 0:
            return 1.0
        s = df / 2.0
        z = chi2 / 2.0
        sum_term = 1.0 / s
        current = sum_term
        for k in range(1, 100):
            sum_term *= z / (s + k)
            current += sum_term
            if sum_term < 1e-12:
                break
        gamma_p = current * math.exp(-z + s * math.log(max(1e-12, z)) - math.lgamma(s))
        p_val = 1.0 - gamma_p
        return max(0.0, min(1.0, p_val))

    @staticmethod
    def compute_cronbach_alpha(items_matrix: List[List[float]]) -> Optional[float]:
        """
        Tính toán hệ số độ tin cậy nội bộ thang đo Cronbach's Alpha (Cronbach 1951).
        Công thức: alpha = (k / (k - 1)) * (1 - sum(var_item) / var_total)
        items_matrix: Ma trận N người trả lời x K câu hỏi thang đo.
        Yêu cầu: N >= 3 người trả lời và K >= 2 mục thang đo.
        """
        if not items_matrix or len(items_matrix) < 3:
            return None
        
        n_respondents = len(items_matrix)
        k_items = len(items_matrix[0])
        if k_items < 2:
            return None

        # 1. Tính phương sai từng mục câu hỏi
        item_variances = []
        for j in range(k_items):
            scores = [row[j] for row in items_matrix if len(row) > j]
            if len(scores) != n_respondents:
                return None
            mean_j = sum(scores) / n_respondents
            var_j = sum((x - mean_j) ** 2 for x in scores) / (n_respondents - 1)
            item_variances.append(var_j)

        sum_item_variances = sum(item_variances)

        # 2. Tính tổng điểm từng người và phương sai của tổng điểm
        total_scores = [sum(row) for row in items_matrix]
        mean_total = sum(total_scores) / n_respondents
        var_total = sum((t - mean_total) ** 2 for t in total_scores) / (n_respondents - 1)

        # Tránh chia cho 0
        if var_total <= 1e-12:
            return 0.0

        alpha = (k_items / (k_items - 1)) * (1.0 - (sum_item_variances / var_total))
        return round(float(alpha), 4)

    @classmethod
    def compute_detailed_reliability(
        cls,
        items_matrix: List[List[float]],
        item_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Phân tích chi tiết độ tin cậy thang đo (Psychometric Scale Reliability Analysis).
        Bao gồm: Cronbach's Alpha tổng thể, Standardized Alpha, Thống kê từng mục (Item Means, Variances),
        Tương quan biến - tổng hiệu chỉnh (Corrected Item-Total Correlation r_it) và Alpha nếu loại bỏ mục (Alpha if item deleted).
        Tuân thủ chuẩn mực phân tích tâm trắc học APA, Nunnally & Bernstein (1994) và SPSS Reliability Analysis.
        """
        if not items_matrix or len(items_matrix) < 3:
            return {
                "is_sufficient": False,
                "notice": "Cần ít nhất 3 người trả lời để phân tích độ tin cậy thang đo.",
                "cronbach_alpha": None,
                "standardized_alpha": None,
                "n_samples": len(items_matrix) if items_matrix else 0,
                "k_items": len(items_matrix[0]) if items_matrix and items_matrix[0] else 0,
                "scale_mean": 0.0,
                "scale_variance": 0.0,
                "scale_std_dev": 0.0,
                "academic_rating": "CHƯA ĐỦ DỮ LIỆU",
                "interpretation": "Chưa có đủ cỡ mẫu (N >= 3) để kiểm định độ tin cậy.",
                "item_statistics": []
            }

        n_resp = len(items_matrix)
        k_items = len(items_matrix[0])
        if k_items < 2:
            return {
                "is_sufficient": False,
                "notice": "Thang đo cần ít nhất 2 câu hỏi để kiểm định độ tin cậy nội bộ.",
                "cronbach_alpha": None,
                "standardized_alpha": None,
                "n_samples": n_resp,
                "k_items": k_items,
                "scale_mean": 0.0,
                "scale_variance": 0.0,
                "scale_std_dev": 0.0,
                "academic_rating": "CHƯA ĐỦ BIẾN SỐ",
                "interpretation": "Thang đo cần ít nhất 2 câu hỏi để tính toán Cronbach's Alpha.",
                "item_statistics": []
            }

        for row in items_matrix:
            if len(row) != k_items:
                return {
                    "is_sufficient": False,
                    "notice": "Ma trận phản hồi không đồng đều giữa các biến thang đo.",
                    "cronbach_alpha": None,
                    "standardized_alpha": None,
                    "n_samples": n_resp,
                    "k_items": k_items,
                    "scale_mean": 0.0,
                    "scale_variance": 0.0,
                    "scale_std_dev": 0.0,
                    "academic_rating": "LỖI DỮ LIỆU",
                    "interpretation": "Dữ liệu thiếu khuyết không đồng đều giữa các biến.",
                    "item_statistics": []
                }

        # 1. Tính toán Mean và Variance từng item
        item_means = []
        item_variances = []
        for j in range(k_items):
            scores = [row[j] for row in items_matrix]
            m_j = sum(scores) / n_resp
            v_j = sum((x - m_j) ** 2 for x in scores) / (n_resp - 1)
            item_means.append(m_j)
            item_variances.append(v_j)

        sum_item_vars = sum(item_variances)

        # 2. Tổng điểm từng người và phương sai tổng
        total_scores = [sum(row) for row in items_matrix]
        scale_mean = sum(total_scores) / n_resp
        scale_var = sum((t - scale_mean) ** 2 for t in total_scores) / (n_resp - 1)

        # Cronbach's Alpha
        if scale_var > 1e-12:
            alpha = (k_items / (k_items - 1)) * (1.0 - (sum_item_vars / scale_var))
        else:
            alpha = 0.0
        alpha = round(float(alpha), 4)

        # 3. Tính ma trận tương quan giữa các items và Standardized Alpha
        inter_correlations = []
        for j in range(k_items):
            for l in range(j + 1, k_items):
                scores_j = [row[j] for row in items_matrix]
                scores_l = [row[l] for row in items_matrix]
                m_j, m_l = item_means[j], item_means[l]
                cov_jl = sum((scores_j[i] - m_j) * (scores_l[i] - m_l) for i in range(n_resp)) / (n_resp - 1)
                std_j = math.sqrt(max(0.0, item_variances[j]))
                std_l = math.sqrt(max(0.0, item_variances[l]))
                if std_j > 1e-9 and std_l > 1e-9:
                    r_jl = cov_jl / (std_j * std_l)
                    inter_correlations.append(r_jl)

        avg_r = sum(inter_correlations) / len(inter_correlations) if inter_correlations else 0.0
        if 1.0 + (k_items - 1) * avg_r > 1e-9:
            std_alpha = (k_items * avg_r) / (1.0 + (k_items - 1) * avg_r)
        else:
            std_alpha = 0.0
        std_alpha = round(float(std_alpha), 4)

        # 4. Item-Total Statistics & Alpha if Item Deleted
        item_stats = []
        for j in range(k_items):
            rest_totals = [total_scores[i] - items_matrix[i][j] for i in range(n_resp)]
            rest_mean = sum(rest_totals) / n_resp
            rest_var = sum((t - rest_mean) ** 2 for t in rest_totals) / (n_resp - 1)

            scores_j = [row[j] for row in items_matrix]
            m_j = item_means[j]
            cov_rest = sum((scores_j[i] - m_j) * (rest_totals[i] - rest_mean) for i in range(n_resp)) / (n_resp - 1)
            std_j = math.sqrt(max(0.0, item_variances[j]))
            std_rest = math.sqrt(max(0.0, rest_var))
            if std_j > 1e-9 and std_rest > 1e-9:
                r_it = cov_rest / (std_j * std_rest)
            else:
                r_it = 0.0
            r_it = round(float(r_it), 4)

            if k_items > 2:
                sum_vars_without_j = sum_item_vars - item_variances[j]
                if rest_var > 1e-12:
                    alpha_deleted = ((k_items - 1) / (k_items - 2)) * (1.0 - (sum_vars_without_j / rest_var))
                else:
                    alpha_deleted = 0.0
                alpha_deleted = round(float(alpha_deleted), 4)
            else:
                alpha_deleted = None

            meta = item_metadata[j] if item_metadata and len(item_metadata) > j else {}
            item_id = meta.get("id") or meta.get("question_id") or f"VAR_{j+1}"
            item_title = meta.get("title") or meta.get("question_title") or f"Câu hỏi thang đo #{j+1}"

            if r_it < 0.20 or (alpha_deleted is not None and alpha_deleted > alpha + 0.05):
                status = "CONSIDER_REVISE"
                recommendation = "Cân nhắc hiệu chỉnh hoặc loại bỏ (Tương quan thấp hoặc tăng Alpha khi bỏ)"
            elif r_it >= 0.30:
                status = "GOOD"
                recommendation = "Đạt chuẩn phân biệt tốt (Nunnally & Bernstein r >= 0.30)"
            else:
                status = "ACCEPTABLE"
                recommendation = "Chấp nhận được (0.20 <= r < 0.30)"

            item_stats.append({
                "item_index": j,
                "item_id": item_id,
                "item_title": item_title,
                "item_mean": round(item_means[j], 2),
                "item_variance": round(item_variances[j], 2),
                "item_std_dev": round(math.sqrt(max(0.0, item_variances[j])), 2),
                "scale_mean_if_deleted": round(rest_mean, 2),
                "scale_variance_if_deleted": round(rest_var, 2),
                "corrected_item_total_correlation": r_it,
                "alpha_if_item_deleted": alpha_deleted,
                "status": status,
                "recommendation": recommendation
            })

        if alpha >= 0.80:
            academic_rating = "XUẤT SẮC (EXCELLENT)"
            interpretation = f"Hệ số Cronbach's Alpha đạt {alpha:.4f} (Standardized Alpha = {std_alpha:.4f}), thể hiện tính nhất quán nội tại rất cao của thang đo theo tiêu chuẩn Nunnally & Bernstein (1994) và Hair et al. (2010)."
        elif alpha >= 0.70:
            academic_rating = "ĐẠT CHUẨN (ACCEPTABLE)"
            interpretation = f"Hệ số Cronbach's Alpha đạt {alpha:.4f} (Standardized Alpha = {std_alpha:.4f}), thỏa mãn ngưỡng độ tin cậy khuyến nghị cho nghiên cứu khoa học (alpha >= 0.70)."
        elif alpha >= 0.60:
            academic_rating = "ĐỊNH HƯỚNG SƠ BỘ (EXPLORATORY)"
            interpretation = f"Hệ số Cronbach's Alpha đạt {alpha:.4f}, chấp nhận được trong các nghiên cứu khám phá ban đầu nhưng khuyến nghị rà soát các mục có tương quan biến - tổng thấp."
        else:
            academic_rating = "KHÔNG ĐẠT (UNACCEPTABLE)"
            interpretation = f"Hệ số Cronbach's Alpha đạt {alpha:.4f} < 0.60, thang đo chưa đảm bảo độ tin cậy nội bộ. Cần loại bỏ hoặc viết lại các mục câu hỏi có tương quan biến - tổng âm hoặc quá thấp."

        return {
            "is_sufficient": True,
            "cronbach_alpha": alpha,
            "standardized_alpha": std_alpha,
            "n_samples": n_resp,
            "k_items": k_items,
            "scale_mean": round(scale_mean, 2),
            "scale_variance": round(scale_var, 2),
            "scale_std_dev": round(math.sqrt(max(0.0, scale_var)), 2),
            "academic_rating": academic_rating,
            "interpretation": interpretation,
            "item_statistics": item_stats
        }

    @classmethod
    def evaluate_cleansing_rules(
        cls,
        responses: List[Dict[str, Any]],
        assessments_by_resp: Dict[str, Dict[str, Any]],
        criteria: Dict[str, Any],
        syndicate_response_ids: Optional[Set[str]] = None,
        coffee_shop_response_ids: Optional[Set[str]] = None,
        impossible_travel_response_ids: Optional[Set[str]] = None,
        geofence_violation_response_ids: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Đánh giá quy tắc lọc loại bỏ dữ liệu rác (Data Cleansing & Exclusion Rules).
        Áp dụng tiêu chuẩn Don Dillman, AAPOR và ISO 20252:2019 để bóc tách mẫu sạch và mẫu bị loại:
        - Speeder: nộp quá nhanh so với ngưỡng tối thiểu
        - Straightlining: trả lời một đường thẳng hoặc hoa văn rập khuôn
        - Logic contradiction: vi phạm logic chéo
        - High risk: điểm rủi ro tổng hợp >= 70
        - Low OMR confidence: chất lượng quét phiếu giấy < ngưỡng tin cậy
        - Unverified enumerator: không có mã điều tra viên
        - Collusion syndicates: vòng lừa đảo / bot rings trùng lặp cao
        - Coffee shop congregation: cụm tọa độ GPS tĩnh bất thường
        - Impossible travel: vận tốc di chuyển phi thực tế / GPS giả mạo
        - Geofence breaches: thu thập nằm ngoài ranh giới vùng chỉ định
        """
        clean_ids = []
        flagged_speeders = []
        flagged_straightlining = []
        flagged_contradictions = []
        flagged_high_risk = []
        flagged_low_omr = []
        flagged_unverified_enum = []
        flagged_syndicates = []
        flagged_coffee_shop = []
        flagged_impossible_travel = []
        flagged_geofence_violations = []
        rejected_reasons: Dict[str, List[str]] = {}

        exclude_speed = criteria.get("exclude_speeders", True)
        min_sec = float(criteria.get("speeder_min_seconds", 10.0))
        exclude_straight = criteria.get("exclude_straightlining", True)
        exclude_logic = criteria.get("exclude_logic_contradictions", True)
        exclude_hr = criteria.get("exclude_high_risk", False)
        min_omr = float(criteria.get("min_omr_confidence", 0.70))
        exclude_unverified_enum = criteria.get("exclude_unverified_enumerator", False)
        exclude_syndicates = criteria.get("exclude_collusion_syndicates", True)
        exclude_coffee_shop = criteria.get("exclude_coffee_shop_congregations", True)
        exclude_impossible_speed = criteria.get("exclude_impossible_travel", True)
        exclude_geofence = criteria.get("exclude_geofence_violations", False)

        for r in responses:
            rid = r["id"]
            reasons = []
            dur = float(r.get("duration_seconds", 0.0))
            risk = float(r.get("risk_score", 0.0))
            source = r.get("source", "online_form")
            enum_id = (r.get("enumerator_id") or "").strip()
            omr_conf = float(r.get("omr_confidence") if r.get("omr_confidence") is not None else 1.0)

            qa = assessments_by_resp.get(rid, {})
            flags = qa.get("flags", [])
            flag_codes = {f.get("code") for f in flags if isinstance(f, dict)}

            # 1. Speeder check
            if exclude_speed:
                if (dur > 0 and dur < min_sec) or "FLAG_SPEEDING" in flag_codes:
                    flagged_speeders.append(rid)
                    reasons.append(f"Tốc độ nộp bài quá nhanh ({dur:.1f}s < {min_sec:.1f}s)")

            # 2. Straightlining & Pattern check
            if exclude_straight:
                pattern_flags = {"FLAG_STRAIGHTLINING", "FLAG_DIAGONAL_PATTERN", "FLAG_ZIGZAG_PATTERN"}
                if flag_codes.intersection(pattern_flags):
                    flagged_straightlining.append(rid)
                    reasons.append("Phát hiện hoa văn trả lời rập khuôn / thẳng hàng")

            # 3. Logic contradiction check
            if exclude_logic:
                if "FLAG_LOGIC_CONTRADICTION" in flag_codes:
                    flagged_contradictions.append(rid)
                    reasons.append("Vi phạm mâu thuẫn logic giữa các câu hỏi")

            # 4. High risk score check
            if exclude_hr:
                if risk >= 70.0:
                    flagged_high_risk.append(rid)
                    reasons.append(f"Điểm rủi ro tổng hợp cao ({risk:.1f}/100)")

            # 5. Low OMR confidence check
            if source == "paper_scan" and omr_conf < min_omr:
                flagged_low_omr.append(rid)
                reasons.append(f"Độ tin cậy nhận dạng OMR thấp ({omr_conf * 100:.1f}% < {min_omr * 100:.1f}%)")

            # 6. Unverified enumerator check
            if exclude_unverified_enum and not enum_id:
                flagged_unverified_enum.append(rid)
                reasons.append("Thiếu định danh điều tra viên thực địa")

            # 7. Collusion syndicate check
            if exclude_syndicates:
                if (syndicate_response_ids and rid in syndicate_response_ids) or "FLAG_COLLUSION_SUSPECT" in flag_codes:
                    flagged_syndicates.append(rid)
                    reasons.append("Thuộc mạng lưới/nhóm thông đồng sao chép (Collusion Syndicate Ring)")

            # 8. Coffee-shop congregation check
            if exclude_coffee_shop:
                if coffee_shop_response_ids and rid in coffee_shop_response_ids:
                    flagged_coffee_shop.append(rid)
                    reasons.append("Cụm tọa độ GPS tĩnh bất thường nghi vấn ngồi quán cà phê (Coffee-Shop Congregation Fraud)")

            # 9. Impossible travel velocity check
            if exclude_impossible_speed:
                if (impossible_travel_response_ids and rid in impossible_travel_response_ids) or "FLAG_GPS_SPOOFING" in flag_codes:
                    flagged_impossible_travel.append(rid)
                    reasons.append("Vận tốc di chuyển phi thực tế / nghi ngờ GPS giả mạo (> 120 km/h)")

            # 10. Geofence violation check
            if exclude_geofence:
                if geofence_violation_response_ids and rid in geofence_violation_response_ids:
                    flagged_geofence_violations.append(rid)
                    reasons.append("Thu thập nằm ngoài ranh giới vùng địa lý được cấp phép (Geofence Breach)")

            if reasons:
                rejected_reasons[rid] = reasons
            else:
                clean_ids.append(rid)

        all_flagged_set = set(rejected_reasons.keys())
        overlap_count = (
            len(flagged_speeders) + len(flagged_straightlining) +
            len(flagged_contradictions) + len(flagged_high_risk) +
            len(flagged_low_omr) + len(flagged_unverified_enum) +
            len(flagged_syndicates) + len(flagged_coffee_shop) +
            len(flagged_impossible_travel) + len(flagged_geofence_violations)
        ) - len(all_flagged_set)

        return {
            "total_evaluated": len(responses),
            "clean_ids": clean_ids,
            "rejected_ids": list(all_flagged_set),
            "clean_count": len(clean_ids),
            "rejected_count": len(all_flagged_set),
            "clean_percentage": round((len(clean_ids) / len(responses) * 100.0), 1) if responses else 100.0,
            "flagged_speeders": len(flagged_speeders),
            "flagged_straightlining": len(flagged_straightlining),
            "flagged_contradictions": len(flagged_contradictions),
            "flagged_high_risk": len(flagged_high_risk),
            "flagged_low_omr": len(flagged_low_omr),
            "flagged_unverified_enum": len(flagged_unverified_enum),
            "flagged_collusion_syndicates": len(flagged_syndicates),
            "flagged_coffee_shop": len(flagged_coffee_shop),
            "flagged_impossible_travel": len(flagged_impossible_travel),
            "flagged_geofence_violations": len(flagged_geofence_violations),
            "overlap_count": max(0, overlap_count),
            "rejected_reasons": rejected_reasons
        }

    @classmethod
    def compute_crosstab_analysis(
        cls,
        pairs: List[Tuple[Any, Any]],
        var1_info: Dict[str, Any],
        var2_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phân tích chéo biến số (Cross-Tabulation & Chi-Square Independence Test).
        Xây dựng Bảng Ngẫu Nhiên (Contingency Table), tính tần số quan sát O_ij,
        tần số kỳ vọng E_ij, tỷ lệ %, thống kê Chi-Square, p-value và hệ số Cramer's V.
        """
        valid_pairs = []
        for v1, v2 in pairs:
            s1 = cls.normalize_value(v1)
            s2 = cls.normalize_value(v2)
            if s1 and s2:
                valid_pairs.append((s1, s2))

        n_samples = len(valid_pairs)
        if n_samples == 0:
            return {
                "total_valid_samples": 0,
                "is_sample_sufficient": False,
                "notice": "Không có cặp dữ liệu hợp lệ nào giữa hai câu hỏi được chọn.",
                "variable_row": var1_info,
                "variable_col": var2_info,
                "row_categories": [],
                "col_categories": [],
                "matrix": {},
                "chi_square_statistic": 0.0,
                "degrees_of_freedom": 0,
                "p_value": 1.0,
                "cramers_v": 0.0,
                "association_strength": "Chưa xác định",
                "is_statistically_significant": False,
                "interpretation": "Chưa có đủ dữ liệu để kiểm định."
            }

        def get_categories(info, observed_vals):
            opts = info.get("options", [])
            cat_list = []
            for opt in opts:
                text = opt.get("text", "") if isinstance(opt, dict) else str(opt)
                norm = cls.normalize_value(text)
                if norm and norm in observed_vals and norm not in cat_list:
                    cat_list.append(norm)
            for v in sorted(observed_vals):
                if v not in cat_list:
                    cat_list.append(v)
            return cat_list

        obs_v1 = set(p[0] for p in valid_pairs)
        obs_v2 = set(p[1] for p in valid_pairs)

        row_cats = get_categories(var1_info, obs_v1)
        col_cats = get_categories(var2_info, obs_v2)

        observed_counts: Dict[str, Dict[str, int]] = {r: {c: 0 for c in col_cats} for r in row_cats}
        row_totals: Dict[str, int] = {r: 0 for r in row_cats}
        col_totals: Dict[str, int] = {c: 0 for c in col_cats}

        for r_val, c_val in valid_pairs:
            if r_val in observed_counts and c_val in observed_counts[r_val]:
                observed_counts[r_val][c_val] += 1
                row_totals[r_val] += 1
                col_totals[c_val] += 1

        chi_square = 0.0
        matrix_result: Dict[str, Dict[str, Any]] = {}

        for r in row_cats:
            matrix_result[r] = {}
            for c in col_cats:
                obs = observed_counts[r][c]
                r_tot = row_totals[r]
                c_tot = col_totals[c]
                exp = (r_tot * c_tot) / n_samples if n_samples > 0 else 0.0

                if exp > 0:
                    chi_square += ((obs - exp) ** 2) / exp

                row_pct = round((obs / r_tot * 100), 1) if r_tot > 0 else 0.0
                col_pct = round((obs / c_tot * 100), 1) if c_tot > 0 else 0.0
                tot_pct = round((obs / n_samples * 100), 1) if n_samples > 0 else 0.0
                pearson_res = round(((obs - exp) / math.sqrt(exp)), 2) if exp > 0 else 0.0

                matrix_result[r][c] = {
                    "observed": obs,
                    "expected": round(exp, 2),
                    "row_percentage": row_pct,
                    "column_percentage": col_pct,
                    "total_percentage": tot_pct,
                    "pearson_residual": pearson_res
                }

        num_rows = len(row_cats)
        num_cols = len(col_cats)
        df = max(0, (num_rows - 1) * (num_cols - 1))
        p_val = cls._chi2_pvalue(chi_square, df) if df > 0 else 1.0

        min_dim = min(num_rows - 1, num_cols - 1)
        if min_dim > 0 and n_samples > 0:
            cramers_v = math.sqrt(chi_square / (n_samples * min_dim))
        else:
            cramers_v = 0.0
        cramers_v = round(min(1.0, max(0.0, cramers_v)), 3)

        if cramers_v >= 0.35:
            strength = "Mối liên hệ rất mạnh (Very Strong Association)"
        elif cramers_v >= 0.20:
            strength = "Mối liên hệ vừa phải (Moderate Association)"
        elif cramers_v >= 0.10:
            strength = "Mối liên hệ yếu (Weak Association)"
        else:
            strength = "Hầu như độc lập (Negligible / Independent)"

        is_sig = bool(p_val < 0.05 and df > 0)
        is_sufficient = n_samples >= 20

        if not is_sufficient:
            interp = f"Cỡ mẫu N = {n_samples} nhỏ hơn ngưỡng khuyến nghị (N >= 20). Kết quả phân tích mang tính định hướng tham khảo."
        elif is_sig:
            interp = f"Kiểm định Chi-Square cho thấy mối liên hệ có ý nghĩa thống kê (chi^2 = {chi_square:.2f}, df = {df}, p = {p_val:.4f} < 0.05). Mức độ liên kết theo Cramer's V là {cramers_v} ({strength})."
        else:
            interp = f"Chưa đủ bằng chứng bác bỏ giả thuyết độc lập giữa hai biến số (chi^2 = {chi_square:.2f}, df = {df}, p = {p_val:.4f} >= 0.05)."

        return {
            "total_valid_samples": n_samples,
            "is_sample_sufficient": is_sufficient,
            "notice": None if is_sufficient else f"Cần cỡ mẫu N >= 20 để kiểm định Bảng ngẫu nhiên đạt độ tin cậy chuẩn (hiện có N = {n_samples}).",
            "variable_row": {
                "id": var1_info.get("id"),
                "title": var1_info.get("title"),
                "type": var1_info.get("question_type"),
                "categories": row_cats,
                "totals": row_totals
            },
            "variable_col": {
                "id": var2_info.get("id"),
                "title": var2_info.get("title"),
                "type": var2_info.get("question_type"),
                "categories": col_cats,
                "totals": col_totals
            },
            "matrix": matrix_result,
            "chi_square_statistic": round(chi_square, 3),
            "degrees_of_freedom": df,
            "p_value": round(p_val, 4),
            "cramers_v": cramers_v,
            "association_strength": strength,
            "is_statistically_significant": is_sig,
            "interpretation": interp
        }

    @classmethod
    def compute_longitudinal_comparison(
        cls,
        wave1_meta: Dict[str, Any],
        wave2_meta: Dict[str, Any],
        matched_items_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Phân tích xu hướng dọc theo đợt khảo sát & Đo lường độ lớn hiệu ứng (Longitudinal Wave-over-Wave Analytics & Cohen's d Effect Size).
        Hỗ trợ so sánh giữa hai đợt khảo sát (Wave 1 / Pre-test vs Wave 2 / Post-test):
        1. Thống kê mô tả từng đợt: N1, N2, Mean 1, Mean 2, Phương sai, Độ lệch chuẩn.
        2. Độ dịch chuyển điểm trung bình (Mean Shift ΔM) và Tỷ lệ phần trăm biến thiên (%Δ).
        3. Độ lệch chuẩn gộp (Pooled Standard Deviation) và Hệ số độ lớn hiệu ứng Cohen's d (Jacob Cohen, 1988).
        4. Kiểm định giả thuyết hai mẫu độc lập Welch's t-test, bậc tự do hiệu chỉnh (Welch-Satterthwaite df) và giá trị p-value.
        5. Phân loại hiệu ứng (Trivial, Small, Medium, Large) và định dạng báo cáo chuẩn APA 7th Edition.
        """
        compared_items = []
        scale_means_1 = []
        scale_means_2 = []
        items_increased = 0
        items_decreased = 0
        items_stable = 0

        for item in matched_items_data:
            q1_id = item.get("question_id_1")
            q2_id = item.get("question_id_2")
            title = item.get("title", "Câu hỏi khảo sát")
            q_type = item.get("question_type", "rating")
            raw_vals_1 = item.get("values_1", [])
            raw_vals_2 = item.get("values_2", [])

            is_scale_or_num = q_type in ("rating", "rating_scale", "linear_scale", "likert", "number", "nps")

            num_vals_1 = []
            for v in raw_vals_1:
                try:
                    num_vals_1.append(float(str(v).strip()))
                except (ValueError, TypeError):
                    pass

            num_vals_2 = []
            for v in raw_vals_2:
                try:
                    num_vals_2.append(float(str(v).strip()))
                except (ValueError, TypeError):
                    pass

            if is_scale_or_num or (len(num_vals_1) >= 2 and len(num_vals_2) >= 2):
                n1 = len(num_vals_1)
                n2 = len(num_vals_2)

                if n1 < 2 or n2 < 2:
                    m1_val = round(statistics.mean(num_vals_1), 2) if n1 > 0 else None
                    m2_val = round(statistics.mean(num_vals_2), 2) if n2 > 0 else None
                    compared_items.append({
                        "question_id_1": q1_id,
                        "question_id_2": q2_id,
                        "title": title,
                        "question_type": q_type,
                        "is_scale": True,
                        "n_wave1": n1,
                        "n_wave2": n2,
                        "mean_wave1": m1_val,
                        "mean_wave2": m2_val,
                        "mean_shift": None,
                        "percent_change": None,
                        "cohens_d": None,
                        "effect_size": "Chưa đủ mẫu",
                        "t_statistic": None,
                        "degrees_of_freedom": None,
                        "p_value": None,
                        "is_statistically_significant": False,
                        "significance_label": "n.s.",
                        "trend_direction": "STABLE",
                        "apa_summary": "Chưa đủ dữ liệu (N < 2 mỗi đợt)"
                    })
                    continue

                m1 = statistics.mean(num_vals_1)
                m2 = statistics.mean(num_vals_2)
                v1 = statistics.variance(num_vals_1) if n1 > 1 else 0.0
                v2 = statistics.variance(num_vals_2) if n2 > 1 else 0.0
                s1 = math.sqrt(v1)
                s2 = math.sqrt(v2)

                scale_means_1.append(m1)
                scale_means_2.append(m2)

                delta_m = m2 - m1
                pct_change = round((delta_m / abs(m1) * 100.0), 1) if m1 != 0 else 0.0

                denom_pooled = (n1 + n2 - 2)
                if denom_pooled > 0:
                    s_pooled_sq = ((n1 - 1) * v1 + (n2 - 1) * v2) / denom_pooled
                    s_pooled = math.sqrt(max(0.0, s_pooled_sq))
                else:
                    s_pooled = 0.0

                cohen_d = round((delta_m / s_pooled), 3) if s_pooled > 1e-6 else 0.0
                abs_d = abs(cohen_d)

                if abs_d < 0.20:
                    effect_magnitude = "Không đáng kể (Trivial, |d| < 0.2)"
                elif abs_d < 0.50:
                    effect_magnitude = "Hiệu ứng nhỏ (Small Effect, 0.2 ≤ |d| < 0.5)"
                elif abs_d < 0.80:
                    effect_magnitude = "Hiệu ứng trung bình (Medium Effect, 0.5 ≤ |d| < 0.8)"
                else:
                    effect_magnitude = "Hiệu ứng lớn (Large Effect, |d| ≥ 0.8)"

                se_diff = math.sqrt(max(1e-9, (v1 / n1) + (v2 / n2)))
                t_stat = delta_m / se_diff

                num_df = (v1 / n1 + v2 / n2) ** 2
                denom_df = ((v1 / n1) ** 2 / (n1 - 1)) + ((v2 / n2) ** 2 / (n2 - 1))
                df = round(num_df / denom_df, 1) if denom_df > 0 else float(n1 + n2 - 2)

                p_val = math.erfc(abs(t_stat) / math.sqrt(2))
                is_sig = bool(p_val < 0.05)

                if p_val < 0.001:
                    p_str = "p < .001 (***)"
                    sig_label = "Cực kỳ có ý nghĩa (p < .001)"
                elif p_val < 0.01:
                    p_str = "p < .01 (**)"
                    sig_label = "Rất có ý nghĩa (p < .01)"
                elif p_val < 0.05:
                    p_str = "p < .05 (*)"
                    sig_label = "Có ý nghĩa thống kê (p < .05)"
                else:
                    p_str = f"p = {p_val:.3f} (n.s.)"
                    sig_label = "Không có ý nghĩa (n.s.)"

                if is_sig and delta_m > 0:
                    trend = "INCREASED"
                    items_increased += 1
                elif is_sig and delta_m < 0:
                    trend = "DECREASED"
                    items_decreased += 1
                else:
                    trend = "STABLE"
                    items_stable += 1

                sign_str = "+" if cohen_d > 0 else ""
                apa = f"t({df}) = {t_stat:.2f}, {p_str}, d = {sign_str}{cohen_d:.2f}"

                compared_items.append({
                    "question_id_1": q1_id,
                    "question_id_2": q2_id,
                    "title": title,
                    "question_type": q_type,
                    "is_scale": True,
                    "n_wave1": n1,
                    "n_wave2": n2,
                    "mean_wave1": round(m1, 2),
                    "mean_wave2": round(m2, 2),
                    "std_wave1": round(s1, 2),
                    "std_wave2": round(s2, 2),
                    "mean_shift": round(delta_m, 2),
                    "percent_change": pct_change,
                    "cohens_d": cohen_d,
                    "effect_size": effect_magnitude,
                    "t_statistic": round(t_stat, 2),
                    "degrees_of_freedom": df,
                    "p_value": round(p_val, 4),
                    "is_statistically_significant": is_sig,
                    "significance_label": sig_label,
                    "trend_direction": trend,
                    "apa_summary": apa
                })
            else:
                cat_counts_1 = Counter(str(v).strip() for v in raw_vals_1 if str(v).strip())
                cat_counts_2 = Counter(str(v).strip() for v in raw_vals_2 if str(v).strip())
                n1 = sum(cat_counts_1.values())
                n2 = sum(cat_counts_2.values())

                all_opts = sorted(list(set(cat_counts_1.keys()) | set(cat_counts_2.keys())))
                cat_shifts = []
                max_shift = 0.0
                dominant_opt = None

                for opt in all_opts:
                    c1 = cat_counts_1.get(opt, 0)
                    c2 = cat_counts_2.get(opt, 0)
                    pct1 = round((c1 / n1 * 100.0), 1) if n1 > 0 else 0.0
                    pct2 = round((c2 / n2 * 100.0), 1) if n2 > 0 else 0.0
                    diff_pct = round(pct2 - pct1, 1)
                    if abs(diff_pct) > max_shift:
                        max_shift = abs(diff_pct)
                        dominant_opt = opt
                    cat_shifts.append({
                        "option": opt,
                        "count_wave1": c1,
                        "pct_wave1": pct1,
                        "count_wave2": c2,
                        "pct_wave2": pct2,
                        "delta_pct": diff_pct
                    })

                items_stable += 1
                compared_items.append({
                    "question_id_1": q1_id,
                    "question_id_2": q2_id,
                    "title": title,
                    "question_type": q_type,
                    "is_scale": False,
                    "n_wave1": n1,
                    "n_wave2": n2,
                    "mean_wave1": None,
                    "mean_wave2": None,
                    "mean_shift": None,
                    "percent_change": None,
                    "cohens_d": None,
                    "effect_size": f"Biến thiên tỷ lệ: {max_shift}% ({dominant_opt})" if dominant_opt else "Ổn định",
                    "t_statistic": None,
                    "degrees_of_freedom": None,
                    "p_value": None,
                    "is_statistically_significant": max_shift >= 10.0,
                    "significance_label": f"Dịch chuyển {max_shift}%" if max_shift >= 10.0 else "Phân bố đồng đều",
                    "trend_direction": "SHIFTED" if max_shift >= 10.0 else "STABLE",
                    "category_shifts": cat_shifts,
                    "apa_summary": f"N1 = {n1}, N2 = {n2}, Dịch chuyển lớn nhất ở '{dominant_opt}': {max_shift:+.1f}%"
                })

        overall_m1 = round(statistics.mean(scale_means_1), 2) if scale_means_1 else None
        overall_m2 = round(statistics.mean(scale_means_2), 2) if scale_means_2 else None
        overall_delta = round(overall_m2 - overall_m1, 2) if (overall_m1 is not None and overall_m2 is not None) else None

        if items_increased > items_decreased and items_increased > 0:
            conclusion = f"Xu hướng tích cực rõ rệt: Có {items_increased} chỉ tiêu tăng điểm có ý nghĩa thống kê (p < 0.05), {items_stable} chỉ tiêu ổn định và {items_decreased} chỉ tiêu giảm."
        elif items_decreased > items_increased and items_decreased > 0:
            conclusion = f"Xu hướng suy giảm cần lưu ý: Có {items_decreased} chỉ tiêu giảm điểm có ý nghĩa thống kê (p < 0.05), {items_stable} chỉ tiêu ổn định và {items_increased} chỉ tiêu tăng."
        else:
            conclusion = f"Xu hướng tổng thể ổn định: {items_stable} chỉ tiêu giữ nguyên phân bố, không có sự dịch chuyển đột biến lớn giữa hai đợt khảo sát."

        return {
            "wave1_survey": wave1_meta,
            "wave2_survey": wave2_meta,
            "matched_questions_count": len(compared_items),
            "overall_scale_mean_wave1": overall_m1,
            "overall_scale_mean_wave2": overall_m2,
            "overall_scale_delta": overall_delta,
            "items_increased_count": items_increased,
            "items_decreased_count": items_decreased,
            "items_stable_count": items_stable,
            "comparative_summary": conclusion,
            "items": compared_items
        }



    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Tính khoảng cách trắc địa đường chim bay theo mặt cầu Trái Đất (Haversine formula).
        """
        R = 6371.0  # Bán kính Trái Đất trung bình (km)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(max(0.0, a)), math.sqrt(max(0.0, 1.0 - a)))
        return R * c

    @staticmethod
    @staticmethod
    def extract_gps_point(meta_raw: Any) -> Optional[Tuple[float, float]]:
        """
        Trích xuất an toàn tọa độ (latitude, longitude) từ client_metadata hoặc dict vị trí.
        """
        if not meta_raw:
            return None
        try:
            data = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
            if not isinstance(data, dict):
                return None
            lat = data.get("latitude") or data.get("lat")
            lon = data.get("longitude") or data.get("lng") or data.get("lon")
            if lat is None or lon is None:
                loc = data.get("location") or data.get("gps")
                if isinstance(loc, dict):
                    lat = loc.get("latitude") or loc.get("lat")
                    lon = loc.get("longitude") or loc.get("lng") or loc.get("lon")
            if lat is not None and lon is not None:
                f_lat = float(lat)
                f_lon = float(lon)
                if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0:
                    return (f_lat, f_lon)
        except Exception:
            pass
        return None

    @classmethod
    def analyze_response(
        cls,
        new_answers: Dict[str, Any],
        duration_seconds: float,
        questions: List[Dict[str, Any]],
        prior_responses: Optional[List[Dict[str, Any]]] = None,
        enumerator_id: Optional[str] = None,
        quality_settings: Optional[Dict[str, Any]] = None,
        client_metadata: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Phân tích toàn diện một phản hồi mới đối chiếu với schema câu hỏi và tập phản hồi trước đó.
        """
        prior_responses = prior_responses or []
        # Cấu hình độ nhạy kiểm định chất lượng (Sensitivity settings)
        q_settings = quality_settings or {}
        sensitivity_mode = q_settings.get("sensitivity", "standard")
        
        duplicate_threshold = 0.85
        straightline_threshold = 0.85
        speed_threshold_per_question = 2.2
        
        if sensitivity_mode == "strict":
            duplicate_threshold = 0.80
            straightline_threshold = 0.75
            speed_threshold_per_question = 2.8
        elif sensitivity_mode == "lenient":
            duplicate_threshold = 0.90
            straightline_threshold = 0.90
            speed_threshold_per_question = 1.5

        if "duplicate_threshold" in q_settings:
            try:
                duplicate_threshold = float(q_settings["duplicate_threshold"])
            except (ValueError, TypeError):
                pass
        if "straightline_threshold" in q_settings:
            try:
                straightline_threshold = float(q_settings["straightline_threshold"])
            except (ValueError, TypeError):
                pass
        if "speed_threshold_per_question" in q_settings:
            try:
                speed_threshold_per_question = float(q_settings["speed_threshold_per_question"])
            except (ValueError, TypeError):
                pass

        flags = []
        score_dup = 0.0
        score_pat = 0.0
        score_logic = 0.0
        score_speed = 0.0
        score_text = 0.0
        score_enum = 0.0
        
        closest_match_id = None
        highest_similarity = 0.0

        # Lọc danh sách câu hỏi đóng để so sánh vector
        closed_q_items = [
            q for q in questions
            if q.get("question_type") not in ("long_text", "short_text")
        ]
        
        # 1. LAYER B: So sánh trùng lặp và gần trùng lặp (Hamming distance)
        if closed_q_items and prior_responses:
            new_vector = [cls.normalize_value(new_answers.get(q["id"]), q.get("question_type", "")) for q in closed_q_items]
            
            for prior in prior_responses:
                prior_answers = prior.get("answers", {})
                prior_vector = [cls.normalize_value(prior_answers.get(q["id"]), q.get("question_type", "")) for q in closed_q_items]
                
                # Tính khoảng cách Hamming
                matches = sum(1 for a, b in zip(new_vector, prior_vector) if a == b and a != "")
                valid_comparisons = sum(1 for a, b in zip(new_vector, prior_vector) if a != "" or b != "")
                
                if valid_comparisons > 0:
                    sim = matches / valid_comparisons
                    if sim > highest_similarity:
                        highest_similarity = sim
                        closest_match_id = prior.get("id")

            if highest_similarity >= 0.999:
                score_dup = 100.0
                flags.append({
                    "code": "FLAG_EXACT_DUPLICATE",
                    "severity": "CRITICAL",
                    "message": "Phản hồi có vector đáp án đóng trùng khớp 100% với một phản hồi đã gửi trước đó.",
                    "details": {"closest_response_id": closest_match_id, "similarity": 1.0}
                })
            elif highest_similarity >= duplicate_threshold:
                score_dup = highest_similarity * 90.0
                flags.append({
                    "code": "FLAG_NEAR_DUPLICATE",
                    "severity": "HIGH",
                    "message": f"Phản hồi gần trùng lặp ({highest_similarity * 100:.1f}%) với một phản hồi trước đó.",
                    "details": {"closest_response_id": closest_match_id, "similarity": round(highest_similarity, 3)}
                })
            elif highest_similarity >= 0.70:
                score_dup = 35.0
                flags.append({
                    "code": "FLAG_MODERATE_SIMILARITY",
                    "severity": "LOW",
                    "message": f"Độ tương đồng câu trả lời ở mức đáng chú ý ({highest_similarity * 100:.1f}%).",
                    "details": {"closest_response_id": closest_match_id, "similarity": round(highest_similarity, 3)}
                })

        # 2. LAYER C: Mẫu đáp án bất thường (Straightlining, Đường chéo, Zíc-zắc & Shannon Entropy)
        scale_answers = []
        for q in questions:
            qid = q["id"]
            qtype = q.get("question_type")
            if qtype in ("linear_scale", "likert", "rating", "rating_scale", "nps"):
                val = new_answers.get(qid)
                if val is not None and str(val).strip() != "":
                    scale_answers.append(str(val).strip())
            elif qtype == "matrix":
                val = new_answers.get(qid)
                if isinstance(val, dict):
                    for row_col in val.values():
                        if row_col is not None and str(row_col).strip() != "":
                            scale_answers.append(str(row_col).strip())

        if len(scale_answers) >= 4:
            # Kiểm tra Straightlining (chọn cùng 1 phương án liên tiếp)
            counts = {}
            for ans in scale_answers:
                counts[ans] = counts.get(ans, 0) + 1
            max_freq = max(counts.values()) if counts else 0
            straightline_ratio = max_freq / len(scale_answers)

            if straightline_ratio >= straightline_threshold:
                score_pat = max(score_pat, 85.0)
                flags.append({
                    "code": "FLAG_STRAIGHTLINING",
                    "severity": "HIGH",
                    "message": f"Phát hiện mẫu điền thẳng (Straightlining): {straightline_ratio * 100:.0f}% câu hỏi thang đo chọn cùng một mức đánh giá.",
                    "details": {"straightline_ratio": round(straightline_ratio, 2), "total_scale_questions": len(scale_answers)}
                })
            elif straightline_ratio >= 0.70:
                score_pat = max(score_pat, 40.0)
                flags.append({
                    "code": "FLAG_REPETITIVE_PATTERN",
                    "severity": "MEDIUM",
                    "message": "Độ đa dạng câu trả lời thang đo thấp, có xu hướng chọn lặp lại một phương án.",
                    "details": {"straightline_ratio": round(straightline_ratio, 2)}
                })

            # Chuyển đổi các câu trả lời thang đo sang dạng số để kiểm tra mẫu hình học (Geometric Pattern Detection)
            numeric_scale_vals = []
            for ans in scale_answers:
                try:
                    numeric_scale_vals.append(float(ans))
                except (ValueError, TypeError):
                    pass

            if len(numeric_scale_vals) >= 4:
                # A. Mẫu đường chéo / bậc thang tăng hoặc giảm liên tiếp (Monotonic Diagonal Pattern)
                # Ví dụ: 1 -> 2 -> 3 -> 4 -> 5 hoặc 5 -> 4 -> 3 -> 2 -> 1
                diffs = [round(numeric_scale_vals[i+1] - numeric_scale_vals[i], 2) for i in range(len(numeric_scale_vals) - 1)]
                is_all_inc = all(d == 1.0 for d in diffs)
                is_all_dec = all(d == -1.0 for d in diffs)

                if is_all_inc or is_all_dec:
                    score_pat = max(score_pat, 80.0)
                    direction_str = "tăng dần đều (1 -> 2 -> 3...)" if is_all_inc else "giảm dần đều (5 -> 4 -> 3...)"
                    flags.append({
                        "code": "FLAG_DIAGONAL_PATTERN",
                        "severity": "HIGH",
                        "message": f"Phát hiện mẫu đường chéo bậc thang ({direction_str}): Thao tác tích lướt qua loa theo đường chéo.",
                        "details": {"pattern_type": "monotonic_diagonal", "total_steps": len(numeric_scale_vals)}
                    })

                # B. Mẫu Zíc-Zắc xen kẽ lặp lại (Alternating Zig-Zag Pattern)
                # Ví dụ: 1 -> 5 -> 1 -> 5 -> 1 hoặc 5 -> 1 -> 5 -> 1
                val_set = set(numeric_scale_vals)
                if len(val_set) == 2:
                    is_alternating = all(
                        numeric_scale_vals[i] != numeric_scale_vals[i+1]
                        for i in range(len(numeric_scale_vals) - 1)
                    )
                    if is_alternating:
                        v_list = sorted(list(val_set))
                        score_pat = max(score_pat, 75.0)
                        flags.append({
                            "code": "FLAG_ZIGZAG_PATTERN",
                            "severity": "HIGH",
                            "message": f"Phát hiện mẫu zíc-zắc xen kẽ hai cực ({v_list[0]} <-> {v_list[1]}): Thể hiện thao tác điền đối xứng cơ học.",
                            "details": {"pattern_type": "alternating_zigzag", "values": v_list, "length": len(numeric_scale_vals)}
                        })

            # Tính Shannon Entropy
            entropy = 0.0
            for count in counts.values():
                p = count / len(scale_answers)
                if p > 0:
                    entropy -= p * math.log2(p)
            
            # Nếu entropy quá thấp trên tập nhiều hơn 3 câu hỏi
            if len(scale_answers) >= 5 and entropy < 0.4:
                score_pat = max(score_pat, 75.0)
                flags.append({
                    "code": "FLAG_LOW_SHANNON_ENTROPY",
                    "severity": "MEDIUM",
                    "message": f"Entropy Shannon cực thấp ({entropy:.2f}), cho thấy câu trả lời thiếu tính đa dạng tự nhiên.",
                    "details": {"entropy": round(entropy, 2)}
                })

        # 3. LAYER D: Vi phạm logic câu hỏi chéo (Cross-question Logic Contradiction)
        for q in questions:
            qid = q["id"]
            rules = q.get("logic_rules", [])
            for rule in rules:
                dep_id = rule.get("depends_on_question_id")
                op = rule.get("operator", "equals")
                expected_val = rule.get("value")
                action = rule.get("action", "show")
                
                dep_ans = cls.normalize_value(new_answers.get(dep_id))
                exp_norm = cls.normalize_value(expected_val)
                curr_ans = new_answers.get(qid)
                
                condition_met = (dep_ans == exp_norm) if op == "equals" else (dep_ans != exp_norm)
                
                # Nếu action là 'show', nhưng condition KHÔNG met mà người dùng vẫn trả lời câu qid
                if action == "show" and not condition_met:
                    if curr_ans is not None and str(curr_ans).strip() != "":
                        score_logic = max(score_logic, 80.0)
                        flags.append({
                            "code": "FLAG_LOGIC_CONTRADICTION",
                            "severity": "HIGH",
                            "message": f"Câu hỏi '{q.get('title')}' được trả lời dù điều kiện phụ thuộc vào câu trước không thỏa mãn.",
                            "details": {"question_id": qid, "dependent_on": dep_id}
                        })

        # 4. LAYER E: Thời gian hoàn thành & Tốc độ làm bài (Speeding)
        total_questions = len(questions)
        min_expected_duration = max(5.0, total_questions * speed_threshold_per_question)
        
        if duration_seconds > 0 and duration_seconds < min_expected_duration:
            ratio = duration_seconds / min_expected_duration
            if ratio < 0.4:
                score_speed = 90.0
                flags.append({
                    "code": "FLAG_EXTREME_SPEEDING",
                    "severity": "HIGH",
                    "message": f"Thời gian làm bài siêu tốc ({duration_seconds:.1f}s cho {total_questions} câu hỏi), người tham gia không đủ thời gian đọc hiểu.",
                    "details": {"duration": duration_seconds, "min_expected": min_expected_duration}
                })
            else:
                score_speed = 50.0
                flags.append({
                    "code": "FLAG_FAST_COMPLETION",
                    "severity": "MEDIUM",
                    "message": f"Thời gian làm bài nhanh bất thường ({duration_seconds:.1f}s so với chuẩn tối thiểu {min_expected_duration:.1f}s).",
                    "details": {"duration": duration_seconds, "min_expected": min_expected_duration}
                })

        # 5. LAYER F: Kiểm tra văn bản mở (Gibberish & Repetition)
        text_q_ids = [
            q["id"] for q in questions
            if q.get("question_type") in ("long_text", "short_text")
        ]
        for qid in text_q_ids:
            txt = str(new_answers.get(qid, "")).strip()
            if txt:
                # Kiểm tra ký tự lặp vô nghĩa (ví dụ: "aaaaaa", "111111", ".....", "asdfasdf")
                if len(txt) >= 4 and len(set(txt)) <= 2:
                    score_text = max(score_text, 75.0)
                    flags.append({
                        "code": "FLAG_GIBBERISH_TEXT",
                        "severity": "MEDIUM",
                        "message": f"Phát hiện văn bản có dấu hiệu vô nghĩa hoặc lặp ký tự đơn điệu: '{txt[:20]}...'",
                        "details": {"question_id": qid, "text_sample": txt[:30]}
                    })
                # Kiểm tra văn bản mở trùng hệt một phản hồi trước đó
                if prior_responses:
                    for prior in prior_responses:
                        prior_txt = str(prior.get("answers", {}).get(qid, "")).strip()
                        if len(txt) >= 15 and txt.lower() == prior_txt.lower():
                            score_text = max(score_text, 80.0)
                            flags.append({
                                "code": "FLAG_DUPLICATE_OPEN_TEXT",
                                "severity": "HIGH",
                                "message": "Câu trả lời mở trùng khớp nguyên văn với câu trả lời của một người tham gia khác.",
                                "details": {"question_id": qid, "matched_response_id": prior.get("id")}
                            })
                            break

        # 6. LAYER G: Phân tích bất thường theo điều tra viên (Enumerator & Group Anomalies)
        if enumerator_id and str(enumerator_id).strip() and prior_responses:
            enum_str = str(enumerator_id).strip()
            # Lọc các phản hồi trước của chính điều tra viên này
            enum_prior = [
                p for p in prior_responses
                if str(p.get("enumerator_id", "")).strip() == enum_str
            ]
            
            # Kiểm tra 1: Tỷ lệ phiếu rủi ro cao trong lô của điều tra viên này (nếu đã nộp >= 3 phiếu)
            if len(enum_prior) >= 3:
                high_risk_priors = sum(
                    1 for p in enum_prior
                    if float(p.get("risk_score", 0.0)) >= 60.0
                )
                if high_risk_priors / len(enum_prior) >= 0.5:
                    score_enum = max(score_enum, 75.0)
                    flags.append({
                        "code": "FLAG_ENUMERATOR_HIGH_RISK_CONCENTRATION",
                        "severity": "HIGH",
                        "message": f"Điều tra viên '{enum_str}' có tỷ lệ phiếu bị cảnh báo rủi ro cao bất thường ({high_risk_priors}/{len(enum_prior)} phiếu).",
                        "details": {"enumerator_id": enum_str, "high_risk_ratio": round(high_risk_priors / len(enum_prior), 2)}
                    })

            # Kiểm tra 2: Đo độ tương đồng nội bộ bất thường giữa các phiếu của cùng một điều tra viên
            eval_q_ids = [q["id"] for q in closed_q_items]
            if eval_q_ids and (len(enum_prior) + 1) >= 4:
                all_enum_responses = enum_prior + [{"answers": new_answers}]
                enum_answer_sets = []
                for resp in all_enum_responses:
                    ans_map = resp.get("answers", {})
                    vec = [cls.normalize_value(ans_map.get(qid)) for qid in eval_q_ids]
                    enum_answer_sets.append(vec)
                
                pairwise_sims = []
                for i in range(len(enum_answer_sets)):
                    for j in range(i + 1, len(enum_answer_sets)):
                        matches = sum(1 for a, b in zip(enum_answer_sets[i], enum_answer_sets[j]) if a == b and a != "")
                        valid = sum(1 for a, b in zip(enum_answer_sets[i], enum_answer_sets[j]) if a != "" or b != "")
                        if valid > 0:
                            pairwise_sims.append(matches / valid)
                
                if pairwise_sims:
                    avg_internal_sim = sum(pairwise_sims) / len(pairwise_sims)
                    if avg_internal_sim >= 0.80:
                        score_enum = max(score_enum, 80.0)
                        flags.append({
                            "code": "FLAG_ENUMERATOR_VARIANCE_ANOMALY",
                            "severity": "HIGH",
                            "message": f"Lô phiếu của điều tra viên '{enum_str}' có độ tương đồng nội bộ bất thường ({avg_internal_sim * 100:.1f}%), nghi ngờ tự điền hàng loạt ngoài thực địa.",
                            "details": {"enumerator_id": enum_str, "avg_internal_similarity": round(avg_internal_sim, 3), "batch_size": len(all_enum_responses)}
                        })

        # 7. LAYER H: Tính điểm rủi ro tổng hợp (Composite Risk Score: 0 - 100)
        # Tái chuẩn hóa trọng số nếu một thành phần không áp dụng
        active_weights = {}
        total_w = 0.0

        active_weights["dup"] = cls.DEFAULT_WEIGHTS["dup"]
        total_w += cls.DEFAULT_WEIGHTS["dup"]

        has_scale_questions = any(
            q.get("question_type") in ("linear_scale", "likert", "matrix", "rating", "rating_scale", "nps")
            for q in questions
        )
        if has_scale_questions:
            active_weights["pat"] = cls.DEFAULT_WEIGHTS["pat"]
            total_w += cls.DEFAULT_WEIGHTS["pat"]

        active_weights["logic"] = cls.DEFAULT_WEIGHTS["logic"]
        total_w += cls.DEFAULT_WEIGHTS["logic"]

        if duration_seconds > 0:
            active_weights["speed"] = cls.DEFAULT_WEIGHTS["speed"]
            total_w += cls.DEFAULT_WEIGHTS["speed"]

        if score_enum > 0:
            active_weights["enum"] = cls.DEFAULT_WEIGHTS["enum"]
            total_w += cls.DEFAULT_WEIGHTS["enum"]

        raw_score = 0.0
        if total_w > 0:
            raw_score += (active_weights.get("dup", 0) / total_w) * score_dup
            raw_score += (active_weights.get("pat", 0) / total_w) * score_pat
            raw_score += (active_weights.get("logic", 0) / total_w) * score_logic
            raw_score += (active_weights.get("speed", 0) / total_w) * score_speed
            raw_score += (active_weights.get("enum", 0) / total_w) * score_enum

        # Quy tắc ưu tiên cho các cờ cảnh báo đặc biệt nghiêm trọng (Overriding rules)
        if score_dup >= 100.0:
            raw_score = max(raw_score, 85.0)
        elif score_dup >= 85.0:
            raw_score = max(raw_score, 55.0)

        # Vi phạm tốc độ làm bài siêu tốc (Extreme Speeding)
        if score_speed >= 80.0:
            raw_score = max(raw_score, 75.0)

        # Mẫu điền thẳng hoặc mẫu hình học (Straightlining / Geometric)
        if score_pat >= 80.0:
            raw_score = max(raw_score, 75.0)

        # Vi phạm logic câu hỏi chéo nghiêm trọng
        if score_logic >= 80.0:
            raw_score = max(raw_score, 70.0)

        # 8. LAYER H: Kiểm định Vùng Địa Lý Thực Địa (Geofencing Compliance)
        score_geofence = 0.0
        geofence_cfg = q_settings.get("geofence")
        if geofence_cfg and isinstance(geofence_cfg, dict) and geofence_cfg.get("enabled"):
            target_lat = geofence_cfg.get("target_lat")
            target_lon = geofence_cfg.get("target_lon")
            max_radius = float(geofence_cfg.get("max_radius_km", 5.0))
            gps_pt = cls.extract_gps_point(client_metadata)
            if gps_pt and target_lat is not None and target_lon is not None:
                lat, lon = gps_pt
                dist_km = cls.haversine_distance_km(lat, lon, float(target_lat), float(target_lon))
                if dist_km > max_radius:
                    excess = dist_km - max_radius
                    score_geofence = min(100.0, 60.0 + excess * 5.0)
                    loc_name = geofence_cfg.get("location_name") or "vùng khảo sát"
                    flags.append({
                        "code": "FLAG_GEOFENCE_BREACH",
                        "severity": "HIGH",
                        "message": f"Tọa độ thực địa ({lat:.4f}, {lon:.4f}) cách tâm {loc_name} {dist_km:.2f} km, vượt quá bán kính quy định ({max_radius} km)."
                    })

        # Bổ sung phụ phí nếu có văn bản vô nghĩa/trùng lặp
        if score_text > 0:
            raw_score = max(raw_score, score_text * 0.7)

        # Vi phạm ranh giới địa lý thực địa (Geofence Breach)
        if score_geofence >= 60.0:
            raw_score = max(raw_score, score_geofence)

        composite_score = round(min(100.0, max(0.0, raw_score)), 1)
        
        if composite_score >= 70.0:
            risk_level = "high"
        elif composite_score >= 40.0:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "score_dup": round(score_dup, 1),
            "score_pattern": round(score_pat, 1),
            "score_logic": round(score_logic, 1),
            "score_speed": round(score_speed, 1),
            "score_text": round(score_text, 1),
            "score_enum": round(score_enum, 1),
            "score_geofence": round(score_geofence, 1),
            "composite_score": composite_score,
            "risk_level": risk_level,
            "flags": flags,
            "closest_match_response_id": closest_match_id,
            "highest_similarity": round(highest_similarity, 3)
        }
