# -*- coding: utf-8 -*-
"""
Route integration tests for Double / Debiased Machine Learning (DML) Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dml_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "High-Dimensional Policy Evaluation Survey (DML)",
        "description": "Estimating debiased causal treatment effects with orthogonal scores"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome (Y), Treatment (D), Covariate 1 (X1), Covariate 2 (X2)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "High-Dimensional Policy Evaluation Survey (DML)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Chỉ số Hài lòng & Gắn kết (Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Tiếp cận Tính năng Thử nghiệm (Treatment D)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Được cấp quyền (Treated)"},
                    {"value": "0", "label": "Tiêu chuẩn (Control)"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Thời gian sử dụng nền tảng (Tháng X1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Mức độ am hiểu kỹ thuật số (X2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    d_qid = q_objs[1]["id"]
    x1_qid = q_objs[2]["id"]
    x2_qid = q_objs[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 36 responses with confounded relationships
    now_time = datetime.now(timezone.utc)
    for i in range(36):
        x1_val = round(3.0 + (i % 6) * 1.5, 2)
        x2_val = round(2.0 + (i % 4) * 1.2, 2)
        
        # Confounded treatment assignment probability
        d_val = "1" if (i % 2 == 0) else "0"
        d_num = 1.0 if d_val == "1" else 0.0

        # Outcome has true causal effect of +2.0 plus confounding from X1 and X2
        y_val = round(4.0 + 2.0 * d_num + 0.8 * x1_val + 0.6 * x2_val, 2)

        started = (now_time - timedelta(minutes=50 - i)).isoformat()
        completed = (now_time - timedelta(minutes=45 - i)).isoformat()

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: y_val,
                    d_qid: d_val,
                    x1_qid: x1_val,
                    x2_qid: x2_val
                },
                "started_at": started,
                "submitted_at": completed,
                "completed_at": completed,
                "honeypot": ""
            }
        )
        assert sub_res.status_code in (200, 201)

    # 5. Call DML endpoint
    dml_res = client.post(
        f"/api/surveys/{survey_id}/analytics/double-machine-learning",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "covariate_question_ids": [x1_qid, x2_qid],
            "n_folds": 3,
            "alpha_penalty": 0.5,
            "scope": "all"
        }
    )
    assert dml_res.status_code == 200
    data = dml_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "DOUBLE_MACHINE_LEARNING_CHERNOZHUKOV_2018"
    assert "diagnostics" in data
    assert data["diagnostics"]["sample_size"] == 36
    assert data["diagnostics"]["n_covariates"] == 2
    assert "theta_dml" in data["diagnostics"]
    assert "ci_lower_95" in data["diagnostics"]
    assert len(data["confounding_covariates"]) == 2
    assert "<svg" in data["svg_visualization"]
    assert "Chernozhukov" in data["apa_narrative"]
