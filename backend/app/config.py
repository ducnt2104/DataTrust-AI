import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "datatrust.db"))
PORT = int(os.getenv("PORT", "8000"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5173")

# Google Gemini Configuration
# API key must NEVER be embedded in source code, logged, or exposed in URLs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-2.0-flash")
AI_REQUEST_TIMEOUT_SECONDS = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "45.0"))

def is_gemini_configured() -> bool:
    """Safe validation of Gemini API key presence without logging credential content."""
    return bool(GEMINI_API_KEY and len(GEMINI_API_KEY) >= 15 and not GEMINI_API_KEY.startswith("your_gemini"))
