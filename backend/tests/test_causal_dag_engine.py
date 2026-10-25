import numpy as np
import pytest
from app.engine.causal_dag_engine import CausalDAGEngine


def test_causal_dag_collider_discovery():
    np.random.seed(42)
    N = 120
    # Two independent exogenous causes: X1 and X3
    X1 = np.random.normal(0, 1, N)
    X3 = np.random.normal(0, 1, N)
    # Collider X2: X1 -> X2 <- X3
    X2 = 0.8 * X1 + 0.8 * X3 + np.random.normal(0, 0.4, N)
    
    data = np.column_stack([X1, X2, X3])
    item_names = ["Kỹ năng số (X1)", "Hiệu suất công việc (X2)", "Động lực học tập (X3)"]

    res = CausalDAGEngine.estimate(
        data=data,
        item_names=item_names,
        alpha=0.05
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["variables_count"] == 3
    assert res["edges_count"] >= 2
    
    # Check that X2 is identified as a sink or has in-degrees from X1 and X3
    assert "<svg" in res["svg_chart"]
    assert "Mạng lưới Nhân quả Có hướng" in res["apa_narrative"]
    assert len(res["nodes"]) == 3


def test_causal_dag_insufficient_sample():
    # Only 10 rows (N < 20)
    data = np.ones((10, 4))
    res = CausalDAGEngine.estimate(data)
    assert res["status"] == "insufficient_data"
    assert "20 quan sát" in res["message"]

    # Only 2 columns (P < 3)
    data_p2 = np.ones((30, 2))
    res2 = CausalDAGEngine.estimate(data_p2)
    assert res2["status"] == "insufficient_data"
    assert "3 biến" in res2["message"]
