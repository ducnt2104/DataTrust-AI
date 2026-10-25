# -*- coding: utf-8 -*-
"""
Route integration tests for Stochastic Frontier Analysis (SFA; Aigner et al. 1977; JLMS 1982)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_stochastic_frontier_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Manufacturing Productivity Benchmark Survey",
        "description": "SFA technical efficiency estimation across production plants"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Output Y, Input Capital K, Input Labor L
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Manufacturing Productivity Benchmark Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Annual Output Value (million USD)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Capital Stock (K)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Labor Hours (L)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    k_qid = q_objs[1]["id"]
    l_qid = q_objs[2]["id"]

    # 3. Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 25 responses
    now_time = datetime.now(timezone.utc)
    for i in range(25):
        cap = 10.0 + (i * 2.0)
        lab = 20.0 + (i * 3.5)
        # Production with efficiency: ln Y = 1.0 + 0.45 ln K + 0.50 ln L - u
        u_ineff = 0.1 * (i % 4)
        out_val = (cap ** 0.45) * (lab ** 0.50) * 2.7 * (1.0 - u_ineff * 0.2)

        answers_payload = {
            y_qid: str(round(out_val, 2)),
            k_qid: str(round(cap, 2)),
            l_qid: str(round(lab, 2))
        }

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_payload,
                "started_at": (now_time - timedelta(minutes=60 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=59 - i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call /stochastic-frontier endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/stochastic-frontier",
        json={
            "output_question_id": y_qid,
            "input_question_ids": [k_qid, l_qid],
            "log_transform": True,
            "scope": "all"
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "STOCHASTIC_FRONTIER_ANALYSIS"
    assert data["diagnostics"]["n_units"] == 25
    assert data["diagnostics"]["n_inputs"] == 2
    assert "mean_technical_efficiency_pct" in data["diagnostics"]
    assert len(data["coefficients"]) == 3
    assert "<svg" in data["svg_visualization"]
    assert "Stochastic Frontier" in data["apa_narrative"]
