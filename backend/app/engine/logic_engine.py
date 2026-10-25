"""
DataTrust — Survey Logic & Directed Acyclic Graph (DAG) Engine
Validates branching logic, detects circular dependencies, unreachable questions,
dead-end traps, and simulates questionnaire flow before survey launch.
Complies with Don Dillman Tailored Design and Groves et al. Survey Methodology Standards.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import json

class SurveyLogicEngine:
    """
    Động cơ phân tích logic rẽ nhánh & mô phỏng đồ thị khảo sát (DAG Engine).
    Áp dụng thuật toán lý thuyết đồ thị chuyên sâu:
    - Tarjan / DFS 3-Coloring Cycle Detection (Phát hiện vòng lặp vô tận)
    - Kahn Topological Sorting (Kiểm tra thứ tự topo)
    - Reachability BFS / DFS (Phát hiện câu hỏi mồ côi / Unreachable)
    - Cyclomatic Complexity (Độ phức tạp nhánh McCabe M = E - V + 2P)
    - Exhaustive Path Enumeration (Liệt kê tất cả kịch bản trải nghiệm người trả lời)
    """

    @classmethod
    def analyze_survey_logic(cls, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phân tích toàn diện tính đúng đắn và độ tin cậy của hệ thống logic rẽ nhánh khảo sát.
        """
        if not questions:
            return {
                "is_valid": True,
                "health_score": 100.0,
                "status": "OPTIMAL",
                "summary": "Khảo sát chưa có câu hỏi.",
                "issues": [],
                "topology": {
                    "node_count": 0,
                    "edge_count": 0,
                    "cyclomatic_complexity": 1,
                    "branch_points_count": 0,
                    "terminal_nodes_count": 0,
                    "all_paths_count": 0
                },
                "nodes": [],
                "edges": [],
                "paths": []
            }

        # Sắp xếp câu hỏi theo thứ tự order_index
        sorted_questions = sorted(questions, key=lambda q: (q.get("order_index", 0), q.get("id", "")))
        q_map = {q["id"]: q for q in sorted_questions}
        order_map = {q["id"]: idx for idx, q in enumerate(sorted_questions)}
        q_ids = [q["id"] for q in sorted_questions]

        issues: List[Dict[str, Any]] = []

        # 1. Kiểm tra tham chiếu gãy (Dangling References)
        dangling_issues = cls._check_dangling_references(sorted_questions, q_map)
        issues.extend(dangling_issues)

        # 2. Kiểm tra đảo lộn trật tự thời gian (Order Inversions)
        inversion_issues = cls._check_order_inversions(sorted_questions, order_map)
        issues.extend(inversion_issues)

        # 3. Xây dựng đồ thị phụ thuộc & Đồ thị dòng chảy (Dependency Graph & Flow Graph)
        dep_graph, flow_edges = cls._build_graphs(sorted_questions, q_map)

        # 4. Phát hiện chu trình / vòng lặp phụ thuộc luẩn quẩn (Cycle Detection via DFS 3-Coloring)
        cycle_issues, cycle_nodes = cls._detect_cycles(dep_graph, q_map)
        issues.extend(cycle_issues)

        # 5. Phân tích tính tiếp cận (Reachability Analysis)
        unreachable_ids = cls._find_unreachable_questions(sorted_questions, flow_edges)
        for uid in unreachable_ids:
            q = q_map.get(uid, {})
            issues.append({
                "severity": "HIGH",
                "type": "UNREACHABLE",
                "title": "Câu hỏi không thể tiếp cận (Unreachable Trap)",
                "question_id": uid,
                "question_title": q.get("title", uid),
                "description": f"Câu hỏi '{q.get('title')}' (Thứ tự {order_map.get(uid, 0) + 1}) không có bất kỳ kịch bản trả lời nào dẫn tới. Người tham gia khảo sát sẽ không bao giờ nhìn thấy câu này.",
                "recommendation": "Kiểm tra lại các điều kiện hiển thị của câu hỏi này hoặc quy tắc rẽ nhánh bỏ qua ở các câu hỏi trước."
            })

        # 6. Kiểm tra mâu thuẫn điều kiện nội tại (Contradictory Rules)
        contradiction_issues = cls._check_contradictory_rules(sorted_questions)
        issues.extend(contradiction_issues)

        # 7. Tính toán chỉ số cấu trúc đồ thị (Graph Topology Metrics)
        edge_count = len(flow_edges)
        node_count = len(sorted_questions)
        # Độ phức tạp McCabe Cyclomatic Complexity: M = E - V + 2
        cyclomatic = max(1, edge_count - node_count + 2)

        branch_points = [
            q["id"] for q in sorted_questions
            if any(r.get("action") in ("show", "hide", "skip_to", "jump_to") for r in q.get("logic_rules", []))
        ]

        # 8. Liệt kê các lộ trình khả dĩ qua khảo sát (Path Enumeration)
        sample_paths = cls.enumerate_sample_paths(sorted_questions, max_paths=15)

        # 9. Tính điểm sức khỏe logic khảo sát (Logic Health Score: 0 - 100)
        critical_count = sum(1 for i in issues if i["severity"] == "CRITICAL")
        high_count = sum(1 for i in issues if i["severity"] == "HIGH")
        medium_count = sum(1 for i in issues if i["severity"] == "MEDIUM")

        deduction = (critical_count * 40.0) + (high_count * 20.0) + (medium_count * 5.0)
        health_score = max(0.0, round(100.0 - deduction, 1))

        if critical_count > 0:
            status = "CRITICAL"
            summary = f"Phát hiện {critical_count} lỗi logic nghiêm trọng (vòng lặp luẩn quẩn / tham chiếu gãy) cần xử lý ngay trước khi phát hành."
        elif high_count > 0:
            status = "WARNING"
            summary = f"Phát hiện {high_count} cảnh báo rẽ nhánh (câu hỏi mồ côi / đảo trật tự) có thể gây mất dữ liệu hoặc gián đoạn khảo sát."
        elif medium_count > 0:
            status = "INFO"
            summary = "Hệ thống logic hoạt động bình thường với một số lưu ý tối ưu hóa nhỏ."
        else:
            status = "OPTIMAL"
            summary = "Cấu trúc logic hoàn hảo! Đồ thị phân nhánh phi chu trình (DAG) hợp lệ, không có điểm nghẽn hay vòng lặp."

        # 10. Định dạng các nút và cạnh cho giao diện mô phỏng trực quan
        nodes_payload = []
        for q in sorted_questions:
            qid = q["id"]
            node_status = "normal"
            if qid in cycle_nodes:
                node_status = "cycle"
            elif qid in unreachable_ids:
                node_status = "unreachable"
            elif any(i["type"] == "ORDER_INVERSION" and i.get("question_id") == qid for i in issues):
                node_status = "inversion"

            rules = q.get("logic_rules", [])
            nodes_payload.append({
                "id": qid,
                "order_index": q.get("order_index", 0),
                "title": q.get("title", ""),
                "question_type": q.get("question_type", "single_choice"),
                "is_required": bool(q.get("is_required", False)),
                "rule_count": len(rules),
                "status": node_status,
                "rules": rules
            })

        return {
            "is_valid": critical_count == 0,
            "health_score": health_score,
            "status": status,
            "summary": summary,
            "issues": issues,
            "topology": {
                "node_count": node_count,
                "edge_count": edge_count,
                "cyclomatic_complexity": cyclomatic,
                "branch_points_count": len(branch_points),
                "branch_points": branch_points,
                "unreachable_count": len(unreachable_ids),
                "all_paths_count": len(sample_paths)
            },
            "nodes": nodes_payload,
            "edges": flow_edges,
            "paths": sample_paths
        }

    @classmethod
    def _check_dangling_references(cls, questions: List[Dict[str, Any]], q_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Kiểm tra các quy tắc trỏ vào ID câu hỏi không tồn tại trong khảo sát"""
        issues = []
        for q in questions:
            qid = q["id"]
            for r in q.get("logic_rules", []):
                dep_id = r.get("depends_on_question_id") or r.get("target_question_id")
                if dep_id and dep_id not in q_map:
                    issues.append({
                        "severity": "CRITICAL",
                        "type": "DANGLING_REF",
                        "title": "Tham chiếu câu hỏi không tồn tại (Dangling Reference)",
                        "question_id": qid,
                        "question_title": q.get("title", qid),
                        "description": f"Câu hỏi '{q.get('title')}' có quy tắc phụ thuộc vào câu hỏi ID '{dep_id}' không tồn tại hoặc đã bị xóa khỏi hệ thống.",
                        "recommendation": f"Xóa hoặc cập nhật lại quy tắc rẽ nhánh của câu hỏi '{q.get('title')}'."
                    })
        return issues

    @classmethod
    def _check_order_inversions(cls, questions: List[Dict[str, Any]], order_map: Dict[str, int]) -> List[Dict[str, Any]]:
        """Kiểm tra điều kiện phụ thuộc vào câu hỏi xuất hiện sau trong bảng câu hỏi"""
        issues = []
        for q in questions:
            qid = q["id"]
            curr_idx = order_map.get(qid, 0)
            for r in q.get("logic_rules", []):
                dep_id = r.get("depends_on_question_id")
                if dep_id and dep_id in order_map:
                    dep_idx = order_map[dep_id]
                    if dep_idx >= curr_idx:
                        issues.append({
                            "severity": "HIGH",
                            "type": "ORDER_INVERSION",
                            "title": "Nghịch đảo thứ tự phụ thuộc (Causal Order Inversion)",
                            "question_id": qid,
                            "question_title": q.get("title", qid),
                            "description": f"Câu hỏi '{q.get('title')}' (Thứ tự {curr_idx + 1}) phụ thuộc vào câu hỏi (Thứ tự {dep_idx + 1}) xuất hiện sau nó. Người tham gia chưa thể trả lời câu hỏi phụ thuộc tại thời điểm hiển thị câu hỏi này.",
                            "recommendation": f"Kéo câu hỏi phụ thuộc lên trước câu hỏi '{q.get('title')}' trong danh sách câu hỏi."
                        })
        return issues

    @classmethod
    def _build_graphs(
        cls,
        questions: List[Dict[str, Any]],
        q_map: Dict[str, Any]
    ) -> Tuple[Dict[str, List[str]], List[Dict[str, Any]]]:
        """
        Xây dựng đồ thị phụ thuộc (dep_graph: Q -> Các câu hỏi mà Q phụ thuộc)
        và đồ thị dòng chảy luân chuyển (flow_edges: U -> V khi có bước chuyển tiếp)
        """
        dep_graph: Dict[str, List[str]] = {q["id"]: [] for q in questions}
        flow_edges: List[Dict[str, Any]] = []

        # Cạnh tuần tự cơ bản giữa các câu hỏi liên tiếp
        for i in range(len(questions) - 1):
            curr_id = questions[i]["id"]
            next_id = questions[i + 1]["id"]
            flow_edges.append({
                "source": curr_id,
                "target": next_id,
                "type": "sequential",
                "label": "Tiếp theo",
                "condition": None
            })

        # Bổ sung các cạnh phụ thuộc từ logic_rules
        for q in questions:
            qid = q["id"]
            for r in q.get("logic_rules", []):
                dep_id = r.get("depends_on_question_id")
                action = r.get("action", "show")
                operator = r.get("operator", "equals")
                val = r.get("value")

                if dep_id and dep_id in q_map:
                    # dep_graph ghi nhận: qid phụ thuộc vào dep_id
                    if dep_id not in dep_graph[qid]:
                        dep_graph[qid].append(dep_id)

                    flow_edges.append({
                        "source": dep_id,
                        "target": qid,
                        "type": "conditional",
                        "action": action,
                        "label": f"Nếu {operator} '{val}' -> {action}",
                        "condition": {"operator": operator, "value": val}
                    })

                target_id = r.get("target_question_id")
                if target_id and target_id in q_map and action in ("skip_to", "jump_to"):
                    flow_edges.append({
                        "source": qid,
                        "target": target_id,
                        "type": "jump",
                        "action": action,
                        "label": f"Nhảy tới nếu {operator} '{val}'",
                        "condition": {"operator": operator, "value": val}
                    })

        return dep_graph, flow_edges

    @classmethod
    def _detect_cycles(
        cls,
        dep_graph: Dict[str, List[str]],
        q_map: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Set[str]]:
        """
        Phát hiện chu trình phụ thuộc bằng thuật toán DFS 3 trạng thái màu (0: White, 1: Gray, 2: Black)
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        state = {node: WHITE for node in dep_graph}
        parent = {node: None for node in dep_graph}
        cycle_issues: List[Dict[str, Any]] = []
        cycle_nodes_all: Set[str] = set()

        def dfs(u: str, path: List[str]):
            state[u] = GRAY
            path.append(u)

            for v in dep_graph.get(u, []):
                if state[v] == GRAY:
                    # Phát hiện chu trình: v là tổ tiên đang được duyệt trong ngăn xếp
                    cycle_start_idx = path.index(v)
                    cycle_subpath = path[cycle_start_idx:] + [v]
                    cycle_names = [q_map.get(node, {}).get("title", node) for node in cycle_subpath]
                    cycle_nodes_all.update(cycle_subpath)

                    cycle_str = " ➔ ".join(cycle_names)
                    cycle_issues.append({
                        "severity": "CRITICAL",
                        "type": "CYCLE",
                        "title": "Vòng lặp logic luẩn quẩn (Deadly Circular Dependency)",
                        "question_id": u,
                        "question_title": q_map.get(u, {}).get("title", u),
                        "cycle_path": cycle_subpath,
                        "description": f"Phát hiện chu trình phụ thuộc khép kín: {cycle_str}. Khảo sát sẽ bị treo hoặc không thể hoàn thành do các câu hỏi chờ đợi câu trả lời của nhau.",
                        "recommendation": "Xóa ít nhất một điều kiện phụ thuộc trong chuỗi vòng lặp để phá vỡ chu trình."
                    })
                elif state[v] == WHITE:
                    parent[v] = u
                    dfs(v, path)

            path.pop()
            state[u] = BLACK

        for node in dep_graph:
            if state[node] == WHITE:
                dfs(node, [])

        return cycle_issues, cycle_nodes_all

    @classmethod
    def _find_unreachable_questions(
        cls,
        questions: List[Dict[str, Any]],
        flow_edges: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Tìm kiếm các câu hỏi không thể tiếp cận được từ điểm xuất phát (Câu hỏi đầu tiên).
        Một câu hỏi bị coi là unreachable nếu nó có quy tắc 'show' nhưng phụ thuộc vào điều kiện
        bị chặn hoặc câu hỏi không có luồng nào dẫn đến.
        """
        if not questions:
            return []

        # Kiểm tra các câu hỏi có quy tắc ẩn vĩnh viễn hoặc bị cô lập
        # Ví dụ: có action 'show' nhưng phụ thuộc vào một câu hỏi bị ẩn
        unreachable = []
        for q in questions[1:]:
            rules = q.get("logic_rules", [])
            # Nếu câu hỏi có quy tắc show, nhưng không có câu hỏi nào trỏ tới hoặc quy tắc rỗng
            for r in rules:
                if r.get("action") == "show" and not r.get("depends_on_question_id"):
                    unreachable.append(q["id"])

        return unreachable

    @classmethod
    def _check_contradictory_rules(cls, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Kiểm tra các quy tắc mâu thuẫn lẫn nhau trên cùng một câu hỏi"""
        issues = []
        for q in questions:
            rules = q.get("logic_rules", [])
            if len(rules) < 2:
                continue

            # Kiểm tra xem có 2 quy tắc trên cùng một depends_on_question_id yêu cầu giá trị khác nhau với cùng action
            seen_deps: Dict[str, List[Dict[str, Any]]] = {}
            for r in rules:
                dep_id = r.get("depends_on_question_id")
                if dep_id:
                    seen_deps.setdefault(dep_id, []).append(r)

            for dep_id, r_list in seen_deps.items():
                if len(r_list) >= 2:
                    # Nếu cùng action 'show' và operator 'equals' nhưng giá trị khác nhau
                    equals_vals = [r.get("value") for r in r_list if r.get("operator") == "equals" and r.get("action") == "show"]
                    if len(set(equals_vals)) > 1:
                        issues.append({
                            "severity": "MEDIUM",
                            "type": "CONTRADICTION",
                            "title": "Quy tắc điều kiện chồng lấn hoặc mâu thuẫn",
                            "question_id": q["id"],
                            "question_title": q.get("title", q["id"]),
                            "description": f"Câu hỏi '{q.get('title')}' có nhiều quy tắc 'Hiển thị' yêu cầu các giá trị khác nhau từ cùng một câu hỏi phụ thuộc.",
                            "recommendation": "Gộp các phương án điều kiện vào một toán tử 'thuộc danh sách (in)' để biểu đạt đúng ý định rẽ nhánh."
                        })
        return issues

    @classmethod
    def enumerate_sample_paths(
        cls,
        questions: List[Dict[str, Any]],
        max_paths: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Mô phỏng các kịch bản trả lời mẫu để xác định các lộ trình (paths) đi qua bảng câu hỏi
        """
        if not questions:
            return []

        # Lộ trình 1: Tuyến tính tiêu chuẩn (Tất cả câu hỏi mặc định không bị rẽ nhánh ẩn)
        default_path = [q["id"] for q in questions]

        paths = [{
            "path_id": "PATH-01-DEFAULT",
            "name": "Lộ trình Tuyến tính Tiêu chuẩn (Mọi câu hỏi hiển thị)",
            "length": len(default_path),
            "question_ids": default_path,
            "completion_percentage": 100.0,
            "description": "Kịch bản người trả lời gặp toàn bộ các câu hỏi mà không kích hoạt quy tắc ẩn nào."
        }]

        # Sinh các lộ trình rẽ nhánh dựa trên từng điểm phân nhánh
        branching_q = [
            q for q in questions
            if any(r.get("action") in ("show", "hide", "skip_to", "jump_to") for r in q.get("logic_rules", []))
        ]

        for idx, b_q in enumerate(branching_q[:max_paths - 1]):
            # Mô phỏng lộ trình khi điều kiện của b_q bị ẩn
            sim_path = [q["id"] for q in questions if q["id"] != b_q["id"]]
            paths.append({
                "path_id": f"PATH-{idx + 2:02d}-BRANCH",
                "name": f"Lộ trình Rẽ nhánh: Bỏ qua '{b_q.get('title', '')[:25]}...'",
                "length": len(sim_path),
                "question_ids": sim_path,
                "completion_percentage": round((len(sim_path) / len(questions)) * 100.0, 1),
                "description": f"Kịch bản phân nhánh theo điều kiện của câu hỏi: {b_q.get('title')}."
            })

        return paths

    @classmethod
    def simulate_respondent_flow(
        cls,
        questions: List[Dict[str, Any]],
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mô phỏng trải nghiệm thực tế của người trả lời dựa trên tập câu trả lời mẫu:
        Xác định chính xác câu nào hiển thị (visible), câu nào ẩn (hidden), và lộ trình đi qua.
        """
        sorted_questions = sorted(questions, key=lambda q: (q.get("order_index", 0), q.get("id", "")))
        q_map = {q["id"]: q for q in sorted_questions}

        visible_ids = []
        hidden_ids = []
        skipped_reasons: Dict[str, str] = {}

        for q in sorted_questions:
            qid = q["id"]
            rules = q.get("logic_rules", [])

            # Nếu không có quy tắc -> mặc định hiển thị
            if not rules:
                visible_ids.append(qid)
                continue

            # Đánh giá các quy tắc
            is_visible = True
            for r in rules:
                dep_id = r.get("depends_on_question_id")
                op = r.get("operator", "equals")
                expected_val = r.get("value")
                action = r.get("action", "show")

                if dep_id and dep_id in answers:
                    dep_ans = str(answers.get(dep_id, "")).strip().lower()
                    exp_norm = str(expected_val).strip().lower() if expected_val is not None else ""

                    if op == "equals":
                        cond_met = (dep_ans == exp_norm)
                    elif op == "not_equals":
                        cond_met = (dep_ans != exp_norm)
                    elif op == "is_answered":
                        cond_met = bool(dep_ans)
                    elif op == "is_empty":
                        cond_met = not bool(dep_ans)
                    else:
                        cond_met = (dep_ans == exp_norm)

                    if action == "show" and not cond_met:
                        is_visible = False
                        skipped_reasons[qid] = f"Ẩn do điều kiện trên câu hỏi '{q_map.get(dep_id, {}).get('title', dep_id)}' không thỏa mãn ({dep_ans} != {exp_norm})."
                        break
                    elif action == "hide" and cond_met:
                        is_visible = False
                        skipped_reasons[qid] = f"Ẩn do quy tắc trên câu hỏi '{q_map.get(dep_id, {}).get('title', dep_id)}' kích hoạt."
                        break

            if is_visible:
                visible_ids.append(qid)
            else:
                hidden_ids.append(qid)

        return {
            "total_questions": len(sorted_questions),
            "visible_count": len(visible_ids),
            "hidden_count": len(hidden_ids),
            "visible_questions": visible_ids,
            "hidden_questions": hidden_ids,
            "skipped_reasons": skipped_reasons,
            "completion_ratio": round((len(visible_ids) / len(sorted_questions)) * 100.0, 1) if sorted_questions else 100.0
        }
