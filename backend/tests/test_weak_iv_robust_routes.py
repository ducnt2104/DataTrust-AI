# -*- coding: utf-8 -*-
"""
Route tests for Weak-Instrument Robust Inference Endpoint.
(POST /api/surveys/{survey_id}/analytics/weak-iv-robust)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_weak_iv_robust_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Returns to Education IV Study",
        "description": "Evaluation of causal educational returns with weak instruments"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Returns to Education IV Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Annual Income ($k)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Years of Education", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Distance to College (Miles)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Tuition Subsidy Eligibility", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Parental Socioeconomic Index", "is_required": True}
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    q_y = questions[0]["id"]
    q_endog = questions[1]["id"]
    q_z1 = questions[2]["id"]
    q_z2 = questions[3]["id"]
    q_x = questions[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 40 synthetic respondents
    now_time = datetime.now(timezone.utc)
    rng = np.random.RandomState(456)
    cov_errors = np.array([[1.0, 0.6], [0.6, 1.0]])
    errors = rng.multivariate_normal(mean=[0, 0], cov=cov_errors, size=40)

    for i in range(40):
        z1 = float(rng.normal(5.0, 2.0))
        z2 = float(rng.binomial(1, 0.4))
        x_val = float(rng.normal(50.0, 10.0))
        u = errors[i, 0]
        v = errors[i, 1]

        # First stage
        ed_years = 12.0 + 0.6 * z1 + 1.2 * z2 + 0.05 * x_val + v
        # Second stage
        income = 20.0 + 3.5 * ed_years + 0.3 * x_val + u

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    q_y: str(round(income, 2)),
                    q_endog: str(round(ed_years, 2)),
                    q_z1: str(round(z1, 2)),
                    q_z2: str(round(z2, 2)),
                    q_x: str(round(x_val, 2))
                },
                "started_at": (now_time - timedelta(minutes=10)).isoformat(),
                "submitted_at": now_time.isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call Weak-IV Robust Analysis Endpoint
    payload = {
        "outcome_question_id": q_y,
        "endogenous_question_id": q_endog,
        "instrument_question_ids": [q_z1, q_z2],
        "covariate_question_ids": [q_x],
        "alpha_level": 0.05,
        "grid_points": 100,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/weak-iv-robust", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "WEAK_IV_ROBUST_MOREIRA_CLR_AR"
    diag = data["diagnostics"]
    assert diag["sample_size"] == 40
    assert diag["num_instruments"] == 2
    assert "first_stage_f" in diag
    assert "effective_f" in diag
    assert "identification_status" in diag

    est = data["estimates"]
    assert "beta_2sls" in est
    assert "wald_ci_95" in est
    assert "ar_ci_95" in est
    assert "clr_ci_95" in est

    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]
    assert "Moreira" in data["apa_narrative"]

    # 6. Test 404 for nonexistent survey
    err_res = client.post("/api/surveys/nonexistent-survey/analytics/weak-iv-robust", json=payload)
    assert err_res.status_code == 404

    # 7. Verify audit log entry
    with get_db() as conn:
        log_entry = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'WEAK_IV_ROBUST_EVALUATED'",
            (survey_id,)
        ).fetchone()
        assert log_entry is not None
