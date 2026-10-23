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
