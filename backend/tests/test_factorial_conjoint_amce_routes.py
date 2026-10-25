"""
Route tests for Factorial Conjoint Experiment Analysis & AMCE Endpoint
(POST /api/surveys/{survey_id}/analytics/factorial-conjoint-amce)
DataTrust Iteration 190
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_factorial_conjoint_amce_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Factorial Conjoint Evaluation",
        "description": "Multi-attribute choice experiment with AMCE and Marginal Means"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Choice outcome, Price attribute, Warranty attribute, Brand attribute
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Factorial Conjoint Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Lua Chon San Pham (Choice)", "is_required": True},
            {"order_index": 1, "question_type": "single_choice", "title": "Muc Gia (Price)", "is_required": True},
            {"order_index": 2, "question_type": "single_choice", "title": "Thoi Han Bao Hanh (Warranty)", "is_required": True},
            {"order_index": 3, "question_type": "single_choice", "title": "Thuong Hieu (Brand)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Vi Tri Profile (Position)", "is_required": True},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    q_map = {q["title"]: q["id"] for q in detail_res.json()["questions"]}
    q_choice = q_map["Lua Chon San Pham (Choice)"]
    q_price = q_map["Muc Gia (Price)"]
    q_warr = q_map["Thoi Han Bao Hanh (Warranty)"]
    q_brand = q_map["Thuong Hieu (Brand)"]
    q_pos = q_map["Vi Tri Profile (Position)"]

    # 4. Submit 40 profile evaluations
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    prices = ["Low", "High"]
    warranties = ["1yr", "2yr"]
    brands = ["BrandA", "BrandB"]

    for i in range(40):
        p_val = prices[i % 2]
        w_val = warranties[(i // 2) % 2]
        b_val = brands[(i // 4) % 2]
        pos_val = 1 if i % 2 == 0 else 2

        # High price drops choice, 2yr increases choice
        chosen = 1 if (p_val == "Low" or w_val == "2yr") and np.random.uniform() > 0.3 else 0

        answers = {
            q_choice: str(chosen),
            q_price: p_val,
            q_warr: w_val,
            q_brand: b_val,
            q_pos: str(pos_val),
        }

        resp = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers,
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat(),
        })
        assert resp.status_code == 201, resp.text

    # 5. Execute Conjoint AMCE endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/factorial-conjoint-amce",
        json={
            "choice_question_id": q_choice,
            "attribute_question_ids": [q_price, q_warr, q_brand],
            "position_question_id": q_pos,
            "reference_levels": {
                q_price: "Low",
                q_warr: "1yr",
                q_brand: "BrandA",
            },
            "scope": "all",
        }
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert data["sample_size_profiles"] == 40
    assert len(data["attributes_evaluated"]) == 3

    # AMCE Estimates
    amces = data["amce_estimates"]
    assert q_price in amces
    assert q_warr in amces

    # Marginal Means
    mms = data["marginal_means"]
    assert q_price in mms

    # Validity Diagnostics
    assert data["validity_diagnostics"]["profile_order"] is not None

    # SVG & APA Narrative
    assert "<svg" in data["svg_visualization"]
    assert "Hainmueller, Hopkins, & Yamamoto, 2014" in data["apa_narrative"]


def test_factorial_conjoint_amce_not_found():
    res = client.post(
        "/api/surveys/non-existent-survey-uuid/analytics/factorial-conjoint-amce",
        json={
            "choice_question_id": "dummy_choice",
            "attribute_question_ids": ["dummy_attr1", "dummy_attr2"],
        }
    )
    assert res.status_code == 404
