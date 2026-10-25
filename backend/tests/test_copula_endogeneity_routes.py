# -*- coding: utf-8 -*-
"""
Route tests for Copula-Based Endogeneity Correction Endpoint.
(POST /api/surveys/{survey_id}/analytics/copula-endogeneity)
"""

import pytest
import numpy as np
from scipy import stats
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_copula_endogeneity_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Consumer Price Sensitivity & Willingness to Pay Copula Study",
        "description": "Copula-based endogeneity correction without external instruments (Park & Gupta 2012)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Purchase Intention (Y), Self-Selected Price (P), Household Income (Z)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Consumer Price Sensitivity & Willingness to Pay Copula Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Purchase Intention (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Observed Price (P - Endogenous)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Household Income (Z - Exogenous)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    p_qid = questions[1]["id"]
    z_qid = questions[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate 40 endogenous responses following Park & Gupta (2012) DGP
    rng = np.random.default_rng(777)
    n = 40
    true_rho = 0.65
    mean = [0.0, 0.0]
    cov = [[1.0, true_rho], [true_rho, 1.0]]
    v1, v2 = rng.multivariate_normal(mean, cov, size=n).T

    # Non-normal marginal (Exponential)
    u1 = stats.norm.cdf(v1)
    p_vals = stats.expon.ppf(u1, scale=4.0)
    z_vals = rng.normal(10.0, 2.0, size=n)
    eps_vals = 1.0 * v2
    y_vals = 15.0 + 2.5 * p_vals + 1.2 * z_vals + eps_vals

    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    for i in range(n):
        sub_time = base_time + timedelta(minutes=i * 2)
        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y_vals[i], 2)),
                p_qid: str(round(p_vals[i], 2)),
                z_qid: str(round(z_vals[i], 2))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })
        assert resp.status_code in (200, 201)

    # 5. Call POST /api/surveys/{survey_id}/analytics/copula-endogeneity
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/copula-endogeneity", json={
        "outcome_question_id": y_qid,
        "endogenous_question_id": p_qid,
        "covariate_question_ids": [z_qid],
        "copula_family": "gaussian",
        "bootstrap_replications": 30,
        "alpha_level": 0.05,
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] == "success"
    assert res_data["sample_size"] >= 25
    assert "non_normality_diagnostics" in res_data
    assert "naive_ols" in res_data
    assert "copula_augmented" in res_data
    assert "endogeneity_test" in res_data
    assert "bias_correction" in res_data
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
    assert "Park and Gupta (2012)" in res_data["apa_narrative"]
