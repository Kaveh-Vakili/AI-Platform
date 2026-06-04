"""Output history and audit log endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.main import get_db
from app.models import AuditLog, GeneratedOutput, User

router = APIRouter(tags=["outputs"])

class OutputOut(BaseModel):
    id: str
    output_type: str | None
    title: str | None
    hallucination_risk: str | None
    source_alignment_score: float | None
    created_at: str

class AuditOut(BaseModel):
    id: str
    action: str
    entity_type: str | None
    details: dict
    created_at: str

@router.get("/workspaces/{workspace_id}/outputs", response_model=list[OutputOut])
def list_outputs(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    outputs = db.query(GeneratedOutput).filter(GeneratedOutput.workspace_id == workspace_id).order_by(GeneratedOutput.created_at.desc()).all()
    return [OutputOut(id=str(o.id), output_type=o.output_type, title=o.title, hallucination_risk=o.hallucination_risk, source_alignment_score=float(o.source_alignment_score) if o.source_alignment_score else None, created_at=str(o.created_at)) for o in outputs]

@router.get("/outputs/{output_id}", response_model=OutputOut)
def get_output(output_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = db.query(GeneratedOutput).filter(GeneratedOutput.id == output_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Output not found")
    return OutputOut(id=str(o.id), output_type=o.output_type, title=o.title, hallucination_risk=o.hallucination_risk, source_alignment_score=float(o.source_alignment_score) if o.source_alignment_score else None, created_at=str(o.created_at))

@router.get("/workspaces/{workspace_id}/audit-logs", response_model=list[AuditOut])
def list_audit_logs(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(AuditLog).filter(AuditLog.workspace_id == workspace_id).order_by(AuditLog.created_at.desc()).all()
    return [AuditOut(id=str(l.id), action=l.action, entity_type=l.entity_type, details=l.details or {}, created_at=str(l.created_at)) for l in logs]