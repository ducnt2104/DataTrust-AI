# DataTrust AI — Hướng Dẫn Triển Khai Môi Trường Sản Xuất (Production Deployment Guide)
## Triển Khai Trên Máy Chủ Linux / Windows Với Nginx, Systemd & SQLite WAL Backup

**Tài liệu mã số:** `DT-DEP-2026-V2`  
**Cập nhật lần cuối:** 2026-10-23  

---

## 1. Yêu Cầu Hạ Tầng (Prerequisites)

- **Hệ điều hành:** Ubuntu 22.04+ LTS / Debian 12 / Windows Server 2022.
- **Python:** Python 3.10+ (Khuyến nghị 3.11 hoặc 3.12).
- **Node.js:** Node.js 18+ LTS hoặc 20+ LTS.
- **Nginx:** Nginx 1.22+ hỗ trợ HTTP/2 và WebSocket.
- **Dung lượng đĩa:** Tối thiểu 10GB SSD/NVMe để đảm bảo hiệu năng I/O cho SQLite WAL mode.

---

## 2. Các Bước Cài Đặt Ban Đầu (Server Setup)

### 2.1. Clone Mã Nguồn & Tạo Môi Trường Ảo
```bash
# Clone dự án vào thư mục chuẩn
cd /var/www
git clone https://github.com/your-org/DataTrust-AI.git datatrust
cd /var/www/datatrust/backend

# Tạo Python Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2. Biên Dịch Giao Diện Frontend
```bash
cd /var/www/datatrust/frontend
npm install
npm run build
# Tệp tĩnh được sinh ra tại: /var/www/datatrust/frontend/dist
```

---

## 3. Cấu Hình Biến Môi Trường (`backend/.env`)

Tạo tệp `/var/www/datatrust/backend/.env` với nội dung:
```env
PORT=8000
HOST=127.0.0.1
DATABASE_URL=sqlite:///./data/datatrust.db
PUBLIC_BASE_URL=https://datatrust.example.com
ENVIRONMENT=production

# Tùy chọn AI (Để trống sẽ sử dụng Deterministic NLP Engine cục bộ)
GEMINI_API_KEY=
OPENAI_API_KEY=
```

Đảm bảo thư mục dữ liệu tồn tại và phân quyền an toàn:
```bash
mkdir -p /var/www/datatrust/backend/data
chmod 700 /var/www/datatrust/backend/data
```

---

## 4. Quản Lý Dịch Vụ Với Systemd (`datatrust-api.service`)

Tạo file dịch vụ `/etc/systemd/system/datatrust-api.service`:
```ini
[Unit]
Description=DataTrust AI Backend API Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/datatrust/backend
EnvironmentFile=/var/www/datatrust/backend/.env
ExecStart=/var/www/datatrust/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --timeout-keep-alive 30
Restart=always
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Kích hoạt và khởi chạy service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable datatrust-api
sudo systemctl start datatrust-api
sudo systemctl status datatrust-api
```

---

## 5. Cấu Hình Nginx Reverse Proxy & Chứng Chỉ SSL/TLS

Tạo file cấu hình `/etc/nginx/sites-available/datatrust.conf`:
```nginx
# Rate limiting zone: 40 requests/phút per IP
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=40r/m;

server {
    listen 80;
    server_name datatrust.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name datatrust.example.com;

    # Chứng chỉ SSL (Ví dụ Certbot Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/datatrust.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/datatrust.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Bảo mật Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 1. Frontend SPA Tĩnh
    root /var/www/datatrust/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 2. Backend REST API
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # 3. Swagger Docs (Chỉ mở nội bộ hoặc có xác thực nếu cần)
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
```

Kích hoạt site và reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/datatrust.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Kịch Bản Sao Lưu Định Kỳ SQLite WAL Không Ngừng Dịch Vụ (`backup_sqlite.sh`)

Vì SQLite đang chạy ở chế độ Write-Ahead Logging (WAL), ta sử dụng lệnh `.backup` chính thống của SQLite CLI để tạo snapshot cơ sở dữ liệu nguyên tử mà **không cần dừng dịch vụ**:

Tạo script `/var/www/datatrust/scripts/backup_sqlite.sh`:
```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/datatrust"
DB_PATH="/var/www/datatrust/backend/data/datatrust.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/datatrust_backup_${TIMESTAMP}.db"

mkdir -p "${BACKUP_DIR}"

# Thực hiện snapshot atomic an toàn tuyệt đối
sqlite3 "${DB_PATH}" ".backup '${BACKUP_FILE}'"

# Nén gzip để tiết kiệm dung lượng
gzip -9 "${BACKUP_FILE}"

# Xóa các bản sao lưu cũ hơn 30 ngày
find "${BACKUP_DIR}" -name "datatrust_backup_*.db.gz" -mtime +30 -delete

echo "[$(date)] Sao lưu DataTrust SQLite thành công: ${BACKUP_FILE}.gz"
```

Cấp quyền thực thi và đưa vào Crontab (chạy hàng ngày lúc 02:00 sáng):
```bash
chmod +x /var/www/datatrust/scripts/backup_sqlite.sh
# Thêm vào crontab
echo "0 2 * * * /var/www/datatrust/scripts/backup_sqlite.sh >> /var/log/datatrust_backup.log 2>&1" | sudo crontab -
```

---

## 7. Giám Sát Sức Khỏe & Tự Động Phục Hồi (Health Monitoring)

- API cung cấp endpoint giám sát sức khỏe:
  ```http
  GET /api/health
  ```
  Trả về HTTP 200 `{ "status": "healthy" }` kèm danh sách capabilities đang hoạt động.
- Có thể tích hợp với Uptime Kuma, Prometheus hoặc AWS Route53 Health Checks để tự động kích hoạt cảnh báo khi dịch vụ gặp sự cố.
