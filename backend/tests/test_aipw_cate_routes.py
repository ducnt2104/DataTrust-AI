"""
Integration tests for Doubly Robust AIPW & Heterogeneous CATE API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_aipw_cate_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "AIPW Training Program Impact & CATE Heterogeneity",
        "description": "Evaluating impact of enterprise training with doubly robust estimation"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "AIPW Training Program Impact & CATE Heterogeneity",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Tham gia Đào tạo (1=Có, 0=Không)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Điểm hiệu suất công việc (Performance Score)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Số năm kinh nghiệm",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Điểm kỹ năng đầu vào (Baseline Skill)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 4,
                "question_type": "text",
                "title": "Phòng ban / Phân khúc (Department)",
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
    assert len(questions) == 5
    q_treat = questions[0]["id"]
    q_score = questions[1]["id"]
    q_exp = questions[2]["id"]
    q_skill = questions[3]["id"]
    q_dept = questions[4]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/aipw-cate", json={
        "treatment_question_id": q_treat,
        "outcome_question_id": q_score,
        "confounder_question_ids": [q_exp, q_skill],
        "subgroup_question_id": q_dept,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit 20 responses: 10 in "Tech", 10 in "Sales"
    now = datetime.now(timezone.utc)
    for i in range(20):
        dept = "Tech" if i < 10 else "Sales"
        is_treated = 1.0 if (i % 2 == 0) else 0.0
        exp = 2.0 + (i % 5)
        skill = 50.0 + (i * 2.0)
        # Outcome has true treatment effect (+8.0 for Tech, +2.0 for Sales) + confounding
        treat_boost = 8.0 if dept == "Tech" else 2.0
        score = 60.0 + 1.2 * exp + 0.3 * skill + (treat_boost * is_treated)

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=1200 + i * 10)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 10)).isoformat(),
            "answers": {
                q_treat: is_treated,
                q_score: score,
                q_exp: exp,
                q_skill: skill,
                q_dept: dept
            }
        })
        assert sub_res.status_code == 201

    # 5. Run AIPW CATE Analysis
    aipw_res = client.post(f"/api/surveys/{survey_id}/analytics/aipw-cate", json={
        "treatment_question_id": q_treat,
        "outcome_question_id": q_score,
        "confounder_question_ids": [q_exp, q_skill],
        "subgroup_question_id": q_dept,
        "trim_alpha": 0.05,
        "scope": "all"
    })
    assert aipw_res.status_code == 200
    data = aipw_res.json()
    assert data["status"] == "success"
    assert data["ate"] is not None
    assert data["se"] > 0
    assert data["ci_95_lower"] < data["ci_95_upper"]
    assert len(data["subgroup_cate"]) == 2
    assert "<svg" in data["svg_chart"]
    assert "AIPW" in data["apa_narrative"]
