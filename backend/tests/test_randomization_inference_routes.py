"""
Integration tests for Exact Permutation & Randomization Inference API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_randomization_inference_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Community Micro-Grant Randomization Trial",
        "description": "Sharp null testing of community development grant impacts"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT: Outcome Y and Treatment D
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Community Micro-Grant Randomization Trial",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Doanh thu hộ kinh doanh (Triệu VNĐ/tháng)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Nhận gói tài trợ vi mô (Micro-Grant)",
                "is_required": True,
                "options": [{"label": "Được tài trợ", "value": "1"}, {"label": "Nhóm đối chứng", "value": "0"}],
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
    assert len(questions) == 2
    q_outcome = questions[0]["id"]
    q_treatment = questions[1]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/randomization-inference", json={
        "outcome_question_id": q_outcome,
        "treatment_question_id": q_treatment,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Submit 24 responses (12 treated, 12 control)
    now = datetime.now(timezone.utc)
    for i in range(24):
        is_treated = 1 if i % 2 == 0 else 0
        revenue = 25.0 + (6.0 if is_treated else 0.0) + (i % 4) * 1.5

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=2000 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_outcome: str(round(revenue, 1)),
                q_treatment: str(is_treated)
            }
        })
        assert sub_res.status_code in [200, 201]

    # 5. Evaluate Randomization Inference
    ri_res = client.post(f"/api/surveys/{survey_id}/analytics/randomization-inference", json={
        "outcome_question_id": q_outcome,
        "treatment_question_id": q_treatment,
        "num_permutations": 1000,
        "scope": "all"
    })
    assert ri_res.status_code == 200
    data = ri_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 24
    assert data["treated_count"] == 12
    assert data["control_count"] == 12
    assert "difference_in_means" in data
    assert "hodges_lehmann_shift" in data
    assert "<svg" in data["svg_chart"]
    assert "Fisher's Exact Randomization Inference" in data["apa_narrative"]

    # 6. Verify audit logs
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-logs")
    if audit_res.status_code == 200:
        logs = audit_res.json()
        actions = [log["action"] for log in logs]
        assert "RANDOMIZATION_INFERENCE_EVALUATED" in actions
