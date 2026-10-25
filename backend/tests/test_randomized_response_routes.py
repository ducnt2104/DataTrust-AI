"""
Route tests for Randomized Response Technique (RRT) & Crosswise Endpoint
(POST /api/surveys/{survey_id}/analytics/randomized-response)
DataTrust Iteration 193
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_randomized_response_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Sensitive Trait & Fraud Prevalence Evaluation",
        "description": "Crosswise model and Randomized Response estimation for sensitive questions"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: RRT Item, Direct Question Item
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Sensitive Trait & Fraud Prevalence Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Crosswise Response Item (0/1)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Direct Question Benchmark (0/1)", "is_required": True},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    q_map = {q["title"]: q["id"] for q in detail_res.json()["questions"]}
    q_rrt = q_map["Crosswise Response Item (0/1)"]
    q_dir = q_map["Direct Question Benchmark (0/1)"]

    # 4. Generate 50 responses
    np.random.seed(193)
    now = datetime.now(timezone.utc)
    N = 50
    p_rand = 0.70
    true_pi = 0.35

    for i in range(N):
        latent = 1 if np.random.uniform() < true_pi else 0
        aux = 1 if np.random.uniform() < p_rand else 0
        rrt_val = 1 if (latent == aux) else 0
        # Direct questioning: severe under-reporting (only 10% report truthfully)
        dir_val = 1 if (latent == 1 and np.random.uniform() < 0.25) else 0

        answers = {
            q_rrt: str(rrt_val),
            q_dir: str(dir_val),
        }

        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers,
            "started_at": (now - timedelta(minutes=10, seconds=i * 5)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 5)).isoformat(),
            "client_metadata": {"device_id": f"device_{i}"}
        })
        assert resp.status_code in (200, 201)

    # 5. Call endpoint
    eval_res = client.post(
        f"/api/surveys/{survey_id}/analytics/randomized-response",
        json={
            "rrt_question_id": q_rrt,
            "direct_question_id": q_dir,
            "model_type": "crosswise",
            "p_randomizer": 0.70,
            "alpha": 0.05,
            "scope": "all"
        }
    )
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 50
    assert data["model_type"] == "crosswise"
    assert 0.0 <= data["estimated_prevalence"] <= 1.0
    assert data["std_error"] > 0
    assert len(data["ci_95"]) == 2

    # Social desirability diagnostics
    sdb = data["social_desirability_diagnostics"]
    assert sdb is not None
    assert "direct_prevalence" in sdb
    assert "sdb_gap_percentage_points" in sdb

    # Visualization & APA narrative
    assert "svg_visualization" in data
    assert len(data["svg_visualization"]) > 100
    assert len(data["apa_narrative"]) > 50


def test_randomized_response_not_found():
    res = client.post("/api/surveys/non-existent-survey/analytics/randomized-response", json={
        "rrt_question_id": "q1",
        "model_type": "crosswise",
        "p_randomizer": 0.70
    })
    assert res.status_code == 404
