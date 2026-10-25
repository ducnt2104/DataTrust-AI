# -*- coding: utf-8 -*-
"""
Zero-Inflated Count Models Engine (ZIP & ZINB)
=====================================================
Theoretical references:
- Lambert, D. (1992). Zero-Inflated Poisson Regression, with an Application to Defects
  in Manufacturing. Technometrics, 34(1), 1-14.
- Greene, W. H. (1994). Accounting for Excess Zeros and Sample Selection in Poisson
  and Negative Binomial Regression Models. NYU Working Paper EC-94-10.
- Vuong, Q. H. (1989). Likelihood Ratio Tests for Model Selection and Non-Nested
  Hypotheses. Econometrica, 57(2), 307-333.
- Long, J. S. (1997). Regression Models for Categorical and Limited Dependent Variables.
  SAGE Publications.
"""
import math
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats, optimize, special


class ZeroInflatedEngine:
    """
    Ước lượng Mô hình Hồi quy Đếm Đột biến Không (Zero-Inflated Count Models):
    - Zero-Inflated Poisson (ZIP)
    - Zero-Inflated Negative Binomial (ZINB)
    Kèm Kiểm định Vuong (1989) phi lồng ghép và Kiểm định Phân tán quá mức (Overdispersion).
    """

    @classmethod
    def estimate(
        cls,
        data: List[Dict[str, Any]],
        count_var: str,
        covariates: List[str],
        inflation_covariates: Optional[List[str]] = None,
        model_type: str = "ZIP",  # "ZIP" or "ZINB"
    ) -> Dict[str, Any]:
        """
        data: Danh sách dict phản hồi
        count_var: Biến đếm Y (không âm, số nguyên >= 0)
        covariates: Biến giải thích cho quá trình đếm (Count process X)
        inflation_covariates: Biến giải thích cho quá trình đột biến không (Zero inflation Z, nếu None dùng X)
        model_type: "ZIP" (Poisson) hoặc "ZINB" (Negative Binomial)
        """
        if not data or not count_var or not covariates:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": "Dữ liệu hoặc danh sách biến không hợp lệ."
            }

        infl_vars = inflation_covariates if (inflation_covariates and len(inflation_covariates) > 0) else covariates

        # Clean rows
        clean_rows = []
        for r in data:
            try:
                y_val = float(r.get(count_var, None))
                if y_val < 0 or math.isnan(y_val):
                    continue
                x_vals = [float(r.get(c, None)) for c in covariates]
                z_vals = [float(r.get(zv, None)) for zv in infl_vars]
                if any(math.isnan(v) for v in x_vals) or any(math.isnan(v) for v in z_vals):
                    continue
                clean_rows.append((int(round(y_val)), x_vals, z_vals))
            except (ValueError, TypeError):
                continue

        N = len(clean_rows)
        K_x = len(covariates)
        K_z = len(infl_vars)

        if N < 25:
            return {
                "status": "INSUFFICIENT_VALID_SAMPLE",
                "message": f"Chỉ có {N} quan sát hợp lệ (cần tối thiểu 25 quan sát để ước lượng mô hình Zero-Inflated)."
            }

        Y = np.array([cr[0] for cr in clean_rows], dtype=int)
        X_raw = np.array([cr[1] for cr in clean_rows], dtype=float)
        Z_raw = np.array([cr[2] for cr in clean_rows], dtype=float)

        # Design matrices with intercept: [1, X] and [1, Z]
        X = np.column_stack([np.ones(N), X_raw])
        Z = np.column_stack([np.ones(N), Z_raw])

        p_x = K_x + 1  # count params (including intercept)
        p_z = K_z + 1  # inflation params (including intercept)

        zero_count = int(np.sum(Y == 0))
        zero_pct = float(zero_count / N * 100.0)
        mean_y = float(np.mean(Y))
        var_y = float(np.var(Y, ddof=1)) if N > 1 else 0.0

        is_zinb = (model_type.upper() == "ZINB")

        # 1. Baseline Standard Poisson / NB Regression (for Vuong test)
        def standard_poisson_neg_ll(beta: np.ndarray) -> float:
            eta = np.clip(X @ beta, -20.0, 20.0)
            mu = np.exp(eta)
            # log f(y) = y*ln(mu) - mu - ln(y!)
            # using gammaln(y+1)
            ll = np.sum(Y * np.log(np.maximum(1e-12, mu)) - mu - special.gammaln(Y + 1))
            return float(-ll)

        # Standard Poisson MLE
        beta_init_std = np.zeros(p_x)
        beta_init_std[0] = math.log(max(0.1, mean_y))
        res_std_pois = optimize.minimize(
            standard_poisson_neg_ll,
            beta_init_std,
            method="L-BFGS-B",
            options={"maxiter": 300}
        )
        beta_std = res_std_pois.x
        ll_std_poisson = float(-res_std_pois.fun)

        # Calculate standard Poisson point-wise log likelihoods
        eta_std = np.clip(X @ beta_std, -20.0, 20.0)
        mu_std = np.exp(eta_std)
        ll_indiv_std = Y * np.log(np.maximum(1e-12, mu_std)) - mu_std - special.gammaln(Y + 1)

        # 2. Zero-Inflated Model MLE
        # Parameter vector theta:
        # ZIP: [beta_0..beta_K (count), gamma_0..gamma_M (inflation)] -> dim = p_x + p_z
        # ZINB: [beta_0..beta_K, gamma_0..gamma_M, ln_alpha] -> dim = p_x + p_z + 1
        dim_total = (p_x + p_z + 1) if is_zinb else (p_x + p_z)

        def zi_neg_log_lik(theta: np.ndarray) -> float:
            beta = theta[:p_x]
            gamma = theta[p_x:p_x + p_z]
            alpha = math.exp(np.clip(theta[p_x + p_z], -10.0, 5.0)) if is_zinb else 0.0

            eta_count = np.clip(X @ beta, -20.0, 20.0)
            mu = np.exp(eta_count)

            eta_infl = np.clip(Z @ gamma, -20.0, 20.0)
            p_infl = 1.0 / (1.0 + np.exp(-eta_infl))  # probability of structural zero

            # Element-wise log-likelihood
            is_zero = (Y == 0)
            ll_i = np.zeros(N)

            if not is_zinb:
                # ZIP
                # For y = 0: P(Y=0) = p_infl + (1 - p_infl) * exp(-mu)
                p0_count = np.exp(-mu)
                prob_zero = p_infl[is_zero] + (1.0 - p_infl[is_zero]) * p0_count[is_zero]
                ll_i[is_zero] = np.log(np.maximum(1e-15, prob_zero))

                # For y > 0: P(Y=y) = (1 - p_infl) * [exp(-mu) * mu^y / y!]
                # ln P(Y=y) = ln(1 - p_infl) - mu + y*ln(mu) - gammaln(y+1)
                not_zero = ~is_zero
                ll_i[not_zero] = (
                    np.log(np.maximum(1e-15, 1.0 - p_infl[not_zero]))
                    - mu[not_zero]
                    + Y[not_zero] * np.log(np.maximum(1e-12, mu[not_zero]))
                    - special.gammaln(Y[not_zero] + 1)
                )
            else:
                # ZINB (NB2 dispersion parameter alpha = 1 / r)
                # Count density: P(Y=y) = Gamma(y + 1/alpha)/(Gamma(y+1)Gamma(1/alpha)) * (1/(1 + alpha*mu))^(1/alpha) * (alpha*mu/(1 + alpha*mu))^y
                inv_a = 1.0 / max(1e-6, alpha)
                p0_nb = (1.0 / (1.0 + alpha * mu)) ** inv_a
                prob_zero = p_infl[is_zero] + (1.0 - p_infl[is_zero]) * p0_nb[is_zero]
                ll_i[is_zero] = np.log(np.maximum(1e-15, prob_zero))

                not_zero = ~is_zero
                y_nz = Y[not_zero]
                mu_nz = mu[not_zero]
                p_infl_nz = p_infl[not_zero]

                log_comb = special.gammaln(y_nz + inv_a) - special.gammaln(y_nz + 1) - special.gammaln(inv_a)
                log_p_nb = (
                    log_comb
                    - inv_a * np.log(1.0 + alpha * mu_nz)
                    + y_nz * np.log(np.maximum(1e-12, alpha * mu_nz / (1.0 + alpha * mu_nz)))
                )
                ll_i[not_zero] = np.log(np.maximum(1e-15, 1.0 - p_infl_nz)) + log_p_nb

            return float(-np.sum(ll_i))

        # Initial parameter guess
        init_beta = beta_std.copy()
        init_gamma = np.zeros(p_z)
        # Prior guess for structural zero rate ~ logit(zero_pct / 100)
        p_guess = max(0.05, min(0.95, zero_pct / 100.0 * 0.5))
        init_gamma[0] = math.log(p_guess / (1.0 - p_guess))

        if is_zinb:
            # guess ln_alpha
            alpha_guess = max(0.05, (var_y - mean_y) / (mean_y ** 2) if var_y > mean_y else 0.1)
            theta_init = np.concatenate([init_beta, init_gamma, [math.log(alpha_guess)]])
            bounds = [(None, None)] * (p_x + p_z) + [(-6.0, 4.0)]
        else:
            theta_init = np.concatenate([init_beta, init_gamma])
            bounds = [(None, None)] * (p_x + p_z)

        res_zi = optimize.minimize(
            zi_neg_log_lik,
            theta_init,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 600, "ftol": 1e-7, "gtol": 1e-6}
        )

        converged = bool(res_zi.success or res_zi.status == 0)
        final_theta = res_zi.x
        final_zi_ll = float(-res_zi.fun)

        beta_hat = final_theta[:p_x]
        gamma_hat = final_theta[p_x:p_x + p_z]
        alpha_hat = float(math.exp(np.clip(final_theta[p_x + p_z], -10.0, 5.0))) if is_zinb else 0.0

        # Standard errors via numerical Hessian inversion
        try:
            h_step = 1e-4
            d_p = len(final_theta)
            H = np.zeros((d_p, d_p))
            for i in range(d_p):
                for j in range(i, d_p):
                    t_pp = final_theta.copy(); t_pp[i] += h_step; t_pp[j] += h_step
                    t_pm = final_theta.copy(); t_pm[i] += h_step; t_pm[j] -= h_step
                    t_mp = final_theta.copy(); t_mp[i] -= h_step; t_mp[j] += h_step
                    t_mm = final_theta.copy(); t_mm[i] -= h_step; t_mm[j] -= h_step
                    v_diff = (zi_neg_log_lik(t_pp) - zi_neg_log_lik(t_pm) - zi_neg_log_lik(t_mp) + zi_neg_log_lik(t_mm)) / (4.0 * h_step * h_step)
                    H[i, j] = v_diff
                    H[j, i] = v_diff
            H_inv = np.linalg.pinv(H)
            se_all = np.sqrt(np.maximum(0.0, np.diag(H_inv)))
        except Exception:
            se_all = np.array([0.1] * dim_total)

        se_beta = se_all[:p_x]
        se_gamma = se_all[p_x:p_x + p_z]
        se_alpha = float(se_all[p_x + p_z]) if is_zinb else 0.0

        # 3. Vuong (1989) Non-Nested Model Selection Test
        # Pointwise log likelihood of Zero-Inflated model
        def get_indiv_zi_ll(theta: np.ndarray) -> np.ndarray:
            b = theta[:p_x]
            g = theta[p_x:p_x + p_z]
            a = math.exp(np.clip(theta[p_x + p_z], -10.0, 5.0)) if is_zinb else 0.0

            eta_c = np.clip(X @ b, -20.0, 20.0)
            m = np.exp(eta_c)
            eta_i = np.clip(Z @ g, -20.0, 20.0)
            p = 1.0 / (1.0 + np.exp(-eta_i))

            ll_arr = np.zeros(N)
            is_z = (Y == 0)

            if not is_zinb:
                p0 = np.exp(-m)
                ll_arr[is_z] = np.log(np.maximum(1e-15, p[is_z] + (1.0 - p[is_z]) * p0[is_z]))
                nz = ~is_z
                ll_arr[nz] = (
                    np.log(np.maximum(1e-15, 1.0 - p[nz]))
                    - m[nz] + Y[nz] * np.log(np.maximum(1e-12, m[nz]))
                    - special.gammaln(Y[nz] + 1)
                )
            else:
                inv_a = 1.0 / max(1e-6, a)
                p0_nb = (1.0 / (1.0 + a * m)) ** inv_a
                ll_arr[is_z] = np.log(np.maximum(1e-15, p[is_z] + (1.0 - p[is_z]) * p0_nb[is_z]))
                nz = ~is_z
                log_c = special.gammaln(Y[nz] + inv_a) - special.gammaln(Y[nz] + 1) - special.gammaln(inv_a)
                log_nb = log_c - inv_a * np.log(1.0 + a * m[nz]) + Y[nz] * np.log(np.maximum(1e-12, a * m[nz] / (1.0 + a * m[nz])))
                ll_arr[nz] = np.log(np.maximum(1e-15, 1.0 - p[nz])) + log_nb

            return ll_arr

        ll_indiv_zi = get_indiv_zi_ll(final_theta)
        m_diff = ll_indiv_zi - ll_indiv_std
        mean_m = float(np.mean(m_diff))
        std_m = float(np.std(m_diff, ddof=1)) if N > 1 else 1.0

        vuong_stat = float(math.sqrt(N) * mean_m / std_m) if std_m > 1e-9 else 0.0
        vuong_pval = float(2.0 * (1.0 - stats.norm.cdf(abs(vuong_stat))))

        if vuong_stat > 1.96:
            vuong_verdict = f"Mô hình {model_type} vượt trội vượt bậc so với Poisson thường (Vuong z = {vuong_stat:.3f}, p < 0.05). Đột biến không có ý nghĩa thống kê."
            favors_zero_inflation = True
        elif vuong_stat < -1.96:
            vuong_verdict = f"Mô hình thường đủ chuẩn, không cần Zero-Inflation (Vuong z = {vuong_stat:.3f}, p < 0.05)."
            favors_zero_inflation = False
        else:
            vuong_verdict = f"Kiểm định Vuong không phân định dứt khoát (|z| <= 1.96, p = {vuong_pval:.3f})."
            favors_zero_inflation = False

        # AIC / BIC
        k_params = dim_total
        aic_zi = float(2.0 * k_params - 2.0 * final_zi_ll)
        bic_zi = float(k_params * math.log(N) - 2.0 * final_zi_ll)

        aic_std = float(2.0 * p_x - 2.0 * ll_std_poisson)
        bic_std = float(p_x * math.log(N) - 2.0 * ll_std_poisson)

        # 4. Coefficients Extraction
        # Count coefficients (beta) -> Incidence Rate Ratio IRR = exp(beta)
        count_coeffs = []
        for j in range(p_x):
            is_int = (j == 0)
            vname = "Intercept (Count β₀)" if is_int else covariates[j - 1]
            b_val = float(beta_hat[j])
            se_b = float(se_beta[j])
            z_val = float(b_val / se_b) if se_b > 1e-9 else 0.0
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_val))))
            irr = float(math.exp(np.clip(b_val, -15.0, 15.0)))
            ci_low = float(b_val - 1.96 * se_b)
            ci_high = float(b_val + 1.96 * se_b)
            irr_low = float(math.exp(np.clip(ci_low, -15.0, 15.0)))
            irr_high = float(math.exp(np.clip(ci_high, -15.0, 15.0)))

            count_coeffs.append({
                "variable": vname,
                "is_intercept": is_int,
                "coefficient": round(b_val, 4),
                "incidence_rate_ratio_irr": round(irr, 4),
                "standard_error": round(se_b, 4),
                "z_statistic": round(z_val, 3),
                "p_value": round(p_val, 4),
                "ci_95_lower": round(ci_low, 4),
                "ci_95_upper": round(ci_high, 4),
                "irr_95_lower": round(irr_low, 4),
                "irr_95_upper": round(irr_high, 4),
                "is_significant": bool(p_val < 0.05)
            })

        # Inflation coefficients (gamma) -> Odds Ratio OR = exp(gamma)
        inflation_coeffs = []
        for j in range(p_z):
            is_int = (j == 0)
            vname = "Intercept (Inflation γ₀)" if is_int else infl_vars[j - 1]
            g_val = float(gamma_hat[j])
            se_g = float(se_gamma[j])
            z_val = float(g_val / se_g) if se_g > 1e-9 else 0.0
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_val))))
            or_val = float(math.exp(np.clip(g_val, -15.0, 15.0)))
            ci_low = float(g_val - 1.96 * se_g)
            ci_high = float(g_val + 1.96 * se_g)
            or_low = float(math.exp(np.clip(ci_low, -15.0, 15.0)))
            or_high = float(math.exp(np.clip(ci_high, -15.0, 15.0)))

            inflation_coeffs.append({
                "variable": vname,
                "is_intercept": is_int,
                "logit_coefficient": round(g_val, 4),
                "odds_ratio": round(or_val, 4),
                "standard_error": round(se_g, 4),
                "z_statistic": round(z_val, 3),
                "p_value": round(p_val, 4),
                "ci_95_lower": round(ci_low, 4),
                "ci_95_upper": round(ci_high, 4),
                "or_95_lower": round(or_low, 4),
                "or_95_upper": round(or_high, 4),
                "is_significant": bool(p_val < 0.05)
            })

        # 5. Model Predicted Frequencies for Counts 0, 1, 2, ..., max_plot_count
        max_c = min(10, int(np.percentile(Y, 98)) + 2)
        count_bins = list(range(max_c + 1))
        obs_counts = [int(np.sum(Y == c)) for c in count_bins]

        # Predicted probabilities by summing over all individuals
        eta_c_all = np.clip(X @ beta_hat, -20.0, 20.0)
        mu_all = np.exp(eta_c_all)
        eta_i_all = np.clip(Z @ gamma_hat, -20.0, 20.0)
        p_infl_all = 1.0 / (1.0 + np.exp(-eta_i_all))

        pred_counts = []
        for c in count_bins:
            if not is_zinb:
                if c == 0:
                    prob_indiv = p_infl_all + (1.0 - p_infl_all) * np.exp(-mu_all)
                else:
                    prob_indiv = (1.0 - p_infl_all) * (np.exp(-mu_all) * (mu_all ** c) / math.factorial(c))
            else:
                inv_a = 1.0 / max(1e-6, alpha_hat)
                if c == 0:
                    p0_nb = (1.0 / (1.0 + alpha_hat * mu_all)) ** inv_a
                    prob_indiv = p_infl_all + (1.0 - p_infl_all) * p0_nb
                else:
                    comb = math.exp(special.gammaln(c + inv_a) - special.gammaln(c + 1) - special.gammaln(inv_a))
                    p_nb = comb * ((1.0 / (1.0 + alpha_hat * mu_all)) ** inv_a) * ((alpha_hat * mu_all / (1.0 + alpha_hat * mu_all)) ** c)
                    prob_indiv = (1.0 - p_infl_all) * p_nb
            pred_counts.append(float(np.sum(prob_indiv)))

        # 6. Dual-Panel SVG Visualization
        svg_chart = cls._render_dual_panel_svg(
            count_bins=count_bins,
            obs_counts=obs_counts,
            pred_counts=pred_counts,
            count_coeffs=count_coeffs,
            model_name=model_type.upper()
        )

        # 7. APA 7th Narrative
        narrative = cls._generate_apa_narrative(
            N=N,
            zero_count=zero_count,
            zero_pct=zero_pct,
            mean_y=mean_y,
            var_y=var_y,
            model_type=model_type.upper(),
            vuong_stat=vuong_stat,
            vuong_pval=vuong_pval,
            favors_zi=favors_zero_inflation,
            count_coeffs=count_coeffs,
            inflation_coeffs=inflation_coeffs,
            alpha_hat=alpha_hat if is_zinb else None
        )

        diagnostics = {
            "sample_size": N,
            "zero_observations_count": zero_count,
            "zero_percentage": round(zero_pct, 2),
            "sample_mean": round(mean_y, 3),
            "sample_variance": round(var_y, 3),
            "dispersion_ratio": round(var_y / max(1e-9, mean_y), 3),
            "converged": converged,
            "model_type": model_type.upper(),
            "log_likelihood_zi": round(final_zi_ll, 2),
            "log_likelihood_standard_poisson": round(ll_std_poisson, 2),
            "aic_zi": round(aic_zi, 2),
            "bic_zi": round(bic_zi, 2),
            "aic_standard_poisson": round(aic_std, 2),
            "bic_standard_poisson": round(bic_std, 2),
            "vuong_test_z": round(vuong_stat, 3),
            "vuong_test_p": round(vuong_pval, 4),
            "vuong_favors_zero_inflation": favors_zero_inflation,
            "vuong_verdict": vuong_verdict,
            "dispersion_parameter_alpha": round(alpha_hat, 4) if is_zinb else None
        }

        return {
            "status": "SUCCESS",
            "model_type": f"ZERO_INFLATED_{model_type.upper()}",
            "diagnostics": diagnostics,
            "count_model_coefficients": count_coeffs,
            "inflation_model_coefficients": inflation_coeffs,
            "frequency_distribution": {
                "counts": count_bins,
                "observed_frequencies": obs_counts,
                "predicted_frequencies": [round(pc, 2) for pc in pred_counts]
            },
            "svg_visualization": svg_chart,
            "apa_narrative": narrative
        }

    @staticmethod
    def _render_dual_panel_svg(
        count_bins: List[int],
        obs_counts: List[int],
        pred_counts: List[float],
        count_coeffs: List[Dict[str, Any]],
        model_name: str
    ) -> str:
        """
        Panel A: Observed vs Predicted Count Frequency (Excess Zeros Spike).
        Panel B: Forest Plot of Count Coefficients (Incidence Rate Ratios IRR) with 95% CIs.
        """
        width, height = 980, 420
        p1_x, p1_y, p1_w, p1_h = 60, 60, 400, 310
        p2_x, p2_y, p2_w, p2_h = 530, 60, 400, 310

        # Panel 1: Bar chart comparing observed vs predicted
        max_freq = max(max(obs_counts), max(pred_counts), 1) * 1.15
        n_bins = len(count_bins)
        bar_group_w = p1_w / max(1, n_bins)
        single_bar_w = max(4.0, (bar_group_w - 6) / 2.0)

        bars_svg = []
        for i, c in enumerate(count_bins):
            gx = p1_x + i * bar_group_w
            # Observed bar (teal)
            obs_h = (obs_counts[i] / max_freq) * p1_h
            obs_y = p1_y + p1_h - obs_h
            bars_svg.append(
                f'<rect x="{gx + 2:.1f}" y="{obs_y:.1f}" width="{single_bar_w:.1f}" height="{obs_h:.1f}" '
                f'fill="#0ea5e9" rx="2" opacity="0.85"><title>Count {c}: Observed {obs_counts[i]}</title></rect>'
            )
            # Predicted bar (amber/emerald)
            pred_h = (pred_counts[i] / max_freq) * p1_h
            pred_y = p1_y + p1_h - pred_h
            bars_svg.append(
                f'<rect x="{gx + 2 + single_bar_w + 1:.1f}" y="{pred_y:.1f}" width="{single_bar_w:.1f}" height="{pred_h:.1f}" '
                f'fill="#10b981" rx="2" opacity="0.85"><title>Count {c}: Predicted {pred_counts[i]:.1f}</title></rect>'
            )
            # Label
            bars_svg.append(
                f'<text x="{gx + bar_group_w / 2:.1f}" y="{p1_y + p1_h + 15}" text-anchor="middle" fill="#94a3b8" font-size="10">{c}</text>'
            )

        # Panel 2: Forest Plot of Count Coefficients (Excluding Intercept if > 1)
        slope_coeffs = [c for c in count_coeffs if not c["is_intercept"]]
        if not slope_coeffs:
            slope_coeffs = count_coeffs

        n_slopes = len(slope_coeffs)
        row_h = p2_h / max(1, n_slopes)

        # Min and Max CI for scaling
        all_lows = [sc["ci_95_lower"] for sc in slope_coeffs]
        all_highs = [sc["ci_95_upper"] for sc in slope_coeffs]
        min_x = min(min(all_lows) - 0.2, -0.2)
        max_x = max(max(all_highs) + 0.2, 0.2)
        rng_x = max(1e-6, max_x - min_x)

        def x_map(v: float) -> float:
            return p2_x + 120 + ((v - min_x) / rng_x) * (p2_w - 140)

        zero_ref_x = x_map(0.0)

        forest_svg = []
        # Zero reference line
        forest_svg.append(
            f'<line x1="{zero_ref_x:.1f}" y1="{p2_y}" x2="{zero_ref_x:.1f}" y2="{p2_y + p2_h}" '
            f'stroke="#64748b" stroke-dasharray="3,3" stroke-width="1.2" />'
        )

        for idx, sc in enumerate(slope_coeffs):
            cy = p2_y + (idx + 0.5) * row_h
            x_est = x_map(sc["coefficient"])
            x_l = x_map(sc["ci_95_lower"])
            x_h = x_map(sc["ci_95_upper"])

            # Variable label
            v_short = sc["variable"][:16] + ".." if len(sc["variable"]) > 18 else sc["variable"]
            forest_svg.append(
                f'<text x="{p2_x + 110}" y="{cy + 4:.1f}" text-anchor="end" fill="#f8fafc" font-size="11" font-weight="500">{v_short}</text>'
            )

            # CI line
            color = "#10b981" if sc["is_significant"] else "#94a3b8"
            forest_svg.append(
                f'<line x1="{x_l:.1f}" y1="{cy:.1f}" x2="{x_h:.1f}" y2="{cy:.1f}" stroke="{color}" stroke-width="2" />'
            )
            # Whiskers
            forest_svg.append(f'<line x1="{x_l:.1f}" y1="{cy - 4:.1f}" x2="{x_l:.1f}" y2="{cy + 4:.1f}" stroke="{color}" stroke-width="1.5" />')
            forest_svg.append(f'<line x1="{x_h:.1f}" y1="{cy - 4:.1f}" x2="{x_h:.1f}" y2="{cy + 4:.1f}" stroke="{color}" stroke-width="1.5" />')

            # Point estimate marker
            forest_svg.append(
                f'<circle cx="{x_est:.1f}" cy="{cy:.1f}" r="4.5" fill="{color}" stroke="#0f172a" stroke-width="1.5">'
                f'<title>{sc["variable"]}: β = {sc["coefficient"]}, IRR = {sc["incidence_rate_ratio_irr"]}</title></circle>'
            )

        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#090d16; font-family:system-ui, sans-serif;">
  <defs>
    <linearGradient id="gradP1" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0284c7" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.0"/>
    </linearGradient>
  </defs>

  <!-- Title -->
  <text x="30" y="32" fill="#f8fafc" font-size="14" font-weight="700">Zero-Inflated Count Model Analysis ({model_name})</text>
  <text x="30" y="48" fill="#94a3b8" font-size="11">Quá trình Đột biến Không (Lambert 1992) &amp; Kiểm định Vuong (1989)</text>

  <!-- Panel 1: Count Frequency Distribution -->
  <rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" fill="#0f172a" rx="6" stroke="#1e293b"/>
  <text x="{p1_x + 12}" y="{p1_y + 22}" fill="#38bdf8" font-size="11" font-weight="600">Panel A: Tần suất Thực tế vs Dự báo (Excess Zeros Spike)</text>
  <!-- Legend P1 -->
  <rect x="{p1_x + p1_w - 170}" y="{p1_y + 12}" width="10" height="10" fill="#0ea5e9" rx="2"/>
  <text x="{p1_x + p1_w - 155}" y="{p1_y + 21}" fill="#94a3b8" font-size="10">Thực tế (Obs)</text>
  <rect x="{p1_x + p1_w - 85}" y="{p1_y + 12}" width="10" height="10" fill="#10b981" rx="2"/>
  <text x="{p1_x + p1_w - 70}" y="{p1_y + 21}" fill="#94a3b8" font-size="10">Dự báo ({model_name})</text>
  {"".join(bars_svg)}

  <!-- Panel 2: Forest Plot -->
  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#0f172a" rx="6" stroke="#1e293b"/>
  <text x="{p2_x + 12}" y="{p2_y + 22}" fill="#34d399" font-size="11" font-weight="600">Panel B: Hệ số Hồi quy Đếm (β) kèm Khoảng Tin Cậy 95%</text>
  {"".join(forest_svg)}
