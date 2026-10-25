"""
Route tests for Nonparametric IV-LATE Quantile Decomposition Endpoint
(POST /api/surveys/{survey_id}/analytics/iv-late-quantile)
DataTrust Iteration 179
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_iv_late_quantile_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust IV-LATE Quantile Decomposition Survey",
        "description": "Evaluation of educational subsidy on learning outcomes using lottery assignment (Abadie 2002; Frölich & Melly 2013)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: outcome, treatment, instrument, covariate
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust IV-LATE Quantile Decomposition Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Điểm số Đánh giá Năng lực (Outcome Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Tham gia Học bổ trợ (Treatment D: 1/0)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Trúng tuyển Học bổng Ngẫu nhiên (Instrument Z: 1/0)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Điểm kiểm tra đầu vào (Covariate X)", "is_required": False}
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
    z_qid = questions[2]["id"]
    x_qid = questions[3]["id"]

    # 5. Simulate 50 observations
    np.random.seed(42)
    n = 50
    now = datetime.now(timezone.utc)

    for i in range(n):
        z_val = 1 if (i % 2 == 0) else 0
        x_val = float(np.random.normal(50.0, 10.0))
        # Complier behavior: compliers take D if Z=1
        if i < 35: # compliers
            d_val = z_val
        else: # always-takers / never-takers
            d_val = 1 if (i % 4 == 0) else 0

        # Outcome with positive treatment effect
        y_val = 40.0 + 0.3 * x_val + 8.0 * d_val + float(np.random.normal(0, 2.0))

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y_val, 2)),
                d_qid: str(d_val),
                z_qid: str(z_val),
                x_qid: str(round(x_val, 2))
            },
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code == 201

    # 6. Execute IV-LATE Quantile Decomposition endpoint
    payload = {
        "outcome_question_id": y_qid,
        "treatment_question_id": d_qid,
        "instrument_question_id": z_qid,
        "covariate_question_ids": [x_qid],
        "num_quantiles": 15,
        "scope": "all"
    }

    eval_res = client.post(f"/api/surveys/{survey_id}/analytics/iv-late-quantile", json=payload)
    assert eval_res.status_code == 200
    data = eval_res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == 50
    assert data["complier_share"] > 0.3
    assert data["mean_late"] > 4.0
    assert "monotonicity_test" in data
    assert "complier_inequality" in data
    assert "quantile_curve" in data
    assert len(data["quantile_curve"]) > 5
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]

    # 7. Test 404 for nonexistent survey
    fake_res = client.post("/api/surveys/nonexistent-uuid-999/analytics/iv-late-quantile", json=payload)
    assert fake_res.status_code == 404
