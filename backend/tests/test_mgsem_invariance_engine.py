"""
Unit tests for Multi-Group Structural Equation Modeling (MG-SEM) Invariance & Latent Means Engine
"""

import numpy as np
import pytest
from app.engine.mgsem_invariance_engine import MGSEMInvarianceEngine


def test_mgsem_insufficient_sample():
    # N < 30
    small_data = [{"Group": "A", "I1": 5, "I2": 4} for _ in range(15)]
    res = MGSEMInvarianceEngine.estimate(small_data, "Group", ["I1", "I2"])
    assert res["status"] == "INSUFFICIENT_SAMPLE"

    # m < 2
    data_one_ind = [{"Group": "A" if i % 2 == 0 else "B", "I1": i} for i in range(40)]
    res_one = MGSEMInvarianceEngine.estimate(data_one_ind, "Group", ["I1"])
    assert res_one["status"] == "INSUFFICIENT_SAMPLE"


def test_mgsem_invariance_synthetic_data():
    np.random.seed(42)
    N1, N2 = 50, 50
    rows = []

    # Group 1 (Reference): Latent mean eta ~ N(0, 1)
    for _ in range(N1):
        eta = float(np.random.normal(0, 1))
        # 3 indicators: y_j = tau_j + lambda_j * eta + e_j
        y1 = 2.0 + 0.8 * eta + float(np.random.normal(0, 0.4))
        y2 = 2.5 + 0.7 * eta + float(np.random.normal(0, 0.4))
        y3 = 3.0 + 0.9 * eta + float(np.random.normal(0, 0.4))
        rows.append({"Cohort": "North", "Ind1": y1, "Ind2": y2, "Ind3": y3})

    # Group 2 (Comparison): Latent mean eta ~ N(0.8, 1)
    for _ in range(N2):
        eta = float(np.random.normal(0.8, 1))
        y1 = 2.0 + 0.8 * eta + float(np.random.normal(0, 0.4))
        y2 = 2.5 + 0.7 * eta + float(np.random.normal(0, 0.4))
        y3 = 3.0 + 0.9 * eta + float(np.random.normal(0, 0.4))
        rows.append({"Cohort": "South", "Ind1": y1, "Ind2": y2, "Ind3": y3})

    result = MGSEMInvarianceEngine.estimate(
        data=rows,
        group_var="Cohort",
        indicator_vars=["Ind1", "Ind2", "Ind3"],
        reference_group="North"
    )

    assert result["status"] == "SUCCESS"
    assert result["model_type"] == "MULTI_GROUP_SEM_INVARIANCE"
    assert "invariance_hierarchy" in result
    assert len(result["invariance_hierarchy"]) == 4
    assert "latent_means_comparison" in result
    l_res = result["latent_means_comparison"]
    assert l_res["reference_group"] == "North"
    assert l_res["comparison_group"] == "South"
    assert l_res["cohens_d"] > 0
    assert "indicator_parameters" in result
    assert len(result["indicator_parameters"]) == 3
    assert "svg_visualization" in result
    assert "<svg" in result["svg_visualization"]
    assert "apa_narrative" in result
    assert "Meredith" in result["apa_narrative"]
