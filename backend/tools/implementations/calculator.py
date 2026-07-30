import time
from decimal import Decimal, InvalidOperation
from logger import get_logger
from ..base import BaseTool
from ..schemas import ToolRequest, ToolResponse

logger = get_logger(__name__)


class CalculatorTool(BaseTool):
    """Tool for performing basic arithmetic operations (add, subtract, multiply, divide)."""

    _SUPPORTED_OPERATIONS: set[str] = {"add", "subtract", "multiply", "divide"}

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Performs basic arithmetic operations (add, subtract, multiply, divide)."

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

        operation = request.parameters.get("operation")
        a = request.parameters.get("a")
        b = request.parameters.get("b")

        # Validate parameter presence
        if not operation or a is None or b is None:
            logger.warning(
                "CalculatorTool validation failed: missing required parameters",
                extra={"tool_name": self.name, "request_id": request.request_id}
            )
            return self.create_error_response(
                "Missing required parameters. 'operation', 'a', and 'b' are required.",
                start_time
            )

        # Validate operation type
        op_name = str(operation).lower().strip()
        if op_name not in self._SUPPORTED_OPERATIONS:
            logger.warning(
                "CalculatorTool validation failed: unsupported operation",
                extra={"tool_name": self.name, "operation": op_name, "request_id": request.request_id}
            )
            return self.create_error_response(
                f"Unsupported operation '{operation}'. Supported operations: {sorted(self._SUPPORTED_OPERATIONS)}",
                start_time
            )

        # Validate numeric types using Decimal for arithmetic precision
        try:
            num_a = Decimal(str(a))
            num_b = Decimal(str(b))
        except (ValueError, TypeError, InvalidOperation):
            logger.warning(
                "CalculatorTool validation failed: non-numeric operands",
                extra={"tool_name": self.name, "a": a, "b": b, "request_id": request.request_id}
            )
            return self.create_error_response("Operands 'a' and 'b' must be valid numbers.", start_time)

        # Execute arithmetic operation
        if op_name == "add":
            res = num_a + num_b
        elif op_name == "subtract":
            res = num_a - num_b
        elif op_name == "multiply":
            res = num_a * num_b
        elif op_name == "divide":
            if num_b == Decimal("0"):
                logger.warning(
                    "CalculatorTool execution failed: division by zero",
                    extra={"tool_name": self.name, "request_id": request.request_id}
                )
                return self.create_error_response("Division by zero is not allowed.", start_time)
            res = num_a / num_b
        else:
            return self.create_error_response("Invalid operation state", start_time)

        # Format output cleanly as integer if whole number or float/number
        final_result: int | float = int(res) if res % 1 == 0 else float(res)
        return self.create_success_response({"result": final_result}, start_time)
