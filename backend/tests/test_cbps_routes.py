"""
Route tests for Covariate Balancing Propensity Score Endpoint
(POST /api/surveys/{survey_id}/analytics/cbps)
DataTrust Iteration 184
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_cbps_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust CBPS Causal Inference Survey",
        "description": "Evaluation of program effect with Covariate Balancing Propensity Score (Imai & Ratkovic 2014)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust CBPS Causal Inference Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Kết Quả Học Tập (Outcome Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Tham Gia Gia Sư (Treatment D: 1/0)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Điểm Đầu Vào (Covariate X1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Thu Nhập Hộ Gia Đình (Covariate X2)", "is_required": True}
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
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]

    # 5. Submit 50 observational responses
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    N = 50
    for i in range(N):
        x1 = float(np.random.normal(50.0, 10.0))
        x2 = float(np.random.normal(25.0, 5.0))
        prob_t = 1.0 / (1.0 + np.exp(-(0.05 * (x1 - 50.0) + 0.08 * (x2 - 25.0))))
        d = 1 if np.random.uniform(0, 1) < prob_t else 0
        y = float(60.0 + 7.5 * d + 0.3 * x1 + 0.4 * x2 + np.random.normal(0, 2.0))

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y, 2)),
                d_qid: str(d),
                x1_qid: str(round(x1, 2)),
                x2_qid: str(round(x2, 2))
            },
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code == 201

    # 6. Execute CBPS endpoint
    cbps_res = client.post(f"/api/surveys/{survey_id}/analytics/cbps", json={
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "method": "overidentified",
        "estimand": "ATE",
        "scope": "all"
    })

    assert cbps_res.status_code == 200
    data = cbps_res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == N
    assert data["treated_count"] > 0
    assert data["control_count"] > 0
    assert data["estimand"] == "ATE"

    assert "causal_effect" in data
    assert "effect" in data["causal_effect"]
    assert "se" in data["causal_effect"]
    assert "p_value" in data["causal_effect"]

    assert len(data["covariate_balance"]) == 2
    for b in data["covariate_balance"]:
        assert abs(b["smd_weighted"]) < 0.30
        assert abs(b["smd_weighted"]) < abs(b["smd_raw"])

    assert data["diagnostics"]["converged"] is True
    assert "hansen_j_stat" in data["diagnostics"]
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]
