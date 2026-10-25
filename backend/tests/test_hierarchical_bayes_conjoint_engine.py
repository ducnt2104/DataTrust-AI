"""
Unit tests for Choice-Based Conjoint Hierarchical Bayes Engine (CBC-HB)
DataTrust Quantitative Intelligence System
"""

import pytest
import numpy as np
from app.engine.hierarchical_bayes_conjoint_engine import run_hierarchical_bayes_conjoint


def test_conjoint_hb_insufficient_data():
    res = run_hierarchical_bayes_conjoint(
        records=[],
        choice_col="choice",
        respondent_col="resp_id",
        attribute_cols=["brand", "warranty"]
    )
    assert res["status"] == "insufficient_data"


def test_conjoint_hb_full_estimation():
    np.random.seed(42)
    # 6 respondents, 6 choice profiles each (36 records)
    records = []
    brands = ["Brand_A", "Brand_B"]
    warranties = ["1_Year", "2_Years", "3_Years"]
    prices = [100.0, 150.0, 200.0]

    for r_idx in range(6):
        resp_id = f"R_{r_idx + 1}"
        for task_idx in range(6):
            b_val = brands[task_idx % 2]
            w_val = warranties[task_idx % 3]
            p_val = prices[(task_idx + r_idx) % 3]

            # True utility: Brand_B (+1.5), 3_Years (+2.0), Price (-0.02 * p)
            u_true = (
                (1.5 if b_val == "Brand_B" else 0.0) +
                (2.0 if w_val == "3_Years" else (1.0 if w_val == "2_Years" else 0.0)) -
                0.02 * p_val +
                np.random.normal(0, 0.2)
            )
            # Binary choice
            choice = 1 if u_true > 0.0 else 0

            records.append({
                "resp_id": resp_id,
                "choice": choice,
                "brand": b_val,
                "warranty": w_val,
                "price": p_val
            })

    res = run_hierarchical_bayes_conjoint(
        records=records,
        choice_col="choice",
        respondent_col="resp_id",
        attribute_cols=["brand", "warranty"],
        price_col="price"
    )

    assert res["status"] == "success"
    assert res["n_respondents"] == 6
    assert res["sample_size"] == 36
    assert "attribute_importance" in res
    assert "brand" in res["attribute_importance"]
    assert "warranty" in res["attribute_importance"]
    assert "price" in res["attribute_importance"]
    assert "part_worth_utilities" in res
    assert len(res["part_worth_utilities"]) >= 5
    assert "market_simulation" in res
    assert len(res["market_simulation"]) == 2
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]
    assert "apa_narrative" in res
