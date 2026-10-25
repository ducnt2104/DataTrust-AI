import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

try:
    from app.main import app
    from app.database import get_db
except ModuleNotFoundError:
    from backend.app.main import app
    from backend.app.database import get_db

client = TestClient(app)


def test_missing_data_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/missing-data-diagnostics", json={})
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thử nghiệm mô thức khuyết thiếu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Kiểm Định Mô Thức Khuyết Thiếu Dữ Liệu",
        "description": "Kiểm định Little's MCAR Test và Động cơ Bù khuyết Đa Phương Pháp"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 3 câu hỏi định lượng
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Kiểm Định Mô Thức Khuyết Thiếu Dữ Liệu",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Chất lượng dịch vụ",
                "is_required": False,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "likert",
                "title": "Độ tin cậy nền tảng",
                "is_required": False,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "nps",
                "title": "Khả năng giới thiệu",
                "is_required": False,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    # Lấy thông tin ID câu hỏi
    client.post(f"/api/surveys/{survey_id}/publish")
    surv_data = client.get(f"/api/surveys/{survey_id}").json()
    qs = surv_data["questions"]
    q1_id = qs[0]["id"]
    q2_id = qs[1]["id"]
    q3_id = qs[2]["id"]

    # 4. Gửi các phản hồi mô phỏng với một số giá trị khuyết thiếu (missing data)
    now = datetime.now(timezone.utc)
    test_cases = [
        {q1_id: "5", q2_id: "4", q3_id: "9"},
        {q1_id: "4", q3_id: "8"},               # khuyết q2
        {q1_id: "3", q2_id: "3"},               # khuyết q3
        {q1_id: "5", q2_id: "5", q3_id: "10"},
        {q2_id: "2", q3_id: "4"},               # khuyết q1
        {q1_id: "2", q2_id: "2", q3_id: "3"},
        {q1_id: "4", q2_id: "4", q3_id: "7"},
        {q1_id: "5", q3_id: "9"},               # khuyết q2
    ]

    for idx, ans_dict in enumerate(test_cases):
        sub_body = {
            "started_at": (now - timedelta(minutes=15 - idx, seconds=30)).isoformat(),
            "submitted_at": (now - timedelta(minutes=15 - idx)).isoformat(),
            "answers": ans_dict,
            "client_metadata": {
                "ip_hash": f"ip_missing_{idx}",
                "user_agent": "Mozilla/5.0 TestBrowser",
                "screen_resolution": "1920x1080"
            }
        }
        resp = client.post(f"/api/public/surveys/{slug}/submit", json=sub_body)
        assert resp.status_code == 201

    # 5. Gọi API Missing Data Diagnostics
    diag_res = client.post(f"/api/surveys/{survey_id}/analytics/missing-data-diagnostics", json={
        "scope": "all"
    })
    assert diag_res.status_code == 200
    diag_data = diag_res.json()
    assert diag_data["status"] == "OK"
    assert diag_data["sample_size"] == 8
    assert diag_data["variables_count"] == 3
    assert diag_data["total_missing_cells"] == 4
    assert diag_data["overall_missing_rate"] > 0
    assert len(diag_data["variables_summary"]) == 3
    assert len(diag_data["patterns"]) >= 2
    assert diag_data["littles_mcar_test"]["applicable"] is True
    assert diag_data["littles_mcar_test"]["chi_square"] is not None
    assert diag_data["littles_mcar_test"]["p_value"] is not None

    # 6. Gọi API Missing Data Imputation với các phương pháp
    for m in ["mean", "median", "hot_deck", "em", "pmm"]:
        imp_res = client.post(f"/api/surveys/{survey_id}/analytics/missing-data-imputation", json={
            "method": m,
            "scope": "all"
        })
        assert imp_res.status_code == 200
        imp_data = imp_res.json()
        assert imp_data["status"] == "OK"
        assert imp_data["method"] == m
        assert imp_data["imputed_cells_count"] == 4
        assert len(imp_data["comparison"]) == 3
        assert len(imp_data["imputed_data_sample"]) == 8

    # 7. Kiểm tra vết kiểm toán bất biến (Audit Log)
    with get_db() as conn:
        logs = conn.execute("""
            SELECT action, details_json FROM audit_logs
            WHERE entity_id = ? AND action IN (
                'MISSING_DATA_DIAGNOSTICS_PERFORMED',
                'MISSING_DATA_IMPUTATION_EXECUTED'
            )
        """, (survey_id,)).fetchall()
        assert len(logs) >= 2
        actions = [l["action"] for l in logs]
        assert "MISSING_DATA_DIAGNOSTICS_PERFORMED" in actions
        assert "MISSING_DATA_IMPUTATION_EXECUTED" in actions
