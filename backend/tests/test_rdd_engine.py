import pytest
import numpy as np
from app.engine.rdd_engine import RDDEngine


def test_sharp_rdd_basic():
    """Kiểm thử mô hình Sharp RDD với bước nhảy gián đoạn nhân quả thực sự tại c = 50."""
    np.random.seed(42)
    n = 120
    x = np.random.uniform(20.0, 80.0, n)
    c = 50.0
    # True treatment jump tau = 3.5 tại x >= 50
    treated = (x >= c).astype(float)
    y = 5.0 + 0.3 * (x - c) + 3.5 * treated + np.random.normal(0, 0.5, n)

    data_rows = [{"score": float(x[i]), "outcome": float(y[i])} for i in range(n)]

    res = RDDEngine.fit_sharp_rdd(
        data_rows=data_rows,
        running_key="score",
        outcome_key="outcome",
        cutoff=c,
        labels={"score": "Điểm kiểm tra đầu vào", "outcome": "Thu nhập sau tốt nghiệp"}
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == n
    assert res["cutoff_threshold"] == c
    assert res["bandwidth"] > 0
    assert res["effective_sample_size"] > 10

    late = res["treatment_effect_late"]
    # Ước lượng bước nhảy phải gần 3.5
    assert 2.0 < late["tau_rdd"] < 5.0
    assert late["is_significant"] is True
    assert late["p_value"] < 0.05

    # Kiểm định McCrary
    mccrary = res["mccrary_manipulation_test"]
    assert "has_manipulation" in mccrary
    assert mccrary["has_manipulation"] is False  # Dữ liệu phân bố đều nên không bị thao túng

    assert len(res["binned_scatter_points"]) >= 4
    assert "svg_chart" in res
    assert "<svg" in res["svg_chart"]
    assert "apa_narrative" in res
    assert "Thistlethwaite & Campbell" in res["apa_narrative"] or "Hahn et al." in res["apa_narrative"]


def test_sharp_rdd_edge_cases():
    # 1. Cỡ mẫu quá nhỏ < 20
    res_few = RDDEngine.fit_sharp_rdd(
        data_rows=[{"x": i, "y": i} for i in range(10)],
        running_key="x",
        outcome_key="y",
        cutoff=5.0
    )
    assert res_few["status"] == "INSUFFICIENT_SAMPLE"

    # 2. Ngưỡng phân loại quá lệch (< 5 quan sát ở một bên)
    res_unbalanced = RDDEngine.fit_sharp_rdd(
        data_rows=[{"x": 1.0 + i * 0.1, "y": i} for i in range(30)],
        running_key="x",
        outcome_key="y",
        cutoff=10.0  # Tất cả đều < 10
    )
    assert res_unbalanced["status"] == "UNBALANCED_CUTOFF"
