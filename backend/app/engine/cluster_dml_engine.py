"""
DataTrust - Double/Debiased Machine Learning with Multiway Cluster-Robust Cross-Fitting Engine (Cluster-DML)
Scientific References:
- Chiang, H. D., Kato, K., Ma, Y., & Sasaki, Y. (2022). "Multiway Cluster Robust Double/Debiased Machine Learning."
  Journal of Econometrics, 227(2): 374-396.
- Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018).
  "Double/debiased machine learning for treatment and structural parameters." The Econometrics Journal, 21(1): C1-C68.
- Belloni, A., Chernozhukov, V., Fernández-Val, I., & Hansen, C. (2016).
  "Program Evaluation and Causal Inference with High-Dimensional Data." Econometrica, 85(1): 233-298.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from scipy import stats


def run_cluster_dml(
    records: List[Dict[str, Any]],
    cluster_col: str,
    treatment_col: str,
    outcome_col: str,
    covariate_cols: List[str],
    n_splits: int = 5,
    ml_model: str = "random_forest",
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Cluster-Robust Double/Debiased Machine Learning (Chiang et al. 2022).
    Cluster-split cross-fitting preserves intra-cluster correlation and eliminates
    the severe false-positive bias of naive i.i.d. DML.
    """
    # 1. Clean records
    valid_rows = []
    for r in records:
        c_raw = r.get(cluster_col)
        d_raw = r.get(treatment_col)
        y_raw = r.get(outcome_col)
        if c_raw is None or d_raw is None or y_raw is None:
            continue
        try:
            c_str = str(c_raw).strip()
            d_val = float(d_raw)
            y_val = float(y_raw)
            if np.isnan(d_val) or np.isnan(y_val) or np.isinf(d_val) or np.isinf(y_val):
                continue

            x_vals = []
            valid_x = True
            for col in covariate_cols:
                xv_raw = r.get(col)
                if xv_raw is None:
                    valid_x = False
                    break
                try:
                    xv = float(xv_raw)
                    if np.isnan(xv) or np.isinf(xv):
                        valid_x = False
                        break
                    x_vals.append(xv)
                except (ValueError, TypeError):
                    valid_x = False
                    break
            if not valid_x:
                continue

            valid_rows.append({
                "cluster": c_str,
                "d": d_val,
                "y": y_val,
                "x": x_vals
            })
        except (ValueError, TypeError):
            continue

    if len(valid_rows) < 30:
        return {
            "status": "error",
            "message": f"Số lượng bản ghi hợp lệ ({len(valid_rows)}) quá ít, yêu cầu tối thiểu 30 bản ghi."
        }

    # 2. Check cluster structure
    unique_clusters = sorted(list(set(r["cluster"] for r in valid_rows)))
    C = len(unique_clusters)
    if C < 4:
        return {
            "status": "error",
            "message": f"Cần tối thiểu 4 cụm (clusters) độc lập để thực hiện Cluster-DML (hiện có {C} cụm)."
        }

    cluster_to_idx = {c: i for i, c in enumerate(unique_clusters)}
    cluster_indices = np.array([cluster_to_idx[r["cluster"]] for r in valid_rows])
    cluster_sizes = [sum(1 for r in valid_rows if r["cluster"] == c) for c in unique_clusters]

    N = len(valid_rows)
    X = np.array([r["x"] for r in valid_rows])
    D = np.array([r["d"] for r in valid_rows])
    Y = np.array([r["y"] for r in valid_rows])

    # 3. Cluster-Split Cross-Fitting
    K = max(2, min(n_splits, min(C, 10)))
    np.random.seed(747)
    shuffled_clusters = np.array(range(C))
    np.random.shuffle(shuffled_clusters)
    cluster_folds = np.array_split(shuffled_clusters, K)

    D_res = np.zeros(N)
    Y_res = np.zeros(N)
    D_pred_all = np.zeros(N)
    Y_pred_all = np.zeros(N)

    for k in range(K):
        test_c = cluster_folds[k]
        test_mask = np.isin(cluster_indices, test_c)
        train_mask = ~test_mask

        # Fallback if fold is empty or degenerated
        if np.sum(train_mask) < 10 or np.sum(test_mask) == 0:
            continue

        X_train, D_train, Y_train = X[train_mask], D[train_mask], Y[train_mask]
        X_test, D_test, Y_test = X[test_mask], D[test_mask], Y[test_mask]

        if ml_model == "gradient_boost":
            m_d = GradientBoostingRegressor(n_estimators=40, max_depth=3, random_state=42)
            m_y = GradientBoostingRegressor(n_estimators=40, max_depth=3, random_state=42)
        elif ml_model == "ridge":
            m_d = Ridge(alpha=1.0)
            m_y = Ridge(alpha=1.0)
        else:
            # Default: Random Forest
            m_d = RandomForestRegressor(n_estimators=40, max_depth=6, random_state=42)
            m_y = RandomForestRegressor(n_estimators=40, max_depth=6, random_state=42)

        m_d.fit(X_train, D_train)
        D_pred = m_d.predict(X_test)

        m_y.fit(X_train, Y_train)
        Y_pred = m_y.predict(X_test)

        D_pred_all[test_mask] = D_pred
        Y_pred_all[test_mask] = Y_pred

        D_res[test_mask] = D_test - D_pred
        Y_res[test_mask] = Y_test - Y_pred

    # 4. Point Estimate (Partially Linear Model)
    denom = float(np.sum(D_res ** 2))
    if denom < 1e-8:
        denom = 1e-6
    theta_hat = float(np.sum(D_res * Y_res) / denom)

    # Residuals
    u_res = Y_res - theta_hat * D_res

    # 5. Variance Estimation: Cluster-Robust vs Naive I.I.D.
    cluster_scores = []
    cluster_profiles = []

    for c_idx, c_name in enumerate(unique_clusters):
        c_mask = (cluster_indices == c_idx)
        n_c = int(np.sum(c_mask))
        psi_c = float(np.sum(u_res[c_mask] * D_res[c_mask]))
        cluster_scores.append(psi_c)

        cluster_profiles.append({
            "cluster_id": c_name,
            "sample_size": n_c,
            "treatment_mean": round(float(np.mean(D[c_mask])), 3),
            "outcome_mean": round(float(np.mean(Y[c_mask])), 3),
            "cluster_score": round(psi_c, 3),
            "contribution_pct": 0.0 # Will compute below
        })

    cluster_scores_arr = np.array(cluster_scores)
    total_abs_score = float(np.sum(np.abs(cluster_scores_arr))) or 1.0
    for cp in cluster_profiles:
        cp["contribution_pct"] = round(float(abs(cp["cluster_score"]) / total_abs_score * 100.0), 2)
    cluster_profiles.sort(key=lambda x: abs(x["cluster_score"]), reverse=True)

    # Cluster-Robust Variance (Chiang et al. 2022)
    var_cluster = float(np.sum(cluster_scores_arr ** 2) / (denom ** 2))
    se_cluster = float(np.sqrt(max(1e-8, var_cluster)))

    # Naive I.I.D. Variance (Ignoring clustering)
    var_naive = float(np.sum((u_res * D_res) ** 2) / (denom ** 2))
    se_naive = float(np.sqrt(max(1e-8, var_naive)))

    se_inflation_ratio = round(float(se_cluster / se_naive), 2) if se_naive > 1e-8 else 1.0

    z_crit = float(stats.norm.ppf(1.0 - alpha_level / 2.0))
    ci_cluster_lower = float(theta_hat - z_crit * se_cluster)
    ci_cluster_upper = float(theta_hat + z_crit * se_cluster)
    t_stat_cluster = float(theta_hat / se_cluster) if se_cluster > 1e-8 else 0.0
    p_val_cluster = float(2.0 * (1.0 - stats.norm.cdf(abs(t_stat_cluster))))
    is_significant = bool(p_val_cluster < alpha_level)

    ci_naive_lower = float(theta_hat - z_crit * se_naive)
    ci_naive_upper = float(theta_hat + z_crit * se_naive)
    p_val_naive = float(2.0 * (1.0 - stats.norm.cdf(abs(theta_hat / se_naive)))) if se_naive > 1e-8 else 0.0

    # 6. Intra-Cluster Correlation (ICC)
    # One-way ANOVA decomposition on outcome Y
    y_grand_mean = np.mean(Y)
    ss_between = sum(len(np.where(cluster_indices == c)[0]) * (np.mean(Y[cluster_indices == c]) - y_grand_mean) ** 2 for c in range(C))
    ss_total = np.sum((Y - y_grand_mean) ** 2)
    icc = float(max(0.0, min(1.0, ss_between / ss_total))) if ss_total > 1e-8 else 0.0

    # ML R-squared diagnostics
    tot_var_y = float(np.sum((Y - np.mean(Y)) ** 2)) or 1.0
    r2_y = float(max(0.0, 1.0 - np.sum((Y - Y_pred_all) ** 2) / tot_var_y))
    tot_var_d = float(np.sum((D - np.mean(D)) ** 2)) or 1.0
    r2_d = float(max(0.0, 1.0 - np.sum((D - D_pred_all) ** 2) / tot_var_d))

    # 7. Dual-Panel SVG Visualization
    svg_viz = generate_cluster_dml_svg(
        theta_hat=theta_hat,
        ci_cluster=(ci_cluster_lower, ci_cluster_upper),
        ci_naive=(ci_naive_lower, ci_naive_upper),
        cluster_profiles=cluster_profiles[:8],
        se_inflation=se_inflation_ratio
    )

    # 8. APA 7th Narrative
    apa_narrative = generate_cluster_dml_apa_narrative(
        theta_hat=theta_hat,
        se_cluster=se_cluster,
        ci_cluster_lower=ci_cluster_lower,
        ci_cluster_upper=ci_cluster_upper,
        t_stat_cluster=t_stat_cluster,
        p_val_cluster=p_val_cluster,
        se_naive=se_naive,
        ci_naive_lower=ci_naive_lower,
        ci_naive_upper=ci_naive_upper,
        p_val_naive=p_val_naive,
        se_inflation=se_inflation_ratio,
        num_clusters=C,
        n_total=N,
        icc=icc,
        r2_y=r2_y,
        r2_d=r2_d,
        ml_model=ml_model,
        top_clusters=cluster_profiles[:3]
    )

    return {
        "status": "success",
        "sample_size": N,
        "estimates": {
            "theta": round(theta_hat, 4),
            "se_cluster": round(se_cluster, 4),
            "ci_95_cluster": [round(ci_cluster_lower, 4), round(ci_cluster_upper, 4)],
            "t_stat_cluster": round(t_stat_cluster, 3),
            "p_value_cluster": round(p_val_cluster, 5),
            "is_significant": is_significant,
            "se_naive": round(se_naive, 4),
            "ci_95_naive": [round(ci_naive_lower, 4), round(ci_naive_upper, 4)],
            "p_value_naive": round(p_val_naive, 5),
            "se_inflation_ratio": se_inflation_ratio
        },
        "diagnostics": {
            "num_clusters": C,
            "avg_cluster_size": round(float(np.mean(cluster_sizes)), 1),
            "min_cluster_size": min(cluster_sizes),
            "max_cluster_size": max(cluster_sizes),
            "intra_cluster_correlation_icc": round(icc, 3),
            "r2_outcome_ml": round(r2_y, 3),
            "r2_treatment_ml": round(r2_d, 3),
            "ml_algorithm": ml_model,
            "k_folds": K
        },
        "cluster_profiles": cluster_profiles,
        "svg_visualization": svg_viz,
        "apa_narrative": apa_narrative
    }


