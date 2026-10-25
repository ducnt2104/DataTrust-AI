"""
Integration tests for Latent Growth Curve Modeling (LGCM) API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_latent_growth_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Longitudinal Digital Skill Acquisition Study",
        "description": "Multi-wave panel tracking participant capability development"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 4 wave questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Longitudinal Digital Skill Acquisition Study",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Điểm kỹ năng số - Tháng 1 (Baseline)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Điểm kỹ năng số - Tháng 3 (Wave 2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Điểm kỹ năng số - Tháng 6 (Wave 3)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Điểm kỹ năng số - Tháng 12 (Wave 4)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 4
    w_qids = [q["id"] for q in questions]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/latent-growth", json={
        "wave_question_ids": w_qids,
        "time_scores": [0.0, 1.0, 2.0, 3.0],
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Submit 20 responses simulating growth
    now = datetime.now(timezone.utc)
    for i in range(20):
        # Base capability + linear growth over 4 waves
        base = 50.0 + (i % 7) * 2.5
        slope = 3.0 + (i % 3) * 1.2
        w1 = base + 1.0
        w2 = base + slope * 1.0 + 0.5
        w3 = base + slope * 2.0 - 0.2
        w4 = base + slope * 3.0 + 0.8

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=2000 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                w_qids[0]: str(round(w1, 1)),
                w_qids[1]: str(round(w2, 1)),
                w_qids[2]: str(round(w3, 1)),
                w_qids[3]: str(round(w4, 1))
            }
        })
        assert sub_res.status_code in [200, 201]

    # 5. Evaluate Latent Growth Curve Model
    lgcm_res = client.post(f"/api/surveys/{survey_id}/analytics/latent-growth", json={
        "wave_question_ids": w_qids,
        "time_scores": [0.0, 1.0, 2.0, 3.0],
        "wave_labels": ["T1", "T2", "T3", "T4"],
        "scope": "all"
    })
    assert lgcm_res.status_code == 200
    data = lgcm_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 20
    assert data["waves_count"] == 4
    assert data["latent_means"]["intercept_mean"] > 40.0
    assert data["latent_means"]["slope_mean"] > 2.0
    assert data["growth_dynamics"]["has_significant_trajectory"] is True
    assert "<svg" in data["svg_chart"]
    assert "Mô hình Quỹ đạo Tăng trưởng Tiềm ẩn" in data["apa_narrative"]

    # 6. Verify audit logs
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-logs")
    if audit_res.status_code == 200:
        logs = audit_res.json()
        actions = [log["action"] for log in logs]
        assert "LATENT_GROWTH_MODEL_EVALUATED" in actions
