# -*- coding: utf-8 -*-
"""
Route integration tests for Multiple Sequential Mediators Engine
VanderWeele (2014); Steen et al. (2012)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_multiple_mediators_route_success():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Organizational Leadership and Performance Mediation Survey",
        "description": "Sequential mediation paths from leadership styles to psychological safety, goal clarity, and employee performance"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Organizational Leadership and Performance Mediation Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Lãnh đạo Chuyển đổi (Transformational Leadership X)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "An toàn Tâm lý Đội nhóm (Psychological Safety M1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Sự rõ ràng Mục tiêu (Goal Clarity M2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Hiệu suất Công việc Cá nhân (Job Performance Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_x = questions[0]["id"]
    qid_m1 = questions[1]["id"]
    qid_m2 = questions[2]["id"]
    qid_y = questions[3]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit 40 simulated responses
    np.random.seed(42)
    now_time = datetime.now(timezone.utc)

    for i in range(40):
        x = float(np.random.normal(3.5, 0.8))
        m1 = float(1.2 + 0.5 * x + np.random.normal(0, 0.3))
        m2 = float(0.8 + 0.3 * x + 0.4 * m1 + np.random.normal(0, 0.3))
        y = float(1.5 + 0.4 * x + 0.5 * m1 + 0.6 * m2 + np.random.normal(0, 0.3))

        started = (now_time - timedelta(minutes=100 - i)).isoformat()
        submitted = (now_time - timedelta(minutes=95 - i)).isoformat()

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    qid_x: round(x, 2),
                    qid_m1: round(m1, 2),
                    qid_m2: round(m2, 2),
                    qid_y: round(y, 2)
                },
                "started_at": started,
                "submitted_at": submitted
            }
        )
        assert resp.status_code == 201

    # 4. Call multiple mediators endpoint
    med_res = client.post(f"/api/surveys/{survey_id}/analytics/multiple-mediators", json={
        "treatment_question_id": qid_x,
        "mediator1_question_id": qid_m1,
        "mediator2_question_id": qid_m2,
        "outcome_question_id": qid_y,
        "n_bootstraps": 100,
        "scope": "all"
    })

    assert med_res.status_code == 200
    data = med_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "MULTIPLE_SEQUENTIAL_MEDIATORS_VANDERWEELE_2014"
    diag = data["diagnostics"]
    assert diag["sample_size"] == 40
    assert "total_effect" in diag
    assert "direct_effect" in diag
    assert "total_indirect_effect" in diag
    assert "nie_seq" in diag
    assert "proportion_mediated_pct" in diag
    assert len(data["path_coefficients"]) == 6
    assert len(data["effects_summary"]) == 6
    assert "<svg" in data["svg_visualization"]
    assert "VanderWeele" in data["apa_narrative"] or "Sequential Multiple Mediation" in data["apa_narrative"] or "Trung gian" in data["apa_narrative"]


def test_multiple_mediators_validation_errors():
    # Non-existent survey
    bad_res = client.post("/api/surveys/non-existent-uuid/analytics/multiple-mediators", json={
        "treatment_question_id": "q1",
        "mediator1_question_id": "q2",
        "mediator2_question_id": "q3",
        "outcome_question_id": "q4"
    })
    assert bad_res.status_code == 404

    # Create survey but send invalid question id
    s = client.post("/api/surveys", json={"title": "Test Validation Survey"}).json()
    survey_id = s["id"]

    bad_qid_res = client.post(f"/api/surveys/{survey_id}/analytics/multiple-mediators", json={
        "treatment_question_id": "invalid_qid",
        "mediator1_question_id": "q2",
        "mediator2_question_id": "q3",
        "outcome_question_id": "q4"
    })
    assert bad_qid_res.status_code == 400
    assert "không tồn tại" in bad_qid_res.json()["detail"]
