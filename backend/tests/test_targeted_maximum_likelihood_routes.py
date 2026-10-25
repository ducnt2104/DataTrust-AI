# -*- coding: utf-8 -*-
"""
Route tests for Targeted Maximum Likelihood Estimation Endpoint.
(POST /api/surveys/{survey_id}/analytics/targeted-maximum-likelihood)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_targeted_maximum_likelihood_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Employee Training Intervention & Productivity TMLE Study",
        "description": "Targeted Maximum Likelihood Estimation (van der Laan & Rose 2011; Schuler & Rose 2017)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Productivity (Y), Training Program (A), Prior Experience (W)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Employee Training Intervention & Productivity TMLE Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Monthly Output Productivity (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Completed Training Program (A)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Years Prior Experience (W)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    a_qid = questions[1]["id"]
    w_qid = questions[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate 35 confounded observational responses
    np.random.seed(42)
    base_time = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(35):
        w_val = float(np.random.normal(5.0, 2.0))
        # Treatment assignment correlated with experience
        prob_a = 1.0 / (1.0 + np.exp(-(w_val - 5.0)))
        a_val = 1 if np.random.uniform(0, 1) < prob_a else 0
        # True effect +6.0
        y_val = 50.0 + 6.0 * a_val + 2.5 * w_val + np.random.normal(0, 1.0)

        sub_time = base_time + timedelta(minutes=i * 2)
        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y_val, 2)),
                a_qid: str(a_val),
                w_qid: str(round(w_val, 2))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })
        assert resp.status_code in (200, 201)

    # 5. Call POST /api/surveys/{survey_id}/analytics/targeted-maximum-likelihood
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/targeted-maximum-likelihood", json={
        "outcome_question_id": y_qid,
        "treatment_question_id": a_qid,
        "covariate_question_ids": [w_qid],
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] == "success"
    assert res_data["sample_size"] >= 25
    assert "ate_tmle" in res_data
    assert res_data["ate_tmle"]["estimate"] > 3.0
    assert "targeted_fluctuation" in res_data
    assert "estimators_comparison" in res_data
    assert len(res_data["estimators_comparison"]) == 4
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
