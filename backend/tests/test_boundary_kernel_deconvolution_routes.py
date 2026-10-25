# -*- coding: utf-8 -*-
"""
Route tests for Nonparametric Boundary Kernel Deconvolution Endpoint.
(POST /api/surveys/{survey_id}/analytics/boundary-kernel-deconvolution)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_boundary_kernel_deconvolution_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Household Economic Well-Being & Income Measurement Error Survey",
        "description": "Boundary Kernel Deconvolution (Delaigle & Meister 2008; Fan 1991)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add question: Self-Reported Income
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Household Economic Well-Being & Income Measurement Error Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Self-Reported Annual Income ($k)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    inc_qid = questions[0]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate 35 noise-contaminated survey responses with staggered timestamps
    # X ~ N(60, 12^2), U ~ N(0, 6^2), W = X + U
    np.random.seed(42)
    base_time = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(35):
        w_val = float(np.random.normal(60.0, 13.4))
        sub_time = base_time + timedelta(minutes=i * 3)
        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                inc_qid: str(round(max(5.0, w_val), 2))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })
        assert resp.status_code in (200, 201)

    # 5. Call POST /api/surveys/{survey_id}/analytics/boundary-kernel-deconvolution
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/boundary-kernel-deconvolution", json={
        "variable_question_id": inc_qid,
        "reliability_ratio": 0.80,
        "error_type": "gaussian",
        "lower_bound": 0.0,
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] == "success"
    assert res_data["sample_size"] >= 25
    assert res_data["reliability_ratio"] == 0.80
    assert res_data["attenuation_correction_factor"] > 1.10
    assert "dispersion_metrics" in res_data
    assert "moments_comparison" in res_data
    assert "density_profile" in res_data
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
