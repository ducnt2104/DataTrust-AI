# -*- coding: utf-8 -*-
"""
Route tests for Surrogate Index & Long-Term Causal Evaluation Endpoint.
(POST /api/surveys/{survey_id}/analytics/surrogate-index)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_surrogate_index_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Educational Intervention Long-Term Earnings Evaluation",
        "description": "Athey et al. (2019) surrogate index evaluation with intermediate survey scores"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Treatment W, Surrogates S1, S2, Long-term outcome Y, Covariate X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Educational Intervention Long-Term Earnings Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Program Participation (0/1)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "1-Month Cognitive Aptitude", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "3-Month Job Placement Score", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "5-Year Cumulative Earnings ($k)", "is_required": False},
            {"order_index": 4, "question_type": "number", "title": "Baseline Education (Years)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    w_qid = questions[0]["id"]
    s1_qid = questions[1]["id"]
    s2_qid = questions[2]["id"]
    y_qid = questions[3]["id"]
    x_qid = questions[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 55 respondents
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    for i in range(55):
        w_val = float(np.random.choice([0, 1]))
        x_val = float(np.random.normal(12, 2))
        s1_val = float(5.0 + 1.2 * w_val + 0.3 * (x_val - 12) + np.random.normal(0, 0.5))
        s2_val = float(3.0 + 0.9 * w_val + 0.2 * (x_val - 12) + np.random.normal(0, 0.5))
        y_val = float(20.0 + 2.5 * s1_val + 3.0 * s2_val + 1.1 * x_val + np.random.normal(0, 1.0))

        started = (now - timedelta(minutes=5)).isoformat()
        submitted = now.isoformat()

        answers_dict = {
            w_qid: str(w_val),
            s1_qid: str(round(s1_val, 2)),
            s2_qid: str(round(s2_val, 2)),
            y_qid: str(round(y_val, 2)),
            x_qid: str(round(x_val, 1))
        }

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_dict,
                "started_at": started,
                "submitted_at": submitted
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call Surrogate Index endpoint
    surr_res = client.post(
        f"/api/surveys/{survey_id}/analytics/surrogate-index",
        json={
            "treatment_question_id": w_qid,
            "surrogate_question_ids": [s1_qid, s2_qid],
            "longterm_outcome_question_id": y_qid,
            "covariate_question_ids": [x_qid],
            "alpha_level": 0.05,
            "n_bootstraps": 40,
            "ridge_lambda": 1.0,
            "scope": "all"
        }
    )
    assert surr_res.status_code == 200
    data = surr_res.json()
    assert data["status"] == "SUCCESS"
    assert "longterm_treatment_effect" in data
    assert "estimate" in data["longterm_treatment_effect"]
    assert len(data["surrogate_decomposition"]) == 2
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data

    # 6. Verify audit log entry
    with get_db() as conn:
        audit_row = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'SURROGATE_INDEX_EVALUATED'",
            (survey_id,)
        ).fetchone()
        assert audit_row is not None
        assert audit_row["action"] == "SURROGATE_INDEX_EVALUATED"
