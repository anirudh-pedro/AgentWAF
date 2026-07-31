import time
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from logger import get_logger

logger = get_logger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding-window token bucket rate limiting middleware for FastAPI.
    
    Protects high-risk endpoints (such as /agent/execute) against flood abuse, DDoS, and prompt spamming.
    """

    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_records: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only rate-limit write execution endpoints (e.g. /agent/execute)
        if request.method == "POST" and request.url.path.startswith("/agent/execute"):
            client_ip = request.client.host if request.client else "127.0.0.1"
            now = time.time()
            window_start = now - self.window_seconds

            # Filter out timestamps older than the sliding window
            timestamps = [t for t in self.request_records[client_ip] if t > window_start]
            self.request_records[client_ip] = timestamps

            if len(timestamps) >= self.max_requests:
                logger.warning(
                    "Rate limit exceeded on /agent/execute",
                    extra={"client_ip": client_ip, "request_count": len(timestamps)},
                )
                return Response(
                    content='{"detail": "Rate limit exceeded. Maximum 30 requests per minute allowed."}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                    headers={
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + self.window_seconds)),
                        "Retry-After": str(self.window_seconds),
                    },
                )

            # Record request timestamp
            self.request_records[client_ip].append(now)

            response = await call_next(request)
            remaining = self.max_requests - len(self.request_records[client_ip])
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            return response

        return await call_next(request)
