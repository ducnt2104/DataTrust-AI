"""
Integration tests for Generalized Estimating Equations (GEE) API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_gee_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Hospital Patient Satisfaction Panel Study",
        "description": "Population-averaged GEE evaluation of hospital care ratings"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT: Cluster ID, Wave, Predictor X, Outcome Y
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Hospital Patient Satisfaction Panel Study",
        "questions": [
            {
                "order_index": 0,
                "question_type": "text",
                "title": "Mã bệnh nhân (Patient ID)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Lần tái khám (Visit Wave)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Thời gian tư vấn của bác sĩ (Phút)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Điểm hài lòng người bệnh (Likert 1-10)",
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
    q_cluster = questions[0]["id"]
    q_time = questions[1]["id"]
    q_x = questions[2]["id"]
    q_y = questions[3]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/gee", json={
        "cluster_question_id": q_cluster,
        "time_question_id": q_time,
        "outcome_question_id": q_y,
        "predictor_question_ids": [q_x],
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Submit 30 responses (15 patients x 2 visits)
    now = datetime.now(timezone.utc)
    resp_idx = 0
    for p_id in range(15):
        pat_code = f"PAT_{100 + p_id}"
        for visit in [1, 2]:
            consult_mins = 10.0 + (p_id % 4) * 5.0 + visit * 2.0
            satisfaction = 5.0 + 0.2 * consult_mins + 0.5 * visit

            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "started_at": (now - timedelta(seconds=2000 + resp_idx * 20)).isoformat(),
                "submitted_at": (now - timedelta(seconds=resp_idx * 20)).isoformat(),
                "answers": {
                    q_cluster: pat_code,
                    q_time: str(visit),
                    q_x: str(round(consult_mins, 1)),
                    q_y: str(round(satisfaction, 1))
                }
            })
            assert sub_res.status_code in [200, 201]
            resp_idx += 1

    # 5. Evaluate GEE Model
    gee_res = client.post(f"/api/surveys/{survey_id}/analytics/gee", json={
        "cluster_question_id": q_cluster,
        "time_question_id": q_time,
        "outcome_question_id": q_y,
        "predictor_question_ids": [q_x],
        "family": "gaussian",
        "corstr": "exchangeable",
        "scope": "all"
    })
    assert gee_res.status_code == 200
    data = gee_res.json()
    assert data["status"] == "success"
    assert data["clusters_count"] == 15
    assert data["observations_count"] == 30
    assert len(data["coefficients"]) >= 2
    assert "<svg" in data["svg_chart"]
    assert "Mô hình Phương trình Ước lượng Tổng quát" in data["apa_narrative"]

    # 6. Verify audit logs
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-logs")
    if audit_res.status_code == 200:
        logs = audit_res.json()
        actions = [log["action"] for log in logs]
        assert "GEE_MODEL_EVALUATED" in actions
