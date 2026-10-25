"""
Integration tests for Joint Modeling (Longitudinal & Survival Attrition) API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_joint_modeling_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Employee Engagement & Attrition Longitudinal Panel",
        "description": "Multi-wave survey monitoring employee engagement and turnover hazard"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Employee Engagement & Attrition Longitudinal Panel",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Mã nhân viên (Subject ID)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Đợt khảo sát / Tháng (Time / Wave)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Điểm gắn kết tổ chức (Engagement Score)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "single_choice",
                "title": "Đã rời tổ chức / Bỏ cuộc (Attrition Event)",
                "is_required": False,
                "options": [{"label": "Đã nghỉ việc", "value": "1"}, {"label": "Còn làm việc", "value": "0"}],
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
    q_subj = questions[0]["id"]
    q_time = questions[1]["id"]
    q_out = questions[2]["id"]
    q_event = questions[3]["id"]

    # 3. Empty survey check -> INSUFFICIENT_SAMPLE
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/joint-model", json={
        "subject_question_id": q_subj,
        "time_question_id": q_time,
        "outcome_question_id": q_out
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Ingest 15 subjects with 2-3 waves each (total ~35 responses)
    now = datetime.now(timezone.utc)
    resp_counter = 0

    for sid in range(1, 16):
        is_attrited = 1 if sid <= 6 else 0
        max_waves = 2 if is_attrited else 3

        for wave in range(1, max_waves + 1):
            resp_counter += 1
            # Lower score for attrited subjects
            score = 50.0 + (5.0 if not is_attrited else -8.0) + wave * 1.5 + (sid % 3)
            ev_status = "1" if (is_attrited and wave == max_waves) else "0"

            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "started_at": (now - timedelta(seconds=5000 + resp_counter * 20)).isoformat(),
                "submitted_at": (now - timedelta(seconds=resp_counter * 20)).isoformat(),
                "answers": {
                    q_subj: str(sid),
                    q_time: str(wave),
                    q_out: str(round(score, 1)),
                    q_event: ev_status
                }
            })
            assert sub_res.status_code in [200, 201]

    # 5. Run Joint Model Analysis
    jm_res = client.post(f"/api/surveys/{survey_id}/analytics/joint-model", json={
        "subject_question_id": q_subj,
        "time_question_id": q_time,
        "outcome_question_id": q_out,
        "event_question_id": q_event,
        "scope": "all"
    })
    assert jm_res.status_code == 200
    jm_data = jm_res.json()

    assert jm_data["status"] == "success"
    assert jm_data["sample_size"] == 15
    assert jm_data["total_longitudinal_observations"] >= 30
    assert "intercept_fixed" in jm_data["longitudinal_submodel"]
    assert "association_alpha" in jm_data["survival_submodel"]
    assert "hazard_ratio" in jm_data["survival_submodel"]
    assert len(jm_data["dynamic_predictions"]) > 5
    assert "<svg" in jm_data["svg_chart"]
    assert "Joint Modeling" in jm_data["apa_narrative"]
