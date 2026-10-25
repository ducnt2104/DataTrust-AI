"""
Route tests for Mixed-Effects Location Scale Models (MELSM) Endpoint
(POST /api/surveys/{survey_id}/analytics/melsm)
DataTrust Iteration 194
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_melsm_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Repeated Longitudinal Experience & Volatility Study",
        "description": "Evaluation of within-subject variance heterogeneity and response stability using MELSM"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Subject ID, Outcome, Time Index (Location Covariate), Task Complexity (Scale Covariate)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Repeated Longitudinal Experience & Volatility Study",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Subject ID", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Outcome Score", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Time Index", "is_required": False},
            {"order_index": 3, "question_type": "number", "title": "Task Complexity", "is_required": False},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    q_map = {q["title"]: q["id"] for q in detail_res.json()["questions"]}
    q_subj = q_map["Subject ID"]
    q_out = q_map["Outcome Score"]
    q_time = q_map["Time Index"]
    q_comp = q_map["Task Complexity"]

    # 4. Generate 40 responses (10 subjects, 4 measurements each)
    np.random.seed(194)
    now = datetime.now(timezone.utc)
    N_subj = 10
    n_per_subj = 4
    total_idx = 0

    for i in range(N_subj):
        subj_name = f"User_{i + 1}"
        u_i = float(np.random.normal(0, 1.5))
        om_i = float(np.random.normal(0, 0.6))
        for t in range(n_per_subj):
            total_idx += 1
            compl = float(np.random.choice([1.0, 2.0, 3.0]))
            err_sd = np.sqrt(np.exp(om_i + 0.3 * compl))
            y_val = 8.0 + u_i + 0.4 * t + float(np.random.normal(0, err_sd))

            answers = {
                q_subj: subj_name,
                q_out: str(round(y_val, 2)),
                q_time: str(t),
                q_comp: str(compl),
            }

            resp = client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": answers,
                "started_at": (now - timedelta(minutes=10, seconds=total_idx * 5)).isoformat(),
                "submitted_at": (now - timedelta(seconds=total_idx * 5)).isoformat(),
                "client_metadata": {"device_id": f"device_usr_{i}_rep_{t}"}
            })
            assert resp.status_code in (200, 201)

    # 5. Call MELSM endpoint
    eval_res = client.post(
        f"/api/surveys/{survey_id}/analytics/melsm",
        json={
            "subject_question_id": q_subj,
            "outcome_question_id": q_out,
            "location_covariate_ids": [q_time],
            "scale_covariate_ids": [q_comp],
            "alpha": 0.05,
            "scope": "all"
        }
    )
    assert eval_res.status_code == 200
    data = eval_res.json()

    assert data["status"] == "success"
    assert data["sample_size_total"] == 40
    assert data["sample_size_subjects"] == 10

    # Fixed effects tables
    assert len(data["location_fixed_effects"]) == 2  # Intercept and Time Index
    assert len(data["scale_fixed_effects"]) == 2     # Intercept and Task Complexity

    # Variance components
    vc = data["random_effects_variance_components"]
    assert vc["between_subject_mean_sd_sigma_u"] > 0
    assert vc["between_subject_scale_sd_sigma_omega"] > 0
    assert -1.0 <= vc["location_scale_correlation_rho"] <= 1.0

    # Scale heterogeneity test
    lrt = data["scale_heterogeneity_test"]
    assert lrt["lrt_statistic"] >= 0
    assert lrt["degrees_of_freedom"] == 2
    assert "heterogeneity_significant" in lrt

    # Subject typology
    typ = data["subject_consistency_typology"]
    assert typ is not None
    assert sum(typ.values()) == 10

    # SVG chart and APA narrative
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
    assert "Panel A:" in data["svg_visualization"]
    assert "Panel B:" in data["svg_visualization"]
    assert "Hedeker" in data["apa_narrative"]


def test_melsm_not_found():
    res = client.post("/api/surveys/non-existent-survey/analytics/melsm", json={
        "subject_question_id": "q_sub",
        "outcome_question_id": "q_y",
    })
    assert res.status_code == 404
