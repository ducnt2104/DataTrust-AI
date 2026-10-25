import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dfm_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Longitudinal Sentiment Tracker Survey",
        "description": "Multi-wave consumer confidence study"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Longitudinal Sentiment Tracker Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Survey Wave", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Consumer Confidence", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Business Outlook", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Financial Security", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    wave_qid = q_objs[0]["id"]
    q1_id = q_objs[1]["id"]
    q2_id = q_objs[2]["id"]
    q3_id = q_objs[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest responses across 5 waves (6 respondents per wave = 30 total)
    now_time = datetime.now(timezone.utc)
    resp_count = 0
    for w in [1, 2, 3, 4, 5]:
        macro = 10.0 + w * 1.5
        for rep in range(6):
            resp_count += 1
            sub_res = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": {
                        wave_qid: str(w),
                        q1_id: str(round(macro + (rep % 2) * 0.4, 2)),
                        q2_id: str(round(0.9 * macro - (rep % 3) * 0.3, 2)),
                        q3_id: str(round(1.1 * macro + 0.2, 2))
                    },
                    "started_at": (now_time - timedelta(days=60 - w * 10, minutes=30)).isoformat(),
                    "submitted_at": (now_time - timedelta(days=60 - w * 10)).isoformat()
                }
            )
            assert sub_res.status_code in [200, 201]

    # 5. Run DFM Analysis
    dfm_res = client.post(
        f"/api/surveys/{survey_id}/analytics/dynamic-factor",
        json={
            "indicator_question_ids": [q1_id, q2_id, q3_id],
            "wave_question_id": wave_qid,
            "scope": "all"
        }
    )
    assert dfm_res.status_code == 200
    data = dfm_res.json()
    assert data["status"] == "success"
    diag = data["sample_diagnostics"]
    assert diag["total_waves_t"] == 5
    assert diag["total_indicators_p"] == 3
    assert len(data["trajectory"]) == 5
    assert len(data["variance_decomposition"]) == 3
    assert "<svg" in data["svg_chart"]
    assert "Stock & Watson" in data["apa_narrative"]

    # 6. Verify audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = [e["action"] for e in audit_res.json()["events"]]
    assert "DYNAMIC_FACTOR_MODEL_EVALUATED" in events


def test_dfm_routes_validation_and_errors():
    # 404
    res_404 = client.post(
        "/api/surveys/non-existent-survey/analytics/dynamic-factor",
        json={"indicator_question_ids": ["q1", "q2"]}
    )
    assert res_404.status_code == 404

    # 400 when < 2 indicator questions
    create_res = client.post("/api/surveys", json={"title": "Small"})
    sid = create_res.json()["id"]
    res_400 = client.post(
        f"/api/surveys/{sid}/analytics/dynamic-factor",
        json={"indicator_question_ids": ["q1"]}
    )
    assert res_400.status_code == 400
    assert "tối thiểu 2" in res_400.json()["detail"]
