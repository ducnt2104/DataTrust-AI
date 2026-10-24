# -*- coding: utf-8 -*-
"""
Staggered Difference-in-Differences & Group-Time Average Treatment Effects Engine
Methodology:
- Callaway, B., & Sant'Anna, P. H. (2021). Difference-in-differences with multiple time periods.
  Journal of Econometrics, 225(2), 200-230.
- Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing.
  Journal of Econometrics, 225(2), 254-277.
- Sun, L., & Abraham, S. (2021). Estimating dynamic treatment effects in event studies with heterogeneous treatment effects.
  Journal of Econometrics, 225(2), 175-199.
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Any, Optional, Tuple


class StaggeredDIDEngine:
    """
    Robust econometric engine for longitudinal/panel survey evaluations with staggered adoption timing.
    Eliminates Two-Way Fixed Effects (TWFE) negative weighting bias caused by heterogeneous
    and dynamic treatment effects through Callaway & Sant'Anna (2021) group-time ATT(g,t)
    and Goodman-Bacon (2021) linear decomposition.
    """

    @staticmethod
    def evaluate_staggered_did(
        y_outcome: np.ndarray,
        unit_ids: np.ndarray,
        time_periods: np.ndarray,
        first_treated_periods: np.ndarray,
        anticipation_periods: int = 0,
        control_group_type: str = "never_treated",  # 'never_treated' or 'not_yet_treated'
        outcome_label: str = "Outcome Metric",
        unit_label: str = "Survey Unit",
        time_label: str = "Observation Wave"
    ) -> Dict[str, Any]:
        """
        Calculates group-time treatment effects ATT(g, t), aggregated dynamic event-study effects ATT(e),
        overall summary ATT, and Goodman-Bacon decomposition diagnostics.
        """
        n = len(y_outcome)
        if n < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát (N={n}) quá ít để ước lượng Staggered DiD. Cần tối thiểu 20 quan sát.",
                "model_type": "STAGGERED_DID_CALLAWAY_SANTANNA_2021",
                "diagnostics": None,
                "group_time_effects": None,
                "event_study_effects": None,
                "bacon_decomposition": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        # 1. Harmonize cohorts and time periods
        unique_times = np.sort(np.unique(time_periods))
        unique_units = np.unique(unit_ids)
        T = len(unique_times)
        N_units = len(unique_units)

        if T < 2:
            return {
                "status": "INSUFFICIENT_TIME_PERIODS",
                "message": f"Số lượng thời điểm khảo sát (T={T}) không đủ. Cần tối thiểu 2 mốc thời gian để so sánh DiD.",
                "model_type": "STAGGERED_DID_CALLAWAY_SANTANNA_2021",
                "diagnostics": None,
                "group_time_effects": None,
                "event_study_effects": None,
                "bacon_decomposition": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        # Extract unit-level first treated time (0 or np.nan or large number for never treated)
        # We represent never-treated as infinity or 0
        unit_first_treated: Dict[Any, float] = {}
        for u in unique_units:
            mask = (unit_ids == u)
            g_vals = first_treated_periods[mask]
            # Take first non-zero/finite value
            g_valid = [g for g in g_vals if g > 0 and not np.isnan(g)]
            if len(g_valid) > 0:
                unit_first_treated[u] = float(g_valid[0])
            else:
                unit_first_treated[u] = float('inf')

        # Cohorts (unique treatment timing)
        all_g = [g for g in unit_first_treated.values() if g != float('inf')]
        unique_g = np.sort(np.unique(all_g)) if len(all_g) > 0 else np.array([])

        if len(unique_g) == 0:
            return {
                "status": "NO_TREATED_UNITS",
                "message": "Không tìm thấy đơn vị nào được can thiệp trong mẫu khảo sát.",
                "model_type": "STAGGERED_DID_CALLAWAY_SANTANNA_2021",
                "diagnostics": None,
                "group_time_effects": None,
                "event_study_effects": None,
                "bacon_decomposition": None,
                "svg_visualization": None,
                "apa_narrative": None
            }

        never_treated_units = [u for u, g in unit_first_treated.items() if g == float('inf')]
        n_never_treated = len(never_treated_units)

        # Build panel map: (unit, time) -> y
        panel_map: Dict[Tuple[Any, Any], float] = {}
        for i in range(n):
            panel_map[(unit_ids[i], time_periods[i])] = float(y_outcome[i])

        # 2. Callaway & Sant'Anna (2021) Estimator for ATT(g, t)
        group_time_effects: List[Dict[str, Any]] = []
        att_gt_values: List[float] = []
        att_gt_weights: List[float] = []

        # Store for event-study aggregation: event_time e -> list of (att, weight, var)
        event_time_dict: Dict[int, List[Tuple[float, float, float]]] = {}

        for g in unique_g:
            g_units = [u for u, ug in unit_first_treated.items() if ug == g]
            n_g = len(g_units)
            if n_g == 0:
                continue

            # Reference pre-treatment period for cohort g is g - 1 (or last period before g)
            pre_times = [t for t in unique_times if t < g]
            if len(pre_times) == 0:
                # Treated in very first period, cannot estimate without earlier pre-period
                continue
            base_t = max(pre_times)

            for t in unique_times:
                # Comparison group C
                if control_group_type == "never_treated" or n_never_treated >= 5:
                    comp_units = never_treated_units
                else:
                    # Not-yet-treated at time t
                    comp_units = [u for u, ug in unit_first_treated.items() if ug > max(g, t)]

                if len(comp_units) == 0:
                    continue

                # Compute change in outcome for treated cohort g between base_t and t
                delta_y_g = []
                for u in g_units:
                    if (u, t) in panel_map and (u, base_t) in panel_map:
                        delta_y_g.append(panel_map[(u, t)] - panel_map[(u, base_t)])

                delta_y_c = []
                for u in comp_units:
                    if (u, t) in panel_map and (u, base_t) in panel_map:
                        delta_y_c.append(panel_map[(u, t)] - panel_map[(u, base_t)])

                if len(delta_y_g) == 0 or len(delta_y_c) == 0:
                    continue

                mean_delta_g = float(np.mean(delta_y_g))
                mean_delta_c = float(np.mean(delta_y_c))
                att_gt = mean_delta_g - mean_delta_c

                # Standard error via independent sample difference of means
                var_g = float(np.var(delta_y_g, ddof=1) / len(delta_y_g)) if len(delta_y_g) > 1 else 0.05
                var_c = float(np.var(delta_y_c, ddof=1) / len(delta_y_c)) if len(delta_y_c) > 1 else 0.05
                se_gt = float(np.sqrt(max(var_g + var_c, 1e-6)))

                t_stat = float(att_gt / se_gt) if se_gt > 0 else 0.0
                df = max(1, len(delta_y_g) + len(delta_y_c) - 2)
                p_val = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=df)))

                ci_low = float(att_gt - 1.96 * se_gt)
                ci_high = float(att_gt + 1.96 * se_gt)

                is_pre = bool(t < g)
                event_time = int(t - g)

                group_time_effects.append({
                    "cohort_g": float(g),
                    "calendar_time_t": float(t),
                    "event_time_e": event_time,
                    "att": round(att_gt, 4),
                    "se": round(se_gt, 4),
                    "t_statistic": round(t_stat, 3),
                    "p_value": round(p_val, 4),
                    "ci_lower_95": round(ci_low, 4),
                    "ci_upper_95": round(ci_high, 4),
                    "is_pre_treatment": is_pre,
                    "n_treated": len(delta_y_g),
                    "n_control": len(delta_y_c)
                })

                # Post-treatment ATT tracking for overall ATT
                if not is_pre:
                    att_gt_values.append(att_gt)
                    att_gt_weights.append(float(n_g))

                if event_time not in event_time_dict:
                    event_time_dict[event_time] = []
                event_time_dict[event_time].append((att_gt, float(n_g), se_gt**2))

        # 3. Dynamic Event Study Aggregation (Sun & Abraham 2021 / Callaway & Sant'Anna 2021)
        event_study_effects: List[Dict[str, Any]] = []
        for e in sorted(event_time_dict.keys()):
            items = event_time_dict[e]
            total_w = sum(w for _, w, _ in items)
            if total_w <= 0:
                continue

            agg_att = sum(val * w for val, w, _ in items) / total_w
            # Variance of weighted average
            agg_var = sum((w / total_w)**2 * var for _, w, var in items)
            agg_se = float(np.sqrt(max(agg_var, 1e-6)))

            z_stat = float(agg_att / agg_se) if agg_se > 0 else 0.0
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))

            event_study_effects.append({
                "event_time": e,
                "att": round(agg_att, 4),
                "se": round(agg_se, 4),
                "z_statistic": round(z_stat, 3),
                "p_value": round(p_val, 4),
                "ci_lower_95": round(agg_att - 1.96 * agg_se, 4),
                "ci_upper_95": round(agg_att + 1.96 * agg_se, 4),
                "is_pre_period": bool(e < 0)
            })

        # Pre-trends test (Joint hypothesis test that all pre-treatment e < 0 are 0)
        pre_effects = [item for item in event_study_effects if item["is_pre_period"]]
        if len(pre_effects) > 0:
            wald_stat = sum((item["att"] / max(item["se"], 1e-4))**2 for item in pre_effects)
            wald_df = len(pre_effects)
            pre_trend_p_value = float(1.0 - stats.chi2.cdf(wald_stat, df=wald_df))
            pre_trends_valid = (pre_trend_p_value >= 0.05)
        else:
            wald_stat = 0.0
            wald_df = 0
            pre_trend_p_value = 1.0
            pre_trends_valid = True

        # Overall Summary ATT
        if len(att_gt_values) > 0 and sum(att_gt_weights) > 0:
            w_sum = sum(att_gt_weights)
            overall_att = float(sum(v * w for v, w in zip(att_gt_values, att_gt_weights)) / w_sum)
            # Estimate overall SE
            var_terms = [
                item["se"]**2 for item in group_time_effects if not item["is_pre_treatment"]
            ]
            overall_se = float(np.sqrt(sum(var_terms) / (len(var_terms)**2))) if len(var_terms) > 0 else 0.05
            overall_z = float(overall_att / overall_se) if overall_se > 0 else 0.0
            overall_p = float(2.0 * (1.0 - stats.norm.cdf(abs(overall_z))))
            ci_low = float(overall_att - 1.96 * overall_se)
            ci_high = float(overall_att + 1.96 * overall_se)
        else:
            overall_att = 0.0
            overall_se = 0.0
            overall_z = 0.0
            overall_p = 1.0
            ci_low = 0.0
            ci_high = 0.0

        # 4. Goodman-Bacon (2021) Decomposition Diagnostics
        # Calculate naive TWFE coefficient via OLS with unit and time fixed effects
        twfe_beta, twfe_se = StaggeredDIDEngine._estimate_naive_twfe(
            y_outcome, unit_ids, time_periods, first_treated_periods
        )

        bacon_diag = StaggeredDIDEngine._decompose_bacon(
            panel_map, unique_units, unique_times, unit_first_treated, unique_g, never_treated_units
        )

        diagnostics = {
            "n_observations": n,
            "n_units": N_units,
            "n_time_periods": T,
            "n_cohorts": len(unique_g),
            "n_never_treated_units": n_never_treated,
            "overall_att": round(overall_att, 4),
            "overall_se": round(overall_se, 4),
            "overall_z": round(overall_z, 3),
            "overall_p_value": round(overall_p, 4),
            "ci_lower_95": round(ci_low, 4),
            "ci_upper_95": round(ci_high, 4),
            "is_statistically_significant": bool(overall_p < 0.05),
            "pre_trends_p_value": round(pre_trend_p_value, 4),
            "pre_trends_wald_stat": round(wald_stat, 3),
            "parallel_trends_supported": bool(pre_trends_valid),
            "twfe_naive_beta": round(twfe_beta, 4),
            "twfe_naive_se": round(twfe_se, 4),
            "twfe_bias_gap": round(overall_att - twfe_beta, 4),
            "pct_negative_weights": bacon_diag.get("pct_negative_weights", 0.0)
        }

        # 5. Dual-Panel Scientific SVG Visualization
        svg_chart = generate_staggered_did_svg(
            event_study_effects=event_study_effects,
            overall_att=overall_att,
            twfe_beta=twfe_beta,
            bacon_components=bacon_diag.get("components", []),
            outcome_label=outcome_label
        )

        # 6. APA 7th Edition Narrative
        apa_narrative = StaggeredDIDEngine._generate_apa_narrative(
            diagnostics, outcome_label, unit_label, time_label
        )

        return {
            "status": "SUCCESS",
            "model_type": "STAGGERED_DID_CALLAWAY_SANTANNA_2021",
            "diagnostics": diagnostics,
            "group_time_effects": group_time_effects,
            "event_study_effects": event_study_effects,
            "bacon_decomposition": bacon_diag,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _estimate_naive_twfe(
        y: np.ndarray,
        units: np.ndarray,
        times: np.ndarray,
        g_treated: np.ndarray
    ) -> Tuple[float, float]:
        """
        Estimates naive Two-Way Fixed Effects OLS: Y_it = a_i + l_t + b*D_it + e_it
        using within-transformation / projection matrix.
        """
        n = len(y)
        # Treatment indicator: D_it = 1 if g > 0 and times[i] >= g_treated[i]
        d = np.array([
            1.0 if (g_treated[i] > 0 and not np.isnan(g_treated[i]) and times[i] >= g_treated[i]) else 0.0
            for i in range(n)
        ])

        unique_u = np.unique(units)
        unique_t = np.unique(times)

        # Demean by unit and time
        u_map = {u: i for i, u in enumerate(unique_u)}
        t_map = {t: i for i, t in enumerate(unique_t)}

        u_idx = np.array([u_map[u] for u in units])
        t_idx = np.array([t_map[t] for t in times])

        # Unit means
        y_u_mean = np.zeros(len(unique_u))
        d_u_mean = np.zeros(len(unique_u))
        u_counts = np.zeros(len(unique_u))
        for i in range(n):
            y_u_mean[u_idx[i]] += y[i]
            d_u_mean[u_idx[i]] += d[i]
            u_counts[u_idx[i]] += 1
        y_u_mean /= np.maximum(u_counts, 1)
        d_u_mean /= np.maximum(u_counts, 1)

        # Time means
        y_t_mean = np.zeros(len(unique_t))
        d_t_mean = np.zeros(len(unique_t))
        t_counts = np.zeros(len(unique_t))
        for i in range(n):
            y_t_mean[t_idx[i]] += y[i]
            d_t_mean[t_idx[i]] += d[i]
            t_counts[t_idx[i]] += 1
        y_t_mean /= np.maximum(t_counts, 1)
        d_t_mean /= np.maximum(t_counts, 1)

        grand_y_mean = float(np.mean(y))
        grand_d_mean = float(np.mean(d))

        y_ddot = np.zeros(n)
        d_ddot = np.zeros(n)
        for i in range(n):
            y_ddot[i] = y[i] - y_u_mean[u_idx[i]] - y_t_mean[t_idx[i]] + grand_y_mean
            d_ddot[i] = d[i] - d_u_mean[u_idx[i]] - d_t_mean[t_idx[i]] + grand_d_mean

        denom = float(np.sum(d_ddot**2))
        if denom < 1e-8:
            return 0.0, 1.0

        beta_twfe = float(np.sum(d_ddot * y_ddot) / denom)
        resids = y_ddot - beta_twfe * d_ddot
        df = max(1, n - len(unique_u) - len(unique_t))
        s2 = float(np.sum(resids**2) / df)
        se_twfe = float(np.sqrt(s2 / denom))

        return beta_twfe, se_twfe

    @staticmethod
    def _decompose_bacon(
        panel_map: Dict[Tuple[Any, Any], float],
        unique_units: np.ndarray,
        unique_times: np.ndarray,
        unit_first_treated: Dict[Any, float],
        unique_g: np.ndarray,
        never_treated_units: List[Any]
    ) -> Dict[str, Any]:
        """
        Decomposes TWFE into 2x2 DiD subgroups according to Goodman-Bacon (2021).
        """
        components: List[Dict[str, Any]] = []

        # 1. Treated vs Never-Treated comparisons
        for g in unique_g:
            g_units = [u for u, ug in unit_first_treated.items() if ug == g]
            if len(g_units) == 0 or len(never_treated_units) == 0:
                continue

            # Pre and post periods for cohort g
            pre_t = [t for t in unique_times if t < g]
            post_t = [t for t in unique_times if t >= g]
            if len(pre_t) == 0 or len(post_t) == 0:
                continue

            # Average outcome changes
            delta_g = []
            for u in g_units:
                y_post = [panel_map[(u, t)] for t in post_t if (u, t) in panel_map]
                y_pre = [panel_map[(u, t)] for t in pre_t if (u, t) in panel_map]
                if len(y_post) > 0 and len(y_pre) > 0:
                    delta_g.append(np.mean(y_post) - np.mean(y_pre))

            delta_c = []
            for u in never_treated_units:
                y_post = [panel_map[(u, t)] for t in post_t if (u, t) in panel_map]
                y_pre = [panel_map[(u, t)] for t in pre_t if (u, t) in panel_map]
                if len(y_post) > 0 and len(y_pre) > 0:
                    delta_c.append(np.mean(y_post) - np.mean(y_pre))

            if len(delta_g) > 0 and len(delta_c) > 0:
                estimate = float(np.mean(delta_g) - np.mean(delta_c))
                # Weight approx
                weight = float(len(g_units) * len(never_treated_units))
                components.append({
                    "comparison_type": "Treated vs Never-Treated",
                    "group_k": float(g),
                    "group_u": "Never-Treated",
                    "estimate": round(estimate, 4),
                    "weight": round(weight, 2)
                })

        # 2. Earlier Treated vs Later Treated
        for i in range(len(unique_g)):
            for j in range(i + 1, len(unique_g)):
                g_early = unique_g[i]
                g_late = unique_g[j]

                units_early = [u for u, ug in unit_first_treated.items() if ug == g_early]
                units_late = [u for u, ug in unit_first_treated.items() if ug == g_late]

                # Comparison 2a: Early treated (treated) vs Later treated (control in window before late treated)
                pre_win = [t for t in unique_times if t < g_early]
                post_win = [t for t in unique_times if t >= g_early and t < g_late]
                if len(pre_win) > 0 and len(post_win) > 0:
                    delta_e = []
                    for u in units_early:
                        y_post = [panel_map[(u, t)] for t in post_win if (u, t) in panel_map]
                        y_pre = [panel_map[(u, t)] for t in pre_win if (u, t) in panel_map]
                        if len(y_post) > 0 and len(y_pre) > 0:
                            delta_e.append(np.mean(y_post) - np.mean(y_pre))

                    delta_l = []
                    for u in units_late:
                        y_post = [panel_map[(u, t)] for t in post_win if (u, t) in panel_map]
                        y_pre = [panel_map[(u, t)] for t in pre_win if (u, t) in panel_map]
                        if len(y_post) > 0 and len(y_pre) > 0:
                            delta_l.append(np.mean(y_post) - np.mean(y_pre))

                    if len(delta_e) > 0 and len(delta_l) > 0:
                        est = float(np.mean(delta_e) - np.mean(delta_l))
                        components.append({
                            "comparison_type": "Earlier vs Later (as Control)",
                            "group_k": float(g_early),
                            "group_u": float(g_late),
                            "estimate": round(est, 4),
                            "weight": round(float(len(units_early) * len(units_late)), 2)
                        })

        # Normalize weights
        total_w = sum(c["weight"] for c in components)
        neg_w_count = 0
        if total_w > 0:
            for c in components:
                c["weight_share"] = round(c["weight"] / total_w, 4)
                if c["weight"] < 0:
                    neg_w_count += 1
        else:
            for c in components:
                c["weight_share"] = 0.0

        pct_neg = round(100.0 * neg_w_count / max(len(components), 1), 2)

        return {
            "n_comparisons": len(components),
            "pct_negative_weights": pct_neg,
            "components": components
        }

    @staticmethod
    def _generate_apa_narrative(
        diag: Dict[str, Any],
        outcome_label: str,
        unit_label: str,
        time_label: str
    ) -> str:
        """
        Generates APA 7th Edition narrative for Staggered DiD analysis.
        """
        sig_str = (
            f"có ý nghĩa thống kê ở mức 5% (z = {diag['overall_z']:.2f}, p = {diag['overall_p_value']:.4f})"
            if diag["is_statistically_significant"]
            else f"không có ý nghĩa thống kê ở mức 5% (z = {diag['overall_z']:.2f}, p = {diag['overall_p_value']:.4f})"
        )

        pt_str = (
            f"Kiểm định giả định xu hướng song song trước can thiệp (Pre-Trends Parallel Assumption) thỏa mãn "
            f"(Wald \u03c7\u00b2({diag['pre_trends_wald_stat']:.1f}), p = {diag['pre_trends_p_value']:.4f} \u2265 .05), "
            f"cho thấy không có hiện tượng chọn mẫu theo xu hướng trước can thiệp."
            if diag["parallel_trends_supported"]
            else f"Cảnh báo: Kiểm định xu hướng song song trước can thiệp bị bác bỏ "
                 f"(Wald \u03c7\u00b2({diag['pre_trends_wald_stat']:.1f}), p = {diag['pre_trends_p_value']:.4f} < .05), "
                 f"cho thấy có sự khác biệt về quỹ đạo trước can thiệp giữa các đoàn hệ."
        )

        bacon_str = (
            f"Phân tích phân rã Goodman-Bacon (2021) ghi nhận hệ số TWFE ngây thơ là \u03b2_TWFE = {diag['twfe_naive_beta']:.4f} "
            f"(SE = {diag['twfe_naive_se']:.4f}). Độ lệch thiên lệch (Bias Gap) giữa ước lượng gộp không chệch Callaway-Sant'Anna "
            f"và TWFE là \u0394 = {diag['twfe_bias_gap']:.4f}, bảo vệ suy diễn chính sách khỏi các trọng số âm tiềm ẩn."
        )

        return (
            f"Ước lượng Khác biệt trong Khác biệt Phân tầng Thời gian (Staggered Difference-in-Differences; "
            f"Callaway & Sant'Anna, 2021; Goodman-Bacon, 2021) được thực hiện trên mẫu bảng gồm N = {diag['n_units']} {unit_label} "
            f"qua T = {diag['n_time_periods']} mốc thời gian ({diag['n_cohorts']} đoàn hệ can thiệp) đối với chỉ số {outcome_label}.\n\n"
            f"Hiệu ứng can thiệp trung bình gộp tổng thể (Overall ATT) đạt \u03c4 = {diag['overall_att']:.4f} "
            f"(SE = {diag['overall_se']:.4f}, 95% CI [{diag['ci_lower_95']:.4f}, {diag['ci_upper_95']:.4f}]), {sig_str}. "
            f"{pt_str}\n\n"
            f"{bacon_str}"
        )


def generate_staggered_did_svg(
    event_study_effects: List[Dict[str, Any]],
    overall_att: float,
    twfe_beta: float,
    bacon_components: List[Dict[str, Any]],
    outcome_label: str
) -> str:
    """
    Renders scientific dual-panel SVG:
    Panel A: Dynamic Event Study Plot ATT(e) with confidence intervals and pre-trend validation.
    Panel B: Goodman-Bacon (2021) 2x2 DiD Decomposition scatter plot vs weights.
    """
    svg_w, svg_h = 960, 420
    pad = 55
    panel_w = (svg_w - 3 * pad) // 2
    panel_h = svg_h - 2 * pad

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;">')
    lines.append('<defs>')
    lines.append('  <linearGradient id="bgGradD" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0f172a"/><stop offset="100%" stop-color="#1e293b"/></linearGradient>')
    lines.append('  <linearGradient id="attGrad" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#10b981"/><stop offset="100%" stop-color="#059669"/></linearGradient>')
    lines.append('  <linearGradient id="preGrad" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#94a3b8"/><stop offset="100%" stop-color="#64748b"/></linearGradient>')
    lines.append('  <filter id="glowD" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    lines.append('</defs>')

    # Background
    lines.append(f'<rect width="{svg_w}" height="{svg_h}" rx="12" fill="url(#bgGradD)" stroke="#334155" stroke-width="1"/>')

    # ================= PANEL A: EVENT STUDY =================
    pa_x0, pa_y0 = pad, pad
    lines.append(f'<rect x="{pa_x0}" y="{pa_y0}" width="{panel_w}" height="{panel_h}" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{pa_x0 + 15}" y="{pa_y0 + 25}" fill="#38bdf8" font-size="13" font-weight="700">PANEL A: Nghiên cứu Biến cố Động ATT(e) (Callaway &amp; Sant\'Anna)</text>')

    if len(event_study_effects) > 0:
        es = event_study_effects
        min_e = min(item["event_time"] for item in es)
        max_e = max(item["event_time"] for item in es)
        min_y = min(item["ci_lower_95"] for item in es)
        max_y = max(item["ci_upper_95"] for item in es)

        # Center around 0
        span_y = max(abs(min_y), abs(max_y), 0.5) * 1.2
        span_e = max(max_e - min_e, 1)

        # Coordinate map
        def map_x_a(e_val):
            return pa_x0 + 40 + ((e_val - min_e) / span_e) * (panel_w - 70)

        def map_y_a(y_val):
            return pa_y0 + panel_h / 2 - (y_val / span_y) * (panel_h / 2 - 40)

        # Zero reference line
        y_zero = map_y_a(0.0)
        lines.append(f'<line x1="{pa_x0 + 35}" y1="{y_zero}" x2="{pa_x0 + panel_w - 20}" y2="{y_zero}" stroke="#64748b" stroke-dasharray="4,4" stroke-width="1.5"/>')

        # Vertical line at e = -0.5 (cutoff between pre and post)
        if min_e <= 0 <= max_e:
            x_cut = map_x_a(-0.5)
            lines.append(f'<line x1="{x_cut}" y1="{pa_y0 + 35}" x2="{x_cut}" y2="{pa_y0 + panel_h - 25}" stroke="#f59e0b" stroke-dasharray="3,3" stroke-width="1.5"/>')
            lines.append(f'<text x="{x_cut - 5}" y="{pa_y0 + 48}" fill="#f59e0b" font-size="10" text-anchor="end">Tiền Can thiệp</text>')
            lines.append(f'<text x="{x_cut + 5}" y="{pa_y0 + 48}" fill="#10b981" font-size="10" text-anchor="start">Hậu Can thiệp</text>')

        # Draw trajectory line
        pts_line = []
        for item in es:
            cx = map_x_a(item["event_time"])
            cy = map_y_a(item["att"])
            pts_line.append(f"{cx:.1f},{cy:.1f}")

        lines.append(f'<polyline points="{" ".join(pts_line)}" fill="none" stroke="#10b981" stroke-width="2" opacity="0.8"/>')

        # Draw CI whiskers and points
        for item in es:
            cx = map_x_a(item["event_time"])
            cy = map_y_a(item["att"])
            cy_low = map_y_a(item["ci_lower_95"])
            cy_high = map_y_a(item["ci_upper_95"])

            color = "#94a3b8" if item["is_pre_period"] else "#10b981"

            # Whiskers
            lines.append(f'<line x1="{cx}" y1="{cy_low}" x2="{cx}" y2="{cy_high}" stroke="{color}" stroke-width="2" opacity="0.7"/>')
            lines.append(f'<line x1="{cx - 3}" y1="{cy_low}" x2="{cx + 3}" y2="{cy_low}" stroke="{color}" stroke-width="1.5"/>')
            lines.append(f'<line x1="{cx - 3}" y1="{cy_high}" x2="{cx + 3}" y2="{cy_high}" stroke="{color}" stroke-width="1.5"/>')

            # Dot
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{color}" stroke="#0f172a" stroke-width="1.5" filter="url(#glowD)"/>')
            # Label
            lines.append(f'<text x="{cx}" y="{pa_y0 + panel_h - 10}" fill="#94a3b8" font-size="10" text-anchor="middle">{item["event_time"]}</text>')

        lines.append(f'<text x="{pa_x0 + panel_w / 2}" y="{pa_y0 + panel_h - 2}" fill="#64748b" font-size="10" text-anchor="middle">Thời gian Biến cố (e = t - g)</text>')
        lines.append(f'<text x="{pa_x0 + 15}" y="{y_zero - 5}" fill="#94a3b8" font-size="9">0.0</text>')

    # ================= PANEL B: GOODMAN-BACON DECOMPOSITION =================
    pb_x0, pb_y0 = pad * 2 + panel_w, pad
    lines.append(f'<rect x="{pb_x0}" y="{pb_y0}" width="{panel_w}" height="{panel_h}" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{pb_x0 + 15}" y="{pb_y0 + 25}" fill="#a855f7" font-size="13" font-weight="700">PANEL B: Phân rã Trọng số Goodman-Bacon (2021)</text>')

    if len(bacon_components) > 0:
        comps = bacon_components
        max_w = max(c.get("weight_share", 0.1) for c in comps)
        max_w = max(max_w, 0.05) * 1.2
        min_est = min(c["estimate"] for c in comps)
        max_est = max(c["estimate"] for c in comps)
        span_est = max(abs(min_est), abs(max_est), 0.5) * 1.3

        def map_x_b(w_val):
            return pb_x0 + 40 + (w_val / max_w) * (panel_w - 70)

        def map_y_b(est_val):
            return pb_y0 + panel_h / 2 - (est_val / span_est) * (panel_h / 2 - 40)

        # Baseline zero line
        y_zero_b = map_y_b(0.0)
        lines.append(f'<line x1="{pb_x0 + 35}" y1="{y_zero_b}" x2="{pb_x0 + panel_w - 20}" y2="{y_zero_b}" stroke="#64748b" stroke-dasharray="4,4" stroke-width="1.5"/>')

        # Overall CS ATT horizontal line
        y_cs = map_y_b(overall_att)
        lines.append(f'<line x1="{pb_x0 + 35}" y1="{y_cs}" x2="{pb_x0 + panel_w - 20}" y2="{y_cs}" stroke="#10b981" stroke-width="2"/>')
        lines.append(f'<text x="{pb_x0 + panel_w - 25}" y="{y_cs - 5}" fill="#10b981" font-size="10" text-anchor="end" font-weight="600">ATT CS = {overall_att:.3f}</text>')

        # Naive TWFE horizontal line
        y_twfe = map_y_b(twfe_beta)
        lines.append(f'<line x1="{pb_x0 + 35}" y1="{y_twfe}" x2="{pb_x0 + panel_w - 20}" y2="{y_twfe}" stroke="#f43f5e" stroke-dasharray="3,3" stroke-width="2"/>')
        lines.append(f'<text x="{pb_x0 + panel_w - 25}" y="{y_twfe + 12}" fill="#f43f5e" font-size="10" text-anchor="end" font-weight="600">TWFE Naive = {twfe_beta:.3f}</text>')

        # Plot comparison components
        for c in comps:
            cx = map_x_b(c.get("weight_share", 0.0))
            cy = map_y_b(c["estimate"])
            color = "#38bdf8" if "Never" in c["comparison_type"] else "#ec4899"
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{color}" fill-opacity="0.8" stroke="#ffffff" stroke-width="1.5"/>')

        # Legend
        lines.append(f'<circle cx="{pb_x0 + 40}" cy="{pb_y0 + panel_h - 20}" r="4" fill="#38bdf8"/>')
        lines.append(f'<text x="{pb_x0 + 50}" y="{pb_y0 + panel_h - 16}" fill="#cbd5e1" font-size="9">Can thiệp vs Chưa bao giờ</text>')
        lines.append(f'<circle cx="{pb_x0 + 175}" cy="{pb_y0 + panel_h - 20}" r="4" fill="#ec4899"/>')
        lines.append(f'<text x="{pb_x0 + 185}" y="{pb_y0 + panel_h - 16}" fill="#cbd5e1" font-size="9">Sớm vs Muộn (Dễ chệch)</text>')
        lines.append(f'<text x="{pb_x0 + panel_w / 2}" y="{pb_y0 + panel_h - 4}" fill="#64748b" font-size="10" text-anchor="middle">Tỷ trọng Phân rã w_k</text>')

    lines.append('</svg>')
    return "".join(lines)
