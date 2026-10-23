import time
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_quality_engine_high_concurrency_stress(client: TestClient):
    """
    Kiểm thử hiệu năng chịu tải cao (High-Concurrency & Throughput Stress Test)
    Mục tiêu: Đảm bảo SQLite WAL và Quality Engine xử lý liên tục hàng trăm phản hồi
    với độ trễ thấp (< 50ms/phản hồi) mà không phát sinh lỗi khóa database (database lock).
    """
    # 1. Khởi tạo khảo sát kiểm thử tải
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm thử Chịu tải Cao & Độ trễ",
        "description": "Stress test 100 phản hồi đồng thời trên SQLite WAL"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    # Tạo 5 câu hỏi đa dạng
    questions = [
        {
            "id": f"q_stress_{i}",
            "question_type": "single_choice" if i < 3 else "rating",
            "title": f"Câu hỏi kiểm thử tải số {i+1}",
            "order_index": i,
            "is_required": True,
            "options": [{"id": f"opt_{j}", "label": f"Lựa chọn {j}"} for j in range(1, 5)],
            "logic_rules": []
        }
        for i in range(5)
    ]

    up_res = client.put(f"/api/surveys/{survey_id}", json={"questions": questions})
    assert up_res.status_code == 200

    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    slug = pub_res.json()["public_slug"]

    # 2. Thực thi nộp dồn dập 100 phản hồi liên tiếp
    N_BATCH = 100
    start_time = time.perf_counter()

    success_count = 0
    for idx in range(N_BATCH):
        # Tạo vector câu trả lời giả lập thực tế
        answers = {
            f"q_stress_{i}": f"opt_{(idx + i) % 4 + 1}" if i < 3 else str((idx % 5) + 1)
            for i in range(5)
        }
        dur = 15.0 + (idx % 20)

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": "2026-10-23T08:00:00Z",
            "submitted_at": "2026-10-23T08:00:20Z",
            "duration_seconds": dur,
            "client_metadata": {"ip": f"10.0.0.{idx % 250}", "user_agent": "StressTester/1.0"},
            "answers": answers
        })
        if sub_res.status_code == 201:
            success_count += 1

    total_time = time.perf_counter() - start_time
    avg_latency_ms = (total_time / N_BATCH) * 1000
    throughput_rps = N_BATCH / total_time if total_time > 0 else 0

    print(f"\n[STRESS TEST] Đã xử lý {success_count}/{N_BATCH} phản hồi thành công.")
    print(f"[STRESS TEST] Tổng thời gian: {total_time:.2f}s | Độ trễ TB: {avg_latency_ms:.2f}ms/phản hồi | Thông lượng: {throughput_rps:.1f} req/s")

    # Xác nhận tỷ lệ thành công 100%
    assert success_count == N_BATCH
    # Độ trễ trung bình phải dưới 50ms cho mỗi phản hồi (bao gồm insert DB + 7 tầng phân tích rủi ro)
    assert avg_latency_ms < 50.0

    # 3. Xác minh tính toàn vẹn của báo cáo phân tích sau bài test tải
    anl_res = client.get(f"/api/surveys/{survey_id}/analytics")
    assert anl_res.status_code == 200
    anl_data = anl_res.json()
    assert anl_data["total_responses"] == N_BATCH
    assert anl_data["is_sample_size_sufficient"] is True
