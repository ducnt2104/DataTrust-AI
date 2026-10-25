# -*- coding: utf-8 -*-
"""
Route tests for Nested Logit Structural Choice Endpoint.
(POST /api/surveys/{survey_id}/analytics/nested-logit)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_nested_logit_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Urban Commuter Modal Choice Survey",
        "description": "Nested Logit Structural Demand & Substitution Elasticities (McFadden 1978)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Choice (1/0), Mode, Nest, Commuter ID, Travel Time, Ticket Cost
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Urban Commuter Modal Choice Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Choice Selected (1/0)", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Transport Mode", "is_required": True},
            {"order_index": 2, "question_type": "text", "title": "Nest Group", "is_required": True},
            {"order_index": 3, "question_type": "text", "title": "Commuter ID", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Travel Time (mins)", "is_required": True},
            {"order_index": 5, "question_type": "number", "title": "Cost (USD)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    c_qid = questions[0]["id"]
    m_qid = questions[1]["id"]
    n_qid = questions[2]["id"]
    id_qid = questions[3]["id"]
    time_qid = questions[4]["id"]
    cost_qid = questions[5]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 25 choice situations (each with 3 alternatives = 75 rows)
    np.random.seed(66)
    now = datetime.now(timezone.utc)
    modes = ["Private_Car", "Rapid_Bus", "Metro_Train"]
    nest_map = {"Private_Car": "Private", "Rapid_Bus": "Public", "Metro_Train": "Public"}

    for i in range(25):
        cid = f"commuter_{i}"
        eps_pub = np.random.normal(0, 1.2)
        v_scores = {}

        for m in modes:
            cost_val = 12.0 if m == "Private_Car" else (4.0 if m == "Rapid_Bus" else 5.0)
            time_val = 20.0 if m == "Private_Car" else (40.0 if m == "Rapid_Bus" else 30.0)
            v_det = -0.1 * cost_val - 0.05 * time_val
            eps = eps_pub + np.random.normal(0, 0.3) if nest_map[m] == "Public" else np.random.normal(0, 0.9)
            v_scores[m] = (cost_val, time_val, v_det + eps)

        chosen_m = max(v_scores.keys(), key=lambda k: v_scores[k][2])

        for m in modes:
            cost_val, time_val, _ = v_scores[m]
            is_chosen = 1.0 if m == chosen_m else 0.0
            answers_dict = {
                c_qid: str(int(is_chosen)),
                m_qid: m,
                n_qid: nest_map[m],
                id_qid: cid,
                time_qid: str(time_val),
                cost_qid: str(cost_val)
            }
            resp = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": answers_dict,
                    "started_at": (now - timedelta(minutes=2)).isoformat(),
                    "submitted_at": now.isoformat()
                }
            )
            assert resp.status_code in [200, 201]

    # 5. Call nested-logit endpoint
    nl_res = client.post(
        f"/api/surveys/{survey_id}/analytics/nested-logit",
        json={
            "choice_question_id": c_qid,
            "alternative_question_id": m_qid,
            "nest_question_id": n_qid,
            "choice_id_question_id": id_qid,
            "attribute_question_ids": [time_qid],
            "cost_question_id": cost_qid,
            "alpha_level": 0.05,
            "scope": "all"
        }
    )
    assert nl_res.status_code == 200
    res_data = nl_res.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["overall_summary"]["n_choice_situations"] == 25
    assert res_data["overall_summary"]["n_alternatives"] == 3
    assert res_data["overall_summary"]["n_nests"] == 2
    assert len(res_data["nests"]) == 2
    assert len(res_data["coefficients"]) >= 2
    assert "<svg" in res_data["svg_visualization"]
    assert "Nested Logit" in res_data["apa_narrative"]
