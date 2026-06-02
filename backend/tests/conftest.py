"""Shared fixtures. The monitoring hooks are redirected into in-memory lists so we
can assert that token logs and hallucination checks actually get written.
"""
import pytest

from app.agents.base import RunContext
from app.monitoring import persistence
from tests.fakes import FakeLLM, FakeRepo, fake_tools

# ensure agents self-register
import app.agents.core_agents  # noqa: F401
import app.agents.control_agent  # noqa: F401


@pytest.fixture
def captured(monkeypatch):
    token_logs, halluc_checks = [], []
    monkeypatch.setattr(persistence, "write_token_log",
                        lambda **kw: token_logs.append(kw))
    monkeypatch.setattr(persistence, "write_hallucination_check",
                        lambda **kw: halluc_checks.append(kw))
    return {"token_logs": token_logs, "halluc_checks": halluc_checks}


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def tools():
    return fake_tools()


@pytest.fixture
def ctx():
    return RunContext(run_id="run-1", workspace_id="ws-1", user_id="u-1",
                      input_payload={"focus": "Create an executive briefing."})