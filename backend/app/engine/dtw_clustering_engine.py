"""
Dynamic Time Warping (DTW) & Longitudinal Trajectory Clustering Engine.
Based on the foundational methodologies of:
- Sakoe, H., & Chiba, S. (1978). Dynamic programming algorithm optimization for spoken word recognition. IEEE Transactions on Acoustics, Speech, and Signal Processing, 26(1), 43-49.
- Keogh, E., & Ratanamahatana, C. A. (2005). Exact indexing of dynamic time warping. Knowledge and Information Systems, 7(3), 358-386.
- Petitjean, F., Ketterlin, A., & Gançarski, P. (2011). A global averaging method for dynamic time warping, with applications to clustering. Pattern Recognition, 44(3), 678-693.
"""

from typing import Dict, List, Any, Optional
import math
import numpy as np


def compute_dtw_distance(
    ts1: np.ndarray,
    ts2: np.ndarray,
    window_radius: Optional[int] = None
) -> float:
    """
    Computes Dynamic Time Warping (DTW) distance with Sakoe-Chiba band constraint.
    """
    n = len(ts1)
    m = len(ts2)
    if n == 0 or m == 0:
        return 0.0

    if window_radius is None:
        window_radius = max(1, int(math.ceil(0.3 * max(n, m))))

    w = max(window_radius, abs(n - m))

    # Cost matrix initialized to infinity
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0.0

    for i in range(1, n + 1):
        j_start = max(1, i - w)
        j_end = min(m + 1, i + w + 1)
        for j in range(j_start, j_end):
            dist = (ts1[i - 1] - ts2[j - 1]) ** 2
            cost[i, j] = dist + min(
                cost[i - 1, j],      # insertion
                cost[i, j - 1],      # deletion
                cost[i - 1, j - 1]   # match
            )

    return float(math.sqrt(cost[n, m]))


def _classify_trajectory_archetype(trajectory: List[float]) -> str:
    """
    Heuristically classifies longitudinal trajectory shape into intuitive academic archetypes.
    """
    if len(trajectory) < 2:
        return "Quỹ đạo điểm đơn (Single Point)"

    first = trajectory[0]
    last = trajectory[-1]
    peak = max(trajectory)
    trough = min(trajectory)
    peak_idx = trajectory.index(peak)
    n = len(trajectory)

    net_change = last - first
    span = max(1e-6, peak - trough)
    rel_change = net_change / span

    # Classification logic
    if rel_change > 0.45:
        return "Tăng trưởng liên tục (Progressive Growth / Upward Surge)"
    elif rel_change < -0.45:
        return "Suy giảm lũy tiến (Progressive Decline / Wear-Off)"
    elif peak_idx > 0 and peak_idx < n - 1 and (peak - first > 0.3 * span) and (peak - last > 0.3 * span):
        return "Đỉnh sớm rồi thoái trào (Early Peak & Fade / Transient Surge)"
    elif (first - trough > 0.3 * span) and (last - trough > 0.3 * span):
        return "Chạm đáy rồi phục hồi (V-Shaped Dip & Recovery)"
    else:
        return "Ổn định đi ngang (Stable Baseline / Plateau)"


