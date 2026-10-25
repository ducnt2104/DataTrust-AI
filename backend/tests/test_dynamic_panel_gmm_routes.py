# -*- coding: utf-8 -*-
"""
Route tests for Dynamic Panel System & Difference GMM Endpoint.
(POST /api/surveys/{survey_id}/analytics/dynamic-panel-gmm)
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_dynamic_panel_gmm_route_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Longitudinal Panel Survey",
        "description": "Multi-wave panel study for dynamic GMM estimation"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Longitudinal Panel Survey",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Unit Identifier", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Time Wave", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Satisfaction Score", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Feature Usage Hours", "is_required": True}
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    q_unit = questions[0]["id"]
    q_wave = questions[1]["id"]
    q_y = questions[2]["id"]
    q_x = questions[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 25 units x 4 waves of panel responses
    from datetime import datetime, timezone, timedelta
    now_time = datetime.now(timezone.utc)
    rng = np.random.RandomState(123)
    for i in range(25):
        uid = f"PANEL_USER_{i+1:03d}"
        y_prev = rng.normal(0, 1.0)
        u_i = rng.normal(0, 0.8)
        for t in range(1, 5):
            x_val = float(rng.normal(2.0, 0.5))
            eps = float(rng.normal(0, 0.3))
            y_val = float(0.45 * y_prev + 0.65 * x_val + u_i + eps)
            y_prev = y_val

            sub_res = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": {
                        q_unit: uid,
                        q_wave: str(t),
                        q_y: str(round(y_val, 3)),
                        q_x: str(round(x_val, 3))
                    },
                    "started_at": (now_time - timedelta(minutes=10)).isoformat(),
                    "submitted_at": now_time.isoformat()
                }
            )
            assert sub_res.status_code in [200, 201]

    # 5. Call System GMM Endpoint
    payload_system = {
        "unit_id_question_id": q_unit,
        "time_question_id": q_wave,
        "outcome_question_id": q_y,
        "covariate_question_ids": [q_x],
        "method": "system",
        "two_step": True,
        "windmeijer_correction": True,
        "scope": "all"
    }

    gmm_res = client.post(f"/api/surveys/{survey_id}/analytics/dynamic-panel-gmm", json=payload_system)
    assert gmm_res.status_code == 200
    data = gmm_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "DYNAMIC_PANEL_SYSTEM_GMM"
    assert data["diagnostics"]["num_panel_units"] == 25
    assert data["diagnostics"]["time_waves"] == 4
    assert len(data["parameters"]) == 2
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]

    # 6. Call Difference GMM Endpoint
    payload_diff = {
        "unit_id_question_id": q_unit,
        "time_question_id": q_wave,
        "outcome_question_id": q_y,
        "covariate_question_ids": [q_x],
        "method": "difference",
        "two_step": False,
        "windmeijer_correction": False,
        "scope": "all"
    }
    diff_res = client.post(f"/api/surveys/{survey_id}/analytics/dynamic-panel-gmm", json=payload_diff)
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert diff_data["status"] == "SUCCESS"
    assert diff_data["model_type"] == "DYNAMIC_PANEL_DIFFERENCE_GMM"

    # 7. Test 404 for nonexistent survey
    err_res = client.post("/api/surveys/nonexistent-survey-id/analytics/dynamic-panel-gmm", json=payload_system)
    assert err_res.status_code == 404

    # 8. Verify audit log entry
    with get_db() as conn:
        logs = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'DYNAMIC_PANEL_GMM_EVALUATED'",
            (survey_id,)
        ).fetchall()
        assert len(logs) >= 2
