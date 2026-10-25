"""
Route tests for Partial Identification & Non-Random Attrition Bounds Endpoint
(POST /api/surveys/{survey_id}/analytics/partial-attrition-bounds)
DataTrust Iteration 192
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_partial_attrition_bounds_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Partial Attrition Evaluation",
        "description": "Bounding causal effects under non-random survey attrition"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Treatment, Outcome, Response Status
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Partial Attrition Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Treatment Arm (D)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Followup Outcome (Y)", "is_required": False},
            {"order_index": 2, "question_type": "number", "title": "Response Status (R)", "is_required": True},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    q_map = {q["title"]: q["id"] for q in detail_res.json()["questions"]}
    q_d = q_map["Treatment Arm (D)"]
    q_y = q_map["Followup Outcome (Y)"]
    q_r = q_map["Response Status (R)"]

    # 4. Generate 50 responses
    np.random.seed(192)
    now = datetime.now(timezone.utc)
    N = 50

    for i in range(N):
        t_val = 1 if i % 2 == 0 else 0
        # Treatment response rate ~ 85%, Control ~ 60%
        p_resp = 0.85 if t_val == 1 else 0.60
        r_val = 1 if np.random.uniform() < p_resp else 0

        # Latent outcome: baseline 10, effect +3 for treated
        if r_val == 1:
            y_val = 13.0 + float(np.random.normal(0, 1.5)) if t_val == 1 else 10.0 + float(np.random.normal(0, 1.5))
        else:
            y_val = None

        answers = {
            q_d: str(t_val),
            q_r: str(r_val),
        }
        if y_val is not None:
            answers[q_y] = str(round(y_val, 2))

        # Distinct timestamp per response to bypass duplicate submission protection
        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers,
            "started_at": (now - timedelta(minutes=10, seconds=i * 5)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 5)).isoformat(),
            "client_metadata": {"device_id": f"device_{i}"}
        })
        assert resp.status_code in (200, 201)

    # 5. Call endpoint
    eval_res = client.post(
        f"/api/surveys/{survey_id}/analytics/partial-attrition-bounds",
        json={
            "treatment_question_id": q_d,
            "outcome_question_id": q_y,
            "response_question_id": q_r,
            "user_ymin": 0.0,
            "user_ymax": 25.0,
            "alpha": 0.05,
            "scope": "all"
        }
    )
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 50
    assert data["response_rate_treatment"] > 0.60
    assert data["response_rate_control"] > 0.40

    # Check bounds
    assert "naive_complete_case" in data
    assert "manski_horowitz_bounds" in data
    assert "lee_trimming_bounds" in data
    assert "mts_bounds" in data

    lee_b = data["lee_trimming_bounds"]
    manski_b = data["manski_horowitz_bounds"]
    assert lee_b["lower_bound"] < lee_b["upper_bound"]
    assert lee_b["interval_width"] <= manski_b["interval_width"]

    assert "svg_visualization" in data
    assert len(data["svg_visualization"]) > 100
    assert len(data["apa_narrative"]) > 50


def test_partial_attrition_bounds_not_found():
    res = client.post("/api/surveys/non-existent-survey/analytics/partial-attrition-bounds", json={
        "treatment_question_id": "q1",
        "outcome_question_id": "q2"
    })
    assert res.status_code == 404
