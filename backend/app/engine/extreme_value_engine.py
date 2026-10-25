"""
Extreme Value Theory (EVT) & Survey Tail Risk / Outlier Modeling Engine
========================================================================
Methodological references:
- Pickands, J. (1975). Statistical inference using extreme order statistics.
  The Annals of Statistics, 3(1), 119-131.
- Balkema, A. A., & de Haan, L. (1974). Residual life time at great age.
  The Annals of Probability, 2(5), 792-804.
- Davison, A. C., & Smith, R. L. (1990). Models for exceedances over high thresholds.
  Journal of the Royal Statistical Society: Series B (Methodological), 52(3), 393-442.
- McNeil, A. J., & Frey, R. (2000). Estimation of tail-related risk measures for
  heteroscedastic financial time series: an extreme value approach.
  Journal of Empirical Finance, 7(3-4), 271-300.
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np
from scipy.stats import genpareto, ks_1samp


class ExtremeValueEngine:
    """
    Peaks-Over-Threshold (POT) Generalized Pareto Distribution (GPD)
    Extreme Value Theory modeling engine for survey metrics and tail risks.
    """

    @classmethod
    def estimate(
        cls,
        data: List[float],
        threshold_percentile: float = 0.90,
        custom_threshold: Optional[float] = None,
        alpha_levels: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Estimate GPD parameters, Value-at-Risk (VaR), and Expected Shortfall (ES).
        """
        arr = np.array([float(x) for x in data if x is not None and not np.isnan(float(x))], dtype=float)
        n_total = len(arr)

        if n_total < 30:
            return {
                "status": "error",
                "message": f"Cỡ mẫu quá nhỏ ({n_total} quan sát). Cần tối thiểu 30 quan sát để phân tích EVT."
            }

        if alpha_levels is None:
            alpha_levels = [0.95, 0.99, 0.995]

        # Determine threshold u
        if custom_threshold is not None:
            u = float(custom_threshold)
            exceedance_pct = float(np.mean(arr > u))
        else:
            q = max(0.50, min(0.98, float(threshold_percentile)))
            u = float(np.quantile(arr, q))
            exceedance_pct = 1.0 - q

        excesses = arr[arr > u] - u
        n_u = len(excesses)

        if n_u < 10:
            return {
                "status": "error",
                "message": f"Số lượng quan sát vượt ngưỡng quá ít (Nu = {n_u}). Vui lòng hạ thấp ngưỡng phân tích."
            }

        # Fit Generalized Pareto Distribution:
        # scipy genpareto has CDF F(y) = 1 - (1 + c * y / scale)^(-1/c)
        # where c = xi (shape parameter) and scale = sigma
        try:
            c_fit, loc_fit, scale_fit = genpareto.fit(excesses, floc=0)
            xi = float(c_fit)
            sigma = float(scale_fit)
        except Exception as e:
            # Fallback to Method of Moments
            mean_y = float(np.mean(excesses))
            var_y = float(np.var(excesses, ddof=1))
            if var_y > 1e-9:
                xi = float(0.5 * (1.0 - (mean_y ** 2) / var_y))
                sigma = float(mean_y * (1.0 - xi))
            else:
                xi = 0.1
                sigma = max(0.1, mean_y)

        # Ensure positive scale
        sigma = max(1e-6, sigma)

        # Asymptotic Standard Errors (Davison & Smith, 1990)
        # Var(xi) ~ (1 + xi)^2 / Nu, Var(sigma) ~ 2 * sigma^2 * (1 + xi) / Nu
        se_xi = float(abs(1.0 + xi) / math.sqrt(n_u))
        se_sigma = float(sigma * math.sqrt(max(0.01, 2.0 * (1.0 + xi)) / n_u))

        # Tail classification
        if xi > 0.05:
            tail_type = "Fréchet (Heavy-tailed / Pareto-like tail risk)"
            tail_interpretation = "Phân phối đuôi nặng (Fat-tail): Tần suất và độ khốc liệt của các phản hồi cực đoan cao hơn nhiều so với phân phối chuẩn. Tiềm ẩn nguy cơ sụt giảm nghiêm trọng."
        elif xi < -0.05:
            tail_type = "Weibull (Light-tailed / Bounded upper support)"
            tail_interpretation = "Phân phối đuôi nhẹ có chặn trên (Bounded): Các điểm cực đoan có giới hạn vật lý tự nhiên, rủi ro đuôi được kiểm soát."
        else:
            tail_type = "Gumbel (Exponential tail / Moderate risk)"
            tail_interpretation = "Phân phối đuôi hàm mũ (Exponential decay): Rủi ro cực đoan suy giảm tương tự phân phối chuẩn hoặc phân phối hàm mũ."

        # Exceedance probability
        zeta_u = n_u / n_total

        # Value-at-Risk (VaR) & Expected Shortfall (ES)
        risk_measures = []
        for p in alpha_levels:
            p = float(p)
            if p >= 1.0 or p <= 0.0:
                continue

            # VaR formula: u + (sigma / xi) * (( (N / Nu) * (1 - p) )^(-xi) - 1)
            factor = (1.0 - p) / zeta_u
            if factor <= 0:
                continue

            if abs(xi) > 1e-5:
                var_p = u + (sigma / xi) * (math.pow(factor, -xi) - 1.0)
            else:
                var_p = u - sigma * math.log(factor)

            # Expected Shortfall formula: ES_p = (VaR_p + sigma - xi * u) / (1 - xi)
            if xi < 1.0:
                es_p = (var_p + sigma - xi * u) / (1.0 - xi)
            else:
                es_p = None

            risk_measures.append({
                "confidence_level": p,
                "var_p": round(float(var_p), 4),
                "es_p": round(float(es_p), 4) if es_p is not None else None,
                "is_infinite_mean": bool(xi >= 1.0)
            })

        # Kolmogorov-Smirnov Goodness-of-fit
        ks_stat, ks_pval = ks_1samp(excesses, lambda x: genpareto.cdf(x, c=xi, scale=sigma))
        gof_passed = bool(ks_pval > 0.05)

        # Mean Excess Plot data points
        # Grid of 10 thresholds from 50th percentile to 92nd percentile
        quantiles = np.linspace(0.50, 0.92, 10)
        mean_excess_grid = []
        for q in quantiles:
            cand_u = float(np.quantile(arr, q))
            cand_excesses = arr[arr > cand_u] - cand_u
            if len(cand_excesses) >= 5:
                mean_excess_grid.append({
                    "threshold": round(cand_u, 3),
                    "mean_excess": round(float(np.mean(cand_excesses)), 3),
                    "count": int(len(cand_excesses))
                })

        # Generate Dual-Panel SVG visualization
        svg_chart = cls._generate_svg_chart(
            arr=arr,
            u=u,
            xi=xi,
            sigma=sigma,
            mean_excess_grid=mean_excess_grid,
            risk_measures=risk_measures
        )

        # APA 7th Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_total=n_total,
            u=u,
            n_u=n_u,
            zeta_u=zeta_u,
            xi=xi,
            se_xi=se_xi,
            sigma=sigma,
            se_sigma=se_sigma,
            tail_type=tail_type,
            ks_stat=float(ks_stat),
            ks_pval=float(ks_pval),
            risk_measures=risk_measures
        )

        return {
            "status": "success",
            "sample_size": n_total,
            "threshold": round(u, 4),
            "exceedances_count": n_u,
            "exceedance_probability": round(zeta_u, 4),
            "shape_xi": round(xi, 4),
            "se_shape_xi": round(se_xi, 4),
            "scale_sigma": round(sigma, 4),
            "se_scale_sigma": round(se_sigma, 4),
            "tail_classification": tail_type,
            "tail_interpretation": tail_interpretation,
            "gof_ks_statistic": round(float(ks_stat), 4),
            "gof_ks_p_value": round(float(ks_pval), 4),
            "gof_passed": gof_passed,
            "risk_measures": risk_measures,
            "mean_excess_grid": mean_excess_grid,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        arr: np.ndarray,
        u: float,
        xi: float,
        sigma: float,
        mean_excess_grid: List[Dict[str, Any]],
        risk_measures: List[Dict[str, Any]]
    ) -> str:
        """
        Generate dual-panel SVG:
        Panel A: Mean Excess Plot with threshold marker.
        Panel B: Tail Survival Function S(x) with fitted GPD and VaR markers.
        """
        width = 820
        height = 360

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="100%" height="{height}" style="background-color:#0b1120;border-radius:10px;'
            f'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">'
        ]

        # Titles
        svg.append(
            '<text x="20" y="26" fill="#f8fafc" font-size="14" font-weight="bold">'
            'Đồ thị Lý thuyết Giá trị Cực đoan (Extreme Value Theory - GPD Tail Risk)</text>'
        )

        # Panel A: Mean Excess Plot (X: 50 to 390, Y: 60 to 310)
        svg.append('<rect x="50" y="60" width="340" height="250" fill="#020617" rx="6" stroke="#1e293b"/>')
        svg.append('<text x="60" y="80" fill="#38bdf8" font-size="11" font-weight="bold">Panel A: Mean Excess Plot (Mean Residual Life)</text>')

        if len(mean_excess_grid) >= 2:
            u_vals = [pt["threshold"] for pt in mean_excess_grid]
            me_vals = [pt["mean_excess"] for pt in mean_excess_grid]

            min_u, max_u = min(u_vals), max(u_vals)
            min_me, max_me = max(0, min(me_vals) * 0.8), max(me_vals) * 1.2
            if max_u == min_u:
                max_u += 1.0
            if max_me == min_me:
                max_me += 1.0

            def scale_a_x(val):
                return 70 + (val - min_u) / (max_u - min_u) * 300

            def scale_a_y(val):
                return 285 - (val - min_me) / (max_me - min_me) * 190

            # Grid lines
            for i in range(4):
                gy = 95 + i * 60
                svg.append(f'<line x1="70" y1="{gy}" x2="370" y2="{gy}" stroke="#1e293b" stroke-dasharray="3,3"/>')

            # Polyline
            poly_pts = [f'{scale_a_x(pt["threshold"]):.1f},{scale_a_y(pt["mean_excess"]):.1f}' for pt in mean_excess_grid]
            svg.append(f'<polyline points="{" ".join(poly_pts)}" fill="none" stroke="#38bdf8" stroke-width="2.5"/>')

            # Points
            for pt in mean_excess_grid:
                px = scale_a_x(pt["threshold"])
                py = scale_a_y(pt["mean_excess"])
                svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5"/>')

            # Threshold u vertical line if within range
            if min_u <= u <= max_u:
                ux = scale_a_x(u)
                svg.append(f'<line x1="{ux:.1f}" y1="85" x2="{ux:.1f}" y2="285" stroke="#f43f5e" stroke-width="2" stroke-dasharray="4,4"/>')
                svg.append(f'<text x="{ux + 5:.1f}" y="105" fill="#f43f5e" font-size="9" font-weight="bold">u = {u:.2f}</text>')

            svg.append('<text x="220" y="304" fill="#94a3b8" font-size="10" text-anchor="middle">Ngưỡng Threshold (u)</text>')
            svg.append('<text x="65" y="190" fill="#94a3b8" font-size="9" text-anchor="middle" transform="rotate(-90 65 190)">Kỳ vọng Vượt trội e(u)</text>')

        # Panel B: GPD Tail Survival Function S(x) (X: 430 to 790, Y: 60 to 310)
        svg.append('<rect x="430" y="60" width="360" height="250" fill="#020617" rx="6" stroke="#1e293b"/>')
        svg.append('<text x="440" y="80" fill="#10b981" font-size="11" font-weight="bold">Panel B: Tail Survival Function &amp; VaR Estimates</text>')

        # Simulate survival curve for excesses
        max_x = max(np.max(arr) * 1.05, u + sigma * 3.5)
        curve_xs = np.linspace(u, max_x, 50)
        curve_pts = []

        def scale_b_x(val):
            return 450 + (val - u) / (max_x - u) * 320

        def scale_b_y(surv):
            # Log survival scale from 0.001 to 1.0
            surv_safe = max(1e-4, min(1.0, surv))
            return 95 + (-math.log10(surv_safe)) / 4.0 * 185

        for x_val in curve_xs:
            y_excess = x_val - u
            if abs(xi) > 1e-5:
                arg = 1.0 + xi * y_excess / sigma
                surv = math.pow(max(1e-6, arg), -1.0 / xi) if arg > 0 else 0.0
            else:
                surv = math.exp(-y_excess / sigma)
            curve_pts.append(f'{scale_b_x(x_val):.1f},{scale_b_y(surv):.1f}')

        if curve_pts:
            svg.append(f'<polyline points="{" ".join(curve_pts)}" fill="none" stroke="#10b981" stroke-width="2.5"/>')

        # Add VaR markers
        colors = ["#f59e0b", "#ec4899", "#8b5cf6"]
        for idx, rm in enumerate(risk_measures):
            conf = rm["confidence_level"]
            var_val = rm["var_p"]
            if u <= var_val <= max_x:
                vx = scale_b_x(var_val)
                col = colors[idx % len(colors)]
                svg.append(f'<line x1="{vx:.1f}" y1="85" x2="{vx:.1f}" y2="285" stroke="{col}" stroke-width="1.5" stroke-dasharray="3,3"/>')
                svg.append(f'<text x="{vx - 2:.1f}" y="{120 + idx * 25}" fill="{col}" font-size="9" font-weight="bold" text-anchor="end">VaR({int(conf*100)}%) = {var_val:.2f}</text>')

        svg.append('<text x="610" y="304" fill="#94a3b8" font-size="10" text-anchor="middle">Giá trị Quan sát (x)</text>')
        svg.append('<text x="445" y="190" fill="#94a3b8" font-size="9" text-anchor="middle" transform="rotate(-90 445 190)">Xác suất Sống sót S(x)</text>')

        # Footer Legend
        svg.append(
            '<text x="410" y="340" fill="#64748b" font-size="10" text-anchor="middle">'
            f'GPD Fit: Shape ξ = {xi:.3f}, Scale σ = {sigma:.3f} | Threshold u = {u:.2f}</text>'
        )

        svg.append('</svg>')
        return "".join(svg)

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_total: int,
        u: float,
        n_u: int,
        zeta_u: float,
        xi: float,
        se_xi: float,
        sigma: float,
        se_sigma: float,
        tail_type: str,
        ks_stat: float,
        ks_pval: float,
        risk_measures: List[Dict[str, Any]]
    ) -> str:
        """
        Generate APA 7th Edition formatted statistical narrative.
        """
        lines = [
            f"Phân tích Lý thuyết Giá trị Cực đoan (Extreme Value Theory - EVT) sử dụng mô hình "
            f"Peaks-Over-Threshold (POT) theo định lý Pickands-Balkema-de Haan (Pickands, 1975; Balkema & de Haan, 1974) "
            f"đã được thực hiện trên mẫu dữ liệu gồm N = {n_total:,} quan sát. "
            f"Ngưỡng phân định cực đoan được thiết lập tại u = {u:.3f}, ghi nhận Nu = {n_u} quan sát vượt ngưỡng "
            f"(xác suất vượt ngưỡng thực nghiệm ζu = {zeta_u:.4f}, tương đương {zeta_u * 100:.1f}% tổng thể mẫu)."
        ]

        lines.append(
            f"Phân phối Pareto Tổng quát (Generalized Pareto Distribution - GPD) ước lượng qua phương pháp Hợp lý Cực đại (MLE) "
            f"cho ra tham số hình dạng (Shape parameter / Tail Index) ξ = {xi:.4f} (SE = {se_xi:.4f}) và tham số tỷ lệ (Scale parameter) "
            f"σ = {sigma:.4f} (SE = {se_sigma:.4f}). "
            f"Mô hình được phân loại thuộc họ {tail_type}."
        )

        # GOF
        if ks_pval > 0.05:
            lines.append(
                f"Kiểm định độ phù hợp Kolmogorov-Smirnov cho thấy mô hình GPD hoàn toàn phù hợp với phân phối thực nghiệm "
                f"của các phần dư vượt ngưỡng (D = {ks_stat:.4f}, p = {ks_pval:.4f} > .05)."
            )
        else:
            lines.append(
                f"Kiểm định Kolmogorov-Smirnov ghi nhận D = {ks_stat:.4f}, p = {ks_pval:.4f}."
            )

        # Risk metrics
        var_texts = []
        for rm in risk_measures:
            c = int(rm["confidence_level"] * 100)
            v = rm["var_p"]
            e = rm["es_p"]
            if e is not None:
                var_texts.append(f"VaR({c}%) = {v:.3f} và Kỳ vọng Tổn thất Đuôi ES({c}%) = {e:.3f}")
            else:
                var_texts.append(f"VaR({c}%) = {v:.3f} (ES vô hạn do ξ ≥ 1.0)")

        if var_texts:
            lines.append(
                f"Về phương diện quản trị rủi ro đuôi (Tail Risk Management; McNeil & Frey, 2000), các chỉ số rủi ro định lượng xác định: "
                f"{'; '.join(var_texts)}. "
                f"Điều này phản ánh mức độ nghiêm trọng tiềm ẩn của các phản hồi bất thường hoặc độ trễ phản hồi cực đại, "
                f"cung cấp cơ sở định lượng chuẩn mực cho việc thiết lập chính sách kiểm soát ngưỡng và kế hoạch phòng ngừa rủi ro vận hành."
            )

        return " ".join(lines)
