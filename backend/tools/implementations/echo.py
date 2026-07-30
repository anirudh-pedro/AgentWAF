import time
from logger import get_logger
from ..base import BaseTool
from ..schemas import ToolRequest, ToolResponse

logger = get_logger(__name__)


class EchoTool(BaseTool):
    """Tool that echoes back received input parameters."""

    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "Echoes back the received message input payload."

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

        message = request.parameters.get("message")
        if message is None:
            logger.warning(
                "EchoTool validation failed: missing 'message' parameter",
                extra={"tool_name": self.name, "request_id": request.request_id}
            )
            return self.create_error_response("Missing required parameter 'message'", start_time)

        result = {"message": message}
        return self.create_success_response(result, start_time)
