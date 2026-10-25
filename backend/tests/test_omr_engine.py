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

def test_omr_auto_orientation_rotation():
    """
    Kiểm thử khả năng tự động phát hiện và xoay chuẩn hóa các ảnh chụp bị nghiêng/lộn:
    - Xoay 90° (Landscape)
    - Xoay 180° (Upside down)
    """
    survey = {"id": "surv-orient-test", "title": "Khảo sát Kiểm định Chiều Xoay"}
    questions = [{
        "id": "q1",
        "question_type": "single_choice",
        "title": "Bạn đồng ý không?",
        "order_index": 0,
        "options": [{"id": "opt1", "label": "Đồng ý"}, {"id": "opt2", "label": "Không"}]
    }]
    layout = OMREngine.generate_paper_template(survey, questions)
    orig_img = OMREngine.synthesize_mock_paper_scan(layout, {"q1": "opt1"})

    # 1. Thử nghiệm ảnh bị xoay 90 độ (Landscape w > h)
    rot90 = cv2.rotate(orig_img, cv2.ROTATE_90_CLOCKWISE)
    assert rot90.shape[1] > rot90.shape[0]  # Width > Height
    oriented90, angle90 = OMREngine.auto_orient_page(rot90)
    assert oriented90.shape[0] > oriented90.shape[1]  # Height > Width (Portrait chuẩn)
    assert angle90 in (90, 270)

    # 2. Thử nghiệm ảnh bị lộn ngược đầu 180 độ (Upside Down)
    rot180 = cv2.rotate(orig_img, cv2.ROTATE_180)
    oriented180, angle180 = OMREngine.auto_orient_page(rot180)
    assert oriented180.shape[0] == OMREngine.PAGE_HEIGHT
    assert angle180 == 180

    # 3. Nắn phối cảnh tích hợp tự động sửa xoay
    warped_from_rot = OMREngine.normalize_perspective(rot180)
    assert warped_from_rot.shape[0] == OMREngine.PAGE_HEIGHT
    assert warped_from_rot.shape[1] == OMREngine.PAGE_WIDTH

    # Đọc đáp án từ ảnh đã được tự động nắn chuẩn
    detected, confs, _ = OMREngine.read_bubbles(warped_from_rot, layout)
    assert detected.get("q1") == "opt1"

def test_omr_illumination_normalization_under_gradient_shadow():
    """
    Kiểm thử khả năng triệt tiêu bóng đổ không đều (Uneven Gradient Shadow)
    do bóng điện thoại hoặc nguồn sáng một bên gây ra.
    """
    survey = {"id": "surv-shadow-test", "title": "Khảo sát Thử Nghiệm Bóng Đổ"}
    questions = [
        {
            "id": "q1",
            "question_type": "single_choice",
            "title": "Vùng sáng bên trái",
            "order_index": 0,
            "options": [{"id": "optA", "label": "A"}, {"id": "optB", "label": "B"}]
        },
        {
            "id": "q2",
            "question_type": "likert",
            "title": "Vùng bóng đổ bên phải",
            "order_index": 1,
            "options": []
        }
    ]
    layout = OMREngine.generate_paper_template(survey, questions)
    orig_img = OMREngine.synthesize_mock_paper_scan(layout, {"q1": "optA", "q2": "5"})

    # Tạo bóng đổ phi tuyến: Bên trái 100% sáng, bên phải bị che tối còn 40% độ sáng
    h, w = orig_img.shape[:2]
    gradient_mask = np.linspace(1.0, 0.40, w, dtype=np.float32)
    gradient_2d = np.tile(gradient_mask, (h, 1))

    shadowed_img = orig_img.copy().astype(np.float32)
    for c in range(3):
        shadowed_img[:, :, c] = shadowed_img[:, :, c] * gradient_2d
    shadowed_img = np.clip(shadowed_img, 0, 255).astype(np.uint8)

    # Đọc ô tích trên ảnh có bóng đổ gradient nặng
    detected, confidences, _ = OMREngine.read_bubbles(shadowed_img, layout)

    # Cả ô q1 (vùng sáng) và q2 (mức 5 - nằm tận cùng bên phải trong vùng bóng tối sâu nhất) đều phải đọc đúng!
    assert detected.get("q1") == "optA", f"Kỳ vọng optA nhưng nhận được {detected.get('q1')}"
    assert detected.get("q2") == "5", f"Kỳ vọng '5' nhưng nhận được {detected.get('q2')}"
    assert confidences.get("q1", 0) >= 0.70
    assert confidences.get("q2", 0) >= 0.70

