# -*- coding: utf-8 -*-
"""
Unit tests for ConjointHBEngine (backend/app/engine/conjoint_hb_engine.py)
"""
import pytest
import numpy as np
from app.engine.conjoint_hb_engine import ConjointHBEngine


def test_conjoint_hb_insufficient_data():
    # Test insufficient data
    res_few = ConjointHBEngine.analyze_conjoint_hb(
        tasks_data=[{"attributes": {"brand": "A"}, "chosen": 1}],
        attributes_config={"brand": ["A", "B"]}
    )
    assert res_few["status"] == "INSUFFICIENT_DATA"

    # Test insufficient attributes
    res_attr = ConjointHBEngine.analyze_conjoint_hb(
        tasks_data=[{"attributes": {"brand": "A"}, "chosen": 1}] * 10,
        attributes_config={"brand": ["A", "B"]}
    )
    assert res_attr["status"] == "INSUFFICIENT_ATTRIBUTES"


def test_conjoint_hb_estimation_and_importance():
    np.random.seed(42)
    # Generate synthetic CBC task data with 10 respondents, each evaluating 6 profiles
    brands = ["Brand A", "Brand B", "Brand C"]
    prices = ["100k", "200k", "300k"]
    storage = ["64GB", "128GB"]

    attributes_config = {
        "brand": brands,
        "price": prices,
        "storage": storage
    }

    tasks_data = []
    # True utilities: Brand A=+0.8, Brand B=0.0, Brand C=-0.8; Price: 100k=+1.2, 200k=0.0, 300k=-1.2; Storage: 128GB=+0.5, 64GB=-0.5
    for resp_i in range(1, 11):
        for task_t in range(1, 7):
            b = np.random.choice(brands)
            p = np.random.choice(prices)
            s = np.random.choice(storage)

            u = 0.0
            if b == "Brand A": u += 0.8
            elif b == "Brand C": u -= 0.8

            if p == "100k": u += 1.2
            elif p == "300k": u -= 1.2

            if s == "128GB": u += 0.5
            else: u -= 0.5

            # Add idiosyncratic preference noise
            prob = 1.0 / (1.0 + np.exp(-u))
            chosen = 1 if np.random.uniform() < prob else 0

            tasks_data.append({
                "respondent_id": f"resp_{resp_i}",
                "task_id": f"task_{task_t}",
                "attributes": {
                    "brand": b,
                    "price": p,
                    "storage": s
                },
                "chosen": chosen
            })

    result = ConjointHBEngine.analyze_conjoint_hb(
        tasks_data=tasks_data,
        attributes_config=attributes_config,
        price_attribute="price",
        n_draws=300,
        burn_in=100,
        random_seed=42
    )

    assert result["status"] == "SUCCESS"
    assert result["model_type"] == "CHOICE_BASED_CONJOINT_HIERARCHICAL_BAYES"
    
    diag = result["diagnostics"]
    assert diag["n_respondents"] == 10
    assert diag["n_total_observations"] == 60
    assert diag["mcmc_draws"] == 300
    assert diag["mcmc_acceptance_rate"] > 0.05
    assert diag["hit_rate_pct"] > 50.0

    # Attribute importance must sum close to 100%
    importances = result["attribute_importance"]
    assert len(importances) == 3
    total_imp = sum(item["relative_importance_pct"] for item in importances)
    assert abs(total_imp - 100.0) < 1.0

    # Check sum-to-zero property for each attribute's level utilities
    details = result["attribute_details"]
    for attr, a_data in details.items():
        levels = a_data["levels"]
        sum_u = sum(lvl["part_worth_utility"] for lvl in levels)
        assert abs(sum_u) < 0.05  # sum to zero within rounding precision

    # Check SVG and APA narrative
    assert "<svg" in result["svg_visualization"]
    assert "Choice-Based Conjoint" in result["apa_narrative"]
    assert "Hierarchical Bayes" in result["apa_narrative"]


def test_conjoint_hb_wtp_and_market_simulation():
    attributes_config = {
        "tier": ["Basic", "Standard", "Pro"],
        "price": ["$50", "$100", "$150"]
    }

    tasks = []
    for r in range(1, 8):
        for t in range(1, 5):
            for tier in ["Basic", "Standard", "Pro"]:
                for pr in ["$50", "$100", "$150"]:
                    # Lower price and higher tier increases preference
                    pr_num = int(pr.replace("$", ""))
                    tier_bonus = 1.0 if tier == "Pro" else (0.5 if tier == "Standard" else 0.0)
                    ch = 1 if (tier_bonus > 0.4 and pr_num <= 100) else 0
                    tasks.append({
                        "respondent_id": f"user_{r}",
                        "attributes": {"tier": tier, "price": pr},
                        "chosen": ch
                    })

    custom_scenarios = [
        {"name": "Gói Tiết Kiệm", "attributes": {"tier": "Basic", "price": "$50"}},
        {"name": "Gói Doanh Nghiệp", "attributes": {"tier": "Pro", "price": "$150"}}
    ]

    res = ConjointHBEngine.analyze_conjoint_hb(
        tasks_data=tasks,
        attributes_config=attributes_config,
        price_attribute="price",
        simulation_scenarios=custom_scenarios,
        n_draws=250,
        burn_in=80,
        random_seed=123
    )

    assert res["status"] == "SUCCESS"
    wtp = res["willingness_to_pay"]
    assert wtp is not None
    assert wtp["price_attribute"] == "price"
    assert len(wtp["wtp_estimates"]) > 0

    sims = res["market_simulations"]
    assert len(sims) == 2
    total_share = sum(s["predicted_choice_share_pct"] for s in sims)
    assert abs(total_share - 100.0) < 1.0