</svg>'''

    @staticmethod
    def _generate_apa_narrative(
        N: int,
        zero_count: int,
        zero_pct: float,
        mean_y: float,
        var_y: float,
        model_type: str,
        vuong_stat: float,
        vuong_pval: float,
        favors_zi: bool,
        count_coeffs: List[Dict[str, Any]],
        inflation_coeffs: List[Dict[str, Any]],
        alpha_hat: Optional[float]
    ) -> str:
        """
        Tạo đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Lambert (1992) và Vuong (1989).
        """
        sig_count = [c for c in count_coeffs if not c["is_intercept"] and c["is_significant"]]
        sig_infl = [c for c in inflation_coeffs if not c["is_intercept"] and c["is_significant"]]

        p1 = (
            f"Mô hình hồi quy đếm đột biến không {model_type} (Zero-Inflated {model_type}; Lambert, 1992; Greene, 1994) "
            f"được ước lượng trên mẫu khảo sát gồm N = {N} quan sát. Biến kết quả dạng đếm thể hiện hiện tượng "
            f"đột biến không đáng kể với {zero_count} quan sát có giá trị bằng 0 (chiếm {zero_pct:.1f}% tổng mẫu). "
            f"Giá trị trung bình mẫu là M = {mean_y:.2f} (phương sai Var = {var_y:.2f}), "
            f"tỷ số phân tán Var/M = {var_y / max(1e-9, mean_y):.2f}"
            + (f", xác nhận hiện tượng phân tán quá mức (overdispersion) với tham số α = {alpha_hat:.4f}." if alpha_hat is not None else ".")
        )

        vuong_str = (
            f"Kiểm định phi lồng ghép Vuong (Vuong, 1989) so sánh mô hình {model_type} với mô hình Poisson tiêu chuẩn "
            f"đạt giá trị z = {vuong_stat:.3f} (p " + ("< .001" if vuong_pval < 0.001 else f"= {vuong_pval:.3f}") + "). "
            + (
                f"Thống kê Vuong có ý nghĩa tích cực (z > 1.96), khẳng định một cách vững chắc rằng mô hình {model_type} "
                f"vượt trội có ý nghĩa thống kê so với mô hình đếm thông thường, chứng minh cơ chế tạo dữ liệu bao gồm hai quá trình phân biệt: "
                f"nhóm người luôn bằng 0 (structural zero) và nhóm tham gia phân phối đếm."
                if favors_zi else
                f"Thống kê Vuong (|z| <= 1.96) chỉ ra rằng cơ chế đột biến không không đem lại sự cải thiện vượt bậc đáng kể so với mô hình thường."
            )
        )

        p3_parts = []
        if sig_count:
            items_c = [
                f"{c['variable']} (β = {c['coefficient']}, IRR = {c['incidence_rate_ratio_irr']}, 95% CI [{c['ci_95_lower']}, {c['ci_95_upper']}], p = {c['p_value']})"
                for c in sig_count
            ]
            p3_parts.append(
                f"Trong phương trình đếm (Count Process), các yếu tố dự báo có ý nghĩa thống kê làm thay đổi tỷ lệ số lần biến cố (Incidence Rate Ratio - IRR) gồm: "
                + "; ".join(items_c) + "."
            )

        if sig_infl:
            items_i = [
                f"{c['variable']} (γ = {c['logit_coefficient']}, Odds Ratio OR = {c['odds_ratio']}, p = {c['p_value']})"
                for c in sig_infl
            ]
            p3_parts.append(
                f"Trong phương trình đột biến không (Zero Inflation Logit Process), các yếu tố làm gia tăng xác suất thuộc nhóm luôn bằng 0 (structural zero) gồm: "
                + "; ".join(items_i) + "."
            )

        p3 = " ".join(p3_parts) if p3_parts else "Các biến giải thích trong cả hai phương trình không đạt ngưỡng ý nghĩa thống kê p < .05."

        return f"{p1}\n\n{vuong_str}\n\n{p3}"
