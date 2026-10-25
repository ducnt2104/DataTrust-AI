import pytest
import numpy as np
from app.engine.bsem_engine import compute_bsem_analysis, _effective_sample_size, _gelman_rubin


def test_bsem_helpers():
    # Test ESS on constant vs random
    const_arr = np.ones(100)
    assert _effective_sample_size(const_arr) == 100.0

    rand_arr = np.random.normal(size=200)
    ess = _effective_sample_size(rand_arr)
    assert 10.0 <= ess <= 200.0

    # Test Gelman-Rubin
    chain1 = np.random.normal(0, 1, 200)
    chain2 = np.random.normal(0, 1, 200)
    r_hat = _gelman_rubin([chain1, chain2])
    assert 1.0 <= r_hat < 1.10


def test_bsem_engine_basic_convergence():
    rng = np.random.RandomState(42)
    N = 80

    # True latent factors: F1 -> F2 with beta = 0.6
    F1 = rng.normal(0, 1, N)
    F2 = 0.6 * F1 + rng.normal(0, 0.6, N)

    records = []
    for i in range(N):
        # Indicators for F1: q1, q2, q3
        # Indicators for F2: q4, q5, q6
        records.append({
            "q1": float(0.8 * F1[i] + rng.normal(0, 0.4)),
            "q2": float(0.7 * F1[i] + rng.normal(0, 0.4)),
            "q3": float(0.75 * F1[i] + rng.normal(0, 0.4)),
            "q4": float(0.85 * F2[i] + rng.normal(0, 0.4)),
            "q5": float(0.7 * F2[i] + rng.normal(0, 0.4)),
            "q6": float(0.8 * F2[i] + rng.normal(0, 0.4)),
        })

    measurement_spec = {
        "F1_Motivation": ["q1", "q2", "q3"],
        "F2_Performance": ["q4", "q5", "q6"]
    }

    res = compute_bsem_analysis(
        records=records,
        measurement_spec=measurement_spec,
        structural_regressions=[{"source": "F1_Motivation", "target": "F2_Performance"}],
        prior_cross_loading_sd=0.01,
        n_iterations=400,
        n_burnin=150,
        n_chains=2,
        seed=42
    )

    assert res["status"] == "success"
    assert "sample_diagnostics" in res
    diag = res["sample_diagnostics"]
    assert diag["n_observations"] == N
    assert diag["n_factors"] == 2
    assert diag["n_items"] == 6
    assert 0.0 <= diag["posterior_predictive_p_value"] <= 1.0

    # Structural path assertions
    paths = res["structural_paths"]
    assert len(paths) == 1
    p = paths[0]
    assert p["source_factor"] == "F1_Motivation"
    assert p["target_factor"] == "F2_Performance"
    assert p["posterior_mean"] > 0.1  # Positive structural link detected
    assert p["gelman_rubin_r_hat"] <= 1.15
    assert p["effective_sample_size"] >= 15.0

    # Loadings table assertions
    loadings = res["loadings"]
    assert len(loadings) == 12  # 6 items * 2 factors
    primary_loadings = [l for l in loadings if l["is_primary"]]
    cross_loadings = [l for l in loadings if not l["is_primary"]]
    assert len(primary_loadings) == 6
    assert len(cross_loadings) == 6

    # Prior sensitivity assertions
    sens = res["prior_sensitivity"]
    assert len(sens) == 4
    for item in sens:
        assert "prior_sd" in item
        assert "posterior_mean_beta" in item

    # Visualizations & Narrative
    assert "<svg" in res["svg_chart"]
    assert "Muthén & Asparouhov" in res["apa_narrative"]
    assert "Gelman-Rubin" in res["apa_narrative"]


def test_bsem_engine_invalid_inputs():
    # Only 1 factor
    res_one_factor = compute_bsem_analysis(
        records=[{"q1": 1.0, "q2": 2.0}],
        measurement_spec={"F1": ["q1", "q2"]}
    )
    assert res_one_factor["status"] == "error"

    # Factor with only 1 indicator
    res_one_indicator = compute_bsem_analysis(
        records=[{"q1": 1.0, "q2": 2.0}],
        measurement_spec={"F1": ["q1"], "F2": ["q2"]}
    )
    assert res_one_indicator["status"] == "error"

    # Insufficient N (< 20)
    small_records = [{"q1": 1.0, "q2": 2.0, "q3": 3.0, "q4": 4.0} for _ in range(10)]
    res_small_n = compute_bsem_analysis(
        records=small_records,
        measurement_spec={"F1": ["q1", "q2"], "F2": ["q3", "q4"]}
    )
    assert res_small_n["status"] == "error"
    assert "quá ít" in res_small_n["message"]
