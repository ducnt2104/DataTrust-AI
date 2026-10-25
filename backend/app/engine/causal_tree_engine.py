"""
Causal Interaction Trees & Honest Subgroup Identification Engine.
Based on the foundational methodologies of:
- Athey, S., & Imbens, G. (2016). Recursive partitioning for heterogeneous causal effects. Proceedings of the National Academy of Sciences (PNAS), 113(27), 7353-7360.
- Su, X., Tsai, C. L., Wang, H., Nickerson, D. M., & Li, B. (2009). Subgroup analysis via recursive partitioning. Journal of Machine Learning Research (JMLR), 10, 141-158.
"""

from typing import Dict, List, Any, Optional
import math
import numpy as np


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


class CausalTreeNode:
    def __init__(
        self,
        node_id: int,
        depth: int = 0,
        rule: str = "Tất cả mẫu (Root)",
        feature_name: Optional[str] = None,
        threshold: Optional[float] = None
    ):
        self.node_id = node_id
        self.depth = depth
        self.rule = rule
        self.feature_name = feature_name
        self.threshold = threshold
        self.left: Optional['CausalTreeNode'] = None
        self.right: Optional['CausalTreeNode'] = None
        self.is_leaf = False

        # Metrics
        self.n_total = 0
        self.n_treated = 0
        self.n_control = 0
        self.tau = 0.0
        self.se = 0.0
        self.ci_lower = 0.0
        self.ci_upper = 0.0
        self.p_value = 1.0
        self.category = "NEUTRAL_NO_EFFECT"


