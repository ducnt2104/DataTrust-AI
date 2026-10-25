import pytest
import math
from app.engine.mahalanobis_engine import MahalanobisEngine

def test_mahalanobis_matrix_inversion():
    # Kiểm tra đảo ma trận 2x2: [[4, 2], [2, 2]]
    # Det = 8 - 4 = 4. Inv = [[2/4, -2/4], [-2/4, 4/4]] = [[0.5, -0.5], [-0.5, 1.0]]
    mat = [[4.0, 2.0], [2.0, 2.0]]
    inv = MahalanobisEngine._invert_matrix_gauss_jordan(mat)
    assert inv is not None
    assert abs(inv[0][0] - 0.5) < 1e-6
    assert abs(inv[0][1] - (-0.5)) < 1e-6
    assert abs(inv[1][0] - (-0.5)) < 1e-6
    assert abs(inv[1][1] - 1.0) < 1e-6

def test_mahalanobis_chi2_p_value():
    # Cho df = 2, giá trị critical chi2 ở mức alpha=0.05 xấp xỉ 5.991
    p_val_05 = MahalanobisEngine._chi2_p_value(5.991, df=2)
    assert abs(p_val_05 - 0.05) < 0.01

    # Cho df = 1, chi2 = 3.841 có p xấp xỉ 0.05
    p_val_1 = MahalanobisEngine._chi2_p_value(3.841, df=1)
    assert abs(p_val_1 - 0.05) < 0.01

def test_mahalanobis_multivariate_outlier_detection():
    # Tạo 25 phản hồi mẫu bình thường: q1 và q2 tương quan thuận (x, x + noise)
    records = []
    scale_vars = ["q1", "q2", "q3"]

    for i in range(25):
        val1 = 2.0 + (i % 3)
        val2 = val1 + 0.5
        val3 = val1 - 0.2
        records.append({
            "id": f"resp_normal_{i}",
            "answers": {"q1": str(val1), "q2": str(val2), "q3": str(val3)},
            "duration_seconds": 90.0,
            "risk_score": 10.0,
            "review_status": "verified_valid"
        })

    # Thêm 1 phản hồi dị biệt cực đoan: q1 cực thấp nhưng q2 cực cao
    records.append({
        "id": "resp_outlier_extreme",
        "answers": {"q1": "1.0", "q2": "5.0", "q3": "5.0"},
        "duration_seconds": 15.0,
        "risk_score": 60.0,
        "review_status": "under_review"
    })

    res = MahalanobisEngine.compute_mahalanobis_distances(records, scale_vars)
    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 26
    assert res["degrees_of_freedom"] == 3

    # Phản hồi dị biệt phải đứng ở vị trí số 1 (D^2 lớn nhất)
    top_outlier = res["outliers_summary"][0]
    assert top_outlier["response_id"] == "resp_outlier_extreme"
    assert top_outlier["d2_mahalanobis"] > res["mean_d2"]
    assert top_outlier["is_outlier"] is True
    assert "apa_interpretation" in res

def test_mahalanobis_insufficient_sample():
    # Khi mẫu N < p + 1
    records = [
        {"id": "r1", "answers": {"q1": "1", "q2": "2", "q3": "3"}}
    ]
    res = MahalanobisEngine.compute_mahalanobis_distances(records, ["q1", "q2", "q3"])
    assert res["status"] == "INSUFFICIENT_SAMPLE"
