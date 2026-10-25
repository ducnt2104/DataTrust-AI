"""
DataTrust — High-Concurrency Stress Load Simulator & Latency Profiling Engine
Simulates real-world high-volume field submissions against FastAPI and SQLite WAL mode.
Measures P50, P90, P95, P99 latencies, validates zero lock errors, and verifies tamper-evident ledger integrity.
"""

import os
import sys
import time
import uuid
import json
import statistics
import concurrent.futures
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Đảm bảo import được module app khi chạy standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi.testclient import TestClient

from app.database import (
    get_db,
    maintenance_wal_checkpoint,
    verify_audit_chain,
    get_system_diagnostics
)

class StressLoadSimulator:
    """
    Công cụ giả lập tải cao và đo lường độ trễ (Stress Load & Latency Profiler).
    Đo lường khả năng chịu tải của SQLite WAL mode và FastAPI dưới áp lực đa luồng đồng thời.
    """

    def __init__(self, client: Optional[TestClient] = None):
        if client is None:
            from app.main import app
            self.client = TestClient(app)
        else:
            self.client = client

    def create_benchmark_survey(self, title: str = "Stress Test Benchmark Survey") -> Dict[str, Any]:
        """Tạo một khảo sát chuẩn đa dạng câu hỏi phục vụ stress test"""
        survey_id = f"stress_{uuid.uuid4().hex[:8]}"
        slug = f"stress-slug-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            conn.execute("""
                INSERT INTO surveys (id, title, description, instructions, status, public_slug, version, created_at, updated_at)
                VALUES (?, ?, 'Benchmark Survey for Concurrency Stress Testing', 'Trả lời đầy đủ', 'published', ?, 1, ?, ?)
            """, (survey_id, title, slug, now_iso, now_iso))

            q1_id = f"q1_{uuid.uuid4().hex[:6]}"
            q2_id = f"q2_{uuid.uuid4().hex[:6]}"
            q3_id = f"q3_{uuid.uuid4().hex[:6]}"

            conn.execute("""
                INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
                VALUES (?, ?, 0, 'single_choice', 'Đánh giá chất lượng dịch vụ', 1, ?, ?)
            """, (q1_id, survey_id, json.dumps([
                {"id": "opt1", "label": "Rất hài lòng"},
                {"id": "opt2", "label": "Hài lòng"},
                {"id": "opt3", "label": "Bình thường"},
                {"id": "opt4", "label": "Không hài lòng"}
            ], ensure_ascii=False), now_iso))

            conn.execute("""
                INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
                VALUES (?, ?, 1, 'likert', 'Mức độ tin cậy vào nền tảng', 1, ?, ?)
            """, (q2_id, survey_id, json.dumps([
                {"id": "l1", "label": "1"}, {"id": "l2", "label": "2"},
                {"id": "l3", "label": "3"}, {"id": "l4", "label": "4"},
                {"id": "l5", "label": "5"}
            ]), now_iso))

            conn.execute("""
                INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
                VALUES (?, ?, 2, 'short_text', 'Đóng góp ý kiến', 0, '[]', ?)
            """, (q3_id, survey_id, now_iso))

        return {
            "survey_id": survey_id,
            "slug": slug,
            "questions": [q1_id, q2_id, q3_id]
        }

    def generate_submission_payload(self, questions: List[str], index: int) -> Dict[str, Any]:
        """Tạo payload phản hồi hợp lệ theo đúng schema ResponseSubmit và BatchResponseItem"""
        opt_idx = (index % 4) + 1
        likert_val = str((index % 5) + 1)
        comments = [
            "Hệ thống vận hành mượt mà, phản hồi nhanh chóng",
            "Giao diện trực quan và dễ sử dụng",
            "Dữ liệu kiểm tra rất minh bạch và an tâm",
            "Cần hỗ trợ thêm xuất báo cáo biểu đồ định dạng vector"
        ]
        
        # GPS quanh Hà Nội / TP.HCM
        base_lat = 21.0285 + (index % 10) * 0.002
        base_lng = 105.8542 + (index % 10) * 0.002

        dur_secs = 45.0 + (index % 60)
        now_dt = datetime.now(timezone.utc)
        start_iso = now_dt.isoformat()
        sub_iso = now_dt.isoformat()
        client_uuid = f"stress-uuid-{uuid.uuid4()}"

        return {
            "client_uuid": client_uuid,
            "started_at": start_iso,
            "submitted_at": sub_iso,
            "source": "online_form",
            "enumerator_id": f"enum_{index % 5}",
            "client_metadata": {
                "client_uuid": client_uuid,
                "device_id": f"dev-stress-{index % 20}",
                "duration_seconds": dur_secs,
                "gps_lat": base_lat,
                "gps_lng": base_lng,
                "user_agent": "Mozilla/5.0 DataTrust-Stress-Profiler/1.0"
            },
            "answers": {
                questions[0]: f"opt{opt_idx}",
                questions[1]: likert_val,
                questions[2]: comments[index % len(comments)]
            }
        }

    def run_stress_test(
        self,
        slug: str,
        questions: List[str],
        total_requests: int = 100,
        concurrency: int = 10
    ) -> Dict[str, Any]:
        """
        Thực hiện bắn đồng thời total_requests vào endpoint submit bằng ThreadPoolExecutor.
        Đo lường thời gian đáp ứng từng request và thống kê phân vị P50, P90, P95, P99.
        """
        latencies_ms: List[float] = []
        status_codes: List[int] = []
        errors: List[str] = []

        def worker(req_idx: int) -> Dict[str, Any]:
            payload = self.generate_submission_payload(questions, req_idx)
            t_start = time.perf_counter()
            try:
                resp = self.client.post(f"/api/public/surveys/{slug}/submit", json=payload)
                t_dur_ms = (time.perf_counter() - t_start) * 1000.0
                is_ok = resp.status_code in (200, 201)
                return {
                    "status_code": resp.status_code,
                    "latency_ms": t_dur_ms,
                    "error": None if is_ok else resp.text
                }
            except Exception as e:
                t_dur_ms = (time.perf_counter() - t_start) * 1000.0
                return {
                    "status_code": 500,
                    "latency_ms": t_dur_ms,
                    "error": str(e)
                }

        wall_start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(worker, i) for i in range(total_requests)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                status_codes.append(res["status_code"])
                latencies_ms.append(res["latency_ms"])
                if res["error"]:
                    errors.append(res["error"])

        wall_duration = time.perf_counter() - wall_start
        throughput_rps = total_requests / wall_duration if wall_duration > 0 else 0.0

        sorted_latencies = sorted(latencies_ms)
        n = len(sorted_latencies)

        def get_percentile(p: float) -> float:
            if not sorted_latencies:
                return 0.0
            k = (n - 1) * (p / 100.0)
            f = int(k)
            c = min(f + 1, n - 1)
            d0 = sorted_latencies[f] * (c - k)
            d1 = sorted_latencies[c] * (k - f)
            return round(d0 + d1, 2)

        p50 = get_percentile(50)
        p90 = get_percentile(90)
        p95 = get_percentile(95)
        p99 = get_percentile(99)
        avg_lat = round(statistics.mean(latencies_ms), 2) if latencies_ms else 0.0
        min_lat = round(min(latencies_ms), 2) if latencies_ms else 0.0
        max_lat = round(max(latencies_ms), 2) if latencies_ms else 0.0

        success_count = sum(1 for sc in status_codes if sc in (200, 201))
        failure_count = len(status_codes) - success_count

        return {
            "total_requests": total_requests,
            "concurrency": concurrency,
            "wall_duration_seconds": round(wall_duration, 3),
            "throughput_rps": round(throughput_rps, 1),
            "success_count": success_count,
            "failure_count": failure_count,
            "error_rate_pct": round((failure_count / total_requests) * 100, 2) if total_requests > 0 else 0.0,
            "latency_profiling_ms": {
                "min": min_lat,
                "p50": p50,
                "p90": p90,
                "p95": p95,
                "p99": p99,
                "max": max_lat,
                "mean": avg_lat
            },
            "errors_sample": errors[:5]
        }

    def run_batch_stress_test(
        self,
        slug: str,
        questions: List[str],
        num_batches: int = 10,
        batch_size: int = 15,
        concurrency: int = 5
    ) -> Dict[str, Any]:
        """
        Thực hiện bắn đồng thời các mẻ đồng bộ ngoại tuyến (batch-sync) vào hệ thống.
        Đo lường tính nguyên tử của SQLite transaction và khả năng chống trùng lặp.
        """
        latencies_ms: List[float] = []
        synced_counts: List[int] = []
        duplicates_counts: List[int] = []
        errors: List[str] = []

        def batch_worker(batch_idx: int) -> Dict[str, Any]:
            batch_payload = {
                "responses": [
                    self.generate_submission_payload(questions, batch_idx * 100 + i)
                    for i in range(batch_size)
                ]
            }
            t_start = time.perf_counter()
            try:
                resp = self.client.post(f"/api/public/surveys/{slug}/batch-sync", json=batch_payload)
                t_dur_ms = (time.perf_counter() - t_start) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status_code": 200,
                        "latency_ms": t_dur_ms,
                        "synced": data.get("synced_count", 0),
                        "duplicates": data.get("duplicates_skipped", 0),
                        "error": None
                    }
                else:
                    return {
                        "status_code": resp.status_code,
                        "latency_ms": t_dur_ms,
                        "synced": 0,
                        "duplicates": 0,
                        "error": resp.text
                    }
            except Exception as e:
                t_dur_ms = (time.perf_counter() - t_start) * 1000.0
                return {
                    "status_code": 500,
                    "latency_ms": t_dur_ms,
                    "synced": 0,
                    "duplicates": 0,
                    "error": str(e)
                }

        wall_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(batch_worker, b) for b in range(num_batches)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                latencies_ms.append(res["latency_ms"])
                synced_counts.append(res["synced"])
                duplicates_counts.append(res["duplicates"])
                if res["error"]:
                    errors.append(res["error"])

        wall_duration = time.perf_counter() - wall_start
        total_items = num_batches * batch_size

        return {
            "num_batches": num_batches,
            "batch_size": batch_size,
            "total_items": total_items,
            "concurrency": concurrency,
            "wall_duration_seconds": round(wall_duration, 3),
            "effective_throughput_items_per_sec": round(total_items / wall_duration, 1) if wall_duration > 0 else 0.0,
            "total_synced": sum(synced_counts),
            "total_duplicates_skipped": sum(duplicates_counts),
            "error_count": len(errors),
            "mean_batch_latency_ms": round(statistics.mean(latencies_ms), 2) if latencies_ms else 0.0,
            "p95_batch_latency_ms": round(sorted(latencies_ms)[int(len(latencies_ms) * 0.95)] if latencies_ms else 0.0, 2),
            "errors": errors[:5]
        }

    def run_full_benchmark(self, total_requests: int = 30, concurrency: int = 6) -> Dict[str, Any]:
        """Khởi tạo khảo sát chuẩn và thực hiện đo lường tải đồng thời toàn diện"""
        bench = self.create_benchmark_survey("Live Concurrency Latency Benchmark")
        test_res = self.run_stress_test(
            bench["slug"],
            bench["questions"],
            total_requests=total_requests,
            concurrency=concurrency
        )
        with get_db() as conn:
            chain_audit = verify_audit_chain(conn)
        cp = maintenance_wal_checkpoint()
        lat_prof = test_res.get("latency_profiling_ms", {})
        return {
            "status": "PASSED" if test_res["failure_count"] == 0 and chain_audit["is_valid"] else "FAILED",
            "total_requests": test_res["total_requests"],
            "successful_requests": test_res["success_count"],
            "failed_requests": test_res["failure_count"],
            "concurrency_workers": test_res["concurrency"],
            "total_time_seconds": test_res["wall_duration_seconds"],
            "throughput_rps": test_res["throughput_rps"],
            "latency_mean_ms": lat_prof.get("mean", 0.0),
            "latency_median_p50_ms": lat_prof.get("p50", 0.0),
            "latency_p90_ms": lat_prof.get("p90", 0.0),
            "latency_p95_ms": lat_prof.get("p95", 0.0),
            "latency_p99_ms": lat_prof.get("p99", 0.0),
            "latency_min_ms": lat_prof.get("min", 0.0),
            "latency_max_ms": lat_prof.get("max", 0.0),
            "database_lock_errors": test_res["failure_count"],
            "audit_chain_valid_post_stress": chain_audit.get("is_valid", True),
            "audit_chain_head_hash": chain_audit.get("head_hash"),
            "wal_size_bytes_after": cp.get("wal_size_bytes", 0)
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  DATATRUST — CONCURRENCY STRESS & LATENCY PROFILER")
    print("=" * 60)
    sim = StressLoadSimulator()
    print("1. Khởi tạo khảo sát chuẩn...")
    bench = sim.create_benchmark_survey("Stress Load CLI Test")
    print(f"   -> Survey ID: {bench['survey_id']}, Slug: {bench['slug']}")
    
    print("\n2. Thực thi thử tải: 150 requests đồng thời, 10 workers...")
    results = sim.run_stress_test(bench["slug"], bench["questions"], total_requests=150, concurrency=10)
    print(json.dumps(results, indent=2, ensure_ascii=False))

    print("\n3. Kiểm tra tính toàn vẹn CSDL và Chuỗi băm kiểm toán...")
    with get_db() as conn:
        chain_audit = verify_audit_chain(conn)
        print(f"   -> Tamper-evident Ledger: {'HỢP LỆ (100% Kháng can thiệp)' if chain_audit['is_valid'] else 'LỖI'}")
        print(f"   -> Tổng số mắt xích đã băm: {chain_audit['total_records']}")

    print("\n4. Thực thi dọn dẹp trang WAL Checkpoint...")
    cp = maintenance_wal_checkpoint()
    print(f"   -> Trạng thái WAL: {cp['status']}, DB Size: {round(cp['db_size_bytes'] / 1024, 1)} KB, WAL Size: {cp['wal_size_bytes']} bytes")
    print("=" * 60)
