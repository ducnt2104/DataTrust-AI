import math
from typing import Dict, Any, List, Optional, Tuple

class DIFEngine:
    """
    Động cơ Kiểm định Bất biến Đo lường & Hàm mục Sai lệch (Differential Item Functioning - DIF).
    Phương pháp luận: Thống kê Mantel-Haenszel (Holland & Thayer, 1988)
    và Tiêu chuẩn Phân loại 3 cấp độ ETS (Educational Testing Service: Class A, B, C).
    
    Kiểm định xem một câu hỏi thang đo có thiên lệch bất công (bias) đối với một nhóm
    nhân khẩu học (Focal group) so với nhóm tham chiếu (Reference group) khi hai người
    có CÙNG điểm năng lực/thái độ tổng thể (stratified score) hay không.
    """

    @staticmethod
    def _chi2_sf(x: float, df: int = 1) -> float:
        """
        Tính xấp xỉ Survival Function (p-value = P(X >= x)) cho phân phối Chi-Square với df=1.
        Sử dụng khai triển hàm erfc (Complementary Error Function) chính xác cao:
        Với df=1, p-value = erfc(sqrt(x / 2)).
        """
        if x <= 0:
            return 1.0
        try:
            z = math.sqrt(x / 2.0)
            return math.erfc(z)
        except Exception:
            return 0.0

    @staticmethod
    def compute_mantel_haenszel_dif(
        records: List[Dict[str, Any]],
        scale_question_ids: List[str],
        grouping_var: str,
        reference_group: str,
        focal_group: str,
        num_strata: int = 4
    ) -> Dict[str, Any]:
        """
        Thực hiện phân tích DIF Mantel-Haenszel cho từng câu hỏi thang đo.
        
        Args:
            records: Danh sách bản ghi đã làm sạch, mỗi bản ghi dạng:
                     {"id": "r1", "answers": {qid: numeric_or_label_val, ...}}
            scale_question_ids: Danh sách các câu hỏi thang đo số (Likert 1-5, 1-7, 0-10...)
            grouping_var: ID câu hỏi phân nhóm (VD: Giới tính, Độ tuổi)
            reference_group: Nhóm tham chiếu (VD: "Nam", "Thành thị")
            focal_group: Nhóm tâm điểm cần kiểm định thiên lệch (VD: "Nữ", "Nông thôn")
            num_strata: Số phân tầng năng lực/tổng điểm (mặc định 4 phân vị - quartiles)
            
        Returns:
            Dict chứa kết quả DIF từng câu hỏi, phân loại Class A/B/C và tóm tắt học thuật.
        """
        # 1. Lọc và chuẩn bị dữ liệu 2 nhóm
        valid_records = []
        for r in records:
            ans = r.get("answers", {})
            grp_val = str(ans.get(grouping_var, "")).strip()
            if grp_val in (reference_group, focal_group):
                # Tính tổng điểm thang đo của người này
                scale_scores = []
                for qid in scale_question_ids:
                    v = ans.get(qid)
                    try:
                        f_v = float(v)
                        scale_scores.append(f_v)
                    except (ValueError, TypeError):
                        pass
                
                if len(scale_scores) == len(scale_question_ids) and len(scale_scores) > 0:
                    tot_score = sum(scale_scores)
                    valid_records.append({
                        "id": r.get("id"),
                        "group": grp_val,
                        "total_score": tot_score,
                        "answers": ans
                    })

        n_total = len(valid_records)
        n_ref = sum(1 for r in valid_records if r["group"] == reference_group)
        n_focal = sum(1 for r in valid_records if r["group"] == focal_group)

        if n_ref < 3 or n_focal < 3 or len(scale_question_ids) < 2:
            return {
                "reference_group": reference_group,
                "focal_group": focal_group,
                "sample_reference": n_ref,
                "sample_focal": n_focal,
                "total_eval_sample": n_total,
                "items": [],
                "summary": "Cỡ mẫu của nhóm tham chiếu hoặc nhóm tâm điểm chưa đủ (tối thiểu N >= 3 mỗi nhóm) để chạy kiểm định DIF.",
                "overall_verdict": "CHƯA_ĐỦ_MẪU"
            }

        # 2. Phân tầng mẫu theo tổng điểm (Stratification into Score Levels / Strata)
        all_totals = sorted(r["total_score"] for r in valid_records)
        # Xác định các mốc phân vị (Strata cutoffs)
        cutoffs = []
        for s in range(1, num_strata):
            idx = int(s * len(all_totals) / num_strata)
            cutoffs.append(all_totals[min(idx, len(all_totals) - 1)])

        def get_stratum(score: float) -> int:
            for s_idx, cut in enumerate(cutoffs):
                if score <= cut:
                    return s_idx
            return len(cutoffs)

        for r in valid_records:
            r["stratum"] = get_stratum(r["total_score"])

        # 3. Phân tích Mantel-Haenszel cho từng câu hỏi thang đo
        items_result = []
        class_a_count = 0
        class_b_count = 0
        class_c_count = 0

        for qid in scale_question_ids:
            # Xác định ngưỡng nhị phân hóa (Dichotomization Threshold) cho câu hỏi này:
            # Điểm >= median câu hỏi đó -> Favorable (1), < median -> Unfavorable (0)
            q_vals = []
            for r in valid_records:
                try:
                    q_vals.append(float(r["answers"].get(qid, 0)))
                except (ValueError, TypeError):
                    pass
            
            if not q_vals:
                continue

            q_vals.sort()
            med_val = q_vals[len(q_vals) // 2]

            # Bảng chéo Mantel-Haenszel qua từng tầng k
            sum_num = 0.0  # \sum A_k - E(A_k)
            sum_var = 0.0  # \sum Var(A_k)
            sum_ad = 0.0   # \sum (A_k * D_k / T_k)
            sum_bc = 0.0   # \sum (B_k * C_k / T_k)

            # Đếm số tầng thực tế có dữ liệu
            active_strata = 0

            for k in range(num_strata + 1):
                stratum_records = [r for r in valid_records if r["stratum"] == k]
                if not stratum_records:
                    continue

                # Nhóm Ref (R) và Focal (F)
                ref_records = [r for r in stratum_records if r["group"] == reference_group]
                focal_records = [r for r in stratum_records if r["group"] == focal_group]

                nR = len(ref_records)
                nF = len(focal_records)
                T = nR + nF

                if nR == 0 or nF == 0 or T < 2:
                    continue

                # Đếm số người đạt điểm cao (Favorable) và thấp (Unfavorable)
                A = sum(1 for r in ref_records if float(r["answers"].get(qid, 0)) >= med_val)
                B = nR - A
                C = sum(1 for r in focal_records if float(r["answers"].get(qid, 0)) >= med_val)
                D = nF - C

                m1 = A + C  # Tổng số người favorable
                m0 = B + D  # Tổng số người unfavorable

                if m1 == 0 or m0 == 0:
                    continue

                active_strata += 1
                e_A = (nR * m1) / T
                var_A = (nR * nF * m1 * m0) / (T * T * (T - 1)) if T > 1 else 0.0

                sum_num += (A - e_A)
                sum_var += var_A

                sum_ad += (A * D) / T
                sum_bc += (B * C) / T

            # 4. Tính toán thống kê kiểm định MH Chi-Square & Tỷ số Chênh (Odds Ratio)
            if sum_var > 0:
                # Công thức kiểm định với hiệu chỉnh liên tục (Continuity Correction):
                chi2_mh = (max(0.0, abs(sum_num) - 0.5) ** 2) / sum_var
                p_value = DIFEngine._chi2_sf(chi2_mh, df=1)
            else:
                chi2_mh = 0.0
                p_value = 1.0

            # Tính Mantel-Haenszel Common Odds Ratio (\alpha_MH)
            if sum_bc > 0:
                alpha_mh = sum_ad / sum_bc
            elif sum_ad > 0:
                alpha_mh = 10.0  # Cận trên xấp xỉ
            else:
                alpha_mh = 1.0

            # Tính chỉ số Delta ETS: \Delta_MH = -2.35 * ln(\alpha_MH)
            # Nếu alpha_mh > 1 -> Ref có ưu thế, Delta < 0
            # Nếu alpha_mh < 1 -> Focal có ưu thế, Delta > 0
            delta_mh = 0.0
            if alpha_mh > 0:
                try:
                    delta_mh = -2.35 * math.log(alpha_mh)
                except Exception:
                    delta_mh = 0.0

            abs_delta = abs(delta_mh)

            # 5. Phân loại theo tiêu chuẩn ETS (Educational Testing Service):
            # Class A: Negligible DIF (p >= 0.05 HOẶC |Delta| < 1.0)
            # Class B: Moderate DIF (p < 0.05 VÀ 1.0 <= |Delta| < 1.5)
            # Class C: Large DIF (p < 0.05 VÀ |Delta| >= 1.5)
            if p_value >= 0.05 or abs_delta < 1.0:
                ets_class = "A"
                ets_label = "Class A (Công Bằng / Không Thiên Lệch)"
                action_recommendation = "Giữ lại câu hỏi (Đạt độ công bằng đo lường)"
                class_a_count += 1
            elif 1.0 <= abs_delta < 1.5:
                ets_class = "B"
                ets_label = "Class B (Thiên Lệch Vừa Phải)"
                action_recommendation = "Cần theo dõi và xem xét lại cách diễn đạt"
                class_b_count += 1
            else:
                ets_class = "C"
                ets_label = "Class C (Thiên Lệch Nghiêm Trọng)"
                action_recommendation = "Khuyến nghị loại bỏ hoặc viết lại để tránh thiên lệch"
                class_c_count += 1

            favored_group = "Trung lập"
            if p_value < 0.05:
                if delta_mh < -0.1:
                    favored_group = f"Ưu thế cho '{reference_group}'"
                elif delta_mh > 0.1:
                    favored_group = f"Ưu thế cho '{focal_group}'"

            items_result.append({
                "question_id": qid,
                "median_threshold": round(med_val, 2),
                "active_strata_count": active_strata,
                "chi2_mh": round(chi2_mh, 3),
                "p_value": round(p_value, 4),
                "alpha_odds_ratio": round(alpha_mh, 3),
                "delta_ets": round(delta_mh, 3),
                "abs_delta_ets": round(abs_delta, 3),
                "ets_class": ets_class,
                "ets_label": ets_label,
                "favored_group": favored_group,
                "action_recommendation": action_recommendation,
                "is_statistically_significant": bool(p_value < 0.05)
            })

        # Đánh giá tổng thể
        if class_c_count > 0:
            overall_verdict = "PHÁT_HIỆN_THIÊN_LỆCH_NGHIÊM_TRỌNG"
            summary_msg = (
                f"Phát hiện {class_c_count} câu hỏi có thiên lệch đo lường nghiêm trọng (Class C) giữa '{reference_group}' "
                f"và '{focal_group}'. Các câu hỏi này có thể dẫn đến kết luận thiên lệch khi so sánh giữa hai nhóm."
            )
        elif class_b_count > 0:
            overall_verdict = "CÓ_THIÊN_LỆCH_VỪA_PHẢI"
            summary_msg = (
                f"Phát hiện {class_b_count} câu hỏi có thiên lệch vừa phải (Class B). "
                f"Có {class_a_count} câu hỏi đạt chuẩn công bằng đo lường (Class A)."
            )
        else:
            overall_verdict = "ĐẠT_CHUẨN_BẤT_BIẾN_ĐO_LƯỜNG"
            summary_msg = (
                f"Toàn bộ {len(items_result)} câu hỏi thang đo đều đạt chuẩn công bằng đo lường (100% Class A) "
                f"giữa hai nhóm '{reference_group}' và '{focal_group}'. Thang đo có tính bất biến đo lường (Measurement Invariance) cao."
            )

        return {
            "reference_group": reference_group,
            "focal_group": focal_group,
            "grouping_variable": grouping_var,
            "sample_reference": n_ref,
            "sample_focal": n_focal,
            "total_eval_sample": n_total,
            "strata_count": num_strata,
            "class_a_count": class_a_count,
            "class_b_count": class_b_count,
            "class_c_count": class_c_count,
            "overall_verdict": overall_verdict,
            "summary": summary_msg,
            "items": items_result
        }
