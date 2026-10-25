"""
Unit tests for Statistical Moderation & Interaction Effects Engine (PROCESS Model 1).
"""

import math
import random
import pytest
from app.engine.moderation_engine import ModerationEngine


def test_moderation_insufficient_sample():
    """Kiểm tra mẫu quá nhỏ (N < 8)"""
    res = ModerationEngine.analyze_moderation(
        x=[1.0, 2.0, 3.0],
        w=[2.0, 3.0, 4.0],
        y=[3.0, 4.0, 5.0]
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_moderation_zero_variance():
    """Kiểm tra biến hằng số (variance = 0)"""
    res = ModerationEngine.analyze_moderation(
        x=[2.0] * 10,
        w=[float(i) for i in range(10)],
        y=[float(i * 2) for i in range(10)]
    )
    assert res["status"] == "ZERO_VARIANCE"


def test_moderation_significant_interaction():
    """
    Kiểm tra mô hình có hiệu ứng điều tiết thực sự mạnh:
    Y = 2 + 1*X + 0.5*W + 1.5*(X*W) + noise
    """
    random.seed(42)
    n = 100
    x = [random.gauss(5, 2) for _ in range(n)]
    w = [random.gauss(10, 3) for _ in range(n)]
    y = [2.0 + 1.0 * xi + 0.5 * wi + 1.5 * (xi * wi) + random.gauss(0, 0.5) for xi, wi in zip(x, w)]

    res = ModerationEngine.analyze_moderation(
        x=x, w=w, y=y,
        center_variables=True,
        x_label="Leadership",
        w_label="Tech_Readiness",
        y_label="Performance"
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 100
    assert "moderation_effect" in res
    assert res["moderation_effect"]["is_significant"] is True
    assert res["moderation_effect"]["delta_r_squared"] > 0
    assert "simple_slopes" in res
    assert len(res["simple_slopes"]) == 3
    # Độ dốc đơn tại High W phải lớn hơn tại Low W do b3 > 0
    slope_low = res["simple_slopes"][0]["slope"]
    slope_high = res["simple_slopes"][2]["slope"]
    assert slope_high > slope_low

    # Johnson-Neyman
    assert "johnson_neyman" in res
    assert "interaction_plot" in res
    assert len(res["interaction_plot"]["lines"]) == 3
    assert "apa_narrative" in res
    assert "PROCESS Model 1" in res["apa_narrative"]


def test_moderation_non_significant():
    """
    Kiểm tra mô hình không có hiệu ứng điều tiết:
    Y = 3 + 2*X + 1.5*W + noise (b3 = 0)
    """
    random.seed(99)
    n = 80
    x = [random.gauss(0, 1) for _ in range(n)]
    w = [random.gauss(0, 1) for _ in range(n)]
    y = [3.0 + 2.0 * xi + 1.5 * wi + random.gauss(0, 0.4) for xi, wi in zip(x, w)]

    res = ModerationEngine.analyze_moderation(
        x=x, w=w, y=y,
        center_variables=True
    )

    assert res["status"] == "SUCCESS"
    assert res["moderation_effect"]["is_significant"] is False
    assert res["moderation_effect"]["verdict_badge"] == "KHÔNG ĐIỀU TIẾT"
