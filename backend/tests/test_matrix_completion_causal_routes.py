# -*- coding: utf-8 -*-
"""
Route integration tests for Matrix Completion for Causal Panel Data Engine
Athey, Bayati, Doudchenko, Imbens, & Khosravi (2021)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_matrix_completion_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Hospital Capacity & Patient Care Quality Panel (Matrix Completion)",
        "description": "Evaluating dynamic health intervention rollout via low-rank matrix imputation"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Y), Unit (U), Time (T), Treatment (W)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Hospital Capacity & Patient Care Quality Panel (Matrix Completion)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Chỉ số Chất lượng Điều trị (Quality Score Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Mã Bệnh viện / Cơ sở Y tế (Unit ID)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Tháng Quan sát (Wave T: 1..5)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "single_choice",
                "title": "Áp dụng Quy trình Chăm sóc Mới (Treatment W)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Đang can thiệp (Treated)"},
                    {"value": "0", "label": "Tiêu chuẩn (Control)"}
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
    # Units 0..3: always W = 0
    # Units 4..5: treated at waves 4 and 5 (W = 1)
    np.random.seed(42)
    now_time = datetime.now(timezone.utc)
    resp_idx = 0

    for u in range(6):
        u_base = 20.0 + u * 4.0
        for t in [1.0, 2.0, 3.0, 4.0, 5.0]:
            t_trend = 2.5 * t
            # True treatment effect +5.0
            is_treated = (u >= 4 and t >= 4.0)
            tau = 5.0 if is_treated else 0.0
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
                        qid_u: float(u + 1),
                        qid_t: t,
                        qid_w: w
                    },
                    "started_at": started,
                    "submitted_at": submitted
                }
            )
            assert resp.status_code == 201

    # 4. Call Matrix Completion route
    mc_res = client.post(f"/api/surveys/{survey_id}/analytics/matrix-completion-causal", json={
        "outcome_question_id": qid_y,
        "unit_question_id": qid_u,
        "time_question_id": qid_t,
        "treatment_question_id": qid_w,
        "max_rank": 2,
        "scope": "all"
    })
    assert mc_res.status_code == 200
    data = mc_res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "CAUSAL_MATRIX_COMPLETION_ATHEY_2021"
    diag = data["diagnostics"]
    assert diag["n_units"] == 6
    assert diag["n_time_periods"] == 5
    assert diag["n_treated_cells"] == 4
    assert diag["n_control_cells"] == 26
    assert diag["effective_rank"] >= 1
    assert "overall_att" in diag
    assert "cell_treatment_effects" in data
    assert len(data["cell_treatment_effects"]) == 4
    assert "singular_value_spectrum" in data
    assert "<svg" in data["svg_visualization"]
    assert "Athey, Bayati, Doudchenko, Imbens, & Khosravi, 2021" in data["apa_narrative"]


def test_matrix_completion_routes_insufficient_sample():
    create_res = client.post("/api/surveys", json={
        "title": "Small MC Survey",
        "description": "Insufficient test"
    })
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Small MC Survey",
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

    res = client.post(f"/api/surveys/{survey_id}/analytics/matrix-completion-causal", json={
        "outcome_question_id": questions[0]["id"],
        "unit_question_id": questions[1]["id"],
        "time_question_id": questions[2]["id"],
        "treatment_question_id": questions[3]["id"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INSUFFICIENT_SAMPLE"
    assert "tối thiểu 20 quan sát" in data["message"]
