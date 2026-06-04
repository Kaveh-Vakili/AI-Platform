"""Monitoring endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.main import get_db
from app.models import HallucinationCheck, TokenUsageLog, User, WorkflowRun

router = APIRouter(prefix="/workflow-runs", tags=["monitoring"])

class TokenLogOut(BaseModel):
    id: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: str

class CostSummaryOut(BaseModel):
    run_id: str
    total_tokens: int
    total_cost: str
    call_count: int

class HallucinationOut(BaseModel):
    id: str
    risk_level: str
    source_alignment_score: float | None
    unsupported_claims: list
    missing_citations: list
    recommended_rewrite: str | None

def _get_run(run_id, db):
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/{run_id}/token-usage", response_model=list[TokenLogOut])
def get_token_usage(run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_run(run_id, db)
    logs = db.query(TokenUsageLog).filter(TokenUsageLog.workflow_run_id == run_id).order_by(TokenUsageLog.created_at).all()
    return [TokenLogOut(id=str(l.id), model_name=l.model_name, prompt_tokens=l.prompt_tokens or 0, completion_tokens=l.completion_tokens or 0, total_tokens=l.total_tokens or 0, estimated_cost=str(l.estimated_cost)) for l in logs]

@router.get("/{run_id}/cost-summary", response_model=CostSummaryOut)
def get_cost_summary(run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_run(run_id, db)
    r = db.query(func.sum(TokenUsageLog.total_tokens).label("total"), func.sum(TokenUsageLog.estimated_cost).label("cost"), func.count(TokenUsageLog.id).label("calls")).filter(TokenUsageLog.workflow_run_id == run_id).first()
    return CostSummaryOut(run_id=run_id, total_tokens=r.total or 0, total_cost=str(round(r.cost or 0, 6)), call_count=r.calls or 0)

@router.get("/{run_id}/hallucination-checks", response_model=list[HallucinationOut])
def get_hallucination_checks(run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_run(run_id, db)
    checks = db.query(HallucinationCheck).filter(HallucinationCheck.workflow_run_id == run_id).all()
    return [HallucinationOut(id=str(c.id), risk_level=c.risk_level, source_alignment_score=float(c.source_alignment_score) if c.source_alignment_score else None, unsupported_claims=c.unsupported_claims or [], missing_citations=c.missing_citations or [], recommended_rewrite=c.recommended_rewrite) for c in checks]