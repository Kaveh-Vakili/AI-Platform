"""Embedding service using OpenAI text-embedding-3-small."""
from __future__ import annotations

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536


def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text.replace("\n", " "),
    )
    return response.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=[t.replace("\n", " ") for t in texts],
    )
    return [d.embedding for d in response.data]
