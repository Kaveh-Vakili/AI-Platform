"""Workspace endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.main import get_db
from app.models import User, Workspace

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceIn(BaseModel):
    name: str
    description: str = ""


class WorkspaceOut(BaseModel):
    id: str
    name: str
    description: str | None


@router.post("", response_model=WorkspaceOut, status_code=201)
def create_workspace(
    body: WorkspaceIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = Workspace(user_id=current_user.id, name=body.name,
                   description=body.description)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return WorkspaceOut(id=str(ws.id), name=ws.name, description=ws.description)


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces = db.query(Workspace).filter(
        Workspace.user_id == current_user.id).all()
    return [WorkspaceOut(id=str(w.id), name=w.name, description=w.description)
            for w in workspaces]
