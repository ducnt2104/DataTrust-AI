# -*- coding: utf-8 -*-
"""
Route tests for Dynamic Spatial Panel Econometrics Endpoint.
(POST /api/surveys/{survey_id}/analytics/dynamic-spatial-panel)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dynamic_spatial_panel_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Regional Consumer Sentiment & Spatio-Temporal Diffusion Survey",
        "description": "Dynamic Spatial Panel (Elhorst 2014; Lee & Yu 2010; LeSage & Pace 2009)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Region, Wave, Covariate X, Lat, Lon
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Regional Consumer Sentiment & Spatio-Temporal Diffusion Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Regional Consumer Confidence Index (Y)", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Economic Region Identifier", "is_required": True},
            {"order_index": 2, "question_type": "text", "title": "Quarterly Survey Wave", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Regional Retail Sales Growth (X)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Latitude", "is_required": False},
            {"order_index": 5, "question_type": "number", "title": "Longitude", "is_required": False}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    r_qid = questions[1]["id"]
    t_qid = questions[2]["id"]
    x_qid = questions[3]["id"]
    lat_qid = questions[4]["id"]
    lon_qid = questions[5]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest panel responses: 4 regions across 5 quarterly waves (20 responses)
    regions = ["North_Metropolitan", "Central_Highlands", "South_Delta", "Coast_Maritime"]
    waves = ["2025_Q1", "2025_Q2", "2025_Q3", "2025_Q4", "2026_Q1"]
    coords = {
        "North_Metropolitan": (21.0, 105.8),
        "Central_Highlands": (14.0, 108.0),
        "South_Delta": (10.7, 106.6),
        "Coast_Maritime": (16.0, 108.2)
    }

    np.random.seed(64)
    now = datetime.now(timezone.utc)
    for w_idx, wave in enumerate(waves):
        for r_name in regions:
            lat, lon = coords[r_name]
            x_val = round(float(np.random.normal(4.5 + 0.2 * w_idx, 1.0)), 2)
            y_val = round(float(65.0 + 1.2 * w_idx + 0.7 * x_val + np.random.normal(0, 0.8)), 2)

            resp = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": {
                        y_qid: str(y_val),
                        r_qid: r_name,
                        t_qid: wave,
                        x_qid: str(x_val),
                        lat_qid: str(lat),
                        lon_qid: str(lon)
                    },
                    "started_at": (now - timedelta(minutes=2)).isoformat(),
                    "submitted_at": now.isoformat()
                }
            )
            assert resp.status_code in (200, 201)

    # 5. Execute Dynamic Spatial Panel endpoint
    payload = {
        "outcome_question_id": y_qid,
        "region_question_id": r_qid,
        "time_question_id": t_qid,
        "covariate_question_ids": [x_qid],
        "lat_question_id": lat_qid,
        "lon_question_id": lon_qid,
        "alpha_level": 0.05,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/dynamic-spatial-panel", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["n_regions"] == 4
    assert data["n_time_periods"] == 5
    assert "spatio_temporal_parameters" in data
    assert "system_stability" in data
    assert "short_run_impacts" in data
    assert "long_run_impacts" in data
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
