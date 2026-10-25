"""
Route tests for Distributional Synthetic Control Endpoint
(POST /api/surveys/{survey_id}/analytics/distributional-synthetic-control)
DataTrust Iteration 176
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_distributional_synthetic_control_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Distributional Synthetic Control Survey",
        "description": "Evaluation of regional policy intervention on full outcome distributions (Chernozhukov et al. 2021)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: unit, period, outcome
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Distributional Synthetic Control Survey",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Khu vực / Tỉnh thành Đơn vị", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Năm Khảo sát", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Điểm Chỉ số Phúc lợi / Thu nhập", "is_required": True}
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

    # 4. Submit responses across units and periods
    np.random.seed(101)
    units = ["Province_T", "Province_D1", "Province_D2", "Province_D3"]
    periods = ["2021", "2022", "2023"]
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    obs_idx = 0

    for period in periods:
        for u in units:
            for _ in range(10):
                obs_idx += 1
                if u == "Province_D1":
                    val = float(np.random.normal(12, 1.5))
                elif u == "Province_D2":
                    val = float(np.random.normal(18, 1.5))
                elif u == "Province_D3":
                    val = float(np.random.normal(30, 2.0))
                else:
                    # Treated unit
                    shift = 4.0 if period == "2023" else 0.0
                    val = float(np.random.normal(15, 1.5) + shift)

                sub_time = base_time + timedelta(minutes=obs_idx * 2)
                sub_resp = client.post(f"/api/public/surveys/{slug}/submit", json={
                    "answers": {
                        unit_qid: u,
                        period_qid: period,
                        outcome_qid: str(round(val, 2))
                    },
                    "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
                    "submitted_at": sub_time.isoformat()
                })
                assert sub_resp.status_code in (200, 201), sub_resp.text

    # 5. Call Distributional Synthetic Control Endpoint
    dsc_payload = {
        "unit_question_id": unit_qid,
        "period_question_id": period_qid,
        "outcome_question_id": outcome_qid,
        "treated_unit_val": "Province_T",
        "post_period_vals": ["2023"],
        "num_quantiles": 11,
        "num_placebos": 3,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/distributional-synthetic-control", json=dsc_payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert data["treated_unit"] == "Province_T"
    assert data["num_donors"] == 3
    assert "wasserstein_distance" in data
    assert "mean_treatment_effect" in data
    assert "median_treatment_effect" in data
    assert data["mean_treatment_effect"] > 0
    assert "inequality_diagnostics" in data
    assert "donor_weights" in data
    assert len(data["donor_weights"]) == 3
    assert len(data["quantile_curve"]) == 11
    assert "<svg" in data["svg_visualization"]
    assert "Chernozhukov et al." in data["apa_narrative"]
