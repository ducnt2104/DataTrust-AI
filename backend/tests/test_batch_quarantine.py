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

def create_sample_survey():
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Thực địa & Trải nghiệm Tiêu dùng",
        "description": "Nghiên cứu thị trường bán lẻ tại địa bàn Hà Nội",
        "instructions": "Vui lòng trả lời trung thực"
    })
    s_data = create_res.json()
    survey_id = s_data["id"]
    slug = s_data["public_slug"]

    # Thêm câu hỏi
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_sat",
                "question_type": "rating",
                "title": "Mức độ hài lòng chung:",
                "is_required": True,
                "options": []
            },
            {
                "id": "q_speed",
                "question_type": "rating",
                "title": "Tốc độ phục vụ:",
                "is_required": True,
                "options": []
            },
            {
                "id": "q_comment",
                "question_type": "text",
                "title": "Ý kiến đóng góp:",
                "is_required": False,
                "options": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")
    return survey_id, slug

def test_batch_quarantine_dry_run_and_execution():
    survey_id, slug = create_sample_survey()
    now = datetime.now(timezone.utc)

    # 1. Nộp 2 phản hồi sạch
    for i in range(2):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=80 + i * 10)).isoformat(),
            "submitted_at": (now - timedelta(seconds=10 + i * 5)).isoformat(),
            "client_metadata": {"browser": "Chrome", "enumerator_id": f"ENUM-0{i+1}"},
            "answers": {"q_sat": 4 + (i % 2), "q_speed": 4, "q_comment": f"Dịch vụ tốt phản hồi {i}"}
        })

    # 2. Nộp 1 phản hồi speeder (< 10 giây)
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=3)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"browser": "Bot/1.0", "enumerator_id": "ENUM-FAKE"},
        "answers": {"q_sat": 1, "q_speed": 1, "q_comment": "nhanh"}
    })

    # 3. Dry-run batch quarantine
    dry_res = client.post(f"/api/surveys/{survey_id}/responses/batch-quarantine-anomalies", json={
        "quarantine_syndicates": True,
        "quarantine_coffee_shop": True,
        "quarantine_impossible_velocity": True,
        "quarantine_speeders": True,
        "quarantine_straightlining": True,
        "min_risk_score": 70.0,
        "dry_run": True
    })
    assert dry_res.status_code == 200
    dry_data = dry_res.json()
    assert dry_data["success"] is True
    assert dry_data["dry_run"] is True
    assert dry_data["total_evaluated"] == 3
    assert dry_data["quarantined_count"] >= 1
    assert "speeder" in dry_data["reasons_breakdown"]
    assert dry_data["audit_log_id"] is None

    # Xác nhận trong CSDL trạng thái vẫn chưa bị thay đổi (dry_run không mutate CSDL)
    list_res = client.get(f"/api/surveys/{survey_id}/responses")
    all_resps = list_res.json()
    for r in all_resps:
        assert r["review_status"] == "unverified"

    # 4. Thực thi thật batch quarantine (dry_run = False)
    apply_res = client.post(f"/api/surveys/{survey_id}/responses/batch-quarantine-anomalies", json={
        "quarantine_syndicates": True,
        "quarantine_coffee_shop": True,
        "quarantine_impossible_velocity": True,
        "quarantine_speeders": True,
        "quarantine_straightlining": True,
        "min_risk_score": 70.0,
        "action": "verified_fraud",
        "dry_run": False
    })
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    assert apply_data["success"] is True
    assert apply_data["dry_run"] is False
    assert apply_data["quarantined_count"] >= 1
    assert apply_data["audit_log_id"] is not None

    # Kiểm tra trạng thái trong DB
    list_res_after = client.get(f"/api/surveys/{survey_id}/responses")
    fraud_resps = [r for r in list_res_after.json() if r["review_status"] == "verified_fraud"]
    assert len(fraud_resps) == apply_data["quarantined_count"]

    # 5. Kiểm tra tính năng hoàn tác / khôi phục (Batch Restore)
    restore_res = client.post(f"/api/surveys/{survey_id}/responses/batch-restore-quarantined", json={
        "restore_to_status": "unverified",
        "reason": "Kiểm toán viên xác nhận lại thực địa"
    })
    assert restore_res.status_code == 200
    restore_data = restore_res.json()
    assert restore_data["success"] is True
    assert restore_data["restored_count"] == len(fraud_resps)
    assert restore_data["audit_log_id"] != ""

    # Kiểm tra lại DB sau hoàn tác
    list_res_restored = client.get(f"/api/surveys/{survey_id}/responses")
    restored_unverified = [r for r in list_res_restored.json() if r["review_status"] == "unverified"]
    assert len(restored_unverified) == 3

def test_batch_quarantine_spatial_and_syndicate_detection():
    survey_id, slug = create_sample_survey()
    now = datetime.now(timezone.utc)

    # 1. Nạp 3 phản hồi tại cùng một tọa độ GPS tĩnh (quán cà phê) bởi 1 điều tra viên
    # Tọa độ: 21.0285, 105.8542
    for i in range(3):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=120 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=40 + i * 20)).isoformat(),
            "client_metadata": {
                "browser": "Chrome",
                "enumerator_id": "ENUM-CAFE",
                "device_id": f"DEV-SHARED",
                "latitude": 21.028500,
                "longitude": 105.854200
            },
            "answers": {
                "q_sat": 5,
                "q_speed": 5,
                "q_comment": "Nhân viên nhiệt tình chu đáo tuyệt vời"
            }
        })

    # 2. Chạy Batch Quarantine với phát hiện Coffee-Shop & Collusion Syndicate
    res = client.post(f"/api/surveys/{survey_id}/responses/batch-quarantine-anomalies", json={
        "quarantine_syndicates": True,
        "quarantine_coffee_shop": True,
        "quarantine_impossible_velocity": True,
        "quarantine_speeders": False,
        "quarantine_straightlining": False,
        "min_risk_score": 50.0,
        "action": "verified_fraud",
        "dry_run": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["quarantined_count"] >= 3
    # Phải có lý do hoặc syndicate hoặc coffee_shop hoặc risk
    breakdown = data["reasons_breakdown"]
    assert len(breakdown) > 0
    assert any(k in breakdown for k in ["coffee_shop_congregation", "collusion_syndicate", "high_risk_score"])

def test_cleansing_preview_enhanced_counts():
    survey_id, slug = create_sample_survey()
    now = datetime.now(timezone.utc)

    # Nạp phản hồi
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=2)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"browser": "Bot"},
        "answers": {"q_sat": 1, "q_speed": 1}
    })

    # Gọi preview
    preview_res = client.post(f"/api/surveys/{survey_id}/responses/cleansing/preview", json={
        "exclude_speeders": True,
        "speeder_min_seconds": 10.0,
        "exclude_straightlining": True,
        "exclude_logic_contradictions": True,
        "exclude_collusion_syndicates": True,
        "exclude_coffee_shop_congregations": True,
        "exclude_impossible_travel": True,
        "exclude_geofence_violations": False
    })
    assert preview_res.status_code == 200
    report = preview_res.json()
    assert "flagged_collusion_syndicates" in report
    assert "flagged_coffee_shop" in report
    assert "flagged_impossible_travel" in report
    assert "flagged_geofence_violations" in report
    assert report["flagged_speeders"] == 1
