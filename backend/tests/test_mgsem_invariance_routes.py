# -*- coding: utf-8 -*-
"""
Route integration tests for Multi-Group Structural Equation Modeling (MG-SEM) Invariance & Latent Means Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mgsem_invariance_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Cross-Regional Digital Readiness & Technology Adoption",
        "description": "Multi-group measurement invariance and latent mean difference test"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Grouping Variable (Region: 1=North, 2=South) and 3 continuous indicators (Adoption items)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Cross-Regional Digital Readiness & Technology Adoption",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Geographic Region (1=North, 2=South)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Digital Infrastructure Satisfaction (1-5)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Cloud Platform Usability (1-5)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Technology Adoption Intention (1-5)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    g_qid = q_objs[0]["id"]
    i1_qid = q_objs[1]["id"]
    i2_qid = q_objs[2]["id"]
    i3_qid = q_objs[3]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 32 responses across 2 groups
    now_time = datetime.now(timezone.utc)
    for i in range(32):
        grp = 1 if (i % 2 == 0) else 2
        # Base latent trait
        eta = 2.0 if grp == 1 else 3.2
        val1 = min(5.0, max(1.0, 0.5 + 0.8 * eta + (i % 3) * 0.2))
        val2 = min(5.0, max(1.0, 0.4 + 0.7 * eta + (i % 2) * 0.3))
        val3 = min(5.0, max(1.0, 0.6 + 0.9 * eta + (i % 4) * 0.1))

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    g_qid: str(grp),
                    i1_qid: str(round(val1, 1)),
                    i2_qid: str(round(val2, 1)),
                    i3_qid: str(round(val3, 1))
                },
                "started_at": (now_time - timedelta(minutes=65 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=64 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call POST /mgsem-invariance
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/mgsem-invariance",
        json={
            "group_question_id": g_qid,
            "indicator_question_ids": [i1_qid, i2_qid, i3_qid],
            "scope": "all"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "MULTI_GROUP_SEM_INVARIANCE"
    assert "invariance_hierarchy" in data
    assert len(data["invariance_hierarchy"]) == 4
    assert "latent_means_comparison" in data
    assert "indicator_parameters" in data
    assert len(data["indicator_parameters"]) == 3
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data
