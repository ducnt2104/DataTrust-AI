import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_public_survey_lifecycle():
    # 1. Tạo khảo sát
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu thị trường công nghệ",
        "description": "Mô tả",
        "instructions": "Hướng dẫn"
    })
    s_data = create_res.json()
    survey_id = s_data["id"]
    slug = s_data["public_slug"]

    # 2. Thêm 2 câu hỏi
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_device",
                "question_type": "single_choice",
                "title": "Thiết bị chính bạn sử dụng?",
                "is_required": True,
                "options": [{"id": "phone", "label": "Smartphone"}, {"id": "laptop", "label": "Laptop"}]
            },
            {
                "id": "q_feedback",
                "question_type": "short_text",
                "title": "Ý kiến đóng góp:",
                "is_required": False,
                "options": []
            }
        ]
    })

    # 3. Khi khảo sát còn là 'draft', public endpoint phải trả về 403 Forbidden
    draft_res = client.get(f"/api/public/surveys/{slug}")
    assert draft_res.status_code == 403

    # 4. Xuất bản khảo sát
    client.post(f"/api/surveys/{survey_id}/publish")

    # 5. Truy cập lại public endpoint -> Thành công 200
    pub_get = client.get(f"/api/public/surveys/{slug}")
    assert pub_get.status_code == 200
    pub_body = pub_get.json()
    assert len(pub_body["questions"]) == 2

    # 6. Gửi phản hồi thiếu trường bắt buộc -> Lỗi 422
    now = datetime.now(timezone.utc)
    submit_fail = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=20)).isoformat(),
        "submitted_at": now.isoformat(),
        "answers": {}  # Thiếu q_device bắt buộc
    })
    assert submit_fail.status_code == 422

    # 7. Gửi phản hồi hợp lệ -> 201 Created
    submit_ok = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=35)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"browser": "Chrome"},
        "answers": {
            "q_device": "laptop",
            "q_feedback": "Nền tảng giao diện rất mượt mà"
        }
    })
    assert submit_ok.status_code == 201
    resp_id = submit_ok.json()["response_id"]

    # 8. Kiểm tra phản hồi hiển thị trong danh sách responses
    list_res = client.get(f"/api/surveys/{survey_id}/responses")
    assert list_res.status_code == 200
    responses_list = list_res.json()
    assert len(responses_list) == 1
    assert responses_list[0]["id"] == resp_id

    # 9. Kiểm tra chi tiết phản hồi
    detail_res = client.get(f"/api/surveys/{survey_id}/responses/{resp_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["answers"]["q_device"] == "laptop"
    assert detail["assessment"] is not None

    # 10. Đóng khảo sát và thử gửi phản hồi tiếp -> Bị từ chối
    client.post(f"/api/surveys/{survey_id}/close")
    submit_after_close = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=10)).isoformat(),
        "submitted_at": now.isoformat(),
        "answers": {"q_device": "phone"}
    })
    assert submit_after_close.status_code == 400

def test_public_survey_offline_batch_sync():
    # 1. Tạo và xuất bản khảo sát
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát thực địa nông thôn Offline Sync Test",
        "description": "Thử nghiệm đồng bộ hàng loạt",
        "instructions": "Vui lòng trả lời"
    })
    s_data = create_res.json()
    survey_id = s_data["id"]
    slug = s_data["public_slug"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_field_loc",
                "question_type": "single_choice",
                "title": "Địa bàn khảo sát:",
                "is_required": True,
                "options": [{"id": "r1", "label": "Khu vực 1"}, {"id": "r2", "label": "Khu vực 2"}]
            },
            {
                "id": "q_satisfaction",
                "question_type": "rating",
                "title": "Mức độ hài lòng (1-5 sao):",
                "is_required": True,
                "options": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    now = datetime.now(timezone.utc)
    uuid_item_1 = "offline-client-uuid-1111"
    uuid_item_2 = "offline-client-uuid-2222"
    uuid_item_3 = "offline-client-uuid-3333"

    batch_payload = {
        "responses": [
            {
                "client_uuid": uuid_item_1,
                "started_at": (now - timedelta(seconds=60)).isoformat(),
                "submitted_at": (now - timedelta(seconds=10)).isoformat(),
                "client_metadata": {"device": "Android Field Tablet", "client_uuid": uuid_item_1},
                "answers": {"q_field_loc": "r1", "q_satisfaction": 4},
                "source": "offline_sync",
                "enumerator_id": "ENUM_AN_GIANG_01"
            },
            {
                "client_uuid": uuid_item_2,
                "started_at": (now - timedelta(seconds=45)).isoformat(),
                "submitted_at": (now - timedelta(seconds=5)).isoformat(),
                "client_metadata": {"device": "Android Field Tablet", "client_uuid": uuid_item_2},
                "answers": {"q_field_loc": "r2", "q_satisfaction": 5},
                "source": "offline_sync",
                "enumerator_id": "ENUM_AN_GIANG_01"
            },
            {
                "client_uuid": uuid_item_3,
                "started_at": (now - timedelta(seconds=30)).isoformat(),
                "submitted_at": now.isoformat(),
                "client_metadata": {"device": "Android Field Tablet", "client_uuid": uuid_item_3},
                "answers": {},  # Thiếu câu hỏi bắt buộc -> Báo lỗi từng phần
                "source": "offline_sync",
                "enumerator_id": "ENUM_AN_GIANG_01"
            }
        ]
    }

    # 2. Gửi đồng bộ mẻ đầu tiên
    sync_res = client.post(f"/api/public/surveys/{slug}/batch-sync", json=batch_payload)
    assert sync_res.status_code == 200
    res_json = sync_res.json()
    assert res_json["success"] is True
    assert res_json["total_received"] == 3
    assert res_json["synced_count"] == 2
    assert res_json["error_count"] == 1
    assert res_json["duplicates_skipped"] == 0

    # 3. Gửi lại cùng mẻ để kiểm tra tính toàn vẹn Idempotency (Trùng lặp client_uuid)
    resync_res = client.post(f"/api/public/surveys/{slug}/batch-sync", json=batch_payload)
    assert resync_res.status_code == 200
    resync_json = resync_res.json()
    assert resync_json["synced_count"] == 0  # Không chèn thêm bản ghi nào
    assert resync_json["duplicates_skipped"] == 2  # 2 bản ghi trước được bỏ qua an toàn
    assert resync_json["error_count"] == 1  # Bản ghi lỗi vẫn báo lỗi

