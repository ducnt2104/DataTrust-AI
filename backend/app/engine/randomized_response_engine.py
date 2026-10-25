"""
Randomized Response Technique (RRT) & Crosswise Sensitive Item Prevalence Engine
================================================================================
Mathematical & Statistical References:
- Warner, S. L. (1965). Randomized response: A survey technique for eliminating
  evasive answer bias. Journal of the American Statistical Association, 60(309), 63-69.
- Horvitz, D. G., Shah, B. V., & Simmons, W. R. (1967). The unrelated question
  randomized response model. Proceedings of the Social Statistics Section, 65-72.
- Yu, J. W., Tian, G. L., & Tang, M. L. (2008). Two new models for survey sampling
  with sensitive characteristics: Design and analysis. Annals of the Institute of
  Statistical Mathematics, 60(4), 721-736.
- Jann, B., Jerke, J., & Krumpal, I. (2012). Asking sensitive questions using the
  crosswise model: An experimental survey measuring plagiarism. Sociological
  Methods & Research, 41(1), 32-49.
- van den Hout, A., & van der Heijden, P. G. (2002). Randomized response,
  statistical disclosure control and misclassification: A review. International
  Statistical Review, 70(2), 269-288.

DataTrust Iteration 193.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import scipy.stats as stats
import scipy.optimize as opt


class RandomizedResponseEngine:
    """
    Engine for de-biasing sensitive survey questions, estimating true latent
    prevalence under evasive answer bias, and evaluating social desirability bias.
    """

    @classmethod
    def evaluate(
        cls,
        rrt_responses: np.ndarray,      # Binary 0/1 observed randomized answers
        model_type: str = "crosswise",  # "warner", "crosswise", or "unrelated"
        p_randomizer: float = 0.70,     # Probability p of answering sensitive item
        p_unrelated: float = 0.50,      # Known prevalence of unrelated item (for unrelated model)
        direct_responses: Optional[np.ndarray] = None,  # Optional benchmark direct question (0/1)
        covariates: Optional[np.ndarray] = None,        # Optional (N, P) matrix for RRT logit regression
        covariate_names: Optional[List[str]] = None,
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Estimates true latent sensitive trait prevalence pi and standard errors.
        """
        N = len(rrt_responses)
        if N < 20:
            raise ValueError(f"Cỡ mẫu quá nhỏ để ước lượng Randomized Response (N={N} < 20).")

        rrt_arr = rrt_responses.astype(int)
        if not np.all(np.isin(rrt_arr, [0, 1])):
            raise ValueError("Câu trả lời RRT phải là biến nhị phân 0 hoặc 1.")

        if abs(p_randomizer - 0.50) < 0.01:
            raise ValueError("Xác suất ngẫu nhiên hóa p không được bằng 0.50 (khiến mẫu số triệt tiêu).")
        if p_randomizer <= 0.0 or p_randomizer >= 1.0:
            raise ValueError("Xác suất ngẫu nhiên hóa p phải nằm trong khoảng (0, 1).")

        # -------------------------------------------------------------
        # Step 1: Observed Sample Proportion
        # -------------------------------------------------------------
        lambda_hat = float(np.mean(rrt_arr))
        var_lambda = float(lambda_hat * (1.0 - lambda_hat) / N)

        # -------------------------------------------------------------
        # Step 2: Latent Prevalence Estimation by Model Type
        # -------------------------------------------------------------
        if model_type.lower() == "warner":
            # Warner (1965): lambda = (2p - 1)*pi + (1 - p)
            # pi = (lambda - (1 - p)) / (2p - 1)
            denom = 2.0 * p_randomizer - 1.0
            pi_hat = float((lambda_hat - (1.0 - p_randomizer)) / denom)
            se_pi = float(np.sqrt(var_lambda / (denom ** 2)))
            model_label = "Warner (1965) Standard RRT"
        elif model_type.lower() == "unrelated":
            # Horvitz-Simmons (1967): lambda = p * pi + (1 - p) * p_U
            # pi = (lambda - (1 - p)*p_U) / p
            pi_hat = float((lambda_hat - (1.0 - p_randomizer) * p_unrelated) / p_randomizer)
            se_pi = float(np.sqrt(var_lambda / (p_randomizer ** 2)))
            model_label = f"Unrelated Question Model (p_U = {p_unrelated:.2f})"
        else:  # "crosswise"
            # Yu et al. (2008), Jann et al. (2012):
            # lambda = Pr(same) = pi * p + (1 - pi)*(1 - p) = (2p - 1)*pi + (1 - p)
            denom = 2.0 * p_randomizer - 1.0
            pi_hat = float((lambda_hat - (1.0 - p_randomizer)) / denom)
            se_pi = float(np.sqrt(var_lambda / (denom ** 2)))
            model_label = "Crosswise Model (Yu et al. 2008; Jann 2012)"

        # Bound estimates to [0, 1] for interpretation, while noting raw
        pi_bounded = float(np.clip(pi_hat, 0.0, 1.0))

        z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))
        ci_lower = max(0.0, pi_hat - z_crit * se_pi)
        ci_upper = min(1.0, pi_hat + z_crit * se_pi)

        # -------------------------------------------------------------
        # Step 3: Direct Questioning Benchmark & Social Desirability Bias (SDB)
        # -------------------------------------------------------------
        sdb_diagnostics: Optional[Dict[str, Any]] = None
        if direct_responses is not None and len(direct_responses) == N:
            direct_arr = direct_responses.astype(int)
            pi_direct = float(np.mean(direct_arr))
            se_direct = float(np.sqrt(pi_direct * (1.0 - pi_direct) / N))

            # SDB Gap: Difference between RRT and Direct Questioning
            sdb_gap = float(pi_hat - pi_direct)
            # Covariance under paired design: cov(lambda_hat, pi_direct)
            cov_pair = float(np.cov(rrt_arr, direct_arr)[0, 1] / N)
            if model_type.lower() == "unrelated":
                var_gap = var_lambda / (p_randomizer ** 2) + se_direct ** 2 - 2.0 * cov_pair / p_randomizer
            else:
                var_gap = var_lambda / (denom ** 2) + se_direct ** 2 - 2.0 * cov_pair / denom

            se_gap = float(np.sqrt(max(1e-8, var_gap)))
            z_sdb = float(sdb_gap / se_gap)
            # One-sided test H0: sdb_gap <= 0 vs H1: sdb_gap > 0 (under-reporting in direct questioning)
            p_val_sdb = float(1.0 - stats.norm.cdf(z_sdb))

            sdb_diagnostics = {
                "direct_prevalence": round(pi_direct, 4),
                "direct_std_error": round(se_direct, 4),
                "direct_ci_95": [round(max(0.0, pi_direct - z_crit * se_direct), 4), round(min(1.0, pi_direct + z_crit * se_direct), 4)],
                "sdb_gap_percentage_points": round(sdb_gap * 100.0, 2),
                "gap_std_error": round(se_gap, 4),
                "z_statistic": round(z_sdb, 3),
                "p_value_underreporting": round(p_val_sdb, 5),
                "significant_underreporting": bool(p_val_sdb < alpha),
            }

        # -------------------------------------------------------------
        # Step 4: RRT Logistic Regression with Covariates (van den Hout 2002)
        # -------------------------------------------------------------
        logit_results: Optional[List[Dict[str, Any]]] = None
        if covariates is not None and covariates.ndim == 2 and covariates.shape[0] == N:
            logit_results = cls._fit_rrt_logistic(
                y_rrt=rrt_arr,
                X=covariates,
                model_type=model_type,
                p_rand=p_randomizer,
                p_unrel=p_unrelated,
                feature_names=covariate_names,
            )

        # -------------------------------------------------------------
        # Step 5: Privacy-Efficiency Curve over grid of p in (0.52, 0.95)
        # -------------------------------------------------------------
        p_grid = np.linspace(0.55, 0.95, 20)
        efficiency_curve: List[Dict[str, float]] = []
        for p_val in p_grid:
            # Efficiency variance multiplier relative to direct sampling:
            # For Crosswise/Warner: var(pi) = var(lambda) / (2p-1)^2
            den_g = 2.0 * p_val - 1.0
            var_mult = float(1.0 / (den_g ** 2))
            # Privacy measure: Shannon entropy or misclassification probability (1 - p_val)
            efficiency_curve.append({
                "p_randomizer": round(float(p_val), 3),
                "variance_inflation_factor": round(var_mult, 2),
                "privacy_protection_pct": round(float(1.0 - p_val) * 100.0, 1),
            })

        # -------------------------------------------------------------
        # Step 6: Dual-Panel Responsive SVG Visualizer
        # -------------------------------------------------------------
        svg_chart = cls._render_dual_panel_svg(
            pi_hat=pi_hat,
            ci_pi=[ci_lower, ci_upper],
            sdb_diag=sdb_diagnostics,
            efficiency_curve=efficiency_curve,
            model_label=model_label,
            p_rand=p_randomizer,
        )

        # -------------------------------------------------------------
        # Step 7: APA 7th Edition Academic Narrative
        # -------------------------------------------------------------
        apa_narrative = (
            f"A sensitive item prevalence evaluation using the {model_label} was conducted with N = {N} respondents "
            f"and randomization parameter p = {p_randomizer:.2f}. "
            f"The observed raw sample affirmative rate was {lambda_hat * 100:.1f}%. "
            f"After inverting the stochastic misclassification matrix to eliminate social desirability bias, "
            f"the estimated latent sensitive trait prevalence was pi = {pi_bounded * 100:.1f}% "
            f"(SE = {se_pi:.3f}, 95% CI [{ci_lower * 100:.1f}%, {ci_upper * 100:.1f}%]). "
        )
        if sdb_diagnostics:
            apa_narrative += (
                f"In contrast, direct questioning yielded a reported prevalence of only {sdb_diagnostics['direct_prevalence'] * 100:.1f}% "
                f"(SE = {sdb_diagnostics['direct_std_error']:.3f}), revealing an evasive answer gap of "
                f"Delta_SDB = {sdb_diagnostics['sdb_gap_percentage_points']:+.1f} percentage points (z = {sdb_diagnostics['z_statistic']:.2f}, "
                f"p = {sdb_diagnostics['p_value_underreporting']:.4f}). "
                f"{'This statistically significant under-reporting confirms pervasive social desirability distortion under conventional questioning.' if sdb_diagnostics['significant_underreporting'] else 'The under-reporting gap was not statistically significant at the nominal level.'}"
            )

        return {
            "status": "success",
            "sample_size": N,
            "model_type": model_type,
            "model_label": model_label,
            "randomization_probability": p_randomizer,
            "observed_affirmative_rate": round(lambda_hat, 4),
            "estimated_prevalence": round(pi_bounded, 4),
            "raw_unbounded_prevalence": round(pi_hat, 4),
            "std_error": round(se_pi, 4),
            "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
            "variance_inflation_factor": round(float(1.0 / max(1e-5, (2.0 * p_randomizer - 1.0) ** 2)), 2),
            "social_desirability_diagnostics": sdb_diagnostics,
            "rrt_logistic_regression": logit_results,
            "efficiency_curve": efficiency_curve,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _fit_rrt_logistic(
        cls,
        y_rrt: np.ndarray,
        X: np.ndarray,
        model_type: str,
        p_rand: float,
        p_unrel: float,
        feature_names: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """
        Fits maximum likelihood logistic regression under randomized response:
        pi_i = 1 / (1 + exp(-X_i beta))
        lambda_i = Pr(Y_i = 1 | X_i) = c + d * pi_i
        """
        N, P = X.shape
        # Add intercept
        X_design = np.column_stack([np.ones(N), X])
        names = ["(Intercept)"] + (feature_names if (feature_names and len(feature_names) == P) else [f"X{j+1}" for j in range(P)])

        if model_type.lower() == "unrelated":
            c = (1.0 - p_rand) * p_unrel
            d = p_rand
        else:
            c = 1.0 - p_rand
            d = 2.0 * p_rand - 1.0

        def neg_log_likelihood(beta):
            logits = X_design @ beta
            # pi_i in (0, 1)
            pi_i = 1.0 / (1.0 + np.exp(-np.clip(logits, -25.0, 25.0)))
            lambda_i = c + d * pi_i
            lambda_i = np.clip(lambda_i, 1e-6, 1.0 - 1e-6)
            ll = np.sum(y_rrt * np.log(lambda_i) + (1 - y_rrt) * np.log(1.0 - lambda_i))
            return -ll

        b0 = np.zeros(P + 1)
        res = opt.minimize(neg_log_likelihood, b0, method="BFGS", options={"maxiter": 100})
        b_hat = res.x

        # Invert Hessian for standard errors
        try:
            cov = res.hess_inv if hasattr(res, "hess_inv") and res.hess_inv.shape == (P + 1, P + 1) else np.eye(P + 1)
            se_b = np.sqrt(np.maximum(1e-6, np.diag(cov)))
        except Exception:
            se_b = np.ones(P + 1) * 0.1

        rows = []
        for j in range(P + 1):
            est = float(b_hat[j])
            se = float(se_b[j])
            z = est / max(1e-6, se)
            pval = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
            odds_ratio = float(np.exp(est)) if j > 0 else None

            rows.append({
                "term": names[j],
                "coefficient": round(est, 4),
                "std_error": round(se, 4),
                "z_statistic": round(float(z), 3),
                "p_value": round(float(pval), 5),
                "odds_ratio": round(odds_ratio, 3) if odds_ratio is not None else None,
            })
        return rows

    @classmethod
    def _render_dual_panel_svg(
        cls,
        pi_hat: float,
        ci_pi: List[float],
        sdb_diag: Optional[Dict[str, Any]],
        efficiency_curve: List[Dict[str, float]],
        model_label: str,
        p_rand: float,
    ) -> str:
        """Renders dual-panel vector SVG visualizer for RRT analysis."""
        width = 940
        height = 380
        p_w = 425
        p_h = 295
        margin = {"top": 45, "bottom": 35, "left": 130, "right": 25}

        # -------------------------------------------------------------
        # Panel A: Prevalence Estimation & SDB Gap Forest Plot
        # -------------------------------------------------------------
        pA_x = 25
        pA_y = 15
        x0_a = pA_x + margin["left"]
        y0_a = pA_y + margin["top"]
        iw_a = p_w - margin["left"] - margin["right"]
        ih_a = p_h - margin["top"] - margin["bottom"]

        # Axis scale: 0% to max(40%, upper CI * 1.2)
        max_pct = max(0.40, ci_pi[1] * 1.2)
        if sdb_diag:
            max_pct = max(max_pct, sdb_diag["direct_ci_95"][1] * 1.2)

        def map_x_a(v_pct: float) -> float:
            return x0_a + (v_pct / max_pct) * iw_a

        forest_items = [
            {
                "name": f"RRT Latent Prevalence ({model_label[:14]})",
                "est": max(0.0, pi_hat),
                "ci": ci_pi,
                "color": "#10b981",
            }
        ]
        if sdb_diag:
            forest_items.append({
                "name": "Direct Questioning (Biased)",
                "est": sdb_diag["direct_prevalence"],
                "ci": sdb_diag["direct_ci_95"],
                "color": "#ef4444",
            })

        row_h_a = ih_a / max(1, len(forest_items))
        elements_a = []

        for i, item in enumerate(forest_items):
            cy = y0_a + (i + 0.5) * row_h_a
            cx_est = map_x_a(item["est"])
            cx_l = map_x_a(item["ci"][0])
            cx_u = map_x_a(item["ci"][1])

            elements_a.append(
                f'<line x1="{cx_l:.1f}" y1="{cy:.1f}" x2="{cx_u:.1f}" y2="{cy:.1f}" stroke="{item["color"]}" stroke-width="2.5" stroke-linecap="round"/>'
            )
            elements_a.append(
                f'<circle cx="{cx_est:.1f}" cy="{cy:.1f}" r="5" fill="{item["color"]}" stroke="#ffffff" stroke-width="1.5"/>'
            )
            elements_a.append(
                f'<text x="{cx_est:.1f}" y="{cy - 8:.1f}" fill="{item["color"]}" font-size="11" font-weight="700" text-anchor="middle">'
                f'{item["est"] * 100:.1f}%</text>'
            )
            elements_a.append(
                f'<text x="{x0_a - 12:.1f}" y="{cy + 4:.1f}" fill="#cbd5e1" font-size="10" text-anchor="end">{item["name"]}</text>'
            )

        # -------------------------------------------------------------
        # Panel B: Privacy vs Efficiency Trade-Off Curve
        # -------------------------------------------------------------
        pB_x = 490
        pB_y = 15
        x0_b = pB_x + 55
        y0_b = pB_y + margin["top"]
        iw_b = p_w - 55 - 20
        ih_b = p_h - margin["top"] - margin["bottom"]

        vifs = [pt["variance_inflation_factor"] for pt in efficiency_curve]
        max_vif = max(vifs)

        def map_x_b(p_val: float) -> float:
            return x0_b + ((p_val - 0.55) / (0.95 - 0.55)) * iw_b

        def map_y_b(vif: float) -> float:
            return y0_b + ih_b - (min(25.0, vif) / 25.0) * ih_b

        pts_b = [f"{map_x_b(pt['p_randomizer']):.1f},{map_y_b(pt['variance_inflation_factor']):.1f}" for pt in efficiency_curve]
        cur_p_x = map_x_b(p_rand)
        cur_vif_y = map_y_b(1.0 / max(1e-5, (2.0 * p_rand - 1.0) ** 2))

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#0f172a; border-radius:12px; font-family:system-ui, -apple-system, sans-serif;">
  <!-- Panel A Header -->
  <text x="{pA_x + 10}" y="{pA_y + 24}" fill="#ffffff" font-size="13" font-weight="700">Panel A: Tỷ Lệ Hiện Nhiễm Thật &amp; Sai Lệch Mong Muốn Xã Hội (SDB)</text>
  <text x="{pA_x + 10}" y="{pA_y + 38}" fill="#94a3b8" font-size="10">So sánh tỷ lệ thực tế RRT vs Báo cáo trực tiếp (Khoảng tin cậy 95%)</text>

  <!-- Panel A Box & Elements -->
  <rect x="{x0_a}" y="{y0_a}" width="{iw_a}" height="{ih_a}" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1" rx="4"/>
  {''.join(elements_a)}

  <!-- Panel A X Axis -->
  <line x1="{x0_a}" y1="{y0_a + ih_a}" x2="{x0_a + iw_a}" y2="{y0_a + ih_a}" stroke="#475569" stroke-width="1"/>
  <text x="{x0_a}" y="{y0_a + ih_a + 16}" fill="#64748b" font-size="10" text-anchor="middle">0%</text>
  <text x="{x0_a + iw_a}" y="{y0_a + ih_a + 16}" fill="#64748b" font-size="10" text-anchor="middle">{max_pct * 100:.0f}%</text>
  <text x="{x0_a + iw_a / 2}" y="{y0_a + ih_a + 22}" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">Tỷ Lệ Hiện Nhiễm Hành Vi Nhạy Cảm (\u03c0)</text>

  <!-- Panel B Header -->
  <text x="{pB_x + 10}" y="{pB_y + 24}" fill="#ffffff" font-size="13" font-weight="700">Panel B: Đánh Đổi Bảo Mật vs Độ Chính Xác Thống Kê</text>
  <text x="{pB_x + 10}" y="{pB_y + 38}" fill="#94a3b8" font-size="10">Hệ số phóng đại phương sai (VIF) theo tham số ngẫu nhiên hóa p \u2208 (0.55, 0.95)</text>

  <!-- Panel B Box & Polyline -->
  <rect x="{x0_b}" y="{y0_b}" width="{iw_b}" height="{ih_b}" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1" rx="4"/>
  <polyline points="{' '.join(pts_b)}" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>

  <!-- Current p marker -->
  {f'<circle cx="{cur_p_x:.1f}" cy="{cur_vif_y:.1f}" r="5" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5"/>' if y0_b <= cur_vif_y <= y0_b + ih_b and x0_b <= cur_p_x <= x0_b + iw_b else ''}
  {f'<text x="{cur_p_x:.1f}" y="{cur_vif_y - 8:.1f}" fill="#f59e0b" font-size="10" font-weight="bold" text-anchor="middle">p = {p_rand:.2f}</text>' if y0_b <= cur_vif_y <= y0_b + ih_b and x0_b <= cur_p_x <= x0_b + iw_b else ''}

  <!-- Panel B Axes -->
  <line x1="{x0_b}" y1="{y0_b + ih_b}" x2="{x0_b + iw_b}" y2="{y0_b + ih_a}" stroke="#475569" stroke-width="1"/>
  <text x="{x0_b}" y="{y0_b + ih_b + 16}" fill="#64748b" font-size="10" text-anchor="middle">0.55</text>
  <text x="{x0_b + iw_b}" y="{y0_b + ih_b + 16}" fill="#64748b" font-size="10" text-anchor="middle">0.95</text>
  <text x="{x0_b + iw_b / 2}" y="{y0_b + ih_b + 22}" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">Xác Suất Ngẫu Nhiên Hóa (p)</text>
  <text x="{x0_b - 8}" y="{y0_b + 10}" fill="#64748b" font-size="9" text-anchor="end">25x</text>
  <text x="{x0_b - 8}" y="{y0_b + ih_b}" fill="#64748b" font-size="9" text-anchor="end">1x</text>
</svg>'''
        return svg


def run_randomized_response_analysis(
    records: List[Dict[str, Any]],
    rrt_question_id: str,
    model_type: str = "crosswise",
    p_randomizer: float = 0.70,
    p_unrelated: float = 0.50,
    direct_question_id: Optional[str] = None,
    covariate_question_ids: Optional[List[str]] = None,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Helper function to parse survey records into numpy arrays and invoke RandomizedResponseEngine.
    """
    rrt_list: List[int] = []
    direct_list: List[int] = []
    cov_rows: List[List[float]] = []

    cov_ids = covariate_question_ids or []

    for r in records:
        rrt_raw = r.get(rrt_question_id)
        if rrt_raw is None or str(rrt_raw).strip() == "":
            continue
        try:
            rrt_val = 1 if float(rrt_raw) > 0.5 else 0
        except (ValueError, TypeError):
            continue

        if direct_question_id is not None:
            dir_raw = r.get(direct_question_id)
            try:
                dir_val = 1 if float(dir_raw) > 0.5 else 0
            except (ValueError, TypeError):
                dir_val = 0
            direct_list.append(dir_val)

        if cov_ids:
            row_c = []
            valid_c = True
            for cid in cov_ids:
                c_val = r.get(cid)
                try:
                    row_c.append(float(c_val))
                except (ValueError, TypeError):
                    valid_c = False
                    break
            if valid_c:
                cov_rows.append(row_c)

        rrt_list.append(rrt_val)

    if len(rrt_list) < 20:
        raise ValueError(f"Không đủ phản hồi hợp lệ cho phân tích Randomized Response (N={len(rrt_list)} < 20).")

    direct_arr = np.array(direct_list) if direct_question_id else None
    cov_arr = np.array(cov_rows) if (cov_ids and len(cov_rows) == len(rrt_list)) else None

    return RandomizedResponseEngine.evaluate(
        rrt_responses=np.array(rrt_list),
        model_type=model_type,
        p_randomizer=p_randomizer,
        p_unrelated=p_unrelated,
        direct_responses=direct_arr,
        covariates=cov_arr,
        covariate_names=cov_ids if cov_arr is not None else None,
        alpha=alpha,
    )
