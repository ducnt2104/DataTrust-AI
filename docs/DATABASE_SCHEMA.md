# DataTrust — Database Schema Specification

## 1. Cơ Chế Lưu Trữ (Storage Engine)
- Hệ quản trị: SQLite 3 / PostgreSQL Compatible.
- Kích hoạt cơ chế: `PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;`

## 2. Các Bảng Dữ Liệu Thực Thể (Entity Tables)

### 2.1. `surveys`
Lưu trữ thông tin cơ bản và vòng đời của từng cuộc khảo sát.
- `id`: `TEXT PRIMARY KEY` (UUID string)
- `title`: `TEXT NOT NULL`
- `description`: `TEXT`
- `instructions`: `TEXT`
- `status`: `TEXT NOT NULL DEFAULT 'draft'` ('draft', 'published', 'closed', 'archived')
- `public_slug`: `TEXT UNIQUE NOT NULL` (Slug dùng cho link công khai `/s/:slug`)
- `version`: `INTEGER NOT NULL DEFAULT 1`
- `created_at`: `TEXT NOT NULL` (ISO-8601 UTC timestamp)
- `updated_at`: `TEXT NOT NULL`
- `closed_at`: `TEXT`
- `settings_json`: `TEXT` (JSON object lưu cấu hình: cho phép ẩn danh, giới hạn thời gian, v.v.)

### 2.2. `questions`
Lưu trữ định nghĩa từng câu hỏi trong khảo sát.
- `id`: `TEXT PRIMARY KEY` (UUID string)
- `survey_id`: `TEXT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE`
- `order_index`: `INTEGER NOT NULL DEFAULT 0`
- `question_type`: `TEXT NOT NULL` ('short_text', 'long_text', 'single_choice', 'multiple_choice', 'dropdown', 'linear_scale', 'likert', 'matrix', 'number', 'date', 'boolean', 'ranking')
- `title`: `TEXT NOT NULL`
- `description`: `TEXT`
- `is_required`: `INTEGER NOT NULL DEFAULT 0` (0: Không bắt buộc, 1: Bắt buộc)
- `options_json`: `TEXT` (JSON array: danh sách các lựa chọn đáp án `[{"id": "opt_1", "label": "Nam"}, ...]`, cấu hình min/max, thang đo)
- `logic_rules_json`: `TEXT` (JSON array: quy tắc rẽ nhánh, hiển thị điều kiện `[{"depends_on_question_id": "q1", "operator": "equals", "value": "Có", "action": "show"}]`)
- `created_at`: `TEXT NOT NULL`

### 2.3. `responses`
Lưu trữ từng bản ghi phản hồi từ người tham gia.
- `id`: `TEXT PRIMARY KEY` (UUID string)
- `survey_id`: `TEXT NOT NULL REFERENCES surveys(id) ON DELETE CASCADE`
- `survey_version`: `INTEGER NOT NULL DEFAULT 1`
- `started_at`: `TEXT NOT NULL` (ISO-8601 UTC)
- `submitted_at`: `TEXT NOT NULL` (ISO-8601 UTC)
- `duration_seconds`: `REAL NOT NULL DEFAULT 0.0`
- `client_metadata_json`: `TEXT` (JSON: kích thước màn hình, user-agent thu gọn, ngôn ngữ)
- `risk_score`: `REAL DEFAULT 0.0` (Điểm rủi ro tổng hợp từ 0.0 đến 100.0)
- `risk_level`: `TEXT DEFAULT 'low'` ('low', 'medium', 'high')
- `analysis_status`: `TEXT DEFAULT 'pending'` ('pending', 'analyzed', 'failed')
- `review_status`: `TEXT DEFAULT 'unverified'` ('unverified', 'under_review', 'verified_valid', 'verified_fraud', 'inconclusive')
- `review_notes`: `TEXT`
- `reviewed_at`: `TEXT`

### 2.4. `response_answers`
Lưu trữ câu trả lời chi tiết cho từng câu hỏi.
- `id`: `TEXT PRIMARY KEY` (UUID string)
- `response_id`: `TEXT NOT NULL REFERENCES responses(id) ON DELETE CASCADE`
- `question_id`: `TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE`
- `answer_value`: `TEXT` (Giá trị câu trả lời được serialize thành JSON string hoặc chuỗi chuẩn hóa)
- `created_at`: `TEXT NOT NULL`

### 2.5. `quality_assessments`
Lưu trữ kết quả đánh giá phân tích chất lượng của Quality Engine cho từng phản hồi.
- `id`: `TEXT PRIMARY KEY` (UUID string)
- `response_id`: `TEXT NOT NULL REFERENCES responses(id) ON DELETE CASCADE`
- `score_dup`: `REAL DEFAULT 0.0` (Điểm trùng lặp / gần trùng lặp)
- `score_pattern`: `REAL DEFAULT 0.0` (Điểm mẫu trả lời bất thường / straightlining)
- `score_logic`: `REAL DEFAULT 0.0` (Điểm vi phạm quy tắc logic)
- `score_speed`: `REAL DEFAULT 0.0` (Điểm tốc độ làm bài bất thường)
- `score_text`: `REAL DEFAULT 0.0` (Điểm câu hỏi mở lặp lại / vô nghĩa)
- `composite_score`: `REAL DEFAULT 0.0` (Điểm rủi ro tổng hợp)
- `flags_json`: `TEXT NOT NULL` (JSON array: danh sách các cờ cảnh báo chi tiết `[{"code": "FLAG_STRAIGHTLINING", "severity": "HIGH", "message": "..."}]`)
- `assessed_at`: `TEXT NOT NULL`

### 2.6. `audit_logs`
Lưu trữ lịch sử thao tác quan trọng để đảm bảo tính minh bạch.
- `id`: `TEXT PRIMARY KEY` (UUID string)
- `entity_type`: `TEXT NOT NULL` ('survey', 'response', 'verification')
- `entity_id`: `TEXT NOT NULL`
- `action`: `TEXT NOT NULL` ('CREATE', 'UPDATE', 'PUBLISH', 'CLOSE', 'REVIEW_DECISION', 'EXPORT')
- `details_json`: `TEXT`
- `created_at`: `TEXT NOT NULL`
