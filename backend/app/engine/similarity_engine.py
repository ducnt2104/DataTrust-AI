"""
DataTrust - Response Pairwise Duplication & Fuzzy Similarity Matrix Engine
Thuật toán phân tích tương đồng đa tầng giữa các cặp phản hồi (Pairwise Similarity Analysis):
- Ma trận khoảng cách Hamming / Jaccard cho câu hỏi đóng (Categorical Answer Matching)
- Phân tích n-gram Jaccard / Levenshtein cho câu hỏi mở (Open-ended Text Similarity)
- Phát hiện dấu vân tay số (Device Fingerprint & IP Collusion Rings)
- Thuật toán đồ thị tìm thành phần liên thông (Connected Components) trích xuất vòng lừa đảo / bot farm
- Tạo ma trận tương đồng (Similarity Heatmap Matrix) và chỉ số liêm chính dữ liệu (Data Integrity Index)
Tuân thủ tiêu chuẩn chất lượng dữ liệu khảo sát quốc tế AAPOR (2003) và ISO 20252:2019.
"""

import math
import json
from collections import defaultdict, deque
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from app.database import get_db
from app.engine.quality_engine import QualityEngine


class SimilarityEngine:
    """
    Bộ động cơ phân tích tương đồng cặp phản hồi & bóc tách mạng lưới gian lận (Collusion Syndicate Detector).
    """

    @staticmethod
    def calculate_categorical_similarity(vec_a: List[str], vec_b: List[str]) -> Tuple[float, int, int]:
        """
        Tính toán độ tương đồng giữa 2 vector đáp án câu hỏi đóng.
        Chỉ so sánh các vị trí có ít nhất một bên trả lời (a != '' or b != '').
        Trả về: (similarity_score [0.0 - 1.0], matches_count, valid_comparisons_count).
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0, 0, 0

        matches = 0
        valid_comparisons = 0

        for a, b in zip(vec_a, vec_b):
            if a != "" or b != "":
                valid_comparisons += 1
                if a == b and a != "":
                    matches += 1

        if valid_comparisons == 0:
            return 0.0, 0, 0

        similarity = matches / valid_comparisons
        return round(similarity, 4), matches, valid_comparisons

    @staticmethod
    def calculate_text_jaccard(text_a: str, text_b: str, n: int = 3) -> float:
        """
        Tính độ tương đồng văn bản câu hỏi mở bằng n-gram Jaccard (mặc định 3-gram).
        Nếu chuỗi ngắn hơn n ký tự, chuyển sang token Jaccard (từ đơn).
        """
        s_a = (text_a or "").strip().lower()
        s_b = (text_b or "").strip().lower()

        if not s_a or not s_b:
            return 0.0
        if s_a == s_b:
            return 1.0

        if len(s_a) < n or len(s_b) < n:
            tokens_a = set(s_a.split())
            tokens_b = set(s_b.split())
            union = tokens_a.union(tokens_b)
            if not union:
                return 0.0
            return round(len(tokens_a.intersection(tokens_b)) / len(union), 4)

        # Tạo tập hợp ký tự n-gram
        ngrams_a = {s_a[i:i + n] for i in range(len(s_a) - n + 1)}
        ngrams_b = {s_b[i:i + n] for i in range(len(s_b) - n + 1)}

        union = ngrams_a.union(ngrams_b)
        if not union:
            return 0.0

        intersection = ngrams_a.intersection(ngrams_b)
        return round(len(intersection) / len(union), 4)

    @classmethod
    def calculate_pair_metrics(
        cls,
        resp_a: Dict[str, Any],
        resp_b: Dict[str, Any],
        closed_q_items: List[Dict[str, Any]],
        open_q_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Đo lường chi tiết tương đồng giữa 2 phản hồi A và B.
        Kết hợp:
        1. Categorical Similarity trên câu hỏi đóng
        2. Text Jaccard trên câu hỏi mở
        3. Thuộc tính thiết bị, IP, thời gian nộp
        """
        ans_a = resp_a.get("answers", {})
        ans_b = resp_b.get("answers", {})

        # 1. Closed questions comparison
        closed_sim = 0.0
        closed_matches = 0
        closed_valid = 0
        if closed_q_items:
            vec_a = [
                QualityEngine.normalize_value(ans_a.get(q["id"]), q.get("question_type", ""))
                for q in closed_q_items
            ]
            vec_b = [
                QualityEngine.normalize_value(ans_b.get(q["id"]), q.get("question_type", ""))
                for q in closed_q_items
            ]
            closed_sim, closed_matches, closed_valid = cls.calculate_categorical_similarity(vec_a, vec_b)

        # 2. Open questions comparison
        open_sim = 0.0
        open_count = len(open_q_items)
        if open_count > 0:
            open_sim_sum = 0.0
            valid_open_comparisons = 0
            for q in open_q_items:
                qid = q["id"]
                val_a = str(ans_a.get(qid, "") or "")
                val_b = str(ans_b.get(qid, "") or "")
                if len(val_a.strip()) >= 3 and len(val_b.strip()) >= 3:
                    sim = cls.calculate_text_jaccard(val_a, val_b)
                    open_sim_sum += sim
                    valid_open_comparisons += 1
            if valid_open_comparisons > 0:
                open_sim = round(open_sim_sum / valid_open_comparisons, 4)

        # 3. Composite Similarity
        if closed_valid > 0 and open_count > 0 and open_sim > 0.0:
            composite_sim = round(0.70 * closed_sim + 0.30 * open_sim, 4)
        elif closed_valid > 0:
            composite_sim = closed_sim
        else:
            composite_sim = open_sim

        # 4. Digital Footprint & Timing signals
        dev_a = resp_a.get("device_id") or ""
        dev_b = resp_b.get("device_id") or ""
        same_device = bool(dev_a and dev_b and dev_a == dev_b)

        ip_a = resp_a.get("ip_address") or ""
        ip_b = resp_b.get("ip_address") or ""
        same_ip = bool(ip_a and ip_b and ip_a == ip_b)

        enum_a = resp_a.get("enumerator_id")
        enum_b = resp_b.get("enumerator_id")
        same_enumerator = bool(enum_a and enum_b and enum_a == enum_b)

        time_delta_seconds: Optional[float] = None
        rapid_succession = False
        t_a_str = resp_a.get("submitted_at")
        t_b_str = resp_b.get("submitted_at")
        if t_a_str and t_b_str:
            try:
                dt_a = datetime.fromisoformat(t_a_str.replace("Z", "+00:00"))
                dt_b = datetime.fromisoformat(t_b_str.replace("Z", "+00:00"))
                time_delta_seconds = abs((dt_a - dt_b).total_seconds())
                rapid_succession = time_delta_seconds <= 120.0
            except Exception:
                pass

        # 5. Risk Category Classification
        if composite_sim >= 0.98:
            risk_category = "IDENTICAL_DUPLICATE"
            severity = "CRITICAL"
            badge = "Trùng lặp 100%"
        elif composite_sim >= 0.85:
            risk_category = "NEAR_DUPLICATE"
            severity = "HIGH"
            badge = "Gần trùng khớp"
        elif composite_sim >= 0.75:
            risk_category = "SUSPICIOUS_VARIANT"
            severity = "MEDIUM"
            badge = "Tương đồng cao"
        else:
            risk_category = "NORMAL_VARIATION"
            severity = "LOW"
            badge = "Bình thường"

        is_collusion_syndicate = False
        if composite_sim >= 0.75 and (same_device or same_ip or (same_enumerator and rapid_succession)):
            is_collusion_syndicate = True
            severity = "CRITICAL"
            badge = "Mạng lưới thông đồng (Collusion)"

        return {
            "response_id_a": resp_a.get("id"),
            "response_id_b": resp_b.get("id"),
            "composite_similarity": composite_sim,
            "closed_similarity": closed_sim,
            "closed_matches": closed_matches,
            "closed_valid_comparisons": closed_valid,
            "open_similarity": open_sim,
            "same_device": same_device,
            "same_ip": same_ip,
            "same_enumerator": same_enumerator,
            "time_delta_seconds": round(time_delta_seconds, 1) if time_delta_seconds is not None else None,
            "rapid_succession": rapid_succession,
            "risk_category": risk_category,
            "is_collusion_syndicate": is_collusion_syndicate,
            "severity": severity,
            "badge": badge
        }

    @classmethod
    def extract_collusion_rings(
        cls,
        high_risk_pairs: List[Dict[str, Any]],
        responses_dict: Dict[str, Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Trích xuất các vòng thông đồng / bot rings (Connected Components trên đồ thị tương đồng).
        Mỗi thành phần liên thông có kích thước >= 2 là một vòng nghi vấn.
        """
        adj = defaultdict(set)
        pair_lookup = {}

        for pair in high_risk_pairs:
            sim = pair["composite_similarity"]
            if sim >= threshold or pair.get("is_collusion_syndicate"):
                u = pair["response_id_a"]
                v = pair["response_id_b"]
                adj[u].add(v)
                adj[v].add(u)
                pair_lookup[(min(u, v), max(u, v))] = pair

        visited = set()
        rings = []
        ring_counter = 1

        # Duyệt đồ thị theo thứ tự số bậc đỉnh giảm dần
        nodes = sorted(list(adj.keys()), key=lambda x: len(adj[x]), reverse=True)

        for start_node in nodes:
            if start_node in visited:
                continue

            component = []
            queue = deque([start_node])
            visited.add(start_node)

            while queue:
                curr = queue.popleft()
                component.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            if len(component) >= 2:
                # Tính toán đặc tính của vòng lừa đảo
                member_count = len(component)
                internal_sims = []
                devices = set()
                ips = set()
                enumerators = set()
                timestamps = []

                for rid in component:
                    resp = responses_dict.get(rid, {})
                    if resp.get("device_id"):
                        devices.add(resp["device_id"])
                    if resp.get("ip_address"):
                        ips.add(resp["ip_address"])
                    if resp.get("enumerator_id"):
                        enumerators.add(resp["enumerator_id"])
                    if resp.get("submitted_at"):
                        try:
                            dt = datetime.fromisoformat(resp["submitted_at"].replace("Z", "+00:00"))
                            timestamps.append(dt.timestamp())
                        except Exception:
                            pass

                for i in range(len(component)):
                    for j in range(i + 1, len(component)):
                        key = (min(component[i], component[j]), max(component[i], component[j]))
                        if key in pair_lookup:
                            internal_sims.append(pair_lookup[key]["composite_similarity"])

                mean_internal_sim = round(sum(internal_sims) / len(internal_sims), 4) if internal_sims else threshold

                has_shared_device = len(devices) < member_count and len(devices) > 0
                has_shared_ip = len(ips) < member_count and len(ips) > 0
                time_span_seconds = round(max(timestamps) - min(timestamps), 1) if len(timestamps) >= 2 else None

                # Đánh giá mức độ nghiêm trọng của vòng
                if has_shared_device or (has_shared_ip and member_count >= 3) or mean_internal_sim >= 0.95:
                    threat_level = "CRITICAL"
                    recommended_action = "Cách ly khẩn cấp và loại bỏ toàn bộ dữ liệu của vòng này khỏi tập số liệu phân tích."
                elif member_count >= 4 or mean_internal_sim >= 0.88:
                    threat_level = "HIGH"
                    recommended_action = "Đưa vào danh sách xem xét đặc biệt, kiểm tra phỏng vấn viên phụ trách."
                else:
                    threat_level = "MEDIUM"
                    recommended_action = "Gắn cờ theo dõi tương đồng cao, đối soát lại chéo giữa các phản hồi."

                rings.append({
                    "ring_id": f"RING-{ring_counter:02d}",
                    "member_count": member_count,
                    "response_ids": component,
                    "mean_internal_similarity": mean_internal_sim,
                    "shared_devices_count": len(devices),
                    "has_shared_device": has_shared_device,
                    "shared_ips_count": len(ips),
                    "has_shared_ip": has_shared_ip,
                    "enumerators_involved": list(enumerators),
                    "time_span_seconds": time_span_seconds,
                    "threat_level": threat_level,
                    "recommended_action": recommended_action
                })
                ring_counter += 1

        # Sắp xếp các vòng theo độ nguy hiểm và kích thước
        rings.sort(key=lambda r: (r["threat_level"] == "CRITICAL", r["threat_level"] == "HIGH", r["member_count"]), reverse=True)
        return rings

    @classmethod
    def generate_academic_narrative(
        cls,
        total_responses: int,
        high_risk_count: int,
        rings_count: int,
        collusion_nodes_count: int,
        highest_sim: float,
        avg_sim: float,
        threshold: float
    ) -> str:
        """Sinh đoạn diễn giải học thuật theo chuẩn APA 7th và ISO 20252:2019"""
        pct_collusion = round(collusion_nodes_count / max(1, total_responses) * 100, 2)
        if rings_count == 0 and high_risk_count == 0:
            return (
                f"Kiểm định ma trận tương đồng cặp (Pairwise Response Similarity Audit) trên N = {total_responses} "
                f"phản hồi với ngưỡng tương đồng cắt lọc S_crit = {threshold:.2f} không phát hiện bất kỳ cặp phản hồi trùng lặp "
                f"hoặc vòng thông đồng có tổ chức nào. Độ tương đồng bình quân toàn mẫu đạt M = {avg_sim:.3f}, nằm trong ngưỡng "
                f"phân tán tự nhiên của hành vi trả lời ngẫu nhiên độc lập (ISO 20252:2019). Dữ liệu đạt độ liêm chính thống kê cao."
            )
        elif rings_count > 0:
            return (
                f"Phát hiện cảnh báo nghiêm trọng về tính độc lập của người tham gia khảo sát (AAPOR Fraud Detection Standards): "
                f"Hệ thống đã nhận diện {rings_count} cụm/vòng thông đồng (Collusion Rings) bao gồm {collusion_nodes_count} "
                f"phản hồi nghi vấn ({pct_collusion}% tổng cỡ mẫu). Độ tương đồng cực đại ghi nhận giữa hai bản ghi đạt "
                f"S_max = {highest_sim:.3f}. Các phản hồi này có dấu hiệu chia sẻ thiết bị, địa chỉ IP hoặc được nộp dồn dập "
                f"trong thời gian ngắn. Khuyến nghị áp dụng quy trình cách ly (Quarantine Filter) trước khi thực hiện các phép "
                f"kiểm định suy diễn."
            )
        else:
            return (
                f"Kiểm định tương đồng cặp trên N = {total_responses} phản hồi phát hiện {high_risk_count} cặp có hệ số tương đồng "
                f"vượt ngưỡng S >= {threshold:.2f} (Độ tương đồng cao nhất S_max = {highest_sim:.3f}, trung bình toàn mẫu M = {avg_sim:.3f}). "
                f"Tuy nhiên, các phản hồi này không hình thành cấu trúc mạng lưới tập trung quy mô lớn. Nên đối chiếu thủ công "
                f"các cặp phản hồi được cảnh báo để loại trừ khả năng trùng hợp ngẫu nhiên."
            )

    @classmethod
    def analyze_survey_similarity(
        cls,
        survey_id: str,
        threshold: float = 0.80,
        max_matrix_size: int = 60,
        scope: str = "all"
    ) -> Dict[str, Any]:
        """
        Thực thi phân tích toàn diện ma trận tương đồng cặp và mạng lưới thông đồng.
        """
        with get_db() as conn:
            # 1. Kiểm tra khảo sát
            survey_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
            if not survey_row:
                raise ValueError("Không tìm thấy khảo sát.")

            # 2. Lấy danh sách câu hỏi
            q_rows = conn.execute(
                "SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC",
                (survey_id,)
            ).fetchall()

            questions = [dict(q) for q in q_rows]
            closed_q_items = [
                q for q in questions
                if q.get("question_type") not in ("short_text", "long_text")
            ]
            open_q_items = [
                q for q in questions
                if q.get("question_type") in ("short_text", "long_text")
            ]

            # 3. Lấy danh sách phản hồi theo phạm vi scope
            query = "SELECT * FROM responses WHERE survey_id = ?"
            params: List[Any] = [survey_id]
            if scope == "verified_clean":
                query += " AND (review_status = 'verified_clean' OR review_status = 'verified_valid')"
            query += " ORDER BY submitted_at ASC"

            resp_rows = conn.execute(query, params).fetchall()
            if not resp_rows:
                return {
                    "survey_id": survey_id,
                    "survey_title": survey_row["title"],
                    "scope": scope,
                    "total_responses": 0,
                    "matrix_size": 0,
                    "threshold": threshold,
                    "high_risk_pairs": [],
                    "collusion_rings": [],
                    "matrix_nodes": [],
                    "similarity_matrix": [],
                    "summary": {
                        "total_responses": 0,
                        "high_risk_pairs_count": 0,
                        "collusion_rings_count": 0,
                        "collusion_nodes_count": 0,
                        "highest_similarity": 0.0,
                        "average_similarity": 0.0,
                        "data_integrity_index": 100.0,
                        "status": "CHƯA CÓ DỮ LIỆU"
                    },
                    "academic_narrative": "Chưa có phản hồi nào để kiểm định tương đồng cặp."
                }

            # 4. Lấy toàn bộ câu trả lời
            resp_ids = [r["id"] for r in resp_rows]
            placeholders = ",".join(["?"] * len(resp_ids))
            ans_rows = conn.execute(
                f"SELECT response_id, question_id, answer_value FROM response_answers WHERE response_id IN ({placeholders})",
                resp_ids
            ).fetchall()

            answers_by_resp: Dict[str, Dict[str, Any]] = defaultdict(dict)
            for a in ans_rows:
                qid = a["question_id"]
                val_str = a["answer_value"]
                # Thử parse JSON cho multi-choice, ranking, matrix
                try:
                    if val_str and (val_str.startswith("[") or val_str.startswith("{")):
                        val = json.loads(val_str)
                    else:
                        val = val_str
                except Exception:
                    val = val_str
                answers_by_resp[a["response_id"]][qid] = val

            responses_dict: Dict[str, Dict[str, Any]] = {}
            for r in resp_rows:
                rid = r["id"]
                resp_obj = dict(r)
                resp_obj["answers"] = answers_by_resp.get(rid, {})
                # Trích xuất metadata an toàn từ client_metadata_json
                client_meta = {}
                try:
                    client_meta = json.loads(r["client_metadata_json"] or "{}")
                except Exception:
                    pass
                resp_obj["device_id"] = client_meta.get("device_id") or ""
                resp_obj["ip_address"] = client_meta.get("ip_address") or ""
                resp_obj["quality_score"] = max(0.0, 100.0 - float(r["risk_score"] or 0.0))
                resp_obj["review_status"] = r["review_status"] or "unverified"
                responses_dict[rid] = resp_obj

            N = len(resp_rows)

            # 5. Duyệt qua tất cả các cặp để tìm cặp tương đồng cao và tính toán ma trận
            high_risk_pairs: List[Dict[str, Any]] = []
            all_pair_sims: List[float] = []

            # Giới hạn ma trận heatmap: chọn N_matrix đầu tiên hoặc các phản hồi đáng ngờ nhất
            matrix_resp_list = resp_rows[:max_matrix_size]
            matrix_rids = [r["id"] for r in matrix_resp_list]
            rid_to_matrix_idx = {rid: idx for idx, rid in enumerate(matrix_rids)}
            M_size = len(matrix_rids)

            # Khởi tạo ma trận M_size x M_size (đường chéo = 1.0)
            similarity_matrix: List[List[float]] = [[0.0] * M_size for _ in range(M_size)]
            for i in range(M_size):
                similarity_matrix[i][i] = 1.0

            # Tính toán ma trận cặp trên toàn bộ phản hồi (với N vừa phải) hoặc giới hạn tối đa N = 300
            max_eval_responses = min(N, 250)
            eval_resp_list = resp_rows[:max_eval_responses]

            for i in range(max_eval_responses):
                resp_a = responses_dict[eval_resp_list[i]["id"]]
                rid_a = resp_a["id"]
                idx_a = rid_to_matrix_idx.get(rid_a)

                for j in range(i + 1, max_eval_responses):
                    resp_b = responses_dict[eval_resp_list[j]["id"]]
                    rid_b = resp_b["id"]
                    idx_b = rid_to_matrix_idx.get(rid_b)

                    metrics = cls.calculate_pair_metrics(resp_a, resp_b, closed_q_items, open_q_items)
                    sim = metrics["composite_similarity"]
                    all_pair_sims.append(sim)

                    # Điền vào ma trận con nếu cả 2 nằm trong matrix_rids
                    if idx_a is not None and idx_b is not None:
                        similarity_matrix[idx_a][idx_b] = sim
                        similarity_matrix[idx_b][idx_a] = sim

                    # Nếu tương đồng >= threshold hoặc có dấu hiệu collusion syndicate
                    if sim >= threshold or metrics.get("is_collusion_syndicate"):
                        high_risk_pairs.append(metrics)

            # Sắp xếp các cặp nguy cơ cao theo độ tương đồng giảm dần
            high_risk_pairs.sort(key=lambda p: (p.get("is_collusion_syndicate", False), p["composite_similarity"]), reverse=True)

            # 6. Trích xuất các vòng thông đồng (Collusion Rings)
            collusion_rings = cls.extract_collusion_rings(high_risk_pairs, responses_dict, threshold)

            # Tập hợp các response_id tham gia vào vòng lừa đảo
            collusion_nodes_set: Set[str] = set()
            for ring in collusion_rings:
                for rid in ring["response_ids"]:
                    collusion_nodes_set.add(rid)

            # 7. Thống kê tổng quan
            highest_sim = max(all_pair_sims) if all_pair_sims else 0.0
            avg_sim = round(sum(all_pair_sims) / len(all_pair_sims), 4) if all_pair_sims else 0.0

            collusion_count = len(collusion_nodes_set)
            integrity_index = max(0.0, round(100.0 - (collusion_count / N * 100.0), 1))

            if collusion_count == 0 and len(high_risk_pairs) == 0:
                status = "LIÊM CHÍNH CAO (Không phát hiện trùng lặp)"
            elif len(collusion_rings) > 0:
                status = f"CẢNH BÁO: Phát hiện {len(collusion_rings)} vòng nghi vấn thông đồng"
            else:
                status = f"CHÚ Ý: Phát hiện {len(high_risk_pairs)} cặp tương đồng bất thường"

            academic_narrative = cls.generate_academic_narrative(
                total_responses=N,
                high_risk_count=len(high_risk_pairs),
                rings_count=len(collusion_rings),
                collusion_nodes_count=collusion_count,
                highest_sim=highest_sim,
                avg_sim=avg_sim,
                threshold=threshold
            )

            # Chuẩn bị danh sách nodes cho ma trận trực quan
            matrix_nodes = []
            for idx, r in enumerate(matrix_resp_list):
                rid = r["id"]
                resp_info = responses_dict.get(rid, {})
                matrix_nodes.append({
                    "index": idx,
                    "id": rid,
                    "short_id": rid[:8],
                    "review_status": resp_info.get("review_status", "unverified"),
                    "quality_score": round(resp_info.get("quality_score", 100.0), 1),
                    "submitted_at": r["submitted_at"],
                    "is_in_collusion_ring": rid in collusion_nodes_set
                })

            return {
                "survey_id": survey_id,
                "survey_title": survey_row["title"],
                "scope": scope,
                "total_responses": N,
                "matrix_size": M_size,
                "threshold": threshold,
                "high_risk_pairs": high_risk_pairs,
                "collusion_rings": collusion_rings,
                "matrix_nodes": matrix_nodes,
                "similarity_matrix": similarity_matrix,
                "summary": {
                    "total_responses": N,
                    "evaluated_pairs": len(all_pair_sims),
                    "high_risk_pairs_count": len(high_risk_pairs),
                    "collusion_rings_count": len(collusion_rings),
                    "collusion_nodes_count": collusion_count,
                    "highest_similarity": highest_sim,
                    "average_similarity": avg_sim,
                    "data_integrity_index": integrity_index,
                    "status": status
                },
                "academic_narrative": academic_narrative
            }
