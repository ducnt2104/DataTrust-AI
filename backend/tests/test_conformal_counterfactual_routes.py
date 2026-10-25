# -*- coding: utf-8 -*-
"""
Route tests for Conformal Counterfactual Risk Inference Endpoint.
(POST /api/surveys/{survey_id}/analytics/conformal-counterfactual)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_conformal_counterfactual_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Treatment Effect Risk & Conformal Counterfactual Study",
        "description": "Finite-sample valid distribution-free counterfactual prediction intervals"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment W, Covariates X1, X2, Subgroup
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Treatment Effect Risk & Conformal Counterfactual Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Productivity Metric (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Algorithm Assistance Treatment (W)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Experience Level (X1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Task Complexity (X2)", "is_required": True},
            {"order_index": 4, "question_type": "text", "title": "Cohort Division", "is_required": False}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    w_qid = questions[1]["id"]
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]
    sub_qid = questions[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 60 responses
    np.random.seed(99)
    now = datetime.now(timezone.utc)
    for i in range(60):
        x1_val = float(np.random.normal(5, 1.5))
        x2_val = float(np.random.uniform(1, 10))
        # Treatment assignment
        p = 1.0 / (1.0 + np.exp(-(0.3 * (x1_val - 5) - 0.2 * (x2_val - 5))))
        w_val = 1.0 if np.random.uniform(0, 1) < p else 0.0
        
        # Heterogeneous effect: some gain, some have downside harm
        tau_i = 3.0 + 1.2 * (x1_val - 5) - 0.8 * (x2_val - 5)
        y_val = float(50.0 + 2.0 * x1_val + 1.5 * x2_val + w_val * tau_i + np.random.normal(0, 1.2))
        cohort = "Senior" if x1_val > 5.0 else "Junior"

        answers_dict = {
            y_qid: str(round(y_val, 2)),
            w_qid: str(w_val),
            x1_qid: str(round(x1_val, 2)),
            x2_qid: str(round(x2_val, 2)),
            sub_qid: cohort
        }

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers_dict,
            "started_at": (now - timedelta(minutes=4)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code in [200, 201]

    # 5. Call conformal-counterfactual analytics endpoint
    eval_res = client.post(f"/api/surveys/{survey_id}/analytics/conformal-counterfactual", json={
        "outcome_question_id": y_qid,
        "treatment_question_id": w_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "miscoverage_alpha": 0.10,
        "calibration_ratio": 0.50,
        "use_propensity_weighting": True,
        "subgroup_question_id": sub_qid,
        "scope": "all"
    })
    assert eval_res.status_code == 200
    res_data = eval_res.json()
    assert res_data["status"] == "SUCCESS"
    assert "overall_summary" in res_data
    assert res_data["overall_summary"]["sample_size"] == 60
    assert res_data["overall_summary"]["target_coverage_pct"] == 90.0
    assert "calibration_diagnostics" in res_data
    assert "subgroup_risk_profiles" in res_data
    assert len(res_data["subgroup_risk_profiles"]) == 2  # Junior and Senior
    assert "individual_predictions_sample" in res_data
    assert len(res_data["individual_predictions_sample"]) > 0
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data

    # 6. Verify audit log entry
    with get_db() as conn:
        log = conn.execute("""
            SELECT * FROM audit_logs 
            WHERE entity_id = ? AND action = 'CONFORMAL_COUNTERFACTUAL_EVALUATED'
        """, (survey_id,)).fetchone()
        assert log is not None
