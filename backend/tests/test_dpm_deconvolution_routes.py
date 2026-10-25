# -*- coding: utf-8 -*-
"""
Route tests for Bayesian Nonparametric Dirichlet Process Mixture Density Deconvolution Endpoint.
(POST /api/surveys/{survey_id}/analytics/dpm-deconvolution)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dpm_deconvolution_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Latent Risk Aversion & Measurement Error Deconvolution Survey",
        "description": "DPM Density Deconvolution (Ferguson 1973; Escobar & West 1995)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Target Y, Replicate Y_rep
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Latent Risk Aversion & Measurement Error Deconvolution Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Risk Aversion Score (Wave 1)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Risk Aversion Score (Wave 2 Replicate)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    yrep_qid = questions[1]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 40 valid responses
    np.random.seed(65)
    now = datetime.now(timezone.utc)
    for i in range(40):
        # Latent true score X* ~ 50 + N(0, 7^2)
        x_true = float(np.random.normal(50.0, 7.0))
        y1_val = round(float(x_true + np.random.normal(0, 2.5)), 2)
        y2_val = round(float(x_true + np.random.normal(0, 2.5)), 2)

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(y1_val),
                    yrep_qid: str(y2_val)
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call DPM Deconvolution endpoint
    analysis_res = client.post(f"/api/surveys/{survey_id}/analytics/dpm-deconvolution", json={
        "target_question_id": y_qid,
        "replicate_question_id": yrep_qid,
        "max_components": 5,
        "dp_alpha": 1.0,
        "scope": "all"
    })

    assert analysis_res.status_code == 200
    res_data = analysis_res.json()
    assert res_data["status"] == "SUCCESS"
    
    summ = res_data["overall_summary"]
    assert summ["sample_size"] == 40
    assert "reliability_ratio" in summ
    assert "latent_true_variance" in summ
    assert "measurement_error_sd" in summ
    assert len(res_data["components"]) == 5
    assert "<svg" in res_data["svg_visualization"]
    assert "Dirichlet Process Mixture" in res_data["apa_narrative"]
