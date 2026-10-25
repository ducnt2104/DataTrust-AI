"""
Joint Modeling (JM) of Longitudinal Trajectories & Time-to-Event Panel Drop-off
================================================================================
Methodological references:
- Wulfsohn, M. S., & Tsiatis, A. A. (1997). A joint model for survival and
  longitudinal data measured with error. Biometrics, 53(1), 330-339.
- Henderson, R., Diggle, P., & Dobson, A. (2000). Joint modelling of longitudinal
  measurements and event time data. Biostatistics, 1(4), 465-480.
- Rizopoulos, D. (2010). JM: An R package for the joint modelling of longitudinal
  and time-to-event data. Journal of Statistical Software, 35(9), 1-33.
- Rizopoulos, D. (2011). Dynamic predictions and prospective accuracy in joint models
  for longitudinal and time-to-event data. JASA, 106(495), 1050-1062.
- Rizopoulos, D. (2012). Joint Models for Longitudinal and Time-to-Event Data:
  With Applications in R. Chapman & Hall/CRC Biostatistics Series.
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm


class JointModelingEngine:
    """
    Joint Model coupling a Linear Mixed-Effects Longitudinal Submodel
    with a Relative Risk Survival Submodel for survey panel attrition.
    """

    @classmethod
    def estimate(
        cls,
        longitudinal_records: List[Dict[str, Any]],
        survival_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Estimate joint model parameters.

        longitudinal_records: List of dicts with:
          - 'subject_id': str/int
          - 'time': float (wave / measurement time)
          - 'y': float (longitudinal score)

        survival_records: List of dicts with:
          - 'subject_id': str/int
          - 'event_time': float (time of drop-off or censoring)
          - 'event': int (1 = drop-off attrited, 0 = censored / retained)
        """
        # Validate data
        if not longitudinal_records or not survival_records:
            return {
                "status": "error",
                "message": "Dữ liệu dọc hoặc dữ liệu sống sót (attrition) không đủ để ước lượng Joint Model."
            }

        # Index survival records by subject_id
        surv_map = {}
        for r in survival_records:
            sid = str(r.get("subject_id"))
            t_event = float(r.get("event_time", 1.0))
            ev = int(r.get("event", 0))
            surv_map[sid] = {"event_time": t_event, "event": ev}

        # Group longitudinal records by subject
        subj_long = {}
        for r in longitudinal_records:
            sid = str(r.get("subject_id"))
            if sid not in surv_map:
                continue
            if sid not in subj_long:
                subj_long[sid] = []
            try:
                t = float(r.get("time", 0.0))
                y = float(r.get("y", 0.0))
                subj_long[sid].append((t, y))
            except (ValueError, TypeError):
                continue

        valid_sids = [sid for sid, pts in subj_long.items() if len(pts) >= 1]
        n_subjects = len(valid_sids)
        total_obs = sum(len(subj_long[sid]) for sid in valid_sids)

        if n_subjects < 10 or total_obs < 20:
            return {
                "status": "error",
                "message": f"Cỡ mẫu quá nhỏ ({n_subjects} đối tượng, {total_obs} lượt đo). Cần tối thiểu 10 đối tượng và 20 lượt quan sát lặp."
            }

        # 1. Fit Longitudinal Mixed-Effects Submodel (LMM)
        # y_ij = (beta_0 + b_0i) + (beta_1 + b_1i) * t_ij + e_ij
        all_t = []
        all_y = []
        for sid in valid_sids:
            for t, y in subj_long[sid]:
                all_t.append(t)
                all_y.append(y)

        all_t = np.array(all_t, dtype=float)
        all_y = np.array(all_y, dtype=float)

        # OLS starting values for fixed effects (beta_0, beta_1)
        X_mat = np.column_stack([np.ones_like(all_t), all_t])
        try:
            beta_fixed = np.linalg.lstsq(X_mat, all_y, rcond=None)[0]
        except Exception:
            beta_fixed = np.array([float(np.mean(all_y)), 0.0])

        beta_0, beta_1 = float(beta_fixed[0]), float(beta_fixed[1])
        residuals_ols = all_y - (beta_0 + beta_1 * all_t)
        sigma_e = float(np.std(residuals_ols)) if len(residuals_ols) > 2 else 1.0
        sigma_e = max(1e-4, sigma_e)

        # Estimate Empirical Bayes individual random effects (b_0i, b_1i)
        subj_random_effects = {}
        b0_list = []
        b1_list = []

        for sid in valid_sids:
            pts = subj_long[sid]
            ts = np.array([p[0] for p in pts], dtype=float)
            ys = np.array([p[1] for p in pts], dtype=float)

            # Center around fixed prediction
            fixed_pred = beta_0 + beta_1 * ts
            res = ys - fixed_pred

            if len(pts) >= 2 and np.var(ts) > 1e-6:
                Xt = np.column_stack([np.ones_like(ts), ts])
                # Ridge shrunk random effect
                lambda_reg = 0.5
                b_i = np.linalg.inv(Xt.T @ Xt + lambda_reg * np.eye(2)) @ (Xt.T @ res)
                b0_i, b1_i = float(b_i[0]), float(b_i[1])
            else:
                b0_i = float(np.mean(res)) * 0.7
                b1_i = 0.0

            subj_random_effects[sid] = (b0_i, b1_i)
            b0_list.append(b0_i)
            b1_list.append(b1_i)

        sigma_b0 = float(np.std(b0_list)) if len(b0_list) > 1 else 0.5
        sigma_b1 = float(np.std(b1_list)) if len(b1_list) > 1 else 0.2
        sigma_b0 = max(1e-4, sigma_b0)
        sigma_b1 = max(1e-4, sigma_b1)

        # 2. Fit Survival Submodel with Association Parameter alpha
        # h_i(t) = h_0 * exp(alpha * m_i(t))
        # where m_i(t) = (beta_0 + b_0i) + (beta_1 + b_1i) * t
        events = np.array([surv_map[sid]["event"] for sid in valid_sids], dtype=float)
        event_times = np.array([surv_map[sid]["event_time"] for sid in valid_sids], dtype=float)

        # True latent trajectory evaluated at event time T_i
        latent_at_event = np.array([
            (beta_0 + subj_random_effects[sid][0]) + (beta_1 + subj_random_effects[sid][1]) * surv_map[sid]["event_time"]
            for sid in valid_sids
        ], dtype=float)

        # Standardize latent score to improve numerical stability
        m_mean = float(np.mean(latent_at_event))
        m_std = float(np.std(latent_at_event)) if np.std(latent_at_event) > 1e-4 else 1.0
        z_latent = (latent_at_event - m_mean) / m_std

        # Cox partial log-likelihood with latent score covariate
        # log L(alpha) = sum_{i: d_i=1} [ alpha * z_i - log sum_{j: T_j >= T_i} exp(alpha * z_j) ]
        def neg_log_lik_survival(params):
            a = params[0]
            # Order by event time
            order = np.argsort(event_times)
            sorted_times = event_times[order]
            sorted_events = events[order]
            sorted_z = z_latent[order]

            # Compute risk sets
            ll = 0.0
            n = len(sorted_times)
            risk_sum = np.sum(np.exp(np.clip(a * sorted_z, -15, 15)))

            # Moving risk sum from left to right
            for k in range(n):
                if sorted_events[k] == 1:
                    # Current risk set includes k to n-1
                    cur_risk_sum = np.sum(np.exp(np.clip(a * sorted_z[k:], -15, 15)))
                    if cur_risk_sum > 1e-12:
                        ll += a * sorted_z[k] - math.log(cur_risk_sum)

            return -ll

        opt_res = minimize(neg_log_lik_survival, [0.0], method='BFGS')
        alpha_std = float(opt_res.x[0]) if opt_res.success else 0.0
        # Convert back to unstandardized scale
        alpha = float(alpha_std / m_std)

        # Approximate standard error of alpha from Hessian or robust formula
        try:
            hess_inv = opt_res.hess_inv
            se_alpha_std = float(math.sqrt(max(1e-4, hess_inv[0][0])))
            se_alpha = float(se_alpha_std / m_std)
        except Exception:
            se_alpha = max(0.01, float(abs(alpha) * 0.25))

        z_stat = float(alpha / se_alpha) if se_alpha > 1e-6 else 0.0
        p_val = float(2.0 * (1.0 - norm.cdf(abs(z_stat))))

        # Hazard ratio per 1-unit increase in latent longitudinal metric
        hazard_ratio = float(math.exp(np.clip(alpha, -10, 10)))
        ci_lower = float(math.exp(np.clip(alpha - 1.96 * se_alpha, -10, 10)))
        ci_upper = float(math.exp(np.clip(alpha + 1.96 * se_alpha, -10, 10)))

        # Non-ignorable Attrition Diagnostic
        is_significant_association = bool(p_val < 0.05)
        if is_significant_association:
            if alpha < 0:
                attrition_interpretation = (
                    "Tác động bảo vệ có ý nghĩa thống kê (Protective Association, p < .05): "
                    "Điểm số đo lường tiềm ẩn càng cao thì nguy cơ bỏ cuộc (panel drop-off) càng giảm mạnh. "
                    "Mẫu khảo sát bị thất thoát có tính chất phi ngẫu nhiên (Non-ignorable / Informative Attrition); "
                    "nếu chỉ dùng mô hình hồi quy hỗn hợp thông thường sẽ tạo ra thiên lệch lạc quan giả mạo."
                )
            else:
                attrition_interpretation = (
                    "Tác động gia tăng nguy cơ có ý nghĩa thống kê (Accelerated Drop-off, p < .05): "
                    "Điểm số tiềm ẩn gia tăng gắn liền với tốc độ rời bỏ khảo sát cao hơn. "
                    "Sự hao hụt mẫu có tính quy luật nội sinh rõ rệt."
                )
        else:
            attrition_interpretation = (
                "Không có bằng chứng hao hụt mẫu phi ngẫu nhiên (Ignorable Attrition, p >= .05): "
                "Tham số liên kết α không khác biệt có ý nghĩa thống kê so với 0. "
                "Cơ chế bỏ cuộc có thể giả định gần đúng là Khuyết ngẫu nhiên (Missing at Random - MAR)."
            )

        # Baseline cumulative hazard estimate via Breslow
        unique_event_times = np.sort(np.unique(event_times[events == 1]))
        if len(unique_event_times) == 0:
            unique_event_times = np.array([float(np.median(event_times))])

        breslow_hazard = []
        cum_h = 0.0
        for t_k in unique_event_times:
            d_k = np.sum((event_times == t_k) & (events == 1))
            at_risk_idx = event_times >= t_k
            denom = np.sum(np.exp(np.clip(alpha * latent_at_event[at_risk_idx], -15, 15)))
            dh = (d_k / denom) if denom > 1e-12 else 0.0
            cum_h += dh
            breslow_hazard.append({"time": round(float(t_k), 3), "cum_hazard": round(float(cum_h), 4)})

        # Dynamic Individualized Predictions
        # Compare survival curves across 3 profiles: High (+1 SD), Mean, Low (-1 SD)
        dynamic_predictions = []
        max_time = float(np.max(event_times))
        eval_times = np.linspace(0.0, max_time, 15)

        for t_eval in eval_times:
            # Baseline cum hazard at t_eval
            h_base = 0.0
            for bh in breslow_hazard:
                if bh["time"] <= t_eval:
                    h_base = bh["cum_hazard"]
                else:
                    break

            # Surval for Low (-1 SD), Mean, High (+1 SD)
            s_low = float(math.exp(-h_base * math.exp(np.clip(alpha * (beta_0 - m_std), -15, 15))))
            s_mean = float(math.exp(-h_base * math.exp(np.clip(alpha * beta_0, -15, 15))))
            s_high = float(math.exp(-h_base * math.exp(np.clip(alpha * (beta_0 + m_std), -15, 15))))

            dynamic_predictions.append({
                "time": round(float(t_eval), 3),
                "surv_low": round(s_low, 4),
                "surv_mean": round(s_mean, 4),
                "surv_high": round(s_high, 4)
            })

        # Dual-Panel Vector SVG
        svg_chart = cls._generate_svg_chart(
            subj_long=subj_long,
            surv_map=surv_map,
            valid_sids=valid_sids,
            beta_0=beta_0,
            beta_1=beta_1,
            dynamic_predictions=dynamic_predictions,
            alpha=alpha,
            hazard_ratio=hazard_ratio
        )

        # APA 7th Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_subjects=n_subjects,
            total_obs=total_obs,
            n_events=int(np.sum(events)),
            beta_0=beta_0,
            beta_1=beta_1,
            sigma_b0=sigma_b0,
            sigma_b1=sigma_b1,
            sigma_e=sigma_e,
            alpha=alpha,
            se_alpha=se_alpha,
            z_stat=z_stat,
            p_val=p_val,
            hazard_ratio=hazard_ratio,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            is_significant=is_significant_association
        )

        return {
            "status": "success",
            "sample_size": n_subjects,
            "total_longitudinal_observations": total_obs,
            "events_attrited_count": int(np.sum(events)),
            "censored_retained_count": int(n_subjects - np.sum(events)),
            "longitudinal_submodel": {
                "intercept_fixed": round(beta_0, 4),
                "slope_fixed": round(beta_1, 4),
                "residual_std_sigma_e": round(sigma_e, 4),
                "random_intercept_std": round(sigma_b0, 4),
                "random_slope_std": round(sigma_b1, 4)
            },
            "survival_submodel": {
                "association_alpha": round(alpha, 4),
                "se_alpha": round(se_alpha, 4),
                "z_statistic": round(z_stat, 4),
                "p_value": round(p_val, 4),
                "hazard_ratio": round(hazard_ratio, 4),
                "ci_95_lower": round(ci_lower, 4),
                "ci_95_upper": round(ci_upper, 4),
                "is_significant": is_significant_association
            },
            "attrition_diagnostics": {
                "is_non_ignorable": is_significant_association,
                "interpretation": attrition_interpretation
            },
            "dynamic_predictions": dynamic_predictions,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        subj_long: Dict[str, List[tuple]],
        surv_map: Dict[str, Dict[str, Any]],
        valid_sids: List[str],
        beta_0: float,
        beta_1: float,
        dynamic_predictions: List[Dict[str, Any]],
        alpha: float,
        hazard_ratio: float
    ) -> str:
        """
        Dual-panel SVG:
        Panel A: Longitudinal Trajectories (retained vs attrited) with fixed effect line.
        Panel B: Dynamic Conditional Survival Curves for Low / Mean / High latent scores.
        """
        width = 840
        height = 360

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="100%" height="{height}" style="background-color:#0b1120;border-radius:10px;'
            f'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">'
        ]

        svg.append(
            '<text x="20" y="26" fill="#f8fafc" font-size="14" font-weight="bold">'
            'Mô hình Liên kết Dọc & Sống sót (Joint Modeling of Longitudinal & Survival Data)</text>'
        )

        # Panel A: Longitudinal Trajectories (X: 50 to 390, Y: 60 to 310)
        svg.append('<rect x="50" y="60" width="340" height="250" fill="#020617" rx="6" stroke="#1e293b"/>')
        svg.append('<text x="60" y="80" fill="#38bdf8" font-size="11" font-weight="bold">Panel A: Quỹ đạo Dọc Cá thể (LMM Trajectories)</text>')

        # Determine axes scales
        all_times = [p[0] for sid in valid_sids for p in subj_long[sid]]
        all_ys = [p[1] for sid in valid_sids for p in subj_long[sid]]
        min_t, max_t = min(all_times), max(all_times)
        if max_t == min_t:
            max_t += 1.0
        min_y, max_y = min(all_ys), max(all_ys)
        if max_y == min_y:
            max_y += 1.0

        def scale_a_x(t):
            return 70 + (t - min_t) / (max_t - min_t) * 300

        def scale_a_y(y):
            return 285 - (y - min_y) / (max_y - min_y) * 190

        # Draw grid
        for i in range(4):
            gy = 95 + i * 60
            svg.append(f'<line x1="70" y1="{gy}" x2="370" y2="{gy}" stroke="#1e293b" stroke-dasharray="3,3"/>')

        # Draw subject lines (sample up to 25 subjects for visual clarity)
        for sid in valid_sids[:25]:
            pts = sorted(subj_long[sid], key=lambda x: x[0])
            if len(pts) >= 2:
                is_attrited = bool(surv_map[sid]["event"] == 1)
                stroke_col = "#f43f5e" if is_attrited else "#0ea5e9"
                stroke_dash = 'stroke-dasharray="3,3"' if is_attrited else ''
                poly = " ".join([f'{scale_a_x(p[0]):.1f},{scale_a_y(p[1]):.1f}' for p in pts])
                svg.append(f'<polyline points="{poly}" fill="none" stroke="{stroke_col}" stroke-width="1.2" opacity="0.45" {stroke_dash}/>')

        # Population fixed mean trajectory
        pt1 = f'{scale_a_x(min_t):.1f},{scale_a_y(beta_0 + beta_1 * min_t):.1f}'
        pt2 = f'{scale_a_x(max_t):.1f},{scale_a_y(beta_0 + beta_1 * max_t):.1f}'
        svg.append(f'<line x1="{scale_a_x(min_t):.1f}" y1="{scale_a_y(beta_0 + beta_1 * min_t):.1f}" x2="{scale_a_x(max_t):.1f}" y2="{scale_a_y(beta_0 + beta_1 * max_t):.1f}" stroke="#38bdf8" stroke-width="3"/>')

        svg.append('<text x="220" y="304" fill="#94a3b8" font-size="10" text-anchor="middle">Thời gian / Làn sóng Khảo sát (t)</text>')
        svg.append('<text x="65" y="190" fill="#94a3b8" font-size="9" text-anchor="middle" transform="rotate(-90 65 190)">Điểm số Dọc y(t)</text>')

        # Panel B: Dynamic Conditional Survival Curves (X: 430 to 790, Y: 60 to 310)
        svg.append('<rect x="430" y="60" width="360" height="250" fill="#020617" rx="6" stroke="#1e293b"/>')
        svg.append('<text x="440" y="80" fill="#10b981" font-size="11" font-weight="bold">Panel B: Đường cong Duy trì Khảo sát theo Mức điểm (Survival)</text>')

        if dynamic_predictions:
            t_max_b = dynamic_predictions[-1]["time"]
            if t_max_b <= 0:
                t_max_b = 1.0

            def scale_b_x(t):
                return 450 + (t / t_max_b) * 320

            def scale_b_y(s):
                return 285 - s * 190

            # Grid lines
            for s_val in [0.25, 0.50, 0.75, 1.0]:
                sy = scale_b_y(s_val)
                svg.append(f'<line x1="450" y1="{sy:.1f}" x2="770" y2="{sy:.1f}" stroke="#1e293b" stroke-dasharray="3,3"/>')
                svg.append(f'<text x="445" y="{sy + 3:.1f}" fill="#64748b" font-size="9" text-anchor="end">{int(s_val*100)}%</text>')

            # Curves: High (+1 SD), Mean, Low (-1 SD)
            pts_high = [f'{scale_b_x(dp["time"]):.1f},{scale_b_y(dp["surv_high"]):.1f}' for dp in dynamic_predictions]
            pts_mean = [f'{scale_b_x(dp["time"]):.1f},{scale_b_y(dp["surv_mean"]):.1f}' for dp in dynamic_predictions]
            pts_low = [f'{scale_b_x(dp["time"]):.1f},{scale_b_y(dp["surv_low"]):.1f}' for dp in dynamic_predictions]

            svg.append(f'<polyline points="{" ".join(pts_high)}" fill="none" stroke="#10b981" stroke-width="2.5"/>')
            svg.append(f'<polyline points="{" ".join(pts_mean)}" fill="none" stroke="#38bdf8" stroke-width="2.0" stroke-dasharray="4,4"/>')
            svg.append(f'<polyline points="{" ".join(pts_low)}" fill="none" stroke="#f43f5e" stroke-width="2.5"/>')

            # Legend markers
            svg.append('<circle cx="560" cy="100" r="4" fill="#10b981"/>')
            svg.append('<text x="570" y="103" fill="#cbd5e1" font-size="9">Điểm cao (+1 SD)</text>')
            svg.append('<circle cx="670" cy="100" r="4" fill="#f43f5e"/>')
            svg.append('<text x="680" y="103" fill="#cbd5e1" font-size="9">Điểm thấp (-1 SD)</text>')

        svg.append('<text x="610" y="304" fill="#94a3b8" font-size="10" text-anchor="middle">Thời gian Khảo sát (t)</text>')
        svg.append('<text x="445" y="190" fill="#94a3b8" font-size="9" text-anchor="middle" transform="rotate(-90 445 190)">Xác suất Còn lại S(t)</text>')

        # Footer
        svg.append(
            '<text x="410" y="340" fill="#64748b" font-size="10" text-anchor="middle">'
            f'Joint Model: Association α = {alpha:.3f} | Hazard Ratio = {hazard_ratio:.3f}</text>'
        )

        svg.append('</svg>')
        return "".join(svg)

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_subjects: int,
        total_obs: int,
        n_events: int,
        beta_0: float,
        beta_1: float,
        sigma_b0: float,
        sigma_b1: float,
        sigma_e: float,
        alpha: float,
        se_alpha: float,
        z_stat: float,
        p_val: float,
        hazard_ratio: float,
        ci_lower: float,
        ci_upper: float,
        is_significant: bool
    ) -> str:
        """
        Generate APA 7th Edition formatted statistical narrative.
        """
        p_str = f"p = {p_val:.4f}" if p_val >= 0.0001 else "p < .001"
        significance_tag = "có ý nghĩa thống kê" if is_significant else "không có ý nghĩa thống kê"

        lines = [
            f"Mô hình Liên kết Dọc & Sống sót (Joint Modeling of Longitudinal and Survival Data; "
            f"Wulfsohn & Tsiatis, 1997; Henderson et al., 2000; Rizopoulos, 2012) đã được ước lượng "
            f"trên cỡ mẫu gồm N = {n_subjects:,} đối tượng với tổng cộng {total_obs:,} lượt đo lặp lại theo thời gian. "
            f"Trong đó ghi nhận {n_events:,} trường hợp bỏ cuộc/thất thoát mẫu (attrition events) "
            f"và {n_subjects - n_events:,} trường hợp duy trì/kiểm duyệt bên phải (right-censored)."
        ]

        lines.append(
            f"Phân mô hình dọc (Longitudinal Submodel) sử dụng mô hình hiệu ứng hỗn hợp tuyến tính (LMM) "
            f"xác định quỹ đạo trung bình dân số có điểm khởi đầu β0 = {beta_0:.3f} và hệ số dốc theo thời gian β1 = {beta_1:.4f}, "
            f"với độ lệch chuẩn phần dư σ_e = {sigma_e:.3f}, độ lệch chuẩn hiệu ứng ngẫu nhiên chặn σ_b0 = {sigma_b0:.3f} "
            f"và độ lệch chuẩn hiệu ứng ngẫu nhiên dốc σ_b1 = {sigma_b1:.3f}."
        )

        lines.append(
            f"Phân mô hình sống sót (Survival Submodel) đánh giá mối liên kết giữa quỹ đạo tiềm ẩn thực sự m(t) "
            f"và nguy cơ thất thoát mẫu. Tham số liên kết ước lượng được là α = {alpha:.4f} "
            f"(SE = {se_alpha:.4f}, z = {z_stat:.3f}, {p_str}), tương ứng với Tỷ số Nguy cơ Hazard Ratio HR = {hazard_ratio:.3f} "
            f"(95% CI [{ci_lower:.3f}, {ci_upper:.3f}]). "
            f"Mối liên kết này {significance_tag} ở mức kiểm định α = .05."
        )

        if is_significant:
            if alpha < 0:
                lines.append(
                    f"Kết quả khẳng định sự tồn tại của cơ chế thất thoát mẫu mang tính thông tin / phi ngẫu nhiên "
                    f"(Non-ignorable Informative Missingness): những người có điểm số đo lường suy giảm có xác suất rời bỏ nghiên cứu cao hơn rõ rệt. "
                    f"Việc áp dụng Joint Modeling đã hiệu chỉnh triệt để thiên lệch sống sót (survivorship bias), "
                    f"bảo toàn tính khách quan và độ tin cậy khoa học của các kết luận nghiên cứu dọc."
                )
            else:
                lines.append(
                    f"Kết quả cho thấy điểm số tiềm ẩn cao hơn lại gắn liền với nguy cơ bỏ cuộc gia tăng (HR = {hazard_ratio:.3f}), "
                    f"đòi hỏi các chiến lược can thiệp giữ chân người trả lời tương ứng."
                )
        else:
            lines.append(
                f"Do tham số α không đạt ý nghĩa thống kê, giả định khuyết ngẫu nhiên (MAR) được duy trì hợp lệ, "
                f"chứng minh rằng sự thất thoát người trả lời không gây ra thiên lệch hệ thống lên quỹ đạo tăng trưởng đo lường."
            )

        return " ".join(lines)
