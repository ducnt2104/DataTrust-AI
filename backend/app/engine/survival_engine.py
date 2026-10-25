import math
from typing import Dict, Any, List, Optional, Tuple


class SurvivalDropOffEngine:
    """
    Động cơ Phân tích Sống sót & Thời gian Bỏ dở Khảo sát (Survival Analysis & Time-to-Drop-off Engine).
    Tuân thủ các tiêu chuẩn phương pháp luận thống kê & dịch tễ học quốc tế:
    - Kaplan, E. L., & Meier, P. (1958). Nonparametric estimation from incomplete observations.
      Journal of the American Statistical Association, 53(282), 457-481.
    - Cox, D. R. (1972). Regression models and life-tables.
      Journal of the Royal Statistical Society: Series B (Methodological), 34(2), 187-202.
    - Mantel, N. (1966). Evaluation of survival data and two new rank order statistics arising in its consideration.
      Cancer Chemotherapy Reports, 50(3), 163-170.
    - Greenwood, M. (1926). The natural duration of cancer.
      Reports on Public Health and Medical Subjects, 33, 1-26.
    - Couper, M. P. (2001). Web surveys: A review of issues and approaches.
      Public Opinion Quarterly, 64(4), 464-494.
    """

    @classmethod
    def analyze_survival(
        cls,
        durations: List[float],
        events: List[int],
        group_labels: Optional[List[str]] = None,
        time_milestones: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Phân tích thời gian sống sót / duy trì tham gia khảo sát (Time-to-Drop-off).
        
        Tham số:
        - durations: Danh sách thời gian tính bằng giây (hoặc phút) của từng người tham gia
        - events: Trạng thái kết quả (1 = Drop-off / Bỏ dở, 0 = Censored / Hoàn thành toàn bài)
        - group_labels: Nhãn phân nhóm tùy chọn (ví dụ: 'Mobile' vs 'Desktop')
        - time_milestones: Các mốc thời gian đánh giá tỷ lệ duy trì (mặc định [60s, 180s, 300s, 600s])
        """
        n = len(durations)
        if n < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 5 người tham gia để phân tích đường cong sống sót (hiện có {n})."
            }

        if len(events) != n:
            return {
                "status": "INVALID_DATA",
                "message": "Độ dài mảng thời gian và mảng biến cố không khớp nhau."
            }

        # 1. Tính toán Kaplan-Meier cho toàn bộ tập mẫu (Overall KM Curve)
        overall_km = cls._compute_kaplan_meier(durations, events)

        # 2. Đánh giá tỷ lệ sống sót tại các mốc thời gian then chốt (Survival Milestones)
        milestones = time_milestones or [60.0, 180.0, 300.0, 600.0]
        milestone_results = []
        for ms in milestones:
            # Tìm bước sống sót tại t <= ms
            surv_at_t = 1.0
            for step in overall_km["steps"]:
                if step["time"] <= ms:
                    surv_at_t = step["survival_prob"]
                else:
                    break
            milestone_results.append({
                "time_seconds": ms,
                "time_minutes": round(ms / 60.0, 1),
                "survival_probability": round(surv_at_t, 3),
                "retention_percentage": round(surv_at_t * 100.0, 1),
                "dropout_percentage": round((1.0 - surv_at_t) * 100.0, 1)
            })

        # 3. Phân tích so sánh 2 nhóm (nếu có group_labels với 2 nhóm)
        group_comparison = None
        log_rank_result = None
        cox_hazard_ratio = None

        if group_labels and len(group_labels) == n:
            unique_groups = sorted(list(set(group_labels)))
            if len(unique_groups) == 2:
                g1_name, g2_name = unique_groups[0], unique_groups[1]
                idx_g1 = [i for i, g in enumerate(group_labels) if g == g1_name]
                idx_g2 = [i for i, g in enumerate(group_labels) if g == g2_name]

                if len(idx_g1) >= 2 and len(idx_g2) >= 2:
                    km_g1 = cls._compute_kaplan_meier(
                        [durations[i] for i in idx_g1],
                        [events[i] for i in idx_g1]
                    )
                    km_g2 = cls._compute_kaplan_meier(
                        [durations[i] for i in idx_g2],
                        [events[i] for i in idx_g2]
                    )

                    # Log-Rank Test (Mantel-Cox)
                    log_rank_result = cls._compute_log_rank_test(
                        durations_1=[durations[i] for i in idx_g1],
                        events_1=[events[i] for i in idx_g1],
                        durations_2=[durations[i] for i in idx_g2],
                        events_2=[events[i] for i in idx_g2],
                        group1_name=g1_name,
                        group2_name=g2_name
                    )

                    # Ước lượng Tỷ số Nguy cơ Cox Hazard Ratio (HR)
                    # HR = (O1 / E1) / (O2 / E2)
                    o1 = log_rank_result["observed_events_1"]
                    e1 = log_rank_result["expected_events_1"]
                    o2 = log_rank_result["observed_events_2"]
                    e2 = log_rank_result["expected_events_2"]

                    if e1 > 1e-4 and e2 > 1e-4 and o2 > 0:
                        hr = (o1 / e1) / (o2 / e2)
                        # Phương sai của ln(HR) xấp xỉ 1/E1 + 1/E2
                        se_ln_hr = math.sqrt((1.0 / max(0.5, e1)) + (1.0 / max(0.5, e2)))
                        ci_lower = math.exp(math.log(hr) - 1.96 * se_ln_hr)
                        ci_upper = math.exp(math.log(hr) + 1.96 * se_ln_hr)
                        cox_hazard_ratio = {
                            "reference_group": g2_name,
                            "comparison_group": g1_name,
                            "hazard_ratio": round(hr, 2),
                            "ci_95_lower": round(ci_lower, 2),
                            "ci_95_upper": round(ci_upper, 2),
                            "risk_interpretation": (
                                f"Nhóm '{g1_name}' có nguy cơ bỏ dở giữa chừng cao gấp {hr:.2f} lần "
                                f"so với nhóm '{g2_name}' (95% CI [{ci_lower:.2f}, {ci_upper:.2f}])."
                                if hr > 1.0 else
                                f"Nhóm '{g1_name}' có nguy cơ bỏ dở giữa chừng thấp hơn {((1.0 - hr)*100):.1f}% "
                                f"so với nhóm '{g2_name}' (HR = {hr:.2f}, 95% CI [{ci_lower:.2f}, {ci_upper:.2f}])."
                            )
                        }

                    group_comparison = {
                        "group_1": {
                            "name": g1_name,
                            "sample_size": len(idx_g1),
                            "events_count": sum(events[i] for i in idx_g1),
                            "median_survival": km_g1["median_survival_time"],
                            "svg_path": km_g1["svg_path"]
                        },
                        "group_2": {
                            "name": g2_name,
                            "sample_size": len(idx_g2),
                            "events_count": sum(events[i] for i in idx_g2),
                            "median_survival": km_g2["median_survival_time"],
                            "svg_path": km_g2["svg_path"]
                        }
                    }

        # 4. Biên soạn Thuyết minh Học thuật Chuẩn APA 7th Edition
        total_events = sum(events)
        total_censored = n - total_events
        completion_pct = (total_censored / n) * 100.0

        apa_parts = [
            f"Phân tích sống sót Kaplan-Meier (Kaplan & Meier, 1958) được thực hiện trên mẫu N = {n} người tham gia "
            f"(trong đó {total_censored} trường hợp hoàn thành toàn bài [{completion_pct:.1f}%] và {total_events} trường hợp bỏ dở giữa chừng [{100.0 - completion_pct:.1f}%])."
        ]

        if overall_km["median_survival_time"] is not None:
            apa_parts.append(
                f"Thời gian duy trì trung vị ước tính đạt Mdn = {overall_km['median_survival_time']:.1f} giây "
                f"(~{overall_km['median_survival_time']/60.0:.1f} phút)."
            )
        else:
            apa_parts.append(
                "Do tỷ lệ hoàn thành vượt quá 50%, thời gian duy trì trung vị không đạt ngưỡng cắt 50% (S(t) > 0.50 trên toàn bộ tiến trình khảo sát)."
            )

        if log_rank_result:
            apa_parts.append(
                f"Kiểm định Log-Rank Mantel-Cox so sánh giữa nhóm '{log_rank_result['group1_name']}' và '{log_rank_result['group2_name']}' "
                f"cho thấy sự khác biệt {'' if log_rank_result['p_value'] < 0.05 else 'không '}có ý nghĩa thống kê "
                f"(chi^2({log_rank_result['degrees_of_freedom']}) = {log_rank_result['chi2_statistic']:.2f}, p = {log_rank_result['p_value']:.4f})."
            )

        if cox_hazard_ratio:
            apa_parts.append(
                f"Tỷ số nguy cơ ước lượng đạt HR = {cox_hazard_ratio['hazard_ratio']:.2f} "
                f"(95% CI [{cox_hazard_ratio['ci_95_lower']:.2f}, {cox_hazard_ratio['ci_95_upper']}])."
            )

        apa_narrative = " ".join(apa_parts)

        return {
            "status": "SUCCESS",
            "total_participants": n,
            "completed_count": total_censored,
            "drop_off_count": total_events,
            "overall_completion_rate": round(completion_pct, 1),
            "overall_drop_off_rate": round(100.0 - completion_pct, 1),
            "overall_km": overall_km,
            "milestones": milestone_results,
            "group_comparison": group_comparison,
            "log_rank_test": log_rank_result,
            "cox_hazard_ratio": cox_hazard_ratio,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _compute_kaplan_meier(cls, durations: List[float], events: List[int]) -> Dict[str, Any]:
        """Tính toán ước lượng sống sót Kaplan-Meier và sai số chuẩn Greenwood."""
        n = len(durations)
        # Sắp xếp theo thời gian tăng dần
        records = sorted(zip(durations, events), key=lambda x: x[0])
        
        # Gom cụm theo thời gian duy nhất
        unique_times = sorted(list(set(r[0] for r in records)))
        
        n_at_risk = n
        current_s = 1.0
        greenwood_sum = 0.0
        
        steps = []
        median_survival = None

        # Điểm mốc t = 0
        steps.append({
            "time": 0.0,
            "at_risk": n,
            "events": 0,
            "censored": 0,
            "survival_prob": 1.0,
            "se_greenwood": 0.0,
            "ci_lower": 1.0,
            "ci_upper": 1.0
        })

        for t in unique_times:
            # Đếm số sự kiện và số kiểm duyệt tại t
            d_i = sum(1 for d, e in records if d == t and e == 1)
            c_i = sum(1 for d, e in records if d == t and e == 0)

            if n_at_risk <= 0:
                break

            if d_i > 0:
                current_s *= (1.0 - (d_i / n_at_risk))
                if (n_at_risk - d_i) > 0:
                    greenwood_sum += d_i / (n_at_risk * (n_at_risk - d_i))

            var_s = (current_s ** 2) * greenwood_sum
            se_s = math.sqrt(max(0.0, var_s))
            ci_low = max(0.0, current_s - 1.96 * se_s)
            ci_high = min(1.0, current_s + 1.96 * se_s)

            if median_survival is None and current_s <= 0.5:
                median_survival = t

            steps.append({
                "time": round(t, 1),
                "at_risk": n_at_risk,
                "events": d_i,
                "censored": c_i,
                "survival_prob": round(current_s, 4),
                "se_greenwood": round(se_s, 4),
                "ci_lower": round(ci_low, 4),
                "ci_upper": round(ci_high, 4)
            })

            n_at_risk -= (d_i + c_i)

        # Tính toán tọa độ vẽ đồ thị đường bậc thang SVG (Step-Function Path)
        # Khung đồ thị: viewBox 520 x 240
        # x: mapping [0, max_time] -> [50, 490] (width = 440)
        # y: mapping [0.0, 1.0] -> [200, 30] (height = 170)
        max_time = max(1.0, max(durations))
        svg_points = []
        prev_x = 50.0
        prev_y = 200.0 - (1.0 * 170.0)
        svg_commands = [f"M {prev_x:.1f},{prev_y:.1f}"]

        for step in steps[1:]:
            t = step["time"]
            s = step["survival_prob"]
            cur_x = 50.0 + (t / max_time) * 440.0
            cur_y = 200.0 - (s * 170.0)

            # Bậc thang ngang trước rồi mới rơi thẳng đứng xuống
            svg_commands.append(f"L {cur_x:.1f},{prev_y:.1f}")
            svg_commands.append(f"L {cur_x:.1f},{cur_y:.1f}")
            svg_points.append({
                "time": t,
                "prob": s,
                "svg_x": round(cur_x, 1),
                "svg_y": round(cur_y, 1)
            })
            prev_x = cur_x
            prev_y = cur_y

        # Kéo dài đến max_time nếu chưa tới
        end_x = 50.0 + 440.0
        svg_commands.append(f"L {end_x:.1f},{prev_y:.1f}")

        return {
            "max_observed_time": round(max_time, 1),
            "median_survival_time": round(median_survival, 1) if median_survival is not None else None,
            "steps": steps,
            "svg_path": " ".join(svg_commands),
            "svg_points": svg_points
        }

    @classmethod
    def _compute_log_rank_test(
        cls,
        durations_1: List[float],
        events_1: List[int],
        durations_2: List[float],
        events_2: List[int],
        group1_name: str,
        group2_name: str
    ) -> Dict[str, Any]:
        """Kiểm định Log-Rank Mantel-Cox so sánh 2 đường cong sống sót."""
        # Gom toàn bộ thời gian có sự kiện xảy ra
        all_times = sorted(list(set(
            [d for d, e in zip(durations_1, events_1) if e == 1] +
            [d for d, e in zip(durations_2, events_2) if e == 1]
        )))

        sum_o1 = sum(events_1)
        sum_o2 = sum(events_2)
        sum_e1 = 0.0
        sum_v1 = 0.0

        for t in all_times:
            # Số người có nguy cơ tại t trong từng nhóm
            y1 = sum(1 for d in durations_1 if d >= t)
            y2 = sum(1 for d in durations_2 if d >= t)
            y_tot = y1 + y2

            # Số sự kiện tại t
            d1 = sum(1 for d, e in zip(durations_1, events_1) if d == t and e == 1)
            d2 = sum(1 for d, e in zip(durations_2, events_2) if d == t and e == 1)
            d_tot = d1 + d2

            if y_tot > 1 and d_tot > 0:
                e1 = d_tot * (y1 / y_tot)
                sum_e1 += e1
                if y_tot > 1:
                    v1 = (d_tot * (y1 / y_tot) * (y2 / y_tot) * (y_tot - d_tot)) / (y_tot - 1)
                    sum_v1 += v1

        # Chi-Square statistic
        chi2 = ((sum_o1 - sum_e1) ** 2) / max(1e-6, sum_v1)
        # Tính p-value với df = 1 (Phân phối Chi-Square df=1 xấp xỉ qua hàm erfc)
        # P(Chi2 >= x) = 2 * (1 - Phi(sqrt(x))) = erfc(sqrt(x/2))
        p_val = math.erfc(math.sqrt(chi2 / 2.0))
        p_val = max(0.0001, min(1.0, p_val))

        return {
            "group1_name": group1_name,
            "group2_name": group2_name,
            "observed_events_1": sum_o1,
            "expected_events_1": round(sum_e1, 2),
            "observed_events_2": sum_o2,
            "expected_events_2": round(sum(events_1 + events_2) - sum_e1, 2),
            "chi2_statistic": round(chi2, 3),
            "degrees_of_freedom": 1,
            "p_value": round(p_val, 4),
            "is_statistically_significant": p_val < 0.05
        }
