"""
Integration tests for Conformal Prediction & Distribution-Free Risk Intervals API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_conformal_prediction_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Customer Loyalty & Service Quality Survey",
        "description": "Risk prediction with distribution-free conformal uncertainty intervals"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Customer Loyalty & Service Quality Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Tốc độ phục vụ (Service Speed)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Chất lượng sản phẩm (Product Quality)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Mức độ hài lòng tổng thể (Overall Satisfaction CSAT)",
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
    speed_qid = questions[0]["id"]
    qual_qid = questions[1]["id"]
    csat_qid = questions[2]["id"]

    # 3. Check empty survey before submission
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/conformal-prediction", json={
        "target_question_id": csat_qid,
        "feature_question_ids": [speed_qid, qual_qid]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Submit responses for 35 respondents with non-normal error distribution
    np.random.seed(99)
    now_time = datetime.now(timezone.utc)
    for i in range(35):
        speed = float(np.random.uniform(1.0, 5.0))
        qual = float(np.random.uniform(1.0, 5.0))
        # Skewed residual
        noise = float(np.random.exponential(scale=0.3))
        csat = min(5.0, max(1.0, 1.2 + 0.4 * speed + 0.35 * qual + noise))

        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                speed_qid: str(round(speed, 2)),
                qual_qid: str(round(qual, 2)),
                csat_qid: str(round(csat, 2))
            },
            "started_at": (now_time - timedelta(minutes=10 + i)).isoformat(),
            "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
        })
        assert resp.status_code in [200, 201]

    # 5. Test Conformal Prediction endpoint with Split Conformal
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/conformal-prediction", json={
        "target_question_id": csat_qid,
        "feature_question_ids": [speed_qid, qual_qid],
        "alpha": 0.05,
        "method": "split_conformal",
        "clamp_min": 1.0,
        "clamp_max": 5.0,
        "scope": "all"
    })
    assert ana_res.status_code == 200
    data = ana_res.json()

    assert data["status"] == "success"
    assert data["method"] == "split_conformal"
    assert data["target_field"] == csat_qid
    assert data["sample_sizes"]["total"] == 35
    assert data["parameters"]["nominal_coverage"] == 0.95
    assert data["evaluation_metrics"]["conformal_coverage"] > 0.70
    assert len(data["calibration_curve"]) > 0
    assert len(data["sample_predictions"]) > 0
    assert "<svg" in data["svg_chart"]
    assert "APA 7th" in data["apa_narrative"]

    # 6. Test Locally-Weighted Conformal Prediction
    lw_res = client.post(f"/api/surveys/{survey_id}/analytics/conformal-prediction", json={
        "target_question_id": csat_qid,
        "feature_question_ids": [speed_qid, qual_qid],
        "alpha": 0.10,
        "method": "locally_weighted",
        "scope": "all"
    })
    assert lw_res.status_code == 200
    lw_data = lw_res.json()
    assert lw_data["status"] == "success"
    assert lw_data["method"] == "locally_weighted"
    assert lw_data["parameters"]["nominal_coverage"] == 0.90
