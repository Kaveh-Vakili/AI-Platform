"""Token monitoring. Every LLM call records a token_usage_logs row and updates
the run's in-memory ledger so the Control Agent can enforce budgets live.

Prices are per 1M tokens (USD). Update from the provider's current pricing page;
treat unknown models as the most expensive tier so cost is never under-reported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

# (input_price, output_price) per 1,000,000 tokens
MODEL_PRICES: dict[str, tuple[Decimal, Decimal]] = {
    "claude-sonnet-4-20250514": (Decimal("3.00"), Decimal("15.00")),
    "claude-haiku-4-5-20251001": (Decimal("1.00"), Decimal("5.00")),
}
_FALLBACK_PRICE = (Decimal("15.00"), Decimal("75.00"))


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    in_price, out_price = MODEL_PRICES.get(model, _FALLBACK_PRICE)
    cost = (Decimal(prompt_tokens) * in_price
            + Decimal(completion_tokens) * out_price) / Decimal(1_000_000)
    return cost.quantize(Decimal("0.000001"))


@dataclass
class TokenLedger:
    """Per-run running total kept in the RunContext."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: Decimal = field(default_factory=lambda: Decimal("0"))

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, model: str, prompt: int, completion: int) -> Decimal:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        c = estimate_cost(model, prompt, completion)
        self.cost += c
        return c


def log_llm_call(ctx, *, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Update the ledger and persist a token_usage_logs row.

    `ctx` is the RunContext (imported lazily to avoid a circular import). The DB
    write is delegated to the persistence layer wired in at engine setup.
    """
    cost = ctx.ledger.add(model, prompt_tokens, completion_tokens)
    from app.monitoring import persistence
    if persistence.write_token_log is not None:
        persistence.write_token_log(
            workflow_run_id=ctx.run_id,
            agent_execution_id=ctx.current_execution_id,
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost=cost,
        )