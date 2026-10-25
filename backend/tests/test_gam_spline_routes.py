# -*- coding: utf-8 -*-
"""
Route integration tests for Generalized Additive Models (GAM) & Penalized Spline Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_gam_spline_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Employee Engagement & Weekly Work Hours Survey",
        "description": "Non-linear GAM Spline curve of burnout and productivity saturation"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Predictor X (Weekly Hours), Outcome Y (Productivity / Score), Covariate Z (Tenure)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Employee Engagement & Weekly Work Hours Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Weekly Work Hours (X)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Self-Rated Productivity Score (Y)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Company Tenure (Years)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    x_qid = q_objs[0]["id"]
    y_qid = q_objs[1]["id"]
    z_qid = q_objs[2]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses with non-linear inverted-U dynamics
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        hours = 20.0 + (i % 10) * 4.0  # 20 to 56 hours
        tenure = 1.0 + (i % 5) * 1.5
        # Inverted-U: productivity peaks around 40 hours
        prod = 50.0 + 3.0 * hours - 0.04 * (hours ** 2) + 0.5 * tenure

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    x_qid: str(round(hours, 1)),
                    y_qid: str(round(prod, 1)),
                    z_qid: str(round(tenure, 1))
                },
                "started_at": (now_time - timedelta(minutes=65 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=64 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call POST /gam-spline
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/gam-spline",
        json={
            "predictor_question_id": x_qid,
            "outcome_question_id": y_qid,
            "covariate_question_ids": [z_qid],
            "n_knots": 8,
            "grid_points": 40,
            "scope": "all"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "GENERALIZED_ADDITIVE_MODEL_SPLINE"
    assert "diagnostics" in data
    assert "smooth_curve" in data
    assert len(data["smooth_curve"]) == 40
    assert "svg_visualization" in data
    assert "<svg" in data["svg_visualization"]
    assert "apa_narrative" in data
