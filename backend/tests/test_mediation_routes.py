import pytest
import random
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

try:
    from app.main import app
except ModuleNotFoundError:
    from backend.app.main import app

client = TestClient(app)


def test_mediation_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey-id/analytics/mediation", json={
        "x_question_id": "x_id",
        "m_question_id": "m_id",
        "y_question_id": "y_id"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên Cứu Tác Động Trung Gian Về Trải Nghiệm Khách Hàng",
        "description": "Kiểm định mô hình: Chất lượng dịch vụ (X) -> Niềm tin thương hiệu (M) -> Lòng trung thành (Y)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 3 câu hỏi cho X, M, Y
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên Cứu Tác Động Trung Gian Về Trải Nghiệm Khách Hàng",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Chất lượng dịch vụ (X)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Niềm tin thương hiệu (M)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Lòng trung thành (Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    x_id = public_q[0]["id"]
    m_id = public_q[1]["id"]
    y_id = public_q[2]["id"]

    # 4. Kiểm tra validate biến trùng lặp (400)
    res_dup = client.post(f"/api/surveys/{survey_id}/analytics/mediation", json={
        "x_question_id": x_id,
        "m_question_id": x_id,
        "y_question_id": y_id
    })
    assert res_dup.status_code == 400

    # 5. Kiểm tra khi chưa có phản hồi nào
    res_empty = client.post(f"/api/surveys/{survey_id}/analytics/mediation", json={
        "x_question_id": x_id,
        "m_question_id": m_id,
        "y_question_id": y_id
    })
    assert res_empty.status_code == 200
    assert res_empty.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 6. Gửi 15 phản hồi hợp lệ mô phỏng chuỗi trung gian
    random.seed(42)
    now = datetime.now(timezone.utc)
    for i in range(15):
        val_x = round(random.uniform(3.0, 9.0), 1)
        val_m = round(1.5 + 0.7 * val_x + random.uniform(-0.3, 0.3), 1)
        val_y = round(2.0 + 0.6 * val_m + random.uniform(-0.3, 0.3), 1)

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=60 + i)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i)).isoformat(),
            "answers": {
                x_id: val_x,
                m_id: val_m,
                y_id: val_y
            },
            "client_metadata": {"user_agent": "Pytest Synthetic Respondent"}
        })
        assert sub_res.status_code == 201

    # 7. Gọi API kiểm định trung gian
    res_analysis = client.post(f"/api/surveys/{survey_id}/analytics/mediation", json={
        "x_question_id": x_id,
        "m_question_id": m_id,
        "y_question_id": y_id,
        "scope": "all",
        "bootstrap_samples": 200
    })
    assert res_analysis.status_code == 200
    data = res_analysis.json()

    assert data["status"] == "OK"
    assert data["sample_size"] >= 10
    assert len(data["steps"]) == 3
    assert "effects_summary" in data
    assert "significance_tests" in data
    assert "conclusion" in data
    assert "diagram" in data
    assert data["effects_summary"]["vaf_percent"] >= 0.0

    # 8. Xác minh audit trail đã ghi lại nhật ký kiểm toán
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    assert any(e["action"] == "MEDIATION_ANALYSIS_PERFORMED" for e in events)
