"""
Integration tests for Rasch Model & Item Response Theory (IRT) API routes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rasch_model_analytics_routes():
    # 1. Create a survey
    res = client.post("/api/surveys", json={
        "title": "Khảo Sát Tâm Trắc Học Đánh Giá Năng Lực Số Rasch 1-PL",
        "description": "Nghiên cứu thang đo Rasch và xây dựng bản đồ Wright Map",
        "instructions": "Trả lời các câu hỏi sau"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    # 2. Add 4 Likert/Rating questions with varying difficulty
    q_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_easy",
                "order_index": 0,
                "question_type": "likert",
                "title": "Tôi có thể sử dụng trình duyệt web cơ bản",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "id": "q_med_1",
                "order_index": 1,
                "question_type": "likert",
                "title": "Tôi có thể phân tích số liệu trên bảng tính Excel",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "id": "q_med_2",
                "order_index": 2,
                "question_type": "likert",
                "title": "Tôi có thể thiết lập xác thực 2 lớp bảo mật số",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "id": "q_hard",
                "order_index": 3,
                "question_type": "likert",
                "title": "Tôi có thể viết script tự động hóa kiểm định dữ liệu",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })
    assert q_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    qids = [q["id"] for q in public_q]

    # 3. Submit 10 responses with distinct response profiles
    # Group A (High ability): high scores across all items
    for i in range(4):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                qids[0]: 5,
                qids[1]: 5,
                qids[2]: 4,
                qids[3]: 4 + (i % 2)
            },
            "started_at": f"2026-10-23T14:00:{i:02d}Z",
            "submitted_at": f"2026-10-23T14:01:{i*10:02d}Z",
            "client_metadata": {"device_id": f"high_{i}"}
        })

    # Group B (Medium ability): high on easy, low on hard
    for i in range(4):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                qids[0]: 5,
                qids[1]: 4,
                qids[2]: 2,
                qids[3]: 1
            },
            "started_at": f"2026-10-23T14:05:{i:02d}Z",
            "submitted_at": f"2026-10-23T14:06:{i*10:02d}Z",
            "client_metadata": {"device_id": f"med_{i}"}
        })

    # Group C (Low ability): low scores everywhere
    for i in range(4):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                qids[0]: 3,
                qids[1]: 2,
                qids[2]: 1,
                qids[3]: 1
            },
            "started_at": f"2026-10-23T14:10:{i:02d}Z",
            "submitted_at": f"2026-10-23T14:11:{i*10:02d}Z",
            "client_metadata": {"device_id": f"low_{i}"}
        })

    # 4. Call POST endpoint
    post_res = client.post(f"/api/surveys/{survey_id}/analytics/rasch", json={"scope": "all"})
    assert post_res.status_code == 200
    data = post_res.json()

    assert data["survey_id"] == survey_id
    assert data["sample_size"] == 12
    assert data["item_count"] == 4
    assert data["convergence"]["iterations"] > 0
    assert "reliability" in data
    assert 0.0 <= data["reliability"]["item_reliability"] <= 1.0
    assert "targeting" in data
    assert "item_calibrations" in data
    assert len(data["item_calibrations"]) == 4

    # Verify that easy question has lower difficulty than hard question
    calibs_by_id = {item["question_id"]: item for item in data["item_calibrations"]}
    assert calibs_by_id[qids[0]]["difficulty_logit"] <= calibs_by_id[qids[3]]["difficulty_logit"]

    # Verify Wright Map
    assert "wright_map" in data
    assert len(data["wright_map"]) > 0

    # Verify APA narrative
    assert "apa_narrative" in data
    assert len(data["apa_narrative"]) > 20

    # 5. Call GET endpoint
    get_res = client.get(f"/api/surveys/{survey_id}/analytics/rasch?scope=all")
    assert get_res.status_code == 200
    assert get_res.json()["item_count"] == 4
