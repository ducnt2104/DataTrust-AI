"""
Unit tests for Double/Debiased Machine Learning with Cluster-Robust Cross-Fitting Engine (Cluster-DML)
DataTrust Iteration 175
"""

import pytest
import numpy as np
from app.engine.cluster_dml_engine import run_cluster_dml


def test_cluster_dml_estimation_recovers_effect():
    np.random.seed(42)
    C = 20
    m = 15
    true_theta = 3.2

    records = []
    # Cluster error shocks
    cluster_u = np.random.normal(0, 1.2, size=C)

    for c in range(C):
        u_c = cluster_u[c]
        for i in range(m):
            x1 = np.random.uniform(-1, 1)
            x2 = np.random.normal(0, 1)

            # Treatment assignment
            d_lat = 0.5 * x1 - 0.3 * x2 + np.random.normal(0, 0.5)
            d = 1.0 if d_lat > 0 else 0.0

            # Outcome with cluster shock
            g = 1.5 * x1 + 0.8 * x2
            y = true_theta * d + g + u_c + np.random.normal(0, 0.5)

            records.append({
                "cluster_id": f"dept_{c}",
                "treatment": d,
                "outcome": round(float(y), 2),
                "cov1": round(float(x1), 3),
                "cov2": round(float(x2), 3)
            })

    res = run_cluster_dml(
        records=records,
        cluster_col="cluster_id",
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["cov1", "cov2"],
        n_splits=4,
        ml_model="random_forest"
    )

    assert res["status"] == "success"
    assert res["sample_size"] == C * m
    assert res["diagnostics"]["num_clusters"] == C

    est = res["estimates"]
    # Check that estimated theta is close to true_theta = 3.2
    assert abs(est["theta"] - true_theta) < 0.5
    assert est["is_significant"] is True
    assert est["p_value_cluster"] < 0.05
    assert est["se_cluster"] > 0
    # Clustered SE should be inflated relative to naive SE when ICC > 0
    assert est["se_inflation_ratio"] >= 1.0

    assert len(res["cluster_profiles"]) == C
    assert "<svg" in res["svg_visualization"]
    assert "Chiang" in res["apa_narrative"]


def test_cluster_dml_insufficient_sample():
    records = [{"cluster": "c1", "d": 1, "y": 10, "x": 1}]
    res = run_cluster_dml(
        records=records,
        cluster_col="cluster",
        treatment_col="d",
        outcome_col="y",
        covariate_cols=["x"]
    )
    assert res["status"] == "error"
    assert "quá ít" in res["message"]


def test_cluster_dml_too_few_clusters():
    records = [{"cluster": f"c_{i%2}", "d": 1, "y": 10, "x": 1} for i in range(40)]
    res = run_cluster_dml(
        records=records,
        cluster_col="cluster",
        treatment_col="d",
        outcome_col="y",
        covariate_cols=["x"]
    )
    assert res["status"] == "error"
    assert "tối thiểu 4 cụm" in res["message"]
