from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection

client = TestClient(app)


def test_propensity_matching_routes():
    # 1. Create a survey
    res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Can thiệp Thực nghiệm PSM",
        "description": "Đo lường tác động can thiệp bằng Propensity Score Matching",
        "instructions": "Trả lời đầy đủ các câu hỏi"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    # 2. Add questions
    q_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_treat",
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Tham gia chương trình can thiệp",
                "is_required": True,
                "options": ["1", "0"],
                "logic_rules": []
            },
            {
                "id": "q_score",
                "order_index": 1,
                "question_type": "likert",
                "title": "Điểm hiệu suất công việc",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                "logic_rules": []
            },
            {
                "id": "q_exp",
                "order_index": 2,
                "question_type": "number",
                "title": "Số năm kinh nghiệm",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "id": "q_skill",
                "order_index": 3,
                "question_type": "likert",
                "title": "Kỹ năng chuyên môn",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })
    assert q_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 3. Submit 24 responses: 12 Treated (higher score), 12 Control
    for i in range(12):
        exp = 4.0 + (i % 4)
        skill = 3.0 + (i % 3)
        score = 7.0 + 0.3 * exp + 0.4 * skill
        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                "q_treat": "1",
                "q_score": score,
                "q_exp": exp,
                "q_skill": skill
            },
            "started_at": f"2026-10-24T05:00:{i:02d}Z",
            "submitted_at": f"2026-10-24T05:01:{i*5:02d}Z",
            "client_metadata": {"device_id": f"dev_treat_{i}"}
        })
        assert submit_res.status_code == 201

    for i in range(12):
        exp = 1.0 + (i % 5)
        skill = 1.0 + (i % 4)
        score = 5.0 + 0.3 * exp + 0.4 * skill
        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                "q_treat": "0",
                "q_score": score,
                "q_exp": exp,
                "q_skill": skill
            },
            "started_at": f"2026-10-24T05:05:{i:02d}Z",
            "submitted_at": f"2026-10-24T05:06:{i*5:02d}Z",
            "client_metadata": {"device_id": f"dev_ctrl_{i}"}
        })
        assert submit_res.status_code == 201

    # 4. Call Propensity Matching endpoint
    post_res = client.post(f"/api/surveys/{survey_id}/analytics/propensity-matching", json={
        "treatment_question_id": "q_treat",
        "treatment_value": "1",
        "outcome_question_id": "q_score",
        "covariate_question_ids": ["q_exp", "q_skill"],
        "caliper_factor": 0.50,
        "scope": "all"
    })
    assert post_res.status_code == 200
    data = post_res.json()

    assert data["status"] == "SUCCESS"
    assert data["survey_id"] == survey_id
    assert data["sample_size"] == 24
    assert data["sample_treated"] == 12
    assert data["sample_control"] == 12
    assert data["matched_pairs_count"] > 0
    assert data["caliper_width"] > 0
    assert data["matched_att"]["estimate"] > 0
    assert "ci_95_lower" in data["matched_att"]
    assert "ci_95_upper" in data["matched_att"]
    assert "ipw_att" in data
    assert data["ipw_att"]["estimate"] > 0

    # Covariate balance
    assert len(data["covariate_balance"]) == 2
    assert len(data["love_plot"]) == 2
    assert len(data["common_support_overlap"]) == 10
    assert "Rosenbaum & Rubin" in data["apa_narrative"]
    assert "Austin, 2011" in data["apa_narrative"]

    # 5. Verify audit log entry
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT action, details_json FROM audit_logs 
            WHERE entity_id = ? AND action = 'PROPENSITY_SCORE_MATCHING_EVALUATED'
        """, (survey_id,))
        log = cursor.fetchone()
        assert log is not None
        assert "PROPENSITY_SCORE_MATCHING_EVALUATED" in log["action"]
    finally:
        conn.close()
