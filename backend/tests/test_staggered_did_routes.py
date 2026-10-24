# -*- coding: utf-8 -*-
"""
Route integration tests for Staggered Difference-in-Differences Engine
Callaway & Sant'Anna (2021); Goodman-Bacon (2021)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_staggered_did_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Longitudinal Digital Transformation & Productivity Survey (Staggered DiD)",
        "description": "Evaluating dynamic rollout effects across enterprise cohorts"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Y), Unit (U), Time (T), Cohort Timing (G)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Longitudinal Digital Transformation & Productivity Survey (Staggered DiD)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Doanh thu biên hàng quý ($k)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Mã định danh doanh nghiệp (Unit ID)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Đợt khảo sát theo quý (Wave T: 1, 2, 3)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Quý bắt đầu triển khai giải pháp (Timing G: 0, 2, 3)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_u = questions[1]["id"]
    qid_t = questions[2]["id"]
    qid_g = questions[3]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit responses: 10 units x 3 waves = 30 responses
    # Units 0..3: never treated (g = 0)
    # Units 4..6: treated at t = 2 (g = 2)
    # Units 7..9: treated at t = 3 (g = 3)
    np.random.seed(101)
    now_time = datetime.now(timezone.utc)
    resp_idx = 0

    for u in range(10):
        if u < 4:
            g = 0.0
        elif u < 7:
            g = 2.0
        else:
            g = 3.0

        u_fe = 50.0 + (u * 3.0)
        for t in [1.0, 2.0, 3.0]:
            t_fe = 4.0 * t
            tau = 0.0
            if g > 0.0 and t >= g:
                tau = 10.0 + (t - g) * 2.0

            noise = float(np.random.normal(0, 0.4))
            y = round(u_fe + t_fe + tau + noise, 2)

            started = (now_time - timedelta(minutes=100 - resp_idx)).isoformat()
            submitted = (now_time - timedelta(minutes=95 - resp_idx)).isoformat()
            resp_idx += 1

            resp = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": {
                        qid_y: y,
                        qid_u: float(u + 100),
                        qid_t: t,
                        qid_g: g
                    },
                    "started_at": started,
                    "submitted_at": submitted
                }
            )
            assert resp.status_code == 201

    # 4. Call Staggered DiD route
    did_res = client.post(f"/api/surveys/{survey_id}/analytics/staggered-did", json={
        "outcome_question_id": qid_y,
        "unit_question_id": qid_u,
        "time_question_id": qid_t,
        "treatment_timing_question_id": qid_g,
        "control_group_type": "never_treated",
        "scope": "all"
    })
    assert did_res.status_code == 200
    data = did_res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "STAGGERED_DID_CALLAWAY_SANTANNA_2021"
    diag = data["diagnostics"]
    assert diag["n_observations"] == 30
    assert diag["n_units"] == 10
    assert diag["n_time_periods"] == 3
    assert diag["n_cohorts"] == 2
    assert diag["overall_att"] > 7.0
    assert diag["overall_p_value"] < 0.05
    assert diag["is_statistically_significant"] is True
    assert diag["parallel_trends_supported"] is True

    # Event study and decomposition
    assert len(data["group_time_effects"]) > 0
    assert len(data["event_study_effects"]) > 0
    assert data["bacon_decomposition"] is not None
    assert "<svg" in data["svg_visualization"]
    assert "Callaway & Sant'Anna, 2021" in data["apa_narrative"]


def test_staggered_did_routes_insufficient_sample():
    create_res = client.post("/api/surveys", json={
        "title": "Small DiD Survey",
        "description": "Sample test"
    })
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Small DiD Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Y", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "U", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "T", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "G", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    questions = put_res.json()["questions"]

    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    now_time = datetime.now(timezone.utc)
    for i in range(5):
        client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    questions[0]["id"]: float(10 + i),
                    questions[1]["id"]: float(i),
                    questions[2]["id"]: float(1),
                    questions[3]["id"]: float(0)
                },
                "started_at": (now_time - timedelta(minutes=10 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=8 - i)).isoformat()
            }
        )

    res = client.post(f"/api/surveys/{survey_id}/analytics/staggered-did", json={
        "outcome_question_id": questions[0]["id"],
        "unit_question_id": questions[1]["id"],
        "time_question_id": questions[2]["id"],
        "treatment_timing_question_id": questions[3]["id"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INSUFFICIENT_SAMPLE"
    assert "tối thiểu 20 quan sát" in data["message"]
