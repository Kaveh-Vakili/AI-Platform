"""Agent registry. The single source of truth for which agents exist.

Agents register themselves by `agent_type` at import time. The workflow engine
resolves the class for each step from here, then instantiates it with the shared
llm client + tool layer.
"""
from __future__ import annotations

from typing import Type

from app.agents.base import BaseAgent

_REGISTRY: dict[str, Type[BaseAgent]] = {}


def register_agent(cls: Type[BaseAgent]) -> Type[BaseAgent]:
    if not cls.agent_type or cls.agent_type == "base":
        raise ValueError(f"{cls.__name__} must define a unique agent_type")
    if cls.agent_type in _REGISTRY:
        raise ValueError(f"agent_type '{cls.agent_type}' already registered")
    _REGISTRY[cls.agent_type] = cls
    return cls


def get_agent_class(agent_type: str) -> Type[BaseAgent]:
    if agent_type not in _REGISTRY:
        raise KeyError(f"no agent registered for type '{agent_type}'")
    return _REGISTRY[agent_type]


def all_agents() -> dict[str, Type[BaseAgent]]:
    return dict(_REGISTRY)


def build_agent(agent_type: str, llm_client, tools) -> BaseAgent:
    return get_agent_class(agent_type)(llm_client, tools)