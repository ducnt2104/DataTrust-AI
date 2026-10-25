import base64
import json
import math
import uuid
from typing import Dict, List, Any, Optional, Tuple
import cv2
import numpy as np

class OMREngine:
    """
    DataTrust Field Survey Digitization & Optical Mark Recognition (OMR) Engine.
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
    def generate_printable_html(
        cls,
        survey: Dict[str, Any],
        questions: List[Dict[str, Any]],
        form_id: str = "",
        enumerator_id: str = "DTV-01"
    ) -> str:
        """
        Sinh mã HTML chuẩn A4 in ấn độ nét cao (Printable Paper Sheet)
        chứa 4 mốc căn góc màu đen (Fiducial markers), mã QR định danh và lưới ô tích OMR.
        """
        import qrcode
        import io

        if not form_id:
            form_id = f"FORM-{uuid.uuid4().hex[:8].upper()}"

        survey_id = survey.get("id", "")
        title = survey.get("title", "Khảo sát DataTrust")
        desc = survey.get("description", "")
        instructions = survey.get("instructions", "Dùng bút chì 2B hoặc bút bi đen tô kín hình tròn. Không gập mép tờ phiếu.")

        qr_payload = json.dumps({
            "survey_id": survey_id,
            "form_id": form_id,
            "enumerator_id": enumerator_id
        }, ensure_ascii=False)

        qr = qrcode.QRCode(box_size=5, border=1)
        qr.add_data(qr_payload)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        qr_data_uri = f"data:image/png;base64,{qr_b64}"

        q_html_parts = []
        for idx, q in enumerate(questions, start=1):
            q_type = q.get("question_type", "single_choice")
            q_title = q.get("title", f"Câu hỏi {idx}")
            raw_options = q.get("options", [])
            options = raw_options if isinstance(raw_options, list) else []

            bubble_html = ""
            if q_type in ("single_choice", "multiple_choice", "dropdown"):
                opts_html = []
                for o_idx, opt in enumerate(options[:6]):
                    label = opt.get("label", opt.get("text", str(opt))) if isinstance(opt, dict) else str(opt)
                    letter = chr(65 + o_idx) if o_idx < 26 else str(o_idx + 1)
                    opts_html.append(f"""
                        <div class="omr-choice">
                            <span class="omr-bubble"></span>
                            <span class="omr-choice-label"><strong>{letter}.</strong> {label}</span>
                        </div>
                    """)
                bubble_html = f"""<div class="omr-choice-grid">{''.join(opts_html)}</div>"""

            elif q_type in ("rating", "likert", "linear_scale"):
                steps_html = []
                for s in range(1, 6):
                    steps_html.append(f"""
                        <div class="omr-scale-item">
                            <span class="omr-bubble"></span>
                            <span class="omr-scale-label">{s}</span>
                        </div>
                    """)
                bubble_html = f"""
                    <div class="omr-scale-container">
                        <span class="scale-hint">Rất không hài lòng (1)</span>
                        <div class="omr-scale-row">{''.join(steps_html)}</div>
                        <span class="scale-hint">Rất hài lòng (5)</span>
                    </div>
                """

            elif q_type == "boolean":
                bubble_html = """
                    <div class="omr-choice-grid">
                        <div class="omr-choice"><span class="omr-bubble"></span><span class="omr-choice-label">Có (Đồng ý)</span></div>
                        <div class="omr-choice"><span class="omr-bubble"></span><span class="omr-choice-label">Không (Không đồng ý)</span></div>
                    </div>
                """

            elif q_type in ("short_text", "number"):
                boxes = "".join(['<span class="char-box"></span>' for _ in range(12)])
                bubble_html = f"""
                    <div class="text-write-in">
                        <div class="char-boxes">{boxes}</div>
                        <span class="text-hint">Viết chữ/số in hoa rõ ràng vào từng ô</span>
                    </div>
                """
            else:
                bubble_html = """<div class="free-text-line"></div>"""

            q_html_parts.append(f"""
                <div class="omr-question-block">
                    <div class="omr-q-header">
                        <span class="omr-q-num">Câu {idx}.</span>
                        <span class="omr-q-title">{q_title}</span>
                    </div>
                    {bubble_html}
                </div>
            """)

        questions_html = "".join(q_html_parts)

        return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Phiếu Khảo Sát Giấy — {title} | DataTrust</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 0;
        }}
        * {{
            box-sizing: border-box;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        body {{
            margin: 0;
            padding: 0;
            background-color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #0f172a;
        }}
        .no-print {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #1e293b;
            color: white;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 9999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-size: 13px;
        }}
        .no-print button {{
            background: #4f46e5;
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .no-print button:hover {{
            background: #4338ca;
        }}
        .a4-page {{
            width: 210mm;
            min-height: 297mm;
            margin: 60px auto 40px auto;
            background: white;
            position: relative;
            box-shadow: 0 8px 30px rgba(0,0,0,0.1);
            padding: 18mm 16mm 18mm 16mm;
        }}
        .fiducial {{
            position: absolute;
            width: 12mm;
            height: 12mm;
            background-color: black;
        }}
        .fiducial-tl {{ top: 6mm; left: 6mm; }}
        .fiducial-tr {{ top: 6mm; right: 6mm; }}
        .fiducial-bl {{ bottom: 6mm; left: 6mm; }}
        .fiducial-br {{ bottom: 6mm; right: 6mm; }}

        .survey-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0f172a;
            padding-bottom: 12px;
            margin-bottom: 12px;
        }}
        .header-left {{
            max-width: 75%;
        }}
        .brand-badge {{
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.5px;
            color: #4f46e5;
            text-transform: uppercase;
        }}
        .survey-title {{
            font-size: 18px;
            font-weight: 900;
            margin: 4px 0;
            text-transform: uppercase;
            line-height: 1.3;
        }}
        .survey-desc {{
            font-size: 11px;
            color: #475569;
            margin: 2px 0 8px 0;
        }}
        .meta-strip {{
            display: flex;
            gap: 16px;
            font-size: 10.5px;
            font-family: monospace;
            color: #334155;
            background: #f8fafc;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
        }}
        .qr-card {{
            text-align: center;
            border: 1px solid #cbd5e1;
            padding: 4px;
            border-radius: 6px;
            background: #ffffff;
        }}
        .qr-card img {{
            width: 80px;
            height: 80px;
            display: block;
        }}
        .qr-label {{
            font-size: 8px;
            font-family: monospace;
            color: #64748b;
            margin-top: 2px;
        }}
        .instruction-box {{
            background: #f1f5f9;
            border-left: 3px solid #4f46e5;
            padding: 6px 10px;
            font-size: 10px;
            color: #334155;
            margin-bottom: 14px;
            border-radius: 0 4px 4px 0;
        }}
        .omr-question-block {{
            margin-bottom: 11px;
            padding-bottom: 9px;
            border-bottom: 1px dashed #e2e8f0;
            page-break-inside: avoid;
        }}
        .omr-q-header {{
            font-size: 12px;
            margin-bottom: 6px;
        }}
        .omr-q-num {{
            font-weight: 800;
            color: #1e293b;
        }}
        .omr-q-title {{
            font-weight: 600;
            color: #0f172a;
        }}
        .omr-choice-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px 24px;
        }}
        .omr-choice {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            min-width: 140px;
        }}
        .omr-bubble {{
            width: 14px;
            height: 14px;
            border: 1.5px solid #0f172a;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
            background: white;
        }}
        .omr-choice-label {{
            color: #1e293b;
        }}
        .omr-scale-container {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            max-width: 420px;
            margin: 4px 0;
        }}
        .omr-scale-row {{
            display: flex;
            gap: 20px;
        }}
        .omr-scale-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 3px;
        }}
        .omr-scale-label {{
            font-size: 10px;
            font-weight: bold;
        }}
        .scale-hint {{
            font-size: 9.5px;
            color: #64748b;
            font-style: italic;
        }}
        .char-boxes {{
            display: flex;
            gap: 3px;
            margin-top: 4px;
        }}
        .char-box {{
            width: 18px;
            height: 22px;
            border: 1px solid #475569;
            display: inline-block;
            background: #ffffff;
        }}
        .text-hint {{
            font-size: 9px;
            color: #64748b;
            margin-top: 2px;
            display: block;
        }}
        .free-text-line {{
            width: 100%;
            height: 20px;
            border-bottom: 1px solid #94a3b8;
            margin-top: 4px;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .no-print {{
                display: none !important;
            }}
            .a4-page {{
                margin: 0;
                box-shadow: none;
                width: 100%;
                min-height: 100vh;
                padding: 16mm 14mm 16mm 14mm;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <div>
            <strong>DATATRUST — BẢN IN PHIẾU KHẢO SÁT CHUẨN OMR (A4)</strong>
            <span style="margin-left: 12px; color: #94a3b8;">Chọn tỷ lệ in 100% (Actual size) để OpenCV nhận diện chính xác.</span>
        </div>
        <div>
            <button onclick="window.print()">🖨️ In Phiếu Ngay (Ctrl + P)</button>
        </div>
    </div>

    <div class="a4-page">
        <div class="fiducial fiducial-tl"></div>
        <div class="fiducial fiducial-tr"></div>
        <div class="fiducial fiducial-bl"></div>
        <div class="fiducial fiducial-br"></div>

        <div class="survey-header">
            <div class="header-left">
                <div class="brand-badge">DATATRUST VERIFIED FIELD SURVEY</div>
                <h1 class="survey-title">{title}</h1>
                {f'<p class="survey-desc">{desc}</p>' if desc else ''}
                <div class="meta-strip">
                    <span>MÃ KHẢO SÁT: <strong>{survey_id[:8].upper()}</strong></span>
                    <span>MÃ PHIẾU: <strong>{form_id}</strong></span>
                    <span>ĐTV: <strong>{enumerator_id}</strong></span>
                    <span>NGÀY: ____/____/2026</span>
                </div>
            </div>
            <div class="qr-card">
                <img src="{qr_data_uri}" alt="QR Định Danh" />
                <div class="qr-label">{form_id}</div>
            </div>
        </div>

        <div class="instruction-box">
            <strong>HƯỚNG DẪN TÔ PHIẾU OMR:</strong> {instructions} Dùng bút chì 2B hoặc bút đen tô kín hình tròn <strong>(●)</strong> tương ứng. Không đánh dấu tick <strong>(✓)</strong> hoặc gạch chéo <strong>(✗)</strong>.
        </div>

        <div class="questions-container">
            {questions_html}
        </div>
    </div>
</body>
</html>"""

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
    def auto_orient_page(cls, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Tự động nhận diện và sửa góc xoay trang phiếu (0°, 90°, 180°, 270°).
        Quy trình xác thực đa tầng:
        1. Kiểm tra tỷ lệ khung hình: nếu ảnh ngang (w > h), tự động xoay 90° clockwise sang dọc.
        2. Thử giải mã mã QR ở các góc: nếu QR giải mã thành công tại góc nào, xác lập góc đó là chuẩn.
        3. Fallback phân tích trọng tâm mật độ nét đen (Header Density): phần đầu phiếu chứa tiêu đề,
           mã định danh và QR luôn có mật độ nét đen cao hơn lề dưới cùng của trang.
        Trả về (ảnh_đã_xoay_chuẩn, góc_xoay_đã_thực_hiện).
        """
        cur_img = image.copy()
        total_rot = 0
        h, w = cur_img.shape[:2]

        # Bước 1: Nếu ảnh đang ở chế độ chụp ngang (Landscape), xoay 90 độ clockwise để đưa về dọc (Portrait)
        if w > h:
            cur_img = cv2.rotate(cur_img, cv2.ROTATE_90_CLOCKWISE)
            total_rot = (total_rot + 90) % 360
            h, w = cur_img.shape[:2]

        # Bước 2: Kiểm tra vị trí mã QR
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(cur_img)
        if data and points is not None and len(points) > 0:
            qr_center = np.mean(points[0], axis=0)
            # Trong chuẩn layout A4 DataTrust, mã QR luôn nằm ở góc trên bên phải (y < h / 2)
            if qr_center[1] > h / 2:
                # Mã QR đang nằm ở nửa dưới -> trang bị lộn ngược đầu 180°
                cur_img = cv2.rotate(cur_img, cv2.ROTATE_180)
                total_rot = (total_rot + 180) % 360
            return cur_img, total_rot

        # Bước 3: Nếu chưa tìm thấy QR (ví dụ ảnh chụp cận cảnh hoặc mock không có QR hoàn chỉnh),
        # kiểm tra mật độ nét ở 22% trên so với 22% dưới của trang.
        gray = cv2.cvtColor(cur_img, cv2.COLOR_BGR2GRAY) if len(cur_img.shape) == 3 else cur_img
        top_band = gray[:int(h * 0.22), :]
        bottom_band = gray[int(h * 0.78):, :]

        # Đếm pixel tối (giá trị < 180)
        top_dark_ratio = float(np.mean(top_band < 180))
        bot_dark_ratio = float(np.mean(bottom_band < 180))

        # Nếu dải dưới lại tối hơn dải trên rõ rệt (do lộn ngược đầu)
        if bot_dark_ratio > top_dark_ratio * 1.25 and bot_dark_ratio > 0.005:
            cur_img = cv2.rotate(cur_img, cv2.ROTATE_180)
            total_rot = (total_rot + 180) % 360

        return cur_img, total_rot

    @classmethod
    def normalize_illumination(cls, gray: np.ndarray) -> np.ndarray:
        """
        Khử bóng tối và cân bằng độ sáng phi tuyến (Illumination & Shadow Normalization).
        Sử dụng kỹ thuật Morphological Background Division kết hợp CLAHE
        để loại bỏ bóng đổ không đều (bóng tay, bóng điện thoại, ánh sáng đèn góc)
        đồng thời làm nổi bật vết chì tô ô tròn.
        """
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

        # 1. Ước lượng độ sáng nền bằng phép đóng hình thái học (Morphological Closing) với kernel lớn
        kernel_size = max(21, min(gray.shape) // 30)
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

        # 2. Phép chia nền: (gray / background) * 255
        norm = np.clip((gray.astype(np.float32) / (background.astype(np.float32) + 1e-5)) * 255.0, 0, 255).astype(np.uint8)

        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization) tăng cường tương phản
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(norm)
        return enhanced

    @classmethod
    def normalize_perspective(
        cls,
        image: np.ndarray,
        corners: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Nắn phẳng phối cảnh ảnh (Perspective Transform) về tỷ lệ kích thước chuẩn A4 (1240 x 1754).
        Tự động nhận dạng và chuẩn hóa chiều xoay (auto-orient) để phiếu luôn đúng chiều dọc.
        """
        w = cls.PAGE_WIDTH
        h = cls.PAGE_HEIGHT

        proc_img = image
        # Tự động xoay về portrait nếu ảnh đầu vào đang là landscape
        if proc_img.shape[1] > proc_img.shape[0]:
            proc_img = cv2.rotate(proc_img, cv2.ROTATE_90_CLOCKWISE)

        if corners is None:
            corners = cls.detect_fiducial_markers(proc_img)

        if corners is None:
            # Fallback: Nếu không tìm thấy 4 mốc căn góc (ảnh scan phẳng sẵn), resize trực tiếp
            warped = cv2.resize(proc_img, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
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
            warped = cv2.warpPerspective(proc_img, matrix, (w, h), flags=cv2.INTER_LINEAR)

        # Kiểm tra xem ảnh nắn phẳng có bị lộn ngược đầu không (auto-orient)
        oriented_warped, _ = cls.auto_orient_page(warped)
        return oriented_warped

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
        Tự động khử bóng đổ và cân bằng ánh sáng phi tuyến trước khi nhị phân hóa.
        """
        gray = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY) if len(warped_image.shape) == 3 else warped_image

        # Cân bằng ánh sáng & khử bóng đổ
        enhanced_gray = cls.normalize_illumination(gray)

        # Nhị phân hóa Otsu đảo ngược (mực bút đen = pixel 255)
        blurred = cv2.GaussianBlur(enhanced_gray, (3, 3), 0)
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

        # 2. Vẽ QR định danh
        qr_reg = template_layout.get("qr_region", {})
        if qr_reg:
            qx, qy, qw, qh = qr_reg["x"], qr_reg["y"], qr_reg["w"], qr_reg["h"]
            try:
                import qrcode
                qr = qrcode.QRCode(box_size=3, border=1)
                qr.add_data(json.dumps({
                    "survey_id": template_layout.get("survey_id", "s1"),
                    "form_id": f"FORM-{uuid.uuid4().hex[:8].upper()}",
                    "enumerator_id": "DTV-TEST"
                }))
                qr.make(fit=True)
                qr_pil = qr.make_image(fill_color="black", back_color="white")
                qr_arr = np.array(qr_pil.convert("RGB"))
                qr_resized = cv2.resize(qr_arr, (qw, qh), interpolation=cv2.INTER_NEAREST)
                img[qy:qy+qh, qx:qx+qw] = qr_resized
            except Exception:
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
