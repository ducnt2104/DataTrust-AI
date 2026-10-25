"""
Integration tests for Small Area Estimation (SAE) & Fay-Herriot API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_small_area_estimation_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Small Area Estimation Healthcare Survey",
        "description": "Evaluating healthcare access across rural and urban districts"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT: area (short_text), score (number), clinic_count (number)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Small Area Estimation Healthcare Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "short_text",
                "title": "Huyện / Quận (District)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Điểm chất lượng tiếp cận y tế (Health Access Score)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Số lượng trạm y tế trên địa bàn",
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

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 3
    q_area = questions[0]["id"]
    q_score = questions[1]["id"]
    q_clinic = questions[2]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/small-area-estimation", json={
        "area_question_id": q_area,
        "outcome_question_id": q_score,
        "auxiliary_question_ids": [q_clinic],
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit responses across 4 districts
    districts = {
        "District_A": ([60, 62, 65, 63], 3),
        "District_B": ([40, 45, 42, 44], 1),
        "District_C": ([75, 78, 76, 79], 5),
        "District_D": ([50, 52, 51, 53], 2)
    }

    now = datetime.now(timezone.utc)
    step = 0

    for d_name, (scores, clinics) in districts.items():
        for score_val in scores:
            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "started_at": (now - timedelta(seconds=1000 + step * 20)).isoformat(),
                "submitted_at": (now - timedelta(seconds=step * 20)).isoformat(),
                "answers": {
                    q_area: d_name,
                    q_score: score_val,
                    q_clinic: clinics
                }
            })
            assert sub_res.status_code == 201
            step += 1

    # 5. Run Small Area Estimation
    sae_res = client.post(f"/api/surveys/{survey_id}/analytics/small-area-estimation", json={
        "area_question_id": q_area,
        "outcome_question_id": q_score,
        "auxiliary_question_ids": [q_clinic],
        "scope": "all"
    })
    assert sae_res.status_code == 200
    data = sae_res.json()
    assert data["status"] == "SUCCESS"
    assert data["area_count"] == 4
    assert data["between_area_variance_sigma_v2"] is not None
    assert data["mean_shrinkage_weight_gamma"] is not None
    assert data["mean_efficiency_gain_pct"] is not None
    assert len(data["area_estimates"]) == 4
    assert len(data["regression_coefficients"]) == 2  # Intercept + clinic
    assert "<svg" in data["svg_chart"]
    assert "Fay-Herriot" in data["apa_narrative"]
