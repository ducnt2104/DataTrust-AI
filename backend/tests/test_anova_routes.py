import pytest
import random
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_anova_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/anova", json={
        "grouping_question_id": "gq",
        "target_question_id": "tq"
    })
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thực nghiệm 3 nhóm
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Khác biệt Nhận thức Theo Trình Độ Học Vấn (One-Way ANOVA)",
        "description": "Đo lường sự khác biệt về mức độ tin cậy số",
        "instructions": "Vui lòng chọn thông tin phù hợp"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo câu hỏi: 1 câu phân nhóm (3 lựa chọn) và 1 câu thang đo
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Khác biệt Nhận thức Theo Trình Độ Học Vấn (One-Way ANOVA)",
        "questions": [
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Trình độ học vấn cao nhất",
                "is_required": True,
                "options": ["THPT", "Đại học", "Sau đại học"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ tin cậy đối với hệ thống số",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    grp_qid = public_q[0]["id"]
    tgt_qid = public_q[1]["id"]

    # 4. Gửi 30 phản hồi chia đều 3 nhóm:
    # THPT: điểm ~ 2.0 (1, 2, 2, 3)
    # Đại học: điểm ~ 3.5 (3, 4, 4, 3)
    # Sau đại học: điểm ~ 5.0 (5, 5, 4, 5)
    random.seed(55)
    for idx in range(10):
        s = random.choice(["1", "2", "2", "3"])
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx:02d}:35Z",
            "answers": {grp_qid: "THPT", tgt_qid: s}
        })

    for idx in range(10):
        s = random.choice(["3", "4", "4", "3"])
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx+10:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx+10:02d}:35Z",
            "answers": {grp_qid: "Đại học", tgt_qid: s}
        })

    for idx in range(10):
        s = random.choice(["5", "5", "4", "5"])
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx+20:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx+20:02d}:35Z",
            "answers": {grp_qid: "Sau đại học", tgt_qid: s}
        })

    # 5. Gọi API ANOVA cho cả 3 nhóm
    res = client.post(f"/api/surveys/{survey_id}/analytics/anova", json={
        "grouping_question_id": grp_qid,
        "target_question_id": tgt_qid,
        "scope": "all"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["groups_count"] == 3
    assert data["total_sample_size"] == 30
    assert data["anova_table"]["df_between"] == 2
    assert data["anova_table"]["df_within"] == 27
    assert data["anova_table"]["f_stat"] > 20.0
    assert data["anova_table"]["is_significant_01"] is True
    assert data["effect_size"]["eta_squared"] > 0.40
    assert data["effect_size"]["magnitude"] == "Lớn (Large)"

    # Kiểm tra Tukey Post-hoc
    assert len(data["post_hoc_tukey"]) == 3
    # Phải có ít nhất cặp THPT vs Sau đại học khác biệt có ý nghĩa
    pair_thpt_sdh = next(p for p in data["post_hoc_tukey"] if "THPT" in p["comparison"] and "Sau đại học" in p["comparison"])
    assert pair_thpt_sdh["is_significant"] is True
    assert pair_thpt_sdh["q_stat"] > pair_thpt_sdh["q_critical_05"]

    # Diễn giải học thuật APA
    assert "One-Way ANOVA" in data["apa_interpretation"]
    assert "Tukey" in data["apa_interpretation"]

    # 6. Kiểm tra khi chọn lọc nhóm bằng selected_groups
    res_subset = client.post(f"/api/surveys/{survey_id}/analytics/anova", json={
        "grouping_question_id": grp_qid,
        "target_question_id": tgt_qid,
        "scope": "all",
        "selected_groups": ["THPT", "Sau đại học"]
    })
    assert res_subset.status_code == 200
    data_sub = res_subset.json()
    assert data_sub["status"] == "SUCCESS"
    assert data_sub["groups_count"] == 2
    assert data_sub["total_sample_size"] == 20
