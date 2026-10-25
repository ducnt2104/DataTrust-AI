"""
Route tests for Discrete RDD with Honest Bounds & Heaping Endpoint
(POST /api/surveys/{survey_id}/analytics/discrete-rd-heaping)
DataTrust Iteration 189
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_discrete_rd_heaping_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Discrete RDD Evaluation",
        "description": "Regression Discontinuity with discrete score and focal rounding"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Running variable X and Outcome Y
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Discrete RDD Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Diem Danh Gia Dau Vao (X)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Ket Qua Tot Nghiep (Y)", "is_required": True},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    q_map = {q["title"]: q["id"] for q in detail_res.json()["questions"]}
    q_x = q_map["Diem Danh Gia Dau Vao (X)"]
    q_y = q_map["Ket Qua Tot Nghiep (Y)"]

    # 4. Submit 50 synthetic responses
    # Cutoff at 50.0. Discrete scores between 30 and 70 with heaping at 40, 50, 60
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    for i in range(50):
        # Base discrete score
        base = 35 + (i % 31)
        # 30% rounding to nearest 5
        if i % 3 == 0:
            x_val = float(round(base / 5.0) * 5)
        else:
            x_val = float(base)

        d_val = 1.0 if x_val >= 50.0 else 0.0
        y_val = 60.0 + 0.5 * (x_val - 50.0) + 8.0 * d_val + float(np.random.normal(0, 1.5))

        answers = {
            q_x: str(int(x_val)),
            q_y: str(round(y_val, 2)),
        }

        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers,
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat(),
        })
        assert resp.status_code == 201, resp.text

    # 5. Execute Discrete RDD endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/discrete-rd-heaping",
        json={
            "running_question_id": q_x,
            "outcome_question_id": q_y,
            "cutoff": 50.0,
            "bandwidth": 15.0,
            "kernel": "triangular",
            "focal_rounding_interval": 5.0,
            "n_permutations": 100,
            "scope": "all",
        }
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == 50
    assert data["cutoff"] == 50.0

    # Diagnostics
    diag = data["discreteness_diagnostics"]
    assert diag["is_discrete"]
    assert "heaping_ratio" in diag

    # Conventional RDD
    assert data["conventional_rdd"]["tau_estimate"] > 4.0
    assert data["conventional_rdd"]["is_significant"]

    # Honest bounds
    honest = data["kolesar_rothe_honest_bounds"]
    assert len(honest) >= 3

    # Donut hole & Local Randomization
    assert "tau_donut" in data["donut_hole_diagnostics"]
    assert "fisher_exact_p_value" in data["local_randomization_inference"]

    # SVG & Narrative
    assert "<svg" in data["svg_visualization"]
    assert "Kolesár & Rothe, 2018" in data["apa_narrative"]


def test_discrete_rd_heaping_not_found():
    res = client.post(
        "/api/surveys/non-existent-survey-uuid/analytics/discrete-rd-heaping",
        json={
            "running_question_id": "dummy_x",
            "outcome_question_id": "dummy_y",
            "cutoff": 0.0,
        }
    )
    assert res.status_code == 404
