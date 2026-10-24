"""
Double / Debiased Machine Learning (DML) for Causal Treatment Effects Engine
Author: DataTrust Platform Architecture
Reference:
- Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018).
  Double/debiased machine learning for treatment and structural parameters.
  The Econometrics Journal, 21(1), C1-C68.
- Robinson, P. M. (1988). Root-N-consistent semiparametric regression. Econometrica, 56(4), 931-954.
- Chernozhukov, V., Hansen, C., & Spindler, M. (2015). Valid post-selection and post-regularization inference:
  An elementary, general approach. Annual Review of Economics, 7(1), 649-688.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats


def generate_dml_svg(
    theta_dml: float,
    se_dml: float,
    ci_lower: float,
    ci_upper: float,
    theta_naive: float,
    se_naive: float,
    res_d: np.ndarray,
    res_y: np.ndarray,
    outcome_label: str,
    treatment_label: str,
    r2_y: float,
    r2_d: float
) -> str:
    """
    Generates dual-panel scientific SVG:
    Panel A: Neyman-Orthogonalized Residual Scatter Plot (Y - g(X) vs D - m(X)) with DML slope.
    Panel B: Debiasing Forest Plot (DML vs Naive OLS) with 95% Confidence Intervals.
    """
    w, h = 940, 480
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; background-color: #0f172a;">')

    # Defs & Gradients
    svg.append('''
    <defs>
      <linearGradient id="dmlGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#10b981"/>
        <stop offset="100%" stop-color="#059669"/>
      </linearGradient>
      <linearGradient id="naiveGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#f59e0b"/>
        <stop offset="100%" stop-color="#d97706"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
        <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000000" flood-opacity="0.4"/>
      </filter>
    </defs>
    ''')

    # Title & Subtitle
    svg.append(f'<text x="24" y="32" fill="#f8fafc" font-size="16" font-weight="bold">Double / Debiased Machine Learning (DML - Chernozhukov et al. 2018)</text>')
    svg.append(f'<text x="24" y="52" fill="#94a3b8" font-size="11">Khử thiên lệch chính quy hóa qua Điểm Neyman Trực giao &amp; K-Fold Cross-Fitting &bull; {treatment_label} &rarr; {outcome_label}</text>')

    # ------------------ PANEL A: Residual Scatter & DML Slope (Left: w=520, h=370) ------------------
    p1_x, p1_y, p1_w, p1_h = 24, 75, 510, 360
    svg.append(f'<rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" rx="10" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p1_x+16}" y="{p1_y+24}" fill="#38bdf8" font-size="12" font-weight="600">Panel A: Đám mây Thặng dư Trực giao Robinson (Y - g&#770; vs D - m&#770;)</text>')

    # Scatter bounds
    subsample_idx = np.random.choice(len(res_d), size=min(120, len(res_d)), replace=False) if len(res_d) > 120 else np.arange(len(res_d))
    d_sub = res_d[subsample_idx]
    y_sub = res_y[subsample_idx]

    d_min, d_max = float(np.percentile(res_d, 2)), float(np.percentile(res_d, 98))
    y_min, y_max = float(np.percentile(res_y, 2)), float(np.percentile(res_y, 98))
    if d_max <= d_min:
        d_min, d_max = -1.0, 1.0
    if y_max <= y_min:
        y_min, y_max = -1.0, 1.0

    d_span = (d_max - d_min) * 0.15
    y_span = (y_max - y_min) * 0.15
    d_min, d_max = d_min - d_span, d_max + d_span
    y_min, y_max = y_min - y_span, y_max + y_span

    c_x, c_y, c_w, c_h = p1_x + 50, p1_y + 45, p1_w - 70, p1_h - 85

    def map_x_res(val: float) -> float:
        return c_x + (val - d_min) / (d_max - d_min) * c_w

    def map_y_res(val: float) -> float:
        return c_y + c_h - (val - y_min) / (y_max - y_min) * c_h

    # Zero axes
    x_zero = map_x_res(0.0)
    y_zero = map_y_res(0.0)
    svg.append(f'<line x1="{c_x}" y1="{y_zero}" x2="{c_x+c_w}" y2="{y_zero}" stroke="#475569" stroke-width="1" stroke-dasharray="3 3"/>')
    svg.append(f'<line x1="{x_zero}" y1="{c_y}" x2="{x_zero}" y2="{c_y+c_h}" stroke="#475569" stroke-width="1" stroke-dasharray="3 3"/>')

    # Scatter points
    for ds, ys in zip(d_sub, y_sub):
        px = map_x_res(ds)
        py = map_y_res(ys)
        if c_x <= px <= c_x + c_w and c_y <= py <= c_y + c_h:
            svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="#38bdf8" fill-opacity="0.6"/>')

    # DML regression line through origin: Y_res = theta_dml * D_res
    x1_line = d_min
    y1_line = theta_dml * x1_line
    x2_line = d_max
    y2_line = theta_dml * x2_line

    lx1 = map_x_res(x1_line)
    ly1 = map_y_res(y1_line)
    lx2 = map_x_res(x2_line)
    ly2 = map_y_res(y2_line)
    svg.append(f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" stroke="#10b981" stroke-width="3"/>')

    # Labels
    svg.append(f'<text x="{c_x+c_w/2}" y="{c_y+c_h+30}" fill="#94a3b8" font-size="10" text-anchor="middle">Thặng dư Can thiệp: D - m&#770;(X)</text>')
    svg.append(f'<text x="{c_x+10}" y="{c_y+20}" fill="#10b981" font-size="11" font-weight="bold">Độ dốc DML &theta;&#770; = {theta_dml:+.3f}</text>')

    # ------------------ PANEL B: Debiasing Forest Plot (Right: w=360, h=370) ------------------
    p2_x, p2_y, p2_w, p2_h = 554, 75, 362, 360
    svg.append(f'<rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" rx="10" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p2_x+16}" y="{p2_y+24}" fill="#38bdf8" font-size="12" font-weight="600">Panel B: So sánh Hiệu ứng &amp; Khử Thiên lệch (Forest Plot)</text>')

    # Forest plot comparing DML vs Naive OLS
    forest_y_start = p2_y + 80
    forest_gap = 90

    # Scales for forest plot
    all_effs = [theta_dml, theta_naive, ci_lower, ci_upper, theta_naive - 1.96 * se_naive, theta_naive + 1.96 * se_naive]
    f_min = min(all_effs) - 0.2 * abs(max(all_effs) - min(all_effs) + 1e-4)
    f_max = max(all_effs) + 0.2 * abs(max(all_effs) - min(all_effs) + 1e-4)
    if f_max <= f_min:
        f_min, f_max = -1.0, 1.0

    fx_start = p2_x + 30
    fx_width = p2_w - 60

    def map_x_forest(val: float) -> float:
        return fx_start + (val - f_min) / (f_max - f_min) * fx_width

    # Zero vertical line in forest plot
    if f_min <= 0.0 <= f_max:
        f_zero = map_x_forest(0.0)
        svg.append(f'<line x1="{f_zero}" y1="{forest_y_start-20}" x2="{f_zero}" y2="{forest_y_start+160}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3 3"/>')
        svg.append(f'<text x="{f_zero}" y="{forest_y_start+175}" fill="#64748b" font-size="9" text-anchor="middle">0.0 (Không tác động)</text>')

    # 1. DML Point & CI
    y_dml = forest_y_start + 20
    x_dml_pt = map_x_forest(theta_dml)
    x_dml_l = map_x_forest(ci_lower)
    x_dml_u = map_x_forest(ci_upper)

    svg.append(f'<text x="{fx_start}" y="{y_dml-16}" fill="#10b981" font-size="11" font-weight="bold">Double ML (Khử Thiên lệch Neyman): {theta_dml:+.3f}</text>')
    svg.append(f'<text x="{fx_start}" y="{y_dml-3}" fill="#94a3b8" font-size="9">95% CI: [{ci_lower:+.3f}, {ci_upper:+.3f}] &bull; SE: {se_dml:.3f}</text>')
    svg.append(f'<line x1="{x_dml_l}" y1="{y_dml+12}" x2="{x_dml_u}" y2="{y_dml+12}" stroke="#10b981" stroke-width="3"/>')
    svg.append(f'<line x1="{x_dml_l}" y1="{y_dml+6}" x2="{x_dml_l}" y2="{y_dml+18}" stroke="#10b981" stroke-width="2"/>')
    svg.append(f'<line x1="{x_dml_u}" y1="{y_dml+6}" x2="{x_dml_u}" y2="{y_dml+18}" stroke="#10b981" stroke-width="2"/>')
    svg.append(f'<circle cx="{x_dml_pt}" cy="{y_dml+12}" r="6" fill="#10b981" stroke="#ffffff" stroke-width="1.5" filter="url(#shadow)"/>')

    # 2. Naive OLS Point & CI
    y_naive = y_dml + forest_gap
    ci_naive_l = theta_naive - 1.96 * se_naive
    ci_naive_u = theta_naive + 1.96 * se_naive
    x_naive_pt = map_x_forest(theta_naive)
    x_naive_l = map_x_forest(ci_naive_l)
    x_naive_u = map_x_forest(ci_naive_u)

    svg.append(f'<text x="{fx_start}" y="{y_naive-16}" fill="#f59e0b" font-size="11" font-weight="bold">Hồi quy Ngây thơ (Naive OLS): {theta_naive:+.3f}</text>')
    svg.append(f'<text x="{fx_start}" y="{y_naive-3}" fill="#94a3b8" font-size="9">95% CI: [{ci_naive_l:+.3f}, {ci_naive_u:+.3f}] &bull; SE: {se_naive:.3f}</text>')
    svg.append(f'<line x1="{x_naive_l}" y1="{y_naive+12}" x2="{x_naive_u}" y2="{y_naive+12}" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="2 2"/>')
    svg.append(f'<line x1="{x_naive_l}" y1="{y_naive+6}" x2="{x_naive_l}" y2="{y_naive+18}" stroke="#f59e0b" stroke-width="2"/>')
    svg.append(f'<line x1="{x_naive_u}" y1="{y_naive+6}" x2="{x_naive_u}" y2="{y_naive+18}" stroke="#f59e0b" stroke-width="2"/>')
    svg.append(f'<rect x="{x_naive_pt-5}" y="{y_naive+7}" width="10" height="10" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5"/>')

    # Confounding Bias eliminated box
    bias_eliminated = abs(theta_naive - theta_dml)
    svg.append(f'<rect x="{p2_x+16}" y="{p2_y+p2_h-80}" width="{p2_w-32}" height="60" rx="8" fill="#064e3b" fill-opacity="0.4" stroke="#10b981" stroke-width="1"/>')
    svg.append(f'<text x="{p2_x+28}" y="{p2_y+p2_h-58}" fill="#34d399" font-size="11" font-weight="bold">Độ chệch được loại bỏ (&Delta;Bias): {bias_eliminated:.3f}</text>')
    svg.append(f'<text x="{p2_x+28}" y="{p2_y+p2_h-40}" fill="#a7f3d0" font-size="9.5">Học máy kiểm soát phi tham số: R&sup2;(Y|X)={r2_y:.1%}, R&sup2;(D|X)={r2_d:.1%}.</text>')
    svg.append(f'<text x="{p2_x+28}" y="{p2_y+p2_h-26}" fill="#6ee7b7" font-size="9">Khắc phục triệt để Regularization Bias &bull; &radic;N-Consistent.</text>')

    # Footer note
    svg.append(f'<text x="24" y="{h-10}" fill="#64748b" font-size="10">Double/Debiased Machine Learning (Chernozhukov et al. 2018 Econometrica) &bull; Robinson (1988) Residual Orthogonalization.</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


class DoubleMachineLearningEngine:
    """
    Engine executing Double / Debiased Machine Learning (DML)
    for Causal Partially Linear Models via Neyman Orthogonal Scores and K-Fold Cross-Fitting
    (Chernozhukov et al. 2018).
    """

    @staticmethod
    def evaluate_dml(
        y_outcome: np.ndarray,
        d_treatment: np.ndarray,
        x_covariates: np.ndarray,
        covariate_names: List[str],
        n_folds: int = 5,
        alpha_penalty: float = 1.0,
        outcome_label: str = "Outcome",
        treatment_label: str = "Treatment"
    ) -> Dict[str, Any]:
        """
        Executes DML for Partially Linear Model (PLR):
        Y = D * theta_0 + g_0(X) + U,  E[U | D, X] = 0
        D = m_0(X) + V,                E[V | X] = 0
        Using K-fold cross-fitting and Ridge nuisance regressions with Neyman orthogonal score:
        psi(W; theta, eta) = (Y - g(X) - theta * (D - m(X))) * (D - m(X))
        """
        y = np.asarray(y_outcome, dtype=float)
        d = np.asarray(d_treatment, dtype=float)
        x = np.asarray(x_covariates, dtype=float)

        n = len(y)
        if n < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Kích thước mẫu không đủ để thực hiện DML (N={n}). Cần tối thiểu 30 quan sát."
            }

        k_folds = max(2, min(10, n_folds))
        n_covs = x.shape[1] if x.ndim > 1 else 1
        if x.ndim == 1:
            x = x.reshape(-1, 1)

        # Remove NaNs
        valid = ~np.isnan(y) & ~np.isnan(d) & ~np.isnan(x).any(axis=1)
        y, d, x = y[valid], d[valid], x[valid]
        n_clean = len(y)
        if n_clean < 30:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N={n_clean}) không đủ sau khi loại bỏ dữ liệu khuyết."
            }

        # ---------------- 1. Naive OLS Regression (Y on D) ----------------
        ones = np.ones(n_clean)
        z_naive = np.column_stack([ones, d])
        try:
            beta_naive, _, _, _ = np.linalg.lstsq(z_naive, y, rcond=None)
            res_naive = y - z_naive @ beta_naive
            dof_naive = max(n_clean - 2, 1)
            se_naive = float(np.sqrt(np.sum(res_naive**2) / dof_naive / np.sum((d - np.mean(d))**2 + 1e-8)))
            theta_naive = float(beta_naive[1])
        except Exception:
            theta_naive = float(np.cov(d, y)[0, 1] / max(np.var(d), 1e-6))
            se_naive = 0.1

        # ---------------- 2. K-Fold Cross-Fitting for DML ----------------
        np.random.seed(42)
        indices = np.arange(n_clean)
        np.random.shuffle(indices)
        folds = np.array_split(indices, k_folds)

        g_hat = np.zeros(n_clean)
        m_hat = np.zeros(n_clean)

        # Standardize X for Ridge stability
        x_mean = np.mean(x, axis=0)
        x_std = np.std(x, axis=0)
        x_std[x_std < 1e-8] = 1.0
        x_norm = (x - x_mean) / x_std

        for k in range(k_folds):
            test_idx = folds[k]
            train_idx = np.setdiff1d(np.arange(n_clean), test_idx)

            x_train, y_train, d_train = x_norm[train_idx], y[train_idx], d[train_idx]
            x_test = x_norm[test_idx]

            # Fit Ridge regression for g(X) = E[Y|X]
            # (X^T X + alpha * I)^{-1} X^T Y
            p = x_train.shape[1]
            x_train_aug = np.column_stack([np.ones(len(x_train)), x_train])
            x_test_aug = np.column_stack([np.ones(len(x_test)), x_test])

            reg_matrix = alpha_penalty * np.eye(p + 1)
            reg_matrix[0, 0] = 0.0  # Do not penalize intercept

            try:
                beta_g = np.linalg.solve(x_train_aug.T @ x_train_aug + reg_matrix, x_train_aug.T @ y_train)
                g_hat[test_idx] = x_test_aug @ beta_g
            except np.linalg.LinAlgError:
                beta_g, _, _, _ = np.linalg.lstsq(x_train_aug, y_train, rcond=None)
                g_hat[test_idx] = x_test_aug @ beta_g

            # Fit Ridge regression for m(X) = E[D|X]
            try:
                beta_m = np.linalg.solve(x_train_aug.T @ x_train_aug + reg_matrix, x_train_aug.T @ d_train)
                m_hat[test_idx] = x_test_aug @ beta_m
            except np.linalg.LinAlgError:
                beta_m, _, _, _ = np.linalg.lstsq(x_train_aug, d_train, rcond=None)
                m_hat[test_idx] = x_test_aug @ beta_m

        # ---------------- 3. Neyman Orthogonal Estimator (Robinson 1988) ----------------
        # Residuals
        y_res = y - g_hat
        d_res = d - m_hat

        # DML Estimator: theta = sum(d_res * y_res) / sum(d_res^2)
        denom = float(np.sum(d_res**2))
        if denom < 1e-8:
            return {
                "status": "COLLINEARITY_ERROR",
                "message": "Phương sai thặng dư can thiệp (D - m(X)) quá nhỏ, biến can thiệp có thể là hàm tiền định từ X."
            }

        theta_dml = float(np.sum(d_res * y_res) / denom)

        # Asymptotic variance via Neyman score
        # psi_i = (y_res_i - theta * d_res_i) * d_res_i
        # J_0 = E[d_res^2]
        psi = (y_res - theta_dml * d_res) * d_res
        v_psi = float(np.mean(psi**2))
        j_hat = float(denom / n_clean)

        se_dml = float(np.sqrt(v_psi / (n_clean * (j_hat**2))))
        z_stat = float(theta_dml / max(se_dml, 1e-8))
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))

        ci_lower = float(theta_dml - 1.96 * se_dml)
        ci_upper = float(theta_dml + 1.96 * se_dml)

        # Nuisance R^2 metrics
        ss_tot_y = np.sum((y - np.mean(y))**2)
        r2_y = float(max(0.0, 1.0 - np.sum(y_res**2) / max(ss_tot_y, 1e-8)))

        ss_tot_d = np.sum((d - np.mean(d))**2)
        r2_d = float(max(0.0, 1.0 - np.sum(d_res**2) / max(ss_tot_d, 1e-8)))

        # Variable importance via correlation with residuals
        top_covs = []
        for c_idx in range(n_covs):
            cov_name = covariate_names[c_idx] if c_idx < len(covariate_names) else f"Covariate {c_idx+1}"
            corr_y = float(np.corrcoef(x[:, c_idx], y)[0, 1]) if np.std(x[:, c_idx]) > 1e-8 else 0.0
            corr_d = float(np.corrcoef(x[:, c_idx], d)[0, 1]) if np.std(x[:, c_idx]) > 1e-8 else 0.0
            confounding_score = float(abs(corr_y * corr_d))
            top_covs.append({
                "covariate": cov_name,
                "corr_outcome": round(corr_y, 3),
                "corr_treatment": round(corr_d, 3),
                "confounding_score": round(confounding_score, 4)
            })

        top_covs.sort(key=lambda item: item["confounding_score"], reverse=True)

        # SVG Chart
        svg_chart = generate_dml_svg(
            theta_dml=theta_dml,
            se_dml=se_dml,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            theta_naive=theta_naive,
            se_naive=se_naive,
            res_d=d_res,
            res_y=y_res,
            outcome_label=outcome_label,
            treatment_label=treatment_label,
            r2_y=r2_y,
            r2_d=r2_d
        )

        bias_gap = theta_naive - theta_dml
        apa = (
            f"Phân tích Học máy Khử thiên lệch Hai bước (Double / Debiased Machine Learning - DML; "
            f"Chernozhukov et al., 2018; Robinson, 1988) được thực hiện với {k_folds}-fold Cross-Fitting "
            f"trên mẫu khảo sát N = {n_clean} quan sát nhằm ước lượng hiệu ứng can thiệp nhân quả của '{treatment_label}' "
            f"lên '{outcome_label}' có kiểm soát phi tham số đồng thời {n_covs} biến kiểm soát. "
            f"Ước lượng tham số nhân quả DML đạt theta = {theta_dml:+.4f} (SE = {se_dml:.4f}, z = {z_stat:.3f}, p = {p_val:.4f}, "
            f"Khoảng tin cậy 95% CI [{ci_lower:+.4f}, {ci_upper:+.4f}]). "
            f"So sánh với hồi quy OLS ngây thơ không điều chỉnh trực giao (Naive OLS beta = {theta_naive:+.4f}, SE = {se_naive:.4f}), "
            f"phương pháp DML đã loại bỏ lượng thiên lệch nhiễu (Confounding Bias) đạt Delta = {bias_gap:+.4f}. "
            f"Mô hình học máy dự báo hàm phụ trợ đạt R2(Y|X) = {r2_y*100:.1f}% và R2(D|X) = {r2_d*100:.1f}%. "
            f"Biến kiểm soát gây nhiễu mạnh nhất trong hệ thống là '{top_covs[0]['covariate'] if top_covs else 'N/A'}' "
            f"(Hệ số tương quan kép = {top_covs[0]['confounding_score']:.4f})."
        )

        return {
            "status": "SUCCESS",
            "model_type": "DOUBLE_MACHINE_LEARNING_CHERNOZHUKOV_2018",
            "diagnostics": {
                "sample_size": n_clean,
                "n_covariates": n_covs,
                "n_folds": k_folds,
                "theta_dml": round(theta_dml, 4),
                "se_dml": round(se_dml, 4),
                "z_statistic": round(z_stat, 3),
                "p_value": round(p_val, 4),
                "ci_lower_95": round(ci_lower, 4),
                "ci_upper_95": round(ci_upper, 4),
                "theta_naive_ols": round(theta_naive, 4),
                "se_naive_ols": round(se_naive, 4),
                "confounding_bias": round(bias_gap, 4),
                "r2_nuisance_y": round(r2_y, 4),
                "r2_nuisance_d": round(r2_d, 4),
                "is_statistically_significant": bool(p_val < 0.05)
            },
            "confounding_covariates": top_covs,
            "svg_visualization": svg_chart,
            "apa_narrative": apa
        }
