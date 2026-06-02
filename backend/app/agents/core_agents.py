"""Two core agents. Research retrieves grounded chunks; Briefing synthesizes a
structured, source-tagged briefing using ONLY those chunks.
"""
from __future__ import annotations

from app.agents.base import AgentResult, BaseAgent, RetrievedChunk
from app.agents.registry import register_agent

SONNET = "claude-sonnet-4-20250514"


@register_agent
class DocumentResearchAgent(BaseAgent):
    agent_type = "document_research"
    description = "Retrieves the most relevant grounded chunks for the user's intent."
    allowed_tools = ["vector_search"]

    def run(self, ctx) -> AgentResult:
        intent = ctx.input_payload.get("focus") or ctx.input_payload.get("query", "")
        top_k = ctx.input_payload.get("top_k", 8)
        hits = self.tool("vector_search")(
            workspace_id=ctx.workspace_id, query=intent, top_k=top_k,
        )
        chunks = [
            RetrievedChunk(chunk_id=h["chunk_id"], content=h["content"],
                           score=h["score"], source=h.get("source", {}))
            for h in hits
        ]
        ctx.chunks = chunks
        coverage = sum(c.score for c in chunks) / (len(chunks) or 1)
        out = {
            "chunk_ids": [c.chunk_id for c in chunks],
            "coverage": round(coverage, 3),
            "count": len(chunks),
        }
        ctx.put(self.agent_type, out)
        return AgentResult(output=out)


@register_agent
class ExecutiveBriefingAgent(BaseAgent):
    agent_type = "executive_briefing"
    description = "Synthesizes a structured briefing strictly from retrieved chunks."
    allowed_tools = []  # generation only — keeps grounding auditable

    SYSTEM = (
        "You are an executive briefing analyst. Use ONLY the provided source chunks. "
        "Every claim MUST end with its source tag like [chunk_id]. If a statement is "
        "not supported by the sources, write it and mark it [UNSUPPORTED] rather than "
        "inventing support. Produce: Executive summary, Key risks, Opportunities, "
        "Open questions, Recommended actions."
    )

    def run(self, ctx) -> AgentResult:
        if not ctx.chunks:
            return AgentResult(output={"error": "no retrieved chunks"},
                               hallucination_risk="high")
        sources = "\n\n".join(
            f"[{c.chunk_id}] {c.content}" for c in ctx.chunks
        )
        focus = ctx.input_payload.get("focus", "Create an executive briefing.")
        text = self.llm(
            ctx, model=SONNET, system=self.SYSTEM,
            messages=[{"role": "user",
                       "content": f"Sources:\n{sources}\n\nTask: {focus}"}],
        )
        out = {"briefing_markdown": text}
        ctx.put(self.agent_type, out)
        return AgentResult(output=out)