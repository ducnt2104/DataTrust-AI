import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_lca_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Lớp Ẩn (Latent Class Analysis - LCA)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/lca", json={
        "item_question_ids": ["none1", "none2", "none3"]
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Phân Đoạn Khách Hàng Bằng Mô Hình Lớp Ẩn LCA",
        "description": "Nghiên cứu phân đoạn khách hàng theo hành vi và thái độ sử dụng số"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Cập nhật 3 câu hỏi chỉ báo phân đoạn
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Phân Đoạn Khách Hàng Bằng Mô Hình Lớp Ẩn LCA",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Tần suất mua sắm trực tuyến",
                "is_required": True,
                "options": ["Thường xuyên", "Hiếm khi"],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Mức chi tiêu công nghệ hàng tháng",
                "is_required": True,
                "options": ["Cao (>5M)", "Thấp (<5M)"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "single_choice",
                "title": "Thái độ với tính năng trí tuệ nhân tạo",
                "is_required": True,
                "options": ["Hào hứng đón nhận", "Thận trọng do dự"],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # Lấy ID câu hỏi từ public API
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q1_id = public_q[0]["id"]
    q2_id = public_q[1]["id"]
    q3_id = public_q[2]["id"]

    # 4. Khi chưa đủ dữ liệu (< 10 phản hồi)
    insufficient_res = client.post(f"/api/surveys/{survey_id}/analytics/lca", json={
        "item_question_ids": [q1_id, q2_id, q3_id]
    })
    assert insufficient_res.status_code == 200
    ins_data = insufficient_res.json()
    assert ins_data["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Gửi 12 phản hồi (6 người thuộc phân đoạn Digital-First, 6 người thuộc phân đoạn Traditional)
    now = datetime.now(timezone.utc)
    dataset = [
        # Phân đoạn 1: Digital-First (6 người)
        ("Thường xuyên", "Cao (>5M)", "Hào hứng đón nhận"),
        ("Thường xuyên", "Cao (>5M)", "Hào hứng đón nhận"),
        ("Thường xuyên", "Cao (>5M)", "Thận trọng do dự"),
        ("Thường xuyên", "Cao (>5M)", "Hào hứng đón nhận"),
        ("Thường xuyên", "Cao (>5M)", "Hào hứng đón nhận"),
        ("Thường xuyên", "Thấp (<5M)", "Hào hứng đón nhận"),
        # Phân đoạn 2: Traditional (6 người)
        ("Hiếm khi", "Thấp (<5M)", "Thận trọng do dự"),
        ("Hiếm khi", "Thấp (<5M)", "Thận trọng do dự"),
        ("Hiếm khi", "Cao (>5M)", "Thận trọng do dự"),
        ("Hiếm khi", "Thấp (<5M)", "Thận trọng do dự"),
        ("Hiếm khi", "Thấp (<5M)", "Thận trọng do dự"),
        ("Hiếm khi", "Thấp (<5M)", "Hào hứng đón nhận"),
    ]

    for i, (ans1, ans2, ans3) in enumerate(dataset):
        dur = 50 + i * 12
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q1_id: ans1,
                q2_id: ans2,
                q3_id: ans3
            },
            "client_metadata": {
                "user_agent": f"LCA Respondent {i}"
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API phân tích Lớp Ẩn LCA
    lca_res = client.post(f"/api/surveys/{survey_id}/analytics/lca", json={
        "item_question_ids": [q1_id, q2_id, q3_id],
        "num_classes": 2,
        "scope": "all"
    })
    assert lca_res.status_code == 200
    res_data = lca_res.json()

    assert res_data["status"] == "SUCCESS"
    assert res_data["sample_size"] == 12
    assert res_data["items_count"] == 3
    assert res_data["optimal_classes_count"] == 2
    assert res_data["entropy"] > 0.60
    assert len(res_data["class_profiles"]) == 2
    assert "<svg" in res_data["svg_profile_plot"]
    assert "apa_narrative" in res_data
    assert "Latent Class Analysis" in res_data["apa_narrative"]

    # 7. Kiểm tra audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "LCA_MODEL_EVALUATED" in actions
