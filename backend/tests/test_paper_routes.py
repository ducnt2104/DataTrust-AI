import io
import json
import cv2
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.omr_engine import OMREngine

@pytest.fixture
def client():
    return TestClient(app)

def test_paper_survey_full_flow(client):
    # 1. Tạo khảo sát mới
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm định Phiếu Giấy & OMR",
        "description": "Thực địa kiểm tra quy trình số hóa phiếu và phát hiện gian lận"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    # 2. Thêm câu hỏi
    update_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "question_type": "single_choice",
                "title": "Bạn đánh giá thế nào về đường xá?",
                "order_index": 0,
                "is_required": True,
                "options": [{"id": "opt1", "label": "Tốt"}, {"id": "opt2", "label": "Bình thường"}, {"id": "opt3", "label": "Kém"}]
            },
            {
                "question_type": "likert",
                "title": "Mức độ tin cậy vào chính quyền địa phương",
                "order_index": 1,
                "is_required": True,
                "options": []
            }
        ]
    })
    assert update_res.status_code == 200

    # Xuất bản khảo sát
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Lấy layout template phiếu chuẩn
    tmpl_res = client.get(f"/api/surveys/{survey_id}/paper/template")
    assert tmpl_res.status_code == 200
    tmpl_data = tmpl_res.json()
    assert tmpl_data["survey_id"] == survey_id
    layout = tmpl_data["layout"]
    assert len(layout["questions"]) == 2

    q1_id = layout["questions"][0]["question_id"]
    q2_id = layout["questions"][1]["question_id"]

    # 4. Sinh ảnh scan giả lập tô opt1 cho q1 và mức 5 cho q2
    mock_answers = {q1_id: "opt1", q2_id: "5"}
    mock_img = OMREngine.synthesize_mock_paper_scan(layout, mock_answers)
    
    # Encode sang JPEG bytes để gửi multipart/form-data
    _, img_encoded = cv2.imencode(".jpg", mock_img)
    img_bytes = img_encoded.tobytes()

    # 5. Gọi endpoint /scan
    scan_res = client.post(
        f"/api/surveys/{survey_id}/paper/scan",
        files={"file": ("scan_test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    )
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["success"] is True
    assert scan_data["image_quality"]["is_passed"] is True
    assert scan_data["detected_answers"][q1_id] == "opt1"
    assert scan_data["detected_answers"][q2_id] == "5"
    assert scan_data["overlay_image_base64"].startswith("data:image/jpeg;base64,")

    # 6. Người dùng thực hiện sửa nhanh (Manual correction) và ingest vào database
    corrected_answers = {q1_id: "opt2", q2_id: "5"}  # Sửa opt1 thành opt2
    ingest_res = client.post(
        f"/api/surveys/{survey_id}/paper/ingest",
        json={
            "form_id": scan_data["form_id"],
            "enumerator_id": "DTV-HA-NOI-01",
            "answers": corrected_answers,
            "omr_confidence": scan_data["confidence_score"],
            "manual_corrections": [
                {
                    "question_id": q1_id,
                    "original": "opt1",
                    "corrected": "opt2",
                    "reason": "Người trả lời gạch chéo ô opt1 và tô lại opt2"
                }
            ]
        }
    )
    assert ingest_res.status_code == 201
    ingest_data = ingest_res.json()
    assert ingest_data["status"] == "ingested"
    assert ingest_data["source"] == "paper_scan"
    resp_id = ingest_data["response_id"]

    # 7. Kiểm tra response detail xem có lưu đúng source, enumerator_id, và audit log không
    detail_res = client.get(f"/api/surveys/{survey_id}/responses/{resp_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["source"] == "paper_scan"
    assert detail["enumerator_id"] == "DTV-HA-NOI-01"
    assert detail["answers"][q1_id] == "opt2"
    assert str(detail["answers"][q2_id]) == "5"
