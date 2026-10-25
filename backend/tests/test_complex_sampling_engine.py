"""
Unit tests for Complex Sampling Design & Horvitz-Thompson Taylor Series Linearization Engine.
"""

import pytest
from app.engine.complex_sampling_engine import ComplexSamplingEngine


def test_complex_sampling_insufficient_sample():
    records = [
        {"target_val": 4.0, "cluster_val": "C1", "weight_val": 1.0},
        {"target_val": 3.5, "cluster_val": "C2", "weight_val": 1.0}
    ]
    res = ComplexSamplingEngine.analyze_complex_design(records)
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "tối thiểu N >= 5" in res["message"]


def test_complex_sampling_zero_variance():
    records = [
        {"target_val": 5.0, "cluster_val": f"C{i%3}", "weight_val": 1.0}
        for i in range(12)
    ]
    res = ComplexSamplingEngine.analyze_complex_design(records)
    assert res["status"] == "ZERO_VARIANCE"


def test_complex_sampling_insufficient_clusters():
    records = [
        {"target_val": float(i + 1), "cluster_val": "Single_Cluster_1", "weight_val": 1.0}
        for i in range(10)
    ]
    res = ComplexSamplingEngine.analyze_complex_design(records)
    assert res["status"] == "INSUFFICIENT_CLUSTERS"


def test_complex_sampling_clustered_design_evaluation():
    # Giả lập mẫu khảo sát 4 trường học (PSU = School_1 .. School_4)
    # Trường 1 & 2 có điểm trung bình cao (4.5), Trường 3 & 4 có điểm thấp (2.0) -> Intra-cluster correlation cao
    records = []
    # Cụm 1
    for _ in range(10):
        records.append({"target_val": 4.5, "cluster_val": "School_A", "stratum_val": "Region_North", "weight_val": 1.2})
    # Cụm 2
    for _ in range(10):
        records.append({"target_val": 4.2, "cluster_val": "School_B", "stratum_val": "Region_North", "weight_val": 1.0})
    # Cụm 3
    for _ in range(10):
        records.append({"target_val": 2.2, "cluster_val": "School_C", "stratum_val": "Region_South", "weight_val": 0.8})
    # Cụm 4
    for _ in range(10):
        records.append({"target_val": 1.8, "cluster_val": "School_D", "stratum_val": "Region_South", "weight_val": 1.1})

    res = ComplexSamplingEngine.analyze_complex_design(
        records=records,
        target_title="Điểm số đánh giá chất lượng",
        cluster_title="Trường học",
        stratum_title="Khu vực"
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 40
    assert res["strata_count"] == 2
    assert res["psu_count"] == 4
    assert res["degrees_of_freedom"] == 2  # 4 PSUs - 2 Strata = 2 df

    # Horvitz-Thompson estimates
    ht = res["horvitz_thompson_estimates"]
    assert 2.5 < ht["weighted_mean"] < 4.0
    assert "weighting_bias_shift" in ht

    # Taylor Series Linearization Variance
    taylor = res["taylor_linearization_variance"]
    assert taylor["complex_variance"] > 0
    assert taylor["complex_se"] > 0
    assert taylor["ci_95_lower"] < ht["weighted_mean"] < taylor["ci_95_upper"]

    # Design effects: Clustering causes DEFF > 1.0 and ICC > 0
    deff_info = res["design_effects"]
    assert deff_info["deff"] > 1.0
    assert deff_info["deft"] > 1.0
    assert deff_info["icc"] > 0.0
    assert deff_info["effective_sample_size"] < 40
    assert deff_info["efficiency_loss_pct"] > 0

    # APA Narrative
    apa = res["apa_narrative"]
    assert "Two-Stage Complex Survey Design" in apa
    assert "Horvitz-Thompson" in apa
    assert "Taylor Series Linearization" in apa
    assert "DEFF =" in apa
