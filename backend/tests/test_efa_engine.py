import pytest
from app.engine.efa_engine import EFAEngine

def test_efa_engine_math_primitives():
    # 1. Kiểm tra tính định thức
    matrix_diag = [[2.0, 0.0], [0.0, 3.0]]
    det = EFAEngine._determinant_gauss(matrix_diag)
    assert abs(det - 6.0) < 1e-6

    # 2. Kiểm tra trị riêng ma trận đường chéo
    evals, evecs = EFAEngine._jacobi_eigenvalues(matrix_diag)
    assert abs(evals[0] - 3.0) < 1e-6
    assert abs(evals[1] - 2.0) < 1e-6

    # 3. Kiểm tra xoay Varimax trên ma trận 4x2
    loadings = [
        [0.7, 0.2],
        [0.8, 0.1],
        [0.1, 0.75],
        [0.2, 0.85]
    ]
    rot = EFAEngine._varimax_rotation(loadings)
    assert len(rot) == 4
    assert len(rot[0]) == 2
    # Sau xoay, tải chính của từng biến phải phân lập rõ rệt
    assert abs(rot[0][0]) > abs(rot[0][1])
    assert abs(rot[2][1]) > abs(rot[2][0])

def test_efa_engine_insufficient_inputs():
    # 1. Dưới 3 biến thang đo
    res_vars = EFAEngine.analyze_survey_efa([], ["q1", "q2"])
    assert res_vars["status"] == "INSUFFICIENT_VARIABLES"

    # 2. Cỡ mẫu quá nhỏ
    dummy_records = [{"id": f"r{i}", "answers": {"q1": 1, "q2": 2, "q3": 3}} for i in range(5)]
    res_sample = EFAEngine.analyze_survey_efa(dummy_records, ["q1", "q2", "q3"])
    assert res_sample["status"] == "INSUFFICIENT_SAMPLE"

def test_efa_engine_two_factor_structure():
    # Tạo dữ liệu khảo sát 6 câu hỏi thuộc 2 nhân tố tiềm ẩn rõ rệt (F1: q1, q2, q3; F2: q4, q5, q6)
    # 30 phản hồi thực nghiệm
    records = []
    import random
    random.seed(42)

    for i in range(40):
        # Nhân tố 1: Trải nghiệm công nghệ (dao động cao hoặc thấp theo cá nhân)
        f1_base = random.choice([1.0, 2.0, 4.0, 5.0])
        # Nhân tố 2: Hỗ trợ cộng đồng (độc lập với f1)
        f2_base = random.choice([1.0, 2.0, 4.0, 5.0])

        q1 = max(1.0, min(5.0, f1_base + random.uniform(-0.4, 0.4)))
        q2 = max(1.0, min(5.0, f1_base + random.uniform(-0.4, 0.4)))
        q3 = max(1.0, min(5.0, f1_base + random.uniform(-0.4, 0.4)))

        q4 = max(1.0, min(5.0, f2_base + random.uniform(-0.4, 0.4)))
        q5 = max(1.0, min(5.0, f2_base + random.uniform(-0.4, 0.4)))
        q6 = max(1.0, min(5.0, f2_base + random.uniform(-0.4, 0.4)))

        records.append({
            "id": f"resp_{i}",
            "answers": {
                "q1": q1, "q2": q2, "q3": q3,
                "q4": q4, "q5": q5, "q6": q6
            }
        })

    scale_qids = ["q1", "q2", "q3", "q4", "q5", "q6"]
    result = EFAEngine.analyze_survey_efa(records, scale_qids, rotation="varimax")

    assert result["status"] == "SUCCESS"
    assert result["sample_size"] == 40
    assert result["variables_count"] == 6

    # KMO phải đạt chuẩn chấp nhận được
    assert result["kmo_overall"] >= 0.50
    assert result["is_kmo_acceptable"] is True

    # Kiểm định Bartlett phải có ý nghĩa p < 0.05
    assert result["bartlett_chi2"] > 0
    assert result["is_bartlett_significant"] is True

    # Phải trích xuất 2 nhân tố chính (Eigenvalues > 1.0)
    assert result["factors_extracted_count"] == 2
    assert len(result["factors"]) == 2

    # Tổng phương sai trích giải thích phải >= 50%
    assert result["cumulative_variance_extracted_pct"] >= 50.0

    # Phân nhóm: q1, q2, q3 phải cùng nhân tố chính; q4, q5, q6 phải cùng nhân tố chính khác
    item_map = {item["question_id"]: item for item in result["items"]}
    f_q1 = item_map["q1"]["primary_factor_index"]
    f_q2 = item_map["q2"]["primary_factor_index"]
    f_q3 = item_map["q3"]["primary_factor_index"]

    f_q4 = item_map["q4"]["primary_factor_index"]
    f_q5 = item_map["q5"]["primary_factor_index"]
    f_q6 = item_map["q6"]["primary_factor_index"]

    assert f_q1 == f_q2 == f_q3
    assert f_q4 == f_q5 == f_q6
    assert f_q1 != f_q4

    # Scree plot data
    assert len(result["scree_plot_data"]) == 6
    assert result["scree_plot_data"][0]["eigenvalue"] >= result["scree_plot_data"][1]["eigenvalue"]

    # Đoạn văn bản APA 7th Edition
    assert "KMO" in result["apa_interpretation"]
    assert "Bartlett" in result["apa_interpretation"]
