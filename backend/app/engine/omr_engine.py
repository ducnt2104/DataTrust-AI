import base64
import json
import math
import uuid
from typing import Dict, List, Any, Optional, Tuple
import cv2
import numpy as np

class OMREngine:
    """
    DataTrust AI Field Survey Digitization & Optical Mark Recognition (OMR) Engine.
    Tuân thủ quy trình 5 bước được định nghĩa trong Bản Thuyết Minh Dự Án:
    1. Chụp & Chuẩn hóa ảnh: Phát hiện 4 mốc góc tờ phiếu, nắn phẳng phối cảnh 2D (warpPerspective), kiểm tra mờ (Laplacian).
    2. Giải mã QR & Siêu dữ liệu: Lấy survey_id, form_id, enumerator_id.
    3. Nhận dạng ô tích (OMR): Đo tỷ lệ điểm ảnh tối (Pixel Fill Ratio) theo lưới tọa độ chuẩn hóa.
    4. Sinh lớp phủ minh chứng (Visual Overlay): Tô sáng ô nhận diện để hiển thị trên giao diện xác nhận nhanh / Side-by-Side.
    5. Đánh giá độ tin cậy (Confidence Score) & Cảnh báo câu hỏi bỏ sót hoặc tích trùng lặp.
    """

    PAGE_WIDTH = 1240
    PAGE_HEIGHT = 1754
    MARKER_SIZE = 48
    BUBBLE_RADIUS = 14
    FILL_THRESHOLD = 0.35  # Tỷ lệ pixel tối >= 35% xem là đã tích
    AMBIGUOUS_THRESHOLD = 0.22  # Tỷ lệ 22% - 35% là chưa chắc chắn

    @classmethod
    def generate_paper_template(
        cls,
        survey: Dict[str, Any],
        questions: List[Dict[str, Any]],
        template_version: int = 1
    ) -> Dict[str, Any]:
        """
        Sinh cấu hình tọa độ chuẩn hóa (Layout Template) cho mẫu phiếu A4
        với 4 dấu căn góc và lưới ô tích cho từng câu hỏi.
        """
        w = cls.PAGE_WIDTH
        h = cls.PAGE_HEIGHT
        m_size = cls.MARKER_SIZE
        margin = 40

        # 4 mốc căn góc (Fiducial markers) tại 4 góc trang giấy
        fiducial_markers = [
            {"id": "top_left", "x": margin, "y": margin, "w": m_size, "h": m_size},
            {"id": "top_right", "x": w - margin - m_size, "y": margin, "w": m_size, "h": m_size},
            {"id": "bottom_right", "x": w - margin - m_size, "y": h - margin - m_size, "w": m_size, "h": m_size},
            {"id": "bottom_left", "x": margin, "y": h - margin - m_size, "w": m_size, "h": m_size}
        ]

        # Vùng chứa mã QR định danh ở góc trên bên phải
        qr_region = {
            "x": w - margin - m_size - 180,
            "y": margin + 10,
            "w": 160,
            "h": 160
        }

        # Bố trí các khối câu hỏi và ô tích
        question_layouts = []
        curr_y = margin + m_size + 150  # Bắt đầu dưới phần Header và QR
        box_w = w - (margin * 2)

        for q in questions:
            qid = q["id"]
            q_type = q.get("question_type", "single_choice")
            title = q.get("title", "")
            raw_options = q.get("options", [])
            options = raw_options if isinstance(raw_options, list) else []

            box_h = 110
            bubbles = []

            if q_type in ("single_choice", "multiple_choice", "dropdown"):
                # Bố trí các ô tròn nằm ngang hoặc tối đa 4 ô trên 1 dòng
                opts_to_show = options[:6]
                if opts_to_show:
                    spacing = min(220, (box_w - 60) // max(1, len(opts_to_show)))
                    for idx, opt in enumerate(opts_to_show):
                        opt_id = opt.get("id") if isinstance(opt, dict) else str(opt)
                        opt_label = opt.get("label", opt_id) if isinstance(opt, dict) else str(opt)
                        bx = margin + 50 + (idx * spacing)
                        by = curr_y + 68
                        bubbles.append({
                            "option_id": opt_id,
                            "option_label": opt_label,
                            "x": bx,
                            "y": by,
                            "radius": cls.BUBBLE_RADIUS
                        })
            elif q_type in ("likert", "linear_scale"):
                # Thang đo 1-5 điểm chuẩn
                scale_steps = 5
                spacing = (box_w - 120) // scale_steps
                for step in range(1, scale_steps + 1):
                    bx = margin + 60 + ((step - 1) * spacing)
                    by = curr_y + 68
                    bubbles.append({
                        "option_id": str(step),
                        "option_label": f"Mức {step}",
                        "x": bx,
                        "y": by,
                        "radius": cls.BUBBLE_RADIUS
                    })
            elif q_type == "yes_no":
                for idx, (val, lbl) in enumerate([("yes", "Đồng ý / Có"), ("no", "Không đồng ý / Không")]):
                    bx = margin + 100 + (idx * 260)
                    by = curr_y + 68
                    bubbles.append({
                        "option_id": val,
                        "option_label": lbl,
                        "x": bx,
                        "y": by,
                        "radius": cls.BUBBLE_RADIUS
                    })
            else:
                # Với short_text/number: ô đánh dấu ghi nhận có câu trả lời
                bx = margin + 80
                by = curr_y + 68
                bubbles.append({
                    "option_id": "filled",
                    "option_label": "Đã điền thông tin",
                    "x": bx,
                    "y": by,
                    "radius": cls.BUBBLE_RADIUS
                })

            question_layouts.append({
                "question_id": qid,
                "question_type": q_type,
                "title": title,
                "order_index": q.get("order_index", 0),
                "box_x": margin,
                "box_y": curr_y,
                "box_w": box_w,
                "box_h": box_h,
                "bubbles": bubbles
            })
            curr_y += box_h + 20

        return {
            "survey_id": survey["id"],
            "survey_title": survey["title"],
            "template_version": template_version,
            "page_width": w,
            "page_height": h,
            "fiducial_markers": fiducial_markers,
            "qr_region": qr_region,
            "questions": question_layouts
        }

    @classmethod
    def assess_image_quality(cls, image: np.ndarray) -> Dict[str, Any]:
        """
        Kiểm tra chất lượng ảnh chụp: độ nét (phương sai Laplacian), độ sáng và tương phản.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        mean_brightness = float(np.mean(gray))
        std_contrast = float(np.std(gray))

        # Đánh giá độ nét
        if laplacian_var >= 100.0:
            sharpness_status = "sharp"
        elif laplacian_var >= 50.0:
            sharpness_status = "acceptable"
        else:
            sharpness_status = "blurry"

        is_passed = (sharpness_status != "blurry") and (30.0 <= mean_brightness <= 254.5)

        return {
            "is_passed": is_passed,
            "laplacian_variance": round(laplacian_var, 2),
            "sharpness_status": sharpness_status,
            "mean_brightness": round(mean_brightness, 1),
            "contrast_std": round(std_contrast, 1),
            "message": "Ảnh đạt tiêu chuẩn độ nét số hóa." if is_passed else "Ảnh chụp bị mờ hoặc thiếu sáng, vui lòng giữ chắc điện thoại và chụp lại."
        }

    @classmethod
    def detect_fiducial_markers(cls, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Tìm 4 mốc căn góc màu đen ở 4 góc của tờ phiếu bằng contour analysis.
        Trả về 4 điểm góc [Top-Left, Top-Right, Bottom-Right, Bottom-Left].
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        h, w = gray.shape

        # Khử nhiễu nhẹ và nhị phân hóa
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        img_area = h * w
        min_marker_area = img_area * 0.0003  # ~ 0.03% diện tích
        max_marker_area = img_area * 0.03    # ~ 3% diện tích

        candidate_boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if min_marker_area <= area <= max_marker_area:
                perimeter = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)
                # Kiểm tra hình tứ giác xấp xỉ vuông
                if len(approx) == 4:
                    x, y, bw, bh = cv2.boundingRect(approx)
                    aspect = float(bw) / float(bh) if bh > 0 else 0
                    if 0.70 <= aspect <= 1.45:
                        M = cv2.moments(c)
                        if M["m00"] > 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            candidate_boxes.append((cx, cy, x, y, bw, bh))

        if len(candidate_boxes) < 4:
            return None

        # Phân chia theo 4 phần tư màn hình (TL, TR, BR, BL)
        half_w = w // 2
        half_h = h // 2

        tl_cand = [b for b in candidate_boxes if b[0] < half_w and b[1] < half_h]
        tr_cand = [b for b in candidate_boxes if b[0] >= half_w and b[1] < half_h]
        br_cand = [b for b in candidate_boxes if b[0] >= half_w and b[1] >= half_h]
        bl_cand = [b for b in candidate_boxes if b[0] < half_w and b[1] >= half_h]

        if not (tl_cand and tr_cand and br_cand and bl_cand):
            return None

        # Chọn mốc gần góc nhất trong từng phần tư
        tl = min(tl_cand, key=lambda b: b[0]**2 + b[1]**2)
        tr = min(tr_cand, key=lambda b: (w - b[0])**2 + b[1]**2)
        br = min(br_cand, key=lambda b: (w - b[0])**2 + (h - b[1])**2)
        bl = min(bl_cand, key=lambda b: b[0]**2 + (h - b[1])**2)

        pts = np.array([
            [tl[0], tl[1]],
            [tr[0], tr[1]],
            [br[0], br[1]],
            [bl[0], bl[1]]
        ], dtype=np.float32)

        return pts

    @classmethod
    def normalize_perspective(
        cls,
        image: np.ndarray,
        corners: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Nắn phẳng phối cảnh ảnh (Perspective Transform) về tỷ lệ kích thước chuẩn A4 (1240 x 1754).
        """
        w = cls.PAGE_WIDTH
        h = cls.PAGE_HEIGHT

        if corners is None:
            corners = cls.detect_fiducial_markers(image)

        if corners is None:
            # Fallback: Nếu không tìm thấy 4 mốc căn góc (ảnh scan phẳng sẵn), resize trực tiếp
            return cv2.resize(image, (w, h), interpolation=cv2.INTER_LINEAR)

        # 4 điểm đích trên mặt phẳng chuẩn A4 tương ứng vị trí tâm 4 mốc
        margin = 40
        m_size = cls.MARKER_SIZE
        half_m = m_size // 2

        dst_pts = np.array([
            [margin + half_m, margin + half_m],
            [w - margin - half_m, margin + half_m],
            [w - margin - half_m, h - margin - half_m],
            [margin + half_m, h - margin - half_m]
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(corners, dst_pts)
        warped = cv2.warpPerspective(image, matrix, (w, h), flags=cv2.INTER_LINEAR)
        return warped

    @classmethod
    def decode_qr(cls, image: np.ndarray) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Giải mã mã QR ở góc trên phiếu để trích xuất siêu dữ liệu (survey_id, form_id, enumerator_id).
        """
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)

        if not data:
            # Thử crop góc trên bên phải nếu quét toàn trang chưa nhận
            h, w = image.shape[:2]
            top_right_roi = image[0:int(h * 0.35), int(w * 0.5):w]
            data, _, _ = detector.detectAndDecode(top_right_roi)

        if data:
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict) and "survey_id" in parsed:
                    return parsed, "QR_VALID"
            except Exception:
                pass
            return {"raw_text": data}, "QR_RAW_TEXT"

        return None, "QR_NOT_FOUND"

    @classmethod
    def read_bubbles(
        cls,
        warped_image: np.ndarray,
        template_layout: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, float], List[str]]:
        """
        Đọc tỷ lệ điểm ảnh tối (Pixel Fill Ratio) cho từng ô tích trong phiếu chuẩn hóa.
        """
        gray = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY) if len(warped_image.shape) == 3 else warped_image

        # Nhị phân hóa Otsu đảo ngược (mực bút đen = pixel 255)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        detected_answers: Dict[str, Any] = {}
        question_confidences: Dict[str, float] = {}
        warnings: List[str] = []

        questions = template_layout.get("questions", [])
        for q in questions:
            qid = q["question_id"]
            q_type = q.get("question_type", "single_choice")
            bubbles = q.get("bubbles", [])

            bubble_scores = []
            for b in bubbles:
                bx = b["x"]
                by = b["y"]
                r = b.get("radius", cls.BUBBLE_RADIUS)

                # Cắt vùng ô tròn
                x1 = max(0, bx - r)
                y1 = max(0, by - r)
                x2 = min(cls.PAGE_WIDTH, bx + r)
                y2 = min(cls.PAGE_HEIGHT, by + r)

                roi = thresh[y1:y2, x1:x2]
                if roi.size == 0:
                    continue

                # Tạo mặt nạ hình tròn để chỉ đếm pixel trong lòng ô tích (bỏ qua viền ô)
                inner_r = max(2, r - 3)
                mask = np.zeros(roi.shape, dtype=np.uint8)
                cv2.circle(mask, (r, r), inner_r, 255, -1)

                masked_roi = cv2.bitwise_and(roi, roi, mask=mask)
                total_mask_pixels = np.count_nonzero(mask)
                fill_pixels = np.count_nonzero(masked_roi)

                fill_ratio = fill_pixels / max(1, total_mask_pixels)
                bubble_scores.append((b["option_id"], fill_ratio, b["option_label"]))

            if not bubble_scores:
                detected_answers[qid] = None
                question_confidences[qid] = 0.5
                continue

            # Phân loại theo dạng câu hỏi
            if q_type in ("single_choice", "likert", "linear_scale", "yes_no", "dropdown"):
                # Chọn ô có fill ratio cao nhất
                bubble_scores.sort(key=lambda item: item[1], reverse=True)
                top_id, top_fill, top_label = bubble_scores[0]
                second_fill = bubble_scores[1][1] if len(bubble_scores) > 1 else 0.0

                if top_fill >= cls.FILL_THRESHOLD:
                    # Kiểm tra xem có tích trùng lặp 2 ô không
                    if second_fill >= cls.FILL_THRESHOLD:
                        warnings.append(f"Câu hỏi '{q.get('title')}' phát hiện tích 2 ô cùng lúc. Vui lòng kiểm tra lại.")
                        detected_answers[qid] = top_id
                        question_confidences[qid] = 0.45
                    else:
                        detected_answers[qid] = top_id
                        question_confidences[qid] = min(0.99, round(top_fill * 1.5, 2))
                elif top_fill >= cls.AMBIGUOUS_THRESHOLD:
                    warnings.append(f"Câu hỏi '{q.get('title')}' có nét tích mờ hoặc chưa tô kín ({round(top_fill*100)}%).")
                    detected_answers[qid] = top_id
                    question_confidences[qid] = 0.60
                else:
                    detected_answers[qid] = None
                    question_confidences[qid] = 0.90  # Tự tin là người dùng để trống

            elif q_type == "multiple_choice":
                # Chấp nhận tất cả các ô vượt ngưỡng
                selected = [item[0] for item in bubble_scores if item[1] >= cls.FILL_THRESHOLD]
                detected_answers[qid] = selected
                question_confidences[qid] = 0.92 if selected else 0.85
            else:
                top_fill = bubble_scores[0][1]
                detected_answers[qid] = "Đã điền trên bản cứng" if top_fill >= cls.FILL_THRESHOLD else ""
                question_confidences[qid] = 0.85

        return detected_answers, question_confidences, warnings

    @classmethod
    def generate_visual_overlay(
        cls,
        warped_image: np.ndarray,
        template_layout: Dict[str, Any],
        detected_answers: Dict[str, Any],
        question_confidences: Dict[str, float]
    ) -> str:
        """
        Vẽ lớp phủ màu (Overlay) đánh dấu các ô đã nhận diện trên ảnh chuẩn hóa
        - Xanh lá: Ô nhận diện hợp lệ
        - Vàng cam: Ô nghi ngờ độ tin cậy thấp
        - Đỏ: Ô bị xung đột hoặc bỏ sót
        Xuất ra chuỗi Base64 Data URL để hiển thị trực tiếp trên Web.
        """
        overlay = warped_image.copy()
        if len(overlay.shape) == 2:
            overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)

        questions = template_layout.get("questions", [])
        for q in questions:
            qid = q["question_id"]
            ans = detected_answers.get(qid)
            conf = question_confidences.get(qid, 0.8)
            bubbles = q.get("bubbles", [])

            # Vẽ khung nhẹ quanh câu hỏi
            bx, by, bw, bh = q["box_x"], q["box_y"], q["box_w"], q["box_h"]
            cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (220, 220, 220), 1)

            for b in bubbles:
                x, y, r = b["x"], b["y"], b.get("radius", cls.BUBBLE_RADIUS)
                opt_id = b["option_id"]

                is_selected = False
                if isinstance(ans, list):
                    is_selected = opt_id in ans
                else:
                    is_selected = (str(ans) == str(opt_id))

                if is_selected:
                    color = (46, 184, 92) if conf >= 0.70 else (0, 165, 255)  # Xanh lá hoặc Cam
                    cv2.circle(overlay, (x, y), r + 4, color, 3)
                    cv2.circle(overlay, (x, y), 4, color, -1)
                else:
                    cv2.circle(overlay, (x, y), r, (180, 180, 180), 1)

        # Vẽ 4 mốc căn góc màu xanh dương
        for m in template_layout.get("fiducial_markers", []):
            mx, my, mw, mh = m["x"], m["y"], m["w"], m["h"]
            cv2.rectangle(overlay, (mx, my), (mx + mw, my + mh), (255, 120, 0), 2)

        # Encode sang JPEG Base64
        _, buffer = cv2.imencode(".jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64_str = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"

    @classmethod
    def synthesize_mock_paper_scan(
        cls,
        template_layout: Dict[str, Any],
        answers_to_fill: Dict[str, Any],
        add_noise: bool = False
    ) -> np.ndarray:
        """
        Sinh ảnh phiếu giấy chuẩn hóa để phục vụ kiểm thử tự động (Unit Test / Benchmark)
        mà không cần thiết bị ngoại vi vật lý.
        """
        w = cls.PAGE_WIDTH
        h = cls.PAGE_HEIGHT
        img = np.ones((h, w, 3), dtype=np.uint8) * 255

        # 1. Vẽ 4 mốc căn góc
        for m in template_layout.get("fiducial_markers", []):
            x, y, mw, mh = m["x"], m["y"], m["w"], m["h"]
            cv2.rectangle(img, (x, y), (x + mw, y + mh), (15, 15, 15), -1)

        # 2. Vẽ khung QR giả lập
        qr_reg = template_layout.get("qr_region", {})
        if qr_reg:
            qx, qy, qw, qh = qr_reg["x"], qr_reg["y"], qr_reg["w"], qr_reg["h"]
            cv2.rectangle(img, (qx, qy), (qx + qw, qy + qh), (50, 50, 50), 2)
            cv2.putText(img, "DATA TRUST QR", (qx + 15, qy + qh // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)

        # 3. Vẽ các câu hỏi và tô các ô tương ứng với answers_to_fill
        for q in template_layout.get("questions", []):
            qid = q["question_id"]
            target_ans = answers_to_fill.get(qid)

            # Vẽ tiêu đề câu hỏi
            cv2.putText(img, f"Q{q['order_index'] + 1}. {q['title'][:45]}", (q["box_x"] + 10, q["box_y"] + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2)

            for b in q.get("bubbles", []):
                bx, by, r = b["x"], b["y"], b.get("radius", cls.BUBBLE_RADIUS)
                opt_id = b["option_id"]

                # Vẽ vòng tròn ô tích
                cv2.circle(img, (bx, by), r, (60, 60, 60), 2)
                cv2.putText(img, b["option_label"][:15], (bx + r + 8, by + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1)

                is_filled = False
                if isinstance(target_ans, list):
                    is_filled = opt_id in target_ans
                elif target_ans is not None:
                    is_filled = (str(target_ans) == str(opt_id))

                if is_filled:
                    # Tô đậm ô tròn như bút mực thật
                    cv2.circle(img, (bx, by), r - 2, (20, 20, 20), -1)

        if add_noise:
            # Thêm nhiễu nhẹ Gaussian và làm mờ nhẹ
            noise = np.random.normal(0, 5, img.shape).astype(np.uint8)
            img = cv2.add(img, noise)

        return img
