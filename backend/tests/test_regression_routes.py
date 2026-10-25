import pytest
import random
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_regression_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/regression", json={
        "dependent_question_id": "dep_q",
        "predictor_question_ids": ["pred_1"]
    })
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thực nghiệm hồi quy
    create_res = client.post("/api/surveys", json={
        "title": "Mô Hình Hồi Quy Tuyến Tính Dự Báo Điểm Học Tập",
        "description": "Nghiên cứu tác động của thời gian tự học và thảo luận nhóm",
        "instructions": "Vui lòng cho biết thời gian và kết quả"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo câu hỏi: 1 biến phụ thuộc (Y) và 2 biến độc lập (X1, X2)
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Mô Hình Hồi Quy Tuyến Tính Dự Báo Điểm Học Tập",
        "questions": [
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Thời gian tự học (giờ/tuần)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ tích cực thảo luận nhóm (1-5)",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Điểm kiểm tra định kỳ (Thang 10)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    x1_id = public_q[0]["id"]
    x2_id = public_q[1]["id"]
    y_id = public_q[2]["id"]

    # 4. Kiểm tra validate lỗi trùng biến hoặc rỗng
    res_bad = client.post(f"/api/surveys/{survey_id}/analytics/regression", json={
        "dependent_question_id": y_id,
        "predictor_question_ids": [y_id]
    })
    assert res_bad.status_code == 400

    # 5. Gửi 20 phản hồi theo mô hình: y = 2.0 + 0.5 * x1 + 0.8 * x2 + noise
    random.seed(99)
    for i in range(20):
        val_x1 = 4.0 + (i % 10) * 1.5
        val_x2 = 1.0 + (i % 5)
        noise = random.uniform(-0.4, 0.4)
        val_y = round(2.0 + 0.5 * val_x1 + 0.8 * val_x2 + noise, 1)

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{i:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{i:02d}:50Z",
            "answers": {
                x1_id: str(val_x1),
                x2_id: str(val_x2),
                y_id: str(val_y)
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API Multiple Linear Regression OLS
    res_reg = client.post(f"/api/surveys/{survey_id}/analytics/regression", json={
        "dependent_question_id": y_id,
        "predictor_question_ids": [x1_id, x2_id],
        "scope": "all"
    })
    assert res_reg.status_code == 200
    data = res_reg.json()

    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 20
    assert data["predictors_count"] == 2
    assert data["model_summary"]["r_squared"] > 0.80
    assert data["model_summary"]["is_significant_05"] is True
    assert data["model_summary"]["f_stat"] > 10.0

    # Bảng ANOVA
    assert data["anova_table"]["df_regression"] == 2
    assert data["anova_table"]["df_residual"] == 17

    # Hệ số hồi quy: Intercept + 2 predictors
    assert len(data["coefficients"]) == 3
    # CONST
    assert data["coefficients"][0]["label"] == "CONST"
    # X1
    assert data["coefficients"][1]["b_unstandardized"] > 0.3
    assert data["coefficients"][1]["is_significant_05"] is True
    assert data["coefficients"][1]["vif"] < 5.0
    # X2
    assert data["coefficients"][2]["b_unstandardized"] > 0.4
    assert data["coefficients"][2]["is_significant_05"] is True
    assert data["coefficients"][2]["vif"] < 5.0

    # APA 7th Edition
    assert "R²" in data["apa_interpretation"]
    assert "F(2, 17)" in data["apa_interpretation"]
