"""
Unit tests for Moderated Mediation & Conditional Indirect Effects Engine (PROCESS Model 7).
"""

import math
import random
import pytest
from app.engine.moderated_mediation_engine import ModeratedMediationEngine


def test_moderated_mediation_insufficient_sample():
    """Kiểm tra mẫu quá nhỏ (N < 10)"""
    res = ModeratedMediationEngine.analyze_moderated_mediation(
        x=[1.0, 2.0, 3.0],
        m=[2.0, 3.0, 4.0],
        w=[3.0, 4.0, 5.0],
        y=[4.0, 5.0, 6.0]
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_moderated_mediation_zero_variance():
    """Kiểm tra biến hằng số (variance = 0)"""
    res = ModeratedMediationEngine.analyze_moderated_mediation(
        x=[1.0] * 12,
        m=[float(i) for i in range(12)],
        w=[float(i) for i in range(12)],
        y=[float(i) for i in range(12)]
    )
    assert res["status"] == "ZERO_VARIANCE"


def test_moderated_mediation_significant_model():
    """
    Kiểm tra mô hình có Moderated Mediation thực sự mạnh:
    Stage 1: M = 1 + 0.8*X + 0.4*W + 0.6*(X*W) + noise (a3 = 0.6)
    Stage 2: Y = 2 + 0.3*X + 0.7*M + noise (b = 0.7)
    Omega lý thuyết = a3 * b = 0.6 * 0.7 = 0.42
    """
    random.seed(123)
    n = 100
    x = [random.gauss(5, 1.5) for _ in range(n)]
    w = [random.gauss(10, 2.0) for _ in range(n)]

    mean_x = sum(x) / n
    mean_w = sum(w) / n
    x_c = [xi - mean_x for xi in x]
    w_c = [wi - mean_w for wi in w]

    m = [1.0 + 0.8 * x_c[i] + 0.4 * w_c[i] + 0.6 * (x_c[i] * w_c[i]) + random.gauss(0, 0.4) for i in range(n)]
    y = [2.0 + 0.3 * x[i] + 0.7 * m[i] + random.gauss(0, 0.4) for i in range(n)]

    res = ModeratedMediationEngine.analyze_moderated_mediation(
        x=x, m=m, w=w, y=y,
        center_variables=True,
        num_bootstrap=200,
        random_seed=42,
        x_label="Training",
        m_label="Self_Efficacy",
        w_label="Supervisory_Support",
        y_label="Performance"
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 100
    assert "index_of_moderated_mediation" in res
    omega = res["index_of_moderated_mediation"]["index_omega"]
    assert omega > 0.1
    assert "conditional_indirect_effects" in res
    assert len(res["conditional_indirect_effects"]) == 3
    # Hiệu ứng gián tiếp tại High W phải lớn hơn tại Low W do a3 > 0 và b > 0
    ind_low = res["conditional_indirect_effects"][0]["indirect_effect"]
    ind_high = res["conditional_indirect_effects"][2]["indirect_effect"]
    assert ind_high > ind_low
    assert "apa_narrative" in res
    assert "PROCESS Model 7" in res["apa_narrative"]
