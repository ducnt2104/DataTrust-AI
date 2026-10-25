# -*- coding: utf-8 -*-
"""
Route tests for Causal Mediation Sensitivity Endpoint.
(POST /api/surveys/{survey_id}/analytics/causal-mediation-sensitivity)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_causal_mediation_sensitivity_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Leadership Style, Job Satisfaction & Retention Causal Mediation Study",
        "description": "Causal mediation with sensitivity bounds for unobserved confounding (Imai et al. 2010)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Leadership Mentoring (T), Job Satisfaction (M), Turnover Intention (Y), Tenure (Z)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Leadership Style, Job Satisfaction & Retention Causal Mediation Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Leadership Mentoring Program (T)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Job Satisfaction Score (M - Mediator)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Performance Rating (Y - Outcome)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Tenure Years (Z - Covariate)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    t_qid = questions[0]["id"]
    m_qid = questions[1]["id"]
    y_qid = questions[2]["id"]
    z_qid = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate 35 responses
    rng = np.random.default_rng(555)
    n = 35
    t_vals = (rng.uniform(0, 1, size=n) < 0.5).astype(int)
    z_vals = rng.normal(3.0, 1.0, size=n)
    m_vals = 3.0 + 1.6 * t_vals + 0.4 * z_vals + rng.normal(0, 0.5, size=n)
    y_vals = 10.0 + 1.1 * t_vals + 1.8 * m_vals + 0.5 * z_vals + rng.normal(0, 0.7, size=n)

    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    for i in range(n):
        sub_time = base_time + timedelta(minutes=i * 2)
        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                t_qid: str(t_vals[i]),
                m_qid: str(round(m_vals[i], 2)),
                y_qid: str(round(y_vals[i], 2)),
                z_qid: str(round(z_vals[i], 2))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })
        assert resp.status_code in (200, 201)

    # 5. Call POST /api/surveys/{survey_id}/analytics/causal-mediation-sensitivity
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-mediation-sensitivity", json={
        "treatment_question_id": t_qid,
        "mediator_question_id": m_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [z_qid],
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] in ("SUCCESS", "success")
    assert "baseline_effects" in res_data
    assert "acme" in res_data["baseline_effects"]
    assert res_data["baseline_effects"]["acme"] > 1.0
    assert "path_estimates" in res_data
    assert "sensitivity_analysis" in res_data
    assert "critical_rho_threshold" in res_data["sensitivity_analysis"]
    assert "svg_chart" in res_data
    assert "<svg" in res_data["svg_chart"]
    assert "apa_narrative" in res_data
    assert "Imai" in res_data["apa_narrative"]
