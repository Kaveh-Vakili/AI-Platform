"""Real SQLAlchemy repo facade."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import AgentExecution, AuditLog, WorkflowRun, WorkflowStep

class WorkflowRepo:
    def __init__(self, db: Session, user_id: str, workspace_id: str):
        self.db = db
        self.user_id = user_id
        self.workspace_id = workspace_id

    def set_run_status(self, run_id: str, status: str, **kw):
        run = self.db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if run:
            run.status = status
            for k, v in kw.items():
                if hasattr(run, k):
                    setattr(run, k, v)
            self.db.commit()

    def audit(self, run_id: str, *, action: str, details: dict = None):
        self.db.add(AuditLog(
            user_id=self.user_id,
            workspace_id=self.workspace_id,
            workflow_run_id=run_id,
            action=action,
            entity_type="workflow_run",
            entity_id=run_id,
            details=details or {},
        ))
        self.db.commit()

    def create_step(self, run_id: str, order: int, agent_type: str, **kw):
        step = WorkflowStep(
            workflow_run_id=run_id,
            step_order=order,
            input_payload=kw.get("input_payload", {}),
            status=kw.get("status", "running"),
            started_at=kw.get("started_at"),
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def create_execution(self, run_id: str, step_id, agent_type: str, **kw):
        exc = AgentExecution(
            workflow_run_id=run_id,
            workflow_step_id=step_id,
            input_payload=kw.get("input_payload", {}),
            status=kw.get("status", "running"),
            started_at=kw.get("started_at"),
        )
        self.db.add(exc)
        self.db.commit()
        self.db.refresh(exc)
        return exc

    def complete_step(self, step_id, *, output_payload: dict, completed_at: datetime):
        step = self.db.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
        if step:
            step.status = "completed"
            step.output_payload = output_payload
            step.completed_at = completed_at
            self.db.commit()

    def complete_execution(self, exec_id, *, output_payload: dict, token_usage: int,
                           hallucination_risk: str, completed_at: datetime):
        exc = self.db.query(AgentExecution).filter(AgentExecution.id == exec_id).first()
        if exc:
            exc.status = "completed"
            exc.output_payload = output_payload
            exc.token_usage = token_usage
            exc.hallucination_risk = hallucination_risk
            exc.completed_at = completed_at
            self.db.commit()

    def fail_step(self, step_id, msg: str, *, completed_at: datetime):
        step = self.db.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
        if step:
            step.status = "failed"
            step.error_message = msg
            step.completed_at = completed_at
            self.db.commit()

    def fail_execution(self, exec_id, msg: str, *, completed_at: datetime):
        exc = self.db.query(AgentExecution).filter(AgentExecution.id == exec_id).first()
        if exc:
            exc.status = "failed"
            exc.error_message = msg
            exc.completed_at = completed_at
            self.db.commit()
