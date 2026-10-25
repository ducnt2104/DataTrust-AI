import pytest
import numpy as np
from app.engine.msem_engine import MSEMEngine


def test_msem_insufficient_records():
    records = [{"cluster": "c1", "x": 1.0, "m": 2.0, "y": 3.0} for _ in range(10)]
    res = MSEMEngine.estimate_multilevel_mediation(
        records=records,
        cluster_field="cluster",
        x_field="x",
        m_field="m",
        y_field="y"
    )
    assert res["status"] == "error"
    assert "tối thiểu 20" in res["message"]


def test_msem_insufficient_clusters():
    # 30 records but only 2 clusters
    records = []
    for i in range(30):
        records.append({
            "cluster": f"c{i % 2}",
            "x": float(i),
            "m": float(i * 1.2),
            "y": float(i * 0.8)
        })
    res = MSEMEngine.estimate_multilevel_mediation(
        records=records,
        cluster_field="cluster",
        x_field="x",
        m_field="m",
        y_field="y"
    )
    assert res["status"] == "error"
    assert "tối thiểu 4 cụm" in res["message"]


def test_msem_valid_multilevel_mediation():
    np.random.seed(42)
    n_clusters = 10
    n_per_cluster = 8
    records = []

    # Cluster-level random components
    for j in range(n_clusters):
        cid = f"cluster_{j+1}"
        xb = float(np.random.normal(3.0, 1.0))
        mb = float(0.8 * xb + np.random.normal(0.0, 0.5))
        yb = float(1.2 * mb + 0.3 * xb + np.random.normal(0.0, 0.5))

        for i in range(n_per_cluster):
            xw = float(np.random.normal(0.0, 0.8))
            mw = float(0.5 * xw + np.random.normal(0.0, 0.4))
            yw = float(0.6 * mw + 0.2 * xw + np.random.normal(0.0, 0.4))

            records.append({
                "dept_id": cid,
                "leadership_support": xb + xw,
                "work_engagement": mb + mw,
                "performance_score": yb + yw
            })

    res = MSEMEngine.estimate_multilevel_mediation(
        records=records,
        cluster_field="dept_id",
        x_field="leadership_support",
        m_field="work_engagement",
        y_field="performance_score",
        n_mc_sims=1000,
        seed=42
    )

    assert res["status"] == "success"
    assert res["sample_diagnostics"]["n_total"] == 80
    assert res["sample_diagnostics"]["n_clusters"] == 10
    assert res["intraclass_correlations"]["icc_x"] > 0
    assert res["intraclass_correlations"]["icc_m"] > 0
    assert res["intraclass_correlations"]["icc_y"] > 0

    # Within submodel
    w_res = res["level1_within_submodel"]
    assert "a_path" in w_res
    assert "b_path" in w_res
    assert "indirect_effect" in w_res
    assert w_res["ci_95_lower"] < w_res["ci_95_upper"]

    # Between submodel
    b_res = res["level2_between_submodel"]
    assert "a_path" in b_res
    assert "b_path" in b_res
    assert "indirect_effect" in b_res
    assert b_res["ci_95_lower"] < b_res["ci_95_upper"]

    # Conflation test
    assert "diff_between_within" in res["conflation_test"]
    assert "<svg" in res["svg_chart"]
    assert "APA 7th Standard" in res["apa_narrative"]
