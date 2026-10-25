"""
Route tests for Conformal Causal Inference Endpoint
(POST /api/surveys/{survey_id}/analytics/conformal-causal)
DataTrust Iteration 180
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_conformal_causal_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Conformal Causal Inference Survey",
        "description": "Evaluation of job training policy with finite-sample distribution-free conformal bounds (Lei & Candes 2021)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: outcome, treatment, covariate
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Conformal Causal Inference Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Thu nhập Sau Đào tạo (Outcome Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Tham gia Đào tạo Kỹ năng (Treatment D: 1/0)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Năm kinh nghiệm làm việc (Covariate X1)", "is_required": False},
            {"order_index": 3, "question_type": "number", "title": "Điểm kỹ năng kiểm tra ban đầu (Covariate X2)", "is_required": False}
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

    # 5. Simulate 65 observations
    np.random.seed(42)
    n = 65
    now = datetime.now(timezone.utc)

    for i in range(n):
        x1_val = float(np.random.normal(5.0, 2.0))
        x2_val = float(np.random.normal(50.0, 10.0))
        d_val = 1 if (i % 2 == 0) else 0
        y_val = 15.0 + 1.2 * x1_val + 0.4 * x2_val + 6.0 * d_val + float(np.random.normal(0, 1.5))

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

    # 6. Execute Conformal Causal Inference endpoint
    payload = {
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "alpha": 0.05,
        "calibration_ratio": 0.4,
        "scope": "all"
    }

    eval_res = client.post(f"/api/surveys/{survey_id}/analytics/conformal-causal", json=payload)
    assert eval_res.status_code == 200
    data = eval_res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == 65
    assert data["nominal_coverage"] == 0.95
    assert data["empirical_calibration_coverage"] >= 0.70
    assert "subgroup_counts" in data
    assert "conformal_cutoffs" in data
    assert "treatment_effect_summary" in data
    assert data["treatment_effect_summary"]["ate_conformal"] > 2.0
    assert len(data["sample_ite_points"]) > 5
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]

    # 7. Test 404 for nonexistent survey
    fake_res = client.post("/api/surveys/nonexistent-uuid-999/analytics/conformal-causal", json=payload)
    assert fake_res.status_code == 404
