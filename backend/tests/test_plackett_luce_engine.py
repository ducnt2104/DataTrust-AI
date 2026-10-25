import pytest
import numpy as np
from app.engine.plackett_luce_engine import PlackettLuceEngine


def test_plackett_luce_engine_success():
    # 40 respondents ranking 4 items: Option A, B, C, D
    # True preference: A > B > C > D
    np.random.seed(42)
    N = 40
    rankings = []
    for _ in range(N):
        # Mostly [0, 1, 2, 3] with slight noise
        if np.random.rand() < 0.75:
            rankings.append([0, 1, 2, 3])
        elif np.random.rand() < 0.5:
            rankings.append([1, 0, 2, 3])
        else:
            rankings.append([0, 2, 1, 3])

    items = ["Feature Alpha (Speed)", "Feature Beta (Security)", "Feature Gamma (UI)", "Feature Delta (Reports)"]

    res = PlackettLuceEngine.compute_ranking_choice(
        rankings_data=rankings,
        item_names=items
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "PLACKETT_LUCE_RANK_ORDERED_LOGIT"
    diag = res["diagnostics"]
    assert diag["sample_size"] == 40
    assert diag["n_items"] == 4
    assert diag["converged"] is True
    assert diag["mcfadden_pseudo_r2"] > 0.10

    # Check items
    res_items = res["items"]
    assert len(res_items) == 4
    assert res_items[0]["item_name"] == "Feature Alpha (Speed)"
    total_worth = sum(d["worth_percentage"] for d in res_items)
    assert abs(total_worth - 100.0) < 0.5

    # Check pairwise win probability
    pw = res["pairwise_win_matrix"]
    assert len(pw) == 4
    assert pw[0][3] > 0.70  # Alpha vs Delta

    # Check SVG and APA
    assert "<svg" in res["svg_visualization"]
    assert "APA 7th Edition" in res["apa_narrative"]
    assert "Hunter (2004)" in res["apa_narrative"]


def test_plackett_luce_insufficient_sample():
    res = PlackettLuceEngine.compute_ranking_choice(
        rankings_data=[[0, 1], [1, 0]],
        item_names=["A", "B"]
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_plackett_luce_insufficient_items():
    res = PlackettLuceEngine.compute_ranking_choice(
        rankings_data=[[0] for _ in range(30)],
        item_names=["A"]
    )
    assert res["status"] == "INSUFFICIENT_ITEMS"