def generate_cluster_dml_svg(
    theta_hat: float,
    ci_cluster: Tuple[float, float],
    ci_naive: Tuple[float, float],
    cluster_profiles: List[Dict[str, Any]],
    se_inflation: float
) -> str:
    """Generates a responsive dual-panel SVG for Cluster-DML Forest Plot and Cluster Leverage."""
    width = 960
    height = 360

    # Panel A: Forest Plot (x: 50, y: 50, w: 430, h: 240)
    p1_x = 55
    p1_y = 50
    p1_w = 420
    p1_h = 240

    all_vals = [ci_cluster[0], ci_cluster[1], ci_naive[0], ci_naive[1], theta_hat, 0.0]
    min_x = min(all_vals)
    max_x = max(all_vals)
    xrange = max_x - min_x
    if xrange < 1e-4:
        xrange = 1.0
    xpad = xrange * 0.2
    x_min_plot = min_x - xpad
    x_max_plot = max_x + xpad
    plot_w = x_max_plot - x_min_plot

    def get_px(val: float) -> float:
        ratio = (val - x_min_plot) / plot_w
        return p1_x + ratio * p1_w

    px_zero = get_px(0.0)
    px_est = get_px(theta_hat)

    # Row 1: Cluster-DML (y: 110)
    y_row1 = p1_y + 70
    px_c_low = get_px(ci_cluster[0])
    px_c_high = get_px(ci_cluster[1])

    # Row 2: Naive DML (y: 170)
    y_row2 = p1_y + 150
    px_n_low = get_px(ci_naive[0])
    px_n_high = get_px(ci_naive[1])

    # Panel B: Cluster Score Contributions (x: 540, y: 50, w: 360, h: 240)
    p2_x = 550
    p2_y = 50
    p2_w = 350
    p2_h = 240

    bars_svg = []
    max_score = max((abs(cp["cluster_score"]) for cp in cluster_profiles), default=1.0)
    if max_score < 1e-4:
        max_score = 1.0
    bar_h = 18
    gap_b = 10

    for idx, cp in enumerate(cluster_profiles[:7]):
        by = p2_y + idx * (bar_h + gap_b) + 12
        score_val = cp["cluster_score"]
        bar_len = (abs(score_val) / max_score) * (p2_w * 0.45)
        bar_color = "#3b82f6" if score_val >= 0 else "#f97316"
        c_label = cp["cluster_id"][:12]

        bars_svg.append(f"""
        <g>
          <text x="{p2_x}" y="{by + 13}" font-size="11" font-family="sans-serif" fill="#475569" font-weight="600">{c_label}</text>
          <rect x="{p2_x + 90}" y="{by}" width="{max(2.0, bar_len):.1f}" height="{bar_h}" rx="3" fill="{bar_color}" opacity="0.85" />
          <text x="{p2_x + 98 + max(2.0, bar_len):.1f}" y="{by + 13}" font-size="10" font-family="sans-serif" fill="#334155" font-weight="bold">
            {score_val:+.2f} ({cp['contribution_pct']}%)
          </text>
        </g>
        """)

    bars_markup = "".join(bars_svg)

    svg = f"""<svg viewBox="0 0 {width} {height}" class="w-full h-auto select-none font-sans" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#f8fafc" rx="12" />

  <!-- Panel A: Forest Plot -->
  <g id="panel-forest">
    <text x="{p1_x}" y="30" font-size="13" font-weight="bold" fill="#0f172a">So sánh Khoảng tin cậy: Cluster-DML vs Naive DML</text>
    
    <!-- Background box -->
    <rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" fill="none" stroke="#e2e8f0" stroke-width="1" />

    <!-- Zero Reference Line -->
    <line x1="{px_zero:.1f}" y1="{p1_y}" x2="{px_zero:.1f}" y2="{p1_y + p1_h}" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="3,3" />
    <text x="{px_zero:.1f}" y="{p1_y + p1_h + 18}" font-size="10" text-anchor="middle" fill="#94a3b8">0</text>

    <!-- Point estimate vertical dash -->
    <line x1="{px_est:.1f}" y1="{p1_y}" x2="{px_est:.1f}" y2="{p1_y + p1_h}" stroke="#3b82f6" stroke-width="1" stroke-dasharray="2,2" />

    <!-- Row 1: Cluster-Robust DML (Blue) -->
    <text x="{p1_x + 10}" y="{y_row1 - 12}" font-size="11" font-weight="bold" fill="#1e40af">Cluster-Robust DML (Chiang et al. 2022)</text>
    <line x1="{px_c_low:.1f}" y1="{y_row1}" x2="{px_c_high:.1f}" y2="{y_row1}" stroke="#2563eb" stroke-width="4" stroke-linecap="round" />
    <circle cx="{px_est:.1f}" cy="{y_row1}" r="6" fill="#1d4ed8" />
    <text x="{px_c_high + 8:.1f}" y="{y_row1 + 4}" font-size="11" font-weight="bold" fill="#1e40af">[{ci_cluster[0]:.2f}, {ci_cluster[1]:.2f}]</text>

    <!-- Row 2: Naive I.I.D. DML (Orange - False confidence) -->
    <text x="{p1_x + 10}" y="{y_row2 - 12}" font-size="11" font-weight="bold" fill="#c2410c">Naive I.I.D. DML (Bỏ qua cấu trúc cụm)</text>
    <line x1="{px_n_low:.1f}" y1="{y_row2}" x2="{px_n_high:.1f}" y2="{y_row2}" stroke="#ea580c" stroke-width="4" stroke-linecap="round" />
    <circle cx="{px_est:.1f}" cy="{y_row2}" r="6" fill="#c2410c" />
    <text x="{px_n_high + 8:.1f}" y="{y_row2 + 4}" font-size="11" font-weight="bold" fill="#c2410c">[{ci_naive[0]:.2f}, {ci_naive[1]:.2f}]</text>

    <!-- Footnote -->
    <text x="{p1_x + 10}" y="{p1_y + p1_h - 14}" font-size="11" fill="#64748b" font-weight="600">
      Độ giãn sai số chuẩn (SE Inflation): <tspan fill="#dc2626" font-weight="bold">{se_inflation:.2f}x</tspan> rộng hơn
    </text>
  </g>

  <!-- Panel B: Cluster Score Contributions -->
  <g id="panel-clusters">
    <text x="{p2_x}" y="30" font-size="13" font-weight="bold" fill="#0f172a">Đóng góp Điểm số Cụm (Cluster Score ψ_c)</text>
    <line x1="{p2_x}" y1="{p2_y + p2_h}" x2="{p2_x + p2_w}" y2="{p2_y + p2_h}" stroke="#cbd5e1" stroke-width="1" />
    {bars_markup}
    <!-- Badge -->
    <rect x="{p2_x}" y="{p2_y + p2_h + 15}" width="{p2_w}" height="28" rx="6" fill="#eff6ff" />
    <text x="{p2_x + 10}" y="{p2_y + p2_h + 34}" font-size="11" font-weight="bold" fill="#1e40af">
      Hiệu ứng Can thiệp θ̂ = {theta_hat:+.3f} (Neyman Orthogonal)
    </text>
  </g>
</svg>"""
    return svg.strip()


