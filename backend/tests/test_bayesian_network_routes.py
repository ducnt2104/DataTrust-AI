# -*- coding: utf-8 -*-
"""
Route integration tests for Bayesian Network DAG Structure Learning
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_bayesian_network_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Digital Platform Trust & Adoption Bayesian Network Survey",
        "description": "Learning causal DAG structure and Markov Blanket across adoption constructs"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 4 numeric questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Digital Platform Trust & Adoption Bayesian Network Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Data Privacy Concern", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Platform Security Trust", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Interface Usability", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Customer Brand Loyalty", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    q1_id = q_objs[0]["id"]
    q2_id = q_objs[1]["id"]
    q3_id = q_objs[2]["id"]
    q4_id = q_objs[3]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses with causal dependency chain
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        priv = 2.0 + (i % 6) * 0.5
        trust = 5.0 - 0.6 * priv + (i % 3) * 0.2
        usability = 2.5 + (i % 5) * 0.5
        loyalty = 0.5 * trust + 0.4 * usability + (i % 4) * 0.2

        started = now_time - timedelta(seconds=120 + i)
        submitted = now_time - timedelta(seconds=i)

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                q1_id: priv,
                q2_id: trust,
                q3_id: usability,
                q4_id: loyalty
            },
            "started_at": started.isoformat(),
            "submitted_at": submitted.isoformat(),
            "client_metadata": {"browser": "Chrome"}
        })
        assert submit_res.status_code == 201

    # 5. Call Bayesian Network endpoint
    bn_res = client.post(f"/api/surveys/{survey_id}/analytics/bayesian-network", json={
        "question_ids": [q1_id, q2_id, q3_id, q4_id],
        "max_parents": 3,
        "scope": "all"
    })

    assert bn_res.status_code == 200
    data = bn_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "GAUSSIAN_BAYESIAN_NETWORK_DAG"
    assert data["diagnostics"]["sample_size"] == 30
    assert data["diagnostics"]["n_nodes"] == 4
    assert data["diagnostics"]["is_acyclic"] is True
    assert len(data["nodes"]) == 4
    assert len(data["edges"]) >= 2
    assert "<svg" in data["svg_visualization"]
    assert "APA 7th Edition" in data["apa_narrative"]
