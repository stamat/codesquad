"""Task intake: `gh:123` / `linear:ABC-123` / plain prompt — a small router over
the input, a few lines of regex. GitHub issues are fetched through `gh --json`
(exact fields, no token waste); Linear rides its official MCP server bound to a
role — the CLI only tags the task."""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_GH = re.compile(r"^gh:(\d+)$")
_LINEAR = re.compile(r"^linear:([A-Za-z][A-Za-z0-9]*-\d+)$")


@dataclass
class Task:
    text: str                      # what the squad actually works on
    slug: str                      # short branch-name fragment
    gh_issue: int | None = None    # set → post the run's report back as a comment
    linear_issue: str | None = None  # set → task expects a linear MCP tool on some role
    closes: str | None = None      # closing keyword line for the PR body (auto-closes on merge)
    source: Literal["github", "linear", "plain"] = "plain"  # which branch resolved this task


def _slugify(text: str, max_len: int = 30) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len].rstrip("-") or "task"


def _resolve_gh(n: int, repo: Path) -> Task:
    proc = subprocess.run(
        ["gh", "issue", "view", str(n), "--json", "title,body,labels"],
        cwd=repo, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gh issue view {n} failed: stderr={proc.stderr.strip()!r} stdout={proc.stdout.strip()!r}"
        )
    d = json.loads(proc.stdout)
    labels = ", ".join(l["name"] for l in d.get("labels", []))
    text = f"GitHub issue #{n}: {d['title']}\n\n{d.get('body') or ''}"
    if labels:
        text += f"\n\nLabels: {labels}"
    return Task(text=text, slug=f"gh-{n}", gh_issue=n, closes=f"Closes #{n}", source="github")


def _resolve_linear(issue: str) -> Task:
    issue = issue.upper()
    return Task(
        # first line doubles as the PR title — keep the MCP instructions below it
        text=(f"Linear issue {issue}\n\nFetch its title and description via the "
              f"linear MCP tools, then complete it."),
        slug=_slugify(issue),
        linear_issue=issue,
        closes=f"Closes {issue}",  # Linear magic word: identifier, no '#'
        source="linear",
    )


def _resolve_plain(raw: str) -> Task:
    return Task(text=raw, slug=_slugify(raw), source="plain")


def resolve_task(raw: str, repo: Path) -> Task:
    """Route the raw input: fetch a GitHub issue, tag a Linear one, or pass through."""
    raw = raw.strip()
    if m := _GH.match(raw):
        return _resolve_gh(int(m.group(1)), repo)
    if m := _LINEAR.match(raw):
        return _resolve_linear(m.group(1))
    return _resolve_plain(raw)


def comment_on_issue(issue: int, body: str, repo: Path) -> str:
    """Post the run's report back on the GitHub issue. Best-effort: a failed
    comment never fails the run."""
    proc = subprocess.run(
        ["gh", "issue", "comment", str(issue), "--body", body],
        cwd=repo, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return f"issue comment failed: {proc.stderr.strip()[:200]}"
    return f"commented on issue #{issue}"
