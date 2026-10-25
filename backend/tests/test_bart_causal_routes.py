# -*- coding: utf-8 -*-
"""
Route integration tests for Bayesian Additive Regression Trees (BART) Causal Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_bart_causal_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "FinTech Cashless Payment Adoption Survey",
        "description": "BART Heterogeneous Treatment Effect on Transaction Frequency"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Treatment T (Cashback Incentive: 1/0), Outcome Y (Transactions/Mo), Covariates X1 (Age), X2 (Income)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "FinTech Cashless Payment Adoption Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Cashback Program Enrolled (1=Yes, 0=No)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Monthly Digital Transactions", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "User Age (Years)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Monthly Income (mil VND)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    t_qid = q_objs[0]["id"]
    y_qid = q_objs[1]["id"]
    x1_qid = q_objs[2]["id"]
    x2_qid = q_objs[3]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 32 responses
    now_time = datetime.now(timezone.utc)
    for i in range(32):
        age = 20.0 + (i % 8) * 5.0
        income = 10.0 + (i % 6) * 4.0
        # Treatment assignment
        t = 1 if (i % 2 == 0) else 0
        # Outcome with heterogeneous treatment effect: younger users benefit more
        tau = max(1.0, 15.0 - 0.2 * age + 0.1 * income)
        y = 5.0 + 0.2 * income + t * tau + (i % 3)

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    t_qid: str(t),
                    y_qid: str(round(y, 1)),
                    x1_qid: str(round(age, 1)),
                    x2_qid: str(round(income, 1))
                },
                "started_at": (now_time - timedelta(minutes=65 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=64 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call POST /bart-causal
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/bart-causal",
        json={
            "treatment_question_id": t_qid,
            "outcome_question_id": y_qid,
            "covariate_question_ids": [x1_qid, x2_qid],
            "n_trees": 25,
            "n_samples": 80,
            "scope": "all"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "BAYESIAN_ADDITIVE_REGRESSION_TREES_CAUSAL"
    assert "treatment_effects" in data
    assert "ate" in data["treatment_effects"]
    assert "att" in data["treatment_effects"]
    assert "ite_distribution" in data
    assert "variable_importance" in data
    assert len(data["variable_importance"]) == 2
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data
