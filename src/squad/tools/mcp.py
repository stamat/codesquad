"""MCP client loader + plain fetch. `browse` = Playwright MCP + fetch, scout's toolset.
User servers from squad.yaml `mcp_servers` bind by name in a role's tools list."""

import asyncio
import urllib.request

from langchain_core.tools import StructuredTool, tool

BROWSE_SERVERS = {
    "playwright": {
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest", "--headless"],
        "transport": "stdio",
    }
}


@tool
def fetch(url: str, max_bytes: int = 40_000) -> str:
    """Fetch a URL and return its raw text content (truncated). For rendered
    pages or interaction, use the browser tools instead."""
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read(max_bytes + 1)
    except Exception as e:  # agent must see why, never crash the run
        return f"fetch failed: {e}"
    text = data[:max_bytes].decode("utf-8", "replace")
    return text + ("\n[truncated]" if len(data) > max_bytes else "")


def _sync_wrap(t: StructuredTool) -> StructuredTool:
    """MCP adapter tools are async-only; agents here run sync. Wrap each in a
    fresh event loop — tool calls execute in worker threads with no loop."""
    if t.func is not None:
        return t
    return StructuredTool(
        name=t.name, description=t.description, args_schema=t.args_schema,
        func=lambda _t=t, **kwargs: asyncio.run(_t.ainvoke(kwargs)),
    )


def load_mcp_tools(servers: dict) -> list:
    if not servers:
        return []
    from langchain_mcp_adapters.client import MultiServerMCPClient  # lazy: heavy

    client = MultiServerMCPClient(servers)
    return [_sync_wrap(t) for t in asyncio.run(client.get_tools())]


def tools_for_role(role_tools: list[str], mcp_servers: dict) -> list:
    """Resolve a role's browse/MCP tool names to bound tool objects."""
    out = []
    if "browse" in role_tools:
        out.append(fetch)
        out += load_mcp_tools(BROWSE_SERVERS)
    named = {n: c for n, c in mcp_servers.items() if n in role_tools}
    if named:
        out += load_mcp_tools(named)
    return out
