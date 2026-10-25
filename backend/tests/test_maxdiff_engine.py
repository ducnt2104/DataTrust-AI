import pytest
import numpy as np
from app.engine.maxdiff_engine import MaxDiffEngine


def test_maxdiff_engine_success():
    np.random.seed(42)
    # 4 items: Feature A, B, C, D
    # True utilities: A > B > C > D
    items = ["AI Summarization (A)", "Export to PDF (B)", "Dark Mode Theme (C)", "Legacy Fax Support (D)"]
    M = 4
    tasks = []

    # 40 tasks comparing 3 items out of 4
    for i in range(40):
        # Choose 3 distinct items
        avail = sorted(list(np.random.choice(4, size=3, replace=False)))
        # In this task, best is the lowest index (highest utility), worst is highest index
        best_item = avail[0]
        worst_item = avail[-1]
        # Introduce 10% random noise
        if np.random.rand() < 0.10:
            best_item, worst_item = worst_item, best_item

        tasks.append({
            "available_items": avail,
            "best_item": best_item,
            "worst_item": worst_item
        })

    res = MaxDiffEngine.compute_maxdiff(
        tasks_data=tasks,
        item_names=items
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "MAXDIFF_BEST_WORST_SCALING"
    diag = res["diagnostics"]
    assert diag["n_tasks"] == 40
    assert diag["n_items"] == 4
    assert diag["converged"] is True

    # Items check
    res_items = res["items"]
    assert len(res_items) == 4
    total_share = sum(it["preference_share_pct"] for it in res_items)
    assert abs(total_share - 100.0) < 0.5
    # Feature A should be top ranked
    assert res_items[0]["item_name"] == "AI Summarization (A)"
    assert res_items[0]["preference_share_pct"] > res_items[-1]["preference_share_pct"]

    # Visualizations and narrative
    assert "<svg" in res["svg_visualization"]
    assert "APA 7th Edition" in res["apa_narrative"]
    assert "Marley & Louviere" in res["apa_narrative"]


def test_maxdiff_insufficient_sample():
    res = MaxDiffEngine.compute_maxdiff(
        tasks_data=[{"available_items": [0, 1, 2], "best_item": 0, "worst_item": 2}],
        item_names=["A", "B", "C"]
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_maxdiff_insufficient_items():
    res = MaxDiffEngine.compute_maxdiff(
        tasks_data=[{"available_items": [0, 1], "best_item": 0, "worst_item": 1} for _ in range(20)],
        item_names=["A", "B"]
    )
    assert res["status"] == "INSUFFICIENT_ITEMS"
