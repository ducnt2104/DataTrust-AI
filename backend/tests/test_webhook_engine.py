import json
import time
import threading
import http.server
from fastapi.testclient import TestClient
from app.main import app
from app.engine.webhook_engine import WebhookEngine

client = TestClient(app)

class MockWebhookHandler(http.server.BaseHTTPRequestHandler):
    received_requests = []

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        parsed_body = json.loads(body.decode("utf-8")) if body else {}

        MockWebhookHandler.received_requests.append({
            "path": self.path,
            "headers": {k.lower(): v for k, v in self.headers.items()},
            "body": parsed_body
        })

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "received": true}')

    def log_message(self, format, *args):
        pass  # Tắt log để giữ test output sạch sẽ

def test_webhook_hmac_signature():
    """Kiểm tra tính toán chữ ký HMAC-SHA256 chuẩn bảo đảm tính toàn vẹn gói tin"""
    secret = "datatrust_secret_key_2026"
    payload = b'{"event":"test","risk_score":85.0}'
    
    sig1 = WebhookEngine.compute_hmac_signature(secret, payload)
    sig2 = WebhookEngine.compute_hmac_signature(secret, payload)
    
    assert sig1.startswith("sha256=")
    assert sig1 == sig2  # Tính tất định
    assert len(sig1) == 7 + 64  # "sha256=" + 64 hex characters

    # Thay đổi payload -> chữ ký phải thay đổi lập tức
    tampered_sig = WebhookEngine.compute_hmac_signature(secret, b'{"event":"test","risk_score":86.0}')
    assert sig1 != tampered_sig

def test_webhook_dispatch_and_test_endpoint():
    """Kiểm tra phát tán gói tin qua HTTP POST và API test webhook của khảo sát"""
    MockWebhookHandler.received_requests = []
    server = http.server.HTTPServer(("127.0.0.1", 0), MockWebhookHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    webhook_url = f"http://127.0.0.1:{port}/webhook-receiver"
    secret = "my_custom_secret_key"

    try:
        # 1. Tạo khảo sát mẫu
        s_res = client.post("/api/surveys", json={
            "title": "Khảo sát Kiểm định Webhook Cảnh báo Gian lận",
            "description": "Test Webhook Dispatcher"
        })
        assert s_res.status_code == 201
        survey_id = s_res.json()["id"]

        # 2. Gọi endpoint test-webhook
        test_res = client.post(f"/api/surveys/{survey_id}/settings/test-webhook", json={
            "webhook_url": webhook_url,
            "webhook_secret": secret
        })
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["success"] is True
        assert test_data["status_code"] == 200
        assert test_data["latency_ms"] >= 0.0

        # Xác minh mock server đã nhận đúng gói tin
        assert len(MockWebhookHandler.received_requests) >= 1
        last_req = MockWebhookHandler.received_requests[-1]
        assert last_req["path"] == "/webhook-receiver"
        assert "x-datatrust-event" in last_req["headers"]
        assert last_req["headers"]["x-datatrust-event"] == "TEST_WEBHOOK_PING"
        assert "x-datatrust-signature-256" in last_req["headers"]
        assert last_req["headers"]["x-datatrust-signature-256"].startswith("sha256=")
        assert last_req["body"]["data"]["simulated_risk_score"] == 85.0

        # 3. Kiểm tra async_dispatch_anomaly_alert
        settings = {
            "alert_webhook_url": webhook_url,
            "webhook_secret": secret
        }
        # Phản hồi rủi ro cao (88.0) -> phải phát tín hiệu
        WebhookEngine.async_dispatch_anomaly_alert(
            survey_settings=settings,
            survey_id=survey_id,
            response_id="resp_fraud_test",
            risk_score=88.0,
            risk_level="high",
            flags=[{"code": "FLAG_SPEEDING", "severity": "HIGH", "message": "Quá tốc độ"}]
        )
        time.sleep(0.15)  # Chờ daemon thread phát tín hiệu
        assert len(MockWebhookHandler.received_requests) >= 2

        # Phản hồi rủi ro thấp (10.0, không có cờ) -> KHÔNG phát tín hiệu
        initial_len = len(MockWebhookHandler.received_requests)
        WebhookEngine.async_dispatch_anomaly_alert(
            survey_settings=settings,
            survey_id=survey_id,
            response_id="resp_clean_test",
            risk_score=10.0,
            risk_level="low",
            flags=[]
        )
        time.sleep(0.1)
        assert len(MockWebhookHandler.received_requests) == initial_len

    finally:
        server.shutdown()
        server.server_close()
