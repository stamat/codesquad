"""Agent construction — capability boundary: a tool not in the role's list is not bound."""

from pathlib import Path

import pytest

from squad.agents import build_agent
from squad.config import load_config

CONFIG = Path(__file__).parent.parent / "squad.yaml"


@pytest.fixture(scope="module")
def cfg():
    return load_config(CONFIG)


def bound_tools(agent) -> set[str]:
    """Names of tools actually bound into the compiled agent graph."""
    return {t.name for t in agent.nodes["tools"].bound._tools_by_name.values()}


def test_coder_gets_shell(cfg, tmp_path):
    agent = build_agent(cfg, "coder", tmp_path, lambda c: False)
    assert "shell" in bound_tools(agent)


@pytest.mark.parametrize("role", ["scout", "planner", "reviewer", "supervisor"])
def test_only_coder_gets_shell(cfg, tmp_path, role):
    # THE security property: no shell binding for browsing/reading roles.
    agent = build_agent(cfg, role, tmp_path, lambda c: False)
    assert "shell" not in bound_tools(agent)
