# -*- coding: utf-8 -*-
"""
Route tests for Two-Way Fixed Effects (TWFE) Decomposition Endpoint.
(POST /api/surveys/{survey_id}/analytics/twfe-decomposition)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_twfe_decomposition_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Corporate Wellness Policy Panel Evaluation",
        "description": "Two-Way Fixed Effects Decomposition & Negative Weights Diagnostics (de Chaisemartin 2020)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Productivity Score), Treatment (Wellness App Active), Unit (Branch), Time (Month Wave)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Corporate Wellness Policy Panel Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Employee Productivity Score", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Wellness App Active (0/1)", "is_required": True},
            {"order_index": 2, "question_type": "text", "title": "Branch Code", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Month Wave", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    u_qid = questions[2]["id"]
    t_qid = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest longitudinal panel data: 6 branches across 3 months
    # Branch 1-2: Already treated at month 1
    # Branch 3-4: Switchers at month 2
    # Branch 5-6: Never treated
    np.random.seed(88)
    now = datetime.now(timezone.utc)
    branches = [f"Branch_{i}" for i in range(1, 7)]
    months = [1, 2, 3]

    for b_idx, b in enumerate(branches):
        b_fe = float(b_idx * 3)
        for m in months:
            t_fe = 1.5 * m
            if b_idx < 2:  # Already treated
                d = 1.0
                tau = 8.0 + 2.0 * m
            elif b_idx < 4:  # Switchers at m >= 2
                d = 1.0 if m >= 2 else 0.0
                tau = 4.0 if m >= 2 else 0.0
            else:  # Controls
                d = 0.0
                tau = 0.0

            for rep in range(3):  # 3 obs per cell = 6 * 3 * 3 = 54 responses
                y_val = float(b_fe + t_fe + tau + np.random.normal(0, 0.2))
                answers_dict = {
                    y_qid: str(round(y_val, 2)),
                    d_qid: str(int(d)),
                    u_qid: b,
                    t_qid: str(m)
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

    # 5. Call twfe-decomposition endpoint
    twfe_res = client.post(
        f"/api/surveys/{survey_id}/analytics/twfe-decomposition",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "unit_question_id": u_qid,
            "time_question_id": t_qid,
            "alpha_level": 0.05,
            "scope": "all"
        }
    )
    assert twfe_res.status_code == 200
    res_data = twfe_res.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["overall_summary"]["n_units"] == 6
    assert res_data["overall_summary"]["n_time_periods"] == 3
    assert res_data["overall_summary"]["n_negative_cells"] > 0
    assert res_data["overall_summary"]["sum_negative_weights"] < 0.0
    assert abs(res_data["overall_summary"]["did_m_estimate"] - 4.0) < 1.0
    assert "<svg" in res_data["svg_visualization"]
    assert "Two-Way Fixed Effects" in res_data["apa_narrative"]
