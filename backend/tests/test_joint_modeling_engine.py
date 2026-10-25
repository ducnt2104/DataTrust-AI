import pytest
import numpy as np
from app.engine.joint_modeling_engine import JointModelingEngine


def test_joint_modeling_engine_success():
    np.random.seed(42)
    n_subjects = 25
    long_records = []
    surv_records = []

    for sid in range(1, n_subjects + 1):
        # True random intercept and slope
        b0 = float(np.random.normal(0, 0.5))
        b1 = float(np.random.normal(0, 0.2))

        # Attrition probability linked to b0 (lower b0 -> higher chance of dropping out)
        drop_hazard = 1.0 / (1.0 + np.exp(b0))
        is_attrited = 1 if np.random.uniform() < drop_hazard else 0
        event_time = float(np.random.uniform(1.5, 4.0)) if is_attrited else 4.0

        surv_records.append({
            "subject_id": str(sid),
            "event_time": event_time,
            "event": is_attrited
        })

        # Generate longitudinal observations at waves 1, 2, 3, 4 (only if wave <= event_time)
        for wave in [1.0, 2.0, 3.0, 4.0]:
            if wave <= event_time + 0.5:
                y_val = 10.0 + b0 + (0.5 + b1) * wave + float(np.random.normal(0, 0.3))
                long_records.append({
                    "subject_id": str(sid),
                    "time": wave,
                    "y": y_val
                })

    res = JointModelingEngine.estimate(
        longitudinal_records=long_records,
        survival_records=surv_records
    )

    assert res["status"] == "success"
    assert res["sample_size"] == n_subjects
    assert res["total_longitudinal_observations"] >= 40
    assert "intercept_fixed" in res["longitudinal_submodel"]
    assert "association_alpha" in res["survival_submodel"]
    assert "hazard_ratio" in res["survival_submodel"]
    assert len(res["dynamic_predictions"]) > 5
    assert "<svg" in res["svg_chart"]
    assert "Joint Modeling" in res["apa_narrative"] or "Wulfsohn" in res["apa_narrative"]


def test_joint_modeling_engine_insufficient_sample():
    # Only 3 subjects
    long_records = [
        {"subject_id": "1", "time": 1.0, "y": 5.0},
        {"subject_id": "2", "time": 1.0, "y": 6.0},
        {"subject_id": "3", "time": 1.0, "y": 7.0}
    ]
    surv_records = [
        {"subject_id": "1", "event_time": 2.0, "event": 1},
        {"subject_id": "2", "event_time": 2.0, "event": 0},
        {"subject_id": "3", "event_time": 2.0, "event": 0}
    ]

    res = JointModelingEngine.estimate(long_records, surv_records)
    assert res["status"] == "error"
    assert "Cỡ mẫu quá nhỏ" in res["message"]


def test_joint_modeling_engine_empty_data():
    res = JointModelingEngine.estimate([], [])
    assert res["status"] == "error"
    assert "không đủ" in res["message"]
