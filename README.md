# Agent WAF (Agent Web Application Firewall) & SIEM Security Dashboard

![Agent WAF Banner](frontend/public/favicon.svg)

An enterprise-grade, high-performance security firewall, policy engine, and real-time SIEM (Security Information and Event Management) operational dashboard designed specifically to protect AI Agent Runtimes, LangGraph Agent Workflows, and Tool Execution Frameworks against Prompt Injections, SQL Injections, Dangerous Tool Category Invocations, and DoS Parameter Overflows.

---

## 🛡️ Architecture & Key Features

- **ASGI Security Proxy Middleware**: Transparent inspection proxy intercepting tool execution requests with minimal latency.
- **Dynamic Rule Engine**: Prioritized, concurrent multi-rule evaluation supporting Prompt Injection detection, SQL Injection detection, Dangerous Tool blocking, and Parameter Length/Depth enforcement.
- **Neon PostgreSQL Persistence**: High-performance asynchronous database persistence via SQLAlchemy 2.0 and `asyncpg`.
- **SIEM Operations Dashboard**: High-density React SIEM dashboard featuring real-time Events Per Second (EPS) circular gauge, live threat risk trends, rule hit analytics, and audit log inspection.

---

## 🚀 API Endpoint Reference

### 🔌 Backend REST API Endpoints (`FastAPI`)

Base URL: `http://localhost:8000/api/v1` (or root prefix `/dashboard`)

| Method | Endpoint Path | Summary | Description | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/dashboard/summary` | **Dashboard Summary Metrics** | Aggregated request volume, allowed vs. blocked counts, average risk score, latency, top rule, top tool, and time-series traffic trend. | `DashboardSummary` |
| `GET` | `/dashboard/audit` | **Audit Log Timeline Stream** | Timeline of audited tool requests with optional query parameters: `tool`, `decision` (`ALLOW`/`BLOCK`), `rule`, and `limit`. | `list[AuditEvent]` |
| `GET` | `/dashboard/rules` | **Security Rule Analytics** | Performance metrics, total evaluation count, total match hit counts, and average latency per security rule. | `list[RuleStatistics]` |
| `GET` | `/dashboard/tools` | **Tool Usage Analytics** | Call volumes (total, allowed, blocked), categories, and execution latency metrics per registered agent tool. | `list[ToolStatistics]` |
| `GET` | `/dashboard/risk` | **Risk Analytics & Severity** | Threat distribution across severity tiers (`low`, `medium`, `high`, `critical`), overall risk score, and risk trends. | `RiskStatistics` |
| `GET` | `/dashboard/health` | **System Readiness Telemetry** | Proxy status, database health (`healthy`), memory usage (MB), uptime, registered tool list, and active module list. | `SystemHealth` |
| `GET` | `/api/v1/health` | **Application Health Check** | FastAPI standard service readiness check. | `dict[str, str]` |

---

### 💻 Frontend API Service & React Hooks (`React` + `TypeScript`)

Location: [`frontend/src/services/api.ts`](file:///c:/Users/HP/Desktop/AgentWAF/frontend/src/services/api.ts) & [`frontend/src/hooks/useDashboard.ts`](file:///c:/Users/HP/Desktop/AgentWAF/frontend/src/hooks/useDashboard.ts)

| Frontend API Function | Backend Endpoint | Custom React Query Hook | Dashboard Component Consumer |
| :--- | :--- | :--- | :--- |
| `api.getSummary()` | `GET /dashboard/summary` | `useDashboardSummary()` | Top Stat Cards (`Total Requests`, `Blocked Threats`), `GaugeCard` (EPS), `Log Sources & Traffic Requests` Bar Chart |
| `api.getAuditEvents(params)` | `GET /dashboard/audit` | `useAuditEvents(params)` | `AuditTable` (Live Audit Timeline), `AuditDrawer` (Inspector) |
| `api.getRuleStats()` | `GET /dashboard/rules` | `useRuleStats()` | `Security Rule Hit Analytics` Bar Chart |
| `api.getToolStats()` | `GET /dashboard/tools` | `useToolStats()` | `Tool Call Volume & Enforcement` Multi-Bar Chart |
| `api.getRiskStats()` | `GET /dashboard/risk` | `useRiskStats()` | `Risk Severity Distribution` Bar Chart, `Threat Risk Score Trend` Area Chart |
| `api.getSystemHealth()` | `GET /dashboard/health` | `useSystemHealth()` | `ServerStatusCard` (Active Server Status), `HealthCard` (System Readiness Telemetry) |

---

## 🛠️ Project Structure

```
AgentWAF/
├── backend/
│   ├── agent/             # LangGraph Agent Runtime & Tool Executor
│   ├── config/            # Pydantic v2 Application Configuration & Environment Settings
│   ├── dashboard/         # Audit Publisher, Repository, Metrics Service, & REST API Routes
│   ├── db/                # Neon PostgreSQL Database Engine & Models
│   ├── logger/            # Structured JSON / Text Logger
│   ├── middleware/        # Pure ASGI Request ID & Tracing Middleware
│   ├── proxy/             # Agent WAF Policy Enforcing Proxy
│   ├── rules/             # Security Rule Engine & Built-in Rule Implementations
│   ├── tools/             # Built-in Agent Tools (Echo, Calculator, DateTime) & Registry
│   ├── app.py             # FastAPI Main Application Bootstrap
│   ├── test_suite.py      # End-to-End Security Test Suite
│   └── tests/             # Pytest Unit Tests for Security Rules
├── frontend/
│   ├── src/
│   │   ├── components/    # GaugeCard, ServerStatusCard, StatCard, ChartCard, AuditTable, AuditDrawer
│   │   ├── hooks/         # React Query Custom Hooks
│   │   ├── pages/         # Single-Page SIEM Operations Dashboard
│   │   ├── services/      # Axios Backend API Integration Service
│   │   └── types/         # TypeScript Interfaces matching Backend Models
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## 🚦 Quick Start & Running Locally

### 1. Backend Setup (`FastAPI` & `Python 3.12`)

```bash
cd backend

# Install dependencies using uv
uv sync

# Configure environment variables (Neon PostgreSQL connection string)
# Create .env with DATABASE_URL="postgresql://user:pass@ep-cold-voice.aws.neon.tech/neondb?sslmode=require"

# Run FastAPI Server
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Run Security Test Suite & Pytest Unit Tests

```bash
cd backend

# Run isolated security rule unit tests
uv run pytest

# Run integration security test suite across diverse attack vectors
uv run python test_suite.py
```

### 3. Frontend Setup (`React` + `Vite` + `Tailwind CSS`)

```bash
cd frontend

# Install dependencies
npm install

# Start Vite Development Server
npm run dev

# Build for Production
npm run build
```

---

## 🔒 Security Rules Reference

1. **`RULE-SEC-PROMPT-INJ-001` (Prompt Injection Detector)**: Detects instructions attempting to override system prompts or jailbreak LLMs (`ignore previous instructions`, `system override`, `reveal keys`, `jailbreak`).
2. **`RULE-SEC-SQL-INJ-002` (SQL Injection Detector)**: Intercepts raw SQL syntax commands (`UNION SELECT`, `DROP TABLE`, `' OR '1'='1`).
3. **`RULE-SEC-DANGEROUS-TOOL-003` (Dangerous Tool Category Policy)**: Prohibits invocation of tools belonging to restricted categories (`shell`, `filesystem`, `system`).
4. **`RULE-SEC-PARAM-SIZE-004` (Parameter Limits Policy)**: Rejects oversized string parameters (>10,000 chars) or deep object nesting (>5 levels).
