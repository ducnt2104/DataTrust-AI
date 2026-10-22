import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import DATABASE_PATH

def init_db(db_path: str = None):
    """Khởi tạo cơ sở dữ liệu và các bảng thực thể nếu chưa tồn tại"""
    target_path = db_path if db_path is not None else os.getenv("DATABASE_PATH", DATABASE_PATH)
    conn = sqlite3.connect(target_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS surveys (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            instructions TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            public_slug TEXT UNIQUE NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT,
            settings_json TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            survey_id TEXT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
            order_index INTEGER NOT NULL DEFAULT 0,
            question_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            is_required INTEGER NOT NULL DEFAULT 0,
            options_json TEXT DEFAULT '[]',
            logic_rules_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS responses (
            id TEXT PRIMARY KEY,
            survey_id TEXT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
            survey_version INTEGER NOT NULL DEFAULT 1,
            started_at TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            duration_seconds REAL NOT NULL DEFAULT 0.0,
            client_metadata_json TEXT DEFAULT '{}',
            risk_score REAL DEFAULT 0.0,
            risk_level TEXT DEFAULT 'low',
            analysis_status TEXT DEFAULT 'pending',
            review_status TEXT DEFAULT 'unverified',
            review_notes TEXT DEFAULT '',
            reviewed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS response_answers (
            id TEXT PRIMARY KEY,
            response_id TEXT NOT NULL REFERENCES responses(id) ON DELETE CASCADE,
            question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            answer_value TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quality_assessments (
            id TEXT PRIMARY KEY,
            response_id TEXT NOT NULL REFERENCES responses(id) ON DELETE CASCADE,
            score_dup REAL DEFAULT 0.0,
            score_pattern REAL DEFAULT 0.0,
            score_logic REAL DEFAULT 0.0,
            score_speed REAL DEFAULT 0.0,
            score_text REAL DEFAULT 0.0,
            composite_score REAL DEFAULT 0.0,
            flags_json TEXT NOT NULL DEFAULT '[]',
            closest_match_response_id TEXT,
            highest_similarity REAL DEFAULT 0.0,
            assessed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_surveys_slug ON surveys(public_slug);
        CREATE INDEX IF NOT EXISTS idx_questions_survey ON questions(survey_id, order_index);
        CREATE INDEX IF NOT EXISTS idx_responses_survey ON responses(survey_id, submitted_at);
        CREATE INDEX IF NOT EXISTS idx_answers_response ON response_answers(response_id);
        CREATE INDEX IF NOT EXISTS idx_quality_response ON quality_assessments(response_id);
        """)
    conn.close()

def get_connection(db_path: str = None) -> sqlite3.Connection:
    target_path = db_path if db_path is not None else os.getenv("DATABASE_PATH", DATABASE_PATH)
    conn = sqlite3.connect(target_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    target_path = db_path if db_path is not None else os.getenv("DATABASE_PATH", DATABASE_PATH)
    conn = get_connection(target_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