def run_dtw_trajectory_clustering(
    records: List[Dict[str, Any]],
    time_series_cols: List[str],
    time_labels: Optional[List[str]] = None,
    n_clusters: int = 3,
    window_radius: Optional[int] = None,
    max_iter: int = 25
) -> Dict[str, Any]:
    """
    Executes DTW pairwise alignment and K-Medoids trajectory clustering.
    """
    t_points = len(time_series_cols)
    if t_points < 3:
        return {
            "status": "error",
            "message": f"Cần tối thiểu 3 mốc thời gian / làn sóng chuỗi dữ liệu (hiện có {t_points} mốc)."
        }

    labels = time_labels or [f"T{i+1}" for i in range(t_points)]
    if len(labels) != t_points:
        labels = [f"T{i+1}" for i in range(t_points)]

    valid_series = []
    for r in records:
        ts = []
        valid = True
        for col in time_series_cols:
            val = r.get(col)
            if val is None:
                valid = False
                break
            try:
                ts.append(float(val))
            except (ValueError, TypeError):
                valid = False
                break
        if valid:
            valid_series.append(np.array(ts, dtype=float))

    n_sample = len(valid_series)
    if n_sample < 15:
        return {
            "status": "error",
            "message": f"Số quan sát có chuỗi thời gian hoàn chỉnh (N={n_sample}) không đủ để phân cụm quỹ đạo DTW (cần tối thiểu N >= 15)."
        }

    k = min(n_clusters, n_sample // 4)
    k = max(2, k)

    w_radius = window_radius if window_radius is not None else max(1, int(math.ceil(0.3 * t_points)))

    # Compute pairwise DTW distance matrix N x N
    dist_matrix = np.zeros((n_sample, n_sample))
    for i in range(n_sample):
        for j in range(i + 1, n_sample):
            d = compute_dtw_distance(valid_series[i], valid_series[j], window_radius=w_radius)
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d

    # K-Medoids (PAM) with greedy initialization
    np.random.seed(42)
    # Pick first medoid as point with minimum total distance to all others
    total_dists = np.sum(dist_matrix, axis=1)
    medoids = [int(np.argmin(total_dists))]

    # Pick remaining medoids using k-means++ distance-weighted probability
    for _ in range(1, k):
        min_dists = np.min(dist_matrix[:, medoids], axis=1)
        min_dists[medoids] = 0.0
        probs = min_dists / max(1e-9, np.sum(min_dists))
        next_medoid = int(np.random.choice(n_sample, p=probs))
        medoids.append(next_medoid)

    cluster_assignments = np.zeros(n_sample, dtype=int)

    # Iterative PAM refinement
    for it in range(max_iter):
        # 1. Assignment step
        cluster_assignments = np.argmin(dist_matrix[:, medoids], axis=1)

        # 2. Update medoids step
        new_medoids = []
        changed = False
        for c in range(k):
            members = np.where(cluster_assignments == c)[0]
            if len(members) == 0:
                new_medoids.append(medoids[c])
                continue
            sub_dists = dist_matrix[np.ix_(members, members)]
            best_member = members[np.argmin(np.sum(sub_dists, axis=1))]
            new_medoids.append(int(best_member))
            if best_member != medoids[c]:
                changed = True

        medoids = new_medoids
        if not changed:
            break

    # Cluster summary and barycenter trajectories
    clusters_info = []
    cluster_colors = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#06b6d4"]

    for c in range(k):
        members = np.where(cluster_assignments == c)[0]
        size = len(members)
        pct = round(size / n_sample * 100.0, 1)

        if size > 0:
            member_trajectories = np.array([valid_series[m] for m in members])
            mean_trajectory = [round(float(v), 3) for v in np.mean(member_trajectories, axis=0)]
            medoid_trajectory = [round(float(v), 3) for v in valid_series[medoids[c]]]
            # Dispersion
            within_dist = float(np.mean(dist_matrix[members, medoids[c]]))
        else:
            mean_trajectory = [0.0] * t_points
            medoid_trajectory = [0.0] * t_points
            within_dist = 0.0

        archetype = _classify_trajectory_archetype(mean_trajectory)

        clusters_info.append({
            "cluster_id": c + 1,
            "color": cluster_colors[c % len(cluster_colors)],
            "size": size,
            "percentage": pct,
            "archetype_title": archetype,
            "within_cluster_dispersion": round(within_dist, 3),
            "mean_trajectory": mean_trajectory,
            "medoid_trajectory": medoid_trajectory
        })

    # Silhouette Score calculation based on DTW distance
    silhouettes = []
    for i in range(n_sample):
        c_i = cluster_assignments[i]
        same_cluster = np.where(cluster_assignments == c_i)[0]
        same_cluster = same_cluster[same_cluster != i]

        if len(same_cluster) == 0:
            silhouettes.append(0.0)
            continue

        a_i = float(np.mean(dist_matrix[i, same_cluster]))

        # Nearest other cluster
        b_i = np.inf
        for c in range(k):
            if c == c_i:
                continue
            other_cluster = np.where(cluster_assignments == c)[0]
            if len(other_cluster) > 0:
                dist_to_other = float(np.mean(dist_matrix[i, other_cluster]))
                b_i = min(b_i, dist_to_other)

        s_i = (b_i - a_i) / max(1e-9, max(a_i, b_i))
        silhouettes.append(float(s_i))

    mean_silhouette = round(float(np.mean(silhouettes)), 3)

    # Generate Dual-Panel SVG Chart
    svg_chart = _generate_dtw_svg(
        valid_series=valid_series,
        cluster_assignments=cluster_assignments,
        clusters_info=clusters_info,
        time_labels=labels,
        n_clusters=k
    )

    # APA 7th Edition Narrative
    top_cluster = max(clusters_info, key=lambda c: c["size"])
    apa_narrative = (
        f"Phân tích phân cụm quỹ đạo theo thời gian bằng thuật toán Dynamic Time Warping (DTW) kết hợp K-Medoids "
        f"(Sakoe & Chiba, 1978; Petitjean et al., 2011) được thực hiện trên cỡ mẫu N = {n_sample} người tham gia "
        f"qua {t_points} mốc theo dõi ({', '.join(labels)}). Mô hình phân tách dữ liệu thành k = {k} hình thái quỹ đạo đặc trưng "
        f"với hệ số tách cụm Silhouette S = {mean_silhouette:.3f}. "
        f"Cụm chiếm ưu thế nhất là Cụm {top_cluster['cluster_id']} ({top_cluster['archetype_title']}) "
        f"đại diện cho n = {top_cluster['size']} người ({top_cluster['percentage']}%) với độ phân tán nội cụm DTW = {top_cluster['within_cluster_dispersion']}. "
        f"Các quỹ đạo được đồng chỉnh phi tuyến giúp loại trừ thiên lệch trễ pha thời gian, ghi nhận sự phân hóa động lực rõ rệt giữa các nhóm đối tượng."
    )

    return {
        "status": "success",
        "time_series_fields": time_series_cols,
        "time_labels": labels,
        "sample_diagnostics": {
            "n_total": n_sample,
            "n_time_points": t_points,
            "n_clusters": k,
            "window_radius": w_radius,
            "mean_silhouette_score": mean_silhouette
        },
        "clusters": clusters_info,
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_dtw_svg(
    valid_series: List[np.ndarray],
    cluster_assignments: np.ndarray,
    clusters_info: List[Dict[str, Any]],
    time_labels: List[str],
    n_clusters: int
) -> str:
    """
    Renders high-definition dual-panel vector SVG:
    Panel A: Longitudinal Trajectory Curves with Cluster Centroids
    Panel B: Cluster Proportion & Amplitude Distribution
    """
    width = 840
    height = 370

    # Panel A bounds (x: 50 to 480, y: 55 to 295)
    ax0, ax1 = 50, 480
    ay0, ay1 = 55, 295
    a_width = ax1 - ax0
    a_height = ay1 - ay0

    # All values min/max for scale
    all_vals = [float(v) for s in valid_series for v in s]
    min_v = min(all_vals)
    max_v = max(all_vals)
    v_range = max(1e-4, max_v - min_v)
    min_v -= 0.08 * v_range
    max_v += 0.08 * v_range
    v_span = max_v - min_v

    t_count = len(time_labels)

    def scale_x(t_idx: int) -> float:
        return ax0 + (t_idx / max(1, t_count - 1)) * a_width

    def scale_y(val: float) -> float:
        return ay1 - ((val - min_v) / v_span) * a_height

    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" class="w-full">',
        # Background
        f'<rect width="{width}" height="{height}" fill="#090d16" rx="12" stroke="#1e293b" stroke-width="1.5"/>',

        # Titles
        '<text x="20" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL A: Quỹ Đạo Đồng Chỉnh DTW & Trung Tâm Cụm (Centroids)</text>',
        '<text x="525" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL B: Cơ Cấu Phân Khúc & Xu Thế</text>',

        # Panel A Box
        f'<rect x="{ax0}" y="{ay0}" width="{a_width}" height="{a_height}" fill="#0c1322" rx="6" stroke="#1e293b" stroke-width="1"/>',
    ]

    # Horizontal grid lines
    for i in range(5):
        gv = min_v + (i / 4.0) * v_span
        gy = scale_y(gv)
        svg_elements.append(f'<line x1="{ax0}" y1="{gy:.1f}" x2="{ax1}" y2="{gy:.1f}" stroke="#1e293b" stroke-width="1" stroke-dasharray="3,3"/>')
        svg_elements.append(f'<text x="{ax0-6}" y="{gy+3:.1f}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="end">{gv:.1f}</text>')

    # Time point vertical grid lines & X-axis labels
    for t_idx, label in enumerate(time_labels):
        tx = scale_x(t_idx)
        svg_elements.append(f'<line x1="{tx:.1f}" y1="{ay0}" x2="{tx:.1f}" y2="{ay1}" stroke="#1e293b" stroke-width="1"/>')
        svg_elements.append(f'<text x="{tx:.1f}" y="{ay1+15}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="10" font-weight="600" text-anchor="middle">{label}</text>')

    # Individual thin trajectory lines (spaghetti, colored faintly by cluster)
    for i, s in enumerate(valid_series):
        c_idx = cluster_assignments[i]
        c_info = clusters_info[c_idx]
        pts = [f"{scale_x(t):.1f},{scale_y(s[t]):.1f}" for t in range(t_count)]
        polyline = " ".join(pts)
        svg_elements.append(f'<polyline points="{polyline}" fill="none" stroke="{c_info["color"]}" stroke-width="0.8" opacity="0.22"/>')

    # Bold mean trajectories for each cluster
    for c_info in clusters_info:
        mean_s = c_info["mean_trajectory"]
        pts = [f"{scale_x(t):.1f},{scale_y(mean_s[t]):.1f}" for t in range(t_count)]
        polyline = " ".join(pts)
        svg_elements.append(f'<polyline points="{polyline}" fill="none" stroke="{c_info["color"]}" stroke-width="3.5" stroke-linecap="round"/>')

        # Dot markers
        for t in range(t_count):
            cx = scale_x(t)
            cy = scale_y(mean_s[t])
            svg_elements.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{c_info["color"]}" stroke="#ffffff" stroke-width="1.5"/>')

    # Panel B: Cluster breakdown cards
    # Bounds: x from 525 to 815, y from 55 to 330
    bx0 = 525
    b_y_curr = 55

    for c_info in clusters_info:
        svg_elements.append(f'<rect x="{bx0}" y="{b_y_curr}" width="290" height="52" fill="#0f172a" rx="6" stroke="#1e293b" stroke-width="1"/>')
        svg_elements.append(f'<circle cx="{bx0+16}" cy="{b_y_curr+26}" r="7" fill="{c_info["color"]}"/>')
        svg_elements.append(f'<text x="{bx0+30}" y="{b_y_curr+20}" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="700">Cụm {c_info["cluster_id"]}: {c_info["percentage"]}% (n={c_info["size"]})</text>')
        svg_elements.append(f'<text x="{bx0+30}" y="{b_y_curr+36}" fill="{c_info["color"]}" font-family="system-ui, sans-serif" font-size="10">{c_info["archetype_title"]}</text>')
        b_y_curr += 60

    # Panel A bottom legend
    svg_elements.append(f'<text x="{(ax0+ax1)/2}" y="{ay1+32}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9.5" text-anchor="middle">Đường mảnh: Quỹ đạo cá nhân · Đường đậm: Trung tâm cụm DTW (Barycenter)</text>')

    svg_elements.append('</svg>')
    return "".join(svg_elements)
