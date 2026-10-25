# -*- coding: utf-8 -*-
"""
Route integration tests for Heckman Two-Step Sample Selection Model (Heckman 1979)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_heckman_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Labor Market Wage Survey",
        "description": "Heckman sample selection evaluation of optional reported wage"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Wage Y, Covariate Education X, Selection Instrument ChildrenCount Z
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Labor Market Wage Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Reported Monthly Wage (mil)", "is_required": False, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Years of Education", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Number of Young Children (Exclusion Instrument)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    x_qid = q_objs[1]["id"]
    z_qid = q_objs[2]["id"]

    # 3. Publish
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses (with ~60% reporting wage and ~40% leaving it blank)
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        edu = 10.0 + (i % 6)
        children = (i % 3)
        # Likelihood of working decreases with children and increases with education
        will_report = (edu > 12.0 or (children == 0 and i % 2 == 0))
        wage_val = (3.0 + 1.2 * edu + (i % 4) * 0.5) if will_report else None

        answers_payload = {
            x_qid: str(edu),
            z_qid: str(children)
        }
        if wage_val is not None:
            answers_payload[y_qid] = str(round(wage_val, 1))

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_payload,
                "started_at": (now_time - timedelta(minutes=60 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=59 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call /heckman-selection endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/heckman-selection",
        json={
            "outcome_question_id": y_qid,
            "outcome_covariate_question_ids": [x_qid],
            "exclusion_restriction_question_ids": [z_qid],
            "scope": "all"
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "HECKMAN_TWO_STEP_SELECTION"
    assert "diagnostics" in data
    assert data["diagnostics"]["n_total_observations"] == 30
    assert len(data["coefficients_comparison"]) == 2
    assert "<svg" in data["svg_visualization"]
    assert "Heckman" in data["apa_narrative"]