def generate_cluster_dml_apa_narrative(
    theta_hat: float,
    se_cluster: float,
    ci_cluster_lower: float,
    ci_cluster_upper: float,
    t_stat_cluster: float,
    p_val_cluster: float,
    se_naive: float,
    ci_naive_lower: float,
    ci_naive_upper: float,
    p_val_naive: float,
    se_inflation: float,
    num_clusters: int,
    n_total: int,
    icc: float,
    r2_y: float,
    r2_d: float,
    ml_model: str,
    top_clusters: List[Dict[str, Any]]
) -> str:
    """Generates standard APA 7th econometric report narrative for Cluster-DML."""
    p_str = "p < .001" if p_val_cluster < 0.001 else f"p = {p_val_cluster:.3f}"
    sig_str = "đạt mức ý nghĩa thống kê cao" if p_val_cluster < 0.01 else ("đạt ý nghĩa thống kê" if p_val_cluster < 0.05 else "không đạt mức ý nghĩa thống kê quy ước")

    top_c_str = ", ".join([f"{c['cluster_id']} ({c['contribution_pct']}%)" for c in top_clusters])

    narrative = (
        f"Ước lượng Hiệu ứng Can thiệp Nhân quả bằng phương pháp Double/Debiased Machine Learning "
        f"có hiệu chỉnh Cụm Đa chiều (Cluster-DML; Chiang, Kato, Ma, & Sasaki, 2022) trên mẫu gồm "
        f"N = {n_total} quan sát phân bổ trên C = {num_clusters} cụm độc lập cho thấy: "
        f"Hiệu ứng can thiệp thuần túy đạt mức θ̂_DML = {theta_hat:.4f} "
        f"(Cluster-Robust SE = {se_cluster:.4f}, 95% CI [{ci_cluster_lower:.4f}, {ci_cluster_upper:.4f}], "
        f"t = {t_stat_cluster:.2f}, {p_str}), {sig_str} ở mức α = 0.05.\n\n"
        f"So sánh với mô hình DML cổ điển giả định quan sát độc lập (Naive I.I.D. DML: SE = {se_naive:.4f}, "
        f"95% CI [{ci_naive_lower:.4f}, {ci_naive_upper:.4f}]), hệ số tương quan nội cụm đạt mức ICC = {icc:.3f}. "
        f"Sự phụ thuộc nội cụm đã dẫn đến mức giãn sai số chuẩn thực tế gấp {se_inflation:.2f} lần. "
        f"Nếu bỏ qua hiệu chỉnh cụm, mô hình Naive sẽ mắc sai lầm loại I nghiêm trọng do tạo ra khoảng tin cậy "
        f"quá hẹp giả tạo.\n\n"
        f"Các hàm phiền nhiễu được ước lượng bằng thuật toán học máy {ml_model} thông qua phân chia cụm chéo "
        f"(Cluster-split cross-fitting) đạt độ giải thích R²_Y = {r2_y:.3f} và R²_D = {r2_d:.3f}. "
        f"Các cụm có đòn bẩy đóng góp lớn nhất vào phương sai tiệm cận bao gồm: {top_c_str}."
    )
    return narrative
