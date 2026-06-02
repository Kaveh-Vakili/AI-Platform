"""Unit tests for the governance internals — fast, no fixtures needed."""
from decimal import Decimal

from app.monitoring.hallucination import check_output
from app.monitoring.token_logger import TokenLedger, estimate_cost
from app.agents.base import RetrievedChunk
from tests.fakes import _cosine, _embed


def test_estimate_cost_known_model():
    # 1M input + 1M output on sonnet pricing (3 + 15) / per-1M
    cost = estimate_cost("claude-sonnet-4-20250514", 1_000_000, 1_000_000)
    assert cost == Decimal("18.000000")


def test_unknown_model_uses_expensive_fallback():
    known = estimate_cost("claude-sonnet-4-20250514", 1000, 1000)
    unknown = estimate_cost("some-future-model", 1000, 1000)
    assert unknown > known  # never under-report cost


def test_ledger_accumulates():
    led = TokenLedger()
    led.add("claude-sonnet-4-20250514", 100, 50)
    led.add("claude-sonnet-4-20250514", 200, 80)
    assert led.prompt_tokens == 300
    assert led.completion_tokens == 130
    assert led.total_tokens == 430
    assert led.cost > 0


def _chunks():
    return [
        RetrievedChunk("chunk_1", "Revenue grew strongly on demand across regions.", 0.8, {}),
        RetrievedChunk("chunk_2", "A competitor may enter the market next year.", 0.7, {}),
    ]


def test_grounded_output_scores_better_than_fabricated():
    grounded = ("Revenue grew strongly on demand across regions [chunk_1]. "
                "A competitor may enter the market next year [chunk_2].")
    fabricated = ("The company secretly acquired a bank in Zurich last week. "
                  "Profits are guaranteed to double by Friday.")

    g = check_output(grounded, _chunks(), embed=_embed, cosine=_cosine)
    f = check_output(fabricated, _chunks(), embed=_embed, cosine=_cosine)

    assert g.source_alignment_score > f.source_alignment_score
    assert f.risk_level == "high"
    assert len(f.unsupported_claims) >= 1


def test_missing_citations_flagged():
    no_cites = "Revenue grew strongly on demand across regions and margins improved."
    v = check_output(no_cites, _chunks(), embed=_embed, cosine=_cosine)
    # supported-but-uncited claims show up in missing_citations
    assert isinstance(v.missing_citations, list)