"""SQLAlchemy models for STRATOS AI.

Relational core in Postgres; chunk embeddings stored via pgvector. The two
monitoring tables (token_usage_logs, hallucination_checks) hang off both
workflow_runs (for run-level rollups) and agent_executions (for per-agent
attribution).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, Numeric,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship

# from pgvector.sqlalchemy import Vector  # enable when pgvector is installed


def _pk():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _ts():
    return Column(DateTime(timezone=True), server_default=func.now())


class Base(DeclarativeBase):
    pass


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    awaiting_approval = "awaiting_approval"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"
    id = _pk()
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="member", nullable=False)
    created_at = _ts()
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Workspace(Base):
    __tablename__ = "workspaces"
    id = _pk()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = _ts()
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Document(Base):
    __tablename__ = "documents"
    id = _pk()
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String, nullable=False)
    file_type = Column(String)
    file_size = Column(Integer)
    storage_url = Column(String)
    status = Column(String, default="uploaded")  # uploaded|parsing|ready|failed
    created_at = _ts()
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    chunks = relationship("DocumentChunk", back_populates="document",
                          cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = _pk()
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # embedding = Column(Vector(1536))  # pgvector column
    embedding_id = Column(String)       # or external index id
    token_count = Column(Integer)
    meta = Column("metadata", JSONB, default=dict)
    created_at = _ts()
    document = relationship("Document", back_populates="chunks")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = _pk()
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String)
    created_at = _ts()
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = _pk()
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    sender = Column(String)  # user|assistant
    message = Column(Text)
    citations = Column(JSONB, default=list)
    token_count = Column(Integer)
    created_at = _ts()


class Agent(Base):
    __tablename__ = "agents"
    id = _pk()
    name = Column(String, nullable=False)
    description = Column(Text)
    agent_type = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = _ts()


class AgentTool(Base):
    __tablename__ = "agent_tools"
    id = _pk()
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    tool_name = Column(String, nullable=False)
    tool_description = Column(Text)
    config = Column(JSONB, default=dict)
    created_at = _ts()


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"
    id = _pk()
    name = Column(String, nullable=False)
    description = Column(Text)
    steps = Column(JSONB, nullable=False)          # ordered list of step defs
    required_agents = Column(JSONB, default=list)  # agent_types used
    created_at = _ts()
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id = _pk()
    workflow_template_id = Column(UUID(as_uuid=True), ForeignKey("workflow_templates.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(Enum(RunStatus), default=RunStatus.pending, nullable=False)
    input_payload = Column(JSONB, default=dict)
    final_output_id = Column(UUID(as_uuid=True), ForeignKey("generated_outputs.id"),
                             nullable=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = _ts()


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    id = _pk()
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"),
                             nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    status = Column(Enum(RunStatus), default=RunStatus.pending)
    input_payload = Column(JSONB, default=dict)
    output_payload = Column(JSONB, default=dict)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    id = _pk()
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"),
                             nullable=False, index=True)
    workflow_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id"))
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    input_payload = Column(JSONB, default=dict)
    output_payload = Column(JSONB, default=dict)
    status = Column(Enum(RunStatus), default=RunStatus.pending)
    token_usage = Column(Integer, default=0)               # denormalized fast total
    hallucination_risk = Column(Enum(RiskLevel), nullable=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)


class GeneratedOutput(Base):
    __tablename__ = "generated_outputs"
    id = _pk()
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    output_type = Column(String)  # briefing|risk_review|investor_memo
    title = Column(String)
    content = Column(JSONB)
    citations = Column(JSONB, default=list)
    hallucination_risk = Column(Enum(RiskLevel), nullable=True)
    source_alignment_score = Column(Float)
    created_at = _ts()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = _pk()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"),
                             nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(String)
    details = Column(JSONB, default=dict)
    created_at = _ts()


# ----- Monitoring tables -----

class TokenUsageLog(Base):
    """One row per LLM call. SUM over workflow_run_id drives the cost summary."""
    __tablename__ = "token_usage_logs"
    id = _pk()
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"),
                             nullable=False, index=True)
    agent_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_executions.id"),
                                index=True)
    model_name = Column(String, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Numeric(10, 6), default=0)
    created_at = _ts()


class HallucinationCheck(Base):
    """One row per output review — the Control Agent's verdict on an artifact."""
    __tablename__ = "hallucination_checks"
    id = _pk()
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"),
                             nullable=False, index=True)
    agent_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_executions.id"))
    output_id = Column(UUID(as_uuid=True), ForeignKey("generated_outputs.id"))
    risk_level = Column(Enum(RiskLevel), nullable=False)
    unsupported_claims = Column(JSONB, default=list)
    missing_citations = Column(JSONB, default=list)
    source_alignment_score = Column(Numeric(4, 3))
    recommended_rewrite = Column(Text)
    created_at = _ts()