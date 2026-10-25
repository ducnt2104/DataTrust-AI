"""
Integration tests for Panel Vector Autoregression (PVAR) & Granger Causality API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_panel_var_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Panel VAR Branch Service & Retention Dynamics",
        "description": "Multi-wave quarterly tracking of retail branches"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Panel VAR Branch Service & Retention Dynamics",
        "questions": [
            {
                "order_index": 0,
                "question_type": "text",
                "title": "Mã chi nhánh (Branch ID)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Quý khảo sát (Quarter)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Chỉ số chất lượng dịch vụ (Service Quality)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Tỷ lệ giữ chân khách hàng (Retention Rate)",
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
    assert len(questions) == 4
    q_unit = questions[0]["id"]
    q_time = questions[1]["id"]
    q_v1 = questions[2]["id"]
    q_v2 = questions[3]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/panel-var", json={
        "unit_question_id": q_unit,
        "time_question_id": q_time,
        "var1_question_id": q_v1,
        "var2_question_id": q_v2,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit 18 responses (3 units across 6 quarters)
    now = datetime.now(timezone.utc)
    units = ["Branch_HN", "Branch_HCM", "Branch_DN"]
    resp_idx = 0

    for u in units:
        v1_val = 70.0
        v2_val = 80.0
        for q in range(1, 7):
            v1_val = 0.5 * v1_val + 35.0 + (q * 0.5)
            v2_val = 0.4 * v2_val + 0.5 * v1_val + 10.0
            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "started_at": (now - timedelta(seconds=2000 + resp_idx * 20)).isoformat(),
                "submitted_at": (now - timedelta(seconds=resp_idx * 20)).isoformat(),
                "answers": {
                    q_unit: u,
                    q_time: q,
                    q_v1: v1_val,
                    q_v2: v2_val
                }
            })
            assert sub_res.status_code == 201
            resp_idx += 1

    # 5. Run Panel VAR Analysis
    pvar_res = client.post(f"/api/surveys/{survey_id}/analytics/panel-var", json={
        "unit_question_id": q_unit,
        "time_question_id": q_time,
        "var1_question_id": q_v1,
        "var2_question_id": q_v2,
        "lags": 1,
        "irf_horizons": 6,
        "scope": "all"
    })
    assert pvar_res.status_code == 200
    data = pvar_res.json()
    assert data["status"] == "success"
    assert data["panel_units_count"] == 3
    assert data["effective_observations"] > 0
    assert isinstance(data["is_stable"], bool)
    assert data["stability_max_modulus"] is not None
    assert "eq_var1" in data["equations"]
    assert "eq_var2" in data["equations"]
    assert "granger_causality" in data
    assert "<svg" in data["svg_chart"]
    assert "Panel VAR" in data["apa_narrative"]
