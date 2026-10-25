"""
Route tests for Bayesian Causal Forests Endpoint
(POST /api/surveys/{survey_id}/analytics/bayesian-causal-forest)
DataTrust Iteration 181
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_bayesian_causal_forest_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Bayesian Causal Forests Survey",
        "description": "Observational study of marketing intervention with targeted smooth propensity priors (Hahn et al. 2020)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: outcome, treatment, covariate
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Bayesian Causal Forests Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Chi tiêu Khách hàng (Outcome Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Chương trình Khách hàng Thân thiết (Treatment D: 1/0)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Điểm tích lũy lịch sử (Covariate X1)", "is_required": False},
            {"order_index": 3, "question_type": "number", "title": "Tần suất mua sắm hàng tháng (Covariate X2)", "is_required": False}
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

    # 5. Simulate 55 observations
    np.random.seed(42)
    n = 55
    now = datetime.now(timezone.utc)

    for i in range(n):
        x1_val = float(np.random.normal(50.0, 10.0))
        x2_val = float(np.random.normal(5.0, 1.5))
        d_val = 1 if (i % 2 == 0) else 0
        y_val = 100.0 + 1.5 * x1_val + 4.0 * x2_val + 12.0 * d_val + float(np.random.normal(0, 3.0))

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y_val, 2)),
                d_qid: str(d_val),
                x1_qid: str(round(x1_val, 2)),
                x2_qid: str(round(x2_val, 2))
            },
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code == 201

    # 6. Execute Bayesian Causal Forest endpoint
    payload = {
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "num_mcmc_draws": 150,
        "credibility_level": 0.95,
        "scope": "all"
    }

    eval_res = client.post(f"/api/surveys/{survey_id}/analytics/bayesian-causal-forest", json=payload)
    assert eval_res.status_code == 200
    data = eval_res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == 55
    assert data["mcmc_draws_count"] == 150
    assert "ate_estimates" in data
    assert data["ate_estimates"]["posterior_mean"] > 5.0
    assert "att_estimates" in data
    assert "mcmc_diagnostics" in data
    assert len(data["propensity_quintiles"]) == 5
    assert len(data["sample_cate_estimates"]) > 5
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]

    # 7. Test 404 for nonexistent survey
    fake_res = client.post("/api/surveys/nonexistent-uuid-999/analytics/bayesian-causal-forest", json=payload)
    assert fake_res.status_code == 404
