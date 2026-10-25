# -*- coding: utf-8 -*-
"""
Route integration tests for Endogenous Switching Regression (ESR; Maddala 1983, Lokshin & Sajaia 2004)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_endogenous_switching_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Agricultural Modernization & Farmer Income Survey",
        "description": "ESR evaluation of smart farming tech adoption on household income"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Binary Treatment T, Outcome Income Y, Covariate LandSize X, Instrument ExtensionContact Z
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Agricultural Modernization & Farmer Income Survey",
        "questions": [
            {"order_index": 0, "question_type": "single_choice", "title": "Smart Tech Adopted (1=Yes, 0=No)", "is_required": True, "options": ["0", "1"], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Annual Net Farm Income (mil VND)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Farm Land Size (Hectares)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Agricultural Extension Contacts (Instrument Z)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    t_qid = q_objs[0]["id"]
    y_qid = q_objs[1]["id"]
    x_qid = q_objs[2]["id"]
    z_qid = q_objs[3]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 36 responses (~50% treated, ~50% untreated)
    now_time = datetime.now(timezone.utc)
    for i in range(36):
        land = 1.0 + (i % 6) * 0.5
        contacts = (i % 4)
        is_treated = 1 if (contacts >= 2 or (land > 2.5 and i % 2 == 0)) else 0

        # Outcome depending on regime
        if is_treated == 1:
            income = 50.0 + 15.0 * land + (i % 5) * 2.0
        else:
            income = 35.0 + 9.0 * land + (i % 4) * 1.5

        answers_payload = {
            t_qid: str(is_treated),
            y_qid: str(round(income, 1)),
            x_qid: str(round(land, 2)),
            z_qid: str(contacts)
        }

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_payload,
                "started_at": (now_time - timedelta(minutes=70 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=69 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call /endogenous-switching endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/endogenous-switching",
        json={
            "treatment_question_id": t_qid,
            "outcome_question_id": y_qid,
            "covariate_question_ids": [x_qid],
            "instrument_question_ids": [z_qid],
            "scope": "all"
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "ENDOGENOUS_SWITCHING_REGRESSION_FIML"
    assert data["diagnostics"]["total_sample"] == 36
    assert "att" in data["treatment_effects"]
    assert "atu" in data["treatment_effects"]
    assert len(data["coefficients"]) == 2
    assert "<svg" in data["svg_visualization"]
    assert "Endogenous Switching Regression" in data["apa_narrative"]
