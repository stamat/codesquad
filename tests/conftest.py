"""Suite-wide policy: offline. MCP loading spawns real server processes (npx
Playwright etc.) — stub it everywhere; tests that care monkeypatch their own."""

import pytest

from squad.tools import mcp


@pytest.fixture(autouse=True)
def no_real_mcp_servers(monkeypatch):
    monkeypatch.setattr(mcp, "load_mcp_tools", lambda servers: [])
