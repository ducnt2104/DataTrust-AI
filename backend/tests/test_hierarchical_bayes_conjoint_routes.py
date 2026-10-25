# -*- coding: utf-8 -*-
"""
Route tests for Choice-Based Conjoint Hierarchical Bayes Endpoint.
(POST /api/surveys/{survey_id}/analytics/hierarchical-bayes-conjoint)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_hierarchical_bayes_conjoint_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Consumer Laptop Choice & Feature Preference Conjoint Survey",
        "description": "Choice-Based Conjoint Hierarchical Bayes (Rossi et al. 2005; Train 2009)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Choice (1/0), Respondent ID, Brand, Warranty, Price
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Consumer Laptop Choice & Feature Preference Conjoint Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Choice Selection (1=Selected, 0=Not)", "is_required": True},
            {"order_index": 1, "question_type": "text", "title": "Respondent ID", "is_required": True},
            {"order_index": 2, "question_type": "text", "title": "Laptop Brand", "is_required": True},
            {"order_index": 3, "question_type": "text", "title": "Warranty Tier", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Offering Price (USD)", "is_required": True}
        ]
    })
    assert put_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    choice_qid = questions[0]["id"]
    resp_qid = questions[1]["id"]
    brand_qid = questions[2]["id"]
    warranty_qid = questions[3]["id"]
    price_qid = questions[4]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate conjoint choice task observations
    # 4 respondents, 6 choice tasks each = 24 total records
    brands = ["Brand_Alpha", "Brand_Omega"]
    warranties = ["1_Year_Standard", "2_Years_Pro", "3_Years_Enterprise"]
    prices = [800.0, 1100.0, 1400.0]

    np.random.seed(42)
    now = datetime.now(timezone.utc)

    for r_idx in range(4):
        resp_id = f"RESP_{r_idx + 1}"
        for task_idx in range(6):
            b_val = brands[task_idx % 2]
            w_val = warranties[task_idx % 3]
            p_val = prices[(task_idx + r_idx) % 3]

            u_val = (
                (1.2 if b_val == "Brand_Omega" else 0.0) +
                (1.8 if w_val == "3_Years_Enterprise" else (0.8 if w_val == "2_Years_Pro" else 0.0)) -
                0.002 * p_val +
                np.random.normal(0, 0.2)
            )
            ch_val = "1" if u_val > 0.0 else "0"

            resp = client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": {
                    choice_qid: ch_val,
                    resp_qid: resp_id,
                    brand_qid: b_val,
                    warranty_qid: w_val,
                    price_qid: str(p_val)
                },
                "started_at": (now - timedelta(minutes=2)).isoformat(),
                "submitted_at": now.isoformat()
            })
            assert resp.status_code in (200, 201)

    # 5. Call POST /api/surveys/{survey_id}/analytics/hierarchical-bayes-conjoint
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/hierarchical-bayes-conjoint", json={
        "choice_question_id": choice_qid,
        "respondent_question_id": resp_qid,
        "attribute_question_ids": [brand_qid, warranty_qid],
        "price_question_id": price_qid,
        "scope": "all"
    })

    assert ana_res.status_code == 200
    res_data = ana_res.json()
    assert res_data["status"] == "success"
    assert res_data["n_respondents"] == 4
    assert res_data["sample_size"] == 24
    assert "attribute_importance" in res_data
    assert "part_worth_utilities" in res_data
    assert "market_simulation" in res_data
    assert len(res_data["market_simulation"]) >= 2
    assert "svg_visualization" in res_data
    assert "<svg" in res_data["svg_visualization"]
    assert "apa_narrative" in res_data
