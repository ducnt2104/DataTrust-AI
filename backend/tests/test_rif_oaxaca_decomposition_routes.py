"""
Route tests for RIF Oaxaca-Blinder Decomposition Endpoint
(POST /api/surveys/{survey_id}/analytics/rif-oaxaca-decomposition)
DataTrust Iteration 173
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_rif_oaxaca_decomposition_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Workforce Compensation & RIF Oaxaca-Blinder Study",
        "description": "Distributional wage decomposition (Firpo, Fortin, & Lemieux 2009, 2018)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: group, outcome, edu, exp
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Workforce Compensation & RIF Oaxaca-Blinder Study",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Gender Group (1=Male, 0=Female)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Hourly Compensation Rate (Outcome)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Years of Formal Education", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Years of Industry Experience", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    g_qid = questions[0]["id"]
    y_qid = questions[1]["id"]
    edu_qid = questions[2]["id"]
    exp_qid = questions[3]["id"]

    # 4. Submit 60 responses: 30 Group 1 (Male) and 30 Group 0 (Female)
    np.random.seed(42)
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)

    for i in range(30):
        edu = np.random.normal(16, 2)
        exp = np.random.normal(10, 3)
        wage = 30.0 + 3.0 * edu + 1.2 * exp + np.random.normal(0, 1.5)
        sub_time = base_time + timedelta(minutes=i * 2)

        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                g_qid: "1",
                y_qid: str(round(float(wage), 2)),
                edu_qid: str(round(float(edu), 1)),
                exp_qid: str(round(float(exp), 1))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })

    for i in range(30):
        edu = np.random.normal(13, 2)
        exp = np.random.normal(7, 3)
        wage = 22.0 + 2.2 * edu + 0.9 * exp + np.random.normal(0, 1.5)
        sub_time = base_time + timedelta(minutes=(30 + i) * 2)

        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                g_qid: "0",
                y_qid: str(round(float(wage), 2)),
                edu_qid: str(round(float(edu), 1)),
                exp_qid: str(round(float(exp), 1))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })

    # 5. Call RIF Oaxaca analytics endpoint
    payload = {
        "group_question_id": g_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [edu_qid, exp_qid],
        "reference_group_val": "1",
        "num_bootstrap_reps": 30,
        "alpha_level": 0.05,
        "scope": "all"
    }

    response = client.post(f"/api/surveys/{survey_id}/analytics/rif-oaxaca-decomposition", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 60
    assert data["group_a_label"] == "1"
    assert data["group_b_label"] == "0"
    assert "mean_decomposition" in data
    assert "median_rif_estimates" in data
    assert data["median_rif_estimates"]["total_median_gap"] > 5.0
    assert "quantile_decomposition_curve" in data
    assert len(data["quantile_decomposition_curve"]) == 5
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data
