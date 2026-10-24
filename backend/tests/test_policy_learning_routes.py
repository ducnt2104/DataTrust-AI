# -*- coding: utf-8 -*-
"""
Route integration tests for Doubly Robust Policy Learning Engine
Athey & Wager (2021); Dudík et al. (2011)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_policy_learning_route_success():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Public Health Intervention Policy Targeting Survey",
        "description": "Doubly robust optimal individualized treatment regime learning"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Public Health Intervention Policy Targeting Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Chỉ số Sức khỏe Cộng đồng (Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Tham gia Chương trình Sức khỏe (Treatment W)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Tham gia (Treated)"},
                    {"value": "0", "label": "Không tham gia (Control)"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Tuổi / Độ tuổi (Age Covariate X1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Thu nhập Hộ gia đình (Income Covariate X2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_w = questions[1]["id"]
    qid_x1 = questions[2]["id"]
    qid_x2 = questions[3]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit 40 responses
    np.random.seed(42)
    now_time = datetime.now(timezone.utc)

    for i in range(40):
        x1 = float(np.random.uniform(20.0, 65.0))
        x2 = float(np.random.uniform(5.0, 50.0))
        # Treatment assignment
        w_val = 1 if (i % 2 == 0) else 0
        tau = 3.0 if x1 > 40.0 else -1.0
        y = float(50.0 + 0.2 * x1 + 0.3 * x2 + w_val * tau + np.random.normal(0, 0.5))

        started = (now_time - timedelta(minutes=120 - i)).isoformat()
        submitted = (now_time - timedelta(minutes=115 - i)).isoformat()

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    qid_y: round(y, 2),
                    qid_w: str(w_val),
                    qid_x1: round(x1, 1),
                    qid_x2: round(x2, 1)
                },
                "started_at": started,
                "submitted_at": submitted
            }
        )
        assert resp.status_code == 201

    # 4. Call policy learning endpoint
    pol_res = client.post(f"/api/surveys/{survey_id}/analytics/policy-learning", json={
        "outcome_question_id": qid_y,
        "treatment_question_id": qid_w,
        "covariate_question_ids": [qid_x1, qid_x2],
        "primary_feature_idx": 0,
        "n_bootstraps": 100,
        "scope": "all"
    })

    assert pol_res.status_code == 200
    data = pol_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "DOUBLY_ROBUST_POLICY_LEARNING_ATHEY_WAGER_2021"
    diag = data["diagnostics"]
    assert diag["sample_size"] == 40
    assert "pct_recommended_treatment" in diag
    assert "optimal_welfare_value" in diag
    assert "net_welfare_gain" in diag
    assert len(data["regimes_comparison"]) == 4
    assert len(data["sample_allocations"]) > 0
    assert "<svg" in data["svg_visualization"]
    assert "Athey & Wager" in data["apa_narrative"] or "Học Chính sách" in data["apa_narrative"]


def test_policy_learning_validation_errors():
    # Non-existent survey
    bad_res = client.post("/api/surveys/non-existent-survey/analytics/policy-learning", json={
        "outcome_question_id": "q1",
        "treatment_question_id": "q2",
        "covariate_question_ids": ["q3"]
    })
    assert bad_res.status_code == 404

    # Create survey but provide invalid QID
    s = client.post("/api/surveys", json={"title": "Test Survey Validation"}).json()
    survey_id = s["id"]

    bad_qid_res = client.post(f"/api/surveys/{survey_id}/analytics/policy-learning", json={
        "outcome_question_id": "invalid_qid",
        "treatment_question_id": "q2",
        "covariate_question_ids": ["q3"]
    })
    assert bad_qid_res.status_code == 400
    assert "không tồn tại" in bad_qid_res.json()["detail"]
