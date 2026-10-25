import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_iv_qr_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "IV-QR Policy Evaluation Survey",
        "description": "Chernozhukov & Hansen instrumental quantile regression study"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, Instrument Z, Covariate X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "IV-QR Policy Evaluation Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Outcome Income Y", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Endogenous Training D", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Voucher Instrument Z", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Baseline Education X", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    d_qid = q_objs[1]["id"]
    z_qid = q_objs[2]["id"]
    x_qid = q_objs[3]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 35 responses
    now_time = datetime.now(timezone.utc)
    for i in range(35):
        z_val = 1.0 if (i % 2 == 0) else 0.0
        u_val = (i % 5) * 0.5 - 1.0
        x_val = 12.0 + (i % 4)
        d_val = 2.0 * z_val + 1.5 * u_val + (i % 3) * 0.3
        y_val = 1.5 * d_val + 0.5 * x_val + u_val * (1.0 + 0.2 * abs(d_val))

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(round(y_val, 2)),
                    d_qid: str(round(d_val, 2)),
                    z_qid: str(round(z_val, 2)),
                    x_qid: str(round(x_val, 2)),
                },
                "started_at": (now_time - timedelta(minutes=60 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=59 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call iv-quantile-regression endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/iv-quantile-regression",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "instrument_question_id": z_qid,
            "covariate_question_ids": [x_qid],
            "quantiles": [0.10, 0.25, 0.50, 0.75, 0.90],
            "grid_points": 50,
            "scope": "all"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "summary" in data
    assert "quantile_estimates" in data
    assert len(data["quantile_estimates"]) == 5
    assert "<svg" in data["svg_chart"]
    assert "Hồi quy Phân vị Biến công cụ" in data["apa_narrative"]


def test_iv_qr_routes_missing_survey():
    res = client.post(
        "/api/surveys/non-existent-id/analytics/iv-quantile-regression",
        json={
            "outcome_question_id": "q1",
            "treatment_question_id": "q2",
            "instrument_question_id": "q3"
        }
    )
    assert res.status_code == 404
