# -*- coding: utf-8 -*-
"""
Route tests for High-Dimensional Causal Mediation Endpoint.
(POST /api/surveys/{survey_id}/analytics/high-dimensional-mediation)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_high_dimensional_mediation_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Employee Training & Organizational Trust Mediation Survey",
        "description": "High-Dimensional Causal Mediation (Imai 2010; VanderWeele 2015; Zhao & Luo 2022)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Treatment T, Outcome Y, Mediator M1, Mediator M2, Confounder X, Subgroup
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Employee Training & Organizational Trust Mediation Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Leadership Training Attendance (T)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Employee Retention / Loyalty Score (Y)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Organizational Trust (M1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Role Clarity Index (M2)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Baseline Job Tenure Years (X)", "is_required": True},
            {"order_index": 5, "question_type": "text", "title": "Department Subgroup", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    t_qid = questions[0]["id"]
    y_qid = questions[1]["id"]
    m1_qid = questions[2]["id"]
    m2_qid = questions[3]["id"]
    x_qid = questions[4]["id"]
    sub_qid = questions[5]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 45 responses
    np.random.seed(55)
    now = datetime.now(timezone.utc)
    for i in range(45):
        t_val = 1.0 if (i % 2 == 0) else 0.0
        x_val = round(float(np.random.normal(3.5, 1.2)), 2)
        dept = "Engineering" if i < 23 else "Operations"

        m1_val = round(float(2.0 + 1.2 * t_val + 0.3 * x_val + np.random.normal(0, 0.4)), 2)
        m2_val = round(float(1.5 + 0.7 * t_val + 0.2 * x_val + np.random.normal(0, 0.5)), 2)
        y_val = round(float(10.0 + 0.5 * t_val + 1.5 * m1_val + 0.8 * m2_val + 0.4 * x_val + np.random.normal(0, 0.6)), 2)

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    t_qid: str(t_val),
                    y_qid: str(y_val),
                    m1_qid: str(m1_val),
                    m2_qid: str(m2_val),
                    x_qid: str(x_val),
                    sub_qid: dept
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in (200, 201)

    # 5. Execute High-Dimensional Mediation route
    payload = {
        "treatment_question_id": t_qid,
        "outcome_question_id": y_qid,
        "mediator_question_ids": [m1_qid, m2_qid],
        "confounder_question_ids": [x_qid],
        "subgroup_question_id": sub_qid,
        "n_boot": 40,
        "alpha_level": 0.05,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/high-dimensional-mediation", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 45
    assert data["n_mediators"] == 2
    assert "total_effect" in data
    assert "natural_direct_effect" in data
    assert "natural_indirect_effect" in data
    assert "proportion_mediated" in data
    assert "mediator_pathways" in data
    assert len(data["mediator_pathways"]) == 2
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
    assert "latent_path_invariance" in data
