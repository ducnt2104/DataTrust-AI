"""
Integration tests for Synthetic Difference-in-Differences (SDID) API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_sdid_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Regional Market Expansion & Revenue SDID Evaluation",
        "description": "Evaluating policy impact on treated regions using doubly weighted SDID"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Regional Market Expansion & Revenue SDID Evaluation",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Vùng thị trường (Region Unit ID)",
                "is_required": True,
                "options": [
                    {"label": f"Vùng {i}", "value": f"Region_{i}"} for i in range(1, 7)
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Quý / Đợt khảo sát (Quarter Time Wave)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Doanh thu bình quân triệu VNĐ (Average Revenue Outcome Y)",
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
    u_qid = questions[0]["id"]
    t_qid = questions[1]["id"]
    y_qid = questions[2]["id"]

    # 3. Check empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/sdid", json={
        "unit_question_id": u_qid,
        "time_question_id": t_qid,
        "outcome_question_id": y_qid,
        "treated_units": ["Region_1"],
        "treatment_start_time": 3
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Ingest 24 responses across 6 regions and 4 quarters (1, 2 = pre, 3, 4 = post)
    np.random.seed(55)
    now_time = datetime.now(timezone.utc)
    resp_count = 0

    for reg_idx in range(1, 7):
        reg_name = f"Region_{reg_idx}"
        is_treated = (reg_name == "Region_1")
        base_val = 50.0 + reg_idx * 5.0

        for qtr in [1, 2, 3, 4]:
            resp_count += 1
            is_post = (qtr >= 3)
            # Treatment jump: +15.0 in quarters 3 and 4 for Region 1
            effect = 15.0 if (is_treated and is_post) else 0.0
            noise = float(np.random.normal(0.0, 0.5))
            rev = base_val + qtr * 2.5 + effect + noise

            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": {
                    u_qid: reg_name,
                    t_qid: str(qtr),
                    y_qid: str(round(rev, 2))
                },
                "started_at": (now_time - timedelta(minutes=40 + resp_count)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=resp_count)).isoformat()
            })
            assert sub_res.status_code in [200, 201]

    # 5. Run SDID Analysis
    sdid_res = client.post(f"/api/surveys/{survey_id}/analytics/sdid", json={
        "unit_question_id": u_qid,
        "time_question_id": t_qid,
        "outcome_question_id": y_qid,
        "treated_units": ["Region_1"],
        "treatment_start_time": 3,
        "n_placebo_reps": 50,
        "scope": "all"
    })
    assert sdid_res.status_code == 200
    data = sdid_res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_treated_units"] == 1
    assert data["sample_diagnostics"]["n_control_units"] == 5
    assert data["sample_diagnostics"]["t_pre_periods"] == 2
    assert data["sample_diagnostics"]["t_post_periods"] == 2
    assert "tau_sdid" in data["sdid_estimates"]
    assert "se_sdid" in data["sdid_estimates"]
    assert len(data["top_donor_weights"]) > 0
    assert len(data["time_weights"]) == 2
    assert len(data["time_trajectories"]) == 4
    assert "<svg" in data["svg_chart"]
    assert "APA 7th" in data["apa_narrative"]
