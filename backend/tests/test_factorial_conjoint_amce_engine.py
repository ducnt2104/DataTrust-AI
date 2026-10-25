"""
Unit tests for Factorial Conjoint Experiment Analysis & AMCE Engine.
DataTrust Quantitative Econometrics Architecture.
"""

import pytest
import numpy as np
from app.engine.factorial_conjoint_amce_engine import (
    FactorialConjointAMCEEngine,
    run_factorial_conjoint_amce,
)


def test_factorial_conjoint_synthetic_amce():
    """Test Factorial Conjoint analysis with known DGP and cluster-robust standard errors."""
    np.random.seed(42)
    n_resps = 50
    tasks_per_resp = 4
    profiles_per_task = 2
    M = n_resps * tasks_per_resp * profiles_per_task  # 400 profiles

    brands = ["BrandA", "BrandB", "BrandC"]
    prices = ["Low", "Medium", "High"]
    warranty = ["Standard", "Extended"]

    resp_ids = []
    task_ids = []
    positions = []
    brand_col = []
    price_col = []
    warranty_col = []
    choice_col = []

    for r in range(n_resps):
        r_name = f"Resp_{r}"
        for t in range(tasks_per_resp):
            # Pairwise choice task
            b1, b2 = np.random.choice(brands, size=2, replace=True)
            p1, p2 = np.random.choice(prices, size=2, replace=True)
            w1, w2 = np.random.choice(warranty, size=2, replace=True)

            # Utilities: High price is penalized (-0.30), Extended warranty is valued (+0.20)
            u1 = (0.20 if w1 == "Extended" else 0.0) - (0.30 if p1 == "High" else 0.0) + (0.10 if b1 == "BrandB" else 0.0) + np.random.normal(0, 0.4)
            u2 = (0.20 if w2 == "Extended" else 0.0) - (0.30 if p2 == "High" else 0.0) + (0.10 if b2 == "BrandB" else 0.0) + np.random.normal(0, 0.4)

            c1 = 1 if u1 >= u2 else 0
            c2 = 1 - c1

            # Profile 1
            resp_ids.append(r_name)
            task_ids.append(t + 1)
            positions.append(1)
            brand_col.append(b1)
            price_col.append(p1)
            warranty_col.append(w1)
            choice_col.append(c1)

            # Profile 2
            resp_ids.append(r_name)
            task_ids.append(t + 1)
            positions.append(2)
            brand_col.append(b2)
            price_col.append(p2)
            warranty_col.append(w2)
            choice_col.append(c2)

    res = FactorialConjointAMCEEngine.analyze(
        respondent_ids=np.array(resp_ids),
        choice_outcomes=np.array(choice_col),
        attributes_data={
            "Brand": np.array(brand_col),
            "Price": np.array(price_col),
            "Warranty": np.array(warranty_col),
        },
        task_ids=np.array(task_ids),
        profile_positions=np.array(positions),
        reference_levels={"Price": "Low", "Warranty": "Standard", "Brand": "BrandA"},
        interaction_pairs=[("Price", "Warranty")],
        seed=42,
    )

    assert res["status"] == "success"
    assert res["sample_size_profiles"] == M
    assert res["respondent_count"] == n_resps

    # AMCE Checks
    amces = res["amce_estimates"]
    assert "Price" in amces
    assert "Warranty" in amces

    # High Price AMCE should be significantly negative relative to Low
    high_price = next(row for row in amces["Price"] if row["level"] == "High")
    assert high_price["estimate"] < -0.10
    assert high_price["is_significant"]
    assert high_price["ci_95"][1] < 0.0

    # Extended Warranty AMCE should be significantly positive relative to Standard
    ext_warr = next(row for row in amces["Warranty"] if row["level"] == "Extended")
    assert ext_warr["estimate"] > 0.05
    assert ext_warr["is_significant"]

    # Marginal Means Checks
    mms = res["marginal_means"]
    assert "Price" in mms
    assert "Warranty" in mms
    # All marginal means should be bounded between 0 and 1, centered near 0.5
    for attr, rows in mms.items():
        for r in rows:
            assert 0.1 < r["marginal_mean"] < 0.9

    # ACIE Interactions
    assert "acie_interactions" in res

    # Internal Validity Diagnostics
    val = res["validity_diagnostics"]
    assert val["profile_order"] is not None
    assert "order_difference" in val["profile_order"]
    assert val["task_fatigue"] is not None
    assert "task_slope" in val["task_fatigue"]

    # SVG & APA Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Average Marginal Component Effects" in res["svg_visualization"]
    assert "Panel B: Marginal Means" in res["svg_visualization"]
    assert "Hainmueller, Hopkins, & Yamamoto, 2014" in res["apa_narrative"]


def test_factorial_conjoint_helper_records():
    """Test helper wrapper with dictionary records."""
    np.random.seed(123)
    records = []
    for i in range(60):
        resp_id = f"R_{i // 2}"
        brand = "Alpha" if i % 2 == 0 else "Beta"
        feature = "Basic" if i % 3 == 0 else "Pro"
        choice = 1 if feature == "Pro" and np.random.uniform() > 0.3 else 0

        records.append({
            "respondent_id": resp_id,
            "chosen": choice,
            "brand_attr": brand,
            "feature_attr": feature,
        })

    res = run_factorial_conjoint_amce(
        records=records,
        respondent_col="respondent_id",
        choice_col="chosen",
        attribute_cols=["brand_attr", "feature_attr"],
    )

    assert res["status"] == "success"
    assert res["sample_size_profiles"] == 60
    assert "brand_attr" in res["amce_estimates"]
    assert "feature_attr" in res["amce_estimates"]


def test_factorial_conjoint_sample_size_error():
    """Test sample size validation (<20 profile records)."""
    with pytest.raises(ValueError, match="too small"):
        FactorialConjointAMCEEngine.analyze(
            respondent_ids=np.array(["R1", "R2", "R3"]),
            choice_outcomes=np.array([1, 0, 1]),
            attributes_data={"A": np.array(["L1", "L2", "L1"])},
        )


def test_factorial_conjoint_single_level_error():
    """Test error when attribute has only 1 distinct level."""
    with pytest.raises(ValueError, match="at least 2 distinct levels"):
        FactorialConjointAMCEEngine.analyze(
            respondent_ids=np.array([f"R{i}" for i in range(30)]),
            choice_outcomes=np.random.randint(0, 2, size=30),
            attributes_data={"OnlyOne": np.array(["ConstantLevel"] * 30)},
        )
