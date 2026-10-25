# -*- coding: utf-8 -*-
"""
Route tests for Quantile Synthetic Control Endpoint.
(POST /api/surveys/{survey_id}/analytics/quantile-synthetic-control)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_quantile_synthetic_control_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Hospital Policy Intervention Panel Survey",
        "description": "Quantile Synthetic Control Evaluation (Gunsilius 2023)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Wait Time), Unit (Hospital ID), Time (Quarter Wave)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Hospital Policy Intervention Panel Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Patient Wait Time (minutes)", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Hospital Code", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Quarter Wave", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    u_qid = questions[1]["id"]
    t_qid = questions[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest responses across 3 hospitals and 4 waves (waves 1-2 pre, waves 3-4 post)
    np.random.seed(99)
    now = datetime.now(timezone.utc)
    units = ["HOSP_TREATED", "DONOR_A", "DONOR_B"]
    waves = [1, 2, 3, 4]

    for u in units:
        base = 45.0 if u == "DONOR_A" else (55.0 if u == "DONOR_B" else 50.0)
        for w in waves:
            # Treatment reduces wait time for HOSP_TREATED at wave >= 3
            tau = -12.0 if (u == "HOSP_TREATED" and w >= 3) else 0.0
            for i in range(5):  # 5 obs per cell = 3 * 4 * 5 = 60 responses
                wait_time = float(np.random.normal(base + 0.2 * w + tau, 3.0))
                answers_dict = {
                    y_qid: str(round(wait_time, 2)),
                    u_qid: u,
                    t_qid: str(w)
                }
                resp = client.post(
                    f"/api/public/surveys/{slug}/submit",
                    json={
                        "answers": answers_dict,
                        "started_at": (now - timedelta(minutes=2)).isoformat(),
                        "submitted_at": now.isoformat()
                    }
                )
                assert resp.status_code in [200, 201]

    # 5. Call quantile-synthetic-control endpoint
    qsc_res = client.post(
        f"/api/surveys/{survey_id}/analytics/quantile-synthetic-control",
        json={
            "outcome_question_id": y_qid,
            "unit_question_id": u_qid,
            "time_question_id": t_qid,
            "treated_unit_id": "HOSP_TREATED",
            "treatment_time": 3,
            "quantiles": [0.10, 0.25, 0.50, 0.75, 0.90],
            "regularization_lambda": 0.001,
            "scope": "all"
        }
    )
    assert qsc_res.status_code == 200
    res_data = qsc_res.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["overall_summary"]["treated_unit"] == "HOSP_TREATED"
    assert res_data["overall_summary"]["median_qte_effect"] < -5.0  # Significant wait time reduction
    assert len(res_data["donor_weights"]) == 2
    assert len(res_data["quantile_treatment_effects"]) == 5
    assert "<svg" in res_data["svg_visualization"]
    assert "Quantile Synthetic Control" in res_data["apa_narrative"]
