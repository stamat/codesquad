# Decisions

Development decision log — why things are the way they are. Newest first.
Add an entry when a choice would surprise a future contributor; keep each to
a few lines: **what** we decided, **why**, and what we rejected.

## Process rules

- **TDD, phase by phase.** Tests are written before features; the whole suite
  must be green before a phase is done. No phase starts until the previous
  one's check passes (PLAN.md §6).
- **README always current.** Every phase/feature update leaves README.md
  accurate on how to start, test, and use the project.
- **Focus before features.** New ideas go into PLAN.md or this file, not into
  the current phase's scope.

## 2026-07-12 — Model calls are logged inline in the model wrapper, not via litellm callbacks

Two failures drove this: (1) litellm runs callbacks on background logging
machinery — records could land *after* the run ended, which made a test flaky
~20% and would lag the cost breaker; (2) supervisors issue parallel `delegate`
calls, so the `current_role` global gets clobbered (live run showed coder's
model calls tagged "reviewer"). Fix: `interceptor.LoggedChat` (a ChatLiteLLM
subclass) writes the record inline in `_generate`/`_agenerate`, and carries
its role on the instance. `router.chat_model(cfg, role)` is the only
constructor. Globals stay only as fallback for shell records.

## 2026-07-12 — Compression digests handoff strings, not message lists

The `delegate` boundary carries two strings (context in, result out) — the
compressor gates those, both directions. `keep_last_messages` stays in config
unused until supervisor *history* ever needs digesting (deepagents manages
subagent-internal context itself). Originals always land in the JSONL
compress record; only live context shrinks.

## 2026-07-12 — PR step refuses empty branches

`push_and_pr` checks `rev-list HEAD..branch` first: a run that committed
nothing pushes nothing (an accidental `--auto` run in this very repo pushed a
junk empty branch to origin — guard added the same hour). Also procedure:
live tests always point `--repo` at a scratch directory, never the tool's own
checkout.

## 2026-07-12 — Worktree creation/removal belongs to the CLI

`squad run` creates the worktree + branch before agents start; `squad clean`
removes only merged ones. Agents are denied `git worktree` commands by the
shell gate. Push failures (e.g. no origin) degrade to "branch stays local" —
the run's work is never lost by the PR step failing.

## 2026-07-12 — Handoffs go through our `delegate` tool, not deepagents subagents

deepagents has built-in subagent delegation, but our own `delegate` tool is
the single interception point: it logs task+context in / result out, sets
role attribution for cost accounting, and enforces the `--max-cost` breaker
*before* each handoff. Cost ceiling within one delegation is bounded by the
role's `max_turns` recursion limit, not per-call — revisit if a single
delegation ever overspends.

## 2026-07-12 — Issue tracking (GitHub/Linear) is config, not code

Reading GitHub/Linear issues = their official MCP servers in `mcp_servers`,
bound to whichever role needs them. PLAN rule: "MCP *is* the plugin system;
build nothing bespoke." Coder can also `gh issue view` through the gated shell.
Rejected: a bespoke issue-fetching module.

## 2026-07-12 — Auto mode declines, never self-approves

`--auto` / `git.pr: auto` makes runs unattended: run-end push + PR creation
happen without a prompt (human decides at merge time). But confirm-gated
*shell* commands (sudo, rm -rf, pipe-to-sh) are auto-DECLINED, not approved —
an unattended run must never self-authorize dangerous commands.
Rejected: blanket auto-approve.

## 2026-07-12 — PR creation is a CLI step, never an agent tool

Run end → push + `gh pr create` from the CLI (confirm | auto | never).
Agents cannot push or open PRs; the capability simply isn't bound.

## 2026-07-12 — Interceptor uses process globals, not ContextVars

LiteLLM fires success callbacks in a separate thread; ContextVars set in the
main thread are invisible there. One squad run = one process, so module-level
slots (`current_log`, `current_role`) are correct. Revisit only if runs ever
share a process.

## 2026-07-12 — `ollama_chat/` prefix for tool-calling local models

LiteLLM's `ollama/` prefix uses Ollama's generate API — **no native tool
calling** (models emit tool calls as text; agent loops silently do nothing).
`ollama_chat/` uses the chat API with real tool calls. Rule: agent roles on
local models use `ollama_chat/...`; plain completion (compressor) may use
`ollama/...`.

## 2026-07-12 — Model override is a dev shim

`--override` / `SQUAD_MODEL_OVERRIDE` reroutes every role to one model
(keyless dev via Ollama, mock tests). Never for production routing — that's
what per-role `model:` in squad.yaml is for.

## 2026-07-12 — Capability boundary = tool binding, not prompts

A tool absent from a role's `tools` list is never bound at agent construction
— the model physically cannot call it. Tested in `test_agents.py` (only coder
gets shell). Prompts carry specialization; binding carries security.
Also: `FilesystemBackend(virtual_mode=True)` so `..`/absolute paths can't
escape the jail.

## 2026-07-12 — Shell gate: deny beats confirm

`rules.check_command` checks deny patterns first, then confirm, then allows.
Both pattern lists live in squad.yaml, validated as regex at config load.
The executor returns agent-visible strings (DENIED/DECLINED/TIMED OUT) and
never raises — the agent must learn why a command didn't run.

## 2026-07-12 — Roles are pure config

Adding/changing a role or its model = editing squad.yaml only (e.g. scout
moved to `gemini/gemini-3.1-flash-lite` in one line). Code never hardcodes a
role's model, tools, or prompt.
