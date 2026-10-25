# -*- coding: utf-8 -*-
"""
Route tests for Causal Inference with Network Interference & Peer Spillover Endpoint.
(POST /api/surveys/{survey_id}/analytics/network-spillover)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_network_spillover_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Workplace Wellness Pilot & Peer Spillover Survey",
        "description": "Network SUTVA & Causal Interference (Hudgens 2008; Aronow & Samii 2017)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment Z, Cluster, Covariate X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Workplace Wellness Pilot & Peer Spillover Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Employee Burnout Index (Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Wellness Stipend Received (Z)", "is_required": True},
            {"order_index": 2, "question_type": "text", "title": "Department Team ID", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Overtime Hours / Week (X)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    z_qid = questions[1]["id"]
    c_qid = questions[2]["id"]
    x_qid = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 48 responses across 8 teams (6 members per team)
    np.random.seed(77)
    now = datetime.now(timezone.utc)
    for team_idx in range(8):
        team_name = f"Dept_Team_{team_idx + 1}"
        # Treatment saturation
        treatments = np.random.binomial(1, 0.5, size=6)
        for m_idx in range(6):
            z_val = float(treatments[m_idx])
            peer_share = (np.sum(treatments) - z_val) / 5.0
            x_val = round(float(np.random.normal(8.0, 2.0)), 1)

            # Direct reduction of burnout (-4.0), spillover from treated teammates (-3.5)
            y_val = round(float(50.0 - 4.0 * z_val - 3.5 * peer_share + 0.8 * x_val + np.random.normal(0, 0.5)), 2)

            resp = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": {
                        y_qid: str(y_val),
                        z_qid: str(z_val),
                        c_qid: team_name,
                        x_qid: str(x_val)
                    },
                    "started_at": (now - timedelta(minutes=2)).isoformat(),
                    "submitted_at": now.isoformat()
                }
            )
            assert resp.status_code in (200, 201)

    # 5. Execute Network Spillover endpoint
    payload = {
        "outcome_question_id": y_qid,
        "treatment_question_id": z_qid,
        "cluster_question_id": c_qid,
        "covariate_question_ids": [x_qid],
        "spillover_threshold": 0.0,
        "alpha_level": 0.05,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/network-spillover", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 48
    assert data["n_clusters"] == 8
    assert "average_direct_effect" in data
    assert "average_spillover_effect" in data
    assert "total_overall_effect" in data
    assert "sutva_test" in data
    assert "dosage_regression" in data
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
