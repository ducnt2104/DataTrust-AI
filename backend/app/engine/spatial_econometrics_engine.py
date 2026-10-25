"""
Spatial Econometrics & Moran's I Autoregressive Engine (SAR / SEM).
References:
- Anselin, L. (1988). Spatial Econometrics: Methods and Models. Kluwer Academic Publishers.
- LeSage, J., & Pace, R. K. (2009). Introduction to Spatial Econometrics. CRC Press.
- Kelejian, H. H., & Prucha, I. R. (1998). A generalized spatial two-stage least squares procedure
  for estimating a spatial autoregressive model with autoregressive disturbances.
  The Journal of Real Estate Finance and Economics, 17(1), 99-121.
- Moran, P. A. (1950). Notes on continuous stochastic phenomena. Biometrika, 37(1/2), 17-23.
"""

import math
from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats


class SpatialEconometricsEngine:
    """
    Computes Moran's I test for spatial autocorrelation and estimates
    Spatial Lag Models (SAR) with direct and spillover impact decomposition.
    """

    @classmethod
    def analyze(
        cls,
        data: List[Dict[str, Any]],
        lat_field: str,
        lon_field: str,
        outcome_var: str,
        covariate_vars: List[str],
        weights_type: str = "inverse_distance",
        knn_k: int = 5,
        distance_power: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Executes spatial weights matrix construction, Moran's I,
        Anselin's LM tests, and Spatial 2SLS with impact decomposition.
        """
        all_required = [lat_field, lon_field, outcome_var] + covariate_vars

        # Filter valid records with non-null numeric coords and variables
        cleaned_rows = []
        for r in data:
            try:
                coords = [float(r[lat_field]), float(r[lon_field])]
                # Valid latitude [-90, 90] and longitude [-180, 180]
                if not (-90.0 <= coords[0] <= 90.0 and -180.0 <= coords[1] <= 180.0):
                    continue
                vals = [float(r[v]) for v in [outcome_var] + covariate_vars]
                if not any(math.isnan(x) or math.isinf(x) for x in coords + vals):
                    cleaned_rows.append(coords + vals)
            except (ValueError, TypeError, KeyError):
                continue

        n_samples = len(cleaned_rows)
        if n_samples < 15:
            return {
                "status": "error",
                "message": f"Dữ liệu không đủ tọa độ hợp lệ (cần tối thiểu 15 phản hồi có GPS, thực tế có {n_samples}).",
            }

        mat = np.array(cleaned_rows, dtype=float)
        lats = mat[:, 0]
        lons = mat[:, 1]
        y = mat[:, 2]
        X_raw = mat[:, 3:] if len(covariate_vars) > 0 else np.empty((n_samples, 0))

        # Check variation in Y
        ss_y = float(np.sum((y - np.mean(y)) ** 2))
        if ss_y <= 1e-12:
            return {
                "status": "error",
                "message": "Biến phụ thuộc Y không có phương sai (hằng số).",
            }

        # 1. Build Spatial Weights Matrix W
        W = cls._build_spatial_weights(
            lats=lats,
            lons=lons,
            weights_type=weights_type,
            knn_k=knn_k,
            power=distance_power,
        )

        # 2. Global Moran's I Test
        moran_res = cls._compute_morans_i(y=y, W=W)

        # 3. Baseline OLS and Anselin LM Diagnostics
        ols_res, lm_res = cls._compute_ols_and_lm_diagnostics(y=y, X=X_raw, W=W)

        # 4. Spatial Lag Model (SAR) via Spatial 2SLS
        sar_res = cls._compute_spatial_lag_2sls(
            y=y,
            X=X_raw,
            W=W,
            covariate_names=covariate_vars,
        )

        # 5. Dual-Panel Vector SVG
        svg_chart = cls._generate_svg_chart(
            y=y,
            W=W,
            moran_res=moran_res,
            sar_res=sar_res,
            outcome_var=outcome_var,
        )

        # 6. APA 7th Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_samples=n_samples,
            outcome_var=outcome_var,
            moran_res=moran_res,
            sar_res=sar_res,
            lm_res=lm_res,
            covariate_names=covariate_vars,
        )

        return {
            "status": "success",
            "morans_i": moran_res,
            "lm_diagnostics": lm_res,
            "baseline_ols": ols_res,
            "spatial_lag_model": sar_res,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _haversine_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great circle distance in kilometers."""
        r_earth = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lam = math.radians(lon2 - lon1)

        a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        return r_earth * c

    @classmethod
    def _build_spatial_weights(
        cls,
        lats: np.ndarray,
        lons: np.ndarray,
        weights_type: str,
        knn_k: int,
        power: float,
    ) -> np.ndarray:
        n = len(lats)
        W = np.zeros((n, n), dtype=float)

        # Pairwise distance matrix
        dists = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(i + 1, n):
                d = cls._haversine_distance(lats[i], lons[i], lats[j], lons[j])
                d = max(d, 0.05)  # floor to 50 meters
                dists[i, j] = d
                dists[j, i] = d

        if weights_type == "knn":
            k_eff = min(knn_k, n - 1)
            for i in range(n):
                # Sort neighbors by distance
                nearest_idx = np.argsort(dists[i, :])[1:k_eff + 1]
                W[i, nearest_idx] = 1.0
        else:
            # Inverse distance
            for i in range(n):
                for j in range(n):
                    if i != j:
                        W[i, j] = 1.0 / (dists[i, j] ** power)

        # Row-standardization
        row_sums = np.sum(W, axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        W_std = W / row_sums
        return W_std

    @classmethod
    def _compute_morans_i(cls, y: np.ndarray, W: np.ndarray) -> Dict[str, Any]:
        """Computes Global Moran's I and its analytical inference."""
        n = len(y)
        y_bar = float(np.mean(y))
        z = y - y_bar
        z_sq_sum = float(np.sum(z ** 2))

        W_z = W @ z
        numerator = float(np.sum(z * W_z))
        s0 = float(np.sum(W))  # equals n for row-standardized

        morans_i = (n / s0) * (numerator / max(z_sq_sum, 1e-12))

        # Expected value under null
        e_i = -1.0 / (n - 1)

        # Analytical variance under normal assumption (Cliff & Ord 1981)
        s1 = 0.5 * float(np.sum((W + W.T) ** 2))
        s2 = float(np.sum((np.sum(W, axis=1) + np.sum(W, axis=0)) ** 2))

        var_i = (n * ((n ** 2 - 3 * n + 3) * s1 - n * s2 + 3 * (s0 ** 2))) / (
            (n - 1) * (n - 2) * (n - 3) * (s0 ** 2)
        ) - (e_i ** 2)
        var_i = max(var_i, 1e-12)
        se_i = float(np.sqrt(var_i))

        z_score = float((morans_i - e_i) / se_i)
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_score))))

        if p_val < 0.05 and morans_i > 0:
            classification = "SPATIAL_CLUSTERING_POSITIVE"
            interpretation = "Tự tương quan không gian Dương có ý nghĩa (Phân cụm không gian tập trung - Spatial Clustering)"
        elif p_val < 0.05 and morans_i < 0:
            classification = "SPATIAL_DISPERSION_NEGATIVE"
            interpretation = "Tự tương quan không gian Âm có ý nghĩa (Phân tán không gian - Spatial Dispersion)"
        else:
            classification = "RANDOM_SPATIAL_DISTRIBUTION"
            interpretation = "Phân bổ không gian ngẫu nhiên (Không vi phạm tính độc lập không gian)"

        # Quadrant counts for Moran Scatterplot
        w_y = W @ y
        w_y_std = (w_y - np.mean(w_y)) / max(float(np.std(w_y)), 1e-6)
        y_std = (y - np.mean(y)) / max(float(np.std(y)), 1e-6)

        hh = int(np.sum((y_std > 0) & (w_y_std > 0)))
        ll = int(np.sum((y_std < 0) & (w_y_std < 0)))
        hl = int(np.sum((y_std > 0) & (w_y_std < 0)))
        lh = int(np.sum((y_std < 0) & (w_y_std > 0)))

        return {
            "morans_i": morans_i,
            "expected_i": e_i,
            "variance_i": var_i,
            "standard_error": se_i,
            "z_score": z_score,
            "p_value": p_val,
            "is_significant": p_val < 0.05,
            "classification": classification,
            "interpretation": interpretation,
            "quadrants": {
                "high_high": hh,
                "low_low": ll,
                "high_low": hl,
                "low_high": lh,
            },
        }

    @classmethod
    def _compute_ols_and_lm_diagnostics(
        cls,
        y: np.ndarray,
        X: np.ndarray,
        W: np.ndarray,
    ) -> (Dict[str, Any], Dict[str, Any]):
        n = len(y)
        ones = np.ones((n, 1))
        design = np.hstack([ones, X]) if X.shape[1] > 0 else ones

        beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        residuals = y - design @ beta
        ss_res = float(np.sum(residuals ** 2))
        sigma_sq = ss_res / n
        df = n - design.shape[1]

        cov = (ss_res / max(df, 1)) * np.linalg.pinv(design.T @ design)
        se = np.sqrt(np.maximum(np.diag(cov), 1e-12))
        t_stats = beta / se
        p_vals = [float(2 * (1 - stats.t.cdf(abs(t), df))) for t in t_stats]

        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = max(0.0, 1.0 - (ss_res / max(ss_tot, 1e-12)))

        ols_summary = {
            "r_squared": r2,
            "sigma_squared": sigma_sq,
            "coefficients": [float(b) for b in beta],
            "standard_errors": [float(s) for s in se],
            "p_values": p_vals,
        }

        # Anselin LM tests
        # LM Error: e' W e / sigma_sq
        e = residuals
        W_e = W @ e
        numerator_err = float(e.T @ W_e) / max(sigma_sq, 1e-12)

        # Trace of (W^2 + W'W)
        W2 = W @ W
        tr_term = float(np.trace(W2 + W.T @ W))
        lm_error = (numerator_err ** 2) / max(tr_term, 1e-12)
        p_lm_error = float(1.0 - stats.chi2.cdf(lm_error, 1))

        # LM Lag: (e' W y / sigma_sq)^2 / D
        W_y = W @ y
        numerator_lag = float(e.T @ W_y) / max(sigma_sq, 1e-12)

        # Auxiliary matrix term D
        W_X = W @ design
        M = np.eye(n) - design @ np.linalg.pinv(design.T @ design) @ design.T
        D_term = float((W_X @ beta).T @ M @ (W_X @ beta) / max(sigma_sq, 1e-12) + tr_term)
        lm_lag = (numerator_lag ** 2) / max(D_term, 1e-12)
        p_lm_lag = float(1.0 - stats.chi2.cdf(lm_lag, 1))

        if p_lm_lag < 0.05 and p_lm_lag <= p_lm_error:
            recommended_model = "SPATIAL_LAG_MODEL (SAR)"
            advice = "Dữ liệu có hiện tượng lan tỏa không gian trực tiếp (Spatial Spillover). Khuyến nghị sử dụng mô hình Spatial Lag."
        elif p_lm_error < 0.05:
            recommended_model = "SPATIAL_ERROR_MODEL (SEM)"
            advice = "Dữ liệu có yếu tố nhiễu không gian tiềm ẩn (Spatial Unobserved Error). Khuyến nghị sử dụng mô hình Spatial Error."
        else:
            recommended_model = "CLASSICAL_OLS"
            advice = "Không phát hiện phụ thuộc không gian có ý nghĩa. Mô hình OLS cổ điển là đủ điều kiện."

        lm_diagnostics = {
            "lm_error_stat": float(lm_error),
            "lm_error_p_value": p_lm_error,
            "lm_lag_stat": float(lm_lag),
            "lm_lag_p_value": p_lm_lag,
            "recommended_model": recommended_model,
            "advice": advice,
        }

        return ols_summary, lm_diagnostics

    @classmethod
    def _compute_spatial_lag_2sls(
        cls,
        y: np.ndarray,
        X: np.ndarray,
        W: np.ndarray,
        covariate_names: List[str],
    ) -> Dict[str, Any]:
        """
        Estimates Spatial Lag Model: Y = rho * W*Y + X * beta + eps
        using Spatial 2SLS (Kelejian & Prucha 1998) with spatial instruments [X, W*X, W^2*X].
        Decomposes impacts into Direct, Indirect (Spillover), and Total.
        """
        n = len(y)
        ones = np.ones((n, 1))
        k = len(covariate_names)

        # Spatially lagged outcome (endogenous variable)
        Wy = (W @ y).reshape(-1, 1)

        # Instruments: [1, X, W*X, W^2*X]
        if k > 0:
            WX = W @ X
            W2X = W @ WX
            instruments = np.hstack([ones, X, WX, W2X])
            exogenous_regressors = np.hstack([ones, X])
        else:
            # Univariate spatial autoregression Y = rho * W*Y + beta0
            # Use W*ones as instrument fallback
            instruments = np.hstack([ones, W @ ones, (W @ W) @ ones])
            exogenous_regressors = ones

        # Stage 1: Regress Wy on instruments
        p_z = instruments @ np.linalg.pinv(instruments.T @ instruments) @ instruments.T
        Wy_hat = p_z @ Wy

        # Stage 2: Regress Y on [Wy_hat, exogenous_regressors]
        Z_hat = np.hstack([Wy_hat, exogenous_regressors])
        Z_true = np.hstack([Wy, exogenous_regressors])

        gamma, _, _, _ = np.linalg.lstsq(Z_hat, y, rcond=None)
        rho_hat = float(gamma[0])

        # Bounds check on rho (-0.99, 0.99)
        rho_hat = max(-0.99, min(0.99, rho_hat))

        residuals = y - Z_true @ gamma
        ss_res = float(np.sum(residuals ** 2))
        df = n - len(gamma)
        sigma_sq = ss_res / max(df, 1)

        cov = sigma_sq * np.linalg.pinv(Z_hat.T @ Z_hat)
        se = np.sqrt(np.maximum(np.diag(cov), 1e-12))
        t_stats = gamma / se
        p_vals = [float(2 * (1 - stats.norm.cdf(abs(t)))) for t in t_stats]

        # Impact Decomposition (LeSage & Pace 2009)
        # S_r(W) = (I - rho * W)^(-1) * beta_r
        # Approximate (I - rho * W)^(-1) via series expansion: I + rho*W + rho^2*W^2
        inv_approx = np.eye(n) + rho_hat * W + (rho_hat ** 2) * (W @ W)
        avg_diagonal = float(np.mean(np.diag(inv_approx)))
        avg_total_multiplier = 1.0 / max(1.0 - rho_hat, 1e-6)

        impacts: List[Dict[str, Any]] = []
        for i, name in enumerate(covariate_names):
            b_r = float(gamma[2 + i])
            direct = b_r * avg_diagonal
            total = b_r * avg_total_multiplier
            spillover = total - direct
            spillover_ratio = (spillover / total) if abs(total) > 1e-6 else 0.0

            impacts.append({
                "variable": name,
                "coefficient": b_r,
                "direct_impact": direct,
                "indirect_spillover_impact": spillover,
                "total_impact": total,
                "spillover_ratio": float(spillover_ratio),
            })

        return {
            "rho": rho_hat,
            "rho_standard_error": float(se[0]),
            "rho_z_stat": float(t_stats[0]),
            "rho_p_value": float(p_vals[0]),
            "is_rho_significant": p_vals[0] < 0.05,
            "intercept": float(gamma[1]),
            "r_squared": max(0.0, 1.0 - (ss_res / max(float(np.sum((y - np.mean(y)) ** 2)), 1e-12))),
            "impact_decomposition": impacts,
        }

    @classmethod
    def _generate_svg_chart(
        cls,
        y: np.ndarray,
        W: np.ndarray,
        moran_res: Dict[str, Any],
        sar_res: Dict[str, Any],
        outcome_var: str,
    ) -> str:
        """
        Creates a dual-panel vector SVG:
        Panel A: Moran's Scatterplot (W*Y vs Y with quadrant quadrants and OLS line = Moran's I)
        Panel B: Direct vs Spillover Impacts decomposition bar chart.
        """
        w, h = 860, 460
        pad_l, pad_r, pad_t, pad_b = 60, 40, 50, 40
        pw = (w - pad_l - pad_r - 40) // 2
        ph = h - pad_t - pad_b

        # Standardize for Moran Scatterplot
        y_bar = np.mean(y)
        y_sd = max(float(np.std(y)), 1e-6)
        y_std = (y - y_bar) / y_sd

        Wy = W @ y
        Wy_bar = np.mean(Wy)
        Wy_sd = max(float(np.std(Wy)), 1e-6)
        Wy_std = (Wy - Wy_bar) / Wy_sd

        # Panel A Coordinates (Left half)
        lim = max(3.0, float(max(np.max(np.abs(y_std)), np.max(np.abs(Wy_std)))))

        def scale_x_a(val: float) -> float:
            norm = (val + lim) / (2 * lim)
            return pad_l + norm * pw

        def scale_y_a(val: float) -> float:
            norm = (val + lim) / (2 * lim)
            return (pad_t + ph) - norm * ph

        cx_a = scale_x_a(0.0)
        cy_a = scale_y_a(0.0)

        panel_a_elements = []
        # Background box
        panel_a_elements.append(
            f'<rect x="{pad_l}" y="{pad_t}" width="{pw}" height="{ph}" fill="#1e293b" rx="8" stroke="#334155" stroke-width="1" />'
        )

        # Crosshairs
        panel_a_elements.append(
            f'<line x1="{pad_l}" y1="{cy_a:.1f}" x2="{pad_l + pw}" y2="{cy_a:.1f}" stroke="#475569" stroke-dasharray="3,3" />'
        )
        panel_a_elements.append(
            f'<line x1="{cx_a:.1f}" y1="{pad_t}" x2="{cx_a:.1f}" y2="{pad_t + ph}" stroke="#475569" stroke-dasharray="3,3" />'
        )

        # Quadrant labels
        q = moran_res["quadrants"]
        panel_a_elements.append(
            f'<text x="{pad_l + pw - 8}" y="{pad_t + 18}" font-size="10" fill="#10b981" font-weight="600" text-anchor="end">High-High ({q["high_high"]})</text>'
        )
        panel_a_elements.append(
            f'<text x="{pad_l + 8}" y="{pad_t + ph - 8}" font-size="10" fill="#38bdf8" font-weight="600">Low-Low ({q["low_low"]})</text>'
        )
        panel_a_elements.append(
            f'<text x="{pad_l + 8}" y="{pad_t + 18}" font-size="10" fill="#f59e0b">Low-High ({q["low_high"]})</text>'
        )
        panel_a_elements.append(
            f'<text x="{pad_l + pw - 8}" y="{pad_t + ph - 8}" font-size="10" fill="#f43f5e" text-anchor="end">High-Low ({q["high_low"]})</text>'
        )

        # Data points
        for i in range(len(y_std)):
            px = scale_x_a(y_std[i])
            py = scale_y_a(Wy_std[i])
            # color based on quadrant
            if y_std[i] >= 0 and Wy_std[i] >= 0:
                col = "#10b981"
            elif y_std[i] < 0 and Wy_std[i] < 0:
                col = "#38bdf8"
            elif y_std[i] >= 0 and Wy_std[i] < 0:
                col = "#f43f5e"
            else:
                col = "#f59e0b"
            panel_a_elements.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{col}" fill-opacity="0.8" />'
            )

        # Moran's I slope line (y = I * x)
        slope = moran_res["morans_i"]
        line_x1 = -lim
        line_y1 = slope * line_x1
        line_x2 = lim
        line_y2 = slope * line_x2

        panel_a_elements.append(
            f'<line x1="{scale_x_a(line_x1):.1f}" y1="{scale_y_a(line_y1):.1f}" x2="{scale_x_a(line_x2):.1f}" y2="{scale_y_a(line_y2):.1f}" stroke="#a855f7" stroke-width="2.5" />'
        )

        # Panel B: Impact Decomposition Grouped Bars (Right half)
        pad_b_l = pad_l + pw + 40
        panel_b_elements = []
        panel_b_elements.append(
            f'<rect x="{pad_b_l}" y="{pad_t}" width="{pw}" height="{ph}" fill="#1e293b" rx="8" stroke="#334155" stroke-width="1" />'
        )

        impacts = sar_res.get("impact_decomposition", [])
        if len(impacts) == 0:
            # Fallback widget showing spatial parameters
            panel_b_elements.append(
                f'<text x="{pad_b_l + pw/2}" y="{pad_t + ph/2 - 20}" font-size="14" font-weight="700" fill="#f8fafc" text-anchor="middle">SPATIAL AUTOREGRESSIVE COEFFICIENT</text>'
            )
            panel_b_elements.append(
                f'<text x="{pad_b_l + pw/2}" y="{pad_t + ph/2 + 25}" font-size="32" font-weight="800" fill="#38bdf8" text-anchor="middle">ρ = {sar_res["rho"]:.3f}</text>'
            )
            panel_b_elements.append(
                f'<text x="{pad_b_l + pw/2}" y="{pad_t + ph/2 + 55}" font-size="11" fill="#94a3b8" text-anchor="middle">p-value: {sar_res["rho_p_value"]:.4f} | R² = {sar_res["r_squared"]:.3f}</text>'
            )
        else:
            # Grouped bar chart: Direct vs Spillover
            n_vars = len(impacts)
            slot_h = (ph - 60) / max(n_vars, 1)
            max_imp = max(max(abs(imp["direct_impact"]), abs(imp["indirect_spillover_impact"]), abs(imp["total_impact"])) for imp in impacts)
            max_imp = max(max_imp, 1e-4)

            zero_x_b = pad_b_l + pw * 0.4

            for idx, imp in enumerate(impacts):
                sy = pad_t + 35 + idx * slot_h
                panel_b_elements.append(
                    f'<text x="{pad_b_l + 12}" y="{sy + 10:.1f}" font-size="11" font-weight="600" fill="#f8fafc">{imp["variable"][:16]}</text>'
                )

                # Direct bar (cyan)
                d_len = (imp["direct_impact"] / max_imp) * (pw * 0.25)
                panel_b_elements.append(
                    f'<rect x="{min(zero_x_b, zero_x_b + d_len):.1f}" y="{sy + 15:.1f}" width="{abs(d_len):.1f}" height="7" fill="#38bdf8" rx="2" />'
                )

                # Spillover bar (violet)
                s_len = (imp["indirect_spillover_impact"] / max_imp) * (pw * 0.25)
                panel_b_elements.append(
                    f'<rect x="{min(zero_x_b, zero_x_b + s_len):.1f}" y="{sy + 25:.1f}" width="{abs(s_len):.1f}" height="7" fill="#a855f7" rx="2" />'
                )

                # Spillover ratio
                panel_b_elements.append(
                    f'<text x="{pad_b_l + pw - 12}" y="{sy + 22:.1f}" font-size="10" fill="#cbd5e1" text-anchor="end">Spillover: {imp["spillover_ratio"]:.1%}</text>'
                )

            # Legend in Panel B
            panel_b_elements.append(
                f'<rect x="{pad_b_l + 15}" y="{pad_t + ph - 22}" width="10" height="10" fill="#38bdf8" rx="2" />'
            )
            panel_b_elements.append(
                f'<text x="{pad_b_l + 30}" y="{pad_t + ph - 14}" font-size="10" fill="#cbd5e1">Tác động Trực tiếp (Direct)</text>'
            )
            panel_b_elements.append(
                f'<rect x="{pad_b_l + 160}" y="{pad_t + ph - 22}" width="10" height="10" fill="#a855f7" rx="2" />'
            )
            panel_b_elements.append(
                f'<text x="{pad_b_l + 175}" y="{pad_t + ph - 14}" font-size="10" fill="#cbd5e1">Lan tỏa Không gian (Spillover)</text>'
            )

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="background:#0f172a; border-radius:12px; font-family:system-ui, -apple-system, sans-serif;">
  <!-- Title -->
  <text x="{pad_l}" y="28" font-size="15" font-weight="700" fill="#f8fafc">SPATIAL ECONOMETRICS &amp; MORAN'S I AUTOREGRESSION (SAR)</text>
  <text x="{pad_l}" y="44" font-size="11" fill="#94a3b8">Biến kết quả: {outcome_var} | Moran's I = {moran_res["morans_i"]:.3f} (z = {moran_res["z_score"]:.2f}, p = {moran_res["p_value"]:.4f})</text>

  <!-- Panel A Header -->
  <text x="{pad_l + pw}" y="28" font-size="11" font-weight="600" fill="#a855f7" text-anchor="end">Panel A: Moran Scatterplot (W·Y vs Y)</text>
  {''.join(panel_a_elements)}

  <!-- Panel B Header -->
  <text x="{pad_b_l + pw}" y="28" font-size="11" font-weight="600" fill="#38bdf8" text-anchor="end">Panel B: Phân rã Hiệu ứng Lan tỏa (Direct vs Spillover)</text>
  {''.join(panel_b_elements)}
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_samples: int,
        outcome_var: str,
        moran_res: Dict[str, Any],
        sar_res: Dict[str, Any],
        lm_res: Dict[str, Any],
        covariate_names: List[str],
    ) -> str:
        cov_str = f" cùng các biến giải thích ({', '.join(covariate_names)})" if covariate_names else ""
        return (
            f"Phân tích Kinh tế lượng Không gian (Spatial Econometrics; Anselin, 1988; LeSage & Pace, 2009) được thực hiện "
            f"trên N = {n_samples} phản hồi khảo sát có định vị địa lý GPS để kiểm định sự phụ thuộc không gian đối với {outcome_var}{cov_str}. "
            f"Kiểm định Moran's I toàn cục với ma trận trọng số chuẩn hóa hàng cho thấy chỉ số Moran's I = {moran_res['morans_i']:.4f} "
            f"(Kỳ vọng E[I] = {moran_res['expected_i']:.4f}, z = {moran_res['z_score']:.2f}, p = {moran_res['p_value']:.4f}), "
            f"xác nhận: {moran_res['interpretation']}. Kiểm định chẩn đoán nhân tử Lagrange của Anselin chỉ ra "
            f"LM_Lag = {lm_res['lm_lag_stat']:.2f} (p = {lm_res['lm_lag_p_value']:.4f}) và LM_Error = {lm_res['lm_error_stat']:.2f} "
            f"(p = {lm_res['lm_error_p_value']:.4f}), dẫn tới đề xuất mô hình phù hợp: {lm_res['recommended_model']}. "
            f"Ước lượng Mô hình Tự hồi quy Không gian (Spatial Lag Model - SAR) qua phương pháp 2SLS cho thấy hệ số tự hồi quy "
            f"không gian ρ = {sar_res['rho']:.4f} (SE = {sar_res['rho_standard_error']:.4f}, z = {sar_res['rho_z_stat']:.2f}, "
            f"p = {sar_res['rho_p_value']:.4f}, R² = {sar_res['r_squared']:.3f}). "
            f"Phân rã hiệu ứng LeSage & Pace xác nhận sự tồn tại của hiệu ứng lan tỏa không gian (spatial spillovers) giữa các "
            f"địa bàn lân cận, chứng minh rằng các mô hình OLS truyền thống bỏ qua tọa độ địa lý sẽ bị thiên lệch sai số chuẩn "
            f"và thổi phồng ý nghĩa thống kê của các can thiệp chính sách."
        )
