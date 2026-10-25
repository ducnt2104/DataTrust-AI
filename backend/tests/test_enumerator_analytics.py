import json
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_enumerator_anomaly_analytics(client):
    # 1. Tạo survey
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Đánh giá Điều tra viên",
        "description": "Thử nghiệm phân tích độ lệch phân bố và phương sai theo điều tra viên"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]

    # 2. Thêm 4 câu hỏi trắc nghiệm / thang đo
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Khu vực cư trú",
                "is_required": True,
                "options": [{"id": "kv1", "label": "Khu vực 1"}, {"id": "kv2", "label": "Khu vực 2"}, {"id": "kv3", "label": "Khu vực 3"}]
            },
            {
                "order_index": 1,
                "question_type": "likert",
                "title": "Mức độ hài lòng hạ tầng",
                "is_required": True,
                "options": []
            },
            {
                "order_index": 2,
                "question_type": "likert",
                "title": "Mức độ hài lòng an ninh",
                "is_required": True,
                "options": []
            },
            {
                "order_index": 3,
                "question_type": "likert",
                "title": "Mức độ hài lòng y tế",
                "is_required": True,
                "options": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")
    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    q_ids = [q["id"] for q in survey_data["questions"]]

    # 3. Nạp 5 phản hồi đa dạng của điều tra viên trung thực DTV-CLEAN
    clean_varied_data = [
        {q_ids[0]: "kv1", q_ids[1]: "4", q_ids[2]: "5", q_ids[3]: "3"},
        {q_ids[0]: "kv2", q_ids[1]: "2", q_ids[2]: "3", q_ids[3]: "4"},
        {q_ids[0]: "kv1", q_ids[1]: "5", q_ids[2]: "4", q_ids[3]: "5"},
        {q_ids[0]: "kv3", q_ids[1]: "3", q_ids[2]: "2", q_ids[3]: "3"},
        {q_ids[0]: "kv2", q_ids[1]: "4", q_ids[2]: "3", q_ids[3]: "2"},
    ]
    for ans in clean_varied_data:
        client.post(f"/api/public/surveys/{survey_data['public_slug']}/submit", json={
            "started_at": "2026-10-23T08:00:00Z",
            "submitted_at": "2026-10-23T08:02:00Z",
            "answers": ans,
            "source": "online_form",
            "enumerator_id": "DTV-CLEAN"
        })

    # 4. Nạp 5 phản hồi gian lận (y hệt nhau 100% hoặc siêu tốc) của DTV-FRAUD
    fraud_identical_data = [
        {q_ids[0]: "kv1", q_ids[1]: "5", q_ids[2]: "5", q_ids[3]: "5"},
        {q_ids[0]: "kv1", q_ids[1]: "5", q_ids[2]: "5", q_ids[3]: "5"},
        {q_ids[0]: "kv1", q_ids[1]: "5", q_ids[2]: "5", q_ids[3]: "5"},
        {q_ids[0]: "kv1", q_ids[1]: "5", q_ids[2]: "5", q_ids[3]: "5"},
        {q_ids[0]: "kv1", q_ids[1]: "5", q_ids[2]: "5", q_ids[3]: "5"},
    ]
    for ans in fraud_identical_data:
        client.post(f"/api/public/surveys/{survey_data['public_slug']}/submit", json={
            "started_at": "2026-10-23T08:00:00Z",
            "submitted_at": "2026-10-23T08:00:04Z",  # 4 giây
            "answers": ans,
            "source": "online_form",
            "enumerator_id": "DTV-FRAUD"
        })

    # 5. Gọi API thống kê điều tra viên
    enum_res = client.get(f"/api/surveys/{survey_id}/enumerators")
    assert enum_res.status_code == 200
    res_data = enum_res.json()

    assert res_data["total_enumerators"] == 2
    assert res_data["total_field_responses"] == 10

    enum_map = {e["enumerator_id"]: e for e in res_data["enumerators"]}
    assert "DTV-CLEAN" in enum_map
    assert "DTV-FRAUD" in enum_map

    clean_metrics = enum_map["DTV-CLEAN"]
    fraud_metrics = enum_map["DTV-FRAUD"]

    # DTV-CLEAN phải có rủi ro thấp
    assert clean_metrics["is_anomaly"] is False
    assert clean_metrics["avg_risk_score"] < 40.0

    # DTV-FRAUD phải bị gắn cờ bất thường
    assert fraud_metrics["is_anomaly"] is True
    assert fraud_metrics["avg_risk_score"] >= 70.0
    assert fraud_metrics["high_risk_rate"] >= 0.80
    assert len(fraud_metrics["anomaly_reasons"]) > 0

    # 6. Kiểm tra API xuất CSV báo cáo giám sát điều tra viên
    export_res = client.get(f"/api/surveys/{survey_id}/enumerators/export")
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    assert "attachment; filename=" in export_res.headers["content-disposition"]
    csv_text = export_res.text
    assert "Mã Điều tra viên" in csv_text
    assert "DTV-CLEAN" in csv_text
    assert "DTV-FRAUD" in csv_text
    assert "CẢNH BÁO" in csv_text
    assert "Độ phủ GPS (%)" in csv_text
    assert "Cảnh báo Tốc độ phi lý" in csv_text

def test_enumerator_gps_geofencing_and_teleportation(client):
    # 1. Tạo survey
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm định Tọa độ GPS Thực Địa",
        "description": "Kiểm tra phát hiện di chuyển phi lý và cụm tọa độ tĩnh"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Địa bàn khảo sát",
                "is_required": True,
                "options": [{"id": "o1", "label": "Địa bàn A"}, {"id": "o2", "label": "Địa bàn B"}]
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")
    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    q_id = survey_data["questions"][0]["id"]

    # 2. Điều tra viên DTV-TELEPORT: 2 phiếu cách nhau 1140 km chỉ trong 3 phút (TP.HCM -> Hà Nội)
    client.post(f"/api/public/surveys/{survey_data['public_slug']}/submit", json={
        "started_at": "2026-10-23T09:00:00Z",
        "submitted_at": "2026-10-23T09:02:00Z",
        "answers": {q_id: "o1"},
        "source": "online_form",
        "enumerator_id": "DTV-TELEPORT",
        "client_metadata": {"latitude": 10.7769, "longitude": 106.7009}  # TP.HCM
    })
    client.post(f"/api/public/surveys/{survey_data['public_slug']}/submit", json={
        "started_at": "2026-10-23T09:03:00Z",
        "submitted_at": "2026-10-23T09:05:00Z",
        "answers": {q_id: "o2"},
        "source": "online_form",
        "enumerator_id": "DTV-TELEPORT",
        "client_metadata": {"latitude": 21.0285, "longitude": 105.8542}  # Hà Nội
    })

    # 3. Điều tra viên DTV-STATIONARY: 4 phiếu liên tiếp tại cùng 1 tọa độ chính xác (<5m)
    for i in range(4):
        client.post(f"/api/public/surveys/{survey_data['public_slug']}/submit", json={
            "started_at": f"2026-10-23T10:0{i}:00Z",
            "submitted_at": f"2026-10-23T10:0{i+1}:00Z",
            "answers": {q_id: "o1" if i % 2 == 0 else "o2"},
            "source": "online_form",
            "enumerator_id": "DTV-STATIONARY",
            "client_metadata": {"lat": 10.775000, "lng": 106.700000}
        })

    # 4. Kiểm tra phân tích điều tra viên
    res = client.get(f"/api/surveys/{survey_id}/enumerators")
    assert res.status_code == 200
    data = res.json()
    enum_map = {e["enumerator_id"]: e for e in data["enumerators"]}

    teleport_metrics = enum_map["DTV-TELEPORT"]
    assert teleport_metrics["impossible_speed_detected"] is True
    assert teleport_metrics["is_anomaly"] is True
    assert teleport_metrics["max_speed_kmh"] is not None
    assert teleport_metrics["max_speed_kmh"] > 1000.0  # Tốc độ máy bay phản lực
    assert any("phi lý" in r for r in teleport_metrics["anomaly_reasons"])

    stationary_metrics = enum_map["DTV-STATIONARY"]
    assert stationary_metrics["stationary_cluster_detected"] is True
    assert stationary_metrics["is_anomaly"] is True
    assert any("tọa độ tĩnh" in r for r in stationary_metrics["anomaly_reasons"])

def test_paper_omr_audit_export(client):
    # 1. Tạo survey và lấy template
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Phiếu Giấy OMR Kiểm Định",
        "description": "Kiểm tra xuất báo cáo audit phiếu quét giấy OMR"
    })
    survey_id = res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Đánh giá chất lượng phục vụ",
                "is_required": True,
                "options": [{"id": "o1", "label": "Tốt"}, {"id": "o2", "label": "Kém"}]
            }
        ]
    })
    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    q_id = survey_data["questions"][0]["id"]

    # 2. Nạp một phiếu giấy OMR qua API ingest
    ingest_res = client.post(f"/api/surveys/{survey_id}/paper/ingest", json={
        "form_id": "FORM-TEST-999",
        "enumerator_id": "DTV-PAPER-01",
        "answers": {q_id: "o1"},
        "omr_confidence": 0.96,
        "manual_corrections": [
            {"question_id": q_id, "original": "o2", "corrected": "o1", "reason": "Tẩy xóa mờ"}
        ]
    })
    assert ingest_res.status_code == 201

    # 3. Gọi API xuất báo cáo kiểm định OMR
    export_res = client.get(f"/api/surveys/{survey_id}/paper/export-audit")
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    assert "attachment; filename=" in export_res.headers["content-disposition"]
    csv_text = export_res.text
    assert "Mã Phiếu Giấy (Form ID)" in csv_text
    assert "FORM-TEST-999" in csv_text
    assert "DTV-PAPER-01" in csv_text
    assert "96.0%" in csv_text
    assert "Độ tin cậy OMR (%)" in csv_text

