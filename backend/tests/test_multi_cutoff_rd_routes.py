# -*- coding: utf-8 -*-
"""
Route tests for Multi-Cutoff Regression Discontinuity Endpoint.
(POST /api/surveys/{survey_id}/analytics/multi-cutoff-rd)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_multi_cutoff_rd_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Regional Targeted Subsidy & Multi-Cutoff RD Survey",
        "description": "Multi-Cutoff Regression Discontinuity (Cattaneo 2015; Bertanha 2020)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Running X, Region Group
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Regional Targeted Subsidy & Multi-Cutoff RD Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Household Welfare Index (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Poverty Assessment Score (X)", "is_required": True},
            {"order_index": 2, "question_type": "text", "title": "Administrative Region", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    x_qid = questions[1]["id"]
    g_qid = questions[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 60 responses (30 in Region A with threshold 40, 30 in Region B with threshold 60)
    np.random.seed(81)
    now = datetime.now(timezone.utc)
    for i in range(60):
        region = "Region_A" if i < 30 else "Region_B"
        cutoff = 40.0 if region == "Region_A" else 60.0
        
        running_val = round(float(np.random.normal(cutoff, 6.0)), 2)
        is_treated = 1.0 if running_val >= cutoff else 0.0
        # Treatment effect +7.5
        outcome_val = round(float(50.0 + 0.8 * (running_val - cutoff) + 7.5 * is_treated + np.random.normal(0, 1.2)), 2)

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(outcome_val),
                    x_qid: str(running_val),
                    g_qid: region
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call Multi-Cutoff RD endpoint
    analysis_res = client.post(f"/api/surveys/{survey_id}/analytics/multi-cutoff-rd", json={
        "outcome_question_id": y_qid,
        "running_question_id": x_qid,
        "group_question_id": g_qid,
        "fixed_cutoffs": {"Region_A": 40.0, "Region_B": 60.0},
        "bandwidth": 5.0,
        "alpha_level": 0.05,
        "scope": "all"
    })

    assert analysis_res.status_code == 200
    res_data = analysis_res.json()
    assert res_data["status"] == "SUCCESS"
    
    summ = res_data["overall_summary"]
    assert summ["sample_size"] == 60
    assert summ["n_distinct_cutoffs"] == 2
    assert "tau_pooled" in summ
    assert "se_pooled" in summ
    assert len(res_data["cutoff_summaries"]) == 2
    assert "<svg" in res_data["svg_visualization"]
    assert "Multi-Cutoff Regression Discontinuity" in res_data["apa_narrative"]
