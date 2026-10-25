"""
Route tests for Many-Weak-IV Robust JIVE, LIML & Fuller (1977) Endpoint
(POST /api/surveys/{survey_id}/analytics/many-weak-iv-jive)
DataTrust Iteration 191
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_many_weak_iv_jive_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Many-Weak-IV JIVE Evaluation",
        "description": "Leave-one-out JIVE, LIML, and Fuller (1977) estimation with many weak instruments"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Many-Weak-IV JIVE Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Treatment Exposure (D)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Outcome Score (Y)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Instrument Z1", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Instrument Z2", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Instrument Z3", "is_required": True},
            {"order_index": 5, "question_type": "number", "title": "Instrument Z4", "is_required": True},
            {"order_index": 6, "question_type": "number", "title": "Covariate Experience (W)", "is_required": True},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    q_map = {q["title"]: q["id"] for q in detail_res.json()["questions"]}
    q_d = q_map["Treatment Exposure (D)"]
    q_y = q_map["Outcome Score (Y)"]
    q_z1 = q_map["Instrument Z1"]
    q_z2 = q_map["Instrument Z2"]
    q_z3 = q_map["Instrument Z3"]
    q_z4 = q_map["Instrument Z4"]
    q_w = q_map["Covariate Experience (W)"]

    # 4. Generate 45 responses
    np.random.seed(191)
    now = datetime.now(timezone.utc)
    N = 45

    for i in range(N):
        z1 = float(np.random.normal(0, 1))
        z2 = float(np.random.normal(0, 1))
        z3 = float(np.random.normal(0, 1))
        z4 = float(np.random.normal(0, 1))
        w = float(np.random.normal(10, 2))

        # Endogeneity
        u = np.random.normal(0, 1)
        d = 0.5 * z1 + 0.4 * z2 + 0.3 * z3 + 0.2 * z4 + 0.2 * w + 0.8 * u + np.random.normal(0, 0.5)
        # True causal effect beta = 2.0
        y = 2.0 * d + 0.6 * w + 0.5 * u + np.random.normal(0, 0.5)

        answers = {
            q_d: str(round(d, 3)),
            q_y: str(round(y, 3)),
            q_z1: str(round(z1, 3)),
            q_z2: str(round(z2, 3)),
            q_z3: str(round(z3, 3)),
            q_z4: str(round(z4, 3)),
            q_w: str(round(w, 3)),
        }

        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers,
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat(),
        })
        assert resp.status_code in (200, 201)

    # 5. Call endpoint
    eval_res = client.post(
        f"/api/surveys/{survey_id}/analytics/many-weak-iv-jive",
        json={
            "treatment_question_id": q_d,
            "outcome_question_id": q_y,
            "instrument_question_ids": [q_z1, q_z2, q_z3, q_z4],
            "covariate_question_ids": [q_w],
            "fuller_a": 1.0,
            "scope": "all"
        }
    )
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 45
    assert data["instruments_count"] == 4

    # Check estimators
    comp = data["estimator_comparisons"]
    assert len(comp) == 5
    estimators = [r["estimator"] for r in comp]
    assert any("OLS" in e for e in estimators)
    assert any("2SLS" in e for e in estimators)
    assert any("JIVE" in e for e in estimators)
    assert any("LIML" in e for e in estimators)
    assert any("Fuller" in e for e in estimators)

    for r in comp:
        assert isinstance(r["estimate"], float)
        assert isinstance(r["std_error"], float)
        assert len(r["ci_95"]) == 2

    assert data["first_stage_diagnostics"]["f_statistic"] > 0
    assert data["overidentification_test"]["sargan_statistic"] >= 0
    assert "svg_visualization" in data
    assert len(data["apa_narrative"]) > 50


def test_many_weak_iv_jive_not_found():
    res = client.post("/api/surveys/non-existent-survey/analytics/many-weak-iv-jive", json={
        "treatment_question_id": "q1",
        "outcome_question_id": "q2",
        "instrument_question_ids": ["z1", "z2"]
    })
    assert res.status_code == 404
