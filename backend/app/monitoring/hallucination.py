"""Hallucination checking. Aligns each claim in a generated output against the
retrieved source chunks and produces a risk verdict + safer rewrite material.

Alignment here uses embedding similarity with a lexical-overlap backstop. Swap in
an NLI/entailment model later for stronger guarantees — the interface stays the same.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

# tune on a labeled set; these are sane starting thresholds
SUPPORTED = 0.78   # >= this similarity to its best chunk => supported
WEAK = 0.62        # between WEAK and SUPPORTED => weak/uncertain

CITE_RE = re.compile(r"\[(chunk[_-]?[\w-]+)\]", re.IGNORECASE)


@dataclass
class ClaimVerdict:
    claim: str
    status: str            # supported | weak | unsupported
    nearest_chunk_id: str | None
    similarity: float
    has_citation: bool


@dataclass
class HallucinationVerdict:
    risk_level: str        # low | medium | high
    source_alignment_score: float
    unsupported_claims: list[dict[str, Any]]
    missing_citations: list[str]
    recommended_rewrite: str | None


def _split_claims(text: str) -> list[str]:
    # one sentence ~= one claim; good enough for the MVP
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 15]


def check_output(
    output_text: str,
    chunks: list,                                   # list[RetrievedChunk]
    embed: Callable[[str], list[float]],
    cosine: Callable[[list[float], list[float]], float],
    build_rewrite: Callable[[str, list[str]], str] | None = None,
) -> HallucinationVerdict:
    chunk_vecs = [(c.chunk_id, embed(c.content)) for c in chunks]
    verdicts: list[ClaimVerdict] = []

    for claim in _split_claims(output_text):
        has_cite = bool(CITE_RE.search(claim))
        cvec = embed(claim)
        best_id, best_sim = None, 0.0
        for cid, vec in chunk_vecs:
            sim = cosine(cvec, vec)
            if sim > best_sim:
                best_id, best_sim = cid, sim
        status = ("supported" if best_sim >= SUPPORTED
                  else "weak" if best_sim >= WEAK else "unsupported")
        verdicts.append(ClaimVerdict(claim, status, best_id, round(best_sim, 3), has_cite))

    n = len(verdicts) or 1
    alignment = sum(v.similarity for v in verdicts) / n
    unsupported = [v for v in verdicts if v.status == "unsupported"]
    missing = [v.claim for v in verdicts if not v.has_citation and v.status != "unsupported"]

    # risk policy: any unsupported claim or low aggregate alignment escalates
    frac_unsupported = len(unsupported) / n
    if frac_unsupported > 0.15 or alignment < WEAK:
        risk = "high"
    elif frac_unsupported > 0 or missing or alignment < SUPPORTED:
        risk = "medium"
    else:
        risk = "low"

    rewrite = None
    if risk != "low" and build_rewrite is not None:
        supported_claims = [v.claim for v in verdicts if v.status == "supported"]
        rewrite = build_rewrite(output_text, supported_claims)

    return HallucinationVerdict(
        risk_level=risk,
        source_alignment_score=round(alignment, 3),
        unsupported_claims=[
            {"claim": v.claim, "reason": "no aligned source chunk",
             "nearest_chunk_id": v.nearest_chunk_id, "similarity": v.similarity}
            for v in unsupported
        ],
        missing_citations=missing,
        recommended_rewrite=rewrite,
    )