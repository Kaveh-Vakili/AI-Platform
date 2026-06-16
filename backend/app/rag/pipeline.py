"""RAG pipeline: embed chunks after upload, answer questions."""
from __future__ import annotations

import json
import os
from collections.abc import Generator

import anthropic
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import DocumentChunk
from app.rag.embeddings import embed_batch
from app.rag.retrieval import retrieve_chunks

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
CHAT_MODEL = "claude-haiku-4-5-20251001"

SYSTEM = """You are a helpful analyst. Answer the user's question using ONLY
the provided source chunks. Tag every claim with its source like [chunk_id].
If the answer is not in the sources, say so — do not invent information."""


def embed_document_chunks(document_id: str, db: Session) -> int:
    """Embed all chunks for a document and store vectors. Returns count."""
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id,
        DocumentChunk.embedding_id == None,
    ).all()

    if not chunks:
        return 0

    texts = [c.content for c in chunks]
    vectors = embed_batch(texts)

    for chunk, vec in zip(chunks, vectors):
        vec_str = "[" + ",".join(str(v) for v in vec) + "]"
        chunk.embedding_id = "stored"
        db.execute(
            text("UPDATE document_chunks SET embedding = :vec WHERE id = :id"),
            {"vec": vec_str, "id": str(chunk.id)},
        )

    db.commit()
    return len(chunks)


def rag_answer(
    query: str,
    workspace_id: str,
    db: Session,
) -> dict:
    """Retrieve relevant chunks and generate a grounded answer."""
    chunks = retrieve_chunks(query, workspace_id, db)

    if not chunks:
        return {
            "answer": "No relevant documents found in this workspace.",
            "citations": [],
            "tokens_used": 0,
        }

    sources = "\n\n".join(
        f"[{c['chunk_id']}] {c['content']}" for c in chunks
    )

    response = claude.messages.create(
        model=CHAT_MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Sources:\n{sources}\n\nQuestion: {query}",
        }],
    )

    answer = response.content[0].text
    return {
        "answer": answer,
        "citations": [
            {"chunk_id": c["chunk_id"], "filename": c["source"]["filename"],
             "score": c["score"]}
            for c in chunks
        ],
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
    }


def rag_answer_stream(
    query: str,
    workspace_id: str,
    db: Session,
) -> Generator[str, None, None]:
    """Yield SSE-formatted strings for a streaming RAG answer."""
    chunks = retrieve_chunks(query, workspace_id, db)

    if not chunks:
        yield f'data: {json.dumps({"type": "done", "citations": [], "tokens_used": 0})}\n\n'
        return

    sources = "\n\n".join(f"[{c['chunk_id']}] {c['content']}" for c in chunks)
    citations = [
        {"chunk_id": c["chunk_id"], "filename": c["source"]["filename"], "score": c["score"]}
        for c in chunks
    ]

    with claude.messages.stream(
        model=CHAT_MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Sources:\n{sources}\n\nQuestion: {query}",
        }],
    ) as stream:
        for text_delta in stream.text_stream:
            yield f'data: {json.dumps({"type": "token", "text": text_delta})}\n\n'
        final = stream.get_final_message()
        tokens_used = final.usage.input_tokens + final.usage.output_tokens

    yield f'data: {json.dumps({"type": "done", "citations": citations, "tokens_used": tokens_used})}\n\n'