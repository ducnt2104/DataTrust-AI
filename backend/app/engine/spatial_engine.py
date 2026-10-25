"""
DataTrust - Geographic Spatial Clustering & Geo-Fencing Compliance Engine
Thuật toán phân tích không gian thực địa & kiểm định tính liêm chính tọa độ GPS:
- Phân cụm mật độ không gian DBSCAN (Ester et al., 1996) phát hiện gian lận ngồi một chỗ khai khống (Coffee-Shop Congregation Fraud)
- Phát hiện vận tốc di chuyển bất khả thi / Giả lập vị trí (Teleportation & GPS Spoofing Velocity Anomaly)
- Kiểm định ranh giới đa giác Geo-Fencing bằng thuật toán Ray-Casting (Jordan Curve Theorem)
- Độ phân tán không gian chuẩn (Spatial Standard Distance Deviation - Bachi 1962) và độ bao phủ lãnh thổ
Tuân thủ tiêu chuẩn chất lượng kiểm định thực địa ISO 20252:2019 (Mục 4.5.3) và AAPOR Fieldwork Verification.
"""

import math
import json
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, Set
from app.database import get_db
from app.engine.quality_engine import QualityEngine


class SpatialEngine:
    """
    Bộ động cơ phân tích không gian thực địa và phát hiện gian lận tọa độ GPS (Spatial Fraud Analytics).
    """

    EARTH_RADIUS_METERS = 6371000.0  # Bán kính Trái Đất (mét)
    EARTH_RADIUS_KM = 6371.0          # Bán kính Trái Đất (km)

    @classmethod
    def haversine_distance_meters(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Tính khoảng cách trắc địa đường chim bay theo mét (Haversine formula)"""
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(max(0.0, a)), math.sqrt(max(0.0, 1.0 - a)))
        return cls.EARTH_RADIUS_METERS * c

    @classmethod
    def haversine_distance_km(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Tính khoảng cách trắc địa theo km"""
        return cls.haversine_distance_meters(lat1, lon1, lat2, lon2) / 1000.0

    @classmethod
    def is_point_in_polygon(cls, lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
        """
        Kiểm tra điểm (lat, lon) có nằm trong đa giác hay không bằng thuật toán Ray-Casting.
        Polygon là danh sách các đỉnh [(lat_1, lon_1), (lat_2, lon_2), ...].
        """
        if not polygon or len(polygon) < 3:
            return True

        n = len(polygon)
        inside = False

        p1_lat, p1_lon = polygon[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = polygon[i % n]
            # Ray-casting từ điểm ra vô cùng theo trục hoành (lon)
            if min(p1_lat, p2_lat) < lat <= max(p1_lat, p2_lat):
                if lon <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        x_inters = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                    else:
                        x_inters = p1_lon
                    if p1_lon == p2_lon or lon <= x_inters:
                        inside = not inside
            p1_lat, p1_lon = p2_lat, p2_lon

        return inside

    @classmethod
    def distance_to_polygon_meters(cls, lat: float, lon: float, polygon: List[Tuple[float, float]]) -> float:
        """
        Tính khoảng cách gần nhất từ điểm đến biên đa giác (nếu điểm nằm ngoài).
        Xấp xỉ bằng khoảng cách nhỏ nhất tới các đoạn thẳng cạnh của đa giác.
        """
        if not polygon:
            return 0.0

        min_dist = float("inf")
        n = len(polygon)
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]
            # Khoảng cách tới điểm đầu mút
            d1 = cls.haversine_distance_meters(lat, lon, p1[0], p1[1])
            d2 = cls.haversine_distance_meters(lat, lon, p2[0], p2[1])
            mid_lat = (p1[0] + p2[0]) / 2.0
            mid_lon = (p1[1] + p2[1]) / 2.0
            d_mid = cls.haversine_distance_meters(lat, lon, mid_lat, mid_lon)
            min_dist = min(min_dist, d1, d2, d_mid)

        return min_dist if min_dist != float("inf") else 0.0

    @classmethod
    def run_dbscan(
        cls,
        points: List[Dict[str, Any]],
        eps_meters: float = 75.0,
        min_samples: int = 3
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Thuật toán phân cụm không gian dựa trên mật độ DBSCAN (Ester et al., 1996).
        points: danh sách dict gồm {'id', 'lat', 'lon', ...}
        Trả về: (clusters_list, noise_response_ids).
        """
        n = len(points)
        if n == 0:
            return [], []

        # Ma trận láng giềng
        neighbors: Dict[int, List[int]] = defaultdict(list)
        for i in range(n):
            for j in range(i + 1, n):
                dist = cls.haversine_distance_meters(
                    points[i]["lat"], points[i]["lon"],
                    points[j]["lat"], points[j]["lon"]
                )
                if dist <= eps_meters:
                    neighbors[i].append(j)
                    neighbors[j].append(i)

        visited = [False] * n
        cluster_assignment = [-1] * n  # -1 là noise
        cluster_id_counter = 0

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True

            # Láng giềng trực tiếp (bao gồm cả chính nó)
            cur_neighbors = [i] + neighbors[i]

            if len(cur_neighbors) < min_samples:
                cluster_assignment[i] = -1  # Tạm thời là noise
            else:
                # Tạo cụm mới
                cluster_assignment[i] = cluster_id_counter
                queue = list(neighbors[i])

                idx_in_queue = 0
                while idx_in_queue < len(queue):
                    nb = queue[idx_in_queue]
                    idx_in_queue += 1

                    if not visited[nb]:
                        visited[nb] = True
                        nb_neighbors = neighbors[nb]
                        if len(nb_neighbors) + 1 >= min_samples:
                            for item in nb_neighbors:
                                if item not in queue and item != i:
                                    queue.append(item)

                    if cluster_assignment[nb] == -1:
                        cluster_assignment[nb] = cluster_id_counter

                cluster_id_counter += 1

        # Gom nhóm kết quả thành các cụm
        clusters: List[Dict[str, Any]] = []
        noise_ids: List[str] = []

        for c_idx in range(cluster_id_counter):
            member_indices = [i for i, c in enumerate(cluster_assignment) if c == c_idx]
            member_points = [points[i] for i in member_indices]

            # Tính tọa độ tâm cụm (Centroid)
            center_lat = sum(p["lat"] for p in member_points) / len(member_points)
            center_lon = sum(p["lon"] for p in member_points) / len(member_points)

            # Tính bán kính cụm (khoảng cách xa nhất từ tâm tới một thành viên)
            radius = max(
                cls.haversine_distance_meters(center_lat, center_lon, p["lat"], p["lon"])
                for p in member_points
            )

            # Thông tin điều tra viên và thiết bị liên quan
            enums = list({p.get("enumerator_id") for p in member_points if p.get("enumerator_id")})
            devices = list({p.get("device_id") for p in member_points if p.get("device_id")})

            # Thời gian thu thập trong cụm
            timestamps = []
            for p in member_points:
                t_str = p.get("submitted_at")
                if t_str:
                    try:
                        dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                        timestamps.append(dt.timestamp())
                    except Exception:
                        pass

            time_span_seconds = max(timestamps) - min(timestamps) if len(timestamps) >= 2 else 0.0

            # Đánh giá dấu hiệu gian lận ngồi một chỗ (Coffee Shop Congregation)
            # Nếu cụm >= 3 người cùng 1 ĐTV hoặc hoàn tất trong vòng 2 giờ
            is_suspicious_coffee_shop = (
                len(member_points) >= 3 and
                (len(enums) <= 1 or time_span_seconds <= 7200.0)
            )

            if len(member_points) >= 5 or (len(enums) == 1 and len(member_points) >= 4):
                threat_level = "CRITICAL"
                recommended_action = "Nghi vấn nghiêm trọng: Khai khống tại chỗ (Coffee-shop fraud). Cần thẩm tra lại toàn bộ mẫu của cụm này."
            elif len(member_points) >= 3:
                threat_level = "HIGH"
                recommended_action = "Mật độ phản hồi bất thường tại tọa độ tĩnh. Cần đối chiếu chéo thời gian và bảng hỏi."
            else:
                threat_level = "MEDIUM"
                recommended_action = "Cụm mật độ nhỏ, tiếp tục theo dõi thêm số liệu."

            clusters.append({
                "cluster_id": f"GEO-CLUSTER-{c_idx + 1:02d}",
                "center_lat": round(center_lat, 6),
                "center_lon": round(center_lon, 6),
                "radius_meters": round(radius, 1),
                "member_count": len(member_points),
                "response_ids": [p["id"] for p in member_points],
                "enumerators_involved": enums,
                "devices_involved": devices,
                "time_span_seconds": round(time_span_seconds, 1),
                "is_suspicious_coffee_shop": is_suspicious_coffee_shop,
                "threat_level": threat_level,
                "recommended_action": recommended_action
            })

        # Sắp xếp các cụm theo số lượng thành viên và mức độ nghiêm trọng
        clusters.sort(key=lambda c: (c["threat_level"] == "CRITICAL", c["member_count"]), reverse=True)

        for i, c in enumerate(cluster_assignment):
            if c == -1:
                noise_ids.append(points[i]["id"])

        return clusters, noise_ids

    @classmethod
    def detect_impossible_travel_velocities(
        cls,
        points: List[Dict[str, Any]],
        max_speed_kmh: float = 120.0
    ) -> List[Dict[str, Any]]:
        """
        Phát hiện vận tốc di chuyển bất khả thi / GPS Spoofing giữa các lần nộp liên tiếp
        của cùng một điều tra viên hoặc cùng một thiết bị.
        """
        anomalies: List[Dict[str, Any]] = []

        # Gom nhóm theo enumerator_id hoặc device_id
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for p in points:
            key = p.get("enumerator_id") or p.get("device_id")
            if key:
                grouped[key].append(p)

        for actor_id, group in grouped.items():
            # Lọc các điểm có thời gian hợp lệ và sắp xếp theo submitted_at
            valid_pts = []
            for p in group:
                t_str = p.get("submitted_at")
                if t_str:
                    try:
                        dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                        valid_pts.append((dt, p))
                    except Exception:
                        pass

            valid_pts.sort(key=lambda x: x[0])

            for idx in range(len(valid_pts) - 1):
                t1, p1 = valid_pts[idx]
                t2, p2 = valid_pts[idx + 1]

                delta_sec = (t2 - t1).total_seconds()
                if delta_sec <= 0:
                    delta_sec = 1.0  # Tránh chia cho 0 nếu nộp cùng giây

                dist_km = cls.haversine_distance_km(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
                hours = delta_sec / 3600.0
                speed_kmh = dist_km / hours if hours > 0 else 0.0

                # Nếu khoảng cách > 0.5 km và tốc độ vượt ngưỡng tối đa
                if dist_km >= 0.5 and speed_kmh > max_speed_kmh and delta_sec <= 7200.0:
                    threat_level = "CRITICAL" if speed_kmh >= 250.0 else "HIGH"
                    anomalies.append({
                        "actor_id": actor_id,
                        "response_id_from": p1["id"],
                        "response_id_to": p2["id"],
                        "from_lat": p1["lat"],
                        "from_lon": p1["lon"],
                        "to_lat": p2["lat"],
                        "to_lon": p2["lon"],
                        "distance_km": round(dist_km, 2),
                        "time_delta_seconds": round(delta_sec, 1),
                        "speed_kmh": round(speed_kmh, 1),
                        "max_allowed_speed_kmh": max_speed_kmh,
                        "threat_level": threat_level,
                        "message": (
                            f"Vận tốc di chuyển bất khả thi v = {speed_kmh:.1f} km/h giữa 2 phản hồi "
                            f"(cách nhau {dist_km:.2f} km trong {delta_sec:.0f} giây). "
                            f"Nghi ngờ điều tra viên dùng phần mềm giả lập vị trí GPS (Fake GPS) hoặc chia sẻ tài khoản."
                        )
                    })

        # Sắp xếp theo tốc độ giảm dần
        anomalies.sort(key=lambda x: x["speed_kmh"], reverse=True)
        return anomalies

    @classmethod
    def compute_spatial_dispersion(
        cls,
        points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Tính toán độ phân tán không gian chuẩn (Spatial Standard Distance Deviation - Bachi 1962).
        SDD = sqrt( sum(Haversine(P_i, MeanP)^2) / N ).
        """
        N = len(points)
        if N == 0:
            return {
                "total_gps_points": 0,
                "center_lat": 0.0,
                "center_lon": 0.0,
                "standard_distance_meters": 0.0,
                "standard_distance_km": 0.0,
                "bounding_box": None,
                "territory_spread": "CHƯA CÓ DỮ LIỆU"
            }

        mean_lat = sum(p["lat"] for p in points) / N
        mean_lon = sum(p["lon"] for p in points) / N

        squared_distances = [
            cls.haversine_distance_meters(mean_lat, mean_lon, p["lat"], p["lon"]) ** 2
            for p in points
        ]
        sdd_meters = math.sqrt(sum(squared_distances) / N)
        sdd_km = sdd_meters / 1000.0

        min_lat = min(p["lat"] for p in points)
        max_lat = max(p["lat"] for p in points)
        min_lon = min(p["lon"] for p in points)
        max_lon = max(p["lon"] for p in points)

        if sdd_km < 0.3:
            spread = "SIÊU TẬP TRUNG (Bán kính < 300m, nghi ngờ mẫu bị dồn cục)"
        elif sdd_km < 3.0:
            spread = "CỤM CỘNG ĐỒNG / KHU PHỐ (Bán kính 300m - 3km)"
        elif sdd_km < 15.0:
            spread = "PHÂN BỐ TOÀN ĐỊA BÀN QUẬN / HUYỆN (3km - 15km)"
        else:
            spread = "DIỆN RỘNG LIÊN TỈNH / TOÀN VÙNG (> 15km)"

        return {
            "total_gps_points": N,
            "center_lat": round(mean_lat, 6),
            "center_lon": round(mean_lon, 6),
            "standard_distance_meters": round(sdd_meters, 1),
            "standard_distance_km": round(sdd_km, 2),
            "bounding_box": {
                "min_lat": round(min_lat, 6),
                "max_lat": round(max_lat, 6),
                "min_lon": round(min_lon, 6),
                "max_lon": round(max_lon, 6)
            },
            "territory_spread": spread
        }

    @classmethod
    def generate_academic_narrative(
        cls,
        total_responses: int,
        total_gps: int,
        clusters_count: int,
        suspicious_cluster_nodes: int,
        speed_anomalies_count: int,
        geofence_breaches_count: int,
        sdd_km: float
    ) -> str:
        """Sinh đoạn văn kiểm toán học thuật chuẩn ISO 20252:2019 và AAPOR"""
        coverage_pct = round(total_gps / max(1, total_responses) * 100, 1)
        if clusters_count == 0 and speed_anomalies_count == 0 and geofence_breaches_count == 0:
            return (
                f"Kiểm chứng không gian thực địa (Fieldwork Spatial Audit) theo tiêu chuẩn ISO 20252:2019 (Mục 4.5.3) "
                f"trên N = {total_gps}/{total_responses} phản hồi có tọa độ định vị GPS (tỷ lệ phủ {coverage_pct}%): "
                f"Không phát hiện hiện tượng tụ tập mật độ cao bất thường (DBSCAN ε = 75m không tạo cụm gian lận), "
                f"không ghi nhận vận tốc di chuyển phi thực tế (> 120 km/h) và không có vi phạm ranh giới địa bàn được cấp phép. "
                f"Độ phân tán không gian chuẩn đạt SDD = {sdd_km:.2f} km, thể hiện mẫu khảo sát được thu thập độc lập, "
                f"rải đều tự nhiên trên toàn bộ địa bàn nghiên cứu."
            )
        else:
            issues = []
            if clusters_count > 0:
                issues.append(f"{clusters_count} cụm mật độ tĩnh ({suspicious_cluster_nodes} phản hồi nghi vấn ngồi quán cà phê khai khống)")
            if speed_anomalies_count > 0:
                issues.append(f"{speed_anomalies_count} cảnh báo vận tốc dịch chuyển tức thời (nghi ngờ giả lập GPS Spoofing)")
            if geofence_breaches_count > 0:
                issues.append(f"{geofence_breaches_count} phản hồi nộp ngoài ranh giới vùng chỉ định (Geofence Breach)")

            issues_text = "; ".join(issues)
            return (
                f"CẢNH BÁO KIỂM TOÁN THỰC ĐỊA (AAPOR & ISO 20252:2019 Fieldwork Verification): "
                f"Hệ thống phát hiện dấu hiệu bất thường về tính xác thực không gian trên mẫu N = {total_gps} phản hồi có GPS: {issues_text}. "
                f"Độ phân tán không gian đạt SDD = {sdd_km:.2f} km. "
                f"Khuyến nghị kích hoạt quy trình cách ly (Quarantine Inspection) và triệu tập phỏng vấn viên phụ trách "
                f"để đối chiếu nhật ký công tác thực địa trước khi đưa dữ liệu vào báo cáo nghiệm thu."
            )

    @classmethod
    def analyze_survey_spatial(
        cls,
        survey_id: str,
        eps_meters: float = 75.0,
        min_samples: int = 3,
        max_speed_kmh: float = 120.0,
        geofence_polygon: Optional[List[Tuple[float, float]]] = None,
        scope: str = "all"
    ) -> Dict[str, Any]:
        """
        Thực thi phân tích toàn diện kiểm định không gian GPS của khảo sát.
        """
        with get_db() as conn:
            survey_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
            if not survey_row:
                raise ValueError("Không tìm thấy khảo sát.")

            # Đọc cấu hình geofence từ settings_json của khảo sát nếu không truyền polygon thủ công
            active_polygon = geofence_polygon
            if not active_polygon and survey_row["settings_json"]:
                try:
                    s_cfg = json.loads(survey_row["settings_json"] or "{}")
                    poly_cfg = s_cfg.get("geofence_polygon")
                    if poly_cfg and isinstance(poly_cfg, list):
                        active_polygon = [(p["lat"], p["lon"]) for p in poly_cfg if "lat" in p and "lon" in p]
                except Exception:
                    pass

            query = "SELECT * FROM responses WHERE survey_id = ?"
            params: List[Any] = [survey_id]
            if scope == "verified_clean":
                query += " AND (review_status = 'verified_clean' OR review_status = 'verified_valid')"
            query += " ORDER BY submitted_at ASC"

            resp_rows = conn.execute(query, params).fetchall()
            N = len(resp_rows)

            if N == 0:
                return {
                    "survey_id": survey_id,
                    "survey_title": survey_row["title"],
                    "scope": scope,
                    "total_responses": 0,
                    "total_gps_points": 0,
                    "gps_coverage_pct": 0.0,
                    "clusters": [],
                    "speed_anomalies": [],
                    "geofence_breaches": [],
                    "dispersion": cls.compute_spatial_dispersion([]),
                    "summary": {
                        "total_responses": 0,
                        "total_gps_points": 0,
                        "clusters_count": 0,
                        "suspicious_nodes_count": 0,
                        "speed_anomalies_count": 0,
                        "geofence_breaches_count": 0,
                        "data_integrity_index": 100.0,
                        "status": "CHƯA CÓ DỮ LIỆU"
                    },
                    "academic_narrative": "Chưa có phản hồi nào để kiểm định không gian thực địa."
                }

            # Trích xuất các điểm GPS hợp lệ
            gps_points: List[Dict[str, Any]] = []
            for r in resp_rows:
                rid = r["id"]
                client_meta = {}
                try:
                    client_meta = json.loads(r["client_metadata_json"] or "{}")
                except Exception:
                    pass

                pt = QualityEngine.extract_gps_point(client_meta)
                if pt:
                    lat, lon = pt
                    gps_points.append({
                        "id": rid,
                        "lat": round(lat, 6),
                        "lon": round(lon, 6),
                        "enumerator_id": r["enumerator_id"] or client_meta.get("enumerator_id") or "",
                        "device_id": client_meta.get("device_id") or "",
                        "submitted_at": r["submitted_at"],
                        "review_status": r["review_status"] or "unverified",
                        "quality_score": max(0.0, 100.0 - float(r["risk_score"] or 0.0))
                    })

            total_gps = len(gps_points)
            coverage_pct = round(total_gps / N * 100, 1)

            if total_gps == 0:
                return {
                    "survey_id": survey_id,
                    "survey_title": survey_row["title"],
                    "scope": scope,
                    "total_responses": N,
                    "total_gps_points": 0,
                    "gps_coverage_pct": 0.0,
                    "clusters": [],
                    "speed_anomalies": [],
                    "geofence_breaches": [],
                    "dispersion": cls.compute_spatial_dispersion([]),
                    "summary": {
                        "total_responses": N,
                        "total_gps_points": 0,
                        "clusters_count": 0,
                        "suspicious_nodes_count": 0,
                        "speed_anomalies_count": 0,
                        "geofence_breaches_count": 0,
                        "data_integrity_index": 100.0,
                        "status": "KHÔNG CÓ DỮ LIỆU GPS"
                    },
                    "academic_narrative": f"Khảo sát có N = {N} phản hồi nhưng không ghi nhận tọa độ GPS thực địa."
                }

            # 1. Phân cụm mật độ DBSCAN
            clusters, noise_ids = cls.run_dbscan(gps_points, eps_meters=eps_meters, min_samples=min_samples)

            # Đánh dấu các response_id thuộc cụm
            clustered_response_ids: Set[str] = set()
            for c in clusters:
                for rid in c["response_ids"]:
                    clustered_response_ids.add(rid)

            for p in gps_points:
                p["is_clustered"] = p["id"] in clustered_response_ids

            # 2. Phát hiện vận tốc di chuyển bất khả thi (Impossible Travel)
            speed_anomalies = cls.detect_impossible_travel_velocities(gps_points, max_speed_kmh=max_speed_kmh)

            # 3. Kiểm định ranh giới Geofence Polygon (nếu có)
            geofence_breaches: List[Dict[str, Any]] = []
            if active_polygon and len(active_polygon) >= 3:
                for p in gps_points:
                    is_in = cls.is_point_in_polygon(p["lat"], p["lon"], active_polygon)
                    if not is_in:
                        excess_dist = cls.distance_to_polygon_meters(p["lat"], p["lon"], active_polygon)
                        geofence_breaches.append({
                            "response_id": p["id"],
                            "lat": p["lat"],
                            "lon": p["lon"],
                            "submitted_at": p["submitted_at"],
                            "excess_distance_meters": round(excess_dist, 1),
                            "enumerator_id": p.get("enumerator_id"),
                            "severity": "HIGH" if excess_dist > 500.0 else "MEDIUM"
                        })

            # 4. Độ phân tán không gian chuẩn (SDD)
            dispersion = cls.compute_spatial_dispersion(gps_points)

            # 5. Đánh giá chỉ số liêm chính không gian (Spatial Integrity Index)
            suspicious_count = len(clustered_response_ids)
            speed_anom_count = len(speed_anomalies)
            breach_count = len(geofence_breaches)

            deduction = (
                (suspicious_count / total_gps * 40.0) +
                min(30.0, speed_anom_count * 15.0) +
                min(30.0, breach_count * 5.0)
            )
            spatial_integrity_index = max(0.0, round(100.0 - deduction, 1))

            if suspicious_count == 0 and speed_anom_count == 0 and breach_count == 0:
                status = "LIÊM CHÍNH KHÔNG GIAN CAO (Tọa độ phân tán tự nhiên)"
            elif len(clusters) > 0 or speed_anom_count > 0:
                status = f"CẢNH BÁO: Phát hiện {len(clusters)} cụm mật độ và {speed_anom_count} bất thường vận tốc"
            else:
                status = f"CHÚ Ý: Phát hiện {breach_count} phản hồi ngoài ranh giới vùng"

            academic_narrative = cls.generate_academic_narrative(
                total_responses=N,
                total_gps=total_gps,
                clusters_count=len(clusters),
                suspicious_cluster_nodes=suspicious_count,
                speed_anomalies_count=speed_anom_count,
                geofence_breaches_count=breach_count,
                sdd_km=dispersion["standard_distance_km"]
            )

            return {
                "survey_id": survey_id,
                "survey_title": survey_row["title"],
                "scope": scope,
                "total_responses": N,
                "total_gps_points": total_gps,
                "gps_coverage_pct": coverage_pct,
                "eps_meters": eps_meters,
                "min_samples": min_samples,
                "max_speed_kmh": max_speed_kmh,
                "has_geofence_polygon": bool(active_polygon and len(active_polygon) >= 3),
                "clusters": clusters,
                "speed_anomalies": speed_anomalies,
                "geofence_breaches": geofence_breaches,
                "dispersion": dispersion,
                "gps_points": gps_points[:150],  # Trả về tối đa 150 điểm cho visualizer map
                "summary": {
                    "total_responses": N,
                    "total_gps_points": total_gps,
                    "clusters_count": len(clusters),
                    "suspicious_nodes_count": suspicious_count,
                    "speed_anomalies_count": speed_anom_count,
                    "geofence_breaches_count": breach_count,
                    "spatial_integrity_index": spatial_integrity_index,
                    "status": status
                },
                "academic_narrative": academic_narrative
            }
