import cv2
import numpy as np
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.engine.quality_engine import QualityEngine

def test_diagonal_staircase_pattern_detection():
    """
    Kiểm thử phát hiện mẫu điền đường chéo bậc thang (Monotonic Diagonal Pattern):
    1 -> 2 -> 3 -> 4 -> 5 hoặc 5 -> 4 -> 3 -> 2 -> 1 trên các câu hỏi Likert
    """
    questions = [
        {"id": f"q_likert_{i}", "question_type": "likert", "title": f"Tiêu chí {i}", "options": []}
        for i in range(1, 6)
    ]

    # Ca 1: Tăng dần đều 1 -> 2 -> 3 -> 4 -> 5
    answers_inc = {f"q_likert_{i}": str(i) for i in range(1, 6)}
    res_inc = QualityEngine.analyze_response(
        new_answers=answers_inc,
        duration_seconds=60.0,
        questions=questions,
        prior_responses=[]
    )
    flag_codes_inc = [f["code"] for f in res_inc["flags"]]
    assert "FLAG_DIAGONAL_PATTERN" in flag_codes_inc
    assert res_inc["score_pattern"] >= 80.0

    # Ca 2: Giảm dần đều 5 -> 4 -> 3 -> 2 -> 1
    answers_dec = {f"q_likert_{i}": str(6 - i) for i in range(1, 6)}
    res_dec = QualityEngine.analyze_response(
        new_answers=answers_dec,
        duration_seconds=60.0,
        questions=questions,
        prior_responses=[]
    )
    flag_codes_dec = [f["code"] for f in res_dec["flags"]]
    assert "FLAG_DIAGONAL_PATTERN" in flag_codes_dec
    assert res_dec["score_pattern"] >= 80.0

def test_zigzag_alternating_pattern_detection():
    """
    Kiểm thử phát hiện mẫu zíc-zắc xen kẽ hai cực (Alternating Zig-Zag Pattern):
    1 -> 5 -> 1 -> 5 -> 1
    """
    questions = [
        {"id": f"q_likert_{i}", "question_type": "likert", "title": f"Tiêu chí {i}", "options": []}
        for i in range(1, 6)
    ]

    answers_zigzag = {
        "q_likert_1": "1",
        "q_likert_2": "5",
        "q_likert_3": "1",
        "q_likert_4": "5",
        "q_likert_5": "1"
    }

    res = QualityEngine.analyze_response(
        new_answers=answers_zigzag,
        duration_seconds=60.0,
        questions=questions,
        prior_responses=[]
    )
    flag_codes = [f["code"] for f in res["flags"]]
    assert "FLAG_ZIGZAG_PATTERN" in flag_codes
    assert res["score_pattern"] >= 75.0

def test_configurable_quality_sensitivity():
    """
    Kiểm thử cấu hình độ nhạy kiểm định chất lượng:
    - Chế độ Standard: 75% lặp lại chưa bị cờ FLAG_STRAIGHTLINING (ngưỡng 85%).
    - Chế độ Strict: 75% lặp lại đã bị cờ FLAG_STRAIGHTLINING (ngưỡng 75%).
    """
    questions = [
        {"id": f"q_scale_{i}", "question_type": "linear_scale", "title": f"Mục {i}", "options": []}
        for i in range(1, 5)
    ]
    # 3/4 câu trả lời chọn "5" (75%)
    answers_75pct = {
        "q_scale_1": "5",
        "q_scale_2": "5",
        "q_scale_3": "5",
        "q_scale_4": "2"
    }

    # Đánh giá với chế độ Standard
    res_std = QualityEngine.analyze_response(
        new_answers=answers_75pct,
        duration_seconds=30.0,
        questions=questions,
        prior_responses=[],
        quality_settings={"sensitivity": "standard"}
    )
    flags_std = [f["code"] for f in res_std["flags"]]
    assert "FLAG_STRAIGHTLINING" not in flags_std
    assert "FLAG_REPETITIVE_PATTERN" in flags_std

    # Đánh giá với chế độ Strict
    res_strict = QualityEngine.analyze_response(
        new_answers=answers_75pct,
        duration_seconds=30.0,
        questions=questions,
        prior_responses=[],
        quality_settings={"sensitivity": "strict"}
    )
    flags_strict = [f["code"] for f in res_strict["flags"]]
    assert "FLAG_STRAIGHTLINING" in flags_strict

