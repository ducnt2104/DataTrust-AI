import pytest
import numpy as np
from app.engine.rdd_local_randomization_engine import RDDLocalRandomizationEngine


def test_rdd_local_randomization_synthetic():
    np.random.seed(42)
    # Discrete running variable: integer scores from 40 to 60
    cutoff = 50.0
    x_integers = np.random.choice(np.arange(42, 58), size=120)
    true_tau = 4.0

    # Baseline covariate (balanced around cutoff)
    cov1 = np.random.normal(10.0, 2.0, 120)

    # Outcome with discontinuous jump at cutoff
    is_treated = (x_integers >= cutoff).astype(float)
    y = 20.0 + 0.5 * (x_integers - cutoff) + true_tau * is_treated + 0.3 * cov1 + np.random.normal(0, 0.4, 120)

    res = RDDLocalRandomizationEngine.evaluate(
        y=y,
        x=x_integers.astype(float),
        cutoff=cutoff,
        covariates=cov1[:, None],
        covariate_names=["Đặc tính nền 1"],
        window_half_width=1.0,
        n_permutations=200
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "RDD_LOCAL_RANDOMIZATION_CATTANEO_2015"
    diag = res["diagnostics"]
    assert diag["sample_size"] == 120
    assert diag["cutoff_c"] == cutoff
    assert diag["n_in_window"] > 0
    # Estimated difference in means inside tight window is close to true_tau
    assert abs(diag["tau_diff_means"] - true_tau) < 1.0
    assert diag["permutation_p_value"] < 0.05
    assert diag["is_statistically_significant"] is True
    assert len(res["balance_table"]) > 0
    assert len(res["discrete_bins"]) > 0
    assert "<svg" in res["svg_visualization"]
    assert "Cattaneo" in res["apa_narrative"] or "Local Randomization" in res["apa_narrative"]


def test_rdd_local_randomization_insufficient_sample():
    y = np.ones(10)
    x = np.linspace(45, 55, 10)
    res = RDDLocalRandomizationEngine.evaluate(y, x, cutoff=50.0)
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_rdd_local_randomization_insufficient_variation():
    y = np.ones(30)
    x = np.linspace(51, 60, 30)  # All above cutoff 50.0 -> 0 control units
    res = RDDLocalRandomizationEngine.evaluate(y, x, cutoff=50.0)
    assert res["status"] == "INSUFFICIENT_VARIATION"
