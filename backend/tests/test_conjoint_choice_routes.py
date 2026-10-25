# -*- coding: utf-8 -*-
"""
Route integration tests for Conjoint Analysis & Discrete Choice Experiment (DCE) Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_conjoint_choice_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Smart Home IoT Choice-Based Conjoint Survey",
        "description": "DCE Preference Evaluation and Willingness to Pay"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Choice Indicator (1=Chosen, 0=Passed), Quality (1-5), Warranty (Years 1-3), Price (mil VND)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Smart Home IoT Choice-Based Conjoint Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Profile Chosen (1=Yes, 0=No)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Hardware Build Quality (1-5)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Warranty Duration (Years)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Subscription Price (mil VND)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    c_qid = q_objs[0]["id"]
    q1_qid = q_objs[1]["id"]
    q2_qid = q_objs[2]["id"]
    p_qid = q_objs[3]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 choice observations with balanced choices
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        qual = 1.0 + (i % 5)
        warr = 1.0 + (i % 3)
        price = 5.0 + (i % 5) * 2.0
        # Balanced choice rule
        choice = 1 if (i % 2 == 0) else 0

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    c_qid: str(choice),
                    q1_qid: str(round(qual, 1)),
                    q2_qid: str(round(warr, 1)),
                    p_qid: str(round(price, 1))
                },
                "started_at": (now_time - timedelta(minutes=65 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=64 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call POST /conjoint-choice
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/conjoint-choice",
        json={
            "choice_question_id": c_qid,
            "attribute_question_ids": [q1_qid, q2_qid, p_qid],
            "price_question_id": p_qid,
            "price_unit": "mil VND",
            "scope": "all"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "CONJOINT_DISCRETE_CHOICE_MNL"
    assert "part_worth_utilities" in data
    assert len(data["part_worth_utilities"]) == 3
    assert "willingness_to_pay" in data
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data
