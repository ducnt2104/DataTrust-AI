# -*- coding: utf-8 -*-
"""
Route integration tests for Causal Discovery DAG Engine (LiNGAM & ANM)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_causal_discovery_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Observational Customer Trust & Loyalty Survey",
        "description": "Causal Discovery between Platform Trust, Service Quality, and Advocacy"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 3 questions: X1 (Quality), X2 (Trust), X3 (Advocacy)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Observational Customer Trust & Loyalty Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Service Quality (1-5)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Platform Trust (1-5)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Brand Advocacy (1-5)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    q1_id = q_objs[0]["id"]
    q2_id = q_objs[1]["id"]
    q3_id = q_objs[2]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 25 responses with non-Gaussian characteristics and causal flow: Quality -> Trust -> Advocacy
    now_time = datetime.now(timezone.utc)
    for i in range(25):
        # Non-Gaussian Likert-like ratings
        q1_val = min(5, max(1, 1 + (i % 5)))
        q2_val = min(5, max(1, int(round(0.6 * q1_val + ((i * 7) % 3) * 0.8))))
        q3_val = min(5, max(1, int(round(0.7 * q2_val + (i % 2) * 1.0))))

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    q1_id: str(q1_val),
                    q2_id: str(q2_val),
                    q3_id: str(q3_val)
                },
                "started_at": (now_time - timedelta(minutes=65 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=64 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call POST /causal-discovery
    causal_res = client.post(
        f"/api/surveys/{survey_id}/analytics/causal-discovery",
        json={
            "variable_question_ids": [q1_id, q2_id, q3_id],
            "prune_threshold": 0.05,
            "scope": "all"
        }
    )
    assert causal_res.status_code == 200
    res_data = causal_res.json()

    assert res_data["status"] == "SUCCESS"
    assert res_data["model_type"] == "CAUSAL_DISCOVERY_LINGAM_ANM"
    assert "causal_order" in res_data
    assert len(res_data["causal_order"]) == 3
    assert "directed_edges" in res_data
    assert "non_gaussianity_tests" in res_data
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
