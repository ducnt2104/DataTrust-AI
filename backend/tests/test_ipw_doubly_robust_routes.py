import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ipw_doubly_robust_routes_workflow():
    """Kiểm thử tích hợp luồng API Trọng số IPW và Ước lượng Vững Kép AIPW."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/ipw", json={
        "treatment_question_id": "q1",
        "outcome_question_id": "q2",
        "covariate_question_ids": ["q3"]
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Suy diễn Nhân quả Tác động Đào tạo (IPW & Doubly Robust)",
        "description": "Đánh giá can thiệp đào tạo bằng trọng số xác suất nghịch đảo"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 4 câu hỏi: Can thiệp (D), Kết quả (Y), Đồng biến 1 (X1), Đồng biến 2 (X2)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Suy diễn Nhân quả Tác động Đào tạo (IPW & Doubly Robust)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Can thiệp Đào tạo (1=Có, 0=Không)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Điểm Hiệu suất Đầu ra (1-5)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Kinh nghiệm Ban đầu (1-5)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Động lực Tự thân (1-5)",
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
    assert len(questions) == 4
    q_treat = questions[0]["id"]
    q_out = questions[1]["id"]
    q_cov1 = questions[2]["id"]
    q_cov2 = questions[3]["id"]

    # 4. Khi chưa có đủ phản hồi (< 16)
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/ipw", json={
        "treatment_question_id": q_treat,
        "outcome_question_id": q_out,
        "covariate_question_ids": [q_cov1, q_cov2]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 5. Sinh 24 phản hồi có can thiệp và hiệu quả
    now = datetime.now(timezone.utc)
    for i in range(24):
        dur = 60 + i * 10
        # Can thiệp: 1 cho nửa đầu, 0 cho nửa sau
        is_treated = 1 if i % 2 == 0 else 0
        cov1_val = 2 + (i % 4)
        cov2_val = 1 + (i % 5)
        # Outcome chịu tác động của treatment (+1.5) và covs
        out_val = min(5, max(1, 1 + is_treated * 2 + (cov1_val // 2)))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_treat: is_treated,
                q_out: out_val,
                q_cov1: cov1_val,
                q_cov2: cov2_val
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API ước lượng mô hình IPW / Doubly Robust (ATE)
    res_ate = client.post(f"/api/surveys/{survey_id}/analytics/ipw", json={
        "treatment_question_id": q_treat,
        "outcome_question_id": q_out,
        "covariate_question_ids": [q_cov1, q_cov2],
        "weight_scheme": "ate",
        "trim_weights": True,
        "scope": "all"
    })
    assert res_ate.status_code == 200
    data_ate = res_ate.json()
    assert data_ate["status"] == "SUCCESS"
    assert data_ate["sample_size"] == 24
    assert data_ate["treated_count"] == 12
    assert data_ate["control_count"] == 12
    assert data_ate["weight_scheme"] == "ATE"
    assert "doubly_robust_estimator" in data_ate
    assert "ipw_estimator" in data_ate
    assert "covariate_balance" in data_ate
    assert "svg_love_plot" in data_ate
    assert "<svg" in data_ate["svg_love_plot"]
    assert "apa_narrative" in data_ate

    # 7. Gọi API với lược đồ Overlap (ATO)
    res_overlap = client.post(f"/api/surveys/{survey_id}/analytics/ipw", json={
        "treatment_question_id": q_treat,
        "outcome_question_id": q_out,
        "covariate_question_ids": [q_cov1, q_cov2],
        "weight_scheme": "overlap"
    })
    assert res_overlap.status_code == 200
    assert res_overlap.json()["weight_scheme"] == "OVERLAP"

    # 8. Kiểm tra ghi vết kiểm toán (Audit Trail)
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    actions = [evt["action"] for evt in events]
    assert "IPW_DOUBLY_ROBUST_EVALUATED" in actions
