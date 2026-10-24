# -*- coding: utf-8 -*-
"""
Route integration tests for Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_fmrm_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Latent Psychometric Class Survey (Rasch Mixture)",
        "description": "Evaluating unobserved differential item functioning across latent classes"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 4 questions (Items A, B, C, D)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Latent Psychometric Class Survey (Rasch Mixture)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Câu hỏi A: Mức độ bảo mật dữ liệu",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Câu hỏi B: Khả năng mở rộng hệ thống",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Câu hỏi C: Tính trực quan giao diện",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Câu hỏi D: Hỗ trợ khách hàng 24/7",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    q_ids = [q["id"] for q in q_objs]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 36 respondents across two distinct latent psychometric patterns
    now_time = datetime.now(timezone.utc)
    for i in range(36):
        is_tech = (i < 18)
        # Tech oriented respondents score high on A & B (4-5), low on C & D (1-2)
        # Service oriented respondents score low on A & B (1-2), high on C & D (4-5)
        ans_dict = {
            q_ids[0]: 4.5 if is_tech else 1.5,
            q_ids[1]: 4.0 if is_tech else 2.0,
            q_ids[2]: 1.5 if is_tech else 4.5,
            q_ids[3]: 2.0 if is_tech else 4.0
        }

        started = (now_time - timedelta(minutes=50 - i)).isoformat()
        completed = (now_time - timedelta(minutes=45 - i)).isoformat()

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": ans_dict,
                "started_at": started,
                "submitted_at": completed,
                "completed_at": completed,
                "honeypot": ""
            }
        )
        assert sub_res.status_code in (200, 201)

    # 5. Call FMRM endpoint
    fmrm_res = client.post(
        f"/api/surveys/{survey_id}/analytics/finite-mixture-rasch",
        json={
            "question_ids": q_ids,
            "n_classes": 2,
            "scope": "all"
        }
    )
    assert fmrm_res.status_code == 200
    data = fmrm_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "FINITE_MIXTURE_RASCH_ROST_1990"
    assert "diagnostics" in data
    assert data["diagnostics"]["n_classes"] == 2
    assert data["diagnostics"]["n_items"] == 4
    assert data["diagnostics"]["sample_size_total"] == 36
    assert len(data["class_proportions"]) == 2
    assert len(data["items_parameters"]) == 4
    assert "<svg" in data["svg_visualization"]
    assert "Rost" in data["apa_narrative"]
