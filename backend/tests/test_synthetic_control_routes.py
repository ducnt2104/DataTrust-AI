"""
Integration tests for Synthetic Control Method (SCM) API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_synthetic_control_route_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "SCM Policy Evaluation Survey",
        "description": "Evaluating policy impact on regional satisfaction over time"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 3 questions via PUT survey: unit (short_text), period (number), outcome (number)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "SCM Policy Evaluation Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "short_text",
                "title": "Khu vực / Đơn vị",
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
                "title": "Điểm hài lòng dịch vụ (Satisfaction)",
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
    q_outcome = questions[2]["id"]

    # 3. Test empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/synthetic-control", json={
        "unit_question_id": q_unit,
        "period_question_id": q_period,
        "outcome_question_id": q_outcome,
        "treated_unit": "Region_A",
        "treatment_period": 4,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit panel responses
    # 4 units: Region_A (treated), Region_B, Region_C, Region_D
    # Waves: 1, 2, 3 (pre), 4, 5 (post)
    units_data = {
        "Region_A": [50.0, 52.0, 55.0, 75.0, 80.0],  # +20 boost in wave 4, 5
        "Region_B": [40.0, 42.0, 44.0, 45.0, 46.0],
        "Region_C": [60.0, 62.0, 65.0, 66.0, 67.0],
        "Region_D": [30.0, 31.0, 33.0, 34.0, 35.0]
    }

    waves = [1, 2, 3, 4, 5]
    now = datetime.now(timezone.utc)
    step = 0

    for unit_name, vals in units_data.items():
        for w_idx, w_val in enumerate(waves):
            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "started_at": (now - timedelta(seconds=1000 + step * 20)).isoformat(),
                "submitted_at": (now - timedelta(seconds=step * 20)).isoformat(),
                "answers": {
                    q_unit: unit_name,
                    q_period: w_val,
                    q_outcome: vals[w_idx]
                }
            })
            assert sub_res.status_code == 201
            step += 1

    # 5. Run SCM Analysis
    scm_res = client.post(f"/api/surveys/{survey_id}/analytics/synthetic-control", json={
        "unit_question_id": q_unit,
        "period_question_id": q_period,
        "outcome_question_id": q_outcome,
        "treated_unit": "Region_A",
        "treatment_period": 4,
        "scope": "all"
    })
    assert scm_res.status_code == 200
    data = scm_res.json()
    assert data["status"] == "SUCCESS"
    assert data["treated_unit"] == "Region_A"
    assert data["treatment_period"] == "4"
    assert data["donor_pool_count"] == 3
    assert data["att_effect"] is not None
    assert data["rmspe_pre"] is not None
    assert data["rmspe_post"] is not None
    assert data["rmspe_ratio"] is not None
    assert data["empirical_p_value"] is not None
    assert isinstance(data["is_significant"], bool)
    assert len(data["trajectory"]) == 5
    assert "<svg" in data["svg_chart"]
    assert "Synthetic Control Method" in data["apa_narrative"]
