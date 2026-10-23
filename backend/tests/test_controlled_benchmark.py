import os
import pytest
from app.engine.benchmark_suite import ControlledBenchmarkSuite

def test_controlled_benchmark_dataset_execution():
    """
    Kiểm thử bộ dữ liệu thực nghiệm có kiểm soát (N = 150)
    Xác minh độ chính xác phát hiện theo các kịch bản của Hồ sơ Thuyết minh.
    """
    results = ControlledBenchmarkSuite.run_benchmark()

    # Kiểm tra quy mô tập mẫu
    assert results["total_samples"] == 150
    assert results["scenarios"]["valid_clean"]["n"] == 105
    assert results["scenarios"]["duplicate_near_duplicate"]["n"] == 20
    assert results["scenarios"]["straightlining_pattern"]["n"] == 15
    assert results["scenarios"]["logic_contradiction"]["n"] == 10

    # Kiểm tra chỉ số phân loại theo chuẩn quốc tế
    assert results["precision"] >= 95.0, f"Precision quá thấp: {results['precision']}%"
    assert results["recall"] >= 95.0, f"Recall quá thấp: {results['recall']}%"
    assert results["f1_score"] >= 95.0, f"F1-score quá thấp: {results['f1_score']}%"
    assert results["accuracy"] >= 95.0, f"Accuracy quá thấp: {results['accuracy']}%"
    
    # Kiểm tra thời gian xử lý: phải dưới 50ms/phiếu
    assert results["avg_latency_ms"] < 50.0, f"Độ trễ quá lớn: {results['avg_latency_ms']} ms"

    # Xuất báo cáo thực nghiệm ra thư mục docs/
    report_md = ControlledBenchmarkSuite.format_markdown_report(results)
    os.makedirs("docs", exist_ok=True)
    with open("docs/BENCHMARK_RESULTS.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    assert os.path.exists("docs/BENCHMARK_RESULTS.md")
