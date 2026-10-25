# -*- coding: utf-8 -*-
"""
Route integration tests for MaxDiff Best-Worst Scaling
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_maxdiff_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Cloud Platform Capabilities MaxDiff Survey",
        "description": "Best-Worst scaling preference estimation across core cloud services"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add Best question and Worst question sharing options
    common_options = [
        {"id": "feat_gpu", "label": "Dedicated H100 GPU Clusters"},
        {"id": "feat_sql", "label": "Serverless Global SQL Database"},
        {"id": "feat_auth", "label": "Enterprise SSO & Auth"},
        {"id": "feat_audit", "label": "Real-time Compliance Audit Trail"}
    ]

    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Cloud Platform Capabilities MaxDiff Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Which capability is MOST IMPORTANT (Best) to your team?",
                "is_required": True,
                "options": common_options,
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Which capability is LEAST IMPORTANT (Worst) to your team?",
                "is_required": True,
                "options": common_options,
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    bq_id = q_objs[0]["id"]
    wq_id = q_objs[1]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses with strong preference for GPU as Best and SSO as Worst
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        if i % 3 == 0:
            b_choice = "feat_gpu"
            w_choice = "feat_auth"
        elif i % 3 == 1:
            b_choice = "feat_sql"
            w_choice = "feat_audit"
        else:
            b_choice = "feat_gpu"
            w_choice = "feat_sql"

        started = now_time - timedelta(seconds=120 + i)
        submitted = now_time - timedelta(seconds=i)

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                bq_id: b_choice,
                wq_id: w_choice
            },
            "started_at": started.isoformat(),
            "submitted_at": submitted.isoformat(),
            "client_metadata": {"browser": "Chrome"}
        })
        assert submit_res.status_code == 201

    # 5. Call MaxDiff endpoint
    md_res = client.post(f"/api/surveys/{survey_id}/analytics/maxdiff", json={
        "best_question_id": bq_id,
        "worst_question_id": wq_id,
        "scope": "all"
    })

    assert md_res.status_code == 200
    data = md_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "MAXDIFF_BEST_WORST_SCALING"
    assert data["diagnostics"]["n_tasks"] >= 20
    assert data["diagnostics"]["n_items"] == 4
    assert len(data["items"]) == 4
    assert data["items"][0]["item_name"] == "Dedicated H100 GPU Clusters"
    assert "<svg" in data["svg_visualization"]
    assert "APA 7th Edition" in data["apa_narrative"]
