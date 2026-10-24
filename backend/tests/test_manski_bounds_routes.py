# -*- coding: utf-8 -*-
"""
Route integration tests for Manski Non-Parametric Partial Identification & Worst-Case Bounds Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_manski_bounds_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Digital Platform Policy Impact Survey under Non-Response",
        "description": "Evaluating non-parametric treatment effect bounds without unverified missingness assumptions"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Treatment Group (D) and Outcome Score (Y)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Digital Platform Policy Impact Survey under Non-Response",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Nhóm Can thiệp Chính sách (1=Can thiệp, 0=Đối chứng)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Nhánh Can thiệp (Treatment)"},
                    {"value": "0", "label": "Nhánh Đối chứng (Control)"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Chỉ số Hiệu quả Số (Outcome 1-10)",
                "is_required": False,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    treat_qid = q_objs[0]["id"]
    out_qid = q_objs[1]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 32 responses (16 treated, 16 control with missingness)
    now_time = datetime.now(timezone.utc)
    for i in range(32):
        is_treated = (i < 16)
        treat_val = "1" if is_treated else "0"
        
        # Treatment has higher scores (7.0 - 9.5), control has lower scores (3.0 - 5.5)
        # 4 treated respondents miss outcome (indices 0, 1, 2, 3)
        # 3 control respondents miss outcome (indices 16, 17, 18)
        is_missing = (i in [0, 1, 2, 3, 16, 17, 18])
        
        answers = {treat_qid: treat_val}
        if not is_missing:
            score = (7.0 + (i % 5) * 0.5) if is_treated else (3.0 + (i % 5) * 0.5)
            answers[out_qid] = score

        started = (now_time - timedelta(minutes=50 - i)).isoformat()
        completed = (now_time - timedelta(minutes=45 - i)).isoformat()

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers,
                "started_at": started,
                "submitted_at": completed,
                "completed_at": completed,
                "honeypot": ""
            }
        )
        assert sub_res.status_code in (200, 201)

    # 5. Call Manski Bounds endpoint
    manski_res = client.post(
        f"/api/surveys/{survey_id}/analytics/manski-bounds",
        json={
            "outcome_question_id": out_qid,
            "treatment_question_id": treat_qid,
            "support_min": 1.0,
            "support_max": 10.0,
            "confidence_level": 0.95,
            "scope": "all"
        }
    )
    assert manski_res.status_code == 200
    data = manski_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "MANSKI_PARTIAL_IDENTIFICATION_BOUNDS_2000"
    assert "diagnostics" in data
    assert data["diagnostics"]["sample_size_total"] == 32
    assert data["diagnostics"]["n_treated"] == 16
    assert data["diagnostics"]["n_control"] == 16
    assert data["diagnostics"]["observed_count"] == 25
    assert data["diagnostics"]["worst_case_lower"] < data["diagnostics"]["worst_case_upper"]
    assert len(data["tiers"]) == 4
    assert len(data["sensitivity_grid"]) == 15
    assert "<svg" in data["svg_visualization"]
    assert "Manski" in data["apa_narrative"]
