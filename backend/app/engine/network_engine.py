import math
from typing import Dict, Any, List, Optional, Tuple


class PsychometricNetworkEngine:
    """
    Động cơ Phân tích Mạng Lưới Tâm lý học Đo lường (Psychometric Network Analysis)
    và Mô hình Đồ thị Gaussian (Gaussian Graphical Models - GGM).
    Tuân thủ phương pháp luận học thuật:
    - Borsboom, D., & Cramer, A. O. (2013). Network analysis: An integrative approach to the structure of psychopathology.
      Annual Review of Clinical Psychology, 9, 91-121.
    - Epskamp, S., Borsboom, D., & Fried, E. I. (2018). Estimating psychological networks and their accuracy:
      A tutorial paper. Behavior Research Methods, 50(1), 195-212.
    - Epskamp, S., Cramer, A. O., Waldorp, L. J., Schmittmann, V. D., & Borsboom, D. (2012).
      qgraph: Network visualizations of relationships in psychometric data. Journal of Statistical Software, 48(4), 1-18.
    - Robinaugh, D. J., Millner, A. J., & McNally, R. J. (2016). Identifying highly influential nodes in the complicated grief network.
      Journal of Abnormal Psychology, 125(6), 747-757.
    - Fruchterman, T. M., & Reingold, E. M. (1991). Graph drawing by force-directed placement.
      Software: Practice and Experience, 21(11), 1129-1164.
    """

    @classmethod
    def analyze_network(
        cls,
        data_matrix: List[List[float]],
        node_names: List[str],
        regularization_threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Phân tích mạng lưới tâm lý học đo lường từ ma trận dữ liệu quan sát [N x P].
        
        Tham số:
        - data_matrix: Ma trận dữ liệu N dòng (phản hồi), P cột (biến khảo sát định lượng)
        - node_names: Tên của P biến/câu hỏi khảo sát
        - regularization_threshold: Ngưỡng loại trừ các cạnh liên kết yếu (mặc định 0.05)
        """
        n = len(data_matrix)
        if n < 4:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 4 phản hồi để phân tích mạng lưới đồ thị (hiện có {n})."
            }

        p = len(node_names)
        if p < 3:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": f"Cần tối thiểu 3 câu hỏi định lượng để thiết lập mạng lưới đồ thị (hiện có {p})."
            }

        # 1. Tính toán ma trận hiệp phương sai và ma trận tương quan Pearson
        means = [sum(row[j] for row in data_matrix) / n for j in range(p)]
        sds = []
        for j in range(p):
            var_j = sum((row[j] - means[j]) ** 2 for row in data_matrix) / (n - 1)
            sds.append(math.sqrt(max(1e-12, var_j)))

        corr_matrix = [[0.0] * p for _ in range(p)]
        for i in range(p):
            corr_matrix[i][i] = 1.0
            for j in range(i + 1, p):
                cov_ij = sum((data_matrix[r][i] - means[i]) * (data_matrix[r][j] - means[j]) for r in range(n)) / (n - 1)
                r_ij = cov_ij / (sds[i] * sds[j]) if (sds[i] * sds[j]) > 1e-12 else 0.0
                r_ij = max(-1.0, min(1.0, r_ij))
                corr_matrix[i][j] = r_ij
                corr_matrix[j][i] = r_ij

        # 2. Nghịch đảo ma trận tương quan (Precision Matrix / Inverse Correlation Matrix)
        # Bổ sung Ridge regularization để đảm bảo tính khả nghịch tuyệt đối
        ridge = 1e-4
        augmented = [[corr_matrix[i][j] + (ridge if i == j else 0.0) for j in range(p)] for i in range(p)]
        # Tạo ma trận đơn vị mở rộng
        inv = [[1.0 if i == j else 0.0 for j in range(p)] for i in range(p)]

        # Khử Gauss-Jordan với phần tử trụ lớn nhất (Partial Pivoting)
        for col in range(p):
            max_row = col
            max_val = abs(augmented[col][col])
            for r in range(col + 1, p):
                if abs(augmented[r][col]) > max_val:
                    max_val = abs(augmented[r][col])
                    max_row = r

            if max_row != col:
                augmented[col], augmented[max_row] = augmented[max_row], augmented[col]
                inv[col], inv[max_row] = inv[max_row], inv[col]

            pivot = augmented[col][col]
            if abs(pivot) < 1e-12:
                pivot = 1e-12

            for c in range(p):
                augmented[col][c] /= pivot
                inv[col][c] /= pivot

            for r in range(p):
                if r != col:
                    factor = augmented[r][col]
                    for c in range(p):
                        augmented[r][c] -= factor * augmented[col][c]
                        inv[r][c] -= factor * inv[col][c]

        # 3. Tính toán Ma trận Tương quan Riêng phần (Partial Correlation Matrix)
        # r_{ij.rest} = - Omega_{ij} / sqrt(Omega_{ii} * Omega_{jj})
        partial_corr = [[0.0] * p for _ in range(p)]
        for i in range(p):
            partial_corr[i][i] = 1.0
            for j in range(i + 1, p):
                denom = math.sqrt(max(1e-12, inv[i][i] * inv[j][j]))
                p_corr = - inv[i][j] / denom
                p_corr = max(-1.0, min(1.0, p_corr))

                # Áp dụng ngưỡng regularization threshold (soft-thresholding)
                if abs(p_corr) < regularization_threshold:
                    p_corr = 0.0

                partial_corr[i][j] = p_corr
                partial_corr[j][i] = p_corr

        # 4. Trích xuất danh sách cạnh (Edge List)
        edges = []
        max_edge_val = 0.0
        for i in range(p):
            for j in range(i + 1, p):
                weight = partial_corr[i][j]
                if abs(weight) > 1e-6:
                    abs_w = abs(weight)
                    if abs_w > max_edge_val:
                        max_edge_val = abs_w
                    edges.append({
                        "source": i,
                        "target": j,
                        "source_name": node_names[i],
                        "target_name": node_names[j],
                        "weight": round(weight, 4),
                        "abs_weight": round(abs_w, 4),
                        "edge_type": "positive" if weight > 0 else "negative"
                    })

        # Sắp xếp các cạnh theo cường độ giảm dần
        edges.sort(key=lambda e: e["abs_weight"], reverse=True)

        # 5. Tính toán các chỉ số Trung tâm Mạng lưới (Node Centrality Indices)
        # - Strength (Cường độ bậc): Tổng giá trị tuyệt đối trọng số các cạnh kết nối
        # - Expected Influence (Tầm ảnh hưởng kỳ vọng): Tổng giá trị có dấu trọng số các cạnh
        # - Closeness (Độ gần gũi): Nghịch đảo tổng khoảng cách ngắn nhất đến các nút khác
        # - Betweenness (Độ trung gian): Tần suất nút nằm trên đường đi ngắn nhất giữa các cặp nút

        strength = [sum(abs(partial_corr[i][j]) for j in range(p) if j != i) for i in range(p)]
        expected_influence = [sum(partial_corr[i][j] for j in range(p) if j != i) for i in range(p)]

        # Xây dựng ma trận khoảng cách cho thuật toán Dijkstra: d(i,j) = 1 / |w_{ij}| nếu có cạnh, ngược lại vô cùng
        dist_matrix = [[float('inf')] * p for _ in range(p)]
        for i in range(p):
            dist_matrix[i][i] = 0.0
            for j in range(p):
                if i != j and abs(partial_corr[i][j]) > 1e-6:
                    dist_matrix[i][j] = 1.0 / abs(partial_corr[i][j])

        # Floyd-Warshall tính đường đi ngắn nhất toàn diện và số đường đi ngắn nhất
        shortest_paths = [[dist_matrix[i][j] for j in range(p)] for i in range(p)]
        for k_node in range(p):
            for i in range(p):
                for j in range(p):
                    if shortest_paths[i][k_node] + shortest_paths[k_node][j] < shortest_paths[i][j]:
                        shortest_paths[i][j] = shortest_paths[i][k_node] + shortest_paths[k_node][j]

        # Closeness Centrality
        closeness = []
        for i in range(p):
            reachable_sum = sum(shortest_paths[i][j] for j in range(p) if j != i and shortest_paths[i][j] < float('inf'))
            reachable_count = sum(1 for j in range(p) if j != i and shortest_paths[i][j] < float('inf'))
            if reachable_count > 0 and reachable_sum > 0:
                closeness.append(reachable_count / reachable_sum)
            else:
                closeness.append(0.0)

        # Betweenness Centrality (xấp xỉ tần suất nằm trên đường đi ngắn nhất)
        betweenness = [0.0] * p
        for s in range(p):
            for t in range(s + 1, p):
                if shortest_paths[s][t] < float('inf') and shortest_paths[s][t] > 0:
                    for v in range(p):
                        if v != s and v != t:
                            # Nếu d(s, v) + d(v, t) == d(s, t) (với dung sai nhỏ)
                            if abs((shortest_paths[s][v] + shortest_paths[v][t]) - shortest_paths[s][t]) < 1e-5:
                                betweenness[v] += 1.0

        # Chuẩn hóa z-score cho các chỉ số trung tâm
        def compute_z_scores(vals: List[float]) -> List[float]:
            n_vals = len(vals)
            m = sum(vals) / n_vals
            s = math.sqrt(sum((x - m) ** 2 for x in vals) / max(1, n_vals - 1))
            if s < 1e-12:
                return [0.0] * n_vals
            return [round((x - m) / s, 3) for x in vals]

        z_strength = compute_z_scores(strength)
        z_closeness = compute_z_scores(closeness)
        z_betweenness = compute_z_scores(betweenness)
        z_influence = compute_z_scores(expected_influence)

        # 6. Thuật toán bố trí lực lò xo Fruchterman-Reingold (Force-Directed Layout)
        # Tạo tọa độ 2D (x, y) trong khung SVG kích thước 500x380
        width = 500.0
        height = 360.0
        area = width * height
        k_spring = math.sqrt(area / p) * 0.75

        # Khởi tạo vị trí phân bổ đều trên đường tròn có jitter
        pos_x = []
        pos_y = []
        center_x = width / 2.0
        center_y = height / 2.0
        radius = min(width, height) * 0.38
        for i in range(p):
            angle = (2.0 * math.pi * i) / p
            pos_x.append(center_x + radius * math.cos(angle))
            pos_y.append(center_y + radius * math.sin(angle))

        # 50 vòng lặp dịch chuyển lực Fruchterman-Reingold
        temp = width / 10.0
        for iteration in range(50):
            disp_x = [0.0] * p
            disp_y = [0.0] * p

            # Lực đẩy giữa tất cả các cặp nút (Repulsive forces)
            for i in range(p):
                for j in range(p):
                    if i != j:
                        dx = pos_x[i] - pos_x[j]
                        dy = pos_y[i] - pos_y[j]
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist < 1e-3:
                            dist = 1e-3
                        rep_force = (k_spring * k_spring) / dist
                        disp_x[i] += (dx / dist) * rep_force
                        disp_y[i] += (dy / dist) * rep_force

            # Lực hút giữa các nút có cạnh liên kết (Attractive forces)
            for edge in edges:
                i = edge["source"]
                j = edge["target"]
                dx = pos_x[i] - pos_x[j]
                dy = pos_y[i] - pos_y[j]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 1e-3:
                    dist = 1e-3
                # Lực hút tỷ lệ với cường độ cạnh tuyệt đối
                att_force = (dist * dist / k_spring) * edge["abs_weight"] * 1.5
                disp_x[i] -= (dx / dist) * att_force
                disp_y[i] -= (dy / dist) * att_force
                disp_x[j] += (dx / dist) * att_force
                disp_y[j] += (dy / dist) * att_force

            # Cập nhật vị trí với bước nhiệt giảm dần (Cooling)
            for i in range(p):
                disp_len = math.sqrt(disp_x[i] * disp_x[i] + disp_y[i] * disp_y[i])
                if disp_len > 1e-3:
                    step = min(disp_len, temp)
                    pos_x[i] += (disp_x[i] / disp_len) * step
                    pos_y[i] += (disp_y[i] / disp_len) * step

                # Giữ nút trong khung viền
                pos_x[i] = max(45.0, min(width - 45.0, pos_x[i]))
                pos_y[i] = max(45.0, min(height - 45.0, pos_y[i]))

            temp *= 0.94

        # 7. Xây dựng danh sách nút (Nodes) kèm vị trí và chỉ số trung tâm
        nodes = []
        for i in range(p):
            nodes.append({
                "id": i,
                "name": node_names[i],
                "x": round(pos_x[i], 1),
                "y": round(pos_y[i], 1),
                "strength": round(strength[i], 3),
                "z_strength": z_strength[i],
                "expected_influence": round(expected_influence[i], 3),
                "z_influence": z_influence[i],
                "closeness": round(closeness[i], 3),
                "z_closeness": z_closeness[i],
                "betweenness": round(betweenness[i], 3),
                "z_betweenness": z_betweenness[i]
            })

        # 8. Chỉ số Mạng lưới Toàn cục (Global Network Metrics)
        possible_edges = (p * (p - 1)) / 2
        active_edges_count = len(edges)
        density = active_edges_count / possible_edges if possible_edges > 0 else 0.0
        mean_weight = sum(e["abs_weight"] for e in edges) / active_edges_count if active_edges_count > 0 else 0.0
        sparsity_pct = (1.0 - density) * 100.0

        # Xác định nút trung tâm có ảnh hưởng lớn nhất
        most_central_node_idx = max(range(p), key=lambda i: strength[i])
        most_central_name = node_names[most_central_node_idx]

        # 9. Tự động sinh báo cáo thuyết minh chuẩn APA 7th Edition
        apa_narrative = (
            f"Mạng lưới tâm lý học đo lường (Psychometric Network Analysis; Borsboom & Cramer, 2013; Epskamp et al., 2018) "
            f"được ước lượng trên tập dữ liệu gồm N = {n} phản hồi khảo sát với P = {p} câu hỏi thang đo. "
            f"Mô hình đồ thị Gaussian (Gaussian Graphical Model - GGM) với ma trận nghịch đảo hiệp phương sai chuẩn hóa "
            f"và kiểm soát ngưỡng liên kết (|r_partial| ≥ {regularization_threshold}) ghi nhận {active_edges_count} cạnh hoạt động "
            f"trên tổng số {int(possible_edges)} cạnh có thể xảy ra, đạt mật độ mạng lưới (network density) là {density:.2%} "
            f"(độ thưa thớt sparsity = {sparsity_pct:.1f}%). "
            f"Độ lớn trọng số liên kết riêng phần tuyệt đối trung bình đạt M = {mean_weight:.3f}. "
        )

        if edges:
            strongest = edges[0]
            apa_narrative += (
                f"Cặp liên kết mạnh nhất trong mạng lưới là giữa '{strongest['source_name']}' và '{strongest['target_name']}' "
                f"với tương quan riêng phần r = {strongest['weight']:+.3f}. "
            )

        apa_narrative += (
            f"Phân tích chỉ số trung tâm (Node Centrality; Robinaugh et al., 2016) xác định câu hỏi "
            f"'{most_central_name}' có cường độ liên kết cao nhất (Strength = {strength[most_central_node_idx]:.3f}, "
            f"z = {z_strength[most_central_node_idx]:+.2f}; Expected Influence = {expected_influence[most_central_node_idx]:.3f}), "
            f"đóng vai trò là nút trung tâm điều tiết cốt lõi (core symptom/indicator) trong toàn bộ cấu trúc hệ thống khảo sát."
        )

        return {
            "status": "SUCCESS",
            "sample_size": n,
            "num_nodes": p,
            "num_edges": active_edges_count,
            "possible_edges": int(possible_edges),
            "density": round(density, 4),
            "density_percent": round(density * 100, 1),
            "sparsity_percent": round(sparsity_pct, 1),
            "mean_weight": round(mean_weight, 4),
            "most_central_node": most_central_name,
            "nodes": nodes,
            "edges": edges,
            "apa_narrative": apa_narrative
        }

    @classmethod
    def _build_empty_response(cls, reason: str = "Không có đủ dữ liệu phản hồi.") -> Dict[str, Any]:
        """Trả về phản hồi rỗng tiêu chuẩn khi không đủ dữ liệu."""
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "message": reason,
            "sample_size": 0,
            "num_nodes": 0,
            "num_edges": 0,
            "density": 0.0,
            "nodes": [],
            "edges": [],
            "apa_narrative": f"Không thể thực hiện phân tích mạng lưới tâm lý học: {reason}"
        }
