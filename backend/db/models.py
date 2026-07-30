from sqlalchemy import Column, Float, Integer, JSON, String
from .database import Base


class AuditLogModel(Base):
    """SQLAlchemy ORM model for storing Agent WAF security audit events in PostgreSQL (Neon)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=False, index=True)
    tool_name = Column(String, nullable=False, index=True)
    policy_result = Column(String, nullable=False, index=True)  # "ALLOW" or "BLOCK"
    risk_score = Column(Float, nullable=False, default=0.0)
    matched_rules = Column(JSON, nullable=False, default=list)
    violations = Column(JSON, nullable=False, default=list)
    trace_id = Column(String, nullable=True)
    graph_run_id = Column(String, nullable=True)
    execution_time_ms = Column(Float, nullable=False, default=0.0)
