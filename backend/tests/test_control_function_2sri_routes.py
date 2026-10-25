"""
Route tests for Two-Stage Residual Inclusion (2SRI) & Control Function Causal Endpoint
(POST /api/surveys/{survey_id}/analytics/control-function-2sri)
DataTrust Iteration 186
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_control_function_2sri_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust 2SRI Control Function Survey",
        "description": "Causal estimation for nonlinear endogenous models via Control Function (Terza et al. 2008)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust 2SRI Control Function Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Khả Năng Chấp Thuận Chính Sách (Outcome Y: 0/1)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Tham Gia Chương Trình (Treatment D: 0/1)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Khoảng Cách Địa Lý Đến Trung Tâm (Instrument Z)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Trình Độ Học Vấn (Covariate X)", "is_required": False}
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
    z_qid = questions[2]["id"]
    x_qid = questions[3]["id"]

    # 5. Submit 45 responses with simulated endogeneity
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    N = 45
    for i in range(N):
        x_val = float(np.random.normal(12.0, 3.0))
        z_val = float(np.random.normal(5.0, 2.0))
        u_val = float(np.random.normal(0.0, 1.0))

        # First stage latent
        d_latent = 0.5 * z_val + 0.2 * x_val + 0.8 * u_val - 4.5
        d_val = 1 if d_latent > 0 else 0

        # Structural latent
        y_latent = 1.0 * d_val + 0.3 * (x_val - 12.0) + 0.6 * u_val
        y_val = 1 if (1.0 / (1.0 + np.exp(-y_latent))) > 0.5 else 0

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(y_val),
                d_qid: str(d_val),
                z_qid: str(round(z_val, 2)),
                x_qid: str(round(x_val, 2))
            },
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code == 201

    # 6. Call 2SRI / Control Function endpoint
    res_2sri = client.post(f"/api/surveys/{survey_id}/analytics/control-function-2sri", json={
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "instrument_question_ids": [z_qid],
        "covariate_question_ids": [x_qid],
        "outcome_family": "logistic",
        "n_bootstraps": 20,
        "scope": "all"
    })

    assert res_2sri.status_code == 200
    data = res_2sri.json()

    assert data["status"] == "success"
    assert data["sample_size"] == N
    assert data["outcome_family"] == "logistic"
    assert "first_stage" in data
    assert data["first_stage"]["f_statistic"] > 0
    assert "endogeneity_test" in data
    assert "causal_effects" in data
    assert "ate" in data["causal_effects"]
    assert "att" in data["causal_effects"]
    assert len(data["model_comparison"]) == 3
    assert "<svg" in data["svg_visualization"]
    assert "Two-Stage Residual Inclusion" in data["apa_narrative"]
