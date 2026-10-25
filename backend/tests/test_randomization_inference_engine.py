import numpy as np
import pytest
from app.engine.randomization_inference_engine import RandomizationInferenceEngine


def test_randomization_inference_treatment_effect():
    np.random.seed(42)
    N1 = 20
    N0 = 20
    N = N1 + N0
    D = np.array([1] * N1 + [0] * N0)
    
    # Ground truth: treatment adds +4.0 points
    y1 = np.random.normal(14.0, 2.0, N1)
    y0 = np.random.normal(10.0, 2.0, N0)
    Y = np.concatenate([y1, y0])

    res = RandomizationInferenceEngine.estimate(
        outcomes=Y,
        treatment=D,
        num_permutations=1000
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["treated_count"] == N1
    assert res["control_count"] == N0
    assert res["permutations_count"] == 1000
    
    # Check difference in means and p-value
    diff_mean = res["difference_in_means"]
    assert 2.5 <= diff_mean["observed_statistic"] <= 5.5
    assert diff_mean["exact_p_value"] < 0.01
    assert diff_mean["is_significant"] is True

    # Hodges Lehmann shift
    hl = res["hodges_lehmann_shift"]
    assert 2.5 <= hl["point_estimate"] <= 5.5
    assert hl["ci_95_lower"] < hl["ci_95_upper"]

    assert "<svg" in res["svg_chart"]
    assert "Fisher's Exact Randomization Inference" in res["apa_narrative"]


def test_randomization_inference_insufficient_sample():
    # Only 3 treated
    D = np.array([1]*3 + [0]*10)
    Y = np.ones(13)
    res = RandomizationInferenceEngine.estimate(Y, D)
    assert res["status"] == "insufficient_data"
    assert "tối thiểu 5 quan sát" in res["message"]
