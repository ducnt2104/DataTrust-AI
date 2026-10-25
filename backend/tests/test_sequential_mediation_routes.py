# -*- coding: utf-8 -*-
"""
Route tests for Sequential Causal Mediation Endpoint.
(POST /api/surveys/{survey_id}/analytics/sequential-mediation)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_sequential_mediation_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Behavioral Intervention & Trust Mediation Study",
        "description": "Multi-stage sequential mediation modeling"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Behavioral Intervention & Trust Mediation Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Experimental Nudge (0=Control, 1=Nudge)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Perceived System Transparency", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Institutional Trust Index", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Data Sharing Consent Likelihood", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Digital Literacy Score", "is_required": True}
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    q_t = questions[0]["id"]
    q_m1 = questions[1]["id"]
    q_m2 = questions[2]["id"]
    q_y = questions[3]["id"]
    q_x = questions[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 45 synthetic respondents
    now_time = datetime.now(timezone.utc)
    rng = np.random.RandomState(789)

    for i in range(45):
        t_val = float(rng.binomial(1, 0.5))
        x_val = float(rng.normal(50.0, 10.0))

        e1 = rng.normal(0, 0.4)
        m1_val = 2.0 + 0.8 * t_val + 0.02 * x_val + e1

        e2 = rng.normal(0, 0.4)
        m2_val = 1.5 + 0.4 * t_val + 0.6 * m1_val + 0.03 * x_val + e2

        ey = rng.normal(0, 0.5)
        y_val = 3.0 + 0.5 * t_val + 0.45 * m1_val + 0.7 * m2_val + 0.01 * x_val + ey

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    q_t: str(t_val),
                    q_m1: str(round(m1_val, 2)),
                    q_m2: str(round(m2_val, 2)),
                    q_y: str(round(y_val, 2)),
                    q_x: str(round(x_val, 2))
                },
                "started_at": (now_time - timedelta(minutes=8)).isoformat(),
                "submitted_at": now_time.isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call Sequential Mediation Endpoint
    payload = {
        "treatment_question_id": q_t,
        "mediator1_question_id": q_m1,
        "mediator2_question_id": q_m2,
        "outcome_question_id": q_y,
        "covariate_question_ids": [q_x],
        "n_bootstraps": 150,
        "alpha_level": 0.05,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/sequential-mediation", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "SEQUENTIAL_CAUSAL_MEDIATION_HAYES_6"
    assert data["sample_size"] == 45
    assert data["bootstrap_replications"] > 0

    effects = data["effects"]
    assert "direct_effect" in effects
    assert "indirect_path1_m1" in effects
    assert "indirect_path2_m2" in effects
    assert "indirect_sequential_m1_m2" in effects
    assert "indirect_total" in effects
    assert "total_effect" in effects

    assert "proportion_mediated_total" in data["proportions"]
    assert "proportion_mediated_sequential" in data["proportions"]
    assert len(data["regression_equations"]) == 3

    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]
    assert "Hayes Model 6" in data["apa_narrative"]

    # 6. Test 404 for nonexistent survey
    err_res = client.post("/api/surveys/nonexistent-survey/analytics/sequential-mediation", json=payload)
    assert err_res.status_code == 404

    # 7. Verify audit log entry
    with get_db() as conn:
        log_entry = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'SEQUENTIAL_MEDIATION_EVALUATED'",
            (survey_id,)
        ).fetchone()
        assert log_entry is not None
