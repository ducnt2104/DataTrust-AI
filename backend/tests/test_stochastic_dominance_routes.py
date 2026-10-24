# -*- coding: utf-8 -*-
"""
Route integration tests for Stochastic Dominance & Distributional Inequality Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_stochastic_dominance_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Customer Tier Satisfaction & Stochastic Dominance Survey",
        "description": "Evaluating non-parametric distributional superiority between customer tiers"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Segment (Group) and Trust Score (Outcome)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Customer Tier Satisfaction & Stochastic Dominance Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Phân khúc Khách hàng",
                "is_required": True,
                "options": [
                    {"value": "enterprise", "label": "Doanh nghiệp Lớn (Enterprise)"},
                    {"value": "smb", "label": "Doanh nghiệp Vừa & Nhỏ (SMB)"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "linear_scale",
                "title": "Mức độ Tin cậy & Hài lòng (1-10)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    grp_qid = q_objs[0]["id"]
    out_qid = q_objs[1]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 30 responses (15 Enterprise with high scores 8-10, 15 SMB with lower scores 4-7)
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        is_ent = (i % 2 == 0)
        grp_val = "enterprise" if is_ent else "smb"
        # Enterprise scores: 7.5 to 9.5; SMB scores: 4.0 to 6.5
        score = (7.5 + (i % 5) * 0.5) if is_ent else (4.0 + (i % 6) * 0.5)

        started = (now_time - timedelta(minutes=45 - i)).isoformat()
        completed = (now_time - timedelta(minutes=40 - i)).isoformat()

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    grp_qid: grp_val,
                    out_qid: round(score, 1)
                },
                "started_at": started,
                "submitted_at": completed,
                "completed_at": completed,
                "honeypot": ""
            }
        )
        assert sub_res.status_code in (200, 201)

    # 5. Call Stochastic Dominance endpoint
    dom_res = client.post(
        f"/api/surveys/{survey_id}/analytics/stochastic-dominance",
        json={
            "outcome_question_id": out_qid,
            "group_question_id": grp_qid,
            "group_a_value": "enterprise",
            "group_b_value": "smb",
            "group_a_label": "Enterprise Tier",
            "group_b_label": "SMB Tier",
            "n_grid_points": 40,
            "scope": "all"
        }
    )
    assert dom_res.status_code == 200
    data = dom_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "STOCHASTIC_DOMINANCE_DAVIDSON_DUCLOS_2000"
    assert "diagnostics" in data
    assert data["diagnostics"]["sample_size_a"] == 15
    assert data["diagnostics"]["sample_size_b"] == 15
    assert data["diagnostics"]["mean_a"] > data["diagnostics"]["mean_b"]
    assert data["diagnostics"]["fsd_dominant_group"] == "A"
    assert "vượt trội Bậc 1" in data["diagnostics"]["fsd_conclusion"]
    assert len(data["grid_thresholds"]) > 5
    assert "<svg" in data["svg_visualization"]
    assert "Davidson & Duclos" in data["apa_narrative"]
