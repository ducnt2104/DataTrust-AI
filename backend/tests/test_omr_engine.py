import cv2
import numpy as np
import pytest
from app.engine.omr_engine import OMREngine

def test_template_generation():
    survey = {"id": "surv-test-1", "title": "Khảo sát ý kiến thực địa"}
    questions = [
        {
            "id": "q1",
            "question_type": "single_choice",
            "title": "Bạn bao nhiêu tuổi?",
            "order_index": 0,
            "options": [{"id": "opt1", "label": "Dưới 18"}, {"id": "opt2", "label": "18-25"}, {"id": "opt3", "label": "Trên 25"}]
        },
        {
            "id": "q2",
            "question_type": "likert",
            "title": "Mức độ hài lòng với dịch vụ",
            "order_index": 1,
            "options": []
        },
        {
            "id": "q3",
            "question_type": "yes_no",
            "title": "Bạn đã từng tham gia chưa?",
            "order_index": 2,
            "options": []
        }
    ]

    layout = OMREngine.generate_paper_template(survey, questions)
    assert layout["survey_id"] == "surv-test-1"
    assert len(layout["fiducial_markers"]) == 4
    assert len(layout["questions"]) == 3
    assert len(layout["questions"][0]["bubbles"]) == 3
    assert len(layout["questions"][1]["bubbles"]) == 5
    assert len(layout["questions"][2]["bubbles"]) == 2

def test_image_quality_sharp_vs_blurry():
    # Ảnh sắc nét
    sharp_img = np.zeros((300, 300), dtype=np.uint8)
    cv2.rectangle(sharp_img, (50, 50), (250, 250), 255, 3)
    cv2.putText(sharp_img, "DATATRUST", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, 255, 2)
    quality_sharp = OMREngine.assess_image_quality(sharp_img)
    assert quality_sharp["laplacian_variance"] > 20.0

    # Ảnh bị làm mờ nặng
    blurry_img = cv2.GaussianBlur(sharp_img, (31, 31), 0)
    quality_blurry = OMREngine.assess_image_quality(blurry_img)
    assert quality_blurry["sharpness_status"] in ("blurry", "acceptable")
    assert quality_blurry["laplacian_variance"] < quality_sharp["laplacian_variance"]

def test_fiducial_detection_and_warp():
    survey = {"id": "surv-warp-test", "title": "Khảo sát Nắn Phối Cảnh"}
    questions = [{
        "id": "q1",
        "question_type": "single_choice",
        "title": "Câu hỏi test",
        "order_index": 0,
        "options": [{"id": "opt1", "label": "A"}, {"id": "opt2", "label": "B"}]
    }]
    layout = OMREngine.generate_paper_template(survey, questions)

    # Sinh ảnh mẫu phẳng
    flat_img = OMREngine.synthesize_mock_paper_scan(layout, {"q1": "opt1"})
    
    # Kiểm tra nhận diện 4 góc
    corners = OMREngine.detect_fiducial_markers(flat_img)
    assert corners is not None
    assert len(corners) == 4

    # Nắn phối cảnh
    warped = OMREngine.normalize_perspective(flat_img, corners)
    assert warped.shape[0] == OMREngine.PAGE_HEIGHT
    assert warped.shape[1] == OMREngine.PAGE_WIDTH

def test_bubble_fill_detection_and_overlay():
    survey = {"id": "surv-bubble-test", "title": "Khảo sát Đọc Ô Tích"}
    questions = [
        {
            "id": "q_single",
            "question_type": "single_choice",
            "title": "Phương án bạn chọn",
            "order_index": 0,
            "options": [{"id": "optA", "label": "Phương án A"}, {"id": "optB", "label": "Phương án B"}]
        },
        {
            "id": "q_likert",
            "question_type": "likert",
            "title": "Đánh giá mức độ",
            "order_index": 1,
            "options": []
        }
    ]
    layout = OMREngine.generate_paper_template(survey, questions)

    # Tô phương án A cho q_single và mức 4 cho q_likert
    filled_answers = {"q_single": "optA", "q_likert": "4"}
    scan_img = OMREngine.synthesize_mock_paper_scan(layout, filled_answers)

    # Đọc ô tích
    detected, confidences, warnings = OMREngine.read_bubbles(scan_img, layout)
    assert detected.get("q_single") == "optA"
    assert detected.get("q_likert") == "4"
    assert confidences.get("q_single", 0) >= 0.70
    assert confidences.get("q_likert", 0) >= 0.70

    # Sinh visual overlay
    overlay_b64 = OMREngine.generate_visual_overlay(scan_img, layout, detected, confidences)
    assert overlay_b64.startswith("data:image/jpeg;base64,")