def _build_causal_tree(
    X_tr: np.ndarray,
    T_tr: np.ndarray,
    Y_tr: np.ndarray,
    X_est: np.ndarray,
    T_est: np.ndarray,
    Y_est: np.ndarray,
    feature_names: List[str],
    depth: int = 0,
    max_depth: int = 3,
    min_leaf_size: int = 4,
    node_counter: List[int] = None,
    rule_desc: str = "Toàn bộ mẫu"
) -> CausalTreeNode:
    if node_counter is None:
        node_counter = [0]

    node_id = node_counter[0]
    node_counter[0] += 1
    node = CausalTreeNode(node_id=node_id, depth=depth, rule=rule_desc)

    # Calculate metrics on estimation set (Honest estimation)
    n_est = len(Y_est)
    treated_mask_est = (T_est == 1.0)
    control_mask_est = (T_est == 0.0)

    n_tr_est = int(np.sum(treated_mask_est))
    n_co_est = int(np.sum(control_mask_est))

    node.n_total = n_est
    node.n_treated = n_tr_est
    node.n_control = n_co_est

    if n_tr_est > 0 and n_co_est > 0:
        mean_y1 = float(np.mean(Y_est[treated_mask_est]))
        mean_y0 = float(np.mean(Y_est[control_mask_est]))
        node.tau = float(mean_y1 - mean_y0)

        var_y1 = float(np.var(Y_est[treated_mask_est], ddof=1)) if n_tr_est > 1 else 0.01
        var_y0 = float(np.var(Y_est[control_mask_est], ddof=1)) if n_co_est > 1 else 0.01
        node.se = float(math.sqrt(var_y1 / n_tr_est + var_y0 / n_co_est))
        node.ci_lower = float(node.tau - 1.96 * node.se)
        node.ci_upper = float(node.tau + 1.96 * node.se)

        z = abs(node.tau) / max(1e-9, node.se)
        node.p_value = float(2.0 * (1.0 - _normal_cdf(z)))

        # Categorization
        if node.p_value < 0.05 and node.tau > 0:
            node.category = "STRONG_POSITIVE_RESPONDERS"
        elif node.p_value < 0.05 and node.tau < 0:
            node.category = "ADVERSE_BACKFIRE_RESPONDERS"
        elif node.tau > 0:
            node.category = "MODERATE_POSITIVE"
        elif node.tau < 0:
            node.category = "MODERATE_NEGATIVE"
        else:
            node.category = "NEUTRAL_NO_EFFECT"
    else:
        node.tau = 0.0
        node.se = 1.0
        node.ci_lower = -1.96
        node.ci_upper = 1.96
        node.p_value = 1.0
        node.category = "NEUTRAL_NO_EFFECT"

    # Stop splitting conditions
    n_tr = len(Y_tr)
    tr_treated = np.sum(T_tr == 1.0)
    tr_control = np.sum(T_tr == 0.0)

    if (
        depth >= max_depth
        or n_tr < 2 * min_leaf_size
        or tr_treated < min_leaf_size
        or tr_control < min_leaf_size
        or n_est < 2 * min_leaf_size
    ):
        node.is_leaf = True
        return node

    # Find best split on training set X_tr to maximize between-leaf tau variance
    n_features = X_tr.shape[1]
    best_crit = -1e9
    best_feat = -1
    best_thresh = None

    for j in range(n_features):
        feat_vals = X_tr[:, j]
        # Test candidate cut points (percentiles 20 to 80)
        percentiles = np.percentile(feat_vals, [25, 35, 50, 65, 75])
        unique_cuts = np.unique(percentiles)

        for cut in unique_cuts:
            left_mask = feat_vals <= cut
            right_mask = ~left_mask

            n_l = np.sum(left_mask)
            n_r = np.sum(right_mask)

            n_l_tr = np.sum(left_mask & (T_tr == 1.0))
            n_l_co = np.sum(left_mask & (T_tr == 0.0))
            n_r_tr = np.sum(right_mask & (T_tr == 1.0))
            n_r_co = np.sum(right_mask & (T_tr == 0.0))

            if min(n_l_tr, n_l_co, n_r_tr, n_r_co) < min_leaf_size:
                continue

            tau_l = np.mean(Y_tr[left_mask & (T_tr == 1.0)]) - np.mean(Y_tr[left_mask & (T_tr == 0.0)])
            tau_r = np.mean(Y_tr[right_mask & (T_tr == 1.0)]) - np.mean(Y_tr[right_mask & (T_tr == 0.0)])

            # Split criterion: weighted difference in tau squared
            crit = (float(n_l) * float(n_r) / float(n_tr)) * (float(tau_l - tau_r) ** 2)

            if crit > best_crit:
                best_crit = crit
                best_feat = j
                best_thresh = float(cut)

    if best_feat == -1 or best_thresh is None:
        node.is_leaf = True
        return node

    # Split training and estimation sets
    node.feature_name = feature_names[best_feat]
    node.threshold = best_thresh

    left_mask_tr = X_tr[:, best_feat] <= best_thresh
    right_mask_tr = ~left_mask_tr

    left_mask_est = X_est[:, best_feat] <= best_thresh
    right_mask_est = ~left_mask_est

    # Verify both leaves have observations in estimation set
    if np.sum(left_mask_est) < min_leaf_size or np.sum(right_mask_est) < min_leaf_size:
        node.is_leaf = True
        return node

    feat_label = feature_names[best_feat]
    left_rule = f"{feat_label} ≤ {best_thresh:.2f}"
    right_rule = f"{feat_label} > {best_thresh:.2f}"

    node.left = _build_causal_tree(
        X_tr=X_tr[left_mask_tr],
        T_tr=T_tr[left_mask_tr],
        Y_tr=Y_tr[left_mask_tr],
        X_est=X_est[left_mask_est],
        T_est=T_est[left_mask_est],
        Y_est=Y_est[left_mask_est],
        feature_names=feature_names,
        depth=depth + 1,
        max_depth=max_depth,
        min_leaf_size=min_leaf_size,
        node_counter=node_counter,
        rule_desc=left_rule
    )

    node.right = _build_causal_tree(
        X_tr=X_tr[right_mask_tr],
        T_tr=T_tr[right_mask_tr],
        Y_tr=Y_tr[right_mask_tr],
        X_est=X_est[right_mask_est],
        T_est=T_est[right_mask_est],
        Y_est=Y_est[right_mask_est],
        feature_names=feature_names,
        depth=depth + 1,
        max_depth=max_depth,
        min_leaf_size=min_leaf_size,
        node_counter=node_counter,
        rule_desc=right_rule
    )

    return node


