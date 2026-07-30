import time
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from logger import get_logger

logger = get_logger(__name__)


def _get_client_ip(request: Request) -> str:
    """Extract client IP handling X-Forwarded-For and X-Real-IP headers."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"


def _sanitize_query(query: str) -> str:
    """Sanitize query string to redact sensitive parameters."""
    if not query:
        return ""
    # Extensible sanitization hook for future parameter redaction
    return query


class RequestLoggingMiddleware:
    """Pure ASGI middleware for HTTP request execution timing and structured logging."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        if "state" in scope and isinstance(scope["state"], dict):
            scope["state"]["start_time"] = start_time

        request = Request(scope)
        request_id = scope.get("state", {}).get("request_id", "unknown")
        method = request.method
        path = request.url.path
        query = _sanitize_query(request.url.query)
        client_ip = _get_client_ip(request)

        status_code = 500

        async def send_with_logging(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_with_logging)

            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "HTTP request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "query": query,
                    "client_ip": client_ip,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "HTTP request failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "query": query,
                    "client_ip": client_ip,
                    "duration_ms": duration_ms,
                },
            )
            raise
