"""
Integration tests for Targeted Maximum Likelihood Estimation (TMLE) API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_tmle_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Corporate Upskilling & Productivity Evaluation Survey",
        "description": "Evaluating causal impact of training program via semiparametric TMLE"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Corporate Upskilling & Productivity Evaluation Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Tham gia khóa đào tạo chuyên sâu (Training Program A)",
                "is_required": True,
                "options": [
                    {"label": "Có tham gia", "value": "1"},
                    {"label": "Không tham gia", "value": "0"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Điểm hiệu suất công việc (Job Performance Score Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Thâm niên công tác năm (Tenure Years W1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Kỹ năng chuyên môn ban đầu (Baseline Competency W2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # Retrieve question IDs
    get_survey = client.get(f"/api/surveys/{survey_id}")
    assert get_survey.status_code == 200
    questions = get_survey.json()["questions"]
    a_qid = questions[0]["id"]
    y_qid = questions[1]["id"]
    w1_qid = questions[2]["id"]
    w2_qid = questions[3]["id"]

    # 3. Check empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/tmle", json={
        "treatment_question_id": a_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [w1_qid, w2_qid]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Ingest 36 respondents
    np.random.seed(77)
    now_time = datetime.now(timezone.utc)

    for i in range(36):
        w1 = float(np.random.uniform(1.0, 10.0))
        w2 = float(np.random.uniform(1.0, 5.0))
        # Confounded assignment probability
        prob = 1.0 / (1.0 + np.exp(-(0.2 * w1 + 0.3 * (w2 - 3.0))))
        a_val = "1" if np.random.uniform() < prob else "0"
        a_num = 1.0 if a_val == "1" else 0.0

        # Causal impact: +2.0 on performance
        y_val = 10.0 + 2.0 * a_num + 0.5 * w1 + 1.2 * w2 + float(np.random.normal(0.0, 0.4))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                a_qid: a_val,
                y_qid: str(round(y_val, 2)),
                w1_qid: str(round(w1, 1)),
                w2_qid: str(round(w2, 1))
            },
            "started_at": (now_time - timedelta(minutes=40 + i)).isoformat(),
            "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
        })
        assert sub_res.status_code in [200, 201]

    # 5. Run TMLE Analysis
    tmle_res = client.post(f"/api/surveys/{survey_id}/analytics/tmle", json={
        "treatment_question_id": a_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [w1_qid, w2_qid],
        "gbound": 0.025,
        "scope": "all"
    })
    assert tmle_res.status_code == 200
    data = tmle_res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_total"] == 36
    assert data["sample_diagnostics"]["n_treated"] > 5
    assert data["sample_diagnostics"]["n_control"] > 5
    assert "targeted_tmle_ate" in data["targeted_parameters"]
    assert "se_tmle" in data["targeted_parameters"]
    assert len(data["estimator_comparisons"]) == 4
    assert "<svg" in data["svg_chart"]
    assert "APA 7th" in data["apa_narrative"]
