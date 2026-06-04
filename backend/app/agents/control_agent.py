"""Token & Hallucination Control Agent — the governance layer.

Runs in two modes:
  - phase="pre"  : before generation. Checks retrieval quality, context size, and
                   token budget; recommends pruning/summarization.
  - phase="post" : after generation. Aligns the output's claims to sources, scores
                   alignment, classifies risk, and proposes a grounded rewrite.

Writes token + hallucination records to the audit trail via the persistence hook.
"""
from __future__ import annotations

from app.agents.base import AgentResult, BaseAgent
from app.agents.registry import register_agent
from app.monitoring import persistence
from app.monitoring.hallucination import check_output
from app.monitoring.token_logger import estimate_cost

SONNET = "claude-haiku-4-5-20251001"

MAX_CONTEXT_TOKENS = 60_000
MAX_CHUNK_TOKENS = 1_200
MIN_COVERAGE = 0.30


@register_agent
class TokenHallucinationControlAgent(BaseAgent):
    agent_type = "token_hallucination_control"
    description = "Governs token cost and grounding before and after generation."
    allowed_tools = ["vector_search", "embed", "cosine"]

    def run(self, ctx) -> AgentResult:
        phase = ctx.input_payload.get("control_phase", "post")
        return self._pre(ctx) if phase == "pre" else self._post(ctx)

    def _pre(self, ctx) -> AgentResult:
        chunks = ctx.chunks
        context_tokens = sum((len(c.content) // 4) for c in chunks)
        oversized = [c.chunk_id for c in chunks
                     if (len(c.content) // 4) > MAX_CHUNK_TOKENS]
        coverage = (sum(c.score for c in chunks) / len(chunks)) if chunks else 0.0

        warnings, recommendations = [], []
        if context_tokens > MAX_CONTEXT_TOKENS:
            warnings.append(f"context {context_tokens} tok exceeds budget "
                            f"{MAX_CONTEXT_TOKENS}")
            recommendations.append("summarize or prune lowest-scoring chunks")
        if oversized:
            recommendations.append(f"split oversized chunks: {oversized}")
        if coverage < MIN_COVERAGE:
            warnings.append(f"low retrieval coverage {coverage:.2f}")

        projected = estimate_cost(SONNET, context_tokens, 1500)
        risk = "high" if (coverage < MIN_COVERAGE or context_tokens > MAX_CONTEXT_TOKENS) \
            else "medium" if warnings else "low"
        out = {
            "phase": "pre",
            "context_tokens": context_tokens,
            "projected_cost": str(projected),
            "coverage": round(coverage, 3),
            "warnings": warnings,
            "recommendations": recommendations,
        }
        ctx.put(self.agent_type + ":pre", out)
        return AgentResult(output=out, hallucination_risk=risk)

    def _post(self, ctx) -> AgentResult:
        briefing = ctx.get("executive_briefing", {}).get("briefing_markdown", "")
        if not briefing:
            return AgentResult(output={"phase": "post", "error": "no output to check"},
                               hallucination_risk="high")

        embed = self.tool("embed")
        cosine = self.tool("cosine")
        verdict = check_output(
            briefing, ctx.chunks, embed=embed, cosine=cosine,
            build_rewrite=self._rewrite_fn(ctx),
        )

        if persistence.write_hallucination_check is not None:
            persistence.write_hallucination_check(
                workflow_run_id=ctx.run_id,
                agent_execution_id=ctx.current_execution_id,
                output_id=ctx.input_payload.get("output_id"),
                risk_level=verdict.risk_level,
                unsupported_claims=verdict.unsupported_claims,
                missing_citations=verdict.missing_citations,
                source_alignment_score=verdict.source_alignment_score,
                recommended_rewrite=verdict.recommended_rewrite,
            )

        out = {
            "phase": "post",
            "risk_level": verdict.risk_level,
            "source_alignment_score": verdict.source_alignment_score,
            "unsupported_claims": verdict.unsupported_claims,
            "missing_citations": verdict.missing_citations,
            "recommended_rewrite": verdict.recommended_rewrite,
            "ledger": {
                "total_tokens": ctx.ledger.total_tokens,
                "cost": str(ctx.ledger.cost),
            },
        }
        ctx.put(self.agent_type + ":post", out)
        return AgentResult(output=out, hallucination_risk=verdict.risk_level)

    def _rewrite_fn(self, ctx):
        def build(original: str, supported_claims: list[str]) -> str:
            sources = "\n\n".join(f"[{c.chunk_id}] {c.content}" for c in ctx.chunks)
            return self.llm(
                ctx, model=SONNET,
                system=("Rewrite the briefing using ONLY the provided sources. Drop or "
                        "soften any claim not grounded in them. Keep [chunk_id] tags."),
                messages=[{"role": "user",
                           "content": f"Sources:\n{sources}\n\nOriginal:\n{original}"}],
            )
        return build