def test_reanalyze_all_responses_endpoint(client: TestClient):
    """
    Kiểm thử API tái phân tích chất lượng toàn bộ phản hồi:
    POST /api/surveys/{survey_id}/responses/re-analyze
    """
    # 1. Tạo khảo sát
    cr_res = client.post("/api/surveys", json={
        "title": "Khảo sát Thử nghiệm Tái Phân Tích",
        "description": "Kiểm tra re-analyze endpoint"
    })
    assert cr_res.status_code == 201
    survey_id = cr_res.json()["id"]

    # Thêm câu hỏi
    q_payload = [
        {
            "id": f"q_diag_{i}",
            "question_type": "likert",
            "title": f"Câu Likert {i}",
            "order_index": i,
            "is_required": True,
            "options": [{"id": str(j), "label": str(j)} for j in range(1, 6)],
            "logic_rules": []
        }
        for i in range(1, 6)
    ]
    client.put(f"/api/surveys/{survey_id}", json={"questions": q_payload})
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    slug = pub_res.json()["public_slug"]

    # 2. Nộp 1 phản hồi có mẫu đường chéo 1 -> 2 -> 3 -> 4 -> 5
    now = datetime.now(timezone.utc)
    sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=60)).isoformat(),
        "submitted_at": now.isoformat(),
        "answers": {f"q_diag_{i}": str(i) for i in range(1, 6)}
    }, headers={"X-Test-Bypass": "1"})
    assert sub_res.status_code == 201

    # 3. Kích hoạt API re-analyze
    re_res = client.post(f"/api/surveys/{survey_id}/responses/re-analyze")
    assert re_res.status_code == 200
    data = re_res.json()
    assert data["total_reanalyzed"] == 1
    assert data["survey_id"] == survey_id

    # 4. Kiểm tra chi tiết đánh giá đã cập nhật cờ FLAG_DIAGONAL_PATTERN
    detail = client.get(f"/api/surveys/{survey_id}/responses/{sub_res.json()['response_id']}").json()
    assert detail["assessment"]["score_pattern"] >= 80.0
    assert any(f["code"] == "FLAG_DIAGONAL_PATTERN" for f in detail["assessment"]["flags"])

def test_batch_paper_scan_endpoint(client: TestClient):
    """
    Kiểm thử API bóc tách ảnh phiếu giấy theo lô (Batch Scan):
    POST /api/surveys/{survey_id}/paper/batch-scan
    """
    # Tạo khảo sát và lấy template
    cr_res = client.post("/api/surveys", json={"title": "Khảo sát Batch Scan Test"})
    survey_id = cr_res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [{
            "id": "q_b1",
            "question_type": "single_choice",
            "title": "Lựa chọn thử nghiệm",
            "is_required": True,
            "options": [{"id": "opt1", "label": "A"}, {"id": "opt2", "label": "B"}]
        }]
    })

    # Tạo 2 ảnh giả lập hợp lệ
    img1 = np.ones((800, 600, 3), dtype=np.uint8) * 255
    cv2.rectangle(img1, (30, 30), (70, 70), (0, 0, 0), -1)
    cv2.rectangle(img1, (530, 30), (570, 70), (0, 0, 0), -1)
    cv2.rectangle(img1, (30, 730), (70, 770), (0, 0, 0), -1)
    cv2.rectangle(img1, (530, 730), (570, 770), (0, 0, 0), -1)
    _, buf1 = cv2.imencode(".png", img1)

    img2 = np.ones((800, 600, 3), dtype=np.uint8) * 255
    cv2.rectangle(img2, (30, 30), (70, 70), (0, 0, 0), -1)
    cv2.rectangle(img2, (530, 30), (570, 70), (0, 0, 0), -1)
    cv2.rectangle(img2, (30, 730), (70, 770), (0, 0, 0), -1)
    cv2.rectangle(img2, (530, 730), (570, 770), (0, 0, 0), -1)
    _, buf2 = cv2.imencode(".png", img2)

    files = [
        ("files", ("sheet1.png", buf1.tobytes(), "image/png")),
        ("files", ("sheet2.png", buf2.tobytes(), "image/png")),
    ]

    res = client.post(f"/api/surveys/{survey_id}/paper/batch-scan", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["total_files"] == 2
    assert data["success_count"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["filename"] == "sheet1.png"
    assert data["results"][1]["filename"] == "sheet2.png"
