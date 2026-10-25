import pytest
import numpy as np
from app.engine.sem_engine import SEMEngine


def test_sem_mediation_model():
    """Kiểm thử mô hình trung gian 3 biến X -> M -> Y và X -> Y (Saturated mediation model)"""
    np.random.seed(42)
    n = 150
    x = np.random.normal(0, 1, n)
    m = 0.6 * x + np.random.normal(0, 0.5, n)
    y = 0.5 * m + 0.3 * x + np.random.normal(0, 0.5, n)

    data = [{"X": float(x[i]), "M": float(m[i]), "Y": float(y[i])} for i in range(n)]
    paths = [
        {"source": "X", "target": "M"},
        {"source": "M", "target": "Y"},
        {"source": "X", "target": "Y"}
    ]
    labels = {"X": "Chất lượng dịch vụ", "M": "Sự hài lòng", "Y": "Lòng trung thành"}

    res = SEMEngine.fit_path_analysis(data, paths, labels)

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 150
    assert set(res["observed_variables"]) == {"X", "M", "Y"}
    assert res["exogenous_variables"] == ["X"]
    assert set(res["endogenous_variables"]) == {"M", "Y"}

    # Kiểm tra 3 đường dẫn
    paths_out = res["paths"]
    assert len(paths_out) == 3
    for p in paths_out:
        assert p["is_significant"] is True
        assert p["p_value"] < 0.05
        assert p["standardized"] > 0

    # Kiểm tra phương trình hồi quy
    eqs = res["equations"]
    assert len(eqs) == 2
    for eq in eqs:
        assert eq["r_squared"] > 0.3
        assert eq["p_value"] < 0.001

    # Kiểm tra tác động gián tiếp (Mediation)
    ind_effects = res["indirect_effects"]
    assert len(ind_effects) == 1
    ind = ind_effects[0]
    assert ind["source"] == "X"
    assert ind["target"] == "Y"
    assert ind["path"] == ["X", "M", "Y"]
    assert ind["is_significant"] is True
    assert ind["unstandardized"] > 0

    # Kiểm tra tổng tác động (Total effects)
    tot_effects = res["total_effects"]
    tot_xy = next((t for t in tot_effects if t["source"] == "X" and t["target"] == "Y"), None)
    assert tot_xy is not None
    assert tot_xy["direct"] > 0
    assert tot_xy["indirect"] > 0
    assert round(tot_xy["total"], 3) == round(tot_xy["direct"] + tot_xy["indirect"], 3)

    # Kiểm tra fit indices (Saturated model df = 0)
    fits = res["fit_indices"]
    assert fits["df"] == 0
    assert fits["cfi"] == 1.0
    assert fits["is_good_fit"] is True

    # Kiểm tra SVG và APA
    assert "<svg" in res["svg_path_diagram"]
    assert "</svg>" in res["svg_path_diagram"]
    assert "Mô hình phương trình cấu trúc" in res["apa_narrative"]
    assert "Chất lượng dịch vụ" in res["apa_narrative"]


def test_sem_overidentified_chain_model():
    """Kiểm thử mô hình chuỗi X -> M -> Y không có đường trực tiếp (df = 1, over-identified)"""
    np.random.seed(123)
    n = 200
    x = np.random.normal(5, 1.5, n)
    m = 0.7 * x + np.random.normal(0, 0.4, n)
    y = 0.8 * m + np.random.normal(0, 0.4, n)

    data = [{"X": float(x[i]), "M": float(m[i]), "Y": float(y[i])} for i in range(n)]
    paths = [
        {"source": "X", "target": "M"},
        {"source": "M", "target": "Y"}
    ]

    res = SEMEngine.fit_path_analysis(data, paths)

    assert res["status"] == "SUCCESS"
    fits = res["fit_indices"]
    assert fits["df"] == 1
    assert fits["cfi"] >= 0.90
    assert fits["rmsea"] >= 0.0
    assert fits["srmr"] < 0.10


def test_sem_edge_cases():
    """Kiểm thử các trường hợp biên: rỗng, thiếu mẫu, biến không đổi"""
    # 1. Rỗng
    res_empty = SEMEngine.fit_path_analysis([], [])
    assert res_empty["status"] == "EMPTY_SPECIFICATION"

    # 2. Thiếu mẫu
    paths = [{"source": "A", "target": "B"}]
    data_few = [{"A": 1.0, "B": 2.0}, {"A": 2.0, "B": 3.0}]
    res_few = SEMEngine.fit_path_analysis(data_few, paths)
    assert res_few["status"] == "INSUFFICIENT_SAMPLE"

    # 3. Phương sai bằng 0
    data_zero_var = [{"A": 5.0, "B": float(i)} for i in range(20)]
    res_zero = SEMEngine.fit_path_analysis(data_zero_var, paths)
    assert res_zero["status"] == "ZERO_VARIANCE"
