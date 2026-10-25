# -*- coding: utf-8 -*-
"""
Route tests for Factor Instrumental Variables Endpoint.
(POST /api/surveys/{survey_id}/analytics/factor-iv)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_factor_iv_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Education Policy & Earnings Evaluation",
        "description": "Factor IV / PC-2SLS with High-Dimensional Instrument Battery (Bai & Ng 2010)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Wage), Treatment (Years of Higher Ed), 5 Instruments (Proximity, Grants, Tuitions...)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Education Policy & Earnings Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Hourly Earnings (USD)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Years of Higher Education", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Distance to Nearest University (km)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Regional Tuition Voucher Rate", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Local Education Subsidy Index", "is_required": True},
            {"order_index": 5, "question_type": "number", "title": "High School Counseling Capacity", "is_required": True},
            {"order_index": 6, "question_type": "number", "title": "County Grant Per Capita", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    z1_qid = questions[2]["id"]
    z2_qid = questions[3]["id"]
    z3_qid = questions[4]["id"]
    z4_qid = questions[5]["id"]
    z5_qid = questions[6]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 40 responses generated from 2 latent policy factors
    np.random.seed(77)
    now = datetime.now(timezone.utc)
    N = 40

    for i in range(N):
        # Latent policy factors
        f1 = float(np.random.normal(0, 1))
        f2 = float(np.random.normal(0, 1))
        u_confounder = float(np.random.normal(0, 1))

        z1 = float(10.0 - 2.5 * f1 + np.random.normal(0, 0.5))
        z2 = float(50.0 + 5.0 * f1 + np.random.normal(0, 0.5))
        z3 = float(100.0 + 8.0 * f1 + np.random.normal(0, 0.5))
        z4 = float(30.0 + 4.0 * f2 + np.random.normal(0, 0.5))
        z5 = float(20.0 + 3.0 * f2 + np.random.normal(0, 0.5))

        # True causal effect = 2.0
        d_val = float(12.0 + 0.8 * f1 + 0.5 * f2 + 1.2 * u_confounder + np.random.normal(0, 0.3))
        y_val = float(25.0 + 2.0 * d_val + 1.8 * u_confounder + np.random.normal(0, 0.4))

        answers_dict = {
            y_qid: str(round(y_val, 2)),
            d_qid: str(round(d_val, 2)),
            z1_qid: str(round(z1, 2)),
            z2_qid: str(round(z2, 2)),
            z3_qid: str(round(z3, 2)),
            z4_qid: str(round(z4, 2)),
            z5_qid: str(round(z5, 2))
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

    # 5. Call factor-iv endpoint
    fiv_res = client.post(
        f"/api/surveys/{survey_id}/analytics/factor-iv",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "instrument_question_ids": [z1_qid, z2_qid, z3_qid, z4_qid, z5_qid],
            "alpha_level": 0.05,
            "scope": "all"
        }
    )
    assert fiv_res.status_code == 200
    res_data = fiv_res.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["overall_summary"]["sample_size"] == 40
    assert res_data["overall_summary"]["n_candidate_instruments_K"] == 5
    assert res_data["overall_summary"]["n_factors_r"] >= 1
    assert res_data["overall_summary"]["first_stage_f_statistic"] > 5.0
    assert abs(res_data["overall_summary"]["beta_factor_iv"] - 2.0) < 0.8
    assert len(res_data["instrument_loadings"]) == 5
    assert "<svg" in res_data["svg_visualization"]
    assert "Factor Instrumental Variables" in res_data["apa_narrative"]
