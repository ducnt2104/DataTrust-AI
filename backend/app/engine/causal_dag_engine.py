"""
DataTrust - Directed Acyclic Graph (DAG) & Causal Discovery Engine
==================================================================
Implements constraint-based Causal Discovery via the PC Algorithm:
- Spirtes, P., Glymour, C. N., & Scheines, R. (2000). Causation, Prediction, and Search.
  MIT Press.
- Pearl, J. (2009). Causality: Models, Reasoning, and Inference (2nd ed.).
  Cambridge University Press.
- Kalisch, M., & Bühlmann, P. (2007). Estimating high-dimensional directed acyclic graphs
  with the PC-algorithm. Journal of Machine Learning Research, 8, 613-636.
- Meek, C. (1995). Causal inference and causal explanation with background knowledge.
  UAI'95, 403-410.
"""

from itertools import combinations
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import scipy.stats as stats


class CausalDAGEngine:
    """
    Constraint-based PC Algorithm for Learning Causal DAGs from Survey Indicators.
    """

    @classmethod
    def estimate(
        cls,
        data: np.ndarray,
        item_names: Optional[List[str]] = None,
        alpha: float = 0.05,
        max_cond_size: int = 2
    ) -> Dict[str, Any]:
        """
        Estimate Directed Acyclic Graph (DAG / CPDAG) using PC Algorithm.
        data: N x P matrix of continuous or ordinal survey answers
        item_names: Optional list of labels for each column
        alpha: Significance threshold for conditional independence
        max_cond_size: Maximum order of conditioning sets |S|
        """
        X = np.asarray(data, dtype=float)
        N, P = X.shape

        if N < 20:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 20 quan sát để suy diễn cấu trúc đồ thị nhân quả DAG (hiện có: {N})."
            }
        if P < 3:
            return {
                "status": "insufficient_data",
                "message": f"Cần tối thiểu 3 biến/mục hỏi để dựng mạng lưới nhân quả có hướng (hiện có: {P})."
            }

        if item_names is None or len(item_names) != P:
            item_names = [f"Item {i+1}" for i in range(P)]

        # 1. Compute Correlation Matrix
        corr_matrix = np.corrcoef(X, rowvar=False)
        # Handle NaN correlations
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        np.fill_diagonal(corr_matrix, 1.0)

        # 2. PC Algorithm Phase 1: Skeleton Discovery
        # Initialize fully connected undirected graph
        # adj_matrix: 0 = no edge, 1 = undirected edge, 2 = directed edge (i -> j)
        adj: List[Set[int]] = [set(range(P)) - {i} for i in range(P)]
        sepset: Dict[Tuple[int, int], List[int]] = {}

        for d in range(max_cond_size + 1):
            for i in range(P):
                neighbors = sorted(list(adj[i]))
                for j in neighbors:
                    if j <= i or j not in adj[i]:
                        continue
                    
                    # Possible conditioning sets from adj(i) \ {j}
                    possible_cond = [n for n in adj[i] if n != j]
                    if len(possible_cond) < d:
                        continue

                    edge_removed = False
                    for S in combinations(possible_cond, d):
                        p_val, p_corr = cls._partial_corr_test(corr_matrix, N, i, j, list(S))
                        if p_val > alpha:
                            # Independent: remove edge
                            adj[i].remove(j)
                            adj[j].remove(i)
                            sepset[(i, j)] = list(S)
                            sepset[(j, i)] = list(S)
                            edge_removed = True
                            break
                    if edge_removed:
                        continue

        # 3. PC Algorithm Phase 2: Collider Orientation (v-structures)
        # Directed adjacency matrix: directed_adj[i, j] = 1 means i -> j
        # If undirected: directed_adj[i, j] = 1 AND directed_adj[j, i] = 1
        directed_adj = np.zeros((P, P), dtype=int)
        for i in range(P):
            for j in adj[i]:
                directed_adj[i, j] = 1

        for k in range(P):
            # Find pairs (i, j) such that i - k and j - k but not i - j
            neighbors_k = sorted(list(adj[k]))
            for i_idx, i in enumerate(neighbors_k):
                for j in neighbors_k[i_idx + 1:]:
                    if j not in adj[i]:  # i and j not adjacent
                        # Check if k is in separating set
                        sep = sepset.get((i, j), [])
                        if k not in sep:
                            # Orient as collider i -> k <- j
                            directed_adj[k, i] = 0  # Remove k -> i
                            directed_adj[k, j] = 0  # Remove k -> j

        # 4. PC Algorithm Phase 3: Meek Orientation Rules
        changed = True
        iterations = 0
        while changed and iterations < 15:
            changed = False
            iterations += 1

            # Rule 1: i -> j and j - k, and i not adjacent to k => j -> k
            for j in range(P):
                for i in range(P):
                    if directed_adj[i, j] == 1 and directed_adj[j, i] == 0:  # i -> j
                        for k in range(P):
                            if k != i and k != j:
                                if (directed_adj[j, k] == 1 and directed_adj[k, j] == 1) and \
                                   (directed_adj[i, k] == 0 and directed_adj[k, i] == 0):
                                    directed_adj[k, j] = 0  # Orient j -> k
                                    changed = True

            # Rule 2: i -> k -> j and i - j => i -> j
            for i in range(P):
                for j in range(P):
                    if directed_adj[i, j] == 1 and directed_adj[j, i] == 1:  # i - j
                        for k in range(P):
                            if directed_adj[i, k] == 1 and directed_adj[k, i] == 0 and \
                               directed_adj[k, j] == 1 and directed_adj[j, k] == 0:  # i -> k -> j
                                directed_adj[j, i] = 0  # Orient i -> j
                                changed = True

        # 5. Extract Edge List & Classify Nodes
        edges: List[Dict[str, Any]] = []
        in_degrees = [0] * P
        out_degrees = [0] * P

        for i in range(P):
            for j in range(P):
                if i == j:
                    continue
                if directed_adj[i, j] == 1 and directed_adj[j, i] == 0:
                    # Directed edge i -> j
                    weight = float(corr_matrix[i, j])
                    edges.append({
                        "source_index": i,
                        "source_name": item_names[i],
                        "target_index": j,
                        "target_name": item_names[j],
                        "type": "directed",
                        "weight": round(weight, 3),
                        "direction": f"{item_names[i]} → {item_names[j]}"
                    })
                    out_degrees[i] += 1
                    in_degrees[j] += 1
                elif directed_adj[i, j] == 1 and directed_adj[j, i] == 1 and i < j:
                    # Undirected edge i - j
                    weight = float(corr_matrix[i, j])
                    edges.append({
                        "source_index": i,
                        "source_name": item_names[i],
                        "target_index": j,
                        "target_name": item_names[j],
                        "type": "undirected",
                        "weight": round(weight, 3),
                        "direction": f"{item_names[i]} — {item_names[j]}"
                    })

        # Classify nodes into Causal Roles
        nodes_info: List[Dict[str, Any]] = []
        root_causes: List[str] = []
        sink_outcomes: List[str] = []
        mediators: List[str] = []

        for i in range(P):
            in_d = in_degrees[i]
            out_d = out_degrees[i]
            if out_d > 0 and in_d == 0:
                role = "Nguyên nhân gốc (Root Cause / Exogenous Driver)"
                root_causes.append(item_names[i])
            elif in_d > 0 and out_d == 0:
                role = "Kết quả hạ nguồn (Sink Outcome / Terminal Effect)"
                sink_outcomes.append(item_names[i])
            elif in_d > 0 and out_d > 0:
                role = "Biến trung gian (Mediator / Transmission Node)"
                mediators.append(item_names[i])
            else:
                role = "Nút độc lập / Tương quan vô hướng"

            nodes_info.append({
                "index": i,
                "name": item_names[i],
                "in_degree": in_d,
                "out_degree": out_d,
                "total_degree": in_d + out_d,
                "causal_role": role
            })

        # 6. Generate Vector SVG DAG Chart
        svg_chart = cls._generate_svg_chart(
            item_names=item_names,
            edges=edges,
            nodes_info=nodes_info
        )

        # 7. Generate APA 7th Edition Academic Narrative
        apa_narrative = cls._generate_apa_narrative(
            n_obs=N,
            n_vars=P,
            alpha=alpha,
            edges=edges,
            root_causes=root_causes,
            sink_outcomes=sink_outcomes,
            mediators=mediators
        )

        return {
            "status": "success",
            "sample_size": N,
            "variables_count": P,
            "edges_count": len(edges),
            "directed_edges_count": sum(1 for e in edges if e["type"] == "directed"),
            "undirected_edges_count": sum(1 for e in edges if e["type"] == "undirected"),
            "root_causes": root_causes,
            "sink_outcomes": sink_outcomes,
            "mediators": mediators,
            "nodes": nodes_info,
            "edges": edges,
            "svg_chart": svg_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _partial_corr_test(
        corr_matrix: np.ndarray,
        N: int,
        x: int,
        y: int,
        S: List[int]
    ) -> Tuple[float, float]:
        """
        Fisher's z-transform conditional independence test for partial correlation.
        """
        if len(S) == 0:
            r = corr_matrix[x, y]
        else:
            # Submatrix inversion
            idx = [x, y] + S
            sub_corr = corr_matrix[np.ix_(idx, idx)]
            try:
                prec = np.linalg.pinv(sub_corr)
                r = -prec[0, 1] / max(1e-8, np.sqrt(abs(prec[0, 0] * prec[1, 1])))
            except np.linalg.LinAlgError:
                r = corr_matrix[x, y]

        r = float(np.clip(r, -0.9999, 0.9999))
        # Fisher's z transform
        z = 0.5 * np.log((1.0 + r) / (1.0 - r))
        dof = max(1, N - len(S) - 3)
        se = 1.0 / np.sqrt(dof)
        z_stat = abs(z) / se
        p_val = float(2.0 * (1.0 - stats.norm.cdf(z_stat)))
        return p_val, r

    @classmethod
    def _generate_svg_chart(
        cls,
        item_names: List[str],
        edges: List[Dict[str, Any]],
        nodes_info: List[Dict[str, Any]]
    ) -> str:
        w, h = 920, 480
        center_x, center_y = w // 2, h // 2
        radius = 180
        P = len(item_names)

        # Place nodes on circle or layout
        node_coords = []
        for i in range(P):
            angle = 2.0 * np.pi * i / P - np.pi / 2
            nx = center_x + radius * np.cos(angle)
            ny = center_y + radius * np.sin(angle)
            node_coords.append((nx, ny))

        svg = f"""<svg width="100%" height="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; font-family:Inter,system-ui,sans-serif;">
  <defs>
    <!-- Arrowhead markers -->
    <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8"/>
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#34d399"/>
    </marker>
  </defs>

  <text x="30" y="32" fill="#f8fafc" font-size="14" font-weight="bold">Sơ đồ Mạng lưới Nhân quả Có hướng (Causal DAG / CPDAG) - Thuật toán PC</text>
  <text x="30" y="50" fill="#94a3b8" font-size="11">Mũi tên định hướng luồng tác động nhân quả trực tiếp (X → Y) sau khi đã kiểm soát biến nhiễu.</text>

  <!-- Edges -->
"""
        for e in edges:
            u = e["source_index"]
            v = e["target_index"]
            x1, y1 = node_coords[u]
            x2, y2 = node_coords[v]
            is_directed = (e["type"] == "directed")
            marker_str = 'marker-end="url(#arrow)"' if is_directed else ""
            stroke_color = "#38bdf8" if is_directed else "#64748b"
            stroke_width = max(1.2, min(4.0, abs(e["weight"]) * 4.0))

            svg += f'  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke_color}" stroke-width="{stroke_width:.1f}" stroke-opacity="0.75" {marker_str}/>\n'

        # Nodes
        for i, info in enumerate(nodes_info):
            nx, ny = node_coords[i]
            in_d = info["in_degree"]
            out_d = info["out_degree"]

            if out_d > 0 and in_d == 0:
                node_fill = "#059669"  # Emerald Root
                stroke_color = "#34d399"
                badge = "ROOT"
            elif in_d > 0 and out_d == 0:
                node_fill = "#b45309"  # Amber Sink
                stroke_color = "#fbbf24"
                badge = "SINK"
            elif in_d > 0 and out_d > 0:
                node_fill = "#0284c7"  # Sky Mediator
                stroke_color = "#38bdf8"
                badge = "MED"
            else:
                node_fill = "#334155"  # Slate
                stroke_color = "#64748b"
                badge = ""

            short_label = info["name"][:16] + "..." if len(info["name"]) > 16 else info["name"]

            svg += f'  <circle cx="{nx:.1f}" cy="{ny:.1f}" r="18" fill="{node_fill}" stroke="{stroke_color}" stroke-width="2"/>\n'
            svg += f'  <text x="{nx:.1f}" y="{ny + 4:.1f}" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">{badge or (i+1)}</text>\n'
            
            # Position label outside circle
            lbl_dx = 26 if nx >= center_x else -26
            lbl_anchor = "start" if nx >= center_x else "end"
            svg += f'  <text x="{nx + lbl_dx:.1f}" y="{ny + 4:.1f}" fill="#e2e8f0" font-size="11" font-weight="500" text-anchor="{lbl_anchor}">{short_label}</text>\n'

        svg += """
  <!-- Legend -->
  <g transform="translate(30, 435)">
    <circle cx="10" cy="10" r="7" fill="#059669" stroke="#34d399" stroke-width="1.5"/>
    <text x="24" y="14" fill="#94a3b8" font-size="11">Nguyên nhân gốc (Root Driver)</text>

    <circle cx="210" cy="10" r="7" fill="#0284c7" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="224" y="14" fill="#94a3b8" font-size="11">Biến trung gian (Mediator)</text>

    <circle cx="390" cy="10" r="7" fill="#b45309" stroke="#fbbf24" stroke-width="1.5"/>
    <text x="404" y="14" fill="#94a3b8" font-size="11">Kết quả hạ nguồn (Terminal Sink)</text>
  </g>
</svg>"""
        return svg

    @classmethod
    def _generate_apa_narrative(
        cls,
        n_obs: int,
        n_vars: int,
        alpha: float,
        edges: List[Dict[str, Any]],
        root_causes: List[str],
        sink_outcomes: List[str],
        mediators: List[str]
    ) -> str:
        directed_count = sum(1 for e in edges if e["type"] == "directed")
        undirected_count = sum(1 for e in edges if e["type"] == "undirected")

        roots_str = ", ".join(root_causes) if root_causes else "Không có nguyên nhân gốc tuyệt đối"
        sinks_str = ", ".join(sink_outcomes) if sink_outcomes else "Không có kết quả hạ nguồn thuần túy"
        meds_str = ", ".join(mediators) if mediators else "Không có biến trung gian đa tầng"

        narrative = (
            f"Mạng lưới Nhân quả Có hướng (Directed Acyclic Graph - DAG / CPDAG) được ước lượng thông qua "
            f"thuật toán PC (Spirtes, Glymour & Scheines, 2000; Kalisch & Bühlmann, 2007) trên cỡ mẫu gồm N = {n_obs} quan sát "
            f"và P = {n_vars} biến/mục khảo sát (ngưỡng độc lập có điều kiện α = {alpha}).\n\n"
            f"Cấu trúc mạng lưới nhân quả thu được gồm tổng cộng {len(edges)} liên kết thực chất "
            f"({directed_count} liên kết có hướng nhân quả xác định và {undirected_count} liên kết vô hướng tương đương quan sát).\n\n"
            f"Phân tích thứ bậc nhân quả (Causal Hierarchy Analysis; Pearl, 2009):\n"
            f"- Động lực gốc thượng nguồn (Root Causes): {roots_str}. Các biến này đóng vai trò kích hoạt ban đầu "
            f"và lan truyền tác động tới các thành phần khác mà không bị chi phối ngược lại.\n"
            f"- Khâu trung gian lan tỏa (Mediators): {meds_str}. Đóng vai trò là cầu nối truyền dẫn hiệu ứng nhân quả gián tiếp.\n"
            f"- Điểm hấp thụ kết quả hạ nguồn (Terminal Sinks): {sinks_str}. Đây là các chỉ số đầu ra cuối cùng chịu tác động tổng hợp "
            f"từ toàn bộ chuỗi mắt xích tiền đề trong hệ thống khảo sát."
        )
        return narrative
