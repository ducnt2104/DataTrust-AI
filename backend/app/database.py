import os
import sqlite3
import hashlib
import json
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Generator, Dict, Any, Optional
from app.config import DATABASE_PATH

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def compute_audit_hash(prev_hash: str, log_id: str, entity_type: str, entity_id: str, action: str, details_json: str, created_at: str) -> str:
    """Tính toán chữ ký băm SHA-256 bảo vệ tính toàn vẹn của một mắt xích kiểm toán"""
    raw_payload = f"{prev_hash}|{log_id}|{entity_type}|{entity_id}|{action}|{details_json}|{created_at}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

def record_audit_log(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    action: str,
    details: Any = None,
    created_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ghi một sự kiện kiểm toán mới vào chuỗi băm bất biến (Tamper-Evident SHA-256 Audit Hash Chain).
    Mỗi mắt xích liên kết chặt chẽ với mắt xích trước đó qua prev_hash và được băm lại toàn bộ trường dữ liệu.
    """
    log_id = str(uuid.uuid4())
    ts = created_at or datetime.now(timezone.utc).isoformat()
    if isinstance(details, (dict, list)):
        details_json = json.dumps(details, ensure_ascii=False, sort_keys=True)
    elif isinstance(details, str):
        details_json = details
    else:
        details_json = "{}"

    # Lấy hash của mắt xích gần nhất
    last_row = conn.execute(
        "SELECT entry_hash FROM audit_logs WHERE entry_hash IS NOT NULL AND entry_hash != '' ORDER BY rowid DESC LIMIT 1"
    ).fetchone()

    prev_hash = last_row[0] if (last_row and last_row[0]) else GENESIS_HASH
    entry_hash = compute_audit_hash(prev_hash, log_id, entity_type, entity_id, action, details_json, ts)

    conn.execute("""
        INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at, prev_hash, entry_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (log_id, entity_type, entity_id, action, details_json, ts, prev_hash, entry_hash))

    return {
        "id": log_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "details_json": details_json,
        "created_at": ts,
        "prev_hash": prev_hash,
        "entry_hash": entry_hash
    }

