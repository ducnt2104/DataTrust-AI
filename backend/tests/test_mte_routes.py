# -*- coding: utf-8 -*-
"""
Route tests for Marginal Treatment Effects (MTE) Endpoint.
(POST /api/surveys/{survey_id}/analytics/mte)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_mte_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Marginal Treatment Effects & Policy Evaluation Study",
        "description": "Semiparametric MTE with instruments for job training returns"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, Instruments Z1, Z2, Covariate X1
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Marginal Treatment Effects & Policy Evaluation Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Log Hourly Earnings", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Completed Skill Training (0/1)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Distance to Training Center (km)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Tuition Voucher Subsidy (0/1)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Baseline Aptitude Score", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    z1_qid = questions[2]["id"]
    z2_qid = questions[3]["id"]
    x_qid = questions[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 55 synthetic respondents
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    for i in range(55):
        z1_val = float(np.random.normal(0, 1))
        z2_val = float(np.random.choice([0, 1]))
        x_val = float(np.random.normal(2, 0.8))
        
        # Propensity to take training
        u_d = float(np.random.uniform(0.01, 0.99))
        eta = 0.7 * z1_val + 0.9 * z2_val + 0.3 * x_val
        p_val = float(1.0 / (1.0 + np.exp(-eta)))
        d_val = float(1 if p_val >= u_d else 0)
        
        # Outcome
        effect = 3.5 - 2.5 * u_d
        y_val = float(8.0 + 1.2 * x_val + d_val * effect + np.random.normal(0, 0.4))

        started = (now - timedelta(minutes=5)).isoformat()
        submitted = now.isoformat()

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(round(y_val, 3)),
                    d_qid: str(d_val),
                    z1_qid: str(round(z1_val, 3)),
                    z2_qid: str(z2_val),
                    x_qid: str(round(x_val, 3))
                },
                "started_at": started,
                "submitted_at": submitted
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call MTE endpoint
    mte_res = client.post(
        f"/api/surveys/{survey_id}/analytics/mte",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "instrument_question_ids": [z1_qid, z2_qid],
            "covariate_question_ids": [x_qid],
            "poly_degree": 3,
            "alpha_level": 0.05,
            "n_bootstraps": 40,
            "policy_shift_pct": 0.15,
            "scope": "all"
        }
    )
    assert mte_res.status_code == 200
    data = mte_res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 55
    assert "parameters" in data
    assert "ate" in data["parameters"]
    assert "att" in data["parameters"]
    assert "atu" in data["parameters"]
    assert "prte" in data["parameters"]
    assert len(data["mte_curve"]) == 50
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data

    # 6. Verify audit log entry
    with get_db() as conn:
        audit_row = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'MTE_EVALUATED'",
            (survey_id,)
        ).fetchone()
        assert audit_row is not None
        assert audit_row["action"] == "MTE_EVALUATED"
