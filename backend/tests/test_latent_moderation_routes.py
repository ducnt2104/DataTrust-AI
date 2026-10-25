# -*- coding: utf-8 -*-
"""
Route integration tests for Latent Moderated Structural Equations (LMS / QML; Klein & Moosbrugger 2000)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_latent_moderation_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Organizational Leadership & Innovation Survey",
        "description": "Latent moderation of psychological safety on autonomy-innovation nexus"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: 2 predictor items, 2 moderator items, 2 outcome items
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Organizational Leadership & Innovation Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Autonomy Indicator 1 (X1)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Autonomy Indicator 2 (X2)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Safety Indicator 1 (M1)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Safety Indicator 2 (M2)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 4, "question_type": "number", "title": "Innovation Indicator 1 (Y1)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 5, "question_type": "number", "title": "Innovation Indicator 2 (Y2)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    x1_qid = q_objs[0]["id"]
    x2_qid = q_objs[1]["id"]
    m1_qid = q_objs[2]["id"]
    m2_qid = q_objs[3]["id"]
    y1_qid = q_objs[4]["id"]
    y2_qid = q_objs[5]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 35 responses
    now_time = datetime.now(timezone.utc)
    for i in range(35):
        # Latent values
        u_x = (i % 7) - 3.0
        u_m = (i % 5) - 2.0
        u_y = 0.6 * u_x + 0.4 * u_m + 0.35 * (u_x * u_m)

        answers_payload = {
            x1_qid: str(round(u_x + (i % 3) * 0.2, 2)),
            x2_qid: str(round(u_x * 0.9 + (i % 2) * 0.2, 2)),
            m1_qid: str(round(u_m + (i % 3) * 0.15, 2)),
            m2_qid: str(round(u_m * 0.85 + (i % 4) * 0.1, 2)),
            y1_qid: str(round(u_y + (i % 3) * 0.2, 2)),
            y2_qid: str(round(u_y * 0.9 + (i % 2) * 0.1, 2))
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

    # 5. Call /latent-moderation endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/latent-moderation",
        json={
            "predictor_item_ids": [x1_qid, x2_qid],
            "moderator_item_ids": [m1_qid, m2_qid],
            "outcome_item_ids": [y1_qid, y2_qid],
            "scope": "all"
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "LATENT_MODERATED_STRUCTURAL_EQUATIONS_LMS"
    assert data["diagnostics"]["sample_size"] == 35
    assert len(data["coefficients"]) == 3
    assert len(data["simple_slopes"]) == 3
    assert "<svg" in data["svg_visualization"]
    assert "Latent Moderated Structural Equations" in data["apa_narrative"]
