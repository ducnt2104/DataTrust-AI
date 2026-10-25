# -*- coding: utf-8 -*-
"""
Route integration tests for Multidimensional Item Response Theory (MIRT; Reckase 2009)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mirt_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Multidimensional Cognitive Competencies Survey",
        "description": "MIRT evaluation across analytical and verbal skill dimensions"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 4 questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Multidimensional Cognitive Competencies Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Math Logic Q1", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Math Algebra Q2", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Verbal Vocabulary Q3", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Verbal Reading Q4", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    qids = [q["id"] for q in q_objs]

    # 3. Publish
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 25 responses
    now_time = datetime.now(timezone.utc)
    for i in range(25):
        m1 = 1 if (i % 2 == 0) else 0
        m2 = 1 if (i % 3 != 0) else 0
        v1 = 1 if (i % 4 != 0) else 0
        v2 = 1 if (i % 5 != 0) else 0

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    qids[0]: str(m1),
                    qids[1]: str(m2),
                    qids[2]: str(v1),
                    qids[3]: str(v2)
                },
                "started_at": (now_time - timedelta(minutes=60 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=59 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call /mirt endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/mirt",
        json={
            "item_question_ids": qids,
            "n_dimensions": 2,
            "dimension_names": ["Năng lực Toán học", "Năng lực Ngôn ngữ"],
            "max_em_iter": 20,
            "scope": "all"
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "MULTIDIMENSIONAL_IRT_2PL"
    assert "diagnostics" in data
    assert data["diagnostics"]["n_samples"] == 25
    assert len(data["item_parameters"]) == 4
    assert "<svg" in data["svg_visualization"]
    assert "Reckase" in data["apa_narrative"]
