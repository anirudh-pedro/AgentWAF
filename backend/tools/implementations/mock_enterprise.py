import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import socket
from typing import Any
import uuid

from config import get_settings
from logger import get_logger
from tools.base import BaseTool
from tools.registry import ToolRegistry
from tools.schemas import ToolRequest, ToolResponse

logger = get_logger(__name__)


class MockEnterpriseTool(BaseTool):
    """Generic Mock Enterprise Tool returning deterministic structured JSON payloads."""

    def __init__(self, tool_name: str, description: str, category: str = "enterprise") -> None:
        self._name = tool_name
        self._description = description
        self._category = category

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def category(self) -> str:
        return self._category

    async def execute(self, request: ToolRequest) -> ToolResponse:
        params = request.parameters or {}
        tool_lower = self._name.lower()

        # Deterministic mock responses
        if "invoice" in tool_lower:
            invoice_id = params.get("invoice_id") or params.get("query") or "INV-100"
            result = {
                "invoice_id": invoice_id,
                "customer": "ACME Corp",
                "amount": "$12,450.00",
                "status": "APPROVED",
                "date": "2026-07-30",
                "items": ["Cloud Infrastructure Services", "Agent WAF License"],
            }
        elif "customer" in tool_lower:
            cust_id = params.get("customer_id") or "customer_123"
            result = {
                "customer_id": cust_id,
                "name": "Global Tech Solutions",
                "tier": "ENTERPRISE",
                "account_manager": "Sarah Jenkins",
                "status": "ACTIVE",
            }
        elif "order" in tool_lower:
            result = {
                "orders_count": 5,
                "total_volume": "$84,200.00",
                "last_order": "2026-07-28",
                "status": "DELIVERED",
            }
        elif "file" in tool_lower:
            file_name = params.get("file") or params.get("query") or "project_report.pdf"
            result = {
                "file_name": file_name,
                "size_bytes": 1048576,
                "content_type": "application/pdf",
                "download_url": f"https://enterprise-cdn.internal/files/{file_name}",
            }
        elif "summary" in tool_lower or "report" in tool_lower:
            result = {
                "summary": "Executive summary generated successfully from source data.",
                "insights": ["High compliance alignment", "Zero critical vulnerabilities detected"],
                "generated_at": "2026-07-31T08:30:00Z",
            }
        elif "calendar" in tool_lower or "meeting" in tool_lower:
            result = {
                "event": "Q3 Architecture Review Meeting",
                "time": "Tomorrow at 10:00 AM UTC",
                "status": "SCHEDULED",
                "attendees": ["engineering-leads@enterprise.internal"],
            }
        else:
            result = {
                "status": "SUCCESS",
                "tool_executed": self._name,
                "parameters_received": params,
            }

        return ToolResponse(
            success=True,
            result=result,
            metadata={"tool_name": self._name, "mock": True},
        )


