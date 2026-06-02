"""Engine-level tests. These run the real Executive Briefing workflow end to end
against fakes — proving the harness wiring (registry -> engine -> context ->
monitoring) holds together without a database or a real model.
"""
import copy

from app.workflow.engine import WorkflowEngine
from app.workflow.templates import EXECUTIVE_BRIEFING
from tests.fakes import FakeRepo, fake_tools


def test_executive_briefing_completes(llm, tools, ctx, captured):
    repo = FakeRepo()
    engine = WorkflowEngine(llm, tools, repo)

    status = engine.run("run-1", EXECUTIVE_BRIEFING, ctx)

    assert status == "completed"
    assert repo.runs["run-1"]["status"] == "completed"
    # 4 steps in the template -> 4 step + 4 execution rows
    assert len(repo.steps) == 4
    assert len(repo.executions) == 4
    # research populated the shared context
    assert len(ctx.chunks) == 2
    # the briefing artifact made it into the context
    assert "briefing_markdown" in ctx.get("executive_briefing")
    # every LLM call was metered -> ledger advanced and token logs were written
    assert ctx.ledger.total_tokens > 0
    assert len(captured["token_logs"]) == len(llm.calls)
    # the control agent wrote exactly one hallucination check
    assert len(captured["halluc_checks"]) == 1
    assert captured["halluc_checks"][0]["risk_level"] in {"low", "medium", "high"}


def test_run_emits_audit_trail(llm, tools, ctx):
    repo = FakeRepo()
    WorkflowEngine(llm, tools, repo).run("run-1", EXECUTIVE_BRIEFING, ctx)
    actions = [a["action"] for a in repo.audits]
    assert actions[0] == "run_started"
    assert actions[-1] == "run_completed"
    assert actions.count("step_completed") == 4


def test_approval_gate_pauses_then_resumes(llm, tools, ctx, captured):
    template = copy.deepcopy(EXECUTIVE_BRIEFING)
    template["steps"][1]["requires_approval"] = True  # gate before the pre-control step
    repo = FakeRepo()
    engine = WorkflowEngine(llm, tools, repo)

    status = engine.run("run-1", template, ctx)
    assert status == "awaiting_approval"
    assert repo.runs["run-1"]["status"] == "awaiting_approval"
    assert repo.runs["run-1"]["resume_index"] == 1
    assert len(repo.steps) == 1  # only step 0 ran before the gate

    # user approves -> resume from the gated step
    ctx.input_payload["_approved_step_1"] = True
    status = engine.run("run-1", template, ctx, resume_from=1)
    assert status == "completed"
    assert len(repo.steps) == 4


def test_agent_failure_fails_run_and_keeps_partial_state(llm, ctx):
    repo = FakeRepo()
    engine = WorkflowEngine(llm, fake_tools(raise_on_search=True), repo)

    status = engine.run("run-1", EXECUTIVE_BRIEFING, ctx)

    assert status == "failed"
    assert repo.runs["run-1"]["status"] == "failed"
    assert repo.executions[0].error  # the failing execution captured the error
    assert any(a["action"] == "step_failed" for a in repo.audits)