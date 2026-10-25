# -*- coding: utf-8 -*-
"""
Route tests for Non-random Survey Attrition & Selection Bounds (Lee Bounds) Endpoint.
(POST /api/surveys/{survey_id}/analytics/lee-bounds)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_lee_bounds_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Longitudinal Survey Attrition & Bound Analysis",
        "description": "Sharp Lee bounds on longitudinal intervention under selective non-response"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment T, Covariate X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Longitudinal Survey Attrition & Bound Analysis",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Endline Wellbeing Score (1-10)", "is_required": False},
            {"order_index": 1, "question_type": "number", "title": "Cash Incentive Intervention (0/1)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Baseline Education Level (Years)", "is_required": False}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    t_qid = questions[1]["id"]
    x_qid = questions[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 50 respondents with selective attrition
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    for i in range(50):
        t_val = float(np.random.choice([0, 1]))
        x_val = float(np.random.normal(12, 2))
        
        # Treated units have 85% retention, control has 60% retention
        p_resp = 0.85 if t_val == 1.0 else 0.60
        responds = (np.random.uniform(0, 1) <= p_resp)

        started = (now - timedelta(minutes=5)).isoformat()
        submitted = now.isoformat()

        answers_dict = {
            t_qid: str(t_val),
            x_qid: str(round(x_val, 1))
        }
        if responds:
            y_val = 6.0 + 1.5 * t_val + 0.2 * (x_val - 12) + float(np.random.normal(0, 0.4))
            answers_dict[y_qid] = str(round(y_val, 2))

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_dict,
                "started_at": started,
                "submitted_at": submitted
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call Lee Bounds endpoint
    lee_res = client.post(
        f"/api/surveys/{survey_id}/analytics/lee-bounds",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": t_qid,
            "covariate_question_ids": [x_qid],
            "alpha_level": 0.05,
            "n_bootstraps": 40,
            "scope": "all"
        }
    )
    assert lee_res.status_code == 200
    data = lee_res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 50
    assert "response_rates" in data
    assert "bounds" in data
    assert "unconditional" in data["bounds"]
    assert "lower_bound" in data["bounds"]["unconditional"]
    assert "upper_bound" in data["bounds"]["unconditional"]
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data

    # 6. Verify audit log entry
    with get_db() as conn:
        audit_row = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'LEE_BOUNDS_EVALUATED'",
            (survey_id,)
        ).fetchone()
        assert audit_row is not None
        assert audit_row["action"] == "LEE_BOUNDS_EVALUATED"
