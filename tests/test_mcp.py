"""MCP/browse toolset — fetch tool, per-role tool resolution. Offline (loader stubbed)."""

import http.server
import threading

import pytest
from langchain_core.tools import tool

from squad.tools import mcp


@pytest.fixture
def local_http(tmp_path):
    (tmp_path / "page.html").write_text("<html>LangGraph 1.2.9 release notes</html>")
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(tmp_path), **kw)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def test_fetch_returns_page_text(local_http):
    out = mcp.fetch.invoke({"url": f"{local_http}/page.html"})
    assert "LangGraph 1.2.9" in out


def test_fetch_truncates(local_http, tmp_path):
    (tmp_path / "big.txt").write_text("x" * 100_000)
    out = mcp.fetch.invoke({"url": f"{local_http}/big.txt", "max_bytes": 500})
    assert len(out) < 1000


def test_fetch_error_is_agent_visible():
    out = mcp.fetch.invoke({"url": "http://127.0.0.1:1/nope"})
    assert "fetch failed" in out.lower()  # returns, never raises


@tool
def fake_browser(action: str) -> str:
    """stub"""
    return "ok"


def test_tools_for_role_browse_and_named_servers(monkeypatch):
    calls = []

    def fake_loader(servers):
        calls.append(servers)
        return [fake_browser]

    monkeypatch.setattr(mcp, "load_mcp_tools", fake_loader)
    user_servers = {"github": {"command": "x"}, "linear": {"command": "y"}}

    got = mcp.tools_for_role(["browse", "github"], user_servers)
    names = {t.name for t in got}
    assert "fetch" in names and "fake_browser" in names
    assert calls[0] == mcp.BROWSE_SERVERS          # browse → playwright MCP
    assert calls[1] == {"github": {"command": "x"}}  # only the named server, not linear

    assert mcp.tools_for_role(["shell", "fs"], user_servers) == []  # no browse, no mcp names
