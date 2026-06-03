"""Document parsing and chunking service."""
from __future__ import annotations

import pathlib
import uuid

import tiktoken
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk

UPLOAD_DIR = pathlib.Path("uploads")
CHUNK_SIZE = 400       # tokens per chunk
CHUNK_OVERLAP = 50     # token overlap between chunks
ENCODING = "cl100k_base"  # works for claude + gpt-4


def _tokenize(text: str) -> list[int]:
    enc = tiktoken.get_encoding(ENCODING)
    return enc.encode(text)


def _decode(tokens: list[int]) -> str:
    enc = tiktoken.get_encoding(ENCODING)
    return enc.decode(tokens)


def save_upload(file_bytes: bytes, filename: str) -> pathlib.Path:
    UPLOAD_DIR.mkdir(exist_ok=True)
    unique_name = f"{uuid.uuid4()}_{filename}"
    path = UPLOAD_DIR / unique_name
    path.write_bytes(file_bytes)
    return path


def extract_text(path: pathlib.Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def chunk_text(text: str) -> list[dict]:
    tokens = _tokenize(text)
    chunks = []
    start = 0
    index = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append({
            "chunk_index": index,
            "content": _decode(chunk_tokens),
            "token_count": len(chunk_tokens),
        })
        start += CHUNK_SIZE - CHUNK_OVERLAP
        index += 1
    return chunks


def parse_and_chunk(document_id: str, path: pathlib.Path, db: Session) -> int:
    """Extract text, chunk it, write chunks to DB. Returns chunk count."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return 0

    doc.status = "parsing"
    db.commit()

    try:
        text = extract_text(path)
        chunks = chunk_text(text)
        for chunk in chunks:
            db.add(DocumentChunk(
                document_id=document_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                token_count=chunk["token_count"],
            ))
        doc.status = "ready"
        db.commit()
        return len(chunks)
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise e