def test_enumerator_geofencing_perimeter_compliance(client):
    """Kiểm tra phát hiện điều tra viên thu thập dữ liệu ngoài ranh giới địa lý (Geofencing Breach)"""
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Nghiên Cứu Địa Bàn Phố Cổ",
        "description": "Kiểm tra ranh giới địa lý thực địa",
        "settings": {
            "quality_settings": {
                "geofence": {
                    "enabled": True,
                    "target_lat": 21.0333,
                    "target_lon": 105.8500,
                    "max_radius_km": 2.0,
                    "location_name": "Phố Cổ Hà Nội"
                }
            }
        }
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Mức độ hài lòng du lịch",
                "is_required": True,
                "options": [{"id": "o1", "label": "Tốt"}, {"id": "o2", "label": "Kém"}]
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")
    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    q_id = survey_data["questions"][0]["id"]
    slug = survey_data["public_slug"]

    # 1. Điều tra viên DTV-VALID: thu thập tại Hoàn Kiếm (cách tâm ~150 mét)
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T11:00:00Z",
        "submitted_at": "2026-10-23T11:02:00Z",
        "answers": {q_id: "o1"},
        "source": "online_form",
        "enumerator_id": "DTV-VALID",
        "client_metadata": {"latitude": 21.0335, "longitude": 105.8505}
    })

    # 2. Điều tra viên DTV-BREACH: thu thập tại Cầu Giấy (cách tâm ~7.2 km > 2.0 km)
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T11:05:00Z",
        "submitted_at": "2026-10-23T11:07:00Z",
        "answers": {q_id: "o2"},
        "source": "online_form",
        "enumerator_id": "DTV-BREACH",
        "client_metadata": {"latitude": 21.0370, "longitude": 105.7800}
    })

    # 3. Phân tích điều tra viên
    enum_res = client.get(f"/api/surveys/{survey_id}/enumerators")
    assert enum_res.status_code == 200
    data = enum_res.json()

    assert data["geofence_setting"] is not None
    assert data["geofence_setting"]["enabled"] is True
    assert data["geofence_setting"]["max_radius_km"] == 2.0

    enum_map = {e["enumerator_id"]: e for e in data["enumerators"]}
    valid_enum = enum_map["DTV-VALID"]
    breach_enum = enum_map["DTV-BREACH"]

    assert valid_enum["geofence_breach_count"] == 0
    assert valid_enum["is_anomaly"] is False
    assert valid_enum["gps_points"][0]["is_geofence_breach"] is False
    assert valid_enum["gps_points"][0]["distance_from_center_km"] < 1.0

    assert breach_enum["geofence_breach_count"] == 1
    assert breach_enum["is_anomaly"] is True
    assert breach_enum["gps_points"][0]["is_geofence_breach"] is True
    assert breach_enum["gps_points"][0]["distance_from_center_km"] > 7.0
    assert any("Vi phạm ranh giới địa lý" in r for r in breach_enum["anomaly_reasons"])

    # 4. Kiểm tra xuất CSV kiểm toán điều tra viên
    export_res = client.get(f"/api/surveys/{survey_id}/enumerators/export")
    assert export_res.status_code == 200
    csv_text = export_res.text
    assert "Số điểm vi phạm ranh giới" in csv_text
    assert "Cảnh báo Vi phạm vùng" in csv_text
    assert "DTV-BREACH" in csv_text

