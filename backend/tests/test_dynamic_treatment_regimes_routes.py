# -*- coding: utf-8 -*-
"""
Route integration tests for Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dtr_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Adaptive Two-Stage Digital Inclusion Survey",
        "description": "Evaluating dynamic treatment regimes via Q-learning backward induction"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 5 questions: X1 (Baseline), A1 (Stage 1), X2 (Interim), A2 (Stage 2), Y (Outcome)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Adaptive Two-Stage Digital Inclusion Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Năng lực Số Ban đầu (Baseline X1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Can thiệp Giai đoạn 1 (A1: 1=Có, 0=Không)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Nhận Khóa tập huấn S1"},
                    {"value": "0", "label": "Tự học thông thường S1"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Chỉ số Tham gia Giữa kỳ (Interim State X2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "single_choice",
                "title": "Can thiệp Giai đoạn 2 (A2: 1=Có, 0=Không)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Hỗ trợ 1-1 Chuyên sâu S2"},
                    {"value": "0", "label": "Hỗ trợ Tiêu chuẩn S2"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 4,
                "question_type": "number",
                "title": "Điểm Tin cậy & Hài lòng Chung Cuối kỳ (Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    x1_qid = q_objs[0]["id"]
    a1_qid = q_objs[1]["id"]
    x2_qid = q_objs[2]["id"]
    a2_qid = q_objs[3]["id"]
    y_qid = q_objs[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 36 respondents across sequential stages
    now_time = datetime.now(timezone.utc)
    for i in range(36):
        x1_val = round(2.0 + (i % 7) * 0.8, 2)
        a1_val = "1" if (i % 2 == 0) else "0"
        x2_val = round(1.5 + (i % 5) * 1.0 + (0.8 if a1_val == "1" else 0.0), 2)
        a2_val = "1" if (i % 3 == 0) else "0"
        
        # Causal outcome
        a1_num = 1 if a1_val == "1" else 0
        a2_num = 1 if a2_val == "1" else 0
        y_val = round(3.0 + 0.6 * x1_val + 0.5 * a1_num + 0.8 * x2_val + 1.2 * a2_num + 1.5 * (a2_num * x2_val), 2)

        started = (now_time - timedelta(minutes=60 - i)).isoformat()
        completed = (now_time - timedelta(minutes=55 - i)).isoformat()

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    x1_qid: x1_val,
                    a1_qid: a1_val,
                    x2_qid: x2_val,
                    a2_qid: a2_val,
                    y_qid: y_val
                },
                "started_at": started,
                "submitted_at": completed,
                "completed_at": completed,
                "honeypot": ""
            }
        )
        assert sub_res.status_code in (200, 201)

    # 5. Call DTR endpoint
    dtr_res = client.post(
        f"/api/surveys/{survey_id}/analytics/dynamic-treatment-regimes",
        json={
            "outcome_question_id": y_qid,
            "stage1_action_question_id": a1_qid,
            "stage2_action_question_id": a2_qid,
            "baseline_covariate_question_id": x1_qid,
            "interim_state_question_id": x2_qid,
            "scope": "all"
        }
    )
    assert dtr_res.status_code == 200
    data = dtr_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "DYNAMIC_TREATMENT_REGIMES_Q_LEARNING_2003"
    assert "diagnostics" in data
    assert data["diagnostics"]["sample_size"] == 36
    assert data["diagnostics"]["v_optimal"] >= data["diagnostics"]["v_never_treated"]
    assert "stage1_model" in data
    assert "stage2_model" in data
    assert "<svg" in data["svg_visualization"]
    assert "Murphy" in data["apa_narrative"]
