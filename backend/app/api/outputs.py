"""Audit log endpoint — output history for a workspace."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.main import get_db
from app.models import AuditLog, User, Workspace

router = APIRouter(tags=["outputs"])


class AuditLogOut(BaseModel):
    id: str
    action: str
    entity_type: str | None
    details: Any
    created_at: str


@router.get("/workspaces/{workspace_id}/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
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

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        AuditLogOut(
            id=str(log.id),
            action=log.action,
            entity_type=log.entity_type,
            details=log.details,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]
