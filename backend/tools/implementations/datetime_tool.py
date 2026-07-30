import time
from datetime import datetime, timezone
from logger import get_logger
from ..base import BaseTool
from ..schemas import ToolRequest, ToolResponse

logger = get_logger(__name__)


class DateTimeTool(BaseTool):
    """Tool that returns the current UTC timestamp in ISO 8601 Z format."""

    @property
    def name(self) -> str:
        return "datetime"

    @property
    def description(self) -> str:
        return "Returns current UTC timestamp in ISO 8601 format."

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def category(self) -> str:
        return "utility"

    async def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        logger.info(
            "Executing tool",
            extra={"tool_name": self.name, "request_id": request.request_id}
        )

        dt = datetime.now(timezone.utc)
        timestamp_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        result = {"timestamp": timestamp_str}
        return self.create_success_response(result, start_time)
