"""Chat endpoint and chunk embedding trigger."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.main import SessionLocal, get_db
from app.models import Document, User, Workspace
from app.rag.pipeline import embed_document_chunks, rag_answer, rag_answer_stream

router = APIRouter(tags=["chat"])


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    answer: str
    citations: list[dict]
    tokens_used: int = 0


class EmbedOut(BaseModel):
    chunks_embedded: int


@router.post("/workspaces/{workspace_id}/embed", response_model=EmbedOut)
def embed_workspace_documents(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Embed all un-embedded chunks in a workspace."""
    docs = db.query(Document).filter(
        Document.workspace_id == workspace_id,
        Document.status == "ready",
    ).all()

    total = 0
    for doc in docs:
        total += embed_document_chunks(str(doc.id), db)

    return EmbedOut(chunks_embedded=total)


@router.post("/workspaces/{workspace_id}/chat/stream")
def chat_stream(
    workspace_id: str,
    body: ChatIn,
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)

    def generate():
        db = SessionLocal()
        try:
            ws = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.user_id == user_id,
            ).first()
            if not ws:
                import json
                yield f'data: {json.dumps({"type": "done", "citations": [], "tokens_used": 0})}\n\n'
                return
            yield from rag_answer_stream(body.message, workspace_id, db)
        finally:
            db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/workspaces/{workspace_id}/chat", response_model=ChatOut)
def chat(
    workspace_id: str,
    body: ChatIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id,
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    result = rag_answer(body.message, workspace_id, db)
    return ChatOut(**result)