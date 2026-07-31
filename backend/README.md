# 🛡️ Agent WAF - FastAPI Backend Service

Enterprise-grade Agent Web Application Firewall backend built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL (Neon Serverless)**, and **Pydantic v2**.

---

## ⚡ Quick Start

```bash
# 1. Install dependencies with uv
uv sync

# 2. Configure environment
cp .env.example .env

# 3. Start development server
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Security Test Suite

```bash
uv run python test_suite.py
```

---

## 📊 Endpoints Summary

- `POST /agent/execute`: Execute agent query through WAF inspection proxy.
- `GET /dashboard/summary`: Operational metrics summary.
- `GET /dashboard/audit`: Audit timeline with decision & tool filters.
- `GET /dashboard/rules`: Security rule hits & performance.
- `GET /dashboard/tools`: Tool invocation stats & latency.
- `GET /dashboard/risk`: Severity risk distribution.
- `GET /dashboard/health`: System health & database readiness.
- `GET /metrics`: Observability & Prometheus scraping metrics.
- `GET /health`, `/ready`, `/live`: Infrastructure probes.
