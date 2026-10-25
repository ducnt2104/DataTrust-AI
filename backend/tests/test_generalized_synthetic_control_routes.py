# -*- coding: utf-8 -*-
"""
Route tests for Generalized Synthetic Control Endpoint.
(POST /api/surveys/{survey_id}/analytics/generalized-synthetic-control)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_generalized_synthetic_control_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Organizational Policy Adoption & Performance Panel Survey",
        "description": "Generalized Synthetic Control (Xu 2017; Bai 2009; Gobillon & Magnac 2016)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Y), Unit, Time, Treatment (D), Covariate (X)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Organizational Policy Adoption & Performance Panel Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Performance Index (Y)", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Business Unit ID", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Quarterly Period (Time)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Policy Intervention (D)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Baseline Budget (X)", "is_required": False}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    u_qid = questions[1]["id"]
    t_qid = questions[2]["id"]
    d_qid = questions[3]["id"]
    x_qid = questions[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate panel observations
    # 4 Control units: C1, C2, C3, C4
    # 2 Treated units: T1 (treated at t=4), T2 (treated at t=5)
    # 6 periods: t = 1..6
    times = [1, 2, 3, 4, 5, 6]
    ctrl_units = ["C1", "C2", "C3", "C4"]
    tr_units = ["T1", "T2"]
    factor_t = [1.0, 1.4, 1.8, 2.2, 2.6, 3.0]

    np.random.seed(42)
    now = datetime.now(timezone.utc)

    # Submit control observations
    for u_idx, u in enumerate(ctrl_units):
        lambda_u = 0.5 + 0.25 * u_idx
        for t_idx, t in enumerate(times):
            y_val = 15.0 + lambda_u * factor_t[t_idx] + np.random.normal(0, 0.1)
            resp = client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": {
                    y_qid: str(round(float(y_val), 2)),
                    u_qid: u,
                    t_qid: str(t),
                    d_qid: "0",
                    x_qid: str(round(float(5.0 + 0.2 * t), 2))
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            })
            assert resp.status_code in (200, 201)

    # Submit treated observations
    for u in tr_units:
        t_adopt = 4 if u == "T1" else 5
        lambda_u = 1.1
        for t_idx, t in enumerate(times):
            treat = 1 if t >= t_adopt else 0
            treatment_effect = 3.8 if treat == 1 else 0.0
            y_val = 15.0 + lambda_u * factor_t[t_idx] + treatment_effect + np.random.normal(0, 0.1)
            resp = client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": {
                    y_qid: str(round(float(y_val), 2)),
                    u_qid: u,
                    t_qid: str(t),
                    d_qid: str(treat),
                    x_qid: str(round(float(5.0 + 0.2 * t), 2))
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            })
            assert resp.status_code in (200, 201)

    # 5. Call POST /api/surveys/{survey_id}/analytics/generalized-synthetic-control
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/generalized-synthetic-control", json={
        "outcome_question_id": y_qid,
        "unit_question_id": u_qid,
        "time_question_id": t_qid,
        "treatment_question_id": d_qid,
        "covariate_question_ids": [x_qid],
        "n_factors": 1,
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] == "success"
    assert res_data["n_treated_units"] == 2
    assert res_data["n_control_units"] == 4
    assert res_data["n_time_periods"] == 6
    assert res_data["overall_att"]["estimate"] > 2.0
    assert len(res_data["event_study_trajectory"]) > 0
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
