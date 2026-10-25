import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rdd_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Thiết kế Gián đoạn Hồi quy Sắc nét (Sharp RDD; Hahn 2001, Imbens 2012)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/rdd", json={
        "running_question_id": "q1",
        "outcome_question_id": "q2",
        "cutoff": 50.0
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Chính sách Học bổng & Nỗ lực Học tập (Sharp RDD)",
        "description": "Đánh giá tác động nhân quả cận ngưỡng điểm 60"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 2 câu hỏi số: Điểm bài kiểm tra (Running X) và Nỗ lực học tập (Outcome Y)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Chính sách Học bổng & Nỗ lực Học tập (Sharp RDD)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Điểm bài kiểm tra đầu vào (Thang 0-100)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Điểm nỗ lực học tập học kỳ sau (Thang 1-10)",
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
    q_score = questions[0]["id"]
    q_effort = questions[1]["id"]

    # 4. Khi chưa có dữ liệu phản hồi (< 20)
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/rdd", json={
        "running_question_id": q_score,
        "outcome_question_id": q_effort,
        "cutoff": 60.0
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 5. Sinh 26 phản hồi phân bố đều qua ngưỡng cutoff c = 60
    now = datetime.now(timezone.utc)
    for i in range(26):
        score_val = 35.0 + i * 2.0  # từ 35 đến 85
        treated = 1.0 if score_val >= 60.0 else 0.0
        # Bước nhảy +2.5 điểm khi score >= 60
        effort_val = max(1.0, min(10.0, 4.0 + 0.04 * (score_val - 60.0) + 2.5 * treated))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=600 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_score: score_val,
                q_effort: effort_val
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API ước lượng mô hình Sharp RDD
    res_rdd = client.post(f"/api/surveys/{survey_id}/analytics/rdd", json={
        "running_question_id": q_score,
        "outcome_question_id": q_effort,
        "cutoff": 60.0,
        "scope": "all"
    })
    assert res_rdd.status_code == 200
    data = res_rdd.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 26
    assert data["cutoff_threshold"] == 60.0
    assert "treatment_effect_late" in data
    assert "mccrary_manipulation_test" in data
    assert "binned_scatter_points" in data
    assert "svg_chart" in data
    assert "<svg" in data["svg_chart"]
    assert "apa_narrative" in data
    assert "Regression Discontinuity" in data["apa_narrative"] or "Hahn et al." in data["apa_narrative"]

    # 7. Kiểm tra audit log
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    actions = [evt["action"] for evt in events]
    assert "RDD_MODEL_EVALUATED" in actions
