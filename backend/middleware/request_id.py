import re
import uuid
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from config import get_settings
from logger import get_logger

logger = get_logger(__name__)

# Validates printable ASCII request ID format with length between 1 and 128 characters
_VALID_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-.:]{1,128}$")


def _is_valid_request_id(request_id: str) -> bool:
    """Validate incoming request ID format and length."""
    return bool(_VALID_REQUEST_ID_REGEX.match(request_id))


class RequestIDMiddleware:
    """Pure ASGI middleware for request trace correlation and state shape initialization."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        header_key = settings.REQUEST_ID_HEADER.lower().encode("latin-1")

        request = Request(scope)
        request_id: str | None = None

        # Extract and validate incoming header
        header_val = request.headers.get(settings.REQUEST_ID_HEADER)
        if header_val:
            candidate = header_val.strip()
            if _is_valid_request_id(candidate):
                request_id = candidate

        if not request_id:
            request_id = str(uuid.uuid4())

        # Ensure state dictionary exists in ASGI scope
        if "state" not in scope:
            scope["state"] = {}

        # Initialize predictable request state shape for downstream modules
        scope["state"]["request_id"] = request_id
        scope["state"]["start_time"] = None
        scope["state"]["agent_id"] = None
        scope["state"]["session_id"] = None
        scope["state"]["tool_name"] = None
        scope["state"]["policy_result"] = None
        scope["state"]["risk_score"] = None

        # Intercept send to append X-Request-ID response header
        async def send_with_request_id(message: dict) -> None:
            if message["type"] == "http.response.start":
                resp_headers = list(message.get("headers", []))
                resp_headers.append(
                    (settings.REQUEST_ID_HEADER.encode("latin-1"), request_id.encode("latin-1"))
                )
                message["headers"] = resp_headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)
