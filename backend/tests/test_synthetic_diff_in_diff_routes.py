"""
Route tests for Synthetic Difference-in-Differences endpoint
DataTrust Iteration 172
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_synthetic_diff_in_diff_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Regional Market Staggered Policy & SDID Study",
        "description": "Synthetic Difference-in-Differences (Arkhangelsky et al. 2021 AER)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: unit, time, treatment, outcome
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Regional Market Staggered Policy & SDID Study",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Store Cluster Unit ID", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Quarter Wave Time Period", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Policy Intervention (1=Treated, 0=Control)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Quarterly Sales Outcome Index", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    unit_qid = questions[0]["id"]
    time_qid = questions[1]["id"]
    treat_qid = questions[2]["id"]
    outcome_qid = questions[3]["id"]

    # 4. Submit responses: 5 units (Store_0 treated in period >= 3, Store_1..4 controls) across 4 periods (1, 2, 3, 4)
    np.random.seed(123)
    units = [f"Store_{i}" for i in range(5)]
    periods = [1, 2, 3, 4]
    base_time = datetime.now(timezone.utc) - timedelta(hours=2)
    obs_idx = 0

    for u_idx, u in enumerate(units):
        is_treated = (u_idx == 0)
        base_u = 20.0 + u_idx * 2.0
        for t in periods:
            for rep in range(2):
                obs_idx += 1
                w = 1 if (is_treated and t >= 3) else 0
                y = base_u + 1.5 * t + (5.0 if w == 1 else 0.0) + np.random.normal(0, 0.2)
                sub_time = base_time + timedelta(minutes=obs_idx * 2)

                submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                    "answers": {
                        unit_qid: u,
                        time_qid: str(t),
                        treat_qid: str(w),
                        outcome_qid: str(round(float(y), 2))
                    },
                    "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
                    "submitted_at": sub_time.isoformat()
                })
                assert submit_res.status_code in (200, 201)

    # 5. Call the SDID analytics endpoint
    payload = {
        "unit_question_id": unit_qid,
        "time_question_id": time_qid,
        "treatment_question_id": treat_qid,
        "outcome_question_id": outcome_qid,
        "num_bootstrap_reps": 30,
        "alpha_level": 0.05,
        "scope": "all"
    }

    response = client.post(f"/api/surveys/{survey_id}/analytics/synthetic-diff-in-diff", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["num_units_total"] == 5
    assert data["num_treated_units"] == 1
    assert data["num_control_units"] == 4
    assert data["num_periods_total"] == 4
    assert "estimates" in data
    assert data["estimates"]["sdid_tau"] > 2.0
    assert "apa_narrative" in data
    assert "<svg" in data["svg_visualization"]
