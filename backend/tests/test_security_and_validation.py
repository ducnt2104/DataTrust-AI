import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_http_security_headers_and_timing():
    """Kiểm tra các HTTP Security Headers và X-Process-Time-Ms được đính kèm vào mọi response."""
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers

    assert "x-process-time-ms" in headers, "Thiếu header X-Process-Time-Ms"
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "SAMEORIGIN"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("permissions-policy", "")

def test_public_survey_response_validation_rules():
    """Kiểm tra hệ thống validation nghiêm ngặt từ chối các phản hồi vi phạm logic (rating > 5, ranking trùng, text quá dài)."""
    # 1. Tạo khảo sát thử nghiệm
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm định Ranh giới Validation",
        "description": "Thử nghiệm các trường hợp biên"
    })
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    # 2. Cấu hình câu hỏi
    questions = [
        {
            "id": "q_rating",
            "question_type": "rating",
            "title": "Đánh giá sao từ 1 đến 5",
            "is_required": True,
            "options": []
        },
        {
            "id": "q_scale",
            "question_type": "linear_scale",
            "title": "Đánh giá NPS từ 0 đến 10",
            "is_required": True,
            "options": []
        },
        {
            "id": "q_rank",
            "question_type": "ranking",
            "title": "Xếp hạng ưu tiên",
            "is_required": True,
            "options": [
                {"id": "A", "label": "Mục A"},
                {"id": "B", "label": "Mục B"},
                {"id": "C", "label": "Mục C"}
            ]
        },
        {
            "id": "q_text",
            "question_type": "text",
            "title": "Nhận xét tự do",
            "is_required": False,
            "options": []
        }
    ]
    client.put(f"/api/surveys/{survey_id}", json={"questions": questions})
    client.post(f"/api/surveys/{survey_id}/publish")

    now = datetime.now(timezone.utc)
    base_payload = {
        "started_at": (now - timedelta(seconds=30)).isoformat(),
        "submitted_at": now.isoformat(),
    }

    # Trường hợp A: Rating > 5 (Ví dụ 10)
    bad_rating_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        **base_payload,
        "answers": {
            "q_rating": 10,
            "q_scale": 8,
            "q_rank": ["A", "B", "C"]
        }
    })
    assert bad_rating_res.status_code == 422
    assert "đánh giá sao" in str(bad_rating_res.json())

    # Trường hợp B: Linear scale < 0 (Ví dụ -1)
    bad_scale_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        **base_payload,
        "answers": {
            "q_rating": 4,
            "q_scale": -1,
            "q_rank": ["A", "B", "C"]
        }
    })
    assert bad_scale_res.status_code == 422
    assert "thang điểm" in str(bad_scale_res.json())

    # Trường hợp C: Ranking chứa phần tử trùng lặp (["A", "A", "B"])
    bad_ranking_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        **base_payload,
        "answers": {
            "q_rating": 5,
            "q_scale": 10,
            "q_rank": ["A", "A", "B"]
        }
    })
    assert bad_ranking_res.status_code == 422
    assert "trùng lặp" in str(bad_ranking_res.json())

    # Trường hợp D: Văn bản quá 10,000 ký tự (DoS mitigation)
    oversized_text = "A" * 10005
    bad_text_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        **base_payload,
        "answers": {
            "q_rating": 5,
            "q_scale": 10,
            "q_rank": ["A", "B", "C"],
            "q_text": oversized_text
        }
    })
    assert bad_text_res.status_code == 422
    assert "10,000 ký tự" in str(bad_text_res.json())

    # Trường hợp E: Dữ liệu hợp lệ chuẩn
    valid_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        **base_payload,
        "answers": {
            "q_rating": 5,
            "q_scale": 10,
            "q_rank": ["A", "B", "C"],
            "q_text": "Phản hồi hợp lệ và tích cực."
        }
    })
    assert valid_res.status_code == 201
    assert valid_res.json()["risk_level"] == "low"

def test_export_filename_sanitization():
    """Kiểm tra xuất file CSV có filename an toàn, tránh HTTP Header Injection."""
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Tên Chứa Ký Tự Lạ \r\n Set-Cookie: admin=true",
        "description": "Test injection"
    })
    survey_id = res.json()["id"]

    export_res = client.get(f"/api/surveys/{survey_id}/export?format=csv")
    assert export_res.status_code == 200
    content_disp = export_res.headers.get("content-disposition", "")
    assert "\r" not in content_disp and "\n" not in content_disp
    assert 'filename="' in content_disp

def test_csv_formula_injection_sanitization():
    """Kiểm tra xuất dữ liệu CSV tự động trung hòa công thức độc hại (CWE-1236 / CSV Formula Injection)."""
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm thử CSV Injection",
        "description": "CWE-1236 Immunity"
    })
    survey_id = res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_inj",
                "order_index": 0,
                "question_type": "short_text",
                "title": "Góp ý của bạn",
                "is_required": True,
                "options": []
            }
        ]
    })

    res_pub = client.post(f"/api/surveys/{survey_id}/publish")
    slug = res_pub.json()["public_slug"]

    # Gửi phản hồi chứa công thức nguy hiểm
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T20:00:00Z",
        "submitted_at": "2026-10-23T20:01:00Z",
        "answers": {"q_inj": "=cmd|' /C calc'!A0"},
        "client_metadata": {},
        "source": "online_form"
    })

    # Xuất CSV
    exp_res = client.get(f"/api/surveys/{survey_id}/export?format=csv&scope=raw")
    assert exp_res.status_code == 200
    csv_text = exp_res.content.decode("utf-8")

    # Ký tự bắt đầu '=' phải được bao bọc bởi dấu nháy đơn "'" để vô hiệu hóa thực thi lệnh
    assert "'=cmd|' /C calc'!A0" in csv_text

def test_system_diagnostics_and_maintenance():
    """Kiểm tra API chẩn đoán toàn diện hệ thống SQLite B-Tree, dung lượng đĩa và chuỗi băm bất biến."""
    diag_res = client.get("/api/system/diagnostics")
    assert diag_res.status_code == 200
    diag_data = diag_res.json()

    assert diag_data["status"] == "healthy"
    assert "db_path" in diag_data
    assert diag_data["file_size_bytes"] > 0
    assert diag_data["sqlite_pragmas"]["integrity_check"] == "ok"
    assert diag_data["sqlite_pragmas"]["journal_mode"] == "wal"
    assert "surveys" in diag_data["table_record_counts"]
    assert "audit_logs" in diag_data["table_record_counts"]
    assert diag_data["tamper_evident_ledger"]["is_chain_valid"] is True

    wal_res = client.post("/api/system/maintenance/wal-checkpoint")
    assert wal_res.status_code == 200
    assert wal_res.json()["status"] == "success"

    vac_res = client.post("/api/system/maintenance/vacuum")
    assert vac_res.status_code == 200
    assert vac_res.json()["status"] == "success"


