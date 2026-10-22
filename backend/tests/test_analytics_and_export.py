import os
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

os.environ["DATABASE_PATH"] = "backend/data/test_datatrust.db"

from app.main import app
from app.database import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("backend/data/test_datatrust.db"):
        try:
            os.remove("backend/data/test_datatrust.db")
        except Exception:
            pass
    init_db("backend/data/test_datatrust.db")
    yield

client = TestClient(app)

def test_analytics_and_export_journey():
    # 1. Tạo và xuất bản khảo sát
    s_res = client.post("/api/surveys", json={
        "title": "Khảo sát ý kiến người tiêu dùng về xe điện",
        "description": "Nghiên cứu thị trường 2026"
    })
    survey_id = s_res.json()["id"]
    slug = s_res.json()["public_slug"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_brand",
                "question_type": "single_choice",
                "title": "Hãng xe bạn quan tâm?",
                "is_required": True,
                "options": [{"id": "vinfast", "label": "VinFast"}, {"id": "tesla", "label": "Tesla"}, {"id": "byd", "label": "BYD"}]
            },
            {
                "id": "q_budget",
                "question_type": "number",
                "title": "Ngân sách dự kiến (triệu VNĐ)?",
                "is_required": True,
                "options": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    # 2. Kiểm tra Analytics khi N = 0
    an_res0 = client.get(f"/api/surveys/{survey_id}/analytics")
    assert an_res0.status_code == 200
    an_data0 = an_res0.json()
    assert an_data0["total_responses"] == 0
    assert an_data0["is_sample_size_sufficient"] is False
    assert "chưa đạt ngưỡng tối thiểu" in an_data0["sample_size_notice"]

    # 3. Gửi 5 phản hồi thực
    now = datetime.now(timezone.utc)
    resp_ids = []
    brands = ["vinfast", "tesla", "vinfast", "byd", "vinfast"]
    budgets = ["700", "1200", "850", "600", "900"]

    for i in range(5):
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=40)).isoformat(),
            "submitted_at": now.isoformat(),
            "answers": {
                "q_brand": brands[i],
                "q_budget": budgets[i]
            }
        })
        assert sub_res.status_code == 201
        resp_ids.append(sub_res.json()["response_id"])

    # 4. Kiểm tra Analytics khi N >= 5
    an_res5 = client.get(f"/api/surveys/{survey_id}/analytics")
    assert an_res5.status_code == 200
    an_data5 = an_res5.json()
    assert an_data5["total_responses"] == 5
    assert an_data5["is_sample_size_sufficient"] is True
    assert an_data5["sample_size_notice"] is None
    
    # Kiểm tra phân bố câu hỏi
    brand_stats = next(q for q in an_data5["questions_analytics"] if q["question_id"] == "q_brand")
    assert brand_stats["option_distribution"]["VinFast"] == 3
    assert brand_stats["option_distribution"]["Tesla"] == 1

    budget_stats = next(q for q in an_data5["questions_analytics"] if q["question_id"] == "q_budget")
    assert budget_stats["stats_summary"]["min"] == 600.0
    assert budget_stats["stats_summary"]["max"] == 1200.0

    # 5. Cập nhật quyết định xác minh (Review decision)
    rev_res = client.patch(f"/api/surveys/{survey_id}/responses/{resp_ids[0]}/review", json={
        "review_status": "verified_valid",
        "review_notes": "Đã gọi điện xác nhận phỏng vấn thành công"
    })
    assert rev_res.status_code == 200

    rev_res_fraud = client.patch(f"/api/surveys/{survey_id}/responses/{resp_ids[1]}/review", json={
        "review_status": "verified_fraud",
        "review_notes": "Số điện thoại không liên lạc được"
    })
    assert rev_res_fraud.status_code == 200

    # 6. Kiểm tra so sánh 2 phản hồi side-by-side
    cmp_res = client.get(f"/api/surveys/{survey_id}/responses/compare/side-by-side?resp1={resp_ids[0]}&resp2={resp_ids[2]}")
    assert cmp_res.status_code == 200
    cmp_data = cmp_res.json()
    assert cmp_data["total_questions_compared"] == 2
    # Cả 2 đều chọn VinFast ở q_brand -> matching_answers_count >= 1
    assert cmp_data["matching_answers_count"] >= 1

    # 7. Xuất dữ liệu CSV
    # Verified Clean scope: Phải bao gồm các bản ghi hợp lệ hoặc chưa bị gắn cờ, nhưng LOẠI BỎ bản ghi verified_fraud
    export_csv = client.get(f"/api/surveys/{survey_id}/export?scope=verified_clean&format=csv")
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
    csv_text = export_csv.content.decode("utf-8-sig")
    assert "Response_ID" in csv_text
    assert "Hãng xe bạn quan tâm?" in csv_text
    # resp_ids[1] bị đánh dấu verified_fraud -> KHÔNG được có trong verified_clean
    assert resp_ids[1] not in csv_text
    # resp_ids[0] là verified_valid -> BẮT BUỘC có trong verified_clean
    assert resp_ids[0] in csv_text

    # 8. Kiểm tra AI endpoints
    ai_gen = client.post("/api/ai/generate-survey", json={
        "topic": "Khảo sát ứng dụng trí tuệ nhân tạo trong giáo dục",
        "audience": "Sinh viên đại học",
        "expected_time_minutes": 5
    })
    assert ai_gen.status_code == 200
    ai_draft = ai_gen.json()
    assert "title" in ai_draft
    assert len(ai_draft["questions"]) >= 3

    # Kiểm định câu hỏi
    ai_audit = client.post("/api/ai/audit-questions", json={
        "questions": [
            {"id": "test_q", "title": "Sản phẩm của chúng tôi tuyệt vời thế nào?", "question_type": "single_choice", "options": [{"id": "1", "label": "Tốt"}]}
        ]
    })
    assert ai_audit.status_code == 200
    assert ai_audit.json()["total_issues"] >= 1
