import pytest
import random
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

try:
    from app.main import app
except ModuleNotFoundError:
    from backend.app.main import app

client = TestClient(app)


def test_non_parametric_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/mann-whitney-u", json={
        "target_question_id": "t_id",
        "grouping_question_id": "g_id"
    })
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thực nghiệm phi tham số
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Phi Tham Số Đa Nhóm & Đo Lường Lặp",
        "description": "Kiểm định Mann-Whitney U, Wilcoxon Signed-Rank và Kruskal-Wallis"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 3 câu hỏi:
    # - q_dept: Biến phân loại (single_choice: IT, Sales, HR)
    # - q_sat_pre: Điểm hài lòng ban đầu (rating 1-5)
    # - q_sat_post: Điểm hài lòng sau cải tiến (rating 1-5)
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Phi Tham Số Đa Nhóm & Đo Lường Lặp",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Phòng ban công tác",
                "is_required": True,
                "options": [
                    {"id": "it", "label": "Công nghệ thông tin"},
                    {"id": "sales", "label": "Kinh doanh"},
                    {"id": "hr", "label": "Nhân sự"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Mức độ hài lòng quy trình ban đầu (1-5)",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ hài lòng quy trình sau cải tiến (1-5)",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    g_id = public_q[0]["id"]
    q_pre_id = public_q[1]["id"]
    q_post_id = public_q[2]["id"]

    # 4. Gửi 21 phản hồi hợp lệ phân bố trên 3 phòng ban
    random.seed(42)
    now = datetime.now(timezone.utc)

    # IT: pre trung bình 4, post 5
    # Sales: pre trung bình 2, post 4
    # HR: pre trung bình 3, post 4
    departments = ["Công nghệ thông tin"] * 7 + ["Kinh doanh"] * 7 + ["Nhân sự"] * 7

    for i, dept in enumerate(departments):
        if dept == "Công nghệ thông tin":
            pre_score = random.choice([4, 4, 5, 5, 4, 5])
            post_score = 5
        elif dept == "Kinh doanh":
            pre_score = random.choice([1, 2, 2, 1, 2, 3])
            post_score = random.choice([3, 4, 4, 3, 4])
        else:
            pre_score = random.choice([2, 3, 3, 3, 4])
            post_score = random.choice([4, 4, 5, 4])

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=120 + i)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i)).isoformat(),
            "answers": {
                g_id: dept,
                q_pre_id: pre_score,
                q_post_id: post_score
            },
            "client_metadata": {"browser": "Pytest Non-Parametric Engine"}
        })
        assert sub_res.status_code == 201

    # 5. Kiểm thử Mann-Whitney U giữa IT và Sales
    res_mwu = client.post(f"/api/surveys/{survey_id}/analytics/mann-whitney-u", json={
        "target_question_id": q_pre_id,
        "grouping_question_id": g_id,
        "group1_value": "Công nghệ thông tin",
        "group2_value": "Kinh doanh"
    })
    assert res_mwu.status_code == 200
    mwu_data = res_mwu.json()
    assert mwu_data["status"] == "OK"
    assert mwu_data["test_type"] == "MANN_WHITNEY_U"
    assert mwu_data["statistics"]["is_significant"] is True
    assert mwu_data["statistics"]["p_value"] < 0.05
    assert mwu_data["effect_size"]["rosenthal_r"] > 0.4

    # 6. Kiểm thử Wilcoxon Signed-Rank giữa q_post và q_pre
    res_wilcoxon = client.post(f"/api/surveys/{survey_id}/analytics/wilcoxon-signed-rank", json={
        "question_id_1": q_post_id,
        "question_id_2": q_pre_id
    })
    assert res_wilcoxon.status_code == 200
    w_data = res_wilcoxon.json()
    assert w_data["status"] == "OK"
    assert w_data["test_type"] == "WILCOXON_SIGNED_RANK"
    assert w_data["total_pairs"] >= 15
    assert w_data["statistics"]["is_significant"] is True
    assert w_data["statistics"]["p_value"] < 0.01

    # 7. Kiểm thử Kruskal-Wallis H cho cả 3 phòng ban
    res_kw = client.post(f"/api/surveys/{survey_id}/analytics/kruskal-wallis", json={
        "target_question_id": q_pre_id,
        "grouping_question_id": g_id
    })
    assert res_kw.status_code == 200
    kw_data = res_kw.json()
    assert kw_data["status"] == "OK"
    assert kw_data["test_type"] == "KRUSKAL_WALLIS_H"
    assert kw_data["k_groups"] == 3
    assert kw_data["degrees_of_freedom"] == 2
    assert kw_data["statistics"]["is_significant"] is True
    assert len(kw_data["post_hoc_dunn_tests"]) == 3

    # 8. Kiểm tra nhật ký kiểm toán bất biến
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    actions = [e["action"] for e in events]
    assert "MANN_WHITNEY_TEST_PERFORMED" in actions
    assert "WILCOXON_TEST_PERFORMED" in actions
    assert "KRUSKAL_WALLIS_TEST_PERFORMED" in actions
