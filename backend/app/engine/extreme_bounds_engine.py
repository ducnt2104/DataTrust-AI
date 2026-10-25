"""
Extreme Bound Analysis (EBA) Engine for Robust Model Specification.
References:
- Leamer, E. E. (1983). Let's take the con out of econometrics. American Economic Review, 73(1), 31-43.
- Sala-i-Martin, X. X. (1997). I just ran four million regressions. American Economic Review, 87(2), 178-183.
- Christensen, G., & Miguel, E. (2018). Transparency, reproducibility, and the credibility of economics research.
  Journal of Economic Literature, 56(3), 920-980.
"""

from itertools import combinations
import math
from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats
from scipy.special import ndtr


class ExtremeBoundsEngine:
    """
    Performs combinatorial regression model scanning to evaluate the sensitivity
    and robustness of a key explanatory variable against specification searches.
    """

    @classmethod
    def analyze(
        cls,
        data: List[Dict[str, Any]],
        focus_var: str,
        outcome_var: str,
        candidate_vars: List[str],
        free_vars: Optional[List[str]] = None,
        max_controls_per_model: int = 4,
        max_total_models: int = 512,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Runs EBA across combinations of candidate control variables.
        """
        free_vars = free_vars or []
        all_required = [outcome_var, focus_var] + free_vars + candidate_vars

        # Filter complete numeric rows
        cleaned_rows = []
        for row in data:
            try:
                vals = [float(row[v]) for v in all_required]
                if not any(math.isnan(x) or math.isinf(x) for x in vals):
                    cleaned_rows.append(vals)
            except (ValueError, TypeError, KeyError):
                continue

        if len(cleaned_rows) < 15:
            return {
                "status": "error",
                "message": f"Dữ liệu không đủ quan sát hợp lệ (cần tối thiểu 15 mẫu, thực tế có {len(cleaned_rows)}).",
            }

        mat = np.array(cleaned_rows, dtype=float)
        y = mat[:, 0]
        p = mat[:, 1]
        free_start = 2
        free_end = 2 + len(free_vars)
        cand_start = free_end

        x_free = mat[:, free_start:free_end] if len(free_vars) > 0 else np.empty((len(cleaned_rows), 0))
        x_cand = mat[:, cand_start:]

        n_samples = len(y)
        k_cand = len(candidate_vars)

        # Generate candidate variable subsets
        model_subsets: List[List[int]] = []
        max_k = min(k_cand, max_controls_per_model)
        for r in range(max_k + 1):
            for combo in combinations(range(k_cand), r):
                model_subsets.append(list(combo))
                if len(model_subsets) >= max_total_models:
                    break
            if len(model_subsets) >= max_total_models:
                break

        crit_z = float(stats.norm.ppf(1.0 - (1.0 - confidence_level) / 2.0))

        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        if ss_tot <= 1e-12:
            return {
                "status": "error",
                "message": "Biến phụ thuộc Y không có phương sai (hằng số).",
            }

        specifications: List[Dict[str, Any]] = []

        for idx, subset in enumerate(model_subsets):
            # Design matrix: [Intercept, Focus, Free, Subset_of_Cand]
            cols = [np.ones((n_samples, 1)), p.reshape(-1, 1)]
            if x_free.shape[1] > 0:
                cols.append(x_free)
            if len(subset) > 0:
                cols.append(x_cand[:, subset])

            X = np.hstack(cols)
            df = n_samples - X.shape[1]
            if df <= 2:
                continue

            try:
                # OLS via pseudo-inverse or solve
                beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
                e = y - X @ beta
                ss_res = float(np.sum(e ** 2))
                sigma_sq = ss_res / max(df, 1)

                XtX_inv = np.linalg.pinv(X.T @ X)
                cov_beta = sigma_sq * XtX_inv

                b_p = float(beta[1])
                se_p = float(np.sqrt(max(cov_beta[1, 1], 1e-12)))

                t_stat = b_p / se_p
                p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(t_stat))))
                r2 = max(0.0, min(1.0, 1.0 - (ss_res / ss_tot)))

                ci_low = b_p - crit_z * se_p
                ci_high = b_p + crit_z * se_p

                # Normal CDF at 0 for Sala-i-Martin
                cdf_at_zero = float(ndtr(b_p / se_p))

                subset_names = [candidate_vars[i] for i in subset]

                specifications.append({
                    "model_id": idx + 1,
                    "beta": b_p,
                    "se": se_p,
                    "t_stat": t_stat,
                    "p_value": p_val,
                    "r_squared": r2,
                    "ci_lower": ci_low,
                    "ci_upper": ci_high,
                    "is_significant": p_val < 0.05,
                    "controls": subset_names,
                    "cdf_zero": cdf_at_zero,
                })
            except Exception:
                continue

        if not specifications:
            return {
                "status": "error",
                "message": "Không thể ước lượng các mô hình hồi quy do ma trận suy biến.",
            }

        # Sort specifications by beta ascending for specification curve
        specifications.sort(key=lambda s: s["beta"])

        betas = np.array([s["beta"] for s in specifications])
        ses = np.array([s["se"] for s in specifications])
        ci_lows = np.array([s["ci_lower"] for s in specifications])
        ci_highs = np.array([s["ci_upper"] for s in specifications])
        p_vals = np.array([s["p_value"] for s in specifications])
        r2s = np.array([s["r_squared"] for s in specifications])
        cdf_zeros = np.array([s["cdf_zero"] for s in specifications])

        m_count = len(specifications)

        # 1. Leamer's Extreme Bounds
        leamer_extreme_lower = float(np.min(ci_lows))
        leamer_extreme_upper = float(np.max(ci_highs))
        min_beta_spec = specifications[int(np.argmin(betas))]
        max_beta_spec = specifications[int(np.argmax(betas))]

        if leamer_extreme_lower > 0:
            leamer_verdict = "ROBUST_POSITIVE"
            leamer_label = "Vững chắc Dương (Robust Positive - Không đổi dấu trên toàn dải cực trị)"
        elif leamer_extreme_upper < 0:
            leamer_verdict = "ROBUST_NEGATIVE"
            leamer_label = "Vững chắc Âm (Robust Negative - Không đổi dấu trên toàn dải cực trị)"
        else:
            leamer_verdict = "FRAGILE"
            leamer_label = "Dễ vỡ / Nhạy cảm (Fragile - Khoảng cực trị bao trùm điểm 0)"

        # 2. Sala-i-Martin's Weighted & Unweighted CDF(0)
        mean_cdf = float(np.mean(cdf_zeros))
        sala_cdf = max(mean_cdf, 1.0 - mean_cdf)

        # Weighted by R2
        r2_sum = float(np.sum(r2s))
        if r2_sum > 1e-12:
            weighted_cdf_raw = float(np.sum(r2s * cdf_zeros) / r2_sum)
            sala_weighted_cdf = max(weighted_cdf_raw, 1.0 - weighted_cdf_raw)
        else:
            sala_weighted_cdf = sala_cdf

        if sala_cdf >= 0.95:
            sala_verdict = "ROBUST"
            sala_label = f"Vững chắc (Robust - Tích lũy CDF(0) = {sala_cdf:.1%} >= 95%)"
        else:
            sala_verdict = "FRAGILE"
            sala_label = f"Dễ vỡ (Fragile - Tích lũy CDF(0) = {sala_cdf:.1%} < 95%)"

        sig_pos_count = int(np.sum((p_vals < 0.05) & (betas > 0)))
        sig_neg_count = int(np.sum((p_vals < 0.05) & (betas < 0)))
        non_sig_count = int(np.sum(p_vals >= 0.05))
        sig_fraction = float(np.mean(p_vals < 0.05))
        pos_fraction = float(np.mean(betas > 0))

        summary = {
            "n_samples": n_samples,
            "total_models_evaluated": m_count,
            "candidate_controls_pool_size": k_cand,
            "mean_beta": float(np.mean(betas)),
            "median_beta": float(np.median(betas)),
            "std_beta": float(np.std(betas)),
            "min_beta": float(np.min(betas)),
            "max_beta": float(np.max(betas)),
            "leamer_lower_bound": leamer_extreme_lower,
            "leamer_upper_bound": leamer_extreme_upper,
            "leamer_verdict": leamer_verdict,
            "leamer_label": leamer_label,
            "sala_i_martin_cdf": sala_cdf,
            "sala_i_martin_weighted_cdf": sala_weighted_cdf,
            "sala_i_martin_verdict": sala_verdict,
            "sala_i_martin_label": sala_label,
            "significant_models_fraction": sig_fraction,
            "positive_models_fraction": pos_fraction,
            "sig_positive_models": sig_pos_count,
            "sig_negative_models": sig_neg_count,
            "non_significant_models": non_sig_count,
            "min_beta_model_controls": min_beta_spec["controls"],
            "max_beta_model_controls": max_beta_spec["controls"],
        }

        # Generate Dual-Panel SVG Chart
        svg_chart = cls._generate_svg_chart(
            specifications=specifications,
            summary=summary,
            focus_var=focus_var,
            outcome_var=outcome_var,
        )

        # Generate APA 7th narrative
        apa_narrative = cls._generate_apa_narrative(
            summary=summary,
            focus_var=focus_var,
            outcome_var=outcome_var,
            free_vars=free_vars,
        )

        # Truncate specifications to top and bottom sample for API payload compactness
        payload_specs = specifications[:15] + specifications[-15:] if len(specifications) > 30 else specifications

        return {
            "status": "success",
            "summary": summary,
            "specifications_sample": payload_specs,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        specifications: List[Dict[str, Any]],
        summary: Dict[str, Any],
        focus_var: str,
        outcome_var: str,
    ) -> str:
        """
        Creates a dual-panel vector SVG:
        Panel A: Specification Curve (ordered beta estimates with confidence intervals)
        Panel B: Histogram / Density distribution with Leamer bounds and Sala-i-Martin CDF gauge.
        """
        w, h = 860, 480
        pad_l, pad_r, pad_t, pad_b = 60, 40, 50, 40
        panel_gap = 40
        pw = w - pad_l - pad_r
        ph = (h - pad_t - pad_b - panel_gap) // 2

        # Panel A Bounds
        all_lows = [s["ci_lower"] for s in specifications]
        all_highs = [s["ci_upper"] for s in specifications]
        min_val = min(min(all_lows), 0.0)
        max_val = max(max(all_highs), 0.0)
        val_range = max(max_val - min_val, 1e-4)

        def scale_y_a(val: float) -> float:
            norm = (val - min_val) / val_range
            return (pad_t + ph) - norm * ph

        m_total = len(specifications)

        def scale_x_a(idx: int) -> float:
            if m_total <= 1:
                return pad_l + pw / 2
            return pad_l + (idx / (m_total - 1)) * pw

        # Points and bars for Panel A
        panel_a_elements = []
        zero_y_a = scale_y_a(0.0)
        panel_a_elements.append(
            f'<line x1="{pad_l}" y1="{zero_y_a:.1f}" x2="{pad_l + pw}" y2="{zero_y_a:.1f}" stroke="#94a3b8" stroke-dasharray="4,4" stroke-width="1.5" />'
        )

        for i, spec in enumerate(specifications):
            cx = scale_x_a(i)
            y_b = scale_y_a(spec["beta"])
            y_low = scale_y_a(spec["ci_lower"])
            y_high = scale_y_a(spec["ci_upper"])

            if spec["is_significant"]:
                color = "#10b981" if spec["beta"] > 0 else "#ef4444"
            else:
                color = "#94a3b8"

            panel_a_elements.append(
                f'<line x1="{cx:.1f}" y1="{y_high:.1f}" x2="{cx:.1f}" y2="{y_low:.1f}" stroke="{color}" stroke-opacity="0.35" stroke-width="1.2" />'
            )
            panel_a_elements.append(
                f'<circle cx="{cx:.1f}" cy="{y_b:.1f}" r="2" fill="{color}" />'
            )

        # Panel B: Histogram of Betas & Sala-i-Martin Gauge
        top_b = pad_t + ph + panel_gap
        betas = [s["beta"] for s in specifications]
        b_min = min(betas)
        b_max = max(betas)
        b_range = max(b_max - b_min, 1e-4)

        n_bins = min(25, max(8, m_total // 4))
        counts, bin_edges = np.histogram(betas, bins=n_bins)
        max_count = max(counts) if len(counts) > 0 and max(counts) > 0 else 1

        panel_b_elements = []

        def scale_x_b(val: float) -> float:
            norm = (val - b_min) / b_range
            return pad_l + norm * (pw * 0.65)

        bin_w = (pw * 0.65) / n_bins
        for i, count in enumerate(counts):
            bx = pad_l + i * bin_w
            bar_h = (count / max_count) * (ph - 30)
            by = (top_b + ph) - bar_h
            panel_b_elements.append(
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bin_w - 2:.1f}" height="{bar_h:.1f}" fill="#3b82f6" fill-opacity="0.7" rx="2" />'
            )

        # Leamer Extreme Bounds Markers
        leamer_low_x = scale_x_b(summary["leamer_lower_bound"]) if b_min <= summary["leamer_lower_bound"] <= b_max else pad_l
        leamer_high_x = scale_x_b(summary["leamer_upper_bound"]) if b_min <= summary["leamer_upper_bound"] <= b_max else pad_l + pw * 0.65

        panel_b_elements.append(
            f'<line x1="{leamer_low_x:.1f}" y1="{top_b}" x2="{leamer_low_x:.1f}" y2="{top_b + ph}" stroke="#ef4444" stroke-width="2" stroke-dasharray="3,3" />'
        )
        panel_b_elements.append(
            f'<line x1="{leamer_high_x:.1f}" y1="{top_b}" x2="{leamer_high_x:.1f}" y2="{top_b + ph}" stroke="#ef4444" stroke-width="2" stroke-dasharray="3,3" />'
        )

        # Sala-i-Martin Gauge Widget (Right side of Panel B)
        gauge_x = pad_l + pw * 0.72
        gauge_y = top_b + 10
        gauge_w = pw * 0.28
        gauge_h = ph - 15

        gauge_color = "#10b981" if summary["sala_i_martin_verdict"] == "ROBUST" else "#f59e0b"
        cdf_pct = summary["sala_i_martin_cdf"] * 100.0

        panel_b_elements.append(
            f'<rect x="{gauge_x:.1f}" y="{gauge_y:.1f}" width="{gauge_w:.1f}" height="{gauge_h:.1f}" fill="#1e293b" rx="8" stroke="#334155" stroke-width="1" />'
        )
        panel_b_elements.append(
            f'<text x="{gauge_x + gauge_w/2:.1f}" y="{gauge_y + 24:.1f}" font-size="11" font-weight="600" fill="#94a3b8" text-anchor="middle">SALA-I-MARTIN CDF(0)</text>'
        )
        panel_b_elements.append(
            f'<text x="{gauge_x + gauge_w/2:.1f}" y="{gauge_y + 58:.1f}" font-size="24" font-weight="700" fill="{gauge_color}" text-anchor="middle">{cdf_pct:.1f}%</text>'
        )
        panel_b_elements.append(
            f'<text x="{gauge_x + gauge_w/2:.1f}" y="{gauge_y + 80:.1f}" font-size="11" font-weight="600" fill="{gauge_color}" text-anchor="middle">{summary["sala_i_martin_verdict"]}</text>'
        )
        panel_b_elements.append(
            f'<text x="{gauge_x + gauge_w/2:.1f}" y="{gauge_y + 100:.1f}" font-size="10" fill="#cbd5e1" text-anchor="middle">Leamer: {summary["leamer_verdict"]}</text>'
        )

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="background:#0f172a; border-radius:12px; font-family:system-ui, -apple-system, sans-serif;">
  <!-- Title -->
  <text x="{pad_l}" y="28" font-size="15" font-weight="700" fill="#f8fafc">EXTREME BOUND ANALYSIS (EBA) SPECIFICATION CURVE</text>
  <text x="{pad_l}" y="44" font-size="11" fill="#94a3b8">Biến trọng tâm: {focus_var} → {outcome_var} | {summary["total_models_evaluated"]} mô hình hồi quy OLS</text>

  <!-- Panel A Header -->
  <text x="{pad_l + pw}" y="28" font-size="11" font-weight="600" fill="#38bdf8" text-anchor="end">Panel A: Specification Curve &amp; 95% CI</text>

  <!-- Panel A Content -->
  {''.join(panel_a_elements)}

  <!-- Panel B Header -->
  <text x="{pad_l}" y="{top_b - 12}" font-size="12" font-weight="700" fill="#f8fafc">Panel B: Hệ số Phân phối Beta &amp; Thước đo Độ vững chắc (Robustness Tests)</text>

  <!-- Panel B Content -->
  {''.join(panel_b_elements)}

  <!-- Legend -->
  <circle cx="{pad_l + pw - 240}" cy="44" r="4" fill="#10b981" />
  <text x="{pad_l + pw - 232}" y="47" font-size="10" fill="#cbd5e1">Ý nghĩa Dương (p&lt;.05)</text>
  <circle cx="{pad_l + pw - 120}" cy="44" r="4" fill="#94a3b8" />
  <text x="{pad_l + pw - 112}" y="47" font-size="10" fill="#cbd5e1">Không có ý nghĩa</text>
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        summary: Dict[str, Any],
        focus_var: str,
        outcome_var: str,
        free_vars: List[str],
    ) -> str:
        """
        Generates an APA 7th publication-grade econometric robustness writeup.
        """
        free_str = f" với các biến kiểm soát nền tảng bắt buộc ({', '.join(free_vars)})" if free_vars else ""
        return (
            f"Phân tích Cực trị (Extreme Bound Analysis - EBA; Leamer, 1983; Sala-i-Martin, 1997) được thực hiện "
            f"trên tổng số N = {summary['n_samples']} quan sát khảo sát nhằm kiểm định độ nhạy và tính vững chắc "
            f"của mối quan hệ giữa biến trọng tâm {focus_var} và biến kết quả {outcome_var}{free_str} qua toàn bộ "
            f"M = {summary['total_models_evaluated']} tổ hợp đặc tả mô hình hồi quy khả dĩ sinh ra từ không gian K = "
            f"{summary['candidate_controls_pool_size']} biến kiểm soát ứng viên. Hệ số ước lượng trung bình của {focus_var} "
            f"đạt β_mean = {summary['mean_beta']:.4f} (SD = {summary['std_beta']:.4f}, Median = {summary['median_beta']:.4f}, "
            f"dao động từ β_min = {summary['min_beta']:.4f} đến β_max = {summary['max_beta']:.4f}). "
            f"Theo tiêu chuẩn khắt khe của Leamer (1983), khoảng cực trị hai đầu đạt [{summary['leamer_lower_bound']:.4f}, "
            f"{summary['leamer_upper_bound']:.4f}], dẫn đến kết luận đặc tả: {summary['leamer_label']}. "
            f"Đồng thời, theo tiêu chuẩn phân phối tích lũy của Sala-i-Martin (1997), xác suất khối lượng phân phối tích lũy "
            f"nằm về một phía của điểm 0 đạt CDF(0) = {summary['sala_i_martin_cdf']:.1%} (trọng số R²: {summary['sala_i_martin_weighted_cdf']:.1%}), "
            f"phân loại độ vững chắc: {summary['sala_i_martin_label']}. Tổng cộng có {summary['significant_models_fraction']:.1%} "
            f"số mô hình đạt mức ý nghĩa thống kê (p < .05), trong đó có {summary['sig_positive_models']} mô hình dương có ý nghĩa "
            f"và {summary['non_significant_models']} mô hình không đạt ý nghĩa, cung cấp bằng chứng thực nghiệm minh bạch "
            f"chống lại hiện tượng thao túng khai thác dữ liệu (p-hacking / specification searching)."
        )
