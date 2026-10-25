import pytest
import random
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_independent_ttest_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/ttest/independent", json={
        "grouping_question_id": "gq",
        "group1_value": "A",
        "group2_value": "B",
        "target_question_id": "tq"
    })
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thực nghiệm
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Can thiệp Giáo dục & Kiểm định T-Test Giả Thuyết",
        "description": "So sánh nhóm đối chứng và nhóm thử nghiệm",
        "instructions": "Vui lòng hoàn thành các mục khảo sát"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo câu hỏi: 1 câu phân nhóm và 1 câu thang đo
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Can thiệp Giáo dục & Kiểm định T-Test Giả Thuyết",
        "questions": [
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Nhóm tham gia can thiệp",
                "is_required": True,
                "options": ["Thực nghiệm", "Đối chứng"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Điểm đánh giá năng lực tư duy số",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Lấy ID câu hỏi
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    grp_qid = public_q[0]["id"]
    tgt_qid = public_q[1]["id"]

    # 5. Gửi 12 phản hồi Nhóm Thực nghiệm (điểm cao ~4.5) và 12 phản hồi Nhóm Đối chứng (điểm thấp ~2.5)
    random.seed(42)
    for idx in range(12):
        s_exp = random.choice(["4", "5", "5", "4", "5"])
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx:02d}:40Z",
            "answers": {grp_qid: "Thực nghiệm", tgt_qid: s_exp}
        })

    for idx in range(12):
        s_ctrl = random.choice(["2", "3", "2", "2", "3"])
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx+20:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx+20:02d}:40Z",
            "answers": {grp_qid: "Đối chứng", tgt_qid: s_ctrl}
        })

    # 6. Gọi API kiểm định Independent T-Test
    res = client.post(f"/api/surveys/{survey_id}/analytics/ttest/independent", json={
        "grouping_question_id": grp_qid,
        "group1_value": "Thực nghiệm",
        "group2_value": "Đối chứng",
        "target_question_id": tgt_qid,
        "scope": "all"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["test_type"] == "independent"
    assert data["group1"]["n"] == 12
    assert data["group2"]["n"] == 12
    assert data["mean_difference"] > 1.0
    assert data["primary_test"]["t_stat"] > 5.0
    assert data["primary_test"]["is_significant_01"] is True
    assert "cohen_d" in data["effect_size"]
    assert "hedges_g" in data["effect_size"]
    assert "Điểm đánh giá năng lực tư duy số" in data["apa_interpretation"]

def test_paired_ttest_routes_workflow():
    # 1. Tạo khảo sát đo lường lặp lại Pre-Post
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Đo lường Trước - Sau Can thiệp (Pre-Post Paired T-Test)",
        "description": "Khảo sát ghép cặp đánh giá hiệu quả tập huấn",
        "instructions": "Vui lòng điền đầy đủ"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Tạo 2 câu hỏi Pre và Post
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Đo lường Trước - Sau Can thiệp (Pre-Post Paired T-Test)",
        "questions": [
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Mức độ tự tin trước tập huấn (Pre)",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ tự tin sau tập huấn (Post)",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    pre_qid = public_q[0]["id"]
    post_qid = public_q[1]["id"]

    # 3. Gửi 15 phản hồi Pre-Post (Post > Pre rõ rệt với độ biến thiên thực tế)
    sample_pairs = [
        ("2", "5"), ("1", "4"), ("2", "4"), ("3", "5"), ("2", "5"),
        ("1", "5"), ("2", "4"), ("3", "4"), ("2", "5"), ("1", "4"),
        ("2", "5"), ("3", "5"), ("2", "4"), ("1", "4"), ("2", "5")
    ]
    for idx, (v_pre, v_post) in enumerate(sample_pairs):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx:02d}:35Z",
            "answers": {
                pre_qid: v_pre,
                post_qid: v_post
            }
        })

    # 4. Gọi API Paired T-Test
    res = client.post(f"/api/surveys/{survey_id}/analytics/ttest/paired", json={
        "pre_question_id": pre_qid,
        "post_question_id": post_qid,
        "scope": "all"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["test_type"] == "paired"
    assert data["sample_size"] == 15
    assert data["degrees_of_freedom"] == 14
    assert data["mean_difference"] > 2.0
    assert data["t_stat"] > 0
    assert data["is_significant_01"] is True
    assert "cohen_d" in data["effect_size"]
    assert "Paired-Samples T-Test" in data["apa_interpretation"]
