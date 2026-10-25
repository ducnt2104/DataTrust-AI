import math
from typing import Dict, Any, List, Optional, Tuple


class DifferenceInDifferencesEngine:
    """
    Difference-in-Differences (DiD) & Two-Way Fixed Effects (TWFE) Policy Evaluation Engine:
    - Card & Krueger (1994) American Economic Review
    - Angrist & Pischke (2009) Mostly Harmless Econometrics (Nobel Prize in Economics 2021)
    - Bertrand, Duflo & Mullainathan (2004) How Much Should We Trust Differences-in-Differences Estimates?
    - Callaway & Sant'Anna (2021) Difference-in-Differences with Multiple Time Periods

    Tính năng cốt lõi:
    1. Ước lượng Hiệu ứng Can thiệp Trung bình trên Đối tượng Thụ hưởng (ATT - Average Treatment Effect on Treated)
    2. Bảng phân rã 2x2 Cell Means (Treatment vs Control qua 2 kỳ Pre vs Post)
    3. Hồi quy Tuyến tính OLS chuẩn hóa kiểm soát xu thế tự nhiên và sai số chuẩn
    4. Ước tính Đường phản thực tế (Counterfactual Trajectory) theo giả định Xu hướng Song song (Parallel Trends)
    5. Đồ họa Vector SVG trực quan hóa đường quỹ đạo thực tế và phản thực tế kèm khoảng cách can thiệp
    6. Tự động sinh thuyết minh học thuật chuẩn APA 7th Edition
    """

    @staticmethod
    def compute_did_analysis(
        data_rows: List[Dict[str, Any]],
        outcome_key: str,
        treatment_key: str,
        time_key: str,
        treatment_value: Any = None,
        post_value: Any = None
    ) -> Dict[str, Any]:
        """
        data_rows: Danh sách bản ghi dữ liệu khảo sát
        outcome_key: Tên trường chứa biến kết quả đo lường Y (liên tục)
        treatment_key: Tên trường phân biệt nhóm can thiệp (Treatment D=1) và nhóm đối chứng (Control D=0)
        time_key: Tên trường phân biệt thời điểm Trước can thiệp (Pre T=0) và Sau can thiệp (Post T=1)
        treatment_value: Giá trị đại diện cho D=1 (nếu None, tự động gán giá trị thứ 2 sau sắp xếp)
        post_value: Giá trị đại diện cho T=1 (nếu None, tự động gán giá trị thứ 2 sau sắp xếp)
        """
        n_obs = len(data_rows)
        if n_obs < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để ước lượng mô hình DiD (hiện có {n_obs})."
            }

        # 1. Trích xuất các giá trị hợp lệ
        valid_rows = []
        treat_vals = set()
        time_vals = set()

        for r in data_rows:
            y_raw = r.get(outcome_key)
            t_raw = r.get(treatment_key)
            tm_raw = r.get(time_key)

            if y_raw is None or t_raw is None or tm_raw is None:
                continue

            try:
                y = float(y_raw)
            except (ValueError, TypeError):
                continue

            treat_str = str(t_raw).strip()
            time_str = str(tm_raw).strip()

            if not treat_str or not time_str:
                continue

            treat_vals.add(treat_str)
            time_vals.add(time_str)
            valid_rows.append({"y": y, "d_raw": treat_str, "t_raw": time_str})

        n_valid = len(valid_rows)
        if n_valid < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 quan sát đầy đủ biến Y, Treatment và Time (hiện có {n_valid})."
            }

        if len(treat_vals) < 2:
            return {
                "status": "INVALID_TREATMENT_GROUPS",
                "message": f"Biến nhóm can thiệp '{treatment_key}' cần có ít nhất 2 nhóm (Treatment và Control)."
            }

        if len(time_vals) < 2:
            return {
                "status": "INVALID_TIME_PERIODS",
                "message": f"Biến thời gian '{time_key}' cần có ít nhất 2 mốc (Pre và Post)."
            }

        # Xác định nhãn phân loại D=1 và T=1
        sorted_treat = sorted(list(treat_vals))
        sorted_time = sorted(list(time_vals))

        treat_target = str(treatment_value) if treatment_value is not None else sorted_treat[-1]
        control_target = [v for v in sorted_treat if v != treat_target][0]

        post_target = str(post_value) if post_value is not None else sorted_time[-1]
        pre_target = [v for v in sorted_time if v != post_target][0]

        # 2. Gom cụm và tính toán 2x2 Cell Means
        # C_00: Control Pre, C_01: Treatment Pre
        # C_10: Control Post, C_11: Treatment Post
        cells: Dict[str, List[float]] = {
            "control_pre": [],
            "treat_pre": [],
            "control_post": [],
            "treat_post": []
        }

        y_all = []
        d_bin = []
        t_bin = []
        dt_bin = []

        for r in valid_rows:
            y = r["y"]
            d = 1.0 if r["d_raw"] == treat_target else 0.0
            t = 1.0 if r["t_raw"] == post_target else 0.0
            dt = d * t

            y_all.append(y)
            d_bin.append(d)
            t_bin.append(t)
            dt_bin.append(dt)

            if d == 0.0 and t == 0.0:
                cells["control_pre"].append(y)
            elif d == 1.0 and t == 0.0:
                cells["treat_pre"].append(y)
            elif d == 0.0 and t == 1.0:
                cells["control_post"].append(y)
            else:
                cells["treat_post"].append(y)

        # Kiểm tra mỗi ô có ít nhất 1 quan sát
        for c_name, c_vals in cells.items():
            if len(c_vals) == 0:
                return {
                    "status": "EMPTY_CELL",
                    "message": f"Ô dữ liệu '{c_name}' không có quan sát nào. Mô hình DiD yêu cầu dữ liệu tại cả 4 ô 2x2."
                }

        # Trung bình và phương sai từng ô
        m_cp = sum(cells["control_pre"]) / len(cells["control_pre"])
        m_tp = sum(cells["treat_pre"]) / len(cells["treat_pre"])
        m_cpost = sum(cells["control_post"]) / len(cells["control_post"])
        m_tpost = sum(cells["treat_post"]) / len(cells["treat_post"])

        n_cp = len(cells["control_pre"])
        n_tp = len(cells["treat_pre"])
        n_cpost = len(cells["control_post"])
        n_tpost = len(cells["treat_post"])

        # 3. Ước lượng DiD 2x2: delta = (m_tpost - m_tp) - (m_cpost - m_cp)
        treat_diff = m_tpost - m_tp
        control_diff = m_cpost - m_cp
        did_point_estimate = treat_diff - control_diff

        # Đường phản thực tế của Treatment Post theo xu hướng của Control:
        # Counterfactual = m_tp + (m_cpost - m_cp)
        counterfactual_target = m_tp + control_diff
        relative_att_pct = (did_point_estimate / counterfactual_target * 100.0) if abs(counterfactual_target) > 1e-6 else 0.0

        # 4. Hồi quy Tuyến tính OLS: Y = beta_0 + beta_1 * D + beta_2 * T + delta * (D * T) + e
        # X matrix: [Intercept, D, T, D*T]
        p_cols = 4
        xtx = [[0.0] * p_cols for _ in range(p_cols)]
        xty = [0.0] * p_cols

        for i in range(n_valid):
            x_vec = [1.0, d_bin[i], t_bin[i], dt_bin[i]]
            y_val = y_all[i]
            for r in range(p_cols):
                xty[r] += x_vec[r] * y_val
                for c in range(p_cols):
                    xtx[r][c] += x_vec[r] * x_vec[c]

        # Regularization nhẹ
        for r in range(1, p_cols):
            xtx[r][r] += 1e-5

        beta = DifferenceInDifferencesEngine._solve_4x4(xtx, xty)
        if not beta:
            beta = [m_cp, m_tp - m_cp, m_cpost - m_cp, did_point_estimate]

        beta_0 = beta[0]
        beta_treat = beta[1]
        beta_time = beta[2]
        beta_did = beta[3]

        # 5. Đánh giá sai số chuẩn SE, t-ratio, p-value và R^2
        residuals = []
        for i in range(n_valid):
            pred = beta[0] + beta[1] * d_bin[i] + beta[2] * t_bin[i] + beta[3] * dt_bin[i]
            residuals.append(y_all[i] - pred)

        ss_res = sum(e ** 2 for e in residuals)
        y_mean = sum(y_all) / n_valid
        ss_tot = sum((y - y_mean) ** 2 for y in y_all)
        r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 1e-9 else 0.0

        df_res = max(1, n_valid - p_cols)
        sigma_sq = ss_res / df_res

        # Ma trận nghịch đảo (X^T X)^-1 để tính SE
        inv_xtx = DifferenceInDifferencesEngine._invert_4x4(xtx)
        se_did = math.sqrt(max(inv_xtx[3][3] * sigma_sq, 1e-8)) if inv_xtx else 0.1

        t_stat = beta_did / se_did if se_did > 1e-8 else 0.0
        # p-value xấp xỉ phân phối chuẩn/Student-t
        p_val = 2.0 * (1.0 - DifferenceInDifferencesEngine._normal_cdf(abs(t_stat)))
        p_val = max(0.0001, min(1.0, p_val))

        ci_lower = beta_did - 1.96 * se_did
        ci_upper = beta_did + 1.96 * se_did

        # 6. Tạo đồ thị Vector SVG trực quan hóa đường quỹ đạo
        svg_trajectory_chart = DifferenceInDifferencesEngine._generate_did_svg(
            pre_label=pre_target,
            post_label=post_target,
            treat_label=treat_target,
            control_label=control_target,
            m_cp=m_cp,
            m_tp=m_tp,
            m_cpost=m_cpost,
            m_tpost=m_tpost,
            counterfactual=counterfactual_target,
            delta=beta_did
        )

        # 7. Biên soạn thuyết minh học thuật chuẩn APA 7th Edition
        apa_narrative = DifferenceInDifferencesEngine._generate_apa_narrative(
            n_valid=n_valid,
            treat_target=treat_target,
            control_target=control_target,
            pre_target=pre_target,
            post_target=post_target,
            beta_0=beta_0,
            beta_treat=beta_treat,
            beta_time=beta_time,
            beta_did=beta_did,
            se_did=se_did,
            t_stat=t_stat,
            p_val=p_val,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            relative_att_pct=relative_att_pct,
            r2=r2
        )

        return {
            "status": "SUCCESS",
            "sample_size": n_valid,
            "groups": {
                "treatment_name": treat_target,
                "control_name": control_target,
                "pre_period_name": pre_target,
                "post_period_name": post_target
            },
            "cell_means_2x2": {
                "control_pre": {"mean": round(m_cp, 3), "n": n_cp},
                "control_post": {"mean": round(m_cpost, 3), "n": n_cpost, "diff": round(control_diff, 3)},
                "treat_pre": {"mean": round(m_tp, 3), "n": n_tp},
                "treat_post": {"mean": round(m_tpost, 3), "n": n_tpost, "diff": round(treat_diff, 3)},
                "counterfactual_post": round(counterfactual_target, 3)
            },
            "did_treatment_effect": {
                "att_estimate": round(beta_did, 4),
                "std_error": round(se_did, 4),
                "t_statistic": round(t_stat, 2),
                "p_value": round(p_val, 4),
                "ci_95_lower": round(ci_lower, 4),
                "ci_95_upper": round(ci_upper, 4),
                "is_statistically_significant": p_val < 0.05,
                "relative_gain_pct": round(relative_att_pct, 1)
            },
            "regression_coefficients": {
                "intercept_beta_0": round(beta_0, 4),
                "baseline_selection_beta_1": round(beta_treat, 4),
                "time_trend_drift_beta_2": round(beta_time, 4),
                "interaction_att_delta": round(beta_did, 4),
                "r_squared": round(r2, 4)
            },
            "svg_trajectory_chart": svg_trajectory_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _generate_did_svg(
        pre_label: str,
        post_label: str,
        treat_label: str,
        control_label: str,
        m_cp: float,
        m_tp: float,
        m_cpost: float,
        m_tpost: float,
        counterfactual: float,
        delta: float
    ) -> str:
        """Tạo biểu đồ đường quỹ đạo Vector SVG kinh điển mô tả phương pháp DiD."""
        width = 600
        height = 320
        top_offset = 40
        bottom_offset = 60
        left_offset = 80
        right_offset = 120

        all_y = [m_cp, m_tp, m_cpost, m_tpost, counterfactual]
        min_y = min(all_y)
        max_y = max(all_y)
        y_range = max(max_y - min_y, 1.0)
        padding_y = y_range * 0.18
        y_low = min_y - padding_y
        y_high = max_y + padding_y

        plot_w = width - left_offset - right_offset
        plot_h = height - top_offset - bottom_offset

        def map_x(t_idx: int) -> float:
            return left_offset + (0.15 if t_idx == 0 else 0.85) * plot_w

        def map_y(val: float) -> float:
            norm = (val - y_low) / (y_high - y_low)
            return top_offset + (1.0 - norm) * plot_h

        x_pre = map_x(0)
        x_post = map_x(1)

        y_cp = map_y(m_cp)
        y_tp = map_y(m_tp)
        y_cpost = map_y(m_cpost)
        y_tpost = map_y(m_tpost)
        y_cf = map_y(counterfactual)

        svg = [
            f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        ]

        # Background grid
        svg.append(f'<line x1="{left_offset}" y1="{top_offset}" x2="{left_offset}" y2="{height - bottom_offset}" stroke="#334155" stroke-width="1"/>')
        svg.append(f'<line x1="{left_offset}" y1="{height - bottom_offset}" x2="{width - right_offset}" y2="{height - bottom_offset}" stroke="#334155" stroke-width="1"/>')

        # Vertical time marker lines
        svg.append(f'<line x1="{x_pre}" y1="{top_offset}" x2="{x_pre}" y2="{height - bottom_offset}" stroke="#1e293b" stroke-dasharray="4 4"/>')
        svg.append(f'<line x1="{x_post}" y1="{top_offset}" x2="{x_post}" y2="{height - bottom_offset}" stroke="#1e293b" stroke-dasharray="4 4"/>')

        svg.append(f'<text x="{x_pre}" y="{height - bottom_offset + 22}" fill="#94a3b8" font-size="11" font-weight="600" text-anchor="middle">{pre_label} (Pre)</text>')
        svg.append(f'<text x="{x_post}" y="{height - bottom_offset + 22}" fill="#94a3b8" font-size="11" font-weight="600" text-anchor="middle">{post_label} (Post)</text>')

        # 1. Control Trajectory (Blue solid)
        svg.append(f'<line x1="{x_pre}" y1="{y_cp}" x2="{x_post}" y2="{y_cpost}" stroke="#0ea5e9" stroke-width="2.5"/>')
        svg.append(f'<circle cx="{x_pre}" cy="{y_cp}" r="4.5" fill="#0ea5e9"/>')
        svg.append(f'<circle cx="{x_post}" cy="{y_cpost}" r="4.5" fill="#0ea5e9"/>')
        svg.append(f'<text x="{x_post + 12}" y="{y_cpost + 4}" fill="#0ea5e9" font-size="11" font-weight="bold">{control_label} ({m_cpost:.2f})</text>')

        # 2. Treatment Counterfactual Trajectory (Purple dashed line: Parallel Trend)
        svg.append(f'<line x1="{x_pre}" y1="{y_tp}" x2="{x_post}" y2="{y_cf}" stroke="#a855f7" stroke-width="2" stroke-dasharray="5 5"/>')
        svg.append(f'<circle cx="{x_post}" cy="{y_cf}" r="3.5" fill="#a855f7"/>')
        svg.append(f'<text x="{x_post + 12}" y="{y_cf + 4}" fill="#a855f7" font-size="10" font-style="italic">Phản thực tế ({counterfactual:.2f})</text>')

        # 3. Treatment Actual Trajectory (Emerald solid)
        svg.append(f'<line x1="{x_pre}" y1="{y_tp}" x2="{x_post}" y2="{y_tpost}" stroke="#10b981" stroke-width="3"/>')
        svg.append(f'<circle cx="{x_pre}" cy="{y_tp}" r="5" fill="#10b981"/>')
        svg.append(f'<circle cx="{x_post}" cy="{y_tpost}" r="5" fill="#10b981"/>')
        svg.append(f'<text x="{x_post + 12}" y="{y_tpost + 4}" fill="#10b981" font-size="11" font-weight="bold">{treat_label} ({m_tpost:.2f})</text>')

        # 4. Causal Gap delta bracket / arrow
        svg.append(f'<line x1="{x_post - 8}" y1="{y_cf}" x2="{x_post - 8}" y2="{y_tpost}" stroke="#f59e0b" stroke-width="2.5"/>')
        svg.append(f'<line x1="{x_post - 14}" y1="{y_cf}" x2="{x_post - 2}" y2="{y_cf}" stroke="#f59e0b" stroke-width="2"/>')
        svg.append(f'<line x1="{x_post - 14}" y1="{y_tpost}" x2="{x_post - 2}" y2="{y_tpost}" stroke="#f59e0b" stroke-width="2"/>')
        svg.append(f'<text x="{x_post - 18}" y="{(y_cf + y_tpost) / 2 + 4}" fill="#f59e0b" font-size="11" font-weight="bold" text-anchor="end">δ = {delta:+.2f}</text>')

        svg.append('</svg>')
        return "".join(svg)

    @staticmethod
    def _generate_apa_narrative(
        n_valid: int,
        treat_target: str,
        control_target: str,
        pre_target: str,
        post_target: str,
        beta_0: float,
        beta_treat: float,
        beta_time: float,
        beta_did: float,
        se_did: float,
        t_stat: float,
        p_val: float,
        ci_lower: float,
        ci_upper: float,
        relative_att_pct: float,
        r2: float
    ) -> str:
        """Biên soạn thuyết minh học thuật chuẩn APA 7th Edition."""
        sig_text = "có ý nghĩa thống kê" if p_val < 0.05 else "không đạt mức ý nghĩa thống kê truyền thống"
        direction = "gia tăng" if beta_did > 0 else "sụt giảm"

        return (
            f"Đánh giá tác động chính sách bằng phương pháp Khác biệt trong Khác biệt "
            f"(Difference-in-Differences - DiD; Card & Krueger, 1994; Angrist & Pischke, 2009) "
            f"được thực hiện trên quy mô mẫu N = {n_valid} quan sát giữa nhóm can thiệp '{treat_target}' "
            f"và nhóm đối chứng '{control_target}' qua hai thời kỳ ('{pre_target}' và '{post_target}'). "
            f"Mô hình hồi quy Hai chiều Cố định (TWFE) đạt R² = {r2:.3f}. "
            f"Trước can thiệp, mức chênh lệch cơ sở giữa hai nhóm là beta_1 = {beta_treat:.3f}. "
            f"Xu thế tự nhiên theo thời gian của nhóm đối chứng ghi nhận mức dịch chuyển beta_2 = {beta_time:.3f}. "
            f"Sau khi loại trừ độ lệch lựa chọn ban đầu và xu thế thời gian chung, hiệu ứng can thiệp nhân quả thuần túy "
            f"(Average Treatment Effect on the Treated - ATT) ước tính đạt delta = {beta_did:+.3f} "
            f"(SE = {se_did:.3f}, t = {t_stat:.2f}, p = {p_val:.4f}, 95% CI [{ci_lower:.3f}, {ci_upper:.3f}]), {sig_text}. "
            f"Mức tác động này tương đương mức {direction} thuần +{relative_att_pct:.1f}% so với quỹ đạo phản thực tế giả định."
        )

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Hàm phân phối tích lũy chuẩn CDF."""
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @staticmethod
    def _solve_4x4(A: List[List[float]], b: List[float]) -> Optional[List[float]]:
        """Khử Gauss-Jordan cho hệ phương trình 4x4."""
        n = 4
        M = [A[i][:] + [b[i]] for i in range(n)]

        for i in range(n):
            max_row = i
            max_val = abs(M[i][i])
            for r in range(i + 1, n):
                if abs(M[r][i]) > max_val:
                    max_val = abs(M[r][i])
                    max_row = r
            if max_val < 1e-12:
                return None
            M[i], M[max_row] = M[max_row], M[i]
            pivot = M[i][i]
            for c in range(i, n + 1):
                M[i][c] /= pivot
            for r in range(n):
                if r != i:
                    factor = M[r][i]
                    for c in range(i, n + 1):
                        M[r][c] -= factor * M[i][c]

        return [M[i][n] for i in range(n)]

    @staticmethod
    def _invert_4x4(A: List[List[float]]) -> Optional[List[List[float]]]:
        """Nghịch đảo ma trận 4x4 bằng Gauss-Jordan."""
        n = 4
        M = [A[i][:] + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        for i in range(n):
            max_row = i
            max_val = abs(M[i][i])
            for r in range(i + 1, n):
                if abs(M[r][i]) > max_val:
                    max_val = abs(M[r][i])
                    max_row = r
            if max_val < 1e-12:
                return None
            M[i], M[max_row] = M[max_row], M[i]
            pivot = M[i][i]
            for c in range(i, 2 * n):
                M[i][c] /= pivot
            for r in range(n):
                if r != i:
                    factor = M[r][i]
                    for c in range(i, 2 * n):
                        M[r][c] -= factor * M[i][c]

        return [[M[i][n + j] for j in range(n)] for i in range(n)]
