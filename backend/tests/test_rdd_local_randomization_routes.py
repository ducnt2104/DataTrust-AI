# -*- coding: utf-8 -*-
"""
Route integration tests for RDD with Local Randomization Engine
Cattaneo, Frandsen, & Titiunik (2015)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rdd_local_randomization_route_success():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Scholarship Eligibility Discrete RDD Survey",
        "description": "Evaluating scholarship impact with integer exam cutoffs using local randomization"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Scholarship Eligibility Discrete RDD Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Điểm Tốt Nghiệp Đại học (Graduation GPA Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Điểm Thi Tuyển Sinh Đầu vào (Discrete Test Score Running Variable X)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Điểm Rèn luyện Phổ thông (Prior Merit Covariate C1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_x = questions[1]["id"]
    qid_c = questions[2]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit 40 responses with discrete integer scores from 45 to 55 (cutoff = 50.0)
    np.random.seed(42)
    now_time = datetime.now(timezone.utc)
    cutoff = 50.0

    for i in range(40):
        x_score = float(np.random.choice([47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0]))
        is_treated = (x_score >= cutoff)
        c1 = float(np.random.normal(75.0, 5.0))
        tau = 3.5 if is_treated else 0.0
        y = float(60.0 + 0.3 * (x_score - cutoff) + tau + 0.1 * c1 + np.random.normal(0, 0.4))

        started = (now_time - timedelta(minutes=100 - i)).isoformat()
        submitted = (now_time - timedelta(minutes=95 - i)).isoformat()

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    qid_y: round(y, 2),
                    qid_x: x_score,
                    qid_c: round(c1, 1)
                },
                "started_at": started,
                "submitted_at": submitted
            }
        )
        assert resp.status_code == 201

    # 4. Call RDD local randomization endpoint
    rdd_res = client.post(f"/api/surveys/{survey_id}/analytics/rdd-local-randomization", json={
        "outcome_question_id": qid_y,
        "running_question_id": qid_x,
        "cutoff": 50.0,
        "covariate_question_ids": [qid_c],
        "window_half_width": 2.0,
        "n_permutations": 150,
        "scope": "all"
    })

    assert rdd_res.status_code == 200
    data = rdd_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "RDD_LOCAL_RANDOMIZATION_CATTANEO_2015"
    diag = data["diagnostics"]
    assert diag["sample_size"] == 40
    assert diag["cutoff_c"] == 50.0
    assert "tau_diff_means" in diag
    assert "permutation_p_value" in diag
    assert "window_half_width" in diag
    assert len(data["balance_table"]) > 0
    assert len(data["discrete_bins"]) > 0
    assert "<svg" in data["svg_visualization"]
    assert "Cattaneo" in data["apa_narrative"] or "Local Randomization" in data["apa_narrative"]


def test_rdd_local_randomization_validation_errors():
    # Non-existent survey
    bad_res = client.post("/api/surveys/non-existent-survey/analytics/rdd-local-randomization", json={
        "outcome_question_id": "q1",
        "running_question_id": "q2",
        "cutoff": 50.0
    })
    assert bad_res.status_code == 404

    # Create survey but provide invalid QID
    s = client.post("/api/surveys", json={"title": "Test Survey Validation RDD LR"}).json()
    survey_id = s["id"]

    bad_qid_res = client.post(f"/api/surveys/{survey_id}/analytics/rdd-local-randomization", json={
        "outcome_question_id": "invalid_qid",
        "running_question_id": "q2",
        "cutoff": 50.0
    })
    assert bad_qid_res.status_code == 400
    assert "không tồn tại" in bad_qid_res.json()["detail"]
