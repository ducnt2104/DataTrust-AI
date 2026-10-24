# -*- coding: utf-8 -*-
"""
Route integration tests for Regression Kink Design (RKD) Engine
Card, Lee, Pei, & Weber (2015); Dong (2018)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rkd_routes_sharp_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Progressive Tax Bracket & Labor Elasticity Survey (RKD)",
        "description": "Estimating behavioral response derivative at income threshold c=50k"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Y), Running (X)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Progressive Tax Bracket & Labor Elasticity Survey (RKD)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Annual Labor Supply Hours",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Gross Pre-Tax Earnings ($k)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_x = questions[1]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit 60 responses around cutoff c = 50.0
    np.random.seed(42)
    n = 60
    x_vals = np.linspace(25.0, 75.0, n)
    now_time = datetime.now(timezone.utc)
    for i in range(n):
        x = float(x_vals[i])
        kink = -0.75 * max(0.0, x - 50.0)
        y = 2000.0 + 5.0 * (x - 50.0) + kink + float(np.random.normal(0, 0.5))

        started = (now_time - timedelta(minutes=70 - i)).isoformat()
        completed = (now_time - timedelta(minutes=65 - i)).isoformat()

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    qid_y: round(y, 2),
                    qid_x: round(x, 2)
                },
                "started_at": started,
                "submitted_at": completed
            }
        )
        assert resp.status_code == 201

    # 4. Call RKD evaluation route (Sharp RKD)
    rkd_res = client.post(f"/api/surveys/{survey_id}/analytics/regression-kink", json={
        "outcome_question_id": qid_y,
        "running_question_id": qid_x,
        "cutoff": 50.0,
        "bandwidth": 20.0,
        "polynomial_order": 1,
        "known_kink_slope": 1.0,
        "scope": "all"
    })
    assert rkd_res.status_code == 200
    data = rkd_res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "REGRESSION_KINK_DESIGN_CARD_2015"
    diag = data["diagnostics"]
    assert diag["cutoff"] == 50.0
    assert diag["effective_sample_size"] >= 30
    assert "tau_rkd" in diag
    assert diag["tau_rkd"] < -0.4
    assert diag["p_value"] < 0.05
    assert "mccrary_p_value" in diag
    assert "binned_scatter" in data
    assert len(data["binned_scatter"]) > 5
    assert "<svg" in data["svg_visualization"]
    assert "Regression Kink Design" in data["apa_narrative"]


def test_rkd_routes_fuzzy_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Benefit Phase-Out Program Survey (Fuzzy RKD)",
        "description": "Estimating fuzzy kink causal effect with endogenous treatment slope"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Y), Running (X), Treatment (D)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Benefit Phase-Out Program Survey (Fuzzy RKD)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Household Food Spending ($)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Reported Income Tier Index",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Actual Subsidy Amount Received",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_x = questions[1]["id"]
    qid_d = questions[2]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit 50 responses around cutoff c = 30.0
    np.random.seed(123)
    n = 50
    x_vals = np.linspace(10.0, 50.0, n)
    now_time = datetime.now(timezone.utc)
    for i in range(n):
        x = float(x_vals[i])
        d = 100.0 - (1.0 * max(0.0, x - 30.0)) + float(np.random.normal(0, 0.3))
        y = 50.0 + 1.5 * d + float(np.random.normal(0, 0.5))

        started = (now_time - timedelta(minutes=60 - i)).isoformat()
        completed = (now_time - timedelta(minutes=55 - i)).isoformat()

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    qid_y: round(y, 2),
                    qid_x: round(x, 2),
                    qid_d: round(d, 2)
                },
                "started_at": started,
                "submitted_at": completed
            }
        )
        assert resp.status_code == 201

    # 4. Call Fuzzy RKD route
    rkd_res = client.post(f"/api/surveys/{survey_id}/analytics/regression-kink", json={
        "outcome_question_id": qid_y,
        "running_question_id": qid_x,
        "treatment_question_id": qid_d,
        "cutoff": 30.0,
        "bandwidth": 18.0,
        "scope": "all"
    })
    assert rkd_res.status_code == 200
    data = rkd_res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "REGRESSION_KINK_DESIGN_CARD_2015"
    diag = data["diagnostics"]
    assert diag["cutoff"] == 30.0
    assert abs(diag["tau_rkd"] - 1.5) < 0.6
    assert data["apa_narrative"] is not None


def test_rkd_routes_insufficient_sample():
    create_res = client.post("/api/surveys", json={
        "title": "Small Sample Survey",
        "description": "Testing insufficient sample handling"
    })
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Small Sample Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Y", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "X", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_x = questions[1]["id"]

    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    now_time = datetime.now(timezone.utc)
    for i in range(5):
        client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    qid_y: float(10 + i),
                    qid_x: float(50 + i)
                },
                "started_at": (now_time - timedelta(minutes=10 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=8 - i)).isoformat()
            }
        )

    res = client.post(f"/api/surveys/{survey_id}/analytics/regression-kink", json={
        "outcome_question_id": qid_y,
        "running_question_id": qid_x,
        "cutoff": 50.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INSUFFICIENT_SAMPLE"
    assert "tối thiểu 20 quan sát" in data["message"]
