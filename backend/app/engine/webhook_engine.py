import hmac
import hashlib
import json
import uuid
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class WebhookEngine:
    """
    Động cơ phát thanh cảnh báo thời gian thực (Real-time Anomaly Webhook Dispatcher)
    Gửi thông báo bảo mật và phát hiện gian lận thực địa đến hệ thống giám sát bên ngoài (Slack, Teams, SIEM).
    Bảo vệ bằng chữ ký mật mã học HMAC-SHA256 (RFC 2104).
    """

    DEFAULT_TIMEOUT_SECONDS = 3.0
    RISK_ALERT_THRESHOLD = 70.0

    @staticmethod
    def compute_hmac_signature(secret: str, payload_bytes: bytes) -> str:
        """
        Tính toán chữ ký HMAC-SHA256 bảo đảm tính xác thực và chống giả mạo của webhook
        """
        key = secret.encode("utf-8") if isinstance(secret, str) else secret
        mac = hmac.new(key, payload_bytes, hashlib.sha256)
        return f"sha256={mac.hexdigest()}"

    @classmethod
    def dispatch_payload(
        cls,
        webhook_url: str,
        payload: Dict[str, Any],
        webhook_secret: Optional[str] = None,
        event_type: str = "ANOMALY_ALERT",
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Dict[str, Any]:
        """
        Gửi payload JSON qua HTTP POST với đầy đủ chữ ký xác thực và đo lường độ trễ
        """
        delivery_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        
        full_payload = {
            "delivery_id": delivery_id,
            "event_type": event_type,
            "timestamp": ts,
            "data": payload
        }

        payload_bytes = json.dumps(full_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "DataTrust-Webhook-Dispatcher/1.0",
            "X-DataTrust-Event": event_type,
            "X-DataTrust-Delivery-ID": delivery_id,
            "X-DataTrust-Timestamp": ts
        }

        if webhook_secret:
            sig = cls.compute_hmac_signature(webhook_secret, payload_bytes)
            headers["X-DataTrust-Signature-256"] = sig

        start_time = time.perf_counter()
        req = urllib.request.Request(
            url=webhook_url,
            data=payload_bytes,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": 200 <= resp.status < 300,
                    "status_code": resp.status,
                    "delivery_id": delivery_id,
                    "latency_ms": elapsed_ms,
                    "error": None
                }
        except urllib.error.HTTPError as he:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "status_code": he.code,
                "delivery_id": delivery_id,
                "latency_ms": elapsed_ms,
                "error": f"HTTP Error {he.code}: {he.reason}"
            }
        except urllib.error.URLError as ue:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "status_code": None,
                "delivery_id": delivery_id,
                "latency_ms": elapsed_ms,
                "error": f"Network Error: {ue.reason}"
            }
        except Exception as ex:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "status_code": None,
                "delivery_id": delivery_id,
                "latency_ms": elapsed_ms,
                "error": str(ex)
            }

    @classmethod
    def async_dispatch_anomaly_alert(
        cls,
        survey_settings: Optional[Dict[str, Any]],
        survey_id: str,
        response_id: str,
        risk_score: float,
        risk_level: str,
        flags: list,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Kiểm tra cấu hình và phát tán webhook cảnh báo ngầm (non-blocking) qua daemon thread
        Không làm chậm hoặc cản trở luồng nộp phiếu của người dùng
        """
        if not survey_settings or not isinstance(survey_settings, dict):
            return

        webhook_url = survey_settings.get("alert_webhook_url") or survey_settings.get("webhook_url")
        if not webhook_url or not str(webhook_url).startswith(("http://", "https://")):
            return

        # Chỉ phát cảnh báo nếu rủi ro vượt ngưỡng hoặc có cờ bất thường
        is_high_risk = risk_score >= cls.RISK_ALERT_THRESHOLD or risk_level == "high"
        has_critical_flags = any(
            f.get("severity") in ("HIGH", "CRITICAL")
            for f in flags
        ) if flags else False

        if not (is_high_risk or has_critical_flags):
            return

        secret = survey_settings.get("webhook_secret", "")
        payload = {
            "survey_id": survey_id,
            "response_id": response_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags_count": len(flags),
            "flags": flags,
            "client_metadata": metadata or {}
        }

        # Phát tán trong daemon thread để giữ latency của API submit ở mức vi giây
        def _worker():
            cls.dispatch_payload(
                webhook_url=webhook_url,
                payload=payload,
                webhook_secret=secret,
                event_type="SURVEY_FRAUD_ANOMALY_DETECTED"
            )

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