class SendEmailTool(BaseTool):
    """Production-grade Gmail SMTP Email Tool supporting real Gmail dispatch and fallback sandbox execution."""

    @property
    def name(self) -> str:
        return "SendEmail"

    @property
    def description(self) -> str:
        return "Send notification email or invoice documents to specified recipients."

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def category(self) -> str:
        return "communication"

    async def execute(self, request: ToolRequest) -> ToolResponse:
        settings = get_settings()
        params = request.parameters or {}

        recipient = str(params.get("recipient") or params.get("to") or params.get("email") or "team@example.com").strip()
        subject = str(params.get("subject") or "Agent WAF Execution Summary Notification").strip()
        body = str(params.get("body") or "Executive summary and notification dispatch from Agent WAF ReAct Agent.").strip()
        attachment = params.get("attachment")

        gmail_user = settings.GMAIL_EMAIL
        gmail_pass = settings.GMAIL_APP_PASSWORD

        # Real Gmail SMTP Dispatch if credentials are fully configured
        if gmail_user and gmail_pass:
            logger.info("Initiating real Gmail SMTP email dispatch", extra={"recipient": recipient, "subject": subject})
            try:
                def _dispatch_smtp() -> str:
                    msg = MIMEMultipart()
                    msg["From"] = gmail_user
                    msg["To"] = recipient
                    msg["Subject"] = subject
                    msg.attach(MIMEText(body, "plain", "utf-8"))

                    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
                        server.starttls()
                        server.login(gmail_user, gmail_pass)
                        server.send_message(msg)

                    return f"msg-gmail-{uuid.uuid4().hex[:8]}"

                msg_id = await asyncio.to_thread(_dispatch_smtp)
                return ToolResponse(
                    success=True,
                    result={
                        "recipient": recipient,
                        "subject": subject,
                        "status": "SENT",
                        "provider": "Gmail SMTP",
                        "message_id": msg_id,
                        "attachment_processed": attachment is not None,
                    },
                    metadata={"tool_name": self.name, "provider": "Gmail SMTP"},
                )
            except smtplib.SMTPAuthenticationError as exc:
                logger.error("Gmail SMTP authentication failed", extra={"recipient": recipient, "error": str(exc)})
                return ToolResponse(
                    success=False,
                    error="Gmail SMTP authentication failed: Invalid GMAIL_EMAIL or GMAIL_APP_PASSWORD",
                    result={"recipient": recipient, "status": "FAILED", "provider": "Gmail SMTP", "error": "Authentication failure"},
                )
            except (smtplib.SMTPException, socket.timeout, TimeoutError, OSError) as exc:
                logger.error("Gmail SMTP network dispatch failed", extra={"recipient": recipient, "error": str(exc)})
                return ToolResponse(
                    success=False,
                    error=f"Gmail SMTP dispatch network timeout or connection error: {str(exc)}",
                    result={"recipient": recipient, "status": "FAILED", "provider": "Gmail SMTP", "error": str(exc)},
                )
            except Exception as exc:
                logger.exception("Unexpected error during Gmail SMTP execution", extra={"error": str(exc)})
                return ToolResponse(
                    success=False,
                    error=f"Gmail SMTP execution error: {str(exc)}",
                    result={"recipient": recipient, "status": "FAILED", "provider": "Gmail SMTP", "error": str(exc)},
                )

        # Fallback Sandbox Mode if Gmail credentials are not configured in environment
        logger.info("Gmail credentials not set in environment. Executing email dispatch in sandbox mode.", extra={"recipient": recipient})
        return ToolResponse(
            success=True,
            result={
                "recipient": recipient,
                "subject": subject,
                "status": "SENT",
                "provider": "Mock Email Service (Gmail SMTP Ready)",
                "message_id": f"msg-sandbox-{uuid.uuid4().hex[:8]}",
                "attachment_processed": attachment is not None,
            },
            metadata={"tool_name": self.name, "mock": True},
        )


def register_mock_enterprise_tools() -> list[str]:
    """Register all mock enterprise tools and real SendEmail tool into the global ToolRegistry."""
    registry = ToolRegistry.get_instance()
    mock_tools = [
        ("SearchInvoice", "Search for enterprise invoices by ID or query", "finance"),
        ("DownloadInvoice", "Download invoice document PDF payload", "finance"),
        ("SearchFiles", "Search internal file repository for documents", "storage"),
        ("DownloadFile", "Download file payload from enterprise repository", "storage"),
        ("ReadCustomer", "Fetch customer profile and subscription details", "crm"),
        ("QueryOrders", "Query customer purchase order history", "crm"),
        ("GenerateSummary", "Generate concise text summary from context data", "ai_utility"),
        ("GenerateReport", "Generate detailed executive report document", "ai_utility"),
        ("ReadCalendar", "Read user calendar schedules and availability", "productivity"),
        ("CreateMeeting", "Create calendar invite and meeting room link", "productivity"),
    ]

    registered = []
    for name, desc, cat in mock_tools:
        tool_obj = MockEnterpriseTool(name, desc, cat)
        try:
            registry.register(tool_obj)
            registered.append(name)
        except ValueError:
            pass

    # Register Real/Sandbox SendEmailTool
    try:
        registry.register(SendEmailTool())
        registered.append("SendEmail")
    except ValueError:
        pass

    return registered
