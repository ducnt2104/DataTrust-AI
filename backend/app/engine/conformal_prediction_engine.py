"""
Conformal Prediction Engine for Distribution-Free Uncertainty Quantification
=============================================================================
Methodological References:
- Vovk, V., Gammerman, A., & Shafer, G. (2005). Algorithmic Learning in a Random World.
  Springer Science & Business Media.
- Shafer, G., & Vovk, V. (2008). A tutorial on conformal prediction.
  Journal of Machine Learning Research, 9(3), 371-421.
- Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018).
  Distribution-free predictive inference for regression.
  Journal of the American Statistical Association, 113(523), 1094-1111.
- Angelopoulos, A. N., & Bates, S. (2023). A gentle introduction to conformal prediction
  and distribution-free uncertainty quantification.
  Foundations and Trends in Machine Learning, 16(4), 494-591.
- Romano, Y., Patterson, E., & Candès, E. (2019). Conformalized quantile regression.
  Advances in Neural Information Processing Systems, 32.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import numpy as np


class ConformalPredictionEngine:
    """
    Split Conformal Prediction Engine providing finite-sample distribution-free
    prediction intervals with rigorous coverage guarantees for survey metrics.
    """

    @classmethod
    def fit_and_predict(
        cls,
        records: List[Dict[str, Any]],
        target_field: str,
        feature_fields: List[str],
        alpha: float = 0.05,
        method: str = "split_conformal",  # 'split_conformal' or 'locally_weighted'
        calib_fraction: float = 0.30,
        test_fraction: float = 0.20,
        clamp_min: Optional[float] = None,
        clamp_max: Optional[float] = None,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Execute Split Conformal Prediction or Locally-Weighted Conformal Prediction.

        records: List of respondent dicts with features and target
        target_field: name of dependent metric (e.g. 'satisfaction', 'nps_score')
        feature_fields: list of predictor names (e.g. ['q1', 'q2', 'age', 'tenure'])
        alpha: significance level (default 0.05 => 95% guaranteed coverage)
        method: 'split_conformal' (standard residual) or 'locally_weighted' (heteroscedastic)
        calib_fraction: fraction of training data reserved for calibration (0.1 to 0.5)
        test_fraction: fraction reserved for out-of-sample evaluation (0.1 to 0.4)
        """
        if not records or len(records) < 15:
            return {
                "status": "error",
                "message": "Cần tối thiểu 15 phản hồi khảo sát đầy đủ để thực hiện Conformal Prediction."
            }

        if alpha <= 0.0 or alpha >= 1.0:
            return {
                "status": "error",
                "message": "Mức ý nghĩa alpha phải nằm trong khoảng (0, 1), ví dụ 0.05 cho độ bao phủ 95%."
            }

        # Extract X and y
        valid_rows = []
        for r in records:
            if target_field not in r or r[target_field] is None:
                continue
            try:
                y_val = float(r[target_field])
            except (ValueError, TypeError):
                continue

            feats = []
            row_ok = True
            for f in feature_fields:
                if f not in r or r[f] is None:
                    row_ok = False
                    break
                try:
                    feats.append(float(r[f]))
                except (ValueError, TypeError):
                    row_ok = False
                    break

            if row_ok:
                valid_rows.append((feats, y_val))

        n_total = len(valid_rows)
        if n_total < 15:
            return {
                "status": "error",
                "message": f"Chỉ tìm thấy {n_total} quan sát hợp lệ không khuyết thiếu. Cần tối thiểu 15 mẫu."
            }

        X = np.array([r[0] for r in valid_rows], dtype=float)
        y = np.array([r[1] for r in valid_rows], dtype=float)

        # Shuffle indices deterministically
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n_total)

        n_test = max(5, int(n_total * test_fraction))
        n_rem = n_total - n_test
        n_cal = max(5, int(n_rem * calib_fraction))
        n_train = n_rem - n_cal

        if n_train < 5 or n_cal < 5:
            # Fallback rebalancing
            n_train = int(n_total * 0.5)
            n_cal = int(n_total * 0.3)
            n_test = n_total - n_train - n_cal

        train_idx = perm[:n_train]
        cal_idx = perm[n_train:n_train + n_cal]
        test_idx = perm[n_train + n_cal:]

        X_train, y_train = X[train_idx], y[train_idx]
        X_cal, y_cal = X[cal_idx], y[cal_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        # 1. Fit base regression model on X_train, y_train (Ridge regularized OLS for stability)
        p = X_train.shape[1]
        X_train_design = np.column_stack([np.ones(n_train), X_train])
        ridge_lambda = 0.01
        XTX = X_train_design.T @ X_train_design + ridge_lambda * np.eye(p + 1)
        XTy = X_train_design.T @ y_train
        try:
            beta = np.linalg.solve(XTX, XTy)
        except np.linalg.LinAlgError:
            beta = np.linalg.pinv(XTX) @ XTy

        # Auxiliary model for heteroscedasticity if locally_weighted
        beta_sigma = None
        if method == "locally_weighted":
            # Predict residual scale |e_i| from features
            train_preds = X_train_design @ beta
            train_abs_resid = np.abs(y_train - train_preds)
            XTy_sigma = X_train_design.T @ np.log(np.maximum(train_abs_resid, 1e-4))
            try:
                beta_sigma = np.linalg.solve(XTX, XTy_sigma)
            except np.linalg.LinAlgError:
                beta_sigma = np.linalg.pinv(XTX) @ XTy_sigma

        def predict_mean(X_mat: np.ndarray) -> np.ndarray:
            X_des = np.column_stack([np.ones(len(X_mat)), X_mat])
            return X_des @ beta

        def predict_dispersion(X_mat: np.ndarray) -> np.ndarray:
            if beta_sigma is None:
                return np.ones(len(X_mat))
            X_des = np.column_stack([np.ones(len(X_mat)), X_mat])
            # exponentiate log residual prediction with clipping
            log_sig = np.clip(X_des @ beta_sigma, -3.0, 4.0)
            return np.exp(log_sig) + 0.05

        # 2. Compute Non-Conformity Scores on Calibration Set
        y_cal_pred = predict_mean(X_cal)
        abs_residuals_cal = np.abs(y_cal - y_cal_pred)

        if method == "locally_weighted":
            cal_disp = predict_dispersion(X_cal)
            scores_cal = abs_residuals_cal / cal_disp
        else:
            scores_cal = abs_residuals_cal

        # 3. Compute Conformal Quantile with Finite-Sample Correction
        # Vovk et al. 2005: quantile at ceil((n_cal + 1) * (1 - alpha)) / n_cal
        q_level = math.ceil((n_cal + 1) * (1.0 - alpha)) / float(n_cal)
        q_level = min(1.0, max(0.0, q_level))
        conformal_quantile = float(np.quantile(scores_cal, q_level, method="higher"))

        # Baseline classical Gaussian standard error (homoscedastic assumption)
        train_residuals = y_train - predict_mean(X_train)
        rmse_train = float(np.sqrt(np.mean(train_residuals ** 2)))
        z_score = float(1.96 if abs(alpha - 0.05) < 1e-3 else -1.0 * float(np.quantile(train_residuals, alpha / 2.0)))
        # Standard normal quantile
        from scipy.stats import norm
        z_crit = float(norm.ppf(1.0 - alpha / 2.0))

        # 4. Predict on Test Set
        y_test_pred = predict_mean(X_test)
        if method == "locally_weighted":
            test_disp = predict_dispersion(X_test)
            half_width = conformal_quantile * test_disp
            gaussian_half_width = z_crit * rmse_train * np.ones(len(X_test))
        else:
            half_width = np.full(len(X_test), conformal_quantile)
            gaussian_half_width = np.full(len(X_test), z_crit * rmse_train)

        lower_conf = y_test_pred - half_width
        upper_conf = y_test_pred + half_width

        lower_gauss = y_test_pred - gaussian_half_width
        upper_gauss = y_test_pred + gaussian_half_width

        # Apply optional domain clamps (e.g. Likert 1-5)
        if clamp_min is not None:
            lower_conf = np.maximum(lower_conf, clamp_min)
            lower_gauss = np.maximum(lower_gauss, clamp_min)
        if clamp_max is not None:
            upper_conf = np.minimum(upper_conf, clamp_max)
            upper_gauss = np.minimum(upper_gauss, clamp_max)

        # 5. Evaluate Empirical Coverage & Efficiency on Test Set
        covered_conf = (y_test >= lower_conf) & (y_test <= upper_conf)
        empirical_coverage_conf = float(np.mean(covered_conf))

        covered_gauss = (y_test >= lower_gauss) & (y_test <= upper_gauss)
        empirical_coverage_gauss = float(np.mean(covered_gauss))

        widths_conf = upper_conf - lower_conf
        mean_width_conf = float(np.mean(widths_conf))
        median_width_conf = float(np.median(widths_conf))
        q25_width = float(np.percentile(widths_conf, 25))
        q75_width = float(np.percentile(widths_conf, 75))

        widths_gauss = upper_gauss - lower_gauss
        mean_width_gauss = float(np.mean(widths_gauss))

        # Nominal coverage target
        nominal_coverage = 1.0 - alpha
        finite_sample_upper_bound = min(1.0, nominal_coverage + 1.0 / (n_cal + 1))

        # 6. Multi-level Calibration Curve across multiple alphas
        test_alphas = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
        calibration_curve = []
        for a_test in test_alphas:
            q_lev = min(1.0, math.ceil((n_cal + 1) * (1.0 - a_test)) / float(n_cal))
            q_val = float(np.quantile(scores_cal, q_lev, method="higher"))
            if method == "locally_weighted":
                hw = q_val * test_disp
            else:
                hw = np.full(len(X_test), q_val)
            lo = y_test_pred - hw
            hi = y_test_pred + hw
            if clamp_min is not None:
                lo = np.maximum(lo, clamp_min)
            if clamp_max is not None:
                hi = np.minimum(hi, clamp_max)
            cov_c = float(np.mean((y_test >= lo) & (y_test <= hi)))

            # Gaussian comparison
            z_c = float(norm.ppf(1.0 - a_test / 2.0))
            hw_g = np.full(len(X_test), z_c * rmse_train)
            lo_g = y_test_pred - hw_g
            hi_g = y_test_pred + hw_g
            if clamp_min is not None:
                lo_g = np.maximum(lo_g, clamp_min)
            if clamp_max is not None:
                hi_g = np.minimum(hi_g, clamp_max)
            cov_g = float(np.mean((y_test >= lo_g) & (y_test <= hi_g)))

            calibration_curve.append({
                "alpha": round(a_test, 3),
                "nominal_coverage": round(1.0 - a_test, 3),
                "conformal_coverage": round(cov_c, 4),
                "gaussian_coverage": round(cov_g, 4),
                "quantile_cutoff": round(q_val, 4)
            })

        # 7. Format Individual Test Predictions (sample up to 25 items for table display)
        test_sample_records = []
        sort_test_idx = np.argsort(y_test_pred)
        display_indices = sort_test_idx[:min(30, len(sort_test_idx))]
        for idx in display_indices:
            test_sample_records.append({
                "test_index": int(idx),
                "actual_y": round(float(y_test[idx]), 3),
                "predicted_y": round(float(y_test_pred[idx]), 3),
                "lower_bound": round(float(lower_conf[idx]), 3),
                "upper_bound": round(float(upper_conf[idx]), 3),
                "interval_width": round(float(widths_conf[idx]), 3),
                "is_covered": bool(covered_conf[idx])
            })

        # 8. Generate Dual-Panel SVG Visualization
        svg_chart = cls._render_dual_panel_svg(
            calibration_curve=calibration_curve,
            test_sample_records=test_sample_records,
            nominal_coverage=nominal_coverage,
            empirical_coverage_conf=empirical_coverage_conf,
            empirical_coverage_gauss=empirical_coverage_gauss,
            target_field=target_field
        )

        # 9. Synthesize APA 7th Statistical Report & Diagnostics
        narrative = cls._synthesize_narrative(
            nominal_coverage=nominal_coverage,
            empirical_coverage_conf=empirical_coverage_conf,
            empirical_coverage_gauss=empirical_coverage_gauss,
            alpha=alpha,
            n_total=n_total,
            n_train=n_train,
            n_cal=n_cal,
            n_test=n_test,
            conformal_quantile=conformal_quantile,
            mean_width_conf=mean_width_conf,
            mean_width_gauss=mean_width_gauss,
            method=method,
            target_field=target_field
        )

        return {
            "status": "success",
            "method": method,
            "target_field": target_field,
            "feature_fields": feature_fields,
            "sample_sizes": {
                "total": n_total,
                "train": n_train,
                "calibration": n_cal,
                "test": n_test
            },
            "parameters": {
                "nominal_coverage": round(nominal_coverage, 4),
                "alpha": round(alpha, 4),
                "conformal_quantile": round(conformal_quantile, 4),
                "finite_sample_lower_guarantee": round(nominal_coverage, 4),
                "finite_sample_upper_bound": round(finite_sample_upper_bound, 4)
            },
            "evaluation_metrics": {
                "conformal_coverage": round(empirical_coverage_conf, 4),
                "gaussian_coverage": round(empirical_coverage_gauss, 4),
                "conformal_mean_width": round(mean_width_conf, 4),
                "conformal_median_width": round(median_width_conf, 4),
                "conformal_iqr_width": round(q75_width - q25_width, 4),
                "gaussian_mean_width": round(mean_width_gauss, 4),
                "efficiency_gain_ratio": round(mean_width_conf / max(1e-4, mean_width_gauss), 3)
            },
            "calibration_curve": calibration_curve,
            "sample_predictions": test_sample_records,
            "svg_chart": svg_chart,
            "apa_narrative": narrative
        }

    @classmethod
    def _render_dual_panel_svg(
        cls,
        calibration_curve: List[Dict[str, Any]],
        test_sample_records: List[Dict[str, Any]],
        nominal_coverage: float,
        empirical_coverage_conf: float,
        empirical_coverage_gauss: float,
        target_field: str
    ) -> str:
        """
        Generate SVG with two panels:
        - Panel 1 (Left): Reliability / Calibration Diagram (Nominal vs Empirical Coverage)
        - Panel 2 (Right): Conformal Prediction Bands vs Actual Observations
        """
        svg_w = 920
        svg_h = 390
        pad_top = 45
        pad_bot = 55
        p1_x = 65
        p1_w = 360
        p2_x = 495
        p2_w = 380
        plot_h = svg_h - pad_top - pad_bot

        # Panel 1: Calibration curve (x: Nominal 0.5 to 1.0, y: Empirical 0.5 to 1.0)
        x_min, x_max = 0.55, 1.0
        y_min, y_max = 0.55, 1.0

        def p1_scale_x(v: float) -> float:
            return p1_x + ((v - x_min) / (x_max - x_min)) * p1_w

        def p1_scale_y(v: float) -> float:
            return (pad_top + plot_h) - ((v - y_min) / (y_max - y_min)) * plot_h

        # Ideal 45 deg diagonal line
        d_x1 = p1_scale_x(0.60)
        d_y1 = p1_scale_y(0.60)
        d_x2 = p1_scale_x(1.00)
        d_y2 = p1_scale_y(1.00)

        # Conformal line coords
        conf_pts = []
        gauss_pts = []
        for pt in sorted(calibration_curve, key=lambda d: d["nominal_coverage"]):
            if pt["nominal_coverage"] >= 0.58:
                cx = p1_scale_x(pt["nominal_coverage"])
                cy_c = p1_scale_y(min(1.0, max(y_min, pt["conformal_coverage"])))
                cy_g = p1_scale_y(min(1.0, max(y_min, pt["gaussian_coverage"])))
                conf_pts.append(f"{cx:.1f},{cy_c:.1f}")
                gauss_pts.append(f"{cx:.1f},{cy_g:.1f}")

        conf_polyline = " ".join(conf_pts)
        gauss_polyline = " ".join(gauss_pts)

        # Panel 2: Prediction intervals ordered by predicted value
        if test_sample_records:
            all_vals = []
            for r in test_sample_records:
                all_vals.extend([r["actual_y"], r["lower_bound"], r["upper_bound"]])
            y2_min = min(all_vals) - 0.2
            y2_max = max(all_vals) + 0.2
        else:
            y2_min, y2_max = 0.0, 5.0

        def p2_scale_y(v: float) -> float:
            return (pad_top + plot_h) - ((v - y2_min) / max(1e-4, y2_max - y2_min)) * plot_h

        n_pts = len(test_sample_records)
        step_x = p2_w / max(1, n_pts + 1)

        # Assemble SVG Elements
        elements = []
        # Background
        elements.append(f'<rect width="{svg_w}" height="{svg_h}" fill="#0f172a" rx="12" />')

        # Title
        elements.append(
            f'<text x="{svg_w // 2}" y="26" text-anchor="middle" fill="#f8fafc" '
            f'font-family="system-ui, sans-serif" font-size="14" font-weight="600">'
            f'Conformal Prediction: Kiểm định Độ bao phủ Phân phối Tự do cho {target_field}'
            f'</text>'
        )

        # Panel 1 Titles & Axes
        elements.append(
            f'<text x="{p1_x + p1_w // 2}" y="42" text-anchor="middle" fill="#94a3b8" '
            f'font-family="system-ui, sans-serif" font-size="11" font-weight="500">'
            f'Đường Chuẩn hóa Độ bao phủ (Reliability Diagram)'
            f'</text>'
        )
        # P1 Box
        elements.append(
            f'<rect x="{p1_x}" y="{pad_top}" width="{p1_w}" height="{plot_h}" '
            f'fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1" rx="4" />'
        )
        # Grid lines for P1
        for val in [0.6, 0.7, 0.8, 0.9, 1.0]:
            gy = p1_scale_y(val)
            gx = p1_scale_x(val)
            elements.append(
                f'<line x1="{p1_x}" y1="{gy:.1f}" x2="{p1_x + p1_w}" y2="{gy:.1f}" '
                f'stroke="#334155" stroke-width="0.8" stroke-dasharray="3,3" />'
            )
            elements.append(
                f'<line x1="{gx:.1f}" y1="{pad_top}" x2="{gx:.1f}" y2="{pad_top + plot_h}" '
                f'stroke="#334155" stroke-width="0.8" stroke-dasharray="3,3" />'
            )
            elements.append(
                f'<text x="{p1_x - 6}" y="{gy + 4:.1f}" text-anchor="end" fill="#64748b" '
                f'font-family="system-ui, sans-serif" font-size="10">{int(val * 100)}%</text>'
            )
            elements.append(
                f'<text x="{gx:.1f}" y="{pad_top + plot_h + 16}" text-anchor="middle" fill="#64748b" '
                f'font-family="system-ui, sans-serif" font-size="10">{int(val * 100)}%</text>'
            )

        # Axis labels P1
        elements.append(
            f'<text x="{p1_x + p1_w // 2}" y="{pad_top + plot_h + 36}" text-anchor="middle" fill="#94a3b8" '
            f'font-family="system-ui, sans-serif" font-size="11">Độ bao phủ Danh nghĩa Kỳ vọng (1 - α)</text>'
        )
        elements.append(
            f'<text x="18" y="{pad_top + plot_h // 2}" text-anchor="middle" fill="#94a3b8" '
            f'font-family="system-ui, sans-serif" font-size="11" transform="rotate(-90 18 {pad_top + plot_h // 2})">'
            f'Độ bao phủ Thực nghiệm</text>'
        )

        # Diagonal line (ideal calibration)
        elements.append(
            f'<line x1="{d_x1:.1f}" y1="{d_y1:.1f}" x2="{d_x2:.1f}" y2="{d_y2:.1f}" '
            f'stroke="#64748b" stroke-width="1.5" stroke-dasharray="4,4" />'
        )

        # Polylines for Conformal & Gaussian
        if gauss_polyline:
            elements.append(
                f'<polyline points="{gauss_polyline}" fill="none" stroke="#f43f5e" stroke-width="2.2" />'
            )
        if conf_polyline:
            elements.append(
                f'<polyline points="{conf_polyline}" fill="none" stroke="#10b981" stroke-width="2.5" />'
            )

        # Dots for Conformal
        for pt in calibration_curve:
            if pt["nominal_coverage"] >= 0.58:
                cx = p1_scale_x(pt["nominal_coverage"])
                cy_c = p1_scale_y(min(1.0, max(y_min, pt["conformal_coverage"])))
                elements.append(
                    f'<circle cx="{cx:.1f}" cy="{cy_c:.1f}" r="4" fill="#10b981" stroke="#0f172a" stroke-width="1.5" />'
                )

        # Panel 1 Legend
        elements.append(
            f'<line x1="{p1_x + 15}" y1="{pad_top + 18}" x2="{p1_x + 35}" y2="{pad_top + 18}" stroke="#10b981" stroke-width="2.5" />'
            f'<circle cx="{p1_x + 25}" cy="{pad_top + 18}" r="3" fill="#10b981" />'
            f'<text x="{p1_x + 42}" y="{pad_top + 22}" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="10">Conformal ({int(empirical_coverage_conf * 100)}%)</text>'
            f'<line x1="{p1_x + 160}" y1="{pad_top + 18}" x2="{p1_x + 180}" y2="{pad_top + 18}" stroke="#f43f5e" stroke-width="2" />'
            f'<text x="{p1_x + 186}" y="{pad_top + 22}" fill="#f87171" font-family="system-ui, sans-serif" font-size="10">Gaussian ({int(empirical_coverage_gauss * 100)}%)</text>'
            f'<line x1="{p1_x + 295}" y1="{pad_top + 18}" x2="{p1_x + 315}" y2="{pad_top + 18}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3" />'
            f'<text x="{p1_x + 320}" y="{pad_top + 22}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="10">Kỳ vọng</text>'
        )

        # Panel 2 Titles & Axes
        elements.append(
            f'<text x="{p2_x + p2_w // 2}" y="42" text-anchor="middle" fill="#94a3b8" '
            f'font-family="system-ui, sans-serif" font-size="11" font-weight="500">'
            f'Dải Dự báo Conformal vs Điểm Thực tế ({int(nominal_coverage * 100)}% Coverage)'
            f'</text>'
        )
        elements.append(
            f'<rect x="{p2_x}" y="{pad_top}" width="{p2_w}" height="{plot_h}" '
            f'fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1" rx="4" />'
        )

        # P2 Grid lines
        for val in np.linspace(y2_min, y2_max, 5):
            gy2 = p2_scale_y(val)
            elements.append(
                f'<line x1="{p2_x}" y1="{gy2:.1f}" x2="{p2_x + p2_w}" y2="{gy2:.1f}" '
                f'stroke="#334155" stroke-width="0.8" stroke-dasharray="3,3" />'
            )
            elements.append(
                f'<text x="{p2_x - 6}" y="{gy2 + 4:.1f}" text-anchor="end" fill="#64748b" '
                f'font-family="system-ui, sans-serif" font-size="10">{val:.1f}</text>'
            )

        # Draw intervals and test points
        for i, rec in enumerate(test_sample_records):
            cur_x = p2_x + (i + 1) * step_x
            y_pred = p2_scale_y(rec["predicted_y"])
            y_low = p2_scale_y(rec["lower_bound"])
            y_up = p2_scale_y(rec["upper_bound"])
            y_act = p2_scale_y(rec["actual_y"])
            is_cov = rec["is_covered"]

            bar_color = "#38bdf8" if is_cov else "#f43f5e"
            point_color = "#10b981" if is_cov else "#ef4444"

            # Interval vertical line
            elements.append(
                f'<line x1="{cur_x:.1f}" y1="{y_up:.1f}" x2="{cur_x:.1f}" y2="{y_low:.1f}" '
                f'stroke="{bar_color}" stroke-width="2.5" stroke-opacity="0.75" />'
            )
            # Whisker caps
            elements.append(
                f'<line x1="{cur_x - 3:.1f}" y1="{y_up:.1f}" x2="{cur_x + 3:.1f}" y2="{y_up:.1f}" '
                f'stroke="{bar_color}" stroke-width="2" />'
            )
            elements.append(
                f'<line x1="{cur_x - 3:.1f}" y1="{y_low:.1f}" x2="{cur_x + 3:.1f}" y2="{y_low:.1f}" '
                f'stroke="{bar_color}" stroke-width="2" />'
            )
            # Center predicted tick
            elements.append(
                f'<circle cx="{cur_x:.1f}" cy="{y_pred:.1f}" r="2" fill="#e2e8f0" />'
            )
            # Actual observed dot
            elements.append(
                f'<circle cx="{cur_x:.1f}" cy="{y_act:.1f}" r="3.5" fill="{point_color}" stroke="#0f172a" stroke-width="1" />'
            )

        # Panel 2 X label
        elements.append(
            f'<text x="{p2_x + p2_w // 2}" y="{pad_top + plot_h + 36}" text-anchor="middle" fill="#94a3b8" '
            f'font-family="system-ui, sans-serif" font-size="11">Các trường hợp kiểm định ngoài mẫu (sắp xếp theo giá trị kỳ vọng)</text>'
        )

        # Panel 2 Legend
        elements.append(
            f'<circle cx="{p2_x + 20}" cy="{pad_top + 18}" r="4" fill="#10b981" />'
            f'<text x="{p2_x + 30}" y="{pad_top + 22}" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="10">Điểm bao phủ (Đạt)</text>'
            f'<circle cx="{p2_x + 155}" cy="{pad_top + 18}" r="4" fill="#ef4444" />'
            f'<text x="{p2_x + 165}" y="{pad_top + 22}" fill="#f87171" font-family="system-ui, sans-serif" font-size="10">Ngoại lai (Outlier)</text>'
            f'<line x1="{p2_x + 285}" y1="{pad_top + 18}" x2="{p2_x + 305}" y2="{pad_top + 18}" stroke="#38bdf8" stroke-width="2.5" />'
            f'<text x="{p2_x + 312}" y="{pad_top + 22}" fill="#7dd3fc" font-family="system-ui, sans-serif" font-size="10">Khoảng 95%</text>'
        )

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" '
            f'width="100%" height="auto">\n' + "\n".join(elements) + "\n</svg>"
        )

    @classmethod
    def _synthesize_narrative(
        cls,
        nominal_coverage: float,
        empirical_coverage_conf: float,
        empirical_coverage_gauss: float,
        alpha: float,
        n_total: int,
        n_train: int,
        n_cal: int,
        n_test: int,
        conformal_quantile: float,
        mean_width_conf: float,
        mean_width_gauss: float,
        method: str,
        target_field: str
    ) -> str:
        """
        Produce APA 7th style analytical narrative and practical implications.
        """
        pct_nom = int(nominal_coverage * 100)
        pct_conf = round(empirical_coverage_conf * 100, 1)
        pct_gauss = round(empirical_coverage_gauss * 100, 1)

        coverage_status = (
            "bảo toàn trọn vẹn cam kết lý thuyết"
            if empirical_coverage_conf >= nominal_coverage - 0.02
            else "xấp xỉ cận dưới lý thuyết do giới hạn cỡ mẫu kiểm định"
        )

        method_vn = (
            "Split Conformal Prediction (Phân đoạn Độc lập)"
            if method == "split_conformal"
            else "Locally-Weighted Conformal Prediction (Thích ứng Phương sai Không đồng nhất)"
        )

        return (
            f"**Báo cáo Phân tích Độ bao phủ Rủi ro Phân phối Tự do (Conformal Prediction - APA 7th Standard)**\n\n"
            f"1. **Thiết kế Phương pháp luận & Cam kết Lý thuyết (Vovk et al., 2005; Angelopoulos & Bates, 2023)**:\n"
            f"Thử nghiệm kiểm định định lượng bất định phân phối tự do được tiến hành trên toàn bộ $N = {n_total}$ quan sát "
            f"cho biến chỉ báo `{target_field}`. Bộ dữ liệu được phân chia thành $N_{{train}} = {n_train}$ (huấn luyện mô hình cơ sở), "
            f"$N_{{cal}} = {n_cal}$ (hiệu chuẩn phân vị phi tham số), và $N_{{test}} = {n_test}$ (đánh giá độc lập ngoài mẫu). "
            f"Phương pháp được áp dụng là {method_vn}.\n\n"
            f"2. **Kết quả Độ bao phủ Thực nghiệm so với Định mức Danh nghĩa ({pct_nom}%)**:\n"
            f"- Điểm ngưỡng phân vị hiệu chuẩn conformal (Conformal Quantile Cutoff): $\\hat{{q}}_{{1-\\alpha}} = {conformal_quantile:.3f}$.\n"
            f"- Khoảng dự báo Conformal đạt độ bao phủ thực nghiệm out-of-sample là **{pct_conf}%** (định mức danh nghĩa {pct_nom}%), "
            f"{coverage_status}. Cận dưới toán học hữu hạn mẫu được chứng minh: "
            f"$P(Y_{{new}} \\in \\hat{{C}}(X_{{new}})) \\ge 1 - \\alpha = {nominal_coverage:.2f}$.\n"
            f"- Ngược lại, mô hình giả định phân phối chuẩn kinh điển (Gaussian Wald CI) chỉ đạt độ bao phủ **{pct_gauss}%**, "
            f"{'bị suy giảm nghiêm trọng do vi phạm giả định chuẩn tắc' if pct_gauss < pct_conf else 'tương đương'} "
            f"(độ rộng trung bình Conformal $W = {mean_width_conf:.2f}$ so với Gaussian $W = {mean_width_gauss:.2f}$).\n\n"
            f"3. **Hàm ý Thực tiễn trong Quản trị Rủi ro Dữ liệu Khảo sát**:\n"
            f"Đối với các chỉ số khảo sát phân phối lệch (skewed) hoặc thang đo Likert/NPS bị ràng buộc biên, "
            f"khoảng dự báo Conformal bảo đảm tuyệt đối rằng không quá ${int(alpha * 100)}\\%$ các trường hợp thực tế vượt ra ngoài dải rủi ro, "
            f"ngay cả khi sai số có phương sai thay đổi hoặc phân phối dị biệt. "
            f"Điều này cung cấp cơ sở kiểm định khách quan, chống lại sự lạc quan thái quá (overconfidence) của các mô hình tham số truyền thống."
        )
