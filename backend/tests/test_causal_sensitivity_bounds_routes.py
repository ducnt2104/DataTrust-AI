"""
Route tests for Causal Sensitivity Bounds Endpoint
(POST /api/surveys/{survey_id}/analytics/causal-sensitivity-bounds)
DataTrust Iteration 177
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_causal_sensitivity_bounds_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Causal Sensitivity & Confounder Tolerance Study",
        "description": "Evaluation of causal robustness against unmeasured confounding (Cinelli & Hazlett 2020)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: treatment, outcome, cov1, cov2
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Causal Sensitivity & Confounder Tolerance Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Chương trình can thiệp (1=Có, 0=Không)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Điểm hiệu suất công việc (Outcome Y)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Kỹ năng chuyên môn ban đầu (X1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Số năm kinh nghiệm làm việc (X2)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    d_qid = questions[0]["id"]
    y_qid = questions[1]["id"]
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]

    # 4. Submit 60 responses
    np.random.seed(42)
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)

    for i in range(60):
        x1 = float(np.random.normal(10, 2))
        x2 = float(np.random.normal(5, 1.5))
        d = 1.0 if (0.3 * x1 + 0.2 * x2 + np.random.normal(0, 0.5) > 4.0) else 0.0
        y = float(3.5 * d + 1.2 * x1 + 0.8 * x2 + np.random.normal(0, 0.8))

        sub_time = base_time + timedelta(minutes=i * 2)
        sub_resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                d_qid: str(d),
                y_qid: str(round(y, 2)),
                x1_qid: str(round(x1, 2)),
                x2_qid: str(round(x2, 2))
            },
            "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
            "submitted_at": sub_time.isoformat()
        })
        assert sub_resp.status_code in (200, 201), sub_resp.text

    # 5. Call Causal Sensitivity Bounds Endpoint
    payload = {
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "alpha_level": 0.05,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/causal-sensitivity-bounds", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == 60
    assert "baseline_estimates" in data
    assert data["baseline_estimates"]["tau_hat"] > 0
    assert "robustness_values" in data
    assert "rv_q_to_zero" in data["robustness_values"]
    assert "covariate_benchmarks" in data
    assert len(data["covariate_benchmarks"]) == 2
    assert "worst_case_curve" in data
    assert "<svg" in data["svg_visualization"]
    assert "Cinelli & Hazlett" in data["apa_narrative"]
