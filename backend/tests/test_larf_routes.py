# -*- coding: utf-8 -*-
"""
Route tests for Instrumental Variable Local Average Response Function (LARF) Endpoint.
(POST /api/surveys/{survey_id}/analytics/larf)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_larf_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Health Intervention Compliance & Non-linear Response Study",
        "description": "Instrumental Variable LARF semi-parametric evaluation"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, Instrument Z, Covariate X1
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Health Intervention Compliance & Non-linear Response Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Health Improvement Reported (0/1)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Program Participation (0/1)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Voucher Subsidy Random Assignment (0/1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Baseline Health Risk Index", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    z_qid = questions[2]["id"]
    x_qid = questions[3]["id"]

    # 3. Publish survey to allow response ingestion
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Submit 45 responses
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    for i in range(45):
        x_val = float(np.random.normal(0, 1))
        z_val = float(np.random.choice([0, 1]))
        # Treatment compliance affected by Z
        d_val = float(1 if (0.8 * z_val + 0.3 * x_val + np.random.normal(0, 0.5) > 0.3) else 0)
        # Outcome affected by D
        y_val = float(1 if (0.7 * d_val + 0.4 * x_val + np.random.normal(0, 0.4) > 0.2) else 0)

        started = (now - timedelta(minutes=5)).isoformat()
        submitted = now.isoformat()

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(y_val),
                    d_qid: str(d_val),
                    z_qid: str(z_val),
                    x_qid: str(x_val)
                },
                "started_at": started,
                "submitted_at": submitted
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call LARF endpoint
    larf_res = client.post(
        f"/api/surveys/{survey_id}/analytics/larf",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "instrument_question_id": z_qid,
            "covariate_question_ids": [x_qid],
            "model_type": "logit",
            "alpha_level": 0.05,
            "n_bootstraps": 50,
            "trim_negative": False,
            "scope": "all"
        }
    )
    assert larf_res.status_code == 200
    data = larf_res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 45
    assert data["complier_probability"] > 0
    assert "late" in data["effects"]
    assert "ci_lower" in data["effects"]["late"]
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data

    # 6. Verify audit log entry
    with get_db() as conn:
        audit_row = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'LARF_EVALUATED'",
            (survey_id,)
        ).fetchone()
        assert audit_row is not None
        assert audit_row["action"] == "LARF_EVALUATED"
