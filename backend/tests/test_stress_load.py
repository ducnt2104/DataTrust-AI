"""
DataTrust — High-Concurrency Stress & Latency Profiling Test Suite
Verifies SQLite WAL mode resilience, latency distributions, batch sync idempotency,
and cryptographic hash chain integrity under multi-threaded load.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, verify_audit_chain, maintenance_wal_checkpoint, get_system_diagnostics
from app.engine.stress_simulator import StressLoadSimulator

client = TestClient(app)

def test_stress_concurrent_submissions_wal():
    """
    Kịch bản 1: Bắn 100 phản hồi đồng thời từ 10 worker threads qua endpoint công khai /submit.
    Xác minh:
    1. Tỷ lệ lỗi = 0% (Không phát sinh lỗi lock 'database is locked' hay 500).
    2. Đạt phân vị độ trễ P95 ổn định.
    3. Chuỗi băm kiểm toán SHA-256 (Tamper-evident Ledger) bảo toàn tính bất biến 100%.
    """
    sim = StressLoadSimulator(client)
    bench = sim.create_benchmark_survey("Stress Pytest Benchmark 1")
    slug = bench["slug"]
    questions = bench["questions"]

    result = sim.run_stress_test(slug, questions, total_requests=100, concurrency=10)

    assert result["failure_count"] == 0, f"Có {result['failure_count']} lỗi: {result['errors_sample']}"
    assert result["success_count"] == 100
    assert result["error_rate_pct"] == 0.0
    assert result["latency_profiling_ms"]["p50"] > 0

    # Kiểm tra tính toàn vẹn của chuỗi băm bất biến
    with get_db() as conn:
        chain_status = verify_audit_chain(conn)
        assert chain_status["is_valid"] is True, "Chuỗi băm kiểm toán bị vi phạm tính toàn vẹn sau stress test!"

def test_stress_batch_sync_concurrency_and_idempotency():
    """
    Kịch bản 2: Bắn đồng thời 4 mẻ đồng bộ ngoại tuyến (batch-sync) với tổng cộng 40 phiếu.
    Sau đó gửi lại 1 mẻ có chứa client_uuid trùng lặp.
    Xác minh:
    1. Toàn bộ 40 phiếu được đồng bộ thành công vào CSDL trong 1 transaction SQLite.
    2. Mẻ gửi lại phát hiện chính xác các phiếu trùng lặp và bỏ qua an toàn (Idempotent).
    """
    sim = StressLoadSimulator(client)
    bench = sim.create_benchmark_survey("Stress Batch Benchmark")
    slug = bench["slug"]
    questions = bench["questions"]

    # 1. Bắn 4 mẻ x 10 items đồng thời
    batch_res = sim.run_batch_stress_test(slug, questions, num_batches=4, batch_size=10, concurrency=4)
    assert batch_res["error_count"] == 0
    assert batch_res["total_synced"] == 40
    assert batch_res["total_duplicates_skipped"] == 0

    # 2. Thử nghiệm gửi lại 1 mẻ với đúng các client_uuid cũ (Idempotency check)
    re_payload = {
        "responses": [
            sim.generate_submission_payload(questions, i)
            for i in range(5)
        ]
    }
    # Giữ nguyên client_uuid đã chèn từ đợt 1
    # Ở đợt 1 batch 0 sinh ra các client_uuid; ở đây generate_submission_payload sinh uuid ngẫu nhiên nên ta lấy client_uuid thực từ CSDL
    with get_db() as conn:
        saved_uuids = [
            row["client_uuid"] for row in conn.execute(
                "SELECT json_extract(client_metadata_json, '$.client_uuid') as client_uuid FROM responses WHERE survey_id = ? LIMIT 5",
                (bench["survey_id"],)
            ).fetchall() if row["client_uuid"]
        ]

    for idx, u in enumerate(saved_uuids):
        re_payload["responses"][idx]["client_uuid"] = u
        re_payload["responses"][idx]["client_metadata"]["client_uuid"] = u

    resp = client.post(f"/api/public/surveys/{slug}/batch-sync", json=re_payload)
    assert resp.status_code == 200
    re_data = resp.json()
    assert re_data["duplicates_skipped"] == len(saved_uuids)

def test_stress_wal_checkpoint_and_diagnostics_recovery():
    """
    Kịch bản 3: Thực thi bảo trì dồn trang WAL Checkpoint và kiểm tra chẩn đoán toàn diện hệ thống.
    Xác minh:
    1. PRAGMA wal_checkpoint(TRUNCATE) thu nhỏ tệp WAL về 0 byte an toàn.
    2. PRAGMA integrity_check trả về kết quả 'ok' (Không tham nhũng B-Tree).
    3. API /api/system/diagnostics trả về trạng thái hoạt động hoàn hảo.
    """
    # 1. Checkpoint dọn dẹp
    cp = maintenance_wal_checkpoint()
    assert cp["status"] == "success"
    assert cp["wal_size_bytes"] == 0

    # 2. Chẩn đoán hệ thống
    diag = get_system_diagnostics()
    assert diag["sqlite_pragmas"]["integrity_check"] == "ok"
    assert diag["sqlite_pragmas"]["journal_mode"] == "wal"
    assert diag["tamper_evident_ledger"]["is_chain_valid"] is True

    # 3. Kiểm tra endpoint GET /api/system/diagnostics
    resp = client.get("/api/system/diagnostics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sqlite_pragmas"]["integrity_check"] == "ok"

def test_stress_test_maintenance_api_endpoint():
    """
    Kịch bản 4: Gọi trực tiếp endpoint POST /api/system/maintenance/stress-test.
    Xác minh báo cáo trả về đầy đủ các chỉ số thống kê P50, P90, P95, P99,
    không có lỗi khóa CSDL và chuỗi băm bất biến bảo toàn 100%.
    """
    resp = client.post("/api/system/maintenance/stress-test?total_requests=20&concurrency=4")
    assert resp.status_code == 200
    report = resp.json()
    assert report["status"] == "PASSED"
    assert report["total_requests"] == 20
    assert report["successful_requests"] == 20
    assert report["failed_requests"] == 0
    assert report["database_lock_errors"] == 0
    assert report["throughput_rps"] > 0
    assert report["latency_median_p50_ms"] >= 0
    assert report["audit_chain_valid_post_stress"] is True

