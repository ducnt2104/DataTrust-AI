"""
Route tests for Robust E-Values & Multi-Bias Causal Sensitivity Endpoint
(POST /api/surveys/{survey_id}/analytics/e-value-sensitivity)
DataTrust Iteration 185
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_e_value_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust E-Value Causal Sensitivity Survey",
        "description": "Sensitivity analysis for unmeasured confounding with E-values (VanderWeele & Ding 2017)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust E-Value Causal Sensitivity Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Chỉ Số Hạnh Phúc (Outcome Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Tham Gia Hoạt Động Xã Hội (Treatment D: 1/0)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Thu Nhập Hàng Tháng (Covariate X)", "is_required": False}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Fetch question IDs
    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    questions = detail_res.json()["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    x_qid = questions[2]["id"]

    # 5. Submit 40 responses
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    N = 40
    for i in range(N):
        x_val = float(np.random.normal(20.0, 5.0))
        d_val = 1 if (i % 2 == 0) else 0
        y_val = float(50.0 + 8.0 * d_val + 0.5 * x_val + np.random.normal(0, 1.5))

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y_val, 2)),
                d_qid: str(d_val),
                x_qid: str(round(x_val, 2))
            },
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code == 201

    # 6. Call E-Value endpoint
    eval_res = client.post(f"/api/surveys/{survey_id}/analytics/e-value-sensitivity", json={
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x_qid],
        "effect_type": "OLS_CONTINUOUS",
        "selection_bias_rr": 1.1,
        "misclassification_rr": 1.05,
        "scope": "all"
    })

    assert eval_res.status_code == 200
    data = eval_res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == N
    assert data["point_estimate"] > 5.0
    assert "e_value_results" in data
    assert data["e_value_results"]["e_value_estimate"] > 1.5
    assert len(data["benchmarks"]) == 4
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]
