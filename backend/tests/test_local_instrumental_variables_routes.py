# -*- coding: utf-8 -*-
"""
Route tests for Local Instrumental Variables & Marginal Treatment Effects Endpoint.
(POST /api/surveys/{survey_id}/analytics/local-instrumental-variables)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_liv_mte_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Returns to Higher Education & Marginal Returns Survey",
        "description": "LIV and Marginal Treatment Effects (Heckman & Vytlacil 2005 Econometrica)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, Instrument Z, Covariate X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Returns to Higher Education & Marginal Returns Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Log Hourly Wage (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "College Degree (D)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Distance to Nearest College (Z)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "AFQT Cognitive Score (X)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    z_qid = questions[2]["id"]
    x_qid = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 45 valid responses
    np.random.seed(99)
    now = datetime.now(timezone.utc)
    for i in range(45):
        z_val = round(float(np.random.normal(0, 1.2)), 2)
        x_val = round(float(np.random.normal(100.0, 15.0)), 2)
        x_std = (x_val - 100.0) / 15.0

        p_treat = 1.0 / (1.0 + np.exp(-(0.7 * z_val + 0.3 * x_std)))
        u_d = np.random.uniform(0, 1)
        d_val = 1.0 if p_treat >= u_d else 0.0

        # Roy selection MTE = 0.40 - 0.25 * u_d
        mte_i = 0.40 - 0.25 * u_d
        y_val = round(float(2.8 + 0.1 * x_std + d_val * mte_i + np.random.normal(0, 0.08)), 3)

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(y_val),
                    d_qid: str(int(d_val)),
                    z_qid: str(z_val),
                    x_qid: str(x_val)
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call LIV/MTE endpoint
    analysis_res = client.post(f"/api/surveys/{survey_id}/analytics/local-instrumental-variables", json={
        "outcome_question_id": y_qid,
        "treatment_question_id": d_qid,
        "instrument_question_ids": [z_qid],
        "covariate_question_ids": [x_qid],
        "n_grid_points": 30,
        "trim_quantile": 0.05,
        "alpha_level": 0.05
    })

    assert analysis_res.status_code == 200
    res_data = analysis_res.json()
    assert res_data["status"] == "SUCCESS"
    
    summ = res_data["overall_summary"]
    assert summ["sample_size"] == 45
    assert "ate" in summ
    assert "att" in summ
    assert "atu" in summ
    assert "late" in summ
    assert "sorting_on_gains_att_minus_ate" in summ
    assert len(res_data["mte_curve"]) == 30
    assert "<svg" in res_data["svg_visualization"]
    assert "Marginal Treatment Effects" in res_data["apa_narrative"]
