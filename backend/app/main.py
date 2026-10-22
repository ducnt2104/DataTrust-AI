from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import surveys, public, responses, analytics, export_import, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo DB khi ứng dụng khởi động
    init_db()
    yield

app = FastAPI(
    title="DataTrust AI — Intelligent Survey & Data Quality Assurance API",
    description="Nền tảng tạo khảo sát trực tuyến, thu thập phản hồi thật và phân tích chất lượng dữ liệu bằng AI & Thuật toán thống kê",
    version="1.0.0",
    lifespan=lifespan
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router nghiệp vụ
app.include_router(surveys.router)
app.include_router(public.router)
app.include_router(responses.router)
app.include_router(analytics.router)
app.include_router(export_import.router)
app.include_router(ai.router)

@app.get("/", tags=["System"])
@app.head("/", tags=["System"])
def root():
    return {
        "service": "DataTrust AI API",
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
        "service": "DataTrust AI API",
        "version": "1.0.0",
        "capabilities": [
            "Survey Builder",
            "Public Survey Link",
            "Quality Assurance Engine",
            "Human Review Center",
            "Real Analytics Dashboard",
            "Multi-scope Export"
        ]
    }
