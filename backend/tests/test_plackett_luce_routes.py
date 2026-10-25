# -*- coding: utf-8 -*-
"""
Route integration tests for Plackett-Luce Choice Model & Rank-Ordered Logit
"""
import pytest
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_plackett_luce_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Product Feature Preference & Ranking Survey",
        "description": "Plackett-Luce choice modeling for ranked feature priorities"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add ranking question with 4 options
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Product Feature Preference & Ranking Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "ranking",
                "title": "Rank your most desired platform capabilities (1st to 4th)",
                "is_required": True,
                "options": [
                    {"id": "opt_fast", "label": "Fast Real-Time Search"},
                    {"id": "opt_sec", "label": "Zero-Knowledge Encryption"},
                    {"id": "opt_export", "label": "Multi-Format Report Export"},
                    {"id": "opt_theme", "label": "Custom Dashboard Themes"}
                ],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    rank_qid = q_objs[0]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses with consistent preference for Search > Security > Export > Themes
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        if i % 3 == 0:
            ranking_ans = ["opt_fast", "opt_sec", "opt_export", "opt_theme"]
        elif i % 3 == 1:
            ranking_ans = ["opt_sec", "opt_fast", "opt_export", "opt_theme"]
        else:
            ranking_ans = ["opt_fast", "opt_export", "opt_sec", "opt_theme"]

        started = now_time - timedelta(seconds=120 + i)
        submitted = now_time - timedelta(seconds=i)

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                rank_qid: ranking_ans
            },
            "started_at": started.isoformat(),
            "submitted_at": submitted.isoformat(),
            "client_metadata": {"browser": "Chrome"}
        })
        assert submit_res.status_code == 201

    # 5. Call Plackett-Luce Choice endpoint
    pl_res = client.post(f"/api/surveys/{survey_id}/analytics/plackett-luce", json={
        "ranking_question_id": rank_qid,
        "scope": "all"
    })

    assert pl_res.status_code == 200
    data = pl_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "PLACKETT_LUCE_RANK_ORDERED_LOGIT"
    assert data["diagnostics"]["sample_size"] >= 20
    assert data["diagnostics"]["n_items"] == 4
    assert len(data["items"]) == 4
    assert data["items"][0]["item_name"] == "Fast Real-Time Search"
    assert len(data["pairwise_win_matrix"]) == 4
    assert "<svg" in data["svg_visualization"]
    assert "APA 7th Edition" in data["apa_narrative"]
