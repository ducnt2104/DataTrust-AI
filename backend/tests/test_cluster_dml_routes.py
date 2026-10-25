"""
Route tests for Cluster-DML Endpoint
(POST /api/surveys/{survey_id}/analytics/cluster-dml)
DataTrust Iteration 175
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_cluster_dml_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Hierarchical Organization Performance & Cluster-DML Study",
        "description": "Multiway Cluster-Robust Double Machine Learning (Chiang et al. 2022)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: cluster, treatment, outcome, cov1, cov2
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Hierarchical Organization Performance & Cluster-DML Study",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Business Department Cluster ID", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "AI Copilot Training Treatment (1=Yes, 0=No)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Quarterly Productivity Output (Outcome)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Employee Tech Affinity Score", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Years of Professional Tenure", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    c_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    y_qid = questions[2]["id"]
    x1_qid = questions[3]["id"]
    x2_qid = questions[4]["id"]

    # 4. Submit 60 responses across 6 departments (10 per department)
    np.random.seed(42)
    true_theta = 4.0
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    obs_idx = 0

    for c in range(6):
        dept_name = f"Dept_{c}"
        u_dept = np.random.normal(0, 1.0)
        for i in range(10):
            obs_idx += 1
            x1 = np.random.uniform(1, 10)
            x2 = np.random.uniform(0.5, 8.0)
            d = 1.0 if (0.3 * x1 + 0.2 * x2 + np.random.normal(0, 0.5) > 2.5) else 0.0
            y = true_theta * d + 1.2 * x1 + 0.8 * x2 + u_dept + np.random.normal(0, 0.4)
            sub_time = base_time + timedelta(minutes=obs_idx * 2)

            client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": {
                    c_qid: dept_name,
                    d_qid: str(d),
                    y_qid: str(round(float(y), 2)),
                    x1_qid: str(round(float(x1), 2)),
                    x2_qid: str(round(float(x2), 2))
                },
                "started_at": (sub_time - timedelta(minutes=2)).isoformat(),
                "submitted_at": sub_time.isoformat()
            })

    # 5. Call Cluster-DML analytics endpoint
    payload = {
        "cluster_question_id": c_qid,
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x1_qid, x2_qid],
        "n_splits": 3,
        "ml_model": "ridge",
        "alpha_level": 0.05,
        "scope": "all"
    }

    response = client.post(f"/api/surveys/{survey_id}/analytics/cluster-dml", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 60
    assert data["diagnostics"]["num_clusters"] == 6
    assert "estimates" in data
    assert abs(data["estimates"]["theta"] - true_theta) < 1.0
    assert data["estimates"]["se_cluster"] > 0
    assert "<svg" in data["svg_visualization"]
    assert "Chiang" in data["apa_narrative"]