def verify_audit_chain(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Xác minh toán học tính toàn vẹn của toàn bộ chuỗi băm kiểm toán audit_logs.
    Phát hiện ngay lập tức bất kỳ sự giả mạo, sửa đổi chi tiết, xoá mắt xích hoặc chèn bản ghi trái phép nào.
    """
    rows = conn.execute(
        "SELECT rowid, id, entity_type, entity_id, action, details_json, created_at, prev_hash, entry_hash FROM audit_logs ORDER BY rowid ASC"
    ).fetchall()

    if not rows:
        return {
            "is_valid": True,
            "total_records": 0,
            "head_hash": GENESIS_HASH,
            "genesis_hash": None,
            "message": "Chuỗi kiểm toán rỗng (hợp lệ)."
        }

    expected_prev = GENESIS_HASH
    for idx, r in enumerate(rows):
        r_id = r[1]
        r_ent_type = r[2]
        r_ent_id = r[3]
        r_action = r[4]
        r_details = r[5] or "{}"
        r_ts = r[6]
        r_prev = r[7]
        r_entry = r[8]

        # 1. Kiểm tra tính liên tục của prev_hash
        if r_prev != expected_prev:
            return {
                "is_valid": False,
                "tampered_at_index": idx,
                "tampered_record_id": r_id,
                "error_type": "PREV_HASH_CHAIN_BROKEN",
                "details": f"Mắt xích #{idx} có prev_hash không khớp với entry_hash của mắt xích trước (Kỳ vọng: {expected_prev}, Thực tế: {r_prev}).",
                "total_records": len(rows)
            }

        # 2. Kiểm tra tính toàn vẹn nội dung của chính mắt xích
        calculated_entry_hash = compute_audit_hash(r_prev, r_id, r_ent_type, r_ent_id, r_action, r_details, r_ts)
        if r_entry != calculated_entry_hash:
            return {
                "is_valid": False,
                "tampered_at_index": idx,
                "tampered_record_id": r_id,
                "error_type": "SIGNATURE_PAYLOAD_TAMPERED",
                "details": f"Nội dung của mắt xích #{idx} ({r_id}) đã bị can thiệp trái phép sau khi ghi nhật ký.",
                "total_records": len(rows)
            }

        expected_prev = r_entry

    return {
        "is_valid": True,
        "total_records": len(rows),
        "genesis_hash": rows[0][8] if rows else None,
        "head_hash": rows[-1][8] if rows else GENESIS_HASH,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "message": f"Toàn bộ {len(rows)} mắt xích kiểm toán đều hợp lệ và bảo toàn tính toàn vẹn SHA-256."
    }

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
            reviewed_at TEXT,
            source TEXT DEFAULT 'online_form',
            enumerator_id TEXT DEFAULT '',
            paper_form_id TEXT DEFAULT '',
            scan_image_url TEXT DEFAULT '',
            omr_confidence REAL DEFAULT 1.0,
            experimental_arm TEXT DEFAULT ''
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
            score_enum REAL DEFAULT 0.0,
            composite_score REAL DEFAULT 0.0,
            flags_json TEXT NOT NULL DEFAULT '[]',
            closest_match_response_id TEXT,
            highest_similarity REAL DEFAULT 0.0,
            assessed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS paper_templates (
            id TEXT PRIMARY KEY,
            survey_id TEXT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
            template_version INTEGER NOT NULL DEFAULT 1,
            layout_config_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            prev_hash TEXT DEFAULT '0000000000000000000000000000000000000000000000000000000000000000',
            entry_hash TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS ai_generation_sessions (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            audience TEXT DEFAULT '',
            objectives TEXT DEFAULT '',
            target_duration INTEGER DEFAULT 5,
            preferred_types_json TEXT DEFAULT '[]',
            extracted_spec_json TEXT DEFAULT '{}',
            model_name TEXT NOT NULL,
            provider_type TEXT NOT NULL,
            status TEXT NOT NULL,
            duration_ms REAL DEFAULT 0.0,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            generated_survey_json TEXT DEFAULT '{}',
            validation_report_json TEXT DEFAULT '{}',
            error_message TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ai_audit_logs (
            id TEXT PRIMARY KEY,
            survey_id TEXT DEFAULT '',
            total_questions INTEGER DEFAULT 0,
            issues_found INTEGER DEFAULT 0,
            issues_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS survey_versions (
            id TEXT PRIMARY KEY,
            survey_id TEXT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            questions_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_surveys_slug ON surveys(public_slug);
        CREATE INDEX IF NOT EXISTS idx_questions_survey ON questions(survey_id, order_index);
        CREATE INDEX IF NOT EXISTS idx_survey_versions_survey_ver ON survey_versions(survey_id, version);
        CREATE INDEX IF NOT EXISTS idx_responses_survey ON responses(survey_id, submitted_at);
        CREATE INDEX IF NOT EXISTS idx_responses_review_risk ON responses(survey_id, review_status, risk_level);
        CREATE INDEX IF NOT EXISTS idx_answers_response ON response_answers(response_id);
        CREATE INDEX IF NOT EXISTS idx_answers_question_resp ON response_answers(question_id, response_id);
        CREATE INDEX IF NOT EXISTS idx_quality_response ON quality_assessments(response_id);
        CREATE INDEX IF NOT EXISTS idx_paper_templates_survey ON paper_templates(survey_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_ai_gen_created ON ai_generation_sessions(created_at);
        CREATE INDEX IF NOT EXISTS idx_ai_gen_status ON ai_generation_sessions(status);
        CREATE INDEX IF NOT EXISTS idx_ai_audit_created ON ai_audit_logs(created_at);
        """)

        # Migration logic for existing tables
        resp_cols = [c[1] for c in conn.execute("PRAGMA table_info(responses);").fetchall()]
        if "source" not in resp_cols:
            conn.execute("ALTER TABLE responses ADD COLUMN source TEXT DEFAULT 'online_form';")
        if "enumerator_id" not in resp_cols:
            conn.execute("ALTER TABLE responses ADD COLUMN enumerator_id TEXT DEFAULT '';")
        if "paper_form_id" not in resp_cols:
            conn.execute("ALTER TABLE responses ADD COLUMN paper_form_id TEXT DEFAULT '';")
        if "scan_image_url" not in resp_cols:
            conn.execute("ALTER TABLE responses ADD COLUMN scan_image_url TEXT DEFAULT '';")
        if "omr_confidence" not in resp_cols:
            conn.execute("ALTER TABLE responses ADD COLUMN omr_confidence REAL DEFAULT 1.0;")
        if "experimental_arm" not in resp_cols:
            conn.execute("ALTER TABLE responses ADD COLUMN experimental_arm TEXT DEFAULT '';")

        # Create indexes that depend on migrated columns
        conn.execute("CREATE INDEX IF NOT EXISTS idx_responses_enum_lookup ON responses(survey_id, source, enumerator_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_responses_exp_arm ON responses(survey_id, experimental_arm);")

        qa_cols = [c[1] for c in conn.execute("PRAGMA table_info(quality_assessments);").fetchall()]
        if "score_enum" not in qa_cols:
            conn.execute("ALTER TABLE quality_assessments ADD COLUMN score_enum REAL DEFAULT 0.0;")

        audit_cols = [c[1] for c in conn.execute("PRAGMA table_info(audit_logs);").fetchall()]
        if "prev_hash" not in audit_cols:
            conn.execute(f"ALTER TABLE audit_logs ADD COLUMN prev_hash TEXT DEFAULT '{GENESIS_HASH}';")
        if "entry_hash" not in audit_cols:
            conn.execute("ALTER TABLE audit_logs ADD COLUMN entry_hash TEXT DEFAULT '';")

        # Backfill existing unhashed audit log entries to establish unbroken hash chain
        unhashed = conn.execute("SELECT COUNT(*) FROM audit_logs WHERE entry_hash IS NULL OR entry_hash = ''").fetchone()[0]
        if unhashed > 0:
            rows = conn.execute("SELECT rowid, id, entity_type, entity_id, action, details_json, created_at FROM audit_logs ORDER BY rowid ASC").fetchall()
            prev = GENESIS_HASH
            for r in rows:
                h = compute_audit_hash(prev, r[1], r[2], r[3], r[4], r[5] or "{}", r[6])
                conn.execute("UPDATE audit_logs SET prev_hash = ?, entry_hash = ? WHERE rowid = ?", (prev, h, r[0]))
                prev = h
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

