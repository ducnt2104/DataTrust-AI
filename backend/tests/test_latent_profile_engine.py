import pytest
import numpy as np
from app.engine.latent_profile_engine import LatentProfileEngine


def test_latent_profile_engine_success():
    # Generate synthetic 2-profile survey data
    np.random.seed(42)
    n1 = 40
    n2 = 40
    p = 3

    # Profile 1: Low-satisfaction detractors
    p1 = np.random.normal(loc=[1.8, 2.0, 1.9], scale=[0.4, 0.4, 0.4], size=(n1, p))
    # Profile 2: High-satisfaction advocates
    p2 = np.random.normal(loc=[4.8, 4.7, 4.9], scale=[0.4, 0.4, 0.4], size=(n2, p))

    data = np.vstack([p1, p2]).tolist()
    labels = ["Trust_Score", "Service_Quality", "Platform_Speed"]

    res = LatentProfileEngine.compute_latent_profiles(
        data_matrix=data,
        indicator_labels=labels,
        n_profiles=2,
        max_profiles=3
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "LATENT_PROFILE_ANALYSIS_GMM"
    diag = res["diagnostics"]
    assert diag["sample_size"] == 80
    assert diag["n_indicators"] == 3
    assert diag["optimal_n_classes"] == 2
    assert diag["entropy"] > 0.70  # Clean separation between two distinct clusters
    assert len(res["profiles"]) == 2
    assert "<svg" in res["svg_visualization"]
    assert "APA 7th Edition" in res["apa_narrative"]
    assert len(res["model_comparison"]) >= 1


def test_latent_profile_engine_insufficient_sample():
    data = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]]
    labels = ["X1", "X2"]
    res = LatentProfileEngine.compute_latent_profiles(data, labels)
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_latent_profile_engine_insufficient_indicators():
    data = [[1.0] for _ in range(25)]
    labels = ["X1"]
    res = LatentProfileEngine.compute_latent_profiles(data, labels)
    assert res["status"] == "INSUFFICIENT_INDICATORS"
