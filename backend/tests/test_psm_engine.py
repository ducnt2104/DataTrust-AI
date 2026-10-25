import pytest
from app.engine.psm_engine import PSMEngine


def test_logistic_regression_and_sigmoid():
    # Verify sigmoid
    assert PSMEngine._sigmoid(0.0) == 0.5
    assert PSMEngine._sigmoid(100.0) > 0.9999
    assert PSMEngine._sigmoid(-100.0) < 0.0001

    # Verify logistic regression on synthetic separation
    # X: intercept, x1
    X = [
        [1.0, 1.0],
        [1.0, 1.2],
        [1.0, 0.8],
        [1.0, 4.0],
        [1.0, 4.5],
        [1.0, 5.0],
    ]
    y = [0, 0, 0, 1, 1, 1]
    beta, probs = PSMEngine._fit_logistic_regression(X, y)
    assert len(beta) == 2
    assert beta[1] > 0  # Higher x1 leads to higher probability of y=1
    assert probs[0] < 0.5
    assert probs[-1] > 0.5


def test_psm_engine_matching_and_balance():
    # Construct 24 records with confounding:
    # Treated: experience higher (4-7), tech skill higher (3-5), outcome higher
    # Control: experience lower (1-5), tech skill lower (1-4), outcome lower
    records = []
    for i in range(12):
        exp = 4.0 + (i % 4)
        tech = 3.0 + (i % 3)
        # Treatment causal effect = +2.0
        out = 5.0 + 2.0 + 0.3 * exp + 0.4 * tech + (0.1 * (i % 2))
        records.append({
            "id": f"treat_{i}",
            "treatment": 1,
            "outcome": out,
            "covariates": [exp, tech]
        })

    for i in range(12):
        exp = 1.0 + (i % 5)
        tech = 1.0 + (i % 4)
        out = 5.0 + 0.0 + 0.3 * exp + 0.4 * tech + (0.1 * (i % 2))
        records.append({
            "id": f"ctrl_{i}",
            "treatment": 0,
            "outcome": out,
            "covariates": [exp, tech]
        })

    result = PSMEngine.analyze_propensity_matching(
        records=records,
        treatment_name="Tham Gia Khóa Đào Tạo AI",
        outcome_name="Hiệu Suất Lao Động (1-10)",
        covariate_names=["Số năm kinh nghiệm", "Thành thạo công nghệ"],
        caliper_factor=0.60
    )

    assert result["status"] == "SUCCESS"
    assert result["sample_size"] == 24
    assert result["sample_treated"] == 12
    assert result["sample_control"] == 12
    assert result["matched_pairs_count"] > 0
    assert result["caliper_width"] > 0

    # Unadjusted difference is confounded and larger than true effect
    assert result["unadjusted_effect"]["difference"] > 2.0

    # Matched ATT should be around ~2.0
    matched_att = result["matched_att"]
    assert "estimate" in matched_att
    assert "p_value" in matched_att
    assert matched_att["estimate"] > 1.0
    assert matched_att["is_significant"] is True

    # IPW ATT should also be positive and significant
    ipw_att = result["ipw_att"]
    assert "estimate" in ipw_att
    assert ipw_att["estimate"] > 1.0

    # Covariate balance
    assert len(result["covariate_balance"]) == 2
    for cb in result["covariate_balance"]:
        assert "smd_pre" in cb
        assert "smd_post" in cb
        assert "variance_ratio_post" in cb
        assert "bias_reduction_pct" in cb

    # Summary and Love Plot
    assert "balance_summary" in result
    assert result["balance_summary"]["total_covariates_count"] == 2
    assert len(result["love_plot"]) == 2
    assert len(result["common_support_overlap"]) == 10

    # APA Narrative
    assert "Rosenbaum & Rubin" in result["apa_narrative"]
    assert "Austin, 2011" in result["apa_narrative"]


def test_psm_engine_insufficient_samples():
    records = [
        {"treatment": 1, "outcome": 5.0, "covariates": [2.0]},
        {"treatment": 0, "outcome": 4.0, "covariates": [1.0]},
    ]
    result = PSMEngine.analyze_propensity_matching(
        records=records,
        treatment_name="T",
        outcome_name="Y",
        covariate_names=["X"]
    )
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["sample_size"] == 0
    assert "Cỡ mẫu quá nhỏ" in result["apa_narrative"]
