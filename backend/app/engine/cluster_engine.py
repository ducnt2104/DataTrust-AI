"""
DataTrust - Respondent Clustering & Typology Segmentation Engine
Triển khai phân tích phân cụm K-Means (Lloyd 1982; Arthur & Vassilvitskii 2007 K-Means++),
chuẩn hóa Z-Score, phân tích hệ số Silhouette (Rousseeuw 1987),
đường cong Elbow (Within-Cluster Sum of Squares - WCSS),
đo lường mức độ phân hóa câu hỏi (ANOVA F-ratio), và tự động đặt tên hồ sơ nhân vật (Persona Profiling).
"""

import math
import random
import json
from typing import List, Dict, Any, Optional, Tuple
from app.database import get_db


class ClusterEngine:
    """
    Bộ động cơ phân cụm người trả lời & phân khúc đối tượng (Respondent Segmentation)
    """

    @classmethod
    def standardize_matrix(
        cls,
        data: List[List[float]]
    ) -> Tuple[List[List[float]], List[float], List[float]]:
        """
        Chuẩn hóa Z-score ma trận dữ liệu: z = (x - mean) / std.
        Nếu std == 0, gán z = 0.
        """
        N = len(data)
        if N == 0:
            return [], [], []
        P = len(data[0])

        means: List[float] = [0.0] * P
        stds: List[float] = [0.0] * P

        for j in range(P):
            col_vals = [data[i][j] for i in range(N)]
            m = sum(col_vals) / N
            means[j] = m
            variance = sum((x - m) ** 2 for x in col_vals) / max(1, N - 1)
            stds[j] = math.sqrt(variance) if variance > 1.0e-9 else 1.0

        z_matrix: List[List[float]] = []
        for i in range(N):
            row: List[float] = []
            for j in range(P):
                s = stds[j]
                z = (data[i][j] - means[j]) / s if s > 1.0e-9 else 0.0
                row.append(z)
            z_matrix.append(row)

        return z_matrix, means, stds

    @classmethod
    def euclidean_distance(cls, p1: List[float], p2: List[float]) -> float:
        """Tính khoảng cách Euclidean đa chiều giữa 2 vector"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    @classmethod
    def kmeans_plus_plus_init(
        cls,
        data: List[List[float]],
        k: int,
        seed: int = 42
    ) -> List[List[float]]:
        """
        Khởi tạo tâm cụm theo thuật toán K-Means++ (Arthur & Vassilvitskii, 2007)
        Đảm bảo tính xác định và độ phân tán tối ưu của các tâm cụm ban đầu
        """
        rng = random.Random(seed)
        N = len(data)
        centroids = [list(data[rng.randint(0, N - 1)])]

        for _ in range(1, k):
            dist_sq = []
            for point in data:
                min_d = min(cls.euclidean_distance(point, c) ** 2 for c in centroids)
                dist_sq.append(min_d)

            sum_dist = sum(dist_sq)
            if sum_dist == 0.0:
                centroids.append(list(data[rng.randint(0, N - 1)]))
                continue

            r = rng.uniform(0.0, sum_dist)
            cum_sum = 0.0
            chosen_idx = N - 1
            for idx, d2 in enumerate(dist_sq):
                cum_sum += d2
                if cum_sum >= r:
                    chosen_idx = idx
                    break
            centroids.append(list(data[chosen_idx]))

        return centroids

    @classmethod
    def run_kmeans(
        cls,
        data: List[List[float]],
        k: int,
        max_iterations: int = 50,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Thực thi thuật toán K-Means Lloyd:
        Gán cụm và cập nhật tâm cụm cho đến khi hội tụ
        """
        N = len(data)
        P = len(data[0]) if N > 0 else 0
        if N < k or k < 2:
            raise ValueError(f"Cần ít nhất N >= k = {k} quan sát để phân cụm.")

        centroids = cls.kmeans_plus_plus_init(data, k, seed)
        assignments = [0] * N
        converged = False
        final_iter = 0

        for it in range(1, max_iterations + 1):
            changed = False
            # 1. Gán từng điểm vào cụm gần nhất
            for i in range(N):
                min_dist = float('inf')
                best_c = 0
                for c_idx, c in enumerate(centroids):
                    d = cls.euclidean_distance(data[i], c)
                    if d < min_dist:
                        min_dist = d
                        best_c = c_idx
                if assignments[i] != best_c:
                    assignments[i] = best_c
                    changed = True

            # 2. Cập nhật lại tâm cụm
            new_centroids = [[0.0] * P for _ in range(k)]
            cluster_counts = [0] * k

            for i in range(N):
                c_idx = assignments[i]
                cluster_counts[c_idx] += 1
                for j in range(P):
                    new_centroids[c_idx][j] += data[i][j]

            for c_idx in range(k):
                if cluster_counts[c_idx] > 0:
                    for j in range(P):
                        new_centroids[c_idx][j] /= cluster_counts[c_idx]
                else:
                    # Tránh cụm rỗng bằng cách tái khởi tạo tâm cụm
                    new_centroids[c_idx] = list(data[random.Random(seed + it).randint(0, N - 1)])

            centroids = new_centroids
            final_iter = it
            if not changed:
                converged = True
                break

        # 3. Tính Within-Cluster Sum of Squares (WCSS / Inertia)
        wcss = 0.0
        cluster_wcss = [0.0] * k
        for i in range(N):
            c_idx = assignments[i]
            d2 = cls.euclidean_distance(data[i], centroids[c_idx]) ** 2
            wcss += d2
            cluster_wcss[c_idx] += d2

        return {
            "k": k,
            "converged": converged,
            "iterations": final_iter,
            "assignments": assignments,
            "centroids": centroids,
            "wcss": round(wcss, 3),
            "cluster_wcss": [round(cw, 3) for cw in cluster_wcss],
            "cluster_sizes": [assignments.count(c) for c in range(k)]
        }

    @classmethod
    def calculate_silhouette_score(
        cls,
        data: List[List[float]],
        assignments: List[int],
        k: int
    ) -> Dict[str, Any]:
        """
        Tính toán hệ số Silhouette (Rousseeuw, 1987) s(i) = (b(i) - a(i)) / max(a(i), b(i))
        """
        N = len(data)
        if N < 3 or k < 2:
            return {"overall_score": 0.0, "cluster_scores": [0.0] * k, "sample_scores": [0.0] * N}

        cluster_indices: Dict[int, List[int]] = {c: [] for c in range(k)}
        for i, c in enumerate(assignments):
            cluster_indices[c].append(i)

        silhouette_values = [0.0] * N

        for i in range(N):
            c_i = assignments[i]
            same_cluster = cluster_indices[c_i]

            # a(i): Khoảng cách trung bình nội cụm
            if len(same_cluster) <= 1:
                silhouette_values[i] = 0.0
                continue

            a_i = sum(cls.euclidean_distance(data[i], data[j]) for j in same_cluster if j != i) / (len(same_cluster) - 1)

            # b(i): Khoảng cách trung bình tối thiểu tới cụm láng giềng gần nhất
            min_b_i = float('inf')
            for other_c in range(k):
                if other_c == c_i:
                    continue
                other_members = cluster_indices[other_c]
                if not other_members:
                    continue
                b_dist = sum(cls.euclidean_distance(data[i], data[j]) for j in other_members) / len(other_members)
                if b_dist < min_b_i:
                    min_b_i = b_dist

            denom = max(a_i, min_b_i)
            s_i = (min_b_i - a_i) / denom if denom > 1.0e-9 else 0.0
            silhouette_values[i] = max(-1.0, min(1.0, s_i))

        overall_score = sum(silhouette_values) / N
        cluster_scores = []
        for c in range(k):
            members = cluster_indices[c]
            c_score = sum(silhouette_values[m] for m in members) / len(members) if members else 0.0
            cluster_scores.append(round(c_score, 3))

        return {
            "overall_score": round(overall_score, 3),
            "cluster_scores": cluster_scores,
            "sample_scores": [round(s, 3) for s in silhouette_values]
        }

    @classmethod
    def calculate_feature_importance(
        cls,
        raw_data: List[List[float]],
        assignments: List[int],
        k: int,
        feature_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Đo lường mức độ quan trọng của từng câu hỏi trong việc phân biệt các cụm bằng tỷ số ANOVA F-ratio:
        F = MS_between / MS_within
        """
        N = len(raw_data)
        P = len(feature_names)
        if N <= k or k < 2:
            return []

        results = []
        for j in range(P):
            col_vals = [raw_data[i][j] for i in range(N)]
            grand_mean = sum(col_vals) / N

            # Tính SS_between và SS_within
            ss_between = 0.0
            ss_within = 0.0

            cluster_means = []
            for c in range(k):
                c_vals = [raw_data[i][j] for i in range(N) if assignments[i] == c]
                n_c = len(c_vals)
                if n_c > 0:
                    c_mean = sum(c_vals) / n_c
                    ss_between += n_c * ((c_mean - grand_mean) ** 2)
                    ss_within += sum((x - c_mean) ** 2 for x in c_vals)
                    cluster_means.append(round(c_mean, 2))
                else:
                    cluster_means.append(0.0)

            df_between = k - 1
            df_within = N - k

            ms_between = ss_between / df_between if df_between > 0 else 0.0
            ms_within = ss_within / df_within if df_within > 0 else 1.0

            f_ratio = ms_between / ms_within if ms_within > 1.0e-9 else 0.0

            # Tính Eta-squared: SS_between / (SS_between + SS_within)
            total_ss = ss_between + ss_within
            eta_sq = ss_between / total_ss if total_ss > 1.0e-9 else 0.0

            results.append({
                "feature_index": j,
                "feature_name": feature_names[j],
                "f_ratio": round(f_ratio, 2),
                "eta_squared": round(eta_sq, 3),
                "cluster_means": cluster_means,
                "grand_mean": round(grand_mean, 2)
            })

        # Sắp xếp câu hỏi có năng lực phân hóa mạnh nhất lên đầu
        results.sort(key=lambda x: x["f_ratio"], reverse=True)
        return results

    @classmethod
    def generate_persona_profiles(
        cls,
        feature_importance: List[Dict[str, Any]],
        cluster_sizes: List[int],
        total_n: int,
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Tự động tổng hợp hồ sơ phân khúc đối tượng (Persona Archetypes) từ các câu hỏi đặc trưng nhất
        """
        personas = []
        for c in range(k):
            size = cluster_sizes[c]
            pct = round((size / total_n) * 100.0, 1) if total_n > 0 else 0.0

            # Tìm 2 câu hỏi có giá trị trung bình nổi bật nhất của cụm này
            high_traits = []
            low_traits = []

            for feat in feature_importance[:4]:
                c_val = feat["cluster_means"][c]
                g_val = feat["grand_mean"]
                diff = c_val - g_val

                if diff > 0.3:
                    high_traits.append(f"{feat['feature_name']} (M={c_val})")
                elif diff < -0.3:
                    low_traits.append(f"{feat['feature_name']} (M={c_val})")

            # Đặt tên phân khúc trực quan
            if c == 0:
                name = "Nhóm Tiên Phong / Đồng Thuận Cao (Core Adopters)"
                archetype = "Đặc trưng bởi điểm số tích cực vượt trội trên các tiêu chí cốt lõi."
            elif c == 1:
                name = "Nhóm Trung Lập / Thận Trọng (Pragmatic Neutrals)"
                archetype = "Xu hướng giữ quan điểm cân bằng, biến thiên ổn định quanh mức trung vị."
            elif c == 2:
                name = "Nhóm Quan Ngại / Kỳ Vọng Cải Tiến (Critical Evaluators)"
                archetype = "Nhóm có nhiều băn khoăn hoặc phản hồi khắt khe về các khía cạnh dịch vụ."
            else:
                name = f"Phân Khúc Tiêu Biểu #{c + 1} (Segment {chr(65 + c)})"
                archetype = "Nhóm người trả lời có cấu trúc phân hóa riêng biệt trên các thang đo."

            personas.append({
                "cluster_id": c,
                "cluster_code": f"C{c + 1}",
                "name": name,
                "archetype_description": archetype,
                "size": size,
                "percentage": pct,
                "high_traits": high_traits[:2],
                "low_traits": low_traits[:2]
            })

        return personas

    @classmethod
    def analyze_survey_clusters(
        cls,
        survey_id: str,
        question_ids: Optional[List[str]] = None,
        k: Optional[int] = None,
        scope: str = "verified_clean"
    ) -> Dict[str, Any]:
        """
        Thực thi phân tích phân cụm toàn diện cho cuộc khảo sát
        """
        with get_db() as conn:
            s_row = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
            if not s_row:
                raise ValueError("Không tìm thấy khảo sát.")

            # Lấy danh sách câu hỏi
            if question_ids:
                placeholders = ",".join(["?"] * len(question_ids))
                q_rows = conn.execute(f"""
                    SELECT id, order_index, question_type, title FROM questions
                    WHERE survey_id = ? AND id IN ({placeholders}) ORDER BY order_index ASC
                """, [survey_id] + question_ids).fetchall()
            else:
                q_rows = conn.execute("""
                    SELECT id, order_index, question_type, title FROM questions
                    WHERE survey_id = ? AND question_type IN ('likert', 'rating', 'rating_scale', 'linear_scale', 'number')
                    ORDER BY order_index ASC
                """, (survey_id,)).fetchall()

            if len(q_rows) < 2:
                raise ValueError("Cần ít nhất 2 câu hỏi thang đo để phân cụm người trả lời.")

            selected_q_ids = [q["id"] for q in q_rows]
            q_titles = {q["id"]: q["title"] for q in q_rows}

            scope_sql = " AND review_status != 'verified_fraud' AND (risk_level != 'high' OR review_status = 'verified_valid')" if scope == "verified_clean" else ""
            resp_rows = conn.execute(f"""
                SELECT id FROM responses WHERE survey_id = ?{scope_sql} ORDER BY submitted_at ASC
            """, (survey_id,)).fetchall()

            if len(resp_rows) < 6:
                raise ValueError("Cần ít nhất 6 phản hồi khảo sát để phân tích phân cụm tin cậy.")

            r_ids = [r["id"] for r in resp_rows]
            resp_placeholders = ",".join(["?"] * len(r_ids))
            a_rows = conn.execute(f"""
                SELECT response_id, question_id, answer_value FROM response_answers
                WHERE response_id IN ({resp_placeholders})
            """, r_ids).fetchall()

            ans_map: Dict[str, Dict[str, Any]] = {rid: {} for rid in r_ids}
            for a in a_rows:
                v = a["answer_value"]
                try:
                    ans_map[a["response_id"]][a["question_id"]] = json.loads(v)
                except Exception:
                    ans_map[a["response_id"]][a["question_id"]] = v

        # Xây dựng ma trận điểm số thực tế
        raw_matrix: List[List[float]] = []
        valid_response_ids: List[str] = []

        # Tính trung bình toàn cục để gán bù (mean imputation) nếu thiếu đơn lẻ
        col_sums = [0.0] * len(selected_q_ids)
        col_counts = [0] * len(selected_q_ids)

        for rid in r_ids:
            for j, qid in enumerate(selected_q_ids):
                v = ans_map[rid].get(qid)
                try:
                    num_v = float(v)
                    col_sums[j] += num_v
                    col_counts[j] += 1
                except (ValueError, TypeError):
                    pass

        col_means = [col_sums[j] / max(1, col_counts[j]) for j in range(len(selected_q_ids))]

        for rid in r_ids:
            row: List[float] = []
            has_data = False
            for j, qid in enumerate(selected_q_ids):
                v = ans_map[rid].get(qid)
                try:
                    num_v = float(v)
                    row.append(num_v)
                    has_data = True
                except (ValueError, TypeError):
                    row.append(col_means[j])

            if has_data:
                raw_matrix.append(row)
                valid_response_ids.append(rid)

        N = len(raw_matrix)
        if N < 6:
            raise ValueError("Không đủ dữ liệu phản hồi hợp lệ để phân cụm.")

        z_matrix, _, _ = cls.standardize_matrix(raw_matrix)

        # Tính đường cong Elbow và Silhouette từ k = 2 đến k = min(5, N - 1)
        max_k_eval = min(5, N - 1)
        elbow_curve = []
        best_k = 3 if max_k_eval >= 3 else 2
        best_sil = -1.0

        for test_k in range(2, max_k_eval + 1):
            km = cls.run_kmeans(z_matrix, test_k)
            sil = cls.calculate_silhouette_score(z_matrix, km["assignments"], test_k)
            elbow_curve.append({
                "k": test_k,
                "wcss": km["wcss"],
                "silhouette_score": sil["overall_score"]
            })
            if sil["overall_score"] > best_sil:
                best_sil = sil["overall_score"]
                best_k = test_k

        # Nếu người dùng chỉ định k cụ thể, sử dụng k đó; nếu không chọn k tối ưu theo Silhouette
        chosen_k = k if (k and 2 <= k <= max_k_eval) else best_k

        final_kmeans = cls.run_kmeans(z_matrix, chosen_k)
        final_silhouette = cls.calculate_silhouette_score(z_matrix, final_kmeans["assignments"], chosen_k)

        feature_names = [q_titles[qid] for qid in selected_q_ids]
        feature_importance = cls.calculate_feature_importance(
            raw_data=raw_matrix,
            assignments=final_kmeans["assignments"],
            k=chosen_k,
            feature_names=feature_names
        )

        personas = cls.generate_persona_profiles(
            feature_importance=feature_importance,
            cluster_sizes=final_kmeans["cluster_sizes"],
            total_n=N,
            k=chosen_k
        )

        # Đánh giá chất lượng phân cụm
        sil_score = final_silhouette["overall_score"]
        if sil_score >= 0.45:
            cluster_quality = "STRONG_CLUSTERING"
            quality_badge = "emerald"
            quality_desc = "Cấu trúc phân cụm rất rõ nét và phân hóa tự nhiên (Silhouette >= 0.45)."
        elif sil_score >= 0.25:
            cluster_quality = "ACCEPTABLE_CLUSTERING"
            quality_badge = "amber"
            quality_desc = "Cấu trúc phân cụm hợp lý, các nhóm có sự giao thoa nhẹ ở ranh giới (0.25 <= Silhouette < 0.45)."
        else:
            cluster_quality = "WEAK_CLUSTERING"
            quality_badge = "rose"
            quality_desc = "Cấu trúc phân cụm yếu, dữ liệu phân bố tương đối đồng nhất (Silhouette < 0.25)."

        # Đoạn trích dẫn APA 7th Edition
        apa_narrative = (
            f"A K-Means cluster analysis with K-Means++ initialization was conducted on {len(selected_q_ids)} survey items "
            f"(N = {N}). The sample was segmented into {chosen_k} empirical respondent typologies with an overall "
            f"Silhouette coefficient of s = {sil_score:.2f} ({cluster_quality.lower().replace('_', ' ')}). "
            f"The cluster distribution was: " + ", ".join([f"{p['name']} (n = {p['size']}, {p['percentage']}%)" for p in personas]) + ". "
            f"Between-cluster differences were primarily driven by '{feature_importance[0]['feature_name']}' "
            f"(F = {feature_importance[0]['f_ratio']:.2f}, eta^2 = {feature_importance[0]['eta_squared']:.2f})."
        )

        return {
            "survey_id": survey_id,
            "survey_title": s_row["title"],
            "scope": scope,
            "sample_size": N,
            "features_count": len(selected_q_ids),
            "features": [
                {"id": qid, "title": q_titles[qid]} for qid in selected_q_ids
            ],
            "chosen_k": chosen_k,
            "wcss": final_kmeans["wcss"],
            "silhouette": {
                "overall_score": sil_score,
                "cluster_scores": final_silhouette["cluster_scores"],
                "quality_level": cluster_quality,
                "quality_badge": quality_badge,
                "description": quality_desc
            },
            "elbow_curve": elbow_curve,
            "personas": personas,
            "feature_importance": feature_importance,
            "apa_narrative": apa_narrative
        }
