"""
Integration tests for DataTrust Geographic Spatial Clustering & Geo-Fencing API routes
(POST & GET /api/surveys/{survey_id}/analytics/spatial)
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
try:
    from app.main import app
except ModuleNotFoundError:
    from backend.app.main import app

client = TestClient(app)


def test_spatial_empty_survey():
    """Kiểm thử khảo sát khi chưa có phản hồi nào (N = 0)"""
    res = client.post("/api/surveys", json={
        "title": "Khảo sát chưa có phản hồi không gian",
        "description": "Empty spatial survey test"
    })
    survey_id = res.json()["id"]

    # 1. Gọi GET
    get_res = client.get(f"/api/surveys/{survey_id}/analytics/spatial")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["total_responses"] == 0
    assert data["total_gps_points"] == 0
    assert data["gps_coverage_pct"] == 0.0
    assert data["clusters"] == []
    assert data["summary"]["status"] == "CHƯA CÓ DỮ LIỆU"

    # 2. Gọi POST
    post_res = client.post(f"/api/surveys/{survey_id}/analytics/spatial", json={
        "eps_meters": 50.0,
        "min_samples": 3,
        "scope": "all"
    })
    assert post_res.status_code == 200
    assert post_res.json()["total_responses"] == 0


def test_spatial_responses_without_gps():
    """Kiểm thử khảo sát có phản hồi nhưng không có tọa độ GPS"""
    res = client.post("/api/surveys", json={
        "title": "Khảo sát không có GPS",
        "description": "No GPS metadata survey test"
    })
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    # Thêm câu hỏi trước khi xuất bản
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [{
            "id": "q_test",
            "question_type": "short_text",
            "title": "Ý kiến",
            "is_required": False
        }]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    # Submit 2 responses without client_metadata GPS
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-24T08:00:00Z",
        "submitted_at": "2026-10-24T08:05:00Z",
        "client_metadata": {"device_id": "dev_no_gps_1"},
        "answers": {"q_test": "Bình luận 1"}
    })
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-24T08:10:00Z",
        "submitted_at": "2026-10-24T08:15:00Z",
        "client_metadata": {"device_id": "dev_no_gps_2"},
        "answers": {"q_test": "Bình luận 2"}
    })

    get_res = client.get(f"/api/surveys/{survey_id}/analytics/spatial")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["total_responses"] == 2
    assert data["total_gps_points"] == 0
    assert data["gps_coverage_pct"] == 0.0
    assert "KHÔNG CÓ DỮ LIỆU GPS" in data["summary"]["status"]


def test_spatial_clustering_and_impossible_velocity_audit():
    """
    Kiểm thử tích hợp toàn diện:
    1. Cụm cà phê DBSCAN: 4 phản hồi trong bán kính 20m cùng 1 điều tra viên enum_cafe_01.
    2. Vận tốc bất khả thi: Phản hồi thứ 5 cách 20km chỉ sau 1 phút bởi enum_cafe_01.
    3. Vi phạm Geofence đa giác: Phản hồi thứ 6 nằm ngoài ranh giới cho phép.
    """
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Thực địa Đô thị Toàn diện",
        "description": "Comprehensive Spatial Fraud Test"
    })
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    # Thêm câu hỏi trước khi xuất bản
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [{
            "id": "q_location_satisfaction",
            "question_type": "rating",
            "title": "Đánh giá vị trí",
            "is_required": False
        }]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    base_time = datetime.now(timezone.utc)
    base_lat, base_lon = 10.7760, 106.7000  # Khu vực trung tâm

    # 1. Bốn phản hồi tại cùng 1 quán cà phê (DBSCAN cluster)
    for i in range(4):
        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (base_time + timedelta(minutes=i * 5)).isoformat(),
            "submitted_at": (base_time + timedelta(minutes=i * 5 + 3)).isoformat(),
            "client_metadata": {
                "latitude": base_lat + (i * 0.00003),
                "longitude": base_lon + (i * 0.00002),
                "enumerator_id": "enum_cafe_01",
                "device_id": "tablet_field_01"
            },
            "answers": {}
        })
        assert submit_res.status_code == 201

    # 2. Phản hồi thứ 5: 1 phút sau nhưng ở tọa độ cách 20km (Teleportation / Fake GPS)
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (base_time + timedelta(minutes=21)).isoformat(),
        "submitted_at": (base_time + timedelta(minutes=22)).isoformat(),
        "client_metadata": {
            "latitude": 10.9500,  # Cách ~20km về phía Bắc
            "longitude": 106.7500,
            "enumerator_id": "enum_cafe_01",
            "device_id": "tablet_field_01"
        },
        "answers": {}
    })

    # 3. Phản hồi thứ 6: Thu thập bởi điều tra viên độc lập hợp lệ ở ngoại thành
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (base_time + timedelta(minutes=60)).isoformat(),
        "submitted_at": (base_time + timedelta(minutes=70)).isoformat(),
        "client_metadata": {
            "latitude": 10.7200,  # Quận 7
            "longitude": 106.7200,
            "enumerator_id": "enum_valid_02",
            "device_id": "tablet_field_02"
        },
        "answers": {}
    })

    # 4. Định nghĩa đa giác ranh giới Geofence (chỉ bao gồm khu vực nội thành Quận 1)
    geofence_poly = [
        [10.7600, 106.6800],
        [10.7600, 106.7150],
        [10.7950, 106.7150],
        [10.7950, 106.6800]
    ]

    # 5. Gọi API POST /spatial
    post_res = client.post(f"/api/surveys/{survey_id}/analytics/spatial", json={
        "eps_meters": 75.0,
        "min_samples": 3,
        "max_speed_kmh": 100.0,
        "geofence_polygon": geofence_poly,
        "scope": "all"
    })
    assert post_res.status_code == 200
    data = post_res.json()

    assert data["total_responses"] == 6
    assert data["total_gps_points"] == 6
    assert data["gps_coverage_pct"] == 100.0

    # Kiểm tra phát hiện cụm cà phê
    clusters = data["clusters"]
    assert len(clusters) == 1
    assert clusters[0]["member_count"] == 4
    assert clusters[0]["is_suspicious_coffee_shop"] is True
    assert clusters[0]["threat_level"] == "CRITICAL"
    assert "enum_cafe_01" in clusters[0]["enumerators_involved"]

    # Kiểm tra phát hiện vận tốc bất khả thi
    speed_anoms = data["speed_anomalies"]
    assert len(speed_anoms) >= 1
    fastest = speed_anoms[0]
    assert fastest["actor_id"] == "enum_cafe_01"
    assert fastest["speed_kmh"] > 200.0
    assert fastest["threat_level"] == "CRITICAL"

    # Kiểm tra phát hiện vi phạm ranh giới Geofence (phản hồi 5 và 6 đều nằm ngoài poly)
    breaches = data["geofence_breaches"]
    assert len(breaches) >= 2

    # Kiểm tra độ phân tán và trích dẫn ISO
    dispersion = data["dispersion"]
    assert dispersion["total_gps_points"] == 6
    assert dispersion["standard_distance_km"] > 1.0

    summary = data["summary"]
    assert summary["clusters_count"] == 1
    assert summary["speed_anomalies_count"] >= 1
    assert summary["geofence_breaches_count"] >= 2
    assert summary["spatial_integrity_index"] < 90.0
    assert "CẢNH BÁO" in summary["status"]
    assert "ISO 20252:2019" in data["academic_narrative"]
