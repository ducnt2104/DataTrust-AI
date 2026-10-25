"""
Route tests for Abadie (2003) Kappa-Weighting Complier Profiling & Compliance Typology Endpoint
(POST /api/surveys/{survey_id}/analytics/abadie-complier-profiling)
DataTrust Iteration 188
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_abadie_complier_profiling_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Abadie Complier Profiling Evaluation",
        "description": "Instrumental encouragement trial with Abadie kappa weighting"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: D (treatment), Z (instrument), X1 (age), X2 (experience), Y (productivity)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Abadie Complier Profiling Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Tham Gia Dao Tao (D)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Nhan Thu Khuyen Khich (Z)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Do Tuoi (X1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "So Nam Kinh Nghiem (X2)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Hieu Qua Cong Tac (Y)", "is_required": True},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    q_map = {q["title"]: q["id"] for q in detail_res.json()["questions"]}
    q_d = q_map["Tham Gia Dao Tao (D)"]
    q_z = q_map["Nhan Thu Khuyen Khich (Z)"]
    q_x1 = q_map["Do Tuoi (X1)"]
    q_x2 = q_map["So Nam Kinh Nghiem (X2)"]
    q_y = q_map["Hieu Qua Cong Tac (Y)"]

    # 4. Submit 40 synthetic responses
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    for i in range(40):
        # 50% randomized encouragement Z
        z_val = 1.0 if i % 2 == 0 else 0.0
        # Age & Experience
        x1_val = float(np.random.normal(35, 5))
        x2_val = float(np.random.normal(8, 3))
        # High experience respondents are compliers: D = Z
        # Low experience are never-takers: D = 0
        is_complier = x2_val > 7.0
        d_val = z_val if is_complier else 0.0
        # Outcome Y
        y_val = 50.0 + 1.2 * x2_val + 6.0 * d_val + float(np.random.normal(0, 1))

        answers = {
            q_d: str(int(d_val)),
            q_z: str(int(z_val)),
            q_x1: str(round(x1_val, 1)),
            q_x2: str(round(x2_val, 1)),
            q_y: str(round(y_val, 2)),
        }

        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers,
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat(),
        })
        assert resp.status_code == 201, resp.text

    # 5. Execute Abadie complier profiling endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/abadie-complier-profiling",
        json={
            "treatment_question_id": q_d,
            "instrument_question_id": q_z,
            "covariate_question_ids": [q_x1, q_x2],
            "outcome_question_id": q_y,
            "estimate_instrument_propensity": True,
            "n_bootstraps": 40,
            "scope": "all",
        }
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == 40

    # Typology
    typology = data["compliance_typology"]
    assert "p_compliers" in typology
    assert "p_always_takers" in typology
    assert "p_never_takers" in typology
    assert typology["p_compliers"] > 0

    # Feature profiles
    profiles = data["feature_profiles"]
    assert len(profiles) == 2
    for p in profiles:
        assert "feature_name" in p
        assert "relative_likelihood_ratio" in p
        assert "representation" in p

    # LATE effect
    assert data["late_causal_effect"] is not None
    assert "late_estimate" in data["late_causal_effect"]

    # SVG & Narrative
    assert "<svg" in data["svg_visualization"]
    assert "Abadie (2003)" in data["apa_narrative"]


def test_abadie_complier_profiling_not_found():
    res = client.post(
        "/api/surveys/non-existent-survey-uuid/analytics/abadie-complier-profiling",
        json={
            "treatment_question_id": "dummy_d",
            "instrument_question_id": "dummy_z",
            "covariate_question_ids": ["dummy_x"],
        }
    )
    assert res.status_code == 404
