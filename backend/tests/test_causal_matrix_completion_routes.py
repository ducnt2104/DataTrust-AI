"""
Route tests for Causal Matrix Completion Endpoint
(POST /api/surveys/{survey_id}/analytics/causal-matrix-completion)
DataTrust Iteration 178
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_causal_matrix_completion_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Causal Matrix Completion Panel Survey",
        "description": "Evaluation of staggered technology adoption across enterprise branches (Athey et al. 2021)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: unit, period, outcome, treatment
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Causal Matrix Completion Panel Survey",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Chi nhánh / Đơn vị", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Năm Khảo sát", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Chỉ số Hiệu suất Vận hành", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Chính sách Số hóa (1=Có, 0=Chưa)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    unit_qid = questions[0]["id"]
    period_qid = questions[1]["id"]
    outcome_qid = questions[2]["id"]
    treatment_qid = questions[3]["id"]

    # 4. Submit responses across 6 units x 4 periods
    np.random.seed(42)
    units = [f"Branch_{i}" for i in range(1, 7)]
    periods = ["2021", "2022", "2023", "2024"]
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    obs_idx = 0

    for i, u in enumerate(units):
        for t, p in enumerate(periods):
            # Staggered adoption: units 3, 4 adopt in 2023; units 5, 6 adopt in 2024
            is_treated = False
            if i in [2, 3] and t >= 2:
                is_treated = True
            elif i in [4, 5] and t >= 3:
                is_treated = True

            effect = 4.5 if is_treated else 0.0
            for _ in range(4):
                obs_idx += 1
                baseline = (i + 1) * 2.0 + (t + 1) * 1.5
                y = baseline + effect + float(np.random.normal(0, 0.4))
                sub_time = base_time + timedelta(minutes=obs_idx * 2)

                sub_resp = client.post(f"/api/public/surveys/{slug}/submit", json={
                    "answers": {
                        unit_qid: u,
                        period_qid: p,
                        outcome_qid: str(round(y, 2)),
                        treatment_qid: "1.0" if is_treated else "0.0"
                    },
                    "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
                    "submitted_at": sub_time.isoformat()
                })
                assert sub_resp.status_code in (200, 201), sub_resp.text

    # 5. Call Causal Matrix Completion Endpoint
    payload = {
        "unit_question_id": unit_qid,
        "period_question_id": period_qid,
        "outcome_question_id": outcome_qid,
        "treatment_question_id": treatment_qid,
        "lambda_nuc": 0.2,
        "max_iter": 100,
        "tol": 1e-4,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/causal-matrix-completion", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert data["dimensions"]["units_count"] == 6
    assert data["dimensions"]["periods_count"] == 4
    assert data["estimates"]["att"] > 0
    assert "algorithm_convergence" in data
    assert "unit_heterogeneity" in data
    assert "event_study_trajectory" in data
    assert "<svg" in data["svg_visualization"]
    assert "Athey et al." in data["apa_narrative"]
