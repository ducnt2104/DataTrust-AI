# -*- coding: utf-8 -*-
"""
Route integration tests for Zero-Inflated Count Models (ZIP & ZINB; Lambert 1992, Vuong 1989)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_zero_inflated_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Patient Healthcare Utilization Survey",
        "description": "Zero-inflated count regression on doctor visits and health risk"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Count DoctorVisits Y, Covariate HealthRisk X, Inflation Covariate UninsuredFlag Z
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Patient Healthcare Utilization Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Annual Doctor Visits Count (Y)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Chronic Health Risk Index (X)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Uninsured Indicator (Z)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    x_qid = q_objs[1]["id"]
    z_qid = q_objs[2]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 30 responses with excess zeros
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        risk = 1.0 + (i % 5) * 0.8
        uninsured = 1 if (i % 3 == 0) else 0

        # Excess zeros for uninsured respondents
        if uninsured == 1 and (i % 2 == 0):
            visits = 0
        else:
            visits = int(max(0, round(0.5 + 0.6 * risk + (i % 3))))

        answers_payload = {
            y_qid: str(visits),
            x_qid: str(round(risk, 2)),
            z_qid: str(uninsured)
        }

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_payload,
                "started_at": (now_time - timedelta(minutes=60 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=59 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call /zero-inflated endpoint (ZIP)
    res_zip = client.post(
        f"/api/surveys/{survey_id}/analytics/zero-inflated",
        json={
            "count_question_id": y_qid,
            "covariate_question_ids": [x_qid],
            "inflation_covariate_question_ids": [z_qid],
            "model_type": "ZIP",
            "scope": "all"
        }
    )

    assert res_zip.status_code == 200
    data_zip = res_zip.json()
    assert data_zip["status"] == "SUCCESS"
    assert data_zip["model_type"] == "ZERO_INFLATED_ZIP"
    assert data_zip["diagnostics"]["sample_size"] == 30
    assert len(data_zip["count_model_coefficients"]) == 2
    assert len(data_zip["inflation_model_coefficients"]) == 2
    assert "<svg" in data_zip["svg_visualization"]
    assert "Zero-Inflated" in data_zip["apa_narrative"]

    # 6. Call /zero-inflated endpoint (ZINB)
    res_zinb = client.post(
        f"/api/surveys/{survey_id}/analytics/zero-inflated",
        json={
            "count_question_id": y_qid,
            "covariate_question_ids": [x_qid],
            "model_type": "ZINB",
            "scope": "all"
        }
    )
    assert res_zinb.status_code == 200
    data_zinb = res_zinb.json()
    assert data_zinb["status"] == "SUCCESS"
    assert data_zinb["model_type"] == "ZERO_INFLATED_ZINB"
    assert data_zinb["diagnostics"]["dispersion_parameter_alpha"] is not None
