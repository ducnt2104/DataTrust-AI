"""
Integration tests for Split-Ballot & Question Wording Experiment API routes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_survey_split_ballot_route():
    # 1. Create a survey
    res = client.post("/api/surveys", json={
        "title": "Khảo Sát Thử Nghiệm Tách Phiếu A/B Wording Effect",
        "description": "Nghiên cứu độ nhạy cảm của người trả lời trước cách hành văn",
        "instructions": "Vui lòng trả lời"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]

    # 2. Add a target question (e.g. Likert scale or rating)
    q_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_exp_target",
                "order_index": 0,
                "question_type": "rating",
                "title": "Đánh giá mức độ đồng thuận chính sách",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })
    assert q_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    slug = res.json()["public_slug"]
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    qid = public_q[0]["id"]

    # Submit 8 responses in arm_a (values 1-3) with distinct timestamps & device metadata
    for i in range(8):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {qid: 2 + (i % 2)},
            "started_at": f"2026-10-23T12:00:{i:02d}Z",
            "submitted_at": f"2026-10-23T12:01:{i*10:02d}Z",
            "experimental_arm": "arm_a",
            "client_metadata": {"device_id": f"dev_a_{i}"}
        })

    # Submit 8 responses in arm_b (values 4-5) with distinct timestamps & device metadata
    for i in range(8):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {qid: 4 + (i % 2)},
            "started_at": f"2026-10-23T12:02:{i:02d}Z",
            "submitted_at": f"2026-10-23T12:03:{i*10:02d}Z",
            "experimental_arm": "arm_b",
            "client_metadata": {"device_id": f"dev_b_{i}"}
        })

    # 3. Call split-ballot analysis endpoint
    post_res = client.post(f"/api/surveys/{survey_id}/analytics/split-ballot", json={
        "question_id": qid,
        "scope": "all"
    })
    assert post_res.status_code == 200
    data = post_res.json()

    assert data["survey_id"] == survey_id
    assert data["question_id"] == qid
    assert data["total_responses"] == 16
    assert data["arms_count"] == 2
    assert "comparison" in data
    assert data["comparison"]["comparison_type"] == "numeric"
    assert data["comparison"]["details"]["is_significant"] is True
    assert "distortion_index" in data
    assert data["distortion_index"]["level"] == "HIGHLY_PLASTIC"
    assert "apa_narrative" in data

    # 4. Also test GET endpoint
    get_res = client.get(f"/api/surveys/{survey_id}/analytics/split-ballot?question_id={qid}&scope=all")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["question_id"] == qid
