"""Document upload, list, delete endpoints."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.main import get_db
from app.models import Document, Workspace, User
from app.services.document_service import parse_and_chunk, save_upload

router = APIRouter(prefix="/workspaces", tags=["documents"])


class DocumentOut(BaseModel):
    id: str
    filename: str
    status: str
    file_size: int | None


@router.post("/{workspace_id}/documents", response_model=DocumentOut, status_code=201)
def upload_document(
    workspace_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id,
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    file_bytes = file.file.read()
    path = save_upload(file_bytes, file.filename)

    doc = Document(
        workspace_id=workspace_id,
        uploaded_by=current_user.id,
        filename=file.filename,
        file_type=file.content_type,
        file_size=len(file_bytes),
        storage_url=str(path),
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(parse_and_chunk, str(doc.id), path, db)

    return DocumentOut(id=str(doc.id), filename=doc.filename,
                       status=doc.status, file_size=doc.file_size)


@router.get("/{workspace_id}/documents", response_model=list[DocumentOut])
def list_documents(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id,
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    return [DocumentOut(id=str(d.id), filename=d.filename,
                        status=d.status, file_size=d.file_size) for d in docs]


@router.delete("/{workspace_id}/documents/{document_id}", status_code=204)
def delete_document(
    workspace_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.workspace_id == workspace_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
