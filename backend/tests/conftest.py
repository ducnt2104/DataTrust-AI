import os
import tempfile
import pytest

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "datatrust_test_suite.db")
os.environ["DATABASE_PATH"] = TEST_DB_PATH

from app.database import init_db, get_db
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_test_database():
    """Tự động dọn dẹp và khởi tạo lại cơ sở dữ liệu trước mỗi bài kiểm thử."""
    init_db(TEST_DB_PATH)
    try:
        with get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            for t in tables:
                conn.execute(f"DELETE FROM {t['name']}")
    except Exception:
        pass
    yield
