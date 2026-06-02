"""In-memory test doubles. These let the whole harness run with no DB, no network.

The engine depends on an injected `repo` facade and a `tools` dict, and every LLM
call goes through BaseAgent.llm — so swapping these three is enough to exercise the
full workflow deterministically.
"""
from __future__ import annotations

import itertools
import math
import re
from types import SimpleNamespace


# ---- fake LLM client (mimics the Anthropic SDK response shape) ----

class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Usage:
    def __init__(self, i, o):
        self.input_tokens = i
        self.output_tokens = o


class _Resp:
    def __init__(self, text, i, o):
        self.content = [_Block(text)]
        self.usage = _Usage(i, o)


class _Messages:
    def __init__(self, parent):
        self._p = parent

    def create(self, *, model, max_tokens, system, messages):
        self._p.calls.append({"model": model, "system": system, "messages": messages})
        return _Resp(self._p.script, self._p.in_toks, self._p.out_toks)


class FakeLLM:
    def __init__(self, script="Summary: revenue grew on strong demand [chunk_1]. "
                              "A competitor may enter the market [chunk_2]. "
                              "The team plans to triple headcount next quarter.",
                 in_toks=120, out_toks=60):
        self.messages = _Messages(self)
        self.script = script
        self.in_toks = in_toks
        self.out_toks = out_toks
        self.calls: list[dict] = []


# ---- fake tool layer ----

def _embed(text: str) -> list[float]:
    vec = [0.0] * 64
    for w in re.findall(r"\w+", text.lower()):
        vec[sum(map(ord, w)) % 64] += 1.0
    return vec


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def fake_tools(raise_on_search=False):
    def vector_search(*, workspace_id, query, top_k):
        if raise_on_search:
            raise RuntimeError("vector store unavailable")
        return [
            {"chunk_id": "chunk_1", "score": 0.82,
             "content": "Revenue grew strongly on demand across all regions.",
             "source": {"doc": "q3.pdf", "page": 2}},
            {"chunk_id": "chunk_2", "score": 0.74,
             "content": "A new competitor may enter the market next year.",
             "source": {"doc": "market.pdf", "page": 5}},
        ][:top_k]

    return {"vector_search": vector_search, "embed": _embed, "cosine": _cosine}


# ---- in-memory repo facade (records every write the engine makes) ----

class FakeRepo:
    def __init__(self):
        self._ids = itertools.count(1)
        self.runs: dict = {}
        self.steps: list = []
        self.executions: list = []
        self.audits: list = []

    def _id(self):
        return next(self._ids)

    def set_run_status(self, run_id, status, **kw):
        self.runs[run_id] = {"status": status, **kw}

    def audit(self, run_id, *, action, details=None):
        self.audits.append({"run_id": run_id, "action": action, "details": details or {}})

    def create_step(self, run_id, order, agent_type, **kw):
        row = SimpleNamespace(id=self._id(), run_id=run_id, order=order,
                              agent_type=agent_type, **kw)
        self.steps.append(row)
        return row

    def create_execution(self, run_id, step_id, agent_type, **kw):
        row = SimpleNamespace(id=self._id(), run_id=run_id, step_id=step_id,
                              agent_type=agent_type, output=None, **kw)
        self.executions.append(row)
        return row

    def complete_step(self, step_id, *, output_payload, completed_at):
        next(s for s in self.steps if s.id == step_id).output_payload = output_payload

    def complete_execution(self, exec_id, *, output_payload, token_usage,
                           hallucination_risk, completed_at):
        e = next(x for x in self.executions if x.id == exec_id)
        e.output, e.token_usage, e.hallucination_risk = (
            output_payload, token_usage, hallucination_risk)

    def fail_step(self, step_id, msg, *, completed_at):
        next(s for s in self.steps if s.id == step_id).error = msg

    def fail_execution(self, exec_id, msg, *, completed_at):
        next(x for x in self.executions if x.id == exec_id).error = msg