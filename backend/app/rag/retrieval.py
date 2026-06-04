"""Vector retrieval using pgvector."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.rag.embeddings import embed_text


def retrieve_chunks(
    query: str,
    workspace_id: str,
    db: Session,
    top_k: int = 6,
) -> list[dict]:
    """Embed the query and return the top_k most similar chunks."""
    query_vec = embed_text(query)
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    sql = text(f"""
        SELECT
            dc.id,
            dc.chunk_index,
            dc.content,
            dc.token_count,
            d.filename,
            1 - (dc.embedding <=> '{vec_str}'::vector) AS score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.workspace_id = :workspace_id
          AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> '{vec_str}'::vector
        LIMIT :top_k
    """)

    rows = db.execute(sql, {
        "workspace_id": workspace_id,
        "top_k": top_k,
    }).fetchall()

    return [
        {
            "chunk_id": str(row.id),
            "content": row.content,
            "score": float(row.score),
            "source": {"filename": row.filename, "chunk_index": row.chunk_index},
        }
        for row in rows
    ]
