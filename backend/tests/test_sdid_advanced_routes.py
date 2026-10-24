# -*- coding: utf-8 -*-
"""
Route integration tests for Synthetic Difference-in-Differences (SDID) Advanced Engine
Arkhangelsky, Athey, Hirshberg, Imbens, & Wager (2021)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sdid_advanced_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Clean Energy Transition Regional Impact Survey (SDID)",
        "description": "Evaluating policy shocks via Synthetic Difference-in-Differences"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Y), Unit (U), Time (T), Treatment (W)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Clean Energy Transition Regional Impact Survey (SDID)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Chỉ số Sản lượng Công nghiệp (Output Index Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Mã Tỉnh / Thành phố (Region Unit ID)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Năm Khảo sát (Wave T: 1..5)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "single_choice",
                "title": "Áp dụng Cơ chế Thử nghiệm Năng lượng (Treatment W)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Khu vực áp dụng (Treated)"},
                    {"value": "0", "label": "Khu vực đối chứng (Control)"}
                ],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_u = questions[1]["id"]
    qid_t = questions[2]["id"]
    qid_w = questions[3]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit 30 panel observations (6 units x 5 waves)
    # Units 0..4: Control (W=0)
    # Unit 5: Treated at waves 4 and 5 (W=1)
    np.random.seed(42)
    now_time = datetime.now(timezone.utc)
    resp_idx = 0

    for u in range(6):
        u_base = 50.0 + u * 5.0
        for t in [1.0, 2.0, 3.0, 4.0, 5.0]:
            t_trend = 3.0 * t
            is_treated = (u == 5 and t >= 4.0)
            tau = 6.0 if is_treated else 0.0
            noise = float(np.random.normal(0, 0.2))
            y = round(u_base + t_trend + tau + noise, 2)
            w = "1" if is_treated else "0"

            started = (now_time - timedelta(minutes=90 - resp_idx)).isoformat()
            submitted = (now_time - timedelta(minutes=85 - resp_idx)).isoformat()
            resp_idx += 1

            resp = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": {
                        qid_y: y,
                        qid_u: float(u + 10),
                        qid_t: t,
                        qid_w: w
                    },
                    "started_at": started,
                    "submitted_at": submitted
                }
            )
            assert resp.status_code == 201

    # 4. Call SDID Advanced route
    sdid_res = client.post(f"/api/surveys/{survey_id}/analytics/sdid-advanced", json={
        "outcome_question_id": qid_y,
        "unit_question_id": qid_u,
        "time_question_id": qid_t,
        "treatment_question_id": qid_w,
        "scope": "all"
    })
    assert sdid_res.status_code == 200
    data = sdid_res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "SYNTHETIC_DID_ARKHANGELSKY_2021"
    diag = data["diagnostics"]
    assert diag["n_units"] == 6
    assert diag["n_treated_units"] == 1
    assert diag["n_control_units"] == 5
    assert diag["n_time_periods"] == 5
    assert diag["n_pre_periods"] == 3
    assert diag["n_post_periods"] == 2
    assert "tau_sdid" in diag
    assert "unit_weights" in data
    assert len(data["unit_weights"]) == 5
    assert "time_weights" in data
    assert len(data["time_weights"]) == 3
    assert "trajectories" in data
    assert len(data["trajectories"]) == 5
    assert "<svg" in data["svg_visualization"]
    assert "Arkhangelsky, Athey, Hirshberg, Imbens, & Wager, 2021" in data["apa_narrative"]


def test_sdid_advanced_routes_insufficient_sample():
    create_res = client.post("/api/surveys", json={
        "title": "Small SDID Survey",
        "description": "Insufficient test"
    })
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Small SDID Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Y", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "U", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "T", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "W", "is_required": True, "options": [], "logic_rules": []}
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

    res = client.post(f"/api/surveys/{survey_id}/analytics/sdid-advanced", json={
        "outcome_question_id": questions[0]["id"],
        "unit_question_id": questions[1]["id"],
        "time_question_id": questions[2]["id"],
        "treatment_question_id": questions[3]["id"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INSUFFICIENT_SAMPLE"
    assert "tối thiểu 20 quan sát" in data["message"]
