# -*- coding: utf-8 -*-
"""
Route tests for Bayesian Causal Forest (BCF) Endpoint.
(POST /api/surveys/{survey_id}/analytics/bcf)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_bcf_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Digital Upskilling Program & Career Growth",
        "description": "Bayesian Causal Forest estimation of heterogeneous treatment returns"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment W, Covariates X1, X2
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Digital Upskilling Program & Career Growth",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Salary Increase (%)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "AI Course Completion (0/1)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Baseline Technical Literacy (1-10)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Years in Industry", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    w_qid = questions[1]["id"]
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 55 responses
    np.random.seed(77)
    now = datetime.now(timezone.utc)
    for i in range(55):
        x1_val = float(np.random.uniform(2, 9))
        x2_val = float(np.random.normal(6, 2))
        
        # Confounding: higher literacy enrolls more
        prob = 1.0 / (1.0 + np.exp(-(0.4 * (x1_val - 5) + 0.1 * (x2_val - 6))))
        w_val = 1.0 if np.random.uniform(0, 1) < prob else 0.0
        
        # Heterogeneous effect: tau(X) = 5.0 + 1.5 * (x1 - 5)
        tau_i = 5.0 + 1.5 * (x1_val - 5.0)
        y_val = float(10.0 + 2.0 * x1_val + 0.8 * x2_val + w_val * tau_i + np.random.normal(0, 1.0))

        answers_dict = {
            y_qid: str(round(y_val, 2)),
            w_qid: str(w_val),
            x1_qid: str(round(x1_val, 2)),
            x2_qid: str(round(x2_val, 2))
        }

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_dict,
                "started_at": (now - timedelta(minutes=4)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call BCF endpoint
    bcf_res = client.post(
        f"/api/surveys/{survey_id}/analytics/bcf",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": w_qid,
            "covariate_question_ids": [x1_qid, x2_qid],
            "n_posterior_draws": 250,
            "alpha_ridge": 1.0,
            "scope": "all"
        }
    )
    assert bcf_res.status_code == 200
    res_data = bcf_res.json()
    assert res_data["status"] == "SUCCESS"
    assert "overall_summary" in res_data
    assert res_data["overall_summary"]["sample_size"] == 55
    assert res_data["overall_summary"]["posterior_ate_mean"] > 0
    assert "subgroups" in res_data
    assert "individual_sample" in res_data
    assert len(res_data["individual_sample"]) > 0
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data

    # 6. Verify audit log entry
    with get_db() as conn:
        log = conn.execute("""
            SELECT * FROM audit_logs 
            WHERE entity_id = ? AND action = 'BCF_EVALUATED'
        """, (survey_id,)).fetchone()
        assert log is not None
