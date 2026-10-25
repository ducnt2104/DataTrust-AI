# -*- coding: utf-8 -*-
"""
Route tests for Shift-Share Instrumental Variables Endpoint.
(POST /api/surveys/{survey_id}/analytics/shift-share-iv)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_shift_share_iv_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Regional Labor Market Shocks & Wage Dynamics",
        "description": "Shift-Share Bartik IV with Goldsmith-Pinkham Rotemberg decomposition"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Endogenous D, Shares S1, S2, S3, Control X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Regional Labor Market Shocks & Wage Dynamics",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Local Average Wage Growth (%)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Local Employment Inflow Rate", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Manufacturing Share (z1)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Technology Services Share (z2)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Hospitality & Retail Share (z3)", "is_required": True},
            {"order_index": 5, "question_type": "number", "title": "Baseline Urbanization Index", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    s1_qid = questions[2]["id"]
    s2_qid = questions[3]["id"]
    s3_qid = questions[4]["id"]
    x_qid = questions[5]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 55 responses
    np.random.seed(55)
    now = datetime.now(timezone.utc)
    g_shocks = [3.0, 1.2, -0.8]

    for i in range(55):
        raw_shares = np.random.dirichlet([2.0, 3.0, 1.5])
        z_bartik = float(np.dot(raw_shares, g_shocks))
        x_val = float(np.random.normal(50, 10))
        d_val = float(2.2 * z_bartik + 0.05 * (x_val - 50) + np.random.normal(0, 0.5))
        y_val = float(10.0 + 1.8 * d_val + 0.1 * (x_val - 50) + np.random.normal(0, 0.7))

        answers_dict = {
            y_qid: str(round(y_val, 2)),
            d_qid: str(round(d_val, 2)),
            s1_qid: str(round(raw_shares[0], 4)),
            s2_qid: str(round(raw_shares[1], 4)),
            s3_qid: str(round(raw_shares[2], 4)),
            x_qid: str(round(x_val, 2))
        }

        resp = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_dict,
                "started_at": (now - timedelta(minutes=3)).isoformat(),
                "submitted_at": now.isoformat()
            }
        )
        assert resp.status_code in [200, 201]

    # 5. Call shift-share-iv endpoint
    ss_res = client.post(
        f"/api/surveys/{survey_id}/analytics/shift-share-iv",
        json={
            "outcome_question_id": y_qid,
            "treatment_question_id": d_qid,
            "share_question_ids": [s1_qid, s2_qid, s3_qid],
            "shocks": g_shocks,
            "covariate_question_ids": [x_qid],
            "alpha_level": 0.05,
            "scope": "all"
        }
    )
    assert ss_res.status_code == 200
    res_data = ss_res.json()
    assert res_data["status"] == "SUCCESS"
    assert "overall_summary" in res_data
    assert res_data["overall_summary"]["sample_size"] == 55
    assert res_data["overall_summary"]["first_stage_f_statistic"] > 5.0
    assert "rotemberg_decomposition" in res_data
    assert len(res_data["rotemberg_decomposition"]) == 3
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data

    # 6. Verify audit log entry
    with get_db() as conn:
        log = conn.execute("""
            SELECT * FROM audit_logs 
            WHERE entity_id = ? AND action = 'SHIFT_SHARE_IV_EVALUATED'
        """, (survey_id,)).fetchone()
        assert log is not None