def _collect_leaves(node: CausalTreeNode) -> List[Dict[str, Any]]:
    leaves = []
    if node.is_leaf or (node.left is None and node.right is None):
        return [{
            "leaf_id": node.node_id,
            "rule": node.rule,
            "n_total": node.n_total,
            "n_treated": node.n_treated,
            "n_control": node.n_control,
            "tau_subgroup": round(node.tau, 4),
            "se": round(node.se, 4),
            "ci_lower": round(node.ci_lower, 4),
            "ci_upper": round(node.ci_upper, 4),
            "p_value": round(node.p_value, 4),
            "is_significant": bool(node.p_value < 0.05),
            "category": node.category
        }]

    if node.left:
        leaves.extend(_collect_leaves(node.left))
    if node.right:
        leaves.extend(_collect_leaves(node.right))
    return leaves


def _tree_to_dict(node: CausalTreeNode) -> Dict[str, Any]:
    res = {
        "node_id": node.node_id,
        "depth": node.depth,
        "rule": node.rule,
        "feature_name": node.feature_name,
        "threshold": node.threshold,
        "is_leaf": node.is_leaf or (node.left is None and node.right is None),
        "n_total": node.n_total,
        "n_treated": node.n_treated,
        "n_control": node.n_control,
        "tau": round(node.tau, 4),
        "se": round(node.se, 4),
        "p_value": round(node.p_value, 4),
        "category": node.category
    }
    if node.left:
        res["left"] = _tree_to_dict(node.left)
    if node.right:
        res["right"] = _tree_to_dict(node.right)
    return res


