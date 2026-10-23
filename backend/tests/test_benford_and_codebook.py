import pytest
from fastapi.testclient import TestClient
from app.engine.quality_engine import QualityEngine

def test_quality_engine_benford_analysis_deterministic():
    """
    Kiểm thử thuật toán Benford's Law trên tập dữ liệu số tự nhiên (chuẩn)
    và tập dữ liệu số ngụy tạo (đồng đều nhân tạo)
    """
    # 1. Tập số tự nhiên theo hàm lũy thừa: e.g. 2^x, 3^x (tuân thủ Benford chặt chẽ)
    natural_numbers = [2.0 ** i for i in range(1, 100)]
    result_natural = QualityEngine.compute_benford_analysis(natural_numbers)
    assert result_natural["total_numeric_samples"] == 99
    assert result_natural["is_sample_sufficient"] is True
    # Tập tự nhiên phải có chi-square thấp (< 15.51) và không bị gắn cờ
    assert result_natural["is_anomalous"] is False

    # 2. Tập số bịa đặt nhân tạo: con người chọn số đầu đều nhau từ 4 đến 9
    fabricated_numbers = []
    for _ in range(20):
        fabricated_numbers.extend([450.0, 520.0, 680.0, 710.0, 890.0, 930.0])
    result_fabricated = QualityEngine.compute_benford_analysis(fabricated_numbers)
    assert result_fabricated["total_numeric_samples"] == 120
    # Tập bịa đặt thiếu chữ số 1, 2, 3 nên chi-square sẽ rất cao (> 20.09) và bị gắn cờ bất thường
    assert result_fabricated["chi_square_statistic"] > 20.09
    assert result_fabricated["is_anomalous"] is True

def test_survey_benford_and_codebook_endpoints(client: TestClient):
    """
    Kiểm thử các API Benford analysis và Academic Codebook (SPSS/R)
    """
    # 1. Tạo khảo sát mẫu có câu hỏi số và câu hỏi trắc nghiệm
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Nghiên cứu Thu nhập & Chi tiêu",
        "description": "Thử nghiệm Benford Law và Codebook SPSS"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    q1_id = "q_brand_choice"
    q2_id = "q_monthly_income"

    up_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": q1_id,
                "question_type": "single_choice",
                "title": "Thương hiệu sử dụng chính",
                "order_index": 0,
                "is_required": True,
                "options": [
                    {"id": "opt_vf", "label": "VinFast"},
                    {"id": "opt_ty", "label": "Toyota"},
                    {"id": "opt_hd", "label": "Honda"}
                ],
                "logic_rules": []
            },
            {
                "id": q2_id,
                "question_type": "number",
                "title": "Thu nhập hàng tháng (triệu VNĐ)",
                "order_index": 1,
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert up_res.status_code == 200

    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    slug = pub_res.json()["public_slug"]

    # Nộp 35 phản hồi với số liệu để kiểm định Benford
    for i in range(35):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": "2026-10-23T08:00:00Z",
            "submitted_at": "2026-10-23T08:00:25Z",
            "duration_seconds": 25.0,
            "answers": {
                q1_id: "opt_vf" if i % 2 == 0 else "opt_ty",
                q2_id: str((i + 1) * 12.5) # Numbers like 12.5, 25.0, 37.5...
            }
        })

    # 2. Kiểm tra API Benford
    ben_res = client.get(f"/api/surveys/{survey_id}/analytics/benford")
    assert ben_res.status_code == 200
    ben_data = ben_res.json()
    assert ben_data["total_numeric_samples"] == 35
    assert ben_data["is_sample_sufficient"] is True
    assert len(ben_data["distribution"]) == 9

    # 3. Kiểm tra API Codebook JSON
    cb_res = client.get(f"/api/surveys/{survey_id}/codebook?format=json")
    assert cb_res.status_code == 200
    cb_data = cb_res.json()
    assert cb_data["total_variables"] == 2
    assert cb_data["variables"][0]["variable_name"] == "VAR001"
    assert cb_data["variables"][0]["measurement_level"] == "Nominal"
    assert "VinFast" in str(cb_data["variables"][0]["value_labels"])
    assert cb_data["variables"][1]["variable_name"] == "VAR002"
    assert cb_data["variables"][1]["measurement_level"] == "Scale"
    assert "VARIABLE LABELS" in cb_data["spss_syntax"]

    # 4. Kiểm tra API Codebook tải cú pháp SPSS
    spss_res = client.get(f"/api/surveys/{survey_id}/codebook?format=spss")
    assert spss_res.status_code == 200
    assert "text/plain" in spss_res.headers["content-type"]
    assert "VARIABLE LABELS" in spss_res.text
    assert "MISSING VALUES ALL (999)." in spss_res.text
