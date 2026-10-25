# -*- coding: utf-8 -*-
"""
Route integration tests for Shapley Value Regression & Key Driver Analysis
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_shapley_driver_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Software Platform Experience & Key Driver Survey",
        "description": "Shapley regression relative importance driver evaluation"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: 3 drivers + 1 outcome
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Software Platform Experience & Key Driver Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Platform Speed & Latency", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Customer Support Response", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Feature Completeness", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Overall Net Promoter Score (NPS)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    d1_id = q_objs[0]["id"]
    d2_id = q_objs[1]["id"]
    d3_id = q_objs[2]["id"]
    out_id = q_objs[3]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        speed = 2.0 + (i % 8) * 0.4
        support = 1.5 + (i % 5) * 0.6
        features = 3.0 + (i % 6) * 0.3
        nps = 0.6 * speed + 0.3 * support + 0.1 * features + 1.0

        started = now_time - timedelta(seconds=120 + i)
        submitted = now_time - timedelta(seconds=i)

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                d1_id: speed,
                d2_id: support,
                d3_id: features,
                out_id: nps
            },
            "started_at": started.isoformat(),
            "submitted_at": submitted.isoformat(),
            "session_metadata": {"duration_seconds": 120}
        })
        assert submit_res.status_code == 201

    # 5. Call Shapley Drivers Analysis endpoint
    kda_res = client.post(f"/api/surveys/{survey_id}/analytics/shapley-drivers", json={
        "driver_question_ids": [d1_id, d2_id, d3_id],
        "outcome_question_id": out_id,
        "scope": "all"
    })

    assert kda_res.status_code == 200
    data = kda_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "SHAPLEY_VALUE_KEY_DRIVER_ANALYSIS"
    assert data["diagnostics"]["sample_size"] == 30
    assert data["diagnostics"]["n_drivers"] == 3
    assert data["diagnostics"]["full_model_r2"] > 0.70
    assert len(data["drivers"]) == 3
    assert "<svg" in data["svg_visualization"]
    assert "APA 7th Edition" in data["apa_narrative"]
