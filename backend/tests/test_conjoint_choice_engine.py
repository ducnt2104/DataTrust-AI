"""
Unit tests for Conjoint Analysis & Discrete Choice Experiment (DCE) Engine
"""

import numpy as np
import pytest
from app.engine.conjoint_choice_engine import ConjointChoiceEngine


def test_conjoint_insufficient_sample():
    # N < 20
    small_data = [{"Choice": 1, "Attr1": 5} for _ in range(10)]
    res = ConjointChoiceEngine.estimate(small_data, "Choice", ["Attr1"])
    assert res["status"] == "INSUFFICIENT_SAMPLE"

    # All chosen (n_rejected < 5)
    all_chosen = [{"Choice": 1, "Attr1": i} for i in range(25)]
    res_all = ConjointChoiceEngine.estimate(all_chosen, "Choice", ["Attr1"])
    assert res_all["status"] == "INSUFFICIENT_SAMPLE"


def test_conjoint_choice_synthetic_data():
    np.random.seed(42)
    N = 120
    rows = []
    for i in range(N):
        quality = float(np.random.uniform(1, 5))
        brand = float(np.random.uniform(1, 5))
        price = float(np.random.uniform(10, 50))  # Price in mil VND

        # True utility: U = 0.8 * quality + 0.4 * brand - 0.05 * price
        utility = 0.8 * quality + 0.4 * brand - 0.05 * price
        prob = 1.0 / (1.0 + np.exp(-utility))
        choice = 1 if np.random.rand() < prob else 0

        rows.append({
            "Choice": choice,
            "Quality": quality,
            "BrandReputation": brand,
            "ProductPrice": price
        })

    result = ConjointChoiceEngine.estimate(
        choice_data=rows,
        choice_var="Choice",
        attribute_vars=["Quality", "BrandReputation", "ProductPrice"],
        price_var="ProductPrice",
        price_unit="mil VND"
    )

    assert result["status"] == "SUCCESS"
    assert result["model_type"] == "CONJOINT_DISCRETE_CHOICE_MNL"
    assert "part_worth_utilities" in result
    assert len(result["part_worth_utilities"]) == 3
    # Check that relative importance sums to ~100%
    total_imp = sum(p["relative_importance_pct"] for p in result["part_worth_utilities"])
    assert abs(total_imp - 100.0) < 1.0

    # Willingness to pay should be computed for Quality and BrandReputation
    assert "willingness_to_pay" in result
    assert len(result["willingness_to_pay"]) == 2
    assert "svg_visualization" in result
    assert "<svg" in result["svg_visualization"]
    assert "apa_narrative" in result
    assert "McFadden" in result["apa_narrative"]


def test_conjoint_without_price():
    np.random.seed(123)
    N = 60
    rows = []
    for i in range(N):
        a1 = float(np.random.randint(1, 6))
        a2 = float(np.random.randint(1, 6))
        choice = 1 if (a1 + a2 > 6) else 0
        rows.append({"Choice": choice, "A1": a1, "A2": a2})

    res = ConjointChoiceEngine.estimate(rows, "Choice", ["A1", "A2"])
    assert res["status"] == "SUCCESS"
    assert len(res["part_worth_utilities"]) == 2
    assert len(res["willingness_to_pay"]) == 0
