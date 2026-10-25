# -*- coding: utf-8 -*-
"""
Route integration tests for Generalized Propensity Score (GPS) Dose-Response (Hirano & Imbens 2004)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_gps_dose_response_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Corporate Training & Sales Performance Survey",
        "description": "Continuous dosage evaluation of training hours on quarterly sales"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Continuous Treatment T (Hours), Outcome Y (Sales), Covariates X1 (Experience), X2 (Education)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Corporate Training & Sales Performance Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Training Hours Received (T)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Quarterly Sales Revenue (mil VND)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Prior Sales Experience (Years)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Education Level (Years)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    t_qid = q_objs[0]["id"]
    y_qid = q_objs[1]["id"]
    x1_qid = q_objs[2]["id"]
    x2_qid = q_objs[3]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        exp = 1.0 + (i % 6) * 1.5
        edu = 12.0 + (i % 5)
        # Dose with confounding
        dose = 5.0 + 1.2 * exp + 0.5 * edu + (i % 4) * 1.0
        # Outcome with diminishing returns
        sales = 100.0 + 12.0 * dose - 0.3 * (dose ** 2) + 5.0 * exp

        answers_payload = {
            t_qid: str(round(dose, 1)),
            y_qid: str(round(sales, 1)),
            x1_qid: str(round(exp, 1)),
            x2_qid: str(round(edu, 1))
        }

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_payload,
                "started_at": (now_time - timedelta(minutes=65 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=64 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call /gps-dose-response endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/gps-dose-response",
        json={
            "treatment_question_id": t_qid,
            "outcome_question_id": y_qid,
            "covariate_question_ids": [x1_qid, x2_qid],
            "n_grid_points": 20,
            "scope": "all"
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "GENERALIZED_PROPENSITY_SCORE_DOSE_RESPONSE"
    assert data["diagnostics"]["sample_size"] == 30
    assert len(data["dose_response_curve"]) == 20
    assert len(data["marginal_effects_curve"]) == 20
    assert "<svg" in data["svg_visualization"]
    assert "Generalized Propensity Score" in data["apa_narrative"]
