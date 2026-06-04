"""Real tool layer for the agent harness."""
from __future__ import annotations

import math
from sqlalchemy.orm import Session
from app.rag.retrieval import retrieve_chunks
from app.rag.embeddings import embed_text


def make_tools(db: Session, workspace_id: str) -> dict:
    def vector_search(*, workspace_id=workspace_id, query: str, top_k: int = 6):
        return retrieve_chunks(query, workspace_id, db, top_k=top_k)

    def embed(text: str) -> list[float]:
        return embed_text(text)

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    return {
        "vector_search": vector_search,
        "embed": embed,
        "cosine": cosine,
    }
