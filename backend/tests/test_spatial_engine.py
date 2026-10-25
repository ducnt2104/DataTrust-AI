"""
Unit tests for DataTrust SpatialEngine (backend/app/engine/spatial_engine.py)
Kiểm thử thuật toán phân cụm mật độ không gian DBSCAN, nhận diện gian lận ngồi một chỗ (Coffee-Shop Fraud),
vận tốc di chuyển bất khả thi (Teleportation / GPS Spoofing), và kiểm tra ranh giới đa giác Ray-Casting.
"""

import pytest
try:
    from app.engine.spatial_engine import SpatialEngine
except ModuleNotFoundError:
    from backend.app.engine.spatial_engine import SpatialEngine


def test_haversine_distance_calculations():
    """Kiểm thử độ chính xác khoảng cách trắc địa mặt cầu (Haversine Formula)"""
    # Tọa độ Hồ Con Rùa (Q.3, TP.HCM) và Nhà thờ Đức Bà (Q.1, TP.HCM): cách nhau khoảng ~650m
    lat1, lon1 = 10.7828, 106.6958
    lat2, lon2 = 10.7798, 106.6990

    dist_m = SpatialEngine.haversine_distance_meters(lat1, lon1, lat2, lon2)
    dist_km = SpatialEngine.haversine_distance_km(lat1, lon1, lat2, lon2)

    assert 400.0 < dist_m < 700.0
    assert abs(dist_m / 1000.0 - dist_km) < 1e-5

    # Khoảng cách giữa 2 điểm trùng nhau
    assert SpatialEngine.haversine_distance_meters(lat1, lon1, lat1, lon1) == 0.0


def test_ray_casting_point_in_polygon():
    """Kiểm thử thuật toán Ray-Casting kiểm định ranh giới Geofence đa giác bất kỳ"""
    # Đa giác hình vuông bao quanh trung tâm Quận 1
    polygon = [
        (10.7700, 106.6900),
        (10.7700, 106.7100),
        (10.7900, 106.7100),
        (10.7900, 106.6900)
    ]

    # 1. Điểm nằm bên trong đa giác
    inside_pt = (10.7800, 106.7000)
    assert SpatialEngine.is_point_in_polygon(inside_pt[0], inside_pt[1], polygon) is True

    # 2. Điểm nằm bên ngoài đa giác
    outside_pt = (10.8200, 106.7500)
    assert SpatialEngine.is_point_in_polygon(outside_pt[0], outside_pt[1], polygon) is False

    # 3. Đo khoảng cách tới biên đa giác khi điểm ở ngoài
    dist_outside = SpatialEngine.distance_to_polygon_meters(outside_pt[0], outside_pt[1], polygon)
    assert dist_outside > 1000.0


def test_dbscan_clustering_coffee_shop_fraud():
    """
    Kiểm thử thuật toán DBSCAN phát hiện cụm mật độ tĩnh:
    Điều tra viên ngồi quán cà phê (bán kính 30m) thu thập 5 phiếu liên tiếp.
    2 phiếu khác thu thập rải rác ngoài thực địa.
    """
    # 5 điểm tại cùng 1 quán cà phê (độ lệch < 0.0002 độ ~ 22m)
    base_lat, base_lon = 10.7828, 106.6958
    points = [
        {"id": "resp-01", "lat": base_lat + 0.00005, "lon": base_lon + 0.00005, "enumerator_id": "enum_lazy", "submitted_at": "2026-10-24T08:00:00Z"},
        {"id": "resp-02", "lat": base_lat - 0.00005, "lon": base_lon + 0.00002, "enumerator_id": "enum_lazy", "submitted_at": "2026-10-24T08:10:00Z"},
        {"id": "resp-03", "lat": base_lat + 0.00002, "lon": base_lon - 0.00008, "enumerator_id": "enum_lazy", "submitted_at": "2026-10-24T08:20:00Z"},
        {"id": "resp-04", "lat": base_lat - 0.00003, "lon": base_lon - 0.00002, "enumerator_id": "enum_lazy", "submitted_at": "2026-10-24T08:35:00Z"},
        {"id": "resp-05", "lat": base_lat + 0.00008, "lon": base_lon + 0.00001, "enumerator_id": "enum_lazy", "submitted_at": "2026-10-24T08:45:00Z"},
        # 2 điểm độc lập cách xa 1.5km và 3km
        {"id": "resp-clean-1", "lat": 10.7950, "lon": 106.7100, "enumerator_id": "enum_diligent", "submitted_at": "2026-10-24T09:00:00Z"},
        {"id": "resp-clean-2", "lat": 10.8100, "lon": 106.7300, "enumerator_id": "enum_diligent", "submitted_at": "2026-10-24T10:00:00Z"}
    ]

    clusters, noise_ids = SpatialEngine.run_dbscan(points, eps_meters=75.0, min_samples=3)

    assert len(clusters) == 1
    coffee_cluster = clusters[0]
    assert coffee_cluster["member_count"] == 5
    assert set(coffee_cluster["response_ids"]) == {"resp-01", "resp-02", "resp-03", "resp-04", "resp-05"}
    assert coffee_cluster["radius_meters"] < 50.0
    assert coffee_cluster["is_suspicious_coffee_shop"] is True
    assert coffee_cluster["threat_level"] == "CRITICAL"
    assert "Coffee-shop" in coffee_cluster["recommended_action"]

    assert len(noise_ids) == 2
    assert set(noise_ids) == {"resp-clean-1", "resp-clean-2"}


