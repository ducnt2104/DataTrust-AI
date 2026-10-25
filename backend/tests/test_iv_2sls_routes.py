"""
Integration tests for Instrumental Variables Two-Stage Least Squares (2SLS) API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_iv_2sls_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "2SLS Marketing Elasticity & Endogeneity Identification",
        "description": "Instrumental variables analysis of marketing expenditure on business sales"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "2SLS Marketing Elasticity & Endogeneity Identification",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Doanh thu quý (Sales Revenue Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Ngân sách Marketing (Endogenous X)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Gói trợ giá thuế khu vực (Instrument Z)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Quy mô nhân sự (Exogenous Control W)",
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
    assert len(questions) == 4
    q_y = questions[0]["id"]
    q_x = questions[1]["id"]
    q_z = questions[2]["id"]
    q_w = questions[3]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/iv-2sls", json={
        "outcome_question_id": q_y,
        "endogenous_question_id": q_x,
        "instrument_question_ids": [q_z],
        "control_question_ids": [q_w],
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit 20 responses
    now = datetime.now(timezone.utc)
    for i in range(20):
        z_val = 5.0 + (i * 1.5)
        w_val = 10.0 + (i % 6)
        # Endogenous X driven by Z and unobserved demand shock U
        u_shock = 2.0 if (i % 3 == 0) else -1.0
        x_val = 15.0 + 1.6 * z_val + 0.5 * w_val + 2.0 * u_shock
        # Y with true beta_X = 2.0 + shock U
        y_val = 40.0 + 2.0 * x_val + 1.2 * w_val + 3.0 * u_shock

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=1200 + i * 15)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 15)).isoformat(),
            "answers": {
                q_y: y_val,
                q_x: x_val,
                q_z: z_val,
                q_w: w_val
            }
        })
        assert sub_res.status_code == 201

    # 5. Run IV 2SLS Analysis
    iv_res = client.post(f"/api/surveys/{survey_id}/analytics/iv-2sls", json={
        "outcome_question_id": q_y,
        "endogenous_question_id": q_x,
        "instrument_question_ids": [q_z],
        "control_question_ids": [q_w],
        "scope": "all"
    })
    assert iv_res.status_code == 200
    data = iv_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 20
    assert data["instruments_count"] == 1
    assert data["iv_estimate"]["beta"] is not None
    assert data["iv_estimate"]["se"] > 0
    assert data["first_stage_diagnostics"]["f_statistic"] > 0
    assert isinstance(data["first_stage_diagnostics"]["is_weak_instrument"], bool)
    assert isinstance(data["wu_hausman_test"]["is_endogenous"], bool)
    assert "<svg" in data["svg_chart"]
    assert "2SLS" in data["apa_narrative"]
