import numpy as np
import pytest
from app.engine.latent_growth_engine import LatentGrowthEngine


def test_latent_growth_linear_trajectory():
    np.random.seed(42)
    N = 60
    T = 4
    time_scores = [0.0, 1.0, 2.0, 3.0]
    
    # Ground truth: intercept ~ N(10, 2), slope ~ N(1.5, 0.5)
    true_intercepts = np.random.normal(10.0, 1.4, N)
    true_slopes = np.random.normal(1.5, 0.6, N)
    
    wave_data = np.zeros((N, T))
    for t_idx, t_val in enumerate(time_scores):
        noise = np.random.normal(0, 0.3, N)
        wave_data[:, t_idx] = true_intercepts + true_slopes * t_val + noise

    res = LatentGrowthEngine.estimate(
        wave_data=wave_data,
        time_scores=time_scores,
        wave_labels=["Wave 1", "Wave 2", "Wave 3", "Wave 4"]
    )

    assert res["status"] == "success"
    # Intercept mean should be ~10.0
    assert 9.0 <= res["latent_means"]["intercept_mean"] <= 11.0
    assert res["latent_means"]["intercept_p"] < 0.001
    
    # Slope mean should be ~1.5
    assert 1.0 <= res["latent_means"]["slope_mean"] <= 2.0
    assert res["latent_means"]["slope_p"] < 0.001
    
    # Variances
    assert res["latent_variances"]["intercept_variance"] > 0
    assert res["latent_variances"]["slope_variance"] > 0
    
    # Fit indices
    fit = res["model_fit"]
    assert "cfi" in fit
    assert "rmsea" in fit
    assert fit["cfi"] >= 0.85
    
    # SVG and APA narrative
    assert "<svg" in res["svg_chart"]
    assert "Mô hình Quỹ đạo Tăng trưởng Tiềm ẩn" in res["apa_narrative"]
    assert len(res["observed_wave_means"]) == T


def test_latent_growth_insufficient_data():
    # Only 2 waves (T < 3)
    data = np.ones((20, 2))
    res = LatentGrowthEngine.estimate(data)
    assert res["status"] == "insufficient_data"
    assert "3 đợt" in res["message"]

    # Only 10 individuals (N < 15)
    data_small = np.ones((10, 4))
    res2 = LatentGrowthEngine.estimate(data_small)
    assert res2["status"] == "insufficient_data"
    assert "15 người" in res2["message"]
