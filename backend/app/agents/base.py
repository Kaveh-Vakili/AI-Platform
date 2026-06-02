"""Agent base class + the shared run context that threads state between steps.

Agents never call each other directly. They read from / write to RunContext.
Every LLM call goes through `self.llm(...)` so token usage is always logged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.monitoring.token_logger import TokenLedger, log_llm_call


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    source: dict[str, Any]


@dataclass
class RunContext:
    """Shared, mutable state for a single workflow run."""
    run_id: str
    workspace_id: str
    user_id: str
    input_payload: dict[str, Any]
    artifacts: dict[str, Any] = field(default_factory=dict)
    chunks: list[RetrievedChunk] = field(default_factory=list)
    ledger: TokenLedger = field(default_factory=TokenLedger)
    current_execution_id: str | None = None

    def put(self, agent_type: str, value: Any) -> None:
        self.artifacts[agent_type] = value

    def get(self, agent_type: str, default: Any = None) -> Any:
        return self.artifacts.get(agent_type, default)


@dataclass
class AgentResult:
    output: dict[str, Any]
    hallucination_risk: str | None = None


class BaseAgent:
    """Subclass and implement `run`. Register with @register_agent."""

    agent_type: str = "base"
    description: str = ""
    allowed_tools: list[str] = []

    def __init__(self, llm_client, tools: dict[str, Any]):
        self._llm = llm_client
        self._tools = tools

    def llm(self, ctx: RunContext, *, model: str, system: str,
            messages: list[dict]) -> str:
        resp = self._llm.messages.create(
            model=model, max_tokens=2048, system=system, messages=messages,
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        log_llm_call(
            ctx,
            model=model,
            prompt_tokens=resp.usage.input_tokens,
            completion_tokens=resp.usage.output_tokens,
        )
        return text

    def tool(self, name: str):
        if name not in self.allowed_tools:
            raise PermissionError(f"{self.agent_type} may not call tool '{name}'")
        return self._tools[name]

    def run(self, ctx: RunContext) -> AgentResult:  # pragma: no cover - abstract
        raise NotImplementedError