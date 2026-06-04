"""Workflow run endpoints."""
from __future__ import annotations

import os
from datetime import datetime

import anthropic
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.main import SessionLocal, get_db
from app.models import AgentExecution, User, Workspace, WorkflowRun, WorkflowStep
from app.services.repo import WorkflowRepo
from app.services.tool_layer import make_tools
from app.workflow.engine import WorkflowEngine
from app.workflow.templates import EXECUTIVE_BRIEFING, INVESTOR_MEMO, RISK_REVIEW

router = APIRouter(prefix="/workflows", tags=["workflows"])

TEMPLATES = {
    "executive_briefing": EXECUTIVE_BRIEFING,
    "risk_review": RISK_REVIEW,
    "investor_memo": INVESTOR_MEMO,
}


class RunIn(BaseModel):
    template_id: str
    workspace_id: str
    focus: str = "Analyze the uploaded documents."


class RunOut(BaseModel):
    run_id: str
    status: str
    template: str


class StepOut(BaseModel):
    step_order: int
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    output_preview: str | None


class ExecutionOut(BaseModel):
    id: str
    status: str
    token_usage: int
    hallucination_risk: str | None
    started_at: datetime | None
    completed_at: datetime | None


def _run_workflow(run_id: str, template: dict, workspace_id: str,
                  user_id: str, focus: str):
    import app.agents.core_agents  # noqa
    import app.agents.control_agent  # noqa
    from app.agents.base import RunContext

    db = SessionLocal()
    try:
        repo = WorkflowRepo(db, user_id=user_id, workspace_id=workspace_id)
        llm = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        tools = make_tools(db, workspace_id)
        ctx = RunContext(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
            input_payload={"focus": focus},
        )
        engine = WorkflowEngine(llm, tools, repo)
        engine.run(run_id, template, ctx)
    finally:
        db.close()


@router.get("/templates")
def list_templates():
    return [{"id": k, "name": v["name"], "description": v["description"]}
            for k, v in TEMPLATES.items()]


@router.post("/run", response_model=RunOut, status_code=201)
def start_run(
    body: RunIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = TEMPLATES.get(body.template_id)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown template: {body.template_id}")

    ws = db.query(Workspace).filter(
        Workspace.id == body.workspace_id,
        Workspace.user_id == current_user.id,
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    run = WorkflowRun(
        workspace_id=body.workspace_id,
        user_id=current_user.id,
        status="pending",
        input_payload={"focus": body.focus},
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(
        _run_workflow, str(run.id), template,
        body.workspace_id, str(current_user.id), body.focus,
    )

    return RunOut(run_id=str(run.id), status="pending", template=template["name"])


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: str, db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)):
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunOut(run_id=str(run.id), status=run.status, template=run_id)


@router.get("/runs/{run_id}/steps", response_model=list[StepOut])
def get_steps(run_id: str, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    steps = db.query(WorkflowStep).filter(
        WorkflowStep.workflow_run_id == run_id
    ).order_by(WorkflowStep.step_order).all()
    return [
        StepOut(
            step_order=s.step_order,
            status=s.status,
            started_at=s.started_at,
            completed_at=s.completed_at,
            output_preview=str(s.output_payload)[:200] if s.output_payload else None,
        )
        for s in steps
    ]


@router.get("/runs/{run_id}/executions", response_model=list[ExecutionOut])
def get_executions(run_id: str, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    execs = db.query(AgentExecution).filter(
        AgentExecution.workflow_run_id == run_id
    ).all()
    return [
        ExecutionOut(
            id=str(e.id),
            status=e.status,
            token_usage=e.token_usage or 0,
            hallucination_risk=e.hallucination_risk,
            started_at=e.started_at,
            completed_at=e.completed_at,
        )
        for e in execs
    ]
