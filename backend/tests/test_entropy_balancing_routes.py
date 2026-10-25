"""
Route tests for Entropy Balancing & Exact Moment-Condition Causal Reweighting Endpoint
(POST /api/surveys/{survey_id}/analytics/entropy-balancing)
DataTrust Iteration 183
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_entropy_balancing_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Entropy Balancing Survey",
        "description": "Evaluation of workforce training program with exact moment condition balance (Hainmueller 2012)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: outcome, treatment, covariate 1, covariate 2
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Entropy Balancing Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Năng suất Lao động (Outcome Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Khóa Đào tạo Kỹ thuật số (Treatment D: 1/0)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Số năm Kinh nghiệm (Covariate X1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Cấp bậc Chuyên môn (Covariate X2)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Fetch questions to get IDs
    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    questions = detail_res.json()["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]

    # 5. Submit 50 observational responses with common support
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    N = 50
    for i in range(N):
        x1 = float(np.random.normal(5.0, 1.5))
        x2 = float(np.random.normal(3.0, 1.0))
        prob_t = 1.0 / (1.0 + np.exp(-(0.2 * (x1 - 5.0) + 0.2 * (x2 - 3.0))))
        d = 1 if np.random.uniform(0, 1) < prob_t else 0
        y = float(20.0 + 5.0 * d + 2.0 * x1 + 1.5 * x2 + np.random.normal(0, 1.0))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y, 2)),
                d_qid: str(d),
                x1_qid: str(round(x1, 2)),
                x2_qid: str(round(x2, 2))
            },
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert sub_res.status_code == 201

    # 6. Call Entropy Balancing endpoint
    eb_res = client.post(f"/api/surveys/{survey_id}/analytics/entropy-balancing", json={
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "moment_orders": [1],
        "tolerance": 1e-5,
        "scope": "all"
    })

    assert eb_res.status_code == 200
    data = eb_res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == N
    assert data["treated_count"] > 0
    assert data["control_count"] > 0

    assert "treatment_effect" in data
    assert "att" in data["treatment_effect"]
    assert "se" in data["treatment_effect"]
    assert "p_value" in data["treatment_effect"]

    assert len(data["covariate_balance"]) == 2
    for b in data["covariate_balance"]:
        assert abs(b["smd_weighted"]) < 0.05

    assert data["diagnostics"]["converged"] is True
    assert data["diagnostics"]["effective_sample_size"] > 0
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]