def maintenance_wal_checkpoint(db_path: str = None) -> Dict[str, Any]:
    """
    Thực hiện bảo trì và dọn dẹp cơ sở dữ liệu định kỳ:
    1. Chạy PRAGMA wal_checkpoint(TRUNCATE) để dồn trang từ WAL vào DB chính và thu nhỏ tệp WAL về 0.
    2. Chạy PRAGMA optimize để tối ưu hóa query planner của SQLite.
    3. Thống kê kích thước tệp CSDL chính (.db) và tệp WAL (.db-wal).
    """
    target_path = db_path if db_path is not None else os.getenv("DATABASE_PATH", DATABASE_PATH)
    conn = sqlite3.connect(target_path, timeout=30.0)
    try:
        checkpoint_res = conn.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
        busy = checkpoint_res[0] if checkpoint_res else 0
        log_pages = checkpoint_res[1] if checkpoint_res else 0
        checkpointed_pages = checkpoint_res[2] if checkpoint_res else 0
        
        conn.execute("PRAGMA optimize;")
        
        db_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0
        wal_path = f"{target_path}-wal"
        wal_size = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
        shm_path = f"{target_path}-shm"
        shm_size = os.path.getsize(shm_path) if os.path.exists(shm_path) else 0
        
        return {
            "status": "success",
            "busy": bool(busy),
            "wal_log_pages": log_pages,
            "checkpointed_pages": checkpointed_pages,
            "db_size_bytes": db_size,
            "wal_size_bytes": wal_size,
            "shm_size_bytes": shm_size,
            "checkpoint_mode": "TRUNCATE",
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
    finally:
        conn.close()

def backup_database(destination_path: str = None, db_path: str = None) -> Dict[str, Any]:
    """
    Tạo bản sao lưu nguyên tử (Atomic Online Backup) của cơ sở dữ liệu SQLite:
    Sử dụng SQLite Online Backup API an toàn, không khóa ghi đồng thời và không làm hỏng tệp WAL.
    """
    target_path = db_path if db_path is not None else os.getenv("DATABASE_PATH", DATABASE_PATH)
    if not destination_path:
        base_dir = os.path.dirname(os.path.abspath(target_path))
        backup_dir = os.path.join(base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        destination_path = os.path.join(backup_dir, f"datatrust_backup_{timestamp}.db")
    
    src_conn = sqlite3.connect(target_path, timeout=30.0)
    dest_conn = sqlite3.connect(destination_path)
    try:
        src_conn.backup(dest_conn)
        backup_size = os.path.getsize(destination_path)
        return {
            "status": "success",
            "source_db": target_path,
            "backup_file": destination_path,
            "backup_size_bytes": backup_size,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    finally:
        dest_conn.close()
        src_conn.close()

def vacuum_database(db_path: str = None) -> Dict[str, Any]:
    """
    Thực hiện VACUUM giải phóng các trang trống (free pages) và chống phân mảnh tệp CSDL SQLite:
    - Thu hồi dung lượng đĩa bị chiếm dụng sau khi xóa hoặc chỉnh sửa nhiều bản ghi.
    - So sánh dung lượng trước và sau khi dọn dẹp (reclaimed bytes).
    """
    target_path = db_path if db_path is not None else os.getenv("DATABASE_PATH", DATABASE_PATH)
    initial_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0
    
    conn = sqlite3.connect(target_path, timeout=60.0)
    try:
        # Trước khi vacuum, thu gọn WAL
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.execute("VACUUM;")
        conn.execute("PRAGMA optimize;")
        
        final_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0
        freed_bytes = max(0, initial_size - final_size)
        
        return {
            "status": "success",
            "db_path": target_path,
            "initial_size_bytes": initial_size,
            "final_size_bytes": final_size,
            "freed_bytes": freed_bytes,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
    finally:
        conn.close()

def get_system_diagnostics(db_path: str = None) -> Dict[str, Any]:
    """
    Thực hiện kiểm tra chẩn đoán toàn diện hệ thống CSDL SQLite:
    - Kích thước tệp CSDL trên đĩa (bytes, MB).
    - Trạng thái toàn vẹn cấu trúc B-Tree (PRAGMA integrity_check).
    - Chế độ nhật ký (PRAGMA journal_mode = WAL).
    - Thống kê số lượng bản ghi của toàn bộ 7 bảng cốt lõi.
    - Kiểm tra tính toàn vẹn của Chuỗi băm kiểm toán bất biến (verify_audit_chain).
    """
    target_path = db_path if db_path is not None else os.getenv("DATABASE_PATH", DATABASE_PATH)
    file_size_bytes = os.path.getsize(target_path) if os.path.exists(target_path) else 0
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

    conn = sqlite3.connect(target_path, timeout=30.0)
    try:
        integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        page_size = conn.execute("PRAGMA page_size;").fetchone()[0]
        page_count = conn.execute("PRAGMA page_count;").fetchone()[0]
        freelist_count = conn.execute("PRAGMA freelist_count;").fetchone()[0]

        counts = {}
        for table in ["surveys", "questions", "responses", "response_answers", "quality_assessments", "audit_logs", "survey_versions"]:
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                counts[table] = row[0] if row else 0
            except sqlite3.OperationalError:
                counts[table] = 0

        audit_check = verify_audit_chain(conn)

        return {
            "status": "healthy" if integrity == "ok" else "warning",
            "db_path": target_path,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": file_size_mb,
            "sqlite_pragmas": {
                "integrity_check": integrity,
                "journal_mode": journal_mode,
                "page_size_bytes": page_size,
                "page_count": page_count,
                "freelist_pages": freelist_count
            },
            "table_record_counts": counts,
            "tamper_evident_ledger": {
                "is_chain_valid": audit_check.get("is_valid", True),
                "total_audit_records": audit_check.get("total_records", 0),
                "head_hash": audit_check.get("head_hash")
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        conn.close()



