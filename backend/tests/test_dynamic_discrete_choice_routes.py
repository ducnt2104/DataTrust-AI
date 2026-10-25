# -*- coding: utf-8 -*-
"""
Route tests for Dynamic Discrete Choice Structural Dynamic Programming Endpoint.
(POST /api/surveys/{survey_id}/analytics/dynamic-discrete-choice)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dynamic_discrete_choice_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Capital Equipment Upgrade & Dynamic Discrete Choice Study",
        "description": "Rust (1987) NFXP structural dynamic programming model"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: State variable (Usage / Mileage index) and Decision (1 = Replace, 0 = Keep)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Capital Equipment Upgrade & Dynamic Discrete Choice Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Cumulative Usage Mileage State (s)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Equipment Upgrade Decision (1=Replace, 0=Maintain)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    s_qid = questions[0]["id"]
    d_qid = questions[1]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate 40 transition observations
    rng = np.random.default_rng(717)
    n = 40
    s_curr = 0.0
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)

    for i in range(n):
        prob_rep = 1.0 / (1.0 + np.exp(-(0.12 * s_curr - 2.5)))
        d_val = 1 if rng.uniform(0, 1) < prob_rep else 0

        sub_time = base_time + timedelta(minutes=i * 2)
        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                s_qid: str(round(s_curr, 2)),
                d_qid: str(d_val)
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })
        assert resp.status_code in (200, 201)

        if d_val == 1:
            s_curr = float(rng.uniform(0.0, 2.0))
        else:
            s_curr = float(s_curr + rng.uniform(1.0, 3.5))

    # 5. Call POST /api/surveys/{survey_id}/analytics/dynamic-discrete-choice
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/dynamic-discrete-choice", json={
        "state_question_id": s_qid,
        "decision_question_id": d_qid,
        "discount_factor": 0.95,
        "num_discretized_states": 10,
        "counterfactual_subsidy_pct": 20.0,
        "alpha_level": 0.05,
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] == "success"
    assert res_data["sample_size"] >= 25
    assert "structural_parameters" in res_data
    assert "replacement_cost_rc" in res_data["structural_parameters"]
    assert "equilibrium_thresholds" in res_data
    assert "state_profiles" in res_data
    assert len(res_data["state_profiles"]) == 10
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
    assert "Rust" in res_data["apa_narrative"]
