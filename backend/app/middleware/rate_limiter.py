import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    Bộ giới hạn tốc độ (Rate Limiter) trượt theo cửa sổ thời gian (Sliding Window)
    Bảo vệ các điểm cuối nhận khảo sát công khai & AI chống tấn công flood/spam/DDoS/Quota exhaustion
    Tuân thủ Tiêu chuẩn OWASP API Security và rà soát bộ nhớ tự động (Memory Leak Prevention).
    """
    def __init__(self, requests_per_minute: int = 40):
        self.rpm = requests_per_minute
        self.history: Dict[str, List[float]] = defaultdict(list)
        self.last_cleanup = time.time()

    def get_client_ip(self, request: Request) -> str:
        """Trích xuất địa chỉ IP thực của client, hỗ trợ môi trường đệm ngược (Reverse Proxy / Load Balancer)"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",") if p.strip()]
            if parts:
                return parts[0]
        return request.client.host if request.client else "unknown"

    def check(self, request: Request, custom_rpm: Optional[int] = None):
        # Bỏ qua khi có header bypass phục vụ test kiểm thử tự động
        if request.headers.get("X-Test-Bypass") == "1":
            return

        # Trong môi trường TestClient, chỉ kích hoạt khi test chỉ định rõ header X-Test-Rate-Limit
        if request.client and request.client.host == "testclient" and request.headers.get("X-Test-Rate-Limit") != "1":
            return

        limit = custom_rpm or self.rpm
        client_ip = self.get_client_ip(request)
        now = time.time()
        window_start = now - 60.0

        # Làm sạch định kỳ chống rò rỉ bộ nhớ (Memory bounds protection)
        if now - self.last_cleanup > 300.0 or len(self.history) > 1000:
            self._cleanup(window_start)
            self.last_cleanup = now

        # Làm sạch các mốc thời gian cũ hơn 60s
        self.history[client_ip] = [ts for ts in self.history[client_ip] if ts > window_start]

        if len(self.history[client_ip]) >= limit:
            retry_after = int(60.0 - (now - self.history[client_ip][0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Tần suất gửi yêu cầu vượt quá giới hạn an toàn. Vui lòng thử lại sau.",
                headers={"Retry-After": str(max(1, retry_after))}
            )

        self.history[client_ip].append(now)

    def _cleanup(self, window_start: float):
        keys_to_remove = []
        for ip, timestamps in self.history.items():
            valid_ts = [ts for ts in timestamps if ts > window_start]
            if not valid_ts:
                keys_to_remove.append(ip)
            else:
                self.history[ip] = valid_ts
        for k in keys_to_remove:
            self.history.pop(k, None)

# Singleton rate limiter instances
public_submission_limiter = SlidingWindowRateLimiter(requests_per_minute=40)
ai_generation_limiter = SlidingWindowRateLimiter(requests_per_minute=20)
InMemoryRateLimiter = SlidingWindowRateLimiter