def run_causal_interaction_tree(
    records: List[Dict[str, Any]],
    treatment_col: str,
    outcome_col: str,
    feature_cols: List[str],
    max_depth: int = 3,
    min_leaf_size: int = 5,
    target_treatment_val: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Builds an honest causal tree and returns subgroup treatment effects.
    """
    if len(feature_cols) == 0:
        return {
            "status": "error",
            "message": "Cần chọn ít nhất một biến hiệp biến/đặc trưng để phân tách nhóm đối tượng."
        }

    valid_rows = []
    for r in records:
        t_raw = r.get(treatment_col)
        y_raw = r.get(outcome_col)
        if t_raw is None or y_raw is None:
            continue

        try:
            y_val = float(y_raw)
        except (ValueError, TypeError):
            continue

        if target_treatment_val is not None:
            t_val = 1.0 if str(t_raw).strip() == str(target_treatment_val).strip() else 0.0
        else:
            try:
                t_num = float(t_raw)
                t_val = 1.0 if t_num > 0.5 else 0.0
            except (ValueError, TypeError):
                t_str = str(t_raw).strip().lower()
                t_val = 1.0 if t_str in ["1", "true", "yes", "treatment", "treated"] else 0.0

        f_vals = []
        valid_f = True
        for col in feature_cols:
            fv = r.get(col)
            if fv is None:
                valid_f = False
                break
            try:
                f_vals.append(float(fv))
            except (ValueError, TypeError):
                valid_f = False
                break

        if valid_f:
            valid_rows.append((t_val, y_val, f_vals))

    n_sample = len(valid_rows)
    if n_sample < 30:
        return {
            "status": "error",
            "message": f"Số lượng quan sát hợp lệ (N={n_sample}) không đủ để phân chia mẫu trung thực cho Causal Tree (cần tối thiểu N >= 30)."
        }

    T_all = np.array([r[0] for r in valid_rows], dtype=float)
    Y_all = np.array([r[1] for r in valid_rows], dtype=float)
    X_all = np.array([r[2] for r in valid_rows], dtype=float)

    n_treated = int(np.sum(T_all == 1.0))
    n_control = int(np.sum(T_all == 0.0))

    if n_treated < 2 * min_leaf_size or n_control < 2 * min_leaf_size:
        return {
            "status": "error",
            "message": f"Số lượng can thiệp ({n_treated}) hoặc đối chứng ({n_control}) không đủ cho điều kiện kích thước lá tối thiểu."
        }

    # Honest Sample Split: 50% training (structure), 50% estimation (honest effects)
    np.random.seed(42)
    indices = np.random.permutation(n_sample)
    split_idx = n_sample // 2
    tr_idx, est_idx = indices[:split_idx], indices[split_idx:]

    X_tr, T_tr, Y_tr = X_all[tr_idx], T_all[tr_idx], Y_all[tr_idx]
    X_est, T_est, Y_est = X_all[est_idx], T_all[est_idx], Y_all[est_idx]

    # Build tree
    root_node = _build_causal_tree(
        X_tr=X_tr,
        T_tr=T_tr,
        Y_tr=Y_tr,
        X_est=X_est,
        T_est=T_est,
        Y_est=Y_est,
        feature_names=feature_cols,
        depth=0,
        max_depth=max_depth,
        min_leaf_size=min_leaf_size
    )

    leaves = _collect_leaves(root_node)

    # Overall ATE
    ate_overall = float(np.mean(Y_all[T_all == 1.0]) - np.mean(Y_all[T_all == 0.0]))

    # Generate Dual-Panel SVG Chart
    svg_chart = _generate_causal_tree_svg(
        root_node=root_node,
        leaves=leaves,
        ate_overall=ate_overall,
        feature_names=feature_cols
    )

    # APA 7th Edition Narrative
    best_leaf = max(leaves, key=lambda l: l["tau_subgroup"]) if leaves else None
    worst_leaf = min(leaves, key=lambda l: l["tau_subgroup"]) if leaves else None

    apa_narrative = (
        f"Phân tích Cây Tương Tác Nhân Quả Trung Thực (Honest Causal Interaction Trees; Athey & Imbens, 2016) "
        f"được tiến hành trên tổng mẫu N = {n_sample} người tham gia (Tập phân tách cấu trúc: n = {len(tr_idx)}, "
        f"Tập ước lượng trung thực: n = {len(est_idx)}). "
        f"Tác động can thiệp trung bình toàn mẫu đạt ATE = {ate_overall:.4f}. "
        f"Thuật toán đã tối ưu hóa tiêu chuẩn phương sai giữa các nhánh và phân tách thành {len(leaves)} phân khúc đối tượng đặc thù. "
    )
    if best_leaf:
        apa_narrative += (
            f"Phân khúc phản hồi tích cực nhất là nhóm [{best_leaf['rule']}] với hiệu ứng tau = {best_leaf['tau_subgroup']:.4f} "
            f"(SE = {best_leaf['se']:.4f}, p = {best_leaf['p_value']:.4f}, 95% CI [{best_leaf['ci_lower']:.3f}, {best_leaf['ci_upper']:.3f}]). "
        )
    if worst_leaf and worst_leaf != best_leaf:
        apa_narrative += (
            f"Ngược lại, phân khúc có mức độ phản hồi thấp nhất là nhóm [{worst_leaf['rule']}] với tau = {worst_leaf['tau_subgroup']:.4f} "
            f"(SE = {worst_leaf['se']:.4f}, p = {worst_leaf['p_value']:.4f})."
        )

    return {
        "status": "success",
        "treatment_field": treatment_col,
        "outcome_field": outcome_col,
        "feature_fields": feature_cols,
        "sample_diagnostics": {
            "n_total": n_sample,
            "n_training_structure": len(tr_idx),
            "n_estimation_honest": len(est_idx),
            "n_treated_total": n_treated,
            "n_control_total": n_control,
            "n_subgroups": len(leaves),
            "ate_overall": round(ate_overall, 4)
        },
        "subgroups": leaves,
        "tree_structure": _tree_to_dict(root_node),
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_causal_tree_svg(
    root_node: CausalTreeNode,
    leaves: List[Dict[str, Any]],
    ate_overall: float,
    feature_names: List[str]
) -> str:
    """
    Renders high-definition dual-panel vector SVG:
    Panel A: Decision Tree Flowchart with Split Nodes & Subgroup Leafs
    Panel B: Subgroup Forest Plot (tau estimates and 95% CI error bars)
    """
    width = 840
    height = 370

    # Panel A bounds (Tree hierarchy)
    ax0, ax1 = 30, 430
    # Panel B bounds (Forest plot)
    bx0, bx1 = 470, 810
    by0, by1 = 60, 310
    b_width = bx1 - bx0
    b_height = by1 - by0

    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" class="w-full">',
        f'<rect width="{width}" height="{height}" fill="#090d16" rx="12" stroke="#1e293b" stroke-width="1.5"/>',

        '<text x="20" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL A: Cây Phân Nhánh Nhân Quả (Honest Causal Tree)</text>',
        f'<text x="{bx0}" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL B: Biểu Đồ Rừng Hiệu Ứng Phân Khúc (Forest Plot)</text>',

        # Panel A Tree diagram representation
        # Root node
        f'<rect x="150" y="55" width="160" height="42" fill="#1e1e38" rx="6" stroke="#6366f1" stroke-width="1.5"/>',
        f'<text x="230" y="73" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="700" text-anchor="middle">Gốc: {root_node.feature_name or "Root"}</text>',
        f'<text x="230" y="88" fill="#a5b4fc" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">ATE Toàn mẫu = {ate_overall:.3f}</text>',
    ]

    # Draw tree branches
    if root_node.left and root_node.right:
        # Left child branch
        svg_elements.append('<line x1="200" y1="97" x2="110" y2="150" stroke="#6366f1" stroke-width="1.5"/>')
        svg_elements.append(f'<text x="140" y="125" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="9" text-anchor="end">≤ {root_node.threshold:.2f}</text>')

        # Right child branch
        svg_elements.append('<line x1="260" y1="97" x2="350" y2="150" stroke="#6366f1" stroke-width="1.5"/>')
        svg_elements.append(f'<text x="320" y="125" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="9" text-anchor="start">> {root_node.threshold:.2f}</text>')

        # Node Left
        l_col = "#10b981" if root_node.left.tau > 0 else "#f43f5e"
        svg_elements.append(f'<rect x="40" y="150" width="140" height="45" fill="#0f172a" rx="6" stroke="{l_col}" stroke-width="1.5"/>')
        svg_elements.append(f'<text x="110" y="168" fill="#ffffff" font-family="system-ui, sans-serif" font-size="10" font-weight="700" text-anchor="middle">{root_node.left.rule[:16]}</text>')
        svg_elements.append(f'<text x="110" y="184" fill="{l_col}" font-family="system-ui, sans-serif" font-size="10" font-weight="bold" text-anchor="middle">τ = {root_node.left.tau:.3f} (n={root_node.left.n_total})</text>')

        # Node Right
        r_col = "#10b981" if root_node.right.tau > 0 else "#f43f5e"
        svg_elements.append(f'<rect x="280" y="150" width="140" height="45" fill="#0f172a" rx="6" stroke="{r_col}" stroke-width="1.5"/>')
        svg_elements.append(f'<text x="350" y="168" fill="#ffffff" font-family="system-ui, sans-serif" font-size="10" font-weight="700" text-anchor="middle">{root_node.right.rule[:16]}</text>')
        svg_elements.append(f'<text x="350" y="184" fill="{r_col}" font-family="system-ui, sans-serif" font-size="10" font-weight="bold" text-anchor="middle">τ = {root_node.right.tau:.3f} (n={root_node.right.n_total})</text>')

    # Panel A Subgroup summary footer
    svg_elements.append(f'<rect x="30" y="240" width="400" height="90" fill="#0c1322" rx="6" stroke="#1e293b" stroke-width="1"/>')
    svg_elements.append('<text x="45" y="260" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="11" font-weight="700">Tóm tắt Phân khúc Phát hiện (Honest Leaves):</text>')
    for idx, leaf in enumerate(leaves[:3]):
        col = "#34d399" if leaf["tau_subgroup"] > 0 else "#fb7185"
        svg_elements.append(f'<text x="45" y="{280 + idx * 18}" fill="{col}" font-family="system-ui, sans-serif" font-size="10">• Nhóm #{leaf["leaf_id"]} [{leaf["rule"][:18]}]: τ = {leaf["tau_subgroup"]:.3f} (p={leaf["p_value"]:.3f})</text>')

    # Panel B Forest plot
    svg_elements.append(f'<rect x="{bx0}" y="{by0}" width="{b_width}" height="{b_height}" fill="#0c1322" rx="6" stroke="#1e293b" stroke-width="1"/>')

    # X scale for tau
    all_tau_vals = [l["ci_lower"] for l in leaves] + [l["ci_upper"] for l in leaves] + [0.0, ate_overall]
    min_tau = min(all_tau_vals)
    max_tau = max(all_tau_vals)
    tau_span = max(1e-4, max_tau - min_tau)
    min_tau -= 0.15 * tau_span
    max_tau += 0.15 * tau_span
    tau_range = max_tau - min_tau

    def scale_tau_x(t_val: float) -> float:
        return bx0 + 60 + ((t_val - min_tau) / tau_range) * (b_width - 90)

    # Vertical line at 0 (No effect)
    x_zero = scale_tau_x(0.0)
    svg_elements.append(f'<line x1="{x_zero:.1f}" y1="{by0}" x2="{x_zero:.1f}" y2="{by1}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3"/>')
    svg_elements.append(f'<text x="{x_zero:.1f}" y="{by1+15}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">0 (Vô hiệu)</text>')

    # Forest plot rows
    row_height = b_height / max(1, len(leaves) + 1)
    for idx, leaf in enumerate(leaves):
        ry = by0 + (idx + 1) * row_height - 10
        lx1 = scale_tau_x(leaf["ci_lower"])
        lx2 = scale_tau_x(leaf["ci_upper"])
        cx = scale_tau_x(leaf["tau_subgroup"])
        pt_col = "#34d399" if leaf["tau_subgroup"] > 0 else "#fb7185"

        # Label
        svg_elements.append(f'<text x="{bx0+10}" y="{ry+4:.1f}" fill="#cbd5e1" font-family="system-ui, sans-serif" font-size="10" font-weight="600">#{leaf["leaf_id"]}</text>')

        # 95% CI Line
        svg_elements.append(f'<line x1="{lx1:.1f}" y1="{ry:.1f}" x2="{lx2:.1f}" y2="{ry:.1f}" stroke="{pt_col}" stroke-width="2"/>')
        # Whisker caps
        svg_elements.append(f'<line x1="{lx1:.1f}" y1="{ry-4:.1f}" x2="{lx1:.1f}" y2="{ry+4:.1f}" stroke="{pt_col}" stroke-width="2"/>')
        svg_elements.append(f'<line x1="{lx2:.1f}" y1="{ry-4:.1f}" x2="{lx2:.1f}" y2="{ry+4:.1f}" stroke="{pt_col}" stroke-width="2"/>')
        # Center square
        svg_elements.append(f'<rect x="{cx-4:.1f}" y="{ry-4:.1f}" width="8" height="8" fill="{pt_col}" stroke="#ffffff" stroke-width="1"/>')
        # Text value
        svg_elements.append(f'<text x="{lx2+8:.1f}" y="{ry+3:.1f}" fill="{pt_col}" font-family="system-ui, sans-serif" font-size="9.5" font-weight="700">{leaf["tau_subgroup"]:.2f}</text>')

    svg_elements.append('</svg>')
    return "".join(svg_elements)
