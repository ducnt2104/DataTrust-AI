import os
import tempfile
import pytest

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "datatrust_test_suite.db")
os.environ["DATABASE_PATH"] = TEST_DB_PATH

from app.database import init_db

@pytest.fixture(autouse=True)
def clean_test_database():
    """Tự động dọn dẹp và khởi tạo lại cơ sở dữ liệu trước mỗi bài kiểm thử."""
    for suffix in ["", "-wal", "-shm"]:
        p = TEST_DB_PATH + suffix
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
    init_db(TEST_DB_PATH)
    yield
    for suffix in ["", "-wal", "-shm"]:
        p = TEST_DB_PATH + suffix
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
