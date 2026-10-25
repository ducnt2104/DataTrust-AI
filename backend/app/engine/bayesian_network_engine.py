"""
Bayesian Network Directed Acyclic Graph (DAG) Structure Learning Engine.
Based on the foundational methodologies of:
- Heckerman, D. (1995). A tutorial on learning with Bayesian networks. In Learning in Graphical Models (pp. 301-354). Springer.
- Geiger, D., & Heckerman, D. (1994). Learning Gaussian networks. Technical Report MSR-TR-94-10, Microsoft Research.
- Scutari, M. (2010). Learning Bayesian networks with the bnlearn R package. Journal of Statistical Software, 35(3), 1-22.
- Koller, D., & Friedman, N. (2009). Probabilistic Graphical Models: Principles and Techniques. MIT Press.
- Pearl, J. (2009). Causality: Models, Reasoning, and Inference (2nd ed.). Cambridge University Press.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import math
import numpy as np


class BayesianNetworkEngine:
    """
    Score-Based Gaussian Bayesian Network (GBN) Structure Learning & Markov Blanket Engine.
    Employs Hill-Climbing heuristic search over DAG space optimizing Bayesian Information Criterion (BIC).
    """

    @staticmethod
    def _has_cycle(adj: np.ndarray) -> bool:
        """Cycle detection in directed graph using Kahn's topological sort algorithm."""
        P = adj.shape[0]
        in_degrees = np.sum(adj, axis=0)  # number of incoming edges to each node
        queue = [i for i in range(P) if in_degrees[i] == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for child in range(P):
                if adj[node, child] == 1:
                    in_degrees[child] -= 1
                    if in_degrees[child] == 0:
                        queue.append(child)

        return visited_count != P

    @staticmethod
    def _local_bic_score(
        X: np.ndarray,
        node: int,
        parents: List[int]
    ) -> float:
        """
        Compute local Gaussian BIC score for a single node given its parents.
        X_j = beta_0 + sum_{k in Pa} beta_k X_k + eps_j
        """
        N, P = X.shape
        y = X[:, node]

        if len(parents) == 0:
            var_res = float(np.var(y, ddof=1)) if N > 1 else float(np.var(y))
            var_res = max(1e-6, var_res)
            # Parameters: intercept + residual variance = 2
            k_params = 2
        else:
            X_pa = X[:, parents]
            X_design = np.column_stack([np.ones(N), X_pa])
            try:
                beta = np.linalg.pinv(X_design.T @ X_design) @ (X_design.T @ y)
                residuals = y - X_design @ beta
                var_res = float(np.sum(residuals ** 2) / max(1, N - len(parents) - 1))
                var_res = max(1e-6, var_res)
            except Exception:
                var_res = max(1e-6, float(np.var(y)))
            # Parameters: intercept + |Pa| regression coeffs + residual variance = 1 + |Pa| + 1
            k_params = len(parents) + 2

        # Log-likelihood for Gaussian node
        ll = -0.5 * N * math.log(2.0 * math.pi) - 0.5 * N * math.log(var_res) - 0.5 * N
        # BIC penalty: - 0.5 * k * log(N)
        bic = ll - 0.5 * k_params * math.log(N)
        return float(bic)

    @classmethod
    def _learn_dag_hill_climbing(
        cls,
        X: np.ndarray,
        max_parents: int = 4,
        max_iter: int = 120
    ) -> Tuple[np.ndarray, float, float]:
        """
        Execute Hill-Climbing heuristic search over DAG space optimizing total BIC score.
        Returns:
            adj: PxP adjacency matrix (adj[i, j] == 1 means i -> j)
            final_bic: float
            initial_bic: float
        """
        N, P = X.shape
        adj = np.zeros((P, P), dtype=int)

        # Initial node parents and scores (empty graph)
        parent_sets = [[] for _ in range(P)]
        node_scores = [cls._local_bic_score(X, j, parent_sets[j]) for j in range(P)]
        initial_bic = float(sum(node_scores))
        current_bic = initial_bic

        for iteration in range(max_iter):
            best_delta = 0.0
            best_op = None  # ("add", i, j), ("del", i, j), ("rev", i, j)
            best_new_score = None

            for i in range(P):
                for j in range(P):
                    if i == j:
                        continue

                    # Operation 1: ADD edge i -> j
                    if adj[i, j] == 0 and adj[j, i] == 0:
                        if len(parent_sets[j]) < max_parents:
                            # Tentatively add edge to check cycle
                            adj[i, j] = 1
                            if not cls._has_cycle(adj):
                                new_parents = parent_sets[j] + [i]
                                score_j = cls._local_bic_score(X, j, new_parents)
                                delta = score_j - node_scores[j]
                                if delta > best_delta:
                                    best_delta = delta
                                    best_op = ("add", i, j)
                                    best_new_score = score_j
                            adj[i, j] = 0

                    # Operation 2: DELETE edge i -> j
                    elif adj[i, j] == 1:
                        new_parents = [p for p in parent_sets[j] if p != i]
                        score_j = cls._local_bic_score(X, j, new_parents)
                        delta = score_j - node_scores[j]
                        if delta > best_delta:
                            best_delta = delta
                            best_op = ("del", i, j)
                            best_new_score = score_j

                        # Operation 3: REVERSE edge i -> j to j -> i
                        if len(parent_sets[i]) < max_parents:
                            adj[i, j] = 0
                            adj[j, i] = 1
                            if not cls._has_cycle(adj):
                                new_pa_j = [p for p in parent_sets[j] if p != i]
                                new_pa_i = parent_sets[i] + [j]
                                score_j = cls._local_bic_score(X, j, new_pa_j)
                                score_i = cls._local_bic_score(X, i, new_pa_i)
                                delta = (score_j - node_scores[j]) + (score_i - node_scores[i])
                                if delta > best_delta:
                                    best_delta = delta
                                    best_op = ("rev", i, j)
                                    best_new_score = (score_i, score_j)
                            # Revert
                            adj[j, i] = 0
                            adj[i, j] = 1

            # If no improvement found, stop (local optimum)
            if best_delta <= 1e-4 or best_op is None:
                break

            # Apply best operation
            op_type, i, j = best_op
            if op_type == "add":
                adj[i, j] = 1
                parent_sets[j].append(i)
                node_scores[j] = best_new_score
            elif op_type == "del":
                adj[i, j] = 0
                parent_sets[j].remove(i)
                node_scores[j] = best_new_score
            elif op_type == "rev":
                adj[i, j] = 0
                adj[j, i] = 1
                parent_sets[j].remove(i)
                parent_sets[i].append(j)
                node_scores[i] = best_new_score[0]
                node_scores[j] = best_new_score[1]

            current_bic += best_delta

        final_bic = float(sum(node_scores))
        return adj, final_bic, initial_bic

    @classmethod
    def _extract_markov_blanket(cls, adj: np.ndarray, node: int) -> Set[int]:
        """
        Extract Markov Blanket of a node: Parents + Children + Spouses (other parents of node's children).
        """
        P = adj.shape[0]
        parents = set(np.where(adj[:, node] == 1)[0])
        children = set(np.where(adj[node, :] == 1)[0])
        spouses = set()
        for child in children:
            other_parents = set(np.where(adj[:, child] == 1)[0])
            for op in other_parents:
                if op != node:
                    spouses.add(op)

        return parents.union(children).union(spouses)

    @classmethod
    def _estimate_path_coefficients(cls, X: np.ndarray, adj: np.ndarray) -> np.ndarray:
        """Estimate standardized linear regression path coefficients for all edges in DAG."""
        N, P = X.shape
        coeffs = np.zeros((P, P))
        # Standardize X for standardized beta path coefficients
        X_std = (X - np.mean(X, axis=0)) / np.maximum(1e-6, np.std(X, axis=0, ddof=1))

        for j in range(P):
            parents = list(np.where(adj[:, j] == 1)[0])
            if parents:
                X_pa = X_std[:, parents]
                y = X_std[:, j]
                try:
                    beta = np.linalg.pinv(X_pa.T @ X_pa) @ (X_pa.T @ y)
                    for idx_k, p_idx in enumerate(parents):
                        coeffs[p_idx, j] = float(beta[idx_k])
                except Exception:
                    pass

        return coeffs

    @classmethod
    def _build_svg_visualization(
        cls,
        adj: np.ndarray,
        coeffs: np.ndarray,
        node_labels: List[str]
    ) -> str:
        """Construct dual-panel SVG: Directed Acyclic Graph (DAG) + Markov Blanket Dependency Table."""
        width = 960
        height = 430

        # Panel A: Directed DAG Layout
        pa_x, pa_y, pa_w, pa_h = 60, 60, 480, 320
        # Panel B: Markov Blanket & Network Metrics Table
        pb_x, pb_y, pb_w, pb_h = 560, 60, 350, 320

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; background: #0f172a; border-radius: 12px;">',
            '<!-- Marker definitions for arrowheads -->',
            '<defs>',
            '  <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
            '    <polygon points="0 0, 8 3, 0 6" fill="#38bdf8" />',
            '  </marker>',
            '  <marker id="arrowhead-neg" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
            '    <polygon points="0 0, 8 3, 0 6" fill="#f43f5e" />',
            '  </marker>',
            '</defs>',
            '<!-- Header -->',
            f'<text x="60" y="36" fill="#f8fafc" font-size="16" font-weight="700">Bayesian Network Structure Learning — Directed Acyclic Graph (DAG)</text>',
            f'<text x="{width - 60}" y="36" fill="#94a3b8" font-size="12" text-anchor="end">Score: GBN Bayesian Information Criterion (BIC) | Hill-Climbing</text>',
            '<!-- Grid Background Panel A -->',
            f'<rect x="{pa_x}" y="{pa_y}" width="{pa_w}" height="{pa_h}" fill="#1e293b" rx="8" />',
            f'<text x="{pa_x + 16}" y="{pa_y + 24}" fill="#f8fafc" font-size="13" font-weight="700">Learned Causal &amp; Probabilistic Dependency DAG</text>'
        ]

        P = len(node_labels)
        # Position nodes in an ellipse within Panel A
        center_x = pa_x + pa_w / 2
        center_y = pa_y + pa_h / 2 + 10
        rx = pa_w * 0.38
        ry = pa_h * 0.36

        node_coords = []
        for i in range(P):
            angle = (2.0 * math.pi * i) / P - math.pi / 2
            x = center_x + rx * math.cos(angle)
            y = center_y + ry * math.sin(angle)
            node_coords.append((x, y))

        # Draw Directed Edges
        for i in range(P):
            for j in range(P):
                if adj[i, j] == 1:
                    x1, y1 = node_coords[i]
                    x2, y2 = node_coords[j]
                    dx = x2 - x1
                    dy = y2 - y1
                    dist = math.hypot(dx, dy)
                    if dist > 1e-6:
                        # Offset edge start/end so arrows don't collide with node circles (radius 18)
                        r_offset = 18.0
                        ux, uy = dx / dist, dy / dist
                        sx = x1 + ux * r_offset
                        sy = y1 + uy * r_offset
                        ex = x2 - ux * r_offset
                        ey = y2 - uy * r_offset

                        beta_val = coeffs[i, j]
                        edge_col = "#38bdf8" if beta_val >= 0 else "#f43f5e"
                        marker_id = "arrowhead" if beta_val >= 0 else "arrowhead-neg"
                        stroke_w = min(4.0, max(1.5, abs(beta_val) * 3.5))

                        svg_lines.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{edge_col}" stroke-width="{stroke_w:.1f}" marker-end="url(#{marker_id})" opacity="0.85" />')

                        # Edge label (beta) at midpoint
                        mx = (sx + ex) / 2 + uy * 8
                        my = (sy + ey) / 2 - ux * 8
                        svg_lines.append(f'<text x="{mx:.1f}" y="{my:.1f}" fill="{edge_col}" font-size="9" font-weight="700" text-anchor="middle">{beta_val:+.2f}</text>')

        # Draw Node Circles & Labels
        node_colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#06b6d4", "#ec4899", "#f43f5e"]
        for i in range(P):
            x, y = node_coords[i]
            col = node_colors[i % len(node_colors)]
            label = node_labels[i]
            short_lbl = label[:10] + '..' if len(label) > 10 else label

            svg_lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="#0f172a" stroke="{col}" stroke-width="2.5" />')
            svg_lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="{col}" opacity="0.25" />')
            svg_lines.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" fill="#f8fafc" font-size="10" font-weight="700" text-anchor="middle">X{i+1}</text>')
            svg_lines.append(f'<text x="{x:.1f}" y="{y + 28:.1f}" fill="#cbd5e1" font-size="9" font-weight="500" text-anchor="middle">{short_lbl}</text>')

        # Panel A Footer
        svg_lines.append(f'<text x="{pa_x + 16}" y="{pa_y + pa_h - 10}" fill="#64748b" font-size="10">Directional paths indicate direct linear conditioning | Cyan: Positive (+), Rose: Negative (-)</text>')

        # --- Panel B: Markov Blanket & Network Metrics Table ---
        svg_lines.append('<!-- Panel B Container -->')
        svg_lines.append(f'<rect x="{pb_x}" y="{pb_y}" width="{pb_w}" height="{pb_h}" fill="#1e293b" rx="8" />')
        svg_lines.append(f'<text x="{pb_x + 16}" y="{pb_y + 24}" fill="#f8fafc" font-size="13" font-weight="700">Markov Blankets &amp; Topological Roles</text>')

        row_h = (pb_h - 60) / max(P, 1)
        for i in range(P):
            curr_y = pb_y + 40 + i * row_h
            col = node_colors[i % len(node_colors)]
            mb = cls._extract_markov_blanket(adj, i)
            mb_str = ", ".join([f"X{idx+1}" for idx in sorted(list(mb))]) if mb else "None (Isolated)"
            short_mb = mb_str[:22] + '..' if len(mb_str) > 22 else mb_str

            svg_lines.append(f'<rect x="{pb_x + 12}" y="{curr_y + 2:.1f}" width="{pb_w - 24}" height="{row_h - 4:.1f}" fill="#0f172a" rx="4" />')
            svg_lines.append(f'<circle cx="{pb_x + 24}" cy="{curr_y + row_h / 2:.1f}" r="4" fill="{col}" />')
            svg_lines.append(f'<text x="{pb_x + 34}" y="{curr_y + row_h / 2 + 3:.1f}" fill="#f8fafc" font-size="10" font-weight="700">X{i+1}: {node_labels[i][:12]}</text>')
            svg_lines.append(f'<text x="{pb_x + pb_w - 20}" y="{curr_y + row_h / 2 + 3:.1f}" fill="#94a3b8" font-size="9" text-anchor="end">MB: {short_mb}</text>')

        # Panel B Footer
        total_edges = int(np.sum(adj))
        density = total_edges / max(1, P * (P - 1))
        svg_lines.append(f'<text x="{pb_x + 16}" y="{pb_y + pb_h - 10}" fill="#64748b" font-size="10">Edges: {total_edges} | Density: {density:.2f} | Acyclic: Guaranteed</text>')

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    @classmethod
    def _generate_apa_narrative(
        cls,
        adj: np.ndarray,
        node_labels: List[str],
        final_bic: float,
        init_bic: float,
        n_obs: int
    ) -> str:
        """Compose academic APA 7th Edition narrative for Bayesian Network Structure Learning."""
        P = len(node_labels)
        total_edges = int(np.sum(adj))
        bic_gain = final_bic - init_bic

        in_degrees = np.sum(adj, axis=0)
        out_degrees = np.sum(adj, axis=1)

        # Identify key root causes (out_degree > 0 and in_degree == 0)
        root_nodes = [node_labels[i] for i in range(P) if out_degrees[i] > 0 and in_degrees[i] == 0]
        # Identify key target sinks (in_degree > 0 and out_degree == 0)
        sink_nodes = [node_labels[i] for i in range(P) if in_degrees[i] > 0 and out_degrees[i] == 0]
        # Identify key mediators (in_degree > 0 and out_degree > 0)
        mediator_nodes = [node_labels[i] for i in range(P) if in_degrees[i] > 0 and out_degrees[i] > 0]

        lines = [
            f"**Thuyết Minh Học Thuật & Đánh Giá Mạng Bayes Chuẩn APA 7th Edition:**\n",
            f"Cấu trúc Mạng Bayes Đa biến (Gaussian Bayesian Network - GBN; Heckerman, 1995; Scutari, 2010) "
            f"được khám phá trên mẫu $N = {n_obs}$ đáp viên với $P = {P}$ biến chỉ báo khảo sát, "
            f"sử dụng thuật toán Leo đồi (Hill-Climbing Search) tối ưu hóa hàm Tiêu chuẩn Thông tin Bayesian Information Criterion (BIC). "
            f"Mô hình đồ thị có hướng không chu trình (Directed Acyclic Graph - DAG) tối ưu đạt tổng điểm số $\\text{{BIC}} = {final_bic:.2f}$, "
            f"cải thiện vượt bậc $\\Delta \\text{{BIC}} = {bic_gain:+.2f}$ so với đồ thị rỗng ban đầu, thiết lập tổng cộng $E = {total_edges}$ liên kết định hướng.\n\n",
            f"Cấu trúc tô-pô của mạng lưới phân rã rõ ràng vai trò của từng biến số trong chuỗi xác suất có điều kiện:\n"
        ]

        if root_nodes:
            lines.append(f"- **Nhóm Biến Cội Nguồn (Exogenous / Root Drivers):** {', '.join(root_nodes)}. Đây là các yếu tố khởi phát ngoại sinh, trực tiếp chi phối các mắt xích tiếp theo mà không bị ảnh hưởng ngược lại bởi các biến khác trong hệ thống.\n")
        if mediator_nodes:
            lines.append(f"- **Nhóm Biến Trung Gian (Mediating Hubs):** {', '.join(mediator_nodes)}. Đóng vai trò là cầu nối truyền dẫn hiệu ứng tác động giữa các biến cội nguồn và biến kết quả.\n")
        if sink_nodes:
            lines.append(f"- **Nhóm Biến Kết Quả Đích (Endogenous / Target Sinks):** {', '.join(sink_nodes)}. Là điểm hội tụ cuối cùng của các luồng tác động xác suất trong khảo sát.\n")

        lines.append(
            "\n**Ý Nghĩa Phân Tích Markov Blanket:** Tập hợp Markov Blanket của mỗi biến xác định ranh giới cách ly thông tin tối thiểu (Minimal Conditioning Set). "
            "Khi kiểm soát toàn bộ các biến trong Markov Blanket của một biến mục tiêu, mọi biến số còn lại trong khảo sát trở nên độc lập có điều kiện, "
            "giúp các nhà nghiên cứu nhận diện chính xác tập hợp các biến cần can thiệp để tối ưu hóa kết quả mà không gây lãng phí nguồn lực."
        )

        return "".join(lines)

    @classmethod
    def learn_bayesian_network(
        cls,
        data_matrix: List[List[float]],
        node_labels: List[str],
        max_parents: int = 4
    ) -> Dict[str, Any]:
        """
        Execute full Bayesian Network Structure Learning pipeline:
        1. Validate inputs and matrix shapes.
        2. Execute Hill-Climbing BIC search over DAG space.
        3. Estimate standardized regression path coefficients for all edges.
        4. Extract Markov Blankets for all nodes.
        5. Generate dual-panel SVG and APA narrative.
        """
        X = np.array(data_matrix, dtype=float)
        N, P = X.shape

        if N < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Kích thước mẫu N = {N} không đủ để học cấu trúc Mạng Bayes (yêu cầu tối thiểu N >= 20)."
            }

        if P < 3:
            return {
                "status": "INSUFFICIENT_NODES",
                "message": f"Số lượng biến P = {P} không đủ (yêu cầu tối thiểu P >= 3 để tạo cấu trúc DAG)."
            }

        # Run Hill-Climbing DAG structure learning
        adj, final_bic, init_bic = cls._learn_dag_hill_climbing(X, max_parents=max_parents)

        # Estimate path coefficients
        coeffs = cls._estimate_path_coefficients(X, adj)

        # Extract edge list
        edges_out = []
        for i in range(P):
            for j in range(P):
                if adj[i, j] == 1:
                    edges_out.append({
                        "from_node": node_labels[i],
                        "to_node": node_labels[j],
                        "from_index": i + 1,
                        "to_index": j + 1,
                        "standardized_path_coeff": round(float(coeffs[i, j]), 3),
                        "relationship_type": "Positive" if coeffs[i, j] >= 0 else "Negative"
                    })

        # Extract node details & Markov Blankets
        nodes_out = []
        for i in range(P):
            mb_indices = cls._extract_markov_blanket(adj, i)
            parents = [node_labels[idx] for idx in np.where(adj[:, i] == 1)[0]]
            children = [node_labels[idx] for idx in np.where(adj[i, :] == 1)[0]]
            mb_labels = [node_labels[idx] for idx in sorted(list(mb_indices))]

            in_deg = len(parents)
            out_deg = len(children)
            if in_deg == 0 and out_deg > 0:
                role = "Root Cause (Ngoại sinh)"
            elif in_deg > 0 and out_deg == 0:
                role = "Target Sink (Kết quả đích)"
            elif in_deg > 0 and out_deg > 0:
                role = "Mediator (Trung gian)"
            else:
                role = "Isolated (Độc lập)"

            nodes_out.append({
                "node_id": i + 1,
                "label": node_labels[i],
                "topological_role": role,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "parents": parents,
                "children": children,
                "markov_blanket": mb_labels
            })

        total_edges = int(np.sum(adj))
        graph_density = total_edges / max(1, P * (P - 1))

        # Generate SVG visualization
        svg_chart = cls._build_svg_visualization(adj, coeffs, node_labels)

        # Academic APA narrative
        apa_narrative = cls._generate_apa_narrative(adj, node_labels, final_bic, init_bic, N)

        return {
            "status": "SUCCESS",
            "model_type": "GAUSSIAN_BAYESIAN_NETWORK_DAG",
            "diagnostics": {
                "sample_size": N,
                "n_nodes": P,
                "total_edges": total_edges,
                "graph_density": round(graph_density, 3),
                "final_bic_score": round(final_bic, 2),
                "empty_graph_bic": round(init_bic, 2),
                "bic_gain": round(final_bic - init_bic, 2),
                "is_acyclic": True
            },
            "nodes": nodes_out,
            "edges": edges_out,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative
        }
