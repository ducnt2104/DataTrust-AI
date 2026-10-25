"""
Integration tests for Statistical Power Analysis & Sample Size Estimator API route
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_survey_power_analysis_route():
    # 1. Create a survey
    res = client.post("/api/surveys", json={
        "title": "Khảo Sát Khảo Sát Lực Thống Kê Thực Nghiệm",
        "description": "Thẩm định độ nhạy cỡ mẫu Power 80%",
        "instructions": "Vui lòng trả lời"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]

    # 2. Add question and publish
    q_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_val",
                "order_index": 0,
                "question_type": "number",
                "title": "Điểm số hài lòng",
                "is_required": True,
                "options": [],
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

    for i in range(12):
        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {qid: 50 + i * 2},
            "started_at": "2026-10-23T12:00:00Z",
            "submitted_at": "2026-10-23T12:01:30Z"
        })
        assert submit_res.status_code == 201

    # 3. Call power-analysis endpoint
    power_res = client.post(f"/api/surveys/{survey_id}/analytics/power-analysis", json={
        "analysis_type": "ttest",
        "confidence_level": 0.95,
        "margin_of_error": 0.05,
        "population_size": 1000,
        "effect_size": 0.50,
        "target_power": 0.80,
        "alpha": 0.05,
        "scope": "all"
    })
    assert power_res.status_code == 200
    data = power_res.json()

    assert data["survey_id"] == survey_id
    assert data["current_sample_size"] == 12
    assert "adequacy" in data
    assert "cochran_estimation" in data
    assert data["cochran_estimation"]["fpc_applied"] is True
    assert data["cochran_estimation"]["required_sample_size"] > 0
    assert len(data["power_curve"]) > 0
    assert "apa_narrative" in data["adequacy"]
