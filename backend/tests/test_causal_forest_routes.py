"""
Integration tests for Generalized Causal Forest (GRF) API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_causal_forest_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Promotion Sensitivity & Consumer CATE Causal Survey",
        "description": "Evaluating heterogeneous treatment effects of promotion discounts across customer segments"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Promotion Sensitivity & Consumer CATE Causal Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Nhận mã giảm giá độc quyền (Discount Promotion A)",
                "is_required": True,
                "options": [
                    {"label": "Có nhận mã", "value": "1"},
                    {"label": "Không nhận mã", "value": "0"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Giá trị giỏ hàng chi tiêu nghìn VNĐ (Cart Spend Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Số tháng gắn bó khách hàng (Customer Tenure Months X1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Tần suất mua sắm hàng tháng (Purchase Frequency X2)",
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
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]

    # 3. Check empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-forest", json={
        "treatment_question_id": a_qid,
        "outcome_question_id": y_qid,
        "feature_question_ids": [x1_qid, x2_qid]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Ingest 36 respondents
    np.random.seed(66)
    now_time = datetime.now(timezone.utc)

    for i in range(36):
        tenure = float(np.random.uniform(1.0, 36.0))
        freq = float(np.random.uniform(1.0, 10.0))
        a_val = "1" if (i % 2 == 0) else "0"
        a_num = 1.0 if a_val == "1" else 0.0

        # CATE is higher for customers with high tenure
        tau = 50.0 + 3.0 * (tenure - 18.0)
        noise = float(np.random.normal(0.0, 5.0))
        spend = 100.0 + tau * a_num + 15.0 * freq + noise

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                a_qid: a_val,
                y_qid: str(round(spend, 2)),
                x1_qid: str(round(tenure, 1)),
                x2_qid: str(round(freq, 1))
            },
            "started_at": (now_time - timedelta(minutes=45 + i)).isoformat(),
            "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
        })
        assert sub_res.status_code in [200, 201]

    # 5. Run Causal Forest Analysis
    cf_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-forest", json={
        "treatment_question_id": a_qid,
        "outcome_question_id": y_qid,
        "feature_question_ids": [x1_qid, x2_qid],
        "n_trees": 30,
        "scope": "all"
    })
    assert cf_res.status_code == 200
    data = cf_res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_total"] == 36
    assert data["sample_diagnostics"]["n_treated"] == 18
    assert data["sample_diagnostics"]["n_control"] == 18
    assert "ate_overall" in data["cate_summary"]
    assert "cate_std" in data["cate_summary"]
    assert len(data["variable_importance"]) == 2
    assert len(data["cate_distribution"]) > 0
    assert "<svg" in data["svg_chart"]
    assert "APA 7th" in data["apa_narrative"]
