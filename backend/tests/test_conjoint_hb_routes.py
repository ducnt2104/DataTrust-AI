# -*- coding: utf-8 -*-
"""
Route integration tests for Choice-Based Conjoint with Hierarchical Bayes (HB-CBC)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_conjoint_hb_route_direct_tasks():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Smartphone CBC Conjoint Study",
        "description": "Choice-based conjoint study on consumer preference"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    # 2. Call /analytics/conjoint-hb with explicit tasks_data
    tasks = []
    brands = ["Brand Alpha", "Brand Beta", "Brand Gamma"]
    prices = ["10tr", "15tr", "20tr"]
    battery = ["4000mAh", "5000mAh"]

    for r in range(1, 10):
        for t in range(1, 5):
            tasks.append({
                "respondent_id": f"resp_{r}",
                "task_id": f"task_{t}",
                "attributes": {
                    "brand": brands[(r + t) % len(brands)],
                    "price": prices[(t) % len(prices)],
                    "battery": battery[(r) % len(battery)]
                },
                "chosen": 1 if (t % 2 == 1) else 0
            })

    sim_scenarios = [
        {"name": "Gói Tiêu Chuẩn", "attributes": {"brand": "Brand Alpha", "price": "10tr", "battery": "5000mAh"}},
        {"name": "Gói Cao Cấp", "attributes": {"brand": "Brand Beta", "price": "20tr", "battery": "4000mAh"}}
    ]

    hb_res = client.post(
        f"/api/surveys/{survey_id}/analytics/conjoint-hb",
        json={
            "attributes_config": {
                "brand": brands,
                "price": prices,
                "battery": battery
            },
            "tasks_data": tasks,
            "price_attribute": "price",
            "simulation_scenarios": sim_scenarios,
            "n_draws": 250,
            "burn_in": 80
        }
    )

    assert hb_res.status_code == 200
    data = hb_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "CHOICE_BASED_CONJOINT_HIERARCHICAL_BAYES"
    assert "diagnostics" in data
    assert data["diagnostics"]["n_respondents"] == 9
    assert len(data["attribute_importance"]) == 3
    assert len(data["part_worth_utilities"]) > 0
    assert data["willingness_to_pay"] is not None
    assert len(data["market_simulations"]) == 2
    assert "<svg" in data["svg_visualization"]
    assert "Choice-Based Conjoint" in data["apa_narrative"]


def test_conjoint_hb_route_survey_assembly():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Conjoint Field Response Survey",
        "description": "Survey with respondent rating questions"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Conjoint Field Response Survey",
        "questions": [
            {"order_index": 0, "question_type": "text", "title": "Brand Choice", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "text", "title": "Service Tier", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Subscription Choice (1=Yes, 0=No)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    brand_qid = q_objs[0]["id"]
    tier_qid = q_objs[1]["id"]
    choice_qid = q_objs[2]["id"]

    # 3. Publish
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Ingest 15 responses
    now_time = datetime.now(timezone.utc)
    for i in range(15):
        b_choice = "EcoBrand" if (i % 2 == 0) else "ProBrand"
        t_choice = "Gold" if (i % 3 == 0) else ("Silver" if i % 3 == 1 else "Bronze")
        ch_val = "1" if (b_choice == "ProBrand" or t_choice == "Gold") else "0"

        client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    brand_qid: b_choice,
                    tier_qid: t_choice,
                    choice_qid: ch_val
                },
                "started_at": (now_time - timedelta(minutes=40 - i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=39 - i)).isoformat()
            }
        )

    # 5. Call conjoint-hb with mapping
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/conjoint-hb",
        json={
            "attributes_config": {
                "Brand": ["EcoBrand", "ProBrand"],
                "Tier": ["Gold", "Silver", "Bronze"]
            },
            "profile_attribute_mapping": {
                "Brand": brand_qid,
                "Tier": tier_qid
            },
            "choice_question_id": choice_qid,
            "n_draws": 200,
            "burn_in": 60
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["diagnostics"]["n_total_observations"] == 15
    assert len(data["attribute_importance"]) == 2
