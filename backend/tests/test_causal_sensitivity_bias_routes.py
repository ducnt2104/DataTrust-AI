# -*- coding: utf-8 -*-
"""
Route tests for Causal Sensitivity Analysis & Omitted Variable Bias Endpoint.
(POST /api/surveys/{survey_id}/analytics/causal-sensitivity-bias)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_causal_sensitivity_bias_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Organizational Well-being & Remote Work Policy",
        "description": "Causal sensitivity assessment against unobserved workplace confounding"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, Covariates X1, X2
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Organizational Well-being & Remote Work Policy",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Job Satisfaction Score (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Remote Days Per Week (D)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Tenure in Years (X1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Weekly Overtime Hours (X2)", "is_required": True}
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

    # 4. Ingest 50 responses
    np.random.seed(123)
    now = datetime.now(timezone.utc)
    for i in range(50):
        x1_val = float(np.random.normal(4, 1.2))
        x2_val = float(np.random.uniform(0, 15))
        d_val = float(max(0, min(5, 1.5 + 0.3 * x1_val - 0.1 * x2_val + np.random.normal(0, 0.8))))
        y_val = float(40.0 + 3.2 * d_val + 1.1 * x1_val - 0.7 * x2_val + np.random.normal(0, 1.0))

        answers_dict = {
            y_qid: str(round(y_val, 2)),
            d_qid: str(round(d_val, 1)),
            x1_qid: str(round(x1_val, 2)),
            x2_qid: str(round(x2_val, 2))
        }

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_dict,
                "started_at": (now - timedelta(minutes=3)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call causal-sensitivity-bias endpoint
    sens_res = client.post(
        f"/api/surveys/{survey_id}/analytics/causal-sensitivity-bias",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "covariate_question_ids": [x1_qid, x2_qid],
            "q_reduction": 1.0,
            "alpha_level": 0.05,
            "benchmark_multipliers": [1.0, 2.0, 3.0],
            "scope": "all"
        }
    )
    assert sens_res.status_code == 200
    res_data = sens_res.json()
    assert res_data["status"] == "SUCCESS"
    assert "overall_summary" in res_data
    assert res_data["overall_summary"]["sample_size"] == 50
    assert res_data["overall_summary"]["robustness_value_q"] > 0
    assert "covariate_benchmarks" in res_data
    assert len(res_data["covariate_benchmarks"]) == 2
    assert "benchmark_scenarios" in res_data
    assert len(res_data["benchmark_scenarios"]) > 0
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data

    # 6. Verify audit log entry
    with get_db() as conn:
        log = conn.execute("""
            SELECT * FROM audit_logs 
            WHERE entity_id = ? AND action = 'CAUSAL_SENSITIVITY_BIAS_EVALUATED'
        """, (survey_id,)).fetchone()
        assert log is not None
