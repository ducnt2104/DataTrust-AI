import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_multilevel_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Mô hình Tuyến tính Thứ bậc Đa cấp (HLM / MLM)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/multilevel", json={
        "outcome_question_id": "none"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Hiệu Suất Đa Cấp Theo Chi Nhánh",
        "description": "Kiểm định mô hình HLM 2 tầng (Nhân viên lồng trong Chi nhánh)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Cập nhật 3 câu hỏi: Cluster (C), Predictor (X), Outcome (Y)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Hiệu Suất Đa Cấp Theo Chi Nhánh",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Chi nhánh làm việc",
                "is_required": True,
                "options": ["Chi nhánh Hà Nội", "Chi nhánh Đà Nẵng", "Chi nhánh TP.HCM"],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Thời lượng đào tạo kỹ năng số",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Chỉ số hiệu suất công việc",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # Lấy ID câu hỏi từ public API
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q_c_id = public_q[0]["id"]
    q_x_id = public_q[1]["id"]
    q_y_id = public_q[2]["id"]

    # 4. Khi chưa đủ dữ liệu (< 8 phản hồi)
    insufficient_res = client.post(f"/api/surveys/{survey_id}/analytics/multilevel", json={
        "outcome_question_id": q_y_id,
        "predictor_question_id": q_x_id,
        "cluster_question_id": q_c_id
    })
    assert insufficient_res.status_code == 200
    ins_data = insufficient_res.json()
    assert ins_data["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Sinh 12 phản hồi mẫu phân bố đều qua 3 chi nhánh với phương sai giữa các cụm
    now = datetime.now(timezone.utc)
    dataset = [
        # Hà Nội (4 nhân viên)
        ("Chi nhánh Hà Nội", 2, 4),
        ("Chi nhánh Hà Nội", 3, 4),
        ("Chi nhánh Hà Nội", 4, 5),
        ("Chi nhánh Hà Nội", 5, 5),
        # Đà Nẵng (4 nhân viên)
        ("Chi nhánh Đà Nẵng", 1, 2),
        ("Chi nhánh Đà Nẵng", 2, 3),
        ("Chi nhánh Đà Nẵng", 3, 3),
        ("Chi nhánh Đà Nẵng", 4, 4),
        # TP.HCM (4 nhân viên)
        ("Chi nhánh TP.HCM", 2, 3),
        ("Chi nhánh TP.HCM", 3, 4),
        ("Chi nhánh TP.HCM", 4, 4),
        ("Chi nhánh TP.HCM", 5, 5),
    ]

    for i, (cluster_val, x_val, y_val) in enumerate(dataset):
        dur = 60 + i * 15
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_c_id: cluster_val,
                q_x_id: x_val,
                q_y_id: y_val
            },
            "client_metadata": {
                "user_agent": f"Branch Employee {cluster_val[:4]} {i}"
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API phân tích Multilevel HLM với scope="all"
    mlm_res = client.post(f"/api/surveys/{survey_id}/analytics/multilevel", json={
        "outcome_question_id": q_y_id,
        "predictor_question_id": q_x_id,
        "cluster_question_id": q_c_id,
        "scope": "all"
    })
    assert mlm_res.status_code == 200
    res_data = mlm_res.json()

    assert res_data["status"] == "SUCCESS"
    assert res_data["total_sample_size"] == 12
    assert res_data["num_clusters"] == 3
    assert res_data["null_model"]["icc"] >= 0.0
    assert res_data["null_model"]["icc_tier"] in ["LOW", "MODERATE", "HIGH"]
    assert "fixed_effects" in res_data
    assert "random_effects" in res_data
    assert len(res_data["cluster_trajectories"]) == 3
    assert res_data["grand_trajectory_path"] is not None
    assert "apa_narrative" in res_data
    assert "Mô hình tuyến tính thứ bậc đa cấp" in res_data["apa_narrative"]
    assert "ICC" in res_data["apa_narrative"]

    # 7. Kiểm tra audit trail ghi nhận sự kiện MULTILEVEL_MODEL_EVALUATED
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "MULTILEVEL_MODEL_EVALUATED" in actions
