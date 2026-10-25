"""
Integration tests for Bayesian Structural Time Series (BSTS) Causal Impact API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_bsts_causal_impact_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "BSTS Brand Sentiment Causal Impact Tracking",
        "description": "Evaluating customer brand trust before and after campaign launch"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT: period (number), score (number), control_metric (number)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "BSTS Brand Sentiment Causal Impact Tracking",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Tuần khảo sát (Week Number)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Chỉ số tin tưởng thương hiệu (Brand Trust Index)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Chỉ số kinh tế vĩ mô đối chứng",
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
    q_week = questions[0]["id"]
    q_score = questions[1]["id"]
    q_control = questions[2]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/bsts-causal-impact", json={
        "time_question_id": q_week,
        "outcome_question_id": q_score,
        "intervention_time": 6,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit 8 time-series responses (weeks 1..8, campaign launched at week 6)
    weeks = list(range(1, 9))
    now = datetime.now(timezone.utc)

    for idx, w in enumerate(weeks):
        base_y = 60.0 + 1.0 * w
        if w >= 6:
            base_y += 12.0  # true campaign impact
        macro_x = 100.0 + 0.5 * w

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=1000 + idx * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=idx * 20)).isoformat(),
            "answers": {
                q_week: w,
                q_score: base_y,
                q_control: macro_x
            }
        })
        assert sub_res.status_code == 201

    # 5. Run BSTS Causal Impact Analysis
    bsts_res = client.post(f"/api/surveys/{survey_id}/analytics/bsts-causal-impact", json={
        "time_question_id": q_week,
        "outcome_question_id": q_score,
        "intervention_time": 6,
        "covariate_question_ids": [q_control],
        "scope": "all"
    })
    assert bsts_res.status_code == 200
    data = bsts_res.json()
    assert data["status"] == "SUCCESS"
    assert data["pre_periods_count"] == 5
    assert data["post_periods_count"] == 3
    assert data["avg_pointwise_effect"] is not None
    assert data["cumulative_effect"] is not None
    assert data["relative_effect_pct"] is not None
    assert data["posterior_tail_p_value"] is not None
    assert isinstance(data["is_significant"], bool)
    assert len(data["trajectory"]) == 8
    assert "<svg" in data["svg_chart"]
    assert "Bayesian Structural Time Series" in data["apa_narrative"]
