# -*- coding: utf-8 -*-
"""
Route tests for Conformal Optimal Transport Counterfactual Distributional Alignment Endpoint.
(POST /api/surveys/{survey_id}/analytics/conformal-optimal-transport)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_conformal_optimal_transport_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Optimal Transport Policy Evaluation Survey",
        "description": "COT Counterfactual Distribution Alignment (Cuturi 2013; Courty 2017)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, Covariate X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Optimal Transport Policy Evaluation Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Quarterly Revenue Gain (kUSD)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Subsidized Consulting Program (D)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Baseline Enterprise Size (Employees)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    x_qid = questions[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 40 valid responses (20 treated, 20 control)
    np.random.seed(77)
    now = datetime.now(timezone.utc)
    for i in range(40):
        d_val = 1.0 if i < 20 else 0.0
        x_val = round(float(np.random.normal(50.0 + 5.0 * d_val, 10.0)), 1)
        
        # True treatment effect +8.0
        y_val = round(float(40.0 + 8.0 * d_val + 0.5 * (x_val - 50.0) + np.random.normal(0, 2.0)), 2)

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(y_val),
                    d_qid: str(int(d_val)),
                    x_qid: str(x_val)
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call Conformal Optimal Transport endpoint
    analysis_res = client.post(f"/api/surveys/{survey_id}/analytics/conformal-optimal-transport", json={
        "outcome_question_id": y_qid,
        "treatment_question_id": d_qid,
        "covariate_question_ids": [x_qid],
        "reg_eps": 0.05,
        "covariate_weight_kappa": 0.5,
        "conformal_alpha": 0.10,
        "scope": "all"
    })

    assert analysis_res.status_code == 200
    res_data = analysis_res.json()
    assert res_data["status"] == "SUCCESS"
    
    summ = res_data["overall_summary"]
    assert summ["n_treated"] == 20
    assert summ["n_control"] == 20
    assert "wasserstein_2_distance" in summ
    assert "optimal_transport_ate" in summ
    assert "optimal_transport_att" in summ
    assert "conformal_half_width_delta" in summ
    assert len(summ["quantiles"]) == 5
    assert "<svg" in res_data["svg_visualization"]
    assert "Conformal Optimal Transport" in res_data["apa_narrative"]