def test_detect_impossible_travel_velocities():
    """Kiểm thử phát hiện dịch chuyển tức thời (Teleportation / GPS Spoofing)"""
    points = [
        # Điểm 1: 08:00:00 tại Quận 1 (10.7750, 106.7000)
        {"id": "r1", "lat": 10.7750, "lon": 106.7000, "enumerator_id": "enum_speedy", "submitted_at": "2026-10-24T08:00:00Z"},
        # Điểm 2: 08:02:00 tại Thủ Đức cách 15km chỉ sau 2 phút (Vận tốc ~ 450 km/h)
        {"id": "r2", "lat": 10.8500, "lon": 106.7800, "enumerator_id": "enum_speedy", "submitted_at": "2026-10-24T08:02:00Z"},
        # Điểm 3: 08:30:00 cách 3km sau 28 phút (Vận tốc bình thường ~ 6.4 km/h)
        {"id": "r3", "lat": 10.8600, "lon": 106.8000, "enumerator_id": "enum_speedy", "submitted_at": "2026-10-24T08:30:00Z"}
    ]

    anomalies = SpatialEngine.detect_impossible_travel_velocities(points, max_speed_kmh=120.0)

    assert len(anomalies) == 1
    anom = anomalies[0]
    assert anom["actor_id"] == "enum_speedy"
    assert anom["response_id_from"] == "r1"
    assert anom["response_id_to"] == "r2"
    assert anom["distance_km"] > 10.0
    assert anom["speed_kmh"] > 300.0
    assert anom["threat_level"] == "CRITICAL"
    assert "Fake GPS" in anom["message"]


def test_spatial_dispersion_calculation():
    """Kiểm thử tính toán độ phân tán không gian chuẩn (Spatial Standard Distance SDD)"""
    points = [
        {"id": "p1", "lat": 10.7700, "lon": 106.6900},
        {"id": "p2", "lat": 10.7800, "lon": 106.7000},
        {"id": "p3", "lat": 10.7900, "lon": 106.7100}
    ]

    disp = SpatialEngine.compute_spatial_dispersion(points)

    assert disp["total_gps_points"] == 3
    assert abs(disp["center_lat"] - 10.7800) < 1e-4
    assert abs(disp["center_lon"] - 106.7000) < 1e-4
    assert disp["standard_distance_meters"] > 500.0
    assert disp["bounding_box"]["min_lat"] == 10.7700
    assert disp["bounding_box"]["max_lat"] == 10.7900


def test_academic_narrative_iso20252():
    """Kiểm thử câu diễn giải học thuật theo chuẩn ISO 20252 Section 4.5.3"""
    clean_narrative = SpatialEngine.generate_academic_narrative(
        total_responses=100,
        total_gps=95,
        clusters_count=0,
        suspicious_cluster_nodes=0,
        speed_anomalies_count=0,
        geofence_breaches_count=0,
        sdd_km=4.52
    )
    assert "ISO 20252:2019" in clean_narrative
    assert "Không phát hiện hiện tượng tụ tập mật độ cao" in clean_narrative

    fraud_narrative = SpatialEngine.generate_academic_narrative(
        total_responses=100,
        total_gps=90,
        clusters_count=2,
        suspicious_cluster_nodes=8,
        speed_anomalies_count=1,
        geofence_breaches_count=3,
        sdd_km=1.20
    )
    assert "CẢNH BÁO KIỂM TOÁN THỰC ĐỊA" in fraud_narrative
    assert "2 cụm mật độ tĩnh" in fraud_narrative
    assert "GPS Spoofing" in fraud_narrative
