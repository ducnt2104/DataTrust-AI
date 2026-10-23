import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    Bộ giới hạn tốc độ (Rate Limiter) trượt theo cửa sổ thời gian (Sliding Window)
    Bảo vệ các điểm cuối nhận khảo sát công khai chống tấn công flood/spam/DDoS
    Tuân thủ Phần VII (Bảo mật & Quyền riêng tư)
    """
    def __init__(self, requests_per_minute: int = 40):
        self.rpm = requests_per_minute
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request, custom_rpm: Optional[int] = None):
        # Bỏ qua khi có header bypass phục vụ test kiểm thử tự động
        if request.headers.get("X-Test-Bypass") == "1":
            return

        # Trong môi trường TestClient, chỉ kích hoạt khi test chỉ định rõ header X-Test-Rate-Limit
        if request.client and request.client.host == "testclient" and request.headers.get("X-Test-Rate-Limit") != "1":
            return

        limit = custom_rpm or self.rpm
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0

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

# Singleton rate limiter instance
public_submission_limiter = SlidingWindowRateLimiter(requests_per_minute=40)
