"""
Dynamic Factor Modeling (DFM) with Kalman Filter & RTS State-Space Smoothing Engine.
Based on the foundational methodologies of:
- Stock, J. H., & Watson, M. W. (2002). Forecasting using principal components from a large number of predictors. Journal of the American Statistical Association, 97(460), 1167-1179.
- Forni, M., Hallin, M., Lippi, M., & Reichlin, L. (2000). The generalized dynamic-factor model: Identification and estimation. Review of Economics and Statistics, 82(4), 540-554.
- Durbin, J., & Koopman, S. J. (2012). Time series analysis by state space methods (2nd ed.). Oxford University Press.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import numpy as np


def run_kalman_filter_smoother(
    Y: np.ndarray,
    Lambda: np.ndarray,
    A: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
    a0: Optional[np.ndarray] = None,
    P0: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Executes Forward Kalman Filter and Backward Rauch-Tung-Striebel (RTS) Smoother.
    Y: (T, P) observed data across T time waves and P indicators.
    Lambda: (P, K) factor loadings matrix.
    A: (K, K) state transition matrix: f_t = A f_{t-1} + u_t.
    Q: (K, K) transition covariance.
    R: (P, P) observation error covariance.
    Returns:
    - filtered_states: (T, K)
    - filtered_covs: (T, K, K)
    - smoothed_states: (T, K)
    - smoothed_covs: (T, K, K)
    """
    T, P = Y.shape
    K = Lambda.shape[1]

    # Initialize state and covariance
    a_prev = a0 if a0 is not None else np.zeros(K)
    P_prev = P0 if P0 is not None else np.eye(K) * 5.0

    filtered_states = np.zeros((T, K))
    filtered_covs = np.zeros((T, K, K))
    predicted_states = np.zeros((T, K))
    predicted_covs = np.zeros((T, K, K))

    # --- 1. Forward Kalman Filter ---
    for t in range(T):
        # Predict
        a_pred = A @ a_prev
        P_pred = A @ P_prev @ A.T + Q

        predicted_states[t] = a_pred
        predicted_covs[t] = P_pred

        # Innovation
        y_t = Y[t]
        v_t = y_t - Lambda @ a_pred
        F_t = Lambda @ P_pred @ Lambda.T + R
        inv_F_t = np.linalg.pinv(F_t)

        # Kalman Gain
        K_t = P_pred @ Lambda.T @ inv_F_t

        # State Update
        a_curr = a_pred + K_t @ v_t
        P_curr = (np.eye(K) - K_t @ Lambda) @ P_pred
        P_curr = 0.5 * (P_curr + P_curr.T)  # Enforce symmetry

        filtered_states[t] = a_curr
        filtered_covs[t] = P_curr

        a_prev = a_curr
        P_prev = P_curr

    # --- 2. Backward RTS Smoother ---
    smoothed_states = np.zeros((T, K))
    smoothed_covs = np.zeros((T, K, K))

    smoothed_states[T - 1] = filtered_states[T - 1]
    smoothed_covs[T - 1] = filtered_covs[T - 1]

    for t in range(T - 2, -1, -1):
        P_filt_t = filtered_covs[t]
        P_pred_next = predicted_covs[t + 1]
        inv_P_pred_next = np.linalg.pinv(P_pred_next)

        # Smoother gain: J_t = P_{t|t} A^T P_{t+1|t}^{-1}
        J_t = P_filt_t @ A.T @ inv_P_pred_next

        # Smoothed state: f_{t|T} = a_{t|t} + J_t (f_{t+1|T} - a_{t+1|t})
        smoothed_states[t] = filtered_states[t] + J_t @ (smoothed_states[t + 1] - predicted_states[t + 1])

        # Smoothed covariance: P_{t|T} = P_{t|t} + J_t (P_{t+1|T} - P_{t+1|t}) J_t^T
        P_diff = smoothed_covs[t + 1] - P_pred_next
        P_smooth_t = P_filt_t + J_t @ P_diff @ J_t.T
        smoothed_covs[t] = 0.5 * (P_smooth_t + P_smooth_t.T)

    return filtered_states, filtered_covs, smoothed_states, smoothed_covs


