# -*- coding: utf-8 -*-
"""
Route integration tests for Fractional Response QMLE Regression (Papke & Wooldridge 1996, 2008)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_fractional_response_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Household Budget Allocation Survey",
        "description": "Survey on % household expenditure allocated to healthcare"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome rate Y (% 0-100), Covariate Income X1, Covariate FamilySize X2
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Household Budget Allocation Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Healthcare Budget Share (%)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Household Monthly Income (mil)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Family Members Count", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    inc_qid = q_objs[1]["id"]
    fam_qid = q_objs[2]["id"]

    # 3. Publish
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 25 responses
    now_time = datetime.now(timezone.utc)
    for i in range(25):
        inc = 10.0 + (i % 8) * 5.0
        fam = 2.0 + (i % 4)
        # Bounded rate % between 0% and 100%
        raw_pct = (fam * 6.0) - (inc * 0.4) + 15.0 + (i % 3) * 2.0
        pct_val = max(0.0, min(100.0, raw_pct))

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(round(pct_val, 1)),
                    inc_qid: str(round(inc, 1)),
                    fam_qid: str(round(fam, 1))
                },
                "started_at": (now_time - timedelta(minutes=50 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=49 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call fractional-response endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/fractional-response",
        json={
            "outcome_question_id": y_qid,
            "covariate_question_ids": [inc_qid, fam_qid],
            "link": "logit",
            "scale_from_percentage": True,
            "scope": "all"
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "FRACTIONAL_RESPONSE_QMLE"
    assert "diagnostics" in data
    assert data["diagnostics"]["n_samples"] == 25
    assert len(data["coefficients"]) == 3
    assert "<svg" in data["svg_visualization"]
    assert "Papke & Wooldridge" in data["apa_narrative"]
