# -*- coding: utf-8 -*-
"""
Route tests for Causal Survival Analysis & RMST Endpoint.
(POST /api/surveys/{survey_id}/analytics/causal-survival-rmst)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_causal_survival_rmst_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Customer Subscription Churn & Retention Causal RMST Study",
        "description": "Counterfactual restricted mean survival time analysis (Royston & Parmar 2013)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Tenure months (Time), Churned (Event), Loyalty Program (Treatment), Usage Frequency (Covariate)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Customer Subscription Churn & Retention Causal RMST Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Tenure Duration in Months (T)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Canceled Subscription Indicator (Event: 1=Yes, 0=Censored)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Loyalty Program Enrolled (Treatment: 1=Enrolled, 0=Standard)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Baseline Weekly Logins (Covariate)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    t_qid = questions[0]["id"]
    e_qid = questions[1]["id"]
    a_qid = questions[2]["id"]
    z_qid = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate 40 survival observations
    rng = np.random.default_rng(888)
    n = 40
    z_vals = rng.normal(5.0, 2.0, size=n)
    # Treatment assignment
    a_vals = (rng.uniform(0, 1, size=n) < 0.5).astype(int)
    # Survival times: treated survives longer
    scale = np.where(a_vals == 1, 28.0, 10.0)
    true_times = rng.exponential(scale=scale)
    cens_times = rng.uniform(6.0, 30.0, size=n)
    obs_times = np.minimum(true_times, cens_times)
    events = (true_times <= cens_times).astype(int)

    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    for i in range(n):
        sub_time = base_time + timedelta(minutes=i * 2)
        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                t_qid: str(round(obs_times[i], 2)),
                e_qid: str(events[i]),
                a_qid: str(a_vals[i]),
                z_qid: str(round(z_vals[i], 2))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })
        assert resp.status_code in (200, 201)

    # 5. Call POST /api/surveys/{survey_id}/analytics/causal-survival-rmst
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-survival-rmst", json={
        "time_question_id": t_qid,
        "event_question_id": e_qid,
        "treatment_question_id": a_qid,
        "covariate_question_ids": [z_qid],
        "tau_horizon": 14.0,
        "alpha_level": 0.05,
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] == "success"
    assert res_data["sample_size"] >= 25
    assert res_data["tau_horizon"] == 14.0
    assert "causal_rmst_difference" in res_data
    assert "rmtl_metrics" in res_data
    assert "milestone_survival_tau" in res_data
    assert "curve_points" in res_data
    assert len(res_data["curve_points"]) > 5
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
    assert "Restricted Mean Survival Time" in res_data["apa_narrative"]
