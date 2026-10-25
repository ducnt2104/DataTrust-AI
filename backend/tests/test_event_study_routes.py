"""
Integration tests for Dynamic Event-Study API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_event_study_route_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Dynamic Event Study Evaluation",
        "description": "Evaluating policy dynamic adoption effects over waves"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT: unit (short_text), period (number), score (number)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Dynamic Event Study Evaluation",
        "questions": [
            {
                "order_index": 0,
                "question_type": "short_text",
                "title": "Đơn vị / Chi nhánh",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Kỳ khảo sát (Wave)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Điểm hiệu suất (Performance Score)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 3
    q_unit = questions[0]["id"]
    q_period = questions[1]["id"]
    q_score = questions[2]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/event-study", json={
        "unit_question_id": q_unit,
        "time_question_id": q_period,
        "outcome_question_id": q_score,
        "treated_units": ["Branch_T1", "Branch_T2"],
        "global_event_time": 3,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit panel responses across 4 branches and 5 waves
    branches = {
        "Branch_T1": [20, 22, 35, 38, 40],  # Event at wave 3 (+10 jump)
        "Branch_T2": [25, 27, 40, 42, 45],
        "Branch_C1": [15, 17, 18, 20, 21],  # Control
        "Branch_C2": [30, 32, 33, 35, 36]
    }

    waves = [1, 2, 3, 4, 5]
    now = datetime.now(timezone.utc)
    step = 0

    for b_name, scores in branches.items():
        for w_idx, w_val in enumerate(waves):
            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "started_at": (now - timedelta(seconds=1000 + step * 20)).isoformat(),
                "submitted_at": (now - timedelta(seconds=step * 20)).isoformat(),
                "answers": {
                    q_unit: b_name,
                    q_period: w_val,
                    q_score: scores[w_idx]
                }
            })
            assert sub_res.status_code == 201
            step += 1

    # 5. Run Event Study Analysis
    es_res = client.post(f"/api/surveys/{survey_id}/analytics/event-study", json={
        "unit_question_id": q_unit,
        "time_question_id": q_period,
        "outcome_question_id": q_score,
        "treated_units": ["Branch_T1", "Branch_T2"],
        "global_event_time": 3,
        "scope": "all"
    })
    assert es_res.status_code == 200
    data = es_res.json()
    assert data["status"] == "SUCCESS"
    assert data["units_count"] == 4
    assert data["periods_count"] == 5
    assert data["pre_trend_p_value"] is not None
    assert isinstance(data["parallel_trends_supported"], bool)
    assert len(data["event_coefficients"]) >= 3
    assert "<svg" in data["svg_chart"]
    assert "Dynamic Event-Study" in data["apa_narrative"]
