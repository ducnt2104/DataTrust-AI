"""
Route tests for Difference-in-Discontinuities Endpoint
(POST /api/surveys/{survey_id}/analytics/diff-in-discontinuities)
DataTrust Iteration 174
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_diff_in_disc_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Municipal Population Grant & Diff-in-Disc Study",
        "description": "Difference-in-Discontinuities evaluation (Grembi et al. 2016 AER)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: running variable, period, outcome, unit
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Municipal Population Grant & Diff-in-Disc Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Municipal Population Score (Cutoff 50)", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Policy Period (0=Pre, 1=Post)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Municipal Fiscal Investment (Outcome)", "is_required": True},
            {"order_index": 3, "question_type": "text", "title": "City Identifier", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    run_qid = questions[0]["id"]
    per_qid = questions[1]["id"]
    out_qid = questions[2]["id"]
    city_qid = questions[3]["id"]

    # 4. Submit 60 responses: 30 cities across 2 periods (0 and 1)
    np.random.seed(123)
    cutoff = 50.0
    true_tau = 5.0
    true_gamma_0 = 3.0
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)

    for i in range(30):
        # 15 below cutoff, 15 above cutoff
        x_val = np.random.uniform(38, 49.5) if i < 15 else np.random.uniform(50.5, 62)
        x_c = x_val - cutoff
        d_val = 1 if x_val >= cutoff else 0
        u_fe = np.random.normal(0, 0.4)
        c_name = f"City_{i}"

        for t in [0, 1]:
            y_val = 20.0 + 0.3 * x_c + true_gamma_0 * d_val + 2.0 * t + true_tau * (d_val * t) + u_fe + np.random.normal(0, 0.3)
            sub_time = base_time + timedelta(minutes=(i * 2 + t))

            client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": {
                    run_qid: str(round(float(x_val), 2)),
                    per_qid: str(t),
                    out_qid: str(round(float(y_val), 2)),
                    city_qid: c_name
                },
                "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
                "submitted_at": sub_time.isoformat()
            })

    # 5. Call Diff-in-Disc analytics endpoint
    payload = {
        "running_question_id": run_qid,
        "cutoff": cutoff,
        "period_question_id": per_qid,
        "outcome_question_id": out_qid,
        "unit_question_id": city_qid,
        "post_period_val": "1",
        "bandwidth": 15.0,
        "kernel_type": "triangular",
        "alpha_level": 0.05,
        "scope": "all"
    }

    response = client.post(f"/api/surveys/{survey_id}/analytics/diff-in-discontinuities", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["sample_size_total"] == 60
    assert data["cutoff_threshold"] == cutoff
    assert "estimates" in data
    assert abs(data["estimates"]["diff_in_disc_tau"] - true_tau) < 1.0
    assert data["estimates"]["baseline_pre_jump_gamma0"] > 1.5
    assert "<svg" in data["svg_visualization"]
    assert "Grembi" in data["apa_narrative"]