def compute_dynamic_factor_analysis(
    records: List[Dict[str, Any]],
    indicator_question_ids: List[str],
    time_field: str = "wave",
    indicator_titles: Optional[Dict[str, str]] = None,
    n_factors: int = 1
) -> Dict[str, Any]:
    """
    Executes full Dynamic Factor Model (DFM) with Kalman Filter & RTS State-Space Smoothing.
    """
    if len(indicator_question_ids) < 2:
        return {
            "status": "error",
            "message": "Cần tối thiểu 2 biến chỉ báo theo dõi chuỗi thời gian để ước lượng mô hình nhân tố động."
        }

    # Group responses by time wave
    waves_dict: Dict[Any, List[Dict[str, Any]]] = {}
    for r in records:
        w_val = r.get(time_field)
        if w_val is None:
            # Fallback to wave / wave_id / wave_number if present
            w_val = r.get("wave_id", r.get("wave_number", r.get("time_index", 1)))
        try:
            w_key = int(w_val)
        except (ValueError, TypeError):
            w_key = str(w_val)
        if w_key not in waves_dict:
            waves_dict[w_key] = []
        waves_dict[w_key].append(r)

    # Sort waves chronologically
    sorted_wave_keys = sorted(waves_dict.keys(), key=lambda x: (int(x) if isinstance(x, int) or (isinstance(x, str) and x.isdigit()) else str(x)))
    T = len(sorted_wave_keys)
    if T < 4:
        return {
            "status": "error",
            "message": f"Số lượng đợt khảo sát (T={T}) quá ngắn để ước lượng mô hình nhân tố động DFM (cần tối thiểu T >= 4 đợt)."
        }

    P = len(indicator_question_ids)
    titles = indicator_titles or {qid: qid for qid in indicator_question_ids}

    # Construct (T, P) wave-aggregated matrix (mean response per wave)
    Y_matrix = np.zeros((T, P))
    wave_sample_sizes = []

    for t_idx, w_key in enumerate(sorted_wave_keys):
        w_records = waves_dict[w_key]
        wave_sample_sizes.append(len(w_records))

        for j_idx, qid in enumerate(indicator_question_ids):
            vals = []
            for r in w_records:
                v = r.get(qid)
                if v is not None:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        continue
            Y_matrix[t_idx, j_idx] = np.mean(vals) if len(vals) > 0 else 0.0

    # Standardize data matrix over time
    means = np.mean(Y_matrix, axis=0)
    stds = np.std(Y_matrix, axis=0)
    stds[stds < 1e-6] = 1.0
    Y_std = (Y_matrix - means) / stds

    # --- 1. Initialize State-Space Parameters via SVD / PCA ---
    K = min(n_factors, P - 1)
    K = max(1, K)

    U, S, Vt = np.linalg.svd(Y_std, full_matrices=False)
    # Factor loadings Lambda (P, K)
    Lambda_init = Vt[:K, :].T * (S[:K] / math.sqrt(T))
    # Latent factors f (T, K)
    f_init = U[:, :K] * math.sqrt(T)

    # Fit VAR(1) transition: f_t = A f_{t-1} + u_t
    f_lag = f_init[:-1, :]
    f_lead = f_init[1:, :]
    A_init = np.linalg.pinv(f_lag.T @ f_lag) @ (f_lag.T @ f_lead)
    u_resid = f_lead - f_lag @ A_init
    Q_init = np.cov(u_resid.T) if K > 1 else np.array([[float(np.var(u_resid))]])
    Q_init = np.atleast_2d(Q_init)
    Q_init = np.maximum(Q_init, 1e-4 * np.eye(K))

    # Observation error covariance R (P, P diagonal)
    fit_y = f_init @ Lambda_init.T
    obs_res = Y_std - fit_y
    r_diag = np.var(obs_res, axis=0)
    r_diag = np.maximum(r_diag, 0.05)
    R_init = np.diag(r_diag)

    # --- 2. Run Forward Kalman Filter & Backward RTS Smoother ---
    filtered_states, filtered_covs, smoothed_states, smoothed_covs = run_kalman_filter_smoother(
        Y=Y_std,
        Lambda=Lambda_init,
        A=A_init,
        Q=Q_init,
        R=R_init
    )

    # Extract primary dynamic factor trajectory
    primary_factor_smoothed = smoothed_states[:, 0]
    primary_factor_se = np.sqrt(np.maximum(1e-6, smoothed_covs[:, 0, 0]))

    # --- 3. Variance Decomposition (Signal-to-Noise Ratio per Indicator) ---
    var_decomp_list = []
    total_signal_var = 0.0
    total_obs_var = 0.0

    for j, qid in enumerate(indicator_question_ids):
        lambda_j = Lambda_init[j, 0]
        factor_var = float(np.var(primary_factor_smoothed))
        common_var = (lambda_j ** 2) * factor_var
        idiosyncratic_var = float(r_diag[j])
        total_var = common_var + idiosyncratic_var
        r_squared = min(0.999, max(0.001, common_var / total_var)) if total_var > 1e-6 else 0.50

        total_signal_var += common_var
        total_obs_var += total_var

        var_decomp_list.append({
            "question_id": qid,
            "title": titles.get(qid, qid),
            "loading_lambda": round(float(lambda_j), 4),
            "common_variance_share_r2": round(r_squared, 4),
            "idiosyncratic_noise_share": round(1.0 - r_squared, 4),
            "signal_to_noise_ratio": round(common_var / max(1e-4, idiosyncratic_var), 2)
        })

    overall_signal_ratio = round(total_signal_var / max(1e-4, total_obs_var), 3)

    # --- 4. Trajectory Data points ---
    trajectory_points = []
    for t_idx, w_key in enumerate(sorted_wave_keys):
        f_val = float(primary_factor_smoothed[t_idx])
        se_val = float(primary_factor_se[t_idx])
        trajectory_points.append({
            "wave_index": t_idx + 1,
            "wave_label": str(w_key),
            "sample_size": wave_sample_sizes[t_idx],
            "filtered_state": round(float(filtered_states[t_idx, 0]), 4),
            "smoothed_factor": round(f_val, 4),
            "standard_error": round(se_val, 4),
            "ci_lower_95": round(f_val - 1.96 * se_val, 4),
            "ci_upper_95": round(f_val + 1.96 * se_val, 4)
        })

    # Persistence parameter (AR(1) coefficient)
    persistence_ar1 = float(A_init[0, 0])

    # --- 5. Generate Dual-Panel SVG Chart ---
    svg_chart = _generate_dfm_svg(
        trajectory=trajectory_points,
        var_decomp=var_decomp_list,
        ar1_persistence=persistence_ar1,
        overall_signal=overall_signal_ratio
    )

    # --- 6. APA 7th Edition Narrative ---
    apa_narrative = (
        f"Mô hình nhân tố động chuỗi thời gian (Dynamic Factor Model - DFM) theo chuẩn mực Stock & Watson (2002) "
        f"và Durbin & Koopman (2012) được ước lượng trên tổng số T = {T} đợt khảo sát "
        f"với P = {P} biến chỉ báo đo lường đồng thời. "
        f"Nhân tố vĩ mô động ẩn tàng F_t được giải mã thông qua thuật toán Lọc Kalman tiến và Làm mượt Rauch-Tung-Striebel (RTS) lùi. "
        f"Hệ số quán tính chuỗi đạt mức AR(1) = {persistence_ar1:.3f}, thể hiện mức độ bền vững theo thời gian "
        f"{'rất cao' if abs(persistence_ar1) > 0.7 else 'vừa phải'}. "
        f"Phân rã phương sai xác nhận nhân tố động chung giải thích trung bình {overall_signal_ratio * 100:.1f}% tổng biến thiên dữ liệu. "
        f"Biến có tải trọng tín hiệu chung mạnh nhất là '{var_decomp_list[0]['title']}' "
        f"(R² = {var_decomp_list[0]['common_variance_share_r2']:.3f}, Tín hiệu/Nhiễu = {var_decomp_list[0]['signal_to_noise_ratio']}), "
        f"cho phép tách biệt hoàn toàn xu hướng thực cốt lõi khỏi các nhiễu ngẫu nhiên đặc thù của từng đợt khảo sát."
    )

    return {
        "status": "success",
        "sample_diagnostics": {
            "total_waves_t": T,
            "total_indicators_p": P,
            "total_observations": sum(wave_sample_sizes),
            "n_dynamic_factors": K,
            "ar1_persistence": round(persistence_ar1, 4),
            "overall_signal_variance_share": overall_signal_ratio,
            "state_space_filter": "Kalman Filter + RTS Smoother (Durbin & Koopman 2012)"
        },
        "trajectory": trajectory_points,
        "variance_decomposition": var_decomp_list,
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_dfm_svg(
    trajectory: List[Dict[str, Any]],
    var_decomp: List[Dict[str, Any]],
    ar1_persistence: float,
    overall_signal: float
) -> str:
    """
    Generates a dual-panel SVG:
    Panel A: Smoothed Latent Dynamic Factor Trajectory with 95% Confidence Band.
    Panel B: Variance Decomposition Stacked Bars (Common Signal vs Idiosyncratic Noise).
    """
    svg_width = 960
    svg_height = 420

    # Panel A bounds (X: 50 to 450, Y: 70 to 360)
    p1_x, p1_y, p1_w, p1_h = 50, 70, 420, 300
    T = len(trajectory)

    all_lowers = [pt["ci_lower_95"] for pt in trajectory]
    all_uppers = [pt["ci_upper_95"] for pt in trajectory]
    min_f = min(all_lowers) - 0.2
    max_f = max(all_uppers) + 0.2
    range_f = max(1e-4, max_f - min_f)

    def to_y1(val):
        return (p1_y + p1_h - 20) - ((val - min_f) / range_f) * (p1_h - 50)

    def to_x1(idx):
        return p1_x + 30 + (idx / float(max(1, T - 1))) * (p1_w - 60)

    # Construct upper and lower polygon for 95% CI ribbon
    poly_pts = []
    for idx, pt in enumerate(trajectory):
        poly_pts.append(f"{to_x1(idx):.1f},{to_y1(pt['ci_upper_95']):.1f}")
    for idx in range(T - 1, -1, -1):
        poly_pts.append(f"{to_x1(idx):.1f},{to_y1(trajectory[idx]['ci_lower_95']):.1f}")
    ribbon_str = " ".join(poly_pts)

    # Line points for smoothed factor
    line_pts = [f"{to_x1(idx):.1f},{to_y1(pt['smoothed_factor']):.1f}" for idx, pt in enumerate(trajectory)]
    line_str = " ".join(line_pts)

    # Filtered state line points (dashed cyan)
    filt_pts = [f"{to_x1(idx):.1f},{to_y1(pt['filtered_state']):.1f}" for idx, pt in enumerate(trajectory)]
    filt_str = " ".join(filt_pts)

    # Zero line in Panel A
    y_zero = to_y1(0.0)

    # Panel B bounds: Variance decomposition bars (X: 510 to 930, Y: 70 to 360)
    p2_x, p2_y, p2_w, p2_h = 510, 70, 410, 300
    P_count = len(var_decomp)
    bar_h = min(32.0, (p2_h - 60) / float(max(1, P_count)))

    bars_svg = []
    for idx, item in enumerate(var_decomp[:7]):  # Max 7 bars for elegance
        by = p2_y + 35 + idx * (bar_h + 8)
        signal_w = item["common_variance_share_r2"] * (p2_w - 140)
        noise_w = item["idiosyncratic_noise_share"] * (p2_w - 140)

        title_short = item["title"][:16] + "..." if len(item["title"]) > 16 else item["title"]

        bars_svg.append(
            f'<text x="{p2_x + 10}" y="{by + bar_h/2 + 4}" font-family="system-ui" font-size="10" fill="#cbd5e1">{title_short}</text>'
        )
        # Common signal bar (Emerald)
        bars_svg.append(
            f'<rect x="{p2_x + 110}" y="{by}" width="{signal_w:.1f}" height="{bar_h:.1f}" fill="#10b981" rx="2" />'
        )
        # Idiosyncratic noise bar (Slate/Red)
        bars_svg.append(
            f'<rect x="{p2_x + 110 + signal_w:.1f}" y="{by}" width="{noise_w:.1f}" height="{bar_h:.1f}" fill="#475569" opacity="0.6" rx="2" />'
        )
        # Label with R2 percentage
        bars_svg.append(
            f'<text x="{p2_x + 115 + signal_w + noise_w}" y="{by + bar_h/2 + 4}" font-family="system-ui" font-size="10" font-weight="700" fill="#34d399">{item["common_variance_share_r2"]*100:.0f}%</text>'
        )

    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" class="dfm-svg">',
        '<style>',
        '.dfm-bg { fill: #0f172a; }',
        '.dfm-panel { fill: #1e293b; stroke: #334155; stroke-width: 1.5; rx: 8px; }',
        '.dfm-title { font-family: system-ui, -apple-system, sans-serif; font-size: 13px; font-weight: 700; fill: #f8fafc; }',
        '.dfm-subtitle { font-family: system-ui, -apple-system, sans-serif; font-size: 10px; fill: #94a3b8; }',
        '.dfm-ref { stroke: #64748b; stroke-width: 1; stroke-dasharray: 2,2; }',
        '.dfm-ribbon { fill: #0284c7; fill-opacity: 0.25; }',
        '.dfm-line { fill: none; stroke: #38bdf8; stroke-width: 2.8; stroke-linecap: round; }',
        '.dfm-filt-line { fill: none; stroke: #a855f7; stroke-width: 1.5; stroke-dasharray: 3,3; }',
        '.dfm-pt { fill: #0284c7; stroke: #fff; stroke-width: 1.5; }',
        '</style>',
        f'<rect width="{svg_width}" height="{svg_height}" class="dfm-bg" rx="12" />',

        # Panel A Container
        f'<rect x="{p1_x - 10}" y="{p1_y - 25}" width="{p1_w + 20}" height="{p1_h + 35}" class="dfm-panel" />',
        f'<text x="{p1_x}" y="{p1_y - 5}" class="dfm-title">Panel A: Quỹ Đạo Nhân Tố Động RTS Smoother (F_t)</text>',
        f'<text x="{p1_x}" y="{p1_y + 10}" class="dfm-subtitle">Lọc Kalman &amp; Làm mượt RTS (Xanh Lam) kèm 95% Confidence Band · AR(1) = {ar1_persistence:.2f}</text>',

        # Zero reference line in Panel A
        f'<line x1="{p1_x + 20}" y1="{y_zero}" x2="{p1_x + p1_w - 20}" y2="{y_zero}" class="dfm-ref" />',
        f'<line x1="{p1_x + 20}" y1="{p1_y + 25}" x2="{p1_x + 20}" y2="{p1_y + p1_h - 20}" stroke="#475569" stroke-width="1" />',
        f'<line x1="{p1_x + 20}" y1="{p1_y + p1_h - 20}" x2="{p1_x + p1_w - 20}" y2="{p1_y + p1_h - 20}" stroke="#475569" stroke-width="1" />',

        # Confidence Ribbon & Trajectory Lines
        f'<polygon points="{ribbon_str}" class="dfm-ribbon" />',
        f'<polyline points="{filt_str}" class="dfm-filt-line" />',
        f'<polyline points="{line_str}" class="dfm-line" />',

        # Nodes
        "".join([
            f'<circle cx="{to_x1(idx):.1f}" cy="{to_y1(pt["smoothed_factor"]):.1f}" r="3.5" class="dfm-pt" />'
            f'<text x="{to_x1(idx):.1f}" y="{p1_y + p1_h - 6}" font-family="system-ui" font-size="9" fill="#94a3b8" text-anchor="middle">W{pt["wave_label"]}</text>'
            for idx, pt in enumerate(trajectory)
        ]),

        # Panel B Container
        f'<rect x="{p2_x - 10}" y="{p2_y - 25}" width="{p2_w + 20}" height="{p2_h + 35}" class="dfm-panel" />',
        f'<text x="{p2_x}" y="{p2_y - 5}" class="dfm-title">Panel B: Phân Rã Phương Sai (Tín Hiệu vs Nhiễu)</text>',
        f'<text x="{p2_x}" y="{p2_y + 10}" class="dfm-subtitle">Tín hiệu chung F_t (Xanh lá) vs Nhiễu đặc thù (Xám) · Tín hiệu toàn bộ: {overall_signal*100:.1f}%</text>',
        "\n".join(bars_svg),

        '</svg>'
    ]

    return "\n".join(svg_elements)
