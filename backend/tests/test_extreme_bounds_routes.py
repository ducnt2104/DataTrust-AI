import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_extreme_bounds_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "EBA Robustness Study Survey",
        "description": "Testing policy robustness against specification searching"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Focus P, Candidates Z1, Z2, Z3
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "EBA Robustness Study Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Outcome Wellbeing Y", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Focus Policy Exposure P", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Candidate Control Z1 (Income)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Candidate Control Z2 (Education)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 4, "question_type": "number", "title": "Candidate Control Z3 (Age)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    p_qid = q_objs[1]["id"]
    z1_qid = q_objs[2]["id"]
    z2_qid = q_objs[3]["id"]
    z3_qid = q_objs[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 30 responses
    now_time = datetime.now(timezone.utc)
    for i in range(30):
        p_val = 10.0 + (i % 7) * 2.0
        z1_val = 2.0 + (i % 5) * 1.5
        z2_val = 12.0 + (i % 4)
        z3_val = 25.0 + (i % 10) * 3
        y_val = 1.8 * p_val + 0.5 * z1_val - 0.2 * z2_val + 0.1 * z3_val

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(round(y_val, 2)),
                    p_qid: str(round(p_val, 2)),
                    z1_qid: str(round(z1_val, 2)),
                    z2_qid: str(round(z2_val, 2)),
                    z3_qid: str(round(z3_val, 2)),
                },
                "started_at": (now_time - timedelta(minutes=15)).isoformat(),
                "submitted_at": now_time.isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Execute EBA analysis
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/extreme-bounds",
        json={
            "focus_question_id": p_qid,
            "outcome_question_id": y_qid,
            "candidate_question_ids": [z1_qid, z2_qid, z3_qid],
            "max_controls_per_model": 3,
            "scope": "all"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "summary" in data
    summary = data["summary"]
    assert summary["n_samples"] == 30
    assert summary["total_models_evaluated"] >= 8  # 2^3 = 8 models
    assert summary["mean_beta"] > 1.0
    assert "leamer_verdict" in summary
    assert "sala_i_martin_cdf" in summary
    assert "<svg" in data["svg_chart"]
    assert "Phân tích Cực trị" in data["apa_narrative"]


def test_extreme_bounds_routes_missing_params():
    res = client.post(
        "/api/surveys/non-existent-survey/analytics/extreme-bounds",
        json={
            "focus_question_id": "q1",
            "outcome_question_id": "q2",
            "candidate_question_ids": ["q3"],
        }
    )
    assert res.status_code == 404
