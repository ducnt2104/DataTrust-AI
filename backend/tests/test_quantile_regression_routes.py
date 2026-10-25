import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_quantile_regression_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Hồi quy Phân vị (Koenker & Bassett 1978, Koenker 2005)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/quantile-regression", json={
        "predictor_question_id": "q1",
        "outcome_question_id": "q2"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Phân phối Điểm Thưởng & Hiệu suất Nhân viên (Quantile Regression)",
        "description": "Kiểm định hồi quy phân vị đa ngưỡng tau"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 2 câu hỏi số
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Phân phối Điểm Thưởng & Hiệu suất Nhân viên (Quantile Regression)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Mức độ khuyến khích tài chính (Triệu VNĐ)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Năng suất đầu ra (Điểm KPI 1-10)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 2
    q_bonus = questions[0]["id"]
    q_kpi = questions[1]["id"]

    # 4. Khi chưa có dữ liệu phản hồi (< 16)
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/quantile-regression", json={
        "predictor_question_id": q_bonus,
        "outcome_question_id": q_kpi
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 5. Sinh 24 phản hồi có phân phối dị phương sai (Heteroskedastic)
    now = datetime.now(timezone.utc)
    for i in range(24):
        bonus_val = 2.0 + i * 0.8
        # Phân vị cao hưởng lợi nhiều hơn từ bonus
        kpi_val = max(1.0, min(10.0, 3.0 + 0.3 * bonus_val + (0.1 * (i % 5)) * bonus_val))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=600 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_bonus: bonus_val,
                q_kpi: kpi_val
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API hồi quy phân vị với các ngưỡng [0.10, 0.25, 0.50, 0.75, 0.90]
    res_qr = client.post(f"/api/surveys/{survey_id}/analytics/quantile-regression", json={
        "predictor_question_id": q_bonus,
        "outcome_question_id": q_kpi,
        "quantiles": [0.10, 0.25, 0.50, 0.75, 0.90],
        "scope": "all"
    })
    assert res_qr.status_code == 200
    data = res_qr.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 24
    assert len(data["quantile_estimates"]) == 5
    assert "ols_baseline" in data
    assert "heterogeneity_test" in data
    assert "svg_process_plot" in data
    assert "<svg" in data["svg_process_plot"]
    assert "apa_narrative" in data
    assert "Quantile Regression" in data["apa_narrative"]

    # 7. Kiểm tra audit log
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    actions = [evt["action"] for evt in events]
    assert "QUANTILE_REGRESSION_EVALUATED" in actions
