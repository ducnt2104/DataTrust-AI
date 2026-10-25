# -*- coding: utf-8 -*-
"""
Route integration tests for Latent Profile Analysis (LPA) & Gaussian Mixture Modeling
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_latent_profile_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Customer Experience & Trust Latent Profile Survey",
        "description": "LPA segmentation across multiple Likert dimensions"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add indicator questions: Trust, Usability, Value
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Customer Experience & Trust Latent Profile Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Platform Trust Score", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "System Usability Score", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Perceived Value Score", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    q1_id = q_objs[0]["id"]
    q2_id = q_objs[1]["id"]
    q3_id = q_objs[2]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses with 2 latent profiles
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        if i % 2 == 0:
            # Profile 1: High Advocates
            trust = 4.5 + (i % 3) * 0.2
            usability = 4.6 + (i % 3) * 0.15
            value = 4.7 + (i % 3) * 0.1
        else:
            # Profile 2: Disengaged Detractors
            trust = 1.8 + (i % 3) * 0.2
            usability = 2.0 + (i % 3) * 0.2
            value = 1.9 + (i % 3) * 0.25

        started = now_time - timedelta(seconds=120 + i)
        submitted = now_time - timedelta(seconds=i)

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                q1_id: trust,
                q2_id: usability,
                q3_id: value
            },
            "started_at": started.isoformat(),
            "submitted_at": submitted.isoformat(),
            "session_metadata": {"duration_seconds": 120}
        })
        assert submit_res.status_code == 201

    # 5. Call Latent Profile Analysis endpoint
    lpa_res = client.post(f"/api/surveys/{survey_id}/analytics/latent-profile", json={
        "indicator_question_ids": [q1_id, q2_id, q3_id],
        "n_profiles": 2,
        "max_profiles": 3,
        "scope": "all"
    })

    assert lpa_res.status_code == 200
    data = lpa_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "LATENT_PROFILE_ANALYSIS_GMM"
    assert data["diagnostics"]["sample_size"] == 30
    assert data["diagnostics"]["n_indicators"] == 3
    assert len(data["profiles"]) == 2
    assert "<svg" in data["svg_visualization"]
    assert "APA 7th Edition" in data["apa_narrative"]
