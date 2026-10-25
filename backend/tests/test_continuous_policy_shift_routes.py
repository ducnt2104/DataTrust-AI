# -*- coding: utf-8 -*-
"""
Route tests for Continuous Policy Shift & Doubly Robust Dosage Response Endpoint.
(POST /api/surveys/{survey_id}/analytics/continuous-policy-shift)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_continuous_policy_shift_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Corporate Wellness Subsidy & Productivity DRC Survey",
        "description": "Continuous Policy Shift (Kennedy 2017; Chernozhukov 2022)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Continuous Treatment A, Confounder X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Corporate Wellness Subsidy & Productivity DRC Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Employee Productivity Index (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Monthly Wellness Subsidy (A)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Baseline Work Stress (X)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    a_qid = questions[1]["id"]
    x_qid = questions[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 40 responses with continuous treatment variation
    np.random.seed(52)
    now = datetime.now(timezone.utc)
    for i in range(40):
        x_val = round(float(np.random.normal(5.0, 1.2)), 1)
        a_val = round(float(12.0 + 1.5 * x_val + np.random.normal(0, 2.0)), 1)
        # Nonlinear response
        y_val = round(float(45.0 + 2.5 * a_val - 0.06 * (a_val ** 2) - 0.8 * x_val + np.random.normal(0, 0.5)), 2)

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(y_val),
                    a_qid: str(a_val),
                    x_qid: str(x_val)
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in (200, 201)

    # 5. Execute Continuous Policy Shift endpoint
    payload = {
        "outcome_question_id": y_qid,
        "treatment_question_id": a_qid,
        "covariate_question_ids": [x_qid],
        "grid_points": 20,
        "shift_delta": 2.5,
        "alpha_level": 0.05,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/continuous-policy-shift", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 40
    assert "treatment_support" in data
    assert "policy_shift" in data
    assert data["policy_shift"]["delta_shift"] == 2.5
    assert "dose_response_curve" in data
    assert len(data["dose_response_curve"]) == 20
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
