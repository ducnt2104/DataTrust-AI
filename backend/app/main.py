import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, maintenance_wal_checkpoint, backup_database, vacuum_database, get_system_diagnostics
from app.schemas import StressTestReportOut
from app.routes import surveys, public, responses, analytics, export_import, ai, paper, enumerators, audit_report, public_verification

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo DB khi ứng dụng khởi động
    init_db()
    yield

app = FastAPI(
    title="DataTrust — Intelligent Survey & Data Quality Assurance API",
    description="Nền tảng tạo khảo sát trực tuyến, thu thập phản hồi thật và phân tích chất lượng dữ liệu bằng AI & Thuật toán thống kê",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware bảo mật HTTP và giám sát độ trễ phản hồi
@app.middleware("http")
async def add_security_headers_and_timing(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time-Ms"]
)

# Đăng ký các router nghiệp vụ
app.include_router(surveys.router)
app.include_router(public.router)
app.include_router(responses.router)
app.include_router(analytics.router)
app.include_router(export_import.router)
app.include_router(ai.router)
app.include_router(paper.router)
app.include_router(enumerators.router)
app.include_router(audit_report.router)
app.include_router(public_verification.router)

@app.get("/", tags=["System"])
@app.head("/", tags=["System"])
def root():
    return {
        "service": "DataTrust API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/api/health", tags=["System"])
@app.get("/api/status", tags=["System"])
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "DataTrust API",
        "version": "1.0.0",
        "capabilities": [
            "Survey Builder",
            "Public Survey Link",
            "Quality Assurance Engine",
            "Human Review Center",
            "Real Analytics Dashboard",
            "Multi-scope Export",
            "Paper Survey & OMR Scanning",
            "Enumerator & Field Group Analytics"
        ]
    }

@app.post("/api/system/maintenance/wal-checkpoint", tags=["System"])
@app.get("/api/system/maintenance/wal-checkpoint", tags=["System"])
def trigger_wal_checkpoint():
    """Kích hoạt dồn trang SQLite WAL và thu gọn tệp WAL về 0 bytes"""
    return maintenance_wal_checkpoint()

@app.post("/api/system/maintenance/backup", tags=["System"])
def trigger_database_backup():
    """Tạo bản sao lưu nguyên tử (Atomic Online Backup) của cơ sở dữ liệu"""
    return backup_database()

@app.post("/api/system/maintenance/vacuum", tags=["System"])
def trigger_database_vacuum():
    """Thực hiện VACUUM chống phân mảnh và giải phóng dung lượng đĩa của cơ sở dữ liệu"""
    return vacuum_database()

@app.get("/api/system/diagnostics", tags=["System"])
def system_diagnostics():
    """Kiểm tra chẩn đoán toàn diện sức khỏe hệ thống CSDL, B-Tree và chuỗi băm bất biến"""
    return get_system_diagnostics()

@app.post("/api/system/maintenance/stress-test", response_model=StressTestReportOut, tags=["System"])
def trigger_stress_test(
    total_requests: int = Query(30, ge=10, le=100, description="Tổng số phản hồi giả lập đa luồng"),
    concurrency: int = Query(6, ge=2, le=20, description="Số luồng gửi đồng thời (Worker threads)")
):
    """
    Thực thi Giả lập Tải cao & Đo lường Độ trễ Concurrency (Stress Load & Latency Profiling):
    Kiểm chứng khả năng chịu tải đa luồng của SQLite WAL mode và tính toàn vẹn của chuỗi băm bất biến.
    """
    from app.engine.stress_simulator import StressLoadSimulator
    simulator = StressLoadSimulator()
    report = simulator.run_full_benchmark(total_requests=total_requests, concurrency=concurrency)
    return report



