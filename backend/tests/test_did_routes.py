import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_did_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Khác biệt trong Khác biệt (DiD / TWFE)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/did", json={
        "outcome_question_id": "none1",
        "treatment_question_id": "none2",
        "time_question_id": "none3"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Tác Động Chính Sách Số Hóa (DiD)",
        "description": "Nghiên cứu đánh giá hiệu quả chương trình hỗ trợ chuyển đổi số"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Cập nhật 3 câu hỏi: Outcome (Y), Treatment (D), Time (T)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Tác Động Chính Sách Số Hóa (DiD)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Chỉ số năng suất lao động",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Nhóm tham gia chính sách",
                "is_required": True,
                "options": ["Nhóm Can Thiệp", "Nhóm Đối Chứng"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "single_choice",
                "title": "Thời điểm khảo sát",
                "is_required": True,
                "options": ["Trước Can Thiệp", "Sau Can Thiệp"],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # Lấy ID câu hỏi từ public API
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q_y_id = public_q[0]["id"]
    q_d_id = public_q[1]["id"]
    q_t_id = public_q[2]["id"]

    # 4. Khi chưa đủ dữ liệu (< 8 phản hồi)
    insufficient_res = client.post(f"/api/surveys/{survey_id}/analytics/did", json={
        "outcome_question_id": q_y_id,
        "treatment_question_id": q_d_id,
        "time_question_id": q_t_id
    })
    assert insufficient_res.status_code == 200
    ins_data = insufficient_res.json()
    assert ins_data["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Gửi 16 phản hồi (4 ô 2x2, mỗi ô 4 người)
    # Control Pre: y = 2
    # Control Post: y = 3 (drift = +1)
    # Treat Pre: y = 2 (baseline ngang bằng)
    # Treat Post: y = 5 (can thiệp = +3, DiD effect = +2)
    now = datetime.now(timezone.utc)
    dataset = [
        # Control Pre (4)
        (2, "Nhóm Đối Chứng", "Trước Can Thiệp"),
        (2, "Nhóm Đối Chứng", "Trước Can Thiệp"),
        (2, "Nhóm Đối Chứng", "Trước Can Thiệp"),
        (3, "Nhóm Đối Chứng", "Trước Can Thiệp"),
        # Control Post (4)
        (3, "Nhóm Đối Chứng", "Sau Can Thiệp"),
        (3, "Nhóm Đối Chứng", "Sau Can Thiệp"),
        (3, "Nhóm Đối Chứng", "Sau Can Thiệp"),
        (4, "Nhóm Đối Chứng", "Sau Can Thiệp"),
        # Treat Pre (4)
        (2, "Nhóm Can Thiệp", "Trước Can Thiệp"),
        (2, "Nhóm Can Thiệp", "Trước Can Thiệp"),
        (2, "Nhóm Can Thiệp", "Trước Can Thiệp"),
        (3, "Nhóm Can Thiệp", "Trước Can Thiệp"),
        # Treat Post (4)
        (5, "Nhóm Can Thiệp", "Sau Can Thiệp"),
        (5, "Nhóm Can Thiệp", "Sau Can Thiệp"),
        (5, "Nhóm Can Thiệp", "Sau Can Thiệp"),
        (5, "Nhóm Can Thiệp", "Sau Can Thiệp"),
    ]

    for i, (y_val, d_val, t_val) in enumerate(dataset):
        dur = 45 + i * 10
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 15)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 15)).isoformat(),
            "answers": {
                q_y_id: y_val,
                q_d_id: d_val,
                q_t_id: t_val
            },
            "client_metadata": {
                "user_agent": f"DiD Respondent {d_val[:3]} {i}"
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API phân tích DiD
    did_res = client.post(f"/api/surveys/{survey_id}/analytics/did", json={
        "outcome_question_id": q_y_id,
        "treatment_question_id": q_d_id,
        "time_question_id": q_t_id,
        "treatment_value": "Nhóm Can Thiệp",
        "post_value": "Sau Can Thiệp",
        "scope": "all"
    })
    assert did_res.status_code == 200
    res_data = did_res.json()

    assert res_data["status"] == "SUCCESS"
    assert res_data["sample_size"] == 16
    assert res_data["did_treatment_effect"]["att_estimate"] > 0
    assert res_data["cell_means_2x2"]["counterfactual_post"] > 0
    assert "<svg" in res_data["svg_trajectory_chart"]
    assert "apa_narrative" in res_data
    assert "Difference-in-Differences" in res_data["apa_narrative"]
    assert "Card & Krueger" in res_data["apa_narrative"]

    # 7. Kiểm tra audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "DID_MODEL_EVALUATED" in actions
