# -*- coding: utf-8 -*-
"""
Route tests for Automatic Debiased Machine Learning via Riesz Representer Learning Endpoint.
(POST /api/surveys/{survey_id}/analytics/auto-dml-riesz)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auto_dml_riesz_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Continuous Policy & Riesz Debiased Evaluation Survey",
        "description": "Auto-DML via Riesz Learning (Chernozhukov, Newey, & Singh 2022 Econometrica)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, Covariates X1, X2
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Continuous Policy & Riesz Debiased Evaluation Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Customer Lifetime Value (USD)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Loyalty Program Tier (D)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Monthly Spend (X1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Tenure Months (X2)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 40 valid survey responses
    np.random.seed(88)
    now = datetime.now(timezone.utc)
    for i in range(40):
        x1_val = round(float(np.random.normal(50.0, 10.0)), 2)
        x2_val = round(float(np.random.normal(12.0, 3.0)), 2)
        
        # Confounded binary treatment
        p_treat = 1.0 / (1.0 + np.exp(-((x1_val - 50.0) / 10.0)))
        d_val = 1.0 if np.random.uniform(0, 1) < p_treat else 0.0
        
        # True ATE = 15.0
        y_val = round(float(100.0 + 15.0 * d_val + 0.8 * x1_val + 1.2 * x2_val + np.random.normal(0, 2.0)), 2)

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(y_val),
                    d_qid: str(int(d_val)),
                    x1_qid: str(x1_val),
                    x2_qid: str(x2_val)
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Execute Auto-DML Riesz analysis
    analysis_res = client.post(f"/api/surveys/{survey_id}/analytics/auto-dml-riesz", json={
        "outcome_question_id": y_qid,
        "treatment_question_id": d_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "functional_type": "ate",
        "n_splits": 4,
        "ridge_lambda": 0.01,
        "alpha_level": 0.05
    })

    assert analysis_res.status_code == 200
    res_data = analysis_res.json()
    assert res_data["status"] == "SUCCESS"
    
    summ = res_data["overall_summary"]
    assert summ["sample_size"] == 40
    assert summ["functional_type"] == "ate"
    assert "theta_autodml" in summ
    assert "theta_naive_plugin" in summ
    assert "se_autodml" in summ
    assert "ci_95" in summ
    assert "<svg" in res_data["svg_visualization"]
    assert "Automatic Debiased Machine Learning" in res_data["apa_narrative"]
