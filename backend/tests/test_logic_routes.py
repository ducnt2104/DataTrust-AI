"""
Integration tests for Survey Logic & Branching Simulation API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_survey_logic_validate_and_simulate_routes():
    # 1. Create a test survey
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Logic Rẽ Nhánh Thực Nghiệm",
        "description": "Kiểm tra chu trình DAG và kịch bản phân nhánh",
        "instructions": "Vui lòng trả lời trung thực"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    q1_id = "test_q1_laptop"
    q2_id = "test_q2_os"
    q3_id = "test_q3_satisfaction"

    # 2. Update survey with 3 questions having branching logic: Q2 depends on Q1
    update_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": q1_id,
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Bạn có đang sử dụng laptop không?",
                "options": ["Có", "Không"],
                "is_required": True,
                "logic_rules": []
            },
            {
                "id": q2_id,
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Hệ điều hành laptop của bạn là gì?",
                "options": ["Windows", "macOS", "Linux"],
                "is_required": True,
                "logic_rules": [
                    {
                        "depends_on_question_id": q1_id,
                        "operator": "equals",
                        "value": "Có",
                        "action": "show"
                    }
                ]
            },
            {
                "id": q3_id,
                "order_index": 2,
                "question_type": "likert",
                "title": "Mức độ hài lòng chung",
                "options": ["1", "2", "3", "4", "5"],
                "is_required": False,
                "logic_rules": []
            }
        ]
    })
    assert update_res.status_code == 200

    # 3. Call validate endpoint
    val_res = client.get(f"/api/surveys/{survey_id}/logic/validate")
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["survey_id"] == survey_id
    assert val_data["is_valid"] is True
    assert val_data["health_score"] == 100.0
    assert val_data["topology"]["node_count"] == 3
    assert val_data["topology"]["branch_points_count"] == 1
    assert len(val_data["nodes"]) == 3

    # 4. Call simulate endpoint (Respondent has laptop -> all 3 questions visible)
    sim1_res = client.post(f"/api/surveys/{survey_id}/logic/simulate", json={
        "answers": {q1_id: "Có"}
    })
    assert sim1_res.status_code == 200
    sim1_data = sim1_res.json()
    assert sim1_data["visible_count"] == 3
    assert q2_id in sim1_data["visible_questions"]
    assert sim1_data["completion_ratio"] == 100.0

    # 5. Call simulate endpoint (Respondent has NO laptop -> Q2 hidden)
    sim2_res = client.post(f"/api/surveys/{survey_id}/logic/simulate", json={
        "answers": {q1_id: "Không"}
    })
    assert sim2_res.status_code == 200
    sim2_data = sim2_res.json()
    assert sim2_data["visible_count"] == 2
    assert q2_id in sim2_data["hidden_questions"]
    assert sim2_data["completion_ratio"] == 66.7